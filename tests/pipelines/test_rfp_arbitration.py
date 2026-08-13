"""Unit tests for fixed §7 arbitration (non-LLM)."""

from __future__ import annotations

import sys
from pathlib import Path

_DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
_data_str = str(_DATA_ROOT)
if _data_str not in sys.path:
    sys.path.insert(0, _data_str)

from pipelines.rfp_intake.arbitration import run_arbitration


def test_setup_sla_breach_fires_when_setup_days_under_10() -> None:
    result = run_arbitration(
        sections={
            "marketing": {"setup_days": 7, "draft_content": "x"},
            "operaciones": {"setup_days": 14},
        },
        metadata={},
    )
    ids = [t["id"] for t in result["triggers_fired"]]
    assert "setup-sla-breach" in ids
    assert "marketing" in result["forced_departments"]
    assert "operaciones" not in result["forced_departments"]
    assert result["section_stamps"]["marketing"]["forced_request_changes"] is True


def test_setup_sla_null_does_not_fire() -> None:
    result = run_arbitration(
        sections={"marketing": {"setup_days": None, "draft_content": "fast setup"}},
        metadata={},
    )
    assert all(t["id"] != "setup-sla-breach" for t in result["triggers_fired"])
    assert result["forced_departments"] == []


def test_cost_vs_feasibility_fires_when_procurement_cost_exceeds_price_per_cover() -> None:
    result = run_arbitration(
        sections={
            "operaciones": {"price_per_cover": 20.0, "cost": 15.0},
            "procurement": {"cost": 25.0, "price_per_cover": None},
        },
        metadata={},
    )
    ids = [t["id"] for t in result["triggers_fired"]]
    assert "cost-vs-feasibility" in ids
    assert set(result["forced_departments"]) == {"operaciones", "procurement"}
    details = next(
        t["details"] for t in result["triggers_fired"] if t["id"] == "cost-vs-feasibility"
    )
    assert details["procurement_cost"] == 25.0
    assert details["operaciones_price_per_cover"] == 20.0


def test_cost_vs_feasibility_does_not_fire_when_price_per_cover_null() -> None:
    result = run_arbitration(
        sections={
            "operaciones": {"price_per_cover": None, "cost": 15.0},
            "procurement": {"cost": 25.0},
        },
        metadata={},
    )
    assert all(t["id"] != "cost-vs-feasibility" for t in result["triggers_fired"])


def test_cost_vs_feasibility_does_not_fire_when_procurement_cost_null() -> None:
    result = run_arbitration(
        sections={
            "operaciones": {"price_per_cover": 20.0},
            "procurement": {"cost": None},
        },
        metadata={},
    )
    assert all(t["id"] != "cost-vs-feasibility" for t in result["triggers_fired"])


def test_cost_vs_feasibility_does_not_fire_when_cost_not_greater() -> None:
    result = run_arbitration(
        sections={
            "operaciones": {"price_per_cover": 30.0},
            "procurement": {"cost": 25.0},
        },
        metadata={},
    )
    assert all(t["id"] != "cost-vs-feasibility" for t in result["triggers_fired"])


def test_ceo_threshold_from_budget_ceiling() -> None:
    result = run_arbitration(
        sections={"marketing": {}},
        metadata={"budget_range": "~$60–75k USD/yr"},
    )
    assert result["ceo_approval_required"] is True
    assert any(t["id"] == "ceo-threshold" for t in result["triggers_fired"])
    assert result["forced_departments"] == []


def test_ceo_threshold_from_section_flag() -> None:
    result = run_arbitration(
        sections={
            "marketing": {
                "evaluation_results": {"ceo_approval_required": True},
            }
        },
        metadata={"budget_range": "~$20,000 USD/yr"},
    )
    assert result["ceo_approval_required"] is True


def test_ceo_not_required_under_threshold() -> None:
    result = run_arbitration(
        sections={"marketing": {"evaluation_results": {"ceo_approval_required": False}}},
        metadata={"budget_range": "~$20,000 USD/yr"},
    )
    assert result["ceo_approval_required"] is False
    assert all(t["id"] != "ceo-threshold" for t in result["triggers_fired"])
