"""Fixed order-accounting projections, explicit filters and exact line reads."""

from __future__ import annotations

import base64
import json
from copy import deepcopy

import pytest
from test_order_documents import (
    FakePort,
    _currency,
    _purchase_header,
    _purchase_line,
    _request,
    _sale_header,
    _sale_line,
    _summary,
)

from odoo_accounting_cli_v4.capabilities.order_documents import (
    OrderDocumentReadError,
    read_order_document,
    validate_order_document_request,
)
from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry

FILTERS = {"user_id": 5, "payment_term_id": 11, "fiscal_position_id": 12}
SUMMARY = {"date_from": "2026-01-01", "date_to": "2026-12-31", "group_by": "partner"}


@pytest.fixture(scope="module")
def registry():
    return load_registry()


def _schema_request(registry, capability, parameters):
    document = _request(parameters)
    registry.validate_instance(f"schemas/v1/{capability}.request.schema.json", document)
    return document


def _read(registry, capability, parameters, row):
    data = read_order_document(FakePort([row]), capability, _schema_request(registry, capability, parameters))
    model = f"{capability.split('.')[0]}.order" + (".line" if ".line." in capability else "")
    document = {
        "schema_version": "v1", "request_id": _request({})["request_id"],
        "success": True, "capability": capability, "status": "verified", "data": data,
        "warnings": [], "error": None,
        "odoo": {"database": "odoo_cli_v4_dev", "company_id": 7, "user_id": 5, "model": model, "record_ids": [row.get("id", 10)]},
        "audit": {"operation_id": None, "idempotency_key": None, "verification": None},
    }
    registry.validate_instance(f"schemas/v1/{capability}.response.schema.json", document)
    return data


def _line(prefix):
    return _sale_line() if prefix == "sale" else _purchase_line()


def _header(prefix, details=False):
    return (_sale_header if prefix == "sale" else _purchase_header)(include_details=details)


def _invoice(prefix, record_id=901, move_type=None):
    return {"id": record_id, "name": f"INV/{record_id}", "move_type": move_type or ("out_invoice" if prefix == "sale" else "in_invoice"),
            "state": "posted", "payment_state": "paid", "amount_total": "30", "currency": _currency()}


@pytest.mark.parametrize("prefix", ["sale", "purchase"])
@pytest.mark.parametrize("operation", ["search", "analysis.summary"])
def test_accounting_filters_preserve_omission_explicit_null_and_input(prefix, operation, registry):
    capability = f"{prefix}.order.{operation}"
    base = SUMMARY if operation == "analysis.summary" else {}
    old = validate_order_document_request(capability, _request(base))[2]
    assert not set(FILTERS) & set(old)
    extra = {**FILTERS, "payment_term_id": None}
    document = _schema_request(registry, capability, {**base, **extra})
    original = deepcopy(document)
    normalized = validate_order_document_request(capability, document)[2]
    assert normalized == {**old, **extra} and document == original


@pytest.mark.parametrize("prefix", ["sale", "purchase"])
@pytest.mark.parametrize("operation", ["search", "analysis.summary"])
@pytest.mark.parametrize("field", FILTERS)
@pytest.mark.parametrize("value", [True, 0, 1.5, "1", [], {}])
def test_accounting_filter_types_are_closed(prefix, operation, field, value, registry):
    capability = f"{prefix}.order.{operation}"
    parameters = {**(SUMMARY if operation == "analysis.summary" else {}), field: value}
    with pytest.raises(OrderDocumentReadError) as caught:
        validate_order_document_request(capability, _request(parameters))
    assert caught.value.code == "invalid_request"
    with pytest.raises(InstanceValidationError):
        _schema_request(registry, capability, parameters)


@pytest.mark.parametrize("prefix", ["sale", "purchase"])
def test_summary_invoice_status_filter_is_optional_sorted_and_native(prefix, registry):
    capability = f"{prefix}.order.analysis.summary"
    old = validate_order_document_request(capability, _request(SUMMARY))[2]
    assert "invoice_statuses" not in old
    parameters = {**SUMMARY, "invoice_statuses": ["to invoice", "no"]}
    normalized = validate_order_document_request(capability, _schema_request(registry, capability, parameters))[2]
    assert normalized["invoice_statuses"] == ["no", "to invoice"]
    _read(registry, capability, {**SUMMARY, **FILTERS, "invoice_statuses": None}, _summary())


@pytest.mark.parametrize("prefix", ["sale", "purchase"])
@pytest.mark.parametrize("value", [True, "no", [], {}, ["unknown"], ["no", "no"], [True], [{}]])
def test_summary_invoice_status_filter_rejects_wrong_types(prefix, value, registry):
    capability = f"{prefix}.order.analysis.summary"
    parameters = {**SUMMARY, "invoice_statuses": value}
    with pytest.raises(OrderDocumentReadError):
        validate_order_document_request(capability, _request(parameters))
    with pytest.raises(InstanceValidationError):
        _schema_request(registry, capability, parameters)


@pytest.mark.parametrize("prefix", ["sale", "purchase"])
@pytest.mark.parametrize("field", ["is_downpayment", "negative_to_invoice_only"])
@pytest.mark.parametrize("value", [None, 0, "true", [], {}])
def test_line_accounting_flags_are_nonnullable_booleans(prefix, field, value, registry):
    capability = f"{prefix}.order.line.search"
    with pytest.raises(OrderDocumentReadError):
        validate_order_document_request(capability, _request({field: value}))
    with pytest.raises(InstanceValidationError):
        _schema_request(registry, capability, {field: value})


@pytest.mark.parametrize("prefix", ["sale", "purchase"])
def test_line_flags_preserve_omission_and_enforce_negative_quantity_and_downpayment(prefix, registry):
    capability = f"{prefix}.order.line.search"
    old = validate_order_document_request(capability, _request({}))[2]
    assert not {"is_downpayment", "negative_to_invoice_only"} & set(old)
    flags = {"is_downpayment": False, "negative_to_invoice_only": True}
    normalized = validate_order_document_request(capability, _schema_request(registry, capability, flags))[2]
    assert normalized == {**old, **flags}
    line = {**_line(prefix), "is_downpayment": False, "to_invoice_quantity": "-1"}
    assert _read(registry, capability, flags, line)["items"] == [line]
    for bad in ({**line, "to_invoice_quantity": "0"}, {**line, "to_invoice_quantity": "1"}, {**line, "is_downpayment": True}, {key: value for key, value in line.items() if key != "is_downpayment"}):
        with pytest.raises(OrderDocumentReadError) as caught:
            read_order_document(FakePort([bad]), capability, _request(flags))
        assert caught.value.code == "failed_validation"
    conflict = {"to_invoice_only": True, "negative_to_invoice_only": True}
    with pytest.raises(OrderDocumentReadError):
        validate_order_document_request(capability, _request(conflict))
    with pytest.raises(InstanceValidationError):
        _schema_request(registry, capability, conflict)


HEADER_PROJECTIONS = [
    (prefix, field, value) for prefix in ("sale", "purchase")
    for field in ("payment_term_id", "fiscal_position_id") for value in (None, 11)
] + [("sale", field, value) for field in ("amount_invoiced", "amount_to_invoice") for value in (None, "-12.5")]


@pytest.mark.parametrize("prefix,field,value", HEADER_PROJECTIONS)
@pytest.mark.parametrize("operation", ["search", "get"])
def test_header_accounting_projections_are_independently_optional(prefix, field, value, operation, registry):
    capability = f"{prefix}.order.{operation}"
    row = {**_header(prefix, operation == "get"), field: value}
    parameters = {"order_id": row["id"]} if operation == "get" else {}
    _read(registry, capability, parameters, row)


LINE_PROJECTIONS = [
    (prefix, "is_downpayment", value) for prefix in ("sale", "purchase") for value in (False, True)
] + [("sale", "invoice_policy", value) for value in (None, "order", "delivery")] \
    + [("purchase", "purchase_method", value) for value in (None, "purchase", "receive")] \
    + [("sale", "invoice_status", value) for value in (None, "no", "upselling")] \
    + [("sale", field, value) for field in ("posted_invoiced_quantity", "amount_invoiced", "amount_to_invoice") for value in (None, "-1.5")]


@pytest.mark.parametrize("prefix,field,value", LINE_PROJECTIONS)
@pytest.mark.parametrize("operation", ["line.search", "line.get", "get"])
def test_line_accounting_projections_are_independently_optional(prefix, field, value, operation, registry):
    line = {**_line(prefix), field: value}
    if operation == "get":
        row = _header(prefix, True)
        row["lines"] = [line]
        parameters = {"order_id": row["id"]}
    elif operation == "line.get":
        row = {**line, "invoices": []}
        parameters = {"line_id": line["id"]}
    else:
        row, parameters = line, {}
    _read(registry, f"{prefix}.order.{operation}", parameters, row)


@pytest.mark.parametrize("prefix,field,value", [
    ("sale", "invoice_policy", value) for value in (True, [], {}, "unknown")
] + [("purchase", "purchase_method", value) for value in (True, [], {}, "unknown")]
    + [("sale", "invoice_status", value) for value in (True, [], {}, "unknown")]
    + [("sale", field, value) for field in ("posted_invoiced_quantity", "amount_invoiced", "amount_to_invoice") for value in (True, 1, {}, "NaN")]
    + [(prefix, "is_downpayment", value) for prefix in ("sale", "purchase") for value in (None, 0, [], {})]
    + [("sale", "purchase_method", None), ("purchase", "invoice_policy", None), ("purchase", "amount_invoiced", None)])
def test_line_projection_types_and_direction_specific_keys_fail_closed(prefix, field, value, registry):
    capability = f"{prefix}.order.line.get"
    line = {**_line(prefix), "invoices": [], field: value}
    with pytest.raises(OrderDocumentReadError) as caught:
        _read(registry, capability, {"line_id": line["id"]}, line)
    assert caught.value.code == "failed_validation"


@pytest.mark.parametrize("prefix", ["sale", "purchase"])
def test_header_explicit_filters_require_native_projection_and_matching_owner(prefix, registry):
    capability = f"{prefix}.order.search"
    row = {**_header(prefix), "payment_term_id": 11, "fiscal_position_id": 12}
    _read(registry, capability, FILTERS, row)
    for field in FILTERS:
        bad = deepcopy(row)
        if field == "user_id":
            bad["user"]["id"] = 99
        else:
            bad.pop(field)
        with pytest.raises(OrderDocumentReadError) as caught:
            read_order_document(FakePort([bad]), capability, _request(FILTERS))
        assert caught.value.code == "failed_validation"


@pytest.mark.parametrize("prefix", ["sale", "purchase"])
@pytest.mark.parametrize("parameters", [{}, {"line_id": True}, {"line_id": 0}, {"line_id": []}, {"line_id": {}}, {"line_id": "1"}, {"line_id": 1, "order_id": 1}, {"line_id": 1, "limit": 1}, {"line_id": 1, "domain": []}])
def test_exact_line_get_request_is_closed(prefix, parameters, registry):
    capability = f"{prefix}.order.line.get"
    with pytest.raises(OrderDocumentReadError) as caught:
        validate_order_document_request(capability, _request(parameters))
    assert caught.value.code == "invalid_request"
    with pytest.raises(InstanceValidationError):
        _schema_request(registry, capability, parameters)


@pytest.mark.parametrize("prefix", ["sale", "purchase"])
def test_exact_line_get_returns_one_line_with_direction_typed_invoice_graph(prefix, registry):
    capability = f"{prefix}.order.line.get"
    line = _line(prefix)
    invoices = [_invoice(prefix), _invoice(prefix, 902, "out_refund" if prefix == "sale" else "in_refund")]
    row = {**line, "invoice_line_ids": [801, 802], "invoices": invoices}
    result = _read(registry, capability, {"line_id": line["id"]}, row)
    assert result == row and "items" not in result and "transfers" not in result
    with pytest.raises(OrderDocumentReadError) as caught:
        read_order_document(FakePort([]), capability, _request({"line_id": line["id"]}))
    assert caught.value.code == "record_not_found"
    for bad in ({**row, "id": 99}, {key: value for key, value in row.items() if key != "invoices"}, {**row, "invoices": list(reversed(invoices))}, {**row, "invoices": [invoices[0], invoices[0]]}, {**row, "invoice_line_ids": []}, {**row, "invoices": [{**invoices[0], "move_type": "in_invoice" if prefix == "sale" else "out_invoice"}]}, {**row, "invoices": [{**invoices[0], "move_type": {}}]}):
        with pytest.raises(OrderDocumentReadError) as caught:
            read_order_document(FakePort([bad]), capability, _request({"line_id": line["id"]}))
        assert caught.value.code == "failed_validation"


@pytest.mark.parametrize("prefix", ["sale", "purchase"])
def test_old_cursor_binding_is_preserved_and_explicit_new_filters_bind_cursors(prefix, registry):
    capability = f"{prefix}.order.search"
    row = _header(prefix)
    first = _read(registry, capability, {"limit": 1}, row)
    assert not first["has_more"]
    rows = [row, {**row, "id": row["id"] + 1}]
    first = read_order_document(FakePort(rows), capability, _request({"limit": 1}))
    cursor = first["next_cursor"]
    payload = json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))
    assert not set(FILTERS) & set(json.loads(payload["binding"])["filters"])
    read_order_document(FakePort([rows[1]]), capability, _request({"limit": 1, "cursor": cursor}))
    with pytest.raises(OrderDocumentReadError) as caught:
        read_order_document(FakePort([]), capability, _request({"limit": 1, "cursor": cursor, "user_id": 5}))
    assert caught.value.code == "invalid_cursor"
