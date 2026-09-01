# LangGraph & ReAct Agent — từ số 0 đến giải thích được code của chính mình

> Bài này gắn với **code thật trong repo của bạn**: [`main_02_02.py`](../../main_02_02.py)
> (bản dựng tay) và [`main_03_01.py`](../../main_03_01.py) (bản rút gọn).
> Mọi dòng code trích ở đây đều copy nguyên từ hai file đó.
>
> Đây là tài liệu **quan trọng nhất** trong thư mục này. Buổi phỏng vấn nào cũng mở đầu
> bằng *"kể tôi nghe về dự án của em"* — và dự án đó là cái agent này.

**Mục lục**

1. [Vấn đề: chatbot thường không làm được gì](#1-vấn-đề-chatbot-thường-không-làm-được-gì)
2. [ReAct: cho model quyền tự quyết](#2-react-cho-model-quyền-tự-quyết)
3. [Đồ thị là gì và vì sao cần nó](#3-đồ-thị-là-gì-và-vì-sao-cần-nó)
4. [State — trí nhớ của agent](#4-state--trí-nhớ-của-agent)
5. [Node — một việc trong đồ thị](#5-node--một-việc-trong-đồ-thị)
6. [Tool — tay chân của model](#6-tool--tay-chân-của-model)
7. [Edge và conditional edge — ai đi đâu](#7-edge-và-conditional-edge--ai-đi-đâu)
8. [Chạy thử một câu hỏi, từng bước](#8-chạy-thử-một-câu-hỏi-từng-bước)
9. [Guard: ngân sách tool-call](#9-guard-ngân-sách-tool-call)
10. [Cắt lịch sử: trim_messages](#10-cắt-lịch-sử-trim_messages)
11. [Checkpointer — nhớ qua nhiều lượt](#11-checkpointer--nhớ-qua-nhiều-lượt)
12. [Bản rút gọn: create_react_agent](#12-bản-rút-gọn-create_react_agent)
13. [Câu hỏi phỏng vấn và cách trả lời](#13-câu-hỏi-phỏng-vấn-và-cách-trả-lời)
14. [Tự kiểm tra](#14-tự-kiểm-tra)

---

## 1. Vấn đề: chatbot thường không làm được gì

Bạn hỏi ChatGPT *"Hôm nay Cornwall trời thế nào?"*. Nó không biết. Model được huấn luyện
xong từ nhiều tháng trước, trong đầu nó không có thời tiết hôm nay.

Có hai cách chữa:

**Cách 1 — nhét sẵn dữ liệu vào câu hỏi.** Bạn tự gọi API thời tiết, dán kết quả vào
prompt rồi mới hỏi model. Chạy được, nhưng bạn phải đoán trước người dùng cần gì. Họ hỏi
*"Cornwall có bãi biển đẹp không?"* thì dán thời tiết vào là thừa.

**Cách 2 — đưa model danh sách công cụ, để nó tự chọn.** Bạn nói với model: *"anh có 2
công cụ: tra thông tin du lịch, và xem thời tiết. Cần cái nào thì bảo tôi."* Model đọc
câu hỏi rồi tự quyết.

Cách 2 chính là **agent**. Và cái vòng lặp "model nghĩ → gọi công cụ → đọc kết quả → nghĩ
tiếp" có tên riêng: **ReAct**.

---

## 2. ReAct: cho model quyền tự quyết

ReAct = **Rea**soning + **Act**ing. Ý tưởng từ một bài báo năm 2022, nhưng đơn giản đến
mức bạn có thể hình dung trong 30 giây:

```
Người dùng hỏi
      ↓
  ┌─→ MODEL nghĩ ─────┐
  │       ↓            │
  │   Cần tool?        │
  │    ├── Có ─→ GỌI TOOL ─→ kết quả quay lại ─┘
  │    └── Không ─→ TRẢ LỜI người dùng
```

Điểm mấu chốt: **cái mũi tên quay ngược**. Sau khi tool trả kết quả, nó không đi thẳng ra
người dùng — nó quay lại cho model đọc. Model đọc xong có thể lại muốn gọi tool khác. Cứ
thế cho tới khi model thấy đủ dữ liệu để trả lời.

Ví dụ thật với agent của bạn, câu hỏi *"Cornwall có gì chơi và thời tiết thế nào?"*:

| Vòng | Model nghĩ gì | Hành động |
|---|---|---|
| 1 | "Cần thông tin du lịch" | gọi `search_travel_info("Cornwall attractions")` |
| 2 | "Có rồi, giờ cần thời tiết" | gọi `weather_forecast("Cornwall")` |
| 3 | "Đủ rồi" | trả lời người dùng |

Ba vòng, hai tool. Model tự quyết thứ tự — bạn không viết `if` nào cả.

> **Câu hay bị hỏi:** *"ReAct khác chain ở chỗ nào?"*
> Chain là đường thẳng cố định: A → B → C, viết sẵn lúc code. ReAct là vòng lặp có
> nhánh, và **model quyết đi nhánh nào lúc chạy**. Chain đoán trước được, agent thì không.

---

## 3. Đồ thị là gì và vì sao cần nó

LangGraph bắt bạn mô tả agent dưới dạng **đồ thị** (graph): các **node** (việc cần làm)
nối với nhau bằng **edge** (đường đi).

Vì sao không viết `while True:` cho xong? Ba lý do thực tế:

1. **Nhìn thấy được.** Đồ thị vẽ ra ảnh được — repo bạn có
   [`make_graph_image.py`](../../make_graph_image.py) làm đúng việc đó. Giải thích cho
   người khác bằng hình dễ hơn bằng code.
2. **Chèn được checkpoint.** Muốn lưu trạng thái sau mỗi bước, chỉ cần đưa checkpointer
   vào lúc compile. Với `while` thì bạn tự viết tay.
3. **Sửa luồng không phải đập code.** Thêm một node kiểm duyệt trước khi trả lời? Thêm
   node + đổi edge. Không đụng vào logic model.

Đồ thị agent của bạn chỉ có **2 node**:

```
      (bắt đầu)
          ↓
    ┌→ llm_node ──── hết tool_calls ──→ END
    │     │
    │  còn tool_calls
    │     ↓
    └── tools
```

Chỉ vậy thôi. Toàn bộ sức mạnh nằm ở **mũi tên quay lại** từ `tools` về `llm_node`.

---

## 4. State — trí nhớ của agent

State là cục dữ liệu đi xuyên qua mọi node. Mỗi node nhận state, trả về phần muốn cập
nhật. Code của bạn:

```python
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
```

Ba thứ cần hiểu trong hai dòng này:

**`TypedDict`** — chỉ là một `dict` Python có khai báo kiểu. `state["messages"]` là danh
sách message. Không có gì huyền bí.

**`Sequence[BaseMessage]`** — danh sách các message. LangChain có mấy loại:
- `HumanMessage` — người dùng nói
- `AIMessage` — model trả lời (có thể kèm `tool_calls`)
- `ToolMessage` — kết quả tool trả về
- `SystemMessage` — chỉ dẫn hệ thống

**`Annotated[..., operator.add]`** ← **đây là chỗ quan trọng nhất, và hay bị hỏi.**

Bình thường, node trả về `{"messages": [x]}` thì LangGraph sẽ **ghi đè**: state cũ mất,
chỉ còn `[x]`. Với `operator.add`, LangGraph **cộng dồn**: `state cũ + [x]`.

Nói cách khác `Annotated[..., operator.add]` là câu lệnh *"khi node trả về messages, hãy
nối vào đuôi chứ đừng thay thế"*. Không có nó, agent quên sạch sau mỗi bước — model sẽ
không bao giờ thấy được kết quả tool nó vừa gọi.

Thử hình dung state lớn dần qua ví dụ mục 2:

```
[Human("Cornwall có gì chơi và thời tiết thế nào?")]
[Human, AI(tool_calls=[search_travel_info])]
[Human, AI, Tool("Cornwall có bãi St Ives...")]
[Human, AI, Tool, AI(tool_calls=[weather_forecast])]
[Human, AI, Tool, AI, Tool("14°C, có mây")]
[Human, AI, Tool, AI, Tool, AI("Cornwall có... và hôm nay 14°C")]
```

Mỗi bước dài thêm. Đó là `operator.add` đang làm việc.

---

## 5. Node — một việc trong đồ thị

Node chỉ là **một hàm nhận state, trả về phần cập nhật**. Agent của bạn có 2 node.

### Node 1: `llm_node` — gọi model

```python
def llm_node(state: AgentState):
    window = trim_messages(state["messages"], ...)          # cắt bớt lịch sử
    current_messages = [SystemMessage(content=SYSTEM_PROMPT), *window]
    response_message = llm_with_tools.invoke(current_messages)
    metrics.record_llm_usage(CHAT_MODEL, ...)               # đếm token + tiền
    return {"messages": [response_message]}
```

Đọc từng dòng:
- Cắt lịch sử cho khỏi quá dài (mục 10 giải thích kỹ)
- Ghép `SystemMessage` lên **đầu danh sách tạm** — chú ý: không nhét vào state, nên
  state không bị bẩn bởi system message lặp đi lặp lại
- `llm_with_tools.invoke(...)` — gọi model
- Đếm token ngay tại đây, vì **mỗi vòng ReAct là một lần gọi model**. Một câu hỏi dùng 3
  tool sẽ tính tiền 4 lần chứ không phải 1. Đây là chi tiết rất đáng nói khi phỏng vấn.
- Trả về message mới → `operator.add` nối vào state

### Node 2: `tools` — chạy tool model yêu cầu

```python
class ToolsExecutionNode:
    def __init__(self, tools):
        self._tools_by_name = {t.name: t for t in tools}

    def __call__(self, state: dict):
        last_msg = state["messages"][-1]
        tool_calls = getattr(last_msg, "tool_calls", [])
        for tool_call in tool_calls:
            tool = self._tools_by_name[tool_call["name"]]
            metrics.TOOL_CALLS.labels(tool=tool_call["name"]).inc()
            with metrics.TOOL_DURATION.labels(tool=tool_call["name"]).time():
                result = tool.invoke(tool_call["args"])
            ...
```

Nó lấy message cuối (là `AIMessage` có `tool_calls`), lặp qua từng yêu cầu, tra tool theo
tên rồi gọi. Đo luôn số lần gọi và thời gian chạy để Prometheus vẽ dashboard.

> Đây là class chứ không phải hàm, vì nó cần **nhớ** bảng `_tools_by_name`. Class có
> `__call__` thì gọi được như hàm — `tools_execution_node(state)`. Kiến thức OOP này có
> trong [`HOC_DSA_OOP.md`](HOC_DSA_OOP.md).

**Một chi tiết bạn tự xử lý và nên khoe:** tool của bạn không ném exception mà trả `dict`
có khoá `"error"`, nên node phải đếm lỗi theo kiểu đó. Lý do: nếu ném exception thì cả đồ
thị chết; trả dict thì model **đọc được lỗi và tự xử lý** — ví dụ đổi tên thành phố rồi
gọi lại.

---

## 6. Tool — tay chân của model

Tool là hàm Python bình thường, gắn thêm decorator `@tool`:

```python
@tool(description="Search travel information about destinations in England. ...")
def search_travel_info(query: str) -> str:
    ...

@tool(description="Get the CURRENT weather of a town or city anywhere in the world, ...")
def weather_forecast(town: str, country: str = "") -> dict:
    ...
```

Rồi buộc vào model:

```python
llm_with_tools = llm_model.bind_tools(TOOLS)
```

**Model không nhìn thấy code tool của bạn.** Nó chỉ thấy: tên hàm, mô tả trong
`description`, và tên + kiểu của tham số. Từ đó nó tự đoán khi nào nên gọi.

Hệ quả rất thực tế: **`description` là prompt engineering, không phải comment.** Viết mô
tả mơ hồ thì model gọi sai tool. Chú ý chữ **CURRENT** viết hoa trong mô tả
`weather_forecast` — đó là cách ép model hiểu tool này cho thời tiết *hiện tại*, không
phải dự báo tuần sau.

`bind_tools` làm gì? Nó đóng gói danh sách tool thành JSON schema gửi kèm mỗi request.
Model trả về `AIMessage` mà trong đó `tool_calls` là danh sách `{name, args}`. Model
**không tự chạy gì cả** — nó chỉ nói "tôi muốn gọi hàm này với tham số này". Việc chạy là
của `ToolsExecutionNode`.

---

## 7. Edge và conditional edge — ai đi đâu

```python
builder = StateGraph(AgentState)
builder.add_node("llm_node", llm_node)
builder.add_node("tools", tools_execution_node)

builder.add_conditional_edges("llm_node", route_after_llm,
                              {"tools": "tools", END: END})
builder.add_edge("tools", "llm_node")
builder.set_entry_point("llm_node")
```

Bốn loại khai báo:

| Lệnh | Nghĩa |
|---|---|
| `add_node(tên, hàm)` | đăng ký một việc |
| `add_edge("tools", "llm_node")` | đi xong `tools` thì **luôn luôn** về `llm_node` |
| `add_conditional_edges(...)` | sau `llm_node`, gọi `route_after_llm` để **hỏi đi đâu** |
| `set_entry_point("llm_node")` | bắt đầu từ đâu |

`route_after_llm` trả về chuỗi `"tools"` hoặc `END`, và cái dict `{"tools": "tools", END: END}`
dịch chuỗi đó thành node đích.

**`add_edge("tools", "llm_node")` chính là mũi tên quay lại** — thứ biến đồ thị thành vòng
lặp, biến chain thành agent. Nếu đổi thành `add_edge("tools", END)` thì agent chỉ gọi được
đúng 1 tool rồi phải trả lời.

---

## 8. Chạy thử một câu hỏi, từng bước

Câu hỏi: *"Thời tiết Cornwall thế nào?"*

```
entry point ──→ llm_node
```
**Bước 1.** `llm_node` gửi `[System, Human("Thời tiết Cornwall thế nào?")]` cho model.
Model trả `AIMessage(content="", tool_calls=[{name:"weather_forecast", args:{town:"Cornwall"}}])`.
State giờ có 2 message.

```
llm_node ──→ route_after_llm
```
**Bước 2.** `route_after_llm` xem message cuối: còn `tool_calls` → trả `"tools"`.

```
route ──→ tools
```
**Bước 3.** `ToolsExecutionNode` tra `weather_forecast`, gọi API thật, nhận `{temp: 14, ...}`.
Đóng thành `ToolMessage` trả về. State có 3 message.

```
tools ──→ llm_node   (mũi tên quay lại)
```
**Bước 4.** `llm_node` chạy lần hai, lần này thấy đủ cả 3 message kể cả kết quả tool.
Model trả `AIMessage(content="Cornwall hôm nay 14°C, có mây")` — **không có `tool_calls`**.

```
llm_node ──→ route_after_llm ──→ END
```
**Bước 5.** Không còn `tool_calls` → `END`. Trả `content` cho người dùng.

**Model được gọi 2 lần** cho 1 câu hỏi. Đó là lý do đo tiền phải đo trong `llm_node`.

---

## 9. Guard: ngân sách tool-call

```python
MAX_TOOL_CALLS = int(os.environ.get("MAX_TOOL_CALLS", "8"))

def count_tool_calls(messages) -> int:
    return sum(len(getattr(m, "tool_calls", None) or []) for m in messages)

def route_after_llm(state) -> str:
    if count_tool_calls(state["messages"]) >= MAX_TOOL_CALLS:
        print(f"   [guard] chạm trần {MAX_TOOL_CALLS} tool call -> trả lời luôn")
        return END
    return tools_condition(state)
```

**Vì sao cần?** Vòng lặp ReAct không có gì đảm bảo nó dừng. Model có thể kẹt: gọi tool →
kết quả không như ý → gọi lại → mãi mãi. Mỗi vòng là một lần trả tiền. Không có chặn thì
một câu hỏi hỏng có thể đốt sạch quota.

Guard đếm tổng số tool đã yêu cầu trong lượt này; chạm 8 thì ép `END` — agent trả lời
bằng dữ liệu đã có, không hoàn hảo nhưng **hữu hạn**.

`tools_condition` là hàm sẵn của LangGraph, làm đúng một việc: còn `tool_calls` thì
`"tools"`, hết thì `END`. Bạn bọc nó lại để thêm ngân sách.

> **Câu phỏng vấn rất hay gặp:** *"Nếu agent lặp vô hạn thì sao?"*
> Trả lời: có ngân sách tool-call qua biến môi trường `MAX_TOOL_CALLS`, mặc định 8; chạm
> trần thì ép kết thúc và trả lời bằng dữ liệu đã thu được. Câu này ăn điểm vì nó cho thấy
> bạn nghĩ tới vận hành chứ không chỉ tới lúc chạy đúng.

---

## 10. Cắt lịch sử: trim_messages

```python
window = trim_messages(
    state["messages"],
    max_tokens=MAX_HISTORY_MESSAGES,
    token_counter=len,        # đếm theo SỐ MESSAGE, không theo token
    strategy="last",          # giữ phần cuối
    start_on="human",         # cắt theo LƯỢT, không cắt giữa chừng
    include_system=False,
    allow_partial=False,
)
```

**Vấn đề:** state cộng dồn mãi. Hội thoại dài → mỗi lần gọi model phải gửi lại toàn bộ →
tốn tiền, chậm, và cuối cùng vượt context window.

**Giải pháp:** chỉ gửi cửa sổ cuối.

Tham số quan trọng nhất là **`start_on="human"`**, và lý do rất tinh tế — comment trong
code của bạn ghi rõ:

> *Cắt bừa có thể bỏ lại một ToolMessage mồ côi không còn AIMessage tool_call đi trước →
> Gemini từ chối cả request.*

Nghĩa là: một `ToolMessage` **bắt buộc** phải có `AIMessage` chứa `tool_calls` đứng trước
nó. Nếu bạn cắt đúng vào giữa cặp đó, danh sách còn lại không hợp lệ và API trả lỗi.
`start_on="human"` bảo hàm cắt: chỉ được cắt tại điểm bắt đầu một lượt người dùng — nên
mọi cặp AI/Tool luôn nguyên vẹn.

**Đây là loại chi tiết đáng kể trong phỏng vấn**, vì nó là bug thật bạn gặp và tự chẩn ra,
không phải kiến thức chép từ tutorial.

---

## 11. Checkpointer — nhớ qua nhiều lượt

```python
def build_agent(checkpointer=None):
    return builder.compile(checkpointer=checkpointer)

travel_info_agent = build_agent()   # bản KHÔNG nhớ — dùng cho test và eval
```

State chỉ sống trong **một lần** `invoke()`. Hỏi câu tiếp theo là state rỗng lại — agent
quên sạch.

Checkpointer sửa việc đó: sau mỗi bước, LangGraph ghi state xuống nơi lưu trữ, gắn theo
`thread_id`. Lần sau đưa cùng `thread_id` thì nó đọc lại. Repo bạn cài trong
[`persistence.py`](../../persistence.py) với **PostgreSQL** — nên hội thoại sống sót cả
khi refresh trang hay restart container.

Chú ý `build_agent()` mặc định **không** checkpointer: test và eval không cần database,
chạy nhanh và không phụ thuộc hạ tầng. Đây là quyết định thiết kế tốt, nên nói ra.

---

## 12. Bản rút gọn: create_react_agent

Toàn bộ mục 4–9 — state, 2 node, edge, compile — gói lại thành **một lời gọi**:

```python
from langgraph.prebuilt import create_react_agent

travel_info_agent = create_react_agent(
    model=llm_model,
    tools=TOOLS,
    prompt=SYSTEM_PROMPT,
)
```

Chạy giống hệt. Vậy vì sao bạn viết cả hai?

| | Dựng tay (`main_02_02.py`) | Prebuilt (`main_03_01.py`) |
|---|---|---|
| Số dòng | ~480 | ~47 |
| Chèn ngân sách tool-call | được | không, trừ khi vá |
| Đo Prometheus trong node | được | khó |
| Kiểm soát trim_messages | được | không |
| Hiểu cơ chế | có | không |

**Câu trả lời đúng khi bị hỏi:** *"Tôi viết bản dựng tay trước để hiểu cơ chế và để chèn
được ngân sách tool-call cùng metrics vào đúng chỗ. Bản prebuilt tôi giữ lại để chứng minh
hai bản cho kết quả giống nhau — nhưng bản production là bản dựng tay, vì tôi cần kiểm
soát chi phí và quan sát."*

Đây là điểm mạnh thật của bạn: **làm hai lần cùng một thứ ở hai mức trừu tượng** cho thấy
bạn hiểu, chứ không phải chỉ gọi thư viện.

---

## 13. Câu hỏi phỏng vấn và cách trả lời

**"Kể tôi nghe về dự án của em."**
> Em xây một ReAct agent trả lời câu hỏi du lịch. Model tự quyết gọi tool nào và theo thứ
> tự nào — em có 2 tool: tìm kiếm RAG trên vector database và gọi API thời tiết thật. Đồ
> thị LangGraph có 2 node, node LLM và node chạy tool, nối vòng lại nhau. Em viết nó hai
> lần: một bản dựng tay để kiểm soát chi phí và metrics, một bản dùng `create_react_agent`
> để đối chiếu. Nó chạy sau FastAPI có SSE streaming, đóng Docker, deploy lên Azure
> Container Apps qua GitHub Actions, và mỗi lần release phải qua bộ eval trong CI.

**"State trong LangGraph là gì?"**
> Là dict đi qua mọi node. Của em chỉ có một khoá `messages`. Điểm quan trọng là
> `Annotated[..., operator.add]` — nó bảo LangGraph nối message mới vào đuôi thay vì ghi
> đè. Không có nó thì model không thấy được kết quả tool nó vừa gọi.

**"Làm sao model biết gọi tool nào?"**
> Nó không thấy code, chỉ thấy tên hàm, mô tả và chữ ký tham số qua `bind_tools`. Nên phần
> `description` thực chất là prompt engineering. Model trả về ý định gọi tool, còn việc
> chạy là của node tool bên em.

**"Agent lặp vô hạn thì sao?"**
> Em có ngân sách `MAX_TOOL_CALLS`, mặc định 8. Chạm trần thì route ép về END và agent trả
> lời bằng dữ liệu đã có. Vì mỗi vòng ReAct là một lần gọi model, không chặn là đốt tiền.

**"Hội thoại dài thì xử lý sao?"**
> `trim_messages` giữ cửa sổ cuối. Tham số quan trọng là `start_on="human"` — nếu cắt bừa
> có thể để lại ToolMessage mồ côi không còn AIMessage tool_call đứng trước, và Gemini từ
> chối cả request. Em gặp đúng lỗi đó nên mới đặt tham số này.

**"Sao không dùng luôn create_react_agent cho nhanh?"** → xem mục 12.

---

## 14. Tự kiểm tra

Trả lời không nhìn tài liệu. Nếu bí câu nào, quay lại đúng mục đó.

1. Vẽ đồ thị agent của bạn ra giấy, ghi rõ node nào nối node nào.
2. `operator.add` trong `AgentState` để làm gì? Bỏ đi thì hỏng thế nào?
3. Một câu hỏi cần 2 tool thì model được gọi mấy lần? Vì sao đó là vấn đề chi phí?
4. `bind_tools` gửi gì cho model? Model có tự chạy tool không?
5. `add_edge("tools", "llm_node")` đổi thành `add_edge("tools", END)` thì agent thay đổi ra sao?
6. Vì sao `route_after_llm` không dùng thẳng `tools_condition`?
7. `start_on="human"` chống lỗi gì? Mô tả lỗi đó bằng lời.
8. Vì sao `build_agent()` mặc định không có checkpointer?
9. Tool trả `dict` có khoá `"error"` thay vì ném exception — lợi ích là gì?
10. Bản dựng tay và bản prebuilt khác nhau ở đâu? Bạn dùng bản nào cho production, vì sao?

---

## 15. Tài liệu

- LangGraph docs: https://langchain-ai.github.io/langgraph/
- Bài báo ReAct (Yao et al., 2022): https://arxiv.org/abs/2210.03629
- Code của bạn: [`main_02_02.py`](../../main_02_02.py) · [`main_03_01.py`](../../main_03_01.py) ·
  [`persistence.py`](../../persistence.py) · [`metrics.py`](../../metrics.py)
- Bài liên quan: [`HOC_VECTOR_DB.md`](HOC_VECTOR_DB.md) (RAG bên trong tool),
  [`HOC_PROMPT_ENGINEERING.md`](HOC_PROMPT_ENGINEERING.md) (viết description tool),
  [`HOC_FASTAPI_SSE.md`](HOC_FASTAPI_SSE.md) (phục vụ agent qua HTTP)
