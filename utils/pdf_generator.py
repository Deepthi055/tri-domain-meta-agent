"""
Generates PDF reports using reportlab.
Used by services/report_service.py
"""
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem
from reportlab.lib.colors import HexColor, black, white, Color

def generate_pdf_report(
    output_dir: str,
    report_data: dict,
) -> str:
    """
    Generates a PDF report and saves it to output_dir.
    Returns the file path.
    """
    os.makedirs(output_dir, exist_ok=True)

    username = report_data.get("username", "User")
    domain = report_data.get("domain", "General").capitalize()
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{username}_{domain}_{timestamp_str}.pdf"
    filepath = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    # Custom Styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        spaceAfter=10,
        textColor=HexColor('#2c3e50')
    )
    h1_style = ParagraphStyle(
        'Heading1',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=10,
        spaceBefore=15,
        textColor=HexColor('#2980b9'),
        borderPadding=5
    )
    h2_style = ParagraphStyle(
        'Heading2',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=8,
        spaceBefore=10,
        textColor=HexColor('#34495e')
    )
    normal_style = styles['Normal']
    normal_style.fontSize = 10
    normal_style.spaceAfter = 6

    # 1. Report Header
    story.append(Paragraph("<b>TriDomain Meta-Agent</b>", normal_style))
    story.append(Paragraph(f"{domain} Advisory Report", title_style))
    story.append(Spacer(1, 0.5*cm))

    # Helper function for tables
    def create_info_table(data_dict):
        table_data = []
        for k, v in data_dict.items():
            if v:
                table_data.append([Paragraph(f"<b>{k}</b>", normal_style), Paragraph(str(v), normal_style)])
        if not table_data:
            return None
        t = Table(table_data, colWidths=[5*cm, 10*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 0), (-1, -1), black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, HexColor('#e9ecef')),
            ('BOX', (0, 0), (-1, -1), 0.25, HexColor('#e9ecef')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        return t

    # 2. Report Information
    story.append(Paragraph("2. Report Information", h1_style))
    info_data = {
        "Report ID": report_data.get("report_id"),
        "Username": report_data.get("username"),
        "User ID": report_data.get("user_id"),
        "Domain": domain,
        "Intent Detected": report_data.get("intent_detected"),
        "Date": report_data.get("date"),
        "Time": report_data.get("time"),
        "Response Time": report_data.get("response_time"),
        "Report Version": report_data.get("version", "1.0"),
        "AI Model Used": report_data.get("ai_model")
    }
    t_info = create_info_table(info_data)
    if t_info:
        story.append(t_info)
    
    # 3. Consultation Request
    if any(report_data.get(k) for k in ["user_query", "query_language", "conversation_id"]):
        story.append(Paragraph("3. Consultation Request", h1_style))
        req_data = {
            "User Query": report_data.get("user_query"),
            "Query Language": report_data.get("query_language"),
            "Conversation ID": report_data.get("conversation_id"),
        }
        t_req = create_info_table(req_data)
        if t_req:
            story.append(t_req)

    # 4. User Profile Snapshot
    story.append(Paragraph("4. User Profile Snapshot", h1_style))
    profile_data = report_data.get("profile_snapshot", {})
    if profile_data:
        t_prof = create_info_table(profile_data)
        if t_prof:
            story.append(t_prof)
    else:
        story.append(Paragraph("No profile data available.", normal_style))

    llm_output = report_data.get("llm_output", {})

    # 5. AI Recommendation ⭐
    story.append(Paragraph("5. AI Recommendation ⭐", h1_style))
    recommendation = llm_output.get("ai_recommendation", "No recommendation generated.")
    rec_table = Table([[Paragraph(recommendation, normal_style)]], colWidths=[15*cm])
    rec_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#fff3cd')),
        ('BOX', (0, 0), (-1, -1), 1, HexColor('#ffe69c')),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(rec_table)
    story.append(Spacer(1, 0.3*cm))

    # 6. Detailed Analysis
    story.append(Paragraph("6. Detailed Analysis", h1_style))
    analysis_data = llm_output.get("detailed_analysis", {})
    if analysis_data:
        for k, v in analysis_data.items():
            story.append(Paragraph(str(k), h2_style))
            story.append(Paragraph(str(v), normal_style))
    else:
        story.append(Paragraph("No detailed analysis provided.", normal_style))

    # 7. Explainability
    story.append(Paragraph("7. Explainability", h1_style))
    explainability = llm_output.get("explainability", {})
    if explainability:
        for k, v in explainability.items():
            title = k.replace("_", " ").title()
            story.append(Paragraph(f"<b>{title}:</b> {v}", normal_style))
    else:
        story.append(Paragraph("No explainability data provided.", normal_style))

    # 8. Key Metrics
    story.append(Paragraph("8. Key Metrics", h1_style))
    metrics = llm_output.get("key_metrics", {})
    if metrics:
        t_metrics = create_info_table(metrics)
        if t_metrics:
            story.append(t_metrics)
    else:
        story.append(Paragraph("No key metrics provided.", normal_style))

    # 9. Action Plan
    story.append(Paragraph("9. Action Plan", h1_style))
    actions = llm_output.get("action_plan", [])
    if actions:
        for i, action in enumerate(actions, 1):
            story.append(Paragraph(f"<b>{i}.</b> {action}", normal_style))
    else:
        story.append(Paragraph("No action plan provided.", normal_style))

    # 10. Risks
    story.append(Paragraph("10. Risks", h1_style))
    risks = llm_output.get("risks", [])
    if risks:
        for risk in risks:
            story.append(Paragraph(f"• {risk}", normal_style))
    else:
        story.append(Paragraph("None identified.", normal_style))

    # 11. Assumptions
    story.append(Paragraph("11. Assumptions", h1_style))
    assumptions = llm_output.get("assumptions", [])
    if assumptions:
        for asm in assumptions:
            story.append(Paragraph(f"• {asm}", normal_style))
    else:
        story.append(Paragraph("None identified.", normal_style))

    # 12. Missing Information
    story.append(Paragraph("12. Missing Information", h1_style))
    missing_info = llm_output.get("missing_information", [])
    if missing_info:
        for info in missing_info:
            story.append(Paragraph(f"• {info}", normal_style))
    else:
        story.append(Paragraph("None identified.", normal_style))

    # 13. Confidence
    story.append(Paragraph("13. Confidence", h1_style))
    story.append(Paragraph(f"<b>Confidence Level:</b> {llm_output.get('confidence_level', 'N/A')}", normal_style))
    story.append(Paragraph(f"<b>Reason:</b> {llm_output.get('confidence_reason', 'N/A')}", normal_style))

    # 14. Disclaimer
    story.append(Paragraph("14. Disclaimer", h1_style))
    disclaimer = llm_output.get("disclaimer", f"This report is generated by an AI agent and should not be considered professional {domain.lower()} advice. Please consult a qualified professional before making significant decisions.")
    story.append(Paragraph(f"<i>{disclaimer}</i>", normal_style))

    # 15. Footer
    story.append(Spacer(1, 1*cm))
    footer_text = f"Generated by TriDomain Meta-Agent v{report_data.get('version', '1.0')} on {report_data.get('date')} {report_data.get('time')} | © TriDomain"
    story.append(Paragraph(f"<font color='grey'>{footer_text}</font>", normal_style))

    doc.build(story)
    return filepath