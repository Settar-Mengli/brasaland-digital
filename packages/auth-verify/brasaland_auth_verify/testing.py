"""Token-minting helpers for test suites of services that verify JWTs.

Not imported by any runtime code path; kept in the package so each service
test suite does not re-implement RSA key generation and claim shaping.
"""

from __future__ import annotations

import time
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwt


def generate_rsa_keypair() -> tuple[str, str]:
    """Return a fresh ``(private_pem, public_pem)`` RSA-2048 pair."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    public_pem = key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return private_pem, public_pem


def mint_access_token(
    private_pem: str,
    *,
    user_id: int = 1,
    is_admin: bool = False,
    expires_in_seconds: int = 900,
    token_type: str | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Sign an RS256 token shaped like services/auth access tokens."""
    now = int(time.time())
    claims: dict[str, Any] = {
        "sub": str(user_id),
        "user_id": user_id,
        "is_admin": is_admin,
        "iat": now,
        "exp": now + expires_in_seconds,
    }
    if token_type is not None:
        claims["type"] = token_type
    if extra_claims:
        claims.update(extra_claims)
    return jwt.encode(claims, private_pem, algorithm="RS256")
