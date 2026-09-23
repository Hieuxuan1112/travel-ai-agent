"""Test cong tac ngat AI - thu bat buoc phai co de tat duoc tinh nang khi bi lam dung.

Rate limit chi lam CHAM ke lam dung. Khi dang bi lam dung that, hoac nha cung cap
doi gia, ta phai tat HAN duoc tinh nang AI ma khong build lai image.

Cai cong nay phai duoc test, vi mot cong hong theo kieu "luon cho qua" con te hon
khong co cong: van tuong minh dang tat trong khi hoa don van chay.
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
    api._hits.clear()
    with TestClient(api.app) as test_client:
        yield test_client
    api._hits.clear()


def test_chat_works_when_ai_is_enabled(client, monkeypatch):
    monkeypatch.setattr(api, "AI_ENABLED", True)
    assert client.post("/chat", json={"question": "weather in St Ives?"}).status_code == 200


def test_chat_returns_503_when_ai_is_disabled(client, monkeypatch):
    monkeypatch.setattr(api, "AI_ENABLED", False)
    response = client.post("/chat", json={"question": "weather in St Ives?"})
    assert response.status_code == 503
    # Retry-After bao cho client biet day la tam thoi, khong phai hong vinh vien.
    assert response.headers["Retry-After"] == "3600"


def test_stream_endpoint_is_disabled_too(client, monkeypatch):
    """Tat mot cua ma quen cua kia thi coi nhu chua tat."""
    monkeypatch.setattr(api, "AI_ENABLED", False)
    assert client.get("/chat/stream", params={"question": "weather in St Ives?"}).status_code == 503


def test_healthz_stays_green_when_ai_is_disabled(client, monkeypatch):
    """Tat AI la quyet dinh CO CHU Y, khong phai container chet.

    Neu /healthz do theo, Container Apps tuong container hong va khoi dong lai
    lien tuc - dung luc ta co y tat no di.
    """
    monkeypatch.setattr(api, "AI_ENABLED", False)
    assert client.get("/healthz").status_code == 200
    assert client.get("/metrics").status_code == 200


@pytest.mark.parametrize(
    "raw, expected",
    [("0", False), ("false", False), ("FALSE", False), ("no", False), (" 0 ", False),
     ("1", True), ("true", True), ("", True), ("yes", True)],
)
def test_env_var_parsing_accepts_the_obvious_spellings(raw, expected, monkeypatch):
    """Nguoi tat cong tac luc 3 gio sang khong nen phai doan chinh ta."""
    monkeypatch.setenv("AI_ENABLED", raw)
    value = os.environ.get("AI_ENABLED", "1").strip().lower() not in {"0", "false", "no"}
    assert value is expected
