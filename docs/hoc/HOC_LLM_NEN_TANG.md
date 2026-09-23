# LLM nền tảng — vì sao model bịa, và chọn model thế nào cho đúng

> Các tài liệu khác dạy **dùng** LLM: gọi tool, RAG, dựng agent. Bài này dạy **bản thân cái
> model**: nó sinh chữ kiểu gì, vì sao nó bịa, ép nó trả JSON thế nào, và chọn model theo
> tiêu chí gì.
>
> Mọi con số lấy từ `evals/model_comparison.md` — **7 model đo thật** bằng
> `evals/compare_models.py`, cùng bộ eval, cùng tool, cùng prompt, chỉ đổi model.

**Mục lục**

1. [Model thực chất làm gì: đoán chữ tiếp theo](#1-model-thực-chất-làm-gì-đoán-chữ-tiếp-theo)
2. [Token — đơn vị tính tiền và đơn vị suy nghĩ](#2-token--đơn-vị-tính-tiền-và-đơn-vị-suy-nghĩ)
3. [Vì sao model bịa (hallucination)](#3-vì-sao-model-bịa-hallucination)
4. [Temperature và các nút điều chỉnh](#4-temperature-và-các-nút-điều-chỉnh)
5. [Structured output — ép model trả JSON](#5-structured-output--ép-model-trả-json)
6. [Cửa sổ ngữ cảnh và cái bẫy "nhét hết vào"](#6-cửa-sổ-ngữ-cảnh-và-cái-bẫy-nhét-hết-vào)
7. [Chọn model: 7 model đo thật](#7-chọn-model-7-model-đo-thật)
8. [Kỹ thuật giảm chi phí](#8-kỹ-thuật-giảm-chi-phí)
9. [Tự kiểm tra](#9-tự-kiểm-tra)
10. [Trả lời phỏng vấn](#10-trả-lời-phỏng-vấn)

---

## 1. Model thực chất làm gì: đoán chữ tiếp theo

Bỏ hết mọi thứ huyền bí đi, một LLM làm **đúng một việc**: cho một chuỗi token, tính **xác
suất cho token tiếp theo**, rồi bốc một cái ra. Lặp lại.

```
"Thủ đô của nước Pháp là"  →  Paris  87%
                              Lyon    3%
                              một     2%
                              ...
```

Mọi thứ khác — trả lời câu hỏi, viết code, gọi tool — đều **mọc ra từ một cơ chế đó**.

Hai hệ quả phải nắm, vì gần như mọi hành vi kỳ lạ của LLM đều truy về đây:

**1. Model không "tra cứu" gì cả.** Nó không có cơ sở dữ liệu bên trong để đối chiếu. Nó chỉ
sinh ra chuỗi *nghe có vẻ đúng* dựa trên thống kê của dữ liệu huấn luyện. Đây là gốc rễ của
mục 3.

**2. Model không biết mình biết gì.** Không có cơ chế nào bảo *"chỗ này tôi không chắc"*. Một
sự thật và một điều bịa ra đều được sinh bằng đúng một cách, với cùng giọng tự tin.

> Đây là lý do `travel-ai-agent` có câu *"Never invent town names from your own knowledge"*
> trong system prompt. Không cấm thì model lấy tên thị trấn từ thống kê và **không có gì phân
> biệt** được nó với tên lấy từ RAG.

---

## 2. Token — đơn vị tính tiền và đơn vị suy nghĩ

Model không nhìn thấy ký tự, cũng không nhìn thấy từ. Nó nhìn thấy **token** — mẩu văn bản
được cắt ra theo tần suất xuất hiện.

```
"unhappiness"  →  ["un", "happi", "ness"]      3 token
"the"          →  ["the"]                       1 token
"Cornwall"     →  ["Corn", "wall"]              2 token
```

Ước lượng nhanh: tiếng Anh **~4 ký tự = 1 token**. Tiếng Việt **tốn token hơn nhiều** vì ít
xuất hiện trong dữ liệu huấn luyện — cùng nội dung, prompt tiếng Việt có thể đắt gấp 2-3 lần
tiếng Anh.

> **Chi tiết thực dụng:** đây là một lý do system prompt của dự án này viết bằng **tiếng Anh**
> dù tài liệu viết tiếng Việt. Không phải sính ngoại — nó rẻ hơn và model theo sát hơn.

Vì sao token quan trọng:

| | |
|---|---|
| **Tính tiền theo token** | Giá luôn niêm yết dạng `$/1M token`, và **vào rẻ hơn ra** — xem mục 7 |
| **Giới hạn theo token** | Cửa sổ ngữ cảnh đo bằng token, không phải số chữ |
| **Đếm nhầm là ước sai tiền** | Đếm bằng số từ có thể lệch 30-50% |

Cách đếm token của một câu hỏi thật trong dự án này: `metrics.py` đọc `usage_metadata` mà API
trả về sau **mỗi** lần gọi model — không tự ước lượng. Và quan trọng: một câu hỏi gọi 3 tool
là **4 lần gọi model**, nên phải cộng cả 4 chứ không lấy mỗi lần cuối.

---

## 3. Vì sao model bịa (hallucination)

Đây là câu hỏi phỏng vấn gần như chắc chắn gặp. Câu trả lời tệ: *"vì AI chưa hoàn hảo"*. Câu
trả lời tốt bám vào cơ chế ở mục 1.

**Model được huấn luyện để sinh chuỗi *có khả năng xuất hiện cao*, không phải chuỗi *đúng*.**
Với model, một cái tên có thật và một cái tên bịa nghe hợp lý là **cùng một loại việc**. Nó
không có khái niệm "sự thật" để mà vi phạm.

Bốn tình huống model hay bịa nhất:

| Tình huống | Vì sao |
|---|---|
| Hỏi chi tiết hiếm (số liệu, ngày tháng, tên riêng, mã số) | Ít dữ liệu huấn luyện → phân bố xác suất tản mát → bốc bừa |
| Hỏi chuyện xảy ra **sau** ngày cắt dữ liệu | Không có thông tin, nhưng vẫn phải sinh ra chữ gì đó |
| Câu hỏi cài sẵn giả định sai | *"Vì sao X gây ra Y?"* → model giải thích thay vì phản bác |
| Ép trả lời khi không đủ dữ kiện | Không có đường "im lặng"; sinh chữ là hành vi mặc định |

### Bốn cách giảm, xếp theo hiệu quả

| Cách | Hiệu quả | Dự án này |
|---|---|---|
| **RAG** — đưa dữ liệu thật vào prompt | Cao nhất | ✅ `search_travel_info` |
| **Gọi tool** để lấy dữ liệu sống | Cao nhất | ✅ `weather_forecast` |
| **Cấm tường minh** dùng trí nhớ riêng | Trung bình | ✅ System prompt |
| **Bắt trích dẫn nguồn** | Trung bình — sai thì dễ soi ra | ✅ Đánh số `[1] [2]` |
| Hạ `temperature` | **Thấp** — model vẫn bịa, chỉ bịa nhất quán hơn | — |

> **Điểm hay bị hiểu nhầm:** hạ temperature về 0 **không** chữa được bịa. Nó chỉ làm model
> luôn bốc token có xác suất cao nhất — nếu điều bịa ra là thứ có xác suất cao nhất thì nó
> vẫn bịa, và bịa y hệt nhau mỗi lần.

**Không có cách nào diệt hẳn.** Nên cách làm đúng là thiết kế để **kiểm chứng được**: trích
dẫn nguồn, đo bằng eval, và với việc có hậu quả thì bắt người duyệt.

---

## 4. Temperature và các nút điều chỉnh

Sau khi model tính xong xác suất, phải **bốc** một token. Cách bốc là chỗ mấy nút này tác động.

| Nút | Làm gì | Đặt thế nào |
|---|---|---|
| `temperature` | Làm phân bố xác suất **nhọn hơn hay bẹt hơn** | `0`–`0.3` cho việc cần chính xác; `0.7`–`1.0` cho viết sáng tạo |
| `top_p` | Chỉ bốc trong nhóm token cộng dồn đủ p% xác suất | `0.9` là mặc định hợp lý |
| `top_k` | Chỉ bốc trong k token khả dĩ nhất | Ít dùng khi đã có `top_p` |
| `max_tokens` | Chặn độ dài đầu ra | Luôn đặt — **chặn hoá đơn** |

**`temperature = 0` gần như tất định nhưng KHÔNG đảm bảo.** Cùng prompt vẫn có thể ra kết quả
khác nhau do tính toán dấu phẩy động song song trên GPU và do nhà cung cấp âm thầm cập nhật
model. Đây là lý do **không được dùng lời gọi LLM thật làm unit test** (xem
[MENTOR.md](../MENTOR.md) mục 11).

Với agent gọi tool thì **temperature thấp** gần như luôn đúng: bạn cần nó chọn đúng tool và
đúng tham số, không cần nó sáng tạo.

---

## 5. Structured output — ép model trả JSON

Model sinh chữ tự do. Nhưng code của bạn cần dữ liệu có cấu trúc. Ba mức, từ tệ tới tốt:

**Mức 1 — xin trong prompt (tệ).** *"Trả lời dạng JSON"*. Model thường nghe lời, nhưng
**thỉnh thoảng** thêm ` ```json `, thêm lời dẫn *"Đây là JSON của bạn:"*, hoặc thiếu dấu ngoặc.
Và "thỉnh thoảng" nghĩa là **sẽ hỏng trên production**.

**Mức 2 — chế độ JSON.** Nhà cung cấp đảm bảo đầu ra là JSON hợp lệ. Đã tốt hơn nhiều, nhưng
chưa đảm bảo **đúng các trường bạn cần**.

**Mức 3 — theo schema (tốt nhất).** Bạn đưa schema, nhà cung cấp đảm bảo đầu ra khớp. Đây
cũng chính là cơ chế **tool calling** đang chạy dưới `bind_tools()`:

```python
llm_with_tools = llm_model.bind_tools(TOOLS)
```

`bind_tools` đóng gói mô tả tool thành **JSON schema** gửi kèm mỗi request. Model trả về
`tool_calls` với `{name, args}` **đã khớp schema** — không cần bạn tự bóc chuỗi.

> **Nhận thức quan trọng:** *tool calling chính là structured output*. Model không chạy hàm
> nào cả — nó chỉ trả về JSON có cấu trúc mô tả **ý định** gọi hàm. Code của bạn mới thực thi.
> Hiểu điều này là hiểu vì sao "mô tả tool là prompt engineering, không phải comment".

**Vẫn phải kiểm tra ở phía mình.** Schema đảm bảo *hình dạng*, không đảm bảo *ý nghĩa*: model
vẫn có thể gửi `town: "Atlantis"` đúng kiểu chuỗi mà không có thật. Đó là lý do
`weather_forecast` bắt lỗi và trả kết quả có cấu trúc thay vì ném exception.

---

## 6. Cửa sổ ngữ cảnh và cái bẫy "nhét hết vào"

**Cửa sổ ngữ cảnh** = tổng token model đọc được trong một lần gọi (prompt + lịch sử + đầu ra).
Model đời mới có cửa sổ rất lớn — hàng trăm nghìn token — và điều đó sinh ra một cám dỗ:
*"cửa sổ to thế thì nhét cả tài liệu vào, cần gì RAG?"*

Ba lý do vẫn cần RAG:

| Vấn đề | Cụ thể |
|---|---|
| **Tiền** | Trả token cho *mỗi* câu hỏi. Nhét 100K token vào 1000 câu hỏi = 100 triệu token |
| **"Lost in the middle"** | Model chú ý tốt phần **đầu** và **cuối** prompt, phần **giữa** kém hẳn. Nhồi nhiều không đồng nghĩa dùng được nhiều |
| **Độ trễ** | Prompt càng dài, thời gian tới token đầu tiên càng lâu |

**Lost in the middle** là kết quả nghiên cứu đã lặp lại được nhiều lần, và là lý do RAG lấy
**4 đoạn liên quan** thay vì nhồi cả 92 chunk. Ít mà đúng chỗ hơn nhiều mà loãng.

Đây cũng là lý do `travel-ai-agent` cắt lịch sử bằng `trim_messages` dù checkpointer giữ toàn
bộ hội thoại: **lưu hết là chuyện của database, gửi đi là chuyện của hoá đơn.**

---

## 7. Chọn model: 7 model đo thật

Cách chọn model của phần lớn người ta: lấy cái mới nhất. `evals/compare_models.py` chạy cùng
một bộ eval trên **7 model**, chỉ đổi model:

| Model | Giá in/out ($/1M) | Tool-selection | Chất lượng | $/1000 câu |
|---|---|:-:|:-:|--:|
| `gemini-2.5-flash-lite` | 0.10 / 0.40 | 100% | 3.5/5 | **$0.21** |
| `gemini-3.1-flash-lite` | 0.25 / 1.50 | 100% | 4.5/5 | $1.19 |
| `gemini-3.5-flash-lite` | 0.30 / 2.50 | 100% | 4.5/5 | $1.55 |
| **`gemini-2.5-flash`** | 0.30 / 2.50 | 100% | **5.0/5** | $1.87 |
| `gemini-3.7-flash` | 0.75 / 3.75 | 100% | 4.6/5 | $4.49 |
| `gemini-3.6-flash` | 0.75 / 3.75 | 100% | 5.0/5 | $6.09 |
| `gemini-3.5-flash` | 1.50 / 9.00 | 100% | 4.8/5 | **$14.69** |

### Bốn điều bảng này dạy

**1. Đắt nhất không phải tốt nhất.** `gemini-3.5-flash` tốn **$14,69**, gấp **68 lần** cái rẻ
nhất, mà chỉ được **4.8/5** — thua `gemini-2.5-flash` giá **$1,87** được **5.0/5**. Trả gấp 8
lần để nhận điểm thấp hơn.

**2. Tool-selection 100% ở mọi model.** Chọn đúng tool là việc **dễ** với model đời nay. Chỉ
số này **không phân biệt** được model nào tốt hơn — nên nếu chỉ đo nó, bạn sẽ kết luận "model
nào cũng như nhau" và chọn bừa. *Một chỉ số mà mọi thứ đều đạt tối đa là một chỉ số vô dụng
cho việc chọn lựa.*

**3. Giá đầu ra đắt hơn đầu vào 4-6 lần.** Nhìn cột giá: `0.10 / 0.40`, `1.50 / 9.00`. Hệ quả
thực dụng: **rút ngắn câu trả lời tiết kiệm nhiều hơn rút ngắn prompt.**

**4. Chi phí thật ≠ giá niêm yết.** `gemini-3.6-flash` và `gemini-3.7-flash` cùng giá
`0.75 / 3.75` nhưng tốn `$6.09` và `$4.49`. Vì sao? Model này **nói dài hơn** model kia. Chỉ
có đo mới biết.

### Cách chọn đúng

Đừng hỏi *"model nào tốt nhất?"*. Hỏi ***"model rẻ nhất còn đạt ngưỡng chất lượng của tôi là
cái nào?"*** Đặt ngưỡng trước, rồi đi từ dưới lên.

Dự án này dùng `gemini-3.1-flash-lite`: **4.5-4.6/5 với $1,19** — không phải điểm cao nhất,
nhưng là điểm đủ tốt với giá gần thấp nhất.

> **Nói trong phỏng vấn:** *"Em đo 7 model trên cùng bộ eval. Cái đắt nhất tốn gấp 68 lần cái
> rẻ nhất mà điểm còn thấp hơn một model rẻ hơn 8 lần. Em chọn theo ngưỡng chất lượng rồi lấy
> model rẻ nhất vượt ngưỡng, chứ không lấy cái mới nhất."*

---

## 8. Kỹ thuật giảm chi phí

Xếp theo mức tiết kiệm trên công bỏ ra:

| Kỹ thuật | Tiết kiệm | Ghi chú |
|---|---|---|
| **Chọn đúng model** | Tới **68 lần** | Xem mục 7 — đòn bẩy lớn nhất, và rẻ nhất để làm |
| **Cắt lịch sử** | Tuyến tính theo độ dài hội thoại | `trim_messages`, dự án này đang dùng |
| **Rút ngắn đầu ra** | Đầu ra đắt gấp 4-6 lần đầu vào | Đặt `max_tokens`; bảo model trả lời gọn |
| **Prompt caching** | 50-90% phần prompt lặp | Hiệu quả khi system prompt dài và cố định |
| **Ngân sách gọi tool** | Chặn trường hợp xấu nhất | `MAX_TOOL_CALLS=8` |
| **Cache câu trả lời** | 100% cho câu lặp lại | Chỉ hợp khi câu hỏi hay trùng |

**Nhưng trước hết phải đo được.** `metrics.py` cộng token của **mỗi vòng ReAct** rồi quy ra
USD, nên chi phí là một con số nhìn thấy trên Grafana chứ không phải điều bất ngờ cuối tháng.

> Tối ưu mà không đo là đoán. Chi phí hiện tại của dự án này là **$0,94/1000 câu**
> (`evals/results.md`) — và chính nhờ đo mà từng biết bản sửa prompt làm chất lượng lên
> 3.5 → 4.6 **đổi lấy** chi phí tăng 11% (lên $1,39 lúc đó); sau này lại giảm xuống $0,94 nhờ
> sửa một bug hiệu năng thật ở tool xếp hạng thị trấn.

---

## 9. Tự kiểm tra

**1.** Vì sao model bịa? Giải thích bằng cơ chế, không nói "AI chưa hoàn hảo".

<details><summary>Đáp án</summary>

Model được huấn luyện để sinh chuỗi **có xác suất xuất hiện cao**, không phải chuỗi **đúng**.
Với nó, một tên có thật và một tên bịa nghe hợp lý là cùng một loại việc — nó không có khái
niệm "sự thật" để mà vi phạm, và không có cơ chế báo "chỗ này tôi không chắc".
</details>

**2.** Hạ `temperature` về 0 có hết bịa không?

<details><summary>Đáp án</summary>

Không. Nó chỉ làm model luôn bốc token có xác suất cao nhất. Nếu điều bịa ra **là** thứ có xác
suất cao nhất thì nó vẫn bịa — chỉ là bịa y hệt nhau mỗi lần. Cách hiệu quả là đưa dữ liệu
thật vào (RAG, tool), không phải chỉnh nút bốc token.
</details>

**3.** Tool calling và structured output liên quan gì tới nhau?

<details><summary>Đáp án</summary>

Chúng là **một thứ**. `bind_tools` gửi JSON schema của các tool kèm request; model trả về JSON
`{name, args}` khớp schema đó. Model **không chạy hàm nào** — nó chỉ mô tả ý định, code mình
mới thực thi.
</details>

**4.** Cửa sổ ngữ cảnh to rồi thì bỏ RAG được chưa?

<details><summary>Đáp án</summary>

Chưa. Ba lý do: **tiền** (trả token cho mỗi câu hỏi), **lost in the middle** (model chú ý kém
ở phần giữa prompt dài, nhồi nhiều không đồng nghĩa dùng được nhiều), và **độ trễ**.
</details>

**5.** Đầu vào hay đầu ra đắt hơn, và điều đó gợi ý tối ưu chỗ nào?

<details><summary>Đáp án</summary>

**Đầu ra đắt hơn 4-6 lần** (`0.10 / 0.40`, `1.50 / 9.00`). Nên rút ngắn câu trả lời tiết kiệm
nhiều hơn rút ngắn prompt. Đặt `max_tokens` và yêu cầu model trả lời gọn.
</details>

**6.** Vì sao chỉ số tool-selection 100% ở cả 7 model lại là thông tin quan trọng?

<details><summary>Đáp án</summary>

Vì nó cho biết **chỉ số đó vô dụng cho việc chọn model** — mọi thứ đều đạt tối đa nên không
phân biệt được gì. Nếu chỉ đo nó, bạn sẽ kết luận "model nào cũng như nhau". Phải có chỉ số
thứ hai (chất lượng) mới chọn được.
</details>

---

## 10. Trả lời phỏng vấn

1. *LLM hoạt động thế nào?* → Cho một chuỗi token, nó tính xác suất token tiếp theo rồi bốc
   một cái, lặp lại. Mọi hành vi khác — trả lời, viết code, gọi tool — đều mọc ra từ cơ chế đó.

2. *Vì sao model bịa, và bạn giảm bằng cách nào?* → Vì nó tối ưu cho *có khả năng xuất hiện*
   chứ không phải *đúng*, và không có cơ chế biểu đạt sự không chắc chắn. Giảm bằng RAG và
   tool để đưa dữ liệu thật vào, cấm tường minh dùng trí nhớ riêng, bắt trích dẫn nguồn để soi
   được. Hạ temperature **không** chữa được.

3. *Ép model trả JSON thế nào cho chắc?* → Dùng structured output theo schema, không xin trong
   prompt. Tool calling chính là cơ chế đó — model trả JSON khớp schema. Nhưng schema chỉ đảm
   bảo **hình dạng**, không đảm bảo **ý nghĩa**, nên vẫn phải kiểm tra ở phía mình.

4. *Bạn chọn model thế nào?* → Đo 7 model trên cùng bộ eval. Cái đắt nhất tốn gấp **68 lần**
   cái rẻ nhất mà điểm còn **thấp hơn** một model rẻ hơn 8 lần. Em đặt ngưỡng chất lượng trước
   rồi lấy model **rẻ nhất vượt ngưỡng**, chứ không lấy cái mới nhất.

5. *Giảm chi phí LLM bằng cách nào?* → Theo thứ tự đòn bẩy: chọn đúng model (tới 68 lần), cắt
   lịch sử gửi đi, rút ngắn đầu ra (đầu ra đắt gấp 4-6 lần đầu vào), prompt caching, ngân sách
   gọi tool. Nhưng trước hết phải **đo được** — dự án em cộng token mỗi vòng ReAct rồi quy ra
   USD trên Grafana.

---

## 11. Liên quan

- [HOC_PROMPT_ENGINEERING.md](HOC_PROMPT_ENGINEERING.md) — viết prompt, mô tả tool, LLM-as-judge
- [HOC_VECTOR_DB.md](HOC_VECTOR_DB.md) — RAG, cách chống bịa hiệu quả nhất
- [HOC_AGENT_PATTERNS.md](HOC_AGENT_PATTERNS.md) — chọn kiến trúc agent
- [../MENTOR.md](../MENTOR.md) mục 10 — đo chất lượng bằng eval
- [HOC_TOAN_AI.md](HOC_TOAN_AI.md) — softmax, thứ biến điểm số thành xác suất ở mục 1
