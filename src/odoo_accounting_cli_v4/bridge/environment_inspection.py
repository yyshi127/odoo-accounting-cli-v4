"""Narrow ports for fixed accounting environment inspections."""

from __future__ import annotations

from typing import Any, Protocol


_ACTIONS = {
    "company.accounting_configuration.inspect": "res.company.accounting_configuration.inspect",
    "diagnostic.accounting_environment.inspect": "accounting.environment.diagnostic.inspect",
}


class BridgeClient(Protocol):
    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]: ...


class OdooEnvironmentInspectionPort:
    def __init__(self, client: BridgeClient, capability_id: str) -> None:
        try:
            self._action = _ACTIONS[capability_id]
        except (KeyError, TypeError) as exc:
            raise ValueError("Unsupported environment inspection capability.") from exc
        self._client = client
        self._user_id: int | None = None

    @property
    def user_id(self) -> int:
        if self._user_id is None:
            raise ValueError("No verified environment inspection has been read.")
        return self._user_id

    def inspect(self, *, company_id: int) -> dict[str, Any]:
        self._user_id = None
        page = self._client.invoke(self._action, {"company_id": company_id})
        if (
            not isinstance(page, dict)
            or set(page)
            != {
                "user_id",
                "company_visible",
                "module_installed",
                "access_allowed",
                "data",
            }
            or not isinstance(page["user_id"], int)
            or isinstance(page["user_id"], bool)
            or page["user_id"] <= 0
            or not isinstance(page["company_visible"], bool)
            or not isinstance(page["module_installed"], bool)
            or not isinstance(page["access_allowed"], bool)
            or not isinstance(page["data"], dict)
        ):
            raise ValueError("The Odoo bridge returned an invalid inspection result.")
        self._user_id = page["user_id"]
        return page
