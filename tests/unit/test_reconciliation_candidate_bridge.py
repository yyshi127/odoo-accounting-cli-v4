from __future__ import annotations

import pytest

from odoo_accounting_cli_v4.bridge.reconciliation_candidates import (
    OdooReconciliationCandidatesPort,
)


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


def test_port_uses_only_the_fixed_reconciliation_candidate_action() -> None:
    client = Client(_page(rows=[{"id": 1}]))
    port = OdooReconciliationCandidatesPort(client)
    filters = {
        "date_from": None,
        "date_to": None,
        "states": ["posted"],
        "account_id": None,
        "partner_id": None,
        "journal_id": None,
        "account_kinds": ["receivable", "payable", "other"],
        "query": None,
    }

    result = port.read_page(
        company_id=7,
        after=["2025-01-25", 20],
        limit=101,
        filters=filters,
    )

    assert result["rows"] == [{"id": 1}]
    assert port.user_id == 5
    assert client.calls == [
        (
            "account.move.line.reconciliation_candidate.read_page",
            {
                "company_id": 7,
                "after": ["2025-01-25", 20],
                "limit": 101,
                "filters": filters,
            },
        )
    ]


def test_user_id_is_not_reused_after_a_malformed_result() -> None:
    client = Client(_page(rows=[]))
    port = OdooReconciliationCandidatesPort(client)
    port.read_page(company_id=7, after=None, limit=2, filters={})
    assert port.user_id == 5
    client.result = {}

    with pytest.raises(ValueError):
        port.read_page(company_id=7, after=None, limit=2, filters={})
    with pytest.raises(ValueError):
        _ = port.user_id


@pytest.mark.parametrize(
    "result",
    [
        {},
        _page(rows=None),
        _page(rows=[None]),
        {**_page(rows=[]), "extra": True},
        {**_page(rows=[]), "user_id": True},
        {**_page(rows=[]), "company_visible": 1},
        {**_page(rows=[]), "module_installed": 1},
        {**_page(rows=[]), "access_allowed": 1},
    ],
)
def test_port_rejects_malformed_bridge_results(result: dict) -> None:
    port = OdooReconciliationCandidatesPort(Client(result))

    with pytest.raises(ValueError):
        port.read_page(company_id=7, after=None, limit=2, filters={})
