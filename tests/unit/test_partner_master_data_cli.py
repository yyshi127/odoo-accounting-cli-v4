from __future__ import annotations

from functools import partial

import pytest

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4.bridge.core_object_reads import OdooCoreObjectReadPort
from odoo_accounting_cli_v4.bridge.core_writes import OdooCoreWritePort
from odoo_accounting_cli_v4.capabilities.core_object_reads import (
    CORE_OBJECT_READ_CAPABILITY_IDS,
)
from odoo_accounting_cli_v4.capabilities.core_writes import CORE_WRITE_CAPABILITY_IDS

READ_CAPABILITIES = {"partner.search", "partner.get"}
PARTNER_WRITE_CAPABILITIES = {
    "partner.create",
    "partner.update",
    "partner.archive",
    "partner.restore",
    "partner.accounting.update",
}
BANK_WRITE_CAPABILITIES = {
    "partner.bank_account.create",
    "partner.bank_account.update",
    "partner.bank_account.archive",
    "partner.bank_account.restore",
}


def _request() -> dict:
    return {
        "schema_version": "v1",
        "request_id": "a2f91531-a230-4dde-a8bf-e56bb03bdaba",
        "context": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": {},
    }


def test_cli_registers_partner_read_handlers_and_validators() -> None:
    for handler_key, capability_id in {
        "partner_search": "partner.search",
        "partner_get": "partner.get",
    }.items():
        handler = cli._HANDLERS[handler_key]
        validator = cli._REQUEST_VALIDATORS[handler_key]
        assert isinstance(handler, partial)
        assert handler.args == (capability_id,)
        assert isinstance(validator, partial)
        assert validator.args == (capability_id,)
        assert capability_id in CORE_OBJECT_READ_CAPABILITY_IDS


def test_cli_registers_every_partner_model_and_write() -> None:
    assert {
        capability_id: cli._CAPABILITY_MODELS[capability_id]
        for capability_id in READ_CAPABILITIES
    } == {
        "partner.search": "res.partner",
        "partner.get": "res.partner",
    }
    for capability_id in PARTNER_WRITE_CAPABILITIES:
        assert capability_id in CORE_WRITE_CAPABILITY_IDS
        assert cli._CAPABILITY_MODELS[capability_id] == "res.partner"
    for capability_id in BANK_WRITE_CAPABILITIES:
        assert capability_id in CORE_WRITE_CAPABILITY_IDS
        assert cli._CAPABILITY_MODELS[capability_id] == "res.partner.bank"


@pytest.mark.parametrize(
    "capability_id",
    sorted(READ_CAPABILITIES | PARTNER_WRITE_CAPABILITIES | BANK_WRITE_CAPABILITIES),
)
def test_configured_factory_uses_the_generic_partner_ports(
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
    monkeypatch.setattr(cli, "OdooBridgeClient", lambda *_args, **_kwargs: client)
    port = cli._configured_port_factory(capability_id, _request())
    expected_type = (
        OdooCoreObjectReadPort
        if capability_id in READ_CAPABILITIES
        else OdooCoreWritePort
    )
    assert type(port) is expected_type
    assert port._client is client
