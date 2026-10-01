"""Closed native account maintenance; existing basic edits are not duplicated."""

from __future__ import annotations

import re
from typing import Any

from odoo_accounting_cli_v4.move_processing_contracts import (
    idempotency_key as _idempotency_key,
)
from odoo_accounting_cli_v4.move_processing_contracts import optional_id, valid_id
from odoo_accounting_cli_v4.payment_term_processing_contracts import decimal_text
from odoo_accounting_cli_v4.reconciliation_processing_contracts import valid_ids

GET_ID = "account.account.processing_settings.get"
READ_IDS = frozenset({GET_ID})
PARAMETER_KEYS = {
    "account.account.duplicate": {"account_id", "code", "name"},
    "account.account.delete": {"account_id"},
    "account.account.default_taxes.assign": {"account_id", "tax_ids"},
    "account.account.tags.assign": {"account_id", "tag_ids"},
    "account.account.notes.update": {"account_id", "changes"},
    "account.account.non_trade.set": {"account_id", "non_trade"},
    "account.group.delete": {"account_group_id"},
}
CAPABILITY_IDS = frozenset(PARAMETER_KEYS)
COPY_FIELDS = ("active", "account_type", "reconcile", "currency_id", "tax_ids", "tag_ids", "description", "note", "non_trade")
GET_FIELDS = ("id", "company_ids", "active", "description", "note", "non_trade", "used", "currency_id",
              "company_currency_id", "tax_ids", "tag_ids", "group_id", "include_initial_balance", "internal_group",
              "related_taxes_amount", "current_balance")


def idempotency_key(capability_id: str, parameters: dict[str, Any], company_id: int) -> str:
    return _idempotency_key(capability_id, parameters, company_id)


def normalize_parameters(capability_id: str, parameters: Any) -> dict[str, Any]:
    field = "account_group_id" if capability_id == "account.group.delete" else "account_id"
    if (capability_id not in CAPABILITY_IDS or not isinstance(parameters, dict)
        or set(parameters) != PARAMETER_KEYS[capability_id] or not valid_id(parameters.get(field))):
        raise ValueError("Account maintenance requires closed company-scoped parameters.")
    result = dict(parameters)
    if "code" in parameters and not (isinstance(parameters["code"], str) and 1 <= len(parameters["code"]) <= 64
                                      and re.fullmatch(r"[A-Za-z0-9.]+", parameters["code"])):
        raise ValueError("code requires 1-64 letters, digits or dots.")
    if "name" in parameters and not (isinstance(parameters["name"], str) and parameters["name"].strip()
                                      and parameters["name"] == parameters["name"].strip() and len(parameters["name"]) <= 256):
        raise ValueError("name requires 1-256 characters without outer whitespace.")
    for field in ("tax_ids", "tag_ids"):
        if field in parameters:
            if not valid_ids(parameters[field], 100):
                raise ValueError(f"{field} requires up to 100 unique positive native IDs.")
            result[field] = sorted(parameters[field])
    if "non_trade" in parameters and not isinstance(parameters["non_trade"], bool):
        raise ValueError("non_trade must be a boolean.")
    if "changes" in parameters:
        changes = parameters["changes"]
        if (not isinstance(changes, dict) or not changes or not set(changes) <= {"description", "note"}
            or any(value is not None and (not isinstance(value, str) or len(value) > 4096) for value in changes.values())):
            raise ValueError("Only bounded nullable description/note changes are accepted.")
        result["changes"] = {field: value or None for field, value in changes.items()}
    return result


def valid_read_item(item: Any, company_id: int) -> bool:
    return (isinstance(item, dict) and set(item) == set(GET_FIELDS) | {"company_id"}
            and valid_id(item["id"]) and valid_id(item["company_id"]) and item["company_id"] == company_id
            and valid_ids(item["company_ids"], 100000) and company_id in item["company_ids"]
            and all(isinstance(item[field], bool) for field in ("active", "non_trade", "used", "include_initial_balance"))
            and all(optional_id(item[field]) for field in ("currency_id", "group_id"))
            and valid_id(item["company_currency_id"])
            and all(valid_ids(item[field], 100000) for field in ("tax_ids", "tag_ids"))
            and all(item[field] is None or isinstance(item[field], str) for field in ("description", "note"))
            and isinstance(item["internal_group"], str)
            and item["internal_group"] in {"equity", "asset", "liability", "income", "expense", "off"}
            and isinstance(item["related_taxes_amount"], int) and not isinstance(item["related_taxes_amount"], bool)
            and item["related_taxes_amount"] >= 0 and decimal_text(item["current_balance"]))
