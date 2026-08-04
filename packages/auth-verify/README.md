# brasaland-auth-verify

Verify-only RS256 JWT validation for Brasaland Python services. Decode and validate access tokens with the **public key only** — no signing, no password hashing, no FastAPI or database code.

## Public API

```python
from brasaland_auth_verify import TokenError, verify_token

claims = verify_token(token)  # dict with sub, user_id, exp, etc.
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

Expect **5** passed.
