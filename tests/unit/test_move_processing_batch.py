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
from odoo_accounting_cli_v4 import move_processing_contracts as contracts
from odoo_accounting_cli_v4.bridge import core_writes_runtime as runtime
from odoo_accounting_cli_v4.capabilities import core_writes as public
from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry

PARAMETERS = {
    "invoice.currency_rate.update": {"move_id":31,"rate":"2"},
    "invoice.currency_rate.refresh": {"move_id":31},
    "invoice.cash_rounding.assign": {"move_id":31,"cash_rounding_id":11},
    "invoice.incoterm.update": {"move_id":31,"changes":{"incoterm_id":11,"incoterm_location":"Shanghai"}},
    "invoice.payment_method.assign": {"move_id":31,"payment_method_line_id":11},
    "invoice.payment_block.set": {"move_id":31,"blocked":True},
    "accounting_move.review.set": {"move_id":31,"checked":False},
    "accounting_move.autopost.configure": {"move_id":31,"auto_post":"monthly","auto_post_until":"2026-12-31"},
}


def result(capability_id, parameters):
    return {
        "model":"account.move","id":parameters["move_id"],"name":"INV/2026/31",
        "state":"posted" if capability_id=="accounting_move.review.set" else "draft",
        "company_id":7,"move_type":"entry" if capability_id.startswith("accounting_move.") else "out_invoice",
        "source_id":None,"line_ids":[41,42],"partial_reconcile_ids":[],
        "full_reconcile_id":None,"reconciled":False,
    }


def read_item():
    return {
        "id":31,"name":"INV/2026/31","company_id":7,"move_type":"out_invoice","state":"draft",
        "date":"2026-10-01","currency_id":2,"company_currency_id":1,
        "invoice_currency_rate":"2","expected_currency_rate":"1.2",
        "invoice_cash_rounding_id":None,"invoice_incoterm_id":None,"incoterm_location":None,
        "preferred_payment_method_line_id":None,"auto_post":"no","auto_post_until":None,
        "auto_post_origin_id":None,"checked":False,"payment_state":"not_paid",
    }


@pytest.fixture(scope="module")
def registry():
    return load_registry()


@pytest.mark.parametrize("capability_id",PARAMETERS)
def test_closed_contract_schema_and_public_cli(capability_id,registry,monkeypatch):
    req=request(PARAMETERS[capability_id])
    registry.validate_instance(f"schemas/v1/{capability_id}.request.schema.json",req)
    params=public.validate_core_write_request(capability_id,req)[2]
    assert runtime._valid_parameters(capability_id,params,7)
    key=public._expected_idempotency_key(capability_id,params,7)
    assert key==runtime._deterministic_key(capability_id,params,7)
    expected=result(capability_id,params)
    class Port:
        user_id=42
        def execute(self,**payload):
            assert payload["parameters"]==params and payload["confirmation"]==capability_id and payload["idempotency_key"]==key
            return {"user_id":42,"company_visible":True,"module_installed":True,"access_allowed":True,"idempotent_replay":False,"result":deepcopy(expected)}
    monkeypatch.setattr(cli,"load_registry",lambda:registry)
    stdout,stderr=io.StringIO(),io.StringIO()
    assert cli.main(["write","run",capability_id,"--request","-","--confirm",capability_id,"--idempotency-key",key],
                    stdin=io.StringIO(json.dumps(req)),stdout=stdout,stderr=stderr,port_factory=lambda *args:Port())==0
    response=json.loads(stdout.getvalue())
    assert response["success"] and not stderr.getvalue()
    registry.validate_instance(f"schemas/v1/{capability_id}.response.schema.json",response)
    with pytest.raises(public.CoreWriteError):
        public._validate_result(capability_id,params,{**expected,"company_id":8},company_id=7,idempotent_replay=False)
    with pytest.raises(public.CoreWriteError):
        public.execute_core_write(Port(),capability_id,req,key,"other-command")


def test_read_contract_and_public_cli(registry,monkeypatch):
    from test_core_object_reads import FakePort
    cap=contracts.READ_ID
    req=request({"move_id":31})
    item=read_item()
    registry.validate_instance(f"schemas/v1/{cap}.request.schema.json",req)
    assert contracts.valid_read_item(item,7)
    monkeypatch.setattr(cli,"load_registry",lambda:registry)
    stdout,stderr=io.StringIO(),io.StringIO()
    assert cli.main(["read",cap,"--request","-"],stdin=io.StringIO(json.dumps(req)),stdout=stdout,stderr=stderr,
                    port_factory=lambda *args:FakePort([item]))==0
    response=json.loads(stdout.getvalue())
    assert response["success"] and response["data"]==item and not stderr.getvalue()
    registry.validate_instance(f"schemas/v1/{cap}.response.schema.json",response)
    for bad in ({"company_id":8},{"company_id":True},{"checked":1},{"auto_post":[]},{"field":1}):
        assert not contracts.valid_read_item({**item,**bad},7)


@pytest.mark.parametrize("capability_id",PARAMETERS)
@pytest.mark.parametrize("denial",["group","acl"])
def test_native_group_acl_denial_never_mutates(capability_id,denial):
    env=Env()
    if denial=="group": env.denied_group=runtime._GROUPS[capability_id]
    else: env.denied_access=("account.move","write")
    params=contracts.normalize_parameters(capability_id,PARAMETERS[capability_id])
    page=runtime.dispatch(env,_payload(capability_id,params,key=contracts.idempotency_key(capability_id,params,7)),7,Failure)
    assert not page["access_allowed"] and page["result"] is None
    assert not any(call[0] in {"create","write","unlink","copy"} for call in env.calls)


@pytest.mark.parametrize("capability_id",PARAMETERS)
def test_fixed_keys_scope_and_identifier_validation(capability_id):
    params=deepcopy(PARAMETERS[capability_id])
    assert contracts.normalize_parameters(capability_id,params)==params
    assert contracts.idempotency_key(capability_id,params,7)!=contracts.idempotency_key(capability_id,params,8)
    for bad in ({**params,"move_id":True},{**params,"model":"res.partner"}):
        with pytest.raises(ValueError): contracts.normalize_parameters(capability_id,bad)


@pytest.mark.parametrize("value",[True,1,None,"0","0.0","-1","1e2","NaN","Infinity","01",".1","1."," 1","1\n"])
def test_rate_rejects_nonpositive_or_invalid_decimal(value, registry):
    with pytest.raises(InstanceValidationError):
        registry.validate_instance("schemas/v1/invoice.currency_rate.update.request.schema.json", request({"move_id":31,"rate":value}))
    with pytest.raises(ValueError): contracts.normalize_parameters("invoice.currency_rate.update",{"move_id":31,"rate":value})


@pytest.mark.parametrize("cap,patch",[
    ("invoice.cash_rounding.assign",{"cash_rounding_id":True}),
    ("invoice.payment_method.assign",{"payment_method_line_id":0}),
    ("invoice.incoterm.update",{"changes":{"partner_id":99}}),
    ("invoice.incoterm.update",{"changes":{}}),
    ("invoice.incoterm.update",{"changes":{"incoterm_location":" padded "}}),
    ("invoice.payment_block.set",{"blocked":1}),
    ("accounting_move.review.set",{"checked":"yes"}),
    ("accounting_move.autopost.configure",{"auto_post":[]}),
    ("accounting_move.autopost.configure",{"auto_post":"unknown"}),
    ("accounting_move.autopost.configure",{"auto_post_until":"2026-02-30"}),
    ("accounting_move.autopost.configure",{"auto_post":"no","auto_post_until":"2026-12-31"}),
])
def test_invalid_native_setting_contract(cap,patch,registry):
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(f"schemas/v1/{cap}.request.schema.json", request({**PARAMETERS[cap],**patch}))
    with pytest.raises(ValueError): contracts.normalize_parameters(cap,{**PARAMETERS[cap],**patch})


@pytest.mark.parametrize("cap",["invoice.payment_block.set","accounting_move.review.set","invoice.currency_rate.refresh"])
def test_native_method_is_called_once_and_replay_does_not_toggle_again(monkeypatch,cap):
    calls=[]
    move=SimpleNamespace(id=31,state="posted" if "review" in cap else "draft",checked=True,
                         payment_state="not_paid",invoice_currency_rate=2.,expected_currency_rate=1.2,
                         currency_id=2,company_id=SimpleNamespace(currency_id=1),invalidate_recordset=lambda *args:None)
    def review(value): calls.append(("review",value)); move.checked=value
    def block(): calls.append(("block",)); move.payment_state="blocked"
    def refresh(): calls.append(("refresh",)); move.invoice_currency_rate=1.2
    move.set_moves_checked=review
    move.action_toggle_block_payment=block
    move.refresh_invoice_currency_rate=refresh
    monkeypatch.setattr(runtime,"_search_one",lambda *args:move)
    monkeypatch.setattr(runtime,"_move_result",lambda *args:result(cap,PARAMETERS[cap]))
    first,replay=runtime._write_move_processing(None,cap,PARAMETERS[cap],7,Failure)
    assert not replay and len(calls)==1
    second,replay=runtime._write_move_processing(None,cap,PARAMETERS[cap],7,Failure)
    assert replay and second==first and len(calls)==1


def test_scheduling_patches_native_fields_without_running_post_or_cron(monkeypatch):
    calls=[]
    move=SimpleNamespace(id=31,state="draft",auto_post="no",auto_post_until=False,invalidate_recordset=lambda *args:None)
    def write(values):
        calls.append(values)
        move.auto_post=values["auto_post"]
        move.auto_post_until=date.fromisoformat(values["auto_post_until"])
    move.write=write
    cap="accounting_move.autopost.configure"
    monkeypatch.setattr(runtime,"_search_one",lambda *args:move)
    monkeypatch.setattr(runtime,"_move_result",lambda *args:result(cap,PARAMETERS[cap]))
    _,replay=runtime._write_move_processing(None,cap,PARAMETERS[cap],7,Failure)
    assert not replay and calls==[{"auto_post":"monthly","auto_post_until":"2026-12-31"}]
    _,replay=runtime._write_move_processing(None,cap,PARAMETERS[cap],7,Failure)
    assert replay and len(calls)==1


@pytest.mark.parametrize("until", [False, date(2026,12,31)])
def test_native_date_objects_normalize_to_json_dates(until):
    from odoo_accounting_cli_v4.bridge import core_object_reads_runtime as reads

    row={**read_item(), "date":date(2026,10,1), "auto_post_until":until,
         "auto_post":"monthly" if until else "no",
         "invoice_currency_rate":2., "expected_currency_rate":1.2}
    normalized=reads._normalize_move_processing(None,[row],7)[0]
    assert normalized["date"]=="2026-10-01"
    assert normalized["auto_post_until"]==("2026-12-31" if until else None)
    assert contracts.valid_read_item(normalized,7)


def test_explicit_null_entry_currency_leaves_native_required_currency_to_default():
    from test_core_writes_runtime import _entry_parameters

    env=Env()
    params=_entry_parameters(env)
    for line in params["lines"]:
        line.update(currency_id=None,amount_currency=None)
    page=runtime.dispatch(env,_payload("journal_entry.create",params,key="implicit-currency-regression"),7,Failure)
    assert page["result"]["move_type"]=="entry"
    values=next(call[2] for call in env.calls if call[:2]==("create","account.move"))
    commands=values["line_ids"]+runtime._replacement_commands("journal_entry.lines.replace",params["lines"])[1:]
    for command in commands:
        assert "currency_id" not in command[2] and "amount_currency" not in command[2]
