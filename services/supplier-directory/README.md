# Brasaland Supplier Directory

An internal Brasaland Operations utility for managing approved suppliers across Colombia and Florida locations. The same business rules run in three places from one shared core: a **seed CLI** (`seed.py`), a **FastAPI backend** (`app.py`), and a **web frontend** (`static/`). Validation, persistence, and supplier lifecycle logic live once in the `supplier_directory/` package and are reused by every entry point—never duplicated in the API, CLI, or UI.

## Architecture

The project follows a single-core, multi-consumer design. `supplier_directory/` owns validation, TinyDB persistence, and supplier CRUD. `app.py` and `seed.py` are thin wrappers that call the core; the frontend calls the REST API, which calls the same core.

**Design principle:** one core, three consumers, zero logic duplication.

```
services/supplier-directory/
├── supplier_directory/          # Shared core
│   ├── constants.py             # Countries, currencies, categories, statuses
│   ├── types.py                 # SupplierRecord, SupplierInput, validation errors
│   ├── validator.py             # Business-rule validation (all failures collected)
│   ├── db.py                    # Lazy TinyDB singleton (see Ops notes)
│   ├── repository.py            # CRUD + id assignment
│   ├── service.py               # Create, list, rate/status updates, seed batch
│   └── seed_data.py             # Canonical 15-record seed fixture
├── app.py                       # FastAPI app + static file serving
├── seed.py                      # CLI seed entry point
├── static/                      # Single-page web UI (HTML, CSS, JS)
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── tests/                       # pytest suite (validator + golden seed + API)
├── data/                        # Runtime TinyDB (gitignored except .gitkeep)
├── CONTEXT-brasaland.md         # Product spec and business context (authoritative)
├── requirements.txt
└── README.md
```

For field definitions, category codes, and operational context, see **`CONTEXT-brasaland.md`**. For the exact seed records, see **`supplier_directory/seed_data.py`**.

## Setup (Windows + venv)

```powershell
cd services/supplier-directory
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Requires **Python 3.11+**.

## Seed the database

```powershell
python seed.py
```

Expected output on a fresh database:

```text
Seeded 15 suppliers (0 skipped).
```

Re-running is idempotent: existing name+country pairs are skipped.

## Web app usage

Start the server:

```powershell
python -m uvicorn app:app --port 8001
```

Open **http://127.0.0.1:8001/** — filter suppliers, register new ones, update rates, and change status without leaving the page.

## API endpoints

| Method | Path | Success | Error responses | Description |
| --- | --- | --- | --- | --- |
| `POST` | `/suppliers` | `201` + supplier JSON | `422` validation failures | Register a supplier |
| `GET` | `/suppliers` | `200` + list | `422` if `category` query is invalid | List suppliers; optional `country` and `category` filters |
| `GET` | `/suppliers/{id}` | `200` + supplier JSON | `404` | Get one supplier by id |
| `PATCH` | `/suppliers/{id}/rate` | `200` + updated supplier | `404`, `422` | Update `rate_per_unit` (must be > 0) |
| `PATCH` | `/suppliers/{id}/status` | `200` + updated supplier | `404`, `422` | Set `active` or `suspended` |
| `DELETE` | `/suppliers/{id}` | `204` empty body | `404` | Remove a supplier (prefer suspension for ops) |

Static assets are served at `/static/`; `GET /` returns the web UI.

## Business rules

Validation runs in the core before any write. **All** failed rules are returned together (422), not just the first failure.

| Rule | Behavior |
| --- | --- |
| **Currency ↔ country** | Colombia → COP, USA → USD; mismatch returns 422 before write |
| **Categories** | At least one required; duplicates are silently deduped in the service layer on create/seed |
| **Rate** | `rate_per_unit` must be a number > 0 |
| **Name** | Required (non-empty after trim) |
| **Status** | `active` or `suspended` only |
| **Suspension vs delete** | Prefer setting status to `suspended`; DELETE exists but suspension is the normal ops path |

Invalid category values in `GET /suppliers?category=…` return **422** before querying the database.

## Verification

From `services/supplier-directory/` with the venv active:

```powershell
pytest
```

**40 tests** cover validator rules, API endpoints, and golden seed behavior. The golden seed tests load `seed_data.py` and assert:

- **15** suppliers inserted on first run (**0** skipped)
- Idempotent re-seed: **0** inserted, **15** skipped
- Country split: **9** Colombia, **6** USA
- Spot checks on named suppliers (rates, categories, status)

## Ops notes

- **Single worker:** The TinyDB handle is a per-process singleton (`db.py`). Use one uvicorn worker in production unless every worker shares the same JSON path.
- **`SUPPLIER_DB_PATH`:** Environment override for the JSON file path—**tests and local tooling only**. Leave unset in production shells; default is `data/suppliers.json` (gitignored at runtime).
- **Data directory:** `data/*` is gitignored; only `data/.gitkeep` is tracked.
