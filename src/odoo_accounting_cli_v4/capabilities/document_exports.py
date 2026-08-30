"""Strict contracts for fixed read-only business-document PDF exports."""

from __future__ import annotations

import base64
import binascii
import hashlib
import re
import uuid
from typing import Any, Protocol

DOCUMENT_EXPORT_SPECS = {
    "invoice.pdf.export": {
        "id_parameter": "move_id",
        "model": "account.move",
        "layouts": frozenset({"with_payments", "without_payments"}),
    },
    "payment.receipt.pdf.export": {
        "id_parameter": "payment_id",
        "model": "account.payment",
    },
    "bank.statement.pdf.export": {
        "id_parameter": "statement_id",
        "model": "account.bank.statement",
    },
    "sale.order.pdf.export": {
        "id_parameter": "order_id",
        "model": "sale.order",
    },
    "purchase.order.pdf.export": {
        "id_parameter": "order_id",
        "model": "purchase.order",
    },
    "purchase.rfq.pdf.export": {
        "id_parameter": "order_id",
        "model": "purchase.order",
    },
    "stock.delivery_slip.pdf.export": {
        "id_parameter": "transfer_id",
        "model": "stock.picking",
    },
    "stock.picking_operations.pdf.export": {
        "id_parameter": "transfer_id",
        "model": "stock.picking",
    },
    "stock.return_slip.pdf.export": {
        "id_parameter": "transfer_id",
        "model": "stock.picking",
    },
    "localization.china.voucher.render": {
        "id_parameter": "move_id",
        "model": "account.move",
    },
}
DOCUMENT_EXPORT_CAPABILITY_IDS = frozenset(DOCUMENT_EXPORT_SPECS)
_PAGE_KEYS = {
    "user_id",
    "company_visible",
    "module_installed",
    "access_allowed",
    "record_visible",
    "applicable",
    "filename",
    "format",
    "mimetype",
    "byte_count",
    "sha256",
    "content_base64",
}
_NULLABLE_BINARY_KEYS = ("filename", "mimetype", "sha256", "content_base64")


class DocumentExportPort(Protocol):
    @property
    def user_id(self) -> int: ...

    def export(
        self,
        *,
        capability_id: str,
        company_id: int,
        target_id: int,
        layout: str | None,
    ) -> dict[str, Any]: ...


class DocumentExportError(RuntimeError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        exit_code: int,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code
        self.retryable = retryable
        self.details = details or {}


def _invalid(message: str) -> DocumentExportError:
    return DocumentExportError("invalid_request", message, exit_code=2)


def _failed(message: str) -> DocumentExportError:
    return DocumentExportError("failed_validation", message, exit_code=8)


def _positive_id(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_envelope(request: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(request, dict) or set(request) != {
        "schema_version",
        "request_id",
        "context",
        "parameters",
    }:
        raise _invalid("The request must match the v1 request envelope.")
    if request["schema_version"] != "v1":
        raise _invalid("schema_version must be 'v1'.")
    request_id = request["request_id"]
    if not isinstance(request_id, str):
        raise _invalid("request_id must be a UUID string.")
    try:
        parsed = uuid.UUID(request_id)
    except (AttributeError, ValueError) as exc:
        raise _invalid("request_id must be a UUID string.") from exc
    if (
        str(parsed) != request_id.lower()
        or parsed.version not in {1, 2, 3, 4, 5}
        or parsed.variant != uuid.RFC_4122
    ):
        raise _invalid("request_id must use canonical UUID syntax.")

    context = request["context"]
    if not isinstance(context, dict) or set(context) != {
        "database",
        "company_id",
        "user_login",
        "language",
        "timezone",
    }:
        raise _invalid("context must contain only the required v1 fields.")
    for key in ("database", "user_login", "language", "timezone"):
        if not _nonempty_string(context[key]):
            raise _invalid(f"context.{key} must be a non-empty string.")
    if not _positive_id(context["company_id"]):
        raise _invalid("context.company_id must be a positive integer.")

    parameters = request["parameters"]
    if not isinstance(parameters, dict):
        raise _invalid("parameters must be an object.")
    return context, parameters


def validate_document_export_request(
    capability_id: str, request: Any
) -> tuple[dict[str, Any], int, str | None]:
    """Validate one closed single-record PDF export request."""

    try:
        spec = DOCUMENT_EXPORT_SPECS[capability_id]
    except (KeyError, TypeError) as exc:
        raise _invalid("The document-export capability is unsupported.") from exc
    context, parameters = _validate_envelope(request)
    expected = {spec["id_parameter"]}
    layouts = spec.get("layouts")
    if layouts is not None:
        expected.add("layout")
    elif "layout" in parameters:
        raise _invalid("layout is unsupported for this document export.")
    if set(parameters) != expected:
        names = ", ".join(sorted(expected))
        raise _invalid(f"{capability_id} requires only {names}.")
    target_id = parameters[spec["id_parameter"]]
    if not _positive_id(target_id):
        raise _invalid(f"{spec['id_parameter']} must be a positive integer.")
    layout = parameters.get("layout")
    if layouts is not None:
        if not isinstance(layout, str) or layout not in layouts:
            raise _invalid("layout must be 'with_payments' or 'without_payments'.")
    elif layout is not None:
        raise _invalid("layout is unsupported for this document export.")
    return context, target_id, layout


def _validated_page(
    port: DocumentExportPort,
    page: Any,
) -> dict[str, Any]:
    if (
        not isinstance(page, dict)
        or set(page) != _PAGE_KEYS
        or not _positive_id(page["user_id"])
        or not _positive_id(port.user_id)
        or page["user_id"] != port.user_id
        or not all(
            isinstance(page[key], bool)
            for key in (
                "company_visible",
                "module_installed",
                "access_allowed",
                "record_visible",
                "applicable",
            )
        )
        or page["access_allowed"]
        and not (page["company_visible"] and page["module_installed"])
        or page["record_visible"]
        and not page["access_allowed"]
        or page["applicable"]
        and not page["record_visible"]
        or page["format"] != "pdf"
        or not isinstance(page["byte_count"], int)
        or isinstance(page["byte_count"], bool)
        or page["byte_count"] < 0
        or any(
            page[key] is not None and not isinstance(page[key], str)
            for key in _NULLABLE_BINARY_KEYS
        )
        or not page["applicable"]
        and (
            page["byte_count"] != 0
            or any(page[key] is not None for key in _NULLABLE_BINARY_KEYS)
        )
    ):
        raise _failed("Odoo returned an invalid document export.")
    return page


def export_document(
    capability_id: str,
    port: DocumentExportPort,
    request: dict[str, Any],
) -> dict[str, Any]:
    """Export one fixed Odoo business document and verify its PDF content."""

    context, target_id, layout = validate_document_export_request(
        capability_id, request
    )
    page = _validated_page(
        port,
        port.export(
            capability_id=capability_id,
            company_id=context["company_id"],
            target_id=target_id,
            layout=layout,
        ),
    )
    if not page["company_visible"]:
        raise DocumentExportError(
            "company_unavailable",
            "The requested company is unavailable to the configured user.",
            exit_code=3,
        )
    if not page["module_installed"]:
        raise DocumentExportError(
            "uninstalled",
            "The requested document report is not installed.",
            exit_code=4,
        )
    if not page["access_allowed"]:
        raise DocumentExportError(
            "unauthorized",
            "The configured user cannot export this document.",
            exit_code=3,
        )
    if not page["record_visible"]:
        raise DocumentExportError(
            "record_not_found",
            "The requested document was not found.",
            exit_code=4,
        )
    if not page["applicable"]:
        raise DocumentExportError(
            "record_not_applicable",
            "The requested document cannot use this report in its current type or state.",
            exit_code=4,
        )

    filename = page["filename"]
    mimetype = page["mimetype"]
    sha256 = page["sha256"]
    content_base64 = page["content_base64"]
    if (
        not _nonempty_string(filename)
        or not filename.lower().endswith(".pdf")
        or mimetype != "application/pdf"
        or not isinstance(sha256, str)
        or re.fullmatch(r"[0-9a-f]{64}", sha256) is None
        or not isinstance(content_base64, str)
        or not content_base64
    ):
        raise _failed("Odoo returned invalid document-export metadata.")
    try:
        content = base64.b64decode(content_base64.encode("ascii"), validate=True)
    except (UnicodeEncodeError, ValueError, binascii.Error) as exc:
        raise _failed("Odoo returned invalid document-export content.") from exc
    if (
        base64.b64encode(content).decode("ascii") != content_base64
        or len(content) != page["byte_count"]
        or hashlib.sha256(content).hexdigest() != sha256
        or not content.startswith(b"%PDF-")
    ):
        raise _failed("Odoo returned invalid document-export content.")
    return {
        "filename": filename,
        "format": "pdf",
        "mimetype": mimetype,
        "byte_count": page["byte_count"],
        "sha256": sha256,
        "content_base64": content_base64,
    }
