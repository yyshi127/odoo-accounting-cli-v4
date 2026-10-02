from __future__ import annotations

import io
import json
from contextlib import nullcontext
from copy import deepcopy
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_company_processing_batch import result as company_result
from test_fiscal_mapping_writes import request
from test_journal_item_processing_batch import result as move_result

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4 import company_processing_contracts as company
from odoo_accounting_cli_v4 import journal_item_processing_contracts as journal_items
from odoo_accounting_cli_v4 import journal_processing_contracts as journal
from odoo_accounting_cli_v4.bridge import core_writes_runtime as runtime
from odoo_accounting_cli_v4.capabilities import core_writes
from odoo_accounting_cli_v4.registry import load_registry

NEW_PARAMETERS = {
    "invoice.reverse_and_reissue": {"move_id": 31, "date": "2026-10-02", "reason": "Correction"},
    "company.default_accounts.assign": {"changes": {"income_account_id": 11, "expense_account_id": 12}},
    "company.bank_defaults.assign": {"changes": {"account_journal_suspense_account_id": 13, "transfer_account_id": None}},
    "company.discount_allocation_accounts.assign": {"changes": {"account_discount_income_allocation_id": 11, "account_discount_expense_allocation_id": 12}},
}
PARAMETERS = {
    **NEW_PARAMETERS,
    "journal_entry.lines.update": {"move_id": 31, "lines": [{"line_id": 41, "changes": {"currency_id": 6, "amount_currency": "20"}}, {"line_id": 42, "changes": {"currency_id": 6, "amount_currency": "-20"}}]},
    "reconciliation.undo": {"mode": "match_group", "line_ids": [41]},
    "journal.sequence_policy.update": {"journal_id": 31, "changes": {"is_self_billing": True}},
}


def result(capability_id, parameters):
    if capability_id.startswith("company."):
        return company_result(capability_id, parameters)
    if capability_id == "invoice.reverse_and_reissue":
        items = [{**move_result("", {"move_id": 81}), "source_id": parameters["move_id"], "state": "posted", "move_type": "out_refund"},
                 {**move_result("", {"move_id": 82}), "source_id": parameters["move_id"], "move_type": "out_invoice", "line_ids": [43, 44]}]
        return {"items": items, "processed_count": 2}
    if capability_id == "reconciliation.undo":
        return {"model": "account.move.line", "id": None, "name": None, "state": "unreconciled", "company_id": 7,
                "move_type": None, "source_id": None, "line_ids": [41, 42, 43], "partial_reconcile_ids": [], "full_reconcile_id": None, "reconciled": False}
    if capability_id == "journal.sequence_policy.update":
        return {**company_result("", {}), "model": "account.journal", "id": 31}
    return move_result(capability_id, parameters)


@pytest.fixture(scope="module")
def registry():
    return load_registry()


@pytest.mark.parametrize("capability_id", PARAMETERS)
def test_public_write_cli_schema_confirmation_and_native_parameter_binding(capability_id, registry, monkeypatch):
    params, expected = PARAMETERS[capability_id], result(capability_id, PARAMETERS[capability_id])
    req = request(params)
    normalized = core_writes.validate_core_write_request(capability_id, req)[2]
    expected_key = core_writes._expected_idempotency_key(capability_id, normalized, 7)
    assert expected_key == runtime._deterministic_key(capability_id, normalized, 7)
    key = expected_key or "workflow:reverse-reissue:source-31"
    assert runtime._valid_parameters(capability_id, normalized, 7)
    registry.validate_instance(f"schemas/v1/{capability_id}.request.schema.json", req)

    class Port:
        user_id = 42

        def execute(self, **payload):
            assert payload["parameters"] == normalized and payload["company_id"] == 7
            assert payload["idempotency_key"] == key and payload["confirmation"] == capability_id
            return {"user_id": 42, "company_visible": True, "module_installed": True, "access_allowed": True,
                    "idempotent_replay": False, "result": expected}

    monkeypatch.setattr(cli, "load_registry", lambda: registry)
    stdout, stderr = io.StringIO(), io.StringIO()
    assert cli.main(["write", "run", capability_id, "--request", "-", "--confirm", capability_id, "--idempotency-key", key],
                    stdin=io.StringIO(json.dumps(req)), stdout=stdout, stderr=stderr, port_factory=lambda *args: Port()) == 0, stdout.getvalue()
    response = json.loads(stdout.getvalue())
    registry.validate_instance(f"schemas/v1/{capability_id}.response.schema.json", response)
    assert response["data"]["result"] == expected and not stderr.getvalue()
    for confirmation in (None, "different.operation"):
        with pytest.raises(core_writes.CoreWriteError):
            core_writes.execute_core_write(Port(), capability_id, req, key, confirmation)


@pytest.mark.parametrize("changes", [{"processed_count": 1}, {"items": []}])
def test_reissue_requires_exact_two_sorted_native_results(changes):
    cap = "invoice.reverse_and_reissue"
    with pytest.raises(core_writes.CoreWriteError):
        core_writes._validate_result(cap, NEW_PARAMETERS[cap], {**result(cap, NEW_PARAMETERS[cap]), **changes}, company_id=7, idempotent_replay=False)


@pytest.mark.parametrize("field,value", [("source_id", 99), ("company_id", 8), ("state", "draft"), ("move_type", "entry"), ("id", 31)])
def test_reissue_refund_result_is_bound_to_original_source_and_native_state(field, value):
    cap = "invoice.reverse_and_reissue"
    response = result(cap, NEW_PARAMETERS[cap])
    response["items"][0][field] = value
    with pytest.raises(core_writes.CoreWriteError):
        core_writes._validate_result(cap, NEW_PARAMETERS[cap], response, company_id=7, idempotent_replay=False)


def test_reissue_result_order_types_and_replacement_state_fail_closed():
    cap, params = "invoice.reverse_and_reissue", NEW_PARAMETERS["invoice.reverse_and_reissue"]
    baseline = result(cap, params)
    candidates = []
    reversed_items = deepcopy(baseline)
    reversed_items["items"].reverse()
    candidates.append(reversed_items)
    for field, value in (("state", "posted"), ("move_type", "in_invoice"), ("source_id", None), ("line_ids", baseline["items"][0]["line_ids"])):
        candidate = deepcopy(baseline)
        candidate["items"][1][field] = value
        candidates.append(candidate)
    for candidate in candidates:
        with pytest.raises(core_writes.CoreWriteError):
            core_writes._validate_result(cap, params, candidate, company_id=7, idempotent_replay=False)


@pytest.mark.parametrize("parameters", [
    {"mode": "match_group", "line_ids": []}, {"mode": "match_group", "line_ids": [42, 41]},
    {"mode": "match_group", "line_ids": [41, 41]}, {"mode": "match_group", "line_ids": [True]},
    {"mode": "match_group", "line_ids": list(range(1, 102))}, {"mode": "all", "line_ids": [41]},
    {"mode": "match_group", "line_ids": [41], "company_id": 8},
])
def test_match_group_undo_has_explicit_closed_sorted_bounded_selection(parameters):
    with pytest.raises(core_writes.CoreWriteError):
        core_writes.validate_core_write_request("reconciliation.undo", request(parameters))


def test_match_group_native_boolean_and_replay_closure_may_shrink():
    cap, params = "reconciliation.undo", PARAMETERS["reconciliation.undo"]
    initial = result(cap, params)
    assert core_writes._validate_result(cap, params, initial, company_id=7, idempotent_replay=False) == initial
    replay = {**initial, "line_ids": [41], "reconciled": True}
    assert core_writes._validate_result(cap, params, replay, company_id=7, idempotent_replay=True) == replay
    for change in ({"line_ids": [42]}, {"partial_reconcile_ids": [91]}, {"full_reconcile_id": 91}, {"company_id": 8}):
        with pytest.raises(core_writes.CoreWriteError):
            core_writes._validate_result(cap, params, {**initial, **change}, company_id=7, idempotent_replay=False)


@pytest.mark.parametrize("capability_id", [cap for cap in NEW_PARAMETERS if cap.startswith("company.")])
def test_company_accounts_only_accept_operation_fields_and_context_company(capability_id):
    params = NEW_PARAMETERS[capability_id]
    assert company.normalize_parameters(capability_id, params) == params
    fields = company.FIELD_GROUPS[capability_id]
    assert company.normalize_parameters(capability_id, {"changes": dict.fromkeys(fields)})["changes"] == dict.fromkeys(fields)
    for candidate in ({**params, "company_id": 8}, {"changes": {}}, {"changes": {next(iter(fields)): False}}, {"changes": {"currency_id": 6}}):
        with pytest.raises(core_writes.CoreWriteError):
            core_writes.validate_core_write_request(capability_id, request(candidate))


@pytest.mark.parametrize("value", [False, None, 0, "6"])
def test_entry_currency_reference_rejects_nonpositive_identifier(value):
    params = {"move_id": 31, "lines": [{"line_id": 41, "changes": {"currency_id": value, "amount_currency": "20"}}]}
    with pytest.raises(core_writes.CoreWriteError):
        core_writes.validate_core_write_request("journal_entry.lines.update", request(params))


def test_entry_amount_currency_alone_is_closed_signed_input_without_tax_editing():
    params = {"move_id": 31, "lines": [{"line_id": 41, "changes": {"amount_currency": "-20.01"}}]}
    assert journal_items.normalize_parameters("journal_entry.lines.update", params) == params
    assert {"currency_id", "amount_currency"} <= journal_items.ENTRY_FIELDS and "tax_ids" not in journal_items.ENTRY_FIELDS
    assert journal.normalize_parameters("journal.sequence_policy.update", PARAMETERS["journal.sequence_policy.update"]) == PARAMETERS["journal.sequence_policy.update"]


def test_statement_filter_binds_cursor_and_checks_each_returned_parent():
    from test_bank_transaction_search import FakePort, _request

    from odoo_accounting_cli_v4.capabilities.bank_transactions import (
        BankTransactionListError,
        search_bank_transactions,
        validate_bank_transaction_search_request,
    )

    port = FakePort()
    for row in port.rows:
        row["statement_id"] = 91
    first = search_bank_transactions(port, _request(statement_id=91))
    cursor = first["next_cursor"]
    assert cursor and port.calls[0]["filters"]["statement_id"] == 91
    assert search_bank_transactions(port, _request(statement_id=91, cursor=cursor))["items"][0]["statement_id"] == 91
    with pytest.raises(BankTransactionListError):
        search_bank_transactions(port, _request(statement_id=92, cursor=cursor))
    port.rows[0]["statement_id"] = 92
    with pytest.raises(BankTransactionListError):
        search_bank_transactions(port, _request(statement_id=91))
    assert validate_bank_transaction_search_request(_request())[2] == validate_bank_transaction_search_request(_request(statement_id=None))[2]


@pytest.mark.parametrize("refs", [[{"id": 91, "company_id": 7, "method": "run"}], [{"id": 92, "company_id": 7}, {"id": 91, "company_id": 7}], [{"id": 91, "company_id": False}], [{"id": 91, "company_id": 7}, {"id": 91, "company_id": 7}]])
def test_payment_bank_refs_are_closed_sorted_and_unique(refs):
    from test_payments import FakePort, _detail, _request

    from odoo_accounting_cli_v4.capabilities.payments import PaymentError, get_payment

    item = _detail(31)
    item["reconciled_bank_transactions"] = refs
    with pytest.raises(PaymentError):
        get_payment(FakePort(payment=item), _request(payment_id=31))


def test_payment_bank_refs_can_have_a_valid_graph_company_other_than_payment_company():
    from test_payments import FakePort, _detail, _request

    from odoo_accounting_cli_v4.capabilities.payments import get_payment

    item = _detail(31)
    item["reconciled_bank_transactions"] = [{"id": 91, "company_id": 8}]
    assert get_payment(FakePort(payment=item), _request(payment_id=31))["reconciled_bank_transactions"] == item["reconciled_bank_transactions"]


@pytest.mark.parametrize("capability_id", ["bank.transaction.list", "bank.transaction.search", "bank.transaction.get", "payment.get", "company.processing_settings.get"])
def test_extended_read_projection_through_public_cli_and_actual_schemas(capability_id, registry, monkeypatch):
    from test_bank_transaction_search import FakePort as SearchPort
    from test_bank_transactions import FakePort as ListPort
    from test_bank_transactions import _row
    from test_core_object_reads import FakePort as ObjectPort
    from test_core_object_reads import _item
    from test_payments import FakePort as PaymentPort
    from test_payments import _detail

    if capability_id == "bank.transaction.list":
        port, params = ListPort(rows=[_row(31, "2026-10-02", statement_id=91)]), {"limit": 1, "cursor": None}
    elif capability_id == "bank.transaction.search":
        port, params = SearchPort(), {"statement_id": 91, "limit": 1, "cursor": None}
        for row in port.rows:
            row["statement_id"] = 91
    elif capability_id == "payment.get":
        item = _detail(31)
        item["reconciled_bank_transactions"] = [{"id": 91, "company_id": 7}]
        port, params = PaymentPort(payment=item), {"payment_id": 31}
    elif capability_id == company.GET_ID:
        item = {"id": 7, "company_id": 7}
        for field in company.SETTING_FIELDS:
            item[field] = False if field in company.BOOL_FIELDS else None if field in company.RELATION_MODELS or field == "quick_edit_mode" else "1" if field == "fiscalyear_last_month" else 31 if field == "fiscalyear_last_day" else "round_per_line" if field == "tax_calculation_rounding_method" else "tax_excluded"
        port, params = ObjectPort([item]), {}
    else:
        item = _item(capability_id, 31)
        port, params = ObjectPort([item]), {"transaction_id": 31} if capability_id == "bank.transaction.get" else {}
    req = request(params)
    registry.validate_instance(f"schemas/v1/{capability_id}.request.schema.json", req)
    monkeypatch.setattr(cli, "load_registry", lambda: registry)
    stdout, stderr = io.StringIO(), io.StringIO()
    assert cli.main(["read", capability_id, "--request", "-"], stdin=io.StringIO(json.dumps(req)), stdout=stdout, stderr=stderr, port_factory=lambda *args: port) == 0, stdout.getvalue()
    response = json.loads(stdout.getvalue())
    registry.validate_instance(f"schemas/v1/{capability_id}.response.schema.json", response)
    assert response["success"] and not stderr.getvalue()


def test_shared_native_client_preserves_closed_denial_page_with_null_result(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "integration"))
    shared = import_module("test_accounting_workflows_batch_live")
    page = {"user_id": 5, "company_visible": True, "module_installed": True,
            "access_allowed": False, "idempotent_replay": False, "result": None}
    monkeypatch.setattr(shared.core._RuntimeClient, "invoke", lambda self, action, payload: page)
    monkeypatch.setattr(shared.core, "_collect_related", lambda env, tracked: None)
    client = shared._Client(SimpleNamespace(cr=SimpleNamespace(savepoint=nullcontext)))
    client.tracked["account.move"].add(None)
    assert client.invoke("accounting.core_write.execute", {}) is page
    assert page["result"] is None and not page["access_allowed"]
    assert all(None not in record_ids for record_ids in client.tracked.values())


def test_shared_native_client_tracks_statement_transactions_without_polluting_journal_items(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "integration"))
    shared = import_module("test_accounting_workflows_batch_live")
    page = {"result": {"model": "account.bank.statement", "id": 71, "line_ids": [31, 32]}}
    legacy_saw_statement = []

    def legacy_invoke(self, action, payload):
        result = page["result"]
        legacy_saw_statement.append(result["model"] in self.tracked)
        if result["model"] in self.tracked:
            self.tracked[result["model"]].add(result["id"])
            self.tracked["account.move.line"].update(result["line_ids"])
        if payload.get("fail"):
            raise RuntimeError("legacy dispatch failed")
        return page

    monkeypatch.setattr(shared.core._RuntimeClient, "invoke", legacy_invoke)
    monkeypatch.setattr(shared.core, "_collect_related", lambda env, tracked: None)
    client = shared._Client(SimpleNamespace(cr=SimpleNamespace(savepoint=nullcontext)))
    statement_ids = {69}
    client.tracked["account.bank.statement"] = statement_ids
    client.tracked["account.move.line"] = {501}
    assert client.invoke("accounting.core_write.execute", {}) is page
    assert client.tracked["account.bank.statement"] is statement_ids and statement_ids == {69, 71}
    assert client.tracked["account.bank.statement.line"] == {31, 32}
    assert client.tracked["account.move.line"] == {501}
    with pytest.raises(RuntimeError, match="legacy dispatch failed"):
        client.invoke("accounting.core_write.execute", {"fail": True})
    assert legacy_saw_statement == [False, False]
    assert client.tracked["account.bank.statement"] is statement_ids and statement_ids == {69, 71}
    assert client.tracked["account.bank.statement.line"] == {31, 32}
    assert client.tracked["account.move.line"] == {501}
