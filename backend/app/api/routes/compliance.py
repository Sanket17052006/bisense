"""Compliance router — Member 4 Vision/Compliance pipeline."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import ComplianceCheck
from app.schemas.schemas import ComplianceCheckOut, ComplianceCheckRequest, ComplianceOverview
from app.vision.compliance.compliance_checker import check_compliance as vision_check_compliance

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.post("/check", response_model=ComplianceCheckOut)
def create_check(
    payload: ComplianceCheckRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Run the Member 4 compliance checker
    try:
        result = vision_check_compliance(
            product_type=payload.product_type,
            is_number=payload.is_number,
            extracted=payload.extracted,
        )
        status_val = result.get("status", "unavailable")
        findings = result.get("findings", [])
        summary = result.get("summary", "")
        confidence = result.get("confidence", 0.0)
    except Exception as e:
        print(f"[Compliance] Check error: {e}")
        status_val = "unavailable"
        findings = []
        summary = "Compliance scanner error"
        confidence = 0.0

    row = ComplianceCheck(
        user_id=user.id,
        product=payload.product_type,
        is_number=payload.is_number,
        status=status_val,
        findings=[f.model_dump() if hasattr(f, 'model_dump') else f for f in findings],
        summary=summary,
        confidence=confidence,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return ComplianceCheckOut.model_validate(row)


@router.get("/overview", response_model=ComplianceOverview)
def overview(user=Depends(get_current_user), db: Session = Depends(get_db)):
    _ = user
    statuses = ["verified", "needs_verification", "potential_gap", "unavailable"]
    counts = {s: 0 for s in statuses}
    rows = db.execute(select(ComplianceCheck.status)).scalars().all()
    for s in rows:
        counts[s] = counts.get(s, 0) + 1
    avg = db.execute(select(func.avg(ComplianceCheck.confidence))).scalar_one()
    recent = (
        db.execute(select(ComplianceCheck).order_by(ComplianceCheck.created_at.desc()).limit(10))
        .scalars()
        .all()
    )
    return ComplianceOverview(
        total_checks=len(rows),
        verified=counts["verified"],
        needs_verification=counts["needs_verification"],
        potential_gap=counts["potential_gap"],
        unavailable=counts["unavailable"],
        avg_confidence=round(float(avg or 0.0), 3),
        recent=[ComplianceCheckOut.model_validate(c) for c in recent],
    )


@router.get("/checks", response_model=list[ComplianceCheckOut])
def checks(
    limit: int = 50,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.execute(select(ComplianceCheck).order_by(ComplianceCheck.created_at.desc()).limit(limit))
        .scalars()
        .all()
    )
    return [ComplianceCheckOut.model_validate(c) for c in rows]


@router.get("/checks/{check_id}", response_model=ComplianceCheckOut)
def check_detail(check_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    c = db.get(ComplianceCheck, check_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Compliance check not found")
    return ComplianceCheckOut.model_validate(c)