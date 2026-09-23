"""Xac nhan cac security header dung tren MOI response, ke ca /healthz (khong
qua bat ky dependency nao) - middleware phai ap dung o tang app, khong phai
gan vao tung route."""

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("GOOGLE_API_KEY", "test-key-not-used")

import api  # noqa: E402


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(api.lab, "get_travel_info_vectorstore", lambda: None)
    monkeypatch.setattr(api.persistence, "get_checkpointer", lambda: None)
    monkeypatch.setattr(api.persistence, "backend_name", lambda: "in-memory")
    with TestClient(api.app) as test_client:
        yield test_client


def test_security_headers_present_on_healthz(client):
    response = client.get("/healthz")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert "max-age" in response.headers["Strict-Transport-Security"]
