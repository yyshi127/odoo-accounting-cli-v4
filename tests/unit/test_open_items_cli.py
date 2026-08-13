from __future__ import annotations

import io
import json

import pytest

from odoo_accounting_cli_v4.bridge.open_items import OdooOpenItemsPort
from odoo_accounting_cli_v4.cli import main
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


def _item(side: str) -> dict:
    payable = side == "payable"
    account_type = "liability_payable" if payable else "asset_receivable"
    return {
        "id": 30,
        "side": side,
        "date": "2025-01-20",
        "due_date": "2025-02-20",
        "name": "Fixture open item",
        "ref": None,
        "move": {
            "id": 20,
            "name": "BILL/2025/0020" if payable else "INV/2025/0020",
            "move_type": "in_invoice" if payable else "out_invoice",
            "state": "posted",
        },
        "journal": {
            "id": 8,
            "code": "BILL" if payable else "INV",
            "name": "Purchases" if payable else "Sales",
        },
        "company_id": 7,
        "partner": {"id": 9, "name": "Fixture Partner", "reference": None},
        "account": {
            "id": 10,
            "code": "2100" if payable else "1100",
            "name": "Accounts Payable" if payable else "Accounts Receivable",
            "account_type": account_type,
            "non_trade": False,
        },
        "currency": {"id": 6, "code": "CNY"},
        "company_currency": {"id": 6, "code": "CNY"},
        "debit": "0" if payable else "113",
        "credit": "113" if payable else "0",
        "balance": "-113" if payable else "113",
        "amount_currency": "-113" if payable else "113",
        "amount_residual": "-113" if payable else "63",
        "amount_residual_currency": "-113" if payable else "63",
        "reconciled": False,
        "matching_number": None,
    }


@pytest.mark.parametrize(
    ("capability_id", "side"),
    [
        ("receivable.open_items.list", "receivable"),
        ("payable.open_items.list", "payable"),
    ],
)
def test_cli_dispatches_fixed_open_item_reads(
    capability_id: str, side: str
) -> None:
    item = _item(side)

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
                    "due_date_from": None,
                    "due_date_to": None,
                    "partner_id": None,
                    "account_id": None,
                    "journal_id": None,
                    "currency_id": None,
                    "query": None,
                },
            }
            return {
                "user_id": 42,
                "company_visible": True,
                "module_installed": True,
                "access_allowed": True,
                "rows": [item],
            }

    stdout = io.StringIO()
    stderr = io.StringIO()
    result = main(
        ["read", capability_id, "--request", "-"],
        stdin=io.StringIO(json.dumps(_request({"limit": 1}))),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda selected, request: Port(),
    )

    document = json.loads(stdout.getvalue())
    assert result == 0
    assert stderr.getvalue() == ""
    assert document["data"] == {
        "items": [item],
        "has_more": False,
        "next_cursor": None,
    }
    assert document["odoo"] == {
        "database": "v4-dev",
        "company_id": 7,
        "user_id": 42,
        "model": "account.move.line",
        "record_ids": [30],
    }
    load_registry().validate_instance(
        f"schemas/v1/{capability_id}.response.schema.json", document
    )


def test_invalid_cursor_fails_before_unverified_bridge_metadata() -> None:
    class Client:
        def invoke(self, action, payload):
            raise AssertionError("invalid cursor must not invoke the bridge")

    stdout = io.StringIO()
    stderr = io.StringIO()
    result = main(
        ["read", "receivable.open_items.list", "--request", "-"],
        stdin=io.StringIO(
            json.dumps(_request({"limit": 1, "cursor": "not-a-valid-cursor"}))
        ),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda selected, request: OdooOpenItemsPort(
            Client(), selected
        ),
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
        "schemas/v1/receivable.open_items.list.response.schema.json", document
    )
