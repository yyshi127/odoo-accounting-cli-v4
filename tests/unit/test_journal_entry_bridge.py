from __future__ import annotations

import pytest

from odoo_accounting_cli_v4.bridge.journal_entries import OdooJournalEntryPort


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
    port = OdooJournalEntryPort(client)
    filters = {
        "date_from": None,
        "date_to": None,
        "states": ["posted"],
        "journal_id": None,
        "partner_id": None,
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
            "account.move.journal_entry.search_page",
            {
                "company_id": 7,
                "after": ["2025-01-15", 2],
                "limit": 101,
                "filters": filters,
            },
        )
    ]


def test_get_uses_the_fixed_composite_action_and_accepts_not_found() -> None:
    client = Client(_page(entry=None))
    port = OdooJournalEntryPort(client)

    result = port.get_entry(company_id=7, entry_id=30)

    assert result["entry"] is None
    assert port.user_id == 5
    assert client.calls == [
        ("account.move.journal_entry.get", {"company_id": 7, "move_id": 30})
    ]


@pytest.mark.parametrize(
    "result",
    [
        {},
        _page(rows=None),
        _page(entry=[]),
        {**_page(rows=[]), "extra": True},
        {**_page(rows=[]), "user_id": True},
    ],
)
def test_port_rejects_malformed_bridge_results(result: dict) -> None:
    port = OdooJournalEntryPort(Client(result))

    with pytest.raises(ValueError):
        if "entry" in result:
            port.get_entry(company_id=7, entry_id=30)
        else:
            port.search_page(company_id=7, after=None, limit=2, filters={})
