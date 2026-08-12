"""Compliance evaluator tests against CONTEXT §5 brand pillars."""

from __future__ import annotations

import sys
from pathlib import Path

_DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
_data_str = str(_DATA_ROOT)
if _data_str not in sys.path:
    sys.path.insert(0, _data_str)

from pipelines.rfp_intake.response_evaluators import evaluate_compliance


def test_compliance_fails_when_brand_pillars_missing() -> None:
    draft = (
        "We propose catering with pricing in COP and USD. "
        "Setup takes twelve business days. "
        "This offer is valid for 30 days from issuance."
    )
    result = evaluate_compliance(draft, budget_range="~$20,000 USD/yr")
    assert result["pass"] is False and "brand_pillars" in result["rule_ids"]


def test_compliance_passes_when_all_hard_rules_met() -> None:
    draft = (
        "Brasaland delivers consistent quality, a warm experience, and speed of service. "
        "Unit pricing is 120000 COP / 30 USD per cover. "
        "Kitchen setup requires 12 business days after award. "
        "This offer is valid for 30 days from issuance."
    )
    result = evaluate_compliance(draft, budget_range=None)
    assert result["pass"] is True
    assert result["rule_ids"] == []
