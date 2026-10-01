from __future__ import annotations

import io
import json
import sys
from contextlib import contextmanager
from copy import deepcopy
from types import SimpleNamespace

import pytest
from test_core_writes_runtime import Env, Failure, _payload
from test_fiscal_mapping_writes import request
from test_payment_term_processing_batch import Rows

from odoo_accounting_cli_v4 import account_processing_contracts as contracts
from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4.bridge import core_object_reads_runtime as reads
from odoo_accounting_cli_v4.bridge import core_writes_runtime as runtime
from odoo_accounting_cli_v4.capabilities import core_writes
from odoo_accounting_cli_v4.registry import load_registry

PARAMETERS = {
    "account.account.duplicate": {"account_id": 31, "code": "V4A.copy", "name": "Copy"},
    "account.account.delete": {"account_id": 31},
    "account.account.default_taxes.assign": {"account_id": 31, "tax_ids": [42, 41]},
    "account.account.tags.assign": {"account_id": 31, "tag_ids": [52, 51]},
    "account.account.notes.update": {"account_id": 31, "changes": {"description": "Description", "note": None}},
    "account.account.non_trade.set": {"account_id": 31, "non_trade": True},
    "account.group.delete": {"account_group_id": 61},
}


def result(capability_id, parameters):
    duplicate = capability_id.endswith("duplicate")
    group = capability_id == "account.group.delete"
    deleted = capability_id.endswith("delete")
    return {"model": "account.group" if group else "account.account", "id": 91 if duplicate else parameters.get("account_id", 61),
            "name": parameters["name"] if duplicate else "Account", "state": "deleted" if deleted else "active", "company_id": 7,
            "move_type": None, "source_id": parameters["account_id"] if duplicate else None, "line_ids": [],
            "partial_reconcile_ids": [], "full_reconcile_id": None, "reconciled": False}


def read_item(capability_id=contracts.GET_ID, record_id=31):
    assert capability_id == contracts.GET_ID
    return {"id": record_id, "company_id": 7, "company_ids": [7], "active": True, "description": None, "note": "Native",
            "non_trade": False, "used": True, "currency_id": None, "company_currency_id": 6, "tax_ids": [41, 42], "tag_ids": [51],
            "group_id": 61, "include_initial_balance": True, "internal_group": "asset", "related_taxes_amount": 2, "current_balance": "-10"}


@pytest.fixture(scope="module")
def registry():
    return load_registry()


@pytest.fixture(autouse=True)
def native_domain(monkeypatch):
    class Domain:
        def __init__(self, *condition): self.conditions = [condition]
        def __and__(self, other):
            result = Domain()
            result.conditions = self.conditions + other.conditions
            return result
    monkeypatch.setitem(sys.modules, "odoo.fields", SimpleNamespace(Domain=Domain))


@pytest.mark.parametrize("capability_id", PARAMETERS)
def test_public_cli_schemas_hashes_and_result_ownership(capability_id, registry, monkeypatch):
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
    invalid_id = params["account_id"] if capability_id.endswith("duplicate") else 999
    for field, value in (("id", invalid_id), ("company_id", 8), ("model", "account.move"), ("source_id", 999), ("line_ids", [999])):
        with pytest.raises(core_writes.CoreWriteError):
            core_writes._validate_result(capability_id, params, {**expected, field: value}, company_id=7, idempotent_replay=False)
    if capability_id.endswith("delete"):
        with pytest.raises(core_writes.CoreWriteError):
            core_writes._validate_result(capability_id, params, expected, company_id=7, idempotent_replay=True)


def test_public_read_normalizes_native_relations_and_balance(registry, monkeypatch):
    item = read_item()
    class Port:
        user_id = 42
        def read(self, **payload):
            assert payload["parameters"] == {"account_id": 31}
            return {"user_id": 42, "company_visible": True, "module_installed": True, "access_allowed": True, "cursor_found": True, "items": [item]}
    monkeypatch.setattr(cli, "load_registry", lambda: registry)
    stdout, stderr = io.StringIO(), io.StringIO()
    assert cli.main(["read", contracts.GET_ID, "--request", "-"], stdin=io.StringIO(json.dumps(request({"account_id": 31}))),
                    stdout=stdout, stderr=stderr, port_factory=lambda *args: Port()) == 0, stdout.getvalue()
    registry.validate_instance(f"schemas/v1/{contracts.GET_ID}.response.schema.json", json.loads(stdout.getvalue()))
    assert not stderr.getvalue()
    raw = {field: [value, "Native"] if field.endswith("_id") and value is not None else False if value is None else value
           for field, value in item.items() if field != "company_id"}
    raw.update(tax_ids=[42, 41], current_balance=-10.0)
    assert reads._normalize_account_processing([raw], 7) == [item]
    for changes in ({"company_ids": [8]}, {"company_id": True}, {"related_taxes_amount": True}, {"internal_group": []}):
        assert not contracts.valid_read_item({**item, **changes}, 7)
    assert contracts.valid_read_item({**item, "internal_group": "off"}, 7)


@pytest.mark.parametrize("capability_id", PARAMETERS)
@pytest.mark.parametrize("denial", ["group", "acl"])
def test_access_denial_precedes_native_write(capability_id, denial, monkeypatch):
    env = Env()
    if denial == "group": env.denied_group = runtime._GROUPS[capability_id]
    else: env.denied_access = next(pair for pair in sorted(runtime._ACCESS[capability_id]) if pair[1] != "read")
    monkeypatch.setattr(runtime, "_dispatch_allowed", lambda *args: pytest.fail("denied mutation dispatched"))
    payload = _payload(capability_id, contracts.normalize_parameters(capability_id, PARAMETERS[capability_id]))
    payload["idempotency_key"] = contracts.idempotency_key(capability_id, payload["parameters"], 7)
    assert runtime.dispatch(env, payload, 7, failure_type=Failure)["access_allowed"] is False


@pytest.mark.parametrize("capability_id,changes", [
    ("account.account.duplicate", {"code": "INVALID SPACE"}), ("account.account.duplicate", {"name": " Copy "}),
    ("account.account.default_taxes.assign", {"tax_ids": [1, 1]}), ("account.account.tags.assign", {"tag_ids": [True]}),
    ("account.account.notes.update", {"changes": {}}), ("account.account.notes.update", {"changes": {"sudo": True}}),
    ("account.account.notes.update", {"changes": {"note": False}}), ("account.account.notes.update", {"changes": {"note": "a" * 4097}}),
    ("account.account.non_trade.set", {"non_trade": 1}), ("account.group.delete", {"account_group_id": True}),
])
def test_invalid_closed_parameters(capability_id, changes):
    with pytest.raises(ValueError): contracts.normalize_parameters(capability_id, {**PARAMETERS[capability_id], **changes})


def test_ids_are_canonical_without_input_mutation_and_empty_notes_clear():
    for cap in ("account.account.tags.assign", "account.account.default_taxes.assign"):
        original = deepcopy(PARAMETERS[cap])
        normalized = contracts.normalize_parameters(cap, original)
        field = "tag_ids" if "tags" in cap else "tax_ids"
        assert normalized[field] == sorted(original[field]) and original == PARAMETERS[cap]
        assert contracts.normalize_parameters(cap, {**original, field: []})[field] == []
    assert contracts.normalize_parameters("account.account.notes.update", {"account_id": 31, "changes": {"note": ""}})["changes"] == {"note": None}


def test_read_refreshes_nonstored_native_fields_after_journal_changes():
    item = read_item()
    calls = []
    class Model:
        def with_context(self, **context):
            assert context == {"active_test": False, "allowed_company_ids": [7]}
            return self
        def search(self, domain, **kwargs):
            assert domain == [("id", "=", 31), ("company_ids", "in", [7])] and kwargs == {"limit": 1}
            return self
        def invalidate_recordset(self, fields):
            assert fields == ["used", "current_balance", "related_taxes_amount", "group_id"]
            calls.append("refresh")
        def read(self, fields):
            assert calls == ["refresh"] and fields == list(contracts.GET_FIELDS)
            return [item]
    assert reads._raw_get_rows({"account.account": Model()}, contracts.GET_ID, 7, {"account_id": 31}) == [item]


@pytest.fixture
def accounts(monkeypatch):
    records, writes = {}, []
    class Account:
        def __init__(self, record_id, company_ids=(7,)):
            self.actual_company_ids = company_ids
            self.id, self.company_ids, self.name, self.code = record_id, Rows([SimpleNamespace(id=7)] if 7 in company_ids else []), "Account", "V4A"
            self.active, self.account_type, self.reconcile, self.currency_id = True, "income", False, SimpleNamespace(id=False)
            self.tax_ids, self.tag_ids = Rows([]), Rows([])
            self.description, self.note, self.non_trade, self.present = False, "Native", False, True
            records[self.id] = self
        def copy(self, defaults):
            assert defaults["company_ids"] == [(6, 0, [7])] and defaults["code_mapping_ids"] == []
            target = Account(max(records) + 1)
            for field in contracts.COPY_FIELDS: setattr(target, field, deepcopy(getattr(self, field)))
            target.code, target.name = defaults["code"], defaults["name"]
            return target
        def write(self, values):
            writes.append(deepcopy(values))
            for field, value in values.items():
                if field in {"tag_ids", "tax_ids"}: value = Rows([SimpleNamespace(id=number) for number in value[0][2]])
                setattr(self, field, value)
            if self.note == "FAIL": raise ValueError("native constraint")
        def unlink(self): self.present = False
        def exists(self): return self.present
        def invalidate_recordset(self): pass
    class Cursor:
        @contextmanager
        def savepoint(self):
            before = {record_id: deepcopy(record.__dict__) for record_id, record in records.items()}
            try: yield
            except BaseException:
                for record_id in list(records):
                    if record_id not in before: del records[record_id]
                    else: records[record_id].__dict__.update(before[record_id])
                raise
    def find(env, model, domain, company_id, failure_type):
        record_id = next(term[2] for term in domain if term[0] == "id")
        record = records.get(record_id)
        if record is None or not record.present or company_id not in record.company_ids.ids:
            raise Failure("record_not_found", "missing scoped account", exit_code=4)
        return record
    class Model:
        def search_count(self, domain, *, limit):
            assert limit == 1
            condition, present, absent = domain.conditions
            assert condition[:2] == ("id", "=") and present == ("company_ids", "in", [7])
            assert absent[:2] == ("company_ids", "not any!") and absent[2].conditions == [("id", "!=", 7)]
            record = records.get(condition[2])
            return int(bool(record and record.present and set(record.actual_company_ids) == {7}))
        def search(self, domain, **kwargs):
            code = next(term[2] for term in domain if term[0] == "code")
            return Rows([record for record in records.values() if record.present and record.code == code and 7 in record.company_ids.ids])
    monkeypatch.setattr(runtime, "_search_one", find)
    monkeypatch.setattr(runtime, "_scoped", lambda *args: Model())
    monkeypatch.setattr(runtime, "_ensure_ids", lambda *args: None)
    return SimpleNamespace(cr=Cursor()), Account(31), Account, records, writes


def test_native_copy_replay_conflict_delete_and_fresh_recreation(accounts):
    env, source, _, records, _ = accounts
    params = PARAMETERS["account.account.duplicate"]
    value, replay = runtime._write_account_processing(env, "account.account.duplicate", params, 7, Failure)
    assert not replay and value["source_id"] == source.id and value["id"] != source.id
    assert runtime._write_account_processing(env, "account.account.duplicate", params, 7, Failure)[1]
    with pytest.raises(Failure): runtime._write_account_processing(env, "account.account.duplicate", {**params, "name": "Other"}, 7, Failure)
    target_id = value["id"]
    assert runtime._write_account_processing(env, "account.account.delete", {"account_id": target_id}, 7, Failure)[0]["state"] == "deleted"
    with pytest.raises(Failure): runtime._write_account_processing(env, "account.account.delete", {"account_id": target_id}, 7, Failure)
    new, replay = runtime._write_account_processing(env, "account.account.duplicate", params, 7, Failure)
    assert not replay and new["id"] != target_id and records[source.id].present


def test_shared_copy_is_isolated_but_shared_updates_are_denied(accounts):
    env, _, account_type, _, writes = accounts
    shared = account_type(32, (7, 8))
    result, replay = runtime._write_account_processing(env, "account.account.duplicate", {**PARAMETERS["account.account.duplicate"], "account_id": shared.id}, 7, Failure)
    assert not replay and result["source_id"] == 32 and shared.company_ids.ids == [7] and shared.actual_company_ids == (7, 8)
    for cap in ("account.account.notes.update", "account.account.delete"):
        with pytest.raises(Failure): runtime._write_account_processing(env, cap, {**PARAMETERS[cap], "account_id": 32}, 7, Failure)
    assert not writes and shared.present


def test_hidden_foreign_membership_cannot_replay_owned_copy_or_create(accounts):
    env, _, account_type, _, _ = accounts
    shared = account_type(32, (7, 8))
    shared.code, shared.name = "V4A.copy", "Copy"
    assert shared.company_ids.ids == [7]
    with pytest.raises(Failure) as error:
        runtime._write_account_processing(env, "account.account.duplicate", PARAMETERS["account.account.duplicate"], 7, Failure)
    assert error.value.code == "idempotency_conflict"
    with pytest.raises(Failure) as error:
        runtime._create_account_config(env, {"code": shared.code, "name": shared.name, "account_type": "income", "reconcile": False, "currency_id": None}, 7, Failure)
    assert error.value.code == "idempotency_conflict" and shared.actual_company_ids == (7, 8)


@pytest.mark.parametrize("capability_id", ["account.account.notes.update", "account.account.default_taxes.assign", "account.account.tags.assign", "account.account.non_trade.set"])
def test_fixed_native_updates_and_replays(capability_id, accounts):
    env, source, _, _, writes = accounts
    params = contracts.normalize_parameters(capability_id, PARAMETERS[capability_id])
    value, replay = runtime._write_account_processing(env, capability_id, params, 7, Failure)
    assert not replay and value["id"] == source.id and len(writes) == 1
    assert runtime._write_account_processing(env, capability_id, params, 7, Failure)[1] and len(writes) == 1


def test_native_failed_notes_patch_rolls_back_both_fields(accounts):
    env, source, _, _, _ = accounts
    with pytest.raises(ValueError): runtime._write_account_processing(env, "account.account.notes.update",
        {"account_id": 31, "changes": {"description": "Changed", "note": "FAIL"}}, 7, Failure)
    assert source.description is False and source.note == "Native"


def test_reference_preflight_happens_before_mutation(accounts, monkeypatch):
    env, source, _, _, writes = accounts
    def denied(*args): raise Failure("record_not_found", "foreign or wrong-applicability reference", exit_code=4)
    monkeypatch.setattr(runtime, "_ensure_ids", denied)
    with pytest.raises(Failure): runtime._write_account_processing(env, "account.account.default_taxes.assign", PARAMETERS["account.account.default_taxes.assign"], 7, Failure)
    assert not writes and not source.tax_ids
