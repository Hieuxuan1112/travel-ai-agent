# Deploy — bản đang chạy và các phương án khác

**Bản đang chạy (miễn phí, không cần thẻ):**
https://travel-ai-agent.streamlit.app

Nền tảng: **Streamlit Community Cloud**, chạy trực tiếp `app.py` từ nhánh `main` của repo.

---

## 1. Vì sao chọn Streamlit Community Cloud

Ban đầu tài liệu này hướng dẫn Hugging Face Spaces bản Docker. Khi làm thật thì phát hiện
**Docker Space đã trở thành tính năng trả phí** — trang pricing của Hugging Face liệt kê
*"Host ZeroGPU, Gradio & Docker Spaces"* trong gói PRO ($9/tháng). Vì yêu cầu là không tốn
đồng nào nên phải đổi hướng.

| Nền tảng | Cần thẻ? | Chạy được gì | Kết luận |
|---|---|---|---|
| **Streamlit Community Cloud** ✅ | Không | `app.py` trực tiếp | **Đang dùng.** Không tốn tiền, không phải viết thêm code |
| Hugging Face Spaces (Docker) | Không, nhưng cần **PRO $9/tháng** | Dockerfile | Loại vì mất phí |
| Hugging Face Spaces (Gradio) | Không | app viết bằng Gradio | Được, nhưng phải viết lại giao diện bằng Gradio |
| Google Cloud Run | **Có thẻ** | Dockerfile | Chuyên nghiệp nhất, free tier rộng, nhưng bắt buộc gắn thẻ |
| Render / Railway / Fly.io | Có | Dockerfile | Free tier 512 MB dễ hết RAM với `chromadb`, hoặc đã bỏ free tier |
| Vercel | — | Không hợp | Serverless: giới hạn dung lượng và thời gian chạy ngắn, agent chạy 10 giây thì không hợp |

Hai thứ chuẩn bị từ trước giúp việc deploy trơn tru:

- **Vector store đã commit vào repo** (3,3 MB) → Streamlit clone về là chạy ngay, không phải
  tải lại 4 trang Wikivoyage và không tốn tiền embedding ở mỗi lần khởi động.
- **`app.py` đã có sẵn** → không phải viết lại giao diện cho nền tảng mới.

## 2. Các bước đã làm

1. https://share.streamlit.io → **Sign in with GitHub**
2. **Create app** → repo `Hieuxuan1112/travel-ai-agent`, branch `main`, main file `app.py`
3. **Advanced settings → Secrets**, dán một dòng:
   ```
   GOOGLE_API_KEY = "..."
   ```
   Định dạng là TOML nên giá trị phải nằm trong dấu nháy kép.
4. **Deploy**, chờ 5–10 phút cài thư viện.

## 3. Cập nhật app sau này

Không cần làm gì thủ công: **Streamlit Cloud tự deploy lại mỗi khi bạn push lên `main`**.
Chỉ cần `git push`, đợi 1–2 phút rồi tải lại trang.

Đổi secret hoặc cấu hình thì vào **Manage app** (góc dưới bên phải trang app) → Settings.

## 4. URL rút gọn (đã làm)

URL mặc định có đuôi ngẫu nhiên, dán vào CV trông rất xấu. Đã đổi qua
**Manage app → Settings → General → Custom subdomain** thành:

```
https://travel-ai-agent.streamlit.app
```

**Bẫy đã dính thật:** đổi subdomain làm **URL cũ chết hẳn — trả 404, không redirect**.
README, `docs/MENTOR.md` và **34 file CV** vẫn trỏ vào URL cũ một thời gian dài; ai bấm
vào cũng ra trang lỗi. Lần sau đổi subdomain thì grep sạch URL cũ ngay trong cùng một lần:

```bash
grep -rn "<đuôi-ngẫu-nhiên>" --include=*.md --include=*.tex .
```

Bài học rộng hơn: một link hỏng trên CV còn tệ hơn không có link. Sau mỗi lần đổi
địa chỉ, mở bằng **cửa sổ ẩn danh** để kiểm — chứ đừng tin trình duyệt còn cache.

## 5. Những điều cần biết

| Điều | Chi tiết |
|---|---|
| **App ngủ** | Không ai dùng vài ngày thì app ngủ; người vào sau đó phải bấm nút đánh thức và chờ ~30 giây. Trước khi gửi CV nên vào một lần cho nó thức |
| **Giới hạn RAM** | Khoảng 1 GB. `chromadb` khá nặng nên nếu kho kiến thức phình to thì có thể hết bộ nhớ |
| **Không thể mất tiền** | Không gắn thẻ ở đâu cả |
| **Quota Gemini** | Đây mới là thứ có thể cạn nếu nhiều người dùng. Free tier hết quota thì API báo lỗi, vẫn không mất tiền |
| **Key có an toàn không** | Có. Nằm trong mục Secrets, không lộ trong repo hay trên giao diện |
| **Rate limit** | Phần giới hạn tần suất nằm trong `api.py`, **không áp dụng** cho `app.py`. Xem mục 6 |

## 6. Điểm còn hở: bản Streamlit không có rate limit

Cơ chế chặn lạm dụng đã viết nằm ở `api.py`, mà bản deploy này chạy `app.py`. Nghĩa là
người lạ vào demo có thể hỏi bao nhiêu tuỳ thích và đốt quota Gemini của bạn.

Hiện chấp nhận được vì key ở free tier nên hết quota chỉ bị chặn chứ không mất tiền, và URL
chưa ai biết ngoài bạn. Nhưng nếu gửi CV cho nhiều nơi thì nên thêm giới hạn cho `app.py` —
đếm số câu mỗi phiên bằng `st.session_state` là đủ ở mức demo.

## 7. Nếu muốn deploy cả bản API (FastAPI + SSE)

Streamlit Cloud chỉ chạy được app Streamlit. Muốn có URL cho `api.py` — kèm `/docs`,
`/chat/stream` và `/metrics` — thì cần nền tảng chạy được Docker:

- **Google Cloud Run** (cần thẻ, free tier rộng, scale về 0): `Dockerfile` đã đọc sẵn biến
  `$PORT` của Cloud Run và chạy non-root, deploy được ngay không phải sửa gì.
- **Hugging Face Space bản Docker**: cần PRO $9/tháng.

Chưa làm vì yêu cầu là không tốn đồng nào.

## 8. Lưu hội thoại xuống Postgres

Trước đây lịch sử chat nằm trong `st.session_state` — F5 một cái là mất sạch, và mỗi
lượt hỏi phải tự ghép lại 4 lượt gần nhất để agent hiểu câu nối tiếp.

Bây giờ dùng **LangGraph checkpointer** (`persistence.py`):

| Có `DATABASE_URL` | Không có |
|---|---|
| `PostgresSaver` — hội thoại sống qua F5, qua restart server, qua cả đổi máy | `InMemorySaver` — state trong RAM tiến trình, mất khi restart |

**Không bắt buộc `DATABASE_URL`.** CI không có database, và bắt buộc nó thì người clone
repo về không chạy thử được ngay. Thiếu biến thì tự lui về `InMemorySaver`, không ném lỗi.

### Vì sao `thread_id` nằm trên URL

F5 là Streamlit tạo phiên mới và xoá sạch `session_state`. Nếu `thread_id` chỉ nằm trong
đó thì ghi xuống Postgres cũng vô nghĩa: refresh xong sinh thread mới, màn hình vẫn trắng.
Đẩy nó lên query param (`?thread=<uuid>`) thì refresh mở lại đúng hội thoại cũ, và dán URL
cho người khác họ cũng mở được đúng thread đó.

### Vì sao vẫn phải cắt cửa sổ lịch sử

Checkpointer giữ **toàn bộ** hội thoại. Ném hết vào model mỗi lượt thì 30 lượt chat là vài
chục nghìn token cho *mỗi* câu hỏi. `llm_node` cắt bằng `trim_messages(start_on="human")` —
state dưới database vẫn nguyên, chỉ phần gửi cho model bị giới hạn (`MAX_HISTORY_MESSAGES`,
mặc định 30).

`start_on="human"` không phải chi tiết làm màu: cắt bừa có thể bỏ lại một `ToolMessage` mồ
côi không còn `AIMessage` tool_call đi trước, và Gemini từ chối nguyên request. Ngưỡng 30
lớn hơn số message tối đa một lượt sinh ra (`MAX_TOOL_CALLS=8` → khoảng 17), nên lượt đang
chạy không bao giờ bị đụng tới.

### Cấu hình khi deploy

Lấy chuỗi kết nối miễn phí ở https://neon.com (0,5 GB, 100 giờ compute/tháng, không cần
thẻ, tự ngủ sau 5 phút). Dùng bản **pooled** (host có `-pooler`).

Streamlit Cloud: **Manage app → Settings → Secrets**, thêm một dòng:

```
DATABASE_URL = "postgresql://...-pooler.../neondb?sslmode=require"
```

Pool đặt `min_size=0` để Neon ngủ được (ngủ thì không đốt giờ compute của gói free) và
`check=ConnectionPool.check_connection` để connection chết sau khi Neon ngủ được mở lại,
thay vì để request đầu tiên sau khi ngủ bị lỗi.

**Nút "Clear conversation" không xoá gì dưới database** — nó chỉ mở một thread mới. Hội
thoại cũ vẫn truy lại được nếu còn giữ URL.

## 9. Pipeline CD — đóng gói image

`.github/workflows/cd.yml` chạy sau khi `ci.yml` xanh: build image, quét lỗ hổng, đẩy lên
**GitHub Container Registry** (`ghcr.io`).

### Vì sao ghcr.io chứ không phải Artifact Registry

ghcr.io miễn phí không giới hạn cho image public. Artifact Registry của Google chỉ free
0,5 GB — image này **đo được 1,45 GB** nên vượt ngay từ lần build đầu.

### Vì sao `workflow_run` chứ không bắt thẳng vào `push`

`ci.yml` trả lời "code có đúng không", `cd.yml` trả lời "có artifact nào sẵn sàng deploy
không". Bắt thẳng vào `push` thì một commit hỏng vẫn sinh ra image nằm trên registry.

Cái bẫy của `workflow_run`: nó chạy trong ngữ cảnh nhánh mặc định chứ **không** tự lấy
commit đã kích hoạt CI. Không ghi rõ `ref: head_sha` là có ngày CI xanh ở commit A nhưng
image lại build từ commit B. Và `workflow_run` bắn cả khi CI **đỏ** — nó chỉ báo "CI đã
chạy xong" — nên phải tự lọc bằng `if: ... conclusion == 'success'`.

### Vì sao build trước, đẩy sau

Quét xong mới đẩy. Đẩy trước rồi mới quét thì image hỏng đã nằm sẵn trên registry cho
người khác kéo về.

### Hai bước quét Trivy, hai mục đích khác nhau

| Bước | Mức | Chặn? | Lý do |
|---|---|---|---|
| Báo cáo | HIGH + CRITICAL | Không | Gom vào tab Security để còn theo dõi |
| Chặn | CRITICAL **đã có bản vá** | Có | Chỉ chặn ở cái thật sự sửa được |

Chặn theo HIGH thì CD đỏ vĩnh viễn, vì ảnh `python:3.12-slim` lúc nào cũng còn vài CVE HIGH
chưa ai vá. Một cổng luôn đỏ thì không ai thèm nhìn, còn tệ hơn là không có cổng.
`ignore-unfixed: true` vì CVE chưa có bản vá thì báo cũng không làm gì được.

### Xác thực

Dùng `secrets.GITHUB_TOKEN` — GitHub tự cấp cho mỗi lần chạy, **không phải tạo secret nào**.
Job khai báo quyền tối thiểu: `packages: write` để đẩy image, `security-events: write` để
đẩy kết quả quét.

### Hai tag mỗi lần build

`:latest` cho tiện tay, và `:<sha>` để truy ngược image đang chạy sinh ra từ commit nào.
**Khi deploy thật thì dùng tag SHA**, không dùng `latest` — `latest` đổi dưới chân mình lúc
nào không biết.
