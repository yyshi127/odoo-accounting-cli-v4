"""Fixed financial-report budget contracts shared by the CLI and ORM adapter."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from typing import Any

CAPABILITY_IDS = frozenset(
    {
        "report.budget_definition.create",
        "report.budget_definition.update",
        "report.budget_definition.duplicate",
        "report.budget_definition.delete",
        "report.budget_item.create",
        "report.budget_item.update",
        "report.budget_item.delete",
        "report.budget_account_period.set_total",
    }
)
PARAMETER_KEYS = {
    "report.budget_definition.create": {"name", "sequence"},
    "report.budget_definition.update": {"budget_definition_id", "changes"},
    "report.budget_definition.duplicate": {"budget_definition_id", "name"},
    "report.budget_definition.delete": {"budget_definition_id"},
    "report.budget_item.create": {
        "budget_definition_id",
        "account_id",
        "date",
        "amount",
    },
    "report.budget_item.update": {"budget_item_id", "changes"},
    "report.budget_item.delete": {"budget_item_id"},
    "report.budget_account_period.set_total": {
        "budget_definition_id",
        "account_id",
        "date_from",
        "date_to",
        "total",
        "rounding",
    },
}
AMOUNT_PATTERN = r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]*[1-9])?$(?![\s\S])"


def _valid_value(field: str, value: Any) -> bool:
    if field.endswith("_id"):
        return isinstance(value, int) and not isinstance(value, bool) and value > 0
    if field == "name":
        return (
            isinstance(value, str) and 1 <= len(value) <= 256 and value == value.strip()
        )
    if field in {"sequence", "rounding"}:
        bounds = (-2147483648, 2147483647) if field == "sequence" else (0, 6)
        return (
            isinstance(value, int)
            and not isinstance(value, bool)
            and bounds[0] <= value <= bounds[1]
        )
    if field in {"amount", "total"}:
        return (
            isinstance(value, str)
            and len(value) <= 18
            and value != "-0"
            and re.fullmatch(AMOUNT_PATTERN, value) is not None
        )
    if field in {"date", "date_from", "date_to"}:
        try:
            return (
                isinstance(value, str)
                and date.fromisoformat(value).isoformat() == value
            )
        except ValueError:
            return False
    return False


def period_months(date_from: str, date_to: str) -> list[date]:
    start, end = date.fromisoformat(date_from), date.fromisoformat(date_to)
    first = start.year * 12 + start.month - 1 + int(start.day != 1)
    last = end.year * 12 + end.month - 1
    if start > end or not 1 <= last - first + 1 <= 120:
        raise ValueError(
            "The native budget period must contain 1-120 included month starts."
        )
    return [date(month // 12, month % 12 + 1, 1) for month in range(first, last + 1)]


def normalize_parameters(capability_id: str, parameters: Any) -> dict[str, Any]:
    if capability_id not in CAPABILITY_IDS or not isinstance(parameters, dict):
        raise ValueError("Unsupported financial-report budget request.")
    normalized = dict(parameters)
    if capability_id == "report.budget_definition.create":
        normalized.setdefault("sequence", 0)
    if set(normalized) != PARAMETER_KEYS[capability_id]:
        raise ValueError(
            "Financial-report budget parameters do not match the fixed contract."
        )
    for field, value in normalized.items():
        if field == "changes":
            allowed = (
                {"name", "sequence"}
                if capability_id == "report.budget_definition.update"
                else {"account_id", "date", "amount"}
            )
            if not isinstance(value, dict) or not value or not set(value) <= allowed:
                raise ValueError(
                    "The budget update must contain a nonempty supported patch."
                )
            if not all(_valid_value(key, item) for key, item in value.items()):
                raise ValueError("The budget update contains an invalid value.")
            normalized[field] = dict(value)
        elif not _valid_value(field, value):
            raise ValueError(f"Invalid financial-report budget field: {field}.")
    if capability_id == "report.budget_account_period.set_total":
        period_months(normalized["date_from"], normalized["date_to"])
    return normalized


def idempotency_key(
    capability_id: str, parameters: dict[str, Any], company_id: int
) -> str:
    digest = hashlib.sha256(
        json.dumps(
            parameters, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()[:32]
    return f"{capability_id}:{company_id}:{digest}"
