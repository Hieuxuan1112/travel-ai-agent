# Toán cho AI Engineer — từ mất gốc đến giải thích được trong phỏng vấn

> Bài này viết cho người **đã quên hết toán phổ thông** nhưng cần hiểu và **nói ra miệng được**
> các hệ thống AI/LLM đang làm gì. Không chứng minh, không định lý — chỉ đúng phần dùng được.
> Mỗi công thức đều được **dịch nghĩa từng ký hiệu**, kèm ví dụ số nhỏ tự tính tay được.
> Có chương trình chạy kèm: [`demo_toan_ai.py`](demo_toan_ai.py).

**Mục lục**

1. [Vector, tích vô hướng, chuẩn, cosine similarity](#1-vector-tích-vô-hướng-chuẩn-cosine-similarity)
2. [Ma trận và phép nhân ma trận — đủ để hiểu Q, K, V](#2-ma-trận-và-phép-nhân-ma-trận--đủ-để-hiểu-q-k-v)
3. [Softmax — biến điểm số thành xác suất, và temperature](#3-softmax--biến-điểm-số-thành-xác-suất-và-temperature)
4. [Xác suất, log-likelihood, perplexity — LLM tối ưu cái gì](#4-xác-suất-log-likelihood-perplexity--llm-tối-ưu-cái-gì)
5. [Đạo hàm và gradient descent — learning rate là gì](#5-đạo-hàm-và-gradient-descent--learning-rate-là-gì)
6. [Trung bình, trung vị, phân vị — vì sao đo p95](#6-trung-bình-trung-vị-phân-vị--vì-sao-đo-p95)
7. [Chạy chương trình demo](#7-chạy-chương-trình-demo)
8. [Bảng tra ký hiệu](#8-bảng-tra-ký-hiệu)

---

## Đọc bài này thế nào

Sáu mục dưới đây xếp **theo đúng thứ tự bạn cần cho công việc**, không phải thứ tự sách giáo khoa:

```
   MUC 1        MUC 2         MUC 3          MUC 4            MUC 5         MUC 6
  vector  -->  ma tran  -->  softmax  -->  xac suat/PPL --> gradient  --> thong ke
    |            |             |               |             descent         |
    v            v             v               v                v            v
  RAG, tim    attention     chon chu       "model tot     fine-tune,     do do tre
  kiem, do    Q, K, V       tiep theo,     hay do?"       learning       he thong,
  giong nhau                temperature    danh gia       rate           SLA p95
```

Ba mục đầu (1–3) trả lời **"model chạy thế nào"**. Mục 4 trả lời **"đo model bằng gì"**.
Mục 5 trả lời **"model học thế nào"**. Mục 6 là toán bạn dùng **hằng ngày khi vận hành**.

Quy ước ký hiệu chung — nhớ 4 dòng này là đọc được hết cả bài:

| Ký hiệu | Đọc là | Nghĩa |
|---|---|---|
| `a`, `b`, `x` | vector | một **danh sách số có thứ tự**, ví dụ `[4, 3, 0]` |
| `a_i` (a chỉ số i) | "a i" | **số thứ i** trong danh sách đó. Với `a = [4,3,0]`: `a_1 = 4`, `a_2 = 3` |
| `Σ` (sigma) | "tổng của" | cộng dồn nhiều số lại |
| `n` | en | **số phần tử** (số chiều của vector, số mẫu dữ liệu…) |

> `Σ(i=1..n) a_i` đọc là: *"cho i chạy từ 1 đến n, cộng tất cả `a_i` lại"*.
> Với `a = [4, 3, 0]` thì `Σ(i=1..3) a_i = 4 + 3 + 0 = 7`. Chỉ có thế thôi.

---

## 1. Vector, tích vô hướng, chuẩn, cosine similarity

### 1.1. Vector là gì — ví dụ đời thường

Bạn muốn mô tả một người bằng số. Bạn chọn 3 tiêu chí: **chiều cao (cm), cân nặng (kg), tuổi**.

```
   Nam  ->  [ 170 ,  65 ,  24 ]
   Hoa  ->  [ 158 ,  50 ,  23 ]
              ^      ^     ^
              |      |     +-- chieu thu 3: tuoi
              |      +-------- chieu thu 2: can nang
              +--------------- chieu thu 1: chieu cao
```

**Vector = danh sách số có thứ tự.** Hết. Không có gì huyền bí.

Hai điều kiện bắt buộc:

- **Thứ tự cố định** — vị trí 1 luôn là chiều cao, không được hôm nay đổi sang cân nặng.
- **Cùng số chiều** — mọi người đều mô tả bằng đúng 3 số thì mới so sánh được với nhau.

Trong AI, thay vì 3 tiêu chí do người chọn, model học ra **768 hoặc 1536 tiêu chí** mà con người
không đặt tên được. Vector đó gọi là **embedding**. Bản chất vẫn y hệt: một danh sách số.

### 1.2. Vector là một MŨI TÊN

Đây là hình ảnh quan trọng nhất của cả mục này. Vector `[4, 3]` là mũi tên đi từ gốc `(0,0)`
tới điểm `(4,3)`:

```
   truc 2  ("la sinh vat song")
     ^
   6 |                              * cun = [8, 6]
     |                          .
   5 |                      .
     |                  .              <-- CUN va CHO cung mot HUONG,
   4 |  * meo = [3,4].                     chi khac DO DAI (cun dai gap doi)
     |   .       .
   3 |    .  .         * cho = [4, 3]
     |     ..
   2 |   ...
     |  ..
   1 | ..
     |.
   0 +---+---+---+---+---+---+---+---+---> truc 1 ("nuoi trong nha")
     0   1   2   3   4   5   6   7   8

   (Chieu thu 3 "la may moc" o day deu bang 0.
    Chiec o to = [0, 0, 5] nam tren truc thu 3, dam thang ra khoi trang giay.)
```

Một mũi tên có **2 tính chất**, và ta sẽ tách riêng chúng ra:

| Tính chất | Nghĩa trong AI |
|---|---|
| **Hướng** (chỉ về đâu) | **Nội dung / ngữ nghĩa** — nói về cái gì |
| **Độ dài** (dài bao nhiêu) | Cường độ, độ dài văn bản, tần suất từ — thường **không quan tâm** |

Đây chính là lý do cosine similarity tồn tại: nó **chỉ đo hướng, vứt bỏ độ dài**.

### 1.3. Tích vô hướng (dot product)

**Công thức:**

```
   a · b  =  a_1·b_1 + a_2·b_2 + a_3·b_3          (viet gon:  Σ(i=1..n) a_i · b_i )
```

**Dịch từng ký hiệu:**

| Ký hiệu | Nghĩa |
|---|---|
| `a`, `b` | hai vector **cùng số chiều** |
| `·` (dấu chấm ở giữa) | phép "tích vô hướng", đọc là *"a chấm b"* |
| `a_i · b_i` | nhân **số thứ i của a** với **số thứ i của b** |
| `Σ` | cộng tất cả các tích đó lại |
| Kết quả | **MỘT SỐ duy nhất** (không phải vector) — nên mới gọi là "vô hướng" |

**Quy trình 3 bước:** ghép cặp theo vị trí → nhân từng cặp → cộng tất cả.

```
      a = [ 4 ,  3 ,  0 ]
            |    |    |
            x    x    x        <-- nhan theo tung cot
            |    |    |
      b = [ 3 ,  4 ,  0 ]
            |    |    |
            v    v    v
           12 + 12 +  0   =  24            a · b = 24
```

**Ý nghĩa trực giác:** dot product **lớn** khi hai vector **cùng hướng và cùng lớn**; bằng **0**
khi chúng **vuông góc** (không dính dáng gì nhau); **âm** khi ngược hướng.

Ví dụ dễ nhớ: `a·b` là điểm một trận đấu. `a` = "bạn coi trọng mỗi tiêu chí bao nhiêu",
`b` = "món hàng ghi được bao nhiêu ở mỗi tiêu chí" → `a·b` = tổng điểm món hàng đó **với bạn**.

### 1.4. Chuẩn (norm) — độ dài của mũi tên

**Công thức:**

```
   ||a||  =  √( a_1² + a_2² + a_3² )              (viet gon:  √( Σ(i) a_i² ) )
```

**Dịch từng ký hiệu:**

| Ký hiệu | Nghĩa |
|---|---|
| `\|\|a\|\|` (hai gạch đứng) | "chuẩn của a" = **độ dài mũi tên a**. Có nơi viết một gạch |
| `a_i²` | số thứ i **nhân với chính nó** (bình phương) |
| `√` | căn bậc hai — *"số nào nhân với chính nó ra cái này?"* `√25 = 5` |

Đây đúng là **định lý Pythagoras** hồi lớp 7, chỉ mở rộng ra nhiều chiều:

```
        ^
      3 +- - - - - - -* cho = [4, 3]
        |          .  |
        |       .     |   canh doc = 3
        |    .        |
        | .           |
      0 +-------------+------>
        0     canh ngang = 4

     do dai = √(4² + 3²) = √(16 + 9) = √25 = 5
```

Lưu ý: `||a||` **luôn ≥ 0**, và chỉ bằng 0 khi vector toàn số 0.

### 1.5. Cosine similarity — công thức chính

**Công thức:**

```
                     a · b                a_1b_1 + a_2b_2 + a_3b_3
   cos(a, b)  =  -------------  =  --------------------------------------
                 ||a|| · ||b||     √(a_1²+a_2²+a_3²) · √(b_1²+b_2²+b_3²)
```

**Dịch nguyên câu:** *"lấy tích vô hướng của hai vector, rồi chia cho tích hai độ dài của chúng."*

Phép chia đó làm đúng một việc: **triệt tiêu độ dài, chỉ chừa lại hướng**. Vì `||a||` nằm dưới
mẫu, nếu bạn nhân `a` lên gấp đôi thì tử số gấp đôi, mẫu số cũng gấp đôi → kết quả **không đổi**.

Kết quả luôn nằm trong `[-1, +1]`, và nó chính là **cosin của góc giữa hai mũi tên**:

```
   goc = 0 do              goc = 90 do             goc = 180 do
   cung huong hoan toan    vuong goc               nguoc huong hoan toan

        a   b                   b                       b
       --> -->                  ^                      <---
                                |
                                +---> a                      ---> a

     cos = 1.0              cos = 0.0                cos = -1.0
     "y het nhau"           "khong lien quan"        "trai nguoc"

   +--------------------------------------------------------------+
   |   -1  <------------  0  ------------>  +1                    |
   |   nguoc nghia     khong lien quan     cung nghia             |
   +--------------------------------------------------------------+
```

### 1.6. Ví dụ số — tự tính tay

Ba chiều lần lượt là: **(1) nuôi trong nhà, (2) là sinh vật sống, (3) là máy móc**.

```
   cho   = [4, 3, 0]
   meo   = [3, 4, 0]
   cun   = [8, 6, 0]     <-- dung bang 2 x cho: cung huong, dai gap doi
   o to  = [0, 0, 5]
```

**Bài 1 — chó vs mèo:**

```
   a · b   = 4·3 + 3·4 + 0·0 = 12 + 12 + 0 = 24
   ||cho|| = √(4² + 3² + 0²) = √25 = 5
   ||meo|| = √(3² + 4² + 0²) = √25 = 5

   cos = 24 / (5 · 5) = 24 / 25 = 0.96        -> rat giong nhau
```

**Bài 2 — chó vs cún (chỉ khác độ dài):**

```
   a · b   = 4·8 + 3·6 + 0·0 = 32 + 18 = 50
   ||cho|| = 5
   ||cun|| = √(8² + 6²) = √100 = 10

   cos = 50 / (5 · 10) = 50 / 50 = 1.0        -> GIONG HET, du dai gap doi
```

Đây là bằng chứng bằng số cho câu *"cosine bỏ qua độ dài"*. Nếu dùng dot product trần (50 so với
24) bạn sẽ kết luận sai rằng *"chó giống cún hơn chó giống mèo"* — trong khi cún chỉ là **cùng
nội dung nhưng viết dài hơn**.

**Bài 3 — chó vs ô tô:**

```
   a · b = 4·0 + 3·0 + 0·5 = 0
   cos   = 0 / (5 · 5) = 0.0                  -> khong lien quan gi nhau
```

**Bảng tổng kết:**

| Cặp | dot | \|\|a\|\| | \|\|b\|\| | **cosine** | Kết luận |
|---|---|---|---|---|---|
| chó – mèo | 24 | 5 | 5 | **0.96** | rất giống |
| chó – cún | 50 | 5 | 10 | **1.00** | y hệt (chỉ khác độ dài) |
| chó – ô tô | 0 | 5 | 5 | **0.00** | không liên quan |

### 1.7. Vì sao nó đo được ĐỘ GIỐNG VỀ NGỮ NGHĨA

Đây là câu hỏi phỏng vấn hay gặp. Trả lời gọn gồm 3 ý:

1. **Không phải toán tạo ra ngữ nghĩa — mà là quá trình huấn luyện.** Model embedding được train
   với mục tiêu: câu cùng nghĩa thì vector **cùng hướng**, câu khác nghĩa thì **lệch hướng**.
   Toán chỉ cung cấp cái thước đo hướng; ngữ nghĩa nằm ở dữ liệu huấn luyện.
2. **Mỗi chiều là một "nét nghĩa" model tự học được.** Hai vector cùng hướng nghĩa là **cùng tỉ lệ
   pha trộn các nét nghĩa đó** — trực giác gần với "cùng chủ đề".
3. **Bỏ độ dài là đúng ý ta muốn.** Độ dài vector thường phản ánh độ dài văn bản/cường độ chứ
   không phản ánh chủ đề. Đoạn 20 chữ và đoạn 200 chữ cùng nói về bãi biển phải được coi là giống nhau.

**Ba cái bẫy nên biết** (nói ra được sẽ ghi điểm):

- **Cosine cao ≠ đúng sự thật.** *"Hà Nội là thủ đô Việt Nam"* và *"Hà Nội không phải thủ đô Việt
  Nam"* có cosine rất cao — cùng chủ đề nhưng trái ngược ý.
- **Con số tuyệt đối vô nghĩa nếu tách khỏi model.** Với nhiều model embedding, hai câu bất kỳ
  hiếm khi có cosine dưới 0.4. Chỉ **thứ tự xếp hạng** mới dùng được; muốn đặt ngưỡng thì phải đo
  trên chính dữ liệu của mình.
- **Nếu vector đã chuẩn hoá** (`||a|| = 1`, nhiều API trả về sẵn như vậy) thì mẫu số bằng 1, nên
  **cosine = dot product**. Đó là lý do vector DB hay dùng thẳng dot product cho nhanh.

<details><summary><b>Tự kiểm tra mục 1 — bấm để xem đáp án</b></summary>

**Câu 1. Tính cosine giữa `a = [1, 2, 2]` và `b = [2, 4, 4]`. Đoán trước khi tính.**

Đoán ngay được là `1.0` vì `b = 2a` (cùng hướng). Kiểm chứng: `a·b = 2 + 8 + 8 = 18`;
`||a|| = √(1+4+4) = 3`; `||b|| = √(4+16+16) = 6`; `18 / (3·6) = 1.0`. ✔

**Câu 2. Vì sao phải chia cho `||a||·||b||` thay vì dùng thẳng dot product?**

Để loại bỏ ảnh hưởng của **độ dài**, chỉ giữ lại **hướng**. Không chia thì một đoạn văn dài
(vector dài) sẽ luôn ăn điểm cao hơn đoạn ngắn, dù nội dung không liên quan hơn.

**Câu 3. Cosine = 0 nghĩa là gì? Cosine = −1 nghĩa là gì?**

`0` = hai vector vuông góc = không chia sẻ nét nghĩa nào. `−1` = ngược hướng hoàn toàn. Với
embedding thật của các model hiện đại, giá trị âm gần như không xuất hiện.

**Câu 4. Sếp bảo "hai câu này cosine 0.87 nên chắc chắn nói cùng một chuyện". Sai ở đâu?**

Hai chỗ: (a) 0.87 chỉ có nghĩa khi so với các cặp khác **cùng một model**, không có ngưỡng phổ
quát; (b) cosine cao chỉ nói **cùng chủ đề**, không nói **cùng khẳng định** — hai câu phủ định
của nhau vẫn cho cosine rất cao.
</details>

---

## 2. Ma trận và phép nhân ma trận — đủ để hiểu Q, K, V

### 2.1. Ma trận là gì — ví dụ đời thường

Một vector là **một dòng số**. Xếp nhiều dòng chồng lên nhau thì thành **ma trận** — nói cách
khác, ma trận là **cái bảng Excel toàn số**.

```
                    Toan   Ly   Hoa
                   +-----------------+
        Nam        |   8    7    9   |      <-- hang 1 = vector cua Nam
        Hoa        |   9    6    7   |      <-- hang 2 = vector cua Hoa
                   +-----------------+
                       ^
                       +-- cot 1 = diem Toan cua ca lop
```

Ma trận này có **2 hàng, 3 cột** → ta nói nó có **kích thước 2×3** (đọc: "hai nhân ba").

| Ký hiệu | Nghĩa |
|---|---|
| `A` (chữ in hoa) | một ma trận |
| `A` cỡ `m × n` | có `m` **hàng**, `n` **cột**. **Luôn đọc hàng trước, cột sau** |
| `A[i][j]` hoặc `A_ij` | số ở **hàng i, cột j**. Ở bảng trên `A[2][1] = 9` (Hoa, Toán) |
| `Aᵀ` (chữ T nhỏ) | **chuyển vị** — lật bảng qua đường chéo: hàng thành cột |

Chuyển vị nhìn thế này, không cần nhớ gì thêm:

```
        A (2x3)                       A^T (3x2)
     +-------------+                +---------+
     | 8   7   9   |     --->       | 8    9  |
     | 9   6   7   |                | 7    6  |
     +-------------+                | 9    7  |
                                    +---------+
     2 hang, 3 cot                  3 hang, 2 cot
```

**Trong LLM, ma trận xuất hiện ở đâu?** Một câu 3 chữ, mỗi chữ là vector 3 chiều → cả câu là
ma trận 3×3. Một batch 32 câu → cứ thế chồng lên. Đó là lý do GPU sinh ra: nó nhân ma trận rất nhanh.

### 2.2. Phép nhân ma trận — chỉ là dot product lặp lại

**Đây là điểm mấu chốt:** nhân ma trận **không phải** nhân từng ô tương ứng. Quy tắc là
**"hàng nhân cột"** — mỗi ô kết quả là **một dot product** (đúng cái bạn học ở mục 1).

```
       C = A x B

       o C[i][j]  =  (hang i cua A)  ·  (cot j cua B)
                      \_____________/    \___________/
                        mot vector         mot vector
                              \               /
                               +-- dot product --> MOT SO
```

**Điều kiện bắt buộc — kiểm tra bằng mắt:**

```
        A (m x n)   x   B (n x p)   =   C (m x p)
              ^ ^         ^   ^            ^   ^
              | |         |   |            |   |
              | +---------+   |            |   |
              |  PHAI BANG    |            |   |
              |  NHAU         |            |   |
              +---------------|------------+   |
                 lay m cua A  +----------------+
                                 lay p cua B

   -> So COT cua ma tran trai phai bang so HANG cua ma tran phai.
   -> Ket qua co so HANG cua trai, so COT cua phai.
```

Đây chính là lỗi `shape mismatch` bạn sẽ gặp suốt ngày khi code. 90% trường hợp là bạn quên
chuyển vị (`.T`) một cái.

### 2.3. Ví dụ số — tự tính tay

```
   A (2x3)              B (3x2)
   +-----------+        +--------+
   | 1   2   0 |        | 1    0 |
   | 0   1   3 |        | 2    1 |
   +-----------+        | 0    4 |
                        +--------+

   Kiem tra: A la 2x3, B la 3x2 -> 3 = 3, hop le. Ket qua se la 2x2.
```

Tính từng ô, mỗi ô là một dot product:

```
   C[1][1] = hang1(A) · cot1(B) = [1,2,0] · [1,2,0] = 1·1 + 2·2 + 0·0 = 5
   C[1][2] = hang1(A) · cot2(B) = [1,2,0] · [0,1,4] = 1·0 + 2·1 + 0·4 = 2
   C[2][1] = hang2(A) · cot1(B) = [0,1,3] · [1,2,0] = 0·1 + 1·2 + 3·0 = 2
   C[2][2] = hang2(A) · cot2(B) = [0,1,3] · [0,1,4] = 0·0 + 1·1 + 3·4 = 13

                 C (2x2)
              +-----------+
              |  5     2  |
              |  2    13  |
              +-----------+
```

**Cách đọc kết quả này theo ngôn ngữ AI:** coi mỗi **hàng của A là một token** (2 token, mỗi
token 3 chiều), coi **B là ma trận trọng số W** mà model đã học được. Thế thì:

```
   token 1 = [1, 2, 0]  --- nhan W --->  [5,  2]     <-- token 1 sau khi bien doi
   token 2 = [0, 1, 3]  --- nhan W --->  [2, 13]     <-- token 2 sau khi bien doi
```

Một phép nhân ma trận = **biến đổi toàn bộ token cùng một lúc, bằng cùng một bộ trọng số**.
Đó là toàn bộ "phép màu" của mạng nơ-ron: nhân ma trận → bóp méo phi tuyến → lặp lại vài chục lần.

### 2.4. Q, K, V trong attention

**Ẩn dụ thư viện — nhớ cái này là hiểu attention:**

```
   Ban vao thu vien tim tai lieu.

     Q (Query)  = CAU HOI ban dang can        "toi can biet AI dang ngu?"
     K (Key)    = NHAN DAN tren gay sach      "sach nay noi ve con meo"
     V (Value)  = NOI DUNG that trong sach    "meo la dong vat co vu, ..."

   Cach lam:  so CAU HOI voi tung NHAN DAN  ->  ra diem giong nhau
              diem cao thi lay nhieu NOI DUNG cua sach do, diem thap lay it
              tron tat ca lai -> do la cau tra loi.
```

Trong Transformer, **mỗi token đều làm cả 3 vai cùng lúc**: nó có câu hỏi riêng (Q), có nhãn dán
riêng (K), và có nội dung riêng (V). Ba thứ đó sinh ra bằng **ba phép nhân ma trận** đúng như mục 2.3:

```
        X                W_Q             W_K             W_V
   (n token x d)     (d x d_k)       (d x d_k)       (d x d_v)
        |                 |               |               |
        +--- X · W_Q ---> Q              |               |
        +--- X · W_K -----------------> K               |
        +--- X · W_V -----------------------------> V

   X   = cac token dau vao (moi hang mot token)
   W_Q, W_K, W_V = BA ma tran trong so, chinh la thu model HOC duoc khi train
   d   = so chieu embedding,  d_k = so chieu cua Q va K,  d_v = so chieu cua V
```

**Công thức attention đầy đủ:**

```
                              Q · Kᵀ
   Attention(Q,K,V) = softmax( -------- ) · V
                                √d_k
```

**Dịch từng ký hiệu:**

| Ký hiệu | Nghĩa |
|---|---|
| `Q · Kᵀ` | mỗi câu hỏi **chấm** với mọi nhãn dán → bảng **điểm giống nhau** giữa mọi cặp token |
| `Kᵀ` | phải chuyển vị thì kích thước mới khớp để nhân (mục 2.2) |
| `√d_k` | căn bậc hai của **số chiều** vector K — xem lý do ở 2.6 |
| `softmax(...)` | biến bảng điểm thành **tỉ lệ phần trăm cộng lại bằng 1** (mục 3) |
| `... · V` | dùng tỉ lệ đó **trộn** các V lại → kết quả cuối |

Toàn bộ attention chỉ là: **dot product để chấm điểm → softmax để chia tỉ lệ → nhân để trộn**.

### 2.5. Ví dụ số — attention cho câu "con mèo ngủ"

Giả sử sau khi nhân `X` với `W_Q, W_K, W_V` (đúng như mục 2.3) ta thu được:

```
   token       K (nhan dan)      V (noi dung)
   ---------------------------------------------
   "con"       [1, 0]            [1, 0, 0]
   "meo"       [2, 1]            [0, 2, 0]
   "ngu"       [0, 1]            [0, 0, 3]

   Ta dang tinh cho token "ngu", query cua no:   q = [1, 1]
```

**Bước 1 — chấm điểm `q · k` với từng token:**

```
   voi "con":  [1,1] · [1,0] = 1·1 + 1·0 = 1
   voi "meo":  [1,1] · [2,1] = 1·2 + 1·1 = 3     <-- diem cao nhat
   voi "ngu":  [1,1] · [0,1] = 1·0 + 1·1 = 1

   diem tho  =  [ 1 , 3 , 1 ]
```

**Bước 2 — softmax để đổi thành tỉ lệ** (cách tính chi tiết ở mục 3):

```
   softmax([1, 3, 1]) = [0.107, 0.787, 0.107]      (cong lai = 1.0)

   "con"  |####                                    | 10.7%
   "meo"  |###############################         | 78.7%
   "ngu"  |####                                    | 10.7%
```

Đọc bằng tiếng Việt: *khi xử lý chữ "ngủ", model dồn 79% sự chú ý vào chữ "mèo"* — hợp lý,
vì muốn hiểu "ngủ" thì phải biết **ai** ngủ.

**Bước 3 — trộn V theo tỉ lệ đó:**

```
   ket qua = 0.107 · [1,0,0]  +  0.787 · [0,2,0]  +  0.107 · [0,0,3]

           = [0.107, 0,     0    ]
           + [0,     1.574, 0    ]
           + [0,     0,     0.320]
           -------------------------
           = [0.107, 1.574, 0.320]
```

Vector `[0.107, 1.574, 0.320]` là biểu diễn mới của chữ "ngủ" — **đã ngấm thông tin từ chữ "mèo"**.
Đó chính là câu "token nhìn nhau" mà người ta hay nói về Transformer.

### 2.6. Vì sao phải chia cho √d_k

Nếu `d_k` lớn (thực tế 64 hoặc 128), dot product là tổng của rất nhiều số hạng nên **giá trị bị
phình to**. Điểm quá to đưa vào softmax sẽ ra phân bố **gần như 0/1** — model chỉ nhìn đúng một
token, và gradient gần như bằng 0 (bão hoà) → không học được.

So sánh trên chính ví dụ trên (`d_k = 2`, nên `√d_k ≈ 1.41`):

```
   khong chia:   diem = [1, 3, 1]           -> softmax = [0.107, 0.787, 0.107]
   co chia 1.41: diem = [0.71, 2.12, 0.71]  -> softmax = [0.164, 0.673, 0.164]
                                                          \___ mem hon, dan deu hon
```

Chia cho `√d_k` kéo điểm về khoảng an toàn để softmax không bão hoà. Chấm hết — không có ý nghĩa
huyền bí nào khác.

<details><summary><b>Tự kiểm tra mục 2 — bấm để xem đáp án</b></summary>

**Câu 1. Nhân được `A (4×5)` với `B (5×2)` không? Kết quả cỡ bao nhiêu? Còn `B × A` thì sao?**

Được: `5 = 5` → kết quả `4×2`. `B × A` thì `B` có 2 cột mà `A` có 4 hàng → `2 ≠ 4`, **không nhân
được**. Nhân ma trận **không giao hoán**, đổi thứ tự là hỏng.

**Câu 2. Nói bằng một câu: Q, K, V là gì?**

Q là câu hỏi mỗi token đặt ra, K là nhãn dán mỗi token tự mô tả mình, V là nội dung thật mỗi token
mang theo. Chấm Q với K ra mức liên quan, dùng mức đó trộn V lại.

**Câu 3. `Q · Kᵀ` cho ra ma trận cỡ bao nhiêu, với n token?**

`n × n` — mỗi token chấm điểm với **mọi** token khác. Đây cũng là lý do attention tốn bộ nhớ theo
`n²`, và vì sao context window dài lại đắt.

**Câu 4. Bỏ `√d_k` đi thì hỏng chuyện gì?**

Điểm số phình to theo số chiều → softmax bão hoà thành gần 0/1 → model chỉ chú ý đúng một token và
gradient tắt ngấm, train không nổi.

**Câu 5. Chỉ số hàng-cột: trong ma trận 2×3 ở đầu mục, `A[1][3]` là số nào?**

Hàng 1, cột 3 → điểm Hoá của Nam → `9`.
</details>

---

## 3. Softmax — biến điểm số thành xác suất, và temperature

### 3.1. Vấn đề — ví dụ đời thường

Ba quán ăn được ban giám khảo chấm điểm: `[2, 1, 0]`. Câu hỏi: *"nếu bốc ngẫu nhiên theo mức ngon,
xác suất mỗi quán được chọn là bao nhiêu %?"*

Điểm thô không dùng làm xác suất được, vì:

- Xác suất phải **không âm** — mà điểm số model xuất ra thường có số âm (`-3.2`).
- Xác suất phải **cộng lại đúng bằng 1** (100%) — mà `2 + 1 + 0 = 3`.

Cần một cái máy biến "dãy điểm bất kỳ" thành "dãy xác suất hợp lệ". Máy đó tên là **softmax**.

```
     DIEM THO (logits)              SOFTMAX                XAC SUAT
   +-------------------+        +-------------+       +------------------+
   |  2.0              |        |             |       |  0.665   (66.5%) |
   | -1.5   co the am  | -----> |  e^x roi    | ----> |  0.245   (24.5%) |
   |  0.7   tong tuy y |        |  chia tong  |       |  0.090   ( 9.0%) |
   +-------------------+        +-------------+       +------------------+
                                                        tat ca > 0
                                                        cong lai = 1.0
```

Trong LLM, "điểm thô" gọi là **logits** — model xuất ra một logit cho **mỗi token trong từ điển**
(cỡ 100.000 - 200.000 số). Softmax biến chúng thành xác suất để chọn chữ tiếp theo.

### 3.2. Công thức

```
                        e^(z_i)
   softmax(z)_i  =  ---------------
                     Σ(j) e^(z_j)
```

**Dịch từng ký hiệu:**

| Ký hiệu | Nghĩa |
|---|---|
| `z` | vector điểm thô (logits), ví dụ `[2, 1, 0]` |
| `z_i` | điểm thô của lựa chọn **thứ i** — cái ta đang tính xác suất |
| `e` | hằng số Euler ≈ **2.71828**. Chỉ là một con số, như `π` |
| `e^(z_i)` | e mũ z_i. `e^0 = 1`, `e^1 = 2.718`, `e^2 = 7.389` |
| `Σ(j) e^(z_j)` | cộng `e^(z_j)` của **tất cả** lựa chọn — đây là mẫu số chung |
| Kết quả | xác suất của lựa chọn i, luôn trong `(0, 1)`, tất cả cộng lại `= 1` |

Đọc thành lời: *"lấy e mũ điểm của mình, chia cho tổng e mũ điểm của tất cả mọi người."*
Y hệt cách tính **tỉ lệ phiếu bầu**, chỉ khác là mỗi phiếu được đi qua hàm `e^x` trước.

### 3.3. Vì sao dùng hàm mũ `e^x`?

Bốn lý do, xếp theo mức độ quan trọng khi trả lời phỏng vấn:

**(1) Nó biến mọi số thành số DƯƠNG.** Đây là lý do bắt buộc. Xác suất không được âm, mà logits thì
có âm. Hàm `e^x` luôn cho kết quả `> 0`, kể cả với `x` âm rất sâu:

```
   e^x
    ^
  8 |                                    .*     e^2  = 7.39
    |                                 .*
  6 |                              .*
    |                          .*
  4 |                      .*
    |                  .*                       e^0  = 1
  2 |            .*
    |     ..*                                   e^-2 = 0.135  (nho, nhung VAN > 0)
  0 +--*--*--*--*--*--*--*--*--*--*--*---> x
   -3   -2   -1    0    1    2    3

   Duong cong KHONG BAO GIO cham truc ngang -> khong bao giờ ra 0 hay so am.
```

**(2) Nó biến chênh lệch CỘNG thành chênh lệch NHÂN.** Tính chất `e^(a+b) = e^a · e^b` nghĩa là:
điểm hơn nhau **1 đơn vị** thì xác suất **gấp e ≈ 2.72 lần**; hơn 2 đơn vị thì gấp `e² ≈ 7.4 lần`.
Đây đúng là hành vi ta muốn: *hơn một chút thì được ưu tiên hẳn*, chứ không phải hơn tí xíu.
(Nếu chỉ chia thẳng `z_i / Σz_j` thì `[2,1,0]` ra `[0.67, 0.33, 0]` — và một điểm âm sẽ phá vỡ tất cả.)

**(3) Chỉ chênh lệch mới quan trọng, không phải giá trị tuyệt đối.** Cộng thêm cùng một số vào **mọi**
logit thì kết quả softmax **không đổi** (thừa số chung triệt tiêu ở tử và mẫu). Nhờ vậy code thật
luôn trừ đi giá trị lớn nhất trước khi mũ — tránh `e^1000` tràn số. Đó là mẹo **numerical stability**.

**(4) Nó mượt và đạo hàm rất đẹp.** Softmax là hàm trơn (mục 5 sẽ nói vì sao cần trơn), và khi ghép
với hàm mất mát cross-entropy, đạo hàm rút gọn thành đúng `(xác suất dự đoán − nhãn đúng)`. Gọn đến
mức đó là lý do cả ngành dùng cặp softmax + cross-entropy.

### 3.4. Ví dụ số — tự tính tay

Với `z = [2, 1, 0]`:

```
   Buoc 1 - mu len:     e^2 = 7.389
                        e^1 = 2.718
                        e^0 = 1.000

   Buoc 2 - cong tong:  7.389 + 2.718 + 1.000 = 11.107

   Buoc 3 - chia:       7.389 / 11.107 = 0.665     (66.5%)
                        2.718 / 11.107 = 0.245     (24.5%)
                        1.000 / 11.107 = 0.090     ( 9.0%)

   Kiem tra: 0.665 + 0.245 + 0.090 = 1.000  ✔
```

### 3.5. Temperature — núm vặn "sáng tạo"

**Công thức:** chỉ thêm một phép chia trước khi làm softmax.

```
                             e^(z_i / T)
   softmax_T(z)_i  =  ---------------------
                        Σ(j) e^(z_j / T)
```

| Ký hiệu | Nghĩa |
|---|---|
| `T` | **temperature** (nhiệt độ), một số dương do bạn đặt. Mặc định `T = 1` |
| `z_i / T` | chia điểm cho T **trước khi** mũ. `T` nhỏ → điểm bị **kéo giãn ra** → chênh lệch to hơn |

Trực giác: **T là cái núm bóp/giãn khoảng cách giữa các điểm số.**

```
    T nho (0.2)          T = 1 (goc)          T lon (2.0)
    "bop chat"            "nguyen ban"         "keo giai deu"

     |#                    |#                   |#
     |#                    |#                   |#  #
     |#                    |#  #                |#  #  #
     |#  .  .              |#  #  .             |#  #  #
     +--------             +--------            +--------
      A  B  C               A  B  C              A  B  C

   gan nhu luon chon A   theo dung diem so    B, C cung hay duoc chon
   -> lap lai, an toan   -> can bang          -> sang tao, de bia
```

**Bảng số cụ thể** với `z = [2, 1, 0]`:

| T | z / T | e^(z/T) | Tổng | Xác suất |
|---|---|---|---|---|
| **0.5** | `[4, 2, 0]` | `54.60, 7.39, 1.00` | 62.99 | **`[0.867, 0.117, 0.016]`** |
| **1.0** | `[2, 1, 0]` | `7.39, 2.72, 1.00` | 11.11 | **`[0.665, 0.245, 0.090]`** |
| **2.0** | `[1, 0.5, 0]` | `2.72, 1.65, 1.00` | 5.37 | **`[0.506, 0.307, 0.186]`** |

Đọc bảng theo cột cuối: lựa chọn hạng nhất đi từ **86.7% → 66.5% → 50.6%** khi T tăng. Càng nóng,
model càng dễ chọn phương án lạ.

**Hai trường hợp cực đoan cần nói được:**

- `T → 0`: chênh lệch bị phóng đại vô hạn → xác suất của phương án cao điểm nhất **tiến tới 1**.
  Đây là **greedy / argmax**: luôn chọn chữ khả dĩ nhất, chạy lại cho kết quả y hệt. (API thường
  hiện thực `temperature=0` bằng cách chọn thẳng argmax, vì chia cho 0 là không hợp lệ.)
- `T → ∞`: mọi `z_i/T` tiến về 0, mọi `e^0 = 1` → xác suất **đều nhau tuyệt đối** = bốc ngẫu nhiên,
  văn bản thành cháo.

**Ứng dụng thực tế:** trích xuất dữ liệu / phân loại / gọi tool → `T = 0` cho ổn định, lặp lại được.
Viết quảng cáo, brainstorm → `T = 0.7 – 1.0`. Trên `1.2` thường bắt đầu sai ngữ pháp và bịa.

> **Phân biệt với `top_p`:** temperature **bóp méo hình dạng** của phân bố rồi mới bốc; `top_p`
> (nucleus sampling) **cắt bỏ đuôi** — chỉ giữ các token có xác suất cộng dồn tới `p` rồi mới bốc.
> Hai núm khác nhau; thường chỉ nên vặn một cái.

**Softmax xuất hiện đúng hai chỗ trong LLM — nhớ để khỏi lẫn:**

```
   1) Trong ATTENTION  ->  chia ti le CHU Y giua cac token   (muc 2.5)
   2) O LOP CUOI       ->  chia ti le XAC SUAT chon chu tiep theo
                           <-- temperature tac dong o day
```

<details><summary><b>Tự kiểm tra mục 3 — bấm để xem đáp án</b></summary>

**Câu 1. `softmax([0, 0, 0])` bằng bao nhiêu? Không tính máy.**

`e^0 = 1` cho cả ba → `[1/3, 1/3, 1/3]`. Điểm bằng nhau thì xác suất chia đều.

**Câu 2. `softmax([12, 11, 10])` có bằng `softmax([2, 1, 0])` không?**

**Có** — bằng chính xác. Cộng thêm 10 vào tất cả logits không đổi kết quả; chỉ **hiệu** giữa các
logit mới quan trọng. Đây cũng là mẹo tránh tràn số.

**Câu 3. Vì sao không chia thẳng `z_i / Σ z_j` cho nhanh?**

Vì logits có thể **âm** (ra xác suất âm — vô nghĩa) và tổng có thể bằng 0 (chia cho 0). Ngoài ra
cách đó không tạo được hiệu ứng "hơn một chút thì ưu tiên hẳn" mà `e^x` mang lại.

**Câu 4. Bug: chatbot hỗ trợ khách hàng thỉnh thoảng bịa số điện thoại. Vặn núm nào trước?**

Hạ **temperature** về 0 (hoặc gần 0) để model bám phương án chắc chắn nhất. Nếu vẫn bịa thì lỗi
không nằm ở sampling mà ở **ngữ cảnh** — phải đưa dữ liệu thật vào prompt (RAG).

**Câu 5. Temperature có làm model "thông minh hơn" không?**

Không. Nó không đổi logits mà model tính ra, chỉ đổi **cách bốc** từ chúng. Kiến thức y nguyên, chỉ
khác mức liều lĩnh khi chọn.
</details>

---

## 4. Xác suất, log-likelihood, perplexity — LLM tối ưu cái gì

### 4.1. Xác suất cơ bản — đúng 3 điều cần nhớ

```
   1)  P(A)  la mot so tu 0 den 1        0 = khong bao gio, 1 = chac chan
   2)  Cong tat ca kha nang lai = 1      troi mua 30% -> troi khong mua 70%
   3)  P(B | A) = "xac suat B, VOI DIEU KIEN da biet A"      <-- quan trong nhat
```

Dấu `|` đọc là **"khi biết"**, không phải phép chia. Ví dụ đời thường:

```
   P(uot ao)                  = 10%     <-- khong biet gi them
   P(uot ao | troi dang mua)  = 80%     <-- da biet troi mua thi doan khac han
                   ^
                   +-- "khi biet rang"
```

**Đây chính xác là việc LLM làm.** Một LLM là một cái máy tính đúng một thứ:

```
   P( chu tiep theo  |  toan bo cac chu da co truoc do )
```

Ví dụ, cho ngữ cảnh `"Hà Nội là thủ đô của"`, model xuất ra xác suất cho **mọi** token trong từ điển:

```
   "Viet"     |################################  |  0.72
   "nuoc"     |######                            |  0.14
   "mot"      |##                                |  0.05
   "banh"     |.                                 |  0.0001
   ... (con ~150.000 token khac, moi cai mot con so)
                                       tat ca cong lai = 1.00
```

### 4.2. Xác suất của cả một câu

Xác suất của cả câu = **nhân** xác suất từng chữ, mỗi chữ tính với điều kiện là các chữ đứng trước:

```
   P("con meo ngu")  =  P("con")
                      x P("meo" | "con")
                      x P("ngu" | "con meo")
```

Quy tắc này gọi là **chain rule** (quy tắc dây chuyền). Nó là toàn bộ lý do LLM sinh chữ **từ trái
sang phải, từng chữ một**: muốn tính chữ sau thì phải có chữ trước.

**Ví dụ số** — giả sử model của ta cho:

```
   P("con")             = 0.5
   P("meo" | "con")     = 0.25
   P("ngu" | "con meo") = 0.5

   P(ca cau) = 0.5 x 0.25 x 0.5 = 0.0625      (tuc 1/16)
```

### 4.3. Vì sao phải lấy log

Một câu thật dài 1000 token, mỗi token xác suất cỡ `0.1`. Nhân 1000 số nhỏ với nhau:

```
   0.1 x 0.1 x 0.1 x ... (1000 lan)  =  10^(-1000)
                                         ^
                                         may tinh lam tron thanh 0 -> mat sach thong tin
```

Đó gọi là **underflow**. Cách chữa: **lấy logarit**.

**Log là gì — giải thích từ mất gốc:** `log` trả lời câu hỏi *"phải mũ lên bao nhiêu lần?"*

```
   log2(8)  = 3     vi  2^3 = 8       ("2 mu MAY thi ra 8?" -> 3)
   log2(1)  = 0     vi  2^0 = 1
   log2(0.5)= -1    vi  2^(-1) = 1/2  <-- xac suat < 1 thi log AM
   log2(0.25) = -2  vi  2^(-2) = 1/4
```

Tính chất vàng khiến cả ngành dùng log:

```
   log(a x b)  =  log(a) + log(b)          NHAN  bien thanh  CONG
```

Nhân 1000 số bé → biến thành cộng 1000 số vừa phải. Máy tính cộng thì không tràn số. Và vì log là
hàm **luôn tăng**, cái gì làm xác suất lớn nhất cũng làm log của nó lớn nhất → tối ưu log thay cho
tối ưu xác suất là **hoàn toàn tương đương**.

### 4.4. Log-likelihood và hàm mất mát

**Log-likelihood** (log của độ khả dĩ) = log của xác suất mà model gán cho dữ liệu thật:

```
   log P(cau)  =  Σ(i=1..n)  log P( token_i | cac token truoc no )
```

| Ký hiệu | Nghĩa |
|---|---|
| `n` | số token trong câu |
| `token_i` | token **thứ i** — token **thật** trong dữ liệu huấn luyện (đáp án đúng) |
| `Σ` | cộng dồn qua tất cả token |
| Giá trị | luôn **âm** (vì log của số < 1 là âm). Càng **gần 0** càng tốt |

Việc huấn luyện đặt ra mục tiêu: **làm cho log-likelihood lớn nhất có thể**. Do quy ước máy học là
"giảm thiểu hàm mất mát", người ta đảo dấu và chia trung bình:

```
                     1
   Loss  =  NLL  =  --- x ( - Σ(i) log P(token_i | truoc do) )
                     n
                     ^         ^
                     |         +-- dau tru: doi tu "cang lon cang tot"
                     |             sang "cang nho cang tot"
                     +-- chia n: lay trung binh moi token, de cau dai
                         cau ngan so sanh duoc voi nhau
```

`NLL` = Negative Log-Likelihood. Với bài toán phân loại token (đúng cái LLM đang làm), NLL này
**chính là cross-entropy loss** mà bạn thấy trong mọi log training. Ba tên gọi, một thứ.

> **Câu trả lời cho "LLM thật ra đang tối ưu cái gì":**
> *"Nó tối ưu đúng một thứ — làm cho xác suất mà nó gán cho văn bản người thật viết cao nhất có thể.
> Nói cách khác: tối thiểu hoá cross-entropy giữa phân bố nó dự đoán và chữ thật ở mỗi vị trí."*
>
> Hệ quả cần nói tiếp, vì đây là chỗ ăn điểm: **nó không hề tối ưu tính đúng đắn, tính hữu ích hay
> an toàn**. Một câu bịa nghe trôi chảy vẫn có xác suất cao. Đó là lý do gốc rễ của **ảo giác
> (hallucination)**, và là lý do phải có thêm giai đoạn **RLHF / instruction tuning** sau pretrain.

### 4.5. Perplexity — tự tính tay

**Perplexity (PPL)** biến con số loss khó hình dung thành một câu người thường hiểu được:

> *"Trung bình, model đang phân vân giữa bao nhiêu lựa chọn khi đoán chữ tiếp theo?"*

```
   PPL  =  2 ^ ( cross-entropy tinh bang bit )        <-- neu dung log co so 2
   PPL  =  e ^ ( cross-entropy tinh bang nat )        <-- neu dung log tu nhien (ln)

   (Hai cach cho ra CUNG mot so, mien la co so mu khop voi co so log.)
```

**Tính tay trên câu "con mèo ngủ"** ở mục 4.2:

```
   Buoc 1 - log2 tung xac suat:
       log2(0.5)  = -1
       log2(0.25) = -2
       log2(0.5)  = -1

   Buoc 2 - cong lai (log-likelihood):
       (-1) + (-2) + (-1) = -4          <-- tong 4 bit "bat ngo"

   Buoc 3 - doi dau, chia so token (cross-entropy):
       4 / 3 = 1.333 bit / token

   Buoc 4 - mu len:
       PPL = 2 ^ 1.333 = 2.52
```

**Đọc kết quả:** model này lúng túng cỡ như đang **tung đồng xu 2.5 mặt** ở mỗi chữ. Kiểm tra chéo
bằng đường tắt: `PPL = (1 / 0.0625)^(1/3) = 16^(1/3) = 2.52` ✔ — perplexity chính là **trung bình
nhân nghịch đảo** của các xác suất.

**Thang đo để nhớ:**

```
   PPL = 1        : hoan hao, model chac chan tuyet doi va luon dung
   PPL = 2.5      : nhu vi du tren, van con phan van
   PPL = 10 - 30  : vung cua cac LLM tot tren van ban thuong
   PPL = 150.000  : doan mo hoan toan (bang kich thuoc tu dien)

   PPL cang THAP  ->  model cang "khong bat ngo" truoc van ban that  ->  cang tot
```

**Ba lưu ý thực tế** (nói ra được là hiểu thật, không học vẹt):

- **Không so PPL giữa hai model khác tokenizer.** Cắt token khác nhau thì mẫu số `n` khác nhau,
  con số hết so sánh được.
- **PPL phụ thuộc tập test.** PPL trên Wikipedia và trên code là hai thế giới. Chỉ so sánh
  cùng model + cùng dữ liệu.
- **PPL thấp không có nghĩa là model hữu ích.** Nó chỉ đo khả năng đoán chữ tiếp theo, không đo
  làm theo chỉ dẫn, không đo tính đúng đắn. Vì thế thực tế phải đánh giá thêm bằng eval theo tác vụ
  và LLM-as-a-judge.

<details><summary><b>Tự kiểm tra mục 4 — bấm để xem đáp án</b></summary>

**Câu 1. Model gán xác suất `[0.5, 0.5]` cho 2 token của một câu. Loss (log2) và PPL bằng bao nhiêu?**

`log2(0.5) = -1` cho cả hai → tổng `-2` → cross-entropy `= 2/2 = 1` bit/token → `PPL = 2^1 = 2`.
Model đang phân vân giữa đúng 2 lựa chọn.

**Câu 2. Vì sao dùng log-likelihood chứ không dùng thẳng likelihood?**

Vì nhân hàng nghìn số nhỏ gây underflow (máy làm tròn về 0). Log biến tích thành tổng, và vì log là
hàm tăng nên chỗ tối ưu không đổi.

**Câu 3. PPL của model A là 12, của model B là 45. Kết luận gì? Cần hỏi thêm gì?**

Nếu **cùng tokenizer và cùng tập test** thì A đoán chữ tốt hơn. Phải hỏi đúng hai câu đó trước khi
kết luận — thiếu một trong hai thì phép so sánh vô nghĩa.

**Câu 4. Model đạt PPL rất thấp nhưng vẫn bịa tên riêng và số liệu. Mâu thuẫn không?**

Không mâu thuẫn. Mục tiêu huấn luyện là **giống văn bản thật**, không phải **nói thật**. Câu bịa
trôi chảy vẫn khớp mục tiêu đó. Muốn đúng sự thật phải cấp dữ kiện (RAG) hoặc căn chỉnh thêm (RLHF).

**Câu 5. `P(B | A)` — dấu gạch đứng có phải phép chia không?**

Không. Nó đọc là **"khi biết A"**. Toàn bộ LLM là `P(chữ tiếp theo | mọi chữ đứng trước)`.
</details>

---

## 5. Đạo hàm và gradient descent — learning rate là gì

### 5.1. Ví dụ đời thường: xuống núi trong sương mù

Bạn đứng trên sườn núi, sương mù dày đặc, chỉ nhìn được 1 mét quanh chân. Nhiệm vụ: **xuống đáy thung lũng**.

Chiến thuật duy nhất khả thi:

```
   1. Dua chan tham xem quanh minh ben nao DOC XUONG nhieu nhat
   2. Buoc mot buoc ve huong do
   3. Lap lai cho toi khi xung quanh phang (khong con doc)
```

Đó **chính xác** là gradient descent. Đổi từ ngữ:

| Trên núi | Trong máy học |
|---|---|
| Độ cao chỗ bạn đứng | **Loss** — model đang sai bao nhiêu |
| Toạ độ chỗ bạn đứng | **Tham số** (weights) của model |
| Hướng dốc dưới chân | **Gradient** |
| Độ dài mỗi bước chân | **Learning rate** |
| Đáy thung lũng | Bộ tham số làm loss nhỏ nhất |

### 5.2. Đạo hàm = độ dốc

**Đạo hàm của `f` tại điểm `w`** trả lời đúng một câu: *"nếu tôi nhích `w` lên một tí xíu, thì `f`
thay đổi bao nhiêu và theo chiều nào?"*

| Ký hiệu | Đọc là | Nghĩa |
|---|---|---|
| `f(w)` | "f của w" | hàm số — ở đây là loss, phụ thuộc tham số `w` |
| `f'(w)` | "f phẩy của w" | **đạo hàm** = độ dốc tại `w` |
| `df/dw` | "d f trên d w" | cách viết khác của cùng thứ đó |

Đọc dấu và độ lớn:

```
   f(w)
     ^
     |*                                              *
     | *          f'(w) < 0        f'(w) > 0        *      <-- doc len,
     |  *         doc XUONG        doc LEN         *           dao ham DUONG
     |   *        -> di sang PHAI |               *
     |    *                       |    (dao ham AM thi di phai,
     |      *                     v     dao ham DUONG thi di trai)
     |        *                 *
     |           *          *
     |               *  *
     +------------------*--------------------------> w
                    f'(w) = 0
                    day thung lung, HET DOC -> dung lai
```

Ta không cần biết cách tính đạo hàm bằng tay. Chỉ cần một công thức duy nhất cho ví dụ dưới đây, và
biết rằng thư viện (PyTorch) tự tính hộ toàn bộ phần này — đó là cái tên `autograd`.

**Gradient** chỉ là **đạo hàm khi có nhiều tham số cùng lúc**: thay vì một số, nó là một **vector**
gồm đạo hàm theo từng tham số. Với model 7 tỉ tham số, gradient là vector 7 tỉ chiều — mỗi thành
phần trả lời *"nếu chỉnh riêng tham số này thì loss đổi thế nào?"*.

### 5.3. Quy tắc cập nhật — trái tim của mọi việc huấn luyện

```
   w_moi  =  w_cu  -  lr  x  f'(w_cu)
```

| Ký hiệu | Nghĩa |
|---|---|
| `w_cu` | giá trị tham số hiện tại |
| `f'(w_cu)` | độ dốc tại chỗ đang đứng |
| `lr` | **learning rate** — bước chân dài bao nhiêu (số dương nhỏ, ví dụ `0.001`) |
| dấu `−` | **đi NGƯỢC dốc**: dốc lên thì lùi lại, dốc xuống thì tiến tới. Đây là chữ "descent" |

Toàn bộ quá trình huấn luyện một LLM là lặp lại đúng dòng này hàng triệu lần, cho hàng tỉ tham số.

### 5.4. Ví dụ số — tự tính tay từng bước

Lấy hàm đơn giản nhất: `f(w) = (w − 3)²`. Nhìn mắt thường cũng biết đáy ở `w = 3` (chỗ duy nhất
`f = 0`). Đạo hàm của nó là `f'(w) = 2(w − 3)` — chỉ cần chấp nhận công thức này.

Bắt đầu ở `w = 0` với `lr = 0.1`:

```
   Buoc 0:  w = 0
            f(0)  = (0-3)^2 = 9
            f'(0) = 2 x (0-3) = -6            <-- am -> dang o suon TRAI, phai di sang PHAI
            w_moi = 0 - 0.1 x (-6) = 0 + 0.6 = 0.6

   Buoc 1:  w = 0.6
            f'(0.6) = 2 x (0.6-3) = -4.8      <-- doc thoai hon -> buoc ngan hon
            w_moi   = 0.6 - 0.1 x (-4.8) = 1.08

   Buoc 2:  w = 1.08    f' = -3.84   ->  w_moi = 1.464
   Buoc 3:  w = 1.464   f' = -3.07   ->  w_moi = 1.771
   Buoc 4:  w = 1.771   f' = -2.46   ->  w_moi = 2.017
```

| Bước | `w` | `f(w)` = loss | `f'(w)` | bước đi |
|---|---|---|---|---|
| 0 | 0.000 | 9.000 | −6.00 | +0.60 |
| 1 | 0.600 | 5.760 | −4.80 | +0.48 |
| 2 | 1.080 | 3.686 | −3.84 | +0.38 |
| 3 | 1.464 | 2.359 | −3.07 | +0.31 |
| 4 | 1.771 | 1.510 | −2.46 | +0.25 |
| … | → 3.000 | → 0.000 | → 0 | → 0 |

```
   f(w)
  9 +*
    | *                                  DUONG DI XUONG DAY
  7 |  *
    |   *                                Cang gan day, DOC cang thoai,
  5 |    o                               nen BUOC TU DONG NGAN LAI.
    |     *o                             Khong can ai bao dung -
  3 |       * o                          toan hoc tu lam.
    |         *  o
  1 |            *   o   o
    |               * * * o o o *
  0 +---+---+---+---+---+---+---+---> w
    0   0.6 1.1 1.5 1.8       3
    ^                         ^
   bat dau                   day (f' = 0)
```

Điểm quan trọng cần thấy: **các bước tự ngắn dần** khi gần đáy, vì gradient nhỏ dần. Không ai phải
lập trình cái đó cả.

### 5.5. Learning rate — chọn sai là hỏng cả buổi train

Vẫn hàm đó, vẫn xuất phát `w = 0`, chỉ đổi `lr`:

```
   lr = 0.01  QUA NHO           lr = 0.5  VUA DEP         lr = 1.0  DAO DONG
   ------------------           -----------------          ------------------
   0.00 -> 0.06 -> 0.12         0.00 -> 3.00               0.00 -> 6.00 -> 0.00
   -> 0.18 -> ... rat lau       DEN DAY NGAY buoc 1        -> 6.00 -> 0.00 ...
   moi toi 3                                               nhay qua nhay lai MAI MAI

        *                            *                          *         *
         *  o o o o o                 *                           *      *
          *                            o------------> day          *    *
           *                            *                           *  *
            *      (bo mai)              *                           o o   <-- khong bao gio
             *  *                         *  *                      *   *      xuong duoc
```

```
   lr = 1.1  QUA LON -> NO (diverge)

   w:  0 -> 6.6 -> -1.32 -> 8.18 -> -3.22 -> 10.47 -> ...  cang ngay cang xa
   loss: 9 -> 12.96 -> 18.66 -> 26.87 -> 38.70 -> 55.8 -> ... -> NaN

        *                                                *
         *                                              *
          *          o                              o
           *              o                    o
            *                   o        o
             o------------------------------->  bay ra khoi thung lung
```

**Bảng đối chiếu triệu chứng — dùng được ngay khi đi làm:**

| Bạn nhìn thấy trong log | Nguyên nhân thường gặp | Xử lý |
|---|---|---|
| Loss giảm cực chậm, chạy cả ngày không nhúc nhích | `lr` quá nhỏ | tăng `lr` lên 3–10 lần |
| Loss nhảy lên xuống, không giảm ổn định | `lr` hơi lớn | giảm `lr`, bật warmup |
| Loss thành `NaN` hoặc `inf` sau vài bước | `lr` quá lớn (nổ) | giảm mạnh `lr`, thêm gradient clipping |
| Loss giảm rồi đứng ở mức cao | kẹt vùng phẳng / model quá nhỏ | dùng scheduler, đổi kiến trúc |

**Vài con số thực tế để có cảm giác:** fine-tune một LLM thường dùng `lr ≈ 1e-5` đến `5e-5` (bước
rất bé vì model **đã** ở gần đáy — đi mạnh là phá mất kiến thức cũ). Train từ đầu một model nhỏ
thì `1e-3` là bình thường. Thực tế người ta còn cho `lr` **thay đổi theo thời gian** (warmup tăng
dần rồi giảm dần — gọi là **learning rate schedule**), và dùng Adam/AdamW để tự chỉnh bước cho từng
tham số.

> **Một mảnh ghép nữa:** loss thật được tính trên **cả tập dữ liệu** thì quá đắt, nên mỗi bước ta chỉ
> lấy một **mẻ nhỏ (mini-batch)** để ước lượng gradient. Vì thế đường loss thực tế **răng cưa** chứ
> không mượt như hình trên — đó là chữ "Stochastic" trong **SGD**.

<details><summary><b>Tự kiểm tra mục 5 — bấm để xem đáp án</b></summary>

**Câu 1. Vì sao công thức cập nhật dùng dấu trừ?**

Vì gradient chỉ hướng **đi LÊN dốc** (loss tăng). Ta muốn loss **giảm** nên đi ngược lại → trừ.

**Câu 2. Với `f(w) = (w−3)²`, đang ở `w = 5`, `lr = 0.1`. Bước tiếp theo `w` bằng bao nhiêu?**

`f'(5) = 2(5−3) = +4` (dương → đang ở sườn phải). `w = 5 − 0.1×4 = 4.6` — dịch về phía 3. ✔

**Câu 3. Gradient khác đạo hàm chỗ nào?**

Đạo hàm dành cho **một** tham số (một số). Gradient là **vector** gộp đạo hàm theo **tất cả** tham
số — bản chất giống hệt, chỉ nhiều chiều hơn.

**Câu 4. Loss ra `NaN` ở epoch đầu. Nghi ngờ đầu tiên là gì?**

`lr` quá lớn làm bước nhảy vọt ra ngoài → số phình vô hạn. Giảm `lr`, thêm gradient clipping, kiểm
tra dữ liệu có giá trị bất thường không.

**Câu 5. Vì sao gần đáy thì bước tự ngắn lại dù `lr` không đổi?**

Vì bước đi `= lr × gradient`, mà gradient nhỏ dần khi tiến về đáy (chỗ phẳng). `lr` chỉ là hệ số nhân.
</details>

---

## 6. Trung bình, trung vị, phân vị — vì sao đo p95

### 6.1. Ví dụ đời thường: "lương trung bình công ty tôi 50 triệu"

Một công ty 10 người: 9 nhân viên lương 20 triệu, ông chủ lương 320 triệu.

```
   Luong trung binh = (20 x 9 + 320) / 10 = 50 trieu

   Nhung: KHONG MOT AI trong cong ty nhan 50 trieu.
          9/10 nguoi nhan 20. Con so 50 mo ta dung 0 nguoi.
```

Đó là bài học cốt lõi của cả mục này: **trung bình bị một giá trị cực đoan kéo đi, và có thể mô tả
sai toàn bộ đám đông.** Hệ thống của bạn cũng vậy — chỉ đổi "lương" thành "độ trễ".

### 6.2. Ba thước đo

**Trung bình (mean / average):**

```
                x_1 + x_2 + ... + x_n           1
   trung binh = ---------------------   =   --- Σ(i=1..n) x_i
                          n                  n
```

| Ký hiệu | Nghĩa |
|---|---|
| `x_i` | giá trị thứ i (ví dụ: độ trễ của request thứ i) |
| `n` | tổng số giá trị |
| Đặc điểm | **mọi** giá trị đều tham gia → **một** outlier đủ sức kéo lệch |

**Trung vị (median):** xếp tất cả theo thứ tự tăng dần rồi lấy **giá trị đứng chính giữa**.

```
   n le  -> lay so o giua                       [1, 3, 100]      -> 3
   n chan -> lay trung binh 2 so giua           [1, 3, 5, 100]   -> (3+5)/2 = 4
```

Đặc điểm: chỉ quan tâm **thứ hạng**, không quan tâm độ lớn. Đổi `100` thành `1.000.000` thì trung vị
**không đổi một chút nào**. Người ta gọi tính chất này là **robust** (kháng nhiễu).

**Phân vị (percentile):** `pK` = giá trị mà **K% dữ liệu nằm dưới hoặc bằng nó**.

```
   p50  = trung vi (dinh nghia khac cua cung mot thu)
   p95  = 95% request nhanh hon hoac bang muc nay,  5% cham hon
   p99  = 99% nhanh hon,  1% cham hon
```

Cách tính đơn giản nhất (**nearest-rank**): sắp xếp tăng dần rồi lấy phần tử ở vị trí
`ceil(K/100 × n)` — `ceil` là **làm tròn LÊN**.

### 6.3. Ví dụ số — độ trễ 10 request

Dữ liệu (đã sắp xếp, đơn vị ms) — 9 request bình thường, 1 request rơi vào lúc GC/retry:

```
   [ 100, 110, 120, 130, 140, 150, 160, 170, 180, 2000 ]
     vi tri: 1    2    3    4    5    6    7    8    9    10
```

**Trung bình:**

```
   Tong = 100+110+120+130+140+150+160+170+180 = 1260
   1260 + 2000 = 3260
   Trung binh = 3260 / 10 = 326 ms
```

**Trung vị:** `n = 10` (chẵn) → lấy hai số giữa là vị trí 5 và 6:

```
   (140 + 150) / 2 = 145 ms
```

**p90:** `ceil(0.90 × 10) = ceil(9) = 9` → phần tử thứ 9 = **180 ms**
**p95:** `ceil(0.95 × 10) = ceil(9.5) = 10` → phần tử thứ 10 = **2000 ms**

**Biểu đồ phân bố — nhìn là hiểu ngay vì sao trung bình vô dụng ở đây:**

```
   so request
      ^
    2 |  #    #    #
      |  #    #    #
    1 |  #  # #  # #  #                                                    #
      +--+--+-+--+-+--+---------------------------------------------------+--->
        100 120 140 160 180                                              2000  ms
        \____________________/                                            \_/
          9 request o day                                            1 request o day
                                                                     ("duoi dai")

        ^              ^                    ^
        |              |                    |
      p50=145      (khong co gi           TRUNG BINH = 326
      trung vi      o day, nhung           <-- bi keo len boi DUNG MOT diem,
                    trung binh                 va no ROI VAO CHO TRONG
                    nam o day)
```

**Bảng tổng kết — cùng một dữ liệu, ba câu chuyện khác nhau:**

| Thước đo | Giá trị | Nó nói gì | Nó giấu gì |
|---|---|---|---|
| Trung bình | **326 ms** | "hệ thống chậm vừa" | Sai cả hai đầu: không ai chậm 326ms |
| Trung vị (p50) | **145 ms** | "trải nghiệm điển hình rất tốt" | Giấu sạch trường hợp 2000ms |
| p90 | **180 ms** | "10% người dùng chậm hơn 180ms" | Vẫn chưa lộ đuôi |
| **p95** | **2000 ms** | **"cứ 20 request thì có 1 lần chờ 2 giây"** | — đây là thứ user thực sự nhớ |

### 6.4. Vì sao đo p95 chứ không đo trung bình

Năm lý do, xếp theo sức nặng khi trả lời phỏng vấn:

1. **Trung bình có thể trỏ vào vùng không tồn tại.** Như ví dụ trên: 326 ms là con số **không request
   nào từng đạt**. Phân phối độ trễ luôn **lệch phải** (có sàn cứng ~0 ms, nhưng không có trần), nên
   trung bình luôn bị đuôi kéo lên.
2. **Người dùng nhớ lần chậm, không nhớ lần trung bình.** Trải nghiệm tệ khắc sâu hơn 19 lần mượt mà.
3. **Một người dùng chạm nhiều request.** Một trang gọi 20 API; nếu mỗi API có 5% chậm thì xác suất
   người đó gặp **ít nhất một** lần chậm là `1 − 0.95²⁰ ≈ 64%`. "Đuôi 5%" hoá ra là **đa số phiên**.
4. **Trung bình che mất hồi quy hiệu năng.** Thêm một lỗi làm 3% request treo 5 giây gần như không
   nhích trung bình, nhưng p95/p99 nhảy dựng lên — báo động sớm nằm ở đuôi.
5. **SLA/SLO viết bằng phân vị.** "95% request dưới 500 ms" là cam kết kiểm chứng được. "Trung bình
   dưới 500 ms" là cam kết có thể đúng trong khi 10% người dùng chờ 10 giây.

> **Riêng với hệ thống LLM, đuôi còn dày hơn nữa:** thời gian phản hồi phụ thuộc **số token sinh ra**
> (câu trả lời dài gấp 5 thì lâu gấp 5), cộng với retry khi rate-limit, cold start, hàng đợi.
> Vì thế trong dự án LLM người ta còn tách riêng **TTFT** (time to first token — đo cảm giác "máy có
> phản hồi không") và **tổng thời gian**, và luôn theo dõi cả hai theo p95/p99.

**Ba cái bẫy về phân vị nên biết:**

```
   1) KHONG duoc lay trung binh cua cac p95!
      Server A p95 = 100ms, Server B p95 = 900ms  ->  p95 toan he KHONG PHAI 500ms.
      Muon dung phai gop du lieu tho (hoac dung histogram) roi tinh lai.

   2) p99 can DU MAU.
      Chi co 50 request thi "p99" chi la 1 diem duy nhat - do la nhieu, khong phai tin hieu.

   3) Phai gan p95 voi CUA SO THOI GIAN.
      "p95 = 200ms" ma khong noi "trong 5 phut qua" thi khong dung de canh bao duoc.
```

> **Nhắc nhanh về độ phân tán:** ngoài vị trí trung tâm, người ta còn mô tả **độ tản** bằng
> **độ lệch chuẩn (std)** — trung bình khoảng cách từ các điểm tới giá trị trung bình. Nhưng std
> cũng bị outlier kéo giống mean, nên với dữ liệu độ trễ, **bộ p50/p95/p99 vẫn là mô tả trung thực nhất**.

<details><summary><b>Tự kiểm tra mục 6 — bấm để xem đáp án</b></summary>

**Câu 1. Dữ liệu `[10, 10, 10, 10, 1000]`. Trung bình? Trung vị? Cái nào mô tả đúng hơn?**

Trung bình `= 1040/5 = 208`. Trung vị `= 10`. Trung vị đúng hơn — 4/5 giá trị là 10, còn 208 không
mô tả điểm nào cả.

**Câu 2. "p95 = 800 ms" nghĩa là gì, nói bằng lời cho người không chuyên?**

"Cứ 100 request thì 95 request xong trong vòng 800 ms; 5 request còn lại chậm hơn thế."

**Câu 3. Trung bình 120 ms nhưng p95 = 4 giây. Bạn nghi ngờ gì?**

Có một nhóm nhỏ request đi vào đường chậm khác hẳn: cache miss, N+1 query, retry, cold start, hoặc
một endpoint/tenant cá biệt. Phải chẻ nhỏ theo endpoint/khách hàng rồi xem đuôi.

**Câu 4. Ba server, p95 lần lượt 100/200/900 ms. p95 toàn hệ có phải 400 ms không?**

Không. **Không được lấy trung bình của các phân vị.** Phải gộp dữ liệu thô (hoặc histogram) rồi tính
lại p95 trên toàn bộ.

**Câu 5. Khi nào dùng trung bình là hợp lý?**

Khi dữ liệu **cân đối, không đuôi dài** (chiều cao, điểm thi), hoặc khi bạn cần **đại lượng cộng
dồn** — ví dụ tính tổng chi phí token thì trung bình × số request mới ra đúng tổng, còn p95 thì không.
</details>

---

## 7. Chạy chương trình demo

Toàn bộ số trong bài này đều kiểm chứng được bằng máy. File demo chỉ dùng **thư viện chuẩn của
Python** (không cần cài gì) và vẽ biểu đồ bằng ký tự ASCII.

```bash
venv\Scripts\python.exe docs\hoc\demo_toan_ai.py
```

Chạy riêng từng phần:

```bash
venv\Scripts\python.exe docs\hoc\demo_toan_ai.py --part 1
```

| Phần | Nội dung in ra | Ứng với mục |
|---|---|---|
| `1` | cosine giữa các vector nhỏ, kèm dot / norm từng bước | 1 |
| `2` | attention cho câu "con mèo ngủ": Q·K → softmax → trộn V | 2 |
| `3` | softmax đổi hình dạng thế nào khi temperature đổi | 3 |
| `4` | log-likelihood và perplexity của một câu 3 chữ | 4 |
| `5` | gradient descent hội tụ từng bước, so 4 mức learning rate | 5 |
| `6` | p95 vs trung bình trên dữ liệu lệch, kèm histogram | 6 |

---

## 8. Bảng tra ký hiệu

Gặp ký hiệu lạ trong paper thì tra ở đây trước:

| Ký hiệu | Đọc là | Nghĩa ngắn gọn |
|---|---|---|
| `a_i` | a chỉ số i | phần tử thứ i của vector `a` |
| `Σ(i=1..n)` | tổng sigma | cộng dồn từ i = 1 đến n |
| `Π` | tích pi | nhân dồn (dùng cho xác suất cả câu) |
| `a · b` | a chấm b | tích vô hướng → ra **một số** |
| `\|\|a\|\|` | chuẩn của a | độ dài vector |
| `Aᵀ` | A chuyển vị | lật hàng thành cột |
| `m × n` | m nhân n | ma trận m hàng, n cột |
| `e` | e | ≈ 2.71828, cơ số của hàm mũ tự nhiên |
| `e^x` hoặc `exp(x)` | e mũ x | hàm mũ, luôn > 0 |
| `log`, `ln`, `log2` | lô-ga | "mũ lên bao nhiêu thì ra?"; `ln` cơ số e, `log2` cơ số 2 |
| `P(A)` | xác suất A | số trong `[0, 1]` |
| `P(B \| A)` | P của B khi biết A | xác suất có điều kiện — **gạch đứng KHÔNG phải chia** |
| `f'(w)`, `df/dw` | f phẩy | đạo hàm = độ dốc |
| `∇` (nabla) | gradient | vector chứa mọi đạo hàm riêng |
| `√d_k` | căn d k | căn bậc hai số chiều của K (hệ số chia trong attention) |
| `argmax` | ác-g-max | "chỉ số của phần tử lớn nhất" (không phải giá trị lớn nhất) |
| `≈` | xấp xỉ | gần bằng |

---

## Ôn 60 giây trước khi vào phỏng vấn

```
   1. VECTOR      danh sach so. Huong = nghia, do dai = do lon (bo di).
                  cosine = dot / (norm x norm) -> do goc -> do giong nhau.

   2. MA TRAN     bang so. Nhan ma tran = "hang nhan cot" = dot product lap lai.
                  Q = cau hoi, K = nhan dan, V = noi dung.
                  Attention = softmax(Q·K^T / √d_k) · V.

   3. SOFTMAX     bien diem tho thanh xac suat. Dung e^x vi luon duong + khuech dai
                  chenh lech. Temperature chia diem truoc khi mu:
                  T nho -> chac chan, T lon -> sang tao.

   4. XAC SUAT    LLM tinh P(chu tiep | cac chu truoc). Loss = cross-entropy =
                  -trung binh log P(chu dung). PPL = mu cua loss = "dang phan van
                  giua bao nhieu lua chon". LLM KHONG toi uu su that -> hallucination.

   5. GRADIENT    dao ham = do doc. w_moi = w_cu - lr x gradient.
      DESCENT     lr = do dai buoc chan: nho thi cham, lon thi dao dong hoac NaN.

   6. THONG KE    trung binh bi outlier keo; trung vi khang nhieu; p95 mo ta duoi.
                  Do p95 vi user nho lan cham, va SLA viet bang phan vi.
                  KHONG duoc lay trung binh cua cac p95.
```
