"""Shared SlowAPI limiter for incident-analysis."""

from __future__ import annotations

import os

from brasaland_proxy_trust import rate_limit_client_key
from slowapi import Limiter

limiter = Limiter(key_func=rate_limit_client_key)
ANALYZE_RATE_LIMIT = os.environ.get("RATE_LIMIT_ANALYZE", "10/minute")
