"""Closed contracts for native reconciliation-rule editing and usage reads."""

from __future__ import annotations

import re
from decimal import Decimal
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

GET_ID = "reconciliation.model.processing_settings.get"
LIST_ID = "reconciliation.model.usage_lines.list"
READ_IDS = frozenset({GET_ID, LIST_ID})
LINE_KEYS = frozenset({"sequence", "account_id", "partner_id", "label", "amount_type", "amount_string", "tax_ids"})
LINE_TYPES = frozenset({"fixed", "percentage", "percentage_st_line", "regex"})
PARAMETER_KEYS = {
    "reconciliation.model.duplicate": {"reconciliation_model_id", "name"},
    "reconciliation.model.delete": {"reconciliation_model_id"},
    "reconciliation.model.line.create": {"reconciliation_model_id", "line"},
    "reconciliation.model.line.update": {"reconciliation_model_id", "line_id", "changes"},
    "reconciliation.model.line.delete": {"reconciliation_model_id", "line_id"},
    "reconciliation.model.lines.resequence": {"reconciliation_model_id", "line_ids"},
    "reconciliation.model.activity_type.assign": {"reconciliation_model_id", "activity_type_id"},
}
CAPABILITY_IDS = frozenset(PARAMETER_KEYS)
GET_FIELDS = ("id", "name", "company_id", "active", "trigger", "can_be_proposed",
              "mapped_partner_id", "next_activity_type_id", "line_ids")
USAGE_FIELDS = ("id", "company_id", "reconcile_model_id", "move_id", "account_id", "partner_id",
                "currency_id", "name", "date", "debit", "credit", "balance", "amount_currency")
DECIMAL = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?")


def idempotency_key(capability_id: str, parameters: dict[str, Any], company_id: int) -> str:
    return _idempotency_key(capability_id, parameters, company_id)


def valid_ids(value: Any, maximum: int = 100) -> bool:
    return (isinstance(value, list) and len(value) <= maximum
            and all(valid_id(item) for item in value) and len(value) == len(set(value)))


def line_values(values: Any, *, partial: bool = False) -> dict[str, Any]:
    if (not isinstance(values, dict) or not values or not set(values) <= LINE_KEYS | {"analytic_distribution"}
        or not partial and not LINE_KEYS <= set(values)):
        raise ValueError("Rule lines require a nonempty fixed-field payload.")
    for field in ("account_id", "partner_id"):
        if field in values and not optional_id(values[field]):
            raise ValueError("Rule account and partner must be null or positive identifiers.")
    if "sequence" in values and not valid_sequence(values["sequence"]):
        raise ValueError("sequence must be a native signed 32-bit integer.")
    if "label" in values and not (values["label"] is None or isinstance(values["label"], str) and 1 <= len(values["label"]) <= 500):
        raise ValueError("label must be null or contain 1-500 characters.")
    if "amount_type" in values and (not isinstance(values["amount_type"], str) or values["amount_type"] not in LINE_TYPES):
        raise ValueError("Unknown native rule amount type.")
    if "amount_string" in values and not (isinstance(values["amount_string"], str) and 1 <= len(values["amount_string"]) <= 500):
        raise ValueError("amount_string must contain 1-500 characters.")
    if {"amount_type", "amount_string"} <= set(values):
        amount = values["amount_string"]
        if values["amount_type"] == "regex":
            try:
                re.compile(amount)
            except re.error as exc:
                raise ValueError("Invalid native rule amount regex.") from exc
        elif not (len(amount) <= 256 and DECIMAL.fullmatch(amount) and Decimal(amount) != 0):
            raise ValueError("Numeric rule amounts must be nonzero bounded decimal strings.")
    if "tax_ids" in values and not valid_ids(values["tax_ids"]):
        raise ValueError("tax_ids must be unique positive identifiers.")
    if "analytic_distribution" in values:
        entries = values["analytic_distribution"]
        if not isinstance(entries, list) or len(entries) > 16:
            raise ValueError("Invalid rule analytic distribution.")
        keys = []
        for entry in entries:
            if (not isinstance(entry, dict) or set(entry) != {"analytic_account_ids", "percentage"}
                or not valid_ids(entry["analytic_account_ids"], 16) or not entry["analytic_account_ids"]
                or not isinstance(entry["percentage"], str) or len(entry["percentage"]) > 256
                or not DECIMAL.fullmatch(entry["percentage"]) or not 0 < Decimal(entry["percentage"]) <= 100
                or Decimal(entry["percentage"]).as_tuple().exponent < -4):
                raise ValueError("Invalid rule analytic distribution entry.")
            keys.append(tuple(sorted(entry["analytic_account_ids"])))
        if len(keys) != len(set(keys)):
            raise ValueError("Duplicate rule analytic distribution keys.")
    result = dict(values)
    if "tax_ids" in result:
        result["tax_ids"] = sorted(result["tax_ids"])
    if "analytic_distribution" in result:
        result["analytic_distribution"] = sorted([
            {"analytic_account_ids": sorted(entry["analytic_account_ids"]),
             "percentage": format(Decimal(entry["percentage"]).normalize(), "f")}
            for entry in result["analytic_distribution"]
        ], key=lambda entry: entry["analytic_account_ids"])
    return result


def normalize_parameters(capability_id: str, parameters: Any) -> dict[str, Any]:
    if (capability_id not in CAPABILITY_IDS or not isinstance(parameters, dict)
        or set(parameters) != PARAMETER_KEYS[capability_id] or not valid_id(parameters.get("reconciliation_model_id"))):
        raise ValueError("Reconciliation processing parameters do not match the closed contract.")
    if "line_id" in parameters and not valid_id(parameters["line_id"]):
        raise ValueError("line_id must be positive.")
    if "name" in parameters and not (isinstance(parameters["name"], str) and parameters["name"].strip() and len(parameters["name"]) <= 256):
        raise ValueError("Duplicate name must contain 1-256 characters.")
    if "activity_type_id" in parameters and not optional_id(parameters["activity_type_id"]):
        raise ValueError("activity_type_id must be null or positive.")
    result = dict(parameters)
    if "line" in parameters:
        result["line"] = line_values(parameters["line"])
    if "changes" in parameters:
        result["changes"] = line_values(parameters["changes"], partial=True)
    if "line_ids" in parameters and not valid_ids(parameters["line_ids"], 500):
        raise ValueError("line_ids must be an ordered unique list of rule lines.")
    return result


def valid_read_item(capability_id: str, item: Any, company_id: int) -> bool:
    fields = GET_FIELDS if capability_id == GET_ID else USAGE_FIELDS
    if (not isinstance(item, dict) or set(item) != set(fields) or not valid_id(item["id"])
        or not valid_id(item["company_id"]) or item["company_id"] != company_id
        or not (item["name"] is None or isinstance(item["name"], str))):
        return False
    if capability_id == GET_ID:
        return (all(isinstance(item[field], bool) for field in ("active", "can_be_proposed"))
                and isinstance(item["trigger"], str) and item["trigger"] in {"manual", "auto_reconcile"}
                and all(optional_id(item[field]) for field in ("mapped_partner_id", "next_activity_type_id"))
                and valid_ids(item["line_ids"], 100000))
    return (all(valid_id(item[field]) for field in ("reconcile_model_id", "move_id", "account_id", "currency_id"))
            and optional_id(item["partner_id"]) and valid_date(item["date"])
            and all(isinstance(item[field], str) and DECIMAL.fullmatch(item[field])
                    for field in ("debit", "credit", "balance", "amount_currency")))
