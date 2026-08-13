from __future__ import annotations

import io
import json

import pytest

from odoo_accounting_cli_v4.bridge.runtime import _dispatch
from odoo_accounting_cli_v4.capabilities.financial_reports import (
    FinancialReportError,
    read_cash_flow,
    validate_cash_flow_request,
)
from odoo_accounting_cli_v4.cli import main
from odoo_accounting_cli_v4.registry import load_registry

from test_trial_balance_runtime import FakeEnv


def _request() -> dict:
    return {
        "schema_version": "v1",
        "request_id": "f3dbd7db-8904-4055-9970-56cd0bfdd4de",
        "context": {
            "database": "v4-dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": {
            "date_from": "2025-01-01",
            "date_to": "2025-01-31",
            "limit": 100,
            "cursor": None,
        },
    }


class Port:
    user_id = 42

    def read_page(self, **kwargs):
        return {
            "user_id": 42,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "cursor_found": True,
            "report": {"key": "cash_flow", "name": "Cash Flow Statement"},
            "date": {"from": "2025-01-01", "to": "2025-01-31"},
            "currency": {"id": 6, "code": "CNY", "decimal_places": 2},
            "basis": "posted_entries",
            "columns": [
                {"index": 0, "label": "Balance", "expression_label": "balance"}
            ],
            "lines": [
                {
                    "id": "closing",
                    "parent_id": None,
                    "name": "Cash and cash equivalents, closing balance",
                    "level": 0,
                    "unfoldable": True,
                    "values": ["-123.45"],
                }
            ],
        }


def test_cash_flow_contract_and_cli() -> None:
    data = read_cash_flow(Port(), _request())
    assert data["report"]["key"] == "cash_flow"
    assert data["lines"][0]["values"] == ["-123.45"]
    stdout, stderr = io.StringIO(), io.StringIO()
    result = main(
        ["read", "report.cash_flow", "--request", "-"],
        stdin=io.StringIO(json.dumps(_request())),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda selected, request: Port(),
    )
    document = json.loads(stdout.getvalue())
    assert result == 0 and stderr.getvalue() == ""
    assert document["odoo"]["model"] == "account.report"
    assert document["odoo"]["record_ids"] == []
    load_registry().validate_instance(
        "schemas/v1/report.cash_flow.response.schema.json", document
    )


def test_cash_flow_runtime_accepts_fixed_child_lines_without_unfoldable() -> None:
    env = FakeEnv(
        lines=[
            {
                "id": "closing",
                "parent_id": False,
                "name": "Cash and cash equivalents, closing balance",
                "level": 0,
                "unfoldable": True,
                "columns": [{"expression_label": "balance", "no_format": -123.45}],
            },
            {
                "id": "bank",
                "parent_id": "closing",
                "name": "1003 Bank",
                "level": 1,
                "columns": [{"expression_label": "balance", "no_format": -123.45}],
            },
        ]
    )
    env.ref = lambda xml_id, raise_if_not_found=False: (
        env.root_report if xml_id == "account_reports.cash_flow_report" else None
    )
    env.effective.name = "Cash Flow Statement"
    env.root_report.get_options = lambda previous: {
        "report_id": env.effective.id,
        "readonly_query": True,
        "all_entries": False,
        "date": {
            "date_from": "2025-01-01",
            "date_to": "2025-01-31",
            "mode": "range",
            "filter": "custom",
        },
        "columns": [
            {
                "name": "Balance",
                "expression_label": "balance",
                "figure_type": "monetary",
            }
        ],
    }
    result = _dispatch(
        env,
        "account.report.cash_flow.read_page",
        {
            "company_id": 7,
            "date_from": "2025-01-01",
            "date_to": "2025-01-31",
            "after_line_id": None,
            "limit": 101,
        },
        7,
    )
    assert result["report"] == {"key": "cash_flow", "name": "Cash Flow Statement"}
    assert result["lines"][1]["unfoldable"] is False


@pytest.mark.parametrize(
    "changes",
    [
        {"date_to": "2025-02-30"},
        {"date_from": "2025-02-01"},
        {"limit": True},
        {"extra": 1},
    ],
)
def test_cash_flow_rejects_invalid_requests(changes) -> None:
    request = _request()
    request["parameters"].update(changes)
    with pytest.raises(FinancialReportError):
        validate_cash_flow_request(request)
