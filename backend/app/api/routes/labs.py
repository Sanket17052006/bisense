"""Laboratory router — BIS/NABL recognized lab finder."""
from __future__ import annotations

import math

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import Laboratory
from app.schemas.schemas import LabOut, Page

router = APIRouter(prefix="/labs", tags=["labs"])


def _haversine_km(lat1, lon1, lat2, lon2) -> float | None:
    if None in (lat1, lon1, lat2, lon2):
        return None
    try:
        lat1, lon1, lat2, lon2 = map(float, (lat1, lon1, lat2, lon2))
    except (TypeError, ValueError):
        return None
    R = 6371.0
    ph1, ph2 = math.radians(lat1), math.radians(lat2)
    dph = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dph / 2) ** 2 + math.cos(ph1) * math.cos(ph2) * math.sin(dl / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


@router.get("", response_model=Page[LabOut])
def list_labs(
    state: str | None = None,
    city: str | None = None,
    pincode: str | None = None,
    product: str | None = None,
    query: str | None = Query(None, description="free-text search"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(Laboratory)
    if state:
        stmt = stmt.where(Laboratory.state.ilike(f"%{state}%"))
    if city:
        stmt = stmt.where(Laboratory.city.ilike(f"%{city}%"))
    if pincode:
        stmt = stmt.where(Laboratory.pincode == pincode)
    if product or query:
        term = product or query
        like = f"%{term}%"
        stmt = stmt.where(
            or_(
                Laboratory.products.ilike(like),
                Laboratory.name.ilike(like),
                Laboratory.accreditations.ilike(like),
            )
        )
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    rows = db.execute(stmt.offset(skip).limit(limit)).scalars().all()
    return Page(items=[LabOut.model_validate(r) for r in rows], total=total, skip=skip, limit=limit)