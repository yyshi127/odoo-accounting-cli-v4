"""Closed currency-aware native cash-rounding calculation contract."""

from __future__ import annotations

from typing import Any

from odoo_accounting_cli_v4.journal_item_processing_contracts import amount_text
from odoo_accounting_cli_v4.move_processing_contracts import valid_id

COMPUTE_ID = "cash_rounding.compute"
READ_IDS = frozenset({COMPUTE_ID})
PARAMETER_FIELDS = {"cash_rounding_id", "currency_id", "amount"}
ITEM_FIELDS = {"id", "company_id", "currency_id", "amount", "base_amount", "rounded_amount", "difference"}


def normalize_parameters(capability_id: str, parameters: Any) -> dict[str, Any]:
    if (capability_id != COMPUTE_ID or not isinstance(parameters, dict)
        or set(parameters) != PARAMETER_FIELDS
        or not valid_id(parameters["cash_rounding_id"])
        or not valid_id(parameters["currency_id"])):
        raise ValueError("Cash rounding requires fixed positive rule and currency IDs.")
    return {**parameters, "amount": amount_text(parameters["amount"], signed=True)}


def valid_read_item(item: Any, company_id: int) -> bool:
    if (not isinstance(item, dict) or set(item) != ITEM_FIELDS
        or not all(valid_id(item[field]) for field in ("id", "company_id", "currency_id"))
        or item["company_id"] != company_id):
        return False
    try:
        return all(amount_text(item[field], signed=True) == item[field]
                   for field in ("amount", "base_amount", "rounded_amount", "difference"))
    except ValueError:
        return False
