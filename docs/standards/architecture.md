# Architecture standards

## Service layout

- **One service, one folder** under `services/` (FastAPI apps and related Python utilities).
- npm UI workspaces live under `uis/` and `apps/`.
- Shared pure cores live under `packages/` (for example `packages/shared`, `packages/auth-verify`).

## Frontend-consumes-backend

- Next.js UIs call backends through **same-origin rewrites** (configured in `next.config.ts`) so the browser does not need cross-origin API allowlists for local/dev proxy flows.
- All domain HTTP calls go through a single `lib/<domain>.ts` module (for example `lib/inventory.ts`, `lib/incidents.ts`). Components must not call `fetch` directly.
- Parse failures at the boundary with `parseApiError` / `parseApiErrorResponse`.
- Data views expose **three UI states**: loading, error, and success.
- Vitest covers `lib/` helpers only (unit tests at the client boundary), not full end-to-end browser flows.

## Shared pure-core packages

- `packages/shared` holds pure validation and lifecycle rules with **no framework or I/O dependencies** (no FastAPI, no database drivers, no HTTP clients).
- Consumers install via uv path / editable sources; do not copy validation logic into service layers.

## Path A storage migration

When replacing a persistence backend (for example TinyDB → SQLModel/PostgreSQL):

1. Swap repository **internals** while keeping the same public function signatures (Path A).
2. Leave `service.py` and `app.py` unchanged except where signatures truly must change.
3. Leave pure shared packages untouched (validation/lifecycle only — no database code).
4. Create/evolve tables via SQLModel metadata plus the Alembic baseline/history under `data/` (see [Schema and database change policy](./agent-workflow.md#schema-and-database-change-policy)); lazy `ensure_schema()` / `create_all` remain transitional bootstrap only.

## Secrets playbook

1. Confirm `.env` (and similar secret files) are gitignored — run `git status` and verify they are **not** listed as new tracked files **before** generating or writing secrets.
2. Generate RSA key material with the repo-standard openssl one-liner pair (documented in `services/auth/README.md`):

   ```text
   openssl genpkey -algorithm RSA -pkcs8 -out private.pem -pkeyopt rsa_keygen_bits:2048
   openssl rsa -in private.pem -pubout -out public.pem
   ```

3. Place PEMs (or other secrets) only in local `.env` / operator secret stores — never in commits, chats as durable storage, or tracked examples beyond placeholders.
4. Rotate anything pasted outside `.env`.
5. JWT **private** keys stay in the signing service (`services/auth`). Verifying services and `packages/auth-verify` receive the **public** key only.

## Supabase

Schema, RLS, indexes, and new-table obligations: see [agent-workflow.md — Schema and database change policy](./agent-workflow.md#schema-and-database-change-policy).

Topology note (not a second policy): the shared project is **brasaland-m5**; inventory, incident-manager, and related services share `DATABASE_URL` against that project.
