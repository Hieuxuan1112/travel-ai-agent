# Thư mục học tập

Tài liệu để **học kiến thức nền**, tách khỏi tài liệu mô tả sản phẩm.

- Muốn hiểu **sản phẩm này chạy thế nào** → đọc [../MENTOR.md](../MENTOR.md)
- Muốn học **kiến thức đứng sau nó** → đọc ở đây

## Thứ tự nên đọc

| # | File | Nội dung | Ưu tiên |
|---|---|---|---|
| 0 | [LO_TRINH_HOC.md](LO_TRINH_HOC.md) | **Đọc đầu tiên.** Bản đồ CV → kiến thức, 6 mức ưu tiên P1–P6, lịch 6 tuần, kịch bản nói về từng dòng CV | ⭐ bắt buộc |
| 1 | [HOC_VECTOR_DB.md](HOC_VECTOR_DB.md) | Embedding, cosine, HNSW, chunking, metadata filter, điểm mù của vector search | P3 |
| 2 | [HOC_PROMPT_ENGINEERING.md](HOC_PROMPT_ENGINEERING.md) | Message, few-shot, mô tả tool, structured output, LLM-as-judge, prompt injection | P2 |
| 3 | [HOC_FASTAPI_SSE.md](HOC_FASTAPI_SSE.md) | HTTP căn bản, FastAPI, pydantic, Server-Sent Events | đã làm |
| 4 | [HOC_DOCKER.md](HOC_DOCKER.md) | Image/container, multi-stage, non-root, healthcheck, compose, volume | đã làm |
| 5 | [HOC_PROMETHEUS.md](HOC_PROMETHEUS.md) | Counter/Gauge/Histogram, p95, PromQL, Grafana provisioning | đã làm |

Mỗi file đều có phần **tự kiểm tra** với đáp án giấu trong `<details>` — trả lời trước rồi
mới mở xem.

## Hai chương trình chạy được

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

## Còn thiếu

Hai chủ đề đã lên kế hoạch nhưng chưa soạn: **SQL** và **toán tối thiểu cho AI**. Khi soạn
xong thì đặt vào đây với tên `HOC_SQL.md` và `HOC_TOAN_AI.md`.
