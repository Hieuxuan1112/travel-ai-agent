"""Test cho ban multi-agent (planner + executor) - chay offline, khong goi LLM that.

Ba dieu can chung minh:
  1. planner_node tra ve dung cau truc (dict rong khi khong co HumanMessage hoac
     khi model tra ve khong parse duoc).
  2. planner_node doc dung message MOI NHAT, khong bi lich su cu lam nhieu.
  3. Quyet dinh cua planner THAT SU toi duoc executor (khong phai nhan mac) -
     kiem chung bang cach chay ca graph da ghep va xem system prompt cua
     executor co doi theo dung "plan" ma planner tao ra khong.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("GOOGLE_API_KEY", "test-key-not-used")

from langchain_core.messages import AIMessage, HumanMessage  # noqa: E402

import main_02_02 as lab  # noqa: E402
import main_05_multi_agent as ma  # noqa: E402


class _FakeStructuredPlanner:
    """Gia lap ket qua cua with_structured_output(..., include_raw=True)."""

    def __init__(self, parsed, raw=None):
        self._parsed = parsed
        self._raw = raw or AIMessage(content="")
        self.seen_messages = None

    def invoke(self, messages):
        self.seen_messages = messages
        return {"raw": self._raw, "parsed": self._parsed}


def test_planner_no_human_message_returns_empty_plan():
    assert ma.planner_node({"messages": []}) == {"plan": {}}


def test_planner_returns_parsed_plan_as_dict(monkeypatch):
    plan = ma.TownRankingPlan(
        needs_town_ranking=True, top_n=3, min_temp_c=18.0, max_temp_c=26.0,
        rationale="user wants 3 warm towns",
    )
    monkeypatch.setattr(ma, "_planner_structured", _FakeStructuredPlanner(plan))

    result = ma.planner_node({"messages": [HumanMessage(content="pick 3 warm towns")]})

    assert result["plan"]["needs_town_ranking"] is True
    assert result["plan"]["top_n"] == 3
    assert result["plan"]["min_temp_c"] == 18.0
    assert result["plan"]["max_temp_c"] == 26.0


def test_planner_returns_empty_plan_when_parsing_fails(monkeypatch):
    monkeypatch.setattr(ma, "_planner_structured", _FakeStructuredPlanner(parsed=None))

    result = ma.planner_node({"messages": [HumanMessage(content="hello")]})
    assert result == {"plan": {}}


def test_planner_uses_the_latest_human_message_not_an_earlier_one(monkeypatch):
    plan = ma.TownRankingPlan(needs_town_ranking=False, rationale="single town")
    fake = _FakeStructuredPlanner(plan)
    monkeypatch.setattr(ma, "_planner_structured", fake)

    ma.planner_node({"messages": [
        HumanMessage(content="first question"),
        AIMessage(content="first answer"),
        HumanMessage(content="second question"),
    ]})

    assert fake.seen_messages[-1].content == "second question"


def test_supervised_agent_actually_passes_the_plan_to_the_executor(monkeypatch):
    """Chung minh planner khong phai nhan mac: quyet dinh needs_town_ranking=True
    voi top_n/min_temp_c/max_temp_c cu the phai xuat hien trong system prompt
    ma executor (llm_node ben trong main_02_02) thuc su gui cho model."""
    plan = ma.TownRankingPlan(
        needs_town_ranking=True, top_n=2, min_temp_c=15.0, max_temp_c=25.0,
        rationale="comparison question",
    )
    monkeypatch.setattr(ma, "_planner_structured", _FakeStructuredPlanner(plan))

    seen_prompts = []

    class _FakeExecutorLLM:
        def invoke(self, messages):
            seen_prompts.append(messages[0].content)
            return AIMessage(content="done")

    monkeypatch.setattr(lab, "llm_with_tools", _FakeExecutorLLM())

    ma.travel_info_agent.invoke(
        {"messages": [HumanMessage(content="pick 2 warm towns")], "plan": {}}
    )

    assert seen_prompts, "executor's llm_node was never reached"
    assert "rank_town_candidates" in seen_prompts[0]
    assert "2" in seen_prompts[0]
    assert "15.0" in seen_prompts[0] and "25.0" in seen_prompts[0]


def test_supervised_agent_leaves_prompt_unchanged_when_ranking_not_needed(monkeypatch):
    plan = ma.TownRankingPlan(needs_town_ranking=False, rationale="single-town search")
    monkeypatch.setattr(ma, "_planner_structured", _FakeStructuredPlanner(plan))

    seen_prompts = []

    class _FakeExecutorLLM:
        def invoke(self, messages):
            seen_prompts.append(messages[0].content)
            return AIMessage(content="done")

    monkeypatch.setattr(lab, "llm_with_tools", _FakeExecutorLLM())

    ma.travel_info_agent.invoke(
        {"messages": [HumanMessage(content="what can I do in St Ives?")], "plan": {}}
    )

    assert seen_prompts[0] == lab.SYSTEM_PROMPT
