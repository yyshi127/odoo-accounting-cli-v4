from __future__ import annotations

import hashlib
import json
from copy import deepcopy

import pytest

from odoo_accounting_cli_v4 import move_processing_contracts as move_processing
from odoo_accounting_cli_v4.capabilities.core_writes import (
    CoreWriteError,
    _expected_idempotency_key,
    validate_core_write_request,
)

REGISTER_IDS = ("receivable.payment.register", "payable.payment.register")
ENTRY_IDS = ("journal_entry.create", "journal_entry.lines.replace", "journal_entry.lines.add")
REFERENCES = ({"payment_method_line_id": 41}, {"partner_bank_id": 51}, {"payment_method_line_id": 41, "partner_bank_id": 51})
TAX_FIELDS = {"tax_ids": [11, 12], "tax_tag_ids": [21, 22], "tax_repartition_line_id": 31, "tax_base_amount": "-100.50"}


def request(parameters):
    return {
        "schema_version": "v1",
        "request_id": "7bc39413-0d69-4092-9319-795d33f3167c",
        "context": {"database": "odoo_cli_v4_dev", "company_id": 7, "user_login": "v4-agent", "language": "zh_CN", "timezone": "Asia/Shanghai"},
        "parameters": deepcopy(parameters),
    }


def register_parameters(many=False, **extra):
    source = {"move_ids": [33, 31]} if many else {"move_id": 31}
    return {**source, "journal_id": 7, "payment_date": "2026-10-02", **extra}


def entry_parameters(capability_id, **fields):
    lines = [
        {"name": "Debit", "account_id": 11, "partner_id": None, "debit": "100.00", "credit": "0", **fields},
        {"name": "Credit", "account_id": 12, "partner_id": None, "debit": "0", "credit": "100.00"},
    ]
    if capability_id == "journal_entry.create":
        return {"journal_id": 7, "date": "2026-10-02", "lines": lines}
    if capability_id == "journal_entry.lines.add":
        return {"move_id": 31, "expected_line_ids": [81, 82], "lines": lines}
    return {"move_id": 31, "lines": lines}


def normalized(capability_id, parameters):
    payload = request(parameters)
    original = deepcopy(payload)
    result = validate_core_write_request(capability_id, payload)[2]
    assert payload == original
    return result


@pytest.mark.parametrize("capability_id", REGISTER_IDS)
@pytest.mark.parametrize("many", [False, True])
@pytest.mark.parametrize("references", REFERENCES)
def test_register_accepts_explicit_references_without_defaults(capability_id, many, references):
    parameters = register_parameters(many, **references)
    expected = {**parameters, "move_ids": [31, 33]} if many else parameters
    assert normalized(capability_id, parameters) == expected


@pytest.mark.parametrize("capability_id", REGISTER_IDS)
@pytest.mark.parametrize("many", [False, True])
@pytest.mark.parametrize("field", ["payment_method_line_id", "partner_bank_id"])
@pytest.mark.parametrize("value", [None, True, False, 0, -1, "41", 41.0])
def test_register_rejects_invalid_explicit_references(capability_id, many, field, value):
    with pytest.raises(CoreWriteError):
        normalized(capability_id, register_parameters(many, **{field: value}))


@pytest.mark.parametrize("capability_id", REGISTER_IDS)
@pytest.mark.parametrize("extra", [{}, {"amount": "99"}, {"payment_difference_handling": "open"}, {"amount": "99", "payment_difference_handling": "reconcile", "writeoff_account_id": 11}])
def test_omitted_references_keep_single_normalization_and_key(capability_id, extra):
    parameters = register_parameters(**extra)
    actual = normalized(capability_id, parameters)
    assert actual == parameters
    expected_key = None if "amount" in extra else f"{capability_id}:31"
    assert _expected_idempotency_key(capability_id, actual, 7) == expected_key


@pytest.mark.parametrize("capability_id", REGISTER_IDS)
@pytest.mark.parametrize("references", ({}, *REFERENCES))
def test_batch_key_hashes_only_supplied_normalized_inputs(capability_id, references):
    parameters = register_parameters(True, **references)
    actual = normalized(capability_id, parameters)
    expected = {**parameters, "move_ids": [31, 33]}
    canonical = json.dumps(expected, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(canonical).hexdigest()[:32]
    assert actual == expected
    assert _expected_idempotency_key(capability_id, actual, 7) == f"{capability_id}:7:{digest}"


@pytest.mark.parametrize("field,value", [("amount", "99"), ("payment_difference_handling", "open"), ("writeoff_account_id", 11), ("writeoff_label", "Fee")])
def test_explicit_references_do_not_enable_batch_difference_inputs(field, value):
    with pytest.raises(CoreWriteError):
        normalized(REGISTER_IDS[0], register_parameters(True, **REFERENCES[2], **{field: value}))


@pytest.mark.parametrize("extra", [{"amount": "99"}, {"amount": "99", "payment_difference_handling": "open"}, {"amount": "99", "payment_difference_handling": "reconcile", "writeoff_account_id": 11, "writeoff_label": "Fee"}])
def test_explicit_references_preserve_single_difference_inputs(extra):
    parameters = register_parameters(**REFERENCES[2], **extra)
    actual = normalized(REGISTER_IDS[0], parameters)
    assert actual == parameters
    assert _expected_idempotency_key(REGISTER_IDS[0], actual, 7) is None


@pytest.mark.parametrize("capability_id", ENTRY_IDS)
def test_omitted_journal_tax_fields_preserve_literals_and_old_keys(capability_id):
    parameters = entry_parameters(capability_id)
    actual = normalized(capability_id, parameters)
    assert actual == parameters
    if capability_id == "journal_entry.create":
        expected_key = None
    elif capability_id == "journal_entry.lines.add":
        expected_key = move_processing.idempotency_key(capability_id, parameters, 7)
    else:
        canonical = json.dumps(parameters["lines"], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        expected_key = f"{capability_id}:31:{hashlib.sha256(canonical).hexdigest()[:32]}"
    assert _expected_idempotency_key(capability_id, actual, 7) == expected_key


@pytest.mark.parametrize("capability_id", ENTRY_IDS)
@pytest.mark.parametrize("fields", [TAX_FIELDS, {"tax_ids": [], "tax_tag_ids": [], "tax_repartition_line_id": None, "tax_base_amount": "0"}, {"tax_base_amount": "-0.00"}, {"tax_base_amount": "100.00"}, {"tax_ids": list(range(1, 101)), "tax_tag_ids": list(range(1, 101))}])
def test_full_journal_lines_accept_tax_fields_and_clear_without_reformatting(capability_id, fields):
    parameters = entry_parameters(capability_id, **fields)
    assert normalized(capability_id, parameters) == parameters


@pytest.mark.parametrize("field", ["tax_ids", "tax_tag_ids"])
@pytest.mark.parametrize("value", [None, True, [True], [0], [2, 1], [1, 1], list(range(1, 102))])
def test_full_journal_lines_reject_invalid_tax_id_lists(field, value):
    with pytest.raises(CoreWriteError):
        normalized(ENTRY_IDS[0], entry_parameters(ENTRY_IDS[0], **{field: value}))


@pytest.mark.parametrize("value", [True, False, 0, -1, "31", 31.0])
def test_full_journal_lines_reject_invalid_repartition_reference(value):
    with pytest.raises(CoreWriteError):
        normalized(ENTRY_IDS[0], entry_parameters(ENTRY_IDS[0], tax_repartition_line_id=value))


@pytest.mark.parametrize("value", [None, True, 1, "1e2", "01", "9" * 257])
def test_full_journal_lines_reject_invalid_tax_base_decimal(value):
    with pytest.raises(CoreWriteError):
        normalized(ENTRY_IDS[0], entry_parameters(ENTRY_IDS[0], tax_base_amount=value))


def test_full_journal_lines_do_not_expose_independent_tax_line_id():
    with pytest.raises(CoreWriteError):
        normalized(ENTRY_IDS[0], entry_parameters(ENTRY_IDS[0], tax_line_id=31))
