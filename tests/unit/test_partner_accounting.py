from __future__ import annotations
import base64
import copy
import json
from pathlib import Path

import pytest

from odoo_accounting_cli_v4.capabilities.partner_accounting import (
    PartnerAccountingError,
    search_accounting_partners,
    validate_partner_accounting_search_request,
)
from odoo_accounting_cli_v4.registry import load_registry


class FakePort:
    def __init__(
        self,
        *,
        rows: list[dict] | None = None,
        company_visible: bool = True,
        module_installed: bool = True,
        access_allowed: bool | None = None,
    ) -> None:
        self.user_id = 42
        self.rows = copy.deepcopy(rows or [])
        self.company_visible = company_visible
        self.module_installed = module_installed
        self.access_allowed = (
            company_visible and module_installed
            if access_allowed is None
            else access_allowed
        )
        self.search_calls: list[dict] = []

    def search_page(
        self,
        *,
        company_id: int,
        after: list[object] | None,
        limit: int,
        filters: dict[str, object],
    ) -> dict:
        self.search_calls.append(
            {
                "company_id": company_id,
                "after": after,
                "limit": limit,
                "filters": filters,
            }
        )
        return {
            "user_id": self.user_id,
            "company_visible": self.company_visible,
            "module_installed": self.module_installed,
            "access_allowed": self.access_allowed,
            "rows": copy.deepcopy(self.rows[:limit]),
        }


def _request(**parameters: object) -> dict:
    return {
        "schema_version": "v1",
        "request_id": "7bc39413-0d69-4092-9319-795d33f3167c",
        "context": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "zh_CN",
            "timezone": "Asia/Shanghai",
        },
        "parameters": parameters,
    }


def _account(record_id: int, code: str, name: str) -> dict:
    return {"id": record_id, "code": code, "name": name}


def _row(
    record_id: int,
    complete_name: str,
    *,
    company_id: int | None = 7,
    customer_rank: int = 1,
    supplier_rank: int = 0,
) -> dict:
    return {
        "id": record_id,
        "complete_name": complete_name,
        "ref": f"PARTNER-{record_id}",
        "active": True,
        "is_company": True,
        "company_id": company_id,
        "customer_rank": customer_rank,
        "supplier_rank": supplier_rank,
        "receivable_account": _account(121, "112200", "Accounts Receivable"),
        "payable_account": _account(221, "220200", "Accounts Payable"),
    }


def test_search_defaults_to_both_and_uses_one_company_scoped_page() -> None:
    row = _row(10, "Alpha Customer", company_id=None)
    port = FakePort(rows=[row])

    result = search_accounting_partners(port, _request())

    assert result == {"items": [row], "has_more": False, "next_cursor": None}
    assert port.search_calls == [
        {
            "company_id": 7,
            "after": None,
            "limit": 101,
            "filters": {"role": "both", "query": None},
        }
    ]


def test_search_paginates_in_complete_name_then_id_order() -> None:
    rows = [
        _row(10, "Alpha"),
        _row(11, "Beta"),
        _row(12, "Gamma", customer_rank=0, supplier_rank=2),
    ]
    first = search_accounting_partners(FakePort(rows=rows), _request(limit=2))

    assert [item["id"] for item in first["items"]] == [10, 11]
    assert first["has_more"] is True
    assert isinstance(first["next_cursor"], str)

    port = FakePort(rows=[rows[-1]])
    second = search_accounting_partners(
        port, _request(limit=2, cursor=first["next_cursor"])
    )
    assert second["items"] == [rows[-1]]
    assert port.search_calls[0]["after"] == ["Beta", 11]


def test_cursor_is_bound_to_database_company_user_and_normalized_filters() -> None:
    first = search_accounting_partners(
        FakePort(rows=[_row(10, "Alpha"), _row(11, "Beta")]),
        _request(limit=1, role="customer", query="Alpha"),
    )
    assert first["next_cursor"]

    mutations = [
        ("context", "database", "other-db"),
        ("context", "company_id", 8),
        ("context", "user_login", "other-user"),
        ("parameters", "role", "both"),
        ("parameters", "query", "Beta"),
    ]
    for section, key, value in mutations:
        request = _request(
            limit=1,
            role="customer",
            query="Alpha",
            cursor=first["next_cursor"],
        )
        request[section][key] = value
        port = FakePort()
        with pytest.raises(PartnerAccountingError) as caught:
            search_accounting_partners(port, request)
        assert caught.value.code == "invalid_cursor"
        assert caught.value.exit_code == 2
        assert port.search_calls == []


@pytest.mark.parametrize(
    "mutate",
    [
        lambda raw: raw.replace('"version":1', '"version":1,"version":1'),
        lambda raw: raw.replace('"version":1', '"version":1.0'),
        lambda raw: raw.replace('"version":1', '"version":NaN'),
    ],
)
def test_cursor_rejects_duplicate_keys_floats_and_nonfinite_numbers(mutate) -> None:
    first = search_accounting_partners(
        FakePort(rows=[_row(10, "Alpha"), _row(11, "Beta")]), _request(limit=1)
    )
    raw = base64.urlsafe_b64decode(first["next_cursor"] + "==").decode("utf-8")
    forged = (
        base64.urlsafe_b64encode(mutate(raw).encode("utf-8"))
        .decode("ascii")
        .rstrip("=")
    )
    port = FakePort()

    with pytest.raises(PartnerAccountingError) as caught:
        search_accounting_partners(port, _request(limit=1, cursor=forged))

    assert caught.value.code == "invalid_cursor"
    assert port.search_calls == []


@pytest.mark.parametrize(
    "parameters",
    [
        {"unexpected": True},
        {"role": None},
        {"role": "CUSTOMER"},
        {"role": "invalid"},
        {"query": " untrimmed"},
        {"query": "trailing "},
        {"query": "x" * 201},
        {"query": 7},
        {"limit": True},
        {"limit": 1.0},
        {"limit": 0},
        {"limit": 1001},
        {"cursor": ""},
    ],
)
def test_invalid_request_fails_before_the_port(parameters: dict) -> None:
    port = FakePort()
    with pytest.raises(PartnerAccountingError) as caught:
        search_accounting_partners(port, _request(**parameters))
    assert caught.value.code == "invalid_request"
    assert caught.value.exit_code == 2
    assert port.search_calls == []


def test_validator_exposes_canonical_defaults_and_filters() -> None:
    request_id, context, filters, limit, cursor = (
        validate_partner_accounting_search_request(_request())
    )
    assert request_id == _request()["request_id"]
    assert context["company_id"] == 7
    assert filters == {"role": "both", "query": None}
    assert limit == 100
    assert cursor is None


@pytest.mark.parametrize(
    "mutation",
    [
        lambda row: row.update(extra=True),
        lambda row: row.update(id=True),
        lambda row: row.update(company_id=8),
        lambda row: row.update(company_id=False),
        lambda row: row.update(complete_name=""),
        lambda row: row.update(ref=""),
        lambda row: row.update(active=1),
        lambda row: row.update(customer_rank=1.0),
        lambda row: row.update(customer_rank=-1),
        lambda row: row.update(customer_rank=0, supplier_rank=0),
        lambda row: row["receivable_account"].update(extra=True),
        lambda row: row["payable_account"].update(id=221.0),
    ],
)
def test_invalid_or_out_of_scope_rows_never_become_verified(mutation) -> None:
    row = _row(10, "Alpha")
    mutation(row)
    with pytest.raises(PartnerAccountingError) as caught:
        search_accounting_partners(FakePort(rows=[row]), _request())
    assert caught.value.code == "failed_validation"
    assert caught.value.exit_code == 8


def test_nullable_partner_fields_and_both_roles_are_supported() -> None:
    row = _row(10, "Alpha", company_id=None, customer_rank=1, supplier_rank=1)
    row.update(ref=None, receivable_account=None, payable_account=None)

    result = search_accounting_partners(FakePort(rows=[row]), _request())

    assert result["items"] == [row]


@pytest.mark.parametrize(
    ("role", "row"),
    [
        ("customer", _row(10, "Vendor", customer_rank=0, supplier_rank=1)),
        ("vendor", _row(10, "Customer", customer_rank=1, supplier_rank=0)),
    ],
)
def test_rows_must_match_the_requested_role(role: str, row: dict) -> None:
    with pytest.raises(PartnerAccountingError) as caught:
        search_accounting_partners(FakePort(rows=[row]), _request(role=role))
    assert caught.value.code == "failed_validation"


@pytest.mark.parametrize(
    "rows",
    [
        [_row(11, "Beta"), _row(10, "Alpha")],
        [_row(11, "Alpha"), _row(10, "Alpha")],
        [_row(10, "Alpha"), _row(10, "Beta")],
    ],
)
def test_search_requires_unique_ascending_name_id_keys(rows: list[dict]) -> None:
    with pytest.raises(PartnerAccountingError) as caught:
        search_accounting_partners(FakePort(rows=rows), _request())
    assert caught.value.code == "failed_validation"


@pytest.mark.parametrize(
    ("port", "code"),
    [
        (FakePort(company_visible=False), "company_unavailable"),
        (FakePort(module_installed=False), "uninstalled"),
        (FakePort(access_allowed=False), "unauthorized"),
    ],
)
def test_runtime_availability_failures_are_explicit(
    port: FakePort, code: str
) -> None:
    with pytest.raises(PartnerAccountingError) as caught:
        search_accounting_partners(port, _request())
    assert caught.value.code == code


def test_contradictory_or_wrong_user_page_is_rejected() -> None:
    with pytest.raises(PartnerAccountingError) as caught:
        search_accounting_partners(
            FakePort(company_visible=False, access_allowed=True), _request()
        )
    assert caught.value.code == "failed_validation"

    class WrongUserPort(FakePort):
        def search_page(self, **kwargs) -> dict:
            page = super().search_page(**kwargs)
            page["user_id"] = self.user_id + 1
            return page

    with pytest.raises(PartnerAccountingError) as caught:
        search_accounting_partners(WrongUserPort(), _request())
    assert caught.value.code == "failed_validation"


def _success_response(data: dict) -> dict:
    return {
        "schema_version": "v1",
        "request_id": _request()["request_id"],
        "success": True,
        "capability": "partner.accounting.search",
        "status": "verified",
        "data": data,
        "warnings": [],
        "error": None,
        "odoo": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_id": 42,
            "model": "res.partner",
            "record_ids": [item["id"] for item in data["items"]],
        },
        "audit": {
            "operation_id": None,
            "idempotency_key": None,
            "verification": {"result": "passed"},
        },
    }


def test_specialized_schemas_accept_success_and_error_documents() -> None:
    capability_id = "partner.accounting.search"
    schema_dir = Path(__file__).parents[2] / "schemas" / "v1"
    assert (schema_dir / f"{capability_id}.request.schema.json").is_file()
    assert (schema_dir / f"{capability_id}.response.schema.json").is_file()
    data = {
        "items": [_row(10, "Alpha", company_id=None)],
        "has_more": False,
        "next_cursor": None,
    }
    registry = load_registry()
    registry.validate_instance(
        f"schemas/v1/{capability_id}.request.schema.json",
        _request(role="both", query=None, limit=100, cursor=None),
    )
    response = _success_response(data)
    registry.validate_instance(
        f"schemas/v1/{capability_id}.response.schema.json", response
    )
    response.update(
        success=False,
        status="failed_validation",
        data=None,
        error={
            "code": "failed_validation",
            "message": "The result failed validation.",
            "details": {},
            "retryable": False,
        },
    )
    registry.validate_instance(
        f"schemas/v1/{capability_id}.response.schema.json", response
    )
