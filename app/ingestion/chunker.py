"""
Heading-aware, structure-preserving text chunker for technical corpora.
Respects markdown headings, code blocks, configuration syntax, and table integrity.
Attaches full provenance metadata: chunk_id, doc_id, section, token counts, and source URLs.
"""
from typing import List, Dict, Any, Optional
import re
import hashlib


class HeadingAwareChunker:
    """Chunks structured technical documents by semantic headings and token boundaries."""

    def __init__(self, target_chunk_tokens: int = 500, overlap_tokens: int = 50,
                 chars_per_token: float = 4.0):
        self.target_tokens = target_chunk_tokens
        self.overlap_tokens = overlap_tokens
        self.chars_per_token = chars_per_token
        self.target_chars = int(target_chunk_tokens * chars_per_token)
        self.overlap_chars = int(overlap_tokens * chars_per_token)

    def _split_into_sections(self, text: str) -> List[Dict[str, str]]:
        """Splits markdown/structured text along header boundaries (#, ##, ###, ====, ----)."""
        lines = text.split("\n")
        sections = []
        current_header = "Introduction / Overview"
        current_lines = []

        header_regex = re.compile(r"^(#{1,4})\s+(.+)$")
        section_divider_regex = re.compile(r"^(-{3,}|={3,})\s*$")

        i = 0
        while i < len(lines):
            line = lines[i]
            header_match = header_regex.match(line)

            if header_match:
                if current_lines:
                    sections.append({
                        "section": current_header,
                        "content": "\n".join(current_lines).strip()
                    })
                    current_lines = []
                current_header = header_match.group(2).strip()
                current_lines.append(line)
            elif section_divider_regex.match(line) and i + 1 < len(lines):
                # Check if next line looks like a major section header
                candidate = lines[i + 1].strip()
                if candidate and not section_divider_regex.match(candidate):
                    if current_lines:
                        sections.append({
                            "section": current_header,
                            "content": "\n".join(current_lines).strip()
                        })
                        current_lines = []
                    current_header = candidate
                    i += 1  # Skip candidate as it's the header
            else:
                current_lines.append(line)
            i += 1

        if current_lines:
            sections.append({
                "section": current_header,
                "content": "\n".join(current_lines).strip()
            })

        return [s for s in sections if s["content"]]

    def _split_section_content(self, section_text: str) -> List[str]:
        """Splits large section text into paragraphs, preserving code blocks and tables."""
        # Detect fenced code blocks
        blocks = []
        in_code_block = False
        current_block = []

        for line in section_text.split("\n"):
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                current_block.append(line)
                if not in_code_block:
                    blocks.append("\n".join(current_block))
                    current_block = []
            elif in_code_block:
                current_block.append(line)
            elif not line.strip() and current_block:
                blocks.append("\n".join(current_block))
                current_block = []
            else:
                current_block.append(line)

        if current_block:
            blocks.append("\n".join(current_block))

        # Merge blocks into target size
        chunks = []
        accum = []
        accum_len = 0

        for b in blocks:
            b_len = len(b)
            if accum_len + b_len > self.target_chars and accum:
                chunks.append("\n\n".join(accum))
                # Carry over overlap if possible
                overlap_text = accum[-1] if len(accum[-1]) < self.overlap_chars else ""
                accum = [overlap_text, b] if overlap_text else [b]
                accum_len = sum(len(x) for x in accum)
            else:
                accum.append(b)
                accum_len += b_len

        if accum:
            chunks.append("\n\n".join(accum))

        return chunks

    def chunk_document(self, doc_record: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Processes a single document record into richly annotated chunks."""
        text = doc_record.get("cleaned_text", "")
        doc_id = doc_record.get("doc_id", "doc")
        title = doc_record.get("title", "")
        topic = doc_record.get("topic", "Networking")
        source_url = doc_record.get("source_url", "")
        version = doc_record.get("version", "1.0")

        sections = self._split_into_sections(text)
        chunks = []
        chunk_idx = 0
        char_offset = 0

        for sec in sections:
            section_name = sec["section"]
            sec_chunks = self._split_section_content(sec["content"])

            for sc in sec_chunks:
                sc = sc.strip()
                if not sc:
                    continue

                chunk_id = f"{doc_id}#chunk-{chunk_idx:03d}"
                token_count = max(1, int(len(sc) / self.chars_per_token))

                chunk_entry = {
                    "chunk_id": chunk_id,
                    "doc_id": doc_id,
                    "title": title,
                    "topic": topic,
                    "section": section_name,
                    "content": sc,
                    "token_count": token_count,
                    "char_start": char_offset,
                    "char_end": char_offset + len(sc),
                    "source_url": source_url,
                    "version": version
                }
                chunks.append(chunk_entry)
                char_offset += len(sc)
                chunk_idx += 1

        return chunks

    def chunk_corpus(self, docs_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Chunks an entire collection of ingested documents."""
        all_chunks = []
        for doc in docs_list:
            all_chunks.extend(self.chunk_document(doc))
        return all_chunks
