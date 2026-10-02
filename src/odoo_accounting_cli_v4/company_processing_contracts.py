"""Closed current-company operating settings; native company ACLs still apply."""

from __future__ import annotations

from typing import Any

from odoo_accounting_cli_v4.move_processing_contracts import (
    idempotency_key as _idempotency_key,
)
from odoo_accounting_cli_v4.move_processing_contracts import optional_id, valid_id

GET_ID = "company.processing_settings.get"
READ_IDS = frozenset({GET_ID})
FIELD_GROUPS = {
    "company.fiscal_year_end.update": {"fiscalyear_last_day", "fiscalyear_last_month"},
    "company.tax_policy.update": {"account_sale_tax_id", "account_purchase_tax_id", "tax_calculation_rounding_method", "account_price_include"},
    "company.cash_discount_accounts.assign": {"account_journal_early_pay_discount_gain_account_id", "account_journal_early_pay_discount_loss_account_id"},
    "company.exchange_configuration.update": {"currency_exchange_journal_id", "income_currency_exchange_account_id", "expense_currency_exchange_account_id"},
    "company.invoice_display.update": {"qr_code", "link_qr_code", "display_invoice_amount_total_words", "display_invoice_tax_company_currency"},
    "company.credit_policy.update": {"account_use_credit_limit"},
    "company.bill_processing_policy.update": {"quick_edit_mode", "autopost_bills"},
}
CAPABILITY_IDS = frozenset(FIELD_GROUPS)
PARAMETER_KEYS = {capability: {"changes"} for capability in CAPABILITY_IDS}
BOOL_FIELDS = {"qr_code", "link_qr_code", "display_invoice_amount_total_words", "display_invoice_tax_company_currency", "account_use_credit_limit", "autopost_bills"}
CHOICES = {
    "fiscalyear_last_month": {str(month) for month in range(1, 13)},
    "tax_calculation_rounding_method": {"round_globally", "round_per_line"},
    "account_price_include": {"tax_included", "tax_excluded"},
    "quick_edit_mode": {None, "out_invoices", "in_invoices", "out_and_in_invoices"},
}
RELATION_MODELS = {
    "account_sale_tax_id": "account.tax",
    "account_purchase_tax_id": "account.tax",
    "currency_exchange_journal_id": "account.journal",
    "account_journal_early_pay_discount_gain_account_id": "account.account",
    "account_journal_early_pay_discount_loss_account_id": "account.account",
    "income_currency_exchange_account_id": "account.account",
    "expense_currency_exchange_account_id": "account.account",
}
SETTING_FIELDS = tuple(sorted(set().union(*FIELD_GROUPS.values())))
GET_FIELDS = ("id", "company_id", *SETTING_FIELDS)


def idempotency_key(capability_id: str, parameters: dict[str, Any], company_id: int) -> str:
    return _idempotency_key(capability_id, parameters, company_id)


def valid_value(field: str, value: Any) -> bool:
    if field in BOOL_FIELDS:
        return isinstance(value, bool)
    if field in RELATION_MODELS:
        return optional_id(value)
    if field == "fiscalyear_last_day":
        return valid_id(value) and value <= 31
    return field in CHOICES and (value is None or isinstance(value, str)) and value in CHOICES[field]


def normalize_parameters(capability_id: str, parameters: Any) -> dict[str, Any]:
    if capability_id == GET_ID and isinstance(parameters, dict) and not parameters:
        return {}
    if capability_id not in CAPABILITY_IDS or not isinstance(parameters, dict) or set(parameters) != {"changes"}:
        raise ValueError("Company settings require closed current-company parameters.")
    changes = parameters["changes"]
    if (not isinstance(changes, dict) or not changes or not set(changes) <= FIELD_GROUPS[capability_id]
        or not all(valid_value(field, value) for field, value in changes.items())):
        raise ValueError("Only typed settings belonging to this operation may change.")
    return {"changes": dict(changes)}


def valid_read_item(item: Any, company_id: int) -> bool:
    return (isinstance(item, dict) and set(item) == set(GET_FIELDS)
            and valid_id(item["id"]) and valid_id(item["company_id"]) and item["id"] == item["company_id"] == company_id
            and all(valid_value(field, item[field]) for field in SETTING_FIELDS))
