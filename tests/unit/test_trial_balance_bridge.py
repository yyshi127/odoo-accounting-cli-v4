from __future__ import annotations

import pytest

from odoo_accounting_cli_v4.bridge.financial_reports import OdooFinancialReportPort


def _page() -> dict:
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
        "columns": [],
        "lines": [],
    }


def test_financial_report_port_calls_only_the_fixed_trial_balance_action() -> None:
    class Client:
        def invoke(self, action, payload):
            assert action == "account.report.trial_balance.read_page"
            assert payload == {
                "company_id": 7,
                "date_from": "2025-01-01",
                "date_to": "2025-01-31",
                "after_line_id": None,
                "limit": 101,
            }
            return _page()

    port = OdooFinancialReportPort(Client())
    assert port.read_page(
        company_id=7,
        date_from="2025-01-01",
        date_to="2025-01-31",
        after_line_id=None,
        limit=101,
    ) == _page()
    assert port.user_id == 42


def test_financial_report_port_rejects_a_noncanonical_bridge_envelope() -> None:
    class Client:
        def invoke(self, action, payload):
            return {**_page(), "extra": True}

    port = OdooFinancialReportPort(Client())
    with pytest.raises(ValueError):
        port.read_page(
            company_id=7,
            date_from="2025-01-01",
            date_to="2025-01-31",
            after_line_id=None,
            limit=101,
        )
    with pytest.raises(ValueError):
        _ = port.user_id
