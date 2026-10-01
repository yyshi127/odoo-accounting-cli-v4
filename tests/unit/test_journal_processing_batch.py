from __future__ import annotations

import io
import json
from contextlib import contextmanager
from copy import deepcopy
from itertools import count
from types import SimpleNamespace

import pytest
from test_core_writes_runtime import Env, Failure, _payload
from test_fiscal_mapping_writes import request
from test_payment_term_processing_batch import Rows

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4 import journal_processing_contracts as contracts
from odoo_accounting_cli_v4.bridge import core_object_reads_runtime as reads
from odoo_accounting_cli_v4.bridge import core_writes_runtime as runtime
from odoo_accounting_cli_v4.capabilities import core_writes
from odoo_accounting_cli_v4.registry import load_registry

PARAMETERS = {
    "journal.duplicate": {"journal_id": 31, "code": "JCP1", "name": "Copy"},
    "journal.delete": {"journal_id": 31},
    "journal.sequence_policy.update": {"journal_id": 31, "changes": {"refund_sequence": False, "payment_sequence": True}},
    "journal.invoice_reference.update": {"journal_id": 31, "changes": {"invoice_reference_type": "partner", "invoice_reference_model": "euro"}},
    "journal.non_deductible_account.assign": {"journal_id": 31, "account_id": 41},
    "journal.invoice_template.assign": {"journal_id": 31, "report_id": 51},
    "journal.group.delete": {"journal_group_id": 61},
}


def result(capability_id, parameters):
    duplicate = capability_id == "journal.duplicate"
    group = capability_id == "journal.group.delete"
    return {"model": "account.journal.group" if group else "account.journal", "id": 91 if duplicate else parameters.get("journal_id", 61),
            "name": parameters["name"] if duplicate else "Journal", "state": "deleted" if capability_id.endswith("delete") else "active",
            "company_id": 7, "move_type": None, "source_id": parameters["journal_id"] if duplicate else None, "line_ids": [],
            "partial_reconcile_ids": [], "full_reconcile_id": None, "reconciled": False}


def read_item(capability_id=contracts.GET_ID, record_id=31):
    assert capability_id == contracts.GET_ID
    return {"id": record_id, "company_id": 7, "active": True, "type": "sale", "refund_sequence": True, "payment_sequence": False,
            "is_self_billing": False, "non_deductible_account_id": None, "invoice_template_pdf_report_id": 51,
            "available_invoice_template_pdf_report_ids": [51, 52]}


@pytest.fixture(scope="module")
def registry():
    return load_registry()


@pytest.mark.parametrize("capability_id", PARAMETERS)
def test_public_cli_schemas_hashes_and_result_scope(capability_id, registry, monkeypatch):
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
            return {"user_id": 42, "company_visible": True, "module_installed": True, "access_allowed": True, "idempotent_replay": False, "result": expected}
    monkeypatch.setattr(cli, "load_registry", lambda: registry)
    stdout, stderr = io.StringIO(), io.StringIO()
    assert cli.main(["write", "run", capability_id, "--request", "-", "--confirm", capability_id, "--idempotency-key", key],
                    stdin=io.StringIO(json.dumps(req)), stdout=stdout, stderr=stderr, port_factory=lambda *args: Port()) == 0, stdout.getvalue()
    registry.validate_instance(f"schemas/v1/{capability_id}.response.schema.json", json.loads(stdout.getvalue()))
    assert not stderr.getvalue()
    for field, value in (("id", params["journal_id"] if capability_id == "journal.duplicate" else 999), ("company_id", 8), ("model", "account.move"), ("source_id", 999), ("line_ids", [999])):
        with pytest.raises(core_writes.CoreWriteError):
            core_writes._validate_result(capability_id, params, {**expected, field: value}, company_id=7, idempotent_replay=False)
    if capability_id.endswith("delete"):
        with pytest.raises(core_writes.CoreWriteError):
            core_writes._validate_result(capability_id, params, expected, company_id=7, idempotent_replay=True)


def test_public_read_normalizes_relations_and_native_candidates(registry, monkeypatch):
    item = read_item()
    class Port:
        user_id = 42
        def read(self, **payload):
            assert payload["parameters"] == {"journal_id": 31}
            return {"user_id": 42, "company_visible": True, "module_installed": True, "access_allowed": True, "cursor_found": True, "items": [item]}
    monkeypatch.setattr(cli, "load_registry", lambda: registry)
    stdout, stderr = io.StringIO(), io.StringIO()
    assert cli.main(["read", contracts.GET_ID, "--request", "-"], stdin=io.StringIO(json.dumps(request({"journal_id": 31}))),
                    stdout=stdout, stderr=stderr, port_factory=lambda *args: Port()) == 0, stdout.getvalue()
    registry.validate_instance(f"schemas/v1/{contracts.GET_ID}.response.schema.json", json.loads(stdout.getvalue()))
    raw = {**item, "company_id": [7, "Company"], "non_deductible_account_id": False,
           "invoice_template_pdf_report_id": [51, "Invoice"], "available_invoice_template_pdf_report_ids": [52, 51]}
    assert reads._normalize_journal_processing([raw], 7) == [item]
    for change in ({"company_id": 8}, {"company_id": True}, {"type": []}, {"payment_sequence": 1}, {"available_invoice_template_pdf_report_ids": [True]}):
        assert not contracts.valid_read_item({**item, **change}, 7)


@pytest.mark.parametrize("capability_id", PARAMETERS)
def test_runtime_requires_confirmed_company_user_and_native_acl(capability_id):
    params = core_writes.validate_core_write_request(capability_id, request(PARAMETERS[capability_id]))[2]
    payload = _payload(capability_id, parameters=params)
    payload["idempotency_key"] = contracts.idempotency_key(capability_id, params, 7)
    denied = Env()
    denied.denied_group = runtime._GROUPS[capability_id]
    assert runtime.dispatch(denied, payload, 7, failure_type=Failure)["access_allowed"] is False
    model, operation = next(iter(runtime._ACCESS[capability_id]))
    denied = Env()
    denied.denied_access = (model, operation)
    assert runtime.dispatch(denied, payload, 7, failure_type=Failure)["access_allowed"] is False


@pytest.mark.parametrize("capability_id,change", [
    ("journal.duplicate", {"code": "TOOLONG"}), ("journal.duplicate", {"code": "J.P"}), ("journal.duplicate", {"name": " Copy "}),
    ("journal.sequence_policy.update", {"changes": {"refund_sequence": 1}}), ("journal.sequence_policy.update", {"changes": {}}),
    ("journal.sequence_policy.update", {"changes": {"sequence_override_regex": ".*"}}),
    ("journal.invoice_reference.update", {"changes": {"invoice_reference_model": "unknown"}}),
    ("journal.invoice_reference.update", {"changes": {"invoice_reference_model": []}}),
    ("journal.non_deductible_account.assign", {"account_id": False}), ("journal.invoice_template.assign", {"report_id": 0}),
    ("journal.group.delete", {"journal_group_id": True}),
])
def test_closed_invalid_parameters(capability_id, change):
    with pytest.raises(ValueError): contracts.normalize_parameters(capability_id, {**PARAMETERS[capability_id], **change})


def test_native_parent_operations_do_not_require_unrelated_standalone_alias_or_bank_rights():
    assert ("mail.alias", "create") not in runtime._ACCESS["journal.duplicate"]
    assert ("mail.alias", "unlink") not in runtime._ACCESS["journal.delete"]
    assert ("res.partner.bank", "unlink") not in runtime._ACCESS["journal.delete"]
    assert ("account.journal", "create") in runtime._ACCESS["journal.duplicate"]
    assert ("account.journal", "unlink") in runtime._ACCESS["journal.delete"]


@pytest.fixture
def journals(monkeypatch):
    records, calls = {}, []
    identities = count(91)
    class Journal:
        def __init__(self, record_id=31, company_id=7, **changes):
            self.id, self.company_id, self.name, self.code, self.present = record_id, SimpleNamespace(id=company_id), "Journal", "SRC", True
            self.active, self.type, self.sequence = True, "sale", 10
            self.refund_sequence, self.payment_sequence, self.is_self_billing, self.restrict_mode_hash_table = True, False, False, False
            self.invoice_reference_type, self.invoice_reference_model = "invoice", "odoo"
            for field in contracts.RELATION_FIELDS: setattr(self, field, SimpleNamespace(id=False))
            self.available_invoice_template_pdf_report_ids = Rows([SimpleNamespace(id=51), SimpleNamespace(id=52)])
            self.__dict__.update(changes)
            records[self.id] = self
        def copy(self, defaults):
            assert defaults == {"company_id": 7}
            calls.append(("copy", deepcopy(defaults)))
            values = deepcopy(self.__dict__)
            values.pop("id"); values.pop("company_id")
            return Journal(next(identities), code="AUTO", name="Native copy", **{key:value for key,value in values.items() if key not in {"code","name"}})
        def write(self, values):
            calls.append(("write", deepcopy(values)))
            for field, value in values.items(): setattr(self, field, SimpleNamespace(id=value) if field in contracts.RELATION_FIELDS else value)
            if getattr(self, "fail", False): raise ValueError("native failure")
        def invalidate_recordset(self, *args): pass
        def unlink(self):
            if getattr(self, "used", False): raise ValueError("native journal FK guard")
            self.present = False
        def exists(self): return self.present
    class Cursor:
        @contextmanager
        def savepoint(self):
            snapshot = {record_id:deepcopy(record.__dict__) for record_id,record in records.items()}
            try: yield
            except BaseException:
                for record_id in list(records):
                    if record_id not in snapshot: del records[record_id]
                    else:
                        records[record_id].__dict__.clear()
                        records[record_id].__dict__.update(snapshot[record_id])
                raise
    def find(env, record_id, company_id, failure_type):
        record = records.get(record_id)
        if record is None or not record.present or record.company_id.id != company_id:
            raise Failure("record_not_found", "missing scoped journal", exit_code=4)
        return record
    class Model:
        def search(self, domain, **kwargs):
            code = next(value for field,op,value in domain if field=="code")
            return Rows([record for record in records.values() if record.present and record.company_id.id==7 and record.code==code])
    def ensure(env, model, ids, domain, company_id, failure_type):
        assert model in {"account.account", "ir.actions.report"}
        if model=="account.account": assert domain==[("company_ids", "in", [7]), ("active", "=", True)]
        if not ids <= ({41} if model=="account.account" else {51,52}): raise Failure("record_not_found", "bad reference", exit_code=4)
    monkeypatch.setattr(runtime, "_journal_config_record", find)
    monkeypatch.setattr(runtime, "_journal_group", find)
    monkeypatch.setattr(runtime, "_scoped", lambda *args: Model())
    monkeypatch.setattr(runtime, "_ensure_ids", ensure)
    return SimpleNamespace(cr=Cursor()), Journal(), Journal, records, calls


def test_native_copy_renames_only_target_replays_conflicts_and_recreates(journals):
    env, source, _, records, calls = journals
    params = PARAMETERS["journal.duplicate"]
    first, replay = runtime._write_journal_processing(env, "journal.duplicate", params, 7, Failure)
    assert not replay and first["source_id"]==31 and first["id"]!=31
    assert calls[:2]==[("copy", {"company_id":7}), ("write", {"code":"JCP1", "name":"Copy"})]
    assert source.code=="SRC" and source.name=="Journal"
    assert runtime._write_journal_processing(env, "journal.duplicate", params, 7, Failure)[1]
    with pytest.raises(Failure): runtime._write_journal_processing(env, "journal.duplicate", {**params,"name":"Other"}, 7, Failure)
    assert runtime._write_journal_processing(env, "journal.delete", {"journal_id":first["id"]}, 7, Failure)[0]["state"]=="deleted"
    with pytest.raises(Failure): runtime._write_journal_processing(env, "journal.delete", {"journal_id":first["id"]}, 7, Failure)
    second, replay = runtime._write_journal_processing(env, "journal.duplicate", params, 7, Failure)
    assert not replay and second["id"]!=first["id"] and records[31].present


@pytest.mark.parametrize("capability_id", [cap for cap in PARAMETERS if cap not in {"journal.duplicate", "journal.delete", "journal.group.delete"}])
def test_native_fixed_settings_replay_and_nullable_references(journals, capability_id):
    env, source, _, _, _ = journals
    value, replay = runtime._write_journal_processing(env, capability_id, PARAMETERS[capability_id], 7, Failure)
    assert value["id"]==31 and not replay
    assert runtime._write_journal_processing(env, capability_id, PARAMETERS[capability_id], 7, Failure)[1]
    field = "account_id" if capability_id.endswith("account.assign") else "report_id" if capability_id.endswith("template.assign") else None
    if field:
        params = {**PARAMETERS[capability_id],field:None}
        assert not runtime._write_journal_processing(env, capability_id, params, 7, Failure)[1]
        assert runtime._write_journal_processing(env, capability_id, params, 7, Failure)[1]
    assert source.code=="SRC"


def test_foreign_missing_bad_references_and_native_failure_roll_back(journals):
    env, source, journal_type, _, _ = journals
    foreign = journal_type(32,8)
    for cap, parameters in PARAMETERS.items():
        field = "journal_group_id" if cap=="journal.group.delete" else "journal_id"
        for record_id in (foreign.id,999):
            with pytest.raises(Failure): runtime._write_journal_processing(env, cap, {**parameters,field:record_id}, 7, Failure)
    for cap,params in (("journal.non_deductible_account.assign",{"journal_id":31,"account_id":999}),
                       ("journal.invoice_template.assign",{"journal_id":31,"report_id":999})):
        with pytest.raises(Failure): runtime._write_journal_processing(env, cap, params, 7, Failure)
    source.type="purchase"
    with pytest.raises(Failure): runtime._write_journal_processing(env,"journal.invoice_template.assign",PARAMETERS["journal.invoice_template.assign"],7,Failure)
    source.fail=True
    before=runtime._journal_processing_values(source)
    with pytest.raises(ValueError): runtime._write_journal_processing(env,"journal.invoice_reference.update",PARAMETERS["journal.invoice_reference.update"],7,Failure)
    assert runtime._journal_processing_values(source)==before
    source.used=True
    with pytest.raises(ValueError): runtime._write_journal_processing(env,"journal.delete",{"journal_id":31},7,Failure)
    assert source.present


def test_group_delete_and_archived_source_copy(journals):
    env, source, journal_type, _, _ = journals
    group=journal_type(61)
    value,replay=runtime._write_journal_processing(env,"journal.group.delete",{"journal_group_id":61},7,Failure)
    assert value["model"]=="account.journal.group" and value["state"]=="deleted" and not replay and not group.present and source.present
    source.active=False
    value,replay=runtime._write_journal_processing(env,"journal.duplicate",PARAMETERS["journal.duplicate"],7,Failure)
    assert not replay and value["state"]=="archived"
