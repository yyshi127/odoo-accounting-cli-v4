"""Narrow port for the fixed Odoo currency-rate page action."""

from __future__ import annotations

from typing import Any, Protocol

_ACTION = "res.currency.rate.read_page"
_CONVERT_ACTION = "res.currency.convert"


class BridgeClient(Protocol):
    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]: ...


class OdooCurrencyRateListPort:
    def __init__(self, client: BridgeClient) -> None:
        self._client = client
        self._user_id: int | None = None

    @property
    def user_id(self) -> int:
        if self._user_id is None:
            raise ValueError("No verified Odoo currency-rate page has been read.")
        return self._user_id

    def read_page(
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
                "root_company_id",
                "rows",
            }
            or not _positive_integer(page["user_id"])
            or not isinstance(page["company_visible"], bool)
            or not isinstance(page["module_installed"], bool)
            or not isinstance(page["access_allowed"], bool)
            or not (
                page["root_company_id"] is None
                or _positive_integer(page["root_company_id"])
            )
            or not isinstance(page["rows"], list)
            or any(not isinstance(row, dict) for row in page["rows"])
        ):
            raise ValueError("The Odoo bridge returned an invalid currency-rate page.")
        self._user_id = page["user_id"]
        return page


class OdooCurrencyConvertPort:
    def __init__(self, client: BridgeClient) -> None:
        self._client = client
        self._user_id: int | None = None

    @property
    def user_id(self) -> int:
        if self._user_id is None:
            raise ValueError("No verified Odoo currency conversion has been read.")
        return self._user_id

    def convert(
        self,
        *,
        company_id: int,
        amount: str,
        from_currency_id: int,
        to_currency_id: int,
        conversion_date: str,
    ) -> dict[str, Any]:
        self._user_id = None
        page = self._client.invoke(
            _CONVERT_ACTION,
            {
                "company_id": company_id,
                "amount": amount,
                "from_currency_id": from_currency_id,
                "to_currency_id": to_currency_id,
                "date": conversion_date,
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
                "conversion",
            }
            or not _positive_integer(page["user_id"])
            or not isinstance(page["company_visible"], bool)
            or not isinstance(page["module_installed"], bool)
            or not isinstance(page["access_allowed"], bool)
            or not (
                page["conversion"] is None
                or isinstance(page["conversion"], dict)
            )
        ):
            raise ValueError("The Odoo bridge returned an invalid currency conversion.")
        self._user_id = page["user_id"]
        return page


def _positive_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0
