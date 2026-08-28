from __future__ import annotations

from copy import deepcopy

import pytest

from odoo_accounting_cli_v4.capabilities.core_object_reads import (
    CORE_OBJECT_GET_CAPABILITY_IDS,
    CORE_OBJECT_READ_CAPABILITY_IDS,
    CoreObjectReadError,
    read_core_object,
    validate_core_object_read_request,
)

REQUEST_ID = "7bc39413-0d69-4092-9319-795d33f3167c"

GET_ID_FIELDS = {
    "account.account.get": "account_id",
    "journal.get": "journal_id",
    "tax.get": "tax_id",
    "payment_term.get": "payment_term_id",
    "currency.get": "currency_id",
    "partner.get": "partner_id",
    "partner.accounting.get": "partner_id",
    "bank.transaction.get": "transaction_id",
    "journal_item.get": "line_id",
    "product.get": "product_id",
    "analytic.plan.get": "plan_id",
    "analytic.account.get": "analytic_account_id",
    "fiscal_position.get": "fiscal_position_id",
    "account.tag.get": "tag_id",
    "tax.group.get": "tax_group_id",
    "payment.method.get": "payment_method_line_id",
    "reconciliation.model.get": "reconciliation_model_id",
    "cash_rounding.get": "cash_rounding_id",
    "journal.group.get": "journal_group_id",
    "incoterm.get": "incoterm_id",
    "partner.bank_account.get": "partner_bank_id",
    "bank.statement.get": "bank_statement_id",
    "reconciliation.partial.get": "partial_reconcile_id",
    "reconciliation.full.get": "full_reconcile_id",
    "analytic.line.get": "analytic_line_id",
    "analytic.distribution_model.get": "distribution_model_id",
    "analytic.applicability.get": "applicability_id",
    "budget.get": "budget_id",
    "budget.line.get": "budget_line_id",
}
PAGE_CAPABILITIES = (
    "journal_item.search",
    "payment.method.list",
    "reconciliation.model.list",
    "partner.search",
    "product.search",
    "analytic.plan.list",
    "analytic.account.search",
    "fiscal_position.search",
    "account.tag.list",
    "tax.group.list",
    "cash_rounding.list",
    "journal.group.list",
    "incoterm.list",
    "partner.bank_account.search",
    "bank.statement.search",
    "reconciliation.partial.list",
    "reconciliation.full.list",
    "analytic.line.search",
    "analytic.distribution_model.list",
    "analytic.applicability.list",
    "budget.search",
    "budget.line.list",
)
JOURNAL_ITEM_DEFAULTS = {
    "date_from": None,
    "date_to": None,
    "move_id": None,
    "account_id": None,
    "partner_id": None,
    "journal_id": None,
    "posted_only": False,
}
PAGE_DEFAULTS = {
    "journal_item.search": JOURNAL_ITEM_DEFAULTS,
    "payment.method.list": {},
    "reconciliation.model.list": {},
    "partner.search": {
        "query": None,
        "active": None,
        "company_type": None,
        "customer": None,
        "supplier": None,
    },
    "product.search": {"query": None, "active": None},
    "analytic.plan.list": {},
    "analytic.account.search": {"query": None, "active": None, "plan_id": None},
    "fiscal_position.search": {
        "query": None,
        "active": None,
        "auto_apply": None,
    },
    "account.tag.list": {},
    "tax.group.list": {},
    "cash_rounding.list": {},
    "journal.group.list": {},
    "incoterm.list": {},
    "partner.bank_account.search": {"partner_id": None, "active": None},
    "bank.statement.search": {
        "journal_id": None,
        "date_from": None,
        "date_to": None,
    },
    "reconciliation.partial.list": {},
    "reconciliation.full.list": {},
    "analytic.line.search": {
        "query": None,
        "date_from": None,
        "date_to": None,
        "analytic_account_id": None,
    },
    "analytic.distribution_model.list": {},
    "analytic.applicability.list": {},
    "budget.search": {
        "query": None,
        "state": None,
        "budget_type": None,
        "date_from": None,
        "date_to": None,
    },
    "budget.line.list": {
        "budget_id": 71,
        "plan_id": None,
        "analytic_account_id": None,
    },
}


def _request(
    parameters: dict | None = None,
    *,
    database: str = "odoo_cli_v4_dev",
    company_id: int = 7,
    user_login: str = "v4-agent",
) -> dict:
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "context": {
            "database": database,
            "company_id": company_id,
            "user_login": user_login,
            "language": "zh_CN",
            "timezone": "Asia/Shanghai",
        },
        "parameters": deepcopy(parameters) if parameters is not None else {},
    }


def _coded(record_id: int, code: str, name: str) -> dict:
    return {"id": record_id, "code": code, "name": name}


def _item(capability_id: str, record_id: int = 31) -> dict:
    if capability_id == "account.account.get":
        return {
            "id": record_id,
            "code": "1000",
            "name": "Cash",
            "account_type": "asset_cash",
            "active": True,
            "reconcile": False,
            "company_ids": [7],
        }
    if capability_id == "journal.get":
        return {
            "id": record_id,
            "sequence": 10,
            "code": "MISC",
            "name": "Miscellaneous Operations",
            "type": "general",
            "active": True,
            "currency": None,
            "company_id": 7,
        }
    if capability_id == "tax.get":
        return {
            "id": record_id,
            "sequence": 1,
            "name": "VAT 13%",
            "type_tax_use": "sale",
            "amount_type": "percent",
            "amount": "13.00",
            "price_include": False,
            "include_base_amount": False,
            "is_base_affected": True,
            "active": True,
            "tax_group": {"id": 5, "name": "VAT"},
            "company_id": 7,
        }
    if capability_id == "payment_term.get":
        return {
            "id": record_id,
            "sequence": 10,
            "name": "30 Days",
            "active": True,
            "company_id": 7,
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
                    "days_next_month": "10",
                }
            ],
        }
    if capability_id == "currency.get":
        return {
            "id": record_id,
            "code": "CNY",
            "name": "Chinese Yuan",
            "symbol": "¥",
            "rounding": "0.01",
            "decimal_places": 2,
            "active": True,
            "position": "before",
            "is_company_currency": True,
        }
    if capability_id in {"partner.get", "partner.search"}:
        return {
            "id": record_id,
            "name": "Fixture Partner",
            "display_name": "Fixture Partner",
            "company_type": "company",
            "active": True,
            "vat": None,
            "reference": "PARTNER-31",
            "email": "partner@example.com",
            "phone": None,
            "mobile": None,
            "street": "1 Main Street",
            "street2": None,
            "city": "Shanghai",
            "zip": "200000",
            "state": {"id": 3, "name": "Shanghai"},
            "country": {"id": 48, "name": "China"},
            "language": "zh_CN",
            "company_id": None,
            "parent": None,
            "customer_rank": 1,
            "supplier_rank": 0,
        }
    if capability_id == "partner.accounting.get":
        return {
            "id": record_id,
            "complete_name": "Fixture Partner",
            "ref": "PARTNER-31",
            "active": True,
            "is_company": True,
            "company_id": 7,
            "customer_rank": 1,
            "supplier_rank": 0,
            "receivable_account": _coded(121, "112200", "Accounts Receivable"),
            "payable_account": _coded(221, "220200", "Accounts Payable"),
        }
    if capability_id == "bank.transaction.get":
        return {
            "id": record_id,
            "company_id": 7,
            "date": "2026-08-24",
            "payment_date": None,
            "name": "Customer transfer",
            "reference": "BANK/31",
            "partner": {"id": 16, "name": "Fixture Partner"},
            "journal": _coded(9, "BNK1", "Bank"),
            "amount": "125.50",
            "currency": {"id": 6, "code": "CNY"},
            "move": {"id": 301, "name": "BNK1/2026/0031", "state": "posted"},
            "reconciled": False,
        }
    if capability_id in {"journal_item.get", "journal_item.search"}:
        return {
            "id": record_id,
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
            "debit": "125.50",
            "credit": "0",
            "balance": "125.50",
            "amount_currency": "125.50",
            "currency": {"id": 6, "code": "CNY"},
            "reconciled": False,
            "matching_number": None,
        }
    if capability_id in {"product.search", "product.get"}:
        return {
            "id": record_id,
            "name": "Consulting Service",
            "default_code": "CONSULT",
            "active": True,
            "product_type": "service",
            "is_storable": False,
            "template": {"id": 401, "name": "Consulting Template"},
            "category": {"id": 51, "name": "Services"},
            "uom": {"id": 1, "name": "Units"},
            "company_id": None,
            "currency": {"id": 6, "code": "CNY"},
            "standard_price": "100",
            "list_price": "500",
        }
    if capability_id in {"analytic.plan.list", "analytic.plan.get"}:
        return {
            "id": record_id,
            "name": "Projects",
            "complete_name": "Management / Projects",
            "parent": {"id": 90, "name": "Management"},
            "color": 4,
        }
    if capability_id in {"analytic.account.search", "analytic.account.get"}:
        return {
            "id": record_id,
            "name": "Project Alpha",
            "code": "ALPHA",
            "active": True,
            "plan": {"id": 31, "name": "Projects"},
            "partner": {"id": 31, "name": "Fixture Partner"},
            "company_id": None,
            "currency": {"id": 6, "code": "CNY"},
            "balance": "125.5",
        }
    if capability_id in {"fiscal_position.search", "fiscal_position.get"}:
        return {
            "id": record_id,
            "name": "China Domestic",
            "active": True,
            "auto_apply": True,
            "vat_required": False,
            "country": {"id": 156, "name": "China"},
            "country_group": {"id": 77, "name": "Asia"},
            "states": [
                {"id": 91, "name": "Beijing"},
                {"id": 92, "name": "Shanghai"},
            ],
            "company_id": 7,
            "foreign_vat": None,
        }
    if capability_id in {"account.tag.list", "account.tag.get"}:
        return {
            "id": record_id,
            "name": "Operating",
            "applicability": "accounts",
            "active": True,
            "color": 3,
            "country": {"id": 156, "name": "China"},
        }
    if capability_id in {"tax.group.list", "tax.group.get"}:
        return {
            "id": record_id,
            "name": "VAT",
            "sequence": 10,
            "country": {"id": 156, "name": "China"},
            "preceding_subtotal": None,
            "company_id": 7,
        }
    if capability_id in {"payment.method.list", "payment.method.get"}:
        return {
            "id": record_id,
            "name": "Manual",
            "payment_type": "inbound",
            "sequence": 10,
            "company_id": 7,
            "payment_method": {"id": 2, "code": "manual", "name": "Manual"},
            "journal": _coded(9, "BNK1", "Bank"),
            "payment_account": _coded(101, "100200", "Bank Account"),
        }
    if capability_id in {
        "reconciliation.model.list",
        "reconciliation.model.get",
    }:
        return {
            "id": record_id,
            "name": "Bank fees",
            "sequence": 10,
            "active": True,
            "company_id": 7,
            "match_amount": "lower",
            "match_amount_min": "0",
            "match_amount_max": "1000.00",
            "match_label": "contains",
            "match_label_param": "fee",
        }
    if capability_id in {"cash_rounding.list", "cash_rounding.get"}:
        return {
            "id": record_id,
            "name": "Cash rounding 0.05",
            "rounding": "0.05",
            "strategy": "add_invoice_line",
            "rounding_method": "HALF-UP",
            "profit_account": _coded(701, "759000", "Cash Rounding Profit"),
            "loss_account": _coded(702, "659000", "Cash Rounding Loss"),
        }
    if capability_id in {"journal.group.list", "journal.group.get"}:
        return {
            "id": record_id,
            "name": "Liquidity Journals",
            "sequence": 10,
            "company_id": None,
            "excluded_journals": [
                _coded(4, "MISC", "Miscellaneous Operations"),
                _coded(9, "BNK1", "Bank"),
            ],
        }
    if capability_id in {"incoterm.list", "incoterm.get"}:
        return {
            "id": record_id,
            "code": "FOB",
            "name": "Free On Board",
            "active": True,
        }
    if capability_id in {
        "partner.bank_account.search",
        "partner.bank_account.get",
    }:
        return {
            "id": record_id,
            "acc_number": "CN621234",
            "account_holder_name": None,
            "account_type": "bank",
            "active": True,
            "sequence": 10,
            "account_holder": {"id": 16, "name": "Fixture Partner"},
            "allow_out_payment": True,
            "bank": {"id": 18, "name": "Fixture Bank", "bic": None},
            "currency": {"id": 6, "code": "CNY"},
            "company_id": 7,
            "linked_journal": _coded(9, "BNK1", "Bank"),
        }
    if capability_id in {"bank.statement.search", "bank.statement.get"}:
        return {
            "id": record_id,
            "name": "BNK1/2026/08",
            "reference": None,
            "date": "2026-08-24",
            "company_id": 7,
            "journal": _coded(9, "BNK1", "Bank"),
            "currency": {"id": 6, "code": "CNY"},
            "balance_start": "100",
            "balance_end": "225.5",
            "balance_end_real": "225.5",
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
            "id": record_id,
            "company_id": 7,
            "max_date": "2026-08-24",
            "amount": "125.5",
            "company_currency": {"id": 6, "code": "CNY"},
            "debit_amount_currency": "125.5",
            "debit_currency": {"id": 6, "code": "CNY"},
            "credit_amount_currency": "-125.5",
            "credit_currency": {"id": 6, "code": "CNY"},
            "debit_journal_item_id": 301,
            "credit_journal_item_id": 302,
            "full_reconcile_id": None,
            "exchange_move_id": None,
            "matching_number": "P",
        }
    if capability_id in {
        "reconciliation.full.list",
        "reconciliation.full.get",
    }:
        return {
            "id": record_id,
            "company_id": 7,
            "matching_number": str(record_id),
            "partial_reconcile_ids": [401],
            "reconciled_journal_item_ids": [301, 302],
        }
    if capability_id in {"analytic.line.search", "analytic.line.get"}:
        return {
            "id": record_id,
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
            "id": record_id,
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
            "id": record_id,
            "plan": {"id": 21, "name": "Projects"},
            "business_domain": "invoice",
            "applicability": "mandatory",
            "company_id": 7,
            "account_prefix": "4",
            "product_category": {"id": 18, "name": "Services"},
        }
    if capability_id in {"budget.search", "budget.get"}:
        return {
            "id": record_id,
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
            "id": record_id,
            "sequence": 10,
            "budget": {"id": 71, "name": "FY2026 Operating Budget"},
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
    raise AssertionError(capability_id)


class FakePort:
    def __init__(
        self,
        items: list[dict] | None = None,
        *,
        company_visible: bool = True,
        module_installed: bool = True,
        access_allowed: bool | None = None,
        cursor_found: bool = True,
        user_id: int = 42,
        page_user_id: int | None = None,
        page_updates: dict | None = None,
    ) -> None:
        self.items = deepcopy(items or [])
        self.company_visible = company_visible
        self.module_installed = module_installed
        self.access_allowed = (
            company_visible and module_installed
            if access_allowed is None
            else access_allowed
        )
        self.cursor_found = cursor_found
        self.user_id = user_id
        self.page_user_id = user_id if page_user_id is None else page_user_id
        self.page_updates = deepcopy(page_updates or {})
        self.calls: list[dict] = []

    def read(self, **kwargs) -> dict:
        self.calls.append(deepcopy(kwargs))
        page = {
            "user_id": self.page_user_id,
            "company_visible": self.company_visible,
            "module_installed": self.module_installed,
            "access_allowed": self.access_allowed,
            "cursor_found": self.cursor_found,
            "items": deepcopy(self.items),
        }
        page.update(deepcopy(self.page_updates))
        return page


def _page_parameters(capability_id: str, *, after_id: int | None, limit: int) -> dict:
    return {**PAGE_DEFAULTS[capability_id], "after_id": after_id, "limit": limit}


def test_public_capability_sets_are_the_fixed_fifty_one_without_reports() -> None:
    assert CORE_OBJECT_GET_CAPABILITY_IDS == frozenset(GET_ID_FIELDS)
    assert CORE_OBJECT_READ_CAPABILITY_IDS == frozenset(
        {*GET_ID_FIELDS, *PAGE_CAPABILITIES}
    )
    assert "report.bank_reconciliation" not in CORE_OBJECT_READ_CAPABILITY_IDS
    assert "report.budget" not in CORE_OBJECT_READ_CAPABILITY_IDS


@pytest.mark.parametrize(("capability_id", "id_field"), GET_ID_FIELDS.items())
def test_each_get_validates_its_exact_id_and_returns_one_item(
    capability_id: str, id_field: str
) -> None:
    item = _item(capability_id)
    request = _request({id_field: item["id"]})

    request_id, context, parameters = validate_core_object_read_request(
        capability_id, request
    )
    port = FakePort([item])
    result = read_core_object(capability_id, port, request)

    assert request_id == REQUEST_ID
    assert context == request["context"]
    assert parameters == {id_field: item["id"]}
    assert result == item
    assert port.calls == [
        {
            "capability_id": capability_id,
            "company_id": 7,
            "parameters": {id_field: item["id"]},
        }
    ]


@pytest.mark.parametrize("capability_id", PAGE_CAPABILITIES)
def test_page_reads_apply_closed_defaults_and_return_the_public_page(
    capability_id: str,
) -> None:
    item = _item(capability_id)
    request = _request({"budget_id": 71} if capability_id == "budget.line.list" else {})

    _, _, parameters = validate_core_object_read_request(capability_id, request)
    port = FakePort([item])
    result = read_core_object(capability_id, port, request)

    expected = {**PAGE_DEFAULTS[capability_id], "limit": 100, "cursor": None}
    assert parameters == expected
    assert result == {"items": [item], "has_more": False, "next_cursor": None}
    assert port.calls == [
        {
            "capability_id": capability_id,
            "company_id": 7,
            "parameters": _page_parameters(capability_id, after_id=None, limit=101),
        }
    ]


def test_journal_item_search_passes_every_normalized_filter() -> None:
    parameters = {
        "date_from": "2026-08-01",
        "date_to": "2026-08-31",
        "move_id": 301,
        "account_id": 121,
        "partner_id": 16,
        "journal_id": 4,
        "posted_only": True,
        "limit": 17,
        "cursor": None,
    }
    port = FakePort([_item("journal_item.search")])

    read_core_object("journal_item.search", port, _request(parameters))

    assert port.calls[0]["parameters"] == {
        **{
            key: value
            for key, value in parameters.items()
            if key not in {"limit", "cursor"}
        },
        "after_id": None,
        "limit": 18,
    }


@pytest.mark.parametrize(
    ("capability_id", "parameters", "expected_filters"),
    [
        (
            "partner.search",
            {
                "query": "Fixture",
                "active": True,
                "company_type": "company",
                "customer": True,
                "supplier": False,
            },
            {
                "query": "Fixture",
                "active": True,
                "company_type": "company",
                "customer": True,
                "supplier": False,
            },
        ),
        (
            "product.search",
            {"query": "CONSULT", "active": False},
            {"query": "CONSULT", "active": False},
        ),
        (
            "analytic.account.search",
            {"query": "ALPHA", "active": True, "plan_id": 31},
            {"query": "ALPHA", "active": True, "plan_id": 31},
        ),
        (
            "fiscal_position.search",
            {"query": "China", "active": True, "auto_apply": False},
            {"query": "China", "active": True, "auto_apply": False},
        ),
        (
            "partner.bank_account.search",
            {"partner_id": 16, "active": False},
            {"partner_id": 16, "active": False},
        ),
        (
            "bank.statement.search",
            {
                "journal_id": 9,
                "date_from": "2026-08-01",
                "date_to": "2026-08-31",
            },
            {
                "journal_id": 9,
                "date_from": "2026-08-01",
                "date_to": "2026-08-31",
            },
        ),
        (
            "analytic.line.search",
            {
                "query": "Project",
                "date_from": "2026-08-01",
                "date_to": "2026-08-31",
                "analytic_account_id": 31,
            },
            {
                "query": "Project",
                "date_from": "2026-08-01",
                "date_to": "2026-08-31",
                "analytic_account_id": 31,
            },
        ),
        (
            "budget.search",
            {
                "query": "FY2026",
                "state": "confirmed",
                "budget_type": "both",
                "date_from": "2026-04-01",
                "date_to": "2026-06-30",
            },
            {
                "query": "FY2026",
                "state": "confirmed",
                "budget_type": "both",
                "date_from": "2026-04-01",
                "date_to": "2026-06-30",
            },
        ),
        (
            "budget.line.list",
            {"budget_id": 71, "plan_id": 21, "analytic_account_id": 31},
            {"budget_id": 71, "plan_id": 21, "analytic_account_id": 31},
        ),
    ],
)
def test_reference_searches_pass_their_closed_normalized_filters(
    capability_id: str,
    parameters: dict,
    expected_filters: dict,
) -> None:
    port = FakePort([_item(capability_id)])

    read_core_object(capability_id, port, _request(parameters))

    assert port.calls[0]["parameters"] == {
        **expected_filters,
        "after_id": None,
        "limit": 101,
    }


def test_product_contract_accepts_odoo_product_without_a_category() -> None:
    item = _item("product.get")
    item["category"] = None

    result = read_core_object(
        "product.get",
        FakePort([item]),
        _request({"product_id": item["id"]}),
    )

    assert result["category"] is None


def test_unknown_capability_is_rejected_before_the_port() -> None:
    with pytest.raises(CoreObjectReadError) as caught:
        validate_core_object_read_request("report.bank_reconciliation", _request())
    assert caught.value.code == "unsupported_capability"
    assert caught.value.exit_code == 4


@pytest.mark.parametrize(("capability_id", "id_field"), GET_ID_FIELDS.items())
@pytest.mark.parametrize("value", [True, 0, -1, "31"])
def test_get_ids_are_positive_non_boolean_integers(
    capability_id: str, id_field: str, value: object
) -> None:
    port = FakePort()
    with pytest.raises(CoreObjectReadError) as caught:
        read_core_object(capability_id, port, _request({id_field: value}))
    assert caught.value.code == "invalid_request"
    assert caught.value.exit_code == 2
    assert port.calls == []


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    [
        ("account.account.get", {"account_id": 31, "unexpected": True}),
        ("payment.method.list", {"unexpected": True}),
        ("reconciliation.model.list", {"limit": True}),
        ("payment.method.list", {"limit": 0}),
        ("payment.method.list", {"limit": 1001}),
        ("payment.method.list", {"cursor": ""}),
        ("journal_item.search", {"date_from": "2026/08/01"}),
        (
            "journal_item.search",
            {"date_from": "2026-09-01", "date_to": "2026-08-31"},
        ),
        ("journal_item.search", {"move_id": True}),
        ("journal_item.search", {"posted_only": 1}),
        ("journal_item.search", {"unexpected": True}),
        ("product.search", {"query": " spaced "}),
        ("partner.search", {"company_type": "organization"}),
        ("partner.search", {"customer": 1}),
        ("product.search", {"active": 1}),
        ("analytic.account.search", {"plan_id": True}),
        ("fiscal_position.search", {"auto_apply": "yes"}),
        ("account.tag.list", {"country_id": 156}),
        ("cash_rounding.list", {"active": True}),
        ("incoterm.list", {"query": "FOB"}),
        ("partner.bank_account.search", {"partner_id": True}),
        ("partner.bank_account.search", {"active": 1}),
        ("bank.statement.search", {"journal_id": True}),
        ("bank.statement.search", {"date_from": "2026/08/01"}),
        (
            "bank.statement.search",
            {"date_from": "2026-09-01", "date_to": "2026-08-31"},
        ),
        ("reconciliation.partial.list", {"active": True}),
        ("reconciliation.full.list", {"company_id": 7}),
        ("analytic.line.search", {"query": " spaced "}),
        ("analytic.line.search", {"analytic_account_id": True}),
        (
            "analytic.line.search",
            {"date_from": "2026-09-01", "date_to": "2026-08-31"},
        ),
        ("analytic.distribution_model.list", {"company_id": 7}),
        ("analytic.applicability.list", {"business_domain": "general"}),
        ("budget.search", {"state": "approved"}),
        ("budget.search", {"budget_type": "capital"}),
        ("budget.search", {"date_from": "2026/01/01"}),
        ("budget.line.list", {}),
        ("budget.line.list", {"budget_id": True}),
        ("budget.line.list", {"budget_id": 71, "plan_id": 21}),
        (
            "budget.line.list",
            {"budget_id": 71, "analytic_account_id": 31},
        ),
    ],
)
def test_invalid_parameters_fail_before_the_port(
    capability_id: str, parameters: dict
) -> None:
    port = FakePort()
    with pytest.raises(CoreObjectReadError) as caught:
        read_core_object(capability_id, port, _request(parameters))
    assert caught.value.code == "invalid_request"
    assert caught.value.exit_code == 2
    assert port.calls == []


def test_request_envelope_and_context_are_closed() -> None:
    request = _request({"journal_id": 31})
    request["context"]["unexpected"] = True
    with pytest.raises(CoreObjectReadError) as caught:
        validate_core_object_read_request("journal.get", request)
    assert caught.value.code == "invalid_request"


@pytest.mark.parametrize(
    ("port", "code", "exit_code"),
    [
        (
            FakePort(company_visible=False, access_allowed=False),
            "company_unavailable",
            3,
        ),
        (FakePort(module_installed=False, access_allowed=False), "uninstalled", 4),
        (FakePort(access_allowed=False), "unauthorized", 3),
    ],
)
def test_runtime_gates_fail_with_specific_errors(
    port: FakePort, code: str, exit_code: int
) -> None:
    with pytest.raises(CoreObjectReadError) as caught:
        read_core_object("account.account.get", port, _request({"account_id": 31}))
    assert caught.value.code == code
    assert caught.value.exit_code == exit_code


@pytest.mark.parametrize(
    "port",
    [
        FakePort(page_user_id=43),
        FakePort(page_updates={"unexpected": True}),
        FakePort(page_updates={"company_visible": 1}),
        FakePort(page_updates={"items": {}}),
    ],
)
def test_bridge_page_shape_and_user_are_verified(port: FakePort) -> None:
    with pytest.raises(CoreObjectReadError) as caught:
        read_core_object("account.account.get", port, _request({"account_id": 31}))
    assert caught.value.code == "failed_validation"
    assert caught.value.exit_code == 8


def test_get_not_found_and_multiple_rows_are_distinct_failures() -> None:
    request = _request({"account_id": 31})
    with pytest.raises(CoreObjectReadError) as missing:
        read_core_object("account.account.get", FakePort(), request)
    assert missing.value.code == "record_not_found"
    assert missing.value.exit_code == 4

    with pytest.raises(CoreObjectReadError) as multiple:
        read_core_object(
            "account.account.get",
            FakePort(
                [_item("account.account.get", 31), _item("account.account.get", 32)]
            ),
            request,
        )
    assert multiple.value.code == "failed_validation"
    assert multiple.value.exit_code == 8


def test_get_rejects_a_well_formed_different_record() -> None:
    with pytest.raises(CoreObjectReadError) as caught:
        read_core_object(
            "account.account.get",
            FakePort([_item("account.account.get", 32)]),
            _request({"account_id": 31}),
        )
    assert caught.value.code == "failed_validation"


def test_budget_line_list_rejects_a_line_from_another_budget() -> None:
    item = _item("budget.line.list")
    item["budget"] = {"id": 72, "name": "Another Budget"}

    with pytest.raises(CoreObjectReadError) as caught:
        read_core_object(
            "budget.line.list",
            FakePort([item]),
            _request({"budget_id": 71}),
        )

    assert caught.value.code == "failed_validation"


@pytest.mark.parametrize("capability_id", tuple(GET_ID_FIELDS) + PAGE_CAPABILITIES)
def test_every_item_contract_is_closed(capability_id: str) -> None:
    item = _item(capability_id)
    item["unexpected"] = True
    parameters = (
        {GET_ID_FIELDS[capability_id]: item["id"]}
        if capability_id in GET_ID_FIELDS
        else {"budget_id": 71}
        if capability_id == "budget.line.list"
        else {}
    )

    with pytest.raises(CoreObjectReadError) as caught:
        read_core_object(capability_id, FakePort([item]), _request(parameters))
    assert caught.value.code == "failed_validation"
    assert caught.value.exit_code == 8


@pytest.mark.parametrize(
    ("capability_id", "mutation"),
    [
        ("journal.get", lambda item: item.update(company_id=8)),
        ("journal_item.search", lambda item: item.update(debit=125.5)),
        ("payment.method.list", lambda item: item.update(payment_type="transfer")),
        ("reconciliation.model.list", lambda item: item.update(active=1)),
        ("product.search", lambda item: item.update(standard_price=100.0)),
        ("analytic.account.search", lambda item: item.update(currency=None)),
        (
            "fiscal_position.search",
            lambda item: item.update(states=list(reversed(item["states"]))),
        ),
        ("account.tag.list", lambda item: item.update(applicability="partners")),
        ("tax.group.list", lambda item: item.update(company_id=8)),
        ("cash_rounding.list", lambda item: item.update(rounding_method="HALF_DOWN")),
        (
            "journal.group.list",
            lambda item: item.update(
                excluded_journals=list(reversed(item["excluded_journals"]))
            ),
        ),
        ("incoterm.list", lambda item: item.update(active=1)),
        ("partner.search", lambda item: item.update(company_id=8)),
        (
            "partner.bank_account.search",
            lambda item: item.update(company_id=8),
        ),
        (
            "bank.statement.search",
            lambda item: item.update(balance_end=225.5),
        ),
        (
            "reconciliation.partial.list",
            lambda item: item.update(matching_number=""),
        ),
        (
            "reconciliation.full.list",
            lambda item: item.update(matching_number="999"),
        ),
        ("analytic.line.search", lambda item: item.update(company_id=8)),
        (
            "analytic.distribution_model.list",
            lambda item: item["allocations"][0].update(percentage=100.0),
        ),
        (
            "analytic.applicability.list",
            lambda item: item.update(business_domain="sale_order"),
        ),
        ("budget.search", lambda item: item.update(state="approved")),
        ("budget.line.list", lambda item: item.update(budget_amount=100000.0)),
    ],
)
def test_invalid_or_out_of_scope_item_fields_fail_closed(
    capability_id: str, mutation
) -> None:
    item = _item(capability_id)
    mutation(item)
    parameters = (
        {"journal_id": item["id"]}
        if capability_id == "journal.get"
        else {"budget_id": 71}
        if capability_id == "budget.line.list"
        else {}
    )

    with pytest.raises(CoreObjectReadError) as caught:
        read_core_object(capability_id, FakePort([item]), _request(parameters))
    assert caught.value.code == "failed_validation"


def test_nullable_new_object_relations_remain_explicitly_closed() -> None:
    cash_rounding = _item("cash_rounding.get")
    cash_rounding.update(profit_account=None, loss_account=None)
    journal_group = _item("journal.group.get")
    journal_group.update(company_id=None, excluded_journals=[])

    cash_result = read_core_object(
        "cash_rounding.get",
        FakePort([cash_rounding]),
        _request({"cash_rounding_id": cash_rounding["id"]}),
    )
    group_result = read_core_object(
        "journal.group.get",
        FakePort([journal_group]),
        _request({"journal_group_id": journal_group["id"]}),
    )

    assert cash_result["profit_account"] is None
    assert cash_result["loss_account"] is None
    assert group_result["company_id"] is None
    assert group_result["excluded_journals"] == []


def test_nullable_bank_relations_remain_explicitly_closed() -> None:
    partner_bank = _item("partner.bank_account.get")
    partner_bank.update(
        account_holder_name=None,
        bank=None,
        currency=None,
        company_id=None,
        linked_journal=None,
    )
    statement = _item("bank.statement.get")
    statement.update(reference=None, date=None, problem_description=None)

    bank_result = read_core_object(
        "partner.bank_account.get",
        FakePort([partner_bank]),
        _request({"partner_bank_id": partner_bank["id"]}),
    )
    statement_result = read_core_object(
        "bank.statement.get",
        FakePort([statement]),
        _request({"bank_statement_id": statement["id"]}),
    )

    assert bank_result["bank"] is None
    assert bank_result["currency"] is None
    assert bank_result["company_id"] is None
    assert bank_result["linked_journal"] is None
    assert statement_result["date"] is None


def test_nullable_analytic_and_budget_relations_remain_closed() -> None:
    line = _item("analytic.line.get")
    line.update(
        reference=None,
        partner=None,
        product=None,
        uom=None,
        general_account=None,
        journal_item_id=None,
    )
    applicability = _item("analytic.applicability.get")
    applicability.update(
        plan=None,
        company_id=None,
        account_prefix=None,
        product_category=None,
    )
    budget = _item("budget.get")
    budget.update(company_id=None, responsible=None, revision_of=None)

    assert (
        read_core_object(
            "analytic.line.get",
            FakePort([line]),
            _request({"analytic_line_id": line["id"]}),
        )
        == line
    )
    assert (
        read_core_object(
            "analytic.applicability.get",
            FakePort([applicability]),
            _request({"applicability_id": applicability["id"]}),
        )
        == applicability
    )
    assert (
        read_core_object(
            "budget.get",
            FakePort([budget]),
            _request({"budget_id": budget["id"]}),
        )
        == budget
    )


def test_empty_distribution_allocations_are_valid() -> None:
    item = _item("analytic.distribution_model.list")
    item["allocations"] = []

    result = read_core_object(
        "analytic.distribution_model.list",
        FakePort([item]),
        _request({}),
    )

    assert result["items"] == [item]


@pytest.mark.parametrize(
    "capability_id",
    [
        "analytic.line.search",
        "analytic.distribution_model.list",
        "budget.line.list",
    ],
)
def test_analytic_account_reference_lists_must_be_sorted_and_unique(
    capability_id: str,
) -> None:
    item = _item(capability_id)
    references = (
        item["allocations"][0]["analytic_accounts"]
        if capability_id == "analytic.distribution_model.list"
        else item["analytic_accounts"]
    )
    references[:] = list(reversed(references)) + references[:1]
    parameters = {"budget_id": 71} if capability_id == "budget.line.list" else {}

    with pytest.raises(CoreObjectReadError) as caught:
        read_core_object(capability_id, FakePort([item]), _request(parameters))

    assert caught.value.code == "failed_validation"


@pytest.mark.parametrize(
    "field", ["partial_reconcile_ids", "reconciled_journal_item_ids"]
)
@pytest.mark.parametrize("value", [[], [401, 401], [402, 401]])
def test_full_reconcile_contract_rejects_invalid_relation_ids(
    field: str, value: list[int]
) -> None:
    item = _item("reconciliation.full.list")
    item[field] = value

    with pytest.raises(CoreObjectReadError) as caught:
        read_core_object("reconciliation.full.list", FakePort([item]), _request())

    assert caught.value.code == "failed_validation"


@pytest.mark.parametrize("capability_id", PAGE_CAPABILITIES)
def test_each_page_capability_paginates_with_an_id_keyset_cursor(
    capability_id: str,
) -> None:
    first_items = [_item(capability_id, 40), _item(capability_id, 41)]
    first_port = FakePort(first_items)
    required = {"budget_id": 71} if capability_id == "budget.line.list" else {}

    first = read_core_object(
        capability_id, first_port, _request({**required, "limit": 1})
    )

    assert first["items"] == first_items[:1]
    assert first["has_more"] is True
    assert isinstance(first["next_cursor"], str)
    assert first_port.calls[0]["parameters"] == _page_parameters(
        capability_id, after_id=None, limit=2
    )

    second_item = _item(capability_id, 41)
    second_port = FakePort([second_item])
    second = read_core_object(
        capability_id,
        second_port,
        _request({**required, "limit": 2, "cursor": first["next_cursor"]}),
    )
    assert second == {
        "items": [second_item],
        "has_more": False,
        "next_cursor": None,
    }
    assert second_port.calls[0]["parameters"] == _page_parameters(
        capability_id, after_id=40, limit=3
    )


def test_cursor_is_bound_to_capability_database_company_and_user() -> None:
    first = read_core_object(
        "payment.method.list",
        FakePort([_item("payment.method.list", 40), _item("payment.method.list", 41)]),
        _request({"limit": 1}),
    )
    cursor = first["next_cursor"]
    assert cursor

    requests = [
        ("reconciliation.model.list", _request({"limit": 1, "cursor": cursor})),
        (
            "payment.method.list",
            _request({"limit": 1, "cursor": cursor}, database="other-db"),
        ),
        (
            "payment.method.list",
            _request({"limit": 1, "cursor": cursor}, company_id=8),
        ),
        (
            "payment.method.list",
            _request({"limit": 1, "cursor": cursor}, user_login="other-user"),
        ),
    ]
    for capability_id, request in requests:
        port = FakePort()
        with pytest.raises(CoreObjectReadError) as caught:
            read_core_object(capability_id, port, request)
        assert caught.value.code == "invalid_cursor"
        assert port.calls == []


def test_journal_item_cursor_is_bound_to_every_normalized_filter() -> None:
    filters = {
        "date_from": "2026-08-01",
        "date_to": "2026-08-31",
        "move_id": 301,
        "account_id": 121,
        "partner_id": 16,
        "journal_id": 4,
        "posted_only": True,
    }
    first = read_core_object(
        "journal_item.search",
        FakePort([_item("journal_item.search", 40), _item("journal_item.search", 41)]),
        _request({**filters, "limit": 1}),
    )
    cursor = first["next_cursor"]
    assert cursor

    changes = {
        "date_from": "2026-08-02",
        "date_to": "2026-09-01",
        "move_id": 302,
        "account_id": 122,
        "partner_id": 17,
        "journal_id": 5,
        "posted_only": False,
    }
    for field, value in changes.items():
        port = FakePort()
        with pytest.raises(CoreObjectReadError) as caught:
            read_core_object(
                "journal_item.search",
                port,
                _request({**filters, field: value, "limit": 1, "cursor": cursor}),
            )
        assert caught.value.code == "invalid_cursor"
        assert port.calls == []


@pytest.mark.parametrize(
    ("capability_id", "filters", "changes"),
    [
        (
            "partner.search",
            {
                "query": "Fixture",
                "active": True,
                "company_type": "company",
                "customer": True,
                "supplier": False,
            },
            {
                "query": "Other",
                "active": False,
                "company_type": "person",
                "customer": False,
                "supplier": True,
            },
        ),
        (
            "partner.bank_account.search",
            {"partner_id": 16, "active": True},
            {"partner_id": 17, "active": False},
        ),
        (
            "bank.statement.search",
            {
                "journal_id": 9,
                "date_from": "2026-08-01",
                "date_to": "2026-08-31",
            },
            {
                "journal_id": 10,
                "date_from": "2026-08-02",
                "date_to": "2026-09-01",
            },
        ),
        (
            "analytic.line.search",
            {
                "query": "Project",
                "date_from": "2026-08-01",
                "date_to": "2026-08-31",
                "analytic_account_id": 31,
            },
            {
                "query": "Other",
                "date_from": "2026-08-02",
                "date_to": "2026-09-01",
                "analytic_account_id": 32,
            },
        ),
        (
            "budget.search",
            {
                "query": "FY2026",
                "state": "confirmed",
                "budget_type": "both",
                "date_from": "2026-01-01",
                "date_to": "2026-12-31",
            },
            {
                "query": "FY2027",
                "state": "revised",
                "budget_type": "expense",
                "date_from": "2026-02-01",
                "date_to": "2026-11-30",
            },
        ),
        (
            "budget.line.list",
            {"budget_id": 71, "plan_id": 21, "analytic_account_id": 31},
            {"budget_id": 72, "plan_id": 22, "analytic_account_id": 32},
        ),
    ],
)
def test_new_search_cursors_are_bound_to_every_filter(
    capability_id: str, filters: dict, changes: dict
) -> None:
    first = read_core_object(
        capability_id,
        FakePort([_item(capability_id, 40), _item(capability_id, 41)]),
        _request({**filters, "limit": 1}),
    )
    cursor = first["next_cursor"]
    assert cursor

    for field, value in changes.items():
        port = FakePort()
        with pytest.raises(CoreObjectReadError) as caught:
            read_core_object(
                capability_id,
                port,
                _request({**filters, field: value, "limit": 1, "cursor": cursor}),
            )
        assert caught.value.code == "invalid_cursor"
        assert port.calls == []


def test_missing_cursor_boundary_is_an_explicit_invalid_cursor() -> None:
    first = read_core_object(
        "reconciliation.model.list",
        FakePort(
            [
                _item("reconciliation.model.list", 40),
                _item("reconciliation.model.list", 41),
            ]
        ),
        _request({"limit": 1}),
    )
    port = FakePort(cursor_found=False)

    with pytest.raises(CoreObjectReadError) as caught:
        read_core_object(
            "reconciliation.model.list",
            port,
            _request({"limit": 1, "cursor": first["next_cursor"]}),
        )
    assert caught.value.code == "invalid_cursor"
    assert caught.value.exit_code == 2
    assert port.calls[0]["parameters"] == {"after_id": 40, "limit": 2}
