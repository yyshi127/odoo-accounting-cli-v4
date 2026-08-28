"""Closed contracts for Odoo 19 accounting-return reads."""

from __future__ import annotations

import base64
import binascii
import json
import uuid
from datetime import date
from typing import Any, Protocol

ACCOUNT_RETURN_CAPABILITY_IDS = frozenset(
    {
        "account.return.search",
        "account.return.get",
        "account.return.summary",
        "account.return.type.list",
        "account.return.check.list",
        "account.return.check.get",
    }
)
RETURN_STATES = frozenset({"new", "reviewed", "submitted", "paid"})
RETURN_CATEGORIES = frozenset({"account_return", "audit"})
CHECK_TYPES = frozenset({"check", "file"})
CHECK_RESULTS = frozenset({"todo", "reviewed", "supervised", "anomaly"})
WORKFLOWS = frozenset(
    {
        "generic_state_review",
        "generic_state_review_submit",
        "generic_state_tax_report",
        "generic_state_only_pay",
    }
)
PERIODICITIES = frozenset(
    {"monthly", "2_months", "trimester", "4_months", "semester", "year"}
)
DEFAULT_LIMIT = 100
MAX_LIMIT = 1000
_CURSOR_VERSION = 1
_PAGED_CAPABILITIES = frozenset(
    {
        "account.return.search",
        "account.return.type.list",
        "account.return.check.list",
    }
)


class AccountReturnPort(Protocol):
    @property
    def user_id(self) -> int: ...

    def read(
        self,
        *,
        capability_id: str,
        company_id: int,
        parameters: dict[str, Any],
    ) -> dict[str, Any]: ...


class AccountReturnReadError(RuntimeError):
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


def _invalid(message: str, *, code: str = "invalid_request") -> AccountReturnReadError:
    return AccountReturnReadError(code, message, exit_code=2)


def _failed(message: str) -> AccountReturnReadError:
    return AccountReturnReadError("failed_validation", message, exit_code=8)


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


def _optional_date(value: Any) -> bool:
    return value is None or _date(value)


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


def _limit_cursor(parameters: dict[str, Any]) -> tuple[int, str | None]:
    limit = parameters.get("limit", DEFAULT_LIMIT)
    cursor = parameters.get("cursor")
    if not _integer(limit) or not 1 <= limit <= MAX_LIMIT:
        raise _invalid(f"parameters.limit must be between 1 and {MAX_LIMIT}.")
    if cursor is not None and (
        not isinstance(cursor, str) or not cursor or len(cursor) > 4096
    ):
        raise _invalid("parameters.cursor must be null or non-empty text.")
    return limit, cursor


def validate_account_return_request(
    capability_id: str, request: Any
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    """Validate and normalize one accounting-return request."""

    if capability_id not in ACCOUNT_RETURN_CAPABILITY_IDS:
        raise AccountReturnReadError(
            "unsupported_capability",
            "The accounting-return capability is unsupported.",
            exit_code=4,
        )
    request_id, context, parameters = _envelope(request)

    if capability_id == "account.return.get":
        if set(parameters) != {"return_id"} or not _positive_id(
            parameters.get("return_id")
        ):
            raise _invalid("parameters must contain one positive return_id.")
        normalized = {"return_id": parameters["return_id"]}
    elif capability_id == "account.return.summary":
        if set(parameters) != {"as_of"} or not _date(parameters.get("as_of")):
            raise _invalid("parameters must contain one YYYY-MM-DD as_of date.")
        normalized = {"as_of": parameters["as_of"]}
    elif capability_id == "account.return.check.get":
        if set(parameters) != {"check_id"} or not _positive_id(
            parameters.get("check_id")
        ):
            raise _invalid("parameters must contain one positive check_id.")
        normalized = {"check_id": parameters["check_id"]}
    elif capability_id == "account.return.search":
        allowed = {
            "type_id",
            "state",
            "completed",
            "deadline_from",
            "deadline_to",
            "active",
            "limit",
            "cursor",
        }
        if not set(parameters) <= allowed:
            raise _invalid("account.return.search contains an unsupported parameter.")
        type_id = parameters.get("type_id")
        state = parameters.get("state")
        completed = parameters.get("completed")
        deadline_from = parameters.get("deadline_from")
        deadline_to = parameters.get("deadline_to")
        active = parameters.get("active", True)
        if type_id is not None and not _positive_id(type_id):
            raise _invalid("parameters.type_id must be null or a positive integer.")
        if state is not None and state not in RETURN_STATES:
            raise _invalid("parameters.state is unsupported.")
        if completed is not None and not isinstance(completed, bool):
            raise _invalid("parameters.completed must be null or boolean.")
        if not _optional_date(deadline_from) or not _optional_date(deadline_to):
            raise _invalid("Deadline filters must be null or YYYY-MM-DD dates.")
        if (
            deadline_from is not None
            and deadline_to is not None
            and deadline_from > deadline_to
        ):
            raise _invalid("parameters.deadline_from cannot be after deadline_to.")
        if active is not None and not isinstance(active, bool):
            raise _invalid("parameters.active must be null or boolean.")
        limit, cursor = _limit_cursor(parameters)
        normalized = {
            "type_id": type_id,
            "state": state,
            "completed": completed,
            "deadline_from": deadline_from,
            "deadline_to": deadline_to,
            "active": active,
            "limit": limit,
            "cursor": cursor,
        }
    elif capability_id == "account.return.type.list":
        if not set(parameters) <= {"category", "limit", "cursor"}:
            raise _invalid("account.return.type.list has an unsupported parameter.")
        category = parameters.get("category")
        if category is not None and category not in RETURN_CATEGORIES:
            raise _invalid("parameters.category is unsupported.")
        limit, cursor = _limit_cursor(parameters)
        normalized = {"category": category, "limit": limit, "cursor": cursor}
    else:
        if not {"return_id"} <= set(parameters) or not set(parameters) <= {
            "return_id",
            "result",
            "type",
            "limit",
            "cursor",
        }:
            raise _invalid("account.return.check.list requires return_id.")
        return_id = parameters.get("return_id")
        result = parameters.get("result")
        check_type = parameters.get("type")
        if not _positive_id(return_id):
            raise _invalid("parameters.return_id must be a positive integer.")
        if result is not None and result not in CHECK_RESULTS:
            raise _invalid("parameters.result is unsupported.")
        if check_type is not None and check_type not in CHECK_TYPES:
            raise _invalid("parameters.type is unsupported.")
        limit, cursor = _limit_cursor(parameters)
        normalized = {
            "return_id": return_id,
            "result": result,
            "type": check_type,
            "limit": limit,
            "cursor": cursor,
        }
    return request_id, context, normalized


def _cursor_binding(
    capability_id: str, context: dict[str, Any], parameters: dict[str, Any]
) -> str:
    return json.dumps(
        {
            "capability": capability_id,
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


def _encode_cursor(
    after: int,
    *,
    capability_id: str,
    context: dict[str, Any],
    parameters: dict[str, Any],
) -> str:
    raw = json.dumps(
        {
            "after": after,
            "binding": _cursor_binding(capability_id, context, parameters),
            "version": _CURSOR_VERSION,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate cursor key")
        result[key] = value
    return result


def _reject_number(_value: str) -> None:
    raise ValueError("unsupported cursor number")


def _decode_cursor(
    cursor: str,
    *,
    capability_id: str,
    context: dict[str, Any],
    parameters: dict[str, Any],
) -> int:
    try:
        raw = base64.b64decode(
            (cursor + "=" * (-len(cursor) % 4)).encode("ascii"),
            altchars=b"-_",
            validate=True,
        )
        value = json.loads(
            raw.decode(),
            object_pairs_hook=_pairs,
            parse_float=_reject_number,
            parse_constant=_reject_number,
        )
    except (ValueError, UnicodeError, json.JSONDecodeError, binascii.Error) as exc:
        raise _invalid("The cursor is invalid.", code="invalid_cursor") from exc
    if (
        not isinstance(value, dict)
        or set(value) != {"after", "binding", "version"}
        or value["version"] != _CURSOR_VERSION
        or not _integer(value["version"])
        or value["binding"] != _cursor_binding(capability_id, context, parameters)
        or not _positive_id(value["after"])
    ):
        raise _invalid("The cursor does not match this request.", code="invalid_cursor")
    return value["after"]


def _named(value: Any) -> bool:
    return bool(
        isinstance(value, dict)
        and set(value) == {"id", "name"}
        and _positive_id(value["id"])
        and _text(value["name"])
    )


def _return_type(value: Any) -> bool:
    return bool(
        isinstance(value, dict)
        and set(value) == {"id", "name", "category"}
        and _positive_id(value["id"])
        and _text(value["name"])
        and value["category"] in RETURN_CATEGORIES
    )


_RETURN_KEYS = {
    "id",
    "name",
    "active",
    "date_from",
    "date_to",
    "date_deadline",
    "date_submission",
    "date_lock",
    "type",
    "state",
    "next_state",
    "is_completed",
    "company_id",
    "tax_unit_id",
    "manually_created",
    "check_counts",
}


def _valid_return(
    value: Any, *, company_id: int, parameters: dict[str, Any] | None = None
) -> bool:
    if not isinstance(value, dict) or set(value) != _RETURN_KEYS:
        return False
    counts = value["check_counts"]
    if not (
        _positive_id(value["id"])
        and _text(value["name"])
        and isinstance(value["active"], bool)
        and _date(value["date_from"])
        and _date(value["date_to"])
        and value["date_from"] <= value["date_to"]
        and _date(value["date_deadline"])
        and _optional_date(value["date_submission"])
        and _optional_date(value["date_lock"])
        and _return_type(value["type"])
        and value["state"] in RETURN_STATES
        and (value["next_state"] is None or value["next_state"] in RETURN_STATES)
        and isinstance(value["is_completed"], bool)
        and value["company_id"] == company_id
        and (value["tax_unit_id"] is None or _positive_id(value["tax_unit_id"]))
        and isinstance(value["manually_created"], bool)
        and isinstance(counts, dict)
        and set(counts) == {"total", "unresolved", "resolved"}
        and all(_integer(item) and item >= 0 for item in counts.values())
        and counts["total"] == counts["unresolved"] + counts["resolved"]
    ):
        return False
    if parameters is None:
        return True
    return bool(
        (parameters["type_id"] is None or value["type"]["id"] == parameters["type_id"])
        and (parameters["state"] is None or value["state"] == parameters["state"])
        and (
            parameters["completed"] is None
            or value["is_completed"] == parameters["completed"]
        )
        and (
            parameters["deadline_from"] is None
            or value["date_deadline"] >= parameters["deadline_from"]
        )
        and (
            parameters["deadline_to"] is None
            or value["date_deadline"] <= parameters["deadline_to"]
        )
        and (parameters["active"] is None or value["active"] == parameters["active"])
    )


_TYPE_KEYS = {
    "id",
    "name",
    "company_id",
    "category",
    "report",
    "country",
    "auto_generate",
    "states_workflow",
    "deadline_periodicity",
    "deadline_start_date",
    "deadline_days_delay",
}


def _valid_type(value: Any, *, company_id: int, category: str | None) -> bool:
    return bool(
        isinstance(value, dict)
        and set(value) == _TYPE_KEYS
        and _positive_id(value["id"])
        and _text(value["name"])
        and value["company_id"] == company_id
        and value["category"] in RETURN_CATEGORIES
        and (category is None or value["category"] == category)
        and (value["report"] is None or _named(value["report"]))
        and (value["country"] is None or _named(value["country"]))
        and isinstance(value["auto_generate"], bool)
        and value["states_workflow"] in WORKFLOWS
        and (
            value["deadline_periodicity"] is None
            or value["deadline_periodicity"] in PERIODICITIES
        )
        and _optional_date(value["deadline_start_date"])
        and _integer(value["deadline_days_delay"])
    )


_CHECK_KEYS = {
    "id",
    "return",
    "code",
    "type",
    "name",
    "message",
    "state",
    "result",
    "records_count",
}


def _valid_check(value: Any, parameters: dict[str, Any] | None = None) -> bool:
    if not (
        isinstance(value, dict)
        and set(value) == _CHECK_KEYS
        and _positive_id(value["id"])
        and _named(value["return"])
        and _text(value["code"])
        and value["type"] in CHECK_TYPES
        and _text(value["name"])
        and (value["message"] is None or isinstance(value["message"], str))
        and value["state"] in RETURN_STATES
        and value["result"] in CHECK_RESULTS
        and _integer(value["records_count"])
        and value["records_count"] >= 0
    ):
        return False
    if parameters is None:
        return True
    return bool(
        value["return"]["id"] == parameters["return_id"]
        and (parameters["result"] is None or value["result"] == parameters["result"])
        and (parameters["type"] is None or value["type"] == parameters["type"])
    )


def _valid_summary(value: Any, *, company_id: int, as_of: str) -> bool:
    if not isinstance(value, dict) or set(value) != {"company_id", "as_of", "counts"}:
        return False
    counts = value["counts"]
    if not (
        value["company_id"] == company_id
        and value["as_of"] == as_of
        and isinstance(counts, dict)
        and set(counts)
        == {
            "total",
            "open",
            "completed",
            "overdue",
            "due_today",
            "due_next_30_days",
            "later",
        }
        and all(_integer(item) and item >= 0 for item in counts.values())
    ):
        return False
    return bool(
        counts["total"] == counts["open"] + counts["completed"]
        and counts["open"]
        == counts["overdue"]
        + counts["due_today"]
        + counts["due_next_30_days"]
        + counts["later"]
    )


def _page(port: AccountReturnPort, value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, dict) or set(value) != {
        "user_id",
        "company_visible",
        "module_installed",
        "access_allowed",
        "cursor_found",
        "items",
    }:
        raise _failed("Odoo returned an invalid accounting-return page.")
    if not (
        _positive_id(value["user_id"])
        and value["user_id"] == port.user_id
        and all(
            isinstance(value[key], bool)
            for key in (
                "company_visible",
                "module_installed",
                "access_allowed",
                "cursor_found",
            )
        )
        and isinstance(value["items"], list)
        and all(isinstance(item, dict) for item in value["items"])
        and (
            not value["access_allowed"]
            or value["company_visible"]
            and value["module_installed"]
        )
        and (value["access_allowed"] or not value["items"])
    ):
        raise _failed("Odoo returned an inconsistent accounting-return page.")
    return value["items"]


def _availability(page: dict[str, Any]) -> None:
    if not page["company_visible"]:
        raise AccountReturnReadError(
            "company_unavailable",
            "The requested company is unavailable to the configured user.",
            exit_code=3,
        )
    if not page["module_installed"]:
        raise AccountReturnReadError(
            "uninstalled",
            "Accounting returns are not installed in this database.",
            exit_code=4,
        )
    if not page["access_allowed"]:
        raise AccountReturnReadError(
            "unauthorized",
            "The configured user cannot read accounting returns.",
            exit_code=3,
        )


def _paged_result(
    items: list[dict[str, Any]],
    *,
    capability_id: str,
    context: dict[str, Any],
    parameters: dict[str, Any],
    after: int | None,
    validator: Any,
) -> dict[str, Any]:
    if len(items) > parameters["limit"] + 1 or any(
        not validator(item) for item in items
    ):
        raise _failed("Odoo returned invalid accounting-return rows.")
    ids = [item["id"] for item in items]
    if ids != sorted(set(ids), reverse=True) or (
        after is not None and any(item_id >= after for item_id in ids)
    ):
        raise _failed("Odoo returned unordered accounting-return rows.")
    has_more = len(items) > parameters["limit"]
    visible = items[: parameters["limit"]]
    return {
        "items": visible,
        "has_more": has_more,
        "next_cursor": (
            _encode_cursor(
                visible[-1]["id"],
                capability_id=capability_id,
                context=context,
                parameters=parameters,
            )
            if has_more
            else None
        ),
    }


def read_account_return(
    port: AccountReturnPort, capability_id: str, request: Any
) -> dict[str, Any]:
    """Execute one validated accounting-return read."""

    _, context, parameters = validate_account_return_request(capability_id, request)
    runtime_parameters = dict(parameters)
    after: int | None = None
    if capability_id in _PAGED_CAPABILITIES:
        if parameters["cursor"] is not None:
            after = _decode_cursor(
                parameters["cursor"],
                capability_id=capability_id,
                context=context,
                parameters=parameters,
            )
        runtime_parameters = {
            key: value
            for key, value in parameters.items()
            if key not in {"cursor", "limit"}
        }
        runtime_parameters.update({"after": after, "limit": parameters["limit"] + 1})

    page = port.read(
        capability_id=capability_id,
        company_id=context["company_id"],
        parameters=runtime_parameters,
    )
    items = _page(port, page)
    _availability(page)

    if capability_id in _PAGED_CAPABILITIES:
        if parameters["cursor"] is not None and not page["cursor_found"]:
            raise _invalid("The cursor no longer resolves.", code="invalid_cursor")
        if capability_id == "account.return.search":
            validator = lambda item: _valid_return(
                item, company_id=context["company_id"], parameters=parameters
            )
        elif capability_id == "account.return.type.list":
            validator = lambda item: _valid_type(
                item,
                company_id=context["company_id"],
                category=parameters["category"],
            )
        else:
            validator = lambda item: _valid_check(item, parameters)
        return _paged_result(
            items,
            capability_id=capability_id,
            context=context,
            parameters=parameters,
            after=after,
            validator=validator,
        )

    if not page["cursor_found"] or len(items) > 1:
        raise _failed("Odoo returned an invalid single accounting-return result.")
    if not items:
        raise AccountReturnReadError(
            "record_not_found",
            "The requested accounting-return record was not found.",
            exit_code=4,
        )
    item = items[0]
    if capability_id == "account.return.get":
        valid = _valid_return(item, company_id=context["company_id"])
        valid = valid and item["id"] == parameters["return_id"]
    elif capability_id == "account.return.summary":
        valid = _valid_summary(
            item, company_id=context["company_id"], as_of=parameters["as_of"]
        )
    else:
        valid = _valid_check(item) and item["id"] == parameters["check_id"]
    if not valid:
        raise _failed("Odoo returned an invalid accounting-return result.")
    return item
