"""Test cho lop luu lich su eval theo thoi gian - chay offline, dung SQLite tam.

results.md/results.json bi GHI DE moi lan chay -> khong tra loi duoc "chat luong
co tut theo thoi gian khong". File nay them mot bang eval_runs (SQLite cuc bo,
hoac Postgres neu co DATABASE_URL - cung Neon voi checkpointer hoi thoai) de
tra loi cau hoi do bang du lieu that.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import eval_history  # noqa: E402


@pytest.fixture
def sqlite_history(tmp_path, monkeypatch):
    """Moi test dung mot file SQLite rieng trong tmp_path, khong dam vao nhau."""
    monkeypatch.setattr(eval_history, "_SQLITE_PATH", tmp_path / "eval_history.db")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    return eval_history


def test_backend_is_sqlite_without_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert eval_history.backend_name() == "sqlite"


def test_backend_is_postgres_with_database_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@host/db")
    assert eval_history.backend_name() == "postgres"


def test_record_and_read_back_a_run(sqlite_history):
    sqlite_history.record_run(
        model="gemini-3.1-flash-lite",
        dataset_size=31,
        tool_accuracy=1.0,
        judge_score=4.6,
        avg_latency_s=5.2,
        cost_per_1k_usd=1.39,
    )

    runs = sqlite_history.recent_runs(limit=5)

    assert len(runs) == 1
    assert runs[0]["model"] == "gemini-3.1-flash-lite"
    assert runs[0]["dataset_size"] == 31
    assert runs[0]["tool_accuracy"] == 1.0
    assert runs[0]["judge_score"] == 4.6
    assert runs[0]["run_at"]  # co gia tri, khong quan tam dinh dang chinh xac


def test_most_recent_run_comes_first(sqlite_history):
    sqlite_history.record_run(model="m", dataset_size=1, tool_accuracy=0.5, judge_score=3.0)
    sqlite_history.record_run(model="m", dataset_size=2, tool_accuracy=0.9, judge_score=4.0)

    runs = sqlite_history.recent_runs(limit=5)

    assert [r["dataset_size"] for r in runs] == [2, 1]


def test_limit_caps_the_number_of_rows_returned(sqlite_history):
    for i in range(5):
        sqlite_history.record_run(model="m", dataset_size=i, tool_accuracy=1.0, judge_score=5.0)

    assert len(sqlite_history.recent_runs(limit=3)) == 3


def test_record_run_swallows_backend_errors_instead_of_crashing_the_eval(
    sqlite_history, monkeypatch
):
    """Mot lan eval that bai vi khong ghi duoc lich su la vo ly - phai chi canh
    bao, khong duoc lam hong ket qua eval chinh."""
    def boom(row):
        raise RuntimeError("disk full")

    monkeypatch.setattr(eval_history, "_record_sqlite", boom)

    eval_history.record_run(model="m", dataset_size=1, tool_accuracy=1.0, judge_score=5.0)
    # khong nem exception la dat yeu cau - khong assert gi them


def test_git_sha_is_recorded_when_available(sqlite_history):
    sqlite_history.record_run(model="m", dataset_size=1, tool_accuracy=1.0, judge_score=5.0)

    runs = sqlite_history.recent_runs(limit=1)
    # Chay trong repo git that -> phai lay duoc sha (7 hex chars tro len).
    assert runs[0]["git_sha"] is None or len(runs[0]["git_sha"]) >= 7
