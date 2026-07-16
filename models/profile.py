"""
app/models/profile.py

One-time-entry profile tables. Each user has at most one row in each of
these four tables — entered once, updated thereafter, and loaded on every
chat request to personalize responses (see services/context_builder.py).
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from core.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class UserProfile(Base):
    """General demographic profile — entered once at onboarding."""
    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, unique=True, index=True
    )
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    location = Column(String(120), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")


class CareerProfile(Base):
    __tablename__ = "career_profiles"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, unique=True, index=True
    )
    education = Column(String(120), nullable=True)
    current_skills = Column(JSON, nullable=True, default=list)
    target_role = Column(String(120), nullable=True)
    experience_level = Column(String(50), nullable=True)  # intern/junior/mid/senior
    career_goal = Column(String(255), nullable=True)
    preferred_roles = Column(String(255), nullable=True)
    resume = Column(String(2000), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="career_profile")


class HealthProfile(Base):
    __tablename__ = "health_profiles"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, unique=True, index=True
    )
    medical_conditions = Column(String(500), nullable=True)
    lifestyle = Column(String(50), nullable=True)
    fitness_goal = Column(String(120), nullable=True)
    sleep_hours = Column(Float, nullable=True)
    sleep_quality = Column(Integer, nullable=True)  # 1-10
    diet_preference = Column(String(50), nullable=True)  # veg/non-veg/vegan/etc
    workout = Column(String(120), nullable=True)
    health_goals = Column(String(255), nullable=True)
    water_intake = Column(Float, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="health_profile")


class FinanceProfile(Base):
    __tablename__ = "finance_profiles"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, unique=True, index=True
    )
    monthly_income = Column(Float, nullable=True)
    monthly_expenses = Column(Float, nullable=True)
    savings_goal = Column(Float, nullable=True)
    investments = Column(String(255), nullable=True)
    risk_appetite = Column(String(50), nullable=True)  # low/medium/high
    investment_experience = Column(String(50), nullable=True)  # beginner/intermediate/advanced
    financial_goals = Column(String(255), nullable=True)
    budget = Column(String(500), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="finance_profile")
