"""Compare router for side-by-side standard comparison."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import Clause, Standard, StandardRevision
from app.schemas.schemas import StandardOut

router = APIRouter(prefix="/compare", tags=["compare"])


class CompareRequest(BaseModel):
    standard_a_id: str
    standard_b_id: str


class CompareResponse(BaseModel):
    standard_a: StandardOut
    standard_b: StandardOut
    differences: dict


@router.post("", response_model=CompareResponse)
def compare_standards(
    payload: CompareRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ = user
    
    std_a = db.get(Standard, payload.standard_a_id)
    std_b = db.get(Standard, payload.standard_b_id)
    
    if not std_a:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Standard {payload.standard_a_id} not found")
    if not std_b:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Standard {payload.standard_b_id} not found")

    # Load clauses
    clauses_a = db.execute(
        select(Clause).where(Clause.standard_id == std_a.id).order_by(Clause.clause_ref)
    ).scalars().all()
    clauses_b = db.execute(
        select(Clause).where(Clause.standard_id == std_b.id).order_by(Clause.clause_ref)
    ).scalars().all()
    
    std_a.clauses = clauses_a
    std_b.clauses = clauses_b
    
    # Load revisions
    revisions_a = db.execute(
        select(StandardRevision).where(StandardRevision.standard_id == std_a.id).order_by(StandardRevision.revision_year.desc())
    ).scalars().all()
    revisions_b = db.execute(
        select(StandardRevision).where(StandardRevision.standard_id == std_b.id).order_by(StandardRevision.revision_year.desc())
    ).scalars().all()
    
    std_a.revisions = revisions_a
    std_b.revisions = revisions_b

    # Build differences
    differences = {
        "is_number": {"a": std_a.is_number, "b": std_b.is_number},
        "title": {"a": std_a.title, "b": std_b.title},
        "category": {"a": std_a.category, "b": std_b.category},
        "status": {"a": std_a.status, "b": std_b.status},
        "certification_type": {"a": std_a.certification_type, "b": std_b.certification_type},
        "scope": {"a": std_a.boundary, "b": std_b.boundary},
        "clauses_count": {"a": len(clauses_a), "b": len(clauses_b)},
        "revisions_count": {"a": len(revisions_a), "b": len(revisions_b)},
    }

    return CompareResponse(
        standard_a=StandardOut.model_validate(std_a),
        standard_b=StandardOut.model_validate(std_b),
        differences=differences,
    )


@router.get("/search", response_model=list[StandardOut])
def search_standards_for_compare(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    like = f"%{q}%"
    stmt = select(Standard).where(
        or_(
            Standard.title.ilike(like),
            Standard.is_number.ilike(like),
            Standard.boundary.ilike(like),
            Standard.category.ilike(like),
        )
    ).limit(limit)
    
    rows = db.execute(stmt).scalars().all()
    return [StandardOut.model_validate(r) for r in rows]