"""Closed contract for the official Odoo budget execution detail report."""

from __future__ import annotations

import base64
import binascii
import json
import re
import uuid
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol

CAPABILITY_ID = "report.budget"
DEFAULT_LIMIT = 100
MAX_LIMIT = 1000
_CURSOR_VERSION = 1
_LINE_TYPES = frozenset({"budget", "achieved"})
_SOURCE_MODELS = frozenset({"budget.analytic", "account.analytic.line"})
_ROW_KEY = re.compile(r"^(?:bl|aal)[1-9][0-9]*$")
_DECIMAL = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
_POSITION_KEYS = (
    "date",
    "row_key",
    "budget_line_id",
    "line_type",
    "source_model",
    "source_id",
)


class BudgetReportPort(Protocol):
    @property
    def user_id(self) -> int: ...

    def read(
        self, *, company_id: int, parameters: dict[str, Any]
    ) -> dict[str, Any]: ...


class BudgetReportError(RuntimeError):
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


def _invalid(message: str, *, code: str = "invalid_request") -> BudgetReportError:
    return BudgetReportError(code, message, exit_code=2)


def _failed(message: str) -> BudgetReportError:
    return BudgetReportError("failed_validation", message, exit_code=8)


def _integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _positive_id(value: Any) -> bool:
    return _integer(value) and value > 0


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _decimal(value: Any) -> bool:
    if not isinstance(value, str) or len(value) > 256 or not _DECIMAL.fullmatch(value):
        return False
    try:
        return Decimal(value).is_finite()
    except InvalidOperation:
        return False


def _envelope(request: Any) -> tuple[str, dict[str, Any], dict[str, Any]]:
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
    try:
        parsed = uuid.UUID(request_id) if isinstance(request_id, str) else None
    except ValueError as exc:
        raise _invalid("request_id must be a UUID string.") from exc
    if (
        parsed is None
        or str(parsed) != request_id.lower()
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
    if not all(
        _text(context.get(key))
        for key in ("database", "user_login", "language", "timezone")
    ) or not _positive_id(context.get("company_id")):
        raise _invalid("context contains an invalid value.")
    parameters = request["parameters"]
    if not isinstance(parameters, dict):
        raise _invalid("parameters must be an object.")
    return request_id, context, parameters


def validate_budget_report_request(
    request: Any,
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    """Validate and normalize one fixed budget-report request."""

    request_id, context, parameters = _envelope(request)
    allowed = {
        "budget_id",
        "budget_line_id",
        "date_from",
        "date_to",
        "plan_id",
        "analytic_account_id",
        "line_type",
        "limit",
        "cursor",
    }
    if not set(parameters) <= allowed or not _positive_id(parameters.get("budget_id")):
        raise _invalid("parameters must contain one positive integer budget_id.")

    budget_line_id = parameters.get("budget_line_id")
    if budget_line_id is not None and not _positive_id(budget_line_id):
        raise _invalid("parameters.budget_line_id must be null or a positive integer.")
    date_from = parameters.get("date_from")
    date_to = parameters.get("date_to")
    if date_from is not None and not _date(date_from):
        raise _invalid("parameters.date_from must be null or a YYYY-MM-DD date.")
    if date_to is not None and not _date(date_to):
        raise _invalid("parameters.date_to must be null or a YYYY-MM-DD date.")
    if date_from is not None and date_to is not None and date_from > date_to:
        raise _invalid("parameters.date_from cannot be after parameters.date_to.")

    plan_id = parameters.get("plan_id")
    analytic_account_id = parameters.get("analytic_account_id")
    if (plan_id is None) != (analytic_account_id is None) or (
        plan_id is not None
        and (not _positive_id(plan_id) or not _positive_id(analytic_account_id))
    ):
        raise _invalid(
            "parameters.plan_id and parameters.analytic_account_id must be null "
            "together or positive integers together."
        )
    line_type = parameters.get("line_type")
    if line_type is not None and (
        not isinstance(line_type, str) or line_type not in _LINE_TYPES
    ):
        raise _invalid("parameters.line_type must be null, 'budget', or 'achieved'.")
    limit = parameters.get("limit", DEFAULT_LIMIT)
    if not _integer(limit) or not 1 <= limit <= MAX_LIMIT:
        raise _invalid(f"parameters.limit must be between 1 and {MAX_LIMIT}.")
    cursor = parameters.get("cursor")
    if cursor is not None and (
        not isinstance(cursor, str) or not cursor or len(cursor) > 4096
    ):
        raise _invalid("parameters.cursor must be null or a non-empty cursor string.")
    return (
        request_id,
        context,
        {
            "budget_id": parameters["budget_id"],
            "budget_line_id": budget_line_id,
            "date_from": date_from,
            "date_to": date_to,
            "plan_id": plan_id,
            "analytic_account_id": analytic_account_id,
            "line_type": line_type,
            "limit": limit,
            "cursor": cursor,
        },
    )


def _binding(context: dict[str, Any], parameters: dict[str, Any]) -> str:
    return json.dumps(
        {
            "capability": CAPABILITY_ID,
            "company_id": context["company_id"],
            "database": context["database"],
            "filters": {
                key: value
                for key, value in parameters.items()
                if key not in {"limit", "cursor"}
            },
            "user_login": context["user_login"],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _position(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "date": item["date"],
        "row_key": item["row_key"],
        "budget_line_id": item["budget_line"]["id"],
        "line_type": item["line_type"],
        "source_model": item["source"]["model"],
        "source_id": item["source"]["id"],
    }


def _position_tuple(value: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(value[key] for key in _POSITION_KEYS)


def _valid_position(value: Any) -> bool:
    return bool(
        isinstance(value, dict)
        and set(value) == set(_POSITION_KEYS)
        and _date(value["date"])
        and isinstance(value["row_key"], str)
        and _ROW_KEY.fullmatch(value["row_key"])
        and _positive_id(value["budget_line_id"])
        and isinstance(value["line_type"], str)
        and value["line_type"] in _LINE_TYPES
        and isinstance(value["source_model"], str)
        and value["source_model"] in _SOURCE_MODELS
        and _positive_id(value["source_id"])
    )


def _encode_cursor(
    after: dict[str, Any], *, context: dict[str, Any], parameters: dict[str, Any]
) -> str:
    raw = json.dumps(
        {
            "after": after,
            "binding": _binding(context, parameters),
            "version": _CURSOR_VERSION,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate cursor key")
        result[key] = value
    return result


def _reject_float(_value: str) -> None:
    raise ValueError("floating-point cursor number")


def _reject_constant(_value: str) -> None:
    raise ValueError("non-finite cursor number")


def _decode_cursor(
    cursor: str, *, context: dict[str, Any], parameters: dict[str, Any]
) -> dict[str, Any]:
    try:
        raw = base64.b64decode(
            (cursor + "=" * (-len(cursor) % 4)).encode("ascii"),
            altchars=b"-_",
            validate=True,
        )
        value = json.loads(
            raw.decode(),
            object_pairs_hook=_pairs,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
        )
    except (ValueError, UnicodeError, json.JSONDecodeError, binascii.Error) as exc:
        raise _invalid("The cursor is invalid.", code="invalid_cursor") from exc
    if (
        not isinstance(value, dict)
        or set(value) != {"after", "binding", "version"}
        or value["binding"] != _binding(context, parameters)
        or value["version"] != _CURSOR_VERSION
        or not _integer(value["version"])
        or not _valid_position(value["after"])
    ):
        raise _invalid("The cursor does not match this request.", code="invalid_cursor")
    return value["after"]


def _named_ref(value: Any) -> bool:
    return bool(
        isinstance(value, dict)
        and set(value) == {"id", "name"}
        and _positive_id(value["id"])
        and _text(value["name"])
    )


def _valid_item(item: Any, *, company_id: int, budget_id: int) -> bool:
    if not isinstance(item, dict) or set(item) != {
        "row_key",
        "line_type",
        "date",
        "budget",
        "budget_line",
        "source",
        "description",
        "plan_accounts",
        "company_id",
        "user",
        "budget_amount",
        "achieved_amount",
        "theoretical_amount",
    }:
        return False
    budget = item["budget"]
    budget_line = item["budget_line"]
    source = item["source"]
    plan_accounts = item["plan_accounts"]
    if (
        not isinstance(item["row_key"], str)
        or not _ROW_KEY.fullmatch(item["row_key"])
        or not isinstance(item["line_type"], str)
        or item["line_type"] not in _LINE_TYPES
        or not _date(item["date"])
        or not _named_ref(budget)
        or budget["id"] != budget_id
        or not isinstance(budget_line, dict)
        or set(budget_line) != {"id"}
        or not _positive_id(budget_line["id"])
        or not isinstance(source, dict)
        or set(source) != {"model", "id"}
        or not isinstance(source["model"], str)
        or source["model"] not in _SOURCE_MODELS
        or not _positive_id(source["id"])
        or (item["description"] is not None and not _text(item["description"]))
        or not isinstance(plan_accounts, list)
        or (item["company_id"] is not None and item["company_id"] != company_id)
        or (item["user"] is not None and not _named_ref(item["user"]))
        or not all(
            _decimal(item[key])
            for key in ("budget_amount", "achieved_amount", "theoretical_amount")
        )
    ):
        return False
    if item["line_type"] == "budget":
        if item["row_key"] != f"bl{budget_line['id']}" or source != {
            "model": "budget.analytic",
            "id": budget_id,
        }:
            return False
    elif (
        item["row_key"] != f"aal{source['id']}"
        or source["model"] != "account.analytic.line"
    ):
        return False
    if any(
        not isinstance(value, dict)
        or set(value) != {"plan", "account"}
        or not _named_ref(value["plan"])
        or not _named_ref(value["account"])
        for value in plan_accounts
    ):
        return False
    positions = [
        (value["plan"]["id"], value["account"]["id"]) for value in plan_accounts
    ]
    return positions == sorted(set(positions))


def _validated_page(
    port: BudgetReportPort,
    value: Any,
    *,
    company_id: int,
    budget_id: int,
    maximum: int,
) -> list[dict[str, Any]]:
    if not isinstance(value, dict) or set(value) != {
        "user_id",
        "company_visible",
        "module_installed",
        "access_allowed",
        "cursor_found",
        "items",
    }:
        raise _failed("Odoo returned an invalid budget-report page.")
    if (
        not _positive_id(value["user_id"])
        or not _positive_id(port.user_id)
        or value["user_id"] != port.user_id
        or any(
            not isinstance(value[key], bool)
            for key in (
                "company_visible",
                "module_installed",
                "access_allowed",
                "cursor_found",
            )
        )
        or not isinstance(value["items"], list)
        or len(value["items"]) > maximum
        or (
            value["access_allowed"]
            and not (value["company_visible"] and value["module_installed"])
        )
        or (not value["access_allowed"] and value["items"])
    ):
        raise _failed("Odoo returned an inconsistent budget-report page.")
    if not value["company_visible"]:
        raise BudgetReportError(
            "company_unavailable",
            "The requested company is unavailable to the configured user.",
            exit_code=3,
        )
    if not value["module_installed"]:
        raise BudgetReportError(
            "uninstalled",
            "The Odoo budget report is not installed in this database.",
            exit_code=4,
        )
    if not value["access_allowed"]:
        raise BudgetReportError(
            "unauthorized",
            "The configured user cannot read the Odoo budget report.",
            exit_code=3,
        )
    if not value["cursor_found"]:
        raise _invalid("The cursor is no longer present.", code="invalid_cursor")
    items = [dict(item) for item in value["items"]]
    if any(
        not _valid_item(item, company_id=company_id, budget_id=budget_id)
        for item in items
    ):
        raise _failed("Odoo returned an invalid budget-report row.")
    positions = [_position_tuple(_position(item)) for item in items]
    if positions != sorted(positions) or len(positions) != len(set(positions)):
        raise _failed("Odoo returned budget-report rows in an unstable order.")
    return items


def read_budget_report(
    port: BudgetReportPort, request: dict[str, Any]
) -> dict[str, Any]:
    """Read one page of official raw budget execution detail without aggregation."""

    _, context, parameters = validate_budget_report_request(request)
    cursor = parameters["cursor"]
    after = (
        _decode_cursor(cursor, context=context, parameters=parameters)
        if cursor is not None
        else None
    )
    runtime_parameters = {
        **{
            key: value
            for key, value in parameters.items()
            if key not in {"limit", "cursor"}
        },
        "after": after,
        "limit": parameters["limit"] + 1,
    }
    page = port.read(company_id=context["company_id"], parameters=runtime_parameters)
    items = _validated_page(
        port,
        page,
        company_id=context["company_id"],
        budget_id=parameters["budget_id"],
        maximum=parameters["limit"] + 1,
    )
    if after is not None and any(
        _position_tuple(_position(item)) <= _position_tuple(after) for item in items
    ):
        raise _failed("Odoo returned an invalid budget-report cursor page.")
    has_more = len(items) > parameters["limit"]
    visible = items[: parameters["limit"]]
    return {
        "items": visible,
        "has_more": has_more,
        "next_cursor": (
            _encode_cursor(
                _position(visible[-1]), context=context, parameters=parameters
            )
            if has_more
            else None
        ),
    }
