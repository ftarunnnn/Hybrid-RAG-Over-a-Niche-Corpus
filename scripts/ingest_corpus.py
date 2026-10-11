"""
Command-line runner for corpus ingestion pipeline.
Usage:
    python scripts/ingest_corpus.py [--raw-dir data/raw] [--manifest data/corpus_manifest.json]
"""
import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ingestion.pipeline import IngestionPipeline


def main():
    parser = argparse.ArgumentParser(description="Ingest networking documents into normalized JSON records.")
    parser.add_argument("--raw-dir", default="data/raw", help="Path to raw documents directory")
    parser.add_argument("--manifest", default="data/corpus_manifest.json", help="Path to manifest JSON")
    parser.add_argument("--output", default="data/processed/documents.json", help="Output path for processed documents")
    args = parser.parse_args()

    pipeline = IngestionPipeline(manifest_path=args.manifest, processed_output_path=args.output)
    print(f"Starting ingestion from: {args.raw_dir}")
    records = pipeline.ingest_directory(raw_dir=args.raw_dir)
    print(f"Ingestion finished successfully: {len(records)} documents processed and verified.")


if __name__ == "__main__":
    main()
