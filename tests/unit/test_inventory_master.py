from __future__ import annotations

from copy import deepcopy
from uuid import uuid4

import pytest

from odoo_accounting_cli_v4.capabilities.inventory_master import (
    InventoryMasterReadError,
    read_inventory_master,
    validate_inventory_master_request,
)

CAPABILITIES = {
    "product.category.list": {
        "id": 9,
        "name": "All",
        "complete_name": "All",
        "parent_id": None,
    },
    "warehouse.list": {
        "id": 9,
        "name": "Main Warehouse",
        "code": "WH",
        "active": True,
        "company_id": 1,
        "reception_steps": "one_step",
        "delivery_steps": "ship_only",
    },
    "stock.location.list": {
        "id": 9,
        "name": "Stock",
        "complete_name": "WH/Stock",
        "active": True,
        "usage": "internal",
        "company_id": 1,
        "parent_id": 3,
        "warehouse_id": 2,
    },
    "stock.operation_type.list": {
        "id": 9,
        "name": "Receipts",
        "active": True,
        "code": "incoming",
        "sequence_code": "IN",
        "company_id": 1,
        "warehouse_id": 2,
        "source_location_id": 4,
        "destination_location_id": 9,
    },
    "stock.route.list": {
        "id": 9,
        "name": "Buy",
        "active": True,
        "sequence": 10,
        "company_id": None,
        "product_selectable": True,
        "product_category_selectable": True,
        "warehouse_selectable": False,
        "warehouse_ids": [2],
    },
}

DEFAULT_FILTERS = {
    "product.category.list": {"parent_id": None},
    "warehouse.list": {"active": True},
    "stock.location.list": {
        "active": True,
        "warehouse_id": None,
        "usage": None,
    },
    "stock.operation_type.list": {
        "active": True,
        "warehouse_id": None,
        "code": None,
    },
    "stock.route.list": {"active": True, "warehouse_id": None},
}


def request(parameters: dict | None = None, *, company_id: int = 1) -> dict:
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


class Port:
    user_id = 5

    def __init__(self, items: list[dict]) -> None:
        self.items = items
        self.calls: list[dict] = []

    def read(self, **kwargs: object) -> dict:
        self.calls.append(kwargs)
        return {
            "user_id": 5,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "cursor_found": True,
            "items": deepcopy(self.items),
        }


@pytest.mark.parametrize(("capability_id", "item"), CAPABILITIES.items())
def test_lists_validate_rows_and_use_limit_plus_one(
    capability_id: str, item: dict
) -> None:
    older = {**item, "id": 8}
    port = Port([item, older])

    result = read_inventory_master(port, capability_id, request({"limit": 1}))

    assert result["items"] == [item]
    assert result["has_more"] is True
    assert isinstance(result["next_cursor"], str)
    assert port.calls == [
        {
            "capability_id": capability_id,
            "company_id": 1,
            "parameters": {
                **DEFAULT_FILTERS[capability_id],
                "after": None,
                "limit": 2,
            },
        }
    ]


def test_cursor_is_bound_to_capability_company_user_and_filters() -> None:
    port = Port(
        [
            {**CAPABILITIES["warehouse.list"], "id": 9},
            {**CAPABILITIES["warehouse.list"], "id": 8},
        ]
    )
    first = read_inventory_master(
        port, "warehouse.list", request({"active": None, "limit": 1})
    )

    cursor = first["next_cursor"]
    second_port = Port([])
    read_inventory_master(
        second_port,
        "warehouse.list",
        request({"active": None, "limit": 1, "cursor": cursor}),
    )
    assert second_port.calls[0]["parameters"]["after"] == 9

    with pytest.raises(InventoryMasterReadError, match="cursor") as exc_info:
        read_inventory_master(
            Port([]),
            "warehouse.list",
            request({"active": False, "limit": 1, "cursor": cursor}),
        )
    assert exc_info.value.code == "invalid_cursor"


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    [
        ("product.category.list", {"active": True}),
        ("warehouse.list", {"active": "yes"}),
        ("stock.location.list", {"warehouse_id": 0}),
        ("stock.operation_type.list", {"code": ""}),
        ("stock.route.list", {"warehouse_id": True}),
    ],
)
def test_rejects_parameters_outside_the_frozen_contract(
    capability_id: str, parameters: dict
) -> None:
    with pytest.raises(InventoryMasterReadError) as exc_info:
        validate_inventory_master_request(capability_id, request(parameters))
    assert exc_info.value.code == "invalid_request"


@pytest.mark.parametrize(
    ("capability_id", "parameters", "item"),
    [
        (
            "product.category.list",
            {"parent_id": 4},
            {**CAPABILITIES["product.category.list"], "parent_id": 4},
        ),
        (
            "stock.location.list",
            {"warehouse_id": 2, "usage": "internal"},
            CAPABILITIES["stock.location.list"],
        ),
        (
            "stock.operation_type.list",
            {"warehouse_id": 2, "code": "incoming"},
            CAPABILITIES["stock.operation_type.list"],
        ),
        (
            "stock.route.list",
            {"warehouse_id": 2},
            CAPABILITIES["stock.route.list"],
        ),
    ],
)
def test_native_filters_are_normalized_and_checked_against_rows(
    capability_id: str, parameters: dict, item: dict
) -> None:
    port = Port([item])
    assert read_inventory_master(port, capability_id, request(parameters))["items"] == [
        item
    ]
    runtime = port.calls[0]["parameters"]
    for key, value in parameters.items():
        assert runtime[key] == value


def test_rejects_cross_company_and_unordered_rows() -> None:
    cross_company = deepcopy(CAPABILITIES["warehouse.list"])
    cross_company["company_id"] = 2
    with pytest.raises(InventoryMasterReadError) as exc_info:
        read_inventory_master(Port([cross_company]), "warehouse.list", request())
    assert exc_info.value.code == "failed_validation"

    item = CAPABILITIES["product.category.list"]
    with pytest.raises(InventoryMasterReadError) as exc_info:
        read_inventory_master(
            Port([{**item, "id": 8}, {**item, "id": 9}]),
            "product.category.list",
            request(),
        )
    assert exc_info.value.code == "failed_validation"


def test_maps_scope_failures_and_disappearing_cursor() -> None:
    page = {
        "user_id": 5,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": False,
        "cursor_found": True,
        "items": [],
    }

    class FixedPort(Port):
        def read(self, **kwargs: object) -> dict:
            return page

    with pytest.raises(InventoryMasterReadError) as exc_info:
        read_inventory_master(FixedPort([]), "warehouse.list", request())
    assert exc_info.value.code == "unauthorized"

    first = read_inventory_master(
        Port(
            [
                CAPABILITIES["product.category.list"],
                {**CAPABILITIES["product.category.list"], "id": 8},
            ]
        ),
        "product.category.list",
        request({"limit": 1}),
    )
    missing = deepcopy(page)
    missing.update({"access_allowed": True, "cursor_found": False})

    class MissingPort(Port):
        def read(self, **kwargs: object) -> dict:
            return missing

    with pytest.raises(InventoryMasterReadError) as exc_info:
        read_inventory_master(
            MissingPort([]),
            "product.category.list",
            request({"limit": 1, "cursor": first["next_cursor"]}),
        )
    assert exc_info.value.code == "invalid_cursor"
