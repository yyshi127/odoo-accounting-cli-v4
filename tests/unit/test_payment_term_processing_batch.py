from __future__ import annotations

import io
import json
from contextlib import contextmanager
from copy import deepcopy
from datetime import date
from types import SimpleNamespace

import pytest
from test_core_writes_runtime import Env, Failure, _payload
from test_fiscal_mapping_writes import request
from test_reconciliation_processing_batch import Rows as BaseRows

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4 import payment_term_processing_contracts as contracts
from odoo_accounting_cli_v4.bridge import core_object_reads_runtime as reads
from odoo_accounting_cli_v4.bridge import core_writes_runtime as runtime
from odoo_accounting_cli_v4.capabilities import core_object_reads, core_writes
from odoo_accounting_cli_v4.registry import load_registry

LINE = {"value": "fixed", "value_amount": "-7.5", "delay_type": "days_after", "nb_days": -10, "days_next_month": 10}
PARAMETERS = {
    "payment_term.duplicate": {"payment_term_id": 31, "name": "COPY"},
    "payment_term.delete": {"payment_term_id": 31},
    "payment_term.line.create": {"payment_term_id": 31, "line": LINE},
    "payment_term.line.update": {"payment_term_id": 31, "line_id": 41, "changes": {"nb_days": -11}},
    "payment_term.line.delete": {"payment_term_id": 31, "line_id": 41},
    "payment_term.lines.update": {"payment_term_id": 31, "lines": [
        {"line_id": 42, "changes": {"value_amount": "75"}}, {"line_id": 41, "changes": {"value_amount": "25"}},
    ]},
}


def result(capability_id, parameters):
    duplicate = capability_id.endswith("duplicate")
    deleted = capability_id == "payment_term.delete"
    child = capability_id.startswith("payment_term.line.")
    return {"model": "account.payment.term", "id": 61 if duplicate else parameters["payment_term_id"],
            "name": "COPY" if duplicate else "TERM", "state": "deleted" if deleted else "active", "company_id": 7,
            "move_type": None, "source_id": parameters["payment_term_id"] if duplicate else parameters.get("line_id", 41) if child else None,
            "line_ids": [] if deleted else [43, 44] if duplicate else [42] if capability_id.endswith("line.delete") else [41, 42],
            "partial_reconcile_ids": [], "full_reconcile_id": None, "reconciled": False}


def read_item(capability_id=contracts.GET_ID, record_id=31):
    if capability_id == contracts.GET_ID:
        return {"id": record_id, "company_id": 7, "move_type": "out_invoice", "state": "draft", "currency_id": 6,
                "company_currency_id": 6, "payment_term_id": None,
                "lines": [{"date_maturity": "2026-10-01", "discount_date": None, "balance": "100", "amount_currency": "100",
                           "discount_balance": "0", "discount_amount_currency": "0"}]}
    return {"id": record_id, "company_id": 7, "move_type": "out_invoice", "state": "posted", "name": None,
            "invoice_payment_term_id": 71, "partner_id": None, "currency_id": 6, "date": "2026-10-01",
            "invoice_date": None, "amount_total": "100", "amount_residual": "100"}


@pytest.fixture(scope="module")
def registry():
    return load_registry()


@pytest.mark.parametrize("capability_id", PARAMETERS)
def test_closed_public_cli_schemas_hashes_and_result_scope(capability_id, registry, monkeypatch):
    req = request(PARAMETERS[capability_id])
    registry.validate_instance(f"schemas/v1/{capability_id}.request.schema.json", req)
    params = core_writes.validate_core_write_request(capability_id, req)[2]
    key = contracts.idempotency_key(capability_id, params, 7)
    assert runtime._valid_parameters(capability_id, params, 7)
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
                    stdin=io.StringIO(json.dumps(req)), stdout=stdout, stderr=stderr, port_factory=lambda *args: Port()) == 0
    assert not stderr.getvalue()
    registry.validate_instance(f"schemas/v1/{capability_id}.response.schema.json", json.loads(stdout.getvalue()))
    invalid_id = params["payment_term_id"] if capability_id.endswith("duplicate") else expected["id"]+1
    for field, value in (("id", invalid_id), ("company_id", 8), ("model", "account.move"), ("source_id", 999)):
        with pytest.raises(core_writes.CoreWriteError):
            core_writes._validate_result(capability_id, params, {**expected, field: value}, company_id=7, idempotent_replay=False)


@pytest.mark.parametrize("capability_id", sorted(contracts.READ_IDS))
def test_closed_reads_and_parent_scope(capability_id, registry, monkeypatch):
    item = read_item(capability_id)
    params = {"invoice_id": 31} if capability_id == contracts.GET_ID else {"payment_term_id": 71}
    class Port:
        user_id = 42
        def read(self, **payload):
            assert all(payload["parameters"][field] == value for field, value in params.items())
            return {"user_id": 42, "company_visible": True, "module_installed": True, "access_allowed": True, "cursor_found": True, "items": [item]}
    monkeypatch.setattr(cli, "load_registry", lambda: registry)
    stdout, stderr = io.StringIO(), io.StringIO()
    assert cli.main(["read", capability_id, "--request", "-"], stdin=io.StringIO(json.dumps(request(params))),
                    stdout=stdout, stderr=stderr, port_factory=lambda *args: Port()) == 0, stdout.getvalue()
    registry.validate_instance(f"schemas/v1/{capability_id}.response.schema.json", json.loads(stdout.getvalue()))
    assert not contracts.valid_read_item(capability_id, {**item, "company_id": True}, 7)
    if capability_id == contracts.LIST_ID:
        raw = {field: [value, "Native"] if field.endswith("_id") and value is not None else False if value is None else value for field, value in item.items()}
        raw.update(date=date(2026,10,1), amount_total=100.0, amount_residual=100.0)
        assert reads._normalize_payment_term_processing(capability_id, [raw], 7) == [item]
        item = {**item, "invoice_payment_term_id": 72}
        with pytest.raises(core_object_reads.CoreObjectReadError):
            core_object_reads.read_core_object(capability_id, Port(), request(params))


@pytest.mark.parametrize("capability_id", PARAMETERS)
@pytest.mark.parametrize("denial", ["group", "acl"])
def test_access_denials_precede_native_savepoint_and_mutation(capability_id, denial, monkeypatch):
    env = Env()
    if denial == "group": env.denied_group = runtime._GROUPS[capability_id]
    else: env.denied_access = next(pair for pair in sorted(runtime._ACCESS[capability_id]) if pair[1] != "read")
    monkeypatch.setattr(runtime, "_dispatch_allowed", lambda *args: pytest.fail("denied mutation dispatched"))
    payload = _payload(capability_id, contracts.normalize_parameters(capability_id, PARAMETERS[capability_id]))
    payload["idempotency_key"] = contracts.idempotency_key(capability_id, payload["parameters"], 7)
    assert runtime.dispatch(env, payload, 7, failure_type=Failure)["access_allowed"] is False


@pytest.mark.parametrize("changes", [{"sudo": True}, {"payment_term_id": False}, {"line": {}},
    {"line": {**LINE, "value": []}}, {"line": {**LINE, "nb_days": True}},
    {"line": {**LINE, "days_next_month": 32}}, {"line": {**LINE, "delay_type": {}}},
    {"line": {**LINE, "value_amount": "NaN"}}, {"line": {**LINE, "value": "percent", "value_amount": "101"}}])
def test_invalid_closed_line_inputs(changes):
    with pytest.raises(ValueError): contracts.normalize_parameters("payment_term.line.create", {**PARAMETERS["payment_term.line.create"], **changes})


@pytest.mark.parametrize("amount", ["0", "100", "30.00"])
@pytest.mark.parametrize("delay", sorted(contracts.DELAY_TYPES))
def test_native_percentage_and_delay_shapes(amount, delay):
    values = {**LINE, "value": "percent", "value_amount": amount, "delay_type": delay}
    assert contracts.line_values(values) == values


def test_atomic_parameters_sort_ids_without_mutating_input():
    params = deepcopy(PARAMETERS["payment_term.lines.update"])
    before = deepcopy(params)
    normalized = contracts.normalize_parameters("payment_term.lines.update", params)
    assert params == before and [entry["line_id"] for entry in normalized["lines"]] == [41,42]
    for lines in ([params["lines"][0]], [params["lines"][0]]*2):
        with pytest.raises(ValueError): contracts.normalize_parameters("payment_term.lines.update", {**params, "lines": lines})


class Rows(BaseRows):
    def sorted(self, key):
        return Rows(sorted(self, key=(lambda row: getattr(row,key)) if isinstance(key,str) else key))


class ValidationError(ValueError):
    pass


def term_fixture(monkeypatch):
    calls = []
    term = SimpleNamespace(id=31, company_id=SimpleNamespace(id=7), name="TERM", active=True, sequence=10,
        note="<p>Terms</p>", display_on_invoice=True, early_discount=False, discount_percentage=2.0,
        discount_days=10, early_pay_discount_computation="excluded", line_ids=Rows(), invalidate_recordset=lambda:None)
    def make_line(row_id, values):
        row = SimpleNamespace(id=row_id, payment_id=term, **values)
        row.value_amount=float(row.value_amount)
        row.days_next_month=str(row.days_next_month)
        return row
    term.line_ids.extend(make_line(row_id,{**LINE,"value":"percent","value_amount":str(amount),"nb_days":days})
                         for row_id,amount,days in ((41,40,10),(42,60,30)))
    def write(values):
        calls.append(deepcopy(values))
        for command in values.get("line_ids",[]):
            op,row_id,data = command
            if op==0: term.line_ids.append(make_line(43,data))
            elif op==2: term.line_ids[:] = [row for row in term.line_ids if row.id != row_id]
            else: vars(next(row for row in term.line_ids if row.id==row_id)).update(data)
        if sum(row.value_amount for row in term.line_ids if row.value=="percent") != 100:
            raise ValidationError("Native percentage total constraint")
    term.write=write
    @contextmanager
    def savepoint():
        original=Rows(term.line_ids)
        snapshot={row.id:vars(row).copy() for row in original}
        try: yield
        except BaseException:
            term.line_ids[:]=original
            for row in original: vars(row).update(snapshot[row.id])
            raise
    env=SimpleNamespace(cr=SimpleNamespace(savepoint=savepoint))
    def search_one(env, model, domain, company_id, failure_type):
        if model=="account.payment.term": return term
        row_id=next(value for field,op,value in domain if field=="id")
        matches=Rows(row for row in term.line_ids if row.id==row_id)
        if not matches: raise Failure("record_not_found","Missing native child",exit_code=4)
        return matches
    monkeypatch.setattr(runtime,"_search_one",search_one)
    return env,term,calls


def test_atomic_native_parent_write_preserves_ids_and_replays(monkeypatch):
    env,term,calls=term_fixture(monkeypatch)
    params=contracts.normalize_parameters("payment_term.lines.update",PARAMETERS["payment_term.lines.update"])
    value,replay=runtime._write_payment_term_processing(env,"payment_term.lines.update",params,7,Failure)
    assert value["line_ids"]==[41,42] and value["source_id"] is None and replay is False
    assert [row.value_amount for row in term.line_ids]==[25,75] and len(calls)==1
    assert runtime._write_payment_term_processing(env,"payment_term.lines.update",params,7,Failure)[1] is True
    assert len(calls)==1


@pytest.mark.parametrize("capability_id", ["payment_term.line.update","payment_term.line.delete","payment_term.lines.update"])
def test_native_constraint_failure_uses_savepoint_and_restores_all_lines(capability_id,monkeypatch):
    env,term,_=term_fixture(monkeypatch)
    snapshot=[runtime._normalized_payment_term_line(row) for row in term.line_ids]
    params={**PARAMETERS[capability_id]}
    if capability_id.endswith("line.update"): params["changes"]={"value_amount":"30"}
    if capability_id.endswith("lines.update"): params["lines"]=[{"line_id":41,"changes":{"value_amount":"30"}},{"line_id":42,"changes":{"value_amount":"60"}}]
    with pytest.raises(ValidationError): runtime._write_payment_term_processing(env,capability_id,params,7,Failure)
    assert [runtime._normalized_payment_term_line(row) for row in term.line_ids]==snapshot and term.line_ids.ids==[41,42]


def test_single_update_validates_the_merged_native_type(monkeypatch):
    env,term,calls=term_fixture(monkeypatch)
    term.line_ids[0].value="fixed"
    term.line_ids[0].value_amount=-7.5
    with pytest.raises(Failure) as exc:
        runtime._write_payment_term_processing(env,"payment_term.line.update",{"payment_term_id":31,"line_id":41,"changes":{"value":"percent"}},7,Failure)
    assert exc.value.code=="business_rule_error" and not calls


@pytest.mark.parametrize("active", [True,False])
def test_actual_native_config_result_state_is_accepted(active,monkeypatch):
    _,term,_=term_fixture(monkeypatch)
    term.active=active
    value=runtime._payment_term_result(term,7)
    value["source_id"]=41
    assert core_writes._validate_result("payment_term.line.update",PARAMETERS["payment_term.line.update"],value,
                                        company_id=7,idempotent_replay=False)["state"]==("active" if active else "archived")


def test_schedule_reads_native_computed_map_without_writing(monkeypatch):
    class Key(dict):
        def __hash__(self): return hash(tuple(self.items()))
    item=read_item()
    line=item["lines"][0]
    invoice=SimpleNamespace(id=31,company_id=SimpleNamespace(id=7,currency_id=SimpleNamespace(id=6)),
        currency_id=SimpleNamespace(id=6),invoice_payment_term_id=SimpleNamespace(id=False),
        move_type="out_invoice",state="draft",needed_terms={Key(move_id=31,date_maturity=date(2026,10,1)):line})
    class Model:
        def with_context(self,**context): assert context=={"allowed_company_ids":[7]}; return self
        def search(self,domain,limit):
            assert ("company_id","=",7) in domain and ("id","=",31) in domain
            return invoice
    assert reads._invoice_payment_schedule_rows({"account.move":Model()},{"invoice_id":31},7)==[item]


def test_copy_preserves_native_configuration_after_copy_name_defaults_and_replays(monkeypatch):
    env,term,calls=term_fixture(monkeypatch)
    term.active=False
    term.company_id=False  # A shared source is read, then copied into the requested company.
    candidates=Rows()
    def copy(defaults):
        assert defaults=={"company_id":7}
        target=SimpleNamespace(**{key:value for key,value in vars(term).items() if key not in {"copy","write","line_ids"}})
        target.id=61
        target.name="NATIVE COPY NAME"
        target.company_id=SimpleNamespace(id=7)
        target.early_pay_discount_computation="included"
        target.line_ids=Rows(SimpleNamespace(**{**vars(row),"id":row.id+2,"payment_id":target}) for row in term.line_ids)
        def write(values):
            calls.append(dict(values))
            vars(target).update(values)
        target.write=write
        candidates.append(target)
        return target
    term.copy=copy
    monkeypatch.setattr(runtime,"_scoped",lambda *args:SimpleNamespace(search=lambda *args,**kwargs:candidates))
    cap="payment_term.duplicate"
    first,replay=runtime._write_payment_term_processing(env,cap,PARAMETERS[cap],7,Failure)
    assert first["id"]==61 and first["name"]=="COPY" and first["state"]=="archived" and replay is False
    assert first["line_ids"]==[43,44] and runtime._payment_term_copy_values(candidates)==runtime._payment_term_copy_values(term)
    assert runtime._write_payment_term_processing(env,cap,PARAMETERS[cap],7,Failure)==(first,True)
    assert len(calls)==1 and candidates.early_pay_discount_computation=="excluded"
    term.line_ids[0].value_amount,term.line_ids[1].value_amount=35,65
    with pytest.raises(Failure) as exc:
        runtime._write_payment_term_processing(env,cap,PARAMETERS[cap],7,Failure)
    assert exc.value.code=="idempotency_conflict" and len(calls)==1


def test_line_create_delete_and_ambiguous_replay_preserve_siblings(monkeypatch):
    env,term,calls=term_fixture(monkeypatch)
    cap="payment_term.line.create"
    first,replay=runtime._write_payment_term_processing(env,cap,PARAMETERS[cap],7,Failure)
    assert first["source_id"]==43 and first["line_ids"]==[41,42,43] and replay is False
    assert term.line_ids[-1].value_amount==-7.5 and term.line_ids[-1].nb_days==-10
    assert runtime._write_payment_term_processing(env,cap,PARAMETERS[cap],7,Failure)==(first,True)
    assert len(calls)==1
    shadow=SimpleNamespace(**{**vars(term.line_ids[-1]),"id":44})
    term.line_ids.append(shadow)
    with pytest.raises(Failure) as exc:
        runtime._write_payment_term_processing(env,cap,PARAMETERS[cap],7,Failure)
    assert exc.value.code=="idempotency_conflict" and len(calls)==1
    term.line_ids.remove(shadow)
    removed,replay=runtime._write_payment_term_processing(env,"payment_term.line.delete",{"payment_term_id":31,"line_id":43},7,Failure)
    assert removed["source_id"]==43 and removed["line_ids"]==[41,42] and replay is False
    with pytest.raises(Failure) as exc:
        runtime._write_payment_term_processing(env,"payment_term.line.delete",{"payment_term_id":31,"line_id":43},7,Failure)
    assert exc.value.code=="record_not_found"


def test_all_atomic_child_ids_are_scoped_before_first_write(monkeypatch):
    env,term,calls=term_fixture(monkeypatch)
    params={"payment_term_id":31,"lines":[{"line_id":41,"changes":{"nb_days":20}},{"line_id":99,"changes":{"nb_days":30}}]}
    with pytest.raises(Failure) as exc:
        runtime._write_payment_term_processing(env,"payment_term.lines.update",params,7,Failure)
    assert exc.value.code=="record_not_found" and not calls and term.line_ids[0].nb_days==10


def test_native_parent_delete_returns_actual_deleted_shape(monkeypatch):
    env,term,_=term_fixture(monkeypatch)
    term.unlink=lambda:term.line_ids.clear()
    term.exists=lambda:False
    cap="payment_term.delete"
    value,replay=runtime._write_payment_term_processing(env,cap,PARAMETERS[cap],7,Failure)
    assert value["state"]=="deleted" and value["line_ids"]==[] and replay is False
    assert core_writes._validate_result(cap,PARAMETERS[cap],value,company_id=7,idempotent_replay=False)==value
