"""Unit tests for pipelines.rag — mocked Qdrant, embed, and LLM (no downloads)."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from pipelines.rag import (
    SOURCE_DOCUMENTS,
    chunk_markdown,
    query,
    retrieve,
    setup,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CORPUS = REPO_ROOT / "docs" / "company-knowledge-base"


def test_chunk_markdown_at_least_three_per_doc() -> None:
    for stem in SOURCE_DOCUMENTS:
        text = (CORPUS / f"{stem}.md").read_text(encoding="utf-8")
        chunks = chunk_markdown(text, source_document=stem)
        assert len(chunks) >= 3
        for index, chunk in enumerate(chunks):
            assert chunk["company"] == "brasaland"
            assert chunk["source_document"] == stem
            assert chunk["language"] == "en"
            assert chunk["chunk_index"] == index
            assert isinstance(chunk["section"], str) and chunk["section"]
            assert isinstance(chunk["text"], str) and chunk["text"].strip()


def test_retrieve_filters_min_score_and_respects_k() -> None:
    fake_hits = [
        SimpleNamespace(
            score=0.9,
            payload={
                "text": "gold tier",
                "source_document": "loyalty-program",
                "section": "tiers",
            },
        ),
        SimpleNamespace(
            score=0.4,
            payload={
                "text": "noise",
                "source_document": "waste-protocol",
                "section": "x",
            },
        ),
        SimpleNamespace(
            score=0.7,
            payload={
                "text": "silver",
                "source_document": "loyalty-program",
                "section": "tiers",
            },
        ),
    ]
    client = MagicMock()
    client.query_points.return_value = SimpleNamespace(points=fake_hits)

    with (
        patch("pipelines.rag.embed", return_value=[0.1] * 384) as embed_mock,
        patch("pipelines.rag.get_qdrant_client", return_value=client),
    ):
        results = retrieve("Gold tier?", k=5, min_score=0.55)

    embed_mock.assert_called_once_with("query: Gold tier?")
    client.query_points.assert_called_once()
    assert client.query_points.call_args.kwargs["limit"] == 5
    assert len(results) == 2
    assert all(r["_score"] >= 0.55 for r in results)
    assert results[0]["text"] == "gold tier"


def test_query_returns_generation_not_raw_chunks() -> None:
    chunks = [
        {
            "text": "Gold (50+ points): 15% permanent discount",
            "source_document": "loyalty-program",
            "section": "Program tiers",
            "_score": 0.9,
        }
    ]
    with (
        patch("pipelines.rag.retrieve", return_value=chunks) as retrieve_mock,
        patch(
            "pipelines.rag._generate", return_value="Gold needs 50+ points."
        ) as gen_mock,
    ):
        answer = query("How many points for Gold?")

    retrieve_mock.assert_called_once()
    gen_mock.assert_called_once()
    assert answer == "Gold needs 50+ points."
    # Must not return the raw retrieved chunk text as the answer.
    assert answer != chunks[0]["text"]


def test_setup_recreates_collection_and_upserts(tmp_path: Path) -> None:
    for stem in SOURCE_DOCUMENTS:
        src = CORPUS / f"{stem}.md"
        (tmp_path / f"{stem}.md").write_text(
            src.read_text(encoding="utf-8"), encoding="utf-8"
        )

    client = MagicMock()
    client.collection_exists.return_value = True
    fake_vector = [0.0] * 384

    with (
        patch("pipelines.rag.get_qdrant_client", return_value=client),
        patch("pipelines.rag.embed", return_value=fake_vector),
    ):
        summary = setup(corpus_path=tmp_path)

    client.delete_collection.assert_called_once_with("brasaland_knowledge")
    client.create_collection.assert_called_once()
    client.upsert.assert_called_once()
    assert summary["points"] >= 12
    for stem in SOURCE_DOCUMENTS:
        assert summary["per_document"][stem] >= 3


def test_query_empty_question_raises() -> None:
    with pytest.raises(ValueError):
        query("   ")


def test_generation_tiers_stop_at_gap(monkeypatch: pytest.MonkeyPatch) -> None:
    """GEN_2 absent stops discovery; GEN_3 is not attempted (stop-at-gap)."""
    from pipelines import rag

    monkeypatch.setenv("GEN_1_API_KEY", "key-1")
    monkeypatch.setenv("GEN_1_BASE_URL", "https://api.groq.com/openai/v1")
    monkeypatch.setenv("GEN_1_MODEL", "model-1")
    monkeypatch.delenv("GEN_2_API_KEY", raising=False)
    monkeypatch.setenv("GEN_3_API_KEY", "key-3")
    monkeypatch.setenv("GEN_3_BASE_URL", "https://api.example.com/v1")
    monkeypatch.setenv("GEN_3_MODEL", "model-3")
    tiers = rag._generation_tiers()
    assert [t[0] for t in tiers] == [1]


def test_generation_tiers_include_gen_4_when_contiguous(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from pipelines import rag

    for i in (1, 2, 3, 4):
        monkeypatch.setenv(f"GEN_{i}_API_KEY", f"k{i}")
        monkeypatch.setenv(f"GEN_{i}_BASE_URL", f"https://t{i}.example/v1")
        monkeypatch.setenv(f"GEN_{i}_MODEL", f"m{i}")
    monkeypatch.delenv("GEN_5_API_KEY", raising=False)
    tiers = rag._generation_tiers()
    assert [t[0] for t in tiers] == [1, 2, 3, 4]


def test_generate_fails_over_to_gen_4(monkeypatch: pytest.MonkeyPatch) -> None:
    from typing import Any

    from pipelines import rag

    for i in (1, 2, 3, 4):
        monkeypatch.setenv(f"GEN_{i}_API_KEY", f"key-{i}")
        monkeypatch.setenv(f"GEN_{i}_BASE_URL", f"https://tier{i}.example/v1")
        monkeypatch.setenv(f"GEN_{i}_MODEL", f"model-{i}")
    monkeypatch.delenv("GEN_5_API_KEY", raising=False)

    calls: list[str] = []

    class FakeOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            self.api_key = kwargs["api_key"]
            assert kwargs["max_retries"] == 0
            assert kwargs["timeout"] == rag.GENERATION_TIMEOUT_SECONDS

        @property
        def chat(self) -> Any:
            return self

        @property
        def completions(self) -> Any:
            return self

        def create(self, **_kwargs: Any) -> Any:
            calls.append(self.api_key)
            if self.api_key != "key-4":
                raise RuntimeError(f"tier failed: {self.api_key}")
            fake_message = MagicMock()
            fake_message.content = "answer from tier 4"
            fake_completion = MagicMock()
            fake_completion.choices = [MagicMock(message=fake_message)]
            return fake_completion

    monkeypatch.setattr("openai.OpenAI", FakeOpenAI)
    answer = rag._generate("q?", [])
    assert answer == "answer from tier 4"
    assert calls == ["key-1", "key-2", "key-3", "key-4"]
