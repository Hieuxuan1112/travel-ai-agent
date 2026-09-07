# Học Git và GitHub — cách người đi làm thật sự dùng

> Tài liệu này **không** dạy lại 50 lệnh git. Nó dạy đúng những gì bạn cần để (1) làm việc
> trong một nhóm mà không phá của người khác, (2) trả lời được câu hỏi phỏng vấn về quy
> trình. Mọi ví dụ lấy từ **chính repo này**, gồm cả những lần bạn đã làm sai.

**Mục lục**

1. [Git và GitHub không phải một thứ](#1-git-và-github-không-phải-một-thứ)
2. [Ba vùng của git — hiểu cái này là hiểu 80%](#2-ba-vùng-của-git--hiểu-cái-này-là-hiểu-80)
3. [Commit là gì, và vì sao message lại quan trọng](#3-commit-là-gì-và-vì-sao-message-lại-quan-trọng)
4. [Nhánh — vì sao không ai làm thẳng trên `main`](#4-nhánh--vì-sao-không-ai-làm-thẳng-trên-main)
5. [Vòng đời một thay đổi trong công ty](#5-vòng-đời-một-thay-đổi-trong-công-ty)
6. [Pull Request — thứ quan trọng nhất khi đi làm](#6-pull-request--thứ-quan-trọng-nhất-khi-đi-làm)
7. [Bốn lỗi bạn đã gặp thật](#7-bốn-lỗi-bạn-đã-gặp-thật)
8. [Merge conflict — không đáng sợ như nghe đồn](#8-merge-conflict--không-đáng-sợ-như-nghe-đồn)
9. [`merge` hay `rebase`](#9-merge-hay-rebase)
10. [Những thứ tuyệt đối không làm](#10-những-thứ-tuyệt-đối-không-làm)
11. [`.gitignore` và chuyện lỡ commit secret](#11-gitignore-và-chuyện-lỡ-commit-secret)
12. [Nhánh được bảo vệ và cổng CI](#12-nhánh-được-bảo-vệ-và-cổng-ci)
13. [Bảng lệnh hay dùng](#13-bảng-lệnh-hay-dùng)
14. [Tự kiểm tra](#14-tự-kiểm-tra)
15. [Trả lời phỏng vấn](#15-trả-lời-phỏng-vấn)

---

## 1. Git và GitHub không phải một thứ

Rất nhiều người dùng lẫn lộn hai từ này, và đây là câu hỏi lọc ứng viên rất hay gặp.

| | Git | GitHub |
|---|---|---|
| Là gì | **Phần mềm** chạy trên máy bạn | **Dịch vụ web** của một công ty (Microsoft) |
| Làm gì | Ghi lại lịch sử thay đổi của thư mục | Lưu bản sao repo trên mạng + PR, issue, Actions |
| Cần mạng? | **Không** — commit được cả khi mất mạng | Có |
| Thay được không? | Gần như không (chuẩn ngành) | Được: GitLab, Bitbucket, Gitea… |

Ví dụ đời thường: **git là cuốn sổ nhật ký**, GitHub là **cái tủ ở thư viện** để cất cuốn sổ
đó cho người khác đọc và ghi chú vào.

Hệ quả thực tế: `git commit` là việc **hoàn toàn trên máy bạn**. Commit xong mà chưa `git
push` thì trên GitHub **chưa có gì cả**. Đây là chỗ người mới hiểu sai nhiều nhất.

---

## 2. Ba vùng của git — hiểu cái này là hiểu 80%

Một file trong repo luôn nằm ở một trong ba vùng:

```
  Working directory        Staging area           Repository
  (thư mục làm việc)       (khu chờ)              (lịch sử)
        │                       │                      │
        │──── git add ─────────>│                      │
        │                       │──── git commit ─────>│
        │                       │                      │
        │<─────────── git checkout / git restore ──────│
                                                       │
                                                       │── git push ──> GitHub
```

Ví dụ đời thường — đóng một thùng hàng gửi đi:

| Vùng git | Tương đương |
|---|---|
| Working directory | Đồ đang bày trên bàn, sửa thoải mái |
| Staging area (`git add`) | Đồ đã **chọn** bỏ vào thùng, chưa dán băng keo |
| Commit (`git commit`) | **Dán băng keo, ghi nhãn** — thùng này chốt rồi |
| Push (`git push`) | **Mang ra bưu điện** gửi đi |

**Vì sao có staging area?** Để bạn chọn *một phần* thay đổi mà commit, thay vì gói tất cả.
Hôm nay bạn dùng đúng cơ chế này:

```bash
git add docs/MENTOR.md README.md HUONG_DAN.md
```

Trong thư mục lúc đó còn `chroma_travel_info/*.sqlite3` bị sửa vài byte. Không `git add` nó
là nó **không vào commit** — dù vẫn nằm trên đĩa. Đó là staging area làm việc.

> **Lệnh nguy hiểm cần biết:** `git add .` gói **tất cả**. Nhanh nhưng dễ lỡ tay đưa file rác,
> file to, hoặc file secret vào. Người đi làm lâu năm thường gõ tên file cụ thể.

---

## 3. Commit là gì, và vì sao message lại quan trọng

Một commit gồm: **ảnh chụp toàn bộ repo** tại thời điểm đó + tác giả + thời gian + message +
con trỏ tới commit cha. Mỗi commit có một mã băm SHA, ví dụ `0fe4723`.

Nhớ lại `docs/DEPLOY.md`: pipeline deploy dùng **tag SHA** chứ không dùng `latest`, chính là
mã này. Nó là sợi dây duy nhất nối "image đang chạy trên Azure" về "đúng dòng code nào".

### Message: viết cho người đọc 6 tháng sau

Message tệ nhất là loại mô tả **cái đã làm**, vì `git diff` đã nói điều đó rồi:

| Tệ | Vì sao tệ |
|---|---|
| `update` | Không mang thông tin nào |
| `fix bug` | Bug nào? |
| `sửa MENTOR.md` | Diff đã cho biết file nào bị sửa |

Message tốt trả lời **vì sao**:

```
fix(agent): make the model quote tool figures, lifting judge score 3.5 -> 4.6

Multi-step answers scored 2/5 while single-step ones scored 4-5/5. Judging one
fixed answer five times showed the judge is deterministic, so the variance was
the agent's: it aggregated several weather results into qualitative prose and
dropped every number the rubric asks for.
```

Cấu trúc chuẩn: **dòng đầu ≤ 72 ký tự, thể mệnh lệnh** (`fix`, `add`, `remove` — không phải
`fixed`/`adding`), **một dòng trống**, rồi phần thân giải thích *vì sao*.

### Conventional Commits

Tiền tố `fix:`, `feat:`, `docs:`, `refactor:`, `test:`, `chore:` — đây là quy ước rất phổ
biến ở công ty. Repo này đang dùng. Lợi ích: máy đọc được để **tự sinh changelog** và **tự
tăng số phiên bản** (`fix:` → 1.2.**4**, `feat:` → 1.**3**.0).

---

## 4. Nhánh — vì sao không ai làm thẳng trên `main`

Nhánh là **một con trỏ tới một commit**. Nhẹ tới mức tạo ra gần như miễn phí — đó là lý do
git thắng các hệ thống cũ (SVN), nơi tạo nhánh là chuyện tốn kém.

```
main         A ── B ── C
                        \
nhánh của bạn            D ── E
```

`main` là **bản luôn phải chạy được**. Ở công ty, `main` thường là thứ đang deploy cho khách
hàng dùng — commit thẳng vào đó nghĩa là đẩy code chưa ai xem lên production.

| Làm thẳng trên `main` | Làm trên nhánh riêng |
|---|---|
| Code hỏng là cả nhóm đứng | Hỏng chỉ mình bạn chịu |
| Không ai review trước | Có chỗ để đồng nghiệp góp ý |
| Hai người sửa cùng lúc là đụng nhau | Mỗi người một nhánh, gộp sau |
| Muốn bỏ thì phải revert giữa lịch sử chung | Bỏ nhánh là xong, `main` không biết gì |

Đặt tên nhánh theo quy ước, ví dụ nhánh bạn vừa dùng: `docs/deploy-and-persistence`. Kiểu
phổ biến ở công ty: `feature/ten-viec`, `fix/ten-loi`, `docs/…`, hoặc gắn mã ticket
`PROJ-123-them-dang-nhap`.

---

## 5. Vòng đời một thay đổi trong công ty

Đây là vòng bạn sẽ lặp lại hàng ngày khi đi làm:

```
1. git checkout main          ← luôn bắt đầu từ main
2. git pull                   ← lấy code mới nhất của đồng nghiệp
3. git checkout -b fix/abc    ← tạo nhánh mới TỪ main vừa cập nhật
4. ... sửa code ...
5. git add <file>             ← chọn thứ muốn đưa vào
6. git commit -m "..."        ← chốt, giải thích vì sao
7. git push -u origin fix/abc ← đẩy nhánh lên GitHub
8. Mở Pull Request trên web
9. CI chạy — đợi xanh
10. Đồng nghiệp review — sửa theo góp ý, commit + push tiếp
11. Merge PR
12. git checkout main && git pull    ← QUAY VỀ MAIN
13. git branch -d fix/abc            ← xoá nhánh đã xong
```

**Bước 1-2 và 12-13 là hai chỗ người mới hay bỏ.** Bỏ bước 1-2 thì nhánh của bạn mọc ra từ
code cũ, dễ conflict. Bỏ bước 12-13 thì… đúng cái bạn vừa dính, xem mục 7.

---

## 6. Pull Request — thứ quan trọng nhất khi đi làm

**PR không phải một tính năng của git.** Nó là của GitHub/GitLab. Về bản chất PR là lời đề
nghị: *"tôi có nhánh này, xin gộp vào `main`, mời mọi người xem trước."*

Ở công ty, PR là nơi diễn ra **phần lớn việc học nghề của bạn**. Nó đồng thời là:

| Vai trò của PR | Nghĩa là gì |
|---|---|
| Chỗ review | Người có kinh nghiệm đọc diff và góp ý |
| Cổng chất lượng | CI chạy test/lint; đỏ thì nút Merge bị khoá |
| Tài liệu lịch sử | 6 tháng sau ai đó hỏi "vì sao code thế này" → mở PR ra đọc thảo luận |
| Bằng chứng công việc | Người ngoài nhìn repo thấy bạn làm việc có quy trình |

### Viết PR thế nào

- **Title**: như dòng đầu commit — ngắn, mệnh lệnh, nói kết quả.
- **Body**: trả lời ba câu — *vì sao cần thay đổi này*, *đã làm gì*, *kiểm chứng ra sao*.
- **Nhỏ thôi**: PR 200 dòng được review kỹ; PR 3000 dòng nhận về "LGTM" cho xong. Đây là
  điều người mới hay làm ngược.

### Nhận review thế nào

Bị góp ý **không phải bị chê**. Nhưng cũng đừng sửa mù: nếu thấy góp ý sai hoặc chưa hiểu,
**hỏi lại**. Câu trả lời tốt nhất trong PR là *"chỗ này em làm vậy vì X, anh thấy có ổn
không?"* — nó cho thấy bạn có lý do, không phải làm bừa.

---

## 7. Bốn lỗi bạn đã gặp thật

Phần đáng học nhất tài liệu này. Bốn lỗi dưới đây đều **đã xảy ra** trong repo này.

### Lỗi 1 — Commit xong tưởng là đã lên GitHub

Có 4 commit nằm im trên máy nhiều ngày. `git log` thấy đủ, nhưng GitHub **không có gì**.

**Cách tự kiểm:**

```bash
git status -sb
```

Dòng đầu ra `## main...origin/main [ahead 4]` — chữ **ahead 4** nghĩa là 4 commit chưa push.
Không có ngoặc vuông nghĩa là đã đồng bộ.

### Lỗi 2 — Push xong tưởng là đã xong

Push lên nhánh `docs/deploy-and-persistence` rồi, nhưng `main` vẫn ở commit cũ. Người khác
clone repo về vẫn **không thấy** thay đổi nào, vì mặc định họ ở `main`.

> **Ba trạng thái khác nhau, đừng nhầm:** commit (trên máy) → push (lên nhánh ở GitHub) →
> **merge** (vào `main`). Chỉ bước cuối mới là "xong".

### Lỗi 3 — Merge PR xong vẫn đứng ở nhánh cũ rồi commit tiếp

Đây là lỗi kinh điển và bạn đã dính đúng nó. Sau khi merge PR #1:

```
Bạn tưởng:  đang ở main, commit mới vào main
Thực tế:    vẫn ở docs/deploy-and-persistence, commit mới vào nhánh đó
Hậu quả:    phải mở PR #2 cho một commit lẽ ra đi cùng PR #1
```

**Cách tránh:** merge xong là làm ngay ba lệnh, thành phản xạ:

```bash
git checkout main && git pull && git branch -d ten-nhanh-cu
```

**Cách tự kiểm trước mỗi commit:** `git branch --show-current`. Mất 1 giây.

### Lỗi 4 — File nhị phân bị sửa mà không ai chủ ý

`chroma_travel_info/chroma.sqlite3` liên tục hiện trong `git status` chỉ vì chạy app làm
sqlite ghi lại vài byte — **nội dung không đổi**. Nếu vô tư `git add .` thì mỗi commit phình
thêm vài MB rác mà không mang thông tin nào.

Bài học: **`git status` sạch là một thói quen tốt.** File nào cứ hiện lên hoài mà bạn không
chủ ý sửa thì phải hiểu vì sao, chứ đừng quen mắt bỏ qua.

---

## 8. Merge conflict — không đáng sợ như nghe đồn

Conflict xảy ra khi **hai nhánh sửa cùng một dòng** của cùng một file. Git không dám đoán,
nên nhờ bạn quyết. Nó chèn dấu vào file:

```
<<<<<<< HEAD
dòng theo phiên bản của nhánh bạn đang đứng
=======
dòng theo phiên bản nhánh được gộp vào
>>>>>>> ten-nhanh-kia
```

Cách xử lý:

1. Mở file, **xoá cả ba dòng dấu** `<<<<<<<`, `=======`, `>>>>>>>`.
2. Sửa lại thành nội dung đúng — có thể là bên này, bên kia, hoặc trộn cả hai.
3. `git add <file>` để báo "đã giải quyết".
4. `git commit` (không cần `-m`, git soạn sẵn message).

**Nguyên tắc phòng conflict:** `git pull` thường xuyên và giữ PR nhỏ. Nhánh sống 3 tuần rồi
mới merge thì gần như chắc chắn conflict.

**Nếu rối quá:** `git merge --abort` đưa mọi thứ về như trước khi merge. Không mất gì.

---

## 9. `merge` hay `rebase`

Hai cách đưa code từ nhánh này sang nhánh kia, khác nhau ở **hình dạng lịch sử**.

```
merge:                          rebase:
  A ── B ──── M (main)            A ── B ── D' ── E' (main)
       \     /
        D ── E                  (D, E được "chép lại" lên sau B)
```

| | `merge` | `rebase` |
|---|---|---|
| Lịch sử | Giữ nguyên sự thật, có nhánh rẽ | Thẳng tắp, dễ đọc |
| Commit | Thêm một "merge commit" | Viết lại commit → **đổi SHA** |
| An toàn | Rất an toàn | Nguy hiểm nếu nhánh đã chia sẻ |

**Quy tắc vàng: không bao giờ rebase một nhánh mà người khác đang dùng.** Vì rebase tạo ra
commit mới có SHA khác, đồng nghiệp pull về sẽ thấy lịch sử "lệch" và rất khó gỡ.

Người mới đi làm: **cứ dùng `merge`**, và làm theo quy ước của nhóm. Mỗi công ty một luật —
hỏi ngay ngày đầu là an toàn nhất.

---

## 10. Những thứ tuyệt đối không làm

| Đừng làm | Vì sao |
|---|---|
| `git push --force` lên nhánh chung | Xoá commit của người khác khỏi lịch sử. Nếu buộc phải, dùng `--force-with-lease` |
| `git reset --hard` khi chưa hiểu | Xoá sạch thay đổi chưa commit, **không có thùng rác** |
| Commit file secret (`.env`, key, mật khẩu) | Xem mục 11 — xoá đi vẫn còn trong lịch sử |
| `git commit -am` theo phản xạ | Gói mọi file đã theo dõi, kể cả thứ bạn không định đưa vào |
| Sửa lịch sử đã push chung (`rebase`, `amend`) | Phá lịch sử của cả nhóm |
| Để `git status` bẩn triền miên | Quen mắt rồi có ngày commit nhầm thứ quan trọng |

Câu thần chú khi hoảng: **commit rồi thì gần như luôn cứu được** (`git reflog` lưu cả những
thứ tưởng đã mất). Chưa commit thì không ai cứu nổi. Nên khi sắp làm gì đáng sợ, **commit
trước đã**.

---

## 11. `.gitignore` và chuyện lỡ commit secret

`.gitignore` liệt kê những gì git **không theo dõi**: thư mục `venv/`, `__pycache__/`, file
`.env`, thư mục build.

Repo này có một ví dụ hay ở `docs/MENTOR.md` mục 20: `chroma_travel_info/` **cố ý bị bỏ khỏi**
`.gitignore` để vector store được commit vào repo — deploy khỏi phải dựng lại. Tức là
`.gitignore` là **quyết định thiết kế**, không phải danh sách chép sẵn.

### Nếu lỡ commit secret

**Phải coi như secret đó đã lộ.** Kể cả bạn xoá ở commit sau, nó vẫn nằm trong lịch sử và ai
clone repo về cũng đọc được.

Thứ tự xử lý đúng:

1. **Vô hiệu hoá key ngay** (revoke trên Google/Azure/AWS) — việc này gấp nhất.
2. Tạo key mới.
3. Rồi mới tính chuyện dọn lịch sử (`git filter-repo`) nếu cần.

Nhiều người làm ngược: cuống lên xoá lịch sử trước, trong lúc đó key cũ vẫn sống và đã bị bot
quét GitHub nhặt mất. **Bot quét key công khai chỉ mất vài giây.**

Đây cũng chính là lý do repo này dùng **OIDC keyless** cho Azure (xem
[HOC_CICD_CLOUD.md](HOC_CICD_CLOUD.md) mục 5): không có mật khẩu dài hạn nào tồn tại để mà lộ.

---

## 12. Nhánh được bảo vệ và cổng CI

Ở công ty, `main` thường được **bảo vệ** (branch protection). Nghĩa là GitHub từ chối:

- push thẳng vào `main` — bắt buộc đi qua PR
- merge khi CI chưa xanh
- merge khi chưa có đủ số người approve

Repo này đã có sẵn hai cổng đó, đúng chuẩn công ty:

| Cổng | Chặn cái gì |
|---|---|
| `ci.yml` | Test + lint. Chạy cả trên PR |
| Eval gate | Điểm chất lượng dưới ngưỡng là đỏ |
| `cd.yml` | Chỉ chạy **sau khi CI xanh** trên `main` |

Nên nhớ: `cd.yml` móc vào `main` chứ không móc vào PR. Đó là lý do PR của bạn chạy CI mà
**không** deploy — chỉ khi merge vào `main` thì Azure mới được cập nhật.

---

## 13. Bảng lệnh hay dùng

**Xem mình đang ở đâu**

| Lệnh | Trả lời câu hỏi |
|---|---|
| `git status -sb` | Đang ở nhánh nào, lệch với remote bao nhiêu, file nào đang sửa |
| `git branch --show-current` | Đang đứng ở nhánh nào (gõ trước mỗi commit) |
| `git log --oneline -5` | 5 commit gần nhất |
| `git diff` | Thay đổi **chưa** `git add` |
| `git diff --staged` | Thay đổi **đã** `git add`, sắp commit |

**Làm việc hằng ngày**

| Lệnh | Làm gì |
|---|---|
| `git checkout main` | Về nhánh main |
| `git pull` | Kéo code mới nhất về |
| `git checkout -b ten-nhanh` | Tạo nhánh mới và nhảy sang luôn |
| `git add <file>` | Đưa file vào khu chờ |
| `git commit -m "..." -m "..."` | Chốt (nhiều `-m` = nhiều đoạn) |
| `git push -u origin ten-nhanh` | Đẩy nhánh mới lên (lần đầu cần `-u`) |
| `git push` | Những lần sau |

**Cứu hộ**

| Lệnh | Dùng khi |
|---|---|
| `git restore <file>` | Bỏ thay đổi chưa `git add` của một file |
| `git restore --staged <file>` | Lấy file ra khỏi khu chờ (giữ nguyên nội dung) |
| `git commit --amend` | Sửa commit vừa tạo — **chỉ khi chưa push** |
| `git merge --abort` | Bỏ giữa chừng một merge đang conflict |
| `git reflog` | Xem mọi thứ HEAD từng trỏ tới — cứu commit "đã mất" |
| `git stash` / `git stash pop` | Cất tạm thay đổi để đổi nhánh gấp |

---

## 14. Tự kiểm tra

Trả lời trước rồi mới mở đáp án.

**1.** Bạn `git commit` xong. Đồng nghiệp clone repo về có thấy thay đổi đó không?

<details><summary>Đáp án</summary>

Không. Commit chỉ nằm trên máy bạn. Phải `git push` mới lên GitHub — và nếu push vào nhánh
riêng thì đồng nghiệp ở `main` vẫn chưa thấy, phải merge PR nữa.
</details>

**2.** Staging area để làm gì? Bỏ nó đi có được không?

<details><summary>Đáp án</summary>

Để **chọn** phần nào của thay đổi sẽ vào commit này. Nhờ nó mà hôm nay ta commit được ba file
docs mà bỏ lại file sqlite bị sửa vài byte. Bỏ nó thì mỗi commit buộc phải gói tất cả.
</details>

**3.** Vì sao không nên `git push --force` lên nhánh chung?

<details><summary>Đáp án</summary>

Nó ghi đè lịch sử trên remote — commit của người khác biến mất. Nếu bắt buộc phải force,
dùng `--force-with-lease`: lệnh này từ chối nếu remote đã có commit mới mà bạn chưa thấy.
</details>

**4.** Lỡ commit `.env` chứa API key và đã push. Làm gì đầu tiên?

<details><summary>Đáp án</summary>

**Revoke key ngay lập tức**, rồi tạo key mới. Dọn lịch sử là việc làm sau. Xoá file ở commit
sau **không** làm key an toàn — nó vẫn nằm trong lịch sử, và bot quét GitHub tìm ra key công
khai chỉ trong vài giây.
</details>

**5.** `merge` khác `rebase` chỗ nào, và khi nào tuyệt đối không rebase?

<details><summary>Đáp án</summary>

`merge` giữ nguyên hình dạng lịch sử và thêm một merge commit. `rebase` chép lại các commit
lên đầu nhánh đích, cho lịch sử thẳng nhưng **đổi SHA**. Tuyệt đối không rebase nhánh mà
người khác đang dùng, vì SHA đổi làm lịch sử của họ lệch.
</details>

**6.** Merge PR xong, việc tiếp theo phải làm là gì?

<details><summary>Đáp án</summary>

`git checkout main` → `git pull` → xoá nhánh cũ. Nếu không, bạn vẫn đứng ở nhánh đã merge và
commit tiếp vào đó — đúng lỗi đã phải mở PR #2 để sửa.
</details>

**7.** Vì sao PR nhỏ tốt hơn PR to?

<details><summary>Đáp án</summary>

PR to không được review thật — người ta lướt rồi duyệt cho xong. PR nhỏ thì đọc được từng
dòng, bắt được lỗi thật, và ít conflict hơn vì sống ngắn.
</details>

---

## 15. Trả lời phỏng vấn

1. *Git và GitHub khác nhau thế nào?* → Git là phần mềm quản lý phiên bản chạy trên máy,
   hoạt động không cần mạng. GitHub là dịch vụ lưu repo trên mạng, thêm PR, issue, CI. Đổi
   sang GitLab vẫn dùng git y nguyên.

2. *Mô tả quy trình làm một tính năng.* → Từ `main` đã `pull` mới nhất, tạo nhánh riêng,
   commit nhỏ có message giải thích *vì sao*, push, mở PR, đợi CI xanh và review, merge, rồi
   về `main` và xoá nhánh.

3. *Vì sao không commit thẳng vào `main`?* → `main` là bản luôn phải chạy được, thường là thứ
   đang deploy. Đi qua nhánh + PR để có chỗ review và để CI chặn trước khi code hỏng ảnh
   hưởng cả nhóm.

4. *Staging area để làm gì?* → Chọn phần nào vào commit này. Cho phép tách một lần sửa lộn xộn
   thành nhiều commit gọn, mỗi commit một ý.

5. *Xử lý merge conflict thế nào?* → Mở file, xoá dấu `<<<<<<<`/`=======`/`>>>>>>>`, quyết
   nội dung đúng, `git add` rồi commit. Phòng bằng cách pull thường xuyên và giữ PR nhỏ.

6. *`merge` hay `rebase`?* → Merge giữ lịch sử thật, rebase cho lịch sử thẳng nhưng đổi SHA.
   Không rebase nhánh đã chia sẻ. Ở nhóm thì theo quy ước chung của nhóm.

7. *Lỡ đẩy secret lên repo thì sao?* → Revoke key ngay, tạo key mới, rồi mới dọn lịch sử. Xoá
   ở commit sau không đủ vì lịch sử vẫn còn. Tốt nhất là thiết kế để không có key dài hạn —
   như repo này dùng OIDC keyless cho Azure.

8. *Bạn viết commit message thế nào?* → Dòng đầu ngắn, thể mệnh lệnh, theo Conventional
   Commits (`fix:`, `feat:`, `docs:`). Thân giải thích **vì sao** thay đổi, vì *cái gì* thì
   diff đã nói rồi.

9. *`git status` của bạn có sạch không?* → Câu hỏi bẫy kiểm tra thói quen. Trả lời đúng: giữ
   sạch, file nào cứ hiện lên mà không chủ ý sửa thì phải hiểu vì sao, đừng quen mắt bỏ qua.

---

## 16. Liên quan

- [HOC_CICD_CLOUD.md](HOC_CICD_CLOUD.md) — cái gì xảy ra **sau khi** bạn merge: CI, Trivy,
  GHCR, deploy Azure.
- [../MENTOR.md](../MENTOR.md) mục 20 — vì sao `.gitignore` của repo này cố ý cho vector
  store vào git.
