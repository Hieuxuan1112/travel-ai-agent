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
import time
from collections.abc import Iterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse, StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, Field

import main_02_02 as lab
import metrics

# ===========================================================================
# 1. VONG DOI UNG DUNG (lifespan)
# Code truoc chu "yield" chay MOT LAN luc server khoi dong, sau "yield" chay
# luc tat. Nap vector store o day de nguoi dung dau tien khong phai cho.
# ===========================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Warming up the vector store ...")
    lab.get_travel_info_vectorstore()
    print("API ready.")
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


class ToolCallInfo(BaseModel):
    name: str
    args: dict


class ChatResponse(BaseModel):
    answer: str
    tool_calls: list[ToolCallInfo]
    elapsed_seconds: float
    model: str


# ===========================================================================
# 3. ENDPOINT DON GIAN
# ===========================================================================

@app.get("/healthz", tags=["system"])
def healthz() -> dict:
    """Song hay chet. Cloud Run / Kubernetes goi lien tuc vao day de biet."""
    return {"status": "ok", "model": lab.CHAT_MODEL, "weather_source": lab.WEATHER_MODE}


@app.get("/metrics", tags=["system"], include_in_schema=False)
def prometheus_metrics() -> PlainTextResponse:
    """Prometheus goi vao day 15 giay mot lan de "hut" so lieu ve.

    Tra ve text thuan, moi dong mot chi so - mo bang trinh duyet doc duoc luon.
    """
    return PlainTextResponse(
        generate_latest(metrics.build_registry()), media_type=CONTENT_TYPE_LATEST
    )


@app.post("/chat", response_model=ChatResponse, tags=["agent"])
def chat(request: ChatRequest) -> ChatResponse:
    """Hoi mot cau, doi agent lam xong, tra ve mot cuc JSON.

    Don gian nhung nguoi dung phai nhin man hinh trong ~15 giay ma khong biet
    chuyen gi dang xay ra -> vi vay moi co /chat/stream ben duoi.
    """
    started = time.time()
    metrics.IN_FLIGHT.inc()
    try:
        result = lab.travel_info_agent.invoke(
            {"messages": [HumanMessage(content=request.question)]}
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


def agent_events(question: str) -> Iterator[str]:
    """Generator: moi lan 'yield' la mot mieng du lieu day ngay ra cho client.

    Ham nay la trai tim cua SSE. LangGraph cho stream_mode='updates' -> cu mot
    node trong do thi chay xong thi tra ve ket qua node do, ta doi thanh su kien.
    """
    started = time.time()
    tool_calls = 0
    status = "error"
    metrics.IN_FLIGHT.inc()
    yield sse("start", {"question": question, "model": lab.CHAT_MODEL})

    try:
        for update in lab.travel_info_agent.stream(
            {"messages": [HumanMessage(content=question)]}, stream_mode="updates"
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


@app.get("/chat/stream", tags=["agent"])
def chat_stream(q: str = Query(min_length=3, max_length=500, description="Cau hoi")):
    """Hoi mot cau, nhan tung su kien ngay khi agent lam - khong phai cho het 15 giay.

    Dung GET (khong phai POST) vi EventSource cua trinh duyet chi goi duoc GET.
    """
    return StreamingResponse(
        agent_events(q),
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
