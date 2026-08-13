from __future__ import annotations

import io
import json

import pytest

import odoo_accounting_cli_v4.cli as cli
from odoo_accounting_cli_v4.bridge.payments import OdooPaymentPort
from odoo_accounting_cli_v4.registry import load_registry


def _request(parameters: dict) -> dict:
    return {
        "schema_version": "v1",
        "request_id": "7bc39413-0d69-4092-9319-795d33f3167c",
        "context": {
            "database": "v4-dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": parameters,
    }


def _payment() -> dict:
    return {
        "id": 30,
        "name": "BNK1/2025/0030",
        "date": "2025-01-25",
        "state": "in_process",
        "payment_type": "inbound",
        "partner_type": "customer",
        "amount": "50",
        "amount_signed": "50",
        "amount_company_currency_signed": "50",
        "currency": {"id": 6, "code": "CNY"},
        "company_currency": {"id": 6, "code": "CNY"},
        "company_id": 7,
        "partner": {"id": 9, "name": "Fixture Customer"},
        "journal": {"id": 8, "code": "BNK1", "name": "Fixture Bank"},
        "memo": "Fixture receipt",
        "payment_reference": "INV/2025/0040",
        "payment_method_line": {"id": 3, "name": "Manual", "journal_id": 8},
        "payment_method": {
            "id": 1,
            "code": "manual",
            "name": "Manual",
            "payment_type": "inbound",
        },
        "move_id": 80,
        "is_reconciled": True,
        "is_matched": False,
    }


def _payment_detail() -> dict:
    document = {
        "id": 40,
        "name": "INV/2025/0040",
        "move_type": "out_invoice",
        "state": "posted",
        "payment_state": "partial",
        "company_id": 7,
    }
    return {
        **_payment(),
        "journal_entry": {
            "id": 80,
            "name": "BNK1/2025/0030",
            "state": "posted",
            "date": "2025-01-25",
        },
        "invoice_ids": [document],
        "reconciled_invoices": [document],
        "reconciled_bills": [],
    }


@pytest.mark.parametrize(
    ("capability_id", "parameters", "expected_data"),
    (
        (
            "payment.search",
            {"limit": 1},
            {"items": [_payment()], "has_more": False, "next_cursor": None},
        ),
        ("payment.get", {"payment_id": 30}, _payment_detail()),
    ),
)
def test_cli_dispatches_fixed_payment_reads(
    capability_id: str,
    parameters: dict,
    expected_data: dict,
) -> None:
    class Port:
        user_id = 42

        def search_page(self, **kwargs):
            assert kwargs == {
                "company_id": 7,
                "after": None,
                "limit": 2,
                "filters": {
                    "date_from": None,
                    "date_to": None,
                    "states": [],
                    "payment_types": [],
                    "partner_types": [],
                    "journal_id": None,
                    "partner_id": None,
                    "currency_id": None,
                    "query": None,
                },
            }
            return {
                "user_id": 42,
                "company_visible": True,
                "module_installed": True,
                "access_allowed": True,
                "rows": [_payment()],
            }

        def get_payment(self, **kwargs):
            assert kwargs == {"company_id": 7, "payment_id": 30}
            return {
                "user_id": 42,
                "company_visible": True,
                "module_installed": True,
                "access_allowed": True,
                "payment": _payment_detail(),
            }

    def port_factory(selected: str, request: dict) -> Port:
        assert selected == capability_id
        assert request == _request(parameters)
        return Port()

    stdout = io.StringIO()
    stderr = io.StringIO()
    result = cli.main(
        ["read", capability_id, "--request", "-"],
        stdin=io.StringIO(json.dumps(_request(parameters))),
        stdout=stdout,
        stderr=stderr,
        port_factory=port_factory,
    )

    document = json.loads(stdout.getvalue())
    assert result == 0
    assert stderr.getvalue() == ""
    assert document["success"] is True
    assert document["data"] == expected_data
    assert document["odoo"] == {
        "database": "v4-dev",
        "company_id": 7,
        "user_id": 42,
        "model": "account.payment",
        "record_ids": [30],
    }
    load_registry().validate_instance(
        f"schemas/v1/{capability_id}.response.schema.json", document
    )


def test_payment_not_found_preserves_verified_odoo_context() -> None:
    class Port:
        user_id = 42

        def get_payment(self, **kwargs):
            assert kwargs == {"company_id": 7, "payment_id": 30}
            return {
                "user_id": 42,
                "company_visible": True,
                "module_installed": True,
                "access_allowed": True,
                "payment": None,
            }

    stdout = io.StringIO()
    stderr = io.StringIO()
    result = cli.main(
        ["read", "payment.get", "--request", "-"],
        stdin=io.StringIO(json.dumps(_request({"payment_id": 30}))),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda selected, request: Port(),
    )

    document = json.loads(stdout.getvalue())
    assert result == 4
    assert stderr.getvalue() == ""
    assert document["error"]["code"] == "record_not_found"
    assert document["odoo"] == {
        "database": "v4-dev",
        "company_id": 7,
        "user_id": 42,
        "model": "account.payment",
        "record_ids": [],
    }
    load_registry().validate_instance(
        "schemas/v1/payment.get.response.schema.json", document
    )


def test_invalid_payment_cursor_does_not_read_unverified_port_user_id() -> None:
    class Client:
        def invoke(self, action, payload):
            raise AssertionError("invalid cursor must fail before bridge invocation")

    stdout = io.StringIO()
    stderr = io.StringIO()
    result = cli.main(
        ["read", "payment.search", "--request", "-"],
        stdin=io.StringIO(
            json.dumps(_request({"limit": 1, "cursor": "not-a-valid-cursor"}))
        ),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda selected, request: OdooPaymentPort(Client()),
    )

    document = json.loads(stdout.getvalue())
    assert result == 2
    assert stderr.getvalue() == ""
    assert document["error"]["code"] == "invalid_cursor"
    assert document["odoo"] == {
        "database": None,
        "company_id": None,
        "user_id": None,
        "model": None,
        "record_ids": [],
    }
    load_registry().validate_instance(
        "schemas/v1/payment.search.response.schema.json", document
    )


@pytest.mark.parametrize("capability_id", ["payment.search", "payment.get"])
def test_configured_factory_selects_payment_port(
    monkeypatch: pytest.MonkeyPatch, capability_id: str
) -> None:
    target = object()
    client = object()

    class RuntimeConfig:
        def resolve(self, database: str, company_id: int, user_login: str) -> object:
            assert (database, company_id, user_login) == ("v4-dev", 7, "v4-agent")
            return target

    monkeypatch.setattr(cli, "load_runtime_config", lambda path: RuntimeConfig())
    monkeypatch.setattr(
        cli,
        "OdooBridgeClient",
        lambda selected_target, **kwargs: (
            client
            if selected_target is target
            and kwargs == {"language": "en_US", "timezone": "Asia/Shanghai"}
            else None
        ),
    )

    port = cli._configured_port_factory(capability_id, _request({}))

    assert isinstance(port, OdooPaymentPort)
    assert port._client is client
