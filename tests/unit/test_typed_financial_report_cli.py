from __future__ import annotations

import io
import json

import pytest

from odoo_accounting_cli_v4.cli import main
from odoo_accounting_cli_v4.registry import load_registry

REPORTS = {
    "report.general_ledger": ("general_ledger", "range"),
    "report.partner_ledger": ("partner_ledger", "range"),
    "report.customer_statement": ("customer_statement", "range"),
    "report.followup": ("followup", "single"),
    "report.aged_receivable": ("aged_receivable", "single"),
    "report.aged_payable": ("aged_payable", "single"),
    "report.journal": ("journal", "range"),
    "report.executive_summary": ("executive_summary", "range"),
    "report.asset": ("asset", "range"),
    "report.deferred_expense": ("deferred_expense", "range"),
    "report.deferred_revenue": ("deferred_revenue", "range"),
    "report.multicurrency_revaluation": ("multicurrency_revaluation", "single"),
    "report.china.balance_sheet": ("china_balance_sheet", "single"),
    "report.china.profit_and_loss": ("china_profit_and_loss", "range"),
    "report.china.cash_flow": ("china_cash_flow", "range"),
    "report.singapore.gst": ("singapore_gst", "range"),
}


def _request(capability_id: str) -> dict:
    parameters = (
        {"as_of": "2025-01-31"}
        if REPORTS[capability_id][1] == "single"
        else {"date_from": "2025-01-01", "date_to": "2025-01-31"}
    )
    if capability_id in {"report.customer_statement", "report.followup"}:
        parameters["partner_id"] = 16
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


@pytest.mark.parametrize("capability_id", REPORTS)
def test_cli_dispatches_each_typed_report(capability_id: str) -> None:
    class Port:
        user_id = 42

        def read_page(self, **kwargs):
            assert kwargs["company_id"] == 7
            return {
                "user_id": 42,
                "company_visible": True,
                "module_installed": True,
                "access_allowed": True,
                "cursor_found": True,
                "report": {"key": REPORTS[capability_id][0], "name": "Report"},
                "date": {"from": "2025-01-01", "to": "2025-01-31"},
                "currency": {"id": 6, "code": "CNY", "decimal_places": 2},
                "basis": "posted_entries",
                "columns": [
                    {"index": 0, "label": "Date", "expression_label": "date", "figure_type": "date"},
                    {"index": 1, "label": "Balance", "expression_label": "balance", "figure_type": "monetary"},
                ],
                "lines": [
                    {
                        "id": "line:1",
                        "parent_id": None,
                        "name": "Line",
                        "level": 1,
                        "unfoldable": False,
                        "values": ["2025-01-10", "12.5"],
                    }
                ],
            }

    stdout = io.StringIO()
    stderr = io.StringIO()
    result = main(
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
    assert document["data"]["report"]["key"] == REPORTS[capability_id][0]
    assert document["odoo"] == {
        "database": "v4-dev",
        "company_id": 7,
        "user_id": 42,
        "model": "account.report",
        "record_ids": [],
    }
    load_registry().validate_instance(
        f"schemas/v1/{capability_id}.response.schema.json", document
    )
