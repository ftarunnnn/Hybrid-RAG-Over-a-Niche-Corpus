"""
Ingestion Pipeline orchestrator.
Manages multi-document parsing, text cleaning, metadata enrichment,
hash-based deduplication, and incremental processing state.
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib
import json
import logging
from app.ingestion.loaders import DocumentLoader, DocumentLoaderError
from app.ingestion.cleaner import TextCleaner

logger = logging.getLogger("ingestion_pipeline")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class IngestionPipeline:
    """Manages the full document ingestion lifecycle."""

    def __init__(self, manifest_path: Optional[str] = "data/corpus_manifest.json",
                 processed_output_path: str = "data/processed/documents.json"):
        self.manifest_path = Path(manifest_path) if manifest_path else None
        self.processed_output_path = Path(processed_output_path)
        self.manifest_data = self._load_manifest()

    def _load_manifest(self) -> Dict[str, Any]:
        """Loads metadata manifest if available."""
        if self.manifest_path and self.manifest_path.exists():
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"documents": []}

    def _get_manifest_metadata(self, filename: str) -> Dict[str, Any]:
        """Matches a filename to its manifest metadata entry."""
        for doc in self.manifest_data.get("documents", []):
            if doc.get("filename") == filename:
                return doc
        return {}

    def compute_sha256(self, file_path: Path) -> str:
        """Computes SHA-256 hash of a file."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def process_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Loads, cleans, and enriches a single document."""
        try:
            logger.info(f"Ingesting: {file_path.name}")
            loaded = DocumentLoader.load_file(file_path)
            cleaned_text = TextCleaner.clean(loaded["raw_text"])
            file_hash = self.compute_sha256(file_path)
            meta = self._get_manifest_metadata(file_path.name)

            record = {
                "doc_id": loaded["doc_id"],
                "filename": loaded["filename"],
                "filepath": loaded["filepath"],
                "format": loaded["format"],
                "page_count": loaded.get("page_count", 1),
                "sha256": file_hash,
                "title": meta.get("title", loaded.get("html_title", loaded["doc_id"].replace("_", " ").title())),
                "topic": meta.get("topic", "General Networking"),
                "source_url": meta.get("source_url", ""),
                "version": meta.get("version", "1.0"),
                "license": meta.get("license", "Open Reference"),
                "cleaned_text": cleaned_text,
                "char_count": len(cleaned_text),
                "word_count": len(cleaned_text.split())
            }
            return record
        except Exception as e:
            logger.error(f"Failed to ingest {file_path}: {e}")
            return None

    def ingest_directory(self, raw_dir: str = "data/raw") -> List[Dict[str, Any]]:
        """Ingests all valid files in a directory, supporting incremental checks."""
        path = Path(raw_dir)
        if not path.exists():
            raise FileNotFoundError(f"Raw directory not found: {raw_dir}")

        supported_exts = {".md", ".markdown", ".txt", ".html", ".htm", ".pdf"}
        files = [p for p in path.glob("*") if p.suffix.lower() in supported_exts]
        logger.info(f"Discovered {len(files)} documents to ingest.")

        existing_hashes = {}
        if self.processed_output_path.exists():
            try:
                with open(self.processed_output_path, "r", encoding="utf-8") as f:
                    past_docs = json.load(f)
                    existing_hashes = {d["filename"]: d["sha256"] for d in past_docs}
            except Exception:
                existing_hashes = {}

        processed_records = []
        skipped_count = 0

        for file_path in files:
            current_hash = self.compute_sha256(file_path)
            if file_path.name in existing_hashes and existing_hashes[file_path.name] == current_hash:
                logger.info(f"Skipping unchanged file (incremental): {file_path.name}")
                # Load existing record if possible
                with open(self.processed_output_path, "r", encoding="utf-8") as f:
                    past_docs = json.load(f)
                    match = next((d for d in past_docs if d["filename"] == file_path.name), None)
                    if match:
                        processed_records.append(match)
                        skipped_count += 1
                        continue

            record = self.process_file(file_path)
            if record:
                processed_records.append(record)

        self.processed_output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.processed_output_path, "w", encoding="utf-8") as f:
            json.dump(processed_records, f, indent=2)

        logger.info(f"Ingestion complete: {len(processed_records)} total records saved to {self.processed_output_path} ({skipped_count} unchanged skipped).")
        return processed_records
