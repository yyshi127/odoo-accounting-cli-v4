"""Narrow port for fixed local Odoo accounting-report actions."""

from __future__ import annotations

from typing import Any, Protocol


_ACTIONS = {
    "report.trial_balance": "account.report.trial_balance.read_page",
    "report.balance_sheet": "account.report.balance_sheet.read_page",
    "report.profit_and_loss": "account.report.profit_and_loss.read_page",
    "report.cash_flow": "account.report.cash_flow.read_page",
    "report.tax": "account.report.tax.read_page",
}

class BridgeClient(Protocol):
    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]: ...


class OdooFinancialReportPort:
    def __init__(
        self, client: BridgeClient, capability_id: str = "report.trial_balance"
    ) -> None:
        try:
            action = _ACTIONS[capability_id]
        except (KeyError, TypeError) as exc:
            raise ValueError("Unsupported financial-report capability.") from exc
        self._client = client
        self._action = action
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
        date_from: str | None,
        date_to: str,
        after_line_id: str | None,
        limit: int,
    ) -> dict[str, Any]:
        self._user_id = None
        page = self._client.invoke(
            self._action,
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
