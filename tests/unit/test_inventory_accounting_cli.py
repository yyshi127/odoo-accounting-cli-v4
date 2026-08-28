from __future__ import annotations

from functools import partial
from typing import Any

import pytest

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4.bridge.inventory_accounting import (
    OdooInventoryAccountingPort,
)
from odoo_accounting_cli_v4.capabilities.inventory_accounting import (
    read_inventory_accounting,
    validate_inventory_accounting_request,
)
from odoo_accounting_cli_v4.registry import load_registry

CAPABILITIES = {
    "cogs.entries.list": ("cogs_entries_list", "account.move.line"),
    "inventory.accounting_entries.list": (
        "inventory_accounting_entries_list",
        "stock.move",
    ),
    "report.inventory_valuation": (
        "report_inventory_valuation",
        "stock_account.stock.valuation.report",
    ),
    "purchase_bill.matching.inspect": (
        "purchase_bill_matching_inspect",
        "account.move",
    ),
    "sale_invoice.stock_link.inspect": (
        "sale_invoice_stock_link_inspect",
        "account.move",
    ),
}


def _request() -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "request_id": "d522461d-54ad-441a-9db2-f64fd1dfd48b",
        "context": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "zh_CN",
            "timezone": "Asia/Shanghai",
        },
        "parameters": {},
    }


def _assert_partial(value: object, function: object, capability_id: str) -> None:
    assert isinstance(value, partial)
    assert value.func is function
    assert value.args == (capability_id,)


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_inventory_accounting_cli_wiring(capability_id: str) -> None:
    handler_key, model = CAPABILITIES[capability_id]

    assert load_registry().describe(capability_id)["handler_key"] == handler_key
    _assert_partial(
        cli._HANDLERS[handler_key], read_inventory_accounting, capability_id
    )
    _assert_partial(
        cli._REQUEST_VALIDATORS[handler_key],
        validate_inventory_accounting_request,
        capability_id,
    )
    assert cli._CAPABILITY_MODELS[capability_id] == model


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_configured_factory_uses_the_shared_inventory_accounting_port(
    capability_id: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = object()
    client = object()

    class RuntimeConfig:
        def resolve(self, database: str, company_id: int, user_login: str) -> object:
            assert (database, company_id, user_login) == (
                "odoo_cli_v4_dev",
                7,
                "v4-agent",
            )
            return target

    monkeypatch.setattr(cli, "load_runtime_config", lambda _path: RuntimeConfig())
    monkeypatch.setattr(
        cli,
        "OdooBridgeClient",
        lambda selected, **kwargs: (
            client
            if selected is target
            and kwargs == {"language": "zh_CN", "timezone": "Asia/Shanghai"}
            else None
        ),
    )

    port = cli._configured_port_factory(capability_id, _request())

    assert isinstance(port, OdooInventoryAccountingPort)
    assert port._client is client
