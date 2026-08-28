"""Narrow bridge port for the official Odoo budget execution report."""

from __future__ import annotations

from typing import Any, Protocol

ACTION = "accounting.budget_report.read"


class BridgeClient(Protocol):
    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]: ...


class OdooBudgetReportPort:
    def __init__(self, client: BridgeClient) -> None:
        self._client = client
        self._user_id: int | None = None

    @property
    def user_id(self) -> int:
        if self._user_id is None:
            raise ValueError("No verified Odoo budget-report page has been read.")
        return self._user_id

    def read(self, *, company_id: int, parameters: dict[str, Any]) -> dict[str, Any]:
        self._user_id = None
        page = self._client.invoke(
            ACTION,
            {
                "company_id": company_id,
                "parameters": parameters,
            },
        )
        if not _valid_page(page):
            raise ValueError("The Odoo bridge returned an invalid budget-report page.")
        self._user_id = page["user_id"]
        return page


def _valid_page(page: Any) -> bool:
    return bool(
        isinstance(page, dict)
        and set(page)
        == {
            "user_id",
            "company_visible",
            "module_installed",
            "access_allowed",
            "cursor_found",
            "items",
        }
        and isinstance(page["user_id"], int)
        and not isinstance(page["user_id"], bool)
        and page["user_id"] > 0
        and all(
            isinstance(page[key], bool)
            for key in (
                "company_visible",
                "module_installed",
                "access_allowed",
                "cursor_found",
            )
        )
        and isinstance(page["items"], list)
        and all(isinstance(item, dict) for item in page["items"])
    )
