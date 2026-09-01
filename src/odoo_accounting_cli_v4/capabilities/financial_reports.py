"""Strict contracts for fixed read-only accounting reports."""

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

TRIAL_BALANCE_CAPABILITY_ID = "report.trial_balance"
BALANCE_SHEET_CAPABILITY_ID = "report.balance_sheet"
PROFIT_AND_LOSS_CAPABILITY_ID = "report.profit_and_loss"
CASH_FLOW_CAPABILITY_ID = "report.cash_flow"
TAX_REPORT_CAPABILITY_ID = "report.tax"
GENERAL_LEDGER_CAPABILITY_ID = "report.general_ledger"
PARTNER_LEDGER_CAPABILITY_ID = "report.partner_ledger"
AGED_RECEIVABLE_CAPABILITY_ID = "report.aged_receivable"
AGED_PAYABLE_CAPABILITY_ID = "report.aged_payable"
JOURNAL_REPORT_CAPABILITY_ID = "report.journal"
EXECUTIVE_SUMMARY_CAPABILITY_ID = "report.executive_summary"
ASSET_REPORT_CAPABILITY_ID = "report.asset"
DEFERRED_EXPENSE_REPORT_CAPABILITY_ID = "report.deferred_expense"
DEFERRED_REVENUE_REPORT_CAPABILITY_ID = "report.deferred_revenue"
MULTICURRENCY_REVALUATION_REPORT_CAPABILITY_ID = "report.multicurrency_revaluation"
CHINA_BALANCE_SHEET_REPORT_CAPABILITY_ID = "report.china.balance_sheet"
CHINA_PROFIT_AND_LOSS_REPORT_CAPABILITY_ID = "report.china.profit_and_loss"
CHINA_CASH_FLOW_REPORT_CAPABILITY_ID = "report.china.cash_flow"
SINGAPORE_GST_REPORT_CAPABILITY_ID = "report.singapore.gst"
BANK_RECONCILIATION_REPORT_CAPABILITY_ID = "report.bank_reconciliation"
CUSTOMER_STATEMENT_REPORT_CAPABILITY_ID = "report.customer_statement"
FOLLOWUP_REPORT_CAPABILITY_ID = "report.followup"
FINANCIAL_REPORT_EXPORTS = {
    "report.trial_balance.export": {"key": "trial_balance", "mode": "range"},
    "report.balance_sheet.export": {"key": "balance_sheet", "mode": "single"},
    "report.profit_and_loss.export": {
        "key": "profit_and_loss",
        "mode": "range",
    },
    "report.cash_flow.export": {"key": "cash_flow", "mode": "range"},
    "report.tax.export": {"key": "tax", "mode": "range"},
    "report.general_ledger.export": {"key": "general_ledger", "mode": "range"},
    "report.partner_ledger.export": {"key": "partner_ledger", "mode": "range"},
    "report.aged_receivable.export": {
        "key": "aged_receivable",
        "mode": "single",
    },
    "report.aged_payable.export": {"key": "aged_payable", "mode": "single"},
    "report.executive_summary.export": {
        "key": "executive_summary",
        "mode": "range",
    },
    "report.journal.export": {"key": "journal", "mode": "range"},
    "report.asset.export": {"key": "asset", "mode": "range"},
    "report.deferred_expense.export": {
        "key": "deferred_expense",
        "mode": "range",
    },
    "report.deferred_revenue.export": {
        "key": "deferred_revenue",
        "mode": "range",
    },
    "report.multicurrency_revaluation.export": {
        "key": "multicurrency_revaluation",
        "mode": "single",
    },
    "report.china.balance_sheet.export": {
        "key": "china_balance_sheet",
        "mode": "single",
    },
    "report.china.profit_and_loss.export": {
        "key": "china_profit_and_loss",
        "mode": "range",
    },
    "report.china.cash_flow.export": {
        "key": "china_cash_flow",
        "mode": "range",
    },
    "report.singapore.gst.export": {
        "key": "singapore_gst",
        "mode": "range",
    },
    "report.customer_statement.export": {
        "key": "customer_statement",
        "mode": "range",
        "requires_partner_id": True,
    },
    "report.followup.export": {
        "key": "followup",
        "mode": "single",
        "requires_partner_id": True,
    },
}
FINANCIAL_REPORT_EXPORT_CAPABILITY_IDS = frozenset(FINANCIAL_REPORT_EXPORTS)
_JOURNAL_FILTER_REPORTS = frozenset(
    {
        TRIAL_BALANCE_CAPABILITY_ID,
        BALANCE_SHEET_CAPABILITY_ID,
        PROFIT_AND_LOSS_CAPABILITY_ID,
        GENERAL_LEDGER_CAPABILITY_ID,
    }
)
DEFAULT_LIMIT = 100
MAX_LIMIT = 1000
_CURSOR_VERSION = 1
_DECIMAL_PATTERN = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
_INTEGER_PATTERN = re.compile(r"^-?(?:0|[1-9][0-9]*)$")
_TYPED_REPORTS = {
    GENERAL_LEDGER_CAPABILITY_ID: {"key": "general_ledger", "mode": "range"},
    PARTNER_LEDGER_CAPABILITY_ID: {"key": "partner_ledger", "mode": "range"},
    AGED_RECEIVABLE_CAPABILITY_ID: {"key": "aged_receivable", "mode": "single"},
    AGED_PAYABLE_CAPABILITY_ID: {"key": "aged_payable", "mode": "single"},
    JOURNAL_REPORT_CAPABILITY_ID: {"key": "journal", "mode": "range"},
    EXECUTIVE_SUMMARY_CAPABILITY_ID: {
        "key": "executive_summary",
        "mode": "range",
    },
    ASSET_REPORT_CAPABILITY_ID: {"key": "asset", "mode": "range"},
    DEFERRED_EXPENSE_REPORT_CAPABILITY_ID: {
        "key": "deferred_expense",
        "mode": "range",
    },
    DEFERRED_REVENUE_REPORT_CAPABILITY_ID: {
        "key": "deferred_revenue",
        "mode": "range",
    },
    MULTICURRENCY_REVALUATION_REPORT_CAPABILITY_ID: {
        "key": "multicurrency_revaluation",
        "mode": "single",
    },
    CHINA_BALANCE_SHEET_REPORT_CAPABILITY_ID: {
        "key": "china_balance_sheet",
        "mode": "single",
    },
    CHINA_PROFIT_AND_LOSS_REPORT_CAPABILITY_ID: {
        "key": "china_profit_and_loss",
        "mode": "range",
    },
    CHINA_CASH_FLOW_REPORT_CAPABILITY_ID: {
        "key": "china_cash_flow",
        "mode": "range",
    },
    SINGAPORE_GST_REPORT_CAPABILITY_ID: {
        "key": "singapore_gst",
        "mode": "range",
    },
    BANK_RECONCILIATION_REPORT_CAPABILITY_ID: {
        "key": "bank_reconciliation",
        "mode": "single",
        "requires_journal_id": True,
    },
    CUSTOMER_STATEMENT_REPORT_CAPABILITY_ID: {
        "key": "customer_statement",
        "mode": "range",
        "requires_partner_id": True,
    },
    FOLLOWUP_REPORT_CAPABILITY_ID: {
        "key": "followup",
        "mode": "single",
        "requires_partner_id": True,
    },
}
_REPORT_FIGURE_TYPES = frozenset(
    {"monetary", "float", "percentage", "integer", "date", "string"}
)


class FinancialReportPort(Protocol):
    @property
    def user_id(self) -> int: ...

    def read_page(
        self,
        *,
        company_id: int,
        date_from: str | None,
        date_to: str,
        after_line_id: str | None,
        limit: int,
        journal_id: int | None = None,
        partner_id: int | None = None,
        journal_ids: list[int] | None = None,
    ) -> dict[str, Any]: ...


class FinancialReportExportPort(Protocol):
    @property
    def user_id(self) -> int: ...

    def export(
        self,
        *,
        capability_id: str,
        company_id: int,
        date_from: str | None,
        date_to: str,
        format: str,
        journal_ids: list[int] | None = None,
        partner_id: int | None = None,
    ) -> dict[str, Any]: ...


class FinancialReportError(RuntimeError):
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


def _invalid(message: str, *, code: str = "invalid_request") -> FinancialReportError:
    return FinancialReportError(code, message, exit_code=2)


def _failed(message: str) -> FinancialReportError:
    return FinancialReportError("failed_validation", message, exit_code=8)


def _is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _valid_id(value: Any) -> bool:
    return _is_integer(value) and value > 0


def _journal_ids(parameters: dict[str, Any]) -> list[int] | None:
    if "journal_ids" not in parameters:
        return None
    value = parameters["journal_ids"]
    if (
        not isinstance(value, list)
        or not 1 <= len(value) <= MAX_LIMIT
        or not all(_valid_id(item) for item in value)
        or len(value) != len(set(value))
    ):
        raise _invalid("journal_ids must contain 1-1000 unique positive integer IDs.")
    return sorted(value)


def _journal_ids_digest(journal_ids: list[int]) -> str:
    payload = json.dumps(journal_ids, separators=(",", ":")).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _canonical_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return False
    return parsed.isoformat() == value


def _decimal_string(value: Any) -> bool:
    if not isinstance(value, str) or _DECIMAL_PATTERN.fullmatch(value) is None:
        return False
    try:
        return Decimal(value).is_finite()
    except InvalidOperation:
        return False


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate cursor key")
        value[key] = item
    return value


def _reject_json_constant(_value: str) -> None:
    raise ValueError("non-finite cursor number")


def _validate_envelope(request: Any) -> tuple[dict[str, Any], dict[str, Any]]:
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
        parsed = uuid.UUID(request_id)
    except (ValueError, AttributeError) as exc:
        raise _invalid("request_id must be a UUID string.") from exc
    if (
        str(parsed) != request_id.lower()
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
    for key in ("database", "user_login", "language", "timezone"):
        if not _nonempty_string(context[key]):
            raise _invalid(f"context.{key} must be a non-empty string.")
    if not _valid_id(context["company_id"]):
        raise _invalid("context.company_id must be a positive integer.")
    parameters = request["parameters"]
    if not isinstance(parameters, dict):
        raise _invalid("parameters must be an object.")
    return context, parameters


def validate_trial_balance_request(
    request: Any,
) -> tuple[dict[str, Any], str, str, int, str | None]:
    context, parameters = _validate_envelope(request)
    if not set(parameters) <= {
        "date_from",
        "date_to",
        "limit",
        "cursor",
        "journal_ids",
    }:
        raise _invalid("report.trial_balance contains an unsupported parameter.")
    _journal_ids(parameters)
    if not {"date_from", "date_to"} <= set(parameters):
        raise _invalid("date_from and date_to are required.")
    date_from = parameters["date_from"]
    date_to = parameters["date_to"]
    if not _canonical_date(date_from) or not _canonical_date(date_to):
        raise _invalid("date_from and date_to must be YYYY-MM-DD dates.")
    if date_from > date_to:
        raise _invalid("date_from cannot be after date_to.")
    limit = parameters.get("limit", DEFAULT_LIMIT)
    if not _is_integer(limit) or not 1 <= limit <= MAX_LIMIT:
        raise _invalid(f"limit must be between 1 and {MAX_LIMIT}.")
    cursor = parameters.get("cursor")
    if cursor is not None and (
        not isinstance(cursor, str) or not cursor or len(cursor) > 4096
    ):
        raise _invalid("cursor must be null or a non-empty cursor string.")
    return context, date_from, date_to, limit, cursor


def validate_balance_sheet_request(
    request: Any,
) -> tuple[dict[str, Any], None, str, int, str | None]:
    context, parameters = _validate_envelope(request)
    if not set(parameters) <= {"as_of", "limit", "cursor", "journal_ids"}:
        raise _invalid("report.balance_sheet contains an unsupported parameter.")
    _journal_ids(parameters)
    if "as_of" not in parameters or not _canonical_date(parameters["as_of"]):
        raise _invalid("as_of must be a YYYY-MM-DD date.")
    limit = parameters.get("limit", DEFAULT_LIMIT)
    if not _is_integer(limit) or not 1 <= limit <= MAX_LIMIT:
        raise _invalid(f"limit must be between 1 and {MAX_LIMIT}.")
    cursor = parameters.get("cursor")
    if cursor is not None and (
        not isinstance(cursor, str) or not cursor or len(cursor) > 4096
    ):
        raise _invalid("cursor must be null or a non-empty cursor string.")
    return context, None, parameters["as_of"], limit, cursor


def validate_profit_and_loss_request(
    request: Any,
) -> tuple[dict[str, Any], str, str, int, str | None]:
    context, parameters = _validate_envelope(request)
    if not set(parameters) <= {
        "date_from",
        "date_to",
        "limit",
        "cursor",
        "journal_ids",
    }:
        raise _invalid("report.profit_and_loss contains an unsupported parameter.")
    _journal_ids(parameters)
    if not {"date_from", "date_to"} <= set(parameters):
        raise _invalid("date_from and date_to are required.")
    date_from = parameters["date_from"]
    date_to = parameters["date_to"]
    if not _canonical_date(date_from) or not _canonical_date(date_to):
        raise _invalid("date_from and date_to must be YYYY-MM-DD dates.")
    if date_from > date_to:
        raise _invalid("date_from cannot be after date_to.")
    limit = parameters.get("limit", DEFAULT_LIMIT)
    if not _is_integer(limit) or not 1 <= limit <= MAX_LIMIT:
        raise _invalid(f"limit must be between 1 and {MAX_LIMIT}.")
    cursor = parameters.get("cursor")
    if cursor is not None and (
        not isinstance(cursor, str) or not cursor or len(cursor) > 4096
    ):
        raise _invalid("cursor must be null or a non-empty cursor string.")
    return context, date_from, date_to, limit, cursor


def validate_cash_flow_request(
    request: Any,
) -> tuple[dict[str, Any], str, str, int, str | None]:
    context, parameters = _validate_envelope(request)
    if not set(parameters) <= {"date_from", "date_to", "limit", "cursor"}:
        raise _invalid("report.cash_flow contains an unsupported parameter.")
    if not {"date_from", "date_to"} <= set(parameters):
        raise _invalid("date_from and date_to are required.")
    date_from = parameters["date_from"]
    date_to = parameters["date_to"]
    if not _canonical_date(date_from) or not _canonical_date(date_to):
        raise _invalid("date_from and date_to must be YYYY-MM-DD dates.")
    if date_from > date_to:
        raise _invalid("date_from cannot be after date_to.")
    limit = parameters.get("limit", DEFAULT_LIMIT)
    if not _is_integer(limit) or not 1 <= limit <= MAX_LIMIT:
        raise _invalid(f"limit must be between 1 and {MAX_LIMIT}.")
    cursor = parameters.get("cursor")
    if cursor is not None and (
        not isinstance(cursor, str) or not cursor or len(cursor) > 4096
    ):
        raise _invalid("cursor must be null or a non-empty cursor string.")
    return context, date_from, date_to, limit, cursor


def validate_tax_report_request(
    request: Any,
) -> tuple[dict[str, Any], str, str, int, str | None]:
    context, parameters = _validate_envelope(request)
    if not set(parameters) <= {"date_from", "date_to", "limit", "cursor"}:
        raise _invalid("report.tax contains an unsupported parameter.")
    if not {"date_from", "date_to"} <= set(parameters):
        raise _invalid("date_from and date_to are required.")
    date_from = parameters["date_from"]
    date_to = parameters["date_to"]
    if not _canonical_date(date_from) or not _canonical_date(date_to):
        raise _invalid("date_from and date_to must be YYYY-MM-DD dates.")
    if date_from > date_to:
        raise _invalid("date_from cannot be after date_to.")
    limit = parameters.get("limit", DEFAULT_LIMIT)
    if not _is_integer(limit) or not 1 <= limit <= MAX_LIMIT:
        raise _invalid(f"limit must be between 1 and {MAX_LIMIT}.")
    cursor = parameters.get("cursor")
    if cursor is not None and (
        not isinstance(cursor, str) or not cursor or len(cursor) > 4096
    ):
        raise _invalid("cursor must be null or a non-empty cursor string.")
    return context, date_from, date_to, limit, cursor


def validate_typed_financial_report_request(
    capability_id: str, request: Any
) -> tuple[dict[str, Any], str | None, str, int, str | None]:
    """Validate one of the additional fixed Odoo accounting reports."""

    try:
        spec = _TYPED_REPORTS[capability_id]
    except (KeyError, TypeError) as exc:
        raise _invalid("The financial-report capability is unsupported.") from exc
    context, parameters = _validate_envelope(request)
    date_key = "as_of" if spec["mode"] == "single" else "date_to"
    allowed = {date_key, "limit", "cursor"}
    if spec["mode"] == "range":
        allowed.add("date_from")
    if spec.get("requires_journal_id"):
        allowed.add("journal_id")
    if spec.get("requires_partner_id"):
        allowed.add("partner_id")
    if capability_id in _JOURNAL_FILTER_REPORTS:
        allowed.add("journal_ids")
    if not set(parameters) <= allowed:
        raise _invalid(f"{capability_id} contains an unsupported parameter.")
    _journal_ids(parameters)
    if spec["mode"] == "single":
        if "as_of" not in parameters or not _canonical_date(parameters["as_of"]):
            raise _invalid("as_of must be a YYYY-MM-DD date.")
        date_from = None
        date_to = parameters["as_of"]
    else:
        if not {"date_from", "date_to"} <= set(parameters):
            raise _invalid("date_from and date_to are required.")
        date_from = parameters["date_from"]
        date_to = parameters["date_to"]
        if not _canonical_date(date_from) or not _canonical_date(date_to):
            raise _invalid("date_from and date_to must be YYYY-MM-DD dates.")
        if date_from > date_to:
            raise _invalid("date_from cannot be after date_to.")
    if spec.get("requires_journal_id") and not _valid_id(parameters.get("journal_id")):
        raise _invalid("journal_id must be a positive integer.")
    if spec.get("requires_partner_id") and not _valid_id(parameters.get("partner_id")):
        raise _invalid("partner_id must be a positive integer.")
    limit = parameters.get("limit", DEFAULT_LIMIT)
    if not _is_integer(limit) or not 1 <= limit <= MAX_LIMIT:
        raise _invalid(f"limit must be between 1 and {MAX_LIMIT}.")
    cursor = parameters.get("cursor")
    if cursor is not None and (
        not isinstance(cursor, str) or not cursor or len(cursor) > 4096
    ):
        raise _invalid("cursor must be null or a non-empty cursor string.")
    return context, date_from, date_to, limit, cursor


def validate_financial_report_export_request(
    capability_id: str, request: Any
) -> tuple[dict[str, Any], str | None, str, str]:
    """Validate one fixed PDF or XLSX financial-report export request."""

    try:
        spec = FINANCIAL_REPORT_EXPORTS[capability_id]
    except (KeyError, TypeError) as exc:
        raise _invalid("The financial-report export capability is unsupported.") from exc
    context, parameters = _validate_envelope(request)
    optional = (
        {"journal_ids"}
        if capability_id.removesuffix(".export") in _JOURNAL_FILTER_REPORTS
        else set()
    )
    required_partner = (
        {"partner_id"} if spec.get("requires_partner_id") is True else set()
    )
    if spec["mode"] == "single":
        required = {"as_of", "format"} | required_partner
        if not required <= set(parameters) <= required | optional:
            if required_partner:
                raise _invalid(f"{capability_id} contains invalid export parameters.")
            raise _invalid(f"{capability_id} requires only as_of and format.")
        if not _canonical_date(parameters["as_of"]):
            raise _invalid("as_of must be a YYYY-MM-DD date.")
        date_from = None
        date_to = parameters["as_of"]
    else:
        required = {"date_from", "date_to", "format"} | required_partner
        if not required <= set(parameters) <= required | optional:
            if required_partner:
                raise _invalid(f"{capability_id} contains invalid export parameters.")
            raise _invalid(
                f"{capability_id} requires only date_from, date_to, and format."
            )
        date_from = parameters["date_from"]
        date_to = parameters["date_to"]
        if not _canonical_date(date_from) or not _canonical_date(date_to):
            raise _invalid("date_from and date_to must be YYYY-MM-DD dates.")
        if date_from > date_to:
            raise _invalid("date_from cannot be after date_to.")
    export_format = parameters["format"]
    if not isinstance(export_format, str) or export_format not in {"pdf", "xlsx"}:
        raise _invalid("format must be 'pdf' or 'xlsx'.")
    if required_partner and not _valid_id(parameters["partner_id"]):
        raise _invalid("partner_id must be a positive integer.")
    _journal_ids(parameters)
    return context, date_from, date_to, export_format


def validate_bank_reconciliation_request(
    request: Any,
) -> tuple[dict[str, Any], None, str, int, int, str | None]:
    """Validate one journal-scoped bank reconciliation report request."""

    context, date_from, date_to, limit, cursor = (
        validate_typed_financial_report_request(
            BANK_RECONCILIATION_REPORT_CAPABILITY_ID, request
        )
    )
    return (
        context,
        date_from,
        date_to,
        request["parameters"]["journal_id"],
        limit,
        cursor,
    )


def _encode_cursor(
    line_id: str,
    *,
    capability_id: str,
    context: dict[str, Any],
    date_from: str | None,
    date_to: str,
    journal_id: int | None = None,
    partner_id: int | None = None,
    journal_ids: list[int] | None = None,
) -> str:
    cursor_payload = {
        "after_line_id": line_id,
        "capability": capability_id,
        "company_id": context["company_id"],
        "database": context["database"],
        "date_from": date_from,
        "date_to": date_to,
        "user_login": context["user_login"],
        "version": _CURSOR_VERSION,
    }
    if journal_id is not None:
        cursor_payload["journal_id"] = journal_id
    if partner_id is not None:
        cursor_payload["partner_id"] = partner_id
    if journal_ids is not None:
        cursor_payload["journal_ids_sha256"] = _journal_ids_digest(journal_ids)
    payload = json.dumps(
        cursor_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def _decode_cursor(
    cursor: str,
    *,
    capability_id: str,
    context: dict[str, Any],
    date_from: str | None,
    date_to: str,
    journal_id: int | None = None,
    partner_id: int | None = None,
    journal_ids: list[int] | None = None,
) -> str:
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
    expected_fields = {
        "after_line_id",
        "capability",
        "company_id",
        "database",
        "date_from",
        "date_to",
        "user_login",
        "version",
    }
    if journal_id is not None:
        expected_fields.add("journal_id")
    if partner_id is not None:
        expected_fields.add("partner_id")
    if journal_ids is not None:
        expected_fields.add("journal_ids_sha256")
    if (
        not isinstance(value, dict)
        or set(value) != expected_fields
        or value["capability"] != capability_id
        or value["version"] != _CURSOR_VERSION
        or not _is_integer(value["version"])
        or value["company_id"] != context["company_id"]
        or value["database"] != context["database"]
        or value["user_login"] != context["user_login"]
        or value["date_from"] != date_from
        or value["date_to"] != date_to
        or (
            journal_ids is not None
            and value["journal_ids_sha256"] != _journal_ids_digest(journal_ids)
        )
        or (
            journal_id is not None
            and (
                not _valid_id(value["journal_id"]) or value["journal_id"] != journal_id
            )
        )
        or (
            partner_id is not None
            and (
                not _valid_id(value["partner_id"]) or value["partner_id"] != partner_id
            )
        )
        or not _nonempty_string(value["after_line_id"])
    ):
        raise _invalid("The cursor does not match this request.", code="invalid_cursor")
    return value["after_line_id"]


def _validate_columns(value: Any, *, typed_values: bool) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise _failed("Odoo returned invalid trial-balance columns.")
    result: list[dict[str, Any]] = []
    for index, column in enumerate(value):
        expected_keys = {"index", "label", "expression_label"}
        if typed_values:
            expected_keys.add("figure_type")
        if (
            not isinstance(column, dict)
            or set(column) != expected_keys
            or column["index"] != index
            or not _nonempty_string(column["label"])
            or not _nonempty_string(column["expression_label"])
            or (typed_values and column["figure_type"] not in _REPORT_FIGURE_TYPES)
        ):
            raise _failed("Odoo returned invalid trial-balance columns.")
        result.append(dict(column))
    return result


def _valid_typed_value(value: Any, figure_type: str) -> bool:
    if value is None:
        return True
    if figure_type in {"monetary", "float", "percentage"}:
        return _decimal_string(value)
    if figure_type == "integer":
        return isinstance(value, str) and _INTEGER_PATTERN.fullmatch(value) is not None
    if figure_type == "date":
        return _canonical_date(value)
    return figure_type == "string" and isinstance(value, str)


def _validate_lines(
    value: Any,
    *,
    columns: list[dict[str, Any]],
    maximum: int,
    typed_values: bool,
) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) > maximum:
        raise _failed("Odoo returned an invalid trial-balance page.")
    line_ids: set[str] = set()
    result: list[dict[str, Any]] = []
    for line in value:
        if (
            not isinstance(line, dict)
            or set(line) != {"id", "parent_id", "name", "level", "unfoldable", "values"}
            or not _nonempty_string(line["id"])
            or line["id"] in line_ids
            or not (line["parent_id"] is None or _nonempty_string(line["parent_id"]))
            or not _nonempty_string(line["name"])
            or not _is_integer(line["level"])
            or line["level"] < 0
            or not isinstance(line["unfoldable"], bool)
            or not isinstance(line["values"], list)
            or len(line["values"]) != len(columns)
            or (
                typed_values
                and any(
                    not _valid_typed_value(item, columns[index]["figure_type"])
                    for index, item in enumerate(line["values"])
                )
            )
            or (
                not typed_values
                and any(
                    item is not None and not _decimal_string(item)
                    for item in line["values"]
                )
            )
        ):
            raise _failed("Odoo returned an invalid trial-balance line.")
        line_ids.add(line["id"])
        result.append(dict(line))
    return result


def _validated_page(
    port: FinancialReportPort,
    page: Any,
    *,
    report_key: str,
    date_from: str | None,
    date_to: str,
    maximum: int,
    typed_values: bool,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    expected = {
        "user_id",
        "company_visible",
        "module_installed",
        "access_allowed",
        "cursor_found",
        "report",
        "date",
        "currency",
        "basis",
        "columns",
        "lines",
    }
    if (
        not isinstance(page, dict)
        or set(page) != expected
        or not _valid_id(page["user_id"])
        or not _valid_id(port.user_id)
        or page["user_id"] != port.user_id
        or not all(
            isinstance(page[key], bool)
            for key in (
                "company_visible",
                "module_installed",
                "access_allowed",
                "cursor_found",
            )
        )
        or (
            page["access_allowed"]
            and not (page["company_visible"] and page["module_installed"])
        )
        or (not page["access_allowed"] and (page["columns"] or page["lines"]))
    ):
        raise _failed("Odoo returned an invalid trial-balance page.")
    if not page["company_visible"]:
        raise FinancialReportError(
            "company_unavailable",
            "The requested company is unavailable to the configured user.",
            exit_code=3,
        )
    if not page["module_installed"]:
        raise FinancialReportError(
            "uninstalled", "The trial-balance report is not installed.", exit_code=4
        )
    if not page["access_allowed"]:
        raise FinancialReportError(
            "unauthorized", "The configured user cannot read this report.", exit_code=3
        )
    if not page["cursor_found"]:
        raise _invalid("The cursor is no longer present.", code="invalid_cursor")
    report = page["report"]
    report_date = page["date"]
    currency = page["currency"]
    if (
        not isinstance(report, dict)
        or set(report) != {"key", "name"}
        or report["key"] != report_key
        or not _nonempty_string(report["name"])
        or not isinstance(report_date, dict)
        or set(report_date) != {"from", "to"}
        or not _canonical_date(report_date["from"])
        or report_date["to"] != date_to
        or report_date["from"] > report_date["to"]
        or (date_from is not None and report_date["from"] != date_from)
        or not isinstance(currency, dict)
        or set(currency) != {"id", "code", "decimal_places"}
        or not _valid_id(currency["id"])
        or not _nonempty_string(currency["code"])
        or len(currency["code"]) > 3
        or not _is_integer(currency["decimal_places"])
        or currency["decimal_places"] < 0
        or page["basis"] != "posted_entries"
    ):
        raise _failed("Odoo returned invalid trial-balance metadata.")
    columns = _validate_columns(page["columns"], typed_values=typed_values)
    lines = _validate_lines(
        page["lines"],
        columns=columns,
        maximum=maximum,
        typed_values=typed_values,
    )
    return (
        {
            "report": report,
            "date": report_date,
            "currency": currency,
            "basis": page["basis"],
        },
        columns,
        lines,
    )


def _read_financial_report(
    port: FinancialReportPort,
    *,
    capability_id: str,
    report_key: str,
    context: dict[str, Any],
    date_from: str | None,
    date_to: str,
    limit: int,
    cursor: str | None,
    typed_values: bool = False,
    journal_id: int | None = None,
    partner_id: int | None = None,
    journal_ids: list[int] | None = None,
) -> dict[str, Any]:
    after_line_id = (
        _decode_cursor(
            cursor,
            capability_id=capability_id,
            context=context,
            date_from=date_from,
            date_to=date_to,
            journal_id=journal_id,
            partner_id=partner_id,
            journal_ids=journal_ids,
        )
        if cursor
        else None
    )
    fetch_limit = limit + 1
    read_parameters: dict[str, Any] = {
        "company_id": context["company_id"],
        "date_from": date_from,
        "date_to": date_to,
        "after_line_id": after_line_id,
        "limit": fetch_limit,
    }
    if journal_id is not None:
        read_parameters["journal_id"] = journal_id
    if partner_id is not None:
        read_parameters["partner_id"] = partner_id
    if journal_ids is not None:
        read_parameters["journal_ids"] = journal_ids
    page = port.read_page(**read_parameters)
    metadata, columns, lines = _validated_page(
        port,
        page,
        report_key=report_key,
        date_from=date_from,
        date_to=date_to,
        maximum=fetch_limit,
        typed_values=typed_values,
    )
    has_more = len(lines) > limit
    visible = lines[:limit]
    next_cursor = None
    if has_more and visible:
        next_cursor = _encode_cursor(
            visible[-1]["id"],
            capability_id=capability_id,
            context=context,
            date_from=date_from,
            date_to=date_to,
            journal_id=journal_id,
            partner_id=partner_id,
            journal_ids=journal_ids,
        )
    return {
        **metadata,
        "columns": columns,
        "lines": visible,
        "has_more": has_more,
        "next_cursor": next_cursor,
    }


def read_trial_balance(
    port: FinancialReportPort, request: dict[str, Any]
) -> dict[str, Any]:
    """Read one verified page from the fixed Odoo trial-balance report."""

    context, date_from, date_to, limit, cursor = validate_trial_balance_request(request)
    return _read_financial_report(
        port,
        capability_id=TRIAL_BALANCE_CAPABILITY_ID,
        report_key="trial_balance",
        context=context,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        cursor=cursor,
        journal_ids=_journal_ids(request["parameters"]),
    )


def read_balance_sheet(
    port: FinancialReportPort, request: dict[str, Any]
) -> dict[str, Any]:
    """Read one verified page from the fixed Odoo balance-sheet report."""

    context, date_from, date_to, limit, cursor = validate_balance_sheet_request(request)
    return _read_financial_report(
        port,
        capability_id=BALANCE_SHEET_CAPABILITY_ID,
        report_key="balance_sheet",
        context=context,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        cursor=cursor,
        journal_ids=_journal_ids(request["parameters"]),
    )


def read_profit_and_loss(
    port: FinancialReportPort, request: dict[str, Any]
) -> dict[str, Any]:
    """Read one verified page from the fixed Odoo profit-and-loss report."""

    context, date_from, date_to, limit, cursor = validate_profit_and_loss_request(
        request
    )
    return _read_financial_report(
        port,
        capability_id=PROFIT_AND_LOSS_CAPABILITY_ID,
        report_key="profit_and_loss",
        context=context,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        cursor=cursor,
        journal_ids=_journal_ids(request["parameters"]),
    )


def read_cash_flow(
    port: FinancialReportPort, request: dict[str, Any]
) -> dict[str, Any]:
    """Read one verified page from the fixed Odoo cash-flow report."""

    context, date_from, date_to, limit, cursor = validate_cash_flow_request(request)
    return _read_financial_report(
        port,
        capability_id=CASH_FLOW_CAPABILITY_ID,
        report_key="cash_flow",
        context=context,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        cursor=cursor,
    )


def read_tax_report(
    port: FinancialReportPort, request: dict[str, Any]
) -> dict[str, Any]:
    """Read one verified page from the configured Odoo tax report."""

    context, date_from, date_to, limit, cursor = validate_tax_report_request(request)
    return _read_financial_report(
        port,
        capability_id=TAX_REPORT_CAPABILITY_ID,
        report_key="tax",
        context=context,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        cursor=cursor,
    )


def read_typed_financial_report(
    capability_id: str,
    port: FinancialReportPort,
    request: dict[str, Any],
) -> dict[str, Any]:
    """Read one page from an Odoo report that contains typed columns."""

    if capability_id == BANK_RECONCILIATION_REPORT_CAPABILITY_ID:
        return read_bank_reconciliation(port, request)

    context, date_from, date_to, limit, cursor = (
        validate_typed_financial_report_request(capability_id, request)
    )
    spec = _TYPED_REPORTS[capability_id]
    partner_id = (
        request["parameters"]["partner_id"]
        if spec.get("requires_partner_id")
        else None
    )
    return _read_financial_report(
        port,
        capability_id=capability_id,
        report_key=spec["key"],
        context=context,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        cursor=cursor,
        typed_values=True,
        partner_id=partner_id,
        journal_ids=_journal_ids(request["parameters"]),
    )


def read_bank_reconciliation(
    port: FinancialReportPort, request: dict[str, Any]
) -> dict[str, Any]:
    """Read one verified journal-scoped bank reconciliation report page."""

    context, date_from, date_to, journal_id, limit, cursor = (
        validate_bank_reconciliation_request(request)
    )
    return _read_financial_report(
        port,
        capability_id=BANK_RECONCILIATION_REPORT_CAPABILITY_ID,
        report_key="bank_reconciliation",
        context=context,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        cursor=cursor,
        typed_values=True,
        journal_id=journal_id,
    )


def export_financial_report(
    capability_id: str,
    port: FinancialReportExportPort,
    request: dict[str, Any],
) -> dict[str, Any]:
    """Export one fixed Odoo financial report and verify its binary content."""

    context, date_from, date_to, export_format = (
        validate_financial_report_export_request(capability_id, request)
    )
    export_parameters = {
        "capability_id": capability_id,
        "company_id": context["company_id"],
        "date_from": date_from,
        "date_to": date_to,
        "format": export_format,
    }
    journal_ids = _journal_ids(request["parameters"])
    if journal_ids is not None:
        export_parameters["journal_ids"] = journal_ids
    if FINANCIAL_REPORT_EXPORTS[capability_id].get("requires_partner_id") is True:
        export_parameters["partner_id"] = request["parameters"]["partner_id"]
    page = port.export(**export_parameters)
    expected = {
        "user_id",
        "company_visible",
        "module_installed",
        "access_allowed",
        "filename",
        "format",
        "mimetype",
        "byte_count",
        "sha256",
        "content_base64",
    }
    nullable_strings = ("filename", "mimetype", "sha256", "content_base64")
    if (
        not isinstance(page, dict)
        or set(page) != expected
        or not _valid_id(page["user_id"])
        or not _valid_id(port.user_id)
        or page["user_id"] != port.user_id
        or not all(
            isinstance(page[key], bool)
            for key in ("company_visible", "module_installed", "access_allowed")
        )
        or (
            page["access_allowed"]
            and not (page["company_visible"] and page["module_installed"])
        )
        or not isinstance(page["format"], str)
        or page["format"] not in {"pdf", "xlsx"}
        or page["format"] != export_format
        or not _is_integer(page["byte_count"])
        or page["byte_count"] < 0
        or any(
            page[key] is not None and not isinstance(page[key], str)
            for key in nullable_strings
        )
        or (
            not page["access_allowed"]
            and (
                any(page[key] is not None for key in nullable_strings)
                or page["byte_count"] != 0
            )
        )
    ):
        raise _failed("Odoo returned an invalid financial-report export.")
    if not page["company_visible"]:
        raise FinancialReportError(
            "company_unavailable",
            "The requested company is unavailable to the configured user.",
            exit_code=3,
        )
    if not page["module_installed"]:
        raise FinancialReportError(
            "uninstalled",
            "The requested financial report is not installed.",
            exit_code=4,
        )
    if not page["access_allowed"]:
        raise FinancialReportError(
            "unauthorized",
            "The configured user cannot export this report.",
            exit_code=3,
        )

    filename = page["filename"]
    mimetype = page["mimetype"]
    sha256 = page["sha256"]
    content_base64 = page["content_base64"]
    suffix = f".{export_format}"
    expected_mimetype = {
        "pdf": "application/pdf",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }[export_format]
    if (
        not _nonempty_string(filename)
        or not filename.lower().endswith(suffix)
        or mimetype != expected_mimetype
        or not isinstance(sha256, str)
        or re.fullmatch(r"[0-9a-f]{64}", sha256) is None
        or not isinstance(content_base64, str)
        or not content_base64
    ):
        raise _failed("Odoo returned invalid financial-report export metadata.")
    try:
        content = base64.b64decode(content_base64.encode("ascii"), validate=True)
    except (UnicodeEncodeError, ValueError, binascii.Error) as exc:
        raise _failed("Odoo returned invalid financial-report export content.") from exc
    magic = b"%PDF-" if export_format == "pdf" else b"PK\x03\x04"
    if (
        base64.b64encode(content).decode("ascii") != content_base64
        or len(content) != page["byte_count"]
        or hashlib.sha256(content).hexdigest() != sha256
        or not content.startswith(magic)
    ):
        raise _failed("Odoo returned invalid financial-report export content.")
    return {
        "filename": filename,
        "format": export_format,
        "mimetype": mimetype,
        "byte_count": page["byte_count"],
        "sha256": sha256,
        "content_base64": content_base64,
    }
