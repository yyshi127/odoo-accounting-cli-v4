from __future__ import annotations

import pytest

from odoo_accounting_cli_v4.bridge.invoices import OdooInvoicePort


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


def test_search_uses_the_fixed_composite_action() -> None:
    client = Client(_page(rows=[{"id": 1}]))
    port = OdooInvoicePort(client)
    filters = {
        "date_from": None,
        "date_to": None,
        "document_types": ["out_invoice"],
        "states": ["posted"],
        "payment_states": ["partial"],
        "journal_id": None,
        "partner_id": 9,
        "query": None,
    }

    result = port.search_page(
        company_id=7,
        after=["2025-01-15", 2],
        limit=101,
        filters=filters,
    )

    assert result["rows"] == [{"id": 1}]
    assert port.user_id == 5
    assert client.calls == [
        (
            "account.move.invoice.search_page",
            {
                "company_id": 7,
                "after": ["2025-01-15", 2],
                "limit": 101,
                "filters": filters,
            },
        )
    ]


def test_get_and_payment_status_use_fixed_actions() -> None:
    get_client = Client(_page(invoice=None))
    get_port = OdooInvoicePort(get_client)
    assert get_port.get_invoice(company_id=7, invoice_id=30)["invoice"] is None
    assert get_client.calls == [
        ("account.move.invoice.get", {"company_id": 7, "move_id": 30})
    ]

    status_client = Client(_page(payment_status=None))
    status_port = OdooInvoicePort(status_client)
    assert (
        status_port.inspect_payment_status(company_id=7, invoice_id=30)[
            "payment_status"
        ]
        is None
    )
    assert status_client.calls == [
        (
            "account.move.invoice.payment_status.inspect",
            {"company_id": 7, "move_id": 30},
        )
    ]


@pytest.mark.parametrize(
    ("result", "operation"),
    [
        ({}, "search"),
        (_page(rows=None), "search"),
        (_page(invoice=[]), "get"),
        (_page(payment_status=[]), "status"),
        ({**_page(rows=[]), "extra": True}, "search"),
        ({**_page(rows=[]), "user_id": True}, "search"),
    ],
)
def test_port_rejects_malformed_bridge_results(result: dict, operation: str) -> None:
    port = OdooInvoicePort(Client(result))

    with pytest.raises(ValueError):
        if operation == "search":
            port.search_page(company_id=7, after=None, limit=2, filters={})
        elif operation == "get":
            port.get_invoice(company_id=7, invoice_id=30)
        else:
            port.inspect_payment_status(company_id=7, invoice_id=30)
