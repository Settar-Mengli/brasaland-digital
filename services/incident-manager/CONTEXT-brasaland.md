# CONTEXT — Centralized Incident Manager — Brasaland

> **Repository path:** `services/incident-manager/CONTEXT-brasaland.md`

---

## Your company

You are part of the **Brasaland Digital** team, the internal technology unit of Brasaland, a grilled-food restaurant chain with **14 locations** in Colombia and Florida.

Operations tracks every incident across the chain — equipment failures, supply problems, customer complaints, food quality issues, and staff-related events. Until now, location managers logged incidents in a shared spreadsheet. That export is the seed CSV for this service. The **Centralized Incident Manager** is the single source of truth that will replace the spreadsheet workflow.

---

## English rule

All UI, code comments, API messages, and documentation are in **English**.

Category **codes** (`QUEJA_CLIENTE`, etc.) are fixed identifiers — they are stored and validated as-is and are **not** translated as data. English **display labels** (Customer Complaint, Equipment, …) exist only in the web UI.

---

## Categories (5 fixed codes)

Same codes as **`services/incident-analysis/CONTEXT-brasaland.md`**. Cross-reference that document for operational definitions.

| Code | Meaning |
| --- | --- |
| `QUEJA_CLIENTE` | Customer complaint (service, wait time, treatment) |
| `EQUIPAMIENTO` | Equipment failure or breakdown |
| `ABASTECIMIENTO` | Supply or stock shortage |
| `CALIDAD_ALIMENTO` | Food quality issue |
| `PERSONAL` | Staff-related incident |

Stored in the database and API as the code string. Never localized at rest.

---

## Branches

| Pattern | Values |
| --- | --- |
| Colombia | `COL-01` … `COL-10` |
| Florida | `FLA-01` … `FLA-04` |
| HQ | `Central` |

`Central` is valid for incidents with `origin: internal` (not present in the historical CSV `location_id` column).

---

## Statuses

| Status | Meaning |
| --- | --- |
| `open` | New or awaiting action |
| `in_progress` | Actively being handled |
| `resolved` | Closed successfully |
| `discarded` | Closed without resolution / not actionable |

### Lifecycle

```
open ──────────► in_progress ──────────► resolved  (terminal)
 │                      │                      │
 │                      └──────────► discarded  (terminal)
 └──────────────────────────────────► discarded  (terminal)
```

Illegal transitions return **HTTP 400** from the API (see `packages/shared/brasaland_shared/lifecycle.py`).

---

## Origins

| Value | Meaning |
| --- | --- |
| `customer` | Reported by or on behalf of a customer |
| `branch` | Reported by branch staff |
| `internal` | Reported by HQ / internal operations |

---

## Seed CSV mapping

**Source file (default):** `services/incident-analysis/incidents-brasaland.csv`  
**Encoding:** UTF-8, comma-separated, header row present.

The CSV is **read-only** — never edited by this service. Spanish `description` values are translated to English **at seed-time** in `incident_manager/translations.py`.

| CSV column | Incident field | Notes |
| --- | --- | --- |
| `incident_id` | `source_incident_id` | e.g. `BRS-000001` |
| `date` | `created_at`, `updated_at` | Parsed as `YYYY-MM-DD`, stored as UTC midnight ISO 8601 |
| `location_id` | `branch` | Must be a valid branch code |
| `category` | `category` | One of five fixed codes |
| `description` | `description` | Translated Spanish → English; empty fails validation |
| `status` | `status` | See status mapping below |
| _(synthesized)_ | `title` | `"{incident_id}: {english_description[:60]}"` |
| _(fixed)_ | `origin` | Always `customer` for seeded rows |

Columns not mapped (`customer_id`, `satisfaction_score`, `reporter_id`, etc.) are ignored by the incident manager seed (validation rules differ from incident-analysis).

### CSV status → incident status

| CSV `status` | Incident `status` |
| --- | --- |
| `ABIERTO` | `open` |
| `CERRADO` | `resolved` |
| `DESCARTADO` | `discarded` |

### Assumption: `CERRADO` → `resolved`

The historical spreadsheet uses `CERRADO` for all closed incidents. The source data **does not distinguish** between “resolved successfully” and “discarded / not actionable” closure — only `ABIERTO`, `CERRADO`, and `DESCARTADO` exist in the export.

**This service maps every `CERRADO` row to `resolved`.** Rows explicitly marked `DESCARTADO` in the CSV map to `discarded`. If finer-grained closure semantics are needed later, the CSV schema or a new column would be required; until then, `resolved` is the canonical meaning of `CERRADO` here.

### Golden seed outcome (100-row fixture)

| Result | Count |
| --- | --- |
| Inserted | 97 |
| Rejected | 3 |

| `source_incident_id` | Rejection reason |
| --- | --- |
| `BRS-000044` | invalid / missing branch |
| `BRS-000049` | invalid / missing category |
| `BRS-000079` | empty description |

Re-running the seed after a successful load inserts **0** additional rows (idempotent on `source_incident_id`).

---

## Incident record (runtime)

After seed or API create, each stored incident includes:

`id`, `source_incident_id`, `title`, `description`, `category`, `status`, `origin`, `branch`, `created_at`, `updated_at`

Required on create: `title`, `description`, `category`, `origin`, `branch` (`status` defaults to `open` via API).

Validation: `packages/shared/brasaland_shared/incident_validator.py` (accumulate-all-errors).
