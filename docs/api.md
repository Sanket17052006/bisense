# API Reference — BISense AI

Base URL: `http://localhost:8000/api`. Interactive docs: `/docs` (Swagger) and `/redoc`.

All routes except `/api/auth/register`, `/api/auth/login`, `/api/auth/refresh`
and `/api/health` require header `Authorization: Bearer <access_token>`
(`/api/auth/me` and `/api/auth/logout` *also* require the Bearer token).
Everything lives behind `/api` (config `api_prefix`).

## Authentication & Users

Flow: `register` or `login` → receive **both** `access_token` (short-lived) and
`refresh_token` (7 days). When an API call returns `401`, call `POST
/api/auth/refresh` with the refresh token to get a fresh pair (the old refresh
token is revoked). Call `POST /api/auth/logout` (Bearer + refresh token in
body) to revoke the refresh token.

| Method | Path | Body | Purpose |
|--------|------|------|---------|
| POST | `/api/auth/register` | `{name, email, password}` | create user → tokens (role auto: `admin@bisense.ai`) |
| POST | `/api/auth/login` | `{email, password}` | tokens (rate-limited; locks after 5 fails/15 min) |
| POST | `/api/auth/refresh` | `{refresh_token}` | rotate to a new token pair |
| POST | `/api/auth/logout` | `{refresh_token}` | revoke the refresh token |
| GET | `/api/auth/me` | — | current user profile |

Token response shape (register/login/refresh):

```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {"id": "...", "email": "...", "name": "...", "role": "user"}
}
```

## Chat & Search
| Method | Path | Body/Query | Purpose |
|--------|------|-----------|---------|
| POST | `/api/chat` | `{message, conversation_id?, agent?}` | AI assistant |
| GET | `/api/search` | `?q=...&limit=` | global hybrid search |

## BIS Knowledge
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/standards` | list/filter: `?q=&is_number=&category=&skip=&limit=` |
| GET | `/api/standards/categories` | distinct categories |
| GET | `/api/standards/{standard_id}` | detail + clauses + revisions |
| POST | `/api/standards/range` | fetch by `{is_numbers:[]}` |
| GET | `/api/certification/roadmap` | `?is_number=` → steps to certify a product |
| GET | `/api/certification/schemes` | list certification schemes |
| GET | `/api/qco` | list QCOs `?search=&product=&status=` |
| GET | `/api/qco/{qco_id}` | QCO detail |
| GET | `/api/labs` | `?pincode=&state=&product=&limit=` filter/search labs |

## Domain Assistants (data endpoints that back agents)
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/hallmarking` | hallmarking info `?query=` |
| GET | `/api/consumer` | consumer guidance + complaints `?query=` |
| GET | `/api/consumer/complaints` | register/view complaints |

## Documents & Knowledge Base (Admin/Member 3/6)
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/documents` | multipart upload (PDF/TXT/MD/HTML) → Document (status `pending` until M3 ingestion) |
| GET | `/api/documents` | list ingested docs `?status=` |
| GET | `/api/documents/stats/engines` | embedder/reranker status (M3) |
| GET | `/api/documents/{document_id}` | detail + chunks |
| DELETE | `/api/documents/{document_id}` | remove doc + file |
| POST | `/api/documents/{document_id}/reindex` | re-run ingestion pipeline (`503` until M3 integrates) |

## Vision & Compliance
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/labels/scan` | multipart image → `LabelReport` (stub until M4) |
| POST | `/api/compliance/check` | run a compliance gap check (stub until M4) |
| GET | `/api/compliance/overview` | dashboard stats |
| GET | `/api/compliance/checks` | recent compliance checks |
| GET | `/api/compliance/checks/{check_id}` | detail |

## Chat history (Member 5)
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/history` | current user's conversations + messages |
| GET | `/api/history/{conversation_id}` | one conversation's detail |
| DELETE | `/api/history/{conversation_id}` | delete a conversation |

## Verification (Member 6)
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/citations/validate` | `{claim, source_ids[]}` → confidence (stub until M6) |
| GET | `/api/citations/sources` | source list with freshness |
| GET | `/api/citations/sources/{source_id}` | freshness detail |
| GET | `/api/citations/recent` | most recent citation validations |

## Admin (Member 6)
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/admin/analytics` | queries, documents, hallu reports |
| GET | `/api/admin/users` | user list |
| POST | `/api/admin/users/{user_id}/role` | change role (`user`/`admin`) |
| GET | `/api/admin/freshness` | superseded/amended source report |

## System
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health` | unauthenticated; app/db/llm flags |

## Response shapes (examples)

> These are the **target contracts** for the final integrated product. Live
> stubs return placeholder values today: `POST /api/chat` returns
> `unsupported=true` with `sources=[]` until Member 2/3 integrate,
> `/api/labels/scan` and `/api/compliance/check` return `status="unavailable"`
> until Member 4 integrates, and `/api/citations/validate` returns
> `validated=false` until Member 6 integrates. Key names and structure match
> the actual schema now.

```jsonc
// POST /api/chat  (target once Member 2 + 3 integrate)
{
  "reply": "IS 302-2-1 ... Clause 2 of IS 302-2-1 covers ...",
  "intent": "standards",
  "agent": "standards",
  "confidence": 0.91,
  "conversation_id": "...",
  "sources": [
    {
      "id": "src_1",
      "title": "IS 302-2-1: Safety of household appliances",
      "is_number": "IS 302-2-1",
      "chapter": "Clause 2",
      "page": 4,
      "year": 2009,
      "score": 0.88,
      "fresh": true,
      "amendment": null,
      "superseded": false
    }
  ],
  "unsupported": false,
  "disclaimer": null
}
```

```jsonc
// POST /api/labels/scan  (target once Member 4 integrates; today: status="unavailable")
{
  "id": "scan_1",
  "status": "potential_gap",
  "extracted": {
    "is_number": "IS 302-2-1", "licence_number": "CM/L-4110890",
    "mrp": "₹1,299", "quantity": "30 L", "manufacturer": "ABC Ltd",
    "hsn_code": null
  },
  "findings": [
    {"check": "Standard marking (IS) present", "status": "verified", "detail": "Found 'IS 302-2-1'"},
    {"check": "Valid licence number format", "status": "needs_verification", "detail": "Format OK; confirm with BIS"},
    {"check": "Mandatory declaration fields", "status": "potential_gap", "detail": "Max Retail Price missing"}
  ],
  "confidence": 0.82,
  "disclaimer": "This is a technical scan, not a legal determination of compliance."
}
```

---

# Integration Contract (Member 5 → Members 1, 2, 3, 4, 6)

Member 5 owns: `app/api/routes/` (router shells), `app/schemas/schemas.py`,
`app/models/models.py`, `app/db/`, `app/core/`. Everything else is owned by the
member named below. Use these seams — **don't rewrite auth, DB session, or the
route entry points.**

## Rules that keep the merge clean

1. **Route paths are frozen.** Own your feature inside the existing router →
   service → schema structure. Replace the *implementation* of
   `app/services/...`, never the `@router` path or the `response_model`.
2. **`schemas.py` is the contract.** Add new fields/routes there;
   `response_model` stays so the API shape is stable for the frontend.
3. **New DB tables** → add the model in `app/models/models.py`,
   then register an `ALTER TABLE`/`CREATE TABLE` in
   `app/db/migrations.py` (no Alembic; runs idempotently at boot).
4. **Auth is already wired** — read the user via `Depends(get_current_user)`
   from `app/api/deps.py`; never hand-roll JWT checks.

## Per member

### Member 1 — Frontend
- Call `http://localhost:8000/api/...` (CORS is wide open for dev).
- Auth flow to implement: `register`/`login` → store `access_token` +
  `refresh_token`; on a `401` call `/api/auth/refresh` and retry; `logout`
  sends the refresh token. On lockout (`423`) or rate-limit (`429`) show a
  retry message.
- Health: `GET /api/health` (returns `db`, `llm`, `embedder` flags).

### Member 2 — AI Chat & Agents
- **Seam:** `app/api/routes/chat.py` → `app/services/agents/` (router, agents,
  llm, prompts). Replace the internals; keep `ChatRequest`/`ChatResponse`.
- Tables ready: `Conversation`, `Message` (rows are written by the chat route —
  reuse it). `app/schemas/schemas.py` documents the intent enum the frontend
  expects: `standards | certification | qco | lab | hallmarking | consumer |
  general` — today's stub always returns `intent="general"` and
  `unsupported=true` until you integrate.
- LLM env is already read by config (`OPENAI_API_KEY`, `LLM_MODEL`,
  `LLM_BASE_URL`), but **no LLM call is wired yet** — `chat.py` returns a
  static placeholder reply. Swap the internals freely.

### Member 3 — RAG & Knowledge Base
- **Seam:** `app/services/rag/` (ingestion, chunking, embeddings, vector_store,
  retrieval, reranking) + `app/api/routes/documents.py`.
- Tables ready: `Document`, `DocumentChunk`, `Clause`, `StandardRevision`.
  `DocumentChunk.embedding` is JSON today (works on SQLite + Postgres).
  **pgvector decision is yours:** if you add a real `vector(D)` column,
  coordinate the dimension here; otherwise keep JSON or bring Qdrant.
- Documents already upload via `POST /api/documents` (status stays `pending`);
  `POST .../reindex` returns `503` until your pipeline lands. `app/db/seed.py`
  exposes `seed_rag_index()` as an idempotent **no-op** — there is no TF-IDF or
  vector index yet; implement that (or your own ingestion) so demo data gets
  indexed.

### Member 4 — Computer Vision & Compliance
- **Seam:** `app/api/routes/labels.py` → `app/services/vision/` and
  `app/api/routes/compliance.py` → `app/services/compliance/`.
- Tables ready: `UploadedDocument`, `LabelScan`, `ComplianceCheck`. Statuses:
  `verified | needs_verification | potential_gap | unavailable` (never claim
  legal compliance from an image alone).
- OCR is env-switchable: `OCR_ENGINE=tesseract|paddle|none`.

### Member 6 — Verification, Admin & DevOps
- **Seam:** `app/services/verification/` (freshness, citations, confidence),
  `app/api/routes/admin.py`, `app/api/routes/citations.py`.
- Tables ready: `Source`, `Citation`, `Feedback`.
- Docker/CI already scaffolded (`Dockerfile`, `docker-compose.yml` with
  `pgvector/pgvector:pg16`, `.github/workflows/ci.yml`). Run locally against
  Postgres: `docker compose up -d postgres backend`. New additive schema →
  `app/db/migrations.py`.

## Verified working (Member 5)
- 16 API areas (15 routers + inline `health`) registered — 39 paths in OpenAPI.
- 19 tables (incl. `token_blacklist`) — `create_all` + additive migrations at
  boot; portable SQLAlchemy types (JSON for embeddings today) so they work on
  SQLite and the pgvector/Postgres image in `docker-compose.yml`.
- Seeded demo data: 12 standards / 6 QCOs / 9 labs / 3 certification schemes.
- Full auth flow (register/login/refresh/logout, lockout after 5 fails/15 min,
  per-IP rate-limit) — covered by tests: CI runs `pytest -q`, 12 passing.

RAG/agent/vision/verification routes are live contract stubs that return a
clear "owned by Member X" payload until each owner integrates — the API shape
never changes.