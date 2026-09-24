"""BISense AI — FastAPI application entrypoint (Members 2–6).

Run:  uvicorn app.main:app --reload --port 8000
Docs: http://localhost:8000/docs
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import engine
from app.models import models  # noqa: F401  (registers tables)
from app.db.base import Base

from app.api.routes import (
    admin,
    auth,
    certification,
    chat,
    citations,
    compliance,
    consumer,
    documents,
    hallmarking,
    history,
    labs,
    labels,
    qco,
    search,
    standards,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ensure schema exists (pgvector/sqlite agnostic)
    Base.metadata.create_all(bind=engine)
    from app.db.migrations import run_migrations

    run_migrations()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description=(
        "BISense AI — source-backed answers about BIS standards, QCOs, labs, "
        "hallmarking and product compliance. SIH 2026 PS 26107."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PREFIX = settings.api_prefix

app.include_router(auth.router, prefix=PREFIX)
app.include_router(chat.router, prefix=PREFIX)
app.include_router(search.router, prefix=PREFIX)
app.include_router(standards.router, prefix=PREFIX)
app.include_router(certification.router, prefix=PREFIX)
app.include_router(qco.router, prefix=PREFIX)
app.include_router(labs.router, prefix=PREFIX)
app.include_router(hallmarking.router, prefix=PREFIX)
app.include_router(consumer.router, prefix=PREFIX)
app.include_router(documents.router, prefix=PREFIX)
app.include_router(compliance.router, prefix=PREFIX)
app.include_router(labels.router, prefix=PREFIX)
app.include_router(citations.router, prefix=PREFIX)
app.include_router(history.router, prefix=PREFIX)
app.include_router(admin.router, prefix=PREFIX)


@app.get("/api/health", tags=["health"])
def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.version,
        "llm": (
            settings.llm_model
            if settings.openai_api_key
            else "not configured (rule-based fallback)"
        ),
        "embedder": "n/a (Member 3)",
        "reranker": "n/a (Member 3)",
        "db": "postgresql" if settings.database_url.startswith("postgresql") else "sqlite",
    }


@app.get("/", include_in_schema=False)
def root():
    return {"service": settings.app_name, "docs": "/docs"}