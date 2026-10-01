from __future__ import annotations

import io
import json
from contextlib import contextmanager, nullcontext
from copy import deepcopy
from types import SimpleNamespace

import pytest
from jsonschema import Draft202012Validator
from test_core_writes_runtime import Env, Failure, _payload
from test_fiscal_mapping_writes import request

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4 import invoice_presentation_contracts as contracts
from odoo_accounting_cli_v4.bridge import core_object_reads_runtime as reads
from odoo_accounting_cli_v4.bridge import core_writes_runtime as runtime
from odoo_accounting_cli_v4.capabilities import core_object_reads, core_writes
from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry

LAYOUT = {"display_type": "line_section", "name": "Services", "sequence": 10,
          "collapse_prices": False, "collapse_composition": False}
PARAMETERS = {
    "invoice.presentation_settings.update": {"move_id":31,"changes":{"narration":"<p>Terms</p>"}},
    "invoice.layout_line.create": {"move_id":31,"line":LAYOUT},
    "invoice.layout_line.update": {"move_id":31,"line_id":41,"changes":{"name":"Services revised"}},
    "invoice.layout_line.delete": {"move_id":31,"line_id":41},
    "invoice.lines.resequence": {"move_id":31,"line_ids":[42,41]},
    "invoice.fiscal_position.refresh": {"move_id":31},
}


def result(capability_id, parameters):
    return {"model":"account.move","id":parameters["move_id"],"name":"/","state":"draft",
            "company_id":7,"move_type":"out_invoice","source_id":41 if ".layout_line." in capability_id else None,
            "line_ids":[42] if capability_id.endswith(".delete") else [41,42],
            "partial_reconcile_ids":[],"full_reconcile_id":None,"reconciled":False}


def read_item(capability_id=contracts.GET_ID, record_id=31):
    if capability_id==contracts.LIST_ID:
        return {"id":record_id,"move_id":31,"company_id":7,**LAYOUT,"parent_id":None}
    return {"id":record_id,"name":"/","company_id":7,"move_type":"out_invoice","state":"draft",
            "partner_id":11,"partner_shipping_id":12,"invoice_user_id":5,
            "narration":"<p>Terms</p>","fiscal_position_id":None}


@pytest.fixture(scope="module")
def registry():
    return load_registry()


@pytest.mark.parametrize("capability_id", PARAMETERS)
def test_fixed_public_cli_contract_and_scope(capability_id, registry, monkeypatch):
    req=request(PARAMETERS[capability_id])
    registry.validate_instance(f"schemas/v1/{capability_id}.request.schema.json",req)
    params=core_writes.validate_core_write_request(capability_id,req)[2]
    assert runtime._valid_parameters(capability_id,params,7)
    key=core_writes._expected_idempotency_key(capability_id,params,7)
    assert key==runtime._deterministic_key(capability_id,params,7)
    expected=result(capability_id,params)
    class Port:
        user_id=42
        def execute(self,**payload):
            assert payload["parameters"]==params and payload["confirmation"]==capability_id and payload["idempotency_key"]==key
            return {"user_id":42,"company_visible":True,"module_installed":True,"access_allowed":True,
                    "idempotent_replay":False,"result":deepcopy(expected)}
    monkeypatch.setattr(cli,"load_registry",lambda:registry)
    stdout,stderr=io.StringIO(),io.StringIO()
    assert cli.main(["write","run",capability_id,"--request","-","--confirm",capability_id,"--idempotency-key",key],
                    stdin=io.StringIO(json.dumps(req)),stdout=stdout,stderr=stderr,port_factory=lambda *args:Port())==0
    response=json.loads(stdout.getvalue())
    assert response["success"] and not stderr.getvalue()
    registry.validate_instance(f"schemas/v1/{capability_id}.response.schema.json",response)
    for field,value in (("id",32),("company_id",8),("state","posted"),("move_type","entry")):
        with pytest.raises(core_writes.CoreWriteError):
            core_writes._validate_result(capability_id,params,{**expected,field:value},company_id=7,idempotent_replay=False)


@pytest.mark.parametrize("capability_id", sorted(contracts.READ_IDS))
def test_closed_reads_and_native_relation_normalization(capability_id,registry,monkeypatch):
    item=read_item(capability_id)
    class Port:
        user_id=42
        def read(self,**payload):
            assert payload["parameters"]["move_id"]==31
            return {"user_id":42,"company_visible":True,"module_installed":True,"access_allowed":True,"cursor_found":True,"items":[item]}
    req=request({"move_id":31})
    registry.validate_instance(f"schemas/v1/{capability_id}.request.schema.json",req)
    monkeypatch.setattr(cli,"load_registry",lambda:registry)
    stdout,stderr=io.StringIO(),io.StringIO()
    assert cli.main(["read",capability_id,"--request","-"],stdin=io.StringIO(json.dumps(req)),
                    stdout=stdout,stderr=stderr,port_factory=lambda *args:Port())==0, (stdout.getvalue(),stderr.getvalue())
    response=json.loads(stdout.getvalue())
    assert response["success"] and not stderr.getvalue()
    registry.validate_instance(f"schemas/v1/{capability_id}.response.schema.json",response)
    raw={field:[value,"Native relation"] if field.endswith("_id") and value is not None else False if value is None else value for field,value in item.items()}
    assert reads._normalize_invoice_presentation(capability_id,[raw],7)==[item]
    assert not contracts.valid_read_item(capability_id,{**item,"company_id":True},7)
    if capability_id==contracts.LIST_ID:
        item["move_id"]=32
        with pytest.raises(core_object_reads.CoreObjectReadError,match="wrong invoice"):
            core_object_reads.read_core_object(capability_id,Port(),req)


@pytest.mark.parametrize("capability_id",PARAMETERS)
@pytest.mark.parametrize("denial",["group","acl"])
def test_runtime_checks_native_access_before_mutation(capability_id,denial,monkeypatch):
    env=Env()
    if denial=="group": env.denied_group=runtime._GROUPS[capability_id]
    else: env.denied_access=("account.move","write")
    monkeypatch.setattr(runtime,"_dispatch_allowed",lambda *args:pytest.fail("denied mutation dispatched"))
    payload=_payload(capability_id,PARAMETERS[capability_id])
    payload["idempotency_key"]=contracts.idempotency_key(capability_id,payload["parameters"],7)
    page=runtime.dispatch(env,payload,7,failure_type=Failure)
    assert not page["access_allowed"] and page["result"] is None


INVALID = [
    ("invoice.presentation_settings.update",{"changes":{"arbitrary_field":True}}),
    ("invoice.presentation_settings.update",{"changes":{"invoice_user_id":True}}),
    ("invoice.presentation_settings.update",{"changes":{"narration":""}}),
    ("invoice.layout_line.create",{"line":{**LAYOUT,"display_type":"product"}}),
    ("invoice.layout_line.create",{"line":{**LAYOUT,"account_id":11}}),
    ("invoice.layout_line.create",{"line":{**LAYOUT,"sequence":True}}),
    ("invoice.layout_line.create",{"line":{**LAYOUT,"sequence":2147483648}}),
    ("invoice.layout_line.create",{"line":{**LAYOUT,"name":"  \n"}}),
    ("invoice.layout_line.create",{"line":{**LAYOUT,"collapse_prices":"true"}}),
    ("invoice.layout_line.update",{"changes":{}}),
    ("invoice.layout_line.delete",{"line_id":False}),
    ("invoice.lines.resequence",{"line_ids":[]}),
    ("invoice.lines.resequence",{"line_ids":[41,41]}),
    ("invoice.lines.resequence",{"line_ids":[True,42]}),
    ("invoice.fiscal_position.refresh",{"sudo":True}),
]


@pytest.mark.parametrize(("capability_id","changes"),INVALID)
def test_reject_invalid_settings_in_schema_and_contract(capability_id,changes,registry):
    params={**PARAMETERS[capability_id],**changes}
    with pytest.raises(ValueError): contracts.normalize_parameters(capability_id,params)
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(f"schemas/v1/{capability_id}.request.schema.json",request(params))


@pytest.mark.parametrize("move_type",sorted(contracts.INVOICE_TYPES))
def test_native_move_scope_and_posted_boundary(move_type,monkeypatch):
    env=Env()
    env.add("account.move",31,company_id=7,move_type=move_type,state="posted")
    with pytest.raises(Failure) as exc:
        runtime._write_invoice_presentation(env,"invoice.fiscal_position.refresh",{"move_id":31},7,Failure)
    assert exc.value.code=="state_conflict"


def test_fiscal_refresh_uses_native_action_and_detects_actual_change(monkeypatch):
    calls=[]
    line=SimpleNamespace(id=41,account_id=SimpleNamespace(id=11),tax_ids=SimpleNamespace(ids=[]),price_unit=1,balance=1)
    def refresh():
        calls.append("action_update_fpos_values")
        line.price_unit=line.balance=25
    move=SimpleNamespace(state="draft",line_ids=[line],action_update_fpos_values=refresh,invalidate_recordset=lambda:None,
                         _check_balanced=lambda container:nullcontext(),_sync_dynamic_lines=lambda container:nullcontext())
    monkeypatch.setattr(runtime,"_search_one",lambda *args:move)
    monkeypatch.setattr(runtime,"_move_result",lambda *args:result("invoice.fiscal_position.refresh",{"move_id":31}))
    for expected in (False,True):
        assert runtime._write_invoice_presentation(None,"invoice.fiscal_position.refresh",{"move_id":31},7,Failure)[1] is expected
    assert calls==["action_update_fpos_values"]*2


def test_terms_replay_uses_native_html_sanitization(monkeypatch):
    writes=[]
    move=SimpleNamespace(state="draft",narration=None,_fields={"narration":SimpleNamespace(convert_to_cache=lambda value,record:"<p>Terms</p>")},invalidate_recordset=lambda:None)
    def write(changes):
        writes.append(changes)
        move.narration=changes["narration"]
    move.write=write
    monkeypatch.setattr(runtime,"_search_one",lambda *args:move)
    monkeypatch.setattr(runtime,"_move_result",lambda *args:result("invoice.presentation_settings.update",{"move_id":31}))
    params={"move_id":31,"changes":{"narration":"<script>bad()</script><p>Terms</p>"}}
    for expected in (False,True):
        assert runtime._write_invoice_presentation(None,"invoice.presentation_settings.update",params,7,Failure)[1] is expected
    assert writes==[{"narration":"<p>Terms</p>"}]


@pytest.mark.parametrize("name",[None,"Historical native note "*50])
def test_layout_reads_accept_existing_native_empty_and_long_labels(name,registry):
    item={**read_item(contracts.LIST_ID),"name":name}
    assert contracts.valid_read_item(contracts.LIST_ID,item,7)
    response_schema=json.loads((registry._root/f"schemas/v1/{contracts.LIST_ID}.response.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(response_schema["$defs"]["item"]).validate(item)


def test_fiscal_refresh_holds_native_balance_and_dynamic_sync_until_all_computes(monkeypatch):
    events=[]
    @contextmanager
    def guard(kind,container):
        assert container["records"] is move
        events.append(kind+".enter")
        yield
        events.append(kind+".exit")
    def action():
        if events!=["balance.enter","sync.enter"]:
            raise RuntimeError("Dynamic tax synchronization deleted an old line during native account recomputation")
        events.append("native.action")
    move=SimpleNamespace(state="draft",line_ids=[],action_update_fpos_values=action,
                         invalidate_recordset=lambda:None,_check_balanced=lambda c:guard("balance",c),
                         _sync_dynamic_lines=lambda c:guard("sync",c))
    monkeypatch.setattr(runtime,"_search_one",lambda *args:move)
    monkeypatch.setattr(runtime,"_move_result",lambda *args:result("invoice.fiscal_position.refresh",{"move_id":31}))
    runtime._write_invoice_presentation(None,"invoice.fiscal_position.refresh",{"move_id":31},7,Failure)
    assert events==["balance.enter","sync.enter","native.action","sync.exit","balance.exit"]
