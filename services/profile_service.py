"""
app/services/profile_service.py

Handles the "enter profile once, reuse forever" requirement. Each of the
four sub-profiles is upserted independently so a user can fill in, say,
just their career profile today and their health profile next week.
"""
from sqlalchemy.orm import Session

from models.profile import UserProfile, CareerProfile, HealthProfile, FinanceProfile
from schemas.profile import FullProfileIn


def _upsert(db: Session, model, user_id: str, data: dict):
    if data is None:
        return None
    instance = db.query(model).filter(model.user_id == user_id).first()
    if instance is None:
        instance = model(user_id=user_id, **data)
        db.add(instance)
    else:
        for key, value in data.items():
            if value is not None:
                setattr(instance, key, value)
    db.commit()
    db.refresh(instance)
    return instance


def upsert_full_profile(db: Session, user_id: str, payload: FullProfileIn) -> dict:
    general = _upsert(
        db, UserProfile, user_id,
        payload.general.model_dump() if payload.general else None,
    )
    career = _upsert(
        db, CareerProfile, user_id,
        payload.career.model_dump() if payload.career else None,
    )
    health = _upsert(
        db, HealthProfile, user_id,
        payload.health.model_dump() if payload.health else None,
    )
    finance = _upsert(
        db, FinanceProfile, user_id,
        payload.finance.model_dump() if payload.finance else None,
    )
    return {"general": general, "career": career, "health": health, "finance": finance}


def get_full_profile(db: Session, user_id: str) -> dict:
    return {
        "general": db.query(UserProfile).filter(UserProfile.user_id == user_id).first(),
        "career": db.query(CareerProfile).filter(CareerProfile.user_id == user_id).first(),
        "health": db.query(HealthProfile).filter(HealthProfile.user_id == user_id).first(),
        "finance": db.query(FinanceProfile).filter(FinanceProfile.user_id == user_id).first(),
    }
