from __future__ import annotations

import pytest

from odoo_accounting_cli_v4.bridge.partners import OdooPartnerAccountingPort


class Client:
    def __init__(self, result: object) -> None:
        self.result = result
        self.calls: list[tuple[str, dict]] = []

    def invoke(self, action: str, payload: dict) -> object:
        self.calls.append((action, payload))
        return self.result


def _page(**payload: object) -> dict:
    return {
        "user_id": 5,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        **payload,
    }


def test_search_uses_the_fixed_composite_action() -> None:
    client = Client(_page(rows=[{"id": 1}]))
    port = OdooPartnerAccountingPort(client)
    filters = {"role": "customer", "query": "Acme"}

    result = port.search_page(
        company_id=7,
        after=["Acme", 1],
        limit=101,
        filters=filters,
    )

    assert result["rows"] == [{"id": 1}]
    assert port.user_id == 5
    assert client.calls == [
        (
            "res.partner.accounting.search_page",
            {
                "company_id": 7,
                "after": ["Acme", 1],
                "limit": 101,
                "filters": filters,
            },
        )
    ]


def test_user_id_is_unavailable_before_a_verified_page() -> None:
    port = OdooPartnerAccountingPort(Client(_page(rows=[])))
    with pytest.raises(ValueError):
        _ = port.user_id


@pytest.mark.parametrize(
    "result",
    [
        None,
        {},
        _page(rows=None),
        _page(rows=[1]),
        {**_page(rows=[]), "extra": True},
        {**_page(rows=[]), "user_id": True},
        {**_page(rows=[]), "access_allowed": 1},
    ],
)
def test_port_rejects_malformed_bridge_results(result: object) -> None:
    port = OdooPartnerAccountingPort(Client(result))
    with pytest.raises(ValueError):
        port.search_page(company_id=7, after=None, limit=2, filters={})
