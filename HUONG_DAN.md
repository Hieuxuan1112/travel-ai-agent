# Hướng dẫn bài lab — AI Agent 2 tool với LangGraph (Chương 11)

Dự án: `D:\langgraph-agent-lab`
Nguồn: *AI Agents and Applications With LangChain, LangGraph, and MCP* — Chapter 11.

---

## 0. Chạy trong 3 bước

**Bước 1 — lấy API key** (miễn phí): vào https://aistudio.google.com/app/apikey →
*Create API key* → copy. Mở file `.env`, thay dòng:

```
GOOGLE_API_KEY=PASTE_YOUR_GOOGLE_AI_STUDIO_KEY_HERE
```

bằng key vừa tạo. (Key cũ trong project `Facebook-crappe` đã bị Google thu hồi — đã test, trả về `API_KEY_INVALID`.)

**Bước 2 — kiểm tra key + tên model:**

```bash
D:\langgraph-agent-lab\venv\Scripts\python.exe D:\langgraph-agent-lab\list_models.py
```

Nếu in ra danh sách model → key OK. Nếu tên `gemini-3.1-flash-lite` không có trong
danh sách, sửa `CHAT_MODEL` trong `.env` thành tên có thật (vd `gemini-2.5-flash`).

**Bước 3 — chạy agent:**

```bash
D:\langgraph-agent-lab\venv\Scripts\python.exe main_02_02.py
```

Lần chạy đầu mất ~1 phút (tải 4 trang Wikivoyage + tạo embedding). Các lần sau
nạp lại từ thư mục `chroma_travel_info/` nên vào thẳng chat ngay.

Muốn demo bằng **giao diện web** (đẹp hơn hẳn khi trình bày trước lớp):

```bash
D:\langgraph-agent-lab\venv\Scripts\streamlit.exe run D:\langgraph-agent-lab\app.py
```

---

## 1. Bức tranh lớn: agent là cái gì?

Một **LLM** (Gemini, GPT…) chỉ biết sinh chữ. Nó **không** tự tra được dữ liệu
của bạn, không biết thời tiết hôm nay. Muốn nó làm được thì phải đưa cho nó **tool**
(công cụ) — là các hàm Python bình thường.

Khác biệt cốt lõi giữa 2 kiểu hệ thống:

| | **Workflow** (chương 5) | **Agent** (chương 11 — bài này) |
|---|---|---|
| Thứ tự các bước | Lập trình viên viết cứng | **LLM tự quyết định** lúc chạy |
| Gọi tool nào | if/else trong code | LLM đọc mô tả tool rồi chọn |
| Gọi mấy lần | Cố định | Lặp đến khi đủ thông tin |

Câu để nói với thầy: *"Em không hardcode luồng. Em chỉ đăng ký 2 tool kèm mô tả,
LLM tự chọn tool nào, truyền tham số gì, gọi mấy vòng."*

### Bốn cái tên hay bị lẫn

- **LangChain** — thư viện "chuẩn hoá" việc nói chuyện với LLM: model, message,
  tool, embedding, vector store. Ở đây nó lo `@tool`, `bind_tools`, `ChatGoogleGenerativeAI`.
- **LangGraph** — xây agent dưới dạng **đồ thị** (node = việc, edge = luồng đi).
  Nó lo `StateGraph`, `tools_condition`, `create_react_agent`.
- **LangSmith** — trang web xem lại từng bước agent đã chạy (mục 11.9.3). Tuỳ chọn,
  bài này không bắt buộc.
- **MCP** — chuẩn cắm tool từ server ngoài. Chương sau, bài này chưa dùng.

---

## 2. Sáu khái niệm phải hiểu

### 2.1 Tool
Một hàm Python có `@tool`. Ví dụ trong `main_02_02.py`:

```python
@tool(description="Get the weather forecast, given a town name.")
def weather_forecast(town: str) -> dict:
    ...
```

LangChain tự sinh ra "tờ khai" gửi cho LLM gồm: **tên hàm**, **mô tả**, **tham số**
(`town`, kiểu `string`). LLM **không nhìn thấy code bên trong** — nó chỉ đọc mô tả.
→ Vì vậy **mô tả tool viết dở = agent chọn sai tool**. Đây là ý chính của mục 11.8.2.

### 2.2 Tool calling
LLM không tự chạy được hàm. Nó chỉ trả về một *yêu cầu*:

```python
tool_calls=[{'name': 'weather_forecast', 'args': {'town': 'St Ives'}, 'id': 'call_abc'}]
```

**Code của mình** mới là bên thực sự gọi `weather_forecast(town="St Ives")`, rồi
nhét kết quả ngược lại hội thoại dưới dạng `ToolMessage` để LLM đọc. Vòng lặp này
nằm ở lớp `ToolsExecutionNode` trong code.

### 2.3 ReAct (Reason + Act) — hình 11.1 của sách
Mẫu thiết kế: **suy nghĩ → hành động → đọc kết quả → suy nghĩ tiếp → … → trả lời**.

### 2.4 State
Trí nhớ của agent trong một lượt hỏi. Ở đây đơn giản là **danh sách message**:

```python
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
```

`operator.add` = **reducer**: node trả về `{"messages": [x]}` thì x được **nối thêm**
vào danh sách chứ không ghi đè. Bốn loại message: `SystemMessage` (nội quy),
`HumanMessage` (câu hỏi), `AIMessage` (LLM trả lời hoặc đòi gọi tool),
`ToolMessage` (kết quả tool).

### 2.5 Node và Edge
- `llm_node` — đưa toàn bộ message cho LLM, nhận về câu trả lời **hoặc** yêu cầu gọi tool.
- `tools` — thực thi các tool được yêu cầu.
- **Conditional edge** `tools_condition` — hàm rẽ nhánh: message cuối **còn** `tool_calls`
  → đi node `tools`; **hết** → `END`, in câu trả lời ra cho người dùng.

### 2.6 RAG / vector store (tool 1)
4 trang Wikivoyage về Cornwall được tải về → cắt thành đoạn 1024 ký tự → mỗi đoạn
biến thành vector số (embedding) → cất trong Chroma. Khi tìm, câu hỏi cũng thành
vector rồi lấy 4 đoạn **gần nghĩa nhất**. Đây là "tìm theo ngữ nghĩa", không phải
tìm theo từ khoá.

---

## 3. Luồng chạy thật của một câu hỏi

Câu hỏi: **"Suggest two Cornwall beach towns with nice weather"**

```
        ┌──────────── HumanMessage: "Suggest two Cornwall beach towns..."
        ▼
   ┌─────────┐   vòng 1: LLM chưa biết thị trấn nào → đòi gọi tool 1
   │ llm_node│ ──────────────► AIMessage(tool_calls=[search_travel_info("beach towns in Cornwall")])
   └─────────┘
        │ tools_condition thấy có tool_calls → rẽ sang "tools"
        ▼
   ┌─────────┐   chạy hàm Python, lấy 4 đoạn văn từ Chroma
   │  tools  │ ──────────────► ToolMessage("...Newquay... St Ives... Falmouth...")
   └─────────┘
        │ quay lại llm_node
        ▼
   ┌─────────┐   vòng 2: đã có tên thị trấn → đòi thời tiết 2 nơi
   │ llm_node│ ──────────────► AIMessage(tool_calls=[weather_forecast("St Ives"),
   └─────────┘                                        weather_forecast("Newquay")])
        │
        ▼
   ┌─────────┐
   │  tools  │ ──────────────► ToolMessage({"town":"St Ives","country":"United Kingdom",
   └─────────┘                              "weather":"clear sky","temperature":12.9,...})
                               ToolMessage({"town":"Newquay",...,"temperature":12.4,...})
        │
        ▼
   ┌─────────┐   vòng 3: Newquay mưa → có thể hỏi thêm thị trấn khác,
   │ llm_node│   hoặc đủ dữ kiện → trả lời chữ, KHÔNG còn tool_calls
   └─────────┘ ──────────────► AIMessage("Two beach towns with nice weather are...")
        │ tools_condition thấy hết tool_calls → END
        ▼
      In ra "Assistant: ..."
```

Khi chạy, mỗi lần tool được gọi console in một dòng `[tool] ...` — đó là bằng chứng
trực quan để thầy thấy agent **thật sự** gọi tool chứ không bịa.

---

## 4. Đọc code `main_02_02.py` theo từng khối

| Dòng/khối | Nội dung | Listing trong sách |
|---|---|---|
| `load_dotenv()` | nạp API key từ `.env` | 11.1 |
| `build_vectorstore()` + `get_travel_info_vectorstore()` | tải Wikivoyage, cắt chunk, embedding, Chroma; singleton | 11.2 |
| `WeatherForecastService` | service thời tiết **giả** của sách (random) | 11.10 |
| `OpenMeteoWeatherService` | service thời tiết **THẬT** (Open-Meteo, không cần key) | mở rộng |
| `@tool search_travel_info` | **tool 1** — tìm ngữ nghĩa | 11.3 |
| `@tool weather_forecast` | **tool 2** — thời tiết theo **thành phố** | 11.7.2 |
| `TOOLS = [...]` + `bind_tools(TOOLS)` | đăng ký tool với LLM | 11.5 + 11.7.3 |
| `class AgentState` | state = danh sách message | 11.2.4 |
| `class ToolsExecutionNode` | node chạy tool (viết tay) | 11.6 |
| `def llm_node` | node LLM + SystemMessage dẫn đường | 11.7 + 11.11 |
| `builder = StateGraph(...)` … `compile()` | lắp đồ thị | 11.8 |
| `chat_loop()` | vòng chat REPL | 11.9 |

`main_03_01.py` = mục 11.9: xoá hết `AgentState` / `ToolsExecutionNode` / `llm_node` /
`StateGraph`, thay bằng **một** lệnh `create_react_agent(model, tools, prompt)`.
Kết quả y hệt, code ngắn hơn ~120 dòng. Nó `import` lại 2 tool từ `main_02_02.py`
để khỏi chép code hai lần.

---

## 5. Câu để thầy prompt (đã chọn sao cho lộ rõ từng tool)

**Chỉ dùng tool 1 (vector store):**
- `Tell me about surfing in Cornwall`
- `What can I do in St Ives?`
- `Suggest three towns with a nice beach in Cornwall`

**Chỉ dùng tool 2 (thời tiết THẬT theo thành phố — dữ liệu Open-Meteo, mọi nơi trên thế giới):**
- `What is the weather in Falmouth, Cornwall right now?`
- `Compare the weather in Newquay and Penzance`
- `So sánh thời tiết Đà Nẵng và Hà Nội hiện tại` (agent trả lời bằng tiếng Việt luôn)

**Dùng cả 2 tool nối tiếp nhau — câu "đắt" nhất để demo:**
- `Suggest two Cornwall beach towns with nice weather`
- `I want a surfing town in Cornwall where it is not raining today`
- `Which Cornwall coastal town should I visit today based on the weather?`

**Câu chứng minh agent không bịa:** hỏi `What is the weather in Hanoi?` → agent vẫn
gọi `weather_forecast(town="Hanoi")` vì tool nhận **bất kỳ** tên thành phố nào.
Còn `Tell me about Paris` → tool 1 tìm trong kho Cornwall, không có dữ liệu →
agent nói không có thông tin. Đó là hành vi **đúng** của RAG.

---

## 6. Thầy hỏi gì — trả lời sao

**Q: Agent khác chatbot thường ở chỗ nào?**
Chatbot chỉ sinh chữ từ kiến thức đã học. Agent có vòng lặp *reason → act*: nó tự
chọn và gọi công cụ bên ngoài, đọc kết quả rồi mới trả lời, nên câu trả lời bám dữ liệu thật.

**Q: LLM biết gọi tool bằng cách nào?**
`bind_tools()` gửi kèm mỗi lượt chat một tờ khai JSON gồm tên + mô tả + schema tham số
của từng tool. Model được huấn luyện để trả về khối `tool_calls` có cấu trúc khi thấy cần.

**Q: Ai thực sự chạy hàm?**
Code mình — `ToolsExecutionNode.__call__`. LLM chỉ *yêu cầu*. Kết quả gói vào
`ToolMessage` kèm `tool_call_id` để ghép đúng cặp yêu cầu–kết quả.

**Q: Vì sao cần conditional edge?**
Vì không biết trước cần mấy vòng tool. `tools_condition` kiểm tra message cuối:
còn `tool_calls` thì quay lại chạy tool, hết thì kết thúc. Đó chính là vòng lặp ReAct.

**Q: Nếu bỏ SystemMessage thì sao?**
Đúng như mục 11.8.1 của sách: LLM bỏ qua tool 1 và **tự bịa** tên thị trấn từ kiến
thức nền (Newquay, Falmouth) rồi chỉ hỏi thời tiết. SystemMessage
*"Only use the tools to find the information you need (including town names)"*
ép nó phải tra vector store trước → chống bịa (hallucination).

**Q: Tại sao chia đoạn 1024 ký tự, chồng lấn 128?**
Đoạn đủ nhỏ để embedding chính xác và tiết kiệm token; chồng lấn để câu bị cắt
ngang biên vẫn còn nguyên ngữ cảnh ở đoạn kế.

**Q: Tool thời tiết là thật hay giả?**
**Thật** — gọi API Open-Meteo (miễn phí, không cần API key): bước 1 geocoding đổi tên
thành phố ra toạ độ, bước 2 lấy thời tiết hiện tại tại toạ độ đó. Đây chính là bài tập
mở rộng cuối mục 11.8 của sách. Bản mock của sách vẫn giữ trong code, bật lại bằng
`WEATHER_MODE=mock` trong `.env`. Điểm đáng nói: đổi từ mock sang API thật **không phải
sửa một dòng nào trong đồ thị** — chỉ thay ruột hàm tool.

**Q: Vì sao tool có thêm tham số `country`?**
Nhiều thành phố trùng tên (Falmouth có ở cả Anh và Mỹ). Tham số thứ hai để LLM tự truyền
quốc gia khi biết, tránh trả nhầm thời tiết. Đây là ví dụ cho nguyên tắc "mô tả tham số
rõ ràng thì LLM điền đúng" ở phần Summary của chương.

**Q: Thêm tool thứ 3 thì phải sửa gì?**
Chỉ thêm một hàm `@tool` và bỏ tên nó vào list `TOOLS`. Đồ thị giữ nguyên.

**Q: State lưu ở đâu, có nhớ giữa các câu hỏi không?**
Trong RAM, mỗi lần `invoke` là một state mới → **không** nhớ câu trước. Muốn nhớ thì
gắn `checkpointer` (MemorySaver) — nằm ngoài phạm vi chương 11.

**Q: `Annotated[..., operator.add]` để làm gì?**
Báo cho LangGraph biết cách gộp giá trị node trả về vào state: với `messages` là
**nối thêm**, mặc định sẽ là ghi đè.

**Q: Chi phí?**
Gemini Flash-Lite + embedding trên Google AI Studio có free tier; mỗi câu hỏi tốn
vài nghìn token. Embedding chỉ chạy một lần rồi cache xuống đĩa.

---

## 7. Khác biệt so với sách (nêu trước, thầy hỏi thì giải thích)

| Sách | Bài này | Lý do |
|---|---|---|
| OpenAI `gpt-5-mini` + `OpenAIEmbeddings` | Gemini `gemini-3.1-flash-lite` + `gemini-embedding-001` | dùng key Google AI Studio sẵn có, có free tier. Giao thức tool calling giống hệt nên code không đổi cấu trúc |
| Chroma dựng lại mỗi lần chạy | Chroma `persist_directory` → cache xuống đĩa | khỏi tải + embedding lại, chạy demo tức thì |
| `AsyncHtmlLoader` (nền aiohttp) + giữ HTML thô | `WebBaseLoader` (nền requests) | Wikimedia **chặn** client aiohttp, trả về trang "robot policy" → kho rỗng. WebBaseLoader tải được và đã bóc sẵn tag HTML |
| Tool thời tiết mock random | Open-Meteo (API thật, không cần key) + giữ mock qua `WEATHER_MODE` | chính là bài tập mở rộng cuối mục 11.8 |
| `SystemMessage` được `append` vào state mỗi vòng | Ghép vào đầu danh sách tạm | cách của sách khiến system message bị lặp lại nhiều lần trong state |
| `async` + `asyncio.run` khi tải trang | Gọi `.load()` đồng bộ | ngắn hơn, kết quả như nhau |

---

## 8. Lỗi hay gặp

| Triệu chứng | Cách xử lý |
|---|---|
| `API key not valid` | Key sai/bị thu hồi → tạo key mới ở AI Studio, dán vào `.env` |
| `404 ... models/... is not found` | Tên model sai → chạy `list_models.py`, sửa `CHAT_MODEL`/`EMBED_MODEL` trong `.env` |
| `429 RESOURCE_EXHAUSTED` | Vượt free tier → chờ ít phút, hoặc đổi sang model lite hơn |
| Kết quả tìm kiếm lạ / rỗng | Xoá thư mục `chroma_travel_info/` rồi chạy lại để dựng kho mới |
| Chạy rất lâu ở lần đầu | Bình thường: đang tải 4 trang web + tạo embedding |
| Tiếng Việt gõ vào bị lỗi font | Chạy `chcp 65001` trong PowerShell trước khi chạy script |
| `Both GOOGLE_API_KEY and GEMINI_API_KEY are set` | Chỉ là thông báo: máy bạn có sẵn biến `GEMINI_API_KEY` cũ (đã chết), thư viện ưu tiên `GOOGLE_API_KEY` trong `.env` nên vẫn đúng |

---

> **Muốn hiểu TOÀN BỘ sản phẩm** (kiến trúc, luồng chạy, vì sao thiết kế vậy, số liệu
> thật, 20 câu phỏng vấn kèm đáp án): đọc [docs/MENTOR.md](docs/MENTOR.md).

## 9. Phần mở rộng (ngoài yêu cầu bài lab — để đưa lên GitHub/CV)

| File | Là gì | Chạy thế nào |
|---|---|---|
| `app.py` | Giao diện web Streamlit, hiện **realtime** từng bước agent gọi tool nào, kết quả gì, mất bao lâu | `venv\Scripts\streamlit.exe run app.py` |
| `api.py` | **HTTP API** cho agent: `POST /chat` trả JSON, `GET /chat/stream` đẩy sự kiện realtime bằng SSE, `/docs` tài liệu tự sinh. Học chi tiết ở [docs/hoc/HOC_FASTAPI_SSE.md](docs/hoc/HOC_FASTAPI_SSE.md) | `venv\Scripts\python.exe api.py` |
| `mcp_server.py` | Đóng gói 2 tool thành **MCP server** chuẩn giao thức — cắm được vào Claude Desktop / Cursor | tự chạy khi client gọi |
| `main_04_mcp.py` | Agent lấy tool **qua giao thức MCP** (2 tiến trình tách rời) thay vì import trực tiếp | `venv\Scripts\python.exe main_04_mcp.py` |
| `evals/eval_agent.py` | Chấm điểm agent: độ chính xác chọn tool + LLM chấm chất lượng trả lời | `venv\Scripts\python.exe evals\eval_agent.py` |
| `tests/test_tools.py` | 7 unit test, **không cần mạng, không cần API key** (giả lập `requests`) | `venv\Scripts\python.exe -m pytest tests -q` |
| `.github/workflows/ci.yml` | GitHub Actions: tự lint + test mỗi lần push | tự động trên GitHub |
| `Dockerfile` + `docker-compose.yml` | Đóng gói chạy bằng Docker: multi-stage, non-root, healthcheck. Học chi tiết ở [docs/hoc/HOC_DOCKER.md](docs/hoc/HOC_DOCKER.md) | `docker compose up --build` |
| `metrics.py` + `monitoring/` | **Prometheus + Grafana**: đo p95 latency, tool nào gọi bao nhiêu lần / lỗi bao nhiêu, token và **chi phí USD**. Học chi tiết ở [docs/hoc/HOC_PROMETHEUS.md](docs/hoc/HOC_PROMETHEUS.md) | dashboard tại http://localhost:3000/d/travel-agent |
| `make_graph_image.py` | Xuất sơ đồ đồ thị agent ra `docs/graph.png` | `venv\Scripts\python.exe make_graph_image.py` |

**Kết quả eval đã đo được:** chọn đúng tool **8/8 (100%)**, LLM chấm chất lượng **4.1/5**,
trung bình 10.4 giây/câu. Số liệu chi tiết trong `evals/results.md`.

### Nếu thầy hỏi về phần MCP
MCP (Model Context Protocol) là chuẩn để agent lấy tool từ **server bên ngoài** thay vì
import trong code. So sánh:

```
main_02_02.py :  agent  --import Python-->      hàm tool        (cùng 1 tiến trình)
main_04_mcp.py:  agent  --JSON-RPC qua stdio--> mcp_server.py   (2 tiến trình rời nhau)
```

Lợi ích: đổi server (viết ngôn ngữ khác, chạy máy khác) mà **không sửa dòng nào** ở agent;
và bất kỳ ứng dụng nào nói được MCP đều dùng lại được 2 tool này. Chi tiết chuẩn giao thức
là chương sau của sách — bài này đã làm trước một bước.

Một chi tiết kỹ thuật đáng nói: MCP trên stdio dùng **stdout để truyền JSON-RPC**, nên mọi
lệnh `print` lọt vào stdout sẽ làm hỏng kết nối. Trong `mcp_server.py` phải chuyển hướng
log lúc import sang stderr.

---

## 10. Đưa lên GitHub và commit các ngày sau

### 10.1 Nguyên tắc số một: KHÔNG BAO GIỜ push file `.env`
Key Google cũ của bạn đã bị thu hồi — key bị lộ công khai thường bị Google vô hiệu hoá tự
động. Repo này đã có `.gitignore` loại trừ `.env`, và có `.env.example` (không chứa key
thật) để người khác biết cần điền gì. **Kiểm tra trước mỗi lần push:**

```bash
git status --short
```

Nếu thấy dòng nào có `.env` (không phải `.env.example`) → dừng lại, đừng commit.
Lỡ push key rồi thì vào https://aistudio.google.com/app/apikey xoá key đó và tạo key mới —
xoá commit **không đủ**, key vẫn nằm trong lịch sử.

### 10.2 Lần đầu đưa lên GitHub
1. Vào https://github.com/new → đặt tên repo `travel-ai-agent` →
   **KHÔNG** tích "Add a README file" / "Add .gitignore" / "Choose a license"
   (repo đã có sẵn nội dung, tích vào sẽ xung đột khi push).
2. Chạy các lệnh sau:

```bash
cd D:\langgraph-agent-lab
git remote add origin https://github.com/Hieuxuan1112/travel-ai-agent.git
git branch -M main
git push -u origin main
```

3. Nếu tài khoản GitHub của bạn KHÔNG phải `Hieuxuan1112`, sửa lại tên đó trong
   `README.md` (badge CI + link clone) và trong lệnh `git remote add` ở trên.
4. Vào tab **Actions** trên GitHub xem CI chạy — badge xanh là đẹp hồ sơ.

### 10.3 Các ngày sau: thêm tính năng / sửa lỗi
```bash
cd D:\langgraph-agent-lab
git status                      # xem đã sửa gì
git add .
git commit -m "feat: them tool tra cuu tau hoa"
git push
```

Quy ước đặt tên commit (nhà tuyển dụng nhìn lịch sử commit sẽ đánh giá):
`feat:` tính năng mới · `fix:` sửa lỗi · `docs:` sửa tài liệu · `test:` thêm test ·
`refactor:` dọn code · `chore:` việc lặt vặt (đổi version, config).

Với tính năng lớn, làm trên nhánh riêng rồi mở Pull Request — CI sẽ chạy trên PR, trông
rất chuyên nghiệp:

```bash
git checkout -b feat/hotel-search
git add . ; git commit -m "feat: them tool tim khach san"
git push -u origin feat/hotel-search
```

### 10.4 Trước khi push, chạy đúng những gì CI sẽ chạy
```bash
venv\Scripts\python.exe -m ruff check .
venv\Scripts\python.exe -m pytest tests -q
```
Sạch cả hai thì CI trên GitHub cũng sẽ xanh.

### 10.5 Nên bổ sung dần để repo càng "nặng ký"
1. **Ảnh chụp giao diện** — chạy `streamlit run app.py`, chụp màn hình lưu vào
   `docs/screenshot.png`, chèn vào README ngay dưới tiêu đề. Đây là thứ người xem nhìn đầu tiên.
2. **Tool thứ 3** (khách sạn, tàu xe, tỉ giá) — chỉ cần thêm một hàm `@tool` và một dòng
   trong `TOOLS`, rồi thêm case vào `evals/eval_agent.py` để chứng minh không làm tệ đi.
3. **Trí nhớ hội thoại** bằng checkpointer SQLite → agent nhớ được nhiều lượt.
4. **Hybrid search** (BM25 + vector) và trích dẫn nguồn trong câu trả lời.
5. **LangSmith tracing** (mục 11.9.3) — chụp ảnh trace đưa vào README.
