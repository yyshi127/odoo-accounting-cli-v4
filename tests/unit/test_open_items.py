from __future__ import annotations

import base64
import copy
from pathlib import Path

import pytest

from odoo_accounting_cli_v4.capabilities.open_items import (
    OpenItemsError,
    search_payable_open_items,
    search_receivable_open_items,
    validate_payable_open_items_list_request,
    validate_receivable_open_items_list_request,
)
from odoo_accounting_cli_v4.registry import load_registry
from odoo_accounting_cli_v4.registry import InstanceValidationError


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


def _currency(record_id: int, code: str) -> dict:
    return {"id": record_id, "code": code}


def _row(
    record_id: int,
    item_date: str,
    *,
    side: str = "receivable",
    due_date: str | None = "2025-02-20",
) -> dict:
    account_type = "asset_receivable" if side == "receivable" else "liability_payable"
    debit = "113" if side == "receivable" else "0"
    credit = "0" if side == "receivable" else "113"
    balance = "113" if side == "receivable" else "-113"
    residual = "63" if side == "receivable" else "-113"
    return {
        "id": record_id,
        "side": side,
        "date": item_date,
        "due_date": due_date,
        "name": f"Open item {record_id}",
        "ref": f"MOVE-REF-{record_id}",
        "move": {
            "id": 1000 + record_id,
            "name": f"INV/2025/{record_id:05d}",
            "move_type": "out_invoice" if side == "receivable" else "in_invoice",
            "state": "posted",
        },
        "journal": {"id": 9, "code": "INV", "name": "Sales"},
        "company_id": 7,
        "partner": {
            "id": 16,
            "name": "Fixture Partner",
            "reference": "PARTNER-16",
        },
        "account": {
            "id": 55,
            "code": "112100",
            "name": "Trade Receivable",
            "account_type": account_type,
            "non_trade": False,
        },
        "currency": _currency(6, "CNY"),
        "company_currency": _currency(6, "CNY"),
        "debit": debit,
        "credit": credit,
        "balance": balance,
        "amount_currency": balance,
        "amount_residual": residual,
        "amount_residual_currency": residual,
        "reconciled": False,
        "matching_number": "P1" if side == "receivable" else None,
    }


EMPTY_FILTERS = {
    "date_from": None,
    "date_to": None,
    "due_date_from": None,
    "due_date_to": None,
    "partner_id": None,
    "account_id": None,
    "journal_id": None,
    "currency_id": None,
    "query": None,
}


@pytest.mark.parametrize(
    ("search", "side"),
    [
        (search_receivable_open_items, "receivable"),
        (search_payable_open_items, "payable"),
    ],
)
def test_search_defaults_and_uses_one_company_scoped_page(search, side: str) -> None:
    row = _row(10, "2025-01-20", side=side)
    port = FakePort(rows=[row])

    result = search(port, _request())

    assert result == {"items": [row], "has_more": False, "next_cursor": None}
    assert port.search_calls == [
        {
            "company_id": 7,
            "after": None,
            "limit": 101,
            "filters": EMPTY_FILTERS,
        }
    ]


def test_search_paginates_in_date_then_id_descending_order() -> None:
    rows = [
        _row(12, "2025-01-22"),
        _row(11, "2025-01-21"),
        _row(10, "2025-01-21"),
    ]
    first = search_receivable_open_items(FakePort(rows=rows), _request(limit=2))

    assert [item["id"] for item in first["items"]] == [12, 11]
    assert first["has_more"] is True
    assert isinstance(first["next_cursor"], str)

    port = FakePort(rows=[rows[-1]])
    second = search_receivable_open_items(
        port, _request(limit=2, cursor=first["next_cursor"])
    )
    assert second["items"] == [rows[-1]]
    assert port.search_calls[0]["after"] == ["2025-01-21", 11]


def test_cursor_is_bound_to_capability_context_and_normalized_filters() -> None:
    parameters = {
        "limit": 1,
        "date_from": "2025-01-01",
        "date_to": "2025-01-31",
        "due_date_from": "2025-02-01",
        "due_date_to": "2025-02-28",
        "partner_id": 16,
        "account_id": 55,
        "journal_id": 9,
        "currency_id": 6,
        "query": "Fixture",
    }
    first = search_receivable_open_items(
        FakePort(rows=[_row(12, "2025-01-22"), _row(11, "2025-01-21")]),
        _request(**parameters),
    )
    assert first["next_cursor"]

    mutations = [
        ("context", "database", "other-db"),
        ("context", "company_id", 8),
        ("context", "user_login", "other-user"),
        ("parameters", "date_from", "2025-01-02"),
        ("parameters", "partner_id", 17),
        ("parameters", "query", "Other"),
    ]
    for section, key, value in mutations:
        request = _request(**parameters, cursor=first["next_cursor"])
        request[section][key] = value
        port = FakePort()
        with pytest.raises(OpenItemsError) as caught:
            search_receivable_open_items(port, request)
        assert caught.value.code == "invalid_cursor"
        assert caught.value.exit_code == 2
        assert port.search_calls == []

    port = FakePort()
    with pytest.raises(OpenItemsError) as caught:
        search_payable_open_items(
            port, _request(**parameters, cursor=first["next_cursor"])
        )
    assert caught.value.code == "invalid_cursor"
    assert port.search_calls == []


def test_cursor_is_bounded_even_for_long_valid_context_values() -> None:
    request = _request(limit=1)
    request["context"]["database"] = "d" * 3500
    request["context"]["user_login"] = "u" * 3500
    first = search_receivable_open_items(
        FakePort(rows=[_row(12, "2025-01-22"), _row(11, "2025-01-21")]),
        request,
    )

    assert first["next_cursor"] is not None
    assert len(first["next_cursor"]) <= 4096

    replay = copy.deepcopy(request)
    replay["parameters"]["cursor"] = first["next_cursor"]
    replay["parameters"]["limit"] = 1
    port = FakePort(rows=[_row(10, "2025-01-20")])
    search_receivable_open_items(port, replay)
    assert port.search_calls[0]["after"] == ["2025-01-22", 12]


@pytest.mark.parametrize(
    "mutate",
    [
        lambda raw: raw.replace('"version":1', '"version":1,"version":1'),
        lambda raw: raw.replace('"version":1', '"version":1.0'),
        lambda raw: raw.replace('"version":1', '"version":NaN'),
    ],
)
def test_cursor_rejects_duplicate_keys_floats_and_nonfinite_numbers(mutate) -> None:
    first = search_receivable_open_items(
        FakePort(rows=[_row(12, "2025-01-22"), _row(11, "2025-01-21")]),
        _request(limit=1),
    )
    raw = base64.urlsafe_b64decode(first["next_cursor"] + "==").decode("utf-8")
    forged = base64.urlsafe_b64encode(mutate(raw).encode()).decode().rstrip("=")
    port = FakePort()

    with pytest.raises(OpenItemsError) as caught:
        search_receivable_open_items(port, _request(limit=1, cursor=forged))

    assert caught.value.code == "invalid_cursor"
    assert port.search_calls == []


@pytest.mark.parametrize(
    "parameters",
    [
        {"unexpected": True},
        {"date_from": "2025/01/01"},
        {"date_from": "2025-02-01", "date_to": "2025-01-01"},
        {"due_date_from": "2025-03-01", "due_date_to": "2025-02-01"},
        {"partner_id": True},
        {"account_id": 0},
        {"journal_id": 1.0},
        {"currency_id": -1},
        {"query": " untrimmed"},
        {"query": "x" * 201},
        {"limit": True},
        {"limit": 1001},
        {"cursor": ""},
    ],
)
def test_invalid_request_fails_before_the_port(parameters: dict) -> None:
    port = FakePort()
    with pytest.raises(OpenItemsError) as caught:
        search_receivable_open_items(port, _request(**parameters))
    assert caught.value.code == "invalid_request"
    assert caught.value.exit_code == 2
    assert port.search_calls == []


@pytest.mark.parametrize(
    "validator",
    [
        validate_receivable_open_items_list_request,
        validate_payable_open_items_list_request,
    ],
)
def test_validator_exposes_canonical_defaults(validator) -> None:
    request_id, context, filters, limit, cursor = validator(_request())
    assert request_id == _request()["request_id"]
    assert context["company_id"] == 7
    assert filters == EMPTY_FILTERS
    assert limit == 100
    assert cursor is None


@pytest.mark.parametrize(
    "mutation",
    [
        lambda row: row.update(extra=True),
        lambda row: row.update(id=True),
        lambda row: row.update(side="payable"),
        lambda row: row.update(company_id=8),
        lambda row: row.update(date="2025/01/20"),
        lambda row: row.update(due_date=False),
        lambda row: row.update(name=""),
        lambda row: row["move"].update(state="draft"),
        lambda row: row["journal"].update(id=True),
        lambda row: row["partner"].update(reference=""),
        lambda row: row["account"].update(account_type="liability_payable"),
        lambda row: row["account"].update(non_trade=0),
        lambda row: row["currency"].update(code="USDX"),
        lambda row: row.update(debit="112"),
        lambda row: row.update(amount_residual=63),
        lambda row: row.update(reconciled=True),
        lambda row: row.update(matching_number=""),
    ],
)
def test_invalid_or_out_of_scope_rows_never_become_verified(mutation) -> None:
    row = _row(10, "2025-01-20")
    mutation(row)
    with pytest.raises(OpenItemsError) as caught:
        search_receivable_open_items(FakePort(rows=[row]), _request())
    assert caught.value.code == "failed_validation"
    assert caught.value.exit_code == 8


def test_nullable_business_fields_and_non_trade_accounts_are_supported() -> None:
    row = _row(10, "2025-01-20", due_date=None)
    row.update(name=None, ref=None, partner=None, matching_number=None)
    row["account"]["non_trade"] = True

    result = search_receivable_open_items(FakePort(rows=[row]), _request())

    assert result["items"] == [row]


def test_legal_whitespace_text_and_partner_without_a_name_are_representable() -> None:
    row = _row(10, "2025-01-20")
    row.update(name="   ", ref="   ", matching_number="   ")
    row["move"]["name"] = "   "
    row["journal"].update(code="   ", name="   ")
    row["account"].update(code="   ", name="   ")
    row["currency"]["code"] = "   "
    row["company_currency"]["code"] = "   "
    row["partner"].update(name=None, reference="   ")

    result = search_receivable_open_items(FakePort(rows=[row]), _request())

    assert result["items"] == [row]


@pytest.mark.parametrize(
    "mutation",
    [
        lambda row: row.update(debit="10", credit="-10", balance="20"),
        lambda row: row.update(balance="113", amount_currency="-113"),
        lambda row: row.update(
            amount_residual="0", amount_residual_currency="0"
        ),
        lambda row: row["company_currency"].update(
            id=row["currency"]["id"], code="USD"
        ),
        lambda row: row.update(amount_currency="100"),
        lambda row: row.update(amount_residual_currency="50"),
    ],
)
def test_impossible_odoo_amount_and_currency_combinations_are_rejected(
    mutation,
) -> None:
    row = _row(10, "2025-01-20")
    mutation(row)

    with pytest.raises(OpenItemsError) as caught:
        search_receivable_open_items(FakePort(rows=[row]), _request())

    assert caught.value.code == "failed_validation"
    assert caught.value.exit_code == 8


@pytest.mark.parametrize(
    ("amount_residual", "amount_residual_currency"),
    [
        ("-1", "63"),
        ("114", "63"),
        ("63", "-1"),
        ("63", "114"),
    ],
)
def test_foreign_currency_residuals_must_stay_within_the_original_direction(
    amount_residual: str,
    amount_residual_currency: str,
) -> None:
    row = _row(10, "2025-01-20")
    row["company_currency"] = _currency(37, "SGD")
    row.update(
        amount_currency="113",
        amount_residual=amount_residual,
        amount_residual_currency=amount_residual_currency,
    )

    with pytest.raises(OpenItemsError) as caught:
        search_receivable_open_items(FakePort(rows=[row]), _request())

    assert caught.value.code == "failed_validation"
    assert caught.value.exit_code == 8


def test_foreign_currency_rounding_can_leave_only_a_foreign_residual() -> None:
    row = _row(10, "2025-01-20")
    row["company_currency"] = _currency(37, "SGD")
    row.update(
        amount_currency="113",
        amount_residual="0",
        amount_residual_currency="0.01",
    )

    assert search_receivable_open_items(FakePort(rows=[row]), _request())[
        "items"
    ] == [row]


def test_rows_must_match_every_normalized_filter() -> None:
    row = _row(10, "2025-01-20")
    valid = {
        "date_from": "2025-01-01",
        "date_to": "2025-01-31",
        "due_date_from": "2025-02-01",
        "due_date_to": "2025-02-28",
        "partner_id": 16,
        "account_id": 55,
        "journal_id": 9,
        "currency_id": 6,
        "query": "Fixture",
    }
    assert search_receivable_open_items(FakePort(rows=[row]), _request(**valid))["items"]

    mutations = {
        "date_from": "2025-01-21",
        "date_to": "2025-01-19",
        "due_date_from": "2025-02-21",
        "due_date_to": "2025-02-19",
        "partner_id": 17,
        "account_id": 56,
        "journal_id": 10,
        "currency_id": 7,
        "query": "No match",
    }
    for key, value in mutations.items():
        request_filters = dict(valid)
        request_filters[key] = value
        with pytest.raises(OpenItemsError) as caught:
            search_receivable_open_items(
                FakePort(rows=[row]), _request(**request_filters)
            )
        assert caught.value.code == "failed_validation"


@pytest.mark.parametrize(
    "rows",
    [
        [_row(10, "2025-01-20"), _row(11, "2025-01-21")],
        [_row(10, "2025-01-20"), _row(11, "2025-01-20")],
        [_row(10, "2025-01-20"), _row(10, "2025-01-19")],
    ],
)
def test_search_requires_unique_descending_date_id_keys(rows: list[dict]) -> None:
    with pytest.raises(OpenItemsError) as caught:
        search_receivable_open_items(FakePort(rows=rows), _request())
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
    with pytest.raises(OpenItemsError) as caught:
        search_receivable_open_items(port, _request())
    assert caught.value.code == code


def test_contradictory_or_wrong_user_page_is_rejected() -> None:
    with pytest.raises(OpenItemsError) as caught:
        search_receivable_open_items(
            FakePort(company_visible=False, access_allowed=True), _request()
        )
    assert caught.value.code == "failed_validation"


def test_malformed_bridge_page_is_mapped_to_failed_validation() -> None:
    class MalformedBridgePort(FakePort):
        def search_page(self, **kwargs) -> dict:
            raise ValueError("malformed bridge page")

    with pytest.raises(OpenItemsError) as caught:
        search_receivable_open_items(MalformedBridgePort(), _request())

    assert caught.value.code == "failed_validation"
    assert caught.value.exit_code == 8

    class WrongUserPort(FakePort):
        def search_page(self, **kwargs) -> dict:
            page = super().search_page(**kwargs)
            page["user_id"] = self.user_id + 1
            return page

    with pytest.raises(OpenItemsError) as caught:
        search_receivable_open_items(WrongUserPort(), _request())
    assert caught.value.code == "failed_validation"


def _success_response(capability_id: str, data: dict) -> dict:
    return {
        "schema_version": "v1",
        "request_id": _request()["request_id"],
        "success": True,
        "capability": capability_id,
        "status": "verified",
        "data": data,
        "warnings": [],
        "error": None,
        "odoo": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_id": 42,
            "model": "account.move.line",
            "record_ids": [item["id"] for item in data["items"]],
        },
        "audit": {
            "operation_id": None,
            "idempotency_key": None,
            "verification": {"result": "passed"},
        },
    }


@pytest.mark.parametrize(
    ("capability_id", "side"),
    [
        ("receivable.open_items.list", "receivable"),
        ("payable.open_items.list", "payable"),
    ],
)
def test_specialized_schemas_accept_success_and_error_documents(
    capability_id: str, side: str
) -> None:
    schema_dir = Path(__file__).parents[2] / "schemas" / "v1"
    assert (schema_dir / f"{capability_id}.request.schema.json").is_file()
    assert (schema_dir / f"{capability_id}.response.schema.json").is_file()
    registry = load_registry()
    registry.validate_instance(
        f"schemas/v1/{capability_id}.request.schema.json",
        _request(**EMPTY_FILTERS, limit=100, cursor=None),
    )
    data = {
        "items": [_row(10, "2025-01-20", side=side)],
        "has_more": False,
        "next_cursor": None,
    }
    response = _success_response(capability_id, data)
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


@pytest.mark.parametrize(
    "capability_id",
    ["receivable.open_items.list", "payable.open_items.list"],
)
def test_request_schema_and_python_both_reject_trailing_whitespace_query(
    capability_id: str,
) -> None:
    registry = load_registry()
    request = _request(query="x\n")
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(
            f"schemas/v1/{capability_id}.request.schema.json", request
        )

    validator = (
        validate_receivable_open_items_list_request
        if capability_id == "receivable.open_items.list"
        else validate_payable_open_items_list_request
    )
    with pytest.raises(OpenItemsError):
        validator(request)


@pytest.mark.parametrize(
    ("capability_id", "search"),
    [
        ("receivable.open_items.list", search_receivable_open_items),
        ("payable.open_items.list", search_payable_open_items),
    ],
)
def test_response_schema_and_python_both_reject_decimal_with_trailing_newline(
    capability_id: str,
    search,
) -> None:
    side = "receivable" if capability_id.startswith("receivable") else "payable"
    row = _row(10, "2025-01-20", side=side)
    row["debit"] += "\n"
    response = _success_response(
        capability_id,
        {"items": [row], "has_more": False, "next_cursor": None},
    )

    with pytest.raises(InstanceValidationError):
        load_registry().validate_instance(
            f"schemas/v1/{capability_id}.response.schema.json", response
        )
    with pytest.raises(OpenItemsError) as caught:
        search(FakePort(rows=[row]), _request())
    assert caught.value.code == "failed_validation"
