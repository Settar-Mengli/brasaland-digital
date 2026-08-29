"""Inventory read + explicit write-reject tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from company_tools_mcp.errors import INVENTORY_WRITE_FORBIDDEN
from company_tools_mcp.tools.inventory import (
    check_stock_impl,
    create_ingredient_impl,
    record_inbound_impl,
    record_outbound_impl,
)


def test_check_stock_by_id(baseline_auth: MagicMock) -> None:
    ingredient = {
        "id": 1,
        "name": "Beef",
        "sku": "BEEF-01",
        "unit": "kg",
        "category": "meat",
        "country": "CO",
        "current_stock": 12.5,
    }
    with patch(
        "company_tools_mcp.tools.inventory.inventory_client.get_product",
        return_value=(200, ingredient),
    ):
        result = check_stock_impl(baseline_auth, ingredient_id=1, location_id=1)
    assert result["ok"] is True
    assert result["ingredient"]["current_stock"] == 12.5


def test_write_tools_reject_without_calling_upstream(baseline_auth: MagicMock) -> None:
    with patch(
        "company_tools_mcp.tools.inventory.inventory_client.list_products"
    ) as list_mock:
        assert create_ingredient_impl(baseline_auth)["code"] == INVENTORY_WRITE_FORBIDDEN
        assert record_inbound_impl(baseline_auth)["code"] == INVENTORY_WRITE_FORBIDDEN
        assert record_outbound_impl(baseline_auth)["code"] == INVENTORY_WRITE_FORBIDDEN
    list_mock.assert_not_called()
