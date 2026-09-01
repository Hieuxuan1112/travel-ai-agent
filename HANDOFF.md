# Bàn giao — đọc file này trước

Phiên trước làm gì, còn gì dở. Cập nhật 2026-08-30.

## Trạng thái: dự án đã xong và chạy thật

| | |
|---|---|
| Streamlit | https://cornwall-travel-agent.streamlit.app |
| API trên Azure | https://travel-agent-api.nicewave-bb4d94a1.japaneast.azurecontainerapps.io/docs |
| Repo | github.com/Hieuxuan1112/travel-ai-agent |
| Test | 56 passed |

Phiên trước đã thêm: checkpointer PostgreSQL (Neon), CD pipeline (Trivy → GHCR),
deploy Azure Container Apps bằng OIDC keyless. Tất cả đã kiểm chứng chạy thật.

## VIỆC CÒN DỞ — ưu tiên theo thứ tự

### 1. Sửa số liệu trên CV (gấp — user đang apply việc)

`D:\career-ops\documents\cv\resume-master.tex`, bullet của Multi-Tool AI Agent
hiện ghi: `100% tool selection, 4.4/5 quality, 50 offline tests`.

Đối chiếu repo:

| CV ghi | Đo được thật |
|---|---|
| 100% tool selection | ✅ đúng (`evals/results.md`) |
| 4.4/5 quality | ❌ chạy lại 2026-08-30 ra **3.5/5** |
| 50 offline tests | ❌ thật ra là **56** (`pytest -q`) |

**Đề nghị:** bỏ hẳn con số chất lượng (không bắt buộc khoe mọi chỉ số, nhưng
không được ghi số sai), giữ `100% tool selection` và đổi `50` → `56 tests`.
Hỏi user chốt trước khi sửa.

Lưu ý: CV có **hai nguồn đang lệch nhau** — `resume-master.tex` trong repo và một
bản trên Overleaf có title/summary riêng (`AI Engineer (LLM, Multi-Agent, RAG)`).
User build PDF từ Overleaf. Nên gộp về một nguồn.

### 2. Bổ sung MENTOR.md

`docs/MENTOR.md` (1037 dòng, tài liệu "sản phẩm chạy thế nào") có **0 lần** nhắc:
PostgreSQL checkpointer, Trivy, GHCR, Azure, OIDC. Cần thêm ~150 dòng, cùng giọng
văn hiện có (tiếng Việt, mục đánh số, bảng có ví dụ đời thường, mục "trả lời
phỏng vấn" ở cuối).

Tham khảo nội dung đã viết ở `docs/hoc/HOC_CICD_CLOUD.md` và `docs/DEPLOY.md` mục 9-10.

### 3. Điểm judge 3.5/5 — tìm hiểu vì sao thấp

`evals/results.md`. Các case điểm thấp đều là loại **nhiều bước** (gọi search rồi
gọi weather nhiều lần): "surfing town where it is not raining" được 2/5,
"which coastal town should I visit today" được 2/5. Case một bước thì 4-5/5.

Đây là phát hiện thật, đáng đưa vào tài liệu học và đáng nói khi phỏng vấn.

### 4. Bản Streamlit deploy có thể vẫn dùng InMemorySaver

Đã bảo user thêm `DATABASE_URL` vào Streamlit Secrets và reboot app, chưa xác nhận
lại. Cách kiểm: đếm thread trong Neon → hỏi một câu qua app → đếm lại.

## Quy tắc user đã chốt (đừng vi phạm)

- **Không ghi lên CV thứ chưa kiểm chứng được.** Mỗi con số phải chỉ về một file
  trong repo hoặc một lần chạy thật.
- **Kiểm link deploy bằng trình duyệt, không tin HTTP status.** Streamlit Cloud là
  SPA, trả 200 cho cả trang lỗi lẫn app của người khác. Dấu hiệu đáng tin duy nhất
  là dòng "Created by ...". Phiên trước đã dính bẫy này và sửa nhầm 38 file trỏ
  vào app của người lạ.
- Tài liệu viết bằng **tiếng Việt**, giọng giải thích cho người tự học.
- Commit message viết bằng **tiếng Anh**, nhiều đoạn `-m`, giải thích *vì sao*
  chứ không phải *làm gì*.

## Tài liệu học hiện có

`docs/hoc/` — 10 file HOC + 4 demo chạy được. Đọc `docs/hoc/README.md` để biết
thứ tự, `docs/hoc/LO_TRINH_HOC.md` có bảng "mỗi dòng CV cần kiến thức gì".
