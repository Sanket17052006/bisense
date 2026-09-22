"""Certification router — roadmap + schemes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import CertificationScheme, Standard
from app.schemas.schemas import CertificationRoadmap, StandardOut

router = APIRouter(prefix="/certification", tags=["certification"])


@router.get("/roadmap", response_model=CertificationRoadmap)
def certification_roadmap(
    is_number: str | None = Query(None),
    is_code: str | None = Query(None, description="alias of is_number"),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    code = is_number or is_code
    std = None
    if code:
        std = db.execute(
            select(Standard).where(Standard.is_number.ilike(f"%{code}%"))
        ).scalars().first()
    scheme = db.execute(
        select(CertificationScheme).where(CertificationScheme.scheme_type == "product")
    ).scalars().first()
    if scheme is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "No certification scheme seeded")

    steps = [
        {
            "title": s.split(":", 1)[0],
            "detail": (s.split(":", 1)[1] if ":" in s else None),
        }
        for s in scheme.steps or []
    ]
    return CertificationRoadmap(
        is_number=std.is_number if std else code,
        title=(
            f"Roadmap to certify {std.title}"
            if std
            else f"Roadmap to certify product under {code or 'latest applicable IS'}"
        ),
        scheme=scheme.name,
        scheme_type=scheme.scheme_type,
        steps=steps,
        documents_required=scheme.documents_required or [],
        disclaimer=(
            "Steps are indicative. Fees, forms and timelines change — confirm on "
            "manakonline.in / bis.gov.in before applying."
        ),
    )


@router.get("/schemes", response_model=list)
def list_schemes(user=Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.execute(select(CertificationScheme)).scalars().all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "scheme_type": s.scheme_type,
            "description": s.description,
            "step_count": len(s.steps or []),
        }
        for s in rows
    ]