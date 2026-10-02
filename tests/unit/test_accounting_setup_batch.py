from __future__ import annotations

import hashlib
import io
import json
from contextlib import nullcontext
from copy import deepcopy
from types import SimpleNamespace

import pytest
from test_company_processing_batch import result as company_result
from test_core_writes_runtime import Failure
from test_fiscal_mapping_writes import request
from test_journal_item_processing_batch import result as move_result

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4 import company_processing_contracts as company
from odoo_accounting_cli_v4.bridge import core_writes_runtime as runtime
from odoo_accounting_cli_v4.capabilities import core_object_reads, core_writes
from odoo_accounting_cli_v4.registry import load_registry

PARAMETERS = {
    "company.cash_basis_configuration.update": {"changes": {"tax_exigibility": True, "tax_cash_basis_journal_id": 11, "account_cash_basis_base_account_id": 12}},
    "tax.create": {"name": "Grouped sale tax", "type_tax_use": "sale", "amount_type": "group", "amount": 0,
                   "children_tax_ids": [32, 31], "tax_scope": None, "analytic": True,
                   "tax_exigibility": "on_payment", "cash_basis_transition_account_id": 12},
    "tax.update": {"tax_id": 33, "changes": {"children_tax_ids": [], "tax_scope": "service", "analytic": False,
                  "tax_exigibility": "on_invoice", "cash_basis_transition_account_id": None}},
    "invoice.update": {"move_id": 31, "changes": {"reference": "Posted reference", "payment_reference": "Posted payment"}},
    "journal_entry.update": {"move_id": 31, "changes": {"reference": "Posted reference"}},
    "invoice.presentation_settings.update": {"move_id": 31, "changes": {"narration": "<p>Updated terms</p>", "invoice_user_id": 42}},
}
READ_PARAMETERS = {company.GET_ID: {}, "cash_rounding.compute": {"cash_rounding_id": 31, "currency_id": 6, "amount": "-23.91"}}


def result(capability_id, parameters):
    if capability_id.startswith("company."):
        return company_result(capability_id, parameters)
    if capability_id.startswith("tax."):
        return {**company_result("", {}), "model": "account.tax", "id": parameters.get("tax_id", 33), "name": "Grouped sale tax"}
    return {**move_result(capability_id, parameters), "state": "posted", "move_type": "entry" if capability_id.startswith("journal_entry.") else "out_invoice"}


def read_item(capability_id):
    if capability_id == "cash_rounding.compute":
        return {"id": 31, "company_id": 7, "currency_id": 6, "amount": "-23.91", "base_amount": "-23.91", "rounded_amount": "-23.9", "difference": "0.01"}
    item = {"id": 7, "company_id": 7}
    for field in company.SETTING_FIELDS:
        item[field] = False if field in company.BOOL_FIELDS else None if field in company.RELATION_MODELS or field == "quick_edit_mode" else 31 if field == "fiscalyear_last_day" else "12" if field == "fiscalyear_last_month" else min(company.CHOICES[field])
    item.update(tax_exigibility=True, tax_cash_basis_journal_id=11, account_cash_basis_base_account_id=12)
    return item


@pytest.fixture(scope="module")
def registry():
    return load_registry()


@pytest.mark.parametrize("capability_id", PARAMETERS)
def test_public_write_confirmation_schema_key_and_closed_native_binding(capability_id, registry, monkeypatch):
    params, expected = PARAMETERS[capability_id], result(capability_id, PARAMETERS[capability_id])
    req = request(params)
    normalized = core_writes.validate_core_write_request(capability_id, req)[2]
    key = core_writes._expected_idempotency_key(capability_id, normalized, 7)
    assert runtime._deterministic_key(capability_id, normalized, 7) == (None if capability_id == "tax.create" else key)
    assert runtime._valid_parameters(capability_id, normalized, 7)
    registry.validate_instance(f"schemas/v1/{capability_id}.request.schema.json", req)

    class Port:
        user_id = 42

        def execute(self, **payload):
            assert payload["parameters"] == normalized and payload["company_id"] == 7
            assert payload["idempotency_key"] == key and payload["confirmation"] == capability_id
            return {"user_id": 42, "company_visible": True, "module_installed": True, "access_allowed": True,
                    "idempotent_replay": False, "result": expected}

    monkeypatch.setattr(cli, "load_registry", lambda: registry)
    stdout, stderr = io.StringIO(), io.StringIO()
    assert cli.main(["write", "run", capability_id, "--request", "-", "--confirm", capability_id, "--idempotency-key", key],
                    stdin=io.StringIO(json.dumps(req)), stdout=stdout, stderr=stderr, port_factory=lambda *args: Port()) == 0, stdout.getvalue()
    response = json.loads(stdout.getvalue())
    registry.validate_instance(f"schemas/v1/{capability_id}.response.schema.json", response)
    assert response["data"]["result"] == expected and not stderr.getvalue()
    for confirmation in (None, "other.operation"):
        with pytest.raises(core_writes.CoreWriteError):
            core_writes.execute_core_write(Port(), capability_id, req, key, confirmation)


@pytest.mark.parametrize("capability_id", READ_PARAMETERS)
def test_read_cli_schema_and_required_current_company_fields(capability_id, registry, monkeypatch):
    item, req = read_item(capability_id), request(READ_PARAMETERS[capability_id])

    class Port:
        user_id = 42

        def read(self, **payload):
            assert payload["parameters"] == READ_PARAMETERS[capability_id] and payload["company_id"] == 7
            return {"user_id": 42, "company_visible": True, "module_installed": True, "access_allowed": True, "cursor_found": True, "items": [item]}

    registry.validate_instance(f"schemas/v1/{capability_id}.request.schema.json", req)
    monkeypatch.setattr(cli, "load_registry", lambda: registry)
    stdout, stderr = io.StringIO(), io.StringIO()
    assert cli.main(["read", capability_id, "--request", "-"], stdin=io.StringIO(json.dumps(req)), stdout=stdout, stderr=stderr, port_factory=lambda *args: Port()) == 0, stdout.getvalue()
    response = json.loads(stdout.getvalue())
    registry.validate_instance(f"schemas/v1/{capability_id}.response.schema.json", response)
    assert response["data"] == item and not stderr.getvalue()
    for field, value in (("id", 99), ("company_id", 8), ("extra", "not allowed")):
        candidate = {**item, field: value}
        item.clear()
        item.update(candidate)
        with pytest.raises(core_object_reads.CoreObjectReadError):
            core_object_reads.read_core_object(capability_id, Port(), req)
        item.clear()
        item.update(read_item(capability_id))


@pytest.mark.parametrize("parameters", [
    {"changes": {}}, {"changes": {"tax_exigibility": 1}}, {"changes": {"tax_exigibility": None}},
    {"changes": {"tax_cash_basis_journal_id": True}}, {"changes": {"account_cash_basis_base_account_id": 0}},
    {"changes": {"currency_id": 6}}, {"changes": {"tax_exigibility": True}, "company_id": 8},
])
def test_company_cash_basis_patch_is_closed_typed_and_context_bound(parameters):
    with pytest.raises(core_writes.CoreWriteError):
        core_writes.validate_core_write_request("company.cash_basis_configuration.update", request(parameters))


@pytest.mark.parametrize("field,value", [
    ("children_tax_ids", [31, 31]), ("children_tax_ids", [False]), ("children_tax_ids", [0]),
    ("children_tax_ids", list(range(1, 102))), ("children_tax_ids", None),
    ("tax_scope", "product"), ("tax_scope", []), ("analytic", 1), ("analytic", None),
    ("tax_exigibility", "cash"), ("cash_basis_transition_account_id", False),
])
def test_advanced_tax_values_reject_bad_types_unknown_choices_and_unbounded_selection(field, value):
    with pytest.raises(core_writes.CoreWriteError):
        core_writes.validate_core_write_request("tax.update", request({"tax_id": 33, "changes": {field: value}}))


def test_group_tax_children_sorted_without_mutating_input_and_clear_is_explicit():
    params = deepcopy(PARAMETERS["tax.create"])
    normalized = core_writes.validate_core_write_request("tax.create", request(params))[2]
    assert params["children_tax_ids"] == [32, 31] and normalized["children_tax_ids"] == [31, 32]
    for children in ([], list(range(1, 101))):
        assert core_writes.validate_core_write_request("tax.update", request({"tax_id": 33, "changes": {"children_tax_ids": children}}))[2]["changes"]["children_tax_ids"] == children


@pytest.mark.parametrize("capability_id", ["tax.create", "tax.update"])
def test_legacy_tax_normalized_parameters_and_key_remain_unchanged(capability_id):
    advanced = {"children_tax_ids", "tax_scope", "analytic", "tax_exigibility", "cash_basis_transition_account_id"}
    params = {"name": "Sales Tax 15%", "type_tax_use": "sale", "amount_type": "percent", "amount": 15.0} if capability_id == "tax.create" else {"tax_id": 33, "changes": {"amount": 12.5, "invoice_label": None}}
    normalized = core_writes.validate_core_write_request(capability_id, request(params))[2]
    values = normalized if capability_id == "tax.create" else normalized["changes"]
    assert not advanced.intersection(values)
    old_values = {**params, "amount": "15", "sequence": None, "tax_group_id": None, "invoice_label": None,
                  "price_include_override": None, "include_base_amount": False, "is_base_affected": True} if capability_id == "tax.create" else {"amount": "12.5", "invoice_label": None}
    assert values == old_values
    digest = hashlib.sha256(json.dumps(old_values, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:32]
    expected = f"{capability_id}:{7 if capability_id == 'tax.create' else 33}:{digest}"
    assert core_writes._expected_idempotency_key(capability_id, normalized, 7) == expected
    assert runtime._deterministic_key(capability_id, normalized, 7) == (None if capability_id == "tax.create" else expected)


@pytest.mark.parametrize("capability_id", ["invoice.update", "journal_entry.update", "invoice.presentation_settings.update"])
def test_posted_result_acceptance_is_limited_to_nonfinancial_header_changes(capability_id):
    params = PARAMETERS[capability_id]
    expected = result(capability_id, params)
    assert core_writes._validate_result(capability_id, params, expected, company_id=7, idempotent_replay=False) == expected
    denied_changes = {"partner_shipping_id": 91} if capability_id == "invoice.presentation_settings.update" else {"date": "2026-10-01"}
    with pytest.raises(core_writes.CoreWriteError):
        core_writes._validate_result(capability_id, {"move_id": 31, "changes": denied_changes}, expected, company_id=7, idempotent_replay=False)
    for field, value in (("state", "cancel"), ("company_id", 8), ("source_id", 99)):
        with pytest.raises(core_writes.CoreWriteError):
            core_writes._validate_result(capability_id, params, {**expected, field: value}, company_id=7, idempotent_replay=False)


@pytest.mark.parametrize("capability_id", ["invoice.update", "journal_entry.update", "invoice.presentation_settings.update"])
def test_posted_nonfinancial_result_preserves_native_reconciliation_metadata(capability_id):
    params = PARAMETERS[capability_id]
    expected = {**result(capability_id, params), "partial_reconcile_ids": [91], "full_reconcile_id": 92, "reconciled": True}
    assert core_writes._validate_result(capability_id, params, expected, company_id=7, idempotent_replay=False) == expected


@pytest.mark.parametrize("params", [
    {"cash_rounding_id": 31, "currency_id": 6, "amount": True},
    {"cash_rounding_id": 31, "currency_id": 6, "amount": 1.2},
    {"cash_rounding_id": 31, "currency_id": 6, "amount": "NaN"},
    {"cash_rounding_id": False, "currency_id": 6, "amount": "0"},
    {"cash_rounding_id": 31, "currency_id": 0, "amount": "0"},
    {"cash_rounding_id": 31, "currency_id": 6, "amount": "0", "company_id": 8},
])
def test_rounding_compute_rejects_invalid_money_and_context_override(params):
    with pytest.raises(core_object_reads.CoreObjectReadError):
        core_object_reads.validate_core_object_read_request("cash_rounding.compute", request(params))


@pytest.mark.parametrize("value", [True, False])
def test_branch_cash_basis_boolean_denied_before_current_state_replay(monkeypatch, value):
    env = SimpleNamespace(cr=SimpleNamespace(savepoint=nullcontext))
    company_record = SimpleNamespace(parent_id=SimpleNamespace(id=1), tax_exigibility=value)
    monkeypatch.setattr(runtime, "_search_one", lambda *args: company_record)
    monkeypatch.setattr(runtime, "_company_processing_values", lambda record: pytest.fail("branch boolean must be denied before replay"))
    with pytest.raises(Failure) as caught:
        runtime._write_company_processing(env, "company.cash_basis_configuration.update", {"changes": {"tax_exigibility": value}}, 7, Failure)
    assert caught.value.code == "company_unavailable" and caught.value.exit_code == 3


def test_root_cash_basis_native_patch_nullable_clear_replay_and_ancestor_reference_domains(monkeypatch):
    env = SimpleNamespace(cr=SimpleNamespace(savepoint=nullcontext))
    values = {"tax_exigibility": False, "tax_cash_basis_journal_id": None, "account_cash_basis_base_account_id": None}
    writes, references = [], []

    def write(changes):
        writes.append(changes)
        values.update({key: None if value is False and key != "tax_exigibility" else value for key, value in changes.items()})

    record = SimpleNamespace(parent_id=False, write=write, invalidate_recordset=lambda: None)
    monkeypatch.setattr(runtime, "_search_one", lambda *args: record)
    monkeypatch.setattr(runtime, "_company_processing_values", lambda record: dict(values))
    monkeypatch.setattr(runtime, "_config_result", lambda *args: company_result("", {}))
    monkeypatch.setattr(runtime, "_ensure_ids", lambda env, model, ids, domain, *args: references.append((model, ids, domain)))
    cap, params = "company.cash_basis_configuration.update", PARAMETERS["company.cash_basis_configuration.update"]
    assert runtime._write_company_processing(env, cap, params, 7, Failure)[1] is False
    assert runtime._write_company_processing(env, cap, params, 7, Failure)[1] is True and len(writes) == 1
    assert ("account.journal", {11}, [("company_id", "parent_of", [7])]) in references
    assert ("account.account", {12}, [("company_ids", "parent_of", [7])]) in references
    cleared = {"changes": {"tax_exigibility": False, "tax_cash_basis_journal_id": None, "account_cash_basis_base_account_id": None}}
    assert runtime._write_company_processing(env, cap, cleared, 7, Failure)[1] is False
    assert writes[-1] == dict.fromkeys(values, False)
    assert runtime._write_company_processing(env, cap, cleared, 7, Failure)[1] is True and len(writes) == 2


@pytest.mark.parametrize("capability_id", ["invoice.update", "journal_entry.update"])
def test_posted_native_reference_set_clear_replay_and_date_gate_before_replay(monkeypatch, capability_id):
    writes = []
    record = SimpleNamespace(state="posted", ref=False, payment_reference=False, date="2026-10-02")

    def write(values):
        writes.append(values)
        for key, value in values.items():
            setattr(record, key, value)

    record.write = write
    monkeypatch.setattr(runtime, "_lifecycle_move", lambda *args: record)
    monkeypatch.setattr(runtime, "_validate_invoice_update_references", lambda *args: None)
    monkeypatch.setattr(runtime, "_validate_journal_update_references", lambda *args: None)
    monkeypatch.setattr(runtime, "_move_result", lambda *args: result(capability_id, PARAMETERS[capability_id]))
    changes = PARAMETERS[capability_id]["changes"]
    params = {"move_id": 31, "changes": changes}
    assert runtime._update_move(None, capability_id, params, 7, Failure)[1] is False
    assert record.ref == changes["reference"]
    assert runtime._update_move(None, capability_id, params, 7, Failure)[1] is True and len(writes) == 1
    with pytest.raises(Failure) as caught:
        runtime._update_move(None, capability_id, {"move_id": 31, "changes": {"date": record.date}}, 7, Failure)
    assert caught.value.code == "state_conflict" and caught.value.exit_code == 5 and len(writes) == 1
    cleared = {"move_id": 31, "changes": dict.fromkeys(changes)}
    assert runtime._update_move(None, capability_id, cleared, 7, Failure)[1] is False
    assert not record.ref and runtime._update_move(None, capability_id, cleared, 7, Failure)[1] is True and len(writes) == 2
    record.state = "cancel"
    with pytest.raises(Failure) as caught:
        runtime._update_move(None, capability_id, cleared, 7, Failure)
    assert caught.value.code == "state_conflict" and len(writes) == 2


@pytest.mark.parametrize("account_id", [None, 12])
def test_cash_basis_transition_requires_native_reconcilable_account(monkeypatch, account_id):
    calls = []

    def ensure(env, model, ids, domain, *args):
        calls.append((model, ids, domain))
        return SimpleNamespace(reconcile=False)

    monkeypatch.setattr(runtime, "_ensure_ids", ensure)
    with pytest.raises(Failure) as caught:
        runtime._validate_tax_references(None, {"tax_exigibility": "on_payment", "cash_basis_transition_account_id": account_id}, 7, Failure)
    assert caught.value.code == "business_rule_error" and caught.value.exit_code == 6
    assert calls == ([] if account_id is None else [("account.account", {12}, [("company_ids", "parent_of", [7])])])


@pytest.mark.parametrize("field,value", [("currency_id", 8), ("amount", "23.91"), ("difference", 0.01), ("rounded_amount", "NaN")])
def test_rounding_results_bind_input_currency_money_and_closed_decimal_fields(field, value):
    item = {**read_item("cash_rounding.compute"), field: value}

    class Port:
        user_id = 42

        def read(self, **kwargs):
            return {"user_id": 42, "company_visible": True, "module_installed": True, "access_allowed": True, "cursor_found": True, "items": [item]}

    with pytest.raises(core_object_reads.CoreObjectReadError):
        core_object_reads.read_core_object("cash_rounding.compute", Port(), request(READ_PARAMETERS["cash_rounding.compute"]))
