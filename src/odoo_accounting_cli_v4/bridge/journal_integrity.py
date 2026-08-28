"""Narrow port for Odoo's native journal hash-integrity inspection."""

from __future__ import annotations

from typing import Any, Protocol


_ACTION = "res.company.journal_integrity.inspect"


class BridgeClient(Protocol):
    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]: ...


class OdooJournalIntegrityPort:
    def __init__(self, client: BridgeClient) -> None:
        self._client = client
        self._user_id: int | None = None

    @property
    def user_id(self) -> int:
        if self._user_id is None:
            raise ValueError("No verified journal-integrity result has been read.")
        return self._user_id

    def inspect(self, *, company_id: int) -> dict[str, Any]:
        self._user_id = None
        page = self._client.invoke(_ACTION, {"company_id": company_id})
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
                "The Odoo bridge returned an invalid journal-integrity result."
            )
        self._user_id = page["user_id"]
        return page
