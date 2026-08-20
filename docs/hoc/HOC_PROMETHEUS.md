# Học Prometheus + Grafana qua chính project này

File liên quan: [`metrics.py`](../../metrics.py), [`api.py`](../../api.py),
[`monitoring/`](../../monitoring), [`docker-compose.yml`](../../docker-compose.yml).

---

## 1. Vì sao đo, và đo cái gì mới đáng

Đo CPU/RAM thì ai cũng đo được và chẳng nói lên gì về một hệ thống LLM. Với agent,
ba câu hỏi thực sự quan trọng là:

1. **Chậm ở đâu?** — request tốn bao lâu, tool nào chậm nhất
2. **Hỏng ở đâu?** — tool nào hay lỗi, request nào thất bại
3. **Tốn bao nhiêu tiền?** — token và chi phí, thứ mà chỉ hệ thống LLM mới có

Đây là điểm phân biệt người "biết gắn Prometheus" với người "biết đo cái gì".

## 2. Prometheus hoạt động thế nào

Khác với hình dung thông thường, **Prometheus không nhận dữ liệu — nó chủ động đi lấy**:

```
                 mỗi 15 giây
  Prometheus  ─────GET /metrics────>  API của bạn
      │                                (trả về text thuần)
      ▼
  lưu theo thời gian
      │
      ▼
  Grafana truy vấn bằng PromQL để vẽ
```

Ứng dụng của bạn chỉ cần làm đúng một việc: mở endpoint `/metrics` trả về text theo
định dạng quy ước. Mở http://localhost:8000/metrics bằng trình duyệt sẽ thấy:

```
# HELP agent_tool_calls_total So lan tung tool duoc goi
# TYPE agent_tool_calls_total counter
agent_tool_calls_total{tool="weather_forecast"} 6.0
agent_tool_calls_total{tool="search_travel_info"} 2.0
```

Ba phần: **tên chỉ số**, **nhãn** trong `{}`, và **giá trị**. Chỉ vậy thôi.

## 3. Bốn loại thuốc đo — chọn đúng loại là nửa phần thắng lợi

| Loại | Đặc điểm | Dùng cho | Trong project |
|---|---|---|---|
| **Counter** | chỉ tăng, không bao giờ giảm | đếm số lần, cộng dồn | `agent_requests_total`, `agent_llm_tokens_total`, `agent_llm_cost_usd_total` |
| **Gauge** | lên xuống tuỳ ý | giá trị tức thời | `agent_requests_in_flight` |
| **Histogram** | chia giá trị vào các "rổ" | thời gian, kích thước → tính p50/p95/p99 | `agent_request_duration_seconds` |
| **Summary** | ít dùng | — | không dùng |

**Vì sao Counter chỉ tăng mà vẫn dùng được?** Vì Prometheus lưu theo thời gian, nên
`rate(counter[5m])` cho ra "bao nhiêu lần mỗi giây trong 5 phút qua". Số tuyệt đối không
quan trọng bằng tốc độ thay đổi.

**Vì sao phải tự đặt buckets cho Histogram?**

```python
REQUEST_DURATION = Histogram(..., buckets=(0.5, 1, 2, 5, 8, 12, 20, 30, 60))
```

Buckets mặc định của Prometheus dừng ở 10 giây — hợp với web thường. Agent này chạy
5–20 giây, dùng mặc định thì gần như mọi request rơi vào rổ cuối `+Inf` và **p95 trở nên
vô nghĩa**. Đây là lỗi rất hay gặp khi đo hệ thống LLM.

## 4. Đo p95 chứ đừng đo trung bình

Trung bình che giấu thảm hoạ: 99 request 2 giây + 1 request 60 giây → trung bình 2,6
giây, nghe ổn, nhưng có người thật đã chờ một phút. **p95 = 95% người dùng được phục vụ
nhanh hơn con số này** — đó mới là thứ phản ánh trải nghiệm.

Công thức PromQL để lấy p95 từ histogram:

```promql
histogram_quantile(0.95, sum(rate(agent_request_duration_seconds_bucket[5m])) by (le))
```

Đọc từ trong ra: `rate(..._bucket[5m])` tốc độ tăng của từng rổ → `sum by (le)` gộp các
instance lại nhưng **giữ nhãn `le`** (le = "less than or equal", tên rổ) → `histogram_quantile`
nội suy ra phân vị. Nhớ: **luôn phải `by (le)`**, quên là sai.

Kết quả đo thật của project: **p95 = 7,55 giây**.

## 5. Tính tiền — thứ chỉ hệ thống LLM mới có

```python
LLM_TOKENS.labels(model=model, kind="input").inc(input_tokens)
price = PRICE_PER_1M_TOKENS.get(model)
if price:
    cost = (input_tokens * price[0] + output_tokens * price[1]) / 1_000_000
    LLM_COST.labels(model=model).inc(cost)
```

Số token lấy từ `AIMessage.usage_metadata` của LangChain. Hai điểm tinh tế:

- **Mỗi vòng ReAct là một lần gọi model.** Một câu hỏi gọi 3 tool sẽ tính tiền 4 lần
  chứ không phải 1. Nếu chỉ đo ở tầng request thì bạn sẽ hiểu sai chi phí thật.
- **Model lạ không có trong bảng giá thì chỉ đếm token, không bịa ra tiền.** Có test
  riêng cho điều này.

Đo thật: **$0,0035 cho 5 request** ≈ $0,0007/câu ≈ **$0,7 cho 1000 câu**.

## 6. Đặt điểm ghi số ở đâu

| Ghi ở đâu | Đo được gì | Vì sao phải ở đó |
|---|---|---|
| `api.py` — endpoint | số request, thời gian, đang chạy bao nhiêu | tầng ngoài cùng, biết một request bắt đầu và kết thúc khi nào |
| `main_02_02.py` — `ToolsExecutionNode` | tool nào, bao lâu, lỗi không | chỉ chỗ này mới biết từng tool chạy hết bao lâu |
| `main_02_02.py` — `llm_node` | token, tiền | mỗi vòng ReAct đi qua đây |

Một chi tiết đáng học trong `agent_events()`:

```python
finally:
    metrics.IN_FLIGHT.dec()
    metrics.REQUEST_DURATION...observe(...)
```

Dùng `finally` vì client có thể **ngắt kết nối giữa chừng** — generator bị đóng, và nếu
không có `finally` thì `IN_FLIGHT` sẽ tăng mãi không giảm, dashboard hiện sai vĩnh viễn.

Một chi tiết nữa: tool của project **không ném exception** mà trả `dict` có khoá `error`
(để LLM tự xử lý), nên đếm lỗi phải theo kiểu đó:

```python
if isinstance(result, dict) and "error" in result:
    metrics.TOOL_ERRORS.labels(tool=tool_name).inc()
```

## 7. Grafana và "provisioning"

Nếu cấu hình Grafana bằng tay trên giao diện, người khác clone repo về sẽ có Grafana
trống trơn. **Provisioning** = khai báo bằng file, bật lên là có sẵn:

```
monitoring/grafana/provisioning/datasources/prometheus.yml   → nguồn dữ liệu
monitoring/grafana/provisioning/dashboards/default.yml       → chỉ chỗ chứa dashboard
monitoring/grafana/dashboards/agent.json                     → dashboard
```

Hai cái bẫy đã gặp thật khi làm:

1. **Datasource phải có `uid` cố định.** Không đặt thì Grafana tự sinh uid ngẫu nhiên,
   còn dashboard JSON lại trỏ tới một uid cụ thể → panel trắng trơn.
2. **Mỗi panel phải có `"id"` riêng.** Thiếu id, Grafana 12 nạp dashboard thành công,
   không báo lỗi gì, nhưng **không vẽ panel nào cả**. Mất thời gian nhất là loại lỗi
   im lặng như thế này.

Ngoài ra `noValue: "0"` cho các panel dạng stat: counter chưa tăng lần nào thì Prometheus
không có chuỗi dữ liệu, Grafana hiện "No data" — trong khi với bộ đếm, không có dữ liệu
nghĩa là 0.

## 8. Xem tận mắt

```bash
docker compose up -d --build
```

| Địa chỉ | Xem gì |
|---|---|
| http://localhost:8000/metrics | text thô Prometheus đọc |
| http://localhost:9090/targets | Prometheus có hút được API không (phải thấy `up`) |
| http://localhost:9090 | gõ thử PromQL, ví dụ `sum(agent_llm_cost_usd_total)` |
| http://localhost:3000/d/travel-agent | dashboard Grafana (vào thẳng, không cần đăng nhập) |

Hỏi vài câu ở http://localhost:8000 rồi quay lại dashboard, đợi 15–30 giây sẽ thấy số nhảy.

## 9. Trả lời phỏng vấn

**"Prometheus push hay pull?"**
Pull. Prometheus chủ động gọi `/metrics` theo chu kỳ. Ưu điểm: ứng dụng không cần biết
gì về hệ thống giám sát, và bản thân việc scrape thất bại đã là một tín hiệu (target down).
Job chạy ngắn không kịp bị scrape thì mới cần Pushgateway.

**"Counter với Gauge khác nhau chỗ nào?"**
Counter chỉ tăng, hỏi nó bằng `rate()` để ra tốc độ. Gauge lên xuống, đọc thẳng giá trị
hiện tại. Đếm request là Counter; số request đang chạy là Gauge.

**"Vì sao p95 chứ không phải trung bình?"**
Trung bình bị các giá trị cực đoan che lấp. p95 mô tả trải nghiệm của gần như tất cả
người dùng, và là thứ đặt SLO lên được.

**"Đo gì cho một hệ thống LLM mà hệ thống thường không có?"**
Token vào/ra, chi phí quy ra tiền, số vòng gọi tool mỗi câu hỏi, tỉ lệ tool lỗi, và
chất lượng câu trả lời qua eval. Chi phí là thứ khác biệt lớn nhất — LLM là hạ tầng
tính tiền theo từng lần gọi.

**"Nhiều worker thì bộ đếm có sai không?"**
Có. Mỗi tiến trình có bộ đếm riêng nên Prometheus scrape trúng worker nào thì thấy số
của worker đó. Phải dùng chế độ multiprocess qua `PROMETHEUS_MULTIPROC_DIR` —
`build_registry()` trong `metrics.py` đã xử lý sẵn trường hợp này.
