"""Authenticated assessment creation endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import get_current_user
from models.profile import CareerProfile, FinanceProfile, HealthProfile, UserProfile
from models.user import User
from schemas.assessment import AssessmentResponse, HealthAssessmentRequest
from services.assessment_persistence import save_assessment_event
from services.assessment_service import (
    calculate_career_assessment,
    calculate_finance_assessment,
    calculate_health_assessment,
)

router = APIRouter(prefix="/assessments", tags=["assessments"])


def _response(event) -> AssessmentResponse:
    return AssessmentResponse(
        assessment_id=event.id,
        domain=event.domain,
        assessment_type=event.assessment_type,
        value=event.value,
        value_kind=event.value_kind,
        target_role=event.target_role,
        assessed_at=event.created_at,
        source=event.source,
        calculation_version=event.calculation_version,
        details=event.details,
    )


def _assessment_error(error: ValueError) -> HTTPException:
    return HTTPException(status_code=400, detail=str(error))


@router.post("/career", response_model=AssessmentResponse)
def create_career_assessment(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    career_profile = (
        db.query(CareerProfile)
        .filter(CareerProfile.user_id == current_user.id)
        .first()
    )
    if career_profile is None:
        raise HTTPException(status_code=400, detail="Career profile is required")

    try:
        assessment = calculate_career_assessment(
            target_role=career_profile.target_role,
            current_skills=career_profile.current_skills,
        )
    except ValueError as error:
        raise _assessment_error(error) from error

    event = save_assessment_event(db, current_user.id, assessment)
    return _response(event)


@router.post("/health", response_model=AssessmentResponse)
def create_health_assessment(
    request: HealthAssessmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_profile = (
        db.query(UserProfile)
        .filter(UserProfile.user_id == current_user.id)
        .first()
    )
    health_profile = (
        db.query(HealthProfile)
        .filter(HealthProfile.user_id == current_user.id)
        .first()
    )
    if user_profile is None or health_profile is None:
        raise HTTPException(status_code=400, detail="Complete health profile is required")

    assessment_inputs = (
        request.sleep_quality,
        request.stress_level,
        request.mood_score,
        request.active_days_per_week,
    )
    if any(value is None for value in assessment_inputs):
        raise HTTPException(
            status_code=400,
            detail="sleep_quality, stress_level, mood_score, and active_days_per_week are required",
        )

    try:
        assessment = calculate_health_assessment(
            age=user_profile.age,
            height_cm=user_profile.height_cm,
            weight_kg=user_profile.weight_kg,
            sleep_quality=request.sleep_quality,
            stress_level=request.stress_level,
            mood_score=request.mood_score,
            active_days_per_week=request.active_days_per_week,
        )
    except ValueError as error:
        raise _assessment_error(error) from error

    event = save_assessment_event(db, current_user.id, assessment)
    return _response(event)


@router.post("/finance", response_model=AssessmentResponse)
def create_finance_assessment(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    finance_profile = (
        db.query(FinanceProfile)
        .filter(FinanceProfile.user_id == current_user.id)
        .first()
    )
    if finance_profile is None:
        raise HTTPException(status_code=400, detail="Finance profile is required")
    if finance_profile.monthly_income is None or finance_profile.monthly_expenses is None:
        raise HTTPException(
            status_code=400,
            detail="Monthly income and monthly expenses are required",
        )

    try:
        assessment = calculate_finance_assessment(
            monthly_income=finance_profile.monthly_income,
            monthly_expenses=finance_profile.monthly_expenses,
        )
    except ValueError as error:
        raise _assessment_error(error) from error

    event = save_assessment_event(db, current_user.id, assessment)
    return _response(event)
