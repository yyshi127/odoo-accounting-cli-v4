from __future__ import annotations

import copy

import pytest

from odoo_accounting_cli_v4.registry import (
    InstanceValidationError,
    load_registry,
)

EXPORTS = {
    "invoice.pdf.export": ("account.move", "move_id", True),
    "payment.receipt.pdf.export": ("account.payment", "payment_id", False),
    "bank.statement.pdf.export": (
        "account.bank.statement",
        "statement_id",
        False,
    ),
    "sale.order.pdf.export": ("sale.order", "order_id", False),
    "purchase.order.pdf.export": ("purchase.order", "order_id", False),
    "purchase.rfq.pdf.export": ("purchase.order", "order_id", False),
    "stock.delivery_slip.pdf.export": ("stock.picking", "transfer_id", False),
    "stock.picking_operations.pdf.export": (
        "stock.picking",
        "transfer_id",
        False,
    ),
    "stock.return_slip.pdf.export": ("stock.picking", "transfer_id", False),
    "localization.china.voucher.render": ("account.move", "move_id", False),
}
REQUEST_ID = "123e4567-e89b-42d3-a456-426614174000"


@pytest.fixture(scope="module")
def registry():
    return load_registry()


def _request(id_parameter: str, *, has_layout: bool) -> dict[str, object]:
    parameters: dict[str, object] = {id_parameter: 37}
    if has_layout:
        parameters["layout"] = "with_payments"
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
        "parameters": parameters,
    }


def _response(capability_id: str, model: str) -> dict[str, object]:
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "success": True,
        "capability": capability_id,
        "status": "verified",
        "data": {
            "filename": "document.pdf",
            "format": "pdf",
            "mimetype": "application/pdf",
            "byte_count": 8,
            "sha256": "0" * 64,
            "content_base64": "JVBERi0=",
        },
        "warnings": [],
        "error": None,
        "odoo": {
            "database": "odoo_cli_v4_dev",
            "company_id": 1,
            "user_id": 5,
            "model": model,
            "record_ids": [37],
        },
        "audit": {
            "operation_id": None,
            "idempotency_key": None,
            "verification": {"read_only": True},
        },
    }


def test_all_ten_document_exports_are_registered_as_fixed_reads(registry) -> None:
    assert set(EXPORTS) <= set(registry.ids())

    for capability_id, (model, _, _) in EXPORTS.items():
        descriptor = registry.describe(capability_id)
        expected_models = {model, "res.company", "ir.actions.report"}
        expected_acl = {
            f"{model}:read",
            "res.company:read",
            "ir.actions.report:read",
        }
        if capability_id == "localization.china.voucher.render":
            expected_models.add("res.country")
            expected_acl.add("res.country:read")
        assert descriptor["access"] == "read"
        assert descriptor["handler_key"] == (
            f"document_{capability_id.replace('.', '_')}"
        )
        assert descriptor["status"]["value"] == "unconfigured"
        assert set(descriptor["source"]["models"]) == expected_models
        assert set(descriptor["requirements"]["acl"]) == expected_acl


@pytest.mark.parametrize("capability_id,definition", EXPORTS.items())
def test_document_export_request_schemas_are_closed_and_specific(
    registry,
    capability_id: str,
    definition: tuple[str, str, bool],
) -> None:
    _, id_parameter, has_layout = definition
    descriptor = registry.describe(capability_id)
    reference = descriptor["schemas"]["request"]
    request = _request(id_parameter, has_layout=has_layout)

    registry.validate_instance(reference, request)

    schema = registry.load_schema(reference)
    parameters = schema["$defs"]["parameters"]
    expected = {id_parameter, "layout"} if has_layout else {id_parameter}
    assert schema["$id"].endswith(f"{capability_id}.request.schema.json")
    assert schema["additionalProperties"] is False
    assert parameters["additionalProperties"] is False
    assert set(parameters["required"]) == expected
    assert set(parameters["properties"]) == expected
    assert parameters["properties"][id_parameter]["type"] == "integer"
    assert parameters["properties"][id_parameter]["minimum"] == 1
    if has_layout:
        assert parameters["properties"]["layout"]["enum"] == [
            "with_payments",
            "without_payments",
        ]

    invalid = copy.deepcopy(request)
    invalid["parameters"]["unexpected"] = True
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(reference, invalid)

    invalid = copy.deepcopy(request)
    invalid["parameters"][id_parameter] = 0
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(reference, invalid)


@pytest.mark.parametrize("capability_id,definition", EXPORTS.items())
def test_document_export_response_schemas_are_exact_pdf_envelopes(
    registry,
    capability_id: str,
    definition: tuple[str, str, bool],
) -> None:
    model, _, _ = definition
    descriptor = registry.describe(capability_id)
    reference = descriptor["schemas"]["response"]
    response = _response(capability_id, model)

    registry.validate_instance(reference, response)

    schema = registry.load_schema(reference)
    data = schema["$defs"]["data"]
    fields = {
        "filename",
        "format",
        "mimetype",
        "byte_count",
        "sha256",
        "content_base64",
    }
    assert schema["$id"].endswith(f"{capability_id}.response.schema.json")
    assert schema["additionalProperties"] is False
    assert data["additionalProperties"] is False
    assert set(data["required"]) == fields
    assert set(data["properties"]) == fields
    assert data["properties"]["format"]["const"] == "pdf"

    invalid = copy.deepcopy(response)
    invalid["data"]["unexpected"] = True
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
