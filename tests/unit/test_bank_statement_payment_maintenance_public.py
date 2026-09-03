from __future__ import annotations

import hashlib
import json
import re
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
from odoo_accounting_cli_v4.registry import load_registry

CAPABILITIES = {
    "bank.statement.create",
    "bank.statement.update",
    "bank.statement.delete",
    "bank.transaction.delete",
    "payment.duplicate",
    "payment.delete",
}
PARAMETERS = {
    "bank.statement.create": {
        "transaction_ids": [32, 31],
        "reference": "August statement",
        "balance_end_real": "1250.5",
    },
    "bank.statement.update": {
        "statement_id": 21,
        "changes": {"reference": None, "balance_end_real": "1300"},
    },
    "bank.statement.delete": {"statement_id": 21},
    "bank.transaction.delete": {"transaction_id": 31},
    "payment.duplicate": {"payment_id": 41},
    "payment.delete": {"payment_id": 41},
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
    if capability_id == "bank.statement.create":
        return f"bank.statement.create:7:{_digest(parameters)}"
    if capability_id == "bank.statement.update":
        return f"bank.statement.update:21:{_digest(parameters['changes'])}"
    target = parameters.get(
        "statement_id", parameters.get("transaction_id", parameters.get("payment_id"))
    )
    return f"{capability_id}:{target}"


class SuccessPort:
    user_id = 42

    def __init__(self, capability_id: str) -> None:
        self.capability_id = capability_id

    def execute(self, **kwargs: object) -> dict:
        parameters = kwargs["parameters"]
        assert isinstance(parameters, dict)
        if self.capability_id.startswith("bank.statement."):
            result = {
                "model": "account.bank.statement",
                "id": 902
                if self.capability_id == "bank.statement.create"
                else parameters["statement_id"],
                "name": "BNK Statement 2026-08",
                "state": "deleted"
                if self.capability_id == "bank.statement.delete"
                else "complete",
                "source_id": None,
                "line_ids": [31, 32],
            }
        elif self.capability_id == "bank.transaction.delete":
            result = {
                "model": "account.bank.statement.line",
                "id": parameters["transaction_id"],
                "name": "Deleted bank transaction",
                "state": "deleted",
                "source_id": 21,
                "move_type": "entry",
                "line_ids": [51, 52],
            }
        else:
            duplicate = self.capability_id == "payment.duplicate"
            result = {
                "model": "account.payment",
                "id": 902 if duplicate else parameters["payment_id"],
                "name": None,
                "state": "draft" if duplicate else "deleted",
                "source_id": parameters["payment_id"] if duplicate else None,
                "line_ids": [],
            }
        return {
            "user_id": self.user_id,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "idempotent_replay": False,
            "result": {
                **result,
                "company_id": 7,
                "move_type": result.get("move_type"),
                "partial_reconcile_ids": [],
                "full_reconcile_id": None,
                "reconciled": False,
            },
        }


def test_closed_contracts_and_cli_models_cover_the_batch() -> None:
    assert CAPABILITIES <= CORE_WRITE_CAPABILITY_IDS
    assert (
        cli._CAPABILITY_MODELS
        | {
            capability_id: (
                "account.bank.statement"
                if capability_id.startswith("bank.statement.")
                else "account.bank.statement.line"
                if capability_id == "bank.transaction.delete"
                else "account.payment"
            )
            for capability_id in CAPABILITIES
        }
        == cli._CAPABILITY_MODELS
    )

    normalized = validate_core_write_request(
        "bank.statement.create", _request("bank.statement.create")
    )[2]
    assert normalized["transaction_ids"] == [31, 32]


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    [
        (
            "bank.statement.create",
            {**PARAMETERS["bank.statement.create"], "transaction_ids": [31, 31]},
        ),
        (
            "bank.statement.create",
            {**PARAMETERS["bank.statement.create"], "reference": " padded "},
        ),
        (
            "bank.statement.create",
            {**PARAMETERS["bank.statement.create"], "balance_end_real": "1.0"},
        ),
        ("bank.statement.update", {"statement_id": 21, "changes": {}}),
        ("bank.statement.update", {"statement_id": 21, "changes": {"extra": 1}}),
        ("bank.statement.delete", {"statement_id": 0}),
        ("bank.transaction.delete", {"transaction_id": 31, "extra": True}),
        ("payment.duplicate", {"payment_id": True}),
    ],
)
def test_closed_contracts_reject_invalid_values(
    capability_id: str, parameters: dict
) -> None:
    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request(capability_id, _request(capability_id, parameters))
    assert caught.value.code == "invalid_request"


def test_idempotency_keys_are_frozen() -> None:
    for capability_id in CAPABILITIES:
        parameters = validate_core_write_request(
            capability_id, _request(capability_id)
        )[2]
        assert _expected_idempotency_key(capability_id, parameters, 7) == _key(
            capability_id
        )


def test_bank_statement_schemas_accept_only_canonical_signed_decimals() -> None:
    registry = load_registry()
    for capability_id in ("bank.statement.create", "bank.statement.update"):
        schema = registry.load_schema(
            f"schemas/v1/{capability_id}.request.schema.json"
        )
        pattern = schema["$defs"]["signedDecimal"]["pattern"]
        assert all(
            re.fullmatch(pattern, value) is not None
            for value in ("0", "1", "-1", "0.01", "-0.01", "10.25")
        )
        assert all(
            re.fullmatch(pattern, value) is None
            for value in ("-0", "1.0", "1.00", "0.0", "01", ".5", "1.")
        )


@pytest.mark.parametrize("capability_id", sorted(CAPABILITIES))
def test_public_execution_validates_each_result(capability_id: str) -> None:
    page = execute_core_write(
        SuccessPort(capability_id),
        capability_id,
        _request(capability_id),
        _key(capability_id),
        capability_id,
    )
    assert page["result"]["model"] == cli._CAPABILITY_MODELS[capability_id]


@pytest.mark.parametrize(
    "capability_id",
    ["bank.statement.delete", "bank.transaction.delete", "payment.delete"],
)
def test_delete_results_cannot_claim_successful_replay(capability_id: str) -> None:
    port = SuccessPort(capability_id)
    original_execute = port.execute

    def replaying_execute(**kwargs: object) -> dict:
        page = original_execute(**kwargs)
        page["idempotent_replay"] = True
        return page

    port.execute = replaying_execute  # type: ignore[method-assign]
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            port,
            capability_id,
            _request(capability_id),
            _key(capability_id),
            capability_id,
        )
    assert caught.value.code == "failed_validation"


@pytest.mark.parametrize(
    ("capability_id", "bad_line_ids"),
    [
        ("bank.statement.create", [31]),
        ("bank.transaction.delete", []),
    ],
)
def test_bank_results_require_the_frozen_source_lines(
    capability_id: str, bad_line_ids: list[int]
) -> None:
    port = SuccessPort(capability_id)
    original_execute = port.execute

    def broken_execute(**kwargs: object) -> dict:
        page = original_execute(**kwargs)
        page["result"]["line_ids"] = bad_line_ids
        return page

    port.execute = broken_execute  # type: ignore[method-assign]
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            port,
            capability_id,
            _request(capability_id),
            _key(capability_id),
            capability_id,
        )
    assert caught.value.code == "failed_validation"
