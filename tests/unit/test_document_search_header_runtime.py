"""Optional search domains stay native and retain omitted legacy bindings."""
import sys
from copy import deepcopy
from types import ModuleType, SimpleNamespace

import pytest

from odoo_accounting_cli_v4.bridge import runtime


@pytest.fixture(autouse=True)
def native_domain_stubs(monkeypatch):
    odoo, osv, fields = ModuleType("odoo"), ModuleType("odoo.osv"), ModuleType("odoo.fields")
    odoo.__path__ = []
    and_domains = lambda domains: [item for domain in domains for item in domain]
    osv.expression = SimpleNamespace(AND=and_domains)
    fields.Domain = SimpleNamespace(AND=and_domains, OR=and_domains)
    for name, module in (("odoo", odoo), ("odoo.osv", osv), ("odoo.fields", fields)):
        monkeypatch.setitem(sys.modules, name, module)


def invoice_payload(**extras):
    return {"company_id": 7, "after": None, "limit": 11, "filters": {
        "date_from": None, "date_to": None, "document_types": [], "states": [],
        "payment_states": [], "journal_id": None, "partner_id": None, "query": None, **extras}}


def entry_filters(**extras):
    return {"date_from": None, "date_to": None, "states": [], "journal_id": None,
            "partner_id": None, "query": None, **extras}


def open_payload(**extras):
    return {"company_id": 7, "after": None, "limit": 11, "filters": {
        "date_from": None, "date_to": None, "due_date_from": None, "due_date_to": None,
        "partner_id": None, "account_id": None, "journal_id": None, "currency_id": None,
        "query": None, **extras}}


def test_optional_header_domains_and_null_relation_filters():
    payload = invoice_payload(invoice_date_from="2026-01-01", invoice_date_to="2026-12-31",
                              due_date_from="2026-02-01", due_date_to="2026-11-30",
                              currency_id=6, invoice_user_id=None, payment_term_id=23, fiscal_position_id=None)
    before = deepcopy(payload)
    assert runtime._invoice_search_payload_is_valid(payload)
    domain = runtime._invoice_domain(7, ["2026-05-01", 99], payload["filters"])
    for item in (("company_id", "=", 7), ("invoice_date", ">=", "2026-01-01"),
                 ("invoice_date", "<=", "2026-12-31"), ("invoice_date_due", ">=", "2026-02-01"),
                 ("invoice_date_due", "<=", "2026-11-30"), ("currency_id", "=", 6),
                 ("invoice_user_id", "=", False), ("invoice_payment_term_id", "=", 23),
                 ("fiscal_position_id", "=", False), ("id", "<", 99)):
        assert item in domain
    assert payload == before
    legacy = invoice_payload()
    assert runtime._invoice_search_payload_is_valid(legacy)
    legacy_domain = runtime._invoice_domain(7, None, legacy["filters"])
    assert not any(item[0] in {"invoice_date", "invoice_date_due", "invoice_user_id", "currency_id"}
                   for item in legacy_domain if isinstance(item, tuple))


@pytest.mark.parametrize("extra", [
    {"currency_id": None}, {"currency_id": True}, {"invoice_user_id": 0},
    {"payment_term_id": False}, {"fiscal_position_id": "1"},
    {"invoice_date_from": "2026-02-30"}, {"due_date_to": "2026-1-1"},
    {"due_date_from": "2026-12-31", "due_date_to": "2026-01-01"},
    {"invoice_date_from": "2026-12-31", "invoice_date_to": "2026-01-01"},
    {"product_id": 1},
])
def test_invalid_invoice_extension_filters(extra):
    assert not runtime._invoice_search_payload_is_valid(invoice_payload(**extra))


def test_entry_currency_is_header_currency_and_account_is_line_membership():
    filters = entry_filters(currency_id=6, account_id=33)
    assert runtime._journal_entry_filters_are_valid(filters)
    domain = runtime._journal_entry_domain(7, None, filters)
    assert ("currency_id", "=", 6) in domain
    assert ("line_ids.account_id", "=", 33) in domain
    assert ("move_type", "=", "entry") in domain
    for key in ("currency_id", "account_id"):
        for value in (None, True, 0, -1, "33"):
            assert not runtime._journal_entry_filters_are_valid(entry_filters(**{key: value}))
    assert runtime._journal_entry_filters_are_valid(entry_filters())


def test_open_items_precise_parent_filters_preserve_posted_side_and_open_scope():
    payload = open_payload(move_id=31, move_types=["out_invoice", "out_refund"])
    assert runtime._open_item_payload_is_valid(payload)
    for side in ("asset_receivable", "liability_payable"):
        domain = runtime._open_item_domain(7, side, None, payload["filters"])
        for item in (("company_id", "=", 7), ("parent_state", "=", "posted"),
                     ("account_type", "=", side), ("reconciled", "=", False),
                     ("move_id", "=", 31), ("move_id.move_type", "in", ["out_invoice", "out_refund"])):
            assert item in domain
    assert runtime._open_item_payload_is_valid(open_payload())


@pytest.mark.parametrize("extra", [
    {"move_id": None}, {"move_id": True}, {"move_id": 0}, {"move_types": []},
    {"move_types": ["out_invoice", "out_invoice"]}, {"move_types": ["out_refund", "out_invoice"]},
    {"move_types": ["invalid"]}, {"move_types": [True]}, {"invoice_user_id": 5},
])
def test_invalid_open_item_extension_filters(extra):
    assert not runtime._open_item_payload_is_valid(open_payload(**extra))
