"""Fixed native analytic queries and company-owned maintenance operations."""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from odoo_accounting_cli_v4.move_processing_contracts import (
    idempotency_key as _idempotency_key,
)
from odoo_accounting_cli_v4.move_processing_contracts import (
    optional_id,
    valid_id,
)

BALANCE_ID = "analytic.account.balance.inspect"
USAGE_ID = "analytic.account.invoice_usage.inspect"
APPLICABILITY_ID = "analytic.applicability.resolve"
DISTRIBUTION_ID = "analytic.distribution.resolve"
READ_IDS = frozenset({BALANCE_ID, USAGE_ID, APPLICABILITY_ID, DISTRIBUTION_ID})
PARAMETER_KEYS = {
    "analytic.account.duplicate": {"analytic_account_id", "name"},
    "analytic.account.delete": {"analytic_account_id"},
    "analytic.applicability.delete": {"applicability_id"},
    "analytic.distribution_model.delete": {"distribution_model_id"},
}
CAPABILITY_IDS = frozenset(PARAMETER_KEYS)
READ_KEYS = {
    BALANCE_ID: {"analytic_account_id", "date_from", "date_to"},
    USAGE_ID: {"analytic_account_id"},
    APPLICABILITY_ID: {"plan_id", "business_domain", "account_id", "product_id"},
    DISTRIBUTION_ID: {"account_id", "partner_id", "product_id"},
}
MODELS = {
    "analytic.account.duplicate": "account.analytic.account",
    "analytic.account.delete": "account.analytic.account",
    "analytic.applicability.delete": "account.analytic.applicability",
    "analytic.distribution_model.delete": "account.analytic.distribution.model",
}
ID_FIELDS = {
    "analytic.account.duplicate": "analytic_account_id",
    "analytic.account.delete": "analytic_account_id",
    "analytic.applicability.delete": "applicability_id",
    "analytic.distribution_model.delete": "distribution_model_id",
}
APPLICABILITIES = {"optional", "mandatory", "unavailable"}
_DECIMAL = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")


def idempotency_key(capability_id: str, parameters: dict[str, Any], company_id: int) -> str:
    return _idempotency_key(capability_id, parameters, company_id)


def _optional_date(value: Any) -> bool:
    if value is None:
        return True
    if not isinstance(value, str):
        return False
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def normalize_parameters(capability_id: str, parameters: Any) -> dict[str, Any]:
    keys = READ_KEYS.get(capability_id, PARAMETER_KEYS.get(capability_id))
    if keys is None or not isinstance(parameters, dict) or set(parameters) != keys:
        raise ValueError("Analytic processing requires fixed closed parameters.")
    for field, value in parameters.items():
        if field.endswith("_id"):
            valid = optional_id(value) if field in {"account_id", "partner_id", "product_id"} else valid_id(value)
            if not valid:
                raise ValueError(f"{field} requires a positive ID or an allowed null.")
    if "name" in parameters and not (isinstance(parameters["name"], str) and 1 <= len(parameters["name"]) <= 256 and parameters["name"] == parameters["name"].strip()):
        raise ValueError("name requires trimmed bounded text.")
    if "business_domain" in parameters and (not isinstance(parameters["business_domain"], str) or parameters["business_domain"] not in {"general", "invoice", "bill"}):
        raise ValueError("Only native general/invoice/bill business domains are accepted.")
    if capability_id == BALANCE_ID:
        start, end = parameters["date_from"], parameters["date_to"]
        if not _optional_date(start) or not _optional_date(end) or start is not None and end is not None and start > end:
            raise ValueError("Analytic dates must be canonical and ordered, or null.")
    return dict(parameters)


def valid_read_item(capability_id: str, item: Any, company_id: int) -> bool:
    if not isinstance(item, dict) or not valid_id(item.get("id")):
        return False
    if capability_id == DISTRIBUTION_ID:
        distribution = item.get("analytic_distribution")
        return (set(item) == {"id", "company_id", "analytic_distribution"} and item["id"] == item["company_id"] == company_id
                and isinstance(distribution, dict) and len(distribution) <= 1000
                and all(isinstance(key, str) and re.fullmatch(r"[1-9][0-9]*(?:,[1-9][0-9]*)*", key)
                        and isinstance(value, str) and len(value) <= 256 and _DECIMAL.fullmatch(value) and 0 <= float(value) <= 100
                        for key, value in distribution.items()))
    if capability_id == APPLICABILITY_ID:
        return (set(item) == {"id", "company_id", "applicability"} and item["company_id"] == company_id
                and isinstance(item["applicability"], str) and item["applicability"] in APPLICABILITIES)
    if not optional_id(item.get("company_id")) or item["company_id"] not in {None, company_id}:
        return False
    if capability_id == USAGE_ID:
        return (set(item) == {"id", "company_id", "invoice_count", "vendor_bill_count"}
                and all(isinstance(item[field], int) and not isinstance(item[field], bool) and item[field] >= 0 for field in ("invoice_count", "vendor_bill_count")))
    return (capability_id == BALANCE_ID and set(item) == {"id", "company_id", "currency_id", "date_from", "date_to", "debit", "credit", "balance"}
            and valid_id(item["currency_id"]) and _optional_date(item["date_from"]) and _optional_date(item["date_to"])
            and all(isinstance(item[field], str) and _DECIMAL.fullmatch(item[field]) for field in ("debit", "credit", "balance")))
