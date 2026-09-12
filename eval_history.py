"""Luu lich su cac lan chay eval THEO THOI GIAN - schema don gian, khong ORM.

evals/results.md va results.json bi GHI DE moi lan chay eval_agent.py, nen
khong the tra loi "chat luong co tut theo thoi gian khong" bang du lieu that,
chi bang cam tinh. Module nay them mot bang eval_runs de tra loi cau hoi do.

Backend chon giong het persistence.py: co DATABASE_URL (cung Neon voi
checkpointer hoi thoai) thi dung Postgres; khong co thi dung SQLite cuc bo
(evals/eval_history.db, gitignore - lich su rieng cho tung may, khong dung
chung qua git). Loi ghi lich su KHONG duoc lam hong ket qua eval chinh - chi
canh bao ra man hinh.
"""

import os
import sqlite3
import subprocess
from datetime import UTC, datetime
from pathlib import Path

_SQLITE_PATH = Path(__file__).parent / "evals" / "eval_history.db"

_CREATE_SQLITE = """
CREATE TABLE IF NOT EXISTS eval_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_at TEXT NOT NULL,
    git_sha TEXT,
    model TEXT NOT NULL,
    dataset_size INTEGER NOT NULL,
    tool_accuracy REAL NOT NULL,
    judge_score REAL NOT NULL,
    avg_latency_s REAL,
    cost_per_1k_usd REAL
)
"""

_CREATE_POSTGRES = """
CREATE TABLE IF NOT EXISTS eval_runs (
    id BIGSERIAL PRIMARY KEY,
    run_at TIMESTAMPTZ NOT NULL,
    git_sha TEXT,
    model TEXT NOT NULL,
    dataset_size INTEGER NOT NULL,
    tool_accuracy DOUBLE PRECISION NOT NULL,
    judge_score DOUBLE PRECISION NOT NULL,
    avg_latency_s DOUBLE PRECISION,
    cost_per_1k_usd DOUBLE PRECISION
)
"""

_INSERT_COLUMNS = (
    "run_at, git_sha, model, dataset_size, tool_accuracy, judge_score, "
    "avg_latency_s, cost_per_1k_usd"
)


def backend_name() -> str:
    """"postgres" hay "sqlite" - cung tieu chi voi persistence.backend_name()."""
    return "postgres" if os.environ.get("DATABASE_URL", "").strip() else "sqlite"


def _git_sha() -> str | None:
    """Best-effort: khong co git (vd tai ve dang zip) thi tra None, khong loi."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL, text=True, timeout=5,
        ).strip()
    except Exception:
        return None


def record_run(
    model: str,
    dataset_size: int,
    tool_accuracy: float,
    judge_score: float,
    avg_latency_s: float | None = None,
    cost_per_1k_usd: float | None = None,
) -> None:
    """Ghi mot dong lich su. Khong bao gio nem loi ra ngoai - mot lan eval that
    bai vi khong ghi duoc DB la vo ly, chi in canh bao va di tiep."""
    row = (
        datetime.now(UTC).isoformat(),
        _git_sha(),
        model,
        dataset_size,
        tool_accuracy,
        judge_score,
        avg_latency_s,
        cost_per_1k_usd,
    )
    try:
        if backend_name() == "postgres":
            _record_postgres(row)
        else:
            _record_sqlite(row)
    except Exception as exc:
        print(f"   [eval_history] khong ghi duoc lich su ({backend_name()}): {exc}")


def _record_sqlite(row: tuple) -> None:
    conn = sqlite3.connect(_SQLITE_PATH)
    try:
        conn.execute(_CREATE_SQLITE)
        conn.execute(
            f"INSERT INTO eval_runs ({_INSERT_COLUMNS}) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            row,
        )
        conn.commit()
    finally:
        conn.close()


def _record_postgres(row: tuple) -> None:
    import psycopg

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn, conn.cursor() as cur:
        cur.execute(_CREATE_POSTGRES)
        cur.execute(
            f"INSERT INTO eval_runs ({_INSERT_COLUMNS}) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            row,
        )
        conn.commit()


def recent_runs(limit: int = 10) -> list[dict]:
    """N lan chay gan nhat, moi nhat truoc - de xem xu huong chat luong."""
    if backend_name() == "postgres":
        return _recent_postgres(limit)
    return _recent_sqlite(limit)


def _recent_sqlite(limit: int) -> list[dict]:
    conn = sqlite3.connect(_SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute(_CREATE_SQLITE)
        rows = conn.execute(
            "SELECT * FROM eval_runs ORDER BY run_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def _recent_postgres(limit: int) -> list[dict]:
    import psycopg
    from psycopg.rows import dict_row

    with psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(_CREATE_POSTGRES)
            cur.execute("SELECT * FROM eval_runs ORDER BY run_at DESC LIMIT %s", (limit,))
            return cur.fetchall()
