"""Test cho HTTP API - chay offline: agent that duoc thay bang agent gia.

Diem hoc o day: test API KHONG duoc goi LLM that. Ta thay
`travel_info_agent` bang mot object gia tra ve san message -> test chay 0.1 giay,
khong ton tien, khong can mang. Day la cach moi cong ty test service co LLM.
"""

import os
import sys
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
    def stream(self, state, stream_mode=None):
        yield from FAKE_RUN

    def invoke(self, state):
        messages = [HumanMessage(content="q")]
        for update in FAKE_RUN:
            for payload in update.values():
                messages.extend(payload["messages"])
        return {"messages": messages}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(api.lab, "travel_info_agent", FakeAgent())
    # Bo qua lifespan (khong dung vector store that) bang cach goi thang TestClient
    # voi app da patch: TestClient van chay lifespan -> patch luon ham nap kho.
    monkeypatch.setattr(api.lab, "get_travel_info_vectorstore", lambda: None)
    with TestClient(api.app) as test_client:
        yield test_client


def test_healthz_reports_configuration(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_chat_returns_answer_and_tool_calls(client):
    response = client.post("/chat", json={"question": "weather in St Ives?"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "It is 21.7 C in St Ives."
    assert body["tool_calls"] == [{"name": "weather_forecast", "args": {"town": "St Ives"}}]
    assert body["elapsed_seconds"] >= 0


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


def test_stream_reports_errors_instead_of_crashing(client, monkeypatch):
    """Agent no giua chung: client phai nhan su kien 'error', khong phai ket noi dut."""
    class BoomAgent:
        def stream(self, state, stream_mode=None):
            raise RuntimeError("model unavailable")
            yield  # pragma: no cover - lam ham nay thanh generator

    monkeypatch.setattr(api.lab, "travel_info_agent", BoomAgent())
    response = client.get("/chat/stream", params={"q": "anything at all"})

    assert "event: error" in response.text
    assert "model unavailable" in response.text
