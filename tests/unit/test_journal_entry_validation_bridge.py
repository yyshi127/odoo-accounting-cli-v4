from __future__ import annotations

from odoo_accounting_cli_v4.bridge.journal_entries import OdooJournalEntryPort


class Client:
    def __init__(self, result: dict) -> None:
        self.result = result
        self.calls: list[tuple[str, dict]] = []

    def invoke(self, action: str, payload: dict) -> dict:
        self.calls.append((action, payload))
        return self.result


def test_check_reuses_the_fixed_read_only_get_action() -> None:
    page = {
        "user_id": 5,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "entry": None,
    }
    client = Client(page)
    port = OdooJournalEntryPort(client)

    result = port.check_entry(company_id=7, entry_id=30)

    assert result == page
    assert port.user_id == 5
    assert client.calls == [
        ("account.move.journal_entry.get", {"company_id": 7, "move_id": 30})
    ]
