from __future__ import annotations

import pytest

from odoo_accounting_cli_v4.bridge.currency_rates import OdooCurrencyRateListPort


class Client:
    def __init__(self, result: dict) -> None:
        self.result = result
        self.calls: list[tuple[str, dict]] = []

    def invoke(self, action: str, payload: dict) -> dict:
        self.calls.append((action, payload))
        return self.result


def _page(**payload) -> dict:
    return {
        "user_id": 5,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "root_company_id": 7,
        **payload,
    }


def test_port_uses_only_the_fixed_currency_rate_action_and_payload() -> None:
    client = Client(_page(rows=[{"id": 1}]))
    port = OdooCurrencyRateListPort(client)
    filters = {
        "date_from": "2025-01-01",
        "date_to": "2025-01-31",
        "currency_id": 2,
    }

    result = port.read_page(
        company_id=7,
        after=["2025-01-25", 20],
        limit=101,
        filters=filters,
    )

    assert result["rows"] == [{"id": 1}]
    assert result["root_company_id"] == 7
    assert port.user_id == 5
    assert client.calls == [
        (
            "res.currency.rate.read_page",
            {
                "company_id": 7,
                "after": ["2025-01-25", 20],
                "limit": 101,
                "filters": filters,
            },
        )
    ]


def test_user_id_is_not_reused_after_a_malformed_result() -> None:
    client = Client(_page(rows=[]))
    port = OdooCurrencyRateListPort(client)
    port.read_page(company_id=7, after=None, limit=2, filters={})
    assert port.user_id == 5
    client.result = {}

    with pytest.raises(ValueError):
        port.read_page(company_id=7, after=None, limit=2, filters={})
    with pytest.raises(ValueError):
        _ = port.user_id


def test_unavailable_page_may_preserve_an_unknown_root_company() -> None:
    client = Client(
        _page(
            company_visible=False,
            access_allowed=False,
            root_company_id=None,
            rows=[],
        )
    )
    port = OdooCurrencyRateListPort(client)

    page = port.read_page(company_id=7, after=None, limit=2, filters={})

    assert page["root_company_id"] is None
    assert port.user_id == 5


@pytest.mark.parametrize(
    "result",
    [
        {},
        _page(rows=None),
        _page(rows=[None]),
        {**_page(rows=[]), "extra": True},
        {**_page(rows=[]), "user_id": True},
        {**_page(rows=[]), "company_visible": 1},
        {**_page(rows=[]), "module_installed": 1},
        {**_page(rows=[]), "access_allowed": 1},
        {**_page(rows=[]), "root_company_id": True},
        {**_page(rows=[]), "root_company_id": 0},
    ],
)
def test_port_rejects_malformed_bridge_results(result: dict) -> None:
    port = OdooCurrencyRateListPort(Client(result))

    with pytest.raises(ValueError):
        port.read_page(company_id=7, after=None, limit=2, filters={})
