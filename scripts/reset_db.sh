#!/usr/bin/env bash
# Reset the database + reseed demo data.
set -euo pipefail
cd "$(dirname "$0")/../backend"
python -m app.db.seed --reset