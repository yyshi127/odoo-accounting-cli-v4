from __future__ import annotations

from odoo_accounting_cli_v4.bridge.runtime import _dispatch

from test_trial_balance_runtime import FakeEnv


def test_balance_sheet_uses_the_fixed_single_date_report_mode() -> None:
    env = FakeEnv(
        lines=[
            {
                "id": "assets",
                "parent_id": False,
                "name": "ASSETS",
                "level": 0,
                "unfoldable": False,
                "columns": [{"expression_label": "balance", "no_format": -123.45}],
            },
            {
                "id": "liabilities-equity",
                "parent_id": False,
                "name": "LIABILITIES + EQUITY",
                "level": 0,
                "unfoldable": False,
                "columns": [{"expression_label": "balance", "no_format": -123.45}],
            },
        ]
    )
    env.root_report.get_options = lambda previous: {
        "report_id": env.effective.id,
        "readonly_query": True,
        "all_entries": False,
        "date": {
            "date_from": "2025-01-01",
            "date_to": "2025-01-31",
            "mode": "single",
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
    env.root_report.name = "Balance Sheet"
    env.effective.name = "Balance Sheet"
    env.ref = lambda xml_id, raise_if_not_found=False: (
        env.root_report if xml_id == "account_reports.balance_sheet" else None
    )

    result = _dispatch(
        env,
        "account.report.balance_sheet.read_page",
        {
            "company_id": 7,
            "date_from": None,
            "date_to": "2025-01-31",
            "after_line_id": None,
            "limit": 101,
        },
        7,
    )

    assert result["report"] == {"key": "balance_sheet", "name": "Balance Sheet"}
    assert result["date"] == {"from": "2025-01-01", "to": "2025-01-31"}
    assert result["columns"] == [
        {"index": 0, "label": "Balance", "expression_label": "balance"}
    ]
    assert [line["values"] for line in result["lines"]] == [
        ["-123.45"],
        ["-123.45"],
    ]
