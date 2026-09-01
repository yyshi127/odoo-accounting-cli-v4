from __future__ import annotations

import io
import json
from copy import deepcopy
from typing import Any

import pytest

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4.bridge.accounting_delivery import (
    OdooAccountingDeliveryPort,
)

REQUEST_ID = "7bc39413-0d69-4092-9319-795d33f3167c"
READ_CASES: dict[str, dict[str, Any]] = {
    "invoice.send.inspect": {"move_ids": [32, 31]},
    "payment.receipt.send.inspect": {"payment_id": 41},
}
WRITE_CASES: dict[str, dict[str, Any]] = {
    "invoice.send": {"move_ids": [32, 31]},
    "payment.receipt.send": {"payment_id": 41},
    "report.customer_statement.send": {
        "partner_ids": [22, 21],
        "date_from": "2026-08-01",
        "date_to": "2026-08-31",
    },
    "report.followup.send": {"partner_id": 21, "as_of": "2026-08-31"},
    "invoice.followup.update": {"move_id": 31, "no_followup": True},
}
SEND_CAPABILITY_IDS = frozenset(
    {
        "invoice.send",
        "payment.receipt.send",
        "report.customer_statement.send",
        "report.followup.send",
    }
)
MODELS = {
    "invoice.send.inspect": "account.move",
    "invoice.send": "account.move",
    "invoice.followup.update": "account.move",
    "payment.receipt.send.inspect": "account.payment",
    "payment.receipt.send": "account.payment",
    "report.customer_statement.send": "res.partner",
    "report.followup.send": "res.partner",
}


def _request(parameters: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "context": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": deepcopy(parameters),
    }


def _normalized(capability_id: str) -> dict[str, Any]:
    if capability_id in {"invoice.send.inspect", "invoice.send"}:
        return {"record_ids": [31, 32]}
    if capability_id in {"payment.receipt.send.inspect", "payment.receipt.send"}:
        return {"record_ids": [41]}
    if capability_id == "report.customer_statement.send":
        return {
            "record_ids": [21, 22],
            "date_from": "2026-08-01",
            "date_to": "2026-08-31",
        }
    if capability_id == "report.followup.send":
        return {"record_ids": [21], "as_of": "2026-08-31"}
    return {"record_id": 31, "no_followup": True}


def _inspection(record_ids: list[int]) -> dict[str, Any]:
    return {
        "records": [
            {
                "record_id": record_id,
                "partner_id": record_id + 100,
                "recipient_emails": [f"accounts-{record_id}@example.com"],
                "template_id": 4,
                "report_id": 5,
                "sending_methods": ["email"],
                "warnings": [],
                "sendable": True,
            }
            for record_id in record_ids
        ]
    }


def _result(capability_id: str) -> dict[str, Any]:
    parameters = _normalized(capability_id)
    if capability_id.endswith(".inspect"):
        return _inspection(parameters["record_ids"])
    if capability_id in SEND_CAPABILITY_IDS:
        return {
            "record_ids": parameters["record_ids"],
            "processed_count": len(parameters["record_ids"]),
        }
    return {
        "record_id": parameters["record_id"],
        "no_followup": parameters["no_followup"],
    }


class FakeDeliveryPort:
    user_id = 42

    def __init__(self, capability_id: str, *, access_allowed: bool = True) -> None:
        self.capability_id = capability_id
        self.access_allowed = access_allowed
        self.calls: list[dict[str, Any]] = []

    def execute(self, **payload: Any) -> dict[str, Any]:
        self.calls.append(deepcopy(payload))
        return {
            "user_id": self.user_id,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": self.access_allowed,
            "idempotent_replay": False,
            "result": _result(self.capability_id) if self.access_allowed else None,
        }


@pytest.mark.parametrize("capability_id", READ_CASES)
def test_execute_read_emits_exact_delivery_envelope_and_audit(
    capability_id: str,
) -> None:
    request = _request(READ_CASES[capability_id])
    port = FakeDeliveryPort(capability_id)
    factory_calls: list[tuple[str, dict[str, Any]]] = []

    def port_factory(
        selected: str, supplied_request: dict[str, Any]
    ) -> FakeDeliveryPort:
        factory_calls.append((selected, deepcopy(supplied_request)))
        return port

    document = cli._execute_read(
        capability_id,
        "-",
        stdin=io.StringIO(json.dumps(request)),
        port_factory=port_factory,
    )

    assert factory_calls == [(capability_id, request)]
    assert port.calls == [
        {
            "capability_id": capability_id,
            "company_id": 7,
            "parameters": _normalized(capability_id),
            "idempotency_key": None,
        }
    ]
    assert document == {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "success": True,
        "capability": capability_id,
        "status": "verified",
        "data": {
            "idempotent_replay": False,
            "result": _result(capability_id),
        },
        "warnings": [],
        "error": None,
        "odoo": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_id": 42,
            "model": MODELS[capability_id],
            "record_ids": _normalized(capability_id)["record_ids"],
        },
        "audit": {
            "operation_id": None,
            "idempotency_key": None,
            "verification": None,
        },
    }


@pytest.mark.parametrize("capability_id", WRITE_CASES)
def test_execute_write_run_emits_exact_delivery_envelope_and_audit(
    capability_id: str,
) -> None:
    request = _request(WRITE_CASES[capability_id])
    idempotency_key = f"delivery:{capability_id}:0001"
    port = FakeDeliveryPort(capability_id)
    factory_calls: list[tuple[str, dict[str, Any]]] = []

    def port_factory(
        selected: str, supplied_request: dict[str, Any]
    ) -> FakeDeliveryPort:
        factory_calls.append((selected, deepcopy(supplied_request)))
        return port

    document = cli._execute_write_run(
        capability_id,
        "-",
        idempotency_key,
        capability_id,
        stdin=io.StringIO(json.dumps(request)),
        port_factory=port_factory,
    )

    result = _result(capability_id)
    normalized = _normalized(capability_id)
    record_ids = (
        result["record_ids"]
        if capability_id in SEND_CAPABILITY_IDS
        else [result["record_id"]]
    )
    verification = (
        {"processed_count": result["processed_count"], "idempotent_replay": False}
        if capability_id in SEND_CAPABILITY_IDS
        else {
            "no_followup": result["no_followup"],
            "idempotent_replay": False,
        }
    )
    warnings = (
        [
            {
                "code": "capability_degraded",
                "reason_code": "odoo_queue_delivery_only",
            }
        ]
        if capability_id in SEND_CAPABILITY_IDS
        else []
    )
    assert factory_calls == [(capability_id, request)]
    assert port.calls == [
        {
            "capability_id": capability_id,
            "company_id": 7,
            "parameters": normalized,
            "idempotency_key": idempotency_key,
        }
    ]
    assert document == {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "success": True,
        "capability": capability_id,
        "status": "verified",
        "data": {"idempotent_replay": False, "result": result},
        "warnings": warnings,
        "error": None,
        "odoo": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_id": 42,
            "model": MODELS[capability_id],
            "record_ids": record_ids,
        },
        "audit": {
            "operation_id": None,
            "idempotency_key": idempotency_key,
            "verification": verification,
        },
    }


@pytest.mark.parametrize(
    ("capability_id", "parameters", "is_write"),
    (
        ("invoice.send.inspect", READ_CASES["invoice.send.inspect"], False),
        ("invoice.send", WRITE_CASES["invoice.send"], True),
    ),
)
def test_delivery_errors_map_to_scoped_cli_errors(
    capability_id: str,
    parameters: dict[str, Any],
    is_write: bool,
) -> None:
    request = _request(parameters)
    port = FakeDeliveryPort(capability_id, access_allowed=False)
    idempotency_key = f"delivery:{capability_id}:0001" if is_write else None

    with pytest.raises(cli.CliError) as caught:
        if is_write:
            cli._execute_write_run(
                capability_id,
                "-",
                idempotency_key,
                capability_id,
                stdin=io.StringIO(json.dumps(request)),
                port_factory=lambda _selected, _request: port,
            )
        else:
            cli._execute_read(
                capability_id,
                "-",
                stdin=io.StringIO(json.dumps(request)),
                port_factory=lambda _selected, _request: port,
            )

    error = caught.value
    assert error.code == "unauthorized"
    assert error.exit_code == 3
    assert error.status == "denied"
    assert error.capability == capability_id
    assert error.request_id == REQUEST_ID
    assert error.database == "odoo_cli_v4_dev"
    assert error.company_id == 7
    assert error.user_id == 42
    assert error.model == MODELS[capability_id]
    assert error.idempotency_key == idempotency_key


def test_registry_routes_all_seven_delivery_capabilities() -> None:
    registry = cli.load_registry()
    expected_handlers = {
        "invoice.send.inspect": "invoice_send_inspect",
        "payment.receipt.send.inspect": "payment_receipt_send_inspect",
        **{capability_id: "accounting_delivery" for capability_id in WRITE_CASES},
    }

    for capability_id, handler_key in expected_handlers.items():
        descriptor = registry.describe(capability_id)
        assert descriptor["handler_key"] == handler_key
        assert descriptor["access"] == (
            "read" if capability_id in READ_CASES else "write"
        )
        if capability_id in SEND_CAPABILITY_IDS:
            assert descriptor["status"]["value"] == "degraded"
            assert descriptor["status"]["reason_code"] == "odoo_queue_delivery_only"
        assert cli._CAPABILITY_MODELS[capability_id] == MODELS[capability_id]
        if capability_id in READ_CASES:
            assert handler_key in cli._HANDLERS
            assert handler_key in cli._REQUEST_VALIDATORS


@pytest.mark.parametrize("capability_id", (*READ_CASES, *WRITE_CASES))
def test_configured_factory_uses_accounting_delivery_port(
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

    def client_factory(selected: object, **kwargs: str) -> object:
        assert selected is target
        assert kwargs == {"language": "en_US", "timezone": "Asia/Shanghai"}
        return client

    monkeypatch.setattr(cli, "load_runtime_config", lambda _path: RuntimeConfig())
    monkeypatch.setattr(cli, "OdooBridgeClient", client_factory)
    parameters = (
        READ_CASES[capability_id]
        if capability_id in READ_CASES
        else WRITE_CASES[capability_id]
    )

    port = cli._configured_port_factory(capability_id, _request(parameters))

    assert type(port) is OdooAccountingDeliveryPort
    assert port._client is client
