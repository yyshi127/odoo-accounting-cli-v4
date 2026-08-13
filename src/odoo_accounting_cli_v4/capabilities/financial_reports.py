"""Strict contracts for fixed read-only accounting reports."""

from __future__ import annotations

import base64
import binascii
import json
import re
import uuid
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol


TRIAL_BALANCE_CAPABILITY_ID = "report.trial_balance"
BALANCE_SHEET_CAPABILITY_ID = "report.balance_sheet"
PROFIT_AND_LOSS_CAPABILITY_ID = "report.profit_and_loss"
DEFAULT_LIMIT = 100
MAX_LIMIT = 1000
_CURSOR_VERSION = 1
_DECIMAL_PATTERN = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")


class FinancialReportPort(Protocol):
    @property
    def user_id(self) -> int: ...

    def read_page(
        self,
        *,
        company_id: int,
        date_from: str | None,
        date_to: str,
        after_line_id: str | None,
        limit: int,
    ) -> dict[str, Any]: ...


class FinancialReportError(RuntimeError):
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


def _invalid(message: str, *, code: str = "invalid_request") -> FinancialReportError:
    return FinancialReportError(code, message, exit_code=2)


def _failed(message: str) -> FinancialReportError:
    return FinancialReportError("failed_validation", message, exit_code=8)


def _is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _valid_id(value: Any) -> bool:
    return _is_integer(value) and value > 0


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _canonical_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return False
    return parsed.isoformat() == value


def _decimal_string(value: Any) -> bool:
    if not isinstance(value, str) or _DECIMAL_PATTERN.fullmatch(value) is None:
        return False
    try:
        return Decimal(value).is_finite()
    except InvalidOperation:
        return False


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate cursor key")
        value[key] = item
    return value


def _reject_json_constant(_value: str) -> None:
    raise ValueError("non-finite cursor number")


def _validate_envelope(request: Any) -> tuple[dict[str, Any], dict[str, Any]]:
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
        parsed = uuid.UUID(request_id)
    except (ValueError, AttributeError) as exc:
        raise _invalid("request_id must be a UUID string.") from exc
    if (
        str(parsed) != request_id.lower()
        or parsed.version not in {1, 2, 3, 4, 5}
        or parsed.variant != uuid.RFC_4122
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
    parameters = request["parameters"]
    if not isinstance(parameters, dict):
        raise _invalid("parameters must be an object.")
    return context, parameters


def validate_trial_balance_request(
    request: Any,
) -> tuple[dict[str, Any], str, str, int, str | None]:
    context, parameters = _validate_envelope(request)
    if not set(parameters) <= {"date_from", "date_to", "limit", "cursor"}:
        raise _invalid("report.trial_balance contains an unsupported parameter.")
    if not {"date_from", "date_to"} <= set(parameters):
        raise _invalid("date_from and date_to are required.")
    date_from = parameters["date_from"]
    date_to = parameters["date_to"]
    if not _canonical_date(date_from) or not _canonical_date(date_to):
        raise _invalid("date_from and date_to must be YYYY-MM-DD dates.")
    if date_from > date_to:
        raise _invalid("date_from cannot be after date_to.")
    limit = parameters.get("limit", DEFAULT_LIMIT)
    if not _is_integer(limit) or not 1 <= limit <= MAX_LIMIT:
        raise _invalid(f"limit must be between 1 and {MAX_LIMIT}.")
    cursor = parameters.get("cursor")
    if cursor is not None and (
        not isinstance(cursor, str) or not cursor or len(cursor) > 4096
    ):
        raise _invalid("cursor must be null or a non-empty cursor string.")
    return context, date_from, date_to, limit, cursor


def validate_balance_sheet_request(
    request: Any,
) -> tuple[dict[str, Any], None, str, int, str | None]:
    context, parameters = _validate_envelope(request)
    if not set(parameters) <= {"as_of", "limit", "cursor"}:
        raise _invalid("report.balance_sheet contains an unsupported parameter.")
    if "as_of" not in parameters or not _canonical_date(parameters["as_of"]):
        raise _invalid("as_of must be a YYYY-MM-DD date.")
    limit = parameters.get("limit", DEFAULT_LIMIT)
    if not _is_integer(limit) or not 1 <= limit <= MAX_LIMIT:
        raise _invalid(f"limit must be between 1 and {MAX_LIMIT}.")
    cursor = parameters.get("cursor")
    if cursor is not None and (
        not isinstance(cursor, str) or not cursor or len(cursor) > 4096
    ):
        raise _invalid("cursor must be null or a non-empty cursor string.")
    return context, None, parameters["as_of"], limit, cursor


def validate_profit_and_loss_request(
    request: Any,
) -> tuple[dict[str, Any], str, str, int, str | None]:
    context, parameters = _validate_envelope(request)
    if not set(parameters) <= {"date_from", "date_to", "limit", "cursor"}:
        raise _invalid("report.profit_and_loss contains an unsupported parameter.")
    if not {"date_from", "date_to"} <= set(parameters):
        raise _invalid("date_from and date_to are required.")
    date_from = parameters["date_from"]
    date_to = parameters["date_to"]
    if not _canonical_date(date_from) or not _canonical_date(date_to):
        raise _invalid("date_from and date_to must be YYYY-MM-DD dates.")
    if date_from > date_to:
        raise _invalid("date_from cannot be after date_to.")
    limit = parameters.get("limit", DEFAULT_LIMIT)
    if not _is_integer(limit) or not 1 <= limit <= MAX_LIMIT:
        raise _invalid(f"limit must be between 1 and {MAX_LIMIT}.")
    cursor = parameters.get("cursor")
    if cursor is not None and (
        not isinstance(cursor, str) or not cursor or len(cursor) > 4096
    ):
        raise _invalid("cursor must be null or a non-empty cursor string.")
    return context, date_from, date_to, limit, cursor


def _encode_cursor(
    line_id: str,
    *,
    capability_id: str,
    context: dict[str, Any],
    date_from: str | None,
    date_to: str,
) -> str:
    payload = json.dumps(
        {
            "after_line_id": line_id,
            "capability": capability_id,
            "company_id": context["company_id"],
            "database": context["database"],
            "date_from": date_from,
            "date_to": date_to,
            "user_login": context["user_login"],
            "version": _CURSOR_VERSION,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def _decode_cursor(
    cursor: str,
    *,
    capability_id: str,
    context: dict[str, Any],
    date_from: str | None,
    date_to: str,
) -> str:
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
    if (
        not isinstance(value, dict)
        or set(value)
        != {
            "after_line_id",
            "capability",
            "company_id",
            "database",
            "date_from",
            "date_to",
            "user_login",
            "version",
        }
        or value["capability"] != capability_id
        or value["version"] != _CURSOR_VERSION
        or not _is_integer(value["version"])
        or value["company_id"] != context["company_id"]
        or value["database"] != context["database"]
        or value["user_login"] != context["user_login"]
        or value["date_from"] != date_from
        or value["date_to"] != date_to
        or not _nonempty_string(value["after_line_id"])
    ):
        raise _invalid("The cursor does not match this request.", code="invalid_cursor")
    return value["after_line_id"]


def _validate_columns(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise _failed("Odoo returned invalid trial-balance columns.")
    result: list[dict[str, Any]] = []
    for index, column in enumerate(value):
        if (
            not isinstance(column, dict)
            or set(column) != {"index", "label", "expression_label"}
            or column["index"] != index
            or not _nonempty_string(column["label"])
            or not _nonempty_string(column["expression_label"])
        ):
            raise _failed("Odoo returned invalid trial-balance columns.")
        result.append(dict(column))
    return result


def _validate_lines(
    value: Any, *, column_count: int, maximum: int
) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) > maximum:
        raise _failed("Odoo returned an invalid trial-balance page.")
    line_ids: set[str] = set()
    result: list[dict[str, Any]] = []
    for line in value:
        if (
            not isinstance(line, dict)
            or set(line)
            != {"id", "parent_id", "name", "level", "unfoldable", "values"}
            or not _nonempty_string(line["id"])
            or line["id"] in line_ids
            or not (line["parent_id"] is None or _nonempty_string(line["parent_id"]))
            or not _nonempty_string(line["name"])
            or not _is_integer(line["level"])
            or line["level"] < 0
            or not isinstance(line["unfoldable"], bool)
            or not isinstance(line["values"], list)
            or len(line["values"]) != column_count
            or any(item is not None and not _decimal_string(item) for item in line["values"])
        ):
            raise _failed("Odoo returned an invalid trial-balance line.")
        line_ids.add(line["id"])
        result.append(dict(line))
    return result


def _validated_page(
    port: FinancialReportPort,
    page: Any,
    *,
    report_key: str,
    date_from: str | None,
    date_to: str,
    maximum: int,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    expected = {
        "user_id",
        "company_visible",
        "module_installed",
        "access_allowed",
        "cursor_found",
        "report",
        "date",
        "currency",
        "basis",
        "columns",
        "lines",
    }
    if (
        not isinstance(page, dict)
        or set(page) != expected
        or not _valid_id(page["user_id"])
        or not _valid_id(port.user_id)
        or page["user_id"] != port.user_id
        or not all(
            isinstance(page[key], bool)
            for key in ("company_visible", "module_installed", "access_allowed", "cursor_found")
        )
        or (page["access_allowed"] and not (page["company_visible"] and page["module_installed"]))
        or (
            not page["access_allowed"]
            and (page["columns"] or page["lines"])
        )
    ):
        raise _failed("Odoo returned an invalid trial-balance page.")
    if not page["company_visible"]:
        raise FinancialReportError(
            "company_unavailable",
            "The requested company is unavailable to the configured user.",
            exit_code=3,
        )
    if not page["module_installed"]:
        raise FinancialReportError(
            "uninstalled", "The trial-balance report is not installed.", exit_code=4
        )
    if not page["access_allowed"]:
        raise FinancialReportError(
            "unauthorized", "The configured user cannot read this report.", exit_code=3
        )
    if not page["cursor_found"]:
        raise _invalid("The cursor is no longer present.", code="invalid_cursor")
    report = page["report"]
    report_date = page["date"]
    currency = page["currency"]
    if (
        not isinstance(report, dict)
        or set(report) != {"key", "name"}
        or report["key"] != report_key
        or not _nonempty_string(report["name"])
        or not isinstance(report_date, dict)
        or set(report_date) != {"from", "to"}
        or not _canonical_date(report_date["from"])
        or report_date["to"] != date_to
        or report_date["from"] > report_date["to"]
        or (date_from is not None and report_date["from"] != date_from)
        or not isinstance(currency, dict)
        or set(currency) != {"id", "code", "decimal_places"}
        or not _valid_id(currency["id"])
        or not _nonempty_string(currency["code"])
        or len(currency["code"]) > 3
        or not _is_integer(currency["decimal_places"])
        or currency["decimal_places"] < 0
        or page["basis"] != "posted_entries"
    ):
        raise _failed("Odoo returned invalid trial-balance metadata.")
    columns = _validate_columns(page["columns"])
    lines = _validate_lines(page["lines"], column_count=len(columns), maximum=maximum)
    return {"report": report, "date": report_date, "currency": currency, "basis": page["basis"]}, columns, lines


def _read_financial_report(
    port: FinancialReportPort,
    *,
    capability_id: str,
    report_key: str,
    context: dict[str, Any],
    date_from: str | None,
    date_to: str,
    limit: int,
    cursor: str | None,
) -> dict[str, Any]:
    after_line_id = (
        _decode_cursor(
            cursor,
            capability_id=capability_id,
            context=context,
            date_from=date_from,
            date_to=date_to,
        )
        if cursor
        else None
    )
    fetch_limit = limit + 1
    page = port.read_page(
        company_id=context["company_id"],
        date_from=date_from,
        date_to=date_to,
        after_line_id=after_line_id,
        limit=fetch_limit,
    )
    metadata, columns, lines = _validated_page(
        port,
        page,
        report_key=report_key,
        date_from=date_from,
        date_to=date_to,
        maximum=fetch_limit,
    )
    has_more = len(lines) > limit
    visible = lines[:limit]
    next_cursor = None
    if has_more and visible:
        next_cursor = _encode_cursor(
            visible[-1]["id"],
            capability_id=capability_id,
            context=context,
            date_from=date_from,
            date_to=date_to,
        )
    return {
        **metadata,
        "columns": columns,
        "lines": visible,
        "has_more": has_more,
        "next_cursor": next_cursor,
    }


def read_trial_balance(
    port: FinancialReportPort, request: dict[str, Any]
) -> dict[str, Any]:
    """Read one verified page from the fixed Odoo trial-balance report."""

    context, date_from, date_to, limit, cursor = validate_trial_balance_request(request)
    return _read_financial_report(
        port,
        capability_id=TRIAL_BALANCE_CAPABILITY_ID,
        report_key="trial_balance",
        context=context,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        cursor=cursor,
    )


def read_balance_sheet(
    port: FinancialReportPort, request: dict[str, Any]
) -> dict[str, Any]:
    """Read one verified page from the fixed Odoo balance-sheet report."""

    context, date_from, date_to, limit, cursor = validate_balance_sheet_request(request)
    return _read_financial_report(
        port,
        capability_id=BALANCE_SHEET_CAPABILITY_ID,
        report_key="balance_sheet",
        context=context,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        cursor=cursor,
    )


def read_profit_and_loss(
    port: FinancialReportPort, request: dict[str, Any]
) -> dict[str, Any]:
    """Read one verified page from the fixed Odoo profit-and-loss report."""

    context, date_from, date_to, limit, cursor = validate_profit_and_loss_request(
        request
    )
    return _read_financial_report(
        port,
        capability_id=PROFIT_AND_LOSS_CAPABILITY_ID,
        report_key="profit_and_loss",
        context=context,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        cursor=cursor,
    )
