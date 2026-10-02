from __future__ import annotations

import sys
from copy import deepcopy
from types import ModuleType, SimpleNamespace

import pytest
import test_document_search_batch_runtime as previous

from odoo_accounting_cli_v4.bridge import core_object_reads_runtime as objects
from odoo_accounting_cli_v4.bridge import invoice_analysis_runtime as analysis
from odoo_accounting_cli_v4.bridge import runtime

INVOICE = {"date_from": None, "date_to": None, "document_types": [], "states": [], "payment_states": [],
           "journal_id": None, "partner_id": None, "query": None}
ENTRY = {"date_from": None, "date_to": None, "states": [], "journal_id": None, "partner_id": None, "query": None}
OPEN = {"date_from": None, "date_to": None, "due_date_from": None, "due_date_to": None,
        "partner_id": None, "account_id": None, "journal_id": None, "currency_id": None, "query": None}


@pytest.fixture(autouse=True)
def expression(monkeypatch):
    odoo, osv, fields = ModuleType("odoo"), ModuleType("odoo.osv"), ModuleType("odoo.fields")
    def flatten(domains):
        return [term for domain in domains for term in domain]
    osv.expression = SimpleNamespace(AND=flatten)
    fields.Domain = SimpleNamespace(AND=flatten)
    monkeypatch.setitem(sys.modules, "odoo", odoo)
    monkeypatch.setitem(sys.modules, "odoo.osv", osv)
    monkeypatch.setitem(sys.modules, "odoo.fields", fields)


def payload(filters):
    return {"company_id": 7, "after": None, "limit": 3, "filters": filters}


def matches(record, domain):
    for field, operator, value in domain:
        actual = record[field]
        if operator == "any":
            if not any(matches(line, value) for line in actual):
                return False
        elif operator == "in":
            if not (set(actual) & set(value) if isinstance(actual, list) else actual in value):
                return False
        elif operator == "ilike":
            if value.lower() not in actual.lower():
                return False
        else:
            assert operator == "="
            if actual != value:
                return False
    return True


def test_invoice_business_criteria_are_one_acl_respecting_any_on_the_same_product_line():
    filters = {**INVOICE, "product_id": 21, "account_id": 31, "tax_id": 91}
    assert runtime._invoice_search_payload_is_valid(payload(filters))
    domain = runtime._invoice_domain(7, None, filters)
    assert domain[-1] == ("invoice_line_ids", "any", [
        ("display_type", "=", "product"), ("product_id", "=", 21),
        ("account_id", "=", 31), ("tax_ids", "in", [91]),
    ])
    split = {"company_id": 7, "move_type": "out_invoice", "invoice_line_ids": [
        {"display_type": "product", "product_id": 21, "account_id": 31, "tax_ids": []},
        {"display_type": "product", "product_id": 22, "account_id": 32, "tax_ids": [91]},
        {"display_type": "tax", "product_id": 21, "account_id": 31, "tax_ids": [91]},
    ]}
    assert not matches(split, domain)
    split["invoice_line_ids"][0]["tax_ids"] = [91]
    assert matches(split, domain)


@pytest.mark.parametrize("key,condition", [
    ("product_id", ("product_id", "=", 21)), ("account_id", ("account_id", "=", 21)),
    ("tax_id", ("tax_ids", "in", [21])),
])
def test_each_invoice_business_filter_independently_uses_product_line_membership(key, condition):
    domain = runtime._invoice_domain(7, None, {**INVOICE, key: 21})
    assert domain[-1] == ("invoice_line_ids", "any", [("display_type", "=", "product"), condition])


def test_invoice_new_filters_omitted_do_not_change_the_old_domain_or_parameters():
    filters = deepcopy(INVOICE)
    assert runtime._invoice_search_payload_is_valid(payload(filters))
    assert runtime._invoice_domain(7, None, filters) == [
        ("company_id", "=", 7), ("move_type", "in", list(runtime._INVOICE_DOCUMENT_TYPES)),
    ]
    assert filters == INVOICE


@pytest.mark.parametrize("key", ["product_id", "account_id", "tax_id"])
@pytest.mark.parametrize("value", [None, True, 0, -1, "21"])
def test_invoice_business_filter_ids_are_strict_nonnull_positive(key, value):
    assert not runtime._invoice_search_payload_is_valid(payload({**INVOICE, key: value}))


def test_entry_tax_text_and_explicit_account_are_bound_to_one_native_line():
    filters = {**ENTRY, "account_id": 31, "tax_id": 91, "line_query": "October"}
    assert runtime._journal_entry_filters_are_valid(filters)
    domain = runtime._journal_entry_domain(7, None, filters)
    assert domain[-1] == ("line_ids", "any", [
        ("account_id", "=", 31), ("tax_ids", "in", [91]), ("name", "ilike", "October"),
    ])
    split = {"company_id": 7, "move_type": "entry", "line_ids": [
        {"account_id": 31, "tax_ids": [], "name": "October"},
        {"account_id": 32, "tax_ids": [91], "name": "October"},
    ]}
    assert not matches(split, domain)
    split["line_ids"][0]["tax_ids"] = [91]
    assert matches(split, domain)


@pytest.mark.parametrize("extras", [{}, {"line_query": None}])
def test_entry_account_only_and_explicit_null_line_query_keep_legacy_domain(extras):
    filters = {**ENTRY, "account_id": 31, **extras}
    assert runtime._journal_entry_filters_are_valid(filters)
    assert runtime._journal_entry_domain(7, None, filters)[-1] == ("line_ids.account_id", "=", 31)


@pytest.mark.parametrize("extras", [{"line_query": "October"}, {"tax_id": 91}, {"tax_id": 91, "line_query": None}])
def test_entry_effective_new_line_criterion_alone_uses_any_without_changing_header_query(extras):
    domain = runtime._journal_entry_domain(7, None, {**ENTRY, **extras})
    assert domain[-1][0:2] == ("line_ids", "any")
    assert all(term[0] not in {"name", "ref"} for term in domain[:-1])


@pytest.mark.parametrize("extras", [
    {"tax_id": None}, {"tax_id": True}, {"tax_id": 0}, {"tax_id": "91"},
    {"line_query": ""}, {"line_query": " October"}, {"line_query": "x" * 201},
    {"line_query": False}, {"business_only": True},
])
def test_entry_new_filters_have_a_closed_protocol(extras):
    assert not runtime._journal_entry_filters_are_valid({**ENTRY, **extras})


@pytest.mark.parametrize("capability,filters", [("invoice.search", INVOICE), ("journal_entry.search", ENTRY)])
def test_header_business_domain_is_applied_before_native_pagination(monkeypatch, capability, filters):
    model = previous.Model()
    env = type("Env", (dict,), {"uid": 5})({"account.move": model})
    monkeypatch.setattr(runtime, "_invoice_gate", lambda *_args: (True, True, True))
    monkeypatch.setattr(runtime, "_journal_entry_gate", lambda *_args, **_kwargs: (True, True, True))
    monkeypatch.setattr(runtime, "_invoice_header_related", lambda *_args: {})
    monkeypatch.setattr(runtime, "_journal_entry_related", lambda *_args: {})
    request = {**payload({**filters, "tax_id": 91}), "after": ["2026-10-02", 20]}
    method = runtime._dispatch_invoice_search if capability == "invoice.search" else runtime._dispatch_journal_entry_search
    result = method(env, request, 7)
    assert result["rows"] == [] and result["user_id"] == 5
    assert model.calls[0][1][2][1] == "any"
    assert model.calls[0][2]["limit"] == 3 and model.calls[0][2]["order"] == "date desc,id desc"
    assert model.contexts == [{"active_test": False, "allowed_company_ids": [7]}]


def test_journal_product_and_applied_tax_filters_are_used_in_cursor_membership_and_page():
    model = previous.Model()
    parameters = {**previous.JOURNAL, "product_id": 21, "tax_id": 91, "after_id": 20}
    assert objects._valid_parameters("journal_item.search", parameters)
    assert objects._journal_item_rows({"account.move.line": model}, parameters, 7) == ([], True)
    assert model.calls[0][1] == [("company_id", "=", 7), ("product_id", "=", 21), ("tax_ids", "in", [91]), ("id", "=", 20)]
    assert model.calls[1][1] == [("company_id", "=", 7), ("product_id", "=", 21), ("tax_ids", "in", [91]), ("id", ">", 20)]
    assert model.contexts == [{"active_test": False, "allowed_company_ids": [7]}]


@pytest.mark.parametrize("key", ["product_id", "tax_id"])
@pytest.mark.parametrize("value", [None, True, 0, "21"])
def test_journal_product_and_tax_filter_ids_are_strict(key, value):
    assert not objects._valid_parameters("journal_item.search", {**previous.JOURNAL, key: value})


@pytest.mark.parametrize("capability", ["invoice.analysis.search", "invoice.analysis.summary"])
@pytest.mark.parametrize("owner,fiscal", [(5, 61), (None, None)])
def test_analysis_filters_native_owner_fiscal_and_business_account_without_new_global_gates(capability, owner, fiscal):
    parameters = deepcopy(previous.ANALYSIS)
    if capability.endswith("summary"):
        parameters.pop("after")
        parameters.pop("limit")
        parameters.update(date_from="2026-10-01", date_to="2026-10-31", group_by="move_type")
    old_domain = analysis._base_domain(7, parameters)
    parameters.update(invoice_user_id=owner, fiscal_position_id=fiscal, account_id=31)
    assert analysis._valid_parameters(capability, parameters)
    assert analysis._base_domain(7, parameters) == [*old_domain, ("account_id", "=", 31),
        ("invoice_user_id", "=", owner if owner is not None else False),
        ("fiscal_position_id", "=", fiscal if fiscal is not None else False)]
    assert not {"invoice_user_id", "fiscal_position_id", "account_id"} & analysis._REQUIRED_FIELDS["account.invoice.report"]


def test_analysis_new_filters_precede_cursor_and_grouping_and_keep_company_amounts(monkeypatch):
    model = previous.Model()
    company = SimpleNamespace(id=7, currency_id=SimpleNamespace(id=61, display_name="CNY"))
    company_model = SimpleNamespace(search=lambda *_args, **_kwargs: [company])
    monkeypatch.setattr(analysis, "_model", lambda _env, name, _company: company_model if name == "res.company" else model)
    parameters = {**previous.ANALYSIS, "invoice_user_id": None, "fiscal_position_id": 62, "account_id": 31, "after": 20}
    assert analysis._search_items(object(), 7, parameters) == (True, [])
    assert model.calls[0][1] == [*analysis._base_domain(7, parameters), ("id", "=", 20)]
    parameters.pop("after")
    parameters.pop("limit")
    parameters.update(date_from="2026-10-01", date_to="2026-10-31", group_by="move_type")
    result = analysis._summary_item(object(), 7, parameters)
    assert model.calls[-1][1] == analysis._base_domain(7, parameters)
    assert model.calls[-1][2]["aggregates"] == list(analysis._AGGREGATES)
    assert result["company_currency"] == {"id": 61, "code": "CNY"} and result["totals"]["total_amount"] == "100"


@pytest.mark.parametrize("extras", [
    {"account_id": None}, {"account_id": True}, {"account_id": 0},
    {"invoice_user_id": False}, {"invoice_user_id": "5"}, {"invoice_user_id": 0},
    {"fiscal_position_id": True}, {"fiscal_position_id": -1}, {"tax_id": 91},
])
def test_analysis_new_ids_are_closed_and_strict(extras):
    assert not analysis._valid_parameters("invoice.analysis.search", {**previous.ANALYSIS, **extras})


@pytest.mark.parametrize("account_type", ["asset_receivable", "liability_payable"])
@pytest.mark.parametrize("owner,term,fiscal", [(5, 51, 61), (None, None, None)])
def test_open_item_header_filters_are_native_move_fields_and_null_means_unset(account_type, owner, term, fiscal):
    filters = {**OPEN, "invoice_user_id": owner, "payment_term_id": term, "fiscal_position_id": fiscal}
    assert runtime._open_item_payload_is_valid(payload(filters))
    domain = runtime._open_item_domain(7, account_type, None, filters)
    assert domain[-3:] == [("move_id.invoice_user_id", "=", owner if owner is not None else False),
        ("move_id.invoice_payment_term_id", "=", term if term is not None else False),
        ("move_id.fiscal_position_id", "=", fiscal if fiscal is not None else False)]
    assert ("parent_state", "=", "posted") in domain and ("reconciled", "=", False) in domain
    assert ("account_type", "=", account_type) in domain
    assert runtime._open_item_domain(7, account_type, None, OPEN) == domain[:-3]


@pytest.mark.parametrize("key", ["invoice_user_id", "payment_term_id", "fiscal_position_id"])
@pytest.mark.parametrize("value", [True, False, 0, -1, "21"])
def test_open_item_header_ids_are_nullable_but_not_bool_or_text(key, value):
    assert not runtime._open_item_payload_is_valid(payload({**OPEN, key: value}))
