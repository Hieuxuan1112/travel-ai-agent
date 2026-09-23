# Backend API — học qua chính SlangWord

> Bài này bám **code thật** trong [`D:\SlangWord`](https://github.com/Hieuxuan1112/SlangWord):
> Spring Boot 3.5 + PostgreSQL 16 + React 19. Mọi đoạn code đều copy nguyên từ repo đó.
>
> Vì sao tách riêng khỏi các tài liệu khác: chín tài liệu còn lại đều xoay quanh
> `travel-ai-agent` (Python, FastAPI, agent). Nhưng CV của bạn có **hai** dự án, và dòng
> thứ hai — REST API có xác thực, database quan hệ, frontend SPA — **chưa có tài liệu nào
> phủ**. Phỏng vấn backend hỏi vào đúng chỗ đó.

**Mục lục**

1. [Kiến trúc phân tầng — vì sao không viết hết vào controller](#1-kiến-trúc-phân-tầng--vì-sao-không-viết-hết-vào-controller)
2. [Thiết kế REST — mã trạng thái nói gì](#2-thiết-kế-rest--mã-trạng-thái-nói-gì)
3. [Xác thực: JWT và câu hỏi "vì sao không dùng session"](#3-xác-thực-jwt-và-câu-hỏi-vì-sao-không-dùng-session)
4. [Refresh token xoay vòng và phát hiện tái sử dụng](#4-refresh-token-xoay-vòng-và-phát-hiện-tái-sử-dụng)
5. [Mật khẩu: vì sao BCrypt chứ không phải SHA-256](#5-mật-khẩu-vì-sao-bcrypt-chứ-không-phải-sha-256)
6. [ORM và bẫy N+1](#6-orm-và-bẫy-n1)
7. [Migration — vì sao không sửa database bằng tay](#7-migration--vì-sao-không-sửa-database-bằng-tay)
8. [Index: câu chuyện `LIKE '%abc%'`](#8-index-câu-chuyện-like-abc)
9. [Phân trang — và vì sao phải chặn `size`](#9-phân-trang--và-vì-sao-phải-chặn-size)
10. [Tháp test và Testcontainers](#10-tháp-test-và-testcontainers)
11. [Tự kiểm tra](#11-tự-kiểm-tra)
12. [Trả lời phỏng vấn](#12-trả-lời-phỏng-vấn)

---

## 1. Kiến trúc phân tầng — vì sao không viết hết vào controller

```
web/          controller, chuyển đổi DTO, @RestControllerAdvice
service/      quy tắc nghiệp vụ   ← unit test bằng Mockito, không cần Spring
repository/   Spring Data JPA
domain/       entity JPA
security/     JWT filter, user details
config/       bean và @ConfigurationProperties
```

Quy tắc: **mỗi tầng chỉ phụ thuộc tầng ngay dưới nó.**

Người mới hay viết hết vào controller vì nó chạy được. Cái giá xuất hiện sau:

| Viết hết vào controller | Tách tầng |
|---|---|
| Muốn test quy tắc nghiệp vụ phải dựng cả HTTP | Test `service` bằng Mockito, **mili giây**, không cần Spring |
| Thêm giao diện mới (CLI, message queue) là chép lại logic | Gọi lại đúng `service` |
| Đổi database là đụng vào code nghiệp vụ | Chỉ đổi `repository` |

Điểm mấu chốt để nói trong phỏng vấn: **`service` không được biết gì về HTTP.** Nó không
nhận `HttpServletRequest`, không trả `ResponseEntity`. Nhờ vậy nó là code Java thuần, test
được mà không cần dựng server — và đó là lý do 31 unit test của repo này chạy trong vài giây.

> **Liên hệ với dự án AI:** `travel-ai-agent` cũng theo đúng nguyên tắc này — `api.py` không
> chứa logic agent, nó chỉ gọi `main_02_02.py`. Nhờ vậy CLI, Streamlit, API và MCP dùng chung
> một agent. Khác ngôn ngữ, cùng một tư duy.

---

## 2. Thiết kế REST — mã trạng thái nói gì

Mã trạng thái HTTP không phải trang trí. Nó là **phần giao diện mà máy đọc được**: client tự
động quyết định thử lại hay bỏ cuộc dựa vào con số đó.

| Mã | Nghĩa | SlangWord dùng khi nào |
|---|---|---|
| `200 OK` | Thành công | Tìm từ, lấy lịch sử |
| `201 Created` | Đã tạo tài nguyên mới | Thêm từ mới |
| `400 Bad Request` | Client gửi sai định dạng | Thiếu trường bắt buộc |
| `401 Unauthorized` | **Chưa biết bạn là ai** | Không có token, hoặc token hết hạn |
| `403 Forbidden` | Biết bạn là ai, **nhưng không cho** | User thường gọi API của admin |
| `404 Not Found` | Không có tài nguyên đó | Từ không tồn tại |
| `409 Conflict` | **Xung đột trạng thái** | Thêm từ đã tồn tại |
| `429 Too Many Requests` | Vượt giới hạn tần suất | Rate limit |

**401 và 403 hay bị dùng lẫn**, và đây là câu hỏi phỏng vấn quen thuộc. Cách nhớ:
`401` = *"bạn là ai?"* (authentication), `403` = *"tôi biết bạn là ai rồi, và không"*
(authorization). Trả nhầm `403` cho token hết hạn thì client không biết đường đi làm mới
token.

### `409 Conflict` — ví dụ đáng nói nhất

Bản Swing cũ: thêm từ trùng thì hiện hộp thoại hỏi ghi đè hay không. Bản API không có hộp
thoại — nhưng vẫn phải giữ **ý nghĩa** đó:

```
POST /api/words              → 409 Conflict   "từ này đã có"
POST /api/words?overwrite=true → 200 OK       "tôi biết, cứ ghi đè"
```

Đây là cách chuyển một quyết định của con người thành **hợp đồng API**: server không tự
đoán ý, nó **từ chối và bắt client nói rõ ý định**. Nguyên tắc chung — *khi có mơ hồ, đừng
đoán; hãy bắt bên gọi khẳng định*.

### RFC 7807 — lỗi cũng phải có cấu trúc

Trả lỗi bằng chuỗi tự do (`"Something went wrong"`) thì client chỉ có thể hiện nguyên văn
cho người dùng, không xử lý được gì. RFC 7807 quy định một khuôn JSON chuẩn cho lỗi:

```json
{ "type": "about:blank", "title": "Conflict",
  "status": 409, "detail": "Word 'lol' already exists" }
```

Spring có sẵn `ProblemDetail` cho khuôn này. Gom việc dịch exception → `ProblemDetail` vào
**một chỗ** bằng `@RestControllerAdvice`, thay vì mỗi controller tự bắt lỗi một kiểu:

```java
@RestControllerAdvice
class ApiExceptionHandler {
    @ExceptionHandler(NotFoundException.class)
    ProblemDetail handle(NotFoundException e) { ... }
}
```

Lợi ích thật: **mọi endpoint trả lỗi cùng một hình dạng**, kể cả endpoint viết sau này —
người viết không phải nhớ quy ước.

---

## 3. Xác thực: JWT và câu hỏi "vì sao không dùng session"

### Hai cách nhớ ai đang đăng nhập

| | Session (cách truyền thống) | JWT (cách này) |
|---|---|---|
| Server lưu gì | **Một bảng session**, mỗi người một dòng | **Không lưu gì** |
| Client cầm gì | Một id vô nghĩa trong cookie | Một chuỗi **tự chứa thông tin** |
| Kiểm tra thế nào | Tra database mỗi request | **Kiểm chữ ký**, không tra gì |
| Thu hồi ngay | Dễ — xoá dòng đó | **Khó** — token đã phát thì còn hiệu lực tới khi hết hạn |
| Scale nhiều server | Phải chia sẻ kho session (Redis) | Server nào cũng kiểm được |

**JWT là gì:** ba phần nối bằng dấu chấm — `header.payload.signature`. Hai phần đầu chỉ là
JSON mã hoá Base64, **ai cũng đọc được**. Phần thứ ba là chữ ký HMAC bằng khoá bí mật của
server.

```java
// JwtService.java
this.key = Keys.hmacShaKeyFor(properties.secret().getBytes(StandardCharsets.UTF_8));
...
    .subject(username)
    .claim("role", role)
    .expiration(Date.from(now.plusSeconds(expirationSeconds)))
```

> **Hiểu nhầm chết người phải tránh:** JWT **không mã hoá**, nó chỉ **ký**. Ai cầm token cũng
> đọc được payload — dán vào jwt.io là thấy hết. Chữ ký chỉ đảm bảo *không ai sửa được* nội
> dung, chứ không giấu nội dung. **Đừng bao giờ để dữ liệu nhạy cảm trong payload.**

### Cái giá của JWT: không thu hồi được

Vì server không lưu gì, nó không có cách nào biết token nào "đã bị cấm". Đuổi một người ra
khỏi hệ thống thì token của họ **vẫn dùng được tới lúc hết hạn**.

Cách xử lý chuẩn, và cũng là cách repo này làm: **access token sống rất ngắn** (vài phút),
kèm một **refresh token sống lâu** có thể thu hồi được. Đó là mục tiếp theo.

---

## 4. Refresh token xoay vòng và phát hiện tái sử dụng

Đây là phần **đáng nói nhất** của dự án SlangWord khi phỏng vấn. Ít bạn fresher làm tới đây.

### Vấn đề

Access token ngắn hạn thì người dùng phải đăng nhập lại liên tục — trải nghiệm tệ. Nên có
refresh token sống lâu: hết hạn access token thì đưa refresh token ra đổi lấy cái mới.

Nhưng refresh token sống lâu mà **bị đánh cắp** thì kẻ trộm dùng được rất lâu. Và server
**không có cách nào biết** nó bị đánh cắp.

### Lời giải: xoay vòng + phát hiện tái sử dụng

Hai ý tưởng ghép lại:

1. **Xoay vòng (rotation):** mỗi lần dùng refresh token là nó **bị đánh dấu đã dùng** và
   server phát ra một cái mới. Một token chỉ dùng được **đúng một lần**.
2. **Phát hiện tái sử dụng (reuse detection):** nếu một token *đã dùng rồi* lại được đưa ra
   lần nữa → chắc chắn có hai bên đang cầm cùng một token → **một trong hai là kẻ trộm**.
   Không biết bên nào, nên **huỷ cả họ token**.

```java
// RefreshTokenService.rotate()
if (!stored.isUsable(now)) {
    // Replay or a desynchronised client: distrust the whole family.
    int revoked = revoker.revokeFamily(stored.getFamilyId(), now);
    log.warn("Refresh token reuse detected for user {}; revoked {} token(s) in family {}",
            stored.getUserId(), revoked, stored.getFamilyId());
    throw new BadCredentialsException("Invalid refresh token");
}
stored.markUsed(now);
IssuedToken replacement = issue(stored.getUserId(), stored.getFamilyId());
```

**"Họ token" (`familyId`) là gì:** mọi token sinh ra từ cùng một lần đăng nhập mang chung một
`familyId`. Huỷ cả họ = đá phiên đăng nhập đó ra, kể cả kẻ trộm lẫn người thật.

```
Đăng nhập → T1 (family F)
  T1 dùng → T2 (family F), T1 đánh dấu đã dùng
  T2 dùng → T3 (family F)

  Kẻ trộm cầm T2 cũ, dùng lại
    → T2 đã có usedAt → PHÁT HIỆN
    → huỷ toàn bộ family F: T1, T2, T3 chết hết
    → người thật bị đăng xuất, và đó là điều ĐÚNG
```

Người dùng thật phải đăng nhập lại — bất tiện, nhưng **đúng**: có dấu hiệu token bị lộ thì
kết thúc phiên là phản ứng an toàn. **Ưu tiên an toàn hơn tiện lợi khi đã có bằng chứng bất
thường** — nói được câu này là ghi điểm.

### Ba chi tiết nhỏ mà đáng giá

**1. Database lưu `token_hash`, không lưu token.**

```java
@Column(name = "token_hash", nullable = false, unique = true, length = 64)
private String tokenHash;
```

Nếu database bị lộ, kẻ tấn công có bảng hash cũng **không đăng nhập được** — vì phải đưa ra
token gốc. Cùng một tư duy với việc không lưu mật khẩu dạng thô.

**2. Đăng xuất chỉ kết thúc phiên hiện tại.**

```java
/** Logout: ends this session only, leaving the user's other devices signed in. */
```

Đăng xuất trên điện thoại thì máy tính vẫn đăng nhập — đúng như người dùng mong đợi. Muốn
"đăng xuất mọi thiết bị" thì có `revokeAllForUser` riêng.

**3. Log lại khi phát hiện tái sử dụng.** Đây là **tín hiệu bảo mật**, không phải lỗi thường.
Không log thì bạn không bao giờ biết có ai đang bị đánh cắp token.

---

## 5. Mật khẩu: vì sao BCrypt chứ không phải SHA-256

Câu hỏi phỏng vấn kinh điển. Cả hai đều là hàm băm, khác nhau ở **mục đích thiết kế**.

| | SHA-256 | BCrypt |
|---|---|---|
| Thiết kế để | **Nhanh** | **Chậm có chủ đích** |
| Tốc độ | Hàng tỉ lần/giây trên GPU | Vài chục lần/giây |
| Salt | Phải tự thêm | **Có sẵn trong chuỗi kết quả** |
| Chỉnh độ khó theo thời gian | Không | **Có** (cost factor) |

Nghịch lý: với hàm băm mật khẩu, **nhanh là nhược điểm**. Kẻ tấn công lấy được database sẽ
thử hàng tỉ mật khẩu mỗi giây. Băm chậm biến việc đó thành hàng năm trời.

**Salt** là chuỗi ngẫu nhiên thêm vào mỗi mật khẩu trước khi băm. Không có salt thì hai người
dùng cùng mật khẩu sẽ có cùng hash — và **rainbow table** (bảng tra hash dựng sẵn) phá được
hàng loạt trong một lần.

**Cost factor** là thứ khiến BCrypt sống lâu: máy tính nhanh gấp đôi thì tăng cost lên một
nấc, thời gian băm trở lại như cũ. Thuật toán không cần đổi.

---

## 6. ORM và bẫy N+1

**ORM** ánh xạ bảng database thành đối tượng Java: `SlangWord` ↔ bảng `slang_word`. Bạn viết
`word.getDefinitions()` thay vì viết SQL.

Tiện, nhưng chính cái tiện đó giấu đi **số lượng câu SQL thật sự chạy**.

### N+1 là gì

Lấy 20 từ, mỗi từ có nhiều nghĩa. Code trông vô hại:

```java
for (SlangWord w : words) {        // 1 câu SQL lấy 20 từ
    w.getDefinitions().size();     // MỖI vòng lặp thêm 1 câu SQL nữa
}
```

**1 + 20 = 21 câu SQL** thay vì 1. Với 1000 từ là 1001 câu. Đây là **nguyên nhân số một khiến
API dùng ORM chạy chậm**, và nó không lộ ra khi test với 3 dòng dữ liệu.

### Cách SlangWord xử lý

```java
// SlangWordRepository.java
@EntityGraph(attributePaths = "definitions")
Page<SlangWord> findBy...(...);
```

`@EntityGraph` bảo JPA: **lấy luôn `definitions` trong cùng câu truy vấn** (bằng `JOIN`), thay
vì để lười rồi mỗi lần chạm vào lại đi hỏi database.

### Điểm phải nói ra: không phải lúc nào cũng nên fetch join

| | Lazy (mặc định) | EntityGraph / fetch join |
|---|---|---|
| Số câu SQL | Nhiều (bẫy N+1) | Một |
| Dữ liệu lấy về | Chỉ khi cần | **Toàn bộ, kể cả không dùng** |
| Hợp khi | Hiếm khi chạm tới quan hệ đó | **Luôn luôn** cần dữ liệu con |

SlangWord luôn hiện nghĩa kèm từ, nên fetch join là đúng. Nếu có màn hình chỉ liệt kê tên từ
thì fetch join lại thành lãng phí.

> **Cách phát hiện N+1 trong thực tế:** bật log SQL (`spring.jpa.show-sql=true`) rồi **đếm số
> câu**. Đây là thứ chỉ nhìn code sẽ không thấy — phải nhìn cái ORM thực sự làm.

---

## 7. Migration — vì sao không sửa database bằng tay

```
src/main/resources/db/migration/
    V1__init.sql
    V2__search_indexes.sql
    V3__refresh_token.sql
```

**Flyway** chạy các file này theo thứ tự, và ghi lại file nào đã chạy vào một bảng riêng.
Database mới thì chạy từ `V1`; database đã có `V1`, `V2` thì chỉ chạy `V3`.

Vì sao cần:

| Sửa database bằng tay | Migration |
|---|---|
| Máy bạn có cột đó, máy đồng nghiệp không | Ai chạy cũng ra **cùng một schema** |
| Không ai nhớ đã đổi gì, khi nào | **Lịch sử nằm trong git**, review được trong PR |
| Deploy lên production phải làm lại bằng tay, dễ sai | Tự chạy khi khởi động |
| Không lùi lại được | Viết `V4` để sửa `V3` |

**Quy tắc vàng: file migration đã chạy thì KHÔNG BAO GIỜ sửa lại.** Flyway lưu checksum; sửa
file cũ là nó báo lỗi và từ chối chạy. Muốn đổi thì **viết file mới**. Lý do: database của
người khác đã chạy bản cũ rồi — sửa file không làm database của họ đổi theo.

Đây chính là tư duy của git áp vào database: **chỉ thêm vào lịch sử, không viết lại lịch sử.**

---

## 8. Index: câu chuyện `LIKE '%abc%'`

File `V2__search_indexes.sql` tự giải thích, và đây là ví dụ tốt nhất về việc **hiểu công cụ
thay vì dùng theo thói quen**:

> *"Substring search (`... LIKE '%fragment%'`) cannot use a B-tree index: a B-tree is ordered
> by prefix, and a leading wildcard has no prefix to seek on."*

### Vì sao B-tree chịu thua

B-tree sắp xếp theo **tiền tố**, giống từ điển giấy. Tra `LIKE 'car%'` thì lật tới vần C là
thấy — nhanh. Nhưng `LIKE '%car%'` thì từ cần tìm có thể là *scar*, *oscar*, *carpet*… **không
có tiền tố để lật tới**. Database đành đọc từng dòng — *sequential scan*.

### Lời giải: GIN + pg_trgm

`pg_trgm` cắt mỗi giá trị thành các chuỗi **3 ký tự** (trigram): `carpet` → `car`, `arp`,
`rpe`, `pet`. Rồi đánh chỉ mục lên chính các trigram đó. Tìm `%car%` trở thành *"dòng nào chứa
trigram `car`"* — tra được bằng index.

```sql
create extension if not exists pg_trgm;
create index idx_slang_word_word_trgm
    on slang_word using gin (lower(word) gin_trgm_ops);
```

### Cái giá — và vì sao vẫn đáng

> *"GIN indexes are larger and slower to update than B-trees. That trade is right here because
> the dictionary is read constantly and written rarely — the opposite workload would not
> justify it."*

Đây là **hình dạng chuẩn của một quyết định kỹ thuật**: nêu cái được, nêu cái mất, và nêu
**điều kiện khiến đánh đổi đó đúng**. Từ điển 7.641 từ đọc liên tục, ghi hiếm → GIN đáng. Một
bảng log ghi liên tục thì ngược lại.

> **Nguyên tắc chung về index:** index làm **đọc nhanh, ghi chậm** và tốn đĩa. Đánh index vào
> mọi cột không phải là tối ưu, đó là làm chậm mọi thao tác ghi.

---

## 9. Phân trang — và vì sao phải chặn `size`

```java
// SlangWordController.java
service.search(q, searchField, PageRequest.of(page, Math.min(size, MAX_PAGE_SIZE)));
```

Trả toàn bộ 7.641 từ trong một response thì chậm cho server, tốn băng thông, và treo trình
duyệt. Phân trang trả từng khúc.

**Chi tiết đáng nói nhất là `Math.min(size, MAX_PAGE_SIZE)`.** Không có nó thì ai đó gọi
`?size=999999` và server cố nạp toàn bộ bảng vào bộ nhớ — **một cách làm sập server chỉ bằng
một tham số URL**. Đây cùng họ với lỗ hổng rate limit: *đừng bao giờ để client quyết định
server phải làm bao nhiêu việc*.

### Hai kiểu phân trang, nên biết cả hai

| | Offset (`page`/`size`) | Cursor (con trỏ) |
|---|---|---|
| Cách làm | `LIMIT 20 OFFSET 4000` | "cho tôi 20 dòng sau id X" |
| Trang sâu | **Chậm dần** — database vẫn phải đếm qua 4000 dòng | Nhanh đều |
| Thêm dòng mới lúc đang xem | **Lệch trang**, có dòng hiện hai lần | Không lệch |
| Nhảy tới trang 50 | Được | Không |

SlangWord dùng offset vì giao diện có số trang và dữ liệu gần như không đổi. Bảng đổi liên
tục (feed mạng xã hội) thì cursor mới đúng.

---

## 10. Tháp test và Testcontainers

SlangWord: **71 test backend (31 unit + 40 integration) + 8 frontend, coverage 91,2%**.

| Loại | Test cái gì | Tốc độ | Số lượng nên có |
|---|---|---|---|
| **Unit** | Quy tắc nghiệp vụ trong `service`, thay phụ thuộc bằng Mockito | Mili giây | Nhiều nhất |
| **Integration** | Nhiều tầng thật ghép lại, **database thật** | Giây | Vừa phải |
| **E2E** | Cả hệ thống qua giao diện | Phút | Ít nhất |

Càng lên cao càng chậm và càng dễ hỏng vặt, nên **đáy tháp phải rộng**.

### Vấn đề của integration test: lấy database ở đâu

| Cách | Vấn đề |
|---|---|
| Database chung trên máy dev | Test của hai người giẫm lên nhau; CI không có |
| **H2 in-memory** giả làm Postgres | **Nguy hiểm nhất** — H2 không có `pg_trgm`, cú pháp khác. Test xanh mà production hỏng |
| **Testcontainers** ✅ | Bật một container **PostgreSQL thật** cho test, xong thì xoá |

`AbstractIntegrationTest.java` dùng Testcontainers. Điểm mấu chốt: chạy **đúng PostgreSQL 16**
như production — nên index `pg_trgm` ở mục 8 được test thật, không phải test trên một database
giả không có tính năng đó.

> **Nguyên tắc:** thay thứ ở ngoài bằng đồ giả là đúng khi bạn **kiểm soát được sự khác biệt**
> (mock API thời tiết như dự án AI). Còn giả lập cả một database thì khác biệt nằm ở chỗ bạn
> không lường trước được — đó là lúc phải dùng đồ thật.

---

## 11. Tự kiểm tra

**1.** `401` khác `403` chỗ nào?

<details><summary>Đáp án</summary>

`401 Unauthorized` = *"bạn là ai?"* — chưa xác thực, hoặc token hết hạn. `403 Forbidden` =
*"biết bạn là ai rồi, nhưng không cho"* — đã xác thực nhưng không đủ quyền. Trả nhầm `403`
cho token hết hạn thì client không biết đường đi làm mới token.
</details>

**2.** JWT có mã hoá dữ liệu bên trong không?

<details><summary>Đáp án</summary>

**Không.** Nó chỉ **ký**. Payload là Base64, ai cầm token cũng đọc được — dán vào jwt.io là
thấy hết. Chữ ký chỉ đảm bảo nội dung không bị sửa. Không bao giờ để dữ liệu nhạy cảm trong
payload.
</details>

**3.** Vì sao xoay vòng refresh token, và vì sao dùng lại token cũ thì huỷ cả họ?

<details><summary>Đáp án</summary>

Xoay vòng để mỗi token chỉ dùng được một lần. Nếu một token đã đánh dấu "đã dùng" lại xuất
hiện lần nữa thì **có hai bên cùng cầm nó** — một trong hai là kẻ trộm. Server không biết bên
nào, nên huỷ cả họ là phản ứng an toàn: người thật phải đăng nhập lại, kẻ trộm mất quyền.
</details>

**4.** Vì sao băm mật khẩu bằng BCrypt chứ không phải SHA-256?

<details><summary>Đáp án</summary>

SHA-256 thiết kế để **nhanh** — hàng tỉ lần/giây trên GPU, tức là kẻ tấn công dò được rất
nhanh. BCrypt **chậm có chủ đích**, có salt sẵn, và có cost factor để tăng độ khó khi phần
cứng mạnh lên. Với băm mật khẩu, nhanh là nhược điểm.
</details>

**5.** N+1 là gì, phát hiện bằng cách nào?

<details><summary>Đáp án</summary>

Lấy N dòng cha rồi mỗi dòng lại chạy thêm một câu SQL lấy dòng con → 1 + N câu thay vì 1.
ORM giấu chuyện này đi vì code trông như một vòng lặp bình thường. Phát hiện bằng cách **bật
log SQL và đếm số câu**. Chữa bằng `@EntityGraph` hoặc `JOIN FETCH` — nhưng chỉ khi thật sự
luôn cần dữ liệu con.
</details>

**6.** Vì sao không được sửa file migration đã chạy?

<details><summary>Đáp án</summary>

Flyway lưu checksum của từng file; sửa file cũ là nó từ chối chạy. Lý do sâu hơn: database
của người khác **đã chạy bản cũ rồi**, sửa file không làm schema của họ đổi theo. Muốn đổi
thì viết file mới. Giống git: chỉ thêm vào lịch sử, không viết lại lịch sử.
</details>

**7.** Vì sao `LIKE '%abc%'` không dùng được index B-tree?

<details><summary>Đáp án</summary>

B-tree sắp xếp theo **tiền tố**. Dấu `%` ở đầu nghĩa là không có tiền tố để lật tới, nên
database phải quét toàn bảng. Lời giải là GIN + `pg_trgm`: cắt chuỗi thành trigram 3 ký tự rồi
đánh index lên trigram. Cái giá là index to hơn và ghi chậm hơn — đáng với dữ liệu đọc nhiều
ghi ít.
</details>

**8.** Vì sao integration test nên dùng Testcontainers thay vì H2 in-memory?

<details><summary>Đáp án</summary>

H2 chỉ **giả làm** Postgres: khác cú pháp, thiếu tính năng như `pg_trgm`. Test xanh trên H2 mà
production vẫn hỏng — loại lỗi tệ nhất. Testcontainers chạy **PostgreSQL 16 thật** trong
container rồi xoá đi, nên thứ được test đúng là thứ sẽ chạy.
</details>

---

## 12. Trả lời phỏng vấn

1. *Kiến trúc backend của bạn thế nào?* → Phân tầng web → service → repository → domain, mỗi
   tầng chỉ phụ thuộc tầng dưới. Quy tắc nghiệp vụ nằm ở `service` và **không biết gì về
   HTTP**, nên unit test được bằng Mockito mà không cần dựng Spring.

2. *Bạn xác thực bằng gì, vì sao?* → JWT, vì server không phải lưu session nên scale ngang dễ.
   Cái giá là **không thu hồi ngay được**, nên access token để ngắn và ghép với refresh token
   có thể thu hồi.

3. *Refresh token bị đánh cắp thì sao?* → Có **xoay vòng + phát hiện tái sử dụng**: mỗi token
   dùng một lần, dùng lại token cũ là bằng chứng có hai bên cùng cầm → huỷ cả `familyId`.
   Database chỉ lưu **hash** của token, lộ database cũng không đăng nhập được.

4. *API của bạn báo lỗi thế nào?* → RFC 7807 `ProblemDetail`, gom vào một
   `@RestControllerAdvice` nên mọi endpoint trả lỗi cùng hình dạng. Thêm từ trùng trả `409`
   kèm `?overwrite=true` để client khẳng định ý định thay vì server đoán.

5. *API chậm thì bạn tìm ở đâu trước?* → Đếm số câu SQL thật sự chạy — **N+1** là nguyên nhân
   phổ biến nhất với ORM và không lộ ra khi test với ít dữ liệu. Sau đó mới tới index.

6. *Bạn quản lý thay đổi database thế nào?* → Flyway, file `V1`, `V2`, `V3` trong git, review
   được trong PR, tự chạy khi khởi động. File đã chạy thì không sửa — muốn đổi thì viết file
   mới.

7. *Kể một quyết định về index.* → Tìm theo chuỗi con nên B-tree vô dụng vì `%` ở đầu không có
   tiền tố để seek. Chuyển sang GIN + `pg_trgm`. Đánh đổi: index to hơn, ghi chậm hơn — đúng
   với từ điển đọc nhiều ghi ít, sai với bảng ghi liên tục.

8. *Bạn test thế nào?* → 31 unit test cho `service` bằng Mockito, 40 integration test với
   **PostgreSQL thật qua Testcontainers**. Không dùng H2 vì nó chỉ giả làm Postgres — thiếu
   `pg_trgm`, và một test xanh trên database giả là thứ nguy hiểm hơn không có test.

---

## 13. Liên quan

- [HOC_SQL.md](HOC_SQL.md) — JOIN, index, transaction ở mức ngôn ngữ SQL
- [HOC_DSA_OOP.md](HOC_DSA_OOP.md) — SOLID, thứ đứng sau kiến trúc phân tầng ở mục 1
- [HOC_BAO_MAT_AI_APP.md](HOC_BAO_MAT_AI_APP.md) — rate limit, secret; mục 4 ở đó nói vì sao
  không có danh tính thì không có row-level security. SlangWord **có** danh tính, nên so hai
  dự án là thấy rõ sự khác biệt
- [HOC_DOCKER.md](HOC_DOCKER.md) — Compose, thứ chạy cả stack bằng một lệnh
- [HOC_GIT_GITHUB.md](HOC_GIT_GITHUB.md) — PR và review, nơi migration được duyệt
