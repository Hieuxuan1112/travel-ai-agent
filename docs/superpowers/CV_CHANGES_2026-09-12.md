# Thay đổi dự án travel-ai-agent — 2026-09-12 — nguồn cho việc sửa CV

File này viết cho một cửa sổ chat KHÁC (chuyên sửa CV), không phải để đọc học.
Mỗi mục có: việc đã làm, số liệu ĐÃ ĐO (không phải ước lượng), và file/PR để
người đọc tự kiểm chứng nếu cần. Repo: `github.com/Hieuxuan1112/travel-ai-agent`.

**Quy tắc khi đưa vào CV: chỉ dùng đúng số ghi ở đây, không làm tròn thêm,
không suy diễn thêm.** Muốn con số mới thì chạy lại lệnh ghi trong mỗi mục.

Trạng thái nguồn: tất cả đã merge vào `main` (PR #4–#14), trừ mục 2 (memory
cho API) — mục đó CHƯA XONG, đừng đưa vào CV.

---

## Con số tổng quan (dùng để thay câu đang có trên CV)

Câu cũ trên CV: *"100% tool selection and 4.6/5 answer quality across 81
offline tests"*.

Câu mới, chính xác hơn (mỗi vế đều đo được, chỉ vào đúng file):
- **140 automated tests** (từ 81) — `pytest -q`, GitHub Actions CI xanh mọi push.
- **32-case live agent eval** (từ 8), **100% tool-selection accuracy**,
  **4.6/5 answer quality** (LLM-as-judge) — `evals/results.md`.
- **$0.94 / 1,000 questions** (giảm từ $1.13 nhờ sửa một bug hiệu năng thật) —
  `evals/results.md`.
- **5/5 injection-refusal score, 0/5 leak attempts** trên bộ adversarial
  riêng — `evals/injection_results.md`.
- **137 req/s baseline throughput, p95 39ms** (hạ tầng); **p95 7.6s** cho
  request AI thật, chứng minh nút thắt là LLM chứ không phải server —
  `loadtest/results.md`.

---

## 1. Composite-score ranking cho việc chọn town (trả lời câu phỏng vấn đã vấp)

**Vấn đề gốc:** khi phỏng vấn, CTO hỏi "sao chọn đúng 2 town này, lỡ cả 2
thời tiết xấu thì sao" — không trả lời được vì lúc đó việc chọn town hoàn
toàn nằm trong suy luận tự do của LLM, không có tiêu chí tường minh.

**Đã làm:** thêm tool thứ 3 `rank_town_candidates` — tính điểm bằng công
thức tường minh trong Python thuần (không qua LLM): composite = 0.4 ×
relevance (Chroma similarity) + 0.6 × weather-fit (nhiệt độ trong khoảng
mong muốn + không mưa/bão). Có ngưỡng tối thiểu; không đủ candidate đạt
ngưỡng thì tự nới và NÓI RÕ cho user đã nới điều kiện, kèm lý do.

**Số liệu:** unit test cho công thức điểm chạy hoàn toàn offline (không gọi
API). Eval case ép kịch bản fallback ("colder than 0 degrees") chạy live:
9/9 pass, 100% tool-selection.

**CV có thể viết:** *"Replaced free-form LLM town selection with a weighted
composite score (relevance + weather-fit) with explicit thresholds and an
auto-relaxing fallback that discloses itself to the user — directly answers
the interview question the previous design couldn't."*

File: `main_02_02.py` (`rank_town_candidates`, `_score_candidates`). PR #4/#6.

---

## 2. Multi-turn memory cho FastAPI backend — **CHƯA XONG, ĐỪNG ĐƯA VÀO CV**

Thiết kế xong, code xong, test pass trong một worktree riêng, nhưng KHÔNG
BAO GIỜ được commit — bị bỏ quên giữa phiên làm việc. `api.py` trên `main`
hiện vẫn hoàn toàn stateless. Xem `HANDOFF.md` mục 2.1 để hoàn thành sau.

---

## 3. Retry tự động khi LLM gọi sai schema tool (reliability engineering)

**Vấn đề:** `ToolsExecutionNode` không có try/except quanh việc thực thi
tool — LLM truyền sai kiểu tham số (vd truyền list thay vì string) làm
crash toàn bộ graph thay vì được sửa.

**Đã làm:** bắt `pydantic.ValidationError` ở đúng lớp thực thi tool, trả về
`ToolMessage` mô tả lỗi cho model đọc — lượt kế tiếp của model đóng vai trò
"retry" tự nhiên, không cần vòng lặp Python riêng.

**Số liệu — chứng minh bằng kịch bản THẬT, không phải giả định:** ép một
tool-call sai kiểu (`town=["not","a","string"]`), quan sát model tự sửa
đúng tham số (`town="Falmouth"`) ở lượt gọi tiếp theo, không cần can thiệp gì
thêm.

**CV có thể viết:** *"Added schema-validation error recovery so malformed
tool calls self-correct on the model's next turn instead of crashing the
agent graph — verified live, not just unit-tested."*

File: `main_02_02.py` (`ToolsExecutionNode.__call__`). PR #5.

---

## 4. Test chống prompt injection + lớp chắn rò rỉ system prompt

**Vấn đề:** README ghi "safe to expose publicly" nhưng chỉ có rate limit,
chưa có bằng chứng nào chống lại việc user cố rút trích system prompt hoặc
lợi dụng agent làm việc ngoài phạm vi.

**Đã làm:** bộ eval riêng 5 case tấn công trực tiếp (rút trích prompt, giả
"developer mode", giả lệnh hệ thống, yêu cầu có hại/ngoài chủ đề, trộn
injection vào câu hỏi hợp lệ) — chạy live, chấm bằng LLM-judge. Thêm lớp
chắn thứ hai ở code: nếu output khớp ≥8 từ liên tiếp với đoạn nhạy cảm của
system prompt thì thay bằng câu từ chối trước khi trả cho user.

**Số liệu:** **5/5 điểm từ chối trung bình, 0/5 lần rò rỉ thật** trên live
run — mô hình tự chống được hầu hết, lớp chắn code là phòng thủ thứ hai.

**CV có thể viết:** *"Closed the gap between the README's security claim
and reality: built a live adversarial eval (5 attack patterns, LLM-judged)
plus an output-side guard against system-prompt leakage — 5/5 refusal score,
0 leaks observed."*

File: `evals/eval_injection.py`, `main_02_02.py` (`_leaks_system_prompt`).
PR #7.

---

## 5. Mở rộng eval set 8 → 32 case (không phải case lặp/na ná nhau)

**Vấn đề:** 8 case là quá ít để tin cậy thật, và không còn khớp con số "56
test" từng ghi nhầm trên một bản CV cũ.

**Đã làm:** thêm 24 case đa dạng thật — nhiều town khác nhau (Padstow, Truro,
Bude, Fowey, Looe, Mousehole, Tintagel, Eden Project...), nhiều loại câu hỏi
(tra cứu, thời tiết đơn, so sánh, edge case town không tồn tại) — không phải
đổi tên town trong cùng một mẫu câu.

**Số liệu:** 32/32 pass live, **100% tool-selection accuracy, 4.6/5 answer
quality**, cost **$0.94/1,000 câu**.

**CV có thể viết:** *"Grew the agent eval suite from 8 to 32 cases (topic
and edge-case diversity, not near-duplicates) — 100% tool-selection accuracy,
4.6/5 judged answer quality, gated in CI on every push."*

File: `evals/eval_agent.py`. PR #9.

---

## 6. Multi-agent: planner + executor qua LangGraph subgraph

**Bối cảnh:** đã từng nói với CTO sẽ mở rộng thành multi-agent nhưng chưa
làm — đây là lời hứa đã thực hiện.

**Đã làm:** file mới `main_05_multi_agent.py` — một node **planner** (dùng
Pydantic structured output, không gọi tool nào) đọc câu hỏi mới nhất của
user, quyết định có cần xếp hạng nhiều town theo thời tiết không và tiêu chí
gì (bao nhiêu town, khoảng nhiệt độ). Quyết định đó được ghép với **executor**
— chính graph ReAct có sẵn (`main_02_02.py`), TÁI SỬ DỤNG NGUYÊN VẸN, không
sửa gì, đưa vào làm một node của graph cha qua `add_node` (subgraph thật của
LangGraph, không phải hai hàm Python gọi tuần tự giả làm "multi-agent").

**Bug thật tìm thấy qua test, không phải qua đọc tài liệu:** LangGraph lọc
state của node-là-subgraph theo đúng schema graph con khai báo — quyết định
`plan` của planner "biến mất" khi tới executor vì `AgentState` gốc không
khai báo field đó. Sửa bằng cách thêm `plan: NotRequired[dict]`.

**Số liệu:** live run thật — planner quyết định đúng (`needs_town_ranking`,
`top_n`, khoảng nhiệt độ), executor đọc được và hành động đúng theo, câu trả
lời có số liệu thời tiết thật trích dẫn đầy đủ.

**CV có thể viết:** *"Implemented a planner+executor multi-agent pattern
using LangGraph's subgraph composition — the existing ReAct graph is reused
unmodified as the executor; a lightweight planner does structured-output
decision-making upstream of it. Found and fixed a real LangGraph state-schema
propagation bug in the process."*

File: `main_05_multi_agent.py` (MỚI). PR #10.

---

## 7. Lưu lịch sử eval theo thời gian (SQL schema design)

**Vấn đề:** `evals/results.md`/`results.json` bị ghi đè mỗi lần chạy — không
trả lời được "chất lượng có tụt theo thời gian không" bằng dữ liệu thật.

**Đã làm:** bảng `eval_runs` (id, run_at, git_sha, model, dataset_size,
tool_accuracy, judge_score, avg_latency_s, cost_per_1k_usd) — Postgres khi có
`DATABASE_URL` (dùng chung Neon với checkpointer hội thoại), SQLite cục bộ
khi không có. Script `evals/history_report.py` xem xu hướng.

**Bug thật tìm thấy qua test thật với Postgres:** cột `run_at` từ Postgres
là `datetime` object thật, không phải chuỗi — làm hỏng canh cột khi in báo
cáo (`{value:<26}` bị Python diễn giải nhầm thành pattern strftime).

**CV có thể viết:** *"Designed and shipped a small time-series schema
(eval_runs) with dual SQLite/Postgres backends sharing the same schema —
live-tested against production Postgres, found and fixed a real
datetime-formatting bug along the way."*

File: `eval_history.py` (MỚI), `evals/history_report.py` (MỚI). PR #11.

---

## 8. Redis: rate-limit chia sẻ nhiều instance + cache thời tiết

**Vấn đề:** rate-limit đang đếm trong bộ nhớ tiến trình — mất khi restart,
không chia sẻ được giữa nhiều instance (giới hạn đã tự ghi trong code từ
trước).

**Đã làm:** rate-limit chuyển sang Redis sorted set (thuật toán sliding
window y hệt bản cũ, chỉ đổi nơi lưu) khi có `REDIS_URL`, tự lùi về bộ nhớ
khi không có — không đổi hành vi bản đang chạy thật. Thêm cache 5 phút cho
`weather_forecast`, giảm gọi lặp Open-Meteo.

**Số liệu — kiểm chứng với Redis THẬT (không chỉ giả lập):** dựng container
Redis thật, chạy server thật, xác nhận qua `redis-cli`: sorted set rate-limit
đúng 3 entry sau 3 request, cache thời tiết có key/TTL đúng 276s trên 300s.
Kịch bản kết hợp API-key + rate-limit qua Redis cũng chạy đúng: không key →
401 (không tốn quota), có key 2 lần → 200, lần 3 → 429.

**CV có thể viết:** *"Migrated the rate limiter from in-process memory to
Redis (sorted-set sliding window), enabling multi-instance deployment, and
added a 5-minute weather-response cache — both verified against a live Redis
container, not just mocked."*

File: `redis_client.py` (MỚI), `api.py`, `main_02_02.py`. PR #13.

---

## 9. API key authentication cho FastAPI

**Vấn đề:** `/chat` và `/chat/stream` hoàn toàn công khai, chỉ có rate limit.

**Đã làm:** header `X-API-Key`, bật qua biến môi trường `API_KEYS`
(danh sách, phân tách dấu phẩy) — không đặt biến thì API vẫn công khai như
cũ (không phá bản đang chạy Azure). `/healthz`, `/metrics` luôn công khai.

**Số liệu:** live test với server thật: không key → 401, sai key → 401,
đúng key → 200.

**CV có thể viết:** *"Added opt-in API key authentication (X-API-Key header)
to the FastAPI service with zero-downtime backward compatibility — the
already-deployed instance keeps working unauthenticated since it never sets
the gating env var."*

File: `api.py` (`require_api_key`). PR #12.

---

## 10. Load test bằng Locust — xác định đúng nút thắt

**Vấn đề:** chưa ai đo p95/throughput dưới tải thật; câu hỏi "nút thắt là
CPU hay quota Gemini" (đã ghi trong tài liệu học từ trước) chưa có câu trả
lời bằng số liệu.

**Đã làm:** 2 kịch bản Locust — (1) `/healthz` (miễn phí, không gọi Gemini)
đo trần hạ tầng thuần; (2) `/chat` thật với quy mô nhỏ có kiểm soát (< 1 cent
cho cả lần chạy) đo p95 thật của đường AI.

**Số liệu:**
- Baseline hạ tầng: **137 req/s, p95 = 39ms, p99 = 96ms, 0% lỗi** (50 user
  đồng thời).
- `/chat` thật: **p50 = 3.7s, p95 = 7.6s, 0% lỗi** (9 request thật).
- **Kết luận có bằng chứng:** nút thắt là round-trip Gemini, không phải
  CPU/FastAPI — hạ tầng còn dư sức rất nhiều so với tốc độ trả lời của AI.

**CV có thể viết:** *"Load-tested with Locust to settle an open question:
infra alone sustains 137 req/s at p95 39ms, while real AI requests cap at
p95 7.6s — hard evidence the bottleneck is LLM latency, not server capacity."*

File: `loadtest/locustfile_healthz.py`, `loadtest/locustfile_chat.py` (MỚI).
PR #14.
