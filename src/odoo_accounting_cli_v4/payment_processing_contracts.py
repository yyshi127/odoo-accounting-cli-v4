"""Closed native payment processing, bank eligibility and duplicate-warning contracts."""

from __future__ import annotations

import re
from typing import Any

from odoo_accounting_cli_v4.move_processing_contracts import (
    idempotency_key as _idempotency_key,
)
from odoo_accounting_cli_v4.move_processing_contracts import (
    optional_id,
    valid_date,
    valid_id,
)

GET_ID = "payment.processing_settings.get"
BANKS_ID = "payment.bank_account_candidates.list"
DUPLICATES_ID = "payment.duplicate_candidates.list"
LIST_IDS = frozenset({BANKS_ID, DUPLICATES_ID})
READ_IDS = LIST_IDS | {GET_ID}
STATES = frozenset({"draft", "in_process", "paid", "canceled", "rejected"})
PARAMETER_KEYS = {
    "payment.bank_account.assign": {"payment_id", "partner_bank_id"},
    "payment.destination_account.assign": {"payment_id", "account_id"},
    "payment.sent_status.set": {"payment_id", "sent"},
    "payment.validate": {"payment_id"},
    "payment.reject": {"payment_id"},
}
CAPABILITY_IDS = frozenset(PARAMETER_KEYS)
GET_FIELDS = ("id", "name", "company_id", "state", "payment_type", "partner_type",
              "partner_id", "partner_bank_id", "destination_account_id", "outstanding_account_id",
              "is_sent", "payment_method_code", "move_id", "is_reconciled", "is_matched",
              "show_partner_bank_account", "require_partner_bank_account")
BANK_FIELDS = ("id", "company_id", "partner_id", "acc_number", "bank_id", "currency_id",
               "active", "allow_out_payment")
DUPLICATE_FIELDS = ("id", "name", "company_id", "date", "state", "payment_type",
                    "partner_type", "partner_id", "currency_id", "amount")
_MONEY = re.compile(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?")


def idempotency_key(capability_id: str, parameters: dict[str, Any], company_id: int) -> str:
    return _idempotency_key(capability_id, parameters, company_id)


def normalize_parameters(capability_id: str, parameters: Any) -> dict[str, Any]:
    if (capability_id not in CAPABILITY_IDS or not isinstance(parameters, dict)
        or set(parameters) != PARAMETER_KEYS[capability_id] or not valid_id(parameters.get("payment_id"))):
        raise ValueError("Payment processing parameters do not match the closed contract.")
    if "partner_bank_id" in parameters and not optional_id(parameters["partner_bank_id"]):
        raise ValueError("partner_bank_id must be null or a positive identifier.")
    if "account_id" in parameters and not valid_id(parameters["account_id"]):
        raise ValueError("account_id must be a positive identifier.")
    if "sent" in parameters and not isinstance(parameters["sent"], bool):
        raise ValueError("sent must be a boolean desired state.")
    return dict(parameters)


def valid_read_item(capability_id: str, item: Any, company_id: int) -> bool:
    fields = GET_FIELDS if capability_id == GET_ID else BANK_FIELDS if capability_id == BANKS_ID else DUPLICATE_FIELDS
    expected = set(fields) | ({"payment_id"} if capability_id in LIST_IDS else set())
    if not isinstance(item, dict) or set(item) != expected or not valid_id(item["id"]):
        return False
    owner = item["company_id"]
    if not (owner is None and capability_id == BANKS_ID or valid_id(owner) and owner == company_id):
        return False
    if capability_id in LIST_IDS and not valid_id(item["payment_id"]):
        return False
    if capability_id == BANKS_ID:
        return (valid_id(item["partner_id"]) and all(optional_id(item[field]) for field in ("bank_id", "currency_id"))
                and (item["acc_number"] is None or isinstance(item["acc_number"], str))
                and all(isinstance(item[field], bool) for field in ("active", "allow_out_payment")))
    if (not isinstance(item["state"], str) or item["state"] not in STATES
        or not isinstance(item["payment_type"], str) or item["payment_type"] not in {"inbound", "outbound"}
        or not isinstance(item["partner_type"], str) or item["partner_type"] not in {"customer", "supplier"}
        or not optional_id(item["partner_id"]) or not (item["name"] is None or isinstance(item["name"], str))):
        return False
    if capability_id == DUPLICATES_ID:
        return (item["id"] != item["payment_id"] and valid_date(item["date"]) and valid_id(item["currency_id"])
                and isinstance(item["amount"], str) and _MONEY.fullmatch(item["amount"]) is not None)
    return (all(optional_id(item[field]) for field in ("partner_bank_id", "destination_account_id", "outstanding_account_id", "move_id"))
            and (item["payment_method_code"] is None or isinstance(item["payment_method_code"], str))
            and all(isinstance(item[field], bool) for field in ("is_sent", "is_reconciled", "is_matched", "show_partner_bank_account", "require_partner_bank_account")))
