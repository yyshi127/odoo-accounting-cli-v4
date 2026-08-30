from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from referencing import Registry, Resource

from odoo_accounting_cli_v4.capabilities.core_writes import (
    CORE_WRITE_CAPABILITY_IDS,
    CoreWriteError,
    _expected_idempotency_key,
    execute_core_write,
    validate_core_write_request,
)

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas" / "v1"
REQUEST_ID = "7bc39413-0d69-4092-9319-795d33f3167c"
CAPABILITY_IDS = (
    "currency.rate.record",
    "account.group.create",
    "account.group.update",
    "tax.repartition_lines.replace",
    "reconciliation.model.create",
    "reconciliation.model.update",
    "reconciliation.model.lines.replace",
    "reconciliation.model.archive",
    "reconciliation.model.restore",
)

REPARTITION_LINES = [
    {
        "sequence": 1,
        "repartition_type": "base",
        "factor_percent": "100",
        "account_id": None,
        "tag_ids": [],
        "use_in_tax_closing": False,
    },
    {
        "sequence": 2,
        "repartition_type": "tax",
        "factor_percent": "100",
        "account_id": 31,
        "tag_ids": [8, 9],
        "use_in_tax_closing": True,
    },
]

RECONCILIATION_HEADER = {
    "name": "Bank fee",
    "sequence": 10,
    "trigger": "auto_reconcile",
    "match_journal_ids": [7, 8],
    "match_partner_ids": [21, 22],
    "match_amount": {"operator": "between", "minimum": "2", "maximum": "5"},
    "match_label": {"operator": "contains", "value": "BANK FEE"},
}

PARAMETERS: dict[str, dict[str, Any]] = {
    "currency.rate.record": {
        "currency_id": 6,
        "date": "2026-08-30",
        "company_units_per_foreign_unit": "0.125",
    },
    "account.group.create": {
        "name": "Current assets",
        "code_prefix_start": "1000",
        "code_prefix_end": "1999",
    },
    "account.group.update": {
        "account_group_id": 41,
        "changes": {"name": "Liquid assets"},
    },
    "tax.repartition_lines.replace": {
        "tax_id": 12,
        "invoice_lines": REPARTITION_LINES,
        "refund_lines": REPARTITION_LINES,
    },
    "reconciliation.model.create": RECONCILIATION_HEADER,
    "reconciliation.model.update": {
        "reconciliation_model_id": 51,
        "changes": {
            "match_journal_ids": [8, 7],
            "match_amount": {
                "operator": "greater",
                "minimum": "10",
                "maximum": None,
            },
        },
    },
    "reconciliation.model.lines.replace": {
        "reconciliation_model_id": 51,
        "lines": [
            {
                "sequence": 10,
                "account_id": 31,
                "partner_id": None,
                "label": "Fee",
                "amount_type": "fixed",
                "amount_string": "-2.5",
                "tax_ids": [9, 8],
                "analytic_distribution": [
                    {"analytic_account_ids": [12, 11], "percentage": "100"}
                ],
            }
        ],
    },
    "reconciliation.model.archive": {"reconciliation_model_id": 51},
    "reconciliation.model.restore": {"reconciliation_model_id": 51},
}


def _request(capability_id: str) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "context": {
            "database": "v4-dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "zh_CN",
            "timezone": "Asia/Shanghai",
        },
        "parameters": deepcopy(PARAMETERS[capability_id]),
    }


def _load_schema(name: str) -> dict[str, Any]:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def _schema_validator(name: str) -> Draft202012Validator:
    resources: dict[str, Resource[Any]] = {}
    for resource_name in (
        "request.schema.json",
        "response.schema.json",
        "core-write-result.schema.json",
    ):
        schema = _load_schema(resource_name)
        resource = Resource.from_contents(schema)
        resources[schema["$id"]] = resource
        resources[resource_name] = resource
    return Draft202012Validator(
        _load_schema(name),
        registry=Registry().with_resources(resources.items()),
        format_checker=FormatChecker(),
    )


def _response(capability_id: str) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "success": True,
        "capability": capability_id,
        "status": "verified",
        "data": {
            "idempotent_replay": False,
            "result": {
                "model": "account.reconcile.model",
                "id": 51,
                "name": "Bank fee",
                "state": "active",
                "company_id": 7,
                "move_type": None,
                "source_id": None,
                "line_ids": [],
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
            "model": "account.reconcile.model",
            "record_ids": [51],
        },
        "audit": {
            "operation_id": None,
            "idempotency_key": "accounting-configuration-write-key",
            "verification": None,
        },
    }


@pytest.mark.parametrize("capability_id", CAPABILITY_IDS)
def test_contracts_normalize_and_derive_a_deterministic_key(capability_id: str) -> None:
    assert capability_id in CORE_WRITE_CAPABILITY_IDS
    _, context, normalized = validate_core_write_request(
        capability_id, _request(capability_id)
    )
    key = _expected_idempotency_key(capability_id, normalized, context["company_id"])
    assert key is not None
    assert key.startswith(f"{capability_id}:")


def test_set_like_ids_are_sorted_without_reordering_business_lines() -> None:
    _, _, update = validate_core_write_request(
        "reconciliation.model.update", _request("reconciliation.model.update")
    )
    assert update["changes"]["match_journal_ids"] == [7, 8]

    _, _, replacement = validate_core_write_request(
        "reconciliation.model.lines.replace",
        _request("reconciliation.model.lines.replace"),
    )
    line = replacement["lines"][0]
    assert line["tax_ids"] == [8, 9]
    assert line["analytic_distribution"] == [
        {"analytic_account_ids": [11, 12], "percentage": "100"}
    ]


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    (
        (
            "currency.rate.record",
            {
                **PARAMETERS["currency.rate.record"],
                "company_units_per_foreign_unit": "1.0",
            },
        ),
        (
            "account.group.create",
            {
                **PARAMETERS["account.group.create"],
                "code_prefix_end": "999",
            },
        ),
        (
            "account.group.update",
            {"account_group_id": 41, "changes": {}},
        ),
        (
            "tax.repartition_lines.replace",
            {
                **PARAMETERS["tax.repartition_lines.replace"],
                "refund_lines": [REPARTITION_LINES[1]],
            },
        ),
        (
            "tax.repartition_lines.replace",
            {
                **PARAMETERS["tax.repartition_lines.replace"],
                "invoice_lines": [
                    REPARTITION_LINES[0],
                    {**REPARTITION_LINES[1], "factor_percent": "90"},
                ],
            },
        ),
        (
            "reconciliation.model.create",
            {
                **RECONCILIATION_HEADER,
                "match_amount": {
                    "operator": "between",
                    "minimum": "5",
                    "maximum": "2",
                },
            },
        ),
        (
            "reconciliation.model.lines.replace",
            {
                "reconciliation_model_id": 51,
                "lines": [
                    {
                        **PARAMETERS["reconciliation.model.lines.replace"]["lines"][0],
                        "amount_type": "regex",
                        "amount_string": "[",
                    }
                ],
            },
        ),
        (
            "reconciliation.model.archive",
            {"reconciliation_model_id": 0},
        ),
    ),
)
def test_contracts_reject_ambiguous_or_unsafe_parameters(
    capability_id: str, parameters: dict[str, Any]
) -> None:
    request = _request(capability_id)
    request["parameters"] = deepcopy(parameters)
    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request(capability_id, request)
    assert caught.value.code == "invalid_request"


@pytest.mark.parametrize("capability_id", CAPABILITY_IDS)
def test_all_eighteen_schemas_parse_and_accept_closed_examples(
    capability_id: str,
) -> None:
    request_name = f"{capability_id}.request.schema.json"
    response_name = f"{capability_id}.response.schema.json"
    Draft202012Validator.check_schema(_load_schema(request_name))
    Draft202012Validator.check_schema(_load_schema(response_name))
    _schema_validator(request_name).validate(_request(capability_id))
    _schema_validator(response_name).validate(_response(capability_id))


@pytest.mark.parametrize("capability_id", CAPABILITY_IDS)
def test_request_schemas_reject_open_parameters(capability_id: str) -> None:
    request = _request(capability_id)
    request["parameters"]["sudo"] = True
    with pytest.raises(ValidationError):
        _schema_validator(f"{capability_id}.request.schema.json").validate(request)


class _Port:
    user_id = 42

    def __init__(self, result: dict[str, Any]) -> None:
        self.result = result

    def execute(self, **_: Any) -> dict[str, Any]:
        return {
            "user_id": 42,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "idempotent_replay": False,
            "result": deepcopy(self.result),
        }


@pytest.mark.parametrize(
    ("capability_id", "model", "record_id", "state", "line_ids", "source_id"),
    (
        ("currency.rate.record", "res.currency.rate", 61, "active", [], 6),
        ("account.group.create", "account.group", 41, "active", [], None),
        ("tax.repartition_lines.replace", "account.tax", 12, "active", [71, 72, 73, 74], None),
        ("reconciliation.model.create", "account.reconcile.model", 51, "active", [], None),
        ("reconciliation.model.archive", "account.reconcile.model", 51, "archived", [], None),
    ),
)
def test_result_contracts_bind_models_targets_and_state(
    capability_id: str,
    model: str,
    record_id: int,
    state: str,
    line_ids: list[int],
    source_id: int | None,
) -> None:
    request = _request(capability_id)
    _, context, normalized = validate_core_write_request(capability_id, request)
    key = _expected_idempotency_key(capability_id, normalized, context["company_id"])
    assert key is not None
    result = {
        "model": model,
        "id": record_id,
        "name": "Configuration",
        "state": state,
        "company_id": 7,
        "move_type": None,
        "source_id": source_id,
        "line_ids": line_ids,
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }
    assert execute_core_write(
        _Port(result), capability_id, request, key, capability_id
    )["result"] == result
