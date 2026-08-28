from __future__ import annotations

import io
import json

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4.bridge.budget_report import OdooBudgetReportPort
from odoo_accounting_cli_v4.capabilities.budget_report import (
    read_budget_report,
    validate_budget_report_request,
)
from odoo_accounting_cli_v4.registry import load_registry


def _request() -> dict:
    return {
        "schema_version": "v1",
        "request_id": "7bc39413-0d69-4092-9319-795d33f3167c",
        "context": {
            "database": "v4-dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "zh_CN",
            "timezone": "Asia/Shanghai",
        },
        "parameters": {
            "budget_id": 71,
            "budget_line_id": 901,
            "date_from": "2026-01-01",
            "date_to": "2026-12-31",
            "plan_id": 21,
            "analytic_account_id": 31,
            "line_type": "achieved",
            "limit": 1,
            "cursor": None,
        },
    }


def _item() -> dict:
    return {
        "row_key": "aal501",
        "line_type": "achieved",
        "date": "2026-08-24",
        "budget": {"id": 71, "name": "FY2026"},
        "budget_line": {"id": 901},
        "source": {"model": "account.analytic.line", "id": 501},
        "description": "Project effort",
        "plan_accounts": [
            {
                "plan": {"id": 21, "name": "Projects"},
                "account": {"id": 31, "name": "Project Alpha"},
            }
        ],
        "company_id": 7,
        "user": {"id": 5, "name": "V4 Accountant"},
        "budget_amount": "0",
        "achieved_amount": "125.5",
        "theoretical_amount": "0",
    }


class Port:
    user_id = 42

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def read(self, *, company_id: int, parameters: dict) -> dict:
        self.calls.append({"company_id": company_id, "parameters": parameters})
        return {
            "user_id": self.user_id,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "cursor_found": True,
            "items": [_item()],
        }


def test_registry_routes_report_to_the_dedicated_contract() -> None:
    descriptor = load_registry().describe("report.budget")

    assert descriptor["handler_key"] == "budget_report"
    assert cli._HANDLERS["budget_report"] is read_budget_report
    assert cli._REQUEST_VALIDATORS["budget_report"] is validate_budget_report_request
    assert cli._CAPABILITY_MODELS["report.budget"] == "budget.report"


def test_configured_factory_uses_the_dedicated_budget_report_port(monkeypatch) -> None:
    target = object()
    client = object()

    class RuntimeConfig:
        def resolve(self, database: str, company_id: int, user_login: str) -> object:
            assert (database, company_id, user_login) == ("v4-dev", 7, "v4-agent")
            return target

    def bridge_factory(selected: object, **kwargs: str) -> object:
        assert selected is target
        assert kwargs == {"language": "zh_CN", "timezone": "Asia/Shanghai"}
        return client

    monkeypatch.setattr(cli, "load_runtime_config", lambda _path: RuntimeConfig())
    monkeypatch.setattr(cli, "OdooBridgeClient", bridge_factory)

    port = cli._configured_port_factory("report.budget", _request())
    assert type(port) is OdooBudgetReportPort
    assert port._client is client


def test_cli_emits_schema_valid_report_and_empty_report_record_ids() -> None:
    port = Port()
    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = cli.main(
        ["read", "report.budget", "--request", "-"],
        stdin=io.StringIO(json.dumps(_request())),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda selected, request: port,
    )

    document = json.loads(stdout.getvalue())
    assert exit_code == 0
    assert stderr.getvalue() == ""
    assert document["success"] is True
    assert document["data"] == {
        "items": [_item()],
        "has_more": False,
        "next_cursor": None,
    }
    assert port.calls == [
        {
            "company_id": 7,
            "parameters": {
                "budget_id": 71,
                "budget_line_id": 901,
                "date_from": "2026-01-01",
                "date_to": "2026-12-31",
                "plan_id": 21,
                "analytic_account_id": 31,
                "line_type": "achieved",
                "after": None,
                "limit": 2,
            },
        }
    ]
    assert document["odoo"] == {
        "database": "v4-dev",
        "company_id": 7,
        "user_id": 42,
        "model": "budget.report",
        "record_ids": [],
    }
    load_registry().validate_instance(
        "schemas/v1/report.budget.response.schema.json", document
    )


def test_invalid_pair_is_rejected_before_port_creation() -> None:
    request = _request()
    request["parameters"]["analytic_account_id"] = None
    called = False

    def factory(_selected: str, _request: dict) -> object:
        nonlocal called
        called = True
        return Port()

    stdout = io.StringIO()
    exit_code = cli.main(
        ["read", "report.budget", "--request", "-"],
        stdin=io.StringIO(json.dumps(request)),
        stdout=stdout,
        stderr=io.StringIO(),
        port_factory=factory,
    )

    assert exit_code == 2
    assert called is False
    assert json.loads(stdout.getvalue())["error"]["code"] == "invalid_request"
