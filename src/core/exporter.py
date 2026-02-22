from __future__ import annotations

from io import BytesIO
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfgen import canvas


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


def _new_page(pdf: canvas.Canvas) -> tuple[float, float, float, float]:
    width, height = A4
    margin_x = 14 * mm
    margin_y = 14 * mm
    return width, height, margin_x, margin_y


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


def _draw_section_single_column(
    pdf: canvas.Canvas,
    section: dict[str, Any],
    x: float,
    y: float,
    width: float,
    margin_bottom: float,
    line_h: float,
) -> float:
    title = section["title"]
    items = section["items"]

    if y < margin_bottom + 30:
        pdf.showPage()
        _, h, _, _ = _new_page(pdf)
        y = h - 14 * mm

    pdf.setFont("Helvetica-Bold", 12)
    pdf.setFillColorRGB(0.12, 0.2, 0.36)
    pdf.drawString(x, y, title)
    y -= 7
    pdf.setLineWidth(0.8)
    pdf.line(x, y, x + width, y)
    y -= 12

    pdf.setFont("Helvetica", 10.5)
    pdf.setFillColorRGB(0.08, 0.08, 0.08)
    for item in items:
        wrapped = simpleSplit(f"- {item}", "Helvetica", 10.5, width)
        needed = max(1, len(wrapped)) * line_h
        if y - needed < margin_bottom:
            pdf.showPage()
            _, h, _, _ = _new_page(pdf)
            y = h - 14 * mm
            pdf.setFont("Helvetica-Bold", 12)
            pdf.setFillColorRGB(0.12, 0.2, 0.36)
            pdf.drawString(x, y, title + " (cont.)")
            y -= 14
            pdf.setFont("Helvetica", 10.5)
            pdf.setFillColorRGB(0.08, 0.08, 0.08)
        for line in wrapped:
            pdf.drawString(x, y, line)
            y -= line_h
    y -= 8
    return y


def _draw_horizontal_single_column(
    pdf: canvas.Canvas,
    sections: list[dict[str, Any]],
    include_photo: bool,
    profile_image_bytes: bytes | None,
) -> None:
    width, height, margin_x, margin_y = _new_page(pdf)
    body_top = height - margin_y

    # Horizontal hero band (style Canada/USA)
    pdf.setFillColorRGB(0.12, 0.28, 0.52)
    pdf.rect(0, height - 32 * mm, width, 32 * mm, stroke=0, fill=1)
    body_top = height - 36 * mm

    if include_photo and profile_image_bytes:
        _draw_photo(pdf, profile_image_bytes, width - margin_x - 24 * mm, height - 6 * mm, 22 * mm, 28 * mm)

    y = body_top
    text_width = width - (2 * margin_x)
    for section in sections:
        y = _draw_section_single_column(pdf, section, margin_x, y, text_width, margin_y, 12.5)


def _draw_vertical_single_column(
    pdf: canvas.Canvas,
    sections: list[dict[str, Any]],
    include_photo: bool,
    profile_image_bytes: bytes | None,
) -> None:
    width, height, margin_x, margin_y = _new_page(pdf)
    y = height - margin_y

    if include_photo and profile_image_bytes:
        _draw_photo(pdf, profile_image_bytes, width - margin_x - 24 * mm, y, 22 * mm, 28 * mm)
        y -= 8

    text_width = width - (2 * margin_x)
    for section in sections:
        y = _draw_section_single_column(pdf, section, margin_x, y, text_width, margin_y, 12.5)


def _draw_two_vertical_columns(
    pdf: canvas.Canvas,
    sections: list[dict[str, Any]],
    include_photo: bool,
    profile_image_bytes: bytes | None,
) -> None:
    width, height, margin_x, margin_y = _new_page(pdf)

    left_w = 62 * mm
    gap = 8 * mm
    right_w = width - (2 * margin_x) - left_w - gap
    left_x = margin_x
    right_x = margin_x + left_w + gap

    left_titles = {
        "profil", "profile", "competences", "skills", "key skills", "core skills",
        "formation", "education", "certifications", "certificates", "languages", "contact"
    }

    left_sections: list[dict[str, Any]] = []
    right_sections: list[dict[str, Any]] = []
    for s in sections:
        t = s["title"].lower().strip()
        if t in left_titles:
            left_sections.append(s)
        else:
            right_sections.append(s)

    if include_photo and profile_image_bytes:
        _draw_photo(pdf, profile_image_bytes, left_x, height - margin_y, 28 * mm, 34 * mm)

    y_left = height - margin_y - (40 * mm if include_photo and profile_image_bytes else 0)
    y_right = height - margin_y

    pdf.setStrokeColorRGB(0.85, 0.85, 0.85)
    pdf.setLineWidth(1)
    pdf.line(right_x - gap / 2, margin_y, right_x - gap / 2, height - margin_y)

    for section in left_sections:
        y_left = _draw_section_single_column(pdf, section, left_x, y_left, left_w, margin_y, 12)

    # Right column on a fresh page if it became crowded on left pass
    if y_left < margin_y + 20:
        pdf.showPage()
        width, height, margin_x, margin_y = _new_page(pdf)
        left_x = margin_x
        right_x = margin_x + left_w + gap

    y_right = height - margin_y
    pdf.setStrokeColorRGB(0.85, 0.85, 0.85)
    pdf.setLineWidth(1)
    pdf.line(right_x - gap / 2, margin_y, right_x - gap / 2, height - margin_y)

    for section in right_sections:
        y_right = _draw_section_single_column(pdf, section, right_x, y_right, right_w, margin_y, 12)


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
    """Generate a country-formatted CV PDF from text."""
    del title, country, model_info, show_header

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    sections = _parse_cv_sections(text)
    if not sections:
        sections = [{"title": "Profile", "items": [line for line in text.splitlines() if line.strip()]}]

    if layout_mode == "horizontal_single_column":
        _draw_horizontal_single_column(pdf, sections, include_photo, profile_image_bytes)
    elif layout_mode == "two_vertical_columns":
        _draw_two_vertical_columns(pdf, sections, include_photo, profile_image_bytes)
    else:
        _draw_vertical_single_column(pdf, sections, include_photo, profile_image_bytes)

    pdf.save()
    return buffer.getvalue()
