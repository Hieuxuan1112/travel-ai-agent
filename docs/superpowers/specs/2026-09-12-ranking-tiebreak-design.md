# Thiết kế: composite score + tie-break cho lựa chọn town

Ngày: 2026-09-12. Vá đúng câu hỏi CTO đã vấp khi phỏng vấn: "sao chọn đúng 2 town
này, lỡ cả 2 thời tiết xấu thì sao?" — hiện agent chọn town hoàn toàn theo phán
đoán tự do của LLM, không có tiêu chí tường minh nào để trả lời.

## Vấn đề

`main_02_02.py` hiện có 2 tool (`search_travel_info`, `weather_forecast`).
Khi user hỏi kiểu "gợi ý 2 town có thời tiết đẹp", agent tự đọc kết quả RAG,
tự chọn vài town, tự gọi `weather_forecast` cho từng town, rồi tự viết câu trả
lời — toàn bộ bước "chọn town nào" nằm trong suy luận ngôn ngữ tự nhiên của
LLM, không có công thức, không có ngưỡng, không có fallback tường minh nào
trong code. Không unit-test được, không giải thích được khi bị hỏi vặn.

Ràng buộc quan trọng phát hiện khi đọc code: kho vector chỉ có 4 trang
Wikivoyage theo VÙNG (Cornwall, North/South/West Cornwall), cắt thành ~92
chunk. Một chunk có thể nhắc nhiều town hoặc không town nào — không có sẵn
"điểm relevance của một town cụ thể". Điểm relevance phải được tính thêm,
không lấy free từ pipeline retrieval hiện tại.

## Giải pháp

Thêm tool thứ ba **`rank_town_candidates`** vào `main_02_02.py` (tự động có ở
`main_03_01.py` vì file đó import `TOOLS` từ đây). Toàn bộ phép tính là Python
thuần, không gọi LLM — unit-test được không cần network/API key.

### Chữ ký tool

```python
@tool
def rank_town_candidates(
    towns: list[str],
    country: str = "",
    min_temp_c: float = 15.0,
    max_temp_c: float = 25.0,
    min_weather_fit: float = 0.5,
    top_n: int = 2,
) -> dict:
    ...
```

`min_temp_c`/`max_temp_c` cho LLM truyền vào khi user nói rõ mong muốn (vd
"dưới 15 độ"); không nói gì thì dùng mặc định 15–25°C.

**Đổi so với bản thiết kế ban đầu** (phát hiện khi chạy thật, không phải đoán
trước): thiết kế đầu tiên nhận `candidates: list[{town, weather}]` — tức LLM
phải tự relay lại nguyên dict thời tiết đã nhận từ `weather_forecast` ở lượt
gọi trước. Chạy `evals/eval_agent.py` thật thì thấy Gemini thường xuyên KHÔNG
relay đúng (vd chỉ gửi `"weather": "overcast"` thay vì cả dict), gây lỗi
validate Pydantic ở mọi lần thử kể cả sau retry (temperature=0 nên lỗi lặp lại
y hệt). Sửa bằng cách để `rank_town_candidates` tự gọi `weather_forecast` bên
trong cho từng town trong `towns` — bỏ hẳn việc bắt LLM chuyển tiếp object
lồng nhau giữa các lượt gọi tool, loại bỏ nguồn lỗi thay vì cố retry quanh nó.
Công thức điểm (bên dưới) không đổi, chỉ đổi cách candidate lấy được `weather`.

### Công thức điểm

- **relevance** = `1 / (1 + distance)`, với `distance` lấy từ
  `vectorstore.similarity_search_with_score(town, k=1)` — truy vấn lại kho
  vector bằng chính tên town. Đây là "tên town này khớp với kho tài liệu đến
  đâu", KHÔNG phải "độ khớp với câu hỏi gốc của user" — ghi rõ trong docstring
  để không phóng đại. Dùng biến đổi đơn điệu `1/(1+d)` để không phải giả định
  Chroma dùng metric nào (L2 hay cosine).
- **temp_score** = 1.0 nếu nhiệt độ nằm trong `[min_temp_c, max_temp_c]`,
  giảm tuyến tính về 0 trên biên độ 5°C ngoài khoảng, 0 nếu xa hơn nữa.
- **condition_score** = 0.0 nếu điều kiện thời tiết chứa
  rain/drizzle/storm/thunderstorm/snow hoặc `precipitation_mm > 0.5`; ngược
  lại 1.0.
- **weather_fit** = `0.5 * temp_score + 0.5 * condition_score`.
- **composite** = `0.4 * relevance + 0.6 * weather_fit` (weather-fit nặng hơn
  vì đó là trọng tâm câu hỏi CTO).

### Ngưỡng + fallback

- Chỉ những candidate có `weather_fit >= min_weather_fit` (mặc định 0.5) mới
  được coi là "đạt".
- Nếu số candidate đạt ngưỡng >= `top_n`: trả về top `top_n` theo `composite`,
  `"relaxed": false`.
- Nếu ít hơn `top_n` candidate đạt ngưỡng: nới ngưỡng, trả về top `top_n` theo
  `weather_fit` bất kể ngưỡng, kèm `"relaxed": true` và một câu lý do bằng
  tiếng Anh mà agent có thể trích thẳng vào câu trả lời, ví dụ:
  `"No candidate scored above the weather-fit threshold; showing the {top_n}
  best available options instead."`

### Output

```python
{
  "ranked": [
    {"town": "St Ives", "relevance": 0.83, "weather_fit": 0.90, "composite": 0.87},
    ...
  ],
  "relaxed": false,
  "relax_reason": None,
}
```

### Thay đổi kèm theo

- `SYSTEM_PROMPT`: thêm một câu hướng dẫn — khi cần so sánh/chọn giữa ≥2 town
  theo thời tiết, gọi thẳng `rank_town_candidates` với tên các town (tool tự
  lấy thời tiết, không cần gọi `weather_forecast` riêng trước); nếu
  `relaxed=true` phải nói rõ cho user là đã nới điều kiện.
- `mcp_server.py`: thêm wrapper cho tool mới, cùng kiểu với 2 tool hiện có, để
  MCP client cũng gọi được (nhất quán, không để MCP surface bị thiếu 1 tool).
- KHÔNG đổi cấu trúc graph (`llm_node`, `tools_execution_node`,
  `route_after_llm`) — tool mới đi qua đúng con đường hiện có
  (`ToolsExecutionNode` đã tổng quát cho mọi tool trong `TOOLS`).

## Testing

- Unit test thuần cho hàm tính điểm (không qua tool-call, không gọi API):
  temp trong khoảng, ngoài khoảng, mưa, không mưa, trường hợp nới ngưỡng.
- 1 test case tích hợp trong `evals/eval_agent.py`: câu hỏi ép fallback (yêu
  cầu một khoảng nhiệt độ mà Cornwall khó đạt) để chứng minh agent nói rõ đã
  nới điều kiện thay vì im lặng chọn đại.
- Không đổi `MAX_TOOL_CALLS` mặc định (8) — 1 tool call thêm vẫn nằm trong
  ngân sách của các câu hỏi so sánh nhiều town hiện tại.

## Rủi ro / đánh đổi đã chấp nhận

- `relevance` là proxy (tên town khớp kho tài liệu), không phải "độ khớp với
  câu hỏi user" đúng nghĩa — chấp nhận vì kho hiện tại không có cấu trúc
  per-town để tính chính xác hơn mà không viết lại toàn bộ retrieval.
  Trọng số 0.4 phản ánh đúng việc tín hiệu này yếu hơn weather-fit.
- Thêm 1 lần gọi vector store mỗi candidate (re-query bằng tên town) — chi phí
  nhỏ (không gọi LLM), chấp nhận được ở quy mô demo này.
