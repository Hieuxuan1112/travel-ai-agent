"""Do chat luong agent tren mot bo cau hoi chuan.

Hai chi so:
  1. Tool-selection accuracy - agent co goi DUNG tool can thiet khong (cham tu dong,
     doc tu lich su message chu khong doan).
  2. Answer quality (LLM-as-judge) - mot LLM khac cham cau tra loi tu 1 den 5.

Chay tay:  venv\\Scripts\\python.exe evals\\eval_agent.py
Lam CONG CHAN: them --gate -> tra exit code 1 khi chat luong tut duoi nguong,
               nho vay CI chan duoc thay doi lam agent te di.

Ket qua ghi ra evals/results.md
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from langchain_core.messages import AIMessage, HumanMessage  # noqa: E402

import main_02_02 as lab  # noqa: E402
import metrics  # noqa: E402

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

# Nguong chan hoi quy. Dat THAP HON ket qua hien tai (100% / 4.4) mot khoang de
# dao dong tu nhien cua LLM khong lam CI do oan, nhung van bat duoc tut that su.
MIN_TOOL_ACCURACY = float(os.environ.get("MIN_TOOL_ACCURACY", "0.85"))
MIN_JUDGE_SCORE = float(os.environ.get("MIN_JUDGE_SCORE", "3.5"))

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


def usage_of(messages) -> tuple[int, int]:
    """Cong token cua MOI vong ReAct trong mot cau hoi.

    Mot cau hoi goi 3 tool = 4 lan goi model, nen phai cong het chu khong lay
    rieng lan cuoi - neu khong se bao cao chi phi thap hon thuc te vai lan.
    """
    input_tokens = output_tokens = 0
    for message in messages:
        usage = getattr(message, "usage_metadata", None)
        if usage:
            input_tokens += usage.get("input_tokens", 0)
            output_tokens += usage.get("output_tokens", 0)
    return input_tokens, output_tokens


def cost_of(model: str, input_tokens: int, output_tokens: int) -> float | None:
    """Quy token ra USD. Tra None neu model khong co trong bang gia."""
    price = metrics.PRICE_PER_1M_TOKENS.get(model)
    if price is None:
        return None
    return (input_tokens * price[0] + output_tokens * price[1]) / 1_000_000


def decide_gate(
    accuracy: float,
    avg_score: float,
    min_accuracy: float = MIN_TOOL_ACCURACY,
    min_score: float = MIN_JUDGE_SCORE,
) -> list[str]:
    """Tra ve danh sach LY DO TRUOT. Danh sach rong nghia la dat.

    Tach thanh ham thuan tuy (khong goi LLM, khong doc file) de test offline duoc
    - ban than cai cong chan cung phai co test, khong thi no hong ma khong ai biet.
    """
    failures = []
    if accuracy < min_accuracy:
        failures.append(
            f"tool-selection accuracy {accuracy:.0%} < nguong {min_accuracy:.0%}"
        )
    if avg_score < min_score:
        failures.append(f"answer quality {avg_score:.2f}/5 < nguong {min_score:.2f}/5")
    return failures


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


def main(limit: int | None = None, gate: bool = False) -> int:
    lab.get_travel_info_vectorstore()
    rows = []

    for question, expected in DATASET[:limit]:
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

        tokens_in, tokens_out = usage_of(result["messages"])
        rows.append((question, expected, tools, passed, score, elapsed, tokens_in, tokens_out))
        print(f"[{'PASS' if passed else 'FAIL'}] {score}/5  {elapsed:5.1f}s  {question}")

    accuracy = sum(r[3] for r in rows) / len(rows)
    avg_score = sum(r[4] for r in rows) / len(rows)
    avg_time = sum(r[5] for r in rows) / len(rows)
    total_in = sum(r[6] for r in rows)
    total_out = sum(r[7] for r in rows)
    total_cost = cost_of(lab.CHAT_MODEL, total_in, total_out)
    cost_per_1k = f"${total_cost / len(rows) * 1000:.2f}" if total_cost is not None else "n/a"

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
        f"| Tokens (in / out) | {total_in:,} / {total_out:,} |",
        f"| Cost per 1,000 questions | **{cost_per_1k}** |",
        "",
        "| Question | Expected tools | Tools actually called | Pass | Score |",
        "| --- | --- | --- | :-: | :-: |",
    ]
    for question, expected, tools, passed, score, *_ in rows:
        report.append(
            f"| {question} | {', '.join(sorted(expected))} | {', '.join(tools) or '-'} "
            f"| {'yes' if passed else 'no'} | {score}/5 |"
        )

    out = Path(__file__).parent / "results.md"
    out.write_text("\n".join(report) + "\n", encoding="utf-8")

    # Ban may doc duoc, de compare_models.py khoi phai boc tach markdown.
    (Path(__file__).parent / "results.json").write_text(
        json.dumps({
            "model": lab.CHAT_MODEL,
            "cases": len(rows),
            "tool_accuracy": accuracy,
            "judge_score": avg_score,
            "avg_latency_s": avg_time,
            "tokens_in": total_in,
            "tokens_out": total_out,
            "cost_per_1k_usd": None if total_cost is None else total_cost / len(rows) * 1000,
        }, indent=2),
        encoding="utf-8",
    )
    print(f"\nTool-selection accuracy {accuracy:.0%} | judge {avg_score:.1f}/5 -> {out}")

    # Tren GitHub Actions: day nguyen bang ket qua vao trang tom tat cua job,
    # de xem duoc ngay tren giao dien khong phai tai artifact ve.
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as fh:
            fh.write("\n".join(report) + "\n")

    failures = decide_gate(accuracy, avg_score)
    if not gate:
        return 0
    if failures:
        print("\nGATE FAILED:")
        for reason in failures:
            print(f"  - {reason}")
        return 1
    print(
        f"\nGATE PASSED (nguong: accuracy >= {MIN_TOOL_ACCURACY:.0%}, "
        f"quality >= {MIN_JUDGE_SCORE:.1f})"
    )
    return 0


def annotate_error(exc: Exception) -> None:
    """In loi theo dinh dang GitHub Actions de no hien thanh annotation.

    Khong co dong nay thi CI that bai chi bao "exit code 1" - phai mo log thu cong
    moi biet chuyen gi, ma log lai can dang nhap. Mat rat nhieu thoi gian.
    """
    if os.environ.get("GITHUB_ACTIONS"):
        print(f"::error::Eval that bai: {type(exc).__name__}: {str(exc)[:300]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cham diem agent tren bo cau hoi chuan.")
    parser.add_argument("--limit", type=int, default=None,
                        help="chi chay N cau dau (chay thu cho nhanh va re)")
    parser.add_argument("--gate", action="store_true",
                        help="tra exit code 1 khi chat luong tut duoi nguong")
    args = parser.parse_args()
    try:
        sys.exit(main(limit=args.limit, gate=args.gate))
    except Exception as exc:
        annotate_error(exc)
        raise
