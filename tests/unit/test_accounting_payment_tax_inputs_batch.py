"""Public CLI/schema wiring; detailed SDK/runtime contracts have separate focused tests."""

from __future__ import annotations

import io
import json
from copy import deepcopy

import pytest
from test_core_object_reads import _item
from test_fiscal_mapping_writes import request
from test_journal_item_processing_batch import read_item

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4.capabilities import core_writes
from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry

TAX = {"tax_ids": [61], "tax_tag_ids": [71], "tax_repartition_line_id": 81, "tax_base_amount": "-100.50"}
LINES = [{"name": "Debit", "account_id": 51, "partner_id": None, "debit": "100", "credit": "0", **TAX},
         {"name": "Credit", "account_id": 52, "partner_id": None, "debit": "0", "credit": "100"}]
PARAMETERS = {
    "receivable.payment.register": {"move_id": 31, "journal_id": 11, "payment_date": "2026-10-02", "payment_method_line_id": 91, "partner_bank_id": 101},
    "payable.payment.register": {"move_ids": [31, 32], "journal_id": 11, "payment_date": "2026-10-02", "payment_method_line_id": 92, "partner_bank_id": 102},
    "journal_entry.create": {"journal_id": 11, "date": "2026-10-02", "lines": LINES},
    "journal_entry.lines.replace": {"move_id": 31, "lines": LINES},
    "journal_entry.lines.update": {"move_id": 31, "lines": [{"line_id": 41, "changes": {**TAX, "tax_base_amount": "-100.5"}}]},
    "journal_entry.lines.add": {"move_id": 31, "expected_line_ids": [41, 42], "lines": LINES},
}
READ_PARAMETERS = {"journal_item.get": {"line_id": 41}, "journal_item.search": {"move_id": 301, "limit": 1},
                   "journal_item.processing_details.get": {"journal_item_id": 41}}


@pytest.fixture(scope="module")
def registry():
    return load_registry()


def result(capability_id):
    payment = capability_id.endswith("payment.register")
    return {"model": "account.payment" if payment else "account.move", "id": 31, "name": "TEST/31",
            "state": "in_process" if payment else "draft", "company_id": 7, "move_type": None if payment else "entry",
            "source_id": None if "move_ids" in PARAMETERS[capability_id] else 31 if payment else None,
            "line_ids": [41, 42, 43, 44] if capability_id.endswith(".add") else [41, 42],
            "partial_reconcile_ids": [111] if payment else [], "full_reconcile_id": None,
            "reconciled": payment and "move_ids" in PARAMETERS[capability_id]}


@pytest.mark.parametrize("capability_id", PARAMETERS)
def test_extended_write_public_cli_closed_schema_confirmation_and_result(capability_id, registry, monkeypatch):
    params, expected = deepcopy(PARAMETERS[capability_id]), result(capability_id)
    req = request(params)
    normalized = core_writes.validate_core_write_request(capability_id, req)[2]
    key = core_writes._expected_idempotency_key(capability_id, normalized, 7) or "payment-tax:caller-key"
    registry.validate_instance(f"schemas/v1/{capability_id}.request.schema.json", req)

    class Port:
        user_id = 42

        def execute(self, **payload):
            assert payload["parameters"] == normalized and payload["confirmation"] == capability_id
            assert payload["idempotency_key"] == key and payload["company_id"] == 7
            return {"user_id": 42, "company_visible": True, "module_installed": True, "access_allowed": True,
                    "idempotent_replay": False, "result": expected}

    monkeypatch.setattr(cli, "load_registry", lambda: registry)
    stdout, stderr = io.StringIO(), io.StringIO()
    code = cli.main(["write", "run", capability_id, "--request", "-", "--confirm", capability_id, "--idempotency-key", key],
                    stdin=io.StringIO(json.dumps(req)), stdout=stdout, stderr=stderr, port_factory=lambda *args: Port())
    response = json.loads(stdout.getvalue())
    assert code == 0 and not stderr.getvalue() and response["data"]["result"] == expected, response
    registry.validate_instance(f"schemas/v1/{capability_id}.response.schema.json", response)


@pytest.mark.parametrize("capability_id", READ_PARAMETERS)
def test_extended_read_public_cli_schema_and_fixed_projection(capability_id, registry, monkeypatch):
    params = READ_PARAMETERS[capability_id]
    item = read_item(capability_id, 41) if capability_id.endswith("processing_details.get") else _item(capability_id, 41)
    item.update(TAX if capability_id.endswith("processing_details.get") else {key: TAX[key] for key in ("tax_tag_ids", "tax_repartition_line_id")})
    if capability_id.endswith("processing_details.get"):
        item["tax_line_id"] = 61
        item["tax_base_amount"] = "-100.5"
    req = request(params)
    registry.validate_instance(f"schemas/v1/{capability_id}.request.schema.json", req)

    class Port:
        user_id = 42

        def read(self, **payload):
            assert payload["company_id"] == 7
            if capability_id.endswith(".search"):
                assert payload["parameters"]["move_id"] == 301 and payload["parameters"]["limit"] == 2
            else:
                assert payload["parameters"] == params
            return {"user_id": 42, "company_visible": True, "module_installed": True, "access_allowed": True,
                    "cursor_found": True, "items": [item]}

    monkeypatch.setattr(cli, "load_registry", lambda: registry)
    stdout, stderr = io.StringIO(), io.StringIO()
    code = cli.main(["read", capability_id, "--request", "-"], stdin=io.StringIO(json.dumps(req)),
                    stdout=stdout, stderr=stderr, port_factory=lambda *args: Port())
    response = json.loads(stdout.getvalue())
    assert code == 0 and not stderr.getvalue(), response
    registry.validate_instance(f"schemas/v1/{capability_id}.response.schema.json", response)
    assert response["data"] == item if not capability_id.endswith(".search") else response["data"]["items"] == [item]


@pytest.mark.parametrize("capability_id,field,value", [
    ("receivable.payment.register", "partner_bank_id", None),
    ("payable.payment.register", "payment_method_line_id", True),
    ("journal_entry.create", "tax_ids", [61, 61]),
    ("journal_entry.lines.replace", "tax_repartition_line_id", 0),
    ("journal_entry.lines.update", "tax_tag_ids", [71, True]),
    ("journal_entry.lines.add", "tax_base_amount", 100.5),
])
def test_request_schemas_reject_bad_explicit_inputs_without_native_calls(capability_id, field, value, registry):
    params = deepcopy(PARAMETERS[capability_id])
    if capability_id.endswith("payment.register"):
        params[field] = value
    elif capability_id.endswith(".update"):
        params["lines"][0]["changes"][field] = value
    else:
        params["lines"][0][field] = value
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(f"schemas/v1/{capability_id}.request.schema.json", request(params))
