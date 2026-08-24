"""Chay cung mot bo eval tren NHIEU model roi lap bang so sanh.

Tra loi mot cau hoi phong van chac chan bi hoi: "sao ban chon model nay?"

Cach lam: goi lai eval_agent.py trong TIEN TRINH RIENG cho tung model, vi
main_02_02.py doc CHAT_MODEL va dung san model + do thi ngay luc import - doi
model trong cung tien trinh se dinh trang thai cu.

Chay:
  venv\\Scripts\\python.exe evals\\compare_models.py
  venv\\Scripts\\python.exe evals\\compare_models.py --limit 3     # chay thu cho re
  venv\\Scripts\\python.exe evals\\compare_models.py --models gemini-2.5-flash-lite

Ket qua ghi ra evals/model_comparison.md
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import metrics  # noqa: E402

# Trai deu tren pho gia, tu re nhat den dat nhat, va co ca doi cu lan doi moi de
# tra loi duoc "model moi hon co dang tien hon khong".
# Bo gemini-3.1-pro-preview (khong co free tier) va gemini-2.5-pro (loi khi chay
# vong ReAct trong lan do dau - chua tim ra nguyen nhan, xem model_comparison.md).
DEFAULT_MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-3.5-flash",
]


def run_eval(model: str, limit: int | None) -> dict | None:
    """Chay eval_agent.py cho mot model, tra ve ket qua doc tu results.json."""
    env = {**os.environ, "CHAT_MODEL": model}
    cmd = [sys.executable, str(ROOT / "evals" / "eval_agent.py")]
    if limit:
        cmd += ["--limit", str(limit)]

    print(f"\n{'=' * 78}\n  {model}\n{'=' * 78}")
    result = subprocess.run(cmd, env=env, cwd=ROOT, text=True, capture_output=True)
    for line in result.stdout.splitlines():
        if line.startswith("[") or line.startswith("Tool-selection"):
            print("  " + line)

    if result.returncode != 0:
        print(f"  LOI: {result.stderr.strip().splitlines()[-1][:120]}")
        return None
    return json.loads((ROOT / "evals" / "results.json").read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="So sanh nhieu model tren cung bo eval.")
    parser.add_argument("--limit", type=int, default=None, help="chi chay N cau dau")
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    args = parser.parse_args()

    results = [r for m in args.models if (r := run_eval(m, args.limit))]
    if not results:
        print("Khong co model nao chay duoc.")
        return 1

    # Xep theo chi phi tang dan - de nguoi doc thay ngay "tra them tien duoc gi".
    results.sort(key=lambda r: r["cost_per_1k_usd"] or 0)
    cheapest = results[0]

    lines = [
        "# So sanh model",
        "",
        f"Cung mot bo eval {results[0]['cases']} cau, cung tool, cung prompt - chi doi model.",
        "Sinh boi `evals/compare_models.py`.",
        "",
        "| Model | Gia in/out ($/1M) | Tool-selection | Chat luong | p-trung binh | $/1000 cau |",
        "| --- | --- | :-: | :-: | :-: | --: |",
    ]
    for r in results:
        price = metrics.PRICE_PER_1M_TOKENS.get(r["model"], (0, 0))
        cost = r["cost_per_1k_usd"]
        lines.append(
            f"| `{r['model']}` | {price[0]:.2f} / {price[1]:.2f} "
            f"| {r['tool_accuracy']:.0%} | {r['judge_score']:.1f}/5 "
            f"| {r['avg_latency_s']:.1f}s | ${cost:.2f} |"
        )

    lines += ["", "## Doc bang the nao", ""]
    for r in results[1:]:
        times = (r["cost_per_1k_usd"] or 0) / (cheapest["cost_per_1k_usd"] or 1)
        delta = r["judge_score"] - cheapest["judge_score"]
        verdict = "khong dang" if delta <= 0.3 else "dang can nhac"
        lines.append(
            f"- `{r['model']}` dat gap **{times:.1f} lan** `{cheapest['model']}` "
            f"nhung chat luong chi lech **{delta:+.1f} diem** -> {verdict}."
        )

    out = ROOT / "evals" / "model_comparison.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n{'=' * 78}")
    print("\n".join(lines[5:]))
    print(f"\n-> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
