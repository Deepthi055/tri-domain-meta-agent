"""
app/schemas/memory.py
"""
from datetime import datetime
from pydantic import BaseModel


class MemoryOut(BaseModel):
    id: str
    memory_text: str
    category: str
    importance_score: float
    created_at: datetime

    class Config:
        from_attributes = True


class MemoryCreate(BaseModel):
    """For manually adding a memory fact (rarely needed — usually auto-extracted)."""
    memory_text: str
    category: str
    importance_score: float = 0.5
