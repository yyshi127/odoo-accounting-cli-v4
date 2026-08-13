"""Strict contract for company-scoped accounting partner search."""

from __future__ import annotations

import base64
import binascii
import json
import uuid
from typing import Any, Protocol


CAPABILITY_ID = "partner.accounting.search"
DEFAULT_LIMIT = 100
MAX_LIMIT = 1000
_CURSOR_VERSION = 1
_ROLES = frozenset({"both", "customer", "vendor"})
_FILTER_FIELDS = frozenset({"role", "query"})
_ROW_FIELDS = frozenset(
    {
        "id",
        "complete_name",
        "ref",
        "active",
        "is_company",
        "company_id",
        "customer_rank",
        "supplier_rank",
        "receivable_account",
        "payable_account",
    }
)


class PartnerAccountingPort(Protocol):
    """Narrow bridge port for the fixed accounting-partner search."""

    @property
    def user_id(self) -> int: ...

    def search_page(
        self,
        *,
        company_id: int,
        after: list[Any] | None,
        limit: int,
        filters: dict[str, Any],
    ) -> dict[str, Any]: ...


class PartnerAccountingError(RuntimeError):
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


def _valid_id(value: Any) -> bool:
    return _is_integer(value) and value > 0


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _valid_optional_string(value: Any) -> bool:
    return value is None or _is_nonempty_string(value)


def _invalid(message: str, *, code: str = "invalid_request") -> PartnerAccountingError:
    return PartnerAccountingError(code, message, exit_code=2)


def _failed(message: str) -> PartnerAccountingError:
    return PartnerAccountingError("failed_validation", message, exit_code=8)


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate cursor key")
        value[key] = item
    return value


def _reject_json_float(_value: str) -> None:
    raise ValueError("floating-point cursor number")


def _reject_json_constant(_value: str) -> None:
    raise ValueError("non-finite cursor number")


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _validate_envelope(request: Any) -> tuple[str, dict[str, Any], dict[str, Any]]:
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
    except (ValueError, AttributeError) as exc:
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
        if not _is_nonempty_string(context[key]):
            raise _invalid(f"context.{key} must be a non-empty string.")
    if not _valid_id(context["company_id"]):
        raise _invalid("context.company_id must be a positive integer.")

    parameters = request["parameters"]
    if not isinstance(parameters, dict):
        raise _invalid("parameters must be an object.")
    return request_id, context, parameters


def validate_partner_accounting_search_request(
    request: Any,
) -> tuple[str, dict[str, Any], dict[str, Any], int, str | None]:
    """Validate and normalize the closed partner search request."""

    request_id, context, parameters = _validate_envelope(request)
    if not set(parameters) <= _FILTER_FIELDS | {"limit", "cursor"}:
        raise _invalid("partner.accounting.search contains an unsupported parameter.")

    role = parameters.get("role", "both")
    if not isinstance(role, str) or role not in _ROLES:
        raise _invalid("parameters.role must be 'both', 'customer', or 'vendor'.")

    query = parameters.get("query")
    if query is not None and (
        not isinstance(query, str)
        or not 1 <= len(query) <= 200
        or query != query.strip()
    ):
        raise _invalid(
            "parameters.query must be null or a trimmed 1-200 character string."
        )

    limit = parameters.get("limit", DEFAULT_LIMIT)
    if not _is_integer(limit) or not 1 <= limit <= MAX_LIMIT:
        raise _invalid(f"parameters.limit must be between 1 and {MAX_LIMIT}.")
    cursor = parameters.get("cursor")
    if cursor is not None and (
        not isinstance(cursor, str) or not cursor or len(cursor) > 4096
    ):
        raise _invalid("parameters.cursor must be null or a non-empty cursor string.")

    return request_id, context, {"role": role, "query": query}, limit, cursor


def _encode_cursor(
    after: list[Any], *, context: dict[str, Any], filters: dict[str, Any]
) -> str:
    payload = json.dumps(
        {
            "after": after,
            "capability": CAPABILITY_ID,
            "company_id": context["company_id"],
            "database": context["database"],
            "filters": filters,
            "user_login": context["user_login"],
            "version": _CURSOR_VERSION,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def _decode_cursor(
    cursor: str, *, context: dict[str, Any], filters: dict[str, Any]
) -> list[Any]:
    try:
        padding = "=" * (-len(cursor) % 4)
        raw = base64.b64decode(
            (cursor + padding).encode("ascii"), altchars=b"-_", validate=True
        )
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_pairs,
            parse_float=_reject_json_float,
            parse_constant=_reject_json_constant,
        )
    except (ValueError, UnicodeError, json.JSONDecodeError, binascii.Error) as exc:
        raise _invalid("The cursor is invalid.", code="invalid_cursor") from exc

    if not isinstance(value, dict) or set(value) != {
        "after",
        "capability",
        "company_id",
        "database",
        "filters",
        "user_login",
        "version",
    }:
        raise _invalid("The cursor is invalid.", code="invalid_cursor")
    after = value["after"]
    try:
        cursor_filters = _canonical_json(value["filters"])
        request_filters = _canonical_json(filters)
    except (TypeError, ValueError) as exc:
        raise _invalid("The cursor is invalid.", code="invalid_cursor") from exc
    if (
        value["capability"] != CAPABILITY_ID
        or not _is_integer(value["version"])
        or value["version"] != _CURSOR_VERSION
        or not _valid_id(value["company_id"])
        or value["company_id"] != context["company_id"]
        or value["database"] != context["database"]
        or value["user_login"] != context["user_login"]
        or cursor_filters != request_filters
        or not isinstance(after, list)
        or len(after) != 2
        or not _is_nonempty_string(after[0])
        or not _valid_id(after[1])
    ):
        raise _invalid("The cursor does not match this request.", code="invalid_cursor")
    return after


def _valid_account(value: Any) -> bool:
    return value is None or (
        isinstance(value, dict)
        and set(value) == {"id", "code", "name"}
        and _valid_id(value["id"])
        and _is_nonempty_string(value["code"])
        and _is_nonempty_string(value["name"])
    )


def _matches_role(row: dict[str, Any], role: str) -> bool:
    if role == "customer":
        return row["customer_rank"] > 0
    if role == "vendor":
        return row["supplier_rank"] > 0
    return row["customer_rank"] > 0 or row["supplier_rank"] > 0


def _valid_row(row: Any, *, company_id: int, role: str) -> bool:
    if not isinstance(row, dict) or set(row) != _ROW_FIELDS:
        return False
    row_company_id = row["company_id"]
    return (
        _valid_id(row["id"])
        and _is_nonempty_string(row["complete_name"])
        and _valid_optional_string(row["ref"])
        and isinstance(row["active"], bool)
        and isinstance(row["is_company"], bool)
        and (
            row_company_id is None
            or (_valid_id(row_company_id) and row_company_id == company_id)
        )
        and _is_integer(row["customer_rank"])
        and row["customer_rank"] >= 0
        and _is_integer(row["supplier_rank"])
        and row["supplier_rank"] >= 0
        and _matches_role(row, role)
        and _valid_account(row["receivable_account"])
        and _valid_account(row["payable_account"])
    )


def _validate_rows(
    rows: Any,
    *,
    company_id: int,
    role: str,
    after: list[Any] | None,
    maximum: int,
) -> list[dict[str, Any]]:
    if not isinstance(rows, list) or len(rows) > maximum:
        raise _failed("Odoo returned an invalid accounting-partner search page.")
    previous = tuple(after) if after is not None else None
    record_ids: set[int] = set()
    result: list[dict[str, Any]] = []
    for row in rows:
        if not _valid_row(row, company_id=company_id, role=role):
            raise _failed(
                "Odoo returned an invalid or out-of-scope accounting partner."
            )
        current = (row["complete_name"], row["id"])
        if row["id"] in record_ids or (previous is not None and current <= previous):
            raise _failed("Odoo returned accounting partners in an unstable order.")
        record_ids.add(row["id"])
        previous = current
        result.append(dict(row))
    return result


def _validate_page(port: PartnerAccountingPort, page: Any) -> list[dict[str, Any]]:
    if not isinstance(page, dict) or set(page) != {
        "user_id",
        "company_visible",
        "module_installed",
        "access_allowed",
        "rows",
    }:
        raise _failed("Odoo returned an invalid accounting-partner page.")
    if (
        not _valid_id(page["user_id"])
        or not _valid_id(port.user_id)
        or page["user_id"] != port.user_id
        or not isinstance(page["company_visible"], bool)
        or not isinstance(page["module_installed"], bool)
        or not isinstance(page["access_allowed"], bool)
        or not isinstance(page["rows"], list)
        or (
            page["access_allowed"]
            and not (page["company_visible"] and page["module_installed"])
        )
        or (not page["access_allowed"] and bool(page["rows"]))
    ):
        raise _failed("Odoo returned an invalid accounting-partner page.")
    if not page["company_visible"]:
        raise PartnerAccountingError(
            "company_unavailable",
            "The requested company is unavailable to the configured user.",
            exit_code=3,
        )
    if not page["module_installed"]:
        raise PartnerAccountingError(
            "uninstalled",
            "The accounting-partner capability is not installed in this database.",
            exit_code=4,
        )
    if not page["access_allowed"]:
        raise PartnerAccountingError(
            "unauthorized",
            "The configured user cannot read accounting partners.",
            exit_code=3,
        )
    return page["rows"]


def search_accounting_partners(
    port: PartnerAccountingPort, request: dict[str, Any]
) -> dict[str, Any]:
    """Read one verified partner page in complete-name/id ascending order."""

    _, context, filters, limit, cursor = validate_partner_accounting_search_request(
        request
    )
    after = _decode_cursor(cursor, context=context, filters=filters) if cursor else None
    fetch_limit = limit + 1
    page = port.search_page(
        company_id=context["company_id"],
        after=after,
        limit=fetch_limit,
        filters=filters,
    )
    records = _validate_rows(
        _validate_page(port, page),
        company_id=context["company_id"],
        role=filters["role"],
        after=after,
        maximum=fetch_limit,
    )
    has_more = len(records) > limit
    items = records[:limit]
    next_cursor = None
    if has_more and items:
        next_cursor = _encode_cursor(
            [items[-1]["complete_name"], items[-1]["id"]],
            context=context,
            filters=filters,
        )
    return {"items": items, "has_more": has_more, "next_cursor": next_cursor}
