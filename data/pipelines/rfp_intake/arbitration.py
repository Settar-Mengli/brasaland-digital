"""Fixed §7 arbitration — deterministic, non-LLM.

Detects cost-vs-feasibility, setup-sla-breach, and ceo-threshold from structured
section numbers + metadata. Never invents missing values (null → trigger skips).
"""

from __future__ import annotations

from typing import Any

from pipelines.rfp_intake.response_evaluators import _parse_budget_usd_ceiling

_SETUP_SLA_MIN_DAYS = 10
_CEO_USD_THRESHOLD = 50_000


def _as_number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def run_arbitration(
    *,
    sections: dict[str, dict],
    metadata: dict | None,
) -> dict[str, Any]:
    """Evaluate CONTEXT §7 triggers against structured section fields.

    Returns a record suitable for ``ApprovalState.arbitration`` plus section
    stamps the graph merges for forced departments.
    """
    meta = metadata or {}
    sections = sections or {}
    triggers_fired: list[dict[str, Any]] = []
    forced: set[str] = set()
    resolutions: list[str] = []

    # setup-sla-breach: any section with setup_days < 10
    for dept, payload in sections.items():
        days = _as_number((payload or {}).get("setup_days"))
        if days is None:
            continue
        if days < _SETUP_SLA_MIN_DAYS:
            forced.add(str(dept))
            triggers_fired.append(
                {
                    "id": "setup-sla-breach",
                    "details": {
                        "department": str(dept),
                        "setup_days": days,
                        "minimum": _SETUP_SLA_MIN_DAYS,
                    },
                }
            )
            resolutions.append(
                f"setup-sla-breach: force request_changes on {dept} "
                f"until setup_days>={_SETUP_SLA_MIN_DAYS}"
            )

    # cost-vs-feasibility: procurement.cost > operaciones.price_per_cover
    ops = sections.get("operaciones") or {}
    proc = sections.get("procurement") or {}
    price_per_cover = _as_number(ops.get("price_per_cover"))
    procurement_cost = _as_number(proc.get("cost"))
    if (
        price_per_cover is not None
        and procurement_cost is not None
        and procurement_cost > price_per_cover
    ):
        forced.add("operaciones")
        forced.add("procurement")
        triggers_fired.append(
            {
                "id": "cost-vs-feasibility",
                "details": {
                    "operaciones_price_per_cover": price_per_cover,
                    "procurement_cost": procurement_cost,
                },
            }
        )
        resolutions.append(
            "cost-vs-feasibility: procurement cost exceeds operaciones "
            "per-cover price — raise price or reduce scope "
            "(force request_changes on operaciones + procurement)"
        )

    # ceo-threshold: budget ceiling > $50k OR any section flag
    ceiling = _parse_budget_usd_ceiling(
        str(meta["budget_range"]) if meta.get("budget_range") is not None else None
    )
    ceo_from_budget = ceiling is not None and ceiling > _CEO_USD_THRESHOLD
    ceo_from_sections = False
    for payload in sections.values():
        evaluation = (payload or {}).get("evaluation_results") or {}
        if isinstance(evaluation, dict) and evaluation.get("ceo_approval_required"):
            ceo_from_sections = True
            break
    ceo_required = bool(ceo_from_budget or ceo_from_sections)
    if ceo_required:
        triggers_fired.append(
            {
                "id": "ceo-threshold",
                "details": {
                    "budget_ceiling_usd": ceiling,
                    "from_budget": ceo_from_budget,
                    "from_sections": ceo_from_sections,
                },
            }
        )
        resolutions.append(
            "ceo-threshold: CEO (Mariana Restrepo) approval required before synthesis"
        )

    forced_departments = sorted(forced)
    section_stamps: dict[str, dict[str, Any]] = {}
    for dept in forced_departments:
        current = dict(sections.get(dept) or {})
        current["forced_request_changes"] = True
        relevant = [
            r
            for r in resolutions
            if f"on {dept}" in r
            or (
                r.startswith("cost-vs-feasibility")
                and dept in ("operaciones", "procurement")
            )
        ]
        current["arbiter_feedback"] = "; ".join(relevant) or "; ".join(resolutions)
        section_stamps[dept] = current

    return {
        "triggers_fired": triggers_fired,
        "forced_departments": forced_departments,
        "ceo_approval_required": ceo_required,
        "resolutions": resolutions,
        "section_stamps": section_stamps,
    }
