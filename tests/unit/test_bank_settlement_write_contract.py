from __future__ import annotations

import hashlib
import json
from copy import deepcopy

import pytest

from odoo_accounting_cli_v4.capabilities import core_writes

COUNTERPART_ID = "bank.transaction.counterparts.replace"
RECORD = {"journal_id": 11, "date": "2026-10-02", "amount": "-100.00", "payment_ref": "Bank fees", "partner_id": None}
STATEMENT = {"transaction_ids": [42, 41], "reference": "Imported October", "balance_end_real": "900"}
ROWS = [{"account_id": 71, "label": "银行费用", "balance": "60"}, {"account_id": 72, "label": "Service fee", "balance": "40"}]


def request(parameters):
    return {
        "schema_version": "v1", "request_id": "7bc39413-0d69-4092-9319-795d33f3167c",
        "context": {"database": "odoo_cli_v4_dev", "company_id": 7, "user_login": "v4-agent", "language": "zh_CN", "timezone": "Asia/Shanghai"},
        "parameters": deepcopy(parameters),
    }


def normalized(capability_id, parameters):
    payload = request(parameters)
    original = deepcopy(payload)
    actual = core_writes.validate_core_write_request(capability_id, payload)[2]
    assert payload == original
    return actual


def digest(value):
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()[:32]


def metadata_parameters(capability_id, metadata):
    if capability_id == "bank.transaction.record":
        return {**RECORD, **metadata}
    return {"transaction_id": 31, "changes": dict(metadata)}


def statement_parameters(capability_id, changes):
    if capability_id == "bank.statement.create":
        return {**STATEMENT, **changes}
    return {"statement_id": 51, "changes": dict(changes)}


def bank_result():
    return {
        "model": "account.bank.statement.line", "id": 31, "name": "BNK/2026/001",
        "state": "posted", "company_id": 7, "move_type": "entry", "source_id": 81,
        "line_ids": [91, 92, 93], "partial_reconcile_ids": [], "full_reconcile_id": None,
        "reconciled": True,
    }


@pytest.mark.parametrize("capability_id", ["bank.transaction.record", "bank.transaction.update"])
@pytest.mark.parametrize("metadata", [{"account_number": None}, {"partner_name": None}, {"account_number": "GB12 1234", "partner_name": "客户"}, {"partner_name": "中" * 200}])
def test_optional_bank_metadata_is_nullable_literal_and_has_no_defaults(capability_id, metadata):
    parameters = metadata_parameters(capability_id, metadata)
    assert normalized(capability_id, parameters) == parameters


@pytest.mark.parametrize("field", ["account_number", "partner_name"])
@pytest.mark.parametrize("value", [True, 7, "", " ", " leading", "trailing ", "x" * 201])
def test_bank_metadata_rejects_untrimmed_or_untyped_values(field, value):
    for capability_id in ("bank.transaction.record", "bank.transaction.update"):
        with pytest.raises(core_writes.CoreWriteError):
            normalized(capability_id, metadata_parameters(capability_id, {field: value}))


def test_omitted_bank_metadata_preserves_old_normalization_and_state_keys():
    assert normalized("bank.transaction.record", RECORD) == RECORD
    assert core_writes._expected_idempotency_key("bank.transaction.record", RECORD, 7) is None
    parameters = {"transaction_id": 31, "changes": {"payment_ref": "Bank fees"}}
    actual = normalized("bank.transaction.update", parameters)
    assert actual == parameters
    assert core_writes._expected_idempotency_key("bank.transaction.update", actual, 7) == f"bank.transaction.update:31:{digest(parameters['changes'])}"
    explicit = {"transaction_id": 31, "changes": {**parameters["changes"], "account_number": None}}
    assert core_writes._expected_idempotency_key("bank.transaction.update", normalized("bank.transaction.update", explicit), 7) == f"bank.transaction.update:31:{digest(explicit['changes'])}"


@pytest.mark.parametrize("capability_id", ["bank.statement.create", "bank.statement.update"])
def test_statement_title_date_inputs_are_optional_and_do_not_change_omitted_keys(capability_id):
    changes = {"name": "October bank statement", "date": "2026-10-01"}
    parameters = statement_parameters(capability_id, changes)
    actual = normalized(capability_id, parameters)
    if capability_id.endswith("create"):
        assert actual == {**parameters, "transaction_ids": [41, 42]}
        assert core_writes._expected_idempotency_key(capability_id, actual, 7) == f"{capability_id}:7:{digest(actual)}"
        old = normalized(capability_id, STATEMENT)
        assert old == {**STATEMENT, "transaction_ids": [41, 42]}
        assert core_writes._expected_idempotency_key(capability_id, old, 7) == f"{capability_id}:7:{digest(old)}"
    else:
        assert actual == parameters
        assert core_writes._expected_idempotency_key(capability_id, actual, 7) == f"{capability_id}:51:{digest(changes)}"
        old = normalized(capability_id, {"statement_id": 51, "changes": {"reference": None}})
        assert old == {"statement_id": 51, "changes": {"reference": None}}
        assert core_writes._expected_idempotency_key(capability_id, old, 7) == f"{capability_id}:51:{digest(old['changes'])}"


@pytest.mark.parametrize("field,value", [("name", None), ("name", ""), ("name", " leading"), ("name", "x" * 201), ("date", None), ("date", "2026-02-30"), ("date", "20261002")])
def test_statement_title_date_reject_null_and_invalid_values(field, value):
    for capability_id in ("bank.statement.create", "bank.statement.update"):
        with pytest.raises(core_writes.CoreWriteError):
            normalized(capability_id, statement_parameters(capability_id, {field: value}))


@pytest.mark.parametrize("rows", [ROWS, list(reversed(ROWS)), [ROWS[0], ROWS[0]], [ROWS[0]] * 100])
def test_counterpart_rows_preserve_order_duplicates_and_canonical_literals(rows):
    parameters = {"transaction_id": 31, "lines": rows}
    actual = normalized(COUNTERPART_ID, parameters)
    assert COUNTERPART_ID in core_writes.CORE_WRITE_CAPABILITY_IDS
    assert actual == parameters
    assert actual["lines"] is not rows and actual["lines"][0] is not rows[0]
    assert core_writes._expected_idempotency_key(COUNTERPART_ID, actual, 7) == f"{COUNTERPART_ID}:31:{digest(rows)}"


@pytest.mark.parametrize("change", [
    {"transaction_id": True}, {"transaction_id": 0}, {"lines": None}, {"lines": []},
    {"lines": ROWS[:1]}, {"lines": [ROWS[0]] * 101}, {"currency_id": 6},
    {"lines": [None, ROWS[1]]}, {"lines": [{**ROWS[0], "tax_ids": []}, ROWS[1]]},
    {"lines": [{"account_id": 71, "label": "Fee"}, ROWS[1]]},
])
def test_counterpart_contract_is_closed_and_bounded(change):
    with pytest.raises(core_writes.CoreWriteError):
        normalized(COUNTERPART_ID, {"transaction_id": 31, "lines": ROWS, **change})


@pytest.mark.parametrize("field,value", [
    ("account_id", True), ("account_id", 0), ("account_id", "71"),
    ("label", None), ("label", ""), ("label", " trailing "), ("label", "x" * 201),
    ("balance", "0"), ("balance", "-0"), ("balance", "1.00"), ("balance", "-0.00"),
    ("balance", "+1"), ("balance", "01"), ("balance", "NaN"), ("balance", 1),
    ("balance", "1" * 257),
])
def test_counterpart_fields_reject_invalid_ids_labels_and_noncanonical_money(field, value):
    rows = [{**ROWS[0], field: value}, ROWS[1]]
    with pytest.raises(core_writes.CoreWriteError):
        normalized(COUNTERPART_ID, {"transaction_id": 31, "lines": rows})


@pytest.mark.parametrize("replay", [False, True])
def test_counterpart_result_accepts_only_complete_native_bank_shape(replay):
    parameters = {"transaction_id": 31, "lines": ROWS}
    result = bank_result()
    assert core_writes._validate_result(COUNTERPART_ID, parameters, result, company_id=7, idempotent_replay=replay) == result


@pytest.mark.parametrize("change", [
    {"model": "account.move"}, {"id": 32}, {"company_id": 8}, {"state": "draft"},
    {"move_type": "out_invoice"}, {"source_id": None}, {"line_ids": [91, 92]},
    {"line_ids": [91, 92, 93, 94]}, {"reconciled": False},
    {"partial_reconcile_ids": [101]}, {"full_reconcile_id": 101}, {"extra": True},
])
def test_counterpart_result_rejects_incomplete_or_mismatched_targets(change):
    with pytest.raises(core_writes.CoreWriteError):
        core_writes._validate_result(COUNTERPART_ID, {"transaction_id": 31, "lines": ROWS}, {**bank_result(), **change}, company_id=7, idempotent_replay=False)


def test_counterpart_confirmation_and_derived_key_are_required_before_port_call():
    class Port:
        user_id = 42

        def execute(self, **payload):
            assert payload["parameters"] == {"transaction_id": 31, "lines": ROWS}
            return {"user_id": 42, "company_visible": True, "module_installed": True, "access_allowed": True, "idempotent_replay": False, "result": bank_result()}

    payload = request({"transaction_id": 31, "lines": ROWS})
    key = f"{COUNTERPART_ID}:31:{digest(ROWS)}"
    assert core_writes.execute_core_write(Port(), COUNTERPART_ID, payload, key, COUNTERPART_ID)["result"] == bank_result()
    for wrong_key, confirmation in ((key, None), (key, "bank.transaction.match"), ("client-key-wrong", COUNTERPART_ID)):
        with pytest.raises(core_writes.CoreWriteError):
            core_writes.execute_core_write(Port(), COUNTERPART_ID, payload, wrong_key, confirmation)


@pytest.mark.parametrize("capability_id", ["bank.statement.create", "bank.statement.update"])
def test_statement_explicit_title_binds_result_but_omitted_title_stays_compatible(capability_id):
    parameters = statement_parameters(capability_id, {"name": "October statement"})
    actual = normalized(capability_id, parameters)
    result = {**bank_result(), "model": "account.bank.statement", "id": 51, "name": "October statement", "state": "complete", "move_type": None, "source_id": None, "line_ids": [41, 42], "reconciled": False}
    assert core_writes._validate_result(capability_id, actual, result, company_id=7, idempotent_replay=False) == result
    with pytest.raises(core_writes.CoreWriteError):
        core_writes._validate_result(capability_id, actual, {**result, "name": "Another statement"}, company_id=7, idempotent_replay=True)
    old = normalized(capability_id, STATEMENT if capability_id.endswith("create") else {"statement_id": 51, "changes": {"reference": None}})
    assert core_writes._validate_result(capability_id, old, {**result, "name": "Native default title"}, company_id=7, idempotent_replay=True)["name"] == "Native default title"
