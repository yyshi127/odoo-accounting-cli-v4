"""Strict contracts for the first company-scoped master-data lists."""

from __future__ import annotations

import base64
import binascii
import json
import re
import uuid
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol


DEFAULT_LIMIT = 100
MAX_LIMIT = 1000
_CURSOR_VERSION = 1
_DECIMAL_PATTERN = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
_NONNEGATIVE_DECIMAL_PATTERN = re.compile(r"^(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")

_CAPABILITIES = frozenset(
    {
        "journal.list",
        "tax.list",
        "payment_term.list",
        "currency.list",
    }
)

_JOURNAL_FIELDS = frozenset(
    {
        "id",
        "sequence",
        "code",
        "name",
        "type",
        "active",
        "currency",
        "company_id",
    }
)
_TAX_FIELDS = frozenset(
    {
        "id",
        "sequence",
        "name",
        "type_tax_use",
        "amount_type",
        "amount",
        "price_include",
        "include_base_amount",
        "is_base_affected",
        "active",
        "tax_group",
        "company_id",
    }
)
_PAYMENT_TERM_FIELDS = frozenset(
    {
        "id",
        "sequence",
        "name",
        "active",
        "company_id",
        "display_on_invoice",
        "early_discount",
        "discount_percentage",
        "discount_days",
        "early_pay_discount_computation",
        "lines",
    }
)
_PAYMENT_TERM_LINE_FIELDS = frozenset(
    {
        "id",
        "value",
        "value_amount",
        "delay_type",
        "nb_days",
        "days_next_month",
    }
)
_CURRENCY_FIELDS = frozenset(
    {
        "id",
        "code",
        "name",
        "symbol",
        "rounding",
        "decimal_places",
        "active",
        "position",
        "is_company_currency",
    }
)


class MasterDataListPort(Protocol):
    @property
    def user_id(self) -> int: ...

    def read_page(
        self,
        *,
        company_id: int,
        after: list[Any] | None,
        limit: int,
    ) -> dict[str, Any]: ...


class MasterDataListError(RuntimeError):
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


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_decimal_string(value: Any, *, nonnegative: bool = False) -> bool:
    pattern = _NONNEGATIVE_DECIMAL_PATTERN if nonnegative else _DECIMAL_PATTERN
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        return False
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        return False
    return parsed.is_finite() and (not nonnegative or parsed >= 0)


def _invalid(message: str, *, code: str = "invalid_request") -> MasterDataListError:
    return MasterDataListError(code, message, exit_code=2)


def _failed(message: str) -> MasterDataListError:
    return MasterDataListError("failed_validation", message, exit_code=8)


def _require_capability(capability_id: Any) -> str:
    if not isinstance(capability_id, str) or capability_id not in _CAPABILITIES:
        raise MasterDataListError(
            "unsupported_capability",
            "The master-data capability is unsupported.",
            exit_code=4,
        )
    return capability_id


def validate_master_data_request(
    capability_id: str, request: Any
) -> tuple[str, dict[str, Any], int, str | None]:
    """Validate the closed v1 envelope shared by these four list capabilities."""

    _require_capability(capability_id)
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
        if not _is_nonempty_string(context[key]):
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


def _encode_cursor(
    capability_id: str,
    after: list[Any],
    *,
    database: str,
    company_id: int,
    user_login: str,
    filters: dict[str, Any],
) -> str:
    payload = json.dumps(
        {
            "after": after,
            "capability": capability_id,
            "company_id": company_id,
            "database": database,
            "filters": filters,
            "user_login": user_login,
            "version": _CURSOR_VERSION,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def _decode_cursor(
    capability_id: str,
    cursor: str,
    *,
    database: str,
    company_id: int,
    user_login: str,
    filters: dict[str, Any],
) -> list[Any]:
    try:
        padding = "=" * (-len(cursor) % 4)
        raw = base64.b64decode(
            (cursor + padding).encode("ascii"), altchars=b"-_", validate=True
        )
        value = json.loads(raw.decode("utf-8"))
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
    if (
        value["capability"] != capability_id
        or not _valid_id(value["company_id"])
        or value["database"] != database
        or value["company_id"] != company_id
        or value["user_login"] != user_login
        or value["filters"] != filters
        or not _is_integer(value["version"])
        or value["version"] != _CURSOR_VERSION
        or not isinstance(value["after"], list)
        or _normalized_after(capability_id, value["after"]) is None
    ):
        raise _invalid("The cursor does not match this request.", code="invalid_cursor")
    return value["after"]


def _valid_id(value: Any) -> bool:
    return _is_integer(value) and value > 0


def _valid_sequence(value: Any) -> bool:
    return _is_integer(value)


def _valid_currency_reference(value: Any) -> bool:
    return value is None or (
        isinstance(value, dict)
        and set(value) == {"id", "code"}
        and _valid_id(value["id"])
        and _is_nonempty_string(value["code"])
        and len(value["code"]) <= 3
    )


def _valid_named_reference(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "name"}
        and _valid_id(value["id"])
        and _is_nonempty_string(value["name"])
    )


def _validate_journal(row: Any, company_id: int) -> bool:
    return (
        isinstance(row, dict)
        and set(row) == _JOURNAL_FIELDS
        and _valid_id(row["id"])
        and _valid_sequence(row["sequence"])
        and _is_nonempty_string(row["code"])
        and len(row["code"]) <= 5
        and _is_nonempty_string(row["name"])
        and row["type"] in {"sale", "purchase", "cash", "bank", "credit", "general"}
        and isinstance(row["active"], bool)
        and _valid_currency_reference(row["currency"])
        and row["company_id"] == company_id
    )


def _validate_tax(row: Any, company_id: int) -> bool:
    return (
        isinstance(row, dict)
        and set(row) == _TAX_FIELDS
        and _valid_id(row["id"])
        and _valid_sequence(row["sequence"])
        and _is_nonempty_string(row["name"])
        and row["type_tax_use"] in {"sale", "purchase", "none"}
        and row["amount_type"] in {"group", "fixed", "percent", "division"}
        and _is_decimal_string(row["amount"])
        and isinstance(row["price_include"], bool)
        and isinstance(row["include_base_amount"], bool)
        and isinstance(row["is_base_affected"], bool)
        and isinstance(row["active"], bool)
        and _valid_named_reference(row["tax_group"])
        and row["company_id"] == company_id
    )


def _valid_days_next_month(value: Any) -> bool:
    return value is None or (
        isinstance(value, str)
        and value.isdigit()
        and 0 <= int(value) <= 31
        and len(value) <= 2
    )


def _validate_payment_lines(lines: Any) -> bool:
    if not isinstance(lines, list) or not lines:
        return False
    previous_id = 0
    for line in lines:
        if (
            not isinstance(line, dict)
            or set(line) != _PAYMENT_TERM_LINE_FIELDS
            or not _valid_id(line["id"])
            or line["id"] <= previous_id
            or line["value"] not in {"percent", "fixed"}
            or not _is_decimal_string(line["value_amount"])
            or line["delay_type"]
            not in {
                "days_after",
                "days_after_end_of_month",
                "days_after_end_of_next_month",
                "days_end_of_month_on_the",
            }
            or not _is_integer(line["nb_days"])
            or not _valid_days_next_month(line["days_next_month"])
        ):
            return False
        amount = Decimal(line["value_amount"])
        if line["value"] == "percent":
            if not 0 <= amount <= 100:
                return False
        previous_id = line["id"]
    return True


def _validate_payment_term(row: Any, company_id: int) -> bool:
    if not (
        isinstance(row, dict)
        and set(row) == _PAYMENT_TERM_FIELDS
        and _valid_id(row["id"])
        and _valid_sequence(row["sequence"])
        and _is_nonempty_string(row["name"])
        and isinstance(row["active"], bool)
        and (row["company_id"] is None or row["company_id"] == company_id)
        and isinstance(row["display_on_invoice"], bool)
        and isinstance(row["early_discount"], bool)
        and _is_decimal_string(row["discount_percentage"])
        and _is_integer(row["discount_days"])
        and row["early_pay_discount_computation"] in {"included", "excluded", "mixed"}
        and _validate_payment_lines(row["lines"])
    ):
        return False
    if row["early_discount"]:
        return (
            len(row["lines"]) == 1
            and Decimal(row["discount_percentage"]) > 0
            and row["discount_days"] > 0
        )
    return True


def _validate_currency(row: Any, _company_id: int) -> bool:
    return (
        isinstance(row, dict)
        and set(row) == _CURRENCY_FIELDS
        and _valid_id(row["id"])
        and _is_nonempty_string(row["code"])
        and len(row["code"]) <= 3
        and (row["name"] is None or _is_nonempty_string(row["name"]))
        and _is_nonempty_string(row["symbol"])
        and _is_decimal_string(row["rounding"], nonnegative=True)
        and Decimal(row["rounding"]) > 0
        and _is_integer(row["decimal_places"])
        and row["decimal_places"] >= 0
        and isinstance(row["active"], bool)
        and row["position"] in {None, "before", "after"}
        and isinstance(row["is_company_currency"], bool)
    )


def _after_for_row(capability_id: str, row: dict[str, Any]) -> list[Any]:
    if capability_id == "journal.list":
        return [row["sequence"], row["type"], row["code"], row["id"]]
    if capability_id in {"tax.list", "payment_term.list"}:
        return [row["sequence"], row["id"]]
    if capability_id == "currency.list":
        return [row["active"], row["code"], row["id"]]
    raise AssertionError("unreachable capability")


def _normalized_after(capability_id: str, after: Any) -> tuple[Any, ...] | None:
    if not isinstance(after, list):
        return None
    if capability_id == "journal.list":
        if (
            len(after) != 4
            or not _valid_sequence(after[0])
            or after[1] not in {"sale", "purchase", "cash", "bank", "credit", "general"}
            or not _is_nonempty_string(after[2])
            or not _valid_id(after[3])
        ):
            return None
        return (after[0], after[1], after[2], after[3])
    if capability_id in {"tax.list", "payment_term.list"}:
        if len(after) != 2 or not _valid_sequence(after[0]) or not _valid_id(after[1]):
            return None
        return (after[0], after[1])
    if capability_id == "currency.list":
        if (
            len(after) != 3
            or not isinstance(after[0], bool)
            or not _is_nonempty_string(after[1])
            or not _valid_id(after[2])
        ):
            return None
        return (0 if after[0] else 1, after[1], after[2])
    return None


def _validated_rows(
    capability_id: str,
    rows: Any,
    *,
    company_id: int,
    after: list[Any] | None,
    maximum: int,
) -> list[dict[str, Any]]:
    if not isinstance(rows, list) or len(rows) > maximum:
        raise _failed("Odoo returned an invalid master-data page.")
    validators = {
        "journal.list": _validate_journal,
        "tax.list": _validate_tax,
        "payment_term.list": _validate_payment_term,
        "currency.list": _validate_currency,
    }
    previous = _normalized_after(capability_id, after) if after is not None else None
    if after is not None and previous is None:
        raise _failed("Odoo returned an invalid master-data cursor boundary.")
    result: list[dict[str, Any]] = []
    record_ids: set[int] = set()
    for row in rows:
        if not validators[capability_id](row, company_id):
            raise _failed("Odoo returned an invalid or out-of-scope master-data record.")
        current_after = _after_for_row(capability_id, row)
        current = _normalized_after(capability_id, current_after)
        if current is None or (previous is not None and current <= previous):
            raise _failed("Odoo returned master data in an unstable order.")
        if row["id"] in record_ids:
            raise _failed("Odoo returned a duplicate master-data record.")
        record_ids.add(row["id"])
        previous = current
        result.append(dict(row))
    return result


def read_master_data(
    capability_id: str, port: MasterDataListPort, request: dict[str, Any]
) -> dict[str, Any]:
    """Read and verify one stable keyset page through a single narrow port call."""

    _require_capability(capability_id)
    _, context, limit, cursor = validate_master_data_request(capability_id, request)
    filters: dict[str, Any] = {}
    after = (
        _decode_cursor(
            capability_id,
            cursor,
            database=context["database"],
            company_id=context["company_id"],
            user_login=context["user_login"],
            filters=filters,
        )
        if cursor
        else None
    )
    fetch_limit = limit + 1
    page = port.read_page(
        company_id=context["company_id"],
        after=after,
        limit=fetch_limit,
    )
    if (
        not isinstance(page, dict)
        or set(page)
        != {
            "user_id",
            "company_visible",
            "module_installed",
            "access_allowed",
            "rows",
        }
        or not _valid_id(page["user_id"])
        or port.user_id != page["user_id"]
        or not isinstance(page["company_visible"], bool)
        or not isinstance(page["module_installed"], bool)
        or not isinstance(page["access_allowed"], bool)
        or not isinstance(page["rows"], list)
        or (
            page["access_allowed"]
            and not (page["company_visible"] and page["module_installed"])
        )
        or (not page["access_allowed"] and page["rows"])
    ):
        raise _failed("Odoo returned an invalid master-data page.")
    if not page["company_visible"]:
        raise MasterDataListError(
            "company_unavailable",
            "The requested company is unavailable to the configured user.",
            exit_code=3,
        )
    if not page["module_installed"]:
        raise MasterDataListError(
            "uninstalled",
            "The master-data capability is not installed in this database.",
            exit_code=4,
        )
    if not page["access_allowed"]:
        raise MasterDataListError(
            "unauthorized",
            "The configured user cannot read this master data.",
            exit_code=3,
        )

    records = _validated_rows(
        capability_id,
        page["rows"],
        company_id=context["company_id"],
        after=after,
        maximum=fetch_limit,
    )
    has_more = len(records) > limit
    items = records[:limit]
    next_cursor = None
    if has_more and items:
        next_cursor = _encode_cursor(
            capability_id,
            _after_for_row(capability_id, items[-1]),
            database=context["database"],
            company_id=context["company_id"],
            user_login=context["user_login"],
            filters=filters,
        )
    return {"items": items, "has_more": has_more, "next_cursor": next_cursor}
