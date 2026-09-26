"""Label scanner router — Member 4 Vision/OCR pipeline."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import LabelScan
from app.schemas.schemas import LabelExtracted, LabelReport
from app.services.files import save_image
from app.vision.product.label_scanner import scan_label as vision_scan_label

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

    # Run the Member 4 vision pipeline
    try:
        result = vision_scan_label(str(path))
        extracted = LabelExtracted(**result.get("extracted", {}))
        findings = result.get("findings", [])
        confidence = result.get("confidence", 0.0)
        status_val = result.get("status", "unavailable")
    except Exception as e:
        print(f"[Vision] Scan error: {e}")
        extracted = LabelExtracted(raw_text="")
        findings = []
        confidence = 0.0
        status_val = "unavailable"

    report = LabelReport(
        id="",
        status=status_val,
        extracted=extracted,
        findings=findings,
        confidence=confidence,
        disclaimer=DISCLAIMER,
    )
    scan = LabelScan(
        user_id=user.id,
        image_path=str(path),
        status=report.status,
        extracted=report.extracted.model_dump(),
        findings=[f.model_dump() for f in findings],
        confidence=confidence,
    )
    db.add(scan)
    db.commit()
    return report.model_copy(update={"id": scan.id})