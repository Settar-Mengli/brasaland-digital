# Brasaland Reporting API

Exposes the **Weekly Location Cost & Waste Report** produced by the Prefect ETL under
`data/pipelines/`. Port **8014**. No authentication on these routes (same convention as
inventory/telemetry GETs; H3 auth arc later).

Contract: [`data/pipelines/CONTEXT-brasaland-pipeline.md`](../../data/pipelines/CONTEXT-brasaland-pipeline.md)
and [`data/pipelines/PIPELINE_DESIGN.md`](../../data/pipelines/PIPELINE_DESIGN.md).

## Architecture

```
services/reporting/
├── app.py                 # FastAPI + lifespan ensure_schema (tolerant if no DATABASE_URL)
├── config.py              # .env + sys.path bootstrap for data/pipelines
├── database.py            # lazy engine + ensure_schema (imports pipelines.db_models)
├── models.py              # API request/response schemas only (CONTEXT §6)
├── routers/reporting.py   # three /reporting/* endpoints → pipelines.api only
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

Reporting’s `pyproject.toml` lists `prefect`, `sqlmodel`, `pandas`, and `psycopg2-binary` so the
imported `pipelines` modules resolve third-party deps inside this service’s venv.

## Endpoints

| Method | Path | Behavior |
| --- | --- | --- |
| `GET` | `/reporting/weekly-location-performance` | Optional `week_start`; default = latest computed week; CONTEXT §6 JSON |
| `GET` | `/reporting/pipeline-runs/latest` | Metadata of the most recent `pipeline_runs` row (structured null object when none exist — never a bare null body) |
| `POST` | `/reporting/pipeline-runs` | Triggers a run **synchronously** and returns completed run metadata |

### Sync POST note

`POST /reporting/pipeline-runs` runs the Prefect flow **in-process** and blocks the HTTP request
until the run finishes (Completed or Failed metadata). Long weeks can exceed typical HTTP
timeouts. An async/queued trigger is a **deliberate follow-up** and is **not** implemented in
this milestone (no `BackgroundTasks`, no job queue).

## Setup

Run from **`services/reporting/`** (use **Python 3.13** — bare 3.14 tries to build `pydantic-core` from source and fails without MSVC):

```powershell
cd services/reporting
uv sync --python 3.13
```

Requires **Python 3.11–3.13** (`requires-python = ">=3.11,<3.14"`). Copy `.env.example` to `.env` and set `DATABASE_URL` (same
brasaland-m5 project as inventory/telemetry). Create the `reporting` schema first via
`scripts/setup_reporting_schema.py` (operator; see design operator rollout).

When no week has been computed yet, `GET /reporting/weekly-location-performance` returns **HTTP 200** with `week_start: null` and `locations: []` (not 404).

### Docker Compose

```powershell
docker compose up reporting
```

Compose passes `DATABASE_URL: ${DATABASE_URL}` and mounts `./services/reporting` plus `./data`.

## Run (local)

```powershell
uv run --python 3.13 uvicorn app:app --port 8014
```

Open **http://127.0.0.1:8014/docs**

CLI ETL (same project DATABASE_URL):

```powershell
uv run --directory data python -m pipelines.pipeline
```

Use the module form (`-m`); `python pipelines/pipeline.py` raises `ModuleNotFoundError` for the `pipelines` package.

## Environment

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Supabase Postgres connection string (required at runtime) |

## Lane-1 / Lane-2

- **Lane 1:** `database.ensure_schema()` → `SQLModel.metadata.create_all` using
  `pipelines.db_models` (`schema="reporting"`).
- **Lane 2:** `scripts/setup_reporting_schema.py` — `CREATE SCHEMA` + RLS (operator-only).
