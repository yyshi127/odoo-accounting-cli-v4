from __future__ import annotations

import io
import json
from functools import partial
from typing import Any

import pytest

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4.bridge.core_object_reads import OdooCoreObjectReadPort
from odoo_accounting_cli_v4.capabilities.core_object_reads import (
    read_core_object,
    validate_core_object_read_request,
)
from odoo_accounting_cli_v4.registry import load_registry

REQUEST_ID = "7bc39413-0d69-4092-9319-795d33f3167c"

CAPABILITIES = {
    "account.account.get": ("account_account_get", "account.account"),
    "account.tag.get": ("account_tag_get", "account.account.tag"),
    "account.tag.list": ("account_tag_list", "account.account.tag"),
    "analytic.account.get": ("analytic_account_get", "account.analytic.account"),
    "analytic.account.search": (
        "analytic_account_search",
        "account.analytic.account",
    ),
    "analytic.plan.get": ("analytic_plan_get", "account.analytic.plan"),
    "analytic.plan.list": ("analytic_plan_list", "account.analytic.plan"),
    "analytic.line.search": ("analytic_line_search", "account.analytic.line"),
    "analytic.line.get": ("analytic_line_get", "account.analytic.line"),
    "analytic.distribution_model.list": (
        "analytic_distribution_model_list",
        "account.analytic.distribution.model",
    ),
    "analytic.distribution_model.get": (
        "analytic_distribution_model_get",
        "account.analytic.distribution.model",
    ),
    "analytic.applicability.list": (
        "analytic_applicability_list",
        "account.analytic.applicability",
    ),
    "analytic.applicability.get": (
        "analytic_applicability_get",
        "account.analytic.applicability",
    ),
    "budget.search": ("budget_search", "budget.analytic"),
    "budget.get": ("budget_get", "budget.analytic"),
    "budget.line.list": ("budget_line_list", "budget.line"),
    "budget.line.get": ("budget_line_get", "budget.line"),
    "bank.statement.get": ("bank_statement_get", "account.bank.statement"),
    "bank.statement.search": (
        "bank_statement_search",
        "account.bank.statement",
    ),
    "journal.get": ("journal_get", "account.journal"),
    "tax.get": ("tax_get", "account.tax"),
    "payment_term.get": ("payment_term_get", "account.payment.term"),
    "currency.get": ("currency_get", "res.currency"),
    "fiscal_position.get": ("fiscal_position_get", "account.fiscal.position"),
    "fiscal_position.search": (
        "fiscal_position_search",
        "account.fiscal.position",
    ),
    "fiscal_position.account_mapping.list": (
        "fiscal_position_account_mapping_list",
        "account.fiscal.position.account",
    ),
    "fiscal_position.tax_mapping.list": (
        "fiscal_position_tax_mapping_list",
        "account.fiscal.position",
    ),
    "partner.accounting.get": ("partner_accounting_get", "res.partner"),
    "partner.bank_account.get": ("partner_bank_account_get", "res.partner.bank"),
    "partner.bank_account.search": (
        "partner_bank_account_search",
        "res.partner.bank",
    ),
    "bank.transaction.get": (
        "bank_transaction_get",
        "account.bank.statement.line",
    ),
    "journal_item.search": ("journal_item_search", "account.move.line"),
    "journal_item.get": ("journal_item_get", "account.move.line"),
    "payment.method.get": (
        "payment_method_get",
        "account.payment.method.line",
    ),
    "payment.method.list": (
        "payment_method_list",
        "account.payment.method.line",
    ),
    "reconciliation.model.get": (
        "reconciliation_model_get",
        "account.reconcile.model",
    ),
    "reconciliation.model.list": (
        "reconciliation_model_list",
        "account.reconcile.model",
    ),
    "reconciliation.full.get": (
        "reconciliation_full_get",
        "account.full.reconcile",
    ),
    "reconciliation.full.list": (
        "reconciliation_full_list",
        "account.full.reconcile",
    ),
    "reconciliation.partial.get": (
        "reconciliation_partial_get",
        "account.partial.reconcile",
    ),
    "reconciliation.partial.list": (
        "reconciliation_partial_list",
        "account.partial.reconcile",
    ),
    "cash_rounding.get": ("cash_rounding_get", "account.cash.rounding"),
    "cash_rounding.list": ("cash_rounding_list", "account.cash.rounding"),
    "journal.group.get": ("journal_group_get", "account.journal.group"),
    "journal.group.list": ("journal_group_list", "account.journal.group"),
    "incoterm.get": ("incoterm_get", "account.incoterms"),
    "incoterm.list": ("incoterm_list", "account.incoterms"),
    "product.get": ("product_get", "product.product"),
    "product.search": ("product_search", "product.product"),
    "tax.group.get": ("tax_group_get", "account.tax.group"),
    "tax.group.list": ("tax_group_list", "account.tax.group"),
}

GET_ID_FIELDS = {
    "account.account.get": ("account_id", 31),
    "account.tag.get": ("tag_id", 31),
    "analytic.account.get": ("analytic_account_id", 31),
    "analytic.plan.get": ("plan_id", 31),
    "bank.statement.get": ("bank_statement_id", 31),
    "journal.get": ("journal_id", 9),
    "tax.get": ("tax_id", 31),
    "payment_term.get": ("payment_term_id", 31),
    "currency.get": ("currency_id", 6),
    "fiscal_position.get": ("fiscal_position_id", 31),
    "partner.accounting.get": ("partner_id", 31),
    "partner.bank_account.get": ("partner_bank_id", 31),
    "bank.transaction.get": ("transaction_id", 31),
    "journal_item.get": ("line_id", 31),
    "payment.method.get": ("payment_method_line_id", 31),
    "reconciliation.model.get": ("reconciliation_model_id", 31),
    "reconciliation.full.get": ("full_reconcile_id", 31),
    "reconciliation.partial.get": ("partial_reconcile_id", 31),
    "cash_rounding.get": ("cash_rounding_id", 31),
    "journal.group.get": ("journal_group_id", 31),
    "incoterm.get": ("incoterm_id", 31),
    "product.get": ("product_id", 31),
    "tax.group.get": ("tax_group_id", 31),
    "analytic.line.get": ("analytic_line_id", 31),
    "analytic.distribution_model.get": ("distribution_model_id", 31),
    "analytic.applicability.get": ("applicability_id", 31),
    "budget.get": ("budget_id", 31),
    "budget.line.get": ("budget_line_id", 31),
}

SEARCH_PARAMETERS = {
    "bank.statement.search": {
        "journal_id": 9,
        "date_from": "2026-08-01",
        "date_to": "2026-08-31",
        "limit": 1,
    },
    "product.search": {"query": "Fixture", "active": True, "limit": 1},
    "analytic.account.search": {
        "query": "Fixture",
        "active": True,
        "plan_id": 71,
        "limit": 1,
    },
    "fiscal_position.search": {
        "query": "Fixture",
        "active": True,
        "auto_apply": False,
        "limit": 1,
    },
    "fiscal_position.account_mapping.list": {
        "fiscal_position_id": 31,
        "limit": 1,
    },
    "fiscal_position.tax_mapping.list": {
        "fiscal_position_id": 31,
        "limit": 1,
    },
    "partner.bank_account.search": {
        "partner_id": 16,
        "active": True,
        "limit": 1,
    },
    "analytic.line.search": {
        "query": "Project",
        "date_from": "2026-08-01",
        "date_to": "2026-08-31",
        "analytic_account_id": 31,
        "limit": 1,
    },
    "budget.search": {
        "query": "FY2026",
        "state": "confirmed",
        "budget_type": "both",
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
        "limit": 1,
    },
    "budget.line.list": {
        "budget_id": 31,
        "plan_id": 21,
        "analytic_account_id": 31,
        "limit": 1,
    },
}


def _request(parameters: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "context": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "zh_CN",
            "timezone": "Asia/Shanghai",
        },
        "parameters": parameters,
    }


def _coded(record_id: int, code: str, name: str) -> dict[str, Any]:
    return {"id": record_id, "code": code, "name": name}


def _item(capability_id: str) -> dict[str, Any]:
    if capability_id in {
        "partner.bank_account.search",
        "partner.bank_account.get",
    }:
        return {
            "id": 31,
            "acc_number": "CN-FIXTURE-31",
            "account_holder_name": "Fixture Partner",
            "account_type": "bank",
            "active": True,
            "sequence": 10,
            "account_holder": {"id": 16, "name": "Fixture Partner"},
            "allow_out_payment": False,
            "bank": {"id": 21, "name": "Fixture Bank", "bic": None},
            "currency": {"id": 6, "code": "CNY"},
            "company_id": 7,
            "linked_journal": _coded(9, "BNK1", "Bank"),
        }
    if capability_id in {"bank.statement.search", "bank.statement.get"}:
        return {
            "id": 31,
            "name": "BNK1 Statement 2026-08-24",
            "reference": "STATEMENT-31",
            "date": "2026-08-24",
            "company_id": 7,
            "journal": _coded(9, "BNK1", "Bank"),
            "currency": {"id": 6, "code": "CNY"},
            "balance_start": "0",
            "balance_end": "125.5",
            "balance_end_real": "125.5",
            "is_complete": True,
            "is_valid": True,
            "problem_description": None,
            "transaction_count": 1,
        }
    if capability_id in {
        "reconciliation.partial.list",
        "reconciliation.partial.get",
    }:
        return {
            "id": 31,
            "company_id": 7,
            "max_date": "2026-08-24",
            "amount": "125.5",
            "company_currency": {"id": 6, "code": "CNY"},
            "debit_amount_currency": "125.5",
            "debit_currency": {"id": 6, "code": "CNY"},
            "credit_amount_currency": "125.5",
            "credit_currency": {"id": 6, "code": "CNY"},
            "debit_journal_item_id": 61,
            "credit_journal_item_id": 62,
            "full_reconcile_id": 31,
            "exchange_move_id": None,
            "matching_number": "31",
        }
    if capability_id in {
        "reconciliation.full.list",
        "reconciliation.full.get",
    }:
        return {
            "id": 31,
            "company_id": 7,
            "matching_number": "31",
            "partial_reconcile_ids": [31],
            "reconciled_journal_item_ids": [61, 62],
        }
    if capability_id in {"product.search", "product.get"}:
        return {
            "id": 31,
            "name": "Fixture Product",
            "default_code": "PROD-31",
            "active": True,
            "product_type": "consu",
            "is_storable": True,
            "template": {"id": 131, "name": "Fixture Product"},
            "category": {"id": 41, "name": "All"},
            "uom": {"id": 1, "name": "Units"},
            "company_id": 7,
            "currency": {"id": 6, "code": "CNY"},
            "standard_price": "80",
            "list_price": "125.5",
        }
    if capability_id in {"analytic.plan.list", "analytic.plan.get"}:
        return {
            "id": 31,
            "name": "Projects",
            "complete_name": "Projects",
            "parent": None,
            "color": 3,
        }
    if capability_id in {"analytic.account.search", "analytic.account.get"}:
        return {
            "id": 31,
            "name": "Fixture Analytic Account",
            "code": "ANA-31",
            "active": True,
            "plan": {"id": 71, "name": "Projects"},
            "partner": {"id": 16, "name": "Fixture Partner"},
            "company_id": 7,
            "currency": {"id": 6, "code": "CNY"},
            "balance": "125.5",
        }
    if capability_id in {"analytic.line.search", "analytic.line.get"}:
        return {
            "id": 31,
            "date": "2026-08-24",
            "name": "Project effort",
            "reference": None,
            "amount": "125.5",
            "unit_amount": "2",
            "company_id": 7,
            "currency": {"id": 6, "code": "CNY"},
            "analytic_accounts": [{"id": 31, "name": "Project Alpha"}],
            "partner": {"id": 16, "name": "Fixture Partner"},
            "product": {"id": 51, "name": "Consulting"},
            "uom": {"id": 1, "name": "Hours"},
            "general_account": _coded(701, "600000", "Consulting Expense"),
            "journal_item_id": 301,
        }
    if capability_id in {
        "analytic.distribution_model.list",
        "analytic.distribution_model.get",
    }:
        return {
            "id": 31,
            "sequence": 10,
            "company_id": 7,
            "account_prefix": "6",
            "partner": {"id": 16, "name": "Fixture Partner"},
            "partner_category": {"id": 17, "name": "Preferred"},
            "product": {"id": 51, "name": "Consulting"},
            "product_category": {"id": 18, "name": "Services"},
            "allocations": [
                {
                    "analytic_accounts": [
                        {"id": 31, "name": "Project Alpha"},
                        {"id": 41, "name": "Department One"},
                    ],
                    "percentage": "100",
                }
            ],
        }
    if capability_id in {
        "analytic.applicability.list",
        "analytic.applicability.get",
    }:
        return {
            "id": 31,
            "plan": {"id": 21, "name": "Projects"},
            "business_domain": "invoice",
            "applicability": "mandatory",
            "company_id": 7,
            "account_prefix": "4",
            "product_category": {"id": 18, "name": "Services"},
        }
    if capability_id in {"budget.search", "budget.get"}:
        return {
            "id": 31,
            "name": "FY2026 Operating Budget",
            "date_from": "2026-01-01",
            "date_to": "2026-12-31",
            "state": "confirmed",
            "budget_type": "both",
            "company_id": 7,
            "responsible": {"id": 5, "name": "V4 Accountant"},
            "revision_of": None,
        }
    if capability_id in {"budget.line.list", "budget.line.get"}:
        return {
            "id": 31,
            "sequence": 10,
            "budget": {"id": 31, "name": "FY2026 Operating Budget"},
            "date_from": "2026-01-01",
            "date_to": "2026-12-31",
            "budget_amount": "100000",
            "achieved_amount": "25000",
            "achieved_percentage": "25",
            "theoretical_amount": "66666.67",
            "theoretical_percentage": "66.66667",
            "above_budget": False,
            "state": "confirmed",
            "currency": {"id": 6, "code": "CNY"},
            "company_id": 7,
            "analytic_accounts": [{"id": 31, "name": "Project Alpha"}],
        }
    if capability_id in {"fiscal_position.search", "fiscal_position.get"}:
        return {
            "id": 31,
            "name": "Fixture Fiscal Position",
            "active": True,
            "auto_apply": False,
            "vat_required": False,
            "country": {"id": 45, "name": "China"},
            "country_group": None,
            "states": [
                {"id": 44, "name": "Beijing"},
                {"id": 45, "name": "Shanghai"},
            ],
            "company_id": 7,
            "foreign_vat": None,
        }
    if capability_id in {"account.tag.list", "account.tag.get"}:
        return {
            "id": 31,
            "name": "Fixture Tax Tag",
            "applicability": "taxes",
            "active": True,
            "color": 2,
            "country": {"id": 45, "name": "China"},
        }
    if capability_id in {"tax.group.list", "tax.group.get"}:
        return {
            "id": 31,
            "name": "Fixture VAT",
            "sequence": 10,
            "country": {"id": 45, "name": "China"},
            "preceding_subtotal": None,
            "company_id": 7,
        }
    if capability_id == "account.account.get":
        return {
            "id": 31,
            "code": "1000",
            "name": "Cash",
            "account_type": "asset_cash",
            "active": True,
            "reconcile": False,
            "company_ids": [7],
        }
    if capability_id == "journal.get":
        return {
            "id": 9,
            "sequence": 10,
            "code": "BNK1",
            "name": "Bank",
            "type": "bank",
            "active": True,
            "currency": None,
            "company_id": 7,
        }
    if capability_id == "tax.get":
        return {
            "id": 31,
            "sequence": 1,
            "name": "VAT 13%",
            "type_tax_use": "sale",
            "amount_type": "percent",
            "amount": "13",
            "price_include": False,
            "include_base_amount": False,
            "is_base_affected": True,
            "active": True,
            "tax_group": {"id": 5, "name": "VAT"},
            "company_id": 7,
        }
    if capability_id == "payment_term.get":
        return {
            "id": 31,
            "sequence": 10,
            "name": "30 Days",
            "active": True,
            "company_id": None,
            "display_on_invoice": True,
            "early_discount": False,
            "discount_percentage": "0",
            "discount_days": 0,
            "early_pay_discount_computation": "included",
            "lines": [
                {
                    "id": 301,
                    "value": "percent",
                    "value_amount": "100",
                    "delay_type": "days_after",
                    "nb_days": 30,
                    "days_next_month": None,
                }
            ],
        }
    if capability_id == "currency.get":
        return {
            "id": 6,
            "code": "CNY",
            "name": "Chinese Yuan",
            "symbol": "¥",
            "rounding": "0.01",
            "decimal_places": 2,
            "active": True,
            "position": "before",
            "is_company_currency": True,
        }
    if capability_id == "partner.accounting.get":
        return {
            "id": 31,
            "complete_name": "Fixture Partner",
            "ref": "PARTNER-31",
            "active": True,
            "is_company": True,
            "company_id": None,
            "customer_rank": 1,
            "supplier_rank": 0,
            "receivable_account": _coded(121, "112200", "Accounts Receivable"),
            "payable_account": _coded(221, "220200", "Accounts Payable"),
        }
    if capability_id == "bank.transaction.get":
        return {
            "id": 31,
            "company_id": 7,
            "date": "2026-08-24",
            "payment_date": None,
            "name": "Customer transfer",
            "reference": "BANK/31",
            "partner": {"id": 16, "name": "Fixture Partner"},
            "journal": _coded(9, "BNK1", "Bank"),
            "amount": "125.5",
            "currency": {"id": 6, "code": "CNY"},
            "move": {
                "id": 302,
                "name": "BNK1/2026/0031",
                "state": "posted",
            },
            "reconciled": False,
        }
    if capability_id in {"journal_item.search", "journal_item.get"}:
        return {
            "id": 31,
            "company_id": 7,
            "date": "2026-08-24",
            "date_maturity": None,
            "move": {
                "id": 301,
                "name": "MISC/2026/0031",
                "state": "posted",
                "move_type": "entry",
            },
            "account": _coded(121, "112200", "Accounts Receivable"),
            "partner": {"id": 16, "name": "Fixture Partner"},
            "journal": _coded(4, "MISC", "Miscellaneous Operations"),
            "name": "Fixture journal item",
            "reference": None,
            "debit": "125.5",
            "credit": "0",
            "balance": "125.5",
            "amount_currency": "125.5",
            "currency": {"id": 6, "code": "CNY"},
            "reconciled": False,
            "matching_number": None,
            "analytic_distribution": {"3,1": "60.125", "1,2": "39.875"},
            "tax_line_id": None,
            "tax_ids": [],
            "tax_base_amount": "0",
        }
    if capability_id in {"payment.method.list", "payment.method.get"}:
        return {
            "id": 31,
            "name": "Manual",
            "payment_type": "inbound",
            "sequence": 10,
            "company_id": 7,
            "payment_method": {
                "id": 2,
                "code": "manual",
                "name": "Manual",
            },
            "journal": _coded(9, "BNK1", "Bank"),
            "payment_account": _coded(101, "100200", "Bank Account"),
        }
    if capability_id in {
        "reconciliation.model.list",
        "reconciliation.model.get",
    }:
        return {
            "id": 31,
            "name": "Bank fees",
            "sequence": 10,
            "active": True,
            "company_id": 7,
            "match_amount": "lower",
            "match_amount_min": "0",
            "match_amount_max": "1000",
            "match_label": "contains",
            "match_label_param": "fee",
        }
    if capability_id in {"cash_rounding.list", "cash_rounding.get"}:
        return {
            "id": 31,
            "name": "Nearest 0.05",
            "rounding": "0.05",
            "strategy": "biggest_tax",
            "rounding_method": "HALF-UP",
            "profit_account": None,
            "loss_account": None,
        }
    if capability_id in {"journal.group.list", "journal.group.get"}:
        return {
            "id": 31,
            "name": "Primary Ledger",
            "sequence": 10,
            "company_id": 7,
            "excluded_journals": [_coded(9, "BNK1", "Bank")],
        }
    if capability_id in {"incoterm.list", "incoterm.get"}:
        return {
            "id": 31,
            "code": "FOB",
            "name": "Free on Board",
            "active": True,
        }
    if capability_id == "fiscal_position.account_mapping.list":
        return {
            "id": 41,
            "company_id": 7,
            "source_account": _coded(101, "4000", "Sales"),
            "destination_account": _coded(102, "4100", "Mapped Sales"),
        }
    if capability_id == "fiscal_position.tax_mapping.list":
        return {
            "source_tax": {"id": 51, "name": "Source Tax"},
            "destination_taxes": [{"id": 52, "name": "Destination Tax"}],
        }
    raise AssertionError(capability_id)


def _parameters(capability_id: str) -> dict[str, Any]:
    if capability_id in GET_ID_FIELDS:
        field, record_id = GET_ID_FIELDS[capability_id]
        return {field: record_id}
    if capability_id in SEARCH_PARAMETERS:
        return dict(SEARCH_PARAMETERS[capability_id])
    return {"limit": 1}


def _runtime_parameters(capability_id: str) -> dict[str, Any]:
    if capability_id in GET_ID_FIELDS:
        return _parameters(capability_id)
    if capability_id in SEARCH_PARAMETERS:
        parameters = _parameters(capability_id)
        parameters["after_id"] = None
        parameters["limit"] = 2
        return parameters
    if capability_id == "journal_item.search":
        return {
            "date_from": None,
            "date_to": None,
            "move_id": None,
            "account_id": None,
            "partner_id": None,
            "journal_id": None,
            "posted_only": False,
            "after_id": None,
            "limit": 2,
        }
    return {"after_id": None, "limit": 2}


REQUESTS = {
    capability_id: _request(_parameters(capability_id))
    for capability_id in CAPABILITIES
}


class _SuccessPort:
    user_id = 42

    def __init__(self, capability_id: str) -> None:
        self.capability_id = capability_id
        self.calls: list[dict[str, Any]] = []

    def read(
        self,
        *,
        capability_id: str,
        company_id: int,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "capability_id": capability_id,
                "company_id": company_id,
                "parameters": parameters,
            }
        )
        page = {
            "user_id": self.user_id,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "cursor_found": True,
            "items": [_item(self.capability_id)],
        }
        if capability_id == "fiscal_position.tax_mapping.list":
            page["removes_all_taxes"] = False
        return page


def _assert_partial(value: object, function: object, capability_id: str) -> None:
    assert isinstance(value, partial)
    assert value.func is function
    assert value.args == (capability_id,)


@pytest.fixture(scope="module")
def registry() -> Any:
    return load_registry()


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_registry_routes_each_capability_to_the_fixed_handler_and_validator(
    capability_id: str, registry: Any
) -> None:
    handler_key, model = CAPABILITIES[capability_id]
    descriptor = registry.describe(capability_id)

    assert descriptor["handler_key"] == handler_key
    _assert_partial(cli._HANDLERS[handler_key], read_core_object, capability_id)
    _assert_partial(
        cli._REQUEST_VALIDATORS[handler_key],
        validate_core_object_read_request,
        capability_id,
    )
    assert cli._CAPABILITY_MODELS[capability_id] == model


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_configured_factory_uses_the_shared_core_object_port(
    capability_id: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = object()
    client = object()

    class RuntimeConfig:
        def resolve(self, database: str, company_id: int, user_login: str) -> object:
            assert (database, company_id, user_login) == (
                "odoo_cli_v4_dev",
                7,
                "v4-agent",
            )
            return target

    def bridge_factory(selected_target: object, **kwargs: str) -> object:
        assert selected_target is target
        assert kwargs == {"language": "zh_CN", "timezone": "Asia/Shanghai"}
        return client

    monkeypatch.setattr(cli, "load_runtime_config", lambda _path: RuntimeConfig())
    monkeypatch.setattr(cli, "OdooBridgeClient", bridge_factory)

    port = cli._configured_port_factory(capability_id, REQUESTS[capability_id])

    assert type(port) is OdooCoreObjectReadPort
    assert port._client is client


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_cli_emits_schema_valid_success_and_exact_odoo_metadata(
    capability_id: str,
    monkeypatch: pytest.MonkeyPatch,
    registry: Any,
) -> None:
    port = _SuccessPort(capability_id)
    monkeypatch.setattr(cli, "load_registry", lambda: registry)

    def port_factory(selected: str, request: dict[str, Any]) -> _SuccessPort:
        assert selected == capability_id
        assert request == REQUESTS[capability_id]
        return port

    stdout = io.StringIO()
    stderr = io.StringIO()
    exit_code = cli.main(
        ["read", capability_id, "--request", "-"],
        stdin=io.StringIO(json.dumps(REQUESTS[capability_id])),
        stdout=stdout,
        stderr=stderr,
        port_factory=port_factory,
    )

    document = json.loads(stdout.getvalue())
    item = _item(capability_id)
    expected_data = (
        item
        if capability_id in GET_ID_FIELDS
        else {
            "items": [item],
            "has_more": False,
            "next_cursor": None,
            **(
                {"removes_all_taxes": False}
                if capability_id == "fiscal_position.tax_mapping.list"
                else {}
            ),
        }
    )
    assert exit_code == 0
    assert stderr.getvalue() == ""
    assert port.calls == [
        {
            "capability_id": capability_id,
            "company_id": 7,
            "parameters": _runtime_parameters(capability_id),
        }
    ]
    assert document["success"] is True
    assert document["capability"] == capability_id
    assert document["status"] == "verified"
    assert document["data"] == expected_data
    assert document["odoo"] == {
        "database": "odoo_cli_v4_dev",
        "company_id": 7,
        "user_id": 42,
        "model": CAPABILITIES[capability_id][1],
        "record_ids": (
            [REQUESTS[capability_id]["parameters"]["fiscal_position_id"]]
            if capability_id == "fiscal_position.tax_mapping.list"
            else [item["id"]]
        ),
    }
    descriptor = registry.describe(capability_id)
    registry.validate_instance(descriptor["schemas"]["response"], document)
