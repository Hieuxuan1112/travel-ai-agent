# Vector Database — từ số 0 đến hiểu và làm được

> Bài giảng này gắn với **kho dữ liệu thật của bạn**: 92 chunk Wikivoyage trong Chroma.
> Có chương trình chạy tương tác kèm theo — [`demo_vector_search.py`](demo_vector_search.py).
> Mọi con số trong bài đều đo trên máy bạn.

**Mục lục**

1. [Vấn đề: vì sao cơ sở dữ liệu thường không đủ](#1-vấn-đề-vì-sao-cơ-sở-dữ-liệu-thường-không-đủ)
2. [Embedding: biến chữ thành toạ độ](#2-embedding-biến-chữ-thành-toạ-độ)
3. [Đo độ gần: cosine similarity](#3-đo-độ-gần-cosine-similarity)
4. [Chạy thử ngay: chương trình tương tác](#4-chạy-thử-ngay-chương-trình-tương-tác)
5. [Vector database làm gì mà không tự viết được](#5-vector-database-làm-gì-mà-không-tự-viết-được)
6. [HNSW: vì sao tìm trong triệu vector vẫn nhanh](#6-hnsw-vì-sao-tìm-trong-triệu-vector-vẫn-nhanh)
7. [Chunking: cắt tài liệu sao cho đúng](#7-chunking-cắt-tài-liệu-sao-cho-đúng)
8. [Metadata filtering](#8-metadata-filtering)
9. [Điểm mù của vector search](#9-điểm-mù-của-vector-search)
10. [Chọn vector DB nào](#10-chọn-vector-db-nào)
11. [Code thật trong repo](#11-code-thật-trong-repo)
12. [Tự kiểm tra](#12-tự-kiểm-tra)
13. [Tài liệu](#13-tài-liệu)

---

## 1. Vấn đề: vì sao cơ sở dữ liệu thường không đủ

Bạn có 92 đoạn văn về Cornwall. Người dùng hỏi *"nơi nào có bãi biển đẹp?"*

Với SQL bạn viết:

```sql
SELECT * FROM docs WHERE content LIKE '%bãi biển đẹp%';
```

Kết quả: **0 dòng**. Vì tài liệu viết bằng tiếng Anh, và ngay cả tiếng Anh thì nó viết
*"sandy beaches"*, *"seaside resort"*, *"coastal town"* — không có cụm nào trùng chữ.

```
      ┌──────────────────────────────────────────────────────────────────┐
      │  CÂU HỎI:  "nơi nào có bãi biển đẹp"                             │
      └──────────────────────────────────────────────────────────────────┘
                    │                                    │
        TÌM THEO CHỮ                          TÌM THEO Ý NGHĨA
        (SQL LIKE, BM25)                      (vector search)
                    │                                    │
                    ▼                                    ▼
      ┌───────────────────────────┐      ┌───────────────────────────────┐
      │  so từng ký tự            │      │  đổi câu thành DÃY SỐ         │
      │  "bãi biển" có trong      │      │  tìm dãy số GẦN NHẤT          │
      │  văn bản không?           │      │  trong kho                    │
      │                           │      │                               │
      │  → KHÔNG có → 0 kết quả   │      │  → "Perranporth — a seaside   │
      │                           │      │     resort town backed by..." │
      └───────────────────────────┘      └───────────────────────────────┘
```

Vector database sinh ra để giải đúng bài này: **tìm theo ý nghĩa, không theo mặt chữ**.

---

## 2. Embedding: biến chữ thành toạ độ

**Embedding** là một hàm biến đoạn text thành một dãy số cố định độ dài.

Của bạn dùng `gemini-embedding-001`, mỗi đoạn ra một dãy **3072 số** (đã đo bằng chương
trình demo). Hình dung dễ nhất là rút xuống 2 chiều rồi vẽ lên giấy:

```
        ▲  chiều 2
        │
    1.0 ┤                                   ● "bãi biển cát"
        │                              ●  "sandy beach"
        │                         ● "seaside resort"
    0.5 ┤                    ● "coastal town"
        │
        │
    0.0 ┼─────────────────────────────────────────────────────────────►  chiều 1
        │                                                   ● "lãi suất
        │                                                      ngân hàng"
   -0.5 ┤                                        ● "bank interest rate"
        │
        │        NHÓM TRÁI TRÊN: mọi thứ về biển, dù khác ngôn ngữ
        │        NHÓM PHẢI DƯỚI: mọi thứ về tài chính
        ▼
```

Ba điều rút ra từ hình:

1. **Cùng nghĩa thì ở gần nhau** dù dùng chữ khác nhau ("bãi biển cát" ↔ "sandy beach").
2. **Khác nghĩa thì ở xa nhau**, dù có thể trùng vài chữ.
3. **Vị trí là do model học được** từ hàng tỉ câu, không ai gán tay.

Thực tế không phải 2 chiều mà **3072 chiều** — không vẽ ra được, nhưng toán học thì y hệt.

### Ai tạo ra embedding?

Một mô hình riêng, khác với mô hình chat:

| | Model chat (`gemini-3.1-flash-lite`) | Model embedding (`gemini-embedding-001`) |
|---|---|---|
| Đầu vào | đoạn hội thoại | một đoạn text |
| Đầu ra | **chữ** | **dãy 3072 số** |
| Dùng để | trả lời, gọi tool | tìm kiếm, phân cụm, gợi ý |
| Giá | đắt hơn | rất rẻ |

Trong repo của bạn cả hai cùng tồn tại — xem [mục 11](#11-code-thật-trong-repo).

---

## 3. Đo độ gần: cosine similarity

Có hai vector rồi, làm sao biết chúng gần nhau bao nhiêu? Đo **góc** giữa chúng.

```
                    ▲
                    │        ●  B = "sandy beach"
                    │      ╱
                    │    ╱
                    │  ╱  góc nhỏ  →  cosine ≈ 1  →  RẤT GIỐNG NHAU
                    │╱ θ
        ────────────●──────────────►   A = "bãi biển cát"
                   ╱ │
                 ╱   │
               ╱     │
             ●       │        C = "lãi suất ngân hàng"
                     │        góc lớn  →  cosine thấp  →  KHÁC NHAU
                     ▼
```

Công thức, và đây cũng là code thật trong `demo_vector_search.py`:

```python
def cosine(a: list[float], b: list[float]) -> float:
    """cos = (a . b) / (|a| * |b|)   -> 1 la cung huong, 0 la khong lien quan"""
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    return dot / (norm_a * norm_b)
```

Đọc từng phần:

- `dot` — **tích vô hướng**: nhân từng cặp số cùng vị trí rồi cộng lại. Hai vector cùng
  hướng thì tích này lớn.
- `norm_a`, `norm_b` — **độ dài** của mỗi vector (định lý Pythagoras mở rộng ra n chiều).
- Chia cho tích hai độ dài để **bỏ ảnh hưởng của độ dài**, chỉ còn lại góc. Nhờ vậy một
  đoạn dài và một đoạn ngắn cùng nội dung vẫn được coi là giống nhau.

### Số đo thật trên máy bạn

Chạy `demo_vector_search.py --compare`, kết quả thật:

| Cặp câu | cosine |
|---|---|
| `sandy beach` ↔ `bai bien cat` | **0.638** |
| `sandy beach` ↔ `bank interest rate` | **0.533** |

**Một điều quan trọng phải hiểu ở đây, và rất hay bị hiểu sai:** 0.638 nghe không cao lắm,
và 0.533 nghe cũng không thấp lắm. Đó là vì **mỗi model có dải giá trị riêng**. Với
`gemini-embedding-001`, hai câu bất kỳ hiếm khi xuống dưới 0.4.

Nên: **đừng bao giờ đọc con số cosine tuyệt đối và kết luận "giống" hay "khác"**. Cái có
ý nghĩa là **thứ tự so sánh** — cặp 0.638 gần nhau hơn cặp 0.533, và đó chính là điều cần
để xếp hạng kết quả tìm kiếm. Nếu bạn muốn đặt một ngưỡng cứng (ví dụ "dưới 0.6 thì loại")
thì phải **đo trên chính dữ liệu của mình** để chọn ngưỡng, không lấy con số từ blog nào đó.

### Khoảng cách vs độ giống

Chroma trả về **khoảng cách** chứ không phải độ giống. Ngược chiều nhau:

```
   độ giống (cosine similarity)   càng LỚN càng gần   ── 1.0 là trùng
   khoảng cách (distance)         càng NHỎ càng gần   ── 0.0 là trùng
```

Nhìn kết quả demo thật, cột "khoảng cách" — số nhỏ nhất đứng đầu:

```
   Cau hoi: 'beaches'
   hang  khoang cach   trich doan
   1     0.6596        Other destinations[edit] ... Tamar Valley
   2     0.7100        50.2702-4.78749 Mevagissey — picturesque hillside fishing vi
   3     0.7101        50.119-5.5376 Penzance — pirate central, Penzance is a town
```

---

## 4. Chạy thử ngay: chương trình tương tác

Đọc mười trang không bằng gõ thử một câu. Chạy:

```bash
D:\langgraph-agent-lab\venv\Scripts\python.exe D:\langgraph-agent-lab\docs\demo_vector_search.py
```

Gõ câu hỏi bất kỳ, nó in ra 5 đoạn gần nhất kèm khoảng cách. Thử theo thứ tự này để thấy
từng tính chất:

| Gõ thử | Sẽ thấy điều gì |
|---|---|
| `beaches` | Trường hợp thường — từ khoá có thật trong tài liệu |
| `sandy shore for swimming` | **Không có chữ "beach"** mà vẫn ra bãi biển → tìm theo nghĩa |
| `nơi nào có bãi biển đẹp` | Hỏi **tiếng Việt**, tài liệu **tiếng Anh**, vẫn ra đúng |
| `SKU-99321` | Mã vô nghĩa → kết quả rác. Đây là **điểm mù**, xem mục 9 |
| `castle` / `surfing` / `where can I eat` | Tự khám phá thêm |

Hai chế độ nữa:

```bash
python docs\demo_vector_search.py --demo      # chạy sẵn 4 ví dụ trên
python docs\demo_vector_search.py --compare   # so độ gần của hai câu bất kỳ
```

Chế độ `--compare` là chỗ bạn tự tay kiểm chứng mục 3: nhập hai câu, nó embed cả hai rồi
tính cosine bằng công thức viết tay ở trên.

---

## 5. Vector database làm gì mà không tự viết được

Câu hỏi hợp lý: có 92 vector, sao không lưu vào một list Python rồi lặp qua tính cosine?

**Với 92 chunk thì làm vậy được thật.** Vector DB chỉ thắng khi quy mô lớn lên:

| Việc | Tự viết bằng list | Vector DB |
|---|---|---|
| Tìm trong 92 vector | ~1 ms, ổn | ~1 ms |
| Tìm trong 1 triệu vector | **quét hết → chậm khủng khiếp** | ~5 ms nhờ chỉ mục HNSW |
| Lưu lại sau khi tắt máy | tự viết code ghi/đọc file | có sẵn |
| Lọc theo điều kiện (ngôn ngữ, ngày) | tự viết | có sẵn |
| Thêm/xoá tài liệu lẻ | phải dựng lại cả cấu trúc | có sẵn |
| Nhiều tiến trình cùng đọc | tự lo khoá | có sẵn |

Tóm lại vector DB = **chỉ mục tìm nhanh + lưu trữ bền + lọc metadata**, đóng gói sẵn.

---

## 6. HNSW: vì sao tìm trong triệu vector vẫn nhanh

Đây là phần "ruột" mà người phỏng vấn hay hỏi để phân biệt người dùng thư viện với người
hiểu thư viện.

**Cách ngây thơ (brute force / exact search):** so câu hỏi với **tất cả** 1 triệu vector.
Chính xác tuyệt đối nhưng chậm tuyến tính theo số lượng.

**HNSW (Hierarchical Navigable Small World)** đổi một chút chính xác lấy tốc độ khổng lồ.
Ý tưởng là xây **nhiều tầng** như hệ thống giao thông:

```
   TẦNG 2  (thưa — như đường cao tốc, nhảy được rất xa)
   ●━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━●━━━━━━━━━━━━━━━━━━━━━━━━━━●
   │                                  │                          │
   │        nhảy xuống tầng dưới      │                          │
   ▼                                  ▼                          ▼
   TẦNG 1  (vừa — như quốc lộ)
   ●━━━━━━━━━●━━━━━━━━━●━━━━━━━━━━━━━━●━━━━━━━━●━━━━━━━━━━━━━━━━━●
   │         │         │              │        │                 │
   ▼         ▼         ▼              ▼        ▼                 ▼
   TẦNG 0  (dày đặc — như đường hẻm, đủ mọi điểm)
   ●━●━●━●━●━●━●━●━●━●━●━●━●━●━●━●━●━●━●━●━●━●━●━●━●━●━●━●━●━●━●━●
                                      ▲
                                   ĐÍCH
```

Cách tìm: bắt đầu ở tầng trên cùng, đi những bước **rất dài** về phía đích; đến khi không
tiến gần thêm được nữa thì nhảy xuống tầng dưới đi bước ngắn hơn; lặp đến tầng 0 thì tinh
chỉnh nốt.

Giống hệt cách bạn đi từ Hà Nội đến một con hẻm ở Sài Gòn: đi cao tốc trước, rồi quốc lộ,
rồi mới vào hẻm — không ai dò từng con hẻm cả nước.

**Đánh đổi:** HNSW là **ANN (Approximate Nearest Neighbor)** — tìm *gần đúng*. Có xác suất
nhỏ bỏ sót kết quả tốt nhất. Với tìm kiếm ngữ nghĩa thì hoàn toàn chấp nhận được, vì bản
thân khái niệm "liên quan" đã mơ hồ sẵn.

Hai tham số hay gặp khi chỉnh HNSW:

- `M` — mỗi điểm nối với bao nhiêu hàng xóm. Lớn hơn = chính xác hơn, tốn RAM hơn.
- `ef_search` — lúc tìm thì xem xét bao nhiêu ứng viên. Lớn hơn = chính xác hơn, chậm hơn.

---

## 7. Chunking: cắt tài liệu sao cho đúng

Không nhét cả trang web vào một vector được. Phải cắt nhỏ. Repo của bạn cắt thế này:

```python
splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=128)
```

Kết quả thật: **4 trang Wikivoyage → 92 chunk**.

### Vì sao 1024 ký tự

```
  QUÁ NHỎ (200 ký tự)              VỪA (1024)                QUÁ LỚN (10.000)
  ┌────────┐                    ┌──────────────┐         ┌───────────────────────┐
  │ mảnh 1 │ ← cụt ý            │              │         │                       │
  ├────────┤                    │  trọn một ý  │         │  lẫn lộn nhiều chủ đề │
  │ mảnh 2 │ ← mất ngữ cảnh     │              │         │  vector bị "trung bình│
  ├────────┤                    │              │         │  hoá" thành vô nghĩa  │
  │ mảnh 3 │                    └──────────────┘         │                       │
  └────────┘                                             └───────────────────────┘
  → tìm ra mảnh đúng            → tìm đúng và            → tìm ra thì cũng
    nhưng không đủ để trả lời      đủ để trả lời            kèm 90% nhiễu
```

Vector là **trung bình hoá ý nghĩa** của cả đoạn. Đoạn càng dài, "trung bình" càng nhạt —
một chunk nói về cả bãi biển lẫn lịch sử lẫn nhà hàng sẽ không gần với câu hỏi nào cả.

### Vì sao chồng lấn 128 ký tự

```
   Văn bản gốc:
   ... St Ives has a beautiful sandy beach. | The town is also famous for its art ...
                                            ▲
                                     chỗ bị cắt

   KHÔNG chồng lấn:
   chunk 1: "... St Ives has a beautiful sandy beach."
   chunk 2: "The town is also famous for its art ..."
                ▲── "The town" là town nào? Mất tên rồi.

   CÓ chồng lấn 128 ký tự:
   chunk 1: "... St Ives has a beautiful sandy beach."
   chunk 2: "St Ives has a beautiful sandy beach. The town is also famous for its art ..."
             └──────── phần lặp lại ────────┘
                Giờ chunk 2 tự đủ nghĩa.
```

### Vì sao "Recursive"

`RecursiveCharacterTextSplitter` cắt theo thứ tự ưu tiên: thử cắt ở **đoạn văn** (`\n\n`)
trước; nếu mảnh vẫn quá dài thì cắt ở **câu**; vẫn dài thì cắt ở **từ**; cùng đường mới cắt
giữa chữ. Nhờ vậy nó hiếm khi cắt ngang một câu.

---

## 8. Metadata filtering

Mỗi chunk lưu kèm **metadata** — thông tin phụ như nguồn, ngày, ngôn ngữ, tác giả.

Điều này giải quyết một bài toán mà vector search thuần không làm được: *"tìm bãi biển đẹp
**nhưng chỉ trong tài liệu về West Cornwall**"*.

```
   Không có filter:                     Có filter:
   ┌──────────────────────┐            ┌──────────────────────┐
   │ tìm trong 92 chunk   │            │ lọc còn 23 chunk     │
   │ → có thể ra North    │            │ (source = West...)   │
   │   Cornwall           │            │ → rồi mới tìm vector │
   └──────────────────────┘            └──────────────────────┘
```

Trong LangChain/Chroma:

```python
retriever = store.as_retriever(search_kwargs={"filter": {"source": "West_Cornwall"}})
```

Đây là lý do vector DB hơn hẳn một file numpy: nó kết hợp được **tìm theo nghĩa** với
**lọc theo điều kiện chính xác**.

---

## 9. Điểm mù của vector search

Rất quan trọng — người phỏng vấn hay hỏi *"khi nào vector search thất bại?"*

| Tình huống | Vì sao hỏng | Cách chữa |
|---|---|---|
| **Mã, số hiệu**: `SKU-99321` | Model không "hiểu" chuỗi ký tự tuỳ ý; nó trả về mã na ná | BM25 / khớp chính xác |
| **Tên riêng lạ** | Có thể trôi sang tên nghe giống | Hybrid search |
| **Phủ định**: "khách sạn KHÔNG có hồ bơi" | Vector thường bỏ qua từ phủ định, ra đúng khách sạn có hồ bơi | Lọc metadata, hoặc rerank |
| **Số liệu chính xác**: "dưới 500k một đêm" | Vector không so sánh số | Lưu thành metadata rồi lọc |
| **Câu hỏi quá ngắn**: "giá?" | Không đủ tín hiệu để định vị | Viết lại truy vấn (LLM làm giúp) |

Bạn tự kiểm chứng được ca đầu tiên: chạy `--demo`, xem kết quả của `SKU-99321` — nó vẫn
trả về 3 đoạn nào đó, vì **vector search luôn trả về k kết quả gần nhất, kể cả khi không có
gì thực sự liên quan**. Nó không biết nói "tôi không tìm thấy".

Đây chính là lý do tuần 4 trong lộ trình là **hybrid search**: BM25 bù đúng những chỗ này.

---

## 10. Chọn vector DB nào

| Tên | Kiểu | Hợp khi |
|---|---|---|
| **Chroma** (đang dùng) | nhúng trong ứng dụng, lưu ra file | dự án nhỏ/vừa, học, prototype |
| **FAISS** | thư viện thuần, không phải DB | cần tốc độ tối đa, tự lo lưu trữ |
| **Qdrant / Weaviate / Milvus** | server riêng | production, nhiều triệu vector, cần lọc phức tạp |
| **pgvector** | tiện ích của PostgreSQL | **đã có Postgres rồi** — khỏi thêm hạ tầng mới |
| **Pinecone** | dịch vụ trả phí | không muốn tự vận hành |

Nói khi phỏng vấn: *"Tôi chọn Chroma vì kho chỉ 92 chunk và tôi cần nó chạy được ngay khi
clone repo, không cần dựng thêm dịch vụ. Nếu lên hàng triệu vector và cần lọc metadata
phức tạp thì tôi sẽ chuyển sang Qdrant, hoặc pgvector nếu hệ thống đã có Postgres."*

Câu đó cho thấy bạn chọn theo bối cảnh chứ không theo trend.

---

## 11. Code thật trong repo

Toàn bộ tầng vector nằm trong `main_02_02.py`, chỉ khoảng 40 dòng.

**Khai báo model embedding** (khác model chat):

```python
EMBED_MODEL = os.environ.get("EMBED_MODEL", "models/gemini-embedding-001")
embeddings = GoogleGenerativeAIEmbeddings(model=EMBED_MODEL)
```

**Dựng kho** — tải, cắt, embed, lưu:

```python
docs = WebBaseLoader(urls).load()
splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=128)
chunks = splitter.split_documents(docs)
return Chroma.from_documents(chunks, embedding=embeddings, persist_directory=PERSIST_DIR)
```

`from_documents` làm ba việc trong một dòng: gọi API embedding cho từng chunk, dựng chỉ mục
HNSW, ghi tất cả xuống thư mục `chroma_travel_info/` (3,3 MB, đã commit vào repo).

**Nạp lại và kiểm tra rỗng** — đoạn này sinh ra từ một lỗi thật:

```python
cached = Chroma(persist_directory=PERSIST_DIR, embedding_function=embeddings)
if not cached.get(limit=1)["ids"]:
    print("Cached vector store is empty - rebuilding.")
    cached = None
```

Thư mục tồn tại **không** có nghĩa là có dữ liệu — khi gắn Docker volume vào, thư mục luôn
tồn tại nhưng rỗng. Chi tiết ở [MENTOR.md](MENTOR.md) mục 14.

**Dùng để tìm** — chính là tool 1 của agent:

```python
@tool(description="Search travel information about destinations in England. ...")
def search_travel_info(query: str) -> str:
    docs = get_travel_info_retriever().invoke(query)
    top = docs[:4] if isinstance(docs, list) else docs
    return "\n---\n".join(d.page_content for d in top)
```

Một dòng `.invoke(query)` gói trọn: embed câu hỏi → đi HNSW → trả về k chunk gần nhất.

---

## 12. Tự kiểm tra

<details><summary><b>1. Embedding là gì? Vì sao nó cho phép tìm theo ý nghĩa?</b></summary>

Là hàm biến text thành vector số cố định chiều, huấn luyện sao cho nội dung giống nhau thì
vector gần nhau. Nhờ vậy đo khoảng cách vector là biết mức liên quan về nghĩa, không cần
trùng chữ.
</details>

<details><summary><b>2. Cosine similarity đo cái gì? Vì sao phải chia cho độ dài vector?</b></summary>

Đo góc giữa hai vector. Chia cho tích hai độ dài để loại bỏ ảnh hưởng của độ dài, chỉ còn
lại hướng — nhờ đó đoạn dài và đoạn ngắn cùng nội dung vẫn được coi là giống nhau.
</details>

<details><summary><b>3. cosine = 0.638 giữa hai câu nghĩa là chúng "khá giống" đúng không?</b></summary>

Không kết luận được. Mỗi model có dải giá trị riêng; với `gemini-embedding-001` hai câu bất
kỳ hiếm khi dưới 0.4. Chỉ **thứ tự so sánh** mới có ý nghĩa. Muốn đặt ngưỡng thì phải đo
trên chính dữ liệu của mình.
</details>

<details><summary><b>4. Chroma trả về "khoảng cách" — số lớn hơn nghĩa là gần hơn hay xa hơn?</b></summary>

Xa hơn. Khoảng cách càng nhỏ càng gần, ngược với độ giống (càng lớn càng gần).
</details>

<details><summary><b>5. HNSW là gì và nó đánh đổi cái gì?</b></summary>

Chỉ mục nhiều tầng cho phép nhảy bước dài ở tầng thưa rồi tinh chỉnh ở tầng dày, nên tìm
trong triệu vector chỉ mất mili giây. Đánh đổi: đây là tìm **gần đúng** (ANN), có xác suất
nhỏ bỏ sót kết quả tốt nhất.
</details>

<details><summary><b>6. Vì sao chunk 1024 ký tự chứ không phải 10.000?</b></summary>

Vector là trung bình hoá ý nghĩa cả đoạn. Đoạn quá dài lẫn nhiều chủ đề nên vector nhạt đi,
không gần với câu hỏi nào; và khi tìm ra thì kèm rất nhiều nhiễu.
</details>

<details><summary><b>7. Chồng lấn 128 ký tự để làm gì?</b></summary>

Để câu bị cắt ngang biên vẫn xuất hiện trọn vẹn ở ít nhất một chunk, tránh mất ngữ cảnh
kiểu "The town" mà không biết town nào.
</details>

<details><summary><b>8. Kể ba tình huống vector search làm kém.</b></summary>

Mã/số hiệu chính xác; câu có phủ định ("không có hồ bơi"); so sánh số ("dưới 500k"). Ngoài
ra nó luôn trả về k kết quả kể cả khi không có gì liên quan — không biết nói "không tìm thấy".
</details>

<details><summary><b>9. Khi nào cần vector DB thật thay vì lưu list vector trong Python?</b></summary>

Khi số vector lớn (cần chỉ mục ANN), cần lưu bền sau khi tắt, cần lọc metadata, cần
thêm/xoá lẻ, hoặc nhiều tiến trình cùng truy cập.
</details>

<details><summary><b>10. Vì sao bạn chọn Chroma cho dự án này?</b></summary>

Kho chỉ 92 chunk và cần chạy được ngay khi clone repo, không dựng thêm dịch vụ. Quy mô lớn
hơn sẽ chuyển Qdrant, hoặc pgvector nếu đã có Postgres.
</details>

---

## 13. Tài liệu

| Nguồn | Dùng cho | Thời lượng |
|---|---|---|
| **`demo_vector_search.py`** trong repo này | tự tay thử — làm trước tiên | 20 phút |
| Pinecone Learning Center — *Vector Embeddings*, *HNSW* | giải thích có hình, ngắn gọn | 1 giờ |
| Tài liệu Chroma — Getting Started | đúng thư viện bạn đang dùng | 30 phút |
| Bài báo HNSW (Malkov & Yashunin) — đọc phần hình minh hoạ | hiểu sâu cấu trúc tầng | tuỳ chọn |
| sbert.net — *Semantic Search* | nối sang phần reranking ở tuần 4 | 1 giờ |
| Tài liệu pgvector | nếu bạn học SQL xong muốn nối hai mảng | tuỳ chọn |
