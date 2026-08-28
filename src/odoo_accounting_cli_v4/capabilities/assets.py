"""Closed contracts for the three fixed-asset read capabilities."""

from __future__ import annotations

import base64
import binascii
import json
import re
import uuid
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol

ASSET_CAPABILITY_IDS = frozenset(
    {
        "asset.search",
        "asset.get",
        "asset.depreciation_schedule.get",
    }
)
ASSET_STATES = frozenset({"draft", "open", "paused", "close", "cancelled"})
DEFAULT_LIMIT = 100
MAX_LIMIT = 1000
_CURSOR_VERSION = 1
_DECIMAL_PATTERN = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
_METHODS = frozenset({"linear", "degressive", "degressive_then_linear"})
_METHOD_PERIODS = frozenset({"1", "12"})
_PRORATA_TYPES = frozenset({"none", "constant_periods", "daily_computation"})
_MOVE_STATES = frozenset({"draft", "posted", "cancel"})


class AssetPort(Protocol):
    @property
    def user_id(self) -> int: ...

    def read(
        self,
        *,
        capability_id: str,
        company_id: int,
        parameters: dict[str, Any],
    ) -> dict[str, Any]: ...


class AssetReadError(RuntimeError):
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


def _invalid(message: str, *, code: str = "invalid_request") -> AssetReadError:
    return AssetReadError(code, message, exit_code=2)


def _failed(message: str) -> AssetReadError:
    return AssetReadError("failed_validation", message, exit_code=8)


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


def _decimal(value: Any) -> Decimal | None:
    if (
        not isinstance(value, str)
        or len(value) > 256
        or _DECIMAL_PATTERN.fullmatch(value) is None
    ):
        return None
    try:
        result = Decimal(value)
    except InvalidOperation:
        return None
    return result if result.is_finite() else None


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


def validate_asset_request(
    capability_id: str, request: Any
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    """Validate and normalize one asset request."""

    if not isinstance(capability_id, str) or capability_id not in ASSET_CAPABILITY_IDS:
        raise AssetReadError(
            "unsupported_capability",
            "The asset capability is unsupported.",
            exit_code=4,
        )
    request_id, context, parameters = _envelope(request)
    if capability_id != "asset.search":
        if set(parameters) != {"asset_id"} or not _positive_id(
            parameters.get("asset_id")
        ):
            raise _invalid("parameters must contain one positive integer asset_id.")
        return request_id, context, {"asset_id": parameters["asset_id"]}

    if not set(parameters) <= {"query", "states", "limit", "cursor"}:
        raise _invalid("asset.search contains an unsupported parameter.")
    query = parameters.get("query")
    if query is not None and (
        not isinstance(query, str)
        or not query
        or query != query.strip()
        or len(query) > 200
    ):
        raise _invalid("parameters.query must be null or trimmed non-empty text.")
    raw_states = parameters.get("states")
    if raw_states is None:
        states = sorted(ASSET_STATES)
    elif (
        not isinstance(raw_states, list)
        or not raw_states
        or len(raw_states) > len(ASSET_STATES)
        or any(
            not isinstance(state, str) or state not in ASSET_STATES
            for state in raw_states
        )
        or len(set(raw_states)) != len(raw_states)
    ):
        raise _invalid("parameters.states contains an invalid asset state set.")
    else:
        states = sorted(raw_states)
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
            "query": query,
            "states": states,
            "limit": limit,
            "cursor": cursor,
        },
    )


def _cursor_binding(context: dict[str, Any], parameters: dict[str, Any]) -> str:
    return json.dumps(
        {
            "capability": "asset.search",
            "company_id": context["company_id"],
            "database": context["database"],
            "query": parameters["query"],
            "states": parameters["states"],
            "user_login": context["user_login"],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _encode_cursor(
    after: int, *, context: dict[str, Any], parameters: dict[str, Any]
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
    ).encode()
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate cursor key")
        result[key] = value
    return result


def _decode_cursor(
    cursor: str, *, context: dict[str, Any], parameters: dict[str, Any]
) -> int:
    try:
        raw = base64.b64decode(
            (cursor + "=" * (-len(cursor) % 4)).encode("ascii"),
            altchars=b"-_",
            validate=True,
        )
        value = json.loads(raw.decode(), object_pairs_hook=_pairs)
    except (ValueError, UnicodeError, json.JSONDecodeError, binascii.Error) as exc:
        raise _invalid("The cursor is invalid.", code="invalid_cursor") from exc
    if (
        not isinstance(value, dict)
        or set(value) != {"after", "binding", "version"}
        or not _integer(value["version"])
        or value["version"] != _CURSOR_VERSION
        or value["binding"] != _cursor_binding(context, parameters)
        or not _positive_id(value["after"])
    ):
        raise _invalid("The cursor does not match this request.", code="invalid_cursor")
    return value["after"]


def _currency(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "code"}
        and _positive_id(value["id"])
        and _text(value["code"])
        and len(value["code"]) <= 3
    )


def _account(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "code", "name"}
        and _positive_id(value["id"])
        and _text(value["code"])
        and _text(value["name"])
    )


def _optional_account(value: Any) -> bool:
    return value is None or _account(value)


def _journal(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "code", "name"}
        and _positive_id(value["id"])
        and _text(value["code"])
        and _text(value["name"])
    )


def _optional_journal(value: Any) -> bool:
    return value is None or _journal(value)


def _summary(value: Any, *, company_id: int, states: list[str] | None = None) -> bool:
    return (
        isinstance(value, dict)
        and set(value)
        == {
            "id",
            "name",
            "state",
            "company_id",
            "currency",
            "acquisition_date",
            "original_value",
            "book_value",
        }
        and _positive_id(value["id"])
        and _text(value["name"])
        and value["state"] in ASSET_STATES
        and (states is None or value["state"] in states)
        and value["company_id"] == company_id
        and _currency(value["currency"])
        and _date(value["acquisition_date"])
        and _decimal(value["original_value"]) is not None
        and _decimal(value["book_value"]) is not None
    )


def _detail(value: Any, *, company_id: int, asset_id: int) -> bool:
    if not isinstance(value, dict) or set(value) != {
        "id",
        "name",
        "state",
        "active",
        "company_id",
        "currency",
        "accounts",
        "journal",
        "values",
        "method",
        "dates",
    }:
        return False
    accounts = value["accounts"]
    values = value["values"]
    method = value["method"]
    dates = value["dates"]
    return (
        value["id"] == asset_id
        and _text(value["name"])
        and value["state"] in ASSET_STATES
        and isinstance(value["active"], bool)
        and value["company_id"] == company_id
        and _currency(value["currency"])
        and isinstance(accounts, dict)
        and set(accounts) == {"asset", "depreciation", "expense"}
        and all(_optional_account(account) for account in accounts.values())
        and _optional_journal(value["journal"])
        and isinstance(values, dict)
        and set(values) == {"original", "salvage", "depreciable", "book", "residual"}
        and all(_decimal(amount) is not None for amount in values.values())
        and isinstance(method, dict)
        and set(method)
        == {
            "type",
            "number",
            "period",
            "progress_factor",
            "prorata_computation_type",
        }
        and method["type"] in _METHODS
        and _integer(method["number"])
        and method["number"] >= 0
        and method["period"] in _METHOD_PERIODS
        and _decimal(method["progress_factor"]) is not None
        and method["prorata_computation_type"] in _PRORATA_TYPES
        and isinstance(dates, dict)
        and set(dates) == {"acquisition", "prorata", "disposal"}
        and _date(dates["acquisition"])
        and _date(dates["prorata"])
        and (dates["disposal"] is None or _date(dates["disposal"]))
    )


def _move(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value)
        == {
            "id",
            "name",
            "date",
            "state",
            "auto_post",
            "journal",
            "depreciation_value",
            "cumulative_depreciation",
            "remaining_value",
            "line_ids",
        }
        and _positive_id(value["id"])
        and (value["name"] is None or _text(value["name"]))
        and _date(value["date"])
        and value["state"] in _MOVE_STATES
        and _text(value["auto_post"])
        and _journal(value["journal"])
        and _decimal(value["depreciation_value"]) is not None
        and _decimal(value["cumulative_depreciation"]) is not None
        and _decimal(value["remaining_value"]) is not None
        and isinstance(value["line_ids"], list)
        and all(_positive_id(line_id) for line_id in value["line_ids"])
        and value["line_ids"] == sorted(set(value["line_ids"]))
    )


def _page(port: AssetPort, value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, dict) or set(value) != {
        "user_id",
        "company_visible",
        "module_installed",
        "access_allowed",
        "cursor_found",
        "items",
    }:
        raise _failed("Odoo returned an invalid asset page.")
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
        raise _failed("Odoo returned an inconsistent asset page.")
    return value["items"]


def _availability(page: dict[str, Any]) -> None:
    if not page["company_visible"]:
        raise AssetReadError(
            "company_unavailable",
            "The requested company is unavailable to the configured user.",
            exit_code=3,
        )
    if not page["module_installed"]:
        raise AssetReadError(
            "uninstalled",
            "The asset capability is not installed in this database.",
            exit_code=4,
        )
    if not page["access_allowed"]:
        raise AssetReadError(
            "unauthorized",
            "The configured user cannot read fixed assets.",
            exit_code=3,
        )


def read_assets(
    capability_id: str, port: AssetPort, request: dict[str, Any]
) -> dict[str, Any]:
    """Read one validated asset result through the fixed asset port."""

    _, context, parameters = validate_asset_request(capability_id, request)
    runtime_parameters = dict(parameters)
    if capability_id == "asset.search":
        cursor = parameters["cursor"]
        runtime_parameters = {
            "query": parameters["query"],
            "states": parameters["states"],
            "after": (
                None
                if cursor is None
                else _decode_cursor(cursor, context=context, parameters=parameters)
            ),
            "limit": parameters["limit"] + 1,
        }
    page = port.read(
        capability_id=capability_id,
        company_id=context["company_id"],
        parameters=runtime_parameters,
    )
    items = _page(port, page)
    _availability(page)

    if capability_id == "asset.search":
        if parameters["cursor"] is not None and not page["cursor_found"]:
            raise _invalid(
                "The cursor no longer resolves in this result set.",
                code="invalid_cursor",
            )
        if len(items) > parameters["limit"] + 1 or any(
            not _summary(
                item,
                company_id=context["company_id"],
                states=parameters["states"],
            )
            for item in items
        ):
            raise _failed("Odoo returned invalid asset search results.")
        ids = [item["id"] for item in items]
        if ids != sorted(set(ids), reverse=True):
            raise _failed("Odoo returned unordered asset search results.")
        has_more = len(items) > parameters["limit"]
        visible = items[: parameters["limit"]]
        return {
            "items": visible,
            "has_more": has_more,
            "next_cursor": (
                _encode_cursor(
                    visible[-1]["id"], context=context, parameters=parameters
                )
                if has_more
                else None
            ),
        }

    if not page["cursor_found"] or len(items) > 1:
        raise _failed("Odoo returned an invalid single-asset result.")
    if not items:
        raise AssetReadError(
            "record_not_found", "The requested asset was not found.", exit_code=4
        )
    asset_id = parameters["asset_id"]
    if capability_id == "asset.get":
        if not _detail(items[0], company_id=context["company_id"], asset_id=asset_id):
            raise _failed("Odoo returned an invalid asset detail.")
        return items[0]

    data = items[0]
    if not isinstance(data, dict) or set(data) != {"asset", "moves"}:
        raise _failed("Odoo returned an invalid depreciation schedule.")
    moves = data["moves"]
    if (
        not _summary(data["asset"], company_id=context["company_id"])
        or data["asset"]["id"] != asset_id
        or not isinstance(moves, list)
        or any(not _move(move) for move in moves)
        or len({move["id"] for move in moves}) != len(moves)
        or moves != sorted(moves, key=lambda move: (move["date"], move["id"]))
    ):
        raise _failed("Odoo returned an invalid depreciation schedule.")
    return data
