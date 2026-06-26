from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from brasaland_auth_verify import TokenError, verify_token
from tests.conftest import OTHER_PUBLIC_PEM, PRIVATE_PEM


def _sign_token(
    payload: dict,
    *,
    private_pem: str = PRIVATE_PEM,
    algorithm: str = "RS256",
) -> str:
    return jwt.encode(payload, private_pem, algorithm=algorithm)


def test_verify_token_round_trip_returns_claims() -> None:
    payload = {"user_id": 42, "sub": "ops@brasaland.com"}
    expire_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    signed_payload = {**payload, "exp": int(expire_at.timestamp())}
    token = _sign_token(signed_payload)

    decoded = verify_token(token)

    assert decoded["user_id"] == 42
    assert decoded["sub"] == "ops@brasaland.com"
    assert "exp" in decoded


def test_verify_token_rejects_expired_token() -> None:
    expire_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    token = _sign_token({"user_id": 99, "exp": int(expire_at.timestamp())})

    with pytest.raises(TokenError):
        verify_token(token)


def test_verify_token_rejects_tampered_payload() -> None:
    token = _sign_token({"user_id": 7, "exp": int((datetime.now(timezone.utc) + timedelta(minutes=30)).timestamp())})
    header, payload_segment, signature = token.split(".")
    tampered_char = "a" if payload_segment[-1] != "a" else "b"
    tampered_token = ".".join(
        [header, payload_segment[:-1] + tampered_char, signature],
    )

    with pytest.raises(TokenError):
        verify_token(tampered_token)


def test_verify_token_rejects_wrong_public_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    token = _sign_token(
        {
            "user_id": 3,
            "exp": int((datetime.now(timezone.utc) + timedelta(minutes=30)).timestamp()),
        },
    )
    monkeypatch.setenv("JWT_PUBLIC_KEY", OTHER_PUBLIC_PEM)

    with pytest.raises(TokenError):
        verify_token(token)


def test_verify_token_requires_public_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JWT_PUBLIC_KEY", raising=False)

    with pytest.raises(ValueError, match="JWT_PUBLIC_KEY"):
        verify_token("not-a-real-token")
