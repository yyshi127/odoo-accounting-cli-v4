"""Closed native journal maintenance, reusing existing basic configuration."""

from __future__ import annotations

import re
from typing import Any

from odoo_accounting_cli_v4.move_processing_contracts import (
    idempotency_key as _idempotency_key,
)
from odoo_accounting_cli_v4.move_processing_contracts import (
    optional_id,
    valid_id,
)
from odoo_accounting_cli_v4.reconciliation_processing_contracts import valid_ids

GET_ID = "journal.processing_settings.get"
READ_IDS = frozenset({GET_ID})
PARAMETER_KEYS = {
    "journal.duplicate": {"journal_id", "code", "name"},
    "journal.delete": {"journal_id"},
    "journal.sequence_policy.update": {"journal_id", "changes"},
    "journal.invoice_reference.update": {"journal_id", "changes"},
    "journal.non_deductible_account.assign": {"journal_id", "account_id"},
    "journal.invoice_template.assign": {"journal_id", "report_id"},
    "journal.group.delete": {"journal_group_id"},
}
CAPABILITY_IDS = frozenset(PARAMETER_KEYS)
SEQUENCE_FIELDS = {"refund_sequence", "payment_sequence", "is_self_billing"}
REFERENCE_CHOICES = {"invoice_reference_type": {"partner", "invoice"}, "invoice_reference_model": {"odoo", "euro", "number"}}
RELATION_FIELDS = ("currency_id", "suspense_account_id", "profit_account_id", "loss_account_id", "non_deductible_account_id", "invoice_template_pdf_report_id")
COPY_FIELDS = ("active", "type", "sequence", *RELATION_FIELDS, "invoice_reference_type", "invoice_reference_model",
               "refund_sequence", "payment_sequence", "is_self_billing", "restrict_mode_hash_table")
GET_FIELDS = ("id", "company_id", "active", "type", "refund_sequence", "payment_sequence", "is_self_billing",
              "non_deductible_account_id", "invoice_template_pdf_report_id", "available_invoice_template_pdf_report_ids")
JOURNAL_TYPES = {"sale", "purchase", "bank", "cash", "credit", "general"}


def idempotency_key(capability_id: str, parameters: dict[str, Any], company_id: int) -> str:
    return _idempotency_key(capability_id, parameters, company_id)


def normalize_parameters(capability_id: str, parameters: Any) -> dict[str, Any]:
    field = "journal_group_id" if capability_id == "journal.group.delete" else "journal_id"
    if (capability_id not in CAPABILITY_IDS or not isinstance(parameters, dict)
        or set(parameters) != PARAMETER_KEYS[capability_id] or not valid_id(parameters.get(field))):
        raise ValueError("Journal maintenance requires closed company-scoped parameters.")
    result = dict(parameters)
    if "code" in parameters and not (isinstance(parameters["code"], str) and re.fullmatch(r"[A-Za-z0-9]{1,5}", parameters["code"])):
        raise ValueError("code requires 1-5 letters or digits.")
    if "name" in parameters and not (isinstance(parameters["name"], str) and 1 <= len(parameters["name"]) <= 256 and parameters["name"] == parameters["name"].strip()):
        raise ValueError("name requires bounded text without outer whitespace.")
    for field in ("account_id", "report_id"):
        if field in parameters and not optional_id(parameters[field]):
            raise ValueError(f"{field} requires a positive ID or null to clear.")
    if "changes" in parameters:
        changes = parameters["changes"]
        sequence = capability_id == "journal.sequence_policy.update"
        allowed = SEQUENCE_FIELDS if sequence else set(REFERENCE_CHOICES)
        if (not isinstance(changes, dict) or not changes or not set(changes) <= allowed
            or any(not isinstance(value, bool) if sequence else not isinstance(value, str) or value not in REFERENCE_CHOICES[field]
                   for field, value in changes.items())):
            raise ValueError("Only fixed native sequence booleans or reference choices may change.")
        result["changes"] = dict(changes)
    return result


def valid_read_item(item: Any, company_id: int) -> bool:
    return (isinstance(item, dict) and set(item) == set(GET_FIELDS) and valid_id(item["id"])
            and valid_id(item["company_id"]) and item["company_id"] == company_id
            and isinstance(item["type"], str) and item["type"] in JOURNAL_TYPES
            and all(isinstance(item[field], bool) for field in ("active", "refund_sequence", "payment_sequence", "is_self_billing"))
            and all(optional_id(item[field]) for field in ("non_deductible_account_id", "invoice_template_pdf_report_id"))
            and valid_ids(item["available_invoice_template_pdf_report_ids"], 100000))
