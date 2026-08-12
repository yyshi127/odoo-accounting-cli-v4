"""Narrow master-data ports backed by fixed local Odoo bridge actions."""

from __future__ import annotations

from typing import Any, Protocol


_ACTIONS = {
    "journal.list": "account.journal.read_page",
    "tax.list": "account.tax.read_page",
    "payment_term.list": "account.payment.term.read_page",
    "currency.list": "res.currency.read_page",
}


class BridgeClient(Protocol):
    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]: ...


class OdooMasterDataPort:
    def __init__(self, client: BridgeClient, capability_id: str) -> None:
        try:
            action = _ACTIONS[capability_id]
        except (KeyError, TypeError) as exc:
            raise ValueError("Unsupported master-data capability.") from exc
        self._client = client
        self._action = action
        self._user_id: int | None = None

    @property
    def user_id(self) -> int:
        if self._user_id is None:
            raise ValueError("No verified Odoo master-data page has been read.")
        return self._user_id

    def read_page(
        self,
        *,
        company_id: int,
        after: Any,
        limit: int,
    ) -> dict[str, Any]:
        self._user_id = None
        page = self._client.invoke(
            self._action,
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
            or not isinstance(page["user_id"], int)
            or isinstance(page["user_id"], bool)
            or page["user_id"] <= 0
            or not isinstance(page["company_visible"], bool)
            or not isinstance(page["module_installed"], bool)
            or not isinstance(page["access_allowed"], bool)
            or not isinstance(page["rows"], list)
            or any(not isinstance(row, dict) for row in page["rows"])
        ):
            raise ValueError("The Odoo bridge returned an invalid master-data page.")
        self._user_id = page["user_id"]
        return page
