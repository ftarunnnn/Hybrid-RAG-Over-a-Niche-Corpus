"""
Unit tests for Reciprocal Rank Fusion (RRF) and Hybrid Retriever.
"""
import pytest
from app.retrieval.fusion import ReciprocalRankFusion, HybridRetriever


def test_rrf_scoring_and_deduplication():
    fuser = ReciprocalRankFusion(k=60, vector_weight=1.0, bm25_weight=1.0)

    vec_results = [
        {"chunk_id": "docA", "title": "A", "section": "s1", "score": 0.9},
        {"chunk_id": "docB", "title": "B", "section": "s2", "score": 0.8},
        {"chunk_id": "docC", "title": "C", "section": "s3", "score": 0.7}
    ]

    bm25_results = [
        {"chunk_id": "docB", "title": "B", "section": "s2", "score": 15.0},
        {"chunk_id": "docD", "title": "D", "section": "s4", "score": 12.0},
        {"chunk_id": "docA", "title": "A", "section": "s1", "score": 10.0}
    ]

    fused = fuser.fuse(vec_results, bm25_results, top_k=4)

    # docB was rank 2 in vec (1/62) and rank 1 in bm25 (1/61) -> ~0.0325
    # docA was rank 1 in vec (1/61) and rank 3 in bm25 (1/63) -> ~0.0322
    assert len(fused) == 4
    # Ensure docB and docA are top 2 because both retrievers found them
    top_cids = [fused[0]["chunk_id"], fused[1]["chunk_id"]]
    assert "docB" in top_cids
    assert "docA" in top_cids

    for item in fused:
        assert "rrf_score" in item
        assert "vector_rank" in item
        assert "bm25_rank" in item
        assert item["retriever"] == "hybrid_rrf"


def test_rrf_weighting():
    # Test setting vector_weight=2.0, bm25_weight=0.0 (vector priority)
    fuser = ReciprocalRankFusion(k=60, vector_weight=2.0, bm25_weight=0.0)

    vec_results = [{"chunk_id": "docVec", "score": 0.9}]
    bm25_results = [{"chunk_id": "docBM25", "score": 20.0}]

    fused = fuser.fuse(vec_results, bm25_results, top_k=2)
    assert fused[0]["chunk_id"] == "docVec"
