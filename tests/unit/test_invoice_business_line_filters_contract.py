from __future__ import annotations

from copy import deepcopy

import pytest
import test_document_search_batch_contract as previous

from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry

FIELDS = {
    "invoice.search": {"product_id": "id", "account_id": "id", "tax_id": "id"},
    "journal_entry.search": {"tax_id": "id", "line_query": "query"},
    "journal_item.search": {"product_id": "id", "tax_id": "id"},
    "receivable.open_items.list": {"invoice_user_id": "nullable_id", "payment_term_id": "nullable_id", "fiscal_position_id": "nullable_id"},
    "payable.open_items.list": {"invoice_user_id": "nullable_id", "payment_term_id": "nullable_id", "fiscal_position_id": "nullable_id"},
    "invoice.analysis.search": {"invoice_user_id": "nullable_id", "fiscal_position_id": "nullable_id", "account_id": "id"},
    "invoice.analysis.summary": {"invoice_user_id": "nullable_id", "fiscal_position_id": "nullable_id", "account_id": "id"},
}
CASES = [(capability, key, kind) for capability, fields in FIELDS.items() for key, kind in fields.items()]
VALID = {"id": [3], "nullable_id": [None, 3], "query": [None, "goods_100%", "x" * 200]}
INVALID = {
    "id": [None, True, False, 0, -1, "3", 1.5, [], {}],
    "nullable_id": [True, False, 0, -1, "3", 1.5, [], {}],
    "query": [True, 3, [], {}, "", " goods", "goods ", "goods\n", "x" * 201],
}


@pytest.fixture(scope="module")
def registry():
    return load_registry()


@pytest.mark.parametrize("capability,key,value", [(cap, key, value) for cap, key, kind in CASES for value in VALID[kind]])
def test_each_explicit_filter_adds_only_its_key_and_preserves_caller_input(capability, key, value, registry):
    current = previous.request(capability, {key: value})
    original = deepcopy(current)
    assert previous.normalize(capability, current) == {**previous.normalize(capability, previous.request(capability)), key: value}
    assert current == original
    registry.validate_instance(f"schemas/v1/{capability}.request.schema.json", current)


@pytest.mark.parametrize("capability,key,value", [(cap, key, value) for cap, key, kind in CASES for value in INVALID[kind]])
def test_invalid_filters_are_rejected_by_sdk_and_schema(capability, key, value, registry):
    current = previous.request(capability, {key: value})
    with pytest.raises(previous.ERRORS) as caught:
        previous.normalize(capability, current)
    assert caught.value.code == "invalid_request" and caught.value.exit_code == 2
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(f"schemas/v1/{capability}.request.schema.json", current)


@pytest.mark.parametrize("capability,key", [(cap, key) for cap, key, kind in CASES if kind != "query"])
def test_integral_float_is_not_an_sdk_identifier(capability, key):
    with pytest.raises(previous.ERRORS):
        previous.normalize(capability, previous.request(capability, {key: 3.0}))


@pytest.mark.parametrize("capability", FIELDS)
def test_omission_keeps_exact_legacy_normalization(capability):
    previous.test_omission_retains_the_exact_old_normalized_shape(capability)
    assert not FIELDS[capability].keys() & previous.normalize(capability, previous.request(capability)).keys()


@pytest.mark.parametrize("capability", FIELDS)
@pytest.mark.parametrize("unsupported", ["domain", "tax_ids", "business_only"])
def test_contract_does_not_admit_unfrozen_fields(capability, unsupported, registry):
    current = previous.request(capability, {unsupported: []})
    with pytest.raises(previous.ERRORS):
        previous.normalize(capability, current)
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(f"schemas/v1/{capability}.request.schema.json", current)


@pytest.mark.parametrize("capability,key,value", [(cap, key, value) for cap, key, kind in CASES if not cap.endswith("summary") for value in VALID[kind]])
def test_each_explicit_value_including_null_binds_the_cursor(capability, key, value):
    base = previous.request(capability)
    filters = previous.normalize(capability, base)
    cursor = previous.cursor_roundtrip(capability, filters, base["context"])
    assert previous.cursor_roundtrip(capability, deepcopy(filters), base["context"]) == cursor
    assert previous.cursor_roundtrip(capability, filters, base["context"], cursor)
    updated = previous.normalize(capability, previous.request(capability, {key: value}))
    with pytest.raises(previous.ERRORS) as caught:
        previous.cursor_roundtrip(capability, updated, base["context"], cursor)
    assert caught.value.code == "invalid_cursor"
    current_cursor = previous.cursor_roundtrip(capability, updated, base["context"])
    assert previous.cursor_roundtrip(capability, updated, base["context"], current_cursor)


def _execute(capability, current):
    if capability == "invoice.search":
        row = previous.invoices_fixture._header()
        port = previous.invoices_fixture.FakePort(rows=[row])
        result = previous.invoices.search_invoices(port, current)
        sent = port.search_calls[0]["filters"]
    elif capability == "journal_entry.search":
        row = previous.entries_fixture._search_row(31, "2026-10-02")
        port = previous.entries_fixture.FakePort(rows=[row])
        result = previous.entries.search_journal_entries(port, current)
        sent = port.search_calls[0]["filters"]
    elif capability == "journal_item.search":
        row = previous.objects_fixture._item(capability)
        port = previous.objects_fixture.FakePort([row])
        result = previous.objects.read_core_object(capability, port, current)
        sent = port.calls[0]["parameters"]
    elif capability.endswith("open_items.list"):
        side = "receivable" if capability.startswith("receivable") else "payable"
        row = previous.open_fixture._row(31, "2026-10-02", side=side)
        port = previous.open_fixture.FakePort(rows=[row])
        search = previous.open_items.search_receivable_open_items if side == "receivable" else previous.open_items.search_payable_open_items
        result = search(port, current)
        sent = port.search_calls[0]["filters"]
    else:
        row = previous.analysis_fixture._summary() if capability.endswith("summary") else previous.analysis_fixture._row(31)
        port = previous.analysis_fixture.FakePort([row])
        result = previous.analysis.read_invoice_analysis(port, capability, current)
        sent = port.calls[0]["parameters"]
    return row, result, sent


@pytest.mark.parametrize("capability", FIELDS)
def test_new_filters_reach_fixed_ports_without_new_response_projection(capability):
    values = {key: VALID[kind][0] for key, kind in FIELDS[capability].items()}
    current = previous.request(capability, values)
    row, result, sent = _execute(capability, current)
    assert all(sent[key] == value for key, value in values.items())
    assert result == row if capability.endswith("summary") else result["items"] == [row]


def test_journal_account_and_line_criteria_are_forwarded_together():
    values = {"account_id": 8, "tax_id": 9, "line_query": "fees", "query": "MISC"}
    _, _, sent = _execute("journal_entry.search", previous.request("journal_entry.search", values))
    assert all(sent[key] == value for key, value in values.items())
    legacy = previous.normalize("journal_entry.search", previous.request("journal_entry.search", {"account_id": 8}))
    assert "tax_id" not in legacy and "line_query" not in legacy


@pytest.mark.parametrize("capability", ["receivable.open_items.list", "payable.open_items.list", "invoice.analysis.search", "invoice.analysis.summary"])
def test_explicit_unset_headers_remain_distinct_from_omission(capability):
    keys = [key for key, kind in FIELDS[capability].items() if kind == "nullable_id"]
    base = previous.normalize(capability, previous.request(capability))
    current = previous.normalize(capability, previous.request(capability, dict.fromkeys(keys)))
    assert all(key not in base and key in current and current[key] is None for key in keys)
