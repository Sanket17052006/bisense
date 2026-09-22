"""History router — user conversations + messages (Member 5 persistence)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import Conversation, Message, User
from app.schemas.schemas import ConversationOut

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=list[ConversationOut])
def my_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    convs = (
        db.execute(
            select(Conversation)
            .where(Conversation.user_id == user.id)
            .order_by(Conversation.created_at.desc())
        )
        .scalars()
        .all()
    )
    for c in convs:
        c.messages = db.execute(
            select(Message)
            .where(Message.conversation_id == c.id)
            .order_by(Message.created_at)
        ).scalars().all()
    return [ConversationOut.model_validate(c) for c in convs]


@router.get("/{conversation_id}", response_model=ConversationOut)
def conversation_detail(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = db.get(Conversation, conversation_id)
    if conv is None or conv.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    conv.messages = db.execute(
        select(Message).where(Message.conversation_id == conv.id).order_by(Message.created_at)
    ).scalars().all()
    return ConversationOut.model_validate(conv)


@router.delete("/{conversation_id}", status_code=204)
def delete_conversation(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = db.get(Conversation, conversation_id)
    if conv is None or conv.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    db.delete(conv)
    db.commit()