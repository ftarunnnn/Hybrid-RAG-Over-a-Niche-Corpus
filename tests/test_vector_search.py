"""
Unit tests for Qdrant vector retrieval and dense embeddings.
"""
import pytest
from app.retrieval.embeddings import DenseEmbeddingEngine
from app.retrieval.vector_search import QdrantVectorStore


def test_dense_embedding_normalization():
    embedder = DenseEmbeddingEngine(vector_dim=384)
    vec = embedder.embed_text("Transmission Control Protocol TCP handshake")
    assert len(vec) == 384
    # Compute L2 norm
    import numpy as np
    norm = np.linalg.norm(vec)
    assert pytest.approx(norm, rel=1e-3) == 1.0


def test_qdrant_in_memory_indexing_and_search():
    embedder = DenseEmbeddingEngine(vector_dim=384)
    store = QdrantVectorStore(collection_name="test_mem_collection", location=":memory:", embedder=embedder)

    sample_chunks = [
        {
            "chunk_id": "dns_001",
            "doc_id": "dns_doc",
            "title": "DNS Guide",
            "topic": "DNS",
            "section": "Records",
            "content": "An A record maps an IPv4 address, while an AAAA record maps an IPv6 address.",
            "token_count": 20,
            "source_url": "https://example.com/dns"
        },
        {
            "chunk_id": "bgp_001",
            "doc_id": "bgp_doc",
            "title": "BGP Guide",
            "topic": "Routing",
            "section": "Path Attributes",
            "content": "BGP uses path attributes like AS_PATH, LOCAL_PREF, and MED to select the best route.",
            "token_count": 22,
            "source_url": "https://example.com/bgp"
        }
    ]

    count = store.index_chunks(sample_chunks)
    assert count == 2
    assert store.count() == 2

    # Query matching DNS
    hits = store.search("Tell me about DNS A and AAAA records", top_k=2)
    assert len(hits) >= 1
    assert hits[0]["chunk_id"] == "dns_001"
    assert "DNS" in hits[0]["title"]


def test_qdrant_metadata_filtering():
    embedder = DenseEmbeddingEngine(vector_dim=384)
    store = QdrantVectorStore(collection_name="test_filter_col", location=":memory:", embedder=embedder)

    sample_chunks = [
        {"chunk_id": "c1", "doc_id": "d1", "topic": "VLANs", "section": "Trunking", "content": "802.1Q tags carry VLAN ID."},
        {"chunk_id": "c2", "doc_id": "d2", "topic": "Security", "section": "Firewalls", "content": "Firewalls use state tables."}
    ]
    store.index_chunks(sample_chunks)

    # Search with topic filter
    hits = store.search("frames and tags", top_k=5, topic_filter="VLANs")
    assert all(h["topic"] == "VLANs" for h in hits)
