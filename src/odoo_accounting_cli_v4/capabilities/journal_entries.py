"""Strict contracts for company-scoped general journal entry reads."""

from __future__ import annotations

import base64
import binascii
import json
import re
import uuid
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol

SEARCH_CAPABILITY_ID = "journal_entry.search"
GET_CAPABILITY_ID = "journal_entry.get"
CHECK_CAPABILITY_ID = "validation.journal_entry.check"
DEFAULT_LIMIT = 100
MAX_LIMIT = 1000
_CURSOR_VERSION = 1
_DECIMAL_PATTERN = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
_STATE_ORDER = ("draft", "posted", "cancel")
_NON_ACCOUNTABLE_DISPLAY_TYPES = frozenset(
    {"line_section", "line_subsection", "line_note"}
)
_DISPLAY_TYPES = frozenset(
    {
        "product",
        "cogs",
        "tax",
        "discount",
        "rounding",
        "payment_term",
        "line_section",
        "line_subsection",
        "line_note",
        "epd",
        "non_deductible_product_total",
        "non_deductible_product",
        "non_deductible_tax",
    }
)
_FILTER_FIELDS = frozenset(
    {"date_from", "date_to", "states", "journal_id", "partner_id", "query"}
)
_SEARCH_FIELDS = frozenset(
    {
        "id",
        "name",
        "date",
        "state",
        "ref",
        "journal",
        "company_id",
        "currency",
        "partner",
        "debit",
        "credit",
        "balance",
    }
)
_ENTRY_FIELDS = frozenset(
    {
        "id",
        "name",
        "date",
        "state",
        "ref",
        "journal",
        "company_id",
        "currency",
        "partner",
        "lines",
        "totals",
    }
)
_LINE_FIELDS = frozenset(
    {
        "id",
        "sequence",
        "display_type",
        "name",
        "account",
        "partner",
        "debit",
        "credit",
        "balance",
        "company_currency",
        "amount_currency",
        "currency",
        "date_maturity",
        "reconciled",
        "matching_number",
    }
)


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate cursor key")
        value[key] = item
    return value


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


class JournalEntryPort(Protocol):
    """Narrow bridge port for fixed journal-entry reads and preflight checks."""

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

    def get_entry(self, *, company_id: int, entry_id: int) -> dict[str, Any]: ...

    def check_entry(self, *, company_id: int, entry_id: int) -> dict[str, Any]: ...


class JournalEntryError(RuntimeError):
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


def _invalid(message: str, *, code: str = "invalid_request") -> JournalEntryError:
    return JournalEntryError(code, message, exit_code=2)


def _failed(message: str) -> JournalEntryError:
    return JournalEntryError("failed_validation", message, exit_code=8)


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


def validate_journal_entry_search_request(
    request: Any,
) -> tuple[str, dict[str, Any], dict[str, Any], int, str | None]:
    """Validate and normalize the closed search request."""

    request_id, context, parameters = _validate_envelope(request)
    if not set(parameters) <= _FILTER_FIELDS | {"limit", "cursor"}:
        raise _invalid("journal_entry.search contains an unsupported parameter.")
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

    if "states" not in parameters:
        normalized_states: list[str] = []
    else:
        states = parameters["states"]
        if (
            not isinstance(states, list)
            or not 1 <= len(states) <= len(_STATE_ORDER)
            or any(not isinstance(state, str) for state in states)
            or len(states) != len(set(states))
            or any(state not in _STATE_ORDER for state in states)
        ):
            raise _invalid("parameters.states must contain one to three unique states.")
        normalized_states = [state for state in _STATE_ORDER if state in states]

    ids: dict[str, int | None] = {}
    for key in ("journal_id", "partner_id"):
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
    filters = {
        "date_from": date_from,
        "date_to": date_to,
        "states": normalized_states,
        "journal_id": ids["journal_id"],
        "partner_id": ids["partner_id"],
        "query": query,
    }
    return request_id, context, filters, limit, cursor


def validate_journal_entry_get_request(
    request: Any,
) -> tuple[str, dict[str, Any], int]:
    """Validate the closed get request."""

    request_id, context, parameters = _validate_envelope(request)
    if set(parameters) != {"entry_id"} or not _valid_id(parameters["entry_id"]):
        raise _invalid("parameters must contain one positive integer entry_id.")
    return request_id, context, parameters["entry_id"]


def validate_journal_entry_check_request(
    request: Any,
) -> tuple[str, dict[str, Any], int]:
    """Validate the closed journal-entry readiness request."""

    return validate_journal_entry_get_request(request)


def _encode_cursor(
    after: list[Any], *, context: dict[str, Any], filters: dict[str, Any]
) -> str:
    payload = json.dumps(
        {
            "after": after,
            "capability": SEARCH_CAPABILITY_ID,
            "company_id": context["company_id"],
            "database": context["database"],
            "filters": filters,
            "user_login": context["user_login"],
            "version": _CURSOR_VERSION,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
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
        value["capability"] != SEARCH_CAPABILITY_ID
        or value["version"] != _CURSOR_VERSION
        or not _is_integer(value["version"])
        or not _valid_id(value["company_id"])
        or value["company_id"] != context["company_id"]
        or value["database"] != context["database"]
        or value["user_login"] != context["user_login"]
        or cursor_filters != request_filters
        or not isinstance(after, list)
        or len(after) != 2
        or not _is_date(after[0])
        or not _valid_id(after[1])
    ):
        raise _invalid("The cursor does not match this request.", code="invalid_cursor")
    return after


def _valid_journal(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "code", "name"}
        and _valid_id(value["id"])
        and _is_nonempty_string(value["code"])
        and len(value["code"]) <= 5
        and _is_nonempty_string(value["name"])
    )


def _valid_currency(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "code"}
        and _valid_id(value["id"])
        and _is_nonempty_string(value["code"])
        and len(value["code"]) <= 3
    )


def _valid_partner(value: Any) -> bool:
    return value is None or (
        isinstance(value, dict)
        and set(value) == {"id", "name"}
        and _valid_id(value["id"])
        and _is_nonempty_string(value["name"])
    )


def _valid_header(row: Any, company_id: int, fields: frozenset[str]) -> bool:
    return (
        isinstance(row, dict)
        and set(row) == fields
        and _valid_id(row["id"])
        and _valid_optional_string(row["name"])
        and _is_date(row["date"])
        and row["state"] in _STATE_ORDER
        and _valid_optional_string(row["ref"])
        and _valid_journal(row["journal"])
        and row["company_id"] == company_id
        and _valid_currency(row["currency"])
        and _valid_partner(row["partner"])
    )


def _valid_money_triplet(value: dict[str, Any]) -> bool:
    if not all(
        _is_decimal_string(value[key]) for key in ("debit", "credit", "balance")
    ):
        return False
    return Decimal(value["debit"]) - Decimal(value["credit"]) == Decimal(
        value["balance"]
    )


def _validate_search_rows(
    rows: Any,
    *,
    company_id: int,
    after: list[Any] | None,
    maximum: int,
) -> list[dict[str, Any]]:
    if not isinstance(rows, list) or len(rows) > maximum:
        raise _failed("Odoo returned an invalid journal-entry search page.")
    previous = tuple(after) if after is not None else None
    record_ids: set[int] = set()
    result: list[dict[str, Any]] = []
    for row in rows:
        if not _valid_header(
            row, company_id, _SEARCH_FIELDS
        ) or not _valid_money_triplet(row):
            raise _failed("Odoo returned an invalid or out-of-scope journal entry.")
        current = (row["date"], row["id"])
        if current[1] in record_ids or (previous is not None and current >= previous):
            raise _failed("Odoo returned journal entries in an unstable order.")
        record_ids.add(current[1])
        previous = current
        result.append(dict(row))
    return result


def _validate_page(
    port: JournalEntryPort,
    page: Any,
    *,
    payload_key: str,
) -> Any:
    if not isinstance(page, dict) or set(page) != {
        "user_id",
        "company_visible",
        "module_installed",
        "access_allowed",
        payload_key,
    }:
        raise _failed("Odoo returned an invalid journal-entry page.")
    payload = page[payload_key]
    payload_present = bool(payload) if payload_key == "rows" else payload is not None
    if (
        not _valid_id(page["user_id"])
        or not _valid_id(port.user_id)
        or page["user_id"] != port.user_id
        or not isinstance(page["company_visible"], bool)
        or not isinstance(page["module_installed"], bool)
        or not isinstance(page["access_allowed"], bool)
        or (payload_key == "rows" and not isinstance(payload, list))
        or (
            page["access_allowed"]
            and not (page["company_visible"] and page["module_installed"])
        )
        or (not page["access_allowed"] and payload_present)
    ):
        raise _failed("Odoo returned an invalid journal-entry page.")
    if not page["company_visible"]:
        raise JournalEntryError(
            "company_unavailable",
            "The requested company is unavailable to the configured user.",
            exit_code=3,
        )
    if not page["module_installed"]:
        raise JournalEntryError(
            "uninstalled",
            "The journal-entry capability is not installed in this database.",
            exit_code=4,
        )
    if not page["access_allowed"]:
        raise JournalEntryError(
            "unauthorized",
            "The configured user cannot read journal entries.",
            exit_code=3,
        )
    return payload


def search_journal_entries(
    port: JournalEntryPort, request: dict[str, Any]
) -> dict[str, Any]:
    """Read one verified company-scoped page in date/id descending order."""

    _, context, filters, limit, cursor = validate_journal_entry_search_request(request)
    after = _decode_cursor(cursor, context=context, filters=filters) if cursor else None
    fetch_limit = limit + 1
    page = port.search_page(
        company_id=context["company_id"],
        after=after,
        limit=fetch_limit,
        filters=filters,
    )
    rows = _validate_page(port, page, payload_key="rows")
    records = _validate_search_rows(
        rows,
        company_id=context["company_id"],
        after=after,
        maximum=fetch_limit,
    )
    has_more = len(records) > limit
    items = records[:limit]
    next_cursor = None
    if has_more and items:
        next_cursor = _encode_cursor(
            [items[-1]["date"], items[-1]["id"]],
            context=context,
            filters=filters,
        )
    return {"items": items, "has_more": has_more, "next_cursor": next_cursor}


def _valid_account(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "code", "name"}
        and _valid_id(value["id"])
        and _is_nonempty_string(value["code"])
        and _is_nonempty_string(value["name"])
    )


def _validate_entry(row: Any, *, company_id: int, entry_id: int) -> dict[str, Any]:
    if (
        not _valid_header(row, company_id, _ENTRY_FIELDS)
        or row["id"] != entry_id
        or not isinstance(row["lines"], list)
        or not isinstance(row["totals"], dict)
        or set(row["totals"]) != {"debit", "credit", "balance"}
        or not _valid_money_triplet(row["totals"])
    ):
        raise _failed("Odoo returned an invalid or out-of-scope journal entry.")

    totals = {key: Decimal("0") for key in ("debit", "credit", "balance")}
    previous: tuple[int, int] | None = None
    line_ids: set[int] = set()
    for line in row["lines"]:
        display_type = line.get("display_type") if isinstance(line, dict) else None
        non_accountable = (
            isinstance(display_type, str)
            and display_type in _NON_ACCOUNTABLE_DISPLAY_TYPES
        )
        if (
            not isinstance(line, dict)
            or set(line) != _LINE_FIELDS
            or not _valid_id(line["id"])
            or not _is_integer(line["sequence"])
            or not (
                display_type is None
                or (isinstance(display_type, str) and display_type in _DISPLAY_TYPES)
            )
            or not _valid_optional_string(line["name"])
            or (non_accountable and line["account"] is not None)
            or (not non_accountable and not _valid_account(line["account"]))
            or not _valid_partner(line["partner"])
            or not _valid_money_triplet(line)
            or line["company_currency"] != row["currency"]
            or not _is_decimal_string(line["amount_currency"])
            or not (line["currency"] is None or _valid_currency(line["currency"]))
            or not (line["date_maturity"] is None or _is_date(line["date_maturity"]))
            or not isinstance(line["reconciled"], bool)
            or not _valid_optional_string(line["matching_number"])
        ):
            raise _failed("Odoo returned an invalid journal-entry line.")
        key = (line["sequence"], line["id"])
        if line["id"] in line_ids or (previous is not None and key <= previous):
            raise _failed("Odoo returned journal-entry lines in an unstable order.")
        line_ids.add(line["id"])
        previous = key
        for amount in totals:
            totals[amount] += Decimal(line[amount])
    if any(totals[key] != Decimal(row["totals"][key]) for key in totals):
        raise _failed("Odoo returned inconsistent journal-entry totals.")
    return dict(row)


def get_journal_entry(
    port: JournalEntryPort, request: dict[str, Any]
) -> dict[str, Any]:
    """Read and verify one exact general journal entry and all of its lines."""

    _, context, entry_id = validate_journal_entry_get_request(request)
    page = port.get_entry(company_id=context["company_id"], entry_id=entry_id)
    entry = _validate_page(port, page, payload_key="entry")
    if entry is None:
        raise JournalEntryError(
            "record_not_found",
            "The requested general journal entry was not found.",
            exit_code=4,
        )
    return _validate_entry(entry, company_id=context["company_id"], entry_id=entry_id)


def check_journal_entry(
    port: JournalEntryPort, request: dict[str, Any]
) -> dict[str, Any]:
    """Check whether one company-scoped general journal entry is ready to post."""

    _, context, entry_id = validate_journal_entry_check_request(request)
    page = port.check_entry(company_id=context["company_id"], entry_id=entry_id)
    entry = _validate_page(port, page, payload_key="entry")
    if entry is None:
        raise JournalEntryError(
            "record_not_found",
            "The requested general journal entry was not found.",
            exit_code=4,
        )
    verified = _validate_entry(
        entry, company_id=context["company_id"], entry_id=entry_id
    )
    accountable_lines = [
        line
        for line in verified["lines"]
        if line["display_type"] not in _NON_ACCOUNTABLE_DISPLAY_TYPES
    ]
    line_items_valid = len(accountable_lines) >= 2 and all(
        not (
            Decimal(line["debit"]) != Decimal(0)
            and Decimal(line["credit"]) != Decimal(0)
        )
        for line in accountable_lines
    )
    totals = verified["totals"]
    debits_equal_credits = (
        Decimal(totals["debit"]) == Decimal(totals["credit"])
        and Decimal(totals["balance"]) == Decimal(0)
    )
    state_is_draft = verified["state"] == "draft"
    return {
        "entry_id": verified["id"],
        "company_id": verified["company_id"],
        "state": verified["state"],
        "ready": state_is_draft and debits_equal_credits and line_items_valid,
        "checks": {
            "company_matches": True,
            "state_is_draft": state_is_draft,
            "debits_equal_credits": debits_equal_credits,
            "line_items_valid": line_items_valid,
        },
        "line_count": len(verified["lines"]),
        "accountable_line_count": len(accountable_lines),
        "totals": dict(totals),
    }
