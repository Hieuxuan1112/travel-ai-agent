# SQL — từ chưa biết gì đến làm được bài phỏng vấn

> Viết cho người sắp phỏng vấn fresher AI Engineer, CV có ghi SQL và cần nói được cho vững.
> Mọi câu SQL trong bài đều **chạy được thật** trên cùng **một bộ bảng mẫu duy nhất**, và
> mọi kết quả in ra trong bài là kết quả **thật** lấy từ chương trình kèm theo:
> [`demo_sql.py`](demo_sql.py) — chỉ dùng `sqlite3` của thư viện chuẩn, không cài gì thêm.

**Cách học bài này:** mở một cửa sổ terminal chạy chế độ tương tác, mở bài giảng ở cửa sổ
bên cạnh, đọc tới đâu gõ lại tới đó. Đọc không gõ thì hôm phỏng vấn sẽ không nhớ.

```bash
venv\Scripts\python.exe docs\hoc\demo_sql.py
```

| Lệnh | Tác dụng |
|---|---|
| `python docs\hoc\demo_sql.py` | chế độ **tương tác** — gõ SQL, xem kết quả ngay |
| `python docs\hoc\demo_sql.py --demo` | chạy lại **toàn bộ ví dụ** trong bài |
| `python docs\hoc\demo_sql.py --demo 8` | chỉ chạy ví dụ mục 8 (window function) |
| `python docs\hoc\demo_sql.py --baitap` | lời giải 10 bài tập cuối bài |
| `python docs\hoc\demo_sql.py --index` | đo thời gian thật trên bảng 200.000 dòng |

**Mục lục**

1. [SQL là gì — mô hình trong đầu](#1-sql-là-gì--mô-hình-trong-đầu)
2. [Bảng mẫu dùng xuyên suốt cả bài](#2-bảng-mẫu-dùng-xuyên-suốt-cả-bài)
3. [SELECT, WHERE, ORDER BY](#3-select-where-order-by)
4. [JOIN — nối bảng](#4-join--nối-bảng)
5. [GROUP BY và HAVING](#5-group-by-và-having)
6. [Subquery — truy vấn lồng](#6-subquery--truy-vấn-lồng)
7. [CTE — mệnh đề WITH](#7-cte--mệnh-đề-with)
8. [Window function](#8-window-function)
9. [NULL và những cạm bẫy của nó](#9-null-và-những-cạm-bẫy-của-nó)
10. [Index — và vì sao query chậm](#10-index--và-vì-sao-query-chậm)
11. [Transaction và ACID](#11-transaction-và-acid)
12. [Những câu lý thuyết hay bị hỏi](#12-những-câu-lý-thuyết-hay-bị-hỏi)
13. [10 bài tập kiểu phỏng vấn (kèm lời giải)](#13-10-bài-tập-kiểu-phỏng-vấn-kèm-lời-giải)
14. [Lộ trình 7 ngày trước hôm phỏng vấn](#14-lộ-trình-7-ngày-trước-hôm-phỏng-vấn)

---

## 1. SQL là gì — mô hình trong đầu

Một **cơ sở dữ liệu quan hệ** chỉ là một tập các **bảng**. Một bảng giống hệt một sheet Excel:
có **cột** (mỗi cột một loại thông tin, có kiểu dữ liệu cố định) và có **dòng** (mỗi dòng
một thực thể: một nhân viên, một đơn hàng, một lượt log).

```text
  CƠ SỞ DỮ LIỆU  (một file / một server)
  │
  ├── BẢNG nhan_vien
  │     ┌────────┬──────────┬────────┐   ← tên cột (schema: cố định, có kiểu)
  │     │ ho_ten │ phong_id │ luong  │
  │     ├────────┼──────────┼────────┤
  │     │ An     │    10    │   25   │   ← một DÒNG = một nhân viên
  │     │ Binh   │    10    │   18   │
  │     └────────┴──────────┴────────┘
  │           ▲
  │           └── một Ô = một giá trị (hoặc NULL = "không có dữ liệu")
  │
  ├── BẢNG phong_ban
  └── BẢNG doanh_so
```

Điểm khác biệt lớn nhất so với lập trình thường: **SQL là ngôn ngữ khai báo**. Bạn mô tả
*"tôi muốn cái gì"*, không mô tả *"làm thế nào để lấy"*. Không có vòng lặp `for`, không có
`if` lồng nhau. Bạn viết:

```sql
SELECT ho_ten FROM nhan_vien WHERE luong > 20;
```

và bộ tối ưu (query optimizer) của database tự quyết định: quét cả bảng hay dùng index, đọc
bảng nào trước, nối bảng bằng thuật toán nào. Đây chính là lý do mục 10 (index) tồn tại: khi
query chậm, bạn không sửa vòng lặp — bạn sửa **dữ liệu và cách viết** để bộ tối ưu chọn được
đường đi tốt.

Bốn nhóm lệnh (nhớ để trả lời phỏng vấn cho gọn):

| Nhóm | Lệnh | Nghĩa |
|---|---|---|
| **DQL** — hỏi dữ liệu | `SELECT` | 90% công việc thật, và ~100% câu hỏi phỏng vấn fresher |
| **DML** — sửa dữ liệu | `INSERT`, `UPDATE`, `DELETE` | thêm / sửa / xoá dòng |
| **DDL** — sửa cấu trúc | `CREATE`, `ALTER`, `DROP` | tạo bảng, tạo index |
| **TCL** — giao dịch | `BEGIN`, `COMMIT`, `ROLLBACK` | mục 11 |

<details>
<summary><b>Tự kiểm tra 1</b> — "SQL là ngôn ngữ khai báo" nghĩa là gì, nói trong một câu?</summary>

Mình mô tả **kết quả mong muốn**, database tự chọn **cách thực hiện**. Hệ quả thực tế: hai
câu SQL viết khác nhau nhưng cùng ý nghĩa có thể chạy nhanh chậm khác nhau rất nhiều, vì
chúng khiến bộ tối ưu chọn kế hoạch khác nhau (xem mục 10.4 — bọc hàm quanh cột làm mất index).
</details>

---

## 2. Bảng mẫu dùng xuyên suốt cả bài

Một công ty nhỏ: **phòng ban**, **nhân viên**, và **doanh số theo tháng**. Toàn bộ ví dụ,
bài tập, sơ đồ trong bài đều chạy trên đúng ba bảng này.

> Dữ liệu cố tình để **không dấu** (An, Binh, Ky thuat…) để chạy trên mọi console Windows
> không bị lỗi font. Lương tính theo **triệu đồng/tháng**, doanh thu theo **triệu đồng**.

```sql
CREATE TABLE phong_ban (
    phong_id  INTEGER PRIMARY KEY,
    ten_phong TEXT NOT NULL,
    dia_diem  TEXT NOT NULL
);

CREATE TABLE nhan_vien (
    nv_id      INTEGER PRIMARY KEY,
    ho_ten     TEXT NOT NULL,
    phong_id   INTEGER REFERENCES phong_ban(phong_id),  -- NULL = chưa phân phòng
    luong      INTEGER,                                 -- NULL = chưa chốt lương
    ngay_vao   TEXT NOT NULL,                           -- 'YYYY-MM-DD'
    quan_ly_id INTEGER REFERENCES nhan_vien(nv_id)      -- NULL = không có sếp
);

CREATE TABLE doanh_so (
    ds_id     INTEGER PRIMARY KEY,
    nv_id     INTEGER NOT NULL REFERENCES nhan_vien(nv_id),
    thang     TEXT NOT NULL,      -- 'YYYY-MM'
    doanh_thu INTEGER NOT NULL
);
```

Dữ liệu (đây là output thật của `SELECT * FROM ...`):

```text
  phong_ban                                nhan_vien
  +----------+------------+-------------+  +-------+--------+----------+-------+------------+------------+
  | phong_id | ten_phong  | dia_diem    |  | nv_id | ho_ten | phong_id | luong | ngay_vao   | quan_ly_id |
  +----------+------------+-------------+  +-------+--------+----------+-------+------------+------------+
  |       10 | Ky thuat   | Ha Noi      |  |     1 | An     |       10 |    25 | 2021-03-01 |       NULL |
  |       20 | Kinh doanh | Ho Chi Minh |  |     2 | Binh   |       10 |    18 | 2022-06-15 |          1 |
  |       30 | Nhan su    | Ha Noi      |  |     3 | Chi    |       10 |    18 | 2023-01-10 |          1 |
  |       40 | Nghien cuu | Da Nang     |  |     4 | Dung   |       20 |    22 | 2020-11-20 |          1 |
  +----------+------------+-------------+  |     5 | Ha     |       20 |    15 | 2023-07-01 |          4 |
       ▲                                   |     6 | Khoa   |       30 |    12 | 2024-02-05 |          1 |
       │ phòng 40 CHƯA CÓ AI               |     7 | Linh   |       30 |  NULL | 2024-09-01 |          6 |
                                           |     8 | Minh   |     NULL |    14 | 2025-01-15 |          1 |
  doanh_so (12 dòng)                       +-------+--------+----------+-------+------------+------------+
  +-------+---------+-------+                                   ▲          ▲
  | nv_id | thang   | d_thu |               Minh CHƯA CÓ PHÒNG ─┘          └─ Linh CHƯA CHỐT LƯƠNG
  +-------+---------+-------+
  |     2 | 2025-01 |    60 |   Chỉ có 3 người (Binh, Dung, Ha) có doanh số.
  |     2 | 2025-02 |   150 |   Mỗi người 4 tháng: 2025-01 → 2025-04.
  |     2 | 2025-03 |    90 |
  |     2 | 2025-04 |    70 |   Binh: 60, 150,  90,  70   (tổng 370)
  |     4 | 2025-01 |   120 |   Dung: 120, 150,  90, 200  (tổng 560)
  |   ... |     ... |   ... |   Ha:   80,  95, 130, 110   (tổng 415)
  +-------+---------+-------+
```

**Bốn "cái bẫy" được cài sẵn trong dữ liệu** — nhớ chúng, vì mọi mục sau đều dựa vào:

1. **Minh** có `phong_id = NULL` → biến mất khi `INNER JOIN` (mục 4), làm hỏng `NOT IN` (mục 6.3).
2. **Phòng 40 (Nghiên cứu)** không có nhân viên nào → chỉ hiện ra nếu dùng `LEFT/RIGHT JOIN`.
3. **Linh** có `luong = NULL` → làm `AVG`, `COUNT`, `<>` cho kết quả gây bất ngờ (mục 9).
4. **Binh và Chi cùng lương 18**, **Binh và Dung cùng doanh thu 90 tháng 03** → dùng để phân
   biệt `ROW_NUMBER` / `RANK` / `DENSE_RANK` (mục 8.3).

Quan hệ giữa ba bảng (khoá ngoại — foreign key):

```text
        phong_ban                    nhan_vien                     doanh_so
     ┌──────────────┐            ┌──────────────┐             ┌──────────────┐
     │ phong_id  PK │◀───────────│ phong_id  FK │◀────────────│ nv_id     FK │
     │ ten_phong    │   1 : N    │ nv_id     PK │    1 : N    │ thang        │
     │ dia_diem     │            │ quan_ly_id FK│─┐           │ doanh_thu    │
     └──────────────┘            └──────────────┘ │           └──────────────┘
                                      ▲           │
                                      └───────────┘  tự trỏ vào chính mình
                                       (sếp cũng là một nhân viên → SELF JOIN, mục 4.5)

     PK = primary key  : khoá chính, định danh duy nhất một dòng, không NULL, tự có index.
     FK = foreign key  : khoá ngoại, trỏ tới khoá chính bảng khác, CÓ THỂ NULL.
     1 : N             : một phòng có nhiều nhân viên; một nhân viên thuộc tối đa một phòng.
```

<details>
<summary><b>Tự kiểm tra 2</b> — Nếu xoá dòng phòng 10 khỏi <code>phong_ban</code> thì chuyện gì xảy ra?</summary>

Nếu database **bật ràng buộc khoá ngoại** (SQLite phải bật thủ công bằng
`PRAGMA foreign_keys = ON`, `demo_sql.py` đã bật), lệnh xoá sẽ **báo lỗi** vì An, Binh, Chi
đang trỏ tới phòng 10 — đó chính là tác dụng của khoá ngoại: giữ dữ liệu không bị "mồ côi".

Muốn xoá được thì phải xử lý các dòng con trước, hoặc khai báo hành vi lan truyền khi tạo bảng
(`ON DELETE CASCADE` = xoá luôn nhân viên, `ON DELETE SET NULL` = đặt `phong_id` về NULL).
</details>

---

## 3. SELECT, WHERE, ORDER BY

### Nói bằng lời

Một câu `SELECT` là một dây chuyền xử lý gồm bốn động tác, luôn theo đúng thứ tự này:

1. **Lấy dữ liệu từ đâu** — `FROM`
2. **Bỏ bớt dòng không cần** — `WHERE`
3. **Chọn/tính các cột muốn xem** — `SELECT`
4. **Sắp xếp rồi cắt lấy vài dòng đầu** — `ORDER BY` … `LIMIT`

Đây là **thứ tự máy chạy**, không phải thứ tự bạn viết. Bạn viết `SELECT` đầu tiên nhưng máy
làm nó gần cuối. Hiểu điều này giải thích được rất nhiều lỗi khó hiểu về sau.

### Sơ đồ

```text
   ┌───────────────────────────────────────────────────────────────────────────┐
   │  SELECT ho_ten, luong          ③ chọn & tính cột                          │
   │  FROM   nhan_vien              ① lấy bảng                                 │
   │  WHERE  luong >= 18            ② lọc dòng                                 │
   │  ORDER BY luong DESC           ④ sắp xếp                                  │
   │  LIMIT  3;                     ⑤ cắt lấy 3 dòng đầu                       │
   └───────────────────────────────────────────────────────────────────────────┘

   ① FROM nhan_vien          ② WHERE luong >= 18       ③ SELECT ho_ten, luong
   ┌──────┬─────┬──────┐     ┌──────┬─────┬──────┐     ┌──────┬──────┐
   │ An   │ 10  │  25  │ ──▶ │ An   │ 10  │  25  │ ──▶ │ An   │  25  │
   │ Binh │ 10  │  18  │     │ Binh │ 10  │  18  │     │ Binh │  18  │
   │ Chi  │ 10  │  18  │     │ Chi  │ 10  │  18  │     │ Chi  │  18  │
   │ Dung │ 20  │  22  │     │ Dung │ 20  │  22  │     │ Dung │  22  │
   │ Ha   │ 20  │  15  │  ✖  │ (bị loại: 15 < 18)  │   │      │      │
   │ Khoa │ 30  │  12  │  ✖  │ (bị loại)           │   │      │      │
   │ Linh │ 30  │ NULL │  ✖  │ (NULL >= 18 → không │   │      │      │
   │ Minh │NULL │  14  │  ✖  │  biết → bị loại!)   │   │      │      │
   └──────┴─────┴──────┘     └─────────────────────┘   └──────┴──────┘
        8 dòng                      4 dòng                 4 dòng, 2 cột
                                                              │
                        ⑤ LIMIT 3 ◀── ④ ORDER BY luong DESC ──┘
                        ┌──────┬──────┐   An 25 → Dung 22 → Binh 18 → Chi 18
                        │ An   │  25  │
                        │ Dung │  22  │   Chú ý: dòng Linh (NULL) bị loại ngay ở
                        │ Binh │  18  │   bước ②, dù ta chưa hề nói gì về NULL.
                        └──────┴──────┘   Xem mục 9 để hiểu vì sao.
```

### Ví dụ chạy được

```sql
-- 3.1  Xem cả bảng
SELECT * FROM nhan_vien;

-- 3.2  Chọn cột, tính toán, đặt tên lại bằng AS (alias)
SELECT ho_ten, luong, luong * 12 AS luong_nam FROM nhan_vien;

-- 3.3  Lọc dòng
SELECT ho_ten, phong_id, luong
FROM nhan_vien
WHERE phong_id = 10 AND luong >= 18;

-- 3.4  IN / BETWEEN / LIKE
SELECT ho_ten, phong_id, luong FROM nhan_vien WHERE phong_id IN (10, 30);
SELECT ho_ten, luong          FROM nhan_vien WHERE luong BETWEEN 15 AND 22;
SELECT ho_ten                 FROM nhan_vien WHERE ho_ten LIKE '%h%';

-- 3.5  Sắp xếp nhiều cột rồi cắt
SELECT ho_ten, phong_id, luong FROM nhan_vien ORDER BY luong DESC, ho_ten ASC LIMIT 3;

-- 3.6  Bỏ trùng
SELECT DISTINCT phong_id FROM nhan_vien ORDER BY phong_id;

-- 3.7  CASE WHEN = if/else của SQL
SELECT ho_ten, luong,
       CASE WHEN luong IS NULL THEN 'chua chot'
            WHEN luong >= 20   THEN 'cao'
            WHEN luong >= 15   THEN 'trung binh'
            ELSE 'thap'
       END AS muc_luong
FROM nhan_vien
ORDER BY luong DESC;
```

Kết quả thật của 3.5 và 3.7:

```text
  3.5                              3.7
  +--------+----------+-------+    +--------+-------+------------+
  | ho_ten | phong_id | luong |    | ho_ten | luong | muc_luong  |
  +--------+----------+-------+    +--------+-------+------------+
  | An     |       10 |    25 |    | An     |    25 | cao        |
  | Dung   |       20 |    22 |    | Dung   |    22 | cao        |
  | Binh   |       10 |    18 |    | Binh   |    18 | trung binh |
  +--------+----------+-------+    | Chi    |    18 | trung binh |
                                   | Ha     |    15 | trung binh |
                                   | Minh   |    14 | thap       |
                                   | Khoa   |    12 | thap       |
                                   | Linh   |  NULL | chua chot  |
                                   +--------+-------+------------+
```

### Bảng thứ tự thực thi (câu hỏi phỏng vấn ruột)

| Thứ tự máy chạy | Mệnh đề | Việc nó làm |
|---|---|---|
| 1 | `FROM` / `JOIN` | dựng bộ dòng ban đầu |
| 2 | `WHERE` | lọc **từng dòng** |
| 3 | `GROUP BY` | gom dòng thành nhóm |
| 4 | `HAVING` | lọc **từng nhóm** |
| 5 | `SELECT` | tính cột, gán alias, **window function chạy ở đây** |
| 6 | `DISTINCT` | bỏ dòng trùng |
| 7 | `ORDER BY` | sắp xếp (đã có alias nên dùng được) |
| 8 | `LIMIT` / `OFFSET` | cắt lấy phần cần |

Ba hệ quả rút ra được ngay, và cả ba đều là câu hỏi phỏng vấn:

* **Không dùng được alias trong `WHERE`** (alias sinh ra ở bước 5, `WHERE` chạy ở bước 2).
  PostgreSQL và MySQL báo lỗi. SQLite dễ dãi cho qua — đừng ỷ vào đó.
* **Không dùng được hàm gom nhóm trong `WHERE`** (`WHERE COUNT(*) > 2` sai) → phải dùng `HAVING`.
* **Không dùng được window function trong `WHERE`** → phải bọc thêm một lớp CTE (mục 8.4).

<details>
<summary><b>Tự kiểm tra 3.1</b> — <code>WHERE luong &lt;&gt; 18</code> có trả về Linh (lương NULL) không?</summary>

**Không.** `NULL <> 18` không cho ra "đúng", nó cho ra "không biết", và `WHERE` chỉ giữ những
dòng ra **đúng**. Muốn giữ Linh phải viết `WHERE luong <> 18 OR luong IS NULL`. Chi tiết ở mục 9.
</details>

<details>
<summary><b>Tự kiểm tra 3.2</b> — <code>ORDER BY luong DESC LIMIT 3</code> khác gì <code>LIMIT 3</code> rồi mới sắp xếp?</summary>

Khác hoàn toàn. `ORDER BY` chạy **trước** `LIMIT`: sắp xếp cả 8 dòng rồi mới lấy 3 dòng cao nhất
→ đúng ý "top 3". Nếu cắt 3 dòng trước rồi mới sắp thì chỉ được "3 dòng bất kỳ, có sắp xếp".
SQL luôn làm theo cách thứ nhất, nên `ORDER BY ... LIMIT n` chính là mẫu chuẩn để lấy top-N.
</details>

<details>
<summary><b>Tự kiểm tra 3.3</b> — Viết câu lấy tên và năm vào làm của người vào công ty năm 2023, mới nhất trước.</summary>

```sql
SELECT ho_ten, ngay_vao
FROM nhan_vien
WHERE ngay_vao >= '2023-01-01' AND ngay_vao < '2024-01-01'
ORDER BY ngay_vao DESC;
```

Kết quả: `Ha (2023-07-01)`, `Chi (2023-01-10)`.

Cách viết dạng khoảng như trên tốt hơn `WHERE substr(ngay_vao,1,4) = '2023'`, vì nó
**dùng được index** còn cách kia thì không (mục 10.4).
</details>

---

## 4. JOIN — nối bảng

### Nói bằng lời

Dữ liệu được cố tình chia ra nhiều bảng để khỏi lặp lại (tên phòng "Ky thuat" chỉ lưu **một**
chỗ, chứ không chép vào từng nhân viên). `JOIN` là động tác **ghép lại**: với mỗi dòng bảng
này, tìm dòng bảng kia thoả điều kiện `ON`, rồi dán hai dòng thành một dòng dài.

Chỉ có đúng **hai câu hỏi** cần trả lời khi chọn kiểu JOIN:

1. Cặp dòng **khớp nhau** thì ghép — điều này mọi kiểu JOIN đều làm.
2. Dòng **không khớp được với ai** thì sao? Vứt đi, hay giữ lại và điền NULL vào phần thiếu?

| Kiểu | Dòng trái không khớp | Dòng phải không khớp |
|---|---|---|
| `INNER JOIN` (viết tắt `JOIN`) | **vứt** | **vứt** |
| `LEFT JOIN` | **giữ**, phần phải = NULL | vứt |
| `RIGHT JOIN` | vứt | **giữ**, phần trái = NULL |
| `FULL OUTER JOIN` | **giữ** | **giữ** |
| `CROSS JOIN` | không có điều kiện — ghép mọi cặp | |

### Vì sao bài này không vẽ hình Venn

Hình Venn hai vòng tròn là cách dạy JOIN phổ biến nhất, và nó **sai về bản chất**:

* Venn mô tả phép toán trên **tập hợp phần tử giống nhau**. Còn JOIN ghép **hai loại dòng khác
  nhau** (nhân viên và phòng ban) thành **một loại dòng thứ ba** — không phải phép giao/hợp gì cả.
* Venn **không thể diễn tả việc nhân dòng**. Phòng 10 là *một* dòng, khớp với *ba* nhân viên,
  nên kết quả có *ba* dòng. Đây là hiện tượng quan trọng nhất của JOIN trong thực tế (nó làm
  `SUM`/`COUNT` sai bét), mà hình Venn thì hoàn toàn im lặng về nó.
* Venn khiến người ta tưởng `INNER JOIN` là "phần chung của hai bảng", dẫn đến câu trả lời sai
  kinh điển: *"INNER JOIN 8 nhân viên với 4 phòng thì ra ít hơn 8 dòng"* — trong khi thực tế
  có thể ra **nhiều hơn**.

Nên bài này vẽ **hai bảng thật với dữ liệu thật, và chỉ rõ dòng nào khớp dòng nào**.

### Sơ đồ: dòng nào khớp dòng nào

Để sơ đồ vừa mắt, lấy 4 trong 8 nhân viên (mỗi phòng một người, cộng Minh chưa có phòng):

```text
        BẢNG TRÁI: nhan_vien                    BẢNG PHẢI: phong_ban
     ┌───────┬────────┬──────────┐          ┌──────────┬────────────┐
     │ nv_id │ ho_ten │ phong_id │          │ phong_id │ ten_phong  │
     ├───────┼────────┼──────────┤          ├──────────┼────────────┤
     │   1   │ An     │    10    │          │    10    │ Ky thuat   │
     │   4   │ Dung   │    20    │          │    20    │ Kinh doanh │
     │   6   │ Khoa   │    30    │          │    30    │ Nhan su    │
     │   8   │ Minh   │   NULL   │          │    40    │ Nghien cuu │
     └───────┴────────┴──────────┘          └──────────┴────────────┘

                    ĐIỀU KIỆN:  ON nv.phong_id = pb.phong_id

     An   (phong_id 10) ──────────────▶ (10) Ky thuat        ✔ KHỚP
     Dung (phong_id 20) ──────────────▶ (20) Kinh doanh      ✔ KHỚP
     Khoa (phong_id 30) ──────────────▶ (30) Nhan su         ✔ KHỚP
     Minh (phong_id NULL) ─── ✖ ───▶ không khớp được ai
                                        (40) Nghien cuu      ✖ không ai trỏ tới

     Lưu ý: Minh không khớp KHÔNG PHẢI vì "NULL không có trong bảng phòng", mà vì
     NULL = NULL cũng không cho ra "đúng". NULL không bao giờ khớp với bất cứ gì.
```

Bây giờ bốn kiểu JOIN chỉ khác nhau ở chỗ **hai dòng thừa** (Minh và phòng 40) được xử lý ra sao:

```text
  ══ INNER JOIN ═══════════════════════   ══ LEFT JOIN ════════════════════════════
  giữ 3 cặp khớp, vứt cả hai dòng thừa    giữ hết bảng TRÁI, phải thiếu thì NULL
  +--------+------------+                 +--------+------------+
  | ho_ten | ten_phong  |                 | ho_ten | ten_phong  |
  +--------+------------+                 +--------+------------+
  | An     | Ky thuat   |                 | An     | Ky thuat   |
  | Dung   | Kinh doanh |                 | Dung   | Kinh doanh |
  | Khoa   | Nhan su    |                 | Khoa   | Nhan su    |
  +--------+------------+                 | Minh   | NULL       | ◀ giữ, điền NULL
   Minh mất, phòng 40 mất                 +--------+------------+
                                           phòng 40 vẫn mất

  ══ RIGHT JOIN ═══════════════════════   ══ FULL OUTER JOIN ══════════════════════
  giữ hết bảng PHẢI                       giữ hết cả hai bên
  +--------+------------+                 +--------+------------+
  | ho_ten | ten_phong  |                 | ho_ten | ten_phong  |
  +--------+------------+                 +--------+------------+
  | An     | Ky thuat   |                 | An     | Ky thuat   |
  | Dung   | Kinh doanh |                 | Dung   | Kinh doanh |
  | Khoa   | Nhan su    |                 | Khoa   | Nhan su    |
  | NULL   | Nghien cuu | ◀ giữ, NULL     | Minh   | NULL       | ◀ giữ
  +--------+------------+                 | NULL   | Nghien cuu | ◀ giữ
   Minh mất                               +--------+------------+
```

Chạy trên **cả 8 nhân viên** thì số dòng lần lượt là: `INNER` **7 dòng** (mất Minh),
`LEFT` **8 dòng**, `RIGHT` **8 dòng** (7 cặp + phòng 40), `FULL` **9 dòng** — đúng như
`demo_sql.py --demo 4` in ra.

### Ví dụ chạy được

```sql
-- 4.1  INNER JOIN → 7 dòng: Minh biến mất
SELECT nv.nv_id, nv.ho_ten, nv.phong_id, pb.ten_phong
FROM nhan_vien nv
JOIN phong_ban pb ON nv.phong_id = pb.phong_id
ORDER BY nv.nv_id;

-- 4.2  LEFT JOIN → 8 dòng: Minh ở lại với ten_phong = NULL
SELECT nv.nv_id, nv.ho_ten, nv.phong_id, pb.ten_phong
FROM nhan_vien nv
LEFT JOIN phong_ban pb ON nv.phong_id = pb.phong_id
ORDER BY nv.nv_id;

-- 4.3  ANTI-JOIN: phòng nào không có nhân viên?  (mẫu LEFT JOIN + IS NULL)
SELECT pb.phong_id, pb.ten_phong
FROM phong_ban pb
LEFT JOIN nhan_vien nv ON pb.phong_id = nv.phong_id
WHERE nv.nv_id IS NULL;
```

```text
  4.2 (LEFT JOIN)                          4.3 (ANTI-JOIN)
  +-------+--------+----------+------------+   +----------+------------+
  | nv_id | ho_ten | phong_id | ten_phong  |   | phong_id | ten_phong  |
  +-------+--------+----------+------------+   +----------+------------+
  |     1 | An     |       10 | Ky thuat   |   |       40 | Nghien cuu |
  |     2 | Binh   |       10 | Ky thuat   |   +----------+------------+
  |     3 | Chi    |       10 | Ky thuat   |
  |     4 | Dung   |       20 | Kinh doanh |   Đọc là: "LEFT JOIN giữ mọi phòng;
  |     5 | Ha     |       20 | Kinh doanh |    phòng nào không ghép được ai thì
  |     6 | Khoa   |       30 | Nhan su    |    cột nv.nv_id bị điền NULL; lọc
  |     7 | Linh   |       30 | Nhan su    |    đúng những dòng NULL đó ra."
  |     8 | Minh   |     NULL | NULL       |
  +-------+--------+----------+------------+
```

### SELF JOIN — bảng tự nối với chính nó

Sếp cũng là một nhân viên, nên `quan_ly_id` trỏ ngược vào chính bảng `nhan_vien`. Cách nghĩ:
tưởng tượng có **hai bản sao** của cùng một bảng, đặt hai tên khác nhau (`nv` và `sep`).

```text
    bản sao "nv" (vai nhân viên)          bản sao "sep" (vai quản lý)
    ┌───────┬────────┬────────────┐       ┌───────┬────────┐
    │ nv_id │ ho_ten │ quan_ly_id │       │ nv_id │ ho_ten │
    ├───────┼────────┼────────────┤       ├───────┼────────┤
    │   1   │ An     │    NULL    │──✖──▶ │   1   │ An     │
    │   2   │ Binh   │      1     │─────▶ │   2   │ Binh   │
    │   5   │ Ha     │      4     │──┐    │   4   │ Dung   │
    └───────┴────────┴────────────┘  └──▶ │   5   │ Ha     │
                                          └───────┴────────┘
        ON nv.quan_ly_id = sep.nv_id      An có quan_ly_id NULL → dùng LEFT JOIN
                                          để An không bị mất khỏi kết quả.
```

```sql
-- 4.5  Mỗi nhân viên kèm tên sếp
SELECT nv.ho_ten AS nhan_vien, sep.ho_ten AS quan_ly
FROM nhan_vien nv
LEFT JOIN nhan_vien sep ON nv.quan_ly_id = sep.nv_id
ORDER BY nv.nv_id;
```

```text
  +-----------+---------+
  | nhan_vien | quan_ly |
  +-----------+---------+
  | An        | NULL    |  ← sếp tổng, không có ai quản lý
  | Binh      | An      |
  | Chi       | An      |
  | Dung      | An      |
  | Ha        | Dung    |
  | Khoa      | An      |
  | Linh      | Khoa    |
  | Minh      | An      |
  +-----------+---------+
```

### JOIN nhân dòng — chỗ giết người thật sự

```text
   Một dòng bên trái khớp NHIỀU dòng bên phải → nó được NHÂN BẢN ra bấy nhiêu lần.

   phong_ban (1 dòng)              nhan_vien (3 dòng khớp)         kết quả: 3 DÒNG
   ┌──────────────┐                ┌──────┐                    ┌────────────┬──────┐
   │ 10 Ky thuat  │───┬──────────▶ │ An   │                    │ Ky thuat   │ An   │
   └──────────────┘   ├──────────▶ │ Binh │        ═════▶      │ Ky thuat   │ Binh │
                      └──────────▶ │ Chi  │                    │ Ky thuat   │ Chi  │
                                   └──────┘                    └────────────┴──────┘

   Hậu quả thực tế: nếu bảng phong_ban có cột "ngan_sach" và bạn viết SUM(pb.ngan_sach)
   sau khi JOIN, ngân sách của phòng 10 sẽ bị cộng BA LẦN. Đây là lỗi báo cáo sai số
   phổ biến nhất mà người mới mắc phải — và là lý do bài 10 cuối bài bắt dùng COUNT(DISTINCT).
```

Đo bằng số thật (ví dụ 4.6):

```text
  +--------------+------------------+------------------+
  | so_nhan_vien | so_dong_doanh_so | so_dong_sau_join |
  +--------------+------------------+------------------+
  |            8 |               12 |               12 |
  +--------------+------------------+------------------+

  8 nhân viên JOIN 12 dòng doanh số → 12 dòng, KHÔNG phải 8.
  Chỉ 3 người có doanh số, mỗi người 4 tháng, nên mỗi người xuất hiện 4 lần.
```

### Bẫy kinh điển: điều kiện lọc đặt ở `WHERE` hay ở `ON`?

Với `INNER JOIN` thì hai chỗ tương đương. Với `LEFT JOIN` thì **khác hẳn**:

```text
   ĐẶT Ở WHERE                              ĐẶT Ở ON
   ...LEFT JOIN nv ON pb.phong_id           ...LEFT JOIN nv ON pb.phong_id = nv.phong_id
                    = nv.phong_id                            AND nv.luong >= 18
   WHERE nv.luong >= 18

   ① LEFT JOIN giữ phòng 30, 40 với         ① Điều kiện tham gia LUÔN vào lúc ghép cặp
     nv.luong = NULL                        ② Phòng 30, 40 không ghép được ai
   ② WHERE kiểm tra NULL >= 18                 → vẫn được GIỮ với NULL (đúng tinh thần LEFT)
     → "không biết" → LOẠI
   ③ Kết quả: LEFT JOIN bị biến thành       ③ Kết quả: 6 dòng, đủ 4 phòng
     INNER JOIN. Chỉ còn 4 dòng!
```

```text
  WHERE nv.luong >= 18 (4 dòng)        ON ... AND nv.luong >= 18 (6 dòng)
  +------------+--------+              +------------+--------+
  | ten_phong  | ho_ten |              | ten_phong  | ho_ten |
  +------------+--------+              +------------+--------+
  | Ky thuat   | An     |              | Ky thuat   | An     |
  | Ky thuat   | Binh   |              | Ky thuat   | Binh   |
  | Ky thuat   | Chi    |              | Ky thuat   | Chi    |
  | Kinh doanh | Dung   |              | Kinh doanh | Dung   |
  +------------+--------+              | Nhan su    | NULL   | ◀ còn
   Nhân sự và Nghiên cứu MẤT           | Nghien cuu | NULL   | ◀ còn
                                       +------------+--------+
```

Câu thần chú để nhớ: **điều kiện về "ghép thế nào" đặt trong `ON`; điều kiện về "giữ dòng nào
của kết quả cuối" đặt trong `WHERE`.** Và: hễ thấy `WHERE` nhắc tới cột của bảng bên phải một
`LEFT JOIN` thì phải dừng lại kiểm tra ngay.

<details>
<summary><b>Tự kiểm tra 4.1</b> — <code>INNER JOIN</code> 8 nhân viên với 4 phòng ban, kết quả nhiều nhất có thể là bao nhiêu dòng? Ít nhất?</summary>

Nhiều nhất **32 dòng** (nếu điều kiện `ON` luôn đúng — chính là `CROSS JOIN`, 8 × 4).
Ít nhất **0 dòng** (không cặp nào khớp). Với dữ liệu thật của ta: **7 dòng**.

Ý cần nói khi phỏng vấn: kết quả JOIN **không bị chặn trên bởi số dòng của bảng lớn hơn** —
đó chính là điều hình Venn khiến người ta hiểu sai.
</details>

<details>
<summary><b>Tự kiểm tra 4.2</b> — Viết câu tìm nhân viên <b>chưa</b> được phân phòng nào.</summary>

```sql
SELECT nv_id, ho_ten FROM nhan_vien WHERE phong_id IS NULL;
```

→ Minh. Ở đây không cần JOIN vì thông tin đã nằm sẵn trong `nhan_vien`. Nhưng nếu câu hỏi là
"nhân viên trỏ tới phòng **không tồn tại**" (dữ liệu bẩn) thì mới cần anti-join:

```sql
SELECT nv.ho_ten
FROM nhan_vien nv
LEFT JOIN phong_ban pb ON nv.phong_id = pb.phong_id
WHERE nv.phong_id IS NOT NULL AND pb.phong_id IS NULL;
```
</details>

Đọc câu SQL này rồi trả lời câu hỏi bên dưới:

```sql
SELECT pb.ten_phong, COUNT(nv.nv_id) AS n
FROM phong_ban pb LEFT JOIN nhan_vien nv ON pb.phong_id = nv.phong_id
WHERE nv.luong > 10
GROUP BY pb.ten_phong;
```

<details>
<summary><b>Tự kiểm tra 4.3</b> — Câu trên ra mấy dòng, phòng nào biến mất, vì sao?</summary>

**3 dòng** — phòng Nghiên cứu biến mất:

```text
  +------------+---+
  | ten_phong  | n |
  +------------+---+
  | Kinh doanh | 2 |
  | Ky thuat   | 3 |
  | Nhan su    | 1 |   ◀ chỉ còn Khoa; Linh bị loại vì lương NULL
  +------------+---+
```

Vì `WHERE nv.luong > 10` chạy **sau** khi LEFT JOIN đã điền NULL cho phòng Nghiên cứu, và
`NULL > 10` không đúng nên dòng đó bị loại → LEFT JOIN thoái hoá thành INNER JOIN.

Sửa: chuyển điều kiện vào `ON` (khi đó đủ 4 phòng, Nghiên cứu = 0):

```sql
SELECT pb.ten_phong, COUNT(nv.nv_id) AS n
FROM phong_ban pb LEFT JOIN nhan_vien nv ON pb.phong_id = nv.phong_id AND nv.luong > 10
GROUP BY pb.ten_phong;
```
</details>

---

## 5. GROUP BY và HAVING

### Nói bằng lời

`GROUP BY` là động tác **chia dòng vào các xô**, rồi **mỗi xô bóp lại thành đúng một dòng**.
Muốn bóp thì phải nói rõ bóp kiểu gì — đó là các **hàm gom nhóm** (aggregate):
`COUNT`, `SUM`, `AVG`, `MIN`, `MAX`.

Nguyên tắc vàng: sau khi `GROUP BY`, mỗi cột trong `SELECT` **hoặc** là cột đã dùng để chia
xô, **hoặc** phải nằm trong một hàm gom nhóm. Không có lựa chọn thứ ba (SQLite và MySQL cũ
cho qua, nhưng đó là sự dễ dãi — PostgreSQL báo lỗi thẳng).

### Sơ đồ

```text
   BẢNG GỐC (8 dòng)          ① CHIA XÔ theo phong_id          ② BÓP mỗi xô
   ┌──────┬──────┬──────┐
   │ An   │  10  │  25  │     ┌─ xô phong_id = 10 ──────┐
   │ Binh │  10  │  18  │     │  An 25, Binh 18, Chi 18 │ ─▶ COUNT=3  SUM=61  AVG=20.3
   │ Chi  │  10  │  18  │     └─────────────────────────┘
   │ Dung │  20  │  22  │     ┌─ xô phong_id = 20 ──────┐
   │ Ha   │  20  │  15  │ ──▶ │  Dung 22, Ha 15         │ ─▶ COUNT=2  SUM=37  AVG=18.5
   │ Khoa │  30  │  12  │     └─────────────────────────┘
   │ Linh │  30  │ NULL │     ┌─ xô phong_id = 30 ──────┐
   │ Minh │ NULL │  14  │     │  Khoa 12, Linh NULL     │ ─▶ COUNT=2  SUM=12  AVG=12
   └──────┴──────┴──────┘     └─────────────────────────┘        ▲
                              ┌─ xô phong_id = NULL ────┐        │ AVG chỉ chia cho 1,
                              │  Minh 14                │ ─▶ ... │ vì lương Linh là NULL
                              └─────────────────────────┘        │ nên KHÔNG được đếm!
                              (mọi NULL gom chung MỘT xô)

                    Kết quả: 8 dòng ─────────────────▶ 4 dòng
```

`WHERE` và `HAVING` khác nhau ở chỗ chúng đứng ở đâu trên dây chuyền này:

```text
   dòng thô ──▶ [ WHERE ] ──▶ chia xô ──▶ bóp xô ──▶ [ HAVING ] ──▶ ORDER BY ──▶ kết quả
                   ▲                                     ▲
                   │                                     │
        lọc TỪNG DÒNG, trước khi gom.          lọc TỪNG NHÓM, sau khi đã có
        Không được nhắc tới COUNT/SUM          COUNT/SUM. Đây là chỗ duy nhất
        vì lúc này chưa gom nhóm.              viết được COUNT(*) >= 2.
```

### Ví dụ chạy được

```sql
-- 5.1  Gom nhóm cả bảng (không GROUP BY = một xô duy nhất)
SELECT COUNT(*)             AS so_dong,
       COUNT(luong)         AS co_luong,
       SUM(luong)           AS tong_luong,
       ROUND(AVG(luong), 2) AS luong_tb,
       MIN(luong)           AS thap_nhat,
       MAX(luong)           AS cao_nhat
FROM nhan_vien;

-- 5.2  Gom theo phòng
SELECT phong_id, COUNT(*) AS so_nv, ROUND(AVG(luong), 1) AS luong_tb
FROM nhan_vien GROUP BY phong_id ORDER BY phong_id;

-- 5.3  Gom + JOIN để lấy tên phòng, giữ cả phòng rỗng
SELECT pb.ten_phong, COUNT(nv.nv_id) AS so_nv, COALESCE(SUM(nv.luong), 0) AS tong_luong
FROM phong_ban pb
LEFT JOIN nhan_vien nv ON pb.phong_id = nv.phong_id
GROUP BY pb.phong_id, pb.ten_phong
ORDER BY so_nv DESC;

-- 5.4  HAVING: chỉ giữ phòng từ 2 người
SELECT phong_id, COUNT(*) AS so_nv, ROUND(AVG(luong), 1) AS luong_tb
FROM nhan_vien GROUP BY phong_id HAVING COUNT(*) >= 2 ORDER BY so_nv DESC;
```

```text
  5.1                                                    5.3
  +---------+----------+------------+----------+         +------------+-------+------------+
  | so_dong | co_luong | tong_luong | luong_tb |         | ten_phong  | so_nv | tong_luong |
  +---------+----------+------------+----------+         +------------+-------+------------+
  |       8 |        7 |        124 |    17.71 |         | Ky thuat   |     3 |         61 |
  +---------+----------+------------+----------+         | Kinh doanh |     2 |         37 |
     ▲          ▲                                        | Nhan su    |     2 |         12 |
     │          └── chỉ đếm dòng CÓ giá trị              | Nghien cuu |     0 |          0 | ◀ giữ được
     └── đếm mọi dòng, kể cả NULL                        +------------+-------+------------+
```

Ba cái bẫy trong mục này, cả ba đều là câu hỏi phỏng vấn:

**Bẫy 1 — `COUNT(*)` với `COUNT(cot)`.** `COUNT(*)` đếm **dòng**; `COUNT(cot)` đếm **giá trị
không NULL** của cột đó. Trong 5.3 nếu viết `COUNT(*)` thì phòng Nghiên cứu ra **1** (đếm cái
dòng NULL do LEFT JOIN sinh ra) thay vì **0**. Quy tắc: **sau `LEFT JOIN` thì luôn `COUNT` một
cột của bảng bên phải, không bao giờ `COUNT(*)`.**

**Bẫy 2 — `AVG` bỏ qua NULL.** Lương trung bình = 124/7 = 17.71, không phải 124/8 = 15.5.
Không sai — nhưng bạn phải **biết** và nói ra được là mình đang tính trên 7 người.

**Bẫy 3 — cột "trần" ngoài `GROUP BY`.** `SELECT phong_id, ho_ten, MAX(luong) ... GROUP BY phong_id`
chạy được trên SQLite nhưng **không đảm bảo** `ho_ten` là người có lương cao nhất ở hệ khác.
Muốn chắc chắn đúng → dùng window function (mục 8.4).

<details>
<summary><b>Tự kiểm tra 5.1</b> — <code>WHERE COUNT(*) > 1</code> sai ở đâu, sửa thế nào?</summary>

`WHERE` chạy **trước** `GROUP BY`, lúc đó chưa có nhóm nào để mà đếm → lỗi cú pháp/ngữ nghĩa.
Điều kiện trên kết quả gom nhóm phải để trong `HAVING`:

```sql
SELECT phong_id, COUNT(*) FROM nhan_vien GROUP BY phong_id HAVING COUNT(*) > 1;
```
</details>

<details>
<summary><b>Tự kiểm tra 5.2</b> — Đếm số nhân viên vào công ty mỗi năm, chỉ lấy năm có từ 2 người.</summary>

```sql
SELECT substr(ngay_vao, 1, 4) AS nam_vao, COUNT(*) AS so_nguoi
FROM nhan_vien
GROUP BY substr(ngay_vao, 1, 4)
HAVING COUNT(*) >= 2
ORDER BY nam_vao;
```

→ `2023: 2` và `2024: 2`. (Gom nhóm theo **biểu thức** hoàn toàn hợp lệ, không cần cột có sẵn.)
</details>

Đọc câu SQL này rồi trả lời câu hỏi bên dưới:

```sql
SELECT pb.ten_phong, COUNT(*) AS n
FROM phong_ban pb LEFT JOIN nhan_vien nv ON pb.phong_id = nv.phong_id
GROUP BY pb.ten_phong;
```

<details>
<summary><b>Tự kiểm tra 5.3</b> — Câu trên in ra mấy dòng, và dòng phòng Nghiên cứu ghi số mấy?</summary>

**4 dòng**, và Nghiên cứu ghi **1** — con số sai:

```text
  +------------+---+
  | ten_phong  | n |
  +------------+---+
  | Kinh doanh | 2 |
  | Ky thuat   | 3 |
  | Nghien cuu | 1 |   ◀ phòng không có ai mà vẫn đếm ra 1
  | Nhan su    | 2 |
  +------------+---+
```

Vì `LEFT JOIN` tạo ra một dòng "Nghiên cứu + toàn NULL", và `COUNT(*)` đếm **dòng** nên vẫn
đếm dòng đó. Đổi thành `COUNT(nv.nv_id)` — đếm **giá trị không NULL** — mới ra 0.
</details>

---

## 6. Subquery — truy vấn lồng

### Nói bằng lời

Subquery là **một câu SELECT nằm bên trong một câu SELECT khác**, dùng khi câu trả lời cần
**hai bước**: bước một tính ra cái gì đó, bước hai dùng kết quả ấy để lọc/so sánh.

Ba chỗ đặt subquery, và mỗi chỗ nó đóng một vai khác nhau:

```text
   ┌── ① trong WHERE ─ vai "giá trị để so sánh" hoặc "danh sách để đối chiếu"
   │
   │   SELECT ho_ten FROM nhan_vien
   │   WHERE luong > ( SELECT AVG(luong) FROM nhan_vien );
   │                  └────────── trả về MỘT số: 17.71 ────┘
   │
   ├── ② trong FROM ─ vai "một bảng tạm"
   │
   │   SELECT t.phong_id FROM ( SELECT phong_id, AVG(luong) AS tb
   │                            FROM nhan_vien GROUP BY phong_id ) AS t
   │   WHERE t.tb > 15;      └──────── trả về một BẢNG ────────┘
   │
   └── ③ trong SELECT ─ vai "thêm một cột tính toán"

       SELECT ho_ten, ( SELECT COUNT(*) FROM doanh_so ds
                        WHERE ds.nv_id = nv.nv_id ) AS so_thang
       FROM nhan_vien nv;
```

Phân biệt hai loại — đây là câu hỏi phỏng vấn thường gặp:

```text
  ĐỘC LẬP (uncorrelated)                    TƯƠNG QUAN (correlated)
  Subquery không nhắc gì tới query ngoài.   Subquery có nhắc tới bảng của query ngoài.
  → Chạy MỘT lần, lấy kết quả, xong.        → Chạy LẠI cho TỪNG DÒNG của query ngoài.

  WHERE luong > (SELECT AVG(luong)          WHERE nv.luong > (SELECT AVG(n2.luong)
                 FROM nhan_vien)                              FROM nhan_vien n2
                                                              WHERE n2.phong_id = nv.phong_id)
  ┌──────────────────────┐                                          ▲──────────────┘
  │ tính 1 lần → 17.71   │                                     tham chiếu ra ngoài
  └──────────┬───────────┘
             ▼                             dòng An   ─▶ tính AVG phòng 10 = 20.3 ─▶ 25 > 20.3 ✔
  An 25 > 17.71 ✔                          dòng Binh ─▶ tính AVG phòng 10 = 20.3 ─▶ 18 > 20.3 ✖
  Binh 18 > 17.71 ✔                        dòng Dung ─▶ tính AVG phòng 20 = 18.5 ─▶ 22 > 18.5 ✔
  Ha 15 > 17.71 ✖                          ...  (8 dòng → 8 lần tính!)
  ...
                                           Đúng nhưng CHẬM khi bảng lớn.
                                           → thường viết lại bằng window function (mục 8.2).
```

### Ví dụ chạy được

```sql
-- 6.1  Ai lương trên trung bình công ty?
SELECT ho_ten, luong FROM nhan_vien
WHERE luong > (SELECT AVG(luong) FROM nhan_vien) ORDER BY luong DESC;
-- → An 25, Dung 22, Binh 18, Chi 18   (trung bình là 17.71)

-- 6.6  EXISTS: ai có ít nhất một tháng doanh thu > 100?
SELECT nv.ho_ten FROM nhan_vien nv
WHERE EXISTS (SELECT 1 FROM doanh_so ds WHERE ds.nv_id = nv.nv_id AND ds.doanh_thu > 100);
-- → Binh, Dung, Ha

-- 6.7  Correlated: ai lương cao hơn trung bình CỦA PHÒNG MÌNH?
SELECT nv.ho_ten, nv.phong_id, nv.luong FROM nhan_vien nv
WHERE nv.luong > (SELECT AVG(n2.luong) FROM nhan_vien n2 WHERE n2.phong_id = nv.phong_id);
-- → An (10), Dung (20)

-- 6.9  Lương cao thứ hai — câu kinh điển
SELECT MAX(luong) AS luong_thu_2 FROM nhan_vien
WHERE luong < (SELECT MAX(luong) FROM nhan_vien);
-- → 22
```

### Bẫy `NOT IN` gặp NULL — câu hỏi phỏng vấn ruột

```sql
-- 6.3  Tìm phòng không có nhân viên nào. Trông có vẻ đúng...
SELECT phong_id, ten_phong FROM phong_ban
WHERE phong_id NOT IN (SELECT phong_id FROM nhan_vien);
```

```text
  +----------+-----------+
  | phong_id | ten_phong |
  +----------+-----------+
  +----------+-----------+
  (0 dòng)          ◀── KHÔNG RA GÌ CẢ. Đáng lẽ phải ra phòng 40!
```

Vì sao:

```text
   Subquery trả về danh sách: [10, 10, 10, 20, 20, 30, 30, NULL]
                                                            └── của Minh!

   SQL dịch  x NOT IN (10, 20, 30, NULL)  thành:
             x <> 10  AND  x <> 20  AND  x <> 30  AND  x <> NULL
                                                       └────┬────┘
                                                            │
                              cái này LUÔN ra "không biết", không bao giờ ra "đúng"
                                                            │
             ĐÚNG AND ĐÚNG AND ĐÚNG AND KHÔNG-BIẾT  =  KHÔNG BIẾT  ──▶ WHERE loại dòng
                                                                        ▼
                                          → mọi dòng đều bị loại → 0 dòng, mãi mãi.
```

Hai cách chữa (cả hai đều trả về đúng phòng 40):

```sql
-- Cách 1: chặn NULL ngay trong subquery
SELECT phong_id, ten_phong FROM phong_ban
WHERE phong_id NOT IN (SELECT phong_id FROM nhan_vien WHERE phong_id IS NOT NULL);

-- Cách 2 (nên dùng): NOT EXISTS — không dính bẫy NULL, và thường nhanh hơn
SELECT pb.phong_id, pb.ten_phong FROM phong_ban pb
WHERE NOT EXISTS (SELECT 1 FROM nhan_vien nv WHERE nv.phong_id = pb.phong_id);
```

> **Cách trả lời ăn điểm:** *"`NOT IN` mà danh sách bên trong có NULL thì kết quả luôn rỗng,
> vì `x <> NULL` cho ra UNKNOWN chứ không phải TRUE. Nên em mặc định dùng `NOT EXISTS`, hoặc
> `NOT IN` kèm `IS NOT NULL`."* — Chú ý: `IN` (không có `NOT`) thì **không** dính bẫy này,
> vì chỉ cần một so sánh ra TRUE là đủ.

<details>
<summary><b>Tự kiểm tra 6.1</b> — <code>IN</code> và <code>EXISTS</code> khác nhau chỗ nào?</summary>

* `IN` so sánh một giá trị với một **danh sách giá trị** do subquery trả về.
* `EXISTS` chỉ hỏi *"subquery có ra được dòng nào không?"* — trả về đúng/sai, nên `SELECT 1`
  hay `SELECT *` bên trong đều như nhau.
* Về ngữ nghĩa, `EXISTS` an toàn với NULL còn `NOT IN` thì không.
* Về hiệu năng, các bộ tối ưu hiện đại thường biến cả hai về cùng một kế hoạch; nhưng
  `EXISTS` có thể dừng ngay khi tìm thấy dòng đầu tiên.
</details>

<details>
<summary><b>Tự kiểm tra 6.2</b> — Viết câu tìm nhân viên có lương bằng đúng lương cao nhất phòng mình.</summary>

```sql
SELECT nv.ho_ten, nv.phong_id, nv.luong
FROM nhan_vien nv
WHERE nv.luong = (SELECT MAX(n2.luong) FROM nhan_vien n2 WHERE n2.phong_id = nv.phong_id);
```

→ An (25, phòng 10), Dung (22, phòng 20), Khoa (12, phòng 30), Minh (14, phòng NULL — vì
`n2.phong_id = nv.phong_id` với cả hai đều NULL thì **không khớp**, subquery ra NULL… nên thực
tế Minh **không** xuất hiện). Đây đúng là chỗ NULL cắn thêm lần nữa — mục 9.
</details>

---

## 7. CTE — mệnh đề WITH

### Nói bằng lời

CTE (Common Table Expression) là cách **đặt tên cho một bước trung gian**. Về kết quả, nó
tương đương subquery trong `FROM`; về khả năng đọc, nó hơn hẳn: query đọc từ **trên xuống**
như đọc một đoạn văn, thay vì bóc ngoặc từ trong ra ngoài.

```text
   VIẾT KIỂU SUBQUERY LỒNG                     VIẾT KIỂU CTE
   (đọc từ trong ra, ngược hướng suy nghĩ)     (đọc từ trên xuống, thuận hướng suy nghĩ)

   SELECT ...                                  WITH buoc_1 AS (
   FROM (SELECT ...                                SELECT ...   ← bước 1: gom doanh số
         FROM (SELECT ...                      ),
               FROM bang                       buoc_2 AS (
               WHERE ...) t1                       SELECT ...   ← bước 2: nối thêm tên
         GROUP BY ...) t2                           FROM buoc_1 ...
   WHERE ...;                                  )
                                               SELECT ...       ← bước 3: kết quả cuối
        ▲                                          FROM buoc_2
        └── phải đọc ngược từ trong ra           ORDER BY ...;
```

```text
   Dây chuyền dữ liệu:

   doanh_so ──▶ ┌──────────────┐ ──▶ ┌──────────────┐ ──▶ ┌─────────────┐ ──▶ kết quả
                │  ds_theo_nv  │     │    co_ten    │     │ SELECT cuối │
                │ gom SUM theo │     │ JOIN thêm    │     │ sắp xếp,    │
                │ từng nv_id   │     │ ho_ten,phong │     │ lọc, đổi tên│
                └──────────────┘     └──────────────┘     └─────────────┘
                   (3 dòng)             (3 dòng)             (3 dòng)
```

### Ví dụ chạy được

```sql
-- 7.2  Hai CTE nối tiếp nhau
WITH ds_theo_nv AS (
    SELECT nv_id, SUM(doanh_thu) AS tong_ds
    FROM doanh_so
    GROUP BY nv_id
),
co_ten AS (
    SELECT nv.ho_ten, nv.phong_id, d.tong_ds
    FROM ds_theo_nv d
    JOIN nhan_vien nv ON nv.nv_id = d.nv_id
)
SELECT ho_ten, phong_id, tong_ds FROM co_ten ORDER BY tong_ds DESC;
```

```text
  +--------+----------+---------+
  | ho_ten | phong_id | tong_ds |
  +--------+----------+---------+
  | Dung   |       20 |     560 |
  | Ha     |       20 |     415 |
  | Binh   |       10 |     370 |
  +--------+----------+---------+
```

### CTE đệ quy — đi hết một cái cây

Dùng khi dữ liệu **tự trỏ vào chính nó**: cây quản lý, cây danh mục, chuỗi chuyến bay nối
chuyến. Cấu trúc luôn gồm đúng hai phần, nối bằng `UNION ALL`:

```text
   WITH RECURSIVE cay AS (

       SELECT ... WHERE quan_ly_id IS NULL        ◀── ĐIỂM XUẤT PHÁT (anchor)
                                                      chạy MỘT lần
       UNION ALL

       SELECT ... FROM nhan_vien nv               ◀── BƯỚC LẶP (recursive step)
       JOIN cay ON nv.quan_ly_id = cay.nv_id           lặp tới khi không ra thêm dòng nào
   )
   SELECT * FROM cay;

   ─────────────── máy chạy như sau ───────────────

   Vòng 0 (anchor) : An                                        cấp 1
                       │
   Vòng 1          : tìm ai có sếp = An  →  Binh, Chi, Dung, Khoa, Minh    cấp 2
                                                    │
   Vòng 2          : tìm ai có sếp ∈ {Binh,Chi,Dung,Khoa,Minh} → Ha, Linh  cấp 3
                                                    │
   Vòng 3          : tìm ai có sếp ∈ {Ha, Linh}  →  (không có) → DỪNG
```

```sql
WITH RECURSIVE cay AS (
    SELECT nv_id, ho_ten, quan_ly_id, 1 AS cap, ho_ten AS duong_di
    FROM nhan_vien
    WHERE quan_ly_id IS NULL
    UNION ALL
    SELECT nv.nv_id, nv.ho_ten, nv.quan_ly_id, cay.cap + 1, cay.duong_di || ' > ' || nv.ho_ten
    FROM nhan_vien nv
    JOIN cay ON nv.quan_ly_id = cay.nv_id
)
SELECT cap, ho_ten, duong_di FROM cay ORDER BY duong_di;
```

```text
  +-----+--------+------------------+
  | cap | ho_ten | duong_di         |          An
  +-----+--------+------------------+          ├── Binh
  |   1 | An     | An               |          ├── Chi
  |   2 | Binh   | An > Binh        |          ├── Dung
  |   2 | Chi    | An > Chi         |          │    └── Ha
  |   2 | Dung   | An > Dung        |          ├── Khoa
  |   3 | Ha     | An > Dung > Ha   |          │    └── Linh
  |   2 | Khoa   | An > Khoa        |          └── Minh
  |   3 | Linh   | An > Khoa > Linh |
  |   2 | Minh   | An > Minh        |
  +-----+--------+------------------+
```

> ⚠️ Nếu dữ liệu có vòng lặp (A là sếp của B, B là sếp của A) thì CTE đệ quy chạy **vô tận**.
> Cách chặn: mang theo cột `duong_di` rồi thêm điều kiện `WHERE instr(duong_di, nv.ho_ten) = 0`,
> hoặc giới hạn `WHERE cap < 10`.

<details>
<summary><b>Tự kiểm tra 7.1</b> — CTE có làm query chạy nhanh hơn subquery không?</summary>

**Không, không tự nhiên nhanh hơn.** CTE chủ yếu để **dễ đọc**. Về hiệu năng:

* SQLite/PostgreSQL hiện đại thường "gộp" CTE vào query chính (inline) → tương đương subquery.
* PostgreSQL ≤ 11 luôn **vật chất hoá** CTE (tính xong lưu bảng tạm), có thể **chậm hơn**;
  từ PG 12 mới inline, và có từ khoá `MATERIALIZED` / `NOT MATERIALIZED` để ép.
* Nếu một CTE được dùng lại **nhiều lần** trong query thì vật chất hoá lại có lợi.

Trả lời an toàn khi phỏng vấn: *"CTE là chuyện dễ đọc, không phải chuyện tốc độ; tuỳ hệ và
tuỳ phiên bản mà nó được inline hay materialize."*
</details>

<details>
<summary><b>Tự kiểm tra 7.2</b> — Dùng CTE đệ quy sinh 5 dòng chứa số 1..5.</summary>

```sql
WITH RECURSIVE dem(n) AS (
    SELECT 1
    UNION ALL
    SELECT n + 1 FROM dem WHERE n < 5
)
SELECT n FROM dem;
```

Mẹo này rất hay dùng để **sinh dữ liệu giả** đo hiệu năng — chính là cách `--index` tạo
200.000 dòng trong `demo_sql.py`.
</details>

---

## 8. Window function

### Nói bằng lời

`GROUP BY` **bóp** nhiều dòng thành một. Nhưng rất nhiều câu hỏi thực tế cần **giữ nguyên
từng dòng** mà vẫn nhìn được con số của cả nhóm:

* "lương của mỗi người, kèm trung bình phòng của họ" — vẫn phải thấy đủ 8 người;
* "doanh thu tháng này so với tháng trước" — cần nhìn dòng bên cạnh;
* "top 2 người lương cao nhất mỗi phòng" — cần đánh số thứ tự trong từng nhóm.

Đó chính là **window function**: nó tính trên một "**cửa sổ**" các dòng liên quan tới dòng
hiện tại, rồi **gắn kết quả vào chính dòng đó**. Không dòng nào bị mất.

### Sơ đồ: GROUP BY và WINDOW khác nhau ở đâu

```text
   ══ GROUP BY (bóp lại) ══════════        ══ WINDOW / OVER (giữ nguyên) ═════════════
   SELECT phong_id, AVG(luong)             SELECT ho_ten, phong_id, luong,
   FROM nhan_vien GROUP BY phong_id;              AVG(luong) OVER (PARTITION BY phong_id)
                                           FROM nhan_vien;

   An   10  25 ┐                           An   10  25 ──▶ An   10  25 │ 20.3
   Binh 10  18 ├─▶ 10 │ 20.3               Binh 10  18 ──▶ Binh 10  18 │ 20.3
   Chi  10  18 ┘                           Chi  10  18 ──▶ Chi  10  18 │ 20.3
   Dung 20  22 ┐                           Dung 20  22 ──▶ Dung 20  22 │ 18.5
   Ha   20  15 ┘─▶ 20 │ 18.5               Ha   20  15 ──▶ Ha   20  15 │ 18.5
   Khoa 30  12 ┐                           Khoa 30  12 ──▶ Khoa 30  12 │ 12
   Linh 30 NULL┘─▶ 30 │ 12                 Linh 30 NULL──▶ Linh 30 NULL│ 12

        8 dòng ─▶ 4 dòng                        8 dòng ─▶ 8 dòng, thêm 1 cột
        MẤT tên từng người                      GIỮ tên, VẪN có số của nhóm
```

### Cú pháp: ba mảnh trong ngoặc `OVER (...)`

```text
   HAM()  OVER ( PARTITION BY ...   ORDER BY ...   ROWS BETWEEN ... )
     │              │                   │              │
     │              │                   │              └─ ③ KHUNG: tính trên mấy dòng
     │              │                   │                    quanh dòng hiện tại?
     │              │                   │                    (mặc định: từ đầu nhóm → dòng này)
     │              │                   └─ ② THỨ TỰ trong mỗi nhóm
     │              │                        (bắt buộc với ROW_NUMBER, RANK, LAG, LEAD)
     │              └─ ① CHIA NHÓM — giống GROUP BY nhưng không bóp dòng
     │                   (bỏ trống = cả bảng là một nhóm)
     └─ hàm: SUM/AVG/COUNT/MIN/MAX, hoặc ROW_NUMBER/RANK/DENSE_RANK, hoặc LAG/LEAD

   Ví dụ đọc thành lời:
   SUM(doanh_thu) OVER (PARTITION BY nv_id ORDER BY thang
                        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
   = "cộng dồn doanh thu, tính riêng cho từng nhân viên, theo thứ tự tháng,
      từ tháng đầu tiên cho tới tháng đang đứng" → doanh thu luỹ kế.
```

### ROW_NUMBER / RANK / DENSE_RANK — khác nhau đúng ở chỗ hoà điểm

Tháng 2025-03, Binh và Dung cùng doanh thu 90:

```text
   doanh_thu    ROW_NUMBER()      RANK()            DENSE_RANK()
   ─────────    ────────────      ──────            ────────────
   Ha    130         1               1                  1
   Binh   90         2               2  ┐               2  ┐
   Dung   90         3               2  ┘ bằng nhau     2  ┘ bằng nhau
   (nếu có dòng                      ↑                  ↑
    tiếp theo)       4               4                  3
                     ▲               ▲                  ▲
        đánh số cứng 1,2,3   hoà thì cùng hạng,   hoà thì cùng hạng,
        kể cả bằng điểm      rồi NHẢY CÓC        KHÔNG nhảy cóc
        (chọn ai trước là    (2,2,4 — giống       (2,2,3 — giống
         tuỳ ý, không ổn định)  huy chương)         "hạng nhì có hai người")
```

Kết quả thật:

```text
  +--------+-----------+----+-----+------+
  | ho_ten | doanh_thu | rn | rnk | drnk |
  +--------+-----------+----+-----+------+
  | Ha     |       130 |  1 |   1 |    1 |
  | Binh   |        90 |  2 |   2 |    2 |
  | Dung   |        90 |  3 |   2 |    2 |
  +--------+-----------+----+-----+------+
```

**Chọn cái nào?** — "lấy đúng 1 dòng cho mỗi nhóm, không cần biết hoà" → `ROW_NUMBER`.
"Top N nhưng hoà thì lấy hết" → `RANK` hoặc `DENSE_RANK`. Khi phỏng vấn, **hỏi lại** người
phỏng vấn *"nếu bằng điểm thì lấy hết hay lấy đúng N?"* — hỏi được câu này là ăn điểm.

### LAG và LEAD — nhìn sang dòng trước/dòng sau

```text
   PARTITION BY nv_id ORDER BY thang        (dữ liệu của Dung)

   thang     doanh_thu    LAG(doanh_thu)   LEAD(doanh_thu)
   ───────   ─────────    ──────────────   ───────────────
   2025-01      120  ◀─┐      NULL   ← không có tháng trước
   2025-02      150  ◀─┼──────  120         ...
   2025-03       90  ◀─┼──────  150
   2025-04      200    └──────   90         NULL  ← không có tháng sau
                  │
                  └── LAG = "lấy giá trị của dòng LÙI LẠI 1 bước trong cùng nhóm"
                      LEAD = ngược lại, dòng TIẾN TỚI 1 bước

   ⚠ PARTITION BY nv_id là bắt buộc — thiếu nó thì tháng 01 của người này
     sẽ đi so với tháng 04 của người khác.
```

### Khung `ROWS` — luỹ kế và trung bình trượt

```text
   ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW   → luỹ kế (cộng dồn từ đầu)

   Dung:  01(120)   02(150)   03(90)   04(200)
          ├─┐       ├───┐     ├─────┐  ├───────┐
          120       270       360      560          ← luy_ke

   ROWS BETWEEN 1 PRECEDING AND CURRENT ROW          → trung bình 2 tháng gần nhất

          [120]     [120,150]  [150,90]  [90,200]
          120       135        120       145         ← tb_2_thang
```

### Ví dụ chạy được

```sql
-- 8.4  MẪU TOP-N MỖI NHÓM (câu phỏng vấn phổ biến nhất của window function)
WITH xep_hang AS (
    SELECT ho_ten, phong_id, luong,
           ROW_NUMBER() OVER (PARTITION BY phong_id ORDER BY luong DESC) AS thu_tu
    FROM nhan_vien
    WHERE phong_id IS NOT NULL
)
SELECT phong_id, ho_ten, luong, thu_tu FROM xep_hang
WHERE thu_tu <= 2 ORDER BY phong_id, thu_tu;

-- 8.5  Chênh lệch so với tháng trước
SELECT nv.ho_ten, ds.thang, ds.doanh_thu,
       LAG(ds.doanh_thu) OVER (PARTITION BY ds.nv_id ORDER BY ds.thang) AS thang_truoc,
       ds.doanh_thu - LAG(ds.doanh_thu) OVER (PARTITION BY ds.nv_id ORDER BY ds.thang) AS chenh
FROM doanh_so ds JOIN nhan_vien nv ON nv.nv_id = ds.nv_id
ORDER BY nv.ho_ten, ds.thang;

-- 8.7  Luỹ kế + trung bình trượt
SELECT nv.ho_ten, ds.thang, ds.doanh_thu,
       SUM(ds.doanh_thu) OVER (PARTITION BY ds.nv_id ORDER BY ds.thang
                               ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS luy_ke
FROM doanh_so ds JOIN nhan_vien nv ON nv.nv_id = ds.nv_id
WHERE nv.ho_ten = 'Dung' ORDER BY ds.thang;
```

```text
  8.4                                     8.5 (trích phần của Dung)
  +----------+--------+-------+--------+  +--------+---------+-----------+-------------+-------+
  | phong_id | ho_ten | luong | thu_tu |  | ho_ten | thang   | doanh_thu | thang_truoc | chenh |
  +----------+--------+-------+--------+  +--------+---------+-----------+-------------+-------+
  |       10 | An     |    25 |      1 |  | Dung   | 2025-01 |       120 |        NULL |  NULL |
  |       10 | Binh   |    18 |      2 |  | Dung   | 2025-02 |       150 |         120 |    30 |
  |       20 | Dung   |    22 |      1 |  | Dung   | 2025-03 |        90 |         150 |   -60 |
  |       20 | Ha     |    15 |      2 |  | Dung   | 2025-04 |       200 |          90 |   110 |
  |       30 | Khoa   |    12 |      1 |  +--------+---------+-----------+-------------+-------+
  |       30 | Linh   |  NULL |      2 |
  +----------+--------+-------+--------+
```

### Hai cái bẫy

**Bẫy 1 — không lọc được window function trong `WHERE`.**

```sql
-- SAI: báo lỗi "misuse of window function RANK()"
SELECT ho_ten, luong FROM nhan_vien WHERE RANK() OVER (ORDER BY luong DESC) <= 3;
```

Vì `WHERE` chạy ở bước 2 còn window function tính ở bước 5 (bảng thứ tự thực thi ở mục 3).
Bắt buộc bọc thêm một lớp CTE/subquery rồi lọc ở lớp ngoài — chính là mẫu 8.4.

**Bẫy 2 — `ORDER BY` trong `OVER` mà không ghi khung thì mặc định là `RANGE`, không phải `ROWS`.**

```text
  SUM(luong) OVER (ORDER BY luong)     ← mặc định RANGE: các dòng BẰNG NHAU bị gộp chung
  +--------+-------+-------------------+--------------+
  | ho_ten | luong | mac_dinh_la_range | ep_dung_rows |
  +--------+-------+-------------------+--------------+
  | Khoa   |    12 |                12 |           12 |
  | Minh   |    14 |                26 |           26 |
  | Ha     |    15 |                41 |           41 |
  | Binh   |    18 |                77 |           59 |  ◀── KHÁC NHAU!
  | Chi    |    18 |                77 |           77 |
  | Dung   |    22 |                99 |           99 |
  | An     |    25 |               124 |          124 |
  +--------+-------+-------------------+--------------+
      Binh và Chi cùng lương 18 → RANGE coi hai dòng này là một "bậc" và cộng cả hai
      vào cả hai dòng (59 + 18 = 77). Muốn luỹ kế đúng từng dòng phải ghi rõ
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW.
```

<details>
<summary><b>Tự kiểm tra 8.1</b> — Khi nào dùng <code>GROUP BY</code>, khi nào dùng window function?</summary>

Câu hỏi duy nhất cần trả lời: **kết quả cuối cần bao nhiêu dòng?**

* Cần **một dòng cho mỗi nhóm** (báo cáo tổng hợp) → `GROUP BY`.
* Cần **giữ nguyên từng dòng chi tiết** mà vẫn có số liệu của nhóm (xếp hạng, tỉ trọng,
  so với dòng trước) → window function.

Được phép dùng cả hai trong cùng một query: window function chạy **sau** `GROUP BY`, nên nó
nhìn thấy các dòng đã gom nhóm (xem lời giải bài 10).
</details>

<details>
<summary><b>Tự kiểm tra 8.2</b> — Lấy tháng có doanh thu cao nhất của <b>mỗi</b> nhân viên.</summary>

```sql
WITH xh AS (
    SELECT nv.ho_ten, ds.thang, ds.doanh_thu,
           ROW_NUMBER() OVER (PARTITION BY ds.nv_id ORDER BY ds.doanh_thu DESC) AS rn
    FROM doanh_so ds JOIN nhan_vien nv ON nv.nv_id = ds.nv_id
)
SELECT ho_ten, thang, doanh_thu FROM xh WHERE rn = 1 ORDER BY ho_ten;
```

→ Binh 2025-02 (150), Dung 2025-04 (200), Ha 2025-03 (130).

Nếu muốn "hoà thì lấy hết" thì đổi `ROW_NUMBER` → `RANK`.
</details>

<details>
<summary><b>Tự kiểm tra 8.3</b> — <code>COUNT(*) OVER ()</code> (ngoặc rỗng) trả về gì?</summary>

Tổng số dòng của **toàn bộ** kết quả, gắn vào từng dòng — vì `PARTITION BY` trống nghĩa là
"cả bảng là một nhóm". Rất hay dùng để tính tỉ trọng phần trăm mà không cần query thứ hai:

```sql
SELECT ho_ten, luong,
       ROUND(luong * 100.0 / SUM(luong) OVER (), 1) AS phan_tram_quy_luong
FROM nhan_vien WHERE luong IS NOT NULL;
```
</details>

---

## 9. NULL và những cạm bẫy của nó

### Nói bằng lời

`NULL` **không phải** số 0, **không phải** chuỗi rỗng, **không phải** `false`. Nó nghĩa là
**"không biết / không có dữ liệu"**. Mọi hành vi kỳ quặc của NULL đều suy ra được từ đúng
một câu đó: *phép so sánh với một cái không biết thì cho ra… không biết.*

Vì vậy SQL không dùng logic 2 giá trị (đúng/sai) mà dùng **logic 3 giá trị**:
`TRUE` / `FALSE` / `UNKNOWN`.

### Sơ đồ

```text
   ┌─────────────────────────────────────────────────────────────────────┐
   │  WHERE chỉ giữ lại những dòng cho ra TRUE.                          │
   │  Dòng cho ra UNKNOWN bị loại — y hệt FALSE. Đây là gốc mọi bất ngờ. │
   └─────────────────────────────────────────────────────────────────────┘

   BẢNG CHÂN TRỊ                          BẢNG SO SÁNH
   ┌─────────┬─────────┬──────────┐       luong = NULL   ──▶ UNKNOWN  (KHÔNG lỗi, KHÔNG false)
   │  AND    │ TRUE    │ UNKNOWN  │       luong <> NULL  ──▶ UNKNOWN
   ├─────────┼─────────┼──────────┤       NULL = NULL    ──▶ UNKNOWN  ◀── kể cả với chính nó!
   │ TRUE    │ TRUE    │ UNKNOWN  │       NULL IS NULL   ──▶ TRUE     ◀── cách duy nhất đúng
   │ FALSE   │ FALSE   │ FALSE ◀──┼── FALSE nuốt hết     NULL + 5     ──▶ NULL
   │ UNKNOWN │ UNKNOWN │ UNKNOWN  │       'a' || NULL    ──▶ NULL     ◀── mất cả chuỗi
   └─────────┴─────────┴──────────┘
   ┌─────────┬─────────┬──────────┐       Đo bằng SQL thật (ví dụ 9.2):
   │  OR     │ TRUE    │ UNKNOWN  │       +---------------+--------------+--------------+
   ├─────────┼─────────┼──────────┤       | dung_and_null | sai_and_null | dung_or_null |
   │ TRUE    │ TRUE ◀──┼── TRUE   │       +---------------+--------------+--------------+
   │ FALSE   │ FALSE   │ UNKNOWN  │  nuốt │ NULL          |            0 |            1 |
   │ UNKNOWN │ UNKNOWN │ UNKNOWN  │  hết  +---------------+--------------+--------------+
   └─────────┴─────────┴──────────┘
```

### Chín cạm bẫy, xếp theo mức độ hay gặp

| # | Cạm bẫy | Ví dụ trên bảng mẫu | Cách xử lý |
|---|---|---|---|
| 1 | `= NULL` không bao giờ đúng | `WHERE luong = NULL` → 0 dòng | dùng `IS NULL` / `IS NOT NULL` |
| 2 | Điều kiện phủ định cũng loại NULL | `WHERE luong <> 18` **không** ra Linh | `... OR luong IS NULL` |
| 3 | `NOT IN` + NULL → rỗng sạch | mục 6.3 | `NOT EXISTS`, hoặc lọc `IS NOT NULL` |
| 4 | `AVG`/`SUM`/`COUNT(cot)` bỏ qua NULL | `AVG(luong)` = 124/**7** = 17.71 | `AVG(COALESCE(luong,0))` nếu muốn chia 8 |
| 5 | `COUNT(*)` ≠ `COUNT(cot)` | 8 và 7 | chọn có chủ đích, nhất là sau `LEFT JOIN` |
| 6 | Phép tính dính NULL → NULL | `luong * 12`, `ho_ten \|\| luong` | `COALESCE(x, 0)` trước khi tính |
| 7 | Vị trí NULL khi sắp xếp khác nhau tuỳ hệ | SQLite/PG: NULL nhỏ nhất; Oracle: lớn nhất | ghi rõ `NULLS FIRST` / `NULLS LAST` |
| 8 | JOIN không khớp NULL | Minh biến mất khỏi `INNER JOIN` | `LEFT JOIN`, hoặc `IS NOT DISTINCT FROM` |
| 9 | Nhưng `GROUP BY`/`DISTINCT` lại **gộp** các NULL | phòng NULL thành **một** nhóm | biết để khỏi ngạc nhiên |

Mâu thuẫn ở dòng 9 chính là chỗ hay bị hỏi vặn: **toán tử `=` bảo "NULL khác NULL", còn
`GROUP BY`, `DISTINCT`, `UNION` lại coi các NULL là như nhau.** Không có logic sâu xa nào cả —
chuẩn SQL quy định vậy, cứ nhớ.

### Bộ công cụ xử lý NULL

```sql
COALESCE(luong, 0)              -- trả về giá trị KHÔNG NULL đầu tiên (nhiều tham số cũng được)
IFNULL(luong, 0)                -- SQLite/MySQL, y hệt COALESCE 2 tham số
NULLIF(a, b)                    -- trả về NULL nếu a = b → mẹo tránh chia cho 0: x / NULLIF(y, 0)
CASE WHEN luong IS NULL THEN ... END
```

```text
  Ví dụ 9.7 — chuỗi dính NULL thì mất trắng:
  +--------+-----------+---------------+
  | ho_ten | mo_ta     | mo_ta_da_chua |
  +--------+-----------+---------------+
  | Binh   | Binh - 18 | Binh - 18     |
  | Linh   | NULL      | Linh - 0      |   ◀ ho_ten || ' - ' || luong  với luong NULL
  +--------+-----------+---------------+     ra NULL, mất luôn cả tên!
```

<details>
<summary><b>Tự kiểm tra 9.1</b> — Bảng có 8 dòng, cột <code>luong</code> có 1 dòng NULL. <code>COUNT(*)</code>, <code>COUNT(luong)</code>, <code>SUM(luong)</code>, <code>AVG(luong)</code> ra gì?</summary>

`COUNT(*)` = **8** · `COUNT(luong)` = **7** · `SUM(luong)` = **124** · `AVG(luong)` = **17.71** (=124/7).

Bẫy phụ: nếu **tất cả** giá trị đều NULL thì `SUM` trả về **NULL** (không phải 0) còn
`COUNT` trả về **0**. Nên báo cáo tài chính hay bọc `COALESCE(SUM(x), 0)`.
</details>

<details>
<summary><b>Tự kiểm tra 9.2</b> — Câu này trả về mấy dòng? <code>SELECT * FROM nhan_vien WHERE luong &gt; 20 OR luong &lt;= 20;</code></summary>

**7 dòng**, không phải 8. Với Linh (`luong` NULL): `NULL > 20` = UNKNOWN, `NULL <= 20` = UNKNOWN,
`UNKNOWN OR UNKNOWN` = UNKNOWN → bị loại. Trong logic 2 giá trị thì "x > 20 hoặc x ≤ 20" luôn
đúng, nhưng SQL không dùng logic 2 giá trị.
</details>

<details>
<summary><b>Tự kiểm tra 9.3</b> — Có nên đặt <code>NOT NULL DEFAULT 0</code> cho cột <code>luong</code> không?</summary>

Tuỳ **ý nghĩa nghiệp vụ**, và đây là câu hỏi thiết kế hay bị hỏi:

* Nếu 0 là một giá trị **có thật và khác** với "chưa biết" (lương 0 ≠ chưa chốt lương) thì
  **giữ NULL** — nhét 0 vào sẽ làm `AVG` sai và không phân biệt được hai tình huống.
* Nếu cột kiểu "số lượt click", "số tiền đã trả" mà không có nghĩa là "chưa biết" thì
  `NOT NULL DEFAULT 0` tốt hơn: query đơn giản hơn, không dính bẫy NULL.

Nói được ý *"NULL mang thông tin 'chưa biết', nên đừng thay bằng 0 nếu 0 có nghĩa khác"* là đủ.
</details>

---

## 10. Index — và vì sao query chậm

### Nói bằng lời

Không có index, muốn tìm `WHERE nv_id = 1234` database phải **đọc từng dòng từ đầu đến cuối**
— gọi là **full table scan**. Với 8 dòng thì không sao; với 200.000 dòng thì mỗi lần tìm
là mỗi lần đọc 200.000 dòng.

Index là **cuốn mục lục** đặt cạnh bảng: một bản sao của một (vài) cột, **đã sắp xếp sẵn**,
kèm con trỏ về dòng gốc. Vì đã sắp xếp nên tìm được bằng cách chia đôi liên tục thay vì
đọc tuần tự — giống tra từ điển giấy: bạn không đọc từ trang 1.

### Sơ đồ: quét cả bảng và tìm qua index

```text
   ══ KHÔNG INDEX: SCAN ═══════════════════════════════════════════════
   WHERE nv_id = 1234
   ┌───┬───┬───┬───┬───┬───┬───┬─────────────────────────────┬───┐
   │ 1 │ 2 │ 3 │ 4 │ 5 │ 6 │ 7 │ ...  đọc HẾT, so từng dòng  │200k│
   └───┴───┴───┴───┴───┴───┴───┴─────────────────────────────┴───┘
     ▲───────────────────── 200.000 lần so sánh ──────────────────▶
     Đo thật trên máy: 5.596 ms mỗi lần chạy.

   ══ CÓ INDEX: SEARCH (cây B-tree) ═══════════════════════════════════
                          ┌──────────────┐
                          │  50k  100k   │           ← gốc: 1234 < 50k → rẽ nhánh trái
                          └───┬──────────┘
                  ┌───────────┴───────────┐
            ┌─────▼─────┐           ┌─────▼─────┐
            │ 10k  25k  │           │  ...      │  ← 1234 < 10k → rẽ trái tiếp
            └─────┬─────┘           └───────────┘
             ┌────▼────┐
             │1200 1240│ ...                       ← lá: tìm thấy 1234 → con trỏ tới dòng gốc
             └─────────┘
     Chỉ ~3 bước nhảy thay vì 200.000 lần đọc.
     Đo thật trên máy: 0.048 ms mỗi lần chạy → NHANH GẤP ~118 LẦN.
```

### Số đo thật (chạy `python docs\hoc\demo_sql.py --index`)

```text
  Bảng 200.000 dòng, truy vấn: SELECT * FROM log_lon WHERE nv_id = 1234

  [1] CHƯA CÓ INDEX
      kế hoạch : SCAN log_lon
      thời gian: 5.596 ms / lần

  [2] SAU KHI CREATE INDEX idx_log_nv ON log_lon(nv_id)   (mất 62 ms để tạo)
      kế hoạch : SEARCH log_lon USING INDEX idx_log_nv (nv_id=?)
      thời gian: 0.048 ms / lần   →  NHANH GẤP 118 LẦN

  [3] VẪN CÓ INDEX, nhưng viết WHERE nv_id + 0 = 1234
      kế hoạch : SCAN log_lon
      thời gian: 6.309 ms / lần   →  index bị vứt đi, chậm lại như cũ
```

Dòng [3] là bài học đắt nhất của mục này: **index có tồn tại không quan trọng bằng việc
query có dùng được nó hay không.**

> Con số tuyệt đối thay đổi theo máy và theo lần chạy (đo lại lần khác ra 8.5 ms → 0.048 ms,
> tức nhanh gấp 179 lần). Cái không đổi là **tỉ lệ hàng trăm lần** và dòng chữ `SCAN` → `SEARCH`
> trong kế hoạch chạy. Khi phỏng vấn, hãy kể theo cơ chế đó chứ đừng cố nhớ con số.

### Đọc kế hoạch chạy: `EXPLAIN QUERY PLAN`

Mọi hệ đều có lệnh này (`EXPLAIN` ở MySQL, `EXPLAIN ANALYZE` ở PostgreSQL,
`EXPLAIN QUERY PLAN` ở SQLite). Chỉ cần nhìn ra **hai từ**:

```text
   SCAN <bảng>                              → đọc cả bảng. Bảng lớn = đèn đỏ.
   SEARCH <bảng> USING INDEX <tên> (cot=?)  → nhảy thẳng bằng index. Tốt.
   SEARCH ... USING COVERING INDEX ...      → còn tốt hơn: không cần mở bảng gốc lần nữa.
   USE TEMP B-TREE FOR ORDER BY             → phải sắp xếp tạm. Index đúng sẽ khử được.
```

```sql
EXPLAIN QUERY PLAN SELECT * FROM nhan_vien WHERE phong_id = 10;   -- SCAN nhan_vien
CREATE INDEX idx_nv_phong ON nhan_vien(phong_id);
EXPLAIN QUERY PLAN SELECT * FROM nhan_vien WHERE phong_id = 10;   -- SEARCH ... USING INDEX
```

### Index nhiều cột và quy tắc "tiền tố trái" (leftmost prefix)

```text
   CREATE INDEX idx_ds ON doanh_so(nv_id, thang);

   Index này giống một cuốn DANH BẠ sắp theo (HỌ, rồi TÊN):

        nv_id=2 ─┬─ 2025-01        Tìm theo HỌ:            WHERE nv_id = 4              ✔ dùng được
                 ├─ 2025-02        Tìm theo HỌ + TÊN:      WHERE nv_id = 4 AND thang=.. ✔ dùng được
                 ├─ 2025-03        Tìm CHỈ theo TÊN:       WHERE thang = '2025-02'      ✖ PHẢI QUÉT
                 └─ 2025-04
        nv_id=4 ─┬─ 2025-01        Vì danh bạ sắp theo họ trước — biết mỗi tên thì
                 ├─ 2025-02        không biết mở trang nào, đành lật cả quyển.
                 └─ ...

   Kế hoạch thật:
     WHERE nv_id = 4 AND thang = '2025-02'  →  SEARCH ... USING INDEX idx_ds (nv_id=? AND thang=?)
     WHERE nv_id = 4                        →  SEARCH ... USING INDEX idx_ds (nv_id=?)
     WHERE thang = '2025-02'                →  SCAN doanh_so                    ◀── mất index
```

Hệ quả khi thiết kế: **thứ tự cột trong index nhiều cột là quan trọng**. Đặt cột hay được lọc
bằng `=` lên trước, cột lọc theo khoảng (`>`, `<`, `BETWEEN`) để sau.

### Năm lý do khiến query chậm (checklist đi phỏng vấn)

| # | Nguyên nhân | Dấu hiệu | Cách chữa |
|---|---|---|---|
| 1 | Không có index trên cột lọc/join | `SCAN` bảng lớn | tạo index đúng cột |
| 2 | **Bọc hàm quanh cột** làm index vô dụng | `SCAN` dù đã có index | để **cột trần** một bên dấu `=` |
| 3 | Sai thứ tự cột trong index nhiều cột | `SCAN` khi lọc cột đứng sau | đổi thứ tự, hoặc thêm index khác |
| 4 | JOIN nhân dòng ngoài dự kiến | kết quả nhiều dòng bất thường, chậm dần | kiểm tra quan hệ 1:N, gom nhóm trước khi JOIN |
| 5 | `SELECT *` khi chỉ cần vài cột | không dùng được covering index | liệt kê đúng cột cần |

Minh hoạ lý do #2 — hai câu **cùng ý nghĩa**, kế hoạch khác hẳn:

```sql
-- ✖ index chết: cột bị bọc trong substr()
SELECT * FROM nhan_vien WHERE substr(ngay_vao, 1, 4) = '2023';       -- SCAN nhan_vien

-- ✔ index sống: viết lại thành khoảng, cột đứng trần
SELECT * FROM nhan_vien WHERE ngay_vao >= '2023-01-01' AND ngay_vao < '2024-01-01';
-- SEARCH nhan_vien USING INDEX idx_nv_ngay (ngay_vao>? AND ngay_vao<?)
```

Các dạng khác của cùng một lỗi: `WHERE YEAR(ngay) = 2023`, `WHERE UPPER(ten) = 'AN'`,
`WHERE luong * 12 > 200`, `WHERE CAST(id AS TEXT) = '5'`. Luôn chuyển phép biến đổi **sang vế
hằng số**: `WHERE luong > 200 / 12`.

### Cái giá của index

Index **không miễn phí** — nói được ý này khi phỏng vấn là điểm cộng:

* Mỗi `INSERT` / `UPDATE` / `DELETE` phải cập nhật **thêm** mọi index liên quan → ghi chậm hơn.
* Index chiếm thêm dung lượng đĩa/RAM (bảng 10 cột đánh index 6 cột có thể phình gấp đôi).
* Index trên cột **ít giá trị khác nhau** (giới tính, cờ true/false) gần như vô dụng: bộ tối
  ưu thấy phải lấy 50% số dòng thì thà quét cả bảng còn nhanh hơn (nó gọi là **selectivity thấp**).
* Nguyên tắc thực tế: đánh index cho cột hay xuất hiện trong `WHERE`, `JOIN ... ON`, `ORDER BY`
  — và đo lại bằng `EXPLAIN` sau khi tạo, đừng đoán.

<details>
<summary><b>Tự kiểm tra 10.1</b> — Có index trên <code>ngay_vao</code>. Vì sao <code>WHERE substr(ngay_vao,1,4) = '2023'</code> vẫn chậm?</summary>

Vì index lưu **giá trị gốc đã sắp xếp** của `ngay_vao`, chứ không lưu `substr(ngay_vao,1,4)`.
Muốn biết `substr(...)` bằng bao nhiêu, database phải tính cho **từng dòng** → buộc phải quét.

Ba cách chữa: (1) viết lại thành khoảng như trên; (2) tạo **index trên biểu thức**
`CREATE INDEX ... ON nhan_vien(substr(ngay_vao,1,4))` (SQLite/PostgreSQL hỗ trợ);
(3) thêm hẳn một cột `nam_vao` rồi đánh index.
</details>

<details>
<summary><b>Tự kiểm tra 10.2</b> — Có nên đánh index cho tất cả các cột không?</summary>

Không. Ghi sẽ chậm đi (mỗi thao tác ghi phải cập nhật mọi index), tốn dung lượng, và index
trên cột ít giá trị khác nhau thường không được dùng tới. Đánh index theo **truy vấn thực tế**:
xem query nào chạy nhiều và chậm, `EXPLAIN` nó, rồi tạo index đúng cột nó cần.
</details>

<details>
<summary><b>Tự kiểm tra 10.3</b> — "Covering index" là gì?</summary>

Là index **chứa đủ mọi cột mà query cần**, nên database đọc xong index là có luôn kết quả,
không phải quay về bảng gốc lấy từng dòng. Đo thật trên bảng mẫu:

```text
SELECT nv_id, thang FROM doanh_so WHERE nv_id = 4;
  → SEARCH doanh_so USING COVERING INDEX idx_ds_nv_thang (nv_id=?)     ◀ khỏi mở bảng

SELECT nv_id, thang, doanh_thu FROM doanh_so WHERE nv_id = 4;
  → SEARCH doanh_so USING INDEX idx_ds_nv_thang (nv_id=?)              ◀ phải mở bảng
```

Đây cũng là một lý do cụ thể để **không viết `SELECT *`**.
</details>

---

## 11. Transaction và ACID

### Nói bằng lời

Chuyển tiền gồm hai bước: trừ tài khoản A, cộng tài khoản B. Nếu điện mất giữa hai bước thì
tiền bốc hơi. **Transaction** là cách nói với database: *"nhóm các lệnh này thành MỘT khối —
hoặc tất cả cùng thành công, hoặc không cái nào tính."*

```sql
BEGIN;                                    -- mở giao dịch
UPDATE tk SET so_du = so_du - 100 WHERE id = 'A';
UPDATE tk SET so_du = so_du + 100 WHERE id = 'B';
COMMIT;                                   -- chốt: từ giờ mọi người đều thấy
-- hoặc ROLLBACK;                         -- huỷ: quay lại như chưa có gì xảy ra
```

### Sơ đồ

```text
   THỜI GIAN ──────────────────────────────────────────────────────────────────▶

   BEGIN            UPDATE ... = 99         ROLLBACK
     │                    │                     │
     ▼                    ▼                     ▼
   ┌────────────────────────────────────────────┐
   │  vùng làm việc riêng của giao dịch này     │   người khác vẫn thấy giá trị CŨ (18)
   │  mình thấy 99, người khác KHÔNG thấy       │   suốt từ BEGIN tới COMMIT
   └────────────────────────────────────────────┘
     dữ liệu thật:  18 ──────────────────────────▶ 18   (ROLLBACK: như chưa có gì)

   BEGIN            UPDATE ... = 20          COMMIT
     │                    │                     │
     ▼                    ▼                     ▼
     dữ liệu thật:  18 ──────────────────────────▶ 20   (COMMIT: ghi thật, bền vững)
```

Chạy thật bằng `python docs\hoc\demo_sql.py --demo 11`:

```text
  [1] Lương của Binh ban đầu                        : 18
  [2] BEGIN; UPDATE ... = 99  → đọc trong transaction: 99
  [3] ROLLBACK                                      : 18   ← như chưa có gì xảy ra
  [4] BEGIN; UPDATE ... = 20; COMMIT                : 20   ← lần này ghi thật

  [5] NGUYÊN KHỐI (Atomicity): hai bước, bước 2 lỗi
      Lương Dung trước khi chuyển: 22
      bước 1 (trừ 5) đã chạy     : 17
      bước 2 BÁO LỖI             : UNIQUE constraint failed: nhan_vien.nv_id
      → gọi ROLLBACK
      Lương Dung sau tất cả      : 22   ← không bị trừ nửa chừng
```

### ACID — bốn chữ, mỗi chữ một câu

| Chữ | Tên | Nghĩa một câu | Thấy ở đâu trong demo |
|---|---|---|---|
| **A** | Atomicity — nguyên khối | Tất cả hoặc không gì cả; lỗi giữa chừng thì quay lại hết | bước [5]: Dung không bị trừ 5 |
| **C** | Consistency — nhất quán | Kết thúc giao dịch, mọi ràng buộc (khoá chính, khoá ngoại, `CHECK`) vẫn đúng | chính lỗi `UNIQUE constraint` đã chặn |
| **I** | Isolation — cô lập | Các giao dịch chạy song song không nhìn thấy phần dở dang của nhau | bước [2]: chỉ mình thấy 99 |
| **D** | Durability — bền vững | Đã `COMMIT` thì mất điện cũng còn (ghi xuống đĩa/WAL) | bước [4]: 20 tồn tại sau đó |

### Isolation level — vì sao có nhiều mức

Cô lập tuyệt đối thì an toàn nhất nhưng chậm nhất (phải khoá nhiều). Nên chuẩn SQL cho phép
chọn mức, đổi độ an toàn lấy tốc độ. Ba hiện tượng lỗi cần biết tên:

```text
   ① DIRTY READ — đọc phải dữ liệu chưa commit
   T1: BEGIN  UPDATE luong=99 ────────────────── ROLLBACK
   T2:                    └─▶ SELECT → thấy 99 (!!)      ← con số 99 chưa từng tồn tại thật

   ② NON-REPEATABLE READ — đọc hai lần, cùng một dòng, ra hai giá trị
   T1: BEGIN  SELECT luong → 18 ─────────────────── SELECT luong → 20 (?!)
   T2:                  └─ UPDATE luong=20; COMMIT ─┘

   ③ PHANTOM READ — đọc hai lần, lần sau xuất hiện thêm DÒNG MỚI
   T1: BEGIN  SELECT COUNT(*) → 8 ────────────────── SELECT COUNT(*) → 9 (?!)
   T2:                  └─ INSERT nhân viên; COMMIT ─┘
```

| Mức cô lập | Chặn dirty read | Chặn non-repeatable | Chặn phantom |
|---|---|---|---|
| READ UNCOMMITTED | ✖ | ✖ | ✖ |
| READ COMMITTED *(mặc định của PostgreSQL, Oracle, SQL Server)* | ✔ | ✖ | ✖ |
| REPEATABLE READ *(mặc định của MySQL InnoDB)* | ✔ | ✔ | ✖ (InnoDB chặn phần lớn nhờ MVCC) |
| SERIALIZABLE *(SQLite mặc định)* | ✔ | ✔ | ✔ |

SQLite đơn giản hơn hẳn: mặc định **SERIALIZABLE**, mỗi lúc chỉ một người ghi (bật WAL thì
nhiều người đọc song song với một người ghi). Đủ dùng cho ứng dụng nhỏ, không hợp cho hệ nhiều
người ghi đồng thời — đó là lúc cần PostgreSQL/MySQL.

> **Lưu ý Python:** thư viện `sqlite3` mặc định **tự mở transaction ngầm** trước các lệnh
> `INSERT/UPDATE/DELETE` và bạn phải gọi `conn.commit()`. `demo_sql.py` đặt
> `isolation_level=None` (chế độ autocommit) để `BEGIN`/`COMMIT`/`ROLLBACK` gõ tay có tác dụng
> đúng như trong bài.

<details>
<summary><b>Tự kiểm tra 11.1</b> — Nếu chương trình chết ngay sau <code>COMMIT</code>, dữ liệu có mất không?</summary>

Không — đó chính là chữ **D (Durability)**. `COMMIT` chỉ trả về sau khi thay đổi đã được ghi
bền vững (transaction log / WAL). Ngược lại, chết **trước** `COMMIT` thì lần khởi động sau
database sẽ tự `ROLLBACK` phần dở dang.
</details>

<details>
<summary><b>Tự kiểm tra 11.2</b> — <code>DELETE</code>, <code>TRUNCATE</code>, <code>DROP</code> khác nhau chỗ nào?</summary>

* `DELETE FROM t WHERE ...` — xoá **dòng**, có `WHERE`, ghi log từng dòng, **rollback được**.
* `TRUNCATE TABLE t` — xoá **sạch** dòng rất nhanh, không `WHERE`; ở nhiều hệ là DDL nên
  **không rollback được** và reset bộ đếm auto-increment. (SQLite không có `TRUNCATE`.)
* `DROP TABLE t` — xoá luôn **cấu trúc bảng**, mất cả schema lẫn dữ liệu.

Bẫy đi kèm: `DELETE FROM nhan_vien;` **quên `WHERE`** là xoá sạch bảng. Thói quen tốt: viết
`SELECT` với đúng điều kiện đó trước, xem đúng số dòng rồi mới đổi thành `DELETE`, và bọc
trong `BEGIN` … `COMMIT`.
</details>

---

## 12. Những câu lý thuyết hay bị hỏi

**`UNION` và `UNION ALL`?** — `UNION` nối hai kết quả rồi **bỏ dòng trùng** (phải sắp xếp/băm
để so → tốn kém). `UNION ALL` nối thẳng, giữ cả trùng, **nhanh hơn**. Mặc định nên dùng
`UNION ALL` trừ khi thật sự cần khử trùng. Điều kiện: số cột và kiểu cột phải khớp nhau.

**`DISTINCT` và `GROUP BY` khác gì?** — Về kết quả, `SELECT DISTINCT a FROM t` và
`SELECT a FROM t GROUP BY a` như nhau. Khác biệt: `GROUP BY` còn cho phép tính hàm gom nhóm
(`COUNT`, `SUM`) trên mỗi nhóm, `DISTINCT` chỉ khử trùng.

**`WHERE` hay `HAVING`?** — Lọc **dòng** thì `WHERE` (chạy trước, ít dữ liệu hơn nên nhanh hơn);
lọc **nhóm** theo giá trị gom nhóm thì `HAVING`. Nguyên tắc tối ưu: lọc được ở `WHERE` thì
đừng để tới `HAVING`.

**`CHAR` / `VARCHAR` / `TEXT`?** — `CHAR(n)` cố định độ dài (đệm khoảng trắng), `VARCHAR(n)`
thay đổi độ dài có giới hạn, `TEXT` không giới hạn thực dụng. SQLite thì đặc biệt: nó dùng
**kiểu động**, mọi thứ khai báo gì cũng lưu được — nhưng đừng lấy đó làm chuẩn khi trả lời.

**Khoá chính và khoá duy nhất (`PRIMARY KEY` vs `UNIQUE`)?** — Cả hai đảm bảo không trùng; một
bảng chỉ có **một** khoá chính và nó **không được NULL**, còn `UNIQUE` có thể có nhiều và
(ở phần lớn hệ) **cho phép NULL** — thậm chí nhiều dòng NULL, vì NULL không bằng NULL.

**Chuẩn hoá (normalization) một câu là gì?** — Tách dữ liệu ra nhiều bảng để **mỗi sự thật chỉ
lưu một chỗ**, tránh sửa một nơi quên nơi khác. Trả giá bằng việc phải JOIN nhiều hơn. Hệ phân
tích/báo cáo thường cố ý **phi chuẩn hoá** một phần để đọc nhanh.

**Câu hỏi "viết `UPDATE` an toàn"** — luôn có `WHERE`, luôn thử bằng `SELECT` trước:

```sql
SELECT * FROM nhan_vien WHERE nv_id = 7;                 -- ① xem đúng dòng cần sửa chưa
BEGIN;
UPDATE nhan_vien SET luong = 16 WHERE nv_id = 7;         -- ② sửa, đúng điều kiện đó
SELECT * FROM nhan_vien WHERE nv_id = 7;                 -- ③ kiểm tra lại
COMMIT;                                                  -- ④ ưng thì chốt, không thì ROLLBACK
```

---

## 13. 10 bài tập kiểu phỏng vấn (kèm lời giải)

Cách dùng: **tự viết trước**, gõ vào chế độ tương tác của `demo_sql.py`, so kết quả rồi mới mở
đáp án. Xem lời giải chạy sẵn: `python docs\hoc\demo_sql.py --baitap` (hoặc `--baitap 7`).

Mọi kết quả dưới đây là output thật của chương trình.

---

**Bài 1 (dễ).** Liệt kê họ tên và lương của nhân viên phòng 10, lương cao trước.

<details>
<summary>Lời giải</summary>

```sql
SELECT ho_ten, luong
FROM nhan_vien
WHERE phong_id = 10
ORDER BY luong DESC;
```

```text
  +--------+-------+
  | ho_ten | luong |
  +--------+-------+
  | An     |    25 |
  | Binh   |    18 |
  | Chi    |    18 |
  +--------+-------+
```
</details>

---

**Bài 2 (dễ).** Công ty có bao nhiêu người, bao nhiêu người **đã chốt lương**, và lương trung
bình thực tế là bao nhiêu?

<details>
<summary>Lời giải</summary>

```sql
SELECT COUNT(*)             AS tong_nv,
       COUNT(luong)         AS da_chot_luong,
       ROUND(AVG(luong), 2) AS luong_tb
FROM nhan_vien;
```

```text
  +---------+---------------+----------+
  | tong_nv | da_chot_luong | luong_tb |
  +---------+---------------+----------+
  |       8 |             7 |    17.71 |
  +---------+---------------+----------+
```

**Ý người hỏi muốn nghe:** `COUNT(*)` đếm dòng, `COUNT(luong)` đếm giá trị không NULL, và
`AVG` chia cho **7** chứ không phải 8. Nói ra được điều đó mới là trả lời đủ.
</details>

---

**Bài 3 (dễ–TB).** Mỗi phòng có mấy người và quỹ lương bao nhiêu? Chỉ lấy phòng từ 2 người trở lên.

<details>
<summary>Lời giải</summary>

```sql
SELECT phong_id, COUNT(*) AS so_nv, SUM(luong) AS quy_luong
FROM nhan_vien
GROUP BY phong_id
HAVING COUNT(*) >= 2
ORDER BY quy_luong DESC;
```

```text
  +----------+-------+-----------+
  | phong_id | so_nv | quy_luong |
  +----------+-------+-----------+
  |       10 |     3 |        61 |
  |       20 |     2 |        37 |
  |       30 |     2 |        12 |
  +----------+-------+-----------+
```

Điều kiện trên **nhóm** → `HAVING`. Chú ý phòng 30 có 2 người nhưng quỹ lương chỉ 12, vì
lương của Linh là NULL nên không được cộng.
</details>

---

**Bài 4 (TB).** Liệt kê **tất cả** phòng ban kèm số nhân viên, kể cả phòng chưa có ai.

<details>
<summary>Lời giải</summary>

```sql
SELECT pb.ten_phong, COUNT(nv.nv_id) AS so_nv
FROM phong_ban pb
LEFT JOIN nhan_vien nv ON pb.phong_id = nv.phong_id
GROUP BY pb.phong_id, pb.ten_phong
ORDER BY so_nv DESC, pb.phong_id;
```

```text
  +------------+-------+
  | ten_phong  | so_nv |
  +------------+-------+
  | Ky thuat   |     3 |
  | Kinh doanh |     2 |
  | Nhan su    |     2 |
  | Nghien cuu |     0 |
  +------------+-------+
```

**Hai chỗ rụng người:** (1) phải `LEFT JOIN` với `phong_ban` ở **bên trái**; (2) phải
`COUNT(nv.nv_id)` — nếu viết `COUNT(*)` thì Nghiên cứu ra **1** vì nó đếm cái dòng NULL.
</details>

---

**Bài 5 (TB).** Những ai **chưa từng** có bản ghi doanh số nào?

<details>
<summary>Lời giải</summary>

```sql
SELECT nv.nv_id, nv.ho_ten
FROM nhan_vien nv
WHERE NOT EXISTS (SELECT 1 FROM doanh_so ds WHERE ds.nv_id = nv.nv_id)
ORDER BY nv.nv_id;
```

```text
  +-------+--------+
  | nv_id | ho_ten |
  +-------+--------+
  |     1 | An     |
  |     3 | Chi    |
  |     6 | Khoa   |
  |     7 | Linh   |
  |     8 | Minh   |
  +-------+--------+
```

Cách khác cùng kết quả: `LEFT JOIN doanh_so ... WHERE ds.nv_id IS NULL`.

Ở bài này `NOT IN` **cũng** đúng vì `doanh_so.nv_id` là `NOT NULL` — nhưng khi trả lời nên
chọn `NOT EXISTS` và **nói rõ lý do**: nếu cột bên trong có NULL thì `NOT IN` trả về rỗng (mục 6.3).
</details>

---

**Bài 6 (TB).** Mỗi nhân viên đi kèm tên quản lý; ai không có sếp thì ghi `(khong co)`.

<details>
<summary>Lời giải</summary>

```sql
SELECT nv.ho_ten AS nhan_vien,
       COALESCE(sep.ho_ten, '(khong co)') AS quan_ly
FROM nhan_vien nv
LEFT JOIN nhan_vien sep ON nv.quan_ly_id = sep.nv_id
ORDER BY nv.nv_id;
```

```text
  +-----------+------------+
  | nhan_vien | quan_ly    |
  +-----------+------------+
  | An        | (khong co) |
  | Binh      | An         |
  | Chi       | An         |
  | Dung      | An         |
  | Ha        | Dung       |
  | Khoa      | An         |
  | Linh      | Khoa       |
  | Minh      | An         |
  +-----------+------------+
```

Ba ý: **SELF JOIN** (một bảng, hai alias) + **LEFT** (để An không mất) + **COALESCE** (hiển thị đẹp).
</details>

---

**Bài 7 (TB–khó).** Tìm **mức lương cao thứ hai** trong công ty. Viết 3 cách.

<details>
<summary>Lời giải</summary>

```sql
-- Cách 1: lớn nhất trong những cái nhỏ hơn cái lớn nhất
SELECT MAX(luong) AS cach_1 FROM nhan_vien
WHERE luong < (SELECT MAX(luong) FROM nhan_vien);

-- Cách 2: sắp xếp rồi bỏ qua 1 dòng
SELECT DISTINCT luong AS cach_2 FROM nhan_vien
WHERE luong IS NOT NULL ORDER BY luong DESC LIMIT 1 OFFSET 1;

-- Cách 3: DENSE_RANK
WITH xh AS (
    SELECT luong, DENSE_RANK() OVER (ORDER BY luong DESC) AS hang
    FROM nhan_vien WHERE luong IS NOT NULL
)
SELECT DISTINCT luong AS cach_3 FROM xh WHERE hang = 2;
```

Cả ba đều ra **22**.

**Bẫy phải nói ra:** câu hỏi là "**mức lương** cao thứ hai", không phải "người thứ hai". Nếu
hai người cùng đứng đỉnh thì mức thứ hai là mức **khác** tiếp theo → dùng `DENSE_RANK` +
`DISTINCT`, không dùng `ROW_NUMBER`. Và cách 1 có ưu điểm: nếu không tồn tại thì trả về `NULL`
chứ không báo lỗi.
</details>

---

**Bài 8 (khó).** Top 2 mức lương cao nhất **mỗi phòng**, kèm tên phòng.

<details>
<summary>Lời giải</summary>

```sql
WITH xh AS (
    SELECT pb.ten_phong, nv.ho_ten, nv.luong,
           DENSE_RANK() OVER (PARTITION BY nv.phong_id ORDER BY nv.luong DESC) AS hang
    FROM nhan_vien nv
    JOIN phong_ban pb ON pb.phong_id = nv.phong_id
    WHERE nv.luong IS NOT NULL
)
SELECT ten_phong, ho_ten, luong, hang
FROM xh
WHERE hang <= 2
ORDER BY ten_phong, hang, ho_ten;
```

```text
  +------------+--------+-------+------+
  | ten_phong  | ho_ten | luong | hang |
  +------------+--------+-------+------+
  | Kinh doanh | Dung   |    22 |    1 |
  | Kinh doanh | Ha     |    15 |    2 |
  | Ky thuat   | An     |    25 |    1 |
  | Ky thuat   | Binh   |    18 |    2 |
  | Ky thuat   | Chi    |    18 |    2 |   ◀ hoà điểm → giữ cả hai
  | Nhan su    | Khoa   |    12 |    1 |
  +------------+--------+-------+------+
```

Phòng Kỹ thuật có Binh và Chi **cùng 18** → `DENSE_RANK` giữ cả hai (3 dòng). Nếu dùng
`ROW_NUMBER` thì một trong hai bị cắt oan. Câu nên hỏi ngược lại người phỏng vấn:
*"bằng điểm thì lấy hết hay lấy đúng 2?"* — hỏi được là ăn điểm.

Lưu ý phải lọc `WHERE nv.luong IS NOT NULL`, nếu không Linh (NULL) sẽ chiếm hạng 2 của phòng Nhân sự.
</details>

---

**Bài 9 (khó).** Với mỗi nhân viên có doanh số: doanh thu từng tháng, doanh thu tháng trước,
và **% tăng trưởng**.

<details>
<summary>Lời giải</summary>

```sql
WITH t AS (
    SELECT nv.ho_ten, ds.thang, ds.doanh_thu,
           LAG(ds.doanh_thu) OVER (PARTITION BY ds.nv_id ORDER BY ds.thang) AS thang_truoc
    FROM doanh_so ds
    JOIN nhan_vien nv ON nv.nv_id = ds.nv_id
)
SELECT ho_ten, thang, doanh_thu, thang_truoc,
       ROUND((doanh_thu - thang_truoc) * 100.0 / NULLIF(thang_truoc, 0), 1) AS tang_truong_pc
FROM t
ORDER BY ho_ten, thang;
```

```text
  +--------+---------+-----------+-------------+----------------+
  | ho_ten | thang   | doanh_thu | thang_truoc | tang_truong_pc |
  +--------+---------+-----------+-------------+----------------+
  | Binh   | 2025-01 |        60 |        NULL |           NULL |
  | Binh   | 2025-02 |       150 |          60 |            150 |
  | Binh   | 2025-03 |        90 |         150 |            -40 |
  | Binh   | 2025-04 |        70 |          90 |          -22.2 |
  | Dung   | 2025-01 |       120 |        NULL |           NULL |
  | Dung   | 2025-02 |       150 |         120 |             25 |
  | Dung   | 2025-03 |        90 |         150 |            -40 |
  | Dung   | 2025-04 |       200 |          90 |          122.2 |
  | Ha     | 2025-01 |        80 |        NULL |           NULL |
  | Ha     | 2025-02 |        95 |          80 |           18.8 |
  | Ha     | 2025-03 |       130 |          95 |           36.8 |
  | Ha     | 2025-04 |       110 |         130 |          -15.4 |
  +--------+---------+-----------+-------------+----------------+
```

**Ba ý ăn điểm:** `PARTITION BY` để không lấy nhầm tháng của người khác; nhân `100.0` (không
phải `100`) để tránh chia số nguyên; `NULLIF(x, 0)` để không nổ lỗi chia cho 0. Tháng đầu
không có tháng trước → `NULL`, hoàn toàn đúng, đừng cố nhét 0 vào.
</details>

---

**Bài 10 (khó).** Bảng xếp hạng phòng ban: số nhân viên, tổng doanh thu, **tỉ trọng %** trên
toàn công ty, và **thứ hạng**. Phòng không có doanh thu vẫn phải hiện với số 0.

<details>
<summary>Lời giải</summary>

```sql
WITH ds_phong AS (
    SELECT pb.phong_id, pb.ten_phong,
           COUNT(DISTINCT nv.nv_id)       AS so_nv,
           COALESCE(SUM(ds.doanh_thu), 0) AS tong_ds
    FROM phong_ban pb
    LEFT JOIN nhan_vien nv ON nv.phong_id = pb.phong_id
    LEFT JOIN doanh_so  ds ON ds.nv_id    = nv.nv_id
    GROUP BY pb.phong_id, pb.ten_phong
)
SELECT ten_phong, so_nv, tong_ds,
       ROUND(tong_ds * 100.0 / NULLIF(SUM(tong_ds) OVER (), 0), 1) AS ty_trong_pc,
       RANK() OVER (ORDER BY tong_ds DESC) AS hang
FROM ds_phong
ORDER BY hang, ten_phong;
```

```text
  +------------+-------+---------+-------------+------+
  | ten_phong  | so_nv | tong_ds | ty_trong_pc | hang |
  +------------+-------+---------+-------------+------+
  | Kinh doanh |     2 |     975 |        72.5 |    1 |
  | Ky thuat   |     3 |     370 |        27.5 |    2 |
  | Nghien cuu |     0 |       0 |           0 |    3 |
  | Nhan su    |     2 |       0 |           0 |    3 |   ◀ hoà → cùng hạng 3
  +------------+-------+---------+-------------+------+
```

Bài này gộp gần như mọi thứ trong bài giảng, và có **một chỗ giết người**:

* JOIN thêm `doanh_so` làm mỗi nhân viên **nhân ra 4 dòng** (4 tháng) → bắt buộc
  `COUNT(DISTINCT nv.nv_id)`; viết `COUNT(nv.nv_id)` sẽ ra Kinh doanh **8 người** thay vì 2.
* `LEFT JOIN` hai lần + `COALESCE` để phòng Nghiên cứu (0 người) và Nhân sự (2 người nhưng
  không có doanh số) vẫn hiện với 0.
* `SUM(tong_ds) OVER ()` là tổng toàn bảng gắn vào từng dòng → tính tỉ trọng mà **không cần
  query thứ hai**. Đây là chỗ `GROUP BY` và window function làm việc cùng nhau: window chạy
  **sau** khi đã gom nhóm.
* Hai phòng cùng 0 → `RANK` cho cả hai **hạng 3** (và sẽ không có hạng 4).
</details>

---

## 14. Lộ trình 7 ngày trước hôm phỏng vấn

| Ngày | Việc | Đạt được |
|---|---|---|
| 1 | Mục 1–3, gõ lại hết ví dụ, làm bài 1–2 | viết được `SELECT/WHERE/ORDER BY` không cần nghĩ |
| 2 | Mục 4 (JOIN), vẽ lại sơ đồ ghép cặp **ra giấy**, làm bài 4–6 | phân biệt được 4 kiểu JOIN, giải thích được bẫy `ON`/`WHERE` |
| 3 | Mục 5–6, làm bài 3, 5, 7 | `GROUP BY`/`HAVING` thành phản xạ, kể được bẫy `NOT IN` |
| 4 | Mục 7–8, làm bài 8–9 | viết được mẫu top-N mỗi nhóm mà không cần nhìn lại |
| 5 | Mục 9–10, chạy `--index`, tự `EXPLAIN` vài câu | trả lời được "vì sao query chậm" bằng ví dụ có số đo |
| 6 | Mục 11–12, làm bài 10 | nói trôi ACID, isolation, và làm được bài tổng hợp |
| 7 | Làm lại cả 10 bài **không mở đáp án**, tự chấm | biết mình yếu chỗ nào để ôn lại đúng chỗ đó |

**Ba câu chắc chắn bị hỏi** — chuẩn bị sẵn câu trả lời 30 giây cho mỗi câu:

1. *"`INNER JOIN` và `LEFT JOIN` khác nhau thế nào?"* → nói bằng **dòng không khớp thì bị vứt
   hay được giữ với NULL**, rồi lấy ví dụ nhân viên chưa có phòng.
2. *"`WHERE` và `HAVING` khác nhau thế nào?"* → **lọc dòng trước khi gom** và **lọc nhóm sau
   khi gom**, dẫn ra bảng thứ tự thực thi.
3. *"Query chậm thì làm gì?"* → `EXPLAIN` xem `SCAN` hay `SEARCH`; kiểm tra index trên cột lọc
   và cột join; kiểm tra có bọc hàm quanh cột không; kiểm tra JOIN có nhân dòng không.

Nếu bị hỏi câu không biết: **nói thẳng là chưa gặp, rồi nói cách mình sẽ tìm ra** (viết thử,
`EXPLAIN`, đọc tài liệu). Fresher không bị trừ điểm vì chưa biết — bị trừ điểm vì đoán bừa
và nói chắc chắn những thứ sai.

**Đọc thêm:** [SQLite — SQL syntax](https://sqlite.org/lang.html) ·
[PostgreSQL Tutorial](https://www.postgresql.org/docs/current/tutorial.html) ·
[Use The Index, Luke](https://use-the-index-luke.com/) (sách online về index, miễn phí) ·
luyện đề: [pgexercises.com](https://pgexercises.com/), LeetCode Database, HackerRank SQL.
