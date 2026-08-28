"""One narrow bridge port for the fixed core-accounting write batch."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Protocol

_ACTION = "accounting.core_write.execute"
_PAGE_FIELDS = {
    "user_id",
    "company_visible",
    "module_installed",
    "access_allowed",
    "idempotent_replay",
    "result",
}
_RESULT_FIELDS = {
    "model",
    "id",
    "name",
    "state",
    "company_id",
    "move_type",
    "source_id",
    "line_ids",
    "partial_reconcile_ids",
    "full_reconcile_id",
    "reconciled",
}


class BridgeClient(Protocol):
    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]: ...


def _positive_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _optional_positive_integer(value: Any) -> bool:
    return value is None or _positive_integer(value)


def _optional_text(value: Any) -> bool:
    return value is None or (isinstance(value, str) and bool(value.strip()))


def _strict_ids(value: Any) -> bool:
    return (
        isinstance(value, list)
        and all(_positive_integer(item) for item in value)
        and value == sorted(set(value))
    )


def _valid_result(result: Any) -> bool:
    return (
        isinstance(result, dict)
        and set(result) == _RESULT_FIELDS
        and isinstance(result["model"], str)
        and bool(result["model"].strip())
        and _optional_positive_integer(result["id"])
        and _optional_text(result["name"])
        and isinstance(result["state"], str)
        and bool(result["state"].strip())
        and _positive_integer(result["company_id"])
        and _optional_text(result["move_type"])
        and _optional_positive_integer(result["source_id"])
        and _strict_ids(result["line_ids"])
        and _strict_ids(result["partial_reconcile_ids"])
        and _optional_positive_integer(result["full_reconcile_id"])
        and isinstance(result["reconciled"], bool)
    )


class OdooCoreWritePort:
    """Invoke only ``accounting.core_write.execute`` with its closed payload."""

    def __init__(self, client: BridgeClient) -> None:
        self._client = client
        self._user_id: int | None = None

    @property
    def user_id(self) -> int:
        if self._user_id is None:
            raise ValueError("No verified Odoo core-write result has been read.")
        return self._user_id

    def execute(
        self,
        *,
        capability_id: str,
        company_id: int,
        idempotency_key: str,
        confirmation: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        self._user_id = None
        page = self._client.invoke(
            _ACTION,
            {
                "capability_id": capability_id,
                "company_id": company_id,
                "idempotency_key": idempotency_key,
                "confirmation": confirmation,
                "parameters": deepcopy(parameters),
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
            or not (page["result"] is None or _valid_result(page["result"]))
        ):
            raise ValueError("The Odoo bridge returned an invalid core-write result.")
        self._user_id = page["user_id"]
        return page
