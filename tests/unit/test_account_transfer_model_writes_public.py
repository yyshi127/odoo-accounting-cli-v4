from __future__ import annotations

import hashlib
import io
import json
from copy import deepcopy

import pytest

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4.capabilities.core_writes import (
    CORE_WRITE_CAPABILITY_IDS,
    CoreWriteError,
    _expected_idempotency_key,
    execute_core_write,
    validate_core_write_request,
)

CAPABILITIES = {
    "account.transfer_model.create",
    "account.transfer_model.update",
    "account.transfer_model.duplicate",
    "account.transfer_model.enable",
    "account.transfer_model.disable",
    "account.transfer_model.archive",
    "account.transfer_model.restore",
    "account.transfer_model.delete",
}
CREATE_PARAMETERS = {
    "name": "Monthly expense transfer",
    "journal_id": 11,
    "date_start": "2026-01-01",
    "date_stop": None,
    "frequency": "month",
    "origin_account_ids": [32, 31],
    "destination_lines": [
        {"account_id": 41, "percentage": "60"},
        {"account_id": 42, "percentage": "40"},
    ],
}
PARAMETERS = {
    "account.transfer_model.create": CREATE_PARAMETERS,
    "account.transfer_model.update": {
        "transfer_model_id": 21,
        "changes": {"frequency": "quarter", "origin_account_ids": [32, 31]},
    },
    "account.transfer_model.duplicate": {
        "transfer_model_id": 21,
        "name": "Monthly expense transfer copy",
    },
    **{
        capability_id: {"transfer_model_id": 21}
        for capability_id in CAPABILITIES
        if capability_id
        not in {
            "account.transfer_model.create",
            "account.transfer_model.update",
            "account.transfer_model.duplicate",
        }
    },
}


def _request(capability_id: str, parameters: dict | None = None) -> dict:
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
        "parameters": deepcopy(
            PARAMETERS[capability_id] if parameters is None else parameters
        ),
    }


def _digest(value: object) -> str:
    canonical = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(canonical).hexdigest()[:32]


def _key(capability_id: str) -> str:
    parameters = validate_core_write_request(capability_id, _request(capability_id))[2]
    if capability_id in {
        "account.transfer_model.create",
        "account.transfer_model.duplicate",
    }:
        return f"{capability_id}:7:{_digest(parameters)}"
    if capability_id == "account.transfer_model.update":
        return f"{capability_id}:21:{_digest(parameters['changes'])}"
    return f"{capability_id}:21"


class SuccessPort:
    user_id = 42

    def __init__(self, capability_id: str) -> None:
        self.capability_id = capability_id
        self.calls: list[dict] = []

    def execute(self, **kwargs: object) -> dict:
        self.calls.append(deepcopy(kwargs))
        parameters = kwargs["parameters"]
        assert isinstance(parameters, dict)
        creates_record = self.capability_id in {
            "account.transfer_model.create",
            "account.transfer_model.duplicate",
        }
        return {
            "user_id": self.user_id,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "idempotent_replay": False,
            "result": {
                "model": "account.transfer.model",
                "id": 902 if creates_record else parameters["transfer_model_id"],
                "name": "Monthly expense transfer",
                "state": {
                    "account.transfer_model.enable": "in_progress",
                    "account.transfer_model.archive": "archived",
                    "account.transfer_model.delete": "deleted",
                }.get(self.capability_id, "disabled"),
                "company_id": 7,
                "move_type": None,
                "source_id": (
                    parameters["transfer_model_id"]
                    if self.capability_id == "account.transfer_model.duplicate"
                    else None
                ),
                "line_ids": [],
                "partial_reconcile_ids": [],
                "full_reconcile_id": None,
                "reconciled": False,
            },
        }


def test_transfer_model_contracts_normalize_only_origin_account_order() -> None:
    assert CAPABILITIES <= CORE_WRITE_CAPABILITY_IDS
    _, _, created = validate_core_write_request(
        "account.transfer_model.create", _request("account.transfer_model.create")
    )
    _, _, updated = validate_core_write_request(
        "account.transfer_model.update", _request("account.transfer_model.update")
    )

    assert created["origin_account_ids"] == [31, 32]
    assert created["destination_lines"] == CREATE_PARAMETERS["destination_lines"]
    assert updated["changes"]["origin_account_ids"] == [31, 32]


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    [
        ("account.transfer_model.create", {**CREATE_PARAMETERS, "date_stop": "bad"}),
        (
            "account.transfer_model.create",
            {**CREATE_PARAMETERS, "date_stop": "2025-12-31"},
        ),
        (
            "account.transfer_model.create",
            {**CREATE_PARAMETERS, "origin_account_ids": [31, 31]},
        ),
        (
            "account.transfer_model.create",
            {
                **CREATE_PARAMETERS,
                "destination_lines": [{"account_id": 41, "percentage": "0"}],
            },
        ),
        (
            "account.transfer_model.create",
            {
                **CREATE_PARAMETERS,
                "destination_lines": [{"account_id": 41, "percentage": "1.0"}],
            },
        ),
        (
            "account.transfer_model.create",
            {
                **CREATE_PARAMETERS,
                "destination_lines": [
                    {"account_id": 41, "percentage": "60"},
                    {"account_id": 42, "percentage": "41"},
                ],
            },
        ),
        (
            "account.transfer_model.create",
            {
                **CREATE_PARAMETERS,
                "destination_lines": [
                    {"account_id": 41, "percentage": "33.3333333"}
                ],
            },
        ),
        ("account.transfer_model.update", {"transfer_model_id": 21, "changes": {}}),
        ("account.transfer_model.enable", {"transfer_model_id": 0}),
    ],
)
def test_transfer_model_contract_rejects_invalid_or_expanded_values(
    capability_id: str, parameters: dict
) -> None:
    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request(capability_id, _request(capability_id, parameters))
    assert caught.value.code == "invalid_request"


def test_transfer_model_idempotency_keys_are_frozen() -> None:
    for capability_id in CAPABILITIES:
        parameters = validate_core_write_request(
            capability_id, _request(capability_id)
        )[2]
        assert _expected_idempotency_key(capability_id, parameters, 7) == _key(
            capability_id
        )


@pytest.mark.parametrize("capability_id", sorted(CAPABILITIES))
def test_public_execution_validates_every_transfer_model_result(
    capability_id: str,
) -> None:
    result = execute_core_write(
        SuccessPort(capability_id),
        capability_id,
        _request(capability_id),
        _key(capability_id),
        capability_id,
    )
    assert result["result"]["model"] == "account.transfer.model"


@pytest.mark.parametrize("capability_id", sorted(CAPABILITIES))
def test_cli_routes_every_transfer_model_write(capability_id: str) -> None:
    stdout = io.StringIO()
    stderr = io.StringIO()
    ports: list[SuccessPort] = []

    def port_factory(selected: str, _document: dict) -> SuccessPort:
        port = SuccessPort(selected)
        ports.append(port)
        return port

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
        port_factory=port_factory,
    )

    document = json.loads(stdout.getvalue())
    assert exit_code == 0
    assert stderr.getvalue() == ""
    assert document["capability"] == capability_id
    assert document["odoo"]["model"] == "account.transfer.model"
    assert ports[0].calls[0]["confirmation"] == capability_id
