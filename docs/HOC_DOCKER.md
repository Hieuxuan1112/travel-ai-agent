# Học Docker qua chính project này

Ba file: [`Dockerfile`](../Dockerfile), [`.dockerignore`](../.dockerignore),
[`docker-compose.yml`](../docker-compose.yml).

---

## 1. Docker giải quyết vấn đề gì

Câu kinh điển: *"máy tôi chạy được mà"*. Nguyên nhân là máy bạn có Python 3.12, có
`venv`, có đúng phiên bản thư viện; máy người khác thì không.

Docker đóng gói **toàn bộ**: hệ điều hành nền, Python, thư viện, code, câu lệnh khởi
chạy — thành một **image**. Ai có image đó chạy lên đều ra kết quả y hệt.

| Khái niệm | Là gì | Ví dụ đời thường |
|---|---|---|
| **Image** | bản đóng gói tĩnh, chỉ đọc | file cài đặt |
| **Container** | một lần chạy của image | chương trình đang chạy |
| **Dockerfile** | công thức để tạo image | công thức nấu ăn |
| **Volume** | ổ đĩa gắn ngoài, sống lâu hơn container | USB cắm vào |
| **Compose** | chạy nhiều container cùng lúc bằng 1 file | dàn nhạc |

Khác với máy ảo: container **dùng chung nhân hệ điều hành** của máy chủ, nên nhẹ và
bật trong một giây thay vì một phút.

---

## 2. Multi-stage build — vì sao chia 2 tầng

```dockerfile
FROM python:3.12-slim AS builder     # tầng 1: cài thư viện
RUN python -m venv /opt/venv
RUN pip install -r requirements.txt

FROM python:3.12-slim AS runtime     # tầng 2: chỉ lấy kết quả
COPY --from=builder /opt/venv /opt/venv
```

Tầng 1 làm việc bẩn (tải, biên dịch, cache pip). Tầng 2 **chỉ copy đúng thư mục
`/opt/venv`** đã cài xong, bỏ lại toàn bộ rác. Kết quả: image gọn hơn, và quan trọng
hơn là **không mang theo công cụ biên dịch** — càng ít thứ trong image thì càng ít
lỗ hổng bảo mật.

Image cuối của project này là **1.4 GB** — nghe to nhưng phần lớn là `torch`-class
dependencies của `chromadb`/`onnxruntime`, không tránh được nếu vẫn dùng Chroma.

## 3. Thứ tự lệnh trong Dockerfile quyết định tốc độ

```dockerfile
COPY requirements.txt .        # ① copy MỖI file này trước
RUN pip install -r requirements.txt   # ② cài thư viện
COPY . .                       # ③ rồi mới copy code
```

Docker cache theo **layer**: một lệnh không đổi thì nó dùng lại kết quả cũ. Nếu bạn
`COPY . .` ngay từ đầu, mỗi lần sửa một dòng code là **cài lại toàn bộ thư viện**
(4 phút). Tách như trên thì sửa code chỉ rebuild vài giây.

Đo thật ở project này: build lần đầu **3 phút 50**, rebuild sau khi sửa code **~15 giây**.

## 4. `.dockerignore` — quan trọng ngang `.gitignore`

Không có nó, `COPY . .` sẽ nhét cả `venv/` (môi trường Windows, vô dụng trong Linux),
`.git/`, và **cả file `.env` chứa API key** vào image. Ai lấy được image là lấy được key.

## 5. Ba thứ "chuyên nghiệp" trong Dockerfile này

**Chạy bằng user thường, không phải root**
```dockerfile
RUN useradd --create-home --uid 1000 appuser
USER appuser
```
Mặc định container chạy bằng root. Nếu ai đó khai thác được lỗ hổng trong app, họ có
root trong container — bước đệm để thoát ra máy chủ. Mọi nơi deploy nghiêm túc đều yêu
cầu non-root. Kiểm chứng: `docker exec tai-test whoami` → `appuser`.

**HEALTHCHECK**
```dockerfile
HEALTHCHECK --start-period=180s CMD python -c "...urlopen('http://127.0.0.1:8000/healthz')"
```
Docker tự gọi `/healthz` định kỳ. Container "đang chạy" không có nghĩa là "dùng được" —
app có thể treo. `start-period=180s` cho phép khởi động chậm (lần đầu phải tạo embedding)
mà không bị đánh dấu là hỏng.

**`PYTHONUNBUFFERED=1`**
Không có biến này, Python gom output vào buffer — log không hiện kịp và **luồng SSE bị
giữ lại**, mất tính realtime. Đây là lỗi rất hay gặp khi đưa app streaming vào container.

---

## 6. Docker Compose — chạy cả hệ thống bằng một lệnh

```bash
docker compose up --build      # bật tất cả
docker compose ps              # xem trạng thái
docker compose logs -f api     # xem log
docker compose down            # tắt (volume vẫn còn)
docker compose down -v         # tắt và XOÁ LUÔN volume
```

Trong `docker-compose.yml` có 4 khái niệm đáng học:

**`volumes`** — vector store nằm trong volume `chroma_data`. Xoá container thì dữ liệu
vẫn còn, bật lại là chạy ngay, không phải tạo embedding lại (đỡ tiền và đỡ chờ).

**`env_file: .env`** — nạp `GOOGLE_API_KEY` lúc chạy chứ không nướng vào image. Đây là
nguyên tắc: **secret không bao giờ nằm trong image**.

**`depends_on` + `condition: service_healthy`** — `ui` chỉ khởi động sau khi `api` đã
khỏe. Không phải cho đẹp: `api` là thằng dựng vector store, hai container cùng dựng một
lúc sẽ tranh chấp file.

**`healthcheck`** — chính là thứ `depends_on` ở trên dựa vào để biết "khỏe" là khi nào.

---

## 7. Một lỗi thật đã bắt được nhờ chạy Docker

Lần chạy compose đầu tiên: API báo `healthy`, agent trả lời trơn tru, nhưng vector store
trong container có **0 chunk** (máy thật có 92). Agent vẫn "chạy đúng" nhưng tool tìm
kiếm trả về rỗng — **hỏng ngầm, không có lỗi nào hiện ra**.

Nguyên nhân: code cũ kiểm tra

```python
if os.path.isdir(PERSIST_DIR):   # thư mục có tồn tại không?
    ...nạp kho đã có...
```

Khi gắn Docker volume vào đường dẫn đó, **thư mục luôn tồn tại nhưng rỗng** → code
tưởng đã có kho, nạp một kho rỗng. Bản sửa kiểm tra *có dữ liệu thật không*:

```python
if not cached.get(limit=1)["ids"]:
    print("Cached vector store is empty - rebuilding.")
    cached = None
```

Bài học đáng giá hơn cả kiến thức Docker: **"thư mục tồn tại" không đồng nghĩa với "có
dữ liệu"**, và lỗi kiểu này chỉ lộ ra khi chạy thật trong môi trường đích. Có một test
riêng cho ca này: `test_existing_but_empty_store_directory_triggers_a_rebuild`.

---

## 8. Lệnh hay dùng

```bash
docker build -t travel-ai-agent .                    # tạo image
docker run -p 8000:8000 --env-file .env travel-ai-agent
docker ps                                            # container đang chạy
docker logs -f <tên container>                       # xem log
docker exec -it <tên container> sh                   # chui vào trong container
docker images                                        # xem image và dung lượng
docker system prune -a                               # dọn rác (giải phóng nhiều GB)
```

`-p 8000:8000` nghĩa là **cổng máy thật : cổng trong container**. Muốn đổi cổng ngoài
thành 9000 thì `-p 9000:8000`.

---

## 9. Trả lời phỏng vấn

**"Multi-stage build để làm gì?"**
Tách tầng cài đặt khỏi tầng chạy. Image cuối chỉ chứa runtime và thư viện đã cài, không
có pip cache hay công cụ biên dịch → nhỏ hơn, ít bề mặt tấn công hơn.

**"Vì sao copy requirements.txt trước rồi mới copy code?"**
Để tận dụng cache theo layer. Thư viện chỉ cài lại khi `requirements.txt` đổi; sửa code
thì rebuild chỉ mất vài giây thay vì vài phút.

**"Làm sao để secret không lọt vào image?"**
`.dockerignore` loại `.env`, và truyền key lúc chạy bằng `--env-file` / biến môi trường /
secret manager. Không bao giờ `COPY .env` hay `ENV API_KEY=...` trong Dockerfile.

**"Volume khác bind mount chỗ nào?"**
Volume do Docker quản lý, sống độc lập với container, hợp cho dữ liệu (vector store,
database). Bind mount gắn thẳng thư mục máy thật vào container, hợp cho lúc dev để sửa
code là thấy ngay.

**"Vì sao chạy container bằng non-root?"**
Giới hạn thiệt hại nếu app bị khai thác. Root trong container là bước đệm để tấn công
máy chủ.

**"HEALTHCHECK khác gì với việc container đang chạy?"**
Tiến trình còn sống không có nghĩa là app phục vụ được. HEALTHCHECK gọi thật vào endpoint
để xác nhận, và orchestrator dựa vào đó để khởi động lại hoặc chưa cho nhận traffic.
