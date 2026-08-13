from __future__ import annotations

import io
import json

import pytest

from odoo_accounting_cli_v4.bridge.runtime import _dispatch
from odoo_accounting_cli_v4.capabilities.financial_reports import (
    FinancialReportError,
    read_profit_and_loss,
    validate_profit_and_loss_request,
)
from odoo_accounting_cli_v4.cli import main
from odoo_accounting_cli_v4.registry import load_registry

from test_trial_balance_runtime import FakeEnv


def _request() -> dict:
    return {
        "schema_version": "v1",
        "request_id": "85037869-a4a7-4e5c-ac88-539d2508d292",
        "context": {"database": "v4-dev", "company_id": 7, "user_login": "v4-agent", "language": "en_US", "timezone": "Asia/Shanghai"},
        "parameters": {"date_from": "2025-01-01", "date_to": "2025-01-31", "limit": 100, "cursor": None},
    }


class Port:
    user_id = 42

    def read_page(self, **kwargs):
        return {
            "user_id": 42, "company_visible": True, "module_installed": True,
            "access_allowed": True, "cursor_found": True,
            "report": {"key": "profit_and_loss", "name": "Profit and Loss"},
            "date": {"from": "2025-01-01", "to": "2025-01-31"},
            "currency": {"id": 6, "code": "CNY", "decimal_places": 2},
            "basis": "posted_entries",
            "columns": [{"index": 0, "label": "Balance", "expression_label": "balance"}],
            "lines": [
                {
                    "id": "net",
                    "parent_id": None,
                    "name": "Net Profit",
                    "level": 0,
                    "unfoldable": False,
                    "values": ["-123.45"],
                }
            ],
        }


def test_profit_and_loss_contract_and_cli() -> None:
    data = read_profit_and_loss(Port(), _request())
    assert data["report"]["key"] == "profit_and_loss"
    assert data["lines"][0]["values"] == ["-123.45"]
    stdout, stderr = io.StringIO(), io.StringIO()
    result = main(
        ["read", "report.profit_and_loss", "--request", "-"],
        stdin=io.StringIO(json.dumps(_request())), stdout=stdout, stderr=stderr,
        port_factory=lambda selected, request: Port(),
    )
    document = json.loads(stdout.getvalue())
    assert result == 0 and stderr.getvalue() == ""
    assert document["odoo"]["model"] == "account.report"
    assert document["odoo"]["record_ids"] == []
    load_registry().validate_instance("schemas/v1/report.profit_and_loss.response.schema.json", document)


def test_profit_and_loss_runtime_uses_only_the_fixed_report() -> None:
    env = FakeEnv(lines=[{"id": "net", "parent_id": False, "name": "Net Profit", "level": 0, "unfoldable": False, "columns": [{"expression_label": "balance", "no_format": -123.45}]}])
    env.ref = lambda xml_id, raise_if_not_found=False: env.root_report if xml_id == "account_reports.profit_and_loss" else None
    env.effective.name = "Profit and Loss"
    env.root_report.get_options = lambda previous: {
        "report_id": env.effective.id, "readonly_query": True, "all_entries": False,
        "date": {"date_from": "2025-01-01", "date_to": "2025-01-31", "mode": "range", "filter": "custom"},
        "columns": [{"name": "Balance", "expression_label": "balance", "figure_type": "monetary"}],
    }
    result = _dispatch(env, "account.report.profit_and_loss.read_page", {"company_id": 7, "date_from": "2025-01-01", "date_to": "2025-01-31", "after_line_id": None, "limit": 101}, 7)
    assert result["report"] == {"key": "profit_and_loss", "name": "Profit and Loss"}
    assert result["lines"][0]["values"] == ["-123.45"]


@pytest.mark.parametrize("changes", [{"date_to": "2025-02-30"}, {"date_from": "2025-02-01"}, {"limit": True}, {"extra": 1}])
def test_profit_and_loss_rejects_invalid_requests(changes) -> None:
    request = _request()
    request["parameters"].update(changes)
    with pytest.raises(FinancialReportError):
        validate_profit_and_loss_request(request)
