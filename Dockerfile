FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Pass your key at run time:
#   docker build -t travel-agent .
#   docker run -p 8000:8000 -e GOOGLE_API_KEY=your-key travel-agent
#
# ${PORT:-8000}: Cloud Run injects the port to listen on via $PORT, so the shell
# form is required here - the exec form would not expand the variable.
CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000}"]

# To run the Streamlit UI in the container instead:
#   docker run -p 8501:8501 -e GOOGLE_API_KEY=your-key travel-agent \
#     streamlit run app.py --server.port=8501 --server.address=0.0.0.0
