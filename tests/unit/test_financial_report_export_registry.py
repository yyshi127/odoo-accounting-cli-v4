from __future__ import annotations

import copy

import pytest

from odoo_accounting_cli_v4.bridge.financial_report_exports_runtime import (
    CAPABILITY_SPECS,
)
from odoo_accounting_cli_v4.registry import (
    InstanceValidationError,
    load_registry,
)

EXPORTS = {
    "report.trial_balance.export": ("report.trial_balance", "range"),
    "report.balance_sheet.export": ("report.balance_sheet", "single"),
    "report.profit_and_loss.export": ("report.profit_and_loss", "range"),
    "report.cash_flow.export": ("report.cash_flow", "range"),
    "report.tax.export": ("report.tax", "range"),
    "report.general_ledger.export": ("report.general_ledger", "range"),
    "report.partner_ledger.export": ("report.partner_ledger", "range"),
    "report.aged_receivable.export": ("report.aged_receivable", "single"),
    "report.aged_payable.export": ("report.aged_payable", "single"),
    "report.executive_summary.export": ("report.executive_summary", "range"),
    "report.journal.export": ("report.journal", "range"),
    "report.asset.export": ("report.asset", "range"),
    "report.deferred_expense.export": ("report.deferred_expense", "range"),
    "report.deferred_revenue.export": ("report.deferred_revenue", "range"),
    "report.multicurrency_revaluation.export": (
        "report.multicurrency_revaluation",
        "single",
    ),
    "report.china.balance_sheet.export": (
        "report.china.balance_sheet",
        "single",
    ),
    "report.china.profit_and_loss.export": (
        "report.china.profit_and_loss",
        "range",
    ),
    "report.china.cash_flow.export": ("report.china.cash_flow", "range"),
    "report.singapore.gst.export": ("report.singapore.gst", "range"),
}
REQUEST_ID = "123e4567-e89b-42d3-a456-426614174000"


@pytest.fixture(scope="module")
def registry():
    return load_registry()


def _parameters(mode: str) -> dict[str, object]:
    if mode == "range":
        return {
            "date_from": "2026-01-01",
            "date_to": "2026-01-31",
            "format": "pdf",
        }
    return {"as_of": "2026-01-31", "format": "xlsx"}


def _request(mode: str) -> dict[str, object]:
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "context": {
            "database": "odoo_cli_v4_dev",
            "company_id": 1,
            "user_login": "accountant@example.test",
            "language": "en_US",
            "timezone": "UTC",
        },
        "parameters": _parameters(mode),
    }


def _response(capability_id: str) -> dict[str, object]:
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "success": True,
        "capability": capability_id,
        "status": "verified",
        "data": {
            "filename": "report.pdf",
            "format": "pdf",
            "mimetype": "application/pdf",
            "byte_count": 3,
            "sha256": "0" * 64,
            "content_base64": "YWJj",
        },
        "warnings": [],
        "error": None,
        "odoo": {
            "database": "odoo_cli_v4_dev",
            "company_id": 1,
            "user_id": 5,
            "model": "account.report",
            "record_ids": [1],
        },
        "audit": {
            "operation_id": None,
            "idempotency_key": None,
            "verification": {"read_only": True},
        },
    }


def test_export_descriptors_reuse_the_fixed_report_sources_and_requirements(
    registry,
) -> None:
    assert set(EXPORTS) <= set(registry.ids())

    for capability_id, (read_id, _) in EXPORTS.items():
        descriptor = registry.describe(capability_id)
        read_descriptor = registry.describe(read_id)

        assert descriptor["domain"] == read_descriptor["domain"]
        assert descriptor["access"] == "read"
        assert descriptor["source"] == read_descriptor["source"]
        assert descriptor["requirements"] == read_descriptor["requirements"]
        runtime_models = set(
            CAPABILITY_SPECS[capability_id].get("models", ("account.report",))
        )
        assert runtime_models <= set(descriptor["source"]["models"])
        assert {f"{model}:read" for model in runtime_models} <= set(
            descriptor["requirements"]["acl"]
        )
        assert descriptor["handler_key"] == capability_id.replace(".", "_")
        assert descriptor["status"]["value"] == "unconfigured"
        assert descriptor["status"]["reason_code"] == "runtime_context_required"
        assert descriptor["strategies"] == {
            "preview": "not_applicable_read_only",
            "execute": "fixed_native_odoo_export_via_account.report.fixed_export",
            "verify": "posted_entries_read_only_export_and_response_schema_validation",
            "idempotency": "not_applicable_read_only",
            "reverse": "not_applicable_read_only",
        }


@pytest.mark.parametrize("capability_id", EXPORTS)
def test_export_schema_metadata_is_capability_specific(
    registry, capability_id: str
) -> None:
    descriptor = registry.describe(capability_id)

    for kind in ("request", "response"):
        schema = registry.load_schema(descriptor["schemas"][kind])
        assert schema["$id"].endswith(f"{capability_id}.{kind}.schema.json")
        assert schema["additionalProperties"] is False

    response_schema = registry.load_schema(descriptor["schemas"]["response"])
    data = response_schema["$defs"]["data"]
    assert data["additionalProperties"] is False
    assert set(data["required"]) == {
        "filename",
        "format",
        "mimetype",
        "byte_count",
        "sha256",
        "content_base64",
    }
    assert set(data["properties"]) == set(data["required"])
    assert data["properties"]["format"]["enum"] == ["pdf", "xlsx"]


@pytest.mark.parametrize("capability_id,definition", EXPORTS.items())
def test_export_request_schemas_are_closed_and_format_checked(
    registry, capability_id: str, definition: tuple[str, str]
) -> None:
    _, mode = definition
    reference = registry.describe(capability_id)["schemas"]["request"]
    request = _request(mode)

    registry.validate_instance(reference, request)

    parameter_schema = registry.load_schema(reference)["$defs"]["parameters"]
    expected = (
        {"date_from", "date_to", "format"}
        if mode == "range"
        else {"as_of", "format"}
    )
    assert parameter_schema["additionalProperties"] is False
    assert set(parameter_schema["required"]) == expected
    assert set(parameter_schema["properties"]) - {"journal_ids"} == expected
    assert parameter_schema["properties"]["format"]["enum"] == ["pdf", "xlsx"]

    invalid = copy.deepcopy(request)
    invalid["parameters"]["unexpected"] = True
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(reference, invalid)

    invalid = copy.deepcopy(request)
    invalid["parameters"]["format"] = "csv"
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(reference, invalid)

    invalid = copy.deepcopy(request)
    date_key = "date_from" if mode == "range" else "as_of"
    invalid["parameters"][date_key] = "2026-1-1"
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(reference, invalid)


@pytest.mark.parametrize(
    "capability_id",
    [capability_id for capability_id, (_, mode) in EXPORTS.items() if mode == "range"],
)
def test_range_order_is_intentionally_deferred_to_code(
    registry, capability_id: str
) -> None:
    reference = registry.describe(capability_id)["schemas"]["request"]
    request = _request("range")
    request["parameters"]["date_from"] = "2026-02-01"
    request["parameters"]["date_to"] = "2026-01-31"

    registry.validate_instance(reference, request)


@pytest.mark.parametrize("capability_id", EXPORTS)
def test_export_response_schemas_accept_exact_success_and_failure_envelopes(
    registry, capability_id: str
) -> None:
    reference = registry.describe(capability_id)["schemas"]["response"]
    response = _response(capability_id)
    registry.validate_instance(reference, response)

    invalid = copy.deepcopy(response)
    invalid["data"]["unexpected"] = True
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(reference, invalid)

    invalid = copy.deepcopy(response)
    invalid["data"]["sha256"] = "not-a-sha256"
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(reference, invalid)

    invalid = copy.deepcopy(response)
    invalid["data"]["content_base64"] = "***"
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(reference, invalid)

    failure = copy.deepcopy(response)
    failure.update(
        {
            "success": False,
            "status": "failed",
            "data": None,
            "error": {
                "code": "ODOO_ERROR",
                "message": "Export failed.",
                "details": {},
                "retryable": False,
            },
        }
    )
    registry.validate_instance(reference, failure)

    failure["data"] = response["data"]
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(reference, failure)
