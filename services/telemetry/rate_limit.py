"""Shared SlowAPI limiter for telemetry ingest."""

from __future__ import annotations

import os

from brasaland_proxy_trust import rate_limit_client_key
from slowapi import Limiter

limiter = Limiter(key_func=rate_limit_client_key)
INGEST_RATE_LIMIT = os.environ.get("RATE_LIMIT_TELEMETRY_INGEST", "60/minute")
