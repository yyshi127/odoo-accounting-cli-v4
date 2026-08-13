"""Strict contract for Odoo's default Journal Items to reconcile page."""

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


CAPABILITY_ID = "reconciliation.candidates.list"
DEFAULT_LIMIT = 100
MAX_LIMIT = 1000
_CURSOR_VERSION = 1
_DECIMAL_PATTERN = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
_ACCOUNT_CODE_PATTERN = re.compile(r"^[A-Za-z0-9.]+$")
_STATES = ("draft", "posted")
_ACCOUNT_KINDS = ("receivable", "payable", "other")
_MOVE_TYPES = frozenset(
    {
        "entry",
        "out_invoice",
        "out_refund",
        "in_invoice",
        "in_refund",
        "out_receipt",
        "in_receipt",
    }
)
_JOURNAL_TYPES = frozenset(
    {"sale", "purchase", "cash", "bank", "credit", "general"}
)
_ACCOUNT_TYPES = frozenset(
    {
        "asset_receivable",
        "asset_cash",
        "asset_current",
        "asset_non_current",
        "asset_prepayments",
        "asset_fixed",
        "liability_payable",
        "liability_credit_card",
        "liability_current",
        "liability_non_current",
        "equity",
        "equity_unaffected",
        "income",
        "income_other",
        "expense",
        "expense_depreciation",
        "expense_direct_cost",
        "expense_other",
        "off_balance",
    }
)
_FILTER_FIELDS = frozenset(
    {
        "date_from",
        "date_to",
        "states",
        "account_id",
        "partner_id",
        "journal_id",
        "account_kinds",
        "query",
    }
)
_ROW_FIELDS = frozenset(
    {
        "id",
        "date",
        "invoice_date",
        "date_maturity",
        "state",
        "move",
        "label",
        "account",
        "partner",
        "journal",
        "company_id",
        "company_currency",
        "currency",
        "balance",
        "amount_currency",
        "amount_residual",
        "amount_residual_currency",
        "matching_number",
        "reconciliation_model",
    }
)
_MONEY_FIELDS = (
    "balance",
    "amount_currency",
    "amount_residual",
    "amount_residual_currency",
)


class ReconciliationCandidatesPort(Protocol):
    @property
    def user_id(self) -> int: ...

    def read_page(
        self,
        *,
        company_id: int,
        after: list[Any] | None,
        limit: int,
        filters: dict[str, Any],
    ) -> dict[str, Any]: ...


class ReconciliationCandidatesError(RuntimeError):
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
) -> ReconciliationCandidatesError:
    return ReconciliationCandidatesError(code, message, exit_code=2)


def _failed(message: str) -> ReconciliationCandidatesError:
    return ReconciliationCandidatesError("failed_validation", message, exit_code=8)


def _is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _valid_id(value: Any) -> bool:
    return _is_integer(value) and value > 0


def _is_context_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_text(value: Any) -> bool:
    return isinstance(value, str) and len(value) > 0


def _valid_optional_text(value: Any) -> bool:
    return value is None or _is_text(value)


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
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate cursor key")
        value[key] = item
    return value


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
        if not _is_context_text(context[key]):
            raise _invalid(f"context.{key} must be a non-empty string.")
    if not _valid_id(context["company_id"]):
        raise _invalid("context.company_id must be a positive integer.")
    parameters = request["parameters"]
    if not isinstance(parameters, dict):
        raise _invalid("parameters must be an object.")
    return request_id, context, parameters


def _normalize_selection(
    parameters: dict[str, Any],
    key: str,
    canonical_order: tuple[str, ...],
    default: tuple[str, ...],
) -> list[str]:
    if key not in parameters:
        return list(default)
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


def validate_reconciliation_candidates_request(
    request: Any,
) -> tuple[str, dict[str, Any], dict[str, Any], int, str | None]:
    """Validate and normalize the closed candidate-list request."""

    request_id, context, parameters = _validate_envelope(request)
    if not set(parameters) <= _FILTER_FIELDS | {"limit", "cursor"}:
        raise _invalid(f"{CAPABILITY_ID} contains an unsupported parameter.")

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
    for key in ("account_id", "partner_id", "journal_id"):
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
        "states": _normalize_selection(
            parameters, "states", _STATES, ("posted",)
        ),
        "account_id": identifiers["account_id"],
        "partner_id": identifiers["partner_id"],
        "journal_id": identifiers["journal_id"],
        "account_kinds": _normalize_selection(
            parameters, "account_kinds", _ACCOUNT_KINDS, _ACCOUNT_KINDS
        ),
        "query": query,
    }
    return request_id, context, filters, limit, cursor


def _cursor_binding(context: dict[str, Any], filters: dict[str, Any]) -> str:
    value = {
        "capability": CAPABILITY_ID,
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
        and _is_text(value["code"])
        and len(value["code"]) <= 3
    )


def _valid_move(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "name", "move_type", "ref"}
        and _valid_id(value["id"])
        and _valid_optional_text(value["name"])
        and value["move_type"] in _MOVE_TYPES
        and _valid_optional_text(value["ref"])
    )


def _valid_account(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "code", "name", "account_type"}
        and _valid_id(value["id"])
        and isinstance(value["code"], str)
        and 1 <= len(value["code"]) <= 64
        and _ACCOUNT_CODE_PATTERN.fullmatch(value["code"]) is not None
        and _is_text(value["name"])
        and value["account_type"] in _ACCOUNT_TYPES
    )


def _valid_partner(value: Any) -> bool:
    return value is None or (
        isinstance(value, dict)
        and set(value) == {"id", "name"}
        and _valid_id(value["id"])
        and _valid_optional_text(value["name"])
    )


def _valid_journal(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "code", "name", "type"}
        and _valid_id(value["id"])
        and _is_text(value["code"])
        and len(value["code"]) <= 5
        and _is_text(value["name"])
        and value["type"] in _JOURNAL_TYPES
    )


def _valid_reconciliation_model(value: Any) -> bool:
    return value is None or (
        isinstance(value, dict)
        and set(value) == {"id", "name"}
        and _valid_id(value["id"])
        and _is_text(value["name"])
    )


def _account_kind(account_type: str) -> str:
    if account_type == "asset_receivable":
        return "receivable"
    if account_type == "liability_payable":
        return "payable"
    return "other"


def _valid_row(row: Any, *, company_id: int) -> bool:
    if (
        not isinstance(row, dict)
        or set(row) != _ROW_FIELDS
        or not _valid_id(row["id"])
        or not _is_date(row["date"])
        or not (row["invoice_date"] is None or _is_date(row["invoice_date"]))
        or not (row["date_maturity"] is None or _is_date(row["date_maturity"]))
        or row["state"] not in _STATES
        or not _valid_move(row["move"])
        or not _valid_optional_text(row["label"])
        or not _valid_account(row["account"])
        or not _valid_partner(row["partner"])
        or not _valid_journal(row["journal"])
        or row["company_id"] != company_id
        or not _valid_currency(row["company_currency"])
        or not _valid_currency(row["currency"])
        or not _valid_optional_text(row["matching_number"])
        or not _valid_reconciliation_model(row["reconciliation_model"])
    ):
        return False

    amounts = {field: _decimal(row[field]) for field in _MONEY_FIELDS}
    if any(value is None for value in amounts.values()):
        return False
    if amounts["amount_residual"] == 0:
        # Mirrors account_accountant's default "With residual" action filter.
        return False
    if row["currency"]["id"] == row["company_currency"]["id"]:
        if (
            row["currency"]["code"] != row["company_currency"]["code"]
            or amounts["balance"] != amounts["amount_currency"]
            or amounts["amount_residual"] != amounts["amount_residual_currency"]
        ):
            return False
    return True


def _validate_page(port: ReconciliationCandidatesPort, page: Any) -> list[Any]:
    if not isinstance(page, dict) or set(page) != {
        "user_id",
        "company_visible",
        "module_installed",
        "access_allowed",
        "rows",
    }:
        raise _failed("Odoo returned an invalid reconciliation-candidate page.")
    rows = page["rows"]
    try:
        port_user_id = port.user_id
    except ValueError as exc:
        raise _failed("Odoo returned an invalid reconciliation-candidate page.") from exc
    if (
        not _valid_id(page["user_id"])
        or not _valid_id(port_user_id)
        or page["user_id"] != port_user_id
        or not isinstance(page["company_visible"], bool)
        or not isinstance(page["module_installed"], bool)
        or not isinstance(page["access_allowed"], bool)
        or not isinstance(rows, list)
        or (page["access_allowed"] and not (
            page["company_visible"] and page["module_installed"]
        ))
        or (not page["access_allowed"] and bool(rows))
    ):
        raise _failed("Odoo returned an invalid reconciliation-candidate page.")
    if not page["company_visible"]:
        raise ReconciliationCandidatesError(
            "company_unavailable",
            "The requested company is unavailable to the configured user.",
            exit_code=3,
        )
    if not page["module_installed"]:
        raise ReconciliationCandidatesError(
            "uninstalled",
            "The reconciliation-candidate capability is not installed in this database.",
            exit_code=4,
        )
    if not page["access_allowed"]:
        raise ReconciliationCandidatesError(
            "unauthorized",
            "The configured user cannot read reconciliation candidates.",
            exit_code=3,
        )
    return rows


def _validate_rows(
    rows: Any,
    *,
    company_id: int,
    after: list[Any] | None,
    filters: dict[str, Any],
    maximum: int,
) -> list[dict[str, Any]]:
    if not isinstance(rows, list) or len(rows) > maximum:
        raise _failed("Odoo returned an invalid reconciliation-candidate page.")
    previous = tuple(after) if after is not None else None
    record_ids: set[int] = set()
    result: list[dict[str, Any]] = []
    for row in rows:
        if not _valid_row(row, company_id=company_id):
            raise _failed("Odoo returned an invalid or out-of-scope candidate.")
        current = (row["date"], row["id"])
        if row["id"] in record_ids or (previous is not None and current >= previous):
            raise _failed("Odoo returned candidates in an unstable order.")
        account_kind = _account_kind(row["account"]["account_type"])
        if (
            (filters["date_from"] is not None and row["date"] < filters["date_from"])
            or (filters["date_to"] is not None and row["date"] > filters["date_to"])
            or row["state"] not in filters["states"]
            or (
                filters["account_id"] is not None
                and row["account"]["id"] != filters["account_id"]
            )
            or (
                filters["partner_id"] is not None
                and (
                    row["partner"] is None
                    or row["partner"]["id"] != filters["partner_id"]
                )
            )
            or (
                filters["journal_id"] is not None
                and row["journal"]["id"] != filters["journal_id"]
            )
            or account_kind not in filters["account_kinds"]
        ):
            raise _failed("Odoo returned a candidate outside the requested filters.")
        record_ids.add(row["id"])
        previous = current
        result.append(dict(row))
    return result


def list_reconciliation_candidates(
    port: ReconciliationCandidatesPort, request: dict[str, Any]
) -> dict[str, Any]:
    """Read one verified page from the default enterprise candidate action."""

    _, context, filters, limit, cursor = validate_reconciliation_candidates_request(
        request
    )
    after = _decode_cursor(cursor, context=context, filters=filters) if cursor else None
    fetch_limit = limit + 1
    try:
        page = port.read_page(
            company_id=context["company_id"],
            after=after,
            limit=fetch_limit,
            filters=filters,
        )
    except ValueError as exc:
        raise _failed(
            "The Odoo bridge returned an invalid reconciliation-candidate page."
        ) from exc
    rows = _validate_page(port, page)
    records = _validate_rows(
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
