from __future__ import annotations

from datetime import datetime, timedelta, timezone

from incident_analysis.types import AnalysisResult, Totals
from result_store import AnalysisResultStore


def _empty_result() -> AnalysisResult:
    return AnalysisResult(
        totals=Totals(valid=0, invalid=0, total=0),
        by_category={},
        by_status={},
        average_satisfaction_closed=None,
        invalid_records=(),
        invalid_count_by_rule={},
        satisfaction_distribution={},
    )


def test_store_returns_unique_ids_and_owner() -> None:
    store = AnalysisResultStore(ttl_seconds=60)
    first = store.store("1", _empty_result())
    second = store.store("1", _empty_result())

    assert first.result_id != second.result_id
    assert store.get(first.result_id) is not None
    assert store.get(first.result_id).owner_user_uuid == "1"


def test_get_purges_expired_entries() -> None:
    store = AnalysisResultStore(ttl_seconds=60)
    entry = store.store("7", _empty_result())
    with store._lock:
        store._entries[entry.result_id] = entry.__class__(
            result_id=entry.result_id,
            owner_user_uuid=entry.owner_user_uuid,
            result=entry.result,
            expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        )

    assert store.get(entry.result_id) is None
