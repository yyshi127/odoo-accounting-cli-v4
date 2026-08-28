"""Closed contracts for period-context reads."""

from __future__ import annotations

import base64
import binascii
import json
import uuid
from datetime import date
from typing import Any, Protocol

PERIOD_CONTEXT_CAPABILITY_IDS = frozenset(
    {
        "company.lock_dates.inspect",
        "company.fiscal_year.resolve",
        "fiscal_year.search",
        "fiscal_year.get",
    }
)
DEFAULT_LIMIT = 100
MAX_LIMIT = 1000
_CURSOR_VERSION = 1
_LOCK_KEYS = frozenset(
    {
        "fiscalyear_lock_date",
        "tax_lock_date",
        "sale_lock_date",
        "purchase_lock_date",
        "hard_lock_date",
    }
)


class PeriodContextPort(Protocol):
    @property
    def user_id(self) -> int: ...

    def read(
        self,
        *,
        capability_id: str,
        company_id: int,
        parameters: dict[str, Any],
    ) -> dict[str, Any]: ...


class PeriodContextReadError(RuntimeError):
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
) -> PeriodContextReadError:
    return PeriodContextReadError(code, message, exit_code=2)


def _failed(message: str) -> PeriodContextReadError:
    return PeriodContextReadError("failed_validation", message, exit_code=8)


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


def validate_period_context_request(
    capability_id: str, request: Any
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    """Validate and normalize one period-context request."""

    if (
        not isinstance(capability_id, str)
        or capability_id not in PERIOD_CONTEXT_CAPABILITY_IDS
    ):
        raise PeriodContextReadError(
            "unsupported_capability",
            "The period-context capability is unsupported.",
            exit_code=4,
        )
    request_id, context, parameters = _envelope(request)

    if capability_id == "company.lock_dates.inspect":
        if parameters:
            raise _invalid("company.lock_dates.inspect accepts no parameters.")
        return request_id, context, {}

    if capability_id == "company.fiscal_year.resolve":
        if set(parameters) != {"date"} or not _date(parameters.get("date")):
            raise _invalid("parameters must contain one YYYY-MM-DD date.")
        return request_id, context, {"date": parameters["date"]}

    if capability_id == "fiscal_year.get":
        if set(parameters) != {"fiscal_year_id"} or not _positive_id(
            parameters.get("fiscal_year_id")
        ):
            raise _invalid(
                "parameters must contain one positive integer fiscal_year_id."
            )
        return request_id, context, {"fiscal_year_id": parameters["fiscal_year_id"]}

    if not set(parameters) <= {
        "contains_date",
        "date_from",
        "date_to",
        "limit",
        "cursor",
    }:
        raise _invalid("fiscal_year.search contains an unsupported parameter.")
    filters = {
        key: parameters.get(key)
        for key in ("contains_date", "date_from", "date_to")
    }
    if any(value is not None and not _date(value) for value in filters.values()):
        raise _invalid("Fiscal-year filters must be null or YYYY-MM-DD dates.")
    if (
        filters["date_from"] is not None
        and filters["date_to"] is not None
        and filters["date_from"] > filters["date_to"]
    ):
        raise _invalid("parameters.date_from cannot be after parameters.date_to.")
    limit = parameters.get("limit", DEFAULT_LIMIT)
    if not _integer(limit) or not 1 <= limit <= MAX_LIMIT:
        raise _invalid(f"parameters.limit must be between 1 and {MAX_LIMIT}.")
    cursor = parameters.get("cursor")
    if cursor is not None and (
        not isinstance(cursor, str) or not cursor or len(cursor) > 4096
    ):
        raise _invalid("parameters.cursor must be null or a non-empty cursor string.")
    return request_id, context, {**filters, "limit": limit, "cursor": cursor}


def _cursor_binding(context: dict[str, Any], parameters: dict[str, Any]) -> str:
    return json.dumps(
        {
            "capability": "fiscal_year.search",
            "company_id": context["company_id"],
            "database": context["database"],
            "filters": {
                key: parameters[key]
                for key in ("contains_date", "date_from", "date_to")
            },
            "user_login": context["user_login"],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _encode_cursor(
    after: list[Any], *, context: dict[str, Any], parameters: dict[str, Any]
) -> str:
    value = json.dumps(
        {
            "after": after,
            "binding": _cursor_binding(context, parameters),
            "version": _CURSOR_VERSION,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate cursor key")
        result[key] = value
    return result


def _reject_json_number(value: str) -> Any:
    raise ValueError(f"invalid JSON number: {value}")


def _decode_cursor(
    cursor: str, *, context: dict[str, Any], parameters: dict[str, Any]
) -> list[Any]:
    try:
        raw = base64.b64decode(
            (cursor + "=" * (-len(cursor) % 4)).encode("ascii"),
            altchars=b"-_",
            validate=True,
        )
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_pairs,
            parse_float=_reject_json_number,
            parse_constant=_reject_json_number,
        )
    except (ValueError, UnicodeError, json.JSONDecodeError, binascii.Error) as exc:
        raise _invalid("The cursor is invalid.", code="invalid_cursor") from exc
    after = value.get("after") if isinstance(value, dict) else None
    if (
        not isinstance(value, dict)
        or set(value) != {"after", "binding", "version"}
        or not _integer(value["version"])
        or value["version"] != _CURSOR_VERSION
        or value["binding"] != _cursor_binding(context, parameters)
        or not isinstance(after, list)
        or len(after) != 2
        or not _date(after[0])
        or not _positive_id(after[1])
    ):
        raise _invalid("The cursor does not match this request.", code="invalid_cursor")
    return after


def _lock_values(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == _LOCK_KEYS
        and all(item is None or _date(item) for item in value.values())
    )


def _lock_result(value: Any, company_id: int) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"company_id", "configured", "effective"}
        and value["company_id"] == company_id
        and _lock_values(value["configured"])
        and _lock_values(value["effective"])
    )


def _fiscal_year_ref(value: Any) -> bool:
    return (
        value is None
        or isinstance(value, dict)
        and set(value) == {"id", "name"}
        and _positive_id(value["id"])
        and _text(value["name"])
    )


def _resolve_result(value: Any, company_id: int, target: str) -> bool:
    return (
        isinstance(value, dict)
        and set(value)
        == {
            "company_id",
            "date",
            "date_from",
            "date_to",
            "fiscal_year",
        }
        and value["company_id"] == company_id
        and value["date"] == target
        and _date(value["date_from"])
        and _date(value["date_to"])
        and value["date_from"] <= target <= value["date_to"]
        and _fiscal_year_ref(value["fiscal_year"])
    )


def _fiscal_year(value: Any, company_id: int) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "name", "company_id", "date_from", "date_to"}
        and _positive_id(value["id"])
        and _text(value["name"])
        and value["company_id"] == company_id
        and _date(value["date_from"])
        and _date(value["date_to"])
        and value["date_from"] <= value["date_to"]
    )


def _matches_filters(value: dict[str, Any], parameters: dict[str, Any]) -> bool:
    contains = parameters["contains_date"]
    requested_from = parameters["date_from"]
    requested_to = parameters["date_to"]
    return (
        (contains is None or value["date_from"] <= contains <= value["date_to"])
        and (requested_from is None or value["date_to"] >= requested_from)
        and (requested_to is None or value["date_from"] <= requested_to)
    )


def _page(port: PeriodContextPort, value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, dict) or set(value) != {
        "user_id",
        "company_visible",
        "module_installed",
        "access_allowed",
        "cursor_found",
        "items",
    }:
        raise _failed("Odoo returned an invalid period-context page.")
    if (
        not _positive_id(value["user_id"])
        or not _positive_id(port.user_id)
        or value["user_id"] != port.user_id
        or not all(
            isinstance(value[key], bool)
            for key in (
                "company_visible",
                "module_installed",
                "access_allowed",
                "cursor_found",
            )
        )
        or not isinstance(value["items"], list)
        or any(not isinstance(item, dict) for item in value["items"])
        or (
            value["access_allowed"]
            and not (value["company_visible"] and value["module_installed"])
        )
        or (not value["access_allowed"] and value["items"])
    ):
        raise _failed("Odoo returned an inconsistent period-context page.")
    return value["items"]


def _availability(page: dict[str, Any]) -> None:
    if not page["company_visible"]:
        raise PeriodContextReadError(
            "company_unavailable",
            "The requested company is unavailable to the configured user.",
            exit_code=3,
        )
    if not page["module_installed"]:
        raise PeriodContextReadError(
            "uninstalled",
            "The period-context capability is not installed in this database.",
            exit_code=4,
        )
    if not page["access_allowed"]:
        raise PeriodContextReadError(
            "unauthorized",
            "The configured user cannot read the requested period context.",
            exit_code=3,
        )


def read_period_context(
    capability_id: str, port: PeriodContextPort, request: dict[str, Any]
) -> dict[str, Any]:
    """Read one verified period-context result."""

    _, context, parameters = validate_period_context_request(capability_id, request)
    runtime_parameters = dict(parameters)
    after: list[Any] | None = None
    if capability_id == "fiscal_year.search":
        if parameters["cursor"] is not None:
            after = _decode_cursor(
                parameters["cursor"], context=context, parameters=parameters
            )
        runtime_parameters = {
            "contains_date": parameters["contains_date"],
            "date_from": parameters["date_from"],
            "date_to": parameters["date_to"],
            "after": after,
            "limit": parameters["limit"] + 1,
        }
    page = port.read(
        capability_id=capability_id,
        company_id=context["company_id"],
        parameters=runtime_parameters,
    )
    items = _page(port, page)
    _availability(page)

    if capability_id == "fiscal_year.search":
        if parameters["cursor"] is not None and not page["cursor_found"]:
            raise _invalid(
                "The cursor no longer resolves in this result set.",
                code="invalid_cursor",
            )
        if len(items) > parameters["limit"] + 1 or any(
            not _fiscal_year(item, context["company_id"])
            or not _matches_filters(item, parameters)
            for item in items
        ):
            raise _failed("Odoo returned invalid fiscal-year search results.")
        order = [(item["date_from"], item["id"]) for item in items]
        if order != sorted(set(order), reverse=True) or (
            after is not None and any(value >= tuple(after) for value in order)
        ):
            raise _failed("Odoo returned unordered fiscal-year search results.")
        has_more = len(items) > parameters["limit"]
        visible = items[: parameters["limit"]]
        return {
            "items": visible,
            "has_more": has_more,
            "next_cursor": (
                _encode_cursor(
                    [visible[-1]["date_from"], visible[-1]["id"]],
                    context=context,
                    parameters=parameters,
                )
                if has_more
                else None
            ),
        }

    if not page["cursor_found"] or len(items) > 1:
        raise _failed("Odoo returned an invalid single period-context result.")
    if capability_id == "fiscal_year.get":
        if not items:
            raise PeriodContextReadError(
                "record_not_found",
                "The requested fiscal year was not found.",
                exit_code=4,
            )
        if (
            not _fiscal_year(items[0], context["company_id"])
            or items[0]["id"] != parameters["fiscal_year_id"]
        ):
            raise _failed("Odoo returned an invalid fiscal-year result.")
        return items[0]

    if len(items) != 1:
        raise _failed("Odoo returned no period-context result.")
    if capability_id == "company.lock_dates.inspect":
        if not _lock_result(items[0], context["company_id"]):
            raise _failed("Odoo returned invalid lock dates.")
    elif not _resolve_result(
        items[0], context["company_id"], parameters["date"]
    ):
        raise _failed("Odoo returned an invalid fiscal-year resolution.")
    return items[0]
