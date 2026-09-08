"""Persistence helpers for immutable assessment events."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from models.progress import AssessmentEvent


def save_assessment_event(
    db: Session,
    user_id: str,
    assessment: dict[str, Any],
) -> AssessmentEvent:
    """Persist one validated assessment result for the authenticated user."""

    event = AssessmentEvent(
        user_id=user_id,
        domain=assessment["domain"],
        assessment_type=assessment["assessment_type"],
        value=assessment["value"],
        value_kind=assessment["value_kind"],
        target_role=assessment.get("target_role"),
        source=assessment["source"],
        calculation_version=assessment["calculation_version"],
        details=_build_details(assessment),
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return event


def _build_details(assessment: dict[str, Any]) -> dict[str, Any] | None:
    """Store only assessment-specific non-primary fields."""

    domain = assessment["domain"]

    if domain == "career":
        return {
            "matched_skills": assessment["matched_skills"],
            "missing_skills": assessment["missing_skills"],
            "total_required_skills": assessment["total_required_skills"],
        }

    if domain == "health":
        return {
            "bmi": assessment["bmi"],
            "component_scores": assessment["component_scores"],
        }

    if domain == "finance":
        return {
            "monthly_savings": assessment["monthly_savings"],
        }

    raise ValueError(f"Unsupported assessment domain: {domain}")