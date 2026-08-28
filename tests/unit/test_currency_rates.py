from __future__ import annotations

import base64
from copy import deepcopy
from pathlib import Path

import pytest

from odoo_accounting_cli_v4.capabilities.currency_rates import (
    CurrencyRateListError,
    list_currency_rates,
    validate_currency_rate_list_request,
)
from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry

REQUEST_ID = "123e4567-e89b-42d3-a456-426614174000"


def _request(**parameters) -> dict:
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "context": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_login": "cli.accounting",
            "language": "en_US",
            "timezone": "UTC",
        },
        "parameters": parameters,
    }


def _currency(currency_id: int, code: str) -> dict:
    return {"id": currency_id, "code": code}


def _row(rate_id: int, rate_date: str, *, source_company_id: int | None = 7) -> dict:
    return {
        "id": rate_id,
        "date": rate_date,
        "currency": _currency(2, "USD"),
        "company_currency": _currency(1, "CNY"),
        "requested_company_id": 7,
        "source_company_id": source_company_id,
        "technical_rate": "0.1406469760900141",
        "foreign_units_per_company_unit": "0.1406469760900141",
        "company_units_per_foreign_unit": "7.11",
    }


class FakePort:
    def __init__(
        self,
        *,
        rows: list[dict] | None = None,
        user_id: int = 42,
        company_visible: bool = True,
        module_installed: bool = True,
        access_allowed: bool | None = None,
        root_company_id: int | None = 7,
    ) -> None:
        self.rows = rows or []
        self._user_id = user_id
        self.company_visible = company_visible
        self.module_installed = module_installed
        self.access_allowed = (
            company_visible and module_installed
            if access_allowed is None
            else access_allowed
        )
        self.root_company_id = root_company_id
        self.calls: list[dict] = []

    @property
    def user_id(self) -> int:
        return self._user_id

    def read_page(self, **kwargs) -> dict:
        self.calls.append(kwargs)
        return {
            "user_id": self._user_id,
            "company_visible": self.company_visible,
            "module_installed": self.module_installed,
            "access_allowed": self.access_allowed,
            "root_company_id": self.root_company_id,
            "rows": self.rows,
        }


def test_closed_request_defaults_and_fixed_bridge_call() -> None:
    port = FakePort(rows=[_row(20, "2025-01-25")])

    result = list_currency_rates(port, _request())

    assert result == {
        "items": [_row(20, "2025-01-25")],
        "has_more": False,
        "next_cursor": None,
    }
    assert port.calls == [
        {
            "company_id": 7,
            "after": None,
            "limit": 101,
            "filters": {
                "date_from": None,
                "date_to": None,
                "currency_id": None,
            },
        }
    ]


def test_date_and_currency_filters_are_normalized_and_enforced() -> None:
    row = _row(20, "2025-01-25")
    port = FakePort(rows=[row])

    result = list_currency_rates(
        port,
        _request(
            date_from="2025-01-25",
            date_to="2025-01-25",
            currency_id=2,
            limit=1,
            cursor=None,
        ),
    )

    assert result["items"] == [row]
    assert port.calls[0]["filters"] == {
        "date_from": "2025-01-25",
        "date_to": "2025-01-25",
        "currency_id": 2,
    }

    for key, value in {
        "date_from": "2025-01-26",
        "date_to": "2025-01-24",
        "currency_id": 3,
    }.items():
        parameters = {
            "date_from": "2025-01-01",
            "date_to": "2025-01-31",
            "currency_id": 2,
        }
        parameters[key] = value
        with pytest.raises(CurrencyRateListError) as caught:
            list_currency_rates(FakePort(rows=[row]), _request(**parameters))
        assert caught.value.code == "failed_validation"
        assert caught.value.exit_code == 8


def test_keyset_is_date_descending_then_id_ascending() -> None:
    rows = [
        _row(20, "2025-01-25"),
        _row(21, "2025-01-25"),
        _row(10, "2025-01-24"),
    ]
    port = FakePort(rows=rows)

    first = list_currency_rates(port, _request(limit=2))

    assert first["items"] == rows[:2]
    assert first["has_more"] is True
    assert isinstance(first["next_cursor"], str)

    second_port = FakePort(rows=[rows[2]])
    second = list_currency_rates(
        second_port, _request(limit=2, cursor=first["next_cursor"])
    )
    assert second["items"] == [rows[2]]
    assert second_port.calls[0]["after"] == ["2025-01-25", 21]


@pytest.mark.parametrize(
    "rows",
    [
        [_row(21, "2025-01-25"), _row(20, "2025-01-25")],
        [_row(20, "2025-01-24"), _row(21, "2025-01-25")],
        [_row(20, "2025-01-25"), _row(20, "2025-01-24")],
    ],
)
def test_rows_must_be_unique_and_strictly_follow_fixed_order(rows: list[dict]) -> None:
    with pytest.raises(CurrencyRateListError) as caught:
        list_currency_rates(FakePort(rows=rows), _request())
    assert caught.value.code == "failed_validation"


def test_cursor_is_bound_to_database_company_user_and_all_filters() -> None:
    first = list_currency_rates(
        FakePort(rows=[_row(20, "2025-01-25"), _row(21, "2025-01-24")]),
        _request(limit=1, date_from="2025-01-01", currency_id=2),
    )
    cursor = first["next_cursor"]
    assert cursor

    mutations = [
        lambda request: request["context"].update(database="other"),
        lambda request: request["context"].update(company_id=8),
        lambda request: request["context"].update(user_login="other"),
        lambda request: request["parameters"].update(date_from="2025-01-02"),
        lambda request: request["parameters"].update(date_to="2025-01-31"),
        lambda request: request["parameters"].update(currency_id=3),
    ]
    for mutation in mutations:
        request = _request(
            limit=1,
            cursor=cursor,
            date_from="2025-01-01",
            currency_id=2,
        )
        mutation(request)
        with pytest.raises(CurrencyRateListError) as caught:
            list_currency_rates(FakePort(), request)
        assert caught.value.code == "invalid_cursor"
        assert caught.value.exit_code == 2


def test_cursor_decoder_rejects_duplicate_keys_and_json_numbers() -> None:
    cursor = base64.urlsafe_b64encode(
        b'{"after":["2025-01-25",20],"binding":"x","binding":"x","version":1}'
    ).decode("ascii").rstrip("=")
    with pytest.raises(CurrencyRateListError) as caught:
        list_currency_rates(FakePort(), _request(cursor=cursor))
    assert caught.value.code == "invalid_cursor"

    cursor = base64.urlsafe_b64encode(
        b'{"after":["2025-01-25",20.0],"binding":"x","version":1}'
    ).decode("ascii").rstrip("=")
    with pytest.raises(CurrencyRateListError) as caught:
        list_currency_rates(FakePort(), _request(cursor=cursor))
    assert caught.value.code == "invalid_cursor"


@pytest.mark.parametrize(
    "mutation",
    [
        lambda request: request.update(extra=True),
        lambda request: request.update(schema_version="v2"),
        lambda request: request.update(request_id="not-a-uuid"),
        lambda request: request["context"].update(extra=True),
        lambda request: request["context"].update(company_id=True),
        lambda request: request["context"].update(database=" "),
        lambda request: request["parameters"].update(extra=True),
        lambda request: request["parameters"].update(date_from="2025/01/01"),
        lambda request: request["parameters"].update(date_to="2025-02-30"),
        lambda request: request["parameters"].update(currency_id=True),
        lambda request: request["parameters"].update(currency_id=0),
        lambda request: request["parameters"].update(limit=0),
        lambda request: request["parameters"].update(cursor=""),
    ],
)
def test_schema_and_python_both_reject_invalid_requests(mutation) -> None:
    request = _request()
    mutation(request)
    with pytest.raises(InstanceValidationError):
        load_registry().validate_instance(
            "schemas/v1/currency.rate.list.request.schema.json", request
        )
    with pytest.raises(CurrencyRateListError) as caught:
        validate_currency_rate_list_request(request)
    assert caught.value.exit_code == 2


def test_python_contract_rejects_reversed_date_range() -> None:
    request = _request(date_from="2025-02-01", date_to="2025-01-01")
    with pytest.raises(CurrencyRateListError) as caught:
        validate_currency_rate_list_request(request)
    assert caught.value.code == "invalid_request"
    assert caught.value.exit_code == 2


@pytest.mark.parametrize(
    "mutation",
    [
        lambda row: row.update(extra=True),
        lambda row: row.update(id=True),
        lambda row: row.update(date="2025/01/25"),
        lambda row: row["currency"].update(id=0),
        lambda row: row["currency"].update(code="USDX"),
        lambda row: row["company_currency"].update(extra=True),
        lambda row: row.update(requested_company_id=8),
        lambda row: row.update(source_company_id=8),
        lambda row: row.update(technical_rate="0"),
        lambda row: row.update(technical_rate="01.0"),
        lambda row: row.update(foreign_units_per_company_unit="NaN"),
        lambda row: row.update(company_units_per_foreign_unit="1e2"),
        lambda row: row.update(company_units_per_foreign_unit="7.12"),
    ],
)
def test_invalid_rate_rows_never_become_verified(mutation) -> None:
    row = _row(20, "2025-01-25")
    mutation(row)
    with pytest.raises(CurrencyRateListError) as caught:
        list_currency_rates(FakePort(rows=[row]), _request())
    assert caught.value.code == "failed_validation"
    assert caught.value.exit_code == 8


def test_global_and_root_rate_sources_are_both_preserved() -> None:
    root_rate = _row(20, "2025-01-25", source_company_id=7)
    global_rate = _row(21, "2025-01-24", source_company_id=None)

    result = list_currency_rates(
        FakePort(rows=[root_rate, global_rate]), _request()
    )

    assert result["items"] == [root_rate, global_rate]


def test_legal_odoo_currency_char_values_are_preserved_without_iso_assumptions() -> None:
    row = _row(20, "2025-01-25")
    row["currency"]["code"] = " "
    row["company_currency"]["code"] = "\t"

    result = list_currency_rates(FakePort(rows=[row]), _request())

    assert result["items"] == [row]


def test_rate_currency_may_be_the_company_currency() -> None:
    row = _row(20, "2025-01-25")
    row["currency"] = deepcopy(row["company_currency"])
    row.update(
        technical_rate="1",
        foreign_units_per_company_unit="1",
        company_units_per_foreign_unit="1",
    )

    result = list_currency_rates(FakePort(rows=[row]), _request())

    assert result["items"] == [row]


def test_child_company_accepts_only_its_root_or_global_rate_source() -> None:
    root_rate = _row(20, "2025-01-25", source_company_id=7)
    root_rate["requested_company_id"] = 9
    request = _request()
    request["context"]["company_id"] = 9
    assert list_currency_rates(
        FakePort(rows=[root_rate], root_company_id=7), request
    )["items"] == [root_rate]

    root_rate["source_company_id"] = 9
    with pytest.raises(CurrencyRateListError) as caught:
        list_currency_rates(
            FakePort(rows=[root_rate], root_company_id=7), request
        )
    assert caught.value.code == "failed_validation"


def test_rate_directions_are_positive_reciprocals_not_balance_claims() -> None:
    row = _row(20, "2025-01-25")
    result = list_currency_rates(FakePort(rows=[row]), _request())["items"][0]

    assert result["technical_rate"] == "0.1406469760900141"
    assert result["foreign_units_per_company_unit"] == "0.1406469760900141"
    assert result["company_units_per_foreign_unit"] == "7.11"
    assert "balance" not in result
    assert "amount" not in result


def test_technical_rate_is_independent_from_the_two_business_directions() -> None:
    row = _row(20, "2025-01-25")
    row["technical_rate"] = "0.2812939521800282"

    result = list_currency_rates(FakePort(rows=[row]), _request())["items"][0]

    assert result["technical_rate"] != result["foreign_units_per_company_unit"]
    assert result == row


@pytest.mark.parametrize(
    ("port", "code"),
    [
        (
            FakePort(
                company_visible=False,
                access_allowed=True,
                root_company_id=None,
            ),
            "company_unavailable",
        ),
        (
            FakePort(
                company_visible=False,
                module_installed=False,
                access_allowed=False,
                root_company_id=None,
            ),
            "uninstalled",
        ),
        (
            FakePort(
                company_visible=False,
                access_allowed=False,
                root_company_id=None,
            ),
            "unauthorized",
        ),
    ],
)
def test_runtime_availability_failures_are_typed(port: FakePort, code: str) -> None:
    with pytest.raises(CurrencyRateListError) as caught:
        list_currency_rates(port, _request())
    assert caught.value.code == code


@pytest.mark.parametrize(
    ("port", "code"),
    [
        (
            FakePort(company_visible=False, access_allowed=False, root_company_id=None),
            "unauthorized",
        ),
        (
            FakePort(
                company_visible=False,
                access_allowed=False,
                root_company_id=None,
            ),
            "unauthorized",
        ),
    ],
)
def test_unavailable_pages_do_not_need_a_fabricated_root_company(
    port: FakePort, code: str
) -> None:
    with pytest.raises(CurrencyRateListError) as caught:
        list_currency_rates(port, _request())
    assert caught.value.code == code


def test_verified_page_requires_a_real_root_company() -> None:
    with pytest.raises(CurrencyRateListError) as caught:
        list_currency_rates(FakePort(root_company_id=None), _request())
    assert caught.value.code == "failed_validation"


def test_uninstalled_takes_precedence_over_company_and_access_to_avoid_probing() -> None:
    port = FakePort(
        company_visible=False,
        module_installed=False,
        access_allowed=False,
        root_company_id=None,
    )
    with pytest.raises(CurrencyRateListError) as caught:
        list_currency_rates(port, _request())
    assert caught.value.code == "uninstalled"


def test_unauthorized_takes_precedence_over_company_visibility() -> None:
    port = FakePort(
        company_visible=False,
        module_installed=True,
        access_allowed=False,
        root_company_id=None,
    )
    with pytest.raises(CurrencyRateListError) as caught:
        list_currency_rates(port, _request())
    assert caught.value.code == "unauthorized"


@pytest.mark.parametrize(
    "port",
    [
        FakePort(
            company_visible=False,
            module_installed=False,
            access_allowed=True,
            root_company_id=None,
        ),
        FakePort(
            company_visible=True,
            module_installed=True,
            access_allowed=False,
            root_company_id=None,
        ),
        FakePort(
            company_visible=True,
            module_installed=False,
            access_allowed=False,
            root_company_id=None,
        ),
    ],
)
def test_availability_booleans_must_follow_the_frozen_implication_chain(
    port: FakePort,
) -> None:
    with pytest.raises(CurrencyRateListError) as caught:
        list_currency_rates(port, _request())
    assert caught.value.code == "failed_validation"


def test_malformed_or_contradictory_pages_are_failed_validation() -> None:
    with pytest.raises(CurrencyRateListError) as caught:
        list_currency_rates(
            FakePort(company_visible=False, access_allowed=True), _request()
        )
    assert caught.value.code == "failed_validation"

    class Broken(FakePort):
        def read_page(self, **kwargs) -> dict:
            raise ValueError("bad page")

    with pytest.raises(CurrencyRateListError) as caught:
        list_currency_rates(Broken(), _request())
    assert caught.value.code == "failed_validation"
    assert caught.value.exit_code == 8


def _success_response(data: dict) -> dict:
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "success": True,
        "capability": "currency.rate.list",
        "status": "verified",
        "data": data,
        "warnings": [],
        "error": None,
        "odoo": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_id": 42,
            "model": "res.currency.rate",
            "record_ids": [item["id"] for item in data["items"]],
        },
        "audit": {
            "operation_id": None,
            "idempotency_key": None,
            "verification": {"result": "passed"},
        },
    }


def test_specialized_closed_schemas_accept_success_and_error_documents() -> None:
    schema_dir = Path(__file__).parents[2] / "schemas" / "v1"
    capability = "currency.rate.list"
    assert (schema_dir / f"{capability}.request.schema.json").is_file()
    assert (schema_dir / f"{capability}.response.schema.json").is_file()
    registry = load_registry()
    registry.validate_instance(
        f"schemas/v1/{capability}.request.schema.json",
        _request(
            date_from=None,
            date_to=None,
            currency_id=None,
            limit=100,
            cursor=None,
        ),
    )
    response = _success_response(
        {"items": [_row(20, "2025-01-25")], "has_more": False, "next_cursor": None}
    )
    registry.validate_instance(f"schemas/v1/{capability}.response.schema.json", response)

    error_response = deepcopy(response)
    error_response.update(
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
        f"schemas/v1/{capability}.response.schema.json", error_response
    )


def test_schema_and_python_reject_decimal_with_trailing_newline() -> None:
    row = _row(20, "2025-01-25")
    row["technical_rate"] += "\n"
    response = _success_response(
        {"items": [row], "has_more": False, "next_cursor": None}
    )
    with pytest.raises(InstanceValidationError):
        load_registry().validate_instance(
            "schemas/v1/currency.rate.list.response.schema.json", response
        )
    with pytest.raises(CurrencyRateListError):
        list_currency_rates(FakePort(rows=[row]), _request())
