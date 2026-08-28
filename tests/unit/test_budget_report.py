from __future__ import annotations

from copy import deepcopy

import pytest

from odoo_accounting_cli_v4.capabilities.budget_report import (
    BudgetReportError,
    read_budget_report,
    validate_budget_report_request,
)

REQUEST_ID = "7bc39413-0d69-4092-9319-795d33f3167c"


def _request(parameters: dict | None = None) -> dict:
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "context": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "zh_CN",
            "timezone": "Asia/Shanghai",
        },
        "parameters": deepcopy(
            parameters if parameters is not None else {"budget_id": 71}
        ),
    }


def _achieved(line_id: int, *, source_id: int = 501) -> dict:
    return {
        "row_key": f"aal{source_id}",
        "line_type": "achieved",
        "date": "2026-08-24",
        "budget": {"id": 71, "name": "FY2026"},
        "budget_line": {"id": line_id},
        "source": {"model": "account.analytic.line", "id": source_id},
        "description": "Project effort",
        "plan_accounts": [
            {
                "plan": {"id": 21, "name": "Projects"},
                "account": {"id": 31, "name": "Project Alpha"},
            }
        ],
        "company_id": 7,
        "user": {"id": 5, "name": "V4 Accountant"},
        "budget_amount": "0",
        "achieved_amount": "125.5",
        "theoretical_amount": "0",
    }


class FakePort:
    user_id = 42

    def __init__(self, items: list[dict], **flags: bool) -> None:
        self.items = deepcopy(items)
        self.flags = flags
        self.calls: list[dict] = []

    def read(self, *, company_id: int, parameters: dict) -> dict:
        self.calls.append({"company_id": company_id, "parameters": parameters})
        return {
            "user_id": self.user_id,
            "company_visible": self.flags.get("company_visible", True),
            "module_installed": self.flags.get("module_installed", True),
            "access_allowed": self.flags.get("access_allowed", True),
            "cursor_found": self.flags.get("cursor_found", True),
            "items": deepcopy(self.items),
        }


def test_request_defaults_are_closed_and_plan_account_filters_are_paired() -> None:
    _, _, parameters = validate_budget_report_request(_request())

    assert parameters == {
        "budget_id": 71,
        "budget_line_id": None,
        "date_from": None,
        "date_to": None,
        "plan_id": None,
        "analytic_account_id": None,
        "line_type": None,
        "limit": 100,
        "cursor": None,
    }

    for invalid in (
        {"budget_id": 71, "plan_id": 21},
        {"budget_id": 71, "analytic_account_id": 31},
        {"budget_id": 71, "plan_id": 21, "analytic_account_id": 0},
    ):
        with pytest.raises(BudgetReportError) as caught:
            validate_budget_report_request(_request(invalid))
        assert caught.value.code == "invalid_request"


@pytest.mark.parametrize(
    "parameters",
    [
        {},
        {"budget_id": True},
        {"budget_id": 71, "date_from": "2026/01/01"},
        {
            "budget_id": 71,
            "date_from": "2026-12-31",
            "date_to": "2026-01-01",
        },
        {"budget_id": 71, "line_type": "committed"},
        {"budget_id": 71, "limit": 1001},
        {"budget_id": 71, "extra": True},
    ],
)
def test_request_rejects_expanded_or_invalid_parameters(parameters: dict) -> None:
    with pytest.raises(BudgetReportError) as caught:
        validate_budget_report_request(_request(parameters))
    assert caught.value.code == "invalid_request"


def test_composite_cursor_keeps_duplicate_sql_ids_on_overlapping_budget_lines() -> None:
    first = _achieved(901)
    second = _achieved(902)
    first_port = FakePort([first, second])
    first_page = read_budget_report(
        first_port,
        _request({"budget_id": 71, "limit": 1, "cursor": None}),
    )

    assert first_page["items"] == [first]
    assert first_page["has_more"] is True
    assert isinstance(first_page["next_cursor"], str)
    assert first_port.calls == [
        {
            "company_id": 7,
            "parameters": {
                "budget_id": 71,
                "budget_line_id": None,
                "date_from": None,
                "date_to": None,
                "plan_id": None,
                "analytic_account_id": None,
                "line_type": None,
                "after": None,
                "limit": 2,
            },
        }
    ]

    second_port = FakePort([second])
    second_page = read_budget_report(
        second_port,
        _request(
            {
                "budget_id": 71,
                "limit": 1,
                "cursor": first_page["next_cursor"],
            }
        ),
    )

    assert second_page == {
        "items": [second],
        "has_more": False,
        "next_cursor": None,
    }
    assert second_port.calls[0]["parameters"]["after"] == {
        "date": "2026-08-24",
        "row_key": "aal501",
        "budget_line_id": 901,
        "line_type": "achieved",
        "source_model": "account.analytic.line",
        "source_id": 501,
    }


def test_cursor_is_bound_to_filters_company_database_and_user() -> None:
    first = read_budget_report(
        FakePort([_achieved(901), _achieved(902)]),
        _request({"budget_id": 71, "limit": 1}),
    )
    changed = _request(
        {
            "budget_id": 71,
            "line_type": "achieved",
            "limit": 1,
            "cursor": first["next_cursor"],
        }
    )

    with pytest.raises(BudgetReportError) as caught:
        read_budget_report(FakePort([]), changed)
    assert caught.value.code == "invalid_cursor"


def test_full_position_must_be_unique_even_when_row_keys_overlap() -> None:
    duplicate = _achieved(901)
    with pytest.raises(BudgetReportError) as caught:
        read_budget_report(FakePort([duplicate, duplicate]), _request())
    assert caught.value.code == "failed_validation"


@pytest.mark.parametrize(
    ("flags", "code"),
    [
        ({"company_visible": False, "access_allowed": False}, "company_unavailable"),
        ({"module_installed": False, "access_allowed": False}, "uninstalled"),
        ({"access_allowed": False}, "unauthorized"),
        ({"cursor_found": False}, "invalid_cursor"),
    ],
)
def test_runtime_scope_failures_are_fail_closed(flags: dict, code: str) -> None:
    with pytest.raises(BudgetReportError) as caught:
        read_budget_report(FakePort([], **flags), _request())
    assert caught.value.code == code


def test_nonfinite_or_cross_company_rows_are_rejected() -> None:
    bad = _achieved(901)
    bad["company_id"] = 8
    with pytest.raises(BudgetReportError) as caught:
        read_budget_report(FakePort([bad]), _request())
    assert caught.value.code == "failed_validation"

    bad = _achieved(901)
    bad["achieved_amount"] = "NaN"
    with pytest.raises(BudgetReportError) as caught:
        read_budget_report(FakePort([bad]), _request())
    assert caught.value.code == "failed_validation"
