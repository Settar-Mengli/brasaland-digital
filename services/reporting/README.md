# Brasaland Reporting API

Exposes the **Weekly Location Cost & Waste Report** produced by the Prefect ETL under
`data/pipelines/`. All `/reporting/*` and `/tasks/{task_id}` routes require a Bearer
access JWT (`brasaland-auth-verify`). Pipeline enqueue is rate-limited
(`RATE_LIMIT_REPORTING_ENQUEUE`, default `10/minute`). Docs/OpenAPI only when
`EXPOSE_DOCS=1`.

Contract: [`data/pipelines/CONTEXT-brasaland-pipeline.md`](../../data/pipelines/CONTEXT-brasaland-pipeline.md)
and [`data/pipelines/PIPELINE_DESIGN.md`](../../data/pipelines/PIPELINE_DESIGN.md).

## Architecture

```
services/reporting/
├── app.py                 # FastAPI + lifespan ensure_schema (tolerant if no DATABASE_URL)
├── celery_app.py          # Celery app (Redis broker + result backend)
├── tasks.py               # run_pipeline_task + DLQ writer
├── config.py              # .env + sys.path bootstrap for data/pipelines
├── database.py            # lazy engine + ensure_schema (imports pipelines.db_models)
├── models.py              # API request/response schemas only (CONTEXT §6)
├── routers/reporting.py   # /reporting/* endpoints
├── routers/tasks.py       # GET /tasks/{task_id}
└── Dockerfile             # copies data/ + this service (not the generic services/Dockerfile)
```

**ETL ownership:** all extract/transform/load and query/trigger helpers live in
`data/pipelines/`. This service never embeds KPI math or SQL.

## Import wiring

`data/pyproject.toml` uses `[tool.uv] package = false`, so `pipelines` is not an installable
package. **Chosen mechanism:** `config.py` inserts the repo `data/` directory on `sys.path`
(and Docker sets `PYTHONPATH=/app/data`).

**Justification:** path injection keeps Lane-1 models and Prefect flows as a single source under
`data/pipelines/` without forcing `data/` to become a published package or duplicating models
inside `services/reporting/`.

Reporting’s `pyproject.toml` lists `prefect`, `sqlmodel`, `pandas`, `psycopg2-binary`, and
`celery[redis]` so the imported `pipelines` modules and the worker resolve third-party deps
inside this service’s venv.

## Endpoints

| Method | Path | Auth | Behavior |
| --- | --- | --- | --- |
| `GET` | `/reporting/weekly-location-performance` | Bearer JWT | Optional `week_start`; default = latest computed week; CONTEXT §6 JSON |
| `GET` | `/reporting/pipeline-runs/latest` | Bearer JWT | Metadata of the most recent `pipeline_runs` row (structured null object when none exist — never a bare null body) |
| `POST` | `/reporting/pipeline-runs` | Bearer JWT (rate-limited) | Enqueues Celery `run_pipeline_task`; returns **202** `{"task_id": "..."}` immediately |
| `GET` | `/tasks/{task_id}` | Bearer JWT | Celery `AsyncResult` status: `pending` \| `started` \| `success` \| `failure` (+ `result` when terminal) |

### Async POST + poll

```powershell
# Enqueue
curl -s -X POST http://127.0.0.1:8014/reporting/pipeline-runs -H "Content-Type: application/json" -d "{}"
# → {"task_id":"<uuid>"}

# Poll until success|failure
curl -s http://127.0.0.1:8014/tasks/<uuid>
```

Optional body: `{"week_start": "YYYY-MM-DD"}` (ISO Monday preferred; same semantics as before).

## Celery retries, guard, and DLQ

- **Job-level (Celery):** `max_retries=3`, backoff `countdown = 2 ** retries` (1s, 2s, 4s).
- **Non-retryable:** `RuntimeError` whose message starts with `Concurrent run already Running` (same-week Running guard in `pipelines.pipeline.write_pipeline_run_start`) fails immediately — no Celery retry and **no** DLQ row.
- **DLQ:** after retry exhaustion only, a row is written to `reporting.task_dead_letters` (`task_id`, `task_name`, `attempt_count`, bounded `error_message`, `created_at`).
- **Prefect step-level retries** (`@task(retries=3)` inside the flow) are a **separate** layer and are not disabled by Celery.
- **`task_acks_late=True`** means a worker crash mid-run redelivers the task; the re-run is safe because the pipeline's same-week Running guard blocks concurrent duplicates and completed weeks re-upsert idempotently.

## Setup

Run from **`services/reporting/`** (use **Python 3.13** — bare 3.14 tries to build `pydantic-core` from source and fails without MSVC):

```powershell
cd services/reporting
uv sync --python 3.13
```

Requires **Python 3.11–3.13** (`requires-python = ">=3.11,<3.14"`). Copy `.env.example` to `.env` and set `DATABASE_URL` and `REDIS_URL` (same
brasaland-m5 project as inventory/telemetry). Create the `reporting` schema first via
`scripts/setup_reporting_schema.py` (operator; see design operator rollout).

When no week has been computed yet, `GET /reporting/weekly-location-performance` returns **HTTP 200** with `week_start: null` and `locations: []` (not 404).

### Docker Compose

```powershell
docker compose up --build redis flower reporting reporting-worker
```

| Service | Role |
| --- | --- |
| `redis` | Broker + result backend (`noeviction`) |
| `reporting` | FastAPI API |
| `reporting-worker` | Celery worker on queue `reporting` (`-Q reporting`; same reporting image; own `reporting_worker_venv`) |
| `flower` | Task monitor. Canonical ports: [../../docs/standards/project-context.md](../../docs/standards/project-context.md#port-assignments). (`CELERY_BROKER_URL` ← `REDIS_URL`) |

**Start / stop worker:**

```powershell
docker compose up -d reporting-worker
docker compose stop reporting-worker
```

Compose passes `DATABASE_URL` and `REDIS_URL`, mounts `./services/reporting`, `./data`, and `./packages`. The worker command is `-Q reporting`; the default Celery queue `celery` is not used. Routing is `task_default_queue` + `task_routes` in `celery_app.py`.

CI job `celery-routing` runs [../../scripts/test_celery_queue_isolation.py](../../scripts/test_celery_queue_isolation.py) against a disposable Redis (FLUSHDB; never the Compose broker).

### Optional Windows host worker

If running the worker on the Windows host (not Compose), Celery’s prefork pool is unsupported — use solo, and bind the named queue:

```powershell
cd services/reporting
uv run --python 3.13 celery -A celery_app.celery_app worker --loglevel=INFO --pool=solo -Q reporting
```

Prefer the Linux Compose worker for day-to-day work.

## Run (local API)

```powershell
uv run --python 3.13 uvicorn app:app --port 8014
```

Open **http://127.0.0.1:8014/docs**

CLI ETL (same project DATABASE_URL; bypasses the HTTP/Celery path):

```powershell
uv run --directory data python -m pipelines.pipeline
```

Use the module form (`-m`); `python pipelines/pipeline.py` raises `ModuleNotFoundError` for the `pipelines` package.

## Testing

```powershell
cd services/reporting
uv run --python 3.13 pytest
```

Expect **16** passed.

## Environment

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Supabase Postgres connection string (required at runtime) |
| `REDIS_URL` | Celery broker + result backend (API enqueue, worker, Flower) |

## Lane-1 / Lane-2

- **Lane 1:** `database.ensure_schema()` → `SQLModel.metadata.create_all` using
  `pipelines.db_models` (`schema="reporting"`). Scoped `ensure_task_dead_letters_schema()` creates
  `task_dead_letters` only.
- **Lane 2:** `scripts/setup_reporting_schema.py` — `CREATE SCHEMA` + RLS (operator-only), including
  `task_dead_letters`.
