from __future__ import annotations

from copy import deepcopy
from typing import Any
from uuid import uuid4

import pytest

from odoo_accounting_cli_v4.bridge.inventory_operations import (
    ACTION,
    OdooInventoryOperationsPort,
)
from odoo_accounting_cli_v4.capabilities.inventory_operations import (
    InventoryOperationsReadError,
    read_inventory_operations,
    validate_inventory_operations_request,
)


def request(parameters: dict[str, Any] | None = None, *, company_id: int = 1) -> dict:
    return {
        "schema_version": "v1",
        "request_id": str(uuid4()),
        "context": {
            "database": "odoo_cli_v4_dev",
            "company_id": company_id,
            "user_login": "accountant",
            "language": "en_US",
            "timezone": "UTC",
        },
        "parameters": parameters or {},
    }


def transfer(record_id: int = 9) -> dict[str, Any]:
    return {
        "id": record_id,
        "company_id": 1,
        "name": f"WH/OUT/{record_id:05d}",
        "origin": "SO001",
        "state": "assigned",
        "operation_type": {"id": 4, "code": "outgoing", "name": "Delivery"},
        "scheduled_date": "2026-08-28T10:00:00Z",
        "completed_date": None,
        "source_location": {"id": 20, "name": "WH/Stock"},
        "destination_location": {"id": 30, "name": "Customers"},
        "partner": {"id": 40, "name": "Customer"},
    }


def move(record_id: int = 19) -> dict[str, Any]:
    return {
        "id": record_id,
        "company_id": 1,
        "reference": "WH/OUT/00009",
        "description_picking": "Test product",
        "state": "assigned",
        "date": "2026-08-28T09:00:00Z",
        "transfer": {"id": 9, "name": "WH/OUT/00009"},
        "product": {"id": 50, "code": "TEST", "name": "Test product"},
        "uom": {"id": 1, "name": "Units"},
        "demand_quantity": "5",
        "moved_quantity": "2",
        "source_location": {"id": 20, "name": "WH/Stock"},
        "destination_location": {"id": 30, "name": "Customers"},
    }


SUMMARY = {
    "company_id": 1,
    "warehouse": {"id": 2, "code": "WH", "name": "Main Warehouse"},
    "location": {"id": 20, "name": "WH/Stock"},
    "groups": [
        {
            "product": {"id": 50, "code": "TEST", "name": "Test product"},
            "uom": {"id": 1, "name": "Units"},
            "quantity": "5",
            "reserved_quantity": "2",
            "available_quantity": "3",
        }
    ],
}

AVAILABILITY = {
    "company_id": 1,
    "product": {"id": 50, "code": "TEST", "name": "Test product"},
    "warehouse": None,
    "location": {"id": 20, "name": "WH/Stock"},
    "uom": {"id": 1, "name": "Units"},
    "on_hand_quantity": "5",
    "free_quantity": "5",
    "incoming_quantity": "0",
    "outgoing_quantity": "0",
    "forecast_quantity": "5",
}


class Port:
    user_id = 5

    def __init__(self, items: list[dict[str, Any]]) -> None:
        self.items = items
        self.calls: list[dict[str, Any]] = []

    def read(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return {
            "user_id": 5,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "cursor_found": True,
            "items": deepcopy(self.items),
        }


def test_transfer_search_uses_only_fixed_filters_and_limit_plus_one() -> None:
    port = Port([transfer(9), transfer(8)])
    parameters = {
        "picking_type_id": 4,
        "partner_id": 40,
        "state": "assigned",
        "date_from": "2026-08-01",
        "date_to": "2026-08-31",
        "limit": 1,
    }

    result = read_inventory_operations(
        port, "stock.transfer.search", request(parameters)
    )

    assert result["items"] == [transfer(9)]
    assert result["has_more"] is True
    assert isinstance(result["next_cursor"], str)
    assert port.calls == [
        {
            "capability_id": "stock.transfer.search",
            "company_id": 1,
            "parameters": {
                "picking_type_id": 4,
                "partner_id": 40,
                "state": "assigned",
                "date_from": "2026-08-01",
                "date_to": "2026-08-31",
                "after": None,
                "limit": 2,
            },
        }
    ]


def test_cursor_is_bound_to_filters_company_user_and_capability() -> None:
    first = read_inventory_operations(
        Port([transfer(9), transfer(8)]),
        "stock.transfer.search",
        request({"state": "assigned", "limit": 1}),
    )
    cursor = first["next_cursor"]
    second = Port([])

    read_inventory_operations(
        second,
        "stock.transfer.search",
        request({"state": "assigned", "limit": 1, "cursor": cursor}),
    )
    assert second.calls[0]["parameters"]["after"] == 9

    with pytest.raises(InventoryOperationsReadError) as caught:
        read_inventory_operations(
            Port([]),
            "stock.transfer.search",
            request({"state": "done", "limit": 1, "cursor": cursor}),
        )
    assert caught.value.code == "invalid_cursor"


def test_transfer_get_and_move_search_have_distinct_fixed_shapes() -> None:
    assert (
        read_inventory_operations(
            Port([transfer()]), "stock.transfer.get", request({"transfer_id": 9})
        )
        == transfer()
    )

    move_port = Port([move()])
    result = read_inventory_operations(
        move_port,
        "stock.move.search",
        request({"transfer_id": 9, "product_id": 50}),
    )
    assert result == {"items": [move()], "has_more": False, "next_cursor": None}
    assert "name" not in result["items"][0]
    assert result["items"][0]["description_picking"] == "Test product"


def test_transfer_accepts_native_operation_type_extension_codes() -> None:
    manufacturing = transfer()
    manufacturing["operation_type"]["code"] = "mrp_operation"

    result = read_inventory_operations(
        Port([manufacturing]), "stock.transfer.get", request({"transfer_id": 9})
    )

    assert result["operation_type"]["code"] == "mrp_operation"


def test_summary_and_availability_validate_scope_and_decimal_strings() -> None:
    summary = read_inventory_operations(
        Port([SUMMARY]),
        "inventory.on_hand.summary",
        request({"warehouse_id": 2, "location_id": 20, "product_id": 50}),
    )
    assert summary == SUMMARY

    availability = read_inventory_operations(
        Port([AVAILABILITY]),
        "inventory.availability.inspect",
        request({"product_id": 50, "location_id": 20}),
    )
    assert availability == AVAILABILITY

    invalid = deepcopy(SUMMARY)
    invalid["groups"][0]["available_quantity"] = "4"
    with pytest.raises(InventoryOperationsReadError) as caught:
        read_inventory_operations(
            Port([invalid]),
            "inventory.on_hand.summary",
            request({"warehouse_id": 2, "location_id": 20, "product_id": 50}),
        )
    assert caught.value.code == "failed_validation"


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    [
        ("stock.transfer.search", {"domain": []}),
        ("stock.transfer.search", {"state": []}),
        ("stock.move.search", {"state": "available"}),
        ("inventory.on_hand.summary", {"group_by": "location"}),
        (
            "inventory.availability.inspect",
            {"product_id": 50, "warehouse_id": 2, "location_id": 20},
        ),
        ("stock.transfer.get", {"transfer_id": True}),
    ],
)
def test_rejects_parameters_outside_the_frozen_contract(
    capability_id: str, parameters: dict[str, Any]
) -> None:
    with pytest.raises(InventoryOperationsReadError) as caught:
        validate_inventory_operations_request(capability_id, request(parameters))
    assert caught.value.code == "invalid_request"


def test_missing_record_and_acl_failures_are_typed() -> None:
    with pytest.raises(InventoryOperationsReadError) as missing:
        read_inventory_operations(
            Port([]), "stock.transfer.get", request({"transfer_id": 404})
        )
    assert missing.value.code == "record_not_found"

    class DeniedPort(Port):
        def read(self, **kwargs: Any) -> dict[str, Any]:
            page = super().read(**kwargs)
            page["access_allowed"] = False
            return page

    with pytest.raises(InventoryOperationsReadError) as denied:
        read_inventory_operations(DeniedPort([]), "stock.transfer.search", request())
    assert denied.value.code == "unauthorized"


def test_bridge_uses_exact_action_payload_and_verifies_page() -> None:
    class Client:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict[str, Any]]] = []

        def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
            self.calls.append((action, payload))
            return {
                "user_id": 5,
                "company_visible": True,
                "module_installed": True,
                "access_allowed": True,
                "cursor_found": True,
                "items": [transfer()],
            }

    client = Client()
    port = OdooInventoryOperationsPort(client)
    page = port.read(
        capability_id="stock.transfer.get",
        company_id=1,
        parameters={"transfer_id": 9},
    )

    assert ACTION == "accounting.inventory_operations.read"
    assert page["items"] == [transfer()]
    assert port.user_id == 5
    assert client.calls == [
        (
            ACTION,
            {
                "capability_id": "stock.transfer.get",
                "company_id": 1,
                "parameters": {"transfer_id": 9},
            },
        )
    ]
