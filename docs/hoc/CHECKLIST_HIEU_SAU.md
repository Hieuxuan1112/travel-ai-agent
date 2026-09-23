# Checklist hiểu sâu — tự chấm xem đã thật sự hiểu chưa

> Đọc xong một tài liệu và **hiểu** nó là hai chuyện khác nhau. Chữ đọc qua thì thấy quen, cảm
> giác quen bị nhầm thành hiểu, và tới lúc phỏng vấn mới lộ ra là không nói được.
>
> **Cách dùng file này: đóng hết code và tài liệu lại, rồi tự trả lời thành tiếng.** Nói vấp,
> nói vòng vo, hoặc phải mở file ra xem — nghĩa là chưa hiểu, không phải "hiểu rồi mà quên".
>
> Với **mỗi** công nghệ, bạn phải trả lời được **bảy câu**:
>
> 1. Nó là gì? 2. Vì sao dùng nó? 3. Trong dự án này nó chạy thế nào? 4. Có cách nào khác?
> 5. Đánh đổi là gì? 6. Hỏng thì sao? 7. Đo bằng gì?
>
> Câu **5, 6, 7** là chỗ phân biệt người hiểu thật với người thuộc bài. Ba câu đó không có
> trong tutorial nào.

**Mục lục**

1. [Cách tự chấm](#1-cách-tự-chấm)
2. [Bản đồ công nghệ — tra nhanh](#2-bản-đồ-công-nghệ--tra-nhanh)
3. [Checklist: dự án AI](#3-checklist-dự-án-ai)
4. [Checklist: dự án SlangWord](#4-checklist-dự-án-slangword)
5. [Checklist: hạ tầng và vận hành](#5-checklist-hạ-tầng-và-vận-hành)
6. [Mười hai con số phải thuộc](#6-mười-hai-con-số-phải-thuộc)
7. [Mười câu "chưa đo" phải nhớ](#7-mười-câu-chưa-đo-phải-nhớ)
8. [Lịch tự chấm](#8-lịch-tự-chấm)

---

## 1. Cách tự chấm

Với mỗi mục, tự cho một mức:

| Mức | Nghĩa là |
|---|---|
| ⬜ **Chưa biết** | Chưa đọc, hoặc đọc rồi mà không nhớ gì |
| 🟨 **Nói được là gì** | Định nghĩa được, nhưng chưa nói được *vì sao chọn* |
| 🟩 **Nói được vì sao** | Nêu được phương án khác và lý do loại |
| 🟦 **Nói được cái giá** | Nêu được đánh đổi, giới hạn, và cách đo |

**Mục tiêu trước khi đi phỏng vấn:** mọi dòng ⭐ phải đạt 🟦, các dòng còn lại tối thiểu 🟩.

Đừng tự lừa. Nếu bạn nói được *"Chroma là vector database"* mà không nói được *"vì sao không
phải FAISS"* thì đó là 🟨, không phải 🟩.

---

## 2. Bản đồ công nghệ — tra nhanh

Dùng bảng này để biết **học cái gì thì mở file nào**.

| Công nghệ | Dùng ở đâu | File code chính | Tài liệu |
|---|---|---|---|
| **LangGraph / ReAct** ⭐ | Vòng lặp agent | `main_02_02.py` | `HOC_LANGGRAPH.md` |
| **Chroma + embedding** ⭐ | RAG | `main_02_02.py`, `retrieval.py` | `HOC_VECTOR_DB.md` |
| **BM25 + RRF** | Hybrid search (tắt) | `retrieval.py` | `MENTOR.md` 7.6 |
| **Gemini API** | Model chat + embedding | `main_02_02.py` | `HOC_LLM_NEN_TANG.md` |
| **FastAPI + SSE** ⭐ | HTTP API | `api.py` | `HOC_FASTAPI_SSE.md` |
| **Prometheus** | Đo lường | `metrics.py`, `monitoring/` | `HOC_PROMETHEUS.md` |
| **LangGraph checkpointer** ⭐ | Nhớ hội thoại | `persistence.py` | `MENTOR.md` 21 |
| **PostgreSQL (Neon)** | Lưu hội thoại | `persistence.py` | `MENTOR.md` 21 |
| **Eval + LLM-as-judge** ⭐ | Đo chất lượng | `evals/` | `MENTOR.md` 10 |
| **MCP** | Phơi tool ra ngoài | `mcp_server.py` | `MENTOR.md` 8 |
| **Rate limit + kill switch** ⭐ | Chống lạm dụng | `api.py`, `app.py` | `HOC_BAO_MAT_AI_APP.md` |
| **Docker** ⭐ | Đóng gói | `Dockerfile` | `HOC_DOCKER.md` |
| **GitHub Actions** ⭐ | CI/CD | `.github/workflows/` | `HOC_CICD_CLOUD.md` |
| **Trivy** | Quét lỗ hổng image | `cd.yml` | `HOC_CICD_CLOUD.md` 3 |
| **OIDC keyless** ⭐ | Xác thực với Azure | `cd.yml` | `HOC_CICD_CLOUD.md` 5 |
| **Azure Container Apps** | Chạy API | `cd.yml` | `MENTOR.md` 22 |
| **Spring Boot** ⭐ | Backend SlangWord | `backend/` | `HOC_BACKEND_API.md` |
| **JWT + refresh rotation** ⭐ | Xác thực SlangWord | `security/`, `RefreshTokenService` | `HOC_BACKEND_API.md` 4 |
| **JPA / EntityGraph** ⭐ | ORM, chống N+1 | `repository/` | `HOC_BACKEND_API.md` 6 |
| **Flyway** | Migration DB | `db/migration/` | `HOC_BACKEND_API.md` 7 |
| **pg_trgm + GIN** ⭐ | Index tìm chuỗi con | `V2__search_indexes.sql` | `HOC_BACKEND_API.md` 8 |
| **Testcontainers** | Integration test | `AbstractIntegrationTest` | `HOC_BACKEND_API.md` 10 |
| **React + TanStack Query** ⭐ | Frontend | `frontend/src/` | `HOC_FRONTEND_REACT.md` |
| **axios interceptor** ⭐ | Tự refresh token | `api/client.ts` | `HOC_FRONTEND_REACT.md` 6 |

---

## 3. Checklist: dự án AI

### ⭐ ReAct và LangGraph

| Câu | Trả lời được chưa |
|---|---|
| ReAct là gì? | ⬜🟨🟩🟦 |
| Vì sao cần agent chứ không phải workflow cứng? | ⬜🟨🟩🟦 |
| Chain / router / plan-execute / multi-agent khác gì, khi nào dùng cái nào? | ⬜🟨🟩🟦 |
| `state` là gì, vì sao `operator.add`? | ⬜🟨🟩🟦 |
| Cạnh điều kiện quyết định đi đâu bằng cách nào? | ⬜🟨🟩🟦 |
| **Đánh đổi:** agent khó đoán, khó gỡ lỗi, đắt hơn | ⬜🟨🟩🟦 |
| **Hỏng:** model không chịu dừng → `MAX_TOOL_CALLS=8`, chạm trần thì **vẫn trả lời** | ⬜🟨🟩🟦 |
| **Đo:** tool-selection accuracy đọc từ lịch sử tin nhắn thật | ⬜🟨🟩🟦 |

*Câu bẫy:* **vì sao là 8?** → Thành thật: chọn theo cảm giác, **chưa đo** đường cong đánh đổi.
Cách đo có trong `HOC_VAN_HANH_THAT.md` 6.3.

### ⭐ RAG và vector store

| Câu | |
|---|---|
| RAG giải quyết vấn đề gì? | ⬜🟨🟩🟦 |
| Vì sao RAG chứ không fine-tune, không nhét cả tài liệu vào prompt? | ⬜🟨🟩🟦 |
| Embedding là gì, vì sao tìm được theo ý nghĩa? | ⬜🟨🟩🟦 |
| Vì sao chunk 1024 / overlap 128? | ⬜🟨🟩🟦 |
| Vì sao Chroma chứ không FAISS / pgvector / Pinecone? | ⬜🟨🟩🟦 |
| **Đánh đổi:** đổi model embedding là phải nạp lại **toàn bộ** kho | ⬜🟨🟩🟦 |
| **Hỏng:** thư mục tồn tại nhưng rỗng → phải kiểm **nội dung**, không chỉ sự tồn tại | ⬜🟨🟩🟦 |
| **Đo:** recall@k — vector 92%/100%, hybrid 83%/100% | ⬜🟨🟩🟦 |
| Vì sao **tắt** hybrid dù đã viết xong? | ⬜🟨🟩🟦 |
| Giới hạn phép đo: **nhãn yếu**, 12 câu, chỉ đủ để so ba cách | ⬜🟨🟩🟦 |

### ⭐ Đánh giá chất lượng

| Câu | |
|---|---|
| Vì sao "chạy thử thấy ổn" không phải bằng chứng? | ⬜🟨🟩🟦 |
| Hai chỉ số là gì, vì sao cần cả hai? | ⬜🟨🟩🟦 |
| Nhờ AI chấm AI thì tin được không — ba lý do? | ⬜🟨🟩🟦 |
| Thí nghiệm chấm 5 lần chứng minh điều gì? | ⬜🟨🟩🟦 |
| Vì sao giả thuyết "không chốt thị trấn" là **sai**? | ⬜🟨🟩🟦 |
| **Đánh đổi:** sửa prompt được 3,5→4,6 nhưng chi phí **+11%** | ⬜🟨🟩🟦 |
| **Hỏng:** cổng "luôn cho qua" tệ hơn không có cổng → 6 test cho `decide_gate` | ⬜🟨🟩🟦 |

### LLM nền tảng

| Câu | |
|---|---|
| Model thực chất làm gì? | ⬜🟨🟩🟦 |
| Vì sao model bịa — giải thích bằng **cơ chế** | ⬜🟨🟩🟦 |
| Hạ temperature có hết bịa không? | ⬜🟨🟩🟦 |
| Tool calling và structured output liên quan gì? | ⬜🟨🟩🟦 |
| Vì sao chọn `gemini-3.1-flash-lite`? | ⬜🟨🟩🟦 |
| **Đo:** 7 model, cái đắt nhất gấp **68 lần** mà điểm **thấp hơn** | ⬜🟨🟩🟦 |

---

## 4. Checklist: dự án SlangWord

### ⭐ JWT và refresh token

| Câu | |
|---|---|
| JWT gồm mấy phần, phần nào ai cũng đọc được? | ⬜🟨🟩🟦 |
| Vì sao JWT chứ không session? | ⬜🟨🟩🟦 |
| **Đánh đổi lớn nhất:** không thu hồi ngay được | ⬜🟨🟩🟦 |
| Xoay vòng refresh token là gì? | ⬜🟨🟩🟦 |
| Phát hiện tái sử dụng hoạt động thế nào, `familyId` để làm gì? | ⬜🟨🟩🟦 |
| Vì sao database chỉ lưu **hash** của token? | ⬜🟨🟩🟦 |
| **Hỏng:** nhiều request song song → refresh trùng → **đăng xuất oan** | ⬜🟨🟩🟦 |
| Frontend chữa bằng cách nào? | ⬜🟨🟩🟦 |
| Vì sao BCrypt chứ không SHA-256? | ⬜🟨🟩🟦 |

*Câu bẫy:* **token để localStorage không sợ XSS à?** → Sợ, và nêu ba lớp bù: CSP, access token
ngắn, phát hiện tái sử dụng.

### ⭐ Database và ORM

| Câu | |
|---|---|
| N+1 là gì, phát hiện bằng cách nào? | ⬜🟨🟩🟦 |
| `@EntityGraph` chữa thế nào, khi nào **không** nên fetch join? | ⬜🟨🟩🟦 |
| Vì sao dùng migration chứ không sửa DB bằng tay? | ⬜🟨🟩🟦 |
| Vì sao **không được sửa** file migration đã chạy? | ⬜🟨🟩🟦 |
| Vì sao `LIKE '%abc%'` không dùng được B-tree? | ⬜🟨🟩🟦 |
| GIN + `pg_trgm` giải quyết thế nào, cái giá là gì? | ⬜🟨🟩🟦 |
| **Đo:** ❌ **chưa chạy `EXPLAIN ANALYZE`** — mới là điều đang *tin* | ⬜🟨🟩🟦 |
| Phân trang offset vs cursor, vì sao phải chặn `size`? | ⬜🟨🟩🟦 |

### REST và test

| Câu | |
|---|---|
| `401` khác `403`? `409` dùng khi nào? | ⬜🟨🟩🟦 |
| RFC 7807 giải quyết gì? | ⬜🟨🟩🟦 |
| Vì sao `service` không được biết về HTTP? | ⬜🟨🟩🟦 |
| Vì sao Testcontainers chứ không H2? | ⬜🟨🟩🟦 |
| Tháp test: unit / integration / E2E — tỉ lệ thế nào và vì sao? | ⬜🟨🟩🟦 |

### ⭐ Frontend

| Câu | |
|---|---|
| Client state vs server state, mỗi loại dùng gì? | ⬜🟨🟩🟦 |
| `queryKey` làm gì? `invalidateQueries` làm gì? | ⬜🟨🟩🟦 |
| Interceptor bắt `401` rồi làm gì — ba chi tiết? | ⬜🟨🟩🟦 |
| `RequireAuth` có phải bảo mật không? | ⬜🟨🟩🟦 |
| TypeScript có kiểm tra dữ liệu **lúc chạy** không? | ⬜🟨🟩🟦 |

---

## 5. Checklist: hạ tầng và vận hành

| Câu | |
|---|---|
| ⭐ CI khác CD chỗ nào? | ⬜🟨🟩🟦 |
| ⭐ Vì sao quét Trivy **trước** khi đẩy image? | ⬜🟨🟩🟦 |
| Vì sao `ignore-unfixed: true`? | ⬜🟨🟩🟦 |
| ⭐ Vì sao deploy bằng tag SHA chứ không `latest`? | ⬜🟨🟩🟦 |
| ⭐ OIDC keyless hơn client secret chỗ nào? | ⬜🟨🟩🟦 |
| Ba secret `AZURE_*` có phải bí mật không? | ⬜🟨🟩🟦 |
| `min-replicas 0` được gì mất gì? | ⬜🟨🟩🟦 |
| Idempotent nghĩa là gì trong workflow deploy? | ⬜🟨🟩🟦 |
| Container vs máy ảo? | ⬜🟨🟩🟦 |
| ⭐ Vì sao p95 chứ không phải trung bình? | ⬜🟨🟩🟦 |
| Vì sao histogram buckets phải tự đặt? | ⬜🟨🟩🟦 |
| ⭐ Gấp 10 lần thì cái gì vỡ trước, vì sao **không phải CPU**? | ⬜🟨🟩🟦 |
| Bộ phận nào hỏng làm **sập cả hệ thống**? | ⬜🟨🟩🟦 |
| Hoá đơn tăng gấp 10 trong đêm — làm gì **trong 5 phút**? | ⬜🟨🟩🟦 |
| ⭐ Bốn lỗ hổng app AI — dự án dính cái nào? | ⬜🟨🟩🟦 |
| Capability URL khác row-level security chỗ nào? | ⬜🟨🟩🟦 |

---

## 6. Mười hai con số phải thuộc

Đây là những con số **đo thật**, có file để chỉ vào. Thuộc lòng — chúng xuất hiện trong hầu
hết câu trả lời.

| # | Con số | Nguồn |
|---|---|---|
| 1 | **100%** tool-selection (32/32 ca) | `evals/results.md` |
| 2 | **4,6/5** answer quality (trước khi sửa prompt trên bộ 8 ca đầu: 3,5) | `evals/results.md` |
| 3 | **p95 = 7,55 giây** (production, Prometheus); load test `/chat` thật cũng ra **7,6 giây** | Prometheus + `loadtest/results.md` |
| 4 | **$0,94 / 1000 câu** (từng lên $1,39 sau lần sửa prompt, sau đó giảm nhờ sửa bug ở `rank_town_candidates`) | `evals/results.md` |
| 5 | **141 test**, offline, ~25 giây | `pytest -q` |
| 6 | **92 chunk**, 3,3 MB, từ 4 trang Wikivoyage | Đếm trực tiếp |
| 7 | Vector recall@1 **92%**, hybrid **83%** | `evals/retrieval_comparison.md` |
| 8 | **7 model** đo; đắt nhất gấp **68 lần** mà điểm thấp hơn | `evals/model_comparison.md` |
| 9 | Image Docker **1,45 GB**, rebuild **~15 giây** | `docker build` |
| 10 | SlangWord: **7.641 từ**, **71+8 test**, coverage **91,2%** | README SlangWord |
| 11 | Throughput hạ tầng **137 req/s**, p95 **39ms**, 0% lỗi (50 user) | `loadtest/results.md` |
| 12 | Injection-refusal **5/5**, 0/5 rò rỉ thật | `evals/injection_results.md` |

---

## 7. Mười câu "chưa đo" phải nhớ

Quan trọng **ngang** mười con số trên. Nhớ để **không bịa** khi bị hỏi bất ngờ.

| # | Chưa đo | Nếu bị hỏi thì nói thêm |
|---|---|---|
| 1 | **`/chat` thật ở tải cao** (đã đo baseline hạ tầng 137 req/s và `/chat` ở quy mô nhỏ 3 user) | "Mỗi request `/chat` tốn tiền thật nên em mới đo ở quy mô nhỏ — tăng dần `-u` trong Locust là bước tiếp theo" |
| 2 | **p99** | "Histogram tính được, nhưng chưa đủ lưu lượng thật để có nghĩa" |
| 3 | **Tỉ lệ lỗi khi tải cao** | "Đếm `agent_requests_total{status="error"}` lúc load test" |
| 4 | **CPU / RAM** | "`docker stats` lúc load test; `py-spy` để soi sâu" |
| 5 | **Số người dùng đồng thời chịu được** | "Tăng dần tới khi p95 vượt ngưỡng" |
| 6 | **`EXPLAIN ANALYZE`** trên SlangWord | "Index GIN là điều em *tin*, chưa phải điều em *đo*" |
| 7 | **Cold start Azure** | "Tài liệu ghi ~15-20 giây, nhưng đó là quan sát vài lần, không phải đo có hệ thống" |
| 8 | **Đường cong `MAX_TOOL_CALLS`** | "Chạy lại eval với 4/6/8 là ra" |
| 9 | **`chunk_size` khác** (512, 2048) | "Có sẵn `eval_retrieval.py` để đo, chỉ chưa chạy" |
| 10 | **Trần connection của Neon** | "Chưa chạm tới nên chưa biết" |

> **Nói "chưa đo" không mất điểm. Bịa số thì mất tất cả** — vì một lời bịa bị lật tẩy làm người
> phỏng vấn nghi ngờ **cả những câu bạn trả lời đúng**.

---

## 8. Lịch tự chấm

| Khi nào | Làm gì |
|---|---|
| **Đọc xong một tài liệu** | Chấm ngay phần tương ứng. Đừng đợi — lúc vừa đọc xong là lúc bạn **tưởng mình hiểu nhất** |
| **Mỗi tuần** | Chọn 5 mục ⭐ ngẫu nhiên, nói thành tiếng, ghi âm rồi nghe lại |
| **Trước phỏng vấn 1 ngày** | Chỉ ôn mục 6 và mục 7 — mười con số và mười câu "chưa đo" |
| **Sau mỗi buổi phỏng vấn** | Ghi lại câu bị hỏi mà mình đuối, thêm vào checklist này |

**Cách luyện hiệu quả nhất: nói thành tiếng và ghi âm.** Đọc thầm luôn cho cảm giác trôi chảy
giả tạo. Nghe lại bản ghi bạn sẽ nghe thấy chỗ mình vòng vo — đó chính là chỗ chưa hiểu.

Khi đã 🟦 hết các mục ⭐, hãy chuyển sang [PHONG_VAN_MO_PHONG.md](PHONG_VAN_MO_PHONG.md) và tự
trả lời trước khi xem đáp án. Chỗ nào bạn đuối trước khi hết đoạn hội thoại — quay lại đây và
hạ mức mục đó xuống.

---

## 9. Liên quan

- [PHONG_VAN_MO_PHONG.md](PHONG_VAN_MO_PHONG.md) — hội thoại phỏng vấn đào sâu
- [HOC_VAN_HANH_THAT.md](HOC_VAN_HANH_THAT.md) — bảng đã đo / chưa đo đầy đủ
- [LO_TRINH_HOC.md](LO_TRINH_HOC.md) — kịch bản nói cho từng dòng CV
- [README.md](README.md) — thứ tự đọc 19 tài liệu
