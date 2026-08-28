from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from odoo_accounting_cli_v4.capabilities.currency_rates import (
    CurrencyConversionError,
    convert_currency,
    validate_currency_convert_request,
)
from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry

REQUEST_ID = "123e4567-e89b-42d3-a456-426614174000"
_DEFAULT_CONVERSION = object()


def _request(**parameters) -> dict:
    defaults = {
        "amount": "125.50",
        "from_currency_id": 2,
        "to_currency_id": 1,
        "date": "2025-01-31",
    }
    defaults.update(parameters)
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
        "parameters": defaults,
    }


def _currency(currency_id: int, code: str) -> dict:
    return {"id": currency_id, "code": code}


def _conversion(**values) -> dict:
    result = {
        "company_id": 7,
        "date": "2025-01-31",
        "amount": "125.50",
        "converted_amount": "892.31",
        "from_currency": _currency(2, "USD"),
        "to_currency": _currency(1, "CNY"),
    }
    result.update(values)
    return result


class FakePort:
    def __init__(
        self,
        *,
        conversion: dict | None | object = _DEFAULT_CONVERSION,
        user_id: int = 42,
        company_visible: bool = True,
        module_installed: bool = True,
        access_allowed: bool = True,
    ) -> None:
        self.conversion = (
            _conversion() if conversion is _DEFAULT_CONVERSION else conversion
        )
        self._user_id = user_id
        self.company_visible = company_visible
        self.module_installed = module_installed
        self.access_allowed = access_allowed
        self.calls: list[dict] = []

    @property
    def user_id(self) -> int:
        return self._user_id

    def convert(self, **payload) -> dict:
        self.calls.append(payload)
        return {
            "user_id": self._user_id,
            "company_visible": self.company_visible,
            "module_installed": self.module_installed,
            "access_allowed": self.access_allowed,
            "conversion": self.conversion,
        }


def test_convert_currency_calls_one_fixed_port_operation_and_returns_verified_data() -> None:
    port = FakePort()

    result = convert_currency(port, _request())

    assert result == _conversion()
    assert port.calls == [
        {
            "company_id": 7,
            "amount": "125.50",
            "from_currency_id": 2,
            "to_currency_id": 1,
            "conversion_date": "2025-01-31",
        }
    ]


@pytest.mark.parametrize("amount", ["0", "-0", "-12.50", "0.0001"])
def test_zero_and_negative_accounting_amounts_are_supported(amount: str) -> None:
    conversion = _conversion(amount=amount, converted_amount=amount)

    assert convert_currency(FakePort(conversion=conversion), _request(amount=amount)) == conversion


@pytest.mark.parametrize(
    "mutation",
    [
        lambda request: request["parameters"].update(extra=True),
        lambda request: request["parameters"].update(amount=1),
        lambda request: request["parameters"].update(amount=True),
        lambda request: request["parameters"].update(amount=""),
        lambda request: request["parameters"].update(amount=" 1"),
        lambda request: request["parameters"].update(amount="01"),
        lambda request: request["parameters"].update(amount="1e2"),
        lambda request: request["parameters"].update(amount="NaN"),
        lambda request: request["parameters"].update(amount="1\n"),
        lambda request: request["parameters"].update(from_currency_id=True),
        lambda request: request["parameters"].update(from_currency_id=0),
        lambda request: request["parameters"].update(to_currency_id=-1),
        lambda request: request["parameters"].update(date="2025/01/31"),
        lambda request: request["parameters"].pop("date"),
    ],
)
def test_currency_convert_request_is_closed_and_decimal_safe(mutation) -> None:
    request = _request()
    mutation(request)

    with pytest.raises(CurrencyConversionError) as caught:
        validate_currency_convert_request(request)

    assert caught.value.code == "invalid_request"
    assert caught.value.exit_code == 2


def test_same_currency_conversion_is_allowed_and_still_verified_by_odoo() -> None:
    conversion = _conversion(
        converted_amount="125.5",
        to_currency=_currency(2, "USD"),
    )

    result = convert_currency(
        FakePort(conversion=conversion),
        _request(to_currency_id=2),
    )

    assert result == conversion


@pytest.mark.parametrize(
    ("port", "code"),
    [
        (
            FakePort(
                conversion=None,
                company_visible=False,
                module_installed=False,
                access_allowed=False,
            ),
            "uninstalled",
        ),
        (
            FakePort(
                conversion=None,
                company_visible=False,
                access_allowed=False,
            ),
            "unauthorized",
        ),
        (
            FakePort(
                conversion=None,
                company_visible=False,
                access_allowed=True,
            ),
            "failed_validation",
        ),
        (FakePort(conversion=None), "record_not_found"),
    ],
)
def test_currency_convert_failures_are_typed(port: FakePort, code: str) -> None:
    with pytest.raises(CurrencyConversionError) as caught:
        convert_currency(port, _request())

    assert caught.value.code == code


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value.update(extra=True),
        lambda value: value.update(company_id=8),
        lambda value: value.update(date="2025-02-01"),
        lambda value: value.update(amount="125.5"),
        lambda value: value.update(converted_amount="NaN"),
        lambda value: value["from_currency"].update(id=3),
        lambda value: value["to_currency"].update(code="USDX"),
    ],
)
def test_mismatched_or_malformed_conversion_never_becomes_verified(mutation) -> None:
    conversion = _conversion()
    mutation(conversion)

    with pytest.raises(CurrencyConversionError) as caught:
        convert_currency(FakePort(conversion=conversion), _request())

    assert caught.value.code == "failed_validation"
    assert caught.value.exit_code == 8


def test_bridge_value_error_becomes_failed_validation() -> None:
    class BrokenPort(FakePort):
        def convert(self, **payload) -> dict:
            raise ValueError("malformed bridge result")

    with pytest.raises(CurrencyConversionError) as caught:
        convert_currency(BrokenPort(), _request())

    assert caught.value.code == "failed_validation"


def _success_response(data: dict) -> dict:
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "success": True,
        "capability": "currency.convert",
        "status": "verified",
        "data": data,
        "warnings": [],
        "error": None,
        "odoo": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_id": 42,
            "model": "res.currency",
            "record_ids": [2, 1],
        },
        "audit": {
            "operation_id": None,
            "idempotency_key": None,
            "verification": {"result": "passed"},
        },
    }


def test_specialized_schemas_accept_success_and_error_documents() -> None:
    schema_dir = Path(__file__).parents[2] / "schemas" / "v1"
    capability = "currency.convert"
    assert (schema_dir / f"{capability}.request.schema.json").is_file()
    assert (schema_dir / f"{capability}.response.schema.json").is_file()
    registry = load_registry()
    registry.validate_instance(
        f"schemas/v1/{capability}.request.schema.json", _request()
    )
    response = _success_response(_conversion())
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


def test_schema_rejects_noncanonical_amount_and_mismatched_success_shape() -> None:
    registry = load_registry()
    request = _request(amount="1e2")
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(
            "schemas/v1/currency.convert.request.schema.json", request
        )

    response = _success_response(_conversion())
    response["data"]["converted_amount"] = "1\n"
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(
            "schemas/v1/currency.convert.response.schema.json", response
        )
