"""Do chat luong agent tren mot bo cau hoi chuan.

Hai chi so:
  1. Tool-selection accuracy - agent co goi DUNG tool can thiet khong (cham tu dong,
     doc tu lich su message chu khong doan).
  2. Answer quality (LLM-as-judge) - mot LLM khac cham cau tra loi tu 1 den 5.

Chay:  venv\\Scripts\\python.exe evals\\eval_agent.py
Ket qua ghi ra evals/results.md
"""

import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from langchain_core.messages import AIMessage, HumanMessage  # noqa: E402

import main_02_02 as lab  # noqa: E402

DATASET = [
    ("Tell me about surfing in Cornwall", {"search_travel_info"}),
    ("What can I do in St Ives?", {"search_travel_info"}),
    ("Suggest three towns with a nice beach in Cornwall", {"search_travel_info"}),
    ("What is the weather in Falmouth, Cornwall right now?", {"weather_forecast"}),
    ("Compare the weather in Newquay and Penzance", {"weather_forecast"}),
    ("Suggest two Cornwall beach towns with nice weather",
     {"search_travel_info", "weather_forecast"}),
    ("I want a surfing town in Cornwall where it is not raining today",
     {"search_travel_info", "weather_forecast"}),
    ("Which Cornwall coastal town should I visit today based on the weather?",
     {"search_travel_info", "weather_forecast"}),
]

JUDGE_PROMPT = """You are grading a travel assistant's answer.

Question: {question}
Answer: {answer}

Score the answer from 1 to 5 on being helpful, concrete and grounded in real data
(named towns, real weather numbers). Reply with the digit only."""


def called_tools(messages) -> list[str]:
    """Doc lich su message de biet agent da goi nhung tool nao."""
    names = []
    for message in messages:
        if isinstance(message, AIMessage):
            names.extend(call["name"] for call in message.tool_calls or [])
    return names


def with_retry(fn, attempts: int = 3):
    """API doi khi tra 429/503 -> thu lai vai lan de mot loi tam thoi khong huy ca eval."""
    for attempt in range(attempts):
        try:
            return fn()
        except Exception as exc:
            if attempt == attempts - 1:
                raise
            print(f"    retry {attempt + 1}/{attempts - 1} after: {str(exc)[:80]}")
            time.sleep(5 * (attempt + 1))


def judge(question: str, answer: str) -> int:
    raw = lab.llm_model.invoke(JUDGE_PROMPT.format(question=question, answer=answer))
    match = re.search(r"[1-5]", lab.answer_text(raw))
    return int(match.group()) if match else 0


def main() -> None:
    lab.get_travel_info_vectorstore()
    rows = []

    for question, expected in DATASET:
        started = time.time()
        result = with_retry(
            lambda q=question: lab.travel_info_agent.invoke(
                {"messages": [HumanMessage(content=q)]}
            )
        )
        elapsed = time.time() - started

        tools = called_tools(result["messages"])
        answer = lab.answer_text(result["messages"][-1])
        passed = expected.issubset(set(tools))
        score = with_retry(lambda q=question, a=answer: judge(q, a))

        rows.append((question, expected, tools, passed, score, elapsed))
        print(f"[{'PASS' if passed else 'FAIL'}] {score}/5  {elapsed:5.1f}s  {question}")

    accuracy = sum(r[3] for r in rows) / len(rows)
    avg_score = sum(r[4] for r in rows) / len(rows)
    avg_time = sum(r[5] for r in rows) / len(rows)

    report = [
        "# Agent evaluation",
        "",
        f"Model: `{lab.CHAT_MODEL}` · weather source: `{lab.WEATHER_MODE}` · "
        f"{len(rows)} test cases",
        "",
        "| Metric | Result |",
        "| --- | --- |",
        f"| Tool-selection accuracy | **{accuracy:.0%}** |",
        f"| Answer quality (LLM-as-judge, 1-5) | **{avg_score:.1f}** |",
        f"| Average latency | {avg_time:.1f}s |",
        "",
        "| Question | Expected tools | Tools actually called | Pass | Score |",
        "| --- | --- | --- | :-: | :-: |",
    ]
    for question, expected, tools, passed, score, _ in rows:
        report.append(
            f"| {question} | {', '.join(sorted(expected))} | {', '.join(tools) or '-'} "
            f"| {'yes' if passed else 'no'} | {score}/5 |"
        )

    out = Path(__file__).parent / "results.md"
    out.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"\nTool-selection accuracy {accuracy:.0%} | judge {avg_score:.1f}/5 -> {out}")


if __name__ == "__main__":
    main()
