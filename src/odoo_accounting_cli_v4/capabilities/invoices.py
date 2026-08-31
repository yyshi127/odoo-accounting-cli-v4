"""Strict contracts for company-scoped invoice and payment-status reads."""

from __future__ import annotations

import base64
import binascii
import json
import re
import uuid
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol

from odoo_accounting_cli_v4.capabilities.core_object_reads import (
    _valid_line_analytic_distribution,
)

SEARCH_CAPABILITY_ID = "invoice.search"
GET_CAPABILITY_ID = "invoice.get"
PAYMENT_STATUS_CAPABILITY_ID = "invoice.payment_status.inspect"
DEFAULT_LIMIT = 100
MAX_LIMIT = 1000
_CURSOR_VERSION = 1
_DECIMAL_PATTERN = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
_DOCUMENT_TYPE_ORDER = ("out_invoice", "out_refund", "in_invoice", "in_refund")
_STATE_ORDER = ("draft", "posted", "cancel")
_PAYMENT_STATE_ORDER = (
    "not_paid",
    "in_payment",
    "paid",
    "partial",
    "reversed",
    "blocked",
    "invoicing_legacy",
)
_PAYMENT_STATES = frozenset({"draft", "in_process", "paid", "canceled", "rejected"})
_DISPLAY_TYPES = frozenset(
    {
        "product",
        "line_section",
        "line_subsection",
        "line_note",
    }
)
_NON_ACCOUNTABLE_TYPES = frozenset(
    {"line_section", "line_subsection", "line_note"}
)
_FILTER_FIELDS = frozenset(
    {
        "date_from",
        "date_to",
        "document_types",
        "states",
        "payment_states",
        "journal_id",
        "partner_id",
        "query",
    }
)
_HEADER_FIELDS = frozenset(
    {
        "id",
        "name",
        "move_type",
        "state",
        "date",
        "invoice_date",
        "invoice_date_due",
        "ref",
        "payment_reference",
        "invoice_origin",
        "journal",
        "company_id",
        "currency",
        "partner",
        "amount_untaxed",
        "amount_tax",
        "amount_total",
        "amount_residual",
        "payment_state",
    }
)
_LINE_FIELDS = frozenset(
    {
        "id",
        "sequence",
        "display_type",
        "name",
        "product",
        "account",
        "quantity",
        "price_unit",
        "discount",
        "price_subtotal",
        "price_total",
        "deferred_start_date",
        "deferred_end_date",
        "taxes",
        "analytic_distribution",
    }
)
_TAX_FIELDS = frozenset(
    {
        "id",
        "name",
        "type_tax_use",
        "amount_type",
        "amount",
        "price_include",
    }
)
_PAYMENT_STATUS_FIELDS = frozenset(
    {
        "id",
        "name",
        "move_type",
        "state",
        "payment_state",
        "company_id",
        "currency",
        "company_currency",
        "amount_total",
        "amount_residual",
        "receivable_payable_lines",
        "reconciliations",
        "payments",
        "outstanding_items",
    }
)
_RECEIVABLE_PAYABLE_LINE_FIELDS = frozenset(
    {
        "id",
        "account",
        "date_maturity",
        "balance",
        "amount_currency",
        "amount_residual",
        "amount_residual_currency",
        "currency",
        "reconciled",
        "matching_number",
    }
)
_RECONCILIATION_FIELDS = frozenset(
    {
        "id",
        "date",
        "amount",
        "company_amount",
        "currency",
        "company_currency",
        "invoice_line_id",
        "counterpart_line_id",
        "counterpart_move",
        "payment_id",
        "exchange_move_id",
    }
)
_OUTSTANDING_ITEM_FIELDS = frozenset(
    {
        "line_id",
        "move_id",
        "payment_id",
        "date",
        "label",
        "amount",
        "currency",
    }
)
_PAYMENT_FIELDS = frozenset(
    {
        "id",
        "name",
        "state",
        "date",
        "payment_type",
        "partner_type",
        "amount",
        "currency",
        "journal",
        "payment_method",
        "move_id",
        "is_reconciled",
        "is_matched",
    }
)


class InvoicePort(Protocol):
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

    def get_invoice(self, *, company_id: int, invoice_id: int) -> dict[str, Any]: ...

    def inspect_payment_status(
        self, *, company_id: int, invoice_id: int
    ) -> dict[str, Any]: ...


class InvoiceError(RuntimeError):
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


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate cursor key")
        result[key] = value
    return result


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


def _is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _valid_id(value: Any) -> bool:
    return _is_integer(value) and value > 0


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _valid_optional_string(value: Any) -> bool:
    return value is None or _is_nonempty_string(value)


def _is_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return False
    return parsed.isoformat() == value


def _is_decimal_string(value: Any) -> bool:
    if not isinstance(value, str) or _DECIMAL_PATTERN.fullmatch(value) is None:
        return False
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        return False
    return parsed.is_finite()


def _invalid(message: str, *, code: str = "invalid_request") -> InvoiceError:
    return InvoiceError(code, message, exit_code=2)


def _failed(message: str) -> InvoiceError:
    return InvoiceError("failed_validation", message, exit_code=8)


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


def validate_invoice_search_request(
    request: Any,
) -> tuple[str, dict[str, Any], dict[str, Any], int, str | None]:
    """Validate and normalize the closed invoice search request."""

    request_id, context, parameters = _validate_envelope(request)
    if not set(parameters) <= _FILTER_FIELDS | {"limit", "cursor"}:
        raise _invalid("invoice.search contains an unsupported parameter.")
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

    ids: dict[str, int | None] = {}
    for key in ("journal_id", "partner_id"):
        value = parameters.get(key)
        if value is not None and not _valid_id(value):
            raise _invalid(f"parameters.{key} must be null or a positive integer.")
        ids[key] = value
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
        "document_types": _normalize_selection(
            parameters, "document_types", _DOCUMENT_TYPE_ORDER
        ),
        "states": _normalize_selection(parameters, "states", _STATE_ORDER),
        "payment_states": _normalize_selection(
            parameters, "payment_states", _PAYMENT_STATE_ORDER
        ),
        "journal_id": ids["journal_id"],
        "partner_id": ids["partner_id"],
        "query": query,
    }
    return request_id, context, filters, limit, cursor


def _validate_invoice_id_request(
    request: Any,
) -> tuple[str, dict[str, Any], int]:
    request_id, context, parameters = _validate_envelope(request)
    if set(parameters) != {"invoice_id"} or not _valid_id(parameters["invoice_id"]):
        raise _invalid("parameters must contain one positive integer invoice_id.")
    return request_id, context, parameters["invoice_id"]


def validate_invoice_get_request(request: Any) -> tuple[str, dict[str, Any], int]:
    return _validate_invoice_id_request(request)


def validate_invoice_payment_status_request(
    request: Any,
) -> tuple[str, dict[str, Any], int]:
    return _validate_invoice_id_request(request)


def _encode_cursor(
    after: list[Any], *, context: dict[str, Any], filters: dict[str, Any]
) -> str:
    payload = json.dumps(
        {
            "after": after,
            "capability": SEARCH_CAPABILITY_ID,
            "company_id": context["company_id"],
            "database": context["database"],
            "filters": filters,
            "user_login": context["user_login"],
            "version": _CURSOR_VERSION,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
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
            parse_constant=_reject_json_constant,
        )
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
    after = value["after"]
    try:
        cursor_filters = _canonical_json(value["filters"])
        request_filters = _canonical_json(filters)
    except (TypeError, ValueError) as exc:
        raise _invalid("The cursor is invalid.", code="invalid_cursor") from exc
    if (
        value["capability"] != SEARCH_CAPABILITY_ID
        or value["version"] != _CURSOR_VERSION
        or not _is_integer(value["version"])
        or not _valid_id(value["company_id"])
        or value["company_id"] != context["company_id"]
        or value["database"] != context["database"]
        or value["user_login"] != context["user_login"]
        or cursor_filters != request_filters
        or not isinstance(after, list)
        or len(after) != 2
        or not _is_date(after[0])
        or not _valid_id(after[1])
    ):
        raise _invalid("The cursor does not match this request.", code="invalid_cursor")
    return after


def _valid_journal(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "code", "name"}
        and _valid_id(value["id"])
        and _is_nonempty_string(value["code"])
        and len(value["code"]) <= 5
        and _is_nonempty_string(value["name"])
    )


def _valid_currency(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "code"}
        and _valid_id(value["id"])
        and _is_nonempty_string(value["code"])
        and len(value["code"]) <= 3
    )


def _valid_named_ref(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "name"}
        and _valid_id(value["id"])
        and _is_nonempty_string(value["name"])
    )


def _valid_optional_named_ref(value: Any) -> bool:
    return value is None or _valid_named_ref(value)


def _valid_account(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "code", "name"}
        and _valid_id(value["id"])
        and _is_nonempty_string(value["code"])
        and _is_nonempty_string(value["name"])
    )


def _valid_header(row: Any, *, company_id: int, fields: frozenset[str]) -> bool:
    if (
        not isinstance(row, dict)
        or set(row) != fields
        or not _valid_id(row["id"])
        or not _valid_optional_string(row["name"])
        or row["move_type"] not in _DOCUMENT_TYPE_ORDER
        or row["state"] not in _STATE_ORDER
        or not _is_date(row["date"])
        or not (
            row["invoice_date"] is None or _is_date(row["invoice_date"])
        )
        or not (
            row["invoice_date_due"] is None or _is_date(row["invoice_date_due"])
        )
        or not all(
            _valid_optional_string(row[key])
            for key in ("ref", "payment_reference", "invoice_origin")
        )
        or not _valid_journal(row["journal"])
        or row["company_id"] != company_id
        or not _valid_currency(row["currency"])
        or not _valid_optional_named_ref(row["partner"])
        or row["payment_state"] not in _PAYMENT_STATE_ORDER
        or not all(
            _is_decimal_string(row[key])
            for key in (
                "amount_untaxed",
                "amount_tax",
                "amount_total",
                "amount_residual",
            )
        )
    ):
        return False
    return Decimal(row["amount_untaxed"]) + Decimal(row["amount_tax"]) == Decimal(
        row["amount_total"]
    )


def _matches_ilike(value: str | None, query: str) -> bool:
    """Mirror Odoo's case-insensitive SQL-like matching for public text fields."""

    if not value:
        return False
    pattern: list[str] = []
    escaped = False
    for char in f"%{query.lower()}%":
        if escaped:
            escaped = False
            pattern.append(re.escape(char))
        elif char == "\\":
            escaped = True
        elif char == "%":
            pattern.append(".*")
        elif char == "_":
            pattern.append(".")
        else:
            pattern.append(re.escape(char))
    return re.compile("".join(pattern), flags=re.DOTALL).fullmatch(value.lower()) is not None


def _validate_page(port: InvoicePort, page: Any, *, payload_key: str) -> Any:
    if not isinstance(page, dict) or set(page) != {
        "user_id",
        "company_visible",
        "module_installed",
        "access_allowed",
        payload_key,
    }:
        raise _failed("Odoo returned an invalid invoice page.")
    payload = page[payload_key]
    payload_present = bool(payload) if payload_key == "rows" else payload is not None
    if (
        not _valid_id(page["user_id"])
        or not _valid_id(port.user_id)
        or page["user_id"] != port.user_id
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
        raise _failed("Odoo returned an invalid invoice page.")
    if not page["company_visible"]:
        raise InvoiceError(
            "company_unavailable",
            "The requested company is unavailable to the configured user.",
            exit_code=3,
        )
    if not page["module_installed"]:
        raise InvoiceError(
            "uninstalled",
            "The invoice capability is not installed in this database.",
            exit_code=4,
        )
    if not page["access_allowed"]:
        raise InvoiceError(
            "unauthorized",
            "The configured user cannot read invoices.",
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
        raise _failed("Odoo returned an invalid invoice search page.")
    previous = tuple(after) if after is not None else None
    record_ids: set[int] = set()
    result: list[dict[str, Any]] = []
    for row in rows:
        if not _valid_header(row, company_id=company_id, fields=_HEADER_FIELDS):
            raise _failed("Odoo returned an invalid or out-of-scope invoice.")
        if (
            (filters["date_from"] is not None and row["date"] < filters["date_from"])
            or (filters["date_to"] is not None and row["date"] > filters["date_to"])
            or (
                filters["document_types"]
                and row["move_type"] not in filters["document_types"]
            )
            or (filters["states"] and row["state"] not in filters["states"])
            or (
                filters["payment_states"]
                and row["payment_state"] not in filters["payment_states"]
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
                filters["query"] is not None
                and not any(
                    _matches_ilike(row[field], filters["query"])
                    for field in (
                        "name",
                        "ref",
                        "payment_reference",
                        "invoice_origin",
                    )
                )
            )
        ):
            raise _failed("Odoo returned an invoice outside the requested filters.")
        current = (row["date"], row["id"])
        if current[1] in record_ids or (previous is not None and current >= previous):
            raise _failed("Odoo returned invoices in an unstable order.")
        record_ids.add(current[1])
        previous = current
        result.append(dict(row))
    return result


def search_invoices(port: InvoicePort, request: dict[str, Any]) -> dict[str, Any]:
    """Read one verified invoice page in date/id descending order."""

    _, context, filters, limit, cursor = validate_invoice_search_request(request)
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
        raise _failed("The Odoo bridge returned an invalid invoice page.") from exc
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


def _valid_tax(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == _TAX_FIELDS
        and _valid_id(value["id"])
        and _is_nonempty_string(value["name"])
        and value["type_tax_use"] in {"sale", "purchase", "none"}
        and _is_nonempty_string(value["amount_type"])
        and _is_decimal_string(value["amount"])
        and isinstance(value["price_include"], bool)
    )


def _validate_invoice(row: Any, *, company_id: int, invoice_id: int) -> dict[str, Any]:
    if (
        not isinstance(row, dict)
        or not _valid_header(
            row,
            company_id=company_id,
            fields=_HEADER_FIELDS | {"partner_bank_id", "fiscal_position_id", "lines"},
        )
        or row["id"] != invoice_id
        or not _valid_optional_id(row["partner_bank_id"])
        or not _valid_optional_id(row["fiscal_position_id"])
        or not isinstance(row["lines"], list)
    ):
        raise _failed("Odoo returned an invalid or out-of-scope invoice.")
    previous: tuple[int, int] | None = None
    line_ids: set[int] = set()
    for line in row["lines"]:
        display_type = line.get("display_type") if isinstance(line, dict) else None
        non_accountable = display_type in _NON_ACCOUNTABLE_TYPES
        if (
            not isinstance(line, dict)
            or set(line) != _LINE_FIELDS
            or not _valid_id(line["id"])
            or not _is_integer(line["sequence"])
            or not (isinstance(display_type, str) and display_type in _DISPLAY_TYPES)
            or not _valid_optional_string(line["name"])
            or not _valid_optional_named_ref(line["product"])
            or (non_accountable and line["account"] is not None)
            or (not non_accountable and not _valid_account(line["account"]))
            or not all(
                _is_decimal_string(line[key])
                for key in (
                    "quantity",
                    "price_unit",
                    "discount",
                    "price_subtotal",
                    "price_total",
                )
            )
            or not all(
                line[field] is None or _is_date(line[field])
                for field in ("deferred_start_date", "deferred_end_date")
            )
            or not isinstance(line["taxes"], list)
            or not _valid_line_analytic_distribution(line["analytic_distribution"])
        ):
            raise _failed("Odoo returned an invalid invoice line.")
        key = (line["sequence"], line["id"])
        if line["id"] in line_ids or (previous is not None and key <= previous):
            raise _failed("Odoo returned invoice lines in an unstable order.")
        line_ids.add(line["id"])
        previous = key
        previous_tax_id: int | None = None
        for tax in line["taxes"]:
            if (
                not _valid_tax(tax)
                or (previous_tax_id is not None and tax["id"] <= previous_tax_id)
            ):
                raise _failed("Odoo returned an invalid invoice-line tax.")
            previous_tax_id = tax["id"]
    return dict(row)


def get_invoice(port: InvoicePort, request: dict[str, Any]) -> dict[str, Any]:
    """Read and verify one exact company-scoped invoice and its invoice lines."""

    _, context, invoice_id = validate_invoice_get_request(request)
    try:
        page = port.get_invoice(
            company_id=context["company_id"], invoice_id=invoice_id
        )
    except ValueError as exc:
        raise _failed("The Odoo bridge returned an invalid invoice page.") from exc
    invoice = _validate_page(port, page, payload_key="invoice")
    if invoice is None:
        raise InvoiceError(
            "record_not_found", "The requested invoice was not found.", exit_code=4
        )
    return _validate_invoice(
        invoice, company_id=context["company_id"], invoice_id=invoice_id
    )


def _valid_receivable_payable_account(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "code", "name", "account_type"}
        and _valid_id(value["id"])
        and _is_nonempty_string(value["code"])
        and _is_nonempty_string(value["name"])
        and value["account_type"] in {"asset_receivable", "liability_payable"}
    )


def _valid_receivable_payable_line(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == _RECEIVABLE_PAYABLE_LINE_FIELDS
        and _valid_id(value["id"])
        and _valid_receivable_payable_account(value["account"])
        and (value["date_maturity"] is None or _is_date(value["date_maturity"]))
        and all(
            _is_decimal_string(value[key])
            for key in (
                "balance",
                "amount_currency",
                "amount_residual",
                "amount_residual_currency",
            )
        )
        and _valid_currency(value["currency"])
        and isinstance(value["reconciled"], bool)
        and _valid_optional_string(value["matching_number"])
    )


def _valid_counterpart_move(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "name", "move_type", "state", "date"}
        and _valid_id(value["id"])
        and _valid_optional_string(value["name"])
        and _is_nonempty_string(value["move_type"])
        and value["state"] in _STATE_ORDER
        and _is_date(value["date"])
    )


def _valid_optional_id(value: Any) -> bool:
    return value is None or _valid_id(value)


def _valid_reconciliation(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == _RECONCILIATION_FIELDS
        and _valid_id(value["id"])
        and _is_date(value["date"])
        and _is_decimal_string(value["amount"])
        and _is_decimal_string(value["company_amount"])
        and _valid_currency(value["currency"])
        and _valid_currency(value["company_currency"])
        and _valid_id(value["invoice_line_id"])
        and _valid_id(value["counterpart_line_id"])
        and _valid_counterpart_move(value["counterpart_move"])
        and _valid_optional_id(value["payment_id"])
        and _valid_optional_id(value["exchange_move_id"])
    )


def _valid_outstanding_item(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == _OUTSTANDING_ITEM_FIELDS
        and _valid_id(value["line_id"])
        and _valid_id(value["move_id"])
        and _valid_optional_id(value["payment_id"])
        and _is_date(value["date"])
        and _is_nonempty_string(value["label"])
        and _is_decimal_string(value["amount"])
        and Decimal(value["amount"]) > 0
        and _valid_currency(value["currency"])
    )


def _valid_payment_method(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "code", "name"}
        and _valid_id(value["id"])
        and _is_nonempty_string(value["code"])
        and _is_nonempty_string(value["name"])
    )


def _valid_payment(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == _PAYMENT_FIELDS
        and _valid_id(value["id"])
        and _valid_optional_string(value["name"])
        and value["state"] in _PAYMENT_STATES
        and _is_date(value["date"])
        and value["payment_type"] in {"inbound", "outbound"}
        and value["partner_type"] in {"customer", "supplier"}
        and _is_decimal_string(value["amount"])
        and _valid_currency(value["currency"])
        and _valid_journal(value["journal"])
        and _valid_payment_method(value["payment_method"])
        and _valid_optional_id(value["move_id"])
        and isinstance(value["is_reconciled"], bool)
        and isinstance(value["is_matched"], bool)
    )


def _validate_payment_status(
    row: Any, *, company_id: int, invoice_id: int
) -> dict[str, Any]:
    if (
        not isinstance(row, dict)
        or set(row) != _PAYMENT_STATUS_FIELDS
        or row["id"] != invoice_id
        or not _valid_id(row["id"])
        or not _valid_optional_string(row["name"])
        or row["move_type"] not in _DOCUMENT_TYPE_ORDER
        or row["state"] not in _STATE_ORDER
        or row["payment_state"] not in _PAYMENT_STATE_ORDER
        or row["company_id"] != company_id
        or not _valid_currency(row["currency"])
        or not _valid_currency(row["company_currency"])
        or not _is_decimal_string(row["amount_total"])
        or not _is_decimal_string(row["amount_residual"])
        or not isinstance(row["receivable_payable_lines"], list)
        or not isinstance(row["reconciliations"], list)
        or not isinstance(row["payments"], list)
        or not isinstance(row["outstanding_items"], list)
    ):
        raise _failed("Odoo returned invalid invoice payment status.")

    previous_line_id: int | None = None
    term_line_ids: set[int] = set()
    for line in row["receivable_payable_lines"]:
        if (
            not _valid_receivable_payable_line(line)
            or (previous_line_id is not None and line["id"] <= previous_line_id)
        ):
            raise _failed("Odoo returned an invalid receivable/payable line.")
        term_line_ids.add(line["id"])
        previous_line_id = line["id"]

    previous_reconciliation: tuple[str, int] | None = None
    reconciliation_ids: set[int] = set()
    for reconciliation in row["reconciliations"]:
        if not _valid_reconciliation(reconciliation):
            raise _failed("Odoo returned an invalid invoice reconciliation.")
        current = (reconciliation["date"], reconciliation["id"])
        if (
            reconciliation["id"] in reconciliation_ids
            or (
                previous_reconciliation is not None
                and current <= previous_reconciliation
            )
        ):
            raise _failed("Odoo returned reconciliations in an unstable order.")
        reconciliation_ids.add(reconciliation["id"])
        previous_reconciliation = current

    previous_payment: tuple[str, int] | None = None
    payments_by_id: dict[int, dict[str, Any]] = {}
    for payment in row["payments"]:
        if not _valid_payment(payment):
            raise _failed("Odoo returned an invalid reconciled payment.")
        current = (payment["date"], payment["id"])
        if (
            payment["id"] in payments_by_id
            or (previous_payment is not None and current >= previous_payment)
        ):
            raise _failed("Odoo returned payments in an unstable order.")
        payments_by_id[payment["id"]] = payment
        previous_payment = current

    for reconciliation in row["reconciliations"]:
        payment_id = reconciliation["payment_id"]
        if (
            reconciliation["invoice_line_id"] not in term_line_ids
            or reconciliation["currency"] != row["currency"]
            or reconciliation["company_currency"] != row["company_currency"]
            or (
                payment_id is not None
                and (
                    payment_id not in payments_by_id
                    or payments_by_id[payment_id]["move_id"]
                    != reconciliation["counterpart_move"]["id"]
                )
            )
        ):
            raise _failed("Odoo returned inconsistent invoice reconciliation links.")

    previous_outstanding: tuple[str, int] | None = None
    outstanding_line_ids: set[int] = set()
    for item in row["outstanding_items"]:
        if not _valid_outstanding_item(item):
            raise _failed("Odoo returned an invalid outstanding payment item.")
        current = (item["date"], item["line_id"])
        if (
            item["line_id"] in outstanding_line_ids
            or (previous_outstanding is not None and current >= previous_outstanding)
            or item["currency"] != row["currency"]
        ):
            raise _failed("Odoo returned outstanding items in an unstable order.")
        outstanding_line_ids.add(item["line_id"])
        previous_outstanding = current
    return dict(row)


def inspect_invoice_payment_status(
    port: InvoicePort, request: dict[str, Any]
) -> dict[str, Any]:
    """Read invoice residuals, partial reconciliations, and reconciled payments."""

    _, context, invoice_id = validate_invoice_payment_status_request(request)
    try:
        page = port.inspect_payment_status(
            company_id=context["company_id"], invoice_id=invoice_id
        )
    except ValueError as exc:
        raise _failed("The Odoo bridge returned invalid invoice payment status.") from exc
    payment_status = _validate_page(port, page, payload_key="payment_status")
    if payment_status is None:
        raise InvoiceError(
            "record_not_found", "The requested invoice was not found.", exit_code=4
        )
    return _validate_payment_status(
        payment_status,
        company_id=context["company_id"],
        invoice_id=invoice_id,
    )
