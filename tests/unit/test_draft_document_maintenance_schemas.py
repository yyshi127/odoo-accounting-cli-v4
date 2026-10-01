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
    "invoice.line.create",
    "invoice.line.update",
    "invoice.line.delete",
    "invoice.delete",
    "journal_entry.duplicate",
    "journal_entry.delete",
)

INVOICE_LINE = {
    "name": "Consulting services",
    "product_id": None,
    "account_id": 401,
    "quantity": "2",
    "price_unit": "125.50",
    "discount": "0",
    "tax_ids": [5],
    "analytic_distribution": {"31": "100"},
    "deferred_start_date": "2026-09-01",
    "deferred_end_date": "2026-09-30",
}

PARAMETERS: dict[str, dict[str, Any]] = {
    "invoice.line.create": {"move_id": 101, "line": INVOICE_LINE},
    "invoice.line.update": {
        "move_id": 101,
        "line_id": 701,
        "changes": {
            "quantity": "3",
            "deferred_start_date": None,
            "deferred_end_date": None,
        },
    },
    "invoice.line.delete": {"move_id": 101, "line_id": 701},
    "invoice.delete": {"move_id": 101},
    "journal_entry.duplicate": {"move_id": 201},
    "journal_entry.delete": {"move_id": 201},
}


def load(name: str) -> dict[str, Any]:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def validator(name: str) -> Draft202012Validator:
    resource_names = {
        "request.schema.json",
        "response.schema.json",
        "core-write-result.schema.json",
        "invoice.lines.replace.request.schema.json",
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
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": deepcopy(parameters),
    }


def response(capability_id: str) -> dict[str, Any]:
    line_action = capability_id.startswith("invoice.line.")
    duplicate = capability_id == "journal_entry.duplicate"
    delete = capability_id.endswith(".delete")
    record_id = 701 if line_action else 901 if duplicate else PARAMETERS[capability_id]["move_id"]
    move_type = "out_invoice" if capability_id.startswith("invoice.") else "entry"
    model = "account.move.line" if line_action else "account.move"
    source_id = 101 if line_action else 201 if duplicate else None
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
                "name": "Consulting services" if line_action else "Draft move",
                "state": "deleted" if delete else "draft",
                "company_id": 7,
                "move_type": move_type,
                "source_id": source_id,
                "line_ids": [701],
                "partial_reconcile_ids": [],
                "full_reconcile_id": None,
                "reconciled": False,
            },
        },
        "warnings": [],
        "error": None,
        "odoo": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_id": 42,
            "model": model,
            "record_ids": [record_id],
        },
        "audit": {
            "operation_id": None,
            "idempotency_key": "draft-document-maintenance-key",
            "verification": None,
        },
    }


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_all_twelve_schemas_are_valid_and_accept_closed_examples(
    capability_id: str,
) -> None:
    request_name = f"{capability_id}.request.schema.json"
    response_name = f"{capability_id}.response.schema.json"
    request_schema = load(request_name)
    response_schema = load(response_name)

    Draft202012Validator.check_schema(request_schema)
    Draft202012Validator.check_schema(response_schema)
    assert request_schema["$id"].endswith(f"/{request_name}")
    assert response_schema["$id"].endswith(f"/{response_name}")
    validator(request_name).validate(request(PARAMETERS[capability_id]))
    validator(response_name).validate(response(capability_id))


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_requests_reject_arbitrary_orm_controls(capability_id: str) -> None:
    document = request({**PARAMETERS[capability_id], "sudo": True})
    with pytest.raises(ValidationError):
        validator(f"{capability_id}.request.schema.json").validate(document)


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    (
        (
            "invoice.line.create",
            {
                "move_id": 101,
                "line": {key: value for key, value in INVOICE_LINE.items() if key != "tax_ids"},
            },
        ),
        (
            "invoice.line.create",
            {"move_id": 101, "line": {**INVOICE_LINE, "display_type": "tax"}},
        ),
        ("invoice.line.update", {"move_id": 101, "line_id": 701, "changes": {}}),
        (
            "invoice.line.update",
            {"move_id": 101, "line_id": 701, "changes": {"sequence": 20}},
        ),
        (
            "invoice.line.update",
            {
                "move_id": 101,
                "line_id": 701,
                "changes": {"deferred_start_date": "2026-09-01"},
            },
        ),
        (
            "invoice.line.update",
            {
                "move_id": 101,
                "line_id": 701,
                "changes": {
                    "deferred_start_date": "2026-09-01",
                    "deferred_end_date": None,
                },
            },
        ),
    ),
)
def test_invoice_line_requests_reject_incomplete_or_system_line_shapes(
    capability_id: str, parameters: dict[str, Any]
) -> None:
    with pytest.raises(ValidationError):
        validator(f"{capability_id}.request.schema.json").validate(request(parameters))


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_request_ids_must_be_positive(capability_id: str) -> None:
    parameters = deepcopy(PARAMETERS[capability_id])
    target = "line_id" if "line_id" in parameters else "move_id"
    parameters[target] = 0
    with pytest.raises(ValidationError):
        validator(f"{capability_id}.request.schema.json").validate(request(parameters))


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_responses_close_capability_status_and_core_write_shape(
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
