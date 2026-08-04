# Brasaland Inventory API

PostgreSQL-backed inventory service for Brasaland Operations. It is the central ingredient stock layer for the Brasaland Digital platform: ingredients, supplier deliveries (entries), and consumption or waste exits (exits). Stock is always computed from order history — never stored on the ingredient row.

Authentication for write endpoints uses JWT verification via **`brasaland-auth-verify`** (same RS256 public key as `services/auth`). User identity is not stored in Supabase; `user_uuid` on entries and exits is the stringified TinyDB user id from the token.

For entity names, field definitions, and seed fixtures, see **`CONTEXT-brasaland.md`**.

## Architecture

```
services/inventory/
├── app.py                 # FastAPI app + lifespan (create_all)
├── database.py            # SQLModel engine, get_db, SQLite FK pragma
├── models.py              # Ingredient, IngredientEntry, IngredientExit
├── schemas.py             # Pydantic request/response schemas
├── dependencies.py        # JWT → user_uuid (brasaland_auth_verify)
├── routers/
│   └── inventory.py       # APIRouter(prefix="/inventory")
├── seed.py                # CLI: load CONTEXT seed rows into Supabase
├── tests/                 # pytest (SQLite in-memory)
├── CONTEXT-brasaland.md   # Data contract (authoritative)
├── pyproject.toml         # Declared deps (locked in uv.lock)
└── README.md
```

**Dual database:** `services/auth` remains on TinyDB for users and tokens. This service uses **Supabase PostgreSQL** (via `DATABASE_URL`) for inventory tables only.

## Concurrency

Outbound stock checks (`POST /inventory/orders/outbound`) serialize on an **`Ingredient` row lock** (`SELECT … FOR UPDATE`) in the same session before the computed stock guard and exit insert. That closes the TOCTOU window between availability read and exit write under PostgreSQL.

SQLite test runs do **not** exercise real row locking (`with_for_update()` is a no-op on SQLite). Lock behavior is verified against live Postgres (brasaland-m5).

## Setup

Run every command from **`services/inventory/`**.

### Environment

Copy `.env.example` to `.env` and set:

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Supabase PostgreSQL connection string (pooler port 6543 recommended) |
| `JWT_PUBLIC_KEY` | RS256 public key PEM (must match `services/auth`) |
| `JWT_ALGORITHM` | `RS256` |

```powershell
cd services/inventory
uv sync --python 3.13
uv run uvicorn app:app --port 8012
```

Open **http://127.0.0.1:8012/docs**

Requires **Python 3.11+**. Dependencies are declared in `pyproject.toml`, locked in `uv.lock`, and managed with [uv](https://docs.astral.sh/uv/).

## Seed

Load the CONTEXT demo dataset into your Supabase database:

```powershell
uv run python seed.py
```

**Idempotency:**

- **Ingredients** — skip if `sku` already exists.
- **Entries / exits** — skip if an identical row already exists (same ingredient, quantity, supplier or reason, and `location_id`).

Re-running after a successful seed prints zero inserts and full skips.

**`user_uuid`:** seed rows use placeholder `"1"`. In production these should correspond to real user ids from the TinyDB auth service.

Expected first-run totals: **6** ingredients, **4** entries, **3** exits.

## Business rules

- **`current_stock`** is computed as `SUM(IngredientEntry.quantity) − SUM(IngredientExit.quantity)` per ingredient. It appears on product responses only — not in the database.
- **`unit_cost` (optional, inbound only)** — `POST /inventory/orders/inbound` accepts an optional non-negative `unit_cost` on `IngredientEntry`. Omitted or null is valid (historical rows). `IngredientExit` has no cost field; waste monetary valuation is deferred to the M6 pipeline, which values waste at the ingredient's latest supply `unit_cost`.
- **Float convention for `unit_cost`:** floats are not exact for monetary values; this field follows the service's existing float convention, while the M6 pipeline's destination table uses NUMERIC per the pipeline CONTEXT and aggregation happens in pandas — precision is enforced at the reporting destination, convention preserved at the source.
- **Live column rollout** — `SQLModel.metadata.create_all` does not add columns to existing tables. On brasaland-m5, operators add `ingrediententry.unit_cost` with `scripts/add_inventory_cost_column.py` (dry-run first) **after merge and before** restarting/deploying inventory with the new model.
- **Negative stock guard** — outbound orders that would drop stock below zero return **HTTP 400** with: `Insufficient stock for ingredient '{name}'. Available: {available}, requested: {requested}.`
- **`reason`** on outbound orders must be exactly `"consumption"` or `"waste"` (otherwise **HTTP 422**).
- **Locations** are numeric ids `1`–`14`; not foreign keys in this milestone.

## API endpoints

All routes are under `/inventory`.

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| `GET` | `/inventory/products` | No | List all ingredients with `current_stock` |
| `POST` | `/inventory/products` | Bearer | Create a new ingredient (`current_stock` starts at 0) |
| `GET` | `/inventory/products/{id}` | No | Get one ingredient with `current_stock` |
| `POST` | `/inventory/orders/inbound` | Bearer | Log a supplier delivery (`IngredientEntry`; optional `unit_cost`) |
| `POST` | `/inventory/orders/outbound` | Bearer | Log consumption or waste (`IngredientExit`) |
| `GET` | `/inventory/orders` | No | List all entries and exits with nested ingredient data |

Write endpoints require a valid **access** JWT (no `type` claim). Refresh and password-reset tokens are rejected with **401**.

## Testing

```powershell
cd services/inventory
uv run pytest
```

Expect **33** passed (SQLite in-memory; no Supabase required for tests).

CI runs this suite via the `uv-tests` matrix row `services/inventory` in `.github/workflows/ci.yml`.
