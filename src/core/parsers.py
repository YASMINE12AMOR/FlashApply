from __future__ import annotations

import io
from typing import Optional

from pypdf import PdfReader


def extract_text_from_pdf_bytes(data: bytes) -> str:
    """Extract plain text from a PDF byte payload."""
    reader = PdfReader(io.BytesIO(data))
    chunks = []
    for page in reader.pages:
        chunks.append(page.extract_text() or "")
    return "\n".join(chunks).strip()


def extract_text(file_bytes: Optional[bytes], filename: Optional[str], fallback_text: str = "") -> str:
    """Extract text from uploaded file or fallback textarea text."""
    if file_bytes and filename:
        lower = filename.lower()
        if lower.endswith(".pdf"):
            return extract_text_from_pdf_bytes(file_bytes)
        if lower.endswith(".txt"):
            return file_bytes.decode("utf-8", errors="ignore").strip()
    return fallback_text.strip()
