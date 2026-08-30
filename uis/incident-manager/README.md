# Brasaland Incident Manager UI

> **Deprecated and unsupported.** This standalone Next.js UI is retained as legacy source only, is not part of the supported demo, and is not an operational Brasaland surface.

The **`services/incident-manager`** API now requires a valid Bearer JWT on every incident route. This deprecated UI intentionally has no login or token integration and sends no `Authorization` header, so its API requests receive **HTTP 401**.

## Historical local setup

The commands below can still start the legacy UI, but its incident operations are unsupported and cannot call the protected API.

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

## Legacy routes

| Path | Historical purpose |
| --- | --- |
| `/` | Landing with links to the three views |
| `/register` | Incident registration form (branch highlight when `origin` is `branch`) |
| `/incidents` | Filterable list with inline status updates (valid transitions only; revert on failure) |
| `/summary` | Aggregated metrics by status, category, origin, and branch |

There is no supported end-to-end manual flow for these routes. Requests made without a Bearer JWT are expected to return **HTTP 401**.

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

## Legacy architecture note

Validation and lifecycle rules live in **`packages/shared/brasaland_shared`** on the backend. This UI sends category codes and status values exactly as defined in `services/incident-manager/CONTEXT-brasaland.md`.
