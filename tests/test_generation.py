"""
Unit tests for grounded answer generation, citation validation, and abstention logic.
"""
import pytest
from app.generation.citations import CitationValidator
from app.generation.llm import LLMGenerator


def test_citation_validator_valid_and_invalid():
    passages = [
        {"doc_id": "01_dns", "chunk_id": "01_dns#c0", "section": "Core Records", "source_url": "https://example.com/dns"}
    ]

    # Valid citation
    text_valid = "An A record maps IPv4 [Doc: 01_dns, Section: Core Records]."
    res_valid = CitationValidator.verify_citations(text_valid, passages)
    assert res_valid["is_valid"] is True
    assert res_valid["citation_precision"] == 1.0
    assert len(res_valid["valid_citations"]) == 1

    # Invalid / hallucinated citation
    text_invalid = "Some fact from an unretrieved document [Doc: fake_doc_99, Section: Fake Sec]."
    res_invalid = CitationValidator.verify_citations(text_invalid, passages)
    assert res_invalid["is_valid"] is False
    assert len(res_invalid["invalid_citations"]) == 1
    assert res_invalid["citation_precision"] == 0.0


def test_generator_abstention_on_unanswerable():
    generator = LLMGenerator(provider="auto")
    query = "What are the recommended fertilizer types for growing hydroponic tomatoes?"

    # Empty or completely unrelated passages
    passages = [
        {"doc_id": "01_dns", "section": "Root Zone", "content": "The root zone is managed by IANA."}
    ]

    result = generator.generate(query, "", passages)
    assert "sufficient evidence" in result["answer"].lower()
    assert result["abstention"] is True
    assert result["is_grounded"] is True


def test_generator_grounded_extractive_answer():
    generator = LLMGenerator(provider="auto")
    query = "What is the function of an A record in DNS?"
    passages = [
        {
            "doc_id": "01_dns_architecture",
            "section": "Core Records",
            "content": "An A record maps an IPv4 address to a hostname (32-bit address). An AAAA record maps an IPv6 address."
        }
    ]

    result = generator.generate(query, "", passages)
    assert "A record" in result["answer"]
    assert len(result["citations"]) >= 1
    assert result["citations"][0]["doc_id"] == "01_dns_architecture"
