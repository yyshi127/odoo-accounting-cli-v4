from __future__ import annotations

import pytest

from odoo_accounting_cli_v4.bridge.open_items import OdooOpenItemsPort


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


@pytest.mark.parametrize(
    ("capability_id", "action"),
    [
        (
            "receivable.open_items.list",
            "account.move.line.receivable.open_items.search_page",
        ),
        (
            "payable.open_items.list",
            "account.move.line.payable.open_items.search_page",
        ),
    ],
)
def test_search_uses_the_capability_bound_fixed_action(
    capability_id: str, action: str
) -> None:
    client = Client(_page(rows=[{"id": 1}]))
    port = OdooOpenItemsPort(client, capability_id)
    filters = {"partner_id": 16}

    result = port.search_page(
        company_id=7,
        after=["2025-01-20", 1],
        limit=101,
        filters=filters,
    )

    assert result["rows"] == [{"id": 1}]
    assert port.user_id == 5
    assert client.calls == [
        (
            action,
            {
                "company_id": 7,
                "after": ["2025-01-20", 1],
                "limit": 101,
                "filters": filters,
            },
        )
    ]


def test_constructor_rejects_any_unmapped_capability() -> None:
    with pytest.raises(ValueError):
        OdooOpenItemsPort(Client(_page(rows=[])), "invoice.search")


def test_user_id_is_unavailable_before_a_verified_page() -> None:
    port = OdooOpenItemsPort(
        Client(_page(rows=[])), "receivable.open_items.list"
    )
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
    port = OdooOpenItemsPort(
        Client(result), "receivable.open_items.list"
    )
    with pytest.raises(ValueError):
        port.search_page(company_id=7, after=None, limit=2, filters={})
