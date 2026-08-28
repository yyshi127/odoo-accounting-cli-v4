"""Odoo-side runtime for fixed high-frequency accounting object reads."""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import date as date_type
from decimal import Decimal, InvalidOperation
from typing import Any

ACTION = "accounting.core_object.read"
CAPABILITY_IDS = frozenset(
    {
        "account.account.get",
        "journal.get",
        "tax.get",
        "payment_term.get",
        "currency.get",
        "partner.accounting.get",
        "partner.search",
        "partner.get",
        "bank.transaction.get",
        "journal_item.search",
        "journal_item.get",
        "payment.method.list",
        "reconciliation.model.list",
        "product.search",
        "product.get",
        "analytic.plan.list",
        "analytic.plan.get",
        "analytic.account.search",
        "analytic.account.get",
        "fiscal_position.search",
        "fiscal_position.get",
        "account.tag.list",
        "account.tag.get",
        "tax.group.list",
        "tax.group.get",
        "payment.method.get",
        "reconciliation.model.get",
        "cash_rounding.list",
        "cash_rounding.get",
        "journal.group.list",
        "journal.group.get",
        "incoterm.list",
        "incoterm.get",
        "partner.bank_account.search",
        "partner.bank_account.get",
        "bank.statement.search",
        "bank.statement.get",
        "reconciliation.partial.list",
        "reconciliation.partial.get",
        "reconciliation.full.list",
        "reconciliation.full.get",
        "analytic.line.search",
        "analytic.line.get",
        "analytic.distribution_model.list",
        "analytic.distribution_model.get",
        "analytic.applicability.list",
        "analytic.applicability.get",
        "budget.search",
        "budget.get",
        "budget.line.list",
        "budget.line.get",
    }
)

_GET_IDS = {
    "account.account.get": ("account.account", "account_id"),
    "journal.get": ("account.journal", "journal_id"),
    "tax.get": ("account.tax", "tax_id"),
    "payment_term.get": ("account.payment.term", "payment_term_id"),
    "currency.get": ("res.currency", "currency_id"),
    "partner.accounting.get": ("res.partner", "partner_id"),
    "partner.get": ("res.partner", "partner_id"),
    "bank.transaction.get": ("account.bank.statement.line", "transaction_id"),
    "journal_item.get": ("account.move.line", "line_id"),
    "product.get": ("product.product", "product_id"),
    "analytic.plan.get": ("account.analytic.plan", "plan_id"),
    "analytic.account.get": ("account.analytic.account", "analytic_account_id"),
    "fiscal_position.get": ("account.fiscal.position", "fiscal_position_id"),
    "account.tag.get": ("account.account.tag", "tag_id"),
    "tax.group.get": ("account.tax.group", "tax_group_id"),
    "payment.method.get": (
        "account.payment.method.line",
        "payment_method_line_id",
    ),
    "reconciliation.model.get": (
        "account.reconcile.model",
        "reconciliation_model_id",
    ),
    "cash_rounding.get": ("account.cash.rounding", "cash_rounding_id"),
    "journal.group.get": ("account.journal.group", "journal_group_id"),
    "incoterm.get": ("account.incoterms", "incoterm_id"),
    "partner.bank_account.get": ("res.partner.bank", "partner_bank_id"),
    "bank.statement.get": ("account.bank.statement", "bank_statement_id"),
    "reconciliation.partial.get": (
        "account.partial.reconcile",
        "partial_reconcile_id",
    ),
    "reconciliation.full.get": (
        "account.full.reconcile",
        "full_reconcile_id",
    ),
    "analytic.line.get": ("account.analytic.line", "analytic_line_id"),
    "analytic.distribution_model.get": (
        "account.analytic.distribution.model",
        "distribution_model_id",
    ),
    "analytic.applicability.get": (
        "account.analytic.applicability",
        "applicability_id",
    ),
    "budget.get": ("budget.analytic", "budget_id"),
    "budget.line.get": ("budget.line", "budget_line_id"),
}
_PAGED_REFERENCE_MODELS = {
    "partner.search": "res.partner",
    "product.search": "product.product",
    "analytic.plan.list": "account.analytic.plan",
    "analytic.account.search": "account.analytic.account",
    "fiscal_position.search": "account.fiscal.position",
    "account.tag.list": "account.account.tag",
    "tax.group.list": "account.tax.group",
    "cash_rounding.list": "account.cash.rounding",
    "journal.group.list": "account.journal.group",
    "incoterm.list": "account.incoterms",
    "partner.bank_account.search": "res.partner.bank",
    "bank.statement.search": "account.bank.statement",
    "reconciliation.partial.list": "account.partial.reconcile",
    "reconciliation.full.list": "account.full.reconcile",
}
_REFERENCE_KINDS = {
    "partner.search": "partner",
    "partner.get": "partner",
    "product.search": "product",
    "product.get": "product",
    "analytic.plan.list": "plan",
    "analytic.plan.get": "plan",
    "analytic.account.search": "analytic",
    "analytic.account.get": "analytic",
    "fiscal_position.search": "fiscal_position",
    "fiscal_position.get": "fiscal_position",
    "account.tag.list": "tag",
    "account.tag.get": "tag",
    "tax.group.list": "tax_group",
    "tax.group.get": "tax_group",
    "cash_rounding.list": "cash_rounding",
    "cash_rounding.get": "cash_rounding",
    "journal.group.list": "journal_group",
    "journal.group.get": "journal_group",
    "incoterm.list": "incoterm",
    "incoterm.get": "incoterm",
    "partner.bank_account.search": "partner_bank",
    "partner.bank_account.get": "partner_bank",
    "bank.statement.search": "bank_statement",
    "bank.statement.get": "bank_statement",
    "reconciliation.partial.list": "partial_reconcile",
    "reconciliation.partial.get": "partial_reconcile",
    "reconciliation.full.list": "full_reconcile",
    "reconciliation.full.get": "full_reconcile",
}
_REFERENCE_FIELDS = {
    "partner": (
        "id",
        "name",
        "display_name",
        "company_type",
        "active",
        "vat",
        "ref",
        "email",
        "phone",
        "mobile",
        "street",
        "street2",
        "city",
        "zip",
        "state_id",
        "country_id",
        "lang",
        "company_id",
        "parent_id",
        "customer_rank",
        "supplier_rank",
    ),
    "product": (
        "id",
        "name",
        "default_code",
        "active",
        "type",
        "is_storable",
        "product_tmpl_id",
        "categ_id",
        "uom_id",
        "company_id",
        "currency_id",
        "standard_price",
        "list_price",
    ),
    "plan": ("id", "name", "complete_name", "parent_id", "color"),
    "analytic": (
        "id",
        "name",
        "code",
        "active",
        "plan_id",
        "partner_id",
        "company_id",
        "currency_id",
        "balance",
    ),
    "fiscal_position": (
        "id",
        "name",
        "active",
        "auto_apply",
        "vat_required",
        "country_id",
        "country_group_id",
        "state_ids",
        "company_id",
        "foreign_vat",
    ),
    "tag": ("id", "name", "applicability", "active", "color", "country_id"),
    "tax_group": (
        "id",
        "name",
        "sequence",
        "country_id",
        "preceding_subtotal",
        "company_id",
    ),
    "cash_rounding": (
        "id",
        "name",
        "rounding",
        "strategy",
        "rounding_method",
        "profit_account_id",
        "loss_account_id",
    ),
    "journal_group": (
        "id",
        "name",
        "sequence",
        "company_id",
        "excluded_journal_ids",
    ),
    "incoterm": ("id", "code", "name", "active"),
    "partner_bank": (
        "id",
        "acc_number",
        "acc_holder_name",
        "acc_type",
        "active",
        "sequence",
        "partner_id",
        "allow_out_payment",
        "bank_id",
        "currency_id",
        "company_id",
        "journal_id",
    ),
    "bank_statement": (
        "id",
        "name",
        "reference",
        "date",
        "company_id",
        "journal_id",
        "currency_id",
        "balance_start",
        "balance_end",
        "balance_end_real",
        "is_complete",
        "is_valid",
        "problem_description",
        "line_ids",
    ),
    "partial_reconcile": (
        "id",
        "company_id",
        "max_date",
        "amount",
        "company_currency_id",
        "debit_amount_currency",
        "debit_currency_id",
        "credit_amount_currency",
        "credit_currency_id",
        "debit_move_id",
        "credit_move_id",
        "full_reconcile_id",
        "exchange_move_id",
    ),
    "full_reconcile": (
        "id",
        "partial_reconcile_ids",
        "reconciled_line_ids",
    ),
}
_ANALYTIC_LINE_FIELDS = (
    "id",
    "date",
    "name",
    "ref",
    "amount",
    "unit_amount",
    "company_id",
    "currency_id",
    "partner_id",
    "product_id",
    "product_uom_id",
    "general_account_id",
    "move_line_id",
)
_DISTRIBUTION_MODEL_FIELDS = (
    "id",
    "sequence",
    "company_id",
    "account_prefix",
    "partner_id",
    "partner_category_id",
    "product_id",
    "product_categ_id",
    "analytic_distribution",
    "distribution_analytic_account_ids",
)
_APPLICABILITY_FIELDS = (
    "id",
    "analytic_plan_id",
    "business_domain",
    "applicability",
    "company_id",
    "account_prefix",
    "product_categ_id",
)
_BUDGET_FIELDS = (
    "id",
    "name",
    "date_from",
    "date_to",
    "state",
    "budget_type",
    "company_id",
    "user_id",
    "parent_id",
)
_BUDGET_LINE_FIELDS = (
    "id",
    "sequence",
    "budget_analytic_id",
    "date_from",
    "date_to",
    "budget_amount",
    "achieved_amount",
    "achieved_percentage",
    "theoritical_amount",
    "theoritical_percentage",
    "is_above_budget",
    "budget_analytic_state",
    "currency_id",
    "company_id",
)
_ANALYTIC_COLUMN_PATTERN = re.compile(r"^(?:account_id|x_plan[1-9][0-9]*_id)$")
_PARTNER_REF_MARKER_SUFFIX = re.compile(r"(?:^| )\[ODACV4:[0-9a-f]{64}\]$")
_REQUIRED_MODELS = {
    "account.account.get": ("res.company", "account.account"),
    "journal.get": ("res.company", "account.journal", "res.currency"),
    "tax.get": ("res.company", "account.tax", "account.tax.group"),
    "payment_term.get": (
        "res.company",
        "account.payment.term",
        "account.payment.term.line",
    ),
    "currency.get": ("res.company", "res.currency"),
    "partner.accounting.get": ("res.company", "res.partner", "account.account"),
    "partner.search": (
        "res.company",
        "res.partner",
        "res.country.state",
        "res.country",
    ),
    "partner.get": (
        "res.company",
        "res.partner",
        "res.country.state",
        "res.country",
    ),
    "bank.transaction.get": (
        "res.company",
        "account.bank.statement.line",
        "account.move",
        "account.journal",
        "res.partner",
        "res.currency",
        "account.payment",
    ),
    "journal_item.search": (
        "res.company",
        "account.move.line",
        "account.move",
        "account.account",
        "account.journal",
        "res.partner",
        "res.currency",
    ),
    "journal_item.get": (
        "res.company",
        "account.move.line",
        "account.move",
        "account.account",
        "account.journal",
        "res.partner",
        "res.currency",
    ),
    "payment.method.list": (
        "res.company",
        "account.payment.method.line",
        "account.payment.method",
        "account.journal",
        "account.account",
    ),
    "payment.method.get": (
        "res.company",
        "account.payment.method.line",
        "account.payment.method",
        "account.journal",
        "account.account",
    ),
    "reconciliation.model.list": ("res.company", "account.reconcile.model"),
    "reconciliation.model.get": ("res.company", "account.reconcile.model"),
    "cash_rounding.list": (
        "res.company",
        "account.cash.rounding",
        "account.account",
    ),
    "cash_rounding.get": (
        "res.company",
        "account.cash.rounding",
        "account.account",
    ),
    "journal.group.list": (
        "res.company",
        "account.journal.group",
        "account.journal",
    ),
    "journal.group.get": (
        "res.company",
        "account.journal.group",
        "account.journal",
    ),
    "incoterm.list": ("res.company", "account.incoterms"),
    "incoterm.get": ("res.company", "account.incoterms"),
    "product.search": (
        "res.company",
        "product.product",
        "product.template",
        "product.category",
        "uom.uom",
        "res.currency",
    ),
    "product.get": (
        "res.company",
        "product.product",
        "product.template",
        "product.category",
        "uom.uom",
        "res.currency",
    ),
    "analytic.plan.list": ("res.company", "account.analytic.plan"),
    "analytic.plan.get": ("res.company", "account.analytic.plan"),
    "analytic.account.search": (
        "res.company",
        "account.analytic.account",
        "account.analytic.plan",
        "account.analytic.line",
        "res.partner",
        "res.currency",
    ),
    "analytic.account.get": (
        "res.company",
        "account.analytic.account",
        "account.analytic.plan",
        "account.analytic.line",
        "res.partner",
        "res.currency",
    ),
    "fiscal_position.search": (
        "res.company",
        "account.fiscal.position",
        "res.country",
        "res.country.group",
        "res.country.state",
    ),
    "fiscal_position.get": (
        "res.company",
        "account.fiscal.position",
        "res.country",
        "res.country.group",
        "res.country.state",
    ),
    "account.tag.list": ("res.company", "account.account.tag", "res.country"),
    "account.tag.get": ("res.company", "account.account.tag", "res.country"),
    "tax.group.list": ("res.company", "account.tax.group", "res.country"),
    "tax.group.get": ("res.company", "account.tax.group", "res.country"),
    "partner.bank_account.search": (
        "res.company",
        "res.partner.bank",
        "res.partner",
        "res.bank",
        "res.currency",
        "account.journal",
    ),
    "partner.bank_account.get": (
        "res.company",
        "res.partner.bank",
        "res.partner",
        "res.bank",
        "res.currency",
        "account.journal",
    ),
    "bank.statement.search": (
        "res.company",
        "account.bank.statement",
        "account.bank.statement.line",
        "account.journal",
        "res.currency",
    ),
    "bank.statement.get": (
        "res.company",
        "account.bank.statement",
        "account.bank.statement.line",
        "account.journal",
        "res.currency",
    ),
    "reconciliation.partial.list": (
        "res.company",
        "account.partial.reconcile",
        "account.move.line",
        "account.move",
        "res.currency",
    ),
    "reconciliation.partial.get": (
        "res.company",
        "account.partial.reconcile",
        "account.move.line",
        "account.move",
        "res.currency",
    ),
    "reconciliation.full.list": (
        "res.company",
        "account.full.reconcile",
        "account.partial.reconcile",
        "account.move.line",
    ),
    "reconciliation.full.get": (
        "res.company",
        "account.full.reconcile",
        "account.partial.reconcile",
        "account.move.line",
    ),
    "analytic.line.search": (
        "res.company",
        "account.analytic.line",
        "account.analytic.account",
        "res.partner",
        "res.currency",
        "product.product",
        "uom.uom",
        "account.account",
        "account.move.line",
    ),
    "analytic.line.get": (
        "res.company",
        "account.analytic.line",
        "account.analytic.account",
        "res.partner",
        "res.currency",
        "product.product",
        "uom.uom",
        "account.account",
        "account.move.line",
    ),
    "analytic.distribution_model.list": (
        "res.company",
        "account.analytic.distribution.model",
        "account.analytic.account",
        "res.partner",
        "res.partner.category",
        "product.product",
        "product.category",
    ),
    "analytic.distribution_model.get": (
        "res.company",
        "account.analytic.distribution.model",
        "account.analytic.account",
        "res.partner",
        "res.partner.category",
        "product.product",
        "product.category",
    ),
    "analytic.applicability.list": (
        "res.company",
        "account.analytic.applicability",
        "account.analytic.plan",
        "product.category",
    ),
    "analytic.applicability.get": (
        "res.company",
        "account.analytic.applicability",
        "account.analytic.plan",
        "product.category",
    ),
    "budget.search": ("res.company", "budget.analytic", "res.users"),
    "budget.get": ("res.company", "budget.analytic", "res.users"),
    "budget.line.list": (
        "res.company",
        "budget.analytic",
        "budget.line",
        "res.currency",
        "account.analytic.plan",
        "account.analytic.account",
    ),
    "budget.line.get": (
        "res.company",
        "budget.analytic",
        "budget.line",
        "res.currency",
        "account.analytic.plan",
        "account.analytic.account",
    ),
}


def _failure(failure_type: Any, code: str, message: str, exit_code: int) -> Exception:
    return failure_type(code, message, exit_code=exit_code)


def _protocol_failure(failure_type: Any) -> Exception:
    return _failure(
        failure_type,
        "bridge_protocol_error",
        "The bridge action payload is invalid.",
        7,
    )


def _runtime_failure(failure_type: Any) -> Exception:
    return _failure(
        failure_type,
        "odoo_runtime_error",
        "The Odoo runtime request failed.",
        7,
    )


def _valid_id(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _valid_limit(value: Any) -> bool:
    return _valid_id(value) and value <= 1001


def _valid_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return date_type.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _optional_date(value: Any) -> bool:
    return value is None or _valid_date(value)


def _reference_id(value: Any) -> int | None:
    if value in (None, False):
        return None
    if _valid_id(value):
        return value
    if isinstance(value, (list, tuple)) and len(value) == 2 and _valid_id(value[0]):
        return value[0]
    return None


def _optional_text(value: Any) -> str | None:
    if value in (None, False, ""):
        return None
    if not isinstance(value, str):
        raise TypeError("invalid text")
    return value


def _date_string(value: Any) -> str:
    text = value.isoformat() if hasattr(value, "isoformat") else value
    if not _valid_date(text):
        raise ValueError("invalid date")
    return text


def _optional_date_string(value: Any) -> str | None:
    return None if value in (None, False) else _date_string(value)


def _decimal_string(value: Any) -> str:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("invalid decimal") from exc
    if not number.is_finite():
        raise ValueError("invalid decimal")
    text = format(number, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return "0" if text in {"-0", ""} else text


def _analytic_column_names(model: Any) -> tuple[str, ...]:
    columns = tuple(
        sorted(
            field_name
            for field_name in model._fields
            if _ANALYTIC_COLUMN_PATTERN.fullmatch(field_name)
        )
    )
    if not columns:
        raise ValueError("missing analytic account columns")
    return columns


def _analytic_account_ids(row: dict[str, Any], columns: tuple[str, ...]) -> list[int]:
    values = [
        account_id
        for column in columns
        if (account_id := _reference_id(row.get(column))) is not None
    ]
    if not values or len(values) != len(set(values)):
        raise ValueError("invalid analytic accounts")
    return sorted(values)


def _analytic_account_references(
    env: Any,
    account_ids: set[int],
    *,
    company_id: int,
    owner_company_id: int | None,
) -> dict[int, dict[str, Any]]:
    accounts = _related_rows(
        env,
        "account.analytic.account",
        account_ids,
        ("name", "company_id", "plan_id"),
    )
    for account in accounts.values():
        account_company_id = _reference_id(account["company_id"])
        if (
            _reference_id(account["plan_id"]) is None
            or account_company_id not in {None, company_id}
            or (owner_company_id is None and account_company_id is not None)
        ):
            raise ValueError("analytic account outside company")
    return accounts


def _named_reference(row: dict[str, Any]) -> dict[str, Any]:
    name = row.get("name", row.get("complete_name"))
    if not _valid_id(row.get("id")) or not isinstance(name, str) or not name.strip():
        raise ValueError("invalid reference")
    return {"id": row["id"], "name": name}


def _coded_reference(row: dict[str, Any]) -> dict[str, Any]:
    if (
        not _valid_id(row.get("id"))
        or not isinstance(row.get("code"), str)
        or not row["code"].strip()
        or not isinstance(row.get("name"), str)
        or not row["name"].strip()
    ):
        raise ValueError("invalid coded reference")
    return {"id": row["id"], "code": row["code"], "name": row["name"]}


def _currency_reference(row: dict[str, Any]) -> dict[str, Any]:
    code = row.get("name")
    if (
        not _valid_id(row.get("id"))
        or not isinstance(code, str)
        or not 1 <= len(code) <= 3
    ):
        raise ValueError("invalid currency")
    return {"id": row["id"], "code": code}


def _related_rows(
    env: Any,
    model_name: str,
    record_ids: set[int],
    fields: tuple[str, ...],
) -> dict[int, dict[str, Any]]:
    if not record_ids:
        return {}
    rows = (
        env[model_name]
        .with_context(active_test=False)
        .search_read(
            [("id", "in", sorted(record_ids))],
            fields=["id", *fields],
            limit=len(record_ids),
            order="id",
        )
    )
    indexed = {
        row["id"]: row
        for row in rows
        if isinstance(row, dict) and _valid_id(row.get("id"))
    }
    if set(indexed) != record_ids or len(indexed) != len(rows):
        raise ValueError("missing related row")
    return indexed


def _sorted_relation_ids(value: Any, *, nonempty: bool = False) -> list[int]:
    if (
        not isinstance(value, list)
        or (nonempty and not value)
        or any(not _valid_id(record_id) for record_id in value)
        or len(value) != len(set(value))
    ):
        raise ValueError("invalid relation ids")
    return sorted(value)


def _company_fiscal_country_id(env: Any, company_id: int) -> int | None:
    rows = (
        env["res.company"]
        .with_context(active_test=False, allowed_company_ids=[company_id])
        .search_read(
            [("id", "=", company_id)],
            fields=["id", "account_fiscal_country_id"],
            limit=1,
            order="id",
        )
    )
    if len(rows) != 1 or rows[0].get("id") != company_id:
        raise ValueError("missing company fiscal country")
    return _reference_id(rows[0].get("account_fiscal_country_id"))


def _scope_domain(env: Any, capability_id: str, company_id: int) -> list[Any]:
    if capability_id == "account.account.get":
        return [("company_ids", "in", [company_id])]
    if capability_id in {
        "journal.get",
        "tax.get",
        "bank.transaction.get",
        "journal_item.get",
        "journal_item.search",
        "payment.method.list",
        "payment.method.get",
        "reconciliation.model.list",
        "reconciliation.model.get",
        "fiscal_position.search",
        "fiscal_position.get",
        "tax.group.list",
        "tax.group.get",
        "bank.statement.search",
        "bank.statement.get",
        "reconciliation.partial.list",
        "reconciliation.partial.get",
        "analytic.line.search",
        "analytic.line.get",
    }:
        return [("company_id", "=", company_id)]
    if capability_id in {
        "payment_term.get",
        "partner.accounting.get",
        "partner.search",
        "partner.get",
        "product.search",
        "product.get",
        "analytic.account.search",
        "analytic.account.get",
        "partner.bank_account.search",
        "partner.bank_account.get",
        "analytic.distribution_model.list",
        "analytic.distribution_model.get",
        "analytic.applicability.list",
        "analytic.applicability.get",
        "budget.search",
        "budget.get",
    }:
        return ["|", ("company_id", "=", False), ("company_id", "=", company_id)]
    if capability_id in {"budget.line.list", "budget.line.get"}:
        return [
            "|",
            ("company_id", "=", False),
            ("company_id", "=", company_id),
            "|",
            ("budget_analytic_id.company_id", "=", False),
            ("budget_analytic_id.company_id", "=", company_id),
        ]
    if capability_id in {
        "reconciliation.full.list",
        "reconciliation.full.get",
    }:
        return [("reconciled_line_ids.company_id", "=", company_id)]
    if capability_id in {"journal.group.list", "journal.group.get"}:
        return ["|", ("company_id", "=", False), ("company_id", "=", company_id)]
    if capability_id in {"account.tag.list", "account.tag.get"}:
        fiscal_country_id = _company_fiscal_country_id(env, company_id)
        if fiscal_country_id is None:
            return [("country_id", "=", False)]
        return [
            "|",
            ("country_id", "=", False),
            ("country_id", "=", fiscal_country_id),
        ]
    return []


def _valid_parameters(capability_id: str, parameters: Any) -> bool:
    if not isinstance(parameters, dict):
        return False
    if capability_id in _GET_IDS:
        id_field = _GET_IDS[capability_id][1]
        return set(parameters) == {id_field} and _valid_id(parameters[id_field])
    if capability_id in {
        "payment.method.list",
        "reconciliation.model.list",
        "analytic.plan.list",
        "account.tag.list",
        "tax.group.list",
        "cash_rounding.list",
        "journal.group.list",
        "incoterm.list",
        "reconciliation.partial.list",
        "reconciliation.full.list",
        "analytic.distribution_model.list",
        "analytic.applicability.list",
    }:
        return (
            set(parameters) == {"after_id", "limit"}
            and (parameters["after_id"] is None or _valid_id(parameters["after_id"]))
            and _valid_limit(parameters["limit"])
        )
    if capability_id == "partner.search":
        if set(parameters) != {
            "query",
            "active",
            "company_type",
            "customer",
            "supplier",
            "after_id",
            "limit",
        }:
            return False
        query = parameters["query"]
        return bool(
            (
                query is None
                or isinstance(query, str)
                and query == query.strip()
                and 1 <= len(query) <= 200
            )
            and (parameters["active"] is None or isinstance(parameters["active"], bool))
            and (
                parameters["company_type"] is None
                or isinstance(parameters["company_type"], str)
                and parameters["company_type"] in {"person", "company"}
            )
            and (
                parameters["customer"] is None
                or isinstance(parameters["customer"], bool)
            )
            and (
                parameters["supplier"] is None
                or isinstance(parameters["supplier"], bool)
            )
            and (parameters["after_id"] is None or _valid_id(parameters["after_id"]))
            and _valid_limit(parameters["limit"])
        )
    if capability_id == "analytic.line.search":
        if set(parameters) != {
            "query",
            "date_from",
            "date_to",
            "analytic_account_id",
            "after_id",
            "limit",
        }:
            return False
        query = parameters["query"]
        return bool(
            (
                query is None
                or isinstance(query, str)
                and 1 <= len(query) <= 200
                and query == query.strip()
            )
            and _optional_date(parameters["date_from"])
            and _optional_date(parameters["date_to"])
            and not (
                parameters["date_from"] is not None
                and parameters["date_to"] is not None
                and parameters["date_from"] > parameters["date_to"]
            )
            and (
                parameters["analytic_account_id"] is None
                or _valid_id(parameters["analytic_account_id"])
            )
            and (parameters["after_id"] is None or _valid_id(parameters["after_id"]))
            and _valid_limit(parameters["limit"])
        )
    if capability_id == "budget.search":
        if set(parameters) != {
            "query",
            "state",
            "budget_type",
            "date_from",
            "date_to",
            "after_id",
            "limit",
        }:
            return False
        query = parameters["query"]
        return bool(
            (
                query is None
                or isinstance(query, str)
                and 1 <= len(query) <= 200
                and query == query.strip()
            )
            and (
                parameters["state"] is None
                or isinstance(parameters["state"], str)
                and parameters["state"]
                in {"draft", "confirmed", "revised", "done", "canceled"}
            )
            and (
                parameters["budget_type"] is None
                or isinstance(parameters["budget_type"], str)
                and parameters["budget_type"] in {"revenue", "expense", "both"}
            )
            and _optional_date(parameters["date_from"])
            and _optional_date(parameters["date_to"])
            and not (
                parameters["date_from"] is not None
                and parameters["date_to"] is not None
                and parameters["date_from"] > parameters["date_to"]
            )
            and (parameters["after_id"] is None or _valid_id(parameters["after_id"]))
            and _valid_limit(parameters["limit"])
        )
    if capability_id == "budget.line.list":
        if set(parameters) != {
            "budget_id",
            "plan_id",
            "analytic_account_id",
            "after_id",
            "limit",
        }:
            return False
        plan_id = parameters["plan_id"]
        analytic_account_id = parameters["analytic_account_id"]
        return bool(
            _valid_id(parameters["budget_id"])
            and (plan_id is None) == (analytic_account_id is None)
            and (
                plan_id is None or _valid_id(plan_id) and _valid_id(analytic_account_id)
            )
            and (parameters["after_id"] is None or _valid_id(parameters["after_id"]))
            and _valid_limit(parameters["limit"])
        )
    if capability_id == "partner.bank_account.search":
        return bool(
            set(parameters) == {"partner_id", "active", "after_id", "limit"}
            and (
                parameters["partner_id"] is None or _valid_id(parameters["partner_id"])
            )
            and (parameters["active"] is None or isinstance(parameters["active"], bool))
            and (parameters["after_id"] is None or _valid_id(parameters["after_id"]))
            and _valid_limit(parameters["limit"])
        )
    if capability_id == "bank.statement.search":
        if set(parameters) != {
            "journal_id",
            "date_from",
            "date_to",
            "after_id",
            "limit",
        }:
            return False
        return bool(
            (parameters["journal_id"] is None or _valid_id(parameters["journal_id"]))
            and _optional_date(parameters["date_from"])
            and _optional_date(parameters["date_to"])
            and not (
                parameters["date_from"] is not None
                and parameters["date_to"] is not None
                and parameters["date_from"] > parameters["date_to"]
            )
            and (parameters["after_id"] is None or _valid_id(parameters["after_id"]))
            and _valid_limit(parameters["limit"])
        )
    if capability_id in {
        "product.search",
        "analytic.account.search",
        "fiscal_position.search",
    }:
        expected = {
            "product.search": {"query", "active", "after_id", "limit"},
            "analytic.account.search": {
                "query",
                "active",
                "plan_id",
                "after_id",
                "limit",
            },
            "fiscal_position.search": {
                "query",
                "active",
                "auto_apply",
                "after_id",
                "limit",
            },
        }[capability_id]
        if set(parameters) != expected:
            return False
        query = parameters["query"]
        if not (
            query is None
            or isinstance(query, str)
            and 1 <= len(query) <= 200
            and query == query.strip()
        ):
            return False
        if parameters["active"] is not None and not isinstance(
            parameters["active"], bool
        ):
            return False
        if parameters["after_id"] is not None and not _valid_id(parameters["after_id"]):
            return False
        if not _valid_limit(parameters["limit"]):
            return False
        if capability_id == "analytic.account.search":
            return parameters["plan_id"] is None or _valid_id(parameters["plan_id"])
        if capability_id == "fiscal_position.search":
            return parameters["auto_apply"] is None or isinstance(
                parameters["auto_apply"], bool
            )
        return True
    if set(parameters) != {
        "date_from",
        "date_to",
        "move_id",
        "account_id",
        "partner_id",
        "journal_id",
        "posted_only",
        "after_id",
        "limit",
    }:
        return False
    if (
        not _optional_date(parameters["date_from"])
        or not _optional_date(parameters["date_to"])
        or (
            parameters["date_from"] is not None
            and parameters["date_to"] is not None
            and parameters["date_from"] > parameters["date_to"]
        )
        or not isinstance(parameters["posted_only"], bool)
        or not _valid_limit(parameters["limit"])
    ):
        return False
    return all(
        parameters[field] is None or _valid_id(parameters[field])
        for field in (
            "move_id",
            "account_id",
            "partner_id",
            "journal_id",
            "after_id",
        )
    )


def _empty_page(
    env: Any,
    *,
    company_visible: bool,
    module_installed: bool,
    access_allowed: bool,
    cursor_found: bool = True,
) -> dict[str, Any]:
    return {
        "user_id": env.uid,
        "company_visible": company_visible,
        "module_installed": module_installed,
        "access_allowed": access_allowed,
        "cursor_found": cursor_found,
        "items": [],
    }


def _available_reference_fields(model: Any, kind: str) -> tuple[str, ...]:
    fields = _REFERENCE_FIELDS[kind]
    available_fields = getattr(model, "_fields", None)
    if (
        kind == "partner"
        and isinstance(available_fields, Mapping)
        and "mobile" not in available_fields
    ):
        return tuple(field for field in fields if field != "mobile")
    return fields


def _raw_get_rows(
    env: Any, capability_id: str, company_id: int, parameters: dict[str, Any]
) -> list[dict[str, Any]]:
    model_name, id_field = _GET_IDS[capability_id]
    raw_model = env[model_name]
    if capability_id in _REFERENCE_KINDS:
        fields = _available_reference_fields(raw_model, _REFERENCE_KINDS[capability_id])
    elif capability_id == "analytic.line.get":
        fields = (*_ANALYTIC_LINE_FIELDS, *_analytic_column_names(raw_model))
    elif capability_id == "analytic.distribution_model.get":
        fields = _DISTRIBUTION_MODEL_FIELDS
    elif capability_id == "analytic.applicability.get":
        fields = _APPLICABILITY_FIELDS
    elif capability_id == "budget.get":
        fields = _BUDGET_FIELDS
    elif capability_id == "budget.line.get":
        fields = (*_BUDGET_LINE_FIELDS, *_analytic_column_names(raw_model))
    else:
        fields = {
            "account.account.get": (
                "id",
                "code",
                "name",
                "account_type",
                "active",
                "reconcile",
                "company_ids",
            ),
            "journal.get": (
                "id",
                "sequence",
                "code",
                "name",
                "type",
                "active",
                "currency_id",
                "company_id",
            ),
            "tax.get": (
                "id",
                "sequence",
                "name",
                "type_tax_use",
                "amount_type",
                "amount",
                "price_include",
                "include_base_amount",
                "is_base_affected",
                "active",
                "tax_group_id",
                "company_id",
            ),
            "payment_term.get": (
                "id",
                "sequence",
                "name",
                "active",
                "company_id",
                "display_on_invoice",
                "early_discount",
                "discount_percentage",
                "discount_days",
                "early_pay_discount_computation",
                "line_ids",
            ),
            "currency.get": (
                "id",
                "name",
                "full_name",
                "symbol",
                "rounding",
                "decimal_places",
                "active",
                "position",
                "is_current_company_currency",
            ),
            "partner.accounting.get": (
                "id",
                "complete_name",
                "ref",
                "active",
                "is_company",
                "company_id",
                "customer_rank",
                "supplier_rank",
                "property_account_receivable_id",
                "property_account_payable_id",
            ),
            "bank.transaction.get": (
                "id",
                "company_id",
                "payment_ref",
                "partner_id",
                "journal_id",
                "amount",
                "currency_id",
                "move_id",
                "is_reconciled",
                "payment_ids",
            ),
            "journal_item.get": (
                "id",
                "company_id",
                "date",
                "date_maturity",
                "move_id",
                "account_id",
                "partner_id",
                "journal_id",
                "name",
                "ref",
                "debit",
                "credit",
                "balance",
                "amount_currency",
                "currency_id",
                "reconciled",
                "matching_number",
            ),
            "payment.method.get": (
                "id",
                "name",
                "payment_type",
                "sequence",
                "company_id",
                "payment_method_id",
                "journal_id",
                "payment_account_id",
            ),
            "reconciliation.model.get": (
                "id",
                "name",
                "sequence",
                "active",
                "company_id",
                "match_amount",
                "match_amount_min",
                "match_amount_max",
                "match_label",
                "match_label_param",
            ),
        }[capability_id]
    from odoo.osv import expression

    domain = expression.AND(
        [
            _scope_domain(env, capability_id, company_id),
            [("id", "=", parameters[id_field])],
        ]
    )
    model = raw_model.with_context(active_test=False, allowed_company_ids=[company_id])
    if capability_id == "cash_rounding.get":
        model = model.with_company(env["res.company"].browse(company_id))
    return model.search_read(domain, fields=list(fields), limit=1, order="id")


def _normalize_master(
    env: Any,
    capability_id: str,
    rows: list[dict[str, Any]],
    company_id: int,
) -> list[dict[str, Any]]:
    if capability_id == "account.account.get":
        for row in rows:
            row["company_ids"] = sorted(row["company_ids"])
        return rows
    if capability_id == "journal.get":
        currency_ids = {
            value
            for row in rows
            if (value := _reference_id(row.get("currency_id"))) is not None
        }
        currencies = _related_rows(env, "res.currency", currency_ids, ("name",))
        for row in rows:
            currency_id = _reference_id(row.pop("currency_id"))
            row["currency"] = (
                _currency_reference(currencies[currency_id])
                if currency_id is not None
                else None
            )
            row["company_id"] = _reference_id(row["company_id"])
        return rows
    if capability_id == "tax.get":
        group_ids = {_reference_id(row.get("tax_group_id")) for row in rows}
        group_ids.discard(None)
        groups = _related_rows(env, "account.tax.group", group_ids, ("name",))
        for row in rows:
            group_id = _reference_id(row.pop("tax_group_id"))
            if group_id is None:
                raise ValueError("missing tax group")
            row["amount"] = _decimal_string(row["amount"])
            row["tax_group"] = _named_reference(groups[group_id])
            row["company_id"] = _reference_id(row["company_id"])
        return rows
    if capability_id == "payment_term.get":
        line_ids = {line_id for row in rows for line_id in row.pop("line_ids")}
        lines = _related_rows(
            env,
            "account.payment.term.line",
            line_ids,
            (
                "payment_id",
                "value",
                "value_amount",
                "delay_type",
                "nb_days",
                "days_next_month",
            ),
        )
        for row in rows:
            term_lines = []
            for line in lines.values():
                if _reference_id(line["payment_id"]) != row["id"]:
                    continue
                term_lines.append(
                    {
                        "id": line["id"],
                        "value": line["value"],
                        "value_amount": _decimal_string(line["value_amount"]),
                        "delay_type": line["delay_type"],
                        "nb_days": line["nb_days"],
                        "days_next_month": (
                            None
                            if line["days_next_month"] is False
                            else line["days_next_month"]
                        ),
                    }
                )
            row["company_id"] = _reference_id(row["company_id"])
            row["discount_percentage"] = _decimal_string(row["discount_percentage"])
            row["lines"] = sorted(term_lines, key=lambda item: item["id"])
        return rows
    if capability_id == "currency.get":
        for row in rows:
            row["is_company_currency"] = row.pop("is_current_company_currency")
            row["code"] = row["name"]
            row["name"] = _optional_text(row.pop("full_name"))
            row["position"] = _optional_text(row["position"])
            row["rounding"] = _decimal_string(row["rounding"])
        return rows
    return rows


def _normalize_partner(
    env: Any, rows: list[dict[str, Any]], company_id: int
) -> list[dict[str, Any]]:
    account_ids = {
        value
        for row in rows
        for field in ("property_account_receivable_id", "property_account_payable_id")
        if (value := _reference_id(row.get(field))) is not None
    }
    accounts = _related_rows(
        env, "account.account", account_ids, ("code", "name", "company_ids")
    )
    for account in accounts.values():
        if company_id not in account["company_ids"]:
            raise ValueError("account outside company")
    for row in rows:
        receivable_id = _reference_id(row.pop("property_account_receivable_id"))
        payable_id = _reference_id(row.pop("property_account_payable_id"))
        row["company_id"] = _reference_id(row["company_id"])
        row["ref"] = _optional_text(row["ref"])
        row["receivable_account"] = (
            _coded_reference(accounts[receivable_id])
            if receivable_id is not None
            else None
        )
        row["payable_account"] = (
            _coded_reference(accounts[payable_id]) if payable_id is not None else None
        )
    return rows


def _normalize_bank(
    env: Any, rows: list[dict[str, Any]], company_id: int
) -> list[dict[str, Any]]:
    partner_ids = {_reference_id(row.get("partner_id")) for row in rows}
    partner_ids.discard(None)
    journal_ids = {_reference_id(row.get("journal_id")) for row in rows}
    currency_ids = {_reference_id(row.get("currency_id")) for row in rows}
    move_ids = {_reference_id(row.get("move_id")) for row in rows}
    payment_ids = {
        value
        for row in rows
        for value in row.get("payment_ids", [])
        if _valid_id(value)
    }
    if None in journal_ids or None in currency_ids or None in move_ids:
        raise ValueError("missing bank relation")
    partners = _related_rows(env, "res.partner", partner_ids, ("complete_name",))
    journals = _related_rows(
        env, "account.journal", journal_ids, ("code", "name", "company_id")
    )
    currencies = _related_rows(env, "res.currency", currency_ids, ("name",))
    moves = _related_rows(
        env, "account.move", move_ids, ("name", "state", "date", "ref", "company_id")
    )
    payments = _related_rows(
        env, "account.payment", payment_ids, ("date", "company_id")
    )
    result = []
    for raw in rows:
        row = dict(raw)
        partner_id = _reference_id(row.pop("partner_id"))
        journal_id = _reference_id(row.pop("journal_id"))
        currency_id = _reference_id(row.pop("currency_id"))
        move_id = _reference_id(row.pop("move_id"))
        linked_payments = row.pop("payment_ids")
        if (
            _reference_id(row.pop("company_id")) != company_id
            or journal_id is None
            or currency_id is None
            or move_id is None
            or _reference_id(journals[journal_id]["company_id"]) != company_id
            or _reference_id(moves[move_id]["company_id"]) != company_id
        ):
            raise ValueError("bank transaction outside company")
        payment_dates = []
        for payment_id in linked_payments:
            payment = payments[payment_id]
            if _reference_id(payment["company_id"]) != company_id:
                raise ValueError("payment outside company")
            payment_dates.append(_date_string(payment["date"]))
        move = moves[move_id]
        result.append(
            {
                "id": row["id"],
                "company_id": company_id,
                "date": _date_string(move["date"]),
                "payment_date": min(payment_dates) if payment_dates else None,
                "name": _optional_text(row["payment_ref"]) or "/",
                "reference": _optional_text(move["ref"]),
                "partner": _named_reference(
                    {"id": partner_id, "name": partners[partner_id]["complete_name"]}
                )
                if partner_id is not None
                else None,
                "journal": _coded_reference(journals[journal_id]),
                "amount": _decimal_string(row["amount"]),
                "currency": _currency_reference(currencies[currency_id]),
                "move": {"id": move_id, "name": move["name"], "state": move["state"]},
                "reconciled": row["is_reconciled"],
            }
        )
    return result


def _journal_item_domain(
    company_id: int, parameters: dict[str, Any], *, include_after: bool
) -> list[Any]:
    domains: list[list[Any]] = [[("company_id", "=", company_id)]]
    for field, operator in (("date_from", ">="), ("date_to", "<=")):
        if parameters[field] is not None:
            domains.append([("date", operator, parameters[field])])
    for field in ("move_id", "account_id", "partner_id", "journal_id"):
        if parameters[field] is not None:
            domains.append([(field, "=", parameters[field])])
    if parameters["posted_only"]:
        domains.append([("parent_state", "=", "posted")])
    if include_after and parameters["after_id"] is not None:
        domains.append([("id", ">", parameters["after_id"])])
    from odoo.osv import expression

    return expression.AND(domains)


def _journal_item_rows(
    env: Any, parameters: dict[str, Any], company_id: int
) -> tuple[list[dict[str, Any]], bool]:
    model = env["account.move.line"].with_context(
        active_test=False, allowed_company_ids=[company_id]
    )
    cursor_found = True
    if parameters["after_id"] is not None:
        from odoo.osv import expression

        boundary_domain = expression.AND(
            [
                _journal_item_domain(company_id, parameters, include_after=False),
                [("id", "=", parameters["after_id"])],
            ]
        )
        cursor_found = bool(model.search_count(boundary_domain, limit=1))
    if not cursor_found:
        return [], False
    rows = model.search_read(
        _journal_item_domain(company_id, parameters, include_after=True),
        fields=[
            "id",
            "company_id",
            "date",
            "date_maturity",
            "move_id",
            "account_id",
            "partner_id",
            "journal_id",
            "name",
            "ref",
            "debit",
            "credit",
            "balance",
            "amount_currency",
            "currency_id",
            "reconciled",
            "matching_number",
        ],
        limit=parameters["limit"],
        order="id",
    )
    return rows, True


def _normalize_journal_items(
    env: Any, rows: list[dict[str, Any]], company_id: int
) -> list[dict[str, Any]]:
    move_ids = {_reference_id(row.get("move_id")) for row in rows}
    account_ids = {_reference_id(row.get("account_id")) for row in rows}
    partner_ids = {_reference_id(row.get("partner_id")) for row in rows}
    journal_ids = {_reference_id(row.get("journal_id")) for row in rows}
    currency_ids = {_reference_id(row.get("currency_id")) for row in rows}
    partner_ids.discard(None)
    if (
        None in move_ids
        or None in account_ids
        or None in journal_ids
        or None in currency_ids
    ):
        raise ValueError("missing journal-item relation")
    moves = _related_rows(
        env, "account.move", move_ids, ("name", "state", "move_type", "company_id")
    )
    accounts = _related_rows(
        env, "account.account", account_ids, ("code", "name", "company_ids")
    )
    partners = _related_rows(env, "res.partner", partner_ids, ("complete_name",))
    journals = _related_rows(
        env, "account.journal", journal_ids, ("code", "name", "company_id")
    )
    currencies = _related_rows(env, "res.currency", currency_ids, ("name",))
    result = []
    for raw in rows:
        row = dict(raw)
        move_id = _reference_id(row.pop("move_id"))
        account_id = _reference_id(row.pop("account_id"))
        partner_id = _reference_id(row.pop("partner_id"))
        journal_id = _reference_id(row.pop("journal_id"))
        currency_id = _reference_id(row.pop("currency_id"))
        if (
            _reference_id(row.pop("company_id")) != company_id
            or _reference_id(moves[move_id]["company_id"]) != company_id
            or company_id not in accounts[account_id]["company_ids"]
            or _reference_id(journals[journal_id]["company_id"]) != company_id
        ):
            raise ValueError("journal item outside company")
        move = moves[move_id]
        result.append(
            {
                "id": row["id"],
                "company_id": company_id,
                "date": _date_string(row["date"]),
                "date_maturity": _optional_date_string(row["date_maturity"]),
                "move": {
                    "id": move_id,
                    "name": move["name"],
                    "state": move["state"],
                    "move_type": move["move_type"],
                },
                "account": _coded_reference(accounts[account_id]),
                "partner": _named_reference(
                    {"id": partner_id, "name": partners[partner_id]["complete_name"]}
                )
                if partner_id is not None
                else None,
                "journal": _coded_reference(journals[journal_id]),
                "name": row["name"] if isinstance(row["name"], str) else "",
                "reference": _optional_text(row["ref"]),
                "debit": _decimal_string(row["debit"]),
                "credit": _decimal_string(row["credit"]),
                "balance": _decimal_string(row["balance"]),
                "amount_currency": _decimal_string(row["amount_currency"]),
                "currency": _currency_reference(currencies[currency_id]),
                "reconciled": row["reconciled"],
                "matching_number": _optional_text(row["matching_number"]),
            }
        )
    return result


def _reference_domain(
    env: Any,
    capability_id: str,
    company_id: int,
    parameters: dict[str, Any],
    *,
    include_after: bool,
) -> list[Any]:
    domains: list[list[Any]] = [_scope_domain(env, capability_id, company_id)]
    query = parameters.get("query")
    if query is not None:
        if capability_id == "partner.search":
            query_fields = (
                "name",
                "display_name",
                "vat",
                "ref",
                "email",
                "phone",
                "mobile",
            )
            partner_fields = getattr(env["res.partner"], "_fields", None)
            if isinstance(partner_fields, Mapping) and "mobile" not in partner_fields:
                query_fields = tuple(
                    field_name for field_name in query_fields if field_name != "mobile"
                )
            domains.append(
                [
                    *(["|"] * (len(query_fields) - 1)),
                    *((field_name, "ilike", query) for field_name in query_fields),
                ]
            )
        elif capability_id == "product.search":
            domains.append(
                [
                    "|",
                    "|",
                    ("name", "ilike", query),
                    ("default_code", "ilike", query),
                    ("barcode", "ilike", query),
                ]
            )
        elif capability_id == "analytic.account.search":
            domains.append(["|", ("name", "ilike", query), ("code", "ilike", query)])
        else:
            domains.append([("name", "ilike", query)])
    active = parameters.get("active")
    if active is not None:
        domains.append([("active", "=", active)])
    if capability_id == "partner.search":
        if parameters["company_type"] is not None:
            domains.append(
                [("is_company", "=", parameters["company_type"] == "company")]
            )
        if parameters["customer"] is not None:
            operator = ">" if parameters["customer"] else "="
            domains.append([("customer_rank", operator, 0)])
        if parameters["supplier"] is not None:
            operator = ">" if parameters["supplier"] else "="
            domains.append([("supplier_rank", operator, 0)])
    if (
        capability_id == "partner.bank_account.search"
        and parameters["partner_id"] is not None
    ):
        domains.append([("partner_id", "=", parameters["partner_id"])])
    if capability_id == "bank.statement.search":
        if parameters["journal_id"] is not None:
            domains.append([("journal_id", "=", parameters["journal_id"])])
        if parameters["date_from"] is not None:
            domains.append([("date", ">=", parameters["date_from"])])
        if parameters["date_to"] is not None:
            domains.append([("date", "<=", parameters["date_to"])])
    if capability_id == "analytic.account.search" and parameters["plan_id"] is not None:
        domains.append([("plan_id", "=", parameters["plan_id"])])
    if (
        capability_id == "fiscal_position.search"
        and parameters["auto_apply"] is not None
    ):
        domains.append([("auto_apply", "=", parameters["auto_apply"])])
    if include_after and parameters["after_id"] is not None:
        domains.append([("id", ">", parameters["after_id"])])
    from odoo.osv import expression

    return expression.AND(domains)


def _reference_rows(
    env: Any, capability_id: str, parameters: dict[str, Any], company_id: int
) -> tuple[list[dict[str, Any]], bool]:
    model = env[_PAGED_REFERENCE_MODELS[capability_id]].with_context(
        active_test=False, allowed_company_ids=[company_id]
    )
    if capability_id == "cash_rounding.list":
        model = model.with_company(env["res.company"].browse(company_id))
    cursor_found = True
    if parameters["after_id"] is not None:
        from odoo.osv import expression

        boundary_domain = expression.AND(
            [
                _reference_domain(
                    env,
                    capability_id,
                    company_id,
                    parameters,
                    include_after=False,
                ),
                [("id", "=", parameters["after_id"])],
            ]
        )
        cursor_found = bool(model.search_count(boundary_domain, limit=1))
    if not cursor_found:
        return [], False
    fields = _available_reference_fields(model, _REFERENCE_KINDS[capability_id])
    return (
        model.search_read(
            _reference_domain(
                env,
                capability_id,
                company_id,
                parameters,
                include_after=True,
            ),
            fields=list(fields),
            limit=parameters["limit"],
            order="id",
        ),
        True,
    )


def _id_page_rows(
    model: Any,
    domain: list[Any],
    *,
    after_id: int | None,
    limit: int,
    fields: tuple[str, ...],
) -> tuple[list[dict[str, Any]], bool]:
    from odoo.osv import expression

    if after_id is not None:
        boundary_domain = expression.AND([domain, [("id", "=", after_id)]])
        if not model.search_count(boundary_domain, limit=1):
            return [], False
    page_domain = domain
    if after_id is not None:
        page_domain = expression.AND([domain, [("id", ">", after_id)]])
    return (
        model.search_read(
            page_domain,
            fields=list(fields),
            limit=limit,
            order="id",
        ),
        True,
    )


def _analytic_line_rows(
    env: Any, parameters: dict[str, Any], company_id: int
) -> tuple[list[dict[str, Any]], bool]:
    from odoo.osv import expression

    domains: list[list[Any]] = [[("company_id", "=", company_id)]]
    if parameters["query"] is not None:
        domains.append(
            [
                "|",
                ("name", "ilike", parameters["query"]),
                ("ref", "ilike", parameters["query"]),
            ]
        )
    if parameters["date_from"] is not None:
        domains.append([("date", ">=", parameters["date_from"])])
    if parameters["date_to"] is not None:
        domains.append([("date", "<=", parameters["date_to"])])
    if parameters["analytic_account_id"] is not None:
        domains.append([("auto_account_id", "=", parameters["analytic_account_id"])])
    model = env["account.analytic.line"].with_context(
        active_test=False, allowed_company_ids=[company_id]
    )
    fields = (*_ANALYTIC_LINE_FIELDS, *_analytic_column_names(model))
    return _id_page_rows(
        model,
        expression.AND(domains),
        after_id=parameters["after_id"],
        limit=parameters["limit"],
        fields=fields,
    )


def _distribution_model_rows(
    env: Any, parameters: dict[str, Any], company_id: int
) -> tuple[list[dict[str, Any]], bool]:
    model = env["account.analytic.distribution.model"].with_context(
        active_test=False, allowed_company_ids=[company_id]
    )
    return _id_page_rows(
        model,
        _scope_domain(env, "analytic.distribution_model.list", company_id),
        after_id=parameters["after_id"],
        limit=parameters["limit"],
        fields=_DISTRIBUTION_MODEL_FIELDS,
    )


def _applicability_rows(
    env: Any, parameters: dict[str, Any], company_id: int
) -> tuple[list[dict[str, Any]], bool]:
    model = env["account.analytic.applicability"].with_context(
        active_test=False, allowed_company_ids=[company_id]
    )
    return _id_page_rows(
        model,
        _scope_domain(env, "analytic.applicability.list", company_id),
        after_id=parameters["after_id"],
        limit=parameters["limit"],
        fields=_APPLICABILITY_FIELDS,
    )


def _budget_rows(
    env: Any, parameters: dict[str, Any], company_id: int
) -> tuple[list[dict[str, Any]], bool]:
    from odoo.osv import expression

    domains: list[list[Any]] = [_scope_domain(env, "budget.search", company_id)]
    if parameters["query"] is not None:
        domains.append([("name", "ilike", parameters["query"])])
    if parameters["state"] is not None:
        domains.append([("state", "=", parameters["state"])])
    if parameters["budget_type"] is not None:
        domains.append([("budget_type", "=", parameters["budget_type"])])
    if parameters["date_from"] is not None:
        domains.append([("date_to", ">=", parameters["date_from"])])
    if parameters["date_to"] is not None:
        domains.append([("date_from", "<=", parameters["date_to"])])
    model = env["budget.analytic"].with_context(
        active_test=False, allowed_company_ids=[company_id]
    )
    return _id_page_rows(
        model,
        expression.AND(domains),
        after_id=parameters["after_id"],
        limit=parameters["limit"],
        fields=_BUDGET_FIELDS,
    )


def _budget_line_filter_visible(
    env: Any, parameters: dict[str, Any], company_id: int
) -> bool:
    from odoo.osv import expression

    budget_model = env["budget.analytic"].with_context(
        active_test=False, allowed_company_ids=[company_id]
    )
    budget_domain = expression.AND(
        [
            _scope_domain(env, "budget.get", company_id),
            [("id", "=", parameters["budget_id"])],
        ]
    )
    if not budget_model.search_count(budget_domain, limit=1):
        return False
    if parameters["plan_id"] is None:
        return True
    plan_visible = bool(
        env["account.analytic.plan"].search_count(
            [("id", "=", parameters["plan_id"])], limit=1
        )
    )
    account_domain = expression.AND(
        [
            [
                "|",
                ("company_id", "=", False),
                ("company_id", "=", company_id),
            ],
            [("id", "=", parameters["analytic_account_id"])],
            [("plan_id", "child_of", parameters["plan_id"])],
        ]
    )
    account_visible = bool(
        env["account.analytic.account"]
        .with_context(active_test=False, allowed_company_ids=[company_id])
        .search_count(account_domain, limit=1)
    )
    return plan_visible and account_visible


def _budget_line_rows(
    env: Any, parameters: dict[str, Any], company_id: int
) -> tuple[list[dict[str, Any]], bool]:
    from odoo.osv import expression

    if not _budget_line_filter_visible(env, parameters, company_id):
        return [], parameters["after_id"] is None
    domains: list[list[Any]] = [
        _scope_domain(env, "budget.line.list", company_id),
        [("budget_analytic_id", "=", parameters["budget_id"])],
    ]
    if parameters["analytic_account_id"] is not None:
        domains.append([("auto_account_id", "=", parameters["analytic_account_id"])])
    model = env["budget.line"].with_context(
        active_test=False, allowed_company_ids=[company_id]
    )
    fields = (*_BUDGET_LINE_FIELDS, *_analytic_column_names(model))
    return _id_page_rows(
        model,
        expression.AND(domains),
        after_id=parameters["after_id"],
        limit=parameters["limit"],
        fields=fields,
    )


def _normalize_products(
    env: Any, rows: list[dict[str, Any]], company_id: int
) -> list[dict[str, Any]]:
    template_ids = {_reference_id(row.get("product_tmpl_id")) for row in rows}
    category_ids = {_reference_id(row.get("categ_id")) for row in rows}
    uom_ids = {_reference_id(row.get("uom_id")) for row in rows}
    currency_ids = {_reference_id(row.get("currency_id")) for row in rows}
    category_ids.discard(None)
    if any(None in values for values in (template_ids, uom_ids, currency_ids)):
        raise ValueError("missing product relation")
    templates = _related_rows(env, "product.template", template_ids, ("name",))
    categories = _related_rows(env, "product.category", category_ids, ("name",))
    uoms = _related_rows(env, "uom.uom", uom_ids, ("name",))
    currencies = _related_rows(env, "res.currency", currency_ids, ("name",))
    result = []
    for row in rows:
        template_id = _reference_id(row["product_tmpl_id"])
        category_id = _reference_id(row["categ_id"])
        uom_id = _reference_id(row["uom_id"])
        currency_id = _reference_id(row["currency_id"])
        row_company_id = _reference_id(row["company_id"])
        if row_company_id not in {None, company_id}:
            raise ValueError("product outside company")
        result.append(
            {
                "id": row["id"],
                "name": row["name"],
                "default_code": _optional_text(row["default_code"]),
                "active": row["active"],
                "product_type": row["type"],
                "is_storable": row["is_storable"],
                "template": _named_reference(templates[template_id]),
                "category": _named_reference(categories[category_id])
                if category_id is not None
                else None,
                "uom": _named_reference(uoms[uom_id]),
                "company_id": row_company_id,
                "currency": _currency_reference(currencies[currency_id]),
                "standard_price": _decimal_string(row["standard_price"]),
                "list_price": _decimal_string(row["list_price"]),
            }
        )
    return result


def _normalize_plans(env: Any, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    parent_ids = {_reference_id(row.get("parent_id")) for row in rows}
    parent_ids.discard(None)
    parents = _related_rows(env, "account.analytic.plan", parent_ids, ("name",))
    result = []
    for row in rows:
        parent_id = _reference_id(row["parent_id"])
        result.append(
            {
                "id": row["id"],
                "name": row["name"],
                "complete_name": row["complete_name"],
                "parent": _named_reference(parents[parent_id])
                if parent_id is not None
                else None,
                "color": row["color"],
            }
        )
    return result


def _normalize_analytic_accounts(
    env: Any, rows: list[dict[str, Any]], company_id: int
) -> list[dict[str, Any]]:
    plan_ids = {_reference_id(row.get("plan_id")) for row in rows}
    partner_ids = {_reference_id(row.get("partner_id")) for row in rows}
    currency_ids = {_reference_id(row.get("currency_id")) for row in rows}
    partner_ids.discard(None)
    currency_ids.discard(None)
    if None in plan_ids:
        raise ValueError("missing analytic plan")
    company_rows = _related_rows(env, "res.company", {company_id}, ("currency_id",))
    company_currency_id = _reference_id(company_rows[company_id]["currency_id"])
    if company_currency_id is None:
        raise ValueError("missing company currency")
    currency_ids.add(company_currency_id)
    plans = _related_rows(env, "account.analytic.plan", plan_ids, ("name",))
    partners = _related_rows(env, "res.partner", partner_ids, ("complete_name",))
    currencies = _related_rows(env, "res.currency", currency_ids, ("name",))
    result = []
    for row in rows:
        plan_id = _reference_id(row["plan_id"])
        partner_id = _reference_id(row["partner_id"])
        row_company_id = _reference_id(row["company_id"])
        currency_id = _reference_id(row["currency_id"]) or company_currency_id
        if row_company_id not in {None, company_id}:
            raise ValueError("analytic account outside company")
        result.append(
            {
                "id": row["id"],
                "name": row["name"],
                "code": _optional_text(row["code"]),
                "active": row["active"],
                "plan": _named_reference(plans[plan_id]),
                "partner": _named_reference(
                    {
                        "id": partner_id,
                        "name": partners[partner_id]["complete_name"],
                    }
                )
                if partner_id is not None
                else None,
                "company_id": row_company_id,
                "currency": _currency_reference(currencies[currency_id]),
                "balance": _decimal_string(row["balance"]),
            }
        )
    return result


def _normalize_fiscal_positions(
    env: Any, rows: list[dict[str, Any]], company_id: int
) -> list[dict[str, Any]]:
    country_ids = {_reference_id(row.get("country_id")) for row in rows}
    group_ids = {_reference_id(row.get("country_group_id")) for row in rows}
    state_ids = {
        state_id
        for row in rows
        for state_id in row.get("state_ids", [])
        if _valid_id(state_id)
    }
    country_ids.discard(None)
    group_ids.discard(None)
    countries = _related_rows(env, "res.country", country_ids, ("name",))
    groups = _related_rows(env, "res.country.group", group_ids, ("name",))
    states = _related_rows(env, "res.country.state", state_ids, ("name",))
    result = []
    for row in rows:
        country_id = _reference_id(row["country_id"])
        group_id = _reference_id(row["country_group_id"])
        if _reference_id(row["company_id"]) != company_id or any(
            not _valid_id(state_id) for state_id in row["state_ids"]
        ):
            raise ValueError("fiscal position outside company")
        result.append(
            {
                "id": row["id"],
                "name": row["name"],
                "active": row["active"],
                "auto_apply": row["auto_apply"],
                "vat_required": row["vat_required"],
                "country": _named_reference(countries[country_id])
                if country_id is not None
                else None,
                "country_group": _named_reference(groups[group_id])
                if group_id is not None
                else None,
                "states": [
                    _named_reference(states[state_id])
                    for state_id in sorted(row["state_ids"])
                ],
                "company_id": company_id,
                "foreign_vat": _optional_text(row["foreign_vat"]),
            }
        )
    return result


def _normalize_tags_or_tax_groups(
    env: Any,
    capability_id: str,
    rows: list[dict[str, Any]],
    company_id: int,
) -> list[dict[str, Any]]:
    country_ids = {_reference_id(row.get("country_id")) for row in rows}
    country_ids.discard(None)
    countries = _related_rows(env, "res.country", country_ids, ("name",))
    result = []
    for row in rows:
        country_id = _reference_id(row["country_id"])
        country = (
            _named_reference(countries[country_id]) if country_id is not None else None
        )
        if capability_id in {"account.tag.list", "account.tag.get"}:
            result.append(
                {
                    "id": row["id"],
                    "name": row["name"],
                    "applicability": row["applicability"],
                    "active": row["active"],
                    "color": row["color"],
                    "country": country,
                }
            )
        else:
            if _reference_id(row["company_id"]) != company_id:
                raise ValueError("tax group outside company")
            result.append(
                {
                    "id": row["id"],
                    "name": row["name"],
                    "sequence": row["sequence"],
                    "country": country,
                    "preceding_subtotal": _optional_text(row["preceding_subtotal"]),
                    "company_id": company_id,
                }
            )
    return result


def _normalize_cash_roundings(
    env: Any, rows: list[dict[str, Any]], company_id: int
) -> list[dict[str, Any]]:
    account_ids = {
        account_id
        for row in rows
        for field in ("profit_account_id", "loss_account_id")
        if (account_id := _reference_id(row.get(field))) is not None
    }
    accounts = _related_rows(
        env, "account.account", account_ids, ("code", "name", "company_ids")
    )
    result = []
    for row in rows:
        profit_account_id = _reference_id(row["profit_account_id"])
        loss_account_id = _reference_id(row["loss_account_id"])
        if any(
            company_id not in accounts[account_id]["company_ids"]
            for account_id in (profit_account_id, loss_account_id)
            if account_id is not None
        ):
            raise ValueError("cash rounding account outside company")
        result.append(
            {
                "id": row["id"],
                "name": row["name"],
                "rounding": _decimal_string(row["rounding"]),
                "strategy": row["strategy"],
                "rounding_method": row["rounding_method"],
                "profit_account": _coded_reference(accounts[profit_account_id])
                if profit_account_id is not None
                else None,
                "loss_account": _coded_reference(accounts[loss_account_id])
                if loss_account_id is not None
                else None,
            }
        )
    return result


def _normalize_journal_groups(
    env: Any, rows: list[dict[str, Any]], company_id: int
) -> list[dict[str, Any]]:
    journal_ids = {
        journal_id
        for row in rows
        for journal_id in row["excluded_journal_ids"]
        if _valid_id(journal_id)
    }
    journals = _related_rows(
        env, "account.journal", journal_ids, ("code", "name", "company_id")
    )
    result = []
    for row in rows:
        excluded_ids = row["excluded_journal_ids"]
        if any(not _valid_id(journal_id) for journal_id in excluded_ids):
            raise ValueError("invalid excluded journal")
        row_company_id = _reference_id(row["company_id"])
        if row_company_id not in {None, company_id} or any(
            _reference_id(journals[journal_id]["company_id"]) != company_id
            for journal_id in excluded_ids
        ):
            raise ValueError("journal group outside company")
        result.append(
            {
                "id": row["id"],
                "name": row["name"],
                "sequence": row["sequence"],
                "company_id": row_company_id,
                "excluded_journals": [
                    _coded_reference(journals[journal_id])
                    for journal_id in sorted(set(excluded_ids))
                ],
            }
        )
    return result


def _normalize_incoterms(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": row["id"],
            "code": row["code"],
            "name": row["name"],
            "active": row["active"],
        }
        for row in rows
    ]


def _normalize_partner_banks(
    env: Any, rows: list[dict[str, Any]], company_id: int
) -> list[dict[str, Any]]:
    partner_ids = {_reference_id(row.get("partner_id")) for row in rows}
    bank_ids = {_reference_id(row.get("bank_id")) for row in rows}
    currency_ids = {_reference_id(row.get("currency_id")) for row in rows}
    linked_journal_ids: dict[int, int | None] = {}
    for row in rows:
        journal_ids = _sorted_relation_ids(row.get("journal_id"))
        if len(journal_ids) > 1:
            raise ValueError("multiple linked journals")
        linked_journal_ids[row["id"]] = journal_ids[0] if journal_ids else None
    journal_ids = {
        journal_id
        for journal_id in linked_journal_ids.values()
        if journal_id is not None
    }
    bank_ids.discard(None)
    currency_ids.discard(None)
    if None in partner_ids:
        raise ValueError("missing bank account holder")
    partners = _related_rows(
        env, "res.partner", partner_ids, ("complete_name", "company_id")
    )
    banks = _related_rows(env, "res.bank", bank_ids, ("name", "bic"))
    currencies = _related_rows(env, "res.currency", currency_ids, ("name",))
    journals = _related_rows(
        env,
        "account.journal",
        journal_ids,
        ("code", "name", "company_id", "bank_account_id"),
    )
    result = []
    for row in rows:
        partner_id = _reference_id(row["partner_id"])
        bank_id = _reference_id(row["bank_id"])
        currency_id = _reference_id(row["currency_id"])
        row_company_id = _reference_id(row["company_id"])
        journal_id = linked_journal_ids[row["id"]]
        if (
            row_company_id not in {None, company_id}
            or _reference_id(partners[partner_id]["company_id"])
            not in {None, company_id}
            or (
                journal_id is not None
                and (
                    _reference_id(journals[journal_id]["company_id"]) != company_id
                    or _reference_id(journals[journal_id]["bank_account_id"])
                    != row["id"]
                )
            )
        ):
            raise ValueError("partner bank outside company")
        result.append(
            {
                "id": row["id"],
                "acc_number": row["acc_number"],
                "account_holder_name": _optional_text(row["acc_holder_name"]),
                "account_type": row["acc_type"],
                "active": row["active"],
                "sequence": row["sequence"],
                "account_holder": _named_reference(
                    {
                        "id": partner_id,
                        "name": partners[partner_id]["complete_name"],
                    }
                ),
                "allow_out_payment": row["allow_out_payment"],
                "bank": {
                    "id": bank_id,
                    "name": banks[bank_id]["name"],
                    "bic": _optional_text(banks[bank_id]["bic"]),
                }
                if bank_id is not None
                else None,
                "currency": _currency_reference(currencies[currency_id])
                if currency_id is not None
                else None,
                "company_id": row_company_id,
                "linked_journal": _coded_reference(journals[journal_id])
                if journal_id is not None
                else None,
            }
        )
    return result


def _normalize_bank_statements(
    env: Any, rows: list[dict[str, Any]], company_id: int
) -> list[dict[str, Any]]:
    journal_ids = {_reference_id(row.get("journal_id")) for row in rows}
    currency_ids = {_reference_id(row.get("currency_id")) for row in rows}
    line_ids_by_statement = {
        row["id"]: _sorted_relation_ids(row.get("line_ids")) for row in rows
    }
    line_ids = {
        line_id
        for statement_ids in line_ids_by_statement.values()
        for line_id in statement_ids
    }
    if None in journal_ids or None in currency_ids:
        raise ValueError("missing bank statement relation")
    journals = _related_rows(
        env, "account.journal", journal_ids, ("code", "name", "company_id")
    )
    currencies = _related_rows(env, "res.currency", currency_ids, ("name",))
    lines = _related_rows(
        env,
        "account.bank.statement.line",
        line_ids,
        ("company_id", "statement_id"),
    )
    result = []
    for row in rows:
        journal_id = _reference_id(row["journal_id"])
        currency_id = _reference_id(row["currency_id"])
        statement_line_ids = line_ids_by_statement[row["id"]]
        if (
            _reference_id(row["company_id"]) != company_id
            or _reference_id(journals[journal_id]["company_id"]) != company_id
            or any(
                _reference_id(lines[line_id]["company_id"]) != company_id
                or _reference_id(lines[line_id]["statement_id"]) != row["id"]
                for line_id in statement_line_ids
            )
        ):
            raise ValueError("bank statement outside company")
        result.append(
            {
                "id": row["id"],
                "name": row["name"],
                "reference": _optional_text(row["reference"]),
                "date": _optional_date_string(row["date"]),
                "company_id": company_id,
                "journal": _coded_reference(journals[journal_id]),
                "currency": _currency_reference(currencies[currency_id]),
                "balance_start": _decimal_string(row["balance_start"]),
                "balance_end": _decimal_string(row["balance_end"]),
                "balance_end_real": _decimal_string(row["balance_end_real"]),
                "is_complete": row["is_complete"],
                "is_valid": row["is_valid"],
                "problem_description": _optional_text(row["problem_description"]),
                "transaction_count": len(statement_line_ids),
            }
        )
    return result


def _normalize_partial_reconciles(
    env: Any, rows: list[dict[str, Any]], company_id: int
) -> list[dict[str, Any]]:
    line_ids: set[int] = set()
    currency_ids: set[int] = set()
    exchange_move_ids: set[int] = set()
    for row in rows:
        debit_line_id = _reference_id(row.get("debit_move_id"))
        credit_line_id = _reference_id(row.get("credit_move_id"))
        company_currency_id = _reference_id(row.get("company_currency_id"))
        debit_currency_id = _reference_id(row.get("debit_currency_id"))
        credit_currency_id = _reference_id(row.get("credit_currency_id"))
        if (
            debit_line_id is None
            or credit_line_id is None
            or debit_line_id == credit_line_id
            or company_currency_id is None
            or debit_currency_id is None
            or credit_currency_id is None
        ):
            raise ValueError("missing partial reconcile relation")
        line_ids.update((debit_line_id, credit_line_id))
        currency_ids.update(
            (company_currency_id, debit_currency_id, credit_currency_id)
        )
        exchange_move_id = _reference_id(row.get("exchange_move_id"))
        if exchange_move_id is not None:
            exchange_move_ids.add(exchange_move_id)
    company_rows = _related_rows(env, "res.company", {company_id}, ("currency_id",))
    company_currency_id = _reference_id(company_rows[company_id]["currency_id"])
    if company_currency_id is None:
        raise ValueError("missing company currency")
    lines = _related_rows(
        env,
        "account.move.line",
        line_ids,
        ("company_id", "matching_number"),
    )
    currencies = _related_rows(env, "res.currency", currency_ids, ("name",))
    exchange_moves = _related_rows(
        env, "account.move", exchange_move_ids, ("company_id",)
    )
    result = []
    for row in rows:
        debit_line_id = _reference_id(row["debit_move_id"])
        credit_line_id = _reference_id(row["credit_move_id"])
        company_currency_id_from_row = _reference_id(row["company_currency_id"])
        debit_currency_id = _reference_id(row["debit_currency_id"])
        credit_currency_id = _reference_id(row["credit_currency_id"])
        full_id = _reference_id(row["full_reconcile_id"])
        exchange_move_id = _reference_id(row["exchange_move_id"])
        debit_line = lines[debit_line_id]
        credit_line = lines[credit_line_id]
        debit_match = _optional_text(debit_line["matching_number"])
        credit_match = _optional_text(credit_line["matching_number"])
        if (
            _reference_id(row["company_id"]) != company_id
            or company_currency_id_from_row != company_currency_id
            or _reference_id(debit_line["company_id"]) != company_id
            or _reference_id(credit_line["company_id"]) != company_id
            or not debit_match
            or debit_match != credit_match
            or (
                exchange_move_id is not None
                and _reference_id(exchange_moves[exchange_move_id]["company_id"])
                != company_id
            )
        ):
            raise ValueError("partial reconcile outside company")
        result.append(
            {
                "id": row["id"],
                "company_id": company_id,
                "max_date": _date_string(row["max_date"]),
                "amount": _decimal_string(row["amount"]),
                "company_currency": _currency_reference(
                    currencies[company_currency_id_from_row]
                ),
                "debit_amount_currency": _decimal_string(row["debit_amount_currency"]),
                "debit_currency": _currency_reference(currencies[debit_currency_id]),
                "credit_amount_currency": _decimal_string(
                    row["credit_amount_currency"]
                ),
                "credit_currency": _currency_reference(currencies[credit_currency_id]),
                "debit_journal_item_id": debit_line_id,
                "credit_journal_item_id": credit_line_id,
                "full_reconcile_id": full_id,
                "exchange_move_id": exchange_move_id,
                "matching_number": debit_match,
            }
        )
    return result


def _normalize_full_reconciles(
    env: Any, rows: list[dict[str, Any]], company_id: int
) -> list[dict[str, Any]]:
    partial_ids_by_full = {
        row["id"]: _sorted_relation_ids(row.get("partial_reconcile_ids"), nonempty=True)
        for row in rows
    }
    line_ids_by_full = {
        row["id"]: _sorted_relation_ids(row.get("reconciled_line_ids"), nonempty=True)
        for row in rows
    }
    partial_ids = {
        partial_id
        for full_ids in partial_ids_by_full.values()
        for partial_id in full_ids
    }
    line_ids = {
        line_id for full_ids in line_ids_by_full.values() for line_id in full_ids
    }
    partials = _related_rows(
        env,
        "account.partial.reconcile",
        partial_ids,
        ("company_id", "debit_move_id", "credit_move_id", "full_reconcile_id"),
    )
    lines = _related_rows(
        env,
        "account.move.line",
        line_ids,
        ("company_id", "matching_number", "full_reconcile_id"),
    )
    result = []
    for row in rows:
        full_id = row["id"]
        full_partial_ids = partial_ids_by_full[full_id]
        full_line_ids = line_ids_by_full[full_id]
        matching_number = str(full_id)
        if any(
            _reference_id(lines[line_id]["company_id"]) != company_id
            or _optional_text(lines[line_id]["matching_number"]) != matching_number
            or _reference_id(lines[line_id]["full_reconcile_id"]) != full_id
            for line_id in full_line_ids
        ) or any(
            _reference_id(partials[partial_id]["company_id"]) != company_id
            or _reference_id(partials[partial_id]["full_reconcile_id"]) != full_id
            or _reference_id(partials[partial_id]["debit_move_id"]) not in full_line_ids
            or _reference_id(partials[partial_id]["credit_move_id"])
            not in full_line_ids
            for partial_id in full_partial_ids
        ):
            raise ValueError("full reconcile outside company")
        result.append(
            {
                "id": full_id,
                "company_id": company_id,
                "matching_number": matching_number,
                "partial_reconcile_ids": full_partial_ids,
                "reconciled_journal_item_ids": full_line_ids,
            }
        )
    return result


def _normalize_analytic_lines(
    env: Any, rows: list[dict[str, Any]], company_id: int
) -> list[dict[str, Any]]:
    columns = _analytic_column_names(env["account.analytic.line"])
    account_ids_by_line = {
        row["id"]: _analytic_account_ids(row, columns) for row in rows
    }
    account_ids = {
        account_id
        for line_ids in account_ids_by_line.values()
        for account_id in line_ids
    }
    partner_ids = {_reference_id(row.get("partner_id")) for row in rows}
    product_ids = {_reference_id(row.get("product_id")) for row in rows}
    uom_ids = {_reference_id(row.get("product_uom_id")) for row in rows}
    general_account_ids = {_reference_id(row.get("general_account_id")) for row in rows}
    journal_item_ids = {_reference_id(row.get("move_line_id")) for row in rows}
    currency_ids = {_reference_id(row.get("currency_id")) for row in rows}
    for values in (
        partner_ids,
        product_ids,
        uom_ids,
        general_account_ids,
        journal_item_ids,
    ):
        values.discard(None)
    if None in currency_ids:
        raise ValueError("missing analytic line currency")
    accounts = _analytic_account_references(
        env,
        account_ids,
        company_id=company_id,
        owner_company_id=company_id,
    )
    partners = _related_rows(
        env, "res.partner", partner_ids, ("complete_name", "company_id")
    )
    products = _related_rows(
        env, "product.product", product_ids, ("name", "company_id")
    )
    uoms = _related_rows(env, "uom.uom", uom_ids, ("name",))
    general_accounts = _related_rows(
        env,
        "account.account",
        general_account_ids,
        ("code", "name", "company_ids"),
    )
    journal_items = _related_rows(
        env, "account.move.line", journal_item_ids, ("company_id",)
    )
    currencies = _related_rows(env, "res.currency", currency_ids, ("name",))
    result = []
    for row in rows:
        partner_id = _reference_id(row["partner_id"])
        product_id = _reference_id(row["product_id"])
        uom_id = _reference_id(row["product_uom_id"])
        general_account_id = _reference_id(row["general_account_id"])
        journal_item_id = _reference_id(row["move_line_id"])
        currency_id = _reference_id(row["currency_id"])
        if (
            _reference_id(row["company_id"]) != company_id
            or (
                partner_id is not None
                and _reference_id(partners[partner_id]["company_id"])
                not in {None, company_id}
            )
            or (
                product_id is not None
                and _reference_id(products[product_id]["company_id"])
                not in {None, company_id}
            )
            or (
                general_account_id is not None
                and company_id
                not in general_accounts[general_account_id]["company_ids"]
            )
            or (
                journal_item_id is not None
                and _reference_id(journal_items[journal_item_id]["company_id"])
                != company_id
            )
        ):
            raise ValueError("analytic line outside company")
        result.append(
            {
                "id": row["id"],
                "date": _date_string(row["date"]),
                "name": "" if row["name"] in (None, False) else row["name"],
                "reference": _optional_text(row["ref"]),
                "amount": _decimal_string(row["amount"]),
                "unit_amount": _decimal_string(row["unit_amount"]),
                "company_id": company_id,
                "currency": _currency_reference(currencies[currency_id]),
                "analytic_accounts": [
                    _named_reference(accounts[account_id])
                    for account_id in account_ids_by_line[row["id"]]
                ],
                "partner": _named_reference(partners[partner_id])
                if partner_id is not None
                else None,
                "product": _named_reference(products[product_id])
                if product_id is not None
                else None,
                "uom": _named_reference(uoms[uom_id]) if uom_id is not None else None,
                "general_account": _coded_reference(
                    general_accounts[general_account_id]
                )
                if general_account_id is not None
                else None,
                "journal_item_id": journal_item_id,
            }
        )
    return result


def _parsed_distribution(value: Any) -> list[tuple[tuple[int, ...], str]]:
    if not isinstance(value, dict):
        raise TypeError("invalid analytic distribution")
    allocations: list[tuple[tuple[int, ...], str]] = []
    seen: set[tuple[int, ...]] = set()
    for raw_key, percentage in value.items():
        if not isinstance(raw_key, str) or not raw_key:
            raise ValueError("invalid analytic distribution key")
        segments = raw_key.split(",")
        if any(
            not segment.isascii()
            or not segment.isdigit()
            or segment == "0"
            or str(int(segment)) != segment
            for segment in segments
        ):
            raise ValueError("invalid analytic distribution key")
        account_ids = tuple(sorted(int(segment) for segment in segments))
        if len(account_ids) != len(set(account_ids)) or account_ids in seen:
            raise ValueError("duplicate analytic distribution accounts")
        seen.add(account_ids)
        allocations.append((account_ids, _decimal_string(percentage)))
    return sorted(allocations, key=lambda allocation: allocation[0])


def _normalize_distribution_models(
    env: Any, rows: list[dict[str, Any]], company_id: int
) -> list[dict[str, Any]]:
    allocations_by_model = {
        row["id"]: _parsed_distribution(row["analytic_distribution"]) for row in rows
    }
    account_ids = {
        account_id
        for allocations in allocations_by_model.values()
        for allocation_ids, _percentage in allocations
        for account_id in allocation_ids
    }
    accounts = _related_rows(
        env,
        "account.analytic.account",
        account_ids,
        ("name", "company_id", "plan_id"),
    )
    partner_ids = {_reference_id(row.get("partner_id")) for row in rows}
    partner_category_ids = {
        _reference_id(row.get("partner_category_id")) for row in rows
    }
    product_ids = {_reference_id(row.get("product_id")) for row in rows}
    product_category_ids = {_reference_id(row.get("product_categ_id")) for row in rows}
    for values in (
        partner_ids,
        partner_category_ids,
        product_ids,
        product_category_ids,
    ):
        values.discard(None)
    partners = _related_rows(
        env, "res.partner", partner_ids, ("complete_name", "company_id")
    )
    partner_categories = _related_rows(
        env, "res.partner.category", partner_category_ids, ("name",)
    )
    products = _related_rows(
        env, "product.product", product_ids, ("name", "company_id")
    )
    product_categories = _related_rows(
        env, "product.category", product_category_ids, ("name",)
    )
    result = []
    for row in rows:
        row_company_id = _reference_id(row["company_id"])
        partner_id = _reference_id(row["partner_id"])
        partner_category_id = _reference_id(row["partner_category_id"])
        product_id = _reference_id(row["product_id"])
        product_category_id = _reference_id(row["product_categ_id"])
        allocations = allocations_by_model[row["id"]]
        parsed_account_ids = {
            account_id
            for allocation_ids, _percentage in allocations
            for account_id in allocation_ids
        }
        relation_account_ids = set(
            _sorted_relation_ids(row["distribution_analytic_account_ids"])
        )
        if (
            row_company_id not in {None, company_id}
            or parsed_account_ids != relation_account_ids
            or any(
                _reference_id(accounts[account_id]["plan_id"]) is None
                or _reference_id(accounts[account_id]["company_id"])
                not in ({None} if row_company_id is None else {None, company_id})
                for account_id in parsed_account_ids
            )
            or (
                partner_id is not None
                and _reference_id(partners[partner_id]["company_id"])
                not in ({None} if row_company_id is None else {None, company_id})
            )
            or (
                product_id is not None
                and _reference_id(products[product_id]["company_id"])
                not in ({None} if row_company_id is None else {None, company_id})
            )
        ):
            raise ValueError("analytic distribution model outside company")
        result.append(
            {
                "id": row["id"],
                "sequence": row["sequence"],
                "company_id": row_company_id,
                "account_prefix": _optional_text(row["account_prefix"]),
                "partner": _named_reference(partners[partner_id])
                if partner_id is not None
                else None,
                "partner_category": _named_reference(
                    partner_categories[partner_category_id]
                )
                if partner_category_id is not None
                else None,
                "product": _named_reference(products[product_id])
                if product_id is not None
                else None,
                "product_category": _named_reference(
                    product_categories[product_category_id]
                )
                if product_category_id is not None
                else None,
                "allocations": [
                    {
                        "analytic_accounts": [
                            _named_reference(accounts[account_id])
                            for account_id in allocation_ids
                        ],
                        "percentage": percentage,
                    }
                    for allocation_ids, percentage in allocations
                ],
            }
        )
    return result


def _normalize_applicabilities(
    env: Any, rows: list[dict[str, Any]], company_id: int
) -> list[dict[str, Any]]:
    plan_ids = {_reference_id(row.get("analytic_plan_id")) for row in rows}
    category_ids = {_reference_id(row.get("product_categ_id")) for row in rows}
    plan_ids.discard(None)
    category_ids.discard(None)
    plans = _related_rows(env, "account.analytic.plan", plan_ids, ("name",))
    categories = _related_rows(env, "product.category", category_ids, ("name",))
    result = []
    for row in rows:
        row_company_id = _reference_id(row["company_id"])
        plan_id = _reference_id(row["analytic_plan_id"])
        category_id = _reference_id(row["product_categ_id"])
        if row_company_id not in {None, company_id}:
            raise ValueError("analytic applicability outside company")
        result.append(
            {
                "id": row["id"],
                "plan": _named_reference(plans[plan_id])
                if plan_id is not None
                else None,
                "business_domain": row["business_domain"],
                "applicability": row["applicability"],
                "company_id": row_company_id,
                "account_prefix": _optional_text(row["account_prefix"]),
                "product_category": _named_reference(categories[category_id])
                if category_id is not None
                else None,
            }
        )
    return result


def _normalize_budgets(
    env: Any, rows: list[dict[str, Any]], company_id: int
) -> list[dict[str, Any]]:
    user_ids = {_reference_id(row.get("user_id")) for row in rows}
    parent_ids = {_reference_id(row.get("parent_id")) for row in rows}
    user_ids.discard(None)
    parent_ids.discard(None)
    users = _related_rows(env, "res.users", user_ids, ("name",))
    parents = _related_rows(env, "budget.analytic", parent_ids, ("name", "company_id"))
    result = []
    for row in rows:
        row_company_id = _reference_id(row["company_id"])
        user_id = _reference_id(row["user_id"])
        parent_id = _reference_id(row["parent_id"])
        if row_company_id not in {None, company_id} or (
            parent_id is not None
            and _reference_id(parents[parent_id]["company_id"])
            not in ({None} if row_company_id is None else {None, company_id})
        ):
            raise ValueError("budget outside company")
        result.append(
            {
                "id": row["id"],
                "name": row["name"],
                "date_from": _date_string(row["date_from"]),
                "date_to": _date_string(row["date_to"]),
                "state": row["state"],
                "budget_type": row["budget_type"],
                "company_id": row_company_id,
                "responsible": _named_reference(users[user_id])
                if user_id is not None
                else None,
                "revision_of": _named_reference(parents[parent_id])
                if parent_id is not None
                else None,
            }
        )
    return result


def _normalize_budget_lines(
    env: Any, rows: list[dict[str, Any]], company_id: int
) -> list[dict[str, Any]]:
    columns = _analytic_column_names(env["budget.line"])
    account_ids_by_line = {
        row["id"]: _analytic_account_ids(row, columns) for row in rows
    }
    account_ids = {
        account_id
        for line_ids in account_ids_by_line.values()
        for account_id in line_ids
    }
    accounts = _related_rows(
        env,
        "account.analytic.account",
        account_ids,
        ("name", "company_id", "plan_id"),
    )
    budget_ids = {_reference_id(row.get("budget_analytic_id")) for row in rows}
    currency_ids = {_reference_id(row.get("currency_id")) for row in rows}
    if None in budget_ids or None in currency_ids:
        raise ValueError("missing budget line relation")
    budgets = _related_rows(env, "budget.analytic", budget_ids, ("name", "company_id"))
    currencies = _related_rows(env, "res.currency", currency_ids, ("name",))
    result = []
    for row in rows:
        row_company_id = _reference_id(row["company_id"])
        budget_id = _reference_id(row["budget_analytic_id"])
        currency_id = _reference_id(row["currency_id"])
        budget_company_id = _reference_id(budgets[budget_id]["company_id"])
        valid_account_companies = (
            {None} if row_company_id is None else {None, company_id}
        )
        if (
            row_company_id not in {None, company_id}
            or budget_company_id not in {None, company_id}
            or (row_company_id is None and budget_company_id is not None)
            or any(
                _reference_id(accounts[account_id]["plan_id"]) is None
                or _reference_id(accounts[account_id]["company_id"])
                not in valid_account_companies
                for account_id in account_ids_by_line[row["id"]]
            )
        ):
            raise ValueError("budget line outside company")
        result.append(
            {
                "id": row["id"],
                "sequence": row["sequence"],
                "budget": _named_reference(budgets[budget_id]),
                "date_from": _date_string(row["date_from"]),
                "date_to": _date_string(row["date_to"]),
                "budget_amount": _decimal_string(row["budget_amount"]),
                "achieved_amount": _decimal_string(row["achieved_amount"]),
                "achieved_percentage": _decimal_string(row["achieved_percentage"]),
                "theoretical_amount": _decimal_string(row["theoritical_amount"]),
                "theoretical_percentage": _decimal_string(
                    row["theoritical_percentage"]
                ),
                "above_budget": row["is_above_budget"],
                "state": row["budget_analytic_state"],
                "currency": _currency_reference(currencies[currency_id]),
                "company_id": row_company_id,
                "analytic_accounts": [
                    _named_reference(accounts[account_id])
                    for account_id in account_ids_by_line[row["id"]]
                ],
            }
        )
    return result


def _partner_business_reference(value: Any) -> str | None:
    text = _optional_text(value)
    if text is None:
        return None
    business_text = _PARTNER_REF_MARKER_SUFFIX.sub("", text).rstrip()
    return business_text or None


def _normalize_partners(
    env: Any, rows: list[dict[str, Any]], company_id: int
) -> list[dict[str, Any]]:
    state_ids = {_reference_id(row.get("state_id")) for row in rows}
    country_ids = {_reference_id(row.get("country_id")) for row in rows}
    parent_ids = {_reference_id(row.get("parent_id")) for row in rows}
    state_ids.discard(None)
    country_ids.discard(None)
    parent_ids.discard(None)
    states = _related_rows(env, "res.country.state", state_ids, ("name",))
    countries = _related_rows(env, "res.country", country_ids, ("name",))
    parents = _related_rows(
        env, "res.partner", parent_ids, ("complete_name", "company_id")
    )
    result = []
    for row in rows:
        row_company_id = _reference_id(row.get("company_id"))
        parent_id = _reference_id(row.get("parent_id"))
        if row_company_id not in {None, company_id}:
            raise ValueError("partner outside company")
        if parent_id is not None and _reference_id(
            parents[parent_id]["company_id"]
        ) not in {
            None,
            company_id,
        }:
            raise ValueError("partner parent outside company")
        display_name = row.get("display_name")
        name = row.get("name") or display_name
        company_type = row.get("company_type")
        customer_rank = row.get("customer_rank")
        supplier_rank = row.get("supplier_rank")
        if (
            not _valid_id(row.get("id"))
            or not isinstance(name, str)
            or not name.strip()
            or not isinstance(display_name, str)
            or not display_name.strip()
            or company_type not in {"person", "company"}
            or not isinstance(row.get("active"), bool)
            or not isinstance(customer_rank, int)
            or isinstance(customer_rank, bool)
            or customer_rank < 0
            or not isinstance(supplier_rank, int)
            or isinstance(supplier_rank, bool)
            or supplier_rank < 0
        ):
            raise ValueError("invalid partner")
        state_id = _reference_id(row.get("state_id"))
        country_id = _reference_id(row.get("country_id"))
        result.append(
            {
                "id": row["id"],
                "name": name,
                "display_name": display_name,
                "company_type": company_type,
                "active": row["active"],
                "vat": _optional_text(row.get("vat")),
                "reference": _partner_business_reference(row.get("ref")),
                "email": _optional_text(row.get("email")),
                "phone": _optional_text(row.get("phone")),
                "mobile": _optional_text(row.get("mobile")),
                "street": _optional_text(row.get("street")),
                "street2": _optional_text(row.get("street2")),
                "city": _optional_text(row.get("city")),
                "zip": _optional_text(row.get("zip")),
                "state": _named_reference(states[state_id])
                if state_id is not None
                else None,
                "country": (
                    _named_reference(countries[country_id])
                    if country_id is not None
                    else None
                ),
                "language": _optional_text(row.get("lang")),
                "company_id": row_company_id,
                "parent": (
                    _named_reference(parents[parent_id])
                    if parent_id is not None
                    else None
                ),
                "customer_rank": customer_rank,
                "supplier_rank": supplier_rank,
            }
        )
    return result


def _normalize_reference_items(
    env: Any,
    capability_id: str,
    rows: list[dict[str, Any]],
    company_id: int,
) -> list[dict[str, Any]]:
    kind = _REFERENCE_KINDS[capability_id]
    if kind == "partner":
        return _normalize_partners(env, rows, company_id)
    if kind == "product":
        return _normalize_products(env, rows, company_id)
    if kind == "plan":
        return _normalize_plans(env, rows)
    if kind == "analytic":
        return _normalize_analytic_accounts(env, rows, company_id)
    if kind == "fiscal_position":
        return _normalize_fiscal_positions(env, rows, company_id)
    if kind == "cash_rounding":
        return _normalize_cash_roundings(env, rows, company_id)
    if kind == "journal_group":
        return _normalize_journal_groups(env, rows, company_id)
    if kind == "incoterm":
        return _normalize_incoterms(rows)
    if kind == "partner_bank":
        return _normalize_partner_banks(env, rows, company_id)
    if kind == "bank_statement":
        return _normalize_bank_statements(env, rows, company_id)
    if kind == "partial_reconcile":
        return _normalize_partial_reconciles(env, rows, company_id)
    if kind == "full_reconcile":
        return _normalize_full_reconciles(env, rows, company_id)
    return _normalize_tags_or_tax_groups(env, capability_id, rows, company_id)


def _support_rows(
    env: Any, capability_id: str, parameters: dict[str, Any], company_id: int
) -> tuple[list[dict[str, Any]], bool]:
    model_name = (
        "account.payment.method.line"
        if capability_id == "payment.method.list"
        else "account.reconcile.model"
    )
    model = env[model_name].with_context(
        active_test=False, allowed_company_ids=[company_id]
    )
    base_domain = [("company_id", "=", company_id)]
    cursor_found = True
    if parameters["after_id"] is not None:
        cursor_found = bool(
            model.search_count(
                [*base_domain, ("id", "=", parameters["after_id"])], limit=1
            )
        )
    if not cursor_found:
        return [], False
    domain = list(base_domain)
    if parameters["after_id"] is not None:
        domain.append(("id", ">", parameters["after_id"]))
    fields = (
        [
            "id",
            "name",
            "payment_type",
            "sequence",
            "company_id",
            "payment_method_id",
            "journal_id",
            "payment_account_id",
        ]
        if capability_id == "payment.method.list"
        else [
            "id",
            "name",
            "sequence",
            "active",
            "company_id",
            "match_amount",
            "match_amount_min",
            "match_amount_max",
            "match_label",
            "match_label_param",
        ]
    )
    return (
        model.search_read(domain, fields=fields, limit=parameters["limit"], order="id"),
        True,
    )


def _normalize_support(
    env: Any, capability_id: str, rows: list[dict[str, Any]], company_id: int
) -> list[dict[str, Any]]:
    if capability_id in {
        "reconciliation.model.list",
        "reconciliation.model.get",
    }:
        for row in rows:
            if _reference_id(row["company_id"]) != company_id:
                raise ValueError("reconciliation model outside company")
            row["company_id"] = company_id
            row["match_amount"] = _optional_text(row["match_amount"])
            row["match_amount_min"] = _decimal_string(row["match_amount_min"])
            row["match_amount_max"] = _decimal_string(row["match_amount_max"])
            row["match_label"] = _optional_text(row["match_label"])
            row["match_label_param"] = _optional_text(row["match_label_param"])
        return rows
    method_ids = {_reference_id(row.get("payment_method_id")) for row in rows}
    journal_ids = {_reference_id(row.get("journal_id")) for row in rows}
    account_ids = {_reference_id(row.get("payment_account_id")) for row in rows}
    account_ids.discard(None)
    if None in method_ids or None in journal_ids:
        raise ValueError("missing payment method relation")
    methods = _related_rows(env, "account.payment.method", method_ids, ("code", "name"))
    journals = _related_rows(
        env, "account.journal", journal_ids, ("code", "name", "company_id")
    )
    accounts = _related_rows(
        env, "account.account", account_ids, ("code", "name", "company_ids")
    )
    result = []
    for row in rows:
        method_id = _reference_id(row["payment_method_id"])
        journal_id = _reference_id(row["journal_id"])
        account_id = _reference_id(row["payment_account_id"])
        if (
            _reference_id(row["company_id"]) != company_id
            or _reference_id(journals[journal_id]["company_id"]) != company_id
            or (
                account_id is not None
                and company_id not in accounts[account_id]["company_ids"]
            )
        ):
            raise ValueError("payment method outside company")
        result.append(
            {
                "id": row["id"],
                "name": row["name"],
                "payment_type": row["payment_type"],
                "sequence": row["sequence"],
                "company_id": company_id,
                "payment_method": {
                    "id": method_id,
                    "code": methods[method_id]["code"],
                    "name": methods[method_id]["name"],
                },
                "journal": _coded_reference(journals[journal_id]),
                "payment_account": _coded_reference(accounts[account_id])
                if account_id is not None
                else None,
            }
        )
    return result


def dispatch(
    env: Any,
    payload: Any,
    company_id: int,
    *,
    failure_type: type[Exception],
) -> dict[str, Any]:
    """Dispatch one allowlisted core-object read inside the caller's read cursor."""

    if not isinstance(payload, dict) or set(payload) != {
        "capability_id",
        "company_id",
        "parameters",
    }:
        raise _protocol_failure(failure_type)
    capability_id = payload["capability_id"]
    parameters = payload["parameters"]
    if (
        capability_id not in CAPABILITY_IDS
        or payload["company_id"] != company_id
        or not _valid_parameters(capability_id, parameters)
    ):
        raise _protocol_failure(failure_type)

    try:
        company_visible = bool(
            env["res.company"].search_count([("id", "=", company_id)], limit=1)
        )
        required_models = _REQUIRED_MODELS[capability_id]
        module_installed = all(
            env.registry.get(model_name) is not None for model_name in required_models
        )
        required_group = (
            "account.group_account_user"
            if capability_id
            in {"analytic.applicability.list", "analytic.applicability.get"}
            else "account.group_account_readonly"
        )
        access_allowed = bool(
            company_visible
            and module_installed
            and env.user.has_group(required_group)
            and all(
                env[model_name].has_access("read") for model_name in required_models
            )
        )
        if not access_allowed:
            return _empty_page(
                env,
                company_visible=company_visible,
                module_installed=module_installed,
                access_allowed=access_allowed,
            )

        cursor_found = True
        if capability_id in _GET_IDS:
            rows = _raw_get_rows(env, capability_id, company_id, parameters)
        elif capability_id == "journal_item.search":
            rows, cursor_found = _journal_item_rows(env, parameters, company_id)
        elif capability_id == "analytic.line.search":
            rows, cursor_found = _analytic_line_rows(env, parameters, company_id)
        elif capability_id == "analytic.distribution_model.list":
            rows, cursor_found = _distribution_model_rows(env, parameters, company_id)
        elif capability_id == "analytic.applicability.list":
            rows, cursor_found = _applicability_rows(env, parameters, company_id)
        elif capability_id == "budget.search":
            rows, cursor_found = _budget_rows(env, parameters, company_id)
        elif capability_id == "budget.line.list":
            rows, cursor_found = _budget_line_rows(env, parameters, company_id)
        elif capability_id in _PAGED_REFERENCE_MODELS:
            rows, cursor_found = _reference_rows(
                env, capability_id, parameters, company_id
            )
        else:
            rows, cursor_found = _support_rows(
                env, capability_id, parameters, company_id
            )
        if not cursor_found:
            return _empty_page(
                env,
                company_visible=True,
                module_installed=True,
                access_allowed=True,
                cursor_found=False,
            )

        if capability_id in {
            "account.account.get",
            "journal.get",
            "tax.get",
            "payment_term.get",
            "currency.get",
        }:
            items = _normalize_master(env, capability_id, rows, company_id)
        elif capability_id == "partner.accounting.get":
            items = _normalize_partner(env, rows, company_id)
        elif capability_id == "bank.transaction.get":
            items = _normalize_bank(env, rows, company_id)
        elif capability_id in {"journal_item.search", "journal_item.get"}:
            items = _normalize_journal_items(env, rows, company_id)
        elif capability_id in {"analytic.line.search", "analytic.line.get"}:
            items = _normalize_analytic_lines(env, rows, company_id)
        elif capability_id in {
            "analytic.distribution_model.list",
            "analytic.distribution_model.get",
        }:
            items = _normalize_distribution_models(env, rows, company_id)
        elif capability_id in {
            "analytic.applicability.list",
            "analytic.applicability.get",
        }:
            items = _normalize_applicabilities(env, rows, company_id)
        elif capability_id in {"budget.search", "budget.get"}:
            items = _normalize_budgets(env, rows, company_id)
        elif capability_id in {"budget.line.list", "budget.line.get"}:
            items = _normalize_budget_lines(env, rows, company_id)
        elif capability_id in _REFERENCE_KINDS:
            items = _normalize_reference_items(env, capability_id, rows, company_id)
        else:
            items = _normalize_support(env, capability_id, rows, company_id)
        return {
            "user_id": env.uid,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "cursor_found": True,
            "items": items,
        }
    except failure_type:
        raise
    except Exception as exc:
        raise _runtime_failure(failure_type) from exc
