"""Company-scoped chart-of-accounts read capability."""

from __future__ import annotations

import base64
import binascii
import json
import uuid
from typing import Any, Protocol


CAPABILITY_ID = "account.account.list"
ACCOUNT_FIELDS = (
    "id",
    "code",
    "name",
    "account_type",
    "active",
    "reconcile",
    "company_ids",
)
DEFAULT_LIMIT = 100
MAX_LIMIT = 1000
_CURSOR_VERSION = 1


class AccountListPort(Protocol):
    """Narrow ORM port implemented later by the local Odoo bridge."""

    def company_is_visible(self, company_id: int) -> bool: ...

    def module_is_installed(self, module: str) -> bool: ...

    def can_read_accounts(self) -> bool: ...

    def search_accounts(
        self,
        *,
        company_id: int,
        after_code: str | None,
        after_id: int | None,
        limit: int,
    ) -> list[dict[str, Any]]: ...


class AccountListError(RuntimeError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        exit_code: int,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code
        self.retryable = retryable
        self.details = details or {}


def _is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _invalid(message: str, *, code: str = "invalid_request") -> AccountListError:
    return AccountListError(code, message, exit_code=2)


def validate_account_list_request(
    request: Any,
) -> tuple[str, dict[str, Any], int, str | None]:
    if not isinstance(request, dict) or set(request) != {
        "schema_version",
        "request_id",
        "context",
        "parameters",
    }:
        raise _invalid("The request must match the v1 request envelope.")
    if request["schema_version"] != "v1":
        raise _invalid("schema_version must be 'v1'.")
    if not isinstance(request["request_id"], str):
        raise _invalid("request_id must be a UUID string.")
    try:
        parsed_request_id = uuid.UUID(request["request_id"])
    except (ValueError, AttributeError) as exc:
        raise _invalid("request_id must be a UUID string.") from exc
    if str(parsed_request_id) != request["request_id"].lower():
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
        if not isinstance(context[key], str) or not context[key].strip():
            raise _invalid(f"context.{key} must be a non-empty string.")
    if not _is_integer(context["company_id"]) or context["company_id"] <= 0:
        raise _invalid("context.company_id must be a positive integer.")

    parameters = request["parameters"]
    if not isinstance(parameters, dict) or not set(parameters) <= {"limit", "cursor"}:
        raise _invalid("parameters may contain only limit and cursor.")
    limit = parameters.get("limit", DEFAULT_LIMIT)
    if not _is_integer(limit) or not 1 <= limit <= MAX_LIMIT:
        raise _invalid(f"parameters.limit must be between 1 and {MAX_LIMIT}.")
    cursor = parameters.get("cursor")
    if cursor is not None and (
        not isinstance(cursor, str) or not cursor or len(cursor) > 4096
    ):
        raise _invalid("parameters.cursor must be null or a non-empty cursor string.")
    return request["request_id"], context, limit, cursor


def encode_cursor(
    code: str,
    record_id: int,
    *,
    company_id: int,
    database: str,
    user_login: str,
) -> str:
    payload = json.dumps(
        {
            "capability": CAPABILITY_ID,
            "code": code,
            "company_id": company_id,
            "database": database,
            "id": record_id,
            "user_login": user_login,
            "version": _CURSOR_VERSION,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def decode_cursor(
    cursor: str, *, company_id: int, database: str, user_login: str
) -> tuple[str, int]:
    try:
        padding = "=" * (-len(cursor) % 4)
        raw = base64.b64decode(
            (cursor + padding).encode("ascii"), altchars=b"-_", validate=True
        )
        value = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeError, json.JSONDecodeError, binascii.Error) as exc:
        raise _invalid("The cursor is invalid.", code="invalid_cursor") from exc
    if not isinstance(value, dict) or set(value) != {
        "capability",
        "code",
        "company_id",
        "database",
        "id",
        "user_login",
        "version",
    }:
        raise _invalid("The cursor is invalid.", code="invalid_cursor")
    if (
        value["capability"] != CAPABILITY_ID
        or not _is_integer(value["version"])
        or value["version"] != _CURSOR_VERSION
        or not _is_integer(value["company_id"])
        or value["company_id"] != company_id
        or value["database"] != database
        or value["user_login"] != user_login
        or not isinstance(value["code"], str)
        or not value["code"]
        or not _is_integer(value["id"])
        or value["id"] <= 0
    ):
        raise _invalid("The cursor does not match this request.", code="invalid_cursor")
    return value["code"], value["id"]


def _validated_rows(
    rows: Any,
    *,
    company_id: int,
    after: tuple[str, int] | None,
) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        raise AccountListError(
            "failed_validation",
            "Odoo returned an invalid account list.",
            exit_code=8,
        )
    result: list[dict[str, Any]] = []
    previous = after
    for row in rows:
        if not isinstance(row, dict):
            raise AccountListError(
                "failed_validation",
                "Odoo returned an invalid account record.",
                exit_code=8,
            )
        record_id = row.get("id")
        code = row.get("code")
        company_ids = row.get("company_ids")
        if (
            not _is_integer(record_id)
            or record_id <= 0
            or not isinstance(code, str)
            or not code
            or not isinstance(row.get("name"), str)
            or not row["name"]
            or not isinstance(row.get("account_type"), str)
            or not row["account_type"]
            or not isinstance(row.get("active"), bool)
            or not isinstance(row.get("reconcile"), bool)
            or not isinstance(company_ids, list)
            or any(
                not _is_integer(item) or item <= 0 for item in company_ids
            )
            or len(company_ids) != len(set(company_ids))
            or company_id not in company_ids
        ):
            raise AccountListError(
                "failed_validation",
                "Odoo returned an account outside the verified company scope.",
                exit_code=8,
            )
        key = (code, record_id)
        if previous is not None and key <= previous:
            raise AccountListError(
                "failed_validation",
                "Odoo returned accounts in an unstable order.",
                exit_code=8,
            )
        previous = key
        result.append({field: row.get(field) for field in ACCOUNT_FIELDS})
    return result


def read_account_accounts(
    port: AccountListPort, request: dict[str, Any]
) -> dict[str, Any]:
    """Read one verified keyset page without bypassing Odoo ACLs."""

    _, context, limit, cursor = validate_account_list_request(request)
    company_id = context["company_id"]
    if not port.company_is_visible(company_id):
        raise AccountListError(
            "company_unavailable",
            "The requested company is unavailable to the configured user.",
            exit_code=3,
        )
    if not port.module_is_installed("account"):
        raise AccountListError(
            "uninstalled",
            "The account capability is not installed in this database.",
            exit_code=4,
        )
    if not port.can_read_accounts():
        raise AccountListError(
            "unauthorized",
            "The configured user cannot read the chart of accounts.",
            exit_code=3,
        )

    after = (
        decode_cursor(
            cursor,
            company_id=company_id,
            database=context["database"],
            user_login=context["user_login"],
        )
        if cursor
        else None
    )
    rows = port.search_accounts(
        company_id=company_id,
        after_code=after[0] if after else None,
        after_id=after[1] if after else None,
        limit=limit + 1,
    )
    records = _validated_rows(rows, company_id=company_id, after=after)
    has_more = len(records) > limit
    items = records[:limit]
    next_cursor = None
    if has_more and items:
        next_cursor = encode_cursor(
            items[-1]["code"],
            items[-1]["id"],
            company_id=company_id,
            database=context["database"],
            user_login=context["user_login"],
        )
    return {"items": items, "has_more": has_more, "next_cursor": next_cursor}
