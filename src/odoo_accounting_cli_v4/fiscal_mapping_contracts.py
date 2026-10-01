"""Closed contracts for native fiscal-position and tax mapping maintenance."""

from __future__ import annotations

import hashlib
import json
from typing import Any

PARAMETER_KEYS = {
    "fiscal_position.taxes.replace": {"fiscal_position_id", "tax_ids"},
    "tax.original_taxes.replace": {"tax_id", "original_tax_ids"},
    "fiscal_position.account_mapping.create": {
        "fiscal_position_id",
        "source_account_id",
        "destination_account_id",
    },
    "fiscal_position.account_mapping.update": {"account_mapping_id", "changes"},
    "fiscal_position.account_mapping.delete": {"account_mapping_id"},
    "fiscal_position.duplicate": {"fiscal_position_id", "name"},
    "fiscal_position.delete": {"fiscal_position_id"},
    "tax.duplicate": {"tax_id", "name"},
}
CAPABILITY_IDS = frozenset(PARAMETER_KEYS)


def normalize_parameters(capability_id: str, parameters: Any) -> dict[str, Any]:
    if (
        capability_id not in CAPABILITY_IDS
        or not isinstance(parameters, dict)
        or set(parameters) != PARAMETER_KEYS[capability_id]
    ):
        raise ValueError("Fiscal mapping parameters do not match the fixed contract.")
    result = dict(parameters)
    for field, value in parameters.items():
        if field.endswith("_id"):
            valid = isinstance(value, int) and not isinstance(value, bool) and value > 0
        elif field.endswith("_ids"):
            valid = (
                isinstance(value, list)
                and len(value) <= 1000
                and all(
                    isinstance(item, int) and not isinstance(item, bool) and item > 0
                    for item in value
                )
                and len(value) == len(set(value))
            )
            if valid:
                result[field] = sorted(value)
        elif field == "name":
            valid = (
                isinstance(value, str)
                and 1 <= len(value) <= 256
                and value == value.strip()
            )
        else:
            valid = (
                isinstance(value, dict)
                and bool(value)
                and set(value) <= {"source_account_id", "destination_account_id"}
                and all(
                    isinstance(item, int) and not isinstance(item, bool) and item > 0
                    for item in value.values()
                )
            )
            if valid:
                result[field] = dict(value)
        if not valid:
            raise ValueError(f"Invalid fiscal mapping field: {field}.")
    mapping = result.get("changes", result)
    if (
        "source_account_id" in mapping
        and mapping.get("destination_account_id") == mapping["source_account_id"]
    ):
        raise ValueError("Source and destination accounts must differ.")
    if (
        capability_id == "tax.original_taxes.replace"
        and result["tax_id"] in result["original_tax_ids"]
    ):
        raise ValueError("A tax cannot replace itself.")
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
