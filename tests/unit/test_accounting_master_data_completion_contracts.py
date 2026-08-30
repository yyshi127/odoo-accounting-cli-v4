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
    "account.tag.create",
    "account.tag.update",
    "account.tag.archive",
    "account.tag.restore",
    "tax.group.create",
    "tax.group.update",
    "cash_rounding.create",
    "cash_rounding.update",
)

PARAMETERS: dict[str, dict[str, Any]] = {
    "account.tag.create": {
        "name": "VAT 13%",
        "applicability": "taxes",
        "color": 4,
        "country_id": 156,
    },
    "account.tag.update": {
        "account_tag_id": 41,
        "changes": {"name": "VAT output", "color": 5},
    },
    "account.tag.archive": {"account_tag_id": 41},
    "account.tag.restore": {"account_tag_id": 41},
    "tax.group.create": {
        "name": "VAT 13%",
        "sequence": 10,
        "preceding_subtotal": None,
    },
    "tax.group.update": {
        "tax_group_id": 51,
        "changes": {"sequence": 20, "preceding_subtotal": "Untaxed Amount"},
    },
    "cash_rounding.create": {
        "name": "Cash 0.05",
        "rounding": "0.05",
        "strategy": "add_invoice_line",
        "rounding_method": "HALF-UP",
        "profit_account_id": 31,
        "loss_account_id": 32,
    },
    "cash_rounding.update": {
        "cash_rounding_id": 61,
        "changes": {
            "strategy": "biggest_tax",
            "profit_account_id": None,
            "loss_account_id": None,
        },
    },
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


def _model(capability_id: str) -> str:
    if capability_id.startswith("account.tag."):
        return "account.account.tag"
    if capability_id.startswith("tax.group."):
        return "account.tax.group"
    return "account.cash.rounding"


def _record_id(capability_id: str) -> int:
    if capability_id.endswith(".create"):
        return 71
    field = (
        "account_tag_id"
        if capability_id.startswith("account.tag.")
        else "tax_group_id"
        if capability_id.startswith("tax.group.")
        else "cash_rounding_id"
    )
    return PARAMETERS[capability_id][field]


def _result(capability_id: str) -> dict[str, Any]:
    return {
        "model": _model(capability_id),
        "id": _record_id(capability_id),
        "name": "Configuration",
        "state": "archived" if capability_id == "account.tag.archive" else "active",
        "company_id": 7,
        "move_type": None,
        "source_id": None,
        "line_ids": [],
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }


def _response(capability_id: str) -> dict[str, Any]:
    result = _result(capability_id)
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "success": True,
        "capability": capability_id,
        "status": "verified",
        "data": {"idempotent_replay": False, "result": result},
        "warnings": [],
        "error": None,
        "odoo": {
            "database": "v4-dev",
            "company_id": 7,
            "user_id": 42,
            "model": result["model"],
            "record_ids": [result["id"]],
        },
        "audit": {
            "operation_id": None,
            "idempotency_key": "accounting-master-data-key",
            "verification": None,
        },
    }


@pytest.mark.parametrize("capability_id", CAPABILITY_IDS)
def test_closed_contracts_derive_deterministic_idempotency_keys(
    capability_id: str,
) -> None:
    assert capability_id in CORE_WRITE_CAPABILITY_IDS
    _, context, normalized = validate_core_write_request(
        capability_id, _request(capability_id)
    )
    key = _expected_idempotency_key(capability_id, normalized, context["company_id"])
    assert key is not None
    assert key.startswith(f"{capability_id}:")


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    (
        (
            "account.tag.create",
            {
                "name": "Product",
                "applicability": "products",
                "color": 1,
                "country_id": 156,
            },
        ),
        (
            "account.tag.update",
            {"account_tag_id": 41, "changes": {"active": False}},
        ),
        ("account.tag.update", {"account_tag_id": 41, "changes": {}}),
        ("account.tag.archive", {"account_tag_id": 0}),
        (
            "tax.group.create",
            {
                **PARAMETERS["tax.group.create"],
                "company_id": 7,
            },
        ),
        ("tax.group.update", {"tax_group_id": 51, "changes": {}}),
        (
            "cash_rounding.create",
            {**PARAMETERS["cash_rounding.create"], "rounding": "0.050"},
        ),
        (
            "cash_rounding.create",
            {
                **PARAMETERS["cash_rounding.create"],
                "strategy": "biggest_tax",
            },
        ),
        (
            "cash_rounding.create",
            {
                **PARAMETERS["cash_rounding.create"],
                "loss_account_id": None,
            },
        ),
        (
            "cash_rounding.update",
            {
                "cash_rounding_id": 61,
                "changes": {"profit_account_id": 31, "loss_account_id": None},
            },
        ),
    ),
)
def test_contracts_reject_open_or_internally_inconsistent_parameters(
    capability_id: str, parameters: dict[str, Any]
) -> None:
    request = _request(capability_id)
    request["parameters"] = deepcopy(parameters)
    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request(capability_id, request)
    assert caught.value.code == "invalid_request"


@pytest.mark.parametrize(
    ("capability_id", "changes"),
    (
        ("account.tag.update", {"country_id": 156}),
        ("account.tag.update", {"applicability": "accounts"}),
        ("cash_rounding.update", {"strategy": "add_invoice_line"}),
        (
            "cash_rounding.update",
            {"strategy": "add_invoice_line", "profit_account_id": 31},
        ),
        ("cash_rounding.update", {"profit_account_id": 31}),
        ("cash_rounding.update", {"strategy": "biggest_tax"}),
    ),
)
def test_updates_defer_old_record_dependent_invariants_to_runtime(
    capability_id: str, changes: dict[str, Any]
) -> None:
    request = _request(capability_id)
    request["parameters"]["changes"] = changes
    assert validate_core_write_request(capability_id, request)[2]["changes"] == changes
    _schema_validator(f"{capability_id}.request.schema.json").validate(request)


@pytest.mark.parametrize("capability_id", CAPABILITY_IDS)
def test_all_sixteen_schemas_parse_and_accept_closed_examples(
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


@pytest.mark.parametrize("capability_id", CAPABILITY_IDS)
def test_result_contracts_bind_models_targets_and_states(capability_id: str) -> None:
    request = _request(capability_id)
    _, context, normalized = validate_core_write_request(capability_id, request)
    key = _expected_idempotency_key(capability_id, normalized, context["company_id"])
    assert key is not None
    result = _result(capability_id)
    assert execute_core_write(
        _Port(result), capability_id, request, key, capability_id
    )["result"] == result


def test_result_contract_rejects_wrong_model() -> None:
    capability_id = "tax.group.update"
    request = _request(capability_id)
    _, context, normalized = validate_core_write_request(capability_id, request)
    key = _expected_idempotency_key(capability_id, normalized, context["company_id"])
    assert key is not None
    result = _result(capability_id)
    result["model"] = "account.tax"
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(_Port(result), capability_id, request, key, capability_id)
    assert caught.value.code == "failed_validation"
