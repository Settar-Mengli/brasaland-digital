"""Regen-node prompt content (LLM mocked; no live generation)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

_DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
_data_str = str(_DATA_ROOT)
if _data_str not in sys.path:
    sys.path.insert(0, _data_str)

from pipelines.rfp_intake.approval_graph import regen_node
from pipelines.rfp_intake.draft_prompt import DRAFT_PROSE_STYLE_RULES

_JSON_NULL_SENTENCE = (
    "For the JSON fields cost, setup_days, and price_per_cover only, use JSON "
    "null when that number is not stated in the revised draft. Do not put the "
    "words null, None, or not stated inside draft_content."
)


def test_regen_prompt_splits_style_rules_from_json_null_instruction() -> None:
    state = {
        "department": "marketing",
        "section": {
            "draft_content": "prior marketing draft",
            "human_feedback": "tighten the setup timeline",
        },
        "rework_count": 0,
    }
    with patch(
        "pipelines.rfp_intake.approval_graph.generate_json",
        return_value={
            "draft_content": "revised draft",
            "cost": None,
            "setup_days": 14,
            "price_per_cover": None,
        },
    ) as mocked:
        regen_node(state)  # type: ignore[arg-type]

    system_prompt = mocked.call_args.kwargs["system_prompt"]
    assert DRAFT_PROSE_STYLE_RULES in system_prompt
    assert _JSON_NULL_SENTENCE in system_prompt
    fused = (
        "Never invent absent figures — use null when a number is not stated. "
        "Respond with JSON only"
    )
    assert fused not in system_prompt
    role_end = system_prompt.index("Address the feedback.")
    rules_start = system_prompt.index(DRAFT_PROSE_STYLE_RULES)
    json_null_start = system_prompt.index(_JSON_NULL_SENTENCE)
    assert role_end < rules_start < json_null_start
