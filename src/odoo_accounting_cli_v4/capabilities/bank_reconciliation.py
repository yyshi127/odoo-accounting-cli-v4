"""Closed reads for one bank transaction's reconciliation state and candidates."""

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

from odoo_accounting_cli_v4.capabilities.reconciliation_candidates import (
    _valid_row as _valid_candidate_row,
)

GET_CAPABILITY_ID = "bank.transaction.reconciliation.get"
CANDIDATES_CAPABILITY_ID = "bank.transaction.match_candidates.list"
DEFAULT_LIMIT = 100
MAX_LIMIT = 1000
_CURSOR_VERSION = 1
_DECIMAL_PATTERN = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
_GATE_FIELDS = {
    "user_id",
    "company_visible",
    "module_installed",
    "access_allowed",
}


class BankReconciliationPort(Protocol):
    @property
    def user_id(self) -> int: ...

    def get(self, *, company_id: int, transaction_id: int) -> dict[str, Any]: ...

    def read_candidates_page(
        self,
        *,
        company_id: int,
        transaction_id: int,
        after: list[Any] | None,
        limit: int,
    ) -> dict[str, Any]: ...


class BankReconciliationError(RuntimeError):
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


def _invalid(message: str, *, code: str = "invalid_request") -> BankReconciliationError:
    return BankReconciliationError(code, message, exit_code=2)


def _failed(message: str) -> BankReconciliationError:
    return BankReconciliationError("failed_validation", message, exit_code=8)


def _is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _valid_id(value: Any) -> bool:
    return _is_integer(value) and value > 0


def _valid_optional_id(value: Any) -> bool:
    return value is None or _valid_id(value)


def _valid_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _valid_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return False
    return parsed.isoformat() == value


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
    for field in ("database", "user_login", "language", "timezone"):
        if not _valid_text(context[field]):
            raise _invalid(f"context.{field} must be a non-empty string.")
    if not _valid_id(context["company_id"]):
        raise _invalid("context.company_id must be a positive integer.")
    parameters = request["parameters"]
    if not isinstance(parameters, dict):
        raise _invalid("parameters must be an object.")
    return request_id, dict(context), parameters


def validate_bank_reconciliation_get_request(
    request: Any,
) -> tuple[str, dict[str, Any], int]:
    request_id, context, parameters = _validate_envelope(request)
    if set(parameters) != {"transaction_id"} or not _valid_id(
        parameters.get("transaction_id")
    ):
        raise _invalid("parameters.transaction_id must be the only positive ID.")
    return request_id, context, parameters["transaction_id"]


def validate_bank_match_candidates_request(
    request: Any,
) -> tuple[str, dict[str, Any], int, int, str | None]:
    request_id, context, parameters = _validate_envelope(request)
    if not set(parameters) <= {"transaction_id", "limit", "cursor"} or not _valid_id(
        parameters.get("transaction_id")
    ):
        raise _invalid("Match-candidate parameters do not match the fixed contract.")
    limit = parameters.get("limit", DEFAULT_LIMIT)
    if not _is_integer(limit) or not 1 <= limit <= MAX_LIMIT:
        raise _invalid(f"parameters.limit must be between 1 and {MAX_LIMIT}.")
    cursor = parameters.get("cursor")
    if cursor is not None and (
        not isinstance(cursor, str) or not cursor or len(cursor) > 4096
    ):
        raise _invalid("parameters.cursor must be null or a non-empty cursor string.")
    return request_id, context, parameters["transaction_id"], limit, cursor


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _cursor_binding(context: dict[str, Any], transaction_id: int) -> str:
    target = {
        "capability": CANDIDATES_CAPABILITY_ID,
        "company_id": context["company_id"],
        "database": context["database"],
        "transaction_id": transaction_id,
        "user_login": context["user_login"],
    }
    return hashlib.sha256(_canonical_json(target).encode("utf-8")).hexdigest()


def _encode_cursor(
    after: list[Any], *, context: dict[str, Any], transaction_id: int
) -> str:
    payload = _canonical_json(
        {
            "after": after,
            "binding": _cursor_binding(context, transaction_id),
            "version": _CURSOR_VERSION,
        }
    ).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate cursor key")
        result[key] = value
    return result


def _reject_json_number(_value: str) -> None:
    raise ValueError("unsupported cursor number")


def _decode_cursor(
    cursor: str, *, context: dict[str, Any], transaction_id: int
) -> list[Any]:
    try:
        padding = "=" * (-len(cursor) % 4)
        raw = base64.b64decode(
            (cursor + padding).encode("ascii"), altchars=b"-_", validate=True
        )
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_pairs,
            parse_float=_reject_json_number,
            parse_constant=_reject_json_number,
        )
    except (ValueError, UnicodeError, json.JSONDecodeError, binascii.Error) as exc:
        raise _invalid("The cursor is invalid.", code="invalid_cursor") from exc
    if (
        not isinstance(value, dict)
        or set(value) != {"after", "binding", "version"}
        or not _is_integer(value["version"])
        or value["version"] != _CURSOR_VERSION
        or value["binding"] != _cursor_binding(context, transaction_id)
        or not isinstance(value["after"], list)
        or len(value["after"]) != 2
        or not _valid_date(value["after"][0])
        or not _valid_id(value["after"][1])
    ):
        raise _invalid("The cursor does not match this request.", code="invalid_cursor")
    return value["after"]


def _validate_gates(
    port: BankReconciliationPort, page: Any, *, result_field: str
) -> Any:
    expected = _GATE_FIELDS | {result_field}
    if (
        not isinstance(page, dict)
        or set(page) != expected
        or not _valid_id(page["user_id"])
        or not isinstance(page["company_visible"], bool)
        or not isinstance(page["module_installed"], bool)
        or not isinstance(page["access_allowed"], bool)
    ):
        raise _failed("Odoo returned an invalid bank-reconciliation result.")
    try:
        user_id = port.user_id
    except ValueError as exc:
        raise _failed("Odoo returned an invalid bank-reconciliation result.") from exc
    if page["user_id"] != user_id:
        raise _failed("Odoo returned a mismatched bank-reconciliation user.")
    if page["access_allowed"] and not (
        page["company_visible"] and page["module_installed"]
    ):
        raise _failed("Odoo returned inconsistent bank-reconciliation gates.")
    if page[result_field] and not (
        page["company_visible"] and page["module_installed"] and page["access_allowed"]
    ):
        raise _failed("Odoo returned data from a denied bank-reconciliation gate.")
    if not page["company_visible"]:
        raise BankReconciliationError(
            "company_unavailable",
            "The requested company is unavailable to the configured user.",
            exit_code=3,
        )
    if not page["module_installed"]:
        raise BankReconciliationError(
            "uninstalled",
            "Bank reconciliation is unavailable in this database.",
            exit_code=4,
        )
    if not page["access_allowed"]:
        raise BankReconciliationError(
            "unauthorized",
            "The configured user cannot read bank reconciliation data.",
            exit_code=3,
        )
    return page[result_field]


def _valid_line(value: Any) -> bool:
    fields = {
        "id",
        "account_id",
        "partner_id",
        "currency_id",
        "balance",
        "amount_currency",
        "amount_residual",
        "amount_residual_currency",
    }
    return (
        isinstance(value, dict)
        and set(value) == fields
        and _valid_id(value["id"])
        and _valid_id(value["account_id"])
        and _valid_optional_id(value["partner_id"])
        and _valid_id(value["currency_id"])
        and all(
            _decimal(value[field]) is not None
            for field in (
                "balance",
                "amount_currency",
                "amount_residual",
                "amount_residual_currency",
            )
        )
    )


def _valid_matched_line(value: Any) -> bool:
    fields = {
        "bank_move_line_id",
        "source_line_id",
        "source_move_id",
        "account_id",
        "partner_id",
        "currency_id",
        "applied_balance",
        "applied_amount_currency",
        "source_amount_residual",
        "source_amount_residual_currency",
        "full_reconcile_id",
    }
    return (
        isinstance(value, dict)
        and set(value) == fields
        and all(
            _valid_id(value[field])
            for field in (
                "bank_move_line_id",
                "source_line_id",
                "source_move_id",
                "account_id",
                "currency_id",
            )
        )
        and _valid_optional_id(value["partner_id"])
        and _valid_optional_id(value["full_reconcile_id"])
        and all(
            _decimal(value[field]) is not None
            for field in (
                "applied_balance",
                "applied_amount_currency",
                "source_amount_residual",
                "source_amount_residual_currency",
            )
        )
    )


def _valid_writeoff_line(value: Any) -> bool:
    fields = {
        "id",
        "name",
        "account_id",
        "partner_id",
        "currency_id",
        "balance",
        "amount_currency",
    }
    return (
        isinstance(value, dict)
        and set(value) == fields
        and _valid_id(value["id"])
        and _valid_text(value["name"])
        and _valid_id(value["account_id"])
        and _valid_optional_id(value["partner_id"])
        and _valid_id(value["currency_id"])
        and _decimal(value["balance"]) is not None
        and _decimal(value["amount_currency"]) is not None
    )


def _validate_reconciliation_result(
    result: Any, *, company_id: int, transaction_id: int
) -> dict[str, Any]:
    fields = {
        "transaction",
        "liquidity_line",
        "suspense_line",
        "matched_lines",
        "writeoff_lines",
        "payment_ids",
    }
    if not isinstance(result, dict) or set(result) != fields:
        raise _failed("Odoo returned a malformed bank-reconciliation result.")
    transaction = result["transaction"]
    transaction_fields = {
        "id",
        "company_id",
        "move_id",
        "move_state",
        "date",
        "journal_id",
        "partner_id",
        "amount",
        "currency_id",
        "foreign_currency_id",
        "amount_currency",
        "amount_residual",
        "is_reconciled",
        "checked",
    }
    if (
        not isinstance(transaction, dict)
        or set(transaction) != transaction_fields
        or transaction["id"] != transaction_id
        or transaction["company_id"] != company_id
        or not _valid_id(transaction["move_id"])
        or transaction["move_state"] not in {"draft", "posted", "cancel"}
        or not _valid_date(transaction["date"])
        or not _valid_id(transaction["journal_id"])
        or not _valid_optional_id(transaction["partner_id"])
        or _decimal(transaction["amount"]) is None
        or not _valid_id(transaction["currency_id"])
        or not _valid_optional_id(transaction["foreign_currency_id"])
        or _decimal(transaction["amount_currency"]) is None
        or _decimal(transaction["amount_residual"]) is None
        or not isinstance(transaction["is_reconciled"], bool)
        or not isinstance(transaction["checked"], bool)
        or not _valid_line(result["liquidity_line"])
        or not (result["suspense_line"] is None or _valid_line(result["suspense_line"]))
        or not isinstance(result["matched_lines"], list)
        or any(not _valid_matched_line(item) for item in result["matched_lines"])
        or not isinstance(result["writeoff_lines"], list)
        or any(not _valid_writeoff_line(item) for item in result["writeoff_lines"])
        or not isinstance(result["payment_ids"], list)
        or any(not _valid_id(item) for item in result["payment_ids"])
        or result["payment_ids"] != sorted(set(result["payment_ids"]))
    ):
        raise _failed("Odoo returned a malformed bank-reconciliation result.")
    return result


def get_bank_transaction_reconciliation(
    port: BankReconciliationPort, request: dict[str, Any]
) -> dict[str, Any]:
    _, context, transaction_id = validate_bank_reconciliation_get_request(request)
    try:
        page = port.get(company_id=context["company_id"], transaction_id=transaction_id)
    except ValueError as exc:
        raise _failed("The Odoo bridge returned an invalid result.") from exc
    result = _validate_gates(port, page, result_field="result")
    if result is None:
        raise BankReconciliationError(
            "record_not_found", "The bank transaction was not found.", exit_code=4
        )
    return _validate_reconciliation_result(
        result, company_id=context["company_id"], transaction_id=transaction_id
    )


def list_bank_match_candidates(
    port: BankReconciliationPort, request: dict[str, Any]
) -> dict[str, Any]:
    _, context, transaction_id, limit, cursor = validate_bank_match_candidates_request(
        request
    )
    after = (
        _decode_cursor(cursor, context=context, transaction_id=transaction_id)
        if cursor
        else None
    )
    fetch_limit = limit + 1
    try:
        page = port.read_candidates_page(
            company_id=context["company_id"],
            transaction_id=transaction_id,
            after=after,
            limit=fetch_limit,
        )
    except ValueError as exc:
        raise _failed("The Odoo bridge returned an invalid candidate page.") from exc
    rows = _validate_gates(port, page, result_field="rows")
    if not isinstance(rows, list) or len(rows) > fetch_limit:
        raise _failed("Odoo returned an invalid candidate page.")
    previous = tuple(after) if after is not None else None
    seen: set[int] = set()
    records: list[dict[str, Any]] = []
    for row in rows:
        if not _valid_candidate_row(row, company_id=context["company_id"]):
            raise _failed("Odoo returned an invalid or out-of-scope candidate.")
        current = (row["date"], row["id"])
        if row["id"] in seen or (previous is not None and current >= previous):
            raise _failed("Odoo returned candidates in an unstable order.")
        seen.add(row["id"])
        previous = current
        records.append(dict(row))
    has_more = len(records) > limit
    items = records[:limit]
    next_cursor = None
    if has_more and items:
        next_cursor = _encode_cursor(
            [items[-1]["date"], items[-1]["id"]],
            context=context,
            transaction_id=transaction_id,
        )
    return {"items": items, "has_more": has_more, "next_cursor": next_cursor}
