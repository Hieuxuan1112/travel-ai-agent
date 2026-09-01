# Thư mục học tập

Tài liệu để **học kiến thức nền**, tách khỏi tài liệu mô tả sản phẩm.

- Muốn hiểu **sản phẩm này chạy thế nào** → đọc [../MENTOR.md](../MENTOR.md)
- Muốn học **kiến thức đứng sau nó** → đọc ở đây

## Thứ tự nên đọc

| # | File | Nội dung | Ưu tiên |
|---|---|---|---|
| 0 | [LO_TRINH_HOC.md](LO_TRINH_HOC.md) | **Đọc đầu tiên.** Bản đồ CV → kiến thức, 6 mức ưu tiên P1–P6, lịch 6 tuần, kịch bản nói về từng dòng CV | ⭐ bắt buộc |
| 8 | [HOC_LANGGRAPH.md](HOC_LANGGRAPH.md) | **ĐỌC TRƯỚC TIÊN.** ReAct, State/Node/Edge, tool, guard, trim_messages, checkpointer — bám code thật `main_02_02.py` | ⭐ bắt buộc |
| 9 | [HOC_DSA_OOP.md](HOC_DSA_OOP.md) | Big-O, hash map, two pointers, stack, tree, BFS/DFS, DP + OOP/SOLID/pattern; lộ trình 40 bài LeetCode | ⭐ vòng technical |
| 1 | [HOC_VECTOR_DB.md](HOC_VECTOR_DB.md) | Embedding, cosine, HNSW, chunking, metadata filter, điểm mù của vector search | P3 |
| 2 | [HOC_PROMPT_ENGINEERING.md](HOC_PROMPT_ENGINEERING.md) | Message, few-shot, mô tả tool, structured output, LLM-as-judge, prompt injection | P2 |
| 3 | [HOC_SQL.md](HOC_SQL.md) | JOIN, GROUP BY, subquery, CTE, window function, index, NULL, transaction | ⭐ hay bị hỏi |
| 4 | [HOC_TOAN_AI.md](HOC_TOAN_AI.md) | Vector, cosine, ma trận, softmax, xác suất, gradient descent, p95 | ⭐ nền của P1–P2 |
| 5 | [HOC_FASTAPI_SSE.md](HOC_FASTAPI_SSE.md) | HTTP căn bản, FastAPI, pydantic, Server-Sent Events | đã làm |
| 6 | [HOC_DOCKER.md](HOC_DOCKER.md) | Image/container, multi-stage, non-root, healthcheck, compose, volume | đã làm |
| 7 | [HOC_PROMETHEUS.md](HOC_PROMETHEUS.md) | Counter/Gauge/Histogram, p95, PromQL, Grafana provisioning | đã làm |
| 10 | [HOC_CICD_CLOUD.md](HOC_CICD_CLOUD.md) | CI vs CD, Trivy, GHCR, tag SHA, **OIDC keyless**, Azure Container Apps, scale-to-zero, 5 lần deploy đỏ và cách lần ra lỗi | ⭐ mới, chưa vững |

Mỗi file đều có phần **tự kiểm tra** với đáp án giấu trong `<details>` — trả lời trước rồi
mới mở xem.

## Bốn chương trình chạy được

Đọc mười trang không bằng gõ thử một câu.

```bash
venv\Scripts\python.exe docs\hoc\demo_vector_search.py
```

Tìm kiếm tương tác trên chính 92 chunk của agent. Thêm `--compare` để so độ gần hai câu bất
kỳ, `--demo` để xem 4 ví dụ dựng sẵn (gồm cả ví dụ vector search **thất bại**).

```bash
venv\Scripts\python.exe docs\hoc\demo_prompt_ab.py
```

Ba thí nghiệm về prompt: có/không system prompt, tờ khai tool mà LLM thật sự nhận được, và
mô tả tool rõ ràng vs mơ hồ. Kết quả đo được **trái với kỳ vọng của sách** — phần phân tích
nằm ở mục 5 của `HOC_PROMPT_ENGINEERING.md`.

```bash
venv\Scripts\python.exe docs\hoc\demo_sql.py
```

Cơ sở dữ liệu SQLite trong bộ nhớ với bảng nhân viên/phòng ban/doanh số dựng sẵn. Gõ câu
SQL bất kỳ và xem kết quả ngay. `--demo` chạy lại toàn bộ ví dụ trong bài, `--baitap` xem
lời giải 10 bài tập, `--index` đo thời gian truy vấn trên 200 nghìn dòng trước và sau khi
tạo index.

```bash
venv\Scripts\python.exe docs\hoc\demo_toan_ai.py
```

Minh hoạ bằng số nhỏ tính tay được: cosine giữa các vector 3 chiều, softmax đổi ra sao khi
đổi temperature, gradient descent hội tụ từng bước, và vì sao p95 khác trung bình.
