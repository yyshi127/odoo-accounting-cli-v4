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
from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from time import strftime, strptime
from typing import Any

ACTION = "accounting.core_write.execute"
CAPABILITIES = frozenset(
    {
        "customer_invoice.create",
        "vendor_bill.create",
        "invoice.update",
        "invoice.lines.replace",
        "invoice.cancel",
        "invoice.reset_to_draft",
        "invoice.post",
        "journal_entry.create",
        "journal_entry.update",
        "journal_entry.lines.replace",
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
        "localization.china.period_transfer.run",
        "payment.create",
        "payment.update_draft",
        "payment.reset_to_draft",
        "bank.transaction.update",
        "bank.transaction.match",
        "bank.transaction.unmatch",
        "reconciliation.write_off",
        "analytic.account.create",
        "analytic.account.update",
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
        "date",
        "invoice_date",
        "invoice_date_due",
        "payment_term_id",
        "reference",
        "payment_reference",
    }
)
_JOURNAL_ENTRY_UPDATE_KEYS = frozenset({"date", "journal_id", "reference"})
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
_ACCOUNTING_REFERENCE_WRITE_CAPABILITIES = frozenset(
    {
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
    }
)
_ACCOUNT_TAG_FIELDS = frozenset({"name", "applicability", "color", "country_id"})
_TAX_GROUP_FIELDS = frozenset({"name", "sequence", "preceding_subtotal"})
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
_ANALYTIC_ACCOUNT_UPDATE_KEYS = frozenset({"name", "code", "partner_id", "active"})
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
_TAX_CONFIG_KEYS = frozenset(
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
_TAX_USE_TYPES = frozenset({"sale", "purchase", "none"})
_TAX_AMOUNT_TYPES = frozenset({"fixed", "percent", "division"})
_TAX_PRICE_INCLUDE_OVERRIDES = frozenset({"tax_included", "tax_excluded"})

_DOCUMENT_CREATE_REQUIRED_KEYS = frozenset(
    {"partner_id", "journal_id", "invoice_date", "currency_id", "lines"}
)
_DOCUMENT_CREATE_OPTIONAL_KEYS = frozenset(
    {
        "date",
        "invoice_date_due",
        "payment_term_id",
        "reference",
        "payment_reference",
    }
)
_DOCUMENT_LINE_REQUIRED_KEYS = frozenset(
    {"name", "account_id", "quantity", "price_unit", "tax_ids"}
)
_DEFERRED_LINE_DATE_FIELDS = ("deferred_start_date", "deferred_end_date")
_DOCUMENT_LINE_OPTIONAL_KEYS = frozenset(
    {"product_id", "discount", "analytic_distribution", *_DEFERRED_LINE_DATE_FIELDS}
)
_ENTRY_LINE_REQUIRED_KEYS = frozenset(
    {"name", "account_id", "partner_id", "debit", "credit"}
)
_ENTRY_LINE_OPTIONAL_KEYS = frozenset(
    {"currency_id", "amount_currency", "analytic_distribution"}
)
_REFUND_REQUIRED_KEYS = frozenset({"move_id", "date", "reason"})
_PAYMENT_REGISTER_REQUIRED_KEYS = frozenset({"move_id", "journal_id", "payment_date"})

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
        "reference",
        "payment_reference",
    },
    "invoice.update": {"move_id", "changes"},
    "invoice.lines.replace": {"move_id", "lines"},
    "invoice.cancel": {"move_id"},
    "invoice.reset_to_draft": {"move_id"},
    "invoice.post": {"move_id"},
    "journal_entry.create": {"journal_id", "date", "lines", "reference"},
    "journal_entry.update": {"move_id", "changes"},
    "journal_entry.lines.replace": {"move_id", "lines"},
    "journal_entry.cancel": {"move_id"},
    "journal_entry.reset_to_draft": {"move_id"},
    "journal_entry.post": {"move_id"},
    "journal_entry.reverse": {"move_id", "date", "reason"},
    "receivable.payment.register": {
        "move_id",
        "journal_id",
        "payment_date",
        "amount",
        "payment_difference_handling",
        "writeoff_account_id",
        "writeoff_label",
    },
    "payable.payment.register": {
        "move_id",
        "journal_id",
        "payment_date",
        "amount",
        "payment_difference_handling",
        "writeoff_account_id",
        "writeoff_label",
    },
    "reconciliation.apply": {"line_ids", "invoice_id", "outstanding_line_id"},
    "payment.cancel": {"payment_id"},
    "customer_credit_note.create": {"move_id", "date", "reason", "lines"},
    "vendor_refund.create": {"move_id", "date", "reason", "lines"},
    "payment.post": {"payment_id"},
    "reconciliation.undo": {
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
    "payment.reset_to_draft": {"payment_id"},
    "bank.transaction.update": {"transaction_id", "changes"},
    "bank.transaction.match": {"transaction_id", "candidate_line_ids"},
    "bank.transaction.unmatch": {"transaction_id"},
    "reconciliation.write_off": {
        "transaction_id",
        "write_off_account_id",
        "label",
        "expected_residual_amount",
    },
    "analytic.account.create": {"name", "plan_id", "code", "partner_id"},
    "analytic.account.update": {"analytic_account_id", "changes"},
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
    "sale.order.invoice.create": {"order_id"},
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
    "purchase.order.bill.create": {"order_id"},
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
    "invoice.cancel": "account.group_account_invoice",
    "invoice.reset_to_draft": "account.group_account_invoice",
    "invoice.post": "account.group_account_invoice",
    "journal_entry.create": "account.group_account_user",
    "journal_entry.update": "account.group_account_user",
    "journal_entry.lines.replace": "account.group_account_user",
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
    "localization.china.period_transfer.run": "account.group_account_user",
    "payment.create": "account.group_account_invoice",
    "payment.update_draft": "account.group_account_invoice",
    "payment.reset_to_draft": "account.group_account_invoice",
    "bank.transaction.update": "account.group_account_user",
    "bank.transaction.match": "account.group_account_user",
    "bank.transaction.unmatch": "account.group_account_user",
    "reconciliation.write_off": "account.group_account_user",
    "analytic.account.create": "account.group_account_user",
    "analytic.account.update": "account.group_account_user",
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
    "invoice.cancel": {"res.company", "account.move"},
    "invoice.reset_to_draft": {"res.company", "account.move"},
    "invoice.post": {"res.company", "account.move"},
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
    "invoice.cancel": {
        ("account.move", "read"),
        ("account.move", "write"),
    },
    "invoice.reset_to_draft": {
        ("account.move", "read"),
        ("account.move", "write"),
    },
    "invoice.post": {("account.move", "read"), ("account.move", "write")},
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
    _MODELS[_capability_id] = {"res.company", "res.country", "account.tax.group"}
    _ACCESS[_capability_id] = {
        ("res.company", "read"),
        ("res.country", "read"),
        ("account.tax.group", "read"),
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

_MODELS["invoice.lines.replace"].add("account.analytic.account")

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
        {"account.partial.reconcile", "account.full.reconcile"}
    )
    _ACCESS[_capability_id].update(
        {
            ("account.move.line", "write"),
            ("account.partial.reconcile", "read"),
            ("account.partial.reconcile", "create"),
            ("account.full.reconcile", "read"),
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


def _is_id(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


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
            or _decimal(line["quantity"], positive=True) is None
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
        ):
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
        if field_name == "partner_id" and not _is_id(field_value):
            return False
        if field_name in {"date", "invoice_date"} and not _is_date(field_value):
            return False
        if field_name == "invoice_date_due" and not (
            field_value is None or _is_date(field_value)
        ):
            return False
        if field_name == "payment_term_id" and not (
            field_value is None or _is_id(field_value)
        ):
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


def _valid_replacement_invoice_lines(value: Any) -> bool:
    if not isinstance(value, list) or not 1 <= len(value) <= 500:
        return False
    required = {
        "name",
        "product_id",
        "account_id",
        "quantity",
        "price_unit",
        "discount",
        "tax_ids",
    }
    for line in value:
        if not isinstance(line, dict) or not required <= set(line) <= required | {
            "analytic_distribution",
            *_DEFERRED_LINE_DATE_FIELDS,
        }:
            return False
        quantity = _decimal(line["quantity"])
        price_unit = _signed_decimal(line["price_unit"])
        discount = _decimal(line["discount"])
        tax_ids = line["tax_ids"]
        if (
            not _is_text(line["name"])
            or (line["product_id"] is not None and not _is_id(line["product_id"]))
            or not _is_id(line["account_id"])
            or quantity is None
            or price_unit is None
            or discount is None
            or discount > Decimal(100)
            or not isinstance(tax_ids, list)
            or any(not _is_id(item) for item in tax_ids)
            or tax_ids != sorted(set(tax_ids))
            or not _valid_deferred_line_dates(line)
            or (
                "analytic_distribution" in line
                and not _valid_analytic_distribution(line["analytic_distribution"])
            )
        ):
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
        }
        for line in lines
    ]


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


def _valid_bank_update_changes(changes: Any) -> bool:
    if (
        not isinstance(changes, dict)
        or not changes
        or not set(changes) <= {"date", "amount", "payment_ref", "partner_id"}
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
    return "partner_id" not in changes or (
        changes["partner_id"] is None or _is_id(changes["partner_id"])
    )


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
    elif set(values) != _TAX_CONFIG_KEYS:
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
    return all(
        field_name not in values or isinstance(values[field_name], bool)
        for field_name in ("include_base_amount", "is_base_affected")
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
        return _is_id(parameters["order_id"])
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
    if (not partial and set(values) != _TAX_GROUP_FIELDS) or not set(values) <= _TAX_GROUP_FIELDS:
        return False
    return bool(
        ("name" not in values or _is_text(values["name"], maximum=256))
        and ("sequence" not in values or isinstance(values["sequence"], int) and not isinstance(values["sequence"], bool) and values["sequence"] >= 0)
        and ("preceding_subtotal" not in values or values["preceding_subtotal"] is None or _is_text(values["preceding_subtotal"], maximum=256))
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


def _valid_parameters(
    capability_id: str, parameters: Any, company_id: int | None = None
) -> bool:
    if not isinstance(parameters, dict):
        return False
    parameter_keys = set(parameters)
    allowed_keys = _PARAMETER_KEYS[capability_id]
    required_keys = allowed_keys
    if capability_id in {"customer_invoice.create", "vendor_bill.create"}:
        required_keys = _DOCUMENT_CREATE_REQUIRED_KEYS
    elif capability_id == "journal_entry.create":
        required_keys = frozenset({"journal_id", "date", "lines"})
    elif capability_id in {
        "customer_credit_note.create",
        "vendor_refund.create",
    }:
        required_keys = _REFUND_REQUIRED_KEYS
    elif capability_id in {
        "receivable.payment.register",
        "payable.payment.register",
    }:
        required_keys = _PAYMENT_REGISTER_REQUIRED_KEYS
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
    if not required_keys <= parameter_keys <= allowed_keys:
        return False
    if capability_id == _SALE_ORDER_INVOICE_CAPABILITY:
        return _is_id(parameters["order_id"])
    if capability_id in _STOCK_TRANSFER_CAPABILITIES:
        return _valid_stock_transfer_parameters(capability_id, parameters)
    if capability_id in _PURCHASE_BILL_CAPABILITIES:
        return _valid_purchase_bill_parameters(capability_id, parameters)
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
            and (
                "payment_term_id" not in parameters
                or parameters["payment_term_id"] is None
                or _is_id(parameters["payment_term_id"])
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
    if capability_id == "journal_entry.lines.replace":
        return _is_id(parameters["move_id"]) and _valid_entry_lines(
            parameters["lines"], minimum=1
        )
    if capability_id in {
        "invoice.cancel",
        "invoice.reset_to_draft",
        "journal_entry.cancel",
        "journal_entry.reset_to_draft",
    }:
        return _is_id(parameters["move_id"])
    if capability_id in {"invoice.post", "journal_entry.post"}:
        return _is_id(parameters["move_id"])
    if capability_id == "journal_entry.reverse" or capability_id in {
        "customer_credit_note.create",
        "vendor_refund.create",
    }:
        return (
            _is_id(parameters["move_id"])
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
            _is_id(parameters["move_id"])
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
    if capability_id == "payment.reset_to_draft":
        return _is_id(parameters["payment_id"])
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
    if capability_id == "reconciliation.write_off":
        expected = _signed_decimal(parameters["expected_residual_amount"])
        return bool(
            _is_id(parameters["transaction_id"])
            and _is_id(parameters["write_off_account_id"])
            and _is_text(parameters["label"], maximum=200)
            and expected is not None
            and expected != 0
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
        return f"{capability_id}:{parameters['order_id']}"
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
        return f"purchase.order.bill.create:{parameters['order_id']}"
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
        "analytic.account.create",
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
    if capability_id in {
        "bank.transaction.update",
        "bank.transaction.match",
        "reconciliation.write_off",
    }:
        if capability_id == "bank.transaction.update":
            target: Any = parameters["changes"]
        elif capability_id == "bank.transaction.match":
            target = parameters["candidate_line_ids"]
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
    if capability_id in {
        "customer_credit_note.create",
        "vendor_refund.create",
    } or (
        capability_id in {"receivable.payment.register", "payable.payment.register"}
        and "amount" in parameters
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
        module_installed and env.user.has_group(_GROUPS[capability_id])
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
    if set(_record_ids(account.company_ids)) != {company_id}:
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
        if len(existing) != 1 or not _account_config_matches(
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
    if not _account_config_matches(account, parameters, company_id, exact_company=True):
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
    for field_name in ("invoice_label", "price_include_override"):
        if field_name in result and result[field_name] is None:
            result[field_name] = False
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
    _validate_tax_references(env, write_changes, company_id, failure_type)
    if "name" in changes or "type_tax_use" in changes:
        target_name = changes.get("name", tax.name)
        target_use = changes.get("type_tax_use", tax.type_tax_use)
        candidates = _scoped(env, "account.tax", company_id).search(
            [
                ("company_id", "=", company_id),
                ("name", "=", target_name),
                ("type_tax_use", "=", target_use),
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
        "reference": "ref",
        "payment_reference": "payment_reference",
    }
    for parameter_name, field_name in header_map.items():
        if parameter_name in parameters:
            values[field_name] = parameters[parameter_name] or False
    move = _scoped(env, "account.move", company_id).create(values)
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
                    **(
                        {
                            "currency_id": line["currency_id"] or False,
                            "amount_currency": (
                                Decimal(line["amount_currency"])
                                if line["amount_currency"] is not None
                                else False
                            ),
                        }
                        if "currency_id" in line
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


def _validate_invoice_update_references(
    env: Any,
    changes: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> None:
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
        if field_name == "partner_id":
            values[field_name] = _many2one_id(move.partner_id)
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
        _validate_invoice_update_references(env, changes, company_id, failure_type)
        current = _current_invoice_changes(move, set(changes))
    else:
        _validate_journal_update_references(env, changes, company_id, failure_type)
        current = _current_journal_entry_changes(move, set(changes))
    if current == changes:
        return _move_result(move, company_id), True
    if move.state != "draft":
        raise _fail(
            failure_type,
            "state_conflict",
            "Only a draft accounting move can be updated.",
            exit_code=5,
        )

    field_map = (
        {
            "partner_id": "partner_id",
            "date": "date",
            "invoice_date": "invoice_date",
            "invoice_date_due": "invoice_date_due",
            "payment_term_id": "invoice_payment_term_id",
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


def _current_invoice_lines(move: Any) -> list[dict[str, Any]] | None:
    result: list[dict[str, Any]] = []
    for line in _ordered_move_lines(move.invoice_line_ids):
        if getattr(line, "display_type", None) not in {None, False, "product"}:
            return None
        account_id = _many2one_id(line.account_id)
        if not _is_text(line.name) or account_id is None:
            return None
        result.append(
            {
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
            }
        )
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
                "debit": _canonical_decimal_text(line.debit),
                "credit": _canonical_decimal_text(line.credit),
                "currency_id": _many2one_id(line.currency_id),
                "amount_currency": _canonical_decimal_text(line.amount_currency),
                "analytic_distribution": _normalized_analytic_distribution(
                    getattr(line, "analytic_distribution", None)
                ),
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
    return company_currency_id


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
                **(
                    {
                        "currency_id": line["currency_id"] or False,
                        "amount_currency": (
                            Decimal(line["amount_currency"])
                            if line["amount_currency"] is not None
                            else False
                        ),
                    }
                    if "currency_id" in line
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
    if invoice_action:
        _validate_invoice_line_references(env, move, lines, company_id, failure_type)
        matches = _invoice_lines_match(_current_invoice_lines(move), lines)
    else:
        company_currency_id = _validate_entry_line_references(
            env, lines, company_id, failure_type
        )
        expected = _normalized_entry_replacement_lines(lines, company_currency_id)
        matches = _current_entry_lines(move) == expected
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
        _invoice_lines_match(_current_invoice_lines(move), lines)
        if invoice_action
        else _current_entry_lines(move) == expected
    )
    if not verified:
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not persist the requested accounting move lines.",
            exit_code=6,
        )
    return _move_result(move, company_id), False


def _transition_move(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
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


def _post_move(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
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


def _create_refund(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    key: str,
    marker: str,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    source_type = (
        "out_invoice"
        if capability_id == "customer_credit_note.create"
        else "in_invoice"
    )
    refund_type = "out_refund" if source_type == "out_invoice" else "in_refund"
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
            _current_invoice_lines(refunds), parameters["lines"]
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
        _current_invoice_lines(refunds), parameters["lines"]
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo did not persist the requested refund lines.",
            exit_code=6,
        )
    return _move_result(refunds, company_id, source_id=source.id), False


def _payment_sources(payment: Any) -> set[int]:
    return set(_record_ids(payment.reconciled_invoice_ids)) | set(
        _record_ids(payment.reconciled_bill_ids)
    )


def _rounded_currency_amount(currency: Any, value: str) -> Decimal:
    return Decimal(str(currency.round(float(Decimal(value)))))


def _register_payment(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    key: str,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    move_type = (
        "out_invoice"
        if capability_id == "receivable.payment.register"
        else "in_invoice"
    )
    source = _search_one(
        env,
        "account.move",
        [
            ("id", "=", parameters["move_id"]),
            ("company_id", "=", company_id),
            ("move_type", "=", move_type),
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
                    or (
                        isinstance(stored_marker, str)
                        and stored_marker.startswith("ODACV4:")
                    )
                )
                and stored_marker != operation_marker
            )
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
    if handling is not None:
        # Native move creation consumes this standard default; no posted write.
        wizard_context["default_invoice_origin"] = operation_marker
    wizard = (
        _scoped(env, "account.payment.register", company_id)
        .with_context(**wizard_context)
        .create(wizard_values)
    )
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
        or (handling is not None and payment.move_id.invoice_origin != operation_marker)
    ):
        raise _fail(
            failure_type,
            "odoo_write_error",
            "Odoo returned an invalid registered payment.",
            exit_code=6,
        )
    if handling == "reconcile":
        signed_difference = difference if move_type == "out_invoice" else -difference
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


def _undo_reconciliation(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
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
    if payment.state not in {"in_process", "paid", "canceled"}:
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


def _bank_transaction_actual_values(transaction: Any) -> dict[str, Any]:
    return {
        "date": str(transaction.date),
        "amount": _canonical_decimal_text(transaction.amount),
        "payment_ref": transaction.payment_ref,
        "partner_id": transaction.partner_id.id or None,
    }


def _bank_transaction_target_values(values: dict[str, Any]) -> dict[str, Any]:
    result = dict(values)
    if "amount" in result:
        result["amount"] = _canonical_decimal_text(result["amount"])
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


def _update_bank_transaction(
    env: Any,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
    transaction = _bank_transaction(
        env, parameters["transaction_id"], company_id, failure_type
    )
    actual = _bank_transaction_actual_values(transaction)
    target = {**actual, **_bank_transaction_target_values(parameters["changes"])}
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
    if values.get("partner_id") is None and "partner_id" in values:
        values["partner_id"] = False
    transaction.write(values)
    _invalidate_bank_transaction(transaction)
    if (
        transaction.move_id.state != "posted"
        or _bank_transaction_actual_values(transaction) != target
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
        raise _fail(
            failure_type,
            "state_conflict",
            "The bank transaction is not in its default unmatched state.",
            exit_code=5,
        )
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
        return _bank_transaction_result(existing, company_id, failure_type), True

    company = _search_one(
        env,
        "res.company",
        [("id", "=", company_id)],
        company_id,
        failure_type,
    )
    _ensure_ids(
        env,
        "account.journal",
        {parameters["journal_id"]},
        [
            ("company_id", "=", company_id),
            ("type", "in", ["bank", "cash"]),
            ("currency_id", "in", [False, company.currency_id.id]),
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
    transaction = _scoped(env, "account.bank.statement.line", company_id).create(
        {
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
    if transaction.move_id.state != "posted":
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
            "The transfer entry cannot hold another operation marker.",
            exit_code=5,
        )
    move.write({"invoice_origin": value})


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


def _tax_group_values(group: Any) -> dict[str, Any]:
    return {"name": group.name, "sequence": group.sequence, "preceding_subtotal": group.preceding_subtotal or None}


def _write_tax_group(env: Any, capability_id: str, parameters: dict[str, Any], company_id: int, failure_type: type[Exception]) -> tuple[dict[str, Any], bool]:
    create = capability_id == "tax.group.create"
    values = parameters if create else parameters["changes"]
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
                and _tax_group_values(existing) == values
            ):
                return _reference_result(existing, "account.tax.group", company_id), True
            raise _fail(failure_type, "state_conflict", "A different tax group already uses this company and name.", exit_code=5)
        group = model.create({**values, "preceding_subtotal": values["preceding_subtotal"] or False, "company_id": company_id, "country_id": country_id or False})
        if _many2one_id(group.company_id) != company_id or _many2one_id(group.country_id) != country_id or _tax_group_values(group) != values:
            raise _fail(failure_type, "odoo_write_error", "Odoo did not create the requested tax group.", exit_code=6)
        return _reference_result(group, "account.tax.group", company_id), False
    group = _search_one(env, "account.tax.group", [("id", "=", parameters["tax_group_id"]), ("company_id", "=", company_id)], company_id, failure_type)
    if _many2one_id(group.company_id) != company_id or _many2one_id(group.country_id) != country_id:
        raise _fail(failure_type, "record_not_found", "The tax group is unavailable in the company country.", exit_code=4)
    target = {**_tax_group_values(group), **values}
    if _tax_group_values(group) == target:
        return _reference_result(group, "account.tax.group", company_id), True
    group.write({key: (False if value is None else value) for key, value in values.items()}); group.invalidate_recordset(list(values))
    if _many2one_id(group.company_id) != company_id or _many2one_id(group.country_id) != country_id or _tax_group_values(group) != target:
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


def _dispatch_allowed(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    key: str,
    marker: str,
    failure_type: type[Exception],
) -> tuple[dict[str, Any], bool]:
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
        return _create_sale_order_invoice(env, parameters, company_id, failure_type)
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
    if capability_id == "analytic.account.create":
        return _create_analytic_account(env, parameters, company_id, key, failure_type)
    if capability_id == "analytic.account.update":
        return _update_analytic_account(env, parameters, company_id, failure_type)
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
    if capability_id in {"invoice.update", "journal_entry.update"}:
        return _update_move(env, capability_id, parameters, company_id, failure_type)
    if capability_id in {
        "invoice.lines.replace",
        "journal_entry.lines.replace",
    }:
        return _replace_move_lines(
            env, capability_id, parameters, company_id, failure_type
        )
    if capability_id in {
        "invoice.cancel",
        "invoice.reset_to_draft",
        "journal_entry.cancel",
        "journal_entry.reset_to_draft",
    }:
        return _transition_move(
            env, capability_id, parameters, company_id, failure_type
        )
    if capability_id in {"invoice.post", "journal_entry.post"}:
        return _post_move(env, capability_id, parameters, company_id, failure_type)
    if capability_id == "journal_entry.reverse":
        return _reverse_entry(env, parameters, company_id, marker, failure_type)
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
    if capability_id == "bank.transaction.update":
        return _update_bank_transaction(env, parameters, company_id, failure_type)
    if capability_id == "bank.transaction.match":
        return _match_bank_transaction(env, parameters, company_id, failure_type)
    if capability_id == "bank.transaction.unmatch":
        return _unmatch_bank_transaction(env, parameters, company_id, failure_type)
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
