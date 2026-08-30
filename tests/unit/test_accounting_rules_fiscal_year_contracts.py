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
    "fiscal_year.create",
    "fiscal_year.update",
    "analytic.applicability.create",
    "analytic.applicability.update",
    "analytic.distribution_model.create",
    "analytic.distribution_model.update",
)
ANALYTIC_CAPABILITY_IDS = CAPABILITY_IDS[2:]

PARAMETERS: dict[str, dict[str, Any]] = {
    "fiscal_year.create": {
        "name": "FY 2027",
        "date_from": "2027-01-01",
        "date_to": "2027-12-31",
    },
    "fiscal_year.update": {
        "id": 41,
        "changes": {"name": "Fiscal 2027", "date_to": "2027-11-30"},
    },
    "analytic.applicability.create": {
        "plan_id": 11,
        "business_domain": "invoice",
        "applicability": "mandatory",
        "account_prefix": "4",
        "product_category_id": None,
    },
    "analytic.applicability.update": {
        "id": 51,
        "changes": {
            "plan_id": 12,
            "business_domain": "bill",
            "applicability": "optional",
            "account_prefix": None,
            "product_category_id": 17,
        },
    },
    "analytic.distribution_model.create": {
        "sequence": 10,
        "account_prefix": "6",
        "partner_id": None,
        "partner_category_id": 21,
        "product_id": None,
        "product_category_id": 31,
        "analytic_distribution": {"11": "25", "7,8": "75"},
    },
    "analytic.distribution_model.update": {
        "id": 61,
        "changes": {
            "sequence": 20,
            "partner_category_id": None,
            "analytic_distribution": None,
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
    if capability_id.startswith("fiscal_year."):
        return "account.fiscal.year"
    if capability_id.startswith("analytic.applicability."):
        return "account.analytic.applicability"
    return "account.analytic.distribution.model"


def _record_id(capability_id: str) -> int:
    return 71 if capability_id.endswith(".create") else PARAMETERS[capability_id]["id"]


def _result(capability_id: str) -> dict[str, Any]:
    return {
        "model": _model(capability_id),
        "id": _record_id(capability_id),
        "name": "Accounting rule",
        "state": "active",
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
            "idempotency_key": "accounting-rule-write-key",
            "verification": None,
        },
    }


@pytest.mark.parametrize("capability_id", CAPABILITY_IDS)
def test_contracts_normalize_and_derive_deterministic_keys(
    capability_id: str,
) -> None:
    assert capability_id in CORE_WRITE_CAPABILITY_IDS
    _, context, normalized = validate_core_write_request(
        capability_id, _request(capability_id)
    )
    first = _expected_idempotency_key(capability_id, normalized, context["company_id"])
    second = _expected_idempotency_key(
        capability_id, deepcopy(normalized), context["company_id"]
    )
    assert first == second
    assert first is not None
    assert first.startswith(f"{capability_id}:")


def test_text_and_distribution_values_are_normalized() -> None:
    request = _request("fiscal_year.create")
    request["parameters"]["name"] = "  FY 2027  "
    assert validate_core_write_request("fiscal_year.create", request)[2]["name"] == (
        "FY 2027"
    )

    request = _request("analytic.applicability.create")
    request["parameters"]["account_prefix"] = "  40  "
    assert (
        validate_core_write_request("analytic.applicability.create", request)[2][
            "account_prefix"
        ]
        == "40"
    )

    request = _request("analytic.distribution_model.create")
    request["parameters"]["analytic_distribution"] = {
        "9": "25",
        "2,3": "75",
    }
    normalized = validate_core_write_request(
        "analytic.distribution_model.create", request
    )[2]
    assert list(normalized["analytic_distribution"]) == ["2,3", "9"]


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    (
        (
            "fiscal_year.create",
            {**PARAMETERS["fiscal_year.create"], "timezone": "UTC"},
        ),
        (
            "fiscal_year.create",
            {**PARAMETERS["fiscal_year.create"], "date_from": "2027-02-29"},
        ),
        ("fiscal_year.update", {"id": 41, "changes": {}}),
        ("fiscal_year.update", {"id": True, "changes": {"name": "FY"}}),
        (
            "analytic.applicability.create",
            {**PARAMETERS["analytic.applicability.create"], "business_domain": "sale"},
        ),
        (
            "analytic.applicability.update",
            {"id": 51, "changes": {"applicability": "required"}},
        ),
        (
            "analytic.applicability.update",
            {"id": 51, "changes": {"account_prefix": "   "}},
        ),
        (
            "analytic.distribution_model.create",
            {
                **PARAMETERS["analytic.distribution_model.create"],
                "analytic_distribution": None,
            },
        ),
        (
            "analytic.distribution_model.create",
            {
                **PARAMETERS["analytic.distribution_model.create"],
                "analytic_distribution": {"8,7": "100"},
            },
        ),
        (
            "analytic.distribution_model.create",
            {
                **PARAMETERS["analytic.distribution_model.create"],
                "analytic_distribution": {"7": "100.0"},
            },
        ),
        (
            "analytic.distribution_model.update",
            {"id": 61, "changes": {"partner_id": 0}},
        ),
        (
            "analytic.distribution_model.update",
            {"id": 61, "changes": {"sudo": True}},
        ),
    ),
)
def test_contracts_reject_open_or_out_of_range_parameters(
    capability_id: str, parameters: dict[str, Any]
) -> None:
    request = _request(capability_id)
    request["parameters"] = deepcopy(parameters)
    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request(capability_id, request)
    assert caught.value.code == "invalid_request"


def test_fiscal_date_order_and_distribution_clear_are_deferred_to_runtime() -> None:
    fiscal_request = _request("fiscal_year.update")
    fiscal_request["parameters"]["changes"] = {
        "date_from": "2027-12-31",
        "date_to": "2027-01-01",
    }
    assert (
        validate_core_write_request("fiscal_year.update", fiscal_request)[2]["changes"]
        == fiscal_request["parameters"]["changes"]
    )

    distribution_request = _request("analytic.distribution_model.update")
    assert (
        validate_core_write_request(
            "analytic.distribution_model.update", distribution_request
        )[2]["changes"]["analytic_distribution"]
        is None
    )


@pytest.mark.parametrize("capability_id", CAPABILITY_IDS)
def test_all_twelve_schemas_parse_and_accept_closed_examples(
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
def test_result_contracts_bind_models_and_update_targets(capability_id: str) -> None:
    request = _request(capability_id)
    _, context, normalized = validate_core_write_request(capability_id, request)
    key = _expected_idempotency_key(capability_id, normalized, context["company_id"])
    assert key is not None
    result = _result(capability_id)
    assert (
        execute_core_write(_Port(result), capability_id, request, key, capability_id)[
            "result"
        ]
        == result
    )


@pytest.mark.parametrize("capability_id", ANALYTIC_CAPABILITY_IDS)
def test_analytic_results_accept_the_native_null_name(capability_id: str) -> None:
    request = _request(capability_id)
    _, context, normalized = validate_core_write_request(capability_id, request)
    key = _expected_idempotency_key(capability_id, normalized, context["company_id"])
    assert key is not None
    result = _result(capability_id)
    result["name"] = None
    assert (
        execute_core_write(_Port(result), capability_id, request, key, capability_id)[
            "result"
        ]
        == result
    )


@pytest.mark.parametrize("capability_id", ANALYTIC_CAPABILITY_IDS)
def test_analytic_results_still_reject_an_invalid_name_type(
    capability_id: str,
) -> None:
    request = _request(capability_id)
    _, context, normalized = validate_core_write_request(capability_id, request)
    key = _expected_idempotency_key(capability_id, normalized, context["company_id"])
    assert key is not None
    result = _result(capability_id)
    result["name"] = 7
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(_Port(result), capability_id, request, key, capability_id)
    assert caught.value.code == "failed_validation"


def test_fiscal_year_result_still_requires_a_text_name() -> None:
    capability_id = "fiscal_year.create"
    request = _request(capability_id)
    _, context, normalized = validate_core_write_request(capability_id, request)
    key = _expected_idempotency_key(capability_id, normalized, context["company_id"])
    assert key is not None
    result = _result(capability_id)
    result["name"] = None
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(_Port(result), capability_id, request, key, capability_id)
    assert caught.value.code == "failed_validation"


@pytest.mark.parametrize(
    ("field", "value"),
    (("model", "account.move"), ("id", 999), ("state", "archived")),
)
def test_result_contract_rejects_mismatched_generic_result(
    field: str, value: Any
) -> None:
    capability_id = "analytic.applicability.update"
    request = _request(capability_id)
    _, context, normalized = validate_core_write_request(capability_id, request)
    key = _expected_idempotency_key(capability_id, normalized, context["company_id"])
    assert key is not None
    result = _result(capability_id)
    result[field] = value
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(_Port(result), capability_id, request, key, capability_id)
    assert caught.value.code == "failed_validation"
