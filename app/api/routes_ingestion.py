"""
Ingestion API routes.
Allows triggering full corpus re-indexing or file uploads.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pathlib import Path
import json

from app.ingestion.pipeline import IngestionPipeline
from app.ingestion.chunker import HeadingAwareChunker
from app.retrieval.vector_search import QdrantVectorStore
from app.retrieval.bm25 import TechnicalBM25Retriever
from app.config import settings

router = APIRouter(tags=["Ingestion"])


def _run_full_ingestion():
    # 1. Pipeline
    pipe = IngestionPipeline()
    docs = pipe.ingest_directory()

    # 2. Chunker
    chunker = HeadingAwareChunker()
    chunks = chunker.chunk_corpus(docs)
    chunks_path = Path("data/processed/chunks.json")
    chunks_path.parent.mkdir(parents=True, exist_ok=True)
    with open(chunks_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)

    # 3. Vector indexing
    store = QdrantVectorStore(
        collection_name=settings.QDRANT_COLLECTION,
        location=settings.QDRANT_LOCATION
    )
    store.index_chunks(chunks)

    # 4. BM25 indexing
    bm25 = TechnicalBM25Retriever()
    bm25.fit(chunks)
    bm25.save(settings.BM25_INDEX_PATH)


@router.post("/ingest")
def trigger_ingestion(background_tasks: BackgroundTasks):
    """Triggers end-to-end ingestion and indexing across Qdrant and BM25."""
    background_tasks.add_task(_run_full_ingestion)
    return {
        "status": "triggered",
        "message": "Ingestion pipeline launched in background."
    }
