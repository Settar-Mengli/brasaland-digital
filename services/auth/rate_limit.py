"""Shared SlowAPI limiter for hot auth routes."""

from __future__ import annotations

import os

from brasaland_proxy_trust import rate_limit_client_key
from slowapi import Limiter

limiter = Limiter(key_func=rate_limit_client_key)

# Strictest bucket — login / register / refresh.
AUTH_RATE_LIMIT = os.environ.get("RATE_LIMIT_AUTH", "5/minute")
