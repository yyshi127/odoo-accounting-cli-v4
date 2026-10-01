"""Fixed native invoice and journal-entry processing settings."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from decimal import Decimal
from typing import Any

READ_ID = "accounting_move.processing_settings.get"
INVOICE_TYPES = frozenset({"out_invoice", "in_invoice", "out_refund", "in_refund", "out_receipt", "in_receipt"})
MOVE_TYPES = INVOICE_TYPES | {"entry"}
AUTO_POST = frozenset({"no", "at_date", "monthly", "quarterly", "yearly"})
PARAMETER_KEYS = {
    "invoice.currency_rate.update": {"move_id", "rate"},
    "invoice.currency_rate.refresh": {"move_id"},
    "invoice.cash_rounding.assign": {"move_id", "cash_rounding_id"},
    "invoice.incoterm.update": {"move_id", "changes"},
    "invoice.payment_method.assign": {"move_id", "payment_method_line_id"},
    "invoice.payment_block.set": {"move_id", "blocked"},
    "accounting_move.review.set": {"move_id", "checked"},
    "accounting_move.autopost.configure": {"move_id", "auto_post", "auto_post_until"},
}
CAPABILITY_IDS = frozenset(PARAMETER_KEYS)
READ_FIELDS = (
    "id", "name", "company_id", "move_type", "state", "date", "currency_id",
    "company_currency_id", "invoice_currency_rate", "expected_currency_rate",
    "invoice_cash_rounding_id", "invoice_incoterm_id", "incoterm_location",
    "preferred_payment_method_line_id", "auto_post", "auto_post_until",
    "auto_post_origin_id", "checked", "payment_state",
)
_DECIMAL = re.compile(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?")


def valid_id(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def optional_id(value: Any) -> bool:
    return value is None or valid_id(value)


def valid_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def decimal_text(value: Any, *, positive: bool = False) -> str:
    if not isinstance(value, str) or len(value) > 256 or not _DECIMAL.fullmatch(value):
        raise ValueError("rate must be a finite decimal string without exponent or sign.")
    number = Decimal(value)
    if not number.is_finite() or number < 0 or (positive and number <= 0):
        raise ValueError("The invoice currency rate must be strictly positive.")
    return value.rstrip("0").rstrip(".") if "." in value else value


def native_decimal(value: Any) -> str:
    if isinstance(value, bool) or not isinstance(value, (float, int, Decimal)):
        raise TypeError("invalid native currency rate")
    return decimal_text(format(Decimal(str(value)), "f"))


def normalize_parameters(capability_id: str, parameters: Any) -> dict[str, Any]:
    if capability_id not in CAPABILITY_IDS or not isinstance(parameters, dict) or set(parameters) != PARAMETER_KEYS[capability_id] or not valid_id(parameters.get("move_id")):
        raise ValueError("Move-processing parameters do not match the closed contract.")
    result = dict(parameters)
    if capability_id == "invoice.currency_rate.update":
        result["rate"] = decimal_text(parameters["rate"], positive=True)
    elif capability_id == "invoice.cash_rounding.assign":
        if not optional_id(parameters["cash_rounding_id"]):
            raise ValueError("cash_rounding_id must be null or a positive identifier.")
    elif capability_id == "invoice.payment_method.assign":
        if not optional_id(parameters["payment_method_line_id"]):
            raise ValueError("payment_method_line_id must be null or a positive identifier.")
    elif capability_id == "invoice.incoterm.update":
        changes = parameters["changes"]
        if not isinstance(changes, dict) or not changes or not set(changes) <= {"incoterm_id", "incoterm_location"}:
            raise ValueError("incoterm changes must be a nonempty fixed-field patch.")
        if "incoterm_id" in changes and not optional_id(changes["incoterm_id"]):
            raise ValueError("incoterm_id must be null or a positive identifier.")
        location = changes.get("incoterm_location")
        if location is not None and not (isinstance(location, str) and 1 <= len(location) <= 200 and location == location.strip()):
            raise ValueError("incoterm_location must be null or 1-200 unpadded characters.")
        result["changes"] = dict(changes)
    elif capability_id in {"invoice.payment_block.set", "accounting_move.review.set"}:
        field = "blocked" if capability_id.startswith("invoice.") else "checked"
        if not isinstance(parameters[field], bool):
            raise ValueError(f"{field} must be a boolean.")
    elif capability_id == "accounting_move.autopost.configure":
        until = parameters["auto_post_until"]
        if not isinstance(parameters["auto_post"], str) or parameters["auto_post"] not in AUTO_POST or not (until is None or valid_date(until)):
            raise ValueError("Invalid native auto-post selection or end date.")
        if parameters["auto_post"] in {"no", "at_date"} and until is not None:
            raise ValueError("Native nonrecurring auto-post modes require a null end date.")
    return result


def idempotency_key(capability_id: str, parameters: dict[str, Any], company_id: int) -> str:
    digest = hashlib.sha256(json.dumps(parameters, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()).hexdigest()[:32]
    return f"{capability_id}:{company_id}:{digest}"


def valid_read_item(item: Any, company_id: int) -> bool:
    if not isinstance(item, dict) or set(item) != set(READ_FIELDS):
        return False
    if not all(valid_id(item[field]) for field in ("id", "company_id", "currency_id", "company_currency_id")) or item["company_id"] != company_id:
        return False
    if not all(isinstance(item[field], str) for field in ("move_type", "state", "auto_post")):
        return False
    if item["move_type"] not in MOVE_TYPES or item["state"] not in {"draft", "posted", "cancel"} or item["auto_post"] not in AUTO_POST or not isinstance(item["checked"], bool):
        return False
    if not all(optional_id(item[field]) for field in ("invoice_cash_rounding_id", "invoice_incoterm_id", "preferred_payment_method_line_id", "auto_post_origin_id")):
        return False
    if not valid_date(item["date"]) or not (item["auto_post_until"] is None or valid_date(item["auto_post_until"])):
        return False
    if not all(item[field] is None or isinstance(item[field], str) and bool(item[field].strip()) for field in ("name", "incoterm_location", "payment_state")):
        return False
    try:
        return all(decimal_text(item[field]) == item[field] for field in ("invoice_currency_rate", "expected_currency_rate"))
    except ValueError:
        return False
