# Bàn giao — đọc file này trước

Cập nhật **2026-09-12**. Phiên trước làm 10 việc từ danh sách CTO đưa (Ưu tiên
1–4), tất cả đã merge vào `main` qua PR (#4–#14). Phiên này KHÔNG cập nhật tài
liệu học (`docs/hoc/`) — đó là việc gấp nhất còn lại, xem mục 1.

---

## 0. VIỆC GẤP NHẤT CŨ VẪN CÒN Y NGUYÊN: 7 tài liệu chưa lên GitHub

Từ phiên **2026-09-08**, vẫn chưa commit. Kiểm tra lại bằng `git status` ở
`D:\langgraph-agent-lab` — nếu các dòng dưới đây vẫn còn thì làm ngay:

```
?? docs/hoc/HOC_LLM_NEN_TANG.md
?? docs/hoc/HOC_AGENT_PATTERNS.md
?? docs/hoc/HOC_BACKEND_API.md
?? docs/hoc/HOC_FRONTEND_REACT.md
?? docs/hoc/HOC_VAN_HANH_THAT.md
?? docs/hoc/PHONG_VAN_MO_PHONG.md
?? docs/hoc/CHECKLIST_HIEU_SAU.md
 M docs/hoc/HOC_DSA_OOP.md
 M docs/hoc/README.md
```

```bash
cd /d D:\langgraph-agent-lab
git checkout main && git pull
git checkout -b docs/deep-understanding
git add docs/hoc/
git commit -m "docs: add the deep-understanding guide set"
git push -u origin docs/deep-understanding
```

**KHÔNG `git add` thư mục `chroma_travel_info/`** — vài byte đổi do chạy app,
nội dung không đổi. Cứ để nó hiện trong `git status`.

---

## 1. VIỆC GẤP THỨ HAI: tài liệu học CHƯA phản ánh 10 thay đổi mới

Phiên `2026-09-12` làm xong toàn bộ danh sách CTO đưa (chi tiết mục 3), nhưng
**không đụng tới `docs/hoc/`**. Các tài liệu đó (kể cả 7 file đang treo ở mục 0)
vẫn mô tả kiến trúc CŨ: agent 2 tool, 8 test case eval, rate-limit trong bộ
nhớ, không có auth, không có multi-agent. Cần một phiên riêng để:

- Cập nhật `docs/hoc/HOC_AGENT_PATTERNS.md` (thêm multi-agent supervisor:
  `main_05_multi_agent.py`, planner + executor qua LangGraph subgraph).
- Cập nhật `docs/hoc/HOC_VAN_HANH_THAT.md` mục 6.1 (load test — ĐÃ ĐO rồi,
  xem `loadtest/results.md`, không còn là "chưa ai chạy" nữa).
- Cập nhật phần nào đó nhắc tới rate-limit/backend/tool count trong
  `HOC_BACKEND_API.md`, `HOC_FASTAPI_SSE.md` (Redis, API key, 3 tool thay vì 2).
- `docs/MENTOR.md` mục nào mô tả kiến trúc/tool cũng cần soát lại.

Đưa file `docs/superpowers/CV_CHANGES_2026-09-12.md` (mục 4 dưới đây, đã ghi
sẵn danh sách 10 thay đổi kèm số liệu thật) cho phiên đó làm nguồn — không
cần dò lại code từ đầu.

---

## 2. Việc CÒN DỞ từ phiên 2026-09-12

### 2.1. `feature/api-multiturn-memory` — CHƯA BAO GIỜ COMMIT

Việc này được lên kế hoạch sớm nhất phiên (thiết kế + plan đầy đủ ở
`docs/superpowers/specs/2026-09-12-api-multiturn-memory-design.md` và
`docs/superpowers/plans/2026-09-12-api-multiturn-memory-plan.md`), CODE ĐÃ
VIẾT XONG VÀ TEST PASS trong worktree `D:\langgraph-agent-lab\.worktrees\api-multiturn-memory`,
nhưng user không bao giờ chạy lệnh commit — bị bỏ quên giữa chừng khi chuyển
sang làm danh sách CTO.

Trạng thái: `api.py` trên `main` HIỆN VẪN STATELESS — mỗi câu hỏi qua
`/chat`/`/chat/stream` không nhớ câu trước, dù `app.py` (Streamlit) đã nhớ từ
rất lâu rồi qua `persistence.py`.

Việc cần làm: vào worktree đó, `git status` xem code còn nguyên không (chưa
merge main mới nên CHẮC CHẮN sẽ conflict ở `api.py` — sau 10 PR khác cùng sửa
file này). Cách an toàn nhất: **viết lại từ đầu trên nhánh mới dựa trên `main`
hiện tại**, dùng lại đúng thiết kế trong file spec/plan đã có, thay vì cố merge
code cũ (conflict sẽ rất nhiều vì `api.py` đã đổi nhiều: `require_api_key`,
`redis_client`, `app.state.agent`...).

### 2.1b. Streamlit demo (`cornwall-travel-agent.streamlit.app`) — ĐÃ SỬA XONG, ĐÃ XÁC NHẬN SỐNG

Trình tự đã xảy ra: push `feat(ui)` toggle ReAct/Multi-agent → mở link demo
thật thì **SẬP** (`ValueError: Duplicated timeseries in CollectorRegistry`
trong `metrics.py`, bug #4 ở mục 3) → sửa bằng `_metric()` (tra collector cũ
trước khi tạo mới) → PR `hotfix/prometheus-reimport-crash` đã merge (commit
`7fbe4f9`) → **mở lại link bằng trình duyệt thật, xác nhận: app KHÔNG còn
sập, sidebar hiện đúng "Agent architecture" (ReAct/Multi-agent), `Conversation
store: postgres` (dữ liệu thật, không phải giả), tool `search_travel_info` +
`weather_forecast` hiện đúng.**

Còn một việc CHƯA xác nhận được do giới hạn công cụ trình duyệt của phiên
trước (trang chat của Streamlit Cloud có vẻ nằm trong iframe, `read_page`/
`get_page_text` không đọc được nội dung bên trong, chỉ `screenshot` thấy):
**chưa gửi thử một câu hỏi thật và xem câu trả lời trên chính bản deploy** (đã
làm việc này thành công trên `localhost:8502` trước đó, nhưng KHÔNG PHẢI trên
domain thật). Việc cần làm: mở `https://cornwall-travel-agent.streamlit.app/`
bằng trình duyệt, gõ tay một câu (vd "What is the weather in St Ives?"), xác
nhận có câu trả lời thật quay về — nếu công cụ tự động vẫn không tương tác
được với textbox, nhờ user tự gõ thử và xác nhận lời.

Việc còn lại (không khẩn, chỉ để hoàn thiện xác nhận):
- Cuộn sidebar xuống xác nhận tool thứ 3 `rank_town_candidates` cũng hiện ra
  (gần như chắc chắn có, vì sidebar chỉ lặp `lab.TOOLS` — nhưng chưa nhìn tận
  mắt trên bản deploy).
- Thử hỏi thật một câu so sánh 2 town ở **cả 2 mode** (ReAct và Multi-agent)
  trên chính domain thật, không chỉ local, để có bằng chứng đầy đủ trước khi
  demo cho người khác xem.
- Không cần secret mới trên Streamlit Cloud — `main_05_multi_agent.py` dùng
  chung `GOOGLE_API_KEY`; `redis_client.get_redis()` tự lùi về `None` an
  toàn nếu không đặt `REDIS_URL`.

### 2.2. Việc lẻ khác (không gấp)

- 46 file trong `career-ops` vẫn ghi số cũ `4.4/5` — mục 5, HANDOFF bản cũ.
- CV repo vs Overleaf lệch nhau (mục "Multi-Agent" trong title) — mục 5,
  HANDOFF bản cũ. **Giờ đã KHÔNG còn là claim suông** — multi-agent thật đã
  code xong (`main_05_multi_agent.py`), có thể ghi thẳng vào CV được rồi.
- CORS `allow_origins=["*"]` và `/metrics` công khai trên Azure — vẫn là
  quyết định mở có chủ ý, chưa ai yêu cầu siết.

---

## 3. Phiên 2026-09-12 đã làm gì — 10 việc, 14 PR, tất cả đã merge vào `main`

Toàn bộ chi tiết + số liệu kiểm chứng nằm ở
`docs/superpowers/CV_CHANGES_2026-09-12.md` (viết riêng cho việc đưa vào CV).
Tóm tắt cực ngắn:

| # | Việc | PR | File chính |
|---|---|---|---|
| 1 | Composite score + fallback cho chọn town | #4, #6, #8 (hotfix) | `main_02_02.py` (`rank_town_candidates`) |
| 3 | Retry khi tool-call sai schema | #5 | `main_02_02.py` (`ToolsExecutionNode`) |
| 4 | Test + chặn prompt injection | #7 | `evals/eval_injection.py`, `main_02_02.py` |
| 5 | Eval 8 → 32 case | #9 | `evals/eval_agent.py` |
| 6 | Multi-agent supervisor (planner+executor) | #10 | `main_05_multi_agent.py` (MỚI) |
| 7 | Lưu lịch sử eval theo thời gian | #11 | `eval_history.py` (MỚI) |
| 9 | API key auth cho FastAPI | #12 | `api.py` |
| 8 | Redis cho rate-limit + cache thời tiết | #13 | `redis_client.py` (MỚI) |
| 10 | Locust load test | #14 | `loadtest/` (MỚI) |
| 2 | Multi-turn memory cho `api.py` | **CHƯA MERGE** | xem mục 2.1 |

Test suite: 81 → **140** (chạy `pytest -q` để xác nhận số hiện tại).
Eval agent: 8 → **32 case**, 100% tool-selection, judge **4.6/5**, cost
**$0.94/1000 câu** (giảm từ $1.13 nhờ sửa `rank_town_candidates`).

Bốn bug thật tìm thấy qua kiểm chứng sống (không phải đoán):
1. `rank_town_candidates` thiếu số liệu thời tiết thô → model tự gọi lại
   `weather_forecast`, có lúc cạn `MAX_TOOL_CALLS` và trả lời RỖNG.
2. LangGraph lọc state con theo đúng schema khai báo — `plan` của planner
   "biến mất" khi qua executor subgraph nếu `AgentState` không khai báo field
   đó.
3. Postgres trả `run_at` là `datetime` thật, không phải chuỗi — làm hỏng
   canh cột trong `evals/history_report.py`.
4. **Tìm thấy trên chính link demo Streamlit** (không phải local): thêm
   `main_05_multi_agent.py` vào `app.py` làm lộ ra một bug đã tiềm ẩn từ
   trước trong `metrics.py` — Prometheus `REGISTRY` là singleton toàn tiến
   trình, nhưng server có cơ chế reload (Streamlit Cloud) có thể thực thi lại
   một module trong CÙNG tiến trình sống, làm `Counter(...)`/`Histogram(...)`
   đăng ký trùng tên → `ValueError: Duplicated timeseries in CollectorRegistry`,
   sập cả app. Sửa bằng cách tra `REGISTRY._names_to_collectors` trước khi
   tạo, trả về metric cũ nếu đã có (hàm `_metric()` trong `metrics.py`) — PR
   `hotfix/prometheus-reimport-crash`, có test chặn tái phát
   (`test_reimporting_the_module_does_not_crash`).

---

## 4. Lệnh hay dùng

```bash
venv\Scripts\python.exe -m pytest -q                    # 140 test
venv\Scripts\python.exe -m evals.eval_agent              # eval 32 case, ghi evals/results.md
venv\Scripts\python.exe -m evals.eval_injection           # 5 case injection, ghi evals/injection_results.md
venv\Scripts\python.exe evals\history_report.py           # xem xu huong chat luong theo thoi gian
venv\Scripts\streamlit.exe run app.py                     # UI
venv\Scripts\python.exe -m uvicorn api:app --reload       # API (API_KEYS, REDIS_URL tuy chon)
locust -f loadtest\locustfile_healthz.py --host http://localhost:8000   # load test mien phi
```

## 5. Đang chạy ở đâu

- Streamlit: https://cornwall-travel-agent.streamlit.app
- API Azure: https://travel-agent-api.nicewave-bb4d94a1.japaneast.azurecontainerapps.io/docs
  (image cũ, CHƯA có API key/Redis/multi-agent — cần build+deploy lại nếu
  muốn đưa những tính năng mới lên đây)
- Image: `ghcr.io/hieuxuan1112/travel-ai-agent` (public, tag theo SHA)

## 6. Quy tắc user đã chốt — không đổi

Giữ nguyên toàn bộ mục "Quy tắc làm việc" và "Quyết định kỹ thuật đã chốt"
trong `CLAUDE.md` — không lặp lại ở đây. Riêng lưu ý mới: `CLAUDE.md` phần
"Bản đồ file" đang ghi `eval_agent.py (8 case)` — **đã lỗi thời**, giờ là 32
case; sửa khi có dịp.
