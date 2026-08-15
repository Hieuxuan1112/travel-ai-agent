# syntax=docker/dockerfile:1
#
# Multi-stage build: BUILDER cai thu vien, RUNTIME chi nhan ket qua.
# Loi ich: anh cuoi khong chua pip cache / cong cu bien dich, va sua code thi
# khong phai cai lai thu vien (Docker dung lai layer cu).

# ============================ Stage 1: builder =============================
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Cai vao mot virtualenv rieng -> stage sau chi viec COPY dung /opt/venv.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# COPY rieng requirements.txt TRUOC khi copy code: chung nao file nay khong doi
# thi Docker dung lai layer da cai san -> rebuild sau khi sua code chi mat vai giay.
COPY requirements.txt .
RUN pip install -r requirements.txt

# ============================ Stage 2: runtime =============================
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"
# PYTHONUNBUFFERED=1 rat quan trong o day: khong co no, Python gom log vao buffer
# -> log khong hien kip va luong SSE bi giu lai, mat tinh realtime.

COPY --from=builder /opt/venv /opt/venv

# Chay bang user thuong, khong phai root: neu ai do chiem duoc tien trinh thi
# ho khong co quyen root trong container. Deploy that cho nao cung yeu cau dieu nay.
RUN useradd --create-home --uid 1000 appuser

WORKDIR /app
COPY --chown=appuser:appuser . .

# Thu muc vector store phai thuoc ve appuser thi container moi ghi duoc vao day.
RUN mkdir -p /app/chroma_travel_info && chown appuser:appuser /app/chroma_travel_info

USER appuser

EXPOSE 8000

# Docker tu goi /healthz de biet container song hay chet.
# start-period dai vi lan chay dau con phai tai trang web va tao embedding.
HEALTHCHECK --interval=30s --timeout=5s --start-period=180s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz')"

# Dang shell de ${PORT} duoc thay the: Cloud Run bao cong can nghe qua bien nay.
CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000}"]

# Chay thu:
#   docker build -t travel-ai-agent .
#   docker run -p 8000:8000 -e GOOGLE_API_KEY=your-key travel-ai-agent
#
# Chay giao dien Streamlit tu chinh anh nay:
#   docker run -p 8501:8501 -e GOOGLE_API_KEY=your-key travel-ai-agent \
#     streamlit run app.py --server.port=8501 --server.address=0.0.0.0
