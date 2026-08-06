"""
Generates PDF reports using reportlab.
Used by services/report_service.py
"""
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.colors import HexColor

def generate_pdf_report(
    output_dir: str,
    user_name: str,
    domain: str,
    title: str,
    sections: dict,
) -> str:
    """
    Generates a PDF report and saves it to output_dir.
    Returns the file path.
    """
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{user_name}_{domain}_{timestamp}.pdf"
    filepath = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=20,
        spaceAfter=20,
        textColor=HexColor('#6c63ff')
    )
    story.append(Paragraph(title, title_style))
    story.append(Paragraph(f"Prepared for: {user_name}", styles['Normal']))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%d %B %Y %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))

    # Sections
    for section_title, content in sections.items():
        story.append(Paragraph(section_title, styles['Heading2']))
        story.append(Paragraph(content, styles['Normal']))
        story.append(Spacer(1, 0.3*cm))

    doc.build(story)
    return filepath