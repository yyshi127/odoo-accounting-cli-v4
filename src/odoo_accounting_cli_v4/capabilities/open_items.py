"""Strict contracts for company-scoped receivable and payable open items."""

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


RECEIVABLE_CAPABILITY_ID = "receivable.open_items.list"
PAYABLE_CAPABILITY_ID = "payable.open_items.list"
DEFAULT_LIMIT = 100
MAX_LIMIT = 1000
_CURSOR_VERSION = 1
_DECIMAL_PATTERN = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
_CAPABILITY_SIDES = {
    RECEIVABLE_CAPABILITY_ID: "receivable",
    PAYABLE_CAPABILITY_ID: "payable",
}
_SIDE_ACCOUNT_TYPES = {
    "receivable": "asset_receivable",
    "payable": "liability_payable",
}
_MOVE_TYPES = frozenset(
    {
        "entry",
        "out_invoice",
        "out_refund",
        "in_invoice",
        "in_refund",
        "out_receipt",
        "in_receipt",
    }
)
_FILTER_FIELDS = frozenset(
    {
        "date_from",
        "date_to",
        "due_date_from",
        "due_date_to",
        "partner_id",
        "account_id",
        "journal_id",
        "currency_id",
        "query",
    }
)
_ROW_FIELDS = frozenset(
    {
        "id",
        "side",
        "date",
        "due_date",
        "name",
        "ref",
        "move",
        "journal",
        "company_id",
        "partner",
        "account",
        "currency",
        "company_currency",
        "debit",
        "credit",
        "balance",
        "amount_currency",
        "amount_residual",
        "amount_residual_currency",
        "reconciled",
        "matching_number",
    }
)
_MONEY_FIELDS = (
    "debit",
    "credit",
    "balance",
    "amount_currency",
    "amount_residual",
    "amount_residual_currency",
)


class OpenItemsPort(Protocol):
    """Narrow bridge port for one fixed open-items side."""

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


class OpenItemsError(RuntimeError):
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


def _is_nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and len(value) > 0


def _valid_optional_string(value: Any) -> bool:
    return value is None or (isinstance(value, str) and len(value) >= 1)


def _is_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return False
    return parsed.isoformat() == value


def _is_decimal_string(value: Any) -> bool:
    if not isinstance(value, str) or _DECIMAL_PATTERN.fullmatch(value) is None:
        return False
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        return False
    return parsed.is_finite()


def _invalid(message: str, *, code: str = "invalid_request") -> OpenItemsError:
    return OpenItemsError(code, message, exit_code=2)


def _failed(message: str) -> OpenItemsError:
    return OpenItemsError("failed_validation", message, exit_code=8)


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


def _validate_request(
    request: Any, capability_id: str
) -> tuple[str, dict[str, Any], dict[str, Any], int, str | None]:
    request_id, context, parameters = _validate_envelope(request)
    if not set(parameters) <= _FILTER_FIELDS | {"limit", "cursor"}:
        raise _invalid(f"{capability_id} contains an unsupported parameter.")

    dates: dict[str, str | None] = {}
    for key in ("date_from", "date_to", "due_date_from", "due_date_to"):
        value = parameters.get(key)
        if value is not None and not _is_date(value):
            raise _invalid(f"parameters.{key} must be null or a YYYY-MM-DD date.")
        dates[key] = value
    if (
        dates["date_from"] is not None
        and dates["date_to"] is not None
        and dates["date_from"] > dates["date_to"]
    ):
        raise _invalid("parameters.date_from cannot be after parameters.date_to.")
    if (
        dates["due_date_from"] is not None
        and dates["due_date_to"] is not None
        and dates["due_date_from"] > dates["due_date_to"]
    ):
        raise _invalid(
            "parameters.due_date_from cannot be after parameters.due_date_to."
        )

    ids: dict[str, int | None] = {}
    for key in ("partner_id", "account_id", "journal_id", "currency_id"):
        value = parameters.get(key)
        if value is not None and not _valid_id(value):
            raise _invalid(f"parameters.{key} must be null or a positive integer.")
        ids[key] = value
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

    filters = {
        "date_from": dates["date_from"],
        "date_to": dates["date_to"],
        "due_date_from": dates["due_date_from"],
        "due_date_to": dates["due_date_to"],
        "partner_id": ids["partner_id"],
        "account_id": ids["account_id"],
        "journal_id": ids["journal_id"],
        "currency_id": ids["currency_id"],
        "query": query,
    }
    return request_id, context, filters, limit, cursor


def validate_receivable_open_items_list_request(
    request: Any,
) -> tuple[str, dict[str, Any], dict[str, Any], int, str | None]:
    return _validate_request(request, RECEIVABLE_CAPABILITY_ID)


def validate_payable_open_items_list_request(
    request: Any,
) -> tuple[str, dict[str, Any], dict[str, Any], int, str | None]:
    return _validate_request(request, PAYABLE_CAPABILITY_ID)


def _encode_cursor(
    after: list[Any],
    *,
    capability_id: str,
    context: dict[str, Any],
    filters: dict[str, Any],
) -> str:
    payload = json.dumps(
        {
            "after": after,
            "binding": _cursor_binding(capability_id, context, filters),
            "version": _CURSOR_VERSION,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def _cursor_binding(
    capability_id: str, context: dict[str, Any], filters: dict[str, Any]
) -> str:
    value = {
        "capability": capability_id,
        "company_id": context["company_id"],
        "database": context["database"],
        "filters": filters,
        "user_login": context["user_login"],
    }
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _decode_cursor(
    cursor: str,
    *,
    capability_id: str,
    context: dict[str, Any],
    filters: dict[str, Any],
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
        "binding",
        "version",
    }:
        raise _invalid("The cursor is invalid.", code="invalid_cursor")
    after = value["after"]
    if (
        not _is_integer(value["version"])
        or value["version"] != _CURSOR_VERSION
        or not isinstance(value["binding"], str)
        or value["binding"] != _cursor_binding(capability_id, context, filters)
        or not isinstance(after, list)
        or len(after) != 2
        or not _is_date(after[0])
        or not _valid_id(after[1])
    ):
        raise _invalid("The cursor does not match this request.", code="invalid_cursor")
    return after


def _valid_currency(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "code"}
        and _valid_id(value["id"])
        and _is_nonempty_text(value["code"])
        and len(value["code"]) <= 3
    )


def _valid_move(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "name", "move_type", "state"}
        and _valid_id(value["id"])
        and _is_nonempty_text(value["name"])
        and value["move_type"] in _MOVE_TYPES
        and value["state"] == "posted"
    )


def _valid_journal(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "code", "name"}
        and _valid_id(value["id"])
        and _is_nonempty_text(value["code"])
        and len(value["code"]) <= 5
        and _is_nonempty_text(value["name"])
    )


def _valid_partner(value: Any) -> bool:
    return value is None or (
        isinstance(value, dict)
        and set(value) == {"id", "name", "reference"}
        and _valid_id(value["id"])
        and _valid_optional_string(value["name"])
        and _valid_optional_string(value["reference"])
    )


def _valid_account(value: Any, side: str) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "code", "name", "account_type", "non_trade"}
        and _valid_id(value["id"])
        and _is_nonempty_text(value["code"])
        and _is_nonempty_text(value["name"])
        and value["account_type"] == _SIDE_ACCOUNT_TYPES[side]
        and isinstance(value["non_trade"], bool)
    )


def _matches_ilike(value: str | None, query: str) -> bool:
    if not value:
        return False
    pattern: list[str] = []
    escaped = False
    for char in f"%{query.lower()}%":
        if escaped:
            escaped = False
            pattern.append(re.escape(char))
        elif char == "\\":
            escaped = True
        elif char == "%":
            pattern.append(".*")
        elif char == "_":
            pattern.append(".")
        else:
            pattern.append(re.escape(char))
    return re.compile("".join(pattern), flags=re.DOTALL).fullmatch(value.lower()) is not None


def _valid_row(row: Any, *, company_id: int, side: str) -> bool:
    if not isinstance(row, dict) or set(row) != _ROW_FIELDS:
        return False
    if (
        not _valid_id(row["id"])
        or row["side"] != side
        or not _is_date(row["date"])
        or not (row["due_date"] is None or _is_date(row["due_date"]))
        or not _valid_optional_string(row["name"])
        or not _valid_optional_string(row["ref"])
        or not _valid_move(row["move"])
        or not _valid_journal(row["journal"])
        or row["company_id"] != company_id
        or not _valid_partner(row["partner"])
        or not _valid_account(row["account"], side)
        or not _valid_currency(row["currency"])
        or not _valid_currency(row["company_currency"])
        or not all(_is_decimal_string(row[field]) for field in _MONEY_FIELDS)
        or row["reconciled"] is not False
        or not _valid_optional_string(row["matching_number"])
    ):
        return False
    debit = Decimal(row["debit"])
    credit = Decimal(row["credit"])
    balance = Decimal(row["balance"])
    amount_currency = Decimal(row["amount_currency"])
    residual = Decimal(row["amount_residual"])
    residual_currency = Decimal(row["amount_residual_currency"])
    same_currency = row["currency"] == row["company_currency"]

    def bounded_in_original_direction(remainder: Decimal, original: Decimal) -> bool:
        if remainder == 0:
            return True
        return (
            original != 0
            and (remainder > 0) == (original > 0)
            and abs(remainder) <= abs(original)
        )

    return (
        debit - credit == balance
        and debit * credit == 0
        and not (
            balance != 0
            and amount_currency != 0
            and (balance > 0) != (amount_currency > 0)
        )
        and not (residual == 0 and residual_currency == 0)
        and bounded_in_original_direction(residual, balance)
        and bounded_in_original_direction(residual_currency, amount_currency)
        and not (
            row["currency"]["id"] == row["company_currency"]["id"]
            and row["currency"] != row["company_currency"]
        )
        and (not same_currency or amount_currency == balance)
        and (not same_currency or residual_currency == residual)
    )


def _matches_filters(row: dict[str, Any], filters: dict[str, Any]) -> bool:
    partner = row["partner"]
    if (
        (filters["date_from"] is not None and row["date"] < filters["date_from"])
        or (filters["date_to"] is not None and row["date"] > filters["date_to"])
        or (
            filters["due_date_from"] is not None
            and (row["due_date"] is None or row["due_date"] < filters["due_date_from"])
        )
        or (
            filters["due_date_to"] is not None
            and (row["due_date"] is None or row["due_date"] > filters["due_date_to"])
        )
        or (
            filters["partner_id"] is not None
            and (partner is None or partner["id"] != filters["partner_id"])
        )
        or (
            filters["account_id"] is not None
            and row["account"]["id"] != filters["account_id"]
        )
        or (
            filters["journal_id"] is not None
            and row["journal"]["id"] != filters["journal_id"]
        )
        or (
            filters["currency_id"] is not None
            and row["currency"]["id"] != filters["currency_id"]
        )
    ):
        return False
    query = filters["query"]
    return query is None or any(
        _matches_ilike(value, query)
        for value in (
            row["move"]["name"],
            row["ref"],
            row["name"],
            partner["name"] if partner is not None else None,
        )
    )


def _validate_page(port: OpenItemsPort, page: Any) -> list[dict[str, Any]]:
    if not isinstance(page, dict) or set(page) != {
        "user_id",
        "company_visible",
        "module_installed",
        "access_allowed",
        "rows",
    }:
        raise _failed("Odoo returned an invalid open-items page.")
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
        raise _failed("Odoo returned an invalid open-items page.")
    if not page["company_visible"]:
        raise OpenItemsError(
            "company_unavailable",
            "The requested company is unavailable to the configured user.",
            exit_code=3,
        )
    if not page["module_installed"]:
        raise OpenItemsError(
            "uninstalled",
            "The open-items capability is not installed in this database.",
            exit_code=4,
        )
    if not page["access_allowed"]:
        raise OpenItemsError(
            "unauthorized",
            "The configured user cannot read open items.",
            exit_code=3,
        )
    return page["rows"]


def _validate_rows(
    rows: Any,
    *,
    company_id: int,
    side: str,
    after: list[Any] | None,
    filters: dict[str, Any],
    maximum: int,
) -> list[dict[str, Any]]:
    if not isinstance(rows, list) or len(rows) > maximum:
        raise _failed("Odoo returned an invalid open-items search page.")
    previous = tuple(after) if after is not None else None
    record_ids: set[int] = set()
    result: list[dict[str, Any]] = []
    for row in rows:
        if not _valid_row(row, company_id=company_id, side=side) or not _matches_filters(
            row, filters
        ):
            raise _failed("Odoo returned an invalid or out-of-scope open item.")
        current = (row["date"], row["id"])
        if row["id"] in record_ids or (previous is not None and current >= previous):
            raise _failed("Odoo returned open items in an unstable order.")
        record_ids.add(row["id"])
        previous = current
        result.append(dict(row))
    return result


def _search_open_items(
    port: OpenItemsPort, request: dict[str, Any], capability_id: str
) -> dict[str, Any]:
    _, context, filters, limit, cursor = _validate_request(request, capability_id)
    after = (
        _decode_cursor(
            cursor,
            capability_id=capability_id,
            context=context,
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
        raise _failed("The Odoo bridge returned an invalid open-items page.") from exc
    records = _validate_rows(
        _validate_page(port, page),
        company_id=context["company_id"],
        side=_CAPABILITY_SIDES[capability_id],
        after=after,
        filters=filters,
        maximum=fetch_limit,
    )
    has_more = len(records) > limit
    items = records[:limit]
    next_cursor = None
    if has_more and items:
        next_cursor = _encode_cursor(
            [items[-1]["date"], items[-1]["id"]],
            capability_id=capability_id,
            context=context,
            filters=filters,
        )
    return {"items": items, "has_more": has_more, "next_cursor": next_cursor}


def search_receivable_open_items(
    port: OpenItemsPort, request: dict[str, Any]
) -> dict[str, Any]:
    """Read one verified page of posted, unreconciled receivable items."""

    return _search_open_items(port, request, RECEIVABLE_CAPABILITY_ID)


def search_payable_open_items(
    port: OpenItemsPort, request: dict[str, Any]
) -> dict[str, Any]:
    """Read one verified page of posted, unreconciled payable items."""

    return _search_open_items(port, request, PAYABLE_CAPABILITY_ID)
