from __future__ import annotations

import pytest

from odoo_accounting_cli_v4.bridge.currency_rates import OdooCurrencyConvertPort


class Client:
    def __init__(self, result: dict) -> None:
        self.result = result
        self.calls: list[tuple[str, dict]] = []

    def invoke(self, action: str, payload: dict) -> dict:
        self.calls.append((action, payload))
        return self.result


def _page(**values) -> dict:
    result = {
        "user_id": 5,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "conversion": {
            "company_id": 7,
            "date": "2025-01-31",
            "amount": "125.50",
            "converted_amount": "892.31",
            "from_currency": {"id": 2, "code": "USD"},
            "to_currency": {"id": 1, "code": "CNY"},
        },
    }
    result.update(values)
    return result


def test_port_uses_only_the_fixed_currency_convert_action_and_payload() -> None:
    client = Client(_page())
    port = OdooCurrencyConvertPort(client)

    result = port.convert(
        company_id=7,
        amount="125.50",
        from_currency_id=2,
        to_currency_id=1,
        conversion_date="2025-01-31",
    )

    assert result == _page()
    assert port.user_id == 5
    assert client.calls == [
        (
            "res.currency.convert",
            {
                "company_id": 7,
                "amount": "125.50",
                "from_currency_id": 2,
                "to_currency_id": 1,
                "date": "2025-01-31",
            },
        )
    ]


def test_port_accepts_null_conversion_for_an_unavailable_or_missing_record() -> None:
    port = OdooCurrencyConvertPort(Client(_page(conversion=None)))

    page = port.convert(
        company_id=7,
        amount="1",
        from_currency_id=2,
        to_currency_id=1,
        conversion_date="2025-01-31",
    )

    assert page["conversion"] is None
    assert port.user_id == 5


@pytest.mark.parametrize(
    "result",
    [
        {},
        _page(conversion=[]),
        {**_page(), "extra": True},
        {**_page(), "user_id": True},
        {**_page(), "company_visible": 1},
        {**_page(), "module_installed": 1},
        {**_page(), "access_allowed": 1},
    ],
)
def test_port_rejects_malformed_results_and_clears_user_identity(result: dict) -> None:
    client = Client(_page())
    port = OdooCurrencyConvertPort(client)
    port.convert(
        company_id=7,
        amount="1",
        from_currency_id=2,
        to_currency_id=1,
        conversion_date="2025-01-31",
    )
    client.result = result

    with pytest.raises(ValueError):
        port.convert(
            company_id=7,
            amount="1",
            from_currency_id=2,
            to_currency_id=1,
            conversion_date="2025-01-31",
        )
    with pytest.raises(ValueError):
        _ = port.user_id
