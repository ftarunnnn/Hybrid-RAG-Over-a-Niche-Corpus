"""
Context Builder and Budget Optimization.
Fits the highest-relevance evidence passages within a strict token budget.
Deduplicates near-identical passages, maintains citation identifiers,
and formats grounded evidence blocks for LLM consumption.
"""
from typing import List, Dict, Any, Tuple
import re


class ContextBuilder:
    """Selects and formats evidence passages within token constraints."""

    def __init__(self, max_context_tokens: int = 2500, chars_per_token: float = 4.0):
        self.max_tokens = max_context_tokens
        self.max_chars = int(max_context_tokens * chars_per_token)

    def _is_redundant(self, new_text: str, existing_texts: List[str], threshold: float = 0.75) -> bool:
        """Jaccard word-overlap redundancy check to avoid repeating duplicate paragraphs."""
        new_words = set(re.findall(r"\w+", new_text.lower()))
        if not new_words:
            return False

        for existing in existing_texts:
            ex_words = set(re.findall(r"\w+", existing.lower()))
            if not ex_words:
                continue
            intersection = len(new_words.intersection(ex_words))
            union = len(new_words.union(ex_words))
            if union > 0 and (intersection / union) > threshold:
                return True
        return False

    def build_context(self, passages: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
        """
        Builds a compact, cited context string.
        Returns:
            - context_string: Formatted text for LLM prompt
            - selected_passages: List of chunks that fit the budget
            - stats: Token and chunk counts
        """
        selected = []
        accepted_texts = []
        total_chars = 0

        for p in passages:
            content = p.get("content", "").strip()
            if not content:
                continue

            # Redundancy check
            if self._is_redundant(content, accepted_texts):
                continue

            # Check character budget
            est_chars = len(content) + 200  # including header boilerplate
            if total_chars + est_chars > self.max_chars and selected:
                break

            selected.append(p)
            accepted_texts.append(content)
            total_chars += est_chars

        # Build structured context block
        formatted_blocks = []
        for idx, item in enumerate(selected, 1):
            doc_id = item.get("doc_id", "unknown")
            chunk_id = item.get("chunk_id", f"chunk_{idx}")
            title = item.get("title", "")
            section = item.get("section", "General")
            source_url = item.get("source_url", "")
            content = item.get("content", "").strip()

            block = (
                f"--- EVIDENCE [{idx}] ---\n"
                f"Source ID: {chunk_id}\n"
                f"Document: {doc_id} ({title})\n"
                f"Section: {section}\n"
                f"Source URL: {source_url}\n"
                f"Passage Content:\n{content}\n"
            )
            formatted_blocks.append(block)

        context_string = "\n".join(formatted_blocks)
        stats = {
            "selected_chunks": len(selected),
            "estimated_tokens": int(total_chars / 4.0),
            "max_tokens_budget": self.max_tokens,
            "dropped_due_to_budget": max(0, len(passages) - len(selected))
        }

        return context_string, selected, stats
