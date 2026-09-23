# Vận hành thật — hỏng, tải cao, và những gì CHƯA đo

> Mười sáu tài liệu còn lại trả lời *"hệ thống chạy thế nào"*. Bài này trả lời ba câu mà
> phỏng vấn senior hay hỏi và tài liệu cũ chưa phủ:
>
> 1. **Cái gì hỏng thì chuyện gì xảy ra?**
> 2. **Gấp 10 lần lưu lượng thì cái gì vỡ trước?**
> 3. **Bạn biết điều đó vì đã đo, hay vì đoán?**
>
> **Nguyên tắc xuyên suốt bài này: không bịa số.** Chỗ nào chưa đo thì ghi thẳng
> **"CHƯA ĐO"** kèm cách đo. Một con số bịa trên CV hay trong phỏng vấn hại hơn là nói
> "em chưa đo cái đó".

**Mục lục**

1. [Bảng trung thực: đã đo và chưa đo](#1-bảng-trung-thực-đã-đo-và-chưa-đo)
2. [Phân tích hỏng hóc — từng bộ phận một](#2-phân-tích-hỏng-hóc--từng-bộ-phận-một)
3. [Suy giảm êm — hỏng một phần vẫn dùng được](#3-suy-giảm-êm--hỏng-một-phần-vẫn-dùng-được)
4. [Gấp 10 lần: cái gì vỡ trước](#4-gấp-10-lần-cái-gì-vỡ-trước)
5. [Gấp 100 lần: phải đổi kiến trúc chỗ nào](#5-gấp-100-lần-phải-đổi-kiến-trúc-chỗ-nào)
6. [Sáu thí nghiệm chạy được ngay](#6-sáu-thí-nghiệm-chạy-được-ngay)
7. [Tự kiểm tra](#7-tự-kiểm-tra)
8. [Trả lời phỏng vấn](#8-trả-lời-phỏng-vấn)

---

## 1. Bảng trung thực: đã đo và chưa đo

Đây là bảng quan trọng nhất tài liệu. Học thuộc **cả cột phải**.

### Đã đo thật

| Chỉ số | Giá trị | Đo bằng gì |
|---|---|---|
| p95 latency (thật, production) | **7,55 s** | Prometheus histogram, `monitoring/` |
| Latency trung bình (eval) | **6,7 s** | 32 ca eval, `evals/results.md` |
| Tool-selection accuracy | **100%** (32/32) | `evals/eval_agent.py` |
| Answer quality (LLM-judge) | **4,6/5** | Cùng trên |
| Chi phí | **$0,94 / 1000 câu** | `evals/results.md` (giảm từ $1,13 nhờ sửa `rank_town_candidates`) |
| Token một lượt eval | 83.030 vào / 6.167 ra | `usage_metadata` từ API |
| Injection-refusal (adversarial) | **5/5**, 0/5 rò rỉ thật | `evals/eval_injection.py`, 5 ca |
| Recall@1 / @3 (vector) | **92% / 100%** | `evals/eval_retrieval.py`, 12 câu |
| So sánh 7 model | Bảng đầy đủ | `evals/compare_models.py` |
| Test | **141 passed, ~25 s** | `pytest -q` |
| Kho kiến thức | 92 chunk, 3,3 MB | Đếm trực tiếp |
| Docker image | 1,45 GB, rebuild ~15 s | `docker build` |
| **Throughput hạ tầng** (baseline, `/healthz`) | **137 req/s**, p95 **39 ms**, p99 96 ms, 0% lỗi (50 user đồng thời) | Locust, `loadtest/results.md` mục kịch bản 1 |
| **Latency `/chat` thật dưới tải** | p50 **3,7 s**, p95 **7,6 s**, 0% lỗi (3 user đồng thời, 9 request) | Locust, `loadtest/results.md` mục kịch bản 2 |

### CHƯA ĐO — và cách đo

| Chỉ số | Vì sao chưa có | Đo bằng cách nào |
|---|---|---|
| **p99 latency** | Histogram **tính được**, nhưng chưa có đủ lưu lượng thật để con số có nghĩa | `histogram_quantile(0.99, ...)` sau khi có tải |
| **`/chat` thật ở tải cao** (>3 user đồng thời) | Load test `/chat` cố tình chạy ở quy mô rất nhỏ (3 user) để không đốt quota Gemini thật | Tăng dần `-u`, xem mục 6.1 |
| **Rate limit dưới tải cao** | Cửa sổ test quá ngắn để chạm ngưỡng `RATE_LIMIT_PER_HOUR` một cách có ý nghĩa | Xem `loadtest/results.md` mục "Chưa đo" |
| **CPU / RAM lúc tải `/chat` thật** | Chưa profile | `docker stats` lúc load test; `py-spy` để soi sâu |
| **Kế hoạch truy vấn database** (SlangWord) | Chưa chạy `EXPLAIN ANALYZE` | Xem mục 6.4 |
| **Cold start Azure** | Tài liệu ghi "~15-20 s" — đó là **quan sát, không phải đo có hệ thống** | Đo 20 lần sau khi ngủ, lấy p50/p95 |
| **Giới hạn connection của Neon** | Chưa chạm trần | Tăng `max_size` của pool và quan sát |
| **Hạ tầng thật trên Azure** | Load test ở trên chạy local qua `docker-compose`, không phải bản deploy | Lặp lại kịch bản nhắm vào URL Azure |

> **Cách nói trong phỏng vấn:** *"Baseline hạ tầng em đã đo bằng Locust: 137 req/s, p95 39ms,
> 0% lỗi. `/chat` thật (gọi Gemini) thì p95 là 7,6 giây — chứng minh nút thắt là Gemini chứ
> không phải server. Cái em CHƯA đo là `/chat` ở tải cao thật sự, vì mỗi request tốn tiền thật
> nên em cố tình giữ quy mô nhỏ (3 user, dưới 1 cent cho cả lần chạy)."*
>
> Câu này **mạnh hơn** một con số bịa, vì nó cho thấy bạn biết ranh giới hiểu biết của mình
> và biết cách mở rộng nó. Người phỏng vấn giỏi **kiểm tra được** con số bịa.

---

## 2. Phân tích hỏng hóc — từng bộ phận một

Với mỗi bộ phận: hỏng thì sao, hệ thống hiện xử lý thế nào, còn hở gì.

### 2.1 API Gemini hỏng hoặc quá tải

| | |
|---|---|
| **Triệu chứng** | `429` (hết quota) hoặc `5xx` từ Google |
| **Hiện xử lý** | Có **thử lại kèm chờ tăng dần** (backoff). Hết lần thử thì trả lỗi có cấu trúc |
| **Người dùng thấy** | Câu trả lời chậm hơn, hoặc thông báo lỗi rõ ràng — **không phải trang trắng** |
| **Còn hở** | Không có **circuit breaker**: khi Gemini chết hẳn, mọi request vẫn cố thử rồi mới chịu thua → tốn thời gian vô ích cho từng người |

**Circuit breaker là gì và khi nào cần:** sau N lần lỗi liên tiếp thì **ngừng thử luôn** trong
một khoảng, trả lỗi ngay. Ba trạng thái: đóng (chạy bình thường) → mở (chặn hết) → hé mở (thử
một request xem đã khỏi chưa).

Vì sao đáng: khi tầng dưới chết, thử lại chỉ **làm nó chết lâu hơn** và bắt người dùng chờ vô
ích. Với quy mô demo hiện tại thì chưa cần; có nhiều người dùng thì cần.

### 2.2 API thời tiết (Open-Meteo) hỏng

| | |
|---|---|
| **Hiện xử lý** | Tool **bắt lỗi và trả kết quả có cấu trúc**, không ném exception |
| **Agent làm gì** | Đọc được nội dung lỗi đó như mọi kết quả khác → tự quyết định: thử thị trấn khác, hoặc trả lời bằng thông tin du lịch và **nói rõ chưa lấy được thời tiết** |
| **Có test không** | ✅ `test_service_failure_is_reported_as_error_not_exception` |

Đây là **ví dụ tốt nhất về suy giảm êm** trong dự án: mất một tool nhưng agent vẫn trả lời
được phần còn lại. Xem mục 3.

### 2.3 PostgreSQL (Neon) hỏng

| | |
|---|---|
| **Triệu chứng** | Neon ngủ dậy chậm, hoặc hết giờ compute của gói free |
| **Hiện xử lý** | Pool đặt `check=ConnectionPool.check_connection` — connection chết sau khi Neon ngủ được **mở lại**, thay vì để request đầu tiên lãnh đủ |
| **Còn hở nghiêm trọng** | Nếu Neon **chết hẳn**, `get_checkpointer()` ném lỗi lúc khởi động → **app không lên được**, dù bản thân agent không cần database để trả lời |

**Đây là lỗ hổng thiết kế đáng nói ra.** `persistence.py` đã có sẵn đường lui về
`InMemorySaver` khi **thiếu** `DATABASE_URL`, nhưng **không** có đường lui khi có biến mà kết
nối hỏng. Đúng ra nên: thử Postgres, hỏng thì ghi log cảnh báo và lui về in-memory — mất lịch
sử còn hơn mất cả dịch vụ.

*Vì sao chưa sửa:* nó đổi hành vi khởi động và cần bàn (im lặng lui về in-memory cũng nguy
hiểm — người dùng tưởng đang lưu mà không lưu). Nêu ra được đánh đổi này quan trọng hơn là vá
vội.

### 2.4 Vector store rỗng hoặc hỏng

| | |
|---|---|
| **Từng xảy ra thật** | Docker tạo thư mục rỗng khi gắn volume → `os.path.isdir` trả `True` mà **không có chunk nào** |
| **Triệu chứng khi đó** | Agent trả lời "không tìm thấy thông tin" — **không báo lỗi gì cả**, loại hỏng tệ nhất |
| **Hiện xử lý** | Kiểm tra **nội dung** chứ không chỉ sự tồn tại: `if not cached.get(limit=1)["ids"]` → dựng lại |
| **Có test không** | ✅ `test_existing_but_empty_store_directory_triggers_a_rebuild` |

### 2.5 Container chết

| | |
|---|---|
| **Phát hiện** | Docker healthcheck gọi `/healthz` định kỳ |
| **Xử lý** | Không trả lời → tự khởi động lại |
| **Mất gì khi restart** | **Bộ đếm rate limit** (trong RAM) và **bộ đếm metrics**. Hội thoại thì **không mất** vì nằm dưới Postgres |

Chi tiết đã lường trước: `/healthz` **được miễn rate limit** và **vẫn xanh khi `AI_ENABLED=0`**
— nếu không, hệ thống điều phối sẽ khởi động lại một container đang khoẻ hoặc một container ta
cố ý tắt.

### 2.6 Request trùng lặp

**Chưa có xử lý, và với dự án này thì chấp nhận được** — vì `/chat` chỉ **đọc**: gọi hai lần
tốn tiền gấp đôi nhưng không làm hỏng dữ liệu.

Nếu sau này có thao tác **ghi** (đặt phòng, thanh toán) thì bắt buộc phải có **idempotency
key**: client sinh một khoá cho mỗi thao tác, server nhớ khoá đã xử lý và trả lại kết quả cũ
thay vì làm lần nữa. Đây là câu hỏi phỏng vấn backend rất hay gặp.

---

## 3. Suy giảm êm — hỏng một phần vẫn dùng được

**Graceful degradation** = mất một phần thì phục vụ ít hơn, chứ không sập hẳn.

| Cái gì hỏng | Hệ thống làm gì | Người dùng vẫn được gì |
|---|---|---|
| API thời tiết | Tool trả lỗi có cấu trúc, agent đọc được | Thông tin du lịch từ RAG |
| Vector store rỗng | Tự dựng lại | Chậm lần đầu, sau đó bình thường |
| Vượt `MAX_TOOL_CALLS` | **Trả lời bằng những gì đã có** | Câu trả lời chưa đầy đủ, còn hơn màn hình lỗi |
| Vượt rate limit | `429` + `Retry-After` + **chỉ đường chạy local** | Biết chờ bao lâu và có lối khác |
| `AI_ENABLED=0` | `503` cho AI, `/healthz` vẫn xanh | Dịch vụ không bị khởi động lại nhầm |
| **Postgres chết** | ❌ **App không lên được** | ❌ Không gì cả |

Dòng cuối là chỗ duy nhất **chưa êm**. Nêu được đúng một chỗ hở trong bảng của chính mình
là dấu hiệu đã nghĩ nghiêm túc, không phải liệt kê cho đẹp.

---

## 4. Gấp 10 lần: cái gì vỡ trước

Hiện tại là demo cá nhân. Giả sử lên **10 lần** lưu lượng, đây là thứ vỡ theo thứ tự — và
**phải nói rõ đây là suy luận, chưa phải kết quả đo**.

| Thứ tự | Cái gì vỡ | Vì sao | Sửa thế nào |
|---|---|---|---|
| **1** | **Quota / hoá đơn Gemini** | Mỗi câu hỏi là tiền thật, không có trần | Ngân sách toàn cục (đã có), cache câu trả lời, model rẻ hơn |
| **2** | **Rate limit đếm sai** | Chỉ khi KHÔNG có `REDIS_URL`: bộ đếm trong RAM, 2 replica là gấp đôi giới hạn thật | Đã có: `redis_client.py` chuyển bộ đếm sang Redis khi bật `REDIS_URL` — bản đang chạy trên Azure hiện là image cũ, chưa bật |
| **3** | **Connection pool Postgres** | `max_size=4`, gói Neon free có trần connection | Tăng pool, hoặc pooler ngoài (PgBouncer) |
| **4** | Cold start Azure | `min-replicas 0` → request đầu chờ ~15-20 s | Đặt `min-replicas 1` (mất tiền) |

**Điểm mấu chốt để nói trong phỏng vấn:** nút thắt đầu tiên **không phải CPU hay RAM**. Với
ứng dụng LLM, hệ thống dành phần lớn thời gian **chờ API bên ngoài** — nó là *I/O-bound*, không
phải *CPU-bound*. Nút thắt là **quota và tiền**, không phải sức máy.

Nhận ra điều này quan trọng vì nó đổi hoàn toàn hướng tối ưu: thêm CPU **không giúp gì cả**.

> **Đã đo một phần:** hạ tầng thuần (`/healthz`) chịu được 137 req/s, p95 39ms, 0% lỗi ở 50 user
> đồng thời — xem mục 6.1. **Chưa đo:** mức đồng thời cụ thể nào làm `/chat` thật (đường có gọi
> Gemini) bắt đầu vỡ — load test `/chat` mới chạy ở quy mô rất nhỏ (3 user) để không đốt quota
> thật.

---

## 5. Gấp 100 lần: phải đổi kiến trúc chỗ nào

Ở mức này thì vá vặt không đủ, phải đổi hình dạng hệ thống:

| Việc | Hiện tại | Ở quy mô 100x |
|---|---|---|
| **Rate limit** | **Đã có Redis** (`redis_client.py`, sliding window) khi bật `REDIS_URL`; bản Azure đang chạy là image cũ chưa bật | Bật `REDIS_URL` khi deploy lại — logic không đổi, chỉ đổi nơi lưu |
| **Trả lời** | Tính lại từ đầu mỗi lần | **Cache theo câu hỏi** — câu hay lặp thì trả ngay |
| **Vector store** | Chroma trên đĩa, nướng vào image | Vector DB chạy riêng (pgvector/Qdrant) — nhiều replica cùng đọc |
| **Câu hỏi dài** | Chờ đồng bộ 8 giây | **Hàng đợi + worker**: nhận việc trả `202`, xong thì báo |
| **Model** | Một model cho mọi câu | **Định tuyến**: câu dễ dùng model rẻ, câu khó mới dùng model đắt |
| **Database** | Một Neon | Bản sao chỉ đọc, tách đọc/ghi |

### Vì sao "thêm nhiều máy" không đủ

Agent này **không giữ trạng thái trong RAM** giữa các request (state nằm dưới Postgres), nên
về mặt kỹ thuật scale ngang được ngay. Nhưng ba thứ **dùng chung** không tự nhân lên:

1. **Quota Gemini** — 10 máy vẫn chung một API key và một hạn mức
2. **Bộ đếm rate limit** — mỗi máy đếm riêng thì giới hạn thật gấp 10 (trừ khi bật `REDIS_URL`,
   lúc đó các máy dùng chung một bộ đếm)
3. **Connection tới database** — mỗi máy một pool, database có trần

> **Nguyên tắc:** scale ngang chỉ giải quyết được nút thắt **ở trong** ứng dụng. Nút thắt ở
> **tài nguyên dùng chung** thì càng thêm máy càng chạm trần nhanh hơn.

### Câu hỏi phải hỏi trước khi làm bất cứ điều nào ở trên

*"Chúng ta có thật sự ở quy mô đó chưa?"* Dựng Redis, hàng đợi, worker cho một demo có 20 người
dùng là **kỹ thuật thừa** — thêm bộ phận để hỏng mà không giải quyết vấn đề nào đang có.

Câu trả lời tốt trong phỏng vấn: *"Em biết phải đổi gì ở quy mô đó, và em cũng biết mình chưa
ở quy mô đó nên chưa làm."*

---

## 6. Sáu thí nghiệm chạy được ngay

Mỗi thí nghiệm theo khuôn: **giả thuyết → cách làm → đo gì → kết luận rút ra được**.
Mục 6.1 đã chạy thật, kết quả lấy từ `loadtest/results.md` — các mục 6.2–6.6 còn **cố ý để
trống**, bạn chạy rồi tự điền, đó mới là số của bạn.

### 6.1 Load test — tìm nút thắt đầu tiên (ĐÃ CHẠY)

**Giả thuyết:** nút thắt là quota/độ trễ Gemini chứ không phải CPU/hạ tầng.

**Cách làm:** hai kịch bản Locust, quy mô nhỏ có kiểm soát để không đốt quota thật:

```bash
# Kịch bản 1 — /healthz, không chạm Gemini, đo trần hạ tầng thuần
locust -f loadtest/locustfile_healthz.py --host http://localhost:8000 \
    --headless -u 50 -r 10 --run-time 20s --csv loadtest/results_healthz

# Kịch bản 2 — /chat thật, MỖI request gọi Gemini thật (tốn tiền thật, giữ quy mô nhỏ)
locust -f loadtest/locustfile_chat.py --host http://localhost:8000 \
    --headless -u 3 -r 1 --run-time 20s --csv loadtest/results_chat
```

**Kết quả thật** (chạy local qua `docker-compose`, không phải Azure — xem `loadtest/results.md`):

| Kịch bản | Request | Lỗi | Throughput | p50 | p95 | p99 |
|---|---|---|---|---|---|---|
| 1 — `/healthz` (baseline hạ tầng) | 2.209 | 0% | **137 req/s** | 9 ms | **39 ms** | 96 ms |
| 2 — `/chat` thật (50 user → chỉ 3, để giữ chi phí <1 cent) | 9 | 0% | 0,5 req/s | 3,7 s | **7,6 s** | — |

**Kết luận rút ra:** hạ tầng thuần chịu tải tốt (p95 39ms ở 50 user đồng thời, 0% lỗi) — không
có dấu hiệu nghẽn CPU. Mỗi request `/chat` tự nó đã mất 3,7–7,6 giây vì vòng ReAct gọi Gemini
nhiều lượt — **nút thắt là Gemini, không phải server**, đúng như giả thuyết. Muốn có con số
p95/lỗi của `/chat` ở tải cao hơn 3 user thật thì phải chấp nhận đốt quota Gemini thật để đo —
đó là phần **còn để trống**, chưa làm vì chi phí.

### 6.2 Cache câu trả lời có đáng không

**Giả thuyết:** trong bộ 32 câu eval, cache làm giảm chi phí đáng kể nếu câu hỏi lặp lại.

**Cách làm:** thêm một `dict` cache khoá theo câu hỏi đã chuẩn hoá, chạy eval **hai lần**.

**Đo gì:** `$/1000 câu` và latency trước/sau; **tỉ lệ trúng cache**.

**Bẫy phải nêu:** câu hỏi thời tiết **không được cache lâu** — thời tiết đổi. Đây chính là bài
toán *cache invalidation*, và là lý do cache không phải lúc nào cũng đúng.

### 6.3 Hạ `MAX_TOOL_CALLS` xuống 4

**Giả thuyết:** hạ trần tiết kiệm tiền nhưng làm hỏng các câu nhiều bước — chính là các câu
gọi 5 tool.

**Cách làm:** `MAX_TOOL_CALLS=4` rồi chạy `python -m evals.eval_agent`.

**Đo gì:** chất lượng, chi phí, latency, số ca chạm trần.

**Kết luận rút ra:** đường cong đánh đổi giữa **ngân sách bước** và **chất lượng** — trả lời
được câu *"vì sao lại chọn 8?"* bằng dữ liệu thay vì bằng cảm giác.

### 6.4 `EXPLAIN ANALYZE` trên SlangWord

**Giả thuyết:** index GIN `pg_trgm` (migration `V2`) thật sự được dùng, và nhanh hơn hẳn quét
tuần tự.

**Cách làm:**

```sql
EXPLAIN ANALYZE SELECT * FROM slang_word WHERE lower(word) LIKE '%lol%';
```

Rồi tạm tắt index để so:

```sql
SET enable_seqscan = off;   -- ep dung index
SET enable_indexscan = off; -- ep quet tuan tu, de so
```

**Đo gì:** `Bitmap Index Scan` hay `Seq Scan`, và `actual time`.

**Kết luận rút ra:** biến một quyết định đã viết trong comment thành **bằng chứng đo được**.
Đây là thí nghiệm đáng giá nhất cho phỏng vấn backend.

### 6.5 Bơm lỗi vào API thời tiết

**Giả thuyết:** tool hỏng thì agent vẫn trả lời được bằng RAG (suy giảm êm ở mục 3).

**Cách làm:** trỏ `weather_forecast` vào một URL chết, rồi hỏi câu cần thời tiết.

**Đo gì:** agent có sập không, câu trả lời có **nói rõ** là thiếu dữ liệu thời tiết không,
`agent_tool_errors_total` có tăng không.

### 6.6 Đo cold start Azure cho tử tế

**Giả thuyết:** cold start ~15-20 giây như tài liệu ghi — nhưng đó mới là **quan sát vài lần**.

**Cách làm:** để app ngủ (không gọi 30 phút), rồi đo lần gọi đầu. Lặp **20 lần**.

```bash
curl -o /dev/null -s -w "%{time_total}\n" https://travel-agent-api.../healthz
```

**Đo gì:** p50 và p95 của thời gian đó.

**Kết luận rút ra:** thay một câu ước lượng trong tài liệu bằng một con số có phân phối —
và biết được `min-replicas 0` thật sự tốn của người dùng bao nhiêu.

---

## 7. Tự kiểm tra

**1.** p95 của dự án là bao nhiêu, và throughput là bao nhiêu?

<details><summary>Đáp án</summary>

p95 (production, Prometheus) = **7,55 giây**. Throughput hạ tầng thuần (Locust, `/healthz`,
50 user) = **137 req/s, p95 39ms, 0% lỗi**. `/chat` thật dưới tải nhỏ (3 user) = p95 **7,6
giây**, khớp với số đo production. Cái **chưa đo** là `/chat` ở tải cao hơn 3 user — mỗi
request tốn tiền thật nên chưa đốt quota để đo tới mức đó. **Nói rõ ranh giới đó** là đáp án
đúng, bịa thêm một con số ở phần chưa đo là sai.
</details>

**2.** Gấp 10 lần lưu lượng thì cái gì vỡ trước, và vì sao không phải CPU?

<details><summary>Đáp án</summary>

**Quota và hoá đơn Gemini** vỡ trước. Vì ứng dụng LLM dành phần lớn thời gian **chờ API bên
ngoài** — nó *I/O-bound* chứ không *CPU-bound*. Thêm CPU không giúp gì. Sau đó tới bộ đếm rate
limit đếm sai khi có nhiều replica, rồi connection pool.
</details>

**3.** API thời tiết chết thì người dùng thấy gì?

<details><summary>Đáp án</summary>

Vẫn nhận được câu trả lời, dựa trên thông tin du lịch từ RAG, và agent **nói rõ** là chưa lấy
được thời tiết. Được vậy vì tool **bắt lỗi và trả kết quả có cấu trúc** thay vì ném exception
— agent đọc lỗi đó như mọi kết quả khác rồi tự quyết. Có test canh điều này.
</details>

**4.** Postgres chết thì sao?

<details><summary>Đáp án</summary>

**App không lên được** — đây là chỗ hở thật của hệ thống. `persistence.py` có đường lui về
`InMemorySaver` khi **thiếu** `DATABASE_URL`, nhưng không có đường lui khi có biến mà kết nối
hỏng. Đúng ra nên lui về in-memory kèm cảnh báo: mất lịch sử còn hơn mất cả dịch vụ.
</details>

**5.** Thêm 10 máy có giải quyết được mọi thứ không?

<details><summary>Đáp án</summary>

Không. Agent không giữ trạng thái trong RAM nên scale ngang được, nhưng ba thứ **dùng chung**
không nhân lên: **quota Gemini** (chung một key), **bộ đếm rate limit** (mỗi máy đếm riêng →
giới hạn thật gấp 10), và **trần connection của database**. Scale ngang chỉ giải quyết nút
thắt bên trong ứng dụng.
</details>

**6.** Vì sao `/chat` không cần idempotency key?

<details><summary>Đáp án</summary>

Vì nó chỉ **đọc** — gọi hai lần tốn tiền gấp đôi nhưng không làm hỏng dữ liệu. Có thao tác
**ghi** (đặt phòng, thanh toán) thì bắt buộc phải có: client sinh khoá cho mỗi thao tác, server
nhớ khoá đã xử lý và trả kết quả cũ thay vì làm lần nữa.
</details>

---

## 8. Trả lời phỏng vấn

1. *Hiệu năng hệ thống của bạn thế nào?* → **p95 = 7,55 giây** (production, Prometheus). Em
   cũng đã load test bằng Locust: hạ tầng thuần chịu **137 req/s, p95 39ms, 0% lỗi** (50 user);
   `/chat` thật thì p95 **7,6 giây**, khớp với số production — chứng minh nút thắt là Gemini
   chứ không phải server. Cái em chưa đo là `/chat` ở tải cao hơn 3 user, vì mỗi request tốn
   tiền thật.

2. *Gấp 10 lần thì cái gì vỡ trước?* → **Quota và hoá đơn Gemini**, không phải CPU. Ứng dụng
   LLM là **I/O-bound** — phần lớn thời gian chờ API ngoài. Thêm CPU không giúp gì. Tiếp theo
   là bộ đếm rate limit — nhưng chỉ khi KHÔNG bật `REDIS_URL`; code đã hỗ trợ Redis, bản đang
   chạy trên Azure là image cũ chưa bật.

3. *Có bộ phận nào hỏng làm sập cả hệ thống không?* → Có: **Postgres**. Đây là chỗ hở em biết
   nhưng chưa vá. Có đường lui khi *thiếu* biến môi trường, nhưng chưa có khi *kết nối hỏng*.
   Đúng ra nên lui về in-memory kèm cảnh báo — nhưng lui im lặng cũng nguy hiểm vì người dùng
   tưởng đang lưu, nên em muốn cân nhắc kỹ trước khi sửa.

4. *Bạn xử lý lỗi từ dịch vụ bên ngoài thế nào?* → Thử lại kèm chờ tăng dần, và tool **trả lỗi
   có cấu trúc thay vì ném exception** để agent tự quyết đường đi tiếp. Còn thiếu **circuit
   breaker** — khi dịch vụ chết hẳn, mọi request vẫn cố thử. Với quy mô này thì chưa cần.

5. *Làm sao bạn biết một tối ưu có tác dụng?* → Đo trước, sửa, đo lại. Em đã làm đúng vậy với
   chất lượng: 3,5 → 4,6/5, **và ghi nhận cả cái giá** — chi phí tăng 11% vì câu trả lời dài
   hơn.

6. *Bạn sẽ chạy thí nghiệm gì tiếp theo?* → Load test `/chat` thật ở mức đồng thời cao hơn (đã
   làm ở quy mô nhỏ, 3 user), và `EXPLAIN ANALYZE` trên SlangWord để chứng minh index GIN đang
   được dùng — hiện đó mới là điều em *tin*, chưa phải điều em *đo*.

---

## 9. Liên quan

- [../MENTOR.md](../MENTOR.md) mục 9.8 — Prometheus, p95 vs trung bình
- [HOC_PROMETHEUS.md](HOC_PROMETHEUS.md) — histogram, PromQL, Grafana
- [HOC_BAO_MAT_AI_APP.md](HOC_BAO_MAT_AI_APP.md) — rate limit, công tắc ngắt
- [HOC_BACKEND_API.md](HOC_BACKEND_API.md) — index, connection pool, transaction
- [HOC_LLM_NEN_TANG.md](HOC_LLM_NEN_TANG.md) mục 8 — giảm chi phí, đòn bẩy lớn nhất
