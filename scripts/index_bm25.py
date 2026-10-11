"""
BM25 indexing script.
Loads data/processed/chunks.json, builds BM25 index, and tests technical keywords.
"""
import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.retrieval.bm25 import TechnicalBM25Retriever


def main():
    chunks_path = Path("data/processed/chunks.json")
    if not chunks_path.exists():
        print("Chunks file not found. Run scripts/chunk_corpus.py first.")
        sys.exit(1)

    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"Loaded {len(chunks)} chunks.")
    retriever = TechnicalBM25Retriever()
    retriever.fit(chunks)

    index_output = "data/bm25_index.pkl"
    retriever.save(index_output)
    print(f"Saved BM25 index to {index_output}.")

    # Test technical queries
    test_queries = [
        "TCP/443 tcp-syn|tcp-rst",
        "802.1Q Native VLAN double-tagging",
        "RFC 5681 fast retransmit three duplicate ACKs"
    ]

    for q in test_queries:
        print(f"\nQuery: '{q}'")
        hits = retriever.search(q, top_k=2)
        for i, h in enumerate(hits, 1):
            print(f"[{i}] Score: {h['score']:.4f} | ID: {h['chunk_id']} | Topic: {h['topic']} | Sec: {h['section']}")
            print(f"    Excerpt: {h['content'][:110]}...")


if __name__ == "__main__":
    main()
