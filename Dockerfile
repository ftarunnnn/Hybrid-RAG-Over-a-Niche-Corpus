# Production Multi-Stage Dockerfile
FROM python:3.11-slim as base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

# Install system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application codebase
COPY . .

# Run ingestion and pre-indexing on build
RUN python scripts/ingest_corpus.py && \
    python scripts/chunk_corpus.py && \
    python scripts/index_bm25.py && \
    python scripts/index_vectors.py

EXPOSE 8000 8501

# Healthcheck definition
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Default startup command (FastAPI backend)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
