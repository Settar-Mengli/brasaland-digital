from __future__ import annotations

from level import derive_level


def test_failed_events_are_warning() -> None:
    assert derive_level("consumption_order_failed") == "warning"


def test_rejected_events_are_warning() -> None:
    assert derive_level("direct_stock_edit_rejected") == "warning"


def test_success_events_are_info() -> None:
    assert derive_level("consumption_order_created") == "info"
