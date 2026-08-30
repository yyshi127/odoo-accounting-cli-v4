from __future__ import annotations

import base64
import copy
import hashlib

import pytest

from odoo_accounting_cli_v4.capabilities.document_exports import (
    DOCUMENT_EXPORT_CAPABILITY_IDS,
    DOCUMENT_EXPORT_SPECS,
    DocumentExportError,
    export_document,
    validate_document_export_request,
)

REQUEST_ID = "1cc79a4a-f09b-4c79-a41e-83dd8ee38ee6"


def _request(capability_id: str, *, layout: str = "with_payments") -> dict:
    spec = DOCUMENT_EXPORT_SPECS[capability_id]
    parameters = {spec["id_parameter"]: 37}
    if capability_id == "invoice.pdf.export":
        parameters["layout"] = layout
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "context": {
            "database": "v4-dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": parameters,
    }


def _page(capability_id: str) -> dict:
    content = b"%PDF-1.7\nfixed document"
    return {
        "user_id": 42,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "record_visible": True,
        "applicable": True,
        "filename": "document.pdf",
        "format": "pdf",
        "mimetype": "application/pdf",
        "byte_count": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "content_base64": base64.b64encode(content).decode("ascii"),
    }


class FakePort:
    user_id = 42

    def __init__(self, page: dict) -> None:
        self.page = page
        self.calls: list[dict] = []

    def export(self, **kwargs):
        self.calls.append(kwargs)
        return copy.deepcopy(self.page)


@pytest.mark.parametrize("capability_id", sorted(DOCUMENT_EXPORT_CAPABILITY_IDS))
def test_each_fixed_document_export_returns_verified_pdf(capability_id: str) -> None:
    port = FakePort(_page(capability_id))

    result = export_document(capability_id, port, _request(capability_id))

    assert result == {
        key: port.page[key]
        for key in (
            "filename",
            "format",
            "mimetype",
            "byte_count",
            "sha256",
            "content_base64",
        )
    }
    assert port.calls == [
        {
            "capability_id": capability_id,
            "company_id": 7,
            "target_id": 37,
            "layout": (
                "with_payments" if capability_id == "invoice.pdf.export" else None
            ),
        }
    ]


@pytest.mark.parametrize(
    "change",
    [
        lambda request: request["parameters"].update(extra=True),
        lambda request: request["parameters"].update(move_id=0),
        lambda request: request["parameters"].update(move_id=True),
        lambda request: request["parameters"].update(layout="custom"),
        lambda request: request["parameters"].pop("layout"),
    ],
)
def test_invoice_request_is_closed_and_layout_is_frozen(change) -> None:
    request = _request("invoice.pdf.export")
    change(request)

    with pytest.raises(DocumentExportError) as caught:
        validate_document_export_request("invoice.pdf.export", request)

    assert caught.value.code == "invalid_request"
    assert caught.value.exit_code == 2


@pytest.mark.parametrize("layout", ["with_payments", "without_payments"])
def test_invoice_accepts_only_the_two_fixed_layouts(layout: str) -> None:
    context, target_id, selected_layout = validate_document_export_request(
        "invoice.pdf.export", _request("invoice.pdf.export", layout=layout)
    )

    assert context["company_id"] == 7
    assert target_id == 37
    assert selected_layout == layout


def test_non_invoice_request_rejects_layout_and_invalid_id() -> None:
    request = _request("payment.receipt.pdf.export")
    request["parameters"]["layout"] = "with_payments"
    with pytest.raises(DocumentExportError, match="unsupported"):
        validate_document_export_request("payment.receipt.pdf.export", request)

    request = _request("payment.receipt.pdf.export")
    request["parameters"]["payment_id"] = False
    with pytest.raises(DocumentExportError) as caught:
        validate_document_export_request("payment.receipt.pdf.export", request)
    assert caught.value.code == "invalid_request"


@pytest.mark.parametrize(
    ("field", "value", "expected_code"),
    [
        ("company_visible", False, "company_unavailable"),
        ("module_installed", False, "uninstalled"),
        ("access_allowed", False, "unauthorized"),
        ("record_visible", False, "record_not_found"),
        ("applicable", False, "record_not_applicable"),
    ],
)
def test_typed_empty_pages_preserve_scope_and_applicability_errors(
    field: str, value: bool, expected_code: str
) -> None:
    capability_id = "sale.order.pdf.export"
    page = _page(capability_id)
    page[field] = value
    if field in {"company_visible", "module_installed", "access_allowed"}:
        page["access_allowed"] = False
        page["record_visible"] = False
        page["applicable"] = False
    elif field == "record_visible":
        page["applicable"] = False
    for key in ("filename", "mimetype", "sha256", "content_base64"):
        page[key] = None
    page["byte_count"] = 0

    with pytest.raises(DocumentExportError) as caught:
        export_document(capability_id, FakePort(page), _request(capability_id))

    assert caught.value.code == expected_code


@pytest.mark.parametrize(
    "change",
    [
        lambda page: page.update(filename="document.txt"),
        lambda page: page.update(format="xlsx"),
        lambda page: page.update(mimetype="application/octet-stream"),
        lambda page: page.update(byte_count=1),
        lambda page: page.update(sha256="0" * 64),
        lambda page: page.update(content_base64=page["content_base64"] + "\n"),
        lambda page: page.update(
            content_base64=base64.b64encode(b"not a pdf").decode("ascii"),
            byte_count=len(b"not a pdf"),
            sha256=hashlib.sha256(b"not a pdf").hexdigest(),
        ),
    ],
)
def test_export_rejects_unverified_pdf(change) -> None:
    capability_id = "stock.delivery_slip.pdf.export"
    page = _page(capability_id)
    change(page)

    with pytest.raises(DocumentExportError) as caught:
        export_document(capability_id, FakePort(page), _request(capability_id))

    assert caught.value.code == "failed_validation"
    assert caught.value.exit_code == 8
