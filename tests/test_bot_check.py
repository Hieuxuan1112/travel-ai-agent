"""Unit test cho bot_check.py - khong goi Cloudflare that."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("GOOGLE_API_KEY", "test-key-not-used")

import bot_check  # noqa: E402


class _FakeResponse:
    def __init__(self, success: bool):
        self._success = success

    def json(self):
        return {"success": self._success}


def _enable(monkeypatch):
    monkeypatch.setattr(bot_check, "TURNSTILE_SITE_KEY", "site-key")
    monkeypatch.setattr(bot_check, "TURNSTILE_SECRET_KEY", "secret-key")


def test_disabled_when_keys_not_configured(monkeypatch):
    monkeypatch.setattr(bot_check, "TURNSTILE_SITE_KEY", "")
    monkeypatch.setattr(bot_check, "TURNSTILE_SECRET_KEY", "")
    assert bot_check.is_enabled() is False
    assert bot_check.verify("") is True  # tat tinh nang -> luon cho qua


def test_verify_accepts_valid_token(monkeypatch):
    _enable(monkeypatch)
    monkeypatch.setattr(bot_check.requests, "post", lambda *a, **k: _FakeResponse(True))
    assert bot_check.verify("real-token") is True


def test_verify_rejects_invalid_token(monkeypatch):
    _enable(monkeypatch)
    monkeypatch.setattr(bot_check.requests, "post", lambda *a, **k: _FakeResponse(False))
    assert bot_check.verify("fake-token") is False


def test_verify_rejects_empty_token_when_enabled(monkeypatch):
    _enable(monkeypatch)
    assert bot_check.verify("") is False


def test_verify_fails_closed_on_network_error(monkeypatch):
    _enable(monkeypatch)

    def _boom(*a, **k):
        raise RuntimeError("network down")

    monkeypatch.setattr(bot_check.requests, "post", _boom)
    assert bot_check.verify("real-token") is False
