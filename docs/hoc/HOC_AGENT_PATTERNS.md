# Các kiểu kiến trúc agent — ReAct không phải lựa chọn duy nhất

> [`HOC_LANGGRAPH.md`](HOC_LANGGRAPH.md) dạy **ReAct** rất kỹ vì đó là thứ `travel-ai-agent`
> đang dùng. Bài này trả lời câu hỏi tiếp theo, và là câu hay bị hỏi trong phỏng vấn:
> ***"vì sao ReAct chứ không phải kiểu khác?"***
>
> Không trả lời được câu đó thì bạn chỉ chứng minh mình **làm theo được một tutorial**. Trả
> lời được thì bạn chứng minh mình **chọn**.

**Mục lục**

1. [Sáu kiểu, xếp theo mức tự do của model](#1-sáu-kiểu-xếp-theo-mức-tự-do-của-model)
2. [Chain — không có quyết định nào](#2-chain--không-có-quyết-định-nào)
3. [Router — một quyết định duy nhất](#3-router--một-quyết-định-duy-nhất)
4. [ReAct — quyết định ở mỗi vòng](#4-react--quyết-định-ở-mỗi-vòng)
5. [Plan-and-Execute — nghĩ trước, làm sau](#5-plan-and-execute--nghĩ-trước-làm-sau)
6. [Reflexion — tự chấm rồi làm lại](#6-reflexion--tự-chấm-rồi-làm-lại)
7. [Multi-agent — nhiều agent chia việc](#7-multi-agent--nhiều-agent-chia-việc)
8. [Chọn kiểu nào: bảng quyết định](#8-chọn-kiểu-nào-bảng-quyết-định)
9. [Ba thứ mọi kiểu đều cần](#9-ba-thứ-mọi-kiểu-đều-cần)
10. [Tự kiểm tra](#10-tự-kiểm-tra)
11. [Trả lời phỏng vấn](#11-trả-lời-phỏng-vấn)

---

## 1. Sáu kiểu, xếp theo mức tự do của model

Đừng học thuộc sáu cái tên. Hãy nhìn **một trục duy nhất**: *bạn giao cho model bao nhiêu
quyền quyết định?*

```
Ít tự do                                                        Nhiều tự do
◄──────────────────────────────────────────────────────────────────────────►
Chain      Router      ReAct       Plan-Execute   Reflexion    Multi-agent
(0 quyết   (1 quyết    (quyết      (lập kế        (tự chấm     (agent gọi
 định)      định)       định mỗi    hoạch rồi      rồi làm      agent khác)
                        vòng)       thi hành)      lại)
```

Và **một đánh đổi duy nhất** chạy suốt trục đó:

| Tự do hơn thì | Tự do ít hơn thì |
|---|---|
| Xử lý được câu hỏi bạn không lường trước | **Đoán trước được** hành vi |
| Ít code điều khiển hơn | Rẻ hơn, nhanh hơn |
| **Khó đoán, khó gỡ lỗi, đắt hơn** | Gặp câu lệch kịch bản là hỏng |

> **Nguyên tắc chọn — và là câu đáng nói nhất trong phỏng vấn:** *chọn mức tự do **thấp nhất**
> mà vẫn giải được bài toán.* Mỗi bậc tự do thêm vào là thêm một chỗ hệ thống có thể cư xử bất
> ngờ, và thêm tiền cho mỗi câu hỏi.

---

## 2. Chain — không có quyết định nào

Các bước cố định, chạy tuần tự. Model chỉ sinh chữ, **không chọn gì cả**.

```
Câu hỏi → luôn tìm kiếm → luôn tóm tắt → trả lời
```

Đây là **phần lớn ứng dụng LLM trong thực tế**, và nhiều người gọi nhầm nó là "agent".

**Khi nào chain là đúng:** khi các bước **thật sự luôn giống nhau**. Tóm tắt tài liệu, dịch,
phân loại email, trích xuất dữ liệu từ hoá đơn — không có gì để quyết định.

**Ưu điểm bị đánh giá thấp:** đoán trước được hoàn toàn, rẻ nhất, gỡ lỗi dễ nhất, và test
được như code thường.

> Sai lầm phổ biến của người mới: dùng agent cho bài toán chain. Bạn trả tiền cho khả năng
> quyết định mà bài toán **không có gì để quyết định**.

---

## 3. Router — một quyết định duy nhất

Model quyết định **một lần** ở đầu: câu hỏi này đi nhánh nào. Sau đó mỗi nhánh là một chain.

```
                 ┌→ hỏi thời tiết  → chain A
Câu hỏi → phân   ├→ hỏi du lịch    → chain B
           loại  └→ ngoài phạm vi  → từ chối lịch sự
```

**Khi nào dùng:** khi bạn biết trước có **vài loại yêu cầu rõ ràng**, và mỗi loại xử lý khác
nhau. Chatbot chăm sóc khách hàng là ví dụ kinh điển: đổi trả / kỹ thuật / thanh toán.

Router mạnh hơn chain nhiều mà vẫn **gần như đoán trước được** — bạn chỉ có N nhánh, kiểm thử
được từng nhánh. Rất nhiều bài toán tưởng cần agent thật ra chỉ cần router.

---

## 4. ReAct — quyết định ở mỗi vòng

Model quyết định **lặp đi lặp lại**: gọi công cụ nào, với tham số gì, và khi nào thì dừng.

```
[Suy nghĩ] → đủ thông tin chưa?
   ├── chưa → [Hành động] gọi tool → nhận kết quả → quay lại [Suy nghĩ]
   └── rồi  → trả lời
```

### Vì sao `travel-ai-agent` chọn ReAct

Câu hỏi *"gợi ý hai thị trấn biển ở Cornwall đang có thời tiết đẹp"* có một tính chất quyết
định: **agent không biết trước phải tra thời tiết của thị trấn nào.** Nó phải tìm trước, đọc
kết quả, rồi mới biết cần gọi `weather_forecast` bao nhiêu lần và cho những cái tên nào.

Chain không làm được — số bước phụ thuộc vào **dữ liệu lấy được giữa chừng**. Router cũng
không, vì đây không phải chuyện chọn nhánh mà là chuyện lặp.

Đây là **ranh giới thật** giữa workflow và agent, và là cách trả lời câu *"vì sao dự án của em
cần agent?"*: **số bước không biết trước được lúc viết code.**

### Điểm yếu của ReAct — đã đo được trong chính dự án này

Bộ eval cho thấy điều đáng nói: câu **một bước** được 4-5/5, câu **nhiều bước** ban đầu chỉ
được **2/5** (xem [MENTOR.md](../MENTOR.md) mục 10).

Nguyên nhân sâu xa nằm ở bản chất ReAct: nó quyết định **từng bước một, không có kế hoạch tổng
thể**. Nó không "biết" mình đang ở giữa một nhiệm vụ gồm 5 bước — mỗi vòng nó chỉ nhìn lịch sử
và hỏi *"giờ làm gì tiếp?"*. Càng nhiều bước, càng dễ lạc: quên yêu cầu ban đầu, bỏ sót một
nhánh, hoặc tóm tắt mất dữ liệu đã lấy được (đúng cái đã xảy ra).

Ba cách chữa, theo thứ tự nên thử:

| Cách | Chi phí | Dự án này |
|---|---|---|
| **Sửa system prompt** cho rõ yêu cầu đầu ra | Gần như 0 | ✅ Đã làm — 3.5 → **4.6/5** |
| Đổi sang **Plan-and-Execute** | Viết lại đồ thị | Chưa cần |
| Đổi sang **multi-agent** | Phức tạp gấp bội | Không cần |

**Bài học đáng giá nhất:** vấn đề trông giống lỗi kiến trúc nhưng hoá ra là lỗi **prompt**.
Đổi kiến trúc trước khi đo là cách đắt nhất để không sửa được gì.

---

## 5. Plan-and-Execute — nghĩ trước, làm sau

Tách làm hai giai đoạn, thường là hai lần gọi model khác nhau:

```
1. LẬP KẾ HOẠCH  → model viết ra toàn bộ các bước trước khi làm gì cả
     1. tìm thị trấn biển ở Cornwall
     2. với MỖI thị trấn tìm được, tra thời tiết
     3. so sánh và chọn hai cái tốt nhất

2. THI HÀNH      → chạy từng bước; có thể sửa kế hoạch nếu bước nào hỏng
```

| So với ReAct | |
|---|---|
| **Hơn** | Không quên yêu cầu ban đầu vì kế hoạch được viết ra rõ ràng; nhiệm vụ dài ổn định hơn; **đọc được kế hoạch để gỡ lỗi** |
| **Kém** | Thêm một lần gọi model; kế hoạch lập lúc chưa có dữ liệu nên có thể sai; cứng nhắc hơn khi tình huống đổi giữa chừng |

**Khi nào đáng đổi:** nhiệm vụ dài (5+ bước), hoặc mỗi bước tốn kém nên đi sai đường là đắt,
hoặc bạn cần **cho người dùng duyệt kế hoạch trước khi thi hành** — điểm này quan trọng với
các agent làm việc có hậu quả thật (gửi mail, đổi dữ liệu, tiêu tiền).

---

## 6. Reflexion — tự chấm rồi làm lại

Thêm một vòng **tự phê bình** vào sau khi đã có câu trả lời:

```
làm → tự chấm câu trả lời của mình → chưa đạt? → làm lại với phần nhận xét đó
                                   → đạt rồi? → trả về
```

**Được:** chất lượng lên rõ ở việc sinh code (tự chạy test rồi sửa), viết dài, suy luận nhiều
bước.

**Mất:** **nhân đôi hoặc nhân ba chi phí và độ trễ**. Và model tự chấm mình có **thiên vị** —
nó hay cho rằng mình đã làm tốt.

> **Liên hệ ngay trong dự án:** cơ chế LLM-as-judge ở `evals/eval_agent.py` chính là ý tưởng
> này, nhưng đặt ở **ngoài** (lúc đánh giá) thay vì **trong** (lúc chạy thật). Đó là một lựa
> chọn có chủ ý: người dùng không phải trả tiền cho vòng tự chấm, mà mình vẫn đo được chất
> lượng. Nói được sự khác nhau giữa *judge lúc eval* và *reflexion lúc chạy* là một điểm cộng.

---

## 7. Multi-agent — nhiều agent chia việc

Nhiều agent, mỗi cái có prompt riêng, bộ công cụ riêng, và chúng gọi nhau.

Hai kiểu tổ chức phổ biến:

```
SUPERVISOR (phổ biến nhất)        HAND-OFF (chuyền tay)
     ┌─ nghiên cứu                agent A ──chuyển──▶ agent B
điều ├─ viết                        (hết phần mình thì giao hẳn)
phối └─ kiểm tra
```

### Khi nào multi-agent thật sự đáng

| Đáng | Không đáng |
|---|---|
| Các vai trò cần **prompt xung khắc nhau** (viết vs phê bình) | Chỉ vì nghe hiện đại |
| Mỗi vai có **bộ công cụ rất khác** (20 tool chia thành 4 nhóm 5) | Có 3 tool cùng miền như dự án này |
| Cần **cách ly**: agent này không được thấy dữ liệu của agent kia | Không có yêu cầu cách ly |
| Các nhánh **chạy song song được** | Các bước phụ thuộc nhau tuần tự |

### Cái giá thật, phải nói ra

1. **Chi phí nhân lên.** Mỗi agent là một chuỗi gọi model riêng. Bốn agent dễ thành gấp bốn
   tiền và gấp bốn độ trễ.
2. **Lỗi tích luỹ.** Mỗi lần chuyển giao là một lần thông tin có thể rơi rụng hoặc bị hiểu
   sai. Bốn bước mỗi bước đúng 90% thì cả chuỗi chỉ còn **66%**.
3. **Gần như không gỡ lỗi được.** Kết quả sai — sai ở agent nào? Ở chỗ chuyển giao? Ở prompt
   của supervisor?
4. **Dễ lặp vô hạn.** A hỏi B, B hỏi lại A. Phải có ngân sách chặn.

### Vì sao vòng lặp chính của dự án này KHÔNG dùng multi-agent

Ba công cụ, một lĩnh vực, các bước phụ thuộc tuần tự (phải tìm thị trấn xong mới tra được
thời tiết). Chia thành nhiều agent chỉ **thêm tiền và thêm chỗ hỏng**, không giải quyết được
gì mà một agent chưa giải được.

> **Cách nói trong phỏng vấn:** *"Em có cân nhắc multi-agent cho vòng lặp chính nhưng không
> dùng — ba tool cùng một lĩnh vực và các bước phụ thuộc tuần tự, nên chia agent chỉ nhân chi
> phí và nhân chỗ hỏng. Multi-agent đáng khi các vai cần prompt xung khắc nhau hoặc bộ tool rất
> khác nhau."*
>
> Câu này **giá trị hơn** việc dựng một hệ multi-agent không cần thiết rồi không giải thích
> được vì sao.

### Nhưng multi-agent thật đã được xây — cho MỘT quyết định hẹp, không phải cả vòng lặp

Lập luận trên vẫn đúng cho **vòng hỏi-đáp chính**. Điều đổi là: dự án có thêm một biến thể
`main_05_multi_agent.py` giải quyết một nhu cầu hẹp hơn nhiều so với "chia agent theo vai".

**Vấn đề cụ thể:** trước khi vào vòng ReAct, có một quyết định đáng tách ra khỏi vòng lặp:
câu hỏi này có cần **xếp hạng nhiều thị trấn theo thời tiết** không, và nếu có thì bao nhiêu
thị trấn (`top_n`) và khoảng nhiệt độ nào user muốn. Để LLM tự suy luận điều này **giữa** vòng
ReAct thì quyết định trộn lẫn với việc gọi tool, khó đọc lại để gỡ lỗi.

**Cách giải:** một node `planner` gọi model **riêng**, ép output qua Pydantic
(`TownRankingPlan`: `needs_town_ranking`, `top_n`, `min_temp_c`, `max_temp_c`, `rationale`) —
không đoán từ văn bản tự do. Quyết định đó được ghép với **executor**, chính là graph ReAct có
sẵn của `main_02_02.py` (`build_agent()`), **tái sử dụng nguyên vẹn không sửa gì**, đưa vào làm
một node của graph cha qua `add_node` — subgraph thật của LangGraph, không phải hai hàm Python
gọi tuần tự giả làm "multi-agent".

**Đây KHÔNG mâu thuẫn với lập luận ở trên**, vì nó không chia agent theo "vai" (viết vs phê
bình, hay bộ tool khác hẳn nhau). Nó tách **một quyết định lập kế hoạch** ra khỏi vòng ReAct,
rồi ghép lại bằng đúng cơ chế multi-agent (subgraph) — một use case hẹp, không phải tổ chức
lại toàn bộ agent.

**Bug thật tìm được qua việc này, không phải qua đọc tài liệu:** LangGraph lọc state của
node-là-subgraph theo đúng schema **graph con** khai báo. Quyết định `plan` của planner "biến
mất" khi tới executor vì `AgentState` gốc (của `main_02_02.py`) không khai báo field đó — sửa
bằng cách thêm `plan: NotRequired[dict]` vào `AgentState`. Đây là điểm đáng nói nhất trong
phỏng vấn về subgraph: **subgraph không tự động thấy mọi khoá của state cha, chỉ thấy khoá nó
khai báo.**

> **Cách nói trong phỏng vấn:** *"Vòng ReAct chính vẫn một agent vì ba tool cùng miền, bước
> phụ thuộc tuần tự. Nhưng em có xây thêm một biến thể planner+executor cho một quyết định hẹp
> — có cần xếp hạng nhiều town không, xếp mấy town — dùng đúng cơ chế subgraph của LangGraph,
> tái sử dụng nguyên graph ReAct làm executor. Qua đó tìm ra một bug thật: subgraph chỉ thấy
> field nó khai báo trong schema, không tự thừa hưởng từ state cha."*

File: `main_05_multi_agent.py` (MỚI). Chi tiết: [MENTOR.md](../MENTOR.md).

---

## 8. Chọn kiểu nào: bảng quyết định

Đi từ trên xuống, dừng ở dòng đầu tiên trả lời "có":

| Câu hỏi | Nếu đúng thì dùng |
|---|---|
| Các bước **luôn giống nhau**? | **Chain** |
| Có **vài loại yêu cầu rõ ràng**, mỗi loại xử lý khác? | **Router** |
| **Số bước phụ thuộc dữ liệu lấy được giữa chừng**? | **ReAct** ← dự án này |
| Nhiệm vụ **dài**, hoặc cần người **duyệt kế hoạch trước**? | **Plan-and-Execute** |
| Chất lượng quan trọng hơn chi phí, và **tự kiểm được**? | **+ Reflexion** |
| Các vai cần **prompt xung khắc** hoặc **bộ tool rất khác**? | **Multi-agent** |

Mặc định nên là **chain**. Mỗi lần đi xuống một dòng, bạn phải nêu được **cái gì buộc bạn
phải đi xuống**.

---

## 9. Ba thứ mọi kiểu đều cần

Đổi kiến trúc kiểu gì thì ba thứ này vẫn phải có. Chúng là **kỹ thuật vận hành agent**, và là
thứ phân biệt bản demo với bản chạy thật.

### 9.1 Ngân sách bước — chặn vòng lặp vô hạn

```python
# main_02_02.py
MAX_TOOL_CALLS = int(os.environ.get("MAX_TOOL_CALLS", "8"))

if count_tool_calls(state["messages"]) >= MAX_TOOL_CALLS:
    print(f"   [guard] cham tran {MAX_TOOL_CALLS} tool call -> tra loi luon")
```

Model quyết định khi nào dừng, nên nó **có thể không dừng**. Không có ngân sách thì một câu
hỏi lỗi có thể gọi tool mãi mãi — đốt tiền và treo request.

Chi tiết đáng nói: chạm trần thì **vẫn trả lời bằng những gì đã có**, không ném lỗi. Người
dùng nhận câu trả lời chưa hoàn hảo còn hơn nhận màn hình lỗi.

### 9.2 Cắt cửa sổ ngữ cảnh

Càng nhiều vòng, lịch sử càng dài, mỗi lần gọi model càng đắt — **chi phí tăng theo bình
phương số bước**. `trim_messages` giới hạn phần gửi đi (xem [MENTOR.md](../MENTOR.md) mục 21).

### 9.3 Quan sát được

Agent là **hộp đen tự quyết định**. Không ghi lại đường đi thì không bao giờ trả lời được câu
*"vì sao nó lại làm thế?"*. Dự án này ghi mỗi lần gọi tool, mỗi vòng, token và tiền từng vòng
— và chính nhờ đọc lịch sử tin nhắn thật mà đo được tool-selection accuracy.

> Ba thứ này **quan trọng hơn việc chọn đúng kiểu kiến trúc**. Một ReAct có ngân sách, có cắt
> ngữ cảnh, có đo lường thì chạy được thật. Một hệ multi-agent không có ba thứ đó thì chỉ chạy
> được trên máy người viết.

---

## 10. Tự kiểm tra

**1.** Ranh giới thật giữa workflow và agent là gì?

<details><summary>Đáp án</summary>

**Số bước có biết trước lúc viết code hay không.** Workflow: các bước cố định. Agent: số bước
và thứ tự phụ thuộc dữ liệu lấy được giữa chừng. Dự án này cần agent vì không biết trước phải
tra thời tiết của thị trấn nào — phải tìm xong mới biết.
</details>

**2.** Vì sao "chọn mức tự do thấp nhất mà vẫn giải được bài toán"?

<details><summary>Đáp án</summary>

Mỗi bậc tự do thêm vào là thêm một chỗ hệ thống cư xử bất ngờ, thêm khó gỡ lỗi, và thêm tiền
cho mỗi câu hỏi. Tự do chỉ đáng khi bài toán **thật sự** có thứ cần quyết định. Dùng agent cho
bài toán chain là trả tiền cho khả năng không dùng đến.
</details>

**3.** Câu nhiều bước bị điểm thấp — vì sao đổi kiến trúc không phải bước đầu tiên?

<details><summary>Đáp án</summary>

Vì trong dự án này nguyên nhân hoá ra là **prompt**, không phải kiến trúc: agent gom nhiều kết
quả rồi tóm tắt định tính, vứt mất số liệu mà rubric đòi. Sửa bốn dòng system prompt đưa điểm
từ 3.5 lên 4.6. Đổi sang Plan-and-Execute sẽ tốn công gấp nhiều lần mà chưa chắc trúng nguyên
nhân. **Đo trước, đổi sau.**
</details>

**4.** Reflexion khác LLM-as-judge trong bộ eval chỗ nào?

<details><summary>Đáp án</summary>

Cùng ý tưởng "nhờ LLM chấm", khác **chỗ đặt**. Reflexion nằm **trong** đường chạy thật —
người dùng chờ lâu hơn và trả tiền cho vòng tự chấm. Judge của eval nằm **ngoài**, chỉ chạy
lúc đánh giá. Dự án này chọn cách sau: đo được chất lượng mà không bắt người dùng trả giá.
</details>

**5.** Bốn agent nối tiếp, mỗi cái đúng 90% thì cả chuỗi đúng bao nhiêu?

<details><summary>Đáp án</summary>

0,9⁴ ≈ **66%**. Đây là lý do multi-agent không miễn phí: mỗi lần chuyển giao là một chỗ thông
tin rơi rụng, và sai số **nhân lên** chứ không cộng vào.
</details>

**6.** Vì sao chạm trần `MAX_TOOL_CALLS` thì vẫn trả lời chứ không ném lỗi?

<details><summary>Đáp án</summary>

Vì lúc đó agent đã có một phần thông tin. Trả lời chưa hoàn hảo vẫn hữu ích hơn màn hình lỗi.
Ngân sách để chặn đốt tiền và treo request, không phải để trừng phạt người dùng.
</details>

---

## 11. Trả lời phỏng vấn

1. *Có những kiểu kiến trúc agent nào?* → Xếp theo **mức tự do của model**: chain (0 quyết
   định) → router (1) → ReAct (mỗi vòng) → plan-and-execute → reflexion → multi-agent. Nguyên
   tắc chọn: **mức tự do thấp nhất mà vẫn giải được bài toán**.

2. *Vì sao dự án của em dùng ReAct?* → Vì **số bước không biết trước được**: phải tìm thị trấn
   xong mới biết cần tra thời tiết cho những cái tên nào và bao nhiêu lần. Chain không làm
   được, router cũng không vì đây là chuyện lặp chứ không phải chọn nhánh.

3. *Sao không dùng multi-agent?* → Cho **vòng hỏi-đáp chính**: ba tool cùng một lĩnh vực, các
   bước phụ thuộc tuần tự. Chia agent chỉ nhân chi phí và nhân chỗ hỏng. Nhưng em có xây thêm
   một biến thể planner+executor (`main_05_multi_agent.py`) cho một quyết định hẹp — có cần
   xếp hạng nhiều town theo thời tiết không — dùng subgraph thật của LangGraph, tái sử dụng
   nguyên graph ReAct làm executor. Multi-agent đáng khi các vai cần **prompt xung khắc** hoặc
   **bộ tool rất khác nhau**, hoặc khi tách một quyết định lập kế hoạch ra khỏi vòng lặp chính
   giúp dễ đọc/gỡ lỗi hơn.

4. *Điểm yếu của ReAct?* → Nó quyết định từng bước, **không có kế hoạch tổng thể**, nên nhiệm
   vụ dài dễ lạc. Em đo được đúng điều đó: câu một bước 4-5/5, câu nhiều bước 2/5. Nhưng
   nguyên nhân hoá ra là prompt chứ không phải kiến trúc — sửa prompt đưa điểm lên 4.6.

5. *Khi nào em sẽ đổi sang Plan-and-Execute?* → Khi nhiệm vụ dài trên 5 bước, hoặc mỗi bước
   tốn kém nên đi sai đường là đắt, hoặc cần **người duyệt kế hoạch trước khi thi hành** —
   với agent có hậu quả thật như gửi mail hay tiêu tiền.

6. *Agent chạy production cần gì ngoài kiến trúc?* → Ba thứ, và chúng quan trọng hơn việc chọn
   đúng kiểu: **ngân sách bước** (model tự quyết khi nào dừng nên nó có thể không dừng), **cắt
   cửa sổ ngữ cảnh** (chi phí tăng theo bình phương số bước), và **quan sát được** (agent là
   hộp đen, không ghi lại thì không trả lời được "vì sao nó làm thế").

---

## 12. Liên quan

- [HOC_LANGGRAPH.md](HOC_LANGGRAPH.md) — ReAct và cách dựng đồ thị, chi tiết code
- [../MENTOR.md](../MENTOR.md) mục 10 — câu chuyện đo ra điểm yếu của ReAct rồi sửa
- [HOC_PROMPT_ENGINEERING.md](HOC_PROMPT_ENGINEERING.md) — mô tả tool, LLM-as-judge
- [HOC_BAO_MAT_AI_APP.md](HOC_BAO_MAT_AI_APP.md) — ngân sách và công tắc ngắt ở góc bảo mật
- `main_05_multi_agent.py` — code planner + executor qua subgraph, xem mục 7 ở trên
