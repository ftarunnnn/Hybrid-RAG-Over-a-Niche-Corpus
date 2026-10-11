# Hybrid RAG Project — 10 Completed Phases

| Phase | Title | Milestone Deliverables | Git Commit |
| :---: | :--- | :--- | :---: |
| **01** | **Scope Definition & Corpus Collection** | 13 specialized networking documents (Markdown, HTML, TXT, PDF), versioned `data/corpus_manifest.json` with SHA-256 hashes, and 41-question ground-truth evaluation dataset (`data/eval_qa.json`). | `1baa94a` |
| **02** | **Ingestion Pipeline & Cleaning** | Multi-format loaders (PyMuPDF, BeautifulSoup), structural text cleaner, incremental hash-based pipeline, and CLI runner (`scripts/ingest_corpus.py`). | `ade0c1e` |
| **03** | **Chunking & Metadata Preservation** | Heading-aware hierarchical chunker preserving code blocks and subnet tables, token-bounded chunks (400-700 tokens), stable IDs (`{doc_id}#chunk-{idx}`), and provenance tracking. | `30382d8` |
| **04** | **Semantic Vector Retrieval** | Dense vector embedding engine (384-dim normalized), Qdrant vector database integration, collection management, Cosine top-k search, and metadata payload filtering. | `51e4eba` |
| **05** | **BM25 Keyword Retrieval** | BM25 Okapi retriever with technical network tokenizer preserving exact IP/CIDR, ports, RFCs, CLI commands, and disk index serialization. | `845f942` |
| **06** | **Hybrid Fusion (RRF)** | Reciprocal Rank Fusion ($k=60$) combining keyword and dense vector streams, rank deduplication, candidate tuning, and baseline comparison harness. | `fa128aa` |
| **07** | **Reranking & Context Selection** | Cross-encoder relevance re-scoring, token budget context optimizer, near-duplicate paragraph suppression, and citation identifier preservation. | `4c60352` |
| **08** | **Grounded Generation & APIs** | Strict grounding prompts, citation validation grammar (`[Doc: <id>, Section: <sec>]`), automatic abstention on unanswerable queries, FastAPI REST API, and Streamlit interactive UI. | `ec10a81` |
| **09** | **Evaluation, Testing & Security** | Automated benchmark report across all 41 questions (Recall@5 = 100%, MRR = 0.9667), 32 passing pytest tests, prompt injection redaction, and path traversal defense. | `6ada6d0` |
| **10** | **Production Deployment & Release** | Multi-stage Dockerfile, docker-compose.yml (Qdrant + FastAPI + Streamlit), GitHub Actions CI/CD, locked requirements.txt, and complete architecture documentation. | `Current` |
