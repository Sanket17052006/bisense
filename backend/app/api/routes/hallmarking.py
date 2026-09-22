"""Hallmarking router (Member 2 consumer domain endpoint + data for the agent)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import CertificationScheme
from app.schemas.schemas import InfoResponse

router = APIRouter(prefix="/hallmarking", tags=["hallmarking"])

FAQ = {
    "purity": "BIS hallmarking certifies gold (916, 875, 750, 22K, 18K…) and silver "
    "(925, 958…) purity. The hallmark shows a BIS logo + purity in carat/grade + "
    "assaying centre mark + HUID (6-digit Hallmark Unique ID).",
    "huid": "The HUID (Hallmark Unique ID) is a 6-digit alphanumeric code that can be "
    "verified against the BIS hallmarking database (consumer app / website).",
    "verify": "You can verify a hallmark by entering the HUID at the BIS consumer "
    "portal or the 'Verify Hallmark' feature.",
}


@router.get("", response_model=InfoResponse)
def hallmarking(
    query: str | None = None,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # route to a pre-built answer by keyword, else general info
    q = (query or "").lower()
    if "verify" in q or "check" in q or "huid" in q:
        answer = FAQ["huid"]
    elif "purity" in q or "916" in q or "carat" in q or "k22" in q or "silver" in q:
        answer = FAQ["purity"]
    else:
        answer = (
            FAQ["purity"]
            + "\n\n"
            + "Since 2021, hallmarking of gold jewellery is mandatory in notified "
            "areas. Jewellers must register with a BIS-recognized Assaying & "
            "Hallmarking Centre."
        )
    scheme = db.execute(
        select(CertificationScheme).where(CertificationScheme.scheme_type == "hallmarking")
    ).scalars().first()
    sources = []
    if scheme:
        sources.append(
            {
                "id": scheme.id,
                "title": scheme.name,
                "score": 1.0,
                "fresh": True,
            }
        )
    return InfoResponse(
        query=query or "",
        answer=answer,
        sources=sources,
        disclaimer="Informational — confirm current mandatory-area lists and fees on bis.gov.in.",
    )