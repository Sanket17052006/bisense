"""Chat router — Member 5 API shell.

The chat engine is owned by Member 2 (agents) and Member 6 (verification).
This stub keeps the POST /api/chat contract stable and persists the
conversation/message rows (Member 5 infrastructure) so /api/history works
until the agent pipeline is integrated.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.services.agents.pipeline import AgentPipeline

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import Conversation, Message, User
from app.schemas.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])

STUB_REPLY = (
    "The chat engine is not integrated yet — this route is the Member 5 "
    "contract stub. Member 2 (AI router/agents) and Member 3 (RAG) own the "
    "implementation and will replace this response."
)


@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation: Conversation | None = None
    if payload.conversation_id:
        conversation = db.get(Conversation, payload.conversation_id)
        if conversation is None:
            conversation = None
    if conversation is None:
        conversation = Conversation(user_id=user.id, title=payload.message[:80])
        db.add(conversation)
        db.flush()

    db.add(Message(conversation_id=conversation.id, role="user", content=payload.message))
    pipeline = AgentPipeline()
    state = pipeline.run(payload.message)

    assistant = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=state.answer,
        intent=state.intent,
        confidence=state.confidence,
        sources=state.sources,
    )

    db.add(assistant)
    db.commit()
    db.refresh(conversation)

    return ChatResponse(
        reply=state.answer,
        intent=state.intent,
        agent=state.agent,
        confidence=state.confidence,
        conversation_id=conversation.id,
        sources=state.sources,
        unsupported=state.unsupported,
        disclaimer=state.disclaimer,
    )
