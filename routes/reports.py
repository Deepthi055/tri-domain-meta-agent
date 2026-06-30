"""
app/routes/reports.py
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import get_current_user
from models.user import User
from schemas.report import ReportCreate, ReportOut
from services.report_service import generate_report, list_reports, get_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=ReportOut)
def create_report(
    payload: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = generate_report(
        db,
        user_id=current_user.id,
        user_name=current_user.name,
        domain=payload.domain,
        conversation_id=payload.conversation_id,
    )
    return report


@router.get("", response_model=List[ReportOut])
def get_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_reports(db, current_user.id)


@router.get("/{report_id}")
def download_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = get_report(db, report_id, current_user.id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(
        path=report.file_path,
        media_type="application/pdf",
        filename=report.report_name.replace(" ", "_") + ".pdf",
    )
