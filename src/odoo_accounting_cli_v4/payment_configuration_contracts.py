"""Fixed contracts for journal liquidity and configured payment-method lines."""

from __future__ import annotations

import hashlib
import json
from typing import Any

PARAMETER_KEYS = {
    "payment.method_line.create": {
        "journal_id",
        "payment_method_id",
        "name",
        "sequence",
        "payment_account_id",
    },
    "payment.method_line.update": {"payment_method_line_id", "changes"},
    "payment.method_line.duplicate": {"payment_method_line_id", "name"},
    "payment.method_line.remove": {"payment_method_line_id"},
    "journal.liquidity_configuration.update": {"journal_id", "changes"},
    "journal.bank_account.assign": {"journal_id", "partner_bank_id"},
}
CAPABILITY_IDS = frozenset(PARAMETER_KEYS)
LINE_FIELDS = {"name", "sequence", "payment_account_id"}
LIQUIDITY_FIELDS = {"suspense_account_id", "profit_account_id", "loss_account_id"}


def _valid_field(field: str, value: Any) -> bool:
    if field == "name":
        return (
            isinstance(value, str) and 1 <= len(value) <= 256 and value == value.strip()
        )
    if field == "sequence":
        return (
            isinstance(value, int)
            and not isinstance(value, bool)
            and 0 <= value <= 2147483647
        )
    if value is None:
        return field in {"payment_account_id", "partner_bank_id"}
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def normalize_parameters(capability_id: str, parameters: Any) -> dict[str, Any]:
    if (
        capability_id not in CAPABILITY_IDS
        or not isinstance(parameters, dict)
        or set(parameters) != PARAMETER_KEYS[capability_id]
    ):
        raise ValueError(
            "Payment configuration parameters do not match the fixed contract."
        )
    result = dict(parameters)
    for field, value in parameters.items():
        if field == "changes":
            fields = (
                LIQUIDITY_FIELDS
                if capability_id.startswith("journal.")
                else LINE_FIELDS
            )
            valid = (
                isinstance(value, dict)
                and bool(value)
                and set(value) <= fields
                and all(_valid_field(key, item) for key, item in value.items())
            )
            if valid:
                result[field] = dict(value)
        else:
            valid = _valid_field(field, value)
        if not valid:
            raise ValueError(f"Invalid payment configuration field: {field}.")
    return result


def idempotency_key(
    capability_id: str, parameters: dict[str, Any], company_id: int
) -> str:
    digest = hashlib.sha256(
        json.dumps(
            parameters, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()[:32]
    return f"{capability_id}:{company_id}:{digest}"
