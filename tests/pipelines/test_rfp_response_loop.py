"""Bounded generate↔evaluate loop exhaust behaviour."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

_DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
_data_str = str(_DATA_ROOT)
if _data_str not in sys.path:
    sys.path.insert(0, _data_str)

from pipelines.rfp_intake.response_evaluators import ITERATION_LIMIT
from pipelines.rfp_intake.response_graph import marketing_worker

# Readable, dual-currency, validity OK — but missing brand pillars so overall_pass fails.
_FAILING_DRAFT = (
    "We propose a catering partnership covering brand exclusivity. "
    "Pricing is listed in both COP and USD for transparency. "
    "Kitchen setup requires fourteen business days after award. "
    "This offer is valid for 30 days from issuance."
)


def test_loop_exhausts_with_needs_human_review_and_keeps_draft() -> None:
    state = {
        "departments_needed": ["marketing"],
        "metadata": {
            "client_name": "Acme",
            "budget_range": "~$20,000 USD/yr",
            "scope": "catering",
        },
        "input_sections": [
            {
                "department_id": "marketing",
                "key_aspects": ["brand exclusivity"],
            }
        ],
    }
    with patch(
        "pipelines.rfp_intake.response_graph.generate_json",
        return_value={"draft_content": _FAILING_DRAFT},
    ) as mocked:
        out = marketing_worker(state)  # type: ignore[arg-type]

    assert mocked.call_count == ITERATION_LIMIT
    section = out["department_sections"][0]
    assert section["draft_content"] == _FAILING_DRAFT
    evaluation = section["evaluation_results"]
    assert evaluation["iterations"] == ITERATION_LIMIT
    assert evaluation["exhausted"] is True
    assert evaluation["needs_human_review"] is True
    assert evaluation["overall_pass"] is False
    assert "discard" not in str(evaluation).lower()
