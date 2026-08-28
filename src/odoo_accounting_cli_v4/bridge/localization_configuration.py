"""Narrow bridge port for fixed localization configuration inspections."""

from __future__ import annotations

from typing import Any, Protocol

ACTION = "accounting.localization_configuration.inspect"
CAPABILITY_IDS = frozenset(
    {
        "localization.china.configuration.inspect",
        "localization.singapore.configuration.inspect",
    }
)


class BridgeClient(Protocol):
    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]: ...


class OdooLocalizationConfigurationPort:
    """Invoke only the fixed localization-configuration runtime action."""

    def __init__(self, client: BridgeClient) -> None:
        self._client = client
        self._user_id: int | None = None

    @property
    def user_id(self) -> int:
        if self._user_id is None:
            raise ValueError("No verified localization configuration page has been read.")
        return self._user_id

    def read(
        self,
        *,
        capability_id: str,
        company_id: int,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        if capability_id not in CAPABILITY_IDS:
            raise ValueError("Unsupported localization configuration capability.")
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
                "The Odoo bridge returned an invalid localization configuration page."
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
