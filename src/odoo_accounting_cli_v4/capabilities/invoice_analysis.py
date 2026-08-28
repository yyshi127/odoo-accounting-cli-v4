"""Closed contracts for Odoo's native invoice-analysis view."""

from __future__ import annotations

import base64
import binascii
import json
import re
import uuid
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol

INVOICE_ANALYSIS_CAPABILITY_IDS = frozenset(
    {"invoice.analysis.search", "invoice.analysis.summary"}
)
MOVE_TYPES = frozenset({"out_invoice", "out_refund", "in_invoice", "in_refund"})
STATES = frozenset({"draft", "posted", "cancel"})
PAYMENT_STATES = frozenset(
    {
        "not_paid",
        "in_payment",
        "paid",
        "partial",
        "reversed",
        "blocked",
        "invoicing_legacy",
    }
)
GROUP_BY_VALUES = frozenset(
    {"move_type", "state", "payment_state", "partner", "product"}
)
DEFAULT_LIMIT = 100
MAX_LIMIT = 1000
_CURSOR_VERSION = 1
_DECIMAL_PATTERN = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")


class InvoiceAnalysisPort(Protocol):
    @property
    def user_id(self) -> int: ...

    def read(
        self,
        *,
        capability_id: str,
        company_id: int,
        parameters: dict[str, Any],
    ) -> dict[str, Any]: ...


class InvoiceAnalysisError(RuntimeError):
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


def _invalid(message: str, *, code: str = "invalid_request") -> InvoiceAnalysisError:
    return InvoiceAnalysisError(code, message, exit_code=2)


def _failed(message: str) -> InvoiceAnalysisError:
    return InvoiceAnalysisError("failed_validation", message, exit_code=8)


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
        parsed = Decimal(value)
    except InvalidOperation:
        return None
    return parsed if parsed.is_finite() else None


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


def _optional_id(parameters: dict[str, Any], key: str) -> int | None:
    value = parameters.get(key)
    if value is not None and not _positive_id(value):
        raise _invalid(f"parameters.{key} must be null or a positive integer.")
    return value


def _optional_enum_list(
    parameters: dict[str, Any], key: str, allowed: frozenset[str]
) -> list[str] | None:
    value = parameters.get(key)
    if value is None:
        return None
    if (
        not isinstance(value, list)
        or not value
        or len(value) > len(allowed)
        or any(not isinstance(item, str) or item not in allowed for item in value)
        or len(set(value)) != len(value)
    ):
        raise _invalid(f"parameters.{key} contains an invalid value set.")
    return sorted(value)


def _filters(parameters: dict[str, Any], *, require_dates: bool) -> dict[str, Any]:
    date_from = parameters.get("date_from")
    date_to = parameters.get("date_to")
    if (date_from is None) != (date_to is None):
        raise _invalid("parameters.date_from and date_to must be supplied together.")
    if require_dates and date_from is None:
        raise _invalid("parameters.date_from and date_to are required.")
    if date_from is not None and (not _date(date_from) or not _date(date_to)):
        raise _invalid("parameters dates must use YYYY-MM-DD syntax.")
    if date_from is not None and date_from > date_to:
        raise _invalid("parameters.date_from cannot be after parameters.date_to.")
    return {
        "date_from": date_from,
        "date_to": date_to,
        "move_types": _optional_enum_list(parameters, "move_types", MOVE_TYPES),
        "states": _optional_enum_list(parameters, "states", STATES),
        "payment_states": _optional_enum_list(
            parameters, "payment_states", PAYMENT_STATES
        ),
        "partner_id": _optional_id(parameters, "partner_id"),
        "product_id": _optional_id(parameters, "product_id"),
    }


def validate_invoice_analysis_request(
    capability_id: str, request: Any
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    """Validate and normalize one invoice-analysis request."""

    if capability_id not in INVOICE_ANALYSIS_CAPABILITY_IDS:
        raise InvoiceAnalysisError(
            "unsupported_capability",
            "The invoice-analysis capability is unsupported.",
            exit_code=4,
        )
    request_id, context, parameters = _envelope(request)
    common = {
        "date_from",
        "date_to",
        "move_types",
        "states",
        "payment_states",
        "partner_id",
        "product_id",
    }
    if capability_id == "invoice.analysis.search":
        if not set(parameters) <= common | {"limit", "cursor"}:
            raise _invalid("invoice.analysis.search contains an unsupported parameter.")
        normalized = _filters(parameters, require_dates=False)
        limit = parameters.get("limit", DEFAULT_LIMIT)
        if not _integer(limit) or not 1 <= limit <= MAX_LIMIT:
            raise _invalid(f"parameters.limit must be between 1 and {MAX_LIMIT}.")
        cursor = parameters.get("cursor")
        if cursor is not None and (
            not isinstance(cursor, str) or not cursor or len(cursor) > 4096
        ):
            raise _invalid("parameters.cursor must be null or non-empty text.")
        normalized.update({"limit": limit, "cursor": cursor})
    else:
        if not {"date_from", "date_to", "group_by"} <= set(parameters) or not set(
            parameters
        ) <= common | {"group_by"}:
            raise _invalid(
                "invoice.analysis.summary requires the fixed filters and group_by."
            )
        normalized = _filters(parameters, require_dates=True)
        group_by = parameters.get("group_by")
        if not isinstance(group_by, str) or group_by not in GROUP_BY_VALUES:
            raise _invalid("parameters.group_by is unsupported.")
        normalized["group_by"] = group_by
    return request_id, context, normalized


def _binding(
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
            "binding": _binding(capability_id, context, parameters),
            "version": _CURSOR_VERSION,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


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
            parse_float=_reject_float,
            parse_constant=_reject_constant,
        )
    except (ValueError, UnicodeError, json.JSONDecodeError, binascii.Error) as exc:
        raise _invalid("The cursor is invalid.", code="invalid_cursor") from exc
    if (
        not isinstance(value, dict)
        or set(value) != {"after", "binding", "version"}
        or not _integer(value["version"])
        or value["version"] != _CURSOR_VERSION
        or value["binding"] != _binding(capability_id, context, parameters)
        or not _positive_id(value["after"])
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


def _optional_ref(value: Any) -> bool:
    return value is None or _named_ref(value)


def _currency(value: Any) -> bool:
    return bool(
        isinstance(value, dict)
        and set(value) == {"id", "code"}
        and _positive_id(value["id"])
        and isinstance(value["code"], str)
        and 1 <= len(value["code"]) <= 3
    )


_SEARCH_ITEM_KEYS = {
    "id",
    "invoice",
    "journal",
    "company_id",
    "company_currency",
    "partner",
    "move_type",
    "state",
    "payment_state",
    "invoice_date",
    "due_date",
    "product",
    "uom",
    "currency",
    "quantity",
    "untaxed_amount_currency",
    "untaxed_amount",
    "total_amount",
    "total_amount_currency",
    "average_price",
    "margin",
    "inventory_value",
}
_AMOUNT_KEYS = (
    "quantity",
    "untaxed_amount_currency",
    "untaxed_amount",
    "total_amount",
    "total_amount_currency",
    "average_price",
    "margin",
    "inventory_value",
)


def _valid_search_item(
    item: Any, *, company_id: int, parameters: dict[str, Any]
) -> bool:
    if not isinstance(item, dict) or set(item) != _SEARCH_ITEM_KEYS:
        return False
    if not (
        _positive_id(item["id"])
        and _named_ref(item["invoice"])
        and _named_ref(item["journal"])
        and item["company_id"] == company_id
        and _currency(item["company_currency"])
        and _optional_ref(item["partner"])
        and item["move_type"] in MOVE_TYPES
        and item["state"] in STATES
        and (item["payment_state"] is None or item["payment_state"] in PAYMENT_STATES)
        and (item["invoice_date"] is None or _date(item["invoice_date"]))
        and (item["due_date"] is None or _date(item["due_date"]))
        and _optional_ref(item["product"])
        and _optional_ref(item["uom"])
        and _currency(item["currency"])
        and all(_decimal(item[key]) is not None for key in _AMOUNT_KEYS)
    ):
        return False
    if parameters["date_from"] is not None and not (
        item["invoice_date"] is not None
        and parameters["date_from"] <= item["invoice_date"] <= parameters["date_to"]
    ):
        return False
    for parameter, field in (
        ("move_types", "move_type"),
        ("states", "state"),
        ("payment_states", "payment_state"),
    ):
        if (
            parameters[parameter] is not None
            and item[field] not in parameters[parameter]
        ):
            return False
    for parameter, field in (("partner_id", "partner"), ("product_id", "product")):
        expected = parameters[parameter]
        if expected is not None and (
            item[field] is None or item[field]["id"] != expected
        ):
            return False
    return True


_SUMMARY_AMOUNT_KEYS = (
    "quantity",
    "untaxed_amount",
    "total_amount",
    "margin",
    "inventory_value",
)


def _group_identity(group: dict[str, Any]) -> tuple[int, str]:
    return (group["id"] or 0, group["value"] or "")


def _valid_summary(value: Any, *, company_id: int, parameters: dict[str, Any]) -> bool:
    if not isinstance(value, dict) or set(value) != {
        "group_by",
        "date_from",
        "date_to",
        "company_id",
        "company_currency",
        "groups",
        "totals",
    }:
        return False
    groups = value["groups"]
    totals = value["totals"]
    if not (
        value["group_by"] == parameters["group_by"]
        and value["date_from"] == parameters["date_from"]
        and value["date_to"] == parameters["date_to"]
        and value["company_id"] == company_id
        and _currency(value["company_currency"])
        and isinstance(groups, list)
        and isinstance(totals, dict)
        and set(totals) == {"row_count", *_SUMMARY_AMOUNT_KEYS}
        and _integer(totals["row_count"])
        and totals["row_count"] >= 0
        and all(_decimal(totals[key]) is not None for key in _SUMMARY_AMOUNT_KEYS)
    ):
        return False
    identities: list[tuple[int, str]] = []
    row_count = 0
    amounts = {key: Decimal(0) for key in _SUMMARY_AMOUNT_KEYS}
    for group in groups:
        if not isinstance(group, dict) or set(group) != {
            "group",
            "row_count",
            *_SUMMARY_AMOUNT_KEYS,
        }:
            return False
        descriptor = group["group"]
        if not (
            isinstance(descriptor, dict)
            and set(descriptor) == {"id", "value"}
            and (descriptor["id"] is None or _positive_id(descriptor["id"]))
            and (descriptor["value"] is None or _text(descriptor["value"]))
            and _integer(group["row_count"])
            and group["row_count"] > 0
            and all(_decimal(group[key]) is not None for key in _SUMMARY_AMOUNT_KEYS)
        ):
            return False
        if parameters["group_by"] in {"partner", "product"}:
            if (descriptor["id"] is None) != (descriptor["value"] is None):
                return False
        elif descriptor["id"] is not None:
            return False
        allowed = {
            "move_type": MOVE_TYPES,
            "state": STATES,
            "payment_state": PAYMENT_STATES,
        }.get(parameters["group_by"])
        if (
            allowed is not None
            and descriptor["value"] is not None
            and descriptor["value"] not in allowed
        ):
            return False
        identities.append(_group_identity(descriptor))
        row_count += group["row_count"]
        for key in _SUMMARY_AMOUNT_KEYS:
            amounts[key] += _decimal(group[key])
    if identities != sorted(set(identities)) or row_count != totals["row_count"]:
        return False
    return all(amounts[key] == _decimal(totals[key]) for key in _SUMMARY_AMOUNT_KEYS)


def _check_scope(page: dict[str, Any]) -> None:
    if not page["company_visible"]:
        raise InvoiceAnalysisError(
            "company_unavailable", "The company is unavailable.", exit_code=3
        )
    if not page["module_installed"]:
        raise InvoiceAnalysisError(
            "uninstalled", "The invoice analysis is unavailable.", exit_code=4
        )
    if not page["access_allowed"]:
        raise InvoiceAnalysisError(
            "unauthorized", "The configured user is not authorized.", exit_code=3
        )


def read_invoice_analysis(
    port: InvoiceAnalysisPort, capability_id: str, request: Any
) -> dict[str, Any]:
    """Execute one validated invoice-analysis read."""

    _, context, parameters = validate_invoice_analysis_request(capability_id, request)
    runtime_parameters = {
        key: value for key, value in parameters.items() if key != "cursor"
    }
    if capability_id == "invoice.analysis.search":
        cursor = parameters["cursor"]
        after = (
            None
            if cursor is None
            else _decode_cursor(
                cursor,
                capability_id=capability_id,
                context=context,
                parameters=parameters,
            )
        )
        runtime_parameters["after"] = after
        runtime_parameters["limit"] = parameters["limit"] + 1
    page = port.read(
        capability_id=capability_id,
        company_id=context["company_id"],
        parameters=runtime_parameters,
    )
    _check_scope(page)
    if capability_id == "invoice.analysis.search":
        if not page["cursor_found"]:
            raise _invalid("The cursor no longer exists.", code="invalid_cursor")
        items = page["items"]
        if len(items) > parameters["limit"] + 1 or any(
            not _valid_search_item(
                item, company_id=context["company_id"], parameters=parameters
            )
            for item in items
        ):
            raise _failed("The Odoo invoice-analysis rows failed validation.")
        ids = [item["id"] for item in items]
        if ids != sorted(set(ids), reverse=True) or (
            runtime_parameters["after"] is not None
            and any(item_id >= runtime_parameters["after"] for item_id in ids)
        ):
            raise _failed("The Odoo invoice-analysis order failed validation.")
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

    if (
        not page["cursor_found"]
        or len(page["items"]) != 1
        or not _valid_summary(
            page["items"][0], company_id=context["company_id"], parameters=parameters
        )
    ):
        raise _failed("The Odoo invoice-analysis summary failed validation.")
    return page["items"][0]
