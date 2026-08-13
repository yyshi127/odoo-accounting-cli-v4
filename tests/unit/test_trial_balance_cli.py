from __future__ import annotations

import io
import json

from odoo_accounting_cli_v4.cli import main
from odoo_accounting_cli_v4.registry import load_registry


def _request() -> dict:
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
        "parameters": {
            "date_from": "2025-01-01",
            "date_to": "2025-01-31",
            "limit": 100,
            "cursor": None,
        },
    }


def test_cli_dispatches_the_fixed_trial_balance_report() -> None:
    class Port:
        user_id = 42

        def read_page(self, **kwargs):
            assert kwargs == {
                "company_id": 7,
                "date_from": "2025-01-01",
                "date_to": "2025-01-31",
                "after_line_id": None,
                "limit": 101,
            }
            return {
                "user_id": 42,
                "company_visible": True,
                "module_installed": True,
                "access_allowed": True,
                "cursor_found": True,
                "report": {"key": "trial_balance", "name": "Trial Balance"},
                "date": {"from": "2025-01-01", "to": "2025-01-31"},
                "currency": {"id": 6, "code": "CNY", "decimal_places": 2},
                "basis": "posted_entries",
                "columns": [
                    {"index": 0, "label": "Balance", "expression_label": "balance"},
                    {"index": 1, "label": "Debit", "expression_label": "debit"},
                    {"index": 2, "label": "Credit", "expression_label": "credit"},
                    {"index": 3, "label": "Balance", "expression_label": "balance"},
                ],
                "lines": [
                    {
                        "id": "total",
                        "parent_id": None,
                        "name": "Total",
                        "level": 1,
                        "unfoldable": False,
                        "values": ["0", "123.45", "123.45", "0"],
                    }
                ],
            }

    stdout = io.StringIO()
    stderr = io.StringIO()
    result = main(
        ["read", "report.trial_balance", "--request", "-"],
        stdin=io.StringIO(json.dumps(_request())),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda selected, request: Port(),
    )

    document = json.loads(stdout.getvalue())
    assert result == 0
    assert stderr.getvalue() == ""
    assert document["success"] is True
    assert document["data"]["lines"][0]["values"] == ["0", "123.45", "123.45", "0"]
    assert document["odoo"] == {
        "database": "v4-dev",
        "company_id": 7,
        "user_id": 42,
        "model": "account.report",
        "record_ids": [],
    }
    load_registry().validate_instance(
        "schemas/v1/report.trial_balance.response.schema.json", document
    )
