from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from referencing import Registry, Resource

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas" / "v1"
CAPABILITIES = (
    "sale.order.create",
    "sale.order.update_draft",
    "sale.order.lines.replace",
    "sale.order.confirm",
    "sale.order.cancel",
    "sale.order.reset_to_draft",
    "purchase.order.create",
    "purchase.order.update_draft",
    "purchase.order.lines.replace",
    "purchase.order.confirm",
    "purchase.order.cancel",
    "purchase.order.reset_to_draft",
)

SALE_LINE = {
    "product_id": 51,
    "name": "Sale line",
    "quantity": "3",
    "uom_id": 1,
    "price_unit": "10.5",
    "discount": "0",
    "tax_ids": [8, 9],
}
PURCHASE_LINE = {
    **SALE_LINE,
    "product_id": 52,
    "name": "Purchase line",
    "quantity": "5",
    "price_unit": "8",
    "date_planned": "2026-08-30 02:03:04",
}
PARAMETERS: dict[str, dict[str, Any]] = {
    "sale.order.create": {
        "partner_id": 31,
        "pricelist_id": 41,
        "date_order": "2026-08-28 01:02:03",
        "client_order_ref": "CLIENT-31",
        "validity_date": "2026-09-30",
        "commitment_date": None,
        "payment_term_id": None,
        "lines": [SALE_LINE],
    },
    "sale.order.update_draft": {
        "order_id": 101,
        "changes": {"client_order_ref": "CLIENT-UPDATED"},
    },
    "sale.order.lines.replace": {"order_id": 101, "lines": [SALE_LINE]},
    "sale.order.confirm": {"order_id": 101},
    "sale.order.cancel": {"order_id": 101},
    "sale.order.reset_to_draft": {"order_id": 101},
    "purchase.order.create": {
        "partner_id": 32,
        "currency_id": 6,
        "picking_type_id": 2,
        "date_order": "2026-08-28 01:02:03",
        "partner_ref": "VENDOR-32",
        "payment_term_id": None,
        "incoterm_id": None,
        "lines": [PURCHASE_LINE],
    },
    "purchase.order.update_draft": {
        "order_id": 201,
        "changes": {"date_order": "2026-08-29 01:02:03"},
    },
    "purchase.order.lines.replace": {"order_id": 201, "lines": [PURCHASE_LINE]},
    "purchase.order.confirm": {"order_id": 201},
    "purchase.order.cancel": {"order_id": 201},
    "purchase.order.reset_to_draft": {"order_id": 201},
}


def load(name: str) -> dict[str, Any]:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def validator(name: str) -> Draft202012Validator:
    resource_names = {
        "request.schema.json",
        "response.schema.json",
        "core-write-result.schema.json",
        "sale.order.create.request.schema.json",
        "sale.order.confirm.request.schema.json",
        "purchase.order.create.request.schema.json",
        "purchase.order.confirm.request.schema.json",
    }
    resources: dict[str, Resource[Any]] = {}
    for resource_name in resource_names:
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
        "request_id": str(uuid4()),
        "context": {
            "database": "v4-dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": deepcopy(parameters),
    }


def _state(capability_id: str) -> str:
    if capability_id == "sale.order.confirm":
        return "sale"
    if capability_id == "purchase.order.confirm":
        return "to approve"
    if capability_id.endswith(".cancel"):
        return "cancel"
    return "draft"


def response(capability_id: str) -> dict[str, Any]:
    sale = capability_id.startswith("sale.order.")
    parameters = PARAMETERS[capability_id]
    record_id = 901 if capability_id.endswith(".create") else parameters["order_id"]
    line_count = len(parameters.get("lines", [None]))
    model = "sale.order" if sale else "purchase.order"
    return {
        "schema_version": "v1",
        "request_id": str(uuid4()),
        "success": True,
        "capability": capability_id,
        "status": "verified",
        "data": {
            "idempotent_replay": False,
            "result": {
                "model": model,
                "id": record_id,
                "name": "S00901" if sale else "P00901",
                "state": _state(capability_id),
                "company_id": 7,
                "move_type": None,
                "source_id": 31 if sale else 32,
                "line_ids": list(range(501, 501 + line_count)),
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
            "idempotency_key": "order-write-safe-key",
            "verification": None,
        },
    }


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_all_24_order_write_schemas_parse_and_accept_closed_examples(
    capability_id: str,
) -> None:
    request_name = f"{capability_id}.request.schema.json"
    response_name = f"{capability_id}.response.schema.json"
    Draft202012Validator.check_schema(load(request_name))
    Draft202012Validator.check_schema(load(response_name))
    validator(request_name).validate(request(PARAMETERS[capability_id]))
    validator(response_name).validate(response(capability_id))


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_requests_reject_arbitrary_orm_controls(capability_id: str) -> None:
    document = request({**PARAMETERS[capability_id], "sudo": True})
    with pytest.raises(ValidationError):
        validator(f"{capability_id}.request.schema.json").validate(document)


@pytest.mark.parametrize(
    ("capability_id", "path", "invalid"),
    (
        ("sale.order.create", ("date_order",), "2026-08-28T01:02:03Z"),
        ("sale.order.create", ("validity_date",), "2026-02-30"),
        ("sale.order.create", ("lines", 0, "quantity"), "0"),
        ("sale.order.create", ("lines", 0, "price_unit"), "-1"),
        ("sale.order.create", ("lines", 0, "price_unit"), "10.50"),
        ("sale.order.create", ("lines", 0, "discount"), "101"),
        ("sale.order.create", ("lines", 0, "tax_ids"), [8, 8]),
        ("purchase.order.create", ("lines", 0, "date_planned"), "2026-08-30"),
        ("purchase.order.update_draft", ("changes", "date_order"), "bad"),
    ),
)
def test_request_schemas_reject_bad_dates_datetimes_and_decimals(
    capability_id: str, path: tuple[Any, ...], invalid: Any
) -> None:
    parameters = deepcopy(PARAMETERS[capability_id])
    target: Any = parameters
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = invalid
    with pytest.raises(ValidationError):
        validator(f"{capability_id}.request.schema.json").validate(request(parameters))


def test_sale_and_purchase_line_shapes_do_not_cross() -> None:
    sale = deepcopy(PARAMETERS["sale.order.lines.replace"])
    sale["lines"][0]["date_planned"] = "2026-08-30 02:03:04"
    with pytest.raises(ValidationError):
        validator("sale.order.lines.replace.request.schema.json").validate(request(sale))

    purchase = deepcopy(PARAMETERS["purchase.order.lines.replace"])
    del purchase["lines"][0]["date_planned"]
    with pytest.raises(ValidationError):
        validator("purchase.order.lines.replace.request.schema.json").validate(
            request(purchase)
        )


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_response_schema_closes_capability_status_and_result_shape(
    capability_id: str,
) -> None:
    schema = validator(f"{capability_id}.response.schema.json")
    wrong_capability = response(capability_id)
    wrong_capability["capability"] = "invoice.post"
    with pytest.raises(ValidationError):
        schema.validate(wrong_capability)

    wrong_status = response(capability_id)
    wrong_status["status"] = "completed"
    with pytest.raises(ValidationError):
        schema.validate(wrong_status)

    malformed = response(capability_id)
    del malformed["data"]["result"]["company_id"]
    with pytest.raises(ValidationError):
        schema.validate(malformed)
