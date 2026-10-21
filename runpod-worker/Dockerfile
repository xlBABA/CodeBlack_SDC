# RunPod Serverless worker for skill embeddings (all-MiniLM-L6-v2).
# Build from this folder:  docker build -t <you>/futurepath-embeddings:1 runpod-worker
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    HF_HOME=/models

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download the model at build time so cold starts do not fetch it.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
# From here on the worker must use the baked-in copy and never reach out to the Hub.
ENV HF_HUB_OFFLINE=1

COPY handler.py .
CMD ["python", "-u", "handler.py"]
