# Brasaland Backoffice

Internal operations dashboard for Brasaland. The app has two data modes:

- **Dashboard** (`/`) and **Locations** (`/locations`) — M2 fixture data from `@brasaland/operations-toolkit` (no API calls).
- **Inventory** (`/inventory/*`) — live ingredient data from `services/inventory` via Next.js rewrites (no backend CORS changes).

## Setup

Run commands from **`uis/backoffice/`**.

### Environment

Copy `.env.example` to `.env.local`:

```powershell
cd uis/backoffice
copy .env.example .env.local
```

| Variable | Purpose |
| --- | --- |
| `NEXT_PUBLIC_INVENTORY_API_URL` | Same-origin proxy base → `http://localhost:3003/api/inventory` |
| `NEXT_PUBLIC_AUTH_API_URL` | Same-origin proxy base → `http://localhost:3003/api/auth` |

Rewrites in `next.config.ts` forward `/api/inventory/*` to inventory **:8012** and `/api/auth/*` to auth **:8002**.

### Dev server

```powershell
npm run dev
```

Open **http://127.0.0.1:3003**

Port **3003** (`next dev -p 3003`).

## Routes

| Path | Auth | Description |
| --- | --- | --- |
| `/` | No | Operations dashboard (M2 fixtures) |
| `/locations` | No | Locations table (M2 fixtures) |
| `/login` | No | Sign in (JWT stored in `localStorage`) |
| `/inventory/products` | Yes | Ingredient list with `current_stock` |
| `/inventory/orders/inbound` | Yes | Log IngredientEntry (supplier delivery) |
| `/inventory/orders/outbound` | Yes | Log IngredientExit (consumption or waste) |
| `/inventory/orders` | Yes | Read-only order history |

## Manual test flow

1. Start auth: `cd services/auth && uv run uvicorn app:app --port 8002`
2. Start inventory: `cd services/inventory && uv run uvicorn app:app --port 8012`
3. Seed inventory (once): `cd services/inventory && uv run python seed.py`
4. Register or use an existing user on auth (port 8002 `/docs` if needed)
5. `cd uis/backoffice && npm run dev`
6. Open `/login` → sign in → redirected to `/inventory/products`
7. Verify seeded ingredients and `current_stock`
8. Log an **inbound** order from `/inventory/orders/inbound`
9. Log an **outbound** order from `/inventory/orders/outbound` (try exceeding stock to see API error message)
10. Open `/inventory/orders` — merged history with Inbound/Outbound badges

## API client

All inventory HTTP calls go through **`lib/inventory.ts`**. Auth token helpers live in **`lib/auth.ts`**. Components must not call `fetch` directly.

## Testing

```powershell
npm run test
```

Vitest unit tests cover `lib/api-error.ts`, `lib/inventory.ts`, and `lib/stock-level.ts`.

```powershell
npm run build
```

## Architecture note

Browser requests hit the Next.js dev server on port 3003, which rewrites to the Python services. This avoids adding CORS middleware to `services/inventory` or `services/auth`.
