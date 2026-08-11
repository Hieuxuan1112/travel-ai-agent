FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

# Pass your key at run time:
#   docker build -t travel-agent .
#   docker run -p 8501:8501 -e GOOGLE_API_KEY=your-key travel-agent
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
