from __future__ import annotations

import base64
import hashlib
import io
import json

import pytest

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4.bridge.financial_reports import (
    OdooFinancialReportExportPort,
)
from odoo_accounting_cli_v4.capabilities.financial_reports import (
    FINANCIAL_REPORT_EXPORTS,
    export_financial_report,
    validate_financial_report_export_request,
)


def _request(capability_id: str) -> dict:
    parameters = (
        {"as_of": "2025-01-31", "format": "pdf"}
        if FINANCIAL_REPORT_EXPORTS[capability_id]["mode"] == "single"
        else {
            "date_from": "2025-01-01",
            "date_to": "2025-01-31",
            "format": "pdf",
        }
    )
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
        "parameters": parameters,
    }


def test_cli_dispatches_a_financial_report_export() -> None:
    capability_id = "report.trial_balance.export"
    content = b"%PDF-1.7\nreport"

    class Port:
        user_id = 42

        def export(self, **kwargs):
            assert kwargs["capability_id"] == capability_id
            assert kwargs["company_id"] == 7
            return {
                "user_id": 42,
                "company_visible": True,
                "module_installed": True,
                "access_allowed": True,
                "filename": "accounting-report.pdf",
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
        "model": "account.report",
        "record_ids": [],
    }


def test_all_export_handler_keys_are_wired_to_their_exact_capability() -> None:
    for capability_id in FINANCIAL_REPORT_EXPORTS:
        handler_key = f"report_{capability_id.removeprefix('report.').replace('.', '_')}"
        handler = cli._HANDLERS[handler_key]
        validator = cli._REQUEST_VALIDATORS[handler_key]
        assert handler.func is export_financial_report
        assert handler.args == (capability_id,)
        assert validator.func is validate_financial_report_export_request
        assert validator.args == (capability_id,)


def test_configured_factory_selects_the_dedicated_export_port(
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

    port = cli._configured_port_factory(
        "report.trial_balance.export", _request("report.trial_balance.export")
    )

    assert type(port) is OdooFinancialReportExportPort
