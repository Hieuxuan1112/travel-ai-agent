# Hiểu toàn bộ sản phẩm này — tài liệu mentor

> Đọc file này là hiểu được **toàn bộ** hệ thống: nó là gì, chạy ra sao, vì sao thiết kế
> như vậy, và trả lời được mọi câu hỏi phỏng vấn về nó. Mọi con số trong đây đều là số
> **đo thật** từ máy bạn, không phải ví dụ.

**Mục lục**

1. [Sản phẩm này là gì](#1-sản-phẩm-này-là-gì)
2. [Agent khác chatbot ở chỗ nào](#2-agent-khác-chatbot-ở-chỗ-nào)
3. [Kiến trúc toàn cảnh](#3-kiến-trúc-toàn-cảnh)
4. [Đi theo một câu hỏi từ đầu đến cuối](#4-đi-theo-một-câu-hỏi-từ-đầu-đến-cuối)
5. [Hai công cụ của agent](#5-hai-công-cụ-của-agent)
6. [Tầng agent: LangGraph](#6-tầng-agent-langgraph)
7. [RAG và vector store](#7-rag-và-vector-store)
8. [MCP](#8-mcp)
9. [Tầng phục vụ: API, Docker, giám sát](#9-tầng-phục-vụ-api-docker-giám-sát)
10. [Đánh giá chất lượng (eval)](#10-đánh-giá-chất-lượng-eval)
11. [Test và CI](#11-test-và-ci)
12. [Bảng số liệu tổng hợp](#12-bảng-số-liệu-tổng-hợp)
13. [Những quyết định thiết kế và đánh đổi](#13-những-quyết-định-thiết-kế-và-đánh-đổi)
14. [Những lỗi thật đã gặp](#14-những-lỗi-thật-đã-gặp)
15. [Giới hạn hiện tại](#15-giới-hạn-hiện-tại)
16. [23 câu phỏng vấn và cách trả lời](#16-23-câu-phỏng-vấn-và-cách-trả-lời)
17. [Demo 5 phút](#17-demo-5-phút)
18. [Từ điển thuật ngữ](#18-từ-điển-thuật-ngữ)
19. [Giới hạn tần suất — chuẩn bị cho việc mở công khai](#19-giới-hạn-tần-suất--chuẩn-bị-cho-việc-mở-công-khai)
20. [Đưa dữ liệu vào image và chuyện deploy](#20-đưa-dữ-liệu-vào-image-và-chuyện-deploy)

---

## 1. Sản phẩm này là gì

**Một câu:** một trợ lý du lịch biết tự quyết định phải tra cứu gì để trả lời bạn.

Hỏi *"gợi ý hai thị trấn biển ở Cornwall đang có thời tiết đẹp"*, hệ thống sẽ tự làm ba
việc mà **không ai lập trình sẵn thứ tự**: tìm trong kho kiến thức du lịch xem Cornwall
có thị trấn biển nào, rồi tra thời tiết thật của từng thị trấn, rồi tổng hợp thành câu
trả lời.

Điểm mấu chốt: **không có dòng code nào ra lệnh "tìm thị trấn trước, tra thời tiết sau"**.
Mô hình ngôn ngữ tự quyết định gọi công cụ nào, gọi mấy lần, theo thứ tự nào — dựa trên
câu hỏi và kết quả nó nhận được ở mỗi bước.

Sản phẩm gốc là bài lab Chương 11 sách *AI Agents and Applications With LangChain,
LangGraph, and MCP*. Phần mở rộng ngoài sách: thời tiết thật thay cho dữ liệu giả, MCP
server, HTTP API có streaming, Docker/Compose, hệ đo lường Prometheus/Grafana, bộ eval,
test và CI.

---

## 2. Agent khác chatbot ở chỗ nào

Ba mức độ, hiểu rõ ba mức này là hiểu được vì sao "agent" là một khái niệm riêng:

| Mức | Cách hoạt động | Ví dụ | Hạn chế |
|---|---|---|---|
| **Chatbot thuần** | LLM trả lời bằng kiến thức đã học | ChatGPT không có công cụ | Không biết thông tin mới; bịa (hallucination) |
| **Workflow** | Người lập trình định sẵn các bước | "luôn tìm kiếm → luôn tóm tắt" | Cứng nhắc; câu hỏi lệch kịch bản là hỏng |
| **Agent** ✅ | LLM tự chọn công cụ, tự quyết thứ tự, lặp đến khi đủ thông tin | Sản phẩm này | Khó đoán trước → phải đo và kiểm soát |

Sản phẩm này ở mức 3, theo mẫu thiết kế **ReAct** (Reasoning + Acting) — công bố năm 2022,
giờ là mẫu chuẩn của mọi agent hiện đại. Vòng lặp của nó:

```
Người hỏi
   ↓
[Suy nghĩ]  LLM đọc câu hỏi: mình đã đủ thông tin để trả lời chưa?
   ↓
   ├── CHƯA ĐỦ → [Hành động] gọi công cụ → nhận kết quả → quay lại [Suy nghĩ]
   │
   └── ĐỦ RỒI → trả lời người dùng, kết thúc
```

Bằng chứng thật từ một lần chạy — agent lặp **4 vòng** cho một câu hỏi:

```
event: tool_call    search_travel_info(query="popular beach towns in Cornwall, England")
event: tool_result  "Towns and cities... Truro, St Ives, Falmouth, Newquay..."
event: tool_call    weather_forecast(town="St Ives", country="United Kingdom")
event: tool_result  {"weather": "clear sky", "temperature": 19.4}
event: tool_call    weather_forecast(town="Falmouth", country="United Kingdom")
event: tool_result  {"weather": "clear sky", "temperature": 21.7}
event: answer       "Two excellent beach towns ... St Ives ... Falmouth ..."
event: done         {"tool_calls": 3, "elapsed_seconds": 8.25}
```

Chú ý: agent **không biết trước** St Ives và Falmouth tồn tại. Nó phải tìm trước, rồi mới
biết tra thời tiết của cái gì. Đó là điều workflow cứng không làm được.

---

## 3. Kiến trúc toàn cảnh

```
┌─────────────── Người dùng vào bằng 4 cửa ────────────────┐
│  CLI            Streamlit UI      HTTP API      MCP client │
│  main_02_02.py  app.py            api.py        main_04_mcp.py │
└──────────────────────────┬─────────────────────────────────┘
                           ▼
        ┌──────────── TẦNG AGENT (LangGraph) ────────────┐
        │                                                 │
        │   ┌─────────────┐   còn tool_calls  ┌────────┐ │
        │   │  llm_node   │ ────────────────▶ │ tools  │ │
        │   │  Gemini     │ ◀──────────────── │  node  │ │
        │   └─────────────┘   kết quả tool    └────────┘ │
        │          │                                      │
        │          └── hết tool_calls ──▶ trả lời, END    │
        └───────────────────┬─────────────────────────────┘
                            ▼
        ┌──────────── HAI CÔNG CỤ ────────────┐
        │  search_travel_info    weather_forecast │
        └────────┬───────────────────┬────────────┘
                 ▼                   ▼
          Chroma (92 chunk)    Open-Meteo API
          Wikivoyage           (thời tiết thật)

        ┌─────── GIÁM SÁT ───────┐
        │ /metrics → Prometheus → Grafana │
        └─────────────────────────┘
```

**Nguyên tắc kiến trúc quan trọng nhất của sản phẩm này:** đồ thị agent **không đổi** khi
công cụ đổi. Tôi đã thay công cụ thời tiết giả bằng API thật, rồi đưa công cụ ra sau MCP
server — **không sửa một dòng nào** trong phần lắp ráp đồ thị. Đây là điều đáng nói nhất
khi phỏng vấn về kiến trúc.

### Danh sách file và vai trò

| File | Vai trò |
|---|---|
| `main_02_02.py` | **Trái tim.** 2 tool + đồ thị LangGraph dựng tay + vòng chat CLI |
| `main_03_01.py` | Cùng agent nhưng dùng `create_react_agent` dựng sẵn — để so sánh |
| `mcp_server.py` | Đóng 2 tool thành MCP server (giao thức chuẩn) |
| `main_04_mcp.py` | Agent lấy tool qua MCP thay vì import trực tiếp |
| `api.py` | HTTP API: `/chat`, `/chat/stream` (SSE), `/metrics`, `/healthz`, `/docs` |
| `app.py` | Giao diện web Streamlit |
| `metrics.py` | Định nghĩa các chỉ số Prometheus |
| `evals/eval_agent.py` | Chấm điểm agent trên bộ 8 câu hỏi |
| `tests/` | 29 test chạy offline |
| `monitoring/` | Cấu hình Prometheus + dashboard Grafana |
| `Dockerfile`, `docker-compose.yml` | Đóng gói và chạy cả hệ thống |

---

## 4. Đi theo một câu hỏi từ đầu đến cuối

Đây là phần quan trọng nhất tài liệu. Hiểu được mục này là hiểu cả hệ thống.

Câu hỏi: **"Suggest two Cornwall beach towns with nice weather"**

### Bước 0 — Khởi động (một lần duy nhất)

Khi server bật, `lifespan` trong `api.py` nạp vector store:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    lab.get_travel_info_vectorstore()   # nạp 92 chunk từ đĩa
    yield
```

Vì sao nạp sẵn: nếu để đến request đầu tiên mới nạp, người dùng đầu tiên phải chờ. Việc
nặng làm lúc khởi động, không làm trong request.

### Bước 1 — Câu hỏi thành `state`

`state` của agent chỉ là **một danh sách tin nhắn**:

```python
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
```

`operator.add` là chi tiết tinh tế: nó bảo LangGraph "khi một node trả về messages, hãy
**cộng dồn** vào danh sách cũ, đừng ghi đè". Nhờ vậy agent nhớ được toàn bộ diễn biến của
lượt hỏi. Không có nó, mỗi node sẽ xoá sạch lịch sử và agent không bao giờ hoàn thành
được vòng lặp.

Ban đầu: `messages = [HumanMessage("Suggest two Cornwall beach towns with nice weather")]`

### Bước 2 — `llm_node` suy nghĩ (vòng 1)

```python
def llm_node(state: AgentState):
    current_messages = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
    response_message = llm_with_tools.invoke(current_messages)
    metrics.record_llm_usage(CHAT_MODEL, getattr(response_message, "usage_metadata", None))
    return {"messages": [response_message]}
```

Ba việc xảy ra:

1. **Ghép system prompt lên đầu** — chỉ dẫn cho LLM: *"Only use the tools to find the
   information you need (including town names). Never invent town names from your own
   knowledge."* Câu này cực kỳ quan trọng, xem mục 13.
2. **`llm_with_tools.invoke(...)`** — gửi tin nhắn kèm **mô tả 2 công cụ** lên Gemini.
3. **Đếm token và tiền** ngay tại đây.

Gemini trả về một `AIMessage` **không có nội dung** nhưng có `tool_calls`:

```python
AIMessage(content='', tool_calls=[
    {'name': 'search_travel_info',
     'args': {'query': 'popular beach towns in Cornwall, England'},
     'id': 'call_...'}
])
```

Chú ý: **LLM tự viết lại câu hỏi**. Người dùng hỏi "two Cornwall beach towns with nice
weather", nhưng LLM biết công cụ tìm kiếm cần một truy vấn tìm kiếm tốt nên nó viết
"popular beach towns in Cornwall, England". Đây gọi là *query rewriting*, và nó xảy ra
miễn phí — không phải lập trình.

### Bước 3 — Cạnh điều kiện quyết định đi đâu

```python
builder.add_conditional_edges("llm_node", tools_condition)
```

`tools_condition` là hàm dựng sẵn của LangGraph, logic đúng một câu: **tin nhắn cuối có
`tool_calls` không?** Có → đi node `tools`. Không → `END`, trả lời người dùng.

Toàn bộ "trí thông minh" của luồng điều khiển nằm ở một câu điều kiện đơn giản này. Phần
thông minh thật nằm ở LLM, không nằm ở đồ thị.

### Bước 4 — `tools` node thực thi

```python
for tool_call in tool_calls:
    tool_name = tool_call["name"]
    tool_args = tool_call["args"]
    tool = self._tools_by_name[tool_name]

    metrics.TOOL_CALLS.labels(tool=tool_name).inc()
    with metrics.TOOL_DURATION.labels(tool=tool_name).time():
        result = tool.invoke(tool_args)
    if isinstance(result, dict) and "error" in result:
        metrics.TOOL_ERRORS.labels(tool=tool_name).inc()

    tool_messages.append(ToolMessage(content=str(result), name=tool_name,
                                     tool_call_id=tool_call["id"]))
```

`tool_call_id` bắt buộc phải khớp: LLM cần biết kết quả nào ứng với lời gọi nào khi nó
gọi nhiều công cụ cùng lúc.

### Bước 5 — Quay lại `llm_node` (vòng 2, 3, 4)

```python
builder.add_edge("tools", "llm_node")   # tool xong thì luôn quay về LLM
```

Vòng 2: LLM đọc danh sách thị trấn, nhận ra cần thời tiết → gọi `weather_forecast("St Ives")`.
Vòng 3: gọi tiếp `weather_forecast("Falmouth")`.
Vòng 4: đã đủ dữ liệu → trả về `AIMessage` **có content, không có tool_calls** →
`tools_condition` cho ra `END`.

**Hệ quả về chi phí cần nhớ:** một câu hỏi gọi 3 công cụ = **4 lần gọi model**, không phải
1. Đo thật: 2 câu hỏi → 6 lần gọi Gemini, 5.633 token vào, 261 token ra.

### Bước 6 — Trả kết quả ra ngoài

Đường JSON thường (`POST /chat`): chờ xong hết rồi trả một cục.
Đường SSE (`GET /chat/stream`): đẩy từng sự kiện ngay khi xảy ra — người dùng thấy tiến
trình thay vì màn hình trắng 8 giây.

---

## 5. Hai công cụ của agent

### Công cụ là gì, LLM "gọi" bằng cách nào

LLM **không thực thi code**. Nó chỉ trả về một đoạn JSON nói "tôi muốn gọi hàm tên X với
tham số Y". Code của bạn (node `tools`) mới là thứ thực sự chạy hàm rồi đưa kết quả lại
cho LLM. Hiểu điều này là hiểu bản chất tool calling.

Vậy LLM biết có công cụ nào? Nhờ `.bind_tools()` — LangChain đọc chữ ký hàm và mô tả rồi
gửi kèm mỗi lần gọi model.

### Tool 1 — `search_travel_info`

```python
@tool(description="Search travel information about destinations in England. "
                  "Use it to find towns, beaches, resorts and activities in Cornwall.")
def search_travel_info(query: str) -> str:
    docs = get_travel_info_retriever().invoke(query)
    top = docs[:4] if isinstance(docs, list) else docs
    return "\n---\n".join(d.page_content for d in top)
```

**Mô tả công cụ chính là giao diện lập trình dành cho LLM.** Mô tả mơ hồ thì LLM chọn sai
công cụ. Đây là lý do có hẳn một test bắt buộc mô tả không được rỗng:

```python
def test_both_tools_are_registered_with_descriptions():
    for tool in lab.TOOLS:
        assert len(tool.description) > 30
```

### Tool 2 — `weather_forecast`

```python
@tool(description="Get the CURRENT weather of a town or city anywhere in the world, given "
                  "its name. Pass 'country' when you know it (e.g. 'United Kingdom') because "
                  "many towns share a name. Returns condition, temperature, wind and rain.")
def weather_forecast(town: str, country: str = "") -> dict:
    service = WeatherForecastService if WEATHER_MODE == "mock" else OpenMeteoWeatherService
    try:
        forecast = (service.get_forecast(town, country)
                    if service is OpenMeteoWeatherService else service.get_forecast(town))
    except Exception as exc:
        return {"error": f"Weather service failed for '{town}'.", "details": str(exc)}
    if forecast is None:
        return {"error": f"No weather data available for '{town}'."}
    return forecast
```

Ba điểm thiết kế đáng nói khi phỏng vấn:

**a) Tham số `country` tồn tại vì một lỗi thật.** Falmouth có ở cả Anh và Mỹ. Không có
`country`, API địa danh trả về Falmouth (Massachusetts) và agent báo thời tiết sai nước.
Mô tả công cụ *chủ động dạy LLM* nên truyền `country`. Có test riêng:

```python
def test_country_argument_disambiguates_same_named_towns(fake_open_meteo, monkeypatch):
    lab.weather_forecast.invoke({"town": "Falmouth", "country": "United Kingdom"})
    forecast_params = [p for url, p in fake_open_meteo if "forecast" in url][0]
    assert forecast_params["latitude"] == 50.15   # Falmouth, Cornwall
```

**b) Tool lỗi thì trả `dict` có khoá `error`, không ném exception.** Vì sao: nếu ném
exception, cả agent sập. Trả lỗi có cấu trúc thì LLM đọc được "không có dữ liệu cho thị
trấn này" và **tự xoay xở** — thử thị trấn khác hoặc nói thật với người dùng. Đây là
nguyên tắc thiết kế công cụ cho agent.

**c) Sách dùng dữ liệu giả (random), sản phẩm này dùng API thật** (Open-Meteo, miễn phí,
không cần API key). Bản giả vẫn giữ, bật bằng `WEATHER_MODE=mock` — hữu ích khi test.

---

## 6. Tầng agent: LangGraph

### Toàn bộ phần lắp ráp chỉ có 6 dòng

```python
builder = StateGraph(AgentState)
builder.add_node("llm_node", llm_node)
builder.add_node("tools", tools_execution_node)
builder.add_conditional_edges("llm_node", tools_condition)
builder.add_edge("tools", "llm_node")
builder.set_entry_point("llm_node")
travel_info_agent = builder.compile()
```

Đọc như một sơ đồ: hai node, một cạnh có điều kiện (LLM → tools hoặc END), một cạnh cố
định (tools → LLM), điểm vào là LLM.

### Vì sao dùng đồ thị mà không phải vòng `while`?

Viết bằng `while` cũng được, nhưng đồ thị cho bạn: **checkpointing** (lưu trạng thái giữa
chừng, khôi phục được), **streaming** từng bước (chính là thứ SSE dùng), **human-in-the-loop**
(dừng trước một node để chờ người duyệt), và khả năng mở rộng thành nhiều agent. Vòng
`while` muốn có những thứ đó thì phải tự viết lại toàn bộ.

### Vì sao repo có cả bản dựng tay và bản dựng sẵn?

`main_03_01.py` làm y hệt nhưng chỉ 3 dòng:

```python
travel_info_agent = create_react_agent(model=llm_model, tools=TOOLS, prompt=SYSTEM_PROMPT)
```

Giữ cả hai là **có chủ đích**: bản dựng tay chứng minh bạn hiểu cơ chế bên dưới, bản dựng
sẵn chứng minh bạn biết dùng công cụ có sẵn khi làm thật. Nếu bị hỏi "sao không dùng luôn
`create_react_agent`?", câu trả lời là: khi agent hỏng, người chỉ biết bản dựng sẵn sẽ
không biết bắt đầu gỡ từ đâu.

---

## 7. RAG và vector store

### RAG là gì

**Retrieval-Augmented Generation**: thay vì hy vọng LLM "nhớ" thông tin, ta **tìm** đoạn
văn liên quan rồi **đưa vào prompt** cho LLM đọc mà trả lời. Giải quyết ba vấn đề: LLM
không biết dữ liệu riêng của bạn, không biết thông tin mới, và hay bịa.

### Đường đi của dữ liệu

```
4 trang Wikivoyage (Cornwall, North/South/West Cornwall)
        ↓ tải về
   văn bản thô
        ↓ cắt nhỏ: chunk_size=1024, overlap=128
   92 đoạn (chunk)
        ↓ embedding (gemini-embedding-001)
   92 vector số
        ↓ lưu
   Chroma (3,3 MB trên đĩa)
```

**Embedding** là biến đoạn văn thành một dãy số sao cho hai đoạn nội dung giống nhau thì
hai dãy số gần nhau. Nhờ đó tìm được theo **ý nghĩa** chứ không phải theo từ khoá: hỏi
"bãi biển đẹp" vẫn tìm ra đoạn viết "sandy beaches" dù không trùng chữ nào.

**Vì sao phải cắt nhỏ?** Một trang web quá dài để nhét cả vào prompt, và nhét cả trang thì
phần lớn là nhiễu. Cắt 1024 ký tự để mỗi mảnh đủ ngắn mà vẫn trọn ý.

**Vì sao chồng lấn 128 ký tự?** Để một câu bị cắt ngang không mất nghĩa — nó xuất hiện
trọn vẹn ở ít nhất một mảnh.

### Cơ chế cache và cái bẫy đã gặp

```python
cached = None
if os.path.isdir(PERSIST_DIR):
    cached = Chroma(persist_directory=PERSIST_DIR, embedding_function=embeddings)
    # Thư mục TỒN TẠI không có nghĩa là CÓ DỮ LIỆU
    if not cached.get(limit=1)["ids"]:
        print("Cached vector store is empty - rebuilding.")
        cached = None
_ti_vectorstore_client = cached or build_vectorstore(UK_DESTINATIONS)
```

Xem mục 14 để biết vì sao dòng kiểm tra đó tồn tại.

---

## 8. MCP

**Model Context Protocol** là chuẩn để agent lấy công cụ từ **một tiến trình khác**, thay
vì import trực tiếp trong code.

```
main_02_02.py :  agent ──import Python──▶      hàm tool        (cùng 1 tiến trình)
main_04_mcp.py:  agent ──JSON-RPC/stdio──▶ mcp_server.py       (2 tiến trình riêng)
```

**Được gì:** đổi server (viết ngôn ngữ khác, chạy máy khác, do đội khác quản lý) mà không
sửa dòng nào ở agent; và mọi ứng dụng nói được MCP — Claude Desktop, Cursor — đều dùng lại
được 2 công cụ này ngay.

**Một chi tiết kỹ thuật đáng nhớ:** MCP trên stdio dùng **stdout để truyền JSON-RPC**. Mọi
lệnh `print` lọt vào stdout sẽ làm hỏng kết nối. Trong `mcp_server.py` phải chuyển hướng
log sang stderr lúc import — nếu không, server chết im lặng không rõ lý do.

---

## 9. Tầng phục vụ: API, Docker, giám sát

Ba phần này mỗi phần có một tài liệu riêng, đây chỉ là bản tóm tắt để nối mạch:

| Phần | Làm gì | Tài liệu chi tiết |
|---|---|---|
| **FastAPI + SSE** | Biến agent thành dịch vụ ai gọi cũng được; SSE đẩy từng bước về client ngay khi xảy ra thay vì bắt chờ 8 giây | [HOC_FASTAPI_SSE.md](hoc/HOC_FASTAPI_SSE.md) |
| **Docker + Compose** | Đóng gói để chạy giống nhau ở mọi máy; multi-stage, non-root, healthcheck; compose chạy 4 dịch vụ bằng 1 lệnh | [HOC_DOCKER.md](hoc/HOC_DOCKER.md) |
| **Prometheus + Grafana** | Đo p95 latency, số lần gọi từng tool, tool lỗi, token và **chi phí USD** | [HOC_PROMETHEUS.md](hoc/HOC_PROMETHEUS.md) |

Ba con số đáng nhớ từ ba phần này: SSE làm sự kiện đầu tiên về trong **~1 giây** thay vì
8 giây; image Docker **1,4 GB**, rebuild sau sửa code **~15 giây**; **p95 = 7,55 giây**.

---

## 10. Đánh giá chất lượng (eval)

Đây là phần **hiếm nhất** trong portfolio sinh viên, và là thứ đáng khoe nhất.

### Vấn đề: làm sao biết agent tốt hay tệ?

LLM không có đúng/sai nhị phân. Chạy thử vài câu thấy "có vẻ ổn" không phải là bằng chứng.
`evals/eval_agent.py` đo hai chỉ số trên một bộ 8 câu hỏi cố định:

**Chỉ số 1 — Tool-selection accuracy (chấm tự động, khách quan).** Đọc lịch sử tin nhắn
thật để biết agent đã gọi công cụ nào, so với công cụ *cần phải gọi*:

```python
def called_tools(messages) -> list[str]:
    names = []
    for message in messages:
        if isinstance(message, AIMessage):
            names.extend(call["name"] for call in message.tool_calls or [])
    return names
```

Chú ý: **đọc từ state thật, không đoán từ câu trả lời**. Đây là điểm khiến bài đo đáng tin.

**Chỉ số 2 — Answer quality (LLM-as-judge).** Một LLM khác chấm câu trả lời 1–5 điểm theo
tiêu chí "hữu ích, cụ thể, có bám dữ liệu thật".

### Kết quả thật

| Chỉ số | Kết quả |
|---|---|
| Tool-selection accuracy | **100%** (8/8) |
| Answer quality (1–5) | **4.1** |
| Latency trung bình | 10,4 s |

**Và một điểm yếu thật, phải nói ra nếu được hỏi:** câu *"I want a surfing town in Cornwall
where it is not raining today"* chọn đúng công cụ nhưng chỉ được **2/5 điểm**. Agent gọi
`weather_forecast` ba lần nhưng câu trả lời không chốt được một thị trấn cụ thể. Đây là ví
dụ hoàn hảo cho việc **chọn đúng công cụ không đồng nghĩa với trả lời tốt** — và là lý do
phải đo hai chỉ số chứ không phải một.

Biết và nói ra điểm yếu này trong phỏng vấn tạo ấn tượng tốt hơn hẳn việc chỉ khoe 100%.

### Cổng chặn hồi quy trong CI

Đo được rồi thì phải **chặn** được. Thêm `--gate` là script trả exit code 1 khi chất lượng
tụt dưới ngưỡng, và workflow `Eval gate` dùng đúng cơ chế đó để bắt CI đỏ:

```python
def decide_gate(accuracy, avg_score, min_accuracy=MIN_TOOL_ACCURACY,
                min_score=MIN_JUDGE_SCORE) -> list[str]:
    failures = []
    if accuracy < min_accuracy:
        failures.append(f"tool-selection accuracy {accuracy:.0%} < nguong {min_accuracy:.0%}")
    if avg_score < min_score:
        failures.append(f"answer quality {avg_score:.2f}/5 < nguong {min_score:.2f}/5")
    return failures
```

Ba quyết định thiết kế đáng nói:

**1. Dùng ngưỡng, không so bằng.** LLM-as-judge có tính ngẫu nhiên — cùng bộ 8 câu, lần
chấm 4.4, lần chấm 4.1. Cổng đòi đúng một con số sẽ đỏ vô cớ; ngưỡng 85% và 3.5/5 có
khoảng đệm nên chỉ đỏ khi tụt thật.

**2. Tách thành hàm thuần tuý để test được.** `decide_gate` không gọi LLM, không đọc file,
nên có 6 unit test chạy offline. Lý do: **một cái cổng hỏng theo kiểu "luôn cho qua" còn
tệ hơn không có cổng** — CI vẫn xanh trong khi agent đã hỏng.

**3. Tách workflow riêng khỏi `ci.yml`.** Unit test luôn chạy được, miễn phí, không cần
key. Eval thì gọi LLM thật: cần secret và tốn khoảng $0,006 mỗi lần. Gộp chung sẽ khiến
PR từ fork đỏ vì thiếu secret — nên workflow eval tự bỏ qua trong trường hợp đó.

---

## 11. Test và CI

**29 test, chạy hoàn toàn offline** — không gọi mạng, không cần API key, xong trong ~20 giây.

Cách làm: thay thế thứ ở ngoài bằng đồ giả.

```python
class FakeAgent:
    def stream(self, state, stream_mode=None):
        yield from FAKE_RUN      # kịch bản dựng sẵn: gọi 1 tool rồi trả lời
```

```python
monkeypatch.setattr(lab.requests, "get", fake_get)    # giả API thời tiết
```

Vì sao quan trọng: test gọi LLM thật thì chậm, tốn tiền, và **kết quả đổi mỗi lần chạy**
nên không dùng làm test được. Mọi công ty làm sản phẩm LLM đều phải giải bài này.

Những thứ được test — chọn lọc, mỗi cái ứng với một rủi ro thật:

| Test | Bảo vệ điều gì |
|---|---|
| `test_country_argument_disambiguates_same_named_towns` | Falmouth Anh ≠ Falmouth Mỹ |
| `test_service_failure_is_reported_as_error_not_exception` | Tool hỏng không làm sập agent |
| `test_existing_but_empty_store_directory_triggers_a_rebuild` | Lỗi Docker volume ở mục 14 |
| `test_stream_emits_events_in_order` | Hợp đồng SSE: đúng thứ tự start→tool→answer→done |
| `test_stream_reports_errors_instead_of_crashing` | Lỗi giữa stream báo bằng event, không đứt ngang |
| `test_unknown_model_counts_tokens_but_not_cost` | Không bịa số tiền cho model lạ |
| `test_limit_is_per_client_not_global` | Người này tiêu hết suất không làm người khác bị chặn |
| `test_healthz_and_metrics_are_never_limited` | Probe hệ thống không bị rate limit chặn nhầm |

**CI (GitHub Actions)**: mỗi lần push, GitHub tự cài thư viện, chạy `ruff check` (lint) và
`pytest`. Dấu tích xanh trên repo nghĩa là code trên nhánh main luôn chạy được.

---

## 12. Bảng số liệu tổng hợp

Học thuộc bảng này là trả lời được phần lớn câu hỏi định lượng:

| Hạng mục | Số đo thật |
|---|---|
| Kho kiến thức | 4 trang Wikivoyage → **92 chunk**, 3,3 MB |
| Cắt chunk | 1024 ký tự, chồng lấn 128 |
| Model | `gemini-3.1-flash-lite` + `gemini-embedding-001` |
| Tool-selection accuracy | **100%** (8/8 ca) |
| Answer quality (LLM-judge) | **4.1/5** |
| Latency trung bình | 10,4 s |
| **p95 latency** | **7,55 s** |
| Chi phí | **$0,0035 cho 5 request** ≈ $0,0007/câu ≈ $0,70 cho 1000 câu |
| Token (2 câu hỏi) | 5.633 vào / 261 ra, qua **6 lần gọi model** |
| Test | **29**, offline, ~20 s |
| Giới hạn tần suất | 30 câu/IP/giờ (mặc định), trả `429` + `Retry-After` |
| Docker image | 1,4 GB; build đầu 3 phút 50, rebuild ~15 giây |
| Số dịch vụ trong compose | 4 (api, ui, prometheus, grafana) |

---

## 13. Những quyết định thiết kế và đánh đổi

Phần này là thứ phân biệt "người làm theo tutorial" với "kỹ sư". Mỗi mục là một câu hỏi
phỏng vấn tiềm năng.

**1. Vì sao system prompt cấm LLM tự nghĩ ra tên thị trấn?**

> *"Only use the tools to find the information you need (including town names). Never
> invent town names from your own knowledge."*

Không có câu này, LLM lấy sẵn "Newquay, Falmouth" từ kiến thức nội tại rồi nhảy thẳng sang
tra thời tiết, **bỏ qua công cụ tìm kiếm**. Chính sách vẫn ra câu trả lời trông hợp lý,
nhưng không dựa trên dữ liệu của ta — nghĩa là không kiểm soát được và dễ bịa. Sách cũng
gặp đúng vấn đề này (mục 11.8.1).

**2. Vì sao tool trả lỗi có cấu trúc thay vì ném exception?** Để agent tự phục hồi thay vì
sập. Xem mục 5.

**3. Vì sao SSE mà không phải WebSocket?** Dữ liệu chỉ chảy một chiều server→client. SSE
chạy trên HTTP thường nên qua được mọi proxy và có sẵn tự kết nối lại; WebSocket hai chiều
nhưng nặng và phải tự lo reconnect. ChatGPT/Claude cũng dùng SSE.

**4. Vì sao chỉ số đo lại đặt ở ba tầng khác nhau?** Vì mỗi tầng biết một thứ mà tầng khác
không biết: chỉ endpoint biết một request bắt đầu/kết thúc khi nào; chỉ node tool biết
từng công cụ chạy bao lâu; chỉ `llm_node` biết mỗi vòng ReAct tốn bao nhiêu token.

**5. Vì sao buckets của histogram phải tự đặt?** Mặc định dừng ở 10 giây, agent này chạy
5–20 giây → mọi request rơi vào rổ cuối và p95 vô nghĩa.

**6. Vì sao giữ cả bản mock thời tiết của sách?** Để test và demo offline không phụ thuộc
mạng. Bật bằng biến môi trường, không phải sửa code.

**7. Vì sao vector store cache xuống đĩa?** Mỗi lần dựng lại tốn thời gian tải web và tiền
embedding. Cache làm lần chạy thứ hai vào thẳng.

---

## 14. Những lỗi thật đã gặp

Kể được lỗi và cách sửa là bằng chứng mạnh nhất cho thấy bạn thật sự làm ra sản phẩm này.

**Lỗi 1 — Vector store rỗng trong Docker (lỗi im lặng, nguy hiểm nhất)**

Chạy compose lần đầu: API báo `healthy`, agent trả lời trơn tru, nhưng vector store trong
container có **0 chunk** trong khi máy thật có 92. Công cụ tìm kiếm trả về rỗng mà **không
có lỗi nào hiện ra**.

Nguyên nhân: code kiểm tra `os.path.isdir(PERSIST_DIR)`. Khi gắn Docker volume vào đường
dẫn đó, **thư mục luôn tồn tại nhưng rỗng** → code tưởng đã có kho, nạp một kho rỗng.

Sửa: kiểm tra *có dữ liệu thật không*, không chỉ kiểm tra thư mục. Thêm test hồi quy.

Bài học: **"thư mục tồn tại" không đồng nghĩa với "có dữ liệu"**, và lỗi loại này chỉ lộ
ra khi chạy trong môi trường đích.

**Lỗi 2 — Grafana không vẽ panel nào, không báo lỗi gì**

Dashboard nạp thành công, log sạch, nhưng trang trắng trơn. Hai nguyên nhân cộng lại:
datasource không có `uid` cố định (Grafana tự sinh uid ngẫu nhiên, dashboard trỏ sai), và
mỗi panel thiếu trường `"id"`. Sửa cả hai thì panel hiện ngay.

**Lỗi 3 — Falmouth nhầm nước**

API địa danh trả về Falmouth (Mỹ) thay vì Falmouth (Cornwall). Sửa bằng cách thêm tham số
`country` và **dạy LLM dùng nó thông qua mô tả công cụ**.

**Lỗi 4 — `EventSource` tự kết nối lại vô hạn**

Trình duyệt tưởng mạng rớt khi server đóng stream nên tự hỏi lại — mỗi vòng là một lần gọi
LLM tính tiền. Sửa: client gọi `es.close()` khi nhận sự kiện `done`. Đã kiểm chứng
`readyState = 2` (CLOSED) sau khi xong.

**Lỗi 5 — Wikivoyage chặn `AsyncHtmlLoader` của sách**

Thư viện sách dùng bị Wikimedia chặn. Đổi sang `WebBaseLoader` (nền `requests`), tải được
và còn trả về text đã bóc thẻ HTML sạch hơn.

**Lỗi 6 — Container `ui` bị báo "unhealthy" dù chạy hoàn toàn bình thường**

`docker compose ps` hiện `ui ... (unhealthy)`. Nguyên nhân: hai service `api` và `ui` dùng
**chung một image**, nên `ui` thừa hưởng luôn `HEALTHCHECK` trong Dockerfile — mà cái đó
gọi vào cổng **8000** của API, trong khi Streamlit chạy ở cổng **8501**.

Sửa bằng cách ghi đè healthcheck cho riêng service `ui` trong compose, trỏ vào endpoint
sẵn có của Streamlit:

```yaml
healthcheck:
  test: ["CMD", "python", "-c",
         "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health')"]
```

Bài học: **dùng chung image thì cũng dùng chung healthcheck** — service nào phục vụ cổng
khác thì phải tự khai lại. Sai chỗ này không làm hỏng chức năng, nhưng hệ thống điều phối
(Kubernetes, Cloud Run) sẽ liên tục khởi động lại một container đang khoẻ mạnh.

---

## 15. Giới hạn hiện tại

Nói ra được giới hạn là dấu hiệu của người hiểu hệ thống mình làm:

| Giới hạn | Ảnh hưởng |
|---|---|
| Bản deploy công khai không có rate limit | Giới hạn tần suất nằm trong `api.py`, còn bản chạy công khai là `app.py` (Streamlit) |
| Chỉ giao diện Streamlit được deploy | Bản FastAPI (`/docs`, `/chat/stream`, `/metrics`) mới chỉ chạy local |
| Kho kiến thức chỉ 4 trang về Cornwall | Hỏi vùng khác là không có dữ liệu |
| Không nhớ hội thoại nhiều lượt | Hỏi "còn thị trấn kia thì sao?" là không hiểu |
| Chỉ tìm theo vector, chưa hybrid | Tên riêng/số hiệu tìm kém hơn nếu có thêm BM25 |
| Không chống prompt injection | Nội dung Wikivoyage là input không tin cậy |
| Rate limit đếm trong bộ nhớ | Đúng với một instance; chạy nhiều bản sao phải chuyển sang Redis |
| Eval chỉ 8 ca | Đủ để phát hiện hồi quy lớn, chưa đủ kết luận mạnh |
| Bộ đếm metrics reset khi restart | Bình thường với Prometheus, nhưng cần biết |

---

## 16. 23 câu phỏng vấn và cách trả lời

**Về agent**

1. *Agent khác chatbot và workflow thế nào?* → Mục 2.
2. *ReAct là gì?* → Vòng lặp suy nghĩ ↔ hành động; LLM tự quyết gọi công cụ nào, lặp đến
   khi đủ thông tin thì trả lời.
3. *LLM "gọi hàm" bằng cách nào?* → Nó không chạy code. Nó trả về JSON mô tả muốn gọi hàm
   nào với tham số gì; code của mình mới thực thi rồi đưa kết quả lại.
4. *Làm sao LLM biết có công cụ nào?* → `bind_tools()` gửi tên, tham số và **mô tả** công
   cụ kèm mỗi lần gọi model.
5. *Mô tả công cụ quan trọng thế nào?* → Nó là API dành cho LLM. Mô tả kém → chọn sai công
   cụ. Có test bắt buộc mô tả dài tối thiểu.

**Về LangGraph**

6. *State của bạn là gì?* → Một danh sách message, gộp bằng `operator.add` để cộng dồn thay
   vì ghi đè.
7. *Cạnh điều kiện hoạt động ra sao?* → `tools_condition` xem message cuối có `tool_calls`
   không: có → node tools, không → END.
8. *Sao không dùng vòng while?* → Đồ thị cho checkpointing, streaming từng bước,
   human-in-the-loop và mở rộng đa agent.
9. *Sao giữ cả bản dựng tay lẫn `create_react_agent`?* → Bản tay để hiểu và gỡ lỗi, bản
   dựng sẵn để làm nhanh khi production.

**Về RAG**

10. *RAG giải quyết gì?* → LLM không biết dữ liệu riêng, không biết tin mới, và hay bịa.
11. *Vì sao chunk 1024 chồng lấn 128?* → Đủ ngắn để không nhiễu, chồng lấn để câu bị cắt
    vẫn còn nguyên ở một mảnh.
12. *Embedding là gì?* → Biến văn bản thành vector sao cho nội dung giống nhau thì gần nhau,
    nhờ đó tìm theo ý nghĩa chứ không theo từ khoá.

**Về hệ thống**

13. *SSE khác WebSocket?* → Mục 13.3.
14. *Lỗi giữa lúc đang stream xử lý sao?* → 200 đã gửi rồi nên không đổi status được; phải
    phát sự kiện `error` rồi đóng tử tế. Có test.
15. *Multi-stage Docker để làm gì?* → Image cuối không mang pip cache và công cụ biên dịch;
    nhỏ hơn, ít bề mặt tấn công hơn.
16. *Sao container chạy non-root?* → Giới hạn thiệt hại nếu app bị khai thác.
17. *Prometheus push hay pull?* → Pull; scrape thất bại tự nó đã là một tín hiệu.
18. *Đo gì cho hệ LLM mà hệ thường không có?* → Token, **chi phí quy ra tiền**, số vòng gọi
    công cụ, tỉ lệ tool lỗi, điểm eval.

**Về chất lượng**

19. *Làm sao biết agent tốt?* → Hai chỉ số: tool-selection accuracy đọc từ state thật (100%)
    và LLM-as-judge (4.1/5). Kèm ví dụ ca 2/5 để cho thấy hai chỉ số bổ sung nhau.
20. *Test hệ thống có LLM kiểu gì?* → Thay agent và API ngoài bằng đồ giả, test hợp đồng:
    đúng thứ tự sự kiện, đúng schema, đúng mã lỗi. 29 test chạy offline trong 20 giây.

**Về vận hành**

21. *Mở demo công khai thì bảo vệ thế nào?* → Rate limit cửa sổ trượt theo IP, trả `429`
    kèm `Retry-After`; `/healthz` và `/metrics` được miễn trừ. Đếm trong bộ nhớ là đủ cho
    một instance, nhiều instance thì cần Redis.
22. *Vì sao commit cả vector store 3,3 MB vào git?* → Để cold start phục vụ được ngay thay
    vì tải lại 4 trang web và trả tiền embedding mỗi lần khởi động. Đánh đổi: file nhị phân
    trong git; chấp nhận được vì nhỏ và ít thay đổi.
23. *Deploy chỗ nào và vì sao?* → Streamlit Community Cloud: miễn phí, không cần thẻ nên
    không thể phát sinh chi phí, và chạy thẳng `app.py` sẵn có. Kế hoạch ban đầu là Docker
    Space trên Hugging Face nhưng tính năng đó đã chuyển sang gói PRO — phải đổi hướng khi
    làm thật. Cloud Run chuyên nghiệp hơn nhưng bắt buộc gắn thẻ.

---

## 17. Demo 5 phút

Kịch bản trình bày trước thầy hoặc nhà tuyển dụng:

```bash
docker compose up -d
```

1. **(30 giây) Nói vấn đề.** "Câu hỏi cần nhiều nguồn thông tin và không biết trước thứ tự
   tra cứu — đó là lúc cần agent thay vì workflow."
2. **(90 giây) Demo SSE** tại http://localhost:8000 — hỏi *"Suggest two Cornwall beach
   towns with nice weather"*, chỉ vào từng sự kiện hiện dần: "nó tìm thị trấn trước, rồi
   mới tra thời tiết từng cái — thứ tự này do model tự quyết."
3. **(60 giây) Mở `/docs`** — API có schema, validation, tài liệu tự sinh.
4. **(60 giây) Mở Grafana** http://localhost:3000/d/travel-agent — "p95 7,55 giây, và tôi
   đo được cả chi phí: $0,0007 mỗi câu hỏi."
5. **(60 giây) Mở `evals/results.md`** — "100% chọn đúng công cụ, 4.1/5 chất lượng. Có một
   ca 2/5, đây là hạn chế tôi đã biết và đang xử lý."

Kết bằng một câu: *"Toàn bộ chạy bằng một lệnh `docker compose up`, có 29 test và CI."*

---

## 18. Từ điển thuật ngữ

| Từ | Nghĩa ngắn gọn |
|---|---|
| **Agent** | Chương trình dùng LLM để tự quyết định gọi công cụ nào, theo thứ tự nào |
| **ReAct** | Mẫu thiết kế xen kẽ suy nghĩ (reasoning) và hành động (acting) |
| **Tool calling** | Cơ chế LLM yêu cầu gọi một hàm với tham số cụ thể |
| **LangChain** | Thư viện ghép nối LLM, prompt, công cụ, vector store |
| **LangGraph** | Thư viện dựng agent dạng đồ thị node/edge, cùng nhà với LangChain |
| **State** | Dữ liệu chảy qua đồ thị; ở đây là danh sách message |
| **Node / Edge** | Một bước xử lý / đường nối giữa các bước |
| **MCP** | Chuẩn giao thức để lấy công cụ từ tiến trình khác |
| **RAG** | Tìm tài liệu liên quan rồi đưa vào prompt để LLM trả lời có căn cứ |
| **Embedding** | Vector số biểu diễn ý nghĩa của văn bản |
| **Vector store** | Kho lưu embedding, tìm theo độ gần (ở đây là Chroma) |
| **Chunk** | Một mảnh văn bản sau khi cắt nhỏ |
| **SSE** | Server đẩy sự kiện text một chiều qua HTTP |
| **FastAPI / uvicorn** | Thư viện viết API / chương trình chạy nó |
| **pydantic** | Khai báo và kiểm tra kiểu dữ liệu bằng class Python |
| **Docker image / container** | Bản đóng gói tĩnh / một lần chạy của bản đó |
| **Volume** | Ổ đĩa của Docker, sống lâu hơn container |
| **Prometheus / Grafana** | Hệ thu thập chỉ số / hệ vẽ dashboard |
| **PromQL** | Ngôn ngữ truy vấn của Prometheus |
| **p95** | Ngưỡng mà 95% request nhanh hơn nó |
| **Eval** | Bộ đo chất lượng agent trên tập câu hỏi cố định |
| **LLM-as-judge** | Dùng một LLM khác để chấm điểm câu trả lời |
| **CI** | Máy chủ tự chạy lint + test mỗi lần push |
| **Rate limit** | Giới hạn số request mỗi người trong một khoảng thời gian |
| **Cold start** | Lần khởi động đầu tiên, khi chưa có gì được nạp sẵn |
| **Frontmatter** | Khối YAML ở đầu file Markdown, dùng làm cấu hình |

---

## 19. Giới hạn tần suất — chuẩn bị cho việc mở công khai

### Vấn đề

Khi deploy công khai, **API key Gemini của bạn nằm sau một cái nút mà bất kỳ ai trên
internet cũng bấm được**. Một người rảnh rỗi viết vòng lặp gọi 10.000 lần là hết sạch
quota (hoặc hết tiền nếu bạn đã gắn thẻ). Đây là việc **bắt buộc làm trước khi deploy**,
không phải tính năng "có thì tốt".

### Thuật toán: cửa sổ trượt (sliding window)

Ý tưởng đơn giản: với mỗi người gọi, ghi lại **thời điểm** của từng request. Khi có
request mới, vứt bỏ những lượt đã quá 1 giờ, rồi đếm số lượt còn lại.

```
Giới hạn 3 câu/giờ. Trục thời gian:

  09:00  09:10  09:30        10:05
    │      │      │            │
    ✓      ✓      ✓            ✓  ← lúc 10:05, lượt 09:00 đã rơi khỏi cửa sổ
                               (còn 09:10, 09:30 → mới 2 lượt → cho qua)
```

Code trong `api.py`:

```python
RATE_LIMIT_PER_HOUR = int(os.environ.get("RATE_LIMIT_PER_HOUR", "30"))
_RATE_WINDOW_SECONDS = 3600
_hits: dict[str, deque[float]] = defaultdict(deque)

def enforce_rate_limit(request: Request) -> None:
    key = client_key(request)
    now = time.time()
    hits = _hits[key]

    while hits and now - hits[0] > _RATE_WINDOW_SECONDS:   # bỏ lượt đã cũ
        hits.popleft()

    if len(hits) >= RATE_LIMIT_PER_HOUR:
        metrics.RATE_LIMITED.inc()
        retry_after = int(_RATE_WINDOW_SECONDS - (now - hits[0])) + 1
        raise HTTPException(status_code=429, detail=..., 
                            headers={"Retry-After": str(retry_after)})

    hits.append(now)
```

`deque` (hàng đợi hai đầu) được chọn vì cần xoá ở **đầu** danh sách rất nhiều lần —
`list.pop(0)` phải dịch cả mảng, `deque.popleft()` thì không.

### "Dependency" của FastAPI — khái niệm cần hiểu

```python
@app.post("/chat", dependencies=[Depends(enforce_rate_limit)])
def chat(request: ChatRequest) -> ChatResponse:
    ...
```

`Depends(...)` bảo FastAPI: **chạy hàm này trước, nếu nó ném lỗi thì handler không chạy**.
Nhờ vậy logic chặn nằm tách khỏi logic nghiệp vụ — thêm rate limit vào endpoint mới chỉ
tốn một dòng, và bỏ đi cũng vậy. Đây là cách chuẩn để làm xác thực, phân quyền, chặn lạm
dụng trong FastAPI.

### Ba quyết định thiết kế đáng nói

**1. Trả `429` kèm header `Retry-After`.** `429 Too Many Requests` là mã chuẩn cho tình
huống này (không phải `403`). `Retry-After` cho client biết chờ bao nhiêu giây — thư viện
HTTP tử tế sẽ tự đợi đúng khoảng đó thay vì đập liên tục.

**2. `/healthz` và `/metrics` được miễn trừ.** Nếu chặn cả hai endpoint này, Docker và
Prometheus gọi vào sẽ nhận `429`, hệ thống điều phối tưởng container chết và **khởi động
lại một container đang khoẻ**. Có test riêng cho điều này.

**3. Nhận dạng người gọi qua `X-Forwarded-For`.**

```python
forwarded = request.headers.get("x-forwarded-for", "")
if forwarded:
    return forwarded.split(",")[0].strip()
return request.client.host if request.client else "unknown"
```

Khi chạy sau proxy (Hugging Face, Cloud Run, nginx), `request.client.host` là IP của
**proxy** — tức mọi người dùng chung một suất, một người xài hết là cả thế giới bị chặn.
Vì vậy phải đọc `X-Forwarded-For`.

**Cảnh báo phải nói ra nếu bị hỏi:** header này do client tự đặt được, nên **không dùng để
chống tấn công có chủ đích**. Nó chỉ chặn lạm dụng thông thường. Muốn chống thật thì phải
xác thực bằng API key hoặc dùng rate limit ở tầng hạ tầng.

### Giới hạn của cách làm hiện tại

Bộ đếm nằm **trong bộ nhớ tiến trình**. Hệ quả: restart là mất bộ đếm, và nếu chạy nhiều
bản sao thì mỗi bản đếm riêng (3 instance × 30 = thực tế 90 câu/giờ). Đúng với quy mô hiện
tại; muốn chính xác khi scale thì chuyển bộ đếm sang Redis — logic không đổi, chỉ đổi chỗ
lưu.

### Bằng chứng chạy thật

Đặt giới hạn 2 câu/giờ rồi bắn 3 câu vào container:

```
cau 1: HTTP 200
cau 2: HTTP 200
cau 3: HTTP 429     retry-after: 3592

{"detail":"Demo limit reached: 2 questions per hour. Try again in 60 minute(s),
           or run it locally - the repo is public."}
```

Thông báo lỗi cố ý **nói cho người dùng cách khác để dùng tiếp** (chạy local, repo công
khai) thay vì chỉ đóng sập cửa. Chi tiết nhỏ nhưng là dấu hiệu của người nghĩ cho người dùng.

---

## 20. Đưa dữ liệu vào image và chuyện deploy

### Vấn đề cold start

Khi container khởi động lần đầu ở nơi chưa có sẵn vector store, nó phải: tải 4 trang
Wikivoyage → cắt 92 chunk → gọi API embedding → ghi ra đĩa. Mất khoảng một phút và **tốn
tiền embedding**. Nền tảng miễn phí thường cho container ngủ khi vắng khách rồi dựng lại
khi có người vào — nghĩa là chuyện này lặp đi lặp lại.

### Ba lựa chọn và vì sao chọn cách này

| Cách | Ưu | Nhược |
|---|---|---|
| Dựng lúc khởi động (cũ) | Repo sạch | Chậm và tốn tiền ở **mỗi** cold start |
| Dựng lúc **build image** | Cold start nhanh | Phải đưa API key vào lúc build — **sai nguyên tắc bảo mật** |
| **Commit sẵn vào repo** ✅ | Cold start tức thì, không tốn tiền, không cần key lúc build | 3,3 MB nhị phân trong git |

Chọn cách 3. Đánh đổi được chấp nhận vì dữ liệu **nhỏ và gần như không đổi**. Nếu kho
kiến thức lên hàng trăm MB hoặc thay đổi hằng ngày thì phải đổi hướng: tải từ object
storage (S3, MinIO) lúc khởi động.

Việc cần làm chỉ là bỏ thư mục khỏi hai file loại trừ:

```
.gitignore     → bỏ dòng chroma_travel_info/   (để git theo dõi)
.dockerignore  → bỏ dòng chroma_travel_info/   (để COPY . . đưa vào image)
```

Quên `.dockerignore` là dữ liệu vào git nhưng **không** vào image — đúng loại lỗi chỉ lộ
ra khi deploy.

### Một hành vi của Docker cần biết

Trong `docker-compose.yml`, thư mục này bị gắn một **named volume** đè lên. Vậy dữ liệu
nướng trong image có bị che mất không?

Không — Docker có quy tắc: **volume có tên mà rỗng, khi gắn vào một thư mục đã có sẵn nội
dung trong image, thì nội dung đó được chép vào volume**. Nên lần chạy đầu volume tự có
đủ 92 chunk. (Quy tắc này **chỉ đúng với named volume**, không đúng với bind mount — bind
mount che hẳn thư mục gốc.)

### Bằng chứng chạy thật

Chạy container **không gắn volume** — đúng như khi deploy lên Hugging Face:

```
Warming up the vector store ...
Loading cached vector store ...     ← không tải web, không gọi API embedding
Vector store ready.
chunks = 92
```

Dòng `Loading cached` thay vì `Downloading destination pages` chính là bằng chứng.

### Deploy: chọn nền tảng nào, và một kế hoạch bị thực tế bác bỏ

Kế hoạch ban đầu là **Hugging Face Spaces bản Docker** — vì nó dùng lại đúng `Dockerfile`
đã có, và image đã chạy non-root **uid 1000** đúng như Spaces yêu cầu.

Nhưng khi bấm tạo Space thì ô Docker hiện nhãn 🔒 **Paid**. Kiểm tra trang pricing của
Hugging Face thấy dòng *"Host ZeroGPU, Gradio & Docker Spaces"* nằm trong gói **PRO
($9/tháng)**. Yêu cầu đặt ra là không tốn đồng nào, nên phải đổi hướng ngay tại chỗ.

| Nền tảng | Cần thẻ? | Chạy được gì | Kết luận |
|---|---|---|---|
| **Streamlit Community Cloud** ✅ | Không | `app.py` trực tiếp | **Đang dùng** |
| Hugging Face Spaces (Docker) | Không, nhưng cần PRO $9/tháng | Dockerfile | Loại vì mất phí |
| Google Cloud Run | **Có thẻ** | Dockerfile | Chuyên nghiệp nhất nhưng phải gắn thẻ |
| Vercel | — | Không hợp | Serverless: thời gian chạy ngắn, thư viện nặng không vừa |

Streamlit Cloud thắng vì hai thứ **đã chuẩn bị từ trước** khiến nó không tốn thêm công sức
nào: `app.py` đã có sẵn nên không phải viết lại giao diện, và vector store đã commit vào
repo nên nền tảng clone về là chạy ngay.

Bài học đáng nhớ hơn cả kỹ thuật: **điều kiện của nền tảng miễn phí thay đổi theo thời
gian**. Kế hoạch deploy phải kiểm chứng bằng cách bấm thử, đừng tin vào tài liệu viết từ
trước — kể cả tài liệu của chính mình.

### Trạng thái hiện tại

**Đã chạy công khai:** https://travel-ai-agent-92l7axm85zjfj2kmqu5e4r.streamlit.app

Streamlit Cloud tự deploy lại mỗi lần push lên `main`, không phải làm gì thêm. Hai điểm
còn hở, đã ghi ở mục 15: bản công khai chạy `app.py` nên **không có rate limit** (cơ chế đó
nằm trong `api.py`), và bản FastAPI kèm `/metrics` vẫn chỉ chạy local vì muốn deploy nó
thì cần nền tảng chạy Docker. Chi tiết ở [DEPLOY.md](DEPLOY.md).
