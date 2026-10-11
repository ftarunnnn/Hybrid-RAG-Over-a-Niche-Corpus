"""
Vector indexing script.
Loads data/processed/chunks.json, embeds passages, and stores them in Qdrant.
Performs verification queries.
"""
import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.retrieval.vector_search import QdrantVectorStore


def main():
    chunks_path = Path("data/processed/chunks.json")
    if not chunks_path.exists():
        print("Chunks not found. Run scripts/chunk_corpus.py first.")
        sys.exit(1)

    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"Loaded {len(chunks)} chunks.")
    # Use local disk storage for persistence
    storage_path = "qdrant_storage"
    store = QdrantVectorStore(collection_name="networking_corpus", location=storage_path)
    count = store.index_chunks(chunks)
    print(f"Indexed {count} chunks into Qdrant collection '{store.collection_name}' at {storage_path}.")

    # Test retrieval
    test_query = "What happens during OSPF DR and BDR election on multi-access networks?"
    print(f"\nRunning test semantic query: '{test_query}'")
    hits = store.search(test_query, top_k=3)
    for i, h in enumerate(hits, 1):
        print(f"[{i}] Score: {h['score']:.4f} | ID: {h['chunk_id']} | Topic: {h['topic']} | Sec: {h['section']}")
        snippet = h['content'][:120].replace('\n', ' ')
        print(f"    Snippet: {snippet}...")


if __name__ == "__main__":
    main()
