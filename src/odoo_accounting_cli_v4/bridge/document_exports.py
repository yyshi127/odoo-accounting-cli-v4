"""Narrow bridge port for fixed business-document PDF exports."""

from __future__ import annotations

from typing import Any, Protocol

from ..capabilities.document_exports import DOCUMENT_EXPORT_SPECS

ACTION = "ir.actions.report.fixed_document_export"
_PAGE_KEYS = {
    "user_id",
    "company_visible",
    "module_installed",
    "access_allowed",
    "record_visible",
    "applicable",
    "filename",
    "format",
    "mimetype",
    "byte_count",
    "sha256",
    "content_base64",
}
_NULLABLE_BINARY_KEYS = ("filename", "mimetype", "sha256", "content_base64")


class BridgeClient(Protocol):
    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]: ...


def _positive_id(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


class OdooDocumentExportPort:
    """Bridge adapter that exposes no caller-controlled report or model name."""

    def __init__(self, client: BridgeClient) -> None:
        self._client = client
        self._user_id: int | None = None

    @property
    def user_id(self) -> int:
        if self._user_id is None:
            raise ValueError("No verified Odoo document export has been read.")
        return self._user_id

    def export(
        self,
        *,
        capability_id: str,
        company_id: int,
        target_id: int,
        layout: str | None,
    ) -> dict[str, Any]:
        self._user_id = None
        try:
            spec = DOCUMENT_EXPORT_SPECS[capability_id]
        except (KeyError, TypeError) as exc:
            raise ValueError("Unsupported document-export capability.") from exc
        if not _positive_id(company_id):
            raise ValueError("company_id must be a positive integer.")
        if not _positive_id(target_id):
            raise ValueError("target_id must be a positive integer.")
        layouts = spec.get("layouts")
        if layouts is not None:
            if not isinstance(layout, str) or layout not in layouts:
                raise ValueError("Unsupported invoice PDF layout.")
        elif layout is not None:
            raise ValueError("layout is unsupported for this document export.")

        payload = {
            "capability_id": capability_id,
            "company_id": company_id,
            spec["id_parameter"]: target_id,
        }
        if layout is not None:
            payload["layout"] = layout
        page = self._client.invoke(ACTION, payload)
        if (
            not isinstance(page, dict)
            or set(page) != _PAGE_KEYS
            or not _positive_id(page["user_id"])
            or not all(
                isinstance(page[key], bool)
                for key in (
                    "company_visible",
                    "module_installed",
                    "access_allowed",
                    "record_visible",
                    "applicable",
                )
            )
            or page["access_allowed"]
            and not (page["company_visible"] and page["module_installed"])
            or page["record_visible"]
            and not page["access_allowed"]
            or page["applicable"]
            and not page["record_visible"]
            or page["format"] != "pdf"
            or not isinstance(page["byte_count"], int)
            or isinstance(page["byte_count"], bool)
            or page["byte_count"] < 0
            or any(
                page[key] is not None and not isinstance(page[key], str)
                for key in _NULLABLE_BINARY_KEYS
            )
            or not page["applicable"]
            and (
                page["byte_count"] != 0
                or any(page[key] is not None for key in _NULLABLE_BINARY_KEYS)
            )
        ):
            raise ValueError("The Odoo bridge returned an invalid document export.")
        self._user_id = page["user_id"]
        return page
