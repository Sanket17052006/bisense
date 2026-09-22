"""Auth hardening tests — register/login/refresh/logout, lockout, rate limiting.

Uses a SQLite test DB so no Postgres infra is required.
"""
import os
import uuid

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_bisense.db")
os.environ.setdefault("SECRET_KEY", "test-secret")

import pytest
from fastapi.testclient import TestClient

from app.api.routes import auth as auth_routes
from app.core.config import settings
from app.core.security import verify_password


@pytest.fixture(scope="module")
def client():
    from app.main import app

    settings.login_max_attempts = 3
    settings.login_lock_minutes = 15
    auth_routes.login_limiter.max_requests = 10_000
    auth_routes.login_limiter.window_seconds = 60
    with TestClient(app) as c:
        yield c


def _email(tag):
    return f"{tag}-{uuid.uuid4().hex[:8]}@example.com"


def _register(client, tag="probe", password="S3cure!pass"):
    email = _email(tag)
    resp = client.post(
        "/api/auth/register",
        json={"name": "Probe", "email": email, "password": password},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["access_token"] and body["refresh_token"]
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == settings.access_token_expire_minutes * 60
    assert body["user"]["email"] == email
    return email, body


def test_register_returns_access_and_refresh(client):
    _register(client, "reg")


def test_password_stored_as_bcrypt_hash(client):
    email, _ = _register(client, "hash")
    from sqlalchemy import select

    from app.db.session import SessionLocal
    from app.models.models import User

    db = SessionLocal()
    try:
        user = db.execute(select(User).where(User.email == email)).scalar_one()
        assert user.hashed_password.startswith("$2")
        assert "passlib" not in user.hashed_password
        assert verify_password("S3cure!pass", user.hashed_password) is True
        assert verify_password("wrong", user.hashed_password) is False
    finally:
        db.close()


def test_login_success_roundtrip(client):
    email, _ = _register(client, "login")
    resp = client.post(
        "/api/auth/login", json={"email": email, "password": "S3cure!pass"}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["access_token"] and body["refresh_token"]


def test_long_password_logs_in_after_truncation(client):
    long_pw = "x" * 100 + "A1!"
    email, _ = _register(client, "long", password=long_pw)
    resp = client.post("/api/auth/login", json={"email": email, "password": long_pw})
    assert resp.status_code == 200, resp.text


def test_wrong_password_401_and_counts_attempts(client):
    email, _ = _register(client, "badpw")
    from sqlalchemy import select

    from app.db.session import SessionLocal
    from app.models.models import User

    resp = client.post("/api/auth/login", json={"email": email, "password": "nope"})
    assert resp.status_code == 401
    db = SessionLocal()
    try:
        user = db.execute(select(User).where(User.email == email)).scalar_one()
        assert user.failed_login_attempts >= 1
    finally:
        db.close()


def test_lockout_after_max_attempts(client):
    email, body = _register(client, "lock")
    for _ in range(settings.login_max_attempts):
        resp = client.post("/api/auth/login", json={"email": email, "password": "nope"})
        assert resp.status_code == 401
    resp = client.post(
        "/api/auth/login", json={"email": email, "password": "S3cure!pass"}
    )
    assert resp.status_code == 423, resp.text
    from sqlalchemy import select

    from app.db.session import SessionLocal
    from app.models.models import User

    db = SessionLocal()
    try:
        user = db.execute(select(User).where(User.email == email)).scalar_one()
        assert user.locked_until is not None
    finally:
        db.close()


def test_refresh_rotates_and_revokes_old(client):
    email, body = _register(client, "rot")
    old_refresh = body["refresh_token"]
    resp = client.post("/api/auth/refresh", json={"refresh_token": old_refresh})
    assert resp.status_code == 200, resp.text
    new = resp.json()
    assert new["refresh_token"] != old_refresh
    # old refresh token must now be revoked
    resp = client.post("/api/auth/refresh", json={"refresh_token": old_refresh})
    assert resp.status_code == 401, resp.text
    # new one still works
    resp = client.post("/api/auth/refresh", json={"refresh_token": new["refresh_token"]})
    assert resp.status_code == 200, resp.text


def test_logout_revokes_refresh(client):
    email, body = _register(client, "out")
    refresh = body["refresh_token"]
    resp = client.post(
        "/api/auth/logout",
        json={"refresh_token": refresh},
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert resp.status_code == 200, resp.text
    resp = client.post("/api/auth/refresh", json={"refresh_token": refresh})
    assert resp.status_code == 401, resp.text


def test_me_requires_access_token(client):
    _, body = _register(client, "me")
    resp = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"}
    )
    assert resp.status_code == 200
    # a refresh token must NOT be accepted as an access token
    resp = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {body['refresh_token']}"}
    )
    assert resp.status_code == 401, resp.text
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_login_no_user_is_401(client):
    resp = client.post(
        "/api/auth/login", json={"email": _email("ghost"), "password": "whatever"}
    )
    assert resp.status_code == 401