"""
app/schemas/profile.py

One combined "create/update" schema covers all four sub-profiles in a
single API call, since the frontend collects them together in one
onboarding form. All fields are optional on update (partial updates).
"""
from datetime import datetime
from typing import List, Optional, Union
from pydantic import BaseModel, field_validator
import json


class GeneralProfileIn(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    location: Optional[str] = None


class CareerProfileIn(BaseModel):
    education: Optional[str] = None
    current_skills: Optional[List[str]] = None
    target_role: Optional[str] = None
    experience_level: Optional[str] = None
    career_goal: Optional[str] = None
    preferred_roles: Optional[str] = None
    resume: Optional[str] = None

    @field_validator('current_skills', mode='before')
    def parse_current_skills(cls, value: Union[str, list, None]):
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
            raise ValueError('current_skills must be a list of strings or a JSON array string')
        return value


class HealthProfileIn(BaseModel):
    medical_conditions: Optional[str] = None
    lifestyle: Optional[str] = None
    fitness_goal: Optional[str] = None
    sleep_hours: Optional[float] = None
    sleep_quality: Optional[int] = None
    diet_preference: Optional[str] = None
    workout: Optional[str] = None
    health_goals: Optional[str] = None
    water_intake: Optional[float] = None


class FinanceProfileIn(BaseModel):
    monthly_income: Optional[float] = None
    monthly_expenses: Optional[float] = None
    savings_goal: Optional[float] = None
    investments: Optional[str] = None
    risk_appetite: Optional[str] = None
    investment_experience: Optional[str] = None
    financial_goals: Optional[str] = None
    budget: Optional[str] = None


class FullProfileIn(BaseModel):
    """Body for POST /profile/create and PUT /profile"""
    general: Optional[GeneralProfileIn] = None
    career: Optional[CareerProfileIn] = None
    health: Optional[HealthProfileIn] = None
    finance: Optional[FinanceProfileIn] = None


class GeneralProfileOut(GeneralProfileIn):
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CareerProfileOut(CareerProfileIn):
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class HealthProfileOut(HealthProfileIn):
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FinanceProfileOut(FinanceProfileIn):
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FullProfileOut(BaseModel):
    general: Optional[GeneralProfileOut] = None
    career: Optional[CareerProfileOut] = None
    health: Optional[HealthProfileOut] = None
    finance: Optional[FinanceProfileOut] = None
