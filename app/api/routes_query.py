"""
Query and Retrieval API routes.
Provides /api/query for end-to-end grounded RAG with citations,
and /api/retrieve for diagnostic multi-retriever inspection.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import time

from app.config import settings
from app.retrieval.vector_search import QdrantVectorStore
from app.retrieval.bm25 import TechnicalBM25Retriever
from app.retrieval.fusion import HybridRetriever
from app.retrieval.reranker import CrossEncoderReranker
from app.retrieval.context_builder import ContextBuilder
from app.generation.llm import LLMGenerator

router = APIRouter(tags=["Query & Retrieval"])

# Global singletons
_vector_store = None
_bm25_retriever = None
_hybrid_retriever = None
_reranker = None
_context_builder = None
_generator = None


def get_pipeline():
    global _vector_store, _bm25_retriever, _hybrid_retriever, _reranker, _context_builder, _generator
    if _vector_store is None:
        _vector_store = QdrantVectorStore(
            collection_name=settings.QDRANT_COLLECTION,
            location=settings.QDRANT_LOCATION
        )
    if _bm25_retriever is None:
        try:
            _bm25_retriever = TechnicalBM25Retriever.load(settings.BM25_INDEX_PATH)
        except Exception:
            _bm25_retriever = TechnicalBM25Retriever()
    if _hybrid_retriever is None:
        _hybrid_retriever = HybridRetriever(
            vector_store=_vector_store,
            bm25_retriever=_bm25_retriever,
            rrf_k=settings.RRF_K,
            vector_weight=settings.VECTOR_WEIGHT,
            bm25_weight=settings.BM25_WEIGHT
        )
    if _reranker is None:
        _reranker = CrossEncoderReranker()
    if _context_builder is None:
        _context_builder = ContextBuilder(max_context_tokens=settings.MAX_CONTEXT_TOKENS)
    if _generator is None:
        _generator = LLMGenerator(
            provider=settings.LLM_PROVIDER,
            model_name=settings.LLM_MODEL,
            api_base_url=settings.LLM_BASE_URL,
            api_key=settings.OPENAI_API_KEY
        )
    return {
        "vector": _vector_store,
        "bm25": _bm25_retriever,
        "hybrid": _hybrid_retriever,
        "reranker": _reranker,
        "builder": _context_builder,
        "generator": _generator
    }


class QueryRequest(BaseModel):
    query: str = Field(..., description="Networking technical question")
    mode: str = Field("hybrid", description="Retrieval mode: 'hybrid', 'bm25', 'vector'")
    enable_rerank: bool = Field(True, description="Enable cross-encoder reranking")
    top_k: int = Field(5, ge=1, le=20, description="Final number of passages to select")
    topic_filter: Optional[str] = Field(None, description="Optional topic filter (e.g. DNS, DHCP, VLANs)")
    doc_id_filter: Optional[str] = Field(None, description="Optional doc_id filter")


class QueryResponse(BaseModel):
    query: str
    answer: str
    is_grounded: bool
    abstention: bool
    citations: List[Dict[str, Any]]
    citation_precision: float
    retrieval_mode: str
    latency_ms: float
    selected_passages: List[Dict[str, Any]]
    context_stats: Dict[str, Any]


@router.post("/query", response_model=QueryResponse)
def answer_question(req: QueryRequest, pipe=Depends(get_pipeline)):
    """Answers networking queries with strict citation provenance."""
    t0 = time.time()
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # 1. Retrieve candidates
    if req.mode == "bm25":
        candidates = pipe["bm25"].search(
            query, top_k=req.top_k * 2, topic_filter=req.topic_filter, doc_id_filter=req.doc_id_filter
        )
    elif req.mode == "vector":
        candidates = pipe["vector"].search(
            query, top_k=req.top_k * 2, topic_filter=req.topic_filter, doc_id_filter=req.doc_id_filter
        )
    else:  # hybrid
        retrieval_res = pipe["hybrid"].retrieve(
            query=query, top_k=req.top_k * 3, candidate_k=settings.TOP_K_CANDIDATES,
            topic_filter=req.topic_filter, doc_id_filter=req.doc_id_filter
        )
        candidates = retrieval_res["fused_results"]

    # 2. Reranking
    if req.enable_rerank and candidates:
        ranked_passages = pipe["reranker"].rerank(query, candidates, top_k=req.top_k)
    else:
        ranked_passages = candidates[:req.top_k]

    # 3. Context Selection
    context_str, selected_chunks, stats = pipe["builder"].build_context(ranked_passages)

    # 4. Grounded Generation
    gen_result = pipe["generator"].generate(query, context_str, selected_chunks)

    elapsed_ms = round((time.time() - t0) * 1000, 2)

    return QueryResponse(
        query=query,
        answer=gen_result["answer"],
        is_grounded=gen_result["is_grounded"],
        abstention=gen_result["abstention"],
        citations=gen_result["citations"],
        citation_precision=gen_result["citation_precision"],
        retrieval_mode=req.mode,
        latency_ms=elapsed_ms,
        selected_passages=selected_chunks,
        context_stats=stats
    )


@router.post("/retrieve")
def inspect_retrieval(req: QueryRequest, pipe=Depends(get_pipeline)):
    """Diagnostic endpoint returning raw BM25, Vector, RRF, and Rerank rankings."""
    t0 = time.time()
    retrieval_res = pipe["hybrid"].retrieve(
        query=req.query, top_k=req.top_k * 2, candidate_k=settings.TOP_K_CANDIDATES,
        topic_filter=req.topic_filter, doc_id_filter=req.doc_id_filter
    )
    fused = retrieval_res["fused_results"]
    reranked = pipe["reranker"].rerank(req.query, fused, top_k=req.top_k)

    return {
        "query": req.query,
        "bm25_top": retrieval_res["raw_bm25_results"][:req.top_k],
        "vector_top": retrieval_res["raw_vector_results"][:req.top_k],
        "fused_rrf_top": fused[:req.top_k],
        "reranked_top": reranked,
        "latency_ms": round((time.time() - t0) * 1000, 2)
    }
