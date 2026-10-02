"""Closed native tax and payment-term previews without accounting writes."""

from __future__ import annotations

from typing import Any

from odoo_accounting_cli_v4.journal_item_processing_contracts import amount_text
from odoo_accounting_cli_v4.move_processing_contracts import (
    optional_id,
    valid_date,
    valid_id,
)

TAX_ID = "tax.compute"
PAYMENT_TERM_ID = "payment_term.compute"
READ_IDS = frozenset({TAX_ID, PAYMENT_TERM_ID})
TAX_REQUIRED = frozenset({"tax_ids", "currency_id", "price_unit", "quantity"})
PAYMENT_TERM_REQUIRED = frozenset({
    "payment_term_id", "date_ref", "currency_id", "tax_amount", "tax_amount_currency",
    "untaxed_amount", "untaxed_amount_currency",
})
PARAMETER_FIELDS = {
    TAX_ID: TAX_REQUIRED | {"product_id", "partner_id", "is_refund", "handle_price_include", "include_caba_tags"},
    PAYMENT_TERM_ID: PAYMENT_TERM_REQUIRED | {"sign", "cash_rounding_id"},
}
ITEM_FIELDS = {
    TAX_ID: frozenset({
        "id", "company_id", "currency_id", "input", "total_excluded", "total_included",
        "total_void", "base_tag_ids", "taxes",
    }),
    PAYMENT_TERM_ID: frozenset({
        "id", "company_id", "currency_id", "company_currency_id", "input", "total_amount",
        "discount_percentage", "discount_date", "discount_balance", "discount_amount_currency", "line_ids",
    }),
}
TAX_ROW_FIELDS = frozenset({
    "tax_id", "tax_repartition_line_id", "name", "amount", "base", "sequence", "account_id",
    "price_include", "tax_exigibility", "group_tax_id", "tag_ids",
})
TERM_LINE_FIELDS = frozenset({"date", "company_amount", "foreign_amount"})


def _sorted_ids(value: Any) -> bool:
    return (
        isinstance(value, list)
        and all(valid_id(identifier) for identifier in value)
        and value == sorted(set(value))
    )


def normalize_parameters(capability_id: str, parameters: Any) -> dict[str, Any]:
    """Keep supplied totals; cash-rounding previews assume an already-rounded total."""
    if capability_id not in READ_IDS or not isinstance(parameters, dict):
        raise ValueError("Parameters must match a supported settlement preview.")
    required = TAX_REQUIRED if capability_id == TAX_ID else PAYMENT_TERM_REQUIRED
    if not required <= set(parameters) <= PARAMETER_FIELDS[capability_id] or not valid_id(parameters.get("currency_id")):
        raise ValueError("Settlement preview parameters do not match the fixed contract.")
    result = dict(parameters)
    if capability_id == TAX_ID:
        tax_ids = parameters["tax_ids"]
        if not isinstance(tax_ids, list) or len(tax_ids) > 100 or not all(valid_id(identifier) for identifier in tax_ids) or len(tax_ids) != len(set(tax_ids)):
            raise ValueError("tax_ids must contain 0-100 unique positive identifiers.")
        result["tax_ids"] = sorted(tax_ids)
        for field in ("price_unit", "quantity"):
            result[field] = amount_text(parameters[field], signed=True)
        for field in ("product_id", "partner_id"):
            result.setdefault(field, None)
            if not optional_id(result[field]):
                raise ValueError(f"{field} must be null or a positive identifier.")
        for field, default in (("is_refund", False), ("handle_price_include", True), ("include_caba_tags", False)):
            result.setdefault(field, default)
            if not isinstance(result[field], bool):
                raise ValueError(f"{field} must be a boolean.")  # noqa: TRY004
    else:
        if not valid_id(parameters["payment_term_id"]) or not valid_date(parameters["date_ref"]):
            raise ValueError("A positive payment_term_id and ISO date_ref are required.")
        for field in ("tax_amount", "tax_amount_currency", "untaxed_amount", "untaxed_amount_currency"):
            result[field] = amount_text(parameters[field], signed=True)
        result.setdefault("sign", 1)
        if isinstance(result["sign"], bool) or not isinstance(result["sign"], int) or result["sign"] not in {-1, 1}:
            raise ValueError("sign must be the integer -1 or 1.")
        result.setdefault("cash_rounding_id", None)
        if not optional_id(result["cash_rounding_id"]):
            raise ValueError("cash_rounding_id must be null or a positive identifier.")
    return result


def valid_read_item(capability_id: str, item: Any, company_id: int) -> bool:
    if capability_id not in READ_IDS or not isinstance(item, dict) or set(item) != ITEM_FIELDS[capability_id]:
        return False
    if not all(valid_id(item[field]) for field in ("id", "company_id", "currency_id")) or item["company_id"] != company_id:
        return False
    try:
        parameters = normalize_parameters(capability_id, item["input"])
        if item["input"] != parameters or item["currency_id"] != parameters["currency_id"]:
            return False
        if capability_id == TAX_ID:
            if item["id"] != company_id or not _sorted_ids(item["base_tag_ids"]) or not isinstance(item["taxes"], list):
                return False
            for field in ("total_excluded", "total_included", "total_void"):
                amount_text(item[field], signed=True)
            for row in item["taxes"]:
                if not isinstance(row, dict) or set(row) != TAX_ROW_FIELDS or not all(valid_id(row[field]) for field in ("tax_id", "tax_repartition_line_id")):
                    return False
                if not isinstance(row["name"], str) or not row["name"] or isinstance(row["sequence"], bool) or not isinstance(row["sequence"], int):
                    return False
                if not optional_id(row["account_id"]) or not optional_id(row["group_tax_id"]) or not isinstance(row["price_include"], bool) or row["tax_exigibility"] not in {"on_invoice", "on_payment"} or not _sorted_ids(row["tag_ids"]):
                    return False
                for field in ("amount", "base"):
                    amount_text(row[field], signed=True)
        else:
            if item["id"] != parameters["payment_term_id"] or not valid_id(item["company_currency_id"]) or not (item["discount_date"] is None or valid_date(item["discount_date"])) or not isinstance(item["line_ids"], list):
                return False
            amount_text(item["discount_percentage"])
            for field in ("total_amount", "discount_balance", "discount_amount_currency"):
                amount_text(item[field], signed=True)
            for row in item["line_ids"]:
                if not isinstance(row, dict) or set(row) != TERM_LINE_FIELDS or not valid_date(row["date"]):
                    return False
                for field in ("company_amount", "foreign_amount"):
                    amount_text(row[field], signed=True)
    except (KeyError, TypeError, ValueError):
        return False
    return True
