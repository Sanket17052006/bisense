"""Chat router — Member 5 API shell.

The chat engine is owned by Member 2 (agents) and Member 6 (verification).
This route keeps the POST /api/chat contract stable, persists conversation
messages, enforces conversation ownership, and passes recent conversation
history to the Member 2 agent pipeline.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import Conversation, Message, User
from app.schemas.schemas import ChatRequest, ChatResponse, SourceOut
from app.services.agents.pipeline import AgentPipeline


router = APIRouter(prefix="/chat", tags=["chat"])


def _coerce_sources(sources: list) -> list[SourceOut]:
    """Map raw RAG dictionaries to SourceOut objects.

    Malformed retrieval results are ignored so they do not cause the
    complete chat response to fail.
    """
    out: list[SourceOut] = []

    for raw in sources or []:
        if not isinstance(raw, dict):
            continue

        try:
            # Support both old format (id, title, content, is_number) and new RAG format
            # title is required - don't provide default, let validation fail
            mapped = {
                "id": raw.get("id") or raw.get("chunk_id") or "",
                "title": raw.get("title") or raw.get("source"),
                "is_number": raw.get("is_number"),
                "chapter": raw.get("chapter"),
                "page": raw.get("page") or raw.get("page_number"),
                "year": raw.get("year"),
                "score": float(raw.get("score") or raw.get("hybrid_score") or raw.get("rerank_score") or 0.0),
                "fresh": True,
                "amendment": raw.get("amendment"),
                "superseded": False,
            }
            # Validate required fields (id and title are required by SourceOut)
            if not mapped["id"] or not mapped["title"]:
                continue
            out.append(SourceOut.model_validate(mapped))
        except ValidationError:
            continue

    return out


@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Process a chat message for the authenticated user."""

    conversation: Conversation | None = None

    # Reuse an existing conversation only when it belongs to the
    # authenticated user.
    if payload.conversation_id:
        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == payload.conversation_id,
                Conversation.user_id == user.id,
            )
            .first()
        )

        if conversation is None:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found",
            )

    # Create a new conversation when no conversation ID was supplied.
    if conversation is None:
        conversation = Conversation(
            user_id=user.id,
            title=payload.message[:80],
        )
        db.add(conversation)
        db.flush()

    # Load only the most recent messages from this conversation.
    # The current user message is added after this query so it is not
    # duplicated in the history passed to the pipeline.
    history_messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(10)
        .all()
    )

    history = [
        {
            "role": message.role,
            "content": message.content,
        }
        for message in reversed(history_messages)
    ]

    # Persist the current user message.
    db.add(
        Message(
            conversation_id=conversation.id,
            role="user",
            content=payload.message,
        )
    )

    # Run the Member 2 AI pipeline with recent conversation context.
    pipeline = AgentPipeline()
    state = pipeline.run(
        payload.message,
        history=history,
    )

    # Persist the assistant response.
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
        sources=_coerce_sources(state.sources),
        unsupported=state.unsupported,
        disclaimer=state.disclaimer,
    )