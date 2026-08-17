"""Test gioi han tan suat - thu bat buoc phai co truoc khi mo demo cong khai."""

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("GOOGLE_API_KEY", "test-key-not-used")

import api  # noqa: E402
from tests.test_api import FakeAgent  # noqa: E402


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(api.lab, "travel_info_agent", FakeAgent())
    monkeypatch.setattr(api.lab, "get_travel_info_vectorstore", lambda: None)
    monkeypatch.setattr(api, "RATE_LIMIT_PER_HOUR", 3)
    api._hits.clear()          # moi test bat dau tu bo dem sach
    with TestClient(api.app) as test_client:
        yield test_client
    api._hits.clear()


def ask(client):
    return client.post("/chat", json={"question": "weather in St Ives?"})


def test_requests_under_the_limit_pass(client):
    for _ in range(3):
        assert ask(client).status_code == 200


def test_request_over_the_limit_gets_429_with_retry_after(client):
    for _ in range(3):
        ask(client)

    blocked = ask(client)
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers          # client biet cho bao lau
    assert "per hour" in blocked.json()["detail"]


def test_limit_is_per_client_not_global(client):
    """Nguoi dung A tieu het suat khong duoc lam nguoi dung B bi chan."""
    for _ in range(3):
        client.post("/chat", json={"question": "weather in St Ives?"},
                    headers={"X-Forwarded-For": "1.1.1.1"})

    assert client.post("/chat", json={"question": "weather in St Ives?"},
                       headers={"X-Forwarded-For": "1.1.1.1"}).status_code == 429
    assert client.post("/chat", json={"question": "weather in St Ives?"},
                       headers={"X-Forwarded-For": "2.2.2.2"}).status_code == 200


def test_stream_endpoint_is_limited_too(client):
    for _ in range(3):
        ask(client)

    blocked = client.get("/chat/stream", params={"q": "weather in St Ives?"})
    assert blocked.status_code == 429


def test_healthz_and_metrics_are_never_limited(client):
    """Probe cua he thong khong duoc dinh rate limit, neu khong container bi coi la chet."""
    for _ in range(10):
        assert client.get("/healthz").status_code == 200
        assert client.get("/metrics").status_code == 200
