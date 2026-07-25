# Brasaland Auth Service

JWT authentication and route protection service for the Brasaland backend.

## Architecture

The project follows **one pure security core, reused everywhere**. Hashing and JWT signing live in `auth/security.py`; JWT **verification** is delegated to the shared [`brasaland-auth-verify`](../../packages/auth-verify/) package (public key only). Neither layer imports FastAPI or a database—so the same functions can be imported by future services without pulling in HTTP or storage code. TinyDB persistence sits in `auth/db.py` and `auth/repository.py`. `auth/service.py` orchestrates registration and authentication: emails are normalized to lowercase before storage, passwords are hashed before they ever reach the repository, and duplicate-email rules run in the service layer. `app.py` is a thin FastAPI layer—Pydantic request/response models, route handlers, and the `get_current_user` guard.

**Design principle:** one security core, layered storage and orchestration, thin HTTP boundary.

Passwords are hashed with **bcrypt** via **passlib** and **never** stored in plain text. Access tokens are signed with RS256 (private key from `.env`) and verified on every protected request via `brasaland-auth-verify`.

```
services/auth/
├── auth/                        # Shared core package
│   ├── security.py              # bcrypt hashing + JWT sign; decode delegates to brasaland-auth-verify
│   ├── types.py                 # UserRecord, domain exceptions
│   ├── db.py                    # Lazy TinyDB singleton (see Ops notes)
│   ├── repository.py            # User CRUD + id assignment
│   ├── service.py               # Register, authenticate, password reset orchestration
│   └── email_sender.py          # Resend wrapper for reset emails
├── app.py                       # FastAPI routes + get_current_user
├── static/                      # Password-reset web UI (HTML, CSS)
│   ├── index.html
│   ├── forgot-password.html
│   ├── reset-password.html
│   └── styles.css
├── tests/                       # pytest (security + service + API)
├── data/                        # Runtime TinyDB (gitignored except .gitkeep)
├── .env.example                 # Environment variable template (tracked)
├── requirements.txt
└── README.md
```

## Setup (uv)

```powershell
cd services/auth
uv sync
uv run pytest
```

Copy the example environment file and set a real secret:

```powershell
copy .env.example .env
```

Requires **Python 3.13 via uv**.

### Environment variables

Copy from [`.env.example`](.env.example) and set real values locally in `.env` (gitignored). Never commit secrets.

| Variable | Purpose | Default / placeholder |
| --- | --- | --- |
| `JWT_PRIVATE_KEY` | RSA private key PEM (signs access and reset JWTs) | placeholder PEM in example |
| `JWT_PUBLIC_KEY` | RSA public key PEM (verifies JWTs) | placeholder PEM in example |
| `JWT_ALGORITHM` | JWT algorithm | `RS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL | `30` |
| `REFRESH_TOKEN_EXPIRE_MINUTES` | Refresh token TTL | `10080` (7 days) |
| `RESET_TOKEN_EXPIRE_MINUTES` | Password-reset token TTL | `30` |
| `RESEND_API_KEY` | [Resend](https://resend.com) API key for reset emails | `replace-with-your-resend-api-key` in example |
| `RESET_EMAIL_FROM` | Sender address for reset emails | `onboarding@resend.dev` (Resend sandbox) |
| `RESET_LINK_BASE_URL` | Base URL for links in email (no trailing slash) | `http://127.0.0.1:8002` |

Generate an RSA keypair for RS256 signing:

```powershell
openssl genpkey -algorithm RSA -pkcs8 -out private.pem -pkeyopt rsa_keygen_bits:2048
openssl rsa -in private.pem -pubout -out public.pem
```

Copy the PEM contents into `JWT_PRIVATE_KEY` and `JWT_PUBLIC_KEY` in `.env` (multiline quoted values are supported).

Start the server:

```powershell
uvicorn app:app --reload --port 8002
```

Interactive API docs: **http://127.0.0.1:8002/docs**

Password-reset pages (public):

- **http://127.0.0.1:8002/forgot-password** — request a reset link
- **http://127.0.0.1:8002/reset-password?token=…** — set a new password from the email link

Static assets are served at `/static/`.

**“Forgot password?” link:** This service has no `/login` HTML page yet (authentication is via **POST /auth/login** or Swagger). The product spec’s “Forgot your password?” link belongs on a **future frontend login page** (M-future). Until then, **`/forgot-password`** is the user-facing entry point. The reset UI includes “Back to sign in” links to `/login` for when that page exists elsewhere in the monorepo.

For login in Swagger, use **POST /auth/login** with `username` = email and `password` = password (`OAuth2PasswordRequestForm`).

## Web pages (public)

| Path | Description |
| --- | --- |
| `/` | Index with links for manual testing |
| `/forgot-password` | Form — POSTs to `/auth/forgot-password` |
| `/reset-password?token=…` | Form — reads token from query string, POSTs to `/auth/reset-password` |

## Password reset flow

1. User submits email on **`/forgot-password`** (or **POST /auth/forgot-password**).
2. **`request_password_reset`** looks up the normalized email. If missing, returns `None` (no error — enumeration protection).
3. If found, a short-lived JWT is created with `type: "password_reset"`, expiry from **`RESET_TOKEN_EXPIRE_MINUTES`**, and a **SHA-256 digest** of the raw token is stored on the user (`reset_token_hash`); the plaintext token is never persisted.
4. **`send_password_reset_email`** (Resend) sends a link: `{RESET_LINK_BASE_URL}/reset-password?token=…` with plain-text and HTML bodies.
5. **POST /auth/forgot-password** always returns the **same** `200` message whether the email exists, and even if Resend fails (errors are logged server-side only).
6. User opens the link, sets a new password on **`/reset-password`**, which calls **POST /auth/reset-password**.
7. **`reset_password`** verifies JWT signature/expiry, checks `type == "password_reset"`, compares SHA-256 digest (single-use), updates `hashed_password`, **clears** `reset_token_hash` / `reset_token_expires`, and **revokes all refresh tokens** for that user.
8. Reusing, tampering, or using a login token → **400** “Invalid or expired reset token”.

Passwords remain **bcrypt**-hashed; only reset **tokens** use SHA-256 for storage comparison (full JWT length, no bcrypt 72-byte truncation).

## Token model

Login and register return **two** RS256 JWTs:

| Token | Lifetime | Use | Storage |
| --- | --- | --- | --- |
| `access_token` | `ACCESS_TOKEN_EXPIRE_MINUTES` (default 30 min) | Bearer header for protected routes | Stateless |
| `refresh_token` | `REFRESH_TOKEN_EXPIRE_MINUTES` (default 7 days) | **POST /auth/refresh** to obtain a new pair | SHA-256 hash in TinyDB `refresh_tokens` table (stateful, revocable) |

Refresh tokens carry `type: "refresh"` and cannot be used as Bearer access tokens. Password-reset tokens carry `type: "password_reset"` and are likewise rejected as Bearer tokens. Only access tokens (no `type` claim) authenticate protected routes. Access tokens cannot be exchanged at `/auth/refresh`. Each refresh **rotates** the refresh token (old one is revoked). **POST /auth/logout** revokes the presented refresh token (idempotent `204`).

## API endpoints

| Method | Path | Auth | Success | Error responses | Description |
| --- | --- | --- | --- | --- | --- |
| `POST` | `/auth/forgot-password` | Public | `200` + message (always) | `422` validation | Request reset link; **enumeration-safe** — identical response whether email exists; email sent only when registered |
| `POST` | `/auth/reset-password` | Public | `200` + message | `400` invalid/expired/used token, `422` validation | Set new password with token from email; **single-use** |
| `POST` | `/auth/register` | Public | `201` + access + refresh tokens | `400` duplicate email, `422` validation | Sign up (`email` + `password` min 8; optional `name`/`phone`/`address`); returns token pair so the new user is logged in immediately |
| `POST` | `/auth/login` | Public | `200` + access + refresh tokens | `401` invalid credentials | Log in with email (`username`) and password |
| `POST` | `/auth/refresh` | Public | `200` + new token pair | `401` invalid/expired/revoked refresh | Exchange refresh token for rotated access + refresh tokens |
| `POST` | `/auth/logout` | Public | `204` empty body | `422` validation | Revoke refresh token (idempotent; unknown tokens still `204`) |
| `GET` | `/auth/me` | Protected | `200` + user JSON | `401` missing/invalid/expired token | Current user (`id`, `email`, flags, `created_at`, plus `name`/`phone`/`address`) |
| `GET` | `/profiles/me` | Protected | `200` + `{ email, name, phone, address }` | `401` | Current user profile fields only |
| `PUT` | `/profiles/me` | Protected | `200` + updated profile | `401`, `422` | Update **only** `name`/`phone`/`address` (owner from Bearer token; email/password/flags ignored if sent) |
| `POST` | `/users` | Protected | `201` + user JSON | `400` duplicate email, `401`, `422` | Create another user (any authenticated caller; no admin check — public signup is `/auth/register`) |
| `GET` | `/users` | Protected | `200` + list | `401` | List all users; email hidden unless requester is owner or admin |
| `GET` | `/users/{id}` | Protected | `200` + user JSON | `401`, `404` | Get one user by id |
| `PUT` | `/users/{id}` | Protected | `200` + user JSON | `400` duplicate email, `401`, `403` not owner/admin, `404` | Update email and/or password (only self or admin) |
| `DELETE` | `/users/{id}` | Protected | `204` empty body | `401`, `403` not owner/admin, `404` | Delete user (only self or admin) |

**Status code guide:** **401** — no token, invalid token, expired token, inactive user, or failed login. **403** — authenticated but not allowed to modify/delete another user. **400** — duplicate email, or invalid/expired/used reset token. **404** — user id not found.

## Privacy and security

- **`hashed_password` never appears in any API response** — only safe fields via `UserResponse`.
- **Email privacy:** when listing or viewing other users, email is omitted unless the requester is that user or an admin.
- **`.env` is gitignored** — copy from `.env.example`; never commit real secrets.
- **Protect by default:** public API routes are `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/forgot-password`, and `/auth/reset-password`; HTML pages at `/`, `/forgot-password`, and `/reset-password` are also public. All `/users` routes and `/auth/me` require a valid Bearer **access** token.

## Verification

From `services/auth/`:

```powershell
uv run pytest
```

Canonical auth tests: [TESTING.md](TESTING.md). Coverage gate **70%** on the `auth/` package.

**Manual smoke check (auth):** register with **POST /auth/register** (`email` + `password` min 8 chars), copy `access_token` from the response, open **/docs**, click **Authorize**, paste the token, then call **GET /auth/me** — expect **200** with your email. Call **GET /auth/me** again without authorizing — expect **401**.

**Manual smoke check (password reset):** open **/forgot-password**, submit a registered email, confirm the generic confirmation message; use the link from email (or capture token in dev) at **/reset-password?token=…**, set a new password, then **POST /auth/login** with the new password.

## Password reset — review evidence

A live end-to-end test was performed: a real reset email was delivered via Resend to a real inbox, and the new password was set successfully through the `/reset-password` page.

The reset flow sends an email containing a single-use tokenized link (not shown here).

![New password set successfully via /reset-password](https://github.com/Settar-Mengli/brasaland-digital/blob/main/docs/screenshots/password-reset-success.png?raw=true)

_New password set successfully via /reset-password_

## Ops notes

- **Port / Ops:** Canonical ports: [../../docs/standards/project-context.md](../../docs/standards/project-context.md#port-assignments).
- **Single worker:** TinyDB is a per-process singleton (`db.py`). Use one uvicorn worker unless every worker shares the same JSON path.
- **`AUTH_DB_PATH`:** Override for the JSON file path — **tests and local tooling only**. Default is `data/users.json` (gitignored at runtime).
- **Environment loading:** `auth/security.py` loads `services/auth/.env` via `python-dotenv` on import so JWT settings are available whether you start via uvicorn or import the core directly.
