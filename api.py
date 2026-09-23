"""HTTP API cho agent - FastAPI + SSE (Server-Sent Events).

Bien agent tu "script chay trong terminal cua toi" thanh "dich vu ai goi cung duoc".

Ba endpoint:
  GET  /            trang demo nho de nhin thay SSE chay that trong trinh duyet
  GET  /healthz     kiem tra song/chet (deploy nao cung can cai nay)
  POST /chat        hoi -> doi -> nhan mot cuc JSON (kieu API co dien)
  GET  /chat/stream hoi -> nhan tung su kien NGAY LUC AGENT LAM (SSE)

Chay:  venv\\Scripts\\python.exe api.py
Xem tai lieu API tu sinh:  http://127.0.0.1:8000/docs
Giai thich chi tiet tung khai niem: docs/HOC_FASTAPI_SSE.md
"""

import json
import os
import time
import uuid
from collections import defaultdict, deque
from collections.abc import Iterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse, StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, Field

import main_02_02 as lab
import metrics
import persistence
import redis_client
import thread_ownership


def _valid_thread(raw: str | None) -> str | None:
    """Chi nhan dung dinh dang UUID.

    Cung ly do voi _valid_thread trong app.py: thread_id di thang vao khoa
    doc/ghi cua checkpointer, khong kiem tra thi khong gian khoa tu 122 bit
    ngau nhien thanh chuoi tuy y doan duoc (?thread_id=admin).
    """
    if not raw:
        return None
    try:
        return str(uuid.UUID(raw))
    except ValueError:
        return None


# ===========================================================================
# 1. VONG DOI UNG DUNG (lifespan)
# Code truoc chu "yield" chay MOT LAN luc server khoi dong, sau "yield" chay
# luc tat. Nap vector store o day de nguoi dung dau tien khong phai cho.
# ===========================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Warming up the vector store ...")
    lab.get_travel_info_vectorstore()
    # Cung mot checkpointer voi app.py (Postgres neu co DATABASE_URL, khong thi
    # in-memory) -> /chat va /chat/stream nho hoi thoai qua thread_id giong het
    # Streamlit, thay vi coi moi cau hoi la mot cuoc hoi thoai moi.
    app.state.agent = lab.build_agent(persistence.get_checkpointer())
    app.state.checkpointer_backend = persistence.backend_name()
    print(f"API ready. Checkpointer backend: {app.state.checkpointer_backend}")
    yield
    print("API shutting down.")


app = FastAPI(
    title="Cornwall Travel Agent API",
    description="LangGraph ReAct agent with two tools: travel search + live weather.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS: trinh duyet CHAN javascript o domain A goi API o domain B, tru khi API
# tu noi "toi cho phep". Demo nen mo het; that thi liet ke dung domain frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ===========================================================================
# 1a. SECURITY HEADERS - chan may loai tan cong pho bien o tang trinh duyet,
# khong lien quan gi den logic nghiep vu nen dat rieng, ngoai vong request.
#
# KHONG dat Content-Security-Policy: trang demo o cuoi file (DEMO_PAGE) co
# <script>/<style> inline - mot CSP that su (script-src khong 'unsafe-inline')
# se lam demo do vo, va mot CSP long leo (cho phep 'unsafe-inline') thi coi
# nhu khong chan duoc gi - chua co ly do de doi trade-off nay.
# ===========================================================================
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    # Vo hai khi chay qua HTTP (trinh duyet bo qua HSTS tren ket noi khong
    # ma hoa) - Azure Container Apps va Streamlit Cloud deu da tu dong ep
    # HTTPS o tang ingress, header nay chi khoa chac them o tang trinh duyet.
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response


# ===========================================================================
# 1b. GIOI HAN TAN SUAT (rate limit)
#
# Demo cong khai = key Gemini cua minh nam sau mot cai nut ai tren internet cung
# bam duoc. Khong chan thi mot nguoi rung cho lap la het quota (hoac het tien).
#
# Dung cua so truot trong BO NHO: don gian, du cho mot instance. Chay nhieu
# instance thi phai chuyen sang Redis vi moi tien trinh dem rieng.
# ===========================================================================

RATE_LIMIT_PER_HOUR = int(os.environ.get("RATE_LIMIT_PER_HOUR", "30"))

# CONG TAC NGAT. Rate limit chi lam CHAM ke lam dung; khi dang bi lam dung that
# hoac nha cung cap doi gia, ta can tat HAN tinh nang AI ngay - ma khong phai
# build lai image, khong phai phat hanh ban moi. Doi bien moi truong nay roi
# khoi dong lai la xong (tren Container Apps la mot revision moi, ~1 phut).
#   AI_ENABLED=0  -> /chat va /chat/stream tra 503, /healthz VAN xanh
AI_ENABLED = os.environ.get("AI_ENABLED", "1").strip().lower() not in {"0", "false", "no"}


# ===========================================================================
# 1c. API KEY (tuy chon)
#
# Khong dat API_KEYS -> API cong khai nhu truoc gio (ban dang chay tren Azure
# khong dat bien nay, nen hanh vi khong doi - chi la kha nang moi, khong phai
# breaking change). Dat bien -> /chat va /chat/stream bat buoc header
# X-API-Key hop le. /healthz va /metrics KHONG bi chan: health check cua
# container orchestrator khong the tu mang theo key, va /metrics cong khai la
# quyet dinh rieng da ghi trong HANDOFF.md, khong doi trong feature nay.
# ===========================================================================

API_KEYS = {key.strip() for key in os.environ.get("API_KEYS", "").split(",") if key.strip()}


def require_api_key(x_api_key: str = Header(default="")) -> None:
    """Dependency: chi bat buoc khi API_KEYS duoc cau hinh."""
    if not API_KEYS:
        return
    if x_api_key not in API_KEYS:
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid API key. Pass a valid key in the X-API-Key header.",
            headers={"WWW-Authenticate": "API-Key"},
        )


def enforce_thread_access(thread_id: str, x_api_key: str) -> None:
    """Khoa thread_id theo API key (xem thread_ownership.py).

    Chi kiem tra khi API_KEYS duoc cau hinh - demo cong khai (API_KEYS rong)
    khong co danh tinh nao de khoa theo, hanh vi giu nguyen nhu truoc.
    """
    if not API_KEYS:
        return
    if not thread_ownership.check_and_claim(thread_id, x_api_key):
        raise HTTPException(
            status_code=403,
            detail="This thread_id belongs to a different API key.",
        )


def require_ai_enabled() -> None:
    """Dependency: chan truoc khi handler chay, giong enforce_rate_limit.

    503 chu khong phai 500: day la tu choi CO CHU Y va tam thoi. 503 con bao cho
    trinh duyet/CDN biet dung cache lai cau tra loi nay.
    """
    if not AI_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="The AI feature is temporarily disabled by the operator. "
                   "The rest of the service is unaffected.",
            headers={"Retry-After": "3600"},
        )
_RATE_WINDOW_SECONDS = 3600
_hits: dict[str, deque[float]] = defaultdict(deque)


def client_key(request: Request) -> str:
    """Nhan dang nguoi goi.

    Sau proxy (Hugging Face, Cloud Run, nginx) thi request.client.host la IP cua
    proxy - moi nguoi dung se chung mot suat. Vi vay uu tien X-Forwarded-For.
    Luu y: header nay client tu dat duoc nen KHONG dung de chong tan cong that;
    o day chi de chan lam dung thong thuong.
    """
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_rate_limit_memory(key: str, now: float) -> tuple[bool, int]:
    """Cua so truot trong BO NHO tien trinh - ban goc, dung khi khong co Redis.

    Han che da biet: dem rieng cho MOI tien trinh, mat sach khi restart, khong
    chia se giua nhieu instance (xem _check_rate_limit_redis ben duoi).
    """
    hits = _hits[key]
    while hits and now - hits[0] > _RATE_WINDOW_SECONDS:
        hits.popleft()

    if len(hits) >= RATE_LIMIT_PER_HOUR:
        retry_after = int(_RATE_WINDOW_SECONDS - (now - hits[0])) + 1
        return False, retry_after

    hits.append(now)
    return True, 0


def _check_rate_limit_redis(client, key: str, now: float) -> tuple[bool, int]:
    """Cung mot thuat toan cua so truot, nhung luu trong Redis sorted set thay
    vi bo nho tien trinh - nhieu instance API dung chung mot bo dem that su.

    Diem (score) cua moi phan tu la chinh thoi diem request - ZREMRANGEBYSCORE
    xoa cac luot da qua cua so 1 gio, ZCARD dem con lai bao nhieu. EXPIRE dat
    tren ca key de Redis tu don don cho client da lau khong quay lai, khong
    can mot tien trinh don rac rieng.
    """
    redis_key = f"ratelimit:{key}"
    client.zremrangebyscore(redis_key, 0, now - _RATE_WINDOW_SECONDS)
    count = client.zcard(redis_key)

    if count >= RATE_LIMIT_PER_HOUR:
        oldest = client.zrange(redis_key, 0, 0, withscores=True)
        oldest_ts = oldest[0][1] if oldest else now
        retry_after = int(_RATE_WINDOW_SECONDS - (now - oldest_ts)) + 1
        return False, retry_after

    pipe = client.pipeline()
    pipe.zadd(redis_key, {str(now): now})
    pipe.expire(redis_key, _RATE_WINDOW_SECONDS)
    pipe.execute()
    return True, 0


def enforce_rate_limit(request: Request) -> None:
    """Dependency cua FastAPI: chay TRUOC handler, vuot nguong thi nem 429.

    Dung Redis khi co REDIS_URL (chia se duoc giua nhieu instance), tu lui ve
    bo dem trong tien trinh khi khong co - xem redis_client.get_redis().
    """
    key = client_key(request)
    now = time.time()
    redis = redis_client.get_redis()

    if redis is not None:
        allowed, retry_after = _check_rate_limit_redis(redis, key, now)
    else:
        allowed, retry_after = _check_rate_limit_memory(key, now)

    if not allowed:
        metrics.RATE_LIMITED.inc()
        raise HTTPException(
            status_code=429,
            detail=(
                f"Demo limit reached: {RATE_LIMIT_PER_HOUR} questions per hour. "
                f"Try again in {retry_after // 60 + 1} minute(s), or run it locally - "
                "the repo is public."
            ),
            headers={"Retry-After": str(retry_after)},
        )


# ===========================================================================
# 2. HOP DONG DU LIEU (pydantic model)
# Khai bao kieu -> FastAPI TU DONG: kiem tra du lieu vao, tra loi 422 neu sai,
# va sinh tai lieu OpenAPI o /docs. Khong phai viet mot dong validate nao.
# ===========================================================================

class ChatRequest(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=500,
        description="Cau hoi cua nguoi dung",
        examples=["Suggest two Cornwall beach towns with nice weather"],
    )
    thread_id: str | None = Field(
        default=None,
        description="Continue a previous conversation. Omit to start a new one - the "
                    "response always echoes the thread_id to reuse for the next call.",
    )


class ToolCallInfo(BaseModel):
    name: str
    args: dict


class ChatResponse(BaseModel):
    answer: str
    tool_calls: list[ToolCallInfo]
    elapsed_seconds: float
    model: str
    thread_id: str


# ===========================================================================
# 3. ENDPOINT DON GIAN
# ===========================================================================

@app.get("/healthz", tags=["system"])
def healthz(request: Request) -> dict:
    """Song hay chet. Cloud Run / Kubernetes goi lien tuc vao day de biet."""
    return {
        "status": "ok",
        "model": lab.CHAT_MODEL,
        "weather_source": lab.WEATHER_MODE,
        "checkpointer_backend": request.app.state.checkpointer_backend,
    }


@app.get("/metrics", tags=["system"], include_in_schema=False)
def prometheus_metrics() -> PlainTextResponse:
    """Prometheus goi vao day 15 giay mot lan de "hut" so lieu ve.

    Tra ve text thuan, moi dong mot chi so - mo bang trinh duyet doc duoc luon.
    """
    return PlainTextResponse(
        generate_latest(metrics.build_registry()), media_type=CONTENT_TYPE_LATEST
    )


@app.post(
    "/chat",
    response_model=ChatResponse,
    tags=["agent"],
    # enforce_rate_limit TRUOC require_api_key co chu y: neu API key sai chan
    # truoc, ke do sai key lien tuc de do quota (khong the sai bao nhieu lan
    # cung duoc, IP van bi dem). Doi cho thi rate limit tro thanh vo tac dung
    # voi ke khong co key dung.
    dependencies=[
        Depends(enforce_rate_limit), Depends(require_api_key), Depends(require_ai_enabled),
    ],
)
def chat(
    request: ChatRequest, http_request: Request, x_api_key: str = Header(default=""),
) -> ChatResponse:
    """Hoi mot cau, doi agent lam xong, tra ve mot cuc JSON.

    Don gian nhung nguoi dung phai nhin man hinh trong ~15 giay ma khong biet
    chuyen gi dang xay ra -> vi vay moi co /chat/stream ben duoi.
    """
    thread_id = _valid_thread(request.thread_id) or str(uuid.uuid4())
    enforce_thread_access(thread_id, x_api_key)
    config = {"configurable": {"thread_id": thread_id}}
    started = time.time()
    metrics.IN_FLIGHT.inc()
    try:
        result = http_request.app.state.agent.invoke(
            {"messages": [HumanMessage(content=request.question)]}, config=config
        )
    except Exception:
        metrics.REQUESTS.labels(endpoint="/chat", status="error").inc()
        raise
    finally:
        metrics.IN_FLIGHT.dec()
        metrics.REQUEST_DURATION.labels(endpoint="/chat").observe(time.time() - started)

    metrics.REQUESTS.labels(endpoint="/chat", status="ok").inc()

    tool_calls = [
        ToolCallInfo(name=call["name"], args=call["args"])
        for message in result["messages"]
        if isinstance(message, AIMessage)
        for call in (message.tool_calls or [])
    ]
    return ChatResponse(
        answer=lab.answer_text(result["messages"][-1]),
        tool_calls=tool_calls,
        elapsed_seconds=round(time.time() - started, 2),
        model=lab.CHAT_MODEL,
        thread_id=thread_id,
    )


# ===========================================================================
# 4. SSE - Server-Sent Events
# Dinh dang tren duong day chi la text thuan, moi su kien 2 dong + 1 dong trong:
#     event: tool_call
#     data: {"name": "weather_forecast", "args": {"town": "St Ives"}}
#     <dong trong ket thuc su kien>
# Trinh duyet doc bang EventSource, curl doc duoc bang mat thuong.
# ===========================================================================

def sse(event: str, payload: dict) -> str:
    """Dong goi mot su kien SSE. ensure_ascii=False de tieng Viet khong bi \\uXXXX."""
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def agent_events(agent, question: str, thread_id: str) -> Iterator[str]:
    """Generator: moi lan 'yield' la mot mieng du lieu day ngay ra cho client.

    Ham nay la trai tim cua SSE. LangGraph cho stream_mode='updates' -> cu mot
    node trong do thi chay xong thi tra ve ket qua node do, ta doi thanh su kien.
    """
    config = {"configurable": {"thread_id": thread_id}}
    started = time.time()
    tool_calls = 0
    status = "error"
    metrics.IN_FLIGHT.inc()
    yield sse("start", {"question": question, "model": lab.CHAT_MODEL, "thread_id": thread_id})

    try:
        for update in agent.stream(
            {"messages": [HumanMessage(content=question)]},
            config=config,
            stream_mode="updates",
        ):
            for payload in update.values():
                for message in payload.get("messages", []):
                    if isinstance(message, AIMessage) and message.tool_calls:
                        for call in message.tool_calls:
                            tool_calls += 1
                            yield sse("tool_call", {"name": call["name"], "args": call["args"]})
                    elif isinstance(message, ToolMessage):
                        yield sse("tool_result", {
                            "name": message.name,
                            "preview": str(message.content)[:300],
                        })
                    elif isinstance(message, AIMessage):
                        yield sse("answer", {"text": lab.answer_text(message)})
        status = "ok"
    except Exception as exc:
        # Loi giua chung: bao cho client biet roi dong stream tu te, khong treo.
        yield sse("error", {"message": str(exc)})
        return
    finally:
        # finally chay ca khi client ngat giua chung (generator bi dong)
        # -> so lieu khong bi ho.
        metrics.IN_FLIGHT.dec()
        metrics.REQUEST_DURATION.labels(endpoint="/chat/stream").observe(time.time() - started)
        metrics.REQUESTS.labels(endpoint="/chat/stream", status=status).inc()

    yield sse("done", {
        "tool_calls": tool_calls,
        "elapsed_seconds": round(time.time() - started, 2),
    })


@app.get(
    "/chat/stream",
    tags=["agent"],
    dependencies=[
        Depends(enforce_rate_limit), Depends(require_api_key), Depends(require_ai_enabled),
    ],
)
def chat_stream(
    http_request: Request,
    q: str = Query(min_length=3, max_length=500, description="Cau hoi"),
    thread: str | None = Query(default=None, description="thread_id de tiep tuc hoi thoai cu"),
    x_api_key: str = Header(default=""),
):
    """Hoi mot cau, nhan tung su kien ngay khi agent lam - khong phai cho het 15 giay.

    Dung GET (khong phai POST) vi EventSource cua trinh duyet chi goi duoc GET.
    """
    thread_id = _valid_thread(thread) or str(uuid.uuid4())
    enforce_thread_access(thread_id, x_api_key)
    return StreamingResponse(
        agent_events(http_request.app.state.agent, q, thread_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",   # cam proxy cache lai luong
            "X-Accel-Buffering": "no",     # cam nginx gom buffer (se lam mat tinh realtime)
        },
    )


# ===========================================================================
# 5. TRANG DEMO - de NHIN THAY SSE chay, khong can cai gi them
# ===========================================================================

DEMO_PAGE = """<!doctype html>
<meta charset="utf-8"><title>Travel Agent API demo</title>
<style>
 body{font:15px system-ui;max-width:760px;margin:40px auto;padding:0 16px}
 #log{margin-top:20px}
 .ev{padding:8px 12px;margin:6px 0;border-left:3px solid #ccc;background:#fafafa}
 .tool_call{border-color:#e67e22} .tool_result{border-color:#7f8c8d} .answer{border-color:#27ae60}
 .done{border-color:#2980b9} .error{border-color:#c0392b}
 input{width:70%;padding:8px} button{padding:8px 16px}
 code{font-size:13px;color:#555}
</style>
<h2>Travel Agent - SSE demo</h2>
<input id="q" value="Suggest two Cornwall beach towns with nice weather">
<button onclick="ask()">Ask</button>
<div id="log"></div>
<script>
let es;
function add(kind, text){
  const d = document.createElement('div');
  d.className = 'ev ' + kind;
  d.innerHTML = '<b>' + kind + '</b><br><code>' + text + '</code>';
  document.getElementById('log').appendChild(d);
}
function ask(){
  if (es) es.close();
  document.getElementById('log').innerHTML = '';
  const q = encodeURIComponent(document.getElementById('q').value);
  es = new EventSource('/chat/stream?q=' + q);

  ['start','tool_call','tool_result','answer','error'].forEach(function(name){
    es.addEventListener(name, function(e){ add(name, e.data); });
  });

  // QUAN TRONG: EventSource TU DONG KET NOI LAI khi server dong stream.
  // Khong close() o day thi trinh duyet se hoi lai cau do mai mai -> chay tien API.
  es.addEventListener('done', function(e){ add('done', e.data); es.close(); });
}
</script>
"""


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def demo_page() -> str:
    return DEMO_PAGE


if __name__ == "__main__":
    import uvicorn

    # reload=True: sua code la server tu khoi dong lai (chi dung khi dev).
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=False)
