<div align="center">

# 🌐 NetRAG: Production Hybrid RAG Over a Niche Corpus

**A production-quality AI question-answering system combining BM25 keyword search, Qdrant dense vector embeddings, Reciprocal Rank Fusion (RRF), Cross-Encoder reranking, and strictly grounded generation with verified citations.**

[![CI](https://github.com/ftarunnnn/Hybrid-RAG-Over-a-Niche-Corpus/actions/workflows/ci.yml/badge.svg)](https://github.com/ftarunnnn/Hybrid-RAG-Over-a-Niche-Corpus/actions)
[![Qdrant](https://img.shields.io/badge/Vector_DB-Qdrant-red?logo=qdrant)](https://github.com/qdrant/qdrant)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python)](https://python.org)
[![Tests](https://img.shields.io/badge/Tests-32%20Passed%20(100%25)-brightgreen)]()

[Architecture](docs/ARCHITECTURE.md) • [10-Phase Roadmap](docs/PHASE_ROADMAP.md) • [Benchmark Report](docs/BENCHMARK_REPORT.md) • [Docker Deployment](#-docker-deployment)

</div>

---

## 🎯 Project Overview
Building a simple toy RAG chatbot over random PDFs is not enough for real enterprise search. In technical domains like **Computer Networking**, queries frequently contain exact identifiers (e.g. `TCP/443`, `802.1Q`, `192.168.1.0/24`, `RFC 5681`, `ip nat inside`) alongside conceptual questions (e.g. *"Why is /31 permitted on point-to-point links?"*).

**NetRAG** solves this through a multi-stage **Dual-Stream Hybrid RAG Architecture**:
1. **Keyword Retrieval (BM25)**: Preserves technical tokens and exact identifiers.
2. **Semantic Vector Search (Qdrant)**: Encodes conceptual relationships in 384-dimensional dense vector space.
3. **Reciprocal Rank Fusion (RRF)**: Merges disparate score distributions without requiring arbitrary weight scaling ($k=60$).
4. **Cross-Encoder Reranking**: Re-scores candidate passages based on query-passage proximity and section alignment.
5. **Grounded Generation**: Restricts LLM responses strictly to retrieved evidence with verifiable `[Doc: <id>, Section: <sec>]` citations, automatically abstaining when evidence is absent.

---

## 🏗️ Architecture Flow

```
                                      ┌────────────────────────┐
                                      │ User Technical Query   │
                                      └───────────┬────────────┘
                                                  │
                                    ┌─────────────┴─────────────┐
                                    ▼                           ▼
                         ┌────────────────────┐      ┌────────────────────┐
                         │   BM25 Retriever   │      │  Qdrant Vector DB  │
                         │ (Exact Identifiers)│      │(Semantic Embeddings│
                         └─────────┬──────────┘      └─────────┬──────────┘
                                   │                           │
                                   └─────────────┬─────────────┘
                                                 ▼
                                    ┌────────────────────────┐
                                    │ Reciprocal Rank Fusion │
                                    │    (RRF Smoothing k=60)│
                                    └────────────┬───────────┘
                                                 ▼
                                    ┌────────────────────────┐
                                    │ Cross-Encoder Reranker │
                                    └────────────┬───────────┘
                                                 ▼
                                    ┌────────────────────────┐
                                    │ Context Budget Builder │
                                    └────────────┬───────────┘
                                                 ▼
                                    ┌────────────────────────┐
                                    │ Grounded LLM Generator │
                                    └────────────┬───────────┘
                                                 ▼
                               ┌───────────────────────────────────┐
                               │ Answer + Verified Provenance Cites│
                               └───────────────────────────────────┘
```

---

## 📊 Empirical Retrieval Benchmark Results

Evaluated across the 41-question ground-truth benchmark (`data/eval_qa.json`):

| Retrieval Configuration | Recall@1 | Recall@3 | Recall@5 | MRR | nDCG@5 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **BM25 Only** | 0.9487 | 0.9744 | **1.0000** | 0.9667 | 1.9715 |
| **Qdrant Vector Only** | 0.8718 | 0.9487 | 0.9744 | 0.9167 | 1.6848 |
| **Hybrid RRF (Dual-Stream)** | 0.9231 | 1.0000 | **1.0000** | 0.9551 | 1.9010 |
| **Hybrid + Reranker** | 0.8718 | 0.9744 | 0.9744 | 0.9197 | 1.6843 |

*Full evaluation report available at [`docs/BENCHMARK_REPORT.md`](docs/BENCHMARK_REPORT.md).*

---

## ⚡ Quickstart

### 1. Clone & Install
```bash
git clone https://github.com/ftarunnnn/Hybrid-RAG-Over-a-Niche-Corpus.git
cd Hybrid-RAG-Over-a-Niche-Corpus
pip install -r requirements.txt
```

### 2. Ingest Corpus & Build Indices
```bash
# Ingest raw technical documents (Markdown, HTML, TXT, PDF)
python scripts/ingest_corpus.py

# Perform heading-aware chunking
python scripts/chunk_corpus.py

# Build BM25 and Qdrant Vector indices
python scripts/index_bm25.py
python scripts/index_vectors.py
```

### 3. Run Automated Tests & Evaluation
```bash
# Run complete test suite (32 tests passing)
pytest tests/ -v

# Run empirical benchmark
python scripts/run_evaluation.py
```

### 4. Launch Application
```bash
# Terminal 1: FastAPI Backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Streamlit Frontend UI
streamlit run frontend/streamlit_app.py
```
- **REST API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Web UI**: [http://localhost:8501](http://localhost:8501)

---

## 🐳 Docker Deployment

Deploy the entire stack (Qdrant + FastAPI + Streamlit) with a single command:

```bash
docker-compose up -d --build
```

Services exposed:
- **FastAPI**: `http://localhost:8000`
- **Streamlit**: `http://localhost:8501`
- **Qdrant**: `http://localhost:6333`

---

## 🛡️ Security Features
- **Prompt Injection Defense**: Scans retrieved passages and automatically redacts adversarial instructions (`Ignore previous instructions`, `System prompt override`).
- **Path Traversal Guard**: Strictly validates file paths to prevent unauthorized directory traversal outside `data/raw`.
- **Zero Hallucination Grounding**: Enforces strict citation mappings and automatically abstains when evidence is insufficient.

---

## 📁 Repository Structure
```
├── app/
│   ├── api/             # FastAPI routes (query, retrieve, health, ingest)
│   ├── ingestion/       # Loaders (PDF/HTML/MD), Text Cleaner, Chunker, Pipeline
│   ├── retrieval/       # BM25, Qdrant Vector Store, RRF Fusion, Reranker, Context Builder
│   ├── generation/      # LLM generator, citation validator, prompt templates
│   ├── evaluation/      # Metrics (Recall@k, MRR, nDCG) and benchmark runner
│   ├── security/        # Prompt injection & path traversal sanitizers
│   ├── config.py        # Central Pydantic Settings
│   └── main.py          # FastAPI application entrypoint
├── data/
│   ├── raw/             # 13 technical networking documents (MD, HTML, TXT, PDF)
│   ├── processed/       # Normalized documents.json & chunks.json
│   ├── corpus_manifest.json  # Manifest with SHA-256 hashes & licenses
│   ├── eval_qa.json     # 41 ground-truth evaluation questions
│   └── benchmark_results.json # Empirical benchmark metrics
├── docs/
│   ├── ARCHITECTURE.md  # System architecture & Mermaid diagrams
│   ├── PHASE_ROADMAP.md # 10 completed project phases
│   └── BENCHMARK_REPORT.md # Comparative retrieval benchmark
├── frontend/
│   └── streamlit_app.py # Interactive Streamlit dashboard
├── scripts/             # CLI runners for ingestion, chunking, indexing, evaluation
├── tests/               # 32 automated unit & integration tests
├── .github/workflows/   # GitHub Actions CI workflow
├── docker-compose.yml   # Multi-container orchestration
├── Dockerfile           # Multi-stage production container
└── requirements.txt     # Python dependencies
```

---

## 📜 License
MIT License. Open for educational and commercial portfolio use.