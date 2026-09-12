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


def test_llm_node_bo_qua_state_khong_co_plan(monkeypatch):
    """Khong co khoa 'plan' trong state (truong hop main_02_02.py/main_03_01.py
    dung binh thuong) thi system prompt khong duoc them gi ca."""
    fake = _FakeLLM()
    monkeypatch.setattr(lab, "llm_with_tools", fake)

    lab.llm_node({"messages": [HumanMessage(content="hello")]})

    assert fake.seen[0].content == lab.SYSTEM_PROMPT


def test_llm_node_them_ghi_chu_khi_planner_quyet_dinh_can_xep_hang(monkeypatch):
    """planner_node (main_05_multi_agent.py) ghi 'plan' vao state - llm_node phai
    doc duoc va them huong dan cu the vao system prompt cho luot nay."""
    fake = _FakeLLM()
    monkeypatch.setattr(lab, "llm_with_tools", fake)

    state = {
        "messages": [HumanMessage(content="pick 2 warm towns")],
        "plan": {
            "needs_town_ranking": True,
            "top_n": 2,
            "min_temp_c": 18.0,
            "max_temp_c": 28.0,
        },
    }
    lab.llm_node(state)

    prompt = fake.seen[0].content
    assert lab.SYSTEM_PROMPT in prompt
    assert "2" in prompt
    assert "18.0" in prompt and "28.0" in prompt
    assert "rank_town_candidates" in prompt


def test_llm_node_bo_qua_plan_khi_khong_can_xep_hang(monkeypatch):
    fake = _FakeLLM()
    monkeypatch.setattr(lab, "llm_with_tools", fake)

    state = {
        "messages": [HumanMessage(content="what can I do in St Ives?")],
        "plan": {"needs_town_ranking": False, "rationale": "single-town search"},
    }
    lab.llm_node(state)

    assert fake.seen[0].content == lab.SYSTEM_PROMPT


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
