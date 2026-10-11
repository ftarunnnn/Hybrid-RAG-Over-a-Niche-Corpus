"""
Automated Evaluation Benchmark Runner.
Compares BM25-only, Vector-only, Hybrid RRF, and Hybrid + Reranking across
the benchmark dataset (data/eval_qa.json).
Outputs statistical report with Recall@1, Recall@3, Recall@5, MRR, and nDCG@5.
"""
from typing import List, Dict, Any
import json
from pathlib import Path
from app.evaluation.metrics import RetrievalMetrics, GenerationMetrics


class RAGBenchmarkRunner:
    """Executes full benchmark suite across all 4 retrieval configurations."""

    def __init__(self, eval_qa_path: str = "data/eval_qa.json"):
        with open(eval_qa_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.questions = data.get("questions", [])

    def evaluate_pipeline(self, pipeline: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs evaluation on BM25, Vector, Hybrid, and Hybrid+Rerank configurations.
        """
        configs = ["bm25", "vector", "hybrid", "hybrid_rerank"]
        results = {c: {"recall@1": [], "recall@3": [], "recall@5": [], "mrr": [], "ndcg@5": [], "latencies": []} for c in configs}

        for q_item in self.questions:
            query = q_item["question"]
            golden_doc = q_item["golden_doc_id"]
            is_unanswerable = golden_doc is None

            # Skip unanswerable questions for pure retrieval rank metrics
            if is_unanswerable:
                continue

            # 1. BM25 Search
            bm25_hits = pipeline["bm25"].search(query, top_k=10)
            bm25_docs = [h.get("doc_id") for h in bm25_hits]

            # 2. Vector Search
            vec_hits = pipeline["vector"].search(query, top_k=10)
            vec_docs = [h.get("doc_id") for h in vec_hits]

            # 3. Hybrid Fused (RRF)
            fused_res = pipeline["hybrid"].retrieve(query, top_k=10, candidate_k=20)
            hybrid_hits = fused_res["fused_results"]
            hybrid_docs = [h.get("doc_id") for h in hybrid_hits]

            # 4. Hybrid + Reranker
            rerank_hits = pipeline["reranker"].rerank(query, hybrid_hits, top_k=10)
            rerank_docs = [h.get("doc_id") for h in rerank_hits]

            runs = {
                "bm25": bm25_docs,
                "vector": vec_docs,
                "hybrid": hybrid_docs,
                "hybrid_rerank": rerank_docs
            }

            for c, doc_list in runs.items():
                results[c]["recall@1"].append(RetrievalMetrics.recall_at_k(doc_list, golden_doc, 1))
                results[c]["recall@3"].append(RetrievalMetrics.recall_at_k(doc_list, golden_doc, 3))
                results[c]["recall@5"].append(RetrievalMetrics.recall_at_k(doc_list, golden_doc, 5))
                results[c]["mrr"].append(RetrievalMetrics.mean_reciprocal_rank(doc_list, golden_doc))
                results[c]["ndcg@5"].append(RetrievalMetrics.ndcg_at_k(doc_list, golden_doc, 5))

        # Compute summary averages
        summary = {}
        for c in configs:
            summary[c] = {
                "Recall@1": round(sum(results[c]["recall@1"]) / len(results[c]["recall@1"]), 4),
                "Recall@3": round(sum(results[c]["recall@3"]) / len(results[c]["recall@3"]), 4),
                "Recall@5": round(sum(results[c]["recall@5"]) / len(results[c]["recall@5"]), 4),
                "MRR": round(sum(results[c]["mrr"]) / len(results[c]["mrr"]), 4),
                "nDCG@5": round(sum(results[c]["ndcg@5"]) / len(results[c]["ndcg@5"]), 4),
                "total_queries_evaluated": len(results[c]["recall@1"])
            }

        return summary
