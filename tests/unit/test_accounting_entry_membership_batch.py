from __future__ import annotations

import hashlib
import io
import json
from copy import deepcopy

import pytest
from test_fiscal_mapping_writes import request

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4.bridge import core_writes_runtime as runtime
from odoo_accounting_cli_v4.capabilities import core_writes
from odoo_accounting_cli_v4.registry import load_registry

ADD = "journal_entry.lines.add"
REMOVE = "journal_entry.lines.remove"
INVOICE_WRITES = ("customer_invoice.create", "vendor_bill.create", "invoice.line.create", "invoice.line.update",
                  "invoice.lines.replace", "customer_credit_note.create", "vendor_refund.create")


def invoice_line(quantity="-2.50", price="-10.00"):
    return {"name": "Signed quantity", "product_id": None, "account_id": 51,
            "quantity": quantity, "price_unit": price, "discount": "0", "tax_ids": [61]}


def invoice_parameters(capability_id, quantity="-2.50", price="-10.00"):
    line = invoice_line(quantity, price)
    if capability_id in {"customer_invoice.create", "vendor_bill.create"}:
        return {"partner_id": 21, "journal_id": 11, "invoice_date": "2026-10-02", "currency_id": 6, "lines": [line]}
    if capability_id == "invoice.line.create":
        return {"move_id": 31, "line": line}
    if capability_id == "invoice.line.update":
        return {"move_id": 31, "line_id": 41, "changes": {"quantity": quantity, "price_unit": price}}
    if capability_id == "invoice.lines.replace":
        return {"move_id": 31, "lines": [line]}
    return {"move_id": 31, "date": "2026-10-02", "reason": "Signed custom refund", "lines": [line]}


ENTRY_LINES = [
    {"name": "Identical balanced pair", "account_id": 51, "partner_id": None, "debit": "12.50", "credit": "0"},
    {"name": "Identical balanced pair", "account_id": 52, "partner_id": None, "debit": "0", "credit": "12.50"},
]
PARAMETERS = {ADD: {"move_id": 31, "expected_line_ids": [41, 42], "lines": ENTRY_LINES},
              REMOVE: {"move_id": 31, "line_ids": [43, 44]}}
PARAMETERS.update({capability: invoice_parameters(capability) for capability in INVOICE_WRITES})


def result(capability_id, parameters):
    move_type = {"vendor_bill.create": "in_invoice", "customer_credit_note.create": "out_refund", "vendor_refund.create": "in_refund"}.get(capability_id, "out_invoice")
    source_id = parameters["move_id"] if capability_id in {"customer_credit_note.create", "vendor_refund.create"} else parameters.get("line_id")
    if capability_id == "invoice.line.create":
        source_id = 43
    return {"model": "account.move", "id": 32 if capability_id in {"customer_credit_note.create", "vendor_refund.create"} else parameters.get("move_id", 31),
            "name": "ENTRY/2026/0031", "state": "draft", "company_id": 7,
            "move_type": "entry" if capability_id in {ADD, REMOVE} else move_type,
            "source_id": source_id, "line_ids": [41, 42, 43, 44] if capability_id == ADD else [41, 42] if capability_id == REMOVE else [41, 42, 43],
            "partial_reconcile_ids": [], "full_reconcile_id": None, "reconciled": False}


@pytest.fixture(scope="module")
def registry():
    return load_registry()


@pytest.mark.parametrize("capability_id", PARAMETERS)
def test_public_cli_schema_confirmation_key_and_typed_result(capability_id, registry, monkeypatch):
    parameters, expected = deepcopy(PARAMETERS[capability_id]), result(capability_id, PARAMETERS[capability_id])
    req = request(parameters)
    normalized = core_writes.validate_core_write_request(capability_id, req)[2]
    key = core_writes._expected_idempotency_key(capability_id, normalized, 7) or "entry-membership:caller-key"
    assert runtime._valid_parameters(capability_id, normalized, 7)
    if capability_id in {ADD, REMOVE}:
        assert runtime._deterministic_key(capability_id, normalized, 7) == key
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
    for confirmation in (None, "different.operation"):
        with pytest.raises(core_writes.CoreWriteError):
            core_writes.execute_core_write(Port(), capability_id, req, key, confirmation)
    for field, value in (("model", "account.move.line"), ("company_id", 8), ("extra", True)):
        with pytest.raises(core_writes.CoreWriteError):
            core_writes._validate_result(capability_id, normalized, {**expected, field: value}, company_id=7, idempotent_replay=False)


@pytest.mark.parametrize("capability_id", [ADD, REMOVE])
def test_membership_validation_uses_real_contract_without_native_execution(capability_id, registry, monkeypatch):

    def no_native(*args):
        raise AssertionError("Dry-run must not invoke native accounting writes")

    monkeypatch.setattr(runtime, "dispatch", no_native)
    req = request(PARAMETERS[capability_id])
    registry.validate_instance(f"schemas/v1/{capability_id}.request.schema.json", req)
    assert core_writes.validate_core_write_request(capability_id, req)[2] == PARAMETERS[capability_id]


@pytest.mark.parametrize("capability_id", INVOICE_WRITES)
@pytest.mark.parametrize("quantity,price", [("-2.50", "10.00"), ("-2.50", "-10.00"), ("2.50", "-10.00")])
def test_signed_quantities_and_prices_preserve_literal_strings_and_omissions(capability_id, quantity, price):
    parameters = invoice_parameters(capability_id, quantity, price)
    normalized = core_writes.validate_core_write_request(capability_id, request(parameters))[2]
    assert normalized == parameters
    assert runtime._valid_parameters(capability_id, normalized, 7)
    if "line" in parameters:
        target, suffix = normalized["line"], "31"
    elif "changes" in parameters:
        target, suffix = normalized["changes"], "31:41"
    else:
        target, suffix = normalized["lines"], "31"
    if capability_id in {"invoice.line.create", "invoice.line.update", "invoice.lines.replace"}:
        digest = hashlib.sha256(json.dumps(target, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:32]
        assert core_writes._expected_idempotency_key(capability_id, normalized, 7) == f"{capability_id}:{suffix}:{digest}"
    else:
        assert core_writes._expected_idempotency_key(capability_id, normalized, 7) is None
    assert not {"payment_term_id", "date", "reference", "analytic_distribution"} & set(parameters) if capability_id in {"customer_invoice.create", "vendor_bill.create"} else True


@pytest.mark.parametrize("capability_id", INVOICE_WRITES)
def test_quantity_zero_preserves_existing_create_vs_maintenance_policy(capability_id):
    req = request(invoice_parameters(capability_id, "0"))
    if capability_id in {"customer_invoice.create", "vendor_bill.create"}:
        with pytest.raises(core_writes.CoreWriteError):
            core_writes.validate_core_write_request(capability_id, req)
    else:
        normalized = core_writes.validate_core_write_request(capability_id, req)[2]
        assert runtime._valid_parameters(capability_id, normalized, 7)


@pytest.mark.parametrize("quantity", [False, None, -2.5, "NaN", "1e3", "--2"])
def test_negative_quantity_does_not_accept_untyped_or_non_decimal_values(quantity):
    for capability_id in INVOICE_WRITES:
        with pytest.raises(core_writes.CoreWriteError):
            core_writes.validate_core_write_request(capability_id, request(invoice_parameters(capability_id, quantity)))


@pytest.mark.parametrize("capability_id,patch", [
    (ADD, {"move_id": True}), (ADD, {"expected_line_ids": [42, 41]}), (ADD, {"expected_line_ids": [41, 41]}),
    (ADD, {"expected_line_ids": [False]}), (ADD, {"expected_line_ids": list(range(1, 502))}),
    (ADD, {"lines": []}), (ADD, {"lines": [ENTRY_LINES[0]]}),
    (ADD, {"lines": [{**ENTRY_LINES[0], "debit": "13"}, ENTRY_LINES[1]]}),
    (ADD, {"lines": [{**ENTRY_LINES[0], "tax_ids": []}, ENTRY_LINES[1]]}),
    (REMOVE, {"line_ids": []}), (REMOVE, {"line_ids": [44, 43]}), (REMOVE, {"line_ids": [43, 43]}),
    (REMOVE, {"line_ids": [False]}), (REMOVE, {"line_ids": list(range(1, 502))}), (REMOVE, {"extra": True}),
])
def test_membership_parameters_are_closed_balanced_and_sorted_unique(capability_id, patch):
    with pytest.raises(core_writes.CoreWriteError):
        core_writes.validate_core_write_request(capability_id, request({**deepcopy(PARAMETERS[capability_id]), **patch}))


def test_add_allows_empty_expected_membership_and_intentionally_duplicate_pairs():
    parameters = {**PARAMETERS[ADD], "expected_line_ids": [], "lines": deepcopy(ENTRY_LINES) * 2}
    assert core_writes.validate_core_write_request(ADD, request(parameters))[2] == parameters
    assert runtime._valid_parameters(ADD, parameters, 7)
    overflow = {**parameters, "expected_line_ids": list(range(1, 498))}
    with pytest.raises(core_writes.CoreWriteError):
        core_writes.validate_core_write_request(ADD, request(overflow))


@pytest.mark.parametrize("capability_id,patch,replay", [
    (ADD, {"line_ids": [41, 43, 44, 45]}, False), (ADD, {"line_ids": [41, 42, 43]}, False),
    (ADD, {"source_id": 41}, False), (ADD, {"state": "posted"}, False), (ADD, {"move_type": "out_invoice"}, False),
    (REMOVE, {"line_ids": [41, 43]}, False), (REMOVE, {"source_id": 43}, False), (REMOVE, {}, True),
])
def test_membership_result_is_bound_to_parent_expected_ids_and_deleted_ids(capability_id, patch, replay):
    with pytest.raises(core_writes.CoreWriteError):
        core_writes._validate_result(capability_id, PARAMETERS[capability_id], {**result(capability_id, PARAMETERS[capability_id]), **patch},
                                    company_id=7, idempotent_replay=replay)


def test_remove_accepts_native_empty_draft_without_fabricating_reconciliation():
    value = {**result(REMOVE, PARAMETERS[REMOVE]), "line_ids": [], "reconciled": False}
    core_writes._validate_result(REMOVE, PARAMETERS[REMOVE], value, company_id=7, idempotent_replay=False)
    with pytest.raises(core_writes.CoreWriteError):
        core_writes._validate_result(REMOVE, PARAMETERS[REMOVE], {**value, "reconciled": True}, company_id=7, idempotent_replay=False)
