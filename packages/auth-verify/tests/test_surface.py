"""Docs gating helpers."""

from __future__ import annotations

import pytest

from brasaland_auth_verify.surface import docs_exposed, fastapi_docs_kwargs


def test_docs_hidden_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EXPOSE_DOCS", raising=False)
    assert docs_exposed() is False
    assert fastapi_docs_kwargs() == {
        "docs_url": None,
        "redoc_url": None,
        "openapi_url": None,
    }


def test_docs_exposed_when_flagged(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EXPOSE_DOCS", "1")
    assert docs_exposed() is True
    assert fastapi_docs_kwargs() == {}
