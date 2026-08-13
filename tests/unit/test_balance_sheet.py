from __future__ import annotations

import copy

import pytest

from odoo_accounting_cli_v4.capabilities.financial_reports import (
    FinancialReportError,
    read_balance_sheet,
    validate_balance_sheet_request,
)


def _request(*, limit: int = 100, cursor: str | None = None) -> dict:
    return {
        "schema_version": "v1",
        "request_id": "9ad18ce2-722d-4cf9-a3a3-f33999467bbc",
        "context": {
            "database": "v4-dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": {"as_of": "2025-01-31", "limit": limit, "cursor": cursor},
    }


_COLUMNS = [{"index": 0, "label": "Balance", "expression_label": "balance"}]
_LINES = [
    {
        "id": "assets",
        "parent_id": None,
        "name": "ASSETS",
        "level": 0,
        "unfoldable": False,
        "values": ["-123.45"],
    },
    {
        "id": "liabilities",
        "parent_id": None,
        "name": "LIABILITIES",
        "level": 0,
        "unfoldable": False,
        "values": ["0"],
    },
    {
        "id": "equity",
        "parent_id": None,
        "name": "EQUITY",
        "level": 0,
        "unfoldable": False,
        "values": ["-123.45"],
    },
]


class FakePort:
    user_id = 42

    def __init__(self, lines=None, **overrides) -> None:
        self.lines = copy.deepcopy(_LINES if lines is None else lines)
        self.overrides = overrides
        self.calls = []

    def read_page(self, **kwargs):
        self.calls.append(kwargs)
        after = kwargs["after_line_id"]
        ids = [line["id"] for line in self.lines]
        cursor_found = after is None or after in ids
        start = ids.index(after) + 1 if after in ids else 0
        page = {
            "user_id": self.user_id,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "cursor_found": cursor_found,
            "report": {"key": "balance_sheet", "name": "Balance Sheet"},
            "date": {"from": "2025-01-01", "to": "2025-01-31"},
            "currency": {"id": 6, "code": "CNY", "decimal_places": 2},
            "basis": "posted_entries",
            "columns": copy.deepcopy(_COLUMNS),
            "lines": copy.deepcopy(self.lines[start : start + kwargs["limit"]]),
        }
        page.update(self.overrides)
        return page


def test_balance_sheet_uses_one_fixed_report_and_returns_verified_data() -> None:
    port = FakePort()
    result = read_balance_sheet(port, _request())
    assert result == {
        "report": {"key": "balance_sheet", "name": "Balance Sheet"},
        "date": {"from": "2025-01-01", "to": "2025-01-31"},
        "currency": {"id": 6, "code": "CNY", "decimal_places": 2},
        "basis": "posted_entries",
        "columns": _COLUMNS,
        "lines": _LINES,
        "has_more": False,
        "next_cursor": None,
    }
    assert port.calls == [
        {
            "company_id": 7,
            "date_from": None,
            "date_to": "2025-01-31",
            "after_line_id": None,
            "limit": 101,
        }
    ]


def test_balance_sheet_cursor_is_bound_to_as_of_and_scope() -> None:
    first = read_balance_sheet(FakePort(), _request(limit=1))
    second_port = FakePort()
    second = read_balance_sheet(
        second_port, _request(limit=10, cursor=first["next_cursor"])
    )
    assert [line["id"] for line in second["lines"]] == ["liabilities", "equity"]
    assert second_port.calls[0]["after_line_id"] == "assets"

    changed = _request(cursor=first["next_cursor"])
    changed["parameters"]["as_of"] = "2025-02-28"
    with pytest.raises(FinancialReportError) as caught:
        read_balance_sheet(FakePort(), changed)
    assert caught.value.code == "invalid_cursor"


@pytest.mark.parametrize(
    "change",
    [
        lambda request: request["parameters"].update(as_of="2025-02-30"),
        lambda request: request["parameters"].update(limit=True),
        lambda request: request["parameters"].update(extra=True),
    ],
)
def test_balance_sheet_request_is_closed(change) -> None:
    request = _request()
    change(request)
    with pytest.raises(FinancialReportError) as caught:
        validate_balance_sheet_request(request)
    assert caught.value.exit_code == 2
