# Coding standards

## TypeScript

### Rules

1. Strict mode must be enabled in every tsconfig.json (strict: true)
2. No any type — use unknown and narrow with type guards
3. No ! non-null assertions — use explicit null checks or optional chaining
4. No loose as casts — only inside documented type guards
5. snake_case for types that map to API wire format
6. camelCase for internal application types
7. import type for all type-only imports
8. JSDoc required on every exported function and interface
9. Record<Union, string> for exhaustive label maps
10. Discriminated unions preferred over optional fields for error states

### Workspace defaults (`uis/*`)

- TypeScript strict mode everywhere in `uis/*`
- No `any`, no `!` non-null assertions
- Server Components by default; `'use client'` only when required

### Accessibility

- `aria-labelledby` on every section
- `scope="col"` on `th`
- `role="status"` for pending states
- `role="alert"` for errors

### Date formatting

- Lists: `Intl.DateTimeFormat('en-US', { dateStyle: 'medium' })`
- Detail views: add `timeStyle: 'short'` (same locale)
- Instantiate formatters at **module level** (not inside render loops)

### Acceptance Criteria

- `tsc --noEmit` passes with zero errors
- No ESLint disable comments suppressing type errors

## Python

### Toolchain

- **uv** is the primary toolchain (not ad-hoc `venv` + `pip` as the documented setup path).
- Prefer `uv run --python 3.13` for repo-root ops scripts.
- Run package commands from the service or package directory via `uv run …`.

### Project layout

- `pyproject.toml` is the source of truth for dependencies and tool config; `uv.lock` locks the resolved set. Install with `uv sync --python 3.13`. There are no pip `requirements.txt` export files.
- Service apps typically use `[tool.uv] package = false`.
- Path dependencies on monorepo packages use `[tool.uv.sources]` (editable path to `packages/*`).

### Dependencies and tests

- Put test and coverage tools in `[dependency-groups] dev`.
- Run tests with `uv run pytest` **from inside** the service or package directory (see [agent-workflow.md](./agent-workflow.md#python-test-invocation)).
- Honor coverage gates where configured (example: `services/auth` uses `fail_under = 70` on the `auth/` package). Universal thresholds are not invented here — use each package's `pyproject.toml`.

### Ruff baseline ratchet

The root [`ruff.toml`](../../ruff.toml) is the lint source of truth. Ruff is pinned in the
`data/` development dependency group, and the `Ruff baseline ratchet` CI job runs this command
from the repository root:

```powershell
uv run --directory data --locked --only-group dev --python 3.13 python ../scripts/check_ruff_baseline.py
```

The checker runs `ruff check` over `data/`, `tests/pipelines/`, the twelve Python projects in the
CI test matrix, and the Python scripts exercised by or implementing the CI checks. Ruff's JSON
diagnostics are compared with [`.ruff-baseline.json`](../../.ruff-baseline.json) using a stable
path/rule/message/source-line fingerprint plus a count for duplicate fingerprints. The recorded
225 violations are tracked debt: a missing baseline diagnostic is allowed, but any unmatched new
diagnostic fails CI.

After legitimately fixing one or more recorded violations, confirm the gate passes and then
regenerate the baseline with the subtraction-only update command:

```powershell
uv run --directory data --locked --only-group dev --python 3.13 python ../scripts/check_ruff_baseline.py --update-baseline
```

The update refuses to write if Ruff reports any new diagnostic. Review the baseline diff before
committing it. `--bootstrap-baseline` is reserved for an explicitly reviewed initial baseline or
an authorized Ruff version, rule, or path-scope migration; it refuses to overwrite an existing
baseline.

### Test isolation

- Prefer an in-memory SQLite (or equivalent isolated engine) pattern for SQLModel services so tests do not touch shared databases.
- TinyDB-backed services may use per-test temporary DB files (see `services/auth/TESTING.md`) — do not force SQLite onto those suites.

### Environment files

- Copy `.env.example` to `.env` (or `.env.local` for Next.js) for local secrets.
- Never commit real secrets.
- Never write secret material into tracked files.
