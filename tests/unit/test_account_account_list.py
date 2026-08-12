from __future__ import annotations

import pytest

from odoo_accounting_cli_v4.capabilities.account_account_list import (
    AccountListError,
    decode_cursor,
    read_account_accounts,
)


class FakePort:
    def __init__(
        self,
        *,
        company_visible: bool = True,
        module_installed: bool = True,
        access_allowed: bool | None = None,
        rows: list[dict] | None = None,
    ) -> None:
        self._company_visible = company_visible
        self._module_installed = module_installed
        self._access_allowed = (
            company_visible and module_installed
            if access_allowed is None
            else access_allowed
        )
        self._rows = rows or []
        self.user_id = 42
        self.read_calls: list[dict] = []

    def read_page(
        self,
        *,
        company_id: int,
        after_code: str | None,
        after_id: int | None,
        limit: int,
    ) -> dict:
        self.read_calls.append(
            {
                "company_id": company_id,
                "after_code": after_code,
                "after_id": after_id,
                "limit": limit,
            }
        )
        return {
            "user_id": self.user_id,
            "company_visible": self._company_visible,
            "module_installed": self._module_installed,
            "access_allowed": self._access_allowed,
            "rows": self._rows[:limit],
        }


def _request(*, company_id: int = 7, limit: int = 2, cursor: str | None = None) -> dict:
    return {
        "schema_version": "v1",
        "request_id": "7bc39413-0d69-4092-9319-795d33f3167c",
        "context": {
            "database": "v4-dev",
            "company_id": company_id,
            "user_login": "v4-agent",
            "language": "zh_CN",
            "timezone": "Asia/Shanghai",
        },
        "parameters": {"limit": limit, "cursor": cursor},
    }


def test_list_uses_company_scope_and_stable_keyset_cursor() -> None:
    rows = [
        {
            "id": 10,
            "code": "1000",
            "name": "Cash",
            "account_type": "asset_cash",
            "active": True,
            "reconcile": False,
            "company_ids": [7],
        },
        {
            "id": 11,
            "code": "1100",
            "name": "Bank",
            "account_type": "asset_cash",
            "active": True,
            "reconcile": True,
            "company_ids": [7],
        },
        {
            "id": 12,
            "code": "1200",
            "name": "Receivable",
            "account_type": "asset_receivable",
            "active": True,
            "reconcile": True,
            "company_ids": [7],
        },
    ]
    port = FakePort(rows=rows)

    result = read_account_accounts(port, _request())

    assert [item["id"] for item in result["items"]] == [10, 11]
    assert result["has_more"] is True
    assert result["next_cursor"] is not None
    assert decode_cursor(
        result["next_cursor"],
        company_id=7,
        database="v4-dev",
        user_login="v4-agent",
    ) == ("1100", 11)
    assert port.read_calls == [
        {"company_id": 7, "after_code": None, "after_id": None, "limit": 3}
    ]


def test_cursor_is_bound_to_company_scope() -> None:
    first = read_account_accounts(
        FakePort(
            rows=[
                {
                    "id": 10,
                    "code": "1000",
                    "name": "Cash",
                    "account_type": "asset_cash",
                    "active": True,
                    "reconcile": False,
                    "company_ids": [7],
                },
                {
                    "id": 11,
                    "code": "1100",
                    "name": "Bank",
                    "account_type": "asset_cash",
                    "active": True,
                    "reconcile": True,
                    "company_ids": [7],
                },
            ]
        ),
        _request(limit=1),
    )

    rejected_port = FakePort()
    with pytest.raises(AccountListError) as caught:
        read_account_accounts(
            rejected_port, _request(company_id=8, cursor=first["next_cursor"])
        )

    assert caught.value.code == "invalid_cursor"
    assert rejected_port.read_calls == []


@pytest.mark.parametrize(
    ("context_key", "context_value"),
    [("database", "another-db"), ("user_login", "another-user")],
)
def test_cursor_is_bound_to_database_and_user(
    context_key: str, context_value: str
) -> None:
    first = read_account_accounts(
        FakePort(
            rows=[
                {
                    "id": 10,
                    "code": "1000",
                    "name": "Cash",
                    "account_type": "asset_cash",
                    "active": True,
                    "reconcile": False,
                    "company_ids": [7],
                },
                {
                    "id": 11,
                    "code": "1100",
                    "name": "Bank",
                    "account_type": "asset_cash",
                    "active": True,
                    "reconcile": True,
                    "company_ids": [7],
                },
            ]
        ),
        _request(limit=1),
    )
    request = _request(cursor=first["next_cursor"])
    request["context"][context_key] = context_value

    with pytest.raises(AccountListError) as caught:
        read_account_accounts(FakePort(), request)

    assert caught.value.code == "invalid_cursor"


def test_company_failure_is_returned_from_the_single_bridge_read() -> None:
    port = FakePort(company_visible=False)

    with pytest.raises(AccountListError) as caught:
        read_account_accounts(port, _request())

    assert caught.value.code == "company_unavailable"
    assert len(port.read_calls) == 1


@pytest.mark.parametrize(
    ("port", "expected_code"),
    [
        (FakePort(module_installed=False), "uninstalled"),
        (FakePort(access_allowed=False), "unauthorized"),
    ],
)
def test_runtime_availability_failures_are_explicit(port: FakePort, expected_code: str) -> None:
    with pytest.raises(AccountListError) as caught:
        read_account_accounts(port, _request())

    assert caught.value.code == expected_code


def test_logically_contradictory_bridge_page_is_rejected() -> None:
    port = FakePort(company_visible=False, access_allowed=True)

    with pytest.raises(AccountListError) as caught:
        read_account_accounts(port, _request())

    assert caught.value.code == "failed_validation"
    assert caught.value.exit_code == 8


def test_default_and_maximum_limits_follow_v1_contract() -> None:
    default_request = _request()
    del default_request["parameters"]["limit"]
    default_port = FakePort(rows=[])
    result = read_account_accounts(default_port, default_request)
    assert result == {"items": [], "has_more": False, "next_cursor": None}
    assert default_port.read_calls[0]["limit"] == 101

    request = _request(limit=1000)
    maximum_port = FakePort(rows=[])
    read_account_accounts(maximum_port, request)
    assert maximum_port.read_calls[0]["limit"] == 1001

    request["parameters"]["limit"] = 1001
    with pytest.raises(AccountListError) as caught:
        read_account_accounts(FakePort(), request)
    assert caught.value.code == "invalid_request"


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("name", None),
        ("account_type", None),
        ("active", None),
        ("reconcile", None),
        ("company_ids", [7, "8"]),
    ],
)
def test_invalid_odoo_row_never_becomes_verified_data(
    field: str, invalid_value: object
) -> None:
    row = {
        "id": 10,
        "code": "1000",
        "name": "Cash",
        "account_type": "asset_cash",
        "active": True,
        "reconcile": False,
        "company_ids": [7],
    }
    row[field] = invalid_value

    with pytest.raises(AccountListError) as caught:
        read_account_accounts(FakePort(rows=[row]), _request())

    assert caught.value.code == "failed_validation"
    assert caught.value.exit_code == 8
