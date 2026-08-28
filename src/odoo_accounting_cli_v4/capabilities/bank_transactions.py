"""Strict read contract for company-scoped bank transactions."""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
import uuid
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol

CAPABILITY_ID = "bank.transaction.list"
SEARCH_CAPABILITY_ID = "bank.transaction.search"
DEFAULT_LIMIT = 100
MAX_LIMIT = 1000
_CURSOR_VERSION = 1
_DECIMAL_PATTERN = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
_ROW_FIELDS = frozenset(
    {
        "id",
        "company_id",
        "date",
        "payment_date",
        "name",
        "reference",
        "partner",
        "journal",
        "amount",
        "currency",
        "move",
        "reconciled",
    }
)
_MOVE_STATES = frozenset({"draft", "posted", "cancel"})


class BankTransactionListPort(Protocol):
    @property
    def user_id(self) -> int: ...

    def search_page(
        self,
        *,
        company_id: int,
        after: list[Any] | None,
        limit: int,
    ) -> dict[str, Any]: ...


class BankTransactionSearchPort(Protocol):
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


class BankTransactionListError(RuntimeError):
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


def _invalid(
    message: str, *, code: str = "invalid_request"
) -> BankTransactionListError:
    return BankTransactionListError(code, message, exit_code=2)


def _failed(message: str) -> BankTransactionListError:
    return BankTransactionListError("failed_validation", message, exit_code=8)


def _is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _valid_id(value: Any) -> bool:
    return _is_integer(value) and value > 0


def _is_context_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_text(value: Any) -> bool:
    return isinstance(value, str) and len(value) > 0


def _is_nullable_text(value: Any) -> bool:
    return value is None or _is_text(value)


def _is_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return False
    return parsed.isoformat() == value


def _is_decimal(value: Any) -> bool:
    if (
        not isinstance(value, str)
        or len(value) > 256
        or _DECIMAL_PATTERN.fullmatch(value) is None
    ):
        return False
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        return False
    return parsed.is_finite()


def validate_bank_transaction_list_request(
    request: Any,
) -> tuple[str, dict[str, Any], int, str | None]:
    """Validate and normalize the closed bank-transaction list request."""

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
        if not _is_context_text(context[key]):
            raise _invalid(f"context.{key} must be a non-empty string.")
    if not _valid_id(context["company_id"]):
        raise _invalid("context.company_id must be a positive integer.")

    parameters = request["parameters"]
    if not isinstance(parameters, dict) or not set(parameters) <= {
        "limit",
        "cursor",
    }:
        raise _invalid(f"{CAPABILITY_ID} contains an unsupported parameter.")
    limit = parameters.get("limit", DEFAULT_LIMIT)
    if not _is_integer(limit) or not 1 <= limit <= MAX_LIMIT:
        raise _invalid(f"parameters.limit must be between 1 and {MAX_LIMIT}.")
    cursor = parameters.get("cursor")
    if cursor is not None and (
        not isinstance(cursor, str) or not cursor or len(cursor) > 4096
    ):
        raise _invalid("parameters.cursor must be null or a non-empty cursor string.")
    return request_id, context, limit, cursor


def validate_bank_transaction_search_request(
    request: Any,
) -> tuple[str, dict[str, Any], dict[str, Any], int, str | None]:
    """Validate and normalize the closed bank-transaction search request."""

    if not isinstance(request, dict) or set(request) != {
        "schema_version",
        "request_id",
        "context",
        "parameters",
    }:
        raise _invalid("The request must match the v1 request envelope.")
    request_id, context, _, _ = validate_bank_transaction_list_request(
        {**request, "parameters": {}}
    )
    parameters = request["parameters"]
    allowed = {
        "date_from",
        "date_to",
        "journal_id",
        "partner_id",
        "reconciled",
        "query",
        "limit",
        "cursor",
    }
    if not isinstance(parameters, dict) or not set(parameters) <= allowed:
        raise _invalid(f"{SEARCH_CAPABILITY_ID} contains an unsupported parameter.")
    limit = parameters.get("limit", DEFAULT_LIMIT)
    if not _is_integer(limit) or not 1 <= limit <= MAX_LIMIT:
        raise _invalid(f"parameters.limit must be between 1 and {MAX_LIMIT}.")
    cursor = parameters.get("cursor")
    if cursor is not None and (
        not isinstance(cursor, str) or not cursor or len(cursor) > 4096
    ):
        raise _invalid("parameters.cursor must be null or a non-empty cursor string.")
    date_from = parameters.get("date_from")
    date_to = parameters.get("date_to")
    if date_from is not None and not _is_date(date_from):
        raise _invalid("parameters.date_from must be null or a YYYY-MM-DD date.")
    if date_to is not None and not _is_date(date_to):
        raise _invalid("parameters.date_to must be null or a YYYY-MM-DD date.")
    if date_from is not None and date_to is not None and date_from > date_to:
        raise _invalid("parameters.date_from cannot be after parameters.date_to.")
    identifiers: dict[str, int | None] = {}
    for field in ("journal_id", "partner_id"):
        value = parameters.get(field)
        if value is not None and not _valid_id(value):
            raise _invalid(f"parameters.{field} must be null or a positive integer.")
        identifiers[field] = value
    reconciled = parameters.get("reconciled")
    if reconciled is not None and not isinstance(reconciled, bool):
        raise _invalid("parameters.reconciled must be null or a boolean.")
    query = parameters.get("query")
    if query is not None and (
        not isinstance(query, str)
        or query != query.strip()
        or not 1 <= len(query) <= 200
    ):
        raise _invalid("parameters.query must be a trimmed 1-200 character string.")
    filters = {
        "date_from": date_from,
        "date_to": date_to,
        "journal_id": identifiers["journal_id"],
        "partner_id": identifiers["partner_id"],
        "reconciled": reconciled,
        "query": query,
    }
    return request_id, context, filters, limit, cursor


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate cursor key")
        result[key] = value
    return result


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


def _cursor_binding(
    context: dict[str, Any],
    *,
    capability_id: str = CAPABILITY_ID,
    filters: dict[str, Any] | None = None,
) -> str:
    value = {
        "capability": capability_id,
        "company_id": context["company_id"],
        "database": context["database"],
        "user_login": context["user_login"],
    }
    if filters is not None:
        value["filters"] = filters
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _encode_cursor(
    after: list[Any],
    *,
    context: dict[str, Any],
    capability_id: str = CAPABILITY_ID,
    filters: dict[str, Any] | None = None,
) -> str:
    payload = _canonical_json(
        {
            "after": after,
            "binding": _cursor_binding(
                context, capability_id=capability_id, filters=filters
            ),
            "version": _CURSOR_VERSION,
        }
    ).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def _decode_cursor(
    cursor: str,
    *,
    context: dict[str, Any],
    capability_id: str = CAPABILITY_ID,
    filters: dict[str, Any] | None = None,
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
    if (
        not isinstance(value, dict)
        or set(value) != {"after", "binding", "version"}
        or not _is_integer(value["version"])
        or value["version"] != _CURSOR_VERSION
        or value["binding"]
        != _cursor_binding(context, capability_id=capability_id, filters=filters)
        or not isinstance(value["after"], list)
        or len(value["after"]) != 2
        or not _is_date(value["after"][0])
        or not _valid_id(value["after"][1])
    ):
        raise _invalid("The cursor does not match this request.", code="invalid_cursor")
    return value["after"]


def _valid_currency(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "code"}
        and _valid_id(value["id"])
        and _is_text(value["code"])
        and len(value["code"]) <= 3
    )


def _valid_partner(value: Any) -> bool:
    return value is None or (
        isinstance(value, dict)
        and set(value) == {"id", "name"}
        and _valid_id(value["id"])
        and _is_text(value["name"])
    )


def _valid_journal(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "code", "name"}
        and _valid_id(value["id"])
        and _is_text(value["code"])
        and len(value["code"]) <= 5
        and _is_text(value["name"])
    )


def _valid_move(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "name", "state"}
        and _valid_id(value["id"])
        and _is_text(value["name"])
        and value["state"] in _MOVE_STATES
    )


def _valid_row(row: Any, *, company_id: int) -> bool:
    return (
        isinstance(row, dict)
        and set(row) == _ROW_FIELDS
        and _valid_id(row["id"])
        and row["company_id"] == company_id
        and _is_date(row["date"])
        and (row["payment_date"] is None or _is_date(row["payment_date"]))
        and _is_nullable_text(row["name"])
        and _is_nullable_text(row["reference"])
        and _valid_partner(row["partner"])
        and _valid_journal(row["journal"])
        and _is_decimal(row["amount"])
        and _valid_currency(row["currency"])
        and _valid_move(row["move"])
        and isinstance(row["reconciled"], bool)
    )


def _validate_page(port: BankTransactionListPort, page: Any) -> list[dict[str, Any]]:
    if not isinstance(page, dict) or set(page) != {
        "user_id",
        "company_visible",
        "module_installed",
        "access_allowed",
        "rows",
    }:
        raise _failed("Odoo returned an invalid bank-transaction page.")
    try:
        port_user_id = port.user_id
    except ValueError as exc:
        raise _failed("Odoo returned an invalid bank-transaction page.") from exc
    if (
        not _valid_id(page["user_id"])
        or not _valid_id(port_user_id)
        or page["user_id"] != port_user_id
        or not isinstance(page["company_visible"], bool)
        or not isinstance(page["module_installed"], bool)
        or not isinstance(page["access_allowed"], bool)
        or not isinstance(page["rows"], list)
        or (page["access_allowed"] and not page["module_installed"])
        or (
            bool(page["rows"])
            and not (
                page["company_visible"]
                and page["module_installed"]
                and page["access_allowed"]
            )
        )
    ):
        raise _failed("Odoo returned an invalid bank-transaction page.")
    if not page["module_installed"]:
        raise BankTransactionListError(
            "uninstalled",
            "The bank-transaction model is unavailable in this database.",
            exit_code=4,
        )
    if not page["access_allowed"]:
        raise BankTransactionListError(
            "unauthorized",
            "The configured user cannot read bank transactions.",
            exit_code=3,
        )
    if not page["company_visible"]:
        raise BankTransactionListError(
            "company_unavailable",
            "The requested company is unavailable to the configured user.",
            exit_code=3,
        )
    return page["rows"]


def _validate_rows(
    rows: Any,
    *,
    company_id: int,
    after: list[Any] | None,
    maximum: int,
) -> list[dict[str, Any]]:
    if not isinstance(rows, list) or len(rows) > maximum:
        raise _failed("Odoo returned an invalid bank-transaction page.")
    previous = tuple(after) if after is not None else None
    record_ids: set[int] = set()
    result: list[dict[str, Any]] = []
    for row in rows:
        if not _valid_row(row, company_id=company_id):
            raise _failed("Odoo returned an invalid or out-of-scope bank transaction.")
        current = (row["date"], row["id"])
        if row["id"] in record_ids or (previous is not None and current >= previous):
            raise _failed("Odoo returned bank transactions in an unstable order.")
        record_ids.add(row["id"])
        previous = current
        result.append(dict(row))
    return result


def list_bank_transactions(
    port: BankTransactionListPort, request: dict[str, Any]
) -> dict[str, Any]:
    """Read one verified date/id-descending bank-transaction page."""

    _, context, limit, cursor = validate_bank_transaction_list_request(request)
    after = _decode_cursor(cursor, context=context) if cursor else None
    fetch_limit = limit + 1
    try:
        page = port.search_page(
            company_id=context["company_id"],
            after=after,
            limit=fetch_limit,
        )
    except ValueError as exc:
        raise _failed(
            "The Odoo bridge returned an invalid bank-transaction page."
        ) from exc
    records = _validate_rows(
        _validate_page(port, page),
        company_id=context["company_id"],
        after=after,
        maximum=fetch_limit,
    )
    has_more = len(records) > limit
    items = records[:limit]
    next_cursor = None
    if has_more and items:
        next_cursor = _encode_cursor(
            [items[-1]["date"], items[-1]["id"]], context=context
        )
    return {"items": items, "has_more": has_more, "next_cursor": next_cursor}


def search_bank_transactions(
    port: BankTransactionSearchPort, request: dict[str, Any]
) -> dict[str, Any]:
    """Read one verified filter-bound bank-transaction page."""

    _, context, filters, limit, cursor = validate_bank_transaction_search_request(
        request
    )
    after = (
        _decode_cursor(
            cursor,
            context=context,
            capability_id=SEARCH_CAPABILITY_ID,
            filters=filters,
        )
        if cursor
        else None
    )
    fetch_limit = limit + 1
    try:
        page = port.search_page(
            company_id=context["company_id"],
            after=after,
            limit=fetch_limit,
            filters=filters,
        )
    except ValueError as exc:
        raise _failed(
            "The Odoo bridge returned an invalid bank-transaction page."
        ) from exc
    records = _validate_rows(
        _validate_page(port, page),
        company_id=context["company_id"],
        after=after,
        maximum=fetch_limit,
    )
    for row in records:
        if (
            (filters["date_from"] is not None and row["date"] < filters["date_from"])
            or (filters["date_to"] is not None and row["date"] > filters["date_to"])
            or (
                filters["journal_id"] is not None
                and row["journal"]["id"] != filters["journal_id"]
            )
            or (
                filters["partner_id"] is not None
                and (
                    row["partner"] is None
                    or row["partner"]["id"] != filters["partner_id"]
                )
            )
            or (
                filters["reconciled"] is not None
                and row["reconciled"] is not filters["reconciled"]
            )
        ):
            raise _failed("Odoo returned a bank transaction outside the filters.")
    has_more = len(records) > limit
    items = records[:limit]
    next_cursor = None
    if has_more and items:
        next_cursor = _encode_cursor(
            [items[-1]["date"], items[-1]["id"]],
            context=context,
            capability_id=SEARCH_CAPABILITY_ID,
            filters=filters,
        )
    return {"items": items, "has_more": has_more, "next_cursor": next_cursor}
