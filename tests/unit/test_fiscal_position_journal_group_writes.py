from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from odoo_accounting_cli_v4.capabilities.core_writes import (
    CORE_WRITE_CAPABILITY_IDS,
    CoreWriteError,
    execute_core_write,
    validate_core_write_request,
)
from odoo_accounting_cli_v4.registry import load_registry

PARAMETERS = {
    "fiscal_position.create": {"name": " EU ", "state_ids": [3, 1]},
    "fiscal_position.update": {
        "fiscal_position_id": 11,
        "changes": {"note": " Updated "},
    },
    "fiscal_position.account_mappings.replace": {
        "fiscal_position_id": 11,
        "mappings": [
            {"source_account_id": 9, "destination_account_id": 19},
            {"source_account_id": 3, "destination_account_id": 13},
        ],
    },
    "fiscal_position.archive": {"fiscal_position_id": 11},
    "fiscal_position.restore": {"fiscal_position_id": 11},
    "journal.group.create": {"name": " Cash ", "excluded_journal_ids": [8, 2]},
    "journal.group.update": {
        "journal_group_id": 21,
        "changes": {"sequence": 4, "excluded_journal_ids": []},
    },
}


def _request(capability_id: str, parameters: dict | None = None) -> dict:
    return {
        "schema_version": "v1",
        "request_id": "31f91531-a230-4dde-a8bf-e56bb03bdaba",
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
    raw = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(raw).hexdigest()[:32]


def _key(capability_id: str, parameters: dict) -> str:
    if capability_id.endswith(".create"):
        return f"{capability_id}:7:{_digest(parameters)}"
    if capability_id.endswith(".update"):
        field = (
            "fiscal_position_id"
            if capability_id.startswith("fiscal_position")
            else "journal_group_id"
        )
        return f"{capability_id}:{parameters[field]}:{_digest(parameters['changes'])}"
    if capability_id.endswith("mappings.replace"):
        return f"{capability_id}:{parameters['fiscal_position_id']}:{_digest(parameters['mappings'])}"
    return f"{capability_id}:{parameters['fiscal_position_id']}"


class Port:
    user_id = 5

    def __init__(self, result: dict) -> None:
        self.result = result

    def execute(self, **kwargs: object) -> dict:
        return {
            "user_id": 5,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "idempotent_replay": False,
            "result": deepcopy(self.result),
        }


@pytest.mark.parametrize("capability_id", sorted(PARAMETERS))
def test_closed_contract_idempotency_and_result(capability_id: str) -> None:
    assert capability_id in CORE_WRITE_CAPABILITY_IDS
    request = _request(capability_id)
    normalized = validate_core_write_request(capability_id, request)[2]
    is_fiscal = capability_id.startswith("fiscal_position")
    record_id = normalized.get(
        "fiscal_position_id", normalized.get("journal_group_id", 101)
    )
    line_ids = list(range(1, len(normalized.get("mappings", [])) + 1))
    state = "archived" if capability_id.endswith("archive") else "active"
    result = {
        "model": "account.fiscal.position" if is_fiscal else "account.journal.group",
        "id": record_id,
        "name": "Configured",
        "state": state,
        "company_id": 7,
        "move_type": None,
        "source_id": None,
        "line_ids": line_ids,
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }
    data = execute_core_write(
        Port(result),
        capability_id,
        request,
        _key(capability_id, normalized),
        capability_id,
    )
    assert data["result"] == result


def test_normalization_and_invalid_boundaries() -> None:
    assert validate_core_write_request(
        "fiscal_position.create", _request("fiscal_position.create")
    )[2] == {"name": "EU", "state_ids": [1, 3]}
    assert validate_core_write_request(
        "journal.group.create", _request("journal.group.create")
    )[2] == {"name": "Cash", "excluded_journal_ids": [2, 8]}
    assert validate_core_write_request(
        "fiscal_position.account_mappings.replace",
        _request(
            "fiscal_position.account_mappings.replace",
            {"fiscal_position_id": 11, "mappings": []},
        ),
    )[2] == {"fiscal_position_id": 11, "mappings": []}
    assert validate_core_write_request(
        "journal.group.create",
        _request("journal.group.create", {"name": "X" * 256}),
    )[2]["name"] == "X" * 256
    invalid = [
        ("fiscal_position.create", {"name": "X", "company_id": 7}),
        ("fiscal_position.update", {"fiscal_position_id": 1, "changes": {}}),
        (
            "fiscal_position.account_mappings.replace",
            {
                "fiscal_position_id": 1,
                "mappings": [{"source_account_id": 2, "destination_account_id": 2}],
            },
        ),
        ("journal.group.update", {"journal_group_id": 1, "changes": {"active": False}}),
    ]
    for capability_id, parameters in invalid:
        with pytest.raises(CoreWriteError, match="fixed contract|unique, distinct"):
            validate_core_write_request(
                capability_id, _request(capability_id, parameters)
            )


def test_fourteen_specialized_schemas_accept_contracts() -> None:
    registry = load_registry()
    schema_root = Path(__file__).parents[2] / "schemas" / "v1"
    for capability_id, parameters in PARAMETERS.items():
        request_path = f"schemas/v1/{capability_id}.request.schema.json"
        response_path = f"schemas/v1/{capability_id}.response.schema.json"
        assert (schema_root / f"{capability_id}.request.schema.json").is_file()
        assert (schema_root / f"{capability_id}.response.schema.json").is_file()
        registry.validate_instance(request_path, _request(capability_id, parameters))
        registry.validate_instance(
            response_path,
            {
                "schema_version": "v1",
                "request_id": "31f91531-a230-4dde-a8bf-e56bb03bdaba",
                "capability": capability_id,
                "status": "verified",
                "success": True,
                "data": {
                    "idempotent_replay": False,
                    "result": {
                        "model": "account.fiscal.position",
                        "id": 1,
                        "name": "Configured",
                        "state": "active",
                        "company_id": 7,
                        "move_type": None,
                        "source_id": None,
                        "line_ids": [],
                        "partial_reconcile_ids": [],
                        "full_reconcile_id": None,
                        "reconciled": False,
                    },
                },
                "warnings": [],
                "error": None,
                "odoo": {
                    "database": "odoo_cli_v4_dev",
                    "company_id": 7,
                    "user_id": 5,
                    "model": None,
                    "record_ids": [],
                },
                "audit": {
                    "operation_id": None,
                    "idempotency_key": None,
                    "verification": None,
                },
            },
        )
