"""
Hybrid Retrieval Fusion Engine.
Implements Reciprocal Rank Fusion (RRF) to merge keyword (BM25) and semantic (Vector) search.
RRF(d) = sum_{r in R} (w_r / (k + rank_r(d)))
Preserves individual retriever scores and rank provenance for observability.
"""
from typing import List, Dict, Any, Optional
from collections import defaultdict
import logging

logger = logging.getLogger("hybrid_fusion")


class ReciprocalRankFusion:
    """Combines multiple ranked lists using Reciprocal Rank Fusion."""

    def __init__(self, k: int = 60, vector_weight: float = 1.0, bm25_weight: float = 1.0):
        self.k = k
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight

    def fuse(self, vector_results: List[Dict[str, Any]],
             bm25_results: List[Dict[str, Any]],
             top_k: int = 5) -> List[Dict[str, Any]]:
        """Fuses vector and BM25 results into a single ranked list."""
        rrf_scores = defaultdict(float)
        chunk_map = {}
        metadata_map = defaultdict(lambda: {
            "vector_rank": None,
            "vector_score": 0.0,
            "bm25_rank": None,
            "bm25_score": 0.0
        })

        # Process vector rankings (rank is 1-indexed)
        for rank, item in enumerate(vector_results, 1):
            cid = item["chunk_id"]
            chunk_map[cid] = item
            score_contrib = self.vector_weight / (self.k + rank)
            rrf_scores[cid] += score_contrib
            metadata_map[cid]["vector_rank"] = rank
            metadata_map[cid]["vector_score"] = float(item.get("score", 0.0))

        # Process BM25 rankings (rank is 1-indexed)
        for rank, item in enumerate(bm25_results, 1):
            cid = item["chunk_id"]
            if cid not in chunk_map:
                chunk_map[cid] = item
            score_contrib = self.bm25_weight / (self.k + rank)
            rrf_scores[cid] += score_contrib
            metadata_map[cid]["bm25_rank"] = rank
            metadata_map[cid]["bm25_score"] = float(item.get("score", 0.0))

        # Sort chunks by fused RRF score descending
        sorted_cids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)

        fused_results = []
        for rank, cid in enumerate(sorted_cids[:top_k], 1):
            base_item = dict(chunk_map[cid])
            meta = metadata_map[cid]

            base_item["fused_rank"] = rank
            base_item["rrf_score"] = float(rrf_scores[cid])
            base_item["vector_rank"] = meta["vector_rank"]
            base_item["vector_score"] = meta["vector_score"]
            base_item["bm25_rank"] = meta["bm25_rank"]
            base_item["bm25_score"] = meta["bm25_score"]
            base_item["retriever"] = "hybrid_rrf"
            fused_results.append(base_item)

        return fused_results


class HybridRetriever:
    """Orchestrates multi-channel retrieval across VectorStore and BM25."""

    def __init__(self, vector_store, bm25_retriever,
                 rrf_k: int = 60, vector_weight: float = 1.0, bm25_weight: float = 1.0):
        self.vector_store = vector_store
        self.bm25_retriever = bm25_retriever
        self.fuser = ReciprocalRankFusion(k=rrf_k, vector_weight=vector_weight, bm25_weight=bm25_weight)

    def retrieve(self, query: str, top_k: int = 5,
                 candidate_k: int = 20,
                 topic_filter: Optional[str] = None,
                 doc_id_filter: Optional[str] = None) -> Dict[str, Any]:
        """Executes vector and keyword search, then applies RRF."""
        # 1. Vector Search
        vector_candidates = self.vector_store.search(
            query=query, top_k=candidate_k,
            topic_filter=topic_filter, doc_id_filter=doc_id_filter
        )

        # 2. BM25 Search
        bm25_candidates = self.bm25_retriever.search(
            query=query, top_k=candidate_k,
            topic_filter=topic_filter, doc_id_filter=doc_id_filter
        )

        # 3. Reciprocal Rank Fusion
        fused = self.fuser.fuse(vector_candidates, bm25_candidates, top_k=top_k)

        return {
            "query": query,
            "fused_results": fused,
            "vector_candidates_count": len(vector_candidates),
            "bm25_candidates_count": len(bm25_candidates),
            "raw_vector_results": vector_candidates[:top_k],
            "raw_bm25_results": bm25_candidates[:top_k]
        }
