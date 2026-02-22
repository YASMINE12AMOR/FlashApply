from __future__ import annotations

import re
import unicodedata
from io import BytesIO
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfgen import canvas


REPLACEMENTS = {
    "•": "-",
    "●": "-",
    "▪": "-",
    "■": "-",
    "►": "-",
    "▸": "-",
    "–": "-",
    "—": "-",
    "¶": " ",
    "\uf0a7": "-",
    "\ufffd": "",
    "ﬁ": "fi",
    "ﬂ": "fl",
}


def _sanitize_line(line: str) -> str:
    line = unicodedata.normalize("NFKC", line)
    for src, dst in REPLACEMENTS.items():
        line = line.replace(src, dst)

    cleaned_chars: list[str] = []
    for ch in line:
        cat = unicodedata.category(ch)
        if cat.startswith("C"):  # control/private/surrogate chars
            continue
        if cat in {"So", "Sk"}:  # symbols that often render as black squares
            cleaned_chars.append(" ")
            continue
        # Keep letters/numbers and a safe set of punctuation only.
        if ch.isalnum() or ch in " .,;:!?%/()[]{}+-_'\"&@#|":
            cleaned_chars.append(ch)
        else:
            cleaned_chars.append(" ")

    cleaned = "".join(cleaned_chars)
    # Final safety pass: remove glyphs unsupported by PDF base fonts.
    cleaned = unicodedata.normalize("NFKD", cleaned).encode("ascii", "ignore").decode("ascii")
    # Remove common icon OCR artifacts from PDF extraction (e.g., "ap-arker").
    cleaned = re.sub(r"\bap-\s*arker\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bmap-\s*arker\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\blinkedin\s*icon\b", "linkedin", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bgithub\s*icon\b", "github", cleaned, flags=re.IGNORECASE)
    # Add spacing when words are accidentally merged (e.g., "arkerRennes").
    cleaned = re.sub(r"(?<=[a-zà-ÿ])(?=[A-ZÀ-ÖØ-Ý])", " ", cleaned)
    # Clean artifacts that appear before dates.
    cleaned = re.sub(r"(^|\s)[^\d\s-]+(?=\d{2}/\d{4})", r"\1", cleaned)
    cleaned = re.sub(r"(^|\s)-\s*(?=\d{2}/\d{4})", r"\1", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _sanitize_text(text: str) -> str:
    lines = [_sanitize_line(line) for line in text.splitlines()]
    return "\n".join([line for line in lines if line])


def _parse_cv_sections(text: str) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue

        is_bullet = line.startswith("-") or line.startswith("*")
        if not is_bullet and len(line) <= 80 and ":" not in line:
            current = {"title": line, "items": []}
            sections.append(current)
            continue

        if current is None:
            current = {"title": "Profile", "items": []}
            sections.append(current)

        value = line[1:].strip() if is_bullet else line
        if value:
            current["items"].append(value)

    return [s for s in sections if s.get("items")]


def _new_page() -> tuple[float, float, float, float]:
    width, height = A4
    margin_x = 14 * mm
    margin_y = 12 * mm
    return width, height, margin_x, margin_y


def _clip(value: str, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 1].rstrip() + "…"


def _extract_identity(sections: list[dict[str, Any]]) -> tuple[str, str, str, list[dict[str, Any]]]:
    identity_titles = {"identity & contact", "identity", "contact", "profile", "profil"}
    identity_items: list[str] = []
    remaining: list[dict[str, Any]] = []
    consumed = False

    for s in sections:
        title = s.get("title", "").strip().lower()
        items = s.get("items", [])
        if not consumed and title in identity_titles and items:
            identity_items.extend(items)
            consumed = True
            continue
        remaining.append(s)

    if not identity_items and sections:
        first = sections[0]
        if first.get("items"):
            identity_items = first["items"][:3]
            remaining = sections[1:] if len(sections) > 1 else []

    raw = " - ".join(identity_items).strip()
    if not raw:
        return "CANDIDATE", "", "", sections

    parts = [p.strip() for p in re.split(r"\s+-\s+|\s+\|\s+", raw) if p.strip()]
    if not parts:
        return "CANDIDATE", "", _clip(raw, 140), remaining

    name = _clip(parts[0].upper(), 40)
    role = _clip(parts[1], 50) if len(parts) > 1 else ""
    contact = _clip(" | ".join(parts[2:]) if len(parts) > 2 else raw, 180)
    return name, role, contact, remaining


def _draw_photo(
    pdf: canvas.Canvas,
    photo_bytes: bytes | None,
    x: float,
    y_top: float,
    w: float,
    h: float,
) -> None:
    if not photo_bytes:
        return
    try:
        image = ImageReader(BytesIO(photo_bytes))
        pdf.drawImage(image, x, y_top - h, width=w, height=h, preserveAspectRatio=True, mask="auto")
    except Exception:
        return


def _draw_blue_header(
    pdf: canvas.Canvas,
    width: float,
    height: float,
    margin_x: float,
    name: str,
    role: str,
    contact: str,
    include_photo: bool,
    photo_bytes: bytes | None,
) -> float:
    band_h = 28 * mm
    band_y = height - band_h

    pdf.setFillColorRGB(0.08, 0.24, 0.49)
    pdf.rect(0, band_y, width, band_h, stroke=0, fill=1)

    text_x = margin_x
    if include_photo and photo_bytes:
        _draw_photo(pdf, photo_bytes, width - margin_x - 18 * mm, height - 4 * mm, 16 * mm, 20 * mm)

    pdf.setFillColorRGB(1, 1, 1)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(text_x, height - 9 * mm, _clip(name, 38))

    if role:
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(text_x, height - 14 * mm, _clip(role, 62))

    if contact:
        pdf.setFont("Helvetica", 8.5)
        pdf.drawString(text_x, height - 19 * mm, _clip(contact, 120))

    return band_y - 6 * mm


def _draw_section(
    pdf: canvas.Canvas,
    section: dict[str, Any],
    x: float,
    y: float,
    width: float,
    margin_bottom: float,
    line_h: float,
    title_upper: bool,
) -> float:
    title = section["title"].strip()
    if title_upper:
        title = title.upper()
    items = section["items"]

    if y < margin_bottom + 22:
        return -1

    pdf.setFillColorRGB(0.08, 0.2, 0.36)
    pdf.setFont("Helvetica-Bold", 10.8)
    pdf.drawString(x, y, _clip(title, 60))
    y -= 4
    pdf.setLineWidth(0.8)
    pdf.setStrokeColorRGB(0.16, 0.34, 0.62)
    pdf.line(x, y, x + width, y)
    y -= 8

    pdf.setFillColorRGB(0.08, 0.08, 0.08)
    pdf.setFont("Helvetica", 9.4)

    for item in items:
        wrapped = simpleSplit(f"- {item}", "Helvetica", 9.4, width)
        for line in wrapped:
            if y < margin_bottom + 10:
                return -1
            pdf.drawString(x, y, line)
            y -= line_h
    return y - 4


def _draw_vertical_single_column(
    pdf: canvas.Canvas,
    sections: list[dict[str, Any]],
    include_photo: bool,
    profile_image_bytes: bytes | None,
) -> None:
    width, height, margin_x, margin_y = _new_page()
    name, role, contact, body_sections = _extract_identity(sections)
    y = _draw_blue_header(pdf, width, height, margin_x, name, role, contact, include_photo, profile_image_bytes)

    text_width = width - (2 * margin_x)
    for section in body_sections:
        y = _draw_section(pdf, section, margin_x, y, text_width, margin_y, 10.5, title_upper=False)
        if y < 0:
            break


def _draw_horizontal_single_column(
    pdf: canvas.Canvas,
    sections: list[dict[str, Any]],
    include_photo: bool,
    profile_image_bytes: bytes | None,
) -> None:
    width, height, margin_x, margin_y = _new_page()
    name, role, contact, body_sections = _extract_identity(sections)
    y = _draw_blue_header(pdf, width, height, margin_x, name, role, contact, include_photo, profile_image_bytes)

    text_width = width - (2 * margin_x)
    for section in body_sections:
        y = _draw_section(pdf, section, margin_x, y, text_width, margin_y, 10.5, title_upper=True)
        if y < 0:
            break


def _draw_two_vertical_columns(
    pdf: canvas.Canvas,
    sections: list[dict[str, Any]],
    include_photo: bool,
    profile_image_bytes: bytes | None,
) -> None:
    width, height, margin_x, margin_y = _new_page()
    name, role, contact, body_sections = _extract_identity(sections)
    y_top = _draw_blue_header(pdf, width, height, margin_x, name, role, contact, include_photo, profile_image_bytes)

    left_w = 60 * mm
    gap = 8 * mm
    right_w = width - (2 * margin_x) - left_w - gap
    left_x = margin_x
    right_x = margin_x + left_w + gap

    left_titles = {
        "profile", "profil", "skills", "competences", "languages", "langues",
        "certifications", "interests", "references", "distinctions"
    }

    left_sections: list[dict[str, Any]] = []
    right_sections: list[dict[str, Any]] = []
    for s in body_sections:
        t = s["title"].lower().strip()
        if t in left_titles:
            left_sections.append(s)
        else:
            right_sections.append(s)

    pdf.setStrokeColorRGB(0.82, 0.82, 0.82)
    pdf.setLineWidth(1)
    pdf.line(right_x - gap / 2, margin_y, right_x - gap / 2, y_top + 2)

    y_left = y_top
    for section in left_sections:
        y_left = _draw_section(pdf, section, left_x, y_left, left_w, margin_y, 10.2, title_upper=True)
        if y_left < 0:
            break

    y_right = y_top
    for section in right_sections:
        y_right = _draw_section(pdf, section, right_x, y_right, right_w, margin_y, 10.2, title_upper=True)
        if y_right < 0:
            break


def text_to_pdf_bytes(
    text: str,
    title: str = "Adapted CV",
    country: str = "",
    model_info: str = "",
    layout_mode: str = "vertical_single_column",
    show_header: bool = False,
    include_photo: bool = False,
    profile_image_bytes: bytes | None = None,
) -> bytes:
    """Generate one-page country-formatted CV PDF from text."""
    del title, country, model_info, show_header

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    clean_text = _sanitize_text(text)
    sections = _parse_cv_sections(clean_text)
    if not sections:
        sections = [{"title": "Profile", "items": [line for line in clean_text.splitlines() if line.strip()]}]

    if layout_mode == "horizontal_single_column":
        _draw_horizontal_single_column(pdf, sections, include_photo, profile_image_bytes)
    elif layout_mode == "two_vertical_columns":
        _draw_two_vertical_columns(pdf, sections, include_photo, profile_image_bytes)
    else:
        _draw_vertical_single_column(pdf, sections, include_photo, profile_image_bytes)

    pdf.save()
    return buffer.getvalue()
