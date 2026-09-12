"""In lich su eval gan day - bang chung "chat luong theo thoi gian", khong chi
mot con so tinh tai mot thoi diem.

Chay:  venv\\Scripts\\python.exe evals\\history_report.py [--limit N]
"""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

import eval_history  # noqa: E402


def main(limit: int) -> None:
    runs = eval_history.recent_runs(limit=limit)
    if not runs:
        print(f"Chua co lich su nao (backend: {eval_history.backend_name()}).")
        return

    print(f"Backend: {eval_history.backend_name()} | {len(runs)} lan chay gan nhat\n")
    header = (
        f"{'run_at':<26} {'git_sha':<9} {'cases':>5} {'accuracy':>8} "
        f"{'judge':>6} {'cost/1k':>8}"
    )
    print(header)
    print("-" * len(header))
    for run in runs:
        cost = f"${run['cost_per_1k_usd']:.2f}" if run["cost_per_1k_usd"] is not None else "n/a"
        # Postgres tra run_at ve datetime that, SQLite tra ve chuoi ISO da luu -
        # ep ve str truoc khi can chinh do rong, khong thi datetime.__format__
        # doc "<26" nhu mot pattern strftime thay vi can chinh cot.
        run_at = str(run["run_at"])
        print(
            f"{run_at:<26} {(run['git_sha'] or '-'):<9} {run['dataset_size']:>5} "
            f"{run['tool_accuracy']:>7.0%} {run['judge_score']:>6.1f} {cost:>8}"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="In lich su eval gan day.")
    parser.add_argument("--limit", type=int, default=10)
    main(parser.parse_args().limit)
