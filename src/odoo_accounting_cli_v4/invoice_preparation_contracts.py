"""Fixed invoice preparation and native product-accounting lookup contracts."""

from __future__ import annotations

from typing import Any

from odoo_accounting_cli_v4.journal_item_processing_contracts import amount_text
from odoo_accounting_cli_v4.move_processing_contracts import (
    MOVE_TYPES,
    optional_id,
    valid_date,
    valid_id,
)
from odoo_accounting_cli_v4.move_processing_contracts import (
    idempotency_key as _idempotency_key,
)

DATES_ID = "invoice.service_dates.get"
ALERTS_ID = "invoice.alerts.inspect"
ORIGINS_ID = "accounting_move.origin_links.inspect"
CATEGORY_ID = "product.category.accounting_profile.get"
TAX_PROFILE_ID = "product.tax_profile.get"
ACCOUNTS_ID = "product.accounts.resolve"
ID_FIELDS = {
    DATES_ID: "move_id", ALERTS_ID: "move_id", ORIGINS_ID: "move_id",
    CATEGORY_ID: "category_id", TAX_PROFILE_ID: "product_id", ACCOUNTS_ID: "product_id",
}
READ_IDS = frozenset(ID_FIELDS)
GET_IDS = READ_IDS
CAPABILITY_IDS = frozenset({"invoice.service_dates.update", "invoice.tax_totals.adjust"})
DOCUMENT_TYPES = frozenset({"out_invoice", "in_invoice", "out_refund", "in_refund"})
BASE_FIELDS = ("id", "company_id", "move_type", "state")
DATE_FIELDS = ("date", "invoice_date", "delivery_date", "taxable_supply_date")
ORIGIN_SINGLE_FIELDS = ("reversed_entry", "tax_cash_basis_origin_move")
ORIGIN_LIST_FIELDS = (
    "reversal_moves", "tax_cash_basis_created_moves", "adjusting_entry_origin_moves", "adjusting_entries_moves",
)
GET_FIELDS = {
    DATES_ID: (*BASE_FIELDS, *DATE_FIELDS, "show_delivery_date", "show_taxable_supply_date"),
    ALERTS_ID: (*BASE_FIELDS, "alerts"),
    ORIGINS_ID: (*BASE_FIELDS, *ORIGIN_SINGLE_FIELDS, *ORIGIN_LIST_FIELDS),
    CATEGORY_ID: ("id", "company_id", "income_account_id", "expense_account_id", "company_income_account_id", "company_expense_account_id"),
    TAX_PROFILE_ID: ("id", "company_id", "template_id", "sale_tax_ids", "purchase_tax_ids", "account_tag_ids"),
    ACCOUNTS_ID: ("id", "company_id", "template_id", "fiscal_position_id", "income_account_id", "expense_account_id", "stock_valuation_account_id", "stock_variation_account_id", "stock_journal_id"),
}


def idempotency_key(capability_id: str, parameters: dict[str, Any], company_id: int) -> str:
    return _idempotency_key(capability_id, parameters, company_id)


def normalize_parameters(capability_id: str, parameters: Any) -> dict[str, Any]:
    if not isinstance(parameters, dict) or capability_id not in READ_IDS | CAPABILITY_IDS:
        raise ValueError("Parameters must match a supported closed operation.")
    if capability_id in READ_IDS:
        keys = {ID_FIELDS[capability_id]}
        if capability_id == ACCOUNTS_ID:
            keys.add("fiscal_position_id")
        if set(parameters) != keys or not valid_id(parameters[ID_FIELDS[capability_id]]):
            raise ValueError("A positive target ID and the exact operation fields are required.")
        if capability_id == ACCOUNTS_ID and not optional_id(parameters["fiscal_position_id"]):
            raise ValueError("Fiscal position must be a positive ID or null for no mapping.")
        return dict(parameters)
    if capability_id not in CAPABILITY_IDS or not valid_id(parameters.get("move_id")):
        raise ValueError("A supported operation and positive move_id are required.")
    if capability_id == "invoice.service_dates.update":
        if set(parameters) != {"move_id", "changes"}:
            raise ValueError("Service-date updates require move_id and changes only.")
        changes = parameters["changes"]
        if (not isinstance(changes, dict) or not changes
                or not set(changes) <= {"delivery_date", "taxable_supply_date"}
                or not all(value is None or valid_date(value) for value in changes.values())):
            raise ValueError("Change one or both service dates using ISO dates or null.")
        return {"move_id": parameters["move_id"], "changes": dict(sorted(changes.items()))}
    if set(parameters) != {"move_id", "groups"}:
        raise ValueError("Tax adjustment requires move_id and existing tax groups only.")
    groups = parameters["groups"]
    if not isinstance(groups, list) or not 1 <= len(groups) <= 64:
        raise ValueError("Adjust 1-64 existing tax groups.")
    result = []
    for group in groups:
        if not isinstance(group, dict) or set(group) != {"tax_group_id", "tax_amount"} or not valid_id(group["tax_group_id"]):
            raise ValueError("Each tax group requires its positive ID and tax_amount only.")
        result.append({"tax_group_id": group["tax_group_id"], "tax_amount": amount_text(group["tax_amount"], signed=True)})
    ids = [group["tax_group_id"] for group in result]
    if ids != sorted(set(ids)):
        raise ValueError("Tax-group IDs must be sorted and unique.")
    return {"move_id": parameters["move_id"], "groups": result}


def _ids(value: Any) -> bool:
    return isinstance(value, list) and all(valid_id(item) for item in value) and value == sorted(set(value))


def _move_reference(value: Any) -> bool:
    return (isinstance(value, dict) and set(value) == {"id", "name", "move_type", "state", "date"}
            and valid_id(value["id"]) and (value["name"] is None or isinstance(value["name"], str) and bool(value["name"].strip()))
            and value["move_type"] in MOVE_TYPES and value["state"] in {"draft", "posted", "cancel"}
            and valid_date(value["date"]))


def valid_read_item(capability_id: str, item: Any, company_id: int) -> bool:
    if (capability_id not in READ_IDS or not isinstance(item, dict) or set(item) != set(GET_FIELDS[capability_id])
            or not valid_id(item["id"]) or item["company_id"] != company_id or not valid_id(item["company_id"])):
        return False
    if capability_id in {DATES_ID, ALERTS_ID, ORIGINS_ID} and (
            item["state"] not in {"draft", "posted", "cancel"}
            or item["move_type"] not in (MOVE_TYPES if capability_id == ORIGINS_ID else DOCUMENT_TYPES)):
        return False
    if capability_id == DATES_ID:
        return (valid_date(item["date"]) and all(item[field] is None or valid_date(item[field]) for field in DATE_FIELDS[1:])
                and all(isinstance(item[field], bool) for field in ("show_delivery_date", "show_taxable_supply_date")))
    if capability_id == ALERTS_ID:
        alerts = item["alerts"]
        if not isinstance(alerts, list):
            return False
        for alert in alerts:
            if (not isinstance(alert, dict) or set(alert) != {"key", "level", "message", "action_label"}
                    or not all(isinstance(alert[field], str) and bool(alert[field].strip()) for field in ("key", "level", "message"))
                    or not (alert["action_label"] is None or isinstance(alert["action_label"], str) and bool(alert["action_label"].strip()))):
                return False
        return len({alert["key"] for alert in alerts}) == len(alerts)
    if capability_id == ORIGINS_ID:
        if not all(item[field] is None or _move_reference(item[field]) for field in ORIGIN_SINGLE_FIELDS):
            return False
        return all(isinstance(item[field], list) and all(_move_reference(value) for value in item[field])
                   and [value["id"] for value in item[field]] == sorted({value["id"] for value in item[field]}) for field in ORIGIN_LIST_FIELDS)
    if capability_id == CATEGORY_ID:
        return all(optional_id(item[field]) for field in GET_FIELDS[capability_id][2:])
    if not valid_id(item["template_id"]):
        return False
    if capability_id == TAX_PROFILE_ID:
        return all(_ids(item[field]) for field in ("sale_tax_ids", "purchase_tax_ids", "account_tag_ids"))
    return all(optional_id(item[field]) for field in GET_FIELDS[capability_id][3:])
