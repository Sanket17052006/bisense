"""Documents router — Member 5 API shell.

Upload/list/details/delete are Member 5 infrastructure (files + DB rows).
The ingestion pipeline (parse → chunk → embed → index) is owned by Member 3
(RAG); upload leaves a Document in "pending" until that is integrated, and
reindex returns 503 until then. Admin re-scan tooling is Member 6's.
"""
from __future__ import annotations

import platform
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import Document, DocumentChunk, UploadedDocument
from app.schemas.schemas import ChunkOut, DocumentOut, Page
from app.services.files import save_upload

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentOut, status_code=201)
async def upload_document(
    file: UploadFile,
    title: str | None = None,
    doc_type: str = Query("standard", description="standard|qco|scheme|other"),
    source_url: str | None = None,
    is_number: str | None = None,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        path, fmt = save_upload(file)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    db.add(
        UploadedDocument(
            user_id=user.id,
            original_name=file.filename or path.name,
            stored_path=str(path),
            content_type=file.content_type,
            size_bytes=path.stat().st_size,
        )
    )
    doc = Document(
        title=title or (file.filename or path.stem),
        source_url=source_url,
        file_type=fmt,
        file_path=str(path),
        doc_type=doc_type,
        is_number=is_number,
        status="pending",  # Member 3 ingestion sets indexed/failed
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return DocumentOut.model_validate(doc)


@router.get("", response_model=Page[DocumentOut])
def list_documents(
    status_filter: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(Document)
    if status_filter:
        stmt = stmt.where(Document.status == status_filter)
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    rows = db.execute(stmt.order_by(Document.created_at.desc()).offset(skip).limit(limit)).scalars().all()
    return Page(items=[DocumentOut.model_validate(r) for r in rows], total=total, skip=skip, limit=limit)


@router.get("/stats/engines", response_model=dict)
def engine_stats(user=Depends(get_current_user), db: Session = Depends(get_db)):
    _ = user, db
    return {
        "embedder": "unavailable",
        "reranker": "unavailable",
        "platform": platform.platform(),
        "note": "Owned by Member 3 (RAG).",
    }


@router.get("/{document_id}", response_model=dict)
def document_detail(document_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    chunks = db.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == doc.id).order_by(DocumentChunk.chunk_index)
    ).scalars().all()
    return {
        "document": DocumentOut.model_validate(doc),
        "chunks": [ChunkOut.model_validate(c) for c in chunks],
        "total_chunks": len(chunks),
    }


@router.post("/{document_id}/reindex", response_model=DocumentOut)
def reindex_document(document_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    _ = user
    if db.get(Document, document_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    raise HTTPException(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "Ingestion pipeline owned by Member 3 (RAG) — not integrated yet.",
    )


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    _ = user
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    if doc.file_path:
        try:
            Path(doc.file_path).unlink(missing_ok=True)
        except OSError:
            pass
    db.delete(doc)
    db.commit()