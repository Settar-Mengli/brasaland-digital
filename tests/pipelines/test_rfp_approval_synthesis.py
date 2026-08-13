"""Unit tests for synthesize_final_document (§2.4 payload)."""

from __future__ import annotations

import sys
from pathlib import Path

_DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
_data_str = str(_DATA_ROOT)
if _data_str not in sys.path:
    sys.path.insert(0, _data_str)

from pipelines.rfp_intake.approval_orchestration import synthesize_final_document


def _base_kwargs(**overrides):
    kwargs = {
        "ticket_id": "t-1",
        "metadata": {
            "client_name": "Acme",
            "location": "Medellín",
            "service_type": "catering",
            "budget_range": "USD 20,000 / COP 80,000,000",
            "open_questions": [],
        },
        "departments_needed": ["marketing", "operaciones"],
        "sections": {
            "marketing": {"draft_content": "M draft"},
            "operaciones": {"draft_content": "O draft"},
            "training": {"draft_content": "should omit"},
        },
        "approval_outcomes": [
            {
                "department_id": "marketing",
                "status": "approved",
                "approver": "Camila Ospina",
                "approved_at": "2026-01-01T00:00:00+00:00",
            },
            {
                "department_id": "operaciones",
                "status": "approved",
                "approver": "Felipe Guerrero",
                "approved_at": "2026-01-01T00:00:01+00:00",
            },
        ],
        "arbitration": {
            "triggers_fired": [],
            "resolutions": [],
            "ceo_approval_required": False,
        },
        "ceo_decision": None,
        "error": None,
    }
    kwargs.update(overrides)
    return kwargs


def test_synthesis_section_order_omits_inactive() -> None:
    doc = synthesize_final_document(**_base_kwargs())
    assert doc is not None
    depts = [s["department_id"] for s in doc["sections"]]
    assert depts == ["marketing", "operaciones"]
    assert doc["sections"][0]["owner"] == "Camila Ospina"
    assert "approved by Camila Ospina at" in (doc["sections"][0]["approval_stamp"] or "")


def test_synthesis_total_from_budget_range_not_section_costs() -> None:
    doc = synthesize_final_document(
        **_base_kwargs(
            sections={
                "marketing": {"draft_content": "M", "cost": 999},
                "operaciones": {"draft_content": "O", "cost": 999},
            }
        )
    )
    assert doc is not None
    assert doc["total_estimated_value"] == "USD 20,000 / COP 80,000,000"


def test_synthesis_omits_total_when_budget_missing() -> None:
    doc = synthesize_final_document(
        **_base_kwargs(metadata={"client_name": "Acme", "open_questions": []})
    )
    assert doc is not None
    assert doc["total_estimated_value"] is None
    assert any("budget" in str(q).lower() for q in doc["open_questions"])


def test_synthesis_ceo_line_when_required_and_approved() -> None:
    doc = synthesize_final_document(
        **_base_kwargs(
            arbitration={
                "triggers_fired": [{"id": "ceo-threshold"}],
                "resolutions": ["ceo-threshold"],
                "ceo_approval_required": True,
            },
            ceo_decision="approved",
            ceo_approved_at="2026-02-01T12:00:00+00:00",
        )
    )
    assert doc is not None
    assert doc["ceo_line"] == "CEO approval: Mariana Restrepo, 2026-02-01T12:00:00+00:00"
    assert doc["arbitration_outcomes"]["triggers_fired"][0]["id"] == "ceo-threshold"


def test_synthesis_none_when_ceo_rejected() -> None:
    doc = synthesize_final_document(
        **_base_kwargs(ceo_decision="rejected", error="CEO rejected the proposal")
    )
    assert doc is None
