"""Generator-node tests for the RFP response worker (LLM mocked)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

_DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
_data_str = str(_DATA_ROOT)
if _data_str not in sys.path:
    sys.path.insert(0, _data_str)

from pipelines.rfp_intake.draft_prompt import DRAFT_PROSE_STYLE_RULES
from pipelines.rfp_intake.response_graph import marketing_worker

_PASSING_DRAFT = (
    "Brasaland delivers consistent quality, a warm experience, and speed of service. "
    "This section covers brand exclusivity for the co-branded offer. "
    "All prices appear in both COP and USD. "
    "Kitchen setup requires fourteen business days. "
    "This offer is valid for 30 days from issuance."
)


def test_worker_returns_passing_draft_on_first_iteration() -> None:
    state = {
        "departments_needed": ["marketing"],
        "metadata": {
            "client_name": "Sunset Bay",
            "budget_range": "~$20,000 USD/yr",
            "scope": "concession",
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
        return_value={"draft_content": _PASSING_DRAFT},
    ):
        out = marketing_worker(state)  # type: ignore[arg-type]

    assert len(out["department_sections"]) == 1
    section = out["department_sections"][0]
    assert section["department_id"] == "marketing"
    assert section["draft_content"] == _PASSING_DRAFT
    evaluation = section["evaluation_results"]
    assert evaluation["overall_pass"] is True
    assert evaluation["iterations"] == 1
    assert evaluation["exhausted"] is False
    assert evaluation["needs_human_review"] is False


def test_worker_prompt_uses_style_rules_and_fenced_metadata() -> None:
    state = {
        "departments_needed": ["marketing"],
        "metadata": {
            "client_name": "Sunset Bay",
            "location": None,
            "budget_range": "",
            "open_questions": [],
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
        return_value={"draft_content": _PASSING_DRAFT},
    ) as mocked:
        marketing_worker(state)  # type: ignore[arg-type]

    kwargs = mocked.call_args.kwargs
    system_prompt = kwargs["system_prompt"]
    user_prompt = kwargs["user_prompt"]
    assert DRAFT_PROSE_STYLE_RULES in system_prompt
    assert '{"draft_content": str}' in system_prompt
    assert "<<<METADATA>>>" in user_prompt
    assert "<<<END METADATA>>>" in user_prompt
    assert "Sunset Bay" in user_prompt
    assert "None" not in user_prompt
    assert "null" not in user_prompt
    assert "client_name" not in user_prompt
    assert "- brand exclusivity" in user_prompt
