"""
app/services/profile_service.py

Handles the "enter profile once, reuse forever" requirement. Each of the
four sub-profiles is upserted independently so a user can fill in, say,
just their career profile today and their health profile next week.
"""
import json
from sqlalchemy.orm import Session

from models.profile import UserProfile, CareerProfile, HealthProfile, FinanceProfile
from schemas.profile import FullProfileIn


def _parse_current_skills(value):
    if value is None:
        return None
    if isinstance(value, list):
        return [str(item).strip() for item in value if item is not None]
    if isinstance(value, str):
        trimmed = value.strip()
        if not trimmed:
            return None
        try:
            parsed = json.loads(trimmed)
        except ValueError:
            parsed = [item.strip() for item in trimmed.split(',') if item.strip()]
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if item is not None]
        raise ValueError('current_skills must be a JSON array string or a list of strings')
    return [str(value)]


def _clean_profile_data(data: dict):
    if data is None:
        return None
    cleaned = {}
    for key, value in data.items():
        if value is None:
            continue
        if key == 'current_skills':
            cleaned[key] = _parse_current_skills(value)
        else:
            cleaned[key] = value
    return cleaned or None


def _upsert(db: Session, model, user_id: str, data: dict):
    data = _clean_profile_data(data)
    if data is None:
        return None
    instance = db.query(model).filter(model.user_id == user_id).first()
    if instance is None:
        instance = model(user_id=user_id, **data)
        db.add(instance)
    else:
        for key, value in data.items():
            setattr(instance, key, value)
    db.flush()
    db.refresh(instance)
    return instance


def upsert_full_profile(db: Session, user_id: str, payload: FullProfileIn) -> dict:
    try:
        general = _upsert(
            db, UserProfile, user_id,
            payload.general.model_dump(exclude_none=True) if payload.general else None,
        )
        career = _upsert(
            db, CareerProfile, user_id,
            payload.career.model_dump(exclude_none=True) if payload.career else None,
        )
        health = _upsert(
            db, HealthProfile, user_id,
            payload.health.model_dump(exclude_none=True) if payload.health else None,
        )
        finance = _upsert(
            db, FinanceProfile, user_id,
            payload.finance.model_dump(exclude_none=True) if payload.finance else None,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"general": general, "career": career, "health": health, "finance": finance}


def get_full_profile(db: Session, user_id: str) -> dict:
    return {
        "general": db.query(UserProfile).filter(UserProfile.user_id == user_id).first(),
        "career": db.query(CareerProfile).filter(CareerProfile.user_id == user_id).first(),
        "health": db.query(HealthProfile).filter(HealthProfile.user_id == user_id).first(),
        "finance": db.query(FinanceProfile).filter(FinanceProfile.user_id == user_id).first(),
    }
