from __future__ import annotations

import re

from sqlalchemy import or_, select

from app.db.session import SessionLocal
from app.models.models import Laboratory, QCO, Standard

RESULT_LIMIT = 3


def _is_number(message: str) -> str | None:
    """Extract an IS number reference like IS 302-2-1 or IS:1234."""
    match = re.search(
        r"\bIS\s*\d[\d.\-:]*\b",
        message,
        re.IGNORECASE,
    )
    return match.group(0).upper() if match else None


def _tokens(message: str) -> list[str]:
    """Lowercased keyword tokens of length >= 3 for loose matching."""
    return [
        token
        for token in re.findall(r"[a-zA-Z0-9][a-zA-Z0-9\-]{2,}", message)
        if token.lower() not in {"the", "and", "for", "what", "whats"}
    ]


def _standards(db, message: str, number: str | None, tokens) -> list:
    conditions = []
    if number:
        like = f"%{number.split()[-1]}%"
        conditions.append(Standard.is_number.ilike(like))
    for token in tokens:
        conditions.append(Standard.title.ilike(f"%{token}%"))
        conditions.append(Standard.description.ilike(f"%{token}%"))
    if not conditions:
        return []
    return list(
        db.execute(
            select(Standard).where(or_(*conditions)).limit(RESULT_LIMIT)
        ).scalars().all()
    )


def _qcos(db, message: str, number: str | None, tokens) -> list:
    conditions = []
    if number:
        like = f"%{number.split()[-1]}%"
        conditions.append(QCO.is_number.ilike(like))
    for token in tokens:
        conditions.append(QCO.title.ilike(f"%{token}%"))
        conditions.append(QCO.product_category.ilike(f"%{token}%"))
    if not conditions:
        return []
    return list(
        db.execute(
            select(QCO).where(or_(*conditions)).limit(RESULT_LIMIT)
        ).scalars().all()
    )


def _labs(db, message: str, tokens) -> list:
    conditions = []
    for token in tokens:
        conditions.append(Laboratory.name.ilike(f"%{token}%"))
        conditions.append(Laboratory.products.ilike(f"%{token}%"))
        conditions.append(Laboratory.state.ilike(f"%{token}%"))
    if not conditions:
        return []
    return list(
        db.execute(
            select(Laboratory).where(or_(*conditions)).limit(RESULT_LIMIT)
        ).scalars().all()
    )


def _format_standards(rows) -> str:
    lines = []
    for row in rows:
        parts = [f"{row.is_number} ({row.year or 'year n/a'})"]
        if row.title:
            parts.append(row.title)
        if row.boundary:
            parts.append(row.boundary[:200])
        lines.append("- " + ": ".join(parts))
    return "\n".join(lines)


def _format_qcos(rows) -> str:
    lines = []
    for row in rows:
        parts = [f"QCO — {row.title}"]
        if row.product_category:
            parts.append(f"Products: {row.product_category}")
        if row.is_number:
            parts.append(f"IS: {row.is_number}")
        if row.status:
            parts.append(f"Status: {row.status}")
        lines.append("- " + ": ".join(parts))
    return "\n".join(lines)


def _format_labs(rows) -> str:
    lines = []
    for row in rows:
        parts = [row.name]
        if row.city and row.state:
            parts.append(f"{row.city}, {row.state}")
        elif row.state:
            parts.append(row.state)
        if row.products:
            parts.append(f"Products: {row.products}")
        lines.append("- " + ": ".join(parts))
    return "\n".join(lines)


def rule_based_answer(intent: str, message: str) -> str:
    """Determine a grounded answer from the seeded BIS knowledge base.

    Used when the LLM is not configured (offline / zero-infra demo). Only
    returns information that actually exists in the database; otherwise it
    clearly says nothing could be verified.
    """
    number = _is_number(message)
    tokens = [t.lower() for t in _tokens(message) if t.lower() not in {"bis"}]
    query = message.strip().rstrip("?.")

    try:
        db = SessionLocal()
        try:
            if intent == "lab":
                rows, formatter = _labs(db, query, tokens), _format_labs
            elif intent == "qco":
                rows, formatter = _qcos(db, query, number, tokens), _format_qcos
            else:
                rows, formatter = _standards(db, query, number, tokens), _format_standards
        finally:
            db.close()
    except Exception:
        rows, formatter = [], None

    if rows and formatter:
        return (
            "Here's what I found in the BIS knowledge base "
            "(offline response — no live AI):\n" + formatter(rows)
        )

    return (
        "I couldn't find specific information about \u201c"
        f"{message}\u201d in the BIS knowledge base. "
        "Please verify against official BIS publications (bis.gov.in)."
    )