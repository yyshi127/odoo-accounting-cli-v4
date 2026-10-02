from __future__ import annotations

import hashlib
import io
import json
import math
from copy import deepcopy
from types import SimpleNamespace

import pytest
from test_company_processing_batch import result as config_result
from test_core_writes_runtime import Failure
from test_fiscal_mapping_writes import request
from test_journal_item_processing_batch import result as move_result

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4.bridge import core_writes_runtime as runtime
from odoo_accounting_cli_v4.capabilities import core_writes
from odoo_accounting_cli_v4.registry import load_registry

PARAMETERS = {
    "currency.rate.update": {"rate_id": 31, "changes": {"date": "2026-10-01", "company_units_per_foreign_unit": "7.123456"}},
    "currency.rate.delete": {"rate_id": 31},
    "bank.statement.update": {"statement_id": 31, "changes": {"transaction_ids": [42, 41]}},
    "bank.transaction.record": {"journal_id": 11, "date": "2026-10-01", "amount": "100", "payment_ref": "Foreign receipt", "partner_id": None, "foreign_currency_id": 6, "amount_currency": "90"},
    "bank.transaction.update": {"transaction_id": 31, "changes": {"foreign_currency_id": 6, "amount_currency": "-90", "amount": "-100"}},
    "invoice.update": {"move_id": 31, "changes": {"partner_bank_id": 51, "reference": "Corrected bank"}},
    "invoice.payment_method.assign": {"move_id": 31, "payment_method_line_id": 61},
    "invoice.incoterm.update": {"move_id": 31, "changes": {"incoterm_id": 71, "incoterm_location": "Shanghai"}},
}


def result(capability_id, parameters):
    if capability_id.startswith("currency.rate."):
        return {**config_result("", {}), "model": "res.currency.rate", "id": parameters["rate_id"],
                "name": parameters.get("changes", {}).get("date", "2026-10-01"), "source_id": 6,
                "state": "deleted" if capability_id.endswith("delete") else "active"}
    if capability_id == "bank.statement.update":
        return {**config_result("", {}), "model": "account.bank.statement", "id": parameters["statement_id"],
                "state": "complete", "line_ids": sorted(parameters["changes"]["transaction_ids"])}
    if capability_id.startswith("bank.transaction."):
        return {**move_result("", {"move_id": 31}), "model": "account.bank.statement.line", "state": "posted", "source_id": 81}
    return {**move_result(capability_id, parameters), "state": "posted", "move_type": "out_invoice", "partial_reconcile_ids": [91]}


@pytest.fixture(scope="module")
def registry():
    return load_registry()


@pytest.mark.parametrize("capability_id", PARAMETERS)
def test_public_cli_schema_confirmation_key_and_closed_native_binding(capability_id, registry, monkeypatch):
    params, expected = PARAMETERS[capability_id], result(capability_id, PARAMETERS[capability_id])
    req = request(params)
    normalized = core_writes.validate_core_write_request(capability_id, req)[2]
    expected_key = core_writes._expected_idempotency_key(capability_id, normalized, 7)
    assert expected_key == runtime._deterministic_key(capability_id, normalized, 7)
    key = expected_key or "maintenance:foreign-receipt:31"
    assert runtime._valid_parameters(capability_id, normalized, 7)
    registry.validate_instance(f"schemas/v1/{capability_id}.request.schema.json", req)

    class Port:
        user_id = 42

        def execute(self, **payload):
            assert payload["parameters"] == normalized and payload["company_id"] == 7
            assert payload["confirmation"] == capability_id and payload["idempotency_key"] == key
            return {"user_id": 42, "company_visible": True, "module_installed": True, "access_allowed": True,
                    "idempotent_replay": False, "result": expected}

    monkeypatch.setattr(cli, "load_registry", lambda: registry)
    stdout, stderr = io.StringIO(), io.StringIO()
    code = cli.main(["write", "run", capability_id, "--request", "-", "--confirm", capability_id, "--idempotency-key", key],
                    stdin=io.StringIO(json.dumps(req)), stdout=stdout, stderr=stderr, port_factory=lambda *args: Port())
    assert code == 0, stdout.getvalue()
    response = json.loads(stdout.getvalue())
    registry.validate_instance(f"schemas/v1/{capability_id}.response.schema.json", response)
    assert response["data"]["result"] == expected and not stderr.getvalue()
    for confirmation in (None, "other.operation"):
        with pytest.raises(core_writes.CoreWriteError):
            core_writes.execute_core_write(Port(), capability_id, req, key, confirmation)


@pytest.mark.parametrize("capability_id", PARAMETERS)
def test_result_rejects_wrong_company_model_target_and_additional_fields(capability_id):
    params, original = PARAMETERS[capability_id], result(capability_id, PARAMETERS[capability_id])
    changes = [("company_id", 8), ("model", "res.partner"), ("extra", True)]
    if capability_id != "bank.transaction.record":
        changes.append(("id", 99))
    for field, value in changes:
        with pytest.raises(core_writes.CoreWriteError):
            core_writes._validate_result(capability_id, params, {**original, field: value}, company_id=7, idempotent_replay=False)


@pytest.mark.parametrize("parameters", [
    {"rate_id": True, "changes": {"date": "2026-10-01"}}, {"rate_id": 0, "changes": {"date": "2026-10-01"}},
    {"rate_id": 31, "changes": {}}, {"rate_id": 31, "changes": {"date": "2026-02-30"}},
    {"rate_id": 31, "changes": {"company_units_per_foreign_unit": "0"}},
    {"rate_id": 31, "changes": {"company_units_per_foreign_unit": "-1"}},
    {"rate_id": 31, "changes": {"company_units_per_foreign_unit": 7.1}},
    {"rate_id": 31, "changes": {"company_units_per_foreign_unit": True}},
    {"rate_id": 31, "changes": {"company_units_per_foreign_unit": "NaN"}},
    {"rate_id": 31, "changes": {"currency_id": 6}}, {"rate_id": 31, "changes": {"company_id": 8}},
])
def test_rate_update_is_positive_date_typed_and_cannot_rehome(parameters):
    with pytest.raises(core_writes.CoreWriteError):
        core_writes.validate_core_write_request("currency.rate.update", request(parameters))


def test_rate_delete_missing_cannot_be_reported_as_successful_replay():
    cap, params = "currency.rate.delete", PARAMETERS["currency.rate.delete"]
    with pytest.raises(core_writes.CoreWriteError):
        core_writes._validate_result(cap, params, result(cap, params), company_id=7, idempotent_replay=True)
    for field, value in (("state", "active"), ("source_id", None)):
        with pytest.raises(core_writes.CoreWriteError):
            core_writes._validate_result(cap, params, {**result(cap, params), field: value}, company_id=7, idempotent_replay=False)


@pytest.mark.parametrize("capability_id", ["bank.transaction.record", "bank.transaction.update"])
@pytest.mark.parametrize("pair", [
    {"foreign_currency_id": 6}, {"amount_currency": "5"}, {"foreign_currency_id": True, "amount_currency": "5"},
    {"foreign_currency_id": 6, "amount_currency": "0"}, {"foreign_currency_id": None, "amount_currency": "5"},
    {"foreign_currency_id": 6, "amount_currency": 5}, {"foreign_currency_id": 6, "amount_currency": "NaN"},
])
def test_foreign_bank_currency_is_an_atomic_typed_nonzero_or_explicit_clear_pair(capability_id, pair):
    parameters = deepcopy(PARAMETERS[capability_id])
    values = parameters if capability_id.endswith("record") else parameters["changes"]
    values.pop("foreign_currency_id")
    values.pop("amount_currency")
    values.update(pair)
    with pytest.raises(core_writes.CoreWriteError):
        core_writes.validate_core_write_request(capability_id, request(parameters))


@pytest.mark.parametrize("capability_id", ["bank.transaction.record", "bank.transaction.update"])
def test_foreign_pair_clear_and_omission_keep_legacy_parameters_and_key(capability_id):
    parameters = deepcopy(PARAMETERS[capability_id])
    values = parameters if capability_id.endswith("record") else parameters["changes"]
    values.pop("foreign_currency_id")
    values.pop("amount_currency")
    legacy = core_writes.validate_core_write_request(capability_id, request(parameters))[2]
    legacy_values = legacy if capability_id.endswith("record") else legacy["changes"]
    assert "foreign_currency_id" not in legacy_values and "amount_currency" not in legacy_values
    digest_values = legacy if capability_id.endswith("record") else legacy["changes"]
    digest = hashlib.sha256(json.dumps(digest_values, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:32]
    expected = f"{capability_id}:{7 if capability_id.endswith('record') else 31}:{digest}"
    expected = None if capability_id.endswith("record") else expected
    assert core_writes._expected_idempotency_key(capability_id, legacy, 7) == expected
    assert runtime._deterministic_key(capability_id, legacy, 7) == expected
    values.update(foreign_currency_id=None, amount_currency="0")
    cleared = core_writes.validate_core_write_request(capability_id, request(parameters))[2]
    assert runtime._valid_parameters(capability_id, cleared, 7)


@pytest.mark.parametrize("ids", [[], [True], [0], [41, 41], list(range(1, 102)), None])
def test_statement_membership_is_nonempty_unique_typed_and_bounded(ids):
    with pytest.raises(core_writes.CoreWriteError):
        core_writes.validate_core_write_request("bank.statement.update", request({"statement_id": 31, "changes": {"transaction_ids": ids}}))


def test_statement_membership_normalizes_copy_and_binds_exact_result_ids():
    cap, params = "bank.statement.update", deepcopy(PARAMETERS["bank.statement.update"])
    normalized = core_writes.validate_core_write_request(cap, request(params))[2]
    assert normalized["changes"]["transaction_ids"] == [41, 42] and params["changes"]["transaction_ids"] == [42, 41]
    with pytest.raises(core_writes.CoreWriteError):
        core_writes._validate_result(cap, normalized, {**result(cap, params), "line_ids": [41]}, company_id=7, idempotent_replay=False)


@pytest.mark.parametrize("capability_id", ["invoice.update", "invoice.payment_method.assign", "invoice.incoterm.update"])
def test_posted_metadata_accepts_native_graph_types_but_not_cancelled_or_financial_changes(capability_id):
    params = PARAMETERS[capability_id]
    expected = {**result(capability_id, params), "full_reconcile_id": 92, "reconciled": True}
    for replay in (False, True):
        assert core_writes._validate_result(capability_id, params, expected, company_id=7, idempotent_replay=replay) == expected
    with pytest.raises(core_writes.CoreWriteError):
        core_writes._validate_result(capability_id, params, {**expected, "state": "cancel"}, company_id=7, idempotent_replay=False)
    if capability_id == "invoice.update":
        with pytest.raises(core_writes.CoreWriteError):
            core_writes._validate_result(capability_id, {"move_id": 31, "changes": {"date": "2026-10-01"}}, expected, company_id=7, idempotent_replay=False)


def test_rate_branch_is_denied_before_target_lookup_and_root_lookup_is_exact(monkeypatch):
    monkeypatch.setattr(runtime, "_root_company_id", lambda *args: 1)
    monkeypatch.setattr(runtime, "_search_one", lambda *args: pytest.fail("branch must not resolve or mutate a root-owned target"))
    with pytest.raises(Failure) as caught:
        runtime._owned_currency_rate(None, 31, 7, Failure)
    assert caught.value.code == "company_unavailable" and caught.value.exit_code == 3
    monkeypatch.setattr(runtime, "_root_company_id", lambda *args: 7)
    calls, record = [], object()
    monkeypatch.setattr(runtime, "_search_one", lambda env, model, domain, *args: calls.append((model, domain)) or record)
    assert runtime._owned_currency_rate(None, 31, 7, Failure) is record
    assert calls == [("res.currency.rate", [("id", "=", 31), ("company_id", "=", 7)])]


class _RateCompany:
    id = 7

    def __init__(self):
        self.root_id = self

    def __or__(self, other):
        assert other is self
        return (self,)


def test_rate_native_patch_writes_only_date_and_inverse_quote_then_current_state_replay(monkeypatch):
    cap, params = "currency.rate.update", PARAMETERS["currency.rate.update"]
    writes, company, base = [], _RateCompany(), 2.0
    record = SimpleNamespace(id=31, company_id=company, currency_id=SimpleNamespace(id=6), env=SimpleNamespace(company=company),
                             name="2026-09-30", rate=(1.0 / 7.125) * base, inverse_company_rate=7.125, invalidate_recordset=lambda: None,
                             _get_last_rates_for_companies=lambda companies: {company: base})

    def write(values):
        writes.append(values)
        for key, value in values.items():
            setattr(record, key, value)
        if "inverse_company_rate" in values:
            record.rate = (1.0 / float(values["inverse_company_rate"])) * base
            record.inverse_company_rate = 1.0 / (record.rate / base)

    record.write = write
    monkeypatch.setattr(runtime, "_owned_currency_rate", lambda *args: record)
    monkeypatch.setattr(runtime, "_scoped", lambda *args: SimpleNamespace(search=lambda *args, **kwargs: []))
    monkeypatch.setattr(runtime, "_currency_rate_result", lambda *args: result(cap, params))
    assert runtime._update_currency_rate(None, params, 7, Failure)[1] is False
    assert set(writes[0]) == {"name", "inverse_company_rate"} and str(writes[0]["inverse_company_rate"]) == "7.123456"
    assert runtime._update_currency_rate(None, params, 7, Failure)[1] is True and len(writes) == 1
    assert record.currency_id.id == 6 and record.company_id.id == 7


def test_rate_float_reciprocal_drift_accepts_exact_native_technical_chain_and_nonunit_base_replay(monkeypatch):
    cap, params = "currency.rate.update", {"rate_id": 31, "changes": {"company_units_per_foreign_unit": "7.123456"}}
    company, base, calls = _RateCompany(), 2.0, []
    technical = (1.0 / float(params["changes"]["company_units_per_foreign_unit"])) * base

    def last_rates(companies):
        calls.append(companies)
        assert companies == (company,)
        return {company: base}

    record = SimpleNamespace(rate=technical, inverse_company_rate=1.0 / (technical / base), company_id=company,
                             env=SimpleNamespace(company=company), _get_last_rates_for_companies=last_rates,
                             write=lambda values: pytest.fail("exact native technical value must replay without another write"))
    assert str(record.inverse_company_rate) == "7.123455999999999"
    monkeypatch.setattr(runtime, "_owned_currency_rate", lambda *args: record)
    monkeypatch.setattr(runtime, "_currency_rate_result", lambda *args: result(cap, params))
    assert runtime._update_currency_rate(None, params, 7, Failure)[1] is True
    assert calls == [(company,)]


def test_rate_postwrite_different_technical_value_even_one_ulp_is_rejected(monkeypatch):
    params = {"rate_id": 31, "changes": {"company_units_per_foreign_unit": "7.123456"}}
    company, base, writes = _RateCompany(), 2.0, []
    expected = (1.0 / float(params["changes"]["company_units_per_foreign_unit"])) * base
    wrong = math.nextafter(expected, math.inf)
    record = SimpleNamespace(id=31, name="2026-10-01", rate=wrong, inverse_company_rate=7.123456,
                             company_id=company, currency_id=SimpleNamespace(id=6), env=SimpleNamespace(company=company),
                             invalidate_recordset=lambda: None, _get_last_rates_for_companies=lambda companies: {company: base})

    def write(values):
        writes.append(values)
        record.rate = wrong  # Deliberately simulate an incorrect native persisted value despite the protected inverse cache.
        record.inverse_company_rate = float(values["inverse_company_rate"])

    record.write = write
    monkeypatch.setattr(runtime, "_owned_currency_rate", lambda *args: record)
    monkeypatch.setattr(runtime, "_currency_rate_result", lambda *args: pytest.fail("different technical value must not be accepted"))
    with pytest.raises(Failure) as caught:
        runtime._update_currency_rate(None, params, 7, Failure)
    assert caught.value.code == "odoo_write_error" and caught.value.exit_code == 6
    assert wrong != expected and len(writes) == 1


@pytest.mark.parametrize("same_currency,amount", [(True, "90"), (False, "89")])
def test_bank_record_pair_replay_rejects_same_native_currency_or_stored_pair_drift(monkeypatch, same_currency, amount):
    class Existing(SimpleNamespace):
        def __len__(self):
            return 1

    params = PARAMETERS["bank.transaction.record"]
    existing = Existing(invoice_origin="marker", move_id=SimpleNamespace(state="posted"), foreign_currency_id=SimpleNamespace(id=6), amount_currency=amount)
    monkeypatch.setattr(runtime, "_scoped", lambda *args: SimpleNamespace(search=lambda *args, **kwargs: existing))
    monkeypatch.setattr(runtime, "_ensure_ids", lambda *args: None)
    monkeypatch.setattr(runtime, "_statement_currency", lambda *args: SimpleNamespace(id=6 if same_currency else 10))
    monkeypatch.setattr(runtime, "_bank_transaction_result", lambda *args: pytest.fail("invalid explicit pair must not be accepted as replay"))
    with pytest.raises(Failure) as caught:
        runtime._record_bank_transaction(None, params, 7, "caller-key", "marker", Failure)
    assert (caught.value.code, caught.value.exit_code) == (("business_rule_error", 6) if same_currency else ("idempotency_conflict", 5))


def test_bank_pair_update_same_native_currency_denied_before_unchanged_state_replay(monkeypatch):
    record = SimpleNamespace()
    params = {"transaction_id": 31, "changes": {"foreign_currency_id": 6, "amount_currency": "90"}}
    monkeypatch.setattr(runtime, "_bank_transaction", lambda *args: record)
    monkeypatch.setattr(runtime, "_bank_is_default_unmatched", lambda *args: True)
    monkeypatch.setattr(runtime, "_bank_transaction_actual_values", lambda *args, **kwargs: {"partner_id": None, "amount": "100", **params["changes"]})
    monkeypatch.setattr(runtime, "_ensure_ids", lambda *args: None)
    monkeypatch.setattr(runtime, "_statement_currency", lambda *args: SimpleNamespace(id=6))
    monkeypatch.setattr(runtime, "_bank_transaction_result", lambda *args: pytest.fail("native-invalid pair must be denied before replay"))
    with pytest.raises(Failure) as caught:
        runtime._update_bank_transaction(None, params, 7, Failure)
    assert caught.value.code == "business_rule_error" and caught.value.exit_code == 6


def test_sent_invoice_bank_update_denied_before_current_state_replay(monkeypatch):
    params = {"move_id": 31, "changes": {"partner_bank_id": None}}
    monkeypatch.setattr(runtime, "_lifecycle_move", lambda *args: SimpleNamespace(state="posted", is_move_sent=True))
    monkeypatch.setattr(runtime, "_validate_invoice_update_references", lambda *args: None)
    monkeypatch.setattr(runtime, "_current_invoice_changes", lambda *args: params["changes"])
    monkeypatch.setattr(runtime, "_move_result", lambda *args: pytest.fail("sent bank mutation cannot be accepted even when unchanged"))
    with pytest.raises(Failure) as caught:
        runtime._update_move(None, "invoice.update", params, 7, Failure)
    assert caught.value.code == "state_conflict" and caught.value.exit_code == 5
