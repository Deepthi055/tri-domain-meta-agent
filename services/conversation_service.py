"""
app/services/conversation_service.py
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from models.conversation import Conversation, Message


def create_conversation(db: Session, user_id: str, domain: str) -> Conversation:
    conversation = Conversation(user_id=user_id, domain=domain)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def get_conversation(db: Session, conversation_id: str) -> Optional[Conversation]:
    return db.query(Conversation).filter(Conversation.id == conversation_id).first()


def save_message(db: Session, conversation_id: str, role: str, content: str) -> Message:
    message = Message(conversation_id=conversation_id, role=role, content=content)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_conversation_history(db: Session, conversation_id: str, limit: int = 20) -> List[Message]:
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.timestamp.asc())
        .limit(limit)
        .all()
    )


def get_recent_conversations(db: Session, user_id: str, limit: int = 10) -> List[Conversation]:
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.created_at.desc())
        .limit(limit)
        .all()
    )


def format_history_for_prompt(messages: List[Message], max_turns: int = 6) -> str:
    """Renders the last few turns as plain text for the LLM prompt."""
    if not messages:
        return ""
    recent = messages[-max_turns:]
    lines = [f"{m.role.upper()}: {m.content}" for m in recent]
    return "Recent conversation history:\n" + "\n".join(lines)
