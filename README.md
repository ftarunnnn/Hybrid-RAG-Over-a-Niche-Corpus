# Hybrid RAG Over a Niche Corpus: Computer Networking Assistant

A production-grade question-answering system operating over a specialized computer networking knowledge corpus. Combines BM25 keyword search with dense vector embeddings in Qdrant, fuses them using Reciprocal Rank Fusion (RRF), cross-encoder reranking, and grounded generation with strict citation verification.

## Architecture Highlights
- **Niche Corpus**: In-depth RFC and production networking manuals (DNS, DHCP, TCP/IP, BGP, OSPF, VLANs, Subnetting, Troubleshooting, TLS 1.3, SD-WAN).
- **Hybrid Retrieval**: Dual-stream BM25 + Qdrant Dense Vector search.
- **Rank Fusion**: Reciprocal Rank Fusion (RRF) with configurable smoothing ($k=60$) and weights.
- **Reranker**: Cross-Encoder relevance re-scoring with token budget context selection.
- **Grounded Generation**: Enforced citation mapping with zero hallucination & automatic abstention.
- **Full Stack**: FastAPI REST API + Streamlit Interactive Dashboard + Docker Compose.