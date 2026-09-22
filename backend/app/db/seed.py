"""Seed script — loads demo BIS standards, QCOs, labs, schemes.

Usage:
    python -m app.db.seed            # create tables + seed
    python -m app.db.seed --reset    # drop + recreate + seed
    python -m app.db.seed --force    # seed even if data exists
"""
from __future__ import annotations

import csv
import sys
from datetime import date, datetime
from pathlib import Path

from app.core.config import BASE_DIR, settings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.models import (
    CertificationScheme,
    Clause,
    Laboratory,
    ProductCategory,
    QCO,
    Standard,
    StandardRevision,
)

# Prefer the app-level data dir (settings.data_dir / "data"), which in the
# Docker image maps to /app/data; fall back to the repo-root ./data for local
# dev where the CSVs live alongside the project.
REPO_DATA = BASE_DIR.parent / "data"


def _data_dir() -> Path:
    for cand in (settings.data_dir, REPO_DATA):
        if (cand / "standards").exists():
            return cand
    return settings.data_dir


DATA_DIR = _data_dir()


def _date(v: str) -> datetime | None:
    try:
        return datetime.strptime(v.strip(), "%Y-%m-%d")
    except Exception:
        return None


def seed_standards(db) -> int:
    path = DATA_DIR / "standards" / "bis_standards.csv"
    if not path.exists():
        return 0
    count = 0
    with path.open() as fh:
        for row in csv.DictReader(fh):
            is_num = (row.get("is_number") or "").strip()
            if not is_num:
                continue
            if db.query(Standard).filter_by(is_number=is_num).first():
                continue
            std = Standard(
                is_number=is_num,
                title=row.get("title", "").strip(),
                year=int(row["year"]) if row.get("year") else None,
                category=row.get("category") or None,
                status=row.get("status", "active"),
                certification_type=row.get("certification_type") or None,
                ics_code=row.get("ics_code") or None,
                boundary=row.get("boundary") or None,
                description=row.get("description") or None,
            )
            db.add(std)
            db.flush()
            for i in range(1, 4):
                content = row.get(f"clause_{i}_content") or ""
                if not content:
                    continue
                db.add(
                    Clause(
                        standard_id=std.id,
                        clause_ref=row.get(f"clause_{i}_ref", f"{i}"),
                        content=content,
                        page=int(row.get(f"clause_{i}_page") or 1),
                    )
                )
            if row.get("revision_year"):
                db.add(
                    StandardRevision(
                        standard_id=std.id,
                        revision_year=int(row["revision_year"]),
                        amendment=row.get("amendment") or None,
                        summary=row.get("revision_summary") or None,
                        effective_from=_date(row["revision_effective"]) if row.get("revision_effective") else None,
                    )
                )
            count += 1
    return count


def seed_labs(db) -> int:
    path = DATA_DIR / "standards" / "bis_labs.csv"
    if not path.exists():
        return 0
    count = 0
    with path.open() as fh:
        for row in csv.DictReader(fh):
            name = (row.get("name") or "").strip()
            if not name:
                continue
            if db.query(Laboratory).filter_by(name=name).first():
                continue
            db.add(
                Laboratory(
                    name=name,
                    state=row.get("state"),
                    city=row.get("city"),
                    pincode=row.get("pincode"),
                    address=row.get("address"),
                    accreditations=row.get("accreditations"),
                    products=row.get("products"),
                    contact=row.get("contact"),
                )
            )
            count += 1
    return count


def seed_qcos(db) -> int:
    path = DATA_DIR / "standards" / "bis_qcos.csv"
    if not path.exists():
        return 0
    count = 0
    with path.open() as fh:
        for row in csv.DictReader(fh):
            title = (row.get("title") or "").strip()
            if not title:
                continue
            if db.query(QCO).filter_by(title=title).first():
                continue
            qco = QCO(
                title=title,
                product_category=row.get("product_category", "").strip(),
                is_number=row.get("is_number") or None,
                notification_ref=row.get("notification_ref") or None,
                gazette_date=_date(row["gazette_date"]) if row.get("gazette_date") else None,
                effective_from=_date(row["effective_from"]) if row.get("effective_from") else None,
                exemptions=row.get("exemptions") or None,
            )
            db.add(qco)
            db.flush()
            db.add(
                ProductCategory(
                    qco_id=qco.id,
                    name=qco.product_category or "General",
                    hs_code=row.get("hs_code") or None,
                    is_number=qco.is_number,
                )
            )
            count += 1
    return count


def seed_schemes(db) -> int:
    schemes = [
        {
            "name": "ISI Mark — Product Certification",
            "scheme_type": "product",
            "description": "BIS Certification Mark (ISI) for products under Indian Standards.",
            "steps": [
                "Identify applicable IS code and QCO for your product category",
                "Submit application + fee to BIS via the ManakOnline portal",
                "Appoint BIS-approved testing laboratory for product testing",
                "BIS inspection of factory (quality control, testing facilities)",
                "Grant of licence and use of ISI Mark",
                "Surveillance — periodic audits + market sampling",
            ],
            "documents_required": [
                "Application form & fee",
                "Copy of IS standard applicable",
                "Test reports from BIS-recognized lab",
                "Factory quality manual & test facilities list",
            ],
        },
        {
            "name": "Hallmarking — Gold/Silver",
            "scheme_type": "hallmarking",
            "description": "BIS Hallmarking of gold and silver jewellery/artefacts.",
            "steps": [
                "Register as jeweller with a BIS-recognized Assaying & Hallmarking Centre",
                "Send batch for fire-assay testing (XRF + cupellation for gold)",
                "Mark HUID + purity stamp (e.g. 916, 22K)",
                "Certified hallmark = quality + purity assurance",
            ],
            "documents_required": [
                "Jeweller registration",
                "Assaying & Hallmarking centre recognition",
            ],
        },
        {
            "name": "CRS — Mandatory Registration Scheme",
            "scheme_type": "sys",
            "description": "Compulsory Registration Scheme for electronics & IT goods.",
            "steps": [
                "Identify if product is in CRS schedule",
                "Self-declaration of conformity after testing in BIS-recognized lab",
                "Register as manufacturer/importer on BIS portal",
                "Obtain Registration Number & affix Standard Mark",
                "Renew periodically",
            ],
            "documents_required": ["Test report", "Self-declaration", "Company registration"],
        },
    ]
    added = 0
    for s in schemes:
        if db.query(CertificationScheme).filter_by(name=s["name"]).first():
            continue
        db.add(CertificationScheme(**s))
        added += 1
    return added


def seed_rag_index(db) -> int:
    """Reserved for Member 3 (RAG). Records are created once their ingestion
    pipeline lands; this no-op keeps the seed script's call site stable."""
    return 0


def main() -> None:
    reset = "--reset" in sys.argv
    force = reset or "--force" in sys.argv

    if reset:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        n_std = seed_standards(db)
        n_lab = seed_labs(db)
        n_qco = seed_qcos(db)
        n_sch = seed_schemes(db)
        n_chunks = 0
        if not force and n_std + n_lab + n_qco == 0 and db.query(Standard).count() == 0:
            print("Nothing to seed. Did you place data/*.csv files?")
        db.commit()
        n_chunks = seed_rag_index(db)
        db.commit()
        print(
            f"Seeded: standards={n_std} labs={n_lab} qcos={n_qco} schemes={n_sch} "
            f"rag_records={n_chunks} (force={force})"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()