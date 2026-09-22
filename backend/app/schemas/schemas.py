"""Pydantic request/response schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field

T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    skip: int = 0
    limit: int = 0


# ---------- auth ----------
class UserRegister(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(ORMModel):
    id: str
    email: str
    name: str
    role: str


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 0  # access-token TTL in seconds
    user: UserOut


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


# ---------- chat ----------
class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: str | None = None
    agent: str | None = None


class SourceOut(BaseModel):
    id: str
    title: str
    is_number: str | None = None
    chapter: str | None = None
    page: int | None = None
    year: int | None = None
    score: float = 0.0
    fresh: bool = True
    amendment: str | None = None
    superseded: bool = False


class ChatResponse(BaseModel):
    reply: str
    intent: str
    agent: str | None = None
    confidence: float
    conversation_id: str
    sources: list[SourceOut] = []
    unsupported: bool = False
    disclaimer: str | None = None


# ---------- standards ----------
class ClauseOut(ORMModel):
    id: str
    clause_ref: str
    title: str | None
    content: str
    page: int | None


class RevisionOut(ORMModel):
    id: str
    revision_year: int
    amendment: str | None
    summary: str | None
    effective_from: datetime | None


class StandardOut(ORMModel):
    id: str
    is_number: str
    title: str
    year: int | None
    category: str | None
    status: str
    certification_type: str | None
    ics_code: str | None
    boundary: str | None
    description: str | None
    clauses: list[ClauseOut] = []
    revisions: list[RevisionOut] = []


class StandardRef(BaseModel):
    is_number: str
    title: str
    year: int | None = None
    category: str | None = None


class StandardRangeRequest(BaseModel):
    is_numbers: list[str]


# ---------- certification ----------
class ScheduleStep(BaseModel):
    title: str
    detail: str | None = None
    duration_days: int | None = None


class CertificationRoadmap(BaseModel):
    is_number: str | None = None
    title: str
    scheme: str
    scheme_type: str
    steps: list[dict]
    documents_required: list[str] = []
    disclaimer: str | None = None


# ---------- qco ----------
class ProductCategoryOut(ORMModel):
    id: str
    name: str
    hs_code: str | None
    is_number: str | None


class QCOOut(ORMModel):
    id: str
    title: str
    product_category: str
    is_number: str | None
    notification_ref: str | None
    gazette_date: datetime | None
    effective_from: datetime | None
    exemptions: str | None
    status: str
    product_categories: list[ProductCategoryOut] = []


# ---------- labs ----------
class LabOut(ORMModel):
    id: str
    name: str
    state: str | None
    city: str | None
    pincode: str | None
    address: str | None
    accreditations: str | None
    products: str | None
    contact: str | None
    distance_km: float | None = None


# ---------- search ----------
class SearchHit(BaseModel):
    id: str
    content: str
    clause_ref: str | None = None
    page: int | None = None
    title: str | None = None
    is_number: str | None = None
    score: float
    rerank_score: float | None = None


class SearchResponse(BaseModel):
    query: str
    hits: list[SearchHit] = []
    engine: str


# ---------- documents ----------
class DocumentOut(ORMModel):
    id: str
    title: str
    source_url: str | None
    file_type: str
    doc_type: str
    is_number: str | None
    status: str
    chunk_count: int
    error: str | None
    superseded_status: str
    created_at: datetime | None


class ChunkOut(ORMModel):
    id: str
    chunk_index: int
    content: str
    clause_ref: str | None
    page: int | None
    meta: dict[str, Any] | None


# ---------- compliance ----------
class ComplianceCheckRequest(BaseModel):
    product_type: str | None = None
    is_number: str | None = None
    extracted: dict | None = None


class ComplianceFinding(BaseModel):
    check: str
    status: str  # verified | needs_verification | potential_gap | unavailable
    detail: str


class ComplianceCheckOut(ORMModel):
    id: str
    product: str | None
    is_number: str | None
    status: str
    findings: list[ComplianceFinding] = []
    summary: str | None
    confidence: float
    created_at: datetime | None


class ComplianceOverview(BaseModel):
    total_checks: int
    verified: int
    needs_verification: int
    potential_gap: int
    unavailable: int
    avg_confidence: float
    recent: list[ComplianceCheckOut] = []


# ---------- labels ----------
class LabelExtracted(BaseModel):
    is_number: str | None = None
    licence_number: str | None = None
    mrp: str | None = None
    quantity: str | None = None
    manufacturer: str | None = None
    product_name: str | None = None
    batch: str | None = None
    hsn_code: str | None = None
    raw_text: str = ""


class LabelReport(BaseModel):
    id: str
    status: str
    extracted: LabelExtracted
    findings: list[ComplianceFinding]
    confidence: float
    disclaimer: str


# ---------- citations ----------
class CitationValidateRequest(BaseModel):
    claim: str
    source_ids: list[str] | None = None


class FreshnessOut(BaseModel):
    id: str
    url: str
    title: str
    published_date: datetime | None
    retrieved_date: datetime | None
    last_checked: datetime | None
    version: str | None
    amendment: str | None
    superseded_by: str | None
    superseded_status: str
    http_status: int | None
    is_fresh: bool


class CitationOut(BaseModel):
    citation_id: str
    claim: str
    quote: str | None
    evidence_score: float
    confidence: float
    supported: bool
    checked_at: datetime | None
    source: FreshnessOut | None


# ---------- history ----------
class MessageOut(ORMModel):
    id: str
    role: str
    content: str
    intent: str | None
    confidence: float | None
    sources: list[dict] | None
    created_at: datetime


class ConversationOut(ORMModel):
    id: str
    title: str
    created_at: datetime
    messages: list[MessageOut] = []


# ---------- admin ----------
class AdminAnalytics(BaseModel):
    total_users: int
    total_messages: int
    total_documents: int
    indexed_documents: int
    failed_documents: int
    total_sources: int
    stale_sources: int
    intent_counts: dict[str, int]
    avg_confidence: float
    hallucination_flags: int
    total_qcos: int
    total_labs: int


# ---------- consumer / hallmark / misc ----------
class InfoResponse(BaseModel):
    query: str
    answer: str
    sources: list[SourceOut] = []
    disclaimer: str | None = None


class FeedbackCreate(BaseModel):
    message_id: str
    rating: int = Field(ge=1, le=5)
    comment: str | None = None