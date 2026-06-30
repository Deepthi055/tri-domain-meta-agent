"""
app/services/report_service.py

Generates a PDF report summarizing a user's profile + recent advice for a
domain (optionally scoped to one conversation), saves the file under
REPORTS_DIR, and records the path in the `reports` table.
"""
from typing import Optional
from sqlalchemy.orm import Session

from core.config import settings
from models.report import Report
from services.profile_service import get_full_profile
from services.memory_service import retrieve_memory
from services.conversation_service import get_conversation_history
from utils.pdf_generator import generate_pdf_report


def generate_report(
    db: Session, user_id: str, user_name: str, domain: str, conversation_id: Optional[str] = None
) -> Report:
    profile = get_full_profile(db, user_id)
    memories = retrieve_memory(db, user_id, category=domain, limit=10)

    sections = {}

    domain_profile = profile.get(domain)
    if domain_profile:
        profile_lines = []
        for key, value in vars(domain_profile).items():
            if key.startswith("_") or key in ("id", "user_id", "updated_at") or value is None:
                continue
            profile_lines.append(f"{key.replace('_', ' ').title()}: {value}")
        sections[f"{domain.capitalize()} Profile"] = "\n".join(profile_lines) or "No data on file."

    if memories:
        sections["Key Facts on File"] = "\n".join(f"- {m.memory_text}" for m in memories)

    if conversation_id:
        history = get_conversation_history(db, conversation_id)
        assistant_turns = [m.content for m in history if m.role == "assistant"]
        sections["Recent Advice Given"] = "\n\n".join(assistant_turns[-5:]) or "No advice recorded yet."

    file_path = generate_pdf_report(
        output_dir=settings.REPORTS_DIR,
        user_name=user_name,
        domain=domain,
        title=f"{domain.capitalize()} Advisory Report",
        sections=sections,
    )

    report = Report(
        user_id=user_id,
        report_name=f"{domain.capitalize()} Advisory Report",
        file_path=file_path,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def list_reports(db: Session, user_id: str):
    return (
        db.query(Report)
        .filter(Report.user_id == user_id)
        .order_by(Report.generated_at.desc())
        .all()
    )


def get_report(db: Session, report_id: str, user_id: str):
    return (
        db.query(Report)
        .filter(Report.id == report_id, Report.user_id == user_id)
        .first()
    )
