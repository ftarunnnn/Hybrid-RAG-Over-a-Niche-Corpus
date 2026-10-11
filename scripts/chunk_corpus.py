"""
CLI runner for heading-aware chunking pipeline.
Generates data/processed/chunks.json with stable IDs and metadata attribution.
"""
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ingestion.chunker import HeadingAwareChunker


def main():
    docs_path = Path("data/processed/documents.json")
    if not docs_path.exists():
        print("Documents not found. Please run scripts/ingest_corpus.py first.")
        sys.exit(1)

    with open(docs_path, "r", encoding="utf-8") as f:
        docs = json.load(f)

    chunker = HeadingAwareChunker(target_chunk_tokens=500, overlap_tokens=50)
    chunks = chunker.chunk_corpus(docs)

    output_path = Path("data/processed/chunks.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)

    token_counts = [c["token_count"] for c in chunks]
    avg_tokens = sum(token_counts) / len(token_counts) if token_counts else 0

    print("=" * 60)
    print("CHUNKING SUMMARY REPORT")
    print("=" * 60)
    print(f"Total documents processed: {len(docs)}")
    print(f"Total chunks generated:   {len(chunks)}")
    print(f"Average tokens per chunk: {avg_tokens:.1f}")
    print(f"Min tokens:               {min(token_counts) if token_counts else 0}")
    print(f"Max tokens:               {max(token_counts) if token_counts else 0}")
    print(f"Chunks saved to:          {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
