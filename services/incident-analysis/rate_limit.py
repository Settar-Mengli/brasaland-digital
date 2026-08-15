"""Shared SlowAPI limiter for incident-analysis."""

from __future__ import annotations

import os

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
ANALYZE_RATE_LIMIT = os.environ.get("RATE_LIMIT_ANALYZE", "10/minute")
