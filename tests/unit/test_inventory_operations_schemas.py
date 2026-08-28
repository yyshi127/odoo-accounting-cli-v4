from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from referencing import Registry, Resource

from odoo_accounting_cli_v4.registry import load_registry

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas" / "v1"
CAPABILITIES = (
    "stock.transfer.search",
    "stock.transfer.get",
    "stock.move.search",
    "inventory.on_hand.summary",
    "inventory.availability.inspect",
)


def load(name: str) -> dict[str, Any]:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def validator(name: str) -> Draft202012Validator:
    resources: dict[str, Resource[Any]] = {}
    for common in ("request.schema.json", "response.schema.json"):
        schema = load(common)
        resource = Resource.from_contents(schema)
        resources[schema["$id"]] = resource
        resources[common] = resource
    schema = load(name)
    return Draft202012Validator(
        schema,
        registry=Registry().with_resources(resources.items()),
        format_checker=FormatChecker(),
    )


def request(parameters: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "request_id": str(uuid4()),
        "context": {
            "database": "odoo_cli_v4_dev",
            "company_id": 1,
            "user_login": "accountant",
            "language": "en_US",
            "timezone": "UTC",
        },
        "parameters": parameters,
    }


TRANSFER = {
    "id": 9,
    "company_id": 1,
    "name": "WH/MO/00009",
    "origin": "MO001",
    "state": "confirmed",
    "operation_type": {
        "id": 4,
        "code": "mrp_operation",
        "name": "Manufacturing",
    },
    "scheduled_date": "2026-08-28T10:00:00Z",
    "completed_date": None,
    "source_location": {"id": 20, "name": "WH/Stock"},
    "destination_location": {"id": 21, "name": "WH/Production"},
    "partner": None,
}

MOVE = {
    "id": 19,
    "company_id": 1,
    "reference": "WH/MO/00009",
    "description_picking": None,
    "state": "confirmed",
    "date": "2026-08-28T09:00:00Z",
    "transfer": {"id": 9, "name": "WH/MO/00009"},
    "product": {"id": 50, "code": "TEST", "name": "Test product"},
    "uom": {"id": 1, "name": "Units"},
    "demand_quantity": "5",
    "moved_quantity": "0",
    "source_location": {"id": 20, "name": "WH/Stock"},
    "destination_location": {"id": 21, "name": "WH/Production"},
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

PARAMETERS = {
    "stock.transfer.search": {"picking_type_id": 4, "state": "confirmed"},
    "stock.transfer.get": {"transfer_id": 9},
    "stock.move.search": {"transfer_id": 9, "product_id": 50},
    "inventory.on_hand.summary": {
        "warehouse_id": 2,
        "location_id": 20,
        "product_id": 50,
    },
    "inventory.availability.inspect": {"product_id": 50, "location_id": 20},
}

DATA = {
    "stock.transfer.search": {
        "items": [TRANSFER],
        "has_more": False,
        "next_cursor": None,
    },
    "stock.transfer.get": TRANSFER,
    "stock.move.search": {
        "items": [MOVE],
        "has_more": False,
        "next_cursor": None,
    },
    "inventory.on_hand.summary": SUMMARY,
    "inventory.availability.inspect": AVAILABILITY,
}

MODELS = {
    "stock.transfer.search": "stock.picking",
    "stock.transfer.get": "stock.picking",
    "stock.move.search": "stock.move",
    "inventory.on_hand.summary": "stock.quant",
    "inventory.availability.inspect": "product.product",
}


def response(capability_id: str) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "request_id": str(uuid4()),
        "success": True,
        "capability": capability_id,
        "status": "verified",
        "data": deepcopy(DATA[capability_id]),
        "warnings": [],
        "error": None,
        "odoo": {
            "database": "odoo_cli_v4_dev",
            "company_id": 1,
            "user_id": 5,
            "model": MODELS[capability_id],
            "record_ids": [9],
        },
        "audit": {
            "operation_id": None,
            "idempotency_key": None,
            "verification": None,
        },
    }


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_inventory_operation_request_and_response_schemas(
    capability_id: str,
) -> None:
    request_name = f"{capability_id}.request.schema.json"
    response_name = f"{capability_id}.response.schema.json"
    Draft202012Validator.check_schema(load(request_name))
    Draft202012Validator.check_schema(load(response_name))

    validator(request_name).validate(request(PARAMETERS[capability_id]))
    validator(response_name).validate(response(capability_id))


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_request_schemas_reject_arbitrary_query_controls(capability_id: str) -> None:
    document = request({**PARAMETERS[capability_id], "domain": []})
    with pytest.raises(ValidationError):
        validator(f"{capability_id}.request.schema.json").validate(document)


def test_availability_schema_enforces_mutually_exclusive_scopes() -> None:
    document = request({"product_id": 50, "warehouse_id": 2, "location_id": 20})
    with pytest.raises(ValidationError):
        validator("inventory.availability.inspect.request.schema.json").validate(
            document
        )


def test_quantity_schemas_reject_numbers_and_extra_fields() -> None:
    summary = response("inventory.on_hand.summary")
    summary["data"]["groups"][0]["quantity"] = 5
    with pytest.raises(ValidationError):
        validator("inventory.on_hand.summary.response.schema.json").validate(summary)

    move_response = response("stock.move.search")
    move_response["data"]["items"][0]["name"] = "not-an-odoo19-stock-move-field"
    with pytest.raises(ValidationError):
        validator("stock.move.search.response.schema.json").validate(move_response)


def test_project_registry_loads_all_inventory_operation_schema_metadata() -> None:
    registry = load_registry()

    for capability_id in CAPABILITIES:
        descriptor = registry.describe(capability_id)
        registry.load_schema(descriptor["schemas"]["request"])
        registry.load_schema(descriptor["schemas"]["response"])
