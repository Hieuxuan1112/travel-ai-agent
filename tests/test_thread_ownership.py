"""Unit test cho thread_ownership.py - chi test nhanh in-memory (khong
DATABASE_URL), nhanh Postgres da co precedent giong het trong eval_history.py."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("GOOGLE_API_KEY", "test-key-not-used")
os.environ.pop("DATABASE_URL", None)  # dam bao dung nhanh in-memory

import thread_ownership  # noqa: E402


def setup_function():
    thread_ownership.reset_for_tests()


def test_first_use_claims_the_thread():
    assert thread_ownership.check_and_claim("thread-1", "key-a") is True


def test_same_key_can_keep_using_its_own_thread():
    thread_ownership.check_and_claim("thread-1", "key-a")
    assert thread_ownership.check_and_claim("thread-1", "key-a") is True


def test_different_key_is_rejected():
    thread_ownership.check_and_claim("thread-1", "key-a")
    assert thread_ownership.check_and_claim("thread-1", "key-b") is False


def test_unrelated_threads_do_not_interfere():
    thread_ownership.check_and_claim("thread-1", "key-a")
    assert thread_ownership.check_and_claim("thread-2", "key-b") is True
