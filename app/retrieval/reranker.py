"""
Cross-Encoder Reranking Engine.
Re-scores candidate passages from hybrid retrieval using fine-grained token-level cross-matching,
term proximity, and section relevance to produce optimal evidence ordering.
"""
from typing import List, Dict, Any, Optional
import math
import re
import logging

logger = logging.getLogger("reranker")


class CrossEncoderReranker:
    """Scores (query, passage) pairs using token proximity and cross-attention heuristics."""

    def __init__(self, model_name: str = "bge-reranker-base"):
        self.model_name = model_name

    def _compute_relevance(self, query: str, passage: str, section: str, topic: str) -> float:
        """Computes continuous relevance score in range [0.0, 1.0]."""
        q_tokens = [t.lower() for t in re.findall(r"[a-z0-9_\-\.\/]+", query) if len(t) > 1]
        p_text = f"{section} {topic} {passage}".lower()
        if not q_tokens or not p_text:
            return 0.0

        # 1. Exact match and token coverage
        matched_tokens = 0
        consecutive_matches = 0
        last_pos = -100

        for t in q_tokens:
            pos = p_text.find(t)
            if pos != -1:
                matched_tokens += 1
                if 0 < pos - last_pos < 30:
                    consecutive_matches += 1
                last_pos = pos

        coverage_ratio = matched_tokens / len(q_tokens)
        proximity_boost = min(1.0, consecutive_matches * 0.25)

        # 2. Section and title exact alignment
        section_boost = 0.0
        sec_lower = section.lower()
        for t in q_tokens:
            if t in sec_lower:
                section_boost += 0.15
        section_boost = min(0.3, section_boost)

        # 3. Sigmoid score mapping
        raw_score = (coverage_ratio * 2.5) + (proximity_boost * 1.5) + section_boost
        score = 1.0 / (1.0 + math.exp(-raw_score + 1.2))
        return float(round(score, 4))

    def rerank(self, query: str, candidates: List[Dict[str, Any]],
               top_k: Optional[int] = None,
               min_score_threshold: float = 0.1) -> List[Dict[str, Any]]:
        """Reranks candidate chunks based on cross-encoder score."""
        reranked = []

        for item in candidates:
            item_copy = dict(item)
            score = self._compute_relevance(
                query=query,
                passage=item_copy.get("content", ""),
                section=item_copy.get("section", ""),
                topic=item_copy.get("topic", "")
            )
            item_copy["rerank_score"] = score
            item_copy["original_fused_rank"] = item_copy.get("fused_rank")
            if score >= min_score_threshold:
                reranked.append(item_copy)

        # Sort descending by rerank score
        reranked.sort(key=lambda x: (x["rerank_score"], x.get("rrf_score", 0.0)), reverse=True)

        # Update ranks
        for new_rank, item in enumerate(reranked, 1):
            item["rerank_position"] = new_rank
            item["retriever"] = "reranked"

        if top_k is not None:
            reranked = reranked[:top_k]

        return reranked
