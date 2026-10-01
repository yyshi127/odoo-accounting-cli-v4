"""Closed native payment-term edits and actual invoice-schedule readbacks."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Any

from odoo_accounting_cli_v4.invoice_presentation_contracts import valid_sequence
from odoo_accounting_cli_v4.move_processing_contracts import (
    idempotency_key as _idempotency_key,
)
from odoo_accounting_cli_v4.move_processing_contracts import (
    optional_id,
    valid_date,
    valid_id,
)

GET_ID = "invoice.payment_schedule.inspect"
LIST_ID = "payment_term.usage_moves.list"
READ_IDS = frozenset({GET_ID, LIST_ID})
LINE_KEYS = frozenset({"value", "value_amount", "delay_type", "nb_days", "days_next_month"})
DELAY_TYPES = frozenset({"days_after", "days_after_end_of_month", "days_after_end_of_next_month", "days_end_of_month_on_the"})
PARAMETER_KEYS = {
    "payment_term.duplicate": {"payment_term_id", "name"},
    "payment_term.delete": {"payment_term_id"},
    "payment_term.line.create": {"payment_term_id", "line"},
    "payment_term.line.update": {"payment_term_id", "line_id", "changes"},
    "payment_term.line.delete": {"payment_term_id", "line_id"},
    "payment_term.lines.update": {"payment_term_id", "lines"},
}
CAPABILITY_IDS = frozenset(PARAMETER_KEYS)
MONEY = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?")
INVOICE_TYPES = frozenset({"out_invoice", "in_invoice", "out_refund", "in_refund", "out_receipt", "in_receipt"})
SCHEDULE_FIELDS = frozenset({"id", "company_id", "move_type", "state", "currency_id", "company_currency_id", "payment_term_id", "lines"})
SCHEDULE_LINE_FIELDS = frozenset({"date_maturity", "discount_date", "balance", "amount_currency", "discount_balance", "discount_amount_currency"})
USAGE_FIELDS = ("id", "company_id", "invoice_payment_term_id", "move_type", "state", "name", "partner_id", "currency_id", "date", "invoice_date", "amount_total", "amount_residual")


def idempotency_key(capability_id: str, parameters: dict[str, Any], company_id: int) -> str:
    return _idempotency_key(capability_id, parameters, company_id)


def decimal_text(value: Any) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= 256 and MONEY.fullmatch(value) is not None


def line_values(values: Any, *, partial: bool = False) -> dict[str, Any]:
    if (not isinstance(values, dict) or not values or not set(values) <= LINE_KEYS
        or not partial and set(values) != LINE_KEYS):
        raise ValueError("Payment-term lines require a nonempty fixed-field payload.")
    if "value" in values and (not isinstance(values["value"], str) or values["value"] not in {"percent", "fixed"}):
        raise ValueError("Unknown native payment-term amount type.")
    if "value_amount" in values and not decimal_text(values["value_amount"]):
        raise ValueError("value_amount must be a bounded signed decimal string.")
    if {"value", "value_amount"} <= set(values) and values["value"] == "percent" and not 0 <= Decimal(values["value_amount"]) <= 100:
        raise ValueError("Native payment-term percentages must be between 0 and 100.")
    if "delay_type" in values and (not isinstance(values["delay_type"], str) or values["delay_type"] not in DELAY_TYPES):
        raise ValueError("Unknown native payment-term delay type.")
    if "nb_days" in values and not valid_sequence(values["nb_days"]):
        raise ValueError("nb_days must be a native signed 32-bit integer.")
    if "days_next_month" in values and not (isinstance(values["days_next_month"], int) and not isinstance(values["days_next_month"], bool) and 0 <= values["days_next_month"] <= 31):
        raise ValueError("days_next_month must be a native day 0-31.")
    return dict(values)


def normalize_parameters(capability_id: str, parameters: Any) -> dict[str, Any]:
    if (capability_id not in CAPABILITY_IDS or not isinstance(parameters, dict)
        or set(parameters) != PARAMETER_KEYS[capability_id] or not valid_id(parameters.get("payment_term_id"))):
        raise ValueError("Payment-term processing requires the closed parent-scoped parameters.")
    if "name" in parameters and not (isinstance(parameters["name"], str) and parameters["name"].strip() and len(parameters["name"]) <= 256):
        raise ValueError("Duplicate name must contain 1-256 characters.")
    if "line_id" in parameters and not valid_id(parameters["line_id"]):
        raise ValueError("line_id must be positive.")
    result = dict(parameters)
    if "line" in parameters:
        result["line"] = line_values(parameters["line"])
    if "changes" in parameters:
        result["changes"] = line_values(parameters["changes"], partial=True)
    if "lines" in parameters:
        lines = parameters["lines"]
        if not isinstance(lines, list) or not 2 <= len(lines) <= 100:
            raise ValueError("Atomic line updates require 2-100 existing native lines.")
        normalized = []
        for entry in lines:
            if not isinstance(entry, dict) or set(entry) != {"line_id", "changes"} or not valid_id(entry["line_id"]):
                raise ValueError("Invalid native line update entry.")
            normalized.append({"line_id": entry["line_id"], "changes": line_values(entry["changes"], partial=True)})
        if len({entry["line_id"] for entry in normalized}) != len(normalized):
            raise ValueError("Atomic line IDs must be unique.")
        result["lines"] = sorted(normalized, key=lambda entry: entry["line_id"])
    return result


def valid_read_item(capability_id: str, item: Any, company_id: int) -> bool:
    if (not isinstance(item, dict) or not valid_id(item.get("id"))
        or not valid_id(item.get("company_id")) or item["company_id"] != company_id
        or not valid_id(item.get("currency_id")) or not isinstance(item.get("state"), str)
        or item["state"] not in {"draft", "posted", "cancel"} or not isinstance(item.get("move_type"), str)):
        return False
    if capability_id == GET_ID:
        lines = item.get("lines")
        return (set(item) == SCHEDULE_FIELDS and item["move_type"] in INVOICE_TYPES
                and valid_id(item["company_currency_id"]) and optional_id(item["payment_term_id"])
                and isinstance(lines, list) and len(lines) <= 100000
                and all(isinstance(line, dict) and set(line) == SCHEDULE_LINE_FIELDS
                        and all(line[field] is None or valid_date(line[field]) for field in ("date_maturity", "discount_date"))
                        and all(decimal_text(line[field]) for field in ("balance", "amount_currency", "discount_balance", "discount_amount_currency"))
                        for line in lines))
    return (set(item) == set(USAGE_FIELDS) and item["move_type"] in INVOICE_TYPES | {"entry"}
            and valid_id(item["invoice_payment_term_id"]) and optional_id(item["partner_id"])
            and (item["name"] is None or isinstance(item["name"], str)) and valid_date(item["date"])
            and (item["invoice_date"] is None or valid_date(item["invoice_date"]))
            and all(decimal_text(item[field]) for field in ("amount_total", "amount_residual")))
