"""Narrow accounting-partner port backed by the local Odoo bridge."""

from __future__ import annotations

from typing import Any, Protocol


class BridgeClient(Protocol):
    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]: ...


class OdooPartnerAccountingPort:
    def __init__(self, client: BridgeClient) -> None:
        self._client = client
        self._user_id: int | None = None

    @property
    def user_id(self) -> int:
        if self._user_id is None:
            raise ValueError("No verified Odoo accounting-partner page has been read.")
        return self._user_id

    def search_page(
        self,
        *,
        company_id: int,
        after: list[Any] | None,
        limit: int,
        filters: dict[str, Any],
    ) -> dict[str, Any]:
        page = self._client.invoke(
            "res.partner.accounting.search_page",
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
            raise ValueError("The Odoo bridge returned an invalid partner page.")
        self._user_id = page["user_id"]
        return page
