from __future__ import annotations

import pytest

from odoo_accounting_cli_v4.bridge.order_documents import (
    ACTION,
    OdooOrderDocumentsPort,
)


def _page() -> dict:
    return {
        "user_id": 5,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "cursor_found": True,
        "items": [],
    }


class Client:
    def __init__(self, page: dict) -> None:
        self.page = page
        self.calls: list[tuple[str, dict]] = []

    def invoke(self, action: str, payload: dict) -> dict:
        self.calls.append((action, payload))
        return self.page


@pytest.mark.parametrize(
    "capability_id",
    [
        "sale.order.search",
        "sale.order.get",
        "sale.order.line.search",
        "sale.order.analysis.summary",
        "purchase.order.search",
        "purchase.order.get",
        "purchase.order.line.search",
        "purchase.order.analysis.summary",
    ],
)
def test_port_uses_one_fixed_action_and_closed_payload(capability_id: str) -> None:
    client = Client(_page())
    port = OdooOrderDocumentsPort(client)
    parameters = {"after": None, "limit": 101}

    assert (
        port.read(
            capability_id=capability_id,
            company_id=7,
            parameters=parameters,
        )
        == _page()
    )
    assert port.user_id == 5
    assert client.calls == [
        (
            ACTION,
            {
                "capability_id": capability_id,
                "company_id": 7,
                "parameters": parameters,
            },
        )
    ]


def test_port_rejects_unknown_capability_and_malformed_page() -> None:
    port = OdooOrderDocumentsPort(Client(_page()))
    with pytest.raises(ValueError):
        _ = port.user_id
    with pytest.raises(ValueError):
        port.read(capability_id="model.search", company_id=7, parameters={})

    bad = _page()
    bad["items"] = ["not-an-object"]
    port = OdooOrderDocumentsPort(Client(bad))
    with pytest.raises(ValueError):
        port.read(
            capability_id="sale.order.search",
            company_id=7,
            parameters={},
        )
    with pytest.raises(ValueError):
        _ = port.user_id


@pytest.mark.parametrize(
    "mutation",
    [
        lambda page: page.update(extra=True),
        lambda page: page.update(user_id=True),
        lambda page: page.update(access_allowed="yes"),
        lambda page: page.update(items={}),
    ],
)
def test_port_rejects_expanded_or_malformed_runtime_pages(mutation) -> None:
    page = _page()
    mutation(page)
    with pytest.raises(ValueError):
        OdooOrderDocumentsPort(Client(page)).read(
            capability_id="purchase.order.get",
            company_id=7,
            parameters={"order_id": 9},
        )
