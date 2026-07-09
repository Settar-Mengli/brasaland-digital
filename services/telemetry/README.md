# Brasaland Telemetry API

Stub ingestion service for Brasaland inventory telemetry (v2.0.0 envelope). Accepts batched events from the backoffice `TelemetryService`, validates each envelope, and logs event types. **No persistence** in this phase — storage replaces the handler internals in the next phase.

Contract: [docs/telemetry/telemetry-plan.md](../../docs/telemetry/telemetry-plan.md) and [docs/telemetry/event-schemas.json](../../docs/telemetry/event-schemas.json).

## Architecture

```
services/telemetry/
├── app.py
├── config.py              # TELEMETRY_ENDPOINT (env pattern; unused for redirection in stub)
├── models.py              # TelemetryEvent envelope + ingest request/response
├── routers/
│   └── telemetry.py       # POST /telemetry/events
├── tests/
├── pyproject.toml
├── uv.lock
└── README.md
```

## Setup

Run from **`services/telemetry/`**:

```powershell
cd services/telemetry
uv sync
```

Requires **Python 3.11+**.

## Run

```powershell
uv run uvicorn app:app --port 8013
```

Open **http://127.0.0.1:8013/docs**

## Environment

Copy `.env.example` to `.env`:

| Variable | Purpose |
| --- | --- |
| `TELEMETRY_ENDPOINT` | Canonical ingest URL (established for future client wiring; not used for redirection in the stub) |

## API

| Method | Path | Body | Success |
| --- | --- | --- | --- |
| `POST` | `/telemetry/events` | `{"events": [<envelope>, ...]}` | **200** `{"received": N}` |

`N` is the number of events in the batch (stub contract). Invalid envelope fields on individual events are logged and skipped; wrong top-level shape returns **422**.

### Envelope fields (v2.0.0)

`eventId`, `timestamp`, `sessionId`, `userId`, `event_type`, `schemaVersion`, `requestId`, `service`, `properties`

Per-event property allowlists (`event-schemas.json`) are **not** validated in this phase.

## Tests

```powershell
uv run pytest
```

## Stub disclaimer

This service does not write to a database. The ingest handler will be extended in the storage phase with per-event JSON Schema validation and bulk insert into `telemetry_events`.
