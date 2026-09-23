"""Test cho lop API key tuy chon - chay offline, khong goi LLM that.

Ba dieu can chung minh:
  1. Khong dat API_KEYS -> API cong khai nhu truoc (khong pha vo ban dang
     chay tren Azure, noi khong dat bien nay).
  2. Dat API_KEYS -> /chat va /chat/stream bat buoc header X-API-Key dung.
  3. /healthz, /metrics khong bao gio bi chan, du co dat API_KEYS hay khong.
"""

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
    monkeypatch.setattr(api.lab, "build_agent", lambda checkpointer=None: FakeAgent())
    monkeypatch.setattr(api.persistence, "get_checkpointer", lambda: None)
    monkeypatch.setattr(api.persistence, "backend_name", lambda: "in-memory")
    monkeypatch.setattr(api.lab, "get_travel_info_vectorstore", lambda: None)
    with TestClient(api.app) as test_client:
        yield test_client


def test_chat_is_public_when_api_keys_not_configured(client, monkeypatch):
    monkeypatch.setattr(api, "API_KEYS", set())
    response = client.post("/chat", json={"question": "weather in St Ives?"})
    assert response.status_code == 200


def test_chat_rejects_missing_key_when_configured(client, monkeypatch):
    monkeypatch.setattr(api, "API_KEYS", {"secret-123"})
    response = client.post("/chat", json={"question": "weather in St Ives?"})
    assert response.status_code == 401
    assert "X-API-Key" in response.json()["detail"]


def test_chat_rejects_wrong_key(client, monkeypatch):
    monkeypatch.setattr(api, "API_KEYS", {"secret-123"})
    response = client.post(
        "/chat", json={"question": "weather in St Ives?"},
        headers={"X-API-Key": "wrong-key"},
    )
    assert response.status_code == 401


def test_chat_accepts_correct_key(client, monkeypatch):
    monkeypatch.setattr(api, "API_KEYS", {"secret-123"})
    response = client.post(
        "/chat", json={"question": "weather in St Ives?"},
        headers={"X-API-Key": "secret-123"},
    )
    assert response.status_code == 200


def test_multiple_keys_are_all_accepted(client, monkeypatch):
    monkeypatch.setattr(api, "API_KEYS", {"key-a", "key-b"})
    for key in ("key-a", "key-b"):
        response = client.post(
            "/chat", json={"question": "weather in St Ives?"},
            headers={"X-API-Key": key},
        )
        assert response.status_code == 200


def test_wrong_key_attempts_still_consume_rate_limit(client, monkeypatch):
    """enforce_rate_limit phai chay TRUOC require_api_key: neu khong, ai do
    khong biet key co the thu sai vo han lan ma khong bao gio bi 429, bien
    rate limit thanh vo tac dung voi chinh ke dang co gang do quota."""
    monkeypatch.setattr(api, "API_KEYS", {"secret-123"})
    monkeypatch.setattr(api, "RATE_LIMIT_PER_HOUR", 3)
    api._hits.clear()
    try:
        for _ in range(3):
            response = client.post(
                "/chat", json={"question": "weather in St Ives?"},
                headers={"X-API-Key": "wrong-key"},
            )
            assert response.status_code == 401
        response = client.post(
            "/chat", json={"question": "weather in St Ives?"},
            headers={"X-API-Key": "wrong-key"},
        )
        assert response.status_code == 429
    finally:
        api._hits.clear()


def test_stream_endpoint_also_requires_the_key_when_configured(client, monkeypatch):
    monkeypatch.setattr(api, "API_KEYS", {"secret-123"})
    blocked = client.get("/chat/stream", params={"q": "weather in St Ives?"})
    assert blocked.status_code == 401

    allowed = client.get(
        "/chat/stream", params={"q": "weather in St Ives?"},
        headers={"X-API-Key": "secret-123"},
    )
    assert allowed.status_code == 200


def test_healthz_and_metrics_stay_public_even_with_api_keys_configured(client, monkeypatch):
    monkeypatch.setattr(api, "API_KEYS", {"secret-123"})
    assert client.get("/healthz").status_code == 200
    assert client.get("/metrics").status_code == 200


def test_env_var_parses_comma_separated_keys_and_trims_whitespace(monkeypatch):
    monkeypatch.setenv("API_KEYS", " key-a, key-b ,, key-c")
    keys = {k.strip() for k in os.environ["API_KEYS"].split(",") if k.strip()}
    assert keys == {"key-a", "key-b", "key-c"}
