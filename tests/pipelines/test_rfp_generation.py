"""Offline tests for RFP generation helper (mocked OpenAI; no network)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

_DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
_data_str = str(_DATA_ROOT)
if _data_str not in sys.path:
    sys.path.insert(0, _data_str)

from pipelines.rfp_intake import generation as gen


def test_clean_markdown_artifacts_strips_cid_glyphs() -> None:
    assert gen.clean_markdown_artifacts("Item (cid:127) next") == "Item - next"
    assert gen.clean_markdown_artifacts("(cid:12) gone") == " gone"
    assert gen.clean_markdown_artifacts("plain") == "plain"


def test_parse_json_object_fenced_bare_and_garbage() -> None:
    assert gen._parse_json_object('{"a": 1}') == {"a": 1}
    assert gen._parse_json_object('```json\n{"b": true}\n```') == {"b": True}
    with pytest.raises(ValueError):
        gen._parse_json_object("not json at all")
    with pytest.raises(ValueError):
        gen._parse_json_object("[1, 2, 3]")


def test_generate_json_parses_canned_completion(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEN_1_API_KEY", "test-key")
    monkeypatch.setenv("GEN_1_BASE_URL", "https://api.groq.com/openai/v1")
    monkeypatch.setenv("GEN_1_MODEL", "test-model")
    monkeypatch.delenv("GEN_2_API_KEY", raising=False)
    monkeypatch.delenv("GEN_3_API_KEY", raising=False)

    fake_message = MagicMock()
    fake_message.content = '```json\n{"ok": true, "n": 2}\n```'
    fake_completion = MagicMock()
    fake_completion.choices = [MagicMock(message=fake_message)]
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = fake_completion

    class FakeOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            assert kwargs["timeout"] == gen.RFP_GENERATION_TIMEOUT_SECONDS
            assert kwargs["max_retries"] == 0
            self._client = fake_client

        @property
        def chat(self) -> Any:
            return fake_client.chat

    monkeypatch.setattr("openai.OpenAI", FakeOpenAI)
    result = gen.generate_json("sys", "user", max_tokens=64)
    assert result == {"ok": True, "n": 2}


def test_generate_json_no_tiers_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    for i in (1, 2, 3):
        monkeypatch.delenv(f"GEN_{i}_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="no generation provider configured"):
        gen.generate_json("sys", "user")


def test_tier_skip_when_key_without_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEN_1_API_KEY", "orphan-key")
    monkeypatch.delenv("GEN_1_BASE_URL", raising=False)
    monkeypatch.delenv("GEN_1_MODEL", raising=False)
    monkeypatch.delenv("GEN_2_API_KEY", raising=False)
    monkeypatch.delenv("GEN_3_API_KEY", raising=False)
    assert gen._rfp_generation_tiers() == []
