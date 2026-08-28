# brasaland-proxy-trust

Trusted-proxy client IP resolution for Brasaland SlowAPI rate limiters.

## Usage

```python
from slowapi import Limiter
from brasaland_proxy_trust import rate_limit_client_key

limiter = Limiter(key_func=rate_limit_client_key)
```

## Environment

| Variable | Purpose |
| --- | --- |
| `TRUSTED_PROXY_IPS` | Comma-separated exact peer IPs that may supply `X-Forwarded-For` |
| `TRUSTED_PROXY_CIDRS` | Comma-separated CIDRs for trusted proxy peers (e.g. Docker bridge) |

When the immediate TCP peer is trusted, the leftmost `X-Forwarded-For` value becomes the rate-limit key. Untrusted peers cannot spoof another client by setting that header.

## Tests

```powershell
cd packages/proxy-trust
uv sync --python 3.13
uv run pytest
```
