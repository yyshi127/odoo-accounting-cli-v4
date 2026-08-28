from __future__ import annotations

import pytest

from odoo_accounting_cli_v4.bridge.fiscal_position import (
    OdooFiscalPositionResolvePort,
)


class Client:
    def __init__(self, result: dict) -> None:
        self.result = result
        self.calls: list[tuple[str, dict]] = []

    def invoke(self, action: str, payload: dict) -> dict:
        self.calls.append((action, payload))
        return self.result


def _page(data: dict | None = None) -> dict:
    return {
        "user_id": 5,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "data": data,
    }


def test_port_uses_only_the_fixed_fiscal_position_action() -> None:
    page = _page({})
    client = Client(page)
    port = OdooFiscalPositionResolvePort(client)

    assert (
        port.resolve(
            company_id=7,
            partner_id=31,
            delivery_partner_id=32,
            account_id=401,
            tax_ids=[101, 102],
        )
        == page
    )
    assert port.user_id == 5
    assert client.calls == [
        (
            "account.fiscal.position.resolve",
            {
                "company_id": 7,
                "partner_id": 31,
                "delivery_partner_id": 32,
                "account_id": 401,
                "tax_ids": [101, 102],
            },
        )
    ]


@pytest.mark.parametrize(
    "page",
    [
        {},
        {**_page({}), "extra": True},
        {**_page({}), "user_id": True},
        {**_page({}), "company_visible": 1},
        {**_page({}), "module_installed": None},
        {**_page({}), "access_allowed": "yes"},
        {**_page({}), "data": []},
    ],
)
def test_port_rejects_malformed_bridge_pages(page: dict) -> None:
    port = OdooFiscalPositionResolvePort(Client(page))

    with pytest.raises(ValueError):
        port.resolve(
            company_id=7,
            partner_id=31,
            delivery_partner_id=None,
            account_id=None,
            tax_ids=None,
        )
