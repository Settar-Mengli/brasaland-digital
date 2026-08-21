"""Unit tests for RFP response evaluators (no LLM / no DB)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
_data_str = str(_DATA_ROOT)
if _data_str not in sys.path:
    sys.path.insert(0, _data_str)

from pipelines.rfp_intake.response_evaluators import (
    evaluate_all,
    evaluate_readability,
    evaluate_relevance,
)
from pipelines.rfp_intake import response_evaluators as evaluators


_CLEAN_DRAFT = (
    "Brasaland delivers consistent quality, a warm experience, and speed of service. "
    "Our catering proposal covers brand exclusivity for the client. "
    "Pricing is quoted in both COP and USD. "
    "Setup requires 12 business days. "
    "This offer is valid for 30 days from issuance."
)

_GIBBERISH = (
    "The anachronistic epistemological methodologies utilized by contemporaneous "
    "institutional apparatuses necessitate comprehensive reconceptualization of "
    "heretofore unexamined paradigmatic frameworks concerning interdisciplinary "
    "pedagogical modalities within multinational organizational conglomerates."
)


def test_evaluate_readability_clean_vs_gibberish() -> None:
    clean = evaluate_readability(_CLEAN_DRAFT)
    assert clean["pass"] is True
    assert "flesch_reading_ease" in clean["details"]
    assert "flesch_kincaid_grade" in clean["details"]

    gibberish = evaluate_readability(_GIBBERISH)
    assert gibberish["pass"] is False


def test_evaluate_relevance_present_and_missing() -> None:
    ok = evaluate_relevance(_CLEAN_DRAFT, ["brand exclusivity", "consistent quality"])
    assert ok["pass"] is True
    assert ok["missing_aspects"] == []

    missing = evaluate_relevance(_CLEAN_DRAFT, ["brand exclusivity", "signature menu"])
    assert missing["pass"] is False
    assert missing["missing_aspects"] == ["signature menu"]


def test_evaluate_all_shape_and_overall_pass() -> None:
    result = evaluate_all(
        _CLEAN_DRAFT,
        key_aspects=["brand exclusivity"],
        budget_range="~$20,000 USD/yr",
        department_id="marketing",
    )
    required = {
        "department_id",
        "readability",
        "relevance",
        "compliance",
        "overall_pass",
        "feedback_for_generator",
        "iterations",
        "exhausted",
        "needs_human_review",
        "ceo_approval_required",
    }
    assert required <= set(result.keys())
    assert result["department_id"] == "marketing"
    assert result["overall_pass"] is True
    assert result["feedback_for_generator"] == ""
    assert result["iterations"] == 1
    assert result["exhausted"] is False
    assert result["needs_human_review"] is False
    assert result["ceo_approval_required"] is False
    assert result["readability"]["pass"] is True
    assert result["relevance"]["pass"] is True
    assert result["compliance"]["pass"] is True


@pytest.fixture
def reset_compliance_cache() -> None:
    evaluators._CONTEXT_SECTION_5 = None
    yield
    evaluators._CONTEXT_SECTION_5 = None


def test_context_path_env_beats_packaged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    reset_compliance_cache: None,
) -> None:
    alt = tmp_path / "CONTEXT-rfp.md"
    alt.write_text("# RFP\n\n## 5. Compliance\n\nenv-tier rulebook\n", encoding="utf-8")
    monkeypatch.setenv("RFP_CONTEXT_PATH", str(alt))

    resolved = evaluators._context_rfp_path()
    assert resolved == alt
    assert resolved != evaluators._PACKAGED_CONTEXT
    assert evaluators._PACKAGED_CONTEXT.is_file()

    rules = evaluators._load_compliance_rules()
    assert "env-tier rulebook" in rules
    assert rules != ""


def test_context_path_all_missing_raises(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    reset_compliance_cache: None,
) -> None:
    monkeypatch.setenv("RFP_CONTEXT_PATH", str(tmp_path / "missing-env.md"))
    monkeypatch.setattr(evaluators, "_PACKAGED_CONTEXT", tmp_path / "raw" / "CONTEXT-rfp.md")
    monkeypatch.setattr(evaluators, "_BAKED_CONTEXT", tmp_path / "context" / "CONTEXT-rfp.md")

    with pytest.raises(FileNotFoundError, match="CONTEXT-rfp.md not found"):
        evaluators._context_rfp_path()
    with pytest.raises(FileNotFoundError, match="CONTEXT-rfp.md not found"):
        evaluators._load_compliance_rules()
    assert evaluators._CONTEXT_SECTION_5 is None
