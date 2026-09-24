"""Application configuration loaded from environment / .env file."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- core ---
    app_name: str = "BISense AI"
    version: str = "0.1.0"
    api_prefix: str = "/api"
    env: str = "development"

    # --- security / auth ---
    secret_key: str = "dev-secret-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    refresh_token_expire_days: int = 7
    login_max_attempts: int = 5
    login_lock_minutes: int = 15
    login_rate_limit_max: int = 20
    login_rate_limit_window: int = 60  # seconds

    # --- database ---
    # Postgres+pgvector when set; SQLite fallback otherwise.
    database_url: str = "sqlite:///./bisense.db"

    # --- LLM ---
    openai_api_key: str | None = None
    llm_model: str = "gpt-4o-mini"
    llm_base_url: str | None = None
    llm_timeout: float = 30.0
    llm_max_retries: int = 2

    # --- RAG ---
    embedder: str = "tfidf"  # "sentence-transformers" | "tfidf" | "openai"
    top_k: int = 6
    rerank_top_k: int = 4
    chunk_size: int = 900
    chunk_overlap: int = 120

    # --- vision ---
    ocr_engine: str = "auto"  # "auto" | "tesseract" | "paddle" | "none"

    # --- storage ---
    upload_dir: Path = BASE_DIR / "uploads"
    data_dir: Path = BASE_DIR / "data"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

for _d in (settings.upload_dir, settings.data_dir):
    _d.mkdir(parents=True, exist_ok=True)