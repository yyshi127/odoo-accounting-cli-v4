"""Narrow bridge port for period-context reads."""

from __future__ import annotations

from typing import Any, Protocol

ACTION = "accounting.period_context.read"
CAPABILITY_IDS = frozenset(
    {
        "company.lock_dates.inspect",
        "company.fiscal_year.resolve",
        "fiscal_year.search",
        "fiscal_year.get",
    }
)


class BridgeClient(Protocol):
    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]: ...


class OdooPeriodContextPort:
    def __init__(self, client: BridgeClient) -> None:
        self._client = client
        self._user_id: int | None = None

    @property
    def user_id(self) -> int:
        if self._user_id is None:
            raise ValueError("No verified Odoo period-context page has been read.")
        return self._user_id

    def read(
        self,
        *,
        capability_id: str,
        company_id: int,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        if capability_id not in CAPABILITY_IDS:
            raise ValueError("Unsupported period-context capability.")
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
            raise ValueError("The Odoo bridge returned an invalid period-context page.")
        self._user_id = page["user_id"]
        return page


def _valid_page(page: Any) -> bool:
    return (
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
