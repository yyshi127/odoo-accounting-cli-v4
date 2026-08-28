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
    "purchase.order.bill.create",
    "purchase_bill.match",
    "purchase_bill.lines.unmatch",
)
PARAMETERS: dict[str, dict[str, Any]] = {
    "purchase.order.bill.create": {"order_id": 41},
    "purchase_bill.match": {
        "bill_id": 51,
        "pairs": [{"bill_line_id": 501, "purchase_line_id": 601}],
    },
    "purchase_bill.lines.unmatch": {"bill_id": 51, "bill_line_ids": [501, 502]},
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


def response(capability_id: str) -> dict[str, Any]:
    parameters = PARAMETERS[capability_id]
    record_id = 52 if capability_id == "purchase.order.bill.create" else 51
    source_id = parameters.get("order_id")
    return {
        "schema_version": "v1",
        "request_id": str(uuid4()),
        "success": True,
        "capability": capability_id,
        "status": "verified",
        "data": {
            "idempotent_replay": False,
            "result": {
                "model": "account.move",
                "id": record_id,
                "name": "BILL/2026/00051",
                "state": "draft",
                "company_id": 7,
                "move_type": "in_invoice",
                "source_id": source_id,
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
            "model": "account.move",
            "record_ids": [record_id],
        },
        "audit": {
            "operation_id": None,
            "idempotency_key": "procurement-write-key",
            "verification": None,
        },
    }


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_all_six_procurement_schemas_parse_and_accept_closed_examples(
    capability_id: str,
) -> None:
    request_name = f"{capability_id}.request.schema.json"
    response_name = f"{capability_id}.response.schema.json"
    Draft202012Validator.check_schema(load(request_name))
    Draft202012Validator.check_schema(load(response_name))
    validator(request_name).validate(request(PARAMETERS[capability_id]))
    validator(response_name).validate(response(capability_id))


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_requests_are_closed_at_envelope_and_parameter_levels(
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


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    (
        ("purchase.order.bill.create", {"order_id": 0}),
        ("purchase_bill.match", {"bill_id": 51, "pairs": []}),
        (
            "purchase_bill.match",
            {
                "bill_id": 51,
                "pairs": [{"bill_line_id": 0, "purchase_line_id": 601}],
            },
        ),
        (
            "purchase_bill.match",
            {
                "bill_id": 51,
                "pairs": [
                    {
                        "bill_line_id": 501,
                        "purchase_line_id": 601,
                        "price": "10",
                    }
                ],
            },
        ),
        ("purchase_bill.lines.unmatch", {"bill_id": 51, "bill_line_ids": []}),
        (
            "purchase_bill.lines.unmatch",
            {"bill_id": 51, "bill_line_ids": [501, 501]},
        ),
        ("purchase_bill.lines.unmatch", {"bill_id": 0, "bill_line_ids": [501]}),
    ),
)
def test_requests_reject_invalid_ids_empty_lists_duplicates_and_nested_extras(
    capability_id: str, parameters: dict[str, Any]
) -> None:
    with pytest.raises(ValidationError):
        validator(f"{capability_id}.request.schema.json").validate(request(parameters))


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_response_schemas_close_capability_status_and_core_result(
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

    missing_result_field = response(capability_id)
    del missing_result_field["data"]["result"]["company_id"]
    with pytest.raises(ValidationError):
        schema.validate(missing_result_field)

    extra_result_field = response(capability_id)
    extra_result_field["data"]["result"]["sudo"] = True
    with pytest.raises(ValidationError):
        schema.validate(extra_result_field)
