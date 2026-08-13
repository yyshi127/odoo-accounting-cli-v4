"""Narrow port for fixed local Odoo accounting-report actions."""

from __future__ import annotations

from typing import Any, Protocol


class BridgeClient(Protocol):
    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]: ...


class OdooFinancialReportPort:
    def __init__(self, client: BridgeClient) -> None:
        self._client = client
        self._user_id: int | None = None

    @property
    def user_id(self) -> int:
        if self._user_id is None:
            raise ValueError("No verified Odoo financial-report page has been read.")
        return self._user_id

    def read_page(
        self,
        *,
        company_id: int,
        date_from: str,
        date_to: str,
        after_line_id: str | None,
        limit: int,
    ) -> dict[str, Any]:
        self._user_id = None
        page = self._client.invoke(
            "account.report.trial_balance.read_page",
            {
                "company_id": company_id,
                "date_from": date_from,
                "date_to": date_to,
                "after_line_id": after_line_id,
                "limit": limit,
            },
        )
        expected = {
            "user_id",
            "company_visible",
            "module_installed",
            "access_allowed",
            "cursor_found",
            "report",
            "date",
            "currency",
            "basis",
            "columns",
            "lines",
        }
        if (
            not isinstance(page, dict)
            or set(page) != expected
            or not isinstance(page["user_id"], int)
            or isinstance(page["user_id"], bool)
            or page["user_id"] <= 0
            or not all(
                isinstance(page[key], bool)
                for key in (
                    "company_visible",
                    "module_installed",
                    "access_allowed",
                    "cursor_found",
                )
            )
            or not isinstance(page["report"], dict)
            or not isinstance(page["date"], dict)
            or not isinstance(page["currency"], dict)
            or not isinstance(page["basis"], str)
            or not isinstance(page["columns"], list)
            or not isinstance(page["lines"], list)
        ):
            raise ValueError("The Odoo bridge returned an invalid financial report.")
        self._user_id = page["user_id"]
        return page
