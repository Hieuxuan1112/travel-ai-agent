"""Test cho lop luu hoi thoai - chay offline, khong can database, khong goi LLM.

Hai thu duoc canh o day:
  1. Thieu DATABASE_URL phai tu lui ve InMemorySaver. Neu no nem loi thi CI
     (khong co database) va nguoi moi clone repo ve deu chay khong duoc.
  2. Cua so cat lich su khong duoc dong toi mot luot hoi-dap binh thuong.
     llm_node dung chung cho ca api.py va evals - hai cho do chi gui MOT cau
     hoi, cat nham vao day la hong ca API lan diem eval.
"""

import os
import sys
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("GOOGLE_API_KEY", "test-key-not-used")

import main_02_02 as lab  # noqa: E402
import persistence  # noqa: E402


def _reset_persistence():
    """persistence cache checkpointer o bien module -> phai don giua cac test."""
    persistence._checkpointer = None
    persistence._backend = ""


def test_khong_co_database_url_thi_lui_ve_in_memory(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    _reset_persistence()

    assert isinstance(persistence.get_checkpointer(), InMemorySaver)
    assert persistence.backend_name() == "in-memory"


def test_database_url_rong_cung_coi_nhu_khong_co(monkeypatch):
    # Streamlit Cloud / Docker hay truyen bien rong thay vi bo han bien di.
    monkeypatch.setenv("DATABASE_URL", "   ")
    _reset_persistence()

    assert isinstance(persistence.get_checkpointer(), InMemorySaver)


def test_goi_hai_lan_tra_ve_cung_mot_checkpointer(monkeypatch):
    # Moi lan tao moi la moi lan mo them mot connection pool ra Neon.
    monkeypatch.delenv("DATABASE_URL", raising=False)
    _reset_persistence()

    assert persistence.get_checkpointer() is persistence.get_checkpointer()


def test_build_agent_khong_checkpointer_thi_khong_nho():
    assert lab.build_agent().checkpointer is None
    assert lab.build_agent(InMemorySaver()).checkpointer is not None


class _FakeLLM:
    """Ghi lai danh sach message that su duoc gui cho model."""

    def __init__(self):
        self.seen = None

    def invoke(self, messages):
        self.seen = messages
        return AIMessage(content="ok")


def test_mot_luot_hoi_dap_binh_thuong_khong_bi_cat(monkeypatch):
    fake = _FakeLLM()
    monkeypatch.setattr(lab, "llm_with_tools", fake)

    # Dung kich ban cua api.py: mot cau hoi, mot tool, mot cau tra loi.
    turn = [
        HumanMessage(content="weather in St Ives?"),
        AIMessage(content="", tool_calls=[
            {"name": "weather_forecast", "args": {"town": "St Ives"}, "id": "c1"}
        ]),
        ToolMessage(content="21.7", name="weather_forecast", tool_call_id="c1"),
    ]
    lab.llm_node({"messages": turn})

    assert isinstance(fake.seen[0], SystemMessage)
    assert fake.seen[1:] == turn  # nguyen ven, khong mat message nao


def test_hoi_thoai_dai_bi_cat_nhung_van_bat_dau_bang_luot_nguoi_dung(monkeypatch):
    fake = _FakeLLM()
    monkeypatch.setattr(lab, "llm_with_tools", fake)

    long_chat = []
    for i in range(40):
        long_chat.append(HumanMessage(content=f"cau hoi {i}"))
        long_chat.append(AIMessage(content=f"tra loi {i}"))
    lab.llm_node({"messages": long_chat})

    window = fake.seen[1:]  # bo SystemMessage duoc ghep them o dau
    assert len(window) < len(long_chat)
    assert len(window) <= lab.MAX_HISTORY_MESSAGES
    # Cat giua luot se bo lai ToolMessage mo coi -> Gemini tu choi ca request.
    assert isinstance(window[0], HumanMessage)
    # Cau hoi moi nhat bat buoc phai con.
    assert window[-1].content == "tra loi 39"
