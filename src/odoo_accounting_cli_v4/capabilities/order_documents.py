"""Closed contracts for sales- and purchase-order document reads."""

from __future__ import annotations

import base64
import binascii
import json
import re
import uuid
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol

ORDER_DOCUMENT_CAPABILITY_IDS = frozenset(
    {
        "sale.order.search",
        "sale.order.get",
        "sale.order.line.search",
        "sale.order.analysis.summary",
        "purchase.order.search",
        "purchase.order.get",
        "purchase.order.line.search",
        "purchase.order.analysis.summary",
    }
)
SEARCH_CAPABILITY_IDS = frozenset({"sale.order.search", "purchase.order.search"})
GET_CAPABILITY_IDS = frozenset({"sale.order.get", "purchase.order.get"})
LINE_SEARCH_CAPABILITY_IDS = frozenset(
    {"sale.order.line.search", "purchase.order.line.search"}
)
SUMMARY_CAPABILITY_IDS = frozenset(
    {"sale.order.analysis.summary", "purchase.order.analysis.summary"}
)
PAGED_CAPABILITY_IDS = SEARCH_CAPABILITY_IDS | LINE_SEARCH_CAPABILITY_IDS

SALE_STATES = frozenset({"draft", "sent", "sale", "cancel"})
PURCHASE_STATES = frozenset({"draft", "sent", "to approve", "purchase", "cancel"})
SALE_INVOICE_STATUSES = frozenset({"upselling", "invoiced", "to invoice", "no"})
PURCHASE_INVOICE_STATUSES = frozenset({"no", "to invoice", "invoiced"})
SALE_GROUP_BY = frozenset(
    {"state", "invoice_status", "partner", "salesperson", "currency"}
)
PURCHASE_GROUP_BY = frozenset(
    {"state", "invoice_status", "partner", "buyer", "currency"}
)
DELIVERY_STATUSES = frozenset({"pending", "started", "partial", "full"})
RECEIPT_STATUSES = frozenset({"pending", "partial", "full"})
TRANSFER_STATES = frozenset(
    {"draft", "waiting", "confirmed", "assigned", "done", "cancel"}
)
INVOICE_STATES = frozenset({"draft", "posted", "cancel"})
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
SALE_MOVE_TYPES = frozenset({"out_invoice", "out_refund", "out_receipt"})
PURCHASE_MOVE_TYPES = frozenset({"in_invoice", "in_refund", "in_receipt"})

DEFAULT_LIMIT = 100
MAX_LIMIT = 1000
_CURSOR_VERSION = 1
_DECIMAL_PATTERN = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
_UTC_PATTERN = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")


class OrderDocumentPort(Protocol):
    @property
    def user_id(self) -> int: ...

    def read(
        self,
        *,
        capability_id: str,
        company_id: int,
        parameters: dict[str, Any],
    ) -> dict[str, Any]: ...


class OrderDocumentReadError(RuntimeError):
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


def _invalid(message: str, *, code: str = "invalid_request") -> OrderDocumentReadError:
    return OrderDocumentReadError(code, message, exit_code=2)


def _failed(message: str) -> OrderDocumentReadError:
    return OrderDocumentReadError("failed_validation", message, exit_code=8)


def _integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _positive_id(value: Any) -> bool:
    return _integer(value) and value > 0


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _optional_text(value: Any) -> bool:
    return value is None or _text(value)


def _canonical_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _utc_datetime(value: Any) -> bool:
    if not isinstance(value, str) or _UTC_PATTERN.fullmatch(value) is None:
        return False
    try:
        datetime.fromisoformat(value)
    except ValueError:
        return False
    return True


def _optional_utc_datetime(value: Any) -> bool:
    return value is None or _utc_datetime(value)


def _decimal(value: Any) -> Decimal | None:
    if (
        not isinstance(value, str)
        or len(value) > 256
        or _DECIMAL_PATTERN.fullmatch(value) is None
    ):
        return None
    try:
        number = Decimal(value)
    except InvalidOperation:
        return None
    return number if number.is_finite() else None


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
    if not _positive_id(context.get("company_id")) or not all(
        _text(context.get(key))
        for key in ("database", "user_login", "language", "timezone")
    ):
        raise _invalid("context contains an invalid value.")
    parameters = request["parameters"]
    if not isinstance(parameters, dict):
        raise _invalid("parameters must be an object.")
    return request_id, context, parameters


def _sale(capability_id: str) -> bool:
    return capability_id.startswith("sale.")


def _states(capability_id: str) -> frozenset[str]:
    return SALE_STATES if _sale(capability_id) else PURCHASE_STATES


def _invoice_statuses(capability_id: str) -> frozenset[str]:
    return SALE_INVOICE_STATUSES if _sale(capability_id) else PURCHASE_INVOICE_STATUSES


def _optional_id(parameters: dict[str, Any], key: str) -> int | None:
    value = parameters.get(key)
    if value is not None and not _positive_id(value):
        raise _invalid(f"parameters.{key} must be null or a positive integer.")
    return value


def _date_range(parameters: dict[str, Any]) -> tuple[str | None, str | None]:
    date_from = parameters.get("date_from")
    date_to = parameters.get("date_to")
    if date_from is not None and not _canonical_date(date_from):
        raise _invalid("parameters.date_from must be null or a YYYY-MM-DD date.")
    if date_to is not None and not _canonical_date(date_to):
        raise _invalid("parameters.date_to must be null or a YYYY-MM-DD date.")
    if date_from is not None and date_to is not None and date_from > date_to:
        raise _invalid("parameters.date_from cannot be after parameters.date_to.")
    return date_from, date_to


def _enum_list(
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


def _pagination(parameters: dict[str, Any]) -> tuple[int, str | None]:
    limit = parameters.get("limit", DEFAULT_LIMIT)
    if not _integer(limit) or not 1 <= limit <= MAX_LIMIT:
        raise _invalid(f"parameters.limit must be between 1 and {MAX_LIMIT}.")
    cursor = parameters.get("cursor")
    if cursor is not None and (
        not isinstance(cursor, str) or not cursor or len(cursor) > 4096
    ):
        raise _invalid("parameters.cursor must be null or non-empty text.")
    return limit, cursor


def _search_parameters(
    capability_id: str, parameters: dict[str, Any]
) -> dict[str, Any]:
    allowed = {
        "query",
        "date_from",
        "date_to",
        "states",
        "partner_id",
        "currency_id",
        "invoice_statuses",
        "limit",
        "cursor",
    }
    if not set(parameters) <= allowed:
        raise _invalid(f"{capability_id} contains an unsupported parameter.")
    query = parameters.get("query")
    if query is not None:
        if not isinstance(query, str) or not query.strip() or len(query.strip()) > 200:
            raise _invalid("parameters.query must be null or 1-200 characters.")
        query = query.strip()
    date_from, date_to = _date_range(parameters)
    limit, cursor = _pagination(parameters)
    return {
        "query": query,
        "date_from": date_from,
        "date_to": date_to,
        "states": _enum_list(parameters, "states", _states(capability_id)),
        "partner_id": _optional_id(parameters, "partner_id"),
        "currency_id": _optional_id(parameters, "currency_id"),
        "invoice_statuses": _enum_list(
            parameters, "invoice_statuses", _invoice_statuses(capability_id)
        ),
        "limit": limit,
        "cursor": cursor,
    }


def _line_parameters(capability_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
    pending_key = "to_deliver_only" if _sale(capability_id) else "to_receive_only"
    allowed = {
        "order_id",
        "date_from",
        "date_to",
        "partner_id",
        "product_id",
        "states",
        pending_key,
        "to_invoice_only",
        "limit",
        "cursor",
    }
    if not set(parameters) <= allowed:
        raise _invalid(f"{capability_id} contains an unsupported parameter.")
    pending_only = parameters.get(pending_key, False)
    to_invoice_only = parameters.get("to_invoice_only", False)
    if not isinstance(pending_only, bool):
        raise _invalid(f"parameters.{pending_key} must be boolean.")
    if not isinstance(to_invoice_only, bool):
        raise _invalid("parameters.to_invoice_only must be boolean.")
    date_from, date_to = _date_range(parameters)
    limit, cursor = _pagination(parameters)
    return {
        "order_id": _optional_id(parameters, "order_id"),
        "date_from": date_from,
        "date_to": date_to,
        "partner_id": _optional_id(parameters, "partner_id"),
        "product_id": _optional_id(parameters, "product_id"),
        "states": _enum_list(parameters, "states", _states(capability_id)),
        pending_key: pending_only,
        "to_invoice_only": to_invoice_only,
        "limit": limit,
        "cursor": cursor,
    }


def _summary_parameters(
    capability_id: str, parameters: dict[str, Any]
) -> dict[str, Any]:
    allowed = {
        "date_from",
        "date_to",
        "group_by",
        "states",
        "partner_id",
        "currency_id",
    }
    if (
        not {"date_from", "date_to", "group_by"} <= set(parameters)
        or not set(parameters) <= allowed
    ):
        raise _invalid(f"{capability_id} requires date_from, date_to and group_by.")
    date_from, date_to = _date_range(parameters)
    if date_from is None or date_to is None:
        raise _invalid("summary dates cannot be null.")
    group_by = parameters["group_by"]
    allowed_groups = SALE_GROUP_BY if _sale(capability_id) else PURCHASE_GROUP_BY
    if not isinstance(group_by, str) or group_by not in allowed_groups:
        raise _invalid("parameters.group_by is unsupported.")
    return {
        "date_from": date_from,
        "date_to": date_to,
        "group_by": group_by,
        "states": _enum_list(parameters, "states", _states(capability_id)),
        "partner_id": _optional_id(parameters, "partner_id"),
        "currency_id": _optional_id(parameters, "currency_id"),
    }


def validate_order_document_request(
    capability_id: str, request: Any
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    """Validate and normalize one order-document request."""

    if (
        not isinstance(capability_id, str)
        or capability_id not in ORDER_DOCUMENT_CAPABILITY_IDS
    ):
        raise OrderDocumentReadError(
            "unsupported_capability",
            "The order-document capability is unsupported.",
            exit_code=4,
        )
    request_id, context, parameters = _envelope(request)
    if capability_id in GET_CAPABILITY_IDS:
        if set(parameters) != {"order_id"} or not _positive_id(
            parameters.get("order_id")
        ):
            raise _invalid("parameters must contain one positive order_id.")
        normalized = {"order_id": parameters["order_id"]}
    elif capability_id in SEARCH_CAPABILITY_IDS:
        normalized = _search_parameters(capability_id, parameters)
    elif capability_id in LINE_SEARCH_CAPABILITY_IDS:
        normalized = _line_parameters(capability_id, parameters)
    else:
        normalized = _summary_parameters(capability_id, parameters)
    return request_id, context, normalized


def _binding(
    capability_id: str, context: dict[str, Any], parameters: dict[str, Any]
) -> str:
    filters = {
        key: value
        for key, value in parameters.items()
        if key not in {"limit", "cursor"}
    }
    return json.dumps(
        {"capability": capability_id, "context": context, "filters": filters},
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
            "binding": _binding(capability_id, context, parameters),
            "version": _CURSOR_VERSION,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
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
            raw.decode("utf-8"),
            object_pairs_hook=_pairs,
            parse_float=_reject_number,
            parse_constant=_reject_number,
        )
    except (ValueError, UnicodeError, json.JSONDecodeError, binascii.Error) as exc:
        raise _invalid("The cursor is invalid.", code="invalid_cursor") from exc
    if (
        not isinstance(value, dict)
        or set(value) != {"after", "binding", "version"}
        or not _integer(value["version"])
        or value["version"] != _CURSOR_VERSION
        or not _positive_id(value["after"])
        or value["binding"] != _binding(capability_id, context, parameters)
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


def _id_list(value: Any) -> bool:
    return bool(
        isinstance(value, list)
        and all(_positive_id(item) for item in value)
        and value == sorted(set(value))
    )


def _ref_list(value: Any) -> bool:
    return bool(
        isinstance(value, list)
        and all(_named_ref(item) for item in value)
        and [item["id"] for item in value] == sorted({item["id"] for item in value})
    )


_COMMON_HEADER_KEYS = {
    "id",
    "name",
    "company",
    "partner",
    "state",
    "date_order",
    "currency",
    "user",
    "invoice_status",
    "amount_untaxed",
    "amount_tax",
    "amount_total",
    "invoice_ids",
    "transfer_ids",
    "line_count",
}
_SALE_HEADER_KEYS = {
    "validity_date",
    "client_order_ref",
    "team",
    "delivery_status",
}
_PURCHASE_HEADER_KEYS = {"date_approve", "partner_ref", "origin", "receipt_status"}


def _header_keys(capability_id: str) -> set[str]:
    return _COMMON_HEADER_KEYS | (
        _SALE_HEADER_KEYS if _sale(capability_id) else _PURCHASE_HEADER_KEYS
    )


def _valid_header(
    capability_id: str,
    value: Any,
    *,
    company_id: int,
    parameters: dict[str, Any] | None,
) -> bool:
    if not isinstance(value, dict) or set(value) != _header_keys(capability_id):
        return False
    states = _states(capability_id)
    statuses = _invoice_statuses(capability_id)
    if not (
        _positive_id(value["id"])
        and _text(value["name"])
        and _named_ref(value["company"])
        and value["company"]["id"] == company_id
        and _named_ref(value["partner"])
        and value["state"] in states
        and _utc_datetime(value["date_order"])
        and _currency(value["currency"])
        and _optional_ref(value["user"])
        and value["invoice_status"] in statuses
        and all(
            _decimal(value[key]) is not None
            for key in ("amount_untaxed", "amount_tax", "amount_total")
        )
        and _id_list(value["invoice_ids"])
        and _id_list(value["transfer_ids"])
        and _integer(value["line_count"])
        and value["line_count"] >= 0
    ):
        return False
    if _sale(capability_id):
        if not (
            (value["validity_date"] is None or _canonical_date(value["validity_date"]))
            and _optional_text(value["client_order_ref"])
            and _optional_ref(value["team"])
            and (
                value["delivery_status"] is None
                or value["delivery_status"] in DELIVERY_STATUSES
            )
        ):
            return False
    elif not (
        _optional_utc_datetime(value["date_approve"])
        and _optional_text(value["partner_ref"])
        and _optional_text(value["origin"])
        and (
            value["receipt_status"] is None
            or value["receipt_status"] in RECEIPT_STATUSES
        )
    ):
        return False
    if parameters is None:
        return True
    date_value = value["date_order"][:10]
    return not (
        parameters["date_from"] is not None
        and date_value < parameters["date_from"]
        or parameters["date_to"] is not None
        and date_value > parameters["date_to"]
        or parameters["states"] is not None
        and value["state"] not in parameters["states"]
        or parameters["partner_id"] is not None
        and value["partner"]["id"] != parameters["partner_id"]
        or parameters["currency_id"] is not None
        and value["currency"]["id"] != parameters["currency_id"]
        or parameters["invoice_statuses"] is not None
        and value["invoice_status"] not in parameters["invoice_statuses"]
    )


_COMMON_LINE_KEYS = {
    "id",
    "order",
    "company",
    "partner",
    "state",
    "date_order",
    "sequence",
    "display_type",
    "description",
    "product",
    "uom",
    "ordered_quantity",
    "invoiced_quantity",
    "to_invoice_quantity",
    "unit_price",
    "discount_percent",
    "amount_untaxed",
    "amount_tax",
    "amount_total",
    "currency",
    "taxes",
    "invoice_line_ids",
    "stock_move_ids",
}
_SALE_LINE_KEYS = {"delivered_quantity", "to_deliver_quantity"}
_PURCHASE_LINE_KEYS = {
    "received_quantity",
    "to_receive_quantity",
    "date_planned",
}


def _line_keys(capability_id: str) -> set[str]:
    return _COMMON_LINE_KEYS | (
        _SALE_LINE_KEYS if _sale(capability_id) else _PURCHASE_LINE_KEYS
    )


def _valid_line(
    capability_id: str,
    value: Any,
    *,
    company_id: int,
    parameters: dict[str, Any] | None,
) -> bool:
    if not isinstance(value, dict) or set(value) != _line_keys(capability_id):
        return False
    decimal_keys = {
        "ordered_quantity",
        "invoiced_quantity",
        "to_invoice_quantity",
        "unit_price",
        "discount_percent",
        "amount_untaxed",
        "amount_tax",
        "amount_total",
    } | (
        {"delivered_quantity", "to_deliver_quantity"}
        if _sale(capability_id)
        else {"received_quantity", "to_receive_quantity"}
    )
    discount = _decimal(value.get("discount_percent"))
    if not (
        _positive_id(value["id"])
        and _named_ref(value["order"])
        and _named_ref(value["company"])
        and value["company"]["id"] == company_id
        and _named_ref(value["partner"])
        and value["state"] in _states(capability_id)
        and _utc_datetime(value["date_order"])
        and _integer(value["sequence"])
        and value["sequence"] >= 0
        and _optional_text(value["display_type"])
        and _text(value["description"])
        and _optional_ref(value["product"])
        and _optional_ref(value["uom"])
        and all(_decimal(value[key]) is not None for key in decimal_keys)
        and discount is not None
        and Decimal(0) <= discount <= Decimal(100)
        and _currency(value["currency"])
        and _ref_list(value["taxes"])
        and _id_list(value["invoice_line_ids"])
        and _id_list(value["stock_move_ids"])
        and (
            _sale(capability_id)
            or value["date_planned"] is None
            or _utc_datetime(value["date_planned"])
        )
    ):
        return False
    if parameters is None:
        return True
    date_value = value["date_order"][:10]
    pending_key = (
        "to_deliver_quantity" if _sale(capability_id) else "to_receive_quantity"
    )
    pending_filter = "to_deliver_only" if _sale(capability_id) else "to_receive_only"
    return not (
        parameters["order_id"] is not None
        and value["order"]["id"] != parameters["order_id"]
        or parameters["date_from"] is not None
        and date_value < parameters["date_from"]
        or parameters["date_to"] is not None
        and date_value > parameters["date_to"]
        or parameters["partner_id"] is not None
        and value["partner"]["id"] != parameters["partner_id"]
        or parameters["product_id"] is not None
        and (
            value["product"] is None
            or value["product"]["id"] != parameters["product_id"]
        )
        or parameters["states"] is not None
        and value["state"] not in parameters["states"]
        or parameters[pending_filter]
        and _decimal(value[pending_key]) <= 0
        or parameters["to_invoice_only"]
        and _decimal(value["to_invoice_quantity"]) <= 0
    )


def _valid_invoice(value: Any, *, sale: bool) -> bool:
    return bool(
        isinstance(value, dict)
        and set(value)
        == {
            "id",
            "name",
            "move_type",
            "state",
            "payment_state",
            "amount_total",
            "currency",
        }
        and _positive_id(value["id"])
        and _text(value["name"])
        and value["move_type"] in (SALE_MOVE_TYPES if sale else PURCHASE_MOVE_TYPES)
        and value["state"] in INVOICE_STATES
        and (value["payment_state"] is None or value["payment_state"] in PAYMENT_STATES)
        and _decimal(value["amount_total"]) is not None
        and _currency(value["currency"])
    )


def _valid_transfer(value: Any) -> bool:
    return bool(
        isinstance(value, dict)
        and set(value)
        == {
            "id",
            "name",
            "state",
            "source_location",
            "destination_location",
        }
        and _positive_id(value["id"])
        and _text(value["name"])
        and value["state"] in TRANSFER_STATES
        and _named_ref(value["source_location"])
        and _named_ref(value["destination_location"])
    )


def _valid_get(
    capability_id: str,
    value: Any,
    *,
    company_id: int,
    order_id: int,
) -> bool:
    expected = _header_keys(capability_id) | {"lines", "invoices", "transfers"}
    if not isinstance(value, dict) or set(value) != expected:
        return False
    header = {key: value[key] for key in _header_keys(capability_id)}
    lines = value["lines"]
    invoices = value["invoices"]
    transfers = value["transfers"]
    return bool(
        _valid_header(capability_id, header, company_id=company_id, parameters=None)
        and value["id"] == order_id
        and isinstance(lines, list)
        and all(
            _valid_line(
                capability_id,
                line,
                company_id=company_id,
                parameters=None,
            )
            and line["order"]["id"] == order_id
            for line in lines
        )
        and [line["id"] for line in lines] == sorted({line["id"] for line in lines})
        and value["line_count"] == len(lines)
        and isinstance(invoices, list)
        and all(
            _valid_invoice(invoice, sale=_sale(capability_id)) for invoice in invoices
        )
        and [invoice["id"] for invoice in invoices]
        == sorted({invoice["id"] for invoice in invoices})
        and value["invoice_ids"] == [invoice["id"] for invoice in invoices]
        and isinstance(transfers, list)
        and all(_valid_transfer(transfer) for transfer in transfers)
        and [transfer["id"] for transfer in transfers]
        == sorted({transfer["id"] for transfer in transfers})
        and value["transfer_ids"] == [transfer["id"] for transfer in transfers]
    )


_SUMMARY_AMOUNT_KEYS = ("amount_untaxed", "amount_tax", "amount_total")


def _valid_group_descriptor(capability_id: str, group_by: str, value: Any) -> bool:
    if not isinstance(value, dict) or set(value) != {"id", "value"}:
        return False
    group_id = value["id"]
    group_value = value["value"]
    if group_by == "state":
        return group_id is None and group_value in _states(capability_id)
    if group_by == "invoice_status":
        return group_id is None and group_value in _invoice_statuses(capability_id)
    if group_by == "partner":
        return _positive_id(group_id) and _text(group_value)
    if group_by == "currency":
        return _positive_id(group_id) and _text(group_value)
    return bool(
        (group_id is None and group_value is None)
        or (_positive_id(group_id) and _text(group_value))
    )


def _valid_summary(
    capability_id: str,
    value: Any,
    *,
    company_id: int,
    parameters: dict[str, Any],
) -> bool:
    if not isinstance(value, dict) or set(value) != {
        "company_id",
        "group_by",
        "date_from",
        "date_to",
        "groups",
        "totals_by_currency",
    }:
        return False
    groups = value["groups"]
    totals = value["totals_by_currency"]
    if not (
        value["company_id"] == company_id
        and value["group_by"] == parameters["group_by"]
        and value["date_from"] == parameters["date_from"]
        and value["date_to"] == parameters["date_to"]
        and isinstance(groups, list)
        and isinstance(totals, list)
    ):
        return False

    group_keys: set[tuple[int, str, int]] = set()
    calculated: dict[int, dict[str, Any]] = {}
    for group in groups:
        if not isinstance(group, dict) or set(group) != {
            "group",
            "currency",
            "order_count",
            *_SUMMARY_AMOUNT_KEYS,
        }:
            return False
        descriptor = group["group"]
        currency = group["currency"]
        if not (
            _valid_group_descriptor(capability_id, parameters["group_by"], descriptor)
            and _currency(currency)
            and _integer(group["order_count"])
            and group["order_count"] > 0
            and all(_decimal(group[key]) is not None for key in _SUMMARY_AMOUNT_KEYS)
            and (
                parameters["currency_id"] is None
                or currency["id"] == parameters["currency_id"]
            )
        ):
            return False
        if parameters["group_by"] == "currency" and descriptor["id"] != currency["id"]:
            return False
        identity = (
            descriptor["id"] or 0,
            descriptor["value"] or "",
            currency["id"],
        )
        if identity in group_keys:
            return False
        group_keys.add(identity)
        accumulated = calculated.setdefault(
            currency["id"],
            {
                "currency": currency,
                "order_count": 0,
                **{key: Decimal(0) for key in _SUMMARY_AMOUNT_KEYS},
            },
        )
        if accumulated["currency"] != currency:
            return False
        accumulated["order_count"] += group["order_count"]
        for key in _SUMMARY_AMOUNT_KEYS:
            accumulated[key] += _decimal(group[key])

    total_ids: set[int] = set()
    for total in totals:
        if not isinstance(total, dict) or set(total) != {
            "currency",
            "order_count",
            *_SUMMARY_AMOUNT_KEYS,
        }:
            return False
        currency = total["currency"]
        if not (
            _currency(currency)
            and currency["id"] not in total_ids
            and _integer(total["order_count"])
            and total["order_count"] > 0
            and all(_decimal(total[key]) is not None for key in _SUMMARY_AMOUNT_KEYS)
            and (
                parameters["currency_id"] is None
                or currency["id"] == parameters["currency_id"]
            )
        ):
            return False
        total_ids.add(currency["id"])
        expected = calculated.get(currency["id"])
        if expected is None or expected["currency"] != currency:
            return False
        if total["order_count"] != expected["order_count"] or any(
            _decimal(total[key]) != expected[key] for key in _SUMMARY_AMOUNT_KEYS
        ):
            return False
    return total_ids == set(calculated)


def _validate_page(port: OrderDocumentPort, page: Any) -> list[dict[str, Any]]:
    if not isinstance(page, dict) or set(page) != {
        "user_id",
        "company_visible",
        "module_installed",
        "access_allowed",
        "cursor_found",
        "items",
    }:
        raise _failed("Odoo returned an invalid order-document page.")
    if not (
        _positive_id(page["user_id"])
        and page["user_id"] == port.user_id
        and all(
            isinstance(page[key], bool)
            for key in (
                "company_visible",
                "module_installed",
                "access_allowed",
                "cursor_found",
            )
        )
        and isinstance(page["items"], list)
        and all(isinstance(item, dict) for item in page["items"])
        and (
            not page["access_allowed"]
            or page["company_visible"]
            and page["module_installed"]
        )
        and (page["access_allowed"] or not page["items"])
    ):
        raise _failed("Odoo returned an inconsistent order-document page.")
    return page["items"]


def _ensure_available(page: dict[str, Any]) -> None:
    if not page["company_visible"]:
        raise OrderDocumentReadError(
            "company_unavailable",
            "The requested company is unavailable to the configured user.",
            exit_code=3,
        )
    if not page["module_installed"]:
        raise OrderDocumentReadError(
            "uninstalled",
            "The required order-document models are not installed.",
            exit_code=4,
        )
    if not page["access_allowed"]:
        raise OrderDocumentReadError(
            "unauthorized",
            "The configured user cannot read the requested order documents.",
            exit_code=3,
        )


def _paged_result(
    capability_id: str,
    items: list[dict[str, Any]],
    *,
    context: dict[str, Any],
    parameters: dict[str, Any],
    after: int | None,
) -> dict[str, Any]:
    if capability_id in SEARCH_CAPABILITY_IDS:
        validator = lambda item: _valid_header(
            capability_id,
            item,
            company_id=context["company_id"],
            parameters=parameters,
        )
    else:
        validator = lambda item: _valid_line(
            capability_id,
            item,
            company_id=context["company_id"],
            parameters=parameters,
        )
    if len(items) > parameters["limit"] + 1 or any(
        not validator(item) for item in items
    ):
        raise _failed("Odoo returned invalid order-document rows.")
    ids = [item["id"] for item in items]
    if ids != sorted(set(ids)) or (
        after is not None and any(item_id <= after for item_id in ids)
    ):
        raise _failed("Odoo returned unordered order-document rows.")
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


def read_order_document(
    port: OrderDocumentPort, capability_id: str, request: Any
) -> dict[str, Any]:
    """Execute one validated order-document read."""

    _, context, parameters = validate_order_document_request(capability_id, request)
    runtime_parameters = dict(parameters)
    after: int | None = None
    if capability_id in PAGED_CAPABILITY_IDS:
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
            if key not in {"limit", "cursor"}
        }
        runtime_parameters.update({"after": after, "limit": parameters["limit"] + 1})

    page = port.read(
        capability_id=capability_id,
        company_id=context["company_id"],
        parameters=runtime_parameters,
    )
    items = _validate_page(port, page)
    _ensure_available(page)

    if capability_id in PAGED_CAPABILITY_IDS:
        if parameters["cursor"] is not None and not page["cursor_found"]:
            raise _invalid("The cursor no longer resolves.", code="invalid_cursor")
        if parameters["cursor"] is None and not page["cursor_found"]:
            raise _failed("Odoo returned an invalid cursor state.")
        return _paged_result(
            capability_id,
            items,
            context=context,
            parameters=parameters,
            after=after,
        )

    if not page["cursor_found"] or len(items) > 1:
        raise _failed("Odoo returned an invalid single order-document result.")
    if not items:
        raise OrderDocumentReadError(
            "record_not_found",
            "The requested order document was not found.",
            exit_code=4,
        )
    item = items[0]
    if capability_id in GET_CAPABILITY_IDS:
        valid = _valid_get(
            capability_id,
            item,
            company_id=context["company_id"],
            order_id=parameters["order_id"],
        )
    else:
        valid = _valid_summary(
            capability_id,
            item,
            company_id=context["company_id"],
            parameters=parameters,
        )
    if not valid:
        raise _failed("Odoo returned an invalid order-document result.")
    return item
