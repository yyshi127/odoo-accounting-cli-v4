"""Capability-bound ports for fixed local Odoo open-items actions."""

from __future__ import annotations

from typing import Any, Protocol


_ACTIONS = {
    "receivable.open_items.list": (
        "account.move.line.receivable.open_items.search_page"
    ),
    "payable.open_items.list": "account.move.line.payable.open_items.search_page",
}


class BridgeClient(Protocol):
    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]: ...


class OdooOpenItemsPort:
    def __init__(self, client: BridgeClient, capability_id: str) -> None:
        if capability_id not in _ACTIONS:
            raise ValueError("Unsupported open-items capability.")
        self._client = client
        self._action = _ACTIONS[capability_id]
        self._user_id: int | None = None

    @property
    def user_id(self) -> int:
        if self._user_id is None:
            raise ValueError("No verified Odoo open-items page has been read.")
        return self._user_id

    def search_page(
        self,
        *,
        company_id: int,
        after: list[Any] | None,
        limit: int,
        filters: dict[str, Any],
    ) -> dict[str, Any]:
        self._user_id = None
        page = self._client.invoke(
            self._action,
            {
                "company_id": company_id,
                "after": after,
                "limit": limit,
                "filters": filters,
            },
        )
        if (
            not isinstance(page, dict)
            or set(page)
            != {
                "user_id",
                "company_visible",
                "module_installed",
                "access_allowed",
                "rows",
            }
            or not isinstance(page["user_id"], int)
            or isinstance(page["user_id"], bool)
            or page["user_id"] <= 0
            or not isinstance(page["company_visible"], bool)
            or not isinstance(page["module_installed"], bool)
            or not isinstance(page["access_allowed"], bool)
            or not isinstance(page["rows"], list)
            or any(not isinstance(row, dict) for row in page["rows"])
        ):
            raise ValueError("The Odoo bridge returned an invalid open-items page.")
        self._user_id = page["user_id"]
        return page
