"""Closed contracts for native invoice presentation and fiscal recomputation."""

from __future__ import annotations

from typing import Any

from odoo_accounting_cli_v4.move_processing_contracts import (
    INVOICE_TYPES,
    optional_id,
    valid_id,
)
from odoo_accounting_cli_v4.move_processing_contracts import (
    idempotency_key as _idempotency_key,
)

GET_ID = "invoice.presentation_settings.get"
LIST_ID = "invoice.layout_line.list"
READ_IDS = frozenset({GET_ID, LIST_ID})
LAYOUT_TYPES = frozenset({"line_section", "line_subsection", "line_note"})
LAYOUT_KEYS = frozenset({"display_type", "name", "sequence", "collapse_prices", "collapse_composition"})
PRESENTATION_KEYS = frozenset({"partner_shipping_id", "invoice_user_id", "narration"})
PARAMETER_KEYS = {
    "invoice.presentation_settings.update": {"move_id", "changes"},
    "invoice.layout_line.create": {"move_id", "line"},
    "invoice.layout_line.update": {"move_id", "line_id", "changes"},
    "invoice.layout_line.delete": {"move_id", "line_id"},
    "invoice.lines.resequence": {"move_id", "line_ids"},
    "invoice.fiscal_position.refresh": {"move_id"},
}
CAPABILITY_IDS = frozenset(PARAMETER_KEYS)
GET_FIELDS = ("id", "name", "company_id", "move_type", "state", "partner_id",
              "partner_shipping_id", "invoice_user_id", "narration", "fiscal_position_id")
LINE_FIELDS = ("id", "move_id", "company_id", "display_type", "name", "sequence",
               "collapse_prices", "collapse_composition", "parent_id")


def idempotency_key(capability_id: str, parameters: dict[str, Any], company_id: int) -> str:
    return _idempotency_key(capability_id, parameters, company_id)


def valid_sequence(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and -2147483648 <= value <= 2147483647


def layout_values(values: Any, *, partial: bool = False) -> dict[str, Any]:
    if not isinstance(values, dict) or not values or (not set(values) <= LAYOUT_KEYS if partial else set(values) != LAYOUT_KEYS):
        raise ValueError("Layout values must match the fixed section/subsection/note contract.")
    if "display_type" in values and (not isinstance(values["display_type"], str) or values["display_type"] not in LAYOUT_TYPES):
        raise ValueError("Only native sections, subsections and notes are layout lines.")
    if "name" in values and not (isinstance(values["name"], str) and values["name"].strip() and len(values["name"]) <= 500):
        raise ValueError("Layout name must contain 1-500 characters, not only whitespace.")
    if "sequence" in values and not valid_sequence(values["sequence"]):
        raise ValueError("sequence must be a native signed 32-bit integer.")
    if any(field in values and not isinstance(values[field], bool) for field in ("collapse_prices", "collapse_composition")):
        raise ValueError("Native section visibility flags must be booleans.")
    return dict(values)


def normalize_parameters(capability_id: str, parameters: Any) -> dict[str, Any]:
    if capability_id not in CAPABILITY_IDS or not isinstance(parameters, dict) or set(parameters) != PARAMETER_KEYS[capability_id] or not valid_id(parameters.get("move_id")):
        raise ValueError("Invoice presentation parameters do not match the closed contract.")
    result = dict(parameters)
    if "line_id" in parameters and not valid_id(parameters["line_id"]):
        raise ValueError("line_id must be a positive identifier.")
    if capability_id == "invoice.layout_line.create":
        result["line"] = layout_values(parameters["line"])
    elif capability_id == "invoice.layout_line.update":
        result["changes"] = layout_values(parameters["changes"], partial=True)
    elif capability_id == "invoice.presentation_settings.update":
        changes = parameters["changes"]
        if not isinstance(changes, dict) or not changes or not set(changes) <= PRESENTATION_KEYS:
            raise ValueError("Presentation changes must be a nonempty fixed-field patch.")
        if any(field in changes and not optional_id(changes[field]) for field in ("partner_shipping_id", "invoice_user_id")):
            raise ValueError("Shipping partner and invoice user must be null or positive identifiers.")
        if "narration" in changes and not (changes["narration"] is None or isinstance(changes["narration"], str) and 1 <= len(changes["narration"]) <= 20000):
            raise ValueError("narration must be null or a bounded HTML string sanitized by the native field.")
        result["changes"] = dict(changes)
    elif capability_id == "invoice.lines.resequence":
        ids = parameters["line_ids"]
        if not isinstance(ids, list) or not 1 <= len(ids) <= 500 or not all(valid_id(value) for value in ids) or len(ids) != len(set(ids)):
            raise ValueError("line_ids must be a nonempty ordered unique list of invoice lines.")
        result["line_ids"] = list(ids)
    return result


def valid_read_item(capability_id: str, item: Any, company_id: int) -> bool:
    fields = GET_FIELDS if capability_id == GET_ID else LINE_FIELDS
    if not isinstance(item, dict) or set(item) != set(fields) or not valid_id(item["id"]) or item["company_id"] != company_id or not valid_id(item["company_id"]):
        return False
    if capability_id == GET_ID:
        return (isinstance(item["move_type"], str) and item["move_type"] in INVOICE_TYPES
                and isinstance(item["state"], str) and item["state"] in {"draft", "posted", "cancel"}
                and all(optional_id(item[field]) for field in ("partner_id", "partner_shipping_id", "invoice_user_id", "fiscal_position_id"))
                and all(item[field] is None or isinstance(item[field], str) for field in ("name", "narration")))
    return (valid_id(item["move_id"]) and optional_id(item["parent_id"])
            and isinstance(item["display_type"], str) and item["display_type"] in LAYOUT_TYPES
            and (item["name"] is None or isinstance(item["name"], str)) and valid_sequence(item["sequence"])
            and all(isinstance(item[field], bool) for field in ("collapse_prices", "collapse_composition")))
