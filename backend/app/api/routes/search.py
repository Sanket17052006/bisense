"""Search router — Member 5 API shell.

Retrieval (embeddings / BM25 / hybrid / reranking) is owned by Member 3 (RAG).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import User
from app.schemas.schemas import SearchResponse, SearchHit
from app.services.agents.rag import RAGService


router = APIRouter(prefix="/search", tags=["search"])

_rag = RAGService()


@router.get("", response_model=SearchResponse)
def search(
    q: str = Query(..., min_length=1),
    limit: int = Query(8, ge=1, le=30),
    is_number: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ = user, db, is_number
    sources = _rag.retrieve(q, limit=limit)

    hits = [
        SearchHit(
            id=s.get("id", s.get("chunk_id", "")),
            content=s.get("text", s.get("content", ""))[:500],
            clause_ref=s.get("clause"),
            page=s.get("page") or s.get("page_number"),
            title=s.get("title") or s.get("source"),
            is_number=s.get("is_number"),
            score=float(s.get("score", s.get("hybrid_score", 0))),
            rerank_score=s.get("rerank_score"),
        )
        for s in sources
    ]

    return SearchResponse(
        query=q,
        hits=hits,
        engine="hybrid+reranker",
    )