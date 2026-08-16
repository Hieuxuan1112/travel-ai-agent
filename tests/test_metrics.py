"""Test cho lop metrics - van chay offline, khong goi LLM that."""

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("GOOGLE_API_KEY", "test-key-not-used")

import api  # noqa: E402
import metrics  # noqa: E402
from tests.test_api import FakeAgent  # noqa: E402


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(api.lab, "travel_info_agent", FakeAgent())
    monkeypatch.setattr(api.lab, "get_travel_info_vectorstore", lambda: None)
    with TestClient(api.app) as test_client:
        yield test_client


def counter_value(name: str, **labels) -> float:
    """Doc gia tri hien tai cua mot counter tu registry."""
    from prometheus_client import REGISTRY

    return REGISTRY.get_sample_value(name, labels) or 0.0


def test_metrics_endpoint_exposes_prometheus_format(client):
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    # Prometheus doc dinh dang nay: moi chi so co dong # HELP + # TYPE di truoc.
    assert "# HELP agent_requests_total" in response.text
    assert "# TYPE agent_request_duration_seconds histogram" in response.text


def test_request_counter_and_latency_are_recorded(client):
    before = counter_value("agent_requests_total", endpoint="/chat", status="ok")

    client.post("/chat", json={"question": "weather in St Ives?"})

    after = counter_value("agent_requests_total", endpoint="/chat", status="ok")
    assert after == before + 1
    # Histogram phai co it nhat mot quan sat -> _count tang theo
    assert counter_value("agent_request_duration_seconds_count", endpoint="/chat") >= 1


def test_stream_endpoint_is_counted_separately(client):
    before = counter_value("agent_requests_total", endpoint="/chat/stream", status="ok")

    client.get("/chat/stream", params={"q": "weather in St Ives?"})

    after = counter_value("agent_requests_total", endpoint="/chat/stream", status="ok")
    assert after == before + 1


def test_token_usage_becomes_tokens_and_cost():
    """Tien duoc tinh tu token theo bang gia, khong phai con so bia."""
    model = "gemini-3.1-flash-lite"
    tokens_before = counter_value("agent_llm_tokens_total", model=model, kind="input")
    cost_before = counter_value("agent_llm_cost_usd_total", model=model)

    metrics.record_llm_usage(model, {"input_tokens": 1_000_000, "output_tokens": 0})

    assert counter_value("agent_llm_tokens_total", model=model, kind="input") == (
        tokens_before + 1_000_000
    )
    # 1 trieu token input cua flash-lite = $0.25
    assert counter_value("agent_llm_cost_usd_total", model=model) == pytest.approx(
        cost_before + 0.25
    )


def test_unknown_model_counts_tokens_but_not_cost():
    """Model khong co trong bang gia: van dem token, khong bia ra tien."""
    cost_before = counter_value("agent_llm_cost_usd_total", model="some-new-model")

    metrics.record_llm_usage("some-new-model", {"input_tokens": 500, "output_tokens": 100})

    assert counter_value("agent_llm_tokens_total", model="some-new-model", kind="output") == 100
    assert counter_value("agent_llm_cost_usd_total", model="some-new-model") == cost_before
