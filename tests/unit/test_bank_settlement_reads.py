"""Focused read contracts and native-domain forwarding, without live database writes."""

from __future__ import annotations

from copy import deepcopy

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from test_bank_transaction_search import FakePort, _row
from test_core_object_reads import _item
from test_core_object_reads_runtime import (
    _dispatch,
    _fake_odoo_expression,  # noqa: F401 - reusable pytest fixture.
    _fixture,
    _parameters,
)
from test_fiscal_mapping_writes import request

from odoo_accounting_cli_v4.bridge import core_object_reads_runtime as objects_runtime
from odoo_accounting_cli_v4.bridge import runtime
from odoo_accounting_cli_v4.capabilities import bank_transactions as transactions
from odoo_accounting_cli_v4.capabilities import core_object_reads as objects
from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry

pytestmark = pytest.mark.usefixtures("_fake_odoo_expression")


@pytest.fixture(scope="module")
def registry():
    return load_registry()


def transaction_filters(parameters):
    return transactions.validate_bank_transaction_search_request(request(parameters))[2]


def payload(filters):
    return {"company_id": 7, "after": None, "limit": 2, "filters": filters}


def get_item_errors(registry, item):
    schema = registry.load_schema("schemas/v1/bank.transaction.get.response.schema.json")
    validator = Draft202012Validator({"$ref": schema["$id"] + "#/$defs/item"},
                                    registry=registry._schema_resources, format_checker=FormatChecker())
    return list(validator.iter_errors(item))


def test_omitted_new_filters_keep_old_normalized_shapes():
    expected = {"date_from": None, "date_to": None, "journal_id": None, "partner_id": None, "reconciled": None, "query": None}
    assert transaction_filters({}) == transaction_filters({"statement_id": None}) == expected
    normalized = objects.validate_core_object_read_request("bank.statement.search", request({}))[2]
    assert normalized == {"journal_id": None, "date_from": None, "date_to": None, "limit": 100, "cursor": None}


@pytest.mark.parametrize("assignment,statement_id", [("assigned", None), ("assigned", 31), ("unassigned", None)])
def test_assignment_filter_reaches_native_domain_and_schema(assignment, statement_id, registry):
    params = {"statement_assignment": assignment, "statement_id": statement_id}
    filters = transaction_filters(params)
    registry.validate_instance("schemas/v1/bank.transaction.search.request.schema.json", request(params))
    assert filters["statement_assignment"] == assignment and runtime._bank_transaction_payload_is_valid(payload(filters))
    domain = runtime._bank_transaction_domain(7, None, filters)
    assert ("statement_id", "!=" if assignment == "assigned" else "=", False) in domain
    if statement_id is not None:
        assert ("statement_id", "=", statement_id) in domain


@pytest.mark.parametrize("value", [None, True, 0, "", "all", [], {}])
def test_assignment_unknown_and_bad_types_denied_before_port(value, registry):
    req = request({"statement_assignment": value})
    with pytest.raises(transactions.BankTransactionListError):
        transactions.search_bank_transactions(object(), req)
    with pytest.raises(InstanceValidationError):
        registry.validate_instance("schemas/v1/bank.transaction.search.request.schema.json", req)
    assert not runtime._bank_transaction_payload_is_valid(payload({**transaction_filters({}), "statement_assignment": value}))


def test_positive_statement_with_unassigned_is_closed_invalid_input(registry):
    params = {"statement_id": 31, "statement_assignment": "unassigned"}
    with pytest.raises(transactions.BankTransactionListError):
        transactions.search_bank_transactions(object(), request(params))
    with pytest.raises(InstanceValidationError):
        registry.validate_instance("schemas/v1/bank.transaction.search.request.schema.json", request(params))
    assert not runtime._bank_transaction_payload_is_valid(payload({**transaction_filters({}), **params}))


@pytest.mark.parametrize("assignment,linked", [("assigned", 31), ("unassigned", None)])
def test_assignment_pagination_cursor_binding_outside_rows_and_empty(assignment, linked):
    port = FakePort()
    port.rows = [{**row, "statement_id": linked} for row in port.rows]
    first = transactions.search_bank_transactions(port, request({"statement_assignment": assignment, "limit": 1}))
    second = transactions.search_bank_transactions(port, request({"statement_assignment": assignment, "limit": 1, "cursor": first["next_cursor"]}))
    assert [first["items"][0]["id"], second["items"][0]["id"]] == [12, 11]
    calls = len(port.calls)
    with pytest.raises(transactions.BankTransactionListError) as denied:
        transactions.search_bank_transactions(port, request({"statement_assignment": "unassigned" if linked else "assigned", "cursor": first["next_cursor"]}))
    assert denied.value.code == "invalid_cursor" and len(port.calls) == calls
    port.rows = [{**_row(12, 20), "statement_id": None if linked else 31}]
    with pytest.raises(transactions.BankTransactionListError):
        transactions.search_bank_transactions(port, request({"statement_assignment": assignment}))
    port.rows = []
    assert transactions.search_bank_transactions(port, request({"statement_assignment": assignment})) == {"items": [], "has_more": False, "next_cursor": None}


@pytest.mark.parametrize("field", ["is_complete", "is_valid"])
@pytest.mark.parametrize("value", [False, True])
def test_statement_boolean_domain_is_forwarded_before_limit(field, value, registry):
    req = request({field: value})
    registry.validate_instance("schemas/v1/bank.statement.search.request.schema.json", req)
    normalized = objects.validate_core_object_read_request("bank.statement.search", req)[2]
    assert normalized[field] is value
    parameters = {**_parameters("bank.statement.search"), field: value, "limit": 1}
    assert objects_runtime._valid_parameters("bank.statement.search", parameters)
    env, records = _fixture()
    domain = objects_runtime._reference_domain(env, "bank.statement.search", 7, parameters, include_after=True)
    assert (field, "=", value) in domain  # Native boolean optimizer, including _search_is_valid, owns expansion.
    page = _dispatch(env, "bank.statement.search", parameters)
    assert [row["id"] for row in page["items"]] == [next(row.id for row in records["bank_statements"] if getattr(row, field) is value)]
    assert all(row[field] is value for row in page["items"])
    calls = [call for call in env.models["account.bank.statement"].calls if call[0] == "search_read"]
    assert (field, "=", value) in calls[-1][1] and calls[-1][3] == 1


@pytest.mark.parametrize("field", ["is_complete", "is_valid"])
@pytest.mark.parametrize("value", [None, 0, 1, "false", [], {}])
def test_statement_boolean_filters_reject_null_and_coercion(field, value, registry):
    req = request({field: value})
    with pytest.raises(objects.CoreObjectReadError):
        objects.read_core_object("bank.statement.search", object(), req)
    with pytest.raises(InstanceValidationError):
        registry.validate_instance("schemas/v1/bank.statement.search.request.schema.json", req)
    assert not objects_runtime._valid_parameters("bank.statement.search", {**_parameters("bank.statement.search"), field: value})


def test_statement_cursor_binds_explicit_booleans_and_empty_page():
    class Port:
        user_id = 42

        def __init__(self):
            self.calls = []

        def read(self, **values):
            self.calls.append(values)
            rows = [_item("bank.statement.search", 31), _item("bank.statement.search", 32)] if values["parameters"]["after_id"] is None else []
            return {"user_id": 42, "company_visible": True, "module_installed": True, "access_allowed": True, "cursor_found": True, "items": rows}

    port = Port()
    first = objects.read_core_object("bank.statement.search", port, request({"is_valid": True, "limit": 1}))
    with pytest.raises(objects.CoreObjectReadError) as denied:
        objects.read_core_object("bank.statement.search", port, request({"is_valid": False, "limit": 1, "cursor": first["next_cursor"]}))
    assert denied.value.code == "invalid_cursor" and len(port.calls) == 1
    second = objects.read_core_object("bank.statement.search", port, request({"is_valid": True, "limit": 1, "cursor": first["next_cursor"]}))
    assert second == {"items": [], "has_more": False, "next_cursor": None}
    assert port.calls[-1]["parameters"]["is_valid"] is True


@pytest.mark.parametrize("metadata", [{}, {"account_number": None}, {"partner_name": "Supplier"}, {"account_number": "ACC-001", "partner_name": None}])
def test_get_metadata_independent_optional_read_compatibility(metadata, registry):
    item = {**_item("bank.transaction.get"), **metadata}
    assert objects._valid_bank_item(item, 7)
    assert not get_item_errors(registry, item)
    assert not objects._valid_bank_item({**item, "company_id": 8}, 7)
    assert not objects._valid_bank_item({**item, "unknown": "value"}, 7)


@pytest.mark.parametrize("field", ["account_number", "partner_name"])
@pytest.mark.parametrize("value", [True, 0, [], {}])
def test_get_metadata_rejects_bad_flat_types(field, value, registry):
    item = {**_item("bank.transaction.get"), field: value}
    assert not objects._valid_bank_item(item, 7)
    assert get_item_errors(registry, item)


@pytest.mark.parametrize("account_number,partner_name", [(False, ""), ("ACC-001", "Supplier")])
def test_native_get_projects_metadata_without_related_bank_gates(account_number, partner_name):
    env, _ = _fixture()
    model = env.models["account.bank.statement.line"]
    model.rows[0].account_number, model.rows[0].partner_name = account_number, partner_name
    before_models = set(env.models)
    page = _dispatch(env, "bank.transaction.get", _parameters("bank.transaction.get"))
    item = page["items"][0]
    assert item["account_number"] == (account_number or None) and item["partner_name"] == (partner_name or None)
    assert set(env.models) == before_models
    fields = next(call[4] for call in model.calls if call[0] == "search_read")
    assert "account_number" in fields and "partner_name" in fields
    assert env.models["res.partner.bank"].calls == []  # Flat import metadata does not dereference a bank account.
    original = deepcopy(item)
    item.pop("account_number")
    assert objects._valid_bank_item(item, 7) and original["id"] == item["id"]
