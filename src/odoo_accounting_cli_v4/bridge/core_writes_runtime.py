"""Odoo-side implementation of the closed core-write batches.

The caller supplies a business-user environment.  This module never elevates it and
never accepts a model name, method name, or company context from capability
parameters.
"""

from __future__ import annotations

import calendar
import hashlib
import json
import re
from collections.abc import Mapping
from copy import deepcopy
from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from math import isfinite
from time import strftime, strptime
from types import SimpleNamespace
from typing import Any

from odoo_accounting_cli_v4 import account_processing_contracts as account_processing
from odoo_accounting_cli_v4 import analytic_processing_contracts as analytic_processing
from odoo_accounting_cli_v4 import company_processing_contracts as company_processing
from odoo_accounting_cli_v4 import fiscal_mapping_contracts as fiscal_mappings
from odoo_accounting_cli_v4 import (
    invoice_preparation_contracts as invoice_preparation,
)
from odoo_accounting_cli_v4 import (
    invoice_presentation_contracts as invoice_presentation,
)
from odoo_accounting_cli_v4 import (
    journal_item_processing_contracts as journal_item_processing,
)
from odoo_accounting_cli_v4 import journal_processing_contracts as journal_processing
from odoo_accounting_cli_v4 import move_processing_contracts as move_processing
from odoo_accounting_cli_v4 import partner_preferences_contracts as partner_preferences
from odoo_accounting_cli_v4 import (
    payment_configuration_contracts as payment_configuration,
)
from odoo_accounting_cli_v4 import payment_processing_contracts as payment_processing
from odoo_accounting_cli_v4 import (
    payment_term_processing_contracts as payment_term_processing,
)
from odoo_accounting_cli_v4 import (
    reconciliation_processing_contracts as reconciliation_processing,
)
from odoo_accounting_cli_v4 import report_budget_contracts as report_budgets
from odoo_accounting_cli_v4 import tax_processing_contracts as tax_processing

ACTION = "accounting.core_write.execute"
CAPABILITIES = invoice_preparation.CAPABILITY_IDS | journal_item_processing.CAPABILITY_IDS | company_processing.CAPABILITY_IDS | analytic_processing.CAPABILITY_IDS | journal_processing.CAPABILITY_IDS | account_processing.CAPABILITY_IDS | tax_processing.CAPABILITY_IDS | payment_term_processing.CAPABILITY_IDS | reconciliation_processing.CAPABILITY_IDS | payment_processing.CAPABILITY_IDS | invoice_presentation.CAPABILITY_IDS | move_processing.CAPABILITY_IDS | partner_preferences.CAPABILITY_IDS | payment_configuration.CAPABILITY_IDS | fiscal_mappings.CAPABILITY_IDS | report_budgets.CAPABILITY_IDS | frozenset(
    {
        "customer_invoice.create",
        "vendor_bill.create",
        "invoice.update",
        "invoice.lines.replace",
        "invoice.lines.update",
        "invoice.lines.add",
        "invoice.lines.remove",
        "invoice.line.create",
        "invoice.line.update",
        "invoice.line.delete",
        "invoice.delete",
        "invoice.cancel",
        "invoice.reset_to_draft",
        "invoice.post",
        "invoice.duplicate",
        "invoice.reverse_and_reissue",
        "invoice.type.switch",
        "journal_entry.create",
        "journal_entry.update",
        "journal_entry.lines.replace",
        "journal_entry.lines.add",
        "journal_entry.lines.remove",
        "journal_entry.duplicate",
        "journal_entry.delete",
        "journal_entry.cancel",
        "journal_entry.reset_to_draft",
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
        "account.transfer_model.create",
        "account.transfer_model.update",
        "account.transfer_model.duplicate",
        "account.transfer_model.enable",
        "account.transfer_model.disable",
        "account.transfer_model.archive",
        "account.transfer_model.restore",
        "account.transfer_model.delete",
        "localization.china.period_transfer.run",
        "payment.create",
        "payment.update_draft",
        "payment.reset_to_draft",
        "bank.transaction.update",
        "bank.transaction.match",
        "bank.transaction.unmatch",
        "bank.transaction.counterparts.replace",
        "bank.statement.create",
        "bank.statement.update",
        "bank.statement.delete",
        "bank.transaction.delete",
        "payment.duplicate",
        "payment.delete",
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
        "account.return.create",
        "account.return.checks.refresh",
        "account.return.check.result.update",
        "account.return.validate",
        "account.return.mark_submitted",
        "account.return.archive",
        "account.return.restore",
        "account.return.delete",
        "product.create",
        "product.update",
        "product.duplicate",
        "product.archive",
        "product.restore",
        "product.cost.update",
        "product.accounting_profile.update",
        "product.category.accounting_profile.update",
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
        "currency.rate.record",
        "currency.rate.update",
        "currency.rate.delete",
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
        "sale.order.create",
        "sale.order.update_draft",
        "sale.order.lines.replace",
        "sale.order.confirm",
        "sale.order.cancel",
        "sale.order.reset_to_draft",
        "sale.order.invoice.create",
        "sale.order.down_payment.create",
        "stock.transfer.create",
        "stock.transfer.confirm",
        "stock.transfer.assign",
        "stock.transfer.quantities.set",
        "stock.transfer.validate",
        "stock.transfer.unreserve",
        "stock.transfer.cancel",
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
    }
)

_PAYLOAD_KEYS = {
    "capability_id",
    "company_id",
    "idempotency_key",
    "confirmation",
    "parameters",
}
_RESULT_KEYS = {
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
_DOCUMENT_TYPES = ("out_invoice", "in_invoice", "out_refund", "in_refund")
_INVOICE_UPDATE_KEYS = frozenset(
    {
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
)
_JOURNAL_ENTRY_UPDATE_KEYS = frozenset({"date", "journal_id", "reference"})
_INVOICE_LIFECYCLE_CAPABILITIES = frozenset(
    {
        "invoice.update",
        "invoice.lines.replace",
        "invoice.lines.update",
        "invoice.lines.add",
        "invoice.lines.remove",
        "invoice.line.create",
        "invoice.line.update",
        "invoice.line.delete",
        "invoice.delete",
        "invoice.cancel",
        "invoice.reset_to_draft",
    }
)
_JOURNAL_ENTRY_LIFECYCLE_CAPABILITIES = frozenset(
    {
        "journal_entry.update",
        "journal_entry.lines.replace",
        "journal_entry.duplicate",
        "journal_entry.delete",
        "journal_entry.cancel",
        "journal_entry.reset_to_draft",
    }
)
_DRAFT_DOCUMENT_MAINTENANCE_CAPABILITIES = frozenset(
    {
        "invoice.line.create",
        "invoice.line.update",
        "invoice.line.delete",
        "invoice.delete",
        "journal_entry.duplicate",
        "journal_entry.delete",
    }
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
_SALE_ORDER_INVOICE_CAPABILITY = "sale.order.invoice.create"
_SALE_DOWN_PAYMENT_CAPABILITY = "sale.order.down_payment.create"
_STOCK_TRANSFER_CREATE_CAPABILITY = "stock.transfer.create"
_STOCK_TRANSFER_ACTION_CAPABILITIES = frozenset(
    {
        "stock.transfer.confirm",
        "stock.transfer.assign",
        "stock.transfer.unreserve",
        "stock.transfer.cancel",
    }
)
_STOCK_TRANSFER_QUANTITIES_CAPABILITY = "stock.transfer.quantities.set"
_STOCK_TRANSFER_VALIDATE_CAPABILITY = "stock.transfer.validate"
_STOCK_TRANSFER_CAPABILITIES = (
    {_STOCK_TRANSFER_CREATE_CAPABILITY}
    | _STOCK_TRANSFER_ACTION_CAPABILITIES
    | {
        _STOCK_TRANSFER_QUANTITIES_CAPABILITY,
        _STOCK_TRANSFER_VALIDATE_CAPABILITY,
    }
)
_PURCHASE_BILL_CAPABILITIES = frozenset(
    {
        "purchase.order.bill.create",
        "purchase_bill.match",
        "purchase_bill.lines.unmatch",
    }
)
_PAYMENT_TERM_CAPABILITIES = frozenset(
    {
        "payment_term.create",
        "payment_term.update",
        "payment_term.lines.replace",
        "payment_term.archive",
        "payment_term.restore",
    }
)
_PAYMENT_TERM_HEADER_KEYS = frozenset(
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
_FISCAL_POSITION_CAPABILITIES = frozenset(
    {
        "fiscal_position.create",
        "fiscal_position.update",
        "fiscal_position.account_mappings.replace",
        "fiscal_position.archive",
        "fiscal_position.restore",
    }
)
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
_FISCAL_POSITION_CREATE_DEFAULTS = {
    "sequence": 0,
    "auto_apply": False,
    "vat_required": False,
    "country_id": None,
    "country_group_id": None,
    "state_ids": [],
    "zip_from": None,
    "zip_to": None,
    "note": None,
}
_JOURNAL_GROUP_CAPABILITIES = frozenset(
    {"journal.group.create", "journal.group.update"}
)
_JOURNAL_GROUP_FIELDS = frozenset({"name", "sequence", "excluded_journal_ids"})
_JOURNAL_GROUP_CREATE_DEFAULTS = {"sequence": 10, "excluded_journal_ids": []}
_TRANSFER_MODEL_CAPABILITIES = frozenset(
    {
        "account.transfer_model.create",
        "account.transfer_model.update",
        "account.transfer_model.duplicate",
        "account.transfer_model.enable",
        "account.transfer_model.disable",
        "account.transfer_model.archive",
        "account.transfer_model.restore",
        "account.transfer_model.delete",
    }
)
_TRANSFER_MODEL_FIELDS = frozenset(
    {
        "name",
        "journal_id",
        "date_start",
        "date_stop",
        "frequency",
        "origin_account_ids",
        "destination_lines",
    }
)
_PRODUCT_WRITE_CAPABILITIES = frozenset(
    {
        "product.create",
        "product.update",
        "product.duplicate",
        "product.archive",
        "product.restore",
        "product.cost.update",
        "product.accounting_profile.update",
        "product.category.accounting_profile.update",
    }
)
_PRODUCT_ARCHIVE_CAPABILITIES = frozenset({"product.archive", "product.restore"})
_PRODUCT_ARCHIVE_ADDITIONAL_GROUP = "stock.group_stock_manager"
_PRODUCT_BASIC_FIELDS = frozenset(
    {
        "name",
        "default_code",
        "product_type",
        "category_id",
        "uom_id",
        "barcode",
        "sale_ok",
        "purchase_ok",
        "list_price",
    }
)
_PRODUCT_CREATE_REQUIRED_FIELDS = frozenset(
    {"name", "default_code", "product_type", "category_id", "uom_id"}
)
_PRODUCT_ACCOUNTING_PROFILE_FIELDS = frozenset(
    {
        "income_account_id",
        "expense_account_id",
        "sale_tax_ids",
        "purchase_tax_ids",
        "invoice_policy",
        "purchase_method",
    }
)
_PRODUCT_CATEGORY_ACCOUNTING_PROFILE_FIELDS = frozenset(
    {"income_account_id", "expense_account_id"}
)
_ACCOUNTING_REFERENCE_WRITE_CAPABILITIES = frozenset(
    {
        "currency.rate.record",
        "currency.rate.update",
        "currency.rate.delete",
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
    }
)
_ACCOUNT_TAG_FIELDS = frozenset({"name", "applicability", "color", "country_id"})
_TAX_GROUP_ACCOUNT_FIELDS = frozenset({
    "tax_payable_account_id", "tax_receivable_account_id", "advance_tax_payment_account_id",
})
_TAX_GROUP_FIELDS = frozenset({"name", "sequence", "preceding_subtotal"}) | _TAX_GROUP_ACCOUNT_FIELDS
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
_FISCAL_YEAR_FIELDS = frozenset({"name", "date_from", "date_to"})
_ANALYTIC_APPLICABILITY_FIELDS = frozenset(
    {
        "plan_id",
        "business_domain",
        "applicability",
        "account_prefix",
        "product_category_id",
    }
)
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
_ACCOUNT_GROUP_FIELDS = frozenset(
    {"name", "code_prefix_start", "code_prefix_end"}
)
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
_SALE_ORDER_UPDATE_KEYS = frozenset(
    {"client_order_ref", "validity_date", "commitment_date", "payment_term_id"}
)
_PURCHASE_ORDER_UPDATE_KEYS = frozenset(
    {"partner_ref", "date_order", "payment_term_id", "incoterm_id"}
)
_DECIMAL_PATTERN = re.compile(r"^(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
_SIGNED_DECIMAL_PATTERN = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
_IDEMPOTENCY_KEY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")
_ASSET_METHODS = frozenset({"linear", "degressive", "degressive_then_linear"})
_ASSET_PRORATA_TYPES = frozenset({"none", "constant_periods", "daily_computation"})
_ASSET_BASE_NAME_MAXIMUM = 426
_ANALYTIC_APPLICABILITIES = frozenset({"optional", "mandatory", "unavailable"})
_ANALYTIC_PLAN_UPDATE_KEYS = frozenset(
    {"name", "color", "default_applicability"}
)
_ANALYTIC_ACCOUNT_UPDATE_KEYS = frozenset({"name", "code", "partner_id", "active"})
_ANALYTIC_LINE_UPDATE_KEYS = frozenset(
    {
        "name",
        "date",
        "amount",
        "analytic_account_id",
        "reference",
        "unit_amount",
    }
)
_BUDGET_UPDATE_KEYS = frozenset({"name", "date_from", "date_to", "budget_type"})
_BUDGET_TYPES = frozenset({"revenue", "expense", "both"})
_VISIBLE_MARKER_SUFFIX = re.compile(r"( \[ODACV4:[0-9a-f]{64}\])$")
_PARTNER_REF_MARKER_SUFFIX = re.compile(r"(?:^| )\[ODACV4:[0-9a-f]{64}\]$")
_PARTNER_CONTACT_KEYS = frozenset(
    {
        "name",
        "company_type",
        "vat",
        "reference",
        "email",
        "phone",
        "mobile",
        "street",
        "street2",
        "city",
        "zip",
        "state_id",
        "country_id",
        "language",
    }
)
_PARTNER_ACCOUNTING_KEYS = frozenset(
    {
        "property_account_receivable_id",
        "property_account_payable_id",
        "property_account_position_id",
        "property_payment_term_id",
        "property_supplier_payment_term_id",
    }
)
_PARTNER_BANK_KEYS = frozenset(
    {"account_number", "account_holder_name", "bank_id", "currency_id"}
)
_ACCOUNT_CONFIG_KEYS = frozenset(
    {"code", "name", "account_type", "reconcile", "currency_id"}
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
        "expense_other",
        "expense_depreciation",
        "expense_direct_cost",
        "off_balance",
    }
)
_JOURNAL_CREATE_KEYS = frozenset(
    {"name", "code", "type", "sequence", "currency_id", "default_account_id"}
)
_JOURNAL_UPDATE_KEYS = frozenset(
    {"name", "code", "sequence", "currency_id", "default_account_id"}
)
_JOURNAL_TYPES = frozenset({"sale", "purchase", "cash", "bank", "credit", "general"})
_JOURNAL_DEFAULT_ACCOUNT_TYPES = {
    "sale": frozenset({"income", "income_other"}),
    "purchase": frozenset({"expense", "expense_depreciation", "expense_direct_cost"}),
    "cash": frozenset({"asset_cash"}),
    "bank": frozenset({"asset_cash", "liability_credit_card"}),
    "credit": frozenset({"liability_credit_card"}),
    "general": _ACCOUNT_TYPES,
}
_TAX_CONFIG_REQUIRED_KEYS = frozenset(
    {
        "name",
        "type_tax_use",
        "amount_type",
        "amount",
        "sequence",
        "tax_group_id",
        "invoice_label",
        "price_include_override",
        "include_base_amount",
        "is_base_affected",
    }
)
_TAX_CONFIG_KEYS = _TAX_CONFIG_REQUIRED_KEYS | frozenset({
    "children_tax_ids", "tax_scope", "analytic", "tax_exigibility",
    "cash_basis_transition_account_id",
})
_TAX_USE_TYPES = frozenset({"sale", "purchase", "none"})
_TAX_AMOUNT_TYPES = frozenset({"fixed", "percent", "division", "group"})
_TAX_PRICE_INCLUDE_OVERRIDES = frozenset({"tax_included", "tax_excluded"})

_DOCUMENT_CREATE_REQUIRED_KEYS = frozenset(
    {"partner_id", "journal_id", "invoice_date", "currency_id", "lines"}
)
_DOCUMENT_CREATE_OPTIONAL_KEYS = frozenset(
    {
        "date",
        "invoice_date_due",
        "payment_term_id",
        "partner_bank_id",
        "fiscal_position_id",
        "reference",
        "payment_reference",
    }
)
_DOCUMENT_LINE_REQUIRED_KEYS = frozenset(
    {"name", "account_id", "quantity", "price_unit", "tax_ids"}
)
_DEFERRED_LINE_DATE_FIELDS = ("deferred_start_date", "deferred_end_date")
_INVOICE_LINE_INPUT_FIELDS = frozenset({"product_uom_id", "deductible_amount"})
_DOCUMENT_LINE_OPTIONAL_KEYS = frozenset(
    {"product_id", "discount", "analytic_distribution", *_DEFERRED_LINE_DATE_FIELDS}
) | _INVOICE_LINE_INPUT_FIELDS
_ENTRY_LINE_REQUIRED_KEYS = frozenset(
    {"name", "account_id", "partner_id", "debit", "credit"}
)
_ENTRY_TAX_FIELDS = frozenset(journal_item_processing.TAX_FIELDS)
_ENTRY_LINE_OPTIONAL_KEYS = frozenset(
    {"currency_id", "amount_currency", "analytic_distribution", "date_maturity"}
) | _ENTRY_TAX_FIELDS
_PAYMENT_REGISTER_REFERENCE_FIELDS = frozenset(
    {"payment_method_line_id", "partner_bank_id"}
)
_PAYMENT_INSTALLMENT_FIELDS = frozenset(
    {"installments_mode", "group_payment", "installment_cutoff_date"}
)
_PRODUCT_POLICY_FIELDS = {"invoice_policy": {"order", "delivery"}, "purchase_method": {"purchase", "receive"}}
_REFUND_REQUIRED_KEYS = frozenset({"move_id", "date", "reason"})
_PAYMENT_REGISTER_REQUIRED_KEYS = frozenset({"move_id", "journal_id", "payment_date"})
_PAYMENT_REGISTER_MANY_REQUIRED_KEYS = frozenset(
    {"move_ids", "journal_id", "payment_date"}
)

_PARAMETER_KEYS = {
    "customer_invoice.create": {
        "partner_id",
        "journal_id",
        "date",
        "invoice_date",
        "currency_id",
        "lines",
        "invoice_date_due",
        "payment_term_id",
        "partner_bank_id",
        "fiscal_position_id",
        "reference",
        "payment_reference",
    },
    "vendor_bill.create": {
        "partner_id",
        "journal_id",
        "date",
        "invoice_date",
        "currency_id",
        "lines",
        "invoice_date_due",
        "payment_term_id",
        "partner_bank_id",
        "fiscal_position_id",
        "reference",
        "payment_reference",
    },
    "invoice.update": {"move_id", "changes"},
    "invoice.lines.replace": {"move_id", "lines"},
    "invoice.lines.update": {"move_id", "lines"},
    "invoice.lines.add": {"move_id", "expected_line_ids", "lines"},
    "invoice.lines.remove": {"move_id", "line_ids"},
    "invoice.line.create": {"move_id", "line"},
    "invoice.line.update": {"move_id", "line_id", "changes"},
    "invoice.line.delete": {"move_id", "line_id"},
    "invoice.delete": {"move_id"},
    "invoice.cancel": {"move_id", "move_ids"},
    "invoice.reset_to_draft": {"move_id", "move_ids"},
    "invoice.post": {"move_id", "move_ids"},
    "invoice.duplicate": {"move_id"},
    "invoice.reverse_and_reissue": {"move_id", "date", "reason"},
    "invoice.type.switch": {"move_id", "target_move_type"},
    "journal_entry.create": {"journal_id", "date", "lines", "reference"},
    "journal_entry.update": {"move_id", "changes"},
    "journal_entry.lines.replace": {"move_id", "lines"},
    "journal_entry.lines.add": {"move_id", "expected_line_ids", "lines"},
    "journal_entry.lines.remove": {"move_id", "line_ids"},
    "journal_entry.duplicate": {"move_id"},
    "journal_entry.delete": {"move_id"},
    "journal_entry.cancel": {"move_id", "move_ids"},
    "journal_entry.reset_to_draft": {"move_id", "move_ids"},
    "journal_entry.post": {"move_id", "move_ids"},
    "journal_entry.reverse": {"move_id", "date", "reason"},
    "receivable.payment.register": {
        "move_id",
        "move_ids",
        "journal_id",
        "payment_date",
        "amount",
        "payment_difference_handling",
        "writeoff_account_id",
        "writeoff_label",
        "payment_method_line_id",
        "partner_bank_id",
    },
    "payable.payment.register": {
        "move_id",
        "move_ids",
        "journal_id",
        "payment_date",
        "amount",
        "payment_difference_handling",
        "writeoff_account_id",
        "writeoff_label",
        "payment_method_line_id",
        "partner_bank_id",
    },
    "reconciliation.apply": {"line_ids", "invoice_id", "outstanding_line_id"},
    "payment.cancel": {"payment_id", "payment_ids"},
    "customer_credit_note.create": {"move_id", "move_ids", "date", "reason", "lines"},
    "vendor_refund.create": {"move_id", "move_ids", "date", "reason", "lines"},
    "payment.post": {"payment_id", "payment_ids"},
    "reconciliation.undo": {
        "mode",
        "line_ids",
        "invoice_id",
        "partial_reconcile_id",
        "invoice_line_id",
        "counterpart_line_id",
    },
    "bank.transaction.record": {
        "journal_id",
        "date",
        "amount",
        "payment_ref",
        "partner_id",
        "foreign_currency_id",
        "amount_currency",
        "account_number",
        "partner_name",
    },
    "asset.create": {
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
    },
    "asset.validate": {"asset_id"},
    "asset.cancel": {"asset_id"},
    "asset.dispose": {"asset_id", "date", "note"},
    "asset.pause": {"asset_id", "date", "note"},
    "deferred_expense.generate_entries": {"date_to"},
    "deferred_revenue.generate_entries": {"date_to"},
    "multicurrency.revaluation.generate_entries": {
        "date",
        "reversal_date",
        "journal_id",
        "expense_provision_account_id",
        "income_provision_account_id",
    },
    "reconciliation.automatic.run": {"line_ids"},
    "period.transfer.run": {"transfer_model_id", "run_date"},
    "account.transfer_model.create": set(_TRANSFER_MODEL_FIELDS),
    "account.transfer_model.update": {"transfer_model_id", "changes"},
    "account.transfer_model.duplicate": {"transfer_model_id", "name"},
    "account.transfer_model.enable": {"transfer_model_id"},
    "account.transfer_model.disable": {"transfer_model_id"},
    "account.transfer_model.archive": {"transfer_model_id"},
    "account.transfer_model.restore": {"transfer_model_id"},
    "account.transfer_model.delete": {"transfer_model_id"},
    "localization.china.period_transfer.run": {"run_date"},
    "payment.create": {
        "payment_type",
        "partner_type",
        "partner_id",
        "amount",
        "currency_id",
        "journal_id",
        "payment_method_line_id",
        "date",
        "payment_reference",
    },
    "payment.update_draft": {"payment_id", "changes"},
    "payment.reset_to_draft": {"payment_id", "payment_ids"},
    "bank.transaction.update": {"transaction_id", "changes"},
    "bank.transaction.match": {"transaction_id", "candidate_line_ids"},
    "bank.transaction.unmatch": {"transaction_id"},
    "bank.transaction.counterparts.replace": {"transaction_id", "lines"},
    "bank.statement.create": {
        "transaction_ids",
        "reference",
        "balance_end_real",
        "balance_start",
        "name",
        "date",
    },
    "bank.statement.update": {"statement_id", "changes"},
    "bank.statement.delete": {"statement_id"},
    "bank.transaction.delete": {"transaction_id"},
    "payment.duplicate": {"payment_id"},
    "payment.delete": {"payment_id"},
    "reconciliation.write_off": {
        "transaction_id",
        "write_off_account_id",
        "label",
        "expected_residual_amount",
    },
    "analytic.plan.create": {
        "name",
        "parent_plan_id",
        "color",
        "default_applicability",
    },
    "analytic.plan.update": {"plan_id", "changes"},
    "analytic.account.create": {"name", "plan_id", "code", "partner_id"},
    "analytic.account.update": {"analytic_account_id", "changes"},
    "analytic.account.archive": {"analytic_account_id"},
    "analytic.account.restore": {"analytic_account_id"},
    "analytic.line.create": {
        "name",
        "date",
        "amount",
        "analytic_account_id",
        "reference",
        "unit_amount",
    },
    "analytic.line.update": {"analytic_line_id", "changes"},
    "analytic.line.delete": {"analytic_line_id"},
    "account.return.create": {"return_type_id", "date_from", "date_to"},
    "account.return.checks.refresh": {"return_id"},
    "account.return.check.result.update": {"check_id", "result"},
    "account.return.validate": {"return_id"},
    "account.return.mark_submitted": {"return_id"},
    "account.return.archive": {"return_id"},
    "account.return.restore": {"return_id"},
    "account.return.delete": {"return_id"},
    "product.create": set(_PRODUCT_BASIC_FIELDS),
    "product.update": {"product_id", "changes"},
    "product.duplicate": {"product_id", "name", "default_code"},
    "product.archive": {"product_id"},
    "product.restore": {"product_id"},
    "product.cost.update": {"product_id", "standard_price"},
    "product.accounting_profile.update": {"product_id", "changes"},
    "product.category.accounting_profile.update": {"category_id", "changes"},
    "budget.create": {"name", "date_from", "date_to", "budget_type"},
    "budget.update_draft": {"budget_id", "changes"},
    "budget.lines.replace": {"budget_id", "lines"},
    "budget.confirm": {"budget_id"},
    "budget.reset_to_draft": {"budget_id"},
    "budget.cancel": {"budget_id"},
    "budget.mark_done": {"budget_id"},
    "partner.create": set(_PARTNER_CONTACT_KEYS),
    "partner.update": {"partner_id", "changes"},
    "partner.archive": {"partner_id"},
    "partner.restore": {"partner_id"},
    "partner.accounting.update": {"partner_id", "changes"},
    "partner.bank_account.create": {
        "partner_id",
        "account_number",
        "account_holder_name",
        "bank_id",
        "currency_id",
    },
    "partner.bank_account.update": {"partner_bank_id", "changes"},
    "partner.bank_account.archive": {"partner_bank_id"},
    "partner.bank_account.restore": {"partner_bank_id"},
    "account.account.create": set(_ACCOUNT_CONFIG_KEYS),
    "account.account.update": {"account_id", "changes"},
    "account.account.archive": {"account_id"},
    "account.account.restore": {"account_id"},
    "journal.create": set(_JOURNAL_CREATE_KEYS),
    "journal.update": {"journal_id", "changes"},
    "journal.archive": {"journal_id"},
    "journal.restore": {"journal_id"},
    "tax.create": set(_TAX_CONFIG_KEYS),
    "tax.update": {"tax_id", "changes"},
    "tax.archive": {"tax_id"},
    "tax.restore": {"tax_id"},
    "currency.rate.record": {
        "currency_id",
        "date",
        "company_units_per_foreign_unit",
    },
    "currency.rate.update": {"rate_id", "changes"},
    "currency.rate.delete": {"rate_id"},
    "account.group.create": set(_ACCOUNT_GROUP_FIELDS),
    "account.group.update": {"account_group_id", "changes"},
    "tax.repartition_lines.replace": {
        "tax_id",
        "invoice_lines",
        "refund_lines",
    },
    "reconciliation.model.create": set(_RECONCILIATION_MODEL_FIELDS),
    "reconciliation.model.update": {"reconciliation_model_id", "changes"},
    "reconciliation.model.lines.replace": {
        "reconciliation_model_id",
        "lines",
    },
    "reconciliation.model.archive": {"reconciliation_model_id"},
    "reconciliation.model.restore": {"reconciliation_model_id"},
    "account.tag.create": set(_ACCOUNT_TAG_FIELDS),
    "account.tag.update": {"account_tag_id", "changes"},
    "account.tag.archive": {"account_tag_id"},
    "account.tag.restore": {"account_tag_id"},
    "tax.group.create": set(_TAX_GROUP_FIELDS),
    "tax.group.update": {"tax_group_id", "changes"},
    "cash_rounding.create": set(_CASH_ROUNDING_FIELDS),
    "cash_rounding.update": {"cash_rounding_id", "changes"},
    "fiscal_year.create": set(_FISCAL_YEAR_FIELDS),
    "fiscal_year.update": {"id", "changes"},
    "analytic.applicability.create": set(_ANALYTIC_APPLICABILITY_FIELDS),
    "analytic.applicability.update": {"id", "changes"},
    "analytic.distribution_model.create": set(
        _ANALYTIC_DISTRIBUTION_MODEL_FIELDS
    ),
    "analytic.distribution_model.update": {"id", "changes"},
    "sale.order.create": {
        "partner_id",
        "pricelist_id",
        "date_order",
        "client_order_ref",
        "validity_date",
        "commitment_date",
        "payment_term_id",
        "lines",
    },
    "sale.order.update_draft": {"order_id", "changes"},
    "sale.order.lines.replace": {"order_id", "lines"},
    "sale.order.confirm": {"order_id"},
    "sale.order.cancel": {"order_id"},
    "sale.order.reset_to_draft": {"order_id"},
    "sale.order.invoice.create": {"order_id", "order_ids", "consolidated_billing", "deduct_down_payments"},
    "sale.order.down_payment.create": {"order_id", "method", "amount"},
    "stock.transfer.create": {
        "picking_type_id",
        "location_id",
        "location_dest_id",
        "partner_id",
        "scheduled_date",
        "origin",
        "moves",
    },
    "stock.transfer.confirm": {"transfer_id"},
    "stock.transfer.assign": {"transfer_id"},
    "stock.transfer.quantities.set": {"transfer_id", "lines"},
    "stock.transfer.validate": {"transfer_id", "backorder_policy"},
    "stock.transfer.unreserve": {"transfer_id"},
    "stock.transfer.cancel": {"transfer_id"},
    "purchase.order.create": {
        "partner_id",
        "currency_id",
        "picking_type_id",
        "date_order",
        "partner_ref",
        "payment_term_id",
        "incoterm_id",
        "lines",
    },
    "purchase.order.update_draft": {"order_id", "changes"},
    "purchase.order.lines.replace": {"order_id", "lines"},
    "purchase.order.confirm": {"order_id"},
    "purchase.order.cancel": {"order_id"},
    "purchase.order.reset_to_draft": {"order_id"},
    "purchase.order.bill.create": {"order_id", "order_ids"},
    "purchase_bill.match": {"bill_id", "pairs"},
    "purchase_bill.lines.unmatch": {"bill_id", "bill_line_ids"},
    "payment_term.create": {"name", "company_id", "lines"}
    | set(_PAYMENT_TERM_HEADER_KEYS),
    "payment_term.update": {"payment_term_id"} | set(_PAYMENT_TERM_HEADER_KEYS),
    "payment_term.lines.replace": {"payment_term_id", "lines"},
    "payment_term.archive": {"payment_term_id"},
    "payment_term.restore": {"payment_term_id"},
    "period.accrual.generate": {
        "source_model",
        "order_ids",
        "date",
        "reversal_date",
        "journal_id",
        "accrual_account_id",
        "amount",
    },
    "fiscal_position.create": set(_FISCAL_POSITION_FIELDS),
    "fiscal_position.update": {"fiscal_position_id", "changes"},
    "fiscal_position.account_mappings.replace": {
        "fiscal_position_id",
        "mappings",
    },
    "fiscal_position.archive": {"fiscal_position_id"},
    "fiscal_position.restore": {"fiscal_position_id"},
    "journal.group.create": set(_JOURNAL_GROUP_FIELDS),
    "journal.group.update": {"journal_group_id", "changes"},
}

_GROUPS = {
    "customer_invoice.create": "account.group_account_invoice",
    "vendor_bill.create": "account.group_account_invoice",
    "invoice.update": "account.group_account_invoice",
    "invoice.lines.replace": "account.group_account_invoice",
    "invoice.line.create": "account.group_account_invoice",
    "invoice.line.update": "account.group_account_invoice",
    "invoice.line.delete": "account.group_account_invoice",
    "invoice.delete": "account.group_account_invoice",
    "invoice.cancel": "account.group_account_invoice",
    "invoice.reset_to_draft": "account.group_account_invoice",
    "invoice.post": "account.group_account_invoice",
    "invoice.duplicate": "account.group_account_invoice",
    "invoice.type.switch": "account.group_account_invoice",
    "journal_entry.create": "account.group_account_user",
    "journal_entry.update": "account.group_account_user",
    "journal_entry.lines.replace": "account.group_account_user",
    "journal_entry.duplicate": "account.group_account_user",
    "journal_entry.delete": "account.group_account_user",
    "journal_entry.cancel": "account.group_account_user",
    "journal_entry.reset_to_draft": "account.group_account_user",
    "journal_entry.post": "account.group_account_user",
    "journal_entry.reverse": "account.group_account_user",
    "receivable.payment.register": "account.group_account_invoice",
    "payable.payment.register": "account.group_account_invoice",
    "reconciliation.apply": "account.group_account_user",
    "payment.cancel": "account.group_account_invoice",
    "customer_credit_note.create": "account.group_account_invoice",
    "vendor_refund.create": "account.group_account_invoice",
    "payment.post": "account.group_account_invoice",
    "reconciliation.undo": "account.group_account_user",
    "bank.transaction.record": "account.group_account_user",
    "asset.create": "account.group_account_user",
    "asset.validate": "account.group_account_user",
    "asset.cancel": "account.group_account_user",
    "asset.dispose": "account.group_account_user",
    "asset.pause": "account.group_account_user",
    "deferred_expense.generate_entries": "account.group_account_user",
    "deferred_revenue.generate_entries": "account.group_account_user",
    "multicurrency.revaluation.generate_entries": "account.group_account_user",
    "reconciliation.automatic.run": "account.group_account_user",
    "period.transfer.run": "account.group_account_user",
    "account.transfer_model.create": "account.group_account_manager",
    "account.transfer_model.update": "account.group_account_manager",
    "account.transfer_model.duplicate": "account.group_account_manager",
    "account.transfer_model.enable": "account.group_account_manager",
    "account.transfer_model.disable": "account.group_account_manager",
    "account.transfer_model.archive": "account.group_account_manager",
    "account.transfer_model.restore": "account.group_account_manager",
    "account.transfer_model.delete": "account.group_account_manager",
    "localization.china.period_transfer.run": "account.group_account_user",
    "payment.create": "account.group_account_invoice",
    "payment.update_draft": "account.group_account_invoice",
    "payment.reset_to_draft": "account.group_account_invoice",
    "bank.transaction.update": "account.group_account_user",
    "bank.transaction.match": "account.group_account_user",
    "bank.transaction.unmatch": "account.group_account_user",
    "bank.statement.create": "account.group_account_user",
    "bank.statement.update": "account.group_account_user",
    "bank.statement.delete": "account.group_account_user",
    "bank.transaction.delete": "account.group_account_user",
    "payment.duplicate": "account.group_account_invoice",
    "payment.delete": "account.group_account_invoice",
    "reconciliation.write_off": "account.group_account_user",
    "analytic.plan.create": "account.group_account_user",
    "analytic.plan.update": "account.group_account_user",
    "analytic.account.create": "account.group_account_user",
    "analytic.account.update": "account.group_account_user",
    "analytic.account.archive": "account.group_account_user",
    "analytic.account.restore": "account.group_account_user",
    "analytic.line.create": "account.group_account_user",
    "analytic.line.update": "account.group_account_user",
    "analytic.line.delete": "account.group_account_user",
    "account.return.create": "account.group_account_user",
    "account.return.checks.refresh": "account.group_account_user",
    "account.return.check.result.update": "account.group_account_user",
    "account.return.validate": "account.group_account_user",
    "account.return.mark_submitted": "account.group_account_user",
    "account.return.archive": "account.group_account_user",
    "account.return.restore": "account.group_account_user",
    "account.return.delete": "account.group_account_user",
    "product.create": "product.group_product_manager",
    "product.update": "product.group_product_manager",
    "product.duplicate": "product.group_product_manager",
    "product.archive": "product.group_product_manager",
    "product.restore": "product.group_product_manager",
    "product.cost.update": "product.group_product_manager",
    "product.accounting_profile.update": "product.group_product_manager",
    "product.category.accounting_profile.update": "product.group_product_manager",
    "budget.create": "account.group_account_user",
    "budget.update_draft": "account.group_account_user",
    "budget.lines.replace": "account.group_account_user",
    "budget.confirm": "account.group_account_user",
    "budget.reset_to_draft": "account.group_account_user",
    "budget.cancel": "account.group_account_user",
    "budget.mark_done": "account.group_account_user",
    "partner.create": "base.group_partner_manager",
    "partner.update": "base.group_partner_manager",
    "partner.archive": "base.group_partner_manager",
    "partner.restore": "base.group_partner_manager",
    "partner.accounting.update": "account.group_account_user",
    "partner.bank_account.create": "base.group_partner_manager",
    "partner.bank_account.update": "base.group_partner_manager",
    "partner.bank_account.archive": "base.group_partner_manager",
    "partner.bank_account.restore": "base.group_partner_manager",
    "account.account.create": "account.group_account_manager",
    "account.account.update": "account.group_account_manager",
    "account.account.archive": "account.group_account_manager",
    "account.account.restore": "account.group_account_manager",
    "journal.create": "account.group_account_manager",
    "journal.update": "account.group_account_manager",
    "journal.archive": "account.group_account_manager",
    "journal.restore": "account.group_account_manager",
    "tax.create": "account.group_account_manager",
    "tax.update": "account.group_account_manager",
    "tax.archive": "account.group_account_manager",
    "tax.restore": "account.group_account_manager",
    "currency.rate.record": "account.group_account_manager",
    "account.group.create": "account.group_account_manager",
    "account.group.update": "account.group_account_manager",
    "tax.repartition_lines.replace": "account.group_account_manager",
    "reconciliation.model.create": "account.group_account_manager",
    "reconciliation.model.update": "account.group_account_manager",
    "reconciliation.model.lines.replace": "account.group_account_manager",
    "reconciliation.model.archive": "account.group_account_manager",
    "reconciliation.model.restore": "account.group_account_manager",
    "account.tag.create": "account.group_account_manager",
    "account.tag.update": "account.group_account_manager",
    "account.tag.archive": "account.group_account_manager",
    "account.tag.restore": "account.group_account_manager",
    "tax.group.create": "account.group_account_manager",
    "tax.group.update": "account.group_account_manager",
    "cash_rounding.create": "account.group_account_manager",
    "cash_rounding.update": "account.group_account_manager",
    "fiscal_year.create": "account.group_account_manager",
    "fiscal_year.update": "account.group_account_manager",
    "analytic.applicability.create": "account.group_account_manager",
    "analytic.applicability.update": "account.group_account_manager",
    "analytic.distribution_model.create": "account.group_account_manager",
    "analytic.distribution_model.update": "account.group_account_manager",
    "sale.order.create": "sales_team.group_sale_salesman",
    "sale.order.update_draft": "sales_team.group_sale_salesman",
    "sale.order.lines.replace": "sales_team.group_sale_salesman",
    "sale.order.confirm": "sales_team.group_sale_salesman",
    "sale.order.cancel": "sales_team.group_sale_salesman",
    "sale.order.reset_to_draft": "sales_team.group_sale_salesman",
    "sale.order.invoice.create": "sales_team.group_sale_salesman",
    "sale.order.down_payment.create": "sales_team.group_sale_salesman",
    "stock.transfer.create": "stock.group_stock_user",
    "stock.transfer.confirm": "stock.group_stock_user",
    "stock.transfer.assign": "stock.group_stock_user",
    "stock.transfer.quantities.set": "stock.group_stock_user",
    "stock.transfer.validate": "stock.group_stock_user",
    "stock.transfer.unreserve": "stock.group_stock_user",
    "stock.transfer.cancel": "stock.group_stock_user",
    "purchase.order.create": "purchase.group_purchase_user",
    "purchase.order.update_draft": "purchase.group_purchase_user",
    "purchase.order.lines.replace": "purchase.group_purchase_user",
    "purchase.order.confirm": "purchase.group_purchase_user",
    "purchase.order.cancel": "purchase.group_purchase_user",
    "purchase.order.reset_to_draft": "purchase.group_purchase_user",
    "purchase.order.bill.create": "account.group_account_invoice",
    "purchase_bill.match": "account.group_account_invoice",
    "purchase_bill.lines.unmatch": "account.group_account_invoice",
    "payment_term.create": "account.group_account_manager",
    "payment_term.update": "account.group_account_manager",
    "payment_term.lines.replace": "account.group_account_manager",
    "payment_term.archive": "account.group_account_manager",
    "payment_term.restore": "account.group_account_manager",
    "period.accrual.generate": "account.group_account_manager",
    "fiscal_position.create": "account.group_account_manager",
    "fiscal_position.update": "account.group_account_manager",
    "fiscal_position.account_mappings.replace": "account.group_account_manager",
    "fiscal_position.archive": "account.group_account_manager",
    "fiscal_position.restore": "account.group_account_manager",
    "journal.group.create": "account.group_account_manager",
    "journal.group.update": "account.group_account_manager",
}

_MODELS = {
    "customer_invoice.create": {
        "res.company",
        "res.partner",
        "res.currency",
        "account.journal",
        "account.account",
        "account.tax",
        "account.move",
        "account.move.line",
    },
    "vendor_bill.create": {
        "res.company",
        "res.partner",
        "res.currency",
        "account.journal",
        "account.account",
        "account.tax",
        "account.move",
        "account.move.line",
    },
    "invoice.update": {
        "res.company",
        "res.partner",
        "res.currency",
        "account.journal",
        "account.payment.term",
        "account.move",
    },
    "invoice.lines.replace": {
        "res.company",
        "res.partner",
        "product.product",
        "account.account",
        "account.tax",
        "account.move",
        "account.move.line",
    },
    "invoice.line.create": {
        "res.company",
        "res.partner",
        "product.product",
        "account.account",
        "account.tax",
        "account.move",
        "account.move.line",
        "account.analytic.account",
    },
    "invoice.line.update": {
        "res.company",
        "res.partner",
        "product.product",
        "account.account",
        "account.tax",
        "account.move",
        "account.move.line",
        "account.analytic.account",
    },
    "invoice.line.delete": {
        "res.company",
        "account.move",
        "account.move.line",
    },
    "invoice.delete": {
        "res.company",
        "account.move",
        "account.move.line",
    },
    "invoice.cancel": {"res.company", "account.move"},
    "invoice.reset_to_draft": {"res.company", "account.move"},
    "invoice.post": {"res.company", "account.move"},
    "invoice.duplicate": {"res.company", "account.move", "account.move.line"},
    "invoice.type.switch": {
        "res.company",
        "account.tax",
        "account.move",
        "account.move.line",
    },
    "journal_entry.create": {
        "res.company",
        "res.partner",
        "account.journal",
        "account.account",
        "account.move",
        "account.move.line",
    },
    "journal_entry.update": {
        "res.company",
        "account.journal",
        "account.move",
    },
    "journal_entry.lines.replace": {
        "res.company",
        "res.partner",
        "account.account",
        "account.move",
        "account.move.line",
    },
    "journal_entry.duplicate": {
        "res.company",
        "account.journal",
        "account.move",
        "account.move.line",
    },
    "journal_entry.delete": {
        "res.company",
        "account.journal",
        "account.move",
        "account.move.line",
    },
    "journal_entry.cancel": {"res.company", "account.move"},
    "journal_entry.reset_to_draft": {"res.company", "account.move"},
    "journal_entry.post": {"res.company", "account.move"},
    "journal_entry.reverse": {
        "res.company",
        "res.partner.bank",
        "account.journal",
        "account.move",
        "account.move.reversal",
    },
    "receivable.payment.register": {
        "res.company",
        "account.account",
        "account.journal",
        "account.move",
        "account.move.line",
        "account.payment",
        "account.payment.register",
    },
    "payable.payment.register": {
        "res.company",
        "account.account",
        "account.journal",
        "account.move",
        "account.move.line",
        "account.payment",
        "account.payment.register",
    },
    "reconciliation.apply": {
        "res.company",
        "account.account",
        "account.move.line",
        "account.partial.reconcile",
        "account.full.reconcile",
    },
    "payment.cancel": {"res.company", "account.move", "account.payment"},
    "customer_credit_note.create": {
        "res.company",
        "res.partner.bank",
        "account.journal",
        "account.move",
        "account.move.reversal",
    },
    "vendor_refund.create": {
        "res.company",
        "res.partner.bank",
        "account.journal",
        "account.move",
        "account.move.reversal",
    },
    "payment.post": {"res.company", "account.move", "account.payment"},
    "reconciliation.undo": {
        "res.company",
        "account.move.line",
        "account.partial.reconcile",
        "account.full.reconcile",
    },
    "bank.transaction.record": {
        "res.company",
        "res.partner",
        "res.currency",
        "account.journal",
        "account.move",
        "account.move.line",
        "account.bank.statement.line",
    },
    "asset.create": {
        "res.company",
        "account.account",
        "account.journal",
        "account.asset",
    },
    "asset.validate": {
        "res.company",
        "account.asset",
        "account.move",
        "account.move.line",
    },
    "asset.cancel": {
        "res.company",
        "account.asset",
        "account.move",
        "account.move.line",
    },
    "asset.dispose": {
        "res.company",
        "account.asset",
        "asset.modify",
        "account.move",
        "account.move.line",
    },
    "asset.pause": {
        "res.company",
        "account.asset",
        "asset.modify",
        "account.move",
        "account.move.line",
    },
    "deferred_expense.generate_entries": {
        "res.company",
        "account.report",
        "account.deferred.expense.report.handler",
        "account.journal",
        "account.account",
        "account.move",
        "account.move.line",
    },
    "deferred_revenue.generate_entries": {
        "res.company",
        "account.report",
        "account.deferred.revenue.report.handler",
        "account.journal",
        "account.account",
        "account.move",
        "account.move.line",
    },
    "multicurrency.revaluation.generate_entries": {
        "res.company",
        "account.report",
        "account.multicurrency.revaluation.wizard",
        "account.journal",
        "account.account",
        "account.move",
        "account.move.line",
        "res.currency",
    },
    "reconciliation.automatic.run": {
        "res.company",
        "account.auto.reconcile.wizard",
        "account.account",
        "account.move.line",
        "account.partial.reconcile",
        "account.full.reconcile",
    },
    "period.transfer.run": {
        "res.company",
        "account.transfer.model",
        "account.transfer.model.line",
        "account.move",
        "account.move.line",
    },
    "localization.china.period_transfer.run": {
        "res.company",
        "res.country",
        "account.transfer.model",
        "account.transfer.model.line",
        "account.move",
        "account.move.line",
    },
    "payment.create": {
        "res.company",
        "res.partner",
        "res.currency",
        "account.journal",
        "account.account",
        "account.payment.method",
        "account.payment.method.line",
        "account.payment",
        "account.move",
        "account.move.line",
    },
    "payment.update_draft": {
        "res.company",
        "res.partner",
        "res.currency",
        "account.journal",
        "account.account",
        "account.payment.method",
        "account.payment.method.line",
        "account.payment",
        "account.move",
        "account.move.line",
    },
    "payment.reset_to_draft": {
        "res.company",
        "account.payment",
        "account.move",
    },
    "payment.duplicate": {
        "res.company",
        "account.payment",
        "account.move",
        "account.move.line",
    },
    "payment.delete": {
        "res.company",
        "account.payment",
        "account.move",
        "account.move.line",
        "account.partial.reconcile",
        "account.full.reconcile",
    },
    "bank.statement.create": {
        "res.company",
        "res.currency",
        "account.journal",
        "account.bank.statement",
        "account.bank.statement.line",
        "account.move",
    },
    "bank.statement.update": {
        "res.company",
        "res.currency",
        "account.bank.statement",
        "account.bank.statement.line",
    },
    "bank.statement.delete": {
        "res.company",
        "account.bank.statement",
        "account.bank.statement.line",
    },
    "bank.transaction.delete": {
        "res.company",
        "account.bank.statement.line",
        "account.move",
        "account.move.line",
        "account.payment",
        "account.partial.reconcile",
        "account.full.reconcile",
    },
    "bank.transaction.update": {
        "res.company",
        "res.partner",
        "account.bank.statement.line",
        "account.move",
        "account.move.line",
    },
    "bank.transaction.match": {
        "res.company",
        "account.account",
        "account.bank.statement.line",
        "account.move",
        "account.move.line",
        "account.partial.reconcile",
        "account.full.reconcile",
    },
    "bank.transaction.unmatch": {
        "res.company",
        "account.bank.statement.line",
        "account.move",
        "account.move.line",
        "account.payment",
        "account.partial.reconcile",
        "account.full.reconcile",
    },
    "reconciliation.write_off": {
        "res.company",
        "account.account",
        "account.bank.statement.line",
        "account.move",
        "account.move.line",
        "account.partial.reconcile",
        "account.full.reconcile",
    },
    "analytic.plan.create": {"res.company", "account.analytic.plan"},
    "analytic.plan.update": {"res.company", "account.analytic.plan"},
    "analytic.account.create": {
        "res.company",
        "res.partner",
        "account.analytic.plan",
        "account.analytic.account",
    },
    "analytic.account.update": {
        "res.company",
        "res.partner",
        "account.analytic.plan",
        "account.analytic.account",
    },
    "analytic.account.archive": {
        "res.company",
        "account.analytic.plan",
        "account.analytic.account",
    },
    "analytic.account.restore": {
        "res.company",
        "account.analytic.plan",
        "account.analytic.account",
    },
    "analytic.line.create": {
        "res.company",
        "account.analytic.plan",
        "account.analytic.account",
        "account.analytic.line",
    },
    "analytic.line.update": {
        "res.company",
        "account.analytic.plan",
        "account.analytic.account",
        "account.analytic.line",
    },
    "analytic.line.delete": {
        "res.company",
        "account.analytic.account",
        "account.analytic.line",
    },
    "account.return.create": {
        "res.company",
        "account.return.type",
        "account.return",
        "account.return.check",
        "account.return.creation.wizard",
    },
    "account.return.checks.refresh": {
        "res.company",
        "account.return.type",
        "account.return",
        "account.return.check",
    },
    "account.return.check.result.update": {
        "res.company",
        "account.return.type",
        "account.return",
        "account.return.check",
    },
    "account.return.validate": {
        "res.company",
        "account.return.type",
        "account.return",
        "account.return.check",
    },
    "account.return.mark_submitted": {
        "res.company",
        "account.return.type",
        "account.return",
        "account.return.check",
    },
    "account.return.archive": {
        "res.company",
        "account.return.type",
        "account.return",
    },
    "account.return.restore": {
        "res.company",
        "account.return.type",
        "account.return",
    },
    "account.return.delete": {
        "res.company",
        "account.return.type",
        "account.return",
    },
    "product.create": {
        "res.company",
        "product.category",
        "uom.uom",
        "product.template",
        "product.product",
    },
    "product.update": {
        "res.company",
        "product.category",
        "uom.uom",
        "product.template",
        "product.product",
    },
    "product.duplicate": {
        "res.company",
        "product.category",
        "uom.uom",
        "product.template",
        "product.product",
    },
    "product.archive": {
        "res.company",
        "product.template",
        "product.product",
        "stock.warehouse.orderpoint",
    },
    "product.restore": {
        "res.company",
        "product.template",
        "product.product",
        "stock.warehouse.orderpoint",
    },
    "product.cost.update": {
        "res.company",
        "product.template",
        "product.product",
    },
    "product.accounting_profile.update": {
        "res.company",
        "account.account",
        "account.tax",
        "product.template",
        "product.product",
    },
    "product.category.accounting_profile.update": {
        "res.company",
        "account.account",
        "product.category",
    },
    "budget.create": {"res.company", "budget.analytic", "budget.line"},
    "budget.update_draft": {"res.company", "budget.analytic", "budget.line"},
    "budget.lines.replace": {
        "res.company",
        "budget.analytic",
        "budget.line",
        "account.analytic.plan",
        "account.analytic.account",
    },
    "budget.confirm": {"res.company", "budget.analytic", "budget.line"},
    "budget.reset_to_draft": {"res.company", "budget.analytic", "budget.line"},
    "budget.cancel": {"res.company", "budget.analytic", "budget.line"},
    "budget.mark_done": {"res.company", "budget.analytic", "budget.line"},
    "partner.create": {
        "res.company",
        "res.partner",
        "res.country.state",
        "res.country",
    },
    "partner.update": {
        "res.company",
        "res.partner",
        "res.country.state",
        "res.country",
    },
    "partner.archive": {"res.company", "res.partner"},
    "partner.restore": {"res.company", "res.partner"},
    "partner.accounting.update": {
        "res.company",
        "res.partner",
        "account.account",
        "account.fiscal.position",
        "account.payment.term",
    },
    "partner.bank_account.create": {
        "res.company",
        "res.partner",
        "res.partner.bank",
        "res.bank",
        "res.currency",
    },
    "partner.bank_account.update": {
        "res.company",
        "res.partner",
        "res.partner.bank",
        "res.bank",
        "res.currency",
    },
    "partner.bank_account.archive": {
        "res.company",
        "res.partner",
        "res.partner.bank",
    },
    "partner.bank_account.restore": {
        "res.company",
        "res.partner",
        "res.partner.bank",
    },
    "account.account.create": {"res.company", "res.currency", "account.account"},
    "account.account.update": {"res.company", "res.currency", "account.account"},
    "account.account.archive": {"res.company", "account.account"},
    "account.account.restore": {"res.company", "account.account"},
    "journal.create": {
        "res.company",
        "res.currency",
        "account.account",
        "account.journal",
    },
    "journal.update": {
        "res.company",
        "res.currency",
        "account.account",
        "account.journal",
    },
    "journal.archive": {"res.company", "account.journal"},
    "journal.restore": {"res.company", "account.journal"},
    "tax.create": {"res.company", "account.tax", "account.tax.group"},
    "tax.update": {"res.company", "account.tax", "account.tax.group"},
    "tax.archive": {"res.company", "account.tax"},
    "tax.restore": {"res.company", "account.tax"},
}

_ACCESS = {
    "customer_invoice.create": {
        ("res.partner", "read"),
        ("res.currency", "read"),
        ("account.journal", "read"),
        ("account.account", "read"),
        ("account.tax", "read"),
        ("account.move", "read"),
        ("account.move", "create"),
        ("account.move.line", "read"),
        ("account.move.line", "create"),
    },
    "vendor_bill.create": {
        ("res.partner", "read"),
        ("res.currency", "read"),
        ("account.journal", "read"),
        ("account.account", "read"),
        ("account.tax", "read"),
        ("account.move", "read"),
        ("account.move", "create"),
        ("account.move.line", "read"),
        ("account.move.line", "create"),
    },
    "invoice.update": {
        ("res.partner", "read"),
        ("res.currency", "read"),
        ("account.journal", "read"),
        ("account.payment.term", "read"),
        ("account.move", "read"),
        ("account.move", "write"),
    },
    "invoice.lines.replace": {
        ("res.partner", "read"),
        ("product.product", "read"),
        ("account.account", "read"),
        ("account.tax", "read"),
        ("account.move", "read"),
        ("account.move", "write"),
        ("account.move.line", "read"),
        ("account.move.line", "create"),
        ("account.move.line", "write"),
        ("account.move.line", "unlink"),
    },
    "invoice.line.create": {
        ("res.partner", "read"),
        ("product.product", "read"),
        ("account.account", "read"),
        ("account.tax", "read"),
        ("account.analytic.account", "read"),
        ("account.move", "read"),
        ("account.move", "write"),
        ("account.move.line", "read"),
        ("account.move.line", "create"),
        ("account.move.line", "write"),
        ("account.move.line", "unlink"),
    },
    "invoice.line.update": {
        ("res.partner", "read"),
        ("product.product", "read"),
        ("account.account", "read"),
        ("account.tax", "read"),
        ("account.analytic.account", "read"),
        ("account.move", "read"),
        ("account.move", "write"),
        ("account.move.line", "read"),
        ("account.move.line", "create"),
        ("account.move.line", "write"),
        ("account.move.line", "unlink"),
    },
    "invoice.line.delete": {
        ("account.move", "read"),
        ("account.move", "write"),
        ("account.move.line", "read"),
        ("account.move.line", "create"),
        ("account.move.line", "write"),
        ("account.move.line", "unlink"),
    },
    "invoice.delete": {
        ("account.move", "read"),
        ("account.move", "unlink"),
        ("account.move.line", "read"),
        ("account.move.line", "unlink"),
    },
    "invoice.cancel": {
        ("account.move", "read"),
        ("account.move", "write"),
    },
    "invoice.reset_to_draft": {
        ("account.move", "read"),
        ("account.move", "write"),
    },
    "invoice.post": {("account.move", "read"), ("account.move", "write")},
    "invoice.duplicate": {
        ("account.move", "read"),
        ("account.move", "create"),
        ("account.move", "write"),
        ("account.move.line", "read"),
        ("account.move.line", "create"),
    },
    "invoice.type.switch": {
        ("account.tax", "read"),
        ("account.move", "read"),
        ("account.move", "write"),
        ("account.move.line", "read"),
        ("account.move.line", "write"),
    },
    "journal_entry.create": {
        ("res.partner", "read"),
        ("account.journal", "read"),
        ("account.account", "read"),
        ("account.move", "read"),
        ("account.move", "create"),
        ("account.move.line", "read"),
        ("account.move.line", "create"),
    },
    "journal_entry.update": {
        ("account.journal", "read"),
        ("account.move", "read"),
        ("account.move", "write"),
    },
    "journal_entry.lines.replace": {
        ("res.partner", "read"),
        ("account.account", "read"),
        ("account.move", "read"),
        ("account.move", "write"),
        ("account.move.line", "read"),
        ("account.move.line", "create"),
        ("account.move.line", "write"),
        ("account.move.line", "unlink"),
    },
    "journal_entry.duplicate": {
        ("account.journal", "read"),
        ("account.move", "read"),
        ("account.move", "create"),
        ("account.move", "write"),
        ("account.move.line", "read"),
        ("account.move.line", "create"),
    },
    "journal_entry.delete": {
        ("account.journal", "read"),
        ("account.move", "read"),
        ("account.move", "unlink"),
        ("account.move.line", "read"),
        ("account.move.line", "unlink"),
    },
    "journal_entry.cancel": {
        ("account.move", "read"),
        ("account.move", "write"),
    },
    "journal_entry.reset_to_draft": {
        ("account.move", "read"),
        ("account.move", "write"),
    },
    "journal_entry.post": {
        ("account.move", "read"),
        ("account.move", "write"),
    },
    "journal_entry.reverse": {
        ("res.partner.bank", "read"),
        ("account.journal", "read"),
        ("account.move", "read"),
        ("account.move", "write"),
        ("account.move", "create"),
        ("account.move.reversal", "create"),
    },
    "receivable.payment.register": {
        ("account.account", "read"),
        ("account.journal", "read"),
        ("account.move", "read"),
        ("account.move.line", "read"),
        ("account.payment", "read"),
        ("account.payment", "create"),
        ("account.payment.register", "create"),
    },
    "payable.payment.register": {
        ("account.account", "read"),
        ("account.journal", "read"),
        ("account.move", "read"),
        ("account.move.line", "read"),
        ("account.payment", "read"),
        ("account.payment", "create"),
        ("account.payment.register", "create"),
    },
    "reconciliation.apply": {
        ("account.account", "read"),
        ("account.move.line", "read"),
        ("account.move.line", "write"),
        ("account.partial.reconcile", "read"),
        ("account.partial.reconcile", "create"),
        ("account.full.reconcile", "read"),
    },
    "payment.cancel": {
        ("account.payment", "read"),
        ("account.payment", "write"),
        ("account.move", "read"),
    },
    "customer_credit_note.create": {
        ("res.partner.bank", "read"),
        ("account.journal", "read"),
        ("account.move", "read"),
        ("account.move", "write"),
        ("account.move", "create"),
        ("account.move.reversal", "create"),
    },
    "vendor_refund.create": {
        ("res.partner.bank", "read"),
        ("account.journal", "read"),
        ("account.move", "read"),
        ("account.move", "write"),
        ("account.move", "create"),
        ("account.move.reversal", "create"),
    },
    "payment.post": {
        ("account.payment", "read"),
        ("account.payment", "write"),
        ("account.move", "read"),
        ("account.move", "write"),
    },
    "reconciliation.undo": {
        ("account.move.line", "read"),
        ("account.move.line", "write"),
        ("account.partial.reconcile", "read"),
        ("account.partial.reconcile", "unlink"),
        ("account.full.reconcile", "read"),
        ("account.full.reconcile", "unlink"),
    },
    "bank.transaction.record": {
        ("res.partner", "read"),
        ("res.currency", "read"),
        ("account.journal", "read"),
        ("account.bank.statement.line", "read"),
        ("account.bank.statement.line", "create"),
        ("account.move", "read"),
        ("account.move", "write"),
        ("account.move", "create"),
        ("account.move.line", "read"),
        ("account.move.line", "write"),
        ("account.move.line", "create"),
    },
    "asset.create": {
        ("account.account", "read"),
        ("account.journal", "read"),
        ("account.asset", "read"),
        ("account.asset", "create"),
    },
    "asset.validate": {
        ("account.asset", "read"),
        ("account.asset", "write"),
        ("account.move", "read"),
        ("account.move", "create"),
        ("account.move", "write"),
        ("account.move.line", "read"),
        ("account.move.line", "create"),
        ("account.move.line", "write"),
    },
    "asset.cancel": {
        ("account.asset", "read"),
        ("account.asset", "write"),
        ("account.move", "read"),
        ("account.move", "write"),
        ("account.move", "create"),
        ("account.move", "unlink"),
        ("account.move.line", "read"),
        ("account.move.line", "write"),
        ("account.move.line", "create"),
        ("account.move.line", "unlink"),
    },
    "asset.dispose": {
        ("account.asset", "read"),
        ("account.asset", "write"),
        ("asset.modify", "create"),
        ("account.move", "read"),
        ("account.move", "write"),
        ("account.move", "create"),
        ("account.move", "unlink"),
        ("account.move.line", "read"),
        ("account.move.line", "write"),
        ("account.move.line", "create"),
        ("account.move.line", "unlink"),
    },
    "asset.pause": {
        ("account.asset", "read"),
        ("account.asset", "write"),
        ("asset.modify", "create"),
        ("account.move", "read"),
        ("account.move", "write"),
        ("account.move", "create"),
        ("account.move", "unlink"),
        ("account.move.line", "read"),
        ("account.move.line", "write"),
        ("account.move.line", "create"),
        ("account.move.line", "unlink"),
    },
    "deferred_expense.generate_entries": {
        ("account.report", "read"),
        ("account.journal", "read"),
        ("account.account", "read"),
        ("account.move", "read"),
        ("account.move", "create"),
        ("account.move", "write"),
        ("account.move.line", "read"),
        ("account.move.line", "create"),
        ("account.move.line", "write"),
    },
    "deferred_revenue.generate_entries": {
        ("account.report", "read"),
        ("account.journal", "read"),
        ("account.account", "read"),
        ("account.move", "read"),
        ("account.move", "create"),
        ("account.move", "write"),
        ("account.move.line", "read"),
        ("account.move.line", "create"),
        ("account.move.line", "write"),
    },
    "multicurrency.revaluation.generate_entries": {
        ("account.report", "read"),
        ("account.journal", "read"),
        ("account.account", "read"),
        ("res.currency", "read"),
        ("account.move", "read"),
        ("account.move", "create"),
        ("account.move", "write"),
        ("account.move.line", "read"),
        ("account.move.line", "create"),
        ("account.move.line", "write"),
    },
    "reconciliation.automatic.run": {
        ("account.auto.reconcile.wizard", "create"),
        ("account.account", "read"),
        ("account.move.line", "read"),
        ("account.move.line", "write"),
        ("account.partial.reconcile", "read"),
        ("account.partial.reconcile", "create"),
        ("account.full.reconcile", "read"),
    },
    "period.transfer.run": {
        ("account.transfer.model", "read"),
        ("account.transfer.model.line", "read"),
        ("account.move", "read"),
        ("account.move", "create"),
        ("account.move", "write"),
        ("account.move.line", "read"),
        ("account.move.line", "create"),
        ("account.move.line", "write"),
        ("account.move.line", "unlink"),
    },
    "localization.china.period_transfer.run": {
        ("res.country", "read"),
        ("account.transfer.model", "read"),
        ("account.transfer.model.line", "read"),
        ("account.move", "read"),
        ("account.move", "create"),
        ("account.move", "write"),
        ("account.move.line", "read"),
        ("account.move.line", "create"),
        ("account.move.line", "write"),
        ("account.move.line", "unlink"),
    },
    "payment.create": {
        ("res.partner", "read"),
        ("res.currency", "read"),
        ("account.journal", "read"),
        ("account.account", "read"),
        ("account.payment.method", "read"),
        ("account.payment.method.line", "read"),
        ("account.payment", "read"),
        ("account.payment", "create"),
        ("account.move", "read"),
        ("account.move", "create"),
        ("account.move.line", "read"),
        ("account.move.line", "create"),
    },
    "payment.update_draft": {
        ("res.partner", "read"),
        ("res.currency", "read"),
        ("account.journal", "read"),
        ("account.account", "read"),
        ("account.payment.method", "read"),
        ("account.payment.method.line", "read"),
        ("account.payment", "read"),
        ("account.payment", "write"),
        ("account.move", "read"),
        ("account.move", "write"),
        ("account.move.line", "read"),
        ("account.move.line", "write"),
    },
    "payment.reset_to_draft": {
        ("account.payment", "read"),
        ("account.payment", "write"),
        ("account.move", "read"),
        ("account.move", "write"),
    },
    "payment.duplicate": {
        ("account.payment", "read"),
        ("account.payment", "create"),
        ("account.payment", "write"),
        ("account.move", "read"),
        ("account.move", "create"),
        ("account.move.line", "read"),
        ("account.move.line", "create"),
    },
    "payment.delete": {
        ("account.payment", "read"),
        ("account.payment", "unlink"),
        ("account.move", "read"),
        ("account.move", "unlink"),
        ("account.move", "write"),
        ("account.move.line", "read"),
        ("account.partial.reconcile", "read"),
        ("account.full.reconcile", "read"),
    },
    "bank.statement.create": {
        ("res.currency", "read"),
        ("account.journal", "read"),
        ("account.bank.statement", "read"),
        ("account.bank.statement", "create"),
        ("account.bank.statement.line", "read"),
        ("account.bank.statement.line", "write"),
        ("account.move", "read"),
    },
    "bank.statement.update": {
        ("res.currency", "read"),
        ("account.bank.statement", "read"),
        ("account.bank.statement", "write"),
        ("account.bank.statement.line", "read"),
    },
    "bank.statement.delete": {
        ("account.bank.statement", "read"),
        ("account.bank.statement", "unlink"),
        ("account.bank.statement.line", "read"),
        ("account.bank.statement.line", "write"),
    },
    "bank.transaction.delete": {
        ("account.bank.statement.line", "read"),
        ("account.bank.statement.line", "unlink"),
        ("account.move", "read"),
        ("account.move", "unlink"),
        ("account.move.line", "read"),
        ("account.payment", "read"),
        ("account.partial.reconcile", "read"),
        ("account.full.reconcile", "read"),
    },
    "bank.transaction.update": {
        ("res.partner", "read"),
        ("account.bank.statement.line", "read"),
        ("account.bank.statement.line", "write"),
        ("account.move", "read"),
        ("account.move", "write"),
        ("account.move.line", "read"),
        ("account.move.line", "write"),
    },
    "bank.transaction.match": {
        ("account.account", "read"),
        ("account.bank.statement.line", "read"),
        ("account.bank.statement.line", "write"),
        ("account.move", "read"),
        ("account.move.line", "read"),
        ("account.move.line", "write"),
        ("account.partial.reconcile", "read"),
        ("account.partial.reconcile", "create"),
        ("account.full.reconcile", "read"),
    },
    "bank.transaction.unmatch": {
        ("account.bank.statement.line", "read"),
        ("account.bank.statement.line", "write"),
        ("account.move", "read"),
        ("account.move", "write"),
        ("account.move.line", "read"),
        ("account.move.line", "create"),
        ("account.move.line", "write"),
        ("account.move.line", "unlink"),
        ("account.payment", "read"),
        ("account.payment", "unlink"),
        ("account.partial.reconcile", "read"),
        ("account.partial.reconcile", "unlink"),
        ("account.full.reconcile", "read"),
        ("account.full.reconcile", "unlink"),
    },
    "reconciliation.write_off": {
        ("account.account", "read"),
        ("account.bank.statement.line", "read"),
        ("account.bank.statement.line", "write"),
        ("account.move", "read"),
        ("account.move", "write"),
        ("account.move.line", "read"),
        ("account.move.line", "create"),
        ("account.move.line", "write"),
        ("account.move.line", "unlink"),
        ("account.partial.reconcile", "read"),
        ("account.partial.reconcile", "create"),
        ("account.full.reconcile", "read"),
    },
    "analytic.plan.create": {
        ("account.analytic.plan", "read"),
        ("account.analytic.plan", "create"),
    },
    "analytic.plan.update": {
        ("account.analytic.plan", "read"),
        ("account.analytic.plan", "write"),
    },
    "analytic.account.create": {
        ("res.partner", "read"),
        ("account.analytic.plan", "read"),
        ("account.analytic.account", "read"),
        ("account.analytic.account", "create"),
    },
    "analytic.account.update": {
        ("res.partner", "read"),
        ("account.analytic.plan", "read"),
        ("account.analytic.account", "read"),
        ("account.analytic.account", "write"),
    },
    "analytic.account.archive": {
        ("account.analytic.plan", "read"),
        ("account.analytic.account", "read"),
        ("account.analytic.account", "write"),
    },
    "analytic.account.restore": {
        ("account.analytic.plan", "read"),
        ("account.analytic.account", "read"),
        ("account.analytic.account", "write"),
    },
    "analytic.line.create": {
        ("account.analytic.plan", "read"),
        ("account.analytic.account", "read"),
        ("account.analytic.line", "read"),
        ("account.analytic.line", "create"),
    },
    "analytic.line.update": {
        ("account.analytic.plan", "read"),
        ("account.analytic.account", "read"),
        ("account.analytic.line", "read"),
        ("account.analytic.line", "write"),
    },
    "analytic.line.delete": {
        ("account.analytic.account", "read"),
        ("account.analytic.line", "read"),
        ("account.analytic.line", "unlink"),
    },
    "account.return.create": {
        ("account.return.type", "read"),
        ("account.return", "read"),
        ("account.return", "create"),
        ("account.return.check", "read"),
        ("account.return.check", "create"),
        ("account.return.check", "write"),
        ("account.return.creation.wizard", "create"),
    },
    "account.return.checks.refresh": {
        ("account.return.type", "read"),
        ("account.return", "read"),
        ("account.return.check", "read"),
        ("account.return.check", "create"),
        ("account.return.check", "write"),
    },
    "account.return.check.result.update": {
        ("account.return.type", "read"),
        ("account.return", "read"),
        ("account.return.check", "read"),
        ("account.return.check", "write"),
    },
    "account.return.validate": {
        ("account.return.type", "read"),
        ("account.return", "read"),
        ("account.return", "write"),
        ("account.return.check", "read"),
        ("account.return.check", "create"),
        ("account.return.check", "write"),
    },
    "account.return.mark_submitted": {
        ("account.return.type", "read"),
        ("account.return", "read"),
        ("account.return", "write"),
        ("account.return.check", "read"),
    },
    "account.return.archive": {
        ("account.return.type", "read"),
        ("account.return", "read"),
        ("account.return", "write"),
    },
    "account.return.restore": {
        ("account.return.type", "read"),
        ("account.return", "read"),
        ("account.return", "write"),
    },
    "account.return.delete": {
        ("account.return.type", "read"),
        ("account.return", "read"),
        ("account.return", "unlink"),
    },
    "product.create": {
        ("product.category", "read"),
        ("uom.uom", "read"),
        ("product.template", "read"),
        ("product.template", "create"),
        ("product.product", "read"),
        ("product.product", "create"),
    },
    "product.update": {
        ("product.category", "read"),
        ("uom.uom", "read"),
        ("product.template", "read"),
        ("product.template", "write"),
        ("product.product", "read"),
        ("product.product", "write"),
    },
    "product.duplicate": {
        ("product.category", "read"),
        ("uom.uom", "read"),
        ("product.template", "read"),
        ("product.template", "create"),
        ("product.product", "read"),
        ("product.product", "create"),
    },
    "product.archive": {
        ("product.template", "read"),
        ("product.template", "write"),
        ("product.product", "read"),
        ("product.product", "write"),
        ("stock.warehouse.orderpoint", "read"),
        ("stock.warehouse.orderpoint", "write"),
    },
    "product.restore": {
        ("product.template", "read"),
        ("product.template", "write"),
        ("product.product", "read"),
        ("product.product", "write"),
        ("stock.warehouse.orderpoint", "read"),
        ("stock.warehouse.orderpoint", "write"),
    },
    "product.cost.update": {
        ("product.template", "read"),
        ("product.product", "read"),
        ("product.product", "write"),
    },
    "product.accounting_profile.update": {
        ("account.account", "read"),
        ("account.tax", "read"),
        ("product.template", "read"),
        ("product.template", "write"),
        ("product.product", "read"),
    },
    "product.category.accounting_profile.update": {
        ("account.account", "read"),
        ("product.category", "read"),
        ("product.category", "write"),
    },
    "budget.create": {
        ("budget.analytic", "read"),
        ("budget.analytic", "create"),
        ("budget.line", "read"),
    },
    "budget.update_draft": {
        ("budget.analytic", "read"),
        ("budget.analytic", "write"),
        ("budget.line", "read"),
    },
    "budget.lines.replace": {
        ("budget.analytic", "read"),
        ("budget.line", "read"),
        ("budget.line", "create"),
        ("budget.line", "unlink"),
        ("account.analytic.plan", "read"),
        ("account.analytic.account", "read"),
    },
    "budget.confirm": {
        ("budget.analytic", "read"),
        ("budget.analytic", "write"),
        ("budget.line", "read"),
    },
    "budget.reset_to_draft": {
        ("budget.analytic", "read"),
        ("budget.analytic", "write"),
        ("budget.line", "read"),
    },
    "budget.cancel": {
        ("budget.analytic", "read"),
        ("budget.analytic", "write"),
        ("budget.line", "read"),
    },
    "budget.mark_done": {
        ("budget.analytic", "read"),
        ("budget.analytic", "write"),
        ("budget.line", "read"),
    },
    "partner.create": {
        ("res.partner", "read"),
        ("res.partner", "create"),
        ("res.country.state", "read"),
        ("res.country", "read"),
    },
    "partner.update": {
        ("res.partner", "read"),
        ("res.partner", "write"),
        ("res.country.state", "read"),
        ("res.country", "read"),
    },
    "partner.archive": {("res.partner", "read"), ("res.partner", "write")},
    "partner.restore": {("res.partner", "read"), ("res.partner", "write")},
    "partner.accounting.update": {
        ("res.partner", "read"),
        ("res.partner", "write"),
        ("account.account", "read"),
        ("account.fiscal.position", "read"),
        ("account.payment.term", "read"),
    },
    "partner.bank_account.create": {
        ("res.partner", "read"),
        ("res.partner.bank", "read"),
        ("res.partner.bank", "create"),
        ("res.bank", "read"),
        ("res.currency", "read"),
    },
    "partner.bank_account.update": {
        ("res.partner", "read"),
        ("res.partner.bank", "read"),
        ("res.partner.bank", "write"),
        ("res.bank", "read"),
        ("res.currency", "read"),
    },
    "partner.bank_account.archive": {
        ("res.partner", "read"),
        ("res.partner.bank", "read"),
        ("res.partner.bank", "write"),
    },
    "partner.bank_account.restore": {
        ("res.partner", "read"),
        ("res.partner.bank", "read"),
        ("res.partner.bank", "write"),
    },
    "account.account.create": {
        ("res.company", "read"),
        ("res.currency", "read"),
        ("account.account", "read"),
        ("account.account", "create"),
    },
    "account.account.update": {
        ("res.company", "read"),
        ("res.currency", "read"),
        ("account.account", "read"),
        ("account.account", "write"),
    },
    "account.account.archive": {
        ("res.company", "read"),
        ("account.account", "read"),
        ("account.account", "write"),
    },
    "account.account.restore": {
        ("res.company", "read"),
        ("account.account", "read"),
        ("account.account", "write"),
    },
    "journal.create": {
        ("res.company", "read"),
        ("res.currency", "read"),
        ("account.account", "read"),
        ("account.account", "create"),
        ("account.journal", "read"),
        ("account.journal", "create"),
    },
    "journal.update": {
        ("res.company", "read"),
        ("res.currency", "read"),
        ("account.account", "read"),
        ("account.journal", "read"),
        ("account.journal", "write"),
    },
    "journal.archive": {
        ("res.company", "read"),
        ("account.journal", "read"),
        ("account.journal", "write"),
    },
    "journal.restore": {
        ("res.company", "read"),
        ("account.journal", "read"),
        ("account.journal", "write"),
    },
    "tax.create": {
        ("res.company", "read"),
        ("account.tax.group", "read"),
        ("account.tax", "read"),
        ("account.tax", "create"),
    },
    "tax.update": {
        ("res.company", "read"),
        ("account.tax.group", "read"),
        ("account.tax", "read"),
        ("account.tax", "write"),
    },
    "tax.archive": {
        ("res.company", "read"),
        ("account.tax", "read"),
        ("account.tax", "write"),
    },
    "tax.restore": {
        ("res.company", "read"),
        ("account.tax", "read"),
        ("account.tax", "write"),
    },
}

for _capability_id in _ORDER_WRITE_CAPABILITIES:
    _sale_order = _capability_id.startswith("sale.order.")
    _order_model = "sale.order" if _sale_order else "purchase.order"
    _line_model = f"{_order_model}.line"
    _MODELS[_capability_id] = {"res.company", _order_model, _line_model}
    if (
        _capability_id
        in _ORDER_CREATE_CAPABILITIES | _ORDER_LINE_REPLACEMENT_CAPABILITIES
    ):
        _MODELS[_capability_id].update({"account.tax", "product.product", "uom.uom"})
    if _capability_id in _ORDER_CREATE_CAPABILITIES:
        _MODELS[_capability_id].update(
            {"account.payment.term", "res.partner"}
            | (
                {"product.pricelist"}
                if _sale_order
                else {"account.incoterms", "res.currency", "stock.picking.type"}
            )
        )
    elif _capability_id in _ORDER_UPDATE_CAPABILITIES:
        _MODELS[_capability_id].add("account.payment.term")
        if not _sale_order:
            _MODELS[_capability_id].add("account.incoterms")
    _ACCESS[_capability_id] = {
        ("res.company", "read"),
        (_order_model, "read"),
        (_order_model, "write"),
        (_line_model, "read"),
    }
    if _capability_id in _ORDER_CREATE_CAPABILITIES:
        _ACCESS[_capability_id].update(
            {(_order_model, "create"), (_line_model, "create"), (_line_model, "write")}
        )
    elif _capability_id in _ORDER_LINE_REPLACEMENT_CAPABILITIES:
        _ACCESS[_capability_id].update(
            {(_line_model, "create"), (_line_model, "write"), (_line_model, "unlink")}
        )

_MODELS[_SALE_ORDER_INVOICE_CAPABILITY] = {
    "res.company",
    "sale.order",
    "sale.order.line",
    "account.move",
    "account.move.line",
}
_ACCESS[_SALE_ORDER_INVOICE_CAPABILITY] = {
    ("res.company", "read"),
    ("sale.order", "read"),
    ("sale.order", "write"),
    ("sale.order.line", "read"),
    ("account.move", "read"),
    ("account.move", "create"),
    ("account.move.line", "read"),
}
_MODELS[_SALE_DOWN_PAYMENT_CAPABILITY] = _MODELS[_SALE_ORDER_INVOICE_CAPABILITY] | {
    "sale.advance.payment.inv", "account.tax",
}
_ACCESS[_SALE_DOWN_PAYMENT_CAPABILITY] = _ACCESS[_SALE_ORDER_INVOICE_CAPABILITY] | {
    ("sale.advance.payment.inv", "create"), ("sale.order.line", "create"),
    ("sale.order.line", "write"), ("account.tax", "read"), ("account.move", "write"),
}
for _payment_round_capability in ("receivable.payment.register", "payable.payment.register"):
    _PARAMETER_KEYS[_payment_round_capability].update(_PAYMENT_INSTALLMENT_FIELDS)

_STOCK_TRANSFER_MODELS = {
    "res.company",
    "stock.picking",
    "stock.move",
    "stock.move.line",
    "stock.quant",
}
_STOCK_TRANSFER_BASE_ACCESS = {
    ("res.company", "read"),
    ("stock.picking", "read"),
    ("stock.move", "read"),
    ("stock.move.line", "read"),
    ("stock.quant", "read"),
}
for _capability_id in _STOCK_TRANSFER_CAPABILITIES:
    _MODELS[_capability_id] = set(_STOCK_TRANSFER_MODELS)
    _ACCESS[_capability_id] = set(_STOCK_TRANSFER_BASE_ACCESS)

_MODELS[_STOCK_TRANSFER_CREATE_CAPABILITY].update(
    {
        "res.partner",
        "stock.picking.type",
        "stock.location",
        "product.product",
        "uom.uom",
    }
)
_ACCESS[_STOCK_TRANSFER_CREATE_CAPABILITY].update(
    {
        ("res.partner", "read"),
        ("stock.picking.type", "read"),
        ("stock.location", "read"),
        ("product.product", "read"),
        ("uom.uom", "read"),
        ("stock.picking", "create"),
        ("stock.picking", "write"),
        ("stock.move", "create"),
        ("stock.move", "write"),
    }
)
_ACCESS["stock.transfer.confirm"].update(
    {("stock.picking", "write"), ("stock.move", "write")}
)
_ACCESS["stock.transfer.assign"].update(
    {
        ("stock.picking", "write"),
        ("stock.move", "write"),
        ("stock.move.line", "create"),
        ("stock.move.line", "write"),
        ("stock.quant", "write"),
    }
)
_ACCESS[_STOCK_TRANSFER_QUANTITIES_CAPABILITY].update(
    {
        ("stock.move", "write"),
        ("stock.move.line", "create"),
        ("stock.move.line", "write"),
        ("stock.move.line", "unlink"),
        ("stock.quant", "write"),
    }
)
_MODELS[_STOCK_TRANSFER_VALIDATE_CAPABILITY].update(
    {"stock.picking.type", "account.move", "account.move.line"}
)
_ACCESS[_STOCK_TRANSFER_VALIDATE_CAPABILITY].update(
    {
        ("stock.picking.type", "read"),
        ("stock.picking", "create"),
        ("stock.picking", "write"),
        ("stock.move", "create"),
        ("stock.move", "write"),
        ("stock.move.line", "create"),
        ("stock.move.line", "write"),
        ("stock.move.line", "unlink"),
        ("stock.quant", "write"),
        ("account.move", "read"),
        ("account.move", "create"),
        ("account.move", "write"),
        ("account.move.line", "read"),
        ("account.move.line", "create"),
        ("account.move.line", "write"),
    }
)
for _capability_id in ("stock.transfer.unreserve", "stock.transfer.cancel"):
    _ACCESS[_capability_id].update(
        {
            ("stock.picking", "write"),
            ("stock.move", "write"),
            ("stock.move.line", "unlink"),
            ("stock.quant", "write"),
        }
    )

_MODELS["purchase.order.bill.create"] = {
    "res.company",
    "purchase.order",
    "purchase.order.line",
    "account.move",
    "account.move.line",
}
_ACCESS["purchase.order.bill.create"] = {
    ("res.company", "read"),
    ("purchase.order", "read"),
    ("purchase.order", "write"),
    ("purchase.order.line", "read"),
    ("account.move", "read"),
    ("account.move", "create"),
    ("account.move", "write"),
    ("account.move.line", "read"),
    ("account.move.line", "create"),
    ("account.move.line", "write"),
}
for _capability_id in ("purchase_bill.match", "purchase_bill.lines.unmatch"):
    _MODELS[_capability_id] = {
        "res.company",
        "res.partner",
        "product.product",
        "purchase.order",
        "purchase.order.line",
        "account.move",
        "account.move.line",
        "purchase.bill.line.match",
    }
    _ACCESS[_capability_id] = {
        ("res.company", "read"),
        ("res.partner", "read"),
        ("product.product", "read"),
        ("purchase.order", "read"),
        ("purchase.order.line", "read"),
        ("account.move", "read"),
        ("account.move", "write"),
        ("account.move.line", "read"),
        ("account.move.line", "write"),
        ("purchase.bill.line.match", "read"),
    }
_MODELS["purchase_bill.lines.unmatch"] = {
    "res.company",
    "purchase.order.line",
    "account.move",
    "account.move.line",
}
_ACCESS["purchase_bill.lines.unmatch"] = {
    ("res.company", "read"),
    ("purchase.order.line", "read"),
    ("account.move", "read"),
    ("account.move", "write"),
    ("account.move.line", "read"),
    ("account.move.line", "write"),
}

for _capability_id in _PAYMENT_TERM_CAPABILITIES:
    _MODELS[_capability_id] = {
        "res.company",
        "account.payment.term",
    }
    _ACCESS[_capability_id] = {
        ("res.company", "read"),
        ("account.payment.term", "read"),
        ("account.payment.term", "write"),
    }
    if _capability_id == "payment_term.create":
        _MODELS[_capability_id].add("account.payment.term.line")
        _ACCESS[_capability_id].update(
            {
                ("account.payment.term.line", "read"),
                ("account.payment.term", "create"),
                ("account.payment.term.line", "create"),
            }
        )
    elif _capability_id == "payment_term.lines.replace":
        _MODELS[_capability_id].add("account.payment.term.line")
        _ACCESS[_capability_id].update(
            {
                ("account.payment.term.line", "read"),
                ("account.payment.term.line", "create"),
                ("account.payment.term.line", "write"),
                ("account.payment.term.line", "unlink"),
            }
        )

_MODELS["period.accrual.generate"] = {
    "res.company",
    "sale.order",
    "purchase.order",
    "account.journal",
    "account.account",
    "account.move",
    "account.move.line",
    "account.accrued.orders.wizard",
}
_ACCESS["period.accrual.generate"] = {
    ("res.company", "read"),
    ("sale.order", "read"),
    ("purchase.order", "read"),
    ("account.journal", "read"),
    ("account.account", "read"),
    ("account.move", "read"),
    ("account.move", "create"),
    ("account.move", "write"),
    ("account.move.line", "read"),
    ("account.move.line", "create"),
    ("account.move.line", "write"),
    ("account.accrued.orders.wizard", "create"),
}
_ACCESS["payment_term.create"].add(("account.payment.term.line", "write"))
_ACCESS["payment_term.create"].discard(("account.payment.term", "write"))
_ACCESS["purchase_bill.match"].add(("purchase.bill.line.match", "write"))

_FISCAL_POSITION_HEADER_MODELS = {
    "res.company",
    "res.country",
    "res.country.group",
    "res.country.state",
    "account.fiscal.position",
}
_FISCAL_POSITION_HEADER_ACCESS = {
    ("res.company", "read"),
    ("res.country", "read"),
    ("res.country.group", "read"),
    ("res.country.state", "read"),
    ("account.fiscal.position", "read"),
}
_MODELS["fiscal_position.create"] = set(_FISCAL_POSITION_HEADER_MODELS)
_ACCESS["fiscal_position.create"] = _FISCAL_POSITION_HEADER_ACCESS | {
    ("account.fiscal.position", "create")
}
_MODELS["fiscal_position.update"] = set(_FISCAL_POSITION_HEADER_MODELS)
_ACCESS["fiscal_position.update"] = _FISCAL_POSITION_HEADER_ACCESS | {
    ("account.fiscal.position", "write")
}
_MODELS["fiscal_position.account_mappings.replace"] = {
    "res.company",
    "account.account",
    "account.fiscal.position",
    "account.fiscal.position.account",
}
_ACCESS["fiscal_position.account_mappings.replace"] = {
    ("res.company", "read"),
    ("account.account", "read"),
    ("account.fiscal.position", "read"),
    ("account.fiscal.position.account", "read"),
    ("account.fiscal.position.account", "create"),
    ("account.fiscal.position.account", "unlink"),
}
for _capability_id in ("fiscal_position.archive", "fiscal_position.restore"):
    _MODELS[_capability_id] = {"res.company", "account.fiscal.position"}
    _ACCESS[_capability_id] = {
        ("res.company", "read"),
        ("account.fiscal.position", "read"),
        ("account.fiscal.position", "write"),
    }

for _capability_id in _JOURNAL_GROUP_CAPABILITIES:
    _MODELS[_capability_id] = {
        "res.company",
        "account.journal",
        "account.journal.group",
    }
    _ACCESS[_capability_id] = {
        ("res.company", "read"),
        ("account.journal", "read"),
        ("account.journal.group", "read"),
    }
_ACCESS["journal.group.create"].add(("account.journal.group", "create"))
_ACCESS["journal.group.update"].add(("account.journal.group", "write"))

_TRANSFER_MODEL_BASE_MODELS = {
    "res.company",
    "account.journal",
    "account.account",
    "account.transfer.model",
    "account.transfer.model.line",
}
_TRANSFER_MODEL_BASE_ACCESS = {
    ("res.company", "read"),
    ("account.journal", "read"),
    ("account.account", "read"),
    ("account.transfer.model", "read"),
    ("account.transfer.model.line", "read"),
}
for _capability_id in _TRANSFER_MODEL_CAPABILITIES:
    _MODELS[_capability_id] = set(_TRANSFER_MODEL_BASE_MODELS)
    _ACCESS[_capability_id] = set(_TRANSFER_MODEL_BASE_ACCESS)
for _capability_id in (
    "account.transfer_model.create",
    "account.transfer_model.duplicate",
):
    _ACCESS[_capability_id].update(
        {
            ("account.transfer.model", "create"),
            ("account.transfer.model.line", "create"),
        }
    )
_ACCESS["account.transfer_model.duplicate"].add(
    ("account.transfer.model", "write")
)
_ACCESS["account.transfer_model.update"].update(
    {
        ("account.transfer.model", "write"),
        ("account.transfer.model.line", "create"),
        ("account.transfer.model.line", "write"),
        ("account.transfer.model.line", "unlink"),
    }
)
for _capability_id in (
    "account.transfer_model.enable",
    "account.transfer_model.disable",
    "account.transfer_model.archive",
    "account.transfer_model.restore",
):
    _ACCESS[_capability_id].add(("account.transfer.model", "write"))
_MODELS["account.transfer_model.delete"].add("account.move")
_ACCESS["account.transfer_model.delete"].update(
    {
        ("account.move", "read"),
        ("account.transfer.model", "unlink"),
    }
)

_MODELS["currency.rate.record"] = {
    "res.company",
    "res.currency",
    "res.currency.rate",
}
_ACCESS["currency.rate.record"] = {
    ("res.company", "read"),
    ("res.currency", "read"),
    ("res.currency.rate", "read"),
    ("res.currency.rate", "create"),
}
for _currency_rate_capability, _currency_rate_operation in (
    ("currency.rate.update", "write"), ("currency.rate.delete", "unlink"),
):
    _GROUPS[_currency_rate_capability] = "account.group_account_manager"
    _MODELS[_currency_rate_capability] = set(_MODELS["currency.rate.record"])
    _ACCESS[_currency_rate_capability] = {
        ("res.company", "read"), ("res.currency", "read"),
        ("res.currency.rate", "read"), ("res.currency.rate", _currency_rate_operation),
    }
_MODELS["bank.statement.update"].update({"account.journal", "account.move"})
_ACCESS["bank.statement.update"].update({
    ("account.journal", "read"), ("account.move", "read"),
    ("account.bank.statement.line", "write"),
})
_MODELS["bank.transaction.update"].add("res.currency")
_ACCESS["bank.transaction.update"].add(("res.currency", "read"))
_MODELS["bank.transaction.unmatch"].add("account.account")
_ACCESS["bank.transaction.unmatch"].add(("account.account", "read"))
for _bank_foreign_capability in ("bank.transaction.record", "bank.transaction.update"):
    _MODELS[_bank_foreign_capability].add("res.currency.rate")
    _ACCESS[_bank_foreign_capability].add(("res.currency.rate", "read"))

_GROUPS["bank.transaction.counterparts.replace"] = "account.group_account_user"
_MODELS["bank.transaction.counterparts.replace"] = {
    "res.company", "res.currency", "res.partner", "res.partner.bank",
    "account.journal", "account.account", "account.bank.statement.line",
    "account.move", "account.move.line", "account.payment",
    "account.partial.reconcile", "account.full.reconcile",
}
_ACCESS["bank.transaction.counterparts.replace"] = {
    ("res.company", "read"), ("res.currency", "read"),
    ("res.partner", "read"), ("res.partner.bank", "read"),
    ("account.journal", "read"),
    ("account.account", "read"), ("account.bank.statement.line", "read"),
    ("account.bank.statement.line", "write"), ("account.move", "read"),
    ("account.move", "write"), ("account.move.line", "read"),
    ("account.move.line", "create"), ("account.move.line", "write"),
    ("account.move.line", "unlink"), ("account.payment", "read"),
    ("account.partial.reconcile", "read"), ("account.full.reconcile", "read"),
}

for _capability_id in _ACCOUNT_GROUP_WRITE_CAPABILITIES:
    _MODELS[_capability_id] = {"res.company", "account.group"}
    _ACCESS[_capability_id] = {
        ("res.company", "read"),
        ("account.group", "read"),
    }
_ACCESS["account.group.create"].add(("account.group", "create"))
_ACCESS["account.group.update"].add(("account.group", "write"))

_MODELS["tax.repartition_lines.replace"] = {
    "res.company",
    "account.tax",
    "account.tax.repartition.line",
    "account.account",
    "account.account.tag",
}
_ACCESS["tax.repartition_lines.replace"] = {
    ("res.company", "read"),
    ("account.tax", "read"),
    ("account.tax", "write"),
    ("account.tax.repartition.line", "read"),
    ("account.tax.repartition.line", "create"),
    ("account.tax.repartition.line", "write"),
    ("account.tax.repartition.line", "unlink"),
    ("account.account", "read"),
    ("account.account.tag", "read"),
}

_RECONCILIATION_MODEL_HEADER_MODELS = {
    "res.company",
    "res.partner",
    "account.journal",
    "account.reconcile.model",
}
_RECONCILIATION_MODEL_HEADER_ACCESS = {
    ("res.company", "read"),
    ("res.partner", "read"),
    ("account.journal", "read"),
    ("account.reconcile.model", "read"),
}
for _capability_id in (
    "reconciliation.model.create",
    "reconciliation.model.update",
):
    _MODELS[_capability_id] = set(_RECONCILIATION_MODEL_HEADER_MODELS)
    _ACCESS[_capability_id] = set(_RECONCILIATION_MODEL_HEADER_ACCESS)
_ACCESS["reconciliation.model.create"].add(("account.reconcile.model", "create"))
_ACCESS["reconciliation.model.update"].add(("account.reconcile.model", "write"))

_MODELS["reconciliation.model.lines.replace"] = {
    "res.company",
    "res.partner",
    "account.account",
    "account.tax",
    "account.analytic.account",
    "account.reconcile.model",
    "account.reconcile.model.line",
}
_ACCESS["reconciliation.model.lines.replace"] = {
    ("res.company", "read"),
    ("res.partner", "read"),
    ("account.account", "read"),
    ("account.tax", "read"),
    ("account.analytic.account", "read"),
    ("account.reconcile.model", "read"),
    ("account.reconcile.model", "write"),
    ("account.reconcile.model.line", "read"),
    ("account.reconcile.model.line", "create"),
    ("account.reconcile.model.line", "write"),
    ("account.reconcile.model.line", "unlink"),
}
for _capability_id in (
    "reconciliation.model.archive",
    "reconciliation.model.restore",
):
    _MODELS[_capability_id] = {"res.company", "account.reconcile.model"}
    _ACCESS[_capability_id] = {
        ("res.company", "read"),
        ("account.reconcile.model", "read"),
        ("account.reconcile.model", "write"),
    }

for _capability_id in (
    "account.tag.create",
    "account.tag.update",
    "account.tag.archive",
    "account.tag.restore",
):
    _MODELS[_capability_id] = {"res.company", "res.country", "account.account.tag"}
    _ACCESS[_capability_id] = {
        ("res.company", "read"),
        ("res.country", "read"),
        ("account.account.tag", "read"),
    }
_ACCESS["account.tag.create"].add(("account.account.tag", "create"))
for _capability_id in ("account.tag.update", "account.tag.archive", "account.tag.restore"):
    _ACCESS[_capability_id].add(("account.account.tag", "write"))

for _capability_id in ("tax.group.create", "tax.group.update"):
    _MODELS[_capability_id] = {"res.company", "res.country", "account.tax.group", "account.account"}
    _ACCESS[_capability_id] = {
        ("res.company", "read"),
        ("res.country", "read"),
        ("account.tax.group", "read"),
        ("account.account", "read"),
    }
_ACCESS["tax.group.create"].add(("account.tax.group", "create"))
_ACCESS["tax.group.update"].add(("account.tax.group", "write"))

for _capability_id in ("cash_rounding.create", "cash_rounding.update"):
    _MODELS[_capability_id] = {"res.company", "account.account", "account.cash.rounding"}
    _ACCESS[_capability_id] = {
        ("res.company", "read"),
        ("account.account", "read"),
        ("account.cash.rounding", "read"),
    }
_ACCESS["cash_rounding.create"].add(("account.cash.rounding", "create"))
_ACCESS["cash_rounding.update"].add(("account.cash.rounding", "write"))

for _capability_id in ("fiscal_year.create", "fiscal_year.update"):
    _MODELS[_capability_id] = {"res.company", "account.fiscal.year"}
    _ACCESS[_capability_id] = {
        ("res.company", "read"),
        ("account.fiscal.year", "read"),
    }
_ACCESS["fiscal_year.create"].add(("account.fiscal.year", "create"))
_ACCESS["fiscal_year.update"].add(("account.fiscal.year", "write"))

for _capability_id in (
    "analytic.applicability.create",
    "analytic.applicability.update",
):
    _MODELS[_capability_id] = {
        "res.company",
        "account.analytic.plan",
        "product.category",
        "account.analytic.applicability",
    }
    _ACCESS[_capability_id] = {
        ("res.company", "read"),
        ("account.analytic.plan", "read"),
        ("product.category", "read"),
        ("account.analytic.applicability", "read"),
    }
_ACCESS["analytic.applicability.create"].add(
    ("account.analytic.applicability", "create")
)
_ACCESS["analytic.applicability.update"].add(
    ("account.analytic.applicability", "write")
)

for _capability_id in (
    "analytic.distribution_model.create",
    "analytic.distribution_model.update",
):
    _MODELS[_capability_id] = {
        "res.company",
        "res.partner",
        "res.partner.category",
        "product.product",
        "product.category",
        "account.analytic.plan",
        "account.analytic.account",
        "account.analytic.distribution.model",
    }
    _ACCESS[_capability_id] = {
        ("res.company", "read"),
        ("res.partner", "read"),
        ("res.partner.category", "read"),
        ("product.product", "read"),
        ("product.category", "read"),
        ("account.analytic.plan", "read"),
        ("account.analytic.account", "read"),
        ("account.analytic.distribution.model", "read"),
    }
_ACCESS["analytic.distribution_model.create"].add(
    ("account.analytic.distribution.model", "create")
)
_ACCESS["analytic.distribution_model.update"].add(
    ("account.analytic.distribution.model", "write")
)


for _capability_id in ("customer_invoice.create", "vendor_bill.create"):
    _MODELS[_capability_id].update(
        {"product.product", "account.payment.term", "account.analytic.account"}
    )

for _capability_id in (
    "customer_invoice.create",
    "vendor_bill.create",
    "invoice.update",
):
    _MODELS[_capability_id].update({"res.partner.bank", "account.fiscal.position"})
    _ACCESS[_capability_id].update(
        {("res.partner.bank", "read"), ("account.fiscal.position", "read")}
    )

_MODELS["invoice.lines.replace"].add("account.analytic.account")
for _capability_id, _single_capability in (
    ("invoice.lines.update", "invoice.line.update"),
    ("invoice.lines.add", "invoice.line.create"),
    ("invoice.lines.remove", "invoice.line.delete"),
):
    _GROUPS[_capability_id] = _GROUPS[_single_capability]
    _MODELS[_capability_id] = set(_MODELS[_single_capability])
    _ACCESS[_capability_id] = set(_ACCESS[_single_capability])

for _capability_id in ("journal_entry.create", "journal_entry.lines.replace"):
    _MODELS[_capability_id].update({"res.currency", "account.analytic.account"})

for _capability_id in ("customer_credit_note.create", "vendor_refund.create"):
    _MODELS[_capability_id].update(
        {
            "res.partner",
            "product.product",
            "account.account",
            "account.tax",
            "account.move.line",
            "account.analytic.account",
        }
    )
    _ACCESS[_capability_id].update(
        {
            ("res.partner", "read"),
            ("account.account", "read"),
            ("account.tax", "read"),
            ("account.move.line", "read"),
            ("account.move.line", "create"),
            ("account.move.line", "write"),
            ("account.move.line", "unlink"),
        }
    )

for _capability_id in (
    "receivable.payment.register",
    "payable.payment.register",
):
    _MODELS[_capability_id].update(
        {
            "account.partial.reconcile", "account.full.reconcile",
            "account.payment.method.line", "res.partner.bank",
        }
    )
    _ACCESS[_capability_id].update(
        {
            ("account.move.line", "write"),
            ("account.partial.reconcile", "read"),
            ("account.partial.reconcile", "create"),
            ("account.full.reconcile", "read"),
            ("account.payment.method.line", "read"),
            ("res.partner.bank", "read"),
        }
    )

for _capability_id in ("reconciliation.apply", "reconciliation.undo"):
    _MODELS[_capability_id].update({"res.partner", "account.account", "account.move"})
    _ACCESS[_capability_id].update(
        {
            ("res.partner", "read"),
            ("account.account", "read"),
            ("account.move", "read"),
            ("account.move", "write"),
        }
    )

for _capability_id in ("invoice.post", "journal_entry.post"):
    _MODELS[_capability_id].update(
        {"account.move.line", "account.analytic.account", "account.analytic.line"}
    )
    _ACCESS[_capability_id].update(
        {
            ("account.move.line", "read"),
        }
    )

for _capability_id in (
    "invoice.cancel",
    "invoice.reset_to_draft",
    "journal_entry.cancel",
    "journal_entry.reset_to_draft",
):
    _MODELS[_capability_id].update({"account.move.line", "account.analytic.line"})
    _ACCESS[_capability_id].update(
        {
            ("account.move.line", "read"),
        }
    )

_MODELS["journal_entry.reverse"].update(
    {"account.move.line", "account.analytic.account", "account.analytic.line"}
)
_ACCESS["journal_entry.reverse"].update(
    {
        ("account.move.line", "read"),
        ("account.move.line", "create"),
    }
)


def _fail(
    failure_type: type[Exception],
    code: str,
    message: str,
    *,
    exit_code: int,
    details: dict[str, Any] | None = None,
) -> Exception:
    return failure_type(
        code,
        message,
        exit_code=exit_code,
        retryable=False,
        details=details or {},
    )


def _protocol(failure_type: type[Exception]) -> Exception:
    return _fail(
        failure_type,
        "bridge_protocol_error",
        "The core-write bridge payload is invalid.",
        exit_code=7,
    )


_PARAMETER_KEYS.update({
    "invoice.service_dates.update": {"move_id", "changes"},
    "invoice.tax_totals.adjust": {"move_id", "groups"},
})
_GROUPS["invoice.reverse_and_reissue"] = "account.group_account_invoice"
_MODELS["invoice.reverse_and_reissue"] = (
    _MODELS["customer_credit_note.create"] | _MODELS["invoice.post"]
    | _MODELS["reconciliation.apply"] | _MODELS["reconciliation.undo"]
    | {"account.tax", "res.currency", "res.currency.rate", "account.payment"}
)
_ACCESS["invoice.reverse_and_reissue"] = (
    _ACCESS["customer_credit_note.create"] | _ACCESS["invoice.post"]
    | _ACCESS["reconciliation.apply"] | _ACCESS["reconciliation.undo"]
    | {("account.tax", "read"), ("res.currency", "read"),
       ("res.currency.rate", "read"), ("account.payment", "read"),
       ("account.payment", "write"), ("account.move.line", "create"),
       ("account.move.line", "unlink"), ("account.full.reconcile", "create"),
       ("account.analytic.line", "create"), ("account.analytic.line", "unlink")}
)
_MODELS["reconciliation.undo"].update({
    "account.payment", "account.journal", "account.tax", "res.currency",
    "res.currency.rate", "account.analytic.account", "account.analytic.line",
})
_ACCESS["reconciliation.undo"].update({
    ("account.payment", "read"), ("account.payment", "write"),
    ("account.journal", "read"), ("account.tax", "read"),
    ("res.currency", "read"), ("res.currency.rate", "read"),
    ("account.move", "create"), ("account.move", "unlink"),
    ("account.move.line", "create"), ("account.move.line", "unlink"),
    ("account.partial.reconcile", "create"), ("account.full.reconcile", "create"),
    ("account.analytic.account", "read"), ("account.analytic.line", "read"),
    ("account.analytic.line", "create"), ("account.analytic.line", "unlink"),
})
_MODELS["invoice.reverse_and_reissue"].update(_MODELS["reconciliation.undo"])
_ACCESS["invoice.reverse_and_reissue"].update(_ACCESS["reconciliation.undo"])
for _invoice_preparation_capability in invoice_preparation.CAPABILITY_IDS:
    _GROUPS[_invoice_preparation_capability] = "account.group_account_invoice"
    _MODELS[_invoice_preparation_capability] = {
        "res.company", "account.move", "account.move.line", "account.account",
        "account.tax", "res.currency",
    }
    _ACCESS[_invoice_preparation_capability] = {
        ("res.company", "read"), ("account.move", "read"),
        ("account.move", "write"), ("account.move.line", "read"),
        ("account.move.line", "write"), ("account.move.line", "create"),
        ("account.move.line", "unlink"), ("account.account", "read"),
        ("account.tax", "read"), ("res.currency", "read"),
    }
_MODELS["invoice.service_dates.update"].add("res.currency.rate")
_ACCESS["invoice.service_dates.update"].add(("res.currency.rate", "read"))

_PARAMETER_KEYS.update(journal_item_processing.PARAMETER_KEYS)
for _journal_item_capability in journal_item_processing.CAPABILITY_IDS:
    _GROUPS[_journal_item_capability] = (
        "account.group_account_invoice"
        if _journal_item_capability.startswith("invoice.")
        else "account.group_account_user"
    )
    _MODELS[_journal_item_capability] = {
        "res.company", "account.move", "account.move.line", "account.account",
    }
    _ACCESS[_journal_item_capability] = {
        ("res.company", "read"), ("account.move", "read"),
        ("account.move.line", "read"), ("account.move.line", "write"),
        ("account.account", "read"),
    }
for _journal_item_capability in (
    "journal_item.analytic_distribution.replace", "journal_entry.lines.update",
):
    _MODELS[_journal_item_capability].update({
        "account.analytic.account", "account.analytic.plan", "account.analytic.line",
    })
    _ACCESS[_journal_item_capability].update({
        ("account.analytic.account", "read"), ("account.analytic.plan", "read"),
        ("account.analytic.line", "read"), ("account.analytic.line", "create"),
        ("account.analytic.line", "unlink"),
    })
_MODELS["journal_entry.lines.update"].update({"account.journal", "res.partner", "res.currency", "res.currency.rate"})
_ACCESS["journal_entry.lines.update"].update({
    ("account.move", "write"), ("account.journal", "read"), ("res.partner", "read"),
    ("res.currency", "read"), ("res.currency.rate", "read"),
})
_GROUPS["journal_entry.lines.add"] = "account.group_account_user"
_MODELS["journal_entry.lines.add"] = set(_MODELS["journal_entry.lines.update"])
_ACCESS["journal_entry.lines.add"] = (
    _ACCESS["journal_entry.lines.update"] - {("account.move.line", "write")}
) | {("account.move.line", "create")}
_GROUPS["journal_entry.lines.remove"] = "account.group_account_user"
_MODELS["journal_entry.lines.remove"] = {
    "res.company", "account.move", "account.move.line", "account.account",
    "account.journal", "account.analytic.line",
}
_ACCESS["journal_entry.lines.remove"] = {
    ("res.company", "read"), ("account.move", "read"), ("account.move", "write"),
    ("account.move.line", "read"), ("account.move.line", "unlink"),
    ("account.account", "read"), ("account.journal", "read"),
    ("account.analytic.line", "read"), ("account.analytic.line", "unlink"),
}
for _capability_id in (
    "journal_entry.create", "journal_entry.lines.replace",
    "journal_entry.lines.add", "journal_entry.lines.update",
):
    _MODELS[_capability_id].update({
        "account.tax", "account.tax.repartition.line", "account.account.tag",
    })
    _ACCESS[_capability_id].update({
        ("account.tax", "read"), ("account.tax.repartition.line", "read"),
        ("account.account.tag", "read"),
    })
for _journal_item_capability in (
    "invoice.line.unit.assign", "invoice.line.deductibility.update",
):
    _MODELS[_journal_item_capability].update({
        "account.journal", "account.tax", "res.currency", "product.product",
        "product.template", "account.fiscal.position",
    })
    _ACCESS[_journal_item_capability].update({
        ("account.move", "write"), ("account.move.line", "create"),
        ("account.move.line", "unlink"), ("account.journal", "read"),
        ("account.tax", "read"), ("res.currency", "read"),
        ("product.product", "read"), ("product.template", "read"),
        ("account.fiscal.position", "read"),
    })
_MODELS["invoice.line.unit.assign"].add("uom.uom")
_ACCESS["invoice.line.unit.assign"].add(("uom.uom", "read"))

_PARAMETER_KEYS.update(company_processing.PARAMETER_KEYS)
_GROUPS['company.bill_processing_policy.update'] = "base.group_erp_manager"
_MODELS['company.bill_processing_policy.update'] = {'res.company', 'ir.default'}
_ACCESS['company.bill_processing_policy.update'] = {('ir.default', 'read'), ('res.company', 'write'), ('res.company', 'read')}
_GROUPS['company.cash_discount_accounts.assign'] = "base.group_erp_manager"
_MODELS['company.cash_discount_accounts.assign'] = {'res.company', 'account.account', 'ir.default'}
_ACCESS['company.cash_discount_accounts.assign'] = {('ir.default', 'read'), ('res.company', 'write'), ('account.account', 'read'), ('res.company', 'read')}
_GROUPS['company.credit_policy.update'] = "base.group_erp_manager"
_MODELS['company.credit_policy.update'] = {'res.company', 'ir.default'}
_ACCESS['company.credit_policy.update'] = {('ir.default', 'read'), ('res.company', 'write'), ('res.company', 'read')}
_GROUPS['company.exchange_configuration.update'] = "base.group_erp_manager"
_MODELS['company.exchange_configuration.update'] = {'res.company', 'account.account', 'ir.default', 'account.journal'}
_ACCESS['company.exchange_configuration.update'] = {('res.company', 'read'), ('ir.default', 'read'), ('res.company', 'write'), ('account.journal', 'read'), ('account.account', 'read')}
_GROUPS["company.cash_basis_configuration.update"] = "base.group_erp_manager"
_MODELS["company.cash_basis_configuration.update"] = {"res.company", "account.account", "account.journal", "ir.default"}
_ACCESS["company.cash_basis_configuration.update"] = {
    ("res.company", "read"), ("res.company", "write"),
    ("account.account", "read"), ("account.journal", "read"), ("ir.default", "read"),
}
for _tax_configuration_capability in ("tax.create", "tax.update"):
    _MODELS[_tax_configuration_capability].add("account.account")
    _ACCESS[_tax_configuration_capability].add(("account.account", "read"))
_GROUPS['company.fiscal_year_end.update'] = "base.group_erp_manager"
_MODELS['company.fiscal_year_end.update'] = {'res.company', 'ir.default'}
_ACCESS['company.fiscal_year_end.update'] = {('ir.default', 'read'), ('res.company', 'write'), ('res.company', 'read')}
_GROUPS['company.invoice_display.update'] = "base.group_erp_manager"
_MODELS['company.invoice_display.update'] = {'res.company', 'ir.default'}
_ACCESS['company.invoice_display.update'] = {('ir.default', 'read'), ('res.company', 'write'), ('res.company', 'read')}
_GROUPS['company.tax_policy.update'] = "base.group_erp_manager"
_MODELS['company.tax_policy.update'] = {'res.company', 'ir.default', 'account.tax'}
_ACCESS['company.tax_policy.update'] = {('ir.default', 'read'), ('account.tax', 'read'), ('res.company', 'write'), ('res.company', 'read')}
for _company_account_capability in (
    "company.default_accounts.assign", "company.bank_defaults.assign",
    "company.discount_allocation_accounts.assign",
):
    _GROUPS[_company_account_capability] = "base.group_erp_manager"
    _MODELS[_company_account_capability] = {"res.company", "account.account", "ir.default"}
    _ACCESS[_company_account_capability] = {
        ("res.company", "read"), ("res.company", "write"),
        ("account.account", "read"), ("ir.default", "read"),
    }
_PARAMETER_KEYS.update(analytic_processing.PARAMETER_KEYS)
_GROUPS['analytic.account.delete'] = "account.group_account_manager"
_MODELS['analytic.account.delete'] = {'res.company', 'account.analytic.account'}
_ACCESS['analytic.account.delete'] = {('res.company', 'read'), ('account.analytic.account', 'read'), ('account.analytic.account', 'unlink')}
_GROUPS['analytic.account.duplicate'] = "account.group_account_manager"
_MODELS['analytic.account.duplicate'] = {'res.company', 'account.analytic.plan', 'account.analytic.account', 'res.partner'}
_ACCESS['analytic.account.duplicate'] = {('res.company', 'read'), ('account.analytic.account', 'create'), ('res.partner', 'read'), ('account.analytic.account', 'read'), ('account.analytic.plan', 'read')}
_GROUPS['analytic.applicability.delete'] = "account.group_account_manager"
_MODELS['analytic.applicability.delete'] = {'account.analytic.applicability', 'res.company'}
_ACCESS['analytic.applicability.delete'] = {('account.analytic.applicability', 'read'), ('account.analytic.applicability', 'unlink'), ('res.company', 'read')}
_GROUPS['analytic.distribution_model.delete'] = "account.group_account_manager"
_MODELS['analytic.distribution_model.delete'] = {'res.company', 'account.analytic.distribution.model'}
_ACCESS['analytic.distribution_model.delete'] = {('account.analytic.distribution.model', 'read'), ('res.company', 'read'), ('account.analytic.distribution.model', 'unlink')}
_PARAMETER_KEYS.update(journal_processing.PARAMETER_KEYS)
_GROUPS['journal.delete'] = "account.group_account_manager"
_MODELS['journal.delete'] = {'account.journal', 'account.move', 'account.payment.method.line', 'res.company', 'res.partner.bank', 'mail.alias'}
_ACCESS['journal.delete'] = {('mail.alias', 'read'), ('account.move', 'read'), ('account.payment.method.line', 'unlink'), ('account.journal', 'unlink'), ('res.company', 'read'), ('res.partner.bank', 'read'), ('account.payment.method.line', 'read'), ('account.journal', 'read')}
_GROUPS['journal.duplicate'] = "account.group_account_manager"
_MODELS['journal.duplicate'] = {'account.journal', 'account.account', 'account.payment.method.line', 'res.company', 'res.currency', 'mail.alias', 'ir.actions.report', 'account.payment.method'}
_ACCESS['journal.duplicate'] = {('account.payment.method.line', 'create'), ('mail.alias', 'read'), ('account.journal', 'create'), ('res.currency', 'read'), ('res.company', 'read'), ('account.journal', 'write'), ('account.account', 'read'), ('account.payment.method', 'read'), ('account.account', 'create'), ('account.account', 'write'), ('account.payment.method.line', 'read'), ('ir.actions.report', 'read'), ('account.journal', 'read')}
_GROUPS['journal.group.delete'] = "account.group_account_manager"
_MODELS['journal.group.delete'] = {'res.company', 'account.journal.group'}
_ACCESS['journal.group.delete'] = {('account.journal.group', 'unlink'), ('res.company', 'read'), ('account.journal.group', 'read')}
_GROUPS['journal.invoice_reference.update'] = "account.group_account_manager"
_MODELS['journal.invoice_reference.update'] = {'res.company', 'account.journal'}
_ACCESS['journal.invoice_reference.update'] = {('res.company', 'read'), ('account.journal', 'write'), ('account.journal', 'read')}
_GROUPS['journal.invoice_template.assign'] = "account.group_account_manager"
_MODELS['journal.invoice_template.assign'] = {'res.company', 'account.journal', 'ir.actions.report'}
_ACCESS['journal.invoice_template.assign'] = {('ir.actions.report', 'read'), ('res.company', 'read'), ('account.journal', 'write'), ('account.journal', 'read')}
_GROUPS['journal.non_deductible_account.assign'] = "account.group_account_manager"
_MODELS['journal.non_deductible_account.assign'] = {'res.company', 'account.journal', 'account.account'}
_ACCESS['journal.non_deductible_account.assign'] = {('account.account', 'read'), ('res.company', 'read'), ('account.journal', 'write'), ('account.journal', 'read')}
_GROUPS['journal.sequence_policy.update'] = "account.group_account_manager"
_MODELS['journal.sequence_policy.update'] = {'res.company', 'account.journal'}
_ACCESS['journal.sequence_policy.update'] = {('res.company', 'read'), ('account.journal', 'write'), ('account.journal', 'read')}
_PARAMETER_KEYS.update(account_processing.PARAMETER_KEYS)
_GROUPS['account.account.default_taxes.assign'] = "account.group_account_manager"
_MODELS['account.account.default_taxes.assign'] = {'res.company', 'account.tax', 'account.account'}
_ACCESS['account.account.default_taxes.assign'] = {('account.account', 'write'), ('account.tax', 'read'), ('res.company', 'read'), ('account.account', 'read')}
_GROUPS['account.account.delete'] = "account.group_account_manager"
_MODELS['account.account.delete'] = {'account.fiscal.position.account', 'account.move.line', 'account.code.mapping', 'account.account', 'res.company', 'account.tax.repartition.line'}
_ACCESS['account.account.delete'] = {('account.fiscal.position.account', 'read'), ('account.move.line', 'read'), ('account.tax.repartition.line', 'read'), ('account.account', 'read'), ('account.code.mapping', 'read'), ('res.company', 'read'), ('account.account', 'unlink')}
_GROUPS['account.account.duplicate'] = "account.group_account_manager"
_MODELS['account.account.duplicate'] = {'res.currency', 'account.tax', 'account.code.mapping', 'account.account', 'res.company', 'account.account.tag'}
_ACCESS['account.account.duplicate'] = {('account.account.tag', 'read'), ('account.account', 'read'), ('account.code.mapping', 'read'), ('account.account', 'create'), ('res.company', 'read'), ('res.currency', 'read'), ('account.tax', 'read')}
_GROUPS['account.account.non_trade.set'] = "account.group_account_manager"
_MODELS['account.account.non_trade.set'] = {'res.company', 'account.account'}
_ACCESS['account.account.non_trade.set'] = {('account.account', 'write'), ('res.company', 'read'), ('account.account', 'read')}
_GROUPS['account.account.notes.update'] = "account.group_account_manager"
_MODELS['account.account.notes.update'] = {'res.company', 'account.account'}
_ACCESS['account.account.notes.update'] = {('account.account', 'write'), ('res.company', 'read'), ('account.account', 'read')}
_GROUPS['account.account.tags.assign'] = "account.group_account_manager"
_MODELS['account.account.tags.assign'] = {'res.company', 'account.account', 'account.account.tag'}
_ACCESS['account.account.tags.assign'] = {('account.account', 'write'), ('res.company', 'read'), ('account.account.tag', 'read'), ('account.account', 'read')}
_GROUPS['account.group.delete'] = "account.group_account_manager"
_MODELS['account.group.delete'] = {'res.company', 'account.group'}
_ACCESS['account.group.delete'] = {('account.group', 'read'), ('res.company', 'read'), ('account.group', 'write'), ('account.group', 'unlink')}
_PARAMETER_KEYS.update(tax_processing.PARAMETER_KEYS)
_GROUPS['tax.delete'] = "account.group_account_manager"
_MODELS['tax.delete'] = {'account.move.line', 'account.tax', 'res.company', 'account.tax.repartition.line'}
_ACCESS['tax.delete'] = {('res.company', 'read'), ('account.tax', 'unlink'), ('account.tax.repartition.line', 'read'), ('account.tax.repartition.line', 'unlink'), ('account.move.line', 'read'), ('account.tax', 'read')}
_GROUPS['tax.repartition_line.update'] = "account.group_account_manager"
_MODELS['tax.repartition_line.update'] = {'account.account.tag', 'res.country', 'account.tax', 'res.company', 'account.account', 'account.tax.repartition.line'}
_ACCESS['tax.repartition_line.update'] = {('account.tax.repartition.line', 'write'), ('account.tax', 'read'), ('res.company', 'read'), ('res.country', 'read'), ('account.account.tag', 'read'), ('account.tax.repartition.line', 'read'), ('account.tax', 'write'), ('account.account', 'read')}
_GROUPS['tax.repartition_lines.resequence'] = "account.group_account_manager"
_MODELS['tax.repartition_lines.resequence'] = {'account.account.tag', 'res.country', 'account.tax', 'res.company', 'account.account', 'account.tax.repartition.line'}
_ACCESS['tax.repartition_lines.resequence'] = {('account.tax.repartition.line', 'write'), ('account.tax', 'read'), ('res.company', 'read'), ('res.country', 'read'), ('account.account.tag', 'read'), ('account.tax.repartition.line', 'read'), ('account.tax', 'write'), ('account.account', 'read')}
_GROUPS['tax.repartition_lines.update'] = "account.group_account_manager"
_MODELS['tax.repartition_lines.update'] = {'account.account.tag', 'res.country', 'account.tax', 'res.company', 'account.account', 'account.tax.repartition.line'}
_ACCESS['tax.repartition_lines.update'] = {('account.tax.repartition.line', 'write'), ('account.tax', 'read'), ('res.company', 'read'), ('res.country', 'read'), ('account.account.tag', 'read'), ('account.tax.repartition.line', 'read'), ('account.tax', 'write'), ('account.account', 'read')}
_GROUPS['tax.repartition_pair.create'] = "account.group_account_manager"
_MODELS['tax.repartition_pair.create'] = {'account.account.tag', 'res.country', 'account.tax', 'res.company', 'account.account', 'account.tax.repartition.line'}
_ACCESS['tax.repartition_pair.create'] = {('account.tax', 'read'), ('account.tax.repartition.line', 'create'), ('res.company', 'read'), ('res.country', 'read'), ('account.account.tag', 'read'), ('account.tax.repartition.line', 'read'), ('account.tax', 'write'), ('account.account', 'read')}
_GROUPS['tax.repartition_pair.delete'] = "account.group_account_manager"
_MODELS['tax.repartition_pair.delete'] = {'account.tax', 'res.company', 'account.tax.repartition.line'}
_ACCESS['tax.repartition_pair.delete'] = {('account.tax.repartition.line', 'unlink'), ('account.tax', 'read'), ('res.company', 'read'), ('account.tax.repartition.line', 'read'), ('account.tax', 'write')}
_PARAMETER_KEYS.update(payment_term_processing.PARAMETER_KEYS)
_GROUPS['payment_term.delete'] = "account.group_account_manager"
_MODELS['payment_term.delete'] = {'account.payment.term.line', 'account.move', 'account.payment.term', 'res.company'}
_ACCESS['payment_term.delete'] = {('account.move', 'read'), ('account.payment.term', 'unlink'), ('res.company', 'read'), ('account.payment.term.line', 'unlink'), ('account.payment.term', 'read'), ('account.payment.term.line', 'read')}
_GROUPS['payment_term.duplicate'] = "account.group_account_manager"
_MODELS['payment_term.duplicate'] = {'account.payment.term.line', 'account.payment.term', 'res.company'}
_ACCESS['payment_term.duplicate'] = {('account.payment.term.line', 'create'), ('res.company', 'read'), ('account.payment.term', 'read'), ('account.payment.term', 'create'), ('account.payment.term.line', 'read'), ('account.payment.term', 'write')}
_GROUPS['payment_term.line.create'] = "account.group_account_manager"
_MODELS['payment_term.line.create'] = {'account.payment.term.line', 'account.payment.term', 'res.company'}
_ACCESS['payment_term.line.create'] = {('account.payment.term.line', 'create'), ('res.company', 'read'), ('account.payment.term', 'read'), ('account.payment.term.line', 'read'), ('account.payment.term', 'write')}
_GROUPS['payment_term.line.delete'] = "account.group_account_manager"
_MODELS['payment_term.line.delete'] = {'account.payment.term.line', 'account.payment.term', 'res.company'}
_ACCESS['payment_term.line.delete'] = {('res.company', 'read'), ('account.payment.term.line', 'unlink'), ('account.payment.term', 'read'), ('account.payment.term.line', 'read'), ('account.payment.term', 'write')}
_GROUPS['payment_term.line.update'] = "account.group_account_manager"
_MODELS['payment_term.line.update'] = {'account.payment.term.line', 'account.payment.term', 'res.company'}
_ACCESS['payment_term.line.update'] = {('res.company', 'read'), ('account.payment.term', 'read'), ('account.payment.term.line', 'write'), ('account.payment.term.line', 'read'), ('account.payment.term', 'write')}
_GROUPS['payment_term.lines.update'] = "account.group_account_manager"
_MODELS['payment_term.lines.update'] = {'account.payment.term.line', 'account.payment.term', 'res.company'}
_ACCESS['payment_term.lines.update'] = {('res.company', 'read'), ('account.payment.term', 'read'), ('account.payment.term.line', 'write'), ('account.payment.term.line', 'read'), ('account.payment.term', 'write')}
_PARAMETER_KEYS.update(reconciliation_processing.PARAMETER_KEYS)
_GROUPS['reconciliation.model.activity_type.assign'] = "account.group_account_manager"
_MODELS['reconciliation.model.activity_type.assign'] = {'res.company', 'account.reconcile.model', 'account.reconcile.model.line', 'mail.activity.type'}
_ACCESS['reconciliation.model.activity_type.assign'] = {('account.reconcile.model', 'write'), ('mail.activity.type', 'read'), ('account.reconcile.model', 'read'), ('res.company', 'read'), ('account.reconcile.model.line', 'read')}
_GROUPS['reconciliation.model.delete'] = "account.group_account_manager"
_MODELS['reconciliation.model.delete'] = {'res.company', 'account.reconcile.model', 'account.reconcile.model.line'}
_ACCESS['reconciliation.model.delete'] = {('account.reconcile.model.line', 'unlink'), ('account.reconcile.model', 'unlink'), ('account.reconcile.model', 'read'), ('res.company', 'read'), ('account.reconcile.model.line', 'read')}
_GROUPS['reconciliation.model.duplicate'] = "account.group_account_manager"
_MODELS['reconciliation.model.duplicate'] = {'res.partner', 'res.company', 'account.reconcile.model.line', 'mail.activity.type', 'account.account', 'account.reconcile.model', 'account.analytic.account', 'account.journal', 'account.tax'}
_ACCESS['reconciliation.model.duplicate'] = {('account.reconcile.model', 'create'), ('mail.activity.type', 'read'), ('account.reconcile.model.line', 'read'), ('res.partner', 'read'), ('account.analytic.account', 'read'), ('account.journal', 'read'), ('account.account', 'read'), ('account.reconcile.model.line', 'create'), ('account.tax', 'read'), ('account.reconcile.model', 'read'), ('res.company', 'read')}
_GROUPS['reconciliation.model.line.create'] = "account.group_account_manager"
_MODELS['reconciliation.model.line.create'] = {'res.partner', 'res.company', 'account.tax', 'account.reconcile.model.line', 'account.reconcile.model', 'account.analytic.account', 'account.account'}
_ACCESS['reconciliation.model.line.create'] = {('account.analytic.account', 'read'), ('account.account', 'read'), ('account.reconcile.model.line', 'create'), ('account.tax', 'read'), ('account.reconcile.model', 'read'), ('res.company', 'read'), ('account.reconcile.model.line', 'read'), ('res.partner', 'read')}
_GROUPS['reconciliation.model.line.delete'] = "account.group_account_manager"
_MODELS['reconciliation.model.line.delete'] = {'res.company', 'account.reconcile.model', 'account.reconcile.model.line'}
_ACCESS['reconciliation.model.line.delete'] = {('account.reconcile.model.line', 'unlink'), ('account.reconcile.model', 'read'), ('res.company', 'read'), ('account.reconcile.model.line', 'read')}
_GROUPS['reconciliation.model.line.update'] = "account.group_account_manager"
_MODELS['reconciliation.model.line.update'] = {'res.partner', 'res.company', 'account.tax', 'account.reconcile.model.line', 'account.reconcile.model', 'account.analytic.account', 'account.account'}
_ACCESS['reconciliation.model.line.update'] = {('account.analytic.account', 'read'), ('account.reconcile.model.line', 'write'), ('account.account', 'read'), ('account.tax', 'read'), ('account.reconcile.model', 'read'), ('res.company', 'read'), ('account.reconcile.model.line', 'read'), ('res.partner', 'read')}
_GROUPS['reconciliation.model.lines.resequence'] = "account.group_account_manager"
_MODELS['reconciliation.model.lines.resequence'] = {'res.company', 'account.reconcile.model', 'account.reconcile.model.line'}
_ACCESS['reconciliation.model.lines.resequence'] = {('account.reconcile.model.line', 'write'), ('account.reconcile.model', 'read'), ('res.company', 'read'), ('account.reconcile.model.line', 'read')}
_PARAMETER_KEYS.update(payment_processing.PARAMETER_KEYS)
_GROUPS['payment.bank_account.assign'] = "account.group_account_invoice"
_MODELS['payment.bank_account.assign'] = {'res.company', 'account.move.line', 'account.payment', 'account.move', 'res.partner.bank'}
_ACCESS['payment.bank_account.assign'] = {('account.payment', 'write'), ('account.move', 'read'), ('account.move.line', 'write'), ('account.move.line', 'read'), ('account.payment', 'read'), ('res.partner.bank', 'read'), ('account.move.line', 'unlink'), ('account.move', 'write'), ('account.move.line', 'create'), ('res.company', 'read')}
_GROUPS['payment.destination_account.assign'] = "account.group_account_invoice"
_MODELS['payment.destination_account.assign'] = {'res.company', 'account.move.line', 'account.account', 'account.payment', 'account.move'}
_ACCESS['payment.destination_account.assign'] = {('account.payment', 'write'), ('account.move', 'read'), ('account.move.line', 'write'), ('account.account', 'read'), ('account.move.line', 'read'), ('account.payment', 'read'), ('account.move.line', 'unlink'), ('account.move', 'write'), ('account.move.line', 'create'), ('res.company', 'read')}
_GROUPS['payment.reject'] = "account.group_account_invoice"
_MODELS['payment.reject'] = {'account.payment', 'res.company', 'account.move', 'account.move.line'}
_ACCESS['payment.reject'] = {('account.payment', 'write'), ('account.payment', 'read'), ('account.move', 'read'), ('res.company', 'read'), ('account.move.line', 'read')}
_GROUPS['payment.sent_status.set'] = "account.group_account_invoice"
_MODELS['payment.sent_status.set'] = {'account.payment', 'res.company', 'account.move', 'account.move.line'}
_ACCESS['payment.sent_status.set'] = {('account.payment', 'write'), ('account.payment', 'read'), ('account.move', 'read'), ('res.company', 'read'), ('account.move.line', 'read')}
_GROUPS['payment.validate'] = "account.group_account_invoice"
_MODELS['payment.validate'] = {'account.payment', 'res.company', 'account.move', 'account.move.line'}
_ACCESS['payment.validate'] = {('account.payment', 'write'), ('account.move', 'read'), ('account.move.line', 'write'), ('account.move.line', 'read'), ('account.payment', 'read'), ('account.move', 'create'), ('account.move', 'write'), ('account.move.line', 'create'), ('res.company', 'read')}
_PARAMETER_KEYS.update(invoice_presentation.PARAMETER_KEYS)
_GROUPS['invoice.fiscal_position.refresh'] = "account.group_account_invoice"
_MODELS['invoice.fiscal_position.refresh'] = {'res.company', 'account.account', 'product.template', 'account.move', 'res.currency', 'account.move.line', 'product.product', 'account.tax', 'account.fiscal.position'}
_ACCESS['invoice.fiscal_position.refresh'] = {('account.tax', 'read'), ('account.move.line', 'unlink'), ('res.company', 'read'), ('account.move.line', 'read'), ('product.product', 'read'), ('account.move', 'read'), ('res.currency', 'read'), ('account.account', 'read'), ('account.move.line', 'write'), ('account.move.line', 'create'), ('account.fiscal.position', 'read'), ('product.template', 'read'), ('account.move', 'write')}
_GROUPS['invoice.layout_line.create'] = "account.group_account_invoice"
_MODELS['invoice.layout_line.create'] = {'account.move.line', 'res.company', 'account.move'}
_ACCESS['invoice.layout_line.create'] = {('account.move', 'read'), ('account.move.line', 'create'), ('account.move', 'write'), ('account.move.line', 'read')}
_GROUPS['invoice.layout_line.delete'] = "account.group_account_invoice"
_MODELS['invoice.layout_line.delete'] = {'account.move.line', 'res.company', 'account.move'}
_ACCESS['invoice.layout_line.delete'] = {('account.move', 'read'), ('account.move.line', 'unlink'), ('account.move', 'write'), ('account.move.line', 'read')}
_GROUPS['invoice.layout_line.update'] = "account.group_account_invoice"
_MODELS['invoice.layout_line.update'] = {'account.move.line', 'res.company', 'account.move'}
_ACCESS['invoice.layout_line.update'] = {('account.move', 'read'), ('account.move.line', 'write'), ('account.move', 'write'), ('account.move.line', 'read')}
_GROUPS['invoice.lines.resequence'] = "account.group_account_invoice"
_MODELS['invoice.lines.resequence'] = {'account.move.line', 'res.company', 'account.move'}
_ACCESS['invoice.lines.resequence'] = {('account.move', 'read'), ('account.move.line', 'write'), ('account.move', 'write'), ('account.move.line', 'read')}
_GROUPS['invoice.presentation_settings.update'] = "account.group_account_invoice"
_MODELS['invoice.presentation_settings.update'] = {'res.partner', 'account.move.line', 'res.company', 'res.users', 'account.move'}
_ACCESS['invoice.presentation_settings.update'] = {('res.partner', 'read'), ('account.move.line', 'read'), ('res.users', 'read'), ('account.move', 'write'), ('account.move', 'read')}
_PARAMETER_KEYS.update(move_processing.PARAMETER_KEYS)
_GROUPS['accounting_move.autopost.configure'] = 'account.group_account_user'
_MODELS['accounting_move.autopost.configure'] = {'account.move', 'account.move.line', 'res.company'}
_ACCESS['accounting_move.autopost.configure'] = {('account.move.line', 'read'), ('account.move', 'read'), ('account.move', 'write')}
_GROUPS['accounting_move.review.set'] = 'account.group_account_user'
_MODELS['accounting_move.review.set'] = {'account.move', 'account.move.line', 'res.company'}
_ACCESS['accounting_move.review.set'] = {('account.move.line', 'read'), ('account.move', 'read'), ('account.move', 'write')}
_GROUPS['invoice.cash_rounding.assign'] = 'account.group_account_invoice'
_MODELS['invoice.cash_rounding.assign'] = {'account.move', 'account.cash.rounding', 'res.company', 'account.account', 'account.move.line'}
_ACCESS['invoice.cash_rounding.assign'] = {('account.move.line', 'read'), ('account.cash.rounding', 'read'), ('account.move', 'read'), ('account.move.line', 'unlink'), ('account.move', 'write'), ('account.move.line', 'write'), ('account.account', 'read'), ('account.move.line', 'create')}
_GROUPS['invoice.currency_rate.refresh'] = 'account.group_account_invoice'
_MODELS['invoice.currency_rate.refresh'] = {'account.move', 'res.company', 'res.currency', 'res.currency.rate', 'account.move.line'}
_ACCESS['invoice.currency_rate.refresh'] = {('account.move.line', 'read'), ('account.move', 'read'), ('account.move.line', 'unlink'), ('account.move', 'write'), ('account.move.line', 'write'), ('res.currency', 'read'), ('account.move.line', 'create'), ('res.currency.rate', 'read')}
_GROUPS['invoice.currency_rate.update'] = 'account.group_account_invoice'
_MODELS['invoice.currency_rate.update'] = {'account.move', 'res.company', 'res.currency', 'res.currency.rate', 'account.move.line'}
_ACCESS['invoice.currency_rate.update'] = {('account.move.line', 'read'), ('account.move', 'read'), ('account.move.line', 'unlink'), ('account.move', 'write'), ('account.move.line', 'write'), ('res.currency', 'read'), ('account.move.line', 'create'), ('res.currency.rate', 'read')}
_GROUPS['invoice.incoterm.update'] = 'account.group_account_invoice'
_MODELS['invoice.incoterm.update'] = {'account.incoterms', 'account.move', 'account.move.line', 'res.company'}
_ACCESS['invoice.incoterm.update'] = {('account.move.line', 'read'), ('account.move', 'read'), ('account.incoterms', 'read'), ('account.move', 'write')}
_GROUPS['invoice.payment_block.set'] = 'account.group_account_invoice'
_MODELS['invoice.payment_block.set'] = {'account.move', 'account.move.line', 'res.company'}
_ACCESS['invoice.payment_block.set'] = {('account.move.line', 'read'), ('account.move', 'read'), ('account.move', 'write')}
_GROUPS['invoice.payment_method.assign'] = 'account.group_account_invoice'
_MODELS['invoice.payment_method.assign'] = {'account.move', 'account.payment.method.line', 'account.journal', 'res.company', 'account.move.line'}
_ACCESS['invoice.payment_method.assign'] = {('account.move.line', 'read'), ('account.move', 'read'), ('account.journal', 'read'), ('account.payment.method.line', 'read'), ('account.move', 'write')}
_PARAMETER_KEYS.update(partner_preferences.PARAMETER_KEYS)
_GROUPS['partner.bill_validation_preferences.update'] = "account.group_account_user"
_MODELS['partner.bill_validation_preferences.update'] = {'res.company', 'res.partner'}
_ACCESS['partner.bill_validation_preferences.update'] = {('res.partner', 'read'), ('res.partner', 'write')}
_GROUPS['partner.credit_limit.reset'] = "account.group_account_user"
_MODELS['partner.credit_limit.reset'] = {'res.company', 'res.partner'}
_ACCESS['partner.credit_limit.reset'] = {('res.partner', 'read'), ('res.partner', 'write')}
_GROUPS['partner.credit_limit.update'] = "account.group_account_user"
_MODELS['partner.credit_limit.update'] = {'res.company', 'res.partner'}
_ACCESS['partner.credit_limit.update'] = {('res.partner', 'read'), ('res.partner', 'write')}
_GROUPS['partner.invoice_delivery_preferences.update'] = "account.group_account_user"
_MODELS['partner.invoice_delivery_preferences.update'] = {'res.company', 'res.partner', 'account.move', 'ir.actions.report'}
_ACCESS['partner.invoice_delivery_preferences.update'] = {('res.partner', 'read'), ('account.move', 'read'), ('ir.actions.report', 'read'), ('res.partner', 'write')}
_GROUPS['partner.payment_preferences.update'] = "account.group_account_user"
_MODELS['partner.payment_preferences.update'] = {'res.company', 'res.partner', 'account.payment.method.line', 'account.journal'}
_ACCESS['partner.payment_preferences.update'] = {('res.partner', 'read'), ('account.payment.method.line', 'read'), ('account.journal', 'read'), ('res.partner', 'write')}
_PARAMETER_KEYS.update(payment_configuration.PARAMETER_KEYS)
_GROUPS['journal.bank_account.assign'] = "account.group_account_manager"
_MODELS['journal.bank_account.assign'] = {'res.company', 'account.journal', 'res.partner.bank'}
_ACCESS['journal.bank_account.assign'] = {('account.journal', 'read'), ('res.partner.bank', 'read'), ('account.journal', 'write')}
_GROUPS['journal.liquidity_configuration.update'] = "account.group_account_manager"
_MODELS['journal.liquidity_configuration.update'] = {'res.company', 'account.journal', 'account.account'}
_ACCESS['journal.liquidity_configuration.update'] = {('account.journal', 'read'), ('account.account', 'read'), ('account.journal', 'write')}
_GROUPS['payment.method_line.create'] = "account.group_account_manager"
_MODELS['payment.method_line.create'] = {'account.account', 'account.payment.method.line', 'res.company', 'account.journal', 'account.payment.method'}
_ACCESS['payment.method_line.create'] = {('account.payment.method.line', 'read'), ('account.payment.method', 'read'), ('account.account', 'write'), ('account.journal', 'read'), ('account.account', 'read'), ('account.payment.method.line', 'create')}
_GROUPS['payment.method_line.duplicate'] = "account.group_account_manager"
_MODELS['payment.method_line.duplicate'] = {'account.account', 'account.payment.method.line', 'res.company', 'account.journal', 'account.payment.method'}
_ACCESS['payment.method_line.duplicate'] = {('account.payment.method.line', 'read'), ('account.payment.method', 'read'), ('account.account', 'write'), ('account.journal', 'read'), ('account.account', 'read'), ('account.payment.method.line', 'create')}
_GROUPS['payment.method_line.remove'] = "account.group_account_manager"
_MODELS['payment.method_line.remove'] = {'account.account', 'account.payment.method.line', 'res.company', 'account.journal', 'account.payment.method'}
_ACCESS['payment.method_line.remove'] = {('account.payment.method.line', 'unlink'), ('account.payment.method.line', 'write'), ('account.payment.method.line', 'read'), ('account.payment.method', 'read'), ('account.journal', 'read'), ('account.account', 'read')}
_GROUPS['payment.method_line.update'] = "account.group_account_manager"
_MODELS['payment.method_line.update'] = {'account.account', 'account.payment.method.line', 'res.company', 'account.journal', 'account.payment.method'}
_ACCESS['payment.method_line.update'] = {('account.payment.method.line', 'write'), ('account.payment.method.line', 'read'), ('account.payment.method', 'read'), ('account.account', 'write'), ('account.journal', 'read'), ('account.account', 'read')}
_PARAMETER_KEYS.update(fiscal_mappings.PARAMETER_KEYS)
_GROUPS["fiscal_position.taxes.replace"] = "account.group_account_manager"
_MODELS["fiscal_position.taxes.replace"] = {"account.fiscal.position","account.fiscal.position.account","account.tax","res.company"}
_ACCESS["fiscal_position.taxes.replace"] = {("account.fiscal.position.account", "read"), ("account.fiscal.position", "read"), ("account.fiscal.position", "write"), ("account.tax", "read")}
_GROUPS["tax.original_taxes.replace"] = "account.group_account_manager"
_MODELS["tax.original_taxes.replace"] = {"account.fiscal.position","account.tax","res.company"}
_ACCESS["tax.original_taxes.replace"] = {("account.fiscal.position", "read"), ("account.tax", "read"), ("account.tax", "write")}
_GROUPS["fiscal_position.account_mapping.create"] = "account.group_account_manager"
_MODELS["fiscal_position.account_mapping.create"] = {"account.account","account.fiscal.position","account.fiscal.position.account","res.company"}
_ACCESS["fiscal_position.account_mapping.create"] = {("account.account", "read"), ("account.fiscal.position.account", "create"), ("account.fiscal.position.account", "read"), ("account.fiscal.position", "read")}
_GROUPS["fiscal_position.account_mapping.update"] = "account.group_account_manager"
_MODELS["fiscal_position.account_mapping.update"] = {"account.account","account.fiscal.position","account.fiscal.position.account","res.company"}
_ACCESS["fiscal_position.account_mapping.update"] = {("account.account", "read"), ("account.fiscal.position.account", "read"), ("account.fiscal.position.account", "write"), ("account.fiscal.position", "read")}
_GROUPS["fiscal_position.account_mapping.delete"] = "account.group_account_manager"
_MODELS["fiscal_position.account_mapping.delete"] = {"account.account","account.fiscal.position","account.fiscal.position.account","res.company"}
_ACCESS["fiscal_position.account_mapping.delete"] = {("account.account", "read"), ("account.fiscal.position.account", "read"), ("account.fiscal.position.account", "unlink"), ("account.fiscal.position", "read")}
_GROUPS["fiscal_position.duplicate"] = "account.group_account_manager"
_MODELS["fiscal_position.duplicate"] = {"account.account","account.fiscal.position","account.fiscal.position.account","account.tax","res.company"}
_ACCESS["fiscal_position.duplicate"] = {("account.account", "read"), ("account.fiscal.position.account", "create"), ("account.fiscal.position.account", "read"), ("account.fiscal.position", "create"), ("account.fiscal.position", "read"), ("account.tax", "read")}
_GROUPS["fiscal_position.delete"] = "account.group_account_manager"
_MODELS["fiscal_position.delete"] = {"account.fiscal.position","account.fiscal.position.account","res.company"}
_ACCESS["fiscal_position.delete"] = {("account.fiscal.position.account", "read"), ("account.fiscal.position.account", "unlink"), ("account.fiscal.position", "read"), ("account.fiscal.position", "unlink")}
_GROUPS["tax.duplicate"] = "account.group_account_manager"
_MODELS["tax.duplicate"] = {"account.tax","account.tax.repartition.line","res.company"}
_ACCESS["tax.duplicate"] = {("account.tax.repartition.line", "create"), ("account.tax.repartition.line", "read"), ("account.tax", "create"), ("account.tax", "read")}
_PARAMETER_KEYS.update(report_budgets.PARAMETER_KEYS)
for _report_budget_capability in report_budgets.CAPABILITY_IDS:
    _GROUPS[_report_budget_capability] = "account.group_account_manager"
    _MODELS[_report_budget_capability] = {
        "res.company", "account.report.budget", "account.report.budget.item"
    }
    _ACCESS[_report_budget_capability] = {
        ("account.report.budget", "read"), ("account.report.budget.item", "read")
    }
    if _report_budget_capability in {
        "report.budget_definition.create", "report.budget_definition.duplicate"
    }:
        _ACCESS[_report_budget_capability].add(("account.report.budget", "create"))
    if _report_budget_capability in {
        "report.budget_definition.update", "report.budget_definition.duplicate",
        "report.budget_account_period.set_total",
    }:
        _ACCESS[_report_budget_capability].add(("account.report.budget", "write"))
    if _report_budget_capability == "report.budget_definition.delete":
        _ACCESS[_report_budget_capability].update({
            ("account.report.budget", "unlink"), ("account.report.budget.item", "unlink")
        })
    if _report_budget_capability in {
        "report.budget_definition.duplicate", "report.budget_item.create",
        "report.budget_account_period.set_total",
    }:
        _ACCESS[_report_budget_capability].add(("account.report.budget.item", "create"))
    if _report_budget_capability in {
        "report.budget_item.update", "report.budget_account_period.set_total"
    }:
        _ACCESS[_report_budget_capability].add(("account.report.budget.item", "write"))
    if _report_budget_capability == "report.budget_item.delete":
        _ACCESS[_report_budget_capability].add(("account.report.budget.item", "unlink"))
    if _report_budget_capability in {
        "report.budget_definition.duplicate", "report.budget_item.create",
        "report.budget_item.update", "report.budget_account_period.set_total",
    }:
        _MODELS[_report_budget_capability].add("account.account")
        _ACCESS[_report_budget_capability].add(("account.account", "read"))


def _is_id(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _valid_batch_ids(value: Any) -> bool:
    return (
        isinstance(value, list)
        and 2 <= len(value) <= 100
        and all(_is_id(item) for item in value)
        and value == sorted(set(value))
    )


def _valid_round_ids(value: Any, *, minimum: int) -> bool:
    return isinstance(value, list) and minimum <= len(value) <= 100 and all(
        _is_id(item) for item in value
    ) and value == sorted(set(value))


def _payment_round_operation(parameters: dict[str, Any]) -> bool:
    return bool(_PAYMENT_INSTALLMENT_FIELDS & set(parameters)) or (
        "move_ids" in parameters and bool({"amount", "payment_difference_handling", "writeoff_account_id", "writeoff_label"} & set(parameters))
    )


def _valid_payment_installments(parameters: dict[str, Any]) -> bool:
    mode = parameters.get("installments_mode")
    return bool(
        ("installments_mode" not in parameters or isinstance(mode, str) and mode in {"full", "next", "overdue", "before_date"})
        and ("group_payment" not in parameters or isinstance(parameters["group_payment"], bool))
        and not (parameters.get("group_payment") is False and "amount" in parameters)
        and ((mode == "before_date" and _is_date(parameters.get("installment_cutoff_date")))
             or (mode != "before_date" and "installment_cutoff_date" not in parameters))
    )


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


def _decimal(value: Any, *, positive: bool = False) -> Decimal | None:
    if (
        not isinstance(value, str)
        or len(value) > 256
        or not _DECIMAL_PATTERN.fullmatch(value)
    ):
        return None
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        return None
    if not parsed.is_finite() or parsed < 0 or (positive and parsed <= 0):
        return None
    return parsed


def _signed_decimal(value: Any) -> Decimal | None:
    if (
        not isinstance(value, str)
        or len(value) > 256
        or not _SIGNED_DECIMAL_PATTERN.fullmatch(value)
    ):
        return None
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        return None
    return parsed if parsed.is_finite() else None


def _is_text(value: Any, *, maximum: int = 500) -> bool:
    return (
        isinstance(value, str) and value == value.strip() and 1 <= len(value) <= maximum
    )


def _valid_analytic_distribution(value: Any) -> bool:
    if value is None:
        return True
    if not isinstance(value, dict) or not 1 <= len(value) <= 16:
        return False
    seen_ids: set[int] = set()
    for key, percentage_text in value.items():
        if not isinstance(key, str):
            return False
        parts = key.split(",")
        if any(not part.isascii() or not part.isdigit() for part in parts):
            return False
        account_ids = [int(part) for part in parts]
        if (
            any(not _is_id(account_id) for account_id in account_ids)
            or account_ids != sorted(set(account_ids))
            or seen_ids.intersection(account_ids)
        ):
            return False
        percentage = _decimal(percentage_text, positive=True)
        if (
            percentage is None
            or _canonical_decimal_text(percentage) != percentage_text
            or percentage > Decimal(100)
            or max(0, -percentage.as_tuple().exponent) > 4
        ):
            return False
        seen_ids.update(account_ids)
    return True


def _analytic_account_ids(lines: list[dict[str, Any]]) -> set[int]:
    return {
        int(account_id)
        for line in lines
        for key in (line.get("analytic_distribution") or {})
        for account_id in key.split(",")
    }


def _odoo_analytic_distribution(value: Any) -> dict[str, float] | bool:
    if not value:
        return False
    return {key: float(Decimal(percentage)) for key, percentage in value.items()}


def _normalized_analytic_distribution(value: Any) -> dict[str, str]:
    if not value:
        return {}
    return {
        str(key): _canonical_decimal_text(percentage)
        for key, percentage in sorted(value.items())
    }


def _valid_deferred_line_dates(line: dict[str, Any]) -> bool:
    has_start, has_end = (field in line for field in _DEFERRED_LINE_DATE_FIELDS)
    if has_start != has_end:
        return False
    if not has_start:
        return True
    start, end = (line[field] for field in _DEFERRED_LINE_DATE_FIELDS)
    return (start is None and end is None) or (
        _is_date(start) and _is_date(end) and start <= end
    )


def _valid_document_lines(value: Any) -> bool:
    if not isinstance(value, list) or not 1 <= len(value) <= 200:
        return False
    for line in value:
        if (
            not isinstance(line, dict)
            or not _DOCUMENT_LINE_REQUIRED_KEYS
            <= set(line)
            <= _DOCUMENT_LINE_REQUIRED_KEYS | _DOCUMENT_LINE_OPTIONAL_KEYS
        ):
            return False
        tax_ids = line["tax_ids"]
        discount = _decimal(line.get("discount", "0"))
        if (
            not _is_text(line["name"])
            or not _is_id(line["account_id"])
            or _signed_decimal(line["quantity"]) in {None, Decimal(0)}
            or _signed_decimal(line["price_unit"]) is None
            or (
                "product_id" in line
                and line["product_id"] is not None
                and not _is_id(line["product_id"])
            )
            or discount is None
            or discount > Decimal(100)
            or (
                "analytic_distribution" in line
                and not _valid_analytic_distribution(line["analytic_distribution"])
            )
            or not isinstance(tax_ids, list)
            or any(not _is_id(item) for item in tax_ids)
            or len(tax_ids) != len(set(tax_ids))
            or not _valid_deferred_line_dates(line)
            or not _valid_invoice_line_inputs(line, partial=False)
        ):
            return False
    return True


def _valid_invoice_line_inputs(values: dict[str, Any], *, partial: bool) -> bool:
    if "product_uom_id" in values and (
        not _is_id(values["product_uom_id"])
        or ((not partial or "product_id" in values) and not _is_id(values.get("product_id")))
    ):
        return False
    if "deductible_amount" in values:
        amount = _decimal(values["deductible_amount"])
        if amount is None or amount > 100:
            return False
    return True


def _valid_entry_lines(value: Any, *, minimum: int = 2) -> bool:
    if not isinstance(value, list) or not minimum <= len(value) <= 500:
        return False
    debit_total = Decimal(0)
    credit_total = Decimal(0)
    for line in value:
        if (
            not isinstance(line, dict)
            or not _ENTRY_LINE_REQUIRED_KEYS
            <= set(line)
            <= _ENTRY_LINE_REQUIRED_KEYS | _ENTRY_LINE_OPTIONAL_KEYS
        ):
            return False
        debit = _decimal(line["debit"])
        credit = _decimal(line["credit"])
        if (
            not _is_text(line["name"])
            or not _is_id(line["account_id"])
            or (line["partner_id"] is not None and not _is_id(line["partner_id"]))
            or debit is None
            or credit is None
            or (debit > 0) == (credit > 0)
            or ("currency_id" in line) != ("amount_currency" in line)
            or (
                "date_maturity" in line
                and line["date_maturity"] is not None
                and not _is_date(line["date_maturity"])
            )
            or (
                "analytic_distribution" in line
                and not _valid_analytic_distribution(line["analytic_distribution"])
            )
        ):
            return False
        if "currency_id" in line:
            currency_id = line["currency_id"]
            amount_currency_value = line["amount_currency"]
            if (currency_id is None) != (amount_currency_value is None):
                return False
            if currency_id is not None:
                amount_currency = _signed_decimal(amount_currency_value)
                if (
                    not _is_id(currency_id)
                    or amount_currency in {None, Decimal(0)}
                    or (amount_currency > 0) != (debit > credit)
                ):
                    return False
        for field in ("tax_ids", "tax_tag_ids"):
            if field in line and not (
                isinstance(line[field], list)
                and len(line[field]) <= 100
                and all(_is_id(item) for item in line[field])
                and line[field] == sorted(set(line[field]))
            ):
                return False
        if "tax_repartition_line_id" in line and not (
            line["tax_repartition_line_id"] is None
            or _is_id(line["tax_repartition_line_id"])
        ):
            return False
        if "tax_base_amount" in line and _signed_decimal(line["tax_base_amount"]) is None:
            return False
        debit_total += debit
        credit_total += credit
    return debit_total > 0 and debit_total == credit_total


def _valid_nullable_text(value: Any, *, maximum: int = 200) -> bool:
    return value is None or (isinstance(value, str) and 1 <= len(value) <= maximum)


def _valid_invoice_changes(value: Any) -> bool:
    if (
        not isinstance(value, dict)
        or not value
        or not set(value) <= _INVOICE_UPDATE_KEYS
        or {"invoice_date_due", "payment_term_id"} <= set(value)
    ):
        return False
    for field_name, field_value in value.items():
        if field_name in {"partner_id", "journal_id", "currency_id"} and not _is_id(
            field_value
        ):
            return False
        if field_name in {"date", "invoice_date"} and not _is_date(field_value):
            return False
        if field_name == "invoice_date_due" and not (
            field_value is None or _is_date(field_value)
        ):
            return False
        if field_name in {
            "payment_term_id", "partner_bank_id", "fiscal_position_id"
        } and not (field_value is None or _is_id(field_value)):
            return False
        if field_name in {"reference", "payment_reference"} and not (
            _valid_nullable_text(field_value)
        ):
            return False
    return True


def _valid_journal_entry_changes(value: Any) -> bool:
    if (
        not isinstance(value, dict)
        or not value
        or not set(value) <= _JOURNAL_ENTRY_UPDATE_KEYS
    ):
        return False
    for field_name, field_value in value.items():
        if field_name == "date" and not _is_date(field_value):
            return False
        if field_name == "journal_id" and not _is_id(field_value):
            return False
        if field_name == "reference" and not _valid_nullable_text(field_value):
            return False
    return True


def _valid_invoice_line_values(value: Any, *, partial: bool) -> bool:
    required = {
        "name",
        "product_id",
        "account_id",
        "quantity",
        "price_unit",
        "discount",
        "tax_ids",
    }
    allowed = required | {"analytic_distribution", *_DEFERRED_LINE_DATE_FIELDS} | _INVOICE_LINE_INPUT_FIELDS
    if (
        not isinstance(value, dict)
        or (partial and (not value or not set(value) <= allowed))
        or (not partial and not required <= set(value) <= allowed)
    ):
        return False
    if "name" in value and not _is_text(value["name"]):
        return False
    if "product_id" in value and value["product_id"] is not None and not _is_id(
        value["product_id"]
    ):
        return False
    if "account_id" in value and not _is_id(value["account_id"]):
        return False
    if "quantity" in value and _signed_decimal(value["quantity"]) is None:
        return False
    if "price_unit" in value and _signed_decimal(value["price_unit"]) is None:
        return False
    if "discount" in value:
        discount = _decimal(value["discount"])
        if discount is None or discount > Decimal(100):
            return False
    if "tax_ids" in value:
        tax_ids = value["tax_ids"]
        if (
            not isinstance(tax_ids, list)
            or any(not _is_id(item) for item in tax_ids)
            or tax_ids != sorted(set(tax_ids))
        ):
            return False
    return bool(
        _valid_deferred_line_dates(value)
        and _valid_invoice_line_inputs(value, partial=partial)
        and (
            "analytic_distribution" not in value
            or _valid_analytic_distribution(value["analytic_distribution"])
        )
    )


def _valid_replacement_invoice_lines(value: Any) -> bool:
    if not isinstance(value, list) or not 1 <= len(value) <= 500:
        return False
    for line in value:
        if not _valid_invoice_line_values(line, partial=False):
            return False
    return True


def _canonical_decimal_text(value: Any) -> str:
    parsed = Decimal(str(value))
    if not parsed:
        return "0"
    text = format(parsed, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def _normalized_invoice_replacement_lines(
    lines: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "name": line["name"],
            "product_id": line["product_id"],
            "account_id": line["account_id"],
            "quantity": _canonical_decimal_text(line["quantity"]),
            "price_unit": _canonical_decimal_text(line["price_unit"]),
            "discount": _canonical_decimal_text(line["discount"]),
            "tax_ids": list(line["tax_ids"]),
            "analytic_distribution": _normalized_analytic_distribution(
                line.get("analytic_distribution")
            ),
            **{field: line.get(field) for field in _DEFERRED_LINE_DATE_FIELDS},
            **{
                field: _canonical_decimal_text(line[field]) if field == "deductible_amount" else line[field]
                for field in _INVOICE_LINE_INPUT_FIELDS if field in line
            },
        }
        for line in lines
    ]


def _invoice_lines_match(
    current: list[dict[str, Any]] | None, lines: list[dict[str, Any]]
) -> bool:
    expected = _normalized_invoice_replacement_lines(lines)
    if current is None or len(current) != len(expected):
        return False
    for actual, target, requested in zip(current, expected, lines, strict=True):
        for field in _DEFERRED_LINE_DATE_FIELDS:
            if field not in requested:
                # Legacy requests did not compare or explicitly clear these dates.
                target[field] = actual[field]
    return current == expected


def _normalized_entry_replacement_lines(
    lines: list[dict[str, Any]],
    company_currency_id: int,
) -> list[dict[str, Any]]:
    return [
        {
            "name": line["name"],
            "account_id": line["account_id"],
            "partner_id": line["partner_id"],
            "date_maturity": line.get("date_maturity"),
            "debit": _canonical_decimal_text(line["debit"]),
            "credit": _canonical_decimal_text(line["credit"]),
            "currency_id": line.get("currency_id") or company_currency_id,
            "amount_currency": (
                _canonical_decimal_text(
                    line["amount_currency"]
                    if line.get("amount_currency") is not None
                    else Decimal(line["debit"]) - Decimal(line["credit"])
                )
            ),
            "analytic_distribution": _normalized_analytic_distribution(
                line.get("analytic_distribution")
            ),
            "tax_ids": list(line.get("tax_ids", [])),
            "tax_tag_ids": list(line.get("tax_tag_ids", [])),
            "tax_repartition_line_id": line.get("tax_repartition_line_id"),
            "tax_base_amount": _canonical_decimal_text(line.get("tax_base_amount", "0")),
        }
        for line in lines
    ]


def _entry_lines_match(
    current: list[dict[str, Any]] | None,
    lines: list[dict[str, Any]],
    company_currency_id: int,
) -> bool:
    expected = _normalized_entry_replacement_lines(lines, company_currency_id)
    if current is None or len(current) != len(expected):
        return False
    current = [dict(item) for item in current]
    for actual, target, requested in zip(current, expected, lines, strict=True):
        if "date_maturity" not in requested:
            # An omitted date must not make an otherwise unchanged replay rewrite lines.
            target["date_maturity"] = actual["date_maturity"]
        for field in _ENTRY_TAX_FIELDS - set(requested):
            actual.pop(field, None)
            target.pop(field, None)
    return current == expected


def _valid_asset_create_parameters(parameters: dict[str, Any]) -> bool:
    original_value = _decimal(parameters["original_value"], positive=True)
    salvage_value = _decimal(parameters["salvage_value"])
    progress_factor = _decimal(parameters["method_progress_factor"], positive=True)
    return bool(
        _is_text(parameters["name"], maximum=_ASSET_BASE_NAME_MAXIMUM)
        and "[ODACV4:" not in parameters["name"]
        and _is_date(parameters["acquisition_date"])
        and original_value is not None
        and salvage_value is not None
        and salvage_value <= original_value
        and all(
            _is_id(parameters[key])
            for key in (
                "account_asset_id",
                "account_depreciation_id",
                "account_depreciation_expense_id",
                "journal_id",
            )
        )
        and parameters["method"] in _ASSET_METHODS
        and isinstance(parameters["method_number"], int)
        and not isinstance(parameters["method_number"], bool)
        and 1 <= parameters["method_number"] <= 1200
        and parameters["method_period"] in {"1", "12"}
        and progress_factor is not None
        and progress_factor <= Decimal(1)
        and parameters["prorata_computation_type"] in _ASSET_PRORATA_TYPES
    )


def _is_month_end(value: str) -> bool:
    parsed = date.fromisoformat(value)
    return parsed.day == calendar.monthrange(parsed.year, parsed.month)[1]


def _valid_payment_fields(values: Any, *, partial: bool) -> bool:
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
    if not isinstance(values, dict):
        return False
    if partial:
        if not values or not set(values) <= fields:
            return False
    elif not (required <= set(values) <= fields):
        return False
    if "payment_type" in values and values["payment_type"] not in {
        "inbound",
        "outbound",
    }:
        return False
    if "partner_type" in values and values["partner_type"] not in {
        "customer",
        "supplier",
    }:
        return False
    for field_name in (
        "partner_id",
        "currency_id",
        "journal_id",
        "payment_method_line_id",
    ):
        if field_name in values and not _is_id(values[field_name]):
            return False
    if "amount" in values and _decimal(values["amount"], positive=True) is None:
        return False
    if "date" in values and not _is_date(values["date"]):
        return False
    return "payment_reference" not in values or (
        values["payment_reference"] is None
        or _is_text(values["payment_reference"], maximum=200)
    )


def _valid_bank_foreign_pair(values: dict[str, Any]) -> bool:
    present = {"foreign_currency_id", "amount_currency"} & set(values)
    if not present:
        return True
    if present != {"foreign_currency_id", "amount_currency"}:
        return False
    currency_id, amount_text = values["foreign_currency_id"], values["amount_currency"]
    amount = _signed_decimal(amount_text)
    if amount is None or _canonical_decimal_text(amount) != amount_text:
        return False
    if currency_id is None:
        return amount_text == "0"
    if not _is_id(currency_id) or amount == 0:
        return False
    if "amount" in values:
        transaction_amount = _signed_decimal(values["amount"])
        return transaction_amount is not None and (transaction_amount > 0) == (amount > 0)
    return True


def _valid_bank_update_changes(changes: Any) -> bool:
    if (
        not isinstance(changes, dict)
        or not changes
        or not set(changes) <= {"date", "amount", "payment_ref", "partner_id", "foreign_currency_id", "amount_currency", "account_number", "partner_name"}
    ):
        return False
    if "date" in changes and not _is_date(changes["date"]):
        return False
    if "amount" in changes:
        amount = _signed_decimal(changes["amount"])
        if amount is None or amount == 0:
            return False
    if "payment_ref" in changes and not _is_text(changes["payment_ref"], maximum=200):
        return False
    if any(field in changes and changes[field] is not None
           and not _is_text(changes[field], maximum=200)
           for field in ("account_number", "partner_name")):
        return False
    return _valid_bank_foreign_pair(changes) and (
        "partner_id" not in changes or changes["partner_id"] is None
        or _is_id(changes["partner_id"])
    )


def _valid_statement_values(values: Any, *, partial: bool) -> bool:
    fields = {"reference", "balance_end_real"}
    if not isinstance(values, dict):
        return False
    if partial:
        if not values or not set(values) <= fields | {"transaction_ids", "balance_start", "name", "date"}:
            return False
    elif not fields <= set(values) <= fields | {"balance_start", "name", "date"}:
        return False
    if "name" in values and not _is_text(values["name"], maximum=200):
        return False
    if "date" in values and not _is_date(values["date"]):
        return False
    if "reference" in values and not (
        values["reference"] is None
        or _is_text(values["reference"], maximum=200)
    ):
        return False
    for field in ("balance_end_real", "balance_start"):
        if field not in values:
            continue
        balance = _signed_decimal(values[field])
        if (
            balance is None
            or _canonical_decimal_text(balance) != values[field]
        ):
            return False
    if "transaction_ids" in values:
        ids = values["transaction_ids"]
        if (not isinstance(ids, list) or not 1 <= len(ids) <= 100
            or not all(_is_id(record_id) for record_id in ids)
            or ids != sorted(set(ids))):
            return False
    return True


def _valid_analytic_account_changes(changes: Any) -> bool:
    if (
        not isinstance(changes, dict)
        or not changes
        or not set(changes) <= _ANALYTIC_ACCOUNT_UPDATE_KEYS
    ):
        return False
    if "name" in changes and (
        not _is_text(changes["name"], maximum=200) or "[ODACV4:" in changes["name"]
    ):
        return False
    if "code" in changes and not (
        changes["code"] is None or _is_text(changes["code"], maximum=200)
    ):
        return False
    if "partner_id" in changes and not (
        changes["partner_id"] is None or _is_id(changes["partner_id"])
    ):
        return False
    return "active" not in changes or isinstance(changes["active"], bool)


def _valid_analytic_plan_values(values: Any, *, partial: bool) -> bool:
    if (
        not isinstance(values, dict)
        or (partial and not values)
        or not set(values) <= _ANALYTIC_PLAN_UPDATE_KEYS
    ):
        return False
    if "name" in values and (
        not _is_text(values["name"], maximum=200)
        or "[ODACV4:" in values["name"]
    ):
        return False
    if "color" in values:
        color = values["color"]
        if color is None:
            if partial:
                return False
        elif (
            not isinstance(color, int)
            or isinstance(color, bool)
            or color < 0
        ):
            return False
    if "default_applicability" in values:
        applicability = values["default_applicability"]
        if applicability is None:
            return not partial
        return applicability in _ANALYTIC_APPLICABILITIES
    return True


def _valid_analytic_line_values(values: Any, *, partial: bool) -> bool:
    if (
        not isinstance(values, dict)
        or (partial and not values)
        or not set(values) <= _ANALYTIC_LINE_UPDATE_KEYS
    ):
        return False
    if "name" in values and (
        not _is_text(values["name"], maximum=200)
        or "[ODACV4:" in values["name"]
    ):
        return False
    if "date" in values and not _is_date(values["date"]):
        return False
    for field_name in ("amount", "unit_amount"):
        if field_name in values:
            parsed = _signed_decimal(values[field_name])
            if (
                parsed is None
                or _canonical_decimal_text(parsed) != values[field_name]
            ):
                return False
    if "analytic_account_id" in values and not _is_id(
        values["analytic_account_id"]
    ):
        return False
    return (
        "reference" not in values
        or values["reference"] is None
        or _is_text(values["reference"], maximum=200)
    )


def _valid_budget_changes(changes: Any) -> bool:
    if (
        not isinstance(changes, dict)
        or not changes
        or not set(changes) <= _BUDGET_UPDATE_KEYS
    ):
        return False
    if "name" in changes and (
        not _is_text(changes["name"], maximum=200) or "[ODACV4:" in changes["name"]
    ):
        return False
    if "date_from" in changes and not _is_date(changes["date_from"]):
        return False
    if "date_to" in changes and not _is_date(changes["date_to"]):
        return False
    if (
        "date_from" in changes
        and "date_to" in changes
        and changes["date_from"] > changes["date_to"]
    ):
        return False
    return "budget_type" not in changes or changes["budget_type"] in _BUDGET_TYPES


def _valid_budget_lines(lines: Any) -> bool:
    if not isinstance(lines, list) or not 1 <= len(lines) <= 200:
        return False
    for line in lines:
        if not isinstance(line, dict) or set(line) != {
            "budget_amount",
            "analytic_account_ids",
        }:
            return False
        account_ids = line["analytic_account_ids"]
        if (
            _signed_decimal(line["budget_amount"]) is None
            or not isinstance(account_ids, list)
            or not 1 <= len(account_ids) <= 16
            or account_ids != sorted(set(account_ids))
            or any(not _is_id(account_id) for account_id in account_ids)
        ):
            return False
    return True


def _valid_partner_contact_values(values: Any, *, partial: bool) -> bool:
    if not isinstance(values, dict):
        return False
    if partial:
        if not values or not set(values) <= _PARTNER_CONTACT_KEYS:
            return False
    elif set(values) != _PARTNER_CONTACT_KEYS:
        return False
    if "name" in values and (
        not _is_text(values["name"], maximum=256) or "[ODACV4:" in values["name"]
    ):
        return False
    if "company_type" in values:
        company_type = values["company_type"]
        if not isinstance(company_type, str) or company_type not in {
            "person",
            "company",
        }:
            return False
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
    for field_name, maximum in text_limits.items():
        if field_name not in values:
            continue
        value = values[field_name]
        if value is not None and not _is_text(value, maximum=maximum):
            return False
    if (
        "reference" in values
        and isinstance(values["reference"], str)
        and ("[ODACV4:" in values["reference"])
    ):
        return False
    for field_name in ("state_id", "country_id"):
        if (
            field_name in values
            and values[field_name] is not None
            and not _is_id(values[field_name])
        ):
            return False
    return not (
        "language" in values
        and values["language"] is not None
        and not _is_text(values["language"], maximum=16)
    )


def _valid_partner_accounting_changes(changes: Any) -> bool:
    return bool(
        isinstance(changes, dict)
        and changes
        and set(changes) <= _PARTNER_ACCOUNTING_KEYS
        and all(value is None or _is_id(value) for value in changes.values())
    )


def _valid_partner_bank_values(values: Any, *, partial: bool) -> bool:
    if not isinstance(values, dict):
        return False
    if partial:
        if not values or not set(values) <= _PARTNER_BANK_KEYS:
            return False
    elif set(values) != _PARTNER_BANK_KEYS:
        return False
    if "account_number" in values:
        account_number = values["account_number"]
        if not _is_text(account_number, maximum=128) or "[ODACV4:" in account_number:
            return False
    if "account_holder_name" in values:
        holder = values["account_holder_name"]
        if holder is not None and (
            not _is_text(holder, maximum=256) or "[ODACV4:" in holder
        ):
            return False
    return all(
        field_name not in values
        or values[field_name] is None
        or _is_id(values[field_name])
        for field_name in ("bank_id", "currency_id")
    )


def _valid_sequence(value: Any, *, allow_none: bool) -> bool:
    return (allow_none and value is None) or (
        isinstance(value, int) and not isinstance(value, bool) and value >= 0
    )


def _valid_account_config_values(values: Any, *, partial: bool) -> bool:
    if not isinstance(values, dict):
        return False
    if partial:
        if not values or not set(values) <= _ACCOUNT_CONFIG_KEYS:
            return False
    elif set(values) != _ACCOUNT_CONFIG_KEYS:
        return False
    if "code" in values and not _is_text(values["code"], maximum=64):
        return False
    if "name" in values and not _is_text(values["name"], maximum=256):
        return False
    if "account_type" in values and values["account_type"] not in _ACCOUNT_TYPES:
        return False
    if "reconcile" in values and not isinstance(values["reconcile"], bool):
        return False
    return "currency_id" not in values or (
        values["currency_id"] is None or _is_id(values["currency_id"])
    )


def _valid_journal_values(values: Any, *, partial: bool) -> bool:
    allowed = _JOURNAL_UPDATE_KEYS if partial else _JOURNAL_CREATE_KEYS
    if not isinstance(values, dict):
        return False
    if partial:
        if not values or not set(values) <= allowed:
            return False
    elif set(values) != allowed:
        return False
    if "name" in values and not _is_text(values["name"], maximum=256):
        return False
    if "code" in values:
        code = values["code"]
        if not _is_text(code, maximum=5) or code != code.upper():
            return False
    if "type" in values and values["type"] not in _JOURNAL_TYPES:
        return False
    if "sequence" in values and not _valid_sequence(
        values["sequence"], allow_none=not partial
    ):
        return False
    return all(
        field_name not in values
        or values[field_name] is None
        or _is_id(values[field_name])
        for field_name in ("currency_id", "default_account_id")
    )


def _valid_tax_values(values: Any, *, partial: bool) -> bool:
    if not isinstance(values, dict):
        return False
    if partial:
        if not values or not set(values) <= _TAX_CONFIG_KEYS:
            return False
    elif not _TAX_CONFIG_REQUIRED_KEYS <= set(values) <= _TAX_CONFIG_KEYS:
        return False
    if "name" in values and not _is_text(values["name"], maximum=256):
        return False
    if "type_tax_use" in values and values["type_tax_use"] not in _TAX_USE_TYPES:
        return False
    if "amount_type" in values and values["amount_type"] not in _TAX_AMOUNT_TYPES:
        return False
    if "amount" in values:
        amount = values["amount"]
        if _signed_decimal(amount) is None or _canonical_decimal_text(amount) != amount:
            return False
    if "sequence" in values and not _valid_sequence(
        values["sequence"], allow_none=not partial
    ):
        return False
    if "tax_group_id" in values and not (
        values["tax_group_id"] is None or _is_id(values["tax_group_id"])
    ):
        return False
    if "invoice_label" in values and not (
        values["invoice_label"] is None
        or _is_text(values["invoice_label"], maximum=256)
    ):
        return False
    if "price_include_override" in values and not (
        values["price_include_override"] is None
        or values["price_include_override"] in _TAX_PRICE_INCLUDE_OVERRIDES
    ):
        return False
    if "children_tax_ids" in values:
        children = values["children_tax_ids"]
        if (not isinstance(children, list) or len(children) > 100
            or not all(_is_id(child) for child in children)
            or children != sorted(set(children))):
            return False
    if "tax_scope" in values and values["tax_scope"] not in (None, "service", "consu"):
        return False
    if "tax_exigibility" in values and values["tax_exigibility"] not in ("on_invoice", "on_payment"):
        return False
    if "cash_basis_transition_account_id" in values and not (
        values["cash_basis_transition_account_id"] is None
        or _is_id(values["cash_basis_transition_account_id"])
    ):
        return False
    return all(
        field_name not in values or isinstance(values[field_name], bool)
        for field_name in ("include_base_amount", "is_base_affected", "analytic")
    )


def _valid_order_lines(capability_id: str, lines: Any) -> bool:
    if not isinstance(lines, list) or not 1 <= len(lines) <= 200:
        return False
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
    for line in lines:
        if not isinstance(line, dict) or set(line) != expected:
            return False
        quantity = _decimal(line["quantity"], positive=True)
        price_unit = _decimal(line["price_unit"])
        discount = _decimal(line["discount"])
        tax_ids = line["tax_ids"]
        if (
            not _is_id(line["product_id"])
            or not _is_id(line["uom_id"])
            or not _is_text(line["name"])
            or quantity is None
            or _canonical_decimal_text(quantity) != line["quantity"]
            or price_unit is None
            or _canonical_decimal_text(price_unit) != line["price_unit"]
            or discount is None
            or discount > Decimal(100)
            or _canonical_decimal_text(discount) != line["discount"]
            or not isinstance(tax_ids, list)
            or any(not _is_id(item) for item in tax_ids)
            or tax_ids != sorted(set(tax_ids))
            or (purchase and not _is_datetime(line["date_planned"]))
        ):
            return False
    return True


def _valid_order_create_parameters(
    capability_id: str, parameters: dict[str, Any]
) -> bool:
    sale = capability_id == "sale.order.create"
    if sale:
        if (
            not _is_id(parameters["partner_id"])
            or not _is_id(parameters["pricelist_id"])
            or not _is_datetime(parameters["date_order"])
            or not (
                parameters["client_order_ref"] is None
                or _is_text(parameters["client_order_ref"], maximum=200)
            )
            or not (
                parameters["validity_date"] is None
                or _is_date(parameters["validity_date"])
            )
            or not (
                parameters["commitment_date"] is None
                or _is_datetime(parameters["commitment_date"])
            )
        ):
            return False
    elif (
        not _is_id(parameters["partner_id"])
        or not _is_id(parameters["currency_id"])
        or not _is_id(parameters["picking_type_id"])
        or not _is_datetime(parameters["date_order"])
        or not (
            parameters["partner_ref"] is None
            or _is_text(parameters["partner_ref"], maximum=200)
        )
        or not (parameters["incoterm_id"] is None or _is_id(parameters["incoterm_id"]))
    ):
        return False
    return (
        parameters["payment_term_id"] is None or _is_id(parameters["payment_term_id"])
    ) and _valid_order_lines(capability_id, parameters["lines"])


def _valid_order_update_parameters(
    capability_id: str, parameters: dict[str, Any]
) -> bool:
    if not _is_id(parameters["order_id"]):
        return False
    changes = parameters["changes"]
    sale = capability_id == "sale.order.update_draft"
    allowed = _SALE_ORDER_UPDATE_KEYS if sale else _PURCHASE_ORDER_UPDATE_KEYS
    if not isinstance(changes, dict) or not changes or not set(changes) <= allowed:
        return False
    reference_field = "client_order_ref" if sale else "partner_ref"
    if reference_field in changes and not (
        changes[reference_field] is None
        or _is_text(changes[reference_field], maximum=200)
    ):
        return False
    if "payment_term_id" in changes and not (
        changes["payment_term_id"] is None or _is_id(changes["payment_term_id"])
    ):
        return False
    if sale:
        return (
            "validity_date" not in changes
            or changes["validity_date"] is None
            or _is_date(changes["validity_date"])
        ) and (
            "commitment_date" not in changes
            or changes["commitment_date"] is None
            or _is_datetime(changes["commitment_date"])
        )
    return ("date_order" not in changes or _is_datetime(changes["date_order"])) and (
        "incoterm_id" not in changes
        or changes["incoterm_id"] is None
        or _is_id(changes["incoterm_id"])
    )


def _valid_stock_transfer_parameters(
    capability_id: str, parameters: dict[str, Any]
) -> bool:
    if capability_id == _STOCK_TRANSFER_CREATE_CAPABILITY:
        moves = parameters["moves"]
        origin = parameters["origin"]
        return bool(
            _is_id(parameters["picking_type_id"])
            and _is_id(parameters["location_id"])
            and _is_id(parameters["location_dest_id"])
            and parameters["location_id"] != parameters["location_dest_id"]
            and (parameters["partner_id"] is None or _is_id(parameters["partner_id"]))
            and (
                parameters["scheduled_date"] is None
                or _is_datetime(parameters["scheduled_date"])
            )
            and (origin is None or _is_text(origin, maximum=200))
            and (origin is None or "ODACV4" not in origin)
            and isinstance(moves, list)
            and 1 <= len(moves) <= 200
            and all(
                isinstance(move, dict)
                and set(move) == {"product_id", "name", "quantity", "uom_id"}
                and _is_id(move["product_id"])
                and _is_id(move["uom_id"])
                and _is_text(move["name"])
                and (quantity := _decimal(move["quantity"], positive=True)) is not None
                and _canonical_decimal_text(quantity) == move["quantity"]
                for move in moves
            )
        )
    if capability_id == _STOCK_TRANSFER_QUANTITIES_CAPABILITY:
        lines = parameters["lines"]
        return bool(
            _is_id(parameters["transfer_id"])
            and isinstance(lines, list)
            and 1 <= len(lines) <= 200
            and all(
                isinstance(line, dict)
                and set(line) == {"move_id", "quantity"}
                and _is_id(line["move_id"])
                and (quantity := _decimal(line["quantity"])) is not None
                and _canonical_decimal_text(quantity) == line["quantity"]
                for line in lines
            )
            and [line["move_id"] for line in lines]
            == sorted({line["move_id"] for line in lines})
        )
    if capability_id == _STOCK_TRANSFER_VALIDATE_CAPABILITY:
        return _is_id(parameters["transfer_id"]) and parameters["backorder_policy"] in {
            "create",
            "cancel",
        }
    return _is_id(parameters["transfer_id"])


def _valid_purchase_bill_parameters(
    capability_id: str, parameters: dict[str, Any]
) -> bool:
    if capability_id == "purchase.order.bill.create":
        return (set(parameters) == {"order_ids"} and _valid_round_ids(parameters["order_ids"], minimum=1)
                if "order_ids" in parameters else set(parameters) == {"order_id"} and _is_id(parameters["order_id"]))
    if not _is_id(parameters["bill_id"]):
        return False
    if capability_id == "purchase_bill.lines.unmatch":
        line_ids = parameters["bill_line_ids"]
        return bool(
            isinstance(line_ids, list)
            and 1 <= len(line_ids) <= 200
            and line_ids == sorted(set(line_ids))
            and all(_is_id(item) for item in line_ids)
        )
    pairs = parameters["pairs"]
    return bool(
        isinstance(pairs, list)
        and 1 <= len(pairs) <= 200
        and all(
            isinstance(pair, dict)
            and set(pair) == {"purchase_line_id", "bill_line_id"}
            and _is_id(pair["purchase_line_id"])
            and _is_id(pair["bill_line_id"])
            for pair in pairs
        )
        and [(pair["purchase_line_id"], pair["bill_line_id"]) for pair in pairs]
        == sorted({(pair["purchase_line_id"], pair["bill_line_id"]) for pair in pairs})
    )


def _valid_payment_term_header(parameters: dict[str, Any]) -> bool:
    if "name" in parameters and not _is_text(parameters["name"], maximum=200):
        return False
    if "sequence" in parameters and not (
        isinstance(parameters["sequence"], int)
        and not isinstance(parameters["sequence"], bool)
        and parameters["sequence"] >= 0
    ):
        return False
    if "note" in parameters and not (
        parameters["note"] is None or _is_text(parameters["note"], maximum=5000)
    ):
        return False
    if any(
        field in parameters and not isinstance(parameters[field], bool)
        for field in ("display_on_invoice", "early_discount")
    ):
        return False
    if "discount_percentage" in parameters:
        percentage = _decimal(parameters["discount_percentage"])
        if percentage is None or percentage > 100:
            return False
    if "discount_days" in parameters and not (
        isinstance(parameters["discount_days"], int)
        and not isinstance(parameters["discount_days"], bool)
        and parameters["discount_days"] >= 0
    ):
        return False
    if parameters.get("early_pay_discount_computation") not in {
        None,
        "included",
        "excluded",
        "mixed",
    }:
        return False
    return not parameters.get("early_discount") or bool(
        _decimal(parameters.get("discount_percentage"), positive=True)
        and isinstance(parameters.get("discount_days"), int)
        and not isinstance(parameters.get("discount_days"), bool)
        and parameters["discount_days"] > 0
    )


def _valid_payment_term_lines(lines: Any) -> bool:
    if not isinstance(lines, list) or not lines:
        return False
    percent_total = Decimal(0)
    has_percent = False
    for line in lines:
        if not isinstance(line, dict) or not {
            "value",
            "value_amount",
            "delay_type",
            "nb_days",
        } <= set(line) <= {
            "value",
            "value_amount",
            "delay_type",
            "nb_days",
            "days_next_month",
        }:
            return False
        amount = _decimal(line["value_amount"])
        if line["value"] not in {"percent", "fixed"} or amount is None:
            return False
        if line["value"] == "percent":
            has_percent = True
            if amount > 100:
                return False
            percent_total += amount
        if line["delay_type"] not in _PAYMENT_TERM_DELAY_TYPES:
            return False
        if not (
            isinstance(line["nb_days"], int)
            and not isinstance(line["nb_days"], bool)
            and line["nb_days"] >= 0
        ):
            return False
        if "days_next_month" in line and not (
            isinstance(line["days_next_month"], int)
            and not isinstance(line["days_next_month"], bool)
            and 0 <= line["days_next_month"] <= 31
        ):
            return False
    return has_percent and percent_total == 100


def _valid_payment_term_parameters(
    capability_id: str, parameters: dict[str, Any], company_id: int
) -> bool:
    if capability_id == "payment_term.create":
        return bool(
            parameters["company_id"] == company_id
            and _is_text(parameters["name"], maximum=200)
            and _valid_payment_term_header(parameters)
            and _valid_payment_term_lines(parameters["lines"])
        )
    if not _is_id(parameters["payment_term_id"]):
        return False
    if capability_id == "payment_term.update":
        return len(parameters) > 1 and _valid_payment_term_header(parameters)
    if capability_id == "payment_term.lines.replace":
        return _valid_payment_term_lines(parameters["lines"])
    return True


def _valid_accrual_parameters(parameters: dict[str, Any]) -> bool:
    order_ids = parameters["order_ids"]
    return bool(
        parameters["source_model"] in {"sale.order", "purchase.order"}
        and isinstance(order_ids, list)
        and order_ids
        and order_ids == sorted(set(order_ids))
        and all(_is_id(item) for item in order_ids)
        and _is_date(parameters["date"])
        and _is_date(parameters["reversal_date"])
        and parameters["reversal_date"] > parameters["date"]
        and _is_id(parameters["journal_id"])
        and _is_id(parameters["accrual_account_id"])
        and (
            "amount" not in parameters
            or (
                len(order_ids) == 1
                and _decimal(parameters["amount"], positive=True) is not None
            )
        )
    )


def _valid_id_list(value: Any) -> bool:
    return bool(
        isinstance(value, list)
        and value == sorted(set(value))
        and all(_is_id(item) for item in value)
    )


def _valid_fiscal_position_values(values: dict[str, Any], *, create: bool) -> bool:
    if not values or not set(values) <= _FISCAL_POSITION_FIELDS:
        return False
    if create and not _is_text(values.get("name"), maximum=256):
        return False
    if "name" in values and not _is_text(values["name"], maximum=256):
        return False
    if "sequence" in values and not (
        isinstance(values["sequence"], int)
        and not isinstance(values["sequence"], bool)
        and values["sequence"] >= 0
    ):
        return False
    if any(
        field in values and not isinstance(values[field], bool)
        for field in ("auto_apply", "vat_required")
    ):
        return False
    for field in ("country_id", "country_group_id"):
        if field in values and values[field] is not None and not _is_id(values[field]):
            return False
    if "state_ids" in values and not _valid_id_list(values["state_ids"]):
        return False
    for field in ("zip_from", "zip_to", "note"):
        if field in values and not (
            values[field] is None or _is_text(values[field], maximum=5000)
        ):
            return False
    if ("zip_from" in values or "zip_to" in values) and bool(
        values.get("zip_from")
    ) != bool(values.get("zip_to")):
        return False
    return not values.get("zip_from") or values["zip_from"] <= values["zip_to"]


def _valid_configuration_parameters(
    capability_id: str, parameters: dict[str, Any]
) -> bool:
    if capability_id == "fiscal_position.create":
        return _valid_fiscal_position_values(parameters, create=True)
    if capability_id == "fiscal_position.update":
        return _is_id(
            parameters["fiscal_position_id"]
        ) and _valid_fiscal_position_values(parameters["changes"], create=False)
    if capability_id == "fiscal_position.account_mappings.replace":
        mappings = parameters["mappings"]
        return bool(
            _is_id(parameters["fiscal_position_id"])
            and isinstance(mappings, list)
            and all(
                isinstance(item, dict)
                and set(item) == {"source_account_id", "destination_account_id"}
                and _is_id(item["source_account_id"])
                and _is_id(item["destination_account_id"])
                and item["source_account_id"] != item["destination_account_id"]
                for item in mappings
            )
            and [item["source_account_id"] for item in mappings]
            == sorted({item["source_account_id"] for item in mappings})
        )
    if capability_id in {"fiscal_position.archive", "fiscal_position.restore"}:
        return _is_id(parameters["fiscal_position_id"])
    if capability_id == "journal.group.create":
        return bool(
            _is_text(parameters["name"], maximum=256)
            and (
                "sequence" not in parameters
                or (
                    isinstance(parameters["sequence"], int)
                    and not isinstance(parameters["sequence"], bool)
                )
            )
            and (
                "excluded_journal_ids" not in parameters
                or _valid_id_list(parameters["excluded_journal_ids"])
            )
        )
    changes = parameters["changes"]
    return bool(
        _is_id(parameters["journal_group_id"])
        and isinstance(changes, dict)
        and changes
        and set(changes) <= _JOURNAL_GROUP_FIELDS
        and ("name" not in changes or _is_text(changes["name"], maximum=256))
        and (
            "sequence" not in changes
            or (
                isinstance(changes["sequence"], int)
                and not isinstance(changes["sequence"], bool)
            )
        )
        and (
            "excluded_journal_ids" not in changes
            or _valid_id_list(changes["excluded_journal_ids"])
        )
    )


def _valid_account_group_values(values: Any, *, partial: bool) -> bool:
    if (
        not isinstance(values, dict)
        or not values
        or not set(values) <= _ACCOUNT_GROUP_FIELDS
        or (not partial and set(values) != _ACCOUNT_GROUP_FIELDS)
    ):
        return False
    if "name" in values and not _is_text(values["name"], maximum=256):
        return False
    if any(
        field in values and not _is_text(values[field], maximum=64)
        for field in ("code_prefix_start", "code_prefix_end")
    ):
        return False
    start = values.get("code_prefix_start")
    end = values.get("code_prefix_end")
    return not (start is not None and end is not None) or (
        len(start) == len(end) and start <= end
    )


def _valid_tax_repartition_line(line: Any) -> bool:
    if not isinstance(line, dict) or set(line) != {
        "sequence",
        "repartition_type",
        "factor_percent",
        "account_id",
        "tag_ids",
        "use_in_tax_closing",
    }:
        return False
    factor = _signed_decimal(line["factor_percent"])
    return bool(
        isinstance(line["sequence"], int)
        and not isinstance(line["sequence"], bool)
        and line["sequence"] >= 0
        and line["repartition_type"] in {"base", "tax"}
        and factor is not None
        and _canonical_decimal_text(factor) == line["factor_percent"]
        and (line["account_id"] is None or _is_id(line["account_id"]))
        and _valid_id_list(line["tag_ids"])
        and isinstance(line["use_in_tax_closing"], bool)
        and (line["repartition_type"] != "base" or line["account_id"] is None)
    )


def _valid_tax_repartition_side(lines: Any) -> bool:
    if not isinstance(lines, list) or not 2 <= len(lines) <= 100 or not all(
        _valid_tax_repartition_line(line) for line in lines
    ):
        return False
    base_lines = [line for line in lines if line["repartition_type"] == "base"]
    tax_factors = [
        Decimal(line["factor_percent"])
        for line in lines
        if line["repartition_type"] == "tax"
    ]
    positive = sum((factor for factor in tax_factors if factor > 0), Decimal(0))
    negative = [factor for factor in tax_factors if factor < 0]
    return bool(
        len(base_lines) == 1
        and tax_factors
        and positive.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) == 100
        and (
            not negative
            or sum(negative, Decimal(0)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            == -100
        )
    )


def _valid_match_amount(value: Any) -> bool:
    if value is None:
        return True
    if not isinstance(value, dict) or set(value) != {
        "operator",
        "minimum",
        "maximum",
    }:
        return False
    operator = value["operator"]
    if operator not in {"lower", "greater", "between"}:
        return False
    for field in ("minimum", "maximum"):
        text = value[field]
        if text is not None:
            parsed = _decimal(text)
            if parsed is None or _canonical_decimal_text(parsed) != text:
                return False
    if operator == "lower":
        return value["minimum"] is None and value["maximum"] is not None
    if operator == "greater":
        return value["minimum"] is not None and value["maximum"] is None
    return bool(
        value["minimum"] is not None
        and value["maximum"] is not None
        and Decimal(value["minimum"]) <= Decimal(value["maximum"])
    )


def _valid_match_label(value: Any) -> bool:
    if value is None:
        return True
    if not (
        isinstance(value, dict)
        and set(value) == {"operator", "value"}
        and value["operator"] in {"contains", "not_contains", "match_regex"}
        and _is_text(value["value"])
    ):
        return False
    if value["operator"] == "match_regex":
        try:
            re.compile(value["value"])
        except re.error:
            return False
    return True


def _valid_reconciliation_model_values(values: Any, *, partial: bool) -> bool:
    if (
        not isinstance(values, dict)
        or not values
        or not set(values) <= _RECONCILIATION_MODEL_FIELDS
        or (not partial and set(values) != _RECONCILIATION_MODEL_FIELDS)
    ):
        return False
    return bool(
        ("name" not in values or _is_text(values["name"], maximum=256))
        and (
            "sequence" not in values
            or (
                isinstance(values["sequence"], int)
                and not isinstance(values["sequence"], bool)
                and values["sequence"] >= 0
            )
        )
        and (
            "trigger" not in values
            or values["trigger"] in {"manual", "auto_reconcile"}
        )
        and (
            "match_journal_ids" not in values
            or _valid_id_list(values["match_journal_ids"])
        )
        and (
            "match_partner_ids" not in values
            or _valid_id_list(values["match_partner_ids"])
        )
        and (
            "match_amount" not in values
            or _valid_match_amount(values["match_amount"])
        )
        and (
            "match_label" not in values or _valid_match_label(values["match_label"])
        )
    )


def _valid_reconciliation_analytic_distribution(value: Any) -> bool:
    if not isinstance(value, list) or not 1 <= len(value) <= 16:
        return False
    seen_ids: set[int] = set()
    for item in value:
        if not isinstance(item, dict) or set(item) != {
            "analytic_account_ids",
            "percentage",
        }:
            return False
        account_ids = item["analytic_account_ids"]
        percentage = _decimal(item["percentage"], positive=True)
        decimal_places = (
            max(0, -percentage.as_tuple().exponent) if percentage is not None else 0
        )
        if (
            not isinstance(account_ids, list)
            or not 1 <= len(account_ids) <= 16
            or not _valid_id_list(account_ids)
            or seen_ids.intersection(account_ids)
            or percentage is None
            or _canonical_decimal_text(percentage) != item["percentage"]
            or percentage > 100
            or decimal_places > 4
        ):
            return False
        seen_ids.update(account_ids)
    return True


def _valid_reconciliation_model_lines(lines: Any) -> bool:
    required = {
        "sequence",
        "account_id",
        "partner_id",
        "label",
        "amount_type",
        "amount_string",
        "tax_ids",
    }
    if not isinstance(lines, list) or len(lines) > 100:
        return False
    for line in lines:
        if (
            not isinstance(line, dict)
            or not required <= set(line) <= required | {"analytic_distribution"}
            or not isinstance(line["sequence"], int)
            or isinstance(line["sequence"], bool)
            or line["sequence"] < 0
            or (line["account_id"] is not None and not _is_id(line["account_id"]))
            or (line["partner_id"] is not None and not _is_id(line["partner_id"]))
            or not (
                line["label"] is None
                or _is_text(line["label"], maximum=500)
            )
            or line["amount_type"]
            not in {"fixed", "percentage", "percentage_st_line", "regex"}
            or not isinstance(line["amount_string"], str)
            or not _valid_id_list(line["tax_ids"])
            or (
                "analytic_distribution" in line
                and not _valid_reconciliation_analytic_distribution(
                    line["analytic_distribution"]
                )
            )
        ):
            return False
        if line["amount_type"] == "regex":
            if not _is_text(line["amount_string"], maximum=500):
                return False
            try:
                re.compile(line["amount_string"])
            except re.error:
                return False
            continue
        amount = _signed_decimal(line["amount_string"])
        if (
            amount is None
            or _canonical_decimal_text(amount) != line["amount_string"]
            or amount == 0
        ):
            return False
        if line["amount_type"] == "percentage" and not 0 < amount <= 100:
            return False
    return True


def _valid_fiscal_year_values(values: Any, *, partial: bool) -> bool:
    if not isinstance(values, dict) or (partial and not values):
        return False
    if (not partial and set(values) != _FISCAL_YEAR_FIELDS) or not set(
        values
    ) <= _FISCAL_YEAR_FIELDS:
        return False
    return bool(
        ("name" not in values or _is_text(values["name"], maximum=256))
        and ("date_from" not in values or _is_date(values["date_from"]))
        and ("date_to" not in values or _is_date(values["date_to"]))
    )


def _valid_analytic_applicability_values(values: Any, *, partial: bool) -> bool:
    if not isinstance(values, dict) or (partial and not values):
        return False
    if (not partial and set(values) != _ANALYTIC_APPLICABILITY_FIELDS) or not set(
        values
    ) <= _ANALYTIC_APPLICABILITY_FIELDS:
        return False
    return bool(
        ("plan_id" not in values or _is_id(values["plan_id"]))
        and (
            "business_domain" not in values
            or values["business_domain"] in {"general", "invoice", "bill"}
        )
        and (
            "applicability" not in values
            or values["applicability"]
            in {"optional", "mandatory", "unavailable"}
        )
        and (
            "account_prefix" not in values
            or values["account_prefix"] is None
            or _is_text(values["account_prefix"], maximum=64)
        )
        and (
            "product_category_id" not in values
            or values["product_category_id"] is None
            or _is_id(values["product_category_id"])
        )
    )


def _valid_analytic_distribution_model_values(
    values: Any, *, partial: bool
) -> bool:
    if not isinstance(values, dict) or (partial and not values):
        return False
    if (
        not partial and set(values) != _ANALYTIC_DISTRIBUTION_MODEL_FIELDS
    ) or not set(values) <= _ANALYTIC_DISTRIBUTION_MODEL_FIELDS:
        return False
    if "sequence" in values and not (
        isinstance(values["sequence"], int)
        and not isinstance(values["sequence"], bool)
        and values["sequence"] >= 0
    ):
        return False
    if "account_prefix" in values and not (
        values["account_prefix"] is None
        or _is_text(values["account_prefix"], maximum=64)
    ):
        return False
    if any(
        values[field_name] is not None and not _is_id(values[field_name])
        for field_name in (
            "partner_id",
            "partner_category_id",
            "product_id",
            "product_category_id",
        )
        if field_name in values
    ):
        return False
    if "analytic_distribution" in values:
        distribution = values["analytic_distribution"]
        return bool(
            (partial and distribution is None)
            or distribution is not None
            and _valid_analytic_distribution(distribution)
        )
    return partial


def _valid_accounting_reference_write_parameters(
    capability_id: str, parameters: dict[str, Any]
) -> bool:
    if capability_id == "fiscal_year.create":
        return _valid_fiscal_year_values(parameters, partial=False)
    if capability_id == "fiscal_year.update":
        return _is_id(parameters["id"]) and _valid_fiscal_year_values(
            parameters["changes"], partial=True
        )
    if capability_id == "analytic.applicability.create":
        return _valid_analytic_applicability_values(parameters, partial=False)
    if capability_id == "analytic.applicability.update":
        return _is_id(parameters["id"]) and _valid_analytic_applicability_values(
            parameters["changes"], partial=True
        )
    if capability_id == "analytic.distribution_model.create":
        return _valid_analytic_distribution_model_values(parameters, partial=False)
    if capability_id == "analytic.distribution_model.update":
        return _is_id(
            parameters["id"]
        ) and _valid_analytic_distribution_model_values(
            parameters["changes"], partial=True
        )
    if capability_id == "account.tag.create":
        return _valid_account_tag_values(parameters, partial=False)
    if capability_id == "account.tag.update":
        return _is_id(parameters["account_tag_id"]) and _valid_account_tag_values(
            parameters["changes"], partial=True
        )
    if capability_id in {"account.tag.archive", "account.tag.restore"}:
        return _is_id(parameters["account_tag_id"])
    if capability_id == "tax.group.create":
        return _valid_tax_group_values(parameters, partial=False)
    if capability_id == "tax.group.update":
        return _is_id(parameters["tax_group_id"]) and _valid_tax_group_values(
            parameters["changes"], partial=True
        )
    if capability_id == "cash_rounding.create":
        return _valid_cash_rounding_values(parameters, partial=False)
    if capability_id == "cash_rounding.update":
        return _is_id(parameters["cash_rounding_id"]) and _valid_cash_rounding_values(
            parameters["changes"], partial=True
        )
    if capability_id == "currency.rate.record":
        rate = _decimal(parameters["company_units_per_foreign_unit"], positive=True)
        return bool(
            _is_id(parameters["currency_id"])
            and _is_date(parameters["date"])
            and rate is not None
            and _canonical_decimal_text(rate)
            == parameters["company_units_per_foreign_unit"]
        )
    if capability_id == "currency.rate.delete":
        return _is_id(parameters["rate_id"])
    if capability_id == "currency.rate.update":
        changes = parameters["changes"]
        if (not _is_id(parameters["rate_id"]) or not isinstance(changes, dict)
            or not changes or not set(changes) <= {"date", "company_units_per_foreign_unit"}):
            return False
        if "date" in changes and not _is_date(changes["date"]):
            return False
        if "company_units_per_foreign_unit" in changes:
            rate = _decimal(changes["company_units_per_foreign_unit"], positive=True)
            return rate is not None and _canonical_decimal_text(rate) == changes["company_units_per_foreign_unit"]
        return True
    if capability_id == "account.group.create":
        return _valid_account_group_values(parameters, partial=False)
    if capability_id == "account.group.update":
        return _is_id(parameters["account_group_id"]) and _valid_account_group_values(
            parameters["changes"], partial=True
        )
    if capability_id == "tax.repartition_lines.replace":
        invoice_lines = parameters["invoice_lines"]
        refund_lines = parameters["refund_lines"]
        return bool(
            _is_id(parameters["tax_id"])
            and _valid_tax_repartition_side(invoice_lines)
            and _valid_tax_repartition_side(refund_lines)
            and len(invoice_lines) == len(refund_lines)
            and all(
                invoice["repartition_type"] == refund["repartition_type"]
                and invoice["factor_percent"] == refund["factor_percent"]
                for invoice, refund in zip(invoice_lines, refund_lines, strict=True)
            )
        )
    if capability_id == "reconciliation.model.create":
        return _valid_reconciliation_model_values(parameters, partial=False)
    if capability_id == "reconciliation.model.update":
        return _is_id(
            parameters["reconciliation_model_id"]
        ) and _valid_reconciliation_model_values(parameters["changes"], partial=True)
    if capability_id == "reconciliation.model.lines.replace":
        return _is_id(
            parameters["reconciliation_model_id"]
        ) and _valid_reconciliation_model_lines(parameters["lines"])
    return _is_id(parameters["reconciliation_model_id"])


def _valid_account_tag_values(values: Any, *, partial: bool) -> bool:
    if not isinstance(values, dict) or (partial and not values):
        return False
    if (not partial and set(values) != _ACCOUNT_TAG_FIELDS) or not set(values) <= _ACCOUNT_TAG_FIELDS:
        return False
    return bool(
        ("name" not in values or _is_text(values["name"], maximum=256))
        and ("applicability" not in values or values["applicability"] in {"accounts", "taxes", "products"})
        and ("color" not in values or isinstance(values["color"], int) and not isinstance(values["color"], bool) and values["color"] >= 0)
        and ("country_id" not in values or values["country_id"] is None or _is_id(values["country_id"]))
        and not (values.get("applicability") in {"accounts", "products"} and values.get("country_id") is not None)
    )


def _valid_tax_group_values(values: Any, *, partial: bool) -> bool:
    if not isinstance(values, dict) or (partial and not values):
        return False
    if (not partial and not (_TAX_GROUP_FIELDS - _TAX_GROUP_ACCOUNT_FIELDS) <= set(values)) or not set(values) <= _TAX_GROUP_FIELDS:
        return False
    return bool(
        ("name" not in values or _is_text(values["name"], maximum=256))
        and ("sequence" not in values or isinstance(values["sequence"], int) and not isinstance(values["sequence"], bool) and values["sequence"] >= 0)
        and ("preceding_subtotal" not in values or values["preceding_subtotal"] is None or _is_text(values["preceding_subtotal"], maximum=256))
        and all(values[field] is None or _is_id(values[field]) for field in _TAX_GROUP_ACCOUNT_FIELDS if field in values)
    )


def _valid_cash_rounding_values(values: Any, *, partial: bool) -> bool:
    if not isinstance(values, dict) or (partial and not values):
        return False
    if (not partial and set(values) != _CASH_ROUNDING_FIELDS) or not set(values) <= _CASH_ROUNDING_FIELDS:
        return False
    rounding = (
        _decimal(values.get("rounding"), positive=True)
        if "rounding" in values
        else Decimal(1)
    )
    if "rounding" in values and (rounding is None or _canonical_decimal_text(rounding) != values["rounding"]):
        return False
    if not partial:
        strategy = values["strategy"]
        accounts_valid = ((strategy == "add_invoice_line" and values["profit_account_id"] is not None and values["loss_account_id"] is not None) or (strategy == "biggest_tax" and values["profit_account_id"] is None and values["loss_account_id"] is None))
    else:
        accounts_valid = True
    return bool(
        ("name" not in values or _is_text(values["name"], maximum=256))
        and ("strategy" not in values or values["strategy"] in {"biggest_tax", "add_invoice_line"})
        and ("rounding_method" not in values or values["rounding_method"] in {"UP", "DOWN", "HALF-UP"})
        and all(values.get(field) is None or _is_id(values[field]) for field in ("profit_account_id", "loss_account_id") if field in values)
        and accounts_valid
    )


def _valid_product_basic_values(values: Any, *, partial: bool) -> bool:
    if not isinstance(values, dict) or (partial and not values):
        return False
    if not set(values) <= _PRODUCT_BASIC_FIELDS:
        return False
    if not partial and not _PRODUCT_CREATE_REQUIRED_FIELDS <= set(values):
        return False
    list_price = (
        _decimal(values["list_price"])
        if "list_price" in values
        else Decimal(0)
    )
    return bool(
        ("name" not in values or _is_text(values["name"], maximum=256))
        and (
            "default_code" not in values
            or _is_text(values["default_code"], maximum=64)
        )
        and (
            "product_type" not in values
            or values["product_type"] in {"consu", "service"}
        )
        and ("category_id" not in values or _is_id(values["category_id"]))
        and ("uom_id" not in values or _is_id(values["uom_id"]))
        and (
            "barcode" not in values
            or values["barcode"] is None
            or _is_text(values["barcode"], maximum=64)
        )
        and (
            "sale_ok" not in values or isinstance(values["sale_ok"], bool)
        )
        and (
            "purchase_ok" not in values
            or isinstance(values["purchase_ok"], bool)
        )
        and (
            "list_price" not in values
            or list_price is not None
            and list_price >= 0
            and _canonical_decimal_text(list_price) == values["list_price"]
        )
    )


def _valid_product_accounting_profile_values(
    values: Any, *, category: bool
) -> bool:
    allowed = (
        _PRODUCT_CATEGORY_ACCOUNTING_PROFILE_FIELDS
        if category
        else _PRODUCT_ACCOUNTING_PROFILE_FIELDS
    )
    if not isinstance(values, dict) or not values or not set(values) <= allowed:
        return False
    if any(
        values[field_name] is not None and not _is_id(values[field_name])
        for field_name in ("income_account_id", "expense_account_id")
        if field_name in values
    ):
        return False
    return all(field not in values or isinstance(values[field], str) and values[field] in choices
               for field, choices in _PRODUCT_POLICY_FIELDS.items()) and all(
        isinstance(values[field_name], list)
        and values[field_name] == sorted(set(values[field_name]))
        and all(_is_id(item) for item in values[field_name])
        for field_name in ("sale_tax_ids", "purchase_tax_ids")
        if field_name in values
    )


def _valid_transfer_model_values(values: Any, *, partial: bool) -> bool:
    if (
        not isinstance(values, dict)
        or not values
        or not set(values) <= _TRANSFER_MODEL_FIELDS
        or (not partial and set(values) != _TRANSFER_MODEL_FIELDS)
    ):
        return False
    if "name" in values and not _is_text(values["name"], maximum=256):
        return False
    if "journal_id" in values and not _is_id(values["journal_id"]):
        return False
    if "date_start" in values and not _is_date(values["date_start"]):
        return False
    if "date_stop" in values and not (
        values["date_stop"] is None or _is_date(values["date_stop"])
    ):
        return False
    if (
        values.get("date_stop") is not None
        and "date_start" in values
        and values["date_stop"] < values["date_start"]
    ):
        return False
    if "frequency" in values and values["frequency"] not in {
        "month",
        "quarter",
        "year",
    }:
        return False
    if "origin_account_ids" in values:
        account_ids = values["origin_account_ids"]
        if not (
            isinstance(account_ids, list)
            and 1 <= len(account_ids) <= 1000
            and account_ids == sorted(set(account_ids))
            and all(_is_id(item) for item in account_ids)
        ):
            return False
    if "destination_lines" in values:
        lines = values["destination_lines"]
        if not isinstance(lines, list) or not 1 <= len(lines) <= 1000:
            return False
        destination_ids: list[int] = []
        total = Decimal(0)
        for line in lines:
            if not isinstance(line, dict) or set(line) != {
                "account_id",
                "percentage",
            }:
                return False
            percentage = _decimal(line["percentage"], positive=True)
            if (
                not _is_id(line["account_id"])
                or percentage is None
                or percentage > Decimal(100)
                or percentage.as_tuple().exponent < -6
                or _canonical_decimal_text(percentage) != line["percentage"]
            ):
                return False
            destination_ids.append(line["account_id"])
            total += percentage
        if len(destination_ids) != len(set(destination_ids)) or not (
            Decimal(0) < total <= Decimal(100)
        ):
            return False
    return True


def _valid_parameters(
    capability_id: str, parameters: Any, company_id: int | None = None
) -> bool:
    if not isinstance(parameters, dict):
        return False
    if capability_id in invoice_preparation.CAPABILITY_IDS:
        try:
            return invoice_preparation.normalize_parameters(capability_id, parameters) == parameters
        except ValueError:
            return False
    if capability_id in journal_item_processing.CAPABILITY_IDS:
        try:
            return journal_item_processing.normalize_parameters(capability_id, parameters) == parameters
        except ValueError:
            return False
    if capability_id in company_processing.CAPABILITY_IDS:
        try:
            return company_processing.normalize_parameters(capability_id, parameters) == parameters
        except ValueError:
            return False
    if capability_id in analytic_processing.CAPABILITY_IDS:
        try:
            return analytic_processing.normalize_parameters(capability_id, parameters) == parameters
        except ValueError:
            return False
    if capability_id in journal_processing.CAPABILITY_IDS:
        try:
            return journal_processing.normalize_parameters(capability_id, parameters) == parameters
        except ValueError:
            return False
    if capability_id in account_processing.CAPABILITY_IDS:
        try:
            return account_processing.normalize_parameters(capability_id, parameters) == parameters
        except ValueError:
            return False
    if capability_id in tax_processing.CAPABILITY_IDS:
        try:
            return tax_processing.normalize_parameters(capability_id, parameters) == parameters
        except ValueError:
            return False
    if capability_id in payment_term_processing.CAPABILITY_IDS:
        try:
            return payment_term_processing.normalize_parameters(capability_id, parameters) == parameters
        except ValueError:
            return False
    if capability_id in reconciliation_processing.CAPABILITY_IDS:
        try:
            return reconciliation_processing.normalize_parameters(capability_id, parameters) == parameters
        except ValueError:
            return False
    if capability_id in payment_processing.CAPABILITY_IDS:
        try:
            return payment_processing.normalize_parameters(capability_id, parameters) == parameters
        except ValueError:
            return False
    if capability_id in invoice_presentation.CAPABILITY_IDS:
        try:
            return invoice_presentation.normalize_parameters(capability_id, parameters) == parameters
        except ValueError:
            return False
    if capability_id in move_processing.CAPABILITY_IDS:
        try:
            return move_processing.normalize_parameters(capability_id, parameters) == parameters
        except ValueError:
            return False
    if capability_id in partner_preferences.CAPABILITY_IDS:
        try:
            return partner_preferences.normalize_parameters(capability_id, parameters) == parameters
        except ValueError:
            return False
    if capability_id in payment_configuration.CAPABILITY_IDS:
        try:
            return payment_configuration.normalize_parameters(capability_id, parameters) == parameters
        except ValueError:
            return False
    if capability_id in fiscal_mappings.CAPABILITY_IDS:
        try:
            return fiscal_mappings.normalize_parameters(capability_id, parameters) == parameters
        except ValueError:
            return False
    if capability_id in report_budgets.CAPABILITY_IDS:
        try:
            return report_budgets.normalize_parameters(capability_id, parameters) == parameters
        except ValueError:
            return False
    parameter_keys = set(parameters)
    allowed_keys = _PARAMETER_KEYS[capability_id]
    required_keys = allowed_keys
    if capability_id in _BATCH_LIFECYCLE_CAPABILITIES:
        required_keys = frozenset()
    elif capability_id in {"customer_invoice.create", "vendor_bill.create"}:
        required_keys = _DOCUMENT_CREATE_REQUIRED_KEYS
    elif capability_id == "journal_entry.create":
        required_keys = frozenset({"journal_id", "date", "lines"})
    elif capability_id in {
        "customer_credit_note.create",
        "vendor_refund.create",
    }:
        required_keys = frozenset({"move_ids", "date", "reason"}) if "move_ids" in parameters else _REFUND_REQUIRED_KEYS
    elif capability_id in {
        "receivable.payment.register",
        "payable.payment.register",
    }:
        required_keys = (
            _PAYMENT_REGISTER_MANY_REQUIRED_KEYS
            if "move_ids" in parameters
            else _PAYMENT_REGISTER_REQUIRED_KEYS
        )
    elif capability_id in {"reconciliation.apply", "reconciliation.undo"}:
        required_keys = frozenset()
    elif capability_id == "payment_term.create":
        required_keys = frozenset({"name", "company_id", "lines"})
    elif capability_id == "payment_term.update":
        required_keys = frozenset({"payment_term_id"})
    elif capability_id == "period.accrual.generate":
        required_keys = frozenset(
            {
                "source_model",
                "order_ids",
                "date",
                "reversal_date",
                "journal_id",
                "accrual_account_id",
            }
        )
    elif capability_id in {"fiscal_position.create", "journal.group.create"}:
        required_keys = frozenset({"name"})
    elif capability_id == "product.create":
        required_keys = _PRODUCT_CREATE_REQUIRED_FIELDS
    elif capability_id == "tax.create":
        required_keys = _TAX_CONFIG_REQUIRED_KEYS
    elif capability_id == "bank.transaction.record":
        required_keys = allowed_keys - {"foreign_currency_id", "amount_currency", "account_number", "partner_name"}
    elif capability_id == "bank.statement.create":
        required_keys = allowed_keys - {"balance_start", "name", "date"}
    elif capability_id == "tax.group.create":
        required_keys = _TAX_GROUP_FIELDS - _TAX_GROUP_ACCOUNT_FIELDS
    elif capability_id in {_SALE_ORDER_INVOICE_CAPABILITY, "purchase.order.bill.create"}:
        required_keys = frozenset({"order_ids"}) if "order_ids" in parameters else frozenset({"order_id"})
    if not required_keys <= parameter_keys <= allowed_keys:
        return False
    if capability_id in _BATCH_LIFECYCLE_CAPABILITIES:
        singular_field, batch_field = (
            ("move_id", "move_ids")
            if capability_id in _MOVE_BATCH_LIFECYCLE_CAPABILITIES
            else ("payment_id", "payment_ids")
        )
        if parameter_keys == {singular_field}:
            return _is_id(parameters[singular_field])
        return parameter_keys == {batch_field} and _valid_batch_ids(
            parameters[batch_field]
        )
    if capability_id == _SALE_ORDER_INVOICE_CAPABILITY:
        if "order_ids" not in parameters:
            return parameter_keys == {"order_id"} and _is_id(parameters["order_id"])
        return "order_id" not in parameters and _valid_round_ids(parameters["order_ids"], minimum=1) and all(
            field not in parameters or isinstance(parameters[field], bool)
            for field in ("consolidated_billing", "deduct_down_payments")
        )
    if capability_id == _SALE_DOWN_PAYMENT_CAPABILITY:
        amount = _decimal(parameters["amount"], positive=True)
        return bool(_is_id(parameters["order_id"]) and isinstance(parameters["method"], str) and parameters["method"] in {"percentage", "fixed"}
                    and amount is not None and _canonical_decimal_text(amount) == parameters["amount"]
                    and (parameters["method"] != "percentage" or amount <= 100))
    if capability_id in _STOCK_TRANSFER_CAPABILITIES:
        return _valid_stock_transfer_parameters(capability_id, parameters)
    if capability_id in _PURCHASE_BILL_CAPABILITIES:
        return _valid_purchase_bill_parameters(capability_id, parameters)
    if capability_id in _TRANSFER_MODEL_CAPABILITIES:
        if capability_id == "account.transfer_model.create":
            return _valid_transfer_model_values(parameters, partial=False)
        if capability_id == "account.transfer_model.update":
            return _is_id(parameters["transfer_model_id"]) and (
                _valid_transfer_model_values(parameters["changes"], partial=True)
            )
        if capability_id == "account.transfer_model.duplicate":
            return _is_id(parameters["transfer_model_id"]) and _is_text(
                parameters["name"], maximum=256
            )
        return _is_id(parameters["transfer_model_id"])
    if capability_id in _PAYMENT_TERM_CAPABILITIES:
        return company_id is not None and _valid_payment_term_parameters(
            capability_id, parameters, company_id
        )
    if capability_id == "period.accrual.generate":
        return _valid_accrual_parameters(parameters)
    if capability_id in _FISCAL_POSITION_CAPABILITIES | _JOURNAL_GROUP_CAPABILITIES:
        return _valid_configuration_parameters(capability_id, parameters)
    if capability_id in _ACCOUNTING_REFERENCE_WRITE_CAPABILITIES:
        return _valid_accounting_reference_write_parameters(capability_id, parameters)
    if capability_id in _ORDER_CREATE_CAPABILITIES:
        return _valid_order_create_parameters(capability_id, parameters)
    if capability_id in _ORDER_UPDATE_CAPABILITIES:
        return _valid_order_update_parameters(capability_id, parameters)
    if capability_id in _ORDER_LINE_REPLACEMENT_CAPABILITIES:
        return _is_id(parameters["order_id"]) and _valid_order_lines(
            capability_id, parameters["lines"]
        )
    if capability_id in _ORDER_TRANSITION_CAPABILITIES:
        return _is_id(parameters["order_id"])
    if capability_id in {"customer_invoice.create", "vendor_bill.create"}:
        return (
            _is_id(parameters["partner_id"])
            and _is_id(parameters["journal_id"])
            and _is_date(parameters["invoice_date"])
            and ("date" not in parameters or _is_date(parameters["date"]))
            and _is_id(parameters["currency_id"])
            and _valid_document_lines(parameters["lines"])
            and (
                "invoice_date_due" not in parameters
                or parameters["invoice_date_due"] is None
                or _is_date(parameters["invoice_date_due"])
            )
            and all(
                field not in parameters
                or parameters[field] is None
                or _is_id(parameters[field])
                for field in ("payment_term_id", "partner_bank_id", "fiscal_position_id")
            )
            and not (
                parameters.get("invoice_date_due") is not None
                and parameters.get("payment_term_id") is not None
            )
            and all(
                field_name not in parameters
                or _valid_nullable_text(parameters[field_name])
                for field_name in ("reference", "payment_reference")
            )
        )
    if capability_id == "journal_entry.create":
        return (
            _is_id(parameters["journal_id"])
            and _is_date(parameters["date"])
            and _valid_entry_lines(parameters["lines"])
            and (
                "reference" not in parameters
                or _valid_nullable_text(parameters["reference"])
            )
        )
    if capability_id == "invoice.update":
        return _is_id(parameters["move_id"]) and _valid_invoice_changes(
            parameters["changes"]
        )
    if capability_id == "journal_entry.update":
        return _is_id(parameters["move_id"]) and _valid_journal_entry_changes(
            parameters["changes"]
        )
    if capability_id == "invoice.lines.replace":
        return _is_id(parameters["move_id"]) and _valid_replacement_invoice_lines(
            parameters["lines"]
        )
    if capability_id in {"invoice.lines.update", "invoice.lines.add"}:
        lines = parameters["lines"]
        if not _is_id(parameters["move_id"]) or not isinstance(lines, list) or not 1 <= len(lines) <= 200:
            return False
        if capability_id == "invoice.lines.update":
            return all(
                isinstance(item, dict) and set(item) == {"line_id", "changes"}
                and _is_id(item["line_id"]) and _valid_invoice_line_values(item["changes"], partial=True)
                for item in lines
            ) and [item["line_id"] for item in lines] == sorted({item["line_id"] for item in lines})
        ids = parameters["expected_line_ids"]
        return (
            isinstance(ids, list) and all(_is_id(item) for item in ids) and ids == sorted(set(ids))
            and all(_valid_invoice_line_values(item, partial=False) for item in lines)
        )
    if capability_id == "invoice.line.create":
        return _is_id(parameters["move_id"]) and _valid_invoice_line_values(
            parameters["line"], partial=False
        )
    if capability_id == "invoice.line.update":
        return bool(
            _is_id(parameters["move_id"])
            and _is_id(parameters["line_id"])
            and _valid_invoice_line_values(parameters["changes"], partial=True)
        )
    if capability_id == "invoice.line.delete":
        return _is_id(parameters["move_id"]) and _is_id(parameters["line_id"])
    if capability_id == "invoice.lines.remove":
        ids = parameters["line_ids"]
        return bool(
            _is_id(parameters["move_id"]) and isinstance(ids, list) and 1 <= len(ids) <= 200
            and all(_is_id(item) for item in ids) and ids == sorted(set(ids))
        )
    if capability_id in {
        "invoice.delete",
        "journal_entry.duplicate",
        "journal_entry.delete",
    }:
        return _is_id(parameters["move_id"])
    if capability_id == "journal_entry.lines.replace":
        return _is_id(parameters["move_id"]) and _valid_entry_lines(
            parameters["lines"], minimum=1
        )
    if capability_id == "journal_entry.lines.add":
        ids = parameters["expected_line_ids"]
        return bool(
            _is_id(parameters["move_id"])
            and isinstance(ids, list)
            and len(ids) <= 500
            and all(_is_id(item) for item in ids)
            and ids == sorted(set(ids))
            and _valid_entry_lines(parameters["lines"])
            and len(ids) + len(parameters["lines"]) <= 500
        )
    if capability_id == "journal_entry.lines.remove":
        ids = parameters["line_ids"]
        return bool(
            _is_id(parameters["move_id"])
            and isinstance(ids, list)
            and 1 <= len(ids) <= 500
            and all(_is_id(item) for item in ids)
            and ids == sorted(set(ids))
        )
    if capability_id == "invoice.duplicate":
        return _is_id(parameters["move_id"])
    if capability_id == "invoice.type.switch":
        return _is_id(parameters["move_id"]) and parameters[
            "target_move_type"
        ] in _DOCUMENT_TYPES
    if capability_id in {"journal_entry.reverse", "invoice.reverse_and_reissue"} or capability_id in {
        "customer_credit_note.create",
        "vendor_refund.create",
    }:
        return (
            (_valid_round_ids(parameters["move_ids"], minimum=2) and "move_id" not in parameters and "lines" not in parameters
             if "move_ids" in parameters else _is_id(parameters["move_id"]))
            and _is_date(parameters["date"])
            and _is_text(parameters["reason"], maximum=200)
            and (
                "lines" not in parameters
                or _valid_replacement_invoice_lines(parameters["lines"])
            )
        )
    if capability_id in {
        "receivable.payment.register",
        "payable.payment.register",
    }:
        if any(
            field in parameters and not _is_id(parameters[field])
            for field in _PAYMENT_REGISTER_REFERENCE_FIELDS
        ):
            return False
        if not _valid_payment_installments(parameters):
            return False
        if "move_ids" in parameters:
            move_ids = parameters["move_ids"]
            if "move_id" in parameters or not _valid_round_ids(move_ids, minimum=2):
                return False
        handling = parameters.get("payment_difference_handling")
        if "payment_difference_handling" in parameters and handling not in (
            "open",
            "reconcile",
        ):
            return False
        if handling == "reconcile":
            if (
                "amount" not in parameters
                or not _is_id(parameters.get("writeoff_account_id"))
                or (
                    "writeoff_label" in parameters
                    and not _is_text(parameters["writeoff_label"], maximum=200)
                )
            ):
                return False
        elif {"writeoff_account_id", "writeoff_label"} & parameter_keys:
            return False
        return (
            ("move_ids" in parameters or _is_id(parameters["move_id"]))
            and _is_id(parameters["journal_id"])
            and _is_date(parameters["payment_date"])
            and (
                "amount" not in parameters
                or (
                    (amount := _decimal(parameters["amount"], positive=True))
                    is not None
                    and _canonical_decimal_text(amount) == parameters["amount"]
                )
            )
        )
    if capability_id in {"reconciliation.apply", "reconciliation.undo"} and set(
        parameters
    ) == {"line_ids"}:
        line_ids = parameters["line_ids"]
        return (
            isinstance(line_ids, list)
            and len(line_ids) == 2
            and all(_is_id(item) for item in line_ids)
            and len(set(line_ids)) == 2
        )
    if capability_id == "reconciliation.apply":
        return set(parameters) == {"invoice_id", "outstanding_line_id"} and all(
            _is_id(parameters[field_name])
            for field_name in ("invoice_id", "outstanding_line_id")
        )
    if capability_id == "reconciliation.undo":
        if set(parameters) == {"mode", "line_ids"}:
            ids = parameters["line_ids"]
            return (parameters["mode"] == "match_group" and isinstance(ids, list)
                    and 1 <= len(ids) <= 100 and all(_is_id(value) for value in ids)
                    and ids == sorted(set(ids)))
        expected = {
            "invoice_id",
            "partial_reconcile_id",
            "invoice_line_id",
            "counterpart_line_id",
        }
        return (
            set(parameters) == expected
            and all(_is_id(parameters[field_name]) for field_name in expected)
            and parameters["invoice_line_id"] != parameters["counterpart_line_id"]
        )
    if capability_id == "bank.transaction.record":
        amount = _signed_decimal(parameters["amount"])
        return (
            _is_id(parameters["journal_id"])
            and _is_date(parameters["date"])
            and amount is not None
            and amount != 0
            and _is_text(parameters["payment_ref"], maximum=200)
            and (parameters["partner_id"] is None or _is_id(parameters["partner_id"]))
            and _valid_bank_foreign_pair(parameters)
            and all(field not in parameters or parameters[field] is None
                    or _is_text(parameters[field], maximum=200)
                    for field in ("account_number", "partner_name"))
        )
    if capability_id == "asset.create":
        return _valid_asset_create_parameters(parameters)
    if capability_id == "asset.validate":
        return _is_id(parameters["asset_id"])
    if capability_id == "asset.cancel":
        return _is_id(parameters["asset_id"])
    if capability_id in {"asset.dispose", "asset.pause"}:
        return bool(
            _is_id(parameters["asset_id"])
            and _is_date(parameters["date"])
            and (
                parameters["note"] is None or _is_text(parameters["note"], maximum=200)
            )
        )
    if capability_id in {
        "deferred_expense.generate_entries",
        "deferred_revenue.generate_entries",
    }:
        return _is_date(parameters["date_to"]) and _is_month_end(parameters["date_to"])
    if capability_id == "multicurrency.revaluation.generate_entries":
        return bool(
            _is_date(parameters["date"])
            and _is_date(parameters["reversal_date"])
            and parameters["reversal_date"] > parameters["date"]
            and _is_id(parameters["journal_id"])
            and _is_id(parameters["expense_provision_account_id"])
            and _is_id(parameters["income_provision_account_id"])
        )
    if capability_id == "reconciliation.automatic.run":
        line_ids = parameters["line_ids"]
        return bool(
            isinstance(line_ids, list)
            and 2 <= len(line_ids) <= 200
            and all(_is_id(item) for item in line_ids)
            and line_ids == sorted(set(line_ids))
        )
    if capability_id == "period.transfer.run":
        return _is_id(parameters["transfer_model_id"]) and _is_date(
            parameters["run_date"]
        )
    if capability_id == "localization.china.period_transfer.run":
        return _is_date(parameters["run_date"])
    if capability_id == "payment.create":
        return _valid_payment_fields(parameters, partial=False)
    if capability_id == "payment.update_draft":
        return _is_id(parameters["payment_id"]) and _valid_payment_fields(
            parameters["changes"], partial=True
        )
    if capability_id == "bank.transaction.update":
        return _is_id(parameters["transaction_id"]) and _valid_bank_update_changes(
            parameters["changes"]
        )
    if capability_id == "bank.transaction.match":
        candidate_ids = parameters["candidate_line_ids"]
        return bool(
            _is_id(parameters["transaction_id"])
            and isinstance(candidate_ids, list)
            and 1 <= len(candidate_ids) <= 50
            and candidate_ids == sorted(set(candidate_ids))
            and all(_is_id(item) for item in candidate_ids)
        )
    if capability_id == "bank.transaction.unmatch":
        return _is_id(parameters["transaction_id"])
    if capability_id == "bank.transaction.counterparts.replace":
        lines = parameters["lines"]
        return bool(
            _is_id(parameters["transaction_id"])
            and isinstance(lines, list)
            and 2 <= len(lines) <= 100
            and all(
                isinstance(line, dict)
                and set(line) == {"account_id", "label", "balance"}
                and _is_id(line["account_id"])
                and _is_text(line["label"], maximum=200)
                and (balance := _signed_decimal(line["balance"])) is not None
                and balance != 0
                and _canonical_decimal_text(balance) == line["balance"]
                for line in lines
            )
        )
    if capability_id == "bank.statement.create":
        transaction_ids = parameters["transaction_ids"]
        return bool(
            isinstance(transaction_ids, list)
            and 1 <= len(transaction_ids) <= 100
            and all(_is_id(item) for item in transaction_ids)
            and transaction_ids == sorted(set(transaction_ids))
            and _valid_statement_values(
                {
                    "reference": parameters["reference"],
                    "balance_end_real": parameters["balance_end_real"],
                    **({"balance_start": parameters["balance_start"]} if "balance_start" in parameters else {}),
                    **{field: parameters[field] for field in ("name", "date") if field in parameters},
                },
                partial=False,
            )
        )
    if capability_id == "bank.statement.update":
        return _is_id(parameters["statement_id"]) and _valid_statement_values(
            parameters["changes"], partial=True
        )
    if capability_id == "bank.statement.delete":
        return _is_id(parameters["statement_id"])
    if capability_id == "bank.transaction.delete":
        return _is_id(parameters["transaction_id"])
    if capability_id in {"payment.duplicate", "payment.delete"}:
        return _is_id(parameters["payment_id"])
    if capability_id == "reconciliation.write_off":
        expected = _signed_decimal(parameters["expected_residual_amount"])
        return bool(
            _is_id(parameters["transaction_id"])
            and _is_id(parameters["write_off_account_id"])
            and _is_text(parameters["label"], maximum=200)
            and expected is not None
            and expected != 0
        )
    if capability_id == "analytic.plan.create":
        return _is_id(parameters["parent_plan_id"]) and _valid_analytic_plan_values(
            {key: value for key, value in parameters.items() if key != "parent_plan_id"},
            partial=False,
        )
    if capability_id == "analytic.plan.update":
        return _is_id(parameters["plan_id"]) and _valid_analytic_plan_values(
            parameters["changes"], partial=True
        )
    if capability_id == "analytic.account.create":
        return bool(
            _is_text(parameters["name"], maximum=200)
            and "[ODACV4:" not in parameters["name"]
            and _is_id(parameters["plan_id"])
            and (
                parameters["code"] is None or _is_text(parameters["code"], maximum=200)
            )
            and (parameters["partner_id"] is None or _is_id(parameters["partner_id"]))
        )
    if capability_id == "analytic.account.update":
        return _is_id(parameters["analytic_account_id"]) and (
            _valid_analytic_account_changes(parameters["changes"])
        )
    if capability_id in {"analytic.account.archive", "analytic.account.restore"}:
        return _is_id(parameters["analytic_account_id"])
    if capability_id == "analytic.line.create":
        return _valid_analytic_line_values(parameters, partial=False)
    if capability_id == "analytic.line.update":
        return _is_id(parameters["analytic_line_id"]) and _valid_analytic_line_values(
            parameters["changes"], partial=True
        )
    if capability_id == "analytic.line.delete":
        return _is_id(parameters["analytic_line_id"])
    if capability_id == "account.return.create":
        return bool(
            _is_id(parameters["return_type_id"])
            and _is_date(parameters["date_from"])
            and _is_date(parameters["date_to"])
            and parameters["date_from"] <= parameters["date_to"]
        )
    if capability_id == "account.return.check.result.update":
        return _is_id(parameters["check_id"]) and parameters["result"] in {
            "todo",
            "reviewed",
        }
    if capability_id in {
        "account.return.checks.refresh",
        "account.return.validate",
        "account.return.mark_submitted",
        "account.return.archive",
        "account.return.restore",
        "account.return.delete",
    }:
        return _is_id(parameters["return_id"])
    if capability_id == "product.create":
        return _valid_product_basic_values(parameters, partial=False)
    if capability_id == "product.update":
        return _is_id(parameters["product_id"]) and _valid_product_basic_values(
            parameters["changes"], partial=True
        )
    if capability_id == "product.duplicate":
        return bool(
            _is_id(parameters["product_id"])
            and _is_text(parameters["name"], maximum=256)
            and _is_text(parameters["default_code"], maximum=64)
        )
    if capability_id in {"product.archive", "product.restore"}:
        return _is_id(parameters["product_id"])
    if capability_id == "product.cost.update":
        standard_price = _decimal(parameters["standard_price"])
        return bool(
            _is_id(parameters["product_id"])
            and standard_price is not None
            and standard_price >= 0
            and _canonical_decimal_text(standard_price)
            == parameters["standard_price"]
        )
    if capability_id == "product.accounting_profile.update":
        return _is_id(
            parameters["product_id"]
        ) and _valid_product_accounting_profile_values(
            parameters["changes"], category=False
        )
    if capability_id == "product.category.accounting_profile.update":
        return _is_id(
            parameters["category_id"]
        ) and _valid_product_accounting_profile_values(
            parameters["changes"], category=True
        )
    if capability_id == "budget.create":
        return bool(
            _is_text(parameters["name"], maximum=200)
            and "[ODACV4:" not in parameters["name"]
            and _is_date(parameters["date_from"])
            and _is_date(parameters["date_to"])
            and parameters["date_from"] <= parameters["date_to"]
            and parameters["budget_type"] in _BUDGET_TYPES
        )
    if capability_id == "budget.update_draft":
        return _is_id(parameters["budget_id"]) and _valid_budget_changes(
            parameters["changes"]
        )
    if capability_id == "budget.lines.replace":
        return _is_id(parameters["budget_id"]) and _valid_budget_lines(
            parameters["lines"]
        )
    if capability_id in {
        "budget.confirm",
        "budget.reset_to_draft",
        "budget.cancel",
        "budget.mark_done",
    }:
        return _is_id(parameters["budget_id"])
    if capability_id == "partner.create":
        return _valid_partner_contact_values(parameters, partial=False)
    if capability_id == "partner.update":
        return _is_id(parameters["partner_id"]) and _valid_partner_contact_values(
            parameters["changes"], partial=True
        )
    if capability_id in {"partner.archive", "partner.restore"}:
        return _is_id(parameters["partner_id"])
    if capability_id == "partner.accounting.update":
        return _is_id(parameters["partner_id"]) and _valid_partner_accounting_changes(
            parameters["changes"]
        )
    if capability_id == "partner.bank_account.create":
        return _is_id(parameters["partner_id"]) and _valid_partner_bank_values(
            {
                "account_number": parameters["account_number"],
                "account_holder_name": parameters["account_holder_name"],
                "bank_id": parameters["bank_id"],
                "currency_id": parameters["currency_id"],
            },
            partial=False,
        )
    if capability_id == "partner.bank_account.update":
        return _is_id(parameters["partner_bank_id"]) and _valid_partner_bank_values(
            parameters["changes"], partial=True
        )
    if capability_id in {
        "partner.bank_account.archive",
        "partner.bank_account.restore",
    }:
        return _is_id(parameters["partner_bank_id"])
    if capability_id == "account.account.create":
        return _valid_account_config_values(parameters, partial=False)
    if capability_id == "account.account.update":
        return _is_id(parameters["account_id"]) and _valid_account_config_values(
            parameters["changes"], partial=True
        )
    if capability_id in {"account.account.archive", "account.account.restore"}:
        return _is_id(parameters["account_id"])
    if capability_id == "journal.create":
        return _valid_journal_values(parameters, partial=False)
    if capability_id == "journal.update":
        return _is_id(parameters["journal_id"]) and _valid_journal_values(
            parameters["changes"], partial=True
        )
    if capability_id in {"journal.archive", "journal.restore"}:
        return _is_id(parameters["journal_id"])
    if capability_id == "tax.create":
        return _valid_tax_values(parameters, partial=False)
    if capability_id == "tax.update":
        return _is_id(parameters["tax_id"]) and _valid_tax_values(
            parameters["changes"], partial=True
        )
    if capability_id in {"tax.archive", "tax.restore"}:
        return _is_id(parameters["tax_id"])
    return _is_id(parameters["payment_id"])


def _validated_payload(
    payload: Any, company_id: int, failure_type: type[Exception]
) -> tuple[str, str, dict[str, Any], str]:
    if not isinstance(payload, dict) or set(payload) != _PAYLOAD_KEYS:
        raise _protocol(failure_type)
    capability_id = payload["capability_id"]
    if (
        capability_id not in CAPABILITIES
        or payload["confirmation"] != capability_id
        or not _is_id(payload["company_id"])
        or not isinstance(payload["idempotency_key"], str)
        or not _IDEMPOTENCY_KEY_PATTERN.fullmatch(payload["idempotency_key"])
        or not _valid_parameters(capability_id, payload["parameters"], company_id)
    ):
        raise _protocol(failure_type)
    if payload["company_id"] != company_id:
        raise _fail(
            failure_type,
            "company_unavailable",
            "The company is unavailable.",
            exit_code=3,
        )
    expected_key = _deterministic_key(capability_id, payload["parameters"], company_id)
    if expected_key is not None and payload["idempotency_key"] != expected_key:
        raise _protocol(failure_type)
    canonical = json.dumps(
        payload["parameters"],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    marker = f"ODACV4:{hashlib.sha256(canonical).hexdigest()}"
    return capability_id, payload["idempotency_key"], payload["parameters"], marker


def _deterministic_key(
    capability_id: str, parameters: dict[str, Any], company_id: int
) -> str | None:
    if capability_id in {
        "currency.rate.update", "currency.rate.delete",
        "journal_entry.lines.add", "journal_entry.lines.remove",
    }:
        return move_processing.idempotency_key(capability_id, parameters, company_id)
    if capability_id in invoice_preparation.CAPABILITY_IDS:
        return invoice_preparation.idempotency_key(capability_id, parameters, company_id)
    if capability_id in journal_item_processing.CAPABILITY_IDS:
        return journal_item_processing.idempotency_key(capability_id, parameters, company_id)
    if capability_id in company_processing.CAPABILITY_IDS:
        return company_processing.idempotency_key(capability_id, parameters, company_id)
    if capability_id in analytic_processing.CAPABILITY_IDS:
        return analytic_processing.idempotency_key(capability_id, parameters, company_id)
    if capability_id in journal_processing.CAPABILITY_IDS:
        return journal_processing.idempotency_key(capability_id, parameters, company_id)
    if capability_id in account_processing.CAPABILITY_IDS:
        return account_processing.idempotency_key(capability_id, parameters, company_id)
    if capability_id in tax_processing.CAPABILITY_IDS:
        return tax_processing.idempotency_key(capability_id, parameters, company_id)
    if capability_id in payment_term_processing.CAPABILITY_IDS:
        return payment_term_processing.idempotency_key(capability_id, parameters, company_id)
    if capability_id in reconciliation_processing.CAPABILITY_IDS:
        return reconciliation_processing.idempotency_key(capability_id, parameters, company_id)
    if capability_id in payment_processing.CAPABILITY_IDS:
        return payment_processing.idempotency_key(capability_id, parameters, company_id)
    if capability_id in invoice_presentation.CAPABILITY_IDS:
        return invoice_presentation.idempotency_key(capability_id, parameters, company_id)
    if capability_id in move_processing.CAPABILITY_IDS:
        return move_processing.idempotency_key(capability_id, parameters, company_id)
    if capability_id in partner_preferences.CAPABILITY_IDS:
        return partner_preferences.idempotency_key(capability_id, parameters, company_id)
    if capability_id in payment_configuration.CAPABILITY_IDS:
        return payment_configuration.idempotency_key(capability_id, parameters, company_id)
    if capability_id in fiscal_mappings.CAPABILITY_IDS:
        return fiscal_mappings.idempotency_key(capability_id, parameters, company_id)
    if capability_id in report_budgets.CAPABILITY_IDS:
        return report_budgets.idempotency_key(capability_id, parameters, company_id)
    if capability_id in _BATCH_LIFECYCLE_CAPABILITIES and (
        "move_ids" in parameters or "payment_ids" in parameters
    ):
        digest = hashlib.sha256(
            json.dumps(
                parameters,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
        ).hexdigest()[:32]
        return f"{capability_id}:{company_id}:{digest}"
    if capability_id in {
        "account.transfer_model.create",
        "account.transfer_model.duplicate",
    }:
        digest = hashlib.sha256(
            json.dumps(
                parameters,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
        ).hexdigest()[:32]
        return f"{capability_id}:{company_id}:{digest}"
    if capability_id == "account.transfer_model.update":
        digest = hashlib.sha256(
            json.dumps(
                parameters["changes"],
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
        ).hexdigest()[:32]
        return f"{capability_id}:{parameters['transfer_model_id']}:{digest}"
    if capability_id in _TRANSFER_MODEL_CAPABILITIES:
        return f"{capability_id}:{parameters['transfer_model_id']}"
    if capability_id == "account.return.create":
        digest = hashlib.sha256(
            json.dumps(
                parameters,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
        ).hexdigest()[:32]
        return f"{capability_id}:{company_id}:{digest}"
    if capability_id == "account.return.check.result.update":
        return (
            f"{capability_id}:{parameters['check_id']}:{parameters['result']}"
        )
    if capability_id in {
        "account.return.checks.refresh",
        "account.return.validate",
        "account.return.mark_submitted",
        "account.return.archive",
        "account.return.restore",
        "account.return.delete",
    }:
        return f"{capability_id}:{parameters['return_id']}"
    if capability_id in {"product.create", "product.duplicate"}:
        canonical_parameters = (
            _normalized_product_create_values(parameters)
            if capability_id == "product.create"
            else parameters
        )
        digest = hashlib.sha256(
            json.dumps(
                canonical_parameters,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
        ).hexdigest()[:32]
        return f"{capability_id}:{company_id}:{digest}"
    if capability_id in {
        "product.update",
        "product.cost.update",
        "product.accounting_profile.update",
        "product.category.accounting_profile.update",
    }:
        target_id = parameters[
            "category_id"
            if capability_id == "product.category.accounting_profile.update"
            else "product_id"
        ]
        content = (
            {"standard_price": parameters["standard_price"]}
            if capability_id == "product.cost.update"
            else parameters["changes"]
        )
        digest = hashlib.sha256(
            json.dumps(
                content,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
        ).hexdigest()[:32]
        if capability_id == "product.category.accounting_profile.update":
            return f"{capability_id}:{company_id}:{target_id}:{digest}"
        return f"{capability_id}:{target_id}:{digest}"
    if capability_id in {"product.archive", "product.restore"}:
        return f"{capability_id}:{parameters['product_id']}"
    if capability_id in {
        "currency.rate.record",
        "account.group.create",
        "reconciliation.model.create",
        "account.tag.create",
        "tax.group.create",
        "cash_rounding.create",
        "fiscal_year.create",
        "analytic.applicability.create",
        "analytic.distribution_model.create",
    }:
        digest = hashlib.sha256(
            json.dumps(
                parameters,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
        ).hexdigest()[:32]
        return f"{capability_id}:{company_id}:{digest}"
    if capability_id in {
        "account.group.update",
        "reconciliation.model.update",
        "account.tag.update",
        "tax.group.update",
        "cash_rounding.update",
        "fiscal_year.update",
        "analytic.applicability.update",
        "analytic.distribution_model.update",
    }:
        id_name = {
            "account.group.update": "account_group_id",
            "reconciliation.model.update": "reconciliation_model_id",
            "account.tag.update": "account_tag_id",
            "tax.group.update": "tax_group_id",
            "cash_rounding.update": "cash_rounding_id",
            "fiscal_year.update": "id",
            "analytic.applicability.update": "id",
            "analytic.distribution_model.update": "id",
        }[capability_id]
        digest = hashlib.sha256(
            json.dumps(
                parameters["changes"],
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
        ).hexdigest()[:32]
        return f"{capability_id}:{parameters[id_name]}:{digest}"
    if capability_id == "tax.repartition_lines.replace":
        content = {
            "invoice_lines": parameters["invoice_lines"],
            "refund_lines": parameters["refund_lines"],
        }
        digest = hashlib.sha256(
            json.dumps(
                content,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
        ).hexdigest()[:32]
        return f"{capability_id}:{parameters['tax_id']}:{digest}"
    if capability_id == "reconciliation.model.lines.replace":
        digest = hashlib.sha256(
            json.dumps(
                parameters["lines"],
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
        ).hexdigest()[:32]
        return (
            f"{capability_id}:{parameters['reconciliation_model_id']}:{digest}"
        )
    if capability_id in {
        "reconciliation.model.archive",
        "reconciliation.model.restore",
    }:
        return f"{capability_id}:{parameters['reconciliation_model_id']}"
    if capability_id in {"account.tag.archive", "account.tag.restore"}:
        return f"{capability_id}:{parameters['account_tag_id']}"
    if capability_id == _SALE_ORDER_INVOICE_CAPABILITY:
        return None if "order_ids" in parameters else f"{capability_id}:{parameters['order_id']}"
    if capability_id == _SALE_DOWN_PAYMENT_CAPABILITY:
        return None
    if capability_id == _STOCK_TRANSFER_CREATE_CAPABILITY:
        return None
    if capability_id == _STOCK_TRANSFER_QUANTITIES_CAPABILITY:
        canonical = json.dumps(
            parameters["lines"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"{capability_id}:{parameters['transfer_id']}:{digest}"
    if capability_id == _STOCK_TRANSFER_VALIDATE_CAPABILITY:
        return (
            f"{capability_id}:{parameters['transfer_id']}:"
            f"{parameters['backorder_policy']}"
        )
    if capability_id in _STOCK_TRANSFER_ACTION_CAPABILITIES:
        return f"{capability_id}:{parameters['transfer_id']}"
    if capability_id == "purchase.order.bill.create":
        return None if "order_ids" in parameters else f"purchase.order.bill.create:{parameters['order_id']}"
    if capability_id in {"invoice.line.create", "invoice.line.update"}:
        content = (
            parameters["line"]
            if capability_id == "invoice.line.create"
            else parameters["changes"]
        )
        digest = hashlib.sha256(
            json.dumps(
                content,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
        ).hexdigest()[:32]
        target = (
            str(parameters["move_id"])
            if capability_id == "invoice.line.create"
            else f"{parameters['move_id']}:{parameters['line_id']}"
        )
        return f"{capability_id}:{target}:{digest}"
    if capability_id == "invoice.line.delete":
        return (
            f"invoice.line.delete:{parameters['move_id']}:{parameters['line_id']}"
        )
    if capability_id in {"invoice.delete", "journal_entry.delete"}:
        return f"{capability_id}:{parameters['move_id']}"
    if capability_id == "journal_entry.duplicate":
        return None
    if capability_id in {"purchase_bill.match", "purchase_bill.lines.unmatch"}:
        target = parameters[
            "pairs" if capability_id == "purchase_bill.match" else "bill_line_ids"
        ]
        digest = hashlib.sha256(
            json.dumps(target, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:32]
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
        digest = hashlib.sha256(
            json.dumps(target, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:32]
        return f"{capability_id}:{parameters['payment_term_id']}:{digest}"
    if capability_id in {"payment_term.archive", "payment_term.restore"}:
        return f"{capability_id}:{parameters['payment_term_id']}"
    if capability_id in {"fiscal_position.update", "journal.group.update"}:
        target_id = parameters[
            "fiscal_position_id"
            if capability_id.startswith("fiscal_position")
            else "journal_group_id"
        ]
        digest = hashlib.sha256(
            json.dumps(
                parameters["changes"], sort_keys=True, separators=(",", ":")
            ).encode()
        ).hexdigest()[:32]
        return f"{capability_id}:{target_id}:{digest}"
    if capability_id == "fiscal_position.account_mappings.replace":
        digest = hashlib.sha256(
            json.dumps(
                parameters["mappings"], sort_keys=True, separators=(",", ":")
            ).encode()
        ).hexdigest()[:32]
        return f"{capability_id}:{parameters['fiscal_position_id']}:{digest}"
    if capability_id in {"fiscal_position.archive", "fiscal_position.restore"}:
        return f"{capability_id}:{parameters['fiscal_position_id']}"
    if capability_id in _ORDER_CREATE_CAPABILITIES or capability_id in {
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
        "account.account.create",
        "journal.create",
        "tax.create",
        "payment_term.create",
        "period.accrual.generate",
        "fiscal_position.create",
        "journal.group.create",
    }:
        return None
    if (
        capability_id
        in _ORDER_UPDATE_CAPABILITIES | _ORDER_LINE_REPLACEMENT_CAPABILITIES
    ):
        content = (
            parameters["changes"]
            if capability_id in _ORDER_UPDATE_CAPABILITIES
            else parameters["lines"]
        )
        canonical = json.dumps(
            content,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"{capability_id}:{parameters['order_id']}:{digest}"
    if capability_id in _ORDER_TRANSITION_CAPABILITIES:
        return f"{capability_id}:{parameters['order_id']}"
    if capability_id in {"reconciliation.apply", "reconciliation.undo"}:
        if parameters.get("mode") == "match_group":
            return move_processing.idempotency_key(capability_id, parameters, company_id)
        if "line_ids" in parameters:
            low, high = sorted(parameters["line_ids"])
            return f"{capability_id}:{low}:{high}"
        if capability_id == "reconciliation.apply":
            return (
                f"reconciliation.apply:{parameters['invoice_id']}:"
                f"{parameters['outstanding_line_id']}"
            )
        low, high = sorted(
            (parameters["invoice_line_id"], parameters["counterpart_line_id"])
        )
        return (
            f"reconciliation.undo:{parameters['invoice_id']}:"
            f"{parameters['partial_reconcile_id']}:{low}:{high}"
        )
    if capability_id in {"invoice.update", "journal_entry.update"}:
        content: Any = parameters["changes"]
        canonical = json.dumps(
            content,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"{capability_id}:{parameters['move_id']}:{digest}"
    if capability_id == "invoice.duplicate":
        return None
    if capability_id == "invoice.type.switch":
        return (
            f"invoice.type.switch:{parameters['move_id']}:"
            f"{parameters['target_move_type']}"
        )
    if capability_id in {
        "invoice.lines.replace",
        "journal_entry.lines.replace",
    }:
        content = parameters["lines"]
        canonical = json.dumps(
            content,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"{capability_id}:{parameters['move_id']}:{digest}"
    if capability_id in {"invoice.lines.update", "invoice.lines.add", "invoice.lines.remove"}:
        digest = hashlib.sha256(json.dumps(parameters, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()[:32]
        return f"{capability_id}:{parameters['move_id']}:{digest}"
    if capability_id == "asset.validate":
        return f"asset.validate:{parameters['asset_id']}"
    if capability_id in {"asset.cancel", "asset.dispose"}:
        return f"{capability_id}:{parameters['asset_id']}"
    if capability_id == "asset.pause":
        return f"asset.pause:{parameters['asset_id']}:{parameters['date']}"
    if capability_id in {
        "deferred_expense.generate_entries",
        "deferred_revenue.generate_entries",
    }:
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
    if capability_id == "payment.update_draft":
        canonical = json.dumps(
            parameters["changes"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"payment.update_draft:{parameters['payment_id']}:{digest}"
    if capability_id == "payment.reset_to_draft":
        return f"payment.reset_to_draft:{parameters['payment_id']}"
    if capability_id == "bank.statement.create":
        canonical = json.dumps(
            parameters,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"bank.statement.create:{company_id}:{digest}"
    if capability_id == "bank.statement.update":
        canonical = json.dumps(
            parameters["changes"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"bank.statement.update:{parameters['statement_id']}:{digest}"
    if capability_id == "bank.statement.delete":
        return f"bank.statement.delete:{parameters['statement_id']}"
    if capability_id == "bank.transaction.delete":
        return f"bank.transaction.delete:{parameters['transaction_id']}"
    if capability_id in {"payment.duplicate", "payment.delete"}:
        return f"{capability_id}:{parameters['payment_id']}"
    if capability_id in {
        "bank.transaction.update",
        "bank.transaction.match",
        "bank.transaction.counterparts.replace",
        "reconciliation.write_off",
    }:
        if capability_id == "bank.transaction.update":
            target: Any = parameters["changes"]
        elif capability_id == "bank.transaction.match":
            target = parameters["candidate_line_ids"]
        elif capability_id == "bank.transaction.counterparts.replace":
            target = parameters["lines"]
        else:
            target = {
                "write_off_account_id": parameters["write_off_account_id"],
                "label": parameters["label"],
                "expected_residual_amount": parameters["expected_residual_amount"],
            }
        canonical = json.dumps(
            target,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"{capability_id}:{parameters['transaction_id']}:{digest}"
    if capability_id == "bank.transaction.unmatch":
        return f"bank.transaction.unmatch:{parameters['transaction_id']}"
    if capability_id == "analytic.plan.update":
        canonical = json.dumps(
            parameters["changes"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"analytic.plan.update:{parameters['plan_id']}:{digest}"
    if capability_id == "analytic.account.update":
        canonical = json.dumps(
            parameters["changes"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"analytic.account.update:{parameters['analytic_account_id']}:{digest}"
    if capability_id in {"analytic.account.archive", "analytic.account.restore"}:
        return f"{capability_id}:{parameters['analytic_account_id']}"
    if capability_id == "analytic.line.update":
        canonical = json.dumps(
            parameters["changes"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"analytic.line.update:{parameters['analytic_line_id']}:{digest}"
    if capability_id == "analytic.line.delete":
        return f"analytic.line.delete:{parameters['analytic_line_id']}"
    if capability_id in {"budget.update_draft", "budget.lines.replace"}:
        content = (
            parameters["changes"]
            if capability_id == "budget.update_draft"
            else parameters["lines"]
        )
        canonical = json.dumps(
            content,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"{capability_id}:{parameters['budget_id']}:{digest}"
    if capability_id in {
        "budget.confirm",
        "budget.reset_to_draft",
        "budget.cancel",
        "budget.mark_done",
    }:
        return f"{capability_id}:{parameters['budget_id']}"
    if capability_id == "partner.create":
        canonical = json.dumps(
            parameters,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"partner.create:{digest}"
    if capability_id in {"partner.update", "partner.accounting.update"}:
        canonical = json.dumps(
            parameters["changes"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
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
            allow_nan=False,
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"partner.bank_account.update:{parameters['partner_bank_id']}:{digest}"
    if capability_id in {
        "partner.bank_account.archive",
        "partner.bank_account.restore",
    }:
        return f"{capability_id}:{parameters['partner_bank_id']}"
    config_update_ids = {
        "account.account.update": "account_id",
        "journal.update": "journal_id",
        "tax.update": "tax_id",
    }
    if capability_id in config_update_ids:
        canonical = json.dumps(
            parameters["changes"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        target_name = config_update_ids[capability_id]
        return f"{capability_id}:{parameters[target_name]}:{digest}"
    config_lifecycle_ids = {
        "account.account.archive": "account_id",
        "account.account.restore": "account_id",
        "journal.archive": "journal_id",
        "journal.restore": "journal_id",
        "tax.archive": "tax_id",
        "tax.restore": "tax_id",
    }
    if capability_id in config_lifecycle_ids:
        target_name = config_lifecycle_ids[capability_id]
        return f"{capability_id}:{parameters[target_name]}"
    if (
        capability_id in {"receivable.payment.register", "payable.payment.register"}
        and "move_ids" in parameters
    ):
        if _payment_round_operation(parameters):
            return None
        canonical = json.dumps(
            parameters,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"{capability_id}:{company_id}:{digest}"
    if capability_id in {
        "customer_credit_note.create",
        "vendor_refund.create",
        "invoice.reverse_and_reissue",
    } or (
        capability_id in {"receivable.payment.register", "payable.payment.register"}
        and ("amount" in parameters or _payment_round_operation(parameters))
    ):
        return None
    primary_name = (
        "payment_id"
        if capability_id in {"payment.cancel", "payment.post"}
        else "move_id"
    )
    return f"{capability_id}:{parameters[primary_name]}"


def _operation_marker(capability_id: str, key: str, parameters: dict[str, Any]) -> str:
    canonical = json.dumps(
        parameters,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    raw = f"{capability_id}\0{key}\0{canonical}".encode()
    return f"ODACV4:{hashlib.sha256(raw).hexdigest()}"


def _page(
    env: Any,
    company_id: int,
    *,
    company_visible: bool,
    module_installed: bool,
    access_allowed: bool,
    idempotent_replay: bool = False,
    result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "user_id": env.uid,
        "company_visible": company_visible,
        "module_installed": module_installed,
        "access_allowed": access_allowed,
        "idempotent_replay": idempotent_replay,
        "result": result,
    }


def _gate(env: Any, capability_id: str, company_id: int) -> tuple[bool, bool, bool]:
    required_models = _MODELS[capability_id]
    installed = {
        model_name: env.registry.get(model_name) is not None
        for model_name in required_models
    }
    company_model = env["res.company"] if installed.get("res.company") else None
    company_read = bool(company_model is not None and company_model.has_access("read"))
    company_visible = bool(
        company_read and company_model.search_count([("id", "=", company_id)], limit=1)
    )
    module_installed = all(installed.values())
    group_allowed = bool(
        module_installed
        and env.user.has_group(_GROUPS[capability_id])
        and (
            capability_id not in _PRODUCT_ARCHIVE_CAPABILITIES
            or env.user.has_group(_PRODUCT_ARCHIVE_ADDITIONAL_GROUP)
        )
    )
    access_allowed = bool(
        company_visible
        and module_installed
        and group_allowed
        and all(
            env[model].has_access(operation)
            for model, operation in _ACCESS[capability_id]
        )
    )
    return company_visible, module_installed, access_allowed


def _scoped(env: Any, model: str, company_id: int) -> Any:
    return (
        env[model]
        .with_company(company_id)
        .with_context(
            active_test=False,
            allowed_company_ids=[company_id],
        )
    )


def _search_one(
    env: Any,
    model: str,
    domain: list[Any],
    company_id: int,
    failure_type: type[Exception],
    *,
    missing_code: str = "record_not_found",
) -> Any:
    records = _scoped(env, model, company_id).search(domain, limit=2)
    if not records:
        raise _fail(
            failure_type,
            missing_code,
            "The requested accounting record was not found.",
            exit_code=4,
        )
    if len(records) != 1:
        raise _fail(
            failure_type,
            "idempotency_conflict",
            "The accounting operation has conflicting records.",
            exit_code=5,
        )
    return records


def _ensure_ids(
    env: Any,
    model: str,
    ids: set[int],
    domain: list[Any],
    company_id: int,
    failure_type: type[Exception],
) -> Any:
    if not ids:
        return _scoped(env, model, company_id).browse([])
    records = _scoped(env, model, company_id).search(
        [("id", "in", sorted(ids)), *domain], limit=len(ids) + 1
    )
    if set(records.ids) != ids:
        raise _fail(
            failure_type,
            "record_not_found",
            "A referenced accounting record was not found in the company.",
            exit_code=4,
        )
    return records


def _validate_line_analytic_references(
    env: Any,
    lines: list[dict[str, Any]],
    company_id: int,
    failure_type: type[Exception],
) -> None:
    _ensure_ids(
        env,
        "account.analytic.account",
        _analytic_account_ids(lines),
        [("company_id", "in", [False, company_id])],
        company_id,
        failure_type,
    )


def _record_ids(value: Any) -> list[int]:
    ids = getattr(value, "ids", [])
    return sorted(item for item in ids if _is_id(item))


def _move_result(
    move: Any, company_id: int, *, source_id: int | None = None
) -> dict[str, Any]:
    line_ids = _record_ids(move.line_ids)
    reconciled = bool(line_ids and all(bool(line.reconciled) for line in move.line_ids))
    result = {
        "model": "account.move",
        "id": move.id,
        "name": move.name or None,
        "state": move.state or None,
        "company_id": company_id,
        "move_type": move.move_type or None,
        "source_id": source_id,
        "line_ids": line_ids,
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": reconciled,
    }
    assert set(result) == _RESULT_KEYS
    return result


def _asset_result(asset: Any, company_id: int) -> dict[str, Any]:
    result = {
        "model": "account.asset",
        "id": asset.id,
        "name": asset.name or None,
        "state": asset.state or None,
        "company_id": company_id,
        "move_type": None,
        "source_id": None,
        "line_ids": _record_ids(asset.depreciation_move_ids),
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }
    assert set(result) == _RESULT_KEYS
    return result


def _asset_marker_suffix(company_id: int, key: str) -> str:
    digest = hashlib.sha256(f"{company_id}{key}".encode()).hexdigest()
    return f"[ODACV4:{digest}]"


def _same_decimal(actual: Any, expected: str) -> bool:
    try:
        return Decimal(str(actual)) == Decimal(expected)
    except (InvalidOperation, TypeError, ValueError):
        return False


def _asset_matches_request(
    asset: Any,
    parameters: dict[str, Any],
    company_id: int,
    full_name: str,
) -> bool:
    return bool(
        asset.name == full_name
        and asset.company_id.id == company_id
        and str(asset.acquisition_date) == parameters["acquisition_date"]
        and _same_decimal(asset.original_value, parameters["original_value"])
        and _same_decimal(asset.salvage_value, parameters["salvage_value"])
        and asset.account_asset_id.id == parameters["account_asset_id"]
        and asset.account_depreciation_id.id == parameters["account_depreciation_id"]
        and asset.account_depreciation_expense_id.id
        == parameters["account_depreciation_expense_id"]
        and asset.journal_id.id == parameters["journal_id"]
        and asset.method == parameters["method"]
        and asset.method_number == parameters["method_number"]
        and asset.method_period == parameters["method_period"]
        and _same_decimal(
            asset.method_progress_factor, parameters["method_progress_factor"]
        )
        and asset.prorata_computation_type == parameters["prorata_computation_type"]
    )


def _create_asset(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    key: str,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    suffix = _asset_marker_suffix(company_id, key)
    full_name = f"{parameters['name']} {suffix}"

    # account.asset has no reference/idempotency field.  The visible name suffix is
    # intentionally the only marker in this minimal contract.  Editing/removing it
    # breaks replay detection, and without a database uniqueness constraint it does
    # not claim concurrency-safe exactly-once semantics.
    existing = _scoped(env, "account.asset", company_id).search(
        [
            ("company_id", "=", company_id),
            ("name", "=like", f"% {suffix}"),
        ],
        limit=2,
    )
    if existing:
        if len(existing) != 1 or not _asset_matches_request(
            existing, parameters, company_id, full_name
        ):
            raise _fail(
                failure_type,
                "idempotency_conflict",
                "The asset marker already exists with different parameters.",
                exit_code=5,
            )
        return _asset_result(existing, company_id), True

    account_ids = {
        parameters["account_asset_id"],
        parameters["account_depreciation_id"],
        parameters["account_depreciation_expense_id"],
    }
    _ensure_ids(
        env,
        "account.account",
        account_ids,
        [("company_ids", "in", [company_id])],
        company_id,
        failure_type,
    )
    _ensure_ids(
        env,
        "account.journal",
        {parameters["journal_id"]},
        [("company_id", "=", company_id), ("type", "=", "general")],
        company_id,
        failure_type,
    )
    asset = _scoped(env, "account.asset", company_id).create(
        {
            "name": full_name,
            "company_id": company_id,
            "acquisition_date": parameters["acquisition_date"],
            "original_value": Decimal(parameters["original_value"]),
            "salvage_value": Decimal(parameters["salvage_value"]),
            "account_asset_id": parameters["account_asset_id"],
            "account_depreciation_id": parameters["account_depreciation_id"],
            "account_depreciation_expense_id": parameters[
                "account_depreciation_expense_id"
            ],
            "journal_id": parameters["journal_id"],
            "method": parameters["method"],
            "method_number": parameters["method_number"],
            "method_period": parameters["method_period"],
            "method_progress_factor": Decimal(parameters["method_progress_factor"]),
            "prorata_computation_type": parameters["prorata_computation_type"],
        }
    )
    if (
        len(asset) != 1
        or asset.state != "draft"
        or asset.depreciation_move_ids
        or not _asset_matches_request(asset, parameters, company_id, full_name)
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo returned an invalid draft asset.",
            exit_code=6,
        )
    return _asset_result(asset, company_id), False


def _validate_asset(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    asset = _search_one(
        env,
        "account.asset",
        [
            ("id", "=", parameters["asset_id"]),
            ("company_id", "=", company_id),
        ],
        company_id,
        failure_type,
    )
    if asset.state == "open":
        return _asset_result(asset, company_id), True
    if asset.state != "draft":
        raise _fail(
            failure_type,
            "state_conflict",
            "Only a draft asset can be validated.",
            exit_code=5,
        )

    # Call the public Odoo business method unchanged.  Any third-party singleton
    # failure bubbles to dispatch(), is normalized to odoo_write_error, and makes
    # the outer write cursor roll the entire transaction back.
    asset.validate()
    if asset.state != "open":
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not validate the asset.",
            exit_code=6,
        )
    return _asset_result(asset, company_id), False


def _lifecycle_asset(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> Any:
    return _search_one(
        env,
        "account.asset",
        [("id", "=", parameters["asset_id"]), ("company_id", "=", company_id)],
        company_id,
        failure_type,
    )


def _cancel_asset(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    asset = _lifecycle_asset(env, parameters, company_id, failure_type)
    if asset.state == "cancelled":
        return _asset_result(asset, company_id), True
    if asset.state != "open":
        raise _fail(
            failure_type,
            "state_conflict",
            "Only a running asset can be cancelled.",
            exit_code=5,
        )
    asset.set_to_cancelled()
    asset.invalidate_recordset(["state", "depreciation_move_ids"])
    if asset.state != "cancelled":
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not cancel the asset.",
            exit_code=6,
        )
    return _asset_result(asset, company_id), False


def _dispose_asset(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    asset = _lifecycle_asset(env, parameters, company_id, failure_type)
    if asset.state == "close":
        if str(asset.disposal_date) != parameters["date"]:
            raise _fail(
                failure_type,
                "state_conflict",
                "The asset was already disposed on another date.",
                exit_code=5,
            )
        return _asset_result(asset, company_id), True
    if asset.state != "open":
        raise _fail(
            failure_type,
            "state_conflict",
            "Only a running asset can be disposed.",
            exit_code=5,
        )

    book_value = Decimal(str(asset._get_own_book_value(parameters["date"])))
    if book_value > 0 and not asset.company_id.loss_account_id:
        raise _fail(
            failure_type,
            "configuration_missing",
            "The company asset-disposal loss account is not configured.",
            exit_code=4,
        )
    if book_value < 0 and not asset.company_id.gain_account_id:
        raise _fail(
            failure_type,
            "configuration_missing",
            "The company asset-disposal gain account is not configured.",
            exit_code=4,
        )

    wizard = _scoped(env, "asset.modify", company_id).create(
        {
            "asset_id": asset.id,
            "modify_action": "dispose",
            "date": parameters["date"],
            "name": parameters["note"] or False,
        }
    )
    wizard.sell_dispose()
    asset.invalidate_recordset(["state", "disposal_date", "depreciation_move_ids"])
    if asset.state != "close" or str(asset.disposal_date) != parameters["date"]:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not dispose the asset on the requested date.",
            exit_code=6,
        )
    return _asset_result(asset, company_id), False


def _pause_asset(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    asset = _lifecycle_asset(env, parameters, company_id, failure_type)
    if asset.state == "paused":
        return _asset_result(asset, company_id), True
    if asset.state != "open":
        raise _fail(
            failure_type,
            "state_conflict",
            "Only a running asset can be paused.",
            exit_code=5,
        )
    wizard = _scoped(env, "asset.modify", company_id).create(
        {
            "asset_id": asset.id,
            "modify_action": "pause",
            "date": parameters["date"],
            "name": parameters["note"] or False,
        }
    )
    wizard.pause()
    asset.invalidate_recordset(["state", "depreciation_move_ids"])
    if asset.state != "paused":
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not pause the asset.",
            exit_code=6,
        )
    return _asset_result(asset, company_id), False


def _relation_id(value: Any) -> int | None:
    record_id = getattr(value, "id", None)
    return record_id if _is_id(record_id) else None


def _analytic_plan_result(plan: Any, company_id: int) -> dict[str, Any]:
    result = {
        "model": "account.analytic.plan",
        "id": plan.id,
        "name": plan.name or None,
        "state": "active",
        "company_id": company_id,
        "move_type": None,
        "source_id": _relation_id(plan.parent_id),
        "line_ids": [],
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }
    assert set(result) == _RESULT_KEYS
    return result


def _analytic_account_result(account: Any, company_id: int) -> dict[str, Any]:
    result = {
        "model": "account.analytic.account",
        "id": account.id,
        "name": account.name or None,
        "state": "active" if account.active else "archived",
        "company_id": company_id,
        "move_type": None,
        "source_id": account.plan_id.id,
        "line_ids": [],
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }
    assert set(result) == _RESULT_KEYS
    return result


def _analytic_line_result(
    line: Any, company_id: int, *, state: str = "manual"
) -> dict[str, Any]:
    result = {
        "model": "account.analytic.line",
        "id": line.id,
        "name": line.name or None,
        "state": state,
        "company_id": company_id,
        "move_type": None,
        "source_id": _relation_id(line.account_id),
        "line_ids": [],
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }
    assert set(result) == _RESULT_KEYS
    return result


def _budget_result(budget: Any, company_id: int) -> dict[str, Any]:
    result = {
        "model": "budget.analytic",
        "id": budget.id,
        "name": budget.name or None,
        "state": budget.state or None,
        "company_id": company_id,
        "move_type": None,
        "source_id": None,
        "line_ids": _record_ids(budget.budget_line_ids),
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }
    assert set(result) == _RESULT_KEYS
    return result


def _name_with_preserved_marker(current_name: Any, requested_name: str) -> str:
    match = _VISIBLE_MARKER_SUFFIX.search(
        current_name if isinstance(current_name, str) else ""
    )
    return f"{requested_name}{match.group(1) if match else ''}"


def _analytic_plan(
    env: Any,
    plan_id: int,
    company_id: int,
    failure_type: type[Exception],
) -> Any:
    plan = _search_one(
        env,
        "account.analytic.plan",
        [("id", "=", plan_id)],
        company_id,
        failure_type,
    )
    plan_company_id = _relation_id(getattr(plan, "company_id", False))
    if plan_company_id not in {None, company_id}:
        raise _fail(
            failure_type,
            "record_not_found",
            "The analytic plan is unavailable in the company.",
            exit_code=4,
        )
    return plan


def _analytic_plan_values(plan: Any) -> dict[str, Any]:
    return {
        "name": plan.name,
        "color": plan.color,
        "default_applicability": plan.default_applicability,
    }


def _analytic_plan_matches_create(
    plan: Any,
    parameters: dict[str, Any],
    full_name: str,
) -> bool:
    return bool(
        plan.name == full_name
        and _relation_id(plan.parent_id) == parameters["parent_plan_id"]
        and (
            parameters["color"] is None
            or plan.color == parameters["color"]
        )
        and (
            parameters["default_applicability"] is None
            or plan.default_applicability == parameters["default_applicability"]
        )
    )


def _create_analytic_plan(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    key: str,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    parent = _analytic_plan(
        env, parameters["parent_plan_id"], company_id, failure_type
    )
    suffix = _asset_marker_suffix(company_id, key)
    full_name = f"{parameters['name']} {suffix}"
    existing = _scoped(env, "account.analytic.plan", company_id).search(
        [("name", "=like", f"% {suffix}")], limit=2
    )
    if existing:
        if len(existing) != 1 or not _analytic_plan_matches_create(
            existing, parameters, full_name
        ):
            raise _fail(
                failure_type,
                "idempotency_conflict",
                "The analytic-plan marker already has different parameters.",
                exit_code=5,
            )
        _analytic_plan(
            env, _relation_id(existing.parent_id), company_id, failure_type
        )
        return _analytic_plan_result(existing, company_id), True

    values: dict[str, Any] = {
        "name": full_name,
        "parent_id": parent.id,
    }
    for field_name in ("color", "default_applicability"):
        if parameters[field_name] is not None:
            values[field_name] = parameters[field_name]
    plan = _scoped(env, "account.analytic.plan", company_id).create(values)
    if (
        len(plan) != 1
        or not _analytic_plan_matches_create(plan, parameters, full_name)
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo returned an invalid analytic subplan.",
            exit_code=6,
        )
    return _analytic_plan_result(plan, company_id), False


def _update_analytic_plan(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    plan = _analytic_plan(env, parameters["plan_id"], company_id, failure_type)
    if _relation_id(plan.parent_id) is None:
        raise _fail(
            failure_type,
            "state_conflict",
            "Only an existing analytic subplan can be updated.",
            exit_code=5,
        )
    actual = _analytic_plan_values(plan)
    changes = dict(parameters["changes"])
    if "name" in changes:
        changes["name"] = _name_with_preserved_marker(plan.name, changes["name"])
    target = {**actual, **changes}
    if actual == target:
        return _analytic_plan_result(plan, company_id), True
    plan.write(changes)
    plan.invalidate_recordset(list(changes))
    if (
        _relation_id(plan.parent_id) is None
        or _analytic_plan_values(plan) != target
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not apply the analytic-subplan update.",
            exit_code=6,
        )
    return _analytic_plan_result(plan, company_id), False


def _validate_analytic_references(
    env: Any,
    *,
    plan_id: int,
    partner_id: int | None,
    company_id: int,
    failure_type: type[Exception],
) -> Any:
    plan = _analytic_plan(env, plan_id, company_id, failure_type)
    if partner_id is not None:
        _ensure_ids(
            env,
            "res.partner",
            {partner_id},
            [("company_id", "in", [False, company_id])],
            company_id,
            failure_type,
        )
    return plan


def _analytic_account_values(account: Any) -> dict[str, Any]:
    return {
        "name": account.name,
        "code": account.code or None,
        "partner_id": _relation_id(account.partner_id),
        "active": bool(account.active),
    }


def _create_analytic_account(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    key: str,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    suffix = _asset_marker_suffix(company_id, key)
    full_name = f"{parameters['name']} {suffix}"
    existing = _scoped(env, "account.analytic.account", company_id).search(
        [("company_id", "=", company_id), ("name", "=like", f"% {suffix}")],
        limit=2,
    )
    if existing:
        matches = bool(
            len(existing) == 1
            and existing.name == full_name
            and existing.company_id.id == company_id
            and existing.plan_id.id == parameters["plan_id"]
            and (existing.code or None) == parameters["code"]
            and _relation_id(existing.partner_id) == parameters["partner_id"]
        )
        if not matches:
            raise _fail(
                failure_type,
                "idempotency_conflict",
                "The analytic-account marker already has different parameters.",
                exit_code=5,
            )
        _validate_analytic_references(
            env,
            plan_id=existing.plan_id.id,
            partner_id=_relation_id(existing.partner_id),
            company_id=company_id,
            failure_type=failure_type,
        )
        return _analytic_account_result(existing, company_id), True

    _validate_analytic_references(
        env,
        plan_id=parameters["plan_id"],
        partner_id=parameters["partner_id"],
        company_id=company_id,
        failure_type=failure_type,
    )
    account = _scoped(env, "account.analytic.account", company_id).create(
        {
            "name": full_name,
            "plan_id": parameters["plan_id"],
            "code": parameters["code"] or False,
            "partner_id": parameters["partner_id"] or False,
            "company_id": company_id,
            "active": True,
        }
    )
    if (
        len(account) != 1
        or account.name != full_name
        or account.company_id.id != company_id
        or account.plan_id.id != parameters["plan_id"]
        or (account.code or None) != parameters["code"]
        or _relation_id(account.partner_id) != parameters["partner_id"]
        or not account.active
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo returned an invalid analytic account.",
            exit_code=6,
        )
    return _analytic_account_result(account, company_id), False


def _update_analytic_account(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    account = _search_one(
        env,
        "account.analytic.account",
        [
            ("id", "=", parameters["analytic_account_id"]),
            ("company_id", "=", company_id),
        ],
        company_id,
        failure_type,
    )
    actual = _analytic_account_values(account)
    changes = dict(parameters["changes"])
    if "name" in changes:
        changes["name"] = _name_with_preserved_marker(account.name, changes["name"])
    if "code" in changes:
        changes["code"] = changes["code"] or None
    target = {**actual, **changes}
    _validate_analytic_references(
        env,
        plan_id=account.plan_id.id,
        partner_id=target["partner_id"],
        company_id=company_id,
        failure_type=failure_type,
    )
    if actual == target:
        return _analytic_account_result(account, company_id), True
    write_values = dict(changes)
    for field_name in ("code", "partner_id"):
        if field_name in write_values and write_values[field_name] is None:
            write_values[field_name] = False
    account.write(write_values)
    if (
        account.company_id.id != company_id
        or _analytic_account_values(account) != target
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not apply the analytic-account update.",
            exit_code=6,
        )
    return _analytic_account_result(account, company_id), False


def _transition_analytic_account(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    account = _search_one(
        env,
        "account.analytic.account",
        [
            ("id", "=", parameters["analytic_account_id"]),
            ("company_id", "=", company_id),
        ],
        company_id,
        failure_type,
    )
    _analytic_plan(env, account.plan_id.id, company_id, failure_type)
    target_active = capability_id == "analytic.account.restore"
    if bool(account.active) is target_active:
        return _analytic_account_result(account, company_id), True
    account.write({"active": target_active})
    account.invalidate_recordset(["active"])
    if bool(account.active) is not target_active:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not apply the analytic-account archive state.",
            exit_code=6,
        )
    return _analytic_account_result(account, company_id), False


def _analytic_line_account(
    env: Any,
    analytic_account_id: int,
    company_id: int,
    failure_type: type[Exception],
) -> Any:
    account = _search_one(
        env,
        "account.analytic.account",
        [
            ("id", "=", analytic_account_id),
            ("company_id", "=", company_id),
        ],
        company_id,
        failure_type,
    )
    root_plan = account.root_plan_id
    if _relation_id(root_plan) is None or root_plan._column_name() != "account_id":
        raise _fail(
            failure_type,
            "business_rule_error",
            "Manual analytic lines currently support only the Project root plan.",
            exit_code=6,
        )
    return account


def _manual_analytic_line(
    env: Any,
    analytic_line_id: int,
    company_id: int,
    failure_type: type[Exception],
) -> Any:
    return _search_one(
        env,
        "account.analytic.line",
        [
            ("id", "=", analytic_line_id),
            ("company_id", "=", company_id),
            ("category", "=", "other"),
            ("move_line_id", "=", False),
            ("account_id", "!=", False),
        ],
        company_id,
        failure_type,
    )


def _analytic_line_values(line: Any) -> dict[str, Any]:
    return {
        "name": line.name,
        "date": str(line.date),
        "amount": _canonical_decimal_text(line.amount),
        "analytic_account_id": _relation_id(line.account_id),
        "reference": line.ref or None,
        "unit_amount": _canonical_decimal_text(line.unit_amount),
    }


def _analytic_line_write_values(values: dict[str, Any]) -> dict[str, Any]:
    mapped: dict[str, Any] = {}
    for field_name, value in values.items():
        target_name = {
            "analytic_account_id": "account_id",
            "reference": "ref",
        }.get(field_name, field_name)
        if field_name in {"amount", "unit_amount"}:
            mapped[target_name] = Decimal(value)
        elif field_name == "reference" and value is None:
            mapped[target_name] = False
        else:
            mapped[target_name] = value
    return mapped


def _create_analytic_line(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    key: str,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    _analytic_line_account(
        env, parameters["analytic_account_id"], company_id, failure_type
    )
    suffix = _asset_marker_suffix(company_id, key)
    full_name = f"{parameters['name']} {suffix}"
    expected = {**parameters, "name": full_name}
    existing = _scoped(env, "account.analytic.line", company_id).search(
        [
            ("company_id", "=", company_id),
            ("name", "=like", f"% {suffix}"),
        ],
        limit=2,
    )
    if existing:
        if (
            len(existing) != 1
            or existing.category != "other"
            or existing.move_line_id
            or _analytic_line_values(existing) != expected
        ):
            raise _fail(
                failure_type,
                "idempotency_conflict",
                "The analytic-line marker already has different parameters.",
                exit_code=5,
            )
        return _analytic_line_result(existing, company_id), True

    values = _analytic_line_write_values(expected)
    values.update(
        {
            "company_id": company_id,
            "category": "other",
            "move_line_id": False,
        }
    )
    line = _scoped(env, "account.analytic.line", company_id).create(values)
    if (
        len(line) != 1
        or line.company_id.id != company_id
        or line.category != "other"
        or line.move_line_id
        or _analytic_line_values(line) != expected
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo returned an invalid manual analytic line.",
            exit_code=6,
        )
    return _analytic_line_result(line, company_id), False


def _update_analytic_line(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    line = _manual_analytic_line(
        env, parameters["analytic_line_id"], company_id, failure_type
    )
    actual = _analytic_line_values(line)
    changes = dict(parameters["changes"])
    if "name" in changes:
        changes["name"] = _name_with_preserved_marker(line.name, changes["name"])
    target = {**actual, **changes}
    _analytic_line_account(
        env, target["analytic_account_id"], company_id, failure_type
    )
    if actual == target:
        return _analytic_line_result(line, company_id), True
    line.write(_analytic_line_write_values(changes))
    line.invalidate_recordset(
        [
            {
                "analytic_account_id": "account_id",
                "reference": "ref",
            }.get(field_name, field_name)
            for field_name in changes
        ]
    )
    if (
        line.company_id.id != company_id
        or line.category != "other"
        or line.move_line_id
        or _analytic_line_values(line) != target
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not apply the manual analytic-line update.",
            exit_code=6,
        )
    return _analytic_line_result(line, company_id), False


def _delete_analytic_line(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    line = _manual_analytic_line(
        env, parameters["analytic_line_id"], company_id, failure_type
    )
    result = _analytic_line_result(line, company_id, state="deleted")
    line_id = line.id
    line.unlink()
    if _scoped(env, "account.analytic.line", company_id).search_count(
        [("id", "=", line_id)], limit=1
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not delete the manual analytic line.",
            exit_code=6,
        )
    return result, False


def _compatible_account_return_type(
    env: Any,
    return_type_id: int,
    company_id: int,
    failure_type: type[Exception],
) -> tuple[Any, Any]:
    company = _search_one(
        env,
        "res.company",
        [("id", "=", company_id)],
        company_id,
        failure_type,
    )
    if getattr(company, "parent_id", False) or not company._all_branches_selected():
        raise _fail(
            failure_type,
            "configuration_missing",
            "Manual account-return creation requires a standalone root company.",
            exit_code=4,
        )
    return_type = _search_one(
        env,
        "account.return.type",
        [("id", "=", return_type_id)],
        company_id,
        failure_type,
    )
    fiscal_country_id = _relation_id(
        getattr(company, "account_fiscal_country_id", False)
    )
    return_country_id = _relation_id(getattr(return_type, "country_id", False))
    if (
        return_type.category != "account_return"
        or return_type.report_id
        or return_type.states_workflow != "generic_state_review_submit"
        or return_country_id not in {None, fiscal_country_id}
    ):
        raise _fail(
            failure_type,
            "record_not_found",
            "The return type is unavailable for this manual company workflow.",
            exit_code=4,
        )
    return company, return_type


def _manual_account_return(
    env: Any,
    return_id: int,
    company_id: int,
    failure_type: type[Exception],
) -> Any:
    account_return = _search_one(
        env,
        "account.return",
        [("id", "=", return_id), ("company_id", "=", company_id)],
        company_id,
        failure_type,
    )
    return_type = account_return.type_id
    if (
        not account_return.manually_created
        or return_type.category != "account_return"
        or return_type.report_id
        or return_type.states_workflow != "generic_state_review_submit"
    ):
        raise _fail(
            failure_type,
            "record_not_found",
            "The requested manual account return is unavailable in this workflow.",
            exit_code=4,
        )
    return account_return


def _account_return_result(
    account_return: Any,
    company_id: int,
    *,
    state: str | None = None,
) -> dict[str, Any]:
    active = bool(getattr(account_return, "active", True))
    result = {
        "model": "account.return",
        "id": account_return.id,
        "name": account_return.name or None,
        "state": state or (account_return.state if active else "archived"),
        "company_id": company_id,
        "move_type": None,
        "source_id": _relation_id(account_return.type_id),
        "line_ids": [],
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }
    assert set(result) == _RESULT_KEYS
    return result


def _account_return_check_result(check: Any, company_id: int) -> dict[str, Any]:
    result = {
        "model": "account.return.check",
        "id": check.id,
        "name": check.name or None,
        "state": check.result,
        "company_id": company_id,
        "move_type": None,
        "source_id": _relation_id(check.return_id),
        "line_ids": [],
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }
    assert set(result) == _RESULT_KEYS
    return result


def _create_account_return(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    company, return_type = _compatible_account_return_type(
        env, parameters["return_type_id"], company_id, failure_type
    )
    period_from, period_to = return_type._get_period_boundaries(
        company, date.fromisoformat(parameters["date_from"])
    )
    if (
        str(period_from) != parameters["date_from"]
        or str(period_to) != parameters["date_to"]
    ):
        raise _fail(
            failure_type,
            "business_rule_error",
            "The selected range must equal exactly one native return period.",
            exit_code=6,
        )
    model = _scoped(env, "account.return", company_id)
    natural_domain = [
        ("company_id", "=", company_id),
        ("type_id", "=", return_type.id),
        ("date_from", "=", parameters["date_from"]),
        ("date_to", "=", parameters["date_to"]),
    ]
    existing = model.search(natural_domain, limit=2)
    if existing:
        if len(existing) == 1 and existing.manually_created:
            return _account_return_result(existing, company_id), True
        raise _fail(
            failure_type,
            "idempotency_conflict",
            "Another account return already uses this company, type, and period.",
            exit_code=5,
        )

    wizard = _scoped(env, "account.return.creation.wizard", company_id).create(
        {
            "company_id": company.id,
            "category": "account_return",
            "return_type_id": return_type.id,
            "date_from": parameters["date_from"],
            "date_to": parameters["date_to"],
        }
    )
    if (
        _relation_id(wizard.company_id) != company_id
        or _relation_id(wizard.return_type_id) != return_type.id
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not retain the requested account-return creation scope.",
            exit_code=6,
        )
    wizard.action_create_manual_account_returns()
    created = model.search(natural_domain, limit=2)
    if (
        len(created) != 1
        or not created.manually_created
        or created.state != "new"
        or not bool(getattr(created, "active", True))
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not create exactly one requested manual account return.",
            exit_code=6,
        )
    return _account_return_result(created, company_id), False


def _account_return_check_fingerprint(account_return: Any) -> list[tuple[Any, ...]]:
    return sorted(
        (
            check.id,
            check.code,
            check.state,
            check.result,
            bool(check.refresh_result),
            check.records_count,
        )
        for check in account_return.check_ids
    )


def _refresh_account_return_checks(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    account_return = _manual_account_return(
        env, parameters["return_id"], company_id, failure_type
    )
    if (
        not bool(getattr(account_return, "active", True))
        or account_return.state != "new"
        or account_return.is_completed
    ):
        raise _fail(
            failure_type,
            "state_conflict",
            "Only an active new account return can refresh its checks.",
            exit_code=5,
        )
    before = _account_return_check_fingerprint(account_return)
    account_return.refresh_checks()
    account_return.invalidate_recordset(["check_ids"])
    account_return.check_ids.invalidate_recordset(
        ["code", "state", "result", "refresh_result", "records_count"]
    )
    after = _account_return_check_fingerprint(account_return)
    return _account_return_result(account_return, company_id), before == after


def _update_account_return_check_result(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    check = _search_one(
        env,
        "account.return.check",
        [("id", "=", parameters["check_id"])],
        company_id,
        failure_type,
    )
    account_return = _manual_account_return(
        env, _relation_id(check.return_id) or 0, company_id, failure_type
    )
    if (
        not bool(getattr(account_return, "active", True))
        or account_return.state != "new"
        or account_return.is_completed
        or check.state != "new"
        or check.result == "supervised"
    ):
        raise _fail(
            failure_type,
            "state_conflict",
            "Only a current unsupervised check on an active new return can change.",
            exit_code=5,
        )
    if check.result == parameters["result"]:
        return _account_return_check_result(check, company_id), True
    check.write({"result": parameters["result"]})
    check.invalidate_recordset(["result"])
    if check.result != parameters["result"]:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not update the requested account-return check result.",
            exit_code=6,
        )
    return _account_return_check_result(check, company_id), False


def _transition_account_return(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    account_return = _manual_account_return(
        env, parameters["return_id"], company_id, failure_type
    )
    active = bool(getattr(account_return, "active", True))
    if capability_id == "account.return.validate":
        if active and account_return.state in {"reviewed", "submitted"}:
            return _account_return_result(account_return, company_id), True
        if not active or account_return.state != "new" or account_return.is_completed:
            raise _fail(
                failure_type,
                "state_conflict",
                "Only an active new account return can be validated.",
                exit_code=5,
            )
        account_return.action_validate()
        account_return.invalidate_recordset(["state", "date_lock"])
        if account_return.state != "reviewed" or not account_return.date_lock:
            raise _fail(
                failure_type,
                "odoo_write_error",
                "Odoo did not validate the requested account return.",
                exit_code=6,
            )
        return _account_return_result(account_return, company_id), False

    if capability_id == "account.return.mark_submitted":
        if active and account_return.state == "submitted" and account_return.is_completed:
            return _account_return_result(account_return, company_id), True
        if not active or account_return.state != "reviewed" or account_return.is_completed:
            raise _fail(
                failure_type,
                "state_conflict",
                "Only an active reviewed account return can be marked submitted.",
                exit_code=5,
            )
        account_return.action_submit()
        account_return.invalidate_recordset(
            ["state", "date_submission", "is_completed"]
        )
        if (
            account_return.state != "submitted"
            or not account_return.date_submission
            or not account_return.is_completed
        ):
            raise _fail(
                failure_type,
                "odoo_write_error",
                "Odoo did not mark the requested account return as submitted.",
                exit_code=6,
            )
        return _account_return_result(account_return, company_id), False

    if account_return.state != "new" or account_return.is_completed:
        raise _fail(
            failure_type,
            "state_conflict",
            "Only a new incomplete account return can change archive state.",
            exit_code=5,
        )
    target_active = capability_id == "account.return.restore"
    if active == target_active:
        return _account_return_result(account_return, company_id), True
    if target_active:
        account_return.action_unarchive()
    else:
        account_return.action_archive()
    account_return.invalidate_recordset(["active"])
    if bool(account_return.active) != target_active:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not change the requested account-return archive state.",
            exit_code=6,
        )
    return _account_return_result(account_return, company_id), False


def _delete_account_return(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    account_return = _manual_account_return(
        env, parameters["return_id"], company_id, failure_type
    )
    if (
        not bool(getattr(account_return, "active", True))
        or account_return.state != "new"
        or account_return.is_completed
    ):
        raise _fail(
            failure_type,
            "state_conflict",
            "Only an active new manual account return can be deleted.",
            exit_code=5,
        )
    result = _account_return_result(account_return, company_id, state="deleted")
    return_id = account_return.id
    account_return.action_delete()
    if _scoped(env, "account.return", company_id).search_count(
        [("id", "=", return_id)], limit=1
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not delete the requested manual account return.",
            exit_code=6,
        )
    return result, False


def _product_result(template: Any, product: Any, company_id: int) -> dict[str, Any]:
    active = bool(getattr(template, "active", True)) and bool(
        getattr(product, "active", True)
    )
    result = {
        "model": "product.product",
        "id": product.id,
        "name": template.name or None,
        "state": "active" if active else "archived",
        "company_id": company_id,
        "move_type": None,
        "source_id": template.id,
        "line_ids": [],
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }
    assert set(result) == _RESULT_KEYS
    return result


def _product_category_result(category: Any, company_id: int) -> dict[str, Any]:
    result = {
        "model": "product.category",
        "id": category.id,
        "name": category.complete_name or category.name or None,
        "state": "active",
        "company_id": company_id,
        "move_type": None,
        "source_id": None,
        "line_ids": [],
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }
    assert set(result) == _RESULT_KEYS
    return result


def _fixed_product(
    env: Any,
    product_id: int,
    company_id: int,
    failure_type: type[Exception],
    *,
    require_active: bool | None = True,
) -> tuple[Any, Any]:
    product = _search_one(
        env,
        "product.product",
        [("id", "=", product_id), ("company_id", "=", company_id)],
        company_id,
        failure_type,
    )
    template = product.product_tmpl_id
    variants = template.with_context(
        active_test=False, allowed_company_ids=[company_id]
    ).product_variant_ids
    template_active = bool(getattr(template, "active", True))
    product_active = bool(getattr(product, "active", True))
    active = template_active and product_active
    if (
        _relation_id(template.company_id) != company_id
        or template.type == "combo"
        or bool(getattr(template, "is_storable", False))
        or bool(template.attribute_line_ids)
        or len(variants) != 1
        or variants.id != product.id
        or template_active is not product_active
        or require_active is not None
        and active is not require_active
    ):
        raise _fail(
            failure_type,
            "record_not_found" if require_active is not False else "state_conflict",
            "The requested simple company product is unavailable.",
            exit_code=4 if require_active is not False else 5,
        )
    return template, product


def _product_basic_values(template: Any, product: Any) -> dict[str, Any]:
    return {
        "name": template.name,
        "default_code": product.default_code or "",
        "product_type": template.type,
        "category_id": _relation_id(template.categ_id),
        "uom_id": _relation_id(template.uom_id),
        "barcode": product.barcode or None,
        "sale_ok": bool(template.sale_ok),
        "purchase_ok": bool(template.purchase_ok),
        "list_price": _canonical_decimal_text(template.list_price),
    }


def _normalized_product_create_values(parameters: dict[str, Any]) -> dict[str, Any]:
    return {
        "barcode": None,
        "sale_ok": True,
        "purchase_ok": True,
        "list_price": "0",
        **parameters,
    }


def _validate_product_references(
    env: Any,
    values: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> None:
    if "category_id" in values:
        _ensure_ids(
            env,
            "product.category",
            {values["category_id"]},
            [],
            company_id,
            failure_type,
        )
    if "uom_id" in values:
        _ensure_ids(
            env,
            "uom.uom",
            {values["uom_id"]},
            [("active", "=", True)],
            company_id,
            failure_type,
        )


def _product_write_values(values: dict[str, Any]) -> dict[str, Any]:
    mapped: dict[str, Any] = {}
    for field_name, value in values.items():
        target = {
            "product_type": "type",
            "category_id": "categ_id",
        }.get(field_name, field_name)
        if field_name == "barcode":
            value = value or False
        elif field_name == "list_price":
            value = Decimal(value)
        mapped[target] = value
    return mapped


def _find_product_by_default_code(
    env: Any, default_code: str, company_id: int
) -> Any:
    return _scoped(env, "product.product", company_id).search(
        [("company_id", "=", company_id), ("default_code", "=", default_code)],
        limit=2,
    )


def _create_product(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    expected = _normalized_product_create_values(parameters)
    _validate_product_references(env, expected, company_id, failure_type)
    existing = _find_product_by_default_code(
        env, expected["default_code"], company_id
    )
    if existing:
        if len(existing) == 1:
            template, product = _fixed_product(
                env, existing.id, company_id, failure_type
            )
            if _product_basic_values(template, product) == expected:
                return _product_result(template, product, company_id), True
        raise _fail(
            failure_type,
            "idempotency_conflict",
            "Another product already uses the requested internal reference.",
            exit_code=5,
        )
    template = _scoped(env, "product.template", company_id).create(
        {
            **_product_write_values(expected),
            "company_id": company_id,
            "active": True,
            "is_storable": False,
        }
    )
    variants = template.with_context(
        active_test=False, allowed_company_ids=[company_id]
    ).product_variant_ids
    if len(template) != 1 or len(variants) != 1:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not create exactly one simple product variant.",
            exit_code=6,
        )
    checked_template, product = _fixed_product(
        env, variants.id, company_id, failure_type
    )
    if _product_basic_values(checked_template, product) != expected:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not retain the requested product values.",
            exit_code=6,
        )
    return _product_result(checked_template, product, company_id), False


def _update_product(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    template, product = _fixed_product(
        env, parameters["product_id"], company_id, failure_type
    )
    changes = parameters["changes"]
    _validate_product_references(env, changes, company_id, failure_type)
    current = _product_basic_values(template, product)
    target = {**current, **changes}
    if target == current:
        return _product_result(template, product, company_id), True
    if target["default_code"] != current["default_code"]:
        conflicts = _find_product_by_default_code(
            env, target["default_code"], company_id
        )
        if conflicts and (len(conflicts) != 1 or conflicts.id != product.id):
            raise _fail(
                failure_type,
                "state_conflict",
                "Another product already uses the requested internal reference.",
                exit_code=5,
            )
    template.write(_product_write_values(changes))
    template.invalidate_recordset(
        [
            "name",
            "type",
            "categ_id",
            "uom_id",
            "barcode",
            "sale_ok",
            "purchase_ok",
            "list_price",
            "default_code",
            "product_variant_ids",
        ]
    )
    product.invalidate_recordset(["default_code", "barcode", "active"])
    checked_template, checked_product = _fixed_product(
        env, product.id, company_id, failure_type
    )
    if _product_basic_values(checked_template, checked_product) != target:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not retain the updated product values.",
            exit_code=6,
        )
    return _product_result(checked_template, checked_product, company_id), False


def _validate_product_policy_fields(template: Any, changes: dict[str, Any], failure_type: type[Exception]) -> None:
    if any(field in changes and field not in template._fields for field in _PRODUCT_POLICY_FIELDS):
        raise _fail(failure_type, "state_conflict", "The installed product template does not expose the requested invoicing policy.", exit_code=5)


def _duplicate_product(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    source_template, source_product = _fixed_product(
        env, parameters["product_id"], company_id, failure_type
    )
    existing = _find_product_by_default_code(
        env, parameters["default_code"], company_id
    )
    expected_common = _product_basic_values(source_template, source_product)
    expected_common.update(
        {
            "name": parameters["name"],
            "default_code": parameters["default_code"],
            "barcode": None,
        }
    )
    if existing:
        if len(existing) == 1:
            template, product = _fixed_product(
                env, existing.id, company_id, failure_type
            )
            actual = _product_basic_values(template, product)
            if actual == expected_common:
                return _product_result(template, product, company_id), True
        raise _fail(
            failure_type,
            "idempotency_conflict",
            "Another product already uses the duplicate internal reference.",
            exit_code=5,
        )
    copied_template = source_template.copy(
        default={
            "name": parameters["name"],
            "default_code": parameters["default_code"],
            "company_id": company_id,
            "active": True,
            "is_storable": False,
        }
    )
    variants = copied_template.with_context(
        active_test=False, allowed_company_ids=[company_id]
    ).product_variant_ids
    if len(copied_template) != 1 or len(variants) != 1:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not duplicate exactly one simple product variant.",
            exit_code=6,
        )
    template, product = _fixed_product(
        env, variants.id, company_id, failure_type
    )
    actual = _product_basic_values(template, product)
    if actual != expected_common:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not retain the duplicated product values.",
            exit_code=6,
        )
    return _product_result(template, product, company_id), False


def _transition_product(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    template, product = _fixed_product(
        env,
        parameters["product_id"],
        company_id,
        failure_type,
        require_active=None,
    )
    target_active = capability_id == "product.restore"
    active = bool(getattr(template, "active", True)) and bool(
        getattr(product, "active", True)
    )
    if active is target_active:
        return _product_result(template, product, company_id), True
    if target_active:
        product.action_unarchive()
    else:
        template.action_archive()
    template.invalidate_recordset(["active", "product_variant_ids"])
    product.invalidate_recordset(["active"])
    checked_template, checked_product = _fixed_product(
        env,
        product.id,
        company_id,
        failure_type,
        require_active=target_active,
    )
    return _product_result(checked_template, checked_product, company_id), False


def _update_product_cost(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    template, product = _fixed_product(
        env, parameters["product_id"], company_id, failure_type
    )
    expected = parameters["standard_price"]
    if _canonical_decimal_text(product.standard_price) == expected:
        return _product_result(template, product, company_id), True
    product.write({"standard_price": Decimal(expected)})
    product.invalidate_recordset(["standard_price"])
    if _canonical_decimal_text(product.standard_price) != expected:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not retain the requested product cost.",
            exit_code=6,
        )
    return _product_result(template, product, company_id), False


_PRODUCT_ACCOUNT_EXCLUDED_TYPES = frozenset(
    {
        "asset_receivable",
        "liability_payable",
        "asset_cash",
        "liability_credit_card",
        "off_balance",
    }
)


def _product_profile_account(
    env: Any,
    account_id: int | None,
    company_id: int,
    failure_type: type[Exception],
) -> Any:
    if account_id is None:
        return False
    account = _account_config_record(env, account_id, company_id, failure_type)
    if not bool(account.active) or account.account_type in _PRODUCT_ACCOUNT_EXCLUDED_TYPES:
        raise _fail(
            failure_type,
            "record_not_found",
            "The referenced product account is unavailable.",
            exit_code=4,
        )
    return account


def _product_accounting_profile_values(template: Any) -> dict[str, Any]:
    return {
        "income_account_id": _relation_id(template.property_account_income_id),
        "expense_account_id": _relation_id(template.property_account_expense_id),
        "sale_tax_ids": _record_ids(template.taxes_id),
        "purchase_tax_ids": _record_ids(template.supplier_taxes_id),
    }


def _update_product_accounting_profile(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    if set(parameters["changes"]) <= set(_PRODUCT_POLICY_FIELDS):
        product = _search_one(env, "product.product", [
            ("id", "=", parameters["product_id"]), ("company_id", "in", [False, company_id]),
        ], company_id, failure_type)
        template = _search_one(env, "product.template", [
            ("id", "=", product.product_tmpl_id.id), ("company_id", "in", [False, company_id]),
        ], company_id, failure_type)
        changes = parameters["changes"]
        _validate_product_policy_fields(template, changes, failure_type)
        if all(getattr(template, field) == value for field, value in changes.items()):
            return _product_result(template, product, company_id), True
        template.write(changes)
        template.invalidate_recordset(list(changes))
        if any(getattr(template, field) != value for field, value in changes.items()):
            raise _fail(failure_type, "odoo_write_error", "Odoo did not retain the template invoicing policies.", exit_code=6)
        return _product_result(template, product, company_id), False
    template, product = _fixed_product(
        env, parameters["product_id"], company_id, failure_type
    )
    template = template.with_company(company_id)
    changes = parameters["changes"]
    _validate_product_policy_fields(template, changes, failure_type)
    write_values: dict[str, Any] = {field: changes[field] for field in _PRODUCT_POLICY_FIELDS if field in changes}
    for source, target in (
        ("income_account_id", "property_account_income_id"),
        ("expense_account_id", "property_account_expense_id"),
    ):
        if source in changes:
            account = _product_profile_account(
                env, changes[source], company_id, failure_type
            )
            write_values[target] = account.id if account else False
    for source, target, tax_use in (
        ("sale_tax_ids", "taxes_id", "sale"),
        ("purchase_tax_ids", "supplier_taxes_id", "purchase"),
    ):
        if source in changes:
            _ensure_ids(
                env,
                "account.tax",
                set(changes[source]),
                [
                    ("company_id", "=", company_id),
                    ("type_tax_use", "=", tax_use),
                    ("active", "=", True),
                ],
                company_id,
                failure_type,
            )
            write_values[target] = [(6, 0, changes[source])]
    current = _product_accounting_profile_values(template)
    current.update({field: getattr(template, field) for field in _PRODUCT_POLICY_FIELDS if field in changes})
    target_values = {**current, **changes}
    if target_values == current:
        return _product_result(template, product, company_id), True
    template.write(write_values)
    template.invalidate_recordset(
        [
            "property_account_income_id",
            "property_account_expense_id",
            "taxes_id",
            "supplier_taxes_id",
        ] + [field for field in _PRODUCT_POLICY_FIELDS if field in changes]
    )
    actual = _product_accounting_profile_values(template)
    actual.update({field: getattr(template, field) for field in _PRODUCT_POLICY_FIELDS if field in changes})
    if actual != target_values:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not retain the product accounting profile.",
            exit_code=6,
        )
    return _product_result(template, product, company_id), False


def _product_category_accounting_profile_values(category: Any) -> dict[str, Any]:
    return {
        "income_account_id": _relation_id(
            category.property_account_income_categ_id
        ),
        "expense_account_id": _relation_id(
            category.property_account_expense_categ_id
        ),
    }


def _update_product_category_accounting_profile(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    category = _search_one(
        env,
        "product.category",
        [("id", "=", parameters["category_id"])],
        company_id,
        failure_type,
    ).with_company(company_id)
    changes = parameters["changes"]
    write_values: dict[str, Any] = {}
    for source, target in (
        ("income_account_id", "property_account_income_categ_id"),
        ("expense_account_id", "property_account_expense_categ_id"),
    ):
        if source in changes:
            account = _product_profile_account(
                env, changes[source], company_id, failure_type
            )
            write_values[target] = account.id if account else False
    current = _product_category_accounting_profile_values(category)
    target_values = {**current, **changes}
    if target_values == current:
        return _product_category_result(category, company_id), True
    category.write(write_values)
    category.invalidate_recordset(
        ["property_account_income_categ_id", "property_account_expense_categ_id"]
    )
    if _product_category_accounting_profile_values(category) != target_values:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not retain the category accounting profile.",
            exit_code=6,
        )
    return _product_category_result(category, company_id), False


def _budget_values(budget: Any) -> dict[str, Any]:
    return {
        "name": budget.name,
        "date_from": str(budget.date_from),
        "date_to": str(budget.date_to),
        "budget_type": budget.budget_type,
    }


def _create_budget(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    key: str,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    suffix = _asset_marker_suffix(company_id, key)
    full_name = f"{parameters['name']} {suffix}"
    existing = _scoped(env, "budget.analytic", company_id).search(
        [("company_id", "=", company_id), ("name", "=like", f"% {suffix}")],
        limit=2,
    )
    if existing:
        expected = {**parameters, "name": full_name}
        if (
            len(existing) != 1
            or existing.company_id.id != company_id
            or _relation_id(existing.user_id) != env.uid
            or _budget_values(existing) != expected
        ):
            raise _fail(
                failure_type,
                "idempotency_conflict",
                "The budget marker already has different parameters.",
                exit_code=5,
            )
        return _budget_result(existing, company_id), True

    budget = _scoped(env, "budget.analytic", company_id).create(
        {
            **parameters,
            "name": full_name,
            "company_id": company_id,
            "user_id": env.uid,
            "state": "draft",
        }
    )
    expected = {**parameters, "name": full_name}
    if (
        len(budget) != 1
        or budget.company_id.id != company_id
        or _relation_id(budget.user_id) != env.uid
        or budget.state != "draft"
        or budget.budget_line_ids
        or _budget_values(budget) != expected
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo returned an invalid draft budget.",
            exit_code=6,
        )
    return _budget_result(budget, company_id), False


def _budget(
    env: Any,
    budget_id: int,
    company_id: int,
    failure_type: type[Exception],
) -> Any:
    return _search_one(
        env,
        "budget.analytic",
        [("id", "=", budget_id), ("company_id", "=", company_id)],
        company_id,
        failure_type,
    )


def _update_draft_budget(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    budget = _budget(env, parameters["budget_id"], company_id, failure_type)
    if budget.state != "draft":
        raise _fail(
            failure_type,
            "state_conflict",
            "Only a draft budget can be updated.",
            exit_code=5,
        )
    actual = _budget_values(budget)
    changes = dict(parameters["changes"])
    if "name" in changes:
        changes["name"] = _name_with_preserved_marker(budget.name, changes["name"])
    target = {**actual, **changes}
    if target["date_from"] > target["date_to"]:
        raise _fail(
            failure_type,
            "state_conflict",
            "The budget start date cannot be after its end date.",
            exit_code=5,
        )
    if actual == target:
        return _budget_result(budget, company_id), True
    budget.write(changes)
    if (
        budget.state != "draft"
        or budget.company_id.id != company_id
        or _budget_values(budget) != target
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not apply the draft-budget update.",
            exit_code=6,
        )
    return _budget_result(budget, company_id), False


def _budget_line_columns(model: Any) -> set[str]:
    fields = getattr(model, "_fields", {})
    if not isinstance(fields, Mapping):
        return set()
    return {
        field_name
        for field_name, field in fields.items()
        if getattr(field, "comodel_name", None) == "account.analytic.account"
    }


def _budget_line_account_columns(
    env: Any,
    lines: list[dict[str, Any]],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[int, str], set[str]]:
    requested_ids = {
        account_id for line in lines for account_id in line["analytic_account_ids"]
    }
    accounts = _ensure_ids(
        env,
        "account.analytic.account",
        requested_ids,
        [("company_id", "in", [False, company_id])],
        company_id,
        failure_type,
    )
    account_by_id = {account.id: account for account in accounts}
    plan_ids: set[int] = set()
    root_id_by_account: dict[int, int] = {}
    for account in accounts:
        plan_id = _relation_id(account.plan_id)
        root_id = _relation_id(getattr(account, "root_plan_id", False))
        if plan_id is None or root_id is None:
            raise _fail(
                failure_type,
                "business_rule_error",
                "An analytic account has no usable root plan.",
                exit_code=6,
            )
        plan_ids.update({plan_id, root_id})
        root_id_by_account[account.id] = root_id
    plans = _ensure_ids(
        env,
        "account.analytic.plan",
        plan_ids,
        [],
        company_id,
        failure_type,
    )
    plan_by_id = {plan.id: plan for plan in plans}
    model = _scoped(env, "budget.line", company_id)
    available_columns = _budget_line_columns(model)
    column_by_account: dict[int, str] = {}
    for account_id, root_id in root_id_by_account.items():
        column_name = plan_by_id[root_id]._column_name()
        if not isinstance(column_name, str) or column_name not in available_columns:
            raise _fail(
                failure_type,
                "configuration_missing",
                "The analytic root plan has no budget-line column.",
                exit_code=4,
            )
        column_by_account[account_id] = column_name
    for line in lines:
        columns = [
            column_by_account[account_id] for account_id in line["analytic_account_ids"]
        ]
        if len(columns) != len(set(columns)):
            raise _fail(
                failure_type,
                "business_rule_error",
                "A budget line cannot contain two accounts from one root plan.",
                exit_code=6,
            )
    if set(account_by_id) != requested_ids:
        raise AssertionError("analytic account lookup lost an id")
    return column_by_account, available_columns


def _budget_line_signature(
    line: Any, analytic_columns: set[str]
) -> tuple[str, tuple[int, ...]]:
    account_ids = sorted(
        account_id
        for column_name in analytic_columns
        if (account_id := _relation_id(getattr(line, column_name, False))) is not None
    )
    return _canonical_decimal_text(line.budget_amount), tuple(account_ids)


def _current_budget_lines(
    budget: Any, analytic_columns: set[str]
) -> list[tuple[str, tuple[int, ...]]]:
    ordered = sorted(budget.budget_line_ids, key=lambda line: (line.sequence, line.id))
    return [_budget_line_signature(line, analytic_columns) for line in ordered]


def _requested_budget_lines(
    lines: list[dict[str, Any]],
) -> list[tuple[str, tuple[int, ...]]]:
    return [
        (
            _canonical_decimal_text(line["budget_amount"]),
            tuple(line["analytic_account_ids"]),
        )
        for line in lines
    ]


def _replace_budget_lines(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    budget = _budget(env, parameters["budget_id"], company_id, failure_type)
    if budget.state != "draft":
        raise _fail(
            failure_type,
            "state_conflict",
            "Only a draft budget can have its lines replaced.",
            exit_code=5,
        )
    lines = parameters["lines"]
    column_by_account, analytic_columns = _budget_line_account_columns(
        env, lines, company_id, failure_type
    )
    expected = _requested_budget_lines(lines)
    if _current_budget_lines(budget, analytic_columns) == expected:
        return _budget_result(budget, company_id), True

    create_values = []
    for index, line in enumerate(lines, start=1):
        values: dict[str, Any] = {
            "sequence": index * 10,
            "budget_analytic_id": budget.id,
            "budget_amount": Decimal(line["budget_amount"]),
        }
        values.update(
            {
                column_by_account[account_id]: account_id
                for account_id in line["analytic_account_ids"]
            }
        )
        create_values.append(values)

    budget.budget_line_ids.unlink()
    created = _scoped(env, "budget.line", company_id).create(create_values)
    budget.invalidate_recordset(["budget_line_ids"])
    if (
        len(created) != len(lines)
        or budget.state != "draft"
        or set(created.ids) != set(budget.budget_line_ids.ids)
        or _current_budget_lines(budget, analytic_columns) != expected
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not apply the budget-line replacement.",
            exit_code=6,
        )
    return _budget_result(budget, company_id), False


def _transition_budget(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    budget = _budget(env, parameters["budget_id"], company_id, failure_type)
    if capability_id == "budget.confirm":
        if budget.state in {"confirmed", "revised"}:
            return _budget_result(budget, company_id), True
        if budget.state != "draft":
            raise _fail(
                failure_type,
                "state_conflict",
                "Only a draft budget can be confirmed.",
                exit_code=5,
            )
        budget.action_budget_confirm()
        expected_state = "revised" if budget.children_ids else "confirmed"
    elif capability_id == "budget.reset_to_draft":
        if budget.state == "draft":
            return _budget_result(budget, company_id), True
        budget.action_budget_draft()
        expected_state = "draft"
    elif capability_id == "budget.cancel":
        if budget.state == "canceled":
            return _budget_result(budget, company_id), True
        if budget.state != "draft":
            raise _fail(
                failure_type,
                "state_conflict",
                "Only a draft budget can be canceled.",
                exit_code=5,
            )
        budget.action_budget_cancel()
        expected_state = "canceled"
    else:
        if budget.state == "done":
            return _budget_result(budget, company_id), True
        if budget.state != "confirmed":
            raise _fail(
                failure_type,
                "state_conflict",
                "Only a confirmed budget can be marked done.",
                exit_code=5,
            )
        budget.action_budget_done()
        expected_state = "done"
    budget.invalidate_recordset(["state", "budget_line_ids"])
    if budget.state != expected_state:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not apply the requested budget transition.",
            exit_code=6,
        )
    return _budget_result(budget, company_id), False


def _partner_scope_domain(company_id: int) -> list[Any]:
    return [
        "|",
        ("company_id", "=", False),
        ("company_id", "=", company_id),
    ]


def _partner(
    env: Any,
    partner_id: int,
    company_id: int,
    failure_type: type[Exception],
) -> Any:
    return _search_one(
        env,
        "res.partner",
        [("id", "=", partner_id), *_partner_scope_domain(company_id)],
        company_id,
        failure_type,
    )


def _partner_result(partner: Any, company_id: int) -> dict[str, Any]:
    result = {
        "model": "res.partner",
        "id": partner.id,
        "name": partner.name or None,
        "state": "active" if partner.active else "archived",
        "company_id": company_id,
        "move_type": None,
        "source_id": None,
        "line_ids": [],
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }
    assert set(result) == _RESULT_KEYS
    return result


def _partner_bank_result(bank: Any, company_id: int) -> dict[str, Any]:
    result = {
        "model": "res.partner.bank",
        "id": bank.id,
        "name": bank.acc_number or None,
        "state": "active" if bank.active else "archived",
        "company_id": company_id,
        "move_type": None,
        "source_id": bank.partner_id.id,
        "line_ids": [],
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }
    assert set(result) == _RESULT_KEYS
    return result


def _false_to_none(value: Any) -> Any:
    return None if value is False else value


def _business_partner_reference(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    business_value = _PARTNER_REF_MARKER_SUFFIX.sub("", value).rstrip()
    return business_value or None


def _partner_reference_marker(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    match = _PARTNER_REF_MARKER_SUFFIX.search(value)
    return match.group(0).lstrip() if match else None


def _partner_reference_value(value: str | None, marker: str | None) -> Any:
    if marker is None:
        return value or False
    return f"{value} {marker}" if value else marker


def _validate_partner_geography(
    env: Any,
    state_id: int | None,
    country_id: int | None,
    company_id: int,
    failure_type: type[Exception],
) -> None:
    state = None
    if state_id is not None:
        state = _ensure_ids(
            env,
            "res.country.state",
            {state_id},
            [],
            company_id,
            failure_type,
        )
    if country_id is not None:
        _ensure_ids(
            env,
            "res.country",
            {country_id},
            [],
            company_id,
            failure_type,
        )
    if (
        state is not None
        and country_id is not None
        and state.country_id.id != country_id
    ):
        raise _fail(
            failure_type,
            "business_rule_error",
            "The partner state does not belong to the selected country.",
            exit_code=6,
        )


def _partner_contact_values(
    values: dict[str, Any],
    *,
    reference_marker: str | None = None,
    model: Any = None,
) -> dict[str, Any]:
    field_names = {
        "name": "name",
        "company_type": "company_type",
        "vat": "vat",
        "email": "email",
        "phone": "phone",
        "mobile": "mobile",
        "street": "street",
        "street2": "street2",
        "city": "city",
        "zip": "zip",
        "state_id": "state_id",
        "country_id": "country_id",
        "language": "lang",
    }
    available_fields = getattr(model, "_fields", None)
    result = {
        odoo_name: value if value is not None else False
        for public_name, odoo_name in field_names.items()
        if public_name in values
        and (not isinstance(available_fields, Mapping) or odoo_name in available_fields)
        for value in [values[public_name]]
    }
    if "reference" in values:
        result["ref"] = _partner_reference_value(values["reference"], reference_marker)
    return result


def _partner_matches_contact_values(
    partner: Any,
    values: dict[str, Any],
    company_id: int,
    *,
    require_active: bool = False,
    require_company_exact: bool = False,
) -> bool:
    comparisons = {
        "name": partner.name,
        "company_type": partner.company_type,
        "vat": _false_to_none(partner.vat),
        "reference": _business_partner_reference(partner.ref),
        "email": _false_to_none(partner.email),
        "phone": _false_to_none(partner.phone),
        "mobile": _false_to_none(getattr(partner, "mobile", False)),
        "street": _false_to_none(partner.street),
        "street2": _false_to_none(partner.street2),
        "city": _false_to_none(partner.city),
        "zip": _false_to_none(partner.zip),
        "state_id": _relation_id(partner.state_id),
        "country_id": _relation_id(partner.country_id),
        "language": _false_to_none(partner.lang),
    }
    partner_company_id = _relation_id(partner.company_id)
    return bool(
        partner_company_id in {None, company_id}
        and (not require_company_exact or partner_company_id == company_id)
        and (not require_active or partner.active)
        and all(comparisons[name] == value for name, value in values.items())
    )


def _create_partner(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    key: str,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    suffix = _asset_marker_suffix(company_id, key)
    model = _scoped(env, "res.partner", company_id)
    available_fields = getattr(model, "_fields", None)
    if (
        isinstance(available_fields, Mapping)
        and "mobile" not in available_fields
        and parameters["mobile"] is not None
    ):
        raise _fail(
            failure_type,
            "configuration_missing",
            "The optional partner mobile field is unavailable.",
            exit_code=4,
        )
    existing = model.search([("ref", "=like", f"%{suffix}")], limit=2)
    if existing:
        if len(existing) != 1 or not _partner_matches_contact_values(
            existing,
            parameters,
            company_id,
            require_active=True,
            require_company_exact=True,
        ):
            raise _fail(
                failure_type,
                "idempotency_conflict",
                "The partner marker already exists with different parameters.",
                exit_code=5,
            )
        return _partner_result(existing, company_id), True

    _validate_partner_geography(
        env,
        parameters["state_id"],
        parameters["country_id"],
        company_id,
        failure_type,
    )
    values = _partner_contact_values(parameters, reference_marker=suffix, model=model)
    values.update({"company_id": company_id, "active": True})
    partner = model.create(values)
    if not _partner_matches_contact_values(
        partner,
        parameters,
        company_id,
        require_active=True,
        require_company_exact=True,
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not create the requested partner.",
            exit_code=6,
        )
    return _partner_result(partner, company_id), False


def _update_partner(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    partner = _partner(env, parameters["partner_id"], company_id, failure_type)
    changes = parameters["changes"]
    model = _scoped(env, "res.partner", company_id)
    available_fields = getattr(model, "_fields", None)
    if (
        isinstance(available_fields, Mapping)
        and "mobile" not in available_fields
        and changes.get("mobile") is not None
    ):
        raise _fail(
            failure_type,
            "configuration_missing",
            "The optional partner mobile field is unavailable.",
            exit_code=4,
        )
    if _partner_matches_contact_values(partner, changes, company_id):
        return _partner_result(partner, company_id), True

    state_id = changes.get("state_id", _relation_id(partner.state_id))
    country_id = changes.get("country_id", _relation_id(partner.country_id))
    _validate_partner_geography(env, state_id, country_id, company_id, failure_type)
    marker = _partner_reference_marker(partner.ref)
    partner.write(
        _partner_contact_values(changes, reference_marker=marker, model=model)
    )
    partner.invalidate_recordset()
    if not _partner_matches_contact_values(partner, changes, company_id):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not update the requested partner fields.",
            exit_code=6,
        )
    return _partner_result(partner, company_id), False


def _transition_partner(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    partner = _partner(env, parameters["partner_id"], company_id, failure_type)
    target_active = capability_id == "partner.restore"
    if partner.active is target_active:
        return _partner_result(partner, company_id), True
    if target_active:
        partner.action_unarchive()
    else:
        partner.action_archive()
    partner.invalidate_recordset(["active"])
    if partner.active is not target_active:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not apply the partner archive state.",
            exit_code=6,
        )
    return _partner_result(partner, company_id), False


def _validate_partner_accounting_references(
    env: Any,
    changes: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> None:
    account_types = {
        "property_account_receivable_id": "asset_receivable",
        "property_account_payable_id": "liability_payable",
    }
    for field_name, account_type in account_types.items():
        account_id = changes.get(field_name)
        if account_id is not None:
            _ensure_ids(
                env,
                "account.account",
                {account_id},
                [
                    ("company_ids", "in", [company_id]),
                    ("account_type", "=", account_type),
                    ("active", "=", True),
                ],
                company_id,
                failure_type,
            )
    fiscal_position_id = changes.get("property_account_position_id")
    if fiscal_position_id is not None:
        _ensure_ids(
            env,
            "account.fiscal.position",
            {fiscal_position_id},
            [("company_id", "=", company_id), ("active", "=", True)],
            company_id,
            failure_type,
        )
    for field_name in (
        "property_payment_term_id",
        "property_supplier_payment_term_id",
    ):
        payment_term_id = changes.get(field_name)
        if payment_term_id is not None:
            _ensure_ids(
                env,
                "account.payment.term",
                {payment_term_id},
                [
                    "|",
                    ("company_id", "=", False),
                    ("company_id", "=", company_id),
                    ("active", "=", True),
                ],
                company_id,
                failure_type,
            )


def _update_partner_accounting(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    partner = _partner(env, parameters["partner_id"], company_id, failure_type)
    if _relation_id(partner.commercial_partner_id) != partner.id:
        raise _fail(
            failure_type,
            "business_rule_error",
            "Accounting properties must be set on the commercial partner.",
            exit_code=6,
        )
    company = _scoped(env, "res.company", company_id).browse(company_id)
    partner = partner.with_company(company)
    changes = parameters["changes"]
    if all(
        _relation_id(getattr(partner, field_name)) == value
        for field_name, value in changes.items()
    ):
        return _partner_result(partner, company_id), True
    _validate_partner_accounting_references(env, changes, company_id, failure_type)
    partner.write(
        {
            field_name: value if value is not None else False
            for field_name, value in changes.items()
        }
    )
    partner.invalidate_recordset(list(changes))
    if any(
        _relation_id(getattr(partner, field_name)) != value
        for field_name, value in changes.items()
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not update the partner accounting properties.",
            exit_code=6,
        )
    return _partner_result(partner, company_id), False


def _partner_bank(
    env: Any,
    bank_id: int,
    company_id: int,
    failure_type: type[Exception],
) -> Any:
    return _search_one(
        env,
        "res.partner.bank",
        [
            ("id", "=", bank_id),
            ("partner_id.company_id", "in", [False, company_id]),
            "|",
            ("company_id", "=", False),
            ("company_id", "=", company_id),
        ],
        company_id,
        failure_type,
    )


def _sanitized_account_number(value: str) -> str:
    return re.sub(r"\W+", "", value).upper()


def _validate_partner_bank_references(
    env: Any,
    values: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> None:
    bank_id = values.get("bank_id")
    if bank_id is not None:
        _ensure_ids(
            env,
            "res.bank",
            {bank_id},
            [("active", "=", True)],
            company_id,
            failure_type,
        )
    currency_id = values.get("currency_id")
    if currency_id is not None:
        _ensure_ids(
            env,
            "res.currency",
            {currency_id},
            [("active", "=", True)],
            company_id,
            failure_type,
        )


def _partner_bank_matches(
    bank: Any,
    values: dict[str, Any],
    *,
    partner_id: int | None = None,
    null_holder_name: str | None = None,
    require_active: bool = False,
    require_out_payment_disabled: bool = False,
) -> bool:
    expected_holder = values.get("account_holder_name")
    if "account_holder_name" in values and expected_holder is None:
        expected_holder = null_holder_name
    comparisons = {
        "account_number": _sanitized_account_number(bank.acc_number),
        "account_holder_name": _false_to_none(bank.acc_holder_name),
        "bank_id": _relation_id(bank.bank_id),
        "currency_id": _relation_id(bank.currency_id),
    }
    expected = dict(values)
    if "account_number" in expected:
        expected["account_number"] = _sanitized_account_number(
            expected["account_number"]
        )
    if "account_holder_name" in expected:
        expected["account_holder_name"] = expected_holder
    return bool(
        (partner_id is None or bank.partner_id.id == partner_id)
        and (not require_active or bank.active)
        and (not require_out_payment_disabled or not bank.allow_out_payment)
        and all(comparisons[name] == value for name, value in expected.items())
    )


def _partner_bank_values(values: dict[str, Any]) -> dict[str, Any]:
    field_names = {
        "account_number": "acc_number",
        "account_holder_name": "acc_holder_name",
        "bank_id": "bank_id",
        "currency_id": "currency_id",
    }
    return {
        odoo_name: value if value is not None else False
        for public_name, odoo_name in field_names.items()
        if public_name in values
        for value in [values[public_name]]
    }


def _create_partner_bank(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    partner = _partner(env, parameters["partner_id"], company_id, failure_type)
    existing = _scoped(env, "res.partner.bank", company_id).search(
        [
            ("partner_id", "=", partner.id),
            ("acc_number", "=", parameters["account_number"]),
        ],
        limit=2,
    )
    values = {name: parameters[name] for name in _PARTNER_BANK_KEYS}
    if existing:
        if len(existing) != 1 or not _partner_bank_matches(
            existing,
            values,
            partner_id=partner.id,
            null_holder_name=partner.name,
            require_active=True,
            require_out_payment_disabled=True,
        ):
            raise _fail(
                failure_type,
                "idempotency_conflict",
                "The partner bank account already exists with other parameters.",
                exit_code=5,
            )
        return _partner_bank_result(existing, company_id), True
    _validate_partner_bank_references(env, values, company_id, failure_type)
    create_values = _partner_bank_values(values)
    if parameters["account_holder_name"] is None:
        create_values.pop("acc_holder_name")
    create_values.update(
        {
            "partner_id": partner.id,
            "active": True,
            "allow_out_payment": False,
        }
    )
    bank = _scoped(env, "res.partner.bank", company_id).create(create_values)
    if not _partner_bank_matches(
        bank,
        values,
        partner_id=partner.id,
        null_holder_name=partner.name,
        require_active=True,
        require_out_payment_disabled=True,
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not create the requested partner bank account.",
            exit_code=6,
        )
    return _partner_bank_result(bank, company_id), False


def _update_partner_bank(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    bank = _partner_bank(env, parameters["partner_bank_id"], company_id, failure_type)
    changes = parameters["changes"]
    if _partner_bank_matches(bank, changes):
        return _partner_bank_result(bank, company_id), True
    _validate_partner_bank_references(env, changes, company_id, failure_type)
    bank.write(_partner_bank_values(changes))
    bank.invalidate_recordset()
    if not _partner_bank_matches(bank, changes):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not update the requested partner bank account.",
            exit_code=6,
        )
    return _partner_bank_result(bank, company_id), False


def _transition_partner_bank(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    bank = _partner_bank(env, parameters["partner_bank_id"], company_id, failure_type)
    target_active = capability_id == "partner.bank_account.restore"
    if bank.active is target_active:
        return _partner_bank_result(bank, company_id), True
    if target_active:
        bank.action_unarchive()
    else:
        bank.action_archive()
    bank.invalidate_recordset(["active"])
    if bank.active is not target_active:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not apply the bank-account archive state.",
            exit_code=6,
        )
    return _partner_bank_result(bank, company_id), False


def _config_result(record: Any, model: str, company_id: int) -> dict[str, Any]:
    result = {
        "model": model,
        "id": record.id,
        "name": getattr(record, "name", False) or None,
        "state": "active" if getattr(record, "active", True) else "archived",
        "company_id": company_id,
        "move_type": None,
        "source_id": None,
        "line_ids": [],
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }
    assert set(result) == _RESULT_KEYS
    return result


def _account_is_single_company(env: Any, account_id: int, company_id: int) -> bool:
    from odoo.fields import Domain

    # company_ids values hide inaccessible companies; only inspect the relation
    # predicate, without reading foreign company records or elevating the user.
    domain = Domain("id", "=", account_id) & Domain("company_ids", "in", [company_id])
    domain &= Domain("company_ids", "not any!", Domain("id", "!=", company_id))
    return bool(_scoped(env, "account.account", company_id).search_count(domain, limit=1))


def _account_config_record(
    env: Any,
    account_id: int,
    company_id: int,
    failure_type: type[Exception],
) -> Any:
    account = _search_one(
        env,
        "account.account",
        [
            ("id", "=", account_id),
            ("company_ids", "in", [company_id]),
        ],
        company_id,
        failure_type,
    )
    if not _account_is_single_company(env, account.id, company_id):
        raise _fail(
            failure_type,
            "record_not_found",
            "The requested account is not isolated to the company.",
            exit_code=4,
        )
    return account


def _journal_config_record(
    env: Any,
    journal_id: int,
    company_id: int,
    failure_type: type[Exception],
) -> Any:
    return _search_one(
        env,
        "account.journal",
        [("id", "=", journal_id), ("company_id", "=", company_id)],
        company_id,
        failure_type,
    )


def _tax_config_record(
    env: Any,
    tax_id: int,
    company_id: int,
    failure_type: type[Exception],
) -> Any:
    return _search_one(
        env,
        "account.tax",
        [("id", "=", tax_id), ("company_id", "=", company_id)],
        company_id,
        failure_type,
    )


def _validate_currency_reference(
    env: Any,
    currency_id: int | None,
    company_id: int,
    failure_type: type[Exception],
) -> None:
    if currency_id is not None:
        _ensure_ids(
            env,
            "res.currency",
            {currency_id},
            [("active", "=", True)],
            company_id,
            failure_type,
        )


def _account_config_matches(
    account: Any,
    values: dict[str, Any],
    company_id: int,
    *,
    exact_company: bool = False,
) -> bool:
    comparisons = {
        "code": account.code,
        "name": account.name,
        "account_type": account.account_type,
        "reconcile": account.reconcile,
        "currency_id": _relation_id(account.currency_id),
    }
    company_ids = set(_record_ids(account.company_ids))
    return bool(
        company_id in company_ids
        and (not exact_company or company_ids == {company_id})
        and all(comparisons[name] == value for name, value in values.items())
    )


def _account_config_values(values: dict[str, Any]) -> dict[str, Any]:
    result = dict(values)
    if "currency_id" in result and result["currency_id"] is None:
        result["currency_id"] = False
    return result


def _create_account_config(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    _validate_currency_reference(
        env, parameters["currency_id"], company_id, failure_type
    )
    model = _scoped(env, "account.account", company_id)
    existing = model.search(
        [
            ("company_ids", "in", [company_id]),
            ("code", "=", parameters["code"]),
        ],
        limit=2,
    )
    if existing:
        if len(existing) != 1 or not _account_is_single_company(env, existing.id, company_id) or not _account_config_matches(
            existing, parameters, company_id, exact_company=True
        ):
            raise _fail(
                failure_type,
                "idempotency_conflict",
                "The account code already exists with different configuration.",
                exit_code=5,
            )
        return _config_result(existing, "account.account", company_id), True

    values = _account_config_values(parameters)
    values["company_ids"] = [(6, 0, [company_id])]
    account = model.create(values)
    if not _account_is_single_company(env, account.id, company_id) or not _account_config_matches(account, parameters, company_id, exact_company=True):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not create the requested account.",
            exit_code=6,
        )
    return _config_result(account, "account.account", company_id), False


def _update_account_config(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    account = _account_config_record(
        env, parameters["account_id"], company_id, failure_type
    )
    changes = parameters["changes"]
    if _account_config_matches(account, changes, company_id):
        return _config_result(account, "account.account", company_id), True
    _validate_currency_reference(
        env, changes.get("currency_id"), company_id, failure_type
    )
    if "code" in changes and changes["code"] != account.code:
        candidates = _scoped(env, "account.account", company_id).search(
            [
                ("company_ids", "in", [company_id]),
                ("code", "=", changes["code"]),
            ],
            limit=2,
        )
        if any(candidate.id != account.id for candidate in candidates):
            raise _fail(
                failure_type,
                "idempotency_conflict",
                "The requested account code is already in use.",
                exit_code=5,
            )
    account.write(_account_config_values(changes))
    account.invalidate_recordset(list(changes))
    if not _account_config_matches(account, changes, company_id):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not update the requested account fields.",
            exit_code=6,
        )
    return _config_result(account, "account.account", company_id), False


def _validate_journal_references(
    env: Any,
    values: dict[str, Any],
    journal_type: str,
    company_id: int,
    failure_type: type[Exception],
) -> None:
    _validate_currency_reference(
        env, values.get("currency_id"), company_id, failure_type
    )
    account_id = values.get("default_account_id")
    if account_id is not None:
        _ensure_ids(
            env,
            "account.account",
            {account_id},
            [
                ("company_ids", "in", [company_id]),
                (
                    "account_type",
                    "in",
                    sorted(_JOURNAL_DEFAULT_ACCOUNT_TYPES[journal_type]),
                ),
                ("active", "=", True),
            ],
            company_id,
            failure_type,
        )


def _journal_matches(
    journal: Any,
    values: dict[str, Any],
    *,
    creating: bool = False,
) -> bool:
    comparisons = {
        "name": journal.name,
        "code": journal.code,
        "type": journal.type,
        "sequence": journal.sequence,
        "currency_id": _relation_id(journal.currency_id),
        "default_account_id": _relation_id(journal.default_account_id),
    }
    expected = dict(values)
    if expected.get("sequence") is None and "sequence" in expected:
        expected["sequence"] = 10
    if (
        creating
        and expected.get("default_account_id") is None
        and "default_account_id" in expected
    ):
        expected.pop("default_account_id")
    return all(comparisons[name] == value for name, value in expected.items())


def _journal_values(values: dict[str, Any]) -> dict[str, Any]:
    result = dict(values)
    if result.get("sequence") is None:
        result.pop("sequence", None)
    for field_name in ("currency_id", "default_account_id"):
        if field_name in result and result[field_name] is None:
            result[field_name] = False
    return result


def _create_journal_config(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    _validate_journal_references(
        env, parameters, parameters["type"], company_id, failure_type
    )
    model = _scoped(env, "account.journal", company_id)
    existing = model.search(
        [("company_id", "=", company_id), ("code", "=", parameters["code"])],
        limit=2,
    )
    if existing:
        if len(existing) != 1 or not _journal_matches(
            existing, parameters, creating=True
        ):
            raise _fail(
                failure_type,
                "idempotency_conflict",
                "The journal code already exists with different configuration.",
                exit_code=5,
            )
        return _config_result(existing, "account.journal", company_id), True

    values = _journal_values(parameters)
    values.update({"company_id": company_id, "active": True})
    journal = model.create(values)
    if journal.company_id.id != company_id or not _journal_matches(
        journal, parameters, creating=True
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not create the requested journal.",
            exit_code=6,
        )
    return _config_result(journal, "account.journal", company_id), False


def _update_journal_config(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    journal = _journal_config_record(
        env, parameters["journal_id"], company_id, failure_type
    )
    changes = parameters["changes"]
    if _journal_matches(journal, changes):
        return _config_result(journal, "account.journal", company_id), True
    _validate_journal_references(env, changes, journal.type, company_id, failure_type)
    if "code" in changes and changes["code"] != journal.code:
        candidates = _scoped(env, "account.journal", company_id).search(
            [("company_id", "=", company_id), ("code", "=", changes["code"])],
            limit=2,
        )
        if any(candidate.id != journal.id for candidate in candidates):
            raise _fail(
                failure_type,
                "idempotency_conflict",
                "The requested journal code is already in use.",
                exit_code=5,
            )
    journal.write(_journal_values(changes))
    journal.invalidate_recordset(list(changes))
    if not _journal_matches(journal, changes):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not update the requested journal fields.",
            exit_code=6,
        )
    return _config_result(journal, "account.journal", company_id), False


def _validate_tax_references(
    env: Any,
    values: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
    *,
    tax: Any = None,
) -> None:
    tax_group_id = values.get("tax_group_id")
    if tax_group_id is not None:
        _ensure_ids(
            env,
            "account.tax.group",
            {tax_group_id},
            [("company_id", "=", company_id)],
            company_id,
            failure_type,
        )
    if set(values) & {"children_tax_ids", "type_tax_use", "tax_scope"}:
        children = values.get("children_tax_ids", _record_ids(getattr(tax, "children_tax_ids", [])))
        if tax is not None and tax.id in children:
            raise _fail(failure_type, "business_rule_error", "A tax cannot be its own child.", exit_code=6)
        tax_use = values.get("type_tax_use", getattr(tax, "type_tax_use", "sale"))
        scope = values.get("tax_scope", getattr(tax, "tax_scope", False)) or False
        if children:
            _ensure_ids(env, "account.tax", set(children), [
                ("company_id", "parent_of", [company_id]),
                ("type_tax_use", "in", ["none", tax_use]),
                ("tax_scope", "in", [False, scope]),
                ("amount_type", "!=", "group"),
            ], company_id, failure_type)
    if set(values) & {"tax_exigibility", "cash_basis_transition_account_id"}:
        exigibility = values.get("tax_exigibility", getattr(tax, "tax_exigibility", "on_invoice"))
        account_id = values.get(
            "cash_basis_transition_account_id",
            _relation_id(getattr(tax, "cash_basis_transition_account_id", False)),
        )
        if exigibility == "on_payment" and account_id is None:
            raise _fail(failure_type, "business_rule_error", "Cash-basis taxes require a reconcilable transition account.", exit_code=6)
        if account_id is not None:
            domain = [("company_ids", "parent_of", [company_id])]
            account = _ensure_ids(env, "account.account", {account_id}, domain, company_id, failure_type)
            if exigibility == "on_payment" and not account.reconcile:
                raise _fail(failure_type, "business_rule_error", "Cash-basis taxes require a reconcilable transition account.", exit_code=6)


def _automatic_tax_group_id(env: Any, tax: Any, company_id: int) -> int | None:
    country_id = _relation_id(getattr(tax, "country_id", False))
    model = _scoped(env, "account.tax.group", company_id)
    group = model.search(
        [("company_id", "=", company_id), ("country_id", "=", country_id or False)],
        limit=1,
    )
    if not group and country_id is not None:
        group = model.search(
            [("company_id", "=", company_id), ("country_id", "=", False)],
            limit=1,
        )
    return _relation_id(group)


def _tax_matches(
    tax: Any,
    values: dict[str, Any],
    *,
    automatic_tax_group_id: int | None,
) -> bool:
    comparisons = {
        "name": tax.name,
        "type_tax_use": tax.type_tax_use,
        "amount_type": tax.amount_type,
        "amount": _canonical_decimal_text(tax.amount),
        "sequence": tax.sequence,
        "tax_group_id": _relation_id(tax.tax_group_id),
        "invoice_label": _false_to_none(tax.invoice_label),
        "price_include_override": _false_to_none(tax.price_include_override),
        "include_base_amount": tax.include_base_amount,
        "is_base_affected": tax.is_base_affected,
    }
    for field in ("tax_scope", "analytic", "tax_exigibility", "cash_basis_transition_account_id", "children_tax_ids"):
        if field in values:
            value = getattr(tax, field)
            if field == "children_tax_ids":
                value = _record_ids(value)
            elif field == "cash_basis_transition_account_id":
                value = _relation_id(value)
            elif field == "tax_scope":
                value = value or None
            comparisons[field] = value
    expected = dict(values)
    if expected.get("sequence") is None and "sequence" in expected:
        expected["sequence"] = 1
    if expected.get("tax_group_id") is None and "tax_group_id" in expected:
        expected["tax_group_id"] = automatic_tax_group_id
    return all(comparisons[name] == value for name, value in expected.items())


def _tax_values(values: dict[str, Any], *, creating: bool) -> dict[str, Any]:
    result = dict(values)
    if "amount" in result:
        result["amount"] = Decimal(result["amount"])
    if result.get("sequence") is None:
        result.pop("sequence", None)
    if "tax_group_id" in result and result["tax_group_id"] is None:
        if creating:
            result.pop("tax_group_id")
        else:
            result["tax_group_id"] = False
    for field_name in ("invoice_label", "price_include_override", "tax_scope", "cash_basis_transition_account_id"):
        if field_name in result and result[field_name] is None:
            result[field_name] = False
    if "children_tax_ids" in result:
        result["children_tax_ids"] = [(6, 0, result["children_tax_ids"])]
    return result


def _create_tax_config(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    _validate_tax_references(env, parameters, company_id, failure_type)
    model = _scoped(env, "account.tax", company_id)
    existing = model.search(
        [
            ("company_id", "=", company_id),
            ("name", "=", parameters["name"]),
            ("type_tax_use", "=", parameters["type_tax_use"]),
            ("tax_scope", "=", parameters.get("tax_scope") or False),
        ],
        limit=2,
    )
    if existing:
        if len(existing) != 1 or not _tax_matches(
            existing,
            parameters,
            automatic_tax_group_id=_automatic_tax_group_id(env, existing, company_id),
        ):
            raise _fail(
                failure_type,
                "idempotency_conflict",
                "The tax identity already exists with different configuration.",
                exit_code=5,
            )
        return _config_result(existing, "account.tax", company_id), True

    values = _tax_values(parameters, creating=True)
    values.update({"company_id": company_id, "active": True})
    tax = model.create(values)
    if tax.company_id.id != company_id or not _tax_matches(
        tax,
        parameters,
        automatic_tax_group_id=_automatic_tax_group_id(env, tax, company_id),
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not create the requested tax.",
            exit_code=6,
        )
    return _config_result(tax, "account.tax", company_id), False


def _update_tax_config(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    tax = _tax_config_record(env, parameters["tax_id"], company_id, failure_type)
    changes = parameters["changes"]
    automatic_group_id = _automatic_tax_group_id(env, tax, company_id)
    if (
        "tax_group_id" in changes
        and changes["tax_group_id"] is None
        and automatic_group_id is None
    ):
        raise _fail(
            failure_type,
            "configuration_missing",
            "No automatic tax group is available for the company and country.",
            exit_code=4,
        )
    if _tax_matches(tax, changes, automatic_tax_group_id=automatic_group_id):
        return _config_result(tax, "account.tax", company_id), True
    write_changes = dict(changes)
    if "tax_group_id" in write_changes and write_changes["tax_group_id"] is None:
        write_changes["tax_group_id"] = automatic_group_id
    _validate_tax_references(env, write_changes, company_id, failure_type, tax=tax)
    if set(changes) & {"name", "type_tax_use", "tax_scope"}:
        target_name = changes.get("name", tax.name)
        target_use = changes.get("type_tax_use", tax.type_tax_use)
        candidates = _scoped(env, "account.tax", company_id).search(
            [
                ("company_id", "=", company_id),
                ("name", "=", target_name),
                ("type_tax_use", "=", target_use),
                ("tax_scope", "=", changes.get("tax_scope", getattr(tax, "tax_scope", False)) or False),
            ],
            limit=2,
        )
        if any(candidate.id != tax.id for candidate in candidates):
            raise _fail(
                failure_type,
                "idempotency_conflict",
                "The requested tax identity is already in use.",
                exit_code=5,
            )
    tax.write(_tax_values(write_changes, creating=False))
    tax.invalidate_recordset(list(changes))
    if not _tax_matches(
        tax,
        changes,
        automatic_tax_group_id=_automatic_tax_group_id(env, tax, company_id),
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not update the requested tax fields.",
            exit_code=6,
        )
    return _config_result(tax, "account.tax", company_id), False


def _transition_config_record(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    prefix = capability_id.rsplit(".", 1)[0]
    configuration = {
        "account.account": (
            _account_config_record,
            "account_id",
            "account.account",
        ),
        "journal": (_journal_config_record, "journal_id", "account.journal"),
        "tax": (_tax_config_record, "tax_id", "account.tax"),
    }
    finder, id_name, model = configuration[prefix]
    record = finder(env, parameters[id_name], company_id, failure_type)
    target_active = capability_id.endswith(".restore")
    if record.active is target_active:
        return _config_result(record, model, company_id), True
    if target_active:
        record.action_unarchive()
    else:
        record.action_archive()
    record.invalidate_recordset(["active"])
    if record.active is not target_active:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not apply the requested configuration archive state.",
            exit_code=6,
        )
    return _config_result(record, model, company_id), False


def _move_pair_result(primary: Any, reversal: Any, company_id: int) -> dict[str, Any]:
    line_ids = sorted(set(primary.line_ids.ids) | set(reversal.line_ids.ids))
    state = "posted" if primary.state == reversal.state == "posted" else "draft"
    result = {
        "model": "account.move",
        "id": reversal.id,
        "name": reversal.name or primary.name or None,
        "state": state,
        "company_id": company_id,
        "move_type": "entry",
        "source_id": primary.id,
        "line_ids": line_ids,
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }
    assert set(result) == _RESULT_KEYS
    return result


def _validated_move_pair(
    moves: Any,
    company_id: int,
    failure_type: type[Exception],
) -> tuple[Any, Any]:
    if len(moves) != 2 or any(
        move.company_id.id != company_id
        or move.move_type != "entry"
        or move.state not in {"draft", "posted"}
        for move in moves
    ):
        raise _fail(
            failure_type,
            "idempotency_conflict",
            "The generated-entry marker does not identify one move pair.",
            exit_code=5,
        )
    reversals = moves.filtered(lambda move: bool(move.reversed_entry_id))
    primaries = moves - reversals
    if (
        len(primaries) != 1
        or len(reversals) != 1
        or reversals.reversed_entry_id != primaries
    ):
        raise _fail(
            failure_type,
            "idempotency_conflict",
            "The generated-entry marker identifies an invalid reversal graph.",
            exit_code=5,
        )
    return primaries, reversals


def _idempotency_key_marker(capability_id: str, company_id: int, key: str) -> str:
    raw = f"{capability_id}\0{company_id}\0{key}".encode()
    return f"ODACV4K:{hashlib.sha256(raw).hexdigest()}"


def _generated_pair_for_key(
    env: Any,
    company_id: int,
    key_marker: str,
    parameter_marker: str,
    failure_type: type[Exception],
) -> tuple[Any, Any] | None:
    moves = _scoped(env, "account.move", company_id).search(
        [
            ("company_id", "=", company_id),
            ("invoice_origin", "ilike", key_marker),
        ],
        limit=3,
    )
    moves = moves.filtered(lambda move: _move_has_marker(move, key_marker))
    if not moves:
        return None
    primary, reversal = _validated_move_pair(moves, company_id, failure_type)
    if any(not _move_has_marker(move, parameter_marker) for move in primary + reversal):
        raise _fail(
            failure_type,
            "idempotency_conflict",
            "The generated-entry idempotency key was already used with other parameters.",
            exit_code=5,
        )
    return primary, reversal


def _deferred_report_options(report: Any, date_to: str) -> dict[str, Any]:
    first_day = date.fromisoformat(date_to).replace(day=1).isoformat()
    return report.get_options(
        {
            "all_entries": False,
            "date": {
                "date_from": first_day,
                "date_to": date_to,
                "mode": "range",
                "filter": "custom",
            },
        }
    )


def _generate_deferred_entries(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    key: str,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    marker = _operation_marker(capability_id, key, parameters)
    key_marker = _idempotency_key_marker(capability_id, company_id, key)
    existing = _generated_pair_for_key(
        env, company_id, key_marker, marker, failure_type
    )
    if existing is not None:
        return _move_pair_result(*existing, company_id), True

    kind = "expense" if capability_id.startswith("deferred_expense") else "revenue"
    company = _search_one(
        env,
        "res.company",
        [("id", "=", company_id)],
        company_id,
        failure_type,
    )
    journal = getattr(company, f"deferred_{kind}_journal_id")
    account = getattr(company, f"deferred_{kind}_account_id")
    if not journal or not account:
        raise _fail(
            failure_type,
            "configuration_missing",
            "The company deferred journal or account is not configured.",
            exit_code=4,
        )

    report = env.ref(
        f"account_reports.deferred_{kind}_report", raise_if_not_found=False
    )
    if not report:
        raise _fail(
            failure_type,
            "uninstalled",
            "The Odoo deferred report is unavailable.",
            exit_code=4,
        )
    options = _deferred_report_options(report, parameters["date_to"])
    if not isinstance(options, dict) or not _is_id(options.get("report_id")):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo returned invalid deferred-report options.",
            exit_code=6,
        )
    handler = env[f"account.deferred.{kind}.report.handler"]
    moves = handler._generate_deferral_entry(options)
    if not moves:
        raise _fail(
            failure_type,
            "nothing_to_generate",
            "No deferred entry is eligible for generation.",
            exit_code=4,
        )
    primary, reversal = _validated_move_pair(moves, company_id, failure_type)
    (primary + reversal).write({"invoice_origin": f"{key_marker};{marker}"})
    return _move_pair_result(primary, reversal, company_id), False


def _revaluation_report_options(report: Any, target_date: str) -> dict[str, Any]:
    return report.get_options(
        {
            "all_entries": False,
            "date": {
                "date_from": False,
                "date_to": target_date,
                "mode": "single",
                "filter": "custom",
            },
        }
    )


def _generate_revaluation_entries(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    key: str,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    marker = _operation_marker(capability_id, key, parameters)
    key_marker = _idempotency_key_marker(capability_id, company_id, key)
    existing = _generated_pair_for_key(
        env, company_id, key_marker, marker, failure_type
    )
    if existing is not None:
        result = _move_pair_result(*existing, company_id)
        if result["state"] != "posted":
            raise _fail(
                failure_type,
                "state_conflict",
                "The marked revaluation pair is no longer posted.",
                exit_code=5,
            )
        return result, True

    _ensure_ids(
        env,
        "account.journal",
        {parameters["journal_id"]},
        [("company_id", "=", company_id), ("type", "=", "general")],
        company_id,
        failure_type,
    )
    _ensure_ids(
        env,
        "account.account",
        {
            parameters["expense_provision_account_id"],
            parameters["income_provision_account_id"],
        },
        [("company_ids", "in", [company_id])],
        company_id,
        failure_type,
    )
    report = env.ref(
        "account_reports.multicurrency_revaluation_report",
        raise_if_not_found=False,
    )
    if not report:
        raise _fail(
            failure_type,
            "uninstalled",
            "The Odoo multicurrency revaluation report is unavailable.",
            exit_code=4,
        )
    options = _revaluation_report_options(report, parameters["date"])
    if not isinstance(options, dict) or not _is_id(options.get("report_id")):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo returned invalid revaluation options.",
            exit_code=6,
        )
    wizard = (
        env["account.multicurrency.revaluation.wizard"]
        .with_context(multicurrency_revaluation_report_options=options)
        .new(
            {
                "company_id": company_id,
                "date": parameters["date"],
                "reversal_date": parameters["reversal_date"],
                "journal_id": parameters["journal_id"],
                "expense_provision_account_id": parameters[
                    "expense_provision_account_id"
                ],
                "income_provision_account_id": parameters[
                    "income_provision_account_id"
                ],
            }
        )
    )
    action = wizard.create_entries()
    primary_id = action.get("res_id") if isinstance(action, dict) else None
    if not _is_id(primary_id):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not return the generated revaluation entry.",
            exit_code=6,
        )
    primary = _search_one(
        env,
        "account.move",
        [("id", "=", primary_id), ("company_id", "=", company_id)],
        company_id,
        failure_type,
    )
    reversal = _search_one(
        env,
        "account.move",
        [("reversed_entry_id", "=", primary.id), ("company_id", "=", company_id)],
        company_id,
        failure_type,
    )
    primary, reversal = _validated_move_pair(
        primary + reversal, company_id, failure_type
    )
    if primary.state != "posted" or reversal.state != "posted":
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not post the revaluation pair.",
            exit_code=6,
        )
    (primary + reversal).write({"invoice_origin": f"{key_marker};{marker}"})
    return _move_pair_result(primary, reversal, company_id), False


def _payment_result(
    payment: Any, company_id: int, *, source_id: int | None
) -> dict[str, Any]:
    move = payment.move_id
    result = {
        "model": "account.payment",
        "id": payment.id,
        "name": payment.name or None,
        "state": payment.state or None,
        "company_id": company_id,
        "move_type": None,
        "source_id": source_id,
        "line_ids": _record_ids(move.line_ids) if move else [],
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": bool(payment.is_reconciled),
    }
    assert set(result) == _RESULT_KEYS
    return result


def _batch_payments(
    env: Any,
    payment_ids: list[int],
    company_id: int,
    failure_type: type[Exception],
) -> Any:
    payments = _ensure_ids(
        env,
        "account.payment",
        set(payment_ids),
        [("company_id", "=", company_id)],
        company_id,
        failure_type,
    )
    return payments.sorted(lambda payment: payment.id)


def _payment_batch_result(payments: Any, company_id: int) -> dict[str, Any]:
    items = [
        _payment_result(payment, company_id, source_id=None) for payment in payments
    ]
    return {"items": items, "processed_count": len(items)}


def _bank_transaction_result(
    transaction: Any, company_id: int, failure_type: type[Exception]
) -> dict[str, Any]:
    move = transaction.move_id
    line_ids = _record_ids(move.line_ids)
    if move.move_type != "entry" or not line_ids:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo returned an invalid bank transaction entry.",
            exit_code=6,
        )
    partials = move.line_ids.matched_debit_ids | move.line_ids.matched_credit_ids
    fulls = move.line_ids.full_reconcile_id | partials.full_reconcile_id
    full_ids = sorted(fulls.ids)
    result = {
        "model": "account.bank.statement.line",
        "id": transaction.id,
        "name": move.name or None,
        "state": move.state,
        "company_id": company_id,
        "move_type": move.move_type,
        "source_id": move.id,
        "line_ids": line_ids,
        "partial_reconcile_ids": sorted(partials.ids),
        "full_reconcile_id": full_ids[0] if len(full_ids) == 1 else None,
        "reconciled": bool(transaction.is_reconciled),
    }
    assert set(result) == _RESULT_KEYS
    return result


def _bank_statement_result(statement: Any, company_id: int) -> dict[str, Any]:
    result = {
        "model": "account.bank.statement",
        "id": statement.id,
        "name": statement.name or statement.reference or None,
        "state": "complete" if statement.is_complete else "incomplete",
        "company_id": company_id,
        "move_type": None,
        "source_id": None,
        "line_ids": _record_ids(statement.line_ids),
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }
    assert set(result) == _RESULT_KEYS
    return result


def _deleted_result(result: dict[str, Any]) -> dict[str, Any]:
    deleted = {**result, "state": "deleted", "reconciled": False}
    assert set(deleted) == _RESULT_KEYS
    return deleted


def _unreconciled_result(
    lines: Any, company_id: int, *, source_id: int | None = None
) -> dict[str, Any]:
    result = {
        "model": "account.move.line",
        "id": None,
        "name": None,
        "state": "unreconciled",
        "company_id": company_id,
        "move_type": None,
        "source_id": source_id,
        "line_ids": sorted(lines.ids),
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }
    assert set(result) == _RESULT_KEYS
    return result


def _existing_move_for_key(
    env: Any,
    capability_id: str,
    company_id: int,
    key: str,
    move_type: str,
    marker: str,
    failure_type: type[Exception],
) -> Any | None:
    key_marker = _idempotency_key_marker(capability_id, company_id, key)
    new_candidates = _scoped(env, "account.move", company_id).search(
        [
            ("company_id", "=", company_id),
            ("move_type", "=", move_type),
            ("invoice_origin", "=like", f"%{key_marker}%"),
        ]
    )
    new_records = new_candidates.filtered(
        lambda move: _move_has_marker(move, key_marker)
    )
    legacy_records = _scoped(env, "account.move", company_id).search(
        [
            ("company_id", "=", company_id),
            ("move_type", "=", move_type),
            ("ref", "=", key),
        ],
        limit=2,
    )
    record_ids = set(new_records.ids) | set(legacy_records.ids)
    if not record_ids:
        return None
    if len(record_ids) != 1:
        raise _fail(
            failure_type,
            "idempotency_conflict",
            "The idempotency key was already used with different parameters.",
            exit_code=5,
        )
    record = _scoped(env, "account.move", company_id).browse(record_ids.pop())
    if record.id in set(new_records.ids):
        valid = _move_has_marker(record, marker)
    else:
        valid = record.invoice_origin == marker
    if not valid:
        raise _fail(
            failure_type,
            "idempotency_conflict",
            "The idempotency key was already used with different parameters.",
            exit_code=5,
        )
    return record


def _validate_invoice_financial_references(
    env: Any,
    values: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> None:
    bank_id = values.get("partner_bank_id")
    if bank_id is not None:
        # Native payment methods can select a journal bank rather than the
        # standard recipient's bank; do not turn the UI owner domain into a lock.
        _ensure_ids(
            env,
            "res.partner.bank",
            {bank_id},
            [
                ("company_id", "in", [False, company_id]),
                ("active", "=", True),
            ],
            company_id,
            failure_type,
        )
    position_id = values.get("fiscal_position_id")
    if position_id is not None:
        _ensure_ids(
            env,
            "account.fiscal.position",
            {position_id},
            [("company_id", "parent_of", [company_id]), ("active", "=", True)],
            company_id,
            failure_type,
        )


def _validate_invoice_line_inputs(
    env: Any, lines: list[dict[str, Any]], company_id: int,
    failure_type: type[Exception], move_type: str,
) -> None:
    requested_fields = set().union(*(set(line) & _INVOICE_LINE_INPUT_FIELDS for line in lines))
    if not requested_fields:
        return
    if not requested_fields <= set(_scoped(env, "account.move.line", company_id)._fields):
        raise _fail(failure_type, "business_rule_error", "The requested native invoice-line inputs are unavailable.", exit_code=6)
    if move_type not in {"in_invoice", "in_refund"} and any(
        "deductible_amount" in line and Decimal(line["deductible_amount"]) != 100 for line in lines
    ):
        raise _fail(failure_type, "business_rule_error", "Partial deductibility is only supported on native purchase documents.", exit_code=6)
    unit_lines = [line for line in lines if "product_uom_id" in line]
    if not unit_lines:
        return
    if any(not _is_id(line.get("product_id")) for line in unit_lines):
        raise _fail(failure_type, "business_rule_error", "Unit assignment requires a product-backed invoice business line.", exit_code=6)
    products = _ensure_ids(env, "product.product", {line["product_id"] for line in unit_lines},
                           [("company_id", "in", [False, company_id])], company_id, failure_type)
    _ensure_ids(env, "uom.uom", {line["product_uom_id"] for line in unit_lines}, [], company_id, failure_type)
    by_id = {product.id: product for product in products}
    if any(line["product_uom_id"] not in (by_id[line["product_id"]].uom_id | by_id[line["product_id"]].uom_ids).ids for line in unit_lines):
        raise _fail(failure_type, "business_rule_error", "The requested unit is not a native allowed unit for this invoice product.", exit_code=6)


def _current_invoice_line_inputs(line: Any, requested: dict[str, Any]) -> dict[str, Any]:
    return {
        field: _canonical_decimal_text(getattr(line, field)) if field == "deductible_amount" else _many2one_id(getattr(line, field))
        for field in _INVOICE_LINE_INPUT_FIELDS if field in requested
    }


def _invoice_line_inputs_match(move: Any, requested: list[dict[str, Any]]) -> bool:
    if not any(_INVOICE_LINE_INPUT_FIELDS & set(line) for line in requested):
        return True
    lines = _ordered_move_lines(move.invoice_line_ids)
    return len(lines) == len(requested) and all(
        _current_invoice_line_inputs(line, values) == {
            field: _canonical_decimal_text(values[field]) if field == "deductible_amount" else values[field]
            for field in _INVOICE_LINE_INPUT_FIELDS if field in values
        }
        for line, values in zip(lines, requested, strict=True)
    )


def _create_document(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    key: str,
    marker: str,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    move_type = (
        "out_invoice" if capability_id == "customer_invoice.create" else "in_invoice"
    )
    existing = _existing_move_for_key(
        env, capability_id, company_id, key, move_type, marker, failure_type
    )
    if existing:
        _validate_invoice_line_inputs(env, parameters["lines"], company_id, failure_type, move_type)
        if not _invoice_line_inputs_match(existing, parameters["lines"]):
            raise _fail(failure_type, "idempotency_conflict", "The document operation key conflicts with different native line inputs.", exit_code=5)
        return _move_result(existing, company_id), True

    journal_type = "sale" if move_type == "out_invoice" else "purchase"
    _ensure_ids(
        env,
        "account.journal",
        {parameters["journal_id"]},
        [("company_id", "=", company_id), ("type", "=", journal_type)],
        company_id,
        failure_type,
    )
    _ensure_ids(
        env,
        "res.partner",
        {parameters["partner_id"]},
        [("company_id", "in", [False, company_id])],
        company_id,
        failure_type,
    )
    _ensure_ids(
        env,
        "res.currency",
        {parameters["currency_id"]},
        [("active", "=", True)],
        company_id,
        failure_type,
    )
    payment_term_id = parameters.get("payment_term_id")
    _ensure_ids(
        env,
        "account.payment.term",
        {payment_term_id} if payment_term_id is not None else set(),
        [("company_id", "in", [False, company_id])],
        company_id,
        failure_type,
    )
    _validate_invoice_financial_references(
        env, parameters, company_id, failure_type
    )
    _ensure_ids(
        env,
        "product.product",
        {
            line["product_id"]
            for line in parameters["lines"]
            if line.get("product_id") is not None
        },
        [("company_id", "in", [False, company_id])],
        company_id,
        failure_type,
    )
    account_ids = {line["account_id"] for line in parameters["lines"]}
    tax_ids = {tax_id for line in parameters["lines"] for tax_id in line["tax_ids"]}
    _ensure_ids(
        env,
        "account.account",
        account_ids,
        [("company_ids", "in", [company_id])],
        company_id,
        failure_type,
    )
    _ensure_ids(
        env,
        "account.tax",
        tax_ids,
        [("company_id", "=", company_id)],
        company_id,
        failure_type,
    )
    _validate_line_analytic_references(
        env, parameters["lines"], company_id, failure_type
    )
    _validate_invoice_line_inputs(env, parameters["lines"], company_id, failure_type, move_type)
    values = {
        "move_type": move_type,
        "company_id": company_id,
        "partner_id": parameters["partner_id"],
        "journal_id": parameters["journal_id"],
        "invoice_date": parameters["invoice_date"],
        "currency_id": parameters["currency_id"],
        "invoice_origin": (
            f"{_idempotency_key_marker(capability_id, company_id, key)};{marker}"
        ),
        "invoice_line_ids": [
            (
                0,
                0,
                {
                    "name": line["name"],
                    "account_id": line["account_id"],
                    "quantity": Decimal(line["quantity"]),
                    "price_unit": Decimal(line["price_unit"]),
                    "tax_ids": [(6, 0, line["tax_ids"])],
                    **_invoice_line_write_values({field: line[field] for field in _INVOICE_LINE_INPUT_FIELDS if field in line}),
                    **(
                        {"product_id": line["product_id"] or False}
                        if "product_id" in line
                        else {}
                    ),
                    **(
                        {"discount": Decimal(line["discount"])}
                        if "discount" in line
                        else {}
                    ),
                    **{
                        field: line[field] or False
                        for field in _DEFERRED_LINE_DATE_FIELDS
                        if field in line
                    },
                    **(
                        {
                            "analytic_distribution": _odoo_analytic_distribution(
                                line["analytic_distribution"]
                            )
                        }
                        if "analytic_distribution" in line
                        else {}
                    ),
                },
            )
            for line in parameters["lines"]
        ],
    }
    header_map = {
        "date": "date",
        "invoice_date_due": "invoice_date_due",
        "payment_term_id": "invoice_payment_term_id",
        "partner_bank_id": "partner_bank_id",
        "fiscal_position_id": "fiscal_position_id",
        "reference": "ref",
        "payment_reference": "payment_reference",
    }
    for parameter_name, field_name in header_map.items():
        if parameter_name in parameters:
            values[field_name] = parameters[parameter_name] or False
    move = _scoped(env, "account.move", company_id).create(values)
    if not _invoice_line_inputs_match(move, parameters["lines"]):
        raise _fail(failure_type, "odoo_write_error", "Odoo did not persist the requested native invoice-line inputs.", exit_code=6)
    return _move_result(move, company_id), False


def _create_entry(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    key: str,
    marker: str,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    existing = _existing_move_for_key(
        env,
        "journal_entry.create",
        company_id,
        key,
        "entry",
        marker,
        failure_type,
    )
    if existing:
        return _move_result(existing, company_id), True
    _ensure_ids(
        env,
        "account.journal",
        {parameters["journal_id"]},
        [("company_id", "=", company_id), ("type", "=", "general")],
        company_id,
        failure_type,
    )
    _ensure_ids(
        env,
        "account.account",
        {line["account_id"] for line in parameters["lines"]},
        [("company_ids", "in", [company_id])],
        company_id,
        failure_type,
    )
    partner_ids = {
        line["partner_id"]
        for line in parameters["lines"]
        if line["partner_id"] is not None
    }
    _ensure_ids(
        env,
        "res.partner",
        partner_ids,
        [("company_id", "in", [False, company_id])],
        company_id,
        failure_type,
    )
    currency_ids = {
        line["currency_id"]
        for line in parameters["lines"]
        if line.get("currency_id") is not None
    }
    _ensure_ids(
        env,
        "res.currency",
        currency_ids,
        [("active", "=", True)],
        company_id,
        failure_type,
    )
    company = _search_one(
        env,
        "res.company",
        [("id", "=", company_id)],
        company_id,
        failure_type,
    )
    company_currency_id = company.currency_id.id
    for line in parameters["lines"]:
        if line.get("currency_id") is None:
            continue
        balance = Decimal(line["debit"]) - Decimal(line["credit"])
        amount_currency = Decimal(line["amount_currency"])
        if (
            line["currency_id"] == company_currency_id and amount_currency != balance
        ) or (
            line["currency_id"] != company_currency_id
            and (amount_currency == 0 or (amount_currency > 0) != (balance > 0))
        ):
            raise _fail(
                failure_type,
                "state_conflict",
                "The journal-entry currency amounts are inconsistent.",
                exit_code=5,
            )
    _validate_line_analytic_references(
        env, parameters["lines"], company_id, failure_type
    )
    tax_inputs = any(_ENTRY_TAX_FIELDS & set(line) for line in parameters["lines"])
    if tax_inputs:
        _validate_entry_tax_references(env, parameters["lines"], company_id, failure_type)
    values = {
        "move_type": "entry",
        "company_id": company_id,
        "journal_id": parameters["journal_id"],
        "date": parameters["date"],
        "invoice_origin": (
            f"{_idempotency_key_marker('journal_entry.create', company_id, key)};"
            f"{marker}"
        ),
        **(
            {"ref": parameters["reference"] or False}
            if "reference" in parameters
            else {}
        ),
        "line_ids": [
            (
                0,
                0,
                {
                    "name": line["name"],
                    "account_id": line["account_id"],
                    "partner_id": line["partner_id"] or False,
                    "debit": Decimal(line["debit"]),
                    "credit": Decimal(line["credit"]),
                    **_journal_item_write_values({
                        field: line[field] for field in _ENTRY_TAX_FIELDS if field in line
                    }),
                    **(
                        {"date_maturity": line["date_maturity"] or False}
                        if "date_maturity" in line
                        else {}
                    ),
                    **(
                        {
                            "currency_id": line["currency_id"] or False,
                            "amount_currency": (
                                Decimal(line["amount_currency"])
                                if line["amount_currency"] is not None
                                else False
                            ),
                        }
                        if line.get("currency_id") is not None
                        else {}
                    ),
                    **(
                        {
                            "analytic_distribution": _odoo_analytic_distribution(
                                line["analytic_distribution"]
                            )
                        }
                        if "analytic_distribution" in line
                        else {}
                    ),
                },
            )
            for line in parameters["lines"]
        ],
    }
    if tax_inputs:
        with env.cr.savepoint():
            move = _scoped(env, "account.move", company_id).create(values)
            if not _entry_lines_match(
                _current_entry_lines(move), parameters["lines"], company_currency_id
            ):
                raise _fail(
                    failure_type, "state_conflict",
                    "Provide the complete balanced base and tax rows; native tax synchronization must preserve the requested rows.",
                    exit_code=5,
                )
    else:
        move = _scoped(env, "account.move", company_id).create(values)
    return _move_result(move, company_id), False


def _many2one_id(value: Any) -> int | None:
    if _is_id(value):
        return value
    record_id = getattr(value, "id", None)
    return record_id if _is_id(record_id) else None


def _nullable_value(value: Any) -> str | None:
    return None if value in (None, False) else str(value)


def _lifecycle_move(
    env: Any,
    capability_id: str,
    move_id: int,
    company_id: int,
    failure_type: type[Exception],
) -> Any:
    invoice_action = capability_id in _INVOICE_LIFECYCLE_CAPABILITIES
    move_types = _DOCUMENT_TYPES if invoice_action else ("entry",)
    move = _search_one(
        env,
        "account.move",
        [
            ("id", "=", move_id),
            ("company_id", "=", company_id),
            ("move_type", "in", list(move_types)),
        ],
        company_id,
        failure_type,
    )
    if not invoice_action and (
        not move.journal_id or move.journal_id.type != "general"
    ):
        raise _fail(
            failure_type,
            "record_not_found",
            "The requested accounting record was not found.",
            exit_code=4,
        )
    return move


def _batch_lifecycle_moves(
    env: Any,
    capability_id: str,
    move_ids: list[int],
    company_id: int,
    failure_type: type[Exception],
) -> Any:
    invoice_action = capability_id.startswith("invoice.")
    move_types = _DOCUMENT_TYPES if invoice_action else ("entry",)
    moves = _ensure_ids(
        env,
        "account.move",
        set(move_ids),
        [
            ("company_id", "=", company_id),
            ("move_type", "in", list(move_types)),
        ],
        company_id,
        failure_type,
    )
    if not invoice_action and any(
        not move.journal_id or move.journal_id.type != "general" for move in moves
    ):
        raise _fail(
            failure_type,
            "record_not_found",
            "A requested accounting record was not found.",
            exit_code=4,
        )
    return moves.sorted(lambda move: move.id)


def _move_batch_result(moves: Any, company_id: int) -> dict[str, Any]:
    items = [_move_result(move, company_id) for move in moves]
    return {"items": items, "processed_count": len(items)}


def _validate_invoice_update_references(
    env: Any,
    move: Any,
    changes: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> None:
    if "journal_id" in changes:
        journal_type = (
            "sale" if move.move_type in {"out_invoice", "out_refund"} else "purchase"
        )
        _ensure_ids(
            env,
            "account.journal",
            {changes["journal_id"]},
            [("company_id", "=", company_id), ("type", "=", journal_type)],
            company_id,
            failure_type,
        )
    if "currency_id" in changes:
        _ensure_ids(
            env,
            "res.currency",
            {changes["currency_id"]},
            [("active", "=", True)],
            company_id,
            failure_type,
        )
    if "partner_id" in changes:
        _ensure_ids(
            env,
            "res.partner",
            {changes["partner_id"]},
            [("company_id", "in", [False, company_id])],
            company_id,
            failure_type,
        )
    payment_term_id = changes.get("payment_term_id")
    if payment_term_id is not None:
        _ensure_ids(
            env,
            "account.payment.term",
            {payment_term_id},
            [("company_id", "in", [False, company_id])],
            company_id,
            failure_type,
        )
    _validate_invoice_financial_references(env, changes, company_id, failure_type)


def _validate_journal_update_references(
    env: Any,
    changes: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> None:
    if "journal_id" in changes:
        _ensure_ids(
            env,
            "account.journal",
            {changes["journal_id"]},
            [("company_id", "=", company_id), ("type", "=", "general")],
            company_id,
            failure_type,
        )


def _current_invoice_changes(move: Any, requested_fields: set[str]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for field_name in requested_fields:
        if field_name in {
            "partner_id",
            "journal_id",
            "currency_id",
            "partner_bank_id",
            "fiscal_position_id",
        }:
            values[field_name] = _many2one_id(getattr(move, field_name))
        elif field_name == "payment_term_id":
            values[field_name] = _many2one_id(move.invoice_payment_term_id)
        elif field_name == "reference":
            values[field_name] = _nullable_value(move.ref)
        else:
            values[field_name] = _nullable_value(getattr(move, field_name))
    return values


def _current_journal_entry_changes(
    move: Any, requested_fields: set[str]
) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for field_name in requested_fields:
        if field_name == "journal_id":
            values[field_name] = _many2one_id(move.journal_id)
        elif field_name == "reference":
            values[field_name] = _nullable_value(move.ref)
        else:
            values[field_name] = _nullable_value(getattr(move, field_name))
    return values


def _update_move(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    move = _lifecycle_move(
        env, capability_id, parameters["move_id"], company_id, failure_type
    )
    changes = parameters["changes"]
    invoice_action = capability_id == "invoice.update"
    if invoice_action:
        _validate_invoice_update_references(env, move, changes, company_id, failure_type)
        current = _current_invoice_changes(move, set(changes))
    else:
        _validate_journal_update_references(env, changes, company_id, failure_type)
        current = _current_journal_entry_changes(move, set(changes))
    nonfinancial_fields = {"reference", "payment_reference", "partner_bank_id"} if invoice_action else {"reference"}
    if invoice_action and move.state == "posted" and "partner_bank_id" in changes and move.is_move_sent:
        raise _fail(failure_type, "state_conflict", "A sent invoice or generated PDF cannot have its recipient bank changed.", exit_code=5)
    if move.state != "draft" and not (
        move.state == "posted" and set(changes) <= nonfinancial_fields
    ):
        raise _fail(
            failure_type,
            "state_conflict",
            "Only draft moves or posted nonfinancial reference fields can be updated.",
            exit_code=5,
        )
    if current == changes:
        return _move_result(move, company_id), True

    field_map = (
        {
            "partner_id": "partner_id",
            "journal_id": "journal_id",
            "currency_id": "currency_id",
            "date": "date",
            "invoice_date": "invoice_date",
            "invoice_date_due": "invoice_date_due",
            "payment_term_id": "invoice_payment_term_id",
            "partner_bank_id": "partner_bank_id",
            "fiscal_position_id": "fiscal_position_id",
            "reference": "ref",
            "payment_reference": "payment_reference",
        }
        if invoice_action
        else {"date": "date", "journal_id": "journal_id", "reference": "ref"}
    )
    values = {
        field_map[field_name]: False if value is None else value
        for field_name, value in changes.items()
    }
    move.write(values)
    verified = (
        _current_invoice_changes(move, set(changes))
        if invoice_action
        else _current_journal_entry_changes(move, set(changes))
    )
    if verified != changes:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not persist the requested accounting move changes.",
            exit_code=6,
        )
    return _move_result(move, company_id), False


def _relation_ids(value: Any) -> list[int]:
    ids = getattr(value, "ids", None)
    if isinstance(ids, list):
        return sorted(item for item in ids if _is_id(item))
    if isinstance(value, (list, tuple, set)):
        return sorted(
            item_id for item in value if (item_id := _many2one_id(item)) is not None
        )
    return []


def _ordered_move_lines(lines: Any) -> list[Any]:
    return sorted(
        lines,
        key=lambda line: (getattr(line, "sequence", 0), line.id),
    )


def _current_invoice_line(line: Any, requested: dict[str, Any] | None = None) -> dict[str, Any] | None:
    if getattr(line, "display_type", None) not in {None, False, "product"}:
        return None
    account_id = _many2one_id(line.account_id)
    if not _is_text(line.name) or account_id is None:
        return None
    return {
        "name": line.name,
        "product_id": _many2one_id(line.product_id),
        "account_id": account_id,
        "quantity": _canonical_decimal_text(line.quantity),
        "price_unit": _canonical_decimal_text(line.price_unit),
        "discount": _canonical_decimal_text(line.discount),
        "tax_ids": _relation_ids(line.tax_ids),
        "analytic_distribution": _normalized_analytic_distribution(
            getattr(line, "analytic_distribution", None)
        ),
        **{
            field: _nullable_value(getattr(line, field, None))
            for field in _DEFERRED_LINE_DATE_FIELDS
        },
        **_current_invoice_line_inputs(line, requested or {}),
    }


def _current_invoice_lines(move: Any, requested: list[dict[str, Any]] | None = None) -> list[dict[str, Any]] | None:
    result: list[dict[str, Any]] = []
    for index, line in enumerate(_ordered_move_lines(move.invoice_line_ids)):
        values = _current_invoice_line(line, requested[index] if requested and index < len(requested) else None)
        if values is None:
            return None
        result.append(values)
    return result


def _current_entry_lines(move: Any) -> list[dict[str, Any]] | None:
    result: list[dict[str, Any]] = []
    for line in _ordered_move_lines(move.line_ids):
        account_id = _many2one_id(line.account_id)
        if not _is_text(line.name) or account_id is None:
            return None
        result.append(
            {
                "name": line.name,
                "account_id": account_id,
                "partner_id": _many2one_id(line.partner_id),
                "date_maturity": _nullable_value(getattr(line, "date_maturity", None)),
                "debit": _canonical_decimal_text(line.debit),
                "credit": _canonical_decimal_text(line.credit),
                "currency_id": _many2one_id(line.currency_id),
                "amount_currency": _canonical_decimal_text(line.amount_currency),
                "analytic_distribution": _normalized_analytic_distribution(
                    getattr(line, "analytic_distribution", None)
                ),
                **_journal_item_current(line, _ENTRY_TAX_FIELDS),
            }
        )
    return result


def _validate_invoice_line_references(
    env: Any,
    move: Any,
    lines: list[dict[str, Any]],
    company_id: int,
    failure_type: type[Exception],
) -> None:
    partner_id = _many2one_id(move.partner_id)
    _ensure_ids(
        env,
        "res.partner",
        {partner_id} if partner_id is not None else set(),
        [("company_id", "in", [False, company_id])],
        company_id,
        failure_type,
    )
    _ensure_ids(
        env,
        "product.product",
        {line["product_id"] for line in lines if line["product_id"] is not None},
        [("company_id", "in", [False, company_id])],
        company_id,
        failure_type,
    )
    _ensure_ids(
        env,
        "account.account",
        {line["account_id"] for line in lines},
        [("company_ids", "in", [company_id])],
        company_id,
        failure_type,
    )
    _ensure_ids(
        env,
        "account.tax",
        {tax_id for line in lines for tax_id in line["tax_ids"]},
        [("company_id", "=", company_id)],
        company_id,
        failure_type,
    )
    _validate_line_analytic_references(env, lines, company_id, failure_type)
    if any(_INVOICE_LINE_INPUT_FIELDS & set(line) for line in lines):
        _validate_invoice_line_inputs(env, lines, company_id, failure_type, move.move_type)


def _validate_entry_line_references(
    env: Any,
    lines: list[dict[str, Any]],
    company_id: int,
    failure_type: type[Exception],
) -> int:
    _ensure_ids(
        env,
        "account.account",
        {line["account_id"] for line in lines},
        [("company_ids", "in", [company_id])],
        company_id,
        failure_type,
    )
    _ensure_ids(
        env,
        "res.partner",
        {line["partner_id"] for line in lines if line["partner_id"] is not None},
        [("company_id", "in", [False, company_id])],
        company_id,
        failure_type,
    )
    _ensure_ids(
        env,
        "res.currency",
        {line["currency_id"] for line in lines if line.get("currency_id") is not None},
        [("active", "=", True)],
        company_id,
        failure_type,
    )
    company = _search_one(
        env,
        "res.company",
        [("id", "=", company_id)],
        company_id,
        failure_type,
    )
    company_currency_id = company.currency_id.id
    for line in lines:
        if line.get("currency_id") is None:
            continue
        balance = Decimal(line["debit"]) - Decimal(line["credit"])
        amount_currency = Decimal(line["amount_currency"])
        if (
            line["currency_id"] == company_currency_id and amount_currency != balance
        ) or (
            line["currency_id"] != company_currency_id
            and (amount_currency == 0 or (amount_currency > 0) != (balance > 0))
        ):
            raise _fail(
                failure_type,
                "state_conflict",
                "The journal-entry currency amounts are inconsistent.",
                exit_code=5,
            )
    _validate_line_analytic_references(env, lines, company_id, failure_type)
    if any(_ENTRY_TAX_FIELDS & set(line) for line in lines):
        _validate_entry_tax_references(env, lines, company_id, failure_type)
    return company_currency_id


def _validate_entry_tax_references(
    env: Any, lines: list[dict[str, Any]], company_id: int,
    failure_type: type[Exception],
) -> None:
    _ensure_ids(
        env, "account.tax", {item for line in lines for item in line.get("tax_ids", [])},
        [("company_id", "=", company_id)], company_id, failure_type,
    )
    _ensure_ids(
        env, "account.account.tag", {item for line in lines for item in line.get("tax_tag_ids", [])},
        [("applicability", "=", "taxes")], company_id, failure_type,
    )
    _ensure_ids(
        env, "account.tax.repartition.line",
        {line["tax_repartition_line_id"] for line in lines if line.get("tax_repartition_line_id") is not None},
        [("company_id", "=", company_id)], company_id, failure_type,
    )


def _has_external_invoice_line_source(move: Any) -> bool:
    for line in move.invoice_line_ids:
        field_names = getattr(line, "_fields", {})
        if "sale_line_ids" in field_names and line.sale_line_ids:
            return True
        if "purchase_line_id" in field_names and line.purchase_line_id:
            return True
    return False


def _replacement_commands(
    capability_id: str, lines: list[dict[str, Any]]
) -> list[tuple[Any, ...]]:
    commands: list[tuple[Any, ...]] = [(5, 0, 0)]
    invoice_action = capability_id in {
        "invoice.lines.replace",
        "customer_credit_note.create",
        "vendor_refund.create",
    }
    for index, line in enumerate(lines, start=1):
        if invoice_action:
            values = {
                "sequence": index * 10,
                "name": line["name"],
                "product_id": line["product_id"] or False,
                "account_id": line["account_id"],
                "quantity": Decimal(line["quantity"]),
                "price_unit": Decimal(line["price_unit"]),
                "discount": Decimal(line["discount"]),
                "tax_ids": [(6, 0, line["tax_ids"])],
                **_invoice_line_write_values({field: line[field] for field in _INVOICE_LINE_INPUT_FIELDS if field in line}),
                "analytic_distribution": _odoo_analytic_distribution(
                    line.get("analytic_distribution")
                ),
                **{
                    field: line[field] or False
                    for field in _DEFERRED_LINE_DATE_FIELDS
                    if field in line
                },
            }
        else:
            values = {
                "sequence": index * 10,
                "name": line["name"],
                "account_id": line["account_id"],
                "partner_id": line["partner_id"] or False,
                "debit": Decimal(line["debit"]),
                "credit": Decimal(line["credit"]),
                **_journal_item_write_values({
                    field: line[field] for field in _ENTRY_TAX_FIELDS if field in line
                }),
                **(
                    {"date_maturity": line["date_maturity"] or False}
                    if "date_maturity" in line
                    else {}
                ),
                **(
                    {
                        "currency_id": line["currency_id"] or False,
                        "amount_currency": (
                            Decimal(line["amount_currency"])
                            if line["amount_currency"] is not None
                            else False
                        ),
                    }
                    if line.get("currency_id") is not None
                    else {}
                ),
                "analytic_distribution": _odoo_analytic_distribution(
                    line.get("analytic_distribution")
                ),
            }
        commands.append((0, 0, values))
    return commands


def _replace_move_lines(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    move = _lifecycle_move(
        env, capability_id, parameters["move_id"], company_id, failure_type
    )
    lines = parameters["lines"]
    invoice_action = capability_id == "invoice.lines.replace"
    if not invoice_action and any(_ENTRY_TAX_FIELDS & set(line) for line in lines):
        if move.state != "draft":
            raise _fail(
                failure_type, "state_conflict",
                "Explicit journal-entry tax inputs require a draft entry.", exit_code=5,
            )
        if _generated_entry(move) or any(_journal_item_sourced(line) for line in move.line_ids):
            raise _fail(
                failure_type, "business_rule_error",
                "Explicit journal-entry tax inputs require an ordinary source-unlinked entry.",
                exit_code=6,
            )
    if invoice_action:
        _validate_invoice_line_references(env, move, lines, company_id, failure_type)
        matches = _invoice_lines_match(_current_invoice_lines(move, lines), lines)
    else:
        company_currency_id = _validate_entry_line_references(
            env, lines, company_id, failure_type
        )
        matches = _entry_lines_match(
            _current_entry_lines(move), lines, company_currency_id
        )
    if matches:
        return _move_result(move, company_id), True
    if invoice_action and _has_external_invoice_line_source(move):
        raise _fail(
            failure_type,
            "business_rule_error",
            "Invoice lines linked to a sales or purchase source cannot be replaced.",
            exit_code=6,
        )
    if move.state != "draft":
        raise _fail(
            failure_type,
            "state_conflict",
            "Only a draft accounting move can have its lines replaced.",
            exit_code=5,
        )

    field_name = "invoice_line_ids" if invoice_action else "line_ids"
    move.write({field_name: _replacement_commands(capability_id, lines)})
    verified = (
        _invoice_lines_match(_current_invoice_lines(move, lines), lines)
        if invoice_action
        else _entry_lines_match(_current_entry_lines(move), lines, company_currency_id)
    )
    if not verified:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not persist the requested accounting move lines.",
            exit_code=6,
        )
    return _move_result(move, company_id), False


def _invoice_line_write_values(values: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for field_name, value in values.items():
        if field_name in {"quantity", "price_unit", "discount", "deductible_amount"}:
            result[field_name] = Decimal(value)
        elif field_name == "tax_ids":
            result[field_name] = [(6, 0, value)]
        elif field_name == "analytic_distribution":
            result[field_name] = _odoo_analytic_distribution(value)
        elif field_name in {
            "product_id",
            "deferred_start_date",
            "deferred_end_date",
        }:
            result[field_name] = value or False
        else:
            result[field_name] = value
    return result


def _invoice_line(
    env: Any,
    move: Any,
    line_id: int,
    company_id: int,
    failure_type: type[Exception],
) -> Any:
    line = _search_one(
        env,
        "account.move.line",
        [
            ("id", "=", line_id),
            ("move_id", "=", move.id),
            ("company_id", "=", company_id),
            ("display_type", "in", [False, "product"]),
        ],
        company_id,
        failure_type,
    )
    if line.id not in set(move.invoice_line_ids.ids):
        raise _fail(
            failure_type,
            "record_not_found",
            "The requested invoice business line was not found.",
            exit_code=4,
        )
    return line


def _invoice_line_matches(line: Any, target: dict[str, Any]) -> bool:
    current = _current_invoice_line(line, target)
    expected = _normalized_invoice_replacement_lines([target])[0]
    return current == expected


def _create_invoice_line(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    move = _lifecycle_move(
        env, "invoice.line.create", parameters["move_id"], company_id, failure_type
    )
    if move.state != "draft":
        raise _fail(
            failure_type,
            "state_conflict",
            "Only a draft invoice or bill can receive a business line.",
            exit_code=5,
        )
    requested = parameters["line"]
    _validate_invoice_line_references(
        env, move, [requested], company_id, failure_type
    )
    matches = [
        line
        for line in move.invoice_line_ids
        if _current_invoice_line(line) is not None
        and _invoice_line_matches(line, requested)
    ]
    if len(matches) == 1:
        return _move_result(move, company_id, source_id=matches[0].id), True
    if len(matches) > 1:
        raise _fail(
            failure_type,
            "idempotency_conflict",
            "More than one invoice line matches the requested create state.",
            exit_code=5,
        )
    before_ids = set(move.invoice_line_ids.ids)
    values = {
        "display_type": "product",
        **_invoice_line_write_values(requested),
    }
    move.write({"invoice_line_ids": [(0, 0, values)]})
    created = [
        line
        for line in move.invoice_line_ids
        if line.id not in before_ids
        and _current_invoice_line(line) is not None
        and _invoice_line_matches(line, requested)
    ]
    if len(created) != 1:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not create exactly one requested invoice business line.",
            exit_code=6,
        )
    return _move_result(move, company_id, source_id=created[0].id), False


def _update_invoice_line(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    move = _lifecycle_move(
        env, "invoice.line.update", parameters["move_id"], company_id, failure_type
    )
    if move.state != "draft":
        raise _fail(
            failure_type,
            "state_conflict",
            "Only a draft invoice or bill can have a business line updated.",
            exit_code=5,
        )
    line = _invoice_line(
        env, move, parameters["line_id"], company_id, failure_type
    )
    current = _current_invoice_line(line)
    if current is None:
        raise _fail(
            failure_type,
            "record_not_found",
            "The requested invoice business line was not found.",
            exit_code=4,
        )
    target = {**current, **parameters["changes"]}
    if _INVOICE_LINE_INPUT_FIELDS & set(parameters["changes"]):
        _validate_invoice_line_inputs(env, [target], company_id, failure_type, move.move_type)
        current.update(_current_invoice_line_inputs(line, parameters["changes"]))
    if _invoice_line_matches(line, target):
        return _move_result(move, company_id, source_id=line.id), True
    field_names = getattr(line, "_fields", {})
    changes_product = (
        "product_id" in parameters["changes"]
        and parameters["changes"]["product_id"] != current["product_id"]
    )
    sourced = (
        "sale_line_ids" in field_names and bool(line.sale_line_ids)
    ) or ("purchase_line_id" in field_names and bool(line.purchase_line_id))
    if changes_product and sourced:
        raise _fail(
            failure_type,
            "business_rule_error",
            "A sales- or purchase-sourced invoice line cannot change product.",
            exit_code=6,
        )
    if sourced and any(
        current[field] != (_canonical_decimal_text(parameters["changes"][field]) if field == "deductible_amount" else parameters["changes"][field])
        for field in _INVOICE_LINE_INPUT_FIELDS if field in parameters["changes"]
    ):
        raise _fail(failure_type, "business_rule_error", "Source-linked invoice business lines cannot change unit or deductibility by this capability.", exit_code=6)
    _validate_invoice_line_references(env, move, [target], company_id, failure_type)
    unit_changed = "product_uom_id" in parameters["changes"] and parameters["changes"]["product_uom_id"] != current["product_uom_id"]
    display_type = getattr(line, "display_type", None)
    line.write(_invoice_line_write_values(parameters["changes"]))
    if unit_changed:
        persisted = _current_invoice_line(line, parameters["changes"])
        expected = _normalized_invoice_replacement_lines([target])[0]
        valid = (
            line.id == parameters["line_id"]
            and _many2one_id(line.move_id) == move.id
            and _many2one_id(line.company_id) == company_id
            and line.id in move.invoice_line_ids.ids
            and getattr(line, "display_type", None) == display_type
            and persisted is not None
            and all(persisted[field] == expected[field] for field in parameters["changes"])
        )
    else:
        valid = _invoice_line_matches(line, target)
    if not valid:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not persist the requested invoice-line update.",
            exit_code=6,
        )
    return _move_result(move, company_id, source_id=line.id), False


def _invoice_bulk_line_snapshot(line: Any) -> dict[str, Any]:
    fields = getattr(line, "_fields", {})
    values: dict[str, Any] = {}
    for field in (
        "name", "display_type", "sequence", "product_id", "account_id", "quantity",
        "price_unit", "discount", "tax_ids", "analytic_distribution",
        *_DEFERRED_LINE_DATE_FIELDS, *_INVOICE_LINE_INPUT_FIELDS,
        "sale_line_ids", "purchase_line_id", "collapse_prices", "collapse_composition",
    ):
        if field not in fields:
            continue
        value = getattr(line, field)
        if field in {"product_id", "account_id", "product_uom_id", "purchase_line_id"}:
            value = _many2one_id(value)
        elif field in {"quantity", "price_unit", "discount", "deductible_amount"}:
            value = _canonical_decimal_text(value)
        elif field in {"tax_ids", "sale_line_ids"}:
            value = _relation_ids(value)
        elif field == "analytic_distribution":
            value = _normalized_analytic_distribution(value)
        elif field in _DEFERRED_LINE_DATE_FIELDS:
            value = _nullable_value(value)
        values[field] = value
    return values


def _invoice_added_lines_match(lines: list[Any], requested: list[dict[str, Any]]) -> bool:
    if len(lines) != len(requested):
        return False
    candidates = [[index for index, line in enumerate(lines) if _invoice_line_matches(line, values)] for values in requested]
    assigned: dict[int, int] = {}

    def assign(request_index: int, visited: set[int]) -> bool:
        for line_index in candidates[request_index]:
            if line_index in visited:
                continue
            visited.add(line_index)
            if line_index not in assigned or assign(assigned[line_index], visited):
                assigned[line_index] = request_index
                return True
        return False

    return all(assign(index, set()) for index in range(len(requested)))


def _write_invoice_bulk_lines(
    env: Any, capability_id: str, parameters: dict[str, Any],
    company_id: int, failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    move = _lifecycle_move(env, capability_id, parameters["move_id"], company_id, failure_type)
    if move.state != "draft":
        raise _fail(failure_type, "state_conflict", "Bulk invoice-line changes require a draft invoice or bill.", exit_code=5)
    before_ids = set(move.invoice_line_ids.ids)
    current_lines = _ensure_ids(env, "account.move.line", before_ids, [
        ("move_id", "=", move.id), ("company_id", "=", company_id),
    ], company_id, failure_type)
    by_id = {line.id: line for line in current_lines}
    updating = capability_id == "invoice.lines.update"
    requested = parameters["lines"]
    targets: dict[int, dict[str, Any]] = {}
    unit_changed: set[int] = set()
    if updating:
        selected_ids = {item["line_id"] for item in requested}
        if not selected_ids <= before_ids:
            raise _fail(failure_type, "record_not_found", "A requested invoice business line was not found.", exit_code=4)
        for item in requested:
            line = by_id[item["line_id"]]
            current = _current_invoice_line(line)
            if current is None:
                raise _fail(failure_type, "record_not_found", "A requested invoice business line was not found.", exit_code=4)
            target = {**current, **item["changes"]}
            _validate_invoice_line_references(env, move, [target], company_id, failure_type)
            current.update(_current_invoice_line_inputs(line, item["changes"]))
            if _journal_item_sourced(line) and (
                "product_id" in item["changes"] and item["changes"]["product_id"] != current["product_id"]
                or any(
                    current[field] != (_canonical_decimal_text(item["changes"][field]) if field == "deductible_amount" else item["changes"][field])
                    for field in _INVOICE_LINE_INPUT_FIELDS if field in item["changes"]
                )
            ):
                raise _fail(failure_type, "business_rule_error", "Source-linked invoice business lines cannot change product, unit or deductibility by this capability.", exit_code=6)
            if "product_uom_id" in item["changes"] and item["changes"]["product_uom_id"] != current["product_uom_id"]:
                unit_changed.add(line.id)
            targets[line.id] = target
        if all(_invoice_line_matches(by_id[item["line_id"]], targets[item["line_id"]]) for item in requested):
            return _move_result(move, company_id), True
        preserved_ids = before_ids - selected_ids
        commands = [(1, item["line_id"], _invoice_line_write_values(item["changes"])) for item in requested]
    else:
        expected_ids = set(parameters["expected_line_ids"])
        _ensure_ids(env, "account.move.line", expected_ids, [
            ("move_id", "=", move.id), ("company_id", "=", company_id),
        ], company_id, failure_type)
        _validate_invoice_line_references(env, move, requested, company_id, failure_type)
        if before_ids != expected_ids:
            appended = [line for line in current_lines if line.id not in expected_ids]
            if expected_ids <= before_ids and _invoice_added_lines_match(appended, requested):
                return _move_result(move, company_id), True
            raise _fail(failure_type, "idempotency_conflict", "The invoice-line membership does not match the requested append state.", exit_code=5)
        preserved_ids = before_ids
        sequence = max((getattr(line, "sequence", 0) for line in current_lines), default=0)
        commands = [(0, 0, {
            "display_type": "product", "sequence": sequence + index * 10,
            **_invoice_line_write_values(values),
        }) for index, values in enumerate(requested, start=1)]
    before = {line_id: _invoice_bulk_line_snapshot(by_id[line_id]) for line_id in preserved_ids}
    selected_identity = {
        line_id: (getattr(by_id[line_id], "display_type", None), _relation_ids(getattr(by_id[line_id], "sale_line_ids", [])), _many2one_id(getattr(by_id[line_id], "purchase_line_id", None)))
        for line_id in targets
    }
    for command in commands:
        for field, value in command[2].items():
            if isinstance(value, Decimal):
                command[2][field] = float(value)
    with env.cr.savepoint():
        move.write({"invoice_line_ids": commands})
        current_lines.invalidate_recordset()
        move.invalidate_recordset()
        final_ids = set(move.invoice_line_ids.ids)
        final_lines = _ensure_ids(env, "account.move.line", final_ids, [
            ("move_id", "=", move.id), ("company_id", "=", company_id),
        ], company_id, failure_type)
        final_by_id = {line.id: line for line in final_lines}
        valid = move.state == "draft" and move.company_id.id == company_id and preserved_ids <= final_ids and before == {
            line_id: _invoice_bulk_line_snapshot(final_by_id[line_id]) for line_id in preserved_ids if line_id in final_by_id
        }
        if updating:
            valid = valid and final_ids == before_ids
            for item in requested:
                line = final_by_id.get(item["line_id"])
                if line is None:
                    valid = False
                    continue
                identity = (getattr(line, "display_type", None), _relation_ids(getattr(line, "sale_line_ids", [])), _many2one_id(getattr(line, "purchase_line_id", None)))
                persisted = _current_invoice_line(line, item["changes"])
                expected = _normalized_invoice_replacement_lines([targets[item["line_id"]]])[0]
                valid = valid and identity == selected_identity[item["line_id"]] and persisted is not None and (
                    all(persisted[field] == expected[field] for field in item["changes"])
                    if item["line_id"] in unit_changed else _invoice_line_matches(line, targets[item["line_id"]])
                )
        else:
            valid = valid and _invoice_added_lines_match([line for line in final_lines if line.id not in before_ids], requested)
        if not valid:
            raise _fail(failure_type, "odoo_write_error", "Native bulk invoice-line changes did not preserve the requested rows and existing line membership.", exit_code=6)
    return _move_result(move, company_id), False


def _remove_invoice_lines(
    env: Any, parameters: dict[str, Any], company_id: int, failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    move = _lifecycle_move(env, "invoice.lines.remove", parameters["move_id"], company_id, failure_type)
    if move.state != "draft":
        raise _fail(failure_type, "state_conflict", "Only a draft invoice or bill can have business lines removed.", exit_code=5)
    before_ids = set(move.invoice_line_ids.ids)
    current = _ensure_ids(env, "account.move.line", before_ids, [
        ("move_id", "=", move.id), ("company_id", "=", company_id),
    ], company_id, failure_type)
    removed_ids = set(parameters["line_ids"])
    if not removed_ids <= before_ids or any(
        _current_invoice_line(line) is None for line in current if line.id in removed_ids
    ):
        raise _fail(failure_type, "record_not_found", "A requested invoice business line was not found.", exit_code=4)
    retained_ids = before_ids - removed_ids
    before = {line.id: _invoice_bulk_line_snapshot(line) for line in current if line.id in retained_ids}
    with env.cr.savepoint():
        move.write({"invoice_line_ids": [(2, line_id, 0) for line_id in parameters["line_ids"]]})
        current.invalidate_recordset()
        move.invalidate_recordset()
        final_ids = set(move.invoice_line_ids.ids)
        final = _ensure_ids(env, "account.move.line", final_ids, [
            ("move_id", "=", move.id), ("company_id", "=", company_id),
        ], company_id, failure_type)
        valid = (
            move.state == "draft" and move.company_id.id == company_id and final_ids == retained_ids
            and before == {line.id: _invoice_bulk_line_snapshot(line) for line in final}
            and not _scoped(env, "account.move.line", company_id).search_count([("id", "in", sorted(removed_ids))], limit=1)
        )
        if not valid:
            raise _fail(failure_type, "odoo_write_error", "Native invoice-line removal did not preserve the remaining rows or delete every requested business line.", exit_code=6)
    return _move_result(move, company_id), False


def _delete_invoice_line(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    move = _lifecycle_move(
        env, "invoice.line.delete", parameters["move_id"], company_id, failure_type
    )
    if move.state != "draft":
        raise _fail(
            failure_type,
            "state_conflict",
            "Only a draft invoice or bill can have a business line deleted.",
            exit_code=5,
        )
    line = _invoice_line(
        env, move, parameters["line_id"], company_id, failure_type
    )
    line_id = line.id
    line.unlink()
    if _scoped(env, "account.move.line", company_id).search_count(
        [("id", "=", line_id)], limit=1
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not delete the requested invoice business line.",
            exit_code=6,
        )
    return _move_result(move, company_id, source_id=line_id), False


_GENERATED_ENTRY_LINK_FIELDS = (
    "origin_payment_id",
    "statement_line_id",
    "tax_cash_basis_origin_move_id",
    "reversed_entry_id",
    "reversal_move_ids",
    "auto_post_origin_id",
    "asset_id",
    "asset_value_change",
    "deferred_original_move_ids",
    "transfer_model_id",
)


def _generated_entry(move: Any) -> bool:
    fields = getattr(move, "_fields", {})
    if "auto_post" in fields and getattr(move, "auto_post", "no") not in {
        False,
        None,
        "no",
    }:
        return True
    return any(
        field_name in fields and bool(getattr(move, field_name, False))
        for field_name in _GENERATED_ENTRY_LINK_FIELDS
    )


def _entry_line_membership_snapshot(line: Any) -> dict[str, Any]:
    values = _journal_item_current(line, journal_item_processing.ENTRY_FIELDS)
    values["sequence"] = getattr(line, "sequence", 0)
    fields = getattr(line, "_fields", {})
    for field in (
        "balance", "quantity", "price_unit", "discount", "tax_base_amount",
    ):
        if field in fields:
            values[field] = _canonical_decimal_text(getattr(line, field))
    for field in ("tax_ids", "tax_tag_ids"):
        if field in fields:
            values[field] = _relation_ids(getattr(line, field))
    for field in (
        "product_id", "tax_line_id", "tax_repartition_line_id", "group_tax_id",
    ):
        if field in fields:
            values[field] = _many2one_id(getattr(line, field))
    for field in ("display_type", "tax_tag_invert", "date"):
        if field in fields:
            values[field] = _nullable_value(getattr(line, field))
    return values


def _write_entry_line_membership(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    move = _lifecycle_move(
        env, capability_id, parameters["move_id"], company_id, failure_type
    )
    if move.state != "draft":
        raise _fail(
            failure_type, "state_conflict",
            "Journal-entry lines can only be added or removed in draft.", exit_code=5,
        )
    current_ids = set(move.line_ids.ids)
    current = _ensure_ids(
        env, "account.move.line", current_ids,
        [("move_id", "=", move.id), ("company_id", "=", company_id)],
        company_id, failure_type,
    )
    if _generated_entry(move) or any(_journal_item_sourced(line) for line in current):
        raise _fail(
            failure_type, "business_rule_error",
            "Only an ordinary source-unlinked general journal entry can have lines added or removed.",
            exit_code=6,
        )

    adding = capability_id == "journal_entry.lines.add"
    if adding:
        expected_ids = set(parameters["expected_line_ids"])
        requested = parameters["lines"]
        company_currency_id = _validate_entry_line_references(
            env, requested, company_id, failure_type
        )
        if current_ids != expected_ids:
            appended = [line for line in current if line.id not in expected_ids]
            if expected_ids <= current_ids and _entry_lines_match(
                _current_entry_lines(SimpleNamespace(line_ids=appended)),
                requested, company_currency_id,
            ):
                return _move_result(move, company_id), True
            raise _fail(
                failure_type, "idempotency_conflict",
                "The journal-entry line set does not match the requested append state.",
                exit_code=5,
            )
        retained_ids = expected_ids
        sequence = max((getattr(line, "sequence", 0) for line in current), default=0)
        commands = _replacement_commands(capability_id, requested)[1:]
        for index, command in enumerate(commands, start=1):
            command[2]["sequence"] = sequence + index * 10
    else:
        removed_ids = set(parameters["line_ids"])
        _ensure_ids(
            env, "account.move.line", removed_ids,
            [("move_id", "=", move.id), ("company_id", "=", company_id)],
            company_id, failure_type,
        )
        retained_ids = current_ids - removed_ids
        commands = [(2, line_id, 0) for line_id in parameters["line_ids"]]

    before = {
        line.id: _entry_line_membership_snapshot(line)
        for line in current if line.id in retained_ids
    }
    with env.cr.savepoint():
        move.write({"line_ids": commands})
        current.invalidate_recordset()
        move.invalidate_recordset()
        final_ids = set(move.line_ids.ids)
        final = _ensure_ids(
            env, "account.move.line", final_ids,
            [("move_id", "=", move.id), ("company_id", "=", company_id)],
            company_id, failure_type,
        )
        preserved = {
            line.id: _entry_line_membership_snapshot(line)
            for line in final if line.id in retained_ids
        }
        valid = move.state == "draft" and preserved == before
        if adding:
            appended = [line for line in final if line.id not in expected_ids]
            valid = valid and expected_ids <= final_ids and _entry_lines_match(
                _current_entry_lines(SimpleNamespace(line_ids=appended)),
                requested, company_currency_id,
            )
        else:
            valid = valid and final_ids == retained_ids
        if not valid:
            raise _fail(
                failure_type, "odoo_write_error",
                "Native journal-entry line membership did not preserve the requested state and existing rows.",
                exit_code=6,
            )
    return _move_result(move, company_id), False


def _delete_draft_move(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    move = _lifecycle_move(
        env, capability_id, parameters["move_id"], company_id, failure_type
    )
    if (
        move.state != "draft"
        or bool(move.posted_before)
        or (capability_id == "journal_entry.delete" and _generated_entry(move))
    ):
        raise _fail(
            failure_type,
            "state_conflict",
            "Only a never-posted ordinary draft document can be deleted.",
            exit_code=5,
        )
    move_id = move.id
    result = _deleted_result(_move_result(move, company_id))
    move.unlink()
    if _scoped(env, "account.move", company_id).search_count(
        [("id", "=", move_id)], limit=1
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not delete the requested draft accounting document.",
            exit_code=6,
        )
    return result, False


def _duplicate_journal_entry(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    key: str,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    source = _lifecycle_move(
        env,
        "journal_entry.duplicate",
        parameters["move_id"],
        company_id,
        failure_type,
    )
    if _generated_entry(source):
        raise _fail(
            failure_type,
            "business_rule_error",
            "Generated journal entries cannot be duplicated by this capability.",
            exit_code=6,
        )
    key_marker = _idempotency_key_marker(
        "journal_entry.duplicate", company_id, key
    )
    operation_marker = _operation_marker(
        "journal_entry.duplicate", key, parameters
    )
    candidates = _scoped(env, "account.move", company_id).search(
        [
            ("company_id", "=", company_id),
            ("move_type", "=", "entry"),
            ("id", "!=", source.id),
            ("invoice_origin", "ilike", key_marker),
        ],
        limit=2,
    )
    candidates = candidates.filtered(lambda move: _move_has_marker(move, key_marker))
    if candidates:
        if (
            len(candidates) != 1
            or not _move_has_marker(candidates, operation_marker)
            or candidates.state != "draft"
            or bool(candidates.posted_before)
            or not candidates.journal_id
            or candidates.journal_id.type != "general"
            or _generated_entry(candidates)
        ):
            raise _fail(
                failure_type,
                "idempotency_conflict",
                "The journal-entry duplication key conflicts with another entry.",
                exit_code=5,
            )
        return _move_result(candidates, company_id, source_id=source.id), True
    preserved_origin = ";".join(
        token
        for token in (
            part.strip() for part in str(source.invoice_origin or "").split(";")
        )
        if token
        and not token.startswith("ODACV4:")
        and not token.startswith("ODACV4K:")
    )
    duplicate = source.copy(default={"invoice_origin": preserved_origin or False})
    if not _is_id(duplicate.id) or duplicate.id == source.id:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not return a new duplicated journal entry.",
            exit_code=6,
        )
    _append_move_marker(duplicate, key_marker, failure_type)
    _append_move_marker(duplicate, operation_marker, failure_type)
    if (
        duplicate.company_id.id != company_id
        or duplicate.move_type != "entry"
        or duplicate.state != "draft"
        or bool(duplicate.posted_before)
        or not duplicate.journal_id
        or duplicate.journal_id.type != "general"
        or _generated_entry(duplicate)
        or not _move_has_marker(duplicate, key_marker)
        or not _move_has_marker(duplicate, operation_marker)
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo returned an invalid duplicated journal entry.",
            exit_code=6,
        )
    return _move_result(duplicate, company_id, source_id=source.id), False


def _transition_move(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    if "move_ids" in parameters:
        moves = _batch_lifecycle_moves(
            env,
            capability_id,
            parameters["move_ids"],
            company_id,
            failure_type,
        )
        cancel = capability_id.endswith(".cancel")
        target_state = "cancel" if cancel else "draft"
        allowed_states = {"draft", "posted", "cancel"}
        if any(move.state not in allowed_states for move in moves):
            raise _fail(
                failure_type,
                "state_conflict",
                "An accounting move cannot make the requested state transition.",
                exit_code=5,
            )
        pending = moves.filtered(lambda move: move.state != target_state)
        replay = not pending
        if pending:
            if cancel:
                pending.button_cancel()
            else:
                pending.button_draft()
        if any(move.state != target_state for move in moves):
            raise _fail(
                failure_type,
                "odoo_write_error",
                "Odoo did not persist every requested accounting move state.",
                exit_code=6,
            )
        return _move_batch_result(moves, company_id), replay

    move = _lifecycle_move(
        env, capability_id, parameters["move_id"], company_id, failure_type
    )
    cancel = capability_id.endswith(".cancel")
    target_state = "cancel" if cancel else "draft"
    if move.state == target_state:
        return _move_result(move, company_id), True
    allowed_states = {"draft", "posted"} if cancel else {"posted", "cancel"}
    if move.state not in allowed_states:
        raise _fail(
            failure_type,
            "state_conflict",
            "The accounting move cannot make the requested state transition.",
            exit_code=5,
        )
    if cancel:
        move.button_cancel()
    else:
        move.button_draft()
    if move.state != target_state:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not persist the requested accounting move state.",
            exit_code=6,
        )
    return _move_result(move, company_id), False


def _duplicate_invoice(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    key: str,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    source = _search_one(
        env,
        "account.move",
        [
            ("id", "=", parameters["move_id"]),
            ("company_id", "=", company_id),
            ("move_type", "in", list(_DOCUMENT_TYPES)),
        ],
        company_id,
        failure_type,
    )
    key_marker = _idempotency_key_marker(capability_id, company_id, key)
    operation_marker = _operation_marker(capability_id, key, parameters)
    candidates = _scoped(env, "account.move", company_id).search(
        [
            ("company_id", "=", company_id),
            ("move_type", "in", list(_DOCUMENT_TYPES)),
            ("invoice_origin", "ilike", key_marker),
        ]
    )
    candidates = candidates.filtered(
        lambda move: _move_has_marker(move, key_marker)
    )
    if candidates:
        if (
            len(candidates) != 1
            or not _move_has_marker(candidates, operation_marker)
            or candidates.state != "draft"
            or bool(candidates.posted_before)
            or candidates.move_type != source.move_type
            or candidates.payment_state != "not_paid"
            or bool(candidates.reconciled_payment_ids)
        ):
            raise _fail(
                failure_type,
                "idempotency_conflict",
                "The invoice duplication key conflicts with another document.",
                exit_code=5,
            )
        return _move_result(candidates, company_id, source_id=source.id), True
    preserved_origin = ";".join(
        token
        for token in (
            part.strip() for part in str(source.invoice_origin or "").split(";")
        )
        if token
        and not token.startswith("ODACV4:")
        and not token.startswith("ODACV4K:")
    )
    duplicate = source.copy(default={"invoice_origin": preserved_origin or False})
    duplicate_id = duplicate.id
    if not _is_id(duplicate_id) or duplicate_id == source.id:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not return a new duplicated invoice.",
            exit_code=6,
        )
    duplicate = _search_one(
        env,
        "account.move",
        [
            ("id", "=", duplicate_id),
            ("company_id", "=", company_id),
            ("move_type", "=", source.move_type),
        ],
        company_id,
        failure_type,
    )
    origin_tokens = [
        token.strip()
        for token in str(duplicate.invoice_origin or "").split(";")
        if token.strip()
    ]
    for marker in (key_marker, operation_marker):
        if marker not in origin_tokens:
            origin_tokens.append(marker)
    duplicate.write({"invoice_origin": ";".join(origin_tokens)})
    if (
        duplicate.state != "draft"
        or bool(duplicate.posted_before)
        or duplicate.payment_state != "not_paid"
        or bool(duplicate.reconciled_payment_ids)
        or not _move_has_marker(duplicate, key_marker)
        or not _move_has_marker(duplicate, operation_marker)
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo returned an invalid duplicated invoice.",
            exit_code=6,
        )
    return _move_result(duplicate, company_id, source_id=source.id), False


def _switch_invoice_type(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    move = _search_one(
        env,
        "account.move",
        [
            ("id", "=", parameters["move_id"]),
            ("company_id", "=", company_id),
            ("move_type", "in", list(_DOCUMENT_TYPES)),
        ],
        company_id,
        failure_type,
    )
    if move.state != "draft" or bool(move.posted_before):
        raise _fail(
            failure_type,
            "state_conflict",
            "Only a never-posted draft invoice can switch document type.",
            exit_code=5,
        )
    target = parameters["target_move_type"]
    if move.move_type == target:
        return _move_result(move, company_id, source_id=move.id), True
    expected_target = {
        "out_invoice": "out_refund",
        "out_refund": "out_invoice",
        "in_invoice": "in_refund",
        "in_refund": "in_invoice",
    }[move.move_type]
    if target != expected_target:
        raise _fail(
            failure_type,
            "state_conflict",
            "The requested invoice type is not the native counterpart type.",
            exit_code=5,
        )
    move.action_switch_move_type()
    if move.state != "draft" or move.move_type != target or bool(move.posted_before):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not switch the invoice to the requested type.",
            exit_code=6,
        )
    return _move_result(move, company_id, source_id=move.id), False


def _post_move(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    if "move_ids" in parameters:
        moves = _batch_lifecycle_moves(
            env,
            capability_id,
            parameters["move_ids"],
            company_id,
            failure_type,
        )
        if any(move.state not in {"draft", "posted"} for move in moves):
            raise _fail(
                failure_type,
                "state_conflict",
                "Only draft accounting moves can be posted.",
                exit_code=5,
            )
        pending = moves.filtered(lambda move: move.state != "posted")
        replay = not pending
        if pending:
            pending.action_post()
        if any(move.state != "posted" for move in moves):
            raise _fail(
                failure_type,
                "odoo_write_error",
                "Odoo did not post every requested accounting move.",
                exit_code=6,
            )
        return _move_batch_result(moves, company_id), replay

    move_types: Any = _DOCUMENT_TYPES if capability_id == "invoice.post" else ("entry",)
    move = _search_one(
        env,
        "account.move",
        [
            ("id", "=", parameters["move_id"]),
            ("company_id", "=", company_id),
            ("move_type", "in", list(move_types)),
        ],
        company_id,
        failure_type,
    )
    if move.state == "posted":
        return _move_result(move, company_id), True
    if move.state != "draft":
        raise _fail(
            failure_type,
            "state_conflict",
            "Only a draft accounting move can be posted.",
            exit_code=5,
        )
    move.action_post()
    return _move_result(move, company_id), False


def _reverse_entry(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    marker: str,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    source = _search_one(
        env,
        "account.move",
        [
            ("id", "=", parameters["move_id"]),
            ("company_id", "=", company_id),
            ("move_type", "=", "entry"),
        ],
        company_id,
        failure_type,
    )
    reversals = _scoped(env, "account.move", company_id).search(
        [
            ("company_id", "=", company_id),
            ("reversed_entry_id", "=", source.id),
        ],
        limit=2,
    )
    if reversals:
        if len(reversals) != 1 or reversals.invoice_origin != marker:
            raise _fail(
                failure_type,
                "idempotency_conflict",
                "The journal entry already has a different reversal.",
                exit_code=5,
            )
        return _move_result(reversals, company_id, source_id=source.id), True
    if source.state != "posted":
        raise _fail(
            failure_type,
            "state_conflict",
            "Only a posted journal entry can be reversed.",
            exit_code=5,
        )
    wizard = (
        _scoped(env, "account.move.reversal", company_id)
        .with_context(active_model="account.move", active_ids=[source.id])
        .create(
            {
                "date": parameters["date"],
                "reason": parameters["reason"],
                "journal_id": source.journal_id.id,
            }
        )
    )
    wizard.reverse_moves()
    reversals = wizard.new_move_ids
    if len(reversals) != 1 or reversals.reversed_entry_id != source:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo returned an invalid reversal result.",
            exit_code=6,
        )
    reversals.write({"invoice_origin": marker})
    return _move_result(reversals, company_id, source_id=source.id), False


def _reverse_and_reissue_invoice(
    env: Any, parameters: dict[str, Any], company_id: int,
    key: str, marker: str, failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    capability_id = "invoice.reverse_and_reissue"
    with env.cr.savepoint():
        source = _search_one(env, "account.move", [
            ("id", "=", parameters["move_id"]), ("company_id", "=", company_id),
            ("move_type", "in", ["out_invoice", "in_invoice"]),
        ], company_id, failure_type)
        if source.state != "posted":
            raise _fail(failure_type, "state_conflict", "Only a posted invoice or bill can be reversed and reissued.", exit_code=5)
        if date.fromisoformat(parameters["date"]) > source._fields["date"].context_today(source):
            raise _fail(failure_type, "business_rule_error", "Reissue requires a current or past native reversal date.", exit_code=6)
        refund_type = "out_refund" if source.move_type == "out_invoice" else "in_refund"
        key_marker = _idempotency_key_marker(capability_id, company_id, key)
        operation_marker = f"{_operation_marker(capability_id, key, parameters)};{key_marker};{marker}"

        def verified_pair(moves: Any, code: str) -> dict[str, Any]:
            refunds = moves.filtered(lambda move: move.move_type == refund_type)
            replacements = moves.filtered(lambda move: move.move_type == source.move_type)
            if (len(moves) != 2 or len(refunds) != 1 or len(replacements) != 1
                or refunds.state != "posted" or refunds.reversed_entry_id != source
                or replacements.state != "draft" or replacements.reversed_entry_id
                or source.state != "posted" or any(
                    move.id == source.id or move.company_id.id != company_id
                    or move.invoice_origin != operation_marker or not move.line_ids
                    for move in moves
                )):
                raise _fail(failure_type, code, "The reissue operation does not identify one posted reversal and one draft replacement.", exit_code=5 if code == "idempotency_conflict" else 6)
            return {"items": [
                _move_result(move, company_id, source_id=source.id)
                for move in moves.sorted(lambda move: move.id)
            ], "processed_count": 2}

        candidates = _scoped(env, "account.move", company_id).search([
            ("company_id", "=", company_id), ("invoice_origin", "ilike", key_marker),
        ], limit=3).filtered(lambda move: _move_has_marker(move, key_marker))
        if candidates:
            return verified_pair(candidates, "idempotency_conflict"), True
        if source.reversal_move_ids:
            raise _fail(failure_type, "idempotency_conflict", "The invoice already has a reversal outside this reissue operation.", exit_code=5)
        wizard = _scoped(env, "account.move.reversal", company_id).with_context(
            active_model="account.move", active_ids=[source.id],
        ).create({"date": parameters["date"], "reason": parameters["reason"], "journal_id": source.journal_id.id})
        wizard.modify_moves()
        source.invalidate_recordset()
        refunds = _scoped(env, "account.move", company_id).search([
            ("company_id", "=", company_id), ("reversed_entry_id", "=", source.id),
            ("move_type", "=", refund_type),
        ], limit=2)
        replacements = _ensure_ids(env, "account.move", set(wizard.new_move_ids.ids), [
            ("company_id", "=", company_id), ("move_type", "=", source.move_type),
        ], company_id, failure_type)
        moves = refunds | replacements
        if len(refunds) != 1 or len(replacements) != 1:
            raise _fail(failure_type, "odoo_write_error", "Native reissue did not create exactly two accounting documents.", exit_code=6)
        moves.write({"invoice_origin": operation_marker})
        moves.invalidate_recordset()
        return verified_pair(moves, "odoo_write_error"), False


def _create_refund(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    key: str,
    marker: str,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    if "move_ids" in parameters:
        return _create_refund_round(env, capability_id, parameters, company_id, key, marker, failure_type)
    source_type = (
        "out_invoice"
        if capability_id == "customer_credit_note.create"
        else "in_invoice"
    )
    refund_type = "out_refund" if source_type == "out_invoice" else "in_refund"
    if "lines" in parameters:
        _validate_invoice_line_inputs(env, parameters["lines"], company_id, failure_type, refund_type)
    source = _search_one(
        env,
        "account.move",
        [
            ("id", "=", parameters["move_id"]),
            ("company_id", "=", company_id),
            ("move_type", "=", source_type),
        ],
        company_id,
        failure_type,
    )
    key_marker = _idempotency_key_marker(capability_id, company_id, key)
    operation_marker = (
        f"{_operation_marker(capability_id, key, parameters)};{key_marker};{marker}"
    )
    key_refunds = _scoped(env, "account.move", company_id).search(
        [
            ("company_id", "=", company_id),
            ("reversed_entry_id", "=", source.id),
            ("move_type", "=", refund_type),
            ("invoice_origin", "ilike", key_marker),
        ],
        limit=2,
    )
    key_refunds = key_refunds.filtered(
        lambda refund: _move_has_marker(refund, key_marker)
    )
    refunds = key_refunds.filtered(
        lambda refund: refund.invoice_origin == operation_marker
    )
    if key_refunds and len(refunds) != len(key_refunds):
        raise _fail(
            failure_type,
            "idempotency_conflict",
            "The refund operation key was already used with different parameters.",
            exit_code=5,
        )
    if refunds:
        if len(refunds) != 1:
            raise _fail(
                failure_type,
                "idempotency_conflict",
                "The refund operation key identifies multiple records.",
                exit_code=5,
            )
        if "lines" in parameters and not _invoice_lines_match(
            _current_invoice_lines(refunds, parameters["lines"]), parameters["lines"]
        ):
            raise _fail(
                failure_type,
                "idempotency_conflict",
                "The refund operation key conflicts with different lines.",
                exit_code=5,
            )
        return _move_result(refunds, company_id, source_id=source.id), True
    legacy_key = f"{capability_id}:{source.id}"
    if "lines" not in parameters and key == legacy_key:
        legacy_refunds = _scoped(env, "account.move", company_id).search(
            [
                ("company_id", "=", company_id),
                ("reversed_entry_id", "=", source.id),
                ("move_type", "=", refund_type),
                ("invoice_origin", "=", marker),
            ],
            limit=2,
        )
        if legacy_refunds:
            if len(legacy_refunds) != 1:
                raise _fail(
                    failure_type,
                    "idempotency_conflict",
                    "The legacy refund marker identifies multiple records.",
                    exit_code=5,
                )
            return _move_result(legacy_refunds, company_id, source_id=source.id), True
    if source.state != "posted":
        raise _fail(
            failure_type,
            "state_conflict",
            "Only a posted invoice or bill can be refunded.",
            exit_code=5,
        )
    if "lines" in parameters:
        _validate_invoice_line_references(
            env, source, parameters["lines"], company_id, failure_type
        )
    wizard = (
        _scoped(env, "account.move.reversal", company_id)
        .with_context(active_model="account.move", active_ids=[source.id])
        .create(
            {
                "date": parameters["date"],
                "reason": parameters["reason"],
                "journal_id": source.journal_id.id,
            }
        )
    )
    wizard.refund_moves()
    refunds = wizard.new_move_ids
    if (
        len(refunds) != 1
        or refunds.reversed_entry_id != source
        or refunds.move_type != refund_type
        or refunds.state != "draft"
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo returned an invalid refund result.",
            exit_code=6,
        )
    refunds.write({"invoice_origin": operation_marker})
    if "lines" in parameters:
        refunds.write(
            {
                "invoice_line_ids": _replacement_commands(
                    capability_id, parameters["lines"]
                )
            }
        )
    refunds = _search_one(
        env,
        "account.move",
        [
            ("id", "=", refunds.id),
            ("company_id", "=", company_id),
            ("move_type", "=", refund_type),
            ("state", "=", "draft"),
            ("invoice_origin", "=", operation_marker),
        ],
        company_id,
        failure_type,
    )
    if "lines" in parameters and not _invoice_lines_match(
        _current_invoice_lines(refunds, parameters["lines"]), parameters["lines"]
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not persist the requested refund lines.",
            exit_code=6,
        )
    return _move_result(refunds, company_id, source_id=source.id), False


def _round_moves_for_key(env: Any, capability_id: str, parameters: dict[str, Any], company_id: int,
                         key: str, failure_type: type[Exception]) -> tuple[Any, str, str]:
    key_marker = _idempotency_key_marker(capability_id, company_id, key)
    operation_marker = _operation_marker(capability_id, key, parameters)
    moves = _scoped(env, "account.move", company_id).search([
        ("company_id", "=", company_id), ("invoice_origin", "ilike", key_marker),
    ], order="id", limit=1001).filtered(lambda move: _move_has_marker(move, key_marker))
    if moves and (len(moves) > 1000 or any(not _move_has_marker(move, operation_marker) for move in moves)):
        raise _fail(failure_type, "idempotency_conflict", "The operation key was already used with other parameters.", exit_code=5)
    return moves, operation_marker, key_marker


def _mark_invoice_round(move: Any, operation_marker: str, key_marker: str, failure_type: type[Exception]) -> None:
    tokens = [token.strip() for token in str(move.invoice_origin or "").split(";") if token.strip()]
    for marker in (operation_marker, key_marker):
        if marker not in tokens:
            tokens.append(marker)
    move.write({"invoice_origin": ";".join(tokens)})
    if not _move_has_marker(move, operation_marker) or not _move_has_marker(move, key_marker):
        raise _fail(failure_type, "odoo_write_error", "Odoo did not retain the invoice operation markers.", exit_code=6)


def _create_refund_round(env: Any, capability_id: str, parameters: dict[str, Any], company_id: int,
                         key: str, marker: str, failure_type: type[Exception]) -> tuple[dict[str, Any], bool]:
    source_type = "out_invoice" if capability_id == "customer_credit_note.create" else "in_invoice"
    refund_type = "out_refund" if source_type == "out_invoice" else "in_refund"
    sources = _ensure_ids(env, "account.move", set(parameters["move_ids"]), [
        ("company_id", "=", company_id), ("move_type", "=", source_type),
    ], company_id, failure_type)
    existing, operation_marker, key_marker = _round_moves_for_key(
        env, capability_id, parameters, company_id, key, failure_type,
    )
    by_id = {source.id: source for source in sources}

    def verified(refunds: Any, code: str) -> dict[str, Any]:
        source_ids = [_many2one_id(refund.reversed_entry_id) for refund in refunds]
        if (len(refunds) != len(sources) or set(source_ids) != set(by_id)
                or any(refund.company_id.id != company_id or refund.move_type != refund_type
                       or refund.state not in ({"draft", "posted", "cancel"} if code == "idempotency_conflict" else {"draft"})
                       or str(refund.date) != parameters["date"]
                       or refund.currency_id.id != by_id[refund.reversed_entry_id.id].currency_id.id
                       or refund.partner_id.id != by_id[refund.reversed_entry_id.id].partner_id.id
                       or refund.journal_id.id != by_id[refund.reversed_entry_id.id].journal_id.id
                       or _rounded_currency_amount(refund.currency_id, str(refund.amount_total))
                       != _rounded_currency_amount(by_id[refund.reversed_entry_id.id].currency_id, str(by_id[refund.reversed_entry_id.id].amount_total))
                       for refund in refunds)):
            raise _fail(failure_type, code, "Odoo did not return the full source-linked refund set.", exit_code=5 if code == "idempotency_conflict" else 6)
        items = [_move_result(refund, company_id, source_id=refund.reversed_entry_id.id)
                 for refund in sorted(refunds, key=lambda record: record.id)]
        return {"items": items, "processed_count": len(items)}

    if existing:
        return verified(existing, "idempotency_conflict"), True
    if any(source.state != "posted" for source in sources):
        raise _fail(failure_type, "state_conflict", "Only posted source documents can be refunded.", exit_code=5)
    refunds = _scoped(env, "account.move", company_id).browse([])
    for source in sorted(sources, key=lambda record: record.id):
        wizard = _scoped(env, "account.move.reversal", company_id).with_context(
            active_model="account.move", active_ids=[source.id],
        ).create({"move_ids": [(6, 0, [source.id])], "journal_id": source.journal_id.id,
                  "date": parameters["date"], "reason": parameters["reason"]})
        wizard.refund_moves()
        refunds |= wizard.new_move_ids
    result = verified(refunds, "odoo_write_error")
    refunds.write({"invoice_origin": f"{operation_marker};{key_marker};{marker}"})
    return result, False


def _payment_sources(payment: Any) -> set[int]:
    return set(_record_ids(payment.reconciled_invoice_ids)) | set(
        _record_ids(payment.reconciled_bill_ids)
    )


def _round_payment_sources(payment: Any) -> set[int]:
    lines = payment.move_id.line_ids.filtered(
        lambda line: line.account_id.account_type in {"asset_receivable", "liability_payable"}
    )
    partials = lines.matched_debit_ids | lines.matched_credit_ids
    counterparts = partials.debit_move_id.move_id | partials.credit_move_id.move_id
    return {move.id for move in counterparts
            if move.id != payment.move_id.id and move.move_type in _DOCUMENT_TYPES}


def _rounded_currency_amount(currency: Any, value: str) -> Decimal:
    return Decimal(str(currency.round(float(Decimal(value)))))


def _register_payment_references(
    env: Any, parameters: dict[str, Any], payment_type: str,
    company_id: int, failure_type: type[Exception],
) -> dict[str, int]:
    references = {
        field: parameters[field]
        for field in _PAYMENT_REGISTER_REFERENCE_FIELDS if field in parameters
    }
    if not references:
        return references
    journal = _search_one(
        env, "account.journal",
        [("id", "=", parameters["journal_id"]), ("company_id", "=", company_id),
         ("type", "in", ["bank", "cash"])],
        company_id, failure_type,
    )
    if "payment_method_line_id" in references:
        _ensure_ids(
            env, "account.payment.method.line", {references["payment_method_line_id"]},
            [("journal_id", "=", journal.id), ("payment_type", "=", payment_type)],
            company_id, failure_type,
        )
    if "partner_bank_id" in references:
        _ensure_ids(
            env, "res.partner.bank", {references["partner_bank_id"]},
            [("company_id", "in", [False, company_id])], company_id, failure_type,
        )
    return references


def _register_payment_references_match(
    payment: Any, references: dict[str, int], payment_type: str,
) -> bool:
    return not references or (
        payment.payment_type == payment_type
        and all(_many2one_id(getattr(payment, field)) == value for field, value in references.items())
    )


def _validate_register_wizard_references(
    wizard: Any, references: dict[str, int], payment_type: str,
    failure_type: type[Exception],
) -> None:
    if not references:
        return
    if "partner_bank_id" in references and not (
        wizard.can_edit_wizard and wizard.batches
        and (len(wizard.batches[0]["lines"]) == 1 or wizard.group_payment)
    ):
        raise _fail(
            failure_type, "state_conflict",
            "The native non-editable payment route cannot carry an explicit bank selection.",
            exit_code=5,
        )
    if not _register_payment_references_match(wizard, references, payment_type) or any(
        value not in getattr(wizard, "available_payment_method_line_ids" if field == "payment_method_line_id" else "available_partner_bank_ids").ids
        for field, value in references.items()
    ):
        raise _fail(
            failure_type, "business_rule_error",
            "The native payment wizard cannot honor the requested payment method or bank account.",
            exit_code=6,
        )


def _register_many_payments(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    key: str,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    move_ids = parameters["move_ids"]
    move_type = (
        "out_invoice"
        if capability_id == "receivable.payment.register"
        else "in_invoice"
    )
    sources = _scoped(env, "account.move", company_id).search(
        [
            ("id", "in", move_ids),
            ("company_id", "=", company_id),
            ("move_type", "=", move_type),
        ]
    )
    if set(_record_ids(sources)) != set(move_ids):
        raise _fail(
            failure_type,
            "record_not_found",
            "One or more payment source documents were not found.",
            exit_code=4,
        )
    partner_ids = set(_record_ids(sources.partner_id))
    currency_ids = set(_record_ids(sources.currency_id))
    if len(partner_ids) != 1 or len(currency_ids) != 1:
        raise _fail(
            failure_type,
            "state_conflict",
            "Batch payment sources must use one partner and one currency.",
            exit_code=5,
        )
    if any(source.state != "posted" for source in sources):
        raise _fail(
            failure_type,
            "state_conflict",
            "Every batch payment source must be posted.",
            exit_code=5,
        )
    payment_type = "inbound" if move_type == "out_invoice" else "outbound"
    references = _register_payment_references(
        env, parameters, payment_type, company_id, failure_type
    )
    operation_marker = _operation_marker(capability_id, key, parameters)
    candidates = _scoped(env, "account.payment", company_id).search(
        [("company_id", "=", company_id), ("memo", "=", key)], limit=2
    )
    if candidates:
        payment = candidates if len(candidates) == 1 else None
        if (
            payment is None
            or payment.state == "canceled"
            or payment.journal_id.id != parameters["journal_id"]
            or str(payment.date) != parameters["payment_date"]
            or payment.move_id.invoice_origin != operation_marker
            or _payment_sources(payment) != set(move_ids)
            or not _register_payment_references_match(payment, references, payment_type)
        ):
            raise _fail(
                failure_type,
                "idempotency_conflict",
                "The payment idempotency key conflicts with another payment.",
                exit_code=5,
            )
        return _payment_result(payment, company_id, source_id=None), True
    if any(Decimal(str(source.amount_residual)) <= 0 for source in sources):
        raise _fail(
            failure_type,
            "state_conflict",
            "Every batch payment source must have a posted positive residual.",
            exit_code=5,
        )
    currency = next(iter(sources)).currency_id
    total_residual = _rounded_currency_amount(
        currency, str(sum(Decimal(str(source.amount_residual)) for source in sources))
    )
    _ensure_ids(
        env,
        "account.journal",
        {parameters["journal_id"]},
        [("company_id", "=", company_id), ("type", "in", ["bank", "cash"])],
        company_id,
        failure_type,
    )
    wizard = (
        _scoped(env, "account.payment.register", company_id)
        .with_context(
            active_model="account.move",
            active_ids=move_ids,
            default_invoice_origin=operation_marker,
        )
        .create(
            {
                "journal_id": parameters["journal_id"],
                "payment_date": parameters["payment_date"],
                "communication": key,
                "installments_mode": "full",
                "group_payment": True,
                **references,
            }
        )
    )
    _validate_register_wizard_references(wizard, references, payment_type, failure_type)
    if (
        len(wizard.batches) != 1
        or not wizard.can_edit_wizard
        or not wizard.can_group_payments
        or not wizard.group_payment
        or wizard.early_payment_discount_mode
        or wizard.writeoff_is_exchange_account
        or wizard.currency_id.id != currency.id
        or _rounded_currency_amount(currency, str(wizard.amount)) != total_residual
        or _rounded_currency_amount(currency, str(wizard.payment_difference)) != 0
    ):
        raise _fail(
            failure_type,
            "state_conflict",
            "The native payment wizard cannot combine these documents into one full payment.",
            exit_code=5,
        )
    wizard.action_create_payments()
    payments = _scoped(env, "account.payment", company_id).search(
        [("company_id", "=", company_id), ("memo", "=", key)], limit=2
    )
    if len(payments) != 1:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not create exactly one combined payment.",
            exit_code=6,
        )
    payment = payments
    if (
        payment.state == "canceled"
        or payment.memo != key
        or payment.journal_id.id != parameters["journal_id"]
        or str(payment.date) != parameters["payment_date"]
        or payment.move_id.invoice_origin != operation_marker
        or _payment_sources(payment) != set(move_ids)
        or not _register_payment_references_match(payment, references, payment_type)
        or _rounded_currency_amount(currency, str(payment.amount)) != total_residual
        or any(
            _rounded_currency_amount(currency, str(source.amount_residual)) != 0
            for source in sources
        )
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo returned an invalid combined registered payment.",
            exit_code=6,
        )
    return _payment_result(payment, company_id, source_id=None), False


def _register_payment(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    key: str,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    if _payment_round_operation(parameters):
        return _register_payment_round(env, capability_id, parameters, company_id, key, failure_type)
    if "move_ids" in parameters:
        return _register_many_payments(
            env, capability_id, parameters, company_id, key, failure_type
        )
    move_types = (
        ["out_invoice", "out_refund"]
        if capability_id == "receivable.payment.register"
        else ["in_invoice", "in_refund"]
    )
    source = _search_one(
        env,
        "account.move",
        [
            ("id", "=", parameters["move_id"]),
            ("company_id", "=", company_id),
            ("move_type", "in", move_types),
        ],
        company_id,
        failure_type,
    )
    requested_amount = (
        _rounded_currency_amount(source.currency_id, parameters["amount"])
        if "amount" in parameters
        else None
    )
    handling = parameters.get("payment_difference_handling")
    payment_type = "inbound" if source.move_type in {"out_invoice", "in_refund"} else "outbound"
    references = _register_payment_references(
        env, parameters, payment_type, company_id, failure_type
    )
    operation_marker = _operation_marker(capability_id, key, parameters)
    residual = Decimal(str(source.amount_residual))
    candidates = _scoped(env, "account.payment", company_id).search(
        [("company_id", "=", company_id), ("memo", "=", key)], limit=2
    )
    if candidates:
        matching = candidates.filtered(
            lambda payment: source.id in _payment_sources(payment)
        )
        stored_marker = matching.move_id.invoice_origin if len(matching) == 1 else False
        if (
            len(candidates) != 1
            or len(matching) != 1
            or matching.state == "canceled"
            or matching.journal_id.id != parameters["journal_id"]
            or str(matching.date) != parameters["payment_date"]
            or (
                requested_amount is not None
                and _rounded_currency_amount(source.currency_id, str(matching.amount))
                != requested_amount
            )
            or (
                (
                    handling is not None
                    or bool(references)
                    or (
                        isinstance(stored_marker, str)
                        and stored_marker.startswith("ODACV4:")
                    )
                )
                and stored_marker != operation_marker
            )
            or not _register_payment_references_match(matching, references, payment_type)
        ):
            raise _fail(
                failure_type,
                "idempotency_conflict",
                "The payment idempotency key conflicts with another payment.",
                exit_code=5,
            )
        return _payment_result(matching, company_id, source_id=source.id), True
    if requested_amount is not None and not Decimal(0) < requested_amount <= residual:
        raise _fail(
            failure_type,
            "state_conflict",
            "The requested payment amount exceeds the current document residual.",
            exit_code=5,
        )
    if source.state != "posted" or residual <= 0:
        raise _fail(
            failure_type,
            "state_conflict",
            "The source document has no posted residual to pay.",
            exit_code=5,
        )
    _ensure_ids(
        env,
        "account.journal",
        {parameters["journal_id"]},
        [("company_id", "=", company_id), ("type", "in", ["bank", "cash"])],
        company_id,
        failure_type,
    )
    wizard_values: dict[str, Any] = {
        "journal_id": parameters["journal_id"],
        "payment_date": parameters["payment_date"],
        "communication": key,
        **references,
    }
    if requested_amount is not None:
        wizard_values.update(
            {
                "amount": float(requested_amount),
                "payment_difference_handling": "open",
            }
        )
    if handling is not None:
        wizard_values["payment_difference_handling"] = handling
    if handling == "reconcile":
        _ensure_ids(
            env,
            "account.account",
            {parameters["writeoff_account_id"]},
            [("company_ids", "in", [company_id]), ("active", "=", True)],
            company_id,
            failure_type,
        )
        wizard_values.update(
            writeoff_account_id=parameters["writeoff_account_id"],
            installments_mode="full",
            group_payment=True,
        )
        if "writeoff_label" in parameters:
            wizard_values["writeoff_label"] = parameters["writeoff_label"]
    wizard_context = {"active_model": "account.move", "active_ids": [source.id]}
    if handling is not None or references:
        # Native move creation consumes this standard default; no posted write.
        wizard_context["default_invoice_origin"] = operation_marker
    wizard = (
        _scoped(env, "account.payment.register", company_id)
        .with_context(**wizard_context)
        .create(wizard_values)
    )
    _validate_register_wizard_references(wizard, references, payment_type, failure_type)
    if handling is not None and wizard.currency_id.id != source.currency_id.id:
        raise _fail(
            failure_type,
            "state_conflict",
            "The native payment currency differs from the document amount currency.",
            exit_code=5,
        )
    difference = None
    if handling == "reconcile":
        difference = (
            _rounded_currency_amount(source.currency_id, str(residual)) - requested_amount
        )
        if (
            wizard.early_payment_discount_mode
            or wizard.writeoff_is_exchange_account
            or not wizard.can_edit_wizard
            or not wizard.group_payment
            or _rounded_currency_amount(source.currency_id, str(wizard.payment_difference))
            != difference
        ):
            raise _fail(
                failure_type,
                "state_conflict",
                "The native discount, exchange, or installment route cannot honor the explicit write-off.",
                exit_code=5,
            )
    action = wizard.action_create_payments()
    payment_id = action.get("res_id") if isinstance(action, dict) else None
    if _is_id(payment_id):
        payment = _search_one(
            env,
            "account.payment",
            [("id", "=", payment_id), ("company_id", "=", company_id)],
            company_id,
            failure_type,
        )
    else:
        payment = _search_one(
            env,
            "account.payment",
            [("company_id", "=", company_id), ("memo", "=", key)],
            company_id,
            failure_type,
        )
    if (
        source.id not in _payment_sources(payment)
        or payment.memo != key
        or (
            requested_amount is not None
            and _rounded_currency_amount(source.currency_id, str(payment.amount))
            != requested_amount
        )
        or ((handling is not None or references) and payment.move_id.invoice_origin != operation_marker)
        or not _register_payment_references_match(payment, references, payment_type)
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo returned an invalid registered payment.",
            exit_code=6,
        )
    if handling == "reconcile":
        signed_difference = (
            difference
            if source.move_type in {"out_invoice", "in_refund"}
            else -difference
        )
        writeoff_lines = payment.move_id.line_ids.filtered(
            lambda line: line.account_id.id == parameters["writeoff_account_id"]
            and line.name == wizard.writeoff_label
            and line.currency_id.id == source.currency_id.id
            and _rounded_currency_amount(source.currency_id, str(line.amount_currency))
            == signed_difference
        )
        if (
            _rounded_currency_amount(source.currency_id, str(source.amount_residual)) != 0
            or (difference != 0 and len(writeoff_lines) != 1)
        ):
            raise _fail(
                failure_type,
                "odoo_write_error",
                "Odoo did not close the document with the requested write-off account and label.",
                exit_code=6,
            )
    return _payment_result(payment, company_id, source_id=source.id), False


def _register_payment_round(env: Any, capability_id: str, parameters: dict[str, Any], company_id: int,
                            key: str, failure_type: type[Exception]) -> tuple[dict[str, Any], bool]:
    move_ids = parameters.get("move_ids", [parameters.get("move_id")])
    move_types = ["out_invoice", "out_refund"] if capability_id == "receivable.payment.register" else ["in_invoice", "in_refund"]
    sources = _ensure_ids(env, "account.move", set(move_ids), [
        ("company_id", "=", company_id), ("move_type", "in", move_types),
    ], company_id, failure_type)
    source_types = {source.move_type for source in sources}
    if len(source_types) != 1:
        raise _fail(failure_type, "state_conflict", "The selected payment sources must have one native payment direction.", exit_code=5)
    payment_type = "inbound" if next(iter(source_types)) in {"out_invoice", "in_refund"} else "outbound"
    references = _register_payment_references(env, parameters, payment_type, company_id, failure_type)
    existing_moves, operation_marker, key_marker = _round_moves_for_key(
        env, capability_id, parameters, company_id, key, failure_type,
    )
    separate = parameters.get("group_payment") is False

    def verified(payments: Any, code: str, expected: list[tuple[dict[str, Any], set[int]]] | None = None) -> dict[str, Any]:
        rows = sorted(payments, key=lambda payment: payment.id)
        if not 1 <= len(rows) <= 1000 or (not separate and len(rows) != 1):
            raise _fail(failure_type, code, "Odoo returned an invalid native payment count.", exit_code=5 if code == "idempotency_conflict" else 6)
        if expected is not None and len(rows) != len(expected):
            raise _fail(failure_type, code, "Odoo did not create the native payment set.", exit_code=6)
        remaining = list(expected or [])
        linked_by_id = {}
        for payment in rows:
            linked = _round_payment_sources(payment)
            linked_by_id[payment.id] = linked
            currency = payment.currency_id
            if (payment.company_id.id != company_id or payment.move_id.company_id.id != company_id
                    or payment.state == "canceled" or payment.journal_id.id != parameters["journal_id"]
                    or str(payment.date) != parameters["payment_date"] or payment.payment_type != payment_type
                    or not linked or not linked <= set(move_ids)
                    or _rounded_currency_amount(currency, str(payment.amount)) <= 0
                    or not _move_has_marker(payment.move_id, operation_marker) or not _move_has_marker(payment.move_id, key_marker)
                    or not _register_payment_references_match(payment, references, payment_type)
                    or ("amount" in parameters and _rounded_currency_amount(currency, str(payment.amount))
                        != _rounded_currency_amount(currency, parameters["amount"]))):
                raise _fail(failure_type, code, "The payment operation conflicts with its native accounting result.", exit_code=5 if code == "idempotency_conflict" else 6)
            if expected is not None:
                matches = [index for index, (values, source_set) in enumerate(remaining)
                           if linked <= source_set and currency.id == values["currency_id"]
                           and _rounded_currency_amount(currency, str(payment.amount)) == _rounded_currency_amount(currency, str(values["amount"]))
                           and payment.memo == values["memo"]
                           and all(not values.get(field) or _many2one_id(getattr(payment, field)) == values[field]
                                   for field in _PAYMENT_REGISTER_REFERENCE_FIELDS)]
                if not matches:
                    raise _fail(failure_type, code, "Odoo did not retain the native payment amount, references, or source links.", exit_code=6)
                native_values, _source_set = remaining.pop(matches[0])
                for writeoff in native_values.get("write_off_line_vals", []):
                    lines = payment.move_id.line_ids.filtered(
                        lambda line, expected_line=writeoff, payment_currency=currency: line.account_id.id == expected_line["account_id"]
                        and line.name == expected_line["name"] and line.currency_id.id == expected_line["currency_id"]
                        and _rounded_currency_amount(payment_currency, str(line.amount_currency))
                        == _rounded_currency_amount(payment_currency, str(expected_line["amount_currency"]))
                    )
                    if len(lines) != 1:
                        raise _fail(failure_type, code, "Odoo did not retain the native payment write-off account, label, and amount.", exit_code=6)
        items = [_payment_result(payment, company_id, source_id=next(iter(linked)) if len(linked := linked_by_id[payment.id]) == 1 else None)
                 for payment in rows]
        return {"items": items, "processed_count": len(items)} if separate else items[0]

    if existing_moves:
        payments = _scoped(env, "account.payment", company_id).search([
            ("company_id", "=", company_id), ("move_id", "in", existing_moves.ids),
        ], order="id", limit=1001)
        if set(payments.move_id.ids) != set(existing_moves.ids) or len(payments) != len(existing_moves):
            raise _fail(failure_type, "idempotency_conflict", "The payment operation marker identifies a different accounting set.", exit_code=5)
        return verified(payments, "idempotency_conflict"), True
    if any(source.state != "posted" or Decimal(str(source.amount_residual)) <= 0 for source in sources):
        raise _fail(failure_type, "state_conflict", "The selected documents have no posted residual to pay.", exit_code=5)
    _ensure_ids(env, "account.journal", {parameters["journal_id"]}, [
        ("company_id", "=", company_id), ("type", "in", ["bank", "cash"]),
    ], company_id, failure_type)
    context = {"active_model": "account.move", "active_ids": move_ids,
               "default_invoice_origin": f"{operation_marker};{key_marker}"}
    if parameters.get("installments_mode") == "before_date":
        context["active_domain"] = [("next_payment_date", "<=", parameters["installment_cutoff_date"])]
    wizard = _scoped(env, "account.payment.register", company_id).with_context(**context).create({
        "journal_id": parameters["journal_id"], "payment_date": parameters["payment_date"],
        "group_payment": not separate, **references,
    })
    batches = wizard.batches
    edit_mode = bool(wizard.can_edit_wizard and batches and (len(batches[0]["lines"]) == 1 or wizard.group_payment))
    if not separate and (len(batches) != 1 or not edit_mode):
        raise _fail(failure_type, "state_conflict", "The native wizard cannot combine these sources into one editable payment.", exit_code=5)
    if ({"amount", "payment_difference_handling", "writeoff_account_id", "writeoff_label"} & set(parameters)) and not edit_mode:
        raise _fail(failure_type, "state_conflict", "The native non-editable route cannot honor an explicit amount or write-off.", exit_code=5)
    _validate_register_wizard_references(wizard, references, payment_type, failure_type)
    totals = wizard._get_total_amounts_to_pay(batches)
    mode = parameters.get("installments_mode", "full")
    if mode != "full" and totals["installment_mode"] != mode:
        raise _fail(failure_type, "state_conflict", "The requested installment mode is not the mode offered by the native wizard.", exit_code=5)
    amount = parameters.get("amount", str(totals["full_amount"] if mode == "full" else totals["amount_by_default"]))
    rounded = _rounded_currency_amount(wizard.currency_id, amount)
    full = _rounded_currency_amount(wizard.currency_id, str(totals["full_amount"]))
    if rounded <= 0 or rounded > full:
        raise _fail(failure_type, "state_conflict", "The payment amount is outside the native payable amount.", exit_code=5)
    if mode != "full" and rounded != _rounded_currency_amount(wizard.currency_id, str(totals["amount_by_default"])):
        raise _fail(failure_type, "state_conflict", "A non-full installment payment must use its native offered amount.", exit_code=5)
    values = {"installments_mode": mode}
    if edit_mode:
        values.update(amount=float(rounded), communication=key)
    if "amount" in parameters:
        values["payment_difference_handling"] = "open"
    if "payment_difference_handling" in parameters:
        values["payment_difference_handling"] = parameters["payment_difference_handling"]
    if parameters.get("payment_difference_handling") == "reconcile":
        _ensure_ids(env, "account.account", {parameters["writeoff_account_id"]}, [
            ("company_ids", "in", [company_id]), ("active", "=", True),
        ], company_id, failure_type)
        values["writeoff_account_id"] = parameters["writeoff_account_id"]
        if "writeoff_label" in parameters:
            values["writeoff_label"] = parameters["writeoff_label"]
        if wizard.early_payment_discount_mode or wizard.writeoff_is_exchange_account:
            raise _fail(failure_type, "state_conflict", "The native discount or exchange route cannot honor this explicit write-off.", exit_code=5)
    wizard.write(values)
    if wizard.installments_mode != mode:
        raise _fail(failure_type, "state_conflict", "The native wizard did not retain the requested installment mode.", exit_code=5)
    if edit_mode and _rounded_currency_amount(wizard.currency_id, str(wizard.amount)) != rounded:
        raise _fail(failure_type, "state_conflict", "The native wizard did not retain the requested payment amount.", exit_code=5)
    if parameters.get("payment_difference_handling") == "reconcile" and (
        wizard.early_payment_discount_mode or wizard.writeoff_is_exchange_account
        or _rounded_currency_amount(wizard.currency_id, str(wizard.payment_difference))
        != _rounded_currency_amount(wizard.currency_id, str(totals["full_amount_for_difference" if mode == "full" else "amount_for_difference"])) - rounded
    ):
        raise _fail(failure_type, "state_conflict", "The native wizard cannot retain the requested explicit payment difference.", exit_code=5)
    expected = []
    if edit_mode:
        expected.append((wizard._create_payment_vals_from_wizard(batches[0]), set(batches[0]["lines"].move_id.ids)))
    else:
        lines_to_pay = totals["lines"] if mode != "full" else wizard.line_ids
        for batch in batches:
            for line in batch["lines"]:
                if line.id not in lines_to_pay.ids:
                    continue
                line_batch = {**batch, "lines": batch["lines"].filtered(lambda candidate, line_id=line.id: candidate.id == line_id),
                              "payment_values": {**batch["payment_values"], "payment_type": "inbound" if line.balance > 0 else "outbound"}}
                expected.append((wizard._create_payment_vals_from_batch(line_batch), {line.move_id.id}))
    if not 1 <= len(expected) <= 1000:
        raise _fail(failure_type, "state_conflict", "The native payment set is outside the supported result bound.", exit_code=5)
    payments = wizard._create_payments()
    return verified(payments, "odoo_write_error", expected), False


def _pair_partials(lines: Any) -> Any:
    line_ids = set(lines.ids)
    partials = lines.matched_debit_ids | lines.matched_credit_ids
    return partials.filtered(
        lambda partial: (
            {
                partial.debit_move_id.id,
                partial.credit_move_id.id,
            }
            == line_ids
        )
    )


def _reconciliation_result(
    lines: Any, company_id: int, *, source_id: int | None = None
) -> dict[str, Any]:
    partials = _pair_partials(lines)
    full_ids = _record_ids(lines.full_reconcile_id)
    reconciled = bool(all(bool(line.reconciled) for line in lines))
    result = {
        "model": "account.move.line",
        "id": None,
        "name": None,
        "state": "reconciled" if reconciled else "partial",
        "company_id": company_id,
        "move_type": None,
        "source_id": source_id,
        "line_ids": sorted(lines.ids),
        "partial_reconcile_ids": sorted(partials.ids),
        "full_reconcile_id": full_ids[0] if len(full_ids) == 1 else None,
        "reconciled": reconciled,
    }
    assert set(result) == _RESULT_KEYS
    return result


def _automatic_reconciliation_result(
    requested_lines: Any, company_id: int
) -> dict[str, Any]:
    partials = requested_lines.matched_debit_ids | requested_lines.matched_credit_ids
    fulls = requested_lines.full_reconcile_id | partials.full_reconcile_id
    related = requested_lines
    if partials:
        related |= partials.debit_move_id | partials.credit_move_id
    if fulls:
        related |= fulls.reconciled_line_ids
    full_ids = sorted(fulls.ids)
    result = {
        "model": "account.move.line",
        "id": None,
        "name": None,
        "state": "reconciled",
        "company_id": company_id,
        "move_type": None,
        "source_id": None,
        "line_ids": sorted(related.ids),
        "partial_reconcile_ids": sorted(partials.ids),
        "full_reconcile_id": full_ids[0] if len(full_ids) == 1 else None,
        "reconciled": bool(
            requested_lines and all(bool(line.reconciled) for line in requested_lines)
        ),
    }
    assert set(result) == _RESULT_KEYS
    return result


def _run_automatic_reconciliation(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    from odoo import Command

    expected_ids = set(parameters["line_ids"])
    lines = _scoped(env, "account.move.line", company_id).search(
        [("id", "in", sorted(expected_ids)), ("company_id", "=", company_id)],
        limit=len(expected_ids) + 1,
        order="id",
    )
    if set(lines.ids) != expected_ids:
        raise _fail(
            failure_type,
            "record_not_found",
            "An automatic-reconciliation line was not found in the company.",
            exit_code=4,
        )
    if all(bool(line.reconciled) for line in lines):
        result = _automatic_reconciliation_result(lines, company_id)
        if not result["partial_reconcile_ids"]:
            raise _fail(
                failure_type,
                "state_conflict",
                "The reconciled journal items have no stable reconciliation graph.",
                exit_code=5,
            )
        return result, True
    existing_partials = lines.matched_debit_ids | lines.matched_credit_ids
    if existing_partials or any(bool(line.reconciled) for line in lines):
        raise _fail(
            failure_type,
            "state_conflict",
            "The journal-item selection is already partially reconciled.",
            exit_code=5,
        )
    if any(
        line.parent_state != "posted"
        or not line.account_id.reconcile
        or line.company_id.id != company_id
        for line in lines
    ):
        raise _fail(
            failure_type,
            "state_conflict",
            "The journal items are not eligible for automatic reconciliation.",
            exit_code=5,
        )

    wizard_model = env["account.auto.reconcile.wizard"]
    values = wizard_model._get_default_wizard_values(lines)
    values.update(
        {
            "company_id": company_id,
            "line_ids": [Command.set(sorted(expected_ids))],
        }
    )
    wizard_model.create(values).auto_reconcile()
    lines.invalidate_recordset(
        [
            "amount_residual",
            "reconciled",
            "matched_debit_ids",
            "matched_credit_ids",
            "full_reconcile_id",
        ]
    )
    result = _automatic_reconciliation_result(lines, company_id)
    if not result["reconciled"] or not result["partial_reconcile_ids"]:
        raise _fail(
            failure_type,
            "nothing_to_reconcile",
            "Odoo did not fully reconcile the requested selection.",
            exit_code=6,
        )
    return result, False


def _commercial_partner_id(line: Any) -> int | None:
    partner = getattr(line, "partner_id", None)
    commercial_partner = getattr(partner, "commercial_partner_id", None) or partner
    return _many2one_id(commercial_partner)


def _invoice_reconciliation_record(
    env: Any,
    invoice_id: int,
    company_id: int,
    failure_type: type[Exception],
) -> Any:
    return _search_one(
        env,
        "account.move",
        [
            ("id", "=", invoice_id),
            ("company_id", "=", company_id),
            ("move_type", "in", list(_DOCUMENT_TYPES)),
            ("state", "=", "posted"),
        ],
        company_id,
        failure_type,
    )


def _invoice_term_lines(invoice: Any) -> Any:
    return invoice.line_ids.filtered(
        lambda line: (
            line.account_id.account_type in {"asset_receivable", "liability_payable"}
        )
    )


def _invoice_widget_line_ids(invoice: Any) -> set[int]:
    widget = invoice.invoice_outstanding_credits_debits_widget
    if not isinstance(widget, Mapping):
        return set()
    content = widget.get("content")
    if not isinstance(content, list):
        return set()
    return {
        line["id"]
        for line in content
        if isinstance(line, Mapping) and _is_id(line.get("id"))
    }


def _invoice_candidate_partials(invoice_lines: Any, counterpart: Any) -> Any:
    invoice_line_ids = set(invoice_lines.ids)
    partials = counterpart.matched_debit_ids | counterpart.matched_credit_ids
    return partials.filtered(
        lambda partial: (
            counterpart.id in {partial.debit_move_id.id, partial.credit_move_id.id}
            and bool(
                invoice_line_ids & {partial.debit_move_id.id, partial.credit_move_id.id}
            )
        )
    )


def _partial_pair_lines(env: Any, partial: Any, company_id: int) -> Any:
    return _scoped(env, "account.move.line", company_id).browse(
        sorted({partial.debit_move_id.id, partial.credit_move_id.id})
    )


def _invoice_partial_lines(env: Any, partials: Any, company_id: int) -> Any:
    line_ids = {
        line_id
        for partial in partials
        for line_id in (partial.debit_move_id.id, partial.credit_move_id.id)
    }
    return _scoped(env, "account.move.line", company_id).browse(sorted(line_ids))


def _invoice_reconciliation_result(
    lines: Any, partials: Any, company_id: int, invoice_id: int
) -> dict[str, Any]:
    full_ids = _record_ids(lines.full_reconcile_id | partials.full_reconcile_id)
    reconciled = bool(lines and all(bool(line.reconciled) for line in lines))
    result = {
        "model": "account.move.line",
        "id": None,
        "name": None,
        "state": "reconciled" if reconciled else "partial",
        "company_id": company_id,
        "move_type": None,
        "source_id": invoice_id,
        "line_ids": sorted(lines.ids),
        "partial_reconcile_ids": sorted(partials.ids),
        "full_reconcile_id": full_ids[0] if len(full_ids) == 1 else None,
        "reconciled": reconciled,
    }
    assert set(result) == _RESULT_KEYS
    return result


def _invoice_undo_result(invoice: Any, company_id: int) -> dict[str, Any]:
    invoice_lines = _invoice_term_lines(invoice)
    partials = invoice_lines.matched_debit_ids | invoice_lines.matched_credit_ids
    lines = invoice_lines
    if partials:
        lines |= partials.debit_move_id | partials.credit_move_id
    full_ids = _record_ids(lines.full_reconcile_id | partials.full_reconcile_id)
    reconciled = bool(
        invoice_lines and all(bool(line.reconciled) for line in invoice_lines)
    )
    result = {
        "model": "account.move.line",
        "id": None,
        "name": None,
        "state": (
            "reconciled" if reconciled else "partial" if partials else "unreconciled"
        ),
        "company_id": company_id,
        "move_type": None,
        "source_id": invoice.id,
        "line_ids": sorted(lines.ids),
        "partial_reconcile_ids": sorted(partials.ids),
        "full_reconcile_id": full_ids[0] if len(full_ids) == 1 else None,
        "reconciled": reconciled,
    }
    assert set(result) == _RESULT_KEYS
    return result


def _apply_invoice_reconciliation(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    invoice = _invoice_reconciliation_record(
        env, parameters["invoice_id"], company_id, failure_type
    )
    counterpart = _search_one(
        env,
        "account.move.line",
        [
            ("id", "=", parameters["outstanding_line_id"]),
            ("company_id", "=", company_id),
        ],
        company_id,
        failure_type,
    )
    invoice_lines = _invoice_term_lines(invoice)
    existing = _invoice_candidate_partials(invoice_lines, counterpart)
    if existing:
        lines = _invoice_partial_lines(env, existing, company_id)
        if (
            counterpart.id not in lines.ids
            or not set(lines.ids) <= (set(invoice_lines.ids) | {counterpart.id})
            or any(
                line.account_id.id != counterpart.account_id.id
                or _commercial_partner_id(line) != _commercial_partner_id(counterpart)
                for line in lines
            )
        ):
            raise _fail(
                failure_type,
                "state_conflict",
                "The invoice reconciliation graph is inconsistent.",
                exit_code=5,
            )
        return _invoice_reconciliation_result(
            lines, existing, company_id, invoice.id
        ), True

    candidate_residual = Decimal(str(counterpart.amount_residual))
    commercial_partner_id = _commercial_partner_id(counterpart)
    eligible_invoice_lines = invoice_lines.filtered(
        lambda line: (
            line.company_id.id == company_id
            and line.account_id.id == counterpart.account_id.id
            and _commercial_partner_id(line) == commercial_partner_id
            and Decimal(str(line.amount_residual)) != 0
            and (Decimal(str(line.amount_residual)) > 0) != (candidate_residual > 0)
        )
    )
    if (
        not eligible_invoice_lines
        or counterpart.id not in _invoice_widget_line_ids(invoice)
        or counterpart.parent_state != "posted"
        or counterpart.company_id.id != company_id
        or not counterpart.account_id.reconcile
        or commercial_partner_id is None
        or candidate_residual == 0
    ):
        raise _fail(
            failure_type,
            "state_conflict",
            "The outstanding line is not eligible for this invoice.",
            exit_code=5,
        )

    invoice.js_assign_outstanding_line(counterpart.id)
    invoice_lines.invalidate_recordset(
        [
            "amount_residual",
            "reconciled",
            "matched_debit_ids",
            "matched_credit_ids",
            "full_reconcile_id",
        ]
    )
    counterpart.invalidate_recordset(
        [
            "amount_residual",
            "reconciled",
            "matched_debit_ids",
            "matched_credit_ids",
            "full_reconcile_id",
        ]
    )
    partials = _invoice_candidate_partials(invoice_lines, counterpart)
    if not partials:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not create an invoice reconciliation link.",
            exit_code=6,
        )
    lines = _invoice_partial_lines(env, partials, company_id)
    if counterpart.id not in lines.ids or not set(lines.ids) <= (
        set(invoice_lines.ids) | {counterpart.id}
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo returned an invalid invoice reconciliation pair.",
            exit_code=6,
        )
    return _invoice_reconciliation_result(
        lines, partials, company_id, invoice.id
    ), False


def _undo_invoice_reconciliation(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    invoice = _invoice_reconciliation_record(
        env, parameters["invoice_id"], company_id, failure_type
    )
    expected_ids = {
        parameters["invoice_line_id"],
        parameters["counterpart_line_id"],
    }
    lines = _scoped(env, "account.move.line", company_id).search(
        [("id", "in", sorted(expected_ids)), ("company_id", "=", company_id)],
        limit=3,
        order="id",
    )
    if set(lines.ids) != expected_ids or parameters["invoice_line_id"] not in set(
        invoice.line_ids.ids
    ):
        raise _fail(
            failure_type,
            "record_not_found",
            "An invoice reconciliation line was not found in the company.",
            exit_code=4,
        )
    invoice_line = lines.filtered(lambda line: line.id == parameters["invoice_line_id"])
    counterpart = lines.filtered(
        lambda line: line.id == parameters["counterpart_line_id"]
    )
    if (
        invoice_line.account_id.id != counterpart.account_id.id
        or _commercial_partner_id(invoice_line) != _commercial_partner_id(counterpart)
    ):
        raise _fail(
            failure_type,
            "state_conflict",
            "The lines do not belong to one invoice reconciliation pair.",
            exit_code=5,
        )
    partials = _scoped(env, "account.partial.reconcile", company_id).search(
        [
            ("id", "=", parameters["partial_reconcile_id"]),
            ("company_id", "=", company_id),
        ],
        limit=2,
    )
    if not partials:
        result = _invoice_undo_result(invoice, company_id)
        if parameters["partial_reconcile_id"] in result["partial_reconcile_ids"]:
            raise _fail(
                failure_type,
                "state_conflict",
                "The invoice still contains the requested reconciliation.",
                exit_code=5,
            )
        return result, True
    if (
        len(partials) != 1
        or {
            partials.debit_move_id.id,
            partials.credit_move_id.id,
        }
        != expected_ids
    ):
        raise _fail(
            failure_type,
            "state_conflict",
            "The partial reconciliation does not connect the requested pair.",
            exit_code=5,
        )
    invoice.js_remove_outstanding_partial(partials.id)
    (_invoice_term_lines(invoice) | lines).invalidate_recordset(
        [
            "amount_residual",
            "reconciled",
            "matched_debit_ids",
            "matched_credit_ids",
            "full_reconcile_id",
        ]
    )
    requested_partial = _scoped(env, "account.partial.reconcile", company_id).search(
        [
            ("id", "=", parameters["partial_reconcile_id"]),
            ("company_id", "=", company_id),
        ],
        limit=1,
    )
    if requested_partial:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not remove the requested invoice reconciliation.",
            exit_code=6,
        )
    result = _invoice_undo_result(invoice, company_id)
    if parameters["partial_reconcile_id"] in result["partial_reconcile_ids"]:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo retained the removed invoice reconciliation in the result graph.",
            exit_code=6,
        )
    return result, False


def _apply_reconciliation(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    if "invoice_id" in parameters:
        return _apply_invoice_reconciliation(env, parameters, company_id, failure_type)
    expected_ids = set(parameters["line_ids"])
    lines = _scoped(env, "account.move.line", company_id).search(
        [
            ("id", "in", sorted(expected_ids)),
            ("company_id", "=", company_id),
        ],
        limit=3,
        order="id",
    )
    if set(lines.ids) != expected_ids:
        raise _fail(
            failure_type,
            "record_not_found",
            "A reconciliation line was not found in the company.",
            exit_code=4,
        )
    existing = _pair_partials(lines)
    if existing:
        return _reconciliation_result(lines, company_id), True
    if (
        len(lines.account_id) != 1
        or not lines.account_id.reconcile
        or any(line.parent_state != "posted" for line in lines)
    ):
        raise _fail(
            failure_type,
            "state_conflict",
            "The journal items are not eligible for reconciliation.",
            exit_code=5,
        )
    residuals = [Decimal(str(line.amount_residual)) for line in lines]
    if not (
        any(value > 0 for value in residuals) and any(value < 0 for value in residuals)
    ):
        raise _fail(
            failure_type,
            "state_conflict",
            "The journal items need opposite non-zero residuals.",
            exit_code=5,
        )
    lines.reconcile()
    lines.invalidate_recordset(
        [
            "amount_residual",
            "reconciled",
            "matched_debit_ids",
            "matched_credit_ids",
            "full_reconcile_id",
        ]
    )
    result = _reconciliation_result(lines, company_id)
    if not result["partial_reconcile_ids"]:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not create a reconciliation record.",
            exit_code=6,
        )
    return result, False


def _undo_match_group(
    env: Any, parameters: dict[str, Any], company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    with env.cr.savepoint():
        requested = _ensure_ids(env, "account.move.line", set(parameters["line_ids"]), [
            ("company_id", "=", company_id),
        ], company_id, failure_type)
        # Native matching-number discovery internally uses sudo; never mutate
        # that unchecked graph. Search it again as the configured caller.
        discovered = requested._all_reconciled_lines()
        lines = _ensure_ids(env, "account.move.line", set(discovered.ids), [
            ("company_id", "=", company_id),
        ], company_id, failure_type)
        if not set(requested.ids) <= set(lines.ids):
            raise _fail(failure_type, "state_conflict", "The native matching group does not contain its requested lines.", exit_code=5)
        lines.check_access("write")
        moves = _ensure_ids(env, "account.move", set(lines.move_id.ids), [
            ("company_id", "=", company_id),
        ], company_id, failure_type)
        moves.check_access("write")
        partials = lines.matched_debit_ids | lines.matched_credit_ids
        partials = _ensure_ids(env, "account.partial.reconcile", set(partials.ids), [
            ("company_id", "=", company_id),
        ], company_id, failure_type)
        fulls = _ensure_ids(env, "account.full.reconcile", set((lines.full_reconcile_id | partials.full_reconcile_id).ids), [], company_id, failure_type)
        if (not set((partials.debit_move_id | partials.credit_move_id).ids) <= set(lines.ids)
            or not set(fulls.reconciled_line_ids.ids) <= set(lines.ids)
            or not set(fulls.partial_reconcile_ids.ids) <= set(partials.ids)):
            raise _fail(failure_type, "state_conflict", "The native matching group has an incomplete reconciliation graph.", exit_code=5)
        partials.check_access("unlink")
        fulls.check_access("unlink")
        replay = not partials and not fulls
        if not replay:
            related = _scoped(env, "account.move", company_id).search([
                ("tax_cash_basis_rec_id", "in", partials.ids),
            ]) | partials.exchange_move_id
            related = _ensure_ids(env, "account.move", set(related.ids), [
                ("company_id", "=", company_id),
            ], company_id, failure_type)
            related.check_access("write")
            related.filtered(lambda move: move.state == "draft").check_access("unlink")
            related_lines = _ensure_ids(env, "account.move.line", set(related.line_ids.ids), [
                ("company_id", "=", company_id),
            ], company_id, failure_type)
            related_lines.check_access("write")
            payments = partials._get_to_update_payments(from_state="paid")
            payments = _ensure_ids(env, "account.payment", set(payments.ids), [
                ("company_id", "=", company_id),
            ], company_id, failure_type)
            payments.check_access("write")
            lines.remove_move_reconcile()
            lines.invalidate_recordset()
        if lines.matched_debit_ids or lines.matched_credit_ids or lines.full_reconcile_id:
            raise _fail(failure_type, "odoo_write_error", "Native matching-group undo left reconciliation links.", exit_code=6)
        result = _unreconciled_result(lines, company_id)
        result["reconciled"] = bool(lines and all(bool(line.reconciled) for line in lines))
        return result, replay


def _undo_reconciliation(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    if parameters.get("mode") == "match_group":
        return _undo_match_group(env, parameters, company_id, failure_type)
    if "invoice_id" in parameters:
        return _undo_invoice_reconciliation(env, parameters, company_id, failure_type)
    expected_ids = set(parameters["line_ids"])
    lines = _scoped(env, "account.move.line", company_id).search(
        [
            ("id", "in", sorted(expected_ids)),
            ("company_id", "=", company_id),
        ],
        limit=3,
        order="id",
    )
    if set(lines.ids) != expected_ids:
        raise _fail(
            failure_type,
            "record_not_found",
            "A reconciliation line was not found in the company.",
            exit_code=4,
        )

    all_partials = lines.matched_debit_ids | lines.matched_credit_ids
    pair_partials = _pair_partials(lines)
    fulls = lines.full_reconcile_id | all_partials.full_reconcile_id
    if not all_partials:
        if fulls or any(bool(line.reconciled) for line in lines):
            raise _fail(
                failure_type,
                "state_conflict",
                "The journal items have an inconsistent reconciliation graph.",
                exit_code=5,
            )
        return _unreconciled_result(lines, company_id), True
    if len(all_partials) != 1 or len(pair_partials) != 1:
        raise _fail(
            failure_type,
            "state_conflict",
            "Only one isolated reconciliation pair can be undone.",
            exit_code=5,
        )
    if fulls and (
        len(fulls) != 1 or set(fulls.reconciled_line_ids.ids) != expected_ids
    ):
        raise _fail(
            failure_type,
            "state_conflict",
            "The full reconciliation contains other journal items.",
            exit_code=5,
        )

    pair_partials.unlink()
    lines.invalidate_recordset(
        [
            "amount_residual",
            "reconciled",
            "matched_debit_ids",
            "matched_credit_ids",
            "full_reconcile_id",
        ]
    )
    remaining = lines.matched_debit_ids | lines.matched_credit_ids
    if (
        remaining
        or lines.full_reconcile_id
        or any(bool(line.reconciled) for line in lines)
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not remove the isolated reconciliation.",
            exit_code=6,
        )
    return _unreconciled_result(lines, company_id), False


def _cancel_payment(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    if "payment_ids" in parameters:
        payments = _batch_payments(
            env, parameters["payment_ids"], company_id, failure_type
        )
        if any(
            payment.state not in {"draft", "in_process", "paid", "canceled"}
            for payment in payments
        ):
            raise _fail(
                failure_type,
                "state_conflict",
                "A payment cannot be canceled from its current state.",
                exit_code=5,
            )
        pending = payments.filtered(lambda payment: payment.state != "canceled")
        replay = not pending
        if pending:
            for payment in pending:
                payment.action_cancel()
        if any(payment.state != "canceled" for payment in payments):
            raise _fail(
                failure_type,
                "odoo_write_error",
                "Odoo did not cancel every requested payment.",
                exit_code=6,
            )
        return _payment_batch_result(payments, company_id), replay

    payment = _search_one(
        env,
        "account.payment",
        [
            ("id", "=", parameters["payment_id"]),
            ("company_id", "=", company_id),
        ],
        company_id,
        failure_type,
    )
    if payment.state == "canceled":
        return _payment_result(payment, company_id, source_id=None), True
    if payment.state not in {"draft", "in_process", "paid"}:
        raise _fail(
            failure_type,
            "state_conflict",
            "The payment cannot be canceled from its current state.",
            exit_code=5,
        )
    payment.action_cancel()
    if payment.state != "canceled":
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not cancel the payment.",
            exit_code=6,
        )
    return _payment_result(payment, company_id, source_id=None), False


def _post_payment(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    if "payment_ids" in parameters:
        payments = _batch_payments(
            env, parameters["payment_ids"], company_id, failure_type
        )
        if any(
            payment.state not in {"draft", "in_process", "paid"}
            for payment in payments
        ):
            raise _fail(
                failure_type,
                "state_conflict",
                "Only draft payments can be posted.",
                exit_code=5,
            )
        pending = payments.filtered(
            lambda payment: payment.state not in {"in_process", "paid"}
        )
        replay = not pending
        if pending:
            for payment in pending:
                payment.action_post()
        if any(
            payment.state not in {"in_process", "paid"} for payment in payments
        ):
            raise _fail(
                failure_type,
                "odoo_write_error",
                "Odoo did not post every requested payment.",
                exit_code=6,
            )
        return _payment_batch_result(payments, company_id), replay

    payment = _search_one(
        env,
        "account.payment",
        [
            ("id", "=", parameters["payment_id"]),
            ("company_id", "=", company_id),
        ],
        company_id,
        failure_type,
    )
    if payment.state in {"in_process", "paid"}:
        return _payment_result(payment, company_id, source_id=None), True
    if payment.state != "draft":
        raise _fail(
            failure_type,
            "state_conflict",
            "Only a draft payment can be posted.",
            exit_code=5,
        )
    payment.action_post()
    if payment.state not in {"in_process", "paid"}:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not post the payment.",
            exit_code=6,
        )
    return _payment_result(payment, company_id, source_id=None), False


def _payment_actual_values(payment: Any) -> dict[str, Any]:
    return {
        "payment_type": payment.payment_type,
        "partner_type": payment.partner_type,
        "partner_id": payment.partner_id.id,
        "amount": _canonical_decimal_text(payment.amount),
        "currency_id": payment.currency_id.id,
        "journal_id": payment.journal_id.id,
        "payment_method_line_id": payment.payment_method_line_id.id,
        "date": str(payment.date),
        "payment_reference": payment.payment_reference or None,
    }


def _payment_target_values(values: dict[str, Any]) -> dict[str, Any]:
    result = dict(values)
    if "amount" in result:
        result["amount"] = _canonical_decimal_text(result["amount"])
    if "payment_reference" in result:
        result["payment_reference"] = result["payment_reference"] or None
    return result


def _validate_payment_configuration(
    env: Any,
    values: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> None:
    _ensure_ids(
        env,
        "res.partner",
        {values["partner_id"]},
        [("company_id", "in", [False, company_id])],
        company_id,
        failure_type,
    )
    _ensure_ids(
        env,
        "res.currency",
        {values["currency_id"]},
        [("active", "=", True)],
        company_id,
        failure_type,
    )
    _ensure_ids(
        env,
        "account.journal",
        {values["journal_id"]},
        [
            ("company_id", "=", company_id),
            ("type", "in", ["bank", "cash", "credit"]),
            ("active", "=", True),
        ],
        company_id,
        failure_type,
    )
    method_line = _search_one(
        env,
        "account.payment.method.line",
        [
            ("id", "=", values["payment_method_line_id"]),
            ("journal_id", "=", values["journal_id"]),
            ("payment_method_id.payment_type", "=", values["payment_type"]),
        ],
        company_id,
        failure_type,
    )
    outstanding = method_line.payment_account_id
    if not outstanding and env["account.move"]._get_invoice_in_payment_state() == "in_payment":
        return
    if (
        not outstanding
        or company_id not in outstanding.company_ids.ids
        or not outstanding.reconcile
    ):
        raise _fail(
            failure_type,
            "configuration_missing",
            "The payment method has no valid company outstanding account.",
            exit_code=4,
        )


def _payment_write_values(values: dict[str, Any]) -> dict[str, Any]:
    result = dict(values)
    if "amount" in result:
        result["amount"] = Decimal(result["amount"])
    if "payment_reference" in result and result["payment_reference"] is None:
        result["payment_reference"] = False
    return result


def _create_payment(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    key: str,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    expected = _payment_target_values(parameters)
    existing = _scoped(env, "account.payment", company_id).search(
        [("company_id", "=", company_id), ("memo", "=", key)],
        limit=2,
        order="id",
    )
    if existing:
        if len(existing) != 1 or _payment_actual_values(existing) != expected:
            raise _fail(
                failure_type,
                "idempotency_conflict",
                "The idempotency key was already used by another payment.",
                exit_code=5,
            )
        if existing.state != "draft":
            raise _fail(
                failure_type,
                "state_conflict",
                "The idempotent payment is no longer in draft.",
                exit_code=5,
            )
        _validate_payment_configuration(
            env, _payment_actual_values(existing), company_id, failure_type
        )
        return _payment_result(existing, company_id, source_id=None), True

    _validate_payment_configuration(env, expected, company_id, failure_type)
    payment = _scoped(env, "account.payment", company_id).create(
        {
            **_payment_write_values(parameters),
            "company_id": company_id,
            "memo": key,
        }
    )
    if (
        payment.company_id.id != company_id
        or payment.memo != key
        or payment.state != "draft"
        or _payment_actual_values(payment) != expected
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo returned an invalid draft payment.",
            exit_code=6,
        )
    _validate_payment_configuration(
        env, _payment_actual_values(payment), company_id, failure_type
    )
    return _payment_result(payment, company_id, source_id=None), False


def _update_draft_payment(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    payment = _search_one(
        env,
        "account.payment",
        [
            ("id", "=", parameters["payment_id"]),
            ("company_id", "=", company_id),
        ],
        company_id,
        failure_type,
    )
    actual = _payment_actual_values(payment)
    target = {**actual, **_payment_target_values(parameters["changes"])}
    if actual == target:
        _validate_payment_configuration(env, target, company_id, failure_type)
        return _payment_result(payment, company_id, source_id=None), True
    if payment.state != "draft":
        raise _fail(
            failure_type,
            "state_conflict",
            "Only a draft payment can be updated.",
            exit_code=5,
        )
    _validate_payment_configuration(env, target, company_id, failure_type)
    payment.write(_payment_write_values(parameters["changes"]))
    if payment.state != "draft" or _payment_actual_values(payment) != target:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not apply the requested draft-payment update.",
            exit_code=6,
        )
    _validate_payment_configuration(
        env, _payment_actual_values(payment), company_id, failure_type
    )
    return _payment_result(payment, company_id, source_id=None), False


def _reset_payment_to_draft(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    if "payment_ids" in parameters:
        payments = _batch_payments(
            env, parameters["payment_ids"], company_id, failure_type
        )
        if any(
            payment.state not in {"draft", "in_process", "paid", "canceled", "rejected"}
            for payment in payments
        ):
            raise _fail(
                failure_type,
                "state_conflict",
                "A payment cannot be reset to draft from its current state.",
                exit_code=5,
            )
        pending = payments.filtered(lambda payment: payment.state != "draft")
        replay = not pending
        if pending:
            for payment in pending:
                payment.action_draft()
        if any(
            payment.state != "draft"
            or (payment.move_id and payment.move_id.state != "draft")
            for payment in payments
        ):
            raise _fail(
                failure_type,
                "odoo_write_error",
                "Odoo did not reset every requested payment to draft.",
                exit_code=6,
            )
        return _payment_batch_result(payments, company_id), replay

    payment = _search_one(
        env,
        "account.payment",
        [
            ("id", "=", parameters["payment_id"]),
            ("company_id", "=", company_id),
        ],
        company_id,
        failure_type,
    )
    if payment.state == "draft":
        return _payment_result(payment, company_id, source_id=None), True
    if payment.state not in {"in_process", "paid", "canceled", "rejected"}:
        raise _fail(
            failure_type,
            "state_conflict",
            "The payment cannot be reset to draft from its current state.",
            exit_code=5,
        )
    payment.action_draft()
    if payment.state != "draft" or (
        payment.move_id and payment.move_id.state != "draft"
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not reset the payment to draft.",
            exit_code=6,
        )
    return _payment_result(payment, company_id, source_id=None), False


def _statement_reference(value: Any) -> str | None:
    return value or None


def _statement_currency(statement_or_journal: Any) -> Any:
    currency = statement_or_journal.currency_id
    if currency:
        return currency
    return statement_or_journal.company_id.currency_id


def _rounded_statement_balance(statement_or_journal: Any, value: str) -> Decimal:
    return _rounded_currency_amount(_statement_currency(statement_or_journal), value)


def _statement_matches(
    statement: Any,
    transaction_ids: list[int],
    reference: str | None,
    balance_end_real: Decimal,
    company_id: int,
    *,
    balance_start: Decimal | None = None,
    name: str | None = None,
    statement_date: str | None = None,
) -> bool:
    return bool(
        statement.company_id.id == company_id
        and _record_ids(statement.line_ids) == transaction_ids
        and _statement_reference(statement.reference) == reference
        and Decimal(str(statement.balance_end_real)) == balance_end_real
        and (balance_start is None or Decimal(str(statement.balance_start)) == balance_start)
        and (name is None or statement.name == name)
        and (statement_date is None or str(statement.date) == statement_date)
    )


def _bank_statement_transactions_are_contiguous(
    env: Any,
    transactions: Any,
    journal_id: int,
    company_id: int,
) -> bool:
    indexes = [transaction.internal_index for transaction in transactions]
    if not indexes or any(not index for index in indexes):
        return False
    lines_between = _scoped(env, "account.bank.statement.line", company_id).search(
        [
            ("company_id", "=", company_id),
            ("journal_id", "=", journal_id),
            ("internal_index", ">=", min(indexes)),
            ("internal_index", "<=", max(indexes)),
            ("state", "!=", "cancel"),
        ],
        limit=len(transactions) + 1,
    )
    return set(lines_between.ids) == set(transactions.ids)


def _create_bank_statement(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    from odoo import Command

    transaction_ids = parameters["transaction_ids"]
    statement_model = _scoped(env, "account.bank.statement", company_id)
    overlapping = statement_model.search(
        [("company_id", "=", company_id), ("line_ids", "in", transaction_ids)],
        limit=2,
        order="id",
    )
    if overlapping:
        if len(overlapping) != 1:
            raise _fail(
                failure_type,
                "idempotency_conflict",
                "The requested bank transactions belong to conflicting statements.",
                exit_code=5,
            )
        expected_balance = _rounded_statement_balance(
            overlapping, parameters["balance_end_real"]
        )
        if not _statement_matches(
            overlapping,
            transaction_ids,
            _statement_reference(parameters["reference"]),
            expected_balance,
            company_id,
            balance_start=_rounded_statement_balance(overlapping, parameters["balance_start"])
            if "balance_start" in parameters else None,
            name=parameters.get("name"),
            statement_date=parameters.get("date"),
        ):
            raise _fail(
                failure_type,
                "idempotency_conflict",
                "The bank-statement transaction set was already used differently.",
                exit_code=5,
            )
        return _bank_statement_result(overlapping, company_id), True

    transactions = _ensure_ids(
        env,
        "account.bank.statement.line",
        set(transaction_ids),
        [("company_id", "=", company_id)],
        company_id,
        failure_type,
    ).sorted(lambda transaction: transaction.id)
    journals = {transaction.journal_id.id for transaction in transactions}
    if len(journals) != 1:
        raise _fail(
            failure_type,
            "state_conflict",
            "All bank transactions must belong to one journal.",
            exit_code=5,
        )
    journal = transactions[0].journal_id
    if (
        journal.company_id.id != company_id
        or journal.type not in {"bank", "cash"}
        or not _bank_statement_transactions_are_contiguous(
            env, transactions, journal.id, company_id
        )
        or any(
            transaction.statement_id
            or transaction.company_id.id != company_id
            or transaction.journal_id.id != journal.id
            or not transaction.move_id
            or transaction.move_id.company_id.id != company_id
            or transaction.move_id.move_type != "entry"
            or transaction.move_id.state != "posted"
            for transaction in transactions
        )
    ):
        raise _fail(
            failure_type,
            "state_conflict",
            "Only contiguous, ungrouped, posted transactions from one company bank or cash journal can form a statement.",
            exit_code=5,
        )
    rounded_balance = _rounded_statement_balance(
        journal, parameters["balance_end_real"]
    )
    statement = statement_model.with_context(
        skip_pdf_attachment_generation=True
    ).create(
        {
            "line_ids": [Command.set(transaction_ids)],
            "reference": parameters["reference"] or False,
            "balance_end_real": rounded_balance,
            **({"balance_start": _rounded_statement_balance(journal, parameters["balance_start"])}
               if "balance_start" in parameters else {}),
            **{field: parameters[field] for field in ("name", "date") if field in parameters},
        }
    )
    statement.invalidate_recordset(
        [
            "company_id",
            "journal_id",
            "currency_id",
            "reference",
            "balance_end_real",
            "balance_start",
            "is_complete",
            "line_ids",
            "name",
            "date",
        ]
    )
    if (
        statement.journal_id.id != journal.id
        or not _statement_matches(
            statement,
            transaction_ids,
            _statement_reference(parameters["reference"]),
            rounded_balance,
            company_id,
            balance_start=_rounded_statement_balance(journal, parameters["balance_start"])
            if "balance_start" in parameters else None,
            name=parameters.get("name"),
            statement_date=parameters.get("date"),
        )
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo returned an invalid bank statement.",
            exit_code=6,
        )
    return _bank_statement_result(statement, company_id), False


def _update_bank_statement(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    statement = _search_one(
        env,
        "account.bank.statement",
        [("id", "=", parameters["statement_id"]), ("company_id", "=", company_id)],
        company_id,
        failure_type,
    )
    changes = parameters["changes"]
    actual = {
        "reference": _statement_reference(statement.reference),
        "balance_end_real": _canonical_decimal_text(statement.balance_end_real),
    }
    native_ending_balance = "balance_start" in changes and "balance_end_real" not in changes
    if native_ending_balance:
        actual.pop("balance_end_real")
    if "balance_start" in changes:
        actual["balance_start"] = _canonical_decimal_text(statement.balance_start)
    for field in ("name", "date"):
        if field in changes:
            actual[field] = str(getattr(statement, field)) if field == "date" else statement.name
    membership = "transaction_ids" in changes
    if membership:
        journal_id = statement.journal_id.id
        _ensure_ids(env, "account.journal", {journal_id}, [
            ("company_id", "=", company_id), ("type", "in", ["bank", "cash"]),
        ], company_id, failure_type)
        existing_ids = set(statement.line_ids.ids)
        target_ids = set(changes["transaction_ids"])
        transactions = _ensure_ids(env, "account.bank.statement.line", existing_ids | target_ids, [
            ("company_id", "=", company_id), ("journal_id", "=", journal_id),
        ], company_id, failure_type)
        transactions.check_access("write")
        if any(not transaction.move_id or transaction.statement_id.id not in (False, statement.id)
               for transaction in transactions):
            raise _fail(failure_type, "state_conflict", "Statement membership cannot steal another statement's transactions.", exit_code=5)
        move_ids = {transaction.move_id.id for transaction in transactions}
        moves = _ensure_ids(env, "account.move", move_ids, [
            ("company_id", "=", company_id), ("journal_id", "=", journal_id),
        ], company_id, failure_type)
        if any(move.move_type != "entry" or move.state != "posted" for move in moves):
            raise _fail(failure_type, "state_conflict", "Statement members require posted bank journal entries.", exit_code=5)
        target_transactions = transactions.filtered(lambda transaction: transaction.id in target_ids)
        if not _bank_statement_transactions_are_contiguous(env, target_transactions, journal_id, company_id):
            raise _fail(failure_type, "state_conflict", "Statement membership requires contiguous transactions from its original journal.", exit_code=5)
        original_moves = {transaction.id: transaction.move_id.id for transaction in transactions}
        actual["transaction_ids"] = sorted(existing_ids)
    target = dict(actual)
    if "reference" in changes:
        target["reference"] = _statement_reference(changes["reference"])
    if "balance_end_real" in changes:
        target["balance_end_real"] = _canonical_decimal_text(
            _rounded_statement_balance(statement, changes["balance_end_real"])
        )
    if "balance_start" in changes:
        target["balance_start"] = _canonical_decimal_text(
            _rounded_statement_balance(statement, changes["balance_start"])
        )
    target.update({field: changes[field] for field in ("name", "date") if field in changes})
    if membership:
        target["transaction_ids"] = changes["transaction_ids"]
    if actual == target:
        return _bank_statement_result(statement, company_id), True
    write_values: dict[str, Any] = {}
    if "reference" in changes:
        write_values["reference"] = changes["reference"] or False
    if "balance_end_real" in changes:
        write_values["balance_end_real"] = Decimal(target["balance_end_real"])
    if "balance_start" in changes:
        write_values["balance_start"] = Decimal(target["balance_start"])
    write_values.update({field: changes[field] for field in ("name", "date") if field in changes})
    if membership:
        from odoo import Command

        write_values["line_ids"] = [Command.set(changes["transaction_ids"])]
    statement.write(write_values)
    statement.invalidate_recordset(
        ["reference", "balance_start", "balance_end", "balance_end_real", "is_complete", "line_ids", "journal_id", "company_id", "name", "date"]
    )
    reread = {
        "reference": _statement_reference(statement.reference),
        "balance_end_real": _canonical_decimal_text(statement.balance_end_real),
    }
    if native_ending_balance:
        reread.pop("balance_end_real")
        if Decimal(str(statement.balance_end_real)) != Decimal(str(statement.balance_end)):
            raise _fail(failure_type, "odoo_write_error", "Native starting-balance update did not recompute the ending balance.", exit_code=6)
    if "balance_start" in changes:
        reread["balance_start"] = _canonical_decimal_text(statement.balance_start)
    for field in ("name", "date"):
        if field in changes:
            reread[field] = str(getattr(statement, field)) if field == "date" else statement.name
    if membership:
        transactions.invalidate_recordset()
        retained = _ensure_ids(env, "account.bank.statement.line", existing_ids | target_ids, [
            ("company_id", "=", company_id), ("journal_id", "=", journal_id),
        ], company_id, failure_type)
        if (statement.company_id.id != company_id or statement.journal_id.id != journal_id
            or any(transaction.move_id.id != original_moves[transaction.id]
                   or transaction.statement_id.id != (statement.id if transaction.id in target_ids else False)
                   for transaction in retained)):
            raise _fail(failure_type, "odoo_write_error", "Native membership update did not preserve and detach the selected bank transactions.", exit_code=6)
        _ensure_ids(env, "account.move", move_ids, [
            ("company_id", "=", company_id), ("journal_id", "=", journal_id),
            ("move_type", "=", "entry"), ("state", "=", "posted"),
        ], company_id, failure_type)
        reread["transaction_ids"] = _record_ids(statement.line_ids)
    if reread != target:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not apply the requested bank-statement update.",
            exit_code=6,
        )
    return _bank_statement_result(statement, company_id), False


def _delete_bank_statement(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    statement = _search_one(
        env,
        "account.bank.statement",
        [("id", "=", parameters["statement_id"]), ("company_id", "=", company_id)],
        company_id,
        failure_type,
    )
    statement_id = statement.id
    transaction_ids = _record_ids(statement.line_ids)
    result = _deleted_result(_bank_statement_result(statement, company_id))
    statement.unlink()
    if _scoped(env, "account.bank.statement", company_id).search_count(
        [("id", "=", statement_id)], limit=1
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not delete the bank statement.",
            exit_code=6,
        )
    transactions = _scoped(env, "account.bank.statement.line", company_id).search(
        [("id", "in", transaction_ids), ("company_id", "=", company_id)],
        limit=len(transaction_ids) + 1,
    )
    if set(transactions.ids) != set(transaction_ids) or any(
        transaction.statement_id for transaction in transactions
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not preserve the ungrouped bank transactions.",
            exit_code=6,
        )
    return result, False


def _duplicate_payment(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    key: str,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    source = _search_one(
        env,
        "account.payment",
        [("id", "=", parameters["payment_id"]), ("company_id", "=", company_id)],
        company_id,
        failure_type,
    )
    expected = _payment_actual_values(source)
    source_memo = source.memo or ""
    memo_marker = f"[ODACV4DUP:{key}]"
    target_memo = f"{source_memo} {memo_marker}" if source_memo else memo_marker
    existing = _scoped(env, "account.payment", company_id).search(
        [
            ("company_id", "=", company_id),
            ("memo", "=like", f"%{memo_marker}"),
            ("id", "!=", source.id),
        ],
        limit=2,
        order="id",
    )
    if existing:
        if (
            len(existing) != 1
            or existing.state != "draft"
            or existing.memo != target_memo
            or _payment_actual_values(existing) != expected
        ):
            raise _fail(
                failure_type,
                "idempotency_conflict",
                "The duplicate-payment key was already used differently.",
                exit_code=5,
            )
        return _payment_result(existing, company_id, source_id=source.id), True
    duplicate = source.copy(
        default={
            "memo": target_memo,
            "payment_reference": source.payment_reference or False,
        }
    )
    if (
        duplicate.id == source.id
        or duplicate.company_id.id != company_id
        or duplicate.state != "draft"
        or duplicate.memo != target_memo
        or _payment_actual_values(duplicate) != expected
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo returned an invalid draft payment copy.",
            exit_code=6,
        )
    return _payment_result(duplicate, company_id, source_id=source.id), False


def _external_reconcile_ids(move: Any) -> tuple[set[int], set[int]]:
    own_ids = set(move.line_ids.ids)
    partial_ids: set[int] = set()
    full_ids: set[int] = set()
    partials = move.line_ids.matched_debit_ids | move.line_ids.matched_credit_ids
    for partial in partials:
        if (
            partial.debit_move_id.id not in own_ids
            or partial.credit_move_id.id not in own_ids
        ):
            partial_ids.add(partial.id)
            if partial.full_reconcile_id:
                full_ids.add(partial.full_reconcile_id.id)
    for line in move.line_ids:
        if line.full_reconcile_id:
            full_ids.add(line.full_reconcile_id.id)
    return partial_ids, full_ids


def _delete_payment(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    payment = _search_one(
        env,
        "account.payment",
        [("id", "=", parameters["payment_id"]), ("company_id", "=", company_id)],
        company_id,
        failure_type,
    )
    move = payment.move_id
    if move and move.company_id.id != company_id:
        raise _fail(
            failure_type,
            "state_conflict",
            "The payment journal entry belongs to another company.",
            exit_code=5,
        )
    external_partials, external_fulls = (
        _external_reconcile_ids(move) if move else (set(), set())
    )
    if (
        payment.state not in {"draft", "canceled"}
        or payment.is_reconciled
        or external_partials
        or external_fulls
    ):
        raise _fail(
            failure_type,
            "state_conflict",
            "Only an unreconciled draft or canceled payment can be deleted.",
            exit_code=5,
    )
    payment_id = payment.id
    move_id = move.id if move else None
    result = _deleted_result(_payment_result(payment, company_id, source_id=None))
    payment.unlink()
    if _scoped(env, "account.payment", company_id).search_count(
        [("id", "=", payment_id)], limit=1
    ) or (
        move_id is not None
        and _scoped(env, "account.move", company_id).search_count(
            [("id", "=", move_id)], limit=1
        )
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not delete the payment and its journal entry.",
            exit_code=6,
        )
    return result, False


def _bank_transaction(
    env: Any,
    transaction_id: int,
    company_id: int,
    failure_type: type[Exception],
) -> Any:
    transaction = _search_one(
        env,
        "account.bank.statement.line",
        [("id", "=", transaction_id), ("company_id", "=", company_id)],
        company_id,
        failure_type,
    )
    if (
        transaction.company_id.id != company_id
        or not transaction.move_id
        or transaction.move_id.company_id.id != company_id
        or transaction.move_id.move_type != "entry"
        or transaction.move_id.state != "posted"
    ):
        raise _fail(
            failure_type,
            "state_conflict",
            "The bank transaction has no valid posted company entry.",
            exit_code=5,
        )
    return transaction


def _bank_transaction_actual_values(
    transaction: Any, *, include_foreign: bool = False,
    metadata_fields: set[str] | None = None,
) -> dict[str, Any]:
    result = {
        "date": str(transaction.date),
        "amount": _canonical_decimal_text(transaction.amount),
        "payment_ref": transaction.payment_ref,
        "partner_id": transaction.partner_id.id or None,
    }
    if include_foreign:
        result.update(
            foreign_currency_id=_relation_id(transaction.foreign_currency_id),
            amount_currency=_canonical_decimal_text(transaction.amount_currency),
        )
    for field in metadata_fields or ():
        result[field] = getattr(transaction, field) or None
    return result


def _bank_transaction_target_values(values: dict[str, Any]) -> dict[str, Any]:
    result = dict(values)
    if "amount" in result:
        result["amount"] = _canonical_decimal_text(result["amount"])
    if "amount_currency" in result:
        result["amount_currency"] = _canonical_decimal_text(result["amount_currency"])
    return result


def _bank_parts(transaction: Any) -> tuple[Any, Any, Any]:
    liquidity, suspense, other = transaction._seek_for_lines()
    return liquidity, suspense, other


def _bank_external_match_ids(transaction: Any) -> set[int]:
    bank_line_ids = set(transaction.move_id.line_ids.ids)
    partials = (
        transaction.move_id.line_ids.matched_debit_ids
        | transaction.move_id.line_ids.matched_credit_ids
    )
    external: set[int] = set()
    for partial in partials:
        debit_id = partial.debit_move_id.id
        credit_id = partial.credit_move_id.id
        if debit_id in bank_line_ids and credit_id not in bank_line_ids:
            external.add(credit_id)
        elif credit_id in bank_line_ids and debit_id not in bank_line_ids:
            external.add(debit_id)
    return external


def _bank_is_default_unmatched(transaction: Any) -> bool:
    liquidity, suspense, other = _bank_parts(transaction)
    lines = transaction.move_id.line_ids
    partials = lines.matched_debit_ids | lines.matched_credit_ids
    return bool(
        len(liquidity) == 1
        and len(suspense) == 1
        and not other
        and not partials
        and not lines.full_reconcile_id
        and not transaction.payment_ids
        and not transaction.is_reconciled
    )


def _bank_has_isolated_lines(transaction: Any) -> bool:
    liquidity, _suspense, _other = _bank_parts(transaction)
    lines = transaction.move_id.line_ids
    return bool(
        len(liquidity) == 1
        and not (lines.matched_debit_ids | lines.matched_credit_ids)
        and not lines.full_reconcile_id
        and not transaction.payment_ids
        and not any(
            getattr(line, "reconciled_lines_ids", False)
            or getattr(line, "payment_id", False)
            for line in lines
        )
    )


def _invalidate_bank_transaction(transaction: Any) -> None:
    transaction.invalidate_recordset(
        ["line_ids", "is_reconciled", "payment_ids", "amount_residual"]
    )
    transaction.move_id.invalidate_recordset(["line_ids", "state"])
    transaction.move_id.line_ids.invalidate_recordset(
        [
            "amount_residual",
            "amount_residual_currency",
            "reconciled",
            "matched_debit_ids",
            "matched_credit_ids",
            "full_reconcile_id",
        ]
    )


def _delete_bank_transaction(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    transaction = _bank_transaction(
        env, parameters["transaction_id"], company_id, failure_type
    )
    if transaction.statement_id or not _bank_is_default_unmatched(transaction):
        raise _fail(
            failure_type,
            "state_conflict",
            "Only an ungrouped, completely unmatched bank transaction can be deleted.",
            exit_code=5,
        )
    transaction_id = transaction.id
    move_id = transaction.move_id.id
    result = _deleted_result(
        _bank_transaction_result(transaction, company_id, failure_type)
    )
    transaction.unlink()
    if _scoped(env, "account.bank.statement.line", company_id).search_count(
        [("id", "=", transaction_id)], limit=1
    ) or _scoped(env, "account.move", company_id).search_count(
        [("id", "=", move_id)], limit=1
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not delete the bank transaction and its journal entry.",
            exit_code=6,
        )
    return result, False


def _update_bank_transaction(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    transaction = _bank_transaction(
        env, parameters["transaction_id"], company_id, failure_type
    )
    include_foreign = "foreign_currency_id" in parameters["changes"]
    metadata_fields = {"account_number", "partner_name"} & set(parameters["changes"])
    if include_foreign and not _bank_is_default_unmatched(transaction):
        raise _fail(failure_type, "state_conflict", "Foreign-currency changes require a completely unmatched bank transaction.", exit_code=5)
    actual = _bank_transaction_actual_values(
        transaction, include_foreign=include_foreign, metadata_fields=metadata_fields,
    )
    target = {**actual, **_bank_transaction_target_values(parameters["changes"])}
    if include_foreign and target["foreign_currency_id"] is not None:
        _ensure_ids(env, "res.currency", {target["foreign_currency_id"]}, [("active", "=", True)], company_id, failure_type)
        if target["foreign_currency_id"] == _statement_currency(transaction).id:
            raise _fail(failure_type, "business_rule_error", "The foreign currency must differ from the journal transaction currency.", exit_code=6)
        if (Decimal(target["amount_currency"]) > 0) != (Decimal(target["amount"]) > 0):
            raise _fail(failure_type, "business_rule_error", "Foreign and journal transaction amounts must have the same sign.", exit_code=6)
    if actual == target:
        return _bank_transaction_result(transaction, company_id, failure_type), True
    if not _bank_is_default_unmatched(transaction):
        raise _fail(
            failure_type,
            "state_conflict",
            "Only a completely unmatched bank transaction can be updated.",
            exit_code=5,
        )
    if target["partner_id"] is not None:
        _ensure_ids(
            env,
            "res.partner",
            {target["partner_id"]},
            [("company_id", "in", [False, company_id])],
            company_id,
            failure_type,
        )
    values = dict(parameters["changes"])
    if "amount" in values:
        values["amount"] = Decimal(values["amount"])
    if include_foreign:
        values["foreign_currency_id"] = values["foreign_currency_id"] or False
        values["amount_currency"] = Decimal(values["amount_currency"])
    if values.get("partner_id") is None and "partner_id" in values:
        values["partner_id"] = False
    for field in metadata_fields:
        values[field] = values[field] or False
    transaction.write(values)
    _invalidate_bank_transaction(transaction)
    if include_foreign:
        transaction.invalidate_recordset(["foreign_currency_id", "amount_currency"])
    if metadata_fields:
        transaction.invalidate_recordset(sorted(metadata_fields))
    if (
        transaction.move_id.state != "posted"
        or _bank_transaction_actual_values(
            transaction, include_foreign=include_foreign, metadata_fields=metadata_fields,
        ) != target
        or not _bank_is_default_unmatched(transaction)
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not apply the requested bank-transaction update.",
            exit_code=6,
        )
    return _bank_transaction_result(transaction, company_id, failure_type), False


def _match_bank_transaction(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    transaction = _bank_transaction(
        env, parameters["transaction_id"], company_id, failure_type
    )
    expected_ids = set(parameters["candidate_line_ids"])
    existing_ids = _bank_external_match_ids(transaction)
    if existing_ids:
        if existing_ids == expected_ids:
            return _bank_transaction_result(transaction, company_id, failure_type), True
        raise _fail(
            failure_type,
            "state_conflict",
            "The bank transaction already has different matched sources.",
            exit_code=5,
        )
    if not _bank_is_default_unmatched(transaction):
        raise _fail(
            failure_type,
            "state_conflict",
            "Only a completely unmatched bank transaction can be matched.",
            exit_code=5,
        )
    domain = list(transaction._get_default_amls_matching_domain(False))
    domain.extend(
        [
            ("id", "in", sorted(expected_ids)),
            ("company_id", "=", company_id),
            ("statement_line_id", "!=", transaction.id),
        ]
    )
    candidates = _scoped(env, "account.move.line", company_id).search(
        domain,
        limit=len(expected_ids) + 1,
        order="date desc, id desc",
    )
    if set(candidates.ids) != expected_ids:
        raise _fail(
            failure_type,
            "record_not_found",
            "A requested bank-match source is not an eligible company journal item.",
            exit_code=4,
        )
    transaction.set_line_bank_statement_line(sorted(expected_ids))
    _invalidate_bank_transaction(transaction)
    if _bank_external_match_ids(transaction) != expected_ids:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not match all requested bank-transaction sources.",
            exit_code=6,
        )
    return _bank_transaction_result(transaction, company_id, failure_type), False


def _unmatch_bank_transaction(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    transaction = _bank_transaction(
        env, parameters["transaction_id"], company_id, failure_type
    )
    if not _bank_external_match_ids(transaction):
        if _bank_is_default_unmatched(transaction):
            return _bank_transaction_result(transaction, company_id, failure_type), True
        if not _bank_has_isolated_lines(transaction):
            raise _fail(
                failure_type,
                "state_conflict",
                "The bank transaction has non-isolated reconciliation sources.",
                exit_code=5,
            )
        _ensure_ids(env, "account.move.line", set(transaction.move_id.line_ids.ids), [
            ("move_id", "=", transaction.move_id.id), ("company_id", "=", company_id),
        ], company_id, failure_type)
        _liquidity, _suspense, other = _bank_parts(transaction)
        account_ids = {
            line.account_id.id for line in other
            if not (getattr(line, "tax_repartition_line_id", False)
                    or getattr(line, "tax_line_id", False)
                    or getattr(line, "display_type", None) == "tax")
        }
        _ensure_ids(env, "account.account", account_ids, [
            ("company_ids", "in", [company_id]),
            ("account_type", "in", ["income", "income_other", "expense", "expense_other", "expense_depreciation", "expense_direct_cost"]),
        ], company_id, failure_type)
        if transaction.checked and transaction.is_reconciled and not transaction.move_id._is_user_able_to_review():
            raise _fail(failure_type, "business_rule_error", "Validated entries can only be changed by your accountant.", exit_code=6)
    transaction.action_undo_reconciliation()
    _invalidate_bank_transaction(transaction)
    if not _bank_is_default_unmatched(transaction):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not restore the default unmatched bank transaction.",
            exit_code=6,
        )
    return _bank_transaction_result(transaction, company_id, failure_type), False


def _replace_bank_counterparts(
    env: Any, parameters: dict[str, Any], company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    transaction = _bank_transaction(env, parameters["transaction_id"], company_id, failure_type)
    company = _search_one(env, "res.company", [("id", "=", company_id)], company_id, failure_type)
    journal = _ensure_ids(env, "account.journal", {transaction.journal_id.id}, [
        ("company_id", "=", company_id), ("type", "in", ["bank", "cash"]),
    ], company_id, failure_type)
    currency = company.currency_id
    if transaction.foreign_currency_id or _statement_currency(journal).id != currency.id:
        raise _fail(failure_type, "state_conflict", "Counterpart replacement requires a company-currency bank transaction without a foreign currency.", exit_code=5)
    _ensure_ids(env, "res.currency", {currency.id}, [], company_id, failure_type)
    _ensure_ids(env, "account.move", {transaction.move_id.id}, [
        ("company_id", "=", company_id), ("journal_id", "=", journal.id),
        ("move_type", "=", "entry"), ("state", "=", "posted"),
    ], company_id, failure_type)
    lines = _ensure_ids(env, "account.move.line", set(transaction.move_id.line_ids.ids), [
        ("company_id", "=", company_id), ("move_id", "=", transaction.move_id.id),
    ], company_id, failure_type)
    liquidity, _suspense, _other = _bank_parts(transaction)
    if not _bank_has_isolated_lines(transaction) or any(
        line.tax_ids or line.tax_repartition_line_id or line.tax_tag_ids
        or getattr(line, "group_tax_id", False) or getattr(line, "tax_line_id", False)
        or getattr(line, "tax_base_amount", 0) or line.display_type == "tax"
        for line in lines
    ):
        raise _fail(failure_type, "state_conflict", "Only isolated bank entries without existing tax lines or tax metadata can replace counterparts.", exit_code=5)
    _ensure_ids(env, "account.account", {line["account_id"] for line in parameters["lines"]}, [
        ("company_ids", "in", [company_id]), ("active", "=", True),
        ("account_type", "in", ["income", "income_other", "expense", "expense_other", "expense_depreciation", "expense_direct_cost"]),
    ], company_id, failure_type)
    _ensure_ids(env, "res.partner", {transaction.partner_id.id} if transaction.partner_id else set(),
                [("company_id", "in", [False, company_id])], company_id, failure_type)
    requested = [
        (line["account_id"], line["label"], _rounded_currency_amount(currency, line["balance"]))
        for line in parameters["lines"]
    ]
    if any(balance == 0 for _account, _label, balance in requested) or sum(
        (balance for _account, _label, balance in requested), Decimal(0)
    ) != -Decimal(str(liquidity.balance)):
        raise _fail(failure_type, "business_rule_error", "Requested counterparts must exactly balance the native liquidity line at company-currency precision.", exit_code=6)
    expected = sorted((account, label, _canonical_decimal_text(balance)) for account, label, balance in requested)

    def matches() -> bool:
        current_liquidity, suspense, counterparts = _bank_parts(transaction)
        return bool(
            len(current_liquidity) == 1 and not suspense and transaction.is_reconciled
            and len(counterparts) == len(requested)
            and sorted((line.account_id.id, line.name, _canonical_decimal_text(line.balance))
                       for line in counterparts) == expected
        )

    if matches():
        return _bank_transaction_result(transaction, company_id, failure_type), True
    if transaction.checked and transaction.is_reconciled and not transaction.move_id._is_user_able_to_review():
        raise _fail(failure_type, "business_rule_error", "Validated entries can only be changed by your accountant.", exit_code=6)
    liquidity_snapshot = (liquidity.id, _canonical_decimal_text(liquidity.balance),
                          liquidity.currency_id.id, _canonical_decimal_text(liquidity.amount_currency))
    values = [{
        "account_id": account, "name": label, "balance": float(balance),
        "currency_id": currency.id, "amount_currency": float(balance),
        "partner_id": transaction.partner_id.id or False,
    } for account, label, balance in requested]
    transaction._set_move_line_to_statement_line_move(liquidity, values)
    _invalidate_bank_transaction(transaction)
    current_liquidity, _suspense, _other = _bank_parts(transaction)
    if (transaction.move_id.state != "posted" or not _bank_has_isolated_lines(transaction)
        or len(current_liquidity) != 1 or not matches()
        or (current_liquidity.id, _canonical_decimal_text(current_liquidity.balance),
            current_liquidity.currency_id.id, _canonical_decimal_text(current_liquidity.amount_currency)) != liquidity_snapshot):
        raise _fail(failure_type, "odoo_write_error", "Odoo did not replace the requested isolated bank counterparts.", exit_code=6)
    return _bank_transaction_result(transaction, company_id, failure_type), False


def _write_off_bank_transaction(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    transaction = _bank_transaction(
        env, parameters["transaction_id"], company_id, failure_type
    )
    liquidity, suspense, other = _bank_parts(transaction)
    expected_account_id = parameters["write_off_account_id"]
    expected_label = parameters["label"]
    if len(liquidity) != 1:
        raise _fail(
            failure_type,
            "state_conflict",
            "The bank transaction has no unique liquidity line.",
            exit_code=5,
        )
    if not suspense:
        matches = other.filtered(
            lambda line: (
                line.account_id.id == expected_account_id
                and line.name == expected_label
            )
        )
        if len(matches) == 1 and len(other) == 1 and transaction.is_reconciled:
            return _bank_transaction_result(transaction, company_id, failure_type), True
        raise _fail(
            failure_type,
            "state_conflict",
            "The bank transaction has no unique suspense line to write off.",
            exit_code=5,
        )
    if len(suspense) != 1 or other or _bank_external_match_ids(transaction):
        raise _fail(
            failure_type,
            "state_conflict",
            "Only one isolated suspense line can be written off.",
            exit_code=5,
        )
    suspense_line = next(iter(suspense))
    actual_residual = _canonical_decimal_text(suspense_line.amount_residual)
    expected_residual = _canonical_decimal_text(parameters["expected_residual_amount"])
    if actual_residual != expected_residual:
        raise _fail(
            failure_type,
            "state_conflict",
            "The suspense residual no longer matches the requested amount.",
            exit_code=5,
        )
    _ensure_ids(
        env,
        "account.account",
        {expected_account_id},
        [
            ("company_ids", "in", [company_id]),
            (
                "account_type",
                "in",
                [
                    "income",
                    "income_other",
                    "expense",
                    "expense_other",
                    "expense_depreciation",
                    "expense_direct_cost",
                ],
            ),
            ("active", "=", True),
        ],
        company_id,
        failure_type,
    )
    transaction.edit_reconcile_line(
        suspense_line.id,
        {"account_id": expected_account_id, "name": expected_label},
    )
    _invalidate_bank_transaction(transaction)
    _liquidity, remaining_suspense, writeoff_lines = _bank_parts(transaction)
    matches = writeoff_lines.filtered(
        lambda line: (
            line.account_id.id == expected_account_id and line.name == expected_label
        )
    )
    if (
        remaining_suspense
        or len(matches) != 1
        or len(writeoff_lines) != 1
        or not transaction.is_reconciled
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not create the requested isolated write-off.",
            exit_code=6,
        )
    return _bank_transaction_result(transaction, company_id, failure_type), False


def _record_bank_transaction(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    key: str,
    marker: str,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    metadata_fields = {"account_number", "partner_name"} & set(parameters)
    existing = _scoped(env, "account.bank.statement.line", company_id).search(
        [
            ("company_id", "=", company_id),
            ("ref", "=", key),
        ],
        limit=2,
    )
    if existing:
        if len(existing) != 1 or existing.invoice_origin != marker:
            raise _fail(
                failure_type,
                "idempotency_conflict",
                "The idempotency key was already used by another bank transaction.",
                exit_code=5,
            )
        if existing.move_id.state != "posted":
            raise _fail(
                failure_type,
                "state_conflict",
                "The recorded bank transaction is no longer posted.",
                exit_code=5,
            )
        if "foreign_currency_id" in parameters:
            foreign_id = parameters["foreign_currency_id"]
            if foreign_id is not None:
                _ensure_ids(env, "res.currency", {foreign_id}, [("active", "=", True)], company_id, failure_type)
                if foreign_id == _statement_currency(existing).id:
                    raise _fail(failure_type, "business_rule_error", "The foreign currency must differ from the journal transaction currency.", exit_code=6)
            if (_relation_id(existing.foreign_currency_id) != foreign_id
                or not _same_decimal(existing.amount_currency, parameters["amount_currency"])):
                raise _fail(failure_type, "idempotency_conflict", "The recorded bank transaction no longer matches the requested foreign-currency pair.", exit_code=5)
        if metadata_fields:
            if any((getattr(existing, field) or None) != parameters[field] for field in metadata_fields):
                raise _fail(failure_type, "idempotency_conflict", "The recorded bank transaction no longer matches the requested bank metadata.", exit_code=5)
            _ensure_ids(env, "res.partner", {existing.partner_id.id} if existing.partner_id else set(),
                        [("company_id", "in", [False, company_id])], company_id, failure_type)
        return _bank_transaction_result(existing, company_id, failure_type), True

    company = _search_one(
        env,
        "res.company",
        [("id", "=", company_id)],
        company_id,
        failure_type,
    )
    journal = _ensure_ids(
        env,
        "account.journal",
        {parameters["journal_id"]},
        [
            ("company_id", "=", company.id),
            ("type", "in", ["bank", "cash"]),
        ],
        company_id,
        failure_type,
    )
    partner_ids = (
        {parameters["partner_id"]} if parameters["partner_id"] is not None else set()
    )
    _ensure_ids(
        env,
        "res.partner",
        partner_ids,
        [("company_id", "in", [False, company_id])],
        company_id,
        failure_type,
    )
    foreign_values: dict[str, Any] = {}
    if "foreign_currency_id" in parameters:
        if parameters["foreign_currency_id"] is not None:
            _ensure_ids(env, "res.currency", {parameters["foreign_currency_id"]}, [("active", "=", True)], company_id, failure_type)
            if parameters["foreign_currency_id"] == _statement_currency(journal).id:
                raise _fail(failure_type, "business_rule_error", "The foreign currency must differ from the journal transaction currency.", exit_code=6)
        foreign_values = {
            "foreign_currency_id": parameters["foreign_currency_id"] or False,
            "amount_currency": Decimal(parameters["amount_currency"]),
        }
    transaction = _scoped(env, "account.bank.statement.line", company_id).create(
        {
            **foreign_values,
            **{field: parameters[field] or False for field in metadata_fields},
            "company_id": company_id,
            "journal_id": parameters["journal_id"],
            "date": parameters["date"],
            "amount": Decimal(parameters["amount"]),
            "payment_ref": parameters["payment_ref"],
            "partner_id": parameters["partner_id"] or False,
            "ref": key,
            "invoice_origin": marker,
        }
    )
    if metadata_fields:
        _ensure_ids(env, "res.partner", {transaction.partner_id.id} if transaction.partner_id else set(),
                    [("company_id", "in", [False, company_id])], company_id, failure_type)
    if (transaction.move_id.state != "posted"
        or any((getattr(transaction, field) or None) != parameters[field] for field in metadata_fields)
        or (foreign_values and (
            _relation_id(transaction.foreign_currency_id) != parameters["foreign_currency_id"]
            or not _same_decimal(transaction.amount_currency, parameters["amount_currency"])
        ))):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not post the bank transaction.",
            exit_code=6,
        )
    return _bank_transaction_result(transaction, company_id, failure_type), False


def _transfer_result(move: Any, transfer_model: Any, company_id: int) -> dict[str, Any]:
    result = {
        "model": "account.move",
        "id": move.id,
        "name": move.name or move.ref or None,
        "state": move.state,
        "company_id": company_id,
        "move_type": move.move_type,
        "source_id": transfer_model.id,
        "line_ids": sorted(move.line_ids.ids),
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }
    assert set(result) == _RESULT_KEYS
    return result


def _move_has_marker(move: Any, marker: str) -> bool:
    origin = move.invoice_origin or ""
    return marker in {token.strip() for token in origin.split(";") if token.strip()}


def _append_move_marker(move: Any, marker: str, failure_type: type[Exception]) -> None:
    origin = move.invoice_origin or ""
    tokens = [token.strip() for token in origin.split(";") if token.strip()]
    if marker not in tokens:
        tokens.append(marker)
    value = ";".join(tokens)
    if len(value) > 255:
        raise _fail(
            failure_type,
            "idempotency_conflict",
            "The accounting move cannot hold another operation marker.",
            exit_code=5,
        )
    move.write({"invoice_origin": value})


def _transfer_model_result(
    transfer_model: Any,
    company_id: int,
    *,
    state: str | None = None,
    source_id: int | None = None,
) -> dict[str, Any]:
    result = {
        "model": "account.transfer.model",
        "id": transfer_model.id,
        "name": transfer_model.name or None,
        "state": state
        or (
            transfer_model.state
            if bool(transfer_model.active)
            else "archived"
        ),
        "company_id": company_id,
        "move_type": None,
        "source_id": source_id,
        "line_ids": _record_ids(transfer_model.line_ids),
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }
    assert set(result) == _RESULT_KEYS
    return result


def _account_transfer_model(
    env: Any,
    transfer_model_id: int,
    company_id: int,
    failure_type: type[Exception],
) -> Any:
    return _search_one(
        env,
        "account.transfer.model",
        [
            ("id", "=", transfer_model_id),
            ("company_id", "=", company_id),
        ],
        company_id,
        failure_type,
    )


def _transfer_model_values(transfer_model: Any) -> dict[str, Any]:
    lines = sorted(
        transfer_model.line_ids,
        key=lambda line: (line.sequence, line.id),
    )
    return {
        "name": transfer_model.name,
        "journal_id": _many2one_id(transfer_model.journal_id),
        "date_start": str(transfer_model.date_start),
        "date_stop": (
            str(transfer_model.date_stop) if transfer_model.date_stop else None
        ),
        "frequency": transfer_model.frequency,
        "origin_account_ids": _record_ids(transfer_model.account_ids),
        "destination_lines": [
            {
                "account_id": _many2one_id(line.account_id),
                "percentage": _canonical_decimal_text(line.percent),
            }
            for line in lines
        ],
    }


def _transfer_model_write_values(
    values: dict[str, Any], *, creating: bool
) -> dict[str, Any]:
    write_values = {
        key: value
        for key, value in values.items()
        if key in {"name", "journal_id", "date_start", "frequency"}
    }
    if "date_stop" in values:
        write_values["date_stop"] = values["date_stop"] or False
    if "origin_account_ids" in values:
        account_ids = values["origin_account_ids"]
        write_values["account_ids"] = [(6, 0, account_ids)]
        write_values["conditions"] = repr([("account_id", "in", account_ids)])
    if "destination_lines" in values:
        commands: list[tuple[Any, ...]] = [] if creating else [(5, 0, 0)]
        commands.extend(
            (
                0,
                0,
                {
                    "account_id": line["account_id"],
                    "percent": float(Decimal(line["percentage"])),
                    "sequence": sequence * 10,
                },
            )
            for sequence, line in enumerate(
                values["destination_lines"], start=1
            )
        )
        write_values["line_ids"] = commands
    return write_values


def _validate_transfer_model_references(
    env: Any,
    values: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> None:
    _search_one(
        env,
        "account.journal",
        [
            ("id", "=", values["journal_id"]),
            ("company_id", "=", company_id),
            ("type", "=", "general"),
            ("active", "=", True),
        ],
        company_id,
        failure_type,
    )
    account_ids = set(values["origin_account_ids"]) | {
        line["account_id"] for line in values["destination_lines"]
    }
    _ensure_ids(
        env,
        "account.account",
        account_ids,
        [
            ("company_ids", "in", [company_id]),
            ("account_type", "!=", "off_balance"),
        ],
        company_id,
        failure_type,
    )
    if values["date_stop"] is not None and (
        values["date_stop"] < values["date_start"]
    ):
        raise _fail(
            failure_type,
            "state_conflict",
            "The transfer stop date cannot precede its start date.",
            exit_code=5,
        )


def _create_transfer_model(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    _validate_transfer_model_references(
        env, parameters, company_id, failure_type
    )
    model = _scoped(env, "account.transfer.model", company_id)
    existing = model.search(
        [
            ("company_id", "=", company_id),
            ("name", "=", parameters["name"]),
        ],
        limit=2,
    )
    if existing:
        if (
            len(existing) == 1
            and bool(existing.active)
            and existing.state == "disabled"
            and _transfer_model_values(existing) == parameters
        ):
            return _transfer_model_result(existing, company_id), True
        raise _fail(
            failure_type,
            "idempotency_conflict",
            "A transfer model already uses the requested company and name.",
            exit_code=5,
        )
    transfer_model = model.create(
        {
            **_transfer_model_write_values(parameters, creating=True),
            "active": True,
            "state": "disabled",
        }
    )
    transfer_model.invalidate_recordset(
        [
            "name",
            "active",
            "state",
            "journal_id",
            "company_id",
            "date_start",
            "date_stop",
            "frequency",
            "account_ids",
            "line_ids",
            "conditions",
        ]
    )
    if (
        _many2one_id(transfer_model.company_id) != company_id
        or not bool(transfer_model.active)
        or transfer_model.state != "disabled"
        or _transfer_model_values(transfer_model) != parameters
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not create the requested transfer model.",
            exit_code=6,
        )
    return _transfer_model_result(transfer_model, company_id), False


def _update_transfer_model(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    transfer_model = _account_transfer_model(
        env, parameters["transfer_model_id"], company_id, failure_type
    )
    if not bool(transfer_model.active) or transfer_model.state != "disabled":
        raise _fail(
            failure_type,
            "state_conflict",
            "Only an active disabled transfer model can be updated.",
            exit_code=5,
        )
    actual = _transfer_model_values(transfer_model)
    target = {**actual, **parameters["changes"]}
    _validate_transfer_model_references(env, target, company_id, failure_type)
    if actual == target:
        return _transfer_model_result(transfer_model, company_id), True
    if "name" in parameters["changes"] and _scoped(
        env, "account.transfer.model", company_id
    ).search_count(
        [
            ("company_id", "=", company_id),
            ("name", "=", target["name"]),
            ("id", "!=", transfer_model.id),
        ],
        limit=1,
    ):
        raise _fail(
            failure_type,
            "state_conflict",
            "Another transfer model already uses the requested name.",
            exit_code=5,
        )
    write_values = _transfer_model_write_values(
        parameters["changes"], creating=False
    )
    transfer_model.write(write_values)
    transfer_model.invalidate_recordset(
        [
            "name",
            "active",
            "state",
            "journal_id",
            "company_id",
            "date_start",
            "date_stop",
            "frequency",
            "account_ids",
            "line_ids",
            "conditions",
        ]
    )
    if (
        _many2one_id(transfer_model.company_id) != company_id
        or not bool(transfer_model.active)
        or transfer_model.state != "disabled"
        or _transfer_model_values(transfer_model) != target
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not update the requested transfer model.",
            exit_code=6,
        )
    return _transfer_model_result(transfer_model, company_id), False


def _duplicate_transfer_model(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    source = _account_transfer_model(
        env, parameters["transfer_model_id"], company_id, failure_type
    )
    expected = {
        **_transfer_model_values(source),
        "name": parameters["name"],
    }
    model = _scoped(env, "account.transfer.model", company_id)
    existing = model.search(
        [
            ("company_id", "=", company_id),
            ("name", "=", parameters["name"]),
        ],
        limit=2,
    )
    if existing:
        if (
            len(existing) == 1
            and existing.id != source.id
            and bool(existing.active)
            and existing.state == "disabled"
            and _transfer_model_values(existing) == expected
        ):
            return _transfer_model_result(
                existing, company_id, source_id=source.id
            ), True
        raise _fail(
            failure_type,
            "idempotency_conflict",
            "A transfer model already uses the requested duplicate name.",
            exit_code=5,
        )
    duplicate = source.copy(
        default={
            "name": parameters["name"],
            "active": True,
            "state": "disabled",
        }
    )
    duplicate.invalidate_recordset(
        [
            "name",
            "active",
            "state",
            "journal_id",
            "company_id",
            "date_start",
            "date_stop",
            "frequency",
            "account_ids",
            "line_ids",
        ]
    )
    if (
        len(duplicate) != 1
        or duplicate.id == source.id
        or _many2one_id(duplicate.company_id) != company_id
        or not bool(duplicate.active)
        or duplicate.state != "disabled"
        or _transfer_model_values(duplicate) != expected
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not duplicate the requested transfer model.",
            exit_code=6,
        )
    return _transfer_model_result(
        duplicate, company_id, source_id=source.id
    ), False


def _transition_transfer_model(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    transfer_model = _account_transfer_model(
        env, parameters["transfer_model_id"], company_id, failure_type
    )
    active = bool(transfer_model.active)
    if capability_id == "account.transfer_model.archive":
        if not active:
            return _transfer_model_result(transfer_model, company_id), True
        transfer_model.action_archive()
        transfer_model.invalidate_recordset(["active", "state"])
        if bool(transfer_model.active) or transfer_model.state != "disabled":
            raise _fail(
                failure_type,
                "odoo_write_error",
                "Odoo did not archive and disable the transfer model.",
                exit_code=6,
            )
        return _transfer_model_result(transfer_model, company_id), False
    if capability_id == "account.transfer_model.restore":
        if active:
            if transfer_model.state != "disabled":
                raise _fail(
                    failure_type,
                    "state_conflict",
                    "An enabled transfer model cannot be restored.",
                    exit_code=5,
                )
            return _transfer_model_result(transfer_model, company_id), True
        transfer_model.action_unarchive()
        transfer_model.invalidate_recordset(["active", "state"])
        if not bool(transfer_model.active) or transfer_model.state != "disabled":
            raise _fail(
                failure_type,
                "odoo_write_error",
                "Odoo did not restore the transfer model as disabled.",
                exit_code=6,
            )
        return _transfer_model_result(transfer_model, company_id), False
    if not active:
        raise _fail(
            failure_type,
            "state_conflict",
            "An archived transfer model cannot change enabled state.",
            exit_code=5,
        )
    target_state = (
        "in_progress"
        if capability_id == "account.transfer_model.enable"
        else "disabled"
    )
    if capability_id == "account.transfer_model.enable":
        values = _transfer_model_values(transfer_model)
        total_percent = Decimal(str(transfer_model.total_percent))
        if (
            not values["origin_account_ids"]
            or not values["destination_lines"]
            or not Decimal(0) < total_percent <= Decimal(100)
        ):
            raise _fail(
                failure_type,
                "configuration_missing",
                "The transfer model is not fully configured.",
                exit_code=4,
            )
        _validate_transfer_model_references(
            env, values, company_id, failure_type
        )
    if transfer_model.state == target_state:
        return _transfer_model_result(transfer_model, company_id), True
    if capability_id == "account.transfer_model.enable":
        transfer_model.action_enable()
    else:
        transfer_model.action_disable()
    transfer_model.invalidate_recordset(["active", "state"])
    if not bool(transfer_model.active) or transfer_model.state != target_state:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not change the transfer-model state.",
            exit_code=6,
        )
    return _transfer_model_result(transfer_model, company_id), False


def _delete_transfer_model(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    transfer_model = _account_transfer_model(
        env, parameters["transfer_model_id"], company_id, failure_type
    )
    if (
        not bool(transfer_model.active)
        or transfer_model.state != "disabled"
        or transfer_model.move_ids
    ):
        raise _fail(
            failure_type,
            "state_conflict",
            "Only an active disabled transfer model without generated moves can be deleted.",
            exit_code=5,
        )
    result = _transfer_model_result(
        transfer_model, company_id, state="deleted"
    )
    transfer_model_id = transfer_model.id
    transfer_model.unlink()
    if _scoped(env, "account.transfer.model", company_id).search_count(
        [("id", "=", transfer_model_id)], limit=1
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not delete the requested transfer model.",
            exit_code=6,
        )
    return result, False


def _transfer_model(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> Any:
    if capability_id == "period.transfer.run":
        return _search_one(
            env,
            "account.transfer.model",
            [
                ("id", "=", parameters["transfer_model_id"]),
                ("company_id", "=", company_id),
            ],
            company_id,
            failure_type,
        )

    company = _search_one(
        env,
        "res.company",
        [("id", "=", company_id)],
        company_id,
        failure_type,
    )
    if company.account_fiscal_country_id.code != "CN":
        raise _fail(
            failure_type,
            "localization_unavailable",
            "The requested company is not configured for China accounting.",
            exit_code=4,
        )
    transfer_model = env.ref(
        "l10n_cn_reports.account_transfer_model_jz",
        raise_if_not_found=False,
    )
    if (
        not transfer_model
        or transfer_model._name != "account.transfer.model"
        or transfer_model.company_id.id != company_id
    ):
        raise _fail(
            failure_type,
            "uninstalled",
            "The China month-end transfer model is unavailable.",
            exit_code=4,
        )
    return transfer_model


def _run_period_transfer(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    key: str,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    from odoo import fields

    if parameters["run_date"] != fields.Date.today().isoformat():
        raise _fail(
            failure_type,
            "state_conflict",
            "parameters.run_date must equal the Odoo server date.",
            exit_code=5,
        )
    transfer_model = _transfer_model(
        env, capability_id, parameters, company_id, failure_type
    )
    if (
        not transfer_model.active
        or transfer_model.journal_id.company_id.id != company_id
        or not transfer_model.account_ids
        or not transfer_model.line_ids
        or abs(float(transfer_model.total_percent) - 100.0) > 0.000001
    ):
        raise _fail(
            failure_type,
            "configuration_missing",
            "The period-transfer model is not fully configured.",
            exit_code=4,
        )

    marker = _operation_marker(capability_id, key, parameters)
    marked = _scoped(env, "account.move", company_id).search(
        [
            ("company_id", "=", company_id),
            ("transfer_model_id", "=", transfer_model.id),
            ("invoice_origin", "ilike", marker),
        ],
        limit=2,
        order="date desc, id desc",
    )
    marked = marked.filtered(lambda move: _move_has_marker(move, marker))
    if len(marked) > 1:
        raise _fail(
            failure_type,
            "idempotency_conflict",
            "The period-transfer marker identifies multiple entries.",
            exit_code=5,
        )
    if marked:
        return _transfer_result(marked, transfer_model, company_id), True

    before_moves = _scoped(env, "account.move", company_id).search(
        [
            ("company_id", "=", company_id),
            ("transfer_model_id", "=", transfer_model.id),
        ],
        order="date, id",
    )
    before_lines = {move.id: tuple(sorted(move.line_ids.ids)) for move in before_moves}
    transfer_model.action_perform_auto_transfer()
    after_moves = _scoped(env, "account.move", company_id).search(
        [
            ("company_id", "=", company_id),
            ("transfer_model_id", "=", transfer_model.id),
        ],
        order="date, id",
    )
    candidates = after_moves.filtered(
        lambda move: before_lines.get(move.id) != tuple(sorted(move.line_ids.ids))
    )
    if not candidates:
        raise _fail(
            failure_type,
            "nothing_to_generate",
            "The transfer model produced no journal entry.",
            exit_code=4,
        )
    selected = candidates[-1:]
    if not selected.line_ids:
        raise _fail(
            failure_type,
            "nothing_to_generate",
            "The transfer model produced no journal entry.",
            exit_code=4,
        )
    if (
        selected.move_type != "entry"
        or selected.company_id.id != company_id
        or not selected.company_id.currency_id.is_zero(
            sum(selected.line_ids.mapped("balance"))
        )
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo returned an invalid period-transfer entry.",
            exit_code=6,
        )
    _append_move_marker(selected, marker, failure_type)
    return _transfer_result(selected, transfer_model, company_id), False


def _order_models(capability_id: str) -> tuple[str, str]:
    order_model = (
        "sale.order" if capability_id.startswith("sale.order.") else "purchase.order"
    )
    return order_model, f"{order_model}.line"


def _order_result(order: Any, company_id: int) -> dict[str, Any]:
    result = {
        "model": order._name,
        "id": order.id,
        "name": str(order.name or order.display_name),
        "state": str(order.state),
        "company_id": company_id,
        "move_type": None,
        "source_id": _many2one_id(order.partner_id),
        "line_ids": sorted(order.order_line.ids),
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }
    assert set(result) == _RESULT_KEYS
    return result


def _order_record(
    env: Any,
    capability_id: str,
    order_id: int,
    company_id: int,
    failure_type: type[Exception],
) -> Any:
    order_model, _ = _order_models(capability_id)
    return _search_one(
        env,
        order_model,
        [("id", "=", order_id), ("company_id", "=", company_id)],
        company_id,
        failure_type,
    )


def _validate_order_references(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> None:
    sale = capability_id.startswith("sale.order.")
    if "partner_id" in parameters:
        _ensure_ids(
            env,
            "res.partner",
            {parameters["partner_id"]},
            [("company_id", "in", [False, company_id])],
            company_id,
            failure_type,
        )
    payment_term_id = parameters.get("payment_term_id")
    if payment_term_id is not None:
        _ensure_ids(
            env,
            "account.payment.term",
            {payment_term_id},
            [("company_id", "in", [False, company_id])],
            company_id,
            failure_type,
        )
    if "pricelist_id" in parameters:
        _ensure_ids(
            env,
            "product.pricelist",
            {parameters["pricelist_id"]},
            [("company_id", "in", [False, company_id])],
            company_id,
            failure_type,
        )
    if "currency_id" in parameters:
        _ensure_ids(
            env,
            "res.currency",
            {parameters["currency_id"]},
            [("active", "=", True)],
            company_id,
            failure_type,
        )
    if "picking_type_id" in parameters:
        _ensure_ids(
            env,
            "stock.picking.type",
            {parameters["picking_type_id"]},
            [("company_id", "=", company_id), ("code", "=", "incoming")],
            company_id,
            failure_type,
        )
    incoterm_id = parameters.get("incoterm_id")
    if incoterm_id is not None:
        _ensure_ids(
            env,
            "account.incoterms",
            {incoterm_id},
            [],
            company_id,
            failure_type,
        )
    lines = parameters.get("lines") or []
    if not lines:
        return
    _ensure_ids(
        env,
        "product.product",
        {line["product_id"] for line in lines},
        [
            ("company_id", "in", [False, company_id]),
            ("sale_ok" if sale else "purchase_ok", "=", True),
        ],
        company_id,
        failure_type,
    )
    _ensure_ids(
        env,
        "uom.uom",
        {line["uom_id"] for line in lines},
        [],
        company_id,
        failure_type,
    )
    _ensure_ids(
        env,
        "account.tax",
        {tax_id for line in lines for tax_id in line["tax_ids"]},
        [
            ("company_id", "=", company_id),
            ("type_tax_use", "in", ["sale" if sale else "purchase", "none"]),
        ],
        company_id,
        failure_type,
    )


def _order_line_values(
    capability_id: str, line: dict[str, Any], sequence: int
) -> dict[str, Any]:
    sale = capability_id.startswith("sale.order.")
    return {
        "sequence": sequence,
        "product_id": line["product_id"],
        "name": line["name"],
        "product_uom_id": line["uom_id"],
        "product_uom_qty" if sale else "product_qty": Decimal(line["quantity"]),
        "price_unit": Decimal(line["price_unit"]),
        "discount": Decimal(line["discount"]),
        "tax_ids": [(6, 0, line["tax_ids"])],
        **({"date_planned": line["date_planned"]} if not sale else {}),
    }


def _order_line_commands(
    capability_id: str, lines: list[dict[str, Any]], *, clear: bool
) -> list[tuple[Any, ...]]:
    commands: list[tuple[Any, ...]] = [(5, 0, 0)] if clear else []
    commands.extend(
        (0, 0, _order_line_values(capability_id, line, index * 10))
        for index, line in enumerate(lines, start=1)
    )
    return commands


def _normalized_order_lines(
    capability_id: str, lines: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    purchase = capability_id.startswith("purchase.order.")
    return [
        {
            "product_id": line["product_id"],
            "name": line["name"],
            "quantity": _canonical_decimal_text(line["quantity"]),
            "uom_id": line["uom_id"],
            "price_unit": _canonical_decimal_text(line["price_unit"]),
            "discount": _canonical_decimal_text(line["discount"]),
            "tax_ids": list(line["tax_ids"]),
            **({"date_planned": line["date_planned"]} if purchase else {}),
        }
        for line in lines
    ]


def _current_order_lines(capability_id: str, order: Any) -> list[dict[str, Any]] | None:
    purchase = capability_id.startswith("purchase.order.")
    current: list[dict[str, Any]] = []
    for line in sorted(
        order.order_line,
        key=lambda item: (getattr(item, "sequence", 0), item.id),
    ):
        if getattr(line, "display_type", None) not in {None, False, "product"}:
            return None
        product_id = _many2one_id(line.product_id)
        uom_id = _many2one_id(line.product_uom_id)
        if product_id is None or uom_id is None or not _is_text(line.name):
            return None
        current.append(
            {
                "product_id": product_id,
                "name": line.name,
                "quantity": _canonical_decimal_text(
                    line.product_qty if purchase else line.product_uom_qty
                ),
                "uom_id": uom_id,
                "price_unit": _canonical_decimal_text(line.price_unit),
                "discount": _canonical_decimal_text(line.discount),
                "tax_ids": _relation_ids(line.tax_ids),
                **(
                    {"date_planned": _nullable_value(line.date_planned)}
                    if purchase
                    else {}
                ),
            }
        )
    return current


def _order_has_marker(order: Any, marker: str) -> bool:
    return marker in str(order.origin or "").split(";")


def _existing_order_for_key(
    env: Any,
    capability_id: str,
    company_id: int,
    key: str,
    marker: str,
    failure_type: type[Exception],
) -> Any | None:
    order_model, _ = _order_models(capability_id)
    key_marker = _idempotency_key_marker(capability_id, company_id, key)
    candidates = _scoped(env, order_model, company_id).search(
        [("company_id", "=", company_id), ("origin", "ilike", key_marker)],
        limit=2,
    )
    candidates = candidates.filtered(lambda order: _order_has_marker(order, key_marker))
    if not candidates:
        return None
    matching = candidates.filtered(lambda order: _order_has_marker(order, marker))
    if len(candidates) != 1 or len(matching) != 1:
        raise _fail(
            failure_type,
            "idempotency_conflict",
            "The order idempotency key was already used with different parameters.",
            exit_code=5,
        )
    return matching


def _create_order(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    key: str,
    marker: str,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    existing = _existing_order_for_key(
        env, capability_id, company_id, key, marker, failure_type
    )
    if existing:
        return _order_result(existing, company_id), True
    _validate_order_references(env, capability_id, parameters, company_id, failure_type)
    sale = capability_id == "sale.order.create"
    order_model, _ = _order_models(capability_id)
    values = {
        "company_id": company_id,
        "partner_id": parameters["partner_id"],
        "date_order": parameters["date_order"],
        "origin": (
            f"{_idempotency_key_marker(capability_id, company_id, key)};{marker}"
        ),
        "order_line": _order_line_commands(
            capability_id, parameters["lines"], clear=False
        ),
        **(
            {
                "pricelist_id": parameters["pricelist_id"],
                "client_order_ref": parameters["client_order_ref"] or False,
                "validity_date": parameters["validity_date"] or False,
                "commitment_date": parameters["commitment_date"] or False,
                "payment_term_id": parameters["payment_term_id"] or False,
            }
            if sale
            else {
                "currency_id": parameters["currency_id"],
                "picking_type_id": parameters["picking_type_id"],
                "partner_ref": parameters["partner_ref"] or False,
                "payment_term_id": parameters["payment_term_id"] or False,
                "incoterm_id": parameters["incoterm_id"] or False,
            }
        ),
    }
    order = _scoped(env, order_model, company_id).create(values)
    if (
        order.company_id.id != company_id
        or order.state != "draft"
        or _current_order_lines(capability_id, order)
        != _normalized_order_lines(capability_id, parameters["lines"])
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not create the requested draft order.",
            exit_code=6,
        )
    return _order_result(order, company_id), False


def _current_order_changes(
    capability_id: str, order: Any, requested_fields: set[str]
) -> dict[str, Any]:
    many2one_fields = {"payment_term_id", "incoterm_id"}
    values: dict[str, Any] = {}
    for field_name in requested_fields:
        raw = getattr(order, field_name)
        values[field_name] = (
            _many2one_id(raw) if field_name in many2one_fields else _nullable_value(raw)
        )
    return values


def _update_draft_order(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    order = _order_record(
        env, capability_id, parameters["order_id"], company_id, failure_type
    )
    changes = parameters["changes"]
    _validate_order_references(env, capability_id, changes, company_id, failure_type)
    current = _current_order_changes(capability_id, order, set(changes))
    if current == changes:
        return _order_result(order, company_id), True
    if order.state != "draft":
        raise _fail(
            failure_type,
            "state_conflict",
            "Only a draft order can be updated.",
            exit_code=5,
        )
    order.write(
        {
            field_name: False if value is None else value
            for field_name, value in changes.items()
        }
    )
    if _current_order_changes(capability_id, order, set(changes)) != changes:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not persist the requested order changes.",
            exit_code=6,
        )
    return _order_result(order, company_id), False


def _replace_order_lines(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    order = _order_record(
        env, capability_id, parameters["order_id"], company_id, failure_type
    )
    lines = parameters["lines"]
    _validate_order_references(
        env, capability_id, {"lines": lines}, company_id, failure_type
    )
    expected = _normalized_order_lines(capability_id, lines)
    if _current_order_lines(capability_id, order) == expected:
        return _order_result(order, company_id), True
    if order.state != "draft":
        raise _fail(
            failure_type,
            "state_conflict",
            "Only a draft order can have its lines replaced.",
            exit_code=5,
        )
    order.write({"order_line": _order_line_commands(capability_id, lines, clear=True)})
    if _current_order_lines(capability_id, order) != expected:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not persist the requested order lines.",
            exit_code=6,
        )
    return _order_result(order, company_id), False


def _transition_order(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    order = _order_record(
        env, capability_id, parameters["order_id"], company_id, failure_type
    )
    sale = capability_id.startswith("sale.order.")
    if capability_id.endswith(".confirm"):
        source_states = {"draft", "sent"}
        target_states = {"sale"} if sale else {"purchase", "to approve"}
        method = "action_confirm" if sale else "button_confirm"
    elif capability_id.endswith(".cancel"):
        source_states = (
            {"draft", "sent", "sale"}
            if sale
            else {"draft", "sent", "to approve", "purchase"}
        )
        target_states = {"cancel"}
        method = "action_cancel" if sale else "button_cancel"
    else:
        source_states = {"cancel"}
        target_states = {"draft"}
        method = "action_draft" if sale else "button_draft"
    if order.state in target_states:
        return _order_result(order, company_id), True
    if order.state not in source_states:
        raise _fail(
            failure_type,
            "state_conflict",
            "The order is not in a state accepted by this transition.",
            exit_code=5,
        )
    getattr(order, method)()
    if order.state not in target_states:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not complete the requested order transition.",
            exit_code=6,
        )
    return _order_result(order, company_id), False


def _linked_sale_invoices(env: Any, order_id: int, company_id: int) -> Any:
    return _scoped(env, "account.move", company_id).search(
        [
            ("company_id", "=", company_id),
            ("move_type", "=", "out_invoice"),
            ("invoice_line_ids.sale_line_ids.order_id", "=", order_id),
        ],
        order="id",
        limit=2,
    )


def _sale_invoice_order_ids(invoice: Any) -> set[int]:
    return {
        order_id
        for invoice_line in invoice.invoice_line_ids
        for sale_line in invoice_line.sale_line_ids
        if (order_id := _many2one_id(sale_line.order_id)) is not None
    }


def _create_sale_order_invoice(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    order = _search_one(
        env,
        "sale.order",
        [("id", "=", parameters["order_id"]), ("company_id", "=", company_id)],
        company_id,
        failure_type,
    )
    linked = _linked_sale_invoices(env, order.id, company_id)
    if linked:
        if len(linked) == 1 and _sale_invoice_order_ids(linked) == {order.id}:
            return _move_result(linked, company_id, source_id=order.id), True
        raise _fail(
            failure_type,
            "state_conflict",
            "The sales order already has a conflicting customer invoice.",
            exit_code=5,
        )
    if order.state != "sale" or order.invoice_status != "to invoice":
        raise _fail(
            failure_type,
            "state_conflict",
            "Only a confirmed sales order currently to invoice can create an invoice.",
            exit_code=5,
        )
    created = order._create_invoices()
    linked = _linked_sale_invoices(env, order.id, company_id)
    if (
        len(created) != 1
        or len(linked) != 1
        or created.id != linked.id
        or linked.company_id.id != company_id
        or linked.move_type != "out_invoice"
        or linked.state != "draft"
        or _sale_invoice_order_ids(linked) != {order.id}
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not create one sales-order-linked draft customer invoice.",
            exit_code=6,
        )
    return _move_result(linked, company_id, source_id=order.id), False


def _order_invoice_round(env: Any, capability_id: str, parameters: dict[str, Any], company_id: int,
                         key: str, failure_type: type[Exception]) -> tuple[dict[str, Any], bool]:
    sale = capability_id == _SALE_ORDER_INVOICE_CAPABILITY
    model = "sale.order" if sale else "purchase.order"
    orders = _ensure_ids(env, model, set(parameters["order_ids"]), [("company_id", "=", company_id)], company_id, failure_type)
    existing, operation_marker, key_marker = _round_moves_for_key(env, capability_id, parameters, company_id, key, failure_type)
    order_ids = set(orders.ids)

    def linked_ids(move: Any) -> set[int]:
        return _sale_invoice_order_ids(move) if sale else {
            line.purchase_line_id.order_id.id for line in move.invoice_line_ids if line.purchase_line_id
        }

    def verified(moves: Any, code: str) -> dict[str, Any]:
        covered = set()
        items = []
        for move in sorted(moves, key=lambda record: record.id):
            linked = linked_ids(move)
            if (move.company_id.id != company_id or not linked or not linked <= order_ids
                    or move.move_type not in ({"out_invoice", "out_refund"} if sale else {"in_invoice", "in_refund"})
                    or move.state not in ({"draft", "posted", "cancel"} if code == "idempotency_conflict" else {"draft"})):
                raise _fail(failure_type, code, "Odoo returned an invalid source-order accounting graph.", exit_code=5 if code == "idempotency_conflict" else 6)
            covered.update(linked)
            items.append(_move_result(move, company_id, source_id=next(iter(linked)) if len(linked) == 1 else None))
        if not 1 <= len(items) <= 1000 or covered != order_ids:
            raise _fail(failure_type, code, "Odoo did not return the selected source-order invoice set.", exit_code=5 if code == "idempotency_conflict" else 6)
        return {"items": items, "processed_count": len(items)}

    if existing:
        return verified(existing, "idempotency_conflict"), True
    if any(order.state != ("sale" if sale else "purchase") or order.invoice_status != "to invoice" for order in orders):
        raise _fail(failure_type, "state_conflict", "Every selected order must be confirmed and currently invoiceable.", exit_code=5)
    expected = {}
    for order in orders:
        lines = order._get_invoiceable_lines(parameters.get("deduct_down_payments", True)) if sale else order.order_line
        for line in lines:
            if not line.display_type:
                quantity = Decimal(-1) if sale and line.is_downpayment else Decimal(str(line.qty_to_invoice))
                if quantity:
                    expected[line.id] = quantity
    if sale:
        if parameters.get("consolidated_billing", True):
            native = orders._create_invoices(grouped=False, final=parameters.get("deduct_down_payments", True))
        else:
            native = _scoped(env, "account.move", company_id).browse([])
            for order in orders:
                native |= order._create_invoices(grouped=True, final=parameters.get("deduct_down_payments", True))
        moves = _ensure_ids(env, "account.move", set(native.ids), [("company_id", "=", company_id)], company_id, failure_type)
    else:
        domain = [("company_id", "=", company_id), ("invoice_line_ids.purchase_line_id.order_id", "in", parameters["order_ids"])]
        before = set(_scoped(env, "account.move", company_id).search(domain).ids)
        orders.action_create_invoice()
        moves = _scoped(env, "account.move", company_id).search(domain, order="id").filtered(lambda move: move.id not in before)
    result = verified(moves, "odoo_write_error")
    actual = {}
    for move in moves:
        sign = Decimal(-1) if move.move_type.endswith("refund") else Decimal(1)
        for line in move.invoice_line_ids:
            if line.display_type not in (False, "product") and not (
                sale and line.display_type == "line_section" and any(
                    source.id in expected and source.product_id.type == "combo" for source in line.sale_line_ids
                )
            ):
                continue
            source_lines = line.sale_line_ids if sale else ([line.purchase_line_id] if line.purchase_line_id else [])
            quantity_sign = sign if line.display_type in (False, "product") else Decimal(1)
            for source_line in source_lines:
                if source_line.id in expected:
                    actual[source_line.id] = actual.get(source_line.id, Decimal(0)) + quantity_sign * Decimal(str(line.quantity))
                elif Decimal(str(line.quantity)):
                    raise _fail(failure_type, "odoo_write_error", "Odoo created an accounting quantity outside the native invoiceable source lines.", exit_code=6)
    if not expected or actual != expected:
        raise _fail(failure_type, "odoo_write_error", "Odoo did not retain the native invoiceable quantities and line links.", exit_code=6)
    for move in moves:
        _mark_invoice_round(move, operation_marker, key_marker, failure_type)
    return result, False


def _create_sale_down_payment(env: Any, parameters: dict[str, Any], company_id: int,
                             key: str, failure_type: type[Exception]) -> tuple[dict[str, Any], bool]:
    order = _search_one(env, "sale.order", [("id", "=", parameters["order_id"]), ("company_id", "=", company_id)], company_id, failure_type)
    existing, operation_marker, key_marker = _round_moves_for_key(env, _SALE_DOWN_PAYMENT_CAPABILITY, parameters, company_id, key, failure_type)

    def verified(invoice: Any, code: str) -> dict[str, Any]:
        lines = invoice.invoice_line_ids.filtered(lambda line: line.display_type in (False, "product"))
        if (len(invoice) != 1 or invoice.company_id.id != company_id or invoice.move_type != "out_invoice"
                or invoice.state not in ({"draft", "posted", "cancel"} if code == "idempotency_conflict" else {"draft"})
                or _sale_invoice_order_ids(invoice) != {order.id} or not lines
                or any(not line.is_downpayment or not line.sale_line_ids
                       or any(not source.is_downpayment or source.order_id.id != order.id for source in line.sale_line_ids)
                       for line in lines)
                or _rounded_currency_amount(invoice.currency_id, str(invoice.amount_total)) <= 0
                or (parameters["method"] == "fixed" and _rounded_currency_amount(invoice.currency_id, str(invoice.amount_total))
                    != _rounded_currency_amount(invoice.currency_id, parameters["amount"]))):
            raise _fail(failure_type, code, "Odoo did not return the requested down-payment accounting graph and amount.", exit_code=5 if code == "idempotency_conflict" else 6)
        return _move_result(invoice, company_id, source_id=order.id)

    if existing:
        return verified(existing, "idempotency_conflict"), True
    if order.state != "sale":
        raise _fail(failure_type, "state_conflict", "Only a confirmed sales order can create a down payment.", exit_code=5)
    wizard = _scoped(env, "sale.advance.payment.inv", company_id).with_context(active_model="sale.order", active_ids=[order.id]).create({
        "sale_order_ids": [(6, 0, [order.id])], "advance_payment_method": parameters["method"],
        "amount" if parameters["method"] == "percentage" else "fixed_amount": float(Decimal(parameters["amount"])),
    })
    wizard._check_amount_is_positive()
    base_lines = [line._prepare_base_line_for_taxes_computation() for line in order.order_line if not line.display_type]
    tax = _scoped(env, "account.tax", company_id)
    tax._add_tax_details_in_base_lines(base_lines, order.company_id)
    tax._round_base_lines_tax_details(base_lines, order.company_id)
    expected_lines = tax._prepare_down_payment_lines(
        base_lines=base_lines, company=order.company_id,
        amount_type="percent" if parameters["method"] == "percentage" else "fixed",
        amount=float(Decimal(parameters["amount"])), computation_key=f"down_payment,{wizard.id}",
    )
    expected_amount = sum(
        Decimal(str(line["tax_details"]["total_excluded_currency"]))
        + Decimal(str(line["tax_details"]["delta_total_excluded_currency"]))
        + sum(Decimal(str(tax_data["tax_amount_currency"])) for tax_data in line["tax_details"]["taxes_data"])
        for line in expected_lines
    )
    native = wizard._create_invoices(order)
    invoice = _ensure_ids(env, "account.move", set(native.ids), [("company_id", "=", company_id)], company_id, failure_type)
    result = verified(invoice, "odoo_write_error")
    if _rounded_currency_amount(invoice.currency_id, str(invoice.amount_total)) != _rounded_currency_amount(invoice.currency_id, str(expected_amount)):
        raise _fail(failure_type, "odoo_write_error", "Odoo did not retain the native down-payment amount.", exit_code=6)
    _mark_invoice_round(invoice, operation_marker, key_marker, failure_type)
    return result, False


def _stock_transfer_result(picking: Any, company_id: int) -> dict[str, Any]:
    result = {
        "model": "stock.picking",
        "id": picking.id,
        "name": str(picking.name or picking.display_name),
        "state": str(picking.state),
        "company_id": company_id,
        "move_type": None,
        "source_id": _many2one_id(picking.picking_type_id),
        "line_ids": _record_ids(picking.move_ids),
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }
    assert set(result) == _RESULT_KEYS
    return result


def _stock_transfer(
    env: Any,
    transfer_id: int,
    company_id: int,
    failure_type: type[Exception],
) -> Any:
    picking = _search_one(
        env,
        "stock.picking",
        [("id", "=", transfer_id), ("company_id", "=", company_id)],
        company_id,
        failure_type,
    )
    if not picking.move_ids:
        raise _fail(
            failure_type,
            "state_conflict",
            "The stock transfer has no stock moves.",
            exit_code=5,
        )
    return picking


def _stock_transfer_has_marker(picking: Any, marker: str) -> bool:
    return marker in {
        token.strip() for token in str(picking.origin or "").split(";") if token.strip()
    }


def _existing_stock_transfer_for_key(
    env: Any,
    company_id: int,
    key: str,
    marker: str,
    failure_type: type[Exception],
) -> Any | None:
    key_marker = _idempotency_key_marker(
        _STOCK_TRANSFER_CREATE_CAPABILITY, company_id, key
    )
    candidates = _scoped(env, "stock.picking", company_id).search(
        [("company_id", "=", company_id), ("origin", "ilike", key_marker)],
        limit=2,
    )
    candidates = candidates.filtered(
        lambda picking: _stock_transfer_has_marker(picking, key_marker)
    )
    if not candidates:
        return None
    matching = candidates.filtered(
        lambda picking: _stock_transfer_has_marker(picking, marker)
    )
    if len(candidates) != 1 or len(matching) != 1:
        raise _fail(
            failure_type,
            "idempotency_conflict",
            "The stock-transfer idempotency key was used with other parameters.",
            exit_code=5,
        )
    return matching


def _validate_stock_transfer_references(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> None:
    _ensure_ids(
        env,
        "stock.picking.type",
        {parameters["picking_type_id"]},
        [("company_id", "=", company_id), ("active", "=", True)],
        company_id,
        failure_type,
    )
    _ensure_ids(
        env,
        "stock.location",
        {parameters["location_id"], parameters["location_dest_id"]},
        [
            ("company_id", "in", [False, company_id]),
            ("usage", "!=", "view"),
            ("active", "=", True),
        ],
        company_id,
        failure_type,
    )
    if parameters["partner_id"] is not None:
        _ensure_ids(
            env,
            "res.partner",
            {parameters["partner_id"]},
            [("company_id", "in", [False, company_id])],
            company_id,
            failure_type,
        )
    products = _ensure_ids(
        env,
        "product.product",
        {move["product_id"] for move in parameters["moves"]},
        [
            ("company_id", "in", [False, company_id]),
            ("active", "=", True),
            ("is_storable", "=", True),
            ("tracking", "=", "none"),
        ],
        company_id,
        failure_type,
    )
    uoms = _ensure_ids(
        env,
        "uom.uom",
        {move["uom_id"] for move in parameters["moves"]},
        [("active", "=", True)],
        company_id,
        failure_type,
    )
    product_by_id = {product.id: product for product in products}
    uom_by_id = {uom.id: uom for uom in uoms}
    if any(
        not product_by_id[move["product_id"]].uom_id._has_common_reference(
            uom_by_id[move["uom_id"]]
        )
        for move in parameters["moves"]
    ):
        raise _fail(
            failure_type,
            "state_conflict",
            "A stock move unit of measure is incompatible with its product.",
            exit_code=5,
        )


def _stock_move_values(
    move: dict[str, Any], parameters: dict[str, Any], company_id: int
) -> dict[str, Any]:
    return {
        "company_id": company_id,
        "product_id": move["product_id"],
        "description_picking": move["name"],
        "product_uom_qty": Decimal(move["quantity"]),
        "product_uom": move["uom_id"],
        "location_id": parameters["location_id"],
        "location_dest_id": parameters["location_dest_id"],
    }


def _normalized_stock_moves(moves: Any) -> list[dict[str, Any]]:
    return [
        {
            "product_id": _many2one_id(move.product_id),
            "name": str(move.description_picking),
            "quantity": _canonical_decimal_text(move.product_uom_qty),
            "uom_id": _many2one_id(move.product_uom),
        }
        for move in sorted(moves, key=lambda item: item.id)
    ]


def _create_stock_transfer(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    key: str,
    marker: str,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    existing = _existing_stock_transfer_for_key(
        env, company_id, key, marker, failure_type
    )
    if existing:
        return _stock_transfer_result(existing, company_id), True
    _validate_stock_transfer_references(env, parameters, company_id, failure_type)
    key_marker = _idempotency_key_marker(
        _STOCK_TRANSFER_CREATE_CAPABILITY, company_id, key
    )
    origin = ";".join(
        token
        for token in (parameters["origin"], key_marker, marker)
        if token is not None
    )
    values = {
        "company_id": company_id,
        "picking_type_id": parameters["picking_type_id"],
        "location_id": parameters["location_id"],
        "location_dest_id": parameters["location_dest_id"],
        "partner_id": parameters["partner_id"] or False,
        "origin": origin,
        "move_ids": [
            (0, 0, _stock_move_values(move, parameters, company_id))
            for move in parameters["moves"]
        ],
    }
    if parameters["scheduled_date"] is not None:
        values["scheduled_date"] = parameters["scheduled_date"]
    picking = _scoped(env, "stock.picking", company_id).create(values)
    expected_moves = [dict(move) for move in parameters["moves"]]
    if (
        picking.company_id.id != company_id
        or picking.state != "draft"
        or _many2one_id(picking.picking_type_id) != parameters["picking_type_id"]
        or _many2one_id(picking.location_id) != parameters["location_id"]
        or _many2one_id(picking.location_dest_id) != parameters["location_dest_id"]
        or _many2one_id(picking.partner_id) != parameters["partner_id"]
        or (
            parameters["scheduled_date"] is not None
            and _nullable_value(picking.scheduled_date) != parameters["scheduled_date"]
        )
        or str(picking.origin or "") != origin
        or _normalized_stock_moves(picking.move_ids) != expected_moves
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not create the requested standalone draft stock transfer.",
            exit_code=6,
        )
    return _stock_transfer_result(picking, company_id), False


def _transition_stock_transfer(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    picking = _stock_transfer(env, parameters["transfer_id"], company_id, failure_type)
    if capability_id == "stock.transfer.confirm":
        replay_states = {"waiting", "confirmed", "assigned", "done"}
        source_states = {"draft"}
        target_states = {"waiting", "confirmed", "assigned"}
        method = "action_confirm"
    elif capability_id == "stock.transfer.assign":
        replay_states = {"assigned", "done"}
        source_states = {"draft", "waiting", "confirmed"}
        target_states = {"waiting", "confirmed", "assigned"}
        method = "action_assign"
    elif capability_id == "stock.transfer.unreserve":
        replay_states = {"waiting", "confirmed"}
        source_states = {"assigned"}
        target_states = replay_states
        method = "do_unreserve"
    else:
        replay_states = {"cancel"}
        source_states = {"draft", "waiting", "confirmed", "assigned"}
        target_states = replay_states
        method = "action_cancel"
    if picking.state in replay_states:
        return _stock_transfer_result(picking, company_id), True
    if picking.state not in source_states:
        raise _fail(
            failure_type,
            "state_conflict",
            "The stock transfer is not in a state accepted by this action.",
            exit_code=5,
        )
    getattr(picking, method)()
    picking.invalidate_recordset(["state", "move_ids"])
    if picking.state not in target_states:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not complete the requested stock-transfer action.",
            exit_code=6,
        )
    return _stock_transfer_result(picking, company_id), False


def _set_stock_transfer_quantities(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    picking = _stock_transfer(env, parameters["transfer_id"], company_id, failure_type)
    move_ids = {line["move_id"] for line in parameters["lines"]}
    moves = _ensure_ids(
        env,
        "stock.move",
        move_ids,
        [("company_id", "=", company_id), ("picking_id", "=", picking.id)],
        company_id,
        failure_type,
    )
    move_by_id = {move.id: move for move in moves}
    if any(move.has_tracking != "none" for move in moves):
        raise _fail(
            failure_type,
            "state_conflict",
            "Tracked stock moves are outside the fixed quantity contract.",
            exit_code=5,
        )
    if picking.state != "cancel" and all(
        _same_decimal(move_by_id[line["move_id"]].quantity, line["quantity"])
        for line in parameters["lines"]
    ):
        return _stock_transfer_result(picking, company_id), True
    if picking.state not in {"draft", "waiting", "confirmed", "assigned"}:
        raise _fail(
            failure_type,
            "state_conflict",
            "Completed or cancelled stock-transfer quantities cannot be changed.",
            exit_code=5,
        )
    for line in parameters["lines"]:
        move_by_id[line["move_id"]].write({"quantity": Decimal(line["quantity"])})
    moves.invalidate_recordset(["quantity"])
    if any(
        not _same_decimal(move_by_id[line["move_id"]].quantity, line["quantity"])
        for line in parameters["lines"]
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not persist the requested stock-move quantities.",
            exit_code=6,
        )
    picking.invalidate_recordset(["state", "move_ids"])
    return _stock_transfer_result(picking, company_id), False


def _validate_stock_transfer(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    picking = _stock_transfer(env, parameters["transfer_id"], company_id, failure_type)
    if picking.state == "done":
        return _stock_transfer_result(picking, company_id), True
    if picking.state not in {"waiting", "confirmed", "assigned"}:
        raise _fail(
            failure_type,
            "state_conflict",
            "The stock transfer is not ready for validation.",
            exit_code=5,
        )
    if any(move.has_tracking != "none" for move in picking.move_ids):
        raise _fail(
            failure_type,
            "state_conflict",
            "Tracked stock moves are outside the fixed validation contract.",
            exit_code=5,
        )
    backorder_policy = parameters["backorder_policy"]
    type_policy = picking.picking_type_id.create_backorder
    if (backorder_policy == "create" and type_policy == "never") or (
        backorder_policy == "cancel" and type_policy == "always"
    ):
        raise _fail(
            failure_type,
            "state_conflict",
            "The picking type conflicts with the requested backorder policy.",
            exit_code=5,
        )
    result = picking.with_context(
        skip_backorder=True,
        button_validate_picking_ids=[picking.id],
        picking_ids_not_to_backorder=(
            [picking.id] if backorder_policy == "cancel" else []
        ),
    ).button_validate()
    picking.invalidate_recordset(["state", "move_ids"])
    if picking.state == "done":
        return _stock_transfer_result(picking, company_id), False
    if result is not True:
        raise _fail(
            failure_type,
            "state_conflict",
            "Odoo returned an unhandled stock-validation action.",
            exit_code=5,
        )
    raise _fail(
        failure_type,
        "odoo_write_error",
        "Odoo did not complete the stock transfer.",
        exit_code=6,
    )


def _purchase_bill(
    env: Any,
    bill_id: int,
    company_id: int,
    failure_type: type[Exception],
) -> Any:
    bill = _search_one(
        env,
        "account.move",
        [
            ("id", "=", bill_id),
            ("company_id", "=", company_id),
            ("move_type", "=", "in_invoice"),
        ],
        company_id,
        failure_type,
    )
    if bill.state != "draft":
        raise _fail(
            failure_type,
            "state_conflict",
            "Purchase bill matching is restricted to draft vendor bills.",
            exit_code=5,
        )
    return bill


def _purchase_bill_result(
    bill: Any,
    company_id: int,
    *,
    source_id: int | None = None,
    line_ids: list[int] | None = None,
) -> dict[str, Any]:
    result = _move_result(bill, company_id, source_id=source_id)
    if line_ids is not None:
        result["line_ids"] = sorted(line_ids)
    return result


def _linked_purchase_bills(env: Any, order_id: int, company_id: int) -> Any:
    return _scoped(env, "account.move", company_id).search(
        [
            ("company_id", "=", company_id),
            ("move_type", "=", "in_invoice"),
            ("invoice_line_ids.purchase_line_id.order_id", "=", order_id),
        ],
        order="id",
        limit=2,
    )


def _bill_covers_purchase_lines(order: Any, bill: Any) -> bool:
    expected = {
        line.id
        for line in order.order_line
        if not getattr(line, "display_type", None)
        and Decimal(str(line.product_qty)) > 0
    }
    linked = {
        line.purchase_line_id.id
        for line in bill.invoice_line_ids
        if _many2one_id(line.purchase_line_id) is not None
        and line.purchase_line_id.order_id.id == order.id
    }
    return bool(expected) and expected <= linked


def _create_purchase_bill(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    order = _search_one(
        env,
        "purchase.order",
        [("id", "=", parameters["order_id"]), ("company_id", "=", company_id)],
        company_id,
        failure_type,
    )
    linked = _linked_purchase_bills(env, order.id, company_id)
    if linked:
        if (
            len(linked) == 1
            and linked.state == "draft"
            and _bill_covers_purchase_lines(order, linked)
        ):
            return _purchase_bill_result(linked, company_id, source_id=order.id), True
        raise _fail(
            failure_type,
            "state_conflict",
            "The purchase order already has a linked vendor bill.",
            exit_code=5,
        )
    if order.state != "purchase" or order.invoice_status != "to invoice":
        raise _fail(
            failure_type,
            "state_conflict",
            "Only a confirmed purchase order currently to invoice can create a bill.",
            exit_code=5,
        )
    order.action_create_invoice()
    linked = _linked_purchase_bills(env, order.id, company_id)
    if (
        len(linked) != 1
        or linked.state != "draft"
        or not _bill_covers_purchase_lines(order, linked)
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not create one complete draft vendor bill.",
            exit_code=6,
        )
    return _purchase_bill_result(linked, company_id, source_id=order.id), False


def _purchase_match_records(
    env: Any,
    bill: Any,
    pairs: list[dict[str, int]],
    company_id: int,
    failure_type: type[Exception],
) -> list[tuple[Any, Any]]:
    purchase_ids = {pair["purchase_line_id"] for pair in pairs}
    bill_line_ids = {pair["bill_line_id"] for pair in pairs}
    if len(purchase_ids) != len(pairs) or len(bill_line_ids) != len(pairs):
        raise _fail(
            failure_type,
            "state_conflict",
            "Purchase and bill lines may occur only once per match request.",
            exit_code=5,
        )
    purchase_lines = _ensure_ids(
        env,
        "purchase.order.line",
        purchase_ids,
        [("company_id", "=", company_id), ("order_id.state", "=", "purchase")],
        company_id,
        failure_type,
    )
    bill_lines = _ensure_ids(
        env,
        "account.move.line",
        bill_line_ids,
        [
            ("company_id", "=", company_id),
            ("move_id", "=", bill.id),
            ("display_type", "=", "product"),
        ],
        company_id,
        failure_type,
    )
    purchase_by_id = {line.id: line for line in purchase_lines}
    bill_by_id = {line.id: line for line in bill_lines}
    records: list[tuple[Any, Any]] = []
    bill_partner = bill.partner_id.commercial_partner_id
    for pair in pairs:
        purchase_line = purchase_by_id[pair["purchase_line_id"]]
        bill_line = bill_by_id[pair["bill_line_id"]]
        if (
            purchase_line.order_id.company_id.id != company_id
            or purchase_line.order_id.state != "purchase"
            or purchase_line.order_id.partner_id.commercial_partner_id != bill_partner
            or purchase_line.product_id != bill_line.product_id
        ):
            raise _fail(
                failure_type,
                "state_conflict",
                "The purchase and bill lines are not eligible for matching.",
                exit_code=5,
            )
        current_id = _many2one_id(bill_line.purchase_line_id)
        if current_id not in {None, purchase_line.id}:
            raise _fail(
                failure_type,
                "state_conflict",
                "A bill line is already linked to another purchase line.",
                exit_code=5,
            )
        records.append((purchase_line, bill_line))
    return records


def _match_purchase_bill_lines(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    bill = _purchase_bill(env, parameters["bill_id"], company_id, failure_type)
    records = _purchase_match_records(
        env, bill, parameters["pairs"], company_id, failure_type
    )
    if all(
        _many2one_id(line.purchase_line_id) == purchase.id for purchase, line in records
    ):
        return _purchase_bill_result(
            bill,
            company_id,
            line_ids=[line.id for _, line in records],
        ), True
    if any(_many2one_id(line.purchase_line_id) is not None for _, line in records):
        raise _fail(
            failure_type,
            "state_conflict",
            "The match request mixes linked and unlinked bill lines.",
            exit_code=5,
        )
    match_model = _scoped(env, "purchase.bill.line.match", company_id)
    for purchase_line, bill_line in records:
        match_rows = match_model.browse([purchase_line.id, -bill_line.id]).exists()
        if len(match_rows) != 2:
            raise _fail(
                failure_type,
                "record_not_found",
                "The native purchase matching rows are unavailable.",
                exit_code=4,
            )
        match_rows.action_match_lines()
    if any(
        _many2one_id(line.purchase_line_id) != purchase.id for purchase, line in records
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not persist the purchase bill matches.",
            exit_code=6,
        )
    return _purchase_bill_result(
        bill,
        company_id,
        line_ids=[line.id for _, line in records],
    ), False


def _unmatch_purchase_bill_lines(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    bill = _purchase_bill(env, parameters["bill_id"], company_id, failure_type)
    lines = _ensure_ids(
        env,
        "account.move.line",
        set(parameters["bill_line_ids"]),
        [
            ("company_id", "=", company_id),
            ("move_id", "=", bill.id),
            ("display_type", "=", "product"),
        ],
        company_id,
        failure_type,
    )
    if not any(_many2one_id(line.purchase_line_id) is not None for line in lines):
        return _purchase_bill_result(
            bill, company_id, line_ids=parameters["bill_line_ids"]
        ), True
    lines.write({"purchase_line_id": False})
    if any(_many2one_id(line.purchase_line_id) is not None for line in lines):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not clear the purchase bill line links.",
            exit_code=6,
        )
    return _purchase_bill_result(
        bill, company_id, line_ids=parameters["bill_line_ids"]
    ), False


def _payment_term_result(term: Any, company_id: int) -> dict[str, Any]:
    result = _config_result(term, "account.payment.term", company_id)
    result["line_ids"] = _record_ids(term.line_ids)
    return result


def _payment_term(
    env: Any, payment_term_id: int, company_id: int, failure_type: type[Exception]
) -> Any:
    return _search_one(
        env,
        "account.payment.term",
        [("id", "=", payment_term_id), ("company_id", "=", company_id)],
        company_id,
        failure_type,
    )


def _normalized_payment_term_line(line: Any) -> dict[str, Any]:
    return {"value": line.value, "value_amount": _canonical_decimal_text(line.value_amount),
            "delay_type": line.delay_type, "nb_days": line.nb_days,
            "days_next_month": int(line.days_next_month)}


def _payment_term_copy_values(term: Any) -> dict[str, Any]:
    return {"active": bool(term.active), "sequence": term.sequence, "note": term.note or None,
            "display_on_invoice": bool(term.display_on_invoice), "early_discount": bool(term.early_discount),
            "discount_percentage": _canonical_decimal_text(term.discount_percentage), "discount_days": term.discount_days,
            "early_pay_discount_computation": term.early_pay_discount_computation,
            "lines": [_normalized_payment_term_line(line) for line in term.line_ids.sorted("id")]}


def _write_payment_term_processing(
    env: Any, capability_id: str, parameters: dict[str, Any],
    company_id: int, failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    with env.cr.savepoint():
        source_id, replay = None, False
        duplicate = capability_id == "payment_term.duplicate"
        term = _search_one(env, "account.payment.term", [
            ("id", "=", parameters["payment_term_id"]),
            ("company_id", "in", [False, company_id]) if duplicate else ("company_id", "=", company_id),
        ], company_id, failure_type)
        if duplicate:
            expected = _payment_term_copy_values(term)
            candidates = _scoped(env, "account.payment.term", company_id).search([
                ("company_id", "=", company_id), ("name", "=", parameters["name"]),
            ], limit=2)
            if candidates:
                if len(candidates) != 1 or candidates.id == term.id or _payment_term_copy_values(candidates) != expected:
                    raise _fail(failure_type, "idempotency_conflict", "The duplicate name already belongs to different payment-term configuration.", exit_code=5)
                target, replay = candidates, True
            else:
                target = term.copy({"company_id": company_id})
                # Native copy_data always substitutes its own name, even with a name default.
                target.write({**_payment_term_header_values(expected), "name": parameters["name"], "active": term.active})
                target.invalidate_recordset()
            if (target.id == term.id or _relation_id(target.company_id) != company_id
                or target.name != parameters["name"] or _payment_term_copy_values(target) != expected
                or set(target.line_ids.ids) & set(term.line_ids.ids)):
                raise _fail(failure_type, "odoo_write_error", "Native payment-term copy did not preserve independent configuration.", exit_code=6)
            result = _payment_term_result(target, company_id)
            result["source_id"] = term.id
            return result, replay
        if capability_id == "payment_term.delete":
            result = _deleted_result(_payment_term_result(term, company_id))
            result["line_ids"] = []
            term.unlink()
            if term.exists():
                raise _fail(failure_type, "odoo_write_error", "Native payment-term deletion failed.", exit_code=6)
            return result, False
        create = capability_id == "payment_term.line.create"
        remove = capability_id == "payment_term.line.delete"
        if create:
            changes = parameters["line"]
            expected = {**changes, "value_amount": _canonical_decimal_text(float(Decimal(changes["value_amount"])))}
            matches = term.line_ids.filtered(lambda line: _normalized_payment_term_line(line) == expected)
            if len(matches) > 1:
                raise _fail(failure_type, "idempotency_conflict", "Multiple native lines match this create payload.", exit_code=5)
            if matches:
                source_id, replay = matches.id, True
            else:
                before = set(term.line_ids.ids)
                term.write({"line_ids": _payment_term_line_commands([changes])[1:]})
                term.invalidate_recordset()
                new = term.line_ids.filtered(lambda line: line.id not in before)
                if len(new) != 1 or _normalized_payment_term_line(new) != expected:
                    raise _fail(failure_type, "odoo_write_error", "Native payment-term line creation did not preserve its payload.", exit_code=6)
                source_id = new.id
        else:
            patches = parameters["lines"] if capability_id == "payment_term.lines.update" else [
                {"line_id": parameters["line_id"], "changes": parameters.get("changes", {})},
            ]
            rows, targets, commands = {}, {}, []
            for patch in patches:
                row = _search_one(env, "account.payment.term.line", [
                    ("id", "=", patch["line_id"]), ("payment_id", "=", term.id),
                ], company_id, failure_type)
                rows[row.id] = row
                if remove:
                    commands.append((2, row.id, 0))
                    source_id = row.id
                else:
                    target = {**_normalized_payment_term_line(row), **patch["changes"]}
                    try:
                        payment_term_processing.line_values(target)
                    except ValueError as exc:
                        raise _fail(failure_type, "business_rule_error", str(exc), exit_code=6) from exc
                    targets[row.id] = {**target, "value_amount": _canonical_decimal_text(float(Decimal(target["value_amount"])))}
                    values = _payment_term_line_commands([target])[1][2]
                    commands.append((1, row.id, {field: value for field, value in values.items() if field in patch["changes"]}))
            if capability_id == "payment_term.line.update":
                source_id = parameters["line_id"]
            replay = not remove and all(_normalized_payment_term_line(rows[row_id]) == target for row_id, target in targets.items())
            if not replay:
                # One parent write validates the final total/discount after all native child commands.
                term.write({"line_ids": commands})
                term.invalidate_recordset()
            if remove:
                if source_id in term.line_ids.ids:
                    raise _fail(failure_type, "odoo_write_error", "Native payment-term line deletion failed.", exit_code=6)
            elif any(_normalized_payment_term_line(rows[row_id]) != target for row_id, target in targets.items()):
                raise _fail(failure_type, "odoo_write_error", "Native payment-term line changes did not preserve their payloads.", exit_code=6)
        result = _payment_term_result(term, company_id)
        result["source_id"] = source_id
        return result, replay


def _payment_term_header_values(parameters: dict[str, Any]) -> dict[str, Any]:
    values = {
        key: value
        for key, value in parameters.items()
        if key in _PAYMENT_TERM_HEADER_KEYS or key == "name"
    }
    for key in ("discount_percentage",):
        if key in values:
            values[key] = float(Decimal(values[key]))
    if "note" in values and values["note"] is None:
        values["note"] = False
    return values


def _payment_term_line_commands(lines: list[dict[str, Any]]) -> list[tuple[Any, ...]]:
    commands: list[tuple[Any, ...]] = [(5, 0, 0)]
    for line in lines:
        values = dict(line)
        values["value_amount"] = float(Decimal(values["value_amount"]))
        if "days_next_month" in values:
            values["days_next_month"] = str(values["days_next_month"])
        commands.append((0, 0, values))
    return commands


def _payment_term_lines_match(term: Any, lines: list[dict[str, Any]]) -> bool:
    if len(term.line_ids) != len(lines):
        return False
    for record, expected in zip(term.line_ids, lines, strict=True):
        if (
            record.value != expected["value"]
            or not _same_decimal(record.value_amount, expected["value_amount"])
            or record.delay_type != expected["delay_type"]
            or record.nb_days != expected["nb_days"]
            or str(record.days_next_month) != str(expected.get("days_next_month", 10))
        ):
            return False
    return True


def _create_payment_term(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    existing = _scoped(env, "account.payment.term", company_id).search(
        [
            ("company_id", "=", company_id),
            ("name", "=", parameters["name"]),
        ],
        limit=2,
    )
    if existing:
        expected_header = _payment_term_header_values(parameters)
        matches = len(existing) == 1 and all(
            getattr(existing, field) == value
            for field, value in expected_header.items()
        )
        if matches and _payment_term_lines_match(existing, parameters["lines"]):
            return _payment_term_result(existing, company_id), True
        raise _fail(
            failure_type,
            "state_conflict",
            "A payment term with this company and name already exists.",
            exit_code=5,
        )
    values = _payment_term_header_values(parameters)
    values.update(
        {
            "company_id": company_id,
            "line_ids": _payment_term_line_commands(parameters["lines"])[1:],
        }
    )
    term = _scoped(env, "account.payment.term", company_id).create(values)
    if _many2one_id(term.company_id) != company_id:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not create the payment term in the requested company.",
            exit_code=6,
        )
    return _payment_term_result(term, company_id), False


def _update_payment_term(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    term = _payment_term(env, parameters["payment_term_id"], company_id, failure_type)
    values = _payment_term_header_values(parameters)
    comparisons = {
        key: (False if value is None else value) for key, value in values.items()
    }
    if all(getattr(term, key) == value for key, value in comparisons.items()):
        return _payment_term_result(term, company_id), True
    term.write(values)
    term.invalidate_recordset(list(values))
    if not all(getattr(term, key) == value for key, value in comparisons.items()):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not update the payment term.",
            exit_code=6,
        )
    return _payment_term_result(term, company_id), False


def _replace_payment_term_lines(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    term = _payment_term(env, parameters["payment_term_id"], company_id, failure_type)
    if _payment_term_lines_match(term, parameters["lines"]):
        return _payment_term_result(term, company_id), True
    term.write({"line_ids": _payment_term_line_commands(parameters["lines"])})
    term.invalidate_recordset(["line_ids"])
    if not term.line_ids:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not replace the payment-term lines.",
            exit_code=6,
        )
    return _payment_term_result(term, company_id), False


def _transition_payment_term(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    term = _payment_term(env, parameters["payment_term_id"], company_id, failure_type)
    target = capability_id == "payment_term.restore"
    if bool(term.active) == target:
        return _payment_term_result(term, company_id), True
    term.write({"active": target})
    term.invalidate_recordset(["active"])
    if bool(term.active) != target:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not change the payment-term archive state.",
            exit_code=6,
        )
    return _payment_term_result(term, company_id), False


def _generate_period_accrual(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    key: str,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    marker = _operation_marker("period.accrual.generate", key, parameters)
    key_marker = _idempotency_key_marker("period.accrual.generate", company_id, key)
    existing = _generated_pair_for_key(
        env, company_id, key_marker, marker, failure_type
    )
    if existing is not None:
        primary, reversal = existing
        if (
            primary.state != "posted"
            or reversal.state != "posted"
            or str(primary.date) != parameters["date"]
            or str(reversal.date) != parameters["reversal_date"]
        ):
            raise _fail(
                failure_type,
                "state_conflict",
                "The existing accrual pair no longer matches the requested state.",
                exit_code=5,
            )
        return _move_result(primary, company_id, source_id=reversal.id), True
    source_model = parameters["source_model"]
    state_domain = (
        [("state", "in", ["sale", "done"])]
        if source_model == "sale.order"
        else [("state", "in", ["purchase", "done"])]
    )
    orders = _ensure_ids(
        env,
        source_model,
        set(parameters["order_ids"]),
        [("company_id", "=", company_id), *state_domain],
        company_id,
        failure_type,
    )
    journal = _search_one(
        env,
        "account.journal",
        [
            ("id", "=", parameters["journal_id"]),
            ("company_id", "=", company_id),
            ("type", "=", "general"),
        ],
        company_id,
        failure_type,
    )
    account = _search_one(
        env,
        "account.account",
        [
            ("id", "=", parameters["accrual_account_id"]),
            ("company_ids", "in", [company_id]),
            (
                "account_type",
                "=",
                "liability_current"
                if source_model == "purchase.order"
                else "asset_current",
            ),
        ],
        company_id,
        failure_type,
    )
    wizard_values = {
        "company_id": company_id,
        "journal_id": journal.id,
        "date": parameters["date"],
        "reversal_date": parameters["reversal_date"],
        "account_id": account.id,
    }
    if "amount" in parameters:
        wizard_values["amount"] = float(Decimal(parameters["amount"]))
    wizard = (
        _scoped(env, "account.accrued.orders.wizard", company_id)
        .with_context(active_model=source_model, active_ids=orders.ids)
        .create(wizard_values)
    )
    action = wizard.create_entries()
    domain = action.get("domain") if isinstance(action, dict) else None
    move_ids = (
        domain[0][2]
        if isinstance(domain, list)
        and len(domain) == 1
        and isinstance(domain[0], (list, tuple))
        and len(domain[0]) == 3
        and tuple(domain[0][:2]) == ("id", "in")
        and isinstance(domain[0][2], (list, tuple))
        else []
    )
    moves = _ensure_ids(
        env,
        "account.move",
        set(move_ids),
        [("company_id", "=", company_id), ("state", "=", "posted")],
        company_id,
        failure_type,
    )
    primary = moves.filtered(lambda move: str(move.date) == parameters["date"])
    reversal = moves.filtered(
        lambda move: str(move.date) == parameters["reversal_date"]
    )
    if len(moves) != 2 or len(primary) != 1 or len(reversal) != 1:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not return the verified accrual and reversal moves.",
            exit_code=6,
        )
    (primary + reversal).write({"invoice_origin": f"{key_marker};{marker}"})
    if any(
        not _move_has_marker(move, key_marker) or not _move_has_marker(move, marker)
        for move in primary + reversal
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not persist the accrual idempotency marker.",
            exit_code=6,
        )
    return _move_result(primary, company_id, source_id=reversal.id), False


def _fiscal_position_result(position: Any, company_id: int) -> dict[str, Any]:
    result = _config_result(position, "account.fiscal.position", company_id)
    result["line_ids"] = _record_ids(position.account_ids)
    return result


def _fiscal_position(
    env: Any, record_id: int, company_id: int, failure_type: type[Exception]
) -> Any:
    return _search_one(
        env,
        "account.fiscal.position",
        [("id", "=", record_id), ("company_id", "=", company_id)],
        company_id,
        failure_type,
    )


def _validate_fiscal_position_references(
    env: Any, values: dict[str, Any], company_id: int, failure_type: type[Exception]
) -> None:
    if values.get("country_id"):
        _ensure_ids(
            env,
            "res.country",
            {values["country_id"]},
            [],
            company_id,
            failure_type,
        )
    if values.get("country_group_id"):
        _ensure_ids(
            env,
            "res.country.group",
            {values["country_group_id"]},
            [],
            company_id,
            failure_type,
        )
    _ensure_ids(
        env,
        "res.country.state",
        set(values.get("state_ids", [])),
        [],
        company_id,
        failure_type,
    )


def _fiscal_position_values(values: dict[str, Any]) -> dict[str, Any]:
    result = dict(values)
    for field in ("country_id", "country_group_id", "zip_from", "zip_to", "note"):
        if field in result and result[field] is None:
            result[field] = False
    if "state_ids" in result:
        result["state_ids"] = [(6, 0, result["state_ids"])]
    return result


def _sanitize_html(value: str) -> Any:
    from odoo.tools import html_sanitize

    return html_sanitize(value)


def _configuration_matches(record: Any, values: dict[str, Any]) -> bool:
    for field, expected in values.items():
        actual = getattr(record, field)
        if field in {"state_ids", "excluded_journal_ids"}:
            if _record_ids(actual) != expected:
                return False
        elif field in {"country_id", "country_group_id"}:
            if _many2one_id(actual) != expected:
                return False
        elif field == "note":
            if actual != (False if expected is None else _sanitize_html(expected)):
                return False
        elif (False if expected is None else expected) != actual:
            return False
    return True


def _create_fiscal_position(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    _validate_fiscal_position_references(env, parameters, company_id, failure_type)
    model = _scoped(env, "account.fiscal.position", company_id)
    existing = model.search(
        [("company_id", "=", company_id), ("name", "=", parameters["name"])],
        limit=2,
    )
    expected = {**_FISCAL_POSITION_CREATE_DEFAULTS, **parameters}
    if existing:
        if len(existing) == 1 and _configuration_matches(existing, expected):
            return _fiscal_position_result(existing, company_id), True
        raise _fail(
            failure_type,
            "state_conflict",
            "A fiscal position with this company and name already exists.",
            exit_code=5,
        )
    values = _fiscal_position_values(parameters)
    values["company_id"] = company_id
    position = model.create(values)
    if _many2one_id(position.company_id) != company_id:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not create the fiscal position in the requested company.",
            exit_code=6,
        )
    position.invalidate_recordset(list(expected))
    if not _configuration_matches(position, expected):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not create the requested fiscal-position configuration.",
            exit_code=6,
        )
    return _fiscal_position_result(position, company_id), False


def _update_fiscal_position(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    position = _fiscal_position(
        env, parameters["fiscal_position_id"], company_id, failure_type
    )
    changes = parameters["changes"]
    if _configuration_matches(position, changes):
        return _fiscal_position_result(position, company_id), True
    effective_references = {
        "country_id": changes.get("country_id", _many2one_id(position.country_id)),
        "country_group_id": changes.get(
            "country_group_id", _many2one_id(position.country_group_id)
        ),
        "state_ids": changes.get("state_ids", _record_ids(position.state_ids)),
    }
    _validate_fiscal_position_references(
        env, effective_references, company_id, failure_type
    )
    position.write(_fiscal_position_values(changes))
    position.invalidate_recordset(list(changes))
    if not _configuration_matches(position, changes):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not update the fiscal position.",
            exit_code=6,
        )
    return _fiscal_position_result(position, company_id), False


def _replace_fiscal_position_mappings(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    position = _fiscal_position(
        env, parameters["fiscal_position_id"], company_id, failure_type
    )
    account_ids = {
        value
        for mapping in parameters["mappings"]
        for value in (mapping["source_account_id"], mapping["destination_account_id"])
    }
    accounts = _ensure_ids(
        env,
        "account.account",
        account_ids,
        [("company_ids", "in", [company_id])],
        company_id,
        failure_type,
    )
    if any(
        set(_record_ids(account.company_ids)) != {company_id} for account in accounts
    ):
        raise _fail(
            failure_type,
            "record_not_found",
            "Fiscal-position mapping accounts must belong only to the company.",
            exit_code=4,
        )
    expected = [
        (mapping["source_account_id"], mapping["destination_account_id"])
        for mapping in parameters["mappings"]
    ]
    current = sorted(
        (_many2one_id(line.account_src_id), _many2one_id(line.account_dest_id))
        for line in position.account_ids
    )
    if current == expected:
        return _fiscal_position_result(position, company_id), True
    position.account_ids.unlink()
    if expected:
        model = _scoped(env, "account.fiscal.position.account", company_id)
        model.create(
            [
                {
                    "position_id": position.id,
                    "account_src_id": source_id,
                    "account_dest_id": destination_id,
                }
                for source_id, destination_id in expected
            ]
        )
    position.invalidate_recordset(["account_ids"])
    reread = sorted(
        (_many2one_id(line.account_src_id), _many2one_id(line.account_dest_id))
        for line in position.account_ids
    )
    if reread != expected:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not replace the fiscal-position account mappings.",
            exit_code=6,
        )
    return _fiscal_position_result(position, company_id), False


def _transition_fiscal_position(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    position = _fiscal_position(
        env, parameters["fiscal_position_id"], company_id, failure_type
    )
    target = capability_id == "fiscal_position.restore"
    if bool(position.active) == target:
        return _fiscal_position_result(position, company_id), True
    position.write({"active": target})
    position.invalidate_recordset(["active"])
    if bool(position.active) != target:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not change the fiscal-position archive state.",
            exit_code=6,
        )
    return _fiscal_position_result(position, company_id), False


def _journal_group(
    env: Any, record_id: int, company_id: int, failure_type: type[Exception]
) -> Any:
    return _search_one(
        env,
        "account.journal.group",
        [("id", "=", record_id), ("company_id", "=", company_id)],
        company_id,
        failure_type,
    )


def _journal_group_values(
    env: Any, values: dict[str, Any], company_id: int, failure_type: type[Exception]
) -> dict[str, Any]:
    result = dict(values)
    journal_ids = result.get("excluded_journal_ids")
    if journal_ids is not None:
        _ensure_ids(
            env,
            "account.journal",
            set(journal_ids),
            [("company_id", "=", company_id)],
            company_id,
            failure_type,
        )
        result["excluded_journal_ids"] = [(6, 0, journal_ids)]
    return result


def _write_journal_group(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    create = capability_id == "journal.group.create"
    values = parameters if create else parameters["changes"]
    if create:
        model = _scoped(env, "account.journal.group", company_id)
        existing = model.search(
            [("company_id", "=", company_id), ("name", "=", values["name"])],
            limit=2,
        )
        expected = {**_JOURNAL_GROUP_CREATE_DEFAULTS, **values}
        if existing:
            if len(existing) == 1 and _configuration_matches(existing, expected):
                return _config_result(
                    existing, "account.journal.group", company_id
                ), True
            raise _fail(
                failure_type,
                "state_conflict",
                "The company already has a different journal group with this name.",
                exit_code=5,
            )
        create_values = _journal_group_values(env, values, company_id, failure_type)
        create_values["company_id"] = company_id
        group = model.create(create_values)
        if _many2one_id(group.company_id) != company_id:
            raise _fail(
                failure_type,
                "odoo_write_error",
                "Odoo did not create the journal group in the requested company.",
                exit_code=6,
            )
        group.invalidate_recordset(list(expected))
        if not _configuration_matches(group, expected):
            raise _fail(
                failure_type,
                "odoo_write_error",
                "Odoo did not create the requested journal-group configuration.",
                exit_code=6,
            )
        return _config_result(group, "account.journal.group", company_id), False
    group = _journal_group(
        env, parameters["journal_group_id"], company_id, failure_type
    )
    if _configuration_matches(group, values):
        return _config_result(group, "account.journal.group", company_id), True
    group.write(_journal_group_values(env, values, company_id, failure_type))
    group.invalidate_recordset(list(values))
    if not _configuration_matches(group, values):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not update the journal group.",
            exit_code=6,
        )
    return _config_result(group, "account.journal.group", company_id), False


def _root_company_id(
    env: Any, company_id: int, failure_type: type[Exception]
) -> int:
    company = _search_one(
        env,
        "res.company",
        [("id", "=", company_id)],
        company_id,
        failure_type,
    )
    return _many2one_id(getattr(company, "root_id", False)) or company.id


def _currency_rate_result(rate: Any, company_id: int) -> dict[str, Any]:
    result = _config_result(rate, "res.currency.rate", company_id)
    result["name"] = str(rate.name) if rate.name else None
    result["source_id"] = _many2one_id(rate.currency_id)
    return result


def _record_currency_rate(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    _ensure_ids(
        env,
        "res.currency",
        {parameters["currency_id"]},
        [("active", "=", True)],
        company_id,
        failure_type,
    )
    root_company_id = _root_company_id(env, company_id, failure_type)
    model = _scoped(env, "res.currency.rate", company_id)
    existing = model.search(
        [
            ("company_id", "=", root_company_id),
            ("currency_id", "=", parameters["currency_id"]),
            ("name", "=", parameters["date"]),
        ],
        limit=2,
    )
    if existing:
        if len(existing) == 1 and _same_decimal(
            existing.inverse_company_rate,
            parameters["company_units_per_foreign_unit"],
        ):
            return _currency_rate_result(existing, company_id), True
        raise _fail(
            failure_type,
            "idempotency_conflict",
            "The currency rate already exists with a different value.",
            exit_code=5,
        )
    rate = model.create(
        {
            "name": parameters["date"],
            "currency_id": parameters["currency_id"],
            "company_id": root_company_id,
            "inverse_company_rate": Decimal(
                parameters["company_units_per_foreign_unit"]
            ),
        }
    )
    if (
        _many2one_id(rate.company_id) != root_company_id
        or _many2one_id(rate.currency_id) != parameters["currency_id"]
        or str(rate.name) != parameters["date"]
        or not _same_decimal(
            rate.inverse_company_rate,
            parameters["company_units_per_foreign_unit"],
        )
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not record the requested currency rate.",
            exit_code=6,
        )
    return _currency_rate_result(rate, company_id), False


def _owned_currency_rate(
    env: Any, rate_id: int, company_id: int, failure_type: type[Exception],
) -> Any:
    if _root_company_id(env, company_id, failure_type) != company_id:
        raise _fail(failure_type, "company_unavailable", "Rate maintenance requires its explicit root-company context.", exit_code=3)
    return _search_one(env, "res.currency.rate", [
        ("id", "=", rate_id), ("company_id", "=", company_id),
    ], company_id, failure_type)


def _update_currency_rate(
    env: Any, parameters: dict[str, Any], company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    rate = _owned_currency_rate(env, parameters["rate_id"], company_id, failure_type)
    changes = parameters["changes"]
    def matches() -> bool:
        if "date" in changes and str(rate.name) != changes["date"]:
            return False
        if "company_units_per_foreign_unit" not in changes:
            return True
        quote = float(Decimal(changes["company_units_per_foreign_unit"]))
        if not isfinite(quote) or quote <= 0:
            return False
        last_rates = rate._get_last_rates_for_companies(rate.company_id | rate.env.company.root_id)
        expected = (1.0 / quote) * last_rates[rate.company_id]
        actual = rate.rate
        return (isfinite(expected) and expected > 0 and isfinite(actual) and actual > 0
                and actual == expected)
    if matches():
        return _currency_rate_result(rate, company_id), True
    currency_id = rate.currency_id.id
    if "date" in changes:
        duplicates = _scoped(env, "res.currency.rate", company_id).search([
            ("company_id", "=", company_id), ("currency_id", "=", currency_id),
            ("name", "=", changes["date"]), ("id", "!=", rate.id),
        ], limit=1)
        if duplicates:
            raise _fail(failure_type, "idempotency_conflict", "The currency already has a rate on the requested date.", exit_code=5)
    values: dict[str, Any] = {}
    if "date" in changes:
        values["name"] = changes["date"]
    if "company_units_per_foreign_unit" in changes:
        values["inverse_company_rate"] = Decimal(changes["company_units_per_foreign_unit"])
    rate.write(values)
    rate.invalidate_recordset()
    if rate.company_id.id != company_id or rate.currency_id.id != currency_id or not matches():
        raise _fail(failure_type, "odoo_write_error", "Native currency-rate maintenance did not persist the requested fields.", exit_code=6)
    return _currency_rate_result(rate, company_id), False


def _delete_currency_rate(
    env: Any, parameters: dict[str, Any], company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    rate = _owned_currency_rate(env, parameters["rate_id"], company_id, failure_type)
    result = _deleted_result(_currency_rate_result(rate, company_id))
    rate.unlink()
    if _scoped(env, "res.currency.rate", company_id).search_count([
        ("id", "=", parameters["rate_id"]),
    ], limit=1):
        raise _fail(failure_type, "odoo_write_error", "Native currency-rate deletion did not remove the selected rate.", exit_code=6)
    return result, False


def _account_group(
    env: Any,
    account_group_id: int,
    company_id: int,
    failure_type: type[Exception],
) -> Any:
    root_company_id = _root_company_id(env, company_id, failure_type)
    return _search_one(
        env,
        "account.group",
        [("id", "=", account_group_id), ("company_id", "=", root_company_id)],
        company_id,
        failure_type,
    )


def _account_group_matches(group: Any, values: dict[str, Any]) -> bool:
    return all(getattr(group, field) == value for field, value in values.items())


def _write_account_group(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    root_company_id = _root_company_id(env, company_id, failure_type)
    if capability_id == "account.group.create":
        existing = _scoped(env, "account.group", company_id).search(
            [
                ("company_id", "=", root_company_id),
                ("code_prefix_start", "=", parameters["code_prefix_start"]),
                ("code_prefix_end", "=", parameters["code_prefix_end"]),
            ],
            limit=2,
        )
        if existing:
            if len(existing) == 1 and _account_group_matches(existing, parameters):
                return _config_result(existing, "account.group", company_id), True
            raise _fail(
                failure_type,
                "idempotency_conflict",
                "The account-group prefix range already has other configuration.",
                exit_code=5,
            )
        values = {**parameters, "company_id": root_company_id}
        group = _scoped(env, "account.group", company_id).create(values)
        if (
            _many2one_id(group.company_id) != root_company_id
            or not _account_group_matches(group, parameters)
        ):
            raise _fail(
                failure_type,
                "odoo_write_error",
                "Odoo did not create the requested account group.",
                exit_code=6,
            )
        return _config_result(group, "account.group", company_id), False

    group = _account_group(
        env, parameters["account_group_id"], company_id, failure_type
    )
    changes = parameters["changes"]
    start = changes.get("code_prefix_start", group.code_prefix_start)
    end = changes.get("code_prefix_end", group.code_prefix_end)
    if len(start) != len(end) or start > end:
        raise _fail(
            failure_type,
            "state_conflict",
            "The updated account-group prefix range is invalid.",
            exit_code=5,
        )
    if _account_group_matches(group, changes):
        return _config_result(group, "account.group", company_id), True
    group.write(changes)
    group.invalidate_recordset(list(changes))
    if not _account_group_matches(group, changes):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not update the requested account group.",
            exit_code=6,
        )
    return _config_result(group, "account.group", company_id), False


def _tax_repartition_line_values(
    line: dict[str, Any], *, document_type: str
) -> dict[str, Any]:
    return {
        "document_type": document_type,
        "sequence": line["sequence"],
        "repartition_type": line["repartition_type"],
        "factor_percent": Decimal(line["factor_percent"]),
        "account_id": line["account_id"] or False,
        "tag_ids": [(6, 0, line["tag_ids"])],
        "use_in_tax_closing": line["use_in_tax_closing"],
    }


def _tax_repartition_commands(
    invoice_lines: list[dict[str, Any]], refund_lines: list[dict[str, Any]]
) -> list[tuple[Any, ...]]:
    return [
        (5, 0, 0),
        *[
            (0, 0, _tax_repartition_line_values(line, document_type="invoice"))
            for line in invoice_lines
        ],
        *[
            (0, 0, _tax_repartition_line_values(line, document_type="refund"))
            for line in refund_lines
        ],
    ]


def _normalized_tax_repartition_line(line: Any) -> dict[str, Any]:
    return {
        "sequence": int(line.sequence),
        "repartition_type": str(line.repartition_type),
        "factor_percent": _canonical_decimal_text(line.factor_percent),
        "account_id": _many2one_id(line.account_id),
        "tag_ids": _record_ids(line.tag_ids),
        "use_in_tax_closing": bool(line.use_in_tax_closing),
    }


def _tax_repartition_lines_match(
    records: Any, expected: list[dict[str, Any]]
) -> bool:
    if len(records) != len(expected):
        return False
    current = [_normalized_tax_repartition_line(line) for line in records]
    order_key = lambda item: (
        item["sequence"],
        item["repartition_type"],
        item["factor_percent"],
        item["account_id"] or 0,
        item["tag_ids"],
        item["use_in_tax_closing"],
    )
    return sorted(current, key=order_key) == sorted(expected, key=order_key)


def _tax_repartition_result(tax: Any, company_id: int) -> dict[str, Any]:
    result = _config_result(tax, "account.tax", company_id)
    result["line_ids"] = sorted(
        set(_record_ids(tax.invoice_repartition_line_ids))
        | set(_record_ids(tax.refund_repartition_line_ids))
    )
    return result


def _validate_tax_repartition_references(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> None:
    lines = parameters["invoice_lines"] + parameters["refund_lines"]
    _ensure_ids(
        env,
        "account.account",
        {line["account_id"] for line in lines if line["account_id"] is not None},
        [("company_ids", "in", [company_id]), ("active", "=", True)],
        company_id,
        failure_type,
    )
    _ensure_ids(
        env,
        "account.account.tag",
        {tag_id for line in lines for tag_id in line["tag_ids"]},
        [],
        company_id,
        failure_type,
    )


def _account_processing_values(account: Any) -> dict[str, Any]:
    values = {field: getattr(account, field) for field in account_processing.COPY_FIELDS}
    values["currency_id"] = _relation_id(values["currency_id"])
    for field in ("tax_ids", "tag_ids"):
        values[field] = _record_ids(values[field])
    for field in ("description", "note"):
        values[field] = values[field] or None
    return values


def _journal_processing_values(journal: Any) -> dict[str, Any]:
    values = {field: getattr(journal, field) for field in journal_processing.COPY_FIELDS}
    for field in journal_processing.RELATION_FIELDS:
        values[field] = _relation_id(values[field])
    return values


def _company_processing_values(company: Any) -> dict[str, Any]:
    values = {field: getattr(company, field) for field in company_processing.SETTING_FIELDS}
    for field in company_processing.RELATION_MODELS:
        values[field] = values[field].id or None
    values["quick_edit_mode"] = values["quick_edit_mode"] or None
    return values


def _write_company_processing(
    env: Any, capability_id: str, parameters: dict[str, Any],
    company_id: int, failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    with env.cr.savepoint():
        company = _search_one(env, "res.company", [("id", "=", company_id)], company_id, failure_type)
        changes = parameters["changes"]
        if capability_id == "company.fiscal_year_end.update" and company.parent_id:
            raise _fail(failure_type, "company_unavailable", "Fiscal year-end is root-delegated; target its root company explicitly.", exit_code=3)
        if capability_id == "company.cash_basis_configuration.update" and "tax_exigibility" in changes and company.parent_id:
            raise _fail(failure_type, "company_unavailable", "Cash-basis activation is root-delegated; target its root company explicitly.", exit_code=3)
        for field, value in changes.items():
            model = company_processing.RELATION_MODELS.get(field)
            if model and value is not None:
                domain = [("company_ids", "in", [company_id])] if model == "account.account" else [("company_id", "=", company_id)]
                if capability_id in {
                    "company.default_accounts.assign", "company.bank_defaults.assign",
                    "company.discount_allocation_accounts.assign",
                }:
                    domain = [("company_ids", "parent_of", [company_id])]
                    if capability_id == "company.default_accounts.assign":
                        domain.append(("account_type", "not in", [
                            "asset_receivable", "liability_payable", "asset_cash",
                            "liability_credit_card", "off_balance",
                        ]))
                    elif capability_id == "company.bank_defaults.assign":
                        domain.append(("account_type", "in", ["asset_current", "liability_current"]))
                        if field == "transfer_account_id":
                            domain.append(("reconcile", "=", True))
                    else:
                        domain.append(("account_type", "in", ["income", "income_other", "expense", "expense_other"]))
                if capability_id == "company.cash_basis_configuration.update":
                    domain = [("company_ids" if model == "account.account" else "company_id", "parent_of", [company_id])]
                elif model == "account.journal":
                    domain.append(("type", "=", "general"))
                _ensure_ids(env, model, {value}, domain, company_id, failure_type)
        current = _company_processing_values(company)
        replay = all(current[field] == value for field, value in changes.items())
        if not replay:
            company.write({field: False if value is None else value for field, value in changes.items()})
            company.invalidate_recordset()
        if any(_company_processing_values(company)[field] != value for field, value in changes.items()):
            raise _fail(failure_type, "odoo_write_error", "Native company settings did not persist.", exit_code=6)
        return _config_result(company, "res.company", company_id), replay


def _write_analytic_processing(
    env: Any, capability_id: str, parameters: dict[str, Any],
    company_id: int, failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    with env.cr.savepoint():
        model = analytic_processing.MODELS[capability_id]
        source = _search_one(env, model, [
            ("id", "=", parameters[analytic_processing.ID_FIELDS[capability_id]]),
            ("company_id", "=", company_id),
        ], company_id, failure_type)
        if capability_id != "analytic.account.duplicate":
            result = _deleted_result(_config_result(source, model, company_id))
            source.unlink()
            if source.exists():
                raise _fail(failure_type, "odoo_write_error", "Native analytic deletion failed.", exit_code=6)
            return result, False
        expected = {**_analytic_account_values(source), "plan_id": source.plan_id.id}
        expected.pop("name")
        _ensure_ids(env, "account.analytic.plan", {expected["plan_id"]}, [], company_id, failure_type)
        partner_id = expected["partner_id"]
        _ensure_ids(env, "res.partner", {partner_id} if partner_id else set(), [("company_id", "in", [False, company_id])], company_id, failure_type)
        candidates = _scoped(env, model, company_id).search([
            ("company_id", "=", company_id), ("id", "!=", source.id), ("name", "=", parameters["name"]),
        ], limit=2)
        replay = bool(candidates)
        if candidates:
            values = {**_analytic_account_values(candidates), "plan_id": candidates.plan_id.id} if len(candidates) == 1 else {}
            values.pop("name", None)
            if len(candidates) != 1 or values != expected:
                raise _fail(failure_type, "idempotency_conflict", "The analytic-account name belongs to another configuration.", exit_code=5)
            target = candidates
        else:
            target = source.copy({"name": parameters["name"], "company_id": company_id})
            target.invalidate_recordset()
        actual = {**_analytic_account_values(target), "plan_id": target.plan_id.id}
        actual.pop("name")
        if (target.id == source.id or target.company_id.id != company_id
            or target.name != parameters["name"] or actual != expected):
            raise _fail(failure_type, "odoo_write_error", "Native analytic copy did not preserve its configuration.", exit_code=6)
        result = _config_result(target, model, company_id)
        result["source_id"] = source.id
        return result, replay


def _write_journal_processing(
    env: Any, capability_id: str, parameters: dict[str, Any],
    company_id: int, failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    with env.cr.savepoint():
        group = capability_id == "journal.group.delete"
        record = (_journal_group(env, parameters["journal_group_id"], company_id, failure_type) if group
                  else _journal_config_record(env, parameters["journal_id"], company_id, failure_type))
        model = "account.journal.group" if group else "account.journal"
        if capability_id in {"journal.delete", "journal.group.delete"}:
            result = _deleted_result(_config_result(record, model, company_id))
            record.unlink()
            if record.exists():
                raise _fail(failure_type, "odoo_write_error", "Native journal/group deletion failed.", exit_code=6)
            return result, False
        if capability_id == "journal.duplicate":
            expected = _journal_processing_values(record)
            candidates = _scoped(env, model, company_id).search([
                ("company_id", "=", company_id), ("code", "=", parameters["code"]),
            ], limit=2)
            replay = bool(candidates)
            if candidates:
                if (len(candidates) != 1 or candidates.id == record.id or candidates.name != parameters["name"]
                    or _journal_processing_values(candidates) != expected):
                    raise _fail(failure_type, "idempotency_conflict", "Journal code belongs to a different configuration.", exit_code=5)
                target = candidates
            else:
                # Native copy_data replaces caller name/code; rename its real copy
                # in the same savepoint, retaining native fresh liquidity children.
                target = record.copy({"company_id": company_id})
                target.write({"code": parameters["code"], "name": parameters["name"]})
                target.invalidate_recordset()
            if (target.id == record.id or target.company_id.id != company_id or target.code != parameters["code"]
                or target.name != parameters["name"] or _journal_processing_values(target) != expected):
                raise _fail(failure_type, "odoo_write_error", "Native journal copy did not preserve requested configuration.", exit_code=6)
            result = _config_result(target, model, company_id)
            result["source_id"] = record.id
            return result, replay
        changes = parameters.get("changes")
        if capability_id == "journal.sequence_policy.update" and "is_self_billing" in changes and record.type != "purchase":
            raise _fail(failure_type, "business_rule_error", "Self-billing sequence policy only applies to purchase journals.", exit_code=6)
        if capability_id == "journal.non_deductible_account.assign":
            account_id = parameters["account_id"]
            if account_id is not None:
                _ensure_ids(env, "account.account", {account_id}, [("company_ids", "in", [company_id]), ("active", "=", True)], company_id, failure_type)
            changes = {"non_deductible_account_id": account_id}
        if capability_id == "journal.invoice_template.assign":
            report_id = parameters["report_id"]
            record.invalidate_recordset(["available_invoice_template_pdf_report_ids"])
            if record.type != "sale" or (report_id is not None and report_id not in record.available_invoice_template_pdf_report_ids.ids):
                raise _fail(failure_type, "record_not_found", "The report is not an available customer-invoice template for this journal.", exit_code=4)
            if report_id is not None:
                _ensure_ids(env, "ir.actions.report", {report_id}, [], company_id, failure_type)
            changes = {"invoice_template_pdf_report_id": report_id}
        current = _journal_processing_values(record)
        replay = all(current[field] == value for field, value in changes.items())
        if not replay:
            record.write({field: False if value is None else value for field, value in changes.items()})
            record.invalidate_recordset()
        if any(_journal_processing_values(record)[field] != value for field, value in changes.items()):
            raise _fail(failure_type, "odoo_write_error", "Native journal update did not persist requested fields.", exit_code=6)
        return _config_result(record, model, company_id), replay


def _write_account_processing(
    env: Any, capability_id: str, parameters: dict[str, Any],
    company_id: int, failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    with env.cr.savepoint():
        group = capability_id == "account.group.delete"
        duplicate = capability_id == "account.account.duplicate"
        record = _account_group(env, parameters["account_group_id"], company_id, failure_type) if group else (
            _search_one(env, "account.account", [("id", "=", parameters["account_id"]), ("company_ids", "in", [company_id])], company_id, failure_type)
            if duplicate else _account_config_record(env, parameters["account_id"], company_id, failure_type))
        model = "account.group" if group else "account.account"
        if group or capability_id == "account.account.delete":
            result = _deleted_result(_config_result(record, model, company_id))
            record.unlink()
            if record.exists():
                raise _fail(failure_type, "odoo_write_error", "Native account/group deletion failed.", exit_code=6)
            return result, False
        if duplicate:
            expected = _account_processing_values(record)
            candidates = _scoped(env, model, company_id).search([
                ("code", "=", parameters["code"]), ("company_ids", "in", [company_id]),
            ], limit=2)
            replay = bool(candidates)
            if candidates:
                if (len(candidates) != 1 or candidates.id == record.id or not _account_is_single_company(env, candidates.id, company_id)
                    or candidates.name != parameters["name"] or _account_processing_values(candidates) != expected):
                    raise _fail(failure_type, "idempotency_conflict", "The account code already belongs to a different configuration.", exit_code=5)
                target = candidates
            else:
                target = record.copy({"code": parameters["code"], "name": parameters["name"],
                                      "company_ids": [(6, 0, [company_id])], "code_mapping_ids": []})
            if (target.id == record.id or not _account_is_single_company(env, target.id, company_id) or target.code != parameters["code"]
                or target.name != parameters["name"] or _account_processing_values(target) != expected):
                raise _fail(failure_type, "odoo_write_error", "Native account copy did not preserve isolated configuration.", exit_code=6)
            result = _config_result(target, model, company_id)
            result["source_id"] = record.id
            return result, replay
        changes = parameters["changes"] if "changes" in parameters else {
            field: parameters[field] for field in ("tax_ids", "tag_ids", "non_trade") if field in parameters}
        if "tax_ids" in changes:
            _ensure_ids(env, "account.tax", set(changes["tax_ids"]), [("company_id", "=", company_id), ("active", "=", True)], company_id, failure_type)
        if "tag_ids" in changes:
            _ensure_ids(env, "account.account.tag", set(changes["tag_ids"]), [("applicability", "=", "accounts"), ("active", "=", True)], company_id, failure_type)
        current = _account_processing_values(record)
        replay = all(current[field] == value for field, value in changes.items())
        if not replay:
            record.write({field: [(6, 0, value)] if field in {"tax_ids", "tag_ids"} else False if value is None else value for field, value in changes.items()})
            record.invalidate_recordset()
        actual = _account_processing_values(record)
        if any(actual[field] != value for field, value in changes.items()):
            raise _fail(failure_type, "odoo_write_error", "Native account update did not preserve requested fields.", exit_code=6)
        return _config_result(record, model, company_id), replay


def _write_tax_processing(
    env: Any, capability_id: str, parameters: dict[str, Any],
    company_id: int, failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    with env.cr.savepoint():
        tax = _tax_config_record(env, parameters["tax_id"], company_id, failure_type)
        if capability_id == "tax.delete":
            result = _deleted_result(_tax_repartition_result(tax, company_id))
            result["line_ids"] = []
            tax.unlink()
            if tax.exists():
                raise _fail(failure_type, "odoo_write_error", "Native tax deletion failed.", exit_code=6)
            return result, False
        sides = {kind: getattr(tax, f"{kind}_repartition_line_ids").sorted(lambda row: (row.sequence, row.id)) for kind in ("invoice", "refund")}
        commands, expected, source_id, replay = [], {}, None, False
        if capability_id == "tax.repartition_pair.create":
            payloads = {kind: parameters[f"{kind}_line"] for kind in sides}
            matches = {kind: rows.filtered(lambda row, kind=kind: _normalized_tax_repartition_line(row) == payloads[kind]) for kind, rows in sides.items()}
            if any(len(rows) > 1 for rows in matches.values()) or bool(matches["invoice"]) != bool(matches["refund"]):
                raise _fail(failure_type, "idempotency_conflict", "The native tax pair payload is ambiguous or only partially present.", exit_code=5)
            if matches["invoice"]:
                if sides["invoice"].ids.index(matches["invoice"].id) != sides["refund"].ids.index(matches["refund"].id):
                    raise _fail(failure_type, "idempotency_conflict", "Matching native lines are not one ordered invoice/refund pair.", exit_code=5)
                return _tax_repartition_result(tax, company_id), True
            before = set(tax.repartition_line_ids.ids)
            for kind, payload in payloads.items():
                commands.append((0, 0, _tax_repartition_line_values(payload, document_type=kind)))
        elif capability_id == "tax.repartition_lines.resequence":
            for kind, rows in sides.items():
                order = parameters[f"{kind}_line_ids"]
                if set(order) != set(rows.ids):
                    raise _fail(failure_type, "record_not_found", "Ordering requires the complete native side's line IDs.", exit_code=4)
                for index, row_id in enumerate(order, 1):
                    expected[row_id] = {"sequence": index * 10}
                    commands.append((1, row_id, expected[row_id]))
        else:
            remove = capability_id == "tax.repartition_pair.delete"
            patches = [{"line_id": parameters[f"{kind}_line_id"], "kind": kind} for kind in sides] if remove else parameters["lines"] if capability_id == "tax.repartition_lines.update" else [
                {"line_id": parameters["line_id"], "changes": parameters["changes"]},
            ]
            for patch in patches:
                row = _search_one(env, "account.tax.repartition.line", [("id", "=", patch["line_id"]), ("tax_id", "=", tax.id)], company_id, failure_type)
                if remove:
                    if row.document_type != patch["kind"]:
                        raise _fail(failure_type, "record_not_found", "The native line belongs to the wrong document side.", exit_code=4)
                    commands.append((2, row.id, 0))
                else:
                    merged = tax_processing.line_values({**_normalized_tax_repartition_line(row), **patch["changes"]})
                    values = _tax_repartition_line_values(merged, document_type=row.document_type)
                    expected[row.id] = patch["changes"]
                    commands.append((1, row.id, {field: value for field, value in values.items() if field in patch["changes"]}))
            if capability_id == "tax.repartition_line.update":
                source_id = parameters["line_id"]
        payloads = [command[2] for command in commands if command[0] in (0, 1)]
        account_ids = {values["account_id"] for values in payloads if values.get("account_id")}
        tag_ids = {tag_id for values in payloads for command in values.get("tag_ids", []) for tag_id in command[2]}
        _ensure_ids(env, "account.account", account_ids,
                    [("company_ids", "in", [company_id]), ("active", "=", True), ("account_type", "not in", ["asset_receivable", "liability_payable", "off_balance"])],
                    company_id, failure_type)
        countries = [False, _relation_id(tax.country_id), *env.company.multi_vat_foreign_country_ids.ids]
        _ensure_ids(env, "account.account.tag", tag_ids, [("applicability", "=", "taxes"), ("country_id", "in", countries)], company_id, failure_type)
        if expected:
            current = {row.id: _normalized_tax_repartition_line(row) for rows in sides.values() for row in rows}
            replay = all(all(current[row_id][field] == value for field, value in values.items()) for row_id, values in expected.items())
        if not replay:
            # Native parent validation checks both document sides only after all commands.
            tax.write({"repartition_line_ids": commands})
            tax.invalidate_recordset()
        if capability_id == "tax.repartition_pair.create":
            created = tax.repartition_line_ids.filtered(lambda row: row.id not in before)
            if (len(created) != 2 or {row.document_type for row in created} != {"invoice", "refund"}
                or any(_normalized_tax_repartition_line(row) != parameters[f"{row.document_type}_line"] for row in created)):
                raise _fail(failure_type, "odoo_write_error", "Native tax pair creation did not preserve its payload.", exit_code=6)
        elif capability_id == "tax.repartition_pair.delete":
            if {parameters["invoice_line_id"], parameters["refund_line_id"]} & set(tax.repartition_line_ids.ids):
                raise _fail(failure_type, "odoo_write_error", "Native tax pair deletion failed.", exit_code=6)
        else:
            current = {row.id: _normalized_tax_repartition_line(row) for row in tax.repartition_line_ids}
            if any(row_id not in current or any(current[row_id][field] != value for field, value in values.items()) for row_id, values in expected.items()):
                raise _fail(failure_type, "odoo_write_error", "Native tax line changes did not preserve requested fields.", exit_code=6)
        result = _tax_repartition_result(tax, company_id)
        result["source_id"] = source_id
        return result, replay


def _replace_tax_repartition_lines(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    tax = _tax_config_record(env, parameters["tax_id"], company_id, failure_type)
    _validate_tax_repartition_references(env, parameters, company_id, failure_type)
    invoice_lines = parameters["invoice_lines"]
    refund_lines = parameters["refund_lines"]
    if _tax_repartition_lines_match(
        tax.invoice_repartition_line_ids, invoice_lines
    ) and _tax_repartition_lines_match(tax.refund_repartition_line_ids, refund_lines):
        return _tax_repartition_result(tax, company_id), True
    tax.write(
        {
            "repartition_line_ids": _tax_repartition_commands(
                invoice_lines, refund_lines
            ),
        }
    )
    tax.invalidate_recordset(
        [
            "repartition_line_ids",
            "invoice_repartition_line_ids",
            "refund_repartition_line_ids",
        ]
    )
    if not _tax_repartition_lines_match(
        tax.invoice_repartition_line_ids, invoice_lines
    ) or not _tax_repartition_lines_match(tax.refund_repartition_line_ids, refund_lines):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not replace the requested tax repartition lines.",
            exit_code=6,
        )
    return _tax_repartition_result(tax, company_id), False


def _reconciliation_model(
    env: Any,
    reconciliation_model_id: int,
    company_id: int,
    failure_type: type[Exception],
) -> Any:
    return _search_one(
        env,
        "account.reconcile.model",
        [
            ("id", "=", reconciliation_model_id),
            ("company_id", "=", company_id),
        ],
        company_id,
        failure_type,
    )


def _normalized_match_amount(model: Any) -> dict[str, Any] | None:
    if not model.match_amount:
        return None
    return {
        "operator": model.match_amount,
        "minimum": (
            _canonical_decimal_text(model.match_amount_min)
            if model.match_amount in {"greater", "between"}
            else None
        ),
        "maximum": (
            _canonical_decimal_text(model.match_amount_max)
            if model.match_amount in {"lower", "between"}
            else None
        ),
    }


def _normalized_match_label(model: Any) -> dict[str, Any] | None:
    if not model.match_label:
        return None
    return {"operator": model.match_label, "value": str(model.match_label_param)}


def _reconciliation_model_matches(model: Any, expected: dict[str, Any]) -> bool:
    current = {
        "name": model.name,
        "sequence": model.sequence,
        "trigger": model.trigger,
        "match_journal_ids": _record_ids(model.match_journal_ids),
        "match_partner_ids": _record_ids(model.match_partner_ids),
        "match_amount": _normalized_match_amount(model),
        "match_label": _normalized_match_label(model),
    }
    return all(current[field] == value for field, value in expected.items())


def _validate_reconciliation_model_references(
    env: Any,
    values: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> None:
    _ensure_ids(
        env,
        "account.journal",
        set(values.get("match_journal_ids", [])),
        [("company_id", "=", company_id), ("type", "in", ["bank", "cash", "credit"])],
        company_id,
        failure_type,
    )
    _ensure_ids(
        env,
        "res.partner",
        set(values.get("match_partner_ids", [])),
        [("company_id", "in", [False, company_id])],
        company_id,
        failure_type,
    )


def _reconciliation_model_values(values: dict[str, Any]) -> dict[str, Any]:
    result = {
        field: value
        for field, value in values.items()
        if field not in {"match_amount", "match_label"}
    }
    for field in ("match_journal_ids", "match_partner_ids"):
        if field in result:
            result[field] = [(6, 0, result[field])]
    if "match_amount" in values:
        match_amount = values["match_amount"]
        result.update(
            {
                "match_amount": match_amount["operator"] if match_amount else False,
                "match_amount_min": (
                    float(Decimal(match_amount["minimum"]))
                    if match_amount and match_amount["minimum"] is not None
                    else 0.0
                ),
                "match_amount_max": (
                    float(Decimal(match_amount["maximum"]))
                    if match_amount and match_amount["maximum"] is not None
                    else 0.0
                ),
            }
        )
    if "match_label" in values:
        match_label = values["match_label"]
        result.update(
            {
                "match_label": match_label["operator"] if match_label else False,
                "match_label_param": match_label["value"] if match_label else False,
            }
        )
    return result


def _reconciliation_model_result(model: Any, company_id: int) -> dict[str, Any]:
    result = _config_result(model, "account.reconcile.model", company_id)
    result["line_ids"] = _record_ids(model.line_ids)
    return result


def _write_reconciliation_model(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    create = capability_id == "reconciliation.model.create"
    values = parameters if create else parameters["changes"]
    _validate_reconciliation_model_references(env, values, company_id, failure_type)
    if create:
        existing = _scoped(env, "account.reconcile.model", company_id).search(
            [("company_id", "=", company_id), ("name", "=", values["name"])],
            limit=2,
        )
        if existing:
            if len(existing) == 1 and _reconciliation_model_matches(existing, values):
                return _reconciliation_model_result(existing, company_id), True
            raise _fail(
                failure_type,
                "idempotency_conflict",
                "The reconciliation-model name already has other configuration.",
                exit_code=5,
            )
        create_values = _reconciliation_model_values(values)
        create_values.update({"company_id": company_id, "active": True})
        model = _scoped(env, "account.reconcile.model", company_id).create(
            create_values
        )
        if (
            _many2one_id(model.company_id) != company_id
            or not _reconciliation_model_matches(model, values)
        ):
            raise _fail(
                failure_type,
                "odoo_write_error",
                "Odoo did not create the requested reconciliation model.",
                exit_code=6,
            )
        return _reconciliation_model_result(model, company_id), False

    model = _reconciliation_model(
        env, parameters["reconciliation_model_id"], company_id, failure_type
    )
    if _reconciliation_model_matches(model, values):
        return _reconciliation_model_result(model, company_id), True
    model.write(_reconciliation_model_values(values))
    model.invalidate_recordset(
        list(values)
        + [
            "match_amount_min",
            "match_amount_max",
            "match_label_param",
        ]
    )
    if not _reconciliation_model_matches(model, values):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not update the requested reconciliation model.",
            exit_code=6,
        )
    return _reconciliation_model_result(model, company_id), False


def _reconciliation_analytic_distribution(
    value: list[dict[str, Any]],
) -> dict[str, float] | bool:
    if not value:
        return False
    return {
        ",".join(str(account_id) for account_id in item["analytic_account_ids"]): float(
            Decimal(item["percentage"])
        )
        for item in value
    }


def _normalized_reconciliation_analytic_distribution(
    value: Any,
) -> list[dict[str, Any]]:
    if not value:
        return []
    return sorted(
        [
            {
                "analytic_account_ids": sorted(
                    int(account_id) for account_id in str(key).split(",")
                ),
                "percentage": _canonical_decimal_text(percentage),
            }
            for key, percentage in value.items()
        ],
        key=lambda item: item["analytic_account_ids"],
    )


def _normalized_reconciliation_line(line: Any) -> dict[str, Any]:
    result = {
        "sequence": int(line.sequence),
        "account_id": _many2one_id(line.account_id),
        "partner_id": _many2one_id(line.partner_id),
        "label": str(line.label) if line.label else None,
        "amount_type": str(line.amount_type),
        "amount_string": str(line.amount_string),
        "tax_ids": _record_ids(line.tax_ids),
    }
    distribution = _normalized_reconciliation_analytic_distribution(
        line.analytic_distribution
    )
    if distribution:
        result["analytic_distribution"] = distribution
    return result


def _expected_reconciliation_line(line: dict[str, Any]) -> dict[str, Any]:
    result = dict(line)
    if line.get("analytic_distribution"):
        result["analytic_distribution"] = sorted(
            line["analytic_distribution"],
            key=lambda item: item["analytic_account_ids"],
        )
    else:
        result.pop("analytic_distribution", None)
    return result


def _reconciliation_lines_match(
    records: Any, expected: list[dict[str, Any]]
) -> bool:
    if len(records) != len(expected):
        return False
    current = [_normalized_reconciliation_line(line) for line in records]
    normalized_expected = [_expected_reconciliation_line(line) for line in expected]
    order_key = lambda item: (
        item["sequence"],
        item["account_id"] or 0,
        item["partner_id"] or 0,
        item["label"] or "",
        item["amount_type"],
        item["amount_string"],
        item["tax_ids"],
    )
    return sorted(current, key=order_key) == sorted(normalized_expected, key=order_key)


def _validate_reconciliation_line_references(
    env: Any,
    lines: list[dict[str, Any]],
    company_id: int,
    failure_type: type[Exception],
) -> None:
    _ensure_ids(
        env,
        "account.account",
        {line["account_id"] for line in lines if line["account_id"] is not None},
        [
            ("company_ids", "in", [company_id]),
            ("account_type", "!=", "off_balance"),
            ("active", "=", True),
        ],
        company_id,
        failure_type,
    )
    _ensure_ids(
        env,
        "res.partner",
        {line["partner_id"] for line in lines if line["partner_id"] is not None},
        [("company_id", "in", [False, company_id])],
        company_id,
        failure_type,
    )
    _ensure_ids(
        env,
        "account.tax",
        {tax_id for line in lines for tax_id in line["tax_ids"]},
        [("company_id", "=", company_id), ("active", "=", True)],
        company_id,
        failure_type,
    )
    _ensure_ids(
        env,
        "account.analytic.account",
        {
            account_id
            for line in lines
            for item in line.get("analytic_distribution", [])
            for account_id in item["analytic_account_ids"]
        },
        [("company_id", "in", [False, company_id])],
        company_id,
        failure_type,
    )


def _reconciliation_line_commands(
    lines: list[dict[str, Any]],
) -> list[tuple[Any, ...]]:
    commands: list[tuple[Any, ...]] = [(5, 0, 0)]
    for line in lines:
        values = {
            "sequence": line["sequence"],
            "account_id": line["account_id"] or False,
            "partner_id": line["partner_id"] or False,
            "label": line["label"] if line["label"] is not None else False,
            "amount_type": line["amount_type"],
            "amount_string": line["amount_string"],
            "tax_ids": [(6, 0, line["tax_ids"])],
        }
        if "analytic_distribution" in line:
            values["analytic_distribution"] = _reconciliation_analytic_distribution(
                line["analytic_distribution"]
            )
        commands.append((0, 0, values))
    return commands


def _replace_reconciliation_model_lines(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    model = _reconciliation_model(
        env, parameters["reconciliation_model_id"], company_id, failure_type
    )
    lines = parameters["lines"]
    _validate_reconciliation_line_references(
        env, lines, company_id, failure_type
    )
    if _reconciliation_lines_match(model.line_ids, lines):
        return _reconciliation_model_result(model, company_id), True
    model.write({"line_ids": _reconciliation_line_commands(lines)})
    model.invalidate_recordset(["line_ids"])
    if not _reconciliation_lines_match(model.line_ids, lines):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not replace the reconciliation-model lines.",
            exit_code=6,
        )
    return _reconciliation_model_result(model, company_id), False


def _transition_reconciliation_model(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    model = _reconciliation_model(
        env, parameters["reconciliation_model_id"], company_id, failure_type
    )
    target_active = capability_id == "reconciliation.model.restore"
    if bool(model.active) == target_active:
        return _reconciliation_model_result(model, company_id), True
    model.write({"active": target_active})
    model.invalidate_recordset(["active"])
    if bool(model.active) != target_active:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not change the reconciliation-model archive state.",
            exit_code=6,
        )
    return _reconciliation_model_result(model, company_id), False


def _reference_result(record: Any, model: str, company_id: int, *, active: bool = True) -> dict[str, Any]:
    result = _config_result(record, model, company_id)
    result["state"] = "active" if active else "archived"
    return result


def _account_tag_values(tag: Any) -> dict[str, Any]:
    return {"name": tag.name, "applicability": tag.applicability, "color": tag.color, "country_id": _many2one_id(tag.country_id)}


def _write_account_tag(env: Any, capability_id: str, parameters: dict[str, Any], company_id: int, failure_type: type[Exception]) -> tuple[dict[str, Any], bool]:
    company = _search_one(env, "res.company", [("id", "=", company_id)], company_id, failure_type)
    company_country = _many2one_id(getattr(company, "account_fiscal_country_id", False)) or _many2one_id(getattr(company, "country_id", False))
    create = capability_id == "account.tag.create"
    if create:
        values = parameters
        if values["applicability"] == "taxes" and values["country_id"] != company_country:
            raise _fail(failure_type, "record_not_found", "The tax-tag country is unavailable in the company.", exit_code=4)
        model = _scoped(env, "account.account.tag", company_id)
        country = values["country_id"] or False
        existing = model.search([("name", "=", values["name"]), ("applicability", "=", values["applicability"]), ("country_id", "=", country)], limit=2)
        if existing:
            if (
                len(existing) == 1
                and bool(existing.active)
                and _account_tag_values(existing) == values
            ):
                return _reference_result(existing, "account.account.tag", company_id, active=bool(existing.active)), True
            raise _fail(failure_type, "state_conflict", "A different account tag already uses this natural key.", exit_code=5)
        tag = model.create({**values, "country_id": country, "active": True})
        if _account_tag_values(tag) != values or not tag.active:
            raise _fail(failure_type, "odoo_write_error", "Odoo did not create the requested account tag.", exit_code=6)
        return _reference_result(tag, "account.account.tag", company_id), False
    tag = _search_one(env, "account.account.tag", [("id", "=", parameters["account_tag_id"])], company_id, failure_type)
    tag_country_id = _many2one_id(tag.country_id)
    if (
        tag.applicability == "taxes" and tag_country_id != company_country
    ) or (tag.applicability != "taxes" and tag_country_id is not None):
        raise _fail(failure_type, "record_not_found", "The account tag is unavailable in the company country.", exit_code=4)
    if capability_id in {"account.tag.archive", "account.tag.restore"}:
        target = capability_id.endswith("restore")
        if bool(tag.active) == target:
            return _reference_result(tag, "account.account.tag", company_id, active=target), True
        tag.write({"active": target}); tag.invalidate_recordset(["active"])
        if bool(tag.active) != target:
            raise _fail(failure_type, "odoo_write_error", "Odoo did not change the account-tag archive state.", exit_code=6)
        return _reference_result(tag, "account.account.tag", company_id, active=target), False
    changes = parameters["changes"]
    target = {**_account_tag_values(tag), **changes}
    if target["applicability"] != "taxes" and target["country_id"] is not None:
        raise _fail(failure_type, "state_conflict", "Only tax tags may have a country.", exit_code=5)
    if target["applicability"] == "taxes" and target["country_id"] != company_country:
        raise _fail(failure_type, "record_not_found", "The tax-tag country is unavailable in the company.", exit_code=4)
    if _account_tag_values(tag) == target:
        return _reference_result(tag, "account.account.tag", company_id, active=bool(tag.active)), True
    write_values = {key: (False if value is None else value) for key, value in changes.items()}
    tag.write(write_values); tag.invalidate_recordset(list(changes))
    if _account_tag_values(tag) != target:
        raise _fail(failure_type, "odoo_write_error", "Odoo did not update the account tag.", exit_code=6)
    return _reference_result(tag, "account.account.tag", company_id, active=bool(tag.active)), False


def _tax_group_values(group: Any, account_fields: set[str] | frozenset[str] = frozenset()) -> dict[str, Any]:
    return {"name": group.name, "sequence": group.sequence, "preceding_subtotal": group.preceding_subtotal or None,
            **{field: _many2one_id(getattr(group, field)) for field in account_fields}}


def _write_tax_group(env: Any, capability_id: str, parameters: dict[str, Any], company_id: int, failure_type: type[Exception]) -> tuple[dict[str, Any], bool]:
    create = capability_id == "tax.group.create"
    values = parameters if create else parameters["changes"]
    account_fields = set(values) & _TAX_GROUP_ACCOUNT_FIELDS
    _ensure_ids(env, "account.account", {values[field] for field in account_fields if values[field] is not None},
                [("company_ids", "parent_of", [company_id])], company_id, failure_type)
    company = _search_one(env, "res.company", [("id", "=", company_id)], company_id, failure_type)
    country_id = _many2one_id(getattr(company, "account_fiscal_country_id", False)) or _many2one_id(getattr(company, "country_id", False))
    if create:
        model = _scoped(env, "account.tax.group", company_id)
        existing = model.search([("company_id", "=", company_id), ("name", "=", values["name"])], limit=2)
        if existing:
            if (
                len(existing) == 1
                and _many2one_id(existing.company_id) == company_id
                and _many2one_id(existing.country_id) == country_id
                and _tax_group_values(existing, account_fields) == values
            ):
                return _reference_result(existing, "account.tax.group", company_id), True
            raise _fail(failure_type, "state_conflict", "A different tax group already uses this company and name.", exit_code=5)
        group = model.create({**{field: False if value is None else value for field, value in values.items()}, "company_id": company_id, "country_id": country_id or False})
        if _many2one_id(group.company_id) != company_id or _many2one_id(group.country_id) != country_id or _tax_group_values(group, account_fields) != values:
            raise _fail(failure_type, "odoo_write_error", "Odoo did not create the requested tax group.", exit_code=6)
        return _reference_result(group, "account.tax.group", company_id), False
    group = _search_one(env, "account.tax.group", [("id", "=", parameters["tax_group_id"]), ("company_id", "=", company_id)], company_id, failure_type)
    if _many2one_id(group.company_id) != company_id or _many2one_id(group.country_id) != country_id:
        raise _fail(failure_type, "record_not_found", "The tax group is unavailable in the company country.", exit_code=4)
    target = {**_tax_group_values(group, account_fields), **values}
    if _tax_group_values(group, account_fields) == target:
        return _reference_result(group, "account.tax.group", company_id), True
    group.write({key: (False if value is None else value) for key, value in values.items()}); group.invalidate_recordset(list(values))
    if _many2one_id(group.company_id) != company_id or _many2one_id(group.country_id) != country_id or _tax_group_values(group, account_fields) != target:
        raise _fail(failure_type, "odoo_write_error", "Odoo did not update the tax group.", exit_code=6)
    return _reference_result(group, "account.tax.group", company_id), False


def _cash_rounding_values(rounding: Any) -> dict[str, Any]:
    return {"name": rounding.name, "rounding": _canonical_decimal_text(rounding.rounding), "strategy": rounding.strategy, "rounding_method": rounding.rounding_method, "profit_account_id": _many2one_id(rounding.profit_account_id), "loss_account_id": _many2one_id(rounding.loss_account_id)}


def _validate_cash_rounding_accounts(env: Any, values: dict[str, Any], company_id: int, failure_type: type[Exception]) -> None:
    if values["strategy"] == "add_invoice_line" and (values["profit_account_id"] is None or values["loss_account_id"] is None):
        raise _fail(failure_type, "state_conflict", "Invoice-line cash rounding requires profit and loss accounts.", exit_code=5)
    if values["strategy"] == "biggest_tax" and (values["profit_account_id"] is not None or values["loss_account_id"] is not None):
        raise _fail(failure_type, "state_conflict", "Biggest-tax cash rounding cannot retain profit or loss accounts.", exit_code=5)
    _ensure_ids(env, "account.account", {item for item in (values["profit_account_id"], values["loss_account_id"]) if item is not None}, [("company_ids", "in", [company_id]), ("account_type", "not in", ["asset_receivable", "liability_payable", "off_balance"]), ("active", "=", True)], company_id, failure_type)


def _write_cash_rounding(env: Any, capability_id: str, parameters: dict[str, Any], company_id: int, failure_type: type[Exception]) -> tuple[dict[str, Any], bool]:
    create = capability_id == "cash_rounding.create"
    values = parameters if create else parameters["changes"]
    model = _scoped(env, "account.cash.rounding", company_id)
    if create:
        _validate_cash_rounding_accounts(env, values, company_id, failure_type)
        existing = model.search([("name", "=", values["name"])], limit=2)
        if existing:
            if len(existing) == 1 and _cash_rounding_values(existing) == values:
                return _reference_result(existing, "account.cash.rounding", company_id), True
            raise _fail(failure_type, "state_conflict", "A different cash-rounding configuration already uses this name.", exit_code=5)
        write_values = {**values, "rounding": float(Decimal(values["rounding"])), "profit_account_id": values["profit_account_id"] or False, "loss_account_id": values["loss_account_id"] or False}
        rounding = model.create(write_values)
        if _cash_rounding_values(rounding) != values:
            raise _fail(failure_type, "odoo_write_error", "Odoo did not create the cash-rounding configuration.", exit_code=6)
        return _reference_result(rounding, "account.cash.rounding", company_id), False
    rounding = _search_one(env, "account.cash.rounding", [("id", "=", parameters["cash_rounding_id"])], company_id, failure_type)
    target = {**_cash_rounding_values(rounding), **values}
    _validate_cash_rounding_accounts(env, target, company_id, failure_type)
    if _cash_rounding_values(rounding) == target:
        return _reference_result(rounding, "account.cash.rounding", company_id), True
    write_values = {key: (float(Decimal(value)) if key == "rounding" else False if value is None else value) for key, value in values.items()}
    rounding.write(write_values); rounding.invalidate_recordset(list(values))
    if _cash_rounding_values(rounding) != target:
        raise _fail(failure_type, "odoo_write_error", "Odoo did not update the cash-rounding configuration.", exit_code=6)
    return _reference_result(rounding, "account.cash.rounding", company_id), False


def _top_level_company(
    env: Any, company_id: int, failure_type: type[Exception]
) -> Any:
    company = _search_one(
        env,
        "res.company",
        [("id", "=", company_id)],
        company_id,
        failure_type,
    )
    if _many2one_id(getattr(company, "parent_id", False)) is not None:
        raise _fail(
            failure_type,
            "company_unavailable",
            "Fiscal years can only be configured on a top-level company.",
            exit_code=3,
        )
    return company


def _fiscal_year_values(fiscal_year: Any) -> dict[str, Any]:
    return {
        "name": fiscal_year.name,
        "date_from": str(fiscal_year.date_from),
        "date_to": str(fiscal_year.date_to),
    }


def _validate_fiscal_year_dates(
    values: dict[str, Any], failure_type: type[Exception]
) -> None:
    if values["date_from"] > values["date_to"]:
        raise _fail(
            failure_type,
            "state_conflict",
            "The fiscal-year start date cannot be after its end date.",
            exit_code=5,
        )


def _write_fiscal_year(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    _top_level_company(env, company_id, failure_type)
    model = _scoped(env, "account.fiscal.year", company_id)
    if capability_id == "fiscal_year.create":
        _validate_fiscal_year_dates(parameters, failure_type)
        existing = model.search(
            [
                ("company_id", "=", company_id),
                ("date_from", "=", parameters["date_from"]),
                ("date_to", "=", parameters["date_to"]),
            ],
            limit=2,
        )
        if existing:
            if len(existing) == 1 and _fiscal_year_values(existing) == parameters:
                return _config_result(existing, "account.fiscal.year", company_id), True
            raise _fail(
                failure_type,
                "state_conflict",
                "A different fiscal year already uses these dates.",
                exit_code=5,
            )
        fiscal_year = model.create({**parameters, "company_id": company_id})
        fiscal_year.invalidate_recordset(["name", "date_from", "date_to", "company_id"])
        if (
            _many2one_id(fiscal_year.company_id) != company_id
            or _fiscal_year_values(fiscal_year) != parameters
        ):
            raise _fail(
                failure_type,
                "odoo_write_error",
                "Odoo did not create the requested fiscal year.",
                exit_code=6,
            )
        return _config_result(fiscal_year, "account.fiscal.year", company_id), False

    fiscal_year = _search_one(
        env,
        "account.fiscal.year",
        [("id", "=", parameters["id"]), ("company_id", "=", company_id)],
        company_id,
        failure_type,
    )
    actual = _fiscal_year_values(fiscal_year)
    target = {**actual, **parameters["changes"]}
    _validate_fiscal_year_dates(target, failure_type)
    if actual == target:
        return _config_result(fiscal_year, "account.fiscal.year", company_id), True
    fiscal_year.write(parameters["changes"])
    fiscal_year.invalidate_recordset([*parameters["changes"], "company_id"])
    if (
        _many2one_id(fiscal_year.company_id) != company_id
        or _fiscal_year_values(fiscal_year) != target
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not update the requested fiscal year.",
            exit_code=6,
        )
    return _config_result(fiscal_year, "account.fiscal.year", company_id), False


def _analytic_applicability_values(rule: Any) -> dict[str, Any]:
    return {
        "plan_id": _many2one_id(rule.analytic_plan_id),
        "business_domain": rule.business_domain,
        "applicability": rule.applicability,
        "account_prefix": rule.account_prefix or None,
        "product_category_id": _many2one_id(rule.product_categ_id),
    }


def _validate_analytic_applicability_references(
    env: Any,
    values: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> None:
    _ensure_ids(
        env,
        "account.analytic.plan",
        {values["plan_id"]},
        [("parent_id", "=", False)],
        company_id,
        failure_type,
    )
    category_id = values["product_category_id"]
    _ensure_ids(
        env,
        "product.category",
        {category_id} if category_id is not None else set(),
        [],
        company_id,
        failure_type,
    )


def _analytic_applicability_write_values(values: dict[str, Any]) -> dict[str, Any]:
    field_names = {
        "plan_id": "analytic_plan_id",
        "product_category_id": "product_categ_id",
    }
    return {
        field_names.get(key, key): False if value is None else value
        for key, value in values.items()
    }


def _write_analytic_applicability(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    model = _scoped(env, "account.analytic.applicability", company_id)
    if capability_id == "analytic.applicability.create":
        _validate_analytic_applicability_references(
            env, parameters, company_id, failure_type
        )
        existing = model.search(
            [
                ("company_id", "=", company_id),
                ("analytic_plan_id", "=", parameters["plan_id"]),
                ("business_domain", "=", parameters["business_domain"]),
                ("account_prefix", "=", parameters["account_prefix"] or False),
                (
                    "product_categ_id",
                    "=",
                    parameters["product_category_id"] or False,
                ),
            ],
            limit=2,
        )
        if existing:
            if (
                len(existing) == 1
                and _analytic_applicability_values(existing) == parameters
            ):
                return _config_result(
                    existing, "account.analytic.applicability", company_id
                ), True
            raise _fail(
                failure_type,
                "state_conflict",
                "A different applicability rule already uses this selector.",
                exit_code=5,
            )
        rule = model.create(
            {
                **_analytic_applicability_write_values(parameters),
                "company_id": company_id,
            }
        )
        rule.invalidate_recordset(
            [
                "analytic_plan_id",
                "business_domain",
                "applicability",
                "account_prefix",
                "product_categ_id",
                "company_id",
            ]
        )
        if (
            _many2one_id(rule.company_id) != company_id
            or _analytic_applicability_values(rule) != parameters
        ):
            raise _fail(
                failure_type,
                "odoo_write_error",
                "Odoo did not create the requested applicability rule.",
                exit_code=6,
            )
        return _config_result(
            rule, "account.analytic.applicability", company_id
        ), False

    rule = _search_one(
        env,
        "account.analytic.applicability",
        [("id", "=", parameters["id"]), ("company_id", "=", company_id)],
        company_id,
        failure_type,
    )
    actual = _analytic_applicability_values(rule)
    target = {**actual, **parameters["changes"]}
    _validate_analytic_applicability_references(env, target, company_id, failure_type)
    selector_conflict = model.search(
        [
            ("id", "!=", parameters["id"]),
            ("company_id", "=", company_id),
            ("analytic_plan_id", "=", target["plan_id"]),
            ("business_domain", "=", target["business_domain"]),
            ("account_prefix", "=", target["account_prefix"] or False),
            ("product_categ_id", "=", target["product_category_id"] or False),
        ],
        limit=1,
    )
    if selector_conflict:
        raise _fail(
            failure_type,
            "state_conflict",
            "Another applicability rule already uses the updated selector.",
            exit_code=5,
        )
    if actual == target:
        return _config_result(rule, "account.analytic.applicability", company_id), True
    write_values = _analytic_applicability_write_values(parameters["changes"])
    rule.write(write_values)
    rule.invalidate_recordset([*write_values, "company_id"])
    if (
        _many2one_id(rule.company_id) != company_id
        or _analytic_applicability_values(rule) != target
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not update the requested applicability rule.",
            exit_code=6,
        )
    return _config_result(rule, "account.analytic.applicability", company_id), False


def _analytic_distribution_model_values(model: Any) -> dict[str, Any]:
    distribution = getattr(model, "analytic_distribution", False)
    return {
        "sequence": model.sequence,
        "account_prefix": model.account_prefix or None,
        "partner_id": _many2one_id(model.partner_id),
        "partner_category_id": _many2one_id(model.partner_category_id),
        "product_id": _many2one_id(model.product_id),
        "product_category_id": _many2one_id(model.product_categ_id),
        "analytic_distribution": (
            _normalized_analytic_distribution(distribution)
            if distribution
            else None
        ),
    }


def _distribution_analytic_account_ids(distribution: Any) -> set[int]:
    return {
        int(account_id)
        for key in distribution or {}
        for account_id in key.split(",")
    }


def _validate_analytic_distribution_model_references(
    env: Any,
    values: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> None:
    for field_name, model_name, domain in (
        ("partner_id", "res.partner", [("company_id", "in", [False, company_id])]),
        ("partner_category_id", "res.partner.category", []),
        ("product_id", "product.product", [("company_id", "in", [False, company_id])]),
        ("product_category_id", "product.category", []),
    ):
        record_id = values[field_name]
        _ensure_ids(
            env,
            model_name,
            {record_id} if record_id is not None else set(),
            domain,
            company_id,
            failure_type,
        )

    account_ids = _distribution_analytic_account_ids(
        values["analytic_distribution"]
    )
    accounts = _ensure_ids(
        env,
        "account.analytic.account",
        account_ids,
        [("company_id", "in", [False, company_id])],
        company_id,
        failure_type,
    )
    plan_ids: set[int] = set()
    root_plan_ids: set[int] = set()
    for account in accounts:
        plan_id = _many2one_id(getattr(account, "plan_id", False))
        root_plan_id = _many2one_id(getattr(account, "root_plan_id", False))
        if plan_id is None or root_plan_id is None:
            raise _fail(
                failure_type,
                "record_not_found",
                "An analytic account has no usable analytic plan.",
                exit_code=4,
            )
        plan_ids.add(plan_id)
        root_plan_ids.add(root_plan_id)
    _ensure_ids(
        env,
        "account.analytic.plan",
        plan_ids,
        [],
        company_id,
        failure_type,
    )
    _ensure_ids(
        env,
        "account.analytic.plan",
        root_plan_ids,
        [("parent_id", "=", False)],
        company_id,
        failure_type,
    )


def _analytic_distribution_model_write_values(
    values: dict[str, Any]
) -> dict[str, Any]:
    relation_fields = {
        "partner_id",
        "partner_category_id",
        "product_id",
        "product_category_id",
    }
    result: dict[str, Any] = {}
    for key, value in values.items():
        field_name = "product_categ_id" if key == "product_category_id" else key
        if key == "analytic_distribution":
            result[field_name] = _odoo_analytic_distribution(value)
        elif key in relation_fields or key == "account_prefix":
            result[field_name] = value or False
        else:
            result[field_name] = value
    return result


def _write_analytic_distribution_model(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    odoo_model = "account.analytic.distribution.model"
    model = _scoped(env, odoo_model, company_id)
    if capability_id == "analytic.distribution_model.create":
        _validate_analytic_distribution_model_references(
            env, parameters, company_id, failure_type
        )
        candidates = model.search(
            [
                ("company_id", "=", company_id),
                ("account_prefix", "=", parameters["account_prefix"] or False),
                ("partner_id", "=", parameters["partner_id"] or False),
                (
                    "partner_category_id",
                    "=",
                    parameters["partner_category_id"] or False,
                ),
                ("product_id", "=", parameters["product_id"] or False),
                (
                    "product_categ_id",
                    "=",
                    parameters["product_category_id"] or False,
                ),
            ],
        )
        exact_matches = candidates.filtered(
            lambda candidate: _analytic_distribution_model_values(candidate)
            == parameters
        )
        if len(exact_matches) == 1:
            return _config_result(exact_matches, odoo_model, company_id), True
        if len(exact_matches) > 1:
            raise _fail(
                failure_type,
                "state_conflict",
                "Multiple distribution models match the complete requested state.",
                exit_code=5,
            )
        distribution_model = model.create(
            {
                **_analytic_distribution_model_write_values(parameters),
                "company_id": company_id,
            }
        )
        distribution_model.invalidate_recordset(
            [
                "sequence",
                "account_prefix",
                "partner_id",
                "partner_category_id",
                "product_id",
                "product_categ_id",
                "analytic_distribution",
                "company_id",
            ]
        )
        if (
            _many2one_id(distribution_model.company_id) != company_id
            or _analytic_distribution_model_values(distribution_model) != parameters
        ):
            raise _fail(
                failure_type,
                "odoo_write_error",
                "Odoo did not create the requested analytic distribution model.",
                exit_code=6,
            )
        return _config_result(distribution_model, odoo_model, company_id), False

    distribution_model = _search_one(
        env,
        odoo_model,
        [("id", "=", parameters["id"]), ("company_id", "=", company_id)],
        company_id,
        failure_type,
    )
    actual = _analytic_distribution_model_values(distribution_model)
    target = {**actual, **parameters["changes"]}
    _validate_analytic_distribution_model_references(
        env, target, company_id, failure_type
    )
    if actual == target:
        return _config_result(distribution_model, odoo_model, company_id), True
    write_values = _analytic_distribution_model_write_values(parameters["changes"])
    distribution_model.write(write_values)
    distribution_model.invalidate_recordset([*write_values, "company_id"])
    if (
        _many2one_id(distribution_model.company_id) != company_id
        or _analytic_distribution_model_values(distribution_model) != target
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not update the requested analytic distribution model.",
            exit_code=6,
        )
    return _config_result(distribution_model, odoo_model, company_id), False


def _report_budget_record(
    env: Any, budget_id: int, company_id: int, failure_type: type[Exception]
) -> Any:
    return _search_one(
        env,
        "account.report.budget",
        [("id", "=", budget_id), ("company_id", "=", company_id)],
        company_id,
        failure_type,
    )


def _report_budget_account(
    env: Any, account_id: int, company_id: int, failure_type: type[Exception]
) -> Any:
    return _search_one(
        env,
        "account.account",
        [
            ("id", "=", account_id),
            ("company_ids", "in", [company_id]),
            (
                "account_type",
                "in",
                [
                    "income",
                    "income_other",
                    "expense",
                    "expense_depreciation",
                    "expense_direct_cost",
                ],
            ),
        ],
        company_id,
        failure_type,
    )


def _report_budget_signature(budget: Any) -> list[tuple[int, str, float]]:
    return sorted(
        (item.account_id.id, str(item.date), item.amount) for item in budget.item_ids
    )


def _report_budget_result(
    budget: Any,
    company_id: int,
    *,
    item: Any = None,
    source_id: int | None = None,
    line_ids: list[int] | None = None,
) -> dict[str, Any]:
    result = _config_result(
        item if item is not None else budget,
        "account.report.budget.item" if item is not None else "account.report.budget",
        company_id,
    )
    result.update(
        state="recorded" if item is not None else "configured",
        source_id=budget.id if item is not None else source_id,
        line_ids=[]
        if item is not None
        else (sorted(budget.item_ids.ids) if line_ids is None else sorted(line_ids)),
    )
    return result


def _report_budget_item_matches(item: Any, values: dict[str, Any]) -> bool:
    return (
        item.account_id.id == values["account_id"]
        and str(item.date) == values["date"]
        and item.amount == float(values["amount"])
    )


def _write_report_budget(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    budget_model = _scoped(env, "account.report.budget", company_id)
    item_model = _scoped(env, "account.report.budget.item", company_id)
    action = capability_id.rsplit(".", 1)[-1]
    definition = capability_id.startswith("report.budget_definition.")
    if definition and action in {"create", "duplicate"}:
        source = (
            _report_budget_record(
                env, parameters["budget_definition_id"], company_id, failure_type
            )
            if action == "duplicate"
            else None
        )
        sequence = source.sequence if source is not None else parameters["sequence"]
        source_signature = (
            _report_budget_signature(source) if source is not None else None
        )
        if source is not None:
            for account_id in {item.account_id.id for item in source.item_ids}:
                _report_budget_account(env, account_id, company_id, failure_type)
        candidates = budget_model.search(
            [("company_id", "=", company_id), ("name", "=", parameters["name"])]
            + ([("id", "!=", source.id)] if source is not None else []),
            limit=2,
        )
        if candidates:
            if (
                len(candidates) != 1
                or candidates.sequence != sequence
                or (
                    source is not None
                    and _report_budget_signature(candidates)
                    != _report_budget_signature(source)
                )
            ):
                raise _fail(
                    failure_type,
                    "idempotency_conflict",
                    "The budget name conflicts with another configuration.",
                    exit_code=5,
                )
            return _report_budget_result(
                candidates,
                company_id,
                source_id=source.id if source is not None else None,
            ), True
        if source is None:
            budget = budget_model.create({**parameters, "company_id": company_id})
        else:
            budget = source.copy()
            # Native copy_data replaces the requested default name; apply it explicitly.
            budget.write({"name": parameters["name"]})
        budget.invalidate_recordset()
        if (
            not _is_id(budget.id)
            or (source is not None and budget.id == source.id)
            or budget.company_id.id != company_id
            or budget.name != parameters["name"]
            or budget.sequence != sequence
            or (
                source is not None
                and (
                    _report_budget_signature(budget) != source_signature
                    or _report_budget_signature(source) != source_signature
                    or set(budget.item_ids.ids).intersection(source.item_ids.ids)
                )
            )
        ):
            raise _fail(
                failure_type,
                "odoo_write_error",
                "Odoo returned an invalid report budget.",
                exit_code=6,
            )
        return _report_budget_result(
            budget, company_id, source_id=source.id if source is not None else None
        ), False

    if capability_id.startswith("report.budget_item.") and action != "create":
        item = _search_one(
            env,
            "account.report.budget.item",
            [
                ("id", "=", parameters["budget_item_id"]),
                ("budget_id.company_id", "=", company_id),
            ],
            company_id,
            failure_type,
        )
        budget = item.budget_id
    else:
        item = None
        budget = _report_budget_record(
            env, parameters["budget_definition_id"], company_id, failure_type
        )

    if action == "delete":
        result = _deleted_result(_report_budget_result(budget, company_id, item=item))
        record = item if item is not None else budget
        record.unlink()
        model = item_model if item is not None else budget_model
        if model.search_count([("id", "=", result["id"])], limit=1) or (
            item is None
            and result["line_ids"]
            and item_model.search_count([("id", "in", result["line_ids"])], limit=1)
        ):
            raise _fail(
                failure_type,
                "odoo_write_error",
                "Odoo did not remove the budget target and its dependent items.",
                exit_code=6,
            )
        return result, False

    if definition:
        changes = parameters["changes"]
        if all(getattr(budget, key) == value for key, value in changes.items()):
            return _report_budget_result(budget, company_id), True
        budget.write(changes)
        budget.invalidate_recordset()
        if not all(getattr(budget, key) == value for key, value in changes.items()):
            raise _fail(
                failure_type,
                "odoo_write_error",
                "Odoo did not persist the report-budget update.",
                exit_code=6,
            )
        return _report_budget_result(budget, company_id), False

    if action in {"create", "update"}:
        values = (
            {key: parameters[key] for key in ("account_id", "date", "amount")}
            if item is None
            else {
                "account_id": item.account_id.id,
                "date": str(item.date),
                "amount": _canonical_decimal_text(item.amount),
                **parameters["changes"],
            }
        )
        _report_budget_account(env, values["account_id"], company_id, failure_type)
        if item is None:
            matches = item_model.search(
                [
                    ("budget_id", "=", budget.id),
                    ("account_id", "=", values["account_id"]),
                    ("date", "=", values["date"]),
                ],
                limit=2,
            )
            if matches:
                if len(matches) != 1 or not _report_budget_item_matches(
                    matches, values
                ):
                    raise _fail(
                        failure_type,
                        "idempotency_conflict",
                        "The budget account/date slot is ambiguous or has another amount.",
                        exit_code=5,
                    )
                return _report_budget_result(budget, company_id, item=matches), True
            item = item_model.create(
                {**values, "amount": float(values["amount"]), "budget_id": budget.id}
            )
        else:
            if _report_budget_item_matches(item, values):
                return _report_budget_result(budget, company_id, item=item), True
            item.write({**values, "amount": float(values["amount"])})
        item.invalidate_recordset()
        if (
            item.budget_id.company_id.id != company_id
            or not _report_budget_item_matches(item, values)
        ):
            raise _fail(
                failure_type,
                "odoo_write_error",
                "Odoo did not persist the report-budget item.",
                exit_code=6,
            )
        return _report_budget_result(budget, company_id, item=item), False

    from odoo.tools import float_round

    _report_budget_account(env, parameters["account_id"], company_id, failure_type)
    months = report_budgets.period_months(
        parameters["date_from"], parameters["date_to"]
    )
    domain = [
        ("budget_id", "=", budget.id),
        ("account_id", "=", parameters["account_id"]),
        ("date", ">=", months[0]),
        ("date", "<=", parameters["date_to"]),
    ]
    items = item_model.search(domain)
    dates = [str(record.date) for record in items]
    if len(dates) != len(set(dates)) or not set(dates) <= {
        str(month) for month in months
    }:
        raise _fail(
            failure_type,
            "business_rule_error",
            "Native period allocation requires unambiguous month-start budget items.",
            exit_code=6,
        )
    target = float_round(
        float(parameters["total"]), precision_digits=parameters["rounding"]
    )
    current = float_round(
        sum(record.amount for record in items), precision_digits=parameters["rounding"]
    )
    if current == target:
        return _report_budget_result(
            budget, company_id, source_id=parameters["account_id"], line_ids=items.ids
        ), True
    budget._create_or_update_budget_items(
        target,
        parameters["account_id"],
        parameters["rounding"],
        parameters["date_from"],
        parameters["date_to"],
    )
    items = item_model.search(domain)
    if (
        float_round(
            sum(record.amount for record in items),
            precision_digits=parameters["rounding"],
        )
        != target
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not persist the requested period budget total.",
            exit_code=6,
        )
    return _report_budget_result(
        budget, company_id, source_id=parameters["account_id"], line_ids=items.ids
    ), False


def _fiscal_mapping_pair(line: Any) -> tuple[int, int]:
    return line.account_src_id.id, line.account_dest_id.id


def _fiscal_mapping_signature(position: Any) -> dict[str, Any]:
    fields = set(_FISCAL_POSITION_FIELDS) - {
        "name",
        "state_ids",
        "country_id",
        "country_group_id",
    }
    return {
        **{field: getattr(position, field) for field in fields},
        "active": position.active,
        "foreign_vat": position.foreign_vat,
        "country_id": _many2one_id(position.country_id),
        "country_group_id": _many2one_id(position.country_group_id),
        "state_ids": _record_ids(position.state_ids),
        "tax_ids": _record_ids(position.tax_ids),
        "accounts": sorted(_fiscal_mapping_pair(line) for line in position.account_ids),
    }


def _tax_copy_signature(tax: Any) -> dict[str, Any]:
    fields = (
        "type_tax_use",
        "tax_scope",
        "amount_type",
        "amount",
        "sequence",
        "active",
        "invoice_label",
        "description",
        "price_include_override",
        "include_base_amount",
        "is_base_affected",
        "tax_exigibility",
    )
    return {
        **{field: getattr(tax, field) for field in fields},
        "tax_group_id": tax.tax_group_id.id,
        "country_id": tax.country_id.id,
        "children_tax_ids": _record_ids(tax.children_tax_ids),
        "original_tax_ids": _record_ids(tax.original_tax_ids),
        "repartition": sorted(
            (
                line.document_type,
                line.repartition_type,
                line.factor_percent,
                _many2one_id(line.account_id) or 0,
                tuple(_record_ids(line.tag_ids)),
                line.use_in_tax_closing,
            )
            for line in tax.repartition_line_ids
        ),
    }


def _write_fiscal_mapping_batch(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    mapping_model = _scoped(env, "account.fiscal.position.account", company_id)
    action = capability_id.rsplit(".", 1)[-1]
    mapping_action = capability_id.startswith("fiscal_position.account_mapping.")
    tax_action = capability_id.startswith("tax.")
    if action == "duplicate":
        source = (
            _tax_config_record(env, parameters["tax_id"], company_id, failure_type)
            if tax_action
            else _fiscal_position(
                env, parameters["fiscal_position_id"], company_id, failure_type
            )
        )
        signature = _tax_copy_signature if tax_action else _fiscal_mapping_signature
        expected = signature(source)
        for tax_id in (
            expected["original_tax_ids"] if tax_action else expected["tax_ids"]
        ):
            _tax_config_record(env, tax_id, company_id, failure_type)
        if not tax_action:
            for pair in expected["accounts"]:
                for account_id in pair:
                    _account_config_record(env, account_id, company_id, failure_type)
        model_name = "account.tax" if tax_action else "account.fiscal.position"
        model = _scoped(env, model_name, company_id)
        copied = model.search(
            [
                ("company_id", "=", company_id),
                ("name", "=", parameters["name"]),
                ("id", "!=", source.id),
            ],
            limit=2,
        )
        replay = bool(copied)
        if copied:
            if (
                len(copied) != 1
                or signature(copied) != expected
                or (
                    tax_action
                    and (copied.fiscal_position_ids or copied.replacing_tax_ids)
                )
            ):
                raise _fail(
                    failure_type,
                    "idempotency_conflict",
                    "The copy name has another fiscal configuration.",
                    exit_code=5,
                )
        else:
            defaults: dict[str, Any] = {"name": parameters["name"]}
            if tax_action:
                # Detach inverse links: a copy must not alter existing fiscal positions or
                # the original-tax sets of taxes which replace the source.
                defaults.update(
                    fiscal_position_ids=[(5, 0, 0)], replacing_tax_ids=[(5, 0, 0)]
                )
            copied = source.copy(defaults)
            copied.invalidate_recordset()
        children = copied.repartition_line_ids if tax_action else copied.account_ids
        source_children = (
            source.repartition_line_ids if tax_action else source.account_ids
        )
        if (
            copied.id == source.id
            or copied.company_id.id != company_id
            or copied.name != parameters["name"]
            or signature(copied) != expected
            or signature(source) != expected
            or set(children.ids).intersection(source_children.ids)
            or (tax_action and (copied.fiscal_position_ids or copied.replacing_tax_ids))
        ):
            raise _fail(
                failure_type,
                "odoo_write_error",
                "Odoo did not persist an independent fiscal configuration copy.",
                exit_code=6,
            )
        result = _config_result(copied, model_name, company_id)
        result.update(source_id=source.id, line_ids=sorted(children.ids))
        return result, replay
    if capability_id == "tax.original_taxes.replace":
        tax = _tax_config_record(env, parameters["tax_id"], company_id, failure_type)
        originals = _ensure_ids(
            env,
            "account.tax",
            set(parameters["original_tax_ids"]),
            [("company_id", "=", company_id)],
            company_id,
            failure_type,
        )
        if any(
            original.type_tax_use != tax.type_tax_use or not original.is_domestic
            for original in originals
        ) or any(
            position.company_id.id != company_id for position in tax.fiscal_position_ids
        ):
            raise _fail(
                failure_type,
                "business_rule_error",
                "Original taxes must be domestic, have the same tax use, and remain company-scoped.",
                exit_code=6,
            )
        replay = _record_ids(tax.original_tax_ids) == parameters["original_tax_ids"]
        if not replay:
            tax.write({"original_tax_ids": [(6, 0, parameters["original_tax_ids"])]})
            tax.invalidate_recordset(["original_tax_ids"])
            tax.fiscal_position_ids.invalidate_recordset(["tax_map"])
        if _record_ids(tax.original_tax_ids) != parameters["original_tax_ids"]:
            raise _fail(
                failure_type,
                "odoo_write_error",
                "Odoo did not persist the original-tax set.",
                exit_code=6,
            )
        return _config_result(tax, "account.tax", company_id), replay
    if mapping_action and action != "create":
        line = _search_one(
            env,
            "account.fiscal.position.account",
            [
                ("id", "=", parameters["account_mapping_id"]),
                ("company_id", "=", company_id),
            ],
            company_id,
            failure_type,
        )
        position = line.position_id
    else:
        line = None
        position = _fiscal_position(
            env, parameters["fiscal_position_id"], company_id, failure_type
        )
    if action == "delete":
        result = (
            _config_result(line, "account.fiscal.position.account", company_id)
            if mapping_action
            else _fiscal_position_result(position, company_id)
        )
        if mapping_action:
            result["source_id"] = position.id
        result = _deleted_result(result)
        (line if mapping_action else position).unlink()
        model = (
            mapping_model
            if mapping_action
            else _scoped(env, "account.fiscal.position", company_id)
        )
        if model.search_count([("id", "=", result["id"])], limit=1) or (
            not mapping_action
            and result["line_ids"]
            and mapping_model.search_count([("id", "in", result["line_ids"])], limit=1)
        ):
            raise _fail(
                failure_type,
                "odoo_write_error",
                "Odoo did not remove the fiscal target and its mapping children.",
                exit_code=6,
            )
        return result, False
    if capability_id == "fiscal_position.taxes.replace":
        _ensure_ids(
            env,
            "account.tax",
            set(parameters["tax_ids"]),
            [("company_id", "=", company_id)],
            company_id,
            failure_type,
        )
        replay = _record_ids(position.tax_ids) == parameters["tax_ids"]
        if not replay:
            position.write({"tax_ids": [(6, 0, parameters["tax_ids"])]})
            position.invalidate_recordset(["tax_ids", "tax_map"])
        if _record_ids(position.tax_ids) != parameters["tax_ids"]:
            raise _fail(
                failure_type,
                "odoo_write_error",
                "Odoo did not persist the fiscal tax set.",
                exit_code=6,
            )
        return _fiscal_position_result(position, company_id), replay
    values = (
        parameters
        if line is None
        else {
            "source_account_id": line.account_src_id.id,
            "destination_account_id": line.account_dest_id.id,
            **parameters["changes"],
        }
    )
    pair = values["source_account_id"], values["destination_account_id"]
    if pair[0] == pair[1]:
        raise _fail(
            failure_type,
            "business_rule_error",
            "Source and destination accounts must differ.",
            exit_code=6,
        )
    for account_id in pair:
        _account_config_record(env, account_id, company_id, failure_type)
    conflicts = mapping_model.search(
        [("position_id", "=", position.id), ("account_src_id", "=", pair[0])]
        + ([("id", "!=", line.id)] if line is not None else []),
        limit=2,
    )
    if line is None and conflicts:
        if len(conflicts) != 1 or _fiscal_mapping_pair(conflicts) != pair:
            raise _fail(
                failure_type,
                "idempotency_conflict",
                "The source account has an ambiguous mapping.",
                exit_code=5,
            )
        line, replay = conflicts, True
    else:
        if conflicts:
            raise _fail(
                failure_type,
                "idempotency_conflict",
                "The source account already has another mapping.",
                exit_code=5,
            )
        replay = line is not None and _fiscal_mapping_pair(line) == pair
        write_values = {"account_src_id": pair[0], "account_dest_id": pair[1]}
        if line is None:
            line = mapping_model.create({**write_values, "position_id": position.id})
        elif not replay:
            line.write(write_values)
        line.invalidate_recordset()
    if (
        line.company_id.id != company_id
        or line.position_id.id != position.id
        or _fiscal_mapping_pair(line) != pair
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not persist the account mapping.",
            exit_code=6,
        )
    position.invalidate_recordset(["account_ids", "account_map"])
    result = _config_result(line, "account.fiscal.position.account", company_id)
    result.update(state="recorded", source_id=position.id)
    return result, bool(replay)


def _payment_line_config_record(env, line_id, company_id, failure_type):
    return _search_one(env, "account.payment.method.line", [
        ("id", "=", line_id), ("journal_id.company_id", "=", company_id),
    ], company_id, failure_type)


def _payment_line_signature(line):
    return {
        "journal_id": _relation_id(line.journal_id),
        "payment_method_id": _relation_id(line.payment_method_id),
        "name": line.name,
        "sequence": line.sequence,
        "payment_account_id": _relation_id(line.payment_account_id),
    }


def _validate_payment_account(env, journal, account_id, company_id, failure_type):
    if account_id is None:
        return
    account = _account_config_record(env, account_id, company_id, failure_type)
    if account.account_type not in {"asset_current", "liability_current"} and account.id != journal.default_account_id.id:
        raise _fail(failure_type, "business_rule_error", "The payment account must be a current asset/liability or the journal default account.", exit_code=6)


def _write_payment_configuration_batch(env, capability_id, parameters, company_id, failure_type):
    if capability_id.startswith("journal."):
        journal = _journal_config_record(env, parameters["journal_id"], company_id, failure_type)
        if capability_id == "journal.bank_account.assign":
            if journal.type != "bank":
                raise _fail(failure_type, "business_rule_error", "Bank-account assignment requires a bank journal.", exit_code=6)
            bank_id = parameters["partner_bank_id"]
            if bank_id is not None:
                bank = _partner_bank(env, bank_id, company_id, failure_type)
                if not bank.active or bank.partner_id.id != journal.company_id.partner_id.id:
                    raise _fail(failure_type, "business_rule_error", "The bank account must be active and belong to the journal company partner.", exit_code=6)
            values = {"bank_account_id": bank_id}
        else:
            if journal.type not in {"bank", "cash", "credit"}:
                raise _fail(failure_type, "business_rule_error", "Liquidity configuration requires a liquidity journal.", exit_code=6)
            values = parameters["changes"]
            types = {"suspense_account_id": {"asset_current"}, "profit_account_id": {"income", "income_other"}, "loss_account_id": {"expense"}}
            for field, account_id in values.items():
                account = _account_config_record(env, account_id, company_id, failure_type)
                if account.account_type not in types[field]:
                    raise _fail(failure_type, "business_rule_error", "The liquidity account has an incompatible account type.", exit_code=6)
        replay = all(_relation_id(getattr(journal, field)) == value for field, value in values.items())
        if not replay:
            journal.write({field: value if value is not None else False for field, value in values.items()})
            journal.invalidate_recordset()
        if any(_relation_id(getattr(journal, field)) != value for field, value in values.items()):
            raise _fail(failure_type, "odoo_write_error", "Odoo did not persist the journal configuration.", exit_code=6)
        return _config_result(journal, "account.journal", company_id), replay

    source = None
    if capability_id != "payment.method_line.create":
        source = _payment_line_config_record(env, parameters["payment_method_line_id"], company_id, failure_type)
        journal = source.journal_id
    else:
        journal = _journal_config_record(env, parameters["journal_id"], company_id, failure_type)
    if capability_id == "payment.method_line.remove":
        result = _config_result(source, "account.payment.method.line", company_id)
        source.unlink()
        remaining = source.exists()
        if remaining:
            remaining.invalidate_recordset()
            if remaining.journal_id:
                raise _fail(failure_type, "odoo_write_error", "Odoo did not remove the configured payment method.", exit_code=6)
        result["state"] = "detached" if remaining else "deleted"
        return result, False

    before = _payment_line_signature(source) if source is not None else None
    if capability_id == "payment.method_line.update":
        values = parameters["changes"]
        if "payment_account_id" in values:
            _validate_payment_account(env, journal, values["payment_account_id"], company_id, failure_type)
        replay = all(before[field] == value for field, value in values.items())
        if not replay:
            source.write({field: value if value is not None else False for field, value in values.items()})
            source.invalidate_recordset()
        if any(_payment_line_signature(source)[field] != value for field, value in values.items()):
            raise _fail(failure_type, "odoo_write_error", "Odoo did not update the payment method line.", exit_code=6)
        return _config_result(source, "account.payment.method.line", company_id), replay

    values = dict(parameters) if source is None else {**before, "name": parameters["name"]}
    method = _search_one(env, "account.payment.method", [("id", "=", values["payment_method_id"])], company_id, failure_type)
    if method.code not in method._get_payment_method_information() or not journal.filtered_domain(method._get_payment_method_domain(method.code)):
        raise _fail(failure_type, "business_rule_error", "The payment method is not supported by this journal.", exit_code=6)
    _validate_payment_account(env, journal, values["payment_account_id"], company_id, failure_type)
    model = _scoped(env, "account.payment.method.line", company_id)
    conflicts = model.search([(field, "=", values[field]) for field in ("journal_id", "payment_method_id", "name")], limit=2)
    replay = bool(conflicts)
    if replay:
        if len(conflicts) != 1 or _payment_line_signature(conflicts) != values or (source is not None and conflicts.id == source.id):
            raise _fail(failure_type, "idempotency_conflict", "A conflicting payment method line already exists.", exit_code=5)
        line = conflicts
    elif source is None:
        line = model.create({field: value if value is not None else False for field, value in values.items()})
    else:
        # Native payment_account_id is copy=False; retain the configured account explicitly.
        line = source.copy({"name": values["name"], "payment_account_id": values["payment_account_id"] or False})
    line.invalidate_recordset()
    if _payment_line_signature(line) != values or (source is not None and (line.id == source.id or _payment_line_signature(source) != before)):
        raise _fail(failure_type, "odoo_write_error", "Odoo did not preserve the requested payment method configuration.", exit_code=6)
    result = _config_result(line, "account.payment.method.line", company_id)
    if source is not None:
        result["source_id"] = source.id
    return result, replay


def _partner_preference_value(partner: Any, field: str) -> Any:
    value = getattr(partner, field)
    if field.endswith("_id"):
        return _relation_id(value)
    if field in {"invoice_sending_method", "invoice_edi_format"}:
        return value or None
    return value


def _write_partner_preferences_batch(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    partner = _partner(env, parameters["partner_id"], company_id, failure_type)
    company = _scoped(env, "res.company", company_id).browse(company_id)
    partner = partner.with_company(company)
    credit_action = capability_id.startswith("partner.credit_limit.")
    invoice_action = capability_id == "partner.invoice_delivery_preferences.update"
    if (credit_action or invoice_action) and partner.commercial_partner_id.id != partner.id:
        raise _fail(
            failure_type, "business_rule_error",
            "Credit limits and invoice sending defaults must target the commercial partner.",
            exit_code=6,
        )
    if credit_action:
        if capability_id.endswith(".reset"):
            expected = partner._fields["credit_limit"].get_company_dependent_fallback(partner)
            replay = not partner.use_partner_credit_limit and partner.credit_limit == expected
            if not replay:
                partner.write({"use_partner_credit_limit": False})
        else:
            expected = float(partner_preferences.credit_amount(parameters["credit_limit"]))
            replay = partner.credit_limit == expected
            if not replay:
                partner.write({"credit_limit": expected})
        partner.invalidate_recordset(["credit_limit", "use_partner_credit_limit"])
        if partner.credit_limit != expected or (capability_id.endswith(".reset") and partner.use_partner_credit_limit):
            raise _fail(failure_type, "odoo_write_error", "Odoo did not persist the requested native credit limit.", exit_code=6)
        return _partner_result(partner, company_id), replay

    changes = parameters["changes"]
    if capability_id == "partner.payment_preferences.update":
        for field, line_id in changes.items():
            if line_id is None:
                continue
            line = _payment_line_config_record(env, line_id, company_id, failure_type)
            direction = "inbound" if "inbound" in field else "outbound"
            if line.payment_type != direction or not line.journal_id.active:
                raise _fail(failure_type, "business_rule_error", "The payment preference requires an active journal and the matching payment direction.", exit_code=6)
    elif invoice_action:
        for field in ("invoice_sending_method", "invoice_edi_format"):
            if field in changes and changes[field] is not None:
                allowed = dict(partner._fields[field]._description_selection(partner.env))
                if changes[field] not in allowed:
                    raise _fail(failure_type, "business_rule_error", "The invoice preference is not an installed native selection.", exit_code=6)
        report_id = changes.get("invoice_template_pdf_report_id")
        if report_id is not None and report_id not in partner.available_invoice_template_pdf_report_ids.ids:
            raise _fail(failure_type, "record_not_found", "The requested report is not available for native invoices.", exit_code=4)
    replay = all(_partner_preference_value(partner, field) == value for field, value in changes.items())
    if not replay:
        partner.write({field: value if value is not None else False for field, value in changes.items()})
        partner.invalidate_recordset()
    if any(_partner_preference_value(partner, field) != value for field, value in changes.items()):
        raise _fail(failure_type, "odoo_write_error", "Odoo did not persist the requested partner preferences.", exit_code=6)
    return _partner_result(partner, company_id), replay


def _reconciliation_copy_values(model: Any) -> dict[str, Any]:
    return {
        "active": bool(model.active), "sequence": model.sequence, "trigger": model.trigger,
        "match_journal_ids": _record_ids(model.match_journal_ids),
        "match_partner_ids": _record_ids(model.match_partner_ids),
        "match_amount": _normalized_match_amount(model), "match_label": _normalized_match_label(model),
        "next_activity_type_id": _relation_id(model.next_activity_type_id),
        "lines": [_normalized_reconciliation_line(line) for line in model.line_ids.sorted(lambda line: (line.sequence, line.id))],
    }


def _write_reconciliation_processing(
    env: Any, capability_id: str, parameters: dict[str, Any],
    company_id: int, failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    model = _reconciliation_model(env, parameters["reconciliation_model_id"], company_id, failure_type)
    source_id = None
    replay = False
    if capability_id == "reconciliation.model.duplicate":
        expected = _reconciliation_copy_values(model)
        candidates = _scoped(env, "account.reconcile.model", company_id).search([
            ("company_id", "=", company_id), ("name", "=", parameters["name"]),
        ], limit=2)
        if candidates:
            if len(candidates) != 1 or candidates.id == model.id or _reconciliation_copy_values(candidates) != expected:
                raise _fail(failure_type, "idempotency_conflict", "The duplicate name already belongs to other reconciliation configuration.", exit_code=5)
            duplicate, replay = candidates, True
        else:
            duplicate = model.copy({"name": parameters["name"]})
            duplicate.invalidate_recordset()
        if (duplicate.id == model.id or _relation_id(duplicate.company_id) != company_id
            or duplicate.name != parameters["name"] or _reconciliation_copy_values(duplicate) != expected
            or set(duplicate.line_ids.ids) & set(model.line_ids.ids)):
            raise _fail(failure_type, "odoo_write_error", "Native reconciliation copy did not preserve the requested configuration with new rule lines.", exit_code=6)
        result = _reconciliation_model_result(duplicate, company_id)
        result["source_id"] = model.id
        return result, replay
    if capability_id == "reconciliation.model.delete":
        result = _deleted_result(_reconciliation_model_result(model, company_id))
        result["line_ids"] = []
        model.unlink()
        if _scoped(env, "account.reconcile.model", company_id).search_count([("id", "=", result["id"])], limit=1):
            raise _fail(failure_type, "odoo_write_error", "Native reconciliation model deletion failed.", exit_code=6)
        return result, False
    if capability_id == "reconciliation.model.activity_type.assign":
        target = parameters["activity_type_id"]
        if target is not None:
            _ensure_ids(env, "mail.activity.type", {target}, [
                ("active", "=", True), ("res_model", "in", [False, "account.bank.statement.line"]),
            ], company_id, failure_type)
        replay = _relation_id(model.next_activity_type_id) == target
        if not replay:
            model.write({"next_activity_type_id": target or False})
            model.invalidate_recordset()
        if _relation_id(model.next_activity_type_id) != target:
            raise _fail(failure_type, "odoo_write_error", "Native reconciliation activity assignment was not persisted.", exit_code=6)
    elif capability_id == "reconciliation.model.lines.resequence":
        ids = parameters["line_ids"]
        if set(ids) != set(model.line_ids.ids):
            raise _fail(failure_type, "business_rule_error", "Resequencing requires every native rule line exactly once.", exit_code=6)
        lines = {line.id: line for line in model.line_ids}
        replay = all(lines[line_id].sequence == index * 10 for index, line_id in enumerate(ids, 1))
        for index, line_id in enumerate(ids, 1):
            if lines[line_id].sequence != index * 10:
                lines[line_id].write({"sequence": index * 10})
        model.invalidate_recordset()
        if (model.line_ids.sorted(lambda line: (line.sequence, line.id)).ids != ids
            or any(line.sequence != index * 10 for index, line in enumerate(model.line_ids.sorted(lambda line: (line.sequence, line.id)), 1))):
            raise _fail(failure_type, "odoo_write_error", "Native rule-line resequencing failed.", exit_code=6)
    else:
        create = capability_id == "reconciliation.model.line.create"
        if not create:
            line = _search_one(env, "account.reconcile.model.line", [
                ("id", "=", parameters["line_id"]), ("model_id", "=", model.id), ("company_id", "=", company_id),
            ], company_id, failure_type)
            source_id = line.id
        if capability_id == "reconciliation.model.line.delete":
            line.unlink()
            model.invalidate_recordset()
            if source_id in model.line_ids.ids:
                raise _fail(failure_type, "odoo_write_error", "Native rule-line deletion failed.", exit_code=6)
        else:
            changes = parameters["line"] if create else parameters["changes"]
            target = changes if create else {**_normalized_reconciliation_line(line), **changes}
            try:
                reconciliation_processing.line_values(target)
            except ValueError as exc:
                raise _fail(failure_type, "business_rule_error", str(exc), exit_code=6) from exc
            references = {"account_id": None, "partner_id": None, "tax_ids": []}
            references.update({field: target[field] for field in ("account_id", "partner_id", "tax_ids", "analytic_distribution") if field in changes})
            _validate_reconciliation_line_references(env, [references], company_id, failure_type)
            expected = _expected_reconciliation_line(target)
            if create:
                matches = model.line_ids.filtered(lambda row: _normalized_reconciliation_line(row) == expected)
                if len(matches) > 1:
                    raise _fail(failure_type, "idempotency_conflict", "Multiple existing rule lines match this create payload.", exit_code=5)
                if matches:
                    line, replay = matches, True
                else:
                    values = _reconciliation_line_commands([target])[1][2]
                    line = _scoped(env, "account.reconcile.model.line", company_id).create({**values, "model_id": model.id})
                source_id = line.id
            else:
                replay = _normalized_reconciliation_line(line) == expected
                if not replay:
                    values = _reconciliation_line_commands([target])[1][2]
                    line.write({field: value for field, value in values.items() if field in changes})
            line.invalidate_recordset()
            model.invalidate_recordset()
            if _normalized_reconciliation_line(line) != expected or _relation_id(line.model_id) != model.id or _relation_id(line.company_id) != company_id:
                raise _fail(failure_type, "odoo_write_error", "Native rule-line payload was not persisted in the requested company/model.", exit_code=6)
    result = _reconciliation_model_result(model, company_id)
    result["source_id"] = source_id
    return result, replay


def _write_payment_processing(
    env: Any, capability_id: str, parameters: dict[str, Any],
    company_id: int, failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    payment = _search_one(env, "account.payment", [
        ("id", "=", parameters["payment_id"]), ("company_id", "=", company_id),
    ], company_id, failure_type)
    if capability_id == "payment.bank_account.assign":
        target = parameters["partner_bank_id"]
        if target is None and payment.require_partner_bank_account:
            raise _fail(failure_type, "business_rule_error", "This native payment method requires a bank account.", exit_code=6)
        if target is not None:
            _ensure_ids(env, "res.partner.bank", {target}, [("company_id", "in", [False, company_id]), ("active", "=", True)], company_id, failure_type)
            if target not in payment.available_partner_bank_ids.ids:
                raise _fail(failure_type, "business_rule_error", "The bank account is not a native eligible recipient/company account for this payment.", exit_code=6)
        replay = _relation_id(payment.partner_bank_id) == target
        if not replay:
            payment.write({"partner_bank_id": target or False})
            payment.invalidate_recordset()
        if _relation_id(payment.partner_bank_id) != target:
            raise _fail(failure_type, "odoo_write_error", "Native payment bank assignment was not persisted.", exit_code=6)
    elif capability_id == "payment.destination_account.assign":
        if payment.state != "draft" or payment.move_id and payment.move_id.state != "draft":
            raise _fail(failure_type, "state_conflict", "The payment and any linked entry must be draft to change its accounting destination.", exit_code=6)
        account = _search_one(env, "account.account", [
            ("id", "=", parameters["account_id"]), ("company_ids", "in", [company_id]),
            ("active", "=", True), ("reconcile", "=", True),
            ("account_type", "=", "asset_receivable" if payment.partner_type == "customer" else "liability_payable"),
        ], company_id, failure_type)
        replay = _relation_id(payment.destination_account_id) == account.id
        if not replay:
            payment.write({"destination_account_id": account.id})
            payment.invalidate_recordset()
        if _relation_id(payment.destination_account_id) != account.id:
            raise _fail(failure_type, "odoo_write_error", "Native payment destination account was not persisted.", exit_code=6)
    elif capability_id == "payment.sent_status.set":
        if payment.state != "in_process" or payment.payment_method_code != "manual":
            raise _fail(failure_type, "state_conflict", "Native sent-status actions require an in-process manual payment.", exit_code=6)
        replay = payment.is_sent == parameters["sent"]
        if not replay:
            if parameters["sent"]:
                payment.mark_as_sent()
            else:
                payment.unmark_as_sent()
            payment.invalidate_recordset()
        if payment.is_sent != parameters["sent"]:
            raise _fail(failure_type, "odoo_write_error", "Native payment sent status was not persisted.", exit_code=6)
    elif capability_id == "payment.validate":
        if payment.move_id or payment.state not in {"in_process", "paid"}:
            raise _fail(failure_type, "state_conflict", "Native manual validation requires an in-process payment without a journal entry; journal-backed payments settle by reconciliation.", exit_code=6)
        replay = payment.state == "paid"
        if not replay:
            payment.action_validate()
            payment.invalidate_recordset()
        if payment.state != "paid" or payment.move_id:
            raise _fail(failure_type, "odoo_write_error", "Native no-entry payment validation did not produce the requested state.", exit_code=6)
    else:
        replay = payment.state == "rejected"
        if not replay:
            if payment.state != "in_process" or not payment.is_sent:
                raise _fail(failure_type, "state_conflict", "Native rejection requires an in-process payment marked as sent.", exit_code=6)
            payment.action_reject()
            payment.invalidate_recordset()
        if payment.state != "rejected":
            raise _fail(failure_type, "odoo_write_error", "Native payment rejection did not produce the requested state.", exit_code=6)
    return _payment_result(payment, company_id, source_id=None), replay


def _layout_current(line: Any) -> dict[str, Any]:
    return {field: getattr(line, field) for field in invoice_presentation.LAYOUT_KEYS}


def _invoice_preparation_tax_groups(totals: Any) -> dict[int, dict[str, Any]]:
    groups = {}
    for subtotal in totals["subtotals"]:
        for group in subtotal["tax_groups"]:
            if not _is_id(group["id"]) or group["id"] in groups:
                raise ValueError("Invalid native invoice tax-group identity.")
            groups[group["id"]] = group
    return groups


def _write_invoice_preparation(
    env: Any, capability_id: str, parameters: dict[str, Any],
    company_id: int, failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    with env.cr.savepoint():
        move = _search_one(env, "account.move", [
            ("id", "=", parameters["move_id"]), ("company_id", "=", company_id),
            ("move_type", "in", list(_DOCUMENT_TYPES)),
        ], company_id, failure_type)
        if move.state != "draft":
            raise _fail(failure_type, "state_conflict", "Invoice preparation changes require a draft invoice or bill.", exit_code=6)
        if capability_id == "invoice.service_dates.update":
            changes = parameters["changes"]
            replay = all(_nullable_value(getattr(move, field)) == value for field, value in changes.items())
            if not replay:
                move.write({field: False if value is None else value for field, value in changes.items()})
                move.invalidate_recordset()
            if any(_nullable_value(getattr(move, field)) != value for field, value in changes.items()):
                raise _fail(failure_type, "odoo_write_error", "Native invoice service dates did not persist.", exit_code=6)
            return _move_result(move, company_id), replay

        totals = deepcopy(move.tax_totals)
        native_groups = _invoice_preparation_tax_groups(totals)
        targets = {group["tax_group_id"]: Decimal(group["tax_amount"]) for group in parameters["groups"]}
        if not set(targets) <= set(native_groups):
            raise _fail(failure_type, "business_rule_error", "Tax adjustment can only target this invoice's existing tax groups.", exit_code=6)
        for group in parameters["groups"]:
            if _rounded_currency_amount(move.currency_id, group["tax_amount"]) != targets[group["tax_group_id"]]:
                raise _fail(failure_type, "business_rule_error", "Tax amounts must already match the invoice currency precision.", exit_code=6)

        def matches(groups: dict[int, dict[str, Any]]) -> bool:
            return all(
                group_id in groups
                and _rounded_currency_amount(move.currency_id, str(groups[group_id]["tax_amount_currency"])) == amount
                for group_id, amount in targets.items()
            )

        replay = matches(native_groups)
        if not replay:
            for group_id, amount in targets.items():
                native_groups[group_id]["tax_amount_currency"] = float(amount)
            move.write({"tax_totals": totals})
            move.invalidate_recordset()
        if not matches(_invoice_preparation_tax_groups(move.tax_totals)):
            raise _fail(failure_type, "odoo_write_error", "Native invoice tax totals did not match the requested adjustment.", exit_code=6)
        return _move_result(move, company_id), replay


def _write_invoice_presentation(
    env: Any, capability_id: str, parameters: dict[str, Any],
    company_id: int, failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    move = _search_one(env, "account.move", [
        ("id", "=", parameters["move_id"]), ("company_id", "=", company_id),
        ("move_type", "in", sorted(invoice_presentation.INVOICE_TYPES)),
    ], company_id, failure_type)
    posted_metadata = (
        capability_id == "invoice.presentation_settings.update"
        and move.state == "posted"
        and set(parameters["changes"]) <= {"narration", "invoice_user_id"}
    )
    if move.state != "draft" and not posted_metadata:
        raise _fail(failure_type, "state_conflict", "Only draft presentation or posted narration and salesperson settings can change.", exit_code=6)
    if capability_id == "invoice.presentation_settings.update":
        changes = dict(parameters["changes"])
        shipping = changes.get("partner_shipping_id")
        if shipping is not None:
            _ensure_ids(env, "res.partner", {shipping}, [("company_id", "in", [False, company_id]), ("active", "=", True)], company_id, failure_type)
        user_id = changes.get("invoice_user_id")
        if user_id is not None:
            _ensure_ids(env, "res.users", {user_id}, [("company_ids", "in", [company_id]), ("share", "=", False), ("active", "=", True)], company_id, failure_type)
        if "narration" in changes:
            changes["narration"] = move._fields["narration"].convert_to_cache(changes["narration"] or False, move) or None
        def current(field: str) -> Any:
            value = getattr(move, field)
            return _relation_id(value) if field.endswith("_id") else value or None
        replay = all(current(field) == value for field, value in changes.items())
        if not replay:
            move.write({field: value if value is not None else False for field, value in changes.items()})
            move.invalidate_recordset()
        if any(current(field) != value for field, value in changes.items()):
            raise _fail(failure_type, "odoo_write_error", "Native presentation settings were not persisted.", exit_code=6)
        return _move_result(move, company_id), replay
    if capability_id == "invoice.fiscal_position.refresh":
        def snapshot() -> list[Any]:
            return sorted((line.id, _relation_id(line.account_id), tuple(sorted(line.tax_ids.ids)), line.price_unit, line.balance) for line in move.line_ids)
        before = snapshot()
        container = {"records": move}
        with move._check_balanced(container), move._sync_dynamic_lines(container):
            move.action_update_fpos_values()
        move.invalidate_recordset()
        return _move_result(move, company_id), before == snapshot()
    if capability_id == "invoice.lines.resequence":
        requested = parameters["line_ids"]
        if set(requested) != set(move.invoice_line_ids.ids):
            raise _fail(failure_type, "business_rule_error", "Resequencing requires exactly all invoice product and layout lines, never tax or payment-term lines.", exit_code=6)
        targets = {line_id: index * 10 for index, line_id in enumerate(requested, 1)}
        replay = all(line.sequence == targets[line.id] for line in move.invoice_line_ids)
        if not replay:
            move.write({"invoice_line_ids": [(1, line_id, {"sequence": sequence}) for line_id, sequence in targets.items()]})
            move.invalidate_recordset()
        if any(line.sequence != targets[line.id] for line in move.invoice_line_ids):
            raise _fail(failure_type, "odoo_write_error", "Native invoice-line ordering was not persisted.", exit_code=6)
        return _move_result(move, company_id), replay
    if capability_id == "invoice.layout_line.create":
        target = parameters["line"]
        matches = [line for line in move.invoice_line_ids if line.display_type in invoice_presentation.LAYOUT_TYPES and _layout_current(line) == target]
        if len(matches) > 1:
            raise _fail(failure_type, "idempotency_conflict", "Multiple layout lines match this create payload; specify a distinct sequence.", exit_code=5)
        if matches:
            return _move_result(move, company_id, source_id=matches[0].id), True
        before_ids = set(move.invoice_line_ids.ids)
        move.write({"invoice_line_ids": [(0, 0, target)]})
        created = [line for line in move.invoice_line_ids if line.id not in before_ids and line.display_type in invoice_presentation.LAYOUT_TYPES and _layout_current(line) == target]
        if len(created) != 1:
            raise _fail(failure_type, "odoo_write_error", "Native layout creation did not produce exactly one requested line.", exit_code=6)
        return _move_result(move, company_id, source_id=created[0].id), False
    line = _search_one(env, "account.move.line", [
        ("id", "=", parameters["line_id"]), ("move_id", "=", move.id),
        ("company_id", "=", company_id), ("display_type", "in", sorted(invoice_presentation.LAYOUT_TYPES)),
    ], company_id, failure_type)
    line_id = line.id
    if capability_id == "invoice.layout_line.delete":
        line.unlink()
        if _scoped(env, "account.move.line", company_id).search_count([("id", "=", line_id)], limit=1):
            raise _fail(failure_type, "odoo_write_error", "The native layout line was not deleted.", exit_code=6)
        return _move_result(move, company_id, source_id=line_id), False
    changes = parameters["changes"]
    replay = all(_layout_current(line)[field] == value for field, value in changes.items())
    if not replay:
        line.write(changes)
        line.invalidate_recordset()
    if any(_layout_current(line)[field] != value for field, value in changes.items()):
        raise _fail(failure_type, "odoo_write_error", "Native layout changes were not persisted.", exit_code=6)
    return _move_result(move, company_id, source_id=line_id), replay


def _write_move_processing(
    env: Any, capability_id: str, parameters: dict[str, Any],
    company_id: int, failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    invoice = capability_id.startswith("invoice.")
    move = _search_one(env, "account.move", [
        ("id", "=", parameters["move_id"]), ("company_id", "=", company_id),
        ("move_type", "in", sorted(move_processing.INVOICE_TYPES if invoice else move_processing.MOVE_TYPES)),
    ], company_id, failure_type)
    if capability_id == "accounting_move.review.set":
        if move.state != "posted":
            raise _fail(failure_type, "state_conflict", "Only a posted move can be reviewed.", exit_code=6)
        expected = parameters["checked"]
        replay = move.checked == expected
        if not replay:
            move.set_moves_checked(expected)
        move.invalidate_recordset(["checked"])
        if move.checked != expected:
            raise _fail(failure_type, "odoo_write_error", "Native review state was not persisted.", exit_code=6)
        return _move_result(move, company_id), replay
    if capability_id == "invoice.payment_block.set":
        expected = parameters["blocked"]
        replay = (move.payment_state == "blocked") == expected
        if not replay:
            if expected and move.payment_state in {"paid", "in_payment"}:
                raise _fail(failure_type, "business_rule_error", "A paid or in-payment invoice cannot be blocked.", exit_code=6)
            move.action_toggle_block_payment()
        move.invalidate_recordset(["payment_state"])
        if (move.payment_state == "blocked") != expected:
            raise _fail(failure_type, "odoo_write_error", "Native payment block state was not persisted.", exit_code=6)
        return _move_result(move, company_id), replay
    posted_metadata = move.state == "posted" and capability_id in {
        "invoice.payment_method.assign", "invoice.incoterm.update",
    }
    if move.state != "draft" and not posted_metadata:
        raise _fail(failure_type, "state_conflict", "Processing settings require a draft move.", exit_code=6)
    if capability_id.startswith("invoice.currency_rate."):
        expected = float(parameters["rate"]) if capability_id.endswith(".update") else move.expected_currency_rate
        if move.currency_id == move.company_id.currency_id and expected != 1:
            raise _fail(failure_type, "business_rule_error", "A same-currency document uses rate 1.", exit_code=6)
        replay = move.invoice_currency_rate == expected
        if not replay:
            if capability_id.endswith(".refresh"):
                move.refresh_invoice_currency_rate()
            else:
                move.write({"invoice_currency_rate": expected})
        move.invalidate_recordset(["invoice_currency_rate"])
        if move.invoice_currency_rate != expected:
            raise _fail(failure_type, "odoo_write_error", "Native currency rate was not persisted.", exit_code=6)
        return _move_result(move, company_id), replay
    if capability_id == "invoice.cash_rounding.assign":
        rounding_id = parameters["cash_rounding_id"]
        if rounding_id is not None:
            rounding = _search_one(env, "account.cash.rounding", [("id", "=", rounding_id)], company_id, failure_type)
            rounding = rounding.with_company(move.company_id)
            accounts = set((rounding.profit_account_id | rounding.loss_account_id).ids)
            if accounts:
                _ensure_ids(env, "account.account", accounts, [("company_ids", "in", [company_id])], company_id, failure_type)
        changes = {"invoice_cash_rounding_id": rounding_id}
    elif capability_id == "invoice.payment_method.assign":
        line_id = parameters["payment_method_line_id"]
        if line_id is not None:
            line = _payment_line_config_record(env, line_id, company_id, failure_type)
            direction = "inbound" if move.move_type.startswith("out_") else "outbound"
            if line.payment_type != direction or not line.journal_id.active:
                raise _fail(failure_type, "business_rule_error", "Invoice payment method needs a matching direction and active same-company journal.", exit_code=6)
        changes = {"preferred_payment_method_line_id": line_id}
    elif capability_id == "invoice.incoterm.update":
        changes = {"invoice_incoterm_id" if field == "incoterm_id" else field: value for field, value in parameters["changes"].items()}
        incoterm_id = changes.get("invoice_incoterm_id")
        if incoterm_id is not None:
            _ensure_ids(env, "account.incoterms", {incoterm_id}, [], company_id, failure_type)
    else:
        changes = {field: parameters[field] for field in ("auto_post", "auto_post_until")}
    def current(field: str) -> Any:
        value = getattr(move, field)
        if field.endswith("_id"):
            return _relation_id(value)
        if field == "auto_post_until":
            return value.isoformat() if value else None
        return value or None
    replay = all(current(field) == value for field, value in changes.items())
    if not replay:
        move.write({field: value if value is not None else False for field, value in changes.items()})
        move.invalidate_recordset()
    if any(current(field) != value for field, value in changes.items()):
        raise _fail(failure_type, "odoo_write_error", "Native processing settings were not persisted.", exit_code=6)
    return _move_result(move, company_id), replay


def _journal_item_current(line: Any, fields: set[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for field in fields:
        value = (
            getattr(line, field, [] if field in {"tax_ids", "tax_tag_ids"} else 0 if field == "tax_base_amount" else None)
            if field in _ENTRY_TAX_FIELDS else getattr(line, field)
        )
        if field in {"account_id", "partner_id", "product_uom_id", "currency_id", "tax_repartition_line_id"}:
            result[field] = _relation_id(value)
        elif field in {"debit", "credit", "deductible_amount", "amount_currency", "tax_base_amount"}:
            result[field] = _canonical_decimal_text(value)
        elif field in {"tax_ids", "tax_tag_ids"}:
            result[field] = _relation_ids(value)
        elif field == "analytic_distribution":
            result[field] = _normalized_analytic_distribution(value) or None
        elif field == "date_maturity":
            result[field] = _nullable_value(value)
        else:
            result[field] = value
    return result


def _journal_item_write_values(changes: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for field, value in changes.items():
        if field in {"debit", "credit", "deductible_amount", "amount_currency", "tax_base_amount"}:
            result[field] = float(Decimal(value))
        elif field in {"tax_ids", "tax_tag_ids"}:
            result[field] = [(6, 0, value)]
        elif field == "analytic_distribution":
            result[field] = _odoo_analytic_distribution(value)
        else:
            result[field] = value if value is not None else False
    return result


def _journal_item_sourced(line: Any) -> bool:
    fields = getattr(line, "_fields", {})
    return bool(
        "sale_line_ids" in fields and line.sale_line_ids
        or "purchase_line_id" in fields and line.purchase_line_id
    )


def _write_journal_item_processing(
    env: Any, capability_id: str, parameters: dict[str, Any],
    company_id: int, failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    move_domain: list[Any] = [
        ("id", "=", parameters["move_id"]), ("company_id", "=", company_id),
    ]
    invoice = capability_id.startswith("invoice.")
    if invoice:
        move_domain.append(("move_type", "in", list(_DOCUMENT_TYPES)))
    elif capability_id == "journal_entry.lines.update":
        move_domain.append(("move_type", "=", "entry"))
    move = _search_one(env, "account.move", move_domain, company_id, failure_type)
    if move.state not in {"draft", "posted"}:
        raise _fail(failure_type, "state_conflict", "Journal-item processing requires a draft or posted move.", exit_code=5)
    if (invoice or capability_id == "journal_entry.lines.update") and move.state != "draft":
        raise _fail(failure_type, "state_conflict", "Financial line changes require a draft accounting document.", exit_code=5)

    if capability_id == "journal_entry.lines.update":
        if not move.journal_id or move.journal_id.type != "general" or _generated_entry(move):
            raise _fail(failure_type, "business_rule_error", "Only an ordinary source-unlinked general journal entry can have its lines updated.", exit_code=6)
        before_ids = set(move.line_ids.ids)
        requested = parameters["lines"]
        lines = _ensure_ids(env, "account.move.line", {item["line_id"] for item in requested}, [
            ("move_id", "=", move.id), ("company_id", "=", company_id),
            ("display_type", "in", [False, "product", "tax"]), ("account_id", "!=", False),
        ], company_id, failure_type)
        by_id = {line.id: line for line in lines}
        _ensure_ids(env, "account.account", {
            item["changes"]["account_id"] for item in requested if "account_id" in item["changes"]
        }, [("company_ids", "in", [company_id])], company_id, failure_type)
        _ensure_ids(env, "res.partner", {
            item["changes"]["partner_id"] for item in requested if item["changes"].get("partner_id") is not None
        }, [("company_id", "in", [False, company_id])], company_id, failure_type)
        currencies = _ensure_ids(env, "res.currency", {
            item["changes"]["currency_id"] for item in requested if "currency_id" in item["changes"]
        }, [("active", "=", True)], company_id, failure_type)
        currency_by_id = {currency.id: currency for currency in currencies}
        for item in requested:
            changes = item["changes"]
            if "amount_currency" in changes:
                currency = currency_by_id[changes["currency_id"]] if "currency_id" in changes else by_id[item["line_id"]].currency_id
                if _rounded_currency_amount(currency, changes["amount_currency"]) != Decimal(changes["amount_currency"]):
                    raise _fail(failure_type, "business_rule_error", "The foreign amount must match its native currency precision.", exit_code=6)
        _validate_line_analytic_references(env, [item["changes"] for item in requested], company_id, failure_type)
        if any(_ENTRY_TAX_FIELDS & set(item["changes"]) for item in requested):
            if any(_journal_item_sourced(line) for line in move.line_ids):
                raise _fail(
                    failure_type, "business_rule_error",
                    "Explicit journal-entry tax inputs require an ordinary source-unlinked entry.",
                    exit_code=6,
                )
            _validate_entry_tax_references(
                env, [item["changes"] for item in requested], company_id, failure_type
            )
        targets = {item["line_id"]: dict(item["changes"]) for item in requested}
        for target in targets.values():
            if "tax_base_amount" in target:
                target["tax_base_amount"] = _canonical_decimal_text(target["tax_base_amount"])
        replay = all(
            _journal_item_current(by_id[item["line_id"]], set(item["changes"])) == targets[item["line_id"]]
            for item in requested
        )
        with env.cr.savepoint():
            if not replay:
                if any(_journal_item_sourced(line) for line in lines):
                    raise _fail(failure_type, "business_rule_error", "Source-linked journal lines cannot be changed by this capability.", exit_code=6)
                move.write({"line_ids": [
                    (1, item["line_id"], _journal_item_write_values(item["changes"]))
                    for item in requested
                ]})
                lines.invalidate_recordset()
                move.invalidate_recordset()
            if set(move.line_ids.ids) != before_ids or any(
                _journal_item_current(by_id[item["line_id"]], set(item["changes"])) != targets[item["line_id"]]
                for item in requested
            ):
                raise _fail(failure_type, "odoo_write_error", "Native journal-line changes were not persisted with the existing line IDs.", exit_code=6)
        return _move_result(move, company_id), replay

    line = _invoice_line(env, move, parameters["line_id"], company_id, failure_type) if invoice else _search_one(
        env, "account.move.line", [
            ("id", "=", parameters["line_id"]), ("move_id", "=", move.id),
            ("company_id", "=", company_id), ("account_id", "!=", False),
            ("display_type", "not in", ["line_section", "line_subsection", "line_note"]),
        ], company_id, failure_type,
    )
    if capability_id == "journal_item.date_maturity.update":
        if line.account_id.account_type not in {"asset_receivable", "liability_payable"}:
            raise _fail(failure_type, "business_rule_error", "Maturity dates can only be changed on a receivable or payable journal item.", exit_code=6)
        changes = {"date_maturity": parameters["date_maturity"]}
    elif capability_id == "journal_item.analytic_distribution.replace":
        changes = {"analytic_distribution": parameters["analytic_distribution"]}
        _validate_line_analytic_references(env, [changes], company_id, failure_type)
    elif capability_id == "invoice.line.unit.assign":
        if not line.product_id:
            raise _fail(failure_type, "business_rule_error", "Unit assignment requires a product-backed invoice business line.", exit_code=6)
        _ensure_ids(env, "product.product", {line.product_id.id}, [
            ("company_id", "in", [False, company_id]),
        ], company_id, failure_type)
        _ensure_ids(env, "uom.uom", {parameters["product_uom_id"]}, [], company_id, failure_type)
        if parameters["product_uom_id"] not in line.allowed_uom_ids.ids:
            raise _fail(failure_type, "business_rule_error", "The requested unit is not a native allowed unit for this invoice product.", exit_code=6)
        changes = {"product_uom_id": parameters["product_uom_id"]}
    else:
        changes = {"deductible_amount": parameters["deductible_amount"]}
        if Decimal(changes["deductible_amount"]) != 100 and move.move_type not in {"in_invoice", "in_refund"}:
            raise _fail(failure_type, "business_rule_error", "Partial deductibility is only supported on native purchase documents.", exit_code=6)
    replay = _journal_item_current(line, set(changes)) == changes
    if not replay:
        if invoice and _journal_item_sourced(line):
            raise _fail(failure_type, "business_rule_error", "Source-linked invoice business lines cannot change unit or deductibility by this capability.", exit_code=6)
        line.write(_journal_item_write_values(changes))
        line.invalidate_recordset()
        move.invalidate_recordset()
    if (
        _journal_item_current(line, set(changes)) != changes
        or _relation_id(line.move_id) != move.id
        or _relation_id(line.company_id) != company_id
    ):
        raise _fail(failure_type, "odoo_write_error", "Native journal-item changes were not persisted on the requested company and move.", exit_code=6)
    return _move_result(move, company_id, source_id=line.id), replay


def _dispatch_allowed(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    key: str,
    marker: str,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    if capability_id in invoice_preparation.CAPABILITY_IDS:
        return _write_invoice_preparation(env, capability_id, parameters, company_id, failure_type)
    if capability_id in journal_item_processing.CAPABILITY_IDS:
        return _write_journal_item_processing(env, capability_id, parameters, company_id, failure_type)
    if capability_id in company_processing.CAPABILITY_IDS:
        return _write_company_processing(env, capability_id, parameters, company_id, failure_type)
    if capability_id in analytic_processing.CAPABILITY_IDS:
        return _write_analytic_processing(env, capability_id, parameters, company_id, failure_type)
    if capability_id in journal_processing.CAPABILITY_IDS:
        return _write_journal_processing(env, capability_id, parameters, company_id, failure_type)
    if capability_id in account_processing.CAPABILITY_IDS:
        return _write_account_processing(env, capability_id, parameters, company_id, failure_type)
    if capability_id in tax_processing.CAPABILITY_IDS:
        return _write_tax_processing(env, capability_id, parameters, company_id, failure_type)
    if capability_id in payment_term_processing.CAPABILITY_IDS:
        return _write_payment_term_processing(env, capability_id, parameters, company_id, failure_type)
    if capability_id in reconciliation_processing.CAPABILITY_IDS:
        return _write_reconciliation_processing(env, capability_id, parameters, company_id, failure_type)
    if capability_id in payment_processing.CAPABILITY_IDS:
        return _write_payment_processing(env, capability_id, parameters, company_id, failure_type)
    if capability_id in invoice_presentation.CAPABILITY_IDS:
        return _write_invoice_presentation(env, capability_id, parameters, company_id, failure_type)
    if capability_id in move_processing.CAPABILITY_IDS:
        return _write_move_processing(env, capability_id, parameters, company_id, failure_type)
    if capability_id in partner_preferences.CAPABILITY_IDS:
        return _write_partner_preferences_batch(env, capability_id, parameters, company_id, failure_type)
    if capability_id in payment_configuration.CAPABILITY_IDS:
        return _write_payment_configuration_batch(env, capability_id, parameters, company_id, failure_type)
    if capability_id in fiscal_mappings.CAPABILITY_IDS:
        return _write_fiscal_mapping_batch(env, capability_id, parameters, company_id, failure_type)
    if capability_id in report_budgets.CAPABILITY_IDS:
        return _write_report_budget(env, capability_id, parameters, company_id, failure_type)
    if capability_id.startswith("fiscal_year."):
        return _write_fiscal_year(
            env, capability_id, parameters, company_id, failure_type
        )
    if capability_id.startswith("analytic.applicability."):
        return _write_analytic_applicability(
            env, capability_id, parameters, company_id, failure_type
        )
    if capability_id.startswith("analytic.distribution_model."):
        return _write_analytic_distribution_model(
            env, capability_id, parameters, company_id, failure_type
        )
    if capability_id.startswith("account.tag."):
        return _write_account_tag(env, capability_id, parameters, company_id, failure_type)
    if capability_id.startswith("tax.group."):
        return _write_tax_group(env, capability_id, parameters, company_id, failure_type)
    if capability_id.startswith("cash_rounding."):
        return _write_cash_rounding(env, capability_id, parameters, company_id, failure_type)
    if capability_id == "currency.rate.record":
        return _record_currency_rate(env, parameters, company_id, failure_type)
    if capability_id == "currency.rate.update":
        return _update_currency_rate(env, parameters, company_id, failure_type)
    if capability_id == "currency.rate.delete":
        return _delete_currency_rate(env, parameters, company_id, failure_type)
    if capability_id in _ACCOUNT_GROUP_WRITE_CAPABILITIES:
        return _write_account_group(
            env, capability_id, parameters, company_id, failure_type
        )
    if capability_id == "tax.repartition_lines.replace":
        return _replace_tax_repartition_lines(
            env, parameters, company_id, failure_type
        )
    if capability_id in {
        "reconciliation.model.create",
        "reconciliation.model.update",
    }:
        return _write_reconciliation_model(
            env, capability_id, parameters, company_id, failure_type
        )
    if capability_id == "reconciliation.model.lines.replace":
        return _replace_reconciliation_model_lines(
            env, parameters, company_id, failure_type
        )
    if capability_id in {
        "reconciliation.model.archive",
        "reconciliation.model.restore",
    }:
        return _transition_reconciliation_model(
            env, capability_id, parameters, company_id, failure_type
        )
    if capability_id == _SALE_ORDER_INVOICE_CAPABILITY:
        if "order_ids" in parameters:
            return _order_invoice_round(env, capability_id, parameters, company_id, key, failure_type)
        return _create_sale_order_invoice(env, parameters, company_id, failure_type)
    if capability_id == _SALE_DOWN_PAYMENT_CAPABILITY:
        return _create_sale_down_payment(env, parameters, company_id, key, failure_type)
    if capability_id == _STOCK_TRANSFER_CREATE_CAPABILITY:
        return _create_stock_transfer(
            env, parameters, company_id, key, marker, failure_type
        )
    if capability_id in _STOCK_TRANSFER_ACTION_CAPABILITIES:
        return _transition_stock_transfer(
            env, capability_id, parameters, company_id, failure_type
        )
    if capability_id == _STOCK_TRANSFER_QUANTITIES_CAPABILITY:
        return _set_stock_transfer_quantities(env, parameters, company_id, failure_type)
    if capability_id == _STOCK_TRANSFER_VALIDATE_CAPABILITY:
        return _validate_stock_transfer(env, parameters, company_id, failure_type)
    if capability_id == "purchase.order.bill.create":
        if "order_ids" in parameters:
            return _order_invoice_round(env, capability_id, parameters, company_id, key, failure_type)
        return _create_purchase_bill(env, parameters, company_id, failure_type)
    if capability_id == "purchase_bill.match":
        return _match_purchase_bill_lines(env, parameters, company_id, failure_type)
    if capability_id == "purchase_bill.lines.unmatch":
        return _unmatch_purchase_bill_lines(env, parameters, company_id, failure_type)
    if capability_id == "payment_term.create":
        return _create_payment_term(env, parameters, company_id, failure_type)
    if capability_id == "payment_term.update":
        return _update_payment_term(env, parameters, company_id, failure_type)
    if capability_id == "payment_term.lines.replace":
        return _replace_payment_term_lines(env, parameters, company_id, failure_type)
    if capability_id in {"payment_term.archive", "payment_term.restore"}:
        return _transition_payment_term(
            env, capability_id, parameters, company_id, failure_type
        )
    if capability_id == "period.accrual.generate":
        return _generate_period_accrual(env, parameters, company_id, key, failure_type)
    if capability_id == "fiscal_position.create":
        return _create_fiscal_position(env, parameters, company_id, failure_type)
    if capability_id == "fiscal_position.update":
        return _update_fiscal_position(env, parameters, company_id, failure_type)
    if capability_id == "fiscal_position.account_mappings.replace":
        return _replace_fiscal_position_mappings(
            env, parameters, company_id, failure_type
        )
    if capability_id in {"fiscal_position.archive", "fiscal_position.restore"}:
        return _transition_fiscal_position(
            env, capability_id, parameters, company_id, failure_type
        )
    if capability_id in _JOURNAL_GROUP_CAPABILITIES:
        return _write_journal_group(
            env, capability_id, parameters, company_id, failure_type
        )
    if capability_id == "account.transfer_model.create":
        return _create_transfer_model(env, parameters, company_id, failure_type)
    if capability_id == "account.transfer_model.update":
        return _update_transfer_model(env, parameters, company_id, failure_type)
    if capability_id == "account.transfer_model.duplicate":
        return _duplicate_transfer_model(env, parameters, company_id, failure_type)
    if capability_id in {
        "account.transfer_model.enable",
        "account.transfer_model.disable",
        "account.transfer_model.archive",
        "account.transfer_model.restore",
    }:
        return _transition_transfer_model(
            env, capability_id, parameters, company_id, failure_type
        )
    if capability_id == "account.transfer_model.delete":
        return _delete_transfer_model(env, parameters, company_id, failure_type)
    if capability_id in _ORDER_CREATE_CAPABILITIES:
        return _create_order(
            env,
            capability_id,
            parameters,
            company_id,
            key,
            marker,
            failure_type,
        )
    if capability_id in _ORDER_UPDATE_CAPABILITIES:
        return _update_draft_order(
            env, capability_id, parameters, company_id, failure_type
        )
    if capability_id in _ORDER_LINE_REPLACEMENT_CAPABILITIES:
        return _replace_order_lines(
            env, capability_id, parameters, company_id, failure_type
        )
    if capability_id in _ORDER_TRANSITION_CAPABILITIES:
        return _transition_order(
            env, capability_id, parameters, company_id, failure_type
        )
    if capability_id == "account.account.create":
        return _create_account_config(env, parameters, company_id, failure_type)
    if capability_id == "account.account.update":
        return _update_account_config(env, parameters, company_id, failure_type)
    if capability_id in {"account.account.archive", "account.account.restore"}:
        return _transition_config_record(
            env, capability_id, parameters, company_id, failure_type
        )
    if capability_id == "journal.create":
        return _create_journal_config(env, parameters, company_id, failure_type)
    if capability_id == "journal.update":
        return _update_journal_config(env, parameters, company_id, failure_type)
    if capability_id in {"journal.archive", "journal.restore"}:
        return _transition_config_record(
            env, capability_id, parameters, company_id, failure_type
        )
    if capability_id == "tax.create":
        return _create_tax_config(env, parameters, company_id, failure_type)
    if capability_id == "tax.update":
        return _update_tax_config(env, parameters, company_id, failure_type)
    if capability_id in {"tax.archive", "tax.restore"}:
        return _transition_config_record(
            env, capability_id, parameters, company_id, failure_type
        )
    if capability_id == "partner.create":
        return _create_partner(env, parameters, company_id, key, failure_type)
    if capability_id == "partner.update":
        return _update_partner(env, parameters, company_id, failure_type)
    if capability_id in {"partner.archive", "partner.restore"}:
        return _transition_partner(
            env, capability_id, parameters, company_id, failure_type
        )
    if capability_id == "partner.accounting.update":
        return _update_partner_accounting(env, parameters, company_id, failure_type)
    if capability_id == "partner.bank_account.create":
        return _create_partner_bank(env, parameters, company_id, failure_type)
    if capability_id == "partner.bank_account.update":
        return _update_partner_bank(env, parameters, company_id, failure_type)
    if capability_id in {
        "partner.bank_account.archive",
        "partner.bank_account.restore",
    }:
        return _transition_partner_bank(
            env, capability_id, parameters, company_id, failure_type
        )
    if capability_id == "analytic.plan.create":
        return _create_analytic_plan(env, parameters, company_id, key, failure_type)
    if capability_id == "analytic.plan.update":
        return _update_analytic_plan(env, parameters, company_id, failure_type)
    if capability_id == "analytic.account.create":
        return _create_analytic_account(env, parameters, company_id, key, failure_type)
    if capability_id == "analytic.account.update":
        return _update_analytic_account(env, parameters, company_id, failure_type)
    if capability_id in {"analytic.account.archive", "analytic.account.restore"}:
        return _transition_analytic_account(
            env, capability_id, parameters, company_id, failure_type
        )
    if capability_id == "analytic.line.create":
        return _create_analytic_line(env, parameters, company_id, key, failure_type)
    if capability_id == "analytic.line.update":
        return _update_analytic_line(env, parameters, company_id, failure_type)
    if capability_id == "analytic.line.delete":
        return _delete_analytic_line(env, parameters, company_id, failure_type)
    if capability_id == "account.return.create":
        return _create_account_return(env, parameters, company_id, failure_type)
    if capability_id == "account.return.checks.refresh":
        return _refresh_account_return_checks(
            env, parameters, company_id, failure_type
        )
    if capability_id == "account.return.check.result.update":
        return _update_account_return_check_result(
            env, parameters, company_id, failure_type
        )
    if capability_id in {
        "account.return.validate",
        "account.return.mark_submitted",
        "account.return.archive",
        "account.return.restore",
    }:
        return _transition_account_return(
            env, capability_id, parameters, company_id, failure_type
        )
    if capability_id == "account.return.delete":
        return _delete_account_return(env, parameters, company_id, failure_type)
    if capability_id == "product.create":
        return _create_product(env, parameters, company_id, failure_type)
    if capability_id == "product.update":
        return _update_product(env, parameters, company_id, failure_type)
    if capability_id == "product.duplicate":
        return _duplicate_product(env, parameters, company_id, failure_type)
    if capability_id in {"product.archive", "product.restore"}:
        return _transition_product(
            env, capability_id, parameters, company_id, failure_type
        )
    if capability_id == "product.cost.update":
        return _update_product_cost(env, parameters, company_id, failure_type)
    if capability_id == "product.accounting_profile.update":
        return _update_product_accounting_profile(
            env, parameters, company_id, failure_type
        )
    if capability_id == "product.category.accounting_profile.update":
        return _update_product_category_accounting_profile(
            env, parameters, company_id, failure_type
        )
    if capability_id == "budget.create":
        return _create_budget(env, parameters, company_id, key, failure_type)
    if capability_id == "budget.update_draft":
        return _update_draft_budget(env, parameters, company_id, failure_type)
    if capability_id == "budget.lines.replace":
        return _replace_budget_lines(env, parameters, company_id, failure_type)
    if capability_id in {
        "budget.confirm",
        "budget.reset_to_draft",
        "budget.cancel",
        "budget.mark_done",
    }:
        return _transition_budget(
            env, capability_id, parameters, company_id, failure_type
        )
    if capability_id == "asset.create":
        return _create_asset(env, parameters, company_id, key, failure_type)
    if capability_id == "asset.validate":
        return _validate_asset(env, parameters, company_id, failure_type)
    if capability_id == "asset.cancel":
        return _cancel_asset(env, parameters, company_id, failure_type)
    if capability_id == "asset.dispose":
        return _dispose_asset(env, parameters, company_id, failure_type)
    if capability_id == "asset.pause":
        return _pause_asset(env, parameters, company_id, failure_type)
    if capability_id in {
        "deferred_expense.generate_entries",
        "deferred_revenue.generate_entries",
    }:
        return _generate_deferred_entries(
            env,
            capability_id,
            parameters,
            company_id,
            key,
            failure_type,
        )
    if capability_id == "multicurrency.revaluation.generate_entries":
        return _generate_revaluation_entries(
            env,
            capability_id,
            parameters,
            company_id,
            key,
            failure_type,
        )
    if capability_id == "reconciliation.automatic.run":
        return _run_automatic_reconciliation(env, parameters, company_id, failure_type)
    if capability_id in {
        "period.transfer.run",
        "localization.china.period_transfer.run",
    }:
        return _run_period_transfer(
            env,
            capability_id,
            parameters,
            company_id,
            key,
            failure_type,
        )
    if capability_id in {"customer_invoice.create", "vendor_bill.create"}:
        return _create_document(
            env, capability_id, parameters, company_id, key, marker, failure_type
        )
    if capability_id == "journal_entry.create":
        return _create_entry(env, parameters, company_id, key, marker, failure_type)
    if capability_id == "invoice.line.create":
        return _create_invoice_line(env, parameters, company_id, failure_type)
    if capability_id == "invoice.line.update":
        return _update_invoice_line(env, parameters, company_id, failure_type)
    if capability_id == "invoice.line.delete":
        return _delete_invoice_line(env, parameters, company_id, failure_type)
    if capability_id in {"invoice.delete", "journal_entry.delete"}:
        return _delete_draft_move(
            env, capability_id, parameters, company_id, failure_type
        )
    if capability_id == "journal_entry.duplicate":
        return _duplicate_journal_entry(
            env, parameters, company_id, key, failure_type
        )
    if capability_id in {"invoice.update", "journal_entry.update"}:
        return _update_move(env, capability_id, parameters, company_id, failure_type)
    if capability_id in {
        "invoice.lines.replace",
        "journal_entry.lines.replace",
    }:
        return _replace_move_lines(
            env, capability_id, parameters, company_id, failure_type
        )
    if capability_id in {"journal_entry.lines.add", "journal_entry.lines.remove"}:
        return _write_entry_line_membership(
            env, capability_id, parameters, company_id, failure_type
        )
    if capability_id in {"invoice.lines.update", "invoice.lines.add"}:
        return _write_invoice_bulk_lines(env, capability_id, parameters, company_id, failure_type)
    if capability_id == "invoice.lines.remove":
        return _remove_invoice_lines(env, parameters, company_id, failure_type)
    if capability_id in {
        "invoice.cancel",
        "invoice.reset_to_draft",
        "journal_entry.cancel",
        "journal_entry.reset_to_draft",
    }:
        return _transition_move(
            env, capability_id, parameters, company_id, failure_type
        )
    if capability_id == "invoice.duplicate":
        return _duplicate_invoice(
            env, capability_id, parameters, company_id, key, failure_type
        )
    if capability_id == "invoice.type.switch":
        return _switch_invoice_type(env, parameters, company_id, failure_type)
    if capability_id in {"invoice.post", "journal_entry.post"}:
        return _post_move(env, capability_id, parameters, company_id, failure_type)
    if capability_id == "journal_entry.reverse":
        return _reverse_entry(env, parameters, company_id, marker, failure_type)
    if capability_id == "invoice.reverse_and_reissue":
        return _reverse_and_reissue_invoice(env, parameters, company_id, key, marker, failure_type)
    if capability_id in {"customer_credit_note.create", "vendor_refund.create"}:
        return _create_refund(
            env, capability_id, parameters, company_id, key, marker, failure_type
        )
    if capability_id in {
        "receivable.payment.register",
        "payable.payment.register",
    }:
        return _register_payment(
            env, capability_id, parameters, company_id, key, failure_type
        )
    if capability_id == "reconciliation.apply":
        return _apply_reconciliation(env, parameters, company_id, failure_type)
    if capability_id == "reconciliation.undo":
        return _undo_reconciliation(env, parameters, company_id, failure_type)
    if capability_id == "payment.cancel":
        return _cancel_payment(env, parameters, company_id, failure_type)
    if capability_id == "payment.post":
        return _post_payment(env, parameters, company_id, failure_type)
    if capability_id == "payment.create":
        return _create_payment(env, parameters, company_id, key, failure_type)
    if capability_id == "payment.update_draft":
        return _update_draft_payment(env, parameters, company_id, failure_type)
    if capability_id == "payment.reset_to_draft":
        return _reset_payment_to_draft(env, parameters, company_id, failure_type)
    if capability_id == "payment.duplicate":
        return _duplicate_payment(env, parameters, company_id, key, failure_type)
    if capability_id == "payment.delete":
        return _delete_payment(env, parameters, company_id, failure_type)
    if capability_id == "bank.statement.create":
        return _create_bank_statement(env, parameters, company_id, failure_type)
    if capability_id == "bank.statement.update":
        return _update_bank_statement(env, parameters, company_id, failure_type)
    if capability_id == "bank.statement.delete":
        return _delete_bank_statement(env, parameters, company_id, failure_type)
    if capability_id == "bank.transaction.delete":
        return _delete_bank_transaction(env, parameters, company_id, failure_type)
    if capability_id == "bank.transaction.update":
        return _update_bank_transaction(env, parameters, company_id, failure_type)
    if capability_id == "bank.transaction.match":
        return _match_bank_transaction(env, parameters, company_id, failure_type)
    if capability_id == "bank.transaction.unmatch":
        return _unmatch_bank_transaction(env, parameters, company_id, failure_type)
    if capability_id == "bank.transaction.counterparts.replace":
        return _replace_bank_counterparts(env, parameters, company_id, failure_type)
    if capability_id == "reconciliation.write_off":
        return _write_off_bank_transaction(env, parameters, company_id, failure_type)
    return _record_bank_transaction(
        env, parameters, company_id, key, marker, failure_type
    )


def dispatch(
    env: Any,
    payload: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> dict[str, Any]:
    """Validate, gate, and execute one fixed business-user write action."""

    capability_id, key, parameters, marker = _validated_payload(
        payload, company_id, failure_type
    )
    company_visible, module_installed, access_allowed = _gate(
        env, capability_id, company_id
    )
    if not access_allowed:
        return _page(
            env,
            company_id,
            company_visible=company_visible,
            module_installed=module_installed,
            access_allowed=False,
        )
    try:
        result, replay = _dispatch_allowed(
            env,
            capability_id,
            parameters,
            company_id,
            key,
            marker,
            failure_type,
        )
    except failure_type:
        raise
    except Exception as exc:
        class_name = type(exc).__name__
        if class_name == "AccessError":
            code, message, exit_code = (
                "unauthorized",
                "The configured user cannot execute this accounting write.",
                3,
            )
        elif class_name in {"UserError", "ValidationError"}:
            code, message, exit_code = (
                "business_rule_error",
                "Odoo rejected the accounting write by a business rule.",
                6,
            )
        else:
            code, message, exit_code = (
                "odoo_write_error",
                "The Odoo accounting write failed.",
                6,
            )
        raise _fail(failure_type, code, message, exit_code=exit_code) from exc
    return _page(
        env,
        company_id,
        company_visible=True,
        module_installed=True,
        access_allowed=True,
        idempotent_replay=replay,
        result=result,
    )
