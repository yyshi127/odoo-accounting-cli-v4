"""Narrow bridge port for five inventory master-data lists."""

from __future__ import annotations

from typing import Any, Protocol

ACTION = "accounting.inventory_master.read"
CAPABILITY_IDS = frozenset(
    {
        "product.category.list",
        "warehouse.list",
        "stock.location.list",
        "stock.operation_type.list",
        "stock.route.list",
    }
)


class BridgeClient(Protocol):
    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]: ...


class OdooInventoryMasterPort:
    """Invoke only the fixed inventory-master runtime action."""

    def __init__(self, client: BridgeClient) -> None:
        self._client = client
        self._user_id: int | None = None

    @property
    def user_id(self) -> int:
        if self._user_id is None:
            raise ValueError("No verified Odoo inventory-master page has been read.")
        return self._user_id

    def read(
        self,
        *,
        capability_id: str,
        company_id: int,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        if capability_id not in CAPABILITY_IDS:
            raise ValueError("Unsupported inventory-master capability.")
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
                "The Odoo bridge returned an invalid inventory-master page."
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
