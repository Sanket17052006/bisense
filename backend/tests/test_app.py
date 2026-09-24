"""Smoke test — app boots and all API areas are registered.

Member 5 scope only: auth/database/API shells. RAG/chunking/BM25 tests belong
to Member 3 and live in their branch once integrated.
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_bisense.db")
os.environ.setdefault("SECRET_KEY", "test-secret")


def test_app_boots():
    from app.main import app

    assert app.title == "BISense AI"
    routes = set(app.openapi()["paths"])
    for expected in (
        "/api/auth/login",
        "/api/chat",
        "/api/search",
        "/api/standards",
        "/api/certification/roadmap",
        "/api/qco",
        "/api/labs",
        "/api/hallmarking",
        "/api/consumer",
        "/api/documents",
        "/api/compliance/overview",
        "/api/labels/scan",
        "/api/citations/validate",
        "/api/history",
        "/api/admin/analytics",
        "/api/health",
    ):
        assert expected in routes, f"missing route {expected}"


def test_health_ok():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        resp = client.get("/api/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"


def test_health_reports_member2_llm_status():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        body = client.get("/api/health").json()
        assert "llm" in body
        assert body["llm"] != "n/a (Member 2)"
