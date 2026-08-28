from __future__ import annotations

import hashlib
import io
import json

import pytest

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4.bridge.core_writes import OdooCoreWritePort

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
        "payment_reference": None,
    },
    "payment.update_draft": {
        "payment_id": 31,
        "changes": {"payment_reference": "Receipt 31"},
    },
    "payment.reset_to_draft": {"payment_id": 32},
    "bank.transaction.update": {
        "transaction_id": 41,
        "changes": {"payment_ref": "Transfer 41"},
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
        "request_id": "99f91531-a230-4dde-a8bf-e56bb03bdaba",
        "context": {
            "database": "v4-dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": PARAMETERS[capability_id],
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
    if capability_id == "bank.transaction.unmatch":
        return "bank.transaction.unmatch:43"
    target = (
        parameters["changes"]
        if capability_id == "bank.transaction.update"
        else parameters["candidate_line_ids"]
        if capability_id == "bank.transaction.match"
        else {
            "write_off_account_id": parameters["write_off_account_id"],
            "expected_residual_amount": parameters["expected_residual_amount"],
            "label": parameters["label"],
        }
    )
    return f"{capability_id}:{parameters['transaction_id']}:{_digest(target)}"


class SuccessPort:
    user_id = 42

    def __init__(self, capability_id: str) -> None:
        self.capability_id = capability_id

    def execute(self, **kwargs) -> dict:
        payment = self.capability_id.startswith("payment.")
        parameters = PARAMETERS[self.capability_id]
        record_id = (
            901
            if self.capability_id == "payment.create"
            else parameters["payment_id"]
            if payment
            else parameters["transaction_id"]
        )
        return {
            "user_id": 42,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "idempotent_replay": False,
            "result": {
                "model": (
                    "account.payment" if payment else "account.bank.statement.line"
                ),
                "id": record_id,
                "name": f"Record {record_id}",
                "state": "draft" if payment else "posted",
                "company_id": 7,
                "move_type": None if payment else "entry",
                "source_id": None if payment else record_id + 500,
                "line_ids": [1001, 1002],
                "partial_reconcile_ids": [],
                "full_reconcile_id": None,
                "reconciled": self.capability_id
                in {"bank.transaction.match", "reconciliation.write_off"},
            },
        }


@pytest.mark.parametrize("capability_id", sorted(PARAMETERS))
def test_cli_runs_each_payment_bank_write(capability_id: str) -> None:
    stdout = io.StringIO()
    stderr = io.StringIO()
    exit_code = cli.main(
        [
            "write",
            "run",
            capability_id,
            "--request",
            "-",
            "--idempotency-key",
            _key(capability_id),
            "--confirm",
            capability_id,
        ],
        stdin=io.StringIO(json.dumps(_request(capability_id))),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda selected, _request: SuccessPort(selected),
    )
    document = json.loads(stdout.getvalue())
    assert exit_code == 0
    assert stderr.getvalue() == ""
    assert document["capability"] == capability_id
    assert document["success"] is True
    assert document["odoo"]["model"] == cli._CAPABILITY_MODELS[capability_id]


@pytest.mark.parametrize("capability_id", sorted(PARAMETERS))
def test_configured_factory_routes_writes_to_the_fixed_core_port(
    capability_id: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = object()
    client = object()

    class RuntimeConfig:
        def resolve(self, database: str, company_id: int, user_login: str) -> object:
            assert (database, company_id, user_login) == ("v4-dev", 7, "v4-agent")
            return target

    monkeypatch.setattr(cli, "load_runtime_config", lambda _path: RuntimeConfig())
    monkeypatch.setattr(cli, "OdooBridgeClient", lambda *_args, **_kwargs: client)
    port = cli._configured_port_factory(capability_id, _request(capability_id))
    assert type(port) is OdooCoreWritePort
    assert port._client is client
