"""Narrow payment ports backed by two fixed local Odoo bridge actions."""

from __future__ import annotations

from typing import Any, Protocol


class BridgeClient(Protocol):
    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]: ...


class OdooPaymentPort:
    """Expose only the closed search and exact-payment read actions."""

    def __init__(self, client: BridgeClient) -> None:
        self._client = client
        self._user_id: int | None = None

    @property
    def user_id(self) -> int:
        if self._user_id is None:
            raise ValueError("No verified Odoo payment result has been read.")
        return self._user_id

    def search_page(
        self,
        *,
        company_id: int,
        after: list[Any] | None,
        limit: int,
        filters: dict[str, Any],
    ) -> dict[str, Any]:
        return self._invoke(
            "account.payment.search_page",
            {
                "company_id": company_id,
                "after": after,
                "limit": limit,
                "filters": filters,
            },
            result_key="rows",
            allow_null=False,
        )

    def get_payment(self, *, company_id: int, payment_id: int) -> dict[str, Any]:
        return self._invoke(
            "account.payment.get",
            {"company_id": company_id, "payment_id": payment_id},
            result_key="payment",
            allow_null=True,
        )

    def _invoke(
        self,
        action: str,
        payload: dict[str, Any],
        *,
        result_key: str,
        allow_null: bool,
    ) -> dict[str, Any]:
        self._user_id = None
        page = self._client.invoke(action, payload)
        expected = {
            "user_id",
            "company_visible",
            "module_installed",
            "access_allowed",
            result_key,
        }
        value = page.get(result_key) if isinstance(page, dict) else None
        valid_result = (
            isinstance(value, list) and all(isinstance(row, dict) for row in value)
            if result_key == "rows"
            else isinstance(value, dict) or (allow_null and value is None)
        )
        if (
            not isinstance(page, dict)
            or set(page) != expected
            or not isinstance(page["user_id"], int)
            or isinstance(page["user_id"], bool)
            or page["user_id"] <= 0
            or not isinstance(page["company_visible"], bool)
            or not isinstance(page["module_installed"], bool)
            or not isinstance(page["access_allowed"], bool)
            or not valid_result
        ):
            raise ValueError("The Odoo bridge returned an invalid payment result.")
        self._user_id = page["user_id"]
        return page
