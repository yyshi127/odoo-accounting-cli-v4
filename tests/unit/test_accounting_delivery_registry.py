from __future__ import annotations

import copy
from typing import Any

import pytest

from odoo_accounting_cli_v4.registry import (
    InstanceValidationError,
    load_registry,
)

REQUEST_ID = "123e4567-e89b-42d3-a456-426614174000"
DELIVERY_IDS = {
    "invoice.send.inspect": ("read", "invoice_send_inspect", "unconfigured"),
    "invoice.send": ("write", "accounting_delivery", "degraded"),
    "payment.receipt.send.inspect": (
        "read",
        "payment_receipt_send_inspect",
        "unconfigured",
    ),
    "payment.receipt.send": ("write", "accounting_delivery", "degraded"),
    "report.customer_statement.send": (
        "write",
        "accounting_delivery",
        "degraded",
    ),
    "report.followup.send": ("write", "accounting_delivery", "degraded"),
    "invoice.followup.update": ("write", "accounting_delivery", "unconfigured"),
}
EXPORT_IDS = {
    "report.customer_statement.export": "report_customer_statement_export",
    "report.followup.export": "report_followup_export",
}
ACL_DENIED_SEND_IDS = {
    "report.customer_statement.send",
    "report.followup.send",
}
LIVE_TEST = "tests/integration/test_accounting_delivery_batch_live.py"
PARAMETERS: dict[str, dict[str, Any]] = {
    "invoice.send.inspect": {"move_id": 31},
    "invoice.send": {"move_ids": [31, 32]},
    "payment.receipt.send.inspect": {"payment_id": 41},
    "payment.receipt.send": {"payment_ids": [41, 42]},
    "report.customer_statement.export": {
        "partner_id": 21,
        "date_from": "2026-08-01",
        "date_to": "2026-08-31",
        "format": "pdf",
    },
    "report.customer_statement.send": {
        "partner_ids": [21, 22],
        "date_from": "2026-08-01",
        "date_to": "2026-08-31",
    },
    "report.followup.export": {
        "partner_id": 21,
        "as_of": "2026-08-31",
        "format": "xlsx",
    },
    "report.followup.send": {
        "partner_ids": [21, 22],
        "as_of": "2026-08-31",
    },
    "invoice.followup.update": {"move_id": 31, "no_followup": True},
}


@pytest.fixture(scope="module")
def registry():
    return load_registry()


def _request(capability_id: str) -> dict[str, Any]:
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
        "parameters": copy.deepcopy(PARAMETERS[capability_id]),
    }


def _inspection_result(record_id: int) -> dict[str, Any]:
    return {
        "records": [
            {
                "record_id": record_id,
                "partner_id": 21,
                "recipient_emails": ["accounts@example.test"],
                "template_id": 8,
                "report_id": 230,
                "sending_methods": ["email"],
                "warnings": [],
                "sendable": True,
            }
        ]
    }


def _export_result() -> dict[str, Any]:
    return {
        "filename": "report.pdf",
        "format": "pdf",
        "mimetype": "application/pdf",
        "byte_count": 3,
        "sha256": "0" * 64,
        "content_base64": "YWJj",
    }


def _data(capability_id: str) -> dict[str, Any]:
    if capability_id == "invoice.send.inspect":
        return {"idempotent_replay": False, "result": _inspection_result(31)}
    if capability_id == "payment.receipt.send.inspect":
        return {"idempotent_replay": False, "result": _inspection_result(41)}
    if capability_id in EXPORT_IDS:
        return _export_result()
    if capability_id == "invoice.followup.update":
        result = {"record_id": 31, "no_followup": True}
    elif capability_id.startswith("report."):
        result = {"record_ids": [21, 22], "processed_count": 2}
    elif capability_id.startswith("invoice."):
        result = {"record_ids": [31, 32], "processed_count": 2}
    else:
        result = {"record_ids": [41, 42], "processed_count": 2}
    return {"idempotent_replay": False, "result": result}


def _response(capability_id: str) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "success": True,
        "capability": capability_id,
        "status": "verified",
        "data": _data(capability_id),
        "warnings": [],
        "error": None,
        "odoo": {
            "database": "odoo_cli_v4_dev",
            "company_id": 1,
            "user_id": 5,
            "model": "account.move",
            "record_ids": [],
        },
        "audit": {
            "operation_id": None,
            "idempotency_key": None,
            "verification": {"schema": "v1"},
        },
    }


def test_registry_declares_the_exact_delivery_handlers_and_status_boundaries(
    registry,
) -> None:
    assert set(DELIVERY_IDS) | set(EXPORT_IDS) <= set(registry.ids())

    for capability_id, (access, handler, status) in DELIVERY_IDS.items():
        descriptor = registry.describe(capability_id)
        assert descriptor["access"] == access
        assert descriptor["handler_key"] == handler
        assert descriptor["status"]["value"] == status
        expected_reason = (
            "odoo_queue_delivery_only"
            if status == "degraded"
            else "runtime_context_required"
        )
        assert descriptor["status"]["reason_code"] == expected_reason
        assert (
            "tests/unit/test_accounting_delivery_registry.py"
            in descriptor["tests"]["unit"]["references"]
        )
        integration = descriptor["tests"]["integration"]
        assert integration["references"] == [LIVE_TEST]
        if capability_id in ACL_DENIED_SEND_IDS:
            assert integration["status"] == "planned"
            assert "res.partner:write" in integration["reason"]
            assert (
                "positive native report delivery remains pending"
                in integration["reason"]
            )
        else:
            assert integration["status"] == "implemented"
            assert "both isolated aliases" in integration["reason"]

    for capability_id, handler in EXPORT_IDS.items():
        descriptor = registry.describe(capability_id)
        assert descriptor["access"] == "read"
        assert descriptor["handler_key"] == handler
        assert descriptor["status"]["value"] == "unconfigured"
        assert descriptor["status"]["reason_code"] == "runtime_context_required"
        assert descriptor["tests"]["integration"]["status"] == "implemented"
        assert descriptor["tests"]["integration"]["references"] == [LIVE_TEST]


def test_registry_sources_name_the_native_odoo_delivery_surfaces(registry) -> None:
    assert registry.describe("invoice.send")["source"]["wizards"] == [
        "account.move.send.wizard"
    ]
    assert registry.describe("payment.receipt.send")["source"]["wizards"] == [
        "mail.compose.message"
    ]
    assert registry.describe("report.customer_statement.send")["source"]["wizards"] == [
        "account.report.send"
    ]
    assert registry.describe("report.followup.send")["source"]["wizards"] == [
        "account.report.send"
    ]
    assert (
        "account.move.line"
        in registry.describe("invoice.followup.update")["source"]["models"]
    )

    for capability_id in ("invoice.send.inspect", "payment.receipt.send.inspect"):
        descriptor = registry.describe(capability_id)
        assert "mail.message" in descriptor["source"]["models"]
        assert "mail.message:read" in descriptor["requirements"]["acl"]

    for capability_id in ("report.customer_statement.export", "report.followup.export"):
        descriptor = registry.describe(capability_id)
        assert "res.currency" in descriptor["source"]["models"]
        assert "res.currency:read" in descriptor["requirements"]["acl"]

    for capability_id in ("report.customer_statement.send", "report.followup.send"):
        assert (
            "res.partner:write"
            in registry.describe(capability_id)["requirements"]["acl"]
        )

    for capability_id in ("invoice.send.inspect", "invoice.send"):
        descriptor = registry.describe(capability_id)
        assert "bill" not in descriptor["summary"]["en_US"].lower()
        assert "Vendor bill delivery" in descriptor["routing"]["not_for"]["en_US"]


@pytest.mark.parametrize("capability_id", [*DELIVERY_IDS, *EXPORT_IDS])
def test_requests_and_responses_validate_against_closed_capability_schemas(
    registry, capability_id: str
) -> None:
    descriptor = registry.describe(capability_id)
    request_reference = descriptor["schemas"]["request"]
    response_reference = descriptor["schemas"]["response"]
    request = _request(capability_id)
    response = _response(capability_id)

    registry.validate_instance(request_reference, request)
    registry.validate_instance(response_reference, response)

    invalid_request = copy.deepcopy(request)
    invalid_request["parameters"]["unexpected"] = True
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(request_reference, invalid_request)

    invalid_response = copy.deepcopy(response)
    invalid_response["data"]["unexpected"] = True
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(response_reference, invalid_response)

    failure = copy.deepcopy(response)
    failure.update(
        {
            "success": False,
            "status": "failed",
            "data": None,
            "error": {
                "code": "ODOO_ERROR",
                "message": "Delivery failed.",
                "details": {},
                "retryable": False,
            },
        }
    )
    registry.validate_instance(response_reference, failure)


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    (
        ("invoice.send", {"move_id": 31, "move_ids": [31, 32]}),
        ("invoice.send", {"move_ids": [31]}),
        ("invoice.send", {"move_ids": [31, 31]}),
        ("payment.receipt.send", {"payment_id": 0}),
        (
            "report.customer_statement.send",
            {
                "partner_id": 21,
                "date_from": "2026-8-1",
                "date_to": "2026-08-31",
            },
        ),
        ("report.followup.send", {"partner_id": 21, "as_of": "2026-02-30"}),
        ("invoice.followup.update", {"move_id": 31, "no_followup": 1}),
    ),
)
def test_delivery_request_schemas_reject_ambiguous_or_invalid_parameters(
    registry, capability_id: str, parameters: dict[str, Any]
) -> None:
    request = _request(capability_id)
    request["parameters"] = parameters
    reference = registry.describe(capability_id)["schemas"]["request"]

    with pytest.raises(InstanceValidationError):
        registry.validate_instance(reference, request)


@pytest.mark.parametrize(
    "capability_id", ["invoice.send.inspect", "payment.receipt.send.inspect"]
)
def test_inspection_response_schema_is_exact(registry, capability_id: str) -> None:
    response = _response(capability_id)
    response["data"]["result"]["records"][0]["unexpected"] = True

    with pytest.raises(InstanceValidationError):
        registry.validate_instance(
            registry.describe(capability_id)["schemas"]["response"], response
        )
