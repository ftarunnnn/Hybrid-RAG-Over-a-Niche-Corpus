"""
Health and readiness API routes.
"""
from fastapi import APIRouter
from app.config import settings
from pathlib import Path

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    """Returns application health and indexing status."""
    bm25_exists = Path(settings.BM25_INDEX_PATH).exists()
    chunks_exist = Path("data/processed/chunks.json").exists()

    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "qdrant_collection": settings.QDRANT_COLLECTION,
        "bm25_index_ready": bm25_exists,
        "corpus_chunks_ready": chunks_exist
    }
