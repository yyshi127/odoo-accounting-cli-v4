from __future__ import annotations

from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge.assets import ACTION, OdooAssetPort


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
        "items": [{"id": 31}],
    }
    value.update(overrides)
    return value


def test_port_invokes_only_fixed_asset_action_and_records_identity() -> None:
    client = Client(_page())
    port = OdooAssetPort(client)

    result = port.read(
        capability_id="asset.get",
        company_id=7,
        parameters={"asset_id": 31},
    )

    assert result == _page()
    assert port.user_id == 5
    assert client.calls == [
        (
            ACTION,
            {
                "capability_id": "asset.get",
                "company_id": 7,
                "parameters": {"asset_id": 31},
            },
        )
    ]


def test_port_rejects_unknown_capability_without_bridge_call() -> None:
    client = Client(_page())
    port = OdooAssetPort(client)
    with pytest.raises(ValueError, match="Unsupported"):
        port.read(capability_id="asset.unlink", company_id=7, parameters={})
    assert client.calls == []


@pytest.mark.parametrize(
    "response",
    [
        None,
        _page(extra=True),
        _page(user_id=True),
        _page(company_visible=1),
        _page(cursor_found=None),
        _page(items=[1]),
    ],
)
def test_port_rejects_malformed_page_and_clears_identity(response: Any) -> None:
    client = Client(_page())
    port = OdooAssetPort(client)
    port.read(capability_id="asset.search", company_id=7, parameters={})
    client.response = response

    with pytest.raises(ValueError, match="invalid asset page"):
        port.read(capability_id="asset.search", company_id=7, parameters={})
    with pytest.raises(ValueError, match="No verified"):
        _ = port.user_id
