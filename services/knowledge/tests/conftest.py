"""Knowledge service test bootstrap."""

from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from brasaland_auth_verify.testing import generate_rsa_keypair

_PRIVATE_PEM, _PUBLIC_PEM = generate_rsa_keypair()

os.environ.setdefault("JWT_ALGORITHM", "RS256")

import config  # noqa: E402, F401 — data/ on sys.path; may load root .env

os.environ["JWT_PUBLIC_KEY"] = _PUBLIC_PEM

PRIVATE_PEM = _PRIVATE_PEM
PUBLIC_PEM = _PUBLIC_PEM


@pytest.fixture(autouse=True)
def disable_rate_limits() -> Generator[None, None, None]:
    from app import app

    limiter = getattr(app.state, "limiter", None)
    if limiter is None:
        yield
        return
    was = limiter.enabled
    limiter.enabled = False
    yield
    limiter.enabled = was
