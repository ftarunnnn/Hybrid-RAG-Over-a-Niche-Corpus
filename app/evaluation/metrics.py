"""
Evaluation Metrics Engine for Retrieval and Grounded Generation.
Implements:
- Retrieval: Recall@k, Precision@k, MRR (Mean Reciprocal Rank), nDCG@k
- Generation: Grounding faithfulness, Citation Precision, Abstention accuracy
"""
from typing import List, Dict, Any, Optional
import math


class RetrievalMetrics:
    """Calculates standardized information retrieval evaluation metrics."""

    @staticmethod
    def recall_at_k(retrieved_doc_ids: List[str], golden_doc_id: Optional[str], k: int) -> float:
        """Recall@k: 1.0 if golden_doc_id is present in top-k, else 0.0."""
        if golden_doc_id is None:
            return 1.0  # For unanswerable queries
        top_k = [d.lower() for d in retrieved_doc_ids[:k]]
        return 1.0 if golden_doc_id.lower() in top_k else 0.0

    @staticmethod
    def precision_at_k(retrieved_doc_ids: List[str], golden_doc_id: Optional[str], k: int) -> float:
        """Precision@k: proportion of top-k retrieved docs that match golden_doc_id."""
        if golden_doc_id is None:
            return 1.0
        top_k = [d.lower() for d in retrieved_doc_ids[:k]]
        matches = sum(1 for d in top_k if d == golden_doc_id.lower())
        return matches / float(k) if k > 0 else 0.0

    @staticmethod
    def mean_reciprocal_rank(retrieved_doc_ids: List[str], golden_doc_id: Optional[str]) -> float:
        """MRR: 1 / rank of the first relevant document."""
        if golden_doc_id is None:
            return 1.0
        golden = golden_doc_id.lower()
        for rank, doc_id in enumerate(retrieved_doc_ids, 1):
            if doc_id.lower() == golden:
                return 1.0 / float(rank)
        return 0.0

    @staticmethod
    def ndcg_at_k(retrieved_doc_ids: List[str], golden_doc_id: Optional[str], k: int) -> float:
        """Normalized Discounted Cumulative Gain (nDCG@k)."""
        if golden_doc_id is None:
            return 1.0
        golden = golden_doc_id.lower()
        dcg = 0.0
        for rank, doc_id in enumerate(retrieved_doc_ids[:k], 1):
            rel = 1.0 if doc_id.lower() == golden else 0.0
            if rel > 0:
                dcg += rel / math.log2(rank + 1)
        idcg = 1.0 / math.log2(2)  # Ideal DCG for single relevant document at rank 1
        return dcg / idcg if idcg > 0 else 0.0


class GenerationMetrics:
    """Calculates ground-truth answer and citation accuracy metrics."""

    @staticmethod
    def keyword_overlap_score(generated_answer: str, must_contain: List[str]) -> float:
        """Measures proportion of required technical keywords present in answer."""
        if not must_contain:
            return 1.0
        ans_lower = generated_answer.lower()
        matches = sum(1 for kw in must_contain if kw.lower() in ans_lower)
        return matches / float(len(must_contain))

    @staticmethod
    def abstention_accuracy(is_unanswerable: bool, declared_abstention: bool) -> float:
        """1.0 if system abstained when unanswerable, or answered when answerable."""
        return 1.0 if is_unanswerable == declared_abstention else 0.0
