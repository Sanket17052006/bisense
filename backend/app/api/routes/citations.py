"""Citations router — Member 5 API shell.

Source list/detail/recent are shared DB reads (M5 tables). Citation
verification (evidence validation, confidence, freshness scoring) is owned by
Member 6; POST /validate returns an unverified response until then.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import Source
from app.schemas.schemas import CitationOut, CitationValidateRequest, FreshnessOut

router = APIRouter(prefix="/citations", tags=["citations"])


@router.post("/validate", response_model=dict)
def validate(
    payload: CitationValidateRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ = user, db
    return {
        "claim": payload.claim,
        "validated": False,
        "confidence": 0.0,
        "supported": False,
        "note": "Citation verification owned by Member 6 — not integrated yet.",
    }


@router.get("/sources", response_model=list[FreshnessOut])
def list_sources(user=Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.execute(select(Source).order_by(Source.last_checked.desc())).scalars().all()
    return [_to_freshness(s) for s in rows]


@router.get("/sources/{source_id}", response_model=FreshnessOut)
def source_detail(source_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    src = db.get(Source, source_id)
    if src is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Source not found")
    return _to_freshness(src)


def _to_freshness(src) -> FreshnessOut:
    return FreshnessOut(
        id=src.id,
        url=src.url,
        title=src.title,
        published_date=src.published_date,
        retrieved_date=src.retrieved_date,
        last_checked=src.last_checked,
        version=src.version,
        amendment=src.amendment,
        superseded_by=src.superseded_by,
        superseded_status=src.superseded_status,
        http_status=src.http_status,
        is_fresh=bool(src.is_fresh),
    )


@router.get("/recent", response_model=list[CitationOut])
def recent_citations(user=Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models.models import Citation

    rows = (
        db.execute(select(Citation).order_by(Citation.checked_at.desc()).limit(20))
        .scalars()
        .all()
    )
    out = []
    for c in rows:
        src = db.get(Source, c.source_id)
        out.append(
            CitationOut(
                citation_id=c.id,
                claim=c.claim,
                quote=c.quote,
                evidence_score=c.evidence_score,
                confidence=c.confidence,
                supported=bool(c.supported),
                checked_at=c.checked_at,
                source=_to_freshness(src) if src else None,
            )
        )
    return out