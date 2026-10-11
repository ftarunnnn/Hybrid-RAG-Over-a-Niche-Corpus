"""
BM25 Keyword Retrieval Engine.
Specialized for networking corpus with technical tokenizer preserving
IP addresses, CIDR notation, RFC identifiers, port numbers, flags, and CLI commands.
Supports serialization to disk and standalone scoring.
"""
from typing import List, Dict, Any, Optional
import re
import pickle
from pathlib import Path
from rank_bm25 import BM25Okapi
import logging

logger = logging.getLogger("bm25_retrieval")


class TechnicalBM25Retriever:
    """Keyword search engine powered by BM25Okapi with network-aware tokenization."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.bm25: Optional[BM25Okapi] = None
        self.corpus_chunks: List[Dict[str, Any]] = []
        self.tokenized_corpus: List[List[str]] = []

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Preserves networking tokens such as TCP/443, 802.1Q, 192.168.1.0/24, SYN-ACK."""
        text = text.lower()
        # Regex captures:
        # 1. CIDR notation / IP prefixes: e.g. 192.168.1.0/24 or /26
        # 2. Port protocols: e.g. tcp/443, udp/53
        # 3. Protocol flags and hyphens: e.g. syn-ack, rfc-1035, 802.1q
        # 4. Standard alphanumeric words: e.g. subnetting, router, vlan
        tokens = re.findall(
            r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?:/\d{1,2})?\b|"  # IP/CIDR
            r"/\d{1,2}\b|"                                             # /24, /32
            r"[a-z0-9_\-\.\/]+",                                      # Technical identifiers
            text
        )
        # Strip trailing punctuation while keeping structural tokens
        cleaned_tokens = []
        for t in tokens:
            t = t.strip(".,;:()[]\"'")
            if len(t) > 1:
                cleaned_tokens.append(t)
        return cleaned_tokens

    def fit(self, chunks: List[Dict[str, Any]]):
        """Builds BM25 index over the chunks collection."""
        self.corpus_chunks = chunks
        self.tokenized_corpus = []

        for chunk in chunks:
            # Combine title, section, and content for rich keyword surface
            full_text = f"{chunk.get('title', '')} {chunk.get('section', '')} {chunk.get('content', '')}"
            tokens = self.tokenize(full_text)
            self.tokenized_corpus.append(tokens)

        self.bm25 = BM25Okapi(self.tokenized_corpus, k1=self.k1, b=self.b, epsilon=0.25)
        logger.info(f"Built BM25 index over {len(chunks)} chunks.")

    def search(self, query: str, top_k: int = 5,
               topic_filter: Optional[str] = None,
               doc_id_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Searches index using BM25 and returns ranked results with scores."""
        if not self.bm25 or not self.corpus_chunks:
            return []

        query_tokens = self.tokenize(query)
        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)
        scored_pairs = []
        for idx, score in enumerate(scores):
            doc_tokens = set(self.tokenized_corpus[idx])
            matches = [t for t in query_tokens if t in doc_tokens]
            if matches:
                effective_score = float(score) if score > 0 else float(len(matches))
                scored_pairs.append((idx, effective_score))

        # Sort descending by score
        scored_pairs.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in scored_pairs:
            chunk = self.corpus_chunks[idx]

            # Apply metadata filters if specified
            if topic_filter and chunk.get("topic") != topic_filter:
                continue
            if doc_id_filter and chunk.get("doc_id") != doc_id_filter:
                continue

            results.append({
                "chunk_id": chunk["chunk_id"],
                "doc_id": chunk["doc_id"],
                "title": chunk.get("title", ""),
                "topic": chunk.get("topic", ""),
                "section": chunk.get("section", ""),
                "content": chunk["content"],
                "source_url": chunk.get("source_url", ""),
                "token_count": chunk.get("token_count", 0),
                "score": float(score),
                "retriever": "bm25"
            })

            if len(results) >= top_k:
                break

        return results

    def save(self, filepath: str = "data/bm25_index.pkl"):
        """Serializes BM25 model and chunk references to disk."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({
                "k1": self.k1,
                "b": self.b,
                "chunks": self.corpus_chunks,
                "tokenized_corpus": self.tokenized_corpus,
                "bm25": self.bm25
            }, f)
        logger.info(f"BM25 index saved to {filepath}.")

    @classmethod
    def load(cls, filepath: str = "data/bm25_index.pkl") -> "TechnicalBM25Retriever":
        """Deserializes BM25 model from disk."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"BM25 index file not found: {filepath}")

        with open(path, "rb") as f:
            data = pickle.load(f)

        instance = cls(k1=data.get("k1", 1.5), b=data.get("b", 0.75))
        instance.corpus_chunks = data["chunks"]
        instance.tokenized_corpus = data["tokenized_corpus"]
        instance.bm25 = data["bm25"]
        return instance
