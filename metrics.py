"""Prometheus metrics cho agent.

Do CPU/RAM thi ai cung do duoc va chang noi len gi. Cai dang do voi mot he thong
LLM la nhung thu RIENG cua LLM:

  - moi request tot bao lau (p95, khong phai trung binh)
  - agent goi tool nao, bao nhieu lan, tool nao hay hong
  - tieu bao nhieu token va HET BAO NHIEU TIEN

File nay chi DINH NGHIA thuoc do; noi ghi so nam trong api.py (theo request) va
main_02_02.py (theo tool / theo lan goi LLM).
"""

import os

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, multiprocess

# ---------------------------------------------------------------------------
# Bon loai thuoc do cua Prometheus - chon dung loai la nua phan thang loi:
#   Counter   chi tang, khong giam (so request, so token, tien)
#   Gauge     len xuong tuy y (so request dang chay)
#   Histogram chia thoi gian vao cac "ro" -> tinh duoc p50/p95/p99
#   Summary   it dung, bo qua
# ---------------------------------------------------------------------------

REQUESTS = Counter(
    "agent_requests_total",
    "So request da xu ly",
    ["endpoint", "status"],
)

# Buckets mac dinh cua Prometheus dung o 10s - agent nay chay 5-20s nen phai
# tu dinh nghia, khong thi moi request deu roi vao ro cuoi va p95 vo nghia.
REQUEST_DURATION = Histogram(
    "agent_request_duration_seconds",
    "Thoi gian tra loi tron mot cau hoi",
    ["endpoint"],
    buckets=(0.5, 1, 2, 5, 8, 12, 20, 30, 60),
)

IN_FLIGHT = Gauge(
    "agent_requests_in_flight",
    "So request dang chay ngay luc nay",
)

RATE_LIMITED = Counter(
    "agent_rate_limited_total",
    "So request bi tu choi vi vuot gioi han tan suat",
)

TOOL_CALLS = Counter(
    "agent_tool_calls_total",
    "So lan tung tool duoc goi",
    ["tool"],
)

TOOL_ERRORS = Counter(
    "agent_tool_errors_total",
    "So lan tool tra ve loi",
    ["tool"],
)

TOOL_DURATION = Histogram(
    "agent_tool_duration_seconds",
    "Thoi gian chay cua tung tool",
    ["tool"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
)

LLM_CALLS = Counter(
    "agent_llm_calls_total",
    "So lan goi model",
    ["model"],
)

LLM_TOKENS = Counter(
    "agent_llm_tokens_total",
    "So token da dung",
    ["model", "kind"],          # kind = input | output
)

LLM_COST = Counter(
    "agent_llm_cost_usd_total",
    "Tien da tieu (USD, uoc tinh tu bang gia)",
    ["model"],
)


# ---------------------------------------------------------------------------
# Bang gia USD cho 1 TRIEU token (input, output) - ai.google.dev, Paid Tier.
# Model khong co trong bang thi khong tinh tien, chi dem token.
# ---------------------------------------------------------------------------
PRICE_PER_1M_TOKENS = {
    "gemini-3.1-flash-lite": (0.25, 1.50),
    "gemini-3.1-flash": (0.30, 2.50),
}


def record_llm_usage(model: str, usage: dict | None) -> None:
    """Ghi token + tien cho mot lan goi model.

    `usage` la AIMessage.usage_metadata cua LangChain:
    {"input_tokens": .., "output_tokens": .., "total_tokens": ..}
    """
    LLM_CALLS.labels(model=model).inc()
    if not usage:
        return

    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    LLM_TOKENS.labels(model=model, kind="input").inc(input_tokens)
    LLM_TOKENS.labels(model=model, kind="output").inc(output_tokens)

    price = PRICE_PER_1M_TOKENS.get(model)
    if price:
        cost = (input_tokens * price[0] + output_tokens * price[1]) / 1_000_000
        LLM_COST.labels(model=model).inc(cost)


def build_registry() -> CollectorRegistry:
    """Registry de xuat metrics.

    Uvicorn mot worker thi dung registry mac dinh la du. Neu chay nhieu worker
    (gunicorn -w 4), moi worker la mot tien trinh voi bo dem rieng -> phai gom
    lai qua thu muc PROMETHEUS_MULTIPROC_DIR, neu khong so lieu se nhay lung tung.
    """
    if os.environ.get("PROMETHEUS_MULTIPROC_DIR"):
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        return registry

    from prometheus_client import REGISTRY

    return REGISTRY
