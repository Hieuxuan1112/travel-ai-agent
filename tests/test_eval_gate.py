"""Test cho logic cong chan chat luong - chay offline, khong goi LLM.

Ban than cai cong chan cung phai co test: neu no hong theo kieu "luon cho qua"
thi CI van xanh trong khi agent da te di, ma khong ai biet.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("GOOGLE_API_KEY", "test-key-not-used")

from evals.eval_agent import decide_gate  # noqa: E402


def test_good_results_pass_the_gate():
    assert decide_gate(accuracy=1.0, avg_score=4.4) == []


def test_low_tool_accuracy_fails():
    failures = decide_gate(accuracy=0.50, avg_score=4.4)

    assert len(failures) == 1
    assert "tool-selection accuracy" in failures[0]


def test_low_answer_quality_fails():
    failures = decide_gate(accuracy=1.0, avg_score=2.0)

    assert len(failures) == 1
    assert "answer quality" in failures[0]


def test_both_metrics_bad_reports_both_reasons():
    """Bao ca hai ly do mot luc, khong dung o cai dau tien."""
    failures = decide_gate(accuracy=0.10, avg_score=1.0)

    assert len(failures) == 2


def test_exactly_at_threshold_passes():
    """Bang dung nguong thi DAT - tranh do oan vi sai so lam tron."""
    assert decide_gate(accuracy=0.85, avg_score=3.5,
                       min_accuracy=0.85, min_score=3.5) == []


def test_thresholds_are_configurable():
    """CI dat nguong qua bien moi truong, nen phai truyen vao duoc."""
    assert decide_gate(accuracy=0.90, avg_score=4.0, min_accuracy=0.95) != []
    assert decide_gate(accuracy=0.90, avg_score=4.0, min_accuracy=0.80) == []
