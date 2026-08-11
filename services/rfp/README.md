# Brasaland RFP API (Milestone 9)

Async HTTP seam for RFP PDF upload, atomic ticket create, and Celery enqueue.
Intake graph attaches in Phase 3 — the worker task is a stub until then.

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

Compose also sets `PYTHONPATH=/app/data`. Uploaded PDFs land in host `data/raw/` (gitignored).

## Tests

Expect **7** tests in `tests/test_upload_and_routes.py` (401×2, 202, 400, 413, GET/404, idempotent enqueue).

```powershell
cd services/rfp
uv sync --python 3.13
uv run pytest
```

## Deviation note

This service is a **new API process**. CONTEXT-rfp’s “no new API process” wording did not anticipate a dedicated FastAPI+worker pair; a separate service matches the established reporting/knowledge pattern, and the reporting-worker cannot cheaply host LLM/PDF deps.
