from __future__ import annotations

import io
import json
from copy import deepcopy
from typing import Any

import pytest

from odoo_accounting_cli_v4.capabilities.core_writes import (
    _expected_idempotency_key,
    validate_core_write_request,
)
from odoo_accounting_cli_v4.cli import main

CAPABILITY_IDS = (
    "sale.order.invoice.create",
    "stock.transfer.create",
    "stock.transfer.confirm",
    "stock.transfer.assign",
    "stock.transfer.quantities.set",
    "stock.transfer.validate",
    "stock.transfer.unreserve",
    "stock.transfer.cancel",
)
PARAMETERS: dict[str, dict[str, Any]] = {
    "sale.order.invoice.create": {"order_id": 101},
    "stock.transfer.create": {
        "picking_type_id": 2,
        "location_id": 8,
        "location_dest_id": 9,
        "partner_id": None,
        "scheduled_date": "2026-08-30 08:00:00",
        "origin": "CLI transfer",
        "moves": [
            {
                "product_id": 51,
                "name": "Stock item",
                "quantity": "3",
                "uom_id": 1,
            }
        ],
    },
    "stock.transfer.confirm": {"transfer_id": 401},
    "stock.transfer.assign": {"transfer_id": 401},
    "stock.transfer.quantities.set": {
        "transfer_id": 401,
        "lines": [
            {"move_id": 502, "quantity": "0"},
            {"move_id": 501, "quantity": "2.5"},
        ],
    },
    "stock.transfer.validate": {
        "transfer_id": 401,
        "backorder_policy": "create",
    },
    "stock.transfer.unreserve": {"transfer_id": 401},
    "stock.transfer.cancel": {"transfer_id": 401},
}


def _request(capability_id: str) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "request_id": "7bc39413-0d69-4092-9319-795d33f3167c",
        "context": {
            "database": "v4-dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": deepcopy(PARAMETERS[capability_id]),
    }


def _normalized_and_key(capability_id: str) -> tuple[dict[str, Any], str]:
    _, context, normalized = validate_core_write_request(
        capability_id, _request(capability_id)
    )
    expected = _expected_idempotency_key(
        capability_id, normalized, context["company_id"]
    )
    return normalized, expected or "caller-stock-transfer-create-key"


def _result(capability_id: str) -> dict[str, Any]:
    invoice = capability_id == "sale.order.invoice.create"
    state = {
        "sale.order.invoice.create": "draft",
        "stock.transfer.create": "draft",
        "stock.transfer.confirm": "confirmed",
        "stock.transfer.assign": "assigned",
        "stock.transfer.quantities.set": "assigned",
        "stock.transfer.validate": "done",
        "stock.transfer.unreserve": "confirmed",
        "stock.transfer.cancel": "cancel",
    }[capability_id]
    return {
        "model": "account.move" if invoice else "stock.picking",
        "id": 907
        if invoice
        else 908
        if capability_id == "stock.transfer.create"
        else 401,
        "name": "INV/2026/00907" if invoice else "WH/INT/00908",
        "state": state,
        "company_id": 7,
        "move_type": "out_invoice" if invoice else None,
        "source_id": 101 if invoice else 2,
        "line_ids": [501],
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }


class Port:
    user_id = 42

    def __init__(
        self,
        capability_id: str,
        *,
        replay: bool = False,
        access_allowed: bool = True,
        result: dict[str, Any] | None = None,
    ) -> None:
        self.capability_id = capability_id
        self.replay = replay
        self.access_allowed = access_allowed
        self.result = result if result is not None else _result(capability_id)
        self.calls: list[dict[str, Any]] = []

    def execute(self, **payload: Any) -> dict[str, Any]:
        self.calls.append(deepcopy(payload))
        return {
            "user_id": self.user_id,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": self.access_allowed,
            "idempotent_replay": self.replay,
            "result": deepcopy(self.result) if self.access_allowed else None,
        }


def _run(
    capability_id: str,
    port: Port,
    *,
    key: str | None = None,
    confirmation: str | None = None,
    request: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any], str]:
    _, expected_key = _normalized_and_key(capability_id)
    stdout = io.StringIO()
    stderr = io.StringIO()
    code = main(
        [
            "write",
            "run",
            capability_id,
            "--request",
            "-",
            "--idempotency-key",
            key or expected_key,
            "--confirm",
            confirmation or capability_id,
        ],
        stdin=io.StringIO(json.dumps(request or _request(capability_id))),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda selected, _document: (
            port if selected == capability_id else None
        ),
    )
    return code, json.loads(stdout.getvalue()), stderr.getvalue()


@pytest.mark.parametrize("capability_id", CAPABILITY_IDS)
def test_all_eight_writes_use_the_public_write_run_path(capability_id: str) -> None:
    normalized, key = _normalized_and_key(capability_id)
    port = Port(capability_id)

    code, document, stderr = _run(capability_id, port)

    result = _result(capability_id)
    assert code == 0
    assert stderr == ""
    assert port.calls == [
        {
            "capability_id": capability_id,
            "company_id": 7,
            "idempotency_key": key,
            "confirmation": capability_id,
            "parameters": normalized,
        }
    ]
    assert document["success"] is True
    assert document["capability"] == capability_id
    assert document["status"] == "verified"
    assert document["odoo"] == {
        "database": "v4-dev",
        "company_id": 7,
        "user_id": 42,
        "model": result["model"],
        "record_ids": [result["id"]],
    }
    assert document["audit"] == {
        "operation_id": None,
        "idempotency_key": key,
        "verification": {
            "company_id": 7,
            "state": result["state"],
            "reconciled": False,
            "idempotent_replay": False,
        },
    }


@pytest.mark.parametrize("capability_id", CAPABILITY_IDS)
def test_public_cli_requires_exact_confirmation_before_port_execution(
    capability_id: str,
) -> None:
    port = Port(capability_id)
    code, document, stderr = _run(
        capability_id, port, confirmation=f"{capability_id}.typo"
    )
    assert code == 2
    assert stderr == ""
    assert port.calls == []
    assert document["success"] is False
    assert document["error"]["code"] == "confirmation_required"
    assert document["odoo"]["model"] == (
        "account.move"
        if capability_id == "sale.order.invoice.create"
        else "stock.picking"
    )
    assert document["odoo"]["record_ids"] == []


def test_public_cli_surfaces_idempotent_replay_in_audit_metadata() -> None:
    capability_id = "stock.transfer.confirm"
    port = Port(capability_id, replay=True)
    code, document, _ = _run(capability_id, port)
    assert code == 0
    assert document["data"]["idempotent_replay"] is True
    assert document["audit"]["verification"]["idempotent_replay"] is True


def test_public_cli_rejects_a_wrong_deterministic_key_before_port_execution() -> None:
    capability_id = "stock.transfer.validate"
    port = Port(capability_id)
    code, document, _ = _run(capability_id, port, key="safe-but-wrong-key")
    assert code == 2
    assert port.calls == []
    assert document["error"]["code"] == "invalid_idempotency_key"
    assert document["audit"]["idempotency_key"] == "safe-but-wrong-key"


def test_public_cli_normalizes_denied_runtime_gate_to_one_json_error() -> None:
    capability_id = "stock.transfer.assign"
    port = Port(capability_id, access_allowed=False)
    code, document, stderr = _run(capability_id, port)
    assert code == 3
    assert stderr == ""
    assert document["success"] is False
    assert document["status"] == "denied"
    assert document["error"] == {
        "code": "unauthorized",
        "message": "The configured user cannot execute this accounting write.",
        "details": {},
        "retryable": False,
    }
    assert document["odoo"] == {
        "database": "v4-dev",
        "company_id": 7,
        "user_id": 42,
        "model": "stock.picking",
        "record_ids": [],
    }


def test_public_cli_normalizes_result_drift_to_failed_validation() -> None:
    capability_id = "sale.order.invoice.create"
    malformed = _result(capability_id)
    malformed["model"] = "res.partner"
    port = Port(capability_id, result=malformed)
    code, document, stderr = _run(capability_id, port)
    assert code == 8
    assert stderr == ""
    assert document["status"] == "failed_validation"
    assert document["error"]["code"] == "failed_validation"
    assert document["odoo"]["model"] == "account.move"
    assert document["odoo"]["record_ids"] == []
