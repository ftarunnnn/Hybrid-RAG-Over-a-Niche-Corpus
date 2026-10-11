"""
LLM Generation Engine.
Supports local Ollama, OpenAI-compatible APIs, and an Extractive Grounded Synthesizer
for deterministic, offline-capable verification.
"""
from typing import List, Dict, Any, Optional
import os
import re
import httpx
from app.generation.prompts import GROUNDED_SYSTEM_PROMPT, build_user_prompt
from app.generation.citations import CitationValidator
import logging

logger = logging.getLogger("llm_generation")

STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "in", "on", "at", "by", "for",
    "with", "about", "against", "between", "into", "through", "during", "before",
    "after", "above", "below", "to", "from", "up", "down", "of", "and", "or",
    "what", "which", "who", "when", "where", "why", "how", "can", "could", "should",
    "would", "do", "does", "did", "have", "has", "had", "this", "that", "these", "those"
}


class LLMGenerator:
    """Manages prompt formatting and LLM execution."""

    def __init__(self, provider: str = "auto",
                 api_key: Optional[str] = None,
                 model_name: Optional[str] = None,
                 api_base_url: Optional[str] = None):
        self.provider = provider
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
        self.model_name = model_name or os.getenv("LLM_MODEL", "llama3:latest")
        self.api_base_url = api_base_url or os.getenv("LLM_BASE_URL", "http://localhost:11434")

    def _generate_extractive(self, query: str, passages: List[Dict[str, Any]]) -> str:
        """
        Extractive grounded generator: finds the most salient sentences in retrieved evidence
        and synthesizes a grounded answer with citations, or declares insufficient evidence.
        """
        if not passages:
            return "I do not have sufficient evidence in the networking corpus to answer this question."

        q_words = {w for w in re.findall(r"[a-z0-9_\-\.\/]+", query.lower()) if w not in STOP_WORDS and len(w) >= 2}
        if not q_words:
            return "I do not have sufficient evidence in the networking corpus to answer this question."

        scored_sentences = []

        for p in passages:
            doc_id = p.get("doc_id", "doc")
            sec = p.get("section", "General")
            content = p.get("content", "")

            lines = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", content) if len(s.strip()) > 15]
            for line in lines:
                l_words = {w for w in re.findall(r"[a-z0-9_\-\.\/]+", line.lower()) if w not in STOP_WORDS and len(w) >= 2}
                common = q_words.intersection(l_words)
                if len(common) >= 1:
                    scored_sentences.append((len(common), line, doc_id, sec))

        if not scored_sentences:
            return "I do not have sufficient evidence in the networking corpus to answer this question."

        # Sort sentences by keyword overlap with query
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        top_sentences = scored_sentences[:3]

        # Assemble grounded response with citations
        answer_parts = []
        for _, text, doc_id, sec in top_sentences:
            clean_s = text.lstrip("-*# ").strip()
            citation = f"[Doc: {doc_id}, Section: {sec}]"
            answer_parts.append(f"{clean_s} {citation}")

        return "\n\n".join(answer_parts)

    def _call_ollama(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Calls local Ollama instance with ultra-fast connection check."""
        try:
            url = f"{self.api_base_url}/api/generate"
            payload = {
                "model": self.model_name,
                "prompt": f"{system_prompt}\n\n{user_prompt}",
                "stream": False
            }
            # Fast 0.3s connect timeout so offline systems don't stall
            with httpx.Client(timeout=httpx.Timeout(10.0, connect=0.3)) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    return res.json().get("response", "").strip()
        except Exception:
            pass
        return None

    def _call_openai_compatible(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Calls OpenAI-compatible endpoint if API key is present."""
        if not self.api_key:
            return None
        try:
            url = f"{self.api_base_url}/v1/chat/completions"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.0
            }
            with httpx.Client(timeout=httpx.Timeout(20.0, connect=2.0)) as client:
                res = client.post(url, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return data["choices"][0]["message"]["content"].strip()
        except Exception:
            pass
        return None

    def generate(self, query: str, context_text: str,
                 selected_passages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Executes end-to-end generation with citation validation.
        """
        user_prompt = build_user_prompt(query, context_text)
        answer = None

        if self.provider == "ollama":
            answer = self._call_ollama(GROUNDED_SYSTEM_PROMPT, user_prompt)
        elif self.provider in ["openai", "hosted"]:
            answer = self._call_openai_compatible(GROUNDED_SYSTEM_PROMPT, user_prompt)
        elif self.provider == "auto":
            if self.api_key:
                answer = self._call_openai_compatible(GROUNDED_SYSTEM_PROMPT, user_prompt)
            if not answer:
                answer = self._call_ollama(GROUNDED_SYSTEM_PROMPT, user_prompt)

        # Fallback to deterministic grounded extractive synthesis
        if not answer:
            answer = self._generate_extractive(query, selected_passages)

        # Validate citations
        citation_info = CitationValidator.verify_citations(answer, selected_passages)

        return {
            "answer": answer,
            "is_grounded": citation_info["is_valid"],
            "abstention": citation_info.get("abstention", False),
            "citations": citation_info["valid_citations"],
            "citation_precision": citation_info["citation_precision"],
            "verification_details": citation_info
        }
