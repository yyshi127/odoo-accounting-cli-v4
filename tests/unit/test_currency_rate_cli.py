from __future__ import annotations

import io
import json

import pytest

import odoo_accounting_cli_v4.cli as cli
from odoo_accounting_cli_v4.registry import load_registry

CAPABILITY_ID = "currency.rate.list"


def _request(parameters: dict) -> dict:
    return {
        "schema_version": "v1",
        "request_id": "cc7ba2b8-c069-47bb-948b-5250f79ec679",
        "context": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "zh_CN",
            "timezone": "Asia/Shanghai",
        },
        "parameters": parameters,
    }


def _rate() -> dict:
    return {
        "id": 20,
        "date": "2025-01-25",
        "currency": {"id": 2, "code": "USD"},
        "company_currency": {"id": 1, "code": "CNY"},
        "requested_company_id": 7,
        "source_company_id": 7,
        "technical_rate": "0.1406469760900141",
        "foreign_units_per_company_unit": "0.1406469760900141",
        "company_units_per_foreign_unit": "7.11",
    }


def test_cli_dispatches_the_fixed_currency_rate_read() -> None:
    rate = _rate()

    class Port:
        user_id = 42

        def read_page(self, **kwargs):
            assert kwargs == {
                "company_id": 7,
                "after": None,
                "limit": 2,
                "filters": {
                    "date_from": None,
                    "date_to": None,
                    "currency_id": None,
                },
            }
            return {
                "user_id": 42,
                "company_visible": True,
                "module_installed": True,
                "access_allowed": True,
                "root_company_id": 7,
                "rows": [rate],
            }

    def port_factory(selected: str, request: dict) -> Port:
        assert selected == CAPABILITY_ID
        assert request == _request({"limit": 1})
        return Port()

    stdout = io.StringIO()
    stderr = io.StringIO()
    result = cli.main(
        ["read", CAPABILITY_ID, "--request", "-"],
        stdin=io.StringIO(json.dumps(_request({"limit": 1}))),
        stdout=stdout,
        stderr=stderr,
        port_factory=port_factory,
    )

    document = json.loads(stdout.getvalue())
    assert result == 0
    assert stderr.getvalue() == ""
    assert document["success"] is True
    assert document["data"] == {
        "items": [rate],
        "has_more": False,
        "next_cursor": None,
    }
    assert document["odoo"] == {
        "database": "odoo_cli_v4_dev",
        "company_id": 7,
        "user_id": 42,
        "model": "res.currency.rate",
        "record_ids": [20],
    }
    load_registry().validate_instance(
        "schemas/v1/currency.rate.list.response.schema.json", document
    )


def test_configured_factory_selects_currency_rate_port(
    monkeypatch: pytest.MonkeyPatch,
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

    monkeypatch.setattr(cli, "load_runtime_config", lambda path: RuntimeConfig())
    monkeypatch.setattr(
        cli,
        "OdooBridgeClient",
        lambda selected_target, **kwargs: (
            client
            if selected_target is target
            and kwargs == {"language": "zh_CN", "timezone": "Asia/Shanghai"}
            else None
        ),
    )

    port = cli._configured_port_factory(CAPABILITY_ID, _request({}))

    assert type(port).__name__ == "OdooCurrencyRateListPort"
    assert port._client is client
