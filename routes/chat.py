"""
app/routes/chat.py

The core conversational endpoint. Flow per request:
  1. Resolve/create the conversation
  2. Save the user's message
  3. Detect domain (if "auto")
  4. Run the domain agent (profile + memory + history + RAG -> Groq)
  5. Save the assistant's reply
  6. Extract + save any new long-term memory from the user's message
  7. Return the answer
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, WebSocket
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import get_current_user
from models.user import User
from schemas.chat import ChatRequest, ChatResponse, ConversationOut, ConversationSummary
from services.conversation_service import (
    create_conversation,
    get_conversation,
    save_message,
    get_conversation_history,
    get_recent_conversations,
)
from core.ws_manager import manager as ws_manager
from services.domain_agents import run_domain_agent
from services.memory_service import extract_and_save_memory
from utils.intent_detector import detect_domain

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. Resolve domain
    domain = request.domain
    if domain == "auto":
        domain = detect_domain(request.query)

    # 2. Resolve/create conversation
    if request.conversation_id:
        conversation = get_conversation(db, request.conversation_id)
        if not conversation or conversation.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = create_conversation(db, user_id=current_user.id, domain=domain)
        # broadcast new conversation to connected websocket clients
        try:
            await ws_manager.broadcast({
                "type": "conversation_created",
                "payload": {
                    "id": conversation.id,
                    "domain": conversation.domain,
                    "created_at": conversation.created_at.isoformat(),
                },
            })
        except Exception:
            pass

    # 3. Save user message
    save_message(db, conversation.id, role="user", content=request.query)

    # 4. Load history (before this turn's reply, for context)
    history = get_conversation_history(db, conversation.id)

    # 5. Run the domain agent (profile + memory + history + RAG -> Groq)
    agent_result = run_domain_agent(
        db=db,
        user_id=current_user.id,
        domain=domain,
        query=request.query,
        conversation_messages=history,
    )

    answer = agent_result.get("recommendation", "")

    # 6. Save assistant reply
    save_message(db, conversation.id, role="assistant", content=answer)

    # 7. Load the full conversation history one final time so the client can use backend timestamps
    history = get_conversation_history(db, conversation.id)

    # 8. Extract + save long-term memory from the user's message (best-effort)
    memory_saved = []
    try:
        memory = extract_and_save_memory(db, current_user.id, request.query)
        if memory:
            memory_saved.append(memory.memory_text)
    except Exception:
        pass  # memory extraction must never break the chat response

    return ChatResponse(
        conversation_id=conversation.id,
        domain=domain,
        answer=answer,
        reason=agent_result.get("reason"),
        confidence=agent_result.get("confidence"),
        confidence_level=agent_result.get("confidence_level"),
        memory_saved=memory_saved,
        sources=agent_result.get("sources", []),
        tools_used=agent_result.get("tools_used", []),
        tool_outputs=agent_result.get("tool_outputs"),
        explainability=agent_result.get("explainability"),
        messages=history,
    )


@router.get("/history", response_model=List[ConversationSummary])
def chat_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_recent_conversations(db, current_user.id)


@router.websocket("/ws")
async def chat_ws(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # keep connection open; clients don't need to send data
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        ws_manager.disconnect(websocket)


@router.get("/conversation/{conversation_id}", response_model=ConversationOut)
def chat_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = get_conversation(db, conversation_id)
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation
