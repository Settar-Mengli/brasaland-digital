# Testing — Brasaland Auth Service

## Purpose and scope

This document describes the pytest suite for `services/auth/`. The testing project adds coverage tooling, uv-based dependency management, and additional tests. **No auth business logic was changed** as part of this work — tests assert behavior as implemented.

## How to run

From `services/auth/`:

```powershell
uv run pytest
```

With an explicit coverage report:

```powershell
uv run pytest --cov=auth --cov-report=term-missing
```

All tests must pass and coverage on the `auth/` package must remain at or above **70%** (`fail_under = 70` in `pyproject.toml`).

## Toolchain

| Tool                             | Role                                                          |
| -------------------------------- | ------------------------------------------------------------- |
| [uv](https://docs.astral.sh/uv/) | Dependency resolution, virtualenv, and test runner entrypoint |
| pytest                           | Test framework                                                |
| pytest-cov                       | Coverage measurement and `fail_under` gate                    |
| httpx                            | HTTP client used by FastAPI `TestClient`                      |

Runtime dependencies live in `[project.dependencies]`; test tools live in `[dependency-groups] dev` inside `pyproject.toml`. Resolved versions are locked in `uv.lock`. Install with `uv sync --python 3.13`.

## Test architecture

Tests are organized in three layers:

1. **Pure unit** — `auth/security.py` hashing and JWT helpers; no database or HTTP.
2. **Service / repository** — `auth/service.py` and `auth/repository.py` orchestration with an isolated TinyDB file per test.
3. **API (TestClient)** — `app.py` routes, guards, RBAC, and HTTP status/message contracts.

### Isolation strategy

[`tests/conftest.py`](tests/conftest.py) provides two autouse fixtures:

- `isolated_auth_db` — sets `AUTH_DB_PATH` to a temporary JSON file and calls `reset_db()` before and after each test.
- `jwt_settings` — sets JWT and reset-token environment variables for deterministic token behavior.

Password-reset email delivery is never sent to Resend in tests. API tests monkeypatch `app_module.send_password_reset_email`; email-sender unit tests monkeypatch `resend.Emails.send`.

## Coverage

| Setting          | Value                                                                             |
| ---------------- | --------------------------------------------------------------------------------- |
| Measured package | `auth/` only (`security`, `service`, `repository`, `refresh_repository`, `db`, `email_sender`, `types`) |
| `app.py`         | Exercised by TestClient tests but **not** included in the coverage denominator    |
| Threshold        | `fail_under = 70`                                                                 |
| Current total    | **~96%** (369/383 statements)                                                     |

Per-file coverage (last run):

| Module                      | Coverage |
| --------------------------- | -------- |
| `auth/__init__.py`          | 100%     |
| `auth/db.py`                | 100%     |
| `auth/email_sender.py`      | 100%     |
| `auth/refresh_repository.py`| 95%      |
| `auth/repository.py`        | 100%     |
| `auth/security.py`          | 100%     |
| `auth/service.py`           | 94%      |
| `auth/types.py`             | 100%     |

Regenerate the report with `uv run pytest`.

## Test catalog

**110 tests** across 9 files.

### `tests/test_security.py` (8)

- Password hashing differs from plaintext; verify accepts/rejects.
- JWT create/decode round-trip; tampered and expired tokens raise `TokenError`.
- Missing `JWT_PRIVATE_KEY` raises `ValueError`.
- Default algorithm (RS256) and `ACCESS_TOKEN_EXPIRE_MINUTES` from env.

### `tests/test_db.py` (5)

- `_resolve_path` explicit argument, `AUTH_DB_PATH` env, and default `data/users.json`.
- `get_db` opens explicit paths and reopens when the path changes.
- `reset_db` when no connection is open.

### `tests/test_repository.py` (5)

- `get_user_by_id` / `get_user_by_email` return `None` for missing records.
- `update_user` returns `None` when the user does not exist.
- `delete_user` returns `False` when nothing is removed.
- `_next_id` starts at 1 on an empty table.

### `tests/test_user_service.py` (8)

- Registration stores bcrypt hash; rejects duplicate email.
- Email normalization on register and authenticate.
- Authenticate success and failure paths.
- Get, list, update, delete lifecycle.
- `update_user` not-found and duplicate-email-on-update errors.
- Email normalization on update.

### `tests/test_reset_service.py` (11)

- Reset token stored as SHA-256 hash; unknown email returns `None`.
- Full reset flow clears hash and updates password.
- Reused, expired, and login-token rejection.
- Token without `user_id`, deleted user, and hash mismatch rejection.
- Sub-only JWT `sub` claim accepted when hash matches.
- Distinct full tokens produce distinct hashes.

### `tests/test_email_sender.py` (4)

- Builds Resend payload and reset link correctly.
- Missing `RESEND_API_KEY`, `RESET_EMAIL_FROM`, or `RESET_LINK_BASE_URL` raises `RuntimeError`.

### `tests/test_refresh_service.py` (12)

- `issue_refresh_token` stores a hashed record; `issue_token_pair` returns distinct access and refresh tokens.
- `rotate_refresh_token` issues a new pair and revokes the old; rejects reuse, expired, access, garbage, and tampered tokens.
- `revoke_refresh_token` makes subsequent rotation fail.
- `resolve_active_user` rejects refresh tokens and accepts access tokens.
- Refresh token carries `type: "refresh"` claim.
- Password reset revokes the user's refresh tokens (H4).

### `tests/test_api.py` (40)

- Register + `/auth/me`; 401 without or with invalid token.
- Login success and wrong password.
- Self-registration gate: `POST /auth/register` returns 403 unless `AUTH_ALLOW_SELF_REGISTER` is true (tests enable it via an autouse fixture).
- RBAC: normal user cannot update/delete another user.
- `GET /users` is admin-only (403 for normal users; admin sees emails); `GET /users/{id}` is self-or-admin.
- `POST /users` is admin-only and can mint admins via `is_admin`; 401 without a token.
- Access tokens carry an `is_admin` claim.
- Bootstrap admin: seeded on startup only when the store is empty and both env vars are set; skipped otherwise.
- `is_admin` cannot be escalated via PUT.
- Duplicate-email update handling; `hashed_password` never in responses.
- Post-merge error constants: `EMAIL_ALREADY_REGISTERED`, `USER_NOT_FOUND`.
- Inactive user receives 401 on protected routes.
- Empty PUT body returns current user unchanged.
- Token with `sub`-only claim accepted by `/auth/me`.
- `/auth/refresh` returns a new working access token and rotates the refresh token.
- `/auth/refresh` rejects garbage and access tokens.
- Refresh and password-reset tokens are rejected as Bearer access tokens (H1).
- `/auth/logout` revokes the presented refresh token.
- Static pages `/`, `/forgot-password`, `/reset-password` return HTML.
- `GET /auth/profiles/me` returns email + name/phone/address for the authenticated user.
- `PUT /auth/profiles/me` updates and returns name/phone/address.
- `GET`/`PUT /auth/profiles/me` without a token return 401.
- `PUT /auth/profiles/me` ignores email, password, `is_admin`, and `is_active` in the body (no privilege escalation or email takeover).

### `tests/test_reset_api.py` (6)

- Forgot-password enumeration-safe generic message.
- Send failure still returns generic 200.
- Full forgot → reset → login flow.
- Invalid and reused reset tokens return 400.

## Known issues surfaced by tests

No auth business-logic bugs were found during this testing project. Tests document the following **non-blocking observations**:

1. **python-jose deprecation warnings** — `jose.jwt` uses `datetime.utcnow()`, which emits `DeprecationWarning` under Python 3.13 during token validation. Behavior is correct; library update deferred.
2. **`load_dotenv` at import** — `auth/security.py` and `auth/email_sender.py` load `.env` on module import. Tests rely on `monkeypatch.setenv` / `delenv` rather than a dedicated settings object. Not a defect; documented for future refactor scope.

## CI

CI runs this suite via the `uv-tests` matrix row `services/auth` in `.github/workflows/ci.yml`. See the root `README.md` for overall CI coverage.
