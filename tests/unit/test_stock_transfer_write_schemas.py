from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from referencing import Registry, Resource

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas" / "v1"
CAPABILITY_IDS = (
    "sale.order.invoice.create",
    "stock.transfer.create",
    "stock.transfer.confirm",
    "stock.transfer.assign",
    "stock.transfer.quantities.set",
    "stock.transfer.validate",
    "stock.transfer.unreserve",
    "stock.transfer.cancel",
)
PARAMETERS: dict[str, dict[str, Any]] = {
    "sale.order.invoice.create": {"order_id": 101},
    "stock.transfer.create": {
        "picking_type_id": 2,
        "location_id": 8,
        "location_dest_id": 9,
        "partner_id": None,
        "scheduled_date": "2026-08-30 08:00:00",
        "origin": "CLI transfer",
        "moves": [
            {
                "product_id": 51,
                "name": "Stock item",
                "quantity": "3",
                "uom_id": 1,
            }
        ],
    },
    "stock.transfer.confirm": {"transfer_id": 401},
    "stock.transfer.assign": {"transfer_id": 401},
    "stock.transfer.quantities.set": {
        "transfer_id": 401,
        "lines": [{"move_id": 501, "quantity": "2.5"}],
    },
    "stock.transfer.validate": {
        "transfer_id": 401,
        "backorder_policy": "create",
    },
    "stock.transfer.unreserve": {"transfer_id": 401},
    "stock.transfer.cancel": {"transfer_id": 401},
}


def load(name: str) -> dict[str, Any]:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def validator(name: str) -> Draft202012Validator:
    resources: dict[str, Resource[Any]] = {}
    for resource_name in (
        "request.schema.json",
        "response.schema.json",
        "core-write-result.schema.json",
    ):
        schema = load(resource_name)
        resource = Resource.from_contents(schema)
        resources[schema["$id"]] = resource
        resources[resource_name] = resource
    return Draft202012Validator(
        load(name),
        registry=Registry().with_resources(resources.items()),
        format_checker=FormatChecker(),
    )


def request(parameters: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "request_id": "7bc39413-0d69-4092-9319-795d33f3167c",
        "context": {
            "database": "v4-dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": deepcopy(parameters),
    }


def response(capability_id: str) -> dict[str, Any]:
    invoice = capability_id == "sale.order.invoice.create"
    create = capability_id == "stock.transfer.create"
    state = {
        "sale.order.invoice.create": "draft",
        "stock.transfer.create": "draft",
        "stock.transfer.confirm": "confirmed",
        "stock.transfer.assign": "assigned",
        "stock.transfer.quantities.set": "assigned",
        "stock.transfer.validate": "done",
        "stock.transfer.unreserve": "confirmed",
        "stock.transfer.cancel": "cancel",
    }[capability_id]
    record_id = 907 if invoice else 908 if create else 401
    model = "account.move" if invoice else "stock.picking"
    return {
        "schema_version": "v1",
        "request_id": "7bc39413-0d69-4092-9319-795d33f3167c",
        "success": True,
        "capability": capability_id,
        "status": "verified",
        "data": {
            "idempotent_replay": False,
            "result": {
                "model": model,
                "id": record_id,
                "name": "INV/2026/00907" if invoice else "WH/INT/00908",
                "state": state,
                "company_id": 7,
                "move_type": "out_invoice" if invoice else None,
                "source_id": 101 if invoice else 2,
                "line_ids": [501],
                "partial_reconcile_ids": [],
                "full_reconcile_id": None,
                "reconciled": False,
            },
        },
        "warnings": [],
        "error": None,
        "odoo": {
            "database": "v4-dev",
            "company_id": 7,
            "user_id": 42,
            "model": model,
            "record_ids": [record_id],
        },
        "audit": {
            "operation_id": None,
            "idempotency_key": "stock-transfer-write-key",
            "verification": None,
        },
    }


@pytest.mark.parametrize("capability_id", CAPABILITY_IDS)
def test_all_sixteen_schemas_parse_and_accept_closed_examples(
    capability_id: str,
) -> None:
    request_name = f"{capability_id}.request.schema.json"
    response_name = f"{capability_id}.response.schema.json"
    Draft202012Validator.check_schema(load(request_name))
    Draft202012Validator.check_schema(load(response_name))
    validator(request_name).validate(request(PARAMETERS[capability_id]))
    validator(response_name).validate(response(capability_id))


@pytest.mark.parametrize("capability_id", CAPABILITY_IDS)
def test_each_request_schema_rejects_open_envelopes_and_parameters(
    capability_id: str,
) -> None:
    schema = validator(f"{capability_id}.request.schema.json")
    extra_parameter = request({**PARAMETERS[capability_id], "sudo": True})
    with pytest.raises(ValidationError):
        schema.validate(extra_parameter)
    extra_envelope = request(PARAMETERS[capability_id])
    extra_envelope["rpc_method"] = "execute_kw"
    with pytest.raises(ValidationError):
        schema.validate(extra_envelope)


@pytest.mark.parametrize("capability_id", CAPABILITY_IDS)
def test_each_response_schema_binds_capability_and_core_result(
    capability_id: str,
) -> None:
    schema = validator(f"{capability_id}.response.schema.json")
    wrong_capability = response(capability_id)
    wrong_capability["capability"] = "invoice.post"
    with pytest.raises(ValidationError):
        schema.validate(wrong_capability)
    malformed = response(capability_id)
    del malformed["data"]["result"]["company_id"]
    with pytest.raises(ValidationError):
        schema.validate(malformed)


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    (
        ("sale.order.invoice.create", {"order_id": 0}),
        (
            "stock.transfer.create",
            {**PARAMETERS["stock.transfer.create"], "scheduled_date": "2026-08-30"},
        ),
        (
            "stock.transfer.create",
            {**PARAMETERS["stock.transfer.create"], "origin": " padded "},
        ),
        (
            "stock.transfer.create",
            {**PARAMETERS["stock.transfer.create"], "moves": []},
        ),
        (
            "stock.transfer.create",
            {
                **PARAMETERS["stock.transfer.create"],
                "moves": [
                    {
                        "product_id": 51,
                        "name": "Stock item",
                        "quantity": "0",
                        "uom_id": 1,
                    }
                ],
            },
        ),
        ("stock.transfer.assign", {"transfer_id": 0}),
        (
            "stock.transfer.quantities.set",
            {"transfer_id": 401, "lines": []},
        ),
        (
            "stock.transfer.quantities.set",
            {"transfer_id": 401, "lines": [{"move_id": 501, "quantity": "-1"}]},
        ),
        (
            "stock.transfer.validate",
            {"transfer_id": 401, "backorder_policy": "ask"},
        ),
    ),
)
def test_request_schemas_reject_invalid_ids_dates_decimals_and_enums(
    capability_id: str, parameters: dict[str, Any]
) -> None:
    with pytest.raises(ValidationError):
        validator(f"{capability_id}.request.schema.json").validate(request(parameters))


@pytest.mark.parametrize(
    ("capability_id", "field", "item"),
    (
        (
            "stock.transfer.create",
            "moves",
            {"product_id": 51, "name": "Stock item", "quantity": "1", "uom_id": 1},
        ),
        (
            "stock.transfer.quantities.set",
            "lines",
            {"move_id": 501, "quantity": "1"},
        ),
    ),
)
def test_request_arrays_reject_more_than_two_hundred_items(
    capability_id: str, field: str, item: dict[str, Any]
) -> None:
    parameters = deepcopy(PARAMETERS[capability_id])
    parameters[field] = [item] * 201
    with pytest.raises(ValidationError):
        validator(f"{capability_id}.request.schema.json").validate(request(parameters))


def test_nullable_stock_transfer_create_fields_remain_explicitly_nullable() -> None:
    parameters = deepcopy(PARAMETERS["stock.transfer.create"])
    parameters.update(partner_id=None, scheduled_date=None, origin=None)
    validator("stock.transfer.create.request.schema.json").validate(request(parameters))
