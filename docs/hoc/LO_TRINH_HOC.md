# Lộ trình học & sổ tay giải thích sản phẩm

> Tài liệu này có hai việc: **dạy bạn kiến thức nền** đang thiếu, và **giúp bạn nói trôi
> chảy** về mọi thứ trong CV. Mỗi mục có: giải thích bằng lời thường → sơ đồ → code thật
> trong repo này → câu tự kiểm tra (bấm để mở đáp án) → tài liệu nên đọc.
>
> Tài liệu anh em: [MENTOR.md](MENTOR.md) mô tả **sản phẩm**. File này dạy **kiến thức
> đứng sau sản phẩm**.

**Mục lục**

- [Cách dùng tài liệu này](#cách-dùng-tài-liệu-này)
- [Phần 0 — Bản đồ: mỗi dòng CV cần kiến thức gì](#phần-0--bản-đồ-mỗi-dòng-cv-cần-kiến-thức-gì)
- [P1 — Đánh giá mô hình & ML căn bản](#p1--đánh-giá-mô-hình--ml-căn-bản)
- [P2 — Transformer, BERT, SBERT, embedding](#p2--transformer-bert-sbert-embedding)
- [P3 — Tìm kiếm: keyword, vector, hybrid](#p3--tìm-kiếm-keyword-vector-hybrid)
- [P4 — Serving model: từ gọi API đến tự host](#p4--serving-model-từ-gọi-api-đến-tự-host)
- [P5 — Fine-tuning, LoRA, QLoRA, quantization](#p5--fine-tuning-lora-qlora-quantization)
- [P6 — Tokenizer & tiền xử lý NLP](#p6--tokenizer--tiền-xử-lý-nlp)
- [Phần 7 — Kịch bản nói về từng dòng CV](#phần-7--kịch-bản-nói-về-từng-dòng-cv)
- [Phần 8 — Lịch 6 tuần](#phần-8--lịch-6-tuần)

## Cách dùng tài liệu này

Mỗi ngày 45–60 phút lý thuyết, code dồn vào cuối tuần. **Đừng học hết lý thuyết rồi mới
code** — kiến thức không gắn với thứ vừa làm thì tuần sau quên sạch.

Với mỗi mục, làm đúng 3 bước:

1. Đọc phần giải thích, rồi **nói to lại bằng lời của mình**. Nghe ngớ ngẩn nhưng đây là
   cách duy nhất biết mình có hiểu thật hay chỉ đang gật gù.
2. Mở file code được trỏ tới, đọc đoạn đó, hiểu vì sao nó viết như vậy.
3. Trả lời câu tự kiểm tra **trước khi** mở đáp án.

---

## Phần 0 — Bản đồ: mỗi dòng CV cần kiến thức gì

Bảng quan trọng nhất tài liệu. Cột phải chỉ bạn tới mục cần học để bảo vệ được dòng đó.

| Dòng trong CV | Con số bạn khoe | Kiến thức phải có để bảo vệ | Học ở |
|---|---|---|---|
| OCR error correction (ViT5) | 94% precision, 90% recall | precision/recall/F1, fine-tune transformer | P1, P5 |
| E-commerce classification | MRR ≈ 0,60, TF-IDF + Logistic Regression | MRR, TF-IDF, đánh giá xếp hạng | P1, P3, P6 |
| Bilingual retrieval | 3s → 0,4s, LaBSE, hybrid rerank | embedding, SBERT, vector search, reranking | P2, P3 |
| Han-Nom corpus (luận văn) | 55K bài → 10K mẫu, 98,2% | đo chất lượng nhãn, thiết kế cổng xác thực | P1 |
| Multi-tool AI Agent | 100% tool-selection (8 case eval) | ReAct, tool calling, RAG, eval, p95 | P1, P2, P3 |
| Prometheus, cost/query | $0,0007/câu | token, tokenizer, đo lường | P6 |
| Docker, FastAPI, CI | 56 test | đã vững — chỉ cần nói rõ | [MENTOR.md](MENTOR.md) |
| Lưu hội thoại bền | checkpointer trên PostgreSQL | thread state, trim context | [HOC_LANGGRAPH.md](HOC_LANGGRAPH.md) |
| CD: Trivy, GHCR | quét trước khi đẩy, tag theo SHA | chuỗi cung ứng phần mềm | [HOC_CICD_CLOUD.md](HOC_CICD_CLOUD.md) |
| Azure Container Apps | keyless OIDC, scale-to-zero, $0 | federated credential, quyền tối thiểu | [HOC_CICD_CLOUD.md](HOC_CICD_CLOUD.md) |

**Nguyên tắc sống còn:** con số trên CV mà không giải thích được thì **quay ra hại bạn** —
người phỏng vấn sẽ nghĩ bạn chép của người khác. Vì vậy P1 đứng đầu.

---

# P1 — Đánh giá mô hình & ML căn bản

> **Vì sao ưu tiên số một:** CV bạn dày đặc con số. Câu "precision khác recall chỗ nào?"
> gần như chắc chắn được hỏi. Đây cũng là phần rẻ nhất — 3 ngày là xong.

## 1.1 Bốn ô của confusion matrix

Tưởng tượng một máy soi bệnh. Mỗi ca, máy nói "có" hoặc "không". Đối chiếu sự thật, có
đúng 4 khả năng:

```
                        SỰ THẬT
                  Có bệnh      Không bệnh
              ┌─────────────┬─────────────┐
   Máy   Có   │     TP      │     FP      │  ← máy báo "có"
   nói        │ (đúng, có)  │ (báo nhầm)  │
              ├─────────────┼─────────────┤
       Không  │     FN      │     TN      │  ← máy báo "không"
              │  (bỏ sót)   │ (đúng, ko)  │
              └─────────────┴─────────────┘
```

- **TP** – máy nói có, thật sự có → đúng
- **FP** – máy nói có, thật ra không → **báo động giả**
- **FN** – máy nói không, thật ra có → **bỏ sót**
- **TN** – máy nói không, thật ra không → đúng

Mẹo nhớ: chữ thứ hai là **máy nói gì**, chữ đầu là **máy đúng hay sai**.

## 1.2 Precision và Recall — nói bằng lời thường

**Precision:** *"trong những cái máy bảo là CÓ, bao nhiêu phần trăm đúng?"*

```
Precision = TP / (TP + FP)
```

**Recall:** *"trong tất cả những cái THẬT SỰ có, máy tìm ra được bao nhiêu?"*

```
Recall = TP / (TP + FN)
```

Nhớ chắc nhất: **Precision hỏi về những gì máy NÓI. Recall hỏi về những gì THẬT SỰ CÓ.**

Vì sao luôn phải nói cả hai — vì mỗi cái đứng một mình đều dễ bị lừa:

- Muốn precision 100%? Chỉ báo "có" đúng một ca chắc ăn nhất. Precision hoàn hảo nhưng
  bỏ sót 999 người bệnh → recall thảm hại.
- Muốn recall 100%? Báo "có" cho tất cả. Không sót ai, nhưng precision thành rác.

Hai chỉ số **đánh đổi nhau**: kéo cái này lên thì cái kia tụt.

**Chọn cái nào tuỳ bài toán** — đây là câu hỏi phỏng vấn hay gặp:

| Bài toán | Ưu tiên | Vì sao |
|---|---|---|
| Sàng lọc ung thư | **Recall** | Bỏ sót người bệnh là chết người; báo nhầm thì xét nghiệm lại |
| Lọc thư rác | **Precision** | Đẩy nhầm email quan trọng vào spam tệ hơn để lọt vài thư rác |
| Sửa lỗi OCR (dự án của bạn) | **Precision** | Sửa bừa làm hỏng chữ vốn đang đúng — tệ hơn bỏ sót |

**Áp vào dự án của bạn.** ViT5 đạt **94% precision, 90% recall**. Nói thành lời:

> *"Trong những chỗ mô hình quyết định sửa, 94% là sửa đúng. Và trong tất cả lỗi OCR thật
> sự có trong văn bản, mô hình bắt được 90%. Tôi ưu tiên precision vì với hậu xử lý OCR,
> sửa hỏng một chữ vốn đang đúng thì tệ hơn là bỏ sót một lỗi."*

Học thuộc đoạn đó. Nó biến con số trên giấy thành bằng chứng bạn hiểu việc mình làm.

## 1.3 F1 — khi cần một con số duy nhất

```
F1 = 2 × (Precision × Recall) / (Precision + Recall)
```

Đây là **trung bình điều hoà**, không phải trung bình cộng. Khác biệt quan trọng: trung
bình cộng của 100% và 0% là 50% (nghe ổn), còn F1 = 0. Trung bình điều hoà **trừng phạt
nặng khi hai số lệch nhau**, nên không gian lận được bằng cách đẩy một chỉ số lên trời.

F1 của bạn: 2 × (0,94 × 0,90) / (0,94 + 0,90) ≈ **0,92**.

## 1.4 Cái bẫy accuracy

**Accuracy = (TP + TN) / tổng**. Nghe hợp lý nhất nhưng nguy hiểm nhất.

1000 người, 10 người bệnh. Máy "ngu" luôn trả lời "không bệnh":

```
Accuracy = 990/1000 = 99%     ← nghe xuất sắc
Recall   = 0/10     = 0%      ← thực tế vô dụng hoàn toàn
```

Đây là **dữ liệu mất cân bằng lớp** (class imbalance). Quy tắc: **lớp hiếm thì đừng bao
giờ báo cáo accuracy một mình.**

## 1.5 MRR — chỉ số của bài toán xếp hạng

Dự án phân loại sản phẩm của bạn có **MRR ≈ 0,60**. MRR = *Mean Reciprocal Rank*, dùng khi
mô hình trả về một **danh sách xếp hạng** chứ không phải một đáp án duy nhất.

Với mỗi câu hỏi, tìm vị trí của đáp án đúng đầu tiên rồi lấy nghịch đảo:

```
đáp án đúng ở hạng 1     →  1/1 = 1,00
đáp án đúng ở hạng 2     →  1/2 = 0,50
đáp án đúng ở hạng 3     →  1/3 = 0,33
không có trong danh sách →  0
```

MRR là trung bình các giá trị đó trên toàn bộ câu hỏi.

**MRR 0,60 nghĩa là:** trung bình đáp án đúng nằm quanh **vị trí 1–2**. Tức phần lớn thời
gian người dùng thấy kết quả đúng ngay đầu danh sách.

Chỉ số họ hàng bạn sẽ gặp ở tuần 4:

- **Recall@k** – trong top-k có chứa đáp án đúng không (chỉ quan tâm có/không)
- **Precision@k** – trong top-k, bao nhiêu cái liên quan
- **nDCG** – như MRR nhưng tính cả nhiều đáp án đúng với mức liên quan khác nhau

## 1.6 Đo chất lượng khi không có "đáp án đúng"

Với LLM không có nhãn đúng/sai rạch ròi. Repo này đo bằng **hai chỉ số bổ sung nhau**.

**Cách 1 — Tool-selection accuracy (khách quan, chấm tự động).**

Code thật trong `evals/eval_agent.py`:

```python
def called_tools(messages) -> list[str]:
    """Doc lich su message de biet agent da goi nhung tool nao."""
    names = []
    for message in messages:
        if isinstance(message, AIMessage):
            names.extend(call["name"] for call in message.tool_calls or [])
    return names
```

Logic từng dòng: duyệt **toàn bộ lịch sử hội thoại**; lấy mọi `AIMessage` (tin nhắn do
model sinh); gom tên các tool nó yêu cầu gọi. Rồi so với tập tool kỳ vọng:

```python
passed = expected.issubset(set(tools))
```

Dùng `issubset` chứ không phải `==`: gọi **thừa** vẫn tính đạt (tra thời tiết 3 thị trấn
thay vì 2 là chấp nhận được), nhưng **thiếu** thì trượt.

Điều làm bài đo này đáng tin: **đọc từ state thật, không đoán từ câu chữ trả lời.**

**Cách 2 — LLM-as-judge (chủ quan, một LLM khác chấm điểm).**

```python
JUDGE_PROMPT = """You are grading a travel assistant's answer.
Question: {question}
Answer: {answer}
Score the answer from 1 to 5 on being helpful, concrete and grounded in real data
(named towns, real weather numbers). Reply with the digit only."""
```

**Vì sao cần cả hai:** kết quả eval thật của bạn có một ca chứng minh hoàn hảo — câu
*"I want a surfing town in Cornwall where it is not raining today"* **chọn đúng tool
(pass)** nhưng chỉ được **2/5 điểm** vì câu trả lời không chốt được thị trấn nào. Chọn
đúng công cụ ≠ trả lời tốt. Kể ca này trong phỏng vấn, nó cho thấy bạn đọc kết quả đo chứ
không chỉ khoe con số đẹp.

## 1.7 Overfitting, underfitting, chia dữ liệu

**Overfitting (học vẹt):** mô hình thuộc lòng dữ liệu huấn luyện, gồm cả nhiễu. Điểm trên
tập train rất cao, gặp dữ liệu mới thì tệ. Như học sinh học thuộc đề cũ mà không hiểu bài.

**Underfitting (học chưa tới):** mô hình quá đơn giản, sai ngay cả trên tập train.

```
   Lỗi
    │╲                                      ╱ lỗi trên dữ liệu mới
    │ ╲                                   ╱
    │  ╲                               ╱
    │   ╲______________________ ____╱        ← điểm ngọt
    │                          ╲
    │                           ╲__________  lỗi trên tập train (luôn giảm)
    └────────────────────────────────────► độ phức tạp mô hình
      underfitting          overfitting
```

**Chia dữ liệu 3 phần:**

| Tập | Dùng để | Tỉ lệ hay dùng |
|---|---|---|
| **Train** | mô hình học từ đây | 70% |
| **Validation** | chỉnh siêu tham số, chọn mô hình | 15% |
| **Test** | đo lần cuối, **chỉ dùng một lần** | 15% |

Vì sao phải tách validation khỏi test: nếu chỉnh mô hình dựa trên tập test thì bạn đã gián
tiếp "học" từ nó, con số cuối không còn trung thực. Test là bài thi thật, chỉ mở một lần.

**Cross-validation (k-fold):** khi dữ liệu ít, chia k phần, lần lượt mỗi phần làm
validation, còn lại làm train, rồi lấy trung bình k kết quả. Tốn thời gian gấp k lần nhưng
đáng tin hơn nhiều và tránh chuyện ăn may vì chia trúng tập dễ.

**Bias–variance:** bias cao = mô hình đơn giản quá, sai có hệ thống (underfitting).
Variance cao = nhạy quá với dữ liệu, đổi dữ liệu chút là kết quả đổi nhiều (overfitting).

Chống overfitting: thêm dữ liệu, regularization (L1/L2), dropout, early stopping, giảm độ
phức tạp mô hình.

## 1.8 Tự kiểm tra P1

<details><summary><b>1. Máy dự đoán 100 ca có bệnh, đúng 94. Thực tế có 120 ca bệnh. Precision và recall?</b></summary>

TP = 94, FP = 100 − 94 = 6, FN = 120 − 94 = 26.
Precision = 94/100 = **94%**. Recall = 94/120 ≈ **78%**.
</details>

<details><summary><b>2. Vì sao dự án OCR ưu tiên precision hơn recall?</b></summary>

Vì sửa nhầm một chữ vốn đang đúng làm hỏng dữ liệu — tệ hơn bỏ sót một lỗi. Chi phí của
FP cao hơn chi phí của FN.
</details>

<details><summary><b>3. Mô hình đạt accuracy 99%. Vì sao con số đó có thể vô nghĩa?</b></summary>

Nếu lớp dương chỉ chiếm 1%, mô hình luôn đoán "âm" cũng được 99% accuracy mà recall = 0.
Dữ liệu mất cân bằng thì phải xem precision/recall/F1.
</details>

<details><summary><b>4. MRR = 0,5 nghĩa là gì?</b></summary>

Trung bình đáp án đúng nằm quanh vị trí thứ 2 trong danh sách kết quả (1/2 = 0,5).
</details>

<details><summary><b>5. Vì sao cần cả validation lẫn test?</b></summary>

Validation dùng để chỉnh mô hình nên mô hình gián tiếp học từ nó. Lấy luôn tập đó làm điểm
cuối thì con số bị thổi phồng. Test phải giữ sạch, chỉ dùng một lần.
</details>

<details><summary><b>6. Một câu chọn đúng tool nhưng bị chấm 2/5. Điều đó nói lên gì?</b></summary>

Chọn đúng công cụ không đảm bảo trả lời tốt. Vì vậy phải đo hai chỉ số bổ sung nhau:
tool-selection accuracy (khách quan) và chất lượng câu trả lời (LLM-as-judge).
</details>

## 1.9 Tài liệu P1

| Nguồn | Dùng cho | Thời lượng |
|---|---|---|
| Google *Machine Learning Crash Course*, phần Classification | precision/recall/ROC, có bài tập tương tác | ~3 giờ |
| *Hands-On Machine Learning* (Géron), chương 3 | confusion matrix, đánh đổi precision/recall, cross-validation | 1 buổi |
| StatQuest (YouTube): "Confusion Matrix", "ROC and AUC" | hình dung trực quan, rất dễ vào | 30 phút |
| Tài liệu scikit-learn, mục `metrics` | tra công thức khi cần | tra cứu |

---

# P2 — Transformer, BERT, SBERT, embedding

> **Vì sao ưu tiên hai:** toàn bộ sản phẩm của bạn chạy trên embedding và LLM, nhưng bạn
> chưa giải thích được cái ruột. Đây là câu hỏi gần như **luôn có** trong phỏng vấn AI.

## 2.1 Từ chữ sang số: embedding là gì

Máy tính không hiểu chữ, chỉ hiểu số. Embedding là cách biến một đoạn text thành một
**dãy số** (vector), sao cho **nội dung giống nhau thì hai dãy số nằm gần nhau**.

```
"bãi biển đẹp"     →  [0.21, -0.88, 0.05, ... ]  ┐
                                                  ├─ gần nhau
"sandy beaches"    →  [0.19, -0.85, 0.07, ... ]  ┘

"lãi suất ngân hàng" → [-0.72, 0.31, 0.94, ... ]  ─ xa hẳn
```

Nhờ vậy tìm kiếm theo **ý nghĩa** chứ không theo mặt chữ: hỏi "bãi biển đẹp" vẫn ra đoạn
viết "sandy beaches" dù không trùng chữ nào. Đây chính là thứ làm dự án bilingual của bạn
chạy được giữa Hán cổ và tiếng Việt hiện đại.

Đo độ gần bằng **cosine similarity** — góc giữa hai vector. Bằng 1 là trùng hướng (rất
giống), bằng 0 là vuông góc (không liên quan).

## 2.2 Attention — trái tim của Transformer

Vấn đề trước Transformer: mô hình đọc câu **tuần tự** từ trái sang phải (RNN/LSTM). Câu
dài thì thông tin đầu câu bị quên dần, và không song song hoá được nên huấn luyện chậm.

Transformer giải bằng **attention**: khi xử lý một từ, mô hình **nhìn thẳng vào mọi từ
khác** trong câu cùng lúc và tự quyết định từ nào quan trọng.

Ví dụ kinh điển:

```
"Con mèo không băng qua đường vì NÓ quá mệt."

Khi xử lý từ "NÓ", attention chấm điểm liên quan với từng từ:

  Con   mèo   không  băng   qua   đường   vì    NÓ    quá   mệt
  0.05  0.61   0.02  0.03  0.02   0.12   0.03  ---   0.04  0.08
         ▲                          ▲
      cao nhất                   thứ nhì
```

Mô hình tự học được "NÓ" trỏ về "mèo" chứ không phải "đường". Không ai lập trình luật đó cả.

**Q, K, V — ba vai** (câu hỏi phỏng vấn rất hay gặp). Ví như tra thư viện:

| Ký hiệu | Tên | Vai trò |
|---|---|---|
| **Q** (Query) | câu hỏi | "tôi là từ NÓ, tôi đang tìm cái gì?" |
| **K** (Key) | nhãn dán | mỗi từ tự mô tả "tôi là loại thông tin gì" |
| **V** (Value) | nội dung | thông tin thật của từ đó |

Cách chạy: nhân Q với mọi K để ra **điểm liên quan** → chuẩn hoá thành tỉ lệ phần trăm
(softmax) → dùng tỉ lệ đó để **trộn các V** lại. Kết quả là biểu diễn mới của từ, đã ngấm
ngữ cảnh xung quanh.

**Multi-head attention:** làm nhiều bộ Q/K/V song song. Mỗi "đầu" học một kiểu quan hệ —
đầu này để ý ngữ pháp, đầu kia để ý đại từ trỏ về đâu.

**Positional encoding:** vì attention nhìn tất cả cùng lúc nên nó **không biết thứ tự từ**.
Phải cộng thêm một tín hiệu vị trí vào mỗi từ, nếu không "chó cắn người" và "người cắn chó"
sẽ giống hệt nhau với mô hình.

## 2.3 Encoder và Decoder — vì sao BERT khác GPT

Transformer gốc có hai nửa:

```
   ENCODER                          DECODER
   đọc & hiểu                       sinh chữ
   nhìn được CẢ HAI phía            chỉ nhìn được phía TRƯỚC
   ↓                                ↓
   BERT                             GPT, Gemini
   hợp: phân loại, tìm kiếm,        hợp: viết, chat, trả lời
        trích xuất
```

- **BERT = encoder.** Nhìn được cả trái lẫn phải của một từ nên "hiểu" rất tốt, nhưng
  không sinh văn bản dài được. Huấn luyện bằng cách che ngẫu nhiên vài từ rồi bắt đoán
  (masked language modelling).
- **GPT/Gemini = decoder.** Chỉ nhìn về trước, đoán từ tiếp theo — nên viết được, chat được.
- **Encoder–decoder (T5, ViT5).** Đọc trọn đầu vào rồi sinh đầu ra mới.

**Áp vào dự án của bạn:** ViT5 là encoder–decoder, và đó là **lựa chọn đúng** cho sửa lỗi
OCR, vì bài toán là "đọc nguyên câu bị lỗi → viết ra câu đã sửa" — cần cả hiểu lẫn sinh.
Nếu bị hỏi "sao không dùng BERT?", trả lời: BERT chỉ hiểu chứ không sinh được câu đã sửa.

## 2.4 SBERT — vì sao BERT thường không dùng làm embedding câu

Đây là chỗ nhiều người nhầm, và là câu hỏi phân loại ứng viên.

BERT gốc muốn so hai câu thì phải **nhét cả hai vào cùng một lượt chạy** (cross-encoder).
Chất lượng cao nhưng: so 1 câu hỏi với 10.000 tài liệu = **10.000 lần chạy model**. Không
xài được cho tìm kiếm.

**SBERT (Sentence-BERT)** sửa bằng hai ý:

1. **Kiến trúc siamese** — hai câu đi qua *cùng một* BERT một cách độc lập, mỗi câu ra một
   vector riêng.
2. **Pooling** — gộp các vector từ thành một vector câu (thường lấy trung bình).

Nhờ vậy **tính vector tài liệu trước một lần**, lúc tìm kiếm chỉ việc so vector — nhanh
hơn hàng nghìn lần.

```
Cross-encoder (BERT gốc)        Bi-encoder (SBERT)
┌──────────────────┐            ┌────────┐   ┌────────┐
│ [câu A ; câu B]  │            │ câu A  │   │ câu B  │
│      BERT        │            │  BERT  │   │  BERT  │
│    → điểm số     │            │   ↓    │   │   ↓    │
└──────────────────┘            │ vector │   │ vector │
 chính xác hơn                  └────┬───┘   └───┬────┘
 chậm, không tiền tính được          └── cosine ─┘
                                  nhanh, tiền tính được
```

**Cả hai đều có chỗ dùng** — và đây là nội dung tuần 4: dùng bi-encoder để lấy nhanh 50
ứng viên, rồi dùng cross-encoder **rerank** 50 cái đó cho chính xác. Vừa nhanh vừa đúng.

**LaBSE** (dự án bilingual của bạn) là một SBERT đa ngữ, huấn luyện sao cho câu cùng nghĩa
ở **các ngôn ngữ khác nhau** cũng nằm gần nhau. Đó chính là lý do nó bắc cầu được Hán cổ
và tiếng Việt mà **không cần dữ liệu gán nhãn** — tức "zero-shot" trong CV của bạn.

## 2.5 Code thật trong repo

`main_02_02.py` — chọn mô hình embedding và cắt chunk:

```python
EMBED_MODEL = os.environ.get("EMBED_MODEL", "models/gemini-embedding-001")
embeddings = GoogleGenerativeAIEmbeddings(model=EMBED_MODEL)

splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=128)
chunks = splitter.split_documents(docs)
```

Logic: 4 trang Wikivoyage → cắt thành **92 chunk**, mỗi chunk tối đa 1024 ký tự, hai chunk
liền kề **chồng lấn 128 ký tự**.

- Vì sao cắt: cả trang quá dài để nhét vào prompt, và phần lớn là nhiễu.
- Vì sao chồng lấn: để một câu bị cắt ngang vẫn còn nguyên vẹn ở ít nhất một mảnh.
- `Recursive...` nghĩa là nó ưu tiên cắt ở ranh giới tự nhiên (đoạn → câu → từ) trước khi
  buộc phải cắt giữa chừng.

## 2.6 Tự kiểm tra P2

<details><summary><b>1. Attention giải quyết vấn đề gì của RNN?</b></summary>

RNN đọc tuần tự nên quên thông tin ở xa và không song song hoá được. Attention cho mỗi từ
nhìn thẳng vào mọi từ khác cùng lúc, giữ được quan hệ xa và huấn luyện song song được.
</details>

<details><summary><b>2. Q, K, V là gì?</b></summary>

Query là câu hỏi của từ đang xét; Key là nhãn mô tả của từng từ; Value là nội dung thật.
Nhân Q với K ra điểm liên quan, softmax thành tỉ lệ, rồi trộn V theo tỉ lệ đó.
</details>

<details><summary><b>3. Vì sao Transformer cần positional encoding?</b></summary>

Attention nhìn mọi từ cùng lúc nên tự nó không biết thứ tự. Không có tín hiệu vị trí thì
"chó cắn người" và "người cắn chó" giống hệt nhau với mô hình.
</details>

<details><summary><b>4. BERT khác GPT chỗ nào?</b></summary>

BERT là encoder, nhìn được hai phía, mạnh ở hiểu/phân loại/tìm kiếm. GPT là decoder, chỉ
nhìn về trước, đoán từ tiếp theo nên sinh văn bản được.
</details>

<details><summary><b>5. Vì sao không dùng thẳng BERT làm embedding câu cho tìm kiếm?</b></summary>

BERT gốc là cross-encoder, phải chạy lại model cho từng cặp câu — so với 10.000 tài liệu
là 10.000 lần chạy. SBERT dùng kiến trúc siamese + pooling nên tính trước vector tài liệu
được, lúc tìm chỉ so vector.
</details>

<details><summary><b>6. Vì sao chọn ViT5 (encoder–decoder) cho sửa lỗi OCR?</b></summary>

Bài toán là đọc trọn câu bị lỗi rồi **sinh ra** câu đã sửa — cần cả hiểu lẫn sinh. BERT
thuần chỉ hiểu, không viết được câu mới.
</details>

## 2.7 Tài liệu P2

| Nguồn | Dùng cho | Thời lượng |
|---|---|---|
| Jay Alammar — *The Illustrated Transformer* | hiểu attention bằng hình, dễ nhất | 1 buổi |
| Jay Alammar — *The Illustrated BERT* | encoder, masked LM | 1 giờ |
| Trang chủ SBERT (sbert.net), mục Training Overview | bi-encoder vs cross-encoder | 1 giờ |
| 3Blue1Brown — loạt video về Transformer/attention | trực quan hoá toán học | 2 giờ |
| Stanford CS224N (YouTube) | học sâu và bài bản, chọn buổi về attention | tuỳ chọn |

---

# P3 — Tìm kiếm: keyword, vector, hybrid

> **Vì sao ưu tiên ba:** đây là mục duy nhất vừa là kiến thức thiếu, vừa là hạng mục đã có
> trong lộ trình sản phẩm (tuần 4). Làm một lần được cả hai, và ra được **bảng recall@k
> trước/sau** — thứ đáng giá nhất bạn có thể thêm vào CV lúc này.

## 3.1 Hai trường phái và điểm mù của mỗi bên

**Keyword search (BM25):** đếm từ khoá trùng nhau. Câu hỏi có chữ "Falmouth" thì tìm tài
liệu chứa chữ "Falmouth".

BM25 tinh vi hơn đếm thô ở ba chỗ:

1. Từ xuất hiện nhiều lần trong tài liệu → điểm cao hơn, nhưng **có bão hoà** (xuất hiện
   20 lần không gấp đôi 10 lần).
2. Từ **hiếm** trong toàn bộ kho thì đáng giá hơn từ phổ biến. Chữ "Falmouth" quý hơn chữ
   "the".
3. Tài liệu **ngắn** mà chứa từ đó thì liên quan hơn tài liệu dài lê thê.

**Vector search:** so theo ý nghĩa như đã học ở P2.

**Điểm mù của mỗi bên** — phần quan trọng nhất mục này:

| Tình huống | BM25 | Vector |
|---|---|---|
| "bãi biển đẹp" ↔ "sandy beaches" | ❌ không trùng chữ nào | ✅ hiểu là cùng nghĩa |
| Mã sản phẩm "SKU-99321" | ✅ khớp chính xác | ❌ vô nghĩa với model, dễ trả về mã na ná |
| Tên riêng lạ "Penzance" | ✅ tìm đúng | ⚠️ có thể trôi sang tên khác gần gần |
| Câu hỏi diễn đạt vòng vo | ❌ trượt | ✅ vẫn bắt được ý |

Nhìn bảng là hiểu ngay vì sao phải **hybrid** — hai bên bù đúng chỗ mù của nhau.

## 3.2 Trộn hai bảng xếp hạng: RRF

Vấn đề: BM25 cho điểm kiểu này, vector cho điểm kiểu khác, không cộng thẳng được.

**RRF (Reciprocal Rank Fusion)** giải bằng cách bỏ hết điểm số, **chỉ dùng thứ hạng**:

```
điểm_RRF(tài liệu) = Σ  1 / (k + hạng của nó trong từng danh sách)      (k thường = 60)
```

Ví dụ tài liệu A đứng hạng 1 ở BM25 và hạng 3 ở vector:

```
1/(60+1) + 1/(60+3) = 0,0164 + 0,0159 = 0,0323
```

Tài liệu nào **được cả hai bên xếp cao** sẽ nổi lên trên. Đơn giản, không cần chỉnh trọng
số, chạy tốt trong thực tế.

## 3.3 Reranking — bước tinh

Sau khi hybrid lấy ra 50 ứng viên, dùng **cross-encoder** (P2 mục 2.4) chấm lại 50 cái đó
cho chính xác, lấy top 5.

```
10.000 tài liệu
      │ bi-encoder + BM25   ← nhanh, thô
      ▼
   50 ứng viên
      │ cross-encoder       ← chậm, tinh (chỉ chạy 50 lần, chấp nhận được)
      ▼
    5 kết quả cuối
```

Đây là kiến trúc chuẩn của mọi hệ tìm kiếm hiện đại: **retrieve rồi rerank**.

## 3.4 Code thật hiện tại và sẽ đổi thành gì

Hiện tại trong `main_02_02.py` — thuần vector:

```python
@tool(description="Search travel information about destinations in England. ...")
def search_travel_info(query: str) -> str:
    docs = get_travel_info_retriever().invoke(query)
    top = docs[:4] if isinstance(docs, list) else docs
    return "\n---\n".join(d.page_content for d in top)
```

Logic: nhận truy vấn → retriever tìm trong Chroma theo cosine → lấy 4 đoạn đầu → nối lại
thành một chuỗi trả cho LLM. `\n---\n` để LLM nhìn ra ranh giới giữa các đoạn.

**Tuần 4 sẽ thành:** BM25 chạy song song với vector → trộn bằng RRF → rerank → trả top 4,
kèm **link nguồn** cho mỗi đoạn (citations). Rồi đo recall@k trước/sau để chứng minh bằng
số là nó tốt lên thật.

## 3.5 Tự kiểm tra P3

<details><summary><b>1. BM25 hơn đếm từ thô ở ba điểm nào?</b></summary>

Bão hoà tần suất (lặp nhiều không tăng điểm tuyến tính); ưu tiên từ hiếm trong kho; chuẩn
hoá theo độ dài tài liệu.
</details>

<details><summary><b>2. Cho một ví dụ vector search thua keyword search.</b></summary>

Mã sản phẩm hoặc số hiệu như "SKU-99321": embedding không nắm được chuỗi ký tự chính xác
nên dễ trả về mã na ná, còn BM25 khớp đúng tuyệt đối.
</details>

<details><summary><b>3. RRF hoạt động thế nào và vì sao không cộng thẳng điểm?</b></summary>

Vì hai hệ cho điểm theo thang khác nhau, cộng thẳng là vô nghĩa. RRF bỏ điểm, chỉ lấy
1/(k+hạng) rồi cộng lại, nên tài liệu được cả hai bên xếp cao sẽ nổi lên.
</details>

<details><summary><b>4. Vì sao không dùng cross-encoder cho toàn bộ kho luôn cho chính xác?</b></summary>

Vì phải chạy model cho từng cặp (câu hỏi, tài liệu) — 10.000 tài liệu là 10.000 lần chạy,
quá chậm. Nên chỉ dùng nó rerank vài chục ứng viên đã lọc thô.
</details>

<details><summary><b>5. Recall@5 = 0,8 nghĩa là gì?</b></summary>

Với 80% số câu hỏi, đáp án đúng nằm trong 5 kết quả đầu.
</details>

## 3.6 Tài liệu P3

| Nguồn | Dùng cho |
|---|---|
| Pinecone Learning Center — *Hybrid Search* và *Rerankers* | giải thích ngắn, có hình, đúng trọng tâm |
| Bài blog Elastic về BM25 | hiểu công thức bằng ví dụ |
| Tài liệu `rank_bm25` (thư viện Python) | chính thư viện sẽ dùng ở tuần 4 |
| sbert.net — *Retrieve & Re-Rank* | đúng kiến trúc hai tầng ở mục 3.3 |

---

# P4 — Serving model: từ gọi API đến tự host

> **Vì sao ưu tiên bốn:** đây là thứ tách "AI Engineer" khỏi "người gọi API". Hiện bạn gọi
> Gemini qua mạng; nhiều JD fresher đòi kinh nghiệm chạy model trên hạ tầng của mình.

## 4.1 Hai cách dùng model

| | Gọi API (hiện tại) | Tự host |
|---|---|---|
| Ví dụ | Gemini, OpenAI | Ollama, vLLM |
| Tiền | Trả theo token | Trả tiền máy (GPU) |
| Dữ liệu | Gửi ra ngoài | **Không rời hạ tầng** — lý do lớn nhất của ngân hàng, bệnh viện |
| Độ trễ | Phụ thuộc mạng | Thấp hơn nếu máy khoẻ |
| Vận hành | Không phải lo | Phải tự lo bộ nhớ, hàng đợi, cập nhật |

## 4.2 Ba khái niệm phải biết khi tự host

**KV cache.** Khi sinh chữ, model phải nhìn lại toàn bộ những gì đã sinh. Nếu mỗi từ mới
lại tính lại từ đầu thì cực chậm. KV cache lưu lại K và V (P2 mục 2.2) của các token
trước, nên mỗi từ mới chỉ tính phần thêm. Đổi lại: **cache ngốn rất nhiều VRAM**, và đây
thường là thứ giới hạn số người dùng đồng thời chứ không phải sức tính toán.

**Batching.** Gom nhiều request chạy chung một lượt để tận dụng GPU. vLLM làm *continuous
batching* — request mới nhảy vào giữa chừng được, không phải chờ cả lô xong.

**Context window.** Số token tối đa model nhìn được trong một lượt (đầu vào + đầu ra).
Vượt là bị cắt. Đây là lý do RAG tồn tại: thay vì nhét cả kho tài liệu vào, chỉ nhét vài
đoạn liên quan nhất.

## 4.3 Sẽ đưa gì vào sản phẩm

Thêm lựa chọn chạy model local qua **Ollama** bên cạnh Gemini. Điểm hay: `main_02_02.py`
chỉ có đúng một dòng tạo model —

```python
llm_model = ChatGoogleGenerativeAI(model=CHAT_MODEL, temperature=0)
```

— nên đổi sang `ChatOllama(model="qwen2.5")` là xong, **phần đồ thị agent không đụng gì**.
Đây lại là một minh chứng cho nguyên tắc kiến trúc đã nói ở [MENTOR.md](MENTOR.md) mục 3.

Ghép thẳng vào **bảng so sánh model/chi phí của tuần 3**: Gemini flash-lite vs Gemini flash
vs Qwen chạy local, so accuracy / p95 / $ per 1k query. Bạn đã có sẵn eval harness và
Prometheus đo chi phí nên bảng này gần như tự sinh ra.

## 4.4 Tự kiểm tra P4

<details><summary><b>1. Vì sao một công ty chọn tự host model dù đắt hơn?</b></summary>

Dữ liệu không được rời khỏi hạ tầng (ngân hàng, y tế, quốc phòng); không phụ thuộc nhà
cung cấp; kiểm soát được độ trễ và phiên bản model.
</details>

<details><summary><b>2. KV cache là gì và đánh đổi gì?</b></summary>

Lưu K và V của các token đã sinh để không phải tính lại từ đầu ở mỗi token mới. Đổi lại nó
ngốn VRAM, và thường chính nó giới hạn số request đồng thời.
</details>

<details><summary><b>3. Context window liên quan gì đến RAG?</b></summary>

Không thể nhét cả kho tài liệu vào cửa sổ ngữ cảnh. RAG chỉ chọn vài đoạn liên quan nhất
để đưa vào, vừa vặn cửa sổ và giảm nhiễu.
</details>

## 4.5 Tài liệu P4

| Nguồn | Dùng cho |
|---|---|
| ollama.com — Quickstart | chạy model local trên máy bạn trong 10 phút |
| Tài liệu vLLM, mục PagedAttention | hiểu KV cache và continuous batching |
| LangChain docs — `ChatOllama` | ghép vào đúng repo này |

---

# P5 — Fine-tuning, LoRA, QLoRA, quantization

> **Vì sao ưu tiên năm:** đây là nhóm keyword nóng, nhưng tốn thời gian nhất mà lợi ích
> phỏng vấn tương đương P3/P4. Làm sau, và bạn đã có nền vì từng fine-tune ViT5.

## 5.1 Ba mức can thiệp vào model

```
Prompt engineering  →  chỉ đổi câu lệnh, không đụng trọng số        (rẻ nhất)
RAG                 →  đưa thêm tài liệu vào prompt                 (bạn đang dùng)
Fine-tuning         →  đổi trọng số của model                       (đắt nhất)
```

Câu hỏi phỏng vấn kinh điển: **"khi nào fine-tune, khi nào RAG?"**

- Cần model biết **kiến thức mới, hay thay đổi** → RAG. Thêm tài liệu là xong, không phải
  huấn luyện lại.
- Cần model đổi **cách hành xử, văn phong, định dạng đầu ra**, hoặc làm một tác vụ hẹp rất
  giỏi → fine-tune. Đây đúng là trường hợp dự án OCR của bạn: sửa lỗi OCR tiếng Việt là
  một tác vụ hẹp, model gốc không làm tốt được bằng prompt.

## 5.2 LoRA — vì sao không fine-tune toàn bộ

Fine-tune đầy đủ nghĩa là cập nhật **mọi** trọng số. Model 7 tỉ tham số cần vài chục GB
VRAM chỉ để chứa gradient và optimizer — máy thường không kham nổi.

**LoRA (Low-Rank Adaptation):** đóng băng toàn bộ trọng số gốc, chỉ **chèn thêm hai ma
trận nhỏ** cạnh các lớp quan trọng và chỉ huấn luyện hai cái đó.

```
        đầu vào
           │
     ┌─────┴─────┐
     ▼           ▼
 W (đóng băng)  A → B   ← chỉ hai ma trận nhỏ này được học
     │           │
     └─────┬─────┘
        cộng lại
```

Ý tưởng toán học: thay đổi cần thiết cho một tác vụ hẹp thường có **hạng thấp** (low rank),
nên biểu diễn được bằng tích hai ma trận gầy A (d×r) và B (r×d) với r rất nhỏ, thường 8–64.

Kết quả: số tham số phải huấn luyện giảm **hàng trăm đến hàng nghìn lần**, và file kết quả
chỉ vài MB thay vì vài GB. Muốn nhiều tác vụ thì giữ một model gốc và nhiều "adapter" nhỏ,
tráo qua lại.

**QLoRA** = LoRA + nén model gốc xuống **4-bit**. Nhờ vậy fine-tune được model 7B trên một
GPU tiêu dùng, thậm chí Colab miễn phí.

## 5.3 Quantization

Trọng số mặc định lưu ở 16 hoặc 32 bit. **Quantization** nén xuống 8-bit hoặc 4-bit.

```
FP16   →  INT8   →  INT4
nặng      nhẹ 2×    nhẹ 4×
chuẩn     ~như cũ   tụt nhẹ chất lượng
```

Được: bộ nhớ nhỏ hơn, chạy nhanh hơn, máy yếu cũng chạy được. Mất: chất lượng giảm một
chút, và mức 4-bit thì tuỳ tác vụ mà giảm nhiều hay ít.

## 5.4 Sẽ đưa gì vào sản phẩm

Fine-tune bằng LoRA **một model nhỏ** — thực tế nhất là một **reranker cho tiếng Việt**,
dùng chính dữ liệu Hán-Nôm của luận văn. Rẻ, chạy được trên Colab free, và nối thẳng vào
bước rerank ở P3. Kết quả đo được: recall@k / MRR trước và sau khi thay reranker.

## 5.5 Tự kiểm tra P5

<details><summary><b>1. Khi nào chọn RAG, khi nào chọn fine-tune?</b></summary>

RAG khi cần kiến thức mới hoặc hay thay đổi. Fine-tune khi cần đổi hành vi, văn phong,
định dạng đầu ra, hoặc làm rất giỏi một tác vụ hẹp.
</details>

<details><summary><b>2. LoRA giảm chi phí bằng cách nào?</b></summary>

Đóng băng trọng số gốc, chỉ chèn và huấn luyện hai ma trận hạng thấp A và B. Số tham số
cần học giảm hàng trăm đến hàng nghìn lần, file adapter chỉ vài MB.
</details>

<details><summary><b>3. QLoRA thêm gì so với LoRA?</b></summary>

Nén model gốc xuống 4-bit trước khi gắn adapter, nhờ đó fine-tune được model lớn trên một
GPU tiêu dùng.
</details>

<details><summary><b>4. Quantization đánh đổi gì?</b></summary>

Đổi một chút chất lượng lấy bộ nhớ nhỏ hơn và tốc độ cao hơn. INT8 gần như không mất gì,
INT4 thì tuỳ tác vụ.
</details>

## 5.6 Tài liệu P5

| Nguồn | Dùng cho |
|---|---|
| Sebastian Raschka — bài blog về LoRA | giải thích rõ nhất về hạng thấp và adapter |
| Hugging Face PEFT — docs | chính thư viện sẽ dùng |
| Bài báo QLoRA (đọc phần Abstract + Method) | hiểu 4-bit + paged optimizer |
| Hugging Face — *Fine-tune with LoRA* notebook | làm theo được ngay trên Colab |

---

# P6 — Tokenizer & tiền xử lý NLP

> **Vì sao ưu tiên cuối:** thời LLM thì phần lớn tiền xử lý cổ điển không còn dùng. Nhưng
> **tokenizer thì bắt buộc hiểu**, vì nó dính trực tiếp đến token và chi phí — mà bạn đang
> đo chi phí trong Prometheus.

## 6.1 Token không phải là từ

Model không đọc chữ, nó đọc **token** — mảnh nhỏ hơn từ:

```
"unbelievable"  →  ["un", "believ", "able"]        3 token
"Hồ Chí Minh"   →  ["H", "ồ", " Chí", " Minh"]     nhiều token hơn tiếng Anh
```

Cách chia này gọi là **BPE / subword**: bắt đầu từ ký tự, ghép dần những cặp hay đi cùng
nhau thành mảnh lớn hơn. Nhờ vậy từ lạ chưa từng gặp vẫn tách được, không bị "không hiểu".

**Hệ quả thực tế cho bạn:** tiếng Việt tốn nhiều token hơn tiếng Anh cho cùng một nội
dung, nên **cùng câu hỏi mà hỏi bằng tiếng Việt thì đắt hơn**. Đây là chi tiết rất đáng
nói khi trình bày phần đo chi phí — nó cho thấy bạn hiểu con số mình đo.

Nối thẳng với code trong `metrics.py`:

```python
input_tokens = usage.get("input_tokens", 0)
output_tokens = usage.get("output_tokens", 0)
cost = (input_tokens * price[0] + output_tokens * price[1]) / 1_000_000
```

Chú ý giá **input và output khác nhau** (0,25 và 1,50 USD cho 1 triệu token) — output đắt
gấp 6 lần vì phải sinh từng token một, tốn tính toán hơn nhiều so với đọc.

## 6.2 Tiền xử lý cổ điển — biết để nói, không cần dự án

| Kỹ thuật | Làm gì | Còn dùng không |
|---|---|---|
| Xoá từ dừng | Bỏ "the", "là", "của" | Có, cho BM25/TF-IDF. Không cần cho LLM |
| Stemming / Lemmatization | Đưa từ về gốc ("running" → "run") | Chủ yếu cho tìm kiếm cổ điển |
| Sửa chính tả | Chuẩn hoá lỗi gõ | Hữu ích ở khâu nhập liệu |
| **Word segmentation** | Tách từ tiếng Việt: "học sinh" là **một** từ, không phải hai | Quan trọng với tiếng Việt; thư viện: underthesea, pyvi |
| Chuẩn hoá Unicode | "hoà" và "hòa" phải như nhau | **Luôn cần** với tiếng Việt |

Riêng hai dòng cuối đáng nhớ vì bạn làm dữ liệu tiếng Việt và Hán-Nôm — chuẩn hoá Unicode
là loại lỗi âm thầm phá hỏng cả pipeline mà rất khó phát hiện.

## 6.3 Tự kiểm tra P6

<details><summary><b>1. Vì sao hỏi bằng tiếng Việt tốn tiền hơn tiếng Anh?</b></summary>

Tokenizer được huấn luyện chủ yếu trên tiếng Anh, nên tiếng Việt bị cắt thành nhiều token
hơn cho cùng một nội dung. Nhiều token hơn = trả tiền nhiều hơn.
</details>

<details><summary><b>2. Vì sao token output đắt hơn token input?</b></summary>

Đọc đầu vào xử lý song song được, còn sinh đầu ra phải làm tuần tự từng token, tốn tính
toán hơn nhiều.
</details>

<details><summary><b>3. Word segmentation là gì và vì sao tiếng Việt cần?</b></summary>

Là tách chuỗi thành từ có nghĩa. Tiếng Việt viết rời từng âm tiết nên "học sinh" dễ bị
hiểu thành hai từ riêng, làm hỏng tìm kiếm theo từ khoá.
</details>

## 6.4 Tài liệu P6

| Nguồn | Dùng cho |
|---|---|
| Hugging Face NLP Course, chương 6 (Tokenizers) | BPE, WordPiece, giải thích bằng code |
| OpenAI Tokenizer (trang web) | dán thử tiếng Việt vs tiếng Anh, thấy ngay chênh lệch |
| underthesea (GitHub) | tách từ tiếng Việt |

---

## Phần 7 — Kịch bản nói về từng dòng CV

Luyện nói to từng đoạn dưới đây. Mỗi đoạn khoảng 30 giây — đủ để trả lời "kể tôi nghe về
dự án này" mà không lan man.

**Multi-tool AI Agent**

> *"Đây là một agent theo mẫu ReAct: mô hình tự quyết định gọi công cụ nào và theo thứ tự
> nào, không có bước nào được lập trình cứng. Nó có hai công cụ — tìm kiếm ngữ nghĩa trên
> kho Wikivoyage và tra thời tiết thật. Tôi dựng đồ thị LangGraph bằng tay để hiểu cơ chế,
> rồi làm lại bằng component dựng sẵn để đối chiếu. Phần phục vụ là FastAPI có streaming
> SSE, đóng gói Docker multi-stage chạy non-root, và đo bằng Prometheus. Tôi đánh giá nó
> bằng một bộ eval 8 câu: 100% chọn đúng công cụ, kèm điểm chất lượng do LLM chấm,
> chi phí khoảng 0,0007 đô mỗi câu hỏi."*

**Han-Nom corpus (luận văn)**

> *"Tôi xây một hệ thu thập tự động bằng Playwright có chặn request GraphQL, lấy hơn 55
> nghìn bài đăng, kèm cơ chế khử trùng lặp và checkpoint để chạy nhiều ngày không mất tiến
> độ. Phần khó nhất là gán nhãn: tôi thiết kế một cổng xác thực dùng mô hình thị giác đọc
> ảnh làm mốc đối chiếu, còn nhãn thì lấy nguyên văn từ caption chứ không lấy từ model —
> nhờ vậy loại được hallucination. Kết quả là hơn 10 nghìn mẫu có nhãn với độ căn chỉnh
> ký tự trung bình 98,2%, và tôi giảm được một nửa chi phí bằng Batch API."*

**OCR error correction**

> *"Tôi fine-tune ViT5 để sửa lỗi OCR trên văn bản y tế scan. Đạt 94% precision và 90%
> recall. Tôi ưu tiên precision vì sửa hỏng một chữ vốn đang đúng thì tệ hơn bỏ sót một
> lỗi. ViT5 là kiến trúc encoder-decoder nên hợp bài toán này — cần vừa hiểu câu lỗi vừa
> sinh ra câu đã sửa."*

**Bilingual retrieval**

> *"Bài toán là truy hồi giữa Hán cổ và tiếng Việt hiện đại, không có dữ liệu gán nhãn.
> Tôi dùng LaBSE — một mô hình embedding đa ngữ — nên câu cùng nghĩa ở hai ngôn ngữ nằm
> gần nhau trong không gian vector, làm được zero-shot. Sau đó tôi rerank bằng cách kết
> hợp điểm ngữ nghĩa với khớp từ khoá trên thực thể do model trích ra. Tôi tối ưu độ trễ
> truy vấn từ 3 giây xuống 0,4 giây."*

**BestHR Solution**

> *"Tôi làm 3 tháng ở đó với vai trò software engineer: xây và bảo trì website công ty,
> tham gia một sản phẩm OCR chuyển tài liệu scan thành văn bản tìm kiếm được, và phát
> triển tính năng cho hệ quản lý tài liệu đi kèm."*

**Câu hay bị hỏi tiếp: "khó nhất là gì?"** — đừng trả lời chung chung. Chọn một trong hai:
lỗi vector store rỗng trong Docker (lỗi im lặng, xem [MENTOR.md](MENTOR.md) mục 14), hoặc
chuyện phải đổi nền tảng deploy giữa chừng khi phát hiện Docker Space thành trả phí.

---

## Phần 8 — Lịch 6 tuần

| Tuần | Làm sản phẩm | Học song song | Kết quả đo được |
|---|---|---|---|
| 1 | Eval gate trong CI | **P1** đánh giá mô hình | CI chặn merge khi accuracy tụt |
| 2 | Thêm Ollama local + bảng so sánh model | **P4** serving | Bảng accuracy / p95 / $ của 3 model |
| 3 | Guardrails + test prompt injection | **P2** Transformer/BERT/SBERT | Test chứng minh chunk độc không chiếm quyền |
| 4 | Hybrid RAG + citations | **P3** BM25/rerank | **Bảng recall@k trước/sau** |
| 5 | LoRA fine-tune reranker tiếng Việt | **P5** LoRA/quantization | MRR trước/sau khi thay reranker |
| 6 | Tái cấu trúc package | **P6** + luyện phỏng vấn | Trả trôi 23 câu ở MENTOR.md |

**Cách tự kiểm tra tiến độ:** cuối mỗi tuần, mở phần "tự kiểm tra" của mục vừa học và trả
lời **không nhìn đáp án**. Sai quá 2 câu thì đọc lại mục đó trước khi sang tuần mới.

**Một điều thẳng thắn để kết:** thứ đang chặn bạn không phải thiếu kiến thức mới, mà là
chưa nói trôi chảy về những gì đã làm. Với hồ sơ hiện tại, một buổi luyện trả lời 23 câu
trong [MENTOR.md](MENTOR.md) có giá trị ngang một tuần học LoRA. Học thêm là để đi xa hơn;
còn để **có việc**, P1 và P2 đã là đủ đòn bẩy.
