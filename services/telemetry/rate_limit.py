"""Shared SlowAPI limiter for telemetry ingest."""

from __future__ import annotations

import os

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
INGEST_RATE_LIMIT = os.environ.get("RATE_LIMIT_TELEMETRY_INGEST", "60/minute")
