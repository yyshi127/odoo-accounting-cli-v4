from __future__ import annotations

import copy

import pytest

from odoo_accounting_cli_v4.bridge.financial_reports import OdooFinancialReportPort
from odoo_accounting_cli_v4.capabilities.financial_reports import (
    FinancialReportError,
    read_typed_financial_report,
    validate_typed_financial_report_request,
)

REPORTS = {
    "report.general_ledger": ("general_ledger", "range"),
    "report.partner_ledger": ("partner_ledger", "range"),
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
    "report.customer_statement": ("customer_statement", "range"),
    "report.followup": ("followup", "single"),
}
PARTNER_REPORTS = {"report.customer_statement", "report.followup"}

_COLUMNS = [
    {"index": 0, "label": "Date", "expression_label": "date", "figure_type": "date"},
    {"index": 1, "label": "Partner", "expression_label": "partner", "figure_type": "string"},
    {"index": 2, "label": "Balance", "expression_label": "balance", "figure_type": "monetary"},
    {"index": 3, "label": "Count", "expression_label": "count", "figure_type": "integer"},
]
_LINES = [
    {
        "id": "line:1",
        "parent_id": None,
        "name": "First",
        "level": 1,
        "unfoldable": True,
        "values": ["2025-01-10", "Alpha", "12.5", "2"],
    },
    {
        "id": "line:2",
        "parent_id": "line:1",
        "name": "Second",
        "level": 2,
        "unfoldable": False,
        "values": [None, "", "-12.5", "0"],
    },
]


def _request(
    capability_id: str,
    *,
    limit: int = 100,
    cursor: str | None = None,
    partner_id: int = 17,
) -> dict:
    mode = REPORTS[capability_id][1]
    parameters = (
        {"as_of": "2025-01-31"}
        if mode == "single"
        else {"date_from": "2025-01-01", "date_to": "2025-01-31"}
    )
    if capability_id in PARTNER_REPORTS:
        parameters["partner_id"] = partner_id
    parameters.update({"limit": limit, "cursor": cursor})
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


class FakePort:
    user_id = 42

    def __init__(self, capability_id: str, *, lines=None) -> None:
        self.capability_id = capability_id
        self.lines = copy.deepcopy(_LINES if lines is None else lines)
        self.calls: list[dict] = []

    def read_page(self, **kwargs):
        self.calls.append(kwargs)
        after = kwargs["after_line_id"]
        start = 0
        cursor_found = True
        if after is not None:
            ids = [line["id"] for line in self.lines]
            if after not in ids:
                cursor_found = False
            else:
                start = ids.index(after) + 1
        return {
            "user_id": self.user_id,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "cursor_found": cursor_found,
            "report": {"key": REPORTS[self.capability_id][0], "name": "Report"},
            "date": {"from": "2025-01-01", "to": "2025-01-31"},
            "currency": {"id": 6, "code": "CNY", "decimal_places": 2},
            "basis": "posted_entries",
            "columns": copy.deepcopy(_COLUMNS),
            "lines": copy.deepcopy(self.lines[start : start + kwargs["limit"]]),
        }


@pytest.mark.parametrize("capability_id", REPORTS)
def test_typed_reports_share_one_closed_contract(capability_id: str) -> None:
    port = FakePort(capability_id)

    result = read_typed_financial_report(capability_id, port, _request(capability_id))

    assert result["report"]["key"] == REPORTS[capability_id][0]
    assert result["columns"] == _COLUMNS
    assert result["lines"] == _LINES
    assert result["has_more"] is False
    expected_call = {
        "company_id": 7,
        "date_from": None if REPORTS[capability_id][1] == "single" else "2025-01-01",
        "date_to": "2025-01-31",
        "after_line_id": None,
        "limit": 101,
    }
    if capability_id in PARTNER_REPORTS:
        expected_call["partner_id"] = 17
    assert port.calls[0] == expected_call


def test_typed_report_cursor_is_bound_to_capability_and_dates() -> None:
    first = read_typed_financial_report(
        "report.general_ledger", FakePort("report.general_ledger"), _request("report.general_ledger", limit=1)
    )
    assert first["has_more"] is True

    continued = read_typed_financial_report(
        "report.general_ledger",
        FakePort("report.general_ledger"),
        _request("report.general_ledger", cursor=first["next_cursor"]),
    )
    assert [line["id"] for line in continued["lines"]] == ["line:2"]

    with pytest.raises(FinancialReportError) as caught:
        read_typed_financial_report(
            "report.partner_ledger",
            FakePort("report.partner_ledger"),
            _request("report.partner_ledger", cursor=first["next_cursor"]),
        )
    assert caught.value.code == "invalid_cursor"


@pytest.mark.parametrize("capability_id", PARTNER_REPORTS)
def test_partner_report_cursor_is_bound_to_partner(capability_id: str) -> None:
    first = read_typed_financial_report(
        capability_id,
        FakePort(capability_id),
        _request(capability_id, limit=1, partner_id=17),
    )

    with pytest.raises(FinancialReportError) as caught:
        read_typed_financial_report(
            capability_id,
            FakePort(capability_id),
            _request(capability_id, cursor=first["next_cursor"], partner_id=18),
        )
    assert caught.value.code == "invalid_cursor"


@pytest.mark.parametrize(
    ("column", "value"),
    [(0, "01/10/2025"), (2, "1e2"), (3, "1.5")],
)
def test_typed_report_rejects_values_that_do_not_match_the_column_type(
    column: int, value: str
) -> None:
    lines = copy.deepcopy(_LINES)
    lines[0]["values"][column] = value
    with pytest.raises(FinancialReportError) as caught:
        read_typed_financial_report(
            "report.general_ledger",
            FakePort("report.general_ledger", lines=lines),
            _request("report.general_ledger"),
        )
    assert caught.value.code == "failed_validation"


def test_typed_report_request_modes_are_closed() -> None:
    with pytest.raises(FinancialReportError):
        validate_typed_financial_report_request(
            "report.aged_receivable", _request("report.general_ledger")
        )
    with pytest.raises(FinancialReportError):
        validate_typed_financial_report_request("report.unknown", _request("report.general_ledger"))


@pytest.mark.parametrize("capability_id", PARTNER_REPORTS)
@pytest.mark.parametrize("partner_id", [None, 0, True])
def test_partner_report_requires_one_positive_partner_id(
    capability_id: str, partner_id: object
) -> None:
    request = _request(capability_id)
    if partner_id is None:
        del request["parameters"]["partner_id"]
    else:
        request["parameters"]["partner_id"] = partner_id

    with pytest.raises(FinancialReportError):
        validate_typed_financial_report_request(capability_id, request)


@pytest.mark.parametrize(("capability_id", "action"), [
    ("report.general_ledger", "account.report.general_ledger.read_page"),
    ("report.partner_ledger", "account.report.partner_ledger.read_page"),
    ("report.aged_receivable", "account.report.aged_receivable.read_page"),
    ("report.aged_payable", "account.report.aged_payable.read_page"),
    ("report.journal", "account.report.journal.read_page"),
    ("report.executive_summary", "account.report.executive_summary.read_page"),
    ("report.asset", "account.report.asset.read_page"),
    ("report.deferred_expense", "account.report.deferred_expense.read_page"),
    ("report.deferred_revenue", "account.report.deferred_revenue.read_page"),
    ("report.multicurrency_revaluation", "account.report.multicurrency_revaluation.read_page"),
    ("report.china.balance_sheet", "account.report.china_balance_sheet.read_page"),
    ("report.china.profit_and_loss", "account.report.china_profit_and_loss.read_page"),
    ("report.china.cash_flow", "account.report.china_cash_flow.read_page"),
    ("report.singapore.gst", "account.report.singapore_gst.read_page"),
    ("report.customer_statement", "account.report.customer_statement.read_page"),
    ("report.followup", "account.report.followup.read_page"),
])
def test_typed_report_bridge_uses_the_fixed_action(capability_id: str, action: str) -> None:
    class Client:
        def invoke(self, selected, payload):
            assert selected == action
            assert payload["company_id"] == 7
            return FakePort(capability_id).read_page(
                company_id=7,
                date_from=payload["date_from"],
                date_to=payload["date_to"],
                after_line_id=payload["after_line_id"],
                limit=payload["limit"],
                **(
                    {"partner_id": payload["partner_id"]}
                    if capability_id in PARTNER_REPORTS
                    else {}
                ),
            )

    port = OdooFinancialReportPort(Client(), capability_id)
    page = port.read_page(
        company_id=7,
        date_from=None if REPORTS[capability_id][1] == "single" else "2025-01-01",
        date_to="2025-01-31",
        after_line_id=None,
        limit=101,
        partner_id=17 if capability_id in PARTNER_REPORTS else None,
    )
    assert page["report"]["key"] == REPORTS[capability_id][0]
    assert port.user_id == 42
