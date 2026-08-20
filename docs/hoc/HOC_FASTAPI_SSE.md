# Học FastAPI + SSE từ số 0 (qua chính project này)

Tài liệu này dạy hai thứ: **FastAPI** (biến code Python thành dịch vụ web) và
**SSE** (đẩy dữ liệu về cho người dùng ngay khi có, không bắt họ chờ). Code thật
nằm ở [`api.py`](../../api.py), test ở [`tests/test_api.py`](../../tests/test_api.py).

---

## Phần 1 — Tại sao cần API?

Hiện tại bạn có 2 cách chạy agent:

| Cách | Ai dùng được | Vấn đề |
|---|---|---|
| `main_02_02.py` (CLI) | chỉ bạn, trên máy bạn, trong terminal | không ai khác gọi được |
| `app.py` (Streamlit) | người vào web | **giao diện và bộ não dính liền nhau** — muốn làm app điện thoại, hay để hệ thống khác gọi agent, thì chịu |

API tách đôi: **bộ não** (agent) thành một dịch vụ chạy độc lập, ai gọi cũng được — web, app điện thoại, một service khác, hay `curl` trong terminal.

```
TRƯỚC:  [Streamlit: giao diện + agent dính nhau]

SAU:    [Streamlit]  ─┐
        [App mobile] ─┼──HTTP──> [API: agent]  ← chỉ có một bộ não, ai cũng gọi được
        [Service khác]─┘
```

Đây là lý do mọi công ty đều bọc model sau một API. Với vai trò AI Engineer, đây là công việc hằng ngày.

---

## Phần 2 — HTTP trong 5 phút (nền tảng bắt buộc)

Web chỉ có 2 vai: **client** hỏi, **server** trả lời. Một lần hỏi–đáp gọi là request–response.

**Request** gồm 4 phần:

```
POST /chat HTTP/1.1          ← method + đường dẫn (path)
Content-Type: application/json   ← header: thông tin phụ về gói tin
                                 ← dòng trống
{"question": "weather in St Ives?"}   ← body: dữ liệu gửi lên
```

- **Method**: `GET` = xin dữ liệu (không thay đổi gì trên server), `POST` = gửi dữ liệu lên. Còn `PUT` (sửa), `DELETE` (xoá).
- **Path**: `/chat`, `/healthz` — tên "cửa" mà bạn gõ vào.
- **Query string**: phần sau dấu `?` trên URL, ví dụ `/chat/stream?q=hello`. Dùng với GET.
- **Body**: dữ liệu gửi kèm, thường là JSON. Chỉ POST/PUT mới có.

**Response** trả về một **status code**, nhớ 5 nhóm này là đủ:

| Mã | Nghĩa | Khi nào gặp trong project |
|---|---|---|
| `200` | OK | mọi thứ ổn |
| `422` | dữ liệu bạn gửi lên sai | gửi câu hỏi 2 ký tự → FastAPI tự chặn |
| `404` | không có cửa đó | gõ sai path |
| `500` | server lỗi | code Python nổ |
| `503` | server quá tải / chưa sẵn sàng | LLM hết quota |

---

## Phần 3 — FastAPI là gì

Là thư viện Python để viết server HTTP. Ba lý do nó phổ biến nhất hiện nay trong mảng AI:

### 3.1 Viết một endpoint = viết một hàm Python

```python
@app.get("/healthz")
def healthz():
    return {"status": "ok"}
```

`@app.get("/healthz")` là **decorator** — nó nói "khi có ai gọi GET /healthz, chạy hàm này". Return một `dict`, FastAPI tự đổi thành JSON. Hết.

### 3.2 Khai báo kiểu = được validate + tài liệu miễn phí

Đây là điểm mạnh lớn nhất của FastAPI. Trong `api.py`:

```python
class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)

@app.post("/chat")
def chat(request: ChatRequest) -> ChatResponse:
    ...
```

Chỉ vì bạn khai báo `request: ChatRequest`, FastAPI **tự động**:
1. Đọc JSON từ body, đổi thành object Python.
2. Kiểm tra `question` có phải string không, dài 3–500 ký tự không. Sai → trả `422` kèm mô tả lỗi rõ ràng, hàm của bạn **không hề chạy**.
3. Sinh tài liệu API tương tác tại `/docs`.

Ta đã kiểm chứng bằng test thật:

```
curl -X POST /chat -d '{"question":"hi"}'   →   HTTP 422
```

`BaseModel` là của thư viện **pydantic** — bạn đã dùng nó gián tiếp mà không biết, vì LangChain dùng pydantic để mô tả tham số tool cho LLM. Cùng một cơ chế.

### 3.3 Tài liệu tự sinh

Mở http://127.0.0.1:8000/docs khi server chạy — có sẵn trang bấm thử được từng endpoint. Không viết dòng nào. File `openapi.json` sinh ra là chuẩn công nghiệp, dùng để sinh code client cho mọi ngôn ngữ.

### So sánh nhanh với Flask / Django

| | FastAPI | Flask | Django |
|---|---|---|---|
| Validate dữ liệu | tự động qua type hint | tự viết tay | qua form/serializer |
| Tài liệu API | tự sinh | phải cài thêm | phải cài thêm |
| Bất đồng bộ (async) | có sẵn từ đầu | chắp vá | có nhưng nặng |
| Hợp với | API, microservice, AI | app nhỏ | web full-stack có sẵn admin/ORM |

---

## Phần 4 — Đọc `api.py` theo thứ tự

### 4.1 `lifespan` — chạy một lần lúc bật/tắt server

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    lab.get_travel_info_vectorstore()   # chạy lúc KHỞI ĐỘNG
    yield
    print("API shutting down.")         # chạy lúc TẮT
```

Vì sao cần: vector store mất vài giây để nạp. Không nạp sẵn thì **người dùng đầu tiên** phải gánh thời gian chờ đó. Nguyên tắc chung: việc nặng làm một lần lúc khởi động, đừng làm trong request.

### 4.2 CORS — vì sao cần

Trình duyệt có luật bảo mật: JavaScript ở `domain-A.com` **không được** gọi API ở `domain-B.com`, trừ khi B nói "tôi cho phép A". Lời cho phép đó là header CORS. Không có nó, frontend của bạn sẽ dính lỗi *"blocked by CORS policy"* — lỗi kinh điển ai làm web cũng gặp.

Demo thì `allow_origins=["*"]` (cho tất cả). Production thì chỉ liệt kê đúng domain frontend.

### 4.3 `/chat` — kiểu cổ điển, và vì sao nó chưa đủ

```python
result = lab.travel_info_agent.invoke(...)   # chờ agent làm XONG HẾT
return ChatResponse(...)
```

Đo thật: **4.63 giây** cho câu đơn giản, **~10 giây** cho câu phải gọi 3 tool. Suốt thời gian đó người dùng nhìn màn hình trắng, không biết còn sống hay treo. Đó chính là bài toán SSE giải.

---

## Phần 5 — SSE (Server-Sent Events)

### 5.1 Bốn cách đẩy dữ liệu về client

| Cách | Cơ chế | Nhược |
|---|---|---|
| **Polling** | client hỏi lại mỗi 1s "xong chưa?" | tốn request, vẫn trễ tới 1s |
| **Long-polling** | server giữ request đến khi có dữ liệu mới trả | phức tạp, mỗi mẩu tin một kết nối |
| **WebSocket** | ống 2 chiều luôn mở | mạnh nhưng nặng: giao thức riêng, khó qua proxy/firewall, phải tự lo reconnect |
| **SSE** ✅ | server đẩy 1 chiều trên HTTP thường | chỉ 1 chiều server→client (đúng nhu cầu của ta) |

**Chọn SSE khi**: dữ liệu chỉ chảy một chiều từ server về (stream câu trả lời LLM, thanh tiến trình, thông báo). **Chọn WebSocket khi**: cần 2 chiều liên tục (chat nhiều người, game, ứng dụng vẽ chung).

ChatGPT, Claude và hầu hết sản phẩm LLM đều stream câu trả lời bằng SSE. Đây là lựa chọn mặc định đúng cho AI.

### 5.2 Định dạng trên đường dây — đơn giản đến bất ngờ

SSE không phải giao thức mới. Nó chỉ là một response HTTP **không bao giờ kết thúc ngay**, với `Content-Type: text/event-stream`, và nội dung là text theo quy ước:

```
event: tool_call
data: {"name": "weather_forecast", "args": {"town": "St Ives"}}
                                     ← DÒNG TRỐNG kết thúc một sự kiện
event: done
data: {"tool_calls": 3, "elapsed_seconds": 9.75}

```

Ba quy tắc: dòng `event:` đặt tên sự kiện (không bắt buộc), dòng `data:` chứa nội dung, **dòng trống** báo hết một sự kiện. Chấm hết — đó là toàn bộ giao thức SSE.

### 5.3 Generator — cách Python đẩy dữ liệu dần

Hàm bình thường `return` một lần rồi chết. Hàm có `yield` là **generator**: mỗi lần `yield` là nhả ra một mẩu rồi *tạm dừng*, giữ nguyên trạng thái, chờ được gọi tiếp.

```python
def agent_events(question):
    yield sse("start", {...})           # nhả ngay lập tức
    for update in agent.stream(...):    # agent chạy dần
        yield sse("tool_call", {...})   # nhả từng bước
    yield sse("done", {...})
```

`StreamingResponse(agent_events(q), media_type="text/event-stream")` nối generator đó thẳng vào socket: **cứ `yield` một cái là client nhận được ngay**, không đợi hàm chạy xong.

Mắt xích cuối là LangGraph: `agent.stream(..., stream_mode="updates")` cũng là generator — cứ một node trong đồ thị chạy xong thì nó nhả kết quả node đó. Ba generator nối nhau: LangGraph → `agent_events` → HTTP socket.

Bằng chứng đo thật (dấu thời gian lúc mỗi sự kiện về tới máy):

```
[04:50] event: start
[04:51] event: tool_call     search_travel_info
[04:52] event: tool_result
[04:53] event: tool_call     weather_forecast St Ives
[04:55] event: tool_result
[04:56] event: tool_call     weather_forecast Falmouth
[04:59] event: tool_result
[05:00] event: answer
[05:01] event: done          9.75s
```

Trải đều 10 giây chứ không dồn một cục ở giây thứ 10 — đó là bằng chứng streaming hoạt động.

### 5.4 Client trong trình duyệt: `EventSource`

```javascript
const es = new EventSource('/chat/stream?q=' + q);
es.addEventListener('tool_call', e => console.log(JSON.parse(e.data)));
es.addEventListener('done', e => es.close());   // ← BẮT BUỘC
```

**Cạm bẫy phải nhớ** (câu hỏi phỏng vấn rất hay gặp): `EventSource` **tự động kết nối lại** khi server đóng stream — nó tưởng mạng rớt. Nếu không gọi `es.close()` khi nhận `done`, trình duyệt sẽ hỏi lại câu đó **mãi mãi**, và mỗi vòng là một lần gọi LLM tính tiền. Đây là lỗi rất dễ mắc và rất tốn.

Hệ quả thứ hai: `EventSource` **chỉ gọi được GET**, không gửi được body JSON — đó là lý do `/chat/stream` dùng GET với query param `?q=`. Muốn POST kèm body thì phải bỏ `EventSource`, dùng `fetch()` + đọc `ReadableStream` thủ công (nhiều sản phẩm thật làm vậy vì câu hỏi có thể rất dài, mà URL bị giới hạn ~2000 ký tự).

### 5.5 Hai header chống "nghẽn"

```python
headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
```

Proxy (nginx, CDN) mặc định hay **gom dữ liệu vào buffer** rồi mới gửi đi một thể cho hiệu quả — làm vậy là giết chết tính realtime: người dùng vẫn nhận tất cả một cục ở cuối. Hai header này bảo chúng đừng làm thế. Triệu chứng điển hình: chạy ở máy thì stream mượt, deploy lên server thì "đơ rồi hiện hết một lúc" — 90% là do buffering.

### 5.6 Lỗi phải xử lý trong stream

Điểm tinh tế: khi đã bắt đầu stream, server **đã gửi status 200 rồi**, không thể đổi thành 500 được nữa. Nên lỗi giữa chừng phải báo bằng một *sự kiện*:

```python
except Exception as exc:
    yield sse("error", {"message": str(exc)})
    return
```

Có hẳn một test cho tình huống này (`test_stream_reports_errors_instead_of_crashing`).

---

## Phần 6 — Tự tay làm (làm hết là có kinh nghiệm thật)

Chạy server:

```bash
D:\langgraph-agent-lab\venv\Scripts\python.exe D:\langgraph-agent-lab\api.py
```

1. Mở http://127.0.0.1:8000/docs → bấm **Try it out** ở `/chat`, gõ câu hỏi, xem response.
2. Mở http://127.0.0.1:8000/ → bấm **Ask**, nhìn các sự kiện hiện dần. Mở **DevTools (F12) → Network → chọn request `chat/stream` → tab EventStream** để thấy từng sự kiện về theo thời gian.
3. Chạy `curl -N "http://127.0.0.1:8000/chat/stream?q=weather in Da Nang"` — thấy đúng text thô của giao thức.
4. Gửi câu hỏi 2 ký tự → nhận 422. Đọc kỹ nội dung lỗi pydantic trả về.
5. **Bài tập sửa code**: thêm endpoint `GET /tools` trả về danh sách tool và mô tả của chúng (gợi ý: `lab.TOOLS`, mỗi tool có `.name` và `.description`).
6. **Bài tập khó hơn**: thêm giới hạn 10 câu/IP mỗi giờ (một `dict` trong bộ nhớ là đủ), trả `429 Too Many Requests` khi vượt. Đây chính là thứ cần trước khi deploy công khai.
7. **Bài tập nâng cao**: chuyển `/chat/stream` sang POST + `fetch()`/`ReadableStream` ở client, để câu hỏi dài không bị giới hạn độ dài URL.

---

## Phần 7 — Trả lời phỏng vấn

**"SSE khác WebSocket chỗ nào, khi nào dùng cái nào?"**
SSE một chiều server→client, chạy trên HTTP thường nên qua được mọi proxy, có sẵn cơ chế tự kết nối lại. WebSocket hai chiều, giao thức riêng, mạnh hơn nhưng nặng và phải tự lo reconnect. Stream câu trả lời LLM chỉ cần một chiều → SSE là lựa chọn đúng, và đó cũng là cách ChatGPT/Claude làm.

**"FastAPI validate dữ liệu kiểu gì?"**
Bằng pydantic qua type hint. Khai báo `question: str = Field(min_length=3)` là FastAPI tự parse, tự kiểm, tự trả 422 kèm chi tiết lỗi, và tự sinh OpenAPI. Không viết code kiểm tra tay.

**"Vì sao stream endpoint của bạn là GET mà không phải POST?"**
Vì `EventSource` của trình duyệt chỉ hỗ trợ GET. Đánh đổi là câu hỏi bị giới hạn bởi độ dài URL; nếu cần dài hơn thì bỏ `EventSource` và dùng `fetch` + `ReadableStream`.

**"Xử lý lỗi giữa chừng khi đang stream thế nào?"**
Không dùng status code được nữa vì 200 đã gửi đi rồi. Phải phát một sự kiện `error` trong luồng rồi đóng tử tế, và client phải lắng nghe sự kiện đó. Tôi có test riêng cho ca này.

**"Deploy lên thì stream bị đơ, nghi gì đầu tiên?"**
Buffering ở proxy/CDN. Kiểm tra header `X-Accel-Buffering: no` và `Cache-Control: no-cache`, và tắt buffer ở tầng nginx/ingress.

**"Test một API có gọi LLM như thế nào?"**
Không gọi LLM thật. Thay agent bằng object giả trả về kịch bản message dựng sẵn, rồi test contract của API: đúng thứ tự sự kiện, đúng schema, đúng mã lỗi. Test chạy trong 0.1 giây, không tốn tiền, chạy được trên CI không cần API key.

---

## Phần 8 — Từ điển thuật ngữ

| Từ | Nghĩa |
|---|---|
| **Endpoint** | một "cửa" của API: method + path, ví dụ `POST /chat` |
| **ASGI** | chuẩn giao tiếp giữa server Python và web server, bản bất đồng bộ của WSGI |
| **uvicorn** | chương trình thực sự lắng nghe cổng mạng và chạy app FastAPI |
| **pydantic** | thư viện khai báo & kiểm tra kiểu dữ liệu bằng class Python |
| **OpenAPI** | chuẩn mô tả API dạng JSON; `/docs` chỉ là giao diện đọc file đó |
| **CORS** | luật trình duyệt về việc gọi API khác domain |
| **Generator** | hàm dùng `yield`, nhả dữ liệu dần thay vì trả một lần |
| **SSE** | giao thức server đẩy sự kiện text một chiều qua HTTP |
| **Middleware** | lớp bọc ngoài mọi request (log, CORS, auth, đo metric) |
| **Lifespan** | code chạy lúc server bật và lúc tắt |
