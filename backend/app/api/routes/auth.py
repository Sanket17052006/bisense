"""Auth router: register, login (rate-limited + lockout), refresh, logout, me.

Hardening vs. the original:
- direct bcrypt password hashing (no passlib)
- per-IP sliding-window rate limit on login
- per-account lockout after N failed attempts (persisted in the DB)
- refresh tokens (separate JWT type) with rotation + revocation on logout
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.ratelimit import SlidingWindowLimiter
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.models import TokenBlacklist, User
from app.schemas.schemas import (
    LogoutRequest,
    RefreshRequest,
    TokenOut,
    UserLogin,
    UserOut,
    UserRegister,
)

router = APIRouter(prefix="/auth", tags=["auth"])

login_limiter = SlidingWindowLimiter(
    settings.login_rate_limit_max, settings.login_rate_limit_window
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime | None) -> datetime | None:
    """SQLite returns naive datetimes; make them UTC-aware for comparisons."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _build_tokens(user: User) -> TokenOut:
    access = create_access_token(user.id, {"role": user.role, "name": user.name})
    refresh = create_refresh_token(user.id)
    return TokenOut(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserOut.model_validate(user),
    )


def _blacklisted(db: Session, jti: str) -> bool:
    return (
        db.execute(select(TokenBlacklist).where(TokenBlacklist.jti == jti))
        .scalar_one_or_none()
        is not None
    )


def _revoke(db: Session, token: str) -> None:
    """Blacklist a token's jti (no-op if not decodable / already revoked)."""
    payload = decode_token(token)
    if payload is None or payload.get("jti") is None:
        return
    if _blacklisted(db, payload["jti"]):
        return
    db.add(
        TokenBlacklist(
            jti=payload["jti"],
            token_type=payload.get("type", "unknown"),
            expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
        )
    )


@router.post("/register", response_model=TokenOut, status_code=201)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    exists = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    user = User(
        email=payload.email,
        name=payload.name,
        hashed_password=hash_password(payload.password),
        role="admin" if payload.email == "admin@bisense.ai" else "user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _build_tokens(user)


@router.post("/login", response_model=TokenOut)
def login(
    payload: UserLogin,
    request: Request,
    db: Session = Depends(get_db),
):
    client_ip = request.client.host if request.client else "unknown"
    if client_ip != "unknown" and not login_limiter.is_allowed(client_ip):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many login attempts. Please try again later.",
        )

    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()

    if user is not None:
        locked_until = _aware(user.locked_until)
        if locked_until and locked_until > _now():
            retry_after = int((locked_until - _now()).total_seconds())
            raise HTTPException(
                status.HTTP_423_LOCKED,
                f"Account locked due to too many failed attempts. Retry in {retry_after}s.",
            )

    ok = user is not None and verify_password(payload.password, user.hashed_password)
    if not ok:
        if user is not None:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= settings.login_max_attempts:
                user.locked_until = _now() + timedelta(minutes=settings.login_lock_minutes)
            db.commit()
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Invalid email or password"
        )

    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()
    db.refresh(user)
    return _build_tokens(user)


@router.post("/refresh", response_model=TokenOut)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    token = payload.refresh_token
    parsed = decode_token(token, expected_type="refresh")
    if parsed is None or parsed.get("jti") is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
    if _blacklisted(db, parsed["jti"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token revoked")
    user = db.get(User, parsed.get("sub"))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")

    # rotate: revoke the old refresh token, issue a fresh pair
    _revoke(db, token)
    db.execute(
        delete(TokenBlacklist).where(TokenBlacklist.expires_at < _now())
    )
    db.commit()
    return _build_tokens(user)


@router.post("/logout", status_code=200)
def logout(
    payload: LogoutRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _revoke(db, payload.refresh_token)
    db.commit()
    return {"detail": "Logged out"}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user