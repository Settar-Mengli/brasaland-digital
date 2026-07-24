# Brasaland Telemetry API

Ingestion service for Brasaland inventory telemetry (v2.1.0 envelope). Accepts batched events from the backoffice `TelemetryService`, validates each envelope and property allowlist, derives `level` server-side, and persists rows to Supabase (`telemetry_events` on brasaland-m5).

Contract: [docs/telemetry/telemetry-plan.md](../../docs/telemetry/telemetry-plan.md) and [docs/telemetry/event-schemas.json](../../docs/telemetry/event-schemas.json). Property allowlists are bundled at `allowlists/event-schemas.json` (keep in sync with docs).

## Architecture

```
services/telemetry/
├── app.py
├── config.py
├── database.py           # engine, ensure_schema, get_session
├── db_models.py          # SQLModel telemetry_events (8 columns)
├── allowlists.py         # stage-2 required/extra-key validation
├── level.py              # derive_level()
├── repository.py         # bulk INSERT ... ON CONFLICT DO NOTHING
├── row_builder.py        # envelope → row dict
├── models.py             # TelemetryEvent envelope + ingest response (unchanged envelope)
├── analysis.py           # report metrics (Pandas)
├── cache.py              # 60s in-memory report cache
├── report_pipeline.py    # metric orchestrator
├── report_service.py     # period resolution + cache wiring
├── routers/telemetry.py  # POST /telemetry/events, GET /telemetry/report
├── allowlists/event-schemas.json
└── tests/
```

## Table schema (`telemetry_events`)

| Column | Type | Source |
| --- | --- | --- |
| `id` | BIGSERIAL PK | server-generated |
| `event_id` | TEXT UNIQUE | envelope `eventId` |
| `event_type` | TEXT | envelope `event_type` (indexed) |
| `timestamp` | TIMESTAMPTZ | envelope `timestamp` (indexed) |
| `service` | TEXT | envelope `service` |
| `level` | TEXT | derived (`warning` for `*_failed` / `*_rejected`, else `info`) |
| `tags` | JSONB | envelope `properties` (allowlist keys only) |
| `context` | JSONB | `sessionId`, `userId`, `requestId`, `schemaVersion` |

**Immutability:** append-only by convention — no UPDATE/DELETE routes exist. Corrections are out of scope for Phase 1.

**GIN index** on `tags` is Postgres-only; created by `scripts/setup_telemetry_table.py` (not asserted in SQLite tests).

## Validation stages

1. **Envelope** — `TelemetryEvent.model_validate` (Pydantic; unchanged model)
2. **Allowlist** — required keys present, no extra keys (`additionalProperties: false` semantics)

Unknown `event_type`, missing required properties, or unexpected property keys increment `rejected` without aborting the batch.

## Setup

Run from **`services/telemetry/`**:

```powershell
cd services/telemetry
uv sync
```

Requires **Python 3.11+**. Copy `.env.example` to `.env` and set `DATABASE_URL` (same brasaland-m5 project as `services/inventory`).

### Docker Compose

`inventory` and `telemetry` receive `DATABASE_URL` from the compose `environment` block (`DATABASE_URL: ${DATABASE_URL}`), not from a mounted `.env` inside the container. Export `DATABASE_URL` in your shell or root `.env` before `docker compose up`.

## Run

```powershell
uv run uvicorn app:app --port 8013
```

Open **http://127.0.0.1:8013/docs**

## Environment

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Supabase Postgres connection string (required) |
| `TELEMETRY_ENDPOINT` | Canonical ingest URL (client wiring reference) |
| `TELEMETRY_SCHEMA_PATH` | Optional override for bundled allowlist JSON |

## API

| Method | Path | Body | Success |
| --- | --- | --- | --- |
| `POST` | `/telemetry/events` | `{"events": [<envelope>, ...]}` | **200** `{"received": N, "stored": M, "rejected": R}` |

`received == stored + rejected` always. Duplicate `eventId` values count toward `rejected` (`ON CONFLICT DO NOTHING`). Wrong top-level shape returns **422**.

### Report

| Method | Path | Query params | Success |
| --- | --- | --- | --- |
| `GET` | `/telemetry/report` | Optional `start_date`, `end_date` (ISO 8601 UTC) | **200** report JSON |

Default period when both params are omitted: last **7 days** UTC (`start = now - 7d`, `end = now`). Provide **both** params or **neither** — supplying only one returns **422**.

Response shape:

```json
{
  "period": {"from": "...", "to": "..."},
  "metrics": {
    "consumption_by_location_per_day": [...],
    "order_failure_rate_per_day": [...],
    "auth_failure_rate_per_day": [...]
  }
}
```

**Cache:** in-memory, 60s TTL. Explicit date ranges cache by `(start_iso, end_iso)`. Default-period requests cache under sentinel key `("__default__",)` so repeated default calls hit cache even as `now` moves; the cached payload includes its `period` envelope. Default-period responses may lag up to 60s behind live data.

| Metric | Plan KPI | Notes |
| --- | --- | --- |
| `consumption_by_location_per_day` | KPI 1 (partial) | Count of `consumption_order_created` per `(date, location_id)` — not quantity/ingredient sum |
| `order_failure_rate_per_day` | KPI 2 (proxy) | Daily order failure ratio; true stock-out KPI needs `stock_threshold_triggered` (forward-looking) |
| `auth_failure_rate_per_day` | — | Daily login failure rate; **per-day only** — `user_login_failed` has no `location_id` (plan §7) |

**Waste-loss ratio (KPI 3):** not implemented. Live API emits `reason` values `consumption` \| `waste` only; canonical spoilage/theft ratio is forward-looking (plan §8 gap).

## Database indexes (production)

After the table exists (first service start runs `ensure_schema()`):

```bash
cd services/telemetry
uv run --python 3.13 python ../../scripts/setup_telemetry_table.py --dry-run
uv run --python 3.13 python ../../scripts/setup_telemetry_table.py
```

## Row-Level Security

After creating `telemetry_events`, re-run `scripts/enable_rls.py` (adds `telemetry_events` to the table list). FastAPI connects as table owner via `DATABASE_URL` and bypasses RLS without FORCE.

## Testing

```powershell
cd services/telemetry
uv run pytest
```

Expect **33** passed.

SQLite in-memory tests cover ingest, allowlists, level derivation, analysis metrics, and report caching. GIN index creation is not tested on SQLite.
