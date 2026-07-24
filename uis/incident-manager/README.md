# Brasaland Incident Manager UI

Next.js frontend for Brasaland Operations to register incidents, filter the incident list, update status inline, and review summary metrics. Consumes the live **`services/incident-manager`** API via same-origin Next.js rewrites (no backend CORS changes).

**Authentication:** The incident API has **no auth** — this app does not use login, JWT, or `Authorization` headers.

## Setup

Run commands from **`uis/incident-manager/`**.

### Environment

Copy `.env.example` to `.env.local`:

```powershell
cd uis/incident-manager
copy .env.example .env.local
```

| Variable | Purpose |
| --- | --- |
| `NEXT_PUBLIC_INCIDENTS_API_URL` | Same-origin proxy base → `http://localhost:3004/api/incidents` |

Rewrites in `next.config.ts` forward `/api/incidents/*` to `services/incident-manager`. Canonical ports: [../../docs/standards/project-context.md](../../docs/standards/project-context.md#port-assignments).

### Dev server

```powershell
npm run dev
```

Open **http://127.0.0.1:3004**

## Routes

| Path | Description |
| --- | --- |
| `/` | Landing with links to the three views |
| `/register` | Incident registration form (branch highlight when `origin` is `branch`) |
| `/incidents` | Filterable list with inline status updates (valid transitions only; revert on failure) |
| `/summary` | Aggregated metrics by status, category, origin, and branch |

## Manual test flow

1. Start the incident API: `cd services/incident-manager && uv run uvicorn app:app --port 8011`
2. Ensure `.env` has `DATABASE_URL` (same brasaland-m5 project as inventory)
3. Seed historical data (once): `cd services/incident-manager && uv run python scripts/seed_incidents.py` — expect **97 inserted**, **3 rejected**
4. `cd uis/incident-manager && npm run dev`
5. Open **http://127.0.0.1:3004/register** — submit a valid incident; confirm success message
6. Open **/incidents** — verify seeded rows; change a status (e.g. `open` → `in_progress`); try an illegal transition and confirm revert + error message
7. Open **/summary** — verify totals and breakdown cards match the data

## API client

All incident HTTP calls go through **`lib/incidents.ts`**. Components must not call `fetch` directly.

## Testing

From the monorepo root:

```bash
npm run test --workspace @brasaland/incident-manager
```

Expect **24** passed.

Vitest unit tests cover `lib/api-error.ts`, `lib/incidents.ts`, `lib/incident-status-control.ts`, `lib/validate-register-form.ts`, and related helpers.

```powershell
npm run build
```

## Architecture note

Validation and lifecycle rules live in **`packages/shared/brasaland_shared`** on the backend. This UI sends category codes and status values exactly as defined in `services/incident-manager/CONTEXT-brasaland.md`.
