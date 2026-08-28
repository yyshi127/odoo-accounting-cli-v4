from __future__ import annotations

import pytest

from odoo_accounting_cli_v4.bridge.journal_integrity import (
    OdooJournalIntegrityPort,
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


def test_port_uses_only_the_fixed_journal_integrity_action() -> None:
    page = _page({})
    client = Client(page)
    port = OdooJournalIntegrityPort(client)

    assert port.inspect(company_id=7) == page
    assert port.user_id == 5
    assert client.calls == [
        ("res.company.journal_integrity.inspect", {"company_id": 7})
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
    port = OdooJournalIntegrityPort(Client(page))

    with pytest.raises(ValueError):
        port.inspect(company_id=7)
