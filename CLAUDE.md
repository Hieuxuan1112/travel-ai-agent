# CLAUDE.md — Multi-Tool AI Agent (Cornwall Travel Agent)

**Đọc [`HANDOFF.md`](HANDOFF.md) trước tiên** — việc còn dở và bối cảnh phiên gần nhất.

## Dự án là gì

Agent ReAct hai tool, dùng làm **dự án chủ lực trên CV** của một sinh viên sắp ra
trường đang apply vị trí AI Engineer fresher. Mọi quyết định kỹ thuật phục vụ hai mục
tiêu: (1) chạy thật, kiểm chứng được; (2) **user giải thích được khi phỏng vấn**.

- `search_travel_info` — RAG trên Wikivoyage (Chroma)
- `weather_forecast` — thời tiết thật, Open-Meteo

## Bản đồ file

| File | Vai trò |
|---|---|
| `main_02_02.py` | State graph LangGraph tự nối tay (bản chính để học) |
| `main_03_01.py` | Bản prebuilt ReAct — cùng tool, ít code hơn |
| `main_04_mcp.py`, `mcp_server.py` | Cùng bộ tool phơi qua MCP |
| `app.py` | Streamlit UI, có checkpointer + thread_id trên URL |
| `api.py` | FastAPI, có SSE streaming, rate limit, `/healthz` |
| `persistence.py` | Chọn checkpointer: có `DATABASE_URL` thì Postgres, không thì in-memory |
| `retrieval.py` | Vector search, có BM25+RRF (tắt mặc định — đo thấy không lợi) |
| `metrics.py` | Prometheus: p95, lỗi theo tool, token, cost/query |
| `evals/` | `eval_agent.py` (8 case), `eval_retrieval.py` (12 case), `compare_models.py` |
| `docs/MENTOR.md` | Sản phẩm chạy thế nào |
| `docs/DEPLOY.md` | Hạ tầng: Docker, CD, Azure |
| `docs/hoc/` | 10 tài liệu học + 4 demo chạy được |

## Quyết định đã chốt — đừng lật lại nếu không được yêu cầu

- **BM25+RRF để TẮT mặc định.** Đã đo: không cải thiện ở cỡ corpus này. Giữ code lại
  để nói được là đã thử và đã đo.
- **Nội dung web lấy về bị rào là `<untrusted_documents>`.** Có test chứng minh chỉ
  thị chèn vào bị bỏ qua. Đừng gỡ rào này.
- **Trivy quét TRƯỚC khi đẩy image**, và chỉ chặn CRITICAL **có bản vá**
  (`ignore-unfixed: true`) để cổng không bị nhờn.
- **Deploy dùng tag SHA, không dùng `latest`.**
- **Azure: `min-replicas 0`** để $0/tháng; environment tạo với
  `--logs-destination none` (Log Analytics bị chặn cho subscription sinh viên).
  Region `japaneast` — 8 region khác đã bị từ chối.
- **Contributor gán ở mức resource group**, không phải subscription.

## Quy tắc làm việc

1. **Không ghi lên CV thứ chưa kiểm chứng được.** Mỗi con số phải chỉ về một file
   trong repo hoặc một lần chạy thật. Số sai trên CV quay ra hại user.
2. **Kiểm link deploy bằng trình duyệt, không tin HTTP status.** Streamlit Cloud là
   SPA, trả 200 cho cả trang lỗi lẫn app của người khác. Dấu hiệu đáng tin duy nhất
   là dòng "Created by ...".
3. **Đọc kỹ thông báo lỗi trước khi dựng giả thuyết.** Đã mất 2 lần deploy vì thấy
   chữ "region" là đi đổi region, trong khi trường `Target:` đã chỉ đích danh Log
   Analytics workspace.
4. **Lệnh hạ tầng thì tách nhỏ.** Một lệnh `az` ôm nhiều tham số trả về
   `InternalServerError` không nói gì; ba lệnh nhỏ thì lỗi tự khai ra ở đâu.
5. Tài liệu viết **tiếng Việt**, giọng giải thích cho người tự học, có mục "trả lời
   phỏng vấn" ở cuối.
6. Commit message viết **tiếng Anh**, nhiều đoạn `-m`, giải thích *vì sao* chứ không
   phải *làm gì*.
7. Hỏi trước khi code nếu yêu cầu mơ hồ. Thay đổi tối giản, đúng chỗ cần.

## Lệnh hay dùng

```bash
venv\Scripts\python.exe -m pytest -q              # 56 test
venv\Scripts\python.exe -m evals.eval_agent       # eval, ghi evals/results.md
venv\Scripts\streamlit.exe run app.py             # UI
venv\Scripts\python.exe -m uvicorn api:app --reload
```

## Đang chạy ở đâu

- Streamlit: https://cornwall-travel-agent.streamlit.app
- API Azure: https://travel-agent-api.nicewave-bb4d94a1.japaneast.azurecontainerapps.io/docs
- Image: `ghcr.io/hieuxuan1112/travel-ai-agent` (public, tag theo SHA)
