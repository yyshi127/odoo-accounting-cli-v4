from __future__ import annotations

import pytest

from odoo_accounting_cli_v4.bridge.inventory_master import (
    ACTION,
    OdooInventoryMasterPort,
)


class Client:
    def __init__(self, page: object) -> None:
        self.page = page
        self.calls: list[tuple[str, dict]] = []

    def invoke(self, action: str, payload: dict) -> object:
        self.calls.append((action, payload))
        return self.page


def page() -> dict:
    return {
        "user_id": 5,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "cursor_found": True,
        "items": [],
    }


def test_port_invokes_only_the_frozen_action_and_payload() -> None:
    client = Client(page())
    port = OdooInventoryMasterPort(client)

    assert (
        port.read(
            capability_id="warehouse.list",
            company_id=1,
            parameters={"active": True, "after": None, "limit": 101},
        )
        == page()
    )
    assert port.user_id == 5
    assert client.calls == [
        (
            ACTION,
            {
                "capability_id": "warehouse.list",
                "company_id": 1,
                "parameters": {"active": True, "after": None, "limit": 101},
            },
        )
    ]
    assert ACTION == "accounting.inventory_master.read"


def test_port_rejects_unknown_capability_and_malformed_page() -> None:
    port = OdooInventoryMasterPort(Client(page()))
    with pytest.raises(ValueError, match="Unsupported"):
        port.read(capability_id="stock.rule.list", company_id=1, parameters={})

    malformed = page()
    malformed["items"] = "not-a-list"
    with pytest.raises(ValueError, match="invalid inventory-master page"):
        OdooInventoryMasterPort(Client(malformed)).read(
            capability_id="stock.route.list", company_id=1, parameters={}
        )
