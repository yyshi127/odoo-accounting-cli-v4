"""Narrow port for fixed local Odoo accounting-report actions."""

from __future__ import annotations

from typing import Any, Protocol

_ACTIONS = {
    "report.trial_balance": "account.report.trial_balance.read_page",
    "report.balance_sheet": "account.report.balance_sheet.read_page",
    "report.profit_and_loss": "account.report.profit_and_loss.read_page",
    "report.cash_flow": "account.report.cash_flow.read_page",
    "report.tax": "account.report.tax.read_page",
    "report.general_ledger": "account.report.general_ledger.read_page",
    "report.partner_ledger": "account.report.partner_ledger.read_page",
    "report.aged_receivable": "account.report.aged_receivable.read_page",
    "report.aged_payable": "account.report.aged_payable.read_page",
    "report.journal": "account.report.journal.read_page",
    "report.executive_summary": "account.report.executive_summary.read_page",
    "report.asset": "account.report.asset.read_page",
    "report.deferred_expense": "account.report.deferred_expense.read_page",
    "report.deferred_revenue": "account.report.deferred_revenue.read_page",
    "report.multicurrency_revaluation": "account.report.multicurrency_revaluation.read_page",
    "report.china.balance_sheet": "account.report.china_balance_sheet.read_page",
    "report.china.profit_and_loss": "account.report.china_profit_and_loss.read_page",
    "report.china.cash_flow": "account.report.china_cash_flow.read_page",
    "report.singapore.gst": "account.report.singapore_gst.read_page",
    "report.bank_reconciliation": "account.report.bank_reconciliation.read_page",
    "report.customer_statement": "account.report.customer_statement.read_page",
    "report.followup": "account.report.followup.read_page",
}
_EXPORT_ACTION = "account.report.fixed_export"
_EXPORT_CAPABILITY_IDS = frozenset(
    {
        "report.trial_balance.export",
        "report.balance_sheet.export",
        "report.profit_and_loss.export",
        "report.cash_flow.export",
        "report.tax.export",
        "report.general_ledger.export",
        "report.partner_ledger.export",
        "report.aged_receivable.export",
        "report.aged_payable.export",
        "report.executive_summary.export",
    }
)


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
        self._requires_journal_id = capability_id == "report.bank_reconciliation"
        self._requires_partner_id = capability_id in {
            "report.customer_statement",
            "report.followup",
        }
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
        journal_id: int | None = None,
        partner_id: int | None = None,
    ) -> dict[str, Any]:
        self._user_id = None
        if self._requires_journal_id:
            if (
                not isinstance(journal_id, int)
                or isinstance(journal_id, bool)
                or journal_id <= 0
            ):
                raise ValueError("journal_id must be a positive integer.")
        elif journal_id is not None:
            raise ValueError("journal_id is unsupported for this financial report.")
        if self._requires_partner_id:
            if (
                not isinstance(partner_id, int)
                or isinstance(partner_id, bool)
                or partner_id <= 0
            ):
                raise ValueError("partner_id must be a positive integer.")
        elif partner_id is not None:
            raise ValueError("partner_id is unsupported for this financial report.")
        payload = {
            "company_id": company_id,
            "date_from": date_from,
            "date_to": date_to,
            "after_line_id": after_line_id,
            "limit": limit,
        }
        if journal_id is not None:
            payload["journal_id"] = journal_id
        if partner_id is not None:
            payload["partner_id"] = partner_id
        page = self._client.invoke(
            self._action,
            payload,
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


class OdooFinancialReportExportPort:
    """Narrow bridge port for the shared fixed financial-report export action."""

    def __init__(self, client: BridgeClient) -> None:
        self._client = client
        self._user_id: int | None = None

    @property
    def user_id(self) -> int:
        if self._user_id is None:
            raise ValueError("No verified Odoo financial-report export has been read.")
        return self._user_id

    def export(
        self,
        *,
        capability_id: str,
        company_id: int,
        date_from: str | None,
        date_to: str,
        format: str,
    ) -> dict[str, Any]:
        self._user_id = None
        if (
            not isinstance(capability_id, str)
            or capability_id not in _EXPORT_CAPABILITY_IDS
        ):
            raise ValueError("Unsupported financial-report export capability.")
        page = self._client.invoke(
            _EXPORT_ACTION,
            {
                "capability_id": capability_id,
                "company_id": company_id,
                "date_from": date_from,
                "date_to": date_to,
                "format": format,
            },
        )
        expected = {
            "user_id",
            "company_visible",
            "module_installed",
            "access_allowed",
            "filename",
            "format",
            "mimetype",
            "byte_count",
            "sha256",
            "content_base64",
        }
        nullable_strings = ("filename", "mimetype", "sha256", "content_base64")
        if (
            not isinstance(page, dict)
            or set(page) != expected
            or not isinstance(page["user_id"], int)
            or isinstance(page["user_id"], bool)
            or page["user_id"] <= 0
            or not all(
                isinstance(page[key], bool)
                for key in ("company_visible", "module_installed", "access_allowed")
            )
            or not isinstance(page["format"], str)
            or not isinstance(page["byte_count"], int)
            or isinstance(page["byte_count"], bool)
            or page["byte_count"] < 0
            or any(
                page[key] is not None and not isinstance(page[key], str)
                for key in nullable_strings
            )
        ):
            raise ValueError(
                "The Odoo bridge returned an invalid financial-report export."
            )
        self._user_id = page["user_id"]
        return page
