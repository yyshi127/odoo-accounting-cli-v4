"""Narrow port for the fixed Odoo bank-transaction page action."""

from __future__ import annotations

from typing import Any, Protocol

_ACTION = "account.bank.statement.line.search_page"


class BridgeClient(Protocol):
    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]: ...


class OdooBankTransactionListPort:
    def __init__(self, client: BridgeClient) -> None:
        self._client = client
        self._user_id: int | None = None

    @property
    def user_id(self) -> int:
        if self._user_id is None:
            raise ValueError("No verified Odoo bank-transaction page has been read.")
        return self._user_id

    def search_page(
        self,
        *,
        company_id: int,
        after: list[Any] | None,
        limit: int,
    ) -> dict[str, Any]:
        self._user_id = None
        page = self._client.invoke(
            _ACTION,
            {"company_id": company_id, "after": after, "limit": limit},
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
            or not _positive_integer(page["user_id"])
            or not isinstance(page["company_visible"], bool)
            or not isinstance(page["module_installed"], bool)
            or not isinstance(page["access_allowed"], bool)
            or not isinstance(page["rows"], list)
            or any(not isinstance(row, dict) for row in page["rows"])
        ):
            raise ValueError(
                "The Odoo bridge returned an invalid bank-transaction page."
            )
        self._user_id = page["user_id"]
        return page


class OdooBankTransactionSearchPort(OdooBankTransactionListPort):
    """Invoke the fixed filtered bank-transaction search action."""

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
            _ACTION,
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
            or not _positive_integer(page["user_id"])
            or not isinstance(page["company_visible"], bool)
            or not isinstance(page["module_installed"], bool)
            or not isinstance(page["access_allowed"], bool)
            or not isinstance(page["rows"], list)
            or any(not isinstance(row, dict) for row in page["rows"])
        ):
            raise ValueError(
                "The Odoo bridge returned an invalid bank-transaction page."
            )
        self._user_id = page["user_id"]
        return page


def _positive_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0
