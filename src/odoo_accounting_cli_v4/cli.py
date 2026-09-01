"""Stable command surface for the independent V4 control CLI."""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
import uuid
from collections.abc import Callable, Sequence
from functools import partial
from pathlib import Path
from typing import Any, TextIO

from odoo_accounting_cli_v4 import __version__
from odoo_accounting_cli_v4.bridge.account_accounts import OdooAccountListPort
from odoo_accounting_cli_v4.bridge.account_returns import OdooAccountReturnPort
from odoo_accounting_cli_v4.bridge.accounting_access import OdooAccountingAccessPort
from odoo_accounting_cli_v4.bridge.accounting_delivery import OdooAccountingDeliveryPort
from odoo_accounting_cli_v4.bridge.assets import OdooAssetPort
from odoo_accounting_cli_v4.bridge.bank_reconciliation import (
    OdooBankReconciliationPort,
)
from odoo_accounting_cli_v4.bridge.bank_transactions import (
    OdooBankTransactionListPort,
    OdooBankTransactionSearchPort,
)
from odoo_accounting_cli_v4.bridge.budget_report import OdooBudgetReportPort
from odoo_accounting_cli_v4.bridge.client import BridgeError, OdooBridgeClient
from odoo_accounting_cli_v4.bridge.core_object_reads import OdooCoreObjectReadPort
from odoo_accounting_cli_v4.bridge.core_writes import OdooCoreWritePort
from odoo_accounting_cli_v4.bridge.currency_rates import (
    OdooCurrencyConvertPort,
    OdooCurrencyRateListPort,
)
from odoo_accounting_cli_v4.bridge.document_exports import OdooDocumentExportPort
from odoo_accounting_cli_v4.bridge.environment_inspection import (
    OdooEnvironmentInspectionPort,
)
from odoo_accounting_cli_v4.bridge.financial_reports import (
    OdooFinancialReportExportPort,
    OdooFinancialReportPort,
)
from odoo_accounting_cli_v4.bridge.fiscal_position import (
    OdooFiscalPositionResolvePort,
)
from odoo_accounting_cli_v4.bridge.inventory_accounting import (
    OdooInventoryAccountingPort,
)
from odoo_accounting_cli_v4.bridge.inventory_master import OdooInventoryMasterPort
from odoo_accounting_cli_v4.bridge.inventory_operations import (
    OdooInventoryOperationsPort,
)
from odoo_accounting_cli_v4.bridge.invoice_analysis import OdooInvoiceAnalysisPort
from odoo_accounting_cli_v4.bridge.invoices import OdooInvoicePort
from odoo_accounting_cli_v4.bridge.journal_analysis import OdooJournalAnalysisPort
from odoo_accounting_cli_v4.bridge.journal_entries import OdooJournalEntryPort
from odoo_accounting_cli_v4.bridge.journal_integrity import OdooJournalIntegrityPort
from odoo_accounting_cli_v4.bridge.localization_configuration import (
    OdooLocalizationConfigurationPort,
)
from odoo_accounting_cli_v4.bridge.master_data import OdooMasterDataPort
from odoo_accounting_cli_v4.bridge.open_items import OdooOpenItemsPort
from odoo_accounting_cli_v4.bridge.order_documents import OdooOrderDocumentsPort
from odoo_accounting_cli_v4.bridge.partners import OdooPartnerAccountingPort
from odoo_accounting_cli_v4.bridge.payments import OdooPaymentPort
from odoo_accounting_cli_v4.bridge.period_context import OdooPeriodContextPort
from odoo_accounting_cli_v4.bridge.product_accounting_profile import (
    OdooProductAccountingProfilePort,
)
from odoo_accounting_cli_v4.bridge.reconciliation_candidates import (
    OdooReconciliationCandidatesPort,
)
from odoo_accounting_cli_v4.capabilities.account_account_list import (
    AccountListError,
    read_account_accounts,
    validate_account_list_request,
)
from odoo_accounting_cli_v4.capabilities.account_returns import (
    AccountReturnReadError,
    read_account_return,
    validate_account_return_request,
)
from odoo_accounting_cli_v4.capabilities.accounting_access import (
    read_accounting_access,
    validate_accounting_access_request,
)
from odoo_accounting_cli_v4.capabilities.accounting_delivery import (
    ACCOUNTING_DELIVERY_CAPABILITY_IDS,
    ACCOUNTING_DELIVERY_READ_CAPABILITY_IDS,
    ACCOUNTING_DELIVERY_WRITE_CAPABILITY_IDS,
    AccountingDeliveryError,
    execute_accounting_delivery,
    validate_accounting_delivery_request,
)
from odoo_accounting_cli_v4.capabilities.assets import (
    AssetReadError,
    read_assets,
    validate_asset_request,
)
from odoo_accounting_cli_v4.capabilities.bank_reconciliation import (
    BankReconciliationError,
    get_bank_transaction_reconciliation,
    list_bank_match_candidates,
    validate_bank_match_candidates_request,
    validate_bank_reconciliation_get_request,
)
from odoo_accounting_cli_v4.capabilities.bank_transactions import (
    BankTransactionListError,
    list_bank_transactions,
    search_bank_transactions,
    validate_bank_transaction_list_request,
    validate_bank_transaction_search_request,
)
from odoo_accounting_cli_v4.capabilities.budget_report import (
    BudgetReportError,
    read_budget_report,
    validate_budget_report_request,
)
from odoo_accounting_cli_v4.capabilities.core_object_reads import (
    CORE_OBJECT_GET_CAPABILITY_IDS,
    CORE_OBJECT_READ_CAPABILITY_IDS,
    CoreObjectReadError,
    read_core_object,
    validate_core_object_read_request,
)
from odoo_accounting_cli_v4.capabilities.core_writes import (
    CORE_WRITE_CAPABILITY_IDS,
    CoreWriteError,
    execute_core_write,
    validate_core_write_request,
)
from odoo_accounting_cli_v4.capabilities.currency_rates import (
    CurrencyRateListError,
    convert_currency,
    list_currency_rates,
    validate_currency_convert_request,
    validate_currency_rate_list_request,
)
from odoo_accounting_cli_v4.capabilities.document_exports import (
    DOCUMENT_EXPORT_CAPABILITY_IDS,
    DOCUMENT_EXPORT_SPECS,
    DocumentExportError,
    export_document,
    validate_document_export_request,
)
from odoo_accounting_cli_v4.capabilities.environment_inspection import (
    read_environment_inspection,
    validate_environment_inspection_request,
)
from odoo_accounting_cli_v4.capabilities.financial_reports import (
    FINANCIAL_REPORT_EXPORT_CAPABILITY_IDS,
    FinancialReportError,
    export_financial_report,
    read_balance_sheet,
    read_bank_reconciliation,
    read_cash_flow,
    read_profit_and_loss,
    read_tax_report,
    read_trial_balance,
    read_typed_financial_report,
    validate_balance_sheet_request,
    validate_bank_reconciliation_request,
    validate_cash_flow_request,
    validate_financial_report_export_request,
    validate_profit_and_loss_request,
    validate_tax_report_request,
    validate_trial_balance_request,
    validate_typed_financial_report_request,
)
from odoo_accounting_cli_v4.capabilities.fiscal_position import (
    resolve_fiscal_position,
    validate_fiscal_position_resolve_request,
)
from odoo_accounting_cli_v4.capabilities.inventory_accounting import (
    InventoryAccountingError,
    read_inventory_accounting,
    validate_inventory_accounting_request,
)
from odoo_accounting_cli_v4.capabilities.inventory_master import (
    InventoryMasterReadError,
    read_inventory_master,
    validate_inventory_master_request,
)
from odoo_accounting_cli_v4.capabilities.inventory_operations import (
    InventoryOperationsReadError,
    read_inventory_operations,
    validate_inventory_operations_request,
)
from odoo_accounting_cli_v4.capabilities.invoice_analysis import (
    InvoiceAnalysisError,
    read_invoice_analysis,
    validate_invoice_analysis_request,
)
from odoo_accounting_cli_v4.capabilities.invoices import (
    InvoiceError,
    get_invoice,
    inspect_invoice_payment_status,
    search_invoices,
    validate_invoice_get_request,
    validate_invoice_payment_status_request,
    validate_invoice_search_request,
)
from odoo_accounting_cli_v4.capabilities.journal_analysis import (
    JournalAnalysisReadError,
    read_journal_analysis,
    validate_journal_analysis_request,
)
from odoo_accounting_cli_v4.capabilities.journal_entries import (
    JournalEntryError,
    check_journal_entry,
    get_journal_entry,
    search_journal_entries,
    validate_journal_entry_check_request,
    validate_journal_entry_get_request,
    validate_journal_entry_search_request,
)
from odoo_accounting_cli_v4.capabilities.journal_integrity import (
    inspect_journal_integrity,
    validate_journal_integrity_request,
)
from odoo_accounting_cli_v4.capabilities.localization_configuration import (
    CAPABILITY_IDS as LOCALIZATION_CONFIGURATION_CAPABILITY_IDS,
)
from odoo_accounting_cli_v4.capabilities.localization_configuration import (
    LocalizationConfigurationReadError,
    read_localization_configuration,
    validate_localization_configuration_request,
)
from odoo_accounting_cli_v4.capabilities.master_data_lists import (
    MasterDataListError,
    read_master_data,
    validate_master_data_request,
)
from odoo_accounting_cli_v4.capabilities.open_items import (
    OpenItemsError,
    search_payable_open_items,
    search_receivable_open_items,
    validate_payable_open_items_list_request,
    validate_receivable_open_items_list_request,
)
from odoo_accounting_cli_v4.capabilities.order_documents import (
    OrderDocumentReadError,
    read_order_document,
    validate_order_document_request,
)
from odoo_accounting_cli_v4.capabilities.partner_accounting import (
    PartnerAccountingError,
    search_accounting_partners,
    validate_partner_accounting_search_request,
)
from odoo_accounting_cli_v4.capabilities.payments import (
    PaymentError,
    get_payment,
    search_payments,
    validate_payment_get_request,
    validate_payment_search_request,
)
from odoo_accounting_cli_v4.capabilities.period_context import (
    PeriodContextReadError,
    read_period_context,
    validate_period_context_request,
)
from odoo_accounting_cli_v4.capabilities.product_accounting_profile import (
    get_product_accounting_profile,
    validate_product_accounting_profile_request,
)
from odoo_accounting_cli_v4.capabilities.reconciliation_candidates import (
    ReconciliationCandidatesError,
    list_reconciliation_candidates,
    validate_reconciliation_candidates_request,
)
from odoo_accounting_cli_v4.config import ConfigError, load_runtime_config
from odoo_accounting_cli_v4.contracts import dumps, error_document, success_document
from odoo_accounting_cli_v4.registry import (
    CapabilityNotFound,
    InstanceValidationError,
    RegistryError,
    load_registry,
)

PortFactory = Callable[[str, dict[str, Any]], object]
_MAX_REQUEST_BYTES = 1024 * 1024
_DEFAULT_RUNTIME_CONFIG = Path("/etc/odoo-accounting-cli-v4/runtime.json")
_HANDLERS: dict[str, Callable[[object, dict[str, Any]], dict[str, Any]]] = {
    "account_account_list": read_account_accounts,
    "account_return_search": lambda port, request: read_account_return(
        port, "account.return.search", request
    ),
    "account_return_get": lambda port, request: read_account_return(
        port, "account.return.get", request
    ),
    "account_return_summary": lambda port, request: read_account_return(
        port, "account.return.summary", request
    ),
    "account_return_type_list": lambda port, request: read_account_return(
        port, "account.return.type.list", request
    ),
    "account_return_check_list": lambda port, request: read_account_return(
        port, "account.return.check.list", request
    ),
    "account_return_check_get": lambda port, request: read_account_return(
        port, "account.return.check.get", request
    ),
    "account_account_get": partial(read_core_object, "account.account.get"),
    "account_group_list": partial(read_core_object, "account.group.list"),
    "account_group_get": partial(read_core_object, "account.group.get"),
    "account_tag_get": partial(read_core_object, "account.tag.get"),
    "account_tag_list": partial(read_core_object, "account.tag.list"),
    "analytic_account_get": partial(read_core_object, "analytic.account.get"),
    "analytic_account_search": partial(read_core_object, "analytic.account.search"),
    "analytic_plan_get": partial(read_core_object, "analytic.plan.get"),
    "analytic_plan_list": partial(read_core_object, "analytic.plan.list"),
    "analytic_line_search": partial(read_core_object, "analytic.line.search"),
    "analytic_line_get": partial(read_core_object, "analytic.line.get"),
    "analytic_distribution_model_list": partial(
        read_core_object, "analytic.distribution_model.list"
    ),
    "analytic_distribution_model_get": partial(
        read_core_object, "analytic.distribution_model.get"
    ),
    "analytic_applicability_list": partial(
        read_core_object, "analytic.applicability.list"
    ),
    "analytic_applicability_get": partial(
        read_core_object, "analytic.applicability.get"
    ),
    "budget_search": partial(read_core_object, "budget.search"),
    "budget_get": partial(read_core_object, "budget.get"),
    "budget_line_list": partial(read_core_object, "budget.line.list"),
    "budget_line_get": partial(read_core_object, "budget.line.get"),
    "budget_report": read_budget_report,
    "company_accounting_context_list": partial(
        read_master_data, "company.accounting_context.list"
    ),
    "journal_list": partial(read_master_data, "journal.list"),
    "journal_get": partial(read_core_object, "journal.get"),
    "journal_configuration_inspect": partial(
        read_core_object, "journal.configuration.inspect"
    ),
    "tax_list": partial(read_master_data, "tax.list"),
    "tax_get": partial(read_core_object, "tax.get"),
    "tax_repartition_line_list": partial(read_core_object, "tax.repartition_line.list"),
    "tax_repartition_line_get": partial(read_core_object, "tax.repartition_line.get"),
    "reconciliation_model_line_list": partial(
        read_core_object, "reconciliation.model.line.list"
    ),
    "reconciliation_model_line_get": partial(
        read_core_object, "reconciliation.model.line.get"
    ),
    "bank_list": partial(read_core_object, "bank.list"),
    "bank_get": partial(read_core_object, "bank.get"),
    "report_catalog_list": partial(read_core_object, "report.catalog.list"),
    "report_catalog_get": partial(read_core_object, "report.catalog.get"),
    "payment_term_list": partial(read_master_data, "payment_term.list"),
    "payment_term_get": partial(read_core_object, "payment_term.get"),
    "currency_list": partial(read_master_data, "currency.list"),
    "currency_get": partial(read_core_object, "currency.get"),
    "currency_rate_list": list_currency_rates,
    "currency_convert": convert_currency,
    "journal_entry_search": search_journal_entries,
    "journal_entry_get": get_journal_entry,
    "validation_journal_entry_check": check_journal_entry,
    "report_trial_balance": read_trial_balance,
    "report_balance_sheet": read_balance_sheet,
    "report_profit_and_loss": read_profit_and_loss,
    "report_cash_flow": read_cash_flow,
    "report_tax": read_tax_report,
    "report_trial_balance_export": partial(
        export_financial_report, "report.trial_balance.export"
    ),
    "report_balance_sheet_export": partial(
        export_financial_report, "report.balance_sheet.export"
    ),
    "report_profit_and_loss_export": partial(
        export_financial_report, "report.profit_and_loss.export"
    ),
    "report_cash_flow_export": partial(
        export_financial_report, "report.cash_flow.export"
    ),
    "report_tax_export": partial(export_financial_report, "report.tax.export"),
    "report_general_ledger_export": partial(
        export_financial_report, "report.general_ledger.export"
    ),
    "report_partner_ledger_export": partial(
        export_financial_report, "report.partner_ledger.export"
    ),
    "report_aged_receivable_export": partial(
        export_financial_report, "report.aged_receivable.export"
    ),
    "report_aged_payable_export": partial(
        export_financial_report, "report.aged_payable.export"
    ),
    "report_executive_summary_export": partial(
        export_financial_report, "report.executive_summary.export"
    ),
    "report_journal_export": partial(export_financial_report, "report.journal.export"),
    "report_asset_export": partial(export_financial_report, "report.asset.export"),
    "report_customer_statement_export": partial(
        export_financial_report, "report.customer_statement.export"
    ),
    "report_followup_export": partial(
        export_financial_report, "report.followup.export"
    ),
    "report_deferred_expense_export": partial(
        export_financial_report, "report.deferred_expense.export"
    ),
    "report_deferred_revenue_export": partial(
        export_financial_report, "report.deferred_revenue.export"
    ),
    "report_multicurrency_revaluation_export": partial(
        export_financial_report, "report.multicurrency_revaluation.export"
    ),
    "report_china_balance_sheet_export": partial(
        export_financial_report, "report.china.balance_sheet.export"
    ),
    "report_china_profit_and_loss_export": partial(
        export_financial_report, "report.china.profit_and_loss.export"
    ),
    "report_china_cash_flow_export": partial(
        export_financial_report, "report.china.cash_flow.export"
    ),
    "report_singapore_gst_export": partial(
        export_financial_report, "report.singapore.gst.export"
    ),
    "document_invoice_pdf_export": partial(export_document, "invoice.pdf.export"),
    "document_payment_receipt_pdf_export": partial(
        export_document, "payment.receipt.pdf.export"
    ),
    "document_bank_statement_pdf_export": partial(
        export_document, "bank.statement.pdf.export"
    ),
    "document_sale_order_pdf_export": partial(export_document, "sale.order.pdf.export"),
    "document_purchase_order_pdf_export": partial(
        export_document, "purchase.order.pdf.export"
    ),
    "document_purchase_rfq_pdf_export": partial(
        export_document, "purchase.rfq.pdf.export"
    ),
    "document_stock_delivery_slip_pdf_export": partial(
        export_document, "stock.delivery_slip.pdf.export"
    ),
    "document_stock_picking_operations_pdf_export": partial(
        export_document, "stock.picking_operations.pdf.export"
    ),
    "document_stock_return_slip_pdf_export": partial(
        export_document, "stock.return_slip.pdf.export"
    ),
    "document_localization_china_voucher_render": partial(
        export_document, "localization.china.voucher.render"
    ),
    "report_customer_statement": partial(
        read_typed_financial_report, "report.customer_statement"
    ),
    "report_followup": partial(read_typed_financial_report, "report.followup"),
    "report_bank_reconciliation": read_bank_reconciliation,
    "report_general_ledger": partial(
        read_typed_financial_report, "report.general_ledger"
    ),
    "report_partner_ledger": partial(
        read_typed_financial_report, "report.partner_ledger"
    ),
    "report_aged_receivable": partial(
        read_typed_financial_report, "report.aged_receivable"
    ),
    "report_aged_payable": partial(read_typed_financial_report, "report.aged_payable"),
    "report_journal": partial(read_typed_financial_report, "report.journal"),
    "report_executive_summary": partial(
        read_typed_financial_report, "report.executive_summary"
    ),
    "report_asset": partial(read_typed_financial_report, "report.asset"),
    "report_deferred_expense": partial(
        read_typed_financial_report, "report.deferred_expense"
    ),
    "report_deferred_revenue": partial(
        read_typed_financial_report, "report.deferred_revenue"
    ),
    "report_multicurrency_revaluation": partial(
        read_typed_financial_report, "report.multicurrency_revaluation"
    ),
    "report_china_balance_sheet": partial(
        read_typed_financial_report, "report.china.balance_sheet"
    ),
    "report_china_profit_and_loss": partial(
        read_typed_financial_report, "report.china.profit_and_loss"
    ),
    "report_china_cash_flow": partial(
        read_typed_financial_report, "report.china.cash_flow"
    ),
    "report_singapore_gst": partial(
        read_typed_financial_report, "report.singapore.gst"
    ),
    "fiscal_position_resolve": resolve_fiscal_position,
    "fiscal_position_get": partial(read_core_object, "fiscal_position.get"),
    "fiscal_position_search": partial(read_core_object, "fiscal_position.search"),
    "fiscal_position_account_mapping_list": partial(
        read_core_object, "fiscal_position.account_mapping.list"
    ),
    "fiscal_position_tax_mapping_list": partial(
        read_core_object, "fiscal_position.tax_mapping.list"
    ),
    "invoice_duplicate_candidates_list": partial(
        read_core_object, "invoice.duplicate_candidates.list"
    ),
    "invoice_tax_breakdown_inspect": partial(
        read_core_object, "invoice.tax_breakdown.inspect"
    ),
    "recurring_journal_entry_search": partial(
        read_core_object, "recurring.journal_entry.search"
    ),
    "recurring_journal_entry_get": partial(
        read_core_object, "recurring.journal_entry.get"
    ),
    "account_transfer_model_search": partial(
        read_core_object, "account.transfer_model.search"
    ),
    "account_transfer_model_get": partial(
        read_core_object, "account.transfer_model.get"
    ),
    "partner_credit_exposure_inspect": partial(
        read_core_object, "partner.credit_exposure.inspect"
    ),
    "journal_sequence_irregularity_list": partial(
        read_core_object, "journal.sequence_irregularity.list"
    ),
    "account_lock_exception_search": partial(
        read_core_object, "account.lock_exception.search"
    ),
    "account_lock_exception_get": partial(
        read_core_object, "account.lock_exception.get"
    ),
    "report_external_value_search": partial(
        read_core_object, "report.external_value.search"
    ),
    "report_external_value_get": partial(read_core_object, "report.external_value.get"),
    "asset_group_search": partial(read_core_object, "asset.group.search"),
    "asset_group_get": partial(read_core_object, "asset.group.get"),
    "report_budget_definition_search": partial(
        read_core_object, "report.budget_definition.search"
    ),
    "report_budget_definition_get": partial(
        read_core_object, "report.budget_definition.get"
    ),
    "report_budget_item_search": partial(read_core_object, "report.budget_item.search"),
    "report_budget_item_get": partial(read_core_object, "report.budget_item.get"),
    "tax_unit_search": partial(read_core_object, "tax.unit.search"),
    "tax_unit_get": partial(read_core_object, "tax.unit.get"),
    "account_return_account_status_search": partial(
        read_core_object, "account.return.account_status.search"
    ),
    "account_return_account_status_get": partial(
        read_core_object, "account.return.account_status.get"
    ),
    "diagnostic_journal_integrity_inspect": inspect_journal_integrity,
    "user_accounting_access_inspect": read_accounting_access,
    "company_accounting_configuration_inspect": partial(
        read_environment_inspection, "company.accounting_configuration.inspect"
    ),
    "localization_china_configuration_inspect": partial(
        read_localization_configuration,
        "localization.china.configuration.inspect",
    ),
    "localization_singapore_configuration_inspect": partial(
        read_localization_configuration,
        "localization.singapore.configuration.inspect",
    ),
    "diagnostic_accounting_environment_inspect": partial(
        read_environment_inspection, "diagnostic.accounting_environment.inspect"
    ),
    "partner_search": partial(read_core_object, "partner.search"),
    "partner_get": partial(read_core_object, "partner.get"),
    "partner_accounting_search": search_accounting_partners,
    "partner_accounting_get": partial(read_core_object, "partner.accounting.get"),
    "partner_bank_account_search": partial(
        read_core_object, "partner.bank_account.search"
    ),
    "partner_bank_account_get": partial(read_core_object, "partner.bank_account.get"),
    "invoice_search": search_invoices,
    "invoice_get": get_invoice,
    "invoice_payment_status_inspect": inspect_invoice_payment_status,
    "invoice_send_inspect": lambda port, request: execute_accounting_delivery(
        port, "invoice.send.inspect", request
    ),
    "invoice_analysis_search": lambda port, request: read_invoice_analysis(
        port, "invoice.analysis.search", request
    ),
    "invoice_analysis_summary": lambda port, request: read_invoice_analysis(
        port, "invoice.analysis.summary", request
    ),
    "receivable_open_items_list": search_receivable_open_items,
    "payable_open_items_list": search_payable_open_items,
    "payment_search": search_payments,
    "payment_get": get_payment,
    "payment_receipt_send_inspect": lambda port, request: execute_accounting_delivery(
        port, "payment.receipt.send.inspect", request
    ),
    "reconciliation_candidates_list": list_reconciliation_candidates,
    "bank_transaction_list": list_bank_transactions,
    "bank_transaction_search": search_bank_transactions,
    "bank_transaction_reconciliation_get": get_bank_transaction_reconciliation,
    "bank_transaction_match_candidates_list": list_bank_match_candidates,
    "bank_transaction_get": partial(read_core_object, "bank.transaction.get"),
    "bank_statement_search": partial(read_core_object, "bank.statement.search"),
    "bank_statement_get": partial(read_core_object, "bank.statement.get"),
    "journal_item_search": partial(read_core_object, "journal_item.search"),
    "journal_item_get": partial(read_core_object, "journal_item.get"),
    "journal_accounting_date_resolve": lambda port, request: read_journal_analysis(
        port, "journal.accounting_date.resolve", request
    ),
    "journal_item_analysis_summary": lambda port, request: read_journal_analysis(
        port, "journal_item.analysis.summary", request
    ),
    "payment_method_get": partial(read_core_object, "payment.method.get"),
    "payment_method_list": partial(read_core_object, "payment.method.list"),
    "reconciliation_model_get": partial(read_core_object, "reconciliation.model.get"),
    "reconciliation_model_list": partial(read_core_object, "reconciliation.model.list"),
    "reconciliation_partial_get": partial(
        read_core_object, "reconciliation.partial.get"
    ),
    "reconciliation_partial_list": partial(
        read_core_object, "reconciliation.partial.list"
    ),
    "reconciliation_full_get": partial(read_core_object, "reconciliation.full.get"),
    "reconciliation_full_list": partial(read_core_object, "reconciliation.full.list"),
    "cash_rounding_get": partial(read_core_object, "cash_rounding.get"),
    "cash_rounding_list": partial(read_core_object, "cash_rounding.list"),
    "journal_group_get": partial(read_core_object, "journal.group.get"),
    "journal_group_list": partial(read_core_object, "journal.group.list"),
    "incoterm_get": partial(read_core_object, "incoterm.get"),
    "incoterm_list": partial(read_core_object, "incoterm.list"),
    "product_accounting_profile_get": get_product_accounting_profile,
    "product_get": partial(read_core_object, "product.get"),
    "product_search": partial(read_core_object, "product.search"),
    "tax_group_get": partial(read_core_object, "tax.group.get"),
    "tax_group_list": partial(read_core_object, "tax.group.list"),
    "cogs_entries_list": partial(read_inventory_accounting, "cogs.entries.list"),
    "inventory_accounting_entries_list": partial(
        read_inventory_accounting, "inventory.accounting_entries.list"
    ),
    "report_inventory_valuation": partial(
        read_inventory_accounting, "report.inventory_valuation"
    ),
    "purchase_bill_matching_inspect": partial(
        read_inventory_accounting, "purchase_bill.matching.inspect"
    ),
    "sale_invoice_stock_link_inspect": partial(
        read_inventory_accounting, "sale_invoice.stock_link.inspect"
    ),
    "product_category_list": lambda port, request: read_inventory_master(
        port, "product.category.list", request
    ),
    "warehouse_list": lambda port, request: read_inventory_master(
        port, "warehouse.list", request
    ),
    "stock_location_list": lambda port, request: read_inventory_master(
        port, "stock.location.list", request
    ),
    "stock_operation_type_list": lambda port, request: read_inventory_master(
        port, "stock.operation_type.list", request
    ),
    "stock_route_list": lambda port, request: read_inventory_master(
        port, "stock.route.list", request
    ),
    "stock_transfer_search": lambda port, request: read_inventory_operations(
        port, "stock.transfer.search", request
    ),
    "stock_transfer_get": lambda port, request: read_inventory_operations(
        port, "stock.transfer.get", request
    ),
    "stock_move_search": lambda port, request: read_inventory_operations(
        port, "stock.move.search", request
    ),
    "inventory_on_hand_summary": lambda port, request: read_inventory_operations(
        port, "inventory.on_hand.summary", request
    ),
    "inventory_availability_inspect": lambda port, request: read_inventory_operations(
        port, "inventory.availability.inspect", request
    ),
    "sale_order_search": lambda port, request: read_order_document(
        port, "sale.order.search", request
    ),
    "sale_order_get": lambda port, request: read_order_document(
        port, "sale.order.get", request
    ),
    "sale_order_line_search": lambda port, request: read_order_document(
        port, "sale.order.line.search", request
    ),
    "sale_order_analysis_summary": lambda port, request: read_order_document(
        port, "sale.order.analysis.summary", request
    ),
    "purchase_order_search": lambda port, request: read_order_document(
        port, "purchase.order.search", request
    ),
    "purchase_order_get": lambda port, request: read_order_document(
        port, "purchase.order.get", request
    ),
    "purchase_order_line_search": lambda port, request: read_order_document(
        port, "purchase.order.line.search", request
    ),
    "purchase_order_analysis_summary": lambda port, request: read_order_document(
        port, "purchase.order.analysis.summary", request
    ),
    "asset_search": partial(read_assets, "asset.search"),
    "asset_get": partial(read_assets, "asset.get"),
    "asset_depreciation_schedule_get": partial(
        read_assets, "asset.depreciation_schedule.get"
    ),
    "company_lock_dates_inspect": partial(
        read_period_context, "company.lock_dates.inspect"
    ),
    "company_fiscal_year_resolve": partial(
        read_period_context, "company.fiscal_year.resolve"
    ),
    "fiscal_year_search": partial(read_period_context, "fiscal_year.search"),
    "fiscal_year_get": partial(read_period_context, "fiscal_year.get"),
}
_REQUEST_VALIDATORS: dict[str, Callable[[Any], object]] = {
    "account_account_list": validate_account_list_request,
    "account_return_search": partial(
        validate_account_return_request, "account.return.search"
    ),
    "account_return_get": partial(
        validate_account_return_request, "account.return.get"
    ),
    "account_return_summary": partial(
        validate_account_return_request, "account.return.summary"
    ),
    "account_return_type_list": partial(
        validate_account_return_request, "account.return.type.list"
    ),
    "account_return_check_list": partial(
        validate_account_return_request, "account.return.check.list"
    ),
    "account_return_check_get": partial(
        validate_account_return_request, "account.return.check.get"
    ),
    "account_account_get": partial(
        validate_core_object_read_request, "account.account.get"
    ),
    "account_group_list": partial(
        validate_core_object_read_request, "account.group.list"
    ),
    "account_group_get": partial(
        validate_core_object_read_request, "account.group.get"
    ),
    "account_tag_get": partial(validate_core_object_read_request, "account.tag.get"),
    "account_tag_list": partial(validate_core_object_read_request, "account.tag.list"),
    "analytic_account_get": partial(
        validate_core_object_read_request, "analytic.account.get"
    ),
    "analytic_account_search": partial(
        validate_core_object_read_request, "analytic.account.search"
    ),
    "analytic_plan_get": partial(
        validate_core_object_read_request, "analytic.plan.get"
    ),
    "analytic_plan_list": partial(
        validate_core_object_read_request, "analytic.plan.list"
    ),
    "analytic_line_search": partial(
        validate_core_object_read_request, "analytic.line.search"
    ),
    "analytic_line_get": partial(
        validate_core_object_read_request, "analytic.line.get"
    ),
    "analytic_distribution_model_list": partial(
        validate_core_object_read_request, "analytic.distribution_model.list"
    ),
    "analytic_distribution_model_get": partial(
        validate_core_object_read_request, "analytic.distribution_model.get"
    ),
    "analytic_applicability_list": partial(
        validate_core_object_read_request, "analytic.applicability.list"
    ),
    "analytic_applicability_get": partial(
        validate_core_object_read_request, "analytic.applicability.get"
    ),
    "budget_search": partial(validate_core_object_read_request, "budget.search"),
    "budget_get": partial(validate_core_object_read_request, "budget.get"),
    "budget_line_list": partial(validate_core_object_read_request, "budget.line.list"),
    "budget_line_get": partial(validate_core_object_read_request, "budget.line.get"),
    "budget_report": validate_budget_report_request,
    "company_accounting_context_list": partial(
        validate_master_data_request, "company.accounting_context.list"
    ),
    "journal_list": partial(validate_master_data_request, "journal.list"),
    "journal_get": partial(validate_core_object_read_request, "journal.get"),
    "journal_configuration_inspect": partial(
        validate_core_object_read_request, "journal.configuration.inspect"
    ),
    "tax_list": partial(validate_master_data_request, "tax.list"),
    "tax_get": partial(validate_core_object_read_request, "tax.get"),
    "tax_repartition_line_list": partial(
        validate_core_object_read_request, "tax.repartition_line.list"
    ),
    "tax_repartition_line_get": partial(
        validate_core_object_read_request, "tax.repartition_line.get"
    ),
    "reconciliation_model_line_list": partial(
        validate_core_object_read_request, "reconciliation.model.line.list"
    ),
    "reconciliation_model_line_get": partial(
        validate_core_object_read_request, "reconciliation.model.line.get"
    ),
    "bank_list": partial(validate_core_object_read_request, "bank.list"),
    "bank_get": partial(validate_core_object_read_request, "bank.get"),
    "report_catalog_list": partial(
        validate_core_object_read_request, "report.catalog.list"
    ),
    "report_catalog_get": partial(
        validate_core_object_read_request, "report.catalog.get"
    ),
    "payment_term_list": partial(validate_master_data_request, "payment_term.list"),
    "payment_term_get": partial(validate_core_object_read_request, "payment_term.get"),
    "currency_list": partial(validate_master_data_request, "currency.list"),
    "currency_get": partial(validate_core_object_read_request, "currency.get"),
    "currency_rate_list": validate_currency_rate_list_request,
    "currency_convert": validate_currency_convert_request,
    "journal_entry_search": validate_journal_entry_search_request,
    "journal_entry_get": validate_journal_entry_get_request,
    "validation_journal_entry_check": validate_journal_entry_check_request,
    "report_trial_balance": validate_trial_balance_request,
    "report_balance_sheet": validate_balance_sheet_request,
    "report_profit_and_loss": validate_profit_and_loss_request,
    "report_cash_flow": validate_cash_flow_request,
    "report_tax": validate_tax_report_request,
    "report_trial_balance_export": partial(
        validate_financial_report_export_request, "report.trial_balance.export"
    ),
    "report_balance_sheet_export": partial(
        validate_financial_report_export_request, "report.balance_sheet.export"
    ),
    "report_profit_and_loss_export": partial(
        validate_financial_report_export_request, "report.profit_and_loss.export"
    ),
    "report_cash_flow_export": partial(
        validate_financial_report_export_request, "report.cash_flow.export"
    ),
    "report_tax_export": partial(
        validate_financial_report_export_request, "report.tax.export"
    ),
    "report_general_ledger_export": partial(
        validate_financial_report_export_request, "report.general_ledger.export"
    ),
    "report_partner_ledger_export": partial(
        validate_financial_report_export_request, "report.partner_ledger.export"
    ),
    "report_aged_receivable_export": partial(
        validate_financial_report_export_request, "report.aged_receivable.export"
    ),
    "report_aged_payable_export": partial(
        validate_financial_report_export_request, "report.aged_payable.export"
    ),
    "report_executive_summary_export": partial(
        validate_financial_report_export_request, "report.executive_summary.export"
    ),
    "report_journal_export": partial(
        validate_financial_report_export_request, "report.journal.export"
    ),
    "report_asset_export": partial(
        validate_financial_report_export_request, "report.asset.export"
    ),
    "report_customer_statement_export": partial(
        validate_financial_report_export_request,
        "report.customer_statement.export",
    ),
    "report_followup_export": partial(
        validate_financial_report_export_request, "report.followup.export"
    ),
    "report_deferred_expense_export": partial(
        validate_financial_report_export_request, "report.deferred_expense.export"
    ),
    "report_deferred_revenue_export": partial(
        validate_financial_report_export_request, "report.deferred_revenue.export"
    ),
    "report_multicurrency_revaluation_export": partial(
        validate_financial_report_export_request,
        "report.multicurrency_revaluation.export",
    ),
    "report_china_balance_sheet_export": partial(
        validate_financial_report_export_request, "report.china.balance_sheet.export"
    ),
    "report_china_profit_and_loss_export": partial(
        validate_financial_report_export_request,
        "report.china.profit_and_loss.export",
    ),
    "report_china_cash_flow_export": partial(
        validate_financial_report_export_request, "report.china.cash_flow.export"
    ),
    "report_singapore_gst_export": partial(
        validate_financial_report_export_request, "report.singapore.gst.export"
    ),
    "document_invoice_pdf_export": partial(
        validate_document_export_request, "invoice.pdf.export"
    ),
    "document_payment_receipt_pdf_export": partial(
        validate_document_export_request, "payment.receipt.pdf.export"
    ),
    "document_bank_statement_pdf_export": partial(
        validate_document_export_request, "bank.statement.pdf.export"
    ),
    "document_sale_order_pdf_export": partial(
        validate_document_export_request, "sale.order.pdf.export"
    ),
    "document_purchase_order_pdf_export": partial(
        validate_document_export_request, "purchase.order.pdf.export"
    ),
    "document_purchase_rfq_pdf_export": partial(
        validate_document_export_request, "purchase.rfq.pdf.export"
    ),
    "document_stock_delivery_slip_pdf_export": partial(
        validate_document_export_request, "stock.delivery_slip.pdf.export"
    ),
    "document_stock_picking_operations_pdf_export": partial(
        validate_document_export_request, "stock.picking_operations.pdf.export"
    ),
    "document_stock_return_slip_pdf_export": partial(
        validate_document_export_request, "stock.return_slip.pdf.export"
    ),
    "document_localization_china_voucher_render": partial(
        validate_document_export_request, "localization.china.voucher.render"
    ),
    "report_customer_statement": partial(
        validate_typed_financial_report_request, "report.customer_statement"
    ),
    "report_followup": partial(
        validate_typed_financial_report_request, "report.followup"
    ),
    "report_bank_reconciliation": validate_bank_reconciliation_request,
    "report_general_ledger": partial(
        validate_typed_financial_report_request, "report.general_ledger"
    ),
    "report_partner_ledger": partial(
        validate_typed_financial_report_request, "report.partner_ledger"
    ),
    "report_aged_receivable": partial(
        validate_typed_financial_report_request, "report.aged_receivable"
    ),
    "report_aged_payable": partial(
        validate_typed_financial_report_request, "report.aged_payable"
    ),
    "report_journal": partial(
        validate_typed_financial_report_request, "report.journal"
    ),
    "report_executive_summary": partial(
        validate_typed_financial_report_request, "report.executive_summary"
    ),
    "report_asset": partial(validate_typed_financial_report_request, "report.asset"),
    "report_deferred_expense": partial(
        validate_typed_financial_report_request, "report.deferred_expense"
    ),
    "report_deferred_revenue": partial(
        validate_typed_financial_report_request, "report.deferred_revenue"
    ),
    "report_multicurrency_revaluation": partial(
        validate_typed_financial_report_request, "report.multicurrency_revaluation"
    ),
    "report_china_balance_sheet": partial(
        validate_typed_financial_report_request, "report.china.balance_sheet"
    ),
    "report_china_profit_and_loss": partial(
        validate_typed_financial_report_request, "report.china.profit_and_loss"
    ),
    "report_china_cash_flow": partial(
        validate_typed_financial_report_request, "report.china.cash_flow"
    ),
    "report_singapore_gst": partial(
        validate_typed_financial_report_request, "report.singapore.gst"
    ),
    "fiscal_position_resolve": validate_fiscal_position_resolve_request,
    "fiscal_position_get": partial(
        validate_core_object_read_request, "fiscal_position.get"
    ),
    "fiscal_position_search": partial(
        validate_core_object_read_request, "fiscal_position.search"
    ),
    "fiscal_position_account_mapping_list": partial(
        validate_core_object_read_request, "fiscal_position.account_mapping.list"
    ),
    "fiscal_position_tax_mapping_list": partial(
        validate_core_object_read_request, "fiscal_position.tax_mapping.list"
    ),
    "invoice_duplicate_candidates_list": partial(
        validate_core_object_read_request, "invoice.duplicate_candidates.list"
    ),
    "invoice_tax_breakdown_inspect": partial(
        validate_core_object_read_request, "invoice.tax_breakdown.inspect"
    ),
    "recurring_journal_entry_search": partial(
        validate_core_object_read_request, "recurring.journal_entry.search"
    ),
    "recurring_journal_entry_get": partial(
        validate_core_object_read_request, "recurring.journal_entry.get"
    ),
    "account_transfer_model_search": partial(
        validate_core_object_read_request, "account.transfer_model.search"
    ),
    "account_transfer_model_get": partial(
        validate_core_object_read_request, "account.transfer_model.get"
    ),
    "partner_credit_exposure_inspect": partial(
        validate_core_object_read_request, "partner.credit_exposure.inspect"
    ),
    "journal_sequence_irregularity_list": partial(
        validate_core_object_read_request, "journal.sequence_irregularity.list"
    ),
    "account_lock_exception_search": partial(
        validate_core_object_read_request, "account.lock_exception.search"
    ),
    "account_lock_exception_get": partial(
        validate_core_object_read_request, "account.lock_exception.get"
    ),
    "report_external_value_search": partial(
        validate_core_object_read_request, "report.external_value.search"
    ),
    "report_external_value_get": partial(
        validate_core_object_read_request, "report.external_value.get"
    ),
    "asset_group_search": partial(
        validate_core_object_read_request, "asset.group.search"
    ),
    "asset_group_get": partial(validate_core_object_read_request, "asset.group.get"),
    "report_budget_definition_search": partial(
        validate_core_object_read_request, "report.budget_definition.search"
    ),
    "report_budget_definition_get": partial(
        validate_core_object_read_request, "report.budget_definition.get"
    ),
    "report_budget_item_search": partial(
        validate_core_object_read_request, "report.budget_item.search"
    ),
    "report_budget_item_get": partial(
        validate_core_object_read_request, "report.budget_item.get"
    ),
    "tax_unit_search": partial(validate_core_object_read_request, "tax.unit.search"),
    "tax_unit_get": partial(validate_core_object_read_request, "tax.unit.get"),
    "account_return_account_status_search": partial(
        validate_core_object_read_request, "account.return.account_status.search"
    ),
    "account_return_account_status_get": partial(
        validate_core_object_read_request, "account.return.account_status.get"
    ),
    "diagnostic_journal_integrity_inspect": validate_journal_integrity_request,
    "user_accounting_access_inspect": validate_accounting_access_request,
    "company_accounting_configuration_inspect": partial(
        validate_environment_inspection_request,
        "company.accounting_configuration.inspect",
    ),
    "localization_china_configuration_inspect": partial(
        validate_localization_configuration_request,
        "localization.china.configuration.inspect",
    ),
    "localization_singapore_configuration_inspect": partial(
        validate_localization_configuration_request,
        "localization.singapore.configuration.inspect",
    ),
    "diagnostic_accounting_environment_inspect": partial(
        validate_environment_inspection_request,
        "diagnostic.accounting_environment.inspect",
    ),
    "partner_search": partial(validate_core_object_read_request, "partner.search"),
    "partner_get": partial(validate_core_object_read_request, "partner.get"),
    "partner_accounting_search": validate_partner_accounting_search_request,
    "partner_accounting_get": partial(
        validate_core_object_read_request, "partner.accounting.get"
    ),
    "partner_bank_account_search": partial(
        validate_core_object_read_request, "partner.bank_account.search"
    ),
    "partner_bank_account_get": partial(
        validate_core_object_read_request, "partner.bank_account.get"
    ),
    "invoice_search": validate_invoice_search_request,
    "invoice_get": validate_invoice_get_request,
    "invoice_payment_status_inspect": validate_invoice_payment_status_request,
    "invoice_send_inspect": partial(
        validate_accounting_delivery_request, "invoice.send.inspect"
    ),
    "invoice_analysis_search": partial(
        validate_invoice_analysis_request, "invoice.analysis.search"
    ),
    "invoice_analysis_summary": partial(
        validate_invoice_analysis_request, "invoice.analysis.summary"
    ),
    "receivable_open_items_list": validate_receivable_open_items_list_request,
    "payable_open_items_list": validate_payable_open_items_list_request,
    "payment_search": validate_payment_search_request,
    "payment_get": validate_payment_get_request,
    "payment_receipt_send_inspect": partial(
        validate_accounting_delivery_request, "payment.receipt.send.inspect"
    ),
    "reconciliation_candidates_list": validate_reconciliation_candidates_request,
    "bank_transaction_list": validate_bank_transaction_list_request,
    "bank_transaction_search": validate_bank_transaction_search_request,
    "bank_transaction_reconciliation_get": validate_bank_reconciliation_get_request,
    "bank_transaction_match_candidates_list": validate_bank_match_candidates_request,
    "bank_transaction_get": partial(
        validate_core_object_read_request, "bank.transaction.get"
    ),
    "bank_statement_search": partial(
        validate_core_object_read_request, "bank.statement.search"
    ),
    "bank_statement_get": partial(
        validate_core_object_read_request, "bank.statement.get"
    ),
    "journal_item_search": partial(
        validate_core_object_read_request, "journal_item.search"
    ),
    "journal_item_get": partial(validate_core_object_read_request, "journal_item.get"),
    "journal_accounting_date_resolve": partial(
        validate_journal_analysis_request, "journal.accounting_date.resolve"
    ),
    "journal_item_analysis_summary": partial(
        validate_journal_analysis_request, "journal_item.analysis.summary"
    ),
    "payment_method_get": partial(
        validate_core_object_read_request, "payment.method.get"
    ),
    "payment_method_list": partial(
        validate_core_object_read_request, "payment.method.list"
    ),
    "reconciliation_model_get": partial(
        validate_core_object_read_request, "reconciliation.model.get"
    ),
    "reconciliation_model_list": partial(
        validate_core_object_read_request, "reconciliation.model.list"
    ),
    "reconciliation_partial_get": partial(
        validate_core_object_read_request, "reconciliation.partial.get"
    ),
    "reconciliation_partial_list": partial(
        validate_core_object_read_request, "reconciliation.partial.list"
    ),
    "reconciliation_full_get": partial(
        validate_core_object_read_request, "reconciliation.full.get"
    ),
    "reconciliation_full_list": partial(
        validate_core_object_read_request, "reconciliation.full.list"
    ),
    "cash_rounding_get": partial(
        validate_core_object_read_request, "cash_rounding.get"
    ),
    "cash_rounding_list": partial(
        validate_core_object_read_request, "cash_rounding.list"
    ),
    "journal_group_get": partial(
        validate_core_object_read_request, "journal.group.get"
    ),
    "journal_group_list": partial(
        validate_core_object_read_request, "journal.group.list"
    ),
    "incoterm_get": partial(validate_core_object_read_request, "incoterm.get"),
    "incoterm_list": partial(validate_core_object_read_request, "incoterm.list"),
    "product_accounting_profile_get": validate_product_accounting_profile_request,
    "product_get": partial(validate_core_object_read_request, "product.get"),
    "product_search": partial(validate_core_object_read_request, "product.search"),
    "tax_group_get": partial(validate_core_object_read_request, "tax.group.get"),
    "tax_group_list": partial(validate_core_object_read_request, "tax.group.list"),
    "cogs_entries_list": partial(
        validate_inventory_accounting_request, "cogs.entries.list"
    ),
    "inventory_accounting_entries_list": partial(
        validate_inventory_accounting_request,
        "inventory.accounting_entries.list",
    ),
    "report_inventory_valuation": partial(
        validate_inventory_accounting_request, "report.inventory_valuation"
    ),
    "purchase_bill_matching_inspect": partial(
        validate_inventory_accounting_request,
        "purchase_bill.matching.inspect",
    ),
    "sale_invoice_stock_link_inspect": partial(
        validate_inventory_accounting_request,
        "sale_invoice.stock_link.inspect",
    ),
    "product_category_list": partial(
        validate_inventory_master_request, "product.category.list"
    ),
    "warehouse_list": partial(validate_inventory_master_request, "warehouse.list"),
    "stock_location_list": partial(
        validate_inventory_master_request, "stock.location.list"
    ),
    "stock_operation_type_list": partial(
        validate_inventory_master_request, "stock.operation_type.list"
    ),
    "stock_route_list": partial(validate_inventory_master_request, "stock.route.list"),
    "stock_transfer_search": partial(
        validate_inventory_operations_request, "stock.transfer.search"
    ),
    "stock_transfer_get": partial(
        validate_inventory_operations_request, "stock.transfer.get"
    ),
    "stock_move_search": partial(
        validate_inventory_operations_request, "stock.move.search"
    ),
    "inventory_on_hand_summary": partial(
        validate_inventory_operations_request, "inventory.on_hand.summary"
    ),
    "inventory_availability_inspect": partial(
        validate_inventory_operations_request, "inventory.availability.inspect"
    ),
    "sale_order_search": partial(validate_order_document_request, "sale.order.search"),
    "sale_order_get": partial(validate_order_document_request, "sale.order.get"),
    "sale_order_line_search": partial(
        validate_order_document_request, "sale.order.line.search"
    ),
    "sale_order_analysis_summary": partial(
        validate_order_document_request, "sale.order.analysis.summary"
    ),
    "purchase_order_search": partial(
        validate_order_document_request, "purchase.order.search"
    ),
    "purchase_order_get": partial(
        validate_order_document_request, "purchase.order.get"
    ),
    "purchase_order_line_search": partial(
        validate_order_document_request, "purchase.order.line.search"
    ),
    "purchase_order_analysis_summary": partial(
        validate_order_document_request, "purchase.order.analysis.summary"
    ),
    "asset_search": partial(validate_asset_request, "asset.search"),
    "asset_get": partial(validate_asset_request, "asset.get"),
    "asset_depreciation_schedule_get": partial(
        validate_asset_request, "asset.depreciation_schedule.get"
    ),
    "company_lock_dates_inspect": partial(
        validate_period_context_request, "company.lock_dates.inspect"
    ),
    "company_fiscal_year_resolve": partial(
        validate_period_context_request, "company.fiscal_year.resolve"
    ),
    "fiscal_year_search": partial(
        validate_period_context_request, "fiscal_year.search"
    ),
    "fiscal_year_get": partial(validate_period_context_request, "fiscal_year.get"),
}
_CAPABILITY_MODELS = {
    "account.account.list": "account.account",
    "account.return.search": "account.return",
    "account.return.get": "account.return",
    "account.return.summary": "account.return",
    "account.return.type.list": "account.return.type",
    "account.return.check.list": "account.return.check",
    "account.return.check.get": "account.return.check",
    "account.account.get": "account.account",
    "account.group.list": "account.group",
    "account.group.get": "account.group",
    "account.group.create": "account.group",
    "account.group.update": "account.group",
    "account.account.create": "account.account",
    "account.account.update": "account.account",
    "account.account.archive": "account.account",
    "account.account.restore": "account.account",
    "account.tag.get": "account.account.tag",
    "account.tag.list": "account.account.tag",
    "account.tag.create": "account.account.tag",
    "account.tag.update": "account.account.tag",
    "account.tag.archive": "account.account.tag",
    "account.tag.restore": "account.account.tag",
    "analytic.account.get": "account.analytic.account",
    "analytic.account.search": "account.analytic.account",
    "analytic.plan.get": "account.analytic.plan",
    "analytic.plan.list": "account.analytic.plan",
    "analytic.line.search": "account.analytic.line",
    "analytic.line.get": "account.analytic.line",
    "analytic.distribution_model.list": "account.analytic.distribution.model",
    "analytic.distribution_model.get": "account.analytic.distribution.model",
    "analytic.applicability.list": "account.analytic.applicability",
    "analytic.applicability.get": "account.analytic.applicability",
    "budget.search": "budget.analytic",
    "budget.get": "budget.analytic",
    "budget.line.list": "budget.line",
    "budget.line.get": "budget.line",
    "report.budget": "budget.report",
    "company.accounting_context.list": "res.company",
    "company.fiscal_year.resolve": "res.company",
    "company.lock_dates.inspect": "res.company",
    "journal.list": "account.journal",
    "journal.get": "account.journal",
    "journal.configuration.inspect": "account.journal",
    "journal.create": "account.journal",
    "journal.update": "account.journal",
    "journal.archive": "account.journal",
    "journal.restore": "account.journal",
    "tax.list": "account.tax",
    "tax.get": "account.tax",
    "tax.repartition_line.list": "account.tax.repartition.line",
    "tax.repartition_line.get": "account.tax.repartition.line",
    "tax.repartition_lines.replace": "account.tax",
    "reconciliation.model.line.list": "account.reconcile.model.line",
    "reconciliation.model.line.get": "account.reconcile.model.line",
    "bank.list": "res.bank",
    "bank.get": "res.bank",
    "tax.create": "account.tax",
    "tax.update": "account.tax",
    "tax.archive": "account.tax",
    "tax.restore": "account.tax",
    "payment_term.list": "account.payment.term",
    "payment_term.get": "account.payment.term",
    "payment_term.create": "account.payment.term",
    "payment_term.update": "account.payment.term",
    "payment_term.lines.replace": "account.payment.term",
    "payment_term.archive": "account.payment.term",
    "payment_term.restore": "account.payment.term",
    "currency.list": "res.currency",
    "currency.get": "res.currency",
    "currency.rate.list": "res.currency.rate",
    "currency.rate.record": "res.currency.rate",
    "currency.convert": "res.currency",
    "journal_entry.search": "account.move",
    "journal_entry.get": "account.move",
    "validation.journal_entry.check": "account.move",
    "report.trial_balance": "account.report",
    "report.balance_sheet": "account.report",
    "report.profit_and_loss": "account.report",
    "report.cash_flow": "account.report",
    "report.tax": "account.report",
    "report.catalog.list": "account.report",
    "report.catalog.get": "account.report",
    "report.trial_balance.export": "account.report",
    "report.balance_sheet.export": "account.report",
    "report.profit_and_loss.export": "account.report",
    "report.cash_flow.export": "account.report",
    "report.tax.export": "account.report",
    "report.general_ledger.export": "account.report",
    "report.partner_ledger.export": "account.report",
    "report.aged_receivable.export": "account.report",
    "report.aged_payable.export": "account.report",
    "report.executive_summary.export": "account.report",
    "report.journal.export": "account.report",
    "report.asset.export": "account.report",
    "report.customer_statement.export": "account.report",
    "report.followup.export": "account.report",
    "report.deferred_expense.export": "account.report",
    "report.deferred_revenue.export": "account.report",
    "report.multicurrency_revaluation.export": "account.report",
    "report.china.balance_sheet.export": "account.report",
    "report.china.profit_and_loss.export": "account.report",
    "report.china.cash_flow.export": "account.report",
    "report.singapore.gst.export": "account.report",
    "report.customer_statement": "account.report",
    "report.followup": "account.report",
    "report.bank_reconciliation": "account.report",
    "report.general_ledger": "account.report",
    "report.partner_ledger": "account.report",
    "report.aged_receivable": "account.report",
    "report.aged_payable": "account.report",
    "report.journal": "account.report",
    "report.executive_summary": "account.report",
    "report.asset": "account.report",
    "report.deferred_expense": "account.report",
    "report.deferred_revenue": "account.report",
    "report.multicurrency_revaluation": "account.report",
    "report.china.balance_sheet": "account.report",
    "report.china.profit_and_loss": "account.report",
    "report.china.cash_flow": "account.report",
    "report.singapore.gst": "account.report",
    "fiscal_position.resolve": "account.fiscal.position",
    "fiscal_position.get": "account.fiscal.position",
    "fiscal_position.search": "account.fiscal.position",
    "fiscal_position.account_mapping.list": "account.fiscal.position.account",
    "fiscal_position.tax_mapping.list": "account.fiscal.position",
    "invoice.duplicate_candidates.list": "account.move",
    "invoice.tax_breakdown.inspect": "account.move",
    "recurring.journal_entry.search": "account.move",
    "recurring.journal_entry.get": "account.move",
    "account.transfer_model.search": "account.transfer.model",
    "account.transfer_model.get": "account.transfer.model",
    "partner.credit_exposure.inspect": "res.partner",
    "journal.sequence_irregularity.list": "account.move",
    "account.lock_exception.search": "account.lock_exception",
    "account.lock_exception.get": "account.lock_exception",
    "report.external_value.search": "account.report.external.value",
    "report.external_value.get": "account.report.external.value",
    "asset.group.search": "account.asset.group",
    "asset.group.get": "account.asset.group",
    "report.budget_definition.search": "account.report.budget",
    "report.budget_definition.get": "account.report.budget",
    "report.budget_item.search": "account.report.budget.item",
    "report.budget_item.get": "account.report.budget.item",
    "tax.unit.search": "account.tax.unit",
    "tax.unit.get": "account.tax.unit",
    "account.return.account_status.search": "account.audit.account.status",
    "account.return.account_status.get": "account.audit.account.status",
    "fiscal_year.get": "account.fiscal.year",
    "fiscal_year.search": "account.fiscal.year",
    "fiscal_year.create": "account.fiscal.year",
    "fiscal_year.update": "account.fiscal.year",
    "diagnostic.journal_integrity.inspect": "res.company",
    "user.accounting_access.inspect": "res.users",
    "company.accounting_configuration.inspect": "res.company",
    "localization.china.configuration.inspect": "res.company",
    "localization.singapore.configuration.inspect": "res.company",
    "diagnostic.accounting_environment.inspect": "ir.module.module",
    "partner.search": "res.partner",
    "partner.get": "res.partner",
    "partner.accounting.search": "res.partner",
    "partner.accounting.get": "res.partner",
    "partner.bank_account.search": "res.partner.bank",
    "partner.bank_account.get": "res.partner.bank",
    "invoice.search": "account.move",
    "invoice.get": "account.move",
    "invoice.payment_status.inspect": "account.move",
    "invoice.send.inspect": "account.move",
    "invoice.send": "account.move",
    "invoice.followup.update": "account.move",
    "invoice.analysis.search": "account.invoice.report",
    "invoice.analysis.summary": "account.invoice.report",
    "receivable.open_items.list": "account.move.line",
    "payable.open_items.list": "account.move.line",
    "payment.search": "account.payment",
    "payment.get": "account.payment",
    "payment.receipt.send.inspect": "account.payment",
    "payment.receipt.send": "account.payment",
    "report.customer_statement.send": "res.partner",
    "report.followup.send": "res.partner",
    "reconciliation.candidates.list": "account.move.line",
    "bank.transaction.list": "account.bank.statement.line",
    "bank.transaction.search": "account.bank.statement.line",
    "bank.transaction.get": "account.bank.statement.line",
    "bank.transaction.reconciliation.get": "account.bank.statement.line",
    "bank.transaction.match_candidates.list": "account.move.line",
    "bank.statement.search": "account.bank.statement",
    "bank.statement.get": "account.bank.statement",
    "journal_item.search": "account.move.line",
    "journal_item.get": "account.move.line",
    "journal.accounting_date.resolve": "account.journal",
    "journal_item.analysis.summary": "account.move.line",
    "payment.method.get": "account.payment.method.line",
    "payment.method.list": "account.payment.method.line",
    "reconciliation.model.get": "account.reconcile.model",
    "reconciliation.model.list": "account.reconcile.model",
    "reconciliation.model.create": "account.reconcile.model",
    "reconciliation.model.update": "account.reconcile.model",
    "reconciliation.model.lines.replace": "account.reconcile.model",
    "reconciliation.model.archive": "account.reconcile.model",
    "reconciliation.model.restore": "account.reconcile.model",
    "reconciliation.partial.get": "account.partial.reconcile",
    "reconciliation.partial.list": "account.partial.reconcile",
    "reconciliation.full.get": "account.full.reconcile",
    "reconciliation.full.list": "account.full.reconcile",
    "cash_rounding.get": "account.cash.rounding",
    "cash_rounding.list": "account.cash.rounding",
    "cash_rounding.create": "account.cash.rounding",
    "cash_rounding.update": "account.cash.rounding",
    "journal.group.get": "account.journal.group",
    "journal.group.list": "account.journal.group",
    "incoterm.get": "account.incoterms",
    "incoterm.list": "account.incoterms",
    "product.accounting_profile.get": "product.product",
    "product.get": "product.product",
    "product.search": "product.product",
    "cogs.entries.list": "account.move.line",
    "inventory.accounting_entries.list": "stock.move",
    "report.inventory_valuation": "stock_account.stock.valuation.report",
    "purchase_bill.matching.inspect": "account.move",
    "sale_invoice.stock_link.inspect": "account.move",
    "product.category.list": "product.category",
    "warehouse.list": "stock.warehouse",
    "stock.location.list": "stock.location",
    "stock.operation_type.list": "stock.picking.type",
    "stock.route.list": "stock.route",
    "stock.transfer.search": "stock.picking",
    "stock.transfer.get": "stock.picking",
    "stock.transfer.create": "stock.picking",
    "stock.transfer.confirm": "stock.picking",
    "stock.transfer.assign": "stock.picking",
    "stock.transfer.quantities.set": "stock.picking",
    "stock.transfer.validate": "stock.picking",
    "stock.transfer.unreserve": "stock.picking",
    "stock.transfer.cancel": "stock.picking",
    "stock.move.search": "stock.move",
    "inventory.on_hand.summary": "stock.quant",
    "inventory.availability.inspect": "product.product",
    "sale.order.search": "sale.order",
    "sale.order.get": "sale.order",
    "sale.order.line.search": "sale.order.line",
    "sale.order.analysis.summary": "sale.order",
    "purchase.order.search": "purchase.order",
    "purchase.order.get": "purchase.order",
    "purchase.order.line.search": "purchase.order.line",
    "purchase.order.analysis.summary": "purchase.order",
    "sale.order.create": "sale.order",
    "sale.order.update_draft": "sale.order",
    "sale.order.lines.replace": "sale.order",
    "sale.order.confirm": "sale.order",
    "sale.order.cancel": "sale.order",
    "sale.order.reset_to_draft": "sale.order",
    "sale.order.invoice.create": "account.move",
    "purchase.order.create": "purchase.order",
    "purchase.order.update_draft": "purchase.order",
    "purchase.order.lines.replace": "purchase.order",
    "purchase.order.confirm": "purchase.order",
    "purchase.order.cancel": "purchase.order",
    "purchase.order.reset_to_draft": "purchase.order",
    "purchase.order.bill.create": "account.move",
    "purchase_bill.match": "account.move",
    "purchase_bill.lines.unmatch": "account.move",
    "period.accrual.generate": "account.move",
    "fiscal_position.create": "account.fiscal.position",
    "fiscal_position.update": "account.fiscal.position",
    "fiscal_position.account_mappings.replace": "account.fiscal.position",
    "fiscal_position.archive": "account.fiscal.position",
    "fiscal_position.restore": "account.fiscal.position",
    "journal.group.create": "account.journal.group",
    "journal.group.update": "account.journal.group",
    "tax.group.get": "account.tax.group",
    "tax.group.list": "account.tax.group",
    "tax.group.create": "account.tax.group",
    "tax.group.update": "account.tax.group",
    "analytic.applicability.create": "account.analytic.applicability",
    "analytic.applicability.update": "account.analytic.applicability",
    "analytic.distribution_model.create": "account.analytic.distribution.model",
    "analytic.distribution_model.update": "account.analytic.distribution.model",
    "asset.search": "account.asset",
    "asset.get": "account.asset",
    "asset.depreciation_schedule.get": "account.asset",
    "asset.create": "account.asset",
    "asset.validate": "account.asset",
    "asset.cancel": "account.asset",
    "asset.dispose": "account.asset",
    "asset.pause": "account.asset",
    "deferred_expense.generate_entries": "account.move",
    "deferred_revenue.generate_entries": "account.move",
    "multicurrency.revaluation.generate_entries": "account.move",
    "reconciliation.automatic.run": "account.move.line",
    "period.transfer.run": "account.move",
    "localization.china.period_transfer.run": "account.move",
    "customer_invoice.create": "account.move",
    "vendor_bill.create": "account.move",
    "invoice.update": "account.move",
    "invoice.lines.replace": "account.move",
    "invoice.cancel": "account.move",
    "invoice.reset_to_draft": "account.move",
    "invoice.post": "account.move",
    "journal_entry.create": "account.move",
    "journal_entry.update": "account.move",
    "journal_entry.lines.replace": "account.move",
    "journal_entry.cancel": "account.move",
    "journal_entry.reset_to_draft": "account.move",
    "journal_entry.post": "account.move",
    "journal_entry.reverse": "account.move",
    "receivable.payment.register": "account.payment",
    "payable.payment.register": "account.payment",
    "reconciliation.apply": "account.move.line",
    "payment.cancel": "account.payment",
    "payment.create": "account.payment",
    "payment.update_draft": "account.payment",
    "payment.reset_to_draft": "account.payment",
    "customer_credit_note.create": "account.move",
    "vendor_refund.create": "account.move",
    "payment.post": "account.payment",
    "reconciliation.undo": "account.move.line",
    "bank.transaction.record": "account.bank.statement.line",
    "bank.transaction.update": "account.bank.statement.line",
    "bank.transaction.match": "account.bank.statement.line",
    "bank.transaction.unmatch": "account.bank.statement.line",
    "reconciliation.write_off": "account.bank.statement.line",
    "analytic.account.create": "account.analytic.account",
    "analytic.account.update": "account.analytic.account",
    "budget.create": "budget.analytic",
    "budget.update_draft": "budget.analytic",
    "budget.lines.replace": "budget.analytic",
    "budget.confirm": "budget.analytic",
    "budget.reset_to_draft": "budget.analytic",
    "budget.cancel": "budget.analytic",
    "budget.mark_done": "budget.analytic",
    "partner.create": "res.partner",
    "partner.update": "res.partner",
    "partner.archive": "res.partner",
    "partner.restore": "res.partner",
    "partner.accounting.update": "res.partner",
    "partner.bank_account.create": "res.partner.bank",
    "partner.bank_account.update": "res.partner.bank",
    "partner.bank_account.archive": "res.partner.bank",
    "partner.bank_account.restore": "res.partner.bank",
    "invoice.pdf.export": "account.move",
    "payment.receipt.pdf.export": "account.payment",
    "bank.statement.pdf.export": "account.bank.statement",
    "sale.order.pdf.export": "sale.order",
    "purchase.order.pdf.export": "purchase.order",
    "purchase.rfq.pdf.export": "purchase.order",
    "stock.delivery_slip.pdf.export": "stock.picking",
    "stock.picking_operations.pdf.export": "stock.picking",
    "stock.return_slip.pdf.export": "stock.picking",
    "localization.china.voucher.render": "account.move",
}
_BATCH_LIFECYCLE_CAPABILITY_IDS = frozenset(
    {
        "invoice.post",
        "invoice.cancel",
        "invoice.reset_to_draft",
        "journal_entry.post",
        "journal_entry.cancel",
        "journal_entry.reset_to_draft",
        "payment.post",
        "payment.cancel",
        "payment.reset_to_draft",
    }
)


class CliError(RuntimeError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        exit_code: int,
        status: str,
        capability: str,
        request_id: str | None = None,
        details: dict[str, Any] | None = None,
        retryable: bool = False,
        database: str | None = None,
        company_id: int | None = None,
        user_id: int | None = None,
        model: str | None = None,
        record_ids: list[int] | None = None,
        idempotency_key: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code
        self.status = status
        self.capability = capability
        self.request_id = request_id
        self.details = details or {}
        self.retryable = retryable
        self.database = database
        self.company_id = company_id
        self.user_id = user_id
        self.model = model
        self.record_ids = record_ids or []
        self.idempotency_key = idempotency_key


class _JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliError(
            "invalid_arguments",
            "The command arguments are invalid.",
            exit_code=2,
            status="invalid",
            capability="cli",
        )


def _parser() -> argparse.ArgumentParser:
    parser = _JsonArgumentParser(prog="odoo-accounting-cli-v4")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("version", help="Show bootstrap package metadata as JSON")
    commands.add_parser("doctor", help="Check the configured V4 runtime")

    capabilities = commands.add_parser(
        "capabilities", help="Discover versioned accounting capabilities"
    )
    capability_commands = capabilities.add_subparsers(
        dest="capabilities_command", required=True
    )
    capability_commands.add_parser("list", help="List all registered capabilities")
    describe = capability_commands.add_parser(
        "describe", help="Describe one exact capability ID"
    )
    describe.add_argument("capability_id")

    read = commands.add_parser("read", help="Execute one registered read capability")
    read.add_argument("capability_id")
    read.add_argument(
        "--request",
        required=True,
        dest="request_source",
        metavar="@FILE|-",
        help="Read one v1 JSON request from @FILE or stdin (-)",
    )

    write = commands.add_parser("write", help="Execute fixed accounting writes")
    write_commands = write.add_subparsers(dest="write_command", required=True)
    run = write_commands.add_parser("run")
    run.add_argument("capability_id")
    run.add_argument("--request", required=True, dest="request_source")
    run.add_argument("--idempotency-key", required=True)
    run.add_argument("--confirm", required=True)
    prepare = write_commands.add_parser("prepare")
    prepare.add_argument("capability_id")
    prepare.add_argument("--request", required=True, dest="request_source")
    prepare.add_argument("--idempotency-key", required=True)
    approve = write_commands.add_parser("approve")
    approve.add_argument("operation_id")
    approve.add_argument("--approval", required=True, dest="approval_source")
    execute = write_commands.add_parser("execute")
    execute.add_argument("operation_id")

    operations = commands.add_parser("operations", help="Inspect write operations")
    operation_commands = operations.add_subparsers(
        dest="operations_command", required=True
    )
    for name in ("get", "verify"):
        operation = operation_commands.add_parser(name)
        operation.add_argument("operation_id")
    reverse = operation_commands.add_parser("reverse")
    reverse.add_argument("operation_id")
    reverse.add_argument("--request", required=True, dest="request_source")
    return parser


def _emit(document: dict[str, Any], stdout: TextIO) -> None:
    stdout.write(dumps(document))
    stdout.write("\n")
    stdout.flush()


def _status_for_exit(exit_code: int) -> str:
    return {
        2: "invalid",
        3: "denied",
        4: "unavailable",
        5: "conflict",
        6: "failed",
        7: "failed",
        8: "failed_validation",
    }.get(exit_code, "failed")


def _safe_request_id(request: dict[str, Any]) -> str | None:
    value = request.get("request_id")
    if not isinstance(value, str):
        return None
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError):
        return None
    return value if str(parsed) == value.lower() else None


def _safe_capability(value: object) -> str:
    return value if isinstance(value, str) and value else "cli"


def _verified_port_user_id(port: object | None) -> int | None:
    if port is None:
        return None
    try:
        value = port.user_id
    except Exception:  # noqa: BLE001 - a port property must not leak runtime failures
        return None
    return (
        value
        if isinstance(value, int) and not isinstance(value, bool) and value > 0
        else None
    )


def _decode_request(raw: str) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise CliError(
                    "invalid_request",
                    "The request contains a duplicate JSON key.",
                    exit_code=2,
                    status="invalid",
                    capability="read",
                )
            value[key] = item
        return value

    try:
        value = json.loads(raw, object_pairs_hook=reject_duplicates)
    except CliError:
        raise
    except json.JSONDecodeError as exc:
        raise CliError(
            "invalid_request",
            "The request is not valid JSON.",
            exit_code=2,
            status="invalid",
            capability="read",
        ) from exc
    if not isinstance(value, dict):
        raise CliError(
            "invalid_request",
            "The request must be a JSON object.",
            exit_code=2,
            status="invalid",
            capability="read",
        )
    return value


def _read_nofollow(path: Path) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise CliError(
            "invalid_request_source",
            "The request file cannot be opened.",
            exit_code=2,
            status="invalid",
            capability="read",
        ) from exc
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_size > _MAX_REQUEST_BYTES:
            raise CliError(
                "invalid_request_source",
                "The request source must be a small regular file.",
                exit_code=2,
                status="invalid",
                capability="read",
            )
        chunks: list[bytes] = []
        remaining = _MAX_REQUEST_BYTES + 1
        while remaining:
            chunk = os.read(descriptor, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        if len(raw) > _MAX_REQUEST_BYTES:
            raise CliError(
                "invalid_request_source",
                "The request file is too large.",
                exit_code=2,
                status="invalid",
                capability="read",
            )
        return raw
    finally:
        os.close(descriptor)


def _load_request(source: str, stdin: TextIO) -> dict[str, Any]:
    if source == "-":
        raw = stdin.read(_MAX_REQUEST_BYTES + 1)
        if len(raw.encode("utf-8")) > _MAX_REQUEST_BYTES:
            raise CliError(
                "invalid_request_source",
                "The request on stdin is too large.",
                exit_code=2,
                status="invalid",
                capability="read",
            )
    elif source.startswith("@") and len(source) > 1:
        try:
            raw = _read_nofollow(Path(source[1:])).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise CliError(
                "invalid_request_source",
                "The request file must be UTF-8 JSON.",
                exit_code=2,
                status="invalid",
                capability="read",
            ) from exc
    else:
        raise CliError(
            "invalid_request_source",
            "--request must be '-' or an @FILE reference.",
            exit_code=2,
            status="invalid",
            capability="read",
        )
    return _decode_request(raw)


def _list_capabilities() -> dict[str, Any]:
    registry = load_registry()
    items = []
    for capability_id in registry.ids():
        descriptor = registry.describe(capability_id)
        items.append(
            {
                "id": capability_id,
                "summary": descriptor["summary"],
                "domain": descriptor["domain"],
                "access": descriptor["access"],
                "status": descriptor["status"],
                "required_slots": descriptor["routing"]["required_slots"],
            }
        )
    document = success_document(
        "capabilities.list",
        {"registry_digest": registry.digest, "capabilities": items},
    )
    registry.validate_instance("schemas/v1/response.schema.json", document)
    return document


def _describe_capability(capability_id: str) -> dict[str, Any]:
    registry = load_registry()
    try:
        descriptor = registry.describe(capability_id)
    except CapabilityNotFound as exc:
        raise CliError(
            "capability_not_found",
            "The requested capability is not registered.",
            exit_code=4,
            status="unavailable",
            capability=capability_id,
        ) from exc
    document = success_document(
        "capabilities.describe",
        {
            "id": capability_id,
            "registry_digest": registry.digest,
            "descriptor": descriptor,
            "request_schema": registry.load_schema(descriptor["schemas"]["request"]),
            "response_schema": registry.load_schema(descriptor["schemas"]["response"]),
        },
    )
    registry.validate_instance("schemas/v1/response.schema.json", document)
    return document


def _execute_read(
    capability_id: str,
    request_source: str,
    *,
    stdin: TextIO,
    port_factory: PortFactory | None,
) -> dict[str, Any]:
    registry = load_registry()
    try:
        descriptor = registry.describe(capability_id)
    except CapabilityNotFound as exc:
        raise CliError(
            "capability_not_found",
            "The requested capability is not registered.",
            exit_code=4,
            status="unavailable",
            capability=capability_id,
        ) from exc
    if descriptor["access"] != "read":
        raise CliError(
            "policy_denied",
            "The requested capability is not a read capability.",
            exit_code=3,
            status="denied",
            capability=capability_id,
        )
    if descriptor["status"]["value"] not in {
        "available",
        "degraded",
        "unconfigured",
    }:
        raise CliError(
            "capability_unavailable",
            "The requested capability is not currently available.",
            exit_code=4,
            status="unavailable",
            capability=capability_id,
            details={"reason_code": descriptor["status"]["reason_code"]},
        )

    handler = _HANDLERS.get(descriptor["handler_key"])
    validator = _REQUEST_VALIDATORS.get(descriptor["handler_key"])
    if handler is None or validator is None:
        raise CliError(
            "capability_unavailable",
            "The registered capability has no allowlisted handler.",
            exit_code=4,
            status="unavailable",
            capability=capability_id,
        )

    try:
        request = _load_request(request_source, stdin)
    except CliError as exc:
        raise CliError(
            exc.code,
            str(exc),
            exit_code=exc.exit_code,
            status=exc.status,
            capability=capability_id,
            request_id=exc.request_id,
            details=exc.details,
            retryable=exc.retryable,
        ) from exc
    request_id = _safe_request_id(request)
    try:
        registry.validate_instance(descriptor["schemas"]["request"], request)
        validator(request)
    except InstanceValidationError as exc:
        raise CliError(
            "invalid_request",
            "The request does not match the capability schema.",
            exit_code=2,
            status="invalid",
            capability=capability_id,
            request_id=request_id,
        ) from exc
    except (
        AccountListError,
        MasterDataListError,
        JournalEntryError,
        FinancialReportError,
        DocumentExportError,
        PartnerAccountingError,
        InvoiceError,
        OpenItemsError,
        PaymentError,
        ReconciliationCandidatesError,
        CurrencyRateListError,
        BankTransactionListError,
        BankReconciliationError,
        CoreObjectReadError,
        InventoryAccountingError,
        InventoryMasterReadError,
        InventoryOperationsReadError,
        OrderDocumentReadError,
        AssetReadError,
        BudgetReportError,
        InvoiceAnalysisError,
        PeriodContextReadError,
        AccountReturnReadError,
        JournalAnalysisReadError,
        LocalizationConfigurationReadError,
        AccountingDeliveryError,
    ) as exc:
        raise CliError(
            exc.code,
            str(exc),
            exit_code=exc.exit_code,
            status=_status_for_exit(exc.exit_code),
            capability=capability_id,
            request_id=request_id,
            details=exc.details,
            retryable=exc.retryable,
        ) from exc
    if port_factory is None:
        port_factory = _configured_port_factory
    port: object | None = None
    try:
        port = port_factory(capability_id, request)
        data = handler(port, request)
    except (
        AccountListError,
        MasterDataListError,
        JournalEntryError,
        FinancialReportError,
        DocumentExportError,
        PartnerAccountingError,
        InvoiceError,
        OpenItemsError,
        PaymentError,
        ReconciliationCandidatesError,
        CurrencyRateListError,
        BankTransactionListError,
        BankReconciliationError,
        CoreObjectReadError,
        InventoryAccountingError,
        InventoryMasterReadError,
        InventoryOperationsReadError,
        OrderDocumentReadError,
        AssetReadError,
        BudgetReportError,
        InvoiceAnalysisError,
        PeriodContextReadError,
        AccountReturnReadError,
        JournalAnalysisReadError,
        LocalizationConfigurationReadError,
        AccountingDeliveryError,
    ) as exc:
        verified_user_id = _verified_port_user_id(port)
        raise CliError(
            exc.code,
            str(exc),
            exit_code=exc.exit_code,
            status=_status_for_exit(exc.exit_code),
            capability=capability_id,
            request_id=request_id,
            details=exc.details,
            retryable=exc.retryable,
            database=(
                request["context"]["database"] if verified_user_id is not None else None
            ),
            company_id=(
                request["context"]["company_id"]
                if verified_user_id is not None
                else None
            ),
            user_id=verified_user_id,
            model=(
                _CAPABILITY_MODELS[capability_id]
                if verified_user_id is not None
                else None
            ),
        ) from exc
    except ConfigError as exc:
        if exc.code in {"unconfigured", "database_unavailable"}:
            exit_code = 4
        elif exc.code in {"company_unavailable", "user_unavailable"}:
            exit_code = 3
        else:
            exit_code = 7
        raise CliError(
            exc.code,
            "No matching Odoo bridge configuration is active.",
            exit_code=exit_code,
            status=_status_for_exit(exit_code),
            capability=capability_id,
            request_id=request_id,
        ) from exc
    except BridgeError as exc:
        raise CliError(
            exc.code,
            str(exc),
            exit_code=exc.exit_code,
            status=_status_for_exit(exc.exit_code),
            capability=capability_id,
            request_id=request_id,
            details=exc.details,
            retryable=exc.retryable,
        ) from exc

    context = request["context"]
    warnings = []
    if descriptor["status"]["value"] == "degraded":
        warnings.append(
            {
                "code": "capability_degraded",
                "reason_code": descriptor["status"]["reason_code"],
            }
        )
    document = success_document(
        capability_id,
        data,
        request_id=request_id,
        warnings=warnings,
        database=context["database"],
        company_id=context["company_id"],
        user_id=getattr(port, "user_id", None),
        model=_CAPABILITY_MODELS[capability_id],
        record_ids=(
            [
                request["parameters"][
                    DOCUMENT_EXPORT_SPECS[capability_id]["id_parameter"]
                ]
            ]
            if capability_id in DOCUMENT_EXPORT_CAPABILITY_IDS
            else (
                []
                if (
                    capability_id.startswith("report.")
                    and capability_id
                    not in {
                        "report.catalog.list",
                        "report.catalog.get",
                        "report.external_value.search",
                        "report.external_value.get",
                        "report.budget_definition.search",
                        "report.budget_definition.get",
                        "report.budget_item.search",
                        "report.budget_item.get",
                    }
                )
                or capability_id
                in {
                    "invoice.analysis.summary",
                    "account.return.summary",
                    "journal_item.analysis.summary",
                    "inventory.on_hand.summary",
                    "sale.order.analysis.summary",
                    "purchase.order.analysis.summary",
                }
                else (
                    [data["journal"]["id"]]
                    if capability_id == "journal.accounting_date.resolve"
                    else (
                        [data["company_id"]]
                        if capability_id
                        in {
                            "diagnostic.journal_integrity.inspect",
                            "company.fiscal_year.resolve",
                            "company.lock_dates.inspect",
                            "localization.china.configuration.inspect",
                            "localization.singapore.configuration.inspect",
                        }
                        else (
                            (
                                [data["fiscal_position"]["id"]]
                                if data["fiscal_position"] is not None
                                else []
                            )
                            if capability_id == "fiscal_position.resolve"
                            else (
                                [data["company"]["id"]]
                                if capability_id
                                == "company.accounting_configuration.inspect"
                                else (
                                    []
                                    if capability_id
                                    == "diagnostic.accounting_environment.inspect"
                                    else (
                                        [data["user"]["id"]]
                                        if capability_id
                                        == "user.accounting_access.inspect"
                                        else (
                                            [
                                                data["from_currency"]["id"],
                                                data["to_currency"]["id"],
                                            ]
                                            if capability_id == "currency.convert"
                                            else (
                                                [data["entry_id"]]
                                                if capability_id
                                                == "validation.journal_entry.check"
                                                else (
                                                    [data["product"]["id"]]
                                                    if capability_id
                                                    in {
                                                        "product.accounting_profile.get",
                                                        "inventory.availability.inspect",
                                                    }
                                                    else (
                                                        [data["transaction"]["id"]]
                                                        if capability_id
                                                        == "bank.transaction.reconciliation.get"
                                                        else (
                                                            [data["id"]]
                                                            if capability_id
                                                            in {
                                                                "journal_entry.get",
                                                                "invoice.get",
                                                                "invoice.payment_status.inspect",
                                                                "fiscal_year.get",
                                                                "payment.get",
                                                                "account.return.get",
                                                                "account.return.check.get",
                                                                "purchase_bill.matching.inspect",
                                                                "sale_invoice.stock_link.inspect",
                                                                "asset.get",
                                                                "stock.transfer.get",
                                                                "sale.order.get",
                                                                "purchase.order.get",
                                                                *CORE_OBJECT_GET_CAPABILITY_IDS,
                                                            }
                                                            else (
                                                                [data["asset"]["id"]]
                                                                if capability_id
                                                                == "asset.depreciation_schedule.get"
                                                                else (
                                                                    [
                                                                        request[
                                                                            "parameters"
                                                                        ][
                                                                            "fiscal_position_id"
                                                                        ]
                                                                    ]
                                                                    if capability_id
                                                                    == "fiscal_position.tax_mapping.list"
                                                                    else (
                                                                        [
                                                                            record[
                                                                                "record_id"
                                                                            ]
                                                                            for record in data[
                                                                                "result"
                                                                            ][
                                                                                "records"
                                                                            ]
                                                                        ]
                                                                        if capability_id
                                                                        in ACCOUNTING_DELIVERY_READ_CAPABILITY_IDS
                                                                        else [
                                                                            item[
                                                                                "id"
                                                                            ]
                                                                            for item in data[
                                                                                "items"
                                                                            ]
                                                                        ]
                                                                    )
                                                                )
                                                            )
                                                        )
                                                    )
                                                )
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            )
        ),
    )
    try:
        registry.validate_instance(descriptor["schemas"]["response"], document)
    except InstanceValidationError as exc:
        raise CliError(
            "failed_validation",
            "The Odoo result does not match the capability schema.",
            exit_code=8,
            status="failed_validation",
            capability=capability_id,
            request_id=request_id,
        ) from exc
    return document


def _execute_write_run(
    capability_id: str,
    request_source: str,
    idempotency_key: str,
    confirmation: str,
    *,
    stdin: TextIO,
    port_factory: PortFactory | None,
) -> dict[str, Any]:
    registry = load_registry()
    try:
        descriptor = registry.describe(capability_id)
    except CapabilityNotFound as exc:
        raise CliError(
            "capability_not_found",
            "The requested capability is not registered.",
            exit_code=4,
            status="unavailable",
            capability=capability_id,
            idempotency_key=idempotency_key,
        ) from exc
    if descriptor["access"] != "write":
        raise CliError(
            "policy_denied",
            "The requested capability is not a write capability.",
            exit_code=3,
            status="denied",
            capability=capability_id,
            idempotency_key=idempotency_key,
        )
    is_core_write = (
        capability_id in CORE_WRITE_CAPABILITY_IDS
        and descriptor["handler_key"] == "core_write"
    )
    is_accounting_delivery_write = (
        capability_id in ACCOUNTING_DELIVERY_WRITE_CAPABILITY_IDS
        and descriptor["handler_key"] == "accounting_delivery"
    )
    if not (is_core_write or is_accounting_delivery_write):
        raise CliError(
            "capability_unavailable",
            "The registered write capability has no allowlisted handler.",
            exit_code=4,
            status="unavailable",
            capability=capability_id,
            idempotency_key=idempotency_key,
        )
    if descriptor["status"]["value"] not in {
        "available",
        "degraded",
        "unconfigured",
    }:
        raise CliError(
            "capability_unavailable",
            "The requested capability is not currently available.",
            exit_code=4,
            status="unavailable",
            capability=capability_id,
            details={"reason_code": descriptor["status"]["reason_code"]},
            idempotency_key=idempotency_key,
        )

    try:
        request = _load_request(request_source, stdin)
    except CliError as exc:
        raise CliError(
            exc.code,
            str(exc),
            exit_code=exc.exit_code,
            status=exc.status,
            capability=capability_id,
            request_id=exc.request_id,
            details=exc.details,
            retryable=exc.retryable,
            idempotency_key=idempotency_key,
        ) from exc
    request_id = _safe_request_id(request)
    try:
        registry.validate_instance(descriptor["schemas"]["request"], request)
        if is_core_write:
            validate_core_write_request(capability_id, request)
        else:
            validate_accounting_delivery_request(capability_id, request)
    except InstanceValidationError as exc:
        raise CliError(
            "invalid_request",
            "The request does not match the capability schema.",
            exit_code=2,
            status="invalid",
            capability=capability_id,
            request_id=request_id,
            idempotency_key=idempotency_key,
        ) from exc
    except (CoreWriteError, AccountingDeliveryError) as exc:
        raise CliError(
            exc.code,
            str(exc),
            exit_code=exc.exit_code,
            status=_status_for_exit(exc.exit_code),
            capability=capability_id,
            request_id=request_id,
            details=exc.details,
            retryable=exc.retryable,
            idempotency_key=idempotency_key,
        ) from exc

    if port_factory is None:
        port_factory = _configured_port_factory
    port: object | None = None
    try:
        port = port_factory(capability_id, request)
        if is_core_write:
            data = execute_core_write(
                port,
                capability_id,
                request,
                idempotency_key,
                confirmation,
            )
        else:
            data = execute_accounting_delivery(
                port,
                capability_id,
                request,
                idempotency_key,
                confirmation,
            )
    except (CoreWriteError, AccountingDeliveryError) as exc:
        verified_user_id = _verified_port_user_id(port)
        raise CliError(
            exc.code,
            str(exc),
            exit_code=exc.exit_code,
            status=_status_for_exit(exc.exit_code),
            capability=capability_id,
            request_id=request_id,
            details=exc.details,
            retryable=exc.retryable,
            database=(
                request["context"]["database"] if verified_user_id is not None else None
            ),
            company_id=(
                request["context"]["company_id"]
                if verified_user_id is not None
                else None
            ),
            user_id=verified_user_id,
            model=(
                _CAPABILITY_MODELS[capability_id]
                if verified_user_id is not None
                else None
            ),
            idempotency_key=idempotency_key,
        ) from exc
    except ConfigError as exc:
        if exc.code in {"unconfigured", "database_unavailable"}:
            exit_code = 4
        elif exc.code in {"company_unavailable", "user_unavailable"}:
            exit_code = 3
        else:
            exit_code = 7
        raise CliError(
            exc.code,
            "No matching Odoo bridge configuration is active.",
            exit_code=exit_code,
            status=_status_for_exit(exit_code),
            capability=capability_id,
            request_id=request_id,
            idempotency_key=idempotency_key,
        ) from exc
    except BridgeError as exc:
        raise CliError(
            exc.code,
            str(exc),
            exit_code=exc.exit_code,
            status=_status_for_exit(exc.exit_code),
            capability=capability_id,
            request_id=request_id,
            details=exc.details,
            retryable=exc.retryable,
            idempotency_key=idempotency_key,
        ) from exc

    context = request["context"]
    result = data["result"]
    if is_accounting_delivery_write:
        if capability_id in {
            "invoice.send",
            "payment.receipt.send",
            "report.customer_statement.send",
            "report.followup.send",
        }:
            record_ids = result["record_ids"]
            verification = {
                "processed_count": result["processed_count"],
                "idempotent_replay": data["idempotent_replay"],
            }
        else:
            record_ids = [result["record_id"]]
            verification = {
                "no_followup": result["no_followup"],
                "idempotent_replay": data["idempotent_replay"],
            }
        warnings = []
        if descriptor["status"]["value"] == "degraded":
            warnings.append(
                {
                    "code": "capability_degraded",
                    "reason_code": descriptor["status"]["reason_code"],
                }
            )
        model = _CAPABILITY_MODELS[capability_id]
        document = success_document(
            capability_id,
            data,
            request_id=request_id,
            warnings=warnings,
            database=context["database"],
            company_id=context["company_id"],
            user_id=getattr(port, "user_id", None),
            model=model,
            record_ids=record_ids,
            idempotency_key=idempotency_key,
            verification=verification,
        )
        try:
            registry.validate_instance(descriptor["schemas"]["response"], document)
        except InstanceValidationError as exc:
            raise CliError(
                "failed_validation",
                "The Odoo result does not match the capability schema.",
                exit_code=8,
                status="failed_validation",
                capability=capability_id,
                request_id=request_id,
                database=context["database"],
                company_id=context["company_id"],
                user_id=_verified_port_user_id(port),
                model=model,
                record_ids=record_ids,
                idempotency_key=idempotency_key,
            ) from exc
        return document

    if capability_id in _BATCH_LIFECYCLE_CAPABILITY_IDS and "items" in result:
        record_ids = [item["id"] for item in result["items"]]
        result_model = _CAPABILITY_MODELS[capability_id]
        verification = {
            "processed_count": result["processed_count"],
            "idempotent_replay": data["idempotent_replay"],
        }
    else:
        result_id = result["id"]
        if capability_id in {
            "deferred_expense.generate_entries",
            "deferred_revenue.generate_entries",
            "multicurrency.revaluation.generate_entries",
        }:
            record_ids = sorted({result["source_id"], result_id})
        else:
            record_ids = (
                [result_id] if isinstance(result_id, int) else result["line_ids"]
            )
        result_model = result["model"]
        verification = {
            "company_id": result["company_id"],
            "state": result["state"],
            "reconciled": result["reconciled"],
            "idempotent_replay": data["idempotent_replay"],
        }
    warnings = []
    if descriptor["status"]["value"] == "degraded":
        warnings.append(
            {
                "code": "capability_degraded",
                "reason_code": descriptor["status"]["reason_code"],
            }
        )
    document = success_document(
        capability_id,
        data,
        request_id=request_id,
        warnings=warnings,
        database=context["database"],
        company_id=context["company_id"],
        user_id=getattr(port, "user_id", None),
        model=result_model,
        record_ids=record_ids,
        idempotency_key=idempotency_key,
        verification=verification,
    )
    try:
        registry.validate_instance(descriptor["schemas"]["response"], document)
    except InstanceValidationError as exc:
        raise CliError(
            "failed_validation",
            "The Odoo result does not match the capability schema.",
            exit_code=8,
            status="failed_validation",
            capability=capability_id,
            request_id=request_id,
            database=context["database"],
            company_id=context["company_id"],
            user_id=_verified_port_user_id(port),
            model=result_model,
            record_ids=record_ids,
            idempotency_key=idempotency_key,
        ) from exc
    return document


def _configured_port_factory(capability_id: str, request: dict[str, Any]) -> object:
    if capability_id not in _CAPABILITY_MODELS:
        raise ConfigError("capability_unavailable", "The capability is unavailable.")
    configured_path = os.environ.get("ODOO_ACCOUNTING_CLI_V4_CONFIG")
    path = Path(configured_path) if configured_path else _DEFAULT_RUNTIME_CONFIG
    context = request["context"]
    target = load_runtime_config(path).resolve(
        context["database"], context["company_id"], context["user_login"]
    )
    client = OdooBridgeClient(
        target,
        language=context["language"],
        timezone=context["timezone"],
    )
    if capability_id == "account.account.list":
        return OdooAccountListPort(client)
    if capability_id in CORE_OBJECT_READ_CAPABILITY_IDS:
        return OdooCoreObjectReadPort(client)
    if capability_id == "report.budget":
        return OdooBudgetReportPort(client)
    if capability_id in CORE_WRITE_CAPABILITY_IDS:
        return OdooCoreWritePort(client)
    if capability_id in ACCOUNTING_DELIVERY_CAPABILITY_IDS:
        return OdooAccountingDeliveryPort(client)
    if capability_id == "partner.accounting.search":
        return OdooPartnerAccountingPort(client)
    if capability_id in {
        "account.return.search",
        "account.return.get",
        "account.return.summary",
        "account.return.type.list",
        "account.return.check.list",
        "account.return.check.get",
    }:
        return OdooAccountReturnPort(client)
    if capability_id in {
        "invoice.search",
        "invoice.get",
        "invoice.payment_status.inspect",
    }:
        return OdooInvoicePort(client)
    if capability_id in {
        "invoice.analysis.search",
        "invoice.analysis.summary",
    }:
        return OdooInvoiceAnalysisPort(client)
    if capability_id in {
        "receivable.open_items.list",
        "payable.open_items.list",
    }:
        return OdooOpenItemsPort(client, capability_id)
    if capability_id in {"payment.search", "payment.get"}:
        return OdooPaymentPort(client)
    if capability_id == "reconciliation.candidates.list":
        return OdooReconciliationCandidatesPort(client)
    if capability_id == "currency.rate.list":
        return OdooCurrencyRateListPort(client)
    if capability_id == "currency.convert":
        return OdooCurrencyConvertPort(client)
    if capability_id in {
        "journal_entry.search",
        "journal_entry.get",
        "validation.journal_entry.check",
    }:
        return OdooJournalEntryPort(client)
    if capability_id in {
        "journal.accounting_date.resolve",
        "journal_item.analysis.summary",
    }:
        return OdooJournalAnalysisPort(client)
    if capability_id == "bank.transaction.list":
        return OdooBankTransactionListPort(client)
    if capability_id == "bank.transaction.search":
        return OdooBankTransactionSearchPort(client)
    if capability_id in {
        "bank.transaction.reconciliation.get",
        "bank.transaction.match_candidates.list",
    }:
        return OdooBankReconciliationPort(client)
    if capability_id == "product.accounting_profile.get":
        return OdooProductAccountingProfilePort(client)
    if capability_id == "fiscal_position.resolve":
        return OdooFiscalPositionResolvePort(client)
    if capability_id == "diagnostic.journal_integrity.inspect":
        return OdooJournalIntegrityPort(client)
    if capability_id in {
        "company.fiscal_year.resolve",
        "company.lock_dates.inspect",
        "fiscal_year.get",
        "fiscal_year.search",
    }:
        return OdooPeriodContextPort(client)
    if capability_id in {
        "asset.search",
        "asset.get",
        "asset.depreciation_schedule.get",
    }:
        return OdooAssetPort(client)
    if capability_id in {
        "cogs.entries.list",
        "inventory.accounting_entries.list",
        "report.inventory_valuation",
        "purchase_bill.matching.inspect",
        "sale_invoice.stock_link.inspect",
    }:
        return OdooInventoryAccountingPort(client)
    if capability_id in {
        "product.category.list",
        "warehouse.list",
        "stock.location.list",
        "stock.operation_type.list",
        "stock.route.list",
    }:
        return OdooInventoryMasterPort(client)
    if capability_id in {
        "stock.transfer.search",
        "stock.transfer.get",
        "stock.move.search",
        "inventory.on_hand.summary",
        "inventory.availability.inspect",
    }:
        return OdooInventoryOperationsPort(client)
    if capability_id in {
        "sale.order.search",
        "sale.order.get",
        "sale.order.line.search",
        "sale.order.analysis.summary",
        "purchase.order.search",
        "purchase.order.get",
        "purchase.order.line.search",
        "purchase.order.analysis.summary",
    }:
        return OdooOrderDocumentsPort(client)
    if capability_id == "user.accounting_access.inspect":
        return OdooAccountingAccessPort(client)
    if capability_id in {
        "company.accounting_configuration.inspect",
        "diagnostic.accounting_environment.inspect",
    }:
        return OdooEnvironmentInspectionPort(client, capability_id)
    if capability_id in LOCALIZATION_CONFIGURATION_CAPABILITY_IDS:
        return OdooLocalizationConfigurationPort(client)
    if capability_id in DOCUMENT_EXPORT_CAPABILITY_IDS:
        return OdooDocumentExportPort(client)
    if capability_id in FINANCIAL_REPORT_EXPORT_CAPABILITY_IDS:
        return OdooFinancialReportExportPort(client)
    if capability_id in {
        "report.trial_balance",
        "report.balance_sheet",
        "report.profit_and_loss",
        "report.cash_flow",
        "report.tax",
        "report.customer_statement",
        "report.followup",
        "report.bank_reconciliation",
        "report.general_ledger",
        "report.partner_ledger",
        "report.aged_receivable",
        "report.aged_payable",
        "report.journal",
        "report.executive_summary",
        "report.asset",
        "report.deferred_expense",
        "report.deferred_revenue",
        "report.multicurrency_revaluation",
        "report.china.balance_sheet",
        "report.china.profit_and_loss",
        "report.china.cash_flow",
        "report.singapore.gst",
    }:
        return OdooFinancialReportPort(client, capability_id)
    return OdooMasterDataPort(client, capability_id)


def main(
    argv: Sequence[str] | None = None,
    *,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    port_factory: PortFactory | None = None,
) -> int:
    input_stream = stdin or sys.stdin
    output_stream = stdout or sys.stdout
    error_stream = stderr or sys.stderr
    try:
        args = _parser().parse_args(argv)
        if args.command == "version":
            _emit(
                {
                    "product": "odoo-accounting-cli-v4",
                    "version": __version__,
                    "status": "bootstrap",
                },
                output_stream,
            )
            return 0
        if (
            args.command == "doctor"
            or args.command == "operations"
            or (args.command == "write" and args.write_command != "run")
        ):
            if args.command == "operations":
                capability = f"operations.{args.operations_command}"
            elif args.command == "write":
                capability = f"write.{args.write_command}"
            else:
                capability = "doctor"
            raise CliError(
                "command_unavailable",
                "This stable command is not implemented in the current bootstrap.",
                exit_code=4,
                status="unavailable",
                capability=capability,
            )
        if args.command == "capabilities":
            if args.capabilities_command == "list":
                document = _list_capabilities()
            elif args.capabilities_command == "describe":
                document = _describe_capability(args.capability_id)
            else:  # pragma: no cover - argparse enforces the choices
                raise AssertionError("unhandled capabilities command")
        elif args.command == "read":
            document = _execute_read(
                args.capability_id,
                args.request_source,
                stdin=input_stream,
                port_factory=port_factory,
            )
        elif args.command == "write" and args.write_command == "run":
            document = _execute_write_run(
                args.capability_id,
                args.request_source,
                args.idempotency_key,
                args.confirm,
                stdin=input_stream,
                port_factory=port_factory,
            )
        else:  # pragma: no cover - argparse enforces the choices
            raise AssertionError(f"unhandled command: {args.command}")
        _emit(document, output_stream)
        return 0
    except CliError as exc:
        _emit(
            error_document(
                _safe_capability(exc.capability),
                exc.code,
                str(exc),
                request_id=exc.request_id,
                status=exc.status,
                details=exc.details,
                retryable=exc.retryable,
                database=exc.database,
                company_id=exc.company_id,
                user_id=exc.user_id,
                model=exc.model,
                record_ids=exc.record_ids,
                idempotency_key=exc.idempotency_key,
            ),
            output_stream,
        )
        return exc.exit_code
    except (RegistryError, InstanceValidationError):
        error_stream.write("registry validation failed\n")
        _emit(
            error_document(
                "registry",
                "registry_invalid",
                "The installed capability registry failed validation.",
                status="failed_validation",
            ),
            output_stream,
        )
        return 8
    except Exception:  # noqa: BLE001 - keep unexpected runtime details out of CLI output
        error_stream.write("internal runtime failure\n")
        _emit(
            error_document(
                _safe_capability(getattr(locals().get("args"), "capability_id", "cli")),
                "runtime_error",
                "The command failed without exposing internal details.",
                status="failed",
                retryable=False,
            ),
            output_stream,
        )
        return 7
