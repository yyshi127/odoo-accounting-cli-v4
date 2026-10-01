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
from odoo_accounting_cli_v4 import reconciliation_processing_contracts as contracts
from odoo_accounting_cli_v4.bridge import core_object_reads_runtime as reads
from odoo_accounting_cli_v4.bridge import core_writes_runtime as runtime
from odoo_accounting_cli_v4.capabilities import core_object_reads, core_writes
from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry

LINE = {"sequence": -10, "account_id": 11, "partner_id": None, "label": "FEE",
        "amount_type": "fixed", "amount_string": "-7.5", "tax_ids": []}
PARAMETERS = {
    "reconciliation.model.duplicate": {"reconciliation_model_id": 31, "name": "COPY"},
    "reconciliation.model.delete": {"reconciliation_model_id": 31},
    "reconciliation.model.line.create": {"reconciliation_model_id": 31, "line": LINE},
    "reconciliation.model.line.update": {"reconciliation_model_id": 31, "line_id": 41, "changes": {"amount_string": "-8.5"}},
    "reconciliation.model.line.delete": {"reconciliation_model_id": 31, "line_id": 41},
    "reconciliation.model.lines.resequence": {"reconciliation_model_id": 31, "line_ids": [42, 41]},
    "reconciliation.model.activity_type.assign": {"reconciliation_model_id": 31, "activity_type_id": 51},
}


def result(capability_id, parameters):
    duplicate = capability_id.endswith("duplicate")
    child = capability_id.startswith("reconciliation.model.line.")
    deleted = capability_id == "reconciliation.model.delete"
    source = parameters["reconciliation_model_id"] if duplicate else parameters.get("line_id", 41) if child else None
    return {"model": "account.reconcile.model", "id": 61 if duplicate else parameters["reconciliation_model_id"],
            "name": "COPY" if duplicate else "RULE", "state": "deleted" if deleted else "active", "company_id": 7,
            "move_type": None, "source_id": source, "line_ids": [] if deleted else [42] if duplicate or capability_id.endswith("line.delete") else [41, 42],
            "partial_reconcile_ids": [], "full_reconcile_id": None, "reconciled": False}


def read_item(capability_id=contracts.GET_ID, record_id=31):
    if capability_id == contracts.GET_ID:
        return {"id": record_id, "name": None, "company_id": 7, "active": True, "trigger": "manual",
                "can_be_proposed": False, "mapped_partner_id": None, "next_activity_type_id": None, "line_ids": [41, 42]}
    return {"id": record_id, "name": None, "company_id": 7, "reconcile_model_id": 71, "move_id": 81,
            "account_id": 11, "partner_id": None, "currency_id": 1, "date": "2026-10-01",
            "debit": "17.5", "credit": "0", "balance": "17.5", "amount_currency": "17.5"}


@pytest.fixture(scope="module")
def registry():
    return load_registry()


@pytest.mark.parametrize("capability_id", PARAMETERS)
def test_fixed_public_cli_schemas_and_result_ownership(capability_id, registry, monkeypatch):
    req = request(PARAMETERS[capability_id])
    registry.validate_instance(f"schemas/v1/{capability_id}.request.schema.json", req)
    params = core_writes.validate_core_write_request(capability_id, req)[2]
    assert runtime._valid_parameters(capability_id, params, 7)
    key = contracts.idempotency_key(capability_id, params, 7)
    assert key == core_writes._expected_idempotency_key(capability_id, params, 7) == runtime._deterministic_key(capability_id, params, 7)
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
                    stdin=io.StringIO(json.dumps(req)), stdout=stdout, stderr=stderr, port_factory=lambda *args: Port()) == 0, stdout.getvalue()
    assert not stderr.getvalue()
    registry.validate_instance(f"schemas/v1/{capability_id}.response.schema.json", json.loads(stdout.getvalue()))
    invalid_id = params["reconciliation_model_id"] if capability_id.endswith("duplicate") else expected["id"]+1
    for field, value in (("id", invalid_id), ("company_id", 8), ("model", "account.move"), ("source_id", 991)):
        with pytest.raises(core_writes.CoreWriteError):
            core_writes._validate_result(capability_id, params, {**expected, field: value}, company_id=7, idempotent_replay=False)


@pytest.mark.parametrize("capability_id", sorted(contracts.READ_IDS))
def test_fixed_reads_cli_normalization_and_parent_scope(capability_id, registry, monkeypatch):
    item = read_item(capability_id)
    parent = 31 if capability_id == contracts.GET_ID else 71
    class Port:
        user_id = 42
        def read(self, **payload):
            assert payload["parameters"]["reconciliation_model_id"] == parent
            return {"user_id": 42, "company_visible": True, "module_installed": True, "access_allowed": True, "cursor_found": True, "items": [item]}
    req = request({"reconciliation_model_id": parent})
    monkeypatch.setattr(cli, "load_registry", lambda: registry)
    stdout, stderr = io.StringIO(), io.StringIO()
    assert cli.main(["read", capability_id, "--request", "-"], stdin=io.StringIO(json.dumps(req)),
                    stdout=stdout, stderr=stderr, port_factory=lambda *args: Port()) == 0, stdout.getvalue()
    registry.validate_instance(f"schemas/v1/{capability_id}.response.schema.json", json.loads(stdout.getvalue()))
    raw = {field: [value, "Native"] if field.endswith("_id") and value is not None else False if value is None else value for field, value in item.items()}
    if capability_id == contracts.LIST_ID:
        raw.update(date=date(2026,10,1), debit=17.5, credit=0, balance=17.5, amount_currency=17.5)
    assert reads._normalize_reconciliation_processing(capability_id, [raw], 7) == [item]
    assert not contracts.valid_read_item(capability_id, {**item, "company_id": True}, 7)
    if capability_id == contracts.LIST_ID:
        item = {**item, "reconcile_model_id": 72}
        with pytest.raises(core_object_reads.CoreObjectReadError):
            core_object_reads.read_core_object(capability_id, Port(), req)


def test_missing_processing_settings_get_returns_typed_error(registry, monkeypatch):
    class Port:
        user_id = 42
        def read(self, **payload):
            return {"user_id": 42, "company_visible": True, "module_installed": True,
                    "access_allowed": True, "cursor_found": True, "items": []}
    monkeypatch.setattr(cli, "load_registry", lambda: registry)
    stdout, stderr = io.StringIO(), io.StringIO()
    capability_id = contracts.GET_ID
    code = cli.main(["read", capability_id, "--request", "-"],
                    stdin=io.StringIO(json.dumps(request({"reconciliation_model_id": 31}))),
                    stdout=stdout, stderr=stderr, port_factory=lambda *args: Port())
    response = json.loads(stdout.getvalue())
    assert code == 4 and not stderr.getvalue() and response["success"] is False
    assert response["data"] is None and response["error"]["code"] == "record_not_found"
    registry.validate_instance(f"schemas/v1/{capability_id}.response.schema.json", response)


@pytest.mark.parametrize("capability_id", PARAMETERS)
@pytest.mark.parametrize("denial", ["group", "acl"])
def test_access_denials_precede_native_mutation(capability_id, denial, monkeypatch):
    env = Env()
    if denial == "group":
        env.denied_group = runtime._GROUPS[capability_id]
    else:
        env.denied_access = next(pair for pair in sorted(runtime._ACCESS[capability_id]) if pair[1] != "read")
    monkeypatch.setattr(runtime, "_dispatch_allowed", lambda *args: pytest.fail("denied native mutation dispatched"))
    payload = _payload(capability_id, PARAMETERS[capability_id])
    payload["idempotency_key"] = contracts.idempotency_key(capability_id, payload["parameters"], 7)
    page = runtime.dispatch(env, payload, 7, failure_type=Failure)
    assert not page["access_allowed"] and page["result"] is None


@pytest.mark.parametrize(("capability_id", "changes"), [
    ("reconciliation.model.delete", {"sudo": True}),
    ("reconciliation.model.delete", {"reconciliation_model_id": False}),
    ("reconciliation.model.duplicate", {"name": None}),
    ("reconciliation.model.activity_type.assign", {"activity_type_id": 0}),
    ("reconciliation.model.line.update", {"changes": {"model_id": 32}}),
    ("reconciliation.model.line.update", {"changes": {}}),
    ("reconciliation.model.line.create", {"line": {**LINE, "amount_string": "0"}}),
    ("reconciliation.model.line.create", {"line": {**LINE, "amount_string": 7.5}}),
    ("reconciliation.model.line.create", {"line": {**LINE, "sequence": 2147483648}}),
    ("reconciliation.model.lines.resequence", {"line_ids": [41, 41]}),
])
def test_closed_invalid_parameters(capability_id, changes, registry):
    params = {**PARAMETERS[capability_id], **changes}
    with pytest.raises(ValueError): contracts.normalize_parameters(capability_id, params)
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(f"schemas/v1/{capability_id}.request.schema.json", request(params))


@pytest.mark.parametrize("amount_type", ["fixed", "percentage", "percentage_st_line"])
@pytest.mark.parametrize("amount", ["-125", "125", "0.12500"])
def test_new_lines_preserve_native_nonzero_numeric_ranges(amount_type, amount, registry):
    params = {"reconciliation_model_id":31, "line":{**LINE,"amount_type":amount_type,"amount_string":amount}}
    assert contracts.normalize_parameters("reconciliation.model.line.create", params) == params
    registry.validate_instance("schemas/v1/reconciliation.model.line.create.request.schema.json", request(params))


def test_tax_and_analytic_set_normalization_does_not_mutate_input():
    values = {**LINE, "tax_ids":[13,12], "analytic_distribution":[{"analytic_account_ids":[17,16],"percentage":"30.00"}]}
    original = deepcopy(values)
    normalized = contracts.line_values(values)
    assert values == original
    assert normalized["tax_ids"] == [12,13]
    assert normalized["analytic_distribution"] == [{"analytic_account_ids":[16,17],"percentage":"30"}]
    assert contracts.line_values({"analytic_distribution":[]}, partial=True) == {"analytic_distribution":[]}


class Rows(list):
    @property
    def ids(self): return [row.id for row in self]
    def __getattr__(self, field):
        if len(self) == 1: return getattr(self[0], field)
        raise AttributeError(field)
    def sorted(self, key): return Rows(sorted(self,key=key))
    def filtered(self, predicate): return Rows(row for row in self if predicate(row))


def rule_fixture(monkeypatch):
    calls = []
    rule = SimpleNamespace(id=31, company_id=SimpleNamespace(id=7), name="RULE", active=True,
                           line_ids=Rows(), next_activity_type_id=False, invalidate_recordset=lambda:None)
    def make_line(record_id, values):
        row = SimpleNamespace(id=record_id, model_id=rule, company_id=rule.company_id, **values)
        row.tax_ids = SimpleNamespace(ids=values["tax_ids"])
        row.account_id = SimpleNamespace(id=values["account_id"]) if values["account_id"] else False
        row.partner_id = SimpleNamespace(id=values["partner_id"]) if values["partner_id"] else False
        row.analytic_distribution = {}
        row.invalidate_recordset = lambda:None
        def write(values):
            calls.append((record_id,dict(values)))
            for field,value in values.items():
                if field=="analytic_distribution": value=value or {}
                setattr(row,field,value)
        row.write=write
        row.unlink=lambda:rule.line_ids.remove(row)
        rule.line_ids.append(row)
        return row
    first=make_line(41,LINE)
    second=make_line(42,{**LINE,"sequence":0,"label":"SECOND"})
    def write(values):
        calls.append((31,dict(values)))
        for field,value in values.items():
            setattr(rule,field,SimpleNamespace(id=value) if field.endswith("_id") and value else value)
    rule.write=write
    monkeypatch.setattr(runtime,"_reconciliation_model",lambda *args:rule)
    monkeypatch.setattr(runtime,"_search_one",lambda *args:first)
    monkeypatch.setattr(runtime,"_validate_reconciliation_line_references",lambda *args:None)
    monkeypatch.setattr(runtime,"_ensure_ids",lambda *args:None)
    monkeypatch.setattr(runtime,"_reconciliation_model_result",lambda model,company:{**result("reconciliation.model.line.update",PARAMETERS["reconciliation.model.line.update"]),"id":model.id,"name":model.name,"source_id":None,"line_ids":sorted(model.line_ids.ids)})
    return rule,first,second,calls


@pytest.mark.parametrize("capability_id", ["reconciliation.model.line.update","reconciliation.model.lines.resequence","reconciliation.model.activity_type.assign"])
def test_native_patch_order_and_activity_serial_replay(capability_id,monkeypatch):
    rule,first,second,calls=rule_fixture(monkeypatch)
    params=PARAMETERS[capability_id]
    initial_second=deepcopy(runtime._normalized_reconciliation_line(second))
    _,replay=runtime._write_reconciliation_processing(None,capability_id,params,7,Failure)
    assert replay is False
    _,replay=runtime._write_reconciliation_processing(None,capability_id,params,7,Failure)
    assert replay is True
    if capability_id.endswith('line.update'):
        assert first.amount_string=="-8.5" and runtime._normalized_reconciliation_line(second)==initial_second
    elif capability_id.endswith('resequence'):
        assert rule.line_ids.sorted(lambda row:(row.sequence,row.id)).ids == [42,41]
        assert len(calls)==2
    else:
        assert rule.next_activity_type_id.id==51 and calls==[(31,{"next_activity_type_id":51})]


def test_resequence_rejects_incomplete_or_other_parent_lines_before_writes(monkeypatch):
    _,_,_,calls=rule_fixture(monkeypatch)
    with pytest.raises(Failure) as exc:
        runtime._write_reconciliation_processing(None,"reconciliation.model.lines.resequence",{"reconciliation_model_id":31,"line_ids":[41]},7,Failure)
    assert exc.value.code=="business_rule_error" and not calls


def test_delete_one_line_preserves_parent_and_other_ids(monkeypatch):
    rule,_,second,_=rule_fixture(monkeypatch)
    value,replay=runtime._write_reconciliation_processing(None,"reconciliation.model.line.delete",PARAMETERS["reconciliation.model.line.delete"],7,Failure)
    assert value["source_id"]==41 and value["line_ids"]==[42] and replay is False
    assert rule.line_ids==[second]


def test_native_regex_and_type_change_validates_merged_payload_before_writing(monkeypatch):
    _,first,_,calls=rule_fixture(monkeypatch)
    first.amount_type="regex"
    first.amount_string=r"FEE: ([0-9]+)"
    with pytest.raises(Failure) as exc:
        runtime._write_reconciliation_processing(None,"reconciliation.model.line.update",{"reconciliation_model_id":31,"line_id":41,"changes":{"amount_type":"fixed"}},7,Failure)
    assert exc.value.code=="business_rule_error" and not calls


@pytest.mark.parametrize("ambiguous", [False, True])
def test_line_create_matches_one_full_payload_and_rejects_ambiguity(ambiguous,monkeypatch):
    rule,first,second,calls=rule_fixture(monkeypatch)
    if ambiguous:
        second.__dict__.update({**first.__dict__,"id":42})
        with pytest.raises(Failure) as exc:
            runtime._write_reconciliation_processing(None,"reconciliation.model.line.create",PARAMETERS["reconciliation.model.line.create"],7,Failure)
        assert exc.value.code=="idempotency_conflict" and not calls
    else:
        value,replay=runtime._write_reconciliation_processing(None,"reconciliation.model.line.create",PARAMETERS["reconciliation.model.line.create"],7,Failure)
        assert replay is True and value["source_id"]==41 and rule.line_ids.ids==[41,42] and not calls


def test_native_copy_preserves_configuration_and_new_child_ids_then_replays(monkeypatch):
    rule,_,_,calls=rule_fixture(monkeypatch)
    rule.sequence=10
    rule.trigger="manual"
    rule.match_journal_ids=SimpleNamespace(ids=[21])
    rule.match_partner_ids=SimpleNamespace(ids=[])
    rule.match_amount=False
    rule.match_label=False
    candidates=Rows()
    def copy(defaults):
        nonlocal candidates
        calls.append(("copy",defaults))
        duplicate=SimpleNamespace(**{**rule.__dict__,"id":61,"name":defaults["name"]})
        duplicate.line_ids=Rows(SimpleNamespace(**{**row.__dict__,"id":row.id+100,"model_id":duplicate}) for row in rule.line_ids)
        candidates=Rows([duplicate])
        return duplicate
    rule.copy=copy
    monkeypatch.setattr(runtime,"_scoped",lambda *args:SimpleNamespace(search=lambda *args,**kwargs:candidates))
    for expected_replay in (False,True):
        value,replay=runtime._write_reconciliation_processing(None,"reconciliation.model.duplicate",PARAMETERS["reconciliation.model.duplicate"],7,Failure)
        assert replay is expected_replay and value["source_id"]==31 and value["id"]==61
    assert calls==[("copy",{"name":"COPY"})] and candidates[0].line_ids.ids==[141,142]
    candidates[0].line_ids[0].amount_string="-9"
    with pytest.raises(Failure) as exc:
        runtime._write_reconciliation_processing(None,"reconciliation.model.duplicate",PARAMETERS["reconciliation.model.duplicate"],7,Failure)
    assert exc.value.code=="idempotency_conflict" and len(calls)==1


def test_native_model_delete_returns_no_live_children_and_is_not_a_fake_replay(monkeypatch):
    rule,_,_,calls=rule_fixture(monkeypatch)
    rule.unlink=lambda:calls.append(("unlink",31))
    monkeypatch.setattr(runtime,"_scoped",lambda *args:SimpleNamespace(search_count=lambda *args,**kwargs:0))
    value,replay=runtime._write_reconciliation_processing(None,"reconciliation.model.delete",PARAMETERS["reconciliation.model.delete"],7,Failure)
    assert value["state"]=="deleted" and value["line_ids"]==[] and replay is False and calls==[("unlink",31)]


@pytest.mark.parametrize("active", [False,True])
def test_new_line_result_uses_the_existing_native_configuration_states(active):
    model=SimpleNamespace(id=31,name="RULE",active=active,line_ids=SimpleNamespace(ids=[41]))
    value=runtime._reconciliation_model_result(model,7)
    value["source_id"]=41
    assert value["state"]==("active" if active else "archived")
    assert core_writes._validate_result("reconciliation.model.line.update",PARAMETERS["reconciliation.model.line.update"],value,
                                       company_id=7,idempotent_replay=False)==value
