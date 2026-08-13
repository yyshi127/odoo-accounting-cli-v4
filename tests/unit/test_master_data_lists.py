from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from odoo_accounting_cli_v4.capabilities.master_data_lists import (
    MasterDataListError,
    read_master_data,
    validate_master_data_request,
)
from odoo_accounting_cli_v4.registry import load_registry


CAPABILITIES = (
    "company.accounting_context.list",
    "journal.list",
    "tax.list",
    "payment_term.list",
    "currency.list",
)


class FakePort:
    def __init__(
        self,
        rows: list[dict] | None = None,
        *,
        company_visible: bool = True,
        module_installed: bool = True,
        access_allowed: bool | None = None,
        user_id: int = 42,
    ) -> None:
        self.rows = rows or []
        self.company_visible = company_visible
        self.module_installed = module_installed
        self.access_allowed = (
            company_visible and module_installed
            if access_allowed is None
            else access_allowed
        )
        self.user_id = user_id
        self.calls: list[dict] = []

    def read_page(
        self,
        *,
        company_id: int,
        after: list | None,
        limit: int,
    ) -> dict:
        self.calls.append(
            {
                "company_id": company_id,
                "after": after,
                "limit": limit,
            }
        )
        return {
            "user_id": self.user_id,
            "company_visible": self.company_visible,
            "module_installed": self.module_installed,
            "access_allowed": self.access_allowed,
            "rows": copy.deepcopy(self.rows[:limit]),
        }


def _request(
    *,
    company_id: int = 7,
    database: str = "v4-dev",
    user_login: str = "v4-agent",
    limit: int = 1,
    cursor: str | None = None,
) -> dict:
    return {
        "schema_version": "v1",
        "request_id": "7bc39413-0d69-4092-9319-795d33f3167c",
        "context": {
            "database": database,
            "company_id": company_id,
            "user_login": user_login,
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": {"limit": limit, "cursor": cursor},
    }


def _rows(capability_id: str) -> list[dict]:
    if capability_id == "company.accounting_context.list":
        return [
            {
                "id": 7,
                "name": "China Company",
                "sequence": 0,
                "active": True,
                "current": True,
                "currency": {"id": 6, "code": "CNY", "decimal_places": 2},
                "country": {"id": 48, "code": "CN", "name": "China"},
                "fiscal_country": {
                    "id": 48,
                    "code": "CN",
                    "name": "China",
                },
                "chart_template": "cn_oscg",
                "tax_calculation_rounding_method": "round_globally",
                "fiscal_year_end": {"month": 12, "day": 31},
            },
            {
                "id": 8,
                "name": "Singapore Company",
                "sequence": 10,
                "active": True,
                "current": False,
                "currency": {"id": 37, "code": "SGD", "decimal_places": 2},
                "country": {
                    "id": 197,
                    "code": "SG",
                    "name": "Singapore",
                },
                "fiscal_country": {
                    "id": 197,
                    "code": "SG",
                    "name": "Singapore",
                },
                "chart_template": "sg",
                "tax_calculation_rounding_method": "round_globally",
                "fiscal_year_end": {"month": 12, "day": 31},
            },
        ]
    if capability_id == "journal.list":
        return [
            {
                "id": 9,
                "sequence": 5,
                "code": "INV",
                "name": "Sales",
                "type": "sale",
                "active": True,
                "currency": None,
                "company_id": 7,
            },
            {
                "id": 10,
                "sequence": 6,
                "code": "BILL",
                "name": "Purchases",
                "type": "purchase",
                "active": True,
                "currency": {"id": 6, "code": "CNY"},
                "company_id": 7,
            },
        ]
    if capability_id == "tax.list":
        return [
            {
                "id": 5,
                "sequence": 1,
                "name": "13% INC",
                "type_tax_use": "sale",
                "amount_type": "percent",
                "amount": "13.0000",
                "price_include": False,
                "include_base_amount": False,
                "is_base_affected": True,
                "active": True,
                "tax_group": {"id": 5, "name": "VAT 13%"},
                "company_id": 7,
            },
            {
                "id": 6,
                "sequence": 1,
                "name": "9% INC",
                "type_tax_use": "sale",
                "amount_type": "percent",
                "amount": "9",
                "price_include": False,
                "include_base_amount": False,
                "is_base_affected": True,
                "active": True,
                "tax_group": {"id": 4, "name": "VAT 9%"},
                "company_id": 7,
            },
        ]
    if capability_id == "payment_term.list":
        return [
            {
                "id": 1,
                "sequence": 10,
                "name": "Immediate Payment",
                "active": True,
                "company_id": None,
                "display_on_invoice": True,
                "early_discount": True,
                "discount_percentage": "150",
                "discount_days": 10,
                "early_pay_discount_computation": "included",
                "lines": [
                    {
                        "id": 1,
                        "value": "percent",
                        "value_amount": "100",
                        "delay_type": "days_after",
                        "nb_days": 0,
                        "days_next_month": "10",
                    }
                ],
            },
            {
                "id": 2,
                "sequence": 10,
                "name": "15 Days",
                "active": True,
                "company_id": 7,
                "display_on_invoice": False,
                "early_discount": False,
                "discount_percentage": "-1",
                "discount_days": 10,
                "early_pay_discount_computation": "included",
                "lines": [
                    {
                        "id": 2,
                        "value": "percent",
                        "value_amount": "100.0",
                        "delay_type": "days_after",
                        "nb_days": 15,
                        "days_next_month": None,
                    }
                ],
            },
        ]
    if capability_id == "currency.list":
        return [
            {
                "id": 6,
                "code": "CNY",
                "name": "Chinese yuan",
                "symbol": "¥",
                "rounding": "0.01",
                "decimal_places": 2,
                "active": True,
                "position": "before",
                "is_company_currency": True,
            },
            {
                "id": 37,
                "code": "SGD",
                "name": None,
                "symbol": "S$",
                "rounding": "0.01",
                "decimal_places": 2,
                "active": True,
                "position": None,
                "is_company_currency": False,
            },
        ]
    raise AssertionError(capability_id)


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_each_list_uses_one_scoped_keyset_read(capability_id: str) -> None:
    port = FakePort(_rows(capability_id))

    result = read_master_data(capability_id, port, _request())

    assert result["items"] == _rows(capability_id)[:1]
    assert result["has_more"] is True
    assert isinstance(result["next_cursor"], str)
    assert port.calls == [
        {
            "company_id": 7,
            "after": None,
            "limit": 2,
        }
    ]

    next_port = FakePort(_rows(capability_id)[1:])
    second = read_master_data(
        capability_id,
        next_port,
        _request(cursor=result["next_cursor"], limit=10),
    )
    assert second == {
        "items": _rows(capability_id)[1:],
        "has_more": False,
        "next_cursor": None,
    }
    expected_after = {
        "company.accounting_context.list": [7],
        "journal.list": [5, "sale", "INV", 9],
        "tax.list": [1, 5],
        "payment_term.list": [10, 1],
        "currency.list": [True, "CNY", 6],
    }[capability_id]
    assert next_port.calls[0]["after"] == expected_after


def test_cursor_is_bound_to_capability_database_company_and_user() -> None:
    first = read_master_data("journal.list", FakePort(_rows("journal.list")), _request())
    assert first["next_cursor"]

    mutations = [
        ("tax.list", _request(cursor=first["next_cursor"])),
        (
            "journal.list",
            _request(database="other", cursor=first["next_cursor"]),
        ),
        (
            "journal.list",
            _request(company_id=8, cursor=first["next_cursor"]),
        ),
        (
            "journal.list",
            _request(user_login="other", cursor=first["next_cursor"]),
        ),
    ]
    for capability_id, request in mutations:
        port = FakePort()
        with pytest.raises(MasterDataListError) as caught:
            read_master_data(capability_id, port, request)
        assert caught.value.code == "invalid_cursor"
        assert port.calls == []


def test_request_validation_is_closed_and_capability_specific() -> None:
    request = _request()
    request["parameters"]["unexpected"] = True
    with pytest.raises(MasterDataListError) as caught:
        validate_master_data_request("journal.list", request)
    assert caught.value.code == "invalid_request"
    assert caught.value.exit_code == 2

    with pytest.raises(MasterDataListError) as caught:
        validate_master_data_request("unknown.list", _request())
    assert caught.value.code == "unsupported_capability"
    assert caught.value.exit_code == 4


@pytest.mark.parametrize(
    ("capability_id", "mutation"),
    [
        ("journal.list", lambda row: row.update(company_id=8)),
        ("tax.list", lambda row: row.update(amount=13.0)),
        ("payment_term.list", lambda row: row.update(company_id=8)),
        ("currency.list", lambda row: row.update(rounding="1e-2")),
        ("currency.list", lambda row: row.update(extra=True)),
        (
            "company.accounting_context.list",
            lambda row: row.update(current="yes"),
        ),
    ],
)
def test_invalid_or_out_of_scope_rows_never_become_verified(
    capability_id: str, mutation
) -> None:
    row = _rows(capability_id)[0]
    mutation(row)

    with pytest.raises(MasterDataListError) as caught:
        read_master_data(capability_id, FakePort([row]), _request(limit=10))

    assert caught.value.code == "failed_validation"
    assert caught.value.exit_code == 8


def test_fixed_payment_term_amount_is_not_artificially_forced_to_zero() -> None:
    row = _rows("payment_term.list")[0]
    row["early_discount"] = False
    row["lines"] = [
        {
            "id": 1,
            "value": "fixed",
            "value_amount": "-25.00",
            "delay_type": "days_after",
            "nb_days": 0,
            "days_next_month": "10",
        },
        {
            "id": 2,
            "value": "percent",
            "value_amount": "100",
            "delay_type": "days_after",
            "nb_days": 30,
            "days_next_month": "10",
        },
    ]

    result = read_master_data(
        "payment_term.list", FakePort([row]), _request(limit=10)
    )

    assert result["items"][0]["lines"][0]["value_amount"] == "-25.00"


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_unstable_row_order_is_rejected(capability_id: str) -> None:
    rows = list(reversed(_rows(capability_id)))
    with pytest.raises(MasterDataListError) as caught:
        read_master_data(capability_id, FakePort(rows), _request(limit=10))
    assert caught.value.code == "failed_validation"


@pytest.mark.parametrize(
    ("port", "code"),
    [
        (FakePort(company_visible=False), "company_unavailable"),
        (FakePort(module_installed=False), "uninstalled"),
        (FakePort(access_allowed=False), "unauthorized"),
    ],
)
def test_runtime_availability_failures_are_explicit(port: FakePort, code: str) -> None:
    with pytest.raises(MasterDataListError) as caught:
        read_master_data("journal.list", port, _request())
    assert caught.value.code == code
    assert len(port.calls) == 1


def test_contradictory_or_wrong_user_page_is_rejected() -> None:
    contradictory = FakePort(company_visible=False, access_allowed=True)
    with pytest.raises(MasterDataListError) as caught:
        read_master_data("journal.list", contradictory, _request())
    assert caught.value.code == "failed_validation"

    class WrongUserPort(FakePort):
        def read_page(self, **kwargs) -> dict:
            page = super().read_page(**kwargs)
            page["user_id"] = self.user_id + 1
            return page

    with pytest.raises(MasterDataListError) as caught:
        read_master_data("journal.list", WrongUserPort(), _request())
    assert caught.value.code == "failed_validation"


def test_default_and_maximum_limits_follow_v1_contract() -> None:
    default_request = _request()
    del default_request["parameters"]["limit"]
    port = FakePort()
    assert read_master_data("journal.list", port, default_request) == {
        "items": [],
        "has_more": False,
        "next_cursor": None,
    }
    assert port.calls[0]["limit"] == 101

    maximum = _request(limit=1000)
    port = FakePort()
    read_master_data("journal.list", port, maximum)
    assert port.calls[0]["limit"] == 1001

    with pytest.raises(MasterDataListError):
        read_master_data("journal.list", FakePort(), _request(limit=1001))


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_specialized_schemas_accept_contract_documents(capability_id: str) -> None:
    schema_dir = Path(__file__).parents[2] / "schemas" / "v1"
    request_schema = json.loads(
        (schema_dir / f"{capability_id}.request.schema.json").read_text(
            encoding="utf-8"
        )
    )
    response_schema = json.loads(
        (schema_dir / f"{capability_id}.response.schema.json").read_text(
            encoding="utf-8"
        )
    )
    registry = Draft202012Validator.META_SCHEMA
    assert registry
    Draft202012Validator.check_schema(request_schema)
    Draft202012Validator.check_schema(response_schema)
    runtime_registry = load_registry()
    runtime_registry.validate_instance(
        f"schemas/v1/{capability_id}.request.schema.json", _request()
    )

    response = {
        "schema_version": "v1",
        "request_id": _request()["request_id"],
        "success": True,
        "capability": capability_id,
        "status": "verified",
        "data": {
            "items": _rows(capability_id),
            "has_more": False,
            "next_cursor": None,
        },
        "warnings": [],
        "error": None,
        "odoo": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_id": 42,
            "model": "res.company",
            "record_ids": [row["id"] for row in _rows(capability_id)],
        },
        "audit": {
            "operation_id": None,
            "idempotency_key": None,
            "verification": {"result": "passed"},
        },
    }
    runtime_registry.validate_instance(
        f"schemas/v1/{capability_id}.response.schema.json", response
    )
