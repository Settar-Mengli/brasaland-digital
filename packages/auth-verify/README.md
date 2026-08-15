# brasaland-auth-verify

Verify-only RS256 JWT validation for Brasaland Python services. Decode and validate access tokens with the **public key only** — no signing, no password hashing, no database code. FastAPI dependencies live in `brasaland_auth_verify.deps` so verify-only callers can keep importing `verify_token` without touching the HTTP layer.

## Public API

```python
from brasaland_auth_verify import TokenError, ensure_jwt_configured, verify_token
from brasaland_auth_verify.deps import get_current_user_uuid, require_admin

claims = verify_token(token)  # dict with sub, user_id, exp, is_admin, etc.
```

| Function | Input | Output | Error |
| --- | --- | --- | --- |
| `verify_token(token)` | JWT string | claims `dict` | `TokenError` if invalid/expired; `ValueError` if `JWT_PUBLIC_KEY` missing |

## Environment variables

| Variable | Purpose | Default |
| --- | --- | --- |
| `JWT_PUBLIC_KEY` | RSA public key PEM | required |
| `JWT_ALGORITHM` | JWT algorithm | `RS256` |

The package does **not** call `load_dotenv`. Callers (e.g. `services/auth/`) are responsible for populating env before calling `verify_token`.

## Install (editable, from a consuming service)

Add to the service `pyproject.toml`:

```toml
dependencies = ["brasaland-auth-verify"]

[tool.uv.sources]
brasaland-auth-verify = { path = "../../packages/auth-verify", editable = true }
```

Then sync from the consuming service:

```powershell
uv sync --python 3.13
```

## Testing

```powershell
cd packages/auth-verify
uv sync --python 3.13
uv run pytest
```

Expect **18** passed.
