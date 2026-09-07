"""Test hai cai chan cua ban Streamlit - ban CONG KHAI that su chay cho nguoi dung.

api.py co rate limit theo IP, nhung cho so ho nam o app.py: no la ban dang chay
cong khai. Hai thu duoc test o day:

  1. thread_id tu URL phai la UUID  -> khong ai dat duoc khoa doan duoc
  2. ngan sach toan cuc theo gio    -> bao ve hoa don API key
"""

import importlib
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture
def app_module(monkeypatch):
    """Nap app.py ma KHONG dung agent that.

    st.cache_resource duoc thay bang mot cai cache gia: ban that cua Streamlit
    doi chay trong runtime co ScriptRunContext, con o day chi can mot ham nho
    ket qua giua cac lan goi.
    """
    import streamlit as st

    def fake_cache_resource(func=None, **_kwargs):
        def wrap(f):
            box = {}

            def inner(*a, **k):
                if "v" not in box:
                    box["v"] = f(*a, **k)
                return box["v"]

            return inner

        return wrap(func) if callable(func) else wrap

    monkeypatch.setattr(st, "cache_resource", fake_cache_resource)
    monkeypatch.setattr(st, "set_page_config", lambda **k: None)
    sys.modules.pop("app", None)
    # Chan phan giao dien: chi lay phan logic o dau file.
    monkeypatch.setattr(st, "chat_input", lambda *a, **k: None)
    monkeypatch.setattr(st, "title", lambda *a, **k: None)
    monkeypatch.setattr(st, "caption", lambda *a, **k: None)
    try:
        return importlib.import_module("app")
    finally:
        pass


# --------------------------------------------------------------------------
# 1. thread_id tu URL
# --------------------------------------------------------------------------

@pytest.mark.parametrize("bad", ["admin", "1", "", None, "../etc/passwd",
                                 "not-a-uuid", "11111111-2222-3333"])
def test_non_uuid_thread_is_rejected(app_module, bad):
    """Khong ep UUID thi ai cung dat duoc ?thread=admin va do la khoa doan duoc."""
    assert app_module._valid_thread(bad) is None


def test_real_uuid_is_accepted_and_normalised(app_module):
    assert app_module._valid_thread("3f2504e0-4f89-11d3-9a0c-0305e82c3301") == (
        "3f2504e0-4f89-11d3-9a0c-0305e82c3301"
    )
    # Chu hoa va chu thuong la cung mot thread, khong phai hai thread khac nhau.
    assert app_module._valid_thread("3F2504E0-4F89-11D3-9A0C-0305E82C3301") == (
        "3f2504e0-4f89-11d3-9a0c-0305e82c3301"
    )


# --------------------------------------------------------------------------
# 2. Ngan sach
# --------------------------------------------------------------------------

def test_budget_allows_questions_under_the_limit(app_module, monkeypatch):
    monkeypatch.setattr(app_module, "AI_ENABLED", True)
    monkeypatch.setattr(app_module, "GLOBAL_BUDGET_PER_HOUR", 3)
    app_module._global_hits().clear()
    assert app_module.check_budget() is None


def test_global_budget_blocks_even_a_brand_new_session(app_module, monkeypatch):
    """Mo tab moi lach duoc han muc phien, nhung KHONG lach duoc ngan sach chung.

    Day moi la lop chan that: no bao ve hoa don, khong bao ve su cong bang.
    """
    monkeypatch.setattr(app_module, "AI_ENABLED", True)
    monkeypatch.setattr(app_module, "GLOBAL_BUDGET_PER_HOUR", 2)
    hits = app_module._global_hits()
    hits.clear()
    now = time.time()
    hits.extend([now, now])
    assert "ngan sach" in app_module.check_budget()


def test_old_hits_fall_out_of_the_window(app_module, monkeypatch):
    """Cua so TRUOT: luot cach day hon mot gio khong duoc tinh nua."""
    monkeypatch.setattr(app_module, "AI_ENABLED", True)
    monkeypatch.setattr(app_module, "GLOBAL_BUDGET_PER_HOUR", 2)
    hits = app_module._global_hits()
    hits.clear()
    stale = time.time() - 3601
    hits.extend([stale, stale])
    assert app_module.check_budget() is None


def test_kill_switch_beats_every_other_check(app_module, monkeypatch):
    """AI_ENABLED=0 chan ngay ca khi ngan sach con nguyen."""
    monkeypatch.setattr(app_module, "AI_ENABLED", False)
    monkeypatch.setattr(app_module, "GLOBAL_BUDGET_PER_HOUR", 9999)
    app_module._global_hits().clear()
    assert "tam tat" in app_module.check_budget()
