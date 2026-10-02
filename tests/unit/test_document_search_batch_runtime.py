from __future__ import annotations

import sys
from copy import deepcopy
from types import ModuleType, SimpleNamespace

import pytest

from odoo_accounting_cli_v4.bridge import core_object_reads_runtime as objects
from odoo_accounting_cli_v4.bridge import invoice_analysis_runtime as analysis

JOURNAL = {"date_from": None, "date_to": None, "move_id": None, "account_id": None, "partner_id": None,
           "journal_id": None, "posted_only": False, "after_id": None, "limit": 3}
ANALYSIS = {"date_from": None, "date_to": None, "move_types": None, "states": None, "payment_states": None,
            "partner_id": None, "product_id": None, "after": None, "limit": 3}


@pytest.fixture(autouse=True)
def expression(monkeypatch):
    odoo = ModuleType("odoo")
    osv = ModuleType("odoo.osv")
    osv.expression = SimpleNamespace(AND=lambda domains: [value for domain in domains for value in domain])
    monkeypatch.setitem(sys.modules, "odoo", odoo)
    monkeypatch.setitem(sys.modules, "odoo.osv", osv)


class Model:
    def __init__(self):
        self.calls = []
        self.contexts = []
        self.cursor_exists = True

    def with_context(self, **context):
        self.contexts.append(context)
        return self

    def search_count(self, domain, **kwargs):
        self.calls.append(("count", deepcopy(domain), kwargs))
        return int(self.cursor_exists)

    def search_read(self, domain, fields, **kwargs):
        self.calls.append(("read", deepcopy(domain), {"fields": fields, **kwargs}))
        return []

    def _read_group(self, domain, **kwargs):
        self.calls.append(("group", deepcopy(domain), kwargs))
        return [("out_invoice", 2, 3, 80, 100, 20, -10)]


def test_journal_item_legacy_omission_shape_and_domain_are_unchanged():
    original = deepcopy(JOURNAL)
    assert objects._valid_parameters("journal_item.search", JOURNAL)
    assert objects._journal_item_domain(7, JOURNAL, include_after=True) == [("company_id", "=", 7)]
    assert JOURNAL == original


def test_journal_item_explicit_false_and_native_filters_are_applied_before_cursor_and_paging():
    model = Model()
    parameters = {**JOURNAL, "after_id": 20, "currency_id": 6, "due_date_from": "2026-10-01", "due_date_to": "2026-10-31",
                  "reconciled": False, "move_types": ["entry", "out_invoice", "in_receipt"], "query": "October"}
    assert objects._valid_parameters("journal_item.search", parameters)
    rows, found = objects._journal_item_rows({"account.move.line": model}, parameters, 7)
    assert rows == [] and found
    expected = [("company_id", "=", 7), ("currency_id", "=", 6), ("date_maturity", ">=", "2026-10-01"),
                ("date_maturity", "<=", "2026-10-31"), ("reconciled", "=", False),
                ("move_type", "in", ["entry", "out_invoice", "in_receipt"]), "|", "|",
                ("name", "ilike", "October"), ("move_id.name", "ilike", "October"), ("move_id.ref", "ilike", "October")]
    assert model.calls[0] == ("count", [*expected, ("id", "=", 20)], {"limit": 1})
    assert model.calls[1][1] == [*expected, ("id", ">", 20)]
    assert model.calls[1][2]["limit"] == 3 and model.calls[1][2]["order"] == "id"
    assert model.contexts == [{"active_test": False, "allowed_company_ids": [7]}]


def test_journal_item_cursor_missing_from_new_filter_domain_returns_no_page():
    model = Model()
    model.cursor_exists = False
    rows, found = objects._journal_item_rows({"account.move.line": model}, {**JOURNAL, "after_id": 20, "reconciled": True}, 7)
    assert rows == [] and not found and len(model.calls) == 1
    assert ("reconciled", "=", True) in model.calls[0][1]


def test_journal_item_explicit_null_dates_do_not_add_native_filters():
    parameters = {**JOURNAL, "due_date_from": None, "due_date_to": None, "query": None}
    assert objects._valid_parameters("journal_item.search", parameters)
    assert objects._journal_item_domain(7, parameters, include_after=False) == [("company_id", "=", 7)]


@pytest.mark.parametrize("values", [
    {"currency_id": None}, {"currency_id": True}, {"currency_id": 0},
    {"due_date_from": "2026-10-32"}, {"due_date_from": 20261001},
    {"due_date_from": "2026-10-31", "due_date_to": "2026-10-01"},
    {"reconciled": None}, {"reconciled": 0}, {"reconciled": "false"},
    {"move_types": None}, {"move_types": []}, {"move_types": ["out_invoice", "entry"]},
    {"move_types": ["entry", "entry"]}, {"move_types": [True]}, {"move_types": ["unknown"]},
    {"query": ""}, {"query": " x"}, {"query": "x" * 201}, {"query": True},
])
def test_journal_item_new_filter_protocol_is_closed_and_strict(values):
    assert not objects._valid_parameters("journal_item.search", {**JOURNAL, **values})


@pytest.mark.parametrize("capability", ["invoice.analysis.search", "invoice.analysis.summary"])
def test_analysis_new_native_filters_are_optional_and_preserve_legacy_parameters(capability):
    parameters = deepcopy(ANALYSIS)
    if capability.endswith("summary"):
        parameters.pop("after")
        parameters.pop("limit")
        parameters.update(date_from="2026-10-01", date_to="2026-10-31", group_by="move_type")
    original = deepcopy(parameters)
    assert analysis._valid_parameters(capability, parameters)
    legacy = analysis._base_domain(7, parameters)
    assert parameters == original
    parameters.update(journal_id=51, currency_id=6, due_date_from="2026-11-01", due_date_to="2026-11-30")
    assert analysis._valid_parameters(capability, parameters)
    assert analysis._base_domain(7, parameters) == [*legacy, ("journal_id", "=", 51), ("currency_id", "=", 6),
                                                  ("invoice_date_due", ">=", "2026-11-01"), ("invoice_date_due", "<=", "2026-11-30")]


def test_analysis_search_new_filters_are_used_for_cursor_membership_and_native_page(monkeypatch):
    model = Model()
    monkeypatch.setattr(analysis, "_model", lambda *_args: model)
    parameters = {**ANALYSIS, "after": 20, "currency_id": 6, "due_date_to": "2026-10-31"}
    found, rows = analysis._search_items(object(), 7, parameters)
    assert found and rows == []
    base = analysis._base_domain(7, parameters)
    assert model.calls[0] == ("count", [*base, ("id", "=", 20)], {"limit": 1})
    assert model.calls[1][1] == [*base, ("id", "<", 20)]


def test_analysis_summary_filters_document_currency_but_keeps_native_company_amounts(monkeypatch):
    model = Model()
    company = SimpleNamespace(id=7, currency_id=SimpleNamespace(id=61, display_name="CNY"))
    company_model = SimpleNamespace(search=lambda *_args, **_kwargs: [company])
    monkeypatch.setattr(analysis, "_model", lambda _env, name, _company: company_model if name == "res.company" else model)
    parameters = {"date_from": "2026-10-01", "date_to": "2026-10-31", "move_types": None, "states": None,
                  "payment_states": None, "partner_id": None, "product_id": None, "group_by": "move_type",
                  "journal_id": 51, "currency_id": 6, "due_date_from": "2026-11-01"}
    result = analysis._summary_item(object(), 7, parameters)
    assert model.calls[0][1] == analysis._base_domain(7, parameters)
    assert model.calls[0][2]["aggregates"] == list(analysis._AGGREGATES)
    assert result["company_currency"] == {"id": 61, "code": "CNY"}
    assert result["totals"]["untaxed_amount"] == "80" and result["totals"]["total_amount"] == "100"


@pytest.mark.parametrize("values", [
    {"journal_id": None}, {"journal_id": True}, {"journal_id": 0},
    {"currency_id": None}, {"currency_id": False}, {"currency_id": "6"},
    {"due_date_from": "2026-10-32"}, {"due_date_to": True},
    {"due_date_from": "2026-11-30", "due_date_to": "2026-11-01"}, {"unknown": 1},
])
def test_analysis_new_filters_are_strict_and_reject_reversed_due_ranges(values):
    assert not analysis._valid_parameters("invoice.analysis.search", {**ANALYSIS, **values})


def test_analysis_explicit_null_due_bound_is_no_native_filter_and_no_extra_field_gate():
    parameters = {**ANALYSIS, "due_date_from": None, "due_date_to": None}
    assert analysis._valid_parameters("invoice.analysis.search", parameters)
    assert analysis._base_domain(7, parameters) == analysis._base_domain(7, ANALYSIS)
    assert {"journal_id", "currency_id", "invoice_date_due"} <= analysis._REQUIRED_FIELDS["account.invoice.report"]
