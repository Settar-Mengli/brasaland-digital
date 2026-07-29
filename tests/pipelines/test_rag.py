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
