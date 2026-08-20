"""Demo TUONG TAC: chung minh prompt va MO TA TOOL doi hanh vi cua agent ra sao.

Khong giai thich chay - chay that, goi model that, in ra quyet dinh that.

Ba thi nghiem DO LUONG (khong phai chung minh san):
  --system  (mac dinh) Cung cau hoi, CO va KHONG CO system prompt -> co doi hanh vi khong?
  --schema  In ra dung "to khai" ma LLM nhan duoc ve moi tool (JSON schema)
  --vague   Lam mo ca TEN lan MO TA tool -> LLM co con chon dung khong?

Ket qua do duoc voi gemini-3.1-flash-lite (xem HOC_PROMPT_ENGINEERING.md muc 5):
ca ba thi nghiem deu KHONG tach duoc khac biet - model nay vung hon ky vong.
Do la mot ket qua HOP LE va dang bao cao, khong phai thi nghiem that bai.

Chay:
  venv\\Scripts\\python.exe docs\\demo_prompt_ab.py
  venv\\Scripts\\python.exe docs\\demo_prompt_ab.py --schema
  venv\\Scripts\\python.exe docs\\demo_prompt_ab.py --vague
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from langchain_core.messages import HumanMessage, SystemMessage  # noqa: E402
from langchain_core.tools import tool  # noqa: E402

import main_02_02 as lab  # noqa: E402

LINE = "=" * 100

QUESTIONS = [
    "Suggest two Cornwall beach towns with nice weather",
    "Which Cornwall town has the best surfing right now?",
]


def tool_calls_of(messages) -> list[str]:
    """Goi model MOT vong va tra ve danh sach tool no muon goi."""
    response = lab.llm_with_tools.invoke(messages)
    return [f"{c['name']}({json.dumps(c['args'], ensure_ascii=False)})"
            for c in (response.tool_calls or [])] or ["(khong goi tool nao - tra loi thang)"]


def experiment_system() -> None:
    print(f"\n{LINE}")
    print("  THI NGHIEM 1 - CO va KHONG CO system prompt")
    print(LINE)
    print("\n  System prompt dang dung:")
    for line in lab.SYSTEM_PROMPT.strip().split("\n"):
        print(f"    | {line.strip()}")

    for question in QUESTIONS:
        print(f"\n{'-' * 100}")
        print(f"  Cau hoi: {question}")
        print("-" * 100)

        without = tool_calls_of([HumanMessage(content=question)])
        with_prompt = tool_calls_of(
            [SystemMessage(content=lab.SYSTEM_PROMPT), HumanMessage(content=question)]
        )

        print("\n  [A] KHONG system prompt:")
        for call in without:
            print(f"        {call}")
        print("\n  [B] CO system prompt:")
        for call in with_prompt:
            print(f"        {call}")

        a_searched = any("search_travel_info" in c for c in without)
        b_searched = any("search_travel_info" in c for c in with_prompt)
        if b_searched and not a_searched:
            print("\n  => KHAC BIET: khong co system prompt, model tu nghi ra ten thi tran tu")
            print("     kien thuc san co roi nhay thang sang tra thoi tiet - BO QUA kho du lieu.")
        elif a_searched and b_searched:
            print("\n  => Lan nay ca hai deu tim truoc (model co the dao dong giua cac lan chay).")
        else:
            print("\n  => Ket qua lan nay khac thuong - chay lai de xem xu huong.")


def experiment_schema() -> None:
    print(f"\n{LINE}")
    print("  THI NGHIEM 2 - 'To khai' tool ma LLM thuc su nhan duoc")
    print(LINE)
    print("\n  LLM KHONG nhin thay code ben trong ham. No chi nhan dung nhung thu nay:")

    for t in lab.TOOLS:
        print(f"\n{'-' * 100}")
        print(f"  Ten        : {t.name}")
        print(f"  Mo ta      : {t.description}")
        print("  Tham so    :")
        schema = t.args_schema.model_json_schema() if t.args_schema else {}
        for arg, spec in schema.get("properties", {}).items():
            required = arg in schema.get("required", [])
            print(f"     - {arg} ({spec.get('type', '?')})"
                  f"{' [bat buoc]' if required else ' [tuy chon]'}")
    print("\n  => Vi vay MO TA chinh la giao dien lap trinh danh cho LLM.")
    print("     Mo ta viet do = agent chon sai tool, du code ben trong hoan hao.")


# Ten ham CUNG la tin hieu cho LLM, khong chi mo ta. Nen de co lap duoc anh huong
# cua rieng MO TA, o day phai lam mo ca TEN: tool_a / tool_b thay vi vague_search.
@tool(description="Search stuff.")
def tool_a(query: str) -> str:
    """Ban mo ta + ten MO HO cua search_travel_info."""
    return lab.search_travel_info.invoke({"query": query})


@tool(description="Get data.")
def tool_b(town: str, country: str = "") -> dict:
    """Ban mo ta + ten MO HO cua weather_forecast."""
    return lab.weather_forecast.invoke({"town": town, "country": country})


def experiment_vague() -> None:
    print(f"\n{LINE}")
    print("  THI NGHIEM 3 - Mo ta tool ro rang vs mo ho")
    print(LINE)
    print("\n  Tool y het nhau ve chuc nang, chi khac MO TA:")
    print("    ro rang : search_travel_info - 'Search travel information about...'")
    print("              weather_forecast   - 'Get the CURRENT weather of a town...'")
    print("    mo ho   : tool_a - 'Search stuff.'  /  tool_b - 'Get data.'")

    vague_llm = lab.llm_model.bind_tools([tool_a, tool_b])

    for question in QUESTIONS:
        print(f"\n{'-' * 100}")
        print(f"  Cau hoi: {question}")
        print("-" * 100)

        clear = tool_calls_of([SystemMessage(content=lab.SYSTEM_PROMPT),
                               HumanMessage(content=question)])
        response = vague_llm.invoke([SystemMessage(content=lab.SYSTEM_PROMPT),
                                     HumanMessage(content=question)])
        vague = [f"{c['name']}({json.dumps(c['args'], ensure_ascii=False)})"
                 for c in (response.tool_calls or [])] or ["(khong goi tool nao)"]

        print("\n  [A] Mo ta RO RANG:")
        for call in clear:
            print(f"        {call}")
        print("\n  [B] Mo ta MO HO:")
        for call in vague:
            print(f"        {call}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", action="store_true", help="in to khai tool")
    parser.add_argument("--vague", action="store_true", help="so mo ta ro vs mo ho")
    args = parser.parse_args()

    if args.schema:
        experiment_schema()
    elif args.vague:
        experiment_vague()
    else:
        experiment_system()


if __name__ == "__main__":
    main()
