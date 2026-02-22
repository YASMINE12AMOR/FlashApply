import mimetypes

import docx
import pdfplumber
import pytesseract
from PIL import Image


def extract_cv_text(file_path: str) -> str:
    mime, _ = mimetypes.guess_type(file_path)

    if mime == "application/pdf":
        chunks = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                chunks.append(page.extract_text() or "")
        return "\n".join(chunks).strip()

    if mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = docx.Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs).strip()

    if mime == "text/plain":
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read().strip()

    if mime and mime.startswith("image"):
        with Image.open(file_path) as image:
            return pytesseract.image_to_string(image).strip()

    raise ValueError(f"Unsupported CV file format: {mime or 'unknown'}")
