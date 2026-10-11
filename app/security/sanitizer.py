"""
Security and Input Sanitization Module.
Protects the RAG system against:
1. Indirect Prompt Injection in retrieved context documents.
2. Path Traversal attacks during document ingestion.
3. Query flood and malformed input vectors.
"""
from pathlib import Path
from typing import Tuple, List, Optional
import re


class SecuritySanitizer:
    """Security filters and validations for RAG pipelines."""

    # Patterns commonly used in prompt injection attempts
    PROMPT_INJECTION_PATTERNS = [
        re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions", re.IGNORECASE),
        re.compile(r"system\s+prompt\s+override", re.IGNORECASE),
        re.compile(r"you\s+are\s+now\s+in\s+developer\s+mode", re.IGNORECASE),
        re.compile(r"print\s+(your\s+)?(system\s+prompt|secret|instructions)", re.IGNORECASE),
        re.compile(r"reveal\s+internal\s+directive", re.IGNORECASE),
        re.compile(r"<\s*script[^>]*>", re.IGNORECASE),
        re.compile(r"\{\{.*\}\}", re.IGNORECASE)  # Template injection
    ]

    @classmethod
    def sanitize_retrieved_context(cls, text: str) -> Tuple[str, bool]:
        """
        Scans retrieved document passage for prompt injection attempts.
        Neutralizes detected attack vectors by redaction.
        Returns: (sanitized_text, was_injection_detected)
        """
        detected = False
        sanitized = text

        for pattern in cls.PROMPT_INJECTION_PATTERNS:
            if pattern.search(sanitized):
                detected = True
                sanitized = pattern.sub("[REDACTED_SECURITY_RISK]", sanitized)

        return sanitized, detected

    @classmethod
    def validate_ingestion_path(cls, file_path: str | Path, base_dir: str | Path = "data/raw") -> Path:
        """
        Validates that a file path resides strictly inside the authorized base directory,
        preventing directory traversal attacks (e.g., ../../etc/passwd).
        """
        base = Path(base_dir).resolve()
        target = Path(file_path).resolve()

        # Check if target is child of base
        try:
            target.relative_to(base)
        except ValueError:
            raise PermissionError(f"Security Violation: Path traversal outside authorized directory: {file_path}")

        # Check extension
        allowed_extensions = {".md", ".markdown", ".txt", ".html", ".htm", ".pdf"}
        if target.suffix.lower() not in allowed_extensions:
            raise ValueError(f"Security Violation: Unauthorized file type: {target.suffix}")

        return target

    @classmethod
    def sanitize_query(cls, query: str, max_length: int = 1000) -> str:
        """Sanitizes user query: bounds length and removes non-printable control characters."""
        if not query:
            return ""
        # Strip control characters
        cleaned = "".join(ch for ch in query if ch.isprintable() or ch in "\n\t")
        return cleaned[:max_length].strip()
