from __future__ import annotations

import base64
import hashlib
import io
import json

import pytest

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4.bridge.document_exports import OdooDocumentExportPort
from odoo_accounting_cli_v4.capabilities.document_exports import (
    DOCUMENT_EXPORT_SPECS,
    export_document,
    validate_document_export_request,
)


def _request(capability_id: str) -> dict:
    spec = DOCUMENT_EXPORT_SPECS[capability_id]
    parameters = {spec["id_parameter"]: 37}
    if capability_id == "invoice.pdf.export":
        parameters["layout"] = "with_payments"
    return {
        "schema_version": "v1",
        "request_id": "e2d0448d-f1cc-4914-a811-0d66293304f8",
        "context": {
            "database": "v4-dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": parameters,
    }


def test_cli_dispatches_a_document_export_and_binds_the_source_record() -> None:
    capability_id = "invoice.pdf.export"
    content = b"%PDF-1.7\ninvoice"

    class Port:
        user_id = 42

        def export(self, **kwargs):
            assert kwargs == {
                "capability_id": capability_id,
                "company_id": 7,
                "target_id": 37,
                "layout": "with_payments",
            }
            return {
                "user_id": 42,
                "company_visible": True,
                "module_installed": True,
                "access_allowed": True,
                "record_visible": True,
                "applicable": True,
                "filename": "invoice.pdf",
                "format": "pdf",
                "mimetype": "application/pdf",
                "byte_count": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
                "content_base64": base64.b64encode(content).decode("ascii"),
            }

    stdout = io.StringIO()
    stderr = io.StringIO()
    result = cli.main(
        ["read", capability_id, "--request", "-"],
        stdin=io.StringIO(json.dumps(_request(capability_id))),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda selected, request: Port(),
    )

    document = json.loads(stdout.getvalue())
    assert result == 0
    assert stderr.getvalue() == ""
    assert document["success"] is True
    assert document["capability"] == capability_id
    assert document["data"]["format"] == "pdf"
    assert document["odoo"] == {
        "database": "v4-dev",
        "company_id": 7,
        "user_id": 42,
        "model": "account.move",
        "record_ids": [37],
    }


def test_all_document_export_handlers_are_wired_to_the_exact_capability() -> None:
    for capability_id in DOCUMENT_EXPORT_SPECS:
        handler_key = f"document_{capability_id.replace('.', '_')}"
        handler = cli._HANDLERS[handler_key]
        validator = cli._REQUEST_VALIDATORS[handler_key]
        assert handler.func is export_document
        assert handler.args == (capability_id,)
        assert validator.func is validate_document_export_request
        assert validator.args == (capability_id,)


def test_configured_factory_selects_the_document_export_port(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Config:
        def resolve(self, database, company_id, user_login):
            assert (database, company_id, user_login) == ("v4-dev", 7, "v4-agent")
            return object()

    monkeypatch.setattr(cli, "load_runtime_config", lambda path: Config())
    monkeypatch.setattr(
        cli,
        "OdooBridgeClient",
        lambda target, *, language, timezone: object(),
    )

    capability_id = "payment.receipt.pdf.export"
    port = cli._configured_port_factory(capability_id, _request(capability_id))

    assert type(port) is OdooDocumentExportPort
