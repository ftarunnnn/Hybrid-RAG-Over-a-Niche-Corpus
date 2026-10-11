"""
Text cleaning and normalization module for technical networking documents.
Preserves technical symbols, CLI syntax, IP addresses, subnets, tables, and code blocks
while stripping repetitive headers, footers, trailing whitespaces, and extraction artifacts.
"""
import re


class TextCleaner:
    """Normalizes raw document text while preserving technical structures."""

    @staticmethod
    def remove_extraction_artifacts(text: str) -> str:
        """Removes null bytes, form feeds, and non-printable control characters."""
        text = text.replace("\x00", "")
        text = text.replace("\x0c", "\n")  # Page breaks to newlines
        text = text.replace("\r\n", "\n")  # Normalize line endings
        text = text.replace("\r", "\n")
        return text

    @staticmethod
    def normalize_excessive_whitespace(text: str) -> str:
        """Collapses 3+ consecutive newlines into 2, without destroying code block indentation."""
        lines = [line.rstrip() for line in text.split("\n")]
        cleaned_text = "\n".join(lines)
        # Collapse 3 or more empty lines to double newline
        cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)
        return cleaned_text.strip()

    @staticmethod
    def strip_page_headers_footers(text: str) -> str:
        """Removes typical page number markers or repeated running headers."""
        # Remove patterns like '--- Page X ---' or '[Page 12]'
        text = re.sub(r"--- Page \d+ ---\n?", "", text)
        text = re.sub(r"\[Page \d+\]", "", text)
        return text

    @classmethod
    def clean(cls, raw_text: str) -> str:
        """Performs full cleaning pipeline."""
        if not raw_text:
            return ""
        text = cls.remove_extraction_artifacts(raw_text)
        text = cls.strip_page_headers_footers(text)
        text = cls.normalize_excessive_whitespace(text)
        return text
