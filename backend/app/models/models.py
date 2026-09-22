"""All BISense AI database tables (Member 5 — database schema design).

User · Conversation · Message · Document · DocumentChunk · Standard ·
StandardRevision · Clause · QCO · CertificationScheme · ProductCategory ·
Laboratory · Source · Citation · ComplianceCheck · UploadedDocument · LabelScan ·
Feedback
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def _uuid() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default="user")  # user | admin
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    conversations: Mapped[list[Conversation]] = relationship(back_populates="user")


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255), default="New chat")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    user: Mapped[User] = relationship(back_populates="conversations")
    messages: Mapped[list[Message]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(16))  # user | assistant
    content: Mapped[str] = mapped_column(Text)
    intent: Mapped[str | None] = mapped_column(String(64), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    sources: Mapped[list | None] = mapped_column(JSON, nullable=True)  # list[dict]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    conversation: Mapped[Conversation] = relationship(back_populates="messages")


class Document(Base):
    """A source document ingested into the knowledge base (Member 3)."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(512))
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    file_type: Mapped[str] = mapped_column(String(32), default="pdf")  # pdf|txt|html|md
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    doc_type: Mapped[str] = mapped_column(String(64), default="standard")  # standard|qco|scheme|other
    is_number: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    published_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    superseded_by: Mapped[str | None] = mapped_column(String(512), nullable=True)
    superseded_status: Mapped[str] = mapped_column(String(32), default="active")  # active|superseded
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending|indexed|failed
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    chunks: Mapped[list[DocumentChunk]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    content: Mapped[str] = mapped_column(Text)
    clause_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)  # e.g. "Clause 2.1"
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    meta: Mapped[dict | None] = mapped_column("meta", JSON, nullable=True)
    # vector embedding stored as JSON for SQLite fallback; pgvector column used on Postgres.
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)

    document: Mapped[Document] = relationship(back_populates="chunks")


class Standard(Base):
    """BIS standard (IS code) master record."""

    __tablename__ = "standards"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    is_number: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(1024))
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="active")  # active|withdrawn|under_revision
    certification_type: Mapped[str | None] = mapped_column(String(64), nullable=True)  # mandatory|voluntary
    ics_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    boundary: Mapped[str | None] = mapped_column(Text, nullable=True)  # scope
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    revisions: Mapped[list[StandardRevision]] = relationship(
        back_populates="standard", cascade="all, delete-orphan"
    )
    clauses: Mapped[list[Clause]] = relationship(
        back_populates="standard", cascade="all, delete-orphan"
    )


class StandardRevision(Base):
    __tablename__ = "standard_revisions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    standard_id: Mapped[str] = mapped_column(
        ForeignKey("standards.id", ondelete="CASCADE"), index=True
    )
    revision_year: Mapped[int] = mapped_column(Integer)
    amendment: Mapped[str | None] = mapped_column(String(32), nullable=True)  # e.g. Amd.1
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    effective_from: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    standard: Mapped[Standard] = relationship(back_populates="revisions")


class Clause(Base):
    __tablename__ = "clauses"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    standard_id: Mapped[str] = mapped_column(
        ForeignKey("standards.id", ondelete="CASCADE"), index=True
    )
    clause_ref: Mapped[str] = mapped_column(String(128), index=True)  # e.g. "2.1"
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    content: Mapped[str] = mapped_column(Text)
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)

    standard: Mapped[Standard] = relationship(back_populates="clauses")


class QCO(Base):
    """Quality Control Order — product-wise mandatory certification."""

    __tablename__ = "qcos"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(1024))
    product_category: Mapped[str] = mapped_column(String(255), index=True)
    is_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notification_ref: Mapped[str | None] = mapped_column(String(512), nullable=True)
    gazette_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    effective_from: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    exemptions: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="in_force")  # in_force|draft

    product_categories: Mapped[list[ProductCategory]] = relationship(
        back_populates="qco"
    )


class CertificationScheme(Base):
    __tablename__ = "certification_schemes"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    scheme_type: Mapped[str] = mapped_column(String(64))  # product | hallmarking | sys
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    steps: Mapped[list | None] = mapped_column(JSON, nullable=True)  # roadmap steps
    documents_required: Mapped[list | None] = mapped_column(JSON, nullable=True)


class ProductCategory(Base):
    __tablename__ = "product_categories"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    qco_id: Mapped[str | None] = mapped_column(
        ForeignKey("qcos.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255))
    hs_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_number: Mapped[str | None] = mapped_column(String(64), nullable=True)

    qco: Mapped[QCO | None] = relationship(back_populates="product_categories")


class Laboratory(Base):
    __tablename__ = "laboratories"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(512))
    state: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    pincode: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    accreditations: Mapped[str | None] = mapped_column(Text, nullable=True)
    products: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact: Mapped[str | None] = mapped_column(String(255), nullable=True)


class Source(Base):
    """Knowledge-freshness-tracking source record (Member 6)."""

    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    url: Mapped[str] = mapped_column(String(1024), unique=True)
    title: Mapped[str] = mapped_column(String(512))
    published_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    retrieved_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=_now
    )
    last_checked: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=_now
    )
    version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    amendment: Mapped[str | None] = mapped_column(String(64), nullable=True)
    superseded_by: Mapped[str | None] = mapped_column(String(512), nullable=True)
    superseded_status: Mapped[str] = mapped_column(String(32), default="active")
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_fresh: Mapped[bool] = mapped_column(Integer, default=1)  # 0/1 (bool compat)


class Citation(Base):
    __tablename__ = "citations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    claim: Mapped[str] = mapped_column(Text)
    source_id: Mapped[str] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), index=True
    )
    quote: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    supported: Mapped[bool] = mapped_column(Integer, default=0)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class ComplianceCheck(Base):
    __tablename__ = "compliance_checks"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    product: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32))  # verified | needs_verification | potential_gap | unavailable
    findings: Mapped[list | None] = mapped_column(JSON, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class UploadedDocument(Base):
    __tablename__ = "uploaded_documents"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    original_name: Mapped[str] = mapped_column(String(512))
    stored_path: Mapped[str] = mapped_column(String(1024))
    content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="uploaded")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class LabelScan(Base):
    __tablename__ = "label_scans"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    image_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(String(32))  # verified | needs_verification | potential_gap | unavailable
    extracted: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    findings: Mapped[list | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    message_id: Mapped[str | None] = mapped_column(
        ForeignKey("messages.id", ondelete="SET NULL"), nullable=True
    )
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1..5
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class TokenBlacklist(Base):
    """Revoked JWT ids (used for refresh-token rotation + logout)."""

    __tablename__ = "token_blacklist"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    jti: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    token_type: Mapped[str] = mapped_column(String(16))  # access | refresh
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)