from __future__ import annotations

from copy import deepcopy

import pytest
import test_core_object_reads as objects_fixture
import test_invoice_analysis as analysis_fixture
import test_invoices as invoices_fixture
import test_journal_entries as entries_fixture
import test_open_items as open_fixture

from odoo_accounting_cli_v4.capabilities import (
    core_object_reads as objects,
)
from odoo_accounting_cli_v4.capabilities import (
    invoice_analysis as analysis,
)
from odoo_accounting_cli_v4.capabilities import (
    invoices,
    open_items,
)
from odoo_accounting_cli_v4.capabilities import (
    journal_entries as entries,
)
from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry

MOVE_TYPES = ["entry", "out_invoice", "out_refund", "in_invoice", "in_refund", "out_receipt", "in_receipt"]
FIELDS = {
    "invoice.search": {"invoice_date_from": "date", "invoice_date_to": "date", "due_date_from": "date", "due_date_to": "date", "currency_id": "id", "invoice_user_id": "nullable_id", "payment_term_id": "nullable_id", "fiscal_position_id": "nullable_id"},
    "journal_entry.search": {"currency_id": "id", "account_id": "id"},
    "journal_item.search": {"currency_id": "id", "due_date_from": "date", "due_date_to": "date", "reconciled": "bool", "move_types": "types", "query": "query"},
    "receivable.open_items.list": {"move_id": "id", "move_types": "types"},
    "payable.open_items.list": {"move_id": "id", "move_types": "types"},
    "invoice.analysis.search": {"journal_id": "id", "currency_id": "id", "due_date_from": "date", "due_date_to": "date"},
    "invoice.analysis.summary": {"journal_id": "id", "currency_id": "id", "due_date_from": "date", "due_date_to": "date"},
}
ERRORS = (invoices.InvoiceError, entries.JournalEntryError, objects.CoreObjectReadError, open_items.OpenItemsError, analysis.InvoiceAnalysisError)
VALID = {"date": [None, "2026-10-02"], "id": [3], "nullable_id": [None, 3], "bool": [False, True], "types": [list(reversed(MOVE_TYPES))], "query": [None, "INV_001%"]}
INVALID = {
    "date": [True, 3, [], {}, "2026-02-30", "20261002", "2026-10-02\n"],
    "id": [None, True, False, 0, -1, "3", 1.5, [], {}],
    "nullable_id": [True, False, 0, -1, "3", 1.5, [], {}],
    "bool": [None, 0, 1, "false", [], {}],
    "types": [None, [], "entry", ["entry", "entry"], ["unknown"], [True], [{}], [[]]],
    "query": [True, 3, [], {}, "", " INV", "INV ", "INV\n", "x" * 201],
}
CASES = [(capability, key, kind) for capability, fields in FIELDS.items() for key, kind in fields.items()]


@pytest.fixture(scope="module")
def registry():
    return load_registry()


def request(capability, parameters=None):
    base = {"date_from": "2026-01-01", "date_to": "2026-12-31", "group_by": "partner"} if capability.endswith("summary") else {}
    return invoices_fixture._request({**base, **(parameters or {})})


def normalize(capability, value):
    if capability == "invoice.search":
        return invoices.validate_invoice_search_request(value)[2]
    if capability == "journal_entry.search":
        return entries.validate_journal_entry_search_request(value)[2]
    if capability == "journal_item.search":
        return objects.validate_core_object_read_request(capability, value)[2]
    if capability.endswith("open_items.list"):
        validator = open_items.validate_receivable_open_items_list_request if capability.startswith("receivable") else open_items.validate_payable_open_items_list_request
        return validator(value)[2]
    return analysis.validate_invoice_analysis_request(capability, value)[2]


@pytest.mark.parametrize("capability,key,kind,value", [(cap, key, kind, value) for cap, key, kind in CASES for value in VALID[kind]])
def test_explicit_filters_are_validated_and_only_add_the_requested_key(capability, key, kind, value, registry):
    current = request(capability, {key: value})
    original = deepcopy(current)
    normalized = normalize(capability, current)
    expected = MOVE_TYPES if kind == "types" else value
    assert normalized == {**normalize(capability, request(capability)), key: expected}
    assert current == original
    registry.validate_instance(f"schemas/v1/{capability}.request.schema.json", current)


@pytest.mark.parametrize("capability,key,value", [(cap, key, value) for cap, key, kind in CASES for value in INVALID[kind]])
def test_new_filter_invalid_types_and_values_fail_cleanly(capability, key, value, registry):
    current = request(capability, {key: value})
    with pytest.raises(ERRORS) as caught:
        normalize(capability, current)
    assert caught.value.code == "invalid_request" and caught.value.exit_code == 2
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(f"schemas/v1/{capability}.request.schema.json", current)


@pytest.mark.parametrize("capability", FIELDS)
def test_unknown_keys_are_closed_in_sdk_and_schema(capability, registry):
    current = request(capability, {"arbitrary_domain": []})
    with pytest.raises(ERRORS):
        normalize(capability, current)
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(f"schemas/v1/{capability}.request.schema.json", current)


@pytest.mark.parametrize("capability,key", [(cap, key) for cap, key, kind in CASES if kind in {"id", "nullable_id"}])
def test_integral_float_is_not_an_sdk_identifier(capability, key):
    with pytest.raises(ERRORS):
        normalize(capability, request(capability, {key: 3.0}))


@pytest.mark.parametrize("capability,prefix", [(cap, prefix) for cap, fields in FIELDS.items() for prefix in ("due_date", "invoice_date") if f"{prefix}_from" in fields])
def test_date_bounds_are_independent_nullable_and_range_checked(capability, prefix):
    start, end = f"{prefix}_from", f"{prefix}_to"
    with pytest.raises(ERRORS):
        normalize(capability, request(capability, {start: "2026-10-03", end: "2026-10-02"}))
    for values in ({start: "2026-10-03"}, {end: "2026-10-02"}, {start: None, end: "2026-10-02"}):
        normalized = normalize(capability, request(capability, values))
        assert all(normalized[key] == value for key, value in values.items())


@pytest.mark.parametrize("capability", FIELDS)
def test_omission_retains_the_exact_old_normalized_shape(capability):
    result = normalize(capability, request(capability))
    assert not set(result) & FIELDS[capability].keys()
    if capability == "invoice.search":
        expected = {"date_from": None, "date_to": None, "document_types": [], "states": [], "payment_states": [], "journal_id": None, "partner_id": None, "query": None}
    elif capability == "journal_entry.search":
        expected = {"date_from": None, "date_to": None, "states": [], "journal_id": None, "partner_id": None, "query": None}
    elif capability == "journal_item.search":
        expected = {"date_from": None, "date_to": None, "move_id": None, "account_id": None, "partner_id": None, "journal_id": None, "posted_only": False, "limit": 100, "cursor": None}
    elif capability.endswith("open_items.list"):
        expected = dict.fromkeys(("date_from", "date_to", "due_date_from", "due_date_to", "partner_id", "account_id", "journal_id", "currency_id", "query"))
    else:
        expected = dict.fromkeys(("date_from", "date_to", "move_types", "states", "payment_states", "partner_id", "product_id"))
        expected.update(request(capability)["parameters"] if capability.endswith("summary") else {"limit": 100, "cursor": None})
    assert result == expected


@pytest.mark.parametrize("capability", FIELDS)
def test_all_extensions_reach_the_existing_fixed_port_without_response_additions(capability):
    values = {key: VALID[kind][0] for key, kind in FIELDS[capability].items()}
    current = request(capability, values)
    normalized = normalize(capability, current)
    if capability == "invoice.search":
        port = invoices_fixture.FakePort()
        result = invoices.search_invoices(port, current)
        sent = port.search_calls[0]["filters"]
    elif capability == "journal_entry.search":
        port = entries_fixture.FakePort()
        result = entries.search_journal_entries(port, current)
        sent = port.search_calls[0]["filters"]
    elif capability.endswith("open_items.list"):
        port = open_fixture.FakePort()
        search = open_items.search_receivable_open_items if capability.startswith("receivable") else open_items.search_payable_open_items
        result = search(port, current)
        sent = port.search_calls[0]["filters"]
    elif capability == "journal_item.search":
        port = objects_fixture.FakePort()
        result = objects.read_core_object(capability, port, current)
        sent = port.calls[0]["parameters"]
    else:
        port = analysis_fixture.FakePort([analysis_fixture._summary()] if capability.endswith("summary") else [])
        result = analysis.read_invoice_analysis(port, capability, current)
        sent = port.calls[0]["parameters"]
    assert all(key in sent and sent[key] == normalized[key] for key in values)
    if capability.endswith("summary"):
        assert result["company_currency"] == {"id": 6, "code": "CNY"}
    else:
        assert result == {"items": [], "has_more": False, "next_cursor": None}


def cursor_roundtrip(capability, filters, context, cursor=None):
    if capability in {"invoice.search", "journal_entry.search"}:
        module = invoices if capability == "invoice.search" else entries
        return module._decode_cursor(cursor, context=context, filters=filters) if cursor else module._encode_cursor(["2026-10-02", 31], context=context, filters=filters)
    if capability.endswith("open_items.list"):
        values = {"capability_id": capability, "context": context, "filters": filters}
        return open_items._decode_cursor(cursor, **values) if cursor else open_items._encode_cursor(["2026-10-02", 31], **values)
    if capability == "journal_item.search":
        values = {"capability_id": capability, "context": context, "filters": objects._cursor_filters(filters)}
        return objects._decode_cursor(cursor, **values) if cursor else objects._encode_cursor(31, **values)
    values = {"capability_id": capability, "context": context, "parameters": filters}
    return analysis._decode_cursor(cursor, **values) if cursor else analysis._encode_cursor(31, **values)


@pytest.mark.parametrize("capability,key,kind", [case for case in CASES if not case[0].endswith("summary")])
def test_each_new_key_binds_the_cursor_without_mutating_legacy_binding(capability, key, kind):
    base = request(capability)
    old_filters = normalize(capability, base)
    cursor = cursor_roundtrip(capability, old_filters, base["context"])
    assert cursor_roundtrip(capability, deepcopy(old_filters), base["context"]) == cursor
    assert cursor_roundtrip(capability, old_filters, base["context"], cursor)
    updated = normalize(capability, request(capability, {key: VALID[kind][0]}))
    with pytest.raises(ERRORS) as caught:
        cursor_roundtrip(capability, updated, base["context"], cursor)
    assert caught.value.code == "invalid_cursor"


@pytest.mark.parametrize("parameters", [{"currency_id": 9}, {"invoice_date_from": "2025-01-21"}, {"due_date_to": "2025-02-19"}])
def test_invoice_visible_scalar_mismatch_is_rejected(parameters):
    with pytest.raises(invoices.InvoiceError, match="outside"):
        invoices.search_invoices(invoices_fixture.FakePort(rows=[invoices_fixture._header()]), request("invoice.search", parameters))


def test_journal_item_explicit_false_rejects_reconciled_rows():
    item = objects_fixture._item("journal_item.search")
    item["reconciled"] = True
    with pytest.raises(objects.CoreObjectReadError, match="outside"):
        objects.read_core_object("journal_item.search", objects_fixture.FakePort([item]), request("journal_item.search", {"reconciled": False}))


def test_journal_entry_header_currency_filter_does_not_compare_company_currency():
    row = entries_fixture._search_row(31, "2026-10-02")
    row["currency"]["id"] = 7
    port = entries_fixture.FakePort(rows=[row])
    result = entries.search_journal_entries(port, request("journal_entry.search", {"currency_id": 6}))
    assert result["items"][0]["currency"]["id"] == 7
    assert port.search_calls[0]["filters"]["currency_id"] == 6


@pytest.mark.parametrize("side", ["receivable", "payable"])
def test_open_item_move_membership_is_checked(side):
    search = open_items.search_receivable_open_items if side == "receivable" else open_items.search_payable_open_items
    with pytest.raises(open_items.OpenItemsError):
        search(open_fixture.FakePort(rows=[open_fixture._row(31, "2026-10-02", side=side)]), request(f"{side}.open_items.list", {"move_id": 999}))


@pytest.mark.parametrize("parameters", [{"journal_id": 12}, {"currency_id": 7}, {"due_date_to": "2026-09-19"}])
def test_analysis_visible_filter_mismatch_is_rejected(parameters):
    with pytest.raises(analysis.InvoiceAnalysisError):
        analysis.read_invoice_analysis(analysis_fixture.FakePort([analysis_fixture._row(31)]), "invoice.analysis.search", request("invoice.analysis.search", parameters))
