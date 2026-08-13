from __future__ import annotations

import io
import json

import pytest

from odoo_accounting_cli_v4.bridge.runtime import _dispatch
from odoo_accounting_cli_v4.capabilities.financial_reports import (
    FinancialReportError,
    read_tax_report,
    validate_tax_report_request,
)
from odoo_accounting_cli_v4.cli import main
from odoo_accounting_cli_v4.registry import load_registry

from test_trial_balance_runtime import FakeEnv


def _request() -> dict:
    return {
        "schema_version": "v1",
        "request_id": "08bbc76b-2314-49b8-a818-5cf354909a7f",
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
            "report": {"key": "tax", "name": "Generic Tax report"},
            "date": {"from": "2025-01-01", "to": "2025-01-31"},
            "currency": {"id": 6, "code": "CNY", "decimal_places": 2},
            "basis": "posted_entries",
            "columns": [
                {"index": 0, "label": "Net", "expression_label": "net"},
                {"index": 1, "label": "Tax", "expression_label": "tax"},
            ],
            "lines": [],
        }


def test_tax_report_contract_and_cli() -> None:
    data = read_tax_report(Port(), _request())
    assert data["report"]["key"] == "tax"
    assert data["lines"] == []
    stdout, stderr = io.StringIO(), io.StringIO()
    result = main(
        ["read", "report.tax", "--request", "-"],
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
        "schemas/v1/report.tax.response.schema.json", document
    )


def test_tax_report_runtime_uses_the_fixed_generic_tax_report() -> None:
    env = FakeEnv(lines=[])
    env.ref = lambda xml_id, raise_if_not_found=False: (
        env.root_report if xml_id == "account.generic_tax_report" else None
    )
    env.effective.name = "Generic Tax report"
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
            {"name": "Net", "expression_label": "net", "figure_type": "monetary"},
            {"name": "Tax", "expression_label": "tax", "figure_type": "monetary"},
        ],
    }
    result = _dispatch(
        env,
        "account.report.tax.read_page",
        {
            "company_id": 7,
            "date_from": "2025-01-01",
            "date_to": "2025-01-31",
            "after_line_id": None,
            "limit": 101,
        },
        7,
    )
    assert result["report"] == {"key": "tax", "name": "Generic Tax report"}
    assert result["columns"] == [
        {"index": 0, "label": "Net", "expression_label": "net"},
        {"index": 1, "label": "Tax", "expression_label": "tax"},
    ]


@pytest.mark.parametrize(
    "changes",
    [
        {"date_to": "2025-02-30"},
        {"date_from": "2025-02-01"},
        {"limit": True},
        {"extra": 1},
    ],
)
def test_tax_report_rejects_invalid_requests(changes) -> None:
    request = _request()
    request["parameters"].update(changes)
    with pytest.raises(FinancialReportError):
        validate_tax_report_request(request)
