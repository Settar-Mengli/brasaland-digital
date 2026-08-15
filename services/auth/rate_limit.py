"""Shared SlowAPI limiter for hot auth routes."""

from __future__ import annotations

import os

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Strictest bucket — login / register / refresh.
AUTH_RATE_LIMIT = os.environ.get("RATE_LIMIT_AUTH", "5/minute")
