"""Closed native tax-repartition edits and scoped tax-processing reads."""

from __future__ import annotations

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
from odoo_accounting_cli_v4.payment_term_processing_contracts import decimal_text
from odoo_accounting_cli_v4.reconciliation_processing_contracts import valid_ids

GET_ID = "tax.processing_settings.get"
LIST_ID = "tax.usage_lines.list"
READ_IDS = frozenset({GET_ID, LIST_ID})
LINE_KEYS = frozenset({"sequence", "repartition_type", "factor_percent", "account_id", "tag_ids", "use_in_tax_closing"})
PARAMETER_KEYS = {
    "tax.delete": {"tax_id"},
    "tax.repartition_line.update": {"tax_id", "line_id", "changes"},
    "tax.repartition_pair.create": {"tax_id", "invoice_line", "refund_line"},
    "tax.repartition_pair.delete": {"tax_id", "invoice_line_id", "refund_line_id"},
    "tax.repartition_lines.update": {"tax_id", "lines"},
    "tax.repartition_lines.resequence": {"tax_id", "invoice_line_ids", "refund_line_ids"},
}
CAPABILITY_IDS = frozenset(PARAMETER_KEYS)
GET_FIELDS = ("id", "company_id", "active", "tax_scope", "tax_exigibility", "cash_basis_transition_account_id",
              "price_include_override", "price_include", "analytic", "is_used", "has_negative_factor",
              "children_tax_ids", "invoice_repartition_line_ids", "refund_repartition_line_ids", "country_id")
USAGE_FIELDS = ("id", "company_id", "move_id", "account_id", "parent_state", "date", "name", "balance",
                "amount_currency", "currency_id", "tax_line_id", "group_tax_id", "tax_ids", "tax_repartition_line_id")


def idempotency_key(capability_id: str, parameters: dict[str, Any], company_id: int) -> str:
    return _idempotency_key(capability_id, parameters, company_id)


def line_values(values: Any, *, partial: bool = False) -> dict[str, Any]:
    if (not isinstance(values, dict) or not values or not set(values) <= LINE_KEYS
        or not partial and set(values) != LINE_KEYS):
        raise ValueError("Tax repartition lines require the fixed-field payload.")
    if "sequence" in values and not valid_sequence(values["sequence"]):
        raise ValueError("sequence must be a native signed 32-bit integer.")
    if "repartition_type" in values and (not isinstance(values["repartition_type"], str) or values["repartition_type"] not in {"base", "tax"}):
        raise ValueError("repartition_type must be base or tax.")
    if "factor_percent" in values and not decimal_text(values["factor_percent"]):
        raise ValueError("factor_percent must be a bounded signed decimal string.")
    if "account_id" in values and not optional_id(values["account_id"]):
        raise ValueError("account_id must be null or positive.")
    if "tag_ids" in values and not valid_ids(values["tag_ids"], 100):
        raise ValueError("tag_ids must be unique positive identifiers.")
    if "use_in_tax_closing" in values and not isinstance(values["use_in_tax_closing"], bool):
        raise ValueError("use_in_tax_closing must be a boolean.")
    result = dict(values)
    if "tag_ids" in result:
        result["tag_ids"] = sorted(result["tag_ids"])
    if "factor_percent" in result:
        text = result["factor_percent"]
        result["factor_percent"] = text.rstrip("0").rstrip(".") if "." in text else text
        if result["factor_percent"] in {"-0", "0"}:
            result["factor_percent"] = "0"
        if "." in result["factor_percent"] and len(result["factor_percent"].split(".")[1]) > 12:
            raise ValueError("Native tax factors have at most twelve decimal places.")
    return result


def normalize_parameters(capability_id: str, parameters: Any) -> dict[str, Any]:
    if (capability_id not in CAPABILITY_IDS or not isinstance(parameters, dict)
        or set(parameters) != PARAMETER_KEYS[capability_id] or not valid_id(parameters.get("tax_id"))):
        raise ValueError("Tax processing requires closed parent-scoped parameters.")
    for field in ("line_id", "invoice_line_id", "refund_line_id"):
        if field in parameters and not valid_id(parameters[field]):
            raise ValueError("Native line IDs must be positive.")
    result = dict(parameters)
    for field in ("invoice_line", "refund_line", "changes"):
        if field in parameters:
            result[field] = line_values(parameters[field], partial=field == "changes")
    if "lines" in parameters:
        lines = parameters["lines"]
        if not isinstance(lines, list) or not 2 <= len(lines) <= 200:
            raise ValueError("Atomic tax updates require 2-200 existing lines.")
        normalized = []
        for entry in lines:
            if not isinstance(entry, dict) or set(entry) != {"line_id", "changes"} or not valid_id(entry["line_id"]):
                raise ValueError("Invalid tax line update entry.")
            normalized.append({"line_id": entry["line_id"], "changes": line_values(entry["changes"], partial=True)})
        if len({entry["line_id"] for entry in normalized}) != len(normalized):
            raise ValueError("Atomic tax line IDs must be unique.")
        result["lines"] = sorted(normalized, key=lambda entry: entry["line_id"])
    for field in ("invoice_line_ids", "refund_line_ids"):
        if field in parameters and not valid_ids(parameters[field], 1000):
            raise ValueError("Ordering requires unique native line IDs.")
    if "invoice_line_ids" in parameters and set(parameters["invoice_line_ids"]) & set(parameters["refund_line_ids"]):
        raise ValueError("Invoice/refund line IDs cannot overlap.")
    return result


def valid_read_item(capability_id: str, item: Any, company_id: int) -> bool:
    fields = GET_FIELDS if capability_id == GET_ID else USAGE_FIELDS
    if (capability_id not in READ_IDS or not isinstance(item, dict) or set(item) != set(fields)
        or not valid_id(item["id"]) or not valid_id(item["company_id"]) or item["company_id"] != company_id):
        return False
    if capability_id == GET_ID:
        return (all(isinstance(item[field], bool) for field in ("active", "price_include", "analytic", "is_used", "has_negative_factor"))
                and item["tax_scope"] in (None, "service", "consu") and item["tax_exigibility"] in ("on_invoice", "on_payment")
                and item["price_include_override"] in (None, "tax_included", "tax_excluded")
                and all(optional_id(item[field]) for field in ("cash_basis_transition_account_id", "country_id"))
                and all(valid_ids(item[field], 100000) for field in ("children_tax_ids", "invoice_repartition_line_ids", "refund_repartition_line_ids"))
                and not set(item["invoice_repartition_line_ids"]) & set(item["refund_repartition_line_ids"]))
    return (all(valid_id(item[field]) for field in ("move_id", "account_id", "currency_id"))
            and all(optional_id(item[field]) for field in ("tax_line_id", "group_tax_id", "tax_repartition_line_id"))
            and valid_ids(item["tax_ids"], 100000) and item["parent_state"] in ("draft", "posted", "cancel")
            and valid_date(item["date"]) and (item["name"] is None or isinstance(item["name"], str))
            and all(decimal_text(item[field]) for field in ("balance", "amount_currency")))
