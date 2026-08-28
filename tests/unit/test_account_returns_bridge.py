from __future__ import annotations

import pytest

from odoo_accounting_cli_v4.bridge.account_returns import (
    ACTION,
    OdooAccountReturnPort,
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


def test_port_uses_one_fixed_action_and_closed_payload() -> None:
    client = Client(_page())
    port = OdooAccountReturnPort(client)
    parameters = {"return_id": 30}

    assert (
        port.read(
            capability_id="account.return.get",
            company_id=7,
            parameters=parameters,
        )
        == _page()
    )
    assert port.user_id == 5
    assert client.calls == [
        (
            "accounting.account_return.read",
            {
                "capability_id": "account.return.get",
                "company_id": 7,
                "parameters": parameters,
            },
        )
    ]
    assert ACTION == "accounting.account_return.read"


def test_port_rejects_unknown_capability_and_malformed_page() -> None:
    port = OdooAccountReturnPort(Client(_page()))
    with pytest.raises(ValueError):
        _ = port.user_id
    with pytest.raises(ValueError):
        port.read(capability_id="model.search", company_id=7, parameters={})

    for mutation in (
        lambda page: page.update(extra=True),
        lambda page: page.update(user_id=True),
        lambda page: page.update(access_allowed="yes"),
        lambda page: page.update(items=["not-an-object"]),
    ):
        bad = _page()
        mutation(bad)
        port = OdooAccountReturnPort(Client(bad))
        with pytest.raises(ValueError):
            port.read(
                capability_id="account.return.summary",
                company_id=7,
                parameters={"as_of": "2026-08-28"},
            )
        with pytest.raises(ValueError):
            _ = port.user_id
