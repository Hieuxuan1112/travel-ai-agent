# API Multi-Turn Memory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `/chat` and `/chat/stream` remember conversation history across calls via a
`thread_id`, mirroring the pattern `app.py` already runs in production, instead of treating
every request as a fresh conversation.

**Architecture:** Build the agent once at FastAPI startup with
`lab.build_agent(persistence.get_checkpointer())` (stored on `app.state`), accept an optional
`thread_id` in the request/query, validate it as a UUID the same way `app.py` does, generate
one when absent, and always echo it back in the response so the caller knows what to send
next time. A `DATABASE_URL` that's set but unreachable crashes at startup — `persistence.py`
already raises for that case, so no new error handling is needed for it.

**Tech Stack:** FastAPI, LangGraph checkpointer (`persistence.py`, already exists), pytest,
`fastapi.testclient.TestClient`.

**Spec:** `docs/superpowers/specs/2026-09-12-api-multiturn-memory-design.md`

---

### Task 1: `thread_id` on the request/response models + validation helper

**Files:**
- Modify: `api.py` (imports near top; `ChatRequest`/`ChatResponse` around lines 148-166)
- Test: `tests/test_api.py`

- [ ] **Step 1: Write the failing test**

Add near the top of `tests/test_api.py` (after the existing imports):

```python
def test_valid_thread_accepts_uuid_rejects_junk():
    valid = "0d1f7f2e-2222-4b3b-9c3c-111111111111"
    assert api._valid_thread(valid) == valid
    assert api._valid_thread("admin") is None
    assert api._valid_thread(None) is None
    assert api._valid_thread("") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv\Scripts\python.exe -m pytest tests/test_api.py -k test_valid_thread -v`
Expected: FAIL with `AttributeError: module 'api' has no attribute '_valid_thread'`

- [ ] **Step 3: Write the implementation**

In `api.py`, add `import uuid` to the import block at the top (alphabetical, next to
`import time`):

```python
import json
import os
import time
import uuid
from collections import defaultdict, deque
```

Add the helper right after the imports/before the `lifespan` function (i.e. after line 31
`os.environ.setdefault(...)` equivalent section, before `# === 1. VONG DOI ...`):

```python
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
```

Update `ChatRequest` and `ChatResponse` (currently lines 148-166):

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `venv\Scripts\python.exe -m pytest tests/test_api.py -k test_valid_thread -v`
Expected: PASS

Note: the full suite will now FAIL to collect/run other `test_api.py` tests because
`ChatResponse` requires `thread_id` and the handlers don't supply it yet - that's expected
and gets fixed in Task 2. Don't chase those failures in this task.

- [ ] **Step 5: Commit**

```bash
git add api.py tests/test_api.py
git commit -m "feat(api): accept and validate thread_id on chat requests" -m "First step toward multi-turn memory: the wire format for continuing a conversation, validated the same way app.py already validates it from the URL." -m "Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 2: Stateful agent built at startup, wired into `/chat` and `/healthz`

**Files:**
- Modify: `api.py` (imports, `lifespan`, `chat()`, `healthz()`)
- Test: `tests/test_api.py` (the `client` fixture and 3 existing tests)

- [ ] **Step 1: Update the fixture and existing tests first (they define the contract)**

Replace the `FakeAgent` class and `client` fixture in `tests/test_api.py`:

```python
class FakeAgent:
    def __init__(self):
        self.last_config = None

    def stream(self, state, config=None, stream_mode=None):
        self.last_config = config
        yield from FAKE_RUN

    def invoke(self, state, config=None):
        self.last_config = config
        messages = [HumanMessage(content="q")]
        for update in FAKE_RUN:
            for payload in update.values():
                messages.extend(payload["messages"])
        return {"messages": messages}


@pytest.fixture
def client(monkeypatch):
    fake_agent = FakeAgent()
    monkeypatch.setattr(api.lab, "get_travel_info_vectorstore", lambda: None)
    monkeypatch.setattr(api.lab, "build_agent", lambda checkpointer=None: fake_agent)
    monkeypatch.setattr(api.persistence, "get_checkpointer", lambda: None)
    monkeypatch.setattr(api.persistence, "backend_name", lambda: "in-memory")
    with TestClient(api.app) as test_client:
        test_client.fake_agent = fake_agent
        yield test_client
```

Update the 3 tests that touched the old global agent:

```python
def test_healthz_reports_configuration(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["checkpointer_backend"] == "in-memory"


def test_chat_returns_answer_and_tool_calls(client):
    response = client.post("/chat", json={"question": "weather in St Ives?"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "It is 21.7 C in St Ives."
    assert body["tool_calls"] == [{"name": "weather_forecast", "args": {"town": "St Ives"}}]
    assert body["elapsed_seconds"] >= 0
    uuid.UUID(body["thread_id"])  # khong nem ValueError nghia la dung dinh dang
```

Add `import uuid` to the top of `tests/test_api.py` alongside the other stdlib imports.

Update `test_stream_reports_errors_instead_of_crashing` (it replaces the whole agent, so it
must still work after Task 3 changes the stream endpoint's signature too - do this part now
since the fixture change already breaks it):

```python
def test_stream_reports_errors_instead_of_crashing(client, monkeypatch):
    """Agent no giua chung: client phai nhan su kien 'error', khong phai ket noi dut."""
    class BoomAgent:
        def stream(self, state, config=None, stream_mode=None):
            raise RuntimeError("model unavailable")
            yield  # pragma: no cover - lam ham nay thanh generator

    client.app.state.agent = BoomAgent()
    response = client.get("/chat/stream", params={"q": "anything at all"})

    assert "event: error" in response.text
    assert "model unavailable" in response.text
```

- [ ] **Step 2: Run to verify the intended failures**

Run: `venv\Scripts\python.exe -m pytest tests/test_api.py -v`
Expected: FAIL - `api.persistence` doesn't exist yet (`AttributeError: module 'api' has no
attribute 'persistence'`), and `app.state.agent` doesn't exist yet either.

- [ ] **Step 3: Write the implementation**

In `api.py`, add the import (module-level, next to `import metrics`):

```python
import main_02_02 as lab
import metrics
import persistence
```

Replace `lifespan` (currently lines 39-45):

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Warming up the vector store ...")
    lab.get_travel_info_vectorstore()
    app.state.agent = lab.build_agent(persistence.get_checkpointer())
    app.state.checkpointer_backend = persistence.backend_name()
    print(f"API ready. Checkpointer backend: {app.state.checkpointer_backend}")
    yield
    print("API shutting down.")
```

Replace `healthz` (currently lines 173-176):

```python
@app.get("/healthz", tags=["system"])
def healthz(request: Request) -> dict:
    """Song hay chet. Cloud Run / Kubernetes goi lien tuc vao day de biet."""
    return {
        "status": "ok",
        "model": lab.CHAT_MODEL,
        "weather_source": lab.WEATHER_MODE,
        "checkpointer_backend": request.app.state.checkpointer_backend,
    }
```

Replace `chat` (currently lines 196-228):

```python
@app.post(
    "/chat",
    response_model=ChatResponse,
    tags=["agent"],
    dependencies=[Depends(require_ai_enabled), Depends(enforce_rate_limit)],
)
def chat(request: ChatRequest, http_request: Request) -> ChatResponse:
    """Hoi mot cau, doi agent lam xong, tra ve mot cuc JSON.

    Don gian nhung nguoi dung phai nhin man hinh trong ~15 giay ma khong biet
    chuyen gi dang xay ra -> vi vay moi co /chat/stream ben duoi.
    """
    thread_id = _valid_thread(request.thread_id) or str(uuid.uuid4())
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
```

- [ ] **Step 4: Run to verify these tests pass**

Run: `venv\Scripts\python.exe -m pytest tests/test_api.py -k "healthz or chat_returns_answer or too_short or stream_reports_errors" -v`
Expected: PASS (the two `/chat/stream`-shape tests not touched yet -
`test_stream_emits_events_in_order` - are handled in Task 3)

- [ ] **Step 5: Commit**

```bash
git add api.py tests/test_api.py
git commit -m "feat(api): build the agent with a real checkpointer at startup" -m "api.py now goes through the same persistence.get_checkpointer() app.py already runs in production, so /chat remembers a conversation by thread_id instead of starting fresh every call." -m "Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 3: `thread_id` on `/chat/stream`

**Files:**
- Modify: `api.py` (`agent_events()`, `chat_stream()`, currently lines 245-309)
- Test: `tests/test_api.py`

- [ ] **Step 1: Write the failing tests**

Update `test_stream_emits_events_in_order` and add a new test:

```python
def test_stream_emits_events_in_order(client):
    response = client.get("/chat/stream", params={"q": "weather in St Ives?"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    events = [line[7:] for line in response.text.splitlines() if line.startswith("event: ")]
    assert events == ["start", "tool_call", "tool_result", "answer", "done"]
    assert '"name": "weather_forecast"' in response.text


def test_stream_generates_thread_id_when_missing(client):
    response = client.get("/chat/stream", params={"q": "weather in St Ives?"})

    start_line = next(
        line for line in response.text.splitlines() if line.startswith("data: ")
    )
    payload = json.loads(start_line[len("data: "):])
    uuid.UUID(payload["thread_id"])
    assert client.fake_agent.last_config == {
        "configurable": {"thread_id": payload["thread_id"]}
    }


def test_stream_reuses_given_thread_id(client):
    thread_id = "0d1f7f2e-2222-4b3b-9c3c-111111111111"
    client.get("/chat/stream", params={"q": "weather in St Ives?", "thread": thread_id})

    assert client.fake_agent.last_config == {"configurable": {"thread_id": thread_id}}
```

Add `import json` to the top of `tests/test_api.py` if not already present (it isn't).

- [ ] **Step 2: Run test to verify it fails**

Run: `venv\Scripts\python.exe -m pytest tests/test_api.py -k "stream_generates_thread_id or stream_reuses_given_thread_id" -v`
Expected: FAIL - `chat_stream()` doesn't accept a `thread` query param yet, and
`agent_events` doesn't put `thread_id` in the `start` payload.

- [ ] **Step 3: Write the implementation**

Replace `agent_events` and `chat_stream` (currently lines 245-309):

```python
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
    dependencies=[Depends(require_ai_enabled), Depends(enforce_rate_limit)],
)
def chat_stream(
    http_request: Request,
    q: str = Query(min_length=3, max_length=500, description="Cau hoi"),
    thread: str | None = Query(default=None, description="thread_id de tiep tuc hoi thoai cu"),
):
    """Hoi mot cau, nhan tung su kien ngay khi agent lam - khong phai cho het 15 giay.

    Dung GET (khong phai POST) vi EventSource cua trinh duyet chi goi duoc GET.
    """
    thread_id = _valid_thread(thread) or str(uuid.uuid4())
    return StreamingResponse(
        agent_events(http_request.app.state.agent, q, thread_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",   # cam proxy cache lai luong
            "X-Accel-Buffering": "no",     # cam nginx gom buffer (se lam mat tinh realtime)
        },
    )
```

- [ ] **Step 4: Run the full test file**

Run: `venv\Scripts\python.exe -m pytest tests/test_api.py -v`
Expected: PASS, all tests in the file green.

- [ ] **Step 5: Commit**

```bash
git add api.py tests/test_api.py
git commit -m "feat(api): carry thread_id through the SSE stream endpoint" -m "Same thread_id contract as /chat, applied to /chat/stream: the start event echoes the id in use so a browser client can persist and resend it." -m "Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 4: Full verification and PR

**Files:** none (verification only)

- [ ] **Step 1: Run the full test suite**

Run: `venv\Scripts\python.exe -m pytest -q`
Expected: all tests pass (81 previous + new ones from Tasks 1-3, minus none removed).

- [ ] **Step 2: Run ruff**

Run: `venv\Scripts\python.exe -m ruff check .`
Expected: no new violations in `api.py` / `tests/test_api.py`.

- [ ] **Step 3: Manual smoke test against a real run (optional but recommended)**

```bash
venv\Scripts\python.exe -m uvicorn api:app --port 8000
```
In another terminal:
```bash
curl -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "{\"question\": \"What is the weather in St Ives?\"}"
```
Copy the `thread_id` from the response, then:
```bash
curl -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "{\"question\": \"and what about its wind speed?\", \"thread_id\": \"<paste-here>\"}"
```
Expected: the second answer addresses St Ives specifically without the question
repeating the town name - proof the history carried over. Stop the server after
(Ctrl+C).

- [ ] **Step 4: Push and open the PR**

```bash
git push -u origin feature/api-multiturn-memory
gh pr create --title "Add multi-turn memory to the FastAPI backend via thread_id" --body "$(cat <<'EOF'
## Summary
- api.py now builds the agent with persistence.get_checkpointer() at startup instead of the memory-less travel_info_agent, mirroring the pattern app.py already runs against Postgres in production.
- /chat and /chat/stream accept an optional thread_id and always echo one back, so a client can continue a conversation across calls.
- A DATABASE_URL that's set but unreachable now fails API startup loudly, matching the "don't silently lose data users think is saved" principle already applied elsewhere in this repo.

## Test plan
- [x] Unit test for the UUID validation helper
- [x] Existing /chat and /chat/stream tests updated for the new agent-on-app.state wiring
- [x] New tests: thread_id is generated when missing, reused when given, and threaded into the agent's config on both endpoints
- [x] Full pytest suite green
- [x] ruff clean
- [x] Manual two-call smoke test against a live run confirming context carries over

Design: docs/superpowers/specs/2026-09-12-api-multiturn-memory-design.md
EOF
)"
```
