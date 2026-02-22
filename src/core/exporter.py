from __future__ import annotations

from datetime import datetime
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas


def _draw_page_header(pdf: canvas.Canvas, title: str, subtitle: str) -> None:
    width, height = A4
    pdf.setFillColorRGB(0.11, 0.24, 0.49)
    pdf.rect(0, height - 38 * mm, width, 38 * mm, stroke=0, fill=1)
    pdf.setFillColorRGB(1, 1, 1)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(15 * mm, height - 18 * mm, title)
    pdf.setFont("Helvetica", 10)
    pdf.drawString(15 * mm, height - 25 * mm, subtitle)


def _draw_page_footer(pdf: canvas.Canvas, page_num: int) -> None:
    width, _ = A4
    pdf.setFillColorRGB(0.4, 0.4, 0.4)
    pdf.setFont("Helvetica", 9)
    pdf.drawRightString(width - 12 * mm, 10 * mm, f"Page {page_num}")


def text_to_pdf_bytes(
    text: str,
    title: str = "Adapted CV",
    country: str = "",
    model_info: str = "",
) -> bytes:
    """Generate a styled PDF from plain text and return bytes."""
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    margin_x = 15 * mm
    margin_top = 48 * mm
    margin_bottom = 18 * mm
    line_height = 13
    usable_width = width - (2 * margin_x)
    section_gap = 8

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    subtitle_parts = [f"Generated: {generated_at}"]
    if country:
        subtitle_parts.append(f"Country: {country}")
    if model_info:
        subtitle_parts.append(f"Model: {model_info}")
    subtitle = " | ".join(subtitle_parts)
    page_num = 1
    _draw_page_header(pdf, title, subtitle)

    y = height - margin_top
    for paragraph in text.splitlines():
        raw = paragraph.strip()

        if not raw:
            y -= 6
            continue

        is_section = (not raw.startswith("-")) and len(raw) <= 48
        if is_section:
            text_font = "Helvetica-Bold"
            text_size = 12
            draw_text = raw
        elif raw.startswith("-"):
            text_font = "Helvetica"
            text_size = 10.5
            draw_text = f"• {raw[1:].strip()}"
        else:
            text_font = "Helvetica"
            text_size = 10.5
            draw_text = raw

        wrapped_lines = simpleSplit(draw_text, text_font, text_size, usable_width)
        for line in wrapped_lines:
            if y < margin_bottom:
                _draw_page_footer(pdf, page_num)
                pdf.showPage()
                page_num += 1
                _draw_page_header(pdf, title, subtitle)
                y = height - margin_top
            pdf.setFillColorRGB(0.1, 0.1, 0.1)
            pdf.setFont(text_font, text_size)
            pdf.drawString(margin_x, y, line)
            y -= line_height
        y -= section_gap if is_section else 3

    _draw_page_footer(pdf, page_num)
    pdf.save()
    return buffer.getvalue()
