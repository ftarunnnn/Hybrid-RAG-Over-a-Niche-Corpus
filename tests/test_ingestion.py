"""
Unit and integration tests for document loaders, text cleaner, and ingestion pipeline.
"""
import pytest
from pathlib import Path
import json
from app.ingestion.loaders import DocumentLoader, DocumentLoaderError
from app.ingestion.cleaner import TextCleaner
from app.ingestion.pipeline import IngestionPipeline


def test_cleaner_removes_artifacts():
    dirty_text = "Some text with \x0c form feed and \r\n line break\n\n\n\nToo many newlines"
    cleaned = TextCleaner.clean(dirty_text)
    assert "\x0c" not in cleaned
    assert "\r" not in cleaned
    assert "\n\n\n" not in cleaned
    assert "Too many newlines" in cleaned


def test_cleaner_strips_headers_footers():
    text_with_headers = "--- Page 1 ---\nReal content here\n[Page 2]\nMore content"
    cleaned = TextCleaner.clean(text_with_headers)
    assert "--- Page 1 ---" not in cleaned
    assert "[Page 2]" not in cleaned
    assert "Real content here" in cleaned
    assert "More content" in cleaned


def test_load_markdown_file():
    path = Path("data/raw/01_dns_architecture_and_resolution.md")
    result = DocumentLoader.load_file(path)
    assert result["format"] == "markdown"
    assert "Domain Name System" in result["raw_text"]
    assert result["doc_id"] == "01_dns_architecture_and_resolution"


def test_load_html_file():
    path = Path("data/raw/09_http_https_and_tls13.html")
    result = DocumentLoader.load_file(path)
    assert result["format"] == "html"
    assert "HTTP/1.1" in result["raw_text"]
    assert "TLS 1.3" in result["raw_text"]


def test_load_pdf_file():
    path = Path("data/raw/13_tcp_congestion_control_spec.pdf")
    result = DocumentLoader.load_file(path)
    assert result["format"] == "pdf"
    assert result["page_count"] >= 1
    assert "RFC 5681" in result["raw_text"]


def test_unsupported_file_format(tmp_path):
    bad_file = tmp_path / "test.unsupported"
    bad_file.write_text("dummy")
    with pytest.raises(DocumentLoaderError):
        DocumentLoader.load_file(bad_file)


def test_ingestion_pipeline_end_to_end(tmp_path):
    output_path = tmp_path / "docs.json"
    pipeline = IngestionPipeline(manifest_path="data/corpus_manifest.json", processed_output_path=str(output_path))
    records = pipeline.ingest_directory(raw_dir="data/raw")
    assert len(records) == 13
    assert output_path.exists()
    
    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 13
    assert all("sha256" in doc and "cleaned_text" in doc for doc in data)
