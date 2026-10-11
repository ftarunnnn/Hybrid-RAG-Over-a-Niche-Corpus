"""
Unit tests for heading-aware chunking and metadata preservation.
"""
import pytest
from app.ingestion.chunker import HeadingAwareChunker


def test_chunking_splits_on_headers():
    sample_doc = {
        "doc_id": "test_net",
        "title": "Networking 101",
        "topic": "Fundamentals",
        "source_url": "https://example.com/net",
        "version": "1.0",
        "cleaned_text": """# Overview
This is the overview section explaining IP addressing.

## Subnetting
Subnetting divides broadcast domains into smaller segments.

### CIDR Notation
CIDR uses slash notation such as /24 or /28."""
    }

    chunker = HeadingAwareChunker(target_chunk_tokens=500, overlap_tokens=50)
    chunks = chunker.chunk_document(sample_doc)

    assert len(chunks) >= 3
    sections = [c["section"] for c in chunks]
    assert "Overview" in sections
    assert "Subnetting" in sections
    assert "CIDR Notation" in sections

    for c in chunks:
        assert c["doc_id"] == "test_net"
        assert c["chunk_id"].startswith("test_net#chunk-")
        assert c["token_count"] > 0
        assert c["source_url"] == "https://example.com/net"


def test_chunking_preserves_code_blocks():
    sample_doc = {
        "doc_id": "test_cisco",
        "title": "Cisco CLI",
        "topic": "Configuration",
        "source_url": "https://example.com/cisco",
        "version": "1.0",
        "cleaned_text": """# Switch Config
Here is the switch configuration:

```text
interface GigabitEthernet0/1
 switchport mode trunk
 switchport trunk allowed vlan 10,20
 spanning-tree portfast trunk
```

End of configuration."""
    }

    chunker = HeadingAwareChunker(target_chunk_tokens=500)
    chunks = chunker.chunk_document(sample_doc)

    # Ensure code block is intact in one of the chunks
    found_code = any("switchport mode trunk" in c["content"] and "```text" in c["content"] for c in chunks)
    assert found_code is True


def test_chunk_ids_are_deterministic():
    sample_doc = {
        "doc_id": "test_id",
        "title": "Test Title",
        "topic": "Test Topic",
        "cleaned_text": "# H1\nContent A\n# H2\nContent B"
    }

    chunker = HeadingAwareChunker()
    run1 = chunker.chunk_document(sample_doc)
    run2 = chunker.chunk_document(sample_doc)

    assert [c["chunk_id"] for c in run1] == [c["chunk_id"] for c in run2]
