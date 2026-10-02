from __future__ import annotations

import io
import json
from copy import deepcopy
from decimal import Decimal

import pytest
from test_fiscal_mapping_writes import request

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4 import journal_item_processing_contracts as contracts
from odoo_accounting_cli_v4.bridge import core_object_reads_runtime as reads
from odoo_accounting_cli_v4.bridge import core_writes_runtime as writes
from odoo_accounting_cli_v4.capabilities import core_object_reads, core_writes
from odoo_accounting_cli_v4.registry import load_registry

PARAMETERS = {
    "journal_item.date_maturity.update": {"move_id": 31, "line_id": 41, "date_maturity": "2026-11-01"},
    "journal_item.analytic_distribution.replace": {"move_id": 31, "line_id": 41, "analytic_distribution": {"51": "100"}},
    "invoice.line.unit.assign": {"move_id": 31, "line_id": 41, "product_uom_id": 61},
    "invoice.line.deductibility.update": {"move_id": 31, "line_id": 41, "deductible_amount": "50"},
    "journal_entry.lines.update": {"move_id": 31, "lines": [
        {"line_id": 41, "changes": {"debit": "20", "name": "Expense"}},
        {"line_id": 42, "changes": {"credit": "20"}},
    ]},
}
READ_PARAMETERS = {
    contracts.DETAIL_ID: {"journal_item_id": 31},
    contracts.RECONCILIATION_ID: {"journal_item_id": 31},
    contracts.ANALYTIC_LIST_ID: {"journal_item_id": 71, "limit": 100, "cursor": None},
}


def result(capability_id, parameters):
    invoice = capability_id.startswith("invoice.")
    return {"model": "account.move", "id": parameters["move_id"], "name": "BILL/2026/0031",
            "state": "draft", "company_id": 7, "move_type": "in_invoice" if invoice else "entry",
            "source_id": parameters.get("line_id"), "line_ids": [41, 42], "partial_reconcile_ids": [],
            "full_reconcile_id": None, "reconciled": False}


def read_item(capability_id, record_id=31):
    item = {"id": record_id, "move_id": 81, "company_id": 7, "amount_residual": "20",
            "amount_residual_currency": "20", "currency_id": 1, "company_currency_id": 1}
    if capability_id == contracts.DETAIL_ID:
        return {**item, "parent_state": "posted", "move_type": "out_invoice", "display_type": "payment_term",
                "account_id": 11, "product_id": None, "product_uom_id": None, "deductible_amount": "100",
                "date_maturity": "2026-11-01", "discount_date": None, "discount_amount_currency": "0",
                "payment_id": None, "statement_line_id": None, "no_followup": False}
    if capability_id == contracts.RECONCILIATION_ID:
        return {**item, "reconciled": False, "matching_number": "P31", "partial_reconcile_ids": [91],
                "full_reconcile_id": None, "reconciled_journal_item_ids": [41]}
    return {"id": record_id, "name": "Allocation", "date": "2026-10-02", "amount": "-20", "unit_amount": "0",
            "company_id": 7, "currency": {"id": 1, "code": "CNY"}, "uom": None,
            "partner": None, "product": None, "general_account": {"id": 11, "code": "6000", "name": "Expense"},
            "journal_item_id": 71, "reference": None, "analytic_accounts": [{"id": 51, "name": "Project"}]}


@pytest.fixture(scope="module")
def registry():
    return load_registry()


@pytest.mark.parametrize("capability_id", PARAMETERS)
def test_closed_write_cli_schema_key_and_parent_line_binding(capability_id, registry, monkeypatch):
    params, expected = PARAMETERS[capability_id], result(capability_id, PARAMETERS[capability_id])
    req = request(params)
    registry.validate_instance(f"schemas/v1/{capability_id}.request.schema.json", req)
    key = contracts.idempotency_key(capability_id, params, 7)
    assert writes._valid_parameters(capability_id, params, 7)
    assert key == writes._deterministic_key(capability_id, params, 7) == core_writes._expected_idempotency_key(capability_id, params, 7)

    class Port:
        user_id = 42

        def execute(self, **payload):
            assert payload["parameters"] == params and payload["company_id"] == 7
            assert payload["confirmation"] == capability_id and payload["idempotency_key"] == key
            return {"user_id": 42, "company_visible": True, "module_installed": True, "access_allowed": True,
                    "idempotent_replay": False, "result": expected}

    monkeypatch.setattr(cli, "load_registry", lambda: registry)
    stdout, stderr = io.StringIO(), io.StringIO()
    assert cli.main(["write", "run", capability_id, "--request", "-", "--confirm", capability_id, "--idempotency-key", key],
                    stdin=io.StringIO(json.dumps(req)), stdout=stdout, stderr=stderr, port_factory=lambda *args: Port()) == 0, stdout.getvalue()
    registry.validate_instance(f"schemas/v1/{capability_id}.response.schema.json", json.loads(stdout.getvalue()))
    assert not stderr.getvalue()
    for field, value in (("id", 99), ("company_id", 8), ("model", "account.move.line"), ("source_id", 99), ("state", "deleted")):
        with pytest.raises(core_writes.CoreWriteError):
            core_writes._validate_result(capability_id, params, {**expected, field: value}, company_id=7, idempotent_replay=False)
    if "line_id" in params:
        with pytest.raises(core_writes.CoreWriteError):
            core_writes._validate_result(capability_id, params, {**expected, "line_ids": [42]}, company_id=7, idempotent_replay=False)


@pytest.mark.parametrize("capability_id", READ_PARAMETERS)
def test_closed_read_cli_schema_target_and_company_binding(capability_id, registry, monkeypatch):
    params, item = READ_PARAMETERS[capability_id], read_item(capability_id)
    req = request(params)
    registry.validate_instance(f"schemas/v1/{capability_id}.request.schema.json", req)
    native = {"journal_item_id": params["journal_item_id"], "limit": 101, "after_id": None} if capability_id == contracts.ANALYTIC_LIST_ID else params
    assert reads._valid_parameters(capability_id, native)

    class Port:
        user_id = 42

        def read(self, **payload):
            assert payload["parameters"] == native and payload["company_id"] == 7
            return {"user_id": 42, "company_visible": True, "module_installed": True, "access_allowed": True,
                    "cursor_found": True, "items": [item]}

    monkeypatch.setattr(cli, "load_registry", lambda: registry)
    stdout, stderr = io.StringIO(), io.StringIO()
    assert cli.main(["read", capability_id, "--request", "-"], stdin=io.StringIO(json.dumps(req)),
                    stdout=stdout, stderr=stderr, port_factory=lambda *args: Port()) == 0, stdout.getvalue()
    response = json.loads(stdout.getvalue())
    registry.validate_instance(f"schemas/v1/{capability_id}.response.schema.json", response)
    assert not stderr.getvalue()
    for field, value in (("company_id", 8), ("journal_item_id", 72)) if capability_id == contracts.ANALYTIC_LIST_ID else (("id", 99), ("company_id", 8)):
        original, item[field] = item[field], value
        with pytest.raises(core_object_reads.CoreObjectReadError):
            core_object_reads.read_core_object(capability_id, Port(), req)
        item[field] = original


@pytest.mark.parametrize("capability_id,changes", [
    ("journal_item.date_maturity.update", {"line_id": True}),
    ("journal_item.date_maturity.update", {"date_maturity": "2026-02-30"}),
    ("journal_item.analytic_distribution.replace", {"analytic_distribution": {}}),
    ("journal_item.analytic_distribution.replace", {"analytic_distribution": {"__update__": "100"}}),
    ("journal_item.analytic_distribution.replace", {"analytic_distribution": {"51": "101"}}),
    ("journal_item.analytic_distribution.replace", {"analytic_distribution": {"51": "0"}}),
    ("journal_item.analytic_distribution.replace", {"analytic_distribution": {"51,52": "50", "52": "50"}}),
    ("invoice.line.unit.assign", {"product_uom_id": None}),
    ("invoice.line.deductibility.update", {"deductible_amount": "100.01"}),
    ("invoice.line.deductibility.update", {"deductible_amount": 50}),
    ("invoice.line.deductibility.update", {"deductible_amount": "50.0"}),
    ("journal_entry.lines.update", {"lines": []}),
    ("journal_entry.lines.update", {"lines": [{"line_id": 41, "changes": {}}]}),
    ("journal_entry.lines.update", {"lines": [{"line_id": 41, "changes": {"balance": "20"}}]}),
    ("journal_entry.lines.update", {"lines": [{"line_id": 41, "changes": {"debit": "-1"}}]}),
    ("journal_entry.lines.update", {"lines": [{"line_id": 42, "changes": {"name": "One"}}, {"line_id": 41, "changes": {"name": "Two"}}]}),
    ("journal_entry.lines.update", {"lines": [{"line_id": 41, "changes": {"name": "One"}}, {"line_id": 41, "changes": {"name": "Two"}}]}),
])
def test_invalid_closed_parameters_are_rejected(capability_id, changes):
    params = {**deepcopy(PARAMETERS[capability_id]), **changes}
    with pytest.raises(ValueError):
        contracts.normalize_parameters(capability_id, params)
    with pytest.raises(core_writes.CoreWriteError):
        core_writes.validate_core_write_request(capability_id, request(params))


def test_native_nullable_distribution_and_existing_line_only_contract():
    assert contracts.normalize_parameters("journal_item.analytic_distribution.replace", {**PARAMETERS["journal_item.analytic_distribution.replace"], "analytic_distribution": None})["analytic_distribution"] is None
    assert contracts.normalize_parameters("invoice.line.deductibility.update", {**PARAMETERS["invoice.line.deductibility.update"], "deductible_amount": "0"})["deductible_amount"] == "0"
    assert contracts.PARAMETER_KEYS["journal_entry.lines.update"] == {"move_id", "lines"}
    assert "amount_currency" not in contracts.ENTRY_FIELDS and "tax_ids" not in contracts.ENTRY_FIELDS


@pytest.mark.parametrize("capability_id", ["journal_item.date_maturity.update", "journal_item.analytic_distribution.replace"])
def test_posted_settled_parent_result_keeps_native_reconciled_boolean(capability_id):
    params = PARAMETERS[capability_id]
    value = {**result(capability_id, params), "state": "posted", "reconciled": True}
    core_writes._validate_result(capability_id, params, value, company_id=7, idempotent_replay=False)


@pytest.mark.parametrize("field,value", [("debit", "40"), ("credit", "40.5"), ("deductible_amount", "50")])
def test_native_float_fields_receive_floats_not_decimal_objects(field, value):
    # Native AML.write subtracts a previous float before ORM field conversion.
    native = writes._journal_item_write_values({field: value})[field]
    assert type(native) is float and native == float(Decimal(value))
    assert 20.0 - native == 20.0 - float(value)
