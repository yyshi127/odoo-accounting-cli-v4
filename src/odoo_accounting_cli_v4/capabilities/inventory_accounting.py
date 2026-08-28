"""Strict contracts for five inventory-accounting read capabilities."""

from __future__ import annotations

import base64
import binascii
import json
import re
import uuid
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol

INVENTORY_ACCOUNTING_CAPABILITY_IDS = frozenset(
    {
        "cogs.entries.list",
        "inventory.accounting_entries.list",
        "report.inventory_valuation",
        "purchase_bill.matching.inspect",
        "sale_invoice.stock_link.inspect",
    }
)
DEFAULT_LIMIT = 100
MAX_LIMIT = 1000
_CURSOR_VERSION = 1
_LIST_CAPABILITIES = frozenset(
    {"cogs.entries.list", "inventory.accounting_entries.list"}
)
_DECIMAL_PATTERN = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
_UTC_DATETIME_PATTERN = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
)
_MOVE_STATES = frozenset({"draft", "posted", "cancel"})


class InventoryAccountingPort(Protocol):
    @property
    def user_id(self) -> int: ...

    def read(
        self,
        *,
        capability_id: str,
        company_id: int,
        parameters: dict[str, Any],
    ) -> dict[str, Any]: ...


class InventoryAccountingError(RuntimeError):
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
) -> InventoryAccountingError:
    return InventoryAccountingError(code, message, exit_code=2)


def _failed(message: str) -> InventoryAccountingError:
    return InventoryAccountingError("failed_validation", message, exit_code=8)


def _require_capability(capability_id: Any) -> str:
    if (
        not isinstance(capability_id, str)
        or capability_id not in INVENTORY_ACCOUNTING_CAPABILITY_IDS
    ):
        raise InventoryAccountingError(
            "unsupported_capability",
            "The inventory-accounting capability is unsupported.",
            exit_code=4,
        )
    return capability_id


def _is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _valid_id(value: Any) -> bool:
    return _is_integer(value) and value > 0


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def _context_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _optional_text(value: Any) -> bool:
    return value is None or _text(value)


def _date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return False
    return parsed.isoformat() == value


def _utc_datetime(value: Any) -> bool:
    if not isinstance(value, str) or _UTC_DATETIME_PATTERN.fullmatch(value) is None:
        return False
    try:
        datetime.fromisoformat(value)
    except ValueError:
        return False
    return True


def _decimal(value: Any, *, nonnegative: bool = False) -> Decimal | None:
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
    if not parsed.is_finite() or (nonnegative and parsed < 0):
        return None
    return parsed


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
    except (AttributeError, ValueError) as exc:
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
        if not _context_text(context[key]):
            raise _invalid(f"context.{key} must be a non-empty string.")
    if not _valid_id(context["company_id"]):
        raise _invalid("context.company_id must be a positive integer.")
    parameters = request["parameters"]
    if not isinstance(parameters, dict):
        raise _invalid("parameters must be an object.")
    return request_id, context, parameters


def _optional_id(parameters: dict[str, Any], key: str) -> int | None:
    value = parameters.get(key)
    if value is not None and not _valid_id(value):
        raise _invalid(f"parameters.{key} must be null or a positive integer.")
    return value


def _list_parameters(capability_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
    optional_ids = {"product_id"}
    if capability_id == "cogs.entries.list":
        optional_ids.add("invoice_id")
    allowed = {"date_from", "date_to", "limit", "cursor", *optional_ids}
    if not set(parameters) <= allowed:
        raise _invalid(f"{capability_id} contains an unsupported parameter.")

    date_from = parameters.get("date_from")
    date_to = parameters.get("date_to")
    if date_from is not None and not _date(date_from):
        raise _invalid("parameters.date_from must be null or a YYYY-MM-DD date.")
    if date_to is not None and not _date(date_to):
        raise _invalid("parameters.date_to must be null or a YYYY-MM-DD date.")
    if date_from is not None and date_to is not None and date_from > date_to:
        raise _invalid("parameters.date_from cannot be after parameters.date_to.")

    limit = parameters.get("limit", DEFAULT_LIMIT)
    if not _is_integer(limit) or not 1 <= limit <= MAX_LIMIT:
        raise _invalid(f"parameters.limit must be between 1 and {MAX_LIMIT}.")
    cursor = parameters.get("cursor")
    if cursor is not None and (
        not isinstance(cursor, str) or not cursor or len(cursor) > 4096
    ):
        raise _invalid("parameters.cursor must be null or a non-empty cursor string.")

    normalized: dict[str, Any] = {
        "date_from": date_from,
        "date_to": date_to,
    }
    for key in sorted(optional_ids):
        normalized[key] = _optional_id(parameters, key)
    normalized.update({"limit": limit, "cursor": cursor})
    return normalized


def validate_inventory_accounting_request(
    capability_id: str, request: Any
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    """Validate and normalize one closed inventory-accounting request."""

    _require_capability(capability_id)
    request_id, context, parameters = _validate_envelope(request)
    if capability_id in _LIST_CAPABILITIES:
        normalized = _list_parameters(capability_id, parameters)
    elif capability_id == "report.inventory_valuation":
        if not set(parameters) <= {"date"}:
            raise _invalid(f"{capability_id} contains an unsupported parameter.")
        report_date = parameters.get("date")
        if report_date is not None and not _date(report_date):
            raise _invalid("parameters.date must be null or a YYYY-MM-DD date.")
        normalized = {"date": report_date}
    else:
        key = (
            "bill_id"
            if capability_id == "purchase_bill.matching.inspect"
            else "invoice_id"
        )
        if set(parameters) != {key} or not _valid_id(parameters.get(key)):
            raise _invalid(f"parameters must contain one positive integer {key}.")
        normalized = {key: parameters[key]}
    return request_id, context, normalized


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


def _cursor_filters(capability_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in parameters.items()
        if key not in {"limit", "cursor"}
    }


def _cursor_binding(
    capability_id: str, context: dict[str, Any], filters: dict[str, Any]
) -> str:
    return _canonical_json(
        {
            "capability": capability_id,
            "company_id": context["company_id"],
            "database": context["database"],
            "filters": filters,
            "user_login": context["user_login"],
        }
    )


def _valid_after(capability_id: str, value: Any) -> bool:
    if not isinstance(value, list) or len(value) != 2 or not _valid_id(value[1]):
        return False
    if capability_id == "cogs.entries.list":
        return _date(value[0])
    return _utc_datetime(value[0])


def _encode_cursor(
    capability_id: str,
    after: list[Any],
    *,
    context: dict[str, Any],
    filters: dict[str, Any],
) -> str:
    payload = _canonical_json(
        {
            "after": after,
            "binding": _cursor_binding(capability_id, context, filters),
            "version": _CURSOR_VERSION,
        }
    ).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def _decode_cursor(
    capability_id: str,
    cursor: str,
    *,
    context: dict[str, Any],
    filters: dict[str, Any],
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
        or value["version"] != _CURSOR_VERSION
        or value["binding"] != _cursor_binding(capability_id, context, filters)
        or not _valid_after(capability_id, value["after"])
    ):
        raise _invalid("The cursor does not match this request.", code="invalid_cursor")
    return value["after"]


def _id_list(value: Any) -> bool:
    return (
        isinstance(value, list)
        and all(_valid_id(item) for item in value)
        and value == sorted(set(value))
    )


def _named_ref(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "name"}
        and _valid_id(value["id"])
        and _text(value["name"])
    )


def _optional_named_ref(value: Any) -> bool:
    return value is None or _named_ref(value)


def _account(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "code", "name"}
        and _valid_id(value["id"])
        and _text(value["code"])
        and _text(value["name"])
    )


def _currency(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "code"}
        and _valid_id(value["id"])
        and _text(value["code"])
        and len(value["code"]) <= 3
    )


def _journal(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "code", "name"}
        and _valid_id(value["id"])
        and _text(value["code"])
        and len(value["code"]) <= 5
        and _text(value["name"])
    )


def _accounting_line(value: Any) -> bool:
    if not isinstance(value, dict) or set(value) != {
        "id",
        "account",
        "debit",
        "credit",
        "balance",
    }:
        return False
    debit = _decimal(value["debit"], nonnegative=True)
    credit = _decimal(value["credit"], nonnegative=True)
    balance = _decimal(value["balance"])
    return (
        _valid_id(value["id"])
        and _account(value["account"])
        and debit is not None
        and credit is not None
        and balance is not None
        and balance == debit - credit
    )


def _accounting_lines(value: Any) -> bool:
    if not isinstance(value, list) or not value:
        return False
    if any(not _accounting_line(item) for item in value):
        return False
    ids = [item["id"] for item in value]
    balances = [_decimal(item["balance"]) for item in value]
    return ids == sorted(set(ids)) and sum(balances, Decimal(0)) == 0


def _cogs_item(row: Any, *, company_id: int, parameters: dict[str, Any]) -> bool:
    if not isinstance(row, dict) or set(row) != {
        "id",
        "date",
        "company_id",
        "invoice",
        "origin_invoice_line_id",
        "account",
        "product",
        "label",
        "quantity",
        "debit",
        "credit",
        "balance",
        "company_currency",
        "sale_order_line_ids",
        "stock_move_ids",
    }:
        return False
    invoice = row["invoice"]
    debit = _decimal(row["debit"], nonnegative=True)
    credit = _decimal(row["credit"], nonnegative=True)
    balance = _decimal(row["balance"])
    if not (
        _valid_id(row["id"])
        and _date(row["date"])
        and row["company_id"] == company_id
        and isinstance(invoice, dict)
        and set(invoice) == {"id", "name", "move_type", "state"}
        and _valid_id(invoice["id"])
        and _optional_text(invoice["name"])
        and invoice["move_type"] in {"out_invoice", "out_refund"}
        and invoice["state"] == "posted"
        and (
            row["origin_invoice_line_id"] is None
            or _valid_id(row["origin_invoice_line_id"])
        )
        and _account(row["account"])
        and _optional_named_ref(row["product"])
        and _optional_text(row["label"])
        and _decimal(row["quantity"]) is not None
        and debit is not None
        and credit is not None
        and balance is not None
        and balance == debit - credit
        and _currency(row["company_currency"])
        and _id_list(row["sale_order_line_ids"])
        and _id_list(row["stock_move_ids"])
    ):
        return False
    return not (
        parameters["date_from"] is not None
        and row["date"] < parameters["date_from"]
        or parameters["date_to"] is not None
        and row["date"] > parameters["date_to"]
        or parameters["invoice_id"] is not None
        and invoice["id"] != parameters["invoice_id"]
        or parameters["product_id"] is not None
        and (row["product"] is None or row["product"]["id"] != parameters["product_id"])
    )


def _inventory_item(row: Any, *, company_id: int, parameters: dict[str, Any]) -> bool:
    if not isinstance(row, dict) or set(row) != {
        "id",
        "date",
        "company_id",
        "reference",
        "state",
        "product",
        "quantity",
        "uom",
        "value",
        "is_in",
        "is_out",
        "account_move",
        "lines",
        "company_currency",
    }:
        return False
    account_move = row["account_move"]
    if not (
        _valid_id(row["id"])
        and _utc_datetime(row["date"])
        and row["company_id"] == company_id
        and _optional_text(row["reference"])
        and row["state"] == "done"
        and _named_ref(row["product"])
        and _decimal(row["quantity"]) is not None
        and _named_ref(row["uom"])
        and _decimal(row["value"]) is not None
        and isinstance(row["is_in"], bool)
        and isinstance(row["is_out"], bool)
        and isinstance(account_move, dict)
        and set(account_move) == {"id", "name", "date", "state", "journal"}
        and _valid_id(account_move["id"])
        and _optional_text(account_move["name"])
        and _date(account_move["date"])
        and account_move["state"] == "posted"
        and _journal(account_move["journal"])
        and _accounting_lines(row["lines"])
        and _currency(row["company_currency"])
    ):
        return False
    row_date = row["date"][:10]
    return not (
        parameters["date_from"] is not None
        and row_date < parameters["date_from"]
        or parameters["date_to"] is not None
        and row_date > parameters["date_to"]
        or parameters["product_id"] is not None
        and row["product"]["id"] != parameters["product_id"]
    )


def _valuation_item(row: Any, *, company_id: int, parameters: dict[str, Any]) -> bool:
    if not isinstance(row, dict) or set(row) != {
        "as_of_date",
        "company",
        "currency",
        "initial_balance",
        "ending_stock",
        "stock_variation",
        "inventory_loss",
        "not_invoiced_delivered_goods",
        "not_invoiced_received_goods",
        "cost_of_production",
        "accounts",
    }:
        return False
    company = row["company"]
    initial = _decimal(row["initial_balance"])
    ending = _decimal(row["ending_stock"])
    variation = _decimal(row["stock_variation"])
    if not (
        row["as_of_date"] == parameters["date"]
        and isinstance(company, dict)
        and set(company) == {"id", "name"}
        and company["id"] == company_id
        and _text(company["name"])
        and _currency(row["currency"])
        and initial is not None
        and ending is not None
        and variation is not None
    ):
        return False
    for key in (
        "inventory_loss",
        "not_invoiced_delivered_goods",
        "not_invoiced_received_goods",
        "cost_of_production",
    ):
        if row[key] is not None and _decimal(row[key]) is None:
            return False
    accounts = row["accounts"]
    if not isinstance(accounts, list):
        return False
    previous = 0
    initial_total = Decimal(0)
    ending_total = Decimal(0)
    variation_total = Decimal(0)
    for item in accounts:
        if not isinstance(item, dict) or set(item) != {
            "account",
            "initial_balance",
            "ending_stock",
            "variation_debit",
            "variation_credit",
        }:
            return False
        account = item["account"]
        item_initial = _decimal(item["initial_balance"])
        item_ending = _decimal(item["ending_stock"])
        item_debit = _decimal(item["variation_debit"], nonnegative=True)
        item_credit = _decimal(item["variation_credit"], nonnegative=True)
        if not (
            _account(account)
            and account["id"] > previous
            and item_initial is not None
            and item_ending is not None
            and item_debit is not None
            and item_credit is not None
        ):
            return False
        previous = account["id"]
        initial_total += item_initial
        ending_total += item_ending
        variation_total += item_debit
    return (
        initial_total == initial
        and ending_total == ending
        and variation_total == variation
    )


def _purchase_line(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value)
        == {
            "id",
            "order_id",
            "ordered_quantity",
            "received_quantity",
            "invoiced_quantity",
            "to_invoice_quantity",
        }
        and _valid_id(value["id"])
        and _valid_id(value["order_id"])
        and all(
            _decimal(value[key]) is not None
            for key in (
                "ordered_quantity",
                "received_quantity",
                "invoiced_quantity",
                "to_invoice_quantity",
            )
        )
    )


def _purchase_item(row: Any, *, company_id: int, parameters: dict[str, Any]) -> bool:
    if not isinstance(row, dict) or set(row) != {
        "id",
        "name",
        "move_type",
        "state",
        "company_id",
        "partner",
        "currency",
        "is_purchase_matched",
        "purchase_order_ids",
        "lines",
    }:
        return False
    if not (
        row["id"] == parameters["bill_id"]
        and _optional_text(row["name"])
        and row["move_type"] in {"in_invoice", "in_refund"}
        and row["state"] in _MOVE_STATES
        and row["company_id"] == company_id
        and _optional_named_ref(row["partner"])
        and _currency(row["currency"])
        and isinstance(row["is_purchase_matched"], bool)
        and _id_list(row["purchase_order_ids"])
        and isinstance(row["lines"], list)
    ):
        return False
    previous = 0
    order_ids: set[int] = set()
    matched = True
    for line in row["lines"]:
        if not isinstance(line, dict) or set(line) != {
            "id",
            "product",
            "label",
            "quantity",
            "price_subtotal",
            "purchase_line",
            "unmatched_queue",
        }:
            return False
        purchase_line = line["purchase_line"]
        if not (
            _valid_id(line["id"])
            and line["id"] > previous
            and _optional_named_ref(line["product"])
            and _optional_text(line["label"])
            and _decimal(line["quantity"]) is not None
            and _decimal(line["price_subtotal"]) is not None
            and (purchase_line is None or _purchase_line(purchase_line))
            and isinstance(line["unmatched_queue"], bool)
            and line["unmatched_queue"] == (purchase_line is None)
        ):
            return False
        previous = line["id"]
        matched = matched and purchase_line is not None
        if purchase_line is not None:
            order_ids.add(purchase_line["order_id"])
    return (
        row["purchase_order_ids"] == sorted(order_ids)
        and row["is_purchase_matched"] == matched
    )


def _accounting_entry(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "name", "date", "state", "lines"}
        and _valid_id(value["id"])
        and _optional_text(value["name"])
        and _date(value["date"])
        and value["state"] == "posted"
        and _accounting_lines(value["lines"])
    )


def _stock_move(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value)
        == {
            "id",
            "date",
            "state",
            "reference",
            "product",
            "quantity",
            "uom",
            "value",
            "accounting_entry",
        }
        and _valid_id(value["id"])
        and _utc_datetime(value["date"])
        and value["state"] == "done"
        and _optional_text(value["reference"])
        and _named_ref(value["product"])
        and _decimal(value["quantity"]) is not None
        and _named_ref(value["uom"])
        and _decimal(value["value"]) is not None
        and (
            value["accounting_entry"] is None
            or _accounting_entry(value["accounting_entry"])
        )
    )


def _sale_item(row: Any, *, company_id: int, parameters: dict[str, Any]) -> bool:
    if not isinstance(row, dict) or set(row) != {
        "id",
        "name",
        "move_type",
        "state",
        "company_id",
        "lines",
        "stock_move_ids",
        "account_move_ids",
    }:
        return False
    if not (
        row["id"] == parameters["invoice_id"]
        and _optional_text(row["name"])
        and row["move_type"] in {"out_invoice", "out_refund"}
        and row["state"] in _MOVE_STATES
        and row["company_id"] == company_id
        and isinstance(row["lines"], list)
        and _id_list(row["stock_move_ids"])
        and _id_list(row["account_move_ids"])
    ):
        return False
    previous_line = 0
    stock_move_ids: set[int] = set()
    account_move_ids: set[int] = set()
    for line in row["lines"]:
        if not isinstance(line, dict) or set(line) != {
            "id",
            "product",
            "quantity",
            "sale_order_line_ids",
            "stock_moves",
        }:
            return False
        if not (
            _valid_id(line["id"])
            and line["id"] > previous_line
            and _optional_named_ref(line["product"])
            and _decimal(line["quantity"]) is not None
            and _id_list(line["sale_order_line_ids"])
            and isinstance(line["stock_moves"], list)
        ):
            return False
        previous_line = line["id"]
        previous_move = 0
        for move in line["stock_moves"]:
            if not _stock_move(move) or move["id"] <= previous_move:
                return False
            previous_move = move["id"]
            stock_move_ids.add(move["id"])
            if move["accounting_entry"] is not None:
                account_move_ids.add(move["accounting_entry"]["id"])
    return row["stock_move_ids"] == sorted(stock_move_ids) and row[
        "account_move_ids"
    ] == sorted(account_move_ids)


def _validate_page(port: InventoryAccountingPort, page: Any) -> list[dict[str, Any]]:
    if not isinstance(page, dict) or set(page) != {
        "user_id",
        "company_visible",
        "module_installed",
        "access_allowed",
        "cursor_found",
        "items",
    }:
        raise _failed("Odoo returned an invalid inventory-accounting page.")
    try:
        user_id = port.user_id
    except ValueError as exc:
        raise _failed("Odoo returned an invalid inventory-accounting page.") from exc
    if (
        not _valid_id(page["user_id"])
        or not _valid_id(user_id)
        or page["user_id"] != user_id
        or not isinstance(page["company_visible"], bool)
        or not isinstance(page["module_installed"], bool)
        or not isinstance(page["access_allowed"], bool)
        or not isinstance(page["cursor_found"], bool)
        or not isinstance(page["items"], list)
        or any(not isinstance(item, dict) for item in page["items"])
        or (
            page["access_allowed"]
            and not (page["company_visible"] and page["module_installed"])
        )
        or (not page["access_allowed"] and bool(page["items"]))
        or (not page["cursor_found"] and bool(page["items"]))
    ):
        raise _failed("Odoo returned an invalid inventory-accounting page.")
    if not page["company_visible"]:
        raise InventoryAccountingError(
            "company_unavailable",
            "The requested company is unavailable to the configured user.",
            exit_code=3,
        )
    if not page["module_installed"]:
        raise InventoryAccountingError(
            "uninstalled",
            "The inventory-accounting capability is not installed in this database.",
            exit_code=4,
        )
    if not page["access_allowed"]:
        raise InventoryAccountingError(
            "unauthorized",
            "The configured user cannot read this inventory-accounting data.",
            exit_code=3,
        )
    return page["items"]


def _read_list(
    port: InventoryAccountingPort,
    capability_id: str,
    context: dict[str, Any],
    parameters: dict[str, Any],
) -> dict[str, Any]:
    filters = _cursor_filters(capability_id, parameters)
    cursor = parameters["cursor"]
    after = (
        _decode_cursor(
            capability_id,
            cursor,
            context=context,
            filters=filters,
        )
        if cursor is not None
        else None
    )
    port_parameters = {**filters, "after": after, "limit": parameters["limit"] + 1}
    page = port.read(
        capability_id=capability_id,
        company_id=context["company_id"],
        parameters=port_parameters,
    )
    rows = _validate_page(port, page)
    if not page["cursor_found"]:
        if cursor is not None:
            raise _invalid("The cursor boundary is unavailable.", code="invalid_cursor")
        raise _failed("Odoo returned an invalid inventory-accounting page.")
    if len(rows) > parameters["limit"] + 1:
        raise _failed("Odoo returned too many inventory-accounting records.")
    validator = _cogs_item if capability_id == "cogs.entries.list" else _inventory_item
    previous = tuple(after) if after is not None else None
    record_ids: set[int] = set()
    verified: list[dict[str, Any]] = []
    for row in rows:
        if not validator(row, company_id=context["company_id"], parameters=parameters):
            raise _failed("Odoo returned invalid or out-of-scope inventory data.")
        current = (row["date"], row["id"])
        if row["id"] in record_ids or (previous is not None and current >= previous):
            raise _failed("Odoo returned inventory data in an unstable order.")
        record_ids.add(row["id"])
        previous = current
        verified.append(dict(row))
    has_more = len(verified) > parameters["limit"]
    items = verified[: parameters["limit"]]
    next_cursor = None
    if has_more and items:
        next_cursor = _encode_cursor(
            capability_id,
            [items[-1]["date"], items[-1]["id"]],
            context=context,
            filters=filters,
        )
    return {"items": items, "has_more": has_more, "next_cursor": next_cursor}


def read_inventory_accounting(
    capability_id: str,
    port: InventoryAccountingPort,
    request: dict[str, Any],
) -> dict[str, Any]:
    """Read and verify one fixed inventory-accounting result."""

    _, context, parameters = validate_inventory_accounting_request(
        capability_id, request
    )
    if capability_id in _LIST_CAPABILITIES:
        return _read_list(port, capability_id, context, parameters)

    page = port.read(
        capability_id=capability_id,
        company_id=context["company_id"],
        parameters=parameters,
    )
    rows = _validate_page(port, page)
    if not page["cursor_found"]:
        raise _failed("Odoo returned an invalid inventory-accounting page.")
    if capability_id == "report.inventory_valuation":
        if len(rows) != 1 or not _valuation_item(
            rows[0], company_id=context["company_id"], parameters=parameters
        ):
            raise _failed("Odoo returned an invalid inventory-valuation report.")
        return dict(rows[0])

    if not rows:
        noun = (
            "bill" if capability_id == "purchase_bill.matching.inspect" else "invoice"
        )
        raise InventoryAccountingError(
            "record_not_found",
            f"The requested {noun} was not found.",
            exit_code=4,
        )
    if len(rows) != 1:
        raise _failed("Odoo returned an invalid inventory-accounting inspection.")
    validator = (
        _purchase_item
        if capability_id == "purchase_bill.matching.inspect"
        else _sale_item
    )
    if not validator(rows[0], company_id=context["company_id"], parameters=parameters):
        raise _failed("Odoo returned an invalid inventory-accounting inspection.")
    return dict(rows[0])
