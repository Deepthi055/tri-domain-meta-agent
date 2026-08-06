"""
app/schemas/chat.py
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
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
    confidence_level: Optional[str] = None
    memory_saved: List[str] = []
    sources: List[str] = []
    tools_used: List[str] = []
    tool_outputs: Optional[Dict[str, Any]] = None
    explainability: Optional[Dict[str, Any]] = None
    messages: List[MessageOut] = []


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
