"""Khoa quyen truy cap thread THEO API KEY (hang muc #8 - record access lock).

Chi co tac dung khi API_KEYS duoc cau hinh trong api.py. Khong dat API_KEYS ->
demo cong khai nhu truoc gio: thread_id (UUID 122 bit ngau nhien) la lop bao
ve duy nhat, giong het truoc - khong co gi de "so huu" khi khong ai dang
nhap bang danh tinh nao ca.

Khi API_KEYS duoc cau hinh: key nao CHAM (claim) thread_id truoc thi chi key
do moi tiep tuc duoc thread do - mot API key hop le khac khong the doc tiep
hoi thoai chi vi lo/doan trung thread_id cua nguoi khac.

Luu ben trong Postgres khi co DATABASE_URL (cung CSDL voi checkpointer, song
voi hoi thoai that su); khong co thi lui ve dict trong tien trinh - mat khi
restart, chi du cho demo/test, cung triet ly voi _hits trong api.py.

ponytail: mo mot connection Postgres moi cho MOI request thay vi dung chung
pool - don gian, dung y het eval_history.py da lam. Nang cap thanh connection
pool khi luu luong that su can (demo hien tai ~30 cau/gio).
"""

import hashlib
import os

_memory_owners: dict[str, str] = {}

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS thread_owners (
    thread_id TEXT PRIMARY KEY,
    key_hash TEXT NOT NULL
)
"""


def _hash_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


def _check_and_claim_memory(thread_id: str, key_hash: str) -> bool:
    existing = _memory_owners.setdefault(thread_id, key_hash)
    return existing == key_hash


def _check_and_claim_postgres(thread_id: str, key_hash: str) -> bool:
    import psycopg

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn, conn.cursor() as cur:
        cur.execute(_CREATE_TABLE_SQL)
        cur.execute(
            "INSERT INTO thread_owners (thread_id, key_hash) VALUES (%s, %s) "
            "ON CONFLICT (thread_id) DO NOTHING RETURNING key_hash",
            (thread_id, key_hash),
        )
        claimed_now = cur.fetchone()
        if claimed_now:
            conn.commit()
            return True
        cur.execute("SELECT key_hash FROM thread_owners WHERE thread_id = %s", (thread_id,))
        existing = cur.fetchone()
        return existing is not None and existing[0] == key_hash


def check_and_claim(thread_id: str, api_key: str) -> bool:
    """True neu key nay duoc phep dung thread_id nay (vua chiem lan dau, hoac
    da la chu cu). False neu thread_id da thuoc ve mot key khac.

    Loi ket noi Postgres KHONG duoc nuot: khac voi redis_client (lop toi uu,
    fail-open), day la lop CHAN QUYEN TRUY CAP - mat ket noi ma van cho qua
    thi coi nhu khong con khoa gi ca.
    """
    key_hash = _hash_key(api_key)
    if os.environ.get("DATABASE_URL", "").strip():
        return _check_and_claim_postgres(thread_id, key_hash)
    return _check_and_claim_memory(thread_id, key_hash)


def reset_for_tests() -> None:
    """Xoa bo dem trong tien trinh - chi goi trong test de moi test doc lap."""
    _memory_owners.clear()
