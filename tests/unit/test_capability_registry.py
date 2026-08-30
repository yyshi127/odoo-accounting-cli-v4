from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path

import pytest

from odoo_accounting_cli_v4.bridge.core_object_reads_runtime import (
    _REQUIRED_MODELS as CORE_OBJECT_READ_MODELS,
)
from odoo_accounting_cli_v4.bridge.core_writes_runtime import (
    _ACCESS as CORE_WRITE_ACCESS,
)
from odoo_accounting_cli_v4.bridge.core_writes_runtime import (
    _GROUPS as CORE_WRITE_GROUPS,
)
from odoo_accounting_cli_v4.bridge.core_writes_runtime import (
    _MODELS as CORE_WRITE_MODELS,
)
from odoo_accounting_cli_v4.bridge.inventory_accounting_runtime import (
    _ACCESS as INVENTORY_ACCOUNTING_ACCESS,
)
from odoo_accounting_cli_v4.bridge.inventory_accounting_runtime import (
    _GROUPS as INVENTORY_ACCOUNTING_GROUPS,
)
from odoo_accounting_cli_v4.bridge.inventory_accounting_runtime import (
    _MODELS as INVENTORY_ACCOUNTING_MODELS,
)
from odoo_accounting_cli_v4.bridge.order_documents_runtime import (
    _required_models as order_document_required_models,
)
from odoo_accounting_cli_v4.registry import (
    InstanceValidationError,
    RegistryError,
    _validate_descriptor,
    load_registry,
)

EXPECTED_CAPABILITY_COUNT = 345
EXPECTED_ENABLED_CAPABILITY_COUNT = 330
EXPECTED_IMPLEMENTED_READ_COUNT = 200
EXPECTED_IMPLEMENTED_WRITE_COUNT = 130
EXPECTED_DISABLED_CAPABILITY_COUNT = 15
EXPECTED_UNCONFIGURED_CAPABILITY_COUNT = 297
EXPECTED_DEGRADED_CAPABILITY_COUNT = 33
EXPECTED_SCHEMA_COUNT = 665
EXPECTED_CAPABILITY_IDS_SHA256 = (
    "79e2fb08cf06789c3689f536a1c447f5b936413810de63df7ef0d3a51b677c8c"
)
EXPECTED_FIRST_CAPABILITY_SHA256 = (
    "7b15597c6b11ea1a421b1a8ca56f25b653492951ee0efd3c9e1c70c06b448216"
)
IMPLEMENTED_READS = {
    "account.account.get": "account_account_get",
    "account.account.list": "account_account_list",
    "account.group.get": "account_group_get",
    "account.group.list": "account_group_list",
    "account.return.check.get": "account_return_check_get",
    "account.return.check.list": "account_return_check_list",
    "account.return.get": "account_return_get",
    "account.return.search": "account_return_search",
    "account.return.summary": "account_return_summary",
    "account.return.type.list": "account_return_type_list",
    "account.tag.get": "account_tag_get",
    "account.tag.list": "account_tag_list",
    "analytic.account.get": "analytic_account_get",
    "analytic.account.search": "analytic_account_search",
    "analytic.applicability.get": "analytic_applicability_get",
    "analytic.applicability.list": "analytic_applicability_list",
    "analytic.distribution_model.get": "analytic_distribution_model_get",
    "analytic.distribution_model.list": "analytic_distribution_model_list",
    "analytic.line.get": "analytic_line_get",
    "analytic.line.search": "analytic_line_search",
    "analytic.plan.get": "analytic_plan_get",
    "analytic.plan.list": "analytic_plan_list",
    "bank.get": "bank_get",
    "bank.list": "bank_list",
    "bank.statement.get": "bank_statement_get",
    "bank.statement.pdf.export": "document_bank_statement_pdf_export",
    "bank.statement.search": "bank_statement_search",
    "bank.transaction.get": "bank_transaction_get",
    "bank.transaction.match_candidates.list": (
        "bank_transaction_match_candidates_list"
    ),
    "bank.transaction.reconciliation.get": ("bank_transaction_reconciliation_get"),
    "bank.transaction.search": "bank_transaction_search",
    "budget.get": "budget_get",
    "budget.line.get": "budget_line_get",
    "budget.line.list": "budget_line_list",
    "budget.search": "budget_search",
    "cash_rounding.get": "cash_rounding_get",
    "cash_rounding.list": "cash_rounding_list",
    "company.accounting_context.list": "company_accounting_context_list",
    "company.fiscal_year.resolve": "company_fiscal_year_resolve",
    "company.lock_dates.inspect": "company_lock_dates_inspect",
    "currency.get": "currency_get",
    "journal.list": "journal_list",
    "journal.get": "journal_get",
    "journal.configuration.inspect": "journal_configuration_inspect",
    "journal_item.get": "journal_item_get",
    "journal_item.search": "journal_item_search",
    "journal.accounting_date.resolve": "journal_accounting_date_resolve",
    "journal_item.analysis.summary": "journal_item_analysis_summary",
    "tax.list": "tax_list",
    "payment_term.list": "payment_term_list",
    "currency.list": "currency_list",
    "journal_entry.search": "journal_entry_search",
    "journal_entry.get": "journal_entry_get",
    "report.trial_balance": "report_trial_balance",
    "report.trial_balance.export": "report_trial_balance_export",
    "report.balance_sheet": "report_balance_sheet",
    "report.balance_sheet.export": "report_balance_sheet_export",
    "report.profit_and_loss": "report_profit_and_loss",
    "report.profit_and_loss.export": "report_profit_and_loss_export",
    "report.cash_flow": "report_cash_flow",
    "report.cash_flow.export": "report_cash_flow_export",
    "report.customer_statement": "report_customer_statement",
    "report.followup": "report_followup",
    "report.tax": "report_tax",
    "report.tax.export": "report_tax_export",
    "user.accounting_access.inspect": "user_accounting_access_inspect",
    "company.accounting_configuration.inspect": (
        "company_accounting_configuration_inspect"
    ),
    "diagnostic.accounting_environment.inspect": (
        "diagnostic_accounting_environment_inspect"
    ),
    "localization.china.configuration.inspect": (
        "localization_china_configuration_inspect"
    ),
    "localization.singapore.configuration.inspect": (
        "localization_singapore_configuration_inspect"
    ),
    "partner.accounting.search": "partner_accounting_search",
    "partner.accounting.get": "partner_accounting_get",
    "partner.get": "partner_get",
    "partner.search": "partner_search",
    "partner.bank_account.get": "partner_bank_account_get",
    "partner.bank_account.search": "partner_bank_account_search",
    "payment.method.get": "payment_method_get",
    "payment.method.list": "payment_method_list",
    "payment_term.get": "payment_term_get",
    "invoice.search": "invoice_search",
    "invoice.get": "invoice_get",
    "invoice.pdf.export": "document_invoice_pdf_export",
    "invoice.analysis.search": "invoice_analysis_search",
    "invoice.analysis.summary": "invoice_analysis_summary",
    "invoice.payment_status.inspect": "invoice_payment_status_inspect",
    "incoterm.get": "incoterm_get",
    "incoterm.list": "incoterm_list",
    "journal.group.get": "journal_group_get",
    "journal.group.list": "journal_group_list",
    "receivable.open_items.list": "receivable_open_items_list",
    "payable.open_items.list": "payable_open_items_list",
    "payment.search": "payment_search",
    "payment.get": "payment_get",
    "payment.receipt.pdf.export": "document_payment_receipt_pdf_export",
    "reconciliation.candidates.list": "reconciliation_candidates_list",
    "reconciliation.full.get": "reconciliation_full_get",
    "reconciliation.full.list": "reconciliation_full_list",
    "reconciliation.model.get": "reconciliation_model_get",
    "reconciliation.model.list": "reconciliation_model_list",
    "reconciliation.model.line.get": "reconciliation_model_line_get",
    "reconciliation.model.line.list": "reconciliation_model_line_list",
    "reconciliation.partial.get": "reconciliation_partial_get",
    "reconciliation.partial.list": "reconciliation_partial_list",
    "currency.rate.list": "currency_rate_list",
    "currency.convert": "currency_convert",
    "validation.journal_entry.check": "validation_journal_entry_check",
    "report.general_ledger": "report_general_ledger",
    "report.general_ledger.export": "report_general_ledger_export",
    "report.partner_ledger": "report_partner_ledger",
    "report.partner_ledger.export": "report_partner_ledger_export",
    "report.aged_receivable": "report_aged_receivable",
    "report.aged_receivable.export": "report_aged_receivable_export",
    "report.aged_payable": "report_aged_payable",
    "report.aged_payable.export": "report_aged_payable_export",
    "report.journal": "report_journal",
    "report.journal.export": "report_journal_export",
    "report.catalog.get": "report_catalog_get",
    "report.catalog.list": "report_catalog_list",
    "report.bank_reconciliation": "report_bank_reconciliation",
    "report.budget": "budget_report",
    "report.executive_summary": "report_executive_summary",
    "report.executive_summary.export": "report_executive_summary_export",
    "bank.transaction.list": "bank_transaction_list",
    "cogs.entries.list": "cogs_entries_list",
    "inventory.accounting_entries.list": "inventory_accounting_entries_list",
    "inventory.availability.inspect": "inventory_availability_inspect",
    "inventory.on_hand.summary": "inventory_on_hand_summary",
    "product.accounting_profile.get": "product_accounting_profile_get",
    "product.category.list": "product_category_list",
    "purchase_bill.matching.inspect": "purchase_bill_matching_inspect",
    "report.inventory_valuation": "report_inventory_valuation",
    "sale_invoice.stock_link.inspect": "sale_invoice_stock_link_inspect",
    "stock.location.list": "stock_location_list",
    "stock.move.search": "stock_move_search",
    "stock.operation_type.list": "stock_operation_type_list",
    "stock.route.list": "stock_route_list",
    "stock.transfer.get": "stock_transfer_get",
    "stock.transfer.search": "stock_transfer_search",
    "tax.get": "tax_get",
    "tax.repartition_line.get": "tax_repartition_line_get",
    "tax.repartition_line.list": "tax_repartition_line_list",
    "asset.search": "asset_search",
    "asset.get": "asset_get",
    "asset.depreciation_schedule.get": "asset_depreciation_schedule_get",
    "report.asset": "report_asset",
    "report.asset.export": "report_asset_export",
    "report.deferred_expense": "report_deferred_expense",
    "report.deferred_expense.export": "report_deferred_expense_export",
    "report.deferred_revenue": "report_deferred_revenue",
    "report.deferred_revenue.export": "report_deferred_revenue_export",
    "report.multicurrency_revaluation": "report_multicurrency_revaluation",
    "report.multicurrency_revaluation.export": (
        "report_multicurrency_revaluation_export"
    ),
    "report.china.balance_sheet": "report_china_balance_sheet",
    "report.china.balance_sheet.export": "report_china_balance_sheet_export",
    "report.china.profit_and_loss": "report_china_profit_and_loss",
    "report.china.profit_and_loss.export": ("report_china_profit_and_loss_export"),
    "report.china.cash_flow": "report_china_cash_flow",
    "report.china.cash_flow.export": "report_china_cash_flow_export",
    "report.singapore.gst": "report_singapore_gst",
    "report.singapore.gst.export": "report_singapore_gst_export",
    "localization.china.voucher.render": ("document_localization_china_voucher_render"),
    "fiscal_position.resolve": "fiscal_position_resolve",
    "fiscal_position.get": "fiscal_position_get",
    "fiscal_position.search": "fiscal_position_search",
    "fiscal_position.account_mapping.list": (
        "fiscal_position_account_mapping_list"
    ),
    "fiscal_position.tax_mapping.list": "fiscal_position_tax_mapping_list",
    "fiscal_year.get": "fiscal_year_get",
    "fiscal_year.search": "fiscal_year_search",
    "diagnostic.journal_integrity.inspect": ("diagnostic_journal_integrity_inspect"),
    "product.get": "product_get",
    "product.search": "product_search",
    "tax.group.get": "tax_group_get",
    "tax.group.list": "tax_group_list",
    "warehouse.list": "warehouse_list",
    "purchase.order.analysis.summary": "purchase_order_analysis_summary",
    "purchase.order.get": "purchase_order_get",
    "purchase.order.line.search": "purchase_order_line_search",
    "purchase.order.pdf.export": "document_purchase_order_pdf_export",
    "purchase.rfq.pdf.export": "document_purchase_rfq_pdf_export",
    "purchase.order.search": "purchase_order_search",
    "sale.order.analysis.summary": "sale_order_analysis_summary",
    "sale.order.get": "sale_order_get",
    "sale.order.line.search": "sale_order_line_search",
    "sale.order.pdf.export": "document_sale_order_pdf_export",
    "sale.order.search": "sale_order_search",
    "stock.delivery_slip.pdf.export": "document_stock_delivery_slip_pdf_export",
    "stock.picking_operations.pdf.export": (
        "document_stock_picking_operations_pdf_export"
    ),
    "stock.return_slip.pdf.export": "document_stock_return_slip_pdf_export",
    "invoice.duplicate_candidates.list": "invoice_duplicate_candidates_list",
    "invoice.tax_breakdown.inspect": "invoice_tax_breakdown_inspect",
    "recurring.journal_entry.search": "recurring_journal_entry_search",
    "recurring.journal_entry.get": "recurring_journal_entry_get",
    "account.transfer_model.search": "account_transfer_model_search",
    "account.transfer_model.get": "account_transfer_model_get",
    "partner.credit_exposure.inspect": "partner_credit_exposure_inspect",
    "journal.sequence_irregularity.list": "journal_sequence_irregularity_list",
    "account.lock_exception.search": "account_lock_exception_search",
    "account.lock_exception.get": "account_lock_exception_get",
    "report.external_value.search": "report_external_value_search",
    "report.external_value.get": "report_external_value_get",
}
ORDER_DOCUMENT_WRITES = {
    "purchase.order.cancel",
    "purchase.order.confirm",
    "purchase.order.create",
    "purchase.order.lines.replace",
    "purchase.order.reset_to_draft",
    "purchase.order.update_draft",
    "sale.order.cancel",
    "sale.order.confirm",
    "sale.order.create",
    "sale.order.lines.replace",
    "sale.order.reset_to_draft",
    "sale.order.update_draft",
}
PROCUREMENT_FOLLOWUP_WRITES = {
    "purchase.order.bill.create",
    "purchase_bill.match",
    "purchase_bill.lines.unmatch",
    "payment_term.create",
    "payment_term.update",
    "payment_term.lines.replace",
    "payment_term.archive",
    "payment_term.restore",
    "period.accrual.generate",
}
IMPLEMENTED_WRITES = {
    "account.group.create",
    "account.group.update",
    "account.tag.archive",
    "account.tag.create",
    "account.tag.restore",
    "account.tag.update",
    "account.account.archive",
    "account.account.create",
    "account.account.restore",
    "account.account.update",
    "analytic.account.create",
    "analytic.account.update",
    "asset.cancel",
    "asset.create",
    "asset.dispose",
    "asset.pause",
    "asset.validate",
    "bank.transaction.record",
    "bank.transaction.match",
    "bank.transaction.unmatch",
    "bank.transaction.update",
    "budget.cancel",
    "budget.confirm",
    "budget.create",
    "budget.lines.replace",
    "budget.mark_done",
    "budget.reset_to_draft",
    "budget.update_draft",
    "cash_rounding.create",
    "cash_rounding.update",
    "customer_credit_note.create",
    "customer_invoice.create",
    "currency.rate.record",
    "deferred_expense.generate_entries",
    "deferred_revenue.generate_entries",
    "invoice.cancel",
    "invoice.lines.replace",
    "invoice.post",
    "invoice.reset_to_draft",
    "invoice.update",
    "journal.archive",
    "journal.create",
    "journal.restore",
    "journal.update",
    "journal_entry.cancel",
    "journal_entry.create",
    "journal_entry.lines.replace",
    "journal_entry.post",
    "journal_entry.reset_to_draft",
    "journal_entry.reverse",
    "journal_entry.update",
    "localization.china.period_transfer.run",
    "multicurrency.revaluation.generate_entries",
    "payable.payment.register",
    "partner.accounting.update",
    "partner.archive",
    "partner.bank_account.archive",
    "partner.bank_account.create",
    "partner.bank_account.restore",
    "partner.bank_account.update",
    "partner.create",
    "partner.restore",
    "partner.update",
    "payment.cancel",
    "payment.create",
    "payment.post",
    "payment.reset_to_draft",
    "payment.update_draft",
    "period.transfer.run",
    "receivable.payment.register",
    "reconciliation.apply",
    "reconciliation.automatic.run",
    "reconciliation.model.archive",
    "reconciliation.model.create",
    "reconciliation.model.lines.replace",
    "reconciliation.model.restore",
    "reconciliation.model.update",
    "reconciliation.undo",
    "reconciliation.write_off",
    "tax.archive",
    "tax.create",
    "tax.group.create",
    "tax.group.update",
    "tax.repartition_lines.replace",
    "tax.restore",
    "tax.update",
    "sale.order.invoice.create",
    "stock.transfer.assign",
    "stock.transfer.cancel",
    "stock.transfer.confirm",
    "stock.transfer.create",
    "stock.transfer.quantities.set",
    "stock.transfer.unreserve",
    "stock.transfer.validate",
    "vendor_bill.create",
    "vendor_refund.create",
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
    "fiscal_year.create",
    "fiscal_year.update",
    "analytic.applicability.create",
    "analytic.applicability.update",
    "analytic.distribution_model.create",
    "analytic.distribution_model.update",
    "journal.group.create",
    "journal.group.update",
} | ORDER_DOCUMENT_WRITES
EXTENDED_WRITES = {
    "asset.cancel",
    "asset.dispose",
    "asset.pause",
    "deferred_expense.generate_entries",
    "deferred_revenue.generate_entries",
    "localization.china.period_transfer.run",
    "multicurrency.revaluation.generate_entries",
    "period.transfer.run",
    "reconciliation.automatic.run",
}
DOCUMENT_LIFECYCLE_WRITES = {
    "invoice.cancel",
    "invoice.lines.replace",
    "invoice.reset_to_draft",
    "invoice.update",
    "journal_entry.cancel",
    "journal_entry.lines.replace",
    "journal_entry.reset_to_draft",
    "journal_entry.update",
}
PAYMENT_BANK_WRITES = {
    "bank.transaction.match",
    "bank.transaction.unmatch",
    "bank.transaction.update",
    "payment.create",
    "payment.reset_to_draft",
    "payment.update_draft",
    "reconciliation.write_off",
}
ANALYTIC_BUDGET_WRITES = {
    "analytic.account.create",
    "analytic.account.update",
    "budget.cancel",
    "budget.confirm",
    "budget.create",
    "budget.lines.replace",
    "budget.mark_done",
    "budget.reset_to_draft",
    "budget.update_draft",
}
PARTNER_MASTER_DATA_READS = {
    "partner.get",
    "partner.search",
}
PARTNER_MASTER_DATA_WRITES = {
    "partner.accounting.update",
    "partner.archive",
    "partner.bank_account.archive",
    "partner.bank_account.create",
    "partner.bank_account.restore",
    "partner.bank_account.update",
    "partner.create",
    "partner.restore",
    "partner.update",
}
ACCOUNTING_CONFIG_WRITES = {
    "account.account.archive",
    "account.account.create",
    "account.account.restore",
    "account.account.update",
    "journal.archive",
    "journal.create",
    "journal.restore",
    "journal.update",
    "tax.archive",
    "tax.create",
    "tax.restore",
    "tax.update",
}
ACCOUNTING_CONFIGURATION_EXPANSION_WRITES = {
    "account.group.create",
    "account.group.update",
    "currency.rate.record",
    "reconciliation.model.archive",
    "reconciliation.model.create",
    "reconciliation.model.lines.replace",
    "reconciliation.model.restore",
    "reconciliation.model.update",
    "tax.repartition_lines.replace",
}
ACCOUNTING_MASTER_DATA_COMPLETION_WRITES = {
    "account.tag.archive",
    "account.tag.create",
    "account.tag.restore",
    "account.tag.update",
    "cash_rounding.create",
    "cash_rounding.update",
    "tax.group.create",
    "tax.group.update",
}
ACCOUNTING_RULES_FISCAL_YEAR_WRITES = {
    "fiscal_year.create",
    "fiscal_year.update",
    "analytic.applicability.create",
    "analytic.applicability.update",
    "analytic.distribution_model.create",
    "analytic.distribution_model.update",
}
ACCOUNTING_RULES_FISCAL_YEAR_READS = {
    "fiscal_position.account_mapping.list",
    "fiscal_position.tax_mapping.list",
}
FISCAL_POSITION_JOURNAL_GROUP_WRITES = {
    "fiscal_position.account_mappings.replace",
    "fiscal_position.archive",
    "fiscal_position.create",
    "fiscal_position.restore",
    "fiscal_position.update",
    "journal.group.create",
    "journal.group.update",
}
LOCALIZATION_CONFIGURATION_READS = {
    "localization.china.configuration.inspect",
    "localization.singapore.configuration.inspect",
}
ACCOUNTING_DEPTH_READS = {
    "invoice.payment_status.inspect",
}
ACCOUNTING_DEPTH_WRITES = {
    "customer_credit_note.create",
    "customer_invoice.create",
    "invoice.lines.replace",
    "journal_entry.create",
    "journal_entry.lines.replace",
    "payable.payment.register",
    "receivable.payment.register",
    "reconciliation.apply",
    "reconciliation.undo",
    "vendor_bill.create",
    "vendor_refund.create",
}
PAYMENT_BANK_BATCH_READS = {
    "bank.transaction.match_candidates.list",
    "bank.transaction.reconciliation.get",
    "bank.transaction.search",
}
TRANSFER_WRITES = {
    "localization.china.period_transfer.run",
    "period.transfer.run",
}
FAILED_LIVE_WRITES = {
    "asset.validate",
}
ACCOUNTING_REFERENCE_BATCH_LIVE_READS = {
    "account.group.list",
    "bank.get",
    "bank.list",
    "journal.configuration.inspect",
    "reconciliation.model.line.get",
    "reconciliation.model.line.list",
    "report.catalog.get",
    "report.catalog.list",
    "tax.repartition_line.get",
    "tax.repartition_line.list",
}
ACCOUNTING_CONFIGURATION_EXPANSION_LIVE_READS = {
    "account.group.get",
}
ACCOUNTING_OPERATIONAL_READS = {
    "invoice.duplicate_candidates.list",
    "invoice.tax_breakdown.inspect",
    "recurring.journal_entry.search",
    "recurring.journal_entry.get",
    "account.transfer_model.search",
    "account.transfer_model.get",
    "partner.credit_exposure.inspect",
    "journal.sequence_irregularity.list",
    "account.lock_exception.search",
    "account.lock_exception.get",
    "report.external_value.search",
    "report.external_value.get",
}
PENDING_LIVE_READS = {
    "product.accounting_profile.get",
}
FINANCIAL_REPORT_EXPORT_LIVE_READS = {
    "report.trial_balance.export",
    "report.balance_sheet.export",
    "report.profit_and_loss.export",
    "report.cash_flow.export",
    "report.tax.export",
    "report.general_ledger.export",
    "report.partner_ledger.export",
    "report.aged_receivable.export",
    "report.aged_payable.export",
    "report.executive_summary.export",
    "report.journal.export",
    "report.asset.export",
    "report.deferred_expense.export",
    "report.deferred_revenue.export",
    "report.multicurrency_revaluation.export",
    "report.china.balance_sheet.export",
    "report.china.profit_and_loss.export",
    "report.china.cash_flow.export",
    "report.singapore.gst.export",
}
DOCUMENT_EXPORT_LIVE_READS = {
    "invoice.pdf.export",
    "payment.receipt.pdf.export",
    "bank.statement.pdf.export",
    "sale.order.pdf.export",
    "purchase.order.pdf.export",
    "purchase.rfq.pdf.export",
    "stock.delivery_slip.pdf.export",
    "stock.picking_operations.pdf.export",
    "stock.return_slip.pdf.export",
    "localization.china.voucher.render",
}
ASSET_LIVE_READS = {
    "asset.search",
    "asset.get",
    "asset.depreciation_schedule.get",
    "report.asset",
}
INVENTORY_ACCOUNTING_LIVE_READS = {
    "cogs.entries.list",
    "inventory.accounting_entries.list",
    "purchase_bill.matching.inspect",
    "report.inventory_valuation",
    "sale_invoice.stock_link.inspect",
}
INVENTORY_READ_LIVE_READS = {
    "inventory.availability.inspect",
    "inventory.on_hand.summary",
    "product.category.list",
    "stock.location.list",
    "stock.move.search",
    "stock.operation_type.list",
    "stock.route.list",
    "stock.transfer.get",
    "stock.transfer.search",
    "warehouse.list",
}
ORDER_DOCUMENT_LIVE_READS = {
    "purchase.order.analysis.summary",
    "purchase.order.get",
    "purchase.order.line.search",
    "purchase.order.search",
    "sale.order.analysis.summary",
    "sale.order.get",
    "sale.order.line.search",
    "sale.order.search",
}
MANAGEMENT_REPORTING_PERIOD_LIVE_READS = {
    "company.fiscal_year.resolve",
    "company.lock_dates.inspect",
    "fiscal_year.get",
    "fiscal_year.search",
    "invoice.analysis.search",
    "invoice.analysis.summary",
    "report.customer_statement",
    "report.followup",
}
RETURN_JOURNAL_ANALYSIS_LIVE_READS = {
    "account.return.check.get",
    "account.return.check.list",
    "account.return.get",
    "account.return.search",
    "account.return.summary",
    "account.return.type.list",
    "journal.accounting_date.resolve",
    "journal_item.analysis.summary",
}
CORE_OBJECT_READ_HANDLERS = {
    "account.account.get": "account_account_get",
    "account.group.get": "account_group_get",
    "account.group.list": "account_group_list",
    "account.tag.get": "account_tag_get",
    "account.tag.list": "account_tag_list",
    "analytic.account.get": "analytic_account_get",
    "analytic.account.search": "analytic_account_search",
    "analytic.applicability.get": "analytic_applicability_get",
    "analytic.applicability.list": "analytic_applicability_list",
    "analytic.distribution_model.get": "analytic_distribution_model_get",
    "analytic.distribution_model.list": "analytic_distribution_model_list",
    "analytic.line.get": "analytic_line_get",
    "analytic.line.search": "analytic_line_search",
    "analytic.plan.get": "analytic_plan_get",
    "analytic.plan.list": "analytic_plan_list",
    "bank.statement.get": "bank_statement_get",
    "bank.statement.search": "bank_statement_search",
    "bank.transaction.get": "bank_transaction_get",
    "bank.get": "bank_get",
    "bank.list": "bank_list",
    "budget.get": "budget_get",
    "budget.line.get": "budget_line_get",
    "budget.line.list": "budget_line_list",
    "budget.search": "budget_search",
    "cash_rounding.get": "cash_rounding_get",
    "cash_rounding.list": "cash_rounding_list",
    "currency.get": "currency_get",
    "incoterm.get": "incoterm_get",
    "incoterm.list": "incoterm_list",
    "journal.get": "journal_get",
    "journal.configuration.inspect": "journal_configuration_inspect",
    "journal.group.get": "journal_group_get",
    "journal.group.list": "journal_group_list",
    "journal_item.get": "journal_item_get",
    "journal_item.search": "journal_item_search",
    "partner.accounting.get": "partner_accounting_get",
    "partner.get": "partner_get",
    "partner.search": "partner_search",
    "partner.bank_account.get": "partner_bank_account_get",
    "partner.bank_account.search": "partner_bank_account_search",
    "payment.method.get": "payment_method_get",
    "payment.method.list": "payment_method_list",
    "payment_term.get": "payment_term_get",
    "reconciliation.model.get": "reconciliation_model_get",
    "reconciliation.model.list": "reconciliation_model_list",
    "reconciliation.model.line.get": "reconciliation_model_line_get",
    "reconciliation.model.line.list": "reconciliation_model_line_list",
    "reconciliation.full.get": "reconciliation_full_get",
    "reconciliation.full.list": "reconciliation_full_list",
    "reconciliation.partial.get": "reconciliation_partial_get",
    "reconciliation.partial.list": "reconciliation_partial_list",
    "tax.get": "tax_get",
    "tax.repartition_line.get": "tax_repartition_line_get",
    "tax.repartition_line.list": "tax_repartition_line_list",
    "fiscal_position.get": "fiscal_position_get",
    "fiscal_position.search": "fiscal_position_search",
    "fiscal_position.account_mapping.list": (
        "fiscal_position_account_mapping_list"
    ),
    "fiscal_position.tax_mapping.list": "fiscal_position_tax_mapping_list",
    "product.get": "product_get",
    "product.search": "product_search",
    "tax.group.get": "tax_group_get",
    "tax.group.list": "tax_group_list",
    "report.catalog.get": "report_catalog_get",
    "report.catalog.list": "report_catalog_list",
    "invoice.duplicate_candidates.list": "invoice_duplicate_candidates_list",
    "invoice.tax_breakdown.inspect": "invoice_tax_breakdown_inspect",
    "recurring.journal_entry.search": "recurring_journal_entry_search",
    "recurring.journal_entry.get": "recurring_journal_entry_get",
    "account.transfer_model.search": "account_transfer_model_search",
    "account.transfer_model.get": "account_transfer_model_get",
    "partner.credit_exposure.inspect": "partner_credit_exposure_inspect",
    "journal.sequence_irregularity.list": "journal_sequence_irregularity_list",
    "account.lock_exception.search": "account_lock_exception_search",
    "account.lock_exception.get": "account_lock_exception_get",
    "report.external_value.search": "report_external_value_search",
    "report.external_value.get": "report_external_value_get",
}
REFERENCE_OBJECT_BATCH_LIVE_READS = {
    "account.tag.get",
    "account.tag.list",
    "analytic.account.get",
    "analytic.account.search",
    "analytic.plan.get",
    "analytic.plan.list",
    "fiscal_position.get",
    "fiscal_position.search",
    "product.get",
    "product.search",
    "tax.group.get",
    "tax.group.list",
}
ACCOUNTING_CONFIGURATION_BATCH_LIVE_READS = {
    "cash_rounding.get",
    "cash_rounding.list",
    "incoterm.get",
    "incoterm.list",
    "journal.group.get",
    "journal.group.list",
    "payment.method.get",
    "reconciliation.model.get",
}
PAYMENT_RECONCILIATION_BATCH_LIVE_READS = {
    "bank.statement.get",
    "bank.statement.search",
    "partner.bank_account.get",
    "partner.bank_account.search",
    "reconciliation.full.get",
    "reconciliation.full.list",
    "reconciliation.partial.get",
    "reconciliation.partial.list",
}
ANALYTIC_BUDGET_BATCH_LIVE_READS = {
    "analytic.applicability.get",
    "analytic.applicability.list",
    "analytic.distribution_model.get",
    "analytic.distribution_model.list",
    "analytic.line.get",
    "analytic.line.search",
    "budget.get",
    "budget.line.get",
    "budget.line.list",
    "budget.search",
    "report.budget",
}
CORE_OBJECT_BATCH_LIVE_READS = (
    {
        *CORE_OBJECT_READ_MODELS,
        "report.bank_reconciliation",
    }
    - REFERENCE_OBJECT_BATCH_LIVE_READS
    - ACCOUNTING_CONFIGURATION_BATCH_LIVE_READS
    - PAYMENT_RECONCILIATION_BATCH_LIVE_READS
    - ANALYTIC_BUDGET_BATCH_LIVE_READS
    - PARTNER_MASTER_DATA_READS
    - ACCOUNTING_REFERENCE_BATCH_LIVE_READS
    - ACCOUNTING_CONFIGURATION_EXPANSION_LIVE_READS
    - ACCOUNTING_RULES_FISCAL_YEAR_READS
    - ACCOUNTING_OPERATIONAL_READS
)


def test_registry_contains_the_frozen_full_matrix() -> None:
    registry = load_registry()

    assert len(registry.ids()) == EXPECTED_CAPABILITY_COUNT
    assert len(IMPLEMENTED_READS) == EXPECTED_IMPLEMENTED_READ_COUNT
    assert len(IMPLEMENTED_WRITES) == EXPECTED_IMPLEMENTED_WRITE_COUNT
    statuses = [registry.describe(item)["status"]["value"] for item in registry.ids()]
    assert statuses.count("disabled") == EXPECTED_DISABLED_CAPABILITY_COUNT
    assert statuses.count("unconfigured") == EXPECTED_UNCONFIGURED_CAPABILITY_COUNT
    assert statuses.count("degraded") == EXPECTED_DEGRADED_CAPABILITY_COUNT
    assert (
        sum(
            registry.describe(item)["handler_key"] is not None
            for item in registry.ids()
        )
        == EXPECTED_ENABLED_CAPABILITY_COUNT
    )
    assert (
        len(
            [
                path
                for path in (
                    Path(__file__).resolve().parents[2] / "schemas" / "v1"
                ).glob("*.json")
                if "\\" not in path.name
            ]
        )
        == EXPECTED_SCHEMA_COUNT
    )
    assert hashlib.sha256("\n".join(registry.ids()).encode()).hexdigest() == (
        EXPECTED_CAPABILITY_IDS_SHA256
    )
    assert re.fullmatch(r"[0-9a-f]{64}", registry.digest)

    domains = {registry.describe(item)["domain"] for item in registry.ids()}
    assert {
        "accounting_context",
        "accounting_master_data",
        "general_ledger",
        "invoices_and_bills",
        "receivables_payables",
        "payments",
        "bank_reconciliation",
        "multicurrency",
        "assets",
        "deferrals",
        "inventory_accounting",
        "purchase_accounting",
        "sales_accounting",
        "financial_reports",
        "localization_china",
        "localization_singapore",
        "diagnostics",
        "validation",
        "operations",
    } <= domains


def test_first_capability_is_byte_semantically_unchanged() -> None:
    registry = load_registry()

    descriptor = registry.describe("account.account.list")
    canonical = json.dumps(
        descriptor,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    assert hashlib.sha256(canonical).hexdigest() == EXPECTED_FIRST_CAPABILITY_SHA256
    assert descriptor["domain"] == "chart_of_accounts"
    assert descriptor["access"] == "read"
    assert descriptor["source"]["modules"] == ["account", "base"]
    assert descriptor["source"]["models"] == ["account.account", "res.company"]
    assert descriptor["requirements"]["company"] == "required"
    assert descriptor["requirements"]["groups"] == ["base.group_user"]
    assert descriptor["requirements"]["acl"] == [
        "res.company:read",
        "account.account:read",
    ]
    assert descriptor["status"] == {
        "value": "unconfigured",
        "reason_code": "runtime_context_required",
        "reason": "Static registry metadata does not declare target-specific runtime availability; availability is evaluated for each configured database, company, and user.",
    }
    assert descriptor["handler_key"] == "account_account_list"
    assert "会计科目" in descriptor["routing"]["aliases"]["zh_CN"]
    assert "科目余额" in descriptor["routing"]["not_for"]["zh_CN"]
    assert set(descriptor["strategies"]) == {
        "preview",
        "execute",
        "verify",
        "idempotency",
        "reverse",
    }
    assert set(descriptor["tests"]) == {"unit", "integration", "golden", "e2e"}
    assert descriptor["tests"]["integration"] == {
        "status": "implemented",
        "references": ["tests/integration/test_account_account_list_live.py"],
        "reason": "The live integration test verifies the real local Odoo bridge against both dedicated synthetic database aliases, including two-page cursor ordering and non-overlap.",
    }


def test_every_unimplemented_capability_is_honestly_disabled_without_a_handler() -> (
    None
):
    registry = load_registry()

    for capability_id in registry.ids():
        if capability_id in IMPLEMENTED_READS or capability_id in IMPLEMENTED_WRITES:
            continue
        descriptor = registry.describe(capability_id)
        assert descriptor["handler_key"] is None
        assert descriptor["status"] == {
            "value": "disabled",
            "reason_code": "implementation_pending",
            "reason": "The capability is frozen in the G3 matrix but has no implementation or allowlisted handler.",
        }
        assert {
            definition["status"] for definition in descriptor["tests"].values()
        } == {"planned"}
        assert all(
            definition["references"] == []
            for definition in descriptor["tests"].values()
        )


def test_implemented_reads_have_specialized_contracts_and_runtime_status() -> None:
    registry = load_registry()

    for capability_id, handler_key in IMPLEMENTED_READS.items():
        descriptor = registry.describe(capability_id)
        assert descriptor["handler_key"] == handler_key
        assert descriptor["schemas"] == {
            "request": f"schemas/v1/{capability_id}.request.schema.json",
            "response": f"schemas/v1/{capability_id}.response.schema.json",
        }
        assert descriptor["status"]["value"] == "unconfigured"
        assert descriptor["status"]["reason_code"] == "runtime_context_required"
        if capability_id in PARTNER_MASTER_DATA_READS:
            assert descriptor["tests"]["unit"]["status"] == "implemented"
            assert descriptor["tests"]["unit"]["references"] == [
                "tests/unit/test_partner_master_data.py",
                "tests/unit/test_partner_master_data_runtime.py",
                "tests/unit/test_partner_master_data_cli.py",
                "tests/unit/test_partner_master_data_registry.py",
            ]
            assert descriptor["tests"]["integration"]["status"] == "implemented"
            assert descriptor["tests"]["integration"]["references"] == [
                "tests/integration/test_partner_master_data_batch_live.py"
            ]
            continue
        assert descriptor["tests"]["unit"]["status"] == "implemented"
        if capability_id in ACCOUNTING_OPERATIONAL_READS:
            assert descriptor["tests"]["integration"]["status"] == "implemented"
            assert descriptor["tests"]["integration"]["references"] == [
                "tests/integration/test_accounting_operational_reads_live.py"
            ]
            continue
        if capability_id in PENDING_LIVE_READS:
            assert descriptor["tests"]["integration"]["status"] == "planned"
            assert descriptor["tests"]["integration"]["references"] == []
            continue
        assert descriptor["tests"]["integration"]["status"] == "implemented"
        if capability_id in DOCUMENT_EXPORT_LIVE_READS:
            expected_live_test = "tests/integration/test_document_export_batch_live.py"
        elif capability_id in FINANCIAL_REPORT_EXPORT_LIVE_READS:
            expected_live_test = (
                "tests/integration/test_financial_report_export_batch_live.py"
            )
        elif capability_id in ASSET_LIVE_READS:
            expected_live_test = "tests/integration/test_asset_batch_live.py"
        elif capability_id in REFERENCE_OBJECT_BATCH_LIVE_READS:
            expected_live_test = (
                "tests/integration/test_reference_object_read_batch_live.py"
            )
        elif capability_id in ACCOUNTING_CONFIGURATION_BATCH_LIVE_READS:
            expected_live_test = (
                "tests/integration/test_accounting_configuration_read_batch_live.py"
            )
        elif capability_id in LOCALIZATION_CONFIGURATION_READS:
            expected_live_test = (
                "tests/integration/test_accounting_configuration_batch_live.py"
            )
        elif capability_id in PAYMENT_RECONCILIATION_BATCH_LIVE_READS:
            expected_live_test = (
                "tests/integration/test_payment_reconciliation_read_batch_live.py"
            )
        elif capability_id in ANALYTIC_BUDGET_BATCH_LIVE_READS:
            expected_live_test = (
                "tests/integration/test_analytic_budget_read_batch_live.py"
            )
        elif capability_id in PAYMENT_BANK_BATCH_READS:
            expected_live_test = (
                "tests/integration/test_payment_bank_capability_batch_live.py"
            )
        elif capability_id in ACCOUNTING_REFERENCE_BATCH_LIVE_READS:
            expected_live_test = (
                "tests/integration/test_accounting_reference_read_batch_live.py"
            )
        elif capability_id in ACCOUNTING_CONFIGURATION_EXPANSION_LIVE_READS:
            expected_live_test = (
                "tests/integration/test_accounting_configuration_expansion_live.py"
            )
        elif capability_id in ACCOUNTING_RULES_FISCAL_YEAR_READS:
            expected_live_test = (
                "tests/integration/test_accounting_rules_fiscal_year_live.py"
            )
        elif capability_id in CORE_OBJECT_BATCH_LIVE_READS:
            expected_live_test = "tests/integration/test_core_object_read_batch_live.py"
        elif capability_id in INVENTORY_ACCOUNTING_LIVE_READS:
            expected_live_test = (
                "tests/integration/test_inventory_accounting_batch_live.py"
            )
        elif capability_id in INVENTORY_READ_LIVE_READS:
            expected_live_test = "tests/integration/test_inventory_read_batch_live.py"
        elif capability_id in ORDER_DOCUMENT_LIVE_READS:
            expected_live_test = "tests/integration/test_order_documents_batch_live.py"
        elif capability_id in MANAGEMENT_REPORTING_PERIOD_LIVE_READS:
            expected_live_test = (
                "tests/integration/test_management_reporting_period_batch_live.py"
            )
        elif capability_id in RETURN_JOURNAL_ANALYSIS_LIVE_READS:
            expected_live_test = (
                "tests/integration/test_return_journal_analysis_batch_live.py"
            )
        elif capability_id in {"journal_entry.search", "journal_entry.get"}:
            expected_live_test = "tests/integration/test_journal_entries_live.py"
        elif capability_id == "currency.rate.list":
            expected_live_test = "tests/integration/test_currency_rate_list_live.py"
        elif capability_id in {
            "bank.transaction.list",
            "currency.convert",
            "validation.journal_entry.check",
            "report.general_ledger",
            "report.partner_ledger",
            "report.aged_receivable",
            "report.aged_payable",
            "report.journal",
            "report.executive_summary",
            "report.deferred_expense",
            "report.deferred_revenue",
            "report.multicurrency_revaluation",
            "report.china.balance_sheet",
            "report.china.profit_and_loss",
            "report.china.cash_flow",
            "report.singapore.gst",
            "fiscal_position.resolve",
            "diagnostic.journal_integrity.inspect",
        }:
            expected_live_test = (
                "tests/integration/test_remaining_read_batch_live.py"
                if capability_id
                in {
                    "report.deferred_expense",
                    "report.deferred_revenue",
                    "report.multicurrency_revaluation",
                    "report.china.balance_sheet",
                    "report.china.profit_and_loss",
                    "report.china.cash_flow",
                    "report.singapore.gst",
                    "fiscal_position.resolve",
                    "diagnostic.journal_integrity.inspect",
                }
                else "tests/integration/test_read_capability_batch_live.py"
            )
        elif capability_id == "report.trial_balance":
            expected_live_test = "tests/integration/test_trial_balance_live.py"
        elif capability_id == "report.balance_sheet":
            expected_live_test = "tests/integration/test_balance_sheet_live.py"
        elif capability_id == "report.profit_and_loss":
            expected_live_test = "tests/integration/test_profit_and_loss_live.py"
        elif capability_id == "report.cash_flow":
            expected_live_test = "tests/integration/test_cash_flow_live.py"
        elif capability_id == "report.tax":
            expected_live_test = "tests/integration/test_tax_report_live.py"
        elif capability_id == "user.accounting_access.inspect":
            expected_live_test = "tests/integration/test_accounting_access_live.py"
        elif capability_id == "partner.accounting.search":
            expected_live_test = "tests/integration/test_partner_accounting_live.py"
        elif capability_id in {
            "invoice.search",
            "invoice.get",
            "invoice.payment_status.inspect",
        }:
            expected_live_test = "tests/integration/test_invoices_live.py"
        elif capability_id in {
            "receivable.open_items.list",
            "payable.open_items.list",
        }:
            expected_live_test = "tests/integration/test_open_items_live.py"
        elif capability_id == "reconciliation.candidates.list":
            expected_live_test = (
                "tests/integration/test_reconciliation_candidates_live.py"
            )
        elif capability_id in {"payment.search", "payment.get"}:
            expected_live_test = "tests/integration/test_payments_live.py"
        elif capability_id in {
            "company.accounting_configuration.inspect",
            "diagnostic.accounting_environment.inspect",
        }:
            expected_live_test = "tests/integration/test_environment_inspection_live.py"
        elif capability_id == "company.accounting_context.list":
            expected_live_test = (
                "tests/integration/test_company_accounting_context_live.py"
            )
        else:
            expected_live_test = (
                "tests/integration/test_account_account_list_live.py"
                if capability_id == "account.account.list"
                else "tests/integration/test_master_data_lists_live.py"
            )
        expected_live_tests = [expected_live_test]
        if capability_id in ACCOUNTING_DEPTH_READS:
            expected_live_tests.append(
                "tests/integration/test_accounting_depth_batch_live.py"
            )
        assert descriptor["tests"]["integration"]["references"] == expected_live_tests


def test_core_object_reads_and_bank_report_match_the_fixed_runtime() -> None:
    registry = load_registry()

    assert set(CORE_OBJECT_READ_MODELS) == set(CORE_OBJECT_READ_HANDLERS)
    for capability_id, handler_key in CORE_OBJECT_READ_HANDLERS.items():
        descriptor = registry.describe(capability_id)
        models = list(CORE_OBJECT_READ_MODELS[capability_id])
        source_models = descriptor["source"]["models"]

        assert descriptor["handler_key"] == handler_key
        if capability_id in ACCOUNTING_OPERATIONAL_READS:
            # These descriptors freeze full source/ACL provenance separately from
            # the runtime bridge's smaller model-availability preflight.
            assert models[0] == source_models[0] == "res.company"
            assert models[1] in source_models
        else:
            assert source_models == models
        assert descriptor["source"]["wizards"] == []
        assert descriptor["source"]["report_handlers"] == []
        assert descriptor["requirements"]["acl"] == [
            f"{model}:read" for model in source_models
        ]
        assert descriptor["schemas"] == {
            "request": f"schemas/v1/{capability_id}.request.schema.json",
            "response": f"schemas/v1/{capability_id}.response.schema.json",
        }
        assert descriptor["status"]["value"] == "unconfigured"
        assert descriptor["status"]["reason_code"] == "runtime_context_required"

    bank_report = registry.describe("report.bank_reconciliation")
    bank_report_models = [
        "account.report",
        "account.move.line",
        "res.currency",
        "account.journal",
        "account.bank.statement",
        "account.bank.statement.line",
    ]
    assert bank_report["handler_key"] == "report_bank_reconciliation"
    assert bank_report["source"]["models"] == bank_report_models
    assert bank_report["requirements"]["acl"] == [
        f"{model}:read" for model in bank_report_models
    ]
    assert bank_report["source"]["report_handlers"] == [
        "account.bank.reconciliation.report.handler"
    ]


def test_reference_object_reads_have_fixed_sources_and_closed_contracts() -> None:
    registry = load_registry()
    expected_modules = {
        "product.search": ["base", "product", "uom", "stock"],
        "product.get": ["base", "product", "uom", "stock"],
        "analytic.plan.list": ["analytic"],
        "analytic.plan.get": ["analytic"],
        "analytic.account.search": ["analytic", "base"],
        "analytic.account.get": ["analytic", "base"],
        "fiscal_position.search": ["account", "base"],
        "fiscal_position.get": ["account", "base"],
        "account.tag.list": ["account", "base"],
        "account.tag.get": ["account", "base"],
        "tax.group.list": ["account", "base"],
        "tax.group.get": ["account", "base"],
    }
    get_ids = {
        "product.get": "product_id",
        "analytic.plan.get": "plan_id",
        "analytic.account.get": "analytic_account_id",
        "fiscal_position.get": "fiscal_position_id",
        "account.tag.get": "tag_id",
        "tax.group.get": "tax_group_id",
    }
    request_fields = {
        "product.search": {"query", "active", "limit", "cursor"},
        "analytic.plan.list": {"limit", "cursor"},
        "analytic.account.search": {
            "query",
            "active",
            "plan_id",
            "limit",
            "cursor",
        },
        "fiscal_position.search": {
            "query",
            "active",
            "auto_apply",
            "limit",
            "cursor",
        },
        "account.tag.list": {"limit", "cursor"},
        "tax.group.list": {"limit", "cursor"},
    }
    item_fields = {
        "product.search": {
            "id",
            "name",
            "default_code",
            "active",
            "product_type",
            "is_storable",
            "template",
            "category",
            "uom",
            "company_id",
            "currency",
            "standard_price",
            "list_price",
        },
        "analytic.plan.list": {
            "id",
            "name",
            "complete_name",
            "parent",
            "color",
        },
        "analytic.account.search": {
            "id",
            "name",
            "code",
            "active",
            "plan",
            "partner",
            "company_id",
            "currency",
            "balance",
        },
        "fiscal_position.search": {
            "id",
            "name",
            "active",
            "auto_apply",
            "vat_required",
            "country",
            "country_group",
            "states",
            "company_id",
            "foreign_vat",
        },
        "account.tag.list": {
            "id",
            "name",
            "applicability",
            "active",
            "color",
            "country",
        },
        "tax.group.list": {
            "id",
            "name",
            "sequence",
            "company_id",
            "country",
            "preceding_subtotal",
        },
    }
    get_sources = {
        "product.get": "product.search",
        "analytic.plan.get": "analytic.plan.list",
        "analytic.account.get": "analytic.account.search",
        "fiscal_position.get": "fiscal_position.search",
        "account.tag.get": "account.tag.list",
        "tax.group.get": "tax.group.list",
    }
    unit_tests = [
        "tests/unit/test_core_object_reads.py",
        "tests/unit/test_core_object_reads_bridge.py",
        "tests/unit/test_core_object_reads_runtime.py",
        "tests/unit/test_core_object_read_cli.py",
        "tests/unit/test_capability_registry.py",
    ]

    assert set(expected_modules) == REFERENCE_OBJECT_BATCH_LIVE_READS
    for capability_id in REFERENCE_OBJECT_BATCH_LIVE_READS:
        descriptor = registry.describe(capability_id)
        models = list(CORE_OBJECT_READ_MODELS[capability_id])

        assert descriptor["access"] == "read"
        assert descriptor["handler_key"] == CORE_OBJECT_READ_HANDLERS[capability_id]
        assert descriptor["source"]["modules"] == expected_modules[capability_id]
        assert descriptor["source"]["models"] == models
        assert descriptor["source"]["wizards"] == []
        assert descriptor["source"]["report_handlers"] == []
        assert descriptor["requirements"] == {
            "modules": expected_modules[capability_id],
            "configuration": [
                "database_alias",
                "company_allowlist",
                "user_mapping",
            ],
            "company": "required",
            "groups": ["account.group_account_readonly"],
            "acl": [f"{model}:read" for model in models],
        }
        assert descriptor["status"]["value"] == "unconfigured"
        assert descriptor["status"]["reason_code"] == "runtime_context_required"
        assert descriptor["strategies"]["execute"] == (
            "fixed_company_scoped_core_object_read_action"
        )
        assert descriptor["tests"]["unit"] == {
            "status": "implemented",
            "references": unit_tests,
            "reason": descriptor["tests"]["unit"]["reason"],
        }
        assert descriptor["tests"]["integration"]["status"] == "implemented"
        assert descriptor["tests"]["integration"]["references"] == [
            "tests/integration/test_reference_object_read_batch_live.py"
        ]

        request_schema = registry.load_schema(descriptor["schemas"]["request"])
        response_schema = registry.load_schema(descriptor["schemas"]["response"])
        assert request_schema["additionalProperties"] is False
        assert response_schema["additionalProperties"] is False
        parameters = request_schema["$defs"]["parameters"]
        assert parameters["additionalProperties"] is False
        if capability_id in get_ids:
            assert parameters["required"] == [get_ids[capability_id]]
            assert set(parameters["properties"]) == {get_ids[capability_id]}
            source = get_sources[capability_id]
            assert response_schema["properties"]["data"]["oneOf"][1]["$ref"] == (
                f"{source}.response.schema.json#/$defs/item"
            )
        else:
            assert set(parameters["properties"]) == request_fields[capability_id]
            assert (
                set(response_schema["$defs"]["item"]["required"])
                == (item_fields[capability_id])
            )
            assert (
                set(response_schema["$defs"]["item"]["properties"])
                == (item_fields[capability_id])
            )

    tax_group = registry.load_schema("schemas/v1/tax.group.list.response.schema.json")[
        "$defs"
    ]["item"]
    assert tax_group["properties"]["company_id"] == {
        "type": "integer",
        "minimum": 1,
    }
    product = registry.load_schema("schemas/v1/product.search.response.schema.json")[
        "$defs"
    ]["item"]
    assert product["properties"]["category"] == {
        "anyOf": [{"$ref": "#/$defs/named"}, {"type": "null"}]
    }


def test_payment_reconciliation_reads_have_fixed_sources_and_contracts() -> None:
    registry = load_registry()
    expected_models = {
        "partner.bank_account.search": [
            "res.company",
            "res.partner.bank",
            "res.partner",
            "res.bank",
            "res.currency",
            "account.journal",
        ],
        "partner.bank_account.get": [
            "res.company",
            "res.partner.bank",
            "res.partner",
            "res.bank",
            "res.currency",
            "account.journal",
        ],
        "bank.statement.search": [
            "res.company",
            "account.bank.statement",
            "account.bank.statement.line",
            "account.journal",
            "res.currency",
        ],
        "bank.statement.get": [
            "res.company",
            "account.bank.statement",
            "account.bank.statement.line",
            "account.journal",
            "res.currency",
        ],
        "reconciliation.partial.list": [
            "res.company",
            "account.partial.reconcile",
            "account.move.line",
            "account.move",
            "res.currency",
        ],
        "reconciliation.partial.get": [
            "res.company",
            "account.partial.reconcile",
            "account.move.line",
            "account.move",
            "res.currency",
        ],
        "reconciliation.full.list": [
            "res.company",
            "account.full.reconcile",
            "account.partial.reconcile",
            "account.move.line",
        ],
        "reconciliation.full.get": [
            "res.company",
            "account.full.reconcile",
            "account.partial.reconcile",
            "account.move.line",
        ],
    }
    expected_parameters = {
        "partner.bank_account.search": {
            "partner_id",
            "active",
            "limit",
            "cursor",
        },
        "partner.bank_account.get": {"partner_bank_id"},
        "bank.statement.search": {
            "journal_id",
            "date_from",
            "date_to",
            "limit",
            "cursor",
        },
        "bank.statement.get": {"bank_statement_id"},
        "reconciliation.partial.list": {"limit", "cursor"},
        "reconciliation.partial.get": {"partial_reconcile_id"},
        "reconciliation.full.list": {"limit", "cursor"},
        "reconciliation.full.get": {"full_reconcile_id"},
    }
    page_item_fields = {
        "partner.bank_account.search": {
            "id",
            "acc_number",
            "account_holder_name",
            "account_type",
            "active",
            "sequence",
            "account_holder",
            "allow_out_payment",
            "bank",
            "currency",
            "company_id",
            "linked_journal",
        },
        "bank.statement.search": {
            "id",
            "name",
            "reference",
            "date",
            "company_id",
            "journal",
            "currency",
            "balance_start",
            "balance_end",
            "balance_end_real",
            "is_complete",
            "is_valid",
            "problem_description",
            "transaction_count",
        },
        "reconciliation.partial.list": {
            "id",
            "company_id",
            "max_date",
            "amount",
            "company_currency",
            "debit_amount_currency",
            "debit_currency",
            "credit_amount_currency",
            "credit_currency",
            "debit_journal_item_id",
            "credit_journal_item_id",
            "full_reconcile_id",
            "exchange_move_id",
            "matching_number",
        },
        "reconciliation.full.list": {
            "id",
            "company_id",
            "matching_number",
            "partial_reconcile_ids",
            "reconciled_journal_item_ids",
        },
    }
    get_sources = {
        "partner.bank_account.get": "partner.bank_account.search",
        "bank.statement.get": "bank.statement.search",
        "reconciliation.partial.get": "reconciliation.partial.list",
        "reconciliation.full.get": "reconciliation.full.list",
    }

    assert set(expected_models) == PAYMENT_RECONCILIATION_BATCH_LIVE_READS
    for capability_id in PAYMENT_RECONCILIATION_BATCH_LIVE_READS:
        descriptor = registry.describe(capability_id)
        models = expected_models[capability_id]
        assert descriptor["source"]["models"] == models
        assert descriptor["source"]["wizards"] == []
        assert descriptor["source"]["report_handlers"] == []
        assert descriptor["requirements"]["groups"] == [
            "account.group_account_readonly"
        ]
        assert descriptor["requirements"]["acl"] == [
            f"{model}:read" for model in models
        ]
        assert descriptor["strategies"]["execute"] == (
            "fixed_company_scoped_core_object_read_action"
        )
        assert descriptor["handler_key"] == CORE_OBJECT_READ_HANDLERS[capability_id]
        assert descriptor["tests"]["integration"]["references"] == [
            "tests/integration/test_payment_reconciliation_read_batch_live.py"
        ]

        request_schema = registry.load_schema(descriptor["schemas"]["request"])
        response_schema = registry.load_schema(descriptor["schemas"]["response"])
        parameters = request_schema["$defs"]["parameters"]
        assert request_schema["additionalProperties"] is False
        assert parameters["additionalProperties"] is False
        assert set(parameters["properties"]) == expected_parameters[capability_id]
        assert response_schema["additionalProperties"] is False
        if capability_id in get_sources:
            only_parameter = next(iter(expected_parameters[capability_id]))
            assert parameters["required"] == [only_parameter]
            source = get_sources[capability_id]
            assert response_schema["properties"]["data"]["oneOf"][1]["$ref"] == (
                f"{source}.response.schema.json#/$defs/item"
            )
        else:
            item = response_schema["$defs"]["item"]
            assert item["additionalProperties"] is False
            assert set(item["required"]) == page_item_fields[capability_id]
            assert set(item["properties"]) == page_item_fields[capability_id]

    full_item = registry.load_schema(
        "schemas/v1/reconciliation.full.list.response.schema.json"
    )["$defs"]["item"]
    for field in ("partial_reconcile_ids", "reconciled_journal_item_ids"):
        assert full_item["properties"][field]["minItems"] == 1
        assert full_item["properties"][field]["uniqueItems"] is True


def test_analytic_budget_reads_have_frozen_sources_acls_and_contracts() -> None:
    registry = load_registry()
    analytic_line_models = [
        "res.company",
        "account.analytic.line",
        "account.analytic.account",
        "res.partner",
        "res.currency",
        "product.product",
        "uom.uom",
        "account.account",
        "account.move.line",
    ]
    distribution_models = [
        "res.company",
        "account.analytic.distribution.model",
        "account.analytic.account",
        "res.partner",
        "res.partner.category",
        "product.product",
        "product.category",
    ]
    applicability_models = [
        "res.company",
        "account.analytic.applicability",
        "account.analytic.plan",
        "product.category",
    ]
    budget_models = ["res.company", "budget.analytic", "res.users"]
    budget_line_models = [
        "res.company",
        "budget.analytic",
        "budget.line",
        "res.currency",
        "account.analytic.plan",
        "account.analytic.account",
    ]
    report_models = [
        "res.company",
        "budget.report",
        "budget.analytic",
        "budget.line",
        "account.analytic.line",
        "account.analytic.plan",
        "account.analytic.account",
        "res.users",
    ]
    expected_models = {
        "analytic.line.get": analytic_line_models,
        "analytic.line.search": analytic_line_models,
        "analytic.distribution_model.get": distribution_models,
        "analytic.distribution_model.list": distribution_models,
        "analytic.applicability.get": applicability_models,
        "analytic.applicability.list": applicability_models,
        "budget.get": budget_models,
        "budget.search": budget_models,
        "budget.line.get": budget_line_models,
        "budget.line.list": budget_line_models,
        "report.budget": report_models,
    }
    expected_modules = {
        "analytic.line.get": ["account", "analytic", "base", "product", "uom"],
        "analytic.line.search": [
            "account",
            "analytic",
            "base",
            "product",
            "uom",
        ],
        "analytic.distribution_model.get": [
            "account",
            "analytic",
            "base",
            "product",
        ],
        "analytic.distribution_model.list": [
            "account",
            "analytic",
            "base",
            "product",
        ],
        "analytic.applicability.get": [
            "account",
            "analytic",
            "base",
            "product",
        ],
        "analytic.applicability.list": [
            "account",
            "analytic",
            "base",
            "product",
        ],
        "budget.get": ["account_budget", "account", "analytic", "base"],
        "budget.search": ["account_budget", "account", "analytic", "base"],
        "budget.line.get": ["account_budget", "account", "analytic", "base"],
        "budget.line.list": ["account_budget", "account", "analytic", "base"],
        "report.budget": ["account_budget", "account", "analytic", "base"],
    }
    analytic_line_locations = [
        "analytic/models/analytic_line.py",
        "account/models/account_analytic_line.py",
        "analytic/security/ir.model.access.csv",
        "analytic/security/analytic_security.xml",
        "account/security/ir.model.access.csv",
    ]
    distribution_locations = [
        "analytic/models/analytic_distribution_model.py",
        "account/models/account_analytic_distribution_model.py",
        "analytic/security/ir.model.access.csv",
        "analytic/security/analytic_security.xml",
        "account/security/ir.model.access.csv",
    ]
    applicability_locations = [
        "analytic/models/analytic_plan.py",
        "account/models/account_analytic_plan.py",
        "analytic/security/ir.model.access.csv",
        "analytic/security/analytic_security.xml",
        "account/security/ir.model.access.csv",
    ]
    budget_locations = [
        "account_budget/models/budget_analytic.py",
        "account_budget/security/ir.model.access.csv",
        "account_budget/security/account_budget_security.xml",
    ]
    budget_line_locations = [
        "account_budget/models/budget_line.py",
        "account_budget/models/budget_analytic.py",
        "account_budget/security/ir.model.access.csv",
        "account_budget/security/account_budget_security.xml",
        "analytic/models/analytic_line.py",
    ]
    expected_locations = {
        "analytic.line.get": analytic_line_locations,
        "analytic.line.search": analytic_line_locations,
        "analytic.distribution_model.get": distribution_locations,
        "analytic.distribution_model.list": distribution_locations,
        "analytic.applicability.get": applicability_locations,
        "analytic.applicability.list": applicability_locations,
        "budget.get": budget_locations,
        "budget.search": budget_locations,
        "budget.line.get": budget_line_locations,
        "budget.line.list": budget_line_locations,
        "report.budget": [
            "account_budget/reports/budget_report.py",
            "account_budget/models/budget_line.py",
            "account_budget/models/budget_analytic.py",
            "account_budget/security/ir.model.access.csv",
            "account_budget/security/account_budget_security.xml",
        ],
    }
    expected_parameters = {
        "analytic.line.search": {
            "query",
            "date_from",
            "date_to",
            "analytic_account_id",
            "limit",
            "cursor",
        },
        "analytic.line.get": {"analytic_line_id"},
        "analytic.distribution_model.list": {"limit", "cursor"},
        "analytic.distribution_model.get": {"distribution_model_id"},
        "analytic.applicability.list": {"limit", "cursor"},
        "analytic.applicability.get": {"applicability_id"},
        "budget.search": {
            "query",
            "state",
            "budget_type",
            "date_from",
            "date_to",
            "limit",
            "cursor",
        },
        "budget.get": {"budget_id"},
        "budget.line.list": {
            "budget_id",
            "plan_id",
            "analytic_account_id",
            "limit",
            "cursor",
        },
        "budget.line.get": {"budget_line_id"},
        "report.budget": {
            "budget_id",
            "budget_line_id",
            "date_from",
            "date_to",
            "plan_id",
            "analytic_account_id",
            "line_type",
            "limit",
            "cursor",
        },
    }
    page_item_fields = {
        "analytic.line.search": {
            "id",
            "date",
            "name",
            "reference",
            "amount",
            "unit_amount",
            "company_id",
            "currency",
            "analytic_accounts",
            "partner",
            "product",
            "uom",
            "general_account",
            "journal_item_id",
        },
        "analytic.distribution_model.list": {
            "id",
            "sequence",
            "company_id",
            "account_prefix",
            "partner",
            "partner_category",
            "product",
            "product_category",
            "allocations",
        },
        "analytic.applicability.list": {
            "id",
            "plan",
            "business_domain",
            "applicability",
            "company_id",
            "account_prefix",
            "product_category",
        },
        "budget.search": {
            "id",
            "name",
            "date_from",
            "date_to",
            "state",
            "budget_type",
            "company_id",
            "responsible",
            "revision_of",
        },
        "budget.line.list": {
            "id",
            "sequence",
            "budget",
            "date_from",
            "date_to",
            "budget_amount",
            "achieved_amount",
            "achieved_percentage",
            "theoretical_amount",
            "theoretical_percentage",
            "above_budget",
            "state",
            "currency",
            "company_id",
            "analytic_accounts",
        },
        "report.budget": {
            "row_key",
            "line_type",
            "date",
            "budget",
            "budget_line",
            "source",
            "description",
            "plan_accounts",
            "company_id",
            "user",
            "budget_amount",
            "achieved_amount",
            "theoretical_amount",
        },
    }
    get_sources = {
        "analytic.line.get": "analytic.line.search",
        "analytic.distribution_model.get": "analytic.distribution_model.list",
        "analytic.applicability.get": "analytic.applicability.list",
        "budget.get": "budget.search",
        "budget.line.get": "budget.line.list",
    }
    core_unit_tests = [
        "tests/unit/test_core_object_reads.py",
        "tests/unit/test_core_object_reads_bridge.py",
        "tests/unit/test_core_object_reads_runtime.py",
        "tests/unit/test_core_object_read_cli.py",
        "tests/unit/test_capability_registry.py",
    ]

    assert set(expected_models) == ANALYTIC_BUDGET_BATCH_LIVE_READS
    for capability_id in ANALYTIC_BUDGET_BATCH_LIVE_READS:
        descriptor = registry.describe(capability_id)
        models = expected_models[capability_id]
        assert descriptor["source"]["modules"] == expected_modules[capability_id]
        assert descriptor["source"]["models"] == models
        assert descriptor["source"]["wizards"] == []
        assert descriptor["source"]["report_handlers"] == []
        assert descriptor["source"]["locations"] == expected_locations[capability_id]
        assert descriptor["requirements"]["modules"] == expected_modules[capability_id]
        assert descriptor["requirements"]["configuration"] == [
            "database_alias",
            "company_allowlist",
            "user_mapping",
        ]
        assert descriptor["requirements"]["company"] == "required"
        assert descriptor["requirements"]["groups"] == [
            "account.group_account_user"
            if capability_id.startswith("analytic.applicability.")
            else "account.group_account_readonly"
        ]
        assert descriptor["requirements"]["acl"] == [
            f"{model}:read" for model in models
        ]
        assert descriptor["tests"]["integration"]["references"] == [
            "tests/integration/test_analytic_budget_read_batch_live.py"
        ]
        if capability_id == "report.budget":
            assert descriptor["handler_key"] == "budget_report"
            assert descriptor["strategies"]["execute"] == (
                "fixed_company_scoped_budget_report_read_action"
            )
            assert descriptor["tests"]["unit"]["references"] == [
                "tests/unit/test_budget_report.py",
                "tests/unit/test_budget_report_bridge.py",
                "tests/unit/test_budget_report_runtime.py",
                "tests/unit/test_budget_report_cli.py",
            ]
        else:
            assert descriptor["handler_key"] == CORE_OBJECT_READ_HANDLERS[capability_id]
            assert descriptor["strategies"]["execute"] == (
                "fixed_company_scoped_core_object_read_action"
            )
            assert descriptor["tests"]["unit"]["references"] == core_unit_tests

        request_schema = registry.load_schema(descriptor["schemas"]["request"])
        response_schema = registry.load_schema(descriptor["schemas"]["response"])
        parameters = request_schema["$defs"]["parameters"]
        assert request_schema["additionalProperties"] is False
        assert parameters["additionalProperties"] is False
        assert set(parameters["properties"]) == expected_parameters[capability_id]
        assert response_schema["additionalProperties"] is False
        if capability_id in get_sources:
            parameter = next(iter(expected_parameters[capability_id]))
            assert parameters["required"] == [parameter]
            source = get_sources[capability_id]
            assert response_schema["properties"]["data"]["oneOf"][1]["$ref"] == (
                f"{source}.response.schema.json#/$defs/item"
            )
        else:
            item = response_schema["$defs"]["item"]
            assert item["additionalProperties"] is False
            assert set(item["required"]) == page_item_fields[capability_id]
            assert set(item["properties"]) == page_item_fields[capability_id]

    for capability_id in ("budget.line.list", "report.budget"):
        parameters = registry.load_schema(
            f"schemas/v1/{capability_id}.request.schema.json"
        )["$defs"]["parameters"]
        assert len(parameters["oneOf"]) == 2

    analytic_line_item = registry.load_schema(
        "schemas/v1/analytic.line.search.response.schema.json"
    )["$defs"]["item"]
    assert analytic_line_item["properties"]["analytic_accounts"]["minItems"] == 1
    assert analytic_line_item["properties"]["analytic_accounts"]["uniqueItems"]
    distribution = registry.load_schema(
        "schemas/v1/analytic.distribution_model.list.response.schema.json"
    )
    assert "minItems" not in distribution["$defs"]["item"]["properties"]["allocations"]
    assert distribution["$defs"]["allocation"]["additionalProperties"] is False
    report_item = registry.load_schema("schemas/v1/report.budget.response.schema.json")[
        "$defs"
    ]["item"]
    assert report_item["properties"]["line_type"]["enum"] == [
        "budget",
        "achieved",
    ]
    assert report_item["properties"]["source"] == {"$ref": "#/$defs/source"}


def test_inventory_accounting_reads_match_the_fixed_runtime_and_contracts() -> None:
    registry = load_registry()
    handlers = {
        "cogs.entries.list": "cogs_entries_list",
        "inventory.accounting_entries.list": "inventory_accounting_entries_list",
        "purchase_bill.matching.inspect": "purchase_bill_matching_inspect",
        "report.inventory_valuation": "report_inventory_valuation",
        "sale_invoice.stock_link.inspect": "sale_invoice_stock_link_inspect",
    }
    expected_unit_tests = [
        "tests/unit/test_inventory_accounting.py",
        "tests/unit/test_inventory_accounting_bridge.py",
        "tests/unit/test_inventory_accounting_runtime.py",
        "tests/unit/test_inventory_accounting_cli.py",
        "tests/unit/test_capability_registry.py",
    ]
    expected_live_reason = (
        "The retained shared live smoke passed against both dedicated isolated "
        "database aliases as the ordinary accounting user, using read-only "
        "operations with no database commits."
    )

    assert set(INVENTORY_ACCOUNTING_MODELS) == set(handlers)
    assert set(INVENTORY_ACCOUNTING_ACCESS) == set(handlers)
    assert set(INVENTORY_ACCOUNTING_GROUPS) == set(handlers)
    for capability_id, handler_key in handlers.items():
        descriptor = registry.describe(capability_id)
        assert descriptor["handler_key"] == handler_key
        assert descriptor["schemas"] == {
            "request": f"schemas/v1/{capability_id}.request.schema.json",
            "response": f"schemas/v1/{capability_id}.response.schema.json",
        }
        assert descriptor["source"]["models"] == list(
            INVENTORY_ACCOUNTING_MODELS[capability_id]
        )
        assert descriptor["source"]["wizards"] == []
        assert descriptor["source"]["report_handlers"] == (
            ["stock_account.stock.valuation.report"]
            if capability_id == "report.inventory_valuation"
            else []
        )
        assert descriptor["requirements"]["modules"] == descriptor["source"]["modules"]
        assert descriptor["requirements"]["configuration"] == [
            "database_alias",
            "company_allowlist",
            "user_mapping",
        ]
        assert descriptor["requirements"]["groups"] == list(
            INVENTORY_ACCOUNTING_GROUPS[capability_id]
        )
        assert descriptor["requirements"]["acl"] == [
            f"{model}:{operation}"
            for model, operation in INVENTORY_ACCOUNTING_ACCESS[capability_id]
        ]
        assert descriptor["status"]["value"] == "unconfigured"
        assert descriptor["status"]["reason_code"] == "runtime_context_required"
        assert descriptor["strategies"]["execute"] != "implementation_pending"
        assert "pending" not in descriptor["strategies"]["verify"]
        assert descriptor["tests"]["unit"]["status"] == "implemented"
        assert descriptor["tests"]["unit"]["references"] == expected_unit_tests
        assert descriptor["tests"]["integration"]["status"] == "implemented"
        assert descriptor["tests"]["integration"]["references"] == [
            "tests/integration/test_inventory_accounting_batch_live.py"
        ]
        assert descriptor["tests"]["integration"]["reason"] == expected_live_reason
        for kind in ("request", "response"):
            schema = registry.load_schema(descriptor["schemas"][kind])
            assert schema["$id"].endswith(f"{capability_id}.{kind}.schema.json")


def test_inventory_reads_have_exact_models_acl_and_shared_evidence() -> None:
    registry = load_registry()
    expected_models = {
        "product.category.list": ["res.company", "product.category"],
        "warehouse.list": ["res.company", "stock.warehouse"],
        "stock.location.list": ["res.company", "stock.location"],
        "stock.operation_type.list": ["res.company", "stock.picking.type"],
        "stock.route.list": ["res.company", "stock.route"],
        "stock.transfer.search": [
            "res.company",
            "stock.picking",
            "stock.picking.type",
            "stock.location",
            "res.partner",
        ],
        "stock.transfer.get": [
            "res.company",
            "stock.picking",
            "stock.picking.type",
            "stock.location",
            "res.partner",
        ],
        "stock.move.search": [
            "res.company",
            "stock.move",
            "stock.picking",
            "product.product",
            "uom.uom",
            "stock.location",
        ],
        "inventory.on_hand.summary": [
            "res.company",
            "stock.quant",
            "stock.location",
            "stock.warehouse",
            "product.product",
            "uom.uom",
        ],
        "inventory.availability.inspect": [
            "res.company",
            "stock.quant",
            "stock.move",
            "stock.location",
            "stock.warehouse",
            "product.product",
            "uom.uom",
        ],
    }

    assert set(expected_models) == INVENTORY_READ_LIVE_READS
    for capability_id, models in expected_models.items():
        descriptor = registry.describe(capability_id)
        assert descriptor["handler_key"] == IMPLEMENTED_READS[capability_id]
        assert descriptor["source"]["models"] == models
        assert descriptor["requirements"]["groups"] == [
            "account.group_account_readonly"
        ]
        assert descriptor["requirements"]["acl"] == [
            f"{model}:read" for model in models
        ]
        assert descriptor["schemas"] == {
            "request": f"schemas/v1/{capability_id}.request.schema.json",
            "response": f"schemas/v1/{capability_id}.response.schema.json",
        }
        assert descriptor["tests"]["integration"]["status"] == "implemented"
        assert descriptor["tests"]["integration"]["references"] == [
            "tests/integration/test_inventory_read_batch_live.py"
        ]
        unit_references = descriptor["tests"]["unit"]["references"]
        assert "tests/unit/test_inventory_read_cli.py" in unit_references
        assert "tests/unit/test_capability_registry.py" in unit_references
        if capability_id in {
            "stock.transfer.search",
            "stock.transfer.get",
            "stock.move.search",
            "inventory.on_hand.summary",
            "inventory.availability.inspect",
        }:
            assert "tests/unit/test_inventory_operations_schemas.py" in unit_references


def test_order_document_reads_match_runtime_acl_and_shared_evidence() -> None:
    registry = load_registry()

    for capability_id in ORDER_DOCUMENT_LIVE_READS:
        descriptor = registry.describe(capability_id)
        models = list(order_document_required_models(capability_id))
        business_module = "sale" if capability_id.startswith("sale.") else "purchase"
        expected_modules = (
            ["base", business_module]
            if capability_id.endswith(".analysis.summary")
            else [
                "account",
                "base",
                business_module,
                f"{business_module}_stock",
                "stock",
            ]
        )

        assert descriptor["handler_key"] == IMPLEMENTED_READS[capability_id]
        assert descriptor["source"]["models"] == models
        assert descriptor["source"]["modules"] == expected_modules
        assert descriptor["requirements"]["modules"] == expected_modules
        assert descriptor["requirements"]["groups"] == [
            "account.group_account_readonly"
        ]
        assert descriptor["requirements"]["acl"] == [
            f"{model}:read" for model in models
        ]
        assert descriptor["tests"]["integration"]["references"] == [
            "tests/integration/test_order_documents_batch_live.py"
        ]
        assert set(descriptor["tests"]["unit"]["references"]) == {
            "tests/unit/test_order_documents.py",
            "tests/unit/test_order_documents_bridge.py",
            "tests/unit/test_order_documents_runtime.py",
            "tests/unit/test_order_documents_schemas.py",
            "tests/unit/test_order_documents_cli.py",
            "tests/unit/test_capability_registry.py",
        }


def test_implemented_writes_match_the_fixed_runtime_and_specialized_contracts() -> None:
    registry = load_registry()
    core_unit_tests = {
        "tests/unit/test_core_writes.py",
        "tests/unit/test_core_writes_bridge.py",
        "tests/unit/test_core_writes_runtime.py",
        "tests/unit/test_core_write_cli.py",
    }
    document_lifecycle_unit_tests = {
        "tests/unit/test_document_lifecycle_writes.py",
        "tests/unit/test_document_lifecycle_writes_runtime.py",
        "tests/unit/test_core_writes_bridge.py",
        "tests/unit/test_core_write_cli.py",
        "tests/unit/test_document_lifecycle_write_cli.py",
    }
    payment_bank_unit_tests = {
        "tests/unit/test_payment_bank_writes.py",
        "tests/unit/test_payment_bank_writes_runtime.py",
        "tests/unit/test_payment_bank_write_cli.py",
    }
    analytic_budget_unit_tests = {
        "tests/unit/test_analytic_budget_writes.py",
        "tests/unit/test_analytic_budget_writes_runtime.py",
        "tests/unit/test_analytic_budget_write_cli.py",
        "tests/unit/test_analytic_budget_write_registry.py",
    }
    order_document_unit_tests = {
        "tests/unit/test_order_document_writes.py",
        "tests/unit/test_order_document_writes_runtime.py",
        "tests/unit/test_order_document_write_cli.py",
        "tests/unit/test_order_document_write_schemas.py",
    }
    stock_transfer_batch_writes = {
        "sale.order.invoice.create",
        "stock.transfer.create",
        "stock.transfer.confirm",
        "stock.transfer.assign",
        "stock.transfer.quantities.set",
        "stock.transfer.validate",
        "stock.transfer.unreserve",
        "stock.transfer.cancel",
    }
    stock_transfer_unit_tests = {
        "tests/unit/test_stock_transfer_writes.py",
        "tests/unit/test_stock_transfer_write_schemas.py",
        "tests/unit/test_stock_transfer_writes_runtime.py",
        "tests/unit/test_stock_transfer_write_cli.py",
    }
    expected_wizards = {
        "customer_credit_note.create": {"account.move.reversal"},
        "journal_entry.reverse": {"account.move.reversal"},
        "asset.dispose": {"asset.modify"},
        "asset.pause": {"asset.modify"},
        "multicurrency.revaluation.generate_entries": {
            "account.multicurrency.revaluation.wizard"
        },
        "reconciliation.automatic.run": {"account.auto.reconcile.wizard"},
        "receivable.payment.register": {"account.payment.register"},
        "payable.payment.register": {"account.payment.register"},
        "vendor_refund.create": {"account.move.reversal"},
        "period.accrual.generate": {"account.accrued.orders.wizard"},
    }
    extended_modules = {
        "analytic.account.create": ["analytic", "account", "base"],
        "analytic.account.update": ["analytic", "account", "base"],
        "asset.cancel": ["account_asset"],
        "asset.dispose": ["account_asset"],
        "asset.pause": ["account_asset"],
        "deferred_expense.generate_entries": ["account_reports"],
        "deferred_revenue.generate_entries": ["account_reports"],
        "multicurrency.revaluation.generate_entries": ["account_reports"],
        "reconciliation.automatic.run": ["account", "account_accountant"],
        "period.transfer.run": ["account_transfer"],
        "localization.china.period_transfer.run": [
            "l10n_cn_reports",
            "account_transfer",
        ],
        "budget.cancel": ["account_budget", "account", "analytic", "base"],
        "budget.confirm": ["account_budget", "account", "analytic", "base"],
        "budget.create": ["account_budget", "account", "analytic", "base"],
        "budget.lines.replace": [
            "account_budget",
            "account",
            "analytic",
            "base",
        ],
        "budget.mark_done": ["account_budget", "account", "analytic", "base"],
        "budget.reset_to_draft": [
            "account_budget",
            "account",
            "analytic",
            "base",
        ],
        "budget.update_draft": [
            "account_budget",
            "account",
            "analytic",
            "base",
        ],
        "partner.accounting.update": ["base", "account"],
        "partner.archive": ["base", "account"],
        "partner.bank_account.archive": ["base", "account"],
        "partner.bank_account.create": ["base", "account"],
        "partner.bank_account.restore": ["base", "account"],
        "partner.bank_account.update": ["base", "account"],
        "partner.create": ["base", "account"],
        "partner.restore": ["base", "account"],
        "partner.update": ["base", "account"],
        "purchase.order.bill.create": ["purchase", "account"],
        "purchase_bill.match": ["purchase", "account"],
        "purchase_bill.lines.unmatch": ["purchase", "account"],
        "payment_term.create": ["account"],
        "payment_term.update": ["account"],
        "payment_term.lines.replace": ["account"],
        "payment_term.archive": ["account"],
        "payment_term.restore": ["account"],
        "period.accrual.generate": ["account"],
    }
    extended_modules.update(
        {
            capability_id: ["account", "base"]
            for capability_id in FISCAL_POSITION_JOURNAL_GROUP_WRITES
        }
    )
    extended_modules.update(
        {
            "currency.rate.record": ["account", "base"],
            "account.group.create": ["account", "base"],
            "account.group.update": ["account", "base"],
            "tax.repartition_lines.replace": ["account", "base"],
            "reconciliation.model.create": [
                "account",
                "account_accountant",
                "base",
            ],
            "reconciliation.model.update": [
                "account",
                "account_accountant",
                "base",
            ],
            "reconciliation.model.lines.replace": [
                "account",
                "account_accountant",
                "analytic",
                "base",
            ],
            "reconciliation.model.archive": [
                "account",
                "account_accountant",
                "base",
            ],
            "reconciliation.model.restore": [
                "account",
                "account_accountant",
                "base",
            ],
        }
    )
    extended_modules.update(
        {
            capability_id: ["account", "base", "sale", "sale_stock", "stock"]
            for capability_id in ORDER_DOCUMENT_WRITES
            if capability_id.startswith("sale.order.")
        }
    )
    extended_modules.update(
        {
            "sale.order.invoice.create": ["account", "base", "sale", "sale_stock"],
            "stock.transfer.create": ["base", "stock"],
            "stock.transfer.confirm": ["base", "stock"],
            "stock.transfer.assign": ["base", "stock"],
            "stock.transfer.quantities.set": ["base", "stock"],
            "stock.transfer.validate": ["account", "base", "stock", "stock_account"],
            "stock.transfer.unreserve": ["base", "stock"],
            "stock.transfer.cancel": ["base", "stock"],
        }
    )
    runtime_support_models = {
        "purchase_bill.match": {
            "res.partner",
            "product.product",
            "purchase.order",
        },
    }
    runtime_support_acl = {
        "purchase.order.bill.create": {"res.company:read"},
        "purchase_bill.match": {
            "res.company:read",
            "res.partner:read",
            "product.product:read",
            "purchase.order:read",
            "purchase.bill.line.match:read",
        },
        "purchase_bill.lines.unmatch": {"res.company:read"},
        "payment_term.create": {"account.payment.term.line:write"},
        "period.accrual.generate": {"res.company:read"},
    }
    extended_modules.update(
        {
            capability_id: [
                "account",
                "base",
                "purchase",
                "purchase_stock",
                "stock",
            ]
            for capability_id in ORDER_DOCUMENT_WRITES
            if capability_id.startswith("purchase.order.")
        }
    )
    extended_modules.update(
        {
            capability_id: ["account", "base"]
            for capability_id in ACCOUNTING_MASTER_DATA_COMPLETION_WRITES
        }
    )
    extended_modules.update(
        {
            "fiscal_year.create": ["account_accountant"],
            "fiscal_year.update": ["account_accountant"],
            "analytic.applicability.create": [
                "account",
                "analytic",
                "base",
                "product",
            ],
            "analytic.applicability.update": [
                "account",
                "analytic",
                "base",
                "product",
            ],
            "analytic.distribution_model.create": [
                "account",
                "analytic",
                "base",
                "product",
            ],
            "analytic.distribution_model.update": [
                "account",
                "analytic",
                "base",
                "product",
            ],
        }
    )

    assert set(CORE_WRITE_MODELS) == IMPLEMENTED_WRITES
    assert set(CORE_WRITE_ACCESS) == IMPLEMENTED_WRITES
    assert set(CORE_WRITE_GROUPS) == IMPLEMENTED_WRITES
    for capability_id in IMPLEMENTED_WRITES:
        descriptor = registry.describe(capability_id)
        assert descriptor["handler_key"] == "core_write"
        assert descriptor["schemas"] == {
            "request": f"schemas/v1/{capability_id}.request.schema.json",
            "response": f"schemas/v1/{capability_id}.response.schema.json",
        }
        assert descriptor["source"]["modules"] == extended_modules.get(
            capability_id,
            ["account", "base"]
            if capability_id in ACCOUNTING_CONFIG_WRITES
            else ["account_asset"]
            if capability_id.startswith("asset.")
            else ["account"],
        )
        expected_runtime_models = (
            set(descriptor["source"]["models"])
            | set(descriptor["source"]["wizards"])
            | {"res.company"}
            | runtime_support_models.get(capability_id, set())
        )
        assert CORE_WRITE_MODELS[capability_id] == expected_runtime_models
        assert set(descriptor["source"]["wizards"]) == expected_wizards.get(
            capability_id, set()
        )
        assert descriptor["requirements"]["configuration"] == [
            "database_alias",
            "company_allowlist",
            "user_mapping",
        ]
        expected_groups = [CORE_WRITE_GROUPS[capability_id]]
        if capability_id == "partner.accounting.update":
            expected_groups.append("base.group_partner_manager")
        assert descriptor["requirements"]["groups"] == expected_groups
        expected_acl = {
            f"{model}:{operation}"
            for model, operation in CORE_WRITE_ACCESS[capability_id]
        }
        if capability_id in PARTNER_MASTER_DATA_WRITES:
            expected_acl.add("res.company:read")
        expected_acl -= runtime_support_acl.get(capability_id, set())
        assert set(descriptor["requirements"]["acl"]) == expected_acl
        if capability_id in {
            "account.tag.archive",
            "account.tag.create",
            "account.tag.restore",
            "account.tag.update",
            "cash_rounding.create",
            "cash_rounding.update",
        }:
            assert descriptor["status"]["value"] == "degraded"
            assert (
                descriptor["status"]["reason_code"]
                == "database_global_record_scope"
            )
        elif capability_id in {
            "account.account.create",
            "account.group.create",
            "reconciliation.model.create",
            "tax.group.create",
            "tax.create",
            "fiscal_year.create",
            "analytic.applicability.create",
            "analytic.distribution_model.create",
        }:
            assert descriptor["status"]["value"] == "degraded"
            assert descriptor["status"]["reason_code"] == "concurrent_idempotency_limit"
        elif capability_id == "analytic.account.create":
            assert descriptor["status"]["value"] == "degraded"
            assert (
                descriptor["status"]["reason_code"]
                == "odoo_native_analytic_account_idempotency_field_unavailable"
            )
        elif capability_id == "budget.create":
            assert descriptor["status"]["value"] == "degraded"
            assert (
                descriptor["status"]["reason_code"]
                == "odoo_native_budget_idempotency_field_unavailable"
            )
        elif capability_id == "partner.create":
            assert descriptor["status"]["value"] == "degraded"
            assert (
                descriptor["status"]["reason_code"]
                == "odoo_native_partner_ref_idempotency_field_unavailable"
            )
        elif capability_id == "asset.create":
            assert descriptor["status"]["value"] == "degraded"
            assert (
                descriptor["status"]["reason_code"]
                == "odoo_native_asset_idempotency_field_unavailable"
            )
        elif capability_id == "asset.validate":
            assert descriptor["status"]["value"] == "degraded"
            assert (
                descriptor["status"]["reason_code"]
                == "server_exchange_currency_constraint_broken"
            )
        elif capability_id == "asset.pause":
            assert descriptor["status"]["value"] == "degraded"
            assert (
                descriptor["status"]["reason_code"]
                == "odoo_asset_pause_date_not_persisted"
            )
        elif capability_id == "sale.order.invoice.create":
            assert descriptor["status"]["value"] == "degraded"
            assert (
                descriptor["status"]["reason_code"]
                == "odoo_linked_invoice_not_concurrency_unique"
            )
        elif capability_id == "stock.transfer.create":
            assert descriptor["status"]["value"] == "degraded"
            assert (
                descriptor["status"]["reason_code"]
                == "odoo_stock_transfer_marker_not_concurrency_unique"
            )
        elif capability_id in {"sale.order.create", "purchase.order.create"}:
            assert descriptor["status"]["value"] == "degraded"
            assert (
                descriptor["status"]["reason_code"]
                == "odoo_order_marker_not_concurrency_unique"
            )
        elif capability_id in {
            "deferred_expense.generate_entries",
            "deferred_revenue.generate_entries",
            "multicurrency.revaluation.generate_entries",
        }:
            assert descriptor["status"]["value"] == "degraded"
            assert (
                descriptor["status"]["reason_code"]
                == "odoo_move_pair_marker_not_concurrency_unique"
            )
        elif capability_id in TRANSFER_WRITES:
            assert descriptor["status"]["value"] == "degraded"
            assert (
                descriptor["status"]["reason_code"]
                == "odoo_transfer_marker_not_concurrency_unique"
            )
        elif capability_id == "purchase.order.bill.create":
            assert descriptor["status"]["value"] == "degraded"
            assert (
                descriptor["status"]["reason_code"]
                == "odoo_linked_bill_not_concurrency_unique"
            )
        elif capability_id == "payment_term.create":
            assert descriptor["status"]["value"] == "degraded"
            assert (
                descriptor["status"]["reason_code"]
                == "odoo_payment_term_name_not_concurrency_unique"
            )
        elif capability_id == "fiscal_position.create":
            assert descriptor["status"]["value"] == "degraded"
            assert (
                descriptor["status"]["reason_code"]
                == "odoo_fiscal_position_name_not_concurrency_unique"
            )
        elif capability_id == "period.accrual.generate":
            assert descriptor["status"]["value"] == "degraded"
            assert (
                descriptor["status"]["reason_code"]
                == "odoo_accrual_pair_not_concurrency_unique"
            )
        else:
            assert descriptor["status"]["value"] == "unconfigured"
            assert descriptor["status"]["reason_code"] == "runtime_context_required"
        if capability_id in ACCOUNTING_RULES_FISCAL_YEAR_WRITES:
            assert descriptor["tests"]["unit"]["status"] == "implemented"
            assert set(descriptor["tests"]["unit"]["references"]) == {
                "tests/unit/test_core_writes.py",
                "tests/unit/test_core_writes_runtime.py",
                "tests/unit/test_accounting_rules_fiscal_year_contracts.py",
                "tests/unit/test_accounting_rules_fiscal_year_registry.py",
            }
            assert descriptor["tests"]["integration"]["status"] == "implemented"
            assert descriptor["tests"]["integration"]["references"] == [
                "tests/integration/test_accounting_rules_fiscal_year_live.py"
            ]
            continue
        if capability_id in ACCOUNTING_MASTER_DATA_COMPLETION_WRITES:
            assert descriptor["tests"]["unit"]["status"] == "implemented"
            assert set(descriptor["tests"]["unit"]["references"]) == {
                "tests/unit/test_core_writes.py",
                "tests/unit/test_core_writes_runtime.py",
                "tests/unit/test_accounting_master_data_completion_contracts.py",
                "tests/unit/test_accounting_master_data_completion_registry.py",
            }
            assert descriptor["tests"]["integration"]["status"] == "implemented"
            assert descriptor["tests"]["integration"]["references"] == [
                "tests/integration/test_accounting_master_data_completion_live.py"
            ]
            continue
        if capability_id in ACCOUNTING_CONFIGURATION_EXPANSION_WRITES:
            assert descriptor["tests"]["unit"]["status"] == "implemented"
            assert set(descriptor["tests"]["unit"]["references"]) == {
                "tests/unit/test_core_writes.py",
                "tests/unit/test_core_writes_runtime.py",
                "tests/unit/test_accounting_configuration_write_contracts.py",
                "tests/unit/test_accounting_configuration_expansion_registry.py",
            }
            assert descriptor["tests"]["integration"]["status"] == "implemented"
            assert descriptor["tests"]["integration"]["references"] == [
                "tests/integration/test_accounting_configuration_expansion_live.py"
            ]
            continue
        if capability_id in FISCAL_POSITION_JOURNAL_GROUP_WRITES:
            assert descriptor["tests"]["unit"]["status"] == "implemented"
            assert set(descriptor["tests"]["unit"]["references"]) == {
                "tests/unit/test_core_writes.py",
                "tests/unit/test_core_writes_runtime.py",
                "tests/unit/test_core_write_cli.py",
                "tests/unit/test_fiscal_position_journal_group_writes.py",
                "tests/unit/test_fiscal_position_journal_group_writes_runtime.py",
            }
            assert descriptor["tests"]["integration"]["status"] == "implemented"
            assert descriptor["tests"]["integration"]["references"] == [
                "tests/integration/test_accounting_configuration_batch_live.py"
            ]
            continue
        if capability_id in ACCOUNTING_CONFIG_WRITES:
            assert descriptor["tests"]["unit"]["status"] == "implemented"
            assert descriptor["tests"]["unit"]["references"] == [
                "tests/unit/test_accounting_config_writes.py",
                "tests/unit/test_accounting_config_writes_runtime.py",
                "tests/unit/test_accounting_config_write_cli.py",
                "tests/unit/test_accounting_config_write_registry.py",
            ]
            assert descriptor["tests"]["integration"]["status"] == "implemented"
            assert descriptor["tests"]["integration"]["references"] == [
                "tests/integration/test_accounting_config_write_batch_live.py"
            ]
            continue
        if capability_id in PARTNER_MASTER_DATA_WRITES:
            assert descriptor["tests"]["unit"]["status"] == "implemented"
            assert descriptor["tests"]["unit"]["references"] == [
                "tests/unit/test_partner_master_data.py",
                "tests/unit/test_partner_master_data_runtime.py",
                "tests/unit/test_partner_master_data_cli.py",
                "tests/unit/test_partner_master_data_registry.py",
            ]
            assert descriptor["tests"]["integration"]["status"] == "implemented"
            assert descriptor["tests"]["integration"]["references"] == [
                "tests/integration/test_partner_master_data_batch_live.py"
            ]
            continue
        if capability_id in PROCUREMENT_FOLLOWUP_WRITES:
            expected_references = (
                {
                    "tests/unit/test_procurement_inventory_writes.py",
                    "tests/unit/test_procurement_inventory_writes_runtime.py",
                    "tests/unit/test_procurement_inventory_write_schemas.py",
                    "tests/unit/test_core_write_cli.py",
                }
                if capability_id.startswith("purchase")
                else {
                    "tests/unit/test_procurement_inventory_writes.py",
                    "tests/unit/test_payment_term_accrual_writes_runtime.py",
                    "tests/unit/test_payment_term_accrual_write_schemas.py",
                    "tests/unit/test_core_write_cli.py",
                }
            )
            assert descriptor["tests"]["unit"]["status"] == "implemented"
            assert set(descriptor["tests"]["unit"]["references"]) == (
                expected_references
            )
            assert descriptor["tests"]["integration"]["status"] == "implemented"
            assert descriptor["tests"]["integration"]["references"] == [
                "tests/integration/test_accounting_followup_write_batch_live.py"
            ]
            continue
        assert descriptor["tests"]["unit"]["status"] == "implemented"
        expected_unit_tests = (
            set(stock_transfer_unit_tests)
            if capability_id in stock_transfer_batch_writes
            else (
                set(order_document_unit_tests)
                if capability_id in ORDER_DOCUMENT_WRITES
                else (
                    set(analytic_budget_unit_tests)
                    if capability_id in ANALYTIC_BUDGET_WRITES
                    else (
                        set(payment_bank_unit_tests)
                        if capability_id in PAYMENT_BANK_WRITES
                        else (
                            set(document_lifecycle_unit_tests)
                            if capability_id in DOCUMENT_LIFECYCLE_WRITES
                            else set(core_unit_tests)
                        )
                    )
                )
            )
        )
        if capability_id in EXTENDED_WRITES:
            expected_unit_tests.add("tests/unit/test_extended_core_writes.py")
        assert set(descriptor["tests"]["unit"]["references"]) == expected_unit_tests
        if capability_id in stock_transfer_batch_writes:
            assert descriptor["tests"]["integration"]["status"] == "implemented"
            assert descriptor["tests"]["integration"]["references"] == [
                "tests/integration/test_stock_transfer_write_batch_live.py"
            ]
        elif capability_id in ORDER_DOCUMENT_WRITES:
            assert descriptor["tests"]["integration"]["status"] == "implemented"
            assert descriptor["tests"]["integration"]["references"] == [
                "tests/integration/test_order_document_write_batch_live.py"
            ]
        elif capability_id in ACCOUNTING_DEPTH_WRITES:
            expected_live_test = (
                "tests/integration/test_document_lifecycle_write_batch_live.py"
                if capability_id in DOCUMENT_LIFECYCLE_WRITES
                else "tests/integration/test_core_write_batch_live.py"
            )
            assert descriptor["tests"]["integration"]["status"] == "implemented"
            assert descriptor["tests"]["integration"]["references"] == [
                expected_live_test,
                "tests/integration/test_accounting_depth_batch_live.py",
            ]
        elif capability_id in DOCUMENT_LIFECYCLE_WRITES:
            assert descriptor["tests"]["integration"]["status"] == "implemented"
            assert descriptor["tests"]["integration"]["references"] == [
                "tests/integration/test_document_lifecycle_write_batch_live.py"
            ]
        elif capability_id in ANALYTIC_BUDGET_WRITES:
            assert descriptor["tests"]["integration"]["status"] == "implemented"
            assert descriptor["tests"]["integration"]["references"] == [
                "tests/integration/test_analytic_budget_write_batch_live.py"
            ]
            assert "immediate replay" in descriptor["tests"]["integration"]["reason"]
        elif capability_id in PAYMENT_BANK_WRITES:
            assert descriptor["tests"]["integration"]["status"] == "implemented"
            assert descriptor["tests"]["integration"]["references"] == [
                "tests/integration/test_payment_bank_capability_batch_live.py"
            ]
        elif capability_id in FAILED_LIVE_WRITES:
            assert descriptor["tests"]["integration"]["status"] == "failed"
            assert descriptor["tests"]["integration"]["references"] == [
                "tests/integration/test_asset_batch_live.py"
            ]
            assert "Expected singleton" in descriptor["tests"]["integration"]["reason"]
            assert "rollback" in descriptor["tests"]["integration"]["reason"]
        elif capability_id in EXTENDED_WRITES:
            assert descriptor["tests"]["integration"]["status"] == "implemented"
            assert descriptor["tests"]["integration"]["references"] == [
                "tests/integration/test_extended_write_batch_live.py"
            ]
        elif capability_id == "asset.create":
            assert descriptor["tests"]["integration"]["status"] == "implemented"
            assert descriptor["tests"]["integration"]["references"] == [
                "tests/integration/test_asset_batch_live.py"
            ]
        else:
            assert descriptor["tests"]["integration"]["status"] == "implemented"
            assert descriptor["tests"]["integration"]["references"] == [
                "tests/integration/test_core_write_batch_live.py"
            ]
        for kind in ("request", "response"):
            schema = registry.load_schema(descriptor["schemas"][kind])
            assert schema["$id"].endswith(f"{capability_id}.{kind}.schema.json")
            if "additionalProperties" in schema:
                assert schema["additionalProperties"] is False
            else:
                assert any(
                    branch.get("$ref") == f"{kind}.schema.json"
                    for branch in schema["allOf"]
                )
                base_schema = registry.load_schema(f"schemas/v1/{kind}.schema.json")
                assert base_schema["additionalProperties"] is False
                if kind == "request":
                    parameter_contracts = [
                        branch.get("properties", {}).get("parameters")
                        for branch in [schema, *schema.get("allOf", [])]
                    ]
                    assert any(
                        isinstance(contract, dict)
                        and (
                            contract.get("additionalProperties") is False
                            or (
                                isinstance(contract.get("oneOf"), list)
                                and bool(contract["oneOf"])
                                and all(
                                    isinstance(option, dict)
                                    and option.get("additionalProperties") is False
                                    for option in contract["oneOf"]
                                )
                            )
                        )
                        for contract in parameter_contracts
                    )
                else:
                    capability_contracts = [
                        branch.get("properties", {}).get("capability")
                        for branch in [schema, *schema.get("allOf", [])]
                    ]
                    assert {"const": capability_id} in capability_contracts


def test_payment_bank_batch_has_exact_registry_and_schema_contracts() -> None:
    registry = load_registry()
    read_models = {
        "bank.transaction.search": {
            "res.company",
            "account.bank.statement.line",
            "account.move",
            "account.journal",
            "res.partner",
            "res.currency",
            "account.payment",
        },
        "bank.transaction.reconciliation.get": {
            "res.company",
            "account.bank.statement.line",
            "account.move",
            "account.move.line",
            "account.account",
            "res.partner",
            "res.currency",
            "account.payment",
            "account.partial.reconcile",
            "account.full.reconcile",
        },
        "bank.transaction.match_candidates.list": {
            "res.company",
            "account.bank.statement.line",
            "account.move",
            "account.move.line",
            "account.account",
            "account.journal",
            "res.partner",
            "res.currency",
            "account.reconcile.model",
        },
    }
    request_fields = {
        "bank.transaction.search": {
            "date_from",
            "date_to",
            "journal_id",
            "partner_id",
            "reconciled",
            "query",
            "limit",
            "cursor",
        },
        "bank.transaction.reconciliation.get": {"transaction_id"},
        "bank.transaction.match_candidates.list": {
            "transaction_id",
            "limit",
            "cursor",
        },
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
    }

    assert set(read_models) == PAYMENT_BANK_BATCH_READS
    assert set(request_fields) == PAYMENT_BANK_BATCH_READS | PAYMENT_BANK_WRITES
    for capability_id, models in read_models.items():
        descriptor = registry.describe(capability_id)
        assert descriptor["access"] == "read"
        assert descriptor["handler_key"] == IMPLEMENTED_READS[capability_id]
        assert set(descriptor["source"]["models"]) == models
        assert set(descriptor["requirements"]["acl"]) == {
            f"{model}:read" for model in models
        }
        assert descriptor["requirements"]["groups"] == [
            "account.group_account_readonly"
        ]

    for capability_id, expected_fields in request_fields.items():
        descriptor = registry.describe(capability_id)
        request_schema = registry.load_schema(descriptor["schemas"]["request"])
        response_schema = registry.load_schema(descriptor["schemas"]["response"])
        assert request_schema["additionalProperties"] is False
        assert (
            set(request_schema["properties"]["parameters"]["properties"])
            == expected_fields
        )
        if capability_id in PAYMENT_BANK_WRITES:
            data_contracts = [
                branch.get("properties", {}).get("data")
                for branch in response_schema["allOf"]
            ]
            assert {
                "oneOf": [
                    {"type": "null"},
                    {"$ref": "core-write-result.schema.json"},
                ]
            } in data_contracts

    create_parameters = registry.load_schema(
        "schemas/v1/payment.create.request.schema.json"
    )["properties"]["parameters"]
    assert set(create_parameters["required"]) == request_fields["payment.create"] - {
        "payment_reference"
    }
    payment_changes = registry.load_schema(
        "schemas/v1/payment.update_draft.request.schema.json"
    )["properties"]["parameters"]["properties"]["changes"]
    assert payment_changes["minProperties"] == 1
    assert set(payment_changes["properties"]) == request_fields["payment.create"]
    bank_changes = registry.load_schema(
        "schemas/v1/bank.transaction.update.request.schema.json"
    )["properties"]["parameters"]["properties"]["changes"]
    assert bank_changes["minProperties"] == 1
    assert set(bank_changes["properties"]) == {
        "date",
        "amount",
        "payment_ref",
        "partner_id",
    }
    candidate_ids = registry.load_schema(
        "schemas/v1/bank.transaction.match.request.schema.json"
    )["properties"]["parameters"]["properties"]["candidate_line_ids"]
    assert candidate_ids["minItems"] == 1
    assert candidate_ids["maxItems"] == 50
    assert candidate_ids["uniqueItems"] is True

    search_response = registry.load_schema(
        "schemas/v1/bank.transaction.search.response.schema.json"
    )
    assert search_response["properties"]["data"]["oneOf"][1]["$ref"] == (
        "bank.transaction.list.response.schema.json#/$defs/data"
    )
    candidates_response = registry.load_schema(
        "schemas/v1/bank.transaction.match_candidates.list.response.schema.json"
    )
    assert candidates_response["properties"]["data"]["oneOf"][1]["$ref"] == (
        "reconciliation.candidates.list.response.schema.json#/$defs/data"
    )
    reconciliation_data = registry.load_schema(
        "schemas/v1/bank.transaction.reconciliation.get.response.schema.json"
    )["$defs"]["data"]
    assert set(reconciliation_data["required"]) == {
        "transaction",
        "liquidity_line",
        "suspense_line",
        "matched_lines",
        "writeoff_lines",
        "payment_ids",
    }


def test_reconciliation_candidates_has_the_closed_source_and_acl_gates() -> None:
    descriptor = load_registry().describe("reconciliation.candidates.list")
    models = [
        "res.company",
        "account.move.line",
        "account.move",
        "account.account",
        "account.journal",
        "res.partner",
        "res.currency",
        "account.reconcile.model",
    ]

    assert descriptor["source"]["modules"] == ["account", "account_accountant"]
    assert descriptor["source"]["models"] == models
    assert descriptor["source"]["wizards"] == ["account.reconcile.wizard"]
    assert descriptor["source"]["locations"] == [
        "_references/base/models/res_company.py",
        "account/models/account_move_line.py",
        "account/models/account_move.py",
        "account/models/account_account.py",
        "account/models/account_journal.py",
        "_references/base/models/res_partner.py",
        "_references/base/models/res_currency.py",
        "account/models/account_reconcile_model.py",
        "account_accountant/models/account_reconcile_model.py",
        "account_accountant/models/account_reconcile_model_line.py",
        "account_accountant/views/account_reconcile_views.xml",
        "account_accountant/wizard/account_reconcile_wizard.py",
    ]
    assert descriptor["requirements"]["acl"] == [f"{model}:read" for model in models]
    assert descriptor["handler_key"] == "reconciliation_candidates_list"
    assert descriptor["tests"]["unit"]["references"] == [
        "tests/unit/test_reconciliation_candidates.py",
        "tests/unit/test_reconciliation_candidate_bridge.py",
        "tests/unit/test_reconciliation_candidates_runtime.py",
        "tests/unit/test_reconciliation_candidates_cli.py",
    ]
    for kind in ("request", "response"):
        schema = load_registry().load_schema(descriptor["schemas"][kind])
        assert schema["$id"].endswith(
            f"reconciliation.candidates.list.{kind}.schema.json"
        )
        assert schema["additionalProperties"] is False


def test_currency_rate_list_has_the_closed_base_source_and_acl_gates() -> None:
    descriptor = load_registry().describe("currency.rate.list")
    models = ["res.company", "res.currency.rate", "res.currency", "res.users"]

    assert descriptor["source"] == {
        "modules": ["base"],
        "models": models,
        "wizards": [],
        "report_handlers": [],
        "locations": [
            "_references/base/models/res_company.py",
            "_references/base/models/res_currency.py",
            "_references/base/models/res_users.py",
        ],
    }
    assert descriptor["requirements"]["modules"] == ["base"]
    assert descriptor["requirements"]["groups"] == ["base.group_user"]
    assert descriptor["requirements"]["acl"] == [f"{model}:read" for model in models]
    assert descriptor["handler_key"] == "currency_rate_list"
    assert descriptor["tests"]["unit"]["references"] == [
        "tests/unit/test_currency_rates.py",
        "tests/unit/test_currency_rate_bridge.py",
        "tests/unit/test_currency_rate_runtime.py",
        "tests/unit/test_currency_rate_cli.py",
    ]
    for kind in ("request", "response"):
        schema = load_registry().load_schema(descriptor["schemas"][kind])
        assert schema["$id"].endswith(f"currency.rate.list.{kind}.schema.json")
        assert schema["additionalProperties"] is False


def test_payment_reads_have_the_closed_source_and_acl_gates() -> None:
    registry = load_registry()
    search = registry.describe("payment.search")
    get = registry.describe("payment.get")

    search_models = [
        "res.company",
        "account.payment",
        "account.payment.method",
        "account.payment.method.line",
        "res.currency",
        "res.partner",
        "account.journal",
        "account.move",
    ]
    get_only_models = [
        "account.move.line",
        "account.account",
        "account.partial.reconcile",
    ]
    assert search["source"]["models"] == search_models
    assert get["source"]["models"] == search_models + get_only_models
    assert search["requirements"]["acl"] == [f"{model}:read" for model in search_models]
    assert get["requirements"]["acl"] == [
        f"{model}:read" for model in search_models + get_only_models
    ]

    for capability_id in ("payment.search", "payment.get"):
        descriptor = registry.describe(capability_id)
        for kind in ("request", "response"):
            schema = registry.load_schema(descriptor["schemas"][kind])
            assert schema["$id"].endswith(f"{capability_id}.{kind}.schema.json")
            assert schema["additionalProperties"] is False


def test_registry_schema_references_resolve_to_public_files() -> None:
    registry = load_registry()
    descriptor = registry.describe("account.account.list")

    request_schema = registry.load_schema(descriptor["schemas"]["request"])
    response_schema = registry.load_schema(descriptor["schemas"]["response"])

    assert request_schema["$id"].endswith("account.account.list.request.schema.json")
    assert response_schema["$id"].endswith("account.account.list.response.schema.json")
    assert request_schema["additionalProperties"] is False
    assert response_schema["additionalProperties"] is False


def test_runtime_registry_validation_rejects_schema_invalid_status_metadata() -> None:
    descriptor = copy.deepcopy(load_registry().describe("account.account.list"))
    descriptor["status"]["reason_code"] = 7

    with pytest.raises(RegistryError):
        _validate_descriptor("account.account.list", descriptor)


def test_runtime_schema_enforces_request_and_response_semantics() -> None:
    registry = load_registry()
    request = {
        "schema_version": "v1",
        "request_id": "7bc39413-0d69-4092-9319-795d33f3167c",
        "context": {
            "database": "v4-dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "zh_CN",
            "timezone": "Asia/Shanghai",
        },
        "parameters": {"limit": 100, "cursor": ""},
    }
    invalid_response = {
        "schema_version": "v1",
        "request_id": request["request_id"],
        "success": True,
        "capability": "account.account.list",
        "status": "verified",
        "data": None,
        "warnings": [],
        "error": {
            "code": "impossible",
            "message": "success and error cannot coexist",
            "details": {},
            "retryable": False,
        },
        "odoo": {
            "database": "v4-dev",
            "company_id": 7,
            "user_id": 42,
            "model": "account.account",
            "record_ids": [],
        },
        "audit": {
            "operation_id": None,
            "idempotency_key": None,
            "verification": None,
        },
    }

    with pytest.raises(InstanceValidationError):
        registry.validate_instance(
            "schemas/v1/account.account.list.request.schema.json", request
        )
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(
            "schemas/v1/account.account.list.response.schema.json",
            invalid_response,
        )
