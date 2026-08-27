# Agent workflow standards

## Memory-bank read-first

Before touching any file, read these in order:

1. `memory-bank/projectbrief.md`
2. `memory-bank/techContext.md`
3. `memory-bank/progress.md`

## Mandatory pre-commit (4 steps)

Complete all four steps before every commit:

1. Run `npx prettier --check` on every file you modified.
2. Run `npm run build --workspace <affected-workspace>` and confirm zero errors (skip when no workspace application code changed).
3. Run `npm run test --workspace @brasaland/operations-toolkit` and confirm toolkit tests pass — Canonical toolkit tests: [../../apps/operations-toolkit/README.md](../../apps/operations-toolkit/README.md).
4. Run `git diff --stat` and confirm no out-of-scope paths and no `.env.local`.

## Commits and attribution

- The **user types every commit**. Agents stage and prepare; they do not create commits unless the user explicitly asks.
- Commits follow Conventional Commits with workspace scopes (for example, `feat(public-website): ...`).
- No Co-Authored-By trailers in any commit.
- No "Generated with" or "Created by AI" comments in any file.
- No AI tool credited anywhere in code, docs, READMEs, or commit messages.
- Sole author: Settar Mengli <263843543+Settar-Mengli@users.noreply.github.com>.

## Review-chunk execution

- Limit each agent run to **2–3 phases** of work.
- Stage the chunk's files when ready; **do not commit** unless the user explicitly asks.
- After every chunk, produce an After-You-Finish report (files touched, commands run, git status, confirmation nothing was committed, warnings).
- Before any commit, cross-read `git status` against the reported files table and reconcile differences.
- After every Agent execution of an **amended** plan, a **read-only audit** must verify each amendment specifically — agents can silently drop amendments while reporting success.

## Git and branch discipline

- Use **branch-per-PR** and **one logical change per branch**.
- Always branch off freshly pulled `main`. Verify clean-off-main with two checks:
  - `git log --oneline -1` on the new branch
  - `git log --oneline -1 origin/main`
  - Confirm they match (or the branch tip is an intentional fast-forward from that `main`) before starting work.
- Run repo-scoped git commands from the **repo root**, never from a service subdirectory.
- Verify every PR merge in the terminal with `git pull` + `git log` — never by assumption.
- For graded or course work, read the spec's **How-to-Submit** section before creating any PR (PR titles may be mandated).

## Python test invocation

Run `uv run pytest` from inside the service or package directory (for example, `services/auth` or `packages/shared`). Running pytest from the monorepo root causes `ImportPathMismatchError`.

## PowerShell constraints

- Do not chain shell commands with the `&&` operator in PowerShell.
- When a CLI HTTP client is required, invoke `curl.exe` explicitly rather than the PowerShell `curl` alias.
- Delete files with `del` one path at a time.

## Production-touching steps

The operator personally runs all production-touching steps (deployments, secret rotation, live database mutations, RLS enablement against shared projects). Agents may propose exact commands; they must not execute production-touching steps unless the operator explicitly asks.

## Ops scripts

- Idempotent ops scripts live at repo-root `scripts/`.
- Always run with `--dry-run` before a real run.
- Target identifiers are hardcoded as module constants (not free-form CLI strings for table names).

## Schema and database change policy

One policy, two lanes. This is the sole home for schema discipline.

**Lane 1 — Tables/columns:** Change tables and columns through SQLModel metadata **and** Alembic revisions under [`data/`](../../data/) (single history / `public.alembic_version` for brasaland-m5). Generate and `upgrade` only against disposable Postgres; **stamp** live m5 when the live schema already matches models (baseline). `create_all` / `ensure_schema()` remain transitional bootstrap until retired — do not use them as the long-term DDL path for production schema changes.

**Lane 2 — RLS and one-off ops not yet expressed in migrations:** Change these only through idempotent scripts at repo-root `scripts/`. Operator-run. `--dry-run` before every real run. Target identifiers hardcoded as module constants. Indexes that belong on models (for example GIN on `telemetry_events.tags`) should be declared in SQLModel/`__table_args__` so Alembic owns them; legacy scripts may remain as idempotent bootstrap only.

**Never, in either lane:**

- Supabase dashboard SQL
- MCP mutation

MCP is **read-only verification** only.

**New-table obligation:** Any new table must be added to the `TABLES` constant in `scripts/enable_rls.py` (or the reporting setup script when in `reporting`), then re-run that script with `--dry-run` first and again for real. Also add the model to Alembic metadata imports in `data/alembic/env.py` and ship a revision.
