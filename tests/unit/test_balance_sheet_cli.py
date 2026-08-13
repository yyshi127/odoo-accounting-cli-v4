from __future__ import annotations

import io
import json

from odoo_accounting_cli_v4.cli import main
from odoo_accounting_cli_v4.registry import load_registry


def test_cli_dispatches_the_fixed_balance_sheet_report() -> None:
    request = {
        "schema_version": "v1",
        "request_id": "9ad18ce2-722d-4cf9-a3a3-f33999467bbc",
        "context": {
            "database": "v4-dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": {"as_of": "2025-01-31", "limit": 100, "cursor": None},
    }

    class Port:
        user_id = 42

        def read_page(self, **kwargs):
            assert kwargs == {
                "company_id": 7,
                "date_from": None,
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
                "report": {"key": "balance_sheet", "name": "Balance Sheet"},
                "date": {"from": "2025-01-01", "to": "2025-01-31"},
                "currency": {"id": 6, "code": "CNY", "decimal_places": 2},
                "basis": "posted_entries",
                "columns": [
                    {"index": 0, "label": "Balance", "expression_label": "balance"}
                ],
                "lines": [
                    {
                        "id": "assets",
                        "parent_id": None,
                        "name": "ASSETS",
                        "level": 0,
                        "unfoldable": False,
                        "values": ["-123.45"],
                    }
                ],
            }

    stdout = io.StringIO()
    stderr = io.StringIO()
    result = main(
        ["read", "report.balance_sheet", "--request", "-"],
        stdin=io.StringIO(json.dumps(request)),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda selected, raw: Port(),
    )
    document = json.loads(stdout.getvalue())
    assert result == 0
    assert stderr.getvalue() == ""
    assert document["success"] is True
    assert document["odoo"] == {
        "database": "v4-dev",
        "company_id": 7,
        "user_id": 42,
        "model": "account.report",
        "record_ids": [],
    }
    load_registry().validate_instance(
        "schemas/v1/report.balance_sheet.response.schema.json", document
    )
