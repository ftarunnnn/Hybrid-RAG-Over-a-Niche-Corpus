"""
Unit tests for CrossEncoderReranker and ContextBuilder.
"""
import pytest
from app.retrieval.reranker import CrossEncoderReranker
from app.retrieval.context_builder import ContextBuilder


def test_reranker_prioritizes_exact_matches_and_sections():
    reranker = CrossEncoderReranker()
    query = "What is the function of DHCP Option 82 Relay Agent?"

    candidates = [
        {
            "chunk_id": "c1",
            "doc_id": "dns",
            "topic": "DNS",
            "section": "Overview",
            "content": "DNS resolves domain names into IP addresses."
        },
        {
            "chunk_id": "c2",
            "doc_id": "dhcp",
            "topic": "DHCP",
            "section": "DHCP Relay Agent (Option 82)",
            "content": "Option 82 is inserted by DHCP Relay Agents, providing Circuit ID and Remote ID."
        }
    ]

    reranked = reranker.rerank(query, candidates, top_k=2)
    assert len(reranked) == 2
    assert reranked[0]["chunk_id"] == "c2"
    assert reranked[0]["rerank_score"] > reranked[1]["rerank_score"]
    assert reranked[0]["rerank_position"] == 1


def test_context_builder_suppresses_redundancy_and_fits_budget():
    builder = ContextBuilder(max_context_tokens=300)

    passages = [
        {
            "chunk_id": "c1",
            "doc_id": "doc1",
            "title": "T1",
            "section": "S1",
            "source_url": "http://example.com/1",
            "content": "Unique passage about BGP local preference attributes."
        },
        {
            "chunk_id": "c2",
            "doc_id": "doc2",
            "title": "T2",
            "section": "S2",
            "source_url": "http://example.com/2",
            "content": "Unique passage about BGP local preference attributes."  # Exact duplicate
        },
        {
            "chunk_id": "c3",
            "doc_id": "doc3",
            "title": "T3",
            "section": "S3",
            "source_url": "http://example.com/3",
            "content": "Distinct passage describing OSPF areas and Dijkstra algorithm."
        }
    ]

    context_str, selected, stats = builder.build_context(passages)
    # The duplicate should be filtered out
    assert len(selected) == 2
    assert "--- EVIDENCE [1] ---" in context_str
    assert "--- EVIDENCE [2] ---" in context_str
    assert "Unique passage about BGP" in context_str
    assert "Distinct passage describing OSPF" in context_str
    assert stats["selected_chunks"] == 2
