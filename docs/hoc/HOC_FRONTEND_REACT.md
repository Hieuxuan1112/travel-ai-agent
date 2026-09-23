# Frontend React — học qua chính SlangWord

> Bám **code thật** trong [`D:\SlangWord\frontend`](https://github.com/Hieuxuan1112/SlangWord):
> React 19 + TypeScript + Vite + TanStack Query + Tailwind. Mọi đoạn code copy nguyên từ repo.
>
> Bài này không dạy lại cú pháp JSX hay `useState` — bạn học CNTT thì tra được. Nó dạy **những
> quyết định** mà chỉ khi tự dựng một SPA có đăng nhập mới gặp: giữ token ở đâu, refresh token
> tự động thế nào, và vì sao phần lớn `useState` trong app thật là sai.

**Mục lục**

1. [SPA khác trang web truyền thống ở đâu](#1-spa-khác-trang-web-truyền-thống-ở-đâu)
2. [Cấu trúc thư mục — chia theo vai trò](#2-cấu-trúc-thư-mục--chia-theo-vai-trò)
3. [Hai loại state, và cái sai phổ biến nhất](#3-hai-loại-state-và-cái-sai-phổ-biến-nhất)
4. [TanStack Query — cache và làm mới](#4-tanstack-query--cache-và-làm-mới)
5. [Giữ token ở đâu: đánh đổi thật](#5-giữ-token-ở-đâu-đánh-đổi-thật)
6. [Tự làm mới token — và cái bẫy chạy song song](#6-tự-làm-mới-token--và-cái-bẫy-chạy-song-song)
7. [Chặn route cần đăng nhập](#7-chặn-route-cần-đăng-nhập)
8. [TypeScript ở ranh giới API](#8-typescript-ở-ranh-giới-api)
9. [Test frontend: test cái gì](#9-test-frontend-test-cái-gì)
10. [Tự kiểm tra](#10-tự-kiểm-tra)
11. [Trả lời phỏng vấn](#11-trả-lời-phỏng-vấn)

---

## 1. SPA khác trang web truyền thống ở đâu

| | Trang truyền thống (server render) | SPA |
|---|---|---|
| Đổi trang | Server trả **HTML mới**, trình duyệt tải lại | JavaScript vẽ lại, **không tải lại trang** |
| Server trả gì | HTML | **JSON** |
| Trạng thái đăng nhập | Cookie + session ở server | Token do **client giữ** |
| Lần tải đầu | Nhanh | Chậm hơn (phải tải bundle JS) |

Hệ quả quan trọng nhất, và là gốc của mục 5-6: **server không còn nhớ bạn là ai**. Trang truyền
thống có session ở server; SPA thì client tự giữ token và tự đính vào mỗi request. Toàn bộ độ
phức tạp về xác thực ở frontend sinh ra từ đúng chỗ này.

Kiến trúc SlangWord:

```
Trình duyệt (React SPA)
      │ HTTP
nginx :80  ── phục vụ file tĩnh, và proxy /api ──▶ Spring Boot :8081 ──▶ PostgreSQL
```

**Vì sao có nginx ở giữa:** file tĩnh (JS, CSS) nên do web server phục vụ chứ không phải
ứng dụng Java. Và cho `/api` đi cùng một origin thì **không dính CORS** — trình duyệt coi đây
là cùng một nơi.

---

## 2. Cấu trúc thư mục — chia theo vai trò

```
src/
  api/         gọi HTTP + kiểu dữ liệu   (client.ts, auth.ts, quiz.ts...)
  auth/        context đăng nhập, chặn route
  components/  mảnh giao diện dùng lại được  (WordCard, Pagination...)
  pages/       một màn hình = một route     (SearchPage, QuizPage...)
```

Quy tắc: **chỉ `api/` được biết đến axios và URL.** Component không bao giờ tự gọi HTTP.

Vì sao đáng: đổi đường dẫn API, đổi thư viện HTTP, thêm header — sửa **một chỗ**. Nếu mỗi
component tự `fetch` thì thay đổi nào cũng phải đi lùng khắp dự án.

> Cùng một nguyên tắc với backend ở mục 1 của [HOC_BACKEND_API.md](HOC_BACKEND_API.md):
> **tầng nghiệp vụ không được biết về giao thức.** Ở đây là component không biết về HTTP.

---

## 3. Hai loại state, và cái sai phổ biến nhất

Người mới học React đưa **mọi thứ** vào `useState`. Nhưng có hai loại state khác hẳn nhau:

| | **Client state** | **Server state** |
|---|---|---|
| Ví dụ | Ô input đang gõ, tab đang mở, modal đóng/mở | Danh sách từ, lịch sử tìm kiếm, thống kê quiz |
| Nguồn sự thật | **Ở trong trình duyệt** | **Ở database**, bạn chỉ giữ một bản sao |
| Có thể cũ đi không? | Không | **Có** — người khác vừa sửa dữ liệu đó |
| Công cụ đúng | `useState` | **TanStack Query** |

Đưa server state vào `useState` là sai lầm phổ biến nhất, vì bạn phải tự viết tay tất cả:

```tsx
// Cach nhieu nguoi viet - va thieu rat nhieu thu
const [data, setData] = useState(null)
const [loading, setLoading] = useState(true)
const [error, setError] = useState(null)
useEffect(() => {
  fetch('/api/words').then(...)   // con: cache? huy request cu? thu lai? dedupe?
}, [])
```

Đoạn này thiếu: cache, huỷ request khi component unmount, tránh gọi trùng khi hai component
cùng cần, làm mới sau khi sửa dữ liệu, thử lại khi lỗi mạng. **Mỗi thứ đó là một bug chờ sẵn.**

---

## 4. TanStack Query — cache và làm mới

```tsx
// HistoryPage.tsx
const history = useQuery({ queryKey: ['history', page], queryFn: () => getHistory(page) })
const stats   = useQuery({ queryKey: ['quiz-stats'],    queryFn: getQuizStats })
```

**`queryKey` là chìa khoá của cả thư viện.** Nó vừa là **khoá cache** vừa là **danh tính** của
dữ liệu:

- Hai component cùng `queryKey` → chỉ **một** request, cả hai dùng chung kết quả
- `queryKey` đổi (`['history', 2]`) → tự động lấy dữ liệu trang 2
- Dữ liệu đã có trong cache → hiện **ngay lập tức**, rồi âm thầm kiểm tra bản mới

### Sửa dữ liệu xong thì làm mới thế nào

```tsx
const clear = useMutation({
  mutationFn: clearHistory,
  onSuccess: () => queryClient.invalidateQueries({ queryKey: ['history'] }),
})
```

`useMutation` cho thao tác **thay đổi dữ liệu**. `invalidateQueries` nói: *"dữ liệu mang khoá
`history` giờ đã cũ, lấy lại đi"* — mọi component đang hiện dữ liệu đó tự cập nhật.

**Vì sao đây là cách đúng:** bạn không phải đi tìm và `setState` cho từng component. Bạn chỉ
tuyên bố *dữ liệu nào đã cũ*, thư viện lo phần còn lại. Đây là khác biệt giữa **mô tả** và
**ra lệnh** — và là lý do code ít bug hơn hẳn.

| Tự viết `useState` + `useEffect` | TanStack Query |
|---|---|
| Tự quản `loading` / `error` từng chỗ | Có sẵn `isPending`, `isError` |
| Hai component cùng cần → hai request | Gộp thành một |
| Sửa dữ liệu → tự đi cập nhật từng nơi | `invalidateQueries` một dòng |
| Không có cache | Hiện ngay từ cache, làm mới nền |

---

## 5. Giữ token ở đâu: đánh đổi thật

Câu hỏi phỏng vấn frontend hay gặp, và **không có đáp án hoàn hảo** — chỉ có đánh đổi.

| Nơi giữ | Chống XSS | Chống CSRF | Ghi chú |
|---|:-:|:-:|---|
| `localStorage` | ❌ | ✅ | JS đọc được → dính XSS là mất token |
| Cookie `httpOnly` | ✅ | ❌ | JS **không** đọc được, nhưng trình duyệt tự gửi kèm → cần chống CSRF |
| Chỉ trong bộ nhớ JS | ✅ hơn | ✅ | **Mất khi F5** — phải đăng nhập lại liên tục |

SlangWord dùng `localStorage`:

```ts
export const REFRESH_KEY = 'slangword.refresh'
localStorage.setItem(REFRESH_KEY, session.refreshToken)
```

**Nói thẳng cái giá:** nếu app dính **XSS** (kẻ tấn công chèn được JS vào trang), token bị đọc
mất. Đó là lý do dự án bật **CSP** (Content-Security-Policy) — chặn script lạ chạy, tức là
chặn ngay ở gốc của XSS.

**Cách phòng thủ thật sự là nhiều lớp:**

1. CSP chặn script lạ → XSS khó xảy ra
2. Access token **sống rất ngắn** → lộ cũng nhanh hết hạn
3. Refresh token **xoay vòng + phát hiện tái sử dụng** → dùng trộm là cả phiên bị huỷ
   (xem [HOC_BACKEND_API.md](HOC_BACKEND_API.md) mục 4)

> Cách trả lời phỏng vấn tốt: *"Em dùng localStorage và biết nó không chống được XSS. Bù lại
> bằng CSP, access token ngắn hạn, và refresh token có phát hiện tái sử dụng. Nếu yêu cầu bảo
> mật cao hơn thì chuyển sang cookie httpOnly và thêm chống CSRF."* — nêu được đánh đổi **và**
> đường nâng cấp.

---

## 6. Tự làm mới token — và cái bẫy chạy song song

Access token cố ý sống ngắn, nên `401` là chuyện **bình thường**, không phải sự cố. Client
phải tự đổi token mới rồi **chạy lại request cũ**, để người dùng không thấy gì.

```ts
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (!axios.isAxiosError(error) || error.response?.status !== 401 || !error.config) {
      return Promise.reject(error)
    }
    const request = error.config as typeof error.config & { _retried?: boolean }
    // Only ever retry once: if the replay also 401s, the session is genuinely over.
    if (request._retried || request.url?.includes('/auth/')) {
      clearSession(); onSessionEnded?.(); return Promise.reject(error)
    }
    request._retried = true
    ...
  },
)
```

**Interceptor** là móc chạy quanh mọi request/response — chỗ đúng để đặt logic áp dụng cho
*mọi* lời gọi API, thay vì lặp lại ở từng chỗ.

Ba chi tiết đáng học:

**1. `_retried` — chỉ thử lại đúng một lần.** Không có cờ này thì `401` → refresh → vẫn `401`
→ refresh → **vòng lặp vô tận**.

**2. Bỏ qua chính `/auth/`.** Nếu request refresh bị `401` mà cũng đem đi refresh thì lại vòng
lặp. Dùng `axios` trần cho lời gọi refresh, không dùng `api` — để interceptor không nhìn thấy
nó.

**3. Gộp các lần refresh chạy song song — chi tiết hay nhất của cả file.**

```ts
let refreshInFlight: Promise<string> | null = null
...
refreshInFlight = refreshInFlight ?? refreshAccessToken().finally(() => {
  refreshInFlight = null
})
const token = await refreshInFlight
```

Vì sao cần, và đây là chỗ **frontend và backend gặp nhau**:

```
Một trang bắn 3 request cùng lúc → cả 3 nhận 401 → cả 3 định refresh
  → cả 3 gửi CÙNG một refresh token
  → server xoay vòng: cái đầu tiên thành công, token bị đánh dấu ĐÃ DÙNG
  → 2 cái sau đưa ra token đã dùng → server coi là TÁI SỬ DỤNG
  → huỷ cả họ token → NGƯỜI DÙNG BỊ ĐĂNG XUẤT
```

Người dùng bị đá ra **chính vì họ mở một trang tải nhiều dữ liệu**. Lỗi này chỉ xuất hiện khi
có nhiều request đồng thời — trên máy dev với một request thì không bao giờ thấy.

Chữa bằng cách chia sẻ **một promise duy nhất**: request đầu tiên tạo ra nó, hai request kia
`await` cùng cái đó thay vì tự gửi refresh riêng.

> **Bài học tổng quát, đáng nói trong phỏng vấn:** *một cơ chế bảo mật ở backend có thể ép ra
> một yêu cầu thiết kế ở frontend.* Không biết server xoay vòng token thì không bao giờ nghĩ
> ra phải gộp refresh. Đây là ví dụ rõ nhất cho việc **hiểu cả hai đầu** thì mới làm đúng.

---

## 7. Chặn route cần đăng nhập

```
auth/
  AuthContext.ts     kieu du lieu cua context
  AuthProvider.tsx   giu phien, cung cap login/logout
  RequireAuth.tsx    boc route can dang nhap
  useAuth.ts         hook doc context
```

**Context** để tránh "prop drilling" — truyền thông tin đăng nhập xuống 5 tầng component.
`RequireAuth` bọc các route riêng tư và đá về trang đăng nhập nếu chưa có phiên.

**Điều bắt buộc phải hiểu:** đây **chỉ là trải nghiệm người dùng, không phải bảo mật.** Ai
cũng sửa được JavaScript trong trình duyệt để bỏ qua `RequireAuth`. Thứ thật sự bảo vệ dữ liệu
là **server kiểm token** ở mỗi request.

> Quy tắc: **frontend kiểm tra để cho đẹp, backend kiểm tra để cho thật.** Người phỏng vấn hỏi
> *"nếu người dùng sửa JS bỏ qua chỗ chặn thì sao?"* — câu trả lời đúng là *"họ vẫn không lấy
> được gì, vì server không cấp dữ liệu nếu không có token hợp lệ."*

---

## 8. TypeScript ở ranh giới API

Giá trị lớn nhất của TypeScript trong dự án này nằm ở **ranh giới giữa frontend và backend** —
nơi dữ liệu từ ngoài vào.

```ts
const { data } = await axios.post<AuthSession>(...)
```

Khai kiểu ở đây thì mọi chỗ dùng `data` sau đó đều được kiểm tra. Backend đổi tên một trường →
frontend **báo lỗi lúc biên dịch**, chứ không phải `undefined` lúc chạy trên máy người dùng.

**Nhưng phải biết giới hạn:** TypeScript chỉ tồn tại lúc biên dịch. Nó **không kiểm tra dữ
liệu thật lúc chạy**. `axios.post<AuthSession>` là bạn **hứa** với trình biên dịch rằng server
trả về đúng hình dạng đó — nếu server trả khác, TypeScript không phát hiện được.

Muốn chắc thì kiểm ở runtime (Zod, io-ts). Với dự án mà cùng một người viết cả hai đầu và có
OpenAPI sinh sẵn thì kiểu tĩnh là đủ — nhưng phải **biết** đó là một đánh đổi có ý thức.

---

## 9. Test frontend: test cái gì

SlangWord có 8 test frontend (Vitest + React Testing Library), ví dụ `QuizCard.test.tsx` và
`RequireAuth.test.tsx`.

Triết lý của React Testing Library: **test như người dùng nhìn thấy**, không test chi tiết bên
trong.

| Đừng test | Hãy test |
|---|---|
| `useState` có giá trị gì | Bấm nút xong **màn hình hiện gì** |
| Component gọi hàm nào bên trong | Trả lời đúng thì **hiện chữ "Correct"** |
| Tên class CSS | Chưa đăng nhập thì **bị đá về trang login** |

Vì sao: test dựa vào chi tiết bên trong sẽ **vỡ khi refactor** dù hành vi không đổi — và một
bộ test hay báo động giả thì người ta sẽ ngừng tin nó. Test theo hành vi thì đổi cách cài đặt
thoải mái, miễn người dùng thấy như cũ.

> Cùng tinh thần với backend: `service` được test qua **kết quả nghiệp vụ**, không test qua
> việc nó gọi repository mấy lần.

---

## 10. Tự kiểm tra

**1.** Client state khác server state chỗ nào, và mỗi loại dùng công cụ gì?

<details><summary>Đáp án</summary>

Client state (ô input, tab đang mở) có nguồn sự thật **trong trình duyệt** → `useState`. Server
state (danh sách từ, lịch sử) có nguồn sự thật **ở database**, bạn chỉ giữ bản sao và bản sao
đó **có thể cũ đi** → TanStack Query. Nhét server state vào `useState` là sai lầm phổ biến
nhất vì bạn phải tự viết cache, dedupe, huỷ request, làm mới.
</details>

**2.** `queryKey` dùng để làm gì?

<details><summary>Đáp án</summary>

Vừa là **khoá cache** vừa là **danh tính** của dữ liệu. Hai component cùng key → một request
dùng chung. Key đổi → tự lấy dữ liệu mới. `invalidateQueries` theo key → mọi nơi đang hiện dữ
liệu đó tự cập nhật.
</details>

**3.** Giữ token trong `localStorage` có an toàn không?

<details><summary>Đáp án</summary>

Không tuyệt đối — JS đọc được nên dính **XSS** là mất token. Đổi lại nó không dính CSRF và đơn
giản. Bù bằng nhiều lớp: CSP chặn script lạ, access token sống ngắn, refresh token xoay vòng
có phát hiện tái sử dụng. Cần bảo mật cao hơn thì dùng cookie `httpOnly` + chống CSRF.
</details>

**4.** Vì sao phải gộp các lần refresh token chạy song song?

<details><summary>Đáp án</summary>

Một trang bắn nhiều request cùng lúc, tất cả nhận `401`, tất cả gửi **cùng một** refresh token.
Server xoay vòng nên cái đầu thành công và đánh dấu token đã dùng; các cái sau bị coi là **tái
sử dụng** → huỷ cả họ → **người dùng bị đăng xuất chỉ vì mở một trang tải nhiều dữ liệu**.
Chia sẻ một promise duy nhất thì chỉ có một lần refresh.
</details>

**5.** `RequireAuth` chặn route — vậy có phải cơ chế bảo mật không?

<details><summary>Đáp án</summary>

**Không.** Nó chỉ là trải nghiệm người dùng. Ai cũng sửa được JS trong trình duyệt để bỏ qua.
Thứ bảo vệ dữ liệu thật là **server kiểm token ở mỗi request**. Frontend kiểm tra cho đẹp,
backend kiểm tra cho thật.
</details>

**6.** TypeScript có bảo vệ được khi server trả sai hình dạng dữ liệu không?

<details><summary>Đáp án</summary>

Không. TypeScript chỉ tồn tại **lúc biên dịch**. `axios.post<AuthSession>` là lời **hứa** với
trình biên dịch, không phải phép kiểm tra lúc chạy. Muốn chắc thì validate runtime bằng Zod.
</details>

---

## 11. Trả lời phỏng vấn

1. *SPA khác trang server-render thế nào?* → Server trả **JSON** thay vì HTML, JS vẽ lại
   trang. Hệ quả lớn nhất: **server không nhớ bạn là ai**, client phải tự giữ token — toàn bộ
   độ phức tạp xác thực ở frontend sinh ra từ đó.

2. *Vì sao dùng TanStack Query mà không phải `useState` + `useEffect`?* → Vì đây là **server
   state**, không phải client state: nó có thể cũ đi. Tự viết thì phải tự lo cache, dedupe,
   huỷ request, làm mới sau khi sửa — mỗi thứ là một bug chờ sẵn.

3. *Bạn giữ token ở đâu, vì sao?* → `localStorage`, và em biết nó không chống XSS. Bù bằng
   CSP, access token ngắn hạn, và refresh token xoay vòng có phát hiện tái sử dụng. Yêu cầu
   cao hơn thì chuyển sang cookie `httpOnly` kèm chống CSRF.

4. *Token hết hạn giữa lúc dùng thì sao?* → Interceptor bắt `401`, đổi token mới rồi **chạy
   lại request cũ** nên người dùng không thấy gì. Chỉ thử lại **một lần**, và lời gọi refresh
   dùng axios trần để không tự kích hoạt interceptor.

5. *Kể một bug khó mà bạn phải hiểu cả frontend lẫn backend mới sửa được.* → Nhiều request
   song song cùng nhận `401` thì cùng gửi một refresh token; server xoay vòng nên các request
   sau bị coi là tái sử dụng và **huỷ cả phiên** — người dùng bị đăng xuất vì mở trang nặng.
   Chữa bằng cách chia sẻ một promise refresh duy nhất. Không biết server xoay vòng token thì
   không nghĩ ra được.

6. *Frontend chặn route đã đủ bảo mật chưa?* → Chưa, và không bao giờ đủ. Đó là UX. Bảo mật
   nằm ở server kiểm token mỗi request.

---

## 12. Liên quan

- [HOC_BACKEND_API.md](HOC_BACKEND_API.md) — đầu kia của cùng dự án; mục 4 giải thích cơ chế
  xoay vòng token mà mục 6 ở đây phải thích ứng theo
- [HOC_BAO_MAT_AI_APP.md](HOC_BAO_MAT_AI_APP.md) — vì sao không bao giờ để API key ở frontend
- [HOC_DSA_OOP.md](HOC_DSA_OOP.md) — SOLID, nền của cách chia thư mục ở mục 2
