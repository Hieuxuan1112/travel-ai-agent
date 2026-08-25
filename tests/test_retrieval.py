"""Test cho tang truy hoi - offline, khong goi mang, khong goi LLM.

RRF va dinh dang trich dan deu la ham thuan tuy nen test duoc truc tiep.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("GOOGLE_API_KEY", "test-key-not-used")

from retrieval import (  # noqa: E402
    format_with_citations,
    reciprocal_rank_fusion,
    tokenize,
)

# ===========================================================================
# Tokenize
# ===========================================================================

def test_tokenize_lowercases_and_drops_punctuation():
    assert tokenize("St Ives, Cornwall!") == ["st", "ives", "cornwall"]


def test_tokenize_keeps_digits():
    """Ma so va nam la thu BM25 gioi hon vector - khong duoc vut di."""
    assert tokenize("SKU-99321 in 2026") == ["sku", "99321", "in", "2026"]


# ===========================================================================
# Reciprocal Rank Fusion
# ===========================================================================

def test_document_ranked_high_by_both_lists_wins():
    """Y chinh cua RRF: duoc CA HAI ben xep cao thi noi len tren."""
    scores = reciprocal_rank_fusion([["a", "b", "c"], ["b", "a", "c"]])

    assert scores["b"] > scores["c"]
    assert scores["a"] > scores["c"]


def test_a_single_first_place_can_lose_to_two_second_places():
    """Vi sao RRF hoat dong: dong thuan cua hai ben thang mot phieu don le."""
    scores = reciprocal_rank_fusion([["solo", "both"], ["other", "both"]])

    assert scores["both"] > scores["solo"]


def test_only_rank_matters_not_the_original_scores():
    """RRF bo diem so vi hai he cham theo thang khac nhau, cong thang la vo nghia."""
    scores = reciprocal_rank_fusion([["x", "y"]])

    assert scores["x"] == 1 / (60 + 1)
    assert scores["y"] == 1 / (60 + 2)


def test_smaller_k_makes_the_top_rank_count_for_more():
    """k la hang so lam mem: k nho thi khoang cach giua hang 1 va hang 2 gian ra."""
    soft = reciprocal_rank_fusion([["x", "y"]], k=60)
    sharp = reciprocal_rank_fusion([["x", "y"]], k=1)

    assert sharp["x"] - sharp["y"] > soft["x"] - soft["y"]


# ===========================================================================
# Trich dan
# ===========================================================================

RESULTS = [
    ("id1", "St Ives has sandy beaches.", {"source": "https://example.org/StIves"}),
    ("id2", "Newquay is the surfing capital.", {"source": "https://example.org/Newquay"}),
]


def test_each_document_gets_a_number_and_a_source_line():
    out = format_with_citations(RESULTS)

    assert "[1] St Ives has sandy beaches." in out
    assert "[2] Newquay is the surfing capital." in out
    assert "[1] https://example.org/StIves" in out
    assert "[2] https://example.org/Newquay" in out


def test_output_is_fenced_as_untrusted():
    out = format_with_citations(RESULTS)

    assert out.startswith("<untrusted_documents")
    assert out.rstrip().endswith("</untrusted_documents>")


def test_model_is_told_to_cite():
    assert "Cite the numbered sources" in format_with_citations(RESULTS)


def test_missing_source_metadata_does_not_crash():
    """Chunk cu chua co metadata nguon - phai chay duoc, khong duoc no."""
    out = format_with_citations([("id", "text", {})])

    assert "[1] unknown" in out


def test_empty_result_still_returns_a_fenced_message():
    """Khong tim thay gi thi van phai rao lai, khong tra chuoi rong."""
    out = format_with_citations([])

    assert "untrusted_documents" in out
    assert "No matching documents" in out
