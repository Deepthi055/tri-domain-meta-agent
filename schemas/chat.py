"""
app/schemas/chat.py
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    query: str
    domain: str = "auto"                      # "auto" | "career" | "health" | "finance"
    conversation_id: Optional[str] = None      # omit to start a new conversation


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    conversation_id: str
    domain: str
    answer: str
    reason: Optional[str] = None
    confidence: Optional[float] = None
    memory_saved: List[str] = []
    sources: List[str] = []  # RAG-retrieved snippet titles used for this answer


class ConversationOut(BaseModel):
    id: str
    domain: str
    created_at: datetime
    messages: List[MessageOut] = []

    class Config:
        from_attributes = True


class ConversationSummary(BaseModel):
    id: str
    domain: str
    created_at: datetime

    class Config:
        from_attributes = True
