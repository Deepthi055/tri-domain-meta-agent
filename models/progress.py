"""
Historical assessment events for Career, Health, and Finance metrics.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from core.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class AssessmentEvent(Base):
    __tablename__ = "assessment_events"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid, nullable=False)
    user_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    domain = Column(String(20), nullable=False)
    assessment_type = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)
    value_kind = Column(String(20), nullable=False)
    target_role = Column(String(120), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    source = Column(String(100), nullable=False)
    calculation_version = Column(String(50), nullable=False)
    details = Column(JSON, nullable=True)

    user = relationship("User", back_populates="assessment_events")