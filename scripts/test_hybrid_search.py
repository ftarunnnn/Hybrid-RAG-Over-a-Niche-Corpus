"""
Script to demonstrate and compare Hybrid Retrieval (RRF) against BM25 and Vector baselines.
"""
import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.retrieval.vector_search import QdrantVectorStore
from app.retrieval.bm25 import TechnicalBM25Retriever
from app.retrieval.fusion import HybridRetriever


def main():
    chunks_path = Path("data/processed/chunks.json")
    if not chunks_path.exists():
        print("Chunks not found. Run previous stages first.")
        sys.exit(1)

    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    # Initialize retrievers
    store = QdrantVectorStore(collection_name="networking_corpus", location="qdrant_storage")
    if store.count() == 0:
        store.index_chunks(chunks)

    bm25 = TechnicalBM25Retriever.load("data/bm25_index.pkl")
    hybrid = HybridRetriever(vector_store=store, bm25_retriever=bm25, rrf_k=60)

    test_queries = [
        "Why is /31 subnet permitted on point-to-point links under RFC 3021?",
        "What causes MTU black holes and how does tcp adjust-mss prevent stalling?",
        "How do Route Reflectors bypass the iBGP split horizon rule?"
    ]

    for q in test_queries:
        print("\n" + "=" * 70)
        print(f"QUERY: {q}")
        print("=" * 70)

        result = hybrid.retrieve(q, top_k=3, candidate_k=15)
        print("\n--- [1] BM25 ONLY TOP 3 ---")
        for i, hit in enumerate(result["raw_bm25_results"], 1):
            print(f"  [{i}] (Score: {hit['score']:.2f}) {hit['chunk_id']} -> {hit['section']}")

        print("\n--- [2] VECTOR ONLY TOP 3 ---")
        for i, hit in enumerate(result["raw_vector_results"], 1):
            print(f"  [{i}] (Score: {hit['score']:.4f}) {hit['chunk_id']} -> {hit['section']}")

        print("\n--- [3] HYBRID FUSED (RRF) TOP 3 ---")
        for i, hit in enumerate(result["fused_results"], 1):
            print(f"  [{i}] (RRF: {hit['rrf_score']:.5f} | VecRank: {hit['vector_rank']} | BM25Rank: {hit['bm25_rank']}) {hit['chunk_id']} -> {hit['section']}")
            print(f"      Snippet: {hit['content'][:100].replace('\n', ' ')}...")


if __name__ == "__main__":
    main()
