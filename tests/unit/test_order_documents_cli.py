from __future__ import annotations

import io
import json
from functools import partial
from typing import Any

import pytest

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4.bridge.order_documents import OdooOrderDocumentsPort
from odoo_accounting_cli_v4.capabilities.order_documents import (
    validate_order_document_request,
)

CAPABILITIES = {
    "sale.order.search": ("sale_order_search", "sale.order", [10]),
    "sale.order.get": ("sale_order_get", "sale.order", [10]),
    "sale.order.line.search": ("sale_order_line_search", "sale.order.line", [11]),
    "sale.order.analysis.summary": (
        "sale_order_analysis_summary",
        "sale.order",
        [],
    ),
    "purchase.order.search": ("purchase_order_search", "purchase.order", [20]),
    "purchase.order.get": ("purchase_order_get", "purchase.order", [20]),
    "purchase.order.line.search": (
        "purchase_order_line_search",
        "purchase.order.line",
        [21],
    ),
    "purchase.order.analysis.summary": (
        "purchase_order_analysis_summary",
        "purchase.order",
        [],
    ),
}


def _parameters(capability_id: str) -> dict[str, Any]:
    if capability_id.endswith(".get"):
        return {"order_id": 10 if capability_id.startswith("sale.") else 20}
    if capability_id.endswith(".analysis.summary"):
        return {
            "date_from": "2026-01-01",
            "date_to": "2026-12-31",
            "group_by": "state",
        }
    return {"limit": 1}


def _request(capability_id: str) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "request_id": "b27a0018-2089-4785-a4f7-3701aa6b3526",
        "context": {
            "database": "v4-dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": _parameters(capability_id),
    }


def _data(capability_id: str) -> dict[str, Any]:
    if capability_id.endswith(".analysis.summary"):
        return {"company_id": 7}
    record_id = CAPABILITIES[capability_id][2][0]
    if capability_id.endswith(".get"):
        return {"id": record_id}
    return {
        "items": [{"id": record_id}],
        "has_more": False,
        "next_cursor": None,
    }


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_order_document_cli_uses_fixed_handler_validator_and_model(
    capability_id: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    handler_key, model, _record_ids = CAPABILITIES[capability_id]
    port = object()
    request = _request(capability_id)
    marker = object()
    calls: list[tuple[object, str, dict[str, Any]]] = []

    def read_order_document(
        selected_port: object,
        selected_capability: str,
        selected_request: dict[str, Any],
    ) -> object:
        calls.append((selected_port, selected_capability, selected_request))
        return marker

    monkeypatch.setattr(cli, "read_order_document", read_order_document)

    assert cli._HANDLERS[handler_key](port, request) is marker
    assert calls == [(port, capability_id, request)]
    validator = cli._REQUEST_VALIDATORS[handler_key]
    assert isinstance(validator, partial)
    assert validator.func is validate_order_document_request
    assert validator.args == (capability_id,)
    assert cli._CAPABILITY_MODELS[capability_id] == model


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_configured_factory_uses_order_document_port(
    capability_id: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = object()
    client = object()

    class RuntimeConfig:
        def resolve(self, database: str, company_id: int, user_login: str) -> object:
            assert (database, company_id, user_login) == ("v4-dev", 7, "v4-agent")
            return target

    def bridge_factory(selected_target: object, **kwargs: str) -> object:
        assert selected_target is target
        assert kwargs == {"language": "en_US", "timezone": "Asia/Shanghai"}
        return client

    monkeypatch.setattr(cli, "load_runtime_config", lambda _path: RuntimeConfig())
    monkeypatch.setattr(cli, "OdooBridgeClient", bridge_factory)

    port = cli._configured_port_factory(capability_id, _request(capability_id))

    assert type(port) is OdooOrderDocumentsPort
    assert port._client is client


class _Registry:
    def __init__(self, capability_id: str) -> None:
        self.capability_id = capability_id

    def describe(self, capability_id: str) -> dict[str, Any]:
        assert capability_id == self.capability_id
        return {
            "access": "read",
            "handler_key": CAPABILITIES[capability_id][0],
            "schemas": {"request": "request", "response": "response"},
            "status": {"value": "available", "reason_code": None},
        }

    def validate_instance(self, _schema: str, _instance: object) -> None:
        return None


class _Port:
    user_id = 42


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_order_document_cli_emits_exact_model_and_record_ids(
    capability_id: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    handler_key, model, record_ids = CAPABILITIES[capability_id]
    request = _request(capability_id)
    monkeypatch.setattr(cli, "load_registry", lambda: _Registry(capability_id))
    monkeypatch.setitem(
        cli._HANDLERS, handler_key, lambda _port, _request: _data(capability_id)
    )

    stdout = io.StringIO()
    stderr = io.StringIO()
    exit_code = cli.main(
        ["read", capability_id, "--request", "-"],
        stdin=io.StringIO(json.dumps(request)),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda selected, supplied: _Port(),
    )

    document = json.loads(stdout.getvalue())
    assert exit_code == 0
    assert stderr.getvalue() == ""
    assert document["odoo"] == {
        "database": "v4-dev",
        "company_id": 7,
        "user_id": 42,
        "model": model,
        "record_ids": record_ids,
    }
