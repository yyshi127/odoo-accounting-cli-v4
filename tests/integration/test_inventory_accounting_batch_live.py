"""Read-only live smoke for the inventory-accounting capability batch."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from decimal import Decimal
from pathlib import Path

import pytest

from odoo_accounting_cli_v4.registry import load_registry

_CONFIG_ENV = "ODOO_ACCOUNTING_CLI_V4_CONFIG"
_ALIASES = ("v4-dev", "v4-e2e")
_COMPANY_ID = 1
_USER_LOGIN = "odacv4_g5_accountant"
_DOCUMENT_REF = {
    "in_invoice": "ODACV4-FX1-CN-BILL-TAX-INCLUDED",
    "out_invoice": "ODACV4-FX1-CN-INVOICE-TAX-EXCLUDED",
}
_MODELS = {
    "cogs.entries.list": "account.move.line",
    "inventory.accounting_entries.list": "stock.move",
    "report.inventory_valuation": "stock_account.stock.valuation.report",
    "purchase_bill.matching.inspect": "account.move",
    "sale_invoice.stock_link.inspect": "account.move",
    "invoice.search": "account.move",
}


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _request(
    alias: str,
    capability_id: str,
    parameters: dict,
    *,
    case: str,
) -> dict:
    return {
        "schema_version": "v1",
        "request_id": str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"odacv4:{alias}:{_COMPANY_ID}:{capability_id}:inventory-live:{case}",
            )
        ),
        "context": {
            "database": alias,
            "company_id": _COMPANY_ID,
            "user_login": _USER_LOGIN,
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": parameters,
    }


def _invoke(
    alias: str,
    capability_id: str,
    parameters: dict,
    *,
    case: str,
) -> dict:
    root = _project_root()
    request = _request(alias, capability_id, parameters, case=case)
    registry = load_registry()
    registry.validate_instance(
        f"schemas/v1/{capability_id}.request.schema.json", request
    )

    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = os.pathsep.join(
        part for part in (str(root / "src"), environment.get("PYTHONPATH")) if part
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "odoo_accounting_cli_v4",
            "read",
            capability_id,
            "--request",
            "-",
        ],
        cwd=root,
        env=environment,
        input=json.dumps(request, sort_keys=True, separators=(",", ":")),
        text=True,
        capture_output=True,
        check=False,
        timeout=240,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert completed.stderr == ""
    assert len(completed.stdout.splitlines()) == 1
    document = json.loads(completed.stdout)
    registry.validate_instance(
        f"schemas/v1/{capability_id}.response.schema.json", document
    )
    assert document["schema_version"] == "v1"
    assert document["request_id"] == request["request_id"]
    assert document["capability"] == capability_id
    assert document["success"] is True
    assert document["status"] == "verified"
    assert document["error"] is None
    assert document["warnings"] == []
    assert document["odoo"]["database"] == alias
    assert document["odoo"]["company_id"] == _COMPANY_ID
    assert isinstance(document["odoo"]["user_id"], int)
    assert document["odoo"]["user_id"] > 0
    assert document["odoo"]["model"] == _MODELS[capability_id]
    return document


def _document_id(alias: str, move_type: str) -> int:
    expected_ref = _DOCUMENT_REF[move_type]
    search = _invoke(
        alias,
        "invoice.search",
        {
            "limit": 100,
            "cursor": None,
            "document_types": [move_type],
            "states": ["posted"],
            "query": expected_ref,
        },
        case=f"select-{move_type}",
    )
    matches = [
        item
        for item in search["data"]["items"]
        if item["move_type"] == move_type and item["ref"] == expected_ref
    ]
    assert len(matches) == 1
    assert search["odoo"]["record_ids"] == [matches[0]["id"]]
    return matches[0]["id"]


def _assert_empty_page(document: dict) -> None:
    assert document["data"] == {
        "items": [],
        "has_more": False,
        "next_cursor": None,
    }
    assert document["odoo"]["record_ids"] == []


@pytest.mark.integration
@pytest.mark.parametrize("alias", _ALIASES)
def test_inventory_accounting_batch_uses_live_read_only_fixture(alias: str) -> None:
    if not os.environ.get(_CONFIG_ENV):
        pytest.skip(f"{_CONFIG_ENV} is not configured")

    bill_id = _document_id(alias, "in_invoice")
    invoice_id = _document_id(alias, "out_invoice")

    cogs = _invoke(
        alias,
        "cogs.entries.list",
        {"invoice_id": invoice_id, "limit": 100, "cursor": None},
        case="empty-cogs",
    )
    _assert_empty_page(cogs)

    inventory_entries = _invoke(
        alias,
        "inventory.accounting_entries.list",
        {
            "date_from": "2025-01-01",
            "date_to": "2025-01-31",
            "limit": 100,
            "cursor": None,
        },
        case="empty-inventory-entries",
    )
    _assert_empty_page(inventory_entries)

    valuation = _invoke(
        alias,
        "report.inventory_valuation",
        {"date": "2025-01-31"},
        case="zero-valuation",
    )
    valuation_data = valuation["data"]
    assert valuation_data["as_of_date"] == "2025-01-31"
    assert valuation_data["company"]["id"] == _COMPANY_ID
    assert valuation_data["currency"]["code"] == "CNY"
    assert Decimal(valuation_data["initial_balance"]) == 0
    assert Decimal(valuation_data["ending_stock"]) == 0
    assert Decimal(valuation_data["stock_variation"]) == 0
    for field in (
        "inventory_loss",
        "not_invoiced_delivered_goods",
        "not_invoiced_received_goods",
        "cost_of_production",
    ):
        value = valuation_data[field]
        assert value is None or Decimal(value) == 0
    assert valuation_data["accounts"] == []
    assert valuation["odoo"]["record_ids"] == []

    purchase_match = _invoke(
        alias,
        "purchase_bill.matching.inspect",
        {"bill_id": bill_id},
        case="unmatched-purchase-bill",
    )
    purchase_data = purchase_match["data"]
    assert purchase_data["id"] == bill_id
    assert purchase_data["move_type"] == "in_invoice"
    assert purchase_data["purchase_order_ids"] == []
    assert purchase_data["is_purchase_matched"] is False
    assert purchase_data["lines"]
    assert any(
        line["purchase_line"] is None and line["unmatched_queue"] is True
        for line in purchase_data["lines"]
    )
    assert purchase_match["odoo"]["record_ids"] == [bill_id]

    sale_link = _invoke(
        alias,
        "sale_invoice.stock_link.inspect",
        {"invoice_id": invoice_id},
        case="unlinked-sale-invoice",
    )
    sale_data = sale_link["data"]
    assert sale_data["id"] == invoice_id
    assert sale_data["move_type"] == "out_invoice"
    assert sale_data["lines"]
    assert all(line["sale_order_line_ids"] == [] for line in sale_data["lines"])
    assert all(line["stock_moves"] == [] for line in sale_data["lines"])
    assert sale_data["stock_move_ids"] == []
    assert sale_data["account_move_ids"] == []
    assert sale_link["odoo"]["record_ids"] == [invoice_id]
