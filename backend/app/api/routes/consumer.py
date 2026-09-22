"""Consumer router — guidance + complaint redirection."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import User
from app.schemas.schemas import InfoResponse

router = APIRouter(prefix="/consumer", tags=["consumer"])

GUIDE = (
    "How to check a product before buying:\n"
    "1. Look for the BIS Standard Mark (ISI / IS number) on the product or label.\n"
    "2. For electronics, check the CRS registration mark + registered number.\n"
    "3. For jewellery, check the BIS hallmark + HUID; verify the HUID online.\n"
    "4. Confirm the licence/CM/L number in the BIS licence database.\n"
    "5. MRP, net quantity, manufacturer/importer details and Mfg date must be printed.\n\n"
    "If a product fails these checks, you can lodge a complaint with BIS via "
    "https://bis.gov.in (or the BIS Care app) and to the consumer helpline 1915."
)


@router.get("", response_model=InfoResponse)
def consumer_guide(
    query: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ = user, db
    return InfoResponse(
        query=query or "",
        answer=GUIDE,
        disclaimer="General consumer guidance, not legal advice.",
    )


@router.get("/complaints", response_model=InfoResponse)
def complaints(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _ = user, db
    return InfoResponse(
        query="complaints",
        answer=(
            "To raise a BIS-related complaint:\n"
            "• File online through the BIS grievance/Web-care portal on bis.gov.in\n"
            "• Contact BIS (nationwide) — consumer helpline 1915.\n"
            "• Include product photos, IS number, licence number and purchase details "
            "for fastest resolution."
        ),
        disclaimer="Contact details are indicative; verify current IDs on bis.gov.in.",
    )