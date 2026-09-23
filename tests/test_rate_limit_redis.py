"""Test gioi han tan suat QUA REDIS - cung kich ban voi test_rate_limit.py
(ban trong bo nho), nhung chay qua fakeredis de chung minh duong Redis that
su hoat dung, khong chi ton tai tren giay.
"""

import os
import sys
from pathlib import Path

import fakeredis
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("GOOGLE_API_KEY", "test-key-not-used")

import api  # noqa: E402
import redis_client  # noqa: E402
from tests.test_api import FakeAgent  # noqa: E402


@pytest.fixture
def client(monkeypatch):
    fake = fakeredis.FakeRedis()
    monkeypatch.setattr(redis_client, "_client", fake)
    monkeypatch.setattr(redis_client, "_checked", True)
    monkeypatch.setattr(api.lab, "build_agent", lambda checkpointer=None: FakeAgent())
    monkeypatch.setattr(api.persistence, "get_checkpointer", lambda: None)
    monkeypatch.setattr(api.persistence, "backend_name", lambda: "in-memory")
    monkeypatch.setattr(api.lab, "get_travel_info_vectorstore", lambda: None)
    monkeypatch.setattr(api, "RATE_LIMIT_PER_HOUR", 3)
    with TestClient(api.app) as test_client:
        yield test_client
    fake.flushall()


def ask(client):
    return client.post("/chat", json={"question": "weather in St Ives?"})


def test_redis_backend_is_actually_used(client):
    """Neu Redis khong duoc dung, key ratelimit:* se khong ton tai sau request."""
    ask(client)
    fake = redis_client.get_redis()
    assert fake.keys("ratelimit:*")


def test_requests_under_the_limit_pass(client):
    for _ in range(3):
        assert ask(client).status_code == 200


def test_request_over_the_limit_gets_429_with_retry_after(client):
    for _ in range(3):
        ask(client)

    blocked = ask(client)
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers
    assert "per hour" in blocked.json()["detail"]


def test_limit_is_per_client_not_global(client):
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


def test_rate_limit_key_expires_so_idle_clients_are_cleaned_up(client):
    """EXPIRE tren key ratelimit - Redis tu don, khong can tien trinh don rac rieng."""
    ask(client)
    fake = redis_client.get_redis()
    key = fake.keys("ratelimit:*")[0]
    ttl = fake.ttl(key)
    assert 0 < ttl <= api._RATE_WINDOW_SECONDS
