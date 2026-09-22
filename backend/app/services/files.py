"""File storage helpers for uploads."""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings

ALLOWED = {".pdf", ".txt", ".md", ".html"}


def save_upload(upload: UploadFile, subdir: str = "documents") -> tuple[Path, str]:
    suffix = Path(upload.filename or "file").suffix.lower()
    if suffix not in ALLOWED:
        raise ValueError(f"Unsupported file type '{suffix}'. Allowed: {sorted(ALLOWED)}")
    folder = settings.upload_dir / subdir
    folder.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}{suffix}"
    dest = folder / name
    with dest.open("wb") as fh:
        fh.write(upload.file.read())
    return dest, suffix[1:]


def save_image(upload: UploadFile, subdir: str = "labels") -> Path:
    folder = settings.upload_dir / subdir
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / f"{uuid.uuid4().hex}{Path(upload.filename or 'img').suffix.lower()}"
    with dest.open("wb") as fh:
        fh.write(upload.file.read())
    return dest