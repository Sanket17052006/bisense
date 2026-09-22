"""Password hashing (bcrypt) + typed JWT tokens (access/refresh) with jti.

Replaces the unmaintained passlib dependency: bcrypt is used directly.
Tokens carry a ``type`` claim ("access" | "refresh") and a unique ``jti`` so
refresh tokens can be rotated and revoked via the token_blacklist table.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import settings

# bcrypt caps input at 72 bytes; truncate consistently on write+verify so
# longer passwords still authenticate (bcrypt>=4.1 raises otherwise).
_BCRYPT_MAX_BYTES = 72


def hash_password(password: str) -> str:
    raw = password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.hashpw(raw, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        raw = plain.encode("utf-8")[:_BCRYPT_MAX_BYTES]
        return bcrypt.checkpw(raw, hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def _base_payload(subject: str | int, token_type: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    return {
        "sub": str(subject),
        "type": token_type,
        "jti": uuid.uuid4().hex,
        "iat": now,
        "exp": now + timedelta(days=1),
    }


def create_token(
    subject: str | int,
    token_type: str,
    expires_delta: timedelta,
    extra: dict[str, Any] | None = None,
) -> str:
    payload = _base_payload(subject, token_type)
    payload["exp"] = datetime.now(timezone.utc) + expires_delta
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(subject: str | int, extra: dict[str, Any] | None = None) -> str:
    return create_token(
        subject,
        "access",
        timedelta(minutes=settings.access_token_expire_minutes),
        extra,
    )


def create_refresh_token(subject: str | int) -> str:
    return create_token(
        subject,
        "refresh",
        timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str, expected_type: str | None = None) -> dict[str, Any] | None:
    """Decode + verify a token. Returns the payload or None.

    When ``expected_type`` is set (e.g. "access"), mismatched token types are
    rejected so a refresh token can never be used as an access token.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except jwt.PyJWTError:
        return None
    if expected_type is not None and payload.get("type") != expected_type:
        return None
    return payload