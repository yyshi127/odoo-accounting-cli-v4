"""Narrow account.account port backed by the local Odoo bridge."""

from __future__ import annotations

from typing import Any, Protocol


class BridgeClient(Protocol):
    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]: ...


class OdooAccountListPort:
    def __init__(self, client: BridgeClient) -> None:
        self._client = client
        self._user_id: int | None = None

    @property
    def user_id(self) -> int:
        if self._user_id is None:
            raise ValueError("No verified Odoo account page has been read.")
        return self._user_id

    def read_page(
        self,
        *,
        company_id: int,
        after_code: str | None,
        after_id: int | None,
        limit: int,
    ) -> dict[str, Any]:
        page = self._client.invoke(
            "account.account.read_page",
            {
                "company_id": company_id,
                "after_code": after_code,
                "after_id": after_id,
                "limit": limit,
            },
        )
        if (
            set(page)
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
            raise ValueError("The Odoo bridge returned an invalid account page.")
        self._user_id = page["user_id"]
        return page
