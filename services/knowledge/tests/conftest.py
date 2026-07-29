"""Knowledge service test bootstrap."""

from __future__ import annotations

import os

# Avoid JWT env requirement during import of dependencies in some paths.
os.environ.setdefault("JWT_ALGORITHM", "RS256")

import config  # noqa: E402, F401 — data/ on sys.path
