from __future__ import annotations

import io
import json

import pytest
from test_fiscal_mapping_writes import request

from odoo_accounting_cli_v4 import analytic_processing_contracts as contracts
from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4.bridge import core_object_reads_runtime as reads
from odoo_accounting_cli_v4.bridge import core_writes_runtime as writes
from odoo_accounting_cli_v4.capabilities import core_object_reads, core_writes
from odoo_accounting_cli_v4.registry import load_registry

PARAMETERS = {
    "analytic.account.duplicate": {"analytic_account_id": 31, "name": "Analytic copy"},
    "analytic.account.delete": {"analytic_account_id": 31},
    "analytic.applicability.delete": {"applicability_id": 31},
    "analytic.distribution_model.delete": {"distribution_model_id": 31},
}
READ_PARAMETERS = {
    contracts.BALANCE_ID: {"analytic_account_id": 31, "date_from": "2026-01-01", "date_to": "2026-12-31"},
    contracts.USAGE_ID: {"analytic_account_id": 31},
    contracts.APPLICABILITY_ID: {"plan_id": 31, "business_domain": "bill", "account_id": None, "product_id": None},
    contracts.DISTRIBUTION_ID: {"account_id": None, "partner_id": None, "product_id": None},
}


@pytest.fixture(scope="module")
def registry():
    return load_registry()


def read_item(capability_id, record_id=31):
    item = {"id": record_id, "company_id": 7}
    if capability_id == contracts.BALANCE_ID:
        return {**item, "currency_id": 1, "date_from": "2026-01-01", "date_to": "2026-12-31",
                "debit": "45", "credit": "100", "balance": "55"}
    if capability_id == contracts.USAGE_ID:
        return {**item, "invoice_count": 2, "vendor_bill_count": 1}
    if capability_id == contracts.APPLICABILITY_ID:
        return {**item, "applicability": "mandatory"}
    return {"id": 7, "company_id": 7, "analytic_distribution": {"41": "100"}}


def result(capability_id, parameters):
    duplicate = capability_id.endswith("duplicate")
    return {"model": contracts.MODELS[capability_id], "id": 91 if duplicate else 31,
            "name": parameters["name"] if duplicate else None, "state": "active" if duplicate else "deleted",
            "company_id": 7, "move_type": None, "source_id": 31 if duplicate else None, "line_ids": [],
            "partial_reconcile_ids": [], "full_reconcile_id": None, "reconciled": False}


@pytest.mark.parametrize("capability_id", PARAMETERS)
def test_closed_write_cli_schema_key_and_result_binding(capability_id, registry, monkeypatch):
    params = PARAMETERS[capability_id]
    req = request(params)
    key = contracts.idempotency_key(capability_id, params, 7)
    registry.validate_instance(f"schemas/v1/{capability_id}.request.schema.json", req)
    assert writes._valid_parameters(capability_id, params, 7)
    assert key == writes._deterministic_key(capability_id, params, 7) == core_writes._expected_idempotency_key(capability_id, params, 7)
    expected = result(capability_id, params)

    class Port:
        user_id = 42

        def execute(self, **payload):
            assert payload["parameters"] == params and payload["confirmation"] == capability_id and payload["idempotency_key"] == key
            return {"user_id": 42, "company_visible": True, "module_installed": True, "access_allowed": True,
                    "idempotent_replay": False, "result": expected}

    monkeypatch.setattr(cli, "load_registry", lambda: registry)
    stdout, stderr = io.StringIO(), io.StringIO()
    assert cli.main(["write", "run", capability_id, "--request", "-", "--confirm", capability_id, "--idempotency-key", key],
                    stdin=io.StringIO(json.dumps(req)), stdout=stdout, stderr=stderr, port_factory=lambda *args: Port()) == 0
    response = json.loads(stdout.getvalue())
    registry.validate_instance(f"schemas/v1/{capability_id}.response.schema.json", response)
    assert not stderr.getvalue()
    for field, value in (("id", 31 if capability_id.endswith("duplicate") else 99), ("company_id", 8),
                         ("model", "account.move"), ("source_id", 99), ("line_ids", [99])):
        with pytest.raises(core_writes.CoreWriteError):
            core_writes._validate_result(capability_id, params, {**expected, field: value}, company_id=7, idempotent_replay=False)
    if capability_id.endswith("delete"):
        with pytest.raises(core_writes.CoreWriteError):
            core_writes._validate_result(capability_id, params, expected, company_id=7, idempotent_replay=True)


@pytest.mark.parametrize("capability_id", READ_PARAMETERS)
def test_closed_native_read_cli_and_query_binding(capability_id, registry, monkeypatch):
    req = request(READ_PARAMETERS[capability_id])
    registry.validate_instance(f"schemas/v1/{capability_id}.request.schema.json", req)
    assert reads._valid_parameters(capability_id, req["parameters"])
    item = read_item(capability_id)

    class Port:
        user_id = 42

        def read(self, **payload):
            assert payload["parameters"] == req["parameters"] and payload["company_id"] == 7
            return {"user_id": 42, "company_visible": True, "module_installed": True, "access_allowed": True,
                    "cursor_found": True, "items": [item]}

    monkeypatch.setattr(cli, "load_registry", lambda: registry)
    stdout, stderr = io.StringIO(), io.StringIO()
    assert cli.main(["read", capability_id, "--request", "-"], stdin=io.StringIO(json.dumps(req)),
                    stdout=stdout, stderr=stderr, port_factory=lambda *args: Port()) == 0
    response = json.loads(stdout.getvalue())
    registry.validate_instance(f"schemas/v1/{capability_id}.response.schema.json", response)
    if capability_id == contracts.DISTRIBUTION_ID:
        assert response["odoo"]["model"] == "res.company" and response["odoo"]["record_ids"] == [7]
    assert not stderr.getvalue()
    for field, value in (("id", 99), ("company_id", 8)):
        original = item[field]
        item[field] = value
        with pytest.raises(core_object_reads.CoreObjectReadError):
            core_object_reads.read_core_object(capability_id, Port(), req)
        item[field] = original
    if capability_id == contracts.BALANCE_ID:
        item["date_from"] = None
        with pytest.raises(core_object_reads.CoreObjectReadError):
            core_object_reads.read_core_object(capability_id, Port(), req)


@pytest.mark.parametrize("capability_id,changes", [
    ("analytic.account.duplicate", {"name": " "}),
    ("analytic.account.duplicate", {"name": []}),
    ("analytic.account.delete", {"analytic_account_id": True}),
    ("analytic.applicability.delete", {"applicability_id": None}),
    (contracts.BALANCE_ID, {"date_from": "2026-02-30"}),
    (contracts.BALANCE_ID, {"date_from": "2027-01-01"}),
    (contracts.APPLICABILITY_ID, {"business_domain": []}),
    (contracts.APPLICABILITY_ID, {"business_domain": "custom"}),
    (contracts.DISTRIBUTION_ID, {"product_id": False}),
])
def test_invalid_closed_parameters_fail_before_runtime(capability_id, changes):
    params = {**(READ_PARAMETERS if capability_id in contracts.READ_IDS else PARAMETERS)[capability_id], **changes}
    with pytest.raises(ValueError):
        contracts.normalize_parameters(capability_id, params)


def test_native_zero_percentage_empty_distribution_and_no_new_plan_mutators():
    assert contracts.valid_read_item(contracts.DISTRIBUTION_ID, {"id": 7, "company_id": 7, "analytic_distribution": {}}, 7)
    assert contracts.valid_read_item(contracts.DISTRIBUTION_ID, {"id": 7, "company_id": 7, "analytic_distribution": {"41": "0"}}, 7)
    assert not contracts.valid_read_item(contracts.DISTRIBUTION_ID, {"id": 7, "company_id": 7, "analytic_distribution": {"41": "101"}}, 7)
    assert not any(cap.startswith("analytic.plan.") for cap in contracts.CAPABILITY_IDS)
