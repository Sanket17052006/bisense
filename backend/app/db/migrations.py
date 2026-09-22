"""Lightweight additive migrations (no Alembic dependency).

``Base.metadata.create_all`` only creates missing tables; it does NOT add new
columns to existing ones. These run idempotent ALTER TABLEs for the columns
added after launch (login lockout on users). Postgres + SQLite safe.
"""
from __future__ import annotations

from sqlalchemy import inspect, text

from app.db.session import engine

_ADDITIVE_COLUMNS: dict[str, dict[str, str]] = {
    "users": {
        "failed_login_attempts": "ALTER TABLE users "
        "ADD COLUMN failed_login_attempts INTEGER NOT NULL DEFAULT 0",
        "locked_until": "ALTER TABLE users ADD COLUMN locked_until {ts}",
    },
}


def run_migrations() -> None:
    dialect = engine.dialect.name
    ts = "TIMESTAMP" if dialect == "postgresql" else "DATETIME"
    inspector = inspect(engine)
    existing = {t for t in inspector.get_table_names()}
    with engine.begin() as conn:
        for table, columns in _ADDITIVE_COLUMNS.items():
            if table not in existing:
                continue
            have = {c["name"] for c in inspector.get_columns(table)}
            for name, ddl in columns.items():
                if name in have:
                    continue
                conn.execute(text(ddl.format(ts=ts)))