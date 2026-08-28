from __future__ import annotations

import pytest

from odoo_accounting_cli_v4.bridge.bank_transactions import (
    OdooBankTransactionListPort,
)


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


def test_port_uses_only_the_fixed_bank_transaction_action_and_payload() -> None:
    client = Client(_page(rows=[{"id": 1}]))
    port = OdooBankTransactionListPort(client)

    result = port.search_page(
        company_id=7,
        after=["2025-01-25", 20],
        limit=101,
    )

    assert result["rows"] == [{"id": 1}]
    assert port.user_id == 5
    assert client.calls == [
        (
            "account.bank.statement.line.search_page",
            {
                "company_id": 7,
                "after": ["2025-01-25", 20],
                "limit": 101,
            },
        )
    ]


def test_user_id_is_not_reused_after_a_malformed_result() -> None:
    client = Client(_page(rows=[]))
    port = OdooBankTransactionListPort(client)
    port.search_page(company_id=7, after=None, limit=2)
    assert port.user_id == 5
    client.result = {}

    with pytest.raises(ValueError):
        port.search_page(company_id=7, after=None, limit=2)
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
        {**_page(rows=[]), "company_visible": 1},
        {**_page(rows=[]), "module_installed": 1},
        {**_page(rows=[]), "access_allowed": 1},
    ],
)
def test_port_rejects_malformed_bridge_results(result: object) -> None:
    port = OdooBankTransactionListPort(Client(result))
    with pytest.raises(ValueError):
        port.search_page(company_id=7, after=None, limit=2)
