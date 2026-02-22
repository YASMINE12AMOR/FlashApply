from __future__ import annotations

import io
import re
import unicodedata
from typing import Optional

from pypdf import PdfReader


def _clean_line(line: str) -> str:
    line = unicodedata.normalize("NFKC", line)
    line = (
        line.replace("•", "-")
        .replace("●", "-")
        .replace("▪", "-")
        .replace("■", " ")
        .replace("¶", " ")
        .replace("\ufffd", " ")
    )

    cleaned_chars: list[str] = []
    for ch in line:
        cat = unicodedata.category(ch)
        if cat.startswith("C"):
            continue
        if cat in {"So", "Sk"}:
            cleaned_chars.append(" ")
            continue
        cleaned_chars.append(ch)
    line = "".join(cleaned_chars)
    # Final safety pass for PDF extraction artifacts/glyphs.
    line = unicodedata.normalize("NFKD", line).encode("ascii", "ignore").decode("ascii")

    line = re.sub(r"^\s*(?:ap|map)?-?\s*arker\S*\s+", "", line, flags=re.IGNORECASE)
    line = re.sub(r"^\s*\S*arker\S*\s+", "", line, flags=re.IGNORECASE)
    line = re.sub(r"^\s*[-|:;,._]+\s*", "", line)
    line = re.sub(r"(?<=[a-zà-ÿ])(?=[A-ZÀ-ÖØ-Ý])", " ", line)
    line = re.sub(r"\s+", " ", line).strip()
    return line


def clean_extracted_text(text: str) -> str:
    lines = [_clean_line(line) for line in text.splitlines()]
    return "\n".join([line for line in lines if line])


def extract_text_from_pdf_bytes(data: bytes) -> str:
    """Extract plain text from a PDF byte payload."""
    reader = PdfReader(io.BytesIO(data))
    chunks = []
    for page in reader.pages:
        chunks.append(page.extract_text() or "")
    return clean_extracted_text("\n".join(chunks).strip())


def extract_text(file_bytes: Optional[bytes], filename: Optional[str], fallback_text: str = "") -> str:
    """Extract text from uploaded file or fallback textarea text."""
    if file_bytes and filename:
        lower = filename.lower()
        if lower.endswith(".pdf"):
            return extract_text_from_pdf_bytes(file_bytes)
        if lower.endswith(".txt"):
            return clean_extracted_text(file_bytes.decode("utf-8", errors="ignore").strip())
    return clean_extracted_text(fallback_text.strip())
