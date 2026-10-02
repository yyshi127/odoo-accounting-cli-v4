"""Eight targets reach existing public read/write CLI paths."""
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
from odoo_accounting_cli_v4.registry import load_registry


@pytest.fixture(scope="module")
def registry():
    return load_registry()


@pytest.fixture(autouse=True)
def reuse_registry(monkeypatch, registry):
    monkeypatch.setattr(cli, "load_registry", lambda: registry)


@pytest.mark.parametrize("capability,parameters,port", [
    ("invoice.search", {"product_id": 11, "account_id": 31, "tax_id": 4}, invoice_tests.FakePort()),
    ("journal_entry.search", {"account_id": 31, "tax_id": 4, "line_query": "item"}, entry_tests.FakePort()),
    ("journal_item.search", {"product_id": 11, "tax_id": 4}, object_tests.FakePort()),
    ("receivable.open_items.list", {"invoice_user_id": None, "payment_term_id": None, "fiscal_position_id": None}, open_tests.FakePort()),
    ("payable.open_items.list", {"invoice_user_id": 5, "payment_term_id": 2, "fiscal_position_id": 3}, open_tests.FakePort()),
    ("invoice.analysis.search", {"invoice_user_id": None, "fiscal_position_id": None, "account_id": 31}, analysis_tests.FakePort([])),
    ("invoice.analysis.summary", {"date_from": "2026-01-01", "date_to": "2026-12-31", "group_by": "partner",
                                 "invoice_user_id": 5, "fiscal_position_id": 3, "account_id": 31}, analysis_tests.FakePort([analysis_tests._summary()])),
])
def test_business_filters_reach_existing_cli_port(capability, parameters, port):
    stdout, stderr = io.StringIO(), io.StringIO()
    code = cli.main(["read", capability, "--request", "-"],
                    stdin=io.StringIO(json.dumps(write_tests._request(parameters))), stdout=stdout, stderr=stderr,
                    port_factory=lambda *_: port)
    response = json.loads(stdout.getvalue())
    assert code == 0 and response["success"] and not stderr.getvalue(), response
    calls = getattr(port, "search_calls", getattr(port, "calls", []))
    assert len(calls) == 1
    normalized = calls[0].get("filters", calls[0].get("parameters", {}))
    assert all(normalized[key] == value for key, value in parameters.items())


def test_remove_uses_confirmation_content_key_and_parent_result():
    parameters = {"move_id": 91, "line_ids": [903, 904]}
    normalized = validate_core_write_request("invoice.lines.remove", write_tests._request(parameters))[2]
    key = _expected_idempotency_key("invoice.lines.remove", normalized, 7)
    port, stdout, stderr = write_tests._Port("invoice.lines.remove"), io.StringIO(), io.StringIO()
    code = cli.main(["write", "run", "invoice.lines.remove", "--request", "-", "--confirm", "invoice.lines.remove",
                     "--idempotency-key", key], stdin=io.StringIO(json.dumps(write_tests._request(parameters))),
                    stdout=stdout, stderr=stderr, port_factory=lambda *_: port)
    response = json.loads(stdout.getvalue())
    assert code == 0 and response["success"] and not stderr.getvalue(), response
    assert response["odoo"]["record_ids"] == [91]
    assert port.calls == [{"capability_id": "invoice.lines.remove", "company_id": 7, "idempotency_key": key,
                           "confirmation": "invoice.lines.remove", "parameters": normalized}]
