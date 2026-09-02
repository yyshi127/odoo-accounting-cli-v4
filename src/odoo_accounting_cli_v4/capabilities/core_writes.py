"""Closed contracts for the fixed batches of core accounting writes."""

from __future__ import annotations

import calendar
import hashlib
import json
import re
import uuid
from copy import deepcopy
from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from time import strftime, strptime
from typing import Any, Protocol

CORE_WRITE_CAPABILITY_IDS = frozenset(
    {
        "customer_invoice.create",
        "vendor_bill.create",
        "invoice.post",
        "journal_entry.create",
        "journal_entry.post",
        "journal_entry.reverse",
        "receivable.payment.register",
        "payable.payment.register",
        "reconciliation.apply",
        "payment.cancel",
        "customer_credit_note.create",
        "vendor_refund.create",
        "payment.post",
        "reconciliation.undo",
        "bank.transaction.record",
        "asset.create",
        "asset.validate",
        "asset.cancel",
        "asset.dispose",
        "asset.pause",
        "deferred_expense.generate_entries",
        "deferred_revenue.generate_entries",
        "multicurrency.revaluation.generate_entries",
        "reconciliation.automatic.run",
        "period.transfer.run",
        "localization.china.period_transfer.run",
        "invoice.update",
        "invoice.lines.replace",
        "invoice.cancel",
        "invoice.reset_to_draft",
        "invoice.duplicate",
        "invoice.type.switch",
        "journal_entry.update",
        "journal_entry.lines.replace",
        "journal_entry.cancel",
        "journal_entry.reset_to_draft",
        "payment.create",
        "payment.update_draft",
        "payment.reset_to_draft",
        "bank.transaction.update",
        "bank.transaction.match",
        "bank.transaction.unmatch",
        "reconciliation.write_off",
        "analytic.plan.create",
        "analytic.plan.update",
        "analytic.account.create",
        "analytic.account.update",
        "analytic.account.archive",
        "analytic.account.restore",
        "analytic.line.create",
        "analytic.line.update",
        "analytic.line.delete",
        "budget.create",
        "budget.update_draft",
        "budget.lines.replace",
        "budget.confirm",
        "budget.reset_to_draft",
        "budget.cancel",
        "budget.mark_done",
        "partner.create",
        "partner.update",
        "partner.archive",
        "partner.restore",
        "partner.accounting.update",
        "partner.bank_account.create",
        "partner.bank_account.update",
        "partner.bank_account.archive",
        "partner.bank_account.restore",
        "account.account.create",
        "account.account.update",
        "account.account.archive",
        "account.account.restore",
        "journal.create",
        "journal.update",
        "journal.archive",
        "journal.restore",
        "tax.create",
        "tax.update",
        "tax.archive",
        "tax.restore",
        "sale.order.create",
        "sale.order.update_draft",
        "sale.order.lines.replace",
        "sale.order.confirm",
        "sale.order.cancel",
        "sale.order.reset_to_draft",
        "purchase.order.create",
        "purchase.order.update_draft",
        "purchase.order.lines.replace",
        "purchase.order.confirm",
        "purchase.order.cancel",
        "purchase.order.reset_to_draft",
        "purchase.order.bill.create",
        "purchase_bill.match",
        "purchase_bill.lines.unmatch",
        "payment_term.create",
        "payment_term.update",
        "payment_term.lines.replace",
        "payment_term.archive",
        "payment_term.restore",
        "period.accrual.generate",
        "fiscal_position.create",
        "fiscal_position.update",
        "fiscal_position.account_mappings.replace",
        "fiscal_position.archive",
        "fiscal_position.restore",
        "journal.group.create",
        "journal.group.update",
        "currency.rate.record",
        "account.group.create",
        "account.group.update",
        "tax.repartition_lines.replace",
        "reconciliation.model.create",
        "reconciliation.model.update",
        "reconciliation.model.lines.replace",
        "reconciliation.model.archive",
        "reconciliation.model.restore",
        "account.tag.create",
        "account.tag.update",
        "account.tag.archive",
        "account.tag.restore",
        "tax.group.create",
        "tax.group.update",
        "cash_rounding.create",
        "cash_rounding.update",
        "fiscal_year.create",
        "fiscal_year.update",
        "analytic.applicability.create",
        "analytic.applicability.update",
        "analytic.distribution_model.create",
        "analytic.distribution_model.update",
        "sale.order.invoice.create",
        "stock.transfer.create",
        "stock.transfer.confirm",
        "stock.transfer.assign",
        "stock.transfer.quantities.set",
        "stock.transfer.validate",
        "stock.transfer.unreserve",
        "stock.transfer.cancel",
        "account.return.create",
        "account.return.checks.refresh",
        "account.return.check.result.update",
        "account.return.validate",
        "account.return.mark_submitted",
        "account.return.archive",
        "account.return.restore",
        "account.return.delete",
    }
)

_CREATE_CAPABILITIES = frozenset(
    {
        "customer_invoice.create",
        "vendor_bill.create",
        "journal_entry.create",
        "bank.transaction.record",
        "asset.create",
        "payment.create",
        "analytic.plan.create",
        "analytic.account.create",
        "analytic.line.create",
        "budget.create",
        "sale.order.create",
        "purchase.order.create",
        "purchase.order.bill.create",
        "payment_term.create",
        "period.accrual.generate",
        "fiscal_position.create",
        "journal.group.create",
        "stock.transfer.create",
    }
)
_INVOICE_CREATE_CAPABILITIES = frozenset(
    {"customer_invoice.create", "vendor_bill.create"}
)
_PAYMENT_REGISTER_CAPABILITIES = frozenset(
    {"receivable.payment.register", "payable.payment.register"}
)
_REFUND_CAPABILITIES = frozenset(
    {"customer_credit_note.create", "vendor_refund.create"}
)
_RECONCILIATION_CAPABILITIES = frozenset(
    {"reconciliation.apply", "reconciliation.undo"}
)
_ASSET_LIFECYCLE_CAPABILITIES = frozenset(
    {"asset.cancel", "asset.dispose", "asset.pause"}
)
_DEFERRED_GENERATION_CAPABILITIES = frozenset(
    {"deferred_expense.generate_entries", "deferred_revenue.generate_entries"}
)
_MOVE_PAIR_CAPABILITIES = frozenset(
    {
        "deferred_expense.generate_entries",
        "deferred_revenue.generate_entries",
        "multicurrency.revaluation.generate_entries",
    }
)
_TRANSFER_CAPABILITIES = frozenset(
    {"period.transfer.run", "localization.china.period_transfer.run"}
)
_INVOICE_LIFECYCLE_CAPABILITIES = frozenset(
    {
        "invoice.update",
        "invoice.lines.replace",
        "invoice.cancel",
        "invoice.reset_to_draft",
    }
)
_JOURNAL_ENTRY_LIFECYCLE_CAPABILITIES = frozenset(
    {
        "journal_entry.update",
        "journal_entry.lines.replace",
        "journal_entry.cancel",
        "journal_entry.reset_to_draft",
    }
)
_DOCUMENT_LIFECYCLE_CAPABILITIES = (
    _INVOICE_LIFECYCLE_CAPABILITIES | _JOURNAL_ENTRY_LIFECYCLE_CAPABILITIES
)
_MOVE_BATCH_LIFECYCLE_CAPABILITIES = frozenset(
    {
        "invoice.post",
        "invoice.cancel",
        "invoice.reset_to_draft",
        "journal_entry.post",
        "journal_entry.cancel",
        "journal_entry.reset_to_draft",
    }
)
_PAYMENT_BATCH_LIFECYCLE_CAPABILITIES = frozenset(
    {"payment.post", "payment.cancel", "payment.reset_to_draft"}
)
_BATCH_LIFECYCLE_CAPABILITIES = (
    _MOVE_BATCH_LIFECYCLE_CAPABILITIES | _PAYMENT_BATCH_LIFECYCLE_CAPABILITIES
)
_DOCUMENT_CONTENT_CAPABILITIES = frozenset(
    {
        "invoice.update",
        "invoice.lines.replace",
        "journal_entry.update",
        "journal_entry.lines.replace",
    }
)
_ORDER_CREATE_CAPABILITIES = frozenset({"sale.order.create", "purchase.order.create"})
_ORDER_UPDATE_CAPABILITIES = frozenset(
    {"sale.order.update_draft", "purchase.order.update_draft"}
)
_ORDER_LINE_REPLACEMENT_CAPABILITIES = frozenset(
    {"sale.order.lines.replace", "purchase.order.lines.replace"}
)
_ORDER_TRANSITION_CAPABILITIES = frozenset(
    {
        "sale.order.confirm",
        "sale.order.cancel",
        "sale.order.reset_to_draft",
        "purchase.order.confirm",
        "purchase.order.cancel",
        "purchase.order.reset_to_draft",
    }
)
_ORDER_WRITE_CAPABILITIES = (
    _ORDER_CREATE_CAPABILITIES
    | _ORDER_UPDATE_CAPABILITIES
    | _ORDER_LINE_REPLACEMENT_CAPABILITIES
    | _ORDER_TRANSITION_CAPABILITIES
)
_SALE_ORDER_INVOICE_CAPABILITIES = frozenset({"sale.order.invoice.create"})
_STOCK_TRANSFER_CREATE_CAPABILITIES = frozenset({"stock.transfer.create"})
_STOCK_TRANSFER_ACTION_CAPABILITIES = frozenset(
    {
        "stock.transfer.confirm",
        "stock.transfer.assign",
        "stock.transfer.unreserve",
        "stock.transfer.cancel",
    }
)
_STOCK_TRANSFER_WRITE_CAPABILITIES = (
    _STOCK_TRANSFER_CREATE_CAPABILITIES
    | _STOCK_TRANSFER_ACTION_CAPABILITIES
    | {"stock.transfer.quantities.set", "stock.transfer.validate"}
)
_PAYMENT_DRAFT_CAPABILITIES = frozenset(
    {"payment.create", "payment.update_draft", "payment.reset_to_draft"}
)
_BANK_RECONCILIATION_WRITE_CAPABILITIES = frozenset(
    {
        "bank.transaction.update",
        "bank.transaction.match",
        "bank.transaction.unmatch",
        "reconciliation.write_off",
    }
)
_ANALYTIC_PLAN_WRITE_CAPABILITIES = frozenset(
    {"analytic.plan.create", "analytic.plan.update"}
)
_ANALYTIC_ACCOUNT_WRITE_CAPABILITIES = frozenset(
    {
        "analytic.account.create",
        "analytic.account.update",
        "analytic.account.archive",
        "analytic.account.restore",
    }
)
_ANALYTIC_LINE_WRITE_CAPABILITIES = frozenset(
    {"analytic.line.create", "analytic.line.update", "analytic.line.delete"}
)
_BUDGET_WRITE_CAPABILITIES = frozenset(
    {
        "budget.create",
        "budget.update_draft",
        "budget.lines.replace",
        "budget.confirm",
        "budget.reset_to_draft",
        "budget.cancel",
        "budget.mark_done",
    }
)
_PARTNER_WRITE_CAPABILITIES = frozenset(
    {
        "partner.create",
        "partner.update",
        "partner.archive",
        "partner.restore",
        "partner.accounting.update",
    }
)
_PARTNER_BANK_WRITE_CAPABILITIES = frozenset(
    {
        "partner.bank_account.create",
        "partner.bank_account.update",
        "partner.bank_account.archive",
        "partner.bank_account.restore",
    }
)
_ACCOUNT_CONFIGURATION_WRITE_CAPABILITIES = frozenset(
    {
        "account.account.create",
        "account.account.update",
        "account.account.archive",
        "account.account.restore",
    }
)
_JOURNAL_CONFIGURATION_WRITE_CAPABILITIES = frozenset(
    {"journal.create", "journal.update", "journal.archive", "journal.restore"}
)
_TAX_CONFIGURATION_WRITE_CAPABILITIES = frozenset(
    {"tax.create", "tax.update", "tax.archive", "tax.restore"}
)
_PAYMENT_TERM_WRITE_CAPABILITIES = frozenset(
    {
        "payment_term.create",
        "payment_term.update",
        "payment_term.lines.replace",
        "payment_term.archive",
        "payment_term.restore",
    }
)
_FISCAL_POSITION_WRITE_CAPABILITIES = frozenset(
    {
        "fiscal_position.create",
        "fiscal_position.update",
        "fiscal_position.account_mappings.replace",
        "fiscal_position.archive",
        "fiscal_position.restore",
    }
)
_JOURNAL_GROUP_WRITE_CAPABILITIES = frozenset(
    {"journal.group.create", "journal.group.update"}
)
_ACCOUNT_GROUP_WRITE_CAPABILITIES = frozenset(
    {"account.group.create", "account.group.update"}
)
_RECONCILIATION_MODEL_WRITE_CAPABILITIES = frozenset(
    {
        "reconciliation.model.create",
        "reconciliation.model.update",
        "reconciliation.model.lines.replace",
        "reconciliation.model.archive",
        "reconciliation.model.restore",
    }
)
_ACCOUNT_TAG_WRITE_CAPABILITIES = frozenset(
    {
        "account.tag.create",
        "account.tag.update",
        "account.tag.archive",
        "account.tag.restore",
    }
)
_TAX_GROUP_WRITE_CAPABILITIES = frozenset({"tax.group.create", "tax.group.update"})
_CASH_ROUNDING_WRITE_CAPABILITIES = frozenset(
    {"cash_rounding.create", "cash_rounding.update"}
)
_ACCOUNTING_RULE_WRITE_CAPABILITIES = frozenset(
    {
        "fiscal_year.create",
        "fiscal_year.update",
        "analytic.applicability.create",
        "analytic.applicability.update",
        "analytic.distribution_model.create",
        "analytic.distribution_model.update",
    }
)
_ACCOUNT_RETURN_WRITE_CAPABILITIES = frozenset(
    {
        "account.return.create",
        "account.return.checks.refresh",
        "account.return.check.result.update",
        "account.return.validate",
        "account.return.mark_submitted",
        "account.return.archive",
        "account.return.restore",
        "account.return.delete",
    }
)
_CONTEXT_FIELDS = frozenset(
    {"database", "company_id", "user_login", "language", "timezone"}
)
_RESULT_FIELDS = frozenset(
    {
        "model",
        "id",
        "name",
        "state",
        "company_id",
        "move_type",
        "source_id",
        "line_ids",
        "partial_reconcile_ids",
        "full_reconcile_id",
        "reconciled",
    }
)
_PAGE_FIELDS = frozenset(
    {
        "user_id",
        "company_visible",
        "module_installed",
        "access_allowed",
        "idempotent_replay",
        "result",
    }
)
_BATCH_RESULT_FIELDS = frozenset({"items", "processed_count"})
_DECIMAL_PATTERN = re.compile(r"^(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
_SIGNED_DECIMAL_PATTERN = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
_ANALYTIC_KEY_PATTERN = re.compile(r"^[1-9][0-9]*(?:,[1-9][0-9]*)*$")
_IDEMPOTENCY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")
_INVOICE_MOVE_TYPES = frozenset(
    {"out_invoice", "out_refund", "in_invoice", "in_refund"}
)
_ASSET_METHODS = frozenset({"linear", "degressive", "degressive_then_linear"})
_ASSET_PRORATA_TYPES = frozenset({"none", "constant_periods", "daily_computation"})
_ASSET_STATES = frozenset({"draft", "open", "paused", "close", "cancelled"})
_ASSET_BASE_NAME_MAXIMUM = 426
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
        "expense_other",
        "expense_depreciation",
        "expense_direct_cost",
        "off_balance",
    }
)
_JOURNAL_TYPES = frozenset({"sale", "purchase", "cash", "bank", "credit", "general"})
_TAX_USES = frozenset({"sale", "purchase", "none"})
_TAX_AMOUNT_TYPES = frozenset({"fixed", "percent", "division"})
_PRICE_INCLUDE_OVERRIDES = frozenset({"tax_included", "tax_excluded"})


class CoreWritePort(Protocol):
    @property
    def user_id(self) -> int: ...

    def execute(
        self,
        *,
        capability_id: str,
        company_id: int,
        idempotency_key: str,
        confirmation: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]: ...


class CoreWriteError(RuntimeError):
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


def _invalid(message: str, *, code: str = "invalid_request") -> CoreWriteError:
    return CoreWriteError(code, message, exit_code=2)


def _failed(message: str) -> CoreWriteError:
    return CoreWriteError("failed_validation", message, exit_code=8)


def _is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _valid_id(value: Any) -> bool:
    return _is_integer(value) and value > 0


def _valid_optional_id(value: Any) -> bool:
    return value is None or _valid_id(value)


def _is_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_bounded_text(value: Any, maximum: int) -> bool:
    return (
        isinstance(value, str) and value == value.strip() and 1 <= len(value) <= maximum
    )


def _is_optional_bounded_string(value: Any, maximum: int) -> bool:
    return value is None or (isinstance(value, str) and 1 <= len(value) <= maximum)


def _is_optional_text(value: Any) -> bool:
    return value is None or _is_text(value)


def _is_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return False
    return parsed.isoformat() == value


def _is_datetime(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return False
    return strftime("%Y-%m-%d %H:%M:%S", parsed) == value


def _is_nullable_bounded_text(value: Any, maximum: int) -> bool:
    return value is None or _is_bounded_text(value, maximum)


def _decimal(value: Any, *, signed: bool) -> Decimal | None:
    pattern = _SIGNED_DECIMAL_PATTERN if signed else _DECIMAL_PATTERN
    if (
        not isinstance(value, str)
        or len(value) > 256
        or pattern.fullmatch(value) is None
    ):
        return None
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        return None
    return parsed if parsed.is_finite() else None


def _canonical_decimal_text(value: Decimal) -> str:
    if not value:
        return "0"
    text = format(value, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def _canonical_decimal(value: Any, *, signed: bool) -> Decimal | None:
    parsed = _decimal(value, signed=signed)
    if parsed is None or _canonical_decimal_text(parsed) != value:
        return None
    return parsed


def _validate_analytic_distribution(value: Any) -> dict[str, str] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or not 1 <= len(value) <= 16:
        raise _invalid(
            "analytic_distribution must be null or contain between 1 and 16 items."
        )
    seen_ids: set[int] = set()
    normalized: dict[str, str] = {}
    for key, percentage_text in value.items():
        if not isinstance(key, str) or _ANALYTIC_KEY_PATTERN.fullmatch(key) is None:
            raise _invalid(
                "analytic_distribution keys must contain sorted positive IDs."
            )
        account_ids = [int(item) for item in key.split(",")]
        if account_ids != sorted(set(account_ids)):
            raise _invalid(
                "analytic_distribution keys must contain sorted unique positive IDs."
            )
        if seen_ids.intersection(account_ids):
            raise _invalid(
                "An analytic account ID cannot occur in more than one distribution key."
            )
        seen_ids.update(account_ids)
        percentage = _canonical_decimal(percentage_text, signed=False)
        decimal_places = (
            max(0, -percentage.as_tuple().exponent) if percentage is not None else 0
        )
        if (
            percentage is None
            or percentage <= 0
            or percentage > 100
            or decimal_places > 4
        ):
            raise _invalid(
                "analytic_distribution values must be canonical percentages "
                "greater than 0 and at most 100 with up to four decimal places."
            )
        normalized[key] = percentage_text
    return {key: normalized[key] for key in sorted(normalized)}


def _validate_envelope(request: Any) -> tuple[str, dict[str, Any], Any]:
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
    if not isinstance(context, dict) or set(context) != _CONTEXT_FIELDS:
        raise _invalid("context must contain only the required v1 fields.")
    for key in ("database", "user_login", "language", "timezone"):
        if not _is_text(context[key]):
            raise _invalid(f"context.{key} must be a non-empty string.")
    if not _valid_id(context["company_id"]):
        raise _invalid("context.company_id must be a positive integer.")
    return request_id, dict(context), request["parameters"]


def _validate_ids(value: Any, *, exact_length: int | None = None) -> list[int] | None:
    if (
        not isinstance(value, list)
        or (exact_length is not None and len(value) != exact_length)
        or any(not _valid_id(item) for item in value)
        or len(set(value)) != len(value)
    ):
        return None
    return list(value)


def _validate_deferred_line_dates(line: dict[str, Any]) -> None:
    has_start = "deferred_start_date" in line
    has_end = "deferred_end_date" in line
    if has_start != has_end:
        raise _invalid("Invoice-line deferred dates must be provided together.")
    if not has_start:
        return
    start, end = line["deferred_start_date"], line["deferred_end_date"]
    if start is None and end is None:
        return
    if not (_is_date(start) and _is_date(end) and start <= end):
        raise _invalid(
            "Invoice-line deferred dates must both be null or YYYY-MM-DD dates "
            "with start on or before end."
        )


def _validate_invoice_parameters(parameters: Any) -> dict[str, Any]:
    required = {"partner_id", "journal_id", "invoice_date", "currency_id", "lines"}
    allowed = required | {
        "date",
        "invoice_date_due",
        "payment_term_id",
        "partner_bank_id",
        "fiscal_position_id",
        "reference",
        "payment_reference",
    }
    if not isinstance(parameters, dict) or not required <= set(parameters) <= allowed:
        raise _invalid("Invoice creation parameters do not match the fixed contract.")
    for key in ("partner_id", "journal_id", "currency_id"):
        if not _valid_id(parameters[key]):
            raise _invalid(f"parameters.{key} must be a positive integer.")
    if not _is_date(parameters["invoice_date"]):
        raise _invalid("parameters.invoice_date must be a YYYY-MM-DD date.")
    if "date" in parameters and not _is_date(parameters["date"]):
        raise _invalid("parameters.date must be a YYYY-MM-DD date.")
    if "invoice_date_due" in parameters and not (
        parameters["invoice_date_due"] is None
        or _is_date(parameters["invoice_date_due"])
    ):
        raise _invalid("parameters.invoice_date_due must be null or a YYYY-MM-DD date.")
    if "payment_term_id" in parameters and not _valid_optional_id(
        parameters["payment_term_id"]
    ):
        raise _invalid("parameters.payment_term_id must be null or a positive integer.")
    for field in ("partner_bank_id", "fiscal_position_id"):
        if field in parameters and not _valid_optional_id(parameters[field]):
            raise _invalid(f"parameters.{field} must be null or a positive integer.")
    if (
        parameters.get("invoice_date_due") is not None
        and parameters.get("payment_term_id") is not None
    ):
        raise _invalid(
            "parameters.invoice_date_due and parameters.payment_term_id are "
            "mutually exclusive when non-null."
        )
    for field in ("reference", "payment_reference"):
        if field in parameters and not _is_optional_bounded_string(
            parameters[field], 200
        ):
            raise _invalid(
                f"parameters.{field} must be null or a 1-200 character string."
            )
    lines = parameters["lines"]
    if not isinstance(lines, list) or not 1 <= len(lines) <= 200:
        raise _invalid("parameters.lines must contain between 1 and 200 lines.")
    normalized_lines: list[dict[str, Any]] = []
    required_line_fields = {
        "name",
        "account_id",
        "quantity",
        "price_unit",
        "tax_ids",
    }
    allowed_line_fields = required_line_fields | {
        "product_id",
        "discount",
        "analytic_distribution",
        "deferred_start_date",
        "deferred_end_date",
    }
    for line in lines:
        if (
            not isinstance(line, dict)
            or not required_line_fields <= set(line) <= allowed_line_fields
        ):
            raise _invalid("Each invoice line must match the fixed line contract.")
        if not _is_bounded_text(line["name"], 500):
            raise _invalid("Invoice line names must be non-empty strings.")
        if not _valid_id(line["account_id"]):
            raise _invalid("Invoice line account_id must be a positive integer.")
        quantity = _decimal(line["quantity"], signed=False)
        if quantity is None or quantity <= 0:
            raise _invalid("Invoice line quantity must be a positive decimal string.")
        if _decimal(line["price_unit"], signed=True) is None:
            raise _invalid("Invoice line price_unit must be a signed decimal string.")
        if "product_id" in line and not _valid_optional_id(line["product_id"]):
            raise _invalid(
                "Invoice line product_id must be null or a positive integer."
            )
        if "discount" in line:
            discount = _decimal(line["discount"], signed=False)
            if discount is None or discount > 100:
                raise _invalid("Invoice line discount must be between 0 and 100.")
        tax_ids = _validate_ids(line["tax_ids"])
        if tax_ids is None:
            raise _invalid(
                "Invoice line tax_ids must contain unique positive integers."
            )
        _validate_deferred_line_dates(line)
        normalized_line = {**line, "tax_ids": tax_ids}
        if "analytic_distribution" in line:
            normalized_line["analytic_distribution"] = _validate_analytic_distribution(
                line["analytic_distribution"]
            )
        normalized_lines.append(normalized_line)
    return {**parameters, "lines": normalized_lines}


def _validate_journal_lines(lines: Any, *, minimum: int) -> list[dict[str, Any]]:
    if not isinstance(lines, list) or not minimum <= len(lines) <= 500:
        raise _invalid(
            f"parameters.lines must contain between {minimum} and 500 lines."
        )
    required_line_fields = {
        "name",
        "account_id",
        "partner_id",
        "debit",
        "credit",
    }
    allowed_line_fields = required_line_fields | {
        "currency_id",
        "amount_currency",
        "analytic_distribution",
        "date_maturity",
    }
    total_debit = Decimal(0)
    total_credit = Decimal(0)
    normalized_lines: list[dict[str, Any]] = []
    for line in lines:
        if (
            not isinstance(line, dict)
            or not required_line_fields <= set(line) <= allowed_line_fields
        ):
            raise _invalid(
                "Each journal-entry line must match the fixed line contract."
            )
        if not _is_bounded_text(line["name"], 500):
            raise _invalid("Journal-entry line names must be non-empty strings.")
        if not _valid_id(line["account_id"]):
            raise _invalid("Journal-entry line account_id must be a positive integer.")
        if not _valid_optional_id(line["partner_id"]):
            raise _invalid(
                "Journal-entry line partner_id must be null or a positive integer."
            )
        if "date_maturity" in line and not (
            line["date_maturity"] is None or _is_date(line["date_maturity"])
        ):
            raise _invalid(
                "Journal-entry line date_maturity must be null or a YYYY-MM-DD date."
            )
        debit = _decimal(line["debit"], signed=False)
        credit = _decimal(line["credit"], signed=False)
        if debit is None or credit is None:
            raise _invalid("Journal-entry debit and credit must be decimal strings.")
        if (debit > 0) == (credit > 0):
            raise _invalid(
                "Each journal-entry line must have exactly one positive side."
            )
        has_currency = "currency_id" in line
        has_amount_currency = "amount_currency" in line
        if has_currency != has_amount_currency:
            raise _invalid(
                "Journal-entry currency_id and amount_currency must be provided "
                "together."
            )
        if has_currency:
            currency_id = line["currency_id"]
            amount_currency_value = line["amount_currency"]
            if currency_id is None or amount_currency_value is None:
                if currency_id is not None or amount_currency_value is not None:
                    raise _invalid(
                        "Journal-entry currency_id and amount_currency must both be "
                        "null or both be non-null."
                    )
            else:
                amount_currency = _decimal(amount_currency_value, signed=True)
                if not _valid_id(currency_id) or amount_currency in {None, Decimal(0)}:
                    raise _invalid(
                        "Journal-entry currency_id must be positive and "
                        "amount_currency must be a nonzero signed decimal string."
                    )
                if (amount_currency > 0) != (debit > credit):
                    raise _invalid(
                        "Journal-entry amount_currency must have the same sign as "
                        "debit minus credit."
                    )
        total_debit += debit
        total_credit += credit
        normalized_line = dict(line)
        if "analytic_distribution" in line:
            normalized_line["analytic_distribution"] = _validate_analytic_distribution(
                line["analytic_distribution"]
            )
        normalized_lines.append(normalized_line)
    if total_debit == 0 or total_debit != total_credit:
        raise _invalid(
            "Journal-entry debit and credit totals must be nonzero and balanced."
        )
    return normalized_lines


def _validate_journal_parameters(parameters: Any) -> dict[str, Any]:
    required = {
        "journal_id",
        "date",
        "lines",
    }
    allowed = required | {"reference"}
    if not isinstance(parameters, dict) or not required <= set(parameters) <= allowed:
        raise _invalid(
            "Journal-entry creation parameters do not match the fixed contract."
        )
    if not _valid_id(parameters["journal_id"]):
        raise _invalid("parameters.journal_id must be a positive integer.")
    if not _is_date(parameters["date"]):
        raise _invalid("parameters.date must be a YYYY-MM-DD date.")
    if "reference" in parameters and not _is_optional_bounded_string(
        parameters["reference"], 200
    ):
        raise _invalid("parameters.reference must be null or a 1-200 character string.")
    normalized_lines = _validate_journal_lines(parameters["lines"], minimum=2)
    return {**parameters, "lines": normalized_lines}


def _validate_invoice_update_parameters(parameters: Any) -> dict[str, Any]:
    if not isinstance(parameters, dict) or set(parameters) != {"move_id", "changes"}:
        raise _invalid("Invoice-update parameters do not match the fixed contract.")
    if not _valid_id(parameters["move_id"]):
        raise _invalid("parameters.move_id must be a positive integer.")
    changes = parameters["changes"]
    allowed = {
        "partner_id",
        "journal_id",
        "currency_id",
        "date",
        "invoice_date",
        "invoice_date_due",
        "payment_term_id",
        "partner_bank_id",
        "fiscal_position_id",
        "reference",
        "payment_reference",
    }
    if not isinstance(changes, dict) or not changes or not set(changes) <= allowed:
        raise _invalid("parameters.changes contains no supported invoice update.")
    for field in ("partner_id", "journal_id", "currency_id"):
        if field in changes and not _valid_id(changes[field]):
            raise _invalid(f"changes.{field} must be a positive integer.")
    for field in ("date", "invoice_date"):
        if field in changes and not _is_date(changes[field]):
            raise _invalid(f"changes.{field} must be a YYYY-MM-DD date.")
    if "invoice_date_due" in changes and not (
        changes["invoice_date_due"] is None or _is_date(changes["invoice_date_due"])
    ):
        raise _invalid("changes.invoice_date_due must be null or a YYYY-MM-DD date.")
    if "payment_term_id" in changes and not _valid_optional_id(
        changes["payment_term_id"]
    ):
        raise _invalid("changes.payment_term_id must be null or a positive integer.")
    for field in ("partner_bank_id", "fiscal_position_id"):
        if field in changes and not _valid_optional_id(changes[field]):
            raise _invalid(f"changes.{field} must be null or a positive integer.")
    for field in ("reference", "payment_reference"):
        if field in changes and not _is_optional_bounded_string(changes[field], 200):
            raise _invalid(f"changes.{field} must be null or a 1-200 character string.")
    if "invoice_date_due" in changes and "payment_term_id" in changes:
        raise _invalid(
            "changes.invoice_date_due and changes.payment_term_id are mutually exclusive."
        )
    return {"move_id": parameters["move_id"], "changes": dict(changes)}


def _validate_invoice_line_replacement_parameters(
    parameters: Any,
) -> dict[str, Any]:
    if not isinstance(parameters, dict) or set(parameters) != {"move_id", "lines"}:
        raise _invalid(
            "Invoice-line replacement parameters do not match the fixed contract."
        )
    if not _valid_id(parameters["move_id"]):
        raise _invalid("parameters.move_id must be a positive integer.")
    lines = parameters["lines"]
    if not isinstance(lines, list) or not 1 <= len(lines) <= 500:
        raise _invalid("parameters.lines must contain between 1 and 500 lines.")
    required_line_fields = {
        "name",
        "product_id",
        "account_id",
        "quantity",
        "price_unit",
        "discount",
        "tax_ids",
    }
    allowed_line_fields = required_line_fields | {
        "analytic_distribution",
        "deferred_start_date",
        "deferred_end_date",
    }
    normalized_lines: list[dict[str, Any]] = []
    for line in lines:
        if (
            not isinstance(line, dict)
            or not required_line_fields <= set(line) <= allowed_line_fields
        ):
            raise _invalid("Each invoice line must match the replacement contract.")
        if not _is_bounded_text(line["name"], 500):
            raise _invalid("Invoice line names must be non-empty strings.")
        if not _valid_optional_id(line["product_id"]):
            raise _invalid(
                "Invoice line product_id must be null or a positive integer."
            )
        if not _valid_id(line["account_id"]):
            raise _invalid("Invoice line account_id must be a positive integer.")
        if _decimal(line["quantity"], signed=False) is None:
            raise _invalid("Invoice line quantity must be an unsigned decimal string.")
        if _decimal(line["price_unit"], signed=True) is None:
            raise _invalid("Invoice line price_unit must be a signed decimal string.")
        discount = _decimal(line["discount"], signed=False)
        if discount is None or discount > 100:
            raise _invalid("Invoice line discount must be between 0 and 100.")
        tax_ids = _validate_ids(line["tax_ids"])
        if tax_ids is None or tax_ids != sorted(tax_ids):
            raise _invalid(
                "Invoice line tax_ids must be sorted unique positive integers."
            )
        _validate_deferred_line_dates(line)
        normalized_line = {**line, "tax_ids": tax_ids}
        if "analytic_distribution" in line:
            normalized_line["analytic_distribution"] = _validate_analytic_distribution(
                line["analytic_distribution"]
            )
        normalized_lines.append(normalized_line)
    return {"move_id": parameters["move_id"], "lines": normalized_lines}


def _validate_journal_entry_update_parameters(parameters: Any) -> dict[str, Any]:
    if not isinstance(parameters, dict) or set(parameters) != {"move_id", "changes"}:
        raise _invalid(
            "Journal-entry update parameters do not match the fixed contract."
        )
    if not _valid_id(parameters["move_id"]):
        raise _invalid("parameters.move_id must be a positive integer.")
    changes = parameters["changes"]
    allowed = {"date", "journal_id", "reference"}
    if not isinstance(changes, dict) or not changes or not set(changes) <= allowed:
        raise _invalid("parameters.changes contains no supported journal-entry update.")
    if "date" in changes and not _is_date(changes["date"]):
        raise _invalid("changes.date must be a YYYY-MM-DD date.")
    if "journal_id" in changes and not _valid_id(changes["journal_id"]):
        raise _invalid("changes.journal_id must be a positive integer.")
    if "reference" in changes and not _is_optional_bounded_string(
        changes["reference"], 200
    ):
        raise _invalid("changes.reference must be null or a 1-200 character string.")
    return {"move_id": parameters["move_id"], "changes": dict(changes)}


def _validate_journal_line_replacement_parameters(
    parameters: Any,
) -> dict[str, Any]:
    if not isinstance(parameters, dict) or set(parameters) != {"move_id", "lines"}:
        raise _invalid(
            "Journal-entry line replacement parameters do not match the fixed contract."
        )
    if not _valid_id(parameters["move_id"]):
        raise _invalid("parameters.move_id must be a positive integer.")
    return {
        "move_id": parameters["move_id"],
        "lines": _validate_journal_lines(parameters["lines"], minimum=1),
    }


def _validate_single_id(parameters: Any, field: str) -> dict[str, Any]:
    if (
        not isinstance(parameters, dict)
        or set(parameters) != {field}
        or not _valid_id(parameters[field])
    ):
        raise _invalid(
            f"parameters.{field} must be the only positive integer parameter."
        )
    return dict(parameters)


def _validate_singular_or_batch_ids(
    parameters: Any, singular_field: str, batch_field: str
) -> dict[str, Any]:
    if not isinstance(parameters, dict):
        raise _invalid(
            f"parameters must contain exactly one of {singular_field} or {batch_field}."
        )
    if set(parameters) == {singular_field} and _valid_id(parameters[singular_field]):
        return dict(parameters)
    if set(parameters) == {batch_field}:
        ids = _validate_ids(parameters[batch_field])
        if ids is not None and 2 <= len(ids) <= 100:
            return {batch_field: sorted(ids)}
    raise _invalid(
        f"parameters must contain one positive {singular_field}, or {batch_field} "
        "with 2 to 100 unique positive integers."
    )


def _validate_reverse_parameters(parameters: Any) -> dict[str, Any]:
    if not isinstance(parameters, dict) or set(parameters) != {
        "move_id",
        "date",
        "reason",
    }:
        raise _invalid(
            "Journal-entry reversal parameters do not match the fixed contract."
        )
    if not _valid_id(parameters["move_id"]):
        raise _invalid("parameters.move_id must be a positive integer.")
    if not _is_date(parameters["date"]):
        raise _invalid("parameters.date must be a YYYY-MM-DD date.")
    if not _is_bounded_text(parameters["reason"], 200):
        raise _invalid("parameters.reason must be a non-empty string.")
    return dict(parameters)


def _validate_refund_parameters(parameters: Any) -> dict[str, Any]:
    required = {"move_id", "date", "reason"}
    allowed = required | {"lines"}
    if not isinstance(parameters, dict) or not required <= set(parameters) <= allowed:
        raise _invalid("Refund creation parameters do not match the fixed contract.")
    _validate_reverse_parameters(
        {field: value for field, value in parameters.items() if field != "lines"}
    )
    normalized = dict(parameters)
    if "lines" in parameters:
        normalized["lines"] = _validate_invoice_line_replacement_parameters(
            {"move_id": parameters["move_id"], "lines": parameters["lines"]}
        )["lines"]
    return normalized


def _validate_payment_register_parameters(parameters: Any) -> dict[str, Any]:
    common = {"journal_id", "payment_date"}
    optional = {
        "amount",
        "payment_difference_handling",
        "writeoff_account_id",
        "writeoff_label",
    }
    if not isinstance(parameters, dict):
        raise _invalid(
            "Payment registration parameters do not match the fixed contract."
        )
    keys = set(parameters)
    single = common | {"move_id"} <= keys <= common | {"move_id"} | optional
    many = keys == common | {"move_ids"}
    if not single and not many:
        raise _invalid(
            "Payment registration parameters do not match the fixed contract."
        )
    if many:
        move_ids = _validate_ids(parameters["move_ids"])
        if move_ids is None or not 2 <= len(move_ids) <= 100:
            raise _invalid(
                "parameters.move_ids must contain 2-100 distinct positive integers."
            )
    for key in ("move_id", "journal_id") if single else ("journal_id",):
        if not _valid_id(parameters[key]):
            raise _invalid(f"parameters.{key} must be a positive integer.")
    if not _is_date(parameters["payment_date"]):
        raise _invalid("parameters.payment_date must be a YYYY-MM-DD date.")
    if "amount" in parameters:
        amount = _canonical_decimal(parameters["amount"], signed=False)
        if amount is None or amount <= 0:
            raise _invalid(
                "parameters.amount must be a positive canonical decimal string."
            )
    handling = parameters.get("payment_difference_handling")
    if "payment_difference_handling" in parameters and handling not in (
        "open",
        "reconcile",
    ):
        raise _invalid("payment_difference_handling must be 'open' or 'reconcile'.")
    if handling == "reconcile":
        if "amount" not in parameters or not _valid_id(
            parameters.get("writeoff_account_id")
        ):
            raise _invalid(
                "Reconcile requires amount and a positive writeoff_account_id."
            )
        if "writeoff_label" in parameters and not _is_bounded_text(
            parameters["writeoff_label"], 200
        ):
            raise _invalid("writeoff_label must be a trimmed 1-200 character string.")
    elif {"writeoff_account_id", "writeoff_label"} & parameters.keys():
        raise _invalid(
            "Write-off fields require payment_difference_handling='reconcile'."
        )
    normalized = dict(parameters)
    if many:
        normalized["move_ids"] = sorted(move_ids)
    return normalized


def _validate_invoice_type_switch_parameters(parameters: Any) -> dict[str, Any]:
    if (
        not isinstance(parameters, dict)
        or set(parameters) != {"move_id", "target_move_type"}
        or not _valid_id(parameters["move_id"])
        or parameters["target_move_type"]
        not in {"out_invoice", "out_refund", "in_invoice", "in_refund"}
    ):
        raise _invalid("Invoice-type-switch parameters do not match the fixed contract.")
    return dict(parameters)


def _validate_payment_fields(values: Any, *, partial: bool) -> dict[str, Any]:
    fields = {
        "payment_type",
        "partner_type",
        "partner_id",
        "amount",
        "currency_id",
        "journal_id",
        "payment_method_line_id",
        "date",
        "payment_reference",
    }
    required = fields - {"payment_reference"}
    if (
        not isinstance(values, dict)
        or (partial and (not values or not set(values) <= fields))
        or (not partial and not (required <= set(values) <= fields))
    ):
        raise _invalid("Payment parameters do not match the fixed contract.")
    if "payment_type" in values and values["payment_type"] not in {
        "inbound",
        "outbound",
    }:
        raise _invalid("payment_type must be 'inbound' or 'outbound'.")
    if "partner_type" in values and values["partner_type"] not in {
        "customer",
        "supplier",
    }:
        raise _invalid("partner_type must be 'customer' or 'supplier'.")
    for field in (
        "partner_id",
        "currency_id",
        "journal_id",
        "payment_method_line_id",
    ):
        if field in values and not _valid_id(values[field]):
            raise _invalid(f"{field} must be a positive integer.")
    if "amount" in values:
        amount = _decimal(values["amount"], signed=False)
        if amount is None or amount <= 0:
            raise _invalid("amount must be a positive decimal string.")
    if "date" in values and not _is_date(values["date"]):
        raise _invalid("date must be a YYYY-MM-DD date.")
    if "payment_reference" in values and not (
        values["payment_reference"] is None
        or _is_bounded_text(values["payment_reference"], 200)
    ):
        raise _invalid("payment_reference must be null or a trimmed string.")
    normalized = dict(values)
    if not partial:
        normalized.setdefault("payment_reference", None)
    return normalized


def _validate_payment_create_parameters(parameters: Any) -> dict[str, Any]:
    return _validate_payment_fields(parameters, partial=False)


def _validate_payment_update_parameters(parameters: Any) -> dict[str, Any]:
    if not isinstance(parameters, dict) or set(parameters) != {"payment_id", "changes"}:
        raise _invalid("Payment-update parameters do not match the fixed contract.")
    if not _valid_id(parameters["payment_id"]):
        raise _invalid("parameters.payment_id must be a positive integer.")
    return {
        "payment_id": parameters["payment_id"],
        "changes": _validate_payment_fields(parameters["changes"], partial=True),
    }


def _validate_reconciliation_parameters(
    capability_id: str, parameters: Any
) -> dict[str, Any]:
    if not isinstance(parameters, dict):
        raise _invalid("Reconciliation parameters do not match the fixed contract.")
    if set(parameters) == {"line_ids"}:
        line_ids = _validate_ids(parameters["line_ids"], exact_length=2)
        if line_ids is None:
            raise _invalid(
                "parameters.line_ids must contain exactly two distinct positive "
                "integers."
            )
        return {"line_ids": sorted(line_ids)}
    invoice_fields = (
        {"invoice_id", "outstanding_line_id"}
        if capability_id == "reconciliation.apply"
        else {
            "invoice_id",
            "partial_reconcile_id",
            "invoice_line_id",
            "counterpart_line_id",
        }
    )
    if set(parameters) != invoice_fields or any(
        not _valid_id(parameters[field]) for field in invoice_fields
    ):
        raise _invalid("Reconciliation parameters do not match the fixed contract.")
    if (
        capability_id == "reconciliation.undo"
        and parameters["invoice_line_id"] == parameters["counterpart_line_id"]
    ):
        raise _invalid(
            "invoice_line_id and counterpart_line_id must be distinct positive "
            "integers."
        )
    return dict(parameters)


def _validate_bank_transaction_parameters(parameters: Any) -> dict[str, Any]:
    expected = {"journal_id", "date", "amount", "payment_ref", "partner_id"}
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise _invalid("Bank-transaction parameters do not match the fixed contract.")
    if not _valid_id(parameters["journal_id"]):
        raise _invalid("parameters.journal_id must be a positive integer.")
    if not _is_date(parameters["date"]):
        raise _invalid("parameters.date must be a YYYY-MM-DD date.")
    amount = _decimal(parameters["amount"], signed=True)
    if amount is None or amount == 0:
        raise _invalid("parameters.amount must be a nonzero signed decimal string.")
    if not _is_bounded_text(parameters["payment_ref"], 200):
        raise _invalid("parameters.payment_ref must be a non-empty string.")
    if not _valid_optional_id(parameters["partner_id"]):
        raise _invalid("parameters.partner_id must be null or a positive integer.")
    return dict(parameters)


def _validate_bank_transaction_update_parameters(parameters: Any) -> dict[str, Any]:
    if not isinstance(parameters, dict) or set(parameters) != {
        "transaction_id",
        "changes",
    }:
        raise _invalid("Bank-transaction update parameters are invalid.")
    if not _valid_id(parameters["transaction_id"]):
        raise _invalid("parameters.transaction_id must be a positive integer.")
    changes = parameters["changes"]
    allowed = {"date", "amount", "payment_ref", "partner_id"}
    if not isinstance(changes, dict) or not changes or not set(changes) <= allowed:
        raise _invalid("parameters.changes contains no supported bank update.")
    if "date" in changes and not _is_date(changes["date"]):
        raise _invalid("changes.date must be a YYYY-MM-DD date.")
    if "amount" in changes:
        amount = _decimal(changes["amount"], signed=True)
        if amount is None or amount == 0:
            raise _invalid("changes.amount must be a nonzero decimal string.")
    if "payment_ref" in changes and not _is_bounded_text(changes["payment_ref"], 200):
        raise _invalid("changes.payment_ref must be a trimmed 1-200 character string.")
    if "partner_id" in changes and not _valid_optional_id(changes["partner_id"]):
        raise _invalid("changes.partner_id must be null or a positive integer.")
    return {"transaction_id": parameters["transaction_id"], "changes": dict(changes)}


def _validate_bank_match_parameters(parameters: Any) -> dict[str, Any]:
    if not isinstance(parameters, dict) or set(parameters) != {
        "transaction_id",
        "candidate_line_ids",
    }:
        raise _invalid("Bank-match parameters do not match the fixed contract.")
    if not _valid_id(parameters["transaction_id"]):
        raise _invalid("parameters.transaction_id must be a positive integer.")
    line_ids = _validate_ids(parameters["candidate_line_ids"])
    if line_ids is None or not 1 <= len(line_ids) <= 50 or line_ids != sorted(line_ids):
        raise _invalid(
            "parameters.candidate_line_ids must contain 1 to 50 sorted unique IDs."
        )
    return {
        "transaction_id": parameters["transaction_id"],
        "candidate_line_ids": line_ids,
    }


def _validate_write_off_parameters(parameters: Any) -> dict[str, Any]:
    if not isinstance(parameters, dict) or set(parameters) != {
        "transaction_id",
        "write_off_account_id",
        "label",
        "expected_residual_amount",
    }:
        raise _invalid("Write-off parameters do not match the fixed contract.")
    for field in ("transaction_id", "write_off_account_id"):
        if not _valid_id(parameters[field]):
            raise _invalid(f"parameters.{field} must be a positive integer.")
    if not _is_bounded_text(parameters["label"], 200):
        raise _invalid("parameters.label must be a trimmed 1-200 character string.")
    residual = _decimal(parameters["expected_residual_amount"], signed=True)
    if residual is None or residual == 0:
        raise _invalid(
            "parameters.expected_residual_amount must be a nonzero decimal string."
        )
    return dict(parameters)


def _validate_analytic_account_create_parameters(parameters: Any) -> dict[str, Any]:
    required = {"name", "plan_id"}
    allowed = required | {"code", "partner_id"}
    if not isinstance(parameters, dict) or not (required <= set(parameters) <= allowed):
        raise _invalid("Analytic-account creation parameters are invalid.")
    if (
        not _is_bounded_text(parameters["name"], 200)
        or "[ODACV4:" in parameters["name"]
    ):
        raise _invalid(
            "parameters.name must be a trimmed business name without the reserved marker."
        )
    if not _valid_id(parameters["plan_id"]):
        raise _invalid("parameters.plan_id must be a positive integer.")
    if "code" in parameters and not (
        parameters["code"] is None or _is_bounded_text(parameters["code"], 200)
    ):
        raise _invalid("parameters.code must be null or a trimmed string.")
    if "partner_id" in parameters and not _valid_optional_id(parameters["partner_id"]):
        raise _invalid("parameters.partner_id must be null or a positive integer.")
    normalized = dict(parameters)
    normalized.setdefault("code", None)
    normalized.setdefault("partner_id", None)
    return normalized


def _validate_analytic_account_update_parameters(parameters: Any) -> dict[str, Any]:
    if not isinstance(parameters, dict) or set(parameters) != {
        "analytic_account_id",
        "changes",
    }:
        raise _invalid("Analytic-account update parameters are invalid.")
    if not _valid_id(parameters["analytic_account_id"]):
        raise _invalid("parameters.analytic_account_id must be a positive integer.")
    changes = parameters["changes"]
    allowed = {"name", "code", "partner_id", "active"}
    if not isinstance(changes, dict) or not changes or not set(changes) <= allowed:
        raise _invalid("parameters.changes contains no supported analytic update.")
    if "name" in changes and (
        not _is_bounded_text(changes["name"], 200) or "[ODACV4:" in changes["name"]
    ):
        raise _invalid(
            "changes.name must be a trimmed business name without the reserved marker."
        )
    if "code" in changes and not (
        changes["code"] is None or _is_bounded_text(changes["code"], 200)
    ):
        raise _invalid("changes.code must be null or a trimmed string.")
    if "partner_id" in changes and not _valid_optional_id(changes["partner_id"]):
        raise _invalid("changes.partner_id must be null or a positive integer.")
    if "active" in changes and not isinstance(changes["active"], bool):
        raise _invalid("changes.active must be a boolean.")
    return {
        "analytic_account_id": parameters["analytic_account_id"],
        "changes": dict(changes),
    }


def _validate_analytic_plan_values(values: Any, *, partial: bool) -> dict[str, Any]:
    allowed = {"name", "color", "default_applicability"}
    if (
        not isinstance(values, dict)
        or (partial and (not values or not set(values) <= allowed))
        or (not partial and not ({"name"} <= set(values) <= allowed))
    ):
        raise _invalid("Analytic-plan values do not match the fixed contract.")
    if "name" in values and (
        not _is_bounded_text(values["name"], 200)
        or "[ODACV4:" in values["name"]
    ):
        raise _invalid(
            "name must be a trimmed business name without the reserved marker."
        )
    if "color" in values and (
        not _is_integer(values["color"]) or values["color"] < 0
    ):
        raise _invalid("color must be a nonnegative integer.")
    if "default_applicability" in values and values["default_applicability"] not in {
        "optional",
        "mandatory",
        "unavailable",
    }:
        raise _invalid(
            "default_applicability must be optional, mandatory, or unavailable."
        )
    return dict(values)


def _validate_analytic_plan_parameters(
    capability_id: str, parameters: Any
) -> dict[str, Any]:
    if capability_id == "analytic.plan.create":
        if (
            not isinstance(parameters, dict)
            or "parent_plan_id" not in parameters
            or not set(parameters)
            <= {"name", "parent_plan_id", "color", "default_applicability"}
            or not _valid_id(parameters["parent_plan_id"])
        ):
            raise _invalid("Analytic-plan creation parameters are invalid.")
        values = _validate_analytic_plan_values(
            {key: value for key, value in parameters.items() if key != "parent_plan_id"},
            partial=False,
        )
        values.setdefault("color", None)
        values.setdefault("default_applicability", None)
        return {"parent_plan_id": parameters["parent_plan_id"], **values}
    if not isinstance(parameters, dict) or set(parameters) != {"plan_id", "changes"}:
        raise _invalid("Analytic-plan update parameters are invalid.")
    if not _valid_id(parameters["plan_id"]):
        raise _invalid("parameters.plan_id must be a positive integer.")
    return {
        "plan_id": parameters["plan_id"],
        "changes": _validate_analytic_plan_values(
            parameters["changes"], partial=True
        ),
    }


def _validate_analytic_line_values(values: Any, *, partial: bool) -> dict[str, Any]:
    allowed = {
        "name",
        "date",
        "amount",
        "analytic_account_id",
        "reference",
        "unit_amount",
    }
    required = {"name", "date", "amount", "analytic_account_id"}
    if (
        not isinstance(values, dict)
        or (partial and (not values or not set(values) <= allowed))
        or (not partial and not (required <= set(values) <= allowed))
    ):
        raise _invalid("Analytic-line values do not match the fixed contract.")
    if "name" in values and (
        not _is_bounded_text(values["name"], 200)
        or "[ODACV4:" in values["name"]
    ):
        raise _invalid(
            "name must be a trimmed business name without the reserved marker."
        )
    if "date" in values and not _is_date(values["date"]):
        raise _invalid("date must be a YYYY-MM-DD date.")
    if "amount" in values and _canonical_decimal(values["amount"], signed=True) is None:
        raise _invalid("amount must be a canonical signed decimal string.")
    if "analytic_account_id" in values and not _valid_id(
        values["analytic_account_id"]
    ):
        raise _invalid("analytic_account_id must be a positive integer.")
    if "reference" in values and not _is_nullable_bounded_text(
        values["reference"], 200
    ):
        raise _invalid("reference must be null or a trimmed 1-200 character string.")
    if "unit_amount" in values and _canonical_decimal(
        values["unit_amount"], signed=True
    ) is None:
        raise _invalid("unit_amount must be a canonical signed decimal string.")
    return dict(values)


def _validate_analytic_line_parameters(
    capability_id: str, parameters: Any
) -> dict[str, Any]:
    if capability_id == "analytic.line.create":
        normalized = _validate_analytic_line_values(parameters, partial=False)
        normalized.setdefault("reference", None)
        normalized.setdefault("unit_amount", "0")
        return normalized
    if capability_id == "analytic.line.update":
        if not isinstance(parameters, dict) or set(parameters) != {
            "analytic_line_id",
            "changes",
        }:
            raise _invalid("Analytic-line update parameters are invalid.")
        if not _valid_id(parameters["analytic_line_id"]):
            raise _invalid("parameters.analytic_line_id must be a positive integer.")
        return {
            "analytic_line_id": parameters["analytic_line_id"],
            "changes": _validate_analytic_line_values(
                parameters["changes"], partial=True
            ),
        }
    return _validate_single_id(parameters, "analytic_line_id")


def _validate_budget_fields(values: Any, *, partial: bool) -> dict[str, Any]:
    allowed = {"name", "date_from", "date_to", "budget_type"}
    if (
        not isinstance(values, dict)
        or (partial and (not values or not set(values) <= allowed))
        or (not partial and set(values) != allowed)
    ):
        raise _invalid("Budget parameters do not match the fixed contract.")
    if "name" in values and (
        not _is_bounded_text(values["name"], 200) or "[ODACV4:" in values["name"]
    ):
        raise _invalid(
            "name must be a trimmed business name without the reserved marker."
        )
    for field in ("date_from", "date_to"):
        if field in values and not _is_date(values[field]):
            raise _invalid(f"{field} must be a YYYY-MM-DD date.")
    if (
        "date_from" in values
        and "date_to" in values
        and values["date_from"] > values["date_to"]
    ):
        raise _invalid("date_from must not be after date_to.")
    if "budget_type" in values and values["budget_type"] not in {
        "revenue",
        "expense",
        "both",
    }:
        raise _invalid("budget_type contains an unsupported value.")
    return dict(values)


def _validate_budget_update_parameters(parameters: Any) -> dict[str, Any]:
    if not isinstance(parameters, dict) or set(parameters) != {"budget_id", "changes"}:
        raise _invalid("Budget-update parameters do not match the fixed contract.")
    if not _valid_id(parameters["budget_id"]):
        raise _invalid("parameters.budget_id must be a positive integer.")
    return {
        "budget_id": parameters["budget_id"],
        "changes": _validate_budget_fields(parameters["changes"], partial=True),
    }


def _validate_budget_line_replacement_parameters(
    parameters: Any,
) -> dict[str, Any]:
    if not isinstance(parameters, dict) or set(parameters) != {"budget_id", "lines"}:
        raise _invalid("Budget-line replacement parameters are invalid.")
    if not _valid_id(parameters["budget_id"]):
        raise _invalid("parameters.budget_id must be a positive integer.")
    lines = parameters["lines"]
    if not isinstance(lines, list) or not 1 <= len(lines) <= 200:
        raise _invalid("parameters.lines must contain between 1 and 200 lines.")
    normalized_lines: list[dict[str, Any]] = []
    for line in lines:
        if not isinstance(line, dict) or set(line) != {
            "budget_amount",
            "analytic_account_ids",
        }:
            raise _invalid("Each budget line must match the fixed contract.")
        if _decimal(line["budget_amount"], signed=True) is None:
            raise _invalid("budget_amount must be a signed decimal string.")
        analytic_account_ids = _validate_ids(line["analytic_account_ids"])
        if (
            analytic_account_ids is None
            or not 1 <= len(analytic_account_ids) <= 16
            or analytic_account_ids != sorted(analytic_account_ids)
        ):
            raise _invalid(
                "analytic_account_ids must contain 1 to 16 sorted unique IDs."
            )
        normalized_lines.append(
            {
                "budget_amount": line["budget_amount"],
                "analytic_account_ids": analytic_account_ids,
            }
        )
    return {"budget_id": parameters["budget_id"], "lines": normalized_lines}


def _validate_partner_values(values: Any, *, partial: bool) -> dict[str, Any]:
    required = {"name", "company_type"}
    text_limits = {
        "vat": 64,
        "reference": 128,
        "email": 320,
        "phone": 64,
        "mobile": 64,
        "street": 256,
        "street2": 256,
        "city": 256,
        "zip": 64,
    }
    optional = set(text_limits) | {"state_id", "country_id", "language"}
    allowed = required | optional
    if (
        not isinstance(values, dict)
        or (partial and (not values or not set(values) <= allowed))
        or (not partial and not (required <= set(values) <= allowed))
    ):
        raise _invalid("Partner parameters do not match the fixed contract.")
    if "name" in values and (
        not _is_bounded_text(values["name"], 256) or "[ODACV4:" in values["name"]
    ):
        raise _invalid(
            "name must be a trimmed business name without the reserved marker."
        )
    if "company_type" in values and (
        not isinstance(values["company_type"], str)
        or values["company_type"] not in {"person", "company"}
    ):
        raise _invalid("company_type must be 'person' or 'company'.")
    for field, maximum in text_limits.items():
        if field not in values:
            continue
        value = values[field]
        if partial and value is None:
            continue
        if not _is_bounded_text(value, maximum):
            raise _invalid(
                f"{field} must be null when clearing or a trimmed 1-{maximum} "
                "character string."
            )
        if field == "reference" and "[ODACV4:" in value:
            raise _invalid("reference must not contain the reserved marker.")
    for field in ("state_id", "country_id"):
        if field in values and not _valid_optional_id(values[field]):
            raise _invalid(f"{field} must be null or a positive integer.")
    if "language" in values and not (
        values["language"] is None or _is_bounded_text(values["language"], 16)
    ):
        raise _invalid("language must be null or a trimmed 1-16 character string.")
    normalized = dict(values)
    if not partial:
        for field in optional:
            normalized.setdefault(field, None)
    return normalized


def _validate_partner_create_parameters(parameters: Any) -> dict[str, Any]:
    return _validate_partner_values(parameters, partial=False)


def _validate_partner_update_parameters(parameters: Any) -> dict[str, Any]:
    if not isinstance(parameters, dict) or set(parameters) != {"partner_id", "changes"}:
        raise _invalid("Partner-update parameters do not match the fixed contract.")
    if not _valid_id(parameters["partner_id"]):
        raise _invalid("parameters.partner_id must be a positive integer.")
    return {
        "partner_id": parameters["partner_id"],
        "changes": _validate_partner_values(parameters["changes"], partial=True),
    }


def _validate_partner_accounting_update_parameters(parameters: Any) -> dict[str, Any]:
    if not isinstance(parameters, dict) or set(parameters) != {"partner_id", "changes"}:
        raise _invalid(
            "Partner-accounting update parameters do not match the fixed contract."
        )
    if not _valid_id(parameters["partner_id"]):
        raise _invalid("parameters.partner_id must be a positive integer.")
    changes = parameters["changes"]
    allowed = {
        "property_account_receivable_id",
        "property_account_payable_id",
        "property_account_position_id",
        "property_payment_term_id",
        "property_supplier_payment_term_id",
    }
    if not isinstance(changes, dict) or not changes or not set(changes) <= allowed:
        raise _invalid("parameters.changes contains no supported accounting update.")
    if any(not _valid_optional_id(value) for value in changes.values()):
        raise _invalid("Partner accounting values must be null or positive integers.")
    return {"partner_id": parameters["partner_id"], "changes": dict(changes)}


def _validate_partner_bank_create_parameters(parameters: Any) -> dict[str, Any]:
    required = {"partner_id", "account_number"}
    optional = {"account_holder_name", "bank_id", "currency_id"}
    if not isinstance(parameters, dict) or not (
        required <= set(parameters) <= required | optional
    ):
        raise _invalid("Partner bank-account creation parameters are invalid.")
    if not _valid_id(parameters["partner_id"]):
        raise _invalid("parameters.partner_id must be a positive integer.")
    if (
        not _is_bounded_text(parameters["account_number"], 128)
        or "[ODACV4:" in parameters["account_number"]
    ):
        raise _invalid(
            "parameters.account_number must be trimmed and omit the reserved marker."
        )
    holder = parameters.get("account_holder_name")
    if not (
        holder is None or (_is_bounded_text(holder, 256) and "[ODACV4:" not in holder)
    ):
        raise _invalid(
            "parameters.account_holder_name must be null or a trimmed business name."
        )
    for field in ("bank_id", "currency_id"):
        if field in parameters and not _valid_optional_id(parameters[field]):
            raise _invalid(f"parameters.{field} must be null or a positive integer.")
    normalized = dict(parameters)
    for field in optional:
        normalized.setdefault(field, None)
    return normalized


def _validate_partner_bank_update_parameters(parameters: Any) -> dict[str, Any]:
    if not isinstance(parameters, dict) or set(parameters) != {
        "partner_bank_id",
        "changes",
    }:
        raise _invalid("Partner bank-account update parameters are invalid.")
    if not _valid_id(parameters["partner_bank_id"]):
        raise _invalid("parameters.partner_bank_id must be a positive integer.")
    changes = parameters["changes"]
    allowed = {"account_number", "account_holder_name", "bank_id", "currency_id"}
    if not isinstance(changes, dict) or not changes or not set(changes) <= allowed:
        raise _invalid("parameters.changes contains no supported bank-account update.")
    if "account_number" in changes and (
        not _is_bounded_text(changes["account_number"], 128)
        or "[ODACV4:" in changes["account_number"]
    ):
        raise _invalid(
            "changes.account_number must be trimmed and omit the reserved marker."
        )
    if "account_holder_name" in changes:
        holder = changes["account_holder_name"]
        if not (
            holder is None
            or (_is_bounded_text(holder, 256) and "[ODACV4:" not in holder)
        ):
            raise _invalid(
                "changes.account_holder_name must be null or a trimmed business name."
            )
    for field in ("bank_id", "currency_id"):
        if field in changes and not _valid_optional_id(changes[field]):
            raise _invalid(f"changes.{field} must be null or a positive integer.")
    return {"partner_bank_id": parameters["partner_bank_id"], "changes": dict(changes)}


def _normalize_configuration_text(
    value: Any,
    *,
    field: str,
    maximum: int,
    uppercase: bool = False,
    pattern: re.Pattern[str] | None = None,
) -> str:
    if not isinstance(value, str):
        raise _invalid(f"{field} must be a string.")
    normalized = value.strip()
    if not 1 <= len(normalized) <= maximum or (
        pattern is not None and pattern.fullmatch(normalized) is None
    ):
        raise _invalid(f"{field} is outside the supported contract.")
    return normalized.upper() if uppercase else normalized


def _validate_account_configuration_values(
    values: Any, *, partial: bool
) -> dict[str, Any]:
    required = {"code", "name", "account_type"}
    optional = {"reconcile", "currency_id"}
    allowed = required | optional
    if (
        not isinstance(values, dict)
        or (partial and (not values or not set(values) <= allowed))
        or (not partial and not (required <= set(values) <= allowed))
    ):
        raise _invalid("Account parameters do not match the fixed contract.")
    normalized = dict(values)
    if "code" in normalized:
        normalized["code"] = _normalize_configuration_text(
            normalized["code"],
            field="code",
            maximum=64,
            pattern=re.compile(r"^[A-Za-z0-9.]+$"),
        )
    if "name" in normalized:
        normalized["name"] = _normalize_configuration_text(
            normalized["name"], field="name", maximum=256
        )
    if (
        "account_type" in normalized
        and normalized["account_type"] not in _ACCOUNT_TYPES
    ):
        raise _invalid("account_type is not supported.")
    if "reconcile" in normalized and not isinstance(normalized["reconcile"], bool):
        raise _invalid("reconcile must be a boolean.")
    if "currency_id" in normalized and not _valid_optional_id(
        normalized["currency_id"]
    ):
        raise _invalid("currency_id must be null or a positive integer.")
    receivable_payable = {"asset_receivable", "liability_payable"}
    if not partial:
        normalized.setdefault(
            "reconcile", normalized["account_type"] in receivable_payable
        )
        normalized.setdefault("currency_id", None)
        if (
            normalized["account_type"] in receivable_payable
            and not normalized["reconcile"]
        ):
            raise _invalid("Receivable and payable accounts must be reconcilable.")
    elif normalized.get("account_type") in receivable_payable:
        if normalized.get("reconcile") is False:
            raise _invalid(
                "Changing to a receivable or payable account requires reconcile=true."
            )
        normalized.setdefault("reconcile", True)
    return normalized


def _validate_account_configuration_update(parameters: Any) -> dict[str, Any]:
    if not isinstance(parameters, dict) or set(parameters) != {"account_id", "changes"}:
        raise _invalid("Account-update parameters do not match the fixed contract.")
    if not _valid_id(parameters["account_id"]):
        raise _invalid("parameters.account_id must be a positive integer.")
    return {
        "account_id": parameters["account_id"],
        "changes": _validate_account_configuration_values(
            parameters["changes"], partial=True
        ),
    }


def _validate_journal_configuration_values(
    values: Any, *, partial: bool
) -> dict[str, Any]:
    required = {"name", "code", "type"}
    mutable = {"name", "code", "sequence", "currency_id", "default_account_id"}
    allowed = required | mutable
    if (
        not isinstance(values, dict)
        or (partial and (not values or not set(values) <= mutable))
        or (not partial and not (required <= set(values) <= allowed))
    ):
        raise _invalid("Journal parameters do not match the fixed contract.")
    normalized = dict(values)
    if "name" in normalized:
        normalized["name"] = _normalize_configuration_text(
            normalized["name"], field="name", maximum=256
        )
    if "code" in normalized:
        normalized["code"] = _normalize_configuration_text(
            normalized["code"],
            field="code",
            maximum=5,
            uppercase=True,
            pattern=re.compile(r"^[A-Za-z0-9]+$"),
        )
    if "type" in normalized and normalized["type"] not in _JOURNAL_TYPES:
        raise _invalid("type is not a supported journal type.")
    if "sequence" in normalized and not (
        _is_integer(normalized["sequence"]) and normalized["sequence"] >= 0
    ):
        raise _invalid("sequence must be a nonnegative integer.")
    for field in ("currency_id", "default_account_id"):
        if field in normalized and not _valid_optional_id(normalized[field]):
            raise _invalid(f"{field} must be null or a positive integer.")
    if not partial:
        normalized.setdefault("sequence", None)
        normalized.setdefault("currency_id", None)
        normalized.setdefault("default_account_id", None)
    return normalized


def _validate_journal_configuration_update(parameters: Any) -> dict[str, Any]:
    if not isinstance(parameters, dict) or set(parameters) != {"journal_id", "changes"}:
        raise _invalid("Journal-update parameters do not match the fixed contract.")
    if not _valid_id(parameters["journal_id"]):
        raise _invalid("parameters.journal_id must be a positive integer.")
    return {
        "journal_id": parameters["journal_id"],
        "changes": _validate_journal_configuration_values(
            parameters["changes"], partial=True
        ),
    }


def _canonical_tax_amount(value: Any) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _invalid("amount must be a JSON number.")
    try:
        amount = Decimal(str(value))
    except InvalidOperation as exc:
        raise _invalid("amount must be a finite JSON number.") from exc
    if not amount.is_finite() or not Decimal(-1000000) <= amount <= Decimal(1000000):
        raise _invalid("amount must be between -1000000 and 1000000.")
    if amount == 0:
        return "0"
    text = format(amount, "f")
    canonical = text.rstrip("0").rstrip(".") if "." in text else text
    if "." in canonical and len(canonical.rsplit(".", 1)[1]) > 4:
        raise _invalid("amount must have at most four decimal places.")
    return canonical


def _validate_tax_configuration_values(values: Any, *, partial: bool) -> dict[str, Any]:
    required = {"name", "type_tax_use", "amount_type", "amount"}
    optional = {
        "sequence",
        "tax_group_id",
        "invoice_label",
        "price_include_override",
        "include_base_amount",
        "is_base_affected",
    }
    allowed = required | optional
    if (
        not isinstance(values, dict)
        or (partial and (not values or not set(values) <= allowed))
        or (not partial and not (required <= set(values) <= allowed))
    ):
        raise _invalid("Tax parameters do not match the fixed contract.")
    normalized = dict(values)
    if "name" in normalized:
        normalized["name"] = _normalize_configuration_text(
            normalized["name"], field="name", maximum=256
        )
    if "type_tax_use" in normalized and normalized["type_tax_use"] not in _TAX_USES:
        raise _invalid("type_tax_use is not supported.")
    if (
        "amount_type" in normalized
        and normalized["amount_type"] not in _TAX_AMOUNT_TYPES
    ):
        raise _invalid("amount_type is not supported.")
    if "amount" in normalized:
        normalized["amount"] = _canonical_tax_amount(normalized["amount"])
    if "sequence" in normalized and not (
        _is_integer(normalized["sequence"]) and normalized["sequence"] >= 0
    ):
        raise _invalid("sequence must be a nonnegative integer.")
    if "tax_group_id" in normalized and not _valid_optional_id(
        normalized["tax_group_id"]
    ):
        raise _invalid("tax_group_id must be null or a positive integer.")
    if "invoice_label" in normalized:
        label = normalized["invoice_label"]
        normalized["invoice_label"] = (
            None
            if label is None
            else _normalize_configuration_text(
                label, field="invoice_label", maximum=256
            )
        )
    if "price_include_override" in normalized and not (
        normalized["price_include_override"] is None
        or normalized["price_include_override"] in _PRICE_INCLUDE_OVERRIDES
    ):
        raise _invalid("price_include_override is not supported.")
    for field in ("include_base_amount", "is_base_affected"):
        if field in normalized and not isinstance(normalized[field], bool):
            raise _invalid(f"{field} must be a boolean.")
    if not partial:
        normalized.setdefault("sequence", None)
        normalized.setdefault("tax_group_id", None)
        normalized.setdefault("invoice_label", None)
        normalized.setdefault("price_include_override", None)
        normalized.setdefault("include_base_amount", False)
        normalized.setdefault("is_base_affected", True)
    return normalized


def _validate_tax_configuration_update(parameters: Any) -> dict[str, Any]:
    if not isinstance(parameters, dict) or set(parameters) != {"tax_id", "changes"}:
        raise _invalid("Tax-update parameters do not match the fixed contract.")
    if not _valid_id(parameters["tax_id"]):
        raise _invalid("parameters.tax_id must be a positive integer.")
    return {
        "tax_id": parameters["tax_id"],
        "changes": _validate_tax_configuration_values(
            parameters["changes"], partial=True
        ),
    }


_ACCOUNT_TAG_FIELDS = frozenset({"name", "applicability", "color", "country_id"})


def _validate_account_tag_values(values: Any, *, partial: bool) -> dict[str, Any]:
    if (
        not isinstance(values, dict)
        or (partial and (not values or not set(values) <= _ACCOUNT_TAG_FIELDS))
        or (not partial and set(values) != _ACCOUNT_TAG_FIELDS)
    ):
        raise _invalid("Account-tag parameters do not match the fixed contract.")
    normalized = dict(values)
    if "name" in normalized:
        normalized["name"] = _normalize_configuration_text(
            normalized["name"], field="name", maximum=256
        )
    if "applicability" in normalized and normalized["applicability"] not in {
        "accounts",
        "taxes",
        "products",
    }:
        raise _invalid("applicability is not supported.")
    if "color" in normalized and not (
        _is_integer(normalized["color"]) and normalized["color"] >= 0
    ):
        raise _invalid("color must be a nonnegative integer.")
    if "country_id" in normalized and not _valid_optional_id(normalized["country_id"]):
        raise _invalid("country_id must be null or a positive integer.")
    if (
        normalized.get("applicability") in {"accounts", "products"}
        and normalized.get("country_id") is not None
    ):
        raise _invalid("country_id must be null unless applicability is taxes.")
    return normalized


def _validate_account_tag_parameters(
    capability_id: str, parameters: Any
) -> dict[str, Any]:
    if capability_id == "account.tag.create":
        return _validate_account_tag_values(parameters, partial=False)
    if capability_id in {"account.tag.archive", "account.tag.restore"}:
        return _validate_single_id(parameters, "account_tag_id")
    if not isinstance(parameters, dict) or set(parameters) != {
        "account_tag_id",
        "changes",
    }:
        raise _invalid("Account-tag update parameters do not match the contract.")
    if not _valid_id(parameters["account_tag_id"]):
        raise _invalid("parameters.account_tag_id must be a positive integer.")
    return {
        "account_tag_id": parameters["account_tag_id"],
        "changes": _validate_account_tag_values(parameters["changes"], partial=True),
    }


_TAX_GROUP_FIELDS = frozenset({"name", "sequence", "preceding_subtotal"})


def _validate_tax_group_values(values: Any, *, partial: bool) -> dict[str, Any]:
    if (
        not isinstance(values, dict)
        or (partial and (not values or not set(values) <= _TAX_GROUP_FIELDS))
        or (not partial and set(values) != _TAX_GROUP_FIELDS)
    ):
        raise _invalid("Tax-group parameters do not match the fixed contract.")
    normalized = dict(values)
    if "name" in normalized:
        normalized["name"] = _normalize_configuration_text(
            normalized["name"], field="name", maximum=256
        )
    if "sequence" in normalized and not (
        _is_integer(normalized["sequence"]) and normalized["sequence"] >= 0
    ):
        raise _invalid("sequence must be a nonnegative integer.")
    if "preceding_subtotal" in normalized:
        subtotal = normalized["preceding_subtotal"]
        normalized["preceding_subtotal"] = (
            None
            if subtotal is None
            else _normalize_configuration_text(
                subtotal, field="preceding_subtotal", maximum=256
            )
        )
    return normalized


def _validate_tax_group_parameters(
    capability_id: str, parameters: Any
) -> dict[str, Any]:
    if capability_id == "tax.group.create":
        return _validate_tax_group_values(parameters, partial=False)
    if not isinstance(parameters, dict) or set(parameters) != {
        "tax_group_id",
        "changes",
    }:
        raise _invalid("Tax-group update parameters do not match the contract.")
    if not _valid_id(parameters["tax_group_id"]):
        raise _invalid("parameters.tax_group_id must be a positive integer.")
    return {
        "tax_group_id": parameters["tax_group_id"],
        "changes": _validate_tax_group_values(parameters["changes"], partial=True),
    }


_CASH_ROUNDING_FIELDS = frozenset(
    {
        "name",
        "rounding",
        "strategy",
        "rounding_method",
        "profit_account_id",
        "loss_account_id",
    }
)


def _validate_cash_rounding_values(values: Any, *, partial: bool) -> dict[str, Any]:
    if (
        not isinstance(values, dict)
        or (partial and (not values or not set(values) <= _CASH_ROUNDING_FIELDS))
        or (not partial and set(values) != _CASH_ROUNDING_FIELDS)
    ):
        raise _invalid("Cash-rounding parameters do not match the fixed contract.")
    normalized = dict(values)
    if "name" in normalized:
        normalized["name"] = _normalize_configuration_text(
            normalized["name"], field="name", maximum=256
        )
    if "rounding" in normalized:
        rounding = _canonical_decimal(normalized["rounding"], signed=False)
        if rounding is None or rounding <= 0:
            raise _invalid("rounding must be a canonical positive decimal.")
    if "strategy" in normalized and normalized["strategy"] not in {
        "biggest_tax",
        "add_invoice_line",
    }:
        raise _invalid("strategy is not supported.")
    if "rounding_method" in normalized and normalized["rounding_method"] not in {
        "UP",
        "DOWN",
        "HALF-UP",
    }:
        raise _invalid("rounding_method is not supported.")
    for field in ("profit_account_id", "loss_account_id"):
        if field in normalized and not _valid_optional_id(normalized[field]):
            raise _invalid(f"{field} must be null or a positive integer.")

    profit_present = "profit_account_id" in normalized
    loss_present = "loss_account_id" in normalized
    profit = normalized.get("profit_account_id")
    loss = normalized.get("loss_account_id")
    if profit_present and loss_present and (profit is None) != (loss is None):
        raise _invalid("Profit and loss accounts must be both set or both null.")
    if normalized.get("strategy") == "biggest_tax" and (
        profit is not None or loss is not None
    ):
        raise _invalid("biggest_tax requires both accounts to be null.")
    if normalized.get("strategy") == "add_invoice_line" and (
        (profit_present and profit is None) or (loss_present and loss is None)
    ):
        raise _invalid("add_invoice_line requires both accounts to be set.")
    return normalized


def _validate_cash_rounding_parameters(
    capability_id: str, parameters: Any
) -> dict[str, Any]:
    if capability_id == "cash_rounding.create":
        return _validate_cash_rounding_values(parameters, partial=False)
    if not isinstance(parameters, dict) or set(parameters) != {
        "cash_rounding_id",
        "changes",
    }:
        raise _invalid("Cash-rounding update parameters do not match the contract.")
    if not _valid_id(parameters["cash_rounding_id"]):
        raise _invalid("parameters.cash_rounding_id must be a positive integer.")
    return {
        "cash_rounding_id": parameters["cash_rounding_id"],
        "changes": _validate_cash_rounding_values(parameters["changes"], partial=True),
    }


_FISCAL_YEAR_FIELDS = frozenset({"name", "date_from", "date_to"})


def _validate_fiscal_year_values(values: Any, *, partial: bool) -> dict[str, Any]:
    if (
        not isinstance(values, dict)
        or (partial and (not values or not set(values) <= _FISCAL_YEAR_FIELDS))
        or (not partial and set(values) != _FISCAL_YEAR_FIELDS)
    ):
        raise _invalid("Fiscal-year parameters do not match the fixed contract.")
    normalized = dict(values)
    if "name" in normalized:
        normalized["name"] = _normalize_configuration_text(
            normalized["name"], field="name", maximum=256
        )
    for field in ("date_from", "date_to"):
        if field in normalized and not _is_date(normalized[field]):
            raise _invalid(f"{field} must be a YYYY-MM-DD date.")
    return normalized


def _validate_fiscal_year_parameters(
    capability_id: str, parameters: Any
) -> dict[str, Any]:
    if capability_id == "fiscal_year.create":
        return _validate_fiscal_year_values(parameters, partial=False)
    if not isinstance(parameters, dict) or set(parameters) != {
        "id",
        "changes",
    }:
        raise _invalid("Fiscal-year update parameters do not match the contract.")
    if not _valid_id(parameters["id"]):
        raise _invalid("parameters.id must be a positive integer.")
    return {
        "id": parameters["id"],
        "changes": _validate_fiscal_year_values(parameters["changes"], partial=True),
    }


_ANALYTIC_APPLICABILITY_FIELDS = frozenset(
    {
        "plan_id",
        "business_domain",
        "applicability",
        "account_prefix",
        "product_category_id",
    }
)


def _validate_analytic_applicability_values(
    values: Any, *, partial: bool
) -> dict[str, Any]:
    if (
        not isinstance(values, dict)
        or (
            partial
            and (not values or not set(values) <= _ANALYTIC_APPLICABILITY_FIELDS)
        )
        or (not partial and set(values) != _ANALYTIC_APPLICABILITY_FIELDS)
    ):
        raise _invalid(
            "Analytic-applicability parameters do not match the fixed contract."
        )
    normalized = dict(values)
    if "plan_id" in normalized and not _valid_id(normalized["plan_id"]):
        raise _invalid("plan_id must be a positive integer.")
    if "business_domain" in normalized and normalized["business_domain"] not in {
        "general",
        "invoice",
        "bill",
    }:
        raise _invalid("business_domain is not supported.")
    if "applicability" in normalized and normalized["applicability"] not in {
        "optional",
        "mandatory",
        "unavailable",
    }:
        raise _invalid("applicability is not supported.")
    if "account_prefix" in normalized:
        prefix = normalized["account_prefix"]
        normalized["account_prefix"] = (
            None
            if prefix is None
            else _normalize_configuration_text(
                prefix, field="account_prefix", maximum=64
            )
        )
    if "product_category_id" in normalized and not _valid_optional_id(
        normalized["product_category_id"]
    ):
        raise _invalid("product_category_id must be null or a positive integer.")
    return normalized


def _validate_analytic_applicability_parameters(
    capability_id: str, parameters: Any
) -> dict[str, Any]:
    if capability_id == "analytic.applicability.create":
        return _validate_analytic_applicability_values(parameters, partial=False)
    if not isinstance(parameters, dict) or set(parameters) != {
        "id",
        "changes",
    }:
        raise _invalid(
            "Analytic-applicability update parameters do not match the contract."
        )
    if not _valid_id(parameters["id"]):
        raise _invalid("parameters.id must be a positive integer.")
    return {
        "id": parameters["id"],
        "changes": _validate_analytic_applicability_values(
            parameters["changes"], partial=True
        ),
    }


_ANALYTIC_DISTRIBUTION_MODEL_FIELDS = frozenset(
    {
        "sequence",
        "account_prefix",
        "partner_id",
        "partner_category_id",
        "product_id",
        "product_category_id",
        "analytic_distribution",
    }
)


def _validate_analytic_distribution_model_values(
    values: Any, *, partial: bool
) -> dict[str, Any]:
    if (
        not isinstance(values, dict)
        or (
            partial
            and (not values or not set(values) <= _ANALYTIC_DISTRIBUTION_MODEL_FIELDS)
        )
        or (not partial and set(values) != _ANALYTIC_DISTRIBUTION_MODEL_FIELDS)
    ):
        raise _invalid(
            "Analytic-distribution-model parameters do not match the fixed contract."
        )
    normalized = dict(values)
    if "sequence" in normalized and not (
        _is_integer(normalized["sequence"]) and normalized["sequence"] >= 0
    ):
        raise _invalid("sequence must be a nonnegative integer.")
    if "account_prefix" in normalized:
        prefix = normalized["account_prefix"]
        normalized["account_prefix"] = (
            None
            if prefix is None
            else _normalize_configuration_text(
                prefix, field="account_prefix", maximum=64
            )
        )
    for field in (
        "partner_id",
        "partner_category_id",
        "product_id",
        "product_category_id",
    ):
        if field in normalized and not _valid_optional_id(normalized[field]):
            raise _invalid(f"{field} must be null or a positive integer.")
    if "analytic_distribution" in normalized:
        normalized["analytic_distribution"] = _validate_analytic_distribution(
            normalized["analytic_distribution"]
        )
        if not partial and normalized["analytic_distribution"] is None:
            raise _invalid("analytic_distribution must be nonempty for creation.")
    return normalized


def _validate_analytic_distribution_model_parameters(
    capability_id: str, parameters: Any
) -> dict[str, Any]:
    if capability_id == "analytic.distribution_model.create":
        return _validate_analytic_distribution_model_values(parameters, partial=False)
    if not isinstance(parameters, dict) or set(parameters) != {
        "id",
        "changes",
    }:
        raise _invalid(
            "Analytic-distribution-model update parameters do not match the contract."
        )
    if not _valid_id(parameters["id"]):
        raise _invalid("parameters.id must be a positive integer.")
    return {
        "id": parameters["id"],
        "changes": _validate_analytic_distribution_model_values(
            parameters["changes"], partial=True
        ),
    }


def _validate_currency_rate_parameters(parameters: Any) -> dict[str, Any]:
    if not isinstance(parameters, dict) or set(parameters) != {
        "currency_id",
        "date",
        "company_units_per_foreign_unit",
    }:
        raise _invalid("Currency-rate parameters do not match the fixed contract.")
    if not _valid_id(parameters["currency_id"]):
        raise _invalid("parameters.currency_id must be a positive integer.")
    if not _is_date(parameters["date"]):
        raise _invalid("parameters.date must be a YYYY-MM-DD date.")
    rate = _canonical_decimal(
        parameters["company_units_per_foreign_unit"], signed=False
    )
    if rate is None or rate <= 0:
        raise _invalid(
            "company_units_per_foreign_unit must be a canonical positive decimal."
        )
    return dict(parameters)


_ACCOUNT_GROUP_FIELDS = frozenset({"name", "code_prefix_start", "code_prefix_end"})


def _validate_account_group_values(values: Any, *, partial: bool) -> dict[str, Any]:
    if (
        not isinstance(values, dict)
        or (partial and (not values or not set(values) <= _ACCOUNT_GROUP_FIELDS))
        or (not partial and set(values) != _ACCOUNT_GROUP_FIELDS)
    ):
        raise _invalid("Account-group parameters do not match the fixed contract.")
    normalized = dict(values)
    if "name" in normalized:
        normalized["name"] = _normalize_configuration_text(
            normalized["name"], field="name", maximum=256
        )
    for field in ("code_prefix_start", "code_prefix_end"):
        if field in normalized:
            normalized[field] = _normalize_configuration_text(
                normalized[field], field=field, maximum=64
            )
    if {"code_prefix_start", "code_prefix_end"} <= set(normalized):
        start = normalized["code_prefix_start"]
        end = normalized["code_prefix_end"]
        if len(start) != len(end) or start > end:
            raise _invalid(
                "Account-group prefixes must have equal length and start at or "
                "before the end prefix."
            )
    return normalized


def _validate_account_group_parameters(
    capability_id: str, parameters: Any
) -> dict[str, Any]:
    if capability_id == "account.group.create":
        return _validate_account_group_values(parameters, partial=False)
    if not isinstance(parameters, dict) or set(parameters) != {
        "account_group_id",
        "changes",
    }:
        raise _invalid("Account-group update parameters do not match the contract.")
    if not _valid_id(parameters["account_group_id"]):
        raise _invalid("parameters.account_group_id must be a positive integer.")
    return {
        "account_group_id": parameters["account_group_id"],
        "changes": _validate_account_group_values(parameters["changes"], partial=True),
    }


_TAX_REPARTITION_LINE_FIELDS = frozenset(
    {
        "sequence",
        "repartition_type",
        "factor_percent",
        "account_id",
        "tag_ids",
        "use_in_tax_closing",
    }
)


def _tax_factor_total_matches(total: Decimal, expected: Decimal) -> bool:
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) == expected


def _validate_tax_repartition_lines(lines: Any, *, field: str) -> list[dict[str, Any]]:
    if not isinstance(lines, list) or not 2 <= len(lines) <= 100:
        raise _invalid(f"{field} must contain between 2 and 100 lines.")
    normalized: list[dict[str, Any]] = []
    factors: list[tuple[str, Decimal]] = []
    for line in lines:
        if not isinstance(line, dict) or set(line) != _TAX_REPARTITION_LINE_FIELDS:
            raise _invalid("Each tax repartition line must use the fixed fields.")
        if not (_is_integer(line["sequence"]) and line["sequence"] >= 0):
            raise _invalid("Tax repartition sequence must be nonnegative.")
        repartition_type = line["repartition_type"]
        if repartition_type not in {"base", "tax"}:
            raise _invalid("Tax repartition_type must be base or tax.")
        factor = _canonical_decimal(line["factor_percent"], signed=True)
        if factor is None:
            raise _invalid("factor_percent must be a canonical signed decimal.")
        if not _valid_optional_id(line["account_id"]):
            raise _invalid("Tax repartition account_id must be null or positive.")
        if repartition_type == "base" and line["account_id"] is not None:
            raise _invalid("Base repartition lines cannot specify account_id.")
        tag_ids = _validate_ids(line["tag_ids"])
        if tag_ids is None:
            raise _invalid("Tax repartition tag_ids must contain unique positive IDs.")
        if not isinstance(line["use_in_tax_closing"], bool):
            raise _invalid("use_in_tax_closing must be a boolean.")
        normalized.append({**line, "tag_ids": sorted(tag_ids)})
        factors.append((repartition_type, factor))

    base_count = sum(kind == "base" for kind, _ in factors)
    tax_factors = [factor for kind, factor in factors if kind == "tax"]
    if base_count != 1 or not tax_factors:
        raise _invalid(
            "Each repartition side requires exactly one base and at least one tax line."
        )
    positive_total = sum((factor for factor in tax_factors if factor > 0), Decimal(0))
    negative_total = sum((factor for factor in tax_factors if factor < 0), Decimal(0))
    if not _tax_factor_total_matches(positive_total, Decimal("100.00")) or (
        negative_total
        and not _tax_factor_total_matches(negative_total, Decimal("-100.00"))
    ):
        raise _invalid(
            "Positive tax factors must total 100 and negative tax factors, when "
            "present, must total -100."
        )
    return normalized


def _validate_tax_repartition_replacement(parameters: Any) -> dict[str, Any]:
    if not isinstance(parameters, dict) or set(parameters) != {
        "tax_id",
        "invoice_lines",
        "refund_lines",
    }:
        raise _invalid(
            "Tax repartition replacement parameters do not match the fixed contract."
        )
    if not _valid_id(parameters["tax_id"]):
        raise _invalid("parameters.tax_id must be a positive integer.")
    invoice_lines = _validate_tax_repartition_lines(
        parameters["invoice_lines"], field="invoice_lines"
    )
    refund_lines = _validate_tax_repartition_lines(
        parameters["refund_lines"], field="refund_lines"
    )
    if len(invoice_lines) != len(refund_lines) or any(
        invoice["repartition_type"] != refund["repartition_type"]
        or invoice["factor_percent"] != refund["factor_percent"]
        for invoice, refund in zip(invoice_lines, refund_lines, strict=True)
    ):
        raise _invalid(
            "Invoice and refund repartition lines must have matching ordered "
            "types and factors."
        )
    return {
        "tax_id": parameters["tax_id"],
        "invoice_lines": invoice_lines,
        "refund_lines": refund_lines,
    }


_RECONCILIATION_MODEL_FIELDS = frozenset(
    {
        "name",
        "sequence",
        "trigger",
        "match_journal_ids",
        "match_partner_ids",
        "match_amount",
        "match_label",
    }
)
_RECONCILIATION_AMOUNT_OPERATORS = frozenset({"lower", "greater", "between"})
_RECONCILIATION_LABEL_OPERATORS = frozenset({"contains", "not_contains", "match_regex"})


def _validate_reconciliation_match_amount(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != {
        "operator",
        "minimum",
        "maximum",
    }:
        raise _invalid("match_amount must be null or use the fixed amount fields.")
    operator = value["operator"]
    if operator not in _RECONCILIATION_AMOUNT_OPERATORS:
        raise _invalid("match_amount.operator is unsupported.")
    minimum = (
        None
        if value["minimum"] is None
        else _canonical_decimal(value["minimum"], signed=False)
    )
    maximum = (
        None
        if value["maximum"] is None
        else _canonical_decimal(value["maximum"], signed=False)
    )
    if (value["minimum"] is not None and minimum is None) or (
        value["maximum"] is not None and maximum is None
    ):
        raise _invalid("match_amount bounds must be canonical nonnegative decimals.")
    valid_bounds = (
        operator == "lower"
        and minimum is None
        and maximum is not None
        or operator == "greater"
        and minimum is not None
        and maximum is None
        or operator == "between"
        and minimum is not None
        and maximum is not None
        and minimum <= maximum
    )
    if not valid_bounds:
        raise _invalid("match_amount bounds do not match its operator.")
    return dict(value)


def _validate_reconciliation_match_label(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != {"operator", "value"}:
        raise _invalid("match_label must be null or use the fixed label fields.")
    operator = value["operator"]
    if operator not in _RECONCILIATION_LABEL_OPERATORS:
        raise _invalid("match_label.operator is unsupported.")
    normalized_value = _normalize_configuration_text(
        value["value"], field="match_label.value", maximum=500
    )
    if operator == "match_regex":
        try:
            re.compile(normalized_value)
        except re.error as exc:
            raise _invalid(
                "match_label.value must be a valid regular expression."
            ) from exc
    return {"operator": operator, "value": normalized_value}


def _validate_reconciliation_model_values(
    values: Any, *, partial: bool
) -> dict[str, Any]:
    if (
        not isinstance(values, dict)
        or (partial and (not values or not set(values) <= _RECONCILIATION_MODEL_FIELDS))
        or (not partial and set(values) != _RECONCILIATION_MODEL_FIELDS)
    ):
        raise _invalid(
            "Reconciliation-model parameters do not match the fixed contract."
        )
    normalized = dict(values)
    if "name" in normalized:
        normalized["name"] = _normalize_configuration_text(
            normalized["name"], field="name", maximum=256
        )
    if "sequence" in normalized and not (
        _is_integer(normalized["sequence"]) and normalized["sequence"] >= 0
    ):
        raise _invalid("sequence must be a nonnegative integer.")
    if "trigger" in normalized and normalized["trigger"] not in {
        "manual",
        "auto_reconcile",
    }:
        raise _invalid("trigger must be manual or auto_reconcile.")
    for field in ("match_journal_ids", "match_partner_ids"):
        if field in normalized:
            identifiers = _validate_ids(normalized[field])
            if identifiers is None:
                raise _invalid(f"{field} must contain unique positive integers.")
            normalized[field] = sorted(identifiers)
    if "match_amount" in normalized:
        normalized["match_amount"] = _validate_reconciliation_match_amount(
            normalized["match_amount"]
        )
    if "match_label" in normalized:
        normalized["match_label"] = _validate_reconciliation_match_label(
            normalized["match_label"]
        )
    return normalized


def _validate_reconciliation_analytic_distribution(
    value: Any,
) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not 1 <= len(value) <= 16:
        raise _invalid("analytic_distribution must contain between 1 and 16 entries.")
    normalized: list[dict[str, Any]] = []
    used_accounts: set[int] = set()
    for entry in value:
        if not isinstance(entry, dict) or set(entry) != {
            "analytic_account_ids",
            "percentage",
        }:
            raise _invalid("Analytic distribution entries must use the fixed fields.")
        account_ids = _validate_ids(entry["analytic_account_ids"])
        if (
            account_ids is None
            or not 1 <= len(account_ids) <= 16
            or used_accounts.intersection(account_ids)
        ):
            raise _invalid(
                "analytic_account_ids must be nonempty, unique across entries, "
                "positive integers."
            )
        percentage = _canonical_decimal(entry["percentage"], signed=False)
        decimal_places = (
            max(0, -percentage.as_tuple().exponent) if percentage is not None else 0
        )
        if (
            percentage is None
            or percentage <= 0
            or percentage > 100
            or decimal_places > 4
        ):
            raise _invalid(
                "Analytic percentages must be canonical values above 0 and at "
                "most 100 with up to four decimal places."
            )
        sorted_ids = sorted(account_ids)
        used_accounts.update(sorted_ids)
        normalized.append(
            {"analytic_account_ids": sorted_ids, "percentage": entry["percentage"]}
        )
    return sorted(normalized, key=lambda item: tuple(item["analytic_account_ids"]))


def _validate_reconciliation_model_lines(parameters: Any) -> dict[str, Any]:
    if not isinstance(parameters, dict) or set(parameters) != {
        "reconciliation_model_id",
        "lines",
    }:
        raise _invalid(
            "Reconciliation-model line parameters do not match the fixed contract."
        )
    if not _valid_id(parameters["reconciliation_model_id"]):
        raise _invalid("parameters.reconciliation_model_id must be positive.")
    lines = parameters["lines"]
    if not isinstance(lines, list) or len(lines) > 100:
        raise _invalid("parameters.lines must contain at most 100 lines.")
    required = {
        "sequence",
        "account_id",
        "partner_id",
        "label",
        "amount_type",
        "amount_string",
        "tax_ids",
    }
    allowed = required | {"analytic_distribution"}
    normalized_lines: list[dict[str, Any]] = []
    for line in lines:
        if not isinstance(line, dict) or not required <= set(line) <= allowed:
            raise _invalid("Each reconciliation-model line must use the fixed fields.")
        if not (_is_integer(line["sequence"]) and line["sequence"] >= 0):
            raise _invalid("Reconciliation-model line sequence must be nonnegative.")
        for field in ("account_id", "partner_id"):
            if not _valid_optional_id(line[field]):
                raise _invalid(
                    f"Reconciliation-model {field} must be null or positive."
                )
        label = line["label"]
        normalized_label = (
            None
            if label is None
            else _normalize_configuration_text(label, field="label", maximum=500)
        )
        amount_type = line["amount_type"]
        if amount_type not in {
            "fixed",
            "percentage",
            "percentage_st_line",
            "regex",
        }:
            raise _invalid("Reconciliation-model amount_type is unsupported.")
        amount_string = line["amount_string"]
        if amount_type == "regex":
            normalized_amount = _normalize_configuration_text(
                amount_string, field="amount_string", maximum=500
            )
            try:
                re.compile(normalized_amount)
            except re.error as exc:
                raise _invalid(
                    "amount_string must be a valid regular expression."
                ) from exc
        else:
            amount = _canonical_decimal(amount_string, signed=True)
            if (
                amount is None
                or amount == 0
                or (amount_type == "percentage" and not 0 < amount <= 100)
            ):
                raise _invalid(
                    "Numeric amount_string must be canonical and nonzero; balance "
                    "percentages must be above 0 and at most 100."
                )
            normalized_amount = amount_string
        tax_ids = _validate_ids(line["tax_ids"])
        if tax_ids is None:
            raise _invalid("Reconciliation-model tax_ids must contain unique IDs.")
        normalized_line = {
            **line,
            "label": normalized_label,
            "amount_string": normalized_amount,
            "tax_ids": sorted(tax_ids),
        }
        if "analytic_distribution" in line:
            normalized_line["analytic_distribution"] = (
                _validate_reconciliation_analytic_distribution(
                    line["analytic_distribution"]
                )
            )
        normalized_lines.append(normalized_line)
    return {
        "reconciliation_model_id": parameters["reconciliation_model_id"],
        "lines": normalized_lines,
    }


def _validate_reconciliation_model_parameters(
    capability_id: str, parameters: Any
) -> dict[str, Any]:
    if capability_id == "reconciliation.model.create":
        return _validate_reconciliation_model_values(parameters, partial=False)
    if capability_id == "reconciliation.model.update":
        if not isinstance(parameters, dict) or set(parameters) != {
            "reconciliation_model_id",
            "changes",
        }:
            raise _invalid(
                "Reconciliation-model update parameters do not match the contract."
            )
        if not _valid_id(parameters["reconciliation_model_id"]):
            raise _invalid("parameters.reconciliation_model_id must be positive.")
        return {
            "reconciliation_model_id": parameters["reconciliation_model_id"],
            "changes": _validate_reconciliation_model_values(
                parameters["changes"], partial=True
            ),
        }
    if capability_id == "reconciliation.model.lines.replace":
        return _validate_reconciliation_model_lines(parameters)
    return _validate_single_id(parameters, "reconciliation_model_id")


_FISCAL_POSITION_FIELDS = frozenset(
    {
        "name",
        "sequence",
        "auto_apply",
        "vat_required",
        "country_id",
        "country_group_id",
        "state_ids",
        "zip_from",
        "zip_to",
        "note",
    }
)


def _validate_fiscal_position_values(values: Any, *, partial: bool) -> dict[str, Any]:
    if (
        not isinstance(values, dict)
        or not values
        or not set(values) <= _FISCAL_POSITION_FIELDS
    ):
        raise _invalid("Fiscal-position parameters do not match the fixed contract.")
    if not partial and "name" not in values:
        raise _invalid("Fiscal-position creation requires name.")
    normalized = dict(values)
    if "name" in normalized:
        normalized["name"] = _normalize_configuration_text(
            normalized["name"], field="name", maximum=256
        )
    if "sequence" in normalized and not (
        _is_integer(normalized["sequence"]) and normalized["sequence"] >= 0
    ):
        raise _invalid("sequence must be a nonnegative integer.")
    for field in ("auto_apply", "vat_required"):
        if field in normalized and not isinstance(normalized[field], bool):
            raise _invalid(f"{field} must be a boolean.")
    for field in ("country_id", "country_group_id"):
        if field in normalized and not _valid_optional_id(normalized[field]):
            raise _invalid(f"{field} must be null or a positive integer.")
    if "state_ids" in normalized:
        state_ids = _validate_ids(normalized["state_ids"])
        if state_ids is None:
            raise _invalid("state_ids must contain distinct positive integers.")
        normalized["state_ids"] = sorted(state_ids)
    for field in ("zip_from", "zip_to", "note"):
        if field in normalized:
            value = normalized[field]
            normalized[field] = (
                None
                if value is None
                else _normalize_configuration_text(value, field=field, maximum=5000)
            )
    return normalized


def _validate_fiscal_position_parameters(
    capability_id: str, parameters: Any
) -> dict[str, Any]:
    if capability_id == "fiscal_position.create":
        return _validate_fiscal_position_values(parameters, partial=False)
    if capability_id == "fiscal_position.update":
        if not isinstance(parameters, dict) or set(parameters) != {
            "fiscal_position_id",
            "changes",
        }:
            raise _invalid(
                "Fiscal-position update parameters do not match the fixed contract."
            )
        if not _valid_id(parameters["fiscal_position_id"]):
            raise _invalid("parameters.fiscal_position_id must be a positive integer.")
        return {
            "fiscal_position_id": parameters["fiscal_position_id"],
            "changes": _validate_fiscal_position_values(
                parameters["changes"], partial=True
            ),
        }
    if capability_id == "fiscal_position.account_mappings.replace":
        if not isinstance(parameters, dict) or set(parameters) != {
            "fiscal_position_id",
            "mappings",
        }:
            raise _invalid(
                "Fiscal-position mapping parameters do not match the fixed contract."
            )
        if not _valid_id(parameters["fiscal_position_id"]) or not isinstance(
            parameters["mappings"], list
        ):
            raise _invalid("Fiscal-position mapping parameters are invalid.")
        mappings = []
        sources = set()
        for mapping in parameters["mappings"]:
            if not isinstance(mapping, dict) or set(mapping) != {
                "source_account_id",
                "destination_account_id",
            }:
                raise _invalid("Each account mapping must use the fixed fields.")
            source = mapping["source_account_id"]
            destination = mapping["destination_account_id"]
            if (
                not _valid_id(source)
                or not _valid_id(destination)
                or source == destination
                or source in sources
            ):
                raise _invalid(
                    "Account mappings require unique, distinct positive account IDs."
                )
            sources.add(source)
            mappings.append(dict(mapping))
        return {
            "fiscal_position_id": parameters["fiscal_position_id"],
            "mappings": sorted(mappings, key=lambda item: item["source_account_id"]),
        }
    return _validate_single_id(parameters, "fiscal_position_id")


def _validate_journal_group_parameters(
    capability_id: str, parameters: Any
) -> dict[str, Any]:
    if capability_id == "journal.group.create":
        if (
            not isinstance(parameters, dict)
            or "name" not in parameters
            or not set(parameters) <= {"name", "sequence", "excluded_journal_ids"}
        ):
            raise _invalid(
                "Journal-group creation parameters do not match the fixed contract."
            )
        values = dict(parameters)
    else:
        if (
            not isinstance(parameters, dict)
            or set(parameters) != {"journal_group_id", "changes"}
            or not _valid_id(parameters["journal_group_id"])
        ):
            raise _invalid(
                "Journal-group update parameters do not match the fixed contract."
            )
        if (
            not isinstance(parameters["changes"], dict)
            or not parameters["changes"]
            or not set(parameters["changes"])
            <= {"name", "sequence", "excluded_journal_ids"}
        ):
            raise _invalid("Journal-group changes do not match the fixed contract.")
        values = dict(parameters["changes"])
    if "name" in values:
        values["name"] = _normalize_configuration_text(
            values["name"], field="name", maximum=256
        )
    if "sequence" in values and not (
        _is_integer(values["sequence"]) and values["sequence"] >= 0
    ):
        raise _invalid("sequence must be a nonnegative integer.")
    if "excluded_journal_ids" in values:
        journal_ids = _validate_ids(values["excluded_journal_ids"])
        if journal_ids is None:
            raise _invalid(
                "excluded_journal_ids must contain distinct positive integers."
            )
        values["excluded_journal_ids"] = sorted(journal_ids)
    return (
        values
        if capability_id == "journal.group.create"
        else {"journal_group_id": parameters["journal_group_id"], "changes": values}
    )


def _validate_asset_create_parameters(parameters: Any) -> dict[str, Any]:
    expected = {
        "name",
        "acquisition_date",
        "original_value",
        "salvage_value",
        "account_asset_id",
        "account_depreciation_id",
        "account_depreciation_expense_id",
        "journal_id",
        "method",
        "method_number",
        "method_period",
        "method_progress_factor",
        "prorata_computation_type",
    }
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise _invalid("Asset creation parameters do not match the fixed contract.")
    if (
        not _is_bounded_text(parameters["name"], _ASSET_BASE_NAME_MAXIMUM)
        or "[ODACV4:" in parameters["name"]
    ):
        raise _invalid(
            "parameters.name must be a bounded business name without the reserved marker."
        )
    if not _is_date(parameters["acquisition_date"]):
        raise _invalid("parameters.acquisition_date must be a YYYY-MM-DD date.")
    original_value = _decimal(parameters["original_value"], signed=False)
    salvage_value = _decimal(parameters["salvage_value"], signed=False)
    if original_value is None or original_value <= 0:
        raise _invalid("parameters.original_value must be a positive decimal string.")
    if salvage_value is None or salvage_value > original_value:
        raise _invalid(
            "parameters.salvage_value must be between zero and original_value."
        )
    for key in (
        "account_asset_id",
        "account_depreciation_id",
        "account_depreciation_expense_id",
        "journal_id",
    ):
        if not _valid_id(parameters[key]):
            raise _invalid(f"parameters.{key} must be a positive integer.")
    if parameters["method"] not in _ASSET_METHODS:
        raise _invalid("parameters.method is not a supported Odoo asset method.")
    if (
        not _is_integer(parameters["method_number"])
        or not 1 <= parameters["method_number"] <= 1200
    ):
        raise _invalid("parameters.method_number must be between 1 and 1200.")
    if parameters["method_period"] not in {"1", "12"}:
        raise _invalid("parameters.method_period must be '1' or '12'.")
    progress_factor = _decimal(parameters["method_progress_factor"], signed=False)
    if progress_factor is None or not Decimal(0) < progress_factor <= Decimal(1):
        raise _invalid(
            "parameters.method_progress_factor must be greater than zero and at most one."
        )
    if parameters["prorata_computation_type"] not in _ASSET_PRORATA_TYPES:
        raise _invalid(
            "parameters.prorata_computation_type is not a supported Odoo value."
        )
    return dict(parameters)


def _validate_asset_lifecycle_parameters(
    capability_id: str, parameters: Any
) -> dict[str, Any]:
    if capability_id == "asset.cancel":
        return _validate_single_id(parameters, "asset_id")
    expected = {"asset_id", "date", "note"}
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise _invalid("Asset lifecycle parameters do not match the fixed contract.")
    if not _valid_id(parameters["asset_id"]):
        raise _invalid("parameters.asset_id must be a positive integer.")
    if not _is_date(parameters["date"]):
        raise _invalid("parameters.date must be a YYYY-MM-DD date.")
    if not (parameters["note"] is None or _is_bounded_text(parameters["note"], 200)):
        raise _invalid("parameters.note must be null or a bounded non-empty string.")
    return dict(parameters)


def _validate_deferred_generation_parameters(parameters: Any) -> dict[str, Any]:
    if (
        not isinstance(parameters, dict)
        or set(parameters) != {"date_to"}
        or not _is_date(parameters["date_to"])
    ):
        raise _invalid("Deferred-generation parameters require one date_to date.")
    parsed = date.fromisoformat(parameters["date_to"])
    if parsed.day != calendar.monthrange(parsed.year, parsed.month)[1]:
        raise _invalid("parameters.date_to must be the last day of a month.")
    return dict(parameters)


def _validate_revaluation_parameters(parameters: Any) -> dict[str, Any]:
    expected = {
        "date",
        "reversal_date",
        "journal_id",
        "expense_provision_account_id",
        "income_provision_account_id",
    }
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise _invalid("Revaluation parameters do not match the fixed contract.")
    if not _is_date(parameters["date"]) or not _is_date(parameters["reversal_date"]):
        raise _invalid("Revaluation dates must use YYYY-MM-DD syntax.")
    if parameters["reversal_date"] <= parameters["date"]:
        raise _invalid("parameters.reversal_date must be after parameters.date.")
    for key in (
        "journal_id",
        "expense_provision_account_id",
        "income_provision_account_id",
    ):
        if not _valid_id(parameters[key]):
            raise _invalid(f"parameters.{key} must be a positive integer.")
    return dict(parameters)


def _validate_automatic_reconciliation_parameters(
    parameters: Any,
) -> dict[str, Any]:
    if not isinstance(parameters, dict) or set(parameters) != {"line_ids"}:
        raise _invalid("Automatic-reconciliation parameters are invalid.")
    line_ids = _validate_ids(parameters["line_ids"])
    if line_ids is None or not 2 <= len(line_ids) <= 200:
        raise _invalid(
            "parameters.line_ids must contain 2 to 200 distinct positive integers."
        )
    return {"line_ids": sorted(line_ids)}


def _validate_order_lines(capability_id: str, lines: Any) -> list[dict[str, Any]]:
    if not isinstance(lines, list) or not 1 <= len(lines) <= 200:
        raise _invalid("parameters.lines must contain between 1 and 200 lines.")
    purchase = capability_id.startswith("purchase.order.")
    expected = {
        "product_id",
        "name",
        "quantity",
        "uom_id",
        "price_unit",
        "discount",
        "tax_ids",
    } | ({"date_planned"} if purchase else set())
    normalized: list[dict[str, Any]] = []
    for line in lines:
        if not isinstance(line, dict) or set(line) != expected:
            raise _invalid("Each order line must match the fixed line contract.")
        if not _valid_id(line["product_id"]):
            raise _invalid("Order line product_id must be a positive integer.")
        if not _valid_id(line["uom_id"]):
            raise _invalid("Order line uom_id must be a positive integer.")
        if not _is_bounded_text(line["name"], 500):
            raise _invalid("Order line names must be bounded non-empty strings.")
        quantity = _canonical_decimal(line["quantity"], signed=False)
        if quantity is None or quantity <= 0:
            raise _invalid("Order line quantity must be a canonical positive decimal.")
        price_unit = _canonical_decimal(line["price_unit"], signed=False)
        if price_unit is None:
            raise _invalid(
                "Order line price_unit must be a canonical nonnegative decimal."
            )
        discount = _canonical_decimal(line["discount"], signed=False)
        if discount is None or discount > 100:
            raise _invalid("Order line discount must be between 0 and 100.")
        tax_ids = _validate_ids(line["tax_ids"])
        if tax_ids is None or tax_ids != sorted(tax_ids):
            raise _invalid(
                "Order line tax_ids must be sorted unique positive integers."
            )
        if purchase and not _is_datetime(line["date_planned"]):
            raise _invalid(
                "Purchase order line date_planned must use YYYY-MM-DD HH:MM:SS."
            )
        normalized.append({**line, "tax_ids": tax_ids})
    return normalized


def _validate_order_create_parameters(
    capability_id: str, parameters: Any
) -> dict[str, Any]:
    sale = capability_id == "sale.order.create"
    expected = (
        {
            "partner_id",
            "pricelist_id",
            "date_order",
            "client_order_ref",
            "validity_date",
            "commitment_date",
            "payment_term_id",
            "lines",
        }
        if sale
        else {
            "partner_id",
            "currency_id",
            "picking_type_id",
            "date_order",
            "partner_ref",
            "payment_term_id",
            "incoterm_id",
            "lines",
        }
    )
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise _invalid("Order creation parameters do not match the fixed contract.")
    for field in (
        ("partner_id", "pricelist_id")
        if sale
        else ("partner_id", "currency_id", "picking_type_id")
    ):
        if not _valid_id(parameters[field]):
            raise _invalid(f"parameters.{field} must be a positive integer.")
    if not _is_datetime(parameters["date_order"]):
        raise _invalid("parameters.date_order must use YYYY-MM-DD HH:MM:SS.")
    if not _valid_optional_id(parameters["payment_term_id"]):
        raise _invalid("parameters.payment_term_id must be null or a positive integer.")
    if sale:
        if not _is_nullable_bounded_text(parameters["client_order_ref"], 200):
            raise _invalid(
                "parameters.client_order_ref must be null or a bounded non-empty string."
            )
        if not (
            parameters["validity_date"] is None or _is_date(parameters["validity_date"])
        ):
            raise _invalid("parameters.validity_date must be null or a date.")
        if not (
            parameters["commitment_date"] is None
            or _is_datetime(parameters["commitment_date"])
        ):
            raise _invalid(
                "parameters.commitment_date must be null or an Odoo datetime."
            )
    else:
        if not _is_nullable_bounded_text(parameters["partner_ref"], 200):
            raise _invalid(
                "parameters.partner_ref must be null or a bounded non-empty string."
            )
        if not _valid_optional_id(parameters["incoterm_id"]):
            raise _invalid("parameters.incoterm_id must be null or a positive integer.")
    return {
        **parameters,
        "lines": _validate_order_lines(capability_id, parameters["lines"]),
    }


def _validate_order_update_parameters(
    capability_id: str, parameters: Any
) -> dict[str, Any]:
    if not isinstance(parameters, dict) or set(parameters) != {"order_id", "changes"}:
        raise _invalid("Order update parameters do not match the fixed contract.")
    if not _valid_id(parameters["order_id"]):
        raise _invalid("parameters.order_id must be a positive integer.")
    changes = parameters["changes"]
    sale = capability_id == "sale.order.update_draft"
    allowed = (
        {"client_order_ref", "validity_date", "commitment_date", "payment_term_id"}
        if sale
        else {"partner_ref", "date_order", "payment_term_id", "incoterm_id"}
    )
    if not isinstance(changes, dict) or not changes or not set(changes) <= allowed:
        raise _invalid("parameters.changes contains no supported order update.")
    reference_field = "client_order_ref" if sale else "partner_ref"
    if reference_field in changes and not _is_nullable_bounded_text(
        changes[reference_field], 200
    ):
        raise _invalid(
            f"changes.{reference_field} must be null or a bounded non-empty string."
        )
    if "payment_term_id" in changes and not _valid_optional_id(
        changes["payment_term_id"]
    ):
        raise _invalid("changes.payment_term_id must be null or a positive integer.")
    if sale:
        if "validity_date" in changes and not (
            changes["validity_date"] is None or _is_date(changes["validity_date"])
        ):
            raise _invalid("changes.validity_date must be null or a date.")
        if "commitment_date" in changes and not (
            changes["commitment_date"] is None
            or _is_datetime(changes["commitment_date"])
        ):
            raise _invalid("changes.commitment_date must be null or an Odoo datetime.")
    else:
        if "date_order" in changes and not _is_datetime(changes["date_order"]):
            raise _invalid("changes.date_order must use YYYY-MM-DD HH:MM:SS.")
        if "incoterm_id" in changes and not _valid_optional_id(changes["incoterm_id"]):
            raise _invalid("changes.incoterm_id must be null or a positive integer.")
    return {"order_id": parameters["order_id"], "changes": dict(changes)}


def _validate_order_line_replacement_parameters(
    capability_id: str, parameters: Any
) -> dict[str, Any]:
    if not isinstance(parameters, dict) or set(parameters) != {"order_id", "lines"}:
        raise _invalid(
            "Order-line replacement parameters do not match the fixed contract."
        )
    if not _valid_id(parameters["order_id"]):
        raise _invalid("parameters.order_id must be a positive integer.")
    return {
        "order_id": parameters["order_id"],
        "lines": _validate_order_lines(capability_id, parameters["lines"]),
    }


def _validate_stock_transfer_create_parameters(parameters: Any) -> dict[str, Any]:
    expected = {
        "picking_type_id",
        "location_id",
        "location_dest_id",
        "partner_id",
        "scheduled_date",
        "origin",
        "moves",
    }
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise _invalid("Stock-transfer creation parameters are invalid.")
    for field in ("picking_type_id", "location_id", "location_dest_id"):
        if not _valid_id(parameters[field]):
            raise _invalid(f"parameters.{field} must be a positive integer.")
    if parameters["location_id"] == parameters["location_dest_id"]:
        raise _invalid("Stock-transfer source and destination locations must differ.")
    if not _valid_optional_id(parameters["partner_id"]):
        raise _invalid("parameters.partner_id must be null or a positive integer.")
    if not (
        parameters["scheduled_date"] is None
        or _is_datetime(parameters["scheduled_date"])
    ):
        raise _invalid(
            "parameters.scheduled_date must be null or use YYYY-MM-DD HH:MM:SS."
        )
    if not _is_nullable_bounded_text(parameters["origin"], 200):
        raise _invalid("parameters.origin must be null or a bounded non-empty string.")
    if parameters["origin"] is not None and "ODACV4" in parameters["origin"]:
        raise _invalid("parameters.origin contains a reserved marker.")
    moves = parameters["moves"]
    if not isinstance(moves, list) or not 1 <= len(moves) <= 200:
        raise _invalid("parameters.moves must contain between 1 and 200 moves.")
    normalized_moves: list[dict[str, Any]] = []
    for move in moves:
        if not isinstance(move, dict) or set(move) != {
            "product_id",
            "name",
            "quantity",
            "uom_id",
        }:
            raise _invalid("Each stock move must match the fixed move contract.")
        if not _valid_id(move["product_id"]):
            raise _invalid("Stock move product_id must be a positive integer.")
        if not _valid_id(move["uom_id"]):
            raise _invalid("Stock move uom_id must be a positive integer.")
        if not _is_bounded_text(move["name"], 500):
            raise _invalid("Stock move names must be bounded non-empty strings.")
        quantity = _canonical_decimal(move["quantity"], signed=False)
        if quantity is None or quantity <= 0:
            raise _invalid("Stock move quantity must be a canonical positive decimal.")
        normalized_moves.append(dict(move))
    return {**parameters, "moves": normalized_moves}


def _validate_stock_transfer_parameters(
    capability_id: str, parameters: Any
) -> dict[str, Any]:
    if capability_id == "stock.transfer.create":
        return _validate_stock_transfer_create_parameters(parameters)
    if capability_id == "stock.transfer.quantities.set":
        if not isinstance(parameters, dict) or set(parameters) != {
            "transfer_id",
            "lines",
        }:
            raise _invalid("Stock-transfer quantity parameters are invalid.")
        if not _valid_id(parameters["transfer_id"]):
            raise _invalid("parameters.transfer_id must be a positive integer.")
        lines = parameters["lines"]
        if not isinstance(lines, list) or not 1 <= len(lines) <= 200:
            raise _invalid("parameters.lines must contain between 1 and 200 lines.")
        normalized_lines: list[dict[str, Any]] = []
        move_ids: set[int] = set()
        for line in lines:
            if not isinstance(line, dict) or set(line) != {"move_id", "quantity"}:
                raise _invalid(
                    "Each stock quantity line must match the fixed line contract."
                )
            move_id = line["move_id"]
            if not _valid_id(move_id) or move_id in move_ids:
                raise _invalid(
                    "Stock quantity move_id values must be distinct positive integers."
                )
            quantity = _canonical_decimal(line["quantity"], signed=False)
            if quantity is None:
                raise _invalid(
                    "Stock quantity values must be canonical nonnegative decimals."
                )
            move_ids.add(move_id)
            normalized_lines.append(dict(line))
        return {
            "transfer_id": parameters["transfer_id"],
            "lines": sorted(normalized_lines, key=lambda item: item["move_id"]),
        }
    if capability_id == "stock.transfer.validate":
        if not isinstance(parameters, dict) or set(parameters) != {
            "transfer_id",
            "backorder_policy",
        }:
            raise _invalid("Stock-transfer validation parameters are invalid.")
        if not _valid_id(parameters["transfer_id"]):
            raise _invalid("parameters.transfer_id must be a positive integer.")
        if parameters["backorder_policy"] not in {"create", "cancel"}:
            raise _invalid("parameters.backorder_policy must be create or cancel.")
        return dict(parameters)
    return _validate_single_id(parameters, "transfer_id")


def _validate_purchase_bill_parameters(
    capability_id: str, parameters: Any
) -> dict[str, Any]:
    if capability_id == "purchase.order.bill.create":
        return _validate_single_id(parameters, "order_id")
    if capability_id == "purchase_bill.lines.unmatch":
        if not isinstance(parameters, dict) or set(parameters) != {
            "bill_id",
            "bill_line_ids",
        }:
            raise _invalid("Purchase-bill unmatch parameters are invalid.")
        if not _valid_id(parameters["bill_id"]):
            raise _invalid("parameters.bill_id must be a positive integer.")
        line_ids = _validate_ids(parameters["bill_line_ids"])
        if line_ids is None or not line_ids:
            raise _invalid(
                "parameters.bill_line_ids must contain distinct positive integers."
            )
        return {"bill_id": parameters["bill_id"], "bill_line_ids": sorted(line_ids)}
    if not isinstance(parameters, dict) or set(parameters) != {"bill_id", "pairs"}:
        raise _invalid("Purchase-bill match parameters are invalid.")
    if not _valid_id(parameters["bill_id"]):
        raise _invalid("parameters.bill_id must be a positive integer.")
    pairs = parameters["pairs"]
    if not isinstance(pairs, list) or not pairs:
        raise _invalid("parameters.pairs must be a non-empty list.")
    normalized = []
    bill_line_ids = set()
    for pair in pairs:
        if not isinstance(pair, dict) or set(pair) != {
            "bill_line_id",
            "purchase_line_id",
        }:
            raise _invalid("Each purchase-bill pair must match the fixed contract.")
        if not _valid_id(pair["bill_line_id"]) or not _valid_id(
            pair["purchase_line_id"]
        ):
            raise _invalid("Purchase-bill pair IDs must be positive integers.")
        if pair["bill_line_id"] in bill_line_ids:
            raise _invalid("Purchase-bill pair bill_line_id values must be unique.")
        bill_line_ids.add(pair["bill_line_id"])
        normalized.append(dict(pair))
    return {
        "bill_id": parameters["bill_id"],
        "pairs": sorted(
            normalized,
            key=lambda item: (item["bill_line_id"], item["purchase_line_id"]),
        ),
    }


_PAYMENT_TERM_HEADER_FIELDS = frozenset(
    {
        "sequence",
        "note",
        "display_on_invoice",
        "early_discount",
        "discount_percentage",
        "discount_days",
        "early_pay_discount_computation",
    }
)
_PAYMENT_TERM_DELAY_TYPES = frozenset(
    {
        "days_after",
        "days_after_end_of_month",
        "days_after_end_of_next_month",
        "days_end_of_month_on_the",
    }
)


def _validate_payment_term_header(values: dict[str, Any]) -> None:
    if "sequence" in values and (
        not isinstance(values["sequence"], int)
        or isinstance(values["sequence"], bool)
        or values["sequence"] < 0
    ):
        raise _invalid("Payment-term sequence must be a nonnegative integer.")
    if "note" in values and not _is_nullable_bounded_text(values["note"], 5000):
        raise _invalid("Payment-term note must be null or bounded non-empty text.")
    for field in ("display_on_invoice", "early_discount"):
        if field in values and not isinstance(values[field], bool):
            raise _invalid(f"Payment-term {field} must be boolean.")
    if "discount_percentage" in values:
        percentage = _canonical_decimal(values["discount_percentage"], signed=False)
        if percentage is None or percentage > 100:
            raise _invalid(
                "Payment-term discount_percentage must be between 0 and 100."
            )
    if "discount_days" in values and (
        not isinstance(values["discount_days"], int)
        or isinstance(values["discount_days"], bool)
        or values["discount_days"] < 0
    ):
        raise _invalid("Payment-term discount_days must be a nonnegative integer.")
    if "early_pay_discount_computation" in values and values[
        "early_pay_discount_computation"
    ] not in {"included", "excluded", "mixed"}:
        raise _invalid("Payment-term discount computation is invalid.")
    if values.get("early_discount") and (
        _canonical_decimal(values.get("discount_percentage"), signed=False) in {None, 0}
        or not isinstance(values.get("discount_days"), int)
        or isinstance(values.get("discount_days"), bool)
        or values["discount_days"] <= 0
    ):
        raise _invalid(
            "Early discount requires positive discount_percentage and discount_days."
        )


def _validate_payment_term_lines(lines: Any) -> list[dict[str, Any]]:
    if not isinstance(lines, list) or not lines:
        raise _invalid("Payment-term lines must be a non-empty list.")
    normalized = []
    percent_total = Decimal(0)
    has_percent = False
    for line in lines:
        required = {"value", "value_amount", "delay_type", "nb_days"}
        if (
            not isinstance(line, dict)
            or not required <= set(line)
            or not set(line) <= (required | {"days_next_month"})
        ):
            raise _invalid("Each payment-term line must match the fixed contract.")
        if line["value"] not in {"percent", "fixed"}:
            raise _invalid("Payment-term line value must be percent or fixed.")
        amount = _canonical_decimal(line["value_amount"], signed=False)
        if amount is None:
            raise _invalid("Payment-term line value_amount must be nonnegative.")
        if line["value"] == "percent":
            has_percent = True
            if amount > 100:
                raise _invalid("Payment-term percentages cannot exceed 100.")
            percent_total += amount
        if line["delay_type"] not in _PAYMENT_TERM_DELAY_TYPES:
            raise _invalid("Payment-term line delay_type is invalid.")
        if (
            not isinstance(line["nb_days"], int)
            or isinstance(line["nb_days"], bool)
            or line["nb_days"] < 0
        ):
            raise _invalid("Payment-term line nb_days must be nonnegative.")
        if "days_next_month" in line and (
            not isinstance(line["days_next_month"], int)
            or isinstance(line["days_next_month"], bool)
            or not 0 <= line["days_next_month"] <= 31
        ):
            raise _invalid("Payment-term line days_next_month must be from 0 to 31.")
        normalized.append(dict(line))
    if not has_percent or percent_total != 100:
        raise _invalid("Payment-term percent lines must total 100.")
    return normalized


def _validate_payment_term_parameters(
    capability_id: str, parameters: Any
) -> dict[str, Any]:
    if capability_id == "payment_term.create":
        required = {"name", "company_id", "lines"}
        if (
            not isinstance(parameters, dict)
            or not required <= set(parameters)
            or not set(parameters) <= (required | _PAYMENT_TERM_HEADER_FIELDS)
        ):
            raise _invalid("Payment-term creation parameters are invalid.")
        if not _is_bounded_text(parameters["name"], 200):
            raise _invalid("Payment-term name must be bounded non-empty text.")
        if not _valid_id(parameters["company_id"]):
            raise _invalid("parameters.company_id must be a positive integer.")
        _validate_payment_term_header(parameters)
        lines = _validate_payment_term_lines(parameters["lines"])
        if parameters.get("early_discount") and not (
            len(lines) == 1
            and lines[0]["value"] == "percent"
            and Decimal(lines[0]["value_amount"]) == 100
        ):
            raise _invalid("Early-discount terms require one 100 percent line.")
        return {**parameters, "lines": lines}
    if capability_id == "payment_term.update":
        if not isinstance(parameters, dict) or set(parameters) <= {"payment_term_id"}:
            raise _invalid("Payment-term update requires at least one head field.")
        if set(parameters) - {"payment_term_id"} - _PAYMENT_TERM_HEADER_FIELDS:
            raise _invalid("Payment-term update contains unsupported fields.")
        if not _valid_id(parameters.get("payment_term_id")):
            raise _invalid("parameters.payment_term_id must be a positive integer.")
        changes = {
            key: value for key, value in parameters.items() if key != "payment_term_id"
        }
        _validate_payment_term_header(changes)
        return {"payment_term_id": parameters["payment_term_id"], **changes}
    if capability_id == "payment_term.lines.replace":
        if not isinstance(parameters, dict) or set(parameters) != {
            "payment_term_id",
            "lines",
        }:
            raise _invalid("Payment-term line replacement parameters are invalid.")
        if not _valid_id(parameters["payment_term_id"]):
            raise _invalid("parameters.payment_term_id must be a positive integer.")
        return {
            "payment_term_id": parameters["payment_term_id"],
            "lines": _validate_payment_term_lines(parameters["lines"]),
        }
    return _validate_single_id(parameters, "payment_term_id")


def _validate_accrual_parameters(parameters: Any) -> dict[str, Any]:
    required = {
        "source_model",
        "order_ids",
        "date",
        "reversal_date",
        "journal_id",
        "accrual_account_id",
    }
    if (
        not isinstance(parameters, dict)
        or not required <= set(parameters)
        or not set(parameters) <= (required | {"amount"})
    ):
        raise _invalid("Period-accrual parameters are invalid.")
    if parameters["source_model"] not in {"sale.order", "purchase.order"}:
        raise _invalid("parameters.source_model is invalid.")
    order_ids = _validate_ids(parameters["order_ids"])
    if order_ids is None or not order_ids:
        raise _invalid("parameters.order_ids must contain distinct positive integers.")
    if not _is_date(parameters["date"]) or not _is_date(parameters["reversal_date"]):
        raise _invalid("Accrual dates must use YYYY-MM-DD.")
    if parameters["reversal_date"] <= parameters["date"]:
        raise _invalid("parameters.reversal_date must be later than parameters.date.")
    for field in ("journal_id", "accrual_account_id"):
        if not _valid_id(parameters[field]):
            raise _invalid(f"parameters.{field} must be a positive integer.")
    if "amount" in parameters:
        amount = _canonical_decimal(parameters["amount"], signed=False)
        if amount is None or amount <= 0:
            raise _invalid("parameters.amount must be a canonical positive decimal.")
        if len(order_ids) != 1:
            raise _invalid("parameters.amount is only valid for one order.")
    return {**parameters, "order_ids": sorted(order_ids)}


def _validate_transfer_parameters(
    capability_id: str, parameters: Any
) -> dict[str, Any]:
    expected = (
        {"transfer_model_id", "run_date"}
        if capability_id == "period.transfer.run"
        else {"run_date"}
    )
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise _invalid("Period-transfer parameters do not match the fixed contract.")
    if not _is_date(parameters["run_date"]):
        raise _invalid("parameters.run_date must be a YYYY-MM-DD date.")
    if capability_id == "period.transfer.run" and not _valid_id(
        parameters["transfer_model_id"]
    ):
        raise _invalid("parameters.transfer_model_id must be a positive integer.")
    return dict(parameters)


def _validate_account_return_parameters(
    capability_id: str, parameters: Any
) -> dict[str, Any]:
    if capability_id == "account.return.create":
        expected = {"return_type_id", "date_from", "date_to"}
        if not isinstance(parameters, dict) or set(parameters) != expected:
            raise _invalid(
                "Account-return create parameters do not match the fixed contract."
            )
        if not _valid_id(parameters["return_type_id"]):
            raise _invalid("parameters.return_type_id must be a positive integer.")
        if not _is_date(parameters["date_from"]) or not _is_date(parameters["date_to"]):
            raise _invalid(
                "parameters.date_from and parameters.date_to must be YYYY-MM-DD dates."
            )
        if parameters["date_from"] > parameters["date_to"]:
            raise _invalid("parameters.date_from must not be after parameters.date_to.")
        return dict(parameters)
    if capability_id == "account.return.check.result.update":
        if not isinstance(parameters, dict) or set(parameters) != {
            "check_id",
            "result",
        }:
            raise _invalid(
                "Account-return check-result parameters do not match the fixed contract."
            )
        if not _valid_id(parameters["check_id"]):
            raise _invalid("parameters.check_id must be a positive integer.")
        if parameters["result"] not in {"todo", "reviewed"}:
            raise _invalid("parameters.result must be todo or reviewed.")
        return dict(parameters)
    return _validate_single_id(parameters, "return_id")


def validate_core_write_request(
    capability_id: str, request: Any
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    """Validate and normalize one request from the fixed core-write set."""

    if capability_id not in CORE_WRITE_CAPABILITY_IDS:
        raise _invalid(
            "The requested core-write capability is unavailable.",
            code="capability_unavailable",
        )
    request_id, context, parameters = _validate_envelope(request)
    if capability_id in _ACCOUNT_RETURN_WRITE_CAPABILITIES:
        normalized = _validate_account_return_parameters(capability_id, parameters)
    elif capability_id.startswith("purchase_bill.") or capability_id == (
        "purchase.order.bill.create"
    ):
        normalized = _validate_purchase_bill_parameters(capability_id, parameters)
    elif capability_id == "sale.order.invoice.create":
        normalized = _validate_single_id(parameters, "order_id")
    elif capability_id in _STOCK_TRANSFER_WRITE_CAPABILITIES:
        normalized = _validate_stock_transfer_parameters(capability_id, parameters)
    elif capability_id.startswith("fiscal_year."):
        normalized = _validate_fiscal_year_parameters(capability_id, parameters)
    elif capability_id.startswith("analytic.applicability."):
        normalized = _validate_analytic_applicability_parameters(
            capability_id, parameters
        )
    elif capability_id.startswith("analytic.distribution_model."):
        normalized = _validate_analytic_distribution_model_parameters(
            capability_id, parameters
        )
    elif capability_id in _ACCOUNT_TAG_WRITE_CAPABILITIES:
        normalized = _validate_account_tag_parameters(capability_id, parameters)
    elif capability_id in _TAX_GROUP_WRITE_CAPABILITIES:
        normalized = _validate_tax_group_parameters(capability_id, parameters)
    elif capability_id in _CASH_ROUNDING_WRITE_CAPABILITIES:
        normalized = _validate_cash_rounding_parameters(capability_id, parameters)
    elif capability_id == "currency.rate.record":
        normalized = _validate_currency_rate_parameters(parameters)
    elif capability_id in _ACCOUNT_GROUP_WRITE_CAPABILITIES:
        normalized = _validate_account_group_parameters(capability_id, parameters)
    elif capability_id == "tax.repartition_lines.replace":
        normalized = _validate_tax_repartition_replacement(parameters)
    elif capability_id in _RECONCILIATION_MODEL_WRITE_CAPABILITIES:
        normalized = _validate_reconciliation_model_parameters(
            capability_id, parameters
        )
    elif capability_id in _FISCAL_POSITION_WRITE_CAPABILITIES:
        normalized = _validate_fiscal_position_parameters(capability_id, parameters)
    elif capability_id in _JOURNAL_GROUP_WRITE_CAPABILITIES:
        normalized = _validate_journal_group_parameters(capability_id, parameters)
    elif capability_id in _PAYMENT_TERM_WRITE_CAPABILITIES:
        normalized = _validate_payment_term_parameters(capability_id, parameters)
    elif capability_id == "period.accrual.generate":
        normalized = _validate_accrual_parameters(parameters)
    elif capability_id in _ORDER_CREATE_CAPABILITIES:
        normalized = _validate_order_create_parameters(capability_id, parameters)
    elif capability_id in _ORDER_UPDATE_CAPABILITIES:
        normalized = _validate_order_update_parameters(capability_id, parameters)
    elif capability_id in _ORDER_LINE_REPLACEMENT_CAPABILITIES:
        normalized = _validate_order_line_replacement_parameters(
            capability_id, parameters
        )
    elif capability_id in _ORDER_TRANSITION_CAPABILITIES:
        normalized = _validate_single_id(parameters, "order_id")
    elif capability_id in _INVOICE_CREATE_CAPABILITIES:
        normalized = _validate_invoice_parameters(parameters)
    elif capability_id == "journal_entry.create":
        normalized = _validate_journal_parameters(parameters)
    elif capability_id == "invoice.update":
        normalized = _validate_invoice_update_parameters(parameters)
    elif capability_id == "invoice.lines.replace":
        normalized = _validate_invoice_line_replacement_parameters(parameters)
    elif capability_id == "invoice.duplicate":
        normalized = _validate_single_id(parameters, "move_id")
    elif capability_id == "invoice.type.switch":
        normalized = _validate_invoice_type_switch_parameters(parameters)
    elif capability_id == "journal_entry.update":
        normalized = _validate_journal_entry_update_parameters(parameters)
    elif capability_id == "journal_entry.lines.replace":
        normalized = _validate_journal_line_replacement_parameters(parameters)
    elif capability_id in _MOVE_BATCH_LIFECYCLE_CAPABILITIES:
        normalized = _validate_singular_or_batch_ids(
            parameters, "move_id", "move_ids"
        )
    elif capability_id == "journal_entry.reverse":
        normalized = _validate_reverse_parameters(parameters)
    elif capability_id in _REFUND_CAPABILITIES:
        normalized = _validate_refund_parameters(parameters)
    elif capability_id in _PAYMENT_REGISTER_CAPABILITIES:
        normalized = _validate_payment_register_parameters(parameters)
    elif capability_id == "payment.create":
        normalized = _validate_payment_create_parameters(parameters)
    elif capability_id == "payment.update_draft":
        normalized = _validate_payment_update_parameters(parameters)
    elif capability_id in _PAYMENT_BATCH_LIFECYCLE_CAPABILITIES:
        normalized = _validate_singular_or_batch_ids(
            parameters, "payment_id", "payment_ids"
        )
    elif capability_id in _RECONCILIATION_CAPABILITIES:
        normalized = _validate_reconciliation_parameters(capability_id, parameters)
    elif capability_id == "bank.transaction.record":
        normalized = _validate_bank_transaction_parameters(parameters)
    elif capability_id == "bank.transaction.update":
        normalized = _validate_bank_transaction_update_parameters(parameters)
    elif capability_id == "bank.transaction.match":
        normalized = _validate_bank_match_parameters(parameters)
    elif capability_id == "bank.transaction.unmatch":
        normalized = _validate_single_id(parameters, "transaction_id")
    elif capability_id == "reconciliation.write_off":
        normalized = _validate_write_off_parameters(parameters)
    elif capability_id in _ANALYTIC_PLAN_WRITE_CAPABILITIES:
        normalized = _validate_analytic_plan_parameters(capability_id, parameters)
    elif capability_id == "analytic.account.create":
        normalized = _validate_analytic_account_create_parameters(parameters)
    elif capability_id == "analytic.account.update":
        normalized = _validate_analytic_account_update_parameters(parameters)
    elif capability_id in {"analytic.account.archive", "analytic.account.restore"}:
        normalized = _validate_single_id(parameters, "analytic_account_id")
    elif capability_id in _ANALYTIC_LINE_WRITE_CAPABILITIES:
        normalized = _validate_analytic_line_parameters(capability_id, parameters)
    elif capability_id == "budget.create":
        normalized = _validate_budget_fields(parameters, partial=False)
    elif capability_id == "budget.update_draft":
        normalized = _validate_budget_update_parameters(parameters)
    elif capability_id == "budget.lines.replace":
        normalized = _validate_budget_line_replacement_parameters(parameters)
    elif capability_id in {
        "budget.confirm",
        "budget.reset_to_draft",
        "budget.cancel",
        "budget.mark_done",
    }:
        normalized = _validate_single_id(parameters, "budget_id")
    elif capability_id == "partner.create":
        normalized = _validate_partner_create_parameters(parameters)
    elif capability_id == "partner.update":
        normalized = _validate_partner_update_parameters(parameters)
    elif capability_id in {"partner.archive", "partner.restore"}:
        normalized = _validate_single_id(parameters, "partner_id")
    elif capability_id == "partner.accounting.update":
        normalized = _validate_partner_accounting_update_parameters(parameters)
    elif capability_id == "partner.bank_account.create":
        normalized = _validate_partner_bank_create_parameters(parameters)
    elif capability_id == "partner.bank_account.update":
        normalized = _validate_partner_bank_update_parameters(parameters)
    elif capability_id in {
        "partner.bank_account.archive",
        "partner.bank_account.restore",
    }:
        normalized = _validate_single_id(parameters, "partner_bank_id")
    elif capability_id == "account.account.create":
        normalized = _validate_account_configuration_values(parameters, partial=False)
    elif capability_id == "account.account.update":
        normalized = _validate_account_configuration_update(parameters)
    elif capability_id in {"account.account.archive", "account.account.restore"}:
        normalized = _validate_single_id(parameters, "account_id")
    elif capability_id == "journal.create":
        normalized = _validate_journal_configuration_values(parameters, partial=False)
    elif capability_id == "journal.update":
        normalized = _validate_journal_configuration_update(parameters)
    elif capability_id in {"journal.archive", "journal.restore"}:
        normalized = _validate_single_id(parameters, "journal_id")
    elif capability_id == "tax.create":
        normalized = _validate_tax_configuration_values(parameters, partial=False)
    elif capability_id == "tax.update":
        normalized = _validate_tax_configuration_update(parameters)
    elif capability_id in {"tax.archive", "tax.restore"}:
        normalized = _validate_single_id(parameters, "tax_id")
    elif capability_id == "asset.create":
        normalized = _validate_asset_create_parameters(parameters)
    elif capability_id == "asset.validate":
        normalized = _validate_single_id(parameters, "asset_id")
    elif capability_id in _ASSET_LIFECYCLE_CAPABILITIES:
        normalized = _validate_asset_lifecycle_parameters(capability_id, parameters)
    elif capability_id in _DEFERRED_GENERATION_CAPABILITIES:
        normalized = _validate_deferred_generation_parameters(parameters)
    elif capability_id == "multicurrency.revaluation.generate_entries":
        normalized = _validate_revaluation_parameters(parameters)
    elif capability_id == "reconciliation.automatic.run":
        normalized = _validate_automatic_reconciliation_parameters(parameters)
    elif capability_id in _TRANSFER_CAPABILITIES:
        normalized = _validate_transfer_parameters(capability_id, parameters)
    else:
        normalized = _validate_single_id(parameters, "payment_id")
    return request_id, context, normalized


def _expected_idempotency_key(
    capability_id: str, parameters: dict[str, Any], company_id: int
) -> str | None:
    if capability_id in _BATCH_LIFECYCLE_CAPABILITIES and (
        "move_ids" in parameters or "payment_ids" in parameters
    ):
        canonical = json.dumps(
            parameters, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"{capability_id}:{company_id}:{digest}"
    if capability_id == "account.return.create":
        canonical = json.dumps(
            parameters, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"account.return.create:{company_id}:{digest}"
    if capability_id == "account.return.check.result.update":
        return (
            f"account.return.check.result.update:{parameters['check_id']}:"
            f"{parameters['result']}"
        )
    if capability_id in _ACCOUNT_RETURN_WRITE_CAPABILITIES:
        return f"{capability_id}:{parameters['return_id']}"
    if capability_id in {
        "account.tag.create",
        "tax.group.create",
        "cash_rounding.create",
        "fiscal_year.create",
        "analytic.applicability.create",
        "analytic.distribution_model.create",
    }:
        canonical = json.dumps(
            parameters, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"{capability_id}:{company_id}:{digest}"
    if capability_id in {
        "account.tag.update",
        "tax.group.update",
        "cash_rounding.update",
        "fiscal_year.update",
        "analytic.applicability.update",
        "analytic.distribution_model.update",
    }:
        canonical = json.dumps(
            parameters["changes"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        primary_field = {
            "account.tag.update": "account_tag_id",
            "tax.group.update": "tax_group_id",
            "cash_rounding.update": "cash_rounding_id",
            "fiscal_year.update": "id",
            "analytic.applicability.update": "id",
            "analytic.distribution_model.update": "id",
        }[capability_id]
        return f"{capability_id}:{parameters[primary_field]}:{digest}"
    if capability_id in {"account.tag.archive", "account.tag.restore"}:
        return f"{capability_id}:{parameters['account_tag_id']}"
    if capability_id in {
        "currency.rate.record",
        "account.group.create",
        "reconciliation.model.create",
    }:
        canonical = json.dumps(
            parameters, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"{capability_id}:{company_id}:{digest}"
    if capability_id in {
        "account.group.update",
        "reconciliation.model.update",
    }:
        canonical = json.dumps(
            parameters["changes"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        primary = (
            parameters["account_group_id"]
            if capability_id == "account.group.update"
            else parameters["reconciliation_model_id"]
        )
        return f"{capability_id}:{primary}:{digest}"
    if capability_id in {
        "tax.repartition_lines.replace",
        "reconciliation.model.lines.replace",
    }:
        target = (
            {
                "invoice_lines": parameters["invoice_lines"],
                "refund_lines": parameters["refund_lines"],
            }
            if capability_id == "tax.repartition_lines.replace"
            else parameters["lines"]
        )
        canonical = json.dumps(
            target, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        primary = (
            parameters["tax_id"]
            if capability_id == "tax.repartition_lines.replace"
            else parameters["reconciliation_model_id"]
        )
        return f"{capability_id}:{primary}:{digest}"
    if capability_id in {
        "reconciliation.model.archive",
        "reconciliation.model.restore",
    }:
        return f"{capability_id}:{parameters['reconciliation_model_id']}"
    if capability_id in {"fiscal_position.create", "journal.group.create"}:
        canonical = json.dumps(
            parameters, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"{capability_id}:{company_id}:{digest}"
    if capability_id in {"fiscal_position.update", "journal.group.update"}:
        canonical = json.dumps(
            parameters["changes"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        field = (
            "fiscal_position_id"
            if capability_id.startswith("fiscal_position.")
            else "journal_group_id"
        )
        return f"{capability_id}:{parameters[field]}:{digest}"
    if capability_id == "fiscal_position.account_mappings.replace":
        canonical = json.dumps(
            parameters["mappings"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"{capability_id}:{parameters['fiscal_position_id']}:{digest}"
    if capability_id in {"fiscal_position.archive", "fiscal_position.restore"}:
        return f"{capability_id}:{parameters['fiscal_position_id']}"
    if capability_id in {
        "account.account.create",
        "journal.create",
        "tax.create",
    }:
        canonical = json.dumps(
            parameters,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"{capability_id}:{company_id}:{digest}"
    if capability_id in {
        "account.account.update",
        "journal.update",
        "tax.update",
    }:
        canonical = json.dumps(
            parameters["changes"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        primary_field = {
            "account.account.update": "account_id",
            "journal.update": "journal_id",
            "tax.update": "tax_id",
        }[capability_id]
        return f"{capability_id}:{parameters[primary_field]}:{digest}"
    if capability_id in {
        "account.account.archive",
        "account.account.restore",
        "journal.archive",
        "journal.restore",
        "tax.archive",
        "tax.restore",
    }:
        primary_field = (
            "account_id"
            if capability_id.startswith("account.account.")
            else "journal_id"
            if capability_id.startswith("journal.")
            else "tax_id"
        )
        return f"{capability_id}:{parameters[primary_field]}"
    if capability_id == "partner.create":
        canonical = json.dumps(
            parameters,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"partner.create:{digest}"
    if capability_id in {"partner.update", "partner.accounting.update"}:
        canonical = json.dumps(
            parameters["changes"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"{capability_id}:{parameters['partner_id']}:{digest}"
    if capability_id in {"partner.archive", "partner.restore"}:
        return f"{capability_id}:{parameters['partner_id']}"
    if capability_id == "partner.bank_account.create":
        digest = hashlib.sha256(
            parameters["account_number"].encode("utf-8")
        ).hexdigest()[:32]
        return f"partner.bank_account.create:{parameters['partner_id']}:{digest}"
    if capability_id == "partner.bank_account.update":
        canonical = json.dumps(
            parameters["changes"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"partner.bank_account.update:{parameters['partner_bank_id']}:{digest}"
    if capability_id in {
        "partner.bank_account.archive",
        "partner.bank_account.restore",
    }:
        return f"{capability_id}:{parameters['partner_bank_id']}"
    if capability_id in {"purchase_bill.match", "purchase_bill.lines.unmatch"}:
        target = parameters.get("pairs", parameters.get("bill_line_ids"))
        canonical = json.dumps(
            target,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"{capability_id}:{parameters['bill_id']}:{digest}"
    if capability_id in {"payment_term.update", "payment_term.lines.replace"}:
        target = (
            parameters["lines"]
            if capability_id == "payment_term.lines.replace"
            else {
                key: value
                for key, value in parameters.items()
                if key != "payment_term_id"
            }
        )
        canonical = json.dumps(
            target,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"{capability_id}:{parameters['payment_term_id']}:{digest}"
    if capability_id in {"payment_term.archive", "payment_term.restore"}:
        return f"{capability_id}:{parameters['payment_term_id']}"
    if capability_id == "sale.order.invoice.create":
        return f"sale.order.invoice.create:{parameters['order_id']}"
    if capability_id == "stock.transfer.create":
        return None
    if capability_id == "stock.transfer.quantities.set":
        canonical = json.dumps(
            parameters["lines"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"stock.transfer.quantities.set:{parameters['transfer_id']}:{digest}"
    if capability_id == "stock.transfer.validate":
        return (
            f"stock.transfer.validate:{parameters['transfer_id']}:"
            f"{parameters['backorder_policy']}"
        )
    if capability_id in _STOCK_TRANSFER_ACTION_CAPABILITIES:
        return f"{capability_id}:{parameters['transfer_id']}"
    if capability_id == "purchase.order.bill.create":
        return f"purchase.order.bill.create:{parameters['order_id']}"
    if capability_id in _CREATE_CAPABILITIES:
        return None
    if capability_id in _REFUND_CAPABILITIES:
        return None
    if capability_id == "invoice.duplicate":
        return None
    if capability_id == "invoice.type.switch":
        return (
            f"invoice.type.switch:{parameters['move_id']}:"
            f"{parameters['target_move_type']}"
        )
    if capability_id in _PAYMENT_REGISTER_CAPABILITIES and "amount" in parameters:
        return None
    if capability_id in _PAYMENT_REGISTER_CAPABILITIES and "move_ids" in parameters:
        canonical = json.dumps(
            parameters,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"{capability_id}:{company_id}:{digest}"
    if (
        capability_id
        in _ORDER_UPDATE_CAPABILITIES | _ORDER_LINE_REPLACEMENT_CAPABILITIES
    ):
        target = (
            parameters["changes"]
            if capability_id in _ORDER_UPDATE_CAPABILITIES
            else parameters["lines"]
        )
        canonical = json.dumps(
            target,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"{capability_id}:{parameters['order_id']}:{digest}"
    if capability_id in _ORDER_TRANSITION_CAPABILITIES:
        return f"{capability_id}:{parameters['order_id']}"
    if capability_id in _DOCUMENT_CONTENT_CAPABILITIES:
        target = (
            parameters["changes"]
            if capability_id in {"invoice.update", "journal_entry.update"}
            else parameters["lines"]
        )
        canonical = json.dumps(
            target,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"{capability_id}:{parameters['move_id']}:{digest}"
    if capability_id == "payment.update_draft":
        canonical = json.dumps(
            parameters["changes"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"payment.update_draft:{parameters['payment_id']}:{digest}"
    if capability_id == "payment.reset_to_draft":
        return f"payment.reset_to_draft:{parameters['payment_id']}"
    if capability_id in {
        "analytic.plan.update",
        "analytic.account.update",
        "analytic.line.update",
        "budget.update_draft",
        "budget.lines.replace",
    }:
        target = (
            parameters["lines"]
            if capability_id == "budget.lines.replace"
            else parameters["changes"]
        )
        canonical = json.dumps(
            target,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        primary = parameters.get(
            "plan_id",
            parameters.get(
                "analytic_account_id",
                parameters.get("analytic_line_id", parameters.get("budget_id")),
            ),
        )
        return f"{capability_id}:{primary}:{digest}"
    if capability_id in {
        "analytic.account.archive",
        "analytic.account.restore",
    }:
        return f"{capability_id}:{parameters['analytic_account_id']}"
    if capability_id == "analytic.line.delete":
        return f"analytic.line.delete:{parameters['analytic_line_id']}"
    if capability_id in {
        "budget.confirm",
        "budget.reset_to_draft",
        "budget.cancel",
        "budget.mark_done",
    }:
        return f"{capability_id}:{parameters['budget_id']}"
    if capability_id == "bank.transaction.update":
        target = parameters["changes"]
    elif capability_id == "bank.transaction.match":
        target = parameters["candidate_line_ids"]
    elif capability_id == "reconciliation.write_off":
        target = {
            "write_off_account_id": parameters["write_off_account_id"],
            "expected_residual_amount": parameters["expected_residual_amount"],
            "label": parameters["label"],
        }
    else:
        target = None
    if target is not None:
        canonical = json.dumps(
            target,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"{capability_id}:{parameters['transaction_id']}:{digest}"
    if capability_id == "bank.transaction.unmatch":
        return f"bank.transaction.unmatch:{parameters['transaction_id']}"
    if capability_id in _RECONCILIATION_CAPABILITIES:
        if "line_ids" in parameters:
            first, second = parameters["line_ids"]
            return f"{capability_id}:{first}:{second}"
        if capability_id == "reconciliation.apply":
            return (
                f"reconciliation.apply:{parameters['invoice_id']}:"
                f"{parameters['outstanding_line_id']}"
            )
        first, second = sorted(
            (parameters["invoice_line_id"], parameters["counterpart_line_id"])
        )
        return (
            f"reconciliation.undo:{parameters['invoice_id']}:"
            f"{parameters['partial_reconcile_id']}:{first}:{second}"
        )
    if capability_id == "asset.validate":
        return f"asset.validate:{parameters['asset_id']}"
    if capability_id in {"asset.cancel", "asset.dispose"}:
        return f"{capability_id}:{parameters['asset_id']}"
    if capability_id == "asset.pause":
        return f"asset.pause:{parameters['asset_id']}:{parameters['date']}"
    if capability_id in _DEFERRED_GENERATION_CAPABILITIES:
        return f"{capability_id}:{parameters['date_to']}"
    if capability_id == "multicurrency.revaluation.generate_entries":
        return f"{capability_id}:{parameters['date']}"
    if capability_id == "reconciliation.automatic.run":
        canonical_ids = ",".join(str(item) for item in parameters["line_ids"])
        digest = hashlib.sha256(canonical_ids.encode("ascii")).hexdigest()[:32]
        return f"reconciliation.automatic.run:{digest}"
    if capability_id == "period.transfer.run":
        return (
            f"period.transfer.run:{parameters['transfer_model_id']}:"
            f"{parameters['run_date']}"
        )
    if capability_id == "localization.china.period_transfer.run":
        return (
            f"localization.china.period_transfer.run:{company_id}:"
            f"{parameters['run_date']}"
        )
    primary = parameters.get("move_id", parameters.get("payment_id"))
    return f"{capability_id}:{primary}"


def _validate_idempotency_and_confirmation(
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    idempotency_key: Any,
    confirmation: Any,
) -> None:
    if (
        not isinstance(idempotency_key, str)
        or _IDEMPOTENCY_PATTERN.fullmatch(idempotency_key) is None
    ):
        raise _invalid(
            "idempotency_key must contain 8 to 128 safe characters.",
            code="invalid_idempotency_key",
        )
    expected = _expected_idempotency_key(capability_id, parameters, company_id)
    if expected is not None and idempotency_key != expected:
        raise _invalid(
            f"idempotency_key must be '{expected}'.",
            code="invalid_idempotency_key",
        )
    if confirmation != capability_id:
        raise _invalid(
            "confirmation must exactly equal the capability ID.",
            code="confirmation_required",
        )


def _strict_ids(value: Any) -> bool:
    return (
        isinstance(value, list)
        and all(_valid_id(item) for item in value)
        and value == sorted(set(value))
    )


def _valid_result_shape(result: Any) -> bool:
    return (
        isinstance(result, dict)
        and set(result) == _RESULT_FIELDS
        and _is_text(result["model"])
        and _valid_optional_id(result["id"])
        and _is_optional_text(result["name"])
        and _is_text(result["state"])
        and _valid_id(result["company_id"])
        and _is_optional_text(result["move_type"])
        and _valid_optional_id(result["source_id"])
        and _strict_ids(result["line_ids"])
        and _strict_ids(result["partial_reconcile_ids"])
        and _valid_optional_id(result["full_reconcile_id"])
        and isinstance(result["reconciled"], bool)
    )


def _valid_batch_result_shape(result: Any) -> bool:
    return (
        isinstance(result, dict)
        and set(result) == _BATCH_RESULT_FIELDS
        and _is_integer(result["processed_count"])
        and 2 <= result["processed_count"] <= 100
        and isinstance(result["items"], list)
        and len(result["items"]) == result["processed_count"]
        and all(_valid_result_shape(item) for item in result["items"])
        and all(_valid_id(item["id"]) for item in result["items"])
        and [item["id"] for item in result["items"]]
        == sorted({item["id"] for item in result["items"]})
    )


def _validate_page(
    port: CoreWritePort, page: Any
) -> tuple[bool, dict[str, Any] | None]:
    if (
        not isinstance(page, dict)
        or set(page) != _PAGE_FIELDS
        or not _valid_id(page["user_id"])
        or not isinstance(page["company_visible"], bool)
        or not isinstance(page["module_installed"], bool)
        or not isinstance(page["access_allowed"], bool)
        or not isinstance(page["idempotent_replay"], bool)
        or not (
            page["result"] is None
            or _valid_result_shape(page["result"])
            or _valid_batch_result_shape(page["result"])
        )
    ):
        raise _failed("The Odoo bridge returned an invalid core-write result.")
    try:
        port_user_id = port.user_id
    except ValueError as exc:
        raise _failed("The Odoo bridge returned an invalid core-write result.") from exc
    if page["user_id"] != port_user_id:
        raise _failed("The Odoo bridge returned a mismatched core-write user.")
    if page["access_allowed"] and not (
        page["company_visible"] and page["module_installed"]
    ):
        raise _failed("The Odoo bridge returned inconsistent core-write gates.")
    if page["result"] is not None and not (
        page["company_visible"] and page["module_installed"] and page["access_allowed"]
    ):
        raise _failed(
            "The Odoo bridge returned a result from a denied core-write gate."
        )
    if not page["module_installed"]:
        raise CoreWriteError(
            "uninstalled",
            "The Odoo accounting module required by this write is unavailable.",
            exit_code=4,
        )
    if not page["company_visible"]:
        raise CoreWriteError(
            "company_unavailable",
            "The requested company is unavailable to the configured user.",
            exit_code=3,
        )
    if not page["access_allowed"]:
        raise CoreWriteError(
            "unauthorized",
            "The configured user cannot execute this accounting write.",
            exit_code=3,
        )
    return page["idempotent_replay"], page["result"]


def _validate_result(
    capability_id: str,
    parameters: dict[str, Any],
    result: Any,
    *,
    company_id: int,
    idempotent_replay: bool,
) -> dict[str, Any]:
    if not _valid_result_shape(result) or result["company_id"] != company_id:
        raise _failed("Odoo returned a malformed or out-of-scope core-write result.")

    if capability_id in _ACCOUNT_RETURN_WRITE_CAPABILITIES:
        check_update = capability_id == "account.return.check.result.update"
        expected_id = (
            parameters["check_id"]
            if check_update
            else result["id"]
            if capability_id == "account.return.create"
            else parameters["return_id"]
        )
        expected_states = {
            "account.return.create": (
                {"new", "reviewed", "submitted", "archived"}
                if idempotent_replay
                else {"new"}
            ),
            "account.return.checks.refresh": {"new"},
            "account.return.check.result.update": {parameters.get("result")},
            "account.return.validate": (
                {"reviewed", "submitted"}
                if idempotent_replay
                else {"reviewed"}
            ),
            "account.return.mark_submitted": {"submitted"},
            "account.return.archive": {"archived"},
            "account.return.restore": {"new"},
            "account.return.delete": {"deleted"},
        }[capability_id]
        source_matches = (
            result["source_id"] == parameters["return_type_id"]
            if capability_id == "account.return.create"
            else _valid_id(result["source_id"])
        )
        if (
            result["model"]
            != ("account.return.check" if check_update else "account.return")
            or result["id"] != expected_id
            or not _valid_id(result["id"])
            or not _is_text(result["name"])
            or result["state"] not in expected_states
            or result["move_type"] is not None
            or not source_matches
            or result["line_ids"]
            or result["partial_reconcile_ids"]
            or result["full_reconcile_id"] is not None
            or result["reconciled"]
        ):
            raise _failed("Odoo returned a mismatched account-return result.")
        return deepcopy(result)

    if capability_id == "reconciliation.apply":
        invoice_mode = "invoice_id" in parameters
        reconciliation_matches = (
            result["source_id"] == parameters["invoice_id"]
            and len(result["line_ids"]) >= 2
            and parameters["outstanding_line_id"] in result["line_ids"]
            if invoice_mode
            else result["source_id"] is None
            and result["line_ids"] == parameters["line_ids"]
        )
        if (
            result["model"] != "account.move.line"
            or result["id"] is not None
            or result["move_type"] is not None
            or not reconciliation_matches
            or not result["partial_reconcile_ids"]
        ):
            raise _failed("Odoo returned a mismatched reconciliation result.")
        if result["full_reconcile_id"] is not None and not result["reconciled"]:
            raise _failed("Odoo returned an inconsistent full reconciliation result.")
        return deepcopy(result)

    if capability_id == "reconciliation.undo":
        invoice_mode = "invoice_id" in parameters
        line_ids_match = (
            parameters["invoice_line_id"] in result["line_ids"]
            if invoice_mode
            else result["line_ids"] == parameters["line_ids"]
        )
        expected_source_id = parameters["invoice_id"] if invoice_mode else None
        common_mismatch = (
            result["model"] != "account.move.line"
            or result["id"] is not None
            or result["name"] is not None
            or result["move_type"] is not None
            or result["source_id"] != expected_source_id
            or not line_ids_match
        )
        if invoice_mode:
            remaining_partial_ids = result["partial_reconcile_ids"]
            state_is_consistent = (
                (
                    result["state"] == "unreconciled"
                    and not remaining_partial_ids
                    and result["full_reconcile_id"] is None
                    and not result["reconciled"]
                )
                or (
                    result["state"] == "partial"
                    and bool(remaining_partial_ids)
                    and not result["reconciled"]
                )
                or (
                    result["state"] == "reconciled"
                    and bool(remaining_partial_ids)
                    and result["reconciled"]
                )
            )
            result_mismatch = (
                parameters["partial_reconcile_id"] in remaining_partial_ids
                or (bool(remaining_partial_ids) and len(result["line_ids"]) < 2)
                or not state_is_consistent
            )
        else:
            result_mismatch = (
                result["state"] != "unreconciled"
                or bool(result["partial_reconcile_ids"])
                or result["full_reconcile_id"] is not None
                or result["reconciled"]
            )
        if common_mismatch or result_mismatch:
            raise _failed("Odoo returned a mismatched reconciliation result.")
        return deepcopy(result)

    if capability_id == "reconciliation.automatic.run":
        if (
            result["model"] != "account.move.line"
            or result["id"] is not None
            or result["name"] is not None
            or result["state"] != "reconciled"
            or result["move_type"] is not None
            or result["source_id"] is not None
            or not set(parameters["line_ids"]).issubset(result["line_ids"])
            or not result["partial_reconcile_ids"]
            or not result["reconciled"]
        ):
            raise _failed("Odoo returned a mismatched automatic reconciliation.")
        return deepcopy(result)

    if not _valid_id(result["id"]):
        raise _failed("Odoo returned a core-write result without a record ID.")
    if capability_id == "currency.rate.record":
        if (
            result["model"] != "res.currency.rate"
            or not _is_text(result["name"])
            or result["state"] != "active"
            or result["move_type"] is not None
            or result["source_id"] != parameters["currency_id"]
            or result["line_ids"]
            or result["partial_reconcile_ids"]
            or result["full_reconcile_id"] is not None
            or result["reconciled"]
        ):
            raise _failed("Odoo returned a mismatched currency-rate result.")
        return deepcopy(result)
    if capability_id in (
        _ACCOUNT_TAG_WRITE_CAPABILITIES
        | _TAX_GROUP_WRITE_CAPABILITIES
        | _CASH_ROUNDING_WRITE_CAPABILITIES
        | _ACCOUNTING_RULE_WRITE_CAPABILITIES
    ):
        identifier_field = (
            "account_tag_id"
            if capability_id.startswith("account.tag.")
            else "tax_group_id"
            if capability_id.startswith("tax.group.")
            else "id"
            if capability_id in _ACCOUNTING_RULE_WRITE_CAPABILITIES
            else "cash_rounding_id"
        )
        expected_id = (
            result["id"]
            if capability_id.endswith(".create")
            else parameters[identifier_field]
        )
        expected_model = (
            "account.account.tag"
            if capability_id.startswith("account.tag.")
            else "account.tax.group"
            if capability_id.startswith("tax.group.")
            else "account.fiscal.year"
            if capability_id.startswith("fiscal_year.")
            else "account.analytic.applicability"
            if capability_id.startswith("analytic.applicability.")
            else "account.analytic.distribution.model"
            if capability_id.startswith("analytic.distribution_model.")
            else "account.cash.rounding"
        )
        expected_states = (
            {"archived"}
            if capability_id == "account.tag.archive"
            else {"active"}
            if capability_id
            in {
                "account.tag.create",
                "account.tag.restore",
                "tax.group.create",
                "tax.group.update",
                "cash_rounding.create",
                "cash_rounding.update",
                "fiscal_year.create",
                "fiscal_year.update",
                "analytic.applicability.create",
                "analytic.applicability.update",
                "analytic.distribution_model.create",
                "analytic.distribution_model.update",
            }
            else {"active", "archived"}
        )
        nullable_name = capability_id.startswith(
            ("analytic.applicability.", "analytic.distribution_model.")
        )
        if (
            result["model"] != expected_model
            or result["id"] != expected_id
            or not (
                _is_text(result["name"]) or (nullable_name and result["name"] is None)
            )
            or result["state"] not in expected_states
            or result["move_type"] is not None
            or result["source_id"] is not None
            or result["line_ids"]
            or result["partial_reconcile_ids"]
            or result["full_reconcile_id"] is not None
            or result["reconciled"]
        ):
            raise _failed("Odoo returned a mismatched accounting master-data result.")
        return deepcopy(result)
    if capability_id in _ACCOUNT_GROUP_WRITE_CAPABILITIES:
        expected_id = (
            result["id"]
            if capability_id == "account.group.create"
            else parameters["account_group_id"]
        )
        if (
            result["model"] != "account.group"
            or result["id"] != expected_id
            or not _is_text(result["name"])
            or result["state"] != "active"
            or result["move_type"] is not None
            or result["source_id"] is not None
            or result["line_ids"]
            or result["partial_reconcile_ids"]
            or result["full_reconcile_id"] is not None
            or result["reconciled"]
        ):
            raise _failed("Odoo returned a mismatched account-group result.")
        return deepcopy(result)
    if capability_id == "tax.repartition_lines.replace":
        if (
            result["model"] != "account.tax"
            or result["id"] != parameters["tax_id"]
            or not _is_text(result["name"])
            or result["state"] not in {"active", "archived"}
            or result["move_type"] is not None
            or result["source_id"] is not None
            or len(result["line_ids"])
            != len(parameters["invoice_lines"]) + len(parameters["refund_lines"])
            or result["partial_reconcile_ids"]
            or result["full_reconcile_id"] is not None
            or result["reconciled"]
        ):
            raise _failed("Odoo returned mismatched tax-repartition lines.")
        return deepcopy(result)
    if capability_id in _RECONCILIATION_MODEL_WRITE_CAPABILITIES:
        expected_id = (
            result["id"]
            if capability_id == "reconciliation.model.create"
            else parameters["reconciliation_model_id"]
        )
        expected_states = (
            {"archived"}
            if capability_id == "reconciliation.model.archive"
            else {"active"}
            if capability_id
            in {"reconciliation.model.create", "reconciliation.model.restore"}
            else {"active", "archived"}
        )
        expected_line_count = (
            len(parameters["lines"])
            if capability_id == "reconciliation.model.lines.replace"
            else None
        )
        if (
            result["model"] != "account.reconcile.model"
            or result["id"] != expected_id
            or not _is_text(result["name"])
            or result["state"] not in expected_states
            or result["move_type"] is not None
            or result["source_id"] is not None
            or (
                expected_line_count is not None
                and len(result["line_ids"]) != expected_line_count
            )
            or result["partial_reconcile_ids"]
            or result["full_reconcile_id"] is not None
            or result["reconciled"]
        ):
            raise _failed("Odoo returned a mismatched reconciliation-model result.")
        return deepcopy(result)
    if capability_id == "sale.order.invoice.create":
        expected_states = (
            {"draft", "posted", "cancel"} if idempotent_replay else {"draft"}
        )
        if (
            result["model"] != "account.move"
            or result["state"] not in expected_states
            or result["move_type"] != "out_invoice"
            or result["source_id"] != parameters["order_id"]
            or not result["line_ids"]
            or result["partial_reconcile_ids"]
            or result["full_reconcile_id"] is not None
            or result["reconciled"]
        ):
            raise _failed("Odoo returned a mismatched sales-order invoice result.")
        return deepcopy(result)
    if capability_id in _STOCK_TRANSFER_WRITE_CAPABILITIES:
        expected_id = (
            result["id"]
            if capability_id == "stock.transfer.create"
            else parameters["transfer_id"]
        )
        all_states = {"draft", "waiting", "confirmed", "assigned", "done", "cancel"}
        if capability_id == "stock.transfer.create":
            expected_states = all_states if idempotent_replay else {"draft"}
        elif capability_id == "stock.transfer.validate":
            expected_states = {"done"}
        elif capability_id == "stock.transfer.cancel":
            expected_states = {"cancel"}
        elif capability_id == "stock.transfer.unreserve":
            expected_states = {"waiting", "confirmed"}
        elif capability_id in {"stock.transfer.confirm", "stock.transfer.assign"}:
            expected_states = {"waiting", "confirmed", "assigned"}
            if idempotent_replay:
                expected_states.add("done")
        else:
            expected_states = {"draft", "waiting", "confirmed", "assigned"}
            if idempotent_replay:
                expected_states.add("done")
        if (
            result["model"] != "stock.picking"
            or result["id"] != expected_id
            or not _is_text(result["name"])
            or result["state"] not in expected_states
            or result["move_type"] is not None
            or not _valid_id(result["source_id"])
            or (
                capability_id == "stock.transfer.create"
                and result["source_id"] != parameters["picking_type_id"]
            )
            or not result["line_ids"]
            or result["partial_reconcile_ids"]
            or result["full_reconcile_id"] is not None
            or result["reconciled"]
        ):
            raise _failed("Odoo returned a mismatched stock-transfer result.")
        return deepcopy(result)
    if capability_id in {
        "purchase.order.bill.create",
        "purchase_bill.match",
        "purchase_bill.lines.unmatch",
    }:
        expected_id = (
            result["id"]
            if capability_id == "purchase.order.bill.create"
            else parameters["bill_id"]
        )
        expected_line_ids = (
            None
            if capability_id == "purchase.order.bill.create"
            else sorted(pair["bill_line_id"] for pair in parameters["pairs"])
            if capability_id == "purchase_bill.match"
            else parameters["bill_line_ids"]
        )
        source_matches = (
            result["source_id"] == parameters["order_id"]
            if capability_id == "purchase.order.bill.create"
            else result["source_id"] is None
        )
        if (
            result["model"] != "account.move"
            or result["id"] != expected_id
            or (result["name"] is not None and not _is_text(result["name"]))
            or result["state"] != "draft"
            or result["move_type"] != "in_invoice"
            or not source_matches
            or (
                not result["line_ids"]
                if expected_line_ids is None
                else result["line_ids"] != expected_line_ids
            )
            or result["partial_reconcile_ids"]
            or result["full_reconcile_id"] is not None
            or result["reconciled"]
        ):
            raise _failed("Odoo returned a mismatched purchase-bill result.")
        return deepcopy(result)
    if capability_id in _FISCAL_POSITION_WRITE_CAPABILITIES:
        expected_id = (
            result["id"]
            if capability_id == "fiscal_position.create"
            else parameters["fiscal_position_id"]
        )
        expected_state = (
            "archived"
            if capability_id == "fiscal_position.archive"
            else "active"
            if capability_id == "fiscal_position.restore"
            else None
        )
        expected_lines = (
            len(parameters["mappings"])
            if capability_id == "fiscal_position.account_mappings.replace"
            else None
        )
        if (
            result["model"] != "account.fiscal.position"
            or result["id"] != expected_id
            or not _is_text(result["name"])
            or (expected_state is not None and result["state"] != expected_state)
            or (
                expected_lines is not None and len(result["line_ids"]) != expected_lines
            )
            or result["move_type"] is not None
            or result["source_id"] is not None
            or result["partial_reconcile_ids"]
            or result["full_reconcile_id"] is not None
            or result["reconciled"]
        ):
            raise _failed("Odoo returned a mismatched fiscal-position result.")
        return deepcopy(result)
    if capability_id in _JOURNAL_GROUP_WRITE_CAPABILITIES:
        expected_id = (
            result["id"]
            if capability_id == "journal.group.create"
            else parameters["journal_group_id"]
        )
        if (
            result["model"] != "account.journal.group"
            or result["id"] != expected_id
            or not _is_text(result["name"])
            or result["state"] != "active"
            or result["move_type"] is not None
            or result["source_id"] is not None
            or result["line_ids"]
            or result["partial_reconcile_ids"]
            or result["full_reconcile_id"] is not None
            or result["reconciled"]
        ):
            raise _failed("Odoo returned a mismatched journal-group result.")
        return deepcopy(result)
    if capability_id in _PAYMENT_TERM_WRITE_CAPABILITIES:
        expected_id = (
            result["id"]
            if capability_id == "payment_term.create"
            else parameters["payment_term_id"]
        )
        expected_states = (
            {"archived"}
            if capability_id == "payment_term.archive"
            else {"active"}
            if capability_id in {"payment_term.create", "payment_term.restore"}
            else {"active", "archived"}
        )
        expected_line_count = (
            len(parameters["lines"])
            if capability_id in {"payment_term.create", "payment_term.lines.replace"}
            else None
        )
        if (
            result["model"] != "account.payment.term"
            or result["id"] != expected_id
            or not _is_text(result["name"])
            or result["state"] not in expected_states
            or result["move_type"] is not None
            or result["source_id"] is not None
            or (
                expected_line_count is not None
                and len(result["line_ids"]) != expected_line_count
            )
            or result["partial_reconcile_ids"]
            or result["full_reconcile_id"] is not None
            or result["reconciled"]
        ):
            raise _failed("Odoo returned a mismatched payment-term result.")
        return deepcopy(result)
    if capability_id == "period.accrual.generate":
        if (
            result["model"] != "account.move"
            or not _is_text(result["name"])
            or result["state"] != "posted"
            or result["move_type"] != "entry"
            or not _valid_id(result["source_id"])
            or len(result["line_ids"]) < 2
            or result["partial_reconcile_ids"]
            or result["full_reconcile_id"] is not None
            or result["reconciled"]
        ):
            raise _failed("Odoo returned a mismatched period-accrual result.")
        return deepcopy(result)
    if capability_id in _ORDER_WRITE_CAPABILITIES:
        sale = capability_id.startswith("sale.order.")
        expected_model = "sale.order" if sale else "purchase.order"
        expected_id = (
            result["id"]
            if capability_id in _ORDER_CREATE_CAPABILITIES
            else parameters["order_id"]
        )
        all_states = (
            {"draft", "sent", "sale", "cancel"}
            if sale
            else {"draft", "sent", "to approve", "purchase", "cancel"}
        )
        if capability_id.endswith(".confirm"):
            expected_states = {"sale"} if sale else {"purchase", "to approve"}
        elif capability_id.endswith(".cancel"):
            expected_states = {"cancel"}
        elif capability_id.endswith(".reset_to_draft"):
            expected_states = {"draft"}
        elif idempotent_replay:
            expected_states = all_states
        else:
            expected_states = {"draft"}
        expected_line_count = (
            len(parameters["lines"])
            if capability_id
            in _ORDER_CREATE_CAPABILITIES | _ORDER_LINE_REPLACEMENT_CAPABILITIES
            else None
        )
        if (
            result["model"] != expected_model
            or result["id"] != expected_id
            or not _is_text(result["name"])
            or result["state"] not in expected_states
            or result["move_type"] is not None
            or not _valid_id(result["source_id"])
            or (
                expected_line_count is not None
                and len(result["line_ids"]) != expected_line_count
            )
            or result["partial_reconcile_ids"]
            or result["full_reconcile_id"] is not None
            or result["reconciled"]
        ):
            raise _failed("Odoo returned a mismatched order result.")
        return deepcopy(result)
    configuration_models = {
        **{
            capability: "account.account"
            for capability in _ACCOUNT_CONFIGURATION_WRITE_CAPABILITIES
        },
        **{
            capability: "account.journal"
            for capability in _JOURNAL_CONFIGURATION_WRITE_CAPABILITIES
        },
        **{
            capability: "account.tax"
            for capability in _TAX_CONFIGURATION_WRITE_CAPABILITIES
        },
    }
    if capability_id in configuration_models:
        primary_field = (
            "account_id"
            if capability_id.startswith("account.account.")
            else "journal_id"
            if capability_id.startswith("journal.")
            else "tax_id"
        )
        expected_id = (
            result["id"]
            if capability_id.endswith(".create")
            else parameters[primary_field]
        )
        expected_states = (
            {"archived"}
            if capability_id.endswith(".archive")
            else {"active"}
            if capability_id.endswith(".restore")
            else {"active", "archived"}
            if capability_id.endswith(".update") or idempotent_replay
            else {"active"}
        )
        if (
            result["model"] != configuration_models[capability_id]
            or result["id"] != expected_id
            or not _is_text(result["name"])
            or result["state"] not in expected_states
            or result["move_type"] is not None
            or result["source_id"] is not None
            or result["line_ids"]
            or result["partial_reconcile_ids"]
            or result["full_reconcile_id"] is not None
            or result["reconciled"]
        ):
            raise _failed("Odoo returned a mismatched accounting-configuration result.")
        return deepcopy(result)
    if capability_id in _PARTNER_WRITE_CAPABILITIES:
        expected_id = (
            result["id"]
            if capability_id == "partner.create"
            else parameters["partner_id"]
        )
        expected_states = (
            {"archived"}
            if capability_id == "partner.archive"
            else {"active"}
            if capability_id == "partner.restore"
            else {"active", "archived"}
        )
        if (
            result["model"] != "res.partner"
            or result["id"] != expected_id
            or not _is_text(result["name"])
            or result["state"] not in expected_states
            or result["move_type"] is not None
            or result["source_id"] is not None
            or result["line_ids"]
            or result["partial_reconcile_ids"]
            or result["full_reconcile_id"] is not None
            or result["reconciled"]
        ):
            raise _failed("Odoo returned a mismatched partner result.")
        return deepcopy(result)
    if capability_id in _PARTNER_BANK_WRITE_CAPABILITIES:
        expected_id = (
            result["id"]
            if capability_id == "partner.bank_account.create"
            else parameters["partner_bank_id"]
        )
        expected_states = (
            {"archived"}
            if capability_id == "partner.bank_account.archive"
            else {"active"}
            if capability_id == "partner.bank_account.restore"
            else {"active", "archived"}
        )
        source_matches = (
            result["source_id"] == parameters["partner_id"]
            if capability_id == "partner.bank_account.create"
            else _valid_id(result["source_id"])
        )
        if (
            result["model"] != "res.partner.bank"
            or result["id"] != expected_id
            or not _is_text(result["name"])
            or result["state"] not in expected_states
            or result["move_type"] is not None
            or not source_matches
            or result["line_ids"]
            or result["partial_reconcile_ids"]
            or result["full_reconcile_id"] is not None
            or result["reconciled"]
        ):
            raise _failed("Odoo returned a mismatched partner bank-account result.")
        return deepcopy(result)
    if capability_id in _ANALYTIC_PLAN_WRITE_CAPABILITIES:
        expected_id = (
            result["id"]
            if capability_id == "analytic.plan.create"
            else parameters["plan_id"]
        )
        expected_source = (
            parameters["parent_plan_id"]
            if capability_id == "analytic.plan.create"
            else None
        )
        if (
            result["model"] != "account.analytic.plan"
            or result["id"] != expected_id
            or not _is_text(result["name"])
            or result["state"] != "active"
            or result["move_type"] is not None
            or (
                result["source_id"] != expected_source
                if expected_source is not None
                else not _valid_id(result["source_id"])
            )
            or result["line_ids"]
            or result["partial_reconcile_ids"]
            or result["full_reconcile_id"] is not None
            or result["reconciled"]
        ):
            raise _failed("Odoo returned a mismatched analytic-plan result.")
        return deepcopy(result)
    if capability_id in _ANALYTIC_ACCOUNT_WRITE_CAPABILITIES:
        expected_id = (
            result["id"]
            if capability_id == "analytic.account.create"
            else parameters["analytic_account_id"]
        )
        source_matches = (
            result["source_id"] == parameters["plan_id"]
            if capability_id == "analytic.account.create"
            else _valid_id(result["source_id"])
        )
        if capability_id == "analytic.account.archive":
            allowed_states = {"archived"}
        elif capability_id == "analytic.account.restore":
            allowed_states = {"active"}
        elif capability_id == "analytic.account.create":
            allowed_states = (
                {"active", "archived"} if idempotent_replay else {"active"}
            )
        else:
            allowed_states = (
                {"active" if parameters["changes"]["active"] else "archived"}
                if "active" in parameters["changes"]
                else {"active", "archived"}
            )
        if (
            result["model"] != "account.analytic.account"
            or result["id"] != expected_id
            or not _is_text(result["name"])
            or result["state"] not in allowed_states
            or result["move_type"] is not None
            or not source_matches
            or result["line_ids"]
            or result["partial_reconcile_ids"]
            or result["full_reconcile_id"] is not None
            or result["reconciled"]
        ):
            raise _failed("Odoo returned a mismatched analytic-account result.")
        return deepcopy(result)
    if capability_id in _ANALYTIC_LINE_WRITE_CAPABILITIES:
        expected_id = (
            result["id"]
            if capability_id == "analytic.line.create"
            else parameters["analytic_line_id"]
        )
        expected_state = (
            "deleted" if capability_id == "analytic.line.delete" else "manual"
        )
        if (
            result["model"] != "account.analytic.line"
            or result["id"] != expected_id
            or not _is_text(result["name"])
            or result["state"] != expected_state
            or result["move_type"] is not None
            or not _valid_id(result["source_id"])
            or result["line_ids"]
            or result["partial_reconcile_ids"]
            or result["full_reconcile_id"] is not None
            or result["reconciled"]
        ):
            raise _failed("Odoo returned a mismatched analytic-line result.")
        return deepcopy(result)
    if capability_id in _BUDGET_WRITE_CAPABILITIES:
        expected_id = (
            result["id"]
            if capability_id == "budget.create"
            else parameters["budget_id"]
        )
        expected_states = (
            {"draft", "confirmed", "revised", "done", "canceled"}
            if capability_id == "budget.create" and idempotent_replay
            else {
                "budget.create": {"draft"},
                "budget.update_draft": {"draft"},
                "budget.lines.replace": {"draft"},
                "budget.confirm": {"confirmed", "revised"},
                "budget.reset_to_draft": {"draft"},
                "budget.cancel": {"canceled"},
                "budget.mark_done": {"done"},
            }[capability_id]
        )
        if (
            result["model"] != "budget.analytic"
            or result["id"] != expected_id
            or not _is_text(result["name"])
            or result["state"] not in expected_states
            or result["move_type"] is not None
            or result["source_id"] is not None
            or result["partial_reconcile_ids"]
            or result["full_reconcile_id"] is not None
            or result["reconciled"]
            or (
                capability_id == "budget.create"
                and not idempotent_replay
                and result["line_ids"]
            )
            or (
                capability_id == "budget.lines.replace"
                and len(result["line_ids"]) != len(parameters["lines"])
            )
        ):
            raise _failed("Odoo returned a mismatched budget result.")
        return deepcopy(result)
    if capability_id in _PAYMENT_DRAFT_CAPABILITIES:
        expected_id = (
            result["id"]
            if capability_id == "payment.create"
            else parameters["payment_id"]
        )
        if (
            result["model"] != "account.payment"
            or result["id"] != expected_id
            or result["state"] != "draft"
            or result["move_type"] is not None
            or result["source_id"] is not None
            or result["partial_reconcile_ids"]
            or result["full_reconcile_id"] is not None
            or result["reconciled"]
        ):
            raise _failed("Odoo returned a mismatched draft-payment result.")
        return deepcopy(result)
    if capability_id in _BANK_RECONCILIATION_WRITE_CAPABILITIES:
        if (
            result["model"] != "account.bank.statement.line"
            or result["id"] != parameters["transaction_id"]
            or result["state"] != "posted"
            or result["move_type"] != "entry"
            or not _valid_id(result["source_id"])
            or not result["line_ids"]
        ):
            raise _failed("Odoo returned a mismatched bank-transaction result.")
        return deepcopy(result)
    if capability_id in _DOCUMENT_LIFECYCLE_CAPABILITIES:
        expected_move_types = (
            _INVOICE_MOVE_TYPES
            if capability_id in _INVOICE_LIFECYCLE_CAPABILITIES
            else {"entry"}
        )
        expected_states = (
            {"cancel"}
            if capability_id in {"invoice.cancel", "journal_entry.cancel"}
            else {"draft"}
            if capability_id
            in {"invoice.reset_to_draft", "journal_entry.reset_to_draft"}
            else {"draft", "posted", "cancel"}
            if idempotent_replay
            else {"draft"}
        )
        if (
            result["model"] != "account.move"
            or result["id"] != parameters["move_id"]
            or result["move_type"] not in expected_move_types
            or result["state"] not in expected_states
            or result["source_id"] is not None
        ):
            raise _failed("Odoo returned a mismatched document-lifecycle result.")
        return deepcopy(result)
    if capability_id == "invoice.duplicate":
        if (
            result["model"] != "account.move"
            or not _valid_id(result["id"])
            or result["id"] == parameters["move_id"]
            or result["state"] != "draft"
            or result["move_type"] not in _INVOICE_MOVE_TYPES
            or result["source_id"] != parameters["move_id"]
        ):
            raise _failed("Odoo returned a mismatched duplicated invoice result.")
        return deepcopy(result)
    if capability_id == "invoice.type.switch":
        if (
            result["model"] != "account.move"
            or result["id"] != parameters["move_id"]
            or result["state"] != "draft"
            or result["move_type"] != parameters["target_move_type"]
            or result["source_id"] != parameters["move_id"]
        ):
            raise _failed("Odoo returned a mismatched switched invoice result.")
        return deepcopy(result)
    if (
        capability_id
        in {"asset.create", "asset.validate"} | _ASSET_LIFECYCLE_CAPABILITIES
    ):
        expected_states = (
            _ASSET_STATES
            if capability_id == "asset.create" and idempotent_replay
            else {"draft"}
            if capability_id == "asset.create"
            else {"open"}
            if capability_id == "asset.validate"
            else {
                "asset.cancel": "cancelled",
                "asset.dispose": "close",
                "asset.pause": "paused",
            }[capability_id]
        )
        if isinstance(expected_states, str):
            expected_states = {expected_states}
        if (
            result["model"] != "account.asset"
            or not _is_text(result["name"])
            or result["state"] not in expected_states
            or result["move_type"] is not None
            or result["source_id"] is not None
            or result["partial_reconcile_ids"]
            or result["full_reconcile_id"] is not None
            or result["reconciled"]
            or (
                capability_id == "asset.create"
                and not idempotent_replay
                and result["line_ids"]
            )
            or (
                capability_id != "asset.create"
                and result["id"] != parameters["asset_id"]
            )
        ):
            raise _failed("Odoo returned a mismatched asset write result.")
        return deepcopy(result)

    if capability_id in _MOVE_PAIR_CAPABILITIES:
        allowed_states = (
            {"posted"}
            if capability_id == "multicurrency.revaluation.generate_entries"
            else {"draft", "posted"}
        )
        if (
            result["model"] != "account.move"
            or result["state"] not in allowed_states
            or result["move_type"] != "entry"
            or not _valid_id(result["source_id"])
            or result["source_id"] == result["id"]
            or not result["line_ids"]
            or result["partial_reconcile_ids"]
            or result["full_reconcile_id"] is not None
            or result["reconciled"]
        ):
            raise _failed("Odoo returned a mismatched generated move pair.")
        return deepcopy(result)

    if capability_id in _TRANSFER_CAPABILITIES:
        expected_source_id = (
            parameters["transfer_model_id"]
            if capability_id == "period.transfer.run"
            else result["source_id"]
        )
        if (
            result["model"] != "account.move"
            or result["state"] not in {"draft", "posted"}
            or result["move_type"] != "entry"
            or not _valid_id(result["source_id"])
            or result["source_id"] != expected_source_id
            or not result["line_ids"]
            or result["partial_reconcile_ids"]
            or result["full_reconcile_id"] is not None
            or result["reconciled"]
        ):
            raise _failed("Odoo returned a mismatched period-transfer result.")
        return deepcopy(result)
    expected_model = (
        "account.payment"
        if capability_id
        in _PAYMENT_REGISTER_CAPABILITIES | {"payment.cancel", "payment.post"}
        else (
            "account.bank.statement.line"
            if capability_id == "bank.transaction.record"
            else "account.move"
        )
    )
    if result["model"] != expected_model:
        raise _failed("Odoo returned a core-write result from the wrong model.")

    if capability_id == "bank.transaction.record":
        if (
            result["state"] != "posted"
            or result["move_type"] != "entry"
            or not _valid_id(result["source_id"])
            or not result["line_ids"]
        ):
            raise _failed(
                "Odoo returned a result inconsistent with the requested write."
            )
        return deepcopy(result)

    if (
        capability_id in {"invoice.post", "journal_entry.post"}
        and result["id"] != parameters["move_id"]
    ):
        raise _failed("Odoo returned a mismatched posted move.")
    if capability_id == "payment.cancel" and result["id"] != parameters["payment_id"]:
        raise _failed("Odoo returned a mismatched canceled payment.")
    if capability_id == "payment.post" and result["id"] != parameters["payment_id"]:
        raise _failed("Odoo returned a mismatched posted payment.")

    if capability_id == "customer_invoice.create":
        expected_move_types = {"out_invoice"}
        expected_states = (
            {"draft", "posted", "cancel"} if idempotent_replay else {"draft"}
        )
        expected_source_id = None
    elif capability_id == "vendor_bill.create":
        expected_move_types = {"in_invoice"}
        expected_states = (
            {"draft", "posted", "cancel"} if idempotent_replay else {"draft"}
        )
        expected_source_id = None
    elif capability_id == "invoice.post":
        expected_move_types = _INVOICE_MOVE_TYPES
        expected_states = {"posted"}
        expected_source_id = None
    elif capability_id == "journal_entry.create":
        expected_move_types = {"entry"}
        expected_states = (
            {"draft", "posted", "cancel"} if idempotent_replay else {"draft"}
        )
        expected_source_id = None
    elif capability_id == "journal_entry.post":
        expected_move_types = {"entry"}
        expected_states = {"posted"}
        expected_source_id = None
    elif capability_id == "journal_entry.reverse":
        expected_move_types = {"entry"}
        expected_states = (
            {"draft", "posted", "cancel"} if idempotent_replay else {"draft", "posted"}
        )
        expected_source_id = parameters["move_id"]
    elif capability_id == "customer_credit_note.create":
        expected_move_types = {"out_refund"}
        expected_states = (
            {"draft", "posted", "cancel"} if idempotent_replay else {"draft"}
        )
        expected_source_id = parameters["move_id"]
    elif capability_id == "vendor_refund.create":
        expected_move_types = {"in_refund"}
        expected_states = (
            {"draft", "posted", "cancel"} if idempotent_replay else {"draft"}
        )
        expected_source_id = parameters["move_id"]
    elif capability_id in _PAYMENT_REGISTER_CAPABILITIES:
        expected_move_types = {None}
        expected_states = {"in_process", "paid"}
        expected_source_id = parameters.get("move_id")
    elif capability_id == "payment.post":
        expected_move_types = {None}
        expected_states = {"in_process", "paid"}
        expected_source_id = None
    else:
        expected_move_types = {None}
        expected_states = {"canceled"}
        expected_source_id = None
    if (
        result["move_type"] not in expected_move_types
        or result["state"] not in expected_states
        or result["source_id"] != expected_source_id
        or (
            capability_id in _PAYMENT_REGISTER_CAPABILITIES
            and "move_ids" in parameters
            and (not result["reconciled"] or not result["line_ids"])
        )
    ):
        raise _failed("Odoo returned a result inconsistent with the requested write.")
    return deepcopy(result)


def _validate_batch_result(
    capability_id: str,
    parameters: dict[str, Any],
    result: Any,
    *,
    company_id: int,
    idempotent_replay: bool,
) -> dict[str, Any]:
    if not _valid_batch_result_shape(result):
        raise _failed("Odoo returned a malformed core-write batch result.")
    singular_field, batch_field = (
        ("move_id", "move_ids")
        if capability_id in _MOVE_BATCH_LIFECYCLE_CAPABILITIES
        else ("payment_id", "payment_ids")
    )
    expected_ids = parameters[batch_field]
    if (
        result["processed_count"] != len(expected_ids)
        or [item["id"] for item in result["items"]] != expected_ids
    ):
        raise _failed("Odoo returned a mismatched core-write batch result.")
    return {
        "items": [
            _validate_result(
                capability_id,
                {singular_field: target_id},
                item,
                company_id=company_id,
                idempotent_replay=idempotent_replay,
            )
            for target_id, item in zip(expected_ids, result["items"], strict=True)
        ],
        "processed_count": result["processed_count"],
    }


def execute_core_write(
    port: CoreWritePort,
    capability_id: str,
    request: dict[str, Any],
    idempotency_key: str,
    confirmation: str,
) -> dict[str, Any]:
    """Execute one validated fixed write and fail closed on runtime drift."""

    _, context, parameters = validate_core_write_request(capability_id, request)
    _validate_idempotency_and_confirmation(
        capability_id,
        parameters,
        context["company_id"],
        idempotency_key,
        confirmation,
    )
    try:
        page = port.execute(
            capability_id=capability_id,
            company_id=context["company_id"],
            idempotency_key=idempotency_key,
            confirmation=confirmation,
            parameters=deepcopy(parameters),
        )
    except ValueError as exc:
        raise _failed("The Odoo bridge returned an invalid core-write result.") from exc
    idempotent_replay, result = _validate_page(port, page)
    if result is None:
        raise CoreWriteError(
            "record_not_found",
            "A target or referenced accounting record was not found.",
            exit_code=4,
        )
    validated_result = (
        _validate_batch_result(
            capability_id,
            parameters,
            result,
            company_id=context["company_id"],
            idempotent_replay=idempotent_replay,
        )
        if capability_id in _BATCH_LIFECYCLE_CAPABILITIES
        and ("move_ids" in parameters or "payment_ids" in parameters)
        else _validate_result(
            capability_id,
            parameters,
            result,
            company_id=context["company_id"],
            idempotent_replay=idempotent_replay,
        )
    )
    return {
        "idempotent_replay": idempotent_replay,
        "result": validated_result,
    }
