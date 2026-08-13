# Brasaland RFP API (Milestone 9)

Async HTTP seam for RFP PDF upload, atomic ticket create, and Celery enqueue.
Part 1 worker runs `run_intake` (convert → classify → extract → parallel department workers →
synthesize), persists metadata + department sections via repository writers, and advances
ticket status through `update_ticket_status` (`discarded` or `intake_complete`).
Part 2 worker runs `run_response` for department drafts + evaluation, then lands at
`under_evaluation`.

## Port

- **8017** — `http://localhost:8017`

## Endpoints

| Method | Path | Auth | Notes |
| --- | --- | --- | --- |
| `GET` | `/` | none | `{"service":"rfp","status":"ok"}` |
| `POST` | `/rfp/tickets` | JWT Bearer | multipart PDF → **202** `{ticket_id, rfp_id, status}` |
| `POST` | `/rfp/tickets/{ticket_id}/response` | JWT Bearer | requires `status == intake_complete` (**409** otherwise); enqueues `process_rfp_response` → **202** `{ticket_id, rfp_id, status}` |
| `GET` | `/rfp/tickets/{ticket_id}` | JWT Bearer | ticket **row** status poll (not Celery AsyncResult) plus `sections[]` |

### GET payload (expanded)

`sections` is always present (empty list when none). Each entry:

`{department_id, key_aspects, draft_content, evaluation_results, approval_status}`

`evaluation_results` may be null until Part 2 runs; after response generation it holds readability / relevance / compliance scores, `overall_pass`, loop metadata (`iterations`, `exhausted`, `needs_human_review`), and optional `ceo_approval_required`.

## Part 2 response flow

1. Client calls `POST /rfp/tickets/{id}/response` when the ticket is `intake_complete`.
2. Celery task `rfp.process_rfp_response` advances status to `drafting`, loads `RfpMetadata.departments_needed` + existing section `key_aspects`, and invokes `run_response`.
3. Per needed department: generator writes `draft_content` → readability / relevance / compliance evaluators → bounded generator↔evaluator loop (`ITERATION_LIMIT=3`).
4. On loop exhaust, the section keeps its last draft and sets `needs_human_review` / `exhausted` **inside** `evaluation_results` (ticket is never discarded for response failures).
5. Sections are updated in place by `(ticket_id, department_id)`; status advances to `under_evaluation`.

Compliance §5 rules are loaded at runtime from `data/raw/CONTEXT-rfp.md` (heading `## 5.`). Generation still uses the existing `GEN_1` / `GEN_2` / `GEN_3` env failover (unchanged).

## Env

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Supabase/Postgres (brasaland-m5) or SQLite for tests |
| `REDIS_URL` | Celery broker/backend + LangGraph Redis checkpointer |
| `JWT_PUBLIC_KEY` | RS256 verify (same as knowledge/inventory) |
| `JWT_ALGORITHM` | default RS256 via auth-verify |
| `GEN_1_BASE_URL` / `GEN_1_API_KEY` / `GEN_1_MODEL` | Primary generation tier (worker) |
| `GEN_2_BASE_URL` / `GEN_2_API_KEY` / `GEN_2_MODEL` | Failover tier 2 |
| `GEN_3_BASE_URL` / `GEN_3_API_KEY` / `GEN_3_MODEL` | Failover tier 3 |
| `GENERATION_TIMEOUT_SECONDS` | Per-attempt OpenAI client timeout (default 30) |

Compose also sets `PYTHONPATH=/app/data`. Uploaded PDFs land in host `data/raw/` (gitignored).

## Checkpointer

Part 3 persists LangGraph interrupt/resume state with `langgraph-checkpoint-redis`
(`RedisSaver`). The SQLAlchemy engine stays on `psycopg2-binary` / `DATABASE_URL`;
the checkpointer is separate and reads `REDIS_URL` (the shared compose Redis used
by Celery).

Use `RedisSaver.from_conn_string` via `checkpointer_cm()` in `checkpointer.py` — it
is a **context manager**. Enter it per graph operation
(`with checkpointer_cm() as saver: ...`); do not cache a process-global saver.
Run `python -m checkpointer` (or `run_setup()`) once so the saver can create its
indexes (calls `FT.INFO`).

The compose `redis` service must be `redis/redis-stack-server` (RediSearch +
RedisJSON). Plain `redis:7-alpine` cannot serve those modules.

Compose mounts separate named volumes `rfp_venv` and `rfp_worker_venv` over
`.venv`. After adding or changing the saver stack, refresh **both** volumes so the
FastAPI container (resume) and the Celery worker (initial run) both have the
packages.

## Upload hardening

Multipart field name `file`. Server-side defenses: **10 MiB** cap (413), require `%PDF-` magic (400), store under `data/raw/` with a **uuid** filename (client filename never used in the path).

## Tests

Expect **11** tests in `tests/test_upload_and_routes.py` (auth, upload hardening, idempotent enqueue, response 401/409/202, GET `sections`).

```powershell
cd services/rfp
uv sync --python 3.13
uv run pytest
```

## Service layout note

`services/rfp` is the dedicated FastAPI + Celery worker process for RFP (port 8017), matching reporting/knowledge. Part 2 **extends this existing service** with new routes and the `process_rfp_response` task — it does **not** introduce a second API process.
