# Bốn lỗ hổng kinh điển của app AI — và dự án này xử lý thế nào

> Bài này bám **code thật trong repo**: [`api.py`](../../api.py), [`app.py`](../../app.py),
> [`persistence.py`](../../persistence.py). Mỗi mục nói rõ: lỗ hổng là gì, vì sao nó chết
> người, dự án đã chặn thế nào, **và chỗ nào vẫn còn hở**.
>
> Bốn mục này là danh sách hay được nhắc khi nói về app AI bị hack. Điểm chung của cả bốn:
> chúng không phải lỗi *lập trình*, chúng là lỗi **quên nghĩ tới**. Code vẫn chạy đúng, chỉ
> là chạy đúng cho cả kẻ xấu.

**Mục lục**

1. [Vì sao app AI khác app thường](#1-vì-sao-app-ai-khác-app-thường)
2. [Lỗ hổng 1 — Endpoint không có rate limit](#2-lỗ-hổng-1--endpoint-không-có-rate-limit)
3. [Lỗ hổng 2 — Gọi AI thẳng từ frontend](#3-lỗ-hổng-2--gọi-ai-thẳng-từ-frontend)
4. [Lỗ hổng 3 — Không có row-level security](#4-lỗ-hổng-3--không-có-row-level-security)
5. [Lỗ hổng 4 — Không có công tắc ngắt](#5-lỗ-hổng-4--không-có-công-tắc-ngắt)
6. [Bảng tổng kết trạng thái dự án](#6-bảng-tổng-kết-trạng-thái-dự-án)
7. [Tự kiểm tra](#7-tự-kiểm-tra)
8. [Trả lời phỏng vấn](#8-trả-lời-phỏng-vấn)

---

## 1. Vì sao app AI khác app thường

Một API thường bị spam thì hậu quả là **server chậm**. Bạn tăng máy hoặc chặn IP là xong.

Một API có LLM đằng sau thì **mỗi request là tiền thật**, trả cho bên thứ ba, và **không có
trần**. Đây là ba khác biệt khiến bốn lỗ hổng dưới đây nguy hiểm hơn hẳn so với app thường:

| | App thường | App AI |
|---|---|---|
| Chi phí mỗi request | Gần như 0 | **Tiền thật** trả cho OpenAI/Google |
| Trần thiệt hại | Server sập rồi thôi | Hoá đơn chạy tiếp cho tới khi hết hạn mức thẻ |
| Ai chịu | Bạn mất uptime | Bạn **mất tiền** |

Với dự án này, chi phí đo được là **$1,39 cho 1000 câu hỏi**. Nghe rẻ. Nhưng một script gọi
50 request/giây trong một đêm là **4,3 triệu request** — khoảng **$6.000**. Đó là lý do bốn
mục dưới đây không phải "nice to have".

---

## 2. Lỗ hổng 1 — Endpoint không có rate limit

### Vấn đề

Bạn deploy API công khai. API key Gemini của bạn giờ **nằm sau một cái nút mà bất kỳ ai trên
internet cũng bấm được**. Không ai chặn thì một vòng `while true` là hết sạch quota — hoặc
hết tiền nếu bạn đã gắn thẻ.

Điểm chết người: **bạn không biết cho tới khi nhận hoá đơn.**

### Dự án giải quyết thế nào

**Thuật toán: cửa sổ trượt (sliding window).** Với mỗi người gọi, ghi lại **thời điểm** từng
request. Có request mới thì vứt bỏ những lượt đã quá 1 giờ, rồi đếm số còn lại.

```
Giới hạn 3 câu/giờ:

  09:00  09:10  09:30        10:05
    │      │      │            │
    ✓      ✓      ✓            ✓  ← lúc 10:05, lượt 09:00 đã rơi khỏi cửa sổ
                               (còn 09:10, 09:30 → mới 2 lượt → cho qua)
```

```python
# api.py
def enforce_rate_limit(request: Request) -> None:
    key = client_key(request)
    now = time.time()
    hits = _hits[key]

    while hits and now - hits[0] > _RATE_WINDOW_SECONDS:   # bỏ lượt đã cũ
        hits.popleft()

    if len(hits) >= RATE_LIMIT_PER_HOUR:
        metrics.RATE_LIMITED.inc()
        retry_after = int(_RATE_WINDOW_SECONDS - (now - hits[0])) + 1
        raise HTTPException(status_code=429, detail=...,
                            headers={"Retry-After": str(retry_after)})
    hits.append(now)
```

### Bốn quyết định đáng giải thích

**1. Vì sao cửa sổ trượt chứ không phải "đếm rồi reset mỗi giờ"?**

Kiểu reset (fixed window) có lỗ hổng **biên cửa sổ**: giới hạn 30/giờ thì kẻ tấn công gửi 30
request lúc 09:59 và 30 request nữa lúc 10:00 — **60 request trong 2 phút**, vẫn hợp lệ theo
luật. Cửa sổ trượt không có biên nên không có lỗ đó.

**2. Vì sao `deque` chứ không phải `list`?**

Vì thao tác chính là **xoá ở đầu** danh sách, rất nhiều lần. `list.pop(0)` phải dịch cả mảng
— O(n). `deque.popleft()` là O(1).

**3. Vì sao `429` kèm `Retry-After` chứ không phải `403`?**

`429 Too Many Requests` là mã chuẩn cho đúng tình huống này; `403` nghĩa là "bạn không có
quyền", sai nghĩa. `Retry-After` cho client biết chờ bao nhiêu giây — **thư viện HTTP tử tế
sẽ tự đợi đúng khoảng đó** thay vì đập liên tục và làm mọi thứ tệ hơn.

**4. Vì sao `/healthz` và `/metrics` được miễn trừ?**

Nếu chặn cả hai endpoint này, Docker và Prometheus gọi vào sẽ nhận `429`, hệ thống điều phối
tưởng container chết và **khởi động lại một container đang khoẻ**. Có test riêng canh điều
này: `test_healthz_and_metrics_are_never_limited`.

### Nhận dạng người gọi: cái bẫy `X-Forwarded-For`

```python
forwarded = request.headers.get("x-forwarded-for", "")
if forwarded:
    return forwarded.split(",")[0].strip()
return request.client.host if request.client else "unknown"
```

Khi chạy sau proxy (Azure, Cloud Run, nginx), `request.client.host` là IP của **proxy** — tức
mọi người dùng chung một suất, một người xài hết là **cả thế giới bị chặn**. Nên phải đọc
`X-Forwarded-For`.

**Cảnh báo phải nói ra nếu bị hỏi:** header này **do client tự đặt được**, nên nó *không*
chống được tấn công có chủ đích — kẻ tấn công đổi header mỗi request là có suất mới. Nó chỉ
chặn lạm dụng thông thường. Muốn chống thật thì phải xác thực bằng API key, hoặc rate limit
ở tầng hạ tầng (WAF, API gateway) nơi IP không giả được.

### Chỗ từng còn hở — và cách vá

**Bản chạy công khai là `app.py` (Streamlit), không phải `api.py`.** Rate limit ở trên nằm
trong `api.py`, nên cho tới gần đây **cửa sổ thật sự mở ra internet lại không được canh**.

Streamlit không đưa IP client ra một cách ổn định giữa các phiên bản. Thay vì giả vờ chặn
theo IP, `app.py` chặn **hai lớp thành thật**:

```python
GLOBAL_BUDGET_PER_HOUR  = 200   # ngân sách TOÀN CỤC: bảo vệ hoá đơn
SESSION_LIMIT_PER_HOUR  = 20    # hạn mức theo PHIÊN: giữ công bằng
```

| Lớp | Bảo vệ cái gì | Lách được không |
|---|---|---|
| Hạn mức theo phiên | Sự **công bằng** giữa người đang dùng | **Được** — mở tab mới là phiên mới |
| Ngân sách toàn cục | **Hoá đơn API key** | **Không** — mở bao nhiêu tab cũng chung một bộ đếm |

Đây là điểm đáng nói khi phỏng vấn: **biết lớp nào lách được và vẫn giữ nó, vì hai lớp bảo vệ
hai thứ khác nhau.** Lớp phiên không chống được kẻ tấn công, nhưng nó ngăn một người dùng vô
tình chiếm hết ngân sách chung.

### Giới hạn còn lại

Bộ đếm nằm **trong bộ nhớ tiến trình**. Hệ quả: restart là mất bộ đếm, và nếu chạy nhiều bản
sao thì mỗi bản đếm riêng (`max-replicas 2` → thực tế gấp đôi giới hạn). Đúng với quy mô hiện
tại; muốn chính xác khi scale thì chuyển bộ đếm sang Redis — **logic không đổi, chỉ đổi chỗ
lưu**.

---

## 3. Lỗ hổng 2 — Gọi AI thẳng từ frontend

### Vấn đề

Bạn viết JavaScript trong trang web gọi thẳng `generativelanguage.googleapis.com`, và nhét
API key vào đó. Trang chạy ngon.

Nhưng **JavaScript chạy trên máy người dùng**. Mọi thứ trong đó đều đọc được: F12 → tab
Network, hoặc chỉ cần View Source. Minify không giúp gì — key vẫn là một chuỗi nằm đó.

Và **bot quét key công khai chỉ mất vài giây**, không phải vài ngày.

### Vì sao đây là lỗi *kiến trúc*, không phải lỗi bất cẩn

Nguyên tắc: **bí mật chỉ được tồn tại ở nơi bạn kiểm soát được.** Máy người dùng thì bạn
không kiểm soát. Không có cách nào "giấu" key trong frontend cho an toàn — obfuscate, mã hoá,
tách file, tất cả đều vô nghĩa vì cuối cùng trình duyệt vẫn phải có key ở dạng dùng được.

Lời giải duy nhất: **key nằm ở server, client gọi server của bạn, server gọi AI.**

```
SAI:   trình duyệt ──key──▶ Google Gemini
ĐÚNG:  trình duyệt ────────▶ server của bạn ──key──▶ Google Gemini
```

Đổi lại bạn được ba thứ, không chỉ một:

| Lợi ích | Vì sao chỉ có ở server |
|---|---|
| Key không lộ | Client không bao giờ thấy |
| **Kiểm soát được ai dùng** | Rate limit, xác thực, ghi log — mục 2 |
| **Tắt được** | Công tắc ngắt — mục 5 |

### Dự án giải quyết thế nào

Cả hai lối vào đều **chạy phía server**:

- `api.py` — FastAPI. Trang demo ở `/` dùng `EventSource` gọi về **chính `/chat/stream` của
  nó**, không gọi Google.
- `app.py` — Streamlit. Toàn bộ code Python chạy trên server, trình duyệt chỉ nhận HTML.

Key đi vào bằng biến môi trường, và trên Azure là **Container Apps secret** tham chiếu qua
`secretref:` chứ không phải env var trần — giá trị không hiện ra trong `az containerapp show`.

Kiểm chứng bằng lịch sử git, không phải bằng niềm tin:

```bash
git log --all --oneline -- .env        # rỗng: .env chưa bao giờ được commit
git log --all -p -S"AIzaSy" --oneline  # rỗng: không có key nào lọt vào lịch sử
```

**Vì sao phải tra cả lịch sử chứ không chỉ xem file hiện tại:** xoá file ở commit sau **không**
làm key an toàn — nó vẫn nằm trong lịch sử và ai clone repo về cũng đọc được.

> **Nếu lỡ commit key:** revoke key **ngay lập tức**, tạo key mới, rồi mới tính chuyện dọn lịch
> sử. Nhiều người làm ngược — cuống lên xoá lịch sử trước, trong lúc đó key cũ vẫn sống và đã
> bị bot nhặt mất.

### Một điểm còn để mở có chủ ý: CORS

```python
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)
```

`allow_origins=["*"]` cho phép **mọi website** gọi API này từ trình duyệt khách của họ.

Vì API này **không dùng cookie hay session**, `*` không cho phép ai đánh cắp phiên đăng nhập
của người khác — đó mới là mối nguy chính của CORS lỏng. Cái mất thật sự là: một trang khác
có thể nhúng API của bạn và **đốt quota bằng IP của khách họ**.

Với demo công khai thì chấp nhận được, và rate limit + ngân sách đã chặn phần thiệt hại. Sản
phẩm thật thì **liệt kê đúng domain frontend** của mình.

---

## 4. Lỗ hổng 3 — Không có row-level security

### Vấn đề

Backend lưu dữ liệu của mọi người trong cùng một bảng. Code lấy dữ liệu theo một cái id do
**client gửi lên**. Không kiểm tra id đó có thuộc về người đang hỏi hay không.

Kết quả: đổi một con số trên URL là đọc được dữ liệu người khác. Đây là lỗ hổng phổ biến nhất
trong danh sách OWASP, tên gọi **IDOR** (Insecure Direct Object Reference).

### Dự án dính chỗ nào

`app.py` lấy `thread_id` **thẳng từ URL** rồi đưa vào khoá đọc/ghi của checkpointer:

```python
st.session_state.thread_id = st.query_params.get("thread") or str(uuid.uuid4())
...
snapshot = agent.get_state(thread_config)   # nạp thẳng hội thoại của thread đó
```

Không có đăng nhập, không có danh tính người dùng, **không có chỗ nào kiểm tra quyền sở hữu**.
Ai có `thread_id` là đọc được — và viết tiếp được — hội thoại đó.

### Vì sao vẫn chấp nhận được: capability URL

Điểm mấu chốt: `thread_id` là **UUID4 — 122 bit ngẫu nhiên**. Không dò được, không đoán được,
không duyệt tuần tự được.

Đây là một mô hình bảo mật có tên: **capability URL** — *"biết được địa chỉ tức là có quyền"*.
Google Docs "ai có link đều xem được", link reset mật khẩu, link Zoom đều dùng đúng mô hình
này. Nó **hợp lệ**, với ba điều kiện:

| Điều kiện | Dự án này |
|---|---|
| Địa chỉ phải đủ ngẫu nhiên | ✅ UUID4, 122 bit |
| Dữ liệu không quá nhạy cảm | ✅ Câu hỏi du lịch, không có dữ liệu cá nhân |
| Phải **nói rõ** đây là mô hình đang dùng | ✅ Chính là mục này |

Và nó là **tính năng có chủ ý**: dán URL cho người khác thì họ mở được đúng hội thoại đó.

**Nhưng phải nói ra cái giá:** URL rò rỉ theo nhiều đường — lịch sử trình duyệt, ảnh chụp màn
hình, header `Referer`, log của proxy, người ngồi cạnh nhìn màn hình. Capability URL **không
phải** row-level security. Nó là *"chưa ai tìm ra"*, không phải *"không ai được phép"*.

### Cái đã vá: ép `thread_id` phải là UUID

```python
def _valid_thread(raw: str | None) -> str | None:
    if not raw:
        return None
    try:
        return str(uuid.UUID(raw))
    except ValueError:
        return None
```

Không có hàm này thì `?thread=admin`, `?thread=1`, `?thread=test` đều được chấp nhận làm khoá.
Hai hậu quả:

1. **Không gian khoá tụt từ 122 bit ngẫu nhiên xuống thứ đoán được.** Nếu bất kỳ ai từng được
   đưa một thread id ngắn, nó dò ra được ngay.
2. Rác trong database — mỗi chuỗi lạ tạo một thread mới.

Hàm này còn **chuẩn hoá** chữ hoa/thường về một dạng, để cùng một hội thoại không bị tách
thành hai thread.

### Muốn có row-level security thật thì cần gì

Câu trả lời trung thực: **cần danh tính người dùng trước đã.** RLS là quy tắc kiểu *"chỉ trả
về dòng nào có `owner_id` = người đang đăng nhập"* — không có `owner_id`, không có RLS.

Lộ trình đúng khi thêm đăng nhập:

1. Thêm xác thực → mỗi người có `user_id`
2. Thêm cột `owner_id` vào bảng checkpoint
3. Bật **Postgres Row Level Security**: database tự lọc, kể cả khi code quên kiểm tra

Điểm 3 mới là ý nghĩa thật của RLS: **hàng rào đặt ở database, không phải ở code.** Code có
bug thì database vẫn chặn. Đặt hàng rào ở tầng thấp nhất có thể — vì mọi đường đi lên đều
phải qua nó.

---

## 5. Lỗ hổng 4 — Không có công tắc ngắt

### Vấn đề

Rate limit chỉ làm **chậm** kẻ lạm dụng, không dừng được. Khi đang bị lạm dụng thật, hoặc nhà
cung cấp đổi giá, hoặc phát hiện lỗi khiến agent trả lời sai nguy hiểm — bạn cần **tắt ngay**.

Không có công tắc thì cách duy nhất là sửa code → build lại image → chạy CI → deploy. **10-15
phút** trong khi hoá đơn vẫn chạy. Tệ hơn: làm vội lúc hoảng là lúc dễ đẩy thêm bug nhất.

### Dự án giải quyết thế nào

Một biến môi trường, chặn ở **cả hai** lối vào:

```python
AI_ENABLED = os.environ.get("AI_ENABLED", "1").strip().lower() not in {"0", "false", "no"}


def require_ai_enabled() -> None:
    if not AI_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="The AI feature is temporarily disabled by the operator. "
                   "The rest of the service is unaffected.",
            headers={"Retry-After": "3600"},
        )
```

Gắn vào endpoint bằng đúng cơ chế `Depends` mà rate limit đang dùng:

```python
@app.get("/chat/stream", tags=["agent"],
         dependencies=[Depends(require_ai_enabled), Depends(enforce_rate_limit)])
```

Tắt trên Azure là **một lệnh, không đụng tới code**:

```bash
az containerapp update -n travel-agent-api -g rg-travel-agent --set-env-vars AI_ENABLED=0
```

Container Apps tạo một **revision mới** — khoảng 1 phút, không build image, không phát hành
bản cập nhật ứng dụng. Bật lại thì đổi về `1`.

### Bốn quyết định đáng giải thích

**1. Vì sao `503` chứ không phải `500` hay `403`?**

`503 Service Unavailable` nghĩa là *"tạm thời không phục vụ"* — đúng ý. `500` nghĩa là hỏng
ngoài ý muốn, sẽ làm hệ thống giám sát báo động nhầm. `403` nghĩa là "bạn không có quyền",
cũng sai. Kèm `Retry-After` để client biết đây là tạm thời.

**2. Vì sao `/healthz` phải vẫn xanh khi AI bị tắt?**

Đây là chi tiết tinh tế nhất mục này. Tắt AI là quyết định **có chủ ý**, không phải container
chết. Nếu `/healthz` đỏ theo, Container Apps tưởng container hỏng và **khởi động lại liên tục**
— đúng lúc bạn đang cố tắt nó đi. Có test canh riêng:
`test_healthz_stays_green_when_ai_is_disabled`.

**3. Vì sao chấp nhận nhiều cách viết (`0`, `false`, `no`, `FALSE`)?**

Người bấm công tắc này thường đang bấm **lúc 3 giờ sáng, trong lúc hoảng**. Bắt họ nhớ đúng
chính tả là thiết kế tồi. Đây là nguyên tắc **human factors**: đường thoát hiểm phải dễ đi
nhất, không phải khó nhất.

**4. Vì sao phải viết test cho cái công tắc?**

Vì **một cái cổng hỏng theo kiểu "luôn cho qua" còn tệ hơn không có cổng**: bạn tưởng đã tắt,
yên tâm đi ngủ, trong khi hoá đơn vẫn chạy. Repo có 5 test riêng cho công tắc này.

### Chỗ còn hở, phải nói ra

Công tắc hiện tại là **toàn cục** — tắt là tắt hết. Không tắt được **theo từng người dùng**,
vì hệ thống **không có danh tính người dùng** (xem mục 4). Muốn có "chặn riêng người này" thì
lại quay về bài toán đăng nhập.

Đây là ví dụ tốt cho thấy các lỗ hổng **liên quan tới nhau**: không có danh tính thì vừa
không có RLS, vừa không có công tắc theo người dùng, vừa phải rate limit theo IP (thứ giả
được) thay vì theo tài khoản.

---

## 6. Bảng tổng kết trạng thái dự án

| # | Lỗ hổng | Trạng thái | Cơ chế |
|---|---|:-:|---|
| 1 | Không rate limit | ✅ | Cửa sổ trượt theo IP (`api.py`) + ngân sách toàn cục & hạn mức phiên (`app.py`) |
| 2 | Gọi AI từ frontend | ✅ | Cả hai lối vào chạy server-side; key chưa từng vào git; Container Apps secret |
| 3 | Không có RLS | ⚠️ **Một phần** | Capability URL (UUID4 122 bit) + ép định dạng UUID. **RLS thật cần đăng nhập** |
| 4 | Không có công tắc ngắt | ✅ | `AI_ENABLED=0` → 503, đổi bằng một lệnh `az`, `/healthz` vẫn xanh |

Điểm còn mở có chủ ý: **CORS `*`** (demo công khai) và **`/metrics` mở** (lộ số liệu vận hành
như token, chi phí — không lộ dữ liệu người dùng).

> **Cách nói trong phỏng vấn:** đừng nói *"dự án của em bảo mật"*. Hãy nói *"em rà bốn lỗ hổng
> này, ba cái đã chặn và có test, cái thứ ba em dùng capability URL vì chưa có đăng nhập — em
> biết đó không phải RLS thật và đây là việc cần làm nếu mở rộng."* Câu sau đáng tin gấp nhiều
> lần câu trước.

---

## 7. Tự kiểm tra

Trả lời trước rồi mới mở đáp án.

**1.** Vì sao rate limit dùng cửa sổ trượt chứ không phải bộ đếm reset mỗi giờ?

<details><summary>Đáp án</summary>

Bộ đếm reset có lỗ hổng **biên cửa sổ**: giới hạn 30/giờ thì gửi 30 request lúc 09:59 và 30
lúc 10:00 là được 60 request trong 2 phút mà vẫn "hợp lệ". Cửa sổ trượt không có biên nên
không có lỗ đó.
</details>

**2.** Vì sao không thể giấu API key an toàn trong frontend, kể cả khi mã hoá nó?

<details><summary>Đáp án</summary>

Vì cuối cùng trình duyệt vẫn phải có key ở **dạng dùng được** để gọi API. Mã hoá thì key giải
mã cũng phải nằm trong đó. Mọi thứ chạy trên máy người dùng đều đọc được. Lời giải duy nhất là
key không bao giờ rời server.
</details>

**3.** `X-Forwarded-For` có chống được tấn công có chủ đích không?

<details><summary>Đáp án</summary>

Không. Header đó **client tự đặt được**, đổi mỗi request là có suất mới. Nó chỉ chặn lạm dụng
thông thường. Nhưng vẫn **phải** đọc nó, vì không đọc thì sau proxy mọi người dùng chung một
IP và một người xài hết là cả thế giới bị chặn. Chống thật thì cần xác thực, hoặc rate limit
ở tầng hạ tầng.
</details>

**4.** Capability URL là gì, và nó khác row-level security chỗ nào?

<details><summary>Đáp án</summary>

Capability URL = *"biết địa chỉ tức là có quyền"*, dựa vào việc địa chỉ đủ ngẫu nhiên để không
dò ra (UUID4, 122 bit). RLS = *"database chỉ trả về dòng thuộc về người đang đăng nhập"*.

Khác biệt: capability URL là **"chưa ai tìm ra"**, RLS là **"không ai được phép"**. URL rò rỉ
qua lịch sử trình duyệt, ảnh chụp màn hình, header Referer. RLS cần danh tính người dùng nên
phải có đăng nhập trước.
</details>

**5.** Vì sao `/healthz` phải vẫn trả 200 khi công tắc AI đã tắt?

<details><summary>Đáp án</summary>

Vì tắt AI là quyết định có chủ ý, không phải container chết. Nếu `/healthz` đỏ theo, hệ thống
điều phối tưởng container hỏng và khởi động lại liên tục — đúng lúc bạn đang cố tắt nó đi.
</details>

**6.** Hạn mức theo phiên trong `app.py` mở tab mới là lách được. Vậy giữ nó làm gì?

<details><summary>Đáp án</summary>

Vì hai lớp bảo vệ **hai thứ khác nhau**. Ngân sách toàn cục bảo vệ **hoá đơn** — không lách
được. Hạn mức phiên bảo vệ **sự công bằng** giữa những người đang dùng cùng lúc, ngăn một
người vô tình chiếm hết ngân sách chung. Biết lớp nào lách được mà vẫn giữ có chủ đích thì
khác hẳn với việc không biết.
</details>

**7.** Vì sao công tắc ngắt lại cần có test riêng?

<details><summary>Đáp án</summary>

Vì một cái cổng hỏng theo kiểu **"luôn cho qua"** còn tệ hơn không có cổng: bạn tưởng đã tắt,
yên tâm đi ngủ, trong khi hoá đơn vẫn chạy. Cổng nào cũng phải được chứng minh là **thật sự
chặn**.
</details>

---

## 8. Trả lời phỏng vấn

1. *App AI khác app thường ở rủi ro nào?* → Mỗi request là **tiền thật** trả cho bên thứ ba và
   **không có trần**. App thường bị spam thì mất uptime; app AI thì mất tiền, và chạy tiếp cho
   tới khi hết hạn mức thẻ.

2. *Bạn chặn lạm dụng thế nào?* → Cửa sổ trượt theo IP ở `api.py` (`deque`, O(1) khi bỏ lượt
   cũ), trả `429` + `Retry-After`. Bản Streamlit công khai thì chặn bằng **ngân sách toàn cục**
   vì Streamlit không đưa IP ra ổn định — và tôi chọn cách chặn thành thật thay vì giả vờ chặn
   theo IP.

3. *Vì sao không gọi LLM thẳng từ trình duyệt?* → Key sẽ lộ, và không có cách nào giấu được vì
   trình duyệt phải có key ở dạng dùng được. Ngoài việc giữ key, đi qua server còn cho tôi
   **kiểm soát ai dùng** và **tắt được**.

4. *Dữ liệu người dùng có bị lẫn không?* → Hội thoại khoá theo `thread_id` là UUID4. Đây là
   **capability URL**, không phải RLS — tôi nói rõ vì hệ thống chưa có đăng nhập. Tôi có ép
   định dạng UUID để không ai đặt được khoá đoán được. RLS thật cần `owner_id` và policy ở
   tầng Postgres.

5. *Đang bị lạm dụng thì bạn làm gì trong 1 phút tới?* → Đặt `AI_ENABLED=0` bằng một lệnh
   `az containerapp update`. Endpoint AI trả `503`, `/healthz` vẫn xanh nên nền tảng không
   khởi động lại nhầm. Không build image, không phát hành bản mới.

6. *Chỗ nào trong hệ thống của bạn còn hở?* → CORS đang `*` và `/metrics` mở — cả hai là lựa
   chọn có chủ ý cho demo, và tôi biết cái giá. Chỗ hở thật là **không có danh tính người
   dùng**: nó kéo theo không có RLS, không tắt được theo từng người, và phải rate limit theo IP
   là thứ giả được.

---

## 9. Liên quan

- [../MENTOR.md](../MENTOR.md) mục 19 — rate limit, giải thích đầy đủ hơn
- [../MENTOR.md](../MENTOR.md) mục 21 — checkpointer và `thread_id`
- [HOC_CICD_CLOUD.md](HOC_CICD_CLOUD.md) mục 5 — OIDC keyless: không có mật khẩu dài hạn nào
  để mà lộ
- [HOC_GIT_GITHUB.md](HOC_GIT_GITHUB.md) mục 11 — lỡ commit secret thì làm gì
- [HOC_PROMPT_ENGINEERING.md](HOC_PROMPT_ENGINEERING.md) — prompt injection, lỗ hổng thứ năm
  mà danh sách này không nhắc tới
