from __future__ import annotations

import pytest

from odoo_accounting_cli_v4.bridge.budget_report import (
    ACTION,
    OdooBudgetReportPort,
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


def test_port_uses_one_fixed_action_and_preserves_the_closed_payload() -> None:
    client = Client(_page())
    port = OdooBudgetReportPort(client)
    parameters = {
        "budget_id": 71,
        "budget_line_id": None,
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
        "plan_id": None,
        "analytic_account_id": None,
        "line_type": None,
        "after": None,
        "limit": 101,
    }

    assert port.read(company_id=7, parameters=parameters) == _page()
    assert port.user_id == 5
    assert client.calls == [
        (
            ACTION,
            {
                "company_id": 7,
                "parameters": parameters,
            },
        )
    ]


def test_user_id_is_unavailable_before_or_after_an_invalid_page() -> None:
    port = OdooBudgetReportPort(Client(_page()))
    with pytest.raises(ValueError):
        _ = port.user_id

    bad = _page()
    bad["items"] = ["not-an-object"]
    port = OdooBudgetReportPort(Client(bad))
    with pytest.raises(ValueError):
        port.read(company_id=7, parameters={})
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
        OdooBudgetReportPort(Client(page)).read(company_id=7, parameters={})
