"""
app/services/memory_service.py

Long-term memory pipeline:
  1. extract_memory()  — ask Groq whether the user's message contains a
     durable fact worth remembering (vs small talk), and if so, normalize
     it into a short third-person statement + category + importance.
  2. save_memory()     — persist it to user_memory.
  3. retrieve_memory()  — pull the most relevant/important memories for a
     user (optionally filtered by domain) to inject into future prompts.
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from models.memory import UserMemory
from utils.groq_client import call_llm_json

MEMORY_EXTRACTION_PROMPT = """You extract durable long-term facts about a user from a single
chat message, for a Career/Health/Finance advisory assistant.

Only extract a fact if it is something worth remembering across future
sessions (a goal, skill, preference, ongoing plan, constraint, or
significant life detail). Casual remarks, greetings, or one-off questions
should NOT produce a memory.

CRITICAL: Respond ONLY with valid JSON in exactly this format:
{
    "has_memory": true,
    "memory_text": "User is preparing for the AWS Solutions Architect certification",
    "category": "career",
    "importance_score": 0.7
}

If there is nothing worth remembering, respond:
{
    "has_memory": false,
    "memory_text": "",
    "category": "",
    "importance_score": 0.0
}

category must be one of: career, health, finance, preference, goal, skill"""


VALID_CATEGORIES = {"career", "health", "finance", "preference", "goal", "skill"}


def extract_memory(user_message: str) -> Optional[dict]:
    """Returns {"memory_text", "category", "importance_score"} or None."""
    result = call_llm_json(MEMORY_EXTRACTION_PROMPT, user_message, temperature=0.1)

    if not result.get("has_memory"):
        return None

    category = result.get("category", "preference")
    if category not in VALID_CATEGORIES:
        category = "preference"

    memory_text = result.get("memory_text", "").strip()
    if not memory_text:
        return None

    importance = result.get("importance_score", 0.5)
    try:
        importance = float(importance)
    except (TypeError, ValueError):
        importance = 0.5

    return {
        "memory_text": memory_text,
        "category": category,
        "importance_score": max(0.0, min(1.0, importance)),
    }


def save_memory(db: Session, user_id: str, memory_text: str, category: str, importance_score: float) -> UserMemory:
    memory = UserMemory(
        user_id=user_id,
        memory_text=memory_text,
        category=category,
        importance_score=importance_score,
    )
    db.add(memory)
    db.commit()
    db.refresh(memory)
    return memory


def extract_and_save_memory(db: Session, user_id: str, user_message: str) -> Optional[UserMemory]:
    extracted = extract_memory(user_message)
    if not extracted:
        return None
    return save_memory(db, user_id, **extracted)


def retrieve_memory(db: Session, user_id: str, category: Optional[str] = None, limit: int = 10) -> List[UserMemory]:
    query = db.query(UserMemory).filter(UserMemory.user_id == user_id)
    if category:
        query = query.filter(UserMemory.category == category)
    return (
        query.order_by(UserMemory.importance_score.desc(), UserMemory.created_at.desc())
        .limit(limit)
        .all()
    )
