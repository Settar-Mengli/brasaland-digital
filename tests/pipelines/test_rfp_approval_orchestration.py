"""Ticket-level approval orchestration helpers (mock generate_json)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

_DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
_data_str = str(_DATA_ROOT)
if _data_str not in sys.path:
    sys.path.insert(0, _data_str)

from pipelines.rfp_intake.approval_orchestration import (
    apply_arbitration_stamps,
    extract_all_sections,
    extract_section_numbers,
    synthesize_final_document,
)
from pipelines.rfp_intake.arbitration import run_arbitration


def _gen(system_prompt: str, user_prompt: str, **_k) -> dict[str, Any]:
    if "Department: operaciones" in user_prompt:
        return {"cost": 10.0, "setup_days": 12, "price_per_cover": 20.0}
    if "Department: procurement" in user_prompt:
        return {"cost": 25.0, "setup_days": 12, "price_per_cover": None}
    if "Department: marketing" in user_prompt:
        return {"cost": None, "setup_days": 7, "price_per_cover": None}
    return {"cost": None, "setup_days": None, "price_per_cover": None}


def test_extract_prompt_does_not_dump_key_aspects_list_repr() -> None:
    captured: dict[str, str] = {}

    def _capture(system_prompt: str, user_prompt: str, **_k) -> dict[str, Any]:
        captured["user"] = user_prompt
        return {"cost": None, "setup_days": None, "price_per_cover": None}

    with patch(
        "pipelines.rfp_intake.approval_orchestration.generate_json",
        side_effect=_capture,
    ):
        extract_section_numbers(
            "marketing",
            {
                "draft_content": "prior marketing draft",
                "key_aspects": ["brand exclusivity", "co-branded offer"],
            },
        )

    user_prompt = captured["user"]
    assert "- brand exclusivity" in user_prompt
    assert "- co-branded offer" in user_prompt
    assert "[" not in user_prompt
    assert "]" not in user_prompt


def test_extract_all_and_arbitration_stamps_forced_depts() -> None:
    sections = {
        "marketing": {"draft_content": "M", "key_aspects": []},
        "operaciones": {"draft_content": "O", "key_aspects": []},
        "procurement": {"draft_content": "P", "key_aspects": []},
    }
    with patch(
        "pipelines.rfp_intake.approval_orchestration.generate_json",
        side_effect=_gen,
    ):
        numbers = extract_all_sections(
            sections,
            ["marketing", "operaciones", "procurement"],
            metadata={"budget_range": "~$20,000 USD/yr"},
        )

    assert numbers["operaciones"]["price_per_cover"] == 20.0
    assert numbers["procurement"]["cost"] == 25.0
    assert numbers["marketing"]["setup_days"] == 7.0

    merged = {
        dept: {**sections[dept], **numbers[dept]}
        for dept in ("marketing", "operaciones", "procurement")
    }
    arb_raw = run_arbitration(sections=merged, metadata={"budget_range": "~$20,000 USD/yr"})
    stamped, arb = apply_arbitration_stamps(merged, arb_raw)

    assert "section_stamps" not in arb
    ids = [t["id"] for t in arb["triggers_fired"]]
    assert "setup-sla-breach" in ids
    assert "cost-vs-feasibility" in ids
    assert stamped["marketing"]["forced_request_changes"] is True
    assert stamped["operaciones"]["forced_request_changes"] is True
    assert stamped["procurement"]["forced_request_changes"] is True


def test_synthesize_final_document_shape() -> None:
    doc = synthesize_final_document(
        ticket_id="t-orch",
        departments_needed=["marketing", "operaciones"],
        sections={
            "marketing": {"draft_content": "M"},
            "operaciones": {"draft_content": "O"},
        },
        metadata={
            "client_name": "Acme",
            "location": "Medellín",
            "service_type": "catering",
            "budget_range": "USD 10 / COP 40",
            "open_questions": [],
        },
        arbitration={
            "triggers_fired": [{"id": "setup-sla-breach"}],
            "resolutions": ["fixed"],
            "ceo_approval_required": False,
        },
        ceo_decision=None,
        approval_outcomes=[
            {
                "department_id": "marketing",
                "approver": "Camila Ospina",
                "approved_at": "2026-01-01T00:00:00+00:00",
            },
            {
                "department_id": "operaciones",
                "approver": "Felipe Guerrero",
                "approved_at": "2026-01-01T00:00:01+00:00",
            },
        ],
    )
    assert doc is not None
    assert doc["header"]["ticket_id"] == "t-orch"
    assert [s["department_id"] for s in doc["sections"]] == [
        "marketing",
        "operaciones",
    ]
    assert doc["total_estimated_value"] == "USD 10 / COP 40"
    assert doc["arbitration_outcomes"]["triggers_fired"][0]["id"] == "setup-sla-breach"
    assert doc["ceo_line"] is None
