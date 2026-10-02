"""Closed line-targeted accounting operations; native accounting rules apply."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Any

from odoo_accounting_cli_v4.move_processing_contracts import (
    idempotency_key as _idempotency_key,
)
from odoo_accounting_cli_v4.move_processing_contracts import (
    optional_id,
    valid_date,
    valid_id,
)

DETAIL_ID = "journal_item.processing_details.get"
RECONCILIATION_ID = "journal_item.reconciliation.inspect"
ANALYTIC_LIST_ID = "journal_item.analytic_lines.list"
GET_IDS = frozenset({DETAIL_ID, RECONCILIATION_ID})
READ_IDS = GET_IDS | {ANALYTIC_LIST_ID}
PARAMETER_KEYS = {
    "journal_item.date_maturity.update": {"move_id", "line_id", "date_maturity"},
    "journal_item.analytic_distribution.replace": {"move_id", "line_id", "analytic_distribution"},
    "invoice.line.unit.assign": {"move_id", "line_id", "product_uom_id"},
    "invoice.line.deductibility.update": {"move_id", "line_id", "deductible_amount"},
    "journal_entry.lines.update": {"move_id", "lines"},
}
CAPABILITY_IDS = frozenset(PARAMETER_KEYS)
TAX_FIELDS = {"tax_ids", "tax_tag_ids", "tax_repartition_line_id", "tax_base_amount"}
ENTRY_FIELDS = {"name", "account_id", "partner_id", "debit", "credit", "currency_id", "amount_currency", "date_maturity", "analytic_distribution"} | TAX_FIELDS
DETAIL_FIELDS = (
    "id", "move_id", "company_id", "parent_state", "move_type", "display_type",
    "account_id", "product_id", "product_uom_id", "deductible_amount", "date_maturity",
    "amount_residual", "amount_residual_currency", "discount_date", "discount_amount_currency",
    "payment_id", "statement_line_id", "no_followup", "currency_id", "company_currency_id",
    "tax_ids", "tax_line_id", "tax_base_amount", "tax_tag_ids", "tax_repartition_line_id",
)
RECONCILIATION_FIELDS = (
    "id", "move_id", "company_id", "reconciled", "matching_number", "amount_residual",
    "amount_residual_currency", "currency_id", "company_currency_id", "partial_reconcile_ids",
    "full_reconcile_id", "reconciled_journal_item_ids",
)
_DECIMAL = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?")
_KEY = re.compile(r"[1-9][0-9]*(?:,[1-9][0-9]*)*")


def idempotency_key(capability_id: str, parameters: dict[str, Any], company_id: int) -> str:
    return _idempotency_key(capability_id, parameters, company_id)


def amount_text(value: Any, *, signed: bool = False, places: int | None = None) -> str:
    if not isinstance(value, str) or len(value) > 256 or not _DECIMAL.fullmatch(value):
        raise ValueError("Amounts must be finite canonical decimal strings.")
    number = Decimal(value)
    canonical = format(number, "f").rstrip("0").rstrip(".") if "." in value else format(number, "f")
    canonical = "0" if number == 0 else canonical
    if value != canonical or (not signed and number < 0) or (places is not None and max(0, -number.as_tuple().exponent) > places):
        raise ValueError("Invalid amount sign, precision or canonical representation.")
    return value


def distribution(value: Any) -> dict[str, str] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or not 1 <= len(value) <= 16:
        raise ValueError("Use null to clear or 1-16 closed analytic distribution keys.")
    seen: set[int] = set()
    for key, text in value.items():
        if not isinstance(key, str) or not _KEY.fullmatch(key):
            raise ValueError("Analytic keys must contain sorted unique positive identifiers.")
        ids = [int(part) for part in key.split(",")]
        if ids != sorted(set(ids)) or seen.intersection(ids):
            raise ValueError("Analytic identifiers must be unique across distribution keys.")
        seen.update(ids)
        if not 0 < Decimal(amount_text(text, places=4)) <= 100:
            raise ValueError("Analytic percentages must be greater than zero and at most 100.")
    return dict(sorted(value.items()))


def _changes(values: Any) -> dict[str, Any]:
    if not isinstance(values, dict) or not values or not set(values) <= ENTRY_FIELDS:
        raise ValueError("Entry updates require a nonempty fixed-field patch.")
    result = dict(values)
    if "currency_id" in values and "amount_currency" not in values:
        raise ValueError("Changing line currency also requires amount_currency.")
    for field, value in values.items():
        if field == "name" and not (isinstance(value, str) and 1 <= len(value) <= 256 and value == value.strip()):
            raise ValueError("Line name must be a trimmed 1-256 character string.")
        if field == "account_id" and not valid_id(value) or field == "partner_id" and not optional_id(value):
            raise ValueError("Invalid accounting-line reference.")
        if field == "currency_id" and not valid_id(value):
            raise ValueError("A positive currency_id is required.")
        if field == "date_maturity" and not (value is None or valid_date(value)):
            raise ValueError("Maturity must be null or an ISO date.")
        if field in {"debit", "credit"}:
            result[field] = amount_text(value)
        if field == "amount_currency":
            result[field] = amount_text(value, signed=True)
        if field == "analytic_distribution":
            result[field] = distribution(value)
        if field in {"tax_ids", "tax_tag_ids"}:
            if not isinstance(value, list) or len(value) > 100 or not all(valid_id(item) for item in value) or value != sorted(set(value)):
                raise ValueError("Tax references must be 0-100 sorted unique positive identifiers.")
            result[field] = list(value)
        if field == "tax_repartition_line_id" and not optional_id(value):
            raise ValueError("Tax repartition reference must be null or a positive identifier.")
        if field == "tax_base_amount":
            result[field] = amount_text(value, signed=True)
    return result


def normalize_parameters(capability_id: str, parameters: Any) -> dict[str, Any]:
    if capability_id not in CAPABILITY_IDS | GET_IDS or not isinstance(parameters, dict):
        raise ValueError("Parameters must match a closed supported operation.")
    if capability_id in GET_IDS:
        if set(parameters) != {"journal_item_id"} or not valid_id(parameters["journal_item_id"]):
            raise ValueError("A positive journal_item_id is required.")
        return dict(parameters)
    if capability_id not in CAPABILITY_IDS or set(parameters) != PARAMETER_KEYS[capability_id] or not valid_id(parameters.get("move_id")):
        raise ValueError("Line-processing parameters do not match the closed operation.")
    result = dict(parameters)
    if capability_id == "journal_entry.lines.update":
        lines = parameters["lines"]
        if not isinstance(lines, list) or not 1 <= len(lines) <= 100:
            raise ValueError("Update 1-100 existing lines in one balanced parent write.")
        for line in lines:
            if not isinstance(line, dict) or set(line) != {"line_id", "changes"} or not valid_id(line["line_id"]):
                raise ValueError("Each existing-line update needs line_id and changes only.")
        ids = [line["line_id"] for line in lines]
        if ids != sorted(set(ids)):
            raise ValueError("Existing line IDs must be sorted and unique.")
        result["lines"] = [{"line_id": line["line_id"], "changes": _changes(line["changes"])} for line in lines]
        return result
    if not valid_id(parameters["line_id"]):
        raise ValueError("A positive line_id bound to move_id is required.")
    if "date_maturity" in parameters and not (parameters["date_maturity"] is None or valid_date(parameters["date_maturity"])):
        raise ValueError("Maturity must be null or an ISO date.")
    if "analytic_distribution" in parameters:
        result["analytic_distribution"] = distribution(parameters["analytic_distribution"])
    if "product_uom_id" in parameters and not valid_id(parameters["product_uom_id"]):
        raise ValueError("A positive product_uom_id is required.")
    if "deductible_amount" in parameters:
        result["deductible_amount"] = amount_text(parameters["deductible_amount"], places=2)
        if Decimal(result["deductible_amount"]) > 100:
            raise ValueError("Deductibility must be between zero and 100 percent.")
    return result


def valid_read_item(capability_id: str, item: Any, company_id: int) -> bool:
    fields = DETAIL_FIELDS if capability_id == DETAIL_ID else RECONCILIATION_FIELDS
    optional_fields = TAX_FIELDS | {"tax_line_id"} if capability_id == DETAIL_ID else set()
    required_fields = set(fields) - optional_fields
    if capability_id not in GET_IDS or not isinstance(item, dict) or not required_fields <= set(item) <= set(fields):
        return False
    if not all(valid_id(item[field]) for field in ("id", "move_id", "company_id", "currency_id", "company_currency_id")) or item["company_id"] != company_id:
        return False
    try:
        for field in ("amount_residual", "amount_residual_currency"):
            amount_text(item[field], signed=True)
        if capability_id == DETAIL_ID:
            if any(field in item and not optional_id(item[field]) for field in ("tax_line_id", "tax_repartition_line_id")):
                return False
            for field in ("tax_ids", "tax_tag_ids"):
                if field in item and (not isinstance(item[field], list) or not all(valid_id(value) for value in item[field]) or item[field] != sorted(set(item[field]))):
                    return False
            if "tax_base_amount" in item:
                amount_text(item["tax_base_amount"], signed=True)
            amount_text(item["discount_amount_currency"], signed=True)
            if not 0 <= Decimal(amount_text(item["deductible_amount"])) <= 100:
                return False
            return (item["parent_state"] in {"draft", "posted", "cancel"}
                    and item["move_type"] in {"entry", "out_invoice", "in_invoice", "out_refund", "in_refund", "out_receipt", "in_receipt"}
                    and isinstance(item["display_type"], str) and bool(item["display_type"])
                    and isinstance(item["no_followup"], bool)
                    and all(optional_id(item[field]) for field in ("account_id", "product_id", "product_uom_id", "payment_id", "statement_line_id"))
                    and all(item[field] is None or valid_date(item[field]) for field in ("date_maturity", "discount_date")))
        return (isinstance(item["reconciled"], bool) and optional_id(item["full_reconcile_id"])
                and (item["matching_number"] is None or isinstance(item["matching_number"], str) and bool(item["matching_number"].strip()))
                and item["id"] not in item["reconciled_journal_item_ids"]
                and all(isinstance(item[field], list) and all(valid_id(value) for value in item[field])
                        and item[field] == sorted(set(item[field])) for field in ("partial_reconcile_ids", "reconciled_journal_item_ids")))
    except (ValueError, TypeError):
        return False
