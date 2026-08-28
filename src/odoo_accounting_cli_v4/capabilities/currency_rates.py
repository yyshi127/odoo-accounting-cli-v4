"""Closed read contract for Odoo currency-rate history.

This capability exposes rate records only. It does not claim ledger balances or
multicurrency balance equivalence.
"""

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

CAPABILITY_ID = "currency.rate.list"
CONVERT_CAPABILITY_ID = "currency.convert"
DEFAULT_LIMIT = 100
MAX_LIMIT = 1000
_CURSOR_VERSION = 1
_POSITIVE_DECIMAL_PATTERN = re.compile(
    r"^(?:(?:[1-9][0-9]*)(?:\.[0-9]+)?|0\.(?=[0-9]*[1-9])[0-9]+)$"
)
_DECIMAL_PATTERN = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
_FILTER_FIELDS = frozenset({"date_from", "date_to", "currency_id"})
_ROW_FIELDS = frozenset(
    {
        "id",
        "date",
        "currency",
        "company_currency",
        "requested_company_id",
        "source_company_id",
        "technical_rate",
        "foreign_units_per_company_unit",
        "company_units_per_foreign_unit",
    }
)
_RECIPROCAL_TOLERANCE = Decimal("0.000000000001")


class CurrencyRateListPort(Protocol):
    @property
    def user_id(self) -> int: ...

    def read_page(
        self,
        *,
        company_id: int,
        after: list[Any] | None,
        limit: int,
        filters: dict[str, Any],
    ) -> dict[str, Any]: ...


class CurrencyConvertPort(Protocol):
    @property
    def user_id(self) -> int: ...

    def convert(
        self,
        *,
        company_id: int,
        amount: str,
        from_currency_id: int,
        to_currency_id: int,
        conversion_date: str,
    ) -> dict[str, Any]: ...


class CurrencyRateListError(RuntimeError):
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


class CurrencyConversionError(CurrencyRateListError):
    """Typed failure from the fixed currency conversion capability."""


def _invalid(message: str, *, code: str = "invalid_request") -> CurrencyRateListError:
    return CurrencyRateListError(code, message, exit_code=2)


def _failed(message: str) -> CurrencyRateListError:
    return CurrencyRateListError("failed_validation", message, exit_code=8)


def _is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _valid_id(value: Any) -> bool:
    return _is_integer(value) and value > 0


def _is_context_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return False
    return parsed.isoformat() == value


def _positive_decimal(value: Any) -> Decimal | None:
    if (
        not isinstance(value, str)
        or len(value) > 256
        or _POSITIVE_DECIMAL_PATTERN.fullmatch(value) is None
    ):
        return None
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        return None
    return parsed if parsed.is_finite() and parsed > 0 else None


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate cursor key")
        value[key] = item
    return value


def _reject_json_float(_value: str) -> None:
    raise ValueError("cursor floats are unsupported")


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


def validate_currency_rate_list_request(
    request: Any,
) -> tuple[str, dict[str, Any], dict[str, Any], int, str | None]:
    """Validate and normalize the closed currency-rate list request."""

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
    if not isinstance(parameters, dict) or not set(parameters) <= _FILTER_FIELDS | {
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

    date_from = parameters.get("date_from")
    date_to = parameters.get("date_to")
    if date_from is not None and not _is_date(date_from):
        raise _invalid("parameters.date_from must be null or a YYYY-MM-DD date.")
    if date_to is not None and not _is_date(date_to):
        raise _invalid("parameters.date_to must be null or a YYYY-MM-DD date.")
    if date_from is not None and date_to is not None and date_from > date_to:
        raise _invalid("parameters.date_from cannot be after parameters.date_to.")
    currency_id = parameters.get("currency_id")
    if currency_id is not None and not _valid_id(currency_id):
        raise _invalid("parameters.currency_id must be null or a positive integer.")

    filters = {
        "date_from": date_from,
        "date_to": date_to,
        "currency_id": currency_id,
    }
    return request_id, context, filters, limit, cursor


def _cursor_binding(context: dict[str, Any], filters: dict[str, Any]) -> str:
    value = {
        "capability": CAPABILITY_ID,
        "company_id": context["company_id"],
        "database": context["database"],
        "filters": filters,
        "user_login": context["user_login"],
    }
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _encode_cursor(
    after: list[Any], *, context: dict[str, Any], filters: dict[str, Any]
) -> str:
    payload = _canonical_json(
        {
            "after": after,
            "binding": _cursor_binding(context, filters),
            "version": _CURSOR_VERSION,
        }
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
    if (
        not isinstance(value, dict)
        or set(value) != {"after", "binding", "version"}
        or not _is_integer(value["version"])
        or value["version"] != _CURSOR_VERSION
        or value["binding"] != _cursor_binding(context, filters)
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
        and isinstance(value["code"], str)
        and 1 <= len(value["code"]) <= 3
    )


def _valid_row(
    row: Any, *, requested_company_id: int, root_company_id: int
) -> bool:
    if (
        not isinstance(row, dict)
        or set(row) != _ROW_FIELDS
        or not _valid_id(row["id"])
        or not _is_date(row["date"])
        or not _valid_currency(row["currency"])
        or not _valid_currency(row["company_currency"])
        or row["requested_company_id"] != requested_company_id
        or row["source_company_id"] not in {None, root_company_id}
    ):
        return False
    technical_rate = _positive_decimal(row["technical_rate"])
    foreign_per_company = _positive_decimal(
        row["foreign_units_per_company_unit"]
    )
    company_per_foreign = _positive_decimal(
        row["company_units_per_foreign_unit"]
    )
    return (
        technical_rate is not None
        and foreign_per_company is not None
        and company_per_foreign is not None
        and abs(foreign_per_company * company_per_foreign - Decimal(1))
        <= _RECIPROCAL_TOLERANCE
    )


def _strictly_after(current: tuple[str, int], previous: tuple[str, int]) -> bool:
    return current[0] < previous[0] or (
        current[0] == previous[0] and current[1] > previous[1]
    )


def _validate_page(
    port: CurrencyRateListPort, page: Any
) -> tuple[int, list[Any]]:
    if not isinstance(page, dict) or set(page) != {
        "user_id",
        "company_visible",
        "module_installed",
        "access_allowed",
        "root_company_id",
        "rows",
    }:
        raise _failed("Odoo returned an invalid currency-rate page.")
    try:
        port_user_id = port.user_id
    except ValueError as exc:
        raise _failed("Odoo returned an invalid currency-rate page.") from exc
    rows = page["rows"]
    if (
        not _valid_id(page["user_id"])
        or page["user_id"] != port_user_id
        or not isinstance(page["company_visible"], bool)
        or not isinstance(page["module_installed"], bool)
        or not isinstance(page["access_allowed"], bool)
        or not (
            page["root_company_id"] is None
            or _valid_id(page["root_company_id"])
        )
        or not isinstance(rows, list)
        or (page["company_visible"] and not page["access_allowed"])
        or (page["access_allowed"] and not page["module_installed"])
        or (
            bool(rows)
            and not (
                page["module_installed"]
                and page["access_allowed"]
                and page["company_visible"]
            )
        )
        or (
            page["module_installed"]
            and page["access_allowed"]
            and page["company_visible"]
            and not _valid_id(page["root_company_id"])
        )
        or (
            not (
                page["module_installed"]
                and page["access_allowed"]
                and page["company_visible"]
            )
            and page["root_company_id"] is not None
        )
    ):
        raise _failed("Odoo returned an invalid currency-rate page.")
    if not page["module_installed"]:
        raise CurrencyRateListError(
            "uninstalled",
            "The base currency-rate model is unavailable in this database.",
            exit_code=4,
        )
    if not page["access_allowed"]:
        raise CurrencyRateListError(
            "unauthorized",
            "The configured user cannot read currency rates.",
            exit_code=3,
        )
    if not page["company_visible"]:
        raise CurrencyRateListError(
            "company_unavailable",
            "The requested company is unavailable to the configured user.",
            exit_code=3,
        )
    root_company_id = page["root_company_id"]
    if not _valid_id(root_company_id):
        raise _failed("Odoo returned an invalid currency-rate company context.")
    return root_company_id, rows


def _validate_rows(
    rows: Any,
    *,
    requested_company_id: int,
    root_company_id: int,
    after: list[Any] | None,
    filters: dict[str, Any],
    maximum: int,
) -> list[dict[str, Any]]:
    if not isinstance(rows, list) or len(rows) > maximum:
        raise _failed("Odoo returned an invalid currency-rate page.")
    previous = tuple(after) if after is not None else None
    record_ids: set[int] = set()
    result: list[dict[str, Any]] = []
    for row in rows:
        if not _valid_row(
            row,
            requested_company_id=requested_company_id,
            root_company_id=root_company_id,
        ):
            raise _failed("Odoo returned an invalid or out-of-scope currency rate.")
        current = (row["date"], row["id"])
        if (
            row["id"] in record_ids
            or (previous is not None and not _strictly_after(current, previous))
            or (
                filters["date_from"] is not None
                and row["date"] < filters["date_from"]
            )
            or (
                filters["date_to"] is not None
                and row["date"] > filters["date_to"]
            )
            or (
                filters["currency_id"] is not None
                and row["currency"]["id"] != filters["currency_id"]
            )
        ):
            raise _failed("Odoo returned a currency rate outside the requested page.")
        record_ids.add(row["id"])
        previous = current
        result.append(dict(row))
    return result


def list_currency_rates(
    port: CurrencyRateListPort, request: dict[str, Any]
) -> dict[str, Any]:
    """Read one verified keyset page of global/root-company rate records."""

    _, context, filters, limit, cursor = validate_currency_rate_list_request(request)
    after = _decode_cursor(cursor, context=context, filters=filters) if cursor else None
    fetch_limit = limit + 1
    try:
        page = port.read_page(
            company_id=context["company_id"],
            after=after,
            limit=fetch_limit,
            filters=filters,
        )
    except ValueError as exc:
        raise _failed("The Odoo bridge returned an invalid currency-rate page.") from exc
    root_company_id, rows = _validate_page(port, page)
    records = _validate_rows(
        rows,
        requested_company_id=context["company_id"],
        root_company_id=root_company_id,
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
            context=context,
            filters=filters,
        )
    return {"items": items, "has_more": has_more, "next_cursor": next_cursor}


def _conversion_invalid(
    message: str, *, code: str = "invalid_request"
) -> CurrencyConversionError:
    return CurrencyConversionError(code, message, exit_code=2)


def _conversion_failed(message: str) -> CurrencyConversionError:
    return CurrencyConversionError("failed_validation", message, exit_code=8)


def _decimal(value: Any) -> Decimal | None:
    if (
        not isinstance(value, str)
        or len(value) > 256
        or _DECIMAL_PATTERN.fullmatch(value) is None
    ):
        return None
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        return None
    return parsed if parsed.is_finite() else None


def validate_currency_convert_request(
    request: Any,
) -> tuple[str, dict[str, Any], str, int, int, str]:
    """Validate the closed request for one standard Odoo currency conversion."""

    if not isinstance(request, dict) or set(request) != {
        "schema_version",
        "request_id",
        "context",
        "parameters",
    }:
        raise _conversion_invalid("The request must match the v1 request envelope.")
    if request["schema_version"] != "v1":
        raise _conversion_invalid("schema_version must be 'v1'.")
    request_id = request["request_id"]
    if not isinstance(request_id, str):
        raise _conversion_invalid("request_id must be a UUID string.")
    try:
        parsed_request_id = uuid.UUID(request_id)
    except (ValueError, AttributeError) as exc:
        raise _conversion_invalid("request_id must be a UUID string.") from exc
    if (
        str(parsed_request_id) != request_id.lower()
        or parsed_request_id.version not in {1, 2, 3, 4, 5}
        or parsed_request_id.variant != uuid.RFC_4122
    ):
        raise _conversion_invalid("request_id must use canonical UUID syntax.")

    context = request["context"]
    if not isinstance(context, dict) or set(context) != {
        "database",
        "company_id",
        "user_login",
        "language",
        "timezone",
    }:
        raise _conversion_invalid("context must contain only the required v1 fields.")
    for key in ("database", "user_login", "language", "timezone"):
        if not _is_context_text(context[key]):
            raise _conversion_invalid(f"context.{key} must be a non-empty string.")
    if not _valid_id(context["company_id"]):
        raise _conversion_invalid("context.company_id must be a positive integer.")

    parameters = request["parameters"]
    if not isinstance(parameters, dict) or set(parameters) != {
        "amount",
        "from_currency_id",
        "to_currency_id",
        "date",
    }:
        raise _conversion_invalid(
            f"{CONVERT_CAPABILITY_ID} requires only amount, from_currency_id, "
            "to_currency_id, and date."
        )
    amount = parameters["amount"]
    if _decimal(amount) is None:
        raise _conversion_invalid("parameters.amount must be a decimal string.")
    from_currency_id = parameters["from_currency_id"]
    to_currency_id = parameters["to_currency_id"]
    if not _valid_id(from_currency_id):
        raise _conversion_invalid(
            "parameters.from_currency_id must be a positive integer."
        )
    if not _valid_id(to_currency_id):
        raise _conversion_invalid(
            "parameters.to_currency_id must be a positive integer."
        )
    conversion_date = parameters["date"]
    if not _is_date(conversion_date):
        raise _conversion_invalid("parameters.date must be a YYYY-MM-DD date.")
    return (
        request_id,
        context,
        amount,
        from_currency_id,
        to_currency_id,
        conversion_date,
    )


def _validate_conversion_page(
    port: CurrencyConvertPort, page: Any
) -> dict[str, Any] | None:
    if not isinstance(page, dict) or set(page) != {
        "user_id",
        "company_visible",
        "module_installed",
        "access_allowed",
        "conversion",
    }:
        raise _conversion_failed("Odoo returned an invalid currency conversion.")
    try:
        port_user_id = port.user_id
    except ValueError as exc:
        raise _conversion_failed("Odoo returned an invalid currency conversion.") from exc
    conversion = page["conversion"]
    if (
        not _valid_id(page["user_id"])
        or page["user_id"] != port_user_id
        or not isinstance(page["company_visible"], bool)
        or not isinstance(page["module_installed"], bool)
        or not isinstance(page["access_allowed"], bool)
        or not (conversion is None or isinstance(conversion, dict))
        or (
            page["access_allowed"]
            and not (page["company_visible"] and page["module_installed"])
        )
        or (not page["access_allowed"] and conversion is not None)
    ):
        raise _conversion_failed("Odoo returned an invalid currency conversion.")
    if not page["module_installed"]:
        raise CurrencyConversionError(
            "uninstalled",
            "The base currency conversion models are unavailable in this database.",
            exit_code=4,
        )
    if not page["access_allowed"]:
        raise CurrencyConversionError(
            "unauthorized",
            "The configured user cannot convert currencies.",
            exit_code=3,
        )
    if not page["company_visible"]:
        raise CurrencyConversionError(
            "company_unavailable",
            "The requested company is unavailable to the configured user.",
            exit_code=3,
        )
    return conversion


def _validate_conversion(
    conversion: Any,
    *,
    company_id: int,
    amount: str,
    from_currency_id: int,
    to_currency_id: int,
    conversion_date: str,
) -> dict[str, Any]:
    if (
        not isinstance(conversion, dict)
        or set(conversion)
        != {
            "company_id",
            "date",
            "amount",
            "converted_amount",
            "from_currency",
            "to_currency",
        }
        or conversion["company_id"] != company_id
        or conversion["date"] != conversion_date
        or conversion["amount"] != amount
        or _decimal(conversion["converted_amount"]) is None
        or not _valid_currency(conversion["from_currency"])
        or conversion["from_currency"]["id"] != from_currency_id
        or not _valid_currency(conversion["to_currency"])
        or conversion["to_currency"]["id"] != to_currency_id
    ):
        raise _conversion_failed(
            "Odoo returned a mismatched or malformed currency conversion."
        )
    return dict(conversion)


def convert_currency(
    port: CurrencyConvertPort, request: dict[str, Any]
) -> dict[str, Any]:
    """Convert one decimal amount through Odoo's company/date-aware rate logic."""

    (
        _,
        context,
        amount,
        from_currency_id,
        to_currency_id,
        conversion_date,
    ) = validate_currency_convert_request(request)
    try:
        page = port.convert(
            company_id=context["company_id"],
            amount=amount,
            from_currency_id=from_currency_id,
            to_currency_id=to_currency_id,
            conversion_date=conversion_date,
        )
    except ValueError as exc:
        raise _conversion_failed(
            "The Odoo bridge returned an invalid currency conversion."
        ) from exc
    conversion = _validate_conversion_page(port, page)
    if conversion is None:
        raise CurrencyConversionError(
            "record_not_found",
            "A requested currency was not found.",
            exit_code=4,
        )
    return _validate_conversion(
        conversion,
        company_id=context["company_id"],
        amount=amount,
        from_currency_id=from_currency_id,
        to_currency_id=to_currency_id,
        conversion_date=conversion_date,
    )
