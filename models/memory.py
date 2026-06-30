"""
app/models/memory.py

Long-term memory store. Each row is a single extracted fact about the user
(e.g. "User is preparing for AWS certification"), tagged with a category
and an importance score used to rank what gets pulled into future prompts.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from core.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class UserMemory(Base):
    __tablename__ = "user_memory"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    memory_text = Column(Text, nullable=False)
    category = Column(String(30), nullable=False)
    # "career" | "health" | "finance" | "preference" | "goal" | "skill"
    importance_score = Column(Float, default=0.5)  # 0.0 - 1.0
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="memories")
