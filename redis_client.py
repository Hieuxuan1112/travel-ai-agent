"""Redis client dung chung cho rate limit (api.py) va cache thoi tiet (main_02_02.py).

Khong dat REDIS_URL -> ca hai cho deu tu lui ve phuong an cu (bo dem trong
tien trinh cho rate limit, khong cache gi cho thoi tiet) - cung triet ly voi
persistence.py va DATABASE_URL: khong bat buoc nguoi clone repo phai co san
ha tang moi chay thu duoc.

Redis o day la TANG TOI UU (rate limit chia se giua nhieu instance, cache
giam goi API thoi tiet), KHONG PHAI duong song con: mat ket noi Redis thi
service van phai chay tiep, chi mat cac loi ich do - nen moi loi ket noi deu
duoc nuot va lui ve None thay vi nem exception.
"""

import os

_client = None
_checked = False


def get_redis():
    """Redis client dung chung ca tien trinh, cache lai sau lan dau.

    Tra None neu khong cau hinh REDIS_URL, hoac neu co cau hinh nhung khong
    ket noi duoc (network hong, sai URL, Redis chua bat...) - khong bao gio
    nem exception ra ngoai.
    """
    global _client, _checked
    if _checked:
        return _client
    _checked = True

    url = os.environ.get("REDIS_URL", "").strip()
    if not url:
        return None

    import redis as redis_lib

    client = redis_lib.from_url(url, socket_connect_timeout=2, socket_timeout=2)
    try:
        client.ping()
    except Exception as exc:
        print(f"   [redis] khong ket noi duoc REDIS_URL ({exc}) - lui ve khong dung Redis.")
        return None
    _client = client
    return _client


def reset_for_tests() -> None:
    """Xoa cache singleton - chi goi trong test de moi test doc lap voi nhau."""
    global _client, _checked
    _client = None
    _checked = False
