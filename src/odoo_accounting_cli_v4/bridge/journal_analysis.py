"""Narrow bridge port for journal accounting-date and analysis reads."""

from __future__ import annotations

from typing import Any, Protocol

ACTION = "accounting.journal_analysis.read"
CAPABILITY_IDS = frozenset(
    {
        "analytic.line.summary",
        "journal.accounting_date.resolve",
        "journal_item.analysis.summary",
    }
)


class BridgeClient(Protocol):
    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]: ...


class OdooJournalAnalysisPort:
    def __init__(self, client: BridgeClient) -> None:
        self._client = client
        self._user_id: int | None = None

    @property
    def user_id(self) -> int:
        if self._user_id is None:
            raise ValueError("No verified Odoo journal-analysis page has been read.")
        return self._user_id

    def read(
        self,
        *,
        capability_id: str,
        company_id: int,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        if capability_id not in CAPABILITY_IDS:
            raise ValueError("Unsupported journal-analysis capability.")
        self._user_id = None
        page = self._client.invoke(
            ACTION,
            {
                "capability_id": capability_id,
                "company_id": company_id,
                "parameters": parameters,
            },
        )
        if not _valid_page(page):
            raise ValueError(
                "The Odoo bridge returned an invalid journal-analysis page."
            )
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
        and _positive_integer(page["user_id"])
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


def _positive_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0
