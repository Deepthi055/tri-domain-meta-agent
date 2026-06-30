"""
app/models/user.py

Core User table. Holds login credentials only — all domain-specific data
lives in app/models/profile.py, linked by user_id.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from core.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ── Relationships ────────────────────────────────────────────
    profile = relationship(
        "UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    career_profile = relationship(
        "CareerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    health_profile = relationship(
        "HealthProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    finance_profile = relationship(
        "FinanceProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    conversations = relationship(
        "Conversation", back_populates="user", cascade="all, delete-orphan"
    )
    memories = relationship(
        "UserMemory", back_populates="user", cascade="all, delete-orphan"
    )
    reports = relationship(
        "Report", back_populates="user", cascade="all, delete-orphan"
    )
