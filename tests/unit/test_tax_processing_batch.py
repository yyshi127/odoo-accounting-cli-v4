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
from test_payment_term_processing_batch import Rows

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4 import tax_processing_contracts as contracts
from odoo_accounting_cli_v4.bridge import core_object_reads_runtime as reads
from odoo_accounting_cli_v4.bridge import core_writes_runtime as runtime
from odoo_accounting_cli_v4.capabilities import core_object_reads, core_writes
from odoo_accounting_cli_v4.registry import load_registry

LINE = {"sequence": 30, "repartition_type": "tax", "factor_percent": "0", "account_id": None, "tag_ids": [], "use_in_tax_closing": False}
PARAMETERS = {
    "tax.delete": {"tax_id": 31},
    "tax.repartition_pair.create": {"tax_id": 31, "invoice_line": LINE, "refund_line": LINE},
    "tax.repartition_pair.delete": {"tax_id": 31, "invoice_line_id": 43, "refund_line_id": 46},
    "tax.repartition_line.update": {"tax_id": 31, "line_id": 42, "changes": {"use_in_tax_closing": True}},
    "tax.repartition_lines.update": {"tax_id": 31, "lines": [{"line_id": 45, "changes": {"factor_percent": "100"}}, {"line_id": 42, "changes": {"factor_percent": "100"}}]},
    "tax.repartition_lines.resequence": {"tax_id": 31, "invoice_line_ids": [41, 42, 43], "refund_line_ids": [44, 45, 46]},
}


def result(capability_id, parameters):
    deleted = capability_id == "tax.delete"
    return {"model": "account.tax", "id": parameters["tax_id"], "name": "TAX", "state": "deleted" if deleted else "active", "company_id": 7,
            "move_type": None, "source_id": parameters.get("line_id"),
            "line_ids": [] if deleted else [41, 42, 44, 45] if capability_id.endswith("pair.delete") else [41, 42, 43, 44, 45, 46],
            "partial_reconcile_ids": [], "full_reconcile_id": None, "reconciled": False}


def read_item(capability_id=contracts.GET_ID, record_id=31):
    if capability_id == contracts.GET_ID:
        return {"id": record_id, "company_id": 7, "active": True, "tax_scope": None, "tax_exigibility": "on_invoice",
                "cash_basis_transition_account_id": None, "price_include_override": "tax_excluded", "price_include": False,
                "analytic": False, "is_used": False, "has_negative_factor": False, "children_tax_ids": [],
                "invoice_repartition_line_ids": [41, 42], "refund_repartition_line_ids": [44, 45], "country_id": 6}
    return {"id": record_id, "company_id": 7, "move_id": 20, "account_id": 8, "parent_state": "posted", "date": "2026-10-01",
            "name": None, "balance": "10", "amount_currency": "10", "currency_id": 6,
            "tax_line_id": 71, "group_tax_id": None, "tax_ids": [], "tax_repartition_line_id": 42}


@pytest.fixture(scope="module")
def registry():
    return load_registry()


@pytest.mark.parametrize("capability_id", PARAMETERS)
def test_public_cli_closed_schemas_hashes_and_result_ownership(capability_id, registry, monkeypatch):
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
    for field, value in (("id", 999), ("company_id", 8), ("model", "account.move"), ("source_id", 999)):
        with pytest.raises(core_writes.CoreWriteError):
            core_writes._validate_result(capability_id, params, {**expected, field: value}, company_id=7, idempotent_replay=False)


@pytest.mark.parametrize("capability_id", sorted(contracts.READ_IDS))
def test_public_read_and_scoped_native_normalization(capability_id, registry, monkeypatch):
    item = read_item(capability_id)
    params = {"tax_id": 31 if capability_id == contracts.GET_ID else 71}
    class Port:
        user_id = 42
        def read(self, **payload):
            assert payload["parameters"]["tax_id"] == params["tax_id"]
            return {"user_id": 42, "company_visible": True, "module_installed": True, "access_allowed": True, "cursor_found": True, "items": [item]}
    monkeypatch.setattr(cli, "load_registry", lambda: registry)
    stdout, stderr = io.StringIO(), io.StringIO()
    assert cli.main(["read", capability_id, "--request", "-"], stdin=io.StringIO(json.dumps(request(params))),
                    stdout=stdout, stderr=stderr, port_factory=lambda *args: Port()) == 0, stdout.getvalue()
    registry.validate_instance(f"schemas/v1/{capability_id}.response.schema.json", json.loads(stdout.getvalue()))
    assert not stderr.getvalue() and not contracts.valid_read_item(capability_id, {**item, "company_id": True}, 7)
    raw = {field: [value, "Native"] if field.endswith("_id") and value is not None else False if value is None else value for field, value in item.items()}
    if capability_id == contracts.LIST_ID: raw.update(date=date(2026, 10, 1), balance=10.0, amount_currency=10.0)
    assert reads._normalize_tax_processing(capability_id, [raw], 7) == [item]
    if capability_id == contracts.LIST_ID:
        item = {**item, "tax_line_id": 72}
        with pytest.raises(core_object_reads.CoreObjectReadError): core_object_reads.read_core_object(capability_id, Port(), request(params))


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


@pytest.mark.parametrize("changes", [{"sudo": True}, {"sequence": True}, {"sequence": 2147483648}, {"repartition_type": []},
    {"factor_percent": "NaN"}, {"factor_percent": "0.1234567890123"}, {"account_id": False}, {"tag_ids": [1, 1]}, {"use_in_tax_closing": 1}])
def test_invalid_closed_line_values(changes):
    with pytest.raises(ValueError): contracts.line_values({**LINE, **changes})


@pytest.mark.parametrize("amount", ["-100", "0", "100", "30.00", "0.000000000001"])
def test_native_signed_and_twelve_decimal_factors(amount, registry):
    params = {**PARAMETERS["tax.repartition_pair.create"], "invoice_line": {**LINE, "factor_percent": amount}}
    registry.validate_instance("schemas/v1/tax.repartition_pair.create.request.schema.json", request(params))
    expected = amount.rstrip("0").rstrip(".") if "." in amount else amount
    assert contracts.normalize_parameters("tax.repartition_pair.create", params)["invoice_line"]["factor_percent"] == expected


def test_atomic_normalization_is_canonical_without_mutation():
    params = deepcopy(PARAMETERS["tax.repartition_lines.update"])
    old = deepcopy(params)
    assert [entry["line_id"] for entry in contracts.normalize_parameters("tax.repartition_lines.update", params)["lines"]] == [42, 45]
    assert params == old
    for entries in ([params["lines"][0]], [params["lines"][0]] * 2):
        with pytest.raises(ValueError): contracts.normalize_parameters("tax.repartition_lines.update", {**params, "lines": entries})


def tax_fixture(monkeypatch):
    calls = []
    tax = SimpleNamespace(id=31, company_id=SimpleNamespace(id=7), country_id=SimpleNamespace(id=6), name="TAX", active=True,
                          repartition_line_ids=Rows(), invalidate_recordset=lambda: None)
    def make_line(row_id, kind, values):
        row = SimpleNamespace(id=row_id, **{**values, "document_type": kind})
        row.factor_percent = float(row.factor_percent)
        row.account_id = SimpleNamespace(id=values["account_id"]) if values["account_id"] else False
        row.tag_ids = SimpleNamespace(ids=values["tag_ids"])
        return row
    for row_id, kind, amount in ((41, "invoice", 100), (42, "invoice", 100), (44, "refund", 100), (45, "refund", 100)):
        tax.repartition_line_ids.append(make_line(row_id, kind, {**LINE, "sequence": 10 if row_id in {41, 44} else 20,
            "repartition_type": "base" if row_id in {41, 44} else "tax", "factor_percent": str(amount)}))
    def sides():
        for kind in ("invoice", "refund"): setattr(tax, f"{kind}_repartition_line_ids", tax.repartition_line_ids.filtered(lambda row, kind=kind: row.document_type == kind))
    sides()
    def write(values):
        calls.append(deepcopy(values))
        for op, row_id, data in values["repartition_line_ids"]:
            if op == 0:
                kind = data["document_type"]
                tax.repartition_line_ids.append(make_line(43 if kind == "invoice" else 46, kind, {**data, "tag_ids": data["tag_ids"][0][2], "account_id": data["account_id"] or None}))
            elif op == 2: tax.repartition_line_ids[:] = [row for row in tax.repartition_line_ids if row.id != row_id]
            else:
                row = next(row for row in tax.repartition_line_ids if row.id == row_id)
                for field, value in data.items():
                    if field == "factor_percent": value = float(value)
                    if field == "account_id": value = SimpleNamespace(id=value) if value else False
                    if field == "tag_ids": value = SimpleNamespace(ids=value[0][2])
                    setattr(row, field, value)
        sides()
    tax.write = write
    @contextmanager
    def savepoint():
        original = Rows(tax.repartition_line_ids)
        snapshot = {row.id: vars(row).copy() for row in original}
        try: yield
        except BaseException:
            tax.repartition_line_ids[:] = original
            for row in original: vars(row).update(snapshot[row.id])
            sides()
            raise
    env = SimpleNamespace(cr=SimpleNamespace(savepoint=savepoint), company=SimpleNamespace(multi_vat_foreign_country_ids=SimpleNamespace(ids=[])))
    def find(env, model, domain, company_id, failure_type):
        row_id = next(value for field, op, value in domain if field == "id")
        rows = tax.repartition_line_ids.filtered(lambda row: row.id == row_id)
        if not rows: raise Failure("record_not_found", "Missing native child", exit_code=4)
        return rows
    monkeypatch.setattr(runtime, "_tax_config_record", lambda *args: tax)
    monkeypatch.setattr(runtime, "_search_one", find)
    monkeypatch.setattr(runtime, "_ensure_ids", lambda *args: None)
    return env, tax, calls


def test_pair_create_replay_delete_preserves_existing_ids(monkeypatch):
    env, _tax, calls = tax_fixture(monkeypatch)
    value, replay = runtime._write_tax_processing(env, "tax.repartition_pair.create", PARAMETERS["tax.repartition_pair.create"], 7, Failure)
    assert not replay and value["line_ids"] == [41, 42, 43, 44, 45, 46]
    assert runtime._write_tax_processing(env, "tax.repartition_pair.create", PARAMETERS["tax.repartition_pair.create"], 7, Failure)[1]
    value, replay = runtime._write_tax_processing(env, "tax.repartition_pair.delete", PARAMETERS["tax.repartition_pair.delete"], 7, Failure)
    assert not replay and value["line_ids"] == [41, 42, 44, 45] and len(calls) == 2
    with pytest.raises(Failure): runtime._write_tax_processing(env, "tax.repartition_pair.delete", PARAMETERS["tax.repartition_pair.delete"], 7, Failure)


def test_atomic_preflights_every_child_before_any_write(monkeypatch):
    env, tax, calls = tax_fixture(monkeypatch)
    params = {"tax_id": 31, "lines": [{"line_id": 42, "changes": {"factor_percent": "30"}}, {"line_id": 999, "changes": {"factor_percent": "30"}}]}
    with pytest.raises(Failure): runtime._write_tax_processing(env, "tax.repartition_lines.update", params, 7, Failure)
    assert not calls and tax.repartition_line_ids.ids == [41, 42, 44, 45]


def test_native_constraint_exception_restores_all_fields(monkeypatch):
    env, tax, _ = tax_fixture(monkeypatch)
    original = [(row.id, runtime._normalized_tax_repartition_line(row)) for row in tax.repartition_line_ids]
    write = tax.write
    def reject(values):
        write(values)
        raise ValueError("simulated native constraint")
    tax.write = reject
    params = {"tax_id": 31, "line_id": 42, "changes": {"factor_percent": "30"}}
    with pytest.raises(ValueError): runtime._write_tax_processing(env, "tax.repartition_line.update", params, 7, Failure)
    assert [(row.id, runtime._normalized_tax_repartition_line(row)) for row in tax.repartition_line_ids] == original
