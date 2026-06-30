"""
app/routes/memory.py
"""
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import get_current_user
from models.user import User
from schemas.memory import MemoryOut, MemoryCreate
from services.memory_service import retrieve_memory, save_memory

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("", response_model=List[MemoryOut])
def list_memory(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return retrieve_memory(db, current_user.id, category=category, limit=50)


@router.post("", response_model=MemoryOut)
def add_memory_manually(
    payload: MemoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return save_memory(
        db,
        user_id=current_user.id,
        memory_text=payload.memory_text,
        category=payload.category,
        importance_score=payload.importance_score,
    )
