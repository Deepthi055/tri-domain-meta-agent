"""Assessment API request and response schemas."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HealthAssessmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sleep_quality: int | None = None
    stress_level: int | None = None
    mood_score: int | None = None
    active_days_per_week: int | None = None


class AssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    assessment_id: str
    domain: str
    assessment_type: str
    value: float
    value_kind: str
    target_role: str | None = None
    assessed_at: datetime
    source: str
    calculation_version: str
    details: dict[str, Any] | None = None


class AssessmentHistoryItem(BaseModel):
    assessment_id: str
    domain: str
    assessment_type: str
    value: float
    value_kind: str
    target_role: str | None = None
    assessed_at: datetime
