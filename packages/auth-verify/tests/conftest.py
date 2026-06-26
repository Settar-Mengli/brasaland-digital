from __future__ import annotations

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PRIVATE_PEM = _key.private_bytes(
    serialization.Encoding.PEM,
    serialization.PrivateFormat.PKCS8,
    serialization.NoEncryption(),
).decode()
PUBLIC_PEM = _key.public_key().public_bytes(
    serialization.Encoding.PEM,
    serialization.PublicFormat.SubjectPublicKeyInfo,
).decode()

_other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTHER_PUBLIC_PEM = _other_key.public_key().public_bytes(
    serialization.Encoding.PEM,
    serialization.PublicFormat.SubjectPublicKeyInfo,
).decode()


@pytest.fixture(autouse=True)
def jwt_public_key_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_PUBLIC_KEY", PUBLIC_PEM)
    monkeypatch.setenv("JWT_ALGORITHM", "RS256")
