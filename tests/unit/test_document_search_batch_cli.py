"""New bulk writes and optional queries use the existing public CLI path."""
import io
import json

import pytest
import test_core_object_reads as object_tests
import test_document_lifecycle_write_cli as write_tests
import test_invoice_analysis as analysis_tests
import test_invoices as invoice_tests
import test_journal_entries as entry_tests
import test_open_items as open_tests

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4.capabilities.core_writes import (
    _expected_idempotency_key,
    validate_core_write_request,
)
from odoo_accounting_cli_v4.cli import main
from odoo_accounting_cli_v4.registry import load_registry


@pytest.fixture(scope="module")
def registry():
    return load_registry()


@pytest.fixture(autouse=True)
def reuse_registry(monkeypatch, registry):
    monkeypatch.setattr(cli, "load_registry", lambda: registry)


@pytest.mark.parametrize("capability,parameters,port", [
    ("invoice.search", {"invoice_user_id": None, "currency_id": 6, "invoice_date_from": "2026-01-01"}, invoice_tests.FakePort()),
    ("journal_entry.search", {"account_id": 31, "currency_id": 6}, entry_tests.FakePort()),
    ("journal_item.search", {"currency_id": 6, "reconciled": False, "move_types": ["out_invoice"], "query": "INV"}, object_tests.FakePort()),
    ("receivable.open_items.list", {"move_id": 31, "move_types": ["out_invoice"]}, open_tests.FakePort()),
    ("payable.open_items.list", {"move_id": 31, "move_types": ["in_invoice"]}, open_tests.FakePort()),
    ("invoice.analysis.search", {"currency_id": 6, "journal_id": 11, "due_date_from": "2026-01-01"}, analysis_tests.FakePort([])),
    ("invoice.analysis.summary", {"date_from": "2026-01-01", "date_to": "2026-12-31", "group_by": "partner",
                                 "currency_id": 6, "journal_id": 11}, analysis_tests.FakePort([analysis_tests._summary()])),
])
def test_search_extensions_reach_existing_cli_port(capability, parameters, port):
    stdout, stderr = io.StringIO(), io.StringIO()
    code = main(["read", capability, "--request", "-"],
                stdin=io.StringIO(json.dumps(write_tests._request(parameters))), stdout=stdout, stderr=stderr,
                port_factory=lambda *_: port)
    result = json.loads(stdout.getvalue())
    assert code == 0 and result["success"] and not stderr.getvalue(), result
    assert result["capability"] == capability
    calls = getattr(port, "search_calls", getattr(port, "calls", []))
    assert len(calls) == 1
    normalized = calls[0].get("filters", calls[0].get("parameters", {}))
    for key, value in parameters.get("filters", parameters).items():
        assert normalized[key] == value


@pytest.mark.parametrize("capability", ["invoice.lines.update", "invoice.lines.add"])
def test_bulk_invoice_lines_use_existing_write_cli_confirmation_and_content_key(capability):
    parameters = {"move_id": 91, "lines": [{"line_id": 901, "changes": {"quantity": "2"}}]}
    if capability.endswith("add"):
        parameters = {"move_id": 91, "expected_line_ids": [901, 902], "lines": write_tests._CASES["invoice.lines.replace"]["lines"]}
    normalized = validate_core_write_request(capability, write_tests._request(parameters))[2]
    key = _expected_idempotency_key(capability, normalized, 7)
    port, stdout, stderr = write_tests._Port(capability), io.StringIO(), io.StringIO()
    code = main(["write", "run", capability, "--request", "-", "--confirm", capability, "--idempotency-key", key],
                stdin=io.StringIO(json.dumps(write_tests._request(parameters))), stdout=stdout, stderr=stderr,
                port_factory=lambda *_: port)
    result = json.loads(stdout.getvalue())
    assert code == 0 and result["success"] and not stderr.getvalue(), result
    assert port.calls == [{"capability_id": capability, "company_id": 7, "idempotency_key": key,
                           "confirmation": capability, "parameters": normalized}]
    assert result["odoo"]["record_ids"] == [91]
