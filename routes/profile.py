"""
app/routes/profile.py
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import get_current_user
from models.user import User
from schemas.profile import FullProfileIn, FullProfileOut
from services.profile_service import upsert_full_profile, get_full_profile

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
