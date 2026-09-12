"""Test cho evals/history_report.py - dac biet la bug run_at kieu datetime that
(Postgres tra ve datetime object, khac SQLite tra ve chuoi ISO da luu san)."""

import os
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals"))
os.environ.setdefault("GOOGLE_API_KEY", "test-key-not-used")

import history_report  # noqa: E402

import eval_history  # noqa: E402


def test_report_formats_a_real_datetime_run_at_without_crashing(monkeypatch, capsys):
    """Postgres tra ve run_at la datetime that, khong phai chuoi - dinh dang
    "{value:<26}" tren mot datetime se dien giai sai thanh pattern strftime
    (":<26" khong phai directive hop le) neu khong ep ve str truoc."""
    fake_row = {
        "run_at": datetime(2026, 9, 12, 10, 22, 7, tzinfo=UTC),
        "git_sha": "85c4ba6",
        "dataset_size": 31,
        "tool_accuracy": 1.0,
        "judge_score": 4.6,
        "cost_per_1k_usd": 1.39,
    }
    monkeypatch.setattr(eval_history, "recent_runs", lambda limit=10: [fake_row])
    monkeypatch.setattr(eval_history, "backend_name", lambda: "postgres")

    history_report.main(limit=5)

    output = capsys.readouterr().out
    assert "2026-09-12" in output
    assert "<26" not in output  # bug cu: format spec bi in ra nguyen van
    assert "85c4ba6" in output
    assert "100%" in output


def test_report_handles_missing_cost(monkeypatch, capsys):
    fake_row = {
        "run_at": "2026-09-12T10:00:00",
        "git_sha": None,
        "dataset_size": 8,
        "tool_accuracy": 0.85,
        "judge_score": 3.7,
        "cost_per_1k_usd": None,
    }
    monkeypatch.setattr(eval_history, "recent_runs", lambda limit=10: [fake_row])
    monkeypatch.setattr(eval_history, "backend_name", lambda: "sqlite")

    history_report.main(limit=5)

    output = capsys.readouterr().out
    assert "n/a" in output


def test_report_handles_empty_history(monkeypatch, capsys):
    monkeypatch.setattr(eval_history, "recent_runs", lambda limit=10: [])
    monkeypatch.setattr(eval_history, "backend_name", lambda: "sqlite")

    history_report.main(limit=5)

    assert "Chua co lich su" in capsys.readouterr().out
