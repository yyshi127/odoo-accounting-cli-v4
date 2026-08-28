from __future__ import annotations

import io
import json
from functools import partial
from typing import Any

import pytest

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4.capabilities.inventory_master import (
    InventoryMasterReadError,
    validate_inventory_master_request,
)
from odoo_accounting_cli_v4.capabilities.inventory_operations import (
    InventoryOperationsReadError,
    validate_inventory_operations_request,
)
from odoo_accounting_cli_v4.registry import load_registry

CAPABILITIES = {
    "product.category.list": ("product_category_list", "product.category", [11]),
    "warehouse.list": ("warehouse_list", "stock.warehouse", [12]),
    "stock.location.list": ("stock_location_list", "stock.location", [13]),
    "stock.operation_type.list": (
        "stock_operation_type_list",
        "stock.picking.type",
        [14],
    ),
    "stock.route.list": ("stock_route_list", "stock.route", [15]),
    "stock.transfer.search": ("stock_transfer_search", "stock.picking", [16]),
    "stock.transfer.get": ("stock_transfer_get", "stock.picking", [16]),
    "stock.move.search": ("stock_move_search", "stock.move", [17]),
    "inventory.on_hand.summary": (
        "inventory_on_hand_summary",
        "stock.quant",
        [],
    ),
    "inventory.availability.inspect": (
        "inventory_availability_inspect",
        "product.product",
        [50],
    ),
}
MASTER_CAPABILITIES = frozenset(
    {
        "product.category.list",
        "warehouse.list",
        "stock.location.list",
        "stock.operation_type.list",
        "stock.route.list",
    }
)
PAGED_CAPABILITIES = MASTER_CAPABILITIES | {
    "stock.transfer.search",
    "stock.move.search",
}
PARAMETERS = {
    "product.category.list": {"parent_id": None, "limit": 1},
    "warehouse.list": {"active": True, "limit": 1},
    "stock.location.list": {
        "active": True,
        "warehouse_id": 12,
        "usage": "internal",
        "limit": 1,
    },
    "stock.operation_type.list": {
        "active": True,
        "warehouse_id": 12,
        "code": "incoming",
        "limit": 1,
    },
    "stock.route.list": {"active": True, "warehouse_id": 12, "limit": 1},
    "stock.transfer.search": {
        "picking_type_id": 14,
        "partner_id": 22,
        "state": "draft",
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
        "limit": 1,
    },
    "stock.transfer.get": {"transfer_id": 16},
    "stock.move.search": {
        "transfer_id": 16,
        "product_id": 50,
        "state": "draft",
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
        "limit": 1,
    },
    "inventory.on_hand.summary": {
        "warehouse_id": 12,
        "location_id": 13,
        "product_id": 50,
    },
    "inventory.availability.inspect": {"product_id": 50, "location_id": 13},
}
RUNTIME_PARAMETERS = {
    "product.category.list": {"parent_id": None, "after": None, "limit": 2},
    "warehouse.list": {"active": True, "after": None, "limit": 2},
    "stock.location.list": {
        "active": True,
        "warehouse_id": 12,
        "usage": "internal",
        "after": None,
        "limit": 2,
    },
    "stock.operation_type.list": {
        "active": True,
        "warehouse_id": 12,
        "code": "incoming",
        "after": None,
        "limit": 2,
    },
    "stock.route.list": {
        "active": True,
        "warehouse_id": 12,
        "after": None,
        "limit": 2,
    },
    "stock.transfer.search": {
        "picking_type_id": 14,
        "partner_id": 22,
        "state": "draft",
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
        "after": None,
        "limit": 2,
    },
    "stock.transfer.get": {"transfer_id": 16},
    "stock.move.search": {
        "transfer_id": 16,
        "product_id": 50,
        "state": "draft",
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
        "after": None,
        "limit": 2,
    },
    "inventory.on_hand.summary": {
        "warehouse_id": 12,
        "location_id": 13,
        "product_id": 50,
    },
    "inventory.availability.inspect": {
        "product_id": 50,
        "warehouse_id": None,
        "location_id": 13,
    },
}


def _request(parameters: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "request_id": "395d3a83-ae0f-4fa1-ac70-f11d61d41097",
        "context": {
            "database": "v4-dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": parameters,
    }


REQUESTS = {
    capability_id: _request(parameters)
    for capability_id, parameters in PARAMETERS.items()
}


def _named(record_id: int, name: str) -> dict[str, Any]:
    return {"id": record_id, "name": name}


def _coded(record_id: int, code: str, name: str) -> dict[str, Any]:
    return {"id": record_id, "code": code, "name": name}


def _product() -> dict[str, Any]:
    return {"id": 50, "code": "SKU-50", "name": "Inventory Product"}


def _transfer() -> dict[str, Any]:
    return {
        "id": 16,
        "company_id": 7,
        "name": "WH/IN/00016",
        "origin": "PO00016",
        "state": "draft",
        "operation_type": _coded(14, "incoming", "Receipts"),
        "scheduled_date": "2026-06-30T08:00:00Z",
        "completed_date": None,
        "source_location": _named(20, "Partner Locations/Vendors"),
        "destination_location": _named(13, "WH/Stock"),
        "partner": _named(22, "Supplier"),
    }


def _item(capability_id: str) -> dict[str, Any]:
    if capability_id == "product.category.list":
        return {
            "id": 11,
            "name": "All",
            "complete_name": "All",
            "parent_id": None,
        }
    if capability_id == "warehouse.list":
        return {
            "id": 12,
            "name": "Main Warehouse",
            "code": "WH",
            "active": True,
            "company_id": 7,
            "reception_steps": "one_step",
            "delivery_steps": "ship_only",
        }
    if capability_id == "stock.location.list":
        return {
            "id": 13,
            "name": "Stock",
            "complete_name": "WH/Stock",
            "active": True,
            "usage": "internal",
            "company_id": 7,
            "parent_id": 21,
            "warehouse_id": 12,
        }
    if capability_id == "stock.operation_type.list":
        return {
            "id": 14,
            "name": "Receipts",
            "active": True,
            "code": "incoming",
            "sequence_code": "IN",
            "company_id": 7,
            "warehouse_id": 12,
            "source_location_id": 20,
            "destination_location_id": 13,
        }
    if capability_id == "stock.route.list":
        return {
            "id": 15,
            "name": "Buy",
            "active": True,
            "sequence": 10,
            "company_id": 7,
            "product_selectable": True,
            "product_category_selectable": True,
            "warehouse_selectable": True,
            "warehouse_ids": [12],
        }
    if capability_id in {"stock.transfer.search", "stock.transfer.get"}:
        return _transfer()
    if capability_id == "stock.move.search":
        return {
            "id": 17,
            "company_id": 7,
            "reference": "WH/IN/00016",
            "description_picking": None,
            "state": "draft",
            "date": "2026-06-30T08:00:00Z",
            "transfer": _named(16, "WH/IN/00016"),
            "product": _product(),
            "uom": _named(1, "Units"),
            "demand_quantity": "2",
            "moved_quantity": "0",
            "source_location": _named(20, "Partner Locations/Vendors"),
            "destination_location": _named(13, "WH/Stock"),
        }
    if capability_id == "inventory.on_hand.summary":
        return {
            "company_id": 7,
            "warehouse": _coded(12, "WH", "Main Warehouse"),
            "location": _named(13, "WH/Stock"),
            "groups": [
                {
                    "product": _product(),
                    "uom": _named(1, "Units"),
                    "quantity": "5",
                    "reserved_quantity": "0",
                    "available_quantity": "5",
                }
            ],
        }
    if capability_id == "inventory.availability.inspect":
        return {
            "company_id": 7,
            "product": _product(),
            "warehouse": None,
            "location": _named(13, "WH/Stock"),
            "uom": _named(1, "Units"),
            "on_hand_quantity": "5",
            "free_quantity": "5",
            "incoming_quantity": "2",
            "outgoing_quantity": "0",
            "forecast_quantity": "7",
        }
    raise AssertionError(capability_id)


class _SuccessPort:
    user_id = 42

    def __init__(self, capability_id: str) -> None:
        self.capability_id = capability_id
        self.calls: list[dict[str, Any]] = []

    def read(
        self,
        *,
        capability_id: str,
        company_id: int,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "capability_id": capability_id,
                "company_id": company_id,
                "parameters": parameters,
            }
        )
        return {
            "user_id": self.user_id,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "cursor_found": True,
            "items": [_item(self.capability_id)],
        }


class _ErrorPort:
    user_id = 42

    def __init__(self, error: Exception) -> None:
        self.error = error

    def read(self, **_kwargs: Any) -> dict[str, Any]:
        raise self.error


def _assert_partial(value: object, function: object, capability_id: str) -> None:
    assert isinstance(value, partial)
    assert value.func is function
    assert value.args == (capability_id,)


@pytest.fixture(scope="module")
def registry() -> Any:
    return load_registry()


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_inventory_read_cli_uses_fixed_handler_validator_and_model(
    capability_id: str, registry: Any
) -> None:
    handler_key, model, _record_ids = CAPABILITIES[capability_id]
    descriptor = registry.describe(capability_id)
    validator = (
        validate_inventory_master_request
        if capability_id in MASTER_CAPABILITIES
        else validate_inventory_operations_request
    )

    assert descriptor["handler_key"] == handler_key
    assert callable(cli._HANDLERS[handler_key])
    _assert_partial(cli._REQUEST_VALIDATORS[handler_key], validator, capability_id)
    assert cli._CAPABILITY_MODELS[capability_id] == model


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_inventory_read_cli_emits_schema_valid_success_and_exact_odoo_metadata(
    capability_id: str, registry: Any
) -> None:
    port = _SuccessPort(capability_id)

    def port_factory(selected: str, request: dict[str, Any]) -> _SuccessPort:
        assert selected == capability_id
        assert request == REQUESTS[capability_id]
        return port

    stdout = io.StringIO()
    stderr = io.StringIO()
    exit_code = cli.main(
        ["read", capability_id, "--request", "-"],
        stdin=io.StringIO(json.dumps(REQUESTS[capability_id])),
        stdout=stdout,
        stderr=stderr,
        port_factory=port_factory,
    )

    document = json.loads(stdout.getvalue())
    item = _item(capability_id)
    data = (
        {"items": [item], "has_more": False, "next_cursor": None}
        if capability_id in PAGED_CAPABILITIES
        else item
    )
    _handler_key, model, record_ids = CAPABILITIES[capability_id]
    assert exit_code == 0
    assert stderr.getvalue() == ""
    assert port.calls == [
        {
            "capability_id": capability_id,
            "company_id": 7,
            "parameters": RUNTIME_PARAMETERS[capability_id],
        }
    ]
    assert document["success"] is True
    assert document["capability"] == capability_id
    assert document["status"] == "verified"
    assert document["data"] == data
    assert document["odoo"] == {
        "database": "v4-dev",
        "company_id": 7,
        "user_id": 42,
        "model": model,
        "record_ids": record_ids,
    }
    registry.validate_instance(
        registry.describe(capability_id)["schemas"]["response"], document
    )


@pytest.mark.parametrize(
    ("capability_id", "error_type", "code", "exit_code", "status"),
    [
        (
            "warehouse.list",
            InventoryMasterReadError,
            "unauthorized",
            3,
            "denied",
        ),
        (
            "stock.transfer.get",
            InventoryOperationsReadError,
            "record_not_found",
            4,
            "unavailable",
        ),
    ],
)
def test_inventory_read_cli_maps_capability_errors_with_verified_odoo_metadata(
    capability_id: str,
    error_type: type[Exception],
    code: str,
    exit_code: int,
    status: str,
    registry: Any,
) -> None:
    port = _ErrorPort(error_type(code, "expected inventory error", exit_code=exit_code))
    stdout = io.StringIO()
    stderr = io.StringIO()

    actual_exit = cli.main(
        ["read", capability_id, "--request", "-"],
        stdin=io.StringIO(json.dumps(REQUESTS[capability_id])),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda selected, request: port,
    )

    document = json.loads(stdout.getvalue())
    assert actual_exit == exit_code
    assert stderr.getvalue() == ""
    assert document["success"] is False
    assert document["status"] == status
    assert document["error"]["code"] == code
    assert document["odoo"] == {
        "database": "v4-dev",
        "company_id": 7,
        "user_id": 42,
        "model": CAPABILITIES[capability_id][1],
        "record_ids": [],
    }
    registry.validate_instance(
        registry.describe(capability_id)["schemas"]["response"], document
    )


def test_inventory_read_cli_rejects_semantic_date_range_before_port_creation(
    registry: Any,
) -> None:
    capability_id = "stock.transfer.search"
    request = _request({"date_from": "2026-12-31", "date_to": "2026-01-01", "limit": 1})
    called = False

    def port_factory(_selected: str, _request: dict[str, Any]) -> object:
        nonlocal called
        called = True
        return _SuccessPort(capability_id)

    stdout = io.StringIO()
    stderr = io.StringIO()
    exit_code = cli.main(
        ["read", capability_id, "--request", "-"],
        stdin=io.StringIO(json.dumps(request)),
        stdout=stdout,
        stderr=stderr,
        port_factory=port_factory,
    )

    document = json.loads(stdout.getvalue())
    assert exit_code == 2
    assert stderr.getvalue() == ""
    assert called is False
    assert document["error"]["code"] == "invalid_request"
    registry.validate_instance(
        registry.describe(capability_id)["schemas"]["response"], document
    )
