# Load test — kết quả đo thật

Ngày: 2026-09-12. Mục tiêu (đã ghi trong `docs/hoc/HOC_VAN_HANH_THAT.md` mục 6.1,
chưa ai đo tới giờ): trả lời câu hỏi **"nút thắt khi tải cao là CPU/hạ tầng hay
là quota/độ trễ Gemini?"** bằng số thật thay vì phỏng đoán.

Chạy tại chỗ (`docker compose up api`, image local, không phải Azure), Locust
2.46.5, `RATE_LIMIT_PER_HOUR=30` (mặc định docker-compose).

## Kịch bản 1 — Baseline hạ tầng (`locustfile_healthz.py`)

Bắn `/healthz` — endpoint không chạm tới Gemini, không tốn tiền — để đo trần
CPU/Uvicorn/FastAPI thuần túy.

```
locust -f loadtest/locustfile_healthz.py --host http://localhost:8000 \
    --headless -u 50 -r 10 --run-time 20s --csv loadtest/results_healthz
```

| Chỉ số | Giá trị |
| --- | --- |
| Số request | 2 209 |
| Lỗi | 0 (0%) |
| Throughput | **137 req/s** |
| p50 | 9 ms |
| p95 | **39 ms** |
| p99 | 96 ms |

**Kết luận kịch bản 1:** hạ tầng (Uvicorn + FastAPI + middleware) chịu tải rất
tốt — 50 user đồng thời, p95 dưới 40ms, 0% lỗi. Không có dấu hiệu nghẽn CPU ở
quy mô này.

## Kịch bản 2 — `/chat` thật (`locustfile_chat.py`)

Bắn `/chat` thật — MỖI request gọi Gemini thật, tốn tiền thật. Cố tình giữ quy
mô rất nhỏ (3 user ảo, 20 giây) để có số liệu tin cậy mà không đốt ngân sách:
9 request, chi phí ước tính theo bảng giá đã đo trong `evals/results.md`
(~$1.1/1000 câu) là **dưới 1 cent** cho toàn bộ lần chạy này.

```
locust -f loadtest/locustfile_chat.py --host http://localhost:8000 \
    --headless -u 3 -r 1 --run-time 20s --csv loadtest/results_chat
```

| Chỉ số | Giá trị |
| --- | --- |
| Số request | 9 |
| Lỗi | 0 (0%) |
| Throughput | 0.5 req/s |
| p50 | 3,7 s |
| p95 | **7,6 s** |
| Max | 7,6 s |

## Trả lời câu hỏi gốc

**Nút thắt là Gemini, không phải CPU.** Bằng chứng: hạ tầng xử lý được 137
req/s (kịch bản 1) nhưng mỗi request `/chat` tự nó đã mất 3,7–7,6 giây
(kịch bản 2) — độ trễ này đến từ vòng lặp ReAct gọi Gemini nhiều lượt
(search → weather → trả lời), không phải từ việc server bận. Muốn tăng
throughput thật của `/chat`, việc cần làm là giảm số lượt gọi Gemini mỗi câu
hỏi hoặc chạy song song nhiều instance sau load balancer (khi đó rate limit
phải chuyển sang Redis — xem `redis_client.py` — để chia sẻ đúng giữa các
instance thay vì mỗi instance đếm riêng).

## Chưa đo (đừng bịa)

- Hành vi khi vượt `RATE_LIMIT_PER_HOUR` dưới tải đồng thời cao (throughput
  test ở đây quá ngắn/nhỏ để chạm ngưỡng 30/giờ một cách có ý nghĩa).
- p95 khi chạy nhiều instance thật sau load balancer.
- Chi phí/độ trễ trên Azure Container Apps thật (test này chạy local qua
  docker-compose, không phải bản deploy).
