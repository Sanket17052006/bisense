"""Label scanner router — Member 5 API shell.

Vision/OCR is owned by Member 4. This stub keeps the POST /api/labels/scan
contract (LabelReport) and persists the scan row; status is "unavailable"
until the vision pipeline is integrated.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import LabelScan
from app.schemas.schemas import LabelExtracted, LabelReport
from app.services.files import save_image

router = APIRouter(prefix="/labels", tags=["labels"])

DISCLAIMER = "This is a technical scan, not a legal determination of compliance."


@router.post("/scan", response_model=LabelReport)
async def scan_label(
    file: UploadFile,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Upload an image file (JPEG/PNG)")
    path = save_image(file)

    report = LabelReport(
        id="",
        status="unavailable",
        extracted=LabelExtracted(raw_text=""),
        findings=[],
        confidence=0.0,
        disclaimer=DISCLAIMER + " Vision pipeline owned by Member 4 — not integrated yet.",
    )
    scan = LabelScan(
        user_id=user.id,
        image_path=str(path),
        status=report.status,
        extracted=report.extracted.model_dump(),
        findings=[],
        confidence=0.0,
    )
    db.add(scan)
    db.commit()
    return report.model_copy(update={"id": scan.id})