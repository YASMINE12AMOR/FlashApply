from __future__ import annotations

from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas


def text_to_pdf_bytes(text: str, title: str = "Adapted CV") -> bytes:
    """Generate a simple PDF from plain text and return bytes."""
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    margin_x = 50
    margin_top = 50
    margin_bottom = 50
    line_height = 14
    usable_width = width - (2 * margin_x)

    y = height - margin_top
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(margin_x, y, title)
    y -= 24

    pdf.setFont("Helvetica", 11)
    for paragraph in text.splitlines():
        wrapped_lines = simpleSplit(paragraph if paragraph else " ", "Helvetica", 11, usable_width)
        for line in wrapped_lines:
            if y < margin_bottom:
                pdf.showPage()
                pdf.setFont("Helvetica", 11)
                y = height - margin_top
            pdf.drawString(margin_x, y, line)
            y -= line_height
        y -= 3

    pdf.save()
    return buffer.getvalue()
