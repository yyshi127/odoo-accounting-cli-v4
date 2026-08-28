from __future__ import annotations

from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge.inventory_accounting import (
    ACTION,
    OdooInventoryAccountingPort,
)


class Client:
    def __init__(self, response: Any) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def invoke(self, action: str, payload: dict[str, Any]) -> Any:
        self.calls.append((action, payload))
        return self.response


def _page(**overrides: Any) -> dict[str, Any]:
    value = {
        "user_id": 5,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "cursor_found": True,
        "items": [{"id": 11}],
    }
    value.update(overrides)
    return value


def test_port_invokes_only_the_fixed_action_and_records_verified_identity() -> None:
    client = Client(_page())
    port = OdooInventoryAccountingPort(client)

    result = port.read(
        capability_id="purchase_bill.matching.inspect",
        company_id=7,
        parameters={"bill_id": 11},
    )

    assert result == _page()
    assert port.user_id == 5
    assert client.calls == [
        (
            ACTION,
            {
                "capability_id": "purchase_bill.matching.inspect",
                "company_id": 7,
                "parameters": {"bill_id": 11},
            },
        )
    ]


def test_port_rejects_unknown_capability_without_invoking_bridge() -> None:
    client = Client(_page())
    port = OdooInventoryAccountingPort(client)

    with pytest.raises(ValueError, match="Unsupported"):
        port.read(capability_id="arbitrary.call", company_id=7, parameters={})

    assert client.calls == []


@pytest.mark.parametrize(
    "response",
    [
        None,
        _page(extra=True),
        _page(user_id=True),
        _page(cursor_found=1),
        _page(items=[1]),
    ],
)
def test_port_rejects_invalid_page_and_clears_previous_identity(response: Any) -> None:
    client = Client(_page())
    port = OdooInventoryAccountingPort(client)
    port.read(
        capability_id="report.inventory_valuation",
        company_id=7,
        parameters={"date": "2025-01-31"},
    )
    client.response = response

    with pytest.raises(ValueError, match="invalid inventory-accounting page"):
        port.read(
            capability_id="report.inventory_valuation",
            company_id=7,
            parameters={"date": "2025-01-31"},
        )
    with pytest.raises(ValueError, match="No verified"):
        _ = port.user_id
