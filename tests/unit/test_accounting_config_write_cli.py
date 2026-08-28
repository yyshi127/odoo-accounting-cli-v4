from __future__ import annotations

import hashlib
import io
import json
from copy import deepcopy

import pytest

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4.bridge.core_writes import OdooCoreWritePort
from odoo_accounting_cli_v4.capabilities.core_writes import (
    CORE_WRITE_CAPABILITY_IDS,
    validate_core_write_request,
)

CAPABILITIES = {
    "account.account.create",
    "account.account.update",
    "account.account.archive",
    "account.account.restore",
    "journal.create",
    "journal.update",
    "journal.archive",
    "journal.restore",
    "tax.create",
    "tax.update",
    "tax.archive",
    "tax.restore",
}
PARAMETERS = {
    "account.account.create": {
        "code": "1100",
        "name": "Trade Receivables",
        "account_type": "asset_receivable",
    },
    "account.account.update": {
        "account_id": 21,
        "changes": {"name": "Customer Receivables"},
    },
    "account.account.archive": {"account_id": 22},
    "account.account.restore": {"account_id": 23},
    "journal.create": {"name": "Bank", "code": "bnk", "type": "bank"},
    "journal.update": {"journal_id": 31, "changes": {"code": "bn2"}},
    "journal.archive": {"journal_id": 32},
    "journal.restore": {"journal_id": 33},
    "tax.create": {
        "name": "Sales Tax 15%",
        "type_tax_use": "sale",
        "amount_type": "percent",
        "amount": 15,
    },
    "tax.update": {"tax_id": 41, "changes": {"amount": 12.5}},
    "tax.archive": {"tax_id": 42},
    "tax.restore": {"tax_id": 43},
}


def _request(capability_id: str) -> dict:
    return {
        "schema_version": "v1",
        "request_id": "32f91531-a230-4dde-a8bf-e56bb03bdaba",
        "context": {
            "database": "odoo_cli_v4_dev",
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
    parameters = validate_core_write_request(capability_id, _request(capability_id))[2]
    if capability_id.endswith(".create"):
        return f"{capability_id}:7:{_digest(parameters)}"
    if capability_id.endswith(".update"):
        primary = {
            "account.account.update": "account_id",
            "journal.update": "journal_id",
            "tax.update": "tax_id",
        }[capability_id]
        return f"{capability_id}:{parameters[primary]}:{_digest(parameters['changes'])}"
    primary = (
        "account_id"
        if capability_id.startswith("account.account.")
        else "journal_id"
        if capability_id.startswith("journal.")
        else "tax_id"
    )
    return f"{capability_id}:{parameters[primary]}"


class SuccessPort:
    user_id = 42

    def __init__(self, capability_id: str) -> None:
        self.capability_id = capability_id

    def execute(self, **kwargs: object) -> dict:
        parameters = kwargs["parameters"]
        assert isinstance(parameters, dict)
        if self.capability_id == "account.account.create":
            assert parameters["reconcile"] is True
        if self.capability_id == "tax.create":
            assert parameters["amount"] == "15"
        model = cli._CAPABILITY_MODELS[self.capability_id]
        record_id = (
            901
            if self.capability_id.endswith(".create")
            else parameters.get(
                "account_id", parameters.get("journal_id", parameters.get("tax_id"))
            )
        )
        return {
            "user_id": 42,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "idempotent_replay": False,
            "result": {
                "model": model,
                "id": record_id,
                "name": "Configured record",
                "state": (
                    "archived" if self.capability_id.endswith(".archive") else "active"
                ),
                "company_id": 7,
                "move_type": None,
                "source_id": None,
                "line_ids": [],
                "partial_reconcile_ids": [],
                "full_reconcile_id": None,
                "reconciled": False,
            },
        }


@pytest.mark.parametrize("capability_id", sorted(CAPABILITIES))
def test_cli_routes_each_accounting_configuration_write(capability_id: str) -> None:
    assert capability_id in CORE_WRITE_CAPABILITY_IDS
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


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    [
        (
            "account.account.create",
            {
                "code": "1100",
                "name": "Trade Receivables",
                "account_type": "asset_receivable",
                "reconcile": False,
            },
        ),
        ("tax.update", {"tax_id": 41, "changes": {"amount": 0.12345}}),
    ],
)
def test_cli_rejects_odoo_incompatible_configuration_values(
    capability_id: str, parameters: dict
) -> None:
    request = _request(capability_id)
    request["parameters"] = parameters
    stdout = io.StringIO()
    exit_code = cli.main(
        [
            "write",
            "run",
            capability_id,
            "--request",
            "-",
            "--idempotency-key",
            "invalid-request-0001",
            "--confirm",
            capability_id,
        ],
        stdin=io.StringIO(json.dumps(request)),
        stdout=stdout,
        stderr=io.StringIO(),
        port_factory=lambda *_args: pytest.fail("invalid request reached the port"),
    )
    document = json.loads(stdout.getvalue())
    assert exit_code == 2
    assert document["error"]["code"] == "invalid_request"


@pytest.mark.parametrize("capability_id", sorted(CAPABILITIES))
def test_configured_factory_routes_configuration_writes_to_core_port(
    capability_id: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = object()
    client = object()

    class RuntimeConfig:
        def resolve(self, database: str, company_id: int, user_login: str) -> object:
            assert (database, company_id, user_login) == (
                "odoo_cli_v4_dev",
                7,
                "v4-agent",
            )
            return target

    monkeypatch.setattr(cli, "load_runtime_config", lambda _path: RuntimeConfig())
    monkeypatch.setattr(cli, "OdooBridgeClient", lambda *_args, **_kwargs: client)
    port = cli._configured_port_factory(capability_id, _request(capability_id))
    assert type(port) is OdooCoreWritePort
    assert port._client is client
