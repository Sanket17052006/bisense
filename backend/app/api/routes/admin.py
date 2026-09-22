"""Admin router (Member 6) — analytics, user management, freshness report."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models.models import (
    Citation,
    Document,
    Laboratory,
    Message,
    QCO,
    Source,
    User,
)
from app.schemas.schemas import AdminAnalytics, UserOut

router = APIRouter(prefix="/admin", tags=["admin"])


class RoleUpdate(BaseModel):
    role: str


@router.get("/analytics", response_model=AdminAnalytics)
def analytics(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    _ = admin
    total_users = db.execute(select(func.count()).select_from(User)).scalar_one()
    total_messages = db.execute(select(func.count()).select_from(Message)).scalar_one()
    total_documents = db.execute(select(func.count()).select_from(Document)).scalar_one()
    indexed = db.execute(
        select(func.count()).select_from(Document).where(Document.status == "indexed")
    ).scalar_one()
    failed = db.execute(
        select(func.count()).select_from(Document).where(Document.status == "failed")
    ).scalar_one()
    total_sources = db.execute(select(func.count()).select_from(Source)).scalar_one()
    stale = db.execute(
        select(func.count())
        .select_from(Source)
        .where(Source.is_fresh == 0)
    ).scalar_one()

    intent_counts = dict(db.execute(select(Message.intent, func.count()).group_by(Message.intent)).all())
    avg_conf = db.execute(select(func.avg(Message.confidence))).scalar_one()
    hallu = db.execute(
        select(func.count()).select_from(Citation).where(Citation.supported == 0)
    ).scalar_one()
    total_qcos = db.execute(select(func.count()).select_from(QCO)).scalar_one()
    total_labs = db.execute(select(func.count()).select_from(Laboratory)).scalar_one()

    return AdminAnalytics(
        total_users=total_users,
        total_messages=total_messages,
        total_documents=total_documents,
        indexed_documents=indexed,
        failed_documents=failed,
        total_sources=total_sources,
        stale_sources=stale,
        intent_counts={k or "general": v for k, v in intent_counts.items()},
        avg_confidence=round(float(avg_conf or 0.0), 3),
        hallucination_flags=hallu,
        total_qcos=total_qcos,
        total_labs=total_labs,
    )


@router.get("/users", response_model=list[UserOut])
def users(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.execute(select(User)).scalars().all()
    return [UserOut.model_validate(u) for u in rows]


@router.post("/users/{user_id}/role", response_model=UserOut)
def set_role(user_id: str, payload: RoleUpdate, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    if payload.role not in ("user", "admin"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "role must be user|admin")
    u = db.get(User, user_id)
    if u is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    u.role = payload.role
    db.commit()
    db.refresh(u)
    return UserOut.model_validate(u)


@router.get("/freshness", response_model=list)
def freshness_report(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    sources = db.execute(select(Source)).scalars().all()
    out = []
    for s in sources:
        out.append(
            {
                "id": s.id,
                "title": s.title,
                "url": s.url,
                "published_date": s.published_date,
                "last_checked": s.last_checked,
                "superseded_status": s.superseded_status,
                "amendment": s.amendment,
                "http_status": s.http_status,
                "fresh": bool(s.is_fresh),
            }
        )
    return out