"""QCO router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import ProductCategory, QCO
from app.schemas.schemas import Page, QCOOut

router = APIRouter(prefix="/qco", tags=["qco"])


@router.get("", response_model=Page[QCOOut])
def list_qcos(
    search: str | None = None,
    product: str | None = None,
    qco_status: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(QCO)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(
            or_(QCO.title.ilike(like), QCO.product_category.ilike(like), QCO.is_number.ilike(like))
        )
    if product:
        stmt = stmt.where(QCO.product_category.ilike(f"%{product}%"))
    if qco_status:
        stmt = stmt.where(QCO.status == qco_status)
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    rows = db.execute(stmt.offset(skip).limit(limit)).scalars().all()
    items = []
    for q in rows:
        qco = q
        qco.product_categories = db.execute(
            select(ProductCategory).where(ProductCategory.qco_id == q.id)
        ).scalars().all()
        items.append(QCOOut.model_validate(qco))
    return Page(items=items, total=total, skip=skip, limit=limit)


@router.get("/{qco_id}", response_model=QCOOut)
def qco_detail(qco_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.get(QCO, qco_id)
    if q is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "QCO not found")
    q.product_categories = db.execute(
        select(ProductCategory).where(ProductCategory.qco_id == q.id)
    ).scalars().all()
    return QCOOut.model_validate(q)