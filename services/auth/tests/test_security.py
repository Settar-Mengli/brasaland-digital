from __future__ import annotations

import pytest

from auth.security import (
    TokenError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password_output_differs_from_plain_text() -> None:
    plain = "brasaland-ops-password"
    hashed = hash_password(plain)

    assert hashed != plain
    assert hashed.startswith("$2")


def test_verify_password_accepts_correct_and_rejects_wrong() -> None:
    plain = "correct-horse-battery-staple"
    hashed = hash_password(plain)

    assert verify_password(plain, hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_create_and_decode_access_token_round_trip() -> None:
    payload = {"user_id": 42, "sub": "ops@brasaland.com"}
    token = create_access_token(payload)
    decoded = decode_access_token(token)

    assert decoded["user_id"] == 42
    assert decoded["sub"] == "ops@brasaland.com"
    assert "exp" in decoded


def test_decode_access_token_rejects_tampered_payload() -> None:
    token = create_access_token({"user_id": 7})
    header, payload_segment, signature = token.split(".")
    tampered_char = "a" if payload_segment[-1] != "a" else "b"
    tampered_token = ".".join(
        [header, payload_segment[:-1] + tampered_char, signature]
    )

    with pytest.raises(TokenError):
        decode_access_token(tampered_token)


def test_decode_access_token_rejects_expired_token() -> None:
    token = create_access_token({"user_id": 99}, expires_minutes=-1)

    with pytest.raises(TokenError):
        decode_access_token(token)
