from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError
from referencing import Registry, Resource

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas" / "v1"
CAPABILITIES = (
    "product.category.list",
    "warehouse.list",
    "stock.location.list",
    "stock.operation_type.list",
    "stock.route.list",
)
ITEMS = {
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


def load(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def validator(name: str) -> Draft202012Validator:
    resources = {}
    for common in ("request.schema.json", "response.schema.json"):
        schema = load(common)
        resources[schema["$id"]] = Resource.from_contents(schema)
        resources[common] = Resource.from_contents(schema)
    schema = load(name)
    return Draft202012Validator(
        schema,
        registry=Registry().with_resources(resources.items()),
        format_checker=FormatChecker(),
    )


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_inventory_master_schemas_are_draft_2020_12_and_accept_envelopes(
    capability_id: str,
) -> None:
    request_schema = load(f"{capability_id}.request.schema.json")
    response_schema = load(f"{capability_id}.response.schema.json")
    Draft202012Validator.check_schema(request_schema)
    Draft202012Validator.check_schema(response_schema)

    parameters = {} if capability_id == "product.category.list" else {"active": None}
    validator(f"{capability_id}.request.schema.json").validate(
        {
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
    )


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_request_schemas_reject_unknown_parameters(capability_id: str) -> None:
    with pytest.raises(ValidationError):
        validator(f"{capability_id}.request.schema.json").validate(
            {
                "schema_version": "v1",
                "request_id": str(uuid4()),
                "context": {
                    "database": "db",
                    "company_id": 1,
                    "user_login": "user",
                    "language": "en_US",
                    "timezone": "UTC",
                },
                "parameters": {"name": "WH"},
            }
        )


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_response_schemas_accept_the_frozen_item_shape(capability_id: str) -> None:
    request_id = str(uuid4())
    validator(f"{capability_id}.response.schema.json").validate(
        {
            "schema_version": "v1",
            "request_id": request_id,
            "success": True,
            "capability": capability_id,
            "status": "verified",
            "data": {
                "items": [ITEMS[capability_id]],
                "has_more": False,
                "next_cursor": None,
            },
            "warnings": [],
            "error": None,
            "odoo": {
                "database": "odoo_cli_v4_dev",
                "company_id": 1,
                "user_id": 5,
                "model": None,
                "record_ids": [9],
            },
            "audit": {
                "operation_id": None,
                "idempotency_key": None,
                "verification": None,
            },
        }
    )
