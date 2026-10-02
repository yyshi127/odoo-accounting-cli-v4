"""Nine fixed public bank capability contracts through the existing CLI."""

from __future__ import annotations

import io
import json
from copy import deepcopy

import pytest
from test_core_object_reads import _item
from test_fiscal_mapping_writes import request

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4.capabilities import core_writes
from odoo_accounting_cli_v4.registry import load_registry

WRITES = {
    "bank.transaction.record": {"journal_id": 9, "date": "2026-10-02", "amount": "100", "payment_ref": "Receipt", "partner_id": None,
                                "account_number": "BANK123", "partner_name": "Payer"},
    "bank.transaction.update": {"transaction_id": 31, "changes": {"account_number": None, "partner_name": "Payer"}},
    "bank.statement.create": {"reference": None, "balance_end_real": "100", "transaction_ids": [31], "name": "Statement", "date": "2026-10-02"},
    "bank.statement.update": {"statement_id": 31, "changes": {"name": "Statement", "date": "2026-10-02"}},
    "bank.transaction.unmatch": {"transaction_id": 31},
    "bank.transaction.counterparts.replace": {"transaction_id": 31, "lines": [
        {"account_id": 51, "label": "Fee A", "balance": "70"}, {"account_id": 52, "label": "Fee B", "balance": "30"}]},
}
READS = {"bank.transaction.get": {"transaction_id": 31},
         "bank.transaction.search": {"journal_id": 9, "statement_assignment": "unassigned", "limit": 1},
         "bank.statement.search": {"journal_id": 9, "is_complete": True, "is_valid": True, "limit": 1}}


@pytest.fixture(scope="module")
def registry():
    return load_registry()


@pytest.mark.parametrize("capability", WRITES)
def test_bank_writes_public_cli_schema_dispatch_confirmation_and_result(capability, registry, monkeypatch):
    params = deepcopy(WRITES[capability])
    req = request(params)
    normalized = core_writes.validate_core_write_request(capability, req)[2]
    key = core_writes._expected_idempotency_key(capability, normalized, 7) or "bank-inputs:caller-key"
    statement = capability.startswith("bank.statement.")
    result = {"model": "account.bank.statement" if statement else "account.bank.statement.line", "id": 31,
              "name": "Statement" if statement else "BANK/31", "state": "complete" if statement else "posted", "company_id": 7,
              "move_type": None if statement else "entry", "source_id": None if statement else 301,
              "line_ids": [31] if statement else [41, 42, 43] if capability.endswith("counterparts.replace") else [41, 42],
              "partial_reconcile_ids": [], "full_reconcile_id": None, "reconciled": capability.endswith("counterparts.replace")}
    registry.validate_instance(f"schemas/v1/{capability}.request.schema.json", req)

    class Port:
        user_id = 42

        def execute(self, **payload):
            assert payload["parameters"] == normalized and payload["confirmation"] == capability
            assert payload["idempotency_key"] == key and payload["company_id"] == 7
            return {"user_id": 42, "company_visible": True, "module_installed": True, "access_allowed": True,
                    "idempotent_replay": False, "result": result}

    monkeypatch.setattr(cli, "load_registry", lambda: registry)
    stdout, stderr = io.StringIO(), io.StringIO()
    code = cli.main(["write", "run", capability, "--request", "-", "--confirm", capability, "--idempotency-key", key],
                    stdin=io.StringIO(json.dumps(req)), stdout=stdout, stderr=stderr, port_factory=lambda *args: Port())
    response = json.loads(stdout.getvalue())
    assert code == 0 and not stderr.getvalue() and response["data"]["result"] == result, response
    registry.validate_instance(f"schemas/v1/{capability}.response.schema.json", response)


@pytest.mark.parametrize("capability", READS)
def test_bank_reads_public_cli_schema_and_native_filters(capability, registry, monkeypatch):
    params = deepcopy(READS[capability])
    item = _item("bank.transaction.get" if capability == "bank.transaction.search" else capability, 31)
    if capability == "bank.transaction.get":
        item.update({"account_number": "BANK123", "partner_name": "Payer"})
    req = request(params)
    registry.validate_instance(f"schemas/v1/{capability}.request.schema.json", req)

    class Port:
        user_id = 42

        def read(self, **payload):
            assert payload["company_id"] == 7
            if capability == "bank.statement.search":
                assert payload["parameters"]["is_complete"] is True and payload["parameters"]["is_valid"] is True
            return {"user_id": 42, "company_visible": True, "module_installed": True, "access_allowed": True,
                    "cursor_found": True, "items": [item]}

        def search_page(self, **payload):
            assert payload["filters"]["statement_assignment"] == "unassigned" and payload["limit"] == 2
            return {"user_id": 42, "company_visible": True, "module_installed": True, "access_allowed": True, "rows": [item]}

    monkeypatch.setattr(cli, "load_registry", lambda: registry)
    stdout, stderr = io.StringIO(), io.StringIO()
    code = cli.main(["read", capability, "--request", "-"], stdin=io.StringIO(json.dumps(req)),
                    stdout=stdout, stderr=stderr, port_factory=lambda *args: Port())
    response = json.loads(stdout.getvalue())
    assert code == 0 and not stderr.getvalue(), response
    registry.validate_instance(f"schemas/v1/{capability}.response.schema.json", response)
    assert (response["data"] if capability.endswith(".get") else response["data"]["items"]) == (item if capability.endswith(".get") else [item])
