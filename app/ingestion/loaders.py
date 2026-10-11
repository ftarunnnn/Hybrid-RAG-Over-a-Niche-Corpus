"""
Multi-format document loaders for PDF, Markdown, HTML, and Text.
Preserves metadata, document structures, and clean text representations.
"""
from pathlib import Path
from typing import Dict, Any, Optional
import pymupdf  # PyMuPDF
from bs4 import BeautifulSoup


class DocumentLoaderError(Exception):
    """Raised when a document fails to load or parse."""
    pass


class DocumentLoader:
    """Dispatches document loading based on file extension."""

    @staticmethod
    def load_markdown(file_path: Path) -> Dict[str, Any]:
        """Loads and reads Markdown file content."""
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        return {
            "raw_text": text,
            "format": "markdown",
            "page_count": 1
        }

    @staticmethod
    def load_text(file_path: Path) -> Dict[str, Any]:
        """Loads and reads plain text file content."""
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        return {
            "raw_text": text,
            "format": "text",
            "page_count": 1
        }

    @staticmethod
    def load_html(file_path: Path) -> Dict[str, Any]:
        """Extracts structured text from HTML, preserving headings, code, and lists."""
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Remove script and style elements
        for element in soup(["script", "style"]):
            element.decompose()

        # Extract text with newlines
        body = soup.find("body") or soup
        text = body.get_text(separator="\n", strip=True)
        title = soup.title.string.strip() if soup.title and soup.title.string else file_path.stem

        return {
            "raw_text": text,
            "format": "html",
            "html_title": title,
            "page_count": 1
        }

    @staticmethod
    def load_pdf(file_path: Path) -> Dict[str, Any]:
        """Loads PDF document using PyMuPDF, preserving page boundaries and text."""
        try:
            doc = pymupdf.open(file_path)
            pages_text = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text("text")
                pages_text.append(f"--- Page {page_num + 1} ---\n" + page_text)
            full_text = "\n\n".join(pages_text)
            page_count = len(doc)
            doc.close()
            return {
                "raw_text": full_text,
                "format": "pdf",
                "page_count": page_count
            }
        except Exception as e:
            raise DocumentLoaderError(f"Failed to parse PDF {file_path}: {e}")

    @classmethod
    def load_file(cls, file_path: str | Path) -> Dict[str, Any]:
        """Loads a file by auto-detecting its extension."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        ext = path.suffix.lower()
        if ext in [".md", ".markdown"]:
            data = cls.load_markdown(path)
        elif ext in [".txt", ".log", ".cfg"]:
            data = cls.load_text(path)
        elif ext in [".html", ".htm"]:
            data = cls.load_html(path)
        elif ext == ".pdf":
            data = cls.load_pdf(path)
        else:
            raise DocumentLoaderError(f"Unsupported file format: {ext}")

        data["filename"] = path.name
        data["doc_id"] = path.stem
        data["filepath"] = str(path).replace("\\", "/")
        return data
