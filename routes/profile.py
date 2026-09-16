# """
# app/routes/profile.py
# """
# from fastapi import APIRouter, Depends
# from sqlalchemy.orm import Session

# from core.database import get_db
# from core.security import get_current_user
# from models.user import User
# from schemas.profile import FullProfileIn, FullProfileOut
# from services.profile_service import upsert_full_profile, get_full_profile

# router = APIRouter(prefix="/profile", tags=["profile"])


# @router.post("/create", response_model=FullProfileOut)
# def create_profile(
#     payload: FullProfileIn,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     result = upsert_full_profile(db, current_user.id, payload)
#     return result


# @router.get("", response_model=FullProfileOut)
# def read_profile(
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     return get_full_profile(db, current_user.id)


# @router.put("", response_model=FullProfileOut)
# def update_profile(
#     payload: FullProfileIn,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     result = upsert_full_profile(db, current_user.id, payload)
#     return result

"""
app/routes/profile.py
"""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
 
from core.database import get_db
from core.security import get_current_user
from models.user import User
from schemas.profile import FullProfileIn, FullProfileOut, CareerProfileIn
from services.profile_service import upsert_full_profile, get_full_profile
from services.resume_extraction import ResumeExtractionError, extract_resume_text
from services.medical_report_service import analyze_medical_report, extract_medical_report_text
 
router = APIRouter(prefix="/profile", tags=["profile"])
 
 
@router.post("/create", response_model=FullProfileOut)
def create_profile(
    payload: FullProfileIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = upsert_full_profile(db, current_user.id, payload)
    return result
 
 
@router.get("", response_model=FullProfileOut)
def read_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_full_profile(db, current_user.id)
 
 
@router.put("", response_model=FullProfileOut)
def update_profile(
    payload: FullProfileIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = upsert_full_profile(db, current_user.id, payload)
    return result
 
 
@router.post("/resume")
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Extracts text from an uploaded PDF/DOCX/TXT resume in memory and
    persists it through the exact same upsert_full_profile() path the
    normal profile save flow already uses - this is not a second,
    divergent way of writing to CareerProfile. Only `resume` (filename)
    and `resume_text` are included in the payload, so
    _clean_profile_data/_upsert's partial-update behavior leaves every
    other career field (target_role, education, etc.) untouched.
 
    Matches the frontend contract in ProfilePage.tsx:
        api.post('/profile/resume', formData, ...)
        extractedText = response.data?.resume_text
    """
    file_bytes = await file.read()
 
    try:
        resume_text = extract_resume_text(file_bytes, file.filename)
    except ResumeExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
 
    payload = FullProfileIn(
        career=CareerProfileIn(resume=file.filename, resume_text=resume_text)
    )
 
    upsert_full_profile(db, current_user.id, payload)
 
    return {"filename": file.filename, "resume_text": resume_text}


@router.post("/medical-report")
async def upload_medical_report(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Extract and explain a PDF medical report without storing its contents."""
    del current_user
    filename = file.filename or "medical-report.pdf"
    file_bytes = await file.read()
    try:
        report_text = extract_medical_report_text(file_bytes, filename)
        analysis = analyze_medical_report(report_text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "filename": filename,
        "extracted_text": report_text,
        "analysis": analysis,
    }
 

