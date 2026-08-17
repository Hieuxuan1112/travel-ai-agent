# Deploy lên Hugging Face Spaces (0 đồng, không cần thẻ)

Kết quả: một URL công khai dạng `https://<user>-travel-ai-agent.hf.space` — bấm vào là
chạy, dán được vào CV.

**Vì sao chọn Hugging Face:** miễn phí thật, **không cần thẻ tín dụng** nên không thể phát
sinh tiền, và chạy được Docker nên dùng lại đúng `Dockerfile` của repo. Cloud Run trông
chuyên nghiệp hơn nhưng bắt buộc gắn thẻ.

---

## Chuẩn bị (đã xong sẵn trong repo)

| Việc | Trạng thái |
|---|---|
| Dockerfile chạy được, non-root uid 1000 (HF yêu cầu) | ✅ |
| Vector store nướng sẵn trong image → khởi động tức thì, không tốn tiền embedding | ✅ đã kiểm chứng: 92 chunk, log ghi "Loading cached vector store" |
| Rate limit chặn người lạ đốt quota | ✅ mặc định 30 câu/IP/giờ |
| Script sinh metadata cho Space | ✅ `deploy/make_hf_readme.py` |

---

## Bước 1 — Tạo tài khoản và Space

1. Đăng ký tại https://huggingface.co/join (miễn phí, không hỏi thẻ).
2. Vào https://huggingface.co/new-space và điền:

| Ô | Điền |
|---|---|
| Space name | `travel-ai-agent` |
| License | `mit` (hoặc để trống) |
| **Space SDK** | **Docker** → chọn tiếp **Blank** |
| Space hardware | `CPU basic · 2 vCPU · 16 GB` (Free) |
| Visibility | **Public** |

3. Bấm **Create Space**. Space hiện đang trống — bình thường.

## Bước 2 — Nạp API key vào Space

Trong Space vừa tạo: tab **Settings** → mục **Variables and secrets**:

- **New secret**: name `GOOGLE_API_KEY`, value là key Google AI Studio của bạn.
  Phải là **secret**, không phải variable — variable hiện công khai cho mọi người xem.
- **New variable**: name `RATE_LIMIT_PER_HOUR`, value `20`. Đây là chốt an toàn cho quota.

## Bước 3 — Tạo token để đẩy code

https://huggingface.co/settings/tokens → **Create new token** → quyền **Write** → copy lại
(chỉ hiện một lần).

## Bước 4 — Nối repo với Space

Chạy trong `D:\langgraph-agent-lab>`, thay `USERNAME` bằng tên tài khoản Hugging Face:

```bash
git remote add hf https://huggingface.co/spaces/USERNAME/travel-ai-agent
```

## Bước 5 — Đẩy lên

Hugging Face đọc cấu hình Space từ phần YAML ở đầu `README.md`, nhưng để YAML đó trong
README trên GitHub thì GitHub render thành một cái bảng xấu ngay đầu trang. Nên ta để
README trên `main` sạch, và chỉ chèn YAML ở một nhánh riêng dành cho deploy:

```bash
git checkout -B hf-space main
```

```bash
venv\Scripts\python.exe deploy\make_hf_readme.py
```

```bash
git commit -am "chore: add Hugging Face Space metadata"
```

```bash
git push -f hf hf-space:main
```

```bash
git checkout main
```

Khi được hỏi mật khẩu, dán **token** ở bước 3 (không phải mật khẩu tài khoản).

Lệnh cuối đưa bạn về nhánh `main` sạch — **luôn nhớ bước này**, đừng làm việc tiếp trên
nhánh `hf-space`.

## Bước 6 — Chờ build

Mở `https://huggingface.co/spaces/USERNAME/travel-ai-agent`, tab **Logs** để xem tiến
trình. Build lần đầu **5–10 phút** (cài toàn bộ thư viện). Xong thì trạng thái chuyển
**Running** và trang demo hiện ra.

Kiểm tra nhanh:

```
https://USERNAME-travel-ai-agent.hf.space/healthz   → {"status":"ok",...}
https://USERNAME-travel-ai-agent.hf.space/docs      → tài liệu API
https://USERNAME-travel-ai-agent.hf.space/          → trang demo SSE
```

---

## Bước 7 — Đưa URL vào README và CV

Sau khi Space chạy, thêm vào đầu `README.md` (ngay dưới hàng badge):

```markdown
**🔴 Live demo:** https://USERNAME-travel-ai-agent.hf.space
```

và vào CV, sửa dòng dự án:

```latex
| \href{https://USERNAME-travel-ai-agent.hf.space}{live demo} | \href{https://github.com/Hieuxuan1112/travel-ai-agent}{github.com/Hieuxuan1112/travel-ai-agent}
```

Thêm một bullet vào mục dự án:

```latex
\item Deployed as a public Docker service with per-IP rate limiting; the vector store ships inside the image so cold starts serve traffic immediately.
```

---

## Cập nhật Space sau này

Mỗi lần `main` có thay đổi mới muốn đưa lên Space, chạy lại đúng 5 lệnh ở **bước 5**.
Nhánh `hf-space` được tạo lại từ `main` mỗi lần nên không bao giờ có xung đột.

---

## Những điều cần biết

| Điều | Chi tiết |
|---|---|
| **Space ngủ** | Không ai dùng 48 giờ thì Space ngủ; có người vào thì tự thức, lần đầu chờ ~30 giây |
| **Ổ đĩa tạm** | Space restart là mất dữ liệu ghi thêm. Không sao vì vector store nằm sẵn trong image |
| **Không thể mất tiền** | Không gắn thẻ thì không có gì để trừ |
| **Quota Gemini** | Đây mới là thứ có thể cạn. Rate limit 20 câu/IP/giờ để chặn; free tier hết quota thì API báo 429, vẫn không mất tiền |
| **Key có an toàn không** | Có, nếu để ở mục **Secrets**. Nó là biến môi trường trong container, người xem Space không đọc được |
| **Repo công khai** | Code ai cũng xem được — đúng ý đồ, vì đây là portfolio |

## Nếu build lỗi

Xem tab **Logs** trên Space. Hai lỗi hay gặp:

- **Hết RAM khi build** — free tier 16 GB, image này 1,4 GB nên hiếm khi dính.
- **`GOOGLE_API_KEY` chưa đặt** — app khởi động được nhưng gọi model là lỗi. Kiểm tra lại
  bước 2, và nhớ **Restart Space** sau khi thêm secret.
