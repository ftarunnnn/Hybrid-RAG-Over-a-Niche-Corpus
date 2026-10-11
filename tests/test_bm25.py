"""
Unit tests for BM25 keyword retrieval engine.
"""
import pytest
from app.retrieval.bm25 import TechnicalBM25Retriever


def test_technical_tokenizer_preserves_identifiers():
    sample = "Captured on port TCP/443 with 802.1Q tag for subnet 192.168.1.0/24 and SYN-ACK flag."
    tokens = TechnicalBM25Retriever.tokenize(sample)
    assert "tcp/443" in tokens
    assert "802.1q" in tokens
    assert "192.168.1.0/24" in tokens
    assert "syn-ack" in tokens


def test_bm25_fit_and_search():
    chunks = [
        {"chunk_id": "c1", "doc_id": "d1", "title": "BGP", "topic": "Routing", "section": "MED", "content": "MED is Multi-Exit Discriminator."},
        {"chunk_id": "c2", "doc_id": "d2", "title": "OSPF", "topic": "Routing", "section": "LSA", "content": "Type 1 is Router LSA."},
        {"chunk_id": "c3", "doc_id": "d3", "title": "DHCP", "topic": "DHCP", "section": "DORA", "content": "DORA is Discover Offer Request ACK."}
    ]

    retriever = TechnicalBM25Retriever()
    retriever.fit(chunks)

    results = retriever.search("Router LSA", top_k=1)
    assert len(results) == 1
    assert results[0]["chunk_id"] == "c2"
    assert results[0]["score"] > 0


def test_bm25_save_and_load(tmp_path):
    chunks = [
        {"chunk_id": "c1", "doc_id": "d1", "title": "DNS", "topic": "DNS", "section": "Root", "content": "Root nameserver resolves TLD."},
        {"chunk_id": "c2", "doc_id": "d2", "title": "BGP", "topic": "Routing", "section": "AS", "content": "Autonomous system numbers."}
    ]
    retriever = TechnicalBM25Retriever()
    retriever.fit(chunks)

    save_file = str(tmp_path / "test_bm25.pkl")
    retriever.save(save_file)

    loaded = TechnicalBM25Retriever.load(save_file)
    results = loaded.search("nameserver", top_k=1)
    assert len(results) == 1
    assert results[0]["chunk_id"] == "c1"
