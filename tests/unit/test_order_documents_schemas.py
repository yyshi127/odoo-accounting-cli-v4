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
    "sale.order.search",
    "sale.order.get",
    "sale.order.line.search",
    "sale.order.analysis.summary",
    "purchase.order.search",
    "purchase.order.get",
    "purchase.order.line.search",
    "purchase.order.analysis.summary",
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


def _ref(record_id: int, name: str) -> dict[str, Any]:
    return {"id": record_id, "name": name}


def _currency() -> dict[str, Any]:
    return {"id": 6, "code": "CNY"}


SALE_LINE = {
    "id": 101,
    "order": _ref(10, "S00010"),
    "company": _ref(1, "Company"),
    "partner": _ref(31, "Customer"),
    "state": "draft",
    "date_order": "2026-08-28T01:02:03Z",
    "sequence": 10,
    "display_type": None,
    "description": "Product",
    "product": _ref(41, "Product"),
    "uom": _ref(1, "Units"),
    "ordered_quantity": "3",
    "invoiced_quantity": "0",
    "to_invoice_quantity": "3",
    "unit_price": "10",
    "discount_percent": "0",
    "amount_untaxed": "30",
    "amount_tax": "0",
    "amount_total": "30",
    "currency": _currency(),
    "taxes": [],
    "invoice_line_ids": [],
    "stock_move_ids": [],
    "delivered_quantity": "0",
    "to_deliver_quantity": "3",
}

PURCHASE_LINE = {
    **{
        key: deepcopy(value)
        for key, value in SALE_LINE.items()
        if key not in {"delivered_quantity", "to_deliver_quantity"}
    },
    "id": 201,
    "order": _ref(20, "P00020"),
    "partner": _ref(32, "Vendor"),
    "ordered_quantity": "5",
    "to_invoice_quantity": "5",
    "unit_price": "8",
    "amount_untaxed": "40",
    "amount_total": "40",
    "received_quantity": "0",
    "to_receive_quantity": "5",
    "date_planned": "2026-08-29T01:02:03Z",
}

SALE_HEADER = {
    "id": 10,
    "name": "S00010",
    "company": _ref(1, "Company"),
    "partner": _ref(31, "Customer"),
    "state": "draft",
    "date_order": "2026-08-28T01:02:03Z",
    "currency": _currency(),
    "user": _ref(5, "Accountant"),
    "invoice_status": "to invoice",
    "amount_untaxed": "30",
    "amount_tax": "0",
    "amount_total": "30",
    "invoice_ids": [],
    "transfer_ids": [],
    "line_count": 1,
    "validity_date": "2026-09-27",
    "client_order_ref": "CLIENT-1",
    "team": None,
    "delivery_status": None,
}

PURCHASE_HEADER = {
    **{
        key: deepcopy(value)
        for key, value in SALE_HEADER.items()
        if key not in {"validity_date", "client_order_ref", "team", "delivery_status"}
    },
    "id": 20,
    "name": "P00020",
    "partner": _ref(32, "Vendor"),
    "amount_untaxed": "40",
    "amount_total": "40",
    "date_approve": None,
    "partner_ref": "VENDOR-1",
    "origin": None,
    "receipt_status": None,
}

SUMMARY = {
    "company_id": 1,
    "date_from": "2026-01-01",
    "date_to": "2026-12-31",
    "group_by": "partner",
    "groups": [
        {
            "group": {"id": 31, "value": "Customer"},
            "currency": _currency(),
            "order_count": 1,
            "amount_untaxed": "30",
            "amount_tax": "0",
            "amount_total": "30",
        }
    ],
    "totals_by_currency": [
        {
            "currency": _currency(),
            "order_count": 1,
            "amount_untaxed": "30",
            "amount_tax": "0",
            "amount_total": "30",
        }
    ],
}

PARAMETERS = {
    "sale.order.search": {"states": ["draft"], "limit": 10},
    "sale.order.get": {"order_id": 10},
    "sale.order.line.search": {"order_id": 10, "to_deliver_only": True},
    "sale.order.analysis.summary": {
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
        "group_by": "partner",
    },
    "purchase.order.search": {"states": ["draft"], "limit": 10},
    "purchase.order.get": {"order_id": 20},
    "purchase.order.line.search": {"order_id": 20, "to_receive_only": True},
    "purchase.order.analysis.summary": {
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
        "group_by": "partner",
    },
}

DATA = {
    "sale.order.search": {
        "items": [SALE_HEADER],
        "has_more": False,
        "next_cursor": None,
    },
    "sale.order.get": {
        **SALE_HEADER,
        "lines": [SALE_LINE],
        "invoices": [],
        "transfers": [],
    },
    "sale.order.line.search": {
        "items": [SALE_LINE],
        "has_more": False,
        "next_cursor": None,
    },
    "sale.order.analysis.summary": SUMMARY,
    "purchase.order.search": {
        "items": [PURCHASE_HEADER],
        "has_more": False,
        "next_cursor": None,
    },
    "purchase.order.get": {
        **PURCHASE_HEADER,
        "lines": [PURCHASE_LINE],
        "invoices": [],
        "transfers": [],
    },
    "purchase.order.line.search": {
        "items": [PURCHASE_LINE],
        "has_more": False,
        "next_cursor": None,
    },
    "purchase.order.analysis.summary": SUMMARY,
}

MODELS = {
    "sale.order.search": "sale.order",
    "sale.order.get": "sale.order",
    "sale.order.line.search": "sale.order.line",
    "sale.order.analysis.summary": "sale.order",
    "purchase.order.search": "purchase.order",
    "purchase.order.get": "purchase.order",
    "purchase.order.line.search": "purchase.order.line",
    "purchase.order.analysis.summary": "purchase.order",
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
            "record_ids": [10],
        },
        "audit": {
            "operation_id": None,
            "idempotency_key": None,
            "verification": None,
        },
    }


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_order_document_request_and_response_schemas(capability_id: str) -> None:
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


@pytest.mark.parametrize("prefix", ["sale", "purchase"])
def test_summary_schema_requires_date_range_and_group_by(prefix: str) -> None:
    for parameters in (
        {"date_from": "2026-01-01", "date_to": "2026-12-31"},
        {"date_from": "2026-01-01", "group_by": "partner"},
    ):
        with pytest.raises(ValidationError):
            validator(f"{prefix}.order.analysis.summary.request.schema.json").validate(
                request(parameters)
            )


def test_amounts_quantities_and_odoo19_uom_shape_are_closed() -> None:
    sale = response("sale.order.line.search")
    sale["data"]["items"][0]["ordered_quantity"] = 3
    with pytest.raises(ValidationError):
        validator("sale.order.line.search.response.schema.json").validate(sale)

    purchase = response("purchase.order.line.search")
    line = purchase["data"]["items"][0]
    line["product_uom"] = line.pop("uom")
    with pytest.raises(ValidationError):
        validator("purchase.order.line.search.response.schema.json").validate(purchase)


def test_sale_and_purchase_specific_fields_do_not_cross_contracts() -> None:
    sale = response("sale.order.search")
    sale["data"]["items"][0]["receipt_status"] = None
    with pytest.raises(ValidationError):
        validator("sale.order.search.response.schema.json").validate(sale)

    purchase = response("purchase.order.search")
    purchase["data"]["items"][0]["delivery_status"] = None
    with pytest.raises(ValidationError):
        validator("purchase.order.search.response.schema.json").validate(purchase)


def test_summary_keeps_currency_on_every_group_and_total() -> None:
    summary = response("sale.order.analysis.summary")
    del summary["data"]["groups"][0]["currency"]
    with pytest.raises(ValidationError):
        validator("sale.order.analysis.summary.response.schema.json").validate(summary)

    summary = response("purchase.order.analysis.summary")
    del summary["data"]["totals_by_currency"][0]["currency"]
    with pytest.raises(ValidationError):
        validator("purchase.order.analysis.summary.response.schema.json").validate(
            summary
        )
