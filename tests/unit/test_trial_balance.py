from __future__ import annotations

import copy

import pytest

from odoo_accounting_cli_v4.capabilities.financial_reports import (
    FinancialReportError,
    read_trial_balance,
    validate_trial_balance_request,
)


def _request(*, limit: int = 100, cursor: str | None = None) -> dict:
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
            "limit": limit,
            "cursor": cursor,
        },
    }


_COLUMNS = [
    {"index": 0, "label": "Balance", "expression_label": "balance"},
    {"index": 1, "label": "Debit", "expression_label": "debit"},
    {"index": 2, "label": "Credit", "expression_label": "credit"},
    {"index": 3, "label": "Balance", "expression_label": "balance"},
]
_LINES = [
    {
        "id": "account:bank",
        "parent_id": "trial-balance",
        "name": "1003 Bank",
        "level": 2,
        "unfoldable": False,
        "values": ["0", "0", "123.45", "-123.45"],
    },
    {
        "id": "account:expense",
        "parent_id": "trial-balance",
        "name": "530101 R&D expense",
        "level": 2,
        "unfoldable": False,
        "values": ["0", "123.45", "0", "123.45"],
    },
    {
        "id": "total",
        "parent_id": None,
        "name": "Total",
        "level": 1,
        "unfoldable": False,
        "values": ["0", "123.45", "123.45", "0"],
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
        start = 0
        if after is not None:
            ids = [line["id"] for line in self.lines]
            if after not in ids:
                cursor_found = False
            else:
                cursor_found = True
                start = ids.index(after) + 1
        else:
            cursor_found = True
        page = {
            "user_id": self.user_id,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "cursor_found": cursor_found,
            "report": {"key": "trial_balance", "name": "Trial Balance"},
            "date": {"from": "2025-01-01", "to": "2025-01-31"},
            "currency": {"id": 6, "code": "CNY", "decimal_places": 2},
            "basis": "posted_entries",
            "columns": copy.deepcopy(_COLUMNS),
            "lines": copy.deepcopy(self.lines[start : start + kwargs["limit"]]),
        }
        page.update(self.overrides)
        return page


def test_trial_balance_uses_one_fixed_report_read_and_returns_verified_page() -> None:
    port = FakePort()

    result = read_trial_balance(port, _request())

    assert result == {
        "report": {"key": "trial_balance", "name": "Trial Balance"},
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
            "date_from": "2025-01-01",
            "date_to": "2025-01-31",
            "after_line_id": None,
            "limit": 101,
        }
    ]


def test_trial_balance_cursor_is_bound_and_continues_after_exact_line() -> None:
    first = read_trial_balance(FakePort(), _request(limit=1))
    assert first["has_more"] is True
    assert isinstance(first["next_cursor"], str)

    port = FakePort()
    second = read_trial_balance(port, _request(limit=10, cursor=first["next_cursor"]))

    assert [line["id"] for line in second["lines"]] == [
        "account:expense",
        "total",
    ]
    assert port.calls[0]["after_line_id"] == "account:bank"

    changed = _request(limit=10, cursor=first["next_cursor"])
    changed["parameters"]["date_to"] = "2025-02-28"
    with pytest.raises(FinancialReportError) as caught:
        read_trial_balance(FakePort(), changed)
    assert caught.value.code == "invalid_cursor"


@pytest.mark.parametrize(
    "change",
    [
        lambda request: request["parameters"].update(date_from="2025-02-01"),
        lambda request: request["parameters"].update(date_to="2025-01-32"),
        lambda request: request["parameters"].update(limit=True),
        lambda request: request["parameters"].update(extra=True),
    ],
)
def test_trial_balance_request_is_closed_and_dates_are_valid(change) -> None:
    request = _request()
    change(request)
    with pytest.raises(FinancialReportError) as caught:
        validate_trial_balance_request(request)
    assert caught.value.exit_code == 2


def test_trial_balance_rejects_float_amounts_and_stale_runtime_cursor() -> None:
    bad_lines = copy.deepcopy(_LINES)
    bad_lines[0]["values"][0] = 0.0
    with pytest.raises(FinancialReportError) as caught:
        read_trial_balance(FakePort(bad_lines), _request())
    assert caught.value.code == "failed_validation"

    first = read_trial_balance(FakePort(), _request(limit=1))
    with pytest.raises(FinancialReportError) as caught:
        read_trial_balance(
            FakePort(cursor_found=False),
            _request(cursor=first["next_cursor"]),
        )
    assert caught.value.code == "invalid_cursor"


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        (
            {
                "company_visible": False,
                "access_allowed": False,
                "columns": [],
                "lines": [],
            },
            "company_unavailable",
        ),
        (
            {
                "module_installed": False,
                "access_allowed": False,
                "columns": [],
                "lines": [],
            },
            "uninstalled",
        ),
        ({"access_allowed": False, "columns": [], "lines": []}, "unauthorized"),
    ],
)
def test_trial_balance_runtime_gates_are_explicit(overrides: dict, code: str) -> None:
    with pytest.raises(FinancialReportError) as caught:
        read_trial_balance(FakePort(**overrides), _request())
    assert caught.value.code == code
