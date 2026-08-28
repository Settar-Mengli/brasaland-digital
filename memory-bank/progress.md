# Brasaland Digital — M4 Progress

**Convention:** Verification, Delivered, Scope, and Status blocks under completed sections are point-in-time records of the session that produced them. They are never retro-edited. Current repository state lives in `README.md` and `docs/standards/project-context.md`.

## Session Continuity
If a session ends unexpectedly, read this file first. It contains the last known state, files changed, commands run, blockers, and the exact next step.

## Current Branch
main

## M4 Phase Status
| Phase | Description | Status |
|---|---|---|
| A | Branch + agent infrastructure | Complete |
| B | uis/website scaffolding + M1 migration | Complete |
| C | uis/backoffice scaffolding + M2 integration | Complete |
| D | Final verification + PR prep | Complete |

## Phase A Checklist
- [x] milestone-4 branch created
- [x] package.json workspaces updated to include uis/*
- [x] memory-bank/projectbrief.md created
- [x] memory-bank/techContext.md created
- [x] memory-bank/progress.md created (this file)
- [x] AGENTS.md created at root
- [x] .agents/rules/ created with at least one rule
- [x] .agents/skills/ created with at least one skill

## Phase B Checklist
- [x] uis/website/package.json created
- [x] uis/website config files created (tsconfig, next.config, postcss, eslint, .gitignore)
- [x] uis/website/vercel.json created with security headers
- [x] uis/website/CLAUDE.md and AGENTS.md created
- [x] uis/website/app/globals.css created (brand tokens)
- [x] uis/website/app/layout.tsx created (M1 metadata + Schema.org)
- [x] uis/website/app/page.tsx and all _components/ created
- [x] uis/website/app/brasa-points/ page and form created
- [x] uis/website/public/favicon.svg created
- [x] npx prettier --check uis/website/ passes
- [x] npm install run at repo root (2264f97)
- [x] npm run build --workspace @brasaland/website passes (Compiled successfully, / and /brasa-points static)
- [x] Live URL confirmed: https://brasaland-website.vercel.app

## Phase C Checklist
- [x] uis/backoffice/package.json created
- [x] uis/backoffice config files created (tsconfig, next.config, postcss, eslint, .gitignore)
- [x] uis/backoffice/vercel.json created
- [x] uis/backoffice/CLAUDE.md and AGENTS.md created
- [x] uis/backoffice/app/globals.css created
- [x] uis/backoffice/app/layout.tsx and page.tsx created (M2 dashboard)
- [x] npx prettier --check uis/backoffice/ passes
- [x] npm install run at repo root (2264f97)
- [x] npm run build --workspace @brasaland/backoffice passes (Compiled successfully, / static)
- [x] npm run test --workspace @brasaland/operations-toolkit shows 115 passing
- [x] Live URL confirmed: https://brasaland-backoffice.vercel.app

## Phase D Checklist
- [x] npm install run at repo root — 2 packages added, all 5 workspace symlinks created (2264f97)
- [x] npm run build --workspace @brasaland/website passes
- [x] npm run build --workspace @brasaland/backoffice passes
- [x] npm run test --workspace @brasaland/operations-toolkit — 115 passed (0 failing)
- [x] Header sticky background bug fixed (f48fcc6)
- [x] Backoffice locations page created (26cfed6)
- [x] Backoffice nav links added (26cfed6)
- [x] /brasa-points page: Header and Footer added (af1c35f)
- [x] Dashboard: "View all locations" CTA added (af1c35f)
- [x] projectbrief.md: company description corrected (af1c35f)
- [x] Skip link target fixed to #main-content (this commit)
- [x] README: removed non-existent brand-tokens.md from diagram (this commit)
- [x] npm run dev --workspace @brasaland/website — verify all 7 sections, form, mobile nav
- [x] npm run dev --workspace @brasaland/backoffice — verify all 4 dashboard sections with M2 data
- [x] Screenshots taken and committed to docs/screenshots/
- [x] README.md updated — structure diagram, workspace table, tech stack, status rows, M4 live demo section (6779512)
- [x] Deploy uis/website to Vercel → https://brasaland-website.vercel.app
- [x] Deploy uis/backoffice to Vercel → https://brasaland-backoffice.vercel.app
- [x] Fill live URLs in README.md
- [x] memory-bank/progress.md final update + commit: docs(memory-bank): Phase D complete
- [x] Open PR → https://github.com/Settar-Mengli/brasaland-digital/pull/1
- [x] Merge PR into main

## Last Completed Step
DEV-55 complete — async reporting pipeline (Celery + Redis + DLQ), PR #40 merged at 1a99035.

## Files Changed This Session
| File | Action | Commit |
|---|---|---|
| package.json | Modified — added uis/* to workspaces | d2df392 |
| AGENTS.md | Created | d2df392 |
| memory-bank/projectbrief.md | Created | d2df392 |
| memory-bank/techContext.md | Created | d2df392 |
| memory-bank/progress.md | Created | d2df392 |
| .agents/rules/typescript-conventions.md | Created | d2df392 |
| .agents/skills/prettier-check/SKILL.md | Created | d2df392 |
| memory-bank/progress.md | Updated — Phase A marked complete | 096640c |
| memory-bank/techContext.md | Updated — ports set, no duplicate | 096640c |
| apps/operations-toolkit/src/index.ts | Added fixture re-export | 096640c |
| uis/website/ (24 files) | Created — Next.js rebuild of M1 | 2ac0644 |
| memory-bank/progress.md | Updated — Phase B marked complete | a073f6c |
| uis/backoffice/ (13 files) | Created — M2 operations dashboard | 9ce684f |
| memory-bank/progress.md | Updated — Phase C marked complete | 76596fa |
| package-lock.json | Updated — npm install for uis/* workspaces | 2264f97 |
| README.md | Updated — M4 workspaces, structure, status table | 6779512 |
| .prettierignore | Modified — added next-env.d.ts | fbfaf7d |
| uis/website/app/_components/Header.tsx | Modified — removed opacity/blur | f48fcc6 |
| uis/backoffice/app/layout.tsx | Modified — added nav links | 26cfed6 |
| uis/backoffice/app/locations/page.tsx | Created — locations page | 26cfed6 |
| uis/website/app/brasa-points/page.tsx | Modified — added Header/Footer | af1c35f |
| uis/backoffice/app/page.tsx | Modified — added locations CTA | af1c35f |
| memory-bank/projectbrief.md | Modified — fixed company description | af1c35f |
| README.md | Modified — live URLs filled | (this commit) |
| memory-bank/progress.md | Modified — Phase D complete | (this commit) |

## Commands Run This Session
- git checkout -b milestone-4
- git add (Phase A files)
- git commit (d2df392)
- npx prettier --write uis/website/
- git add uis/website/
- git commit (2ac0644)
- npx prettier --write uis/backoffice/
- git add uis/backoffice/
- git commit (9ce684f)
- npm install
- git add package-lock.json && git commit (2264f97)
- npm run build --workspace @brasaland/website — PASS
- npm run build --workspace @brasaland/backoffice — PASS
- npm run test --workspace @brasaland/operations-toolkit — 115 passed
- git add README.md && git commit (6779512)

## Blockers
None.

## Next Step
All merged into main. PR #1, #2, #3 complete. Next: feature/auth (JWT authentication + route protection) off main.

## Backend Architecture Proposal — Progress

### Status
Complete

### Files Changed
| File | Action |
|---|---|
| docs/ARCHITECTURE_PROPOSAL.md | Created |
| memory-bank/PLANNING.md | Created |
| memory-bank/progress.md | Modified |

### Summary
Created the backend architecture proposal document and recorded the planning and progress updates for this assignment.

## Incident Analysis — Progress

**Status:** Complete (merged into milestone-4 → main).

**Scope:** Brasaland incident file analyzer — one shared Python core (CSV validation + metrics) reused by an `analyze.py` CLI, a FastAPI backend, and a served static frontend. Golden fixture: 96 valid / 4 invalid / 3.46 avg.

**Verification:** `pytest` in `services/incident-analysis/` → 18 passed.

## Supplier Directory — Progress

**Status:** Complete (merged into milestone-4 → main).

**Scope:** Brasaland supplier directory — FastAPI + TinyDB + Pydantic core, served static frontend, seed CLI.

**Files touched (high level):**

| Area | Files |
| --- | --- |
| Core | `supplier_directory/` (constants, types, validator, db, repository, service, seed_data) |
| Entry points | `app.py`, `seed.py` |
| Frontend | `static/index.html`, `static/app.js`, `static/styles.css` |
| Tests | `tests/test_validator.py`, `tests/test_golden_seed.py`, `tests/test_api.py`, `tests/conftest.py` |
| Docs | `README.md`, `CONTEXT-brasaland.md` (spec — authoritative) |

**Verification:** `pytest` in `services/supplier-directory/` → 40 passed.

## Building Bullet-Proof Applications (Auth Testing) — Progress

**Status:** Complete (merged into main via PR #8).

**Scope:** Added a pytest suite and `TESTING.md` to `services/auth/` and migrated the service from pip → uv. No auth business logic changed; tests assert behavior as implemented.

**Files touched (high level):**

| Area | Files |
| --- | --- |
| Tooling | `pyproject.toml`, `uv.lock`, `requirements.txt` (exported via `uv export`) |
| Tests | `tests/` (security, db, repository, user service, reset service, email sender, API, reset API) |
| Docs | `TESTING.md` |

**Verification:** `uv run pytest` in `services/auth/` → 64 passed; 100% coverage on the `auth/` package (`fail_under = 70`).

## Auth RS256 Migration — Progress

**Status:** Complete (branch `feature/auth-rs256`).

**Scope:** Migrated JWT signing in `services/auth/` from HS256 (symmetric secret) to RS256 (RSA private/public keypair). Changes limited to `auth/security.py`, test fixtures, and configuration docs. Public function signatures (`create_access_token`, `decode_access_token`) and token claim shape unchanged; `app.py` and `service.py` untouched.

**Files touched (high level):**

| Area | Files |
| --- | --- |
| Core | `auth/security.py` |
| Tests | `tests/conftest.py`, `tests/test_security.py` |
| Config / docs | `.env.example`, `README.md`, `TESTING.md` |

**Verification:** `uv run pytest` in `services/auth/` → 64 passed; coverage gate met.

## Auth verify-only package — Progress

**Status:** Complete (branch `feature/auth-verify-package`).

**Scope:** Extracted a verify-only RS256 JWT helper into `packages/auth-verify/` (`brasaland_auth_verify.verify_token`). `services/auth/auth/security.py` delegates `decode_access_token` to the package; signing and password hashing remain in auth. No route, field, or error-format changes.

**Files touched (high level):**

| Area | Files |
| --- | --- |
| Package | `packages/auth-verify/` (pyproject.toml, `brasaland_auth_verify/`, tests) |
| Auth wiring | `services/auth/pyproject.toml`, `uv.lock`, `requirements.txt`, `auth/security.py` |
| Docs | `packages/auth-verify/README.md`, `services/auth/README.md`, root `README.md` |

**Verification:** `uv run pytest` in `packages/auth-verify/` → 5 passed; `uv run pytest` in `services/auth/` → 64 passed.

## Auth app.py thinning — Progress

**Status:** Complete (branch `feature/auth-app-thinning`).

**Scope:** Moved business/auth logic out of `services/auth/app.py` into `auth/service.py`: `issue_access_token`, `can_modify_user`, `build_update_fields`, and `resolve_active_user`. Removed duplicated `_user_id_from_token` from app.py; `get_current_user` is now a thin HTTP wrapper. No route, status code, error string, or response-model changes.

**Files touched (high level):**

| Area | Files |
| --- | --- |
| Routes | `services/auth/app.py` |
| Service | `services/auth/auth/service.py` |
| Docs | `memory-bank/progress.md` |

**Verification:** `uv run pytest` in `services/auth/` → 64 passed; coverage gate met.

## Python test CI — Progress

**Status:** Complete (branch `feature/ci`).

**Scope:** Added GitHub Actions workflow `.github/workflows/ci.yml` to run all Python test suites on push and pull request to `main`. Single job: `uv-tests` (matrix: services/auth, packages/auth-verify, packages/shared, services/supplier-directory, services/incident-analysis, services/incident-manager). Each suite runs in its own working directory; Python 3.13.

**Files touched (high level):**

| Area | Files |
| --- | --- |
| CI | `.github/workflows/ci.yml` |
| Docs | `README.md` (CI badge), `memory-bank/progress.md` |

**Verification:** Workflow runs six isolated pytest suites; auth enforces `fail_under = 70` via existing pyproject config.

## Auth refresh-token sessions — Progress

**Status:** Complete (branch `feature/auth-refresh-tokens`).

**Scope:** Added stateful, rotating refresh-token sessions to `services/auth/`. Login and register return access + refresh tokens; **POST /auth/refresh** exchanges a refresh token for a rotated pair; **POST /auth/logout** revokes a refresh token. Refresh tokens stored hashed in TinyDB `refresh_tokens` table; access tokens remain short-lived and stateless.

**Files touched (high level):**

| Area | Files |
| --- | --- |
| Storage | `auth/refresh_repository.py` |
| Service | `auth/service.py`, `auth/types.py` |
| Routes | `services/auth/app.py` |
| Tests | `tests/test_refresh_service.py`, `tests/test_api.py` |
| Docs | `services/auth/README.md`, `.env.example` |

**Verification:** `uv run pytest` in `services/auth/` → 82 passed; coverage gate met.

## Auth security fixes — Progress

**Status:** Complete (branch `feature/auth-security-fixes`).

**Scope:** Two behavior tightenings in `services/auth/` with no public contract change (routes, response shapes, status codes unchanged).

| Fix | Change |
| --- | --- |
| H1 | `resolve_active_user` rejects any JWT with a `type` claim — password-reset and refresh tokens can no longer authenticate at `/auth/me` or `/users/*` |
| H4 | `reset_password` calls `revoke_all_for_user` after a successful password change — existing refresh sessions are invalidated |

**Files touched (high level):**

| Area | Files |
| --- | --- |
| Service | `auth/service.py` |
| Tests | `tests/test_api.py`, `tests/test_refresh_service.py` |
| Docs | `services/auth/README.md`, `memory-bank/progress.md` |

**Verification:** `uv run pytest` in `services/auth/` → 84 passed; coverage gate met.

## Auth security fixes — Progress

**Status:** Complete (branch `feature/auth-security-fixes`).

**Scope:** Two behavior tightenings in `services/auth/` with no public contract change (routes, response shapes, status codes unchanged).

| Fix | Change |
| --- | --- |
| H1 | `resolve_active_user` rejects any JWT with a `type` claim — password-reset and refresh tokens can no longer authenticate at `/auth/me` or `/users/*` |
| H4 | `reset_password` calls `revoke_all_for_user` after a successful password change — existing refresh sessions are invalidated |

**Files touched (high level):**

| Area | Files |
| --- | --- |
| Service | `auth/service.py` |
| Tests | `tests/test_api.py`, `tests/test_refresh_service.py` |
| Docs | `services/auth/README.md`, `memory-bank/progress.md` |

**Verification:** `uv run pytest` in `services/auth/` → 84 passed; coverage gate met.

## packages/shared uv migration — Progress

**Status:** Complete (staged, not committed).

**Scope:** Migrated `packages/shared` from pip/setuptools-only to uv, matching `packages/auth-verify`. No changes to `[build-system]` or `[tool.setuptools.packages.find]`. `services/incident-manager` unchanged — still installs via `-e ../../packages/shared`.

**Files touched:**

| Area | Files |
| --- | --- |
| Tooling | `packages/shared/pyproject.toml`, `packages/shared/uv.lock`, `packages/shared/requirements.txt` |
| Docs | `packages/shared/README.md`, `memory-bank/progress.md` |
| CI | `.github/workflows/ci.yml` (`packages/shared` moved from `pip-tests` to `uv-tests`) |

**Verification:** `uv run pytest` in `packages/shared/` → 33 passed.

## supplier-directory uv migration — Progress

**Status:** Complete (staged, not committed).

**Scope:** Migrated `services/supplier-directory` from pip/requirements.txt-only to uv (`[tool.uv] package = false`). `tests/conftest.py` and `seed.py` unchanged.

**Files touched:**

| Area | Files |
| --- | --- |
| Tooling | `services/supplier-directory/pyproject.toml`, `services/supplier-directory/uv.lock`, `services/supplier-directory/requirements.txt` |
| Docs | `services/supplier-directory/README.md`, `memory-bank/progress.md` |
| CI | `.github/workflows/ci.yml` (`services/supplier-directory` moved from `pip-tests` to `uv-tests`) |

**Verification:** `uv run pytest` in `services/supplier-directory/` → 40 passed.

## incident-analysis uv migration — Progress

**Status:** Complete (staged, not committed).

**Scope:** Migrated `services/incident-analysis` from pip/requirements.txt-only to uv (`[tool.uv] package = false`). No `tests/conftest.py` — `[tool.pytest.ini_options] pythonpath = ["."]` resolves imports under `uv run pytest`.

**Files touched:**

| Area | Files |
| --- | --- |
| Tooling | `services/incident-analysis/pyproject.toml`, `services/incident-analysis/uv.lock`, `services/incident-analysis/requirements.txt` |
| Docs | `services/incident-analysis/README.md`, `memory-bank/progress.md` |
| CI | `.github/workflows/ci.yml` (`services/incident-analysis` moved from `pip-tests` to `uv-tests`) |

**Verification:** `uv run pytest` in `services/incident-analysis/` → 18 passed.

## incident-manager uv migration — Progress

**Status:** Complete (staged, not committed).

**Scope:** Final service in the Python uv migration. Migrated `services/incident-manager` from pip/requirements.txt to uv with `brasaland-shared` via `[tool.uv.sources]`. `tests/conftest.py` and `scripts/seed_incidents.py` unchanged (sys.path hacks retained). `pip-tests` CI job removed (matrix was empty).

**Files touched:**

| Area | Files |
| --- | --- |
| Tooling | `services/incident-manager/pyproject.toml`, `services/incident-manager/uv.lock`, `services/incident-manager/requirements.txt` |
| Tests | `services/incident-manager/tests/test_scaffold.py` (error message only) |
| Docs | `services/incident-manager/README.md`, `memory-bank/progress.md` |
| CI | `.github/workflows/ci.yml` (`pip-tests` job removed; `services/incident-manager` added to `uv-tests`) |

**Verification:** `uv run pytest` in `services/incident-manager/` → 23 passed.

## M5 Inventory API — Progress

**Status:** Complete (branch `feat/m5-inventory-backend`, staged, not committed).

**Scope:** New `services/inventory/` — dual-database inventory layer. TinyDB auth (`services/auth`) unchanged; ingredient data in Supabase PostgreSQL via SQLModel. Six endpoints under `/inventory`. `current_stock` computed from entry/exit aggregates (not stored). Write routes authenticated via `brasaland-auth-verify` (`user_uuid` = stringified JWT `user_id`). Negative-stock outbound guard returns HTTP 400 with CONTEXT message.

**Files touched (high level):**

| Area | Files |
| --- | --- |
| Service | `app.py`, `database.py`, `models.py`, `schemas.py`, `dependencies.py`, `routers/inventory.py`, `seed.py` |
| Tooling | `pyproject.toml`, `uv.lock`, `requirements.txt`, `.env.example` |
| Tests | `tests/` (scaffold, database, schemas, auth, products, orders, stock) |
| Docs | `README.md`, `CONTEXT-brasaland.md` (user-authored spec) |
| CI | `.github/workflows/ci.yml` (`services/inventory` in `uv-tests` matrix) |

**Verification:** `uv run pytest` in `services/inventory/` → 27 passed.

## M5 Backoffice Inventory UI — Progress

**Status:** Complete (branch `feat/m5-backoffice-inventory`, staged, not committed).

**Scope:** Inventory management UI in `uis/backoffice/` — login + four protected views consuming `services/inventory` via `lib/inventory.ts`. JWT login against `services/auth` (`localStorage`). `InventoryAuthGuard` on inventory routes. Next.js rewrites proxy `/api/inventory` → :8012 and `/api/auth` → :8002 (no backend CORS changes). Dashboard and Locations remain M2 fixture-only and unchanged.

**Files touched (high level):**

| Area | Files |
| --- | --- |
| API layer | `lib/inventory.ts`, `lib/inventory-types.ts`, `lib/auth.ts`, `lib/api-error.ts`, `lib/stock-level.ts` |
| Pages | `app/login`, `app/inventory/products`, `app/inventory/orders/inbound`, `app/inventory/orders/outbound`, `app/inventory/orders` |
| Components | `InventoryAuthGuard`, `ProductSelect`, `NavLinks` |
| Config | `next.config.ts` (rewrites), `.env.example` |
| Tests | `lib/*.test.ts` (Vitest) |
| Docs | `README.md`, `AGENTS.md` |

**Verification:** `npm run test` in `uis/backoffice/` → 9 passed; `npm run build` includes `/inventory/orders` route.

## incident-manager SQLModel migration — Progress

**Status:** Complete (Part 1 backend migration — staged, not committed).

**Scope:** Migrated `services/incident-manager` persistence from TinyDB to SQLModel/Supabase (Path A). Repository internals swapped to SQLModel while keeping the same public function signatures; `service.py` and `app.py` unchanged. Reuses the brasaland-m5 Supabase project (`DATABASE_URL` shared with `services/inventory`). Schema created via lazy `ensure_schema()` on first DB access. `packages/shared/brasaland_shared` untouched (validation + lifecycle only). `tinydb` dependency removed.

**Files touched:**

| Area | Files |
| --- | --- |
| Persistence | `incident_manager/database.py`, `incident_manager/models.py`, `incident_manager/repository.py` (Chunk B) |
| Seed | `scripts/seed_incidents.py` (`ensure_schema` before batch) |
| Tooling | `pyproject.toml`, `uv.lock`, `requirements.txt`, `.env.example`, `.gitignore` |
| Tests | `tests/conftest.py` (SQLite in-memory), `tests/test_migration_model.py` |
| Removed | `incident_manager/db.py` (TinyDB singleton) |
| Docs | `README.md`, `memory-bank/progress.md` |

**Verification:** `uv run pytest` in `services/incident-manager/` → 24 passed. Golden seed preserved: **97 inserted**, **3 rejected** (`BRS-000044`, `BRS-000049`, `BRS-000079`); idempotent re-seed skips 97 duplicates.

## incident-manager UI — Progress

**Status:** Complete (Part 2 frontend — staged, not committed).

**Scope:** New `uis/incident-manager/` Next.js 16 app (port **3004**) replicating the static incident UI as three App Router views. Consumes `services/incident-manager` on **:8011** via Next.js rewrites (`/api/incidents/*`). No authentication (open API endpoints). `lib/incidents.ts` is the sole fetch layer; Vitest covers lib helpers.

**Views:**

| Route | Features |
| --- | --- |
| `/register` | Registration form; branch field always visible; highlight when `origin === branch`; client validation; field-level API errors |
| `/incidents` | Filters (status, origin, branch, category); loading/error+retry/empty states; inline status update with valid transitions only; revert on failure |
| `/summary` | `GET /api/incidents/summary` metrics; self-contained loading/error; zero-state message |

**Files touched (high level):**

| Area | Files |
| --- | --- |
| App | `app/layout.tsx`, `app/page.tsx`, `app/register/page.tsx`, `app/incidents/page.tsx`, `app/summary/page.tsx`, `app/_components/NavLinks.tsx`, `app/_components/FormField.tsx` |
| Lib | `lib/incidents.ts`, `lib/incident-types.ts`, `lib/api-error.ts`, `lib/validate-register-form.ts`, `lib/incident-status-control.ts`, `lib/incident-display.ts` |
| Config | `package.json`, `next.config.ts`, `.env.example`, `vitest.config.ts` |
| Docs | `README.md`, `AGENTS.md`, `memory-bank/progress.md` |

**Verification:** `npm run test` in `uis/incident-manager/` → 24 passed; `npm run build` includes `/register`, `/incidents`, `/summary`.

## Monorepo containerization (local Docker) — Progress

**Date:** 2026-07-07

**Status:** Complete (Chunk D — compose + docs + smoke test; staged, not committed).

**Scope:** Local development via `docker compose up` from repo root on named network `brasaland-dev`: five FastAPI backends (shared `services/Dockerfile`, uv 3.13, `--host 0.0.0.0`) + one UI container (three Next.js dev servers via `uis/start.sh`). Cloud Supabase via root `.env` `DATABASE_URL` (no local Postgres). Next.js rewrites use server-side origin env vars (`INVENTORY_API_ORIGIN`, `AUTH_API_ORIGIN`, `INCIDENTS_API_ORIGIN`).

**Chunks delivered:**

| Chunk | Files |
| --- | --- |
| A | `uis/backoffice/next.config.ts`, `uis/incident-manager/next.config.ts`, UI `.env.example` updates |
| B | `services/Dockerfile`, root `.dockerignore` (seed) |
| C | `uis/Dockerfile`, `uis/start.sh`, `.dockerignore` extended for UI paths |
| D | `docker-compose.yml`, `.env.example`, `README.md` Docker section, this entry |

**Locked decisions:** Repo-root build context; TinyDB named volumes for auth + supplier-directory; `RESET_LINK_BASE_URL` stays browser-reachable (`127.0.0.1:8002`); `requirements.txt` files untouched.

## brasaland-m5 RLS enablement — Progress

**Date:** 2026-07-07

**Status:** Complete.

**Scope:** Row-Level Security enabled on the four brasaland-m5 public tables (`ingredient`, `ingrediententry`, `ingredientexit`, `incident`) via `scripts/enable_rls.py`. Zero policies; no `FORCE ROW LEVEL SECURITY`.

**Files touched (high level):**

| Area | Files |
| --- | --- |
| Ops script | `scripts/enable_rls.py` |
| Docs | `README.md`, `memory-bank/progress.md` |

**Verification:** Script before/after output (4× DISABLED → 4× ENABLED). MCP read-only re-check (RLS true ×4, zero policies, counts 6/4/3/97). Live smoke GETs on both services returning real rows. `uv run pytest` in `services/inventory/` → 27 passed; `services/incident-manager/` → 24 passed.

## Telemetry Phase 1 — Progress

**Status:** Complete. **Scope:** `docs/telemetry/telemetry-plan.md` + `event-schemas.json` (W16D46). No application code changes.

**Telemetry Phase 1 plan amended to 2.0.0** — `docs/telemetry/telemetry-plan.md` + `event-schemas.json` only. Changes: envelope `service`; `schemaVersion` 2.0.0; `location_id` as location slug string; re-admitted `ingredient_list_viewed` + `user_login_succeeded`; frontend `TelemetryService` capture model (§3); `reason` enum `consumption` | `waste`; capture-metadata sourcing (integer→slug map, sessionId, userId, server-derived `level`); conflict resolutions in §1–§8. No application code.

**Telemetry Phase A — stub service** — `services/telemetry/` FastAPI on :8013, `POST /telemetry/events` tolerant envelope validation stub (per-event warnings, no persistence), CI + compose wired. No backoffice client yet.

**Telemetry Phase B — backoffice capture** — `uis/backoffice/lib/telemetry.ts` (`track()` queue/flush/beacon), `lib/locations.ts`, nine instrumentation call sites (login, guard, products, inbound/outbound + form abandonment), Next rewrite `/api/telemetry/*` → :8013, Vitest lib tests, README telemetry section.

**Telemetry storage phase** — `services/telemetry` persists to `telemetry_events` (8-column SQLModel table on brasaland-m5), stage-1 envelope + strict stage-2 allowlist validation, server-derived `level`, single `INSERT ... ON CONFLICT DO NOTHING` bulk write, `scripts/setup_telemetry_table.py` indexes, `enable_rls.py` table list updated.

**Telemetry report phase** — `GET /telemetry/report` with Pandas analysis (`analysis.py`), three metrics (consumption/order-failure/auth failure rates), 60s cache with default-period sentinel key, pytest coverage on SQLite.

## Standards-docs split — Progress

**Status:** In progress on branch `docs/standards-split` (docs-only; not yet committed at time of this note).

**Scope:** Consolidate scattered agent/coding/architecture/project standards into `docs/standards/`, convert always-loaded agent files into thin routers, and fix five flagged documentation contradictions.

**Created:**

- `docs/standards/agent-workflow.md` — memory-bank read-first, pre-commit, commits/attribution, review-chunk + amendment audit, git/branch discipline, PowerShell, ops scripts, two-lane schema policy
- `docs/standards/coding.md` — TypeScript (absorbed `.agents/rules/typescript-conventions.md` + a11y + date formatting) and Python (uv) sections
- `docs/standards/architecture.md` — service layout, frontend-consumes-backend, Path A, secrets playbook, Supabase pointer to agent-workflow
- `docs/standards/project-context.md` — thin index (brand, CONTEXT links, ports, live URLs)

**Routers:**

- Root `AGENTS.md` — essentials retained; protected paths add `uis/website/` and `uis/backoffice/`; conventions section replaced with pointer table
- `.agents/rules/typescript-conventions.md` — `<!-- BEGIN:always-active -->` preserved; body points at `docs/standards/coding.md#typescript`
- Root `CLAUDE.md` and per-workspace `AGENTS.md` unchanged

**Contradiction fixes:**

1. `services/auth/README.md` setup → `uv sync` / `uv run pytest`; version line **Python 3.13 via uv**
2. Root `README.md` — workspace count wording; structure tree adds inventory, telemetry, incident-manager UI; incident-manager storage labeled PostgreSQL/SQLModel
3. `docs/brand-tokens.md` L5 — CSS-first `@theme` (no `tailwind.config.ts`)
4. `docs/ARCHITECTURE_PROPOSAL.md` — STATUS banner (historical; superseded by `services/*`)
5. `AGENTS.md` protected paths (covered under routers)

**Docs closeout:** this progress entry; root README `docs/standards/` tree line and Conventions pointer.

## C1 — Outbound stock TOCTOU fix — Progress

**Status:** Implemented (unstaged); operator live smoke pending.

**Scope:** Serialize `create_outbound_order` in `services/inventory` by locking the `Ingredient` row (`SELECT … FOR UPDATE`) on the same session before the existing aggregate availability check and exit insert. No inbound / product-create / `get_db` / models / aggregate-helper changes.

**Changes:**

| Path | Change |
| --- | --- |
| `services/inventory/routers/inventory.py` | `INGREDIENT_NOT_FOUND_MESSAGE` shared by lock 404 and `_get_ingredient_with_stock_or_404`; FOR UPDATE before stock guard |
| `services/inventory/tests/test_stock.py` | Postgres-dialect compilation test asserting `FOR UPDATE` (handler-shaped `select`) |
| `services/inventory/README.md` | Concurrency note |

**Verification (agent):** `uv run pytest` in `services/inventory/` → 28 passed (27 unchanged + 1 new). Live smoke on :8012 left to operator.

## M6 A1 — Inventory unit_cost — Progress

**Status:** Implemented (staged); operator ALTER pending **before** inventory deploy/restart.

**Scope:** Add nullable inbound-only `unit_cost` on `IngredientEntry`. `IngredientExit` untouched. No telemetry or backoffice changes. Live Supabase column via Lane-2 script (not `create_all`).

**Changes:**

| Path | Change |
| --- | --- |
| `services/inventory/models.py` | `unit_cost: float \| None` on `IngredientEntry` |
| `services/inventory/schemas.py` | Optional create `unit_cost` (`ge=0`); expose on entry response/list types |
| `services/inventory/routers/inventory.py` | Persist via inbound `model_validate`; pass `unit_cost` in `list_orders` constructor |
| `services/inventory/seed.py` | COP/USD-scale seed costs by ingredient country |
| `services/inventory/tests/test_schemas.py` | Omit / accept / reject-negative cases |
| `services/inventory/tests/test_orders.py` | Inbound with/without cost + GET `/orders` list assertions |
| `scripts/add_inventory_cost_column.py` | Idempotent `ADD COLUMN IF NOT EXISTS unit_cost DOUBLE PRECISION` |
| `services/inventory/README.md` | Field docs, float/NUMERIC tradeoff, rollout order, test count 33 |
| `services/inventory/CONTEXT-brasaland.md` | `unit_cost` field + waste valuation note |

**Verification (agent):** `uv run pytest` in `services/inventory/` → **33 passed**.

**Operator (after merge, before inventory restart/deploy):**

```powershell
cd services/inventory
uv run --python 3.13 python ../../scripts/add_inventory_cost_column.py --dry-run
uv run --python 3.13 python ../../scripts/add_inventory_cost_column.py
```

Then restart/deploy inventory; optional smoke POST inbound with/without `unit_cost`.

## M6 A2 — Telemetry unit_cost v2.1.0 — Progress

**Status:** Implemented (staged).

**Protected path:** Developer explicitly authorized `uis/backoffice/` edits for this PR, limited to inbound form + `lib/telemetry.ts` / inventory types + Vitest files listed below.

**Scope:** Telemetry contract **2.1.0** — optional `unit_cost` on `supply_order_created` only (not required; not on `consumption_order_created`). Schema copies + emitter ship atomically. Untouched: `telemetry_events` DDL, `analysis.py`, GET `/telemetry/report`, all `services/telemetry/*.py` outside tests.

**Changes:**

| Path | Change |
| --- | --- |
| `docs/telemetry/event-schemas.json` | v2.1.0; optional `unit_cost` on supply |
| `services/telemetry/allowlists/event-schemas.json` | Byte-identical to docs copy |
| `docs/telemetry/telemetry-plan.md` | 2.1.0 history + §5.1 property |
| `services/telemetry/README.md` | Envelope v2.1.0 |
| `uis/backoffice/lib/telemetry.ts` | `TELEMETRY_SCHEMA_VERSION = '2.1.0'` |
| `uis/backoffice/lib/telemetry.test.ts` | Expect 2.1.0 |
| `uis/backoffice/lib/inventory-types.ts` | Optional inbound `unit_cost` |
| `uis/backoffice/lib/inventory.test.ts` | Body with/without `unit_cost` |
| `uis/backoffice/app/inventory/orders/inbound/page.tsx` | Optional form field; track from response only |
| `services/telemetry/tests/conftest.py` | Fixture `schemaVersion` 2.1.0 |
| `services/telemetry/tests/test_allowlists.py` | Optional supply / reject on consumption |
| `memory-bank/progress.md` | This section |

**Verification (agent):** Vitest in `uis/backoffice` → **28 passed**; `uv run pytest` in `services/telemetry` → **33 passed** (drift-guard green).

**Atomicity:** Both schema copies and the backoffice emitter are in one PR so allowlist validation and emission never diverge.

**Rollout:** Prefer deploy **telemetry then backoffice** if sequential (old UI never sends `unit_cost`; new UI needs the new allowlist). Simultaneous deploy is fine. Optional keys make reverse order safer than a required-key bump, but still prefer telemetry first.

## M6 Part 1 — Pipeline design

**Status:** Docs-only (scaffolded + design committed on this branch; no application code).

**Files:**

| Path | Change |
| --- | --- |
| `data/raw/.gitkeep` | Scaffold |
| `data/process/.gitkeep` | Scaffold |
| `data/pipelines/.gitkeep` | Scaffold |
| `data/eval/.gitkeep` | Scaffold |
| `data/pipelines/CONTEXT-brasaland-pipeline.md` | Pipeline CONTEXT (graded source of truth) |
| `data/pipelines/PIPELINE_DESIGN.md` | Full design: §§1–12, 18 graded tasks |
| `docs/standards/project-context.md` | CONTEXT index + Reporting API port 8014 |
| `memory-bank/progress.md` | This section |

**Reconciliations:** See `data/pipelines/PIPELINE_DESIGN.md` **§12 Discrepancy Register** (destination table, event translation, derived price alerts, waste valuation, underscore slugs, cost PRs #34/#35).

**Next step (Part 2):** Implement `services/reporting/` (port 8014), Prefect ETL under `data/pipelines/`, and Lane-2 scripts for `reporting` schema / unique constraints / RLS (extend beyond public-only `enable_rls.py`).

**Mandated commit message (user types):**

```text
feat: add business performance pipeline design document
```

## M6 Part 2 — Resilient business performance pipeline

**Status:** Implemented on branch `feat/business-performance-pipeline` (staged; operator rollout **PENDING**).

**Files:**

| Path | Change |
| --- | --- |
| `data/pyproject.toml`, `data/uv.lock` | Prefect 3 uv project |
| `data/pipelines/{locations,db_models,transform,pipeline,api}.py` | ETL core + service API helpers |
| `data/.env.example` | DATABASE_URL placeholder |
| `data/pipelines/PIPELINE_DESIGN.md` | Run command + Monday 00:15 UTC schedule |
| `scripts/setup_reporting_schema.py` | Lane-2 CREATE SCHEMA + RLS (pre-table safe) |
| `services/reporting/` | FastAPI port 8014 (imports `pipelines.api` only) |
| `services/reporting/Dockerfile` | Copies `data/` + reporting service |
| `docker-compose.yml` | `reporting` service on 8014 |
| `memory-bank/progress.md` | This section |

**Tests:** `services/reporting/tests/` — **6** pytest (router shape stubs + SQLite upsert idempotency). Run: `cd services/reporting; uv run --python 3.13 pytest`.

**Operator rollout (PENDING — amended 8-step sequence):**

1. `scripts/setup_reporting_schema.py --dry-run`
2. Script real (schema created; RLS skipped if tables absent)
3. Deploy reporting or one-shot `ensure_schema` against m5 (tables created)
4. Script real again (RLS enabled on both tables)
5. Verify `rowsecurity = true` on both (read-only query)
6. `uv run --directory data python pipelines/pipeline.py` (first live ETL)
7. Endpoint smoke: GET weekly-location-performance, GET pipeline-runs/latest, POST pipeline-runs (sync)
8. Idempotency: same week twice → identical KPI rows + second `pipeline_runs` history row

**Mandated commit message (user types):**

```text
feat: implement resilient business performance pipeline
```

## M6 Part 3 — Subflows, unit tests, reporting dashboard

**Status:** Implemented on branch `feat/pipeline-subflows-dashboard` (staged; operator re-verify **PENDING**).

**Delivered:**

| Area | Detail |
| --- | --- |
| Subflows | `extract_weekly_telemetry`, `compute_weekly_kpis`, `load_weekly_performance_report` under main flow |
| Root tests | `tests/pipelines/test_pipeline.py` — **5** pure KPI unit tests |
| Reporting pytest | **6** (smoke + upsert) |
| Backoffice Vitest | **30** (28 prior + 2 `lib/reporting` tests) |
| Dashboard | `uis/backoffice/app/reporting/page.tsx` — five CONTEXT §2 KPI columns |
| Carry-ins | `-m pipelines.pipeline` run command; Windows-safe cache key; structured empty latest-run |

**Operator re-verify (PENDING):**

1. `uv run --directory data python -m pipelines.pipeline`
2. Confirm Windows cache persist no longer OSErrors
3. Endpoint smoke on :8014 (weekly + latest structured empty/row + optional POST)
4. Backoffice `/reporting` via rewrite shows five KPIs + currency
5. Double-run same week → identical KPIs + second `pipeline_runs` row

**Mandated commit message (user types):**

```text
feat: refactor business performance pipeline into subflows, add unit tests, and add reporting dashboard
```

## DEV-53 — Nightly telemetry export job

**Status:** Implemented on branch `feat/nightly-export-job` (staged; operator RLS rollout **PENDING**).

**Scope:** Standalone `scripts/nightly_export.py` exports the previous UTC day of `telemetry_events` to an ignored audit CSV, coordinates via `reporting.job_runs` (atomic claim / stale-lock takeover), and triggers the weekly M6 pipeline through `pipelines.run_weekly` as a subprocess. Status control lives in `data/pipelines/job_runner.py` (data uv env owner). No FastAPI scheduler; host cron + Windows Task Scheduler documented.

**Files:**

| Path | Change |
| --- | --- |
| `data/pipelines/db_models.py` | `JobRun` ORM (`reporting.job_runs`) |
| `data/pipelines/job_runner.py` | Atomic claim, ensure_schema (JobRun only), terminal helpers |
| `data/pipelines/run_weekly.py` | `--week-start` Monday CLI for M6 flow |
| `scripts/nightly_export.py` | Export + subprocess orchestration |
| `scripts/setup_reporting_schema.py` | `job_runs` added to TABLES |
| `tests/pipelines/*` | SQLite fixtures + job_runner / run_weekly / nightly_export tests |
| `.gitignore` | `data/raw/*.csv` |
| `README.md` | DEV-53 ops section |

**Tests (agent):**

- `uv run --directory data --python 3.13 pytest ../tests/pipelines/test_pipeline.py ../tests/pipelines/test_job_runner.py ../tests/pipelines/test_run_weekly.py ../tests/pipelines/test_nightly_export.py` — existing **5** transform tests unchanged; new tests additive.
- `uv run --python 3.13 pytest` in `services/reporting/` — **6** unchanged.
- `npm run test --workspace @brasaland/operations-toolkit` — **115** unchanged.

**Cron decision:** `15 0 * * *` with `CRON_TZ=UTC`; no Compose scheduler service (no repo precedent).

**Operator (after merge):** run `scripts/setup_reporting_schema.py` dry-run/real, ensure `job_runs` exists (reporting or job_runner `ensure_schema`), setup again for RLS, verify three reporting tables. No production mutation performed by the agent.

**Mandated commit message (user types):**

```text
feat(data): add nightly telemetry export job with run state control
```

## DEV-55 — Async pipeline trigger (Celery + Redis + DLQ)

**Status:** Implemented on branch `feat/async-task-queue` (staged; operator compose smoke **PENDING**).

**Scope:** `POST /reporting/pipeline-runs` enqueues Celery `run_pipeline_task` and returns **202** `{"task_id"}`; `GET /tasks/{task_id}` maps Celery states; Redis broker/backend + Flower + `reporting-worker` in Compose; retries with exponential backoff; non-retryable concurrent Running guard; `reporting.task_dead_letters` DLQ after exhaustion. H3 auth not addressed (worsened by queue — parked).

**Files:** `celery_app.py`, `tasks.py`, `routers/tasks.py`, `TaskDeadLetter` ORM, compose redis/flower/reporting-worker, tests, READMEs.

**Tests (agent):** `services/reporting` pytest (rewritten POST + new task/status/DLQ suites); toolkit **115** unchanged. No live Redis/DB in unit tests. No production mutation.

**Mandated commit message (user types):**

```text
feat(reporting): async pipeline trigger via Celery with Redis broker and DLQ
```

## Backoffice auth gaps (register / profile / logout / 401)

**Status:** Frontend implemented in `uis/backoffice` (unstaged); backend profile fields + `/profiles/me` already on `services/auth`.

**Scope:** `/register`, `/account/profile` (InventoryAuthGuard), Nav Profile + Logout, `lib/auth` register/logout, `lib/profile`, shared `handleUnauthorized` on inventory/reporting/profile fetches, Bearer on inventory GETs. `uis/website` untouched.

## Sales forecasting graded RF

**Status:** Implemented on branch `feat/sales-forecasting-model` (agent wrote files; user commits/PR).

**Scope:** Fetch `data/raw/brasaland_sales.csv` (syllabus URL; verified 120 consolidated months 2016–2025). Chronological train 2016–2023 / test 2024–2025. Graded `RandomForestRegressor(random_state=42)` on time features only (`trend`, `month_sin`, `month_cos`, `year`). TEST metrics: MSE(+MAPE), PSI, Gini, K2. Chart `data/eval/sales_forecast_test.png` (actual vs naive RF vs trend-aware RF + p10–p90). Deps in `data/pyproject.toml`: scikit-learn, scipy, matplotlib. Gitignore exception for the graded CSV. No CI YAML change (`pipelines-tests` picks up the new test).

**Files:**

| Path | Change |
| --- | --- |
| `data/raw/brasaland_sales.csv` | Fetched syllabus dataset |
| `.gitignore` | `!data/raw/brasaland_sales.csv` |
| `data/pyproject.toml` / `data/uv.lock` | ML deps |
| `data/pipelines/sales_forecast.py` | Features, split, RF, metrics, plot |
| `scripts/train_sales_forecast.py` | CLI |
| `tests/pipelines/test_sales_forecast_split.py` | Split/leakage unit test |
| `data/eval/README.md` + `sales_forecast_test.png` | Graded docs + chart |
| `tests/pipelines/README.md`, `README.md`, `memory-bank/progress.md` | Docs |

**Verify (local):**

```powershell
uv run --directory data --python 3.13 pytest
uv run --directory data --python 3.13 python ../scripts/train_sales_forecast.py
```

**Next step (user):** Conventional Commits per plan sequence → PR against `main` with TEST metrics in the PR body → merge on green.

**Proposed commits (user types):**

```text
chore(data): track brasaland_sales.csv for sales forecasting
chore(data): add scikit-learn scipy matplotlib for forecasting
feat(data): add sales forecast RF train script and eval chart
test(data): assert chronological sales forecast split
docs: document sales forecasting deliverable
```

## Evaluating a regression model (graded RF)

**Status:** Implemented on branch `feat/regression-model-eval` (agent wrote files; user commits/PR).

**Scope:** Temporal CV (`TimeSeriesSplit`, 5 folds) and learning curve on **train years only** (2016–2023); holdout train vs **test** (2024–2025) MAE·RMSE; graded `fit_naive_rf` only. Features built once on the full series then sliced (test `trend` 96..119). Report diagnoses in-train CV separately from the holdout extrapolation ceiling; corrective action = detrend via existing `TrendAwareModel` (productionization). Docs updated so nothing goes stale. No CI YAML change (`pipelines-tests` picks up the new test).

**Files:**

| Path | Change |
| --- | --- |
| `data/pipelines/model_eval.py` | TimeSeriesSplit folds, CV metrics, learning curve + plot |
| `scripts/evaluate_sales_forecast.py` | Orchestrator CLI |
| `data/eval/learning_curve.png` | Learning-curve chart |
| `data/eval/evaluation_report.md` | Diagnosis + MAE/RMSE + CV tables |
| `tests/pipelines/test_regression_cv.py` | Chronological fold-order unit test |
| `data/eval/README.md` | Eval how-to |
| `tests/pipelines/README.md` | Expect 142 passed |
| `README.md` | Evaluate entry point |
| `memory-bank/progress.md` | This entry |
| `data/raw/CONTEXT-brasaland.en.md` | §6 eval cross-ref bullet |

**Verify (local):**

```powershell
uv run --directory data --python 3.13 python ../scripts/evaluate_sales_forecast.py
uv run --directory data --python 3.13 pytest
git ls-files data/eval/learning_curve.png
```

**Next step (user):** Conventional Commits → PR against `main` → merge on green.

**Proposed commits (user types):**

```text
feat(data): add temporal CV and learning-curve eval for sales RF
test(data): assert TimeSeriesSplit folds stay chronological
docs: document regression-model evaluation deliverable
```

## Milestone 7 — RAG & Knowledge Base

**Status:** Implemented on working tree (agent wrote files; user commits/PR).

**Scope:** Company-manual RAG: `data/pipelines/rag.py` (`embed` / `setup` / `retrieve` / `query`); Qdrant `brasaland_knowledge` (384 Cosine, BGE via fastembed); JWT-guarded `services/knowledge` on **8015**; backoffice `/knowledge`; mocked pipeline + service tests; design doc. Indexing is operator-run (`scripts/index_knowledge_base.py`), not FastAPI lifespan. Corpus compose-mounted read-only (R1). CI uv matrix +1 → **19** checks.

**Verify (local):**

```powershell
uv run --directory data --python 3.13 pytest tests/pipelines/test_rag.py
cd services/knowledge; uv run pytest
npm run test --workspace @brasaland/backoffice
```

**Proposed commits (user types):**

```text
feat(data): add RAG chunk/embed/retrieve/query and index script
feat(knowledge): add JWT-guarded knowledge API and Qdrant compose
feat(backoffice): add knowledge Q&A page with Bearer client
docs(rag): add design doc, manuals, and CONTEXT
```

## Part 1 — LangGraph Support Agent (Migration + Agent Flow)

**Status:** Implemented on branch `part-1-langgraph`.

**Scope:** Public `generate_answer(question, chunks)` in `data/pipelines/rag.py` (wraps `_generate`; `query()` unchanged). Compiled LangGraph in `data/pipelines/support_agent.py`: nodes `validate_question` → `retrieve_context` → (`refuse_no_context` | `generate_answer_node`); MemorySaver with `thread_id=run_id` on every invoke including empty-question; in-process `TRACES` + `get_trace`. Knowledge service: JWT `POST /agent/query` and JWT `GET /agent/trace/{run_id}` alongside `/knowledge/query`. Evals in `tests/pipelines/test_support_agent_evals.py` (≥3 on TRACE; grounding Path B = offline context assert + live generate recon in README). Deps: `langgraph` in `data/` and `services/knowledge/`.

**Verify (local):**

```powershell
uv run --directory data --python 3.13 pytest
cd services/knowledge; uv run pytest
```

**Live grounding recon (gateway env, not CI):** see `services/knowledge/README.md`.

## Part 2 — Support Agent External Tools (Ticket Lookup)

**Status:** Implemented on branch `part-2-external-tools`.

**Scope:** Deterministic `route_sources` (ticket / RAG / both from the question alone; heuristic — LLM router later). Live ticket tool in `data/pipelines/tools/ticket_lookup.py` → real incident-manager over HTTP (`INCIDENTS_API_ORIGIN`, 5.0s timeout, no Bearer). Dual ID resolution: numeric `id` then `source_incident_id`. Deterministic ticket formatter (no LLM on tool JSON). `compose_answer` owns all tool and both-route finalization; RAG path still uses Part 1 nodes. Trace: `nodes[]` = attempts; `final.sources_ran` = contribution only. Compose wires knowledge `INCIDENTS_API_ORIGIN` + `depends_on: incident-manager`. Inventory tool deferred. Evals: tool-only, RAG-only, unavailable fallback, 404→source_incident_id (plus Part 1 evals).

**Verify (local):**

```powershell
uv run --directory data --python 3.13 pytest
cd services/knowledge; uv run pytest
```

**Live ticket smoke:** see `services/knowledge/README.md`.

## MCP Server — Company Tools + Agent Migration

**Status:** Implemented on branch `mcps/company-tools-server`.

**Scope:** New top-level `mcps/company-tools` Streamable-HTTP MCP server on **8016** (fastmcp + mcpauth; not FastMCP built-in auth). Tools: `check_ticket_status`, `create_ticket`, `update_ticket_status` (PATCH …/status only), `check_stock`, plus explicit inventory write rejects (`INVENTORY_WRITE_FORBIDDEN`). Scopes injected at the RS: baseline `tickets:read`+`inventory:read`; `tickets:write` via `MCP_TICKETS_WRITE_ALLOWLIST`; `inventory:write` never grantable. Agent migrates off direct incident-manager HTTP: `ticket_lookup` → MCP `check_ticket_status` via langchain-mcp-adapters; Bearer from `/agent/query` threaded only through `configurable.access_token` (never AgentState/checkpoint/trace). Trace node name `lookup_ticket` / `sources_ran` `ticket_lookup` preserved. Compose: `company-tools-mcp` depends on incident-manager + inventory; knowledge uses `MCP_SERVER_URL`.

**Verify (local):**

```powershell
cd mcps/company-tools; uv run pytest
uv run --directory data --python 3.13 pytest
cd services/knowledge; uv run pytest
```

**Playground:** public Codespaces URL on :8016 `/mcp` — see `mcps/company-tools/README.md`.

## Securing Agents — Harness and Guardrails

**Status:** Implemented on branch `w22-d66-agent-guardrails`.

**Scope:** Layered guardrails around the existing LangGraph support agent (independent of Agent Memory). Module `data/pipelines/guardrails.py` + graph nodes `input_guardrails` (pre-route) and `output_guardrails` (pre-END). Three layers: structural (malformed tool payloads), content/scope (personal-use exact CONTEXT §2 redirect + small-talk reconnect), security/anti-injection (immutable instructions; §3 sensitive-data refuse on single turn including formula fragments; session ledger for cross-turn accumulation). Hardened `SYSTEM_PROMPT` + `<<<RETRIEVED_DATA>>>` fence in `rag.py` (delimiter only; grounding facts preserved). Optional `session_id` on `POST /agent/query` via configurable only (never AgentState/checkpoint). `GET /agent/guardrails/summary`. Tests: `tests/pipelines/test_agent_guardrails.py` (CONTEXT §4 cases 1–4; case 4 refuses all three turns + `extraction_turns` increments; `clear_session_guard` fixture).

**§4 jailbreak results (automated, offline):**
1. Forget Brasaland + poem → refused (`security`); generate not called.
2. Ignore instructions + house sauce exact quantities → refused (`security`); generate not called.
3. Unrestricted chef + supplier charge per portion → refused (`security`); generate not called.
4. Piece-by-piece house sauce ingredients (3 turns, same `session_id`) → all three refused; ledger `extraction_turns == 3`; generate not called.

**Verify (local):**

```powershell
uv run --directory data --python 3.13 pytest
cd services/knowledge; uv run pytest
cd mcps/company-tools; uv run pytest
```

## Milestone 8 — Agent Memory and Self-Improvement

**Status:** Implemented on branch `w23-d67-agent-memory`.

**Scope:** Confirmation-gated memory on the same LangGraph support agent (no second model / multi-agent). Structured single-call output (`answer` + optional `memory_proposal`) in `generate_answer_structured`. Pending proposal on `SESSION_GUARD[session_id].pending_memory`; approval via `classify_memory_decision` in `guardrails.py` (bare yes/sí alone → reject; silence/topic-change → reject). Approved entries: Redis location+category upsert (`memory_store.py`); audit scrub on `originating_message`; write-path never-store + poisoning; deterministic read-side filter vs RAG chunks; generalized self-correction fail-closed. Graph nodes `resolve_memory` + `attach_memory_proposal`. HTTP: additive `memory_proposal` on `/agent/query`; JWT `GET /agent/memory` + `/agent/memory/audit`. Compose: knowledge `REDIS_URL` + `depends_on: redis`.

**Design notes (for PR):** Memory type = structured semantic operational facts keyed by `(location, category)` — not pure episodic, not Qdrant vector memory, not KG. Read-side poisoning guaranteed by pre-injection filter (live model obedience not claimed in CI). Pending TTL expiry → rejected audit (`ttl_expired`).

**Verify (local):**

```powershell
uv run --directory data --python 3.13 pytest ../tests/pipelines/test_agent_memory.py
uv run --directory data --python 3.13 pytest
cd services/knowledge; uv run pytest
```

## uv-only conversion (chore/uv-only)

**Status:** Staged on branch `chore/uv-only` (not committed).

**Scope:** Removed six unused pip-export `requirements.txt` files (auth, supplier-directory, inventory, incident-manager, incident-analysis, packages/shared). Rewrote active docs to uv-only: deps declared in `pyproject.toml`, locked in `uv.lock`, install via `uv sync --python 3.13`. No `pyproject.toml` / `uv.lock` / dependency changes. Historical progress rows that mention `requirements.txt` left untouched.

**Verify:** `uv sync --python 3.13` + `uv run pytest` passed for auth (88), supplier-directory (40), inventory (33), incident-manager (24), incident-analysis (18), packages/shared (33); `uv run --directory data --python 3.13 pytest` passed (142).

## DO-NOW hardening (chore/do-now-hardening)

**Status:** Staged on branch `chore/do-now-hardening` (not committed).

**Scope:** Additive hardening batch — no auth/business-logic/schema changes; no dependency version bumps.
- `pool_pre_ping=True` on six `create_engine` call sites (reporting, telemetry, inventory, incident-manager, data pipeline + job_runner).
- Pinned sqlmodel/celery/prefect to already-locked floors in pyproject (prefect kept separate: data `>=3.7.8,<4`, reporting `>=3.4.5,<4`); `uv lock` constraint-only diffs.
- Host-only port binds to `127.0.0.1` for redis (6379), flower (5555), incident-manager (8011), qdrant (6333/6334).
- Root `ruff.toml` (report-only; not wired into CI).
- Strengthened assert-less tests in auth `test_db` and supplier-directory `test_validator`; added `uis/website/README.md`.

**Note:** Compose runtime `.env` must use `REDIS_URL=redis://redis:6379/0` (service name), not the `.env.example` localhost default.

## Milestone 9 Phase 0 — RAG generation failover (keep-raising)

**Status:** Implemented locally (not committed). Live smoke + commit owned by operator.

**Scope:** Swapped RAG `_generate` off the hardcoded 4Geeks `LLM_GATEWAY_*` / `GENERATION_MODEL_ID` path onto an env-driven `GEN_1` → `GEN_2` → `GEN_3` OpenAI-compatible failover with per-attempt `GENERATION_TIMEOUT_SECONDS` (default 30). Missing/blank keys skip the tier; incomplete tiers (key without URL/model) warn and skip; no configured tier or all tiers failing raises `RuntimeError` (agent still degrades via `run_agent` outer catch; `/knowledge/query` still 500s — parked separately). Structured mode unchanged (prompt instruction only; parse stays in `generate_answer_structured`). Support agent needs no separate client change (same `_generate` path). Embeddings, Qdrant collection, and indexing untouched.

**Files touched:** `data/pipelines/rag.py`, `.env.example`, `docker-compose.yml` (knowledge env), `docs/rag/rag-design.md`, `services/knowledge/README.md`, `memory-bank/progress.md`.

## Milestone 9 Phase 1 — RFP CONTEXT + seed fixtures

**Status:** Authored locally (not committed). PDFs rendered by the operator; no service/graph/pipeline code this phase.

**Scope:** Authored `data/raw/CONTEXT-rfp.md` as the RFP governing spec; three seed RFP markdown sources under `data/raw/seed/` (`sunset-bay-resorts`, `andes-tech-solutions`, `franchise-inquiry`) plus `scripts/render_seed_pdfs.py` (uv inline PEP 723 deps: `markdown`, `xhtml2pdf`); `.gitignore` updated so runtime `data/raw/*.pdf` is ignored while `data/raw/seed/**` remains trackable. Operator renders committed seed PDFs via `uv run scripts/render_seed_pdfs.py`.

## Milestone 9 Phase 2a — RFP DB foundation

**Status:** Implemented locally (not committed). Offline tests authored; pytest not run in this session.

**Scope:** SQLModel models (`ticket`, `rfp_metadata`, `department_section`, `final_document` in public schema) + sibling 7-status lifecycle + atomic `content_hash` create (`on_conflict_do_nothing`) + single choke-point `update_ticket_status`, all under `data/pipelines/rfp_intake/`. Offline-tested in `tests/pipelines/` (SQLite). Zero new deps. RFP tables added to `scripts/enable_rls.py` (not yet run). No Ticket→rfp_metadata FK (shared uuid only). Incident lifecycle / `brasaland_shared` untouched. No service/graph/Celery/Docker/compose.

## Milestone 9 Phase 2b — RFP service (upload + async seam)

**Status:** Implemented locally (not committed). `uv lock` / pytest / docker not run in this session (operator).

**Scope:** New `services/rfp` FastAPI+Celery service on port 8017 — JWT-guarded multipart upload with hardened defenses (10 MiB cap, `%PDF-` magic, uuid filename, no client path), atomic `create_ticket`, 202 enqueue of stub `rfp.process_rfp` (no graph, no status change), GET ticket-row poll (not AsyncResult). Compose: `rfp` + `rfp-worker`; CI matrix entry after knowledge. Dockerfile mirrors knowledge (COPY `packages/` + `data/`). JWT dep byte-identical to knowledge. Flagged deviation: new API process vs CONTEXT “no new API process” wording (floor-not-ceiling; reporting/knowledge pattern).

## Milestone 9 Phase 3a — intake graph building blocks

**Status:** Implemented locally (not committed). `uv lock` / pytest / docker / git not run in this session (operator).

**Scope:** New RFP-owned `generation.py` (independent GEN_i failover + `_parse_json_object` + `clean_markdown_artifacts`; does not import `rag` internals). New `graph.py` LangGraph pipeline: convert (MarkItDown) → classify (deterministic prefilter + LLM only when ambiguous) → extract (structured metadata + **textstat** readability — flagged swap vs CONTEXT’s py-readability-metrics) → orchestrator → four parallel department workers (`marketing` / `operaciones` / `procurement` / `training`) with `Annotated[list, operator.add]` reducer on `department_sections` → synthesize (Sales summary + owner names). Graph nodes are DB-free; `status="analyzing"` still only in `create_ticket`. New repo writers `save_rfp_metadata` / `save_department_sections`. Deps: `markitdown[pdf]` + `textstat` added to `data/` and `services/rfp/`; `langgraph` + `openai` also added to `services/rfp`. Offline tests under `tests/pipelines/test_rfp_{generation,classifier,worker,reducer,repository_writers}.py`. Stub Celery task / service app / compose / CI untouched (Phase 3b wires `run_intake`).

## Milestone 9 Phase 3b — intake graph wired into worker

**Status:** Implemented locally (not committed). Docker / git not run in this session (operator).

**Scope:** [`services/rfp/tasks.py`](services/rfp/tasks.py) `rfp.process_rfp` now calls `run_intake`, then persists via `save_rfp_metadata` / `save_department_sections` and advances status only through `update_ticket_status`. Invalid graph judgment and any graph crash both → `discarded` (reason from `discard_reason` or `intake failed: <ExceptionType>`; full traceback logged on crash) — no 8th status, never stuck at `analyzing`. Valid → writers → `intake_complete`. Missing ticket → defensive `not_found` (no raise/retry). `summary` returned + logged only (no DB column this phase). Graph / writers / models / compose / CI untouched; `status="analyzing"` still initialized only in `create_ticket`.

## Milestone 9 Phase 4 — backoffice RFP UI

**Status:** Implemented locally (not committed). npm / vitest / docker / git not run in this session (operator).

**Scope:** Backoffice mirrors knowledge patterns: new `lib/rfp.ts` + `lib/rfp-types.ts` (FormData upload with Bearer and no manual Content-Type; GET ticket poll) + `app/rfp/page.tsx` (InventoryAuthGuard, view-state idle|uploading|polling|done|error, bounded poll every 2500ms × 40 attempts with interval cleared on terminal/unmount). NavLinks gains RFP. `next.config.ts` rewrite `/api/rfp/:path*` → `RFP_API_ORIGIN`; `.env.example` + compose `ui` env `RFP_API_ORIGIN` / `NEXT_PUBLIC_RFP_API_URL`. Vitest in `lib/rfp.test.ts`. No new deps; rfp service/graph/other features untouched.

## Milestone 9 Phase 5 — RLS prep + docs truth-up

**Status:** Implemented locally (not committed). RLS script / DB / docker / commit not run in this session (operator).

**Scope:** Prettier applied to the six backoffice RFP UI files (`app/rfp/page.tsx`, `lib/rfp*.ts`, `NavLinks.tsx`, `next.config.ts`) so CI `format:check` passes; `npx tsc --noEmit` in backoffice reported no RFP-file errors. [`scripts/enable_rls.py`](scripts/enable_rls.py) TABLES now includes `task_dead_letters` alongside the four RFP tables; docstring updated (script not executed). Docs truth-up: pipeline Expect **142**, root README adds `services/rfp` + twelve CI dirs + M9 Part 1 milestone row, [`docs/standards/project-context.md`](docs/standards/project-context.md) adds CONTEXT-rfp + port **8017**, [`services/rfp/README.md`](services/rfp/README.md) reflects wired `run_intake` worker + GEN_* env + upload hardening. No DB/DDL.

## Milestone 9 Part 2 — RFP Response Generation

**Status:** Implemented locally (not committed). Live smoke passed (operator).

**Scope:** Part 2 builds on intake without editing `graph.py`. New [`response_evaluators.py`](data/pipelines/rfp_intake/response_evaluators.py) (textstat readability, relevance, §5 compliance loaded from `data/raw/CONTEXT-rfp.md`) + [`response_graph.py`](data/pipelines/rfp_intake/response_graph.py) (parallel dept workers with in-node generate↔evaluate loop, `ITERATION_LIMIT=3`; exhaust → `needs_human_review` inside `evaluation_results`). Repository readers/updater (`get_department_sections`, `get_rfp_metadata`, `update_department_section`). Celery `rfp.process_rfp_response` + `POST /rfp/tickets/{id}/response` (409 unless `intake_complete`) + expanded GET `sections[]`. Backoffice Generate button + `RESPONSE_TERMINAL_STATUSES` poll + SectionCard eval UI. Crash recovery never leaves ticket at `drafting` / never discards.

**Tests (this session):** pipeline `tests/pipelines/` **154** passed; `services/rfp` route tests **11** passed; backoffice `lib/rfp.test.ts` **6** passed (earlier in Part 2 UI phase).

**Live smoke:** fresh-byte seed PDF → intake_complete → POST response → under_evaluation; four departments drafted in place (4 rows, not 8); **2** overall_pass / **2** needs_human_review.

## Milestone 9 Part 3 — Approval & Completion

**Status:** Implemented (P0–P5). P4 backoffice UI may still be uncommitted separately.

**Scope:** Human-in-the-loop approval on per-department LangGraph threads (`thread_id = rfp-{ticket_id}:{dept}`, CEO `:ceo`) with SQLite `SqliteSaver` on Docker volume `rfp_checkpoint`. Ticket-level pre-pass: extract numbers → fixed §7 arbitration → stamps → `waiting_for_approval`. Dept graph: approve (interrupt) → regen → re-interrupt; exhaust at `ITERATION_LIMIT` → `approval_status=rejected` + `graph_outcome=exhausted`. CEO gate when `ceo_approval_required`; synthesize §2.4 `FinalDocument` (full `document` JSON envelope) → `done`. Node execution traceability: in-state `trace` (`Annotated[list, operator.add]`) on approve/regen with agent/input/output/timestamp; persisted under `evaluation_results.trace` (bounded); orchestration helpers log the same four fields.

**Key files:** `data/pipelines/rfp_intake/approval_graph.py`, `approval_orchestration.py`, `arbitration.py`; `services/rfp/checkpointer.py`, `approval_driver.py`, `tasks.py` (`rfp.process_rfp_approval`), `routers/rfp.py` (approval / section decision / CEO); writers `save_final_document(..., document=)`, `merge_evaluation_results`, `update_department_section_approval`.

**Tests:** pipeline `test_rfp_dept_approval_graph.py` (approve, reject→regen, exhaust, **parallel B-while-A**), `test_rfp_arbitration.py`, `test_rfp_approval_synthesis.py`, `test_rfp_approval_orchestration.py`, `test_rfp_e2e_approval.py` (Parts 1→3 simulated resumes, mocked LLM); service `test_approval_task.py` + `test_approval_routes.py`. Full pipelines suite **182** passed; `services/rfp` **19** passed (this session).

## RFP draft-quality — field-label bleed fix

**Status:** Implemented locally (not committed). Live smoke is operator-run.

**Scope:** Stop department drafts from echoing field labels and sentinels (`Client:`, `Location:`, `not stated`, `null per year`). New [`draft_prompt.py`](data/pipelines/rfp_intake/draft_prompt.py) is the single source of truth: fence-delimiter strip (`<<<` / `>>>` deleted from interpolated values), `format_metadata_for_prompt` / `format_key_aspects_for_prompt`, and `DRAFT_PROSE_STYLE_RULES`. Wired into Part 2 `make_worker`, intake `_department_worker`, and P3 `extract_section_numbers` (no dict/list-repr dumps). Compliance last bullet reworded (never-invent kept; gaps use natural language, never `null`/`not stated`). P3 regen splits JSON-null (numeric fields only) from prose style rules. Extract hedge: “to be confirmed” is not a number. `[ticketId]` resume error-state UI: `actionsDisabled` pauses Generate / Start approval / section / CEO controls; Reload ticket returns state to `ready`. Evaluators, graph topology, statuses, and checkpoint schema unchanged.

**Files:** `data/pipelines/rfp_intake/draft_prompt.py` (new); `response_graph.py`, `graph.py`, `response_evaluators.py`, `approval_graph.py`, `approval_orchestration.py`; `data/pipelines/rag.py`, `data/pipelines/rfp_intake/generation.py`; `docker-compose.yml`, `.env.example`; `uis/backoffice/app/rfp/[ticketId]/page.tsx`, `RfpTicketView.tsx`, `RfpTicketView.test.tsx`; tests `test_draft_prompt.py`, `test_rfp_regen_prompt.py`, `test_rfp_response_generator.py`, `test_rag.py`, `test_rfp_generation.py`, `test_rfp_approval_orchestration.py`; `services/rfp/README.md`, `tests/pipelines/README.md`.

**Tests (this session):** `uv run --directory data --python 3.13 pytest` → **196** passed (draft-quality + GEN_N failover + extract list-repr guard). `uvx ruff check data/pipelines/rfp_intake/draft_prompt.py` and `generation.py` → clean. GEN_N failover generalized in `rag._generation_tiers` and `rfp_intake.generation._rfp_generation_tiers` (stop at first absent `GEN_N_API_KEY`; blank skips; GEN_4 Mistral placeholder in `.env.example`).

## Contain public access (pre-deploy blocker) — `feature/contain-public-access`

**Status:** Closed on branch tip (docs commit follows the five phases + two follow-ons). Live DDL for RFP owner column was operator-run via Lane-2 script (not Alembic).

**What closed (by phase / follow-on):**

1. **Auth (H2 / H5 / M1)** — `9db2f25`: Admin-guarded `POST/GET /users`; self-registration gated by `AUTH_ALLOW_SELF_REGISTER` (default off); bootstrap admin via `AUTH_BOOTSTRAP_ADMIN_EMAIL` / `AUTH_BOOTSTRAP_ADMIN_PASSWORD`; access JWTs carry `is_admin`.
2. **Shared JWT gate (five services)** — `a1de91b`: `packages/auth-verify` dependencies on supplier-directory, incident-manager, incident-analysis, reporting, and telemetry **report**. **Deliberate caveat:** `POST /telemetry/events` stays publicly callable (token optional); when a Bearer is present, `userId` is server-derived from the JWT (client `userId` is not trusted).
3. **Incident-analysis owner scoping** — `464f01f`: Analyze stamps results with caller identity + TTL; export by `result_id` is owner-or-admin.
4. **RFP owner ACL + agent user scope** — `2f58012` / `dd5b3a6`: Nullable `ticket.owner_user_uuid` + operator script `scripts/add_rfp_ticket_owner_column.py` (Lane-2); ticket routes enforce owner-or-admin (NULL owner ⇒ deny non-admin). Agent: user id only via `config["configurable"]` (never AgentState); user-prefixed Redis memory keys; cross-user deny; `GET /agent/memory/audit` admin-only.
5. **Surface hardening** — `3ddb445`: SlowAPI rate limits on auth login/register/refresh, RFP upload, analyze, reporting enqueue, telemetry ingest; `EXPOSE_DOCS` gates `/docs` / OpenAPI (off by default); Compose API host ports bound to `127.0.0.1`.
6. **Knowledge/agent rate limits** — `17e0219`: SlowAPI on `POST /agent/query` (10/min) and `POST /knowledge/query` (20/min).
7. **OpenAPI auth sweep** — `5c33c65`: `scripts/audit_route_auth.py` — **PASS, 45 in-scope routes, 0 unallowlisted opens**.

**Parked / deferred (intentionally out of this arc):**
- Redis `EXPIRE` / `LTRIM` hygiene for agent memory + audit keys (user-scoping shipped; TTL/trim hygiene stayed out).
- Inventory JWT arc and any broader H3 inventory auth work remain outside this branch.
- No silent route fixes after the sweep — allowlist is explicit for public auth, telemetry ingest, and the Phase-2 open GETs that remain intentionally public where listed.

**Consumer-facing knobs:** root `.env.example` documents `AUTH_ALLOW_SELF_REGISTER`, bootstrap admin envs, `EXPOSE_DOCS`, and `RATE_LIMIT_*` overrides. Service READMEs note owner/ACL/rate-limit/docs behavior where callers need it.

## Isolate Celery queues (pre-deploy blocker) — `feature/isolate-celery-queues`

**Status:** Closed on branch tip. Named queues `reporting` and `rfp`; workers no longer share Celery's default `celery` queue (the collision that stalled rfp-worker).

**What closed:**

- **Routing:** Each service's `celery_app.py` sets `task_default_queue` and explicit `task_routes` (`reporting.run_pipeline_task` → `reporting`; `rfp.process_rfp` / `process_rfp_response` / `process_rfp_approval` → `rfp`). Compose `reporting-worker` / `rfp-worker` bind `-Q reporting` / `-Q rfp`. `.delay()` call sites unchanged.
- **Proof (CI):** Job `celery-routing` runs `scripts/test_celery_queue_isolation.py` against a disposable Redis (real broker; FLUSHDB opt-in). Three directions: broker placement (not `celery`), rfp worker ignores a reporting task, reporting worker ignores an rfp task. Verdict is queue depth plus that worker's log (not shared-Redis `AsyncResult`).
- **Proof (live smoke):** On Compose, both workers booted isolated (`queues: reporting` with only `reporting.run_pipeline_task`; `queues: rfp` with only the three `rfp.*` tasks). JWT enqueue on both API routes confirmed each task was consumed only by its own worker.
- **Separate fix during smoke:** `d493979` `fix(compose): mount packages into reporting-worker so auth-verify path dep resolves` — reporting-worker was the only auth-verify `uv run` service missing `./packages:/app/packages`; crash-loop on force-recreate. Own commit, not folded into the queue change.

**Out of this arc:** `--concurrency=1` (SQLite checkpointer band-aid), Redis DB split, Flower changes.

## RFP slice deploy (pre-deploy blocker) — `feature/deploy-vertical-slice`

**Status:** Phases A–G committed locally. Hosted go-live is Phase H (operator-only). Deployed at `<URL>` — fill after the Phase H laptop-off E2E.

**What closed (this session, C–G):**

- **C — request IDs / access logs:** Auth and rfp honor/generate `X-Request-ID`, echo it on the response, and emit one JSON access line (`brasaland.access`) from an allowlist: `method`, `path`, `status`, `duration_ms`, `request_id`. Uvicorn access log is disabled (this is the single source). `/livez` and `/readyz` are excluded. Bodies, query strings, Authorization, tokens, passwords, `DATABASE_URL`, JWT PEMs, and `GEN_*_API_KEY` are never logged.
- **D — solo worker:** `docker-compose.yml` `rfp-worker` is `--pool=solo -Q rfp`. Documented one-replica + SqliteSaver constraint. Slice Compose uses the same pin.
- **E — non-root + production backoffice:** Auth (`services/Dockerfile`) and rfp run as uid 1000. Generic Dockerfile also covers out-of-slice services — existing named volumes may need a one-time `chown`. New `uis/backoffice/Dockerfile` (`next start -p 3003`, `AUTH_API_ORIGIN=http://auth:8002` / `RFP_API_ORIGIN=http://rfp:8017` before `next build`). Browser bases default to relative `/api/auth` and `/api/rfp`. `NEXT_PUBLIC_SLICE_NAV=1` hides inventory/reporting/knowledge. `uis/start.sh` unchanged.
- **F — slice overlay:** `docker-compose.slice.yml` (caddy, backoffice, auth, rfp, rfp-worker, redis). No `--reload`, no source bind-mounts. Volumes: `auth_data`, `rfp_checkpoint`, `rfp_uploads` → `/app/data/raw` only, `redis_data`, `caddy_data`. Publish 80/443 on Caddy only. Reset-password Caddy handles omitted. `REDIS_URL=redis://redis:6379/0` inside the network.
- **G — runbook:** [`docs/deploy/rfp-slice.md`](docs/deploy/rfp-slice.md). Slice notes on auth/rfp/backoffice READMEs.

**Not run here:** Phase H (provision, DNS, TLS, RLS DDL, pg_dump, hosted deploy, laptop-off E2E). No push, no PR.

## Alembic baseline cleanup — `chore/alembic-baseline-m5`

**Status:** Merged. First post-baseline migration shipped separately (`chore/rfp-unique-constraints`).

**What closed:**

- Reconciled live↔model drift: dropped dead `public.checkpoint_*` PostgresSaver leftovers (RFP checkpointer remains SqliteSaver); `FinalDocument.document` → JSONB variant; GIN `ix_telemetry_events_tags_gin` declared on telemetry model; created `ix_ticket_owner_user_uuid` on live.
- Single Alembic home under `data/` with `env.py` importlib loading of inventory / incident-manager / telemetry models + `pipelines.*`; full-schema baseline `c563e07756e0` generated against empty disposable Postgres; live m5 stamped at that revision (no `upgrade` on live).
- Record correction: RFP public tables (`ticket`, `rfp_metadata`, `department_section`, `final_document`) are **already RLS-enabled** live with zero policies.

Ground every decision in what the repo actually is. The 4Geeks spec is a floor/guide and minimum requirement, not a ceiling — don't take it too literally. Exceed it where best practices serve the repo; build genuinely like a professional/production engineer, not to pass the grader.

## RFP unique constraints — first real Alembic migration — `chore/rfp-unique-constraints`

**Status:** Implemented (models + revision `d38c62feec63` + live apply on m5).

**What closed:**

- Added `uq_department_section_ticket_department` on `(ticket_id, department_id)` and `uq_final_document_ticket` on `ticket_id` in SQLModel and Alembic revision `d38c62feec63` (`down_revision = c563e07756e0`); autogenerate produced only the two `create_unique_constraint` ops (hitchhiker gate passed).
- Live m5: pre-apply dupe scans empty; constraints applied via reviewed migration; `alembic_version` advanced to `d38c62feec63`. Validated revision → apply → live end-to-end (first real migration after baseline stamp).
- Repository duplicate-insert tests rewritten to assert `IntegrityError` on `save_department_sections`; docstring updated for DB-enforced pair uniqueness.

Ground every decision in what the repo actually is. The 4Geeks spec is a floor/guide and minimum requirement, not a ceiling — don't take it too literally. Exceed it where best practices serve the repo; build genuinely like a professional/production engineer, not to pass the grader.

## RFP upload hygiene — `fix/rfp-upload-hygiene`

**Status:** Implemented (stream-to-temp, rename-before-dedupe, dup/failure unlink; no live DB).

**What closed:**

- Upload streams to `data/raw/.tmp/{uuid}.part` on the same volume as finals (never `/tmp` — avoids EXDEV); O(chunk) memory instead of full in-memory join.
- Router renames temp → final UUID PDF **before** `create_ticket`; duplicate hash unlinks the loser's file; DB/413/400 failure paths unlink temps/finals. Background orphan sweeper parked.
- Upload tests assert filesystem state: dup upload leaves exactly one `.pdf` and empty `.tmp`.

Ground every decision in what the repo actually is. The 4Geeks spec is a floor/guide and minimum requirement, not a ceiling — don't take it too literally. Exceed it where best practices serve the repo; build genuinely like a professional/production engineer, not to pass the grader.

## Log / secret redaction — `fix/log-secret-redaction`

**Status:** Implemented (reset log redaction; path-only 500 + request_id; slice rfp/worker env allowlists).

**What closed:**

- Forgot-password email-send failure: stable `password_reset_email_failed` log with request_id; no traceback/token/reset URL.
- auth + rfp: global Exception handler logs path + request_id only; JSON 500 envelope.
- request_id stored on `request.state` in RequestIdAccessLogMiddleware (auth + rfp).
- docker-compose.slice.yml: rfp + rfp-worker explicit env allowlists; JWT_PRIVATE_KEY no longer injected into rfp/worker. auth env_file left unchanged.

Ground every decision in what the repo actually is. The 4Geeks spec is a floor/guide and minimum requirement, not a ceiling — don't take it too literally. Exceed it where best practices serve the repo; build genuinely like a professional/production engineer, not to pass the grader.

## Agent timeouts + guardrail rather gate — `fix/agent-timeouts-guardrail`

**Status:** Implemented (PR-B: guardrail rather precedence; agent→MCP + Qdrant timeouts).

**What closed:**

- Guardrail: "I'd rather not store it" no longer misclassified as edit (was live confirmation-gate bypass writing garbage memory, not just mis-log).
- Agent→MCP: `get_tools` + `ainvoke` bounded by `MCP_AGENT_TIMEOUT_SECONDS` (default 15s); structured `TicketLookupResult` on timeout.
- Qdrant: `QdrantClient` constructed with `timeout=QDRANT_TIMEOUT_SECONDS` (default 30s).

Ground every decision in what the repo actually is. The 4Geeks spec is a floor/guide and minimum requirement, not a ceiling — don't take it too literally. Exceed it where best practices serve the repo; build genuinely like a professional/production engineer, not to pass the grader.

## C1 reject→regen evaluator parity

**Status:** Implemented (driver-side `evaluate_all` on regen persist; tests rewritten; no checkpoint wipe).

**What closed:** P3 reject→regen previously regenerated `draft_content` but `_persist_regen_section` merged into the prior evaluation without recomputing pass flags (stale `overall_pass` / `compliance.pass`). Fix: after regen, reload `key_aspects` from the DB row (null-safe coerce), call `evaluate_all` on the new draft with metadata `budget_range`, overwrite draft-derived eval fields in the same atomic `update_department_section`, preserve `interrupt_id` / `arbitration` / numbers / bounded `trace` / feedback stamps. Single-shot HITL (no P2 auto-retry loop). Graph nodes/edges unchanged → no `rfp_checkpoint` wipe.

Ground every decision in what the repo actually is. The 4Geeks spec is a floor/guide and minimum requirement, not a ceiling — don't take it too literally. Exceed it where best practices serve the repo; build genuinely like a professional/production engineer, not to pass the grader.

## Readiness probes — `fix/readiness-probes`

**Status:** Implemented (auth JWT sign/verify readyz; RFP generation config gate; backoffice waits for rfp-worker).

**What closed:**

- Auth `/readyz` now fails with **503** when JWT keys are missing or unusable (bounded round-trip; `/livez` unchanged).
- RFP `/readyz` checks generation tier config when `RFP_REQUIRE_GENERATION_CONFIG=1` (slice Compose).
- `backoffice` `depends_on` includes `rfp-worker: service_healthy`.

Ground every decision in what the repo actually is. The 4Geeks spec is a floor/guide and minimum requirement, not a ceiling — don't take it too literally. Exceed it where best practices serve the repo; build genuinely like a professional/production engineer, not to pass the grader.

## Proxy rate-limit identity — `fix/rate-limit-proxy-client`

**Status:** Implemented (shared `brasaland-proxy-trust` key_func; slice TRUSTED_PROXY_CIDRS).

**What closed:**

- SlowAPI limiters honor `X-Forwarded-For` only from configured trusted proxy peers.
- Spoofed forwarded headers from untrusted peers fall back to the TCP peer address.
- Slice Compose sets `TRUSTED_PROXY_CIDRS` on auth and rfp.

Ground every decision in what the repo actually is. The 4Geeks spec is a floor/guide and minimum requirement, not a ceiling — don't take it too literally. Exceed it where best practices serve the repo; build genuinely like a professional/production engineer, not to pass the grader.

## Non-root Docker images — `chore/non-root-knowledge-reporting-images`

**Status:** Implemented (knowledge + reporting `USER app`; Qdrant image pinned).

**What closed:**

- Knowledge and reporting runtime images match the in-slice non-root pattern (uid/gid 1000).
- Full-stack `docker-compose.yml` pins `qdrant/qdrant:v1.12.5` (out of slice; image hygiene only).

Ground every decision in what the repo actually is. The 4Geeks spec is a floor/guide and minimum requirement, not a ceiling — don't take it too literally. Exceed it where best practices serve the repo; build genuinely like a professional/production engineer, not to pass the grader.

## Stale docs and dead links — `docs/readme-counts-and-context-links`

**Status:** Implemented (README Expect counts refreshed; dead Spanish CONTEXT links removed).

**What closed:**

- `tests/pipelines/README.md` and `uis/backoffice/README.md` Expect counts match collected/vitest totals.
- Removed broken `./CONTEXT-brasaland*.es.md` links; hygiene tests guard against regressions.

Ground every decision in what the repo actually is. The 4Geeks spec is a floor/guide and minimum requirement, not a ceiling — don't take it too literally. Exceed it where best practices serve the repo; build genuinely like a professional/production engineer, not to pass the grader.

## Backoffice route guards — `fix/backoffice-dashboard-auth-guard`

**Status:** Implemented (`/` and `/locations` wrapped with `InventoryAuthGuard`).

**What closed:**

- Unauthenticated visits to dashboard and locations redirect to `/login` (same guard as `/rfp` and `/account/profile`).
- RTL tests cover missing token, expired token, and valid-token render paths.

Ground every decision in what the repo actually is. The 4Geeks spec is a floor/guide and minimum requirement, not a ceiling — don't take it too literally. Exceed it where best practices serve the repo; build genuinely like a professional/production engineer, not to pass the grader.

