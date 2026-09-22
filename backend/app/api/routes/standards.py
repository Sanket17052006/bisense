"""Standards router (BIS IS codes)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import Clause, Standard, StandardRevision
from app.schemas.schemas import Page, StandardOut, StandardRangeRequest

router = APIRouter(prefix="/standards", tags=["standards"])


@router.get("", response_model=Page[StandardOut])
def list_standards(
    q: str | None = None,
    is_number: str | None = None,
    category: str | None = None,
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(Standard)
    if is_number:
        stmt = stmt.where(Standard.is_number.ilike(f"%{is_number}%"))
    if category:
        stmt = stmt.where(Standard.category.ilike(f"%{category}%"))
    if status:
        stmt = stmt.where(Standard.status == status)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                Standard.title.ilike(like),
                Standard.is_number.ilike(like),
                Standard.boundary.ilike(like),
                Standard.category.ilike(like),
            )
        )
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    rows = db.execute(stmt.offset(skip).limit(limit)).scalars().all()
    return Page(items=[StandardOut.model_validate(r) for r in rows], total=total, skip=skip, limit=limit)


@router.get("/categories", response_model=list[str])
def list_categories(user=Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.execute(
        select(Standard.category).where(Standard.category.isnot(None)).distinct()
    ).scalars().all()
    return sorted({c for c in rows if c}, key=str.lower)


@router.get("/{standard_id}", response_model=StandardOut)
def get_standard(standard_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    std = db.get(Standard, standard_id)
    if std is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Standard not found")
    std.clauses = db.execute(
        select(Clause).where(Clause.standard_id == std.id).order_by(Clause.clause_ref)
    ).scalars().all()
    std.revisions = db.execute(
        select(StandardRevision).where(StandardRevision.standard_id == std.id).order_by(StandardRevision.revision_year.desc())
    ).scalars().all()
    return StandardOut.model_validate(std)


@router.post("/range", response_model=Page[StandardOut])
def standards_by_numbers(
    payload: StandardRangeRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ = user
    rows = db.execute(
        select(Standard).where(Standard.is_number.in_(payload.is_numbers))
    ).scalars().all()
    return Page(items=[StandardOut.model_validate(r) for r in rows], total=len(rows))