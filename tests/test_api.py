"""Test cho HTTP API - chay offline: agent that duoc thay bang agent gia.

Diem hoc o day: test API KHONG duoc goi LLM that. Ta thay
`travel_info_agent` bang mot object gia tra ve san message -> test chay 0.1 giay,
khong ton tien, khong can mang. Day la cach moi cong ty test service co LLM.
"""

import json
import os
import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("GOOGLE_API_KEY", "test-key-not-used")

import api  # noqa: E402

# Kich ban gia: LLM goi 1 tool, tool tra ket qua, LLM chot cau tra loi.
FAKE_RUN = [
    {"llm_node": {"messages": [
        AIMessage(content="", tool_calls=[
            {"name": "weather_forecast", "args": {"town": "St Ives"}, "id": "call_1"}
        ])
    ]}},
    {"tools": {"messages": [
        ToolMessage(content='{"town": "St Ives", "temperature": 21.7}',
                    name="weather_forecast", tool_call_id="call_1")
    ]}},
    {"llm_node": {"messages": [AIMessage(content="It is 21.7 C in St Ives.")]}},
]


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
    # Bo qua lifespan (khong dung vector store/checkpointer that) bang cach patch
    # truoc khi TestClient chay lifespan.
    monkeypatch.setattr(api.lab, "get_travel_info_vectorstore", lambda: None)
    monkeypatch.setattr(api.lab, "build_agent", lambda checkpointer=None: fake_agent)
    monkeypatch.setattr(api.persistence, "get_checkpointer", lambda: None)
    monkeypatch.setattr(api.persistence, "backend_name", lambda: "in-memory")
    with TestClient(api.app) as test_client:
        test_client.fake_agent = fake_agent
        yield test_client


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


def test_chat_reuses_given_thread_id(client):
    thread_id = "0d1f7f2e-2222-4b3b-9c3c-111111111111"
    client.post("/chat", json={"question": "weather in St Ives?", "thread_id": thread_id})
    assert client.fake_agent.last_config == {"configurable": {"thread_id": thread_id}}


def test_valid_thread_accepts_uuid_rejects_junk():
    valid = "0d1f7f2e-2222-4b3b-9c3c-111111111111"
    assert api._valid_thread(valid) == valid
    assert api._valid_thread("admin") is None
    assert api._valid_thread(None) is None
    assert api._valid_thread("") is None


def test_too_short_question_is_rejected_by_validation(client):
    """Pydantic tu chan input xau -> 422, khong can viet code kiem tra."""
    response = client.post("/chat", json={"question": "hi"})
    assert response.status_code == 422


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


def test_stream_reports_errors_instead_of_crashing(client):
    """Agent no giua chung: client phai nhan su kien 'error', khong phai ket noi dut."""
    class BoomAgent:
        def stream(self, state, config=None, stream_mode=None):
            raise RuntimeError("model unavailable")
            yield  # pragma: no cover - lam ham nay thanh generator

    client.app.state.agent = BoomAgent()
    response = client.get("/chat/stream", params={"q": "anything at all"})

    assert "event: error" in response.text
    assert "model unavailable" in response.text
