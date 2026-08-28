"""Strict contract for Odoo's native journal hash-integrity inspection."""

from __future__ import annotations

import uuid
from typing import Any, Protocol

from odoo_accounting_cli_v4.capabilities.master_data_lists import MasterDataListError


CAPABILITY_ID = "diagnostic.journal_integrity.inspect"
_BASE_RESULT_KEYS = {
    "journal_name",
    "restricted_by_hash_table",
    "status",
    "msg_cover",
}
_VERIFIED_RESULT_KEYS = _BASE_RESULT_KEYS | {
    "first_move_name",
    "first_hash",
    "first_move_date",
    "last_move_name",
    "last_hash",
    "last_move_date",
}


class JournalIntegrityPort(Protocol):
    @property
    def user_id(self) -> int: ...

    def inspect(self, *, company_id: int) -> dict[str, Any]: ...


class JournalIntegrityError(MasterDataListError):
    """Capability-specific error caught by the existing read boundary."""


def _valid_id(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _invalid(message: str) -> JournalIntegrityError:
    return JournalIntegrityError("invalid_request", message, exit_code=2)


def _failed(message: str) -> JournalIntegrityError:
    return JournalIntegrityError("failed_validation", message, exit_code=8)


def validate_journal_integrity_request(
    request: Any,
) -> tuple[str, dict[str, Any]]:
    """Validate the closed no-parameter journal-integrity request."""

    if not isinstance(request, dict) or set(request) != {
        "schema_version",
        "request_id",
        "context",
        "parameters",
    }:
        raise _invalid("The request must match the v1 request envelope.")
    if request["schema_version"] != "v1":
        raise _invalid("schema_version must be 'v1'.")
    request_id = request["request_id"]
    if not isinstance(request_id, str):
        raise _invalid("request_id must be a UUID string.")
    try:
        parsed_request_id = uuid.UUID(request_id)
    except (AttributeError, ValueError) as exc:
        raise _invalid("request_id must be a UUID string.") from exc
    if (
        str(parsed_request_id) != request_id.lower()
        or parsed_request_id.version not in {1, 2, 3, 4, 5}
        or parsed_request_id.variant != uuid.RFC_4122
    ):
        raise _invalid("request_id must use canonical UUID syntax.")

    context = request["context"]
    if not isinstance(context, dict) or set(context) != {
        "database",
        "company_id",
        "user_login",
        "language",
        "timezone",
    }:
        raise _invalid("context must contain only the required v1 fields.")
    for key in ("database", "user_login", "language", "timezone"):
        if not _nonempty_string(context[key]):
            raise _invalid(f"context.{key} must be a non-empty string.")
    if not _valid_id(context["company_id"]):
        raise _invalid("context.company_id must be a positive integer.")
    if request["parameters"] != {}:
        raise _invalid(f"{CAPABILITY_ID} accepts no parameters.")
    return request_id, dict(context)


def _validate_page(port: JournalIntegrityPort, page: Any) -> dict[str, Any] | None:
    if not isinstance(page, dict) or set(page) != {
        "user_id",
        "company_visible",
        "module_installed",
        "access_allowed",
        "data",
    }:
        raise _failed("Odoo returned an invalid journal-integrity page.")
    data = page["data"]
    if (
        not _valid_id(page["user_id"])
        or not _valid_id(port.user_id)
        or page["user_id"] != port.user_id
        or not isinstance(page["company_visible"], bool)
        or not isinstance(page["module_installed"], bool)
        or not isinstance(page["access_allowed"], bool)
        or not (data is None or isinstance(data, dict))
        or (
            page["access_allowed"]
            and not (page["company_visible"] and page["module_installed"])
        )
        or (page["access_allowed"] and data is None)
        or (not page["access_allowed"] and data is not None)
    ):
        raise _failed("Odoo returned an invalid journal-integrity page.")
    return data


def _valid_result(result: Any) -> bool:
    if not isinstance(result, dict):
        return False
    status = result.get("status")
    expected_keys = (
        _VERIFIED_RESULT_KEYS if status == "verified" else _BASE_RESULT_KEYS
    )
    if set(result) != expected_keys or status not in {
        "no_data",
        "verified",
        "corrupted",
    }:
        return False
    if (
        not _nonempty_string(result["journal_name"])
        or result["restricted_by_hash_table"] not in {"V", "X"}
        or not _nonempty_string(result["msg_cover"])
    ):
        return False
    if status == "verified":
        return all(
            _nonempty_string(result[key])
            for key in (
                "first_move_name",
                "first_hash",
                "first_move_date",
                "last_move_name",
                "last_hash",
                "last_move_date",
            )
        )
    return True


def _validate_result(data: Any, *, company_id: int) -> dict[str, Any]:
    if (
        not isinstance(data, dict)
        or set(data) != {"company_id", "printing_date", "results"}
        or data["company_id"] != company_id
        or not _nonempty_string(data["printing_date"])
        or not isinstance(data["results"], list)
        or any(not _valid_result(result) for result in data["results"])
    ):
        raise _failed("Odoo returned an invalid journal-integrity result.")
    return {
        "company_id": data["company_id"],
        "printing_date": data["printing_date"],
        "results": [dict(result) for result in data["results"]],
    }


def inspect_journal_integrity(
    port: JournalIntegrityPort, request: dict[str, Any]
) -> dict[str, Any]:
    """Return Odoo 19's native hash-integrity fields without reimplementation."""

    _, context = validate_journal_integrity_request(request)
    page = port.inspect(company_id=context["company_id"])
    data = _validate_page(port, page)
    if not page["company_visible"]:
        raise JournalIntegrityError(
            "company_unavailable",
            "The requested company is unavailable to the configured user.",
            exit_code=3,
        )
    if not page["module_installed"]:
        raise JournalIntegrityError(
            "module_uninstalled",
            "The journal-integrity capability is not installed in this database.",
            exit_code=4,
        )
    if not page["access_allowed"]:
        raise JournalIntegrityError(
            "unauthorized",
            "The configured user cannot inspect journal integrity.",
            exit_code=3,
        )
    return _validate_result(data, company_id=context["company_id"])
