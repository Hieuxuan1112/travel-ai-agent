"""Bien the multi-agent nhe: planner + executor, ghep bang LangGraph subgraph.

Khac voi main_02_02.py (mot agent ReAct duy nhat quyet dinh tat ca), file nay
tach thanh HAI vai tro:

  planner   - doc CAU HOI MOI NHAT cua user, quyet dinh cau hoi nay co can
              XEP HANG nhieu town theo thoi tiet khong, va neu co thi bao
              nhieu town (top_n) + tieu chi nhiet do nao. KHONG goi tool nao,
              KHONG tra loi user - chi ra quyet dinh (structured output qua
              Pydantic, khong phai doan tu van ban tu do).
  executor  - CHINH LA graph ReAct co san trong main_02_02.py (build_agent()),
              dung nguyen khong sua, duoc ghep vao lam MOT NODE cua graph cha.
              Day la support-graph-as-node that su cua LangGraph, khong phai
              hai ham Python goi tuan tu gia lam "multi-agent".

Vi sao planner co that: quyet dinh cua no (vd top_n=3, target 20-25C) duoc
doc lai trong main_02_02.llm_node() va bien thanh mot doan huong dan cu the
them vao system prompt CHO LUOT DO - xem test_persistence.py::test_llm_node_*.
Khong co planner, agent van chay dung (plan rong -> khong doi gi), nhung khi
co planner, no thuc su thay doi cach executor hanh dong, khong phai nhan mac.

Chay:  venv\\Scripts\\python.exe main_05_multi_agent.py "cau hoi"
"""

import operator
import sys
from collections.abc import Sequence
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

import main_02_02 as lab
import metrics

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ===========================================================================
# STATE cua graph cha: y het AgentState cua main_02_02 (chia se khoa "messages"
# de subgraph doc/ghi duoc), them mot khoa rieng "plan" ma chi graph cha va
# planner_node dung - executor subgraph khong biet ve khoa nay, van chay binh
# thuong vi no chi dong tren "messages".
# ===========================================================================

class SupervisedState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    plan: dict


# ===========================================================================
# PLANNER - mot lan goi LLM rieng, RIENG khoi vong ReAct, ep output qua
# Pydantic (khong phai parse text tu do) de quyet dinh luon co cau truc dung
# duoc, khong can regex doan y model.
# ===========================================================================

class TownRankingPlan(BaseModel):
    needs_town_ranking: bool = Field(
        description="True if answering requires comparing/choosing among two or "
                    "more candidate towns by current weather."
    )
    top_n: int = Field(default=2, ge=1, le=5, description="How many towns to recommend.")
    min_temp_c: float | None = Field(
        default=None, description="User's stated minimum acceptable temperature in "
                                   "Celsius, if any."
    )
    max_temp_c: float | None = Field(
        default=None, description="User's stated maximum acceptable temperature in "
                                   "Celsius, if any."
    )
    rationale: str = Field(description="One sentence explaining the decision.")


PLANNER_SYSTEM_PROMPT = """You are the planning stage of a two-stage travel assistant.
Read only the user's latest message and decide whether answering it requires
comparing or choosing among two or more candidate Cornwall towns by current
weather (e.g. "suggest two towns", "which town should I visit", "pick a warm
beach town"). A single-town question ("weather in St Ives?") or a pure
information lookup ("tell me about surfing in Cornwall") does not need ranking.
Do not answer the user's question yourself and do not call any tools - only
produce the plan."""

planner_llm = ChatGoogleGenerativeAI(model=lab.CHAT_MODEL, temperature=0)
_planner_structured = planner_llm.with_structured_output(TownRankingPlan, include_raw=True)


def planner_node(state: SupervisedState) -> dict:
    last_human = next(
        (m for m in reversed(state["messages"]) if isinstance(m, HumanMessage)), None
    )
    if last_human is None:
        return {"plan": {}}

    response = _planner_structured.invoke(
        [SystemMessage(content=PLANNER_SYSTEM_PROMPT), last_human]
    )
    metrics.record_llm_usage(lab.CHAT_MODEL, getattr(response["raw"], "usage_metadata", None))

    parsed: TownRankingPlan | None = response["parsed"]
    plan = parsed.model_dump() if parsed is not None else {}
    print(f"   [planner] {plan}")
    return {"plan": plan}


# ===========================================================================
# GHEP GRAPH: planner (node moi) -> executor (graph co san cua main_02_02,
# dung lam mot node) -> END.
# ===========================================================================

executor_graph = lab.build_agent()  # khong checkpointer o day, giong travel_info_agent goc

supervisor_builder = StateGraph(SupervisedState)
supervisor_builder.add_node("planner", planner_node)
supervisor_builder.add_node("executor", executor_graph)
supervisor_builder.set_entry_point("planner")
supervisor_builder.add_edge("planner", "executor")
supervisor_builder.add_edge("executor", END)


def build_supervised_agent(checkpointer=None):
    """Lap rap ban co planner. Truyen checkpointer y het build_agent() goc."""
    return supervisor_builder.compile(checkpointer=checkpointer)


travel_info_agent = build_supervised_agent()


def ask(question: str) -> str:
    state = {"messages": [HumanMessage(content=question)], "plan": {}}
    result = travel_info_agent.invoke(state)
    return lab.answer_text(result["messages"][-1])


def chat_loop():
    print("UK Travel Assistant - planner + executor (type 'exit' to quit)")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break
        if not user_input:
            continue
        print(f"Assistant: {ask(user_input)}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(f"You: {sys.argv[1]}")
        print(f"Assistant: {ask(sys.argv[1])}")
    else:
        chat_loop()
