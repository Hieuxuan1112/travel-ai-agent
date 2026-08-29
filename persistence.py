"""Noi luu state hoi thoai cua agent (LangGraph checkpointer).

  co DATABASE_URL    -> PostgresSaver: hoi thoai song qua F5, qua restart server,
                        qua ca viec doi may. Day la duong chay that.
  khong co           -> InMemorySaver: state nam trong RAM tien trinh, mat khi
                        restart.

Vi sao KHONG bat buoc DATABASE_URL: CI khong co database, va bat buoc no thi
nguoi clone repo ve khong chay thu duoc ngay. Thieu bien -> tu dong lui ve
InMemorySaver, khong nem loi.
"""

import os

from langgraph.checkpoint.memory import InMemorySaver

_checkpointer = None
_backend = ""


def get_checkpointer():
    """Checkpointer dung chung ca tien trinh. Tao mot lan roi cache lai.

    Cache o day chu khong de nguoi goi tu lo: PostgresSaver om mot connection
    pool, moi lan goi ma tao pool moi la ro ri connection.
    """
    global _checkpointer, _backend
    if _checkpointer is not None:
        return _checkpointer

    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        _checkpointer, _backend = InMemorySaver(), "in-memory"
        return _checkpointer

    from langgraph.checkpoint.postgres import PostgresSaver
    from psycopg.rows import dict_row
    from psycopg_pool import ConnectionPool

    pool = ConnectionPool(
        conninfo=url,
        # min_size=0: khong om connection nao luc ranh -> Neon moi ngu duoc,
        # ma ngu thi khong dot gio compute cua goi free.
        min_size=0,
        max_size=4,
        # Neon ngu sau 5 phut -> connection trong pool thanh connection chet.
        # check bat pool thu connection truoc khi giao ra, chet thi mo lai,
        # thay vi de request dau tien sau khi ngu bi loi.
        check=ConnectionPool.check_connection,
        # Ba tham so nay khong phai tuy chon: PostgresSaver.from_conn_string
        # cua LangGraph dung dung bo nay. prepare_threshold=0 con bat buoc khi
        # di qua connection pooler cua Neon (pgbouncer khong giu prepared stmt).
        kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
        open=True,
    )
    saver = PostgresSaver(pool)
    saver.setup()  # tao bang o lan chay dau; nhung lan sau la no-op
    _checkpointer, _backend = saver, "postgres"
    return _checkpointer


def backend_name() -> str:
    """"postgres" hay "in-memory" - de giao dien noi that no dang luu o dau."""
    if _checkpointer is None:
        get_checkpointer()
    return _backend
