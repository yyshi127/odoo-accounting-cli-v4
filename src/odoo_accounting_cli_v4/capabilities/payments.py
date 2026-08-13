"""Strict business contracts for company-scoped accounting-payment reads."""

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


SEARCH_CAPABILITY_ID = "payment.search"
GET_CAPABILITY_ID = "payment.get"
DEFAULT_LIMIT = 100
MAX_LIMIT = 1000
_CURSOR_VERSION = 1
_DECIMAL_PATTERN = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
_PAYMENT_STATES = ("draft", "in_process", "paid", "canceled", "rejected")
_PAYMENT_TYPES = ("inbound", "outbound")
_PARTNER_TYPES = ("customer", "supplier")
_MOVE_STATES = frozenset({"draft", "posted", "cancel"})
_DOCUMENT_TYPES = frozenset(
    {
        "out_invoice",
        "out_refund",
        "out_receipt",
        "in_invoice",
        "in_refund",
        "in_receipt",
    }
)
_SALE_DOCUMENT_TYPES = frozenset({"out_invoice", "out_refund", "out_receipt"})
_PURCHASE_DOCUMENT_TYPES = frozenset({"in_invoice", "in_refund", "in_receipt"})
_PAYMENT_STATES_FOR_DOCUMENT = frozenset(
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
_FILTER_FIELDS = frozenset(
    {
        "date_from",
        "date_to",
        "states",
        "payment_types",
        "partner_types",
        "journal_id",
        "partner_id",
        "currency_id",
        "query",
    }
)
_COMMON_FIELDS = frozenset(
    {
        "id",
        "name",
        "date",
        "state",
        "payment_type",
        "partner_type",
        "amount",
        "amount_signed",
        "amount_company_currency_signed",
        "currency",
        "company_currency",
        "company_id",
        "partner",
        "journal",
        "memo",
        "payment_reference",
        "payment_method_line",
        "payment_method",
        "move_id",
        "is_reconciled",
        "is_matched",
    }
)
_GET_FIELDS = _COMMON_FIELDS | {
    "journal_entry",
    "invoice_ids",
    "reconciled_invoices",
    "reconciled_bills",
}


class PaymentPort(Protocol):
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

    def get_payment(self, *, company_id: int, payment_id: int) -> dict[str, Any]: ...


class PaymentError(RuntimeError):
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


def _invalid(message: str, *, code: str = "invalid_request") -> PaymentError:
    return PaymentError(code, message, exit_code=2)


def _failed(message: str) -> PaymentError:
    return PaymentError("failed_validation", message, exit_code=8)


def _is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _valid_id(value: Any) -> bool:
    return _is_integer(value) and value > 0


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and len(value) > 0


def _valid_optional_string(value: Any) -> bool:
    return value is None or _is_nonempty_text(value)


def _is_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return False
    return parsed.isoformat() == value


def _decimal(value: Any) -> Decimal | None:
    if not isinstance(value, str) or _DECIMAL_PATTERN.fullmatch(value) is None:
        return None
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        return None
    return parsed if parsed.is_finite() else None


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate cursor key")
        result[key] = value
    return result


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


def _normalize_selection(
    parameters: dict[str, Any], key: str, canonical_order: tuple[str, ...]
) -> list[str]:
    if key not in parameters:
        return []
    values = parameters[key]
    if (
        not isinstance(values, list)
        or not 1 <= len(values) <= len(canonical_order)
        or any(not isinstance(value, str) for value in values)
        or len(values) != len(set(values))
        or any(value not in canonical_order for value in values)
    ):
        raise _invalid(
            f"parameters.{key} must contain unique supported string values."
        )
    return [value for value in canonical_order if value in values]


def validate_payment_search_request(
    request: Any,
) -> tuple[str, dict[str, Any], dict[str, Any], int, str | None]:
    """Validate and normalize the closed payment search request."""

    request_id, context, parameters = _validate_envelope(request)
    if not set(parameters) <= _FILTER_FIELDS | {"limit", "cursor"}:
        raise _invalid("payment.search contains an unsupported parameter.")
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

    identifiers: dict[str, int | None] = {}
    for key in ("journal_id", "partner_id", "currency_id"):
        value = parameters.get(key)
        if value is not None and not _valid_id(value):
            raise _invalid(f"parameters.{key} must be null or a positive integer.")
        identifiers[key] = value
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
        "states": _normalize_selection(parameters, "states", _PAYMENT_STATES),
        "payment_types": _normalize_selection(
            parameters, "payment_types", _PAYMENT_TYPES
        ),
        "partner_types": _normalize_selection(
            parameters, "partner_types", _PARTNER_TYPES
        ),
        "journal_id": identifiers["journal_id"],
        "partner_id": identifiers["partner_id"],
        "currency_id": identifiers["currency_id"],
        "query": query,
    }
    return request_id, context, filters, limit, cursor


def validate_payment_get_request(
    request: Any,
) -> tuple[str, dict[str, Any], int]:
    """Validate the exact positive payment identifier request."""

    request_id, context, parameters = _validate_envelope(request)
    if set(parameters) != {"payment_id"} or not _valid_id(parameters["payment_id"]):
        raise _invalid("parameters must contain one positive integer payment_id.")
    return request_id, context, parameters["payment_id"]


def _cursor_binding(context: dict[str, Any], filters: dict[str, Any]) -> str:
    value = {
        "capability": SEARCH_CAPABILITY_ID,
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
        or not isinstance(value["binding"], str)
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
        and _is_nonempty_text(value["code"])
        and len(value["code"]) <= 3
    )


def _valid_journal(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "code", "name"}
        and _valid_id(value["id"])
        and _is_nonempty_text(value["code"])
        and len(value["code"]) <= 5
        and _is_nonempty_text(value["name"])
    )


def _valid_partner(value: Any) -> bool:
    return value is None or (
        isinstance(value, dict)
        and set(value) == {"id", "name"}
        and _valid_id(value["id"])
        and _valid_optional_string(value["name"])
    )


def _valid_payment_method_line(value: Any, journal_id: int) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "name", "journal_id"}
        and _valid_id(value["id"])
        and _valid_optional_string(value["name"])
        and (value["journal_id"] is None or value["journal_id"] == journal_id)
    )


def _valid_payment_method(value: Any, payment_type: str) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "code", "name", "payment_type"}
        and _valid_id(value["id"])
        and _is_nonempty_text(value["code"])
        and _is_nonempty_text(value["name"])
        and value["payment_type"] == payment_type
    )


def _valid_common_payment(
    row: Any, *, company_id: int, exact_fields: frozenset[str] | set[str]
) -> bool:
    if (
        not isinstance(row, dict)
        or set(row) != exact_fields
        or not _valid_id(row["id"])
        or not _valid_optional_string(row["name"])
        or not _is_date(row["date"])
        or row["state"] not in _PAYMENT_STATES
        or row["payment_type"] not in _PAYMENT_TYPES
        or row["partner_type"] not in _PARTNER_TYPES
        or row["company_id"] != company_id
        or not _valid_currency(row["currency"])
        or not _valid_currency(row["company_currency"])
        or not _valid_partner(row["partner"])
        or not _valid_journal(row["journal"])
        or not _valid_optional_string(row["memo"])
        or not _valid_optional_string(row["payment_reference"])
        or not _valid_payment_method_line(
            row["payment_method_line"], row["journal"]["id"]
        )
        or not _valid_payment_method(row["payment_method"], row["payment_type"])
        or not (row["move_id"] is None or _valid_id(row["move_id"]))
        or not isinstance(row["is_reconciled"], bool)
        or not isinstance(row["is_matched"], bool)
    ):
        return False
    amount = _decimal(row["amount"])
    amount_signed = _decimal(row["amount_signed"])
    company_signed = _decimal(row["amount_company_currency_signed"])
    if amount is None or amount_signed is None or company_signed is None or amount < 0:
        return False
    expected_signed = amount if row["payment_type"] == "inbound" else -amount
    if amount_signed != expected_signed:
        return False
    if row["currency"]["id"] == row["company_currency"]["id"]:
        if row["currency"]["code"] != row["company_currency"]["code"]:
            return False
    return True


def _validate_page(port: PaymentPort, page: Any, *, payload_key: str) -> Any:
    if not isinstance(page, dict) or set(page) != {
        "user_id",
        "company_visible",
        "module_installed",
        "access_allowed",
        payload_key,
    }:
        raise _failed("Odoo returned an invalid payment page.")
    payload = page[payload_key]
    payload_present = bool(payload) if payload_key == "rows" else payload is not None
    try:
        port_user_id = port.user_id
    except ValueError as exc:
        raise _failed("Odoo returned an invalid payment page.") from exc
    if (
        not _valid_id(page["user_id"])
        or not _valid_id(port_user_id)
        or page["user_id"] != port_user_id
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
        raise _failed("Odoo returned an invalid payment page.")
    if not page["company_visible"]:
        raise PaymentError(
            "company_unavailable",
            "The requested company is unavailable to the configured user.",
            exit_code=3,
        )
    if not page["module_installed"]:
        raise PaymentError(
            "uninstalled",
            "The payment capability is not installed in this database.",
            exit_code=4,
        )
    if not page["access_allowed"]:
        raise PaymentError(
            "unauthorized",
            "The configured user cannot read accounting payments.",
            exit_code=3,
        )
    return payload


def _validate_search_rows(
    rows: Any,
    *,
    company_id: int,
    after: list[Any] | None,
    filters: dict[str, Any],
    maximum: int,
) -> list[dict[str, Any]]:
    if not isinstance(rows, list) or len(rows) > maximum:
        raise _failed("Odoo returned an invalid payment search page.")
    previous = tuple(after) if after is not None else None
    record_ids: set[int] = set()
    result: list[dict[str, Any]] = []
    for row in rows:
        if not _valid_common_payment(
            row, company_id=company_id, exact_fields=_COMMON_FIELDS
        ):
            raise _failed("Odoo returned an invalid or out-of-scope payment.")
        current = (row["date"], row["id"])
        if row["id"] in record_ids or (previous is not None and current >= previous):
            raise _failed("Odoo returned payments in an unstable order.")
        if (
            (filters["date_from"] is not None and row["date"] < filters["date_from"])
            or (filters["date_to"] is not None and row["date"] > filters["date_to"])
            or (filters["states"] and row["state"] not in filters["states"])
            or (
                filters["payment_types"]
                and row["payment_type"] not in filters["payment_types"]
            )
            or (
                filters["partner_types"]
                and row["partner_type"] not in filters["partner_types"]
            )
            or (
                filters["journal_id"] is not None
                and row["journal"]["id"] != filters["journal_id"]
            )
            or (
                filters["partner_id"] is not None
                and (
                    row["partner"] is None
                    or row["partner"]["id"] != filters["partner_id"]
                )
            )
            or (
                filters["currency_id"] is not None
                and row["currency"]["id"] != filters["currency_id"]
            )
        ):
            raise _failed("Odoo returned a payment outside the requested filters.")
        record_ids.add(row["id"])
        previous = current
        result.append(dict(row))
    return result


def search_payments(port: PaymentPort, request: dict[str, Any]) -> dict[str, Any]:
    """Read one verified payment page in date/id descending order."""

    _, context, filters, limit, cursor = validate_payment_search_request(request)
    after = _decode_cursor(cursor, context=context, filters=filters) if cursor else None
    fetch_limit = limit + 1
    try:
        page = port.search_page(
            company_id=context["company_id"],
            after=after,
            limit=fetch_limit,
            filters=filters,
        )
    except ValueError as exc:
        raise _failed("The Odoo bridge returned an invalid payment page.") from exc
    rows = _validate_page(port, page, payload_key="rows")
    records = _validate_search_rows(
        rows,
        company_id=context["company_id"],
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


def _valid_journal_entry(value: Any, *, payment: dict[str, Any]) -> bool:
    if payment["move_id"] is None:
        return value is None
    return (
        isinstance(value, dict)
        and set(value) == {"id", "name", "state", "date"}
        and value["id"] == payment["move_id"]
        and _valid_optional_string(value["name"])
        and value["state"] in _MOVE_STATES
        and _is_date(value["date"])
    )


def _valid_document(value: Any, *, allowed_types: frozenset[str]) -> bool:
    return (
        isinstance(value, dict)
        and set(value)
        == {"id", "name", "move_type", "state", "payment_state", "company_id"}
        and _valid_id(value["id"])
        and _valid_id(value["company_id"])
        and _valid_optional_string(value["name"])
        and value["move_type"] in allowed_types
        and value["state"] in _MOVE_STATES
        and value["payment_state"] in _PAYMENT_STATES_FOR_DOCUMENT
    )


def _valid_document_list(value: Any, *, allowed_types: frozenset[str]) -> bool:
    if not isinstance(value, list):
        return False
    previous_id: int | None = None
    for document in value:
        if not _valid_document(document, allowed_types=allowed_types) or (
            previous_id is not None and document["id"] <= previous_id
        ):
            return False
        previous_id = document["id"]
    return True


def _validate_payment(
    row: Any, *, company_id: int, payment_id: int
) -> dict[str, Any]:
    if (
        not _valid_common_payment(row, company_id=company_id, exact_fields=_GET_FIELDS)
        or row["id"] != payment_id
        or not _valid_journal_entry(row["journal_entry"], payment=row)
        or not _valid_document_list(
            row["invoice_ids"], allowed_types=_DOCUMENT_TYPES
        )
        or not _valid_document_list(
            row["reconciled_invoices"], allowed_types=_SALE_DOCUMENT_TYPES
        )
        or not _valid_document_list(
            row["reconciled_bills"], allowed_types=_PURCHASE_DOCUMENT_TYPES
        )
    ):
        raise _failed("Odoo returned an invalid or out-of-scope payment detail.")
    return dict(row)


def get_payment(port: PaymentPort, request: dict[str, Any]) -> dict[str, Any]:
    """Read one exact payment while preserving direct and reconciled provenance."""

    _, context, payment_id = validate_payment_get_request(request)
    try:
        page = port.get_payment(
            company_id=context["company_id"], payment_id=payment_id
        )
    except ValueError as exc:
        raise _failed("The Odoo bridge returned an invalid payment page.") from exc
    payment = _validate_page(port, page, payload_key="payment")
    if payment is None:
        raise PaymentError(
            "record_not_found", "The requested payment was not found.", exit_code=4
        )
    return _validate_payment(
        payment, company_id=context["company_id"], payment_id=payment_id
    )
