"""
Qdrant Vector Search Engine.
Handles collection creation, vector indexing, payload storage,
nearest-neighbor similarity search (Cosine), and metadata filtering.
"""
from typing import List, Dict, Any, Optional
import qdrant_client
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue
)
from app.retrieval.embeddings import DenseEmbeddingEngine
import logging

logger = logging.getLogger("vector_search")


class QdrantVectorStore:
    """Manages Qdrant collections and vector similarity retrieval."""

    def __init__(self, collection_name: str = "networking_corpus",
                 location: str = ":memory:",
                 embedder: Optional[DenseEmbeddingEngine] = None):
        self.collection_name = collection_name
        self.embedder = embedder or DenseEmbeddingEngine()
        self.dim = self.embedder.vector_dim
        
        # Connect to Qdrant (in-memory, local path, or remote URL)
        if location.startswith("http"):
            self.client = qdrant_client.QdrantClient(url=location)
        elif location == ":memory:":
            self.client = qdrant_client.QdrantClient(location=":memory:")
        else:
            self.client = qdrant_client.QdrantClient(path=location)

        self._ensure_collection()

    def _ensure_collection(self):
        """Creates collection if it does not already exist."""
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection_name not in collections:
            logger.info(f"Creating Qdrant collection: {self.collection_name} (dim={self.dim})")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.dim, distance=Distance.COSINE)
            )

    def index_chunks(self, chunks: List[Dict[str, Any]], batch_size: int = 64) -> int:
        """Embeds and indexes chunks into the Qdrant collection."""
        total = len(chunks)
        logger.info(f"Indexing {total} chunks into Qdrant...")

        for i in range(0, total, batch_size):
            batch = chunks[i:i + batch_size]
            texts = [f"{c.get('title', '')} - {c.get('section', '')}: {c.get('content', '')}" for c in batch]
            embeddings = self.embedder.embed_batch(texts)

            points = []
            for idx, (chunk, emb) in enumerate(zip(batch, embeddings)):
                point_id = i + idx
                point = PointStruct(
                    id=point_id,
                    vector=emb,
                    payload={
                        "chunk_id": chunk["chunk_id"],
                        "doc_id": chunk["doc_id"],
                        "title": chunk.get("title", ""),
                        "topic": chunk.get("topic", ""),
                        "section": chunk.get("section", ""),
                        "content": chunk["content"],
                        "token_count": chunk.get("token_count", 0),
                        "source_url": chunk.get("source_url", ""),
                        "version": chunk.get("version", "")
                    }
                )
                points.append(point)

            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )

        logger.info(f"Successfully indexed {total} points in Qdrant collection '{self.collection_name}'.")
        return total

    def search(self, query: str, top_k: int = 5,
               topic_filter: Optional[str] = None,
               doc_id_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Performs nearest-neighbor vector similarity search with optional metadata filters."""
        query_vector = self.embedder.embed_query(query)

        # Build filter if requested
        query_filter = None
        must_conditions = []
        if topic_filter:
            must_conditions.append(
                FieldCondition(key="topic", match=MatchValue(value=topic_filter))
            )
        if doc_id_filter:
            must_conditions.append(
                FieldCondition(key="doc_id", match=MatchValue(value=doc_id_filter))
            )
        if must_conditions:
            query_filter = Filter(must=must_conditions)

        # Use query_points for qdrant-client >= 1.10
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
            query_filter=query_filter
        )

        results = []
        for point in response.points:
            score = float(point.score) if point.score is not None else 0.0
            payload = point.payload or {}
            results.append({
                "chunk_id": payload.get("chunk_id", f"point_{point.id}"),
                "doc_id": payload.get("doc_id", ""),
                "title": payload.get("title", ""),
                "topic": payload.get("topic", ""),
                "section": payload.get("section", ""),
                "content": payload.get("content", ""),
                "source_url": payload.get("source_url", ""),
                "token_count": payload.get("token_count", 0),
                "score": score,
                "retriever": "vector"
            })
        return results

    def count(self) -> int:
        """Returns total vectors stored in the collection."""
        res = self.client.count(collection_name=self.collection_name)
        return res.count
