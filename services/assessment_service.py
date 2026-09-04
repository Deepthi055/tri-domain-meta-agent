"""Pure assessment calculations with strict input validation.

These functions calculate assessment results only. They do not access a
session, persist rows, call external services, or create history records.
"""
from __future__ import annotations

import math
from numbers import Real
from typing import Any

from tools.calculators import calculate_savings, fitness_score, skill_gap_analyzer


def _require_number(value: Any, name: str, minimum: float, maximum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a number")
    numeric_value = float(value)
    if not math.isfinite(numeric_value):
        raise ValueError(f"{name} must be finite")
    if numeric_value < minimum or (maximum is not None and numeric_value > maximum):
        limit = f"between {minimum} and {maximum}" if maximum is not None else f">= {minimum}"
        raise ValueError(f"{name} must be {limit}")
    return numeric_value


def calculate_career_assessment(target_role: Any, current_skills: Any) -> dict[str, Any]:
    """Calculate a target-role skill-match assessment from explicit inputs."""
    if not isinstance(target_role, str) or not target_role.strip():
        raise ValueError("target_role is required")
    if not isinstance(current_skills, list) or not current_skills:
        raise ValueError("current_skills must be a non-empty list")
    if any(not isinstance(skill, str) or not skill.strip() for skill in current_skills):
        raise ValueError("current_skills must contain non-empty strings")

    normalized_role = target_role.strip().lower()
    normalized_skills = list(dict.fromkeys(skill.strip().lower() for skill in current_skills))
    result = skill_gap_analyzer(normalized_skills, normalized_role)
    if "error" in result:
        raise ValueError(result["error"])

    return {
        "domain": "career",
        "assessment_type": "target_role_skill_match",
        "value": result["match_percentage"],
        "value_kind": "score",
        "target_role": result["target_role"],
        "matched_skills": result["matched_skills"],
        "missing_skills": result["missing_skills"],
        "total_required_skills": result["total_required_skills"],
        "source": "skill_gap_analyzer",
        "calculation_version": "skill-gap-v1",
    }


def calculate_health_assessment(
    age: Any,
    height_cm: Any,
    weight_kg: Any,
    sleep_quality: Any,
    stress_level: Any,
    mood_score: Any,
    active_days_per_week: Any,
) -> dict[str, Any]:
    """Calculate a fitness assessment from complete explicit inputs."""
    age_value = _require_number(age, "age", 1, 120)
    height_value = _require_number(height_cm, "height_cm", 50, 300)
    weight_value = _require_number(weight_kg, "weight_kg", 20, 500)
    sleep_value = _require_number(sleep_quality, "sleep_quality", 1, 10)
    stress_value = _require_number(stress_level, "stress_level", 1, 10)
    mood_value = _require_number(mood_score, "mood_score", 1, 10)
    active_days_value = _require_number(active_days_per_week, "active_days_per_week", 0, 7)

    values = (age_value, sleep_value, stress_value, mood_value, active_days_value)
    if any(value != int(value) for value in values):
        raise ValueError("age and lifestyle scores must be integers")

    result = fitness_score(
        int(age_value),
        weight_value,
        height_value,
        sleep_quality=int(sleep_value),
        stress_level=int(stress_value),
        mood_score=int(mood_value),
        active_days_per_week=int(active_days_value),
    )

    return {
        "domain": "health",
        "assessment_type": "fitness",
        "value": result["fitness_score"],
        "value_kind": "score",
        "target_role": None,
        "bmi": result["bmi"],
        "component_scores": result["score_breakdown"],
        "source": "fitness_score",
        "calculation_version": "fitness-score-v1",
    }


def calculate_finance_assessment(monthly_income: Any, monthly_expenses: Any) -> dict[str, Any]:
    """Calculate a savings-rate metric from explicit income and expenses."""
    income_value = _require_number(monthly_income, "monthly_income", 0)
    expenses_value = _require_number(monthly_expenses, "monthly_expenses", 0)
    if income_value == 0:
        raise ValueError("monthly_income must be greater than 0")

    result = calculate_savings(income_value, expenses_value)
    return {
        "domain": "finance",
        "assessment_type": "savings_rate",
        "value": result["rate_pct"],
        "value_kind": "percentage",
        "target_role": None,
        "monthly_savings": result["savings"],
        "source": "calculate_savings",
        "calculation_version": "savings-rate-v1",
    }
