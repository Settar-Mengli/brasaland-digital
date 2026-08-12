# Brasaland RFP API (Milestone 9)

Async HTTP seam for RFP PDF upload, atomic ticket create, and Celery enqueue.
The worker runs `run_intake` (convert → classify → extract → parallel department workers →
synthesize), persists metadata + department sections via repository writers, and advances
ticket status through `update_ticket_status` (`discarded` or `intake_complete`).

## Port

- **8017** — `http://localhost:8017`

## Endpoints

| Method | Path | Auth | Notes |
| --- | --- | --- | --- |
| `GET` | `/` | none | `{"service":"rfp","status":"ok"}` |
| `POST` | `/rfp/tickets` | JWT Bearer | multipart PDF → **202** `{ticket_id, rfp_id, status}` |
| `GET` | `/rfp/tickets/{ticket_id}` | JWT Bearer | ticket **row** status poll (not Celery AsyncResult) |

## Env

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Supabase/Postgres (brasaland-m5) or SQLite for tests |
| `REDIS_URL` | Celery broker/backend |
| `JWT_PUBLIC_KEY` | RS256 verify (same as knowledge/inventory) |
| `JWT_ALGORITHM` | default RS256 via auth-verify |
| `GEN_1_BASE_URL` / `GEN_1_API_KEY` / `GEN_1_MODEL` | Primary generation tier (worker) |
| `GEN_2_BASE_URL` / `GEN_2_API_KEY` / `GEN_2_MODEL` | Failover tier 2 |
| `GEN_3_BASE_URL` / `GEN_3_API_KEY` / `GEN_3_MODEL` | Failover tier 3 |
| `GENERATION_TIMEOUT_SECONDS` | Per-attempt OpenAI client timeout (default 30) |

Compose also sets `PYTHONPATH=/app/data`. Uploaded PDFs land in host `data/raw/` (gitignored).

## Upload hardening

Multipart field name `file`. Server-side defenses: **10 MiB** cap (413), require `%PDF-` magic (400), store under `data/raw/` with a **uuid** filename (client filename never used in the path).

## Tests

Expect **7** tests in `tests/test_upload_and_routes.py` (401×2, 202, 400, 413, GET/404, idempotent enqueue).

```powershell
cd services/rfp
uv sync --python 3.13
uv run pytest
```

## Deviation note

This service is a **new API process**. CONTEXT-rfp’s “no new API process” wording did not anticipate a dedicated FastAPI+worker pair; a separate service matches the established reporting/knowledge pattern, and the reporting-worker cannot cheaply host LLM/PDF deps.
