from __future__ import annotations

import pytest

from odoo_accounting_cli_v4.bridge.payments import OdooPaymentPort


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
        **payload,
    }


def test_search_uses_only_the_fixed_payment_action() -> None:
    client = Client(_page(rows=[{"id": 1}]))
    port = OdooPaymentPort(client)
    filters = {
        "date_from": None,
        "date_to": None,
        "states": ["paid"],
        "payment_types": ["inbound"],
        "partner_types": ["customer"],
        "journal_id": None,
        "partner_id": None,
        "currency_id": None,
        "query": None,
    }

    result = port.search_page(
        company_id=7,
        after=["2025-01-25", 20],
        limit=101,
        filters=filters,
    )

    assert result["rows"] == [{"id": 1}]
    assert port.user_id == 5
    assert client.calls == [
        (
            "account.payment.search_page",
            {
                "company_id": 7,
                "after": ["2025-01-25", 20],
                "limit": 101,
                "filters": filters,
            },
        )
    ]


def test_get_uses_only_the_fixed_payment_action_and_accepts_not_found() -> None:
    client = Client(_page(payment=None))
    port = OdooPaymentPort(client)

    result = port.get_payment(company_id=7, payment_id=30)

    assert result["payment"] is None
    assert port.user_id == 5
    assert client.calls == [
        ("account.payment.get", {"company_id": 7, "payment_id": 30})
    ]


def test_user_id_is_not_reused_after_a_malformed_result() -> None:
    client = Client(_page(rows=[]))
    port = OdooPaymentPort(client)
    port.search_page(company_id=7, after=None, limit=2, filters={})
    assert port.user_id == 5
    client.result = {}

    with pytest.raises(ValueError):
        port.search_page(company_id=7, after=None, limit=2, filters={})
    with pytest.raises(ValueError):
        _ = port.user_id


@pytest.mark.parametrize(
    "result",
    [
        {},
        _page(rows=None),
        _page(rows=[None]),
        _page(payment=[]),
        {**_page(rows=[]), "extra": True},
        {**_page(rows=[]), "user_id": True},
        {**_page(rows=[]), "access_allowed": 1},
    ],
)
def test_port_rejects_malformed_bridge_results(result: dict) -> None:
    port = OdooPaymentPort(Client(result))

    with pytest.raises(ValueError):
        if "payment" in result:
            port.get_payment(company_id=7, payment_id=30)
        else:
            port.search_page(company_id=7, after=None, limit=2, filters={})
