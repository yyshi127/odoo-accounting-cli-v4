from __future__ import annotations

import hashlib
import json
from copy import deepcopy

import pytest

from odoo_accounting_cli_v4.capabilities.core_writes import (
    CORE_WRITE_CAPABILITY_IDS,
    CoreWriteError,
    execute_core_write,
    validate_core_write_request,
)

CAPABILITIES = {
    "payment.create",
    "payment.update_draft",
    "payment.reset_to_draft",
    "bank.transaction.update",
    "bank.transaction.match",
    "bank.transaction.unmatch",
    "reconciliation.write_off",
}
PARAMETERS = {
    "payment.create": {
        "payment_type": "inbound",
        "partner_type": "customer",
        "partner_id": 21,
        "amount": "125.50",
        "currency_id": 6,
        "journal_id": 8,
        "payment_method_line_id": 9,
        "date": "2026-08-26",
    },
    "payment.update_draft": {
        "payment_id": 31,
        "changes": {"amount": "130.00", "payment_reference": "Receipt 31"},
    },
    "payment.reset_to_draft": {"payment_id": 32},
    "bank.transaction.update": {
        "transaction_id": 41,
        "changes": {"partner_id": 21, "payment_ref": "Transfer 41"},
    },
    "bank.transaction.match": {
        "transaction_id": 42,
        "candidate_line_ids": [101, 102],
    },
    "bank.transaction.unmatch": {"transaction_id": 43},
    "reconciliation.write_off": {
        "transaction_id": 44,
        "write_off_account_id": 71,
        "label": "Bank fee",
        "expected_residual_amount": "-2.50",
    },
}


def _request(capability_id: str) -> dict:
    return {
        "schema_version": "v1",
        "request_id": "77f91531-a230-4dde-a8bf-e56bb03bdaba",
        "context": {
            "database": "v4-dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": deepcopy(PARAMETERS[capability_id]),
    }


def _digest(value: object) -> str:
    canonical = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(canonical).hexdigest()[:32]


def _key(capability_id: str) -> str:
    parameters = PARAMETERS[capability_id]
    if capability_id == "payment.create":
        return "payment.create:client-request-0001"
    if capability_id == "payment.update_draft":
        return f"payment.update_draft:31:{_digest(parameters['changes'])}"
    if capability_id == "payment.reset_to_draft":
        return "payment.reset_to_draft:32"
    if capability_id == "bank.transaction.update":
        target = parameters["changes"]
    elif capability_id == "bank.transaction.match":
        target = parameters["candidate_line_ids"]
    elif capability_id == "reconciliation.write_off":
        target = {
            "write_off_account_id": 71,
            "expected_residual_amount": "-2.50",
            "label": "Bank fee",
        }
    else:
        return "bank.transaction.unmatch:43"
    return f"{capability_id}:{parameters['transaction_id']}:{_digest(target)}"


def _result(capability_id: str) -> dict:
    payment = capability_id.startswith("payment.")
    parameters = PARAMETERS[capability_id]
    record_id = (
        901
        if capability_id == "payment.create"
        else parameters["payment_id"]
        if payment
        else parameters["transaction_id"]
    )
    return {
        "model": "account.payment" if payment else "account.bank.statement.line",
        "id": record_id,
        "name": f"Record {record_id}",
        "state": "draft" if payment else "posted",
        "company_id": 7,
        "move_type": None if payment else "entry",
        "source_id": None if payment else record_id + 500,
        "line_ids": [1001, 1002],
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": capability_id
        in {
            "bank.transaction.match",
            "reconciliation.write_off",
        },
    }


class FakePort:
    user_id = 42

    def __init__(self, capability_id: str) -> None:
        self.capability_id = capability_id
        self.calls: list[dict] = []

    def execute(self, **kwargs) -> dict:
        self.calls.append(deepcopy(kwargs))
        return {
            "user_id": 42,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "idempotent_replay": False,
            "result": _result(self.capability_id),
        }


@pytest.mark.parametrize("capability_id", sorted(CAPABILITIES))
def test_payment_bank_write_contract_and_dispatch(capability_id: str) -> None:
    assert capability_id in CORE_WRITE_CAPABILITY_IDS
    request = _request(capability_id)
    _, _, normalized = validate_core_write_request(capability_id, request)
    if capability_id == "payment.create":
        assert normalized["payment_reference"] is None

    port = FakePort(capability_id)
    data = execute_core_write(
        port, capability_id, request, _key(capability_id), capability_id
    )

    assert data == {"idempotent_replay": False, "result": _result(capability_id)}
    assert port.calls == [
        {
            "capability_id": capability_id,
            "company_id": 7,
            "idempotency_key": _key(capability_id),
            "confirmation": capability_id,
            "parameters": normalized,
        }
    ]


@pytest.mark.parametrize(
    ("capability_id", "field", "value"),
    [
        ("payment.create", "amount", "0"),
        ("payment.create", "payment_type", "transfer"),
        ("payment.update_draft", "changes", {}),
        ("bank.transaction.update", "changes", {}),
        ("bank.transaction.match", "candidate_line_ids", [102, 101]),
        ("reconciliation.write_off", "expected_residual_amount", "0"),
    ],
)
def test_payment_bank_write_rejects_invalid_fixed_parameters(
    capability_id: str, field: str, value: object
) -> None:
    request = _request(capability_id)
    request["parameters"][field] = value
    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request(capability_id, request)
    assert caught.value.code == "invalid_request"


def test_payment_update_key_is_bound_to_the_normalized_target() -> None:
    request = _request("payment.update_draft")
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            FakePort("payment.update_draft"),
            "payment.update_draft",
            request,
            "payment.update_draft:31:00000000000000000000000000000000",
            "payment.update_draft",
        )
    assert caught.value.code == "invalid_idempotency_key"


def test_bank_write_rejects_a_mismatched_result_id() -> None:
    class MismatchedPort(FakePort):
        def execute(self, **kwargs) -> dict:
            page = super().execute(**kwargs)
            page["result"]["id"] = 999
            return page

    capability_id = "bank.transaction.match"
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            MismatchedPort(capability_id),
            capability_id,
            _request(capability_id),
            _key(capability_id),
            capability_id,
        )
    assert caught.value.code == "failed_validation"
