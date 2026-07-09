# Brasaland Digital — M4 Progress

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
Milestone 4 complete — both Vercel deployments live, PR merged, README updated.

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
