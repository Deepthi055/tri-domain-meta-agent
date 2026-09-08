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
    token: str,
    db: Session = Depends(get_db),
):
    from core.security import decode_access_token
    from models.user import User

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="Not authenticated")

    current_user = db.query(User).filter(User.id == user_id).first()
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    report = get_report(db, report_id, current_user.id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    headers = {
        "Content-Disposition": f'inline; filename="{report.report_name.replace(" ", "_")}.pdf"'
    }
    return FileResponse(
        path=report.file_path,
        media_type="application/pdf",
        headers=headers,
    )

@router.delete("/{report_id}", status_code=204)
def remove_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from services.report_service import delete_report
    success = delete_report(db, report_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Report not found")
    return None
