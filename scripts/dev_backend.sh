#!/usr/bin/env bash
# One-command dev bootstrap: backend (uvicorn) + seed demo data.
echo "==> Seeding demo data (standards, labs, QCOs, schemes)"
(cd "$(dirname "$0")/../backend" && python -m app.db.seed --force || true)

echo "==> Starting backend on :8000"
(cd "$(dirname "$0")/../backend" && exec uvicorn app.main:app --reload --port 8000)