"""Narrow port for the fixed fiscal-position resolver action."""

from __future__ import annotations

from typing import Any, Protocol


_ACTION = "account.fiscal.position.resolve"


class BridgeClient(Protocol):
    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]: ...


class OdooFiscalPositionResolvePort:
    def __init__(self, client: BridgeClient) -> None:
        self._client = client
        self._user_id: int | None = None

    @property
    def user_id(self) -> int:
        if self._user_id is None:
            raise ValueError("No verified fiscal-position result has been read.")
        return self._user_id

    def resolve(
        self,
        *,
        company_id: int,
        partner_id: int,
        delivery_partner_id: int | None,
        account_id: int | None,
        tax_ids: list[int] | None,
    ) -> dict[str, Any]:
        self._user_id = None
        page = self._client.invoke(
            _ACTION,
            {
                "company_id": company_id,
                "partner_id": partner_id,
                "delivery_partner_id": delivery_partner_id,
                "account_id": account_id,
                "tax_ids": None if tax_ids is None else list(tax_ids),
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
                "data",
            }
            or not isinstance(page["user_id"], int)
            or isinstance(page["user_id"], bool)
            or page["user_id"] <= 0
            or not isinstance(page["company_visible"], bool)
            or not isinstance(page["module_installed"], bool)
            or not isinstance(page["access_allowed"], bool)
            or not (page["data"] is None or isinstance(page["data"], dict))
        ):
            raise ValueError(
                "The Odoo bridge returned an invalid fiscal-position result."
            )
        self._user_id = page["user_id"]
        return page
