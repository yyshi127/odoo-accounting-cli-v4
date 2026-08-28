from __future__ import annotations

from copy import deepcopy

import pytest

from odoo_accounting_cli_v4.capabilities.account_returns import (
    AccountReturnReadError,
    read_account_return,
    validate_account_return_request,
)

REQUEST_ID = "7bc39413-0d69-4092-9319-795d33f3167c"


def _request(parameters: dict, *, company_id: int = 7) -> dict:
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "context": {
            "database": "odoo_cli_v4_dev",
            "company_id": company_id,
            "user_login": "v4-agent",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": deepcopy(parameters),
    }


def _return_item(return_id: int = 30) -> dict:
    return {
        "id": return_id,
        "name": "August manual return",
        "active": True,
        "date_from": "2026-08-01",
        "date_to": "2026-08-31",
        "date_deadline": "2026-09-15",
        "date_submission": None,
        "date_lock": None,
        "type": {"id": 4, "name": "Manual Return", "category": "account_return"},
        "state": "new",
        "next_state": "reviewed",
        "is_completed": False,
        "company_id": 7,
        "tax_unit_id": None,
        "manually_created": True,
        "check_counts": {"total": 1, "unresolved": 1, "resolved": 0},
    }


def _type_item(type_id: int = 4) -> dict:
    return {
        "id": type_id,
        "name": "Manual Return",
        "company_id": 7,
        "category": "account_return",
        "report": None,
        "country": None,
        "auto_generate": True,
        "states_workflow": "generic_state_review",
        "deadline_periodicity": "year",
        "deadline_start_date": "2026-01-01",
        "deadline_days_delay": 15,
    }


def _check_item(check_id: int = 50, *, return_id: int = 30) -> dict:
    return {
        "id": check_id,
        "return": {"id": return_id, "name": "August manual return"},
        "code": "manual_check",
        "type": "check",
        "name": "Review manual return",
        "message": None,
        "state": "new",
        "result": "todo",
        "records_count": 0,
    }


class FakePort:
    user_id = 5

    def __init__(self, items: list[dict], **flags: bool) -> None:
        self.items = deepcopy(items)
        self.flags = flags
        self.calls: list[dict] = []

    def read(self, *, capability_id: str, company_id: int, parameters: dict) -> dict:
        self.calls.append(
            {
                "capability_id": capability_id,
                "company_id": company_id,
                "parameters": deepcopy(parameters),
            }
        )
        company_visible = self.flags.get("company_visible", True)
        module_installed = self.flags.get("module_installed", True)
        return {
            "user_id": self.user_id,
            "company_visible": company_visible,
            "module_installed": module_installed,
            "access_allowed": self.flags.get(
                "access_allowed", company_visible and module_installed
            ),
            "cursor_found": self.flags.get("cursor_found", True),
            "items": deepcopy(self.items),
        }


def test_search_defaults_are_closed_and_filters_are_fixed() -> None:
    _, _, parameters = validate_account_return_request(
        "account.return.search", _request({})
    )
    assert parameters == {
        "type_id": None,
        "state": None,
        "completed": None,
        "deadline_from": None,
        "deadline_to": None,
        "active": True,
        "limit": 100,
        "cursor": None,
    }

    for invalid in (
        {"type_id": True},
        {"state": "approved"},
        {"completed": 1},
        {"deadline_from": "2026/01/01"},
        {"deadline_from": "2026-12-31", "deadline_to": "2026-01-01"},
        {"active": "yes"},
        {"limit": 1001},
        {"name": "expanded search"},
    ):
        with pytest.raises(AccountReturnReadError) as caught:
            validate_account_return_request("account.return.search", _request(invalid))
        assert caught.value.code == "invalid_request"


def test_single_and_summary_requests_are_exact() -> None:
    cases = (
        ("account.return.get", {"return_id": 30}),
        ("account.return.summary", {"as_of": "2026-08-28"}),
        ("account.return.check.get", {"check_id": 50}),
    )
    for capability_id, expected in cases:
        _, _, parameters = validate_account_return_request(
            capability_id, _request(expected)
        )
        assert parameters == expected

    for capability_id, parameters in (
        ("account.return.get", {}),
        ("account.return.summary", {}),
        ("account.return.summary", {"as_of": "2026-08-28", "extra": True}),
        ("account.return.check.get", {"check_id": 0}),
    ):
        with pytest.raises(AccountReturnReadError):
            validate_account_return_request(capability_id, _request(parameters))


def test_type_and_check_list_defaults_are_closed() -> None:
    _, _, type_parameters = validate_account_return_request(
        "account.return.type.list", _request({})
    )
    assert type_parameters == {
        "category": None,
        "limit": 100,
        "cursor": None,
    }

    _, _, check_parameters = validate_account_return_request(
        "account.return.check.list", _request({"return_id": 30})
    )
    assert check_parameters == {
        "return_id": 30,
        "result": None,
        "type": None,
        "limit": 100,
        "cursor": None,
    }

    for invalid in (
        {"return_id": 30, "result": "passed"},
        {"return_id": 30, "type": "action"},
        {"result": "todo"},
    ):
        with pytest.raises(AccountReturnReadError):
            validate_account_return_request(
                "account.return.check.list", _request(invalid)
            )


def test_search_uses_bound_id_cursor_and_limit_plus_one() -> None:
    first_port = FakePort([_return_item(30), _return_item(29)])
    first = read_account_return(
        first_port,
        "account.return.search",
        _request({"state": "new", "limit": 1}),
    )
    assert first == {
        "items": [_return_item(30)],
        "has_more": True,
        "next_cursor": first["next_cursor"],
    }
    assert isinstance(first["next_cursor"], str)
    assert first_port.calls == [
        {
            "capability_id": "account.return.search",
            "company_id": 7,
            "parameters": {
                "type_id": None,
                "state": "new",
                "completed": None,
                "deadline_from": None,
                "deadline_to": None,
                "active": True,
                "after": None,
                "limit": 2,
            },
        }
    ]

    second_port = FakePort([_return_item(29)])
    second = read_account_return(
        second_port,
        "account.return.search",
        _request({"state": "new", "limit": 1, "cursor": first["next_cursor"]}),
    )
    assert second == {
        "items": [_return_item(29)],
        "has_more": False,
        "next_cursor": None,
    }
    assert second_port.calls[0]["parameters"]["after"] == 30

    with pytest.raises(AccountReturnReadError) as caught:
        read_account_return(
            FakePort([]),
            "account.return.search",
            _request(
                {
                    "type_id": 4,
                    "state": "new",
                    "limit": 1,
                    "cursor": first["next_cursor"],
                }
            ),
        )
    assert caught.value.code == "invalid_cursor"


def test_get_summary_type_list_and_check_reads_validate_exact_results() -> None:
    assert (
        read_account_return(
            FakePort([_return_item()]),
            "account.return.get",
            _request({"return_id": 30}),
        )
        == _return_item()
    )

    summary = {
        "company_id": 7,
        "as_of": "2026-08-28",
        "counts": {
            "total": 5,
            "open": 4,
            "completed": 1,
            "overdue": 1,
            "due_today": 1,
            "due_next_30_days": 1,
            "later": 1,
        },
    }
    assert (
        read_account_return(
            FakePort([summary]),
            "account.return.summary",
            _request({"as_of": "2026-08-28"}),
        )
        == summary
    )

    assert read_account_return(
        FakePort([_type_item()]),
        "account.return.type.list",
        _request({"category": "account_return"}),
    ) == {"items": [_type_item()], "has_more": False, "next_cursor": None}

    assert read_account_return(
        FakePort([_check_item()]),
        "account.return.check.list",
        _request({"return_id": 30, "result": "todo"}),
    ) == {"items": [_check_item()], "has_more": False, "next_cursor": None}

    assert (
        read_account_return(
            FakePort([_check_item()]),
            "account.return.check.get",
            _request({"check_id": 50}),
        )
        == _check_item()
    )


def test_check_cursor_is_bound_to_visible_return() -> None:
    first = read_account_return(
        FakePort([_check_item(50), _check_item(49)]),
        "account.return.check.list",
        _request({"return_id": 30, "limit": 1}),
    )
    with pytest.raises(AccountReturnReadError) as caught:
        read_account_return(
            FakePort([]),
            "account.return.check.list",
            _request({"return_id": 31, "limit": 1, "cursor": first["next_cursor"]}),
        )
    assert caught.value.code == "invalid_cursor"


@pytest.mark.parametrize(
    ("flags", "code"),
    [
        ({"company_visible": False}, "company_unavailable"),
        ({"module_installed": False}, "uninstalled"),
        ({"access_allowed": False}, "unauthorized"),
    ],
)
def test_scope_and_cursor_failures_are_closed(flags: dict, code: str) -> None:
    with pytest.raises(AccountReturnReadError) as caught:
        read_account_return(
            FakePort([], **flags), "account.return.search", _request({})
        )
    assert caught.value.code == code


def test_result_shape_company_order_and_counts_fail_closed() -> None:
    bad_summary = {
        "company_id": 7,
        "as_of": "2026-08-28",
        "counts": {
            "total": 5,
            "open": 4,
            "completed": 1,
            "overdue": 1,
            "due_today": 1,
            "due_next_30_days": 1,
            "later": 2,
        },
    }
    for capability_id, parameters, items in (
        ("account.return.search", {}, [{**_return_item(), "company_id": 8}]),
        ("account.return.search", {}, [_return_item(29), _return_item(30)]),
        ("account.return.summary", {"as_of": "2026-08-28"}, [bad_summary]),
        (
            "account.return.check.get",
            {"check_id": 50},
            [{**_check_item(), "action": {"type": "ir.actions.act_window"}}],
        ),
    ):
        with pytest.raises(AccountReturnReadError) as caught:
            read_account_return(FakePort(items), capability_id, _request(parameters))
        assert caught.value.code == "failed_validation"
