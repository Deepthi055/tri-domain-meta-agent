"""
app/utils/pdf_generator.py

Generates a simple advisory PDF report using reportlab. Pure utility —
no DB or LLM calls happen here, just rendering text onto a PDF page.
"""
import os
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas


def generate_pdf_report(
    output_dir: str,
    user_name: str,
    domain: str,
    title: str,
    sections: dict,
) -> str:
    """
    sections: dict of {heading: body_text} rendered in order.
    Returns the absolute file path written.
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{domain}_report_{timestamp}.pdf"
    file_path = os.path.join(output_dir, filename)

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4
    margin = 2 * cm
    y = height - margin

    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin, y, title)
    y -= 0.8 * cm

    c.setFont("Helvetica", 10)
    c.drawString(margin, y, f"Prepared for: {user_name}")
    y -= 0.5 * cm
    c.drawString(margin, y, f"Domain: {domain.capitalize()}")
    y -= 0.5 * cm
    c.drawString(margin, y, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    y -= 1.0 * cm

    for heading, body in sections.items():
        if y < 4 * cm:
            c.showPage()
            y = height - margin

        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin, y, heading)
        y -= 0.6 * cm

        c.setFont("Helvetica", 10)
        for line in _wrap_text(body, max_chars=95):
            if y < 3 * cm:
                c.showPage()
                y = height - margin
            c.drawString(margin, y, line)
            y -= 0.45 * cm

        y -= 0.4 * cm

    c.save()
    return file_path


def _wrap_text(text: str, max_chars: int = 95):
    """Wraps text to max_chars per line, preserving explicit '\\n' breaks
    in the source (e.g. one profile field per line) instead of collapsing
    them into a single run-on line."""
    all_lines = []
    for paragraph in (text or "").split("\n"):
        words = paragraph.split()
        if not words:
            all_lines.append("")
            continue
        current = ""
        for word in words:
            if len(current) + len(word) + 1 <= max_chars:
                current = f"{current} {word}".strip()
            else:
                all_lines.append(current)
                current = word
        if current:
            all_lines.append(current)
    return all_lines or [""]
