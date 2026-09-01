"""Narrow bridge port for accounting document delivery and follow-up updates."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Protocol

ACTION = "accounting.delivery.execute"
CAPABILITY_IDS = frozenset(
    {
        "invoice.send.inspect",
        "invoice.send",
        "payment.receipt.send.inspect",
        "payment.receipt.send",
        "report.customer_statement.send",
        "report.followup.send",
        "invoice.followup.update",
    }
)
INSPECT_CAPABILITY_IDS = frozenset(
    {"invoice.send.inspect", "payment.receipt.send.inspect"}
)
SEND_CAPABILITY_IDS = frozenset(
    {
        "invoice.send",
        "payment.receipt.send",
        "report.customer_statement.send",
        "report.followup.send",
    }
)
FOLLOWUP_CAPABILITY_IDS = frozenset({"invoice.followup.update"})

_PAGE_FIELDS = {
    "user_id",
    "company_visible",
    "module_installed",
    "access_allowed",
    "idempotent_replay",
    "result",
}
_INSPECT_RECORD_FIELDS = {
    "record_id",
    "partner_id",
    "recipient_emails",
    "template_id",
    "report_id",
    "sending_methods",
    "warnings",
    "sendable",
}


class BridgeClient(Protocol):
    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]: ...


def _positive_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _optional_positive_integer(value: Any) -> bool:
    return value is None or _positive_integer(value)


def _strict_ids(value: Any) -> bool:
    return bool(
        isinstance(value, list)
        and value
        and len(value) <= 100
        and all(_positive_integer(item) for item in value)
        and value == sorted(set(value))
    )


def _strict_texts(value: Any, *, allow_empty: bool = True) -> bool:
    return bool(
        isinstance(value, list)
        and (allow_empty or value)
        and all(
            isinstance(item, str) and item == item.strip() and bool(item)
            for item in value
        )
        and value == sorted(set(value))
    )


def _valid_inspect_record(value: Any) -> bool:
    return bool(
        isinstance(value, dict)
        and set(value) == _INSPECT_RECORD_FIELDS
        and _positive_integer(value["record_id"])
        and _positive_integer(value["partner_id"])
        and _strict_texts(value["recipient_emails"])
        and _optional_positive_integer(value["template_id"])
        and _optional_positive_integer(value["report_id"])
        and _strict_texts(value["sending_methods"])
        and _strict_texts(value["warnings"])
        and isinstance(value["sendable"], bool)
    )


def _valid_result(capability_id: str, parameters: dict[str, Any], result: Any) -> bool:
    if capability_id in INSPECT_CAPABILITY_IDS:
        if not isinstance(result, dict) or set(result) != {"records"}:
            return False
        records = result["records"]
        return bool(
            isinstance(records, list)
            and all(_valid_inspect_record(record) for record in records)
            and [record["record_id"] for record in records]
            == parameters.get("record_ids")
        )
    if capability_id in SEND_CAPABILITY_IDS:
        return bool(
            isinstance(result, dict)
            and set(result) == {"record_ids", "processed_count"}
            and _strict_ids(result["record_ids"])
            and result["record_ids"] == parameters.get("record_ids")
            and isinstance(result["processed_count"], int)
            and not isinstance(result["processed_count"], bool)
            and result["processed_count"] == len(result["record_ids"])
        )
    return bool(
        capability_id in FOLLOWUP_CAPABILITY_IDS
        and isinstance(result, dict)
        and set(result) == {"record_id", "no_followup"}
        and result["record_id"] == parameters.get("record_id")
        and result["no_followup"] == parameters.get("no_followup")
        and isinstance(result["no_followup"], bool)
    )


class OdooAccountingDeliveryPort:
    """Invoke only the fixed accounting-delivery runtime action."""

    def __init__(self, client: BridgeClient) -> None:
        self._client = client
        self._user_id: int | None = None

    @property
    def user_id(self) -> int:
        if self._user_id is None:
            raise ValueError(
                "No verified Odoo accounting-delivery result has been read."
            )
        return self._user_id

    def execute(
        self,
        *,
        capability_id: str,
        company_id: int,
        parameters: dict[str, Any],
        idempotency_key: str | None,
    ) -> dict[str, Any]:
        if capability_id not in CAPABILITY_IDS:
            raise ValueError("Unsupported accounting-delivery capability.")
        self._user_id = None
        closed_parameters = deepcopy(parameters)
        page = self._client.invoke(
            ACTION,
            {
                "capability_id": capability_id,
                "company_id": company_id,
                "parameters": closed_parameters,
                "idempotency_key": idempotency_key,
            },
        )
        if (
            not isinstance(page, dict)
            or set(page) != _PAGE_FIELDS
            or not _positive_integer(page["user_id"])
            or not isinstance(page["company_visible"], bool)
            or not isinstance(page["module_installed"], bool)
            or not isinstance(page["access_allowed"], bool)
            or not isinstance(page["idempotent_replay"], bool)
            or not (
                page["result"] is None
                or _valid_result(capability_id, closed_parameters, page["result"])
            )
        ):
            raise ValueError(
                "The Odoo bridge returned an invalid accounting-delivery result."
            )
        self._user_id = page["user_id"]
        return page
