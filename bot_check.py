"""Chan bot bang Cloudflare Turnstile - widget CAPTCHA vo hinh, mien phi,
khong can the tin dung (hang muc #13). Dung cho app.py (giao dien nguoi that
dung tay go), KHONG dung cho api.py: do la REST API danh cho chuong trinh
goi, bat CAPTCHA o do la tu ban chan chinh minh.

Khong dat TURNSTILE_SECRET_KEY -> tat tinh nang nay, hanh vi nhu truoc (chi
con rate-limit/ngan sach da co san trong app.py) - cung triet ly voi
REDIS_URL/DATABASE_URL: khong bat buoc phai co tai khoan Cloudflare moi
chay thu duoc repo.
"""

import os

import requests

_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

# ponytail: doc os.environ BEN TRONG ham (khong phai o dau module) vi app.py
# import bot_check truoc khi main_02_02.load_dotenv() kip chay - doc o dau
# module se luon thay bien rong du .env co dien gi di nua. redis_client.py
# cung tranh loi nay theo dung cach nay (xem get_redis()).


def site_key() -> str:
    return os.environ.get("TURNSTILE_SITE_KEY", "").strip()


def _secret_key() -> str:
    return os.environ.get("TURNSTILE_SECRET_KEY", "").strip()


def is_enabled() -> bool:
    return bool(site_key() and _secret_key())


def verify(token: str) -> bool:
    """True neu token Turnstile hop le. Fail-CLOSED (khac redis_client/
    tts.py, la lop toi uu fail-open): day la lop CHAN LAM DUNG, mang loi
    hay Cloudflare loi thi tu choi an toan thay vi mo cong.
    """
    if not is_enabled():
        return True
    if not token:
        return False
    try:
        response = requests.post(
            _VERIFY_URL,
            data={"secret": _secret_key(), "response": token},
            timeout=5,
        )
        return bool(response.json().get("success"))
    except Exception as exc:
        print(f"   [bot_check] Turnstile siteverify that bai ({exc}) - tu choi an toan.")
        return False
