"""Search router — Member 5 API shell.

Retrieval (embeddings / BM25 / hybrid / reranking) is owned by Member 3 (RAG).
This stub keeps the GET /api/search contract stable; hits stay empty until the
RAG pipeline is integrated.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import User
from app.schemas.schemas import SearchResponse

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchResponse)
def search(
    q: str = Query(..., min_length=1),
    limit: int = Query(8, ge=1, le=30),
    is_number: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ = user, db, q, limit, is_number
    return SearchResponse(
        query=q,
        hits=[],
        engine="unavailable",
    )