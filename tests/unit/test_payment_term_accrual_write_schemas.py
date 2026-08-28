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
    "payment_term.create",
    "payment_term.update",
    "payment_term.lines.replace",
    "payment_term.archive",
    "payment_term.restore",
    "period.accrual.generate",
)
PAYMENT_LINE = {
    "value": "percent",
    "value_amount": "100",
    "delay_type": "days_after",
    "nb_days": 30,
}
PARAMETERS: dict[str, dict[str, Any]] = {
    "payment_term.create": {
        "name": "Net 30",
        "company_id": 7,
        "sequence": 10,
        "note": "Payment is due within 30 days.",
        "display_on_invoice": True,
        "early_discount": False,
        "discount_percentage": "0",
        "discount_days": 0,
        "early_pay_discount_computation": "excluded",
        "lines": [PAYMENT_LINE],
    },
    "payment_term.update": {
        "payment_term_id": 91,
        "sequence": 20,
        "note": None,
    },
    "payment_term.lines.replace": {
        "payment_term_id": 91,
        "lines": [
            {**PAYMENT_LINE, "value_amount": "50", "nb_days": 15},
            {**PAYMENT_LINE, "value_amount": "50", "nb_days": 30},
        ],
    },
    "payment_term.archive": {"payment_term_id": 91},
    "payment_term.restore": {"payment_term_id": 91},
    "period.accrual.generate": {
        "source_model": "purchase.order",
        "order_ids": [301],
        "date": "2026-08-31",
        "reversal_date": "2026-09-01",
        "journal_id": 11,
        "accrual_account_id": 401,
        "amount": "125.5",
    },
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
    payment_term = capability_id.startswith("payment_term.")
    record_id = 91 if payment_term else 121
    return {
        "schema_version": "v1",
        "request_id": str(uuid4()),
        "success": True,
        "capability": capability_id,
        "status": "verified",
        "data": {
            "idempotent_replay": False,
            "result": {
                "model": "account.payment.term" if payment_term else "account.move",
                "id": record_id,
                "name": "Net 30" if payment_term else "MISC/2026/00121",
                "state": "active" if payment_term else "draft",
                "company_id": 7,
                "move_type": None if payment_term else "entry",
                "source_id": None if payment_term else 301,
                "line_ids": [911],
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
            "model": "account.payment.term" if payment_term else "account.move",
            "record_ids": [record_id],
        },
        "audit": {
            "operation_id": None,
            "idempotency_key": "payment-term-accrual-key",
            "verification": None,
        },
    }


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_all_twelve_schemas_parse_and_accept_closed_examples(
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
        (
            "payment_term.create",
            {**PARAMETERS["payment_term.create"], "name": " Net 30"},
        ),
        (
            "payment_term.create",
            {**PARAMETERS["payment_term.create"], "company_id": 0},
        ),
        (
            "payment_term.create",
            {**PARAMETERS["payment_term.create"], "lines": []},
        ),
        (
            "payment_term.create",
            {
                **PARAMETERS["payment_term.create"],
                "early_discount": True,
                "discount_percentage": "2",
                "discount_days": 10,
                "lines": [{**PAYMENT_LINE, "value_amount": "50"}],
            },
        ),
        ("payment_term.update", {"payment_term_id": 91}),
        ("payment_term.update", {"payment_term_id": 91, "lines": [PAYMENT_LINE]}),
        (
            "payment_term.update",
            {"payment_term_id": 91, "early_discount": True},
        ),
        (
            "payment_term.update",
            {"payment_term_id": 91, "discount_percentage": "100.1"},
        ),
        ("payment_term.lines.replace", {"payment_term_id": 91, "lines": []}),
        (
            "payment_term.lines.replace",
            {
                "payment_term_id": 91,
                "lines": [{**PAYMENT_LINE, "value": "balance"}],
            },
        ),
        (
            "payment_term.lines.replace",
            {
                "payment_term_id": 91,
                "lines": [{**PAYMENT_LINE, "value_amount": "100.0"}],
            },
        ),
        (
            "payment_term.lines.replace",
            {
                "payment_term_id": 91,
                "lines": [{**PAYMENT_LINE, "delay_type": "end_of_month"}],
            },
        ),
        (
            "payment_term.lines.replace",
            {
                "payment_term_id": 91,
                "lines": [{**PAYMENT_LINE, "days_next_month": 32}],
            },
        ),
        ("payment_term.archive", {"payment_term_id": 0}),
        ("payment_term.restore", {"payment_term_id": 0}),
        (
            "period.accrual.generate",
            {**PARAMETERS["period.accrual.generate"], "source_model": "account.move"},
        ),
        (
            "period.accrual.generate",
            {**PARAMETERS["period.accrual.generate"], "order_ids": [301, 301]},
        ),
        (
            "period.accrual.generate",
            {**PARAMETERS["period.accrual.generate"], "order_ids": [0]},
        ),
        (
            "period.accrual.generate",
            {**PARAMETERS["period.accrual.generate"], "date": "2026-02-30"},
        ),
        (
            "period.accrual.generate",
            {**PARAMETERS["period.accrual.generate"], "amount": "0"},
        ),
        (
            "period.accrual.generate",
            {**PARAMETERS["period.accrual.generate"], "amount": "125.50"},
        ),
        (
            "period.accrual.generate",
            {**PARAMETERS["period.accrual.generate"], "order_ids": [301, 302]},
        ),
    ),
)
def test_request_schemas_reject_invalid_payment_term_and_accrual_contracts(
    capability_id: str, parameters: dict[str, Any]
) -> None:
    with pytest.raises(ValidationError):
        validator(f"{capability_id}.request.schema.json").validate(request(parameters))


def test_payment_term_line_rejects_percent_above_one_hundred_and_nested_extras() -> (
    None
):
    schema = validator("payment_term.lines.replace.request.schema.json")
    for line in (
        {**PAYMENT_LINE, "value_amount": "100.1"},
        {**PAYMENT_LINE, "nb_days": -1},
        {**PAYMENT_LINE, "sudo": True},
    ):
        with pytest.raises(ValidationError):
            schema.validate(request({"payment_term_id": 91, "lines": [line]}))


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

    malformed = response(capability_id)
    del malformed["data"]["result"]["company_id"]
    with pytest.raises(ValidationError):
        schema.validate(malformed)

    extra_result_field = response(capability_id)
    extra_result_field["data"]["result"]["sudo"] = True
    with pytest.raises(ValidationError):
        schema.validate(extra_result_field)
