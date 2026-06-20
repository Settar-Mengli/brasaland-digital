# Brasaland Auth Service

JWT authentication and route protection service for the Brasaland backend.

## Architecture

The project follows **one pure security core, reused everywhere**. Hashing, JWT signing, and verification live in `auth/security.py` with no FastAPI and no database—so the same functions can be imported by future services (for example inventory or M5) without pulling in HTTP or storage code. TinyDB persistence sits in `auth/db.py` and `auth/repository.py`. `auth/service.py` orchestrates registration and authentication: emails are normalized to lowercase before storage, passwords are hashed before they ever reach the repository, and duplicate-email rules run in the service layer. `app.py` is a thin FastAPI layer—Pydantic request/response models, route handlers, and the `get_current_user` guard.

**Design principle:** one security core, layered storage and orchestration, thin HTTP boundary.

Passwords are hashed with **bcrypt** via **passlib** and **never** stored in plain text. Access tokens are signed with a secret loaded from `.env` and verified on every protected request.

```
services/auth/
├── auth/                        # Shared core package
│   ├── security.py              # bcrypt hashing + JWT create/decode (pure functions)
│   ├── types.py                 # UserRecord, domain exceptions
│   ├── db.py                    # Lazy TinyDB singleton (see Ops notes)
│   ├── repository.py            # User CRUD + id assignment
│   └── service.py               # Register, authenticate, list/update/delete users
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

## Setup (Windows + venv)

```powershell
cd services/auth
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copy the example environment file and set a real secret:

```powershell
copy .env.example .env
```

Generate a strong `JWT_SECRET_KEY` and paste it into `.env`:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Requires **Python 3.11+**. Optional variables in `.env.example`: `JWT_ALGORITHM` (default `HS256`), `ACCESS_TOKEN_EXPIRE_MINUTES` (default `30`).

Start the server:

```powershell
uvicorn app:app --reload --port 8002
```

Interactive API docs: **http://127.0.0.1:8002/docs**

Password-reset pages (public):

- **http://127.0.0.1:8002/forgot-password** — request a reset link
- **http://127.0.0.1:8002/reset-password?token=…** — set a new password from the email link

Static assets are served at `/static/`.

**Login page note:** This service has no `/login` HTML page yet (authentication is via **POST /auth/login** or Swagger). The spec’s “Forgot your password?” link belongs on a future frontend login screen (M-future); until then, **`/forgot-password`** is the user-facing entry point for password reset. The reset UI includes “Back to sign in” links to `/login` for when that page exists elsewhere in the monorepo.

For login in Swagger, use **POST /auth/login** with `username` = email and `password` = password (`OAuth2PasswordRequestForm`).

## API endpoints

| Method | Path | Auth | Success | Error responses | Description |
| --- | --- | --- | --- | --- | --- |
| `POST` | `/auth/forgot-password` | Public | `200` + message | — | Request reset link (same response whether email exists) |
| `POST` | `/auth/reset-password` | Public | `200` + message | `400` invalid/expired token | Complete reset with token from email |
| `POST` | `/auth/register` | Public | `201` + token | `400` duplicate email, `422` validation | Sign up; returns JWT so the new user is logged in immediately |
| `POST` | `/auth/login` | Public | `200` + token | `401` invalid credentials | Log in with email (`username`) and password |
| `GET` | `/auth/me` | Protected | `200` + user JSON | `401` missing/invalid/expired token | Current user profile (email always shown for self) |
| `POST` | `/users` | Protected | `201` + user JSON | `400` duplicate email, `401`, `422` | Create another user (admin/ops path; public signup is `/auth/register`) |
| `GET` | `/users` | Protected | `200` + list | `401` | List all users; email hidden unless requester is owner or admin |
| `GET` | `/users/{id}` | Protected | `200` + user JSON | `401`, `404` | Get one user by id |
| `PUT` | `/users/{id}` | Protected | `200` + user JSON | `400` duplicate email, `401`, `403` not owner/admin, `404` | Update email and/or password (only self or admin) |
| `DELETE` | `/users/{id}` | Protected | `204` empty body | `401`, `403` not owner/admin, `404` | Delete user (only self or admin) |

**Status code guide:** **401** — no token, invalid token, expired token, inactive user, or failed login. **403** — authenticated but not allowed to modify/delete another user. **400** — email already registered. **404** — user id not found.

## Privacy and security

- **`hashed_password` never appears in any API response** — only safe fields via `UserResponse`.
- **Email privacy:** when listing or viewing other users, email is omitted unless the requester is that user or an admin.
- **`.env` is gitignored** — copy from `.env.example`; never commit real secrets.
- **Protect by default:** only `/auth/register`, `/auth/login`, `/auth/forgot-password`, and `/auth/reset-password` are public API routes; HTML pages at `/`, `/forgot-password`, and `/reset-password` are also public. All `/users` routes and `/auth/me` require a valid Bearer token.

## Verification

From `services/auth/` with the venv active:

```powershell
pytest
```

**35 tests** cover password hashing, JWT round-trip and tamper/expiry rejection, user service orchestration, email sender, password-reset API routes, and existing FastAPI routes via `TestClient`.

**Manual smoke check:** register with **POST /auth/register** (`email` + `password` min 8 chars), copy `access_token` from the response, open **/docs**, click **Authorize**, paste the token, then call **GET /auth/me** — expect **200** with your email. Call **GET /auth/me** again without authorizing — expect **401**.

## Ops notes

- **Port:** **8002** (incident-analysis uses 8000, supplier-directory uses 8001).
- **Single worker:** TinyDB is a per-process singleton (`db.py`). Use one uvicorn worker unless every worker shares the same JSON path.
- **`AUTH_DB_PATH`:** Override for the JSON file path — **tests and local tooling only**. Default is `data/users.json` (gitignored at runtime).
- **Environment loading:** `auth/security.py` loads `services/auth/.env` via `python-dotenv` on import so JWT settings are available whether you start via uvicorn or import the core directly.
