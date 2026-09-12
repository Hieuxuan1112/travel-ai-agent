"""Test cho redis_client.py - chay offline, khong can Redis that.

fakeredis gia lap giao thuc Redis trong bo nho, dung cho cac test can mot
client "that" (co the goi .ping()/.get()/.setex()...); test o day chi kiem
tra logic chon backend + lui ve an toan, khong test ban than thu vien redis.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import redis_client  # noqa: E402


def test_no_redis_url_returns_none(monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)
    redis_client.reset_for_tests()

    assert redis_client.get_redis() is None


def test_empty_redis_url_is_treated_as_not_set(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "   ")
    redis_client.reset_for_tests()

    assert redis_client.get_redis() is None


def test_unreachable_redis_url_falls_back_to_none_not_exception(monkeypatch):
    """URL co dinh dang dung nhung khong co gi lang nghe - phai lui ve None,
    khong duoc de exception roi len lam sap ca service."""
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:1")  # port khong ai dung
    redis_client.reset_for_tests()

    assert redis_client.get_redis() is None


def test_client_is_cached_after_first_successful_call(monkeypatch):
    import fakeredis

    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client.reset_for_tests()

    fake = fakeredis.FakeRedis()
    monkeypatch.setattr("redis.from_url", lambda *a, **k: fake)

    first = redis_client.get_redis()
    second = redis_client.get_redis()

    assert first is fake
    assert second is fake  # cung mot object - khong tao lai moi lan goi


def test_reset_for_tests_forces_a_fresh_lookup(monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)
    redis_client.reset_for_tests()
    assert redis_client.get_redis() is None

    import fakeredis

    fake = fakeredis.FakeRedis()
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setattr("redis.from_url", lambda *a, **k: fake)
    redis_client.reset_for_tests()

    assert redis_client.get_redis() is fake
