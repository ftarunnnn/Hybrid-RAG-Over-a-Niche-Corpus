"""
Citation Extraction and Verification Engine.
Parses citations from generated answers and verifies that each referenced document
and section actually exists within the retrieved evidence set.
"""
from typing import List, Dict, Any, Tuple
import re


class CitationValidator:
    """Validates citations in generated answers against retrieved context chunks."""

    # Matches patterns like [Doc: 01_dns, Section: Core Records] or [Doc: 01_dns]
    CITATION_REGEX = re.compile(r"\[Doc:\s*([^,\]]+)(?:,\s*Section:\s*([^\]]+))?\]")

    @classmethod
    def extract_citations(cls, text: str) -> List[Dict[str, str]]:
        """Extracts all citations from answer text."""
        matches = cls.CITATION_REGEX.findall(text)
        citations = []
        for doc_id, section in matches:
            citations.append({
                "doc_id": doc_id.strip(),
                "section": section.strip() if section else "General"
            })
        return citations

    @classmethod
    def verify_citations(cls, answer_text: str,
                         retrieved_passages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Verifies citations in answer against retrieved passages.
        Returns:
            - is_valid: True if at least one citation exists and all citations point to retrieved documents.
            - valid_citations: List of verified citations.
            - invalid_citations: List of hallucinated citations.
            - citation_precision: Ratio of valid citations over total citations.
        """
        extracted = cls.extract_citations(answer_text)
        if not extracted:
            # If the model declared insufficient/unsupported evidence, absence of citation is valid abstention
            lower_ans = answer_text.lower()
            if "insufficient evidence" in lower_ans or "not have sufficient evidence" in lower_ans or "unsupported" in lower_ans:
                return {
                    "is_valid": True,
                    "abstention": True,
                    "valid_citations": [],
                    "invalid_citations": [],
                    "citation_precision": 1.0
                }
            return {
                "is_valid": False,
                "abstention": False,
                "valid_citations": [],
                "invalid_citations": [],
                "citation_precision": 0.0
            }

        retrieved_docs = {p.get("doc_id", "").lower(): p for p in retrieved_passages}
        retrieved_chunks = {p.get("chunk_id", "").lower(): p for p in retrieved_passages}

        valid = []
        invalid = []

        for cite in extracted:
            doc_key = cite["doc_id"].lower()
            if doc_key in retrieved_docs or doc_key in retrieved_chunks:
                matched_passage = retrieved_docs.get(doc_key) or retrieved_chunks.get(doc_key)
                valid.append({
                    **cite,
                    "source_url": matched_passage.get("source_url", "") if matched_passage else "",
                    "title": matched_passage.get("title", "") if matched_passage else ""
                })
            else:
                invalid.append(cite)

        precision = len(valid) / len(extracted) if extracted else 0.0
        return {
            "is_valid": len(invalid) == 0 and len(valid) > 0,
            "abstention": False,
            "valid_citations": valid,
            "invalid_citations": invalid,
            "citation_precision": round(precision, 4)
        }
