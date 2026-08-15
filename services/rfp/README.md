# Brasaland RFP API (Milestone 9)

Async HTTP seam for RFP PDF upload, atomic ticket create, and Celery enqueue.
Part 1 worker runs `run_intake` (convert → classify → extract → parallel department workers →
synthesize), persists metadata + department sections via repository writers, and advances
ticket status through `update_ticket_status` (`discarded` or `intake_complete`).
Part 2 worker runs `run_response` for department drafts + evaluation, then lands at
`under_evaluation`. Part 3 starts approval (`process_rfp_approval`), resumes per-dept /
CEO interrupts over HTTP, and synthesizes `FinalDocument` → `done`.

## Port

- **8017** — `http://localhost:8017`

## Endpoints

| Method | Path | Auth | Notes |
| --- | --- | --- | --- |
| `GET` | `/` | none | `{"service":"rfp","status":"ok"}` |
| `POST` | `/rfp/tickets` | JWT Bearer (owner stamped; rate-limited) | multipart PDF → **202** `{ticket_id, rfp_id, status}`; sets `owner_user_uuid` from the caller |
| `POST` | `/rfp/tickets/{ticket_id}/response` | JWT Bearer (owner or admin) | requires `status == intake_complete` (**409** otherwise); enqueues `process_rfp_response` → **202** `{ticket_id, rfp_id, status}` |
| `POST` | `/rfp/tickets/{ticket_id}/approval` | JWT Bearer (owner or admin) | requires `status == under_evaluation` (**409** otherwise); enqueues `process_rfp_approval` → **202** |
| `POST` | `/rfp/tickets/{ticket_id}/sections/{department_id}/decision` | JWT Bearer (owner or admin) | requires `waiting_for_approval`; body `{action, feedback?}` → **200** |
| `POST` | `/rfp/tickets/{ticket_id}/ceo/decision` | JWT Bearer (owner or admin) | requires `waiting_for_approval` + `ceo_approval_required`; body `{action}` → **200** |
| `GET` | `/rfp/tickets/{ticket_id}` | JWT Bearer (owner or admin) | ticket **row** status poll (not Celery AsyncResult) plus `sections[]` |

**Owner ACL:** every ticket route after create requires the caller to be the ticket `owner_user_uuid` or an admin (`is_admin`). Tickets with a NULL owner deny non-admins (**403**). Upload is rate-limited (`RATE_LIMIT_RFP_UPLOAD`, default `10/minute`). Interactive docs/OpenAPI only when `EXPOSE_DOCS=1`.

### GET payload (expanded)

`sections` is always present (empty list when none). Each entry:

`{department_id, key_aspects, draft_content, evaluation_results, approval_status, approver, approved_at, awaiting_decision}`

Ticket-level: `arbitration` (from first section eval that has it). When `status == done`,
also `final_document` (`sections`, `total_estimated_value`, `generated_at`).

`evaluation_results` may be null until Part 2 runs; after response generation it holds readability / relevance / compliance scores, `overall_pass`, loop metadata (`iterations`, `exhausted`, `needs_human_review`), and optional `ceo_approval_required`. After Part 3 start it also carries `cost` / `setup_days` / `interrupt_id` / `arbitration` / bounded node `trace` (`agent`, `input`, `output`, `timestamp` per approve/regen execution).

## Part 2 response flow

1. Client calls `POST /rfp/tickets/{id}/response` when the ticket is `intake_complete`.
2. Celery task `rfp.process_rfp_response` advances status to `drafting`, loads `RfpMetadata.departments_needed` + existing section `key_aspects`, and invokes `run_response`.
3. Per needed department: generator writes `draft_content` → readability / relevance / compliance evaluators → bounded generator↔evaluator loop (`ITERATION_LIMIT=3`).
4. On loop exhaust, the section keeps its last draft and sets `needs_human_review` / `exhausted` **inside** `evaluation_results` (ticket is never discarded for response failures).
5. Sections are updated in place by `(ticket_id, department_id)`; status advances to `under_evaluation`.

Department drafts are client-facing prose. Metadata is interpolated as a fenced `<<<METADATA>>>` block with empty/`None`/sentinel values omitted (fence delimiters stripped from values). Missing figures are not verbalized as `null` or `not stated`. Part 3 regen uses JSON `null` only on the `cost` / `setup_days` / `price_per_cover` fields, not inside `draft_content`.

## Part 3 approval flow

1. Client calls `POST /rfp/tickets/{id}/approval` when the ticket is `under_evaluation`.
2. Celery task `rfp.process_rfp_approval` extracts numbers, runs fixed §7 arbitration, flips to `waiting_for_approval`, starts per-dept interrupt threads (`thread_id = rfp-{ticket_id}:{dept}`; CEO uses `rfp-{ticket_id}:ceo`), persists `interrupt_id`s.
3. Clients approve/reject via `POST .../sections/{dept}/decision` (reject→regen in-process; exhaust → `approval_status=rejected` + `graph_outcome=exhausted`).
4. When all active depts are terminal, if `ceo_approval_required` the driver starts the CEO interrupt; otherwise synthesizes `FinalDocument` → `done`.
5. CEO approve → synthesize → `done`; CEO reject stays `waiting_for_approval` with `ceo_decision=rejected`.

Compliance §5 rules are loaded at runtime from `data/raw/CONTEXT-rfp.md` (heading `## 5.`). Generation still uses the existing `GEN_1` / `GEN_2` / `GEN_3` env failover (unchanged).

## Env

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Supabase/Postgres (brasaland-m5) or SQLite for tests |
| `REDIS_URL` | Celery broker/backend only (not the LangGraph checkpointer) |
| `RFP_CHECKPOINT_PATH` | LangGraph SQLite checkpointer DB path (default `/app/checkpoint/rfp.sqlite`) |
| `JWT_PUBLIC_KEY` | RS256 verify (same as knowledge/inventory) |
| `JWT_ALGORITHM` | default RS256 via auth-verify |
| `EXPOSE_DOCS` | When `1`/`true`, serves `/docs` and OpenAPI; default off |
| `RATE_LIMIT_RFP_UPLOAD` | SlowAPI limit for `POST /rfp/tickets` (default `10/minute`) |
| `GEN_1_BASE_URL` / `GEN_1_API_KEY` / `GEN_1_MODEL` | Primary generation tier (worker) |
| `GEN_2_BASE_URL` / `GEN_2_API_KEY` / `GEN_2_MODEL` | Failover tier 2 |
| `GEN_3_BASE_URL` / `GEN_3_API_KEY` / `GEN_3_MODEL` | Failover tier 3 |
| `GENERATION_TIMEOUT_SECONDS` | Per-attempt OpenAI client timeout (default 30) |

Compose also sets `PYTHONPATH=/app/data`. Uploaded PDFs land in host `data/raw/` (gitignored).

## Celery queues

`rfp-worker` binds `-Q rfp`. The app sets `task_default_queue="rfp"` and `task_routes` for `rfp.process_rfp`, `rfp.process_rfp_response`, and `rfp.process_rfp_approval`. It does not consume the default `celery` queue (or reporting's `reporting` queue).

```powershell
docker compose up -d rfp-worker
docker compose stop rfp-worker
```

Host worker (if not Compose) must pass `-Q rfp`:

```powershell
cd services/rfp
uv run --python 3.13 celery -A celery_app.celery_app worker --loglevel=INFO --pool=solo -Q rfp
```

CI job `celery-routing` runs [../../scripts/test_celery_queue_isolation.py](../../scripts/test_celery_queue_isolation.py) against a disposable Redis (FLUSHDB; never the Compose broker).

## Checkpointer

Part 3 persists LangGraph interrupt/resume state with `langgraph-checkpoint-sqlite`
(`SqliteSaver`). The SQLAlchemy engine stays on `psycopg2-binary` / `DATABASE_URL`.
Redis (`REDIS_URL`) remains **only** as the Celery broker/backend — not the
checkpointer.

Use `SqliteSaver.from_conn_string` via `checkpointer_cm()` in `checkpointer.py` — it
is a **context manager**. Enter it per graph operation
(`with checkpointer_cm() as saver: ...`); do not cache a process-global saver.
Path comes from `RFP_CHECKPOINT_PATH` (default `/app/checkpoint/rfp.sqlite`).
Run `python -m checkpointer` (or `run_setup()`) once to create tables.

Compose mounts the named volume `rfp_checkpoint` at `/app/checkpoint` in both
`rfp` (FastAPI resume) and `rfp-worker` (Celery start) so the same SQLite file is
shared. Limits (honest): single Docker host only; `docker compose down -v` **wipes**
in-flight checkpoints; mild SQLite lock contention is possible under many concurrent
tickets.

Compose also mounts separate named volumes `rfp_venv` and `rfp_worker_venv` over
`.venv`. After adding or changing the saver stack, refresh **both** volumes so both
containers have the packages.

## Owner column (Lane-2)

Nullable `ticket.owner_user_uuid` is **not** applied by Alembic. Operators add it once with:

```powershell
uv run --directory services/rfp python ../../scripts/add_rfp_ticket_owner_column.py
```

(Use `--dry-run` first against live `DATABASE_URL`.) Existing rows stay NULL until re-uploaded or manually backfilled; NULL owner ⇒ non-admin access is denied.

## Upload hardening

Multipart field name `file`. Server-side defenses: **10 MiB** cap (413), require `%PDF-` magic (400), store under `data/raw/` with a **uuid** filename (client filename never used in the path).

## Tests

Expect **19** tests under `services/rfp/tests/` (upload/routes, response, approval task + routes). Pipeline E2E for Parts 1→3 lives in `tests/pipelines/test_rfp_e2e_approval.py`.

```powershell
cd services/rfp
uv sync --python 3.13
uv run pytest
```

## Service layout note

`services/rfp` is the dedicated FastAPI + Celery worker process for RFP (port 8017), matching reporting/knowledge. Part 2 **extends this existing service** with new routes and the `process_rfp_response` task — it does **not** introduce a second API process.
