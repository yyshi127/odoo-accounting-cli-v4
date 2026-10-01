from __future__ import annotations

import io
import json
from copy import deepcopy
from datetime import date
from types import SimpleNamespace

import pytest
from test_core_writes_runtime import Env, Failure, _payload
from test_fiscal_mapping_writes import request

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4 import payment_processing_contracts as contracts
from odoo_accounting_cli_v4.bridge import core_object_reads_runtime as reads
from odoo_accounting_cli_v4.bridge import core_writes_runtime as runtime
from odoo_accounting_cli_v4.capabilities import core_object_reads, core_writes
from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry

PARAMETERS = {
    "payment.bank_account.assign": {"payment_id": 31, "partner_bank_id": 41},
    "payment.destination_account.assign": {"payment_id": 31, "account_id": 11},
    "payment.sent_status.set": {"payment_id": 31, "sent": True},
    "payment.validate": {"payment_id": 31},
    "payment.reject": {"payment_id": 31},
}


def result(capability_id, parameters):
    state = "draft" if capability_id == "payment.destination_account.assign" else "paid" if capability_id == "payment.validate" else "rejected" if capability_id == "payment.reject" else "in_process"
    return {"model": "account.payment", "id": parameters["payment_id"], "name": None, "state": state,
            "company_id": 7, "move_type": None, "source_id": None, "line_ids": [],
            "partial_reconcile_ids": [], "full_reconcile_id": None, "reconciled": False}


def read_item(capability_id=contracts.GET_ID, record_id=31):
    if capability_id == contracts.BANKS_ID:
        return {"id": record_id, "payment_id": 71, "company_id": None, "partner_id": 21,
                "acc_number": "SYNTHETIC", "bank_id": None, "currency_id": None, "active": True, "allow_out_payment": False}
    item = {"id": record_id, "name": None, "company_id": 7, "state": "draft",
            "payment_type": "outbound", "partner_type": "supplier", "partner_id": 21}
    if capability_id == contracts.DUPLICATES_ID:
        return {**item, "payment_id": 71, "currency_id": 1, "date": "2026-10-01", "amount": "17.5"}
    return {**item, "partner_bank_id": None, "destination_account_id": 11, "outstanding_account_id": None,
            "is_sent": False, "payment_method_code": "manual", "move_id": None, "is_reconciled": False,
            "is_matched": False, "show_partner_bank_account": True, "require_partner_bank_account": False}


@pytest.fixture(scope="module")
def registry():
    return load_registry()


@pytest.mark.parametrize("capability_id", PARAMETERS)
def test_fixed_public_cli_contract_result_and_scope(capability_id, registry, monkeypatch):
    req = request(PARAMETERS[capability_id])
    registry.validate_instance(f"schemas/v1/{capability_id}.request.schema.json", req)
    params = core_writes.validate_core_write_request(capability_id, req)[2]
    assert runtime._valid_parameters(capability_id, params, 7)
    key = core_writes._expected_idempotency_key(capability_id, params, 7)
    assert key == runtime._deterministic_key(capability_id, params, 7)
    expected = result(capability_id, params)
    class Port:
        user_id = 42
        def execute(self, **payload):
            assert payload["parameters"] == params and payload["confirmation"] == capability_id and payload["idempotency_key"] == key
            return {"user_id": 42, "company_visible": True, "module_installed": True, "access_allowed": True,
                    "idempotent_replay": False, "result": deepcopy(expected)}
    monkeypatch.setattr(cli, "load_registry", lambda: registry)
    stdout, stderr = io.StringIO(), io.StringIO()
    assert cli.main(["write", "run", capability_id, "--request", "-", "--confirm", capability_id, "--idempotency-key", key],
                    stdin=io.StringIO(json.dumps(req)), stdout=stdout, stderr=stderr, port_factory=lambda *args: Port()) == 0
    response = json.loads(stdout.getvalue())
    assert response["success"] and not stderr.getvalue()
    registry.validate_instance(f"schemas/v1/{capability_id}.response.schema.json", response)
    for field, value in (("id", 32), ("company_id", 8), ("model", "account.move"), ("source_id", 41)):
        with pytest.raises(core_writes.CoreWriteError):
            core_writes._validate_result(capability_id, params, {**expected, field: value}, company_id=7, idempotent_replay=False)


@pytest.mark.parametrize("capability_id", sorted(contracts.READ_IDS))
def test_closed_reads_normalization_and_parent_scope(capability_id, registry, monkeypatch):
    item = read_item(capability_id)
    payment_id = 31 if capability_id == contracts.GET_ID else 71
    class Port:
        user_id = 42
        def read(self, **payload):
            assert payload["parameters"]["payment_id"] == payment_id
            return {"user_id": 42, "company_visible": True, "module_installed": True, "access_allowed": True, "cursor_found": True, "items": [item]}
    req = request({"payment_id": payment_id})
    monkeypatch.setattr(cli, "load_registry", lambda: registry)
    stdout, stderr = io.StringIO(), io.StringIO()
    assert cli.main(["read", capability_id, "--request", "-"], stdin=io.StringIO(json.dumps(req)),
                    stdout=stdout, stderr=stderr, port_factory=lambda *args: Port()) == 0, stdout.getvalue()
    registry.validate_instance(f"schemas/v1/{capability_id}.response.schema.json", json.loads(stdout.getvalue()))
    raw = {field: [value, "Native"] if field.endswith("_id") and value is not None else False if value is None else value for field, value in item.items()}
    if capability_id == contracts.DUPLICATES_ID:
        raw.update(date=date(2026, 10, 1), amount=17.5)
    assert reads._normalize_payment_processing(capability_id, [raw], 7) == [item]
    assert not contracts.valid_read_item(capability_id, {**item, "company_id": True}, 7)
    if capability_id in contracts.LIST_IDS:
        item = {**item, "payment_id": 72}
        with pytest.raises(core_object_reads.CoreObjectReadError):
            core_object_reads.read_core_object(capability_id, Port(), req)


@pytest.mark.parametrize("capability_id", PARAMETERS)
@pytest.mark.parametrize("denial", ["group", "acl"])
def test_runtime_denial_precedes_mutation(capability_id, denial, monkeypatch):
    env = Env()
    if denial == "group": env.denied_group = runtime._GROUPS[capability_id]
    else: env.denied_access = ("account.payment", "write")
    monkeypatch.setattr(runtime, "_dispatch_allowed", lambda *args: pytest.fail("denied mutation dispatched"))
    payload = _payload(capability_id, PARAMETERS[capability_id])
    payload["idempotency_key"] = contracts.idempotency_key(capability_id, payload["parameters"], 7)
    page = runtime.dispatch(env, payload, 7, failure_type=Failure)
    assert not page["access_allowed"] and page["result"] is None


@pytest.mark.parametrize(("capability_id", "changes"), [
    ("payment.bank_account.assign", {"partner_bank_id": True}),
    ("payment.bank_account.assign", {"partner_bank_id": 0}),
    ("payment.destination_account.assign", {"account_id": None}),
    ("payment.destination_account.assign", {"account_id": False}),
    ("payment.sent_status.set", {"sent": "true"}),
    ("payment.sent_status.set", {"sent": 1}),
    ("payment.validate", {"state": "paid"}),
    ("payment.reject", {"sudo": True}),
    ("payment.reject", {"payment_id": []}),
])
def test_invalid_write_parameters_are_closed(capability_id, changes, registry):
    params = {**PARAMETERS[capability_id], **changes}
    with pytest.raises(ValueError): contracts.normalize_parameters(capability_id, params)
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(f"schemas/v1/{capability_id}.request.schema.json", request(params))


def payment(monkeypatch, **changes):
    calls = []
    record = SimpleNamespace(id=31, state="in_process", payment_method_code="manual", move_id=False,
        is_sent=False, require_partner_bank_account=False, partner_bank_id=False,
        available_partner_bank_ids=SimpleNamespace(ids=[41]), destination_account_id=False, partner_type="supplier",
        invalidate_recordset=lambda: None, **changes)
    def write(values):
        calls.append(values)
        for field, value in values.items():
            setattr(record, field, SimpleNamespace(id=value) if field.endswith("_id") and value else value)
    record.write = write
    record.mark_as_sent = lambda: write({"is_sent": True})
    record.unmark_as_sent = lambda: write({"is_sent": False})
    record.action_validate = lambda: write({"state": "paid"})
    record.action_reject = lambda: write({"state": "rejected"})
    record.action_draft = lambda: write({"state": "draft"})
    monkeypatch.setattr(runtime, "_search_one", lambda *args: record)
    monkeypatch.setattr(runtime, "_payment_result", lambda *args, **kwargs: {**result("payment.bank_account.assign", {"payment_id":31}), "state": record.state})
    return record, calls


@pytest.mark.parametrize("capability_id", ["payment.bank_account.assign", "payment.sent_status.set", "payment.validate", "payment.reject"])
def test_native_actions_and_immediate_replay(capability_id, monkeypatch):
    record, calls = payment(monkeypatch)
    if capability_id == "payment.reject": record.is_sent = True
    monkeypatch.setattr(runtime, "_ensure_ids", lambda *args: None)
    for expected in (False, True):
        assert runtime._write_payment_processing(None, capability_id, PARAMETERS[capability_id], 7, Failure)[1] is expected
    assert len(calls) == 1


def test_native_unmark_and_clear_bank(monkeypatch):
    record, calls = payment(monkeypatch)
    record.is_sent, record.partner_bank_id = True, SimpleNamespace(id=41)
    runtime._write_payment_processing(None, "payment.sent_status.set", {"payment_id":31, "sent":False}, 7, Failure)
    runtime._write_payment_processing(None, "payment.bank_account.assign", {"payment_id":31, "partner_bank_id":None}, 7, Failure)
    assert calls == [{"is_sent":False}, {"partner_bank_id":False}]


def test_native_draft_destination_assignment_matches_partner_type(monkeypatch):
    record, calls = payment(monkeypatch)
    record.state = "draft"
    def search(env, model, domain, company_id, failure_type):
        if model == "account.payment": return record
        assert model == "account.account" and company_id == 7
        assert ("id", "=", 11) in domain and ("account_type", "=", "liability_payable") in domain
        assert ("reconcile", "=", True) in domain and ("company_ids", "in", [7]) in domain
        return SimpleNamespace(id=11)
    monkeypatch.setattr(runtime, "_search_one", search)
    for expected in (False, True):
        assert runtime._write_payment_processing(None, "payment.destination_account.assign", PARAMETERS["payment.destination_account.assign"], 7, Failure)[1] is expected
    assert calls == [{"destination_account_id":11}]


@pytest.mark.parametrize("required", [False, True])
def test_native_bank_eligibility_and_required_bank_are_not_bypassed(required, monkeypatch):
    record, calls = payment(monkeypatch)
    record.require_partner_bank_account = required
    record.available_partner_bank_ids = SimpleNamespace(ids=[])
    monkeypatch.setattr(runtime, "_ensure_ids", lambda *args: None)
    params = {"payment_id":31, "partner_bank_id":None if required else 41}
    with pytest.raises(Failure) as exc:
        runtime._write_payment_processing(None, "payment.bank_account.assign", params, 7, Failure)
    assert exc.value.code == "business_rule_error" and not calls


@pytest.mark.parametrize(("capability_id", "changes"), [
    ("payment.destination_account.assign", {"state":"paid"}),
    ("payment.sent_status.set", {"state":"draft"}),
    ("payment.sent_status.set", {"payment_method_code":"electronic"}),
    ("payment.validate", {"state":"draft"}),
    ("payment.validate", {"move_id":SimpleNamespace(id=99)}),
    ("payment.reject", {"state":"draft"}),
    ("payment.reject", {"is_sent":False}),
])
def test_native_state_boundaries(capability_id, changes, monkeypatch):
    record, calls = payment(monkeypatch)
    for field, value in changes.items(): setattr(record, field, value)
    with pytest.raises(Failure) as exc:
        runtime._write_payment_processing(None, capability_id, PARAMETERS[capability_id], 7, Failure)
    assert exc.value.code == "state_conflict" and not calls


def test_native_rejected_payment_can_use_existing_reset(monkeypatch):
    record, calls = payment(monkeypatch)
    record.state = "rejected"
    runtime._reset_payment_to_draft(None, {"payment_id":31}, 7, Failure)
    assert record.state == "draft" and calls == [{"state":"draft"}]


@pytest.mark.parametrize("native_invoice_state", ["in_payment", "paid"])
def test_existing_create_allows_native_accountant_no_entry_configuration(native_invoice_state, monkeypatch):
    env = {"account.move": SimpleNamespace(_get_invoice_in_payment_state=lambda: native_invoice_state)}
    monkeypatch.setattr(runtime, "_ensure_ids", lambda *args: None)
    monkeypatch.setattr(runtime, "_search_one", lambda *args: SimpleNamespace(payment_account_id=False))
    values = {"partner_id":21, "currency_id":1, "journal_id":15, "payment_method_line_id":16, "payment_type":"outbound"}
    if native_invoice_state == "in_payment":
        runtime._validate_payment_configuration(env, values, 7, Failure)
    else:
        with pytest.raises(Failure) as exc:
            runtime._validate_payment_configuration(env, values, 7, Failure)
        assert exc.value.code == "configuration_missing"


@pytest.mark.parametrize(("companies", "reconcile"), [([8], True), ([7], False)])
def test_no_entry_support_does_not_allow_an_invalid_existing_outstanding_account(companies, reconcile, monkeypatch):
    account = SimpleNamespace(company_ids=SimpleNamespace(ids=companies), reconcile=reconcile)
    monkeypatch.setattr(runtime, "_ensure_ids", lambda *args: None)
    monkeypatch.setattr(runtime, "_search_one", lambda *args: SimpleNamespace(payment_account_id=account))
    values = {"partner_id":21, "currency_id":1, "journal_id":15, "payment_method_line_id":16, "payment_type":"outbound"}
    with pytest.raises(Failure) as exc:
        runtime._validate_payment_configuration({}, values, 7, Failure)
    assert exc.value.code == "configuration_missing"
