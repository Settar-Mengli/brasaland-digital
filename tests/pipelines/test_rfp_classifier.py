"""Classifier prefilter tests against seed markdown (no PDF / no network)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

_DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
_SEED = _DATA_ROOT / "raw" / "seed"
_data_str = str(_DATA_ROOT)
if _data_str not in sys.path:
    sys.path.insert(0, _data_str)

from pipelines.rfp_intake.graph import classify_node, prefilter_validity


def _read_seed(name: str) -> str:
    return (_SEED / name).read_text(encoding="utf-8")


def test_prefilter_sunset_bay_valid() -> None:
    text = _read_seed("sunset-bay-resorts.md")
    assert prefilter_validity(text) == "valid"
    result = classify_node({"markdown": text})
    assert result["is_valid_rfp"] is True


def test_prefilter_andes_tech_valid() -> None:
    text = _read_seed("andes-tech-solutions.md")
    assert prefilter_validity(text) == "valid"
    result = classify_node({"markdown": text})
    assert result["is_valid_rfp"] is True


def test_prefilter_franchise_invalid() -> None:
    text = _read_seed("franchise-inquiry.md")
    assert prefilter_validity(text) == "invalid"
    result = classify_node({"markdown": text})
    assert result["is_valid_rfp"] is False
    assert "not an actionable RFP" in (result.get("discard_reason") or "")


def test_ambiguous_consults_generate_json() -> None:
    ambiguous = "We have a deadline of April 15 for something vague."
    assert prefilter_validity(ambiguous) == "ambiguous"
    with patch(
        "pipelines.rfp_intake.graph.generate_json",
        return_value={"is_valid_rfp": False, "reason": "not commercial"},
    ) as mocked:
        result = classify_node({"markdown": ambiguous})
        mocked.assert_called_once()
        assert result["is_valid_rfp"] is False
        assert result["discard_reason"] == "not commercial"


def test_clear_valid_does_not_call_llm() -> None:
    text = _read_seed("sunset-bay-resorts.md")
    with patch("pipelines.rfp_intake.graph.generate_json") as mocked:
        classify_node({"markdown": text})
        mocked.assert_not_called()
