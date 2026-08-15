"""Shared SlowAPI limiter for RFP upload."""

from __future__ import annotations

import os

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
RFP_UPLOAD_RATE_LIMIT = os.environ.get("RATE_LIMIT_RFP_UPLOAD", "10/minute")
