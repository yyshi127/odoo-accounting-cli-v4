"""Closed native partner payment, invoice, bill and credit preference contracts."""

from __future__ import annotations

import hashlib
import json
import re
from decimal import Decimal, InvalidOperation
from typing import Any

READ_FIELDS = {
    "partner.payment_preferences.get": (
        "property_inbound_payment_method_line_id",
        "property_outbound_payment_method_line_id",
    ),
    "partner.invoice_delivery_preferences.get": (
        "invoice_sending_method",
        "invoice_edi_format",
        "invoice_template_pdf_report_id",
    ),
    "partner.bill_validation_preferences.get": (
        "autopost_bills",
        "ignore_abnormal_invoice_date",
        "ignore_abnormal_invoice_amount",
    ),
}
PARAMETER_KEYS = {
    "partner.payment_preferences.update": {"partner_id", "changes"},
    "partner.invoice_delivery_preferences.update": {"partner_id", "changes"},
    "partner.bill_validation_preferences.update": {"partner_id", "changes"},
    "partner.credit_limit.update": {"partner_id", "credit_limit"},
    "partner.credit_limit.reset": {"partner_id"},
}
CAPABILITY_IDS = frozenset(PARAMETER_KEYS)
READ_CAPABILITY_IDS = frozenset(READ_FIELDS)
_AMOUNT_PATTERN = re.compile(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?")
READ_HEADER_FIELDS = {
    "id",
    "name",
    "company_id",
    "commercial_partner_id",
    "shared_partner",
}
INVOICE_OPTIONS = {
    "available_sending_methods",
    "available_edi_formats",
    "available_pdf_report_ids",
}


def _valid_id(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def credit_amount(value: Any) -> Decimal:
    if (
        not isinstance(value, str)
        or len(value) > 256
        or not _AMOUNT_PATTERN.fullmatch(value)
    ):
        raise ValueError("credit_limit must be a nonnegative decimal string.")
    try:
        amount = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("credit_limit must be a nonnegative decimal string.") from exc
    if not amount.is_finite() or amount < 0:
        raise ValueError("credit_limit must be finite and nonnegative.")
    return amount


def normalize_parameters(capability_id: str, parameters: Any) -> dict[str, Any]:
    if (
        capability_id not in CAPABILITY_IDS
        or not isinstance(parameters, dict)
        or set(parameters) != PARAMETER_KEYS[capability_id]
        or not _valid_id(parameters.get("partner_id"))
    ):
        raise ValueError(
            "Partner preference parameters do not match the fixed contract."
        )
    result = dict(parameters)
    if capability_id == "partner.credit_limit.update":
        text = format(credit_amount(parameters["credit_limit"]), "f")
        result["credit_limit"] = text.rstrip("0").rstrip(".") if "." in text else text
        return result
    if capability_id == "partner.credit_limit.reset":
        return result
    changes = parameters["changes"]
    fields = READ_FIELDS[capability_id.replace(".update", ".get")]
    if not isinstance(changes, dict) or not changes or not set(changes) <= set(fields):
        raise ValueError("changes must be a nonempty fixed-field preference patch.")
    for field, value in changes.items():
        if field.endswith("_id"):
            valid = value is None or _valid_id(value)
        elif field.startswith("ignore_abnormal_"):
            valid = isinstance(value, bool)
        elif field == "autopost_bills":
            valid = isinstance(value, str) and value in {"always", "ask", "never"}
        else:
            # Installed native selections are checked by the ORM adapter, not invented here.
            valid = (
                value is None
                or isinstance(value, str)
                and 1 <= len(value) <= 128
                and value == value.strip()
            )
        if not valid:
            raise ValueError(f"Invalid partner preference field: {field}.")
    result["changes"] = dict(changes)
    return result


def idempotency_key(
    capability_id: str, parameters: dict[str, Any], company_id: int
) -> str:
    digest = hashlib.sha256(
        json.dumps(
            parameters, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()[:32]
    return f"{capability_id}:{company_id}:{digest}"


def valid_read_item(capability_id: str, item: Any, company_id: int) -> bool:
    invoice = capability_id == "partner.invoice_delivery_preferences.get"
    expected = (
        READ_HEADER_FIELDS
        | set(READ_FIELDS[capability_id])
        | (INVOICE_OPTIONS if invoice else set())
    )
    if not isinstance(item, dict) or set(item) != expected:
        return False
    if (
        not _valid_id(item["id"])
        or not _valid_id(item["commercial_partner_id"])
        or not _valid_id(item["company_id"])
        or item["company_id"] != company_id
        or not isinstance(item["shared_partner"], bool)
    ):
        return False
    if item["name"] is not None and (
        not isinstance(item["name"], str) or not item["name"].strip()
    ):
        return False
    for field in READ_FIELDS[capability_id]:
        value = item[field]
        if field.endswith("_id"):
            valid = value is None or _valid_id(value)
        elif field.startswith("ignore_abnormal_"):
            valid = isinstance(value, bool)
        elif field == "autopost_bills":
            valid = isinstance(value, str) and value in {"always", "ask", "never"}
        else:
            valid = value is None or isinstance(value, str) and bool(value.strip())
        if not valid:
            return False
    if invoice:
        for field in INVOICE_OPTIONS:
            values = item[field]
            if (
                not isinstance(values, list)
                or len(values) > 1000
                or any(
                    not (
                        _valid_id(value)
                        if field == "available_pdf_report_ids"
                        else isinstance(value, str) and bool(value.strip())
                    )
                    for value in values
                )
            ):
                return False
            if values != sorted(set(values)):
                return False
    return True
