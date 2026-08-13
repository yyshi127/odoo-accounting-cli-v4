"""Live open-item reads against accounting fixture v1 only.

Fixture v1 contains exactly one open receivable and one open payable item per
company.  These tests therefore prove honest limit-one terminal pages, but do
not claim live cursor traversal or multi-page coverage.  Cursor traversal is a
contract/unit-test responsibility until a versioned fixture contains at least
two open items on the same side.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import uuid
from decimal import Decimal
from pathlib import Path

import pytest

from odoo_accounting_cli_v4.registry import load_registry


_CONFIG_ENV = "ODOO_ACCOUNTING_CLI_V4_CONFIG"
_ALIASES = ("v4-dev", "v4-e2e")
_COMPANIES = (1, 2)
_CODE = {1: "CN", 2: "SG"}
_CURRENCY = {1: "CNY", 2: "SGD"}
_CAPABILITIES = (
    "receivable.open_items.list",
    "payable.open_items.list",
)
_MONEY = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")


def _invoke(
    alias: str,
    company_id: int,
    capability_id: str,
    parameters: dict,
    *,
    case: str,
) -> dict:
    project_root = Path(__file__).resolve().parents[2]
    request_id = str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"odacv4:{alias}:{company_id}:{capability_id}:open-items-live:{case}",
        )
    )
    request = {
        "schema_version": "v1",
        "request_id": request_id,
        "context": {
            "database": alias,
            "company_id": company_id,
            "user_login": os.environ.get(
                "ODACV4_LIVE_USER_LOGIN", "odacv4_g5_accountant"
            ),
            "language": os.environ.get("ODACV4_LIVE_LANGUAGE", "en_US"),
            "timezone": os.environ.get(
                "ODACV4_LIVE_TIMEZONE", "Asia/Shanghai"
            ),
        },
        "parameters": parameters,
    }
    registry = load_registry()
    registry.validate_instance(
        f"schemas/v1/{capability_id}.request.schema.json", request
    )

    environment = os.environ.copy()
    environment[_CONFIG_ENV] = os.environ[_CONFIG_ENV]
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = os.pathsep.join(
        part
        for part in (str(project_root / "src"), environment.get("PYTHONPATH"))
        if part
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
        cwd=project_root,
        env=environment,
        input=json.dumps(request, sort_keys=True, separators=(",", ":")),
        text=True,
        capture_output=True,
        check=False,
        timeout=240,
    )

    assert completed.returncode == 0, completed.stdout
    assert completed.stderr == ""
    assert len(completed.stdout.splitlines()) == 1
    document = json.loads(completed.stdout)
    assert document["schema_version"] == "v1"
    assert document["capability"] == capability_id
    assert document["request_id"] == request_id
    registry.validate_instance(
        f"schemas/v1/{capability_id}.response.schema.json", document
    )
    return document


def _assert_success_metadata(
    document: dict,
    *,
    alias: str,
    company_id: int,
    record_ids: list[int],
) -> None:
    assert document["success"] is True
    assert document["status"] == "verified"
    assert document["error"] is None
    assert document["warnings"] == []
    assert document["odoo"]["database"] == alias
    assert document["odoo"]["company_id"] == company_id
    assert isinstance(document["odoo"]["user_id"], int)
    assert document["odoo"]["user_id"] > 0
    assert document["odoo"]["model"] == "account.move.line"
    assert document["odoo"]["record_ids"] == record_ids


def _assert_money(value: str, expected: str | None = None) -> None:
    assert isinstance(value, str) and _MONEY.fullmatch(value)
    if expected is not None:
        assert Decimal(value) == Decimal(expected)


def _fixture_expectation(company_id: int, side: str) -> dict[str, str | None]:
    if side == "receivable":
        total = "113" if company_id == 1 else "109"
        residual = "63" if company_id == 1 else "59"
        return {
            "date": "2025-01-20",
            "due_date": "2025-02-20",
            "move_type": "out_invoice",
            "role": "CUSTOMER",
            "ref_kind": "INVOICE-TAX-EXCLUDED",
            "debit": total,
            "credit": "0",
            "balance": total,
            "amount_currency": total,
            "amount_residual": residual,
            "amount_residual_currency": residual,
        }
    return {
        "date": "2025-01-21",
        "due_date": "2025-02-21",
        "move_type": "in_invoice",
        "role": "VENDOR",
        "ref_kind": "BILL-TAX-INCLUDED",
        "debit": "0",
        "credit": "113",
        "balance": "-113",
        "amount_currency": "-113",
        "amount_residual": "-113",
        "amount_residual_currency": "-113",
    }


def _assert_fixture_item(item: dict, *, company_id: int, side: str) -> None:
    expected = _fixture_expectation(company_id, side)
    code = _CODE[company_id]
    expected_ref = f"ODACV4-FX1-{code}-{expected['ref_kind']}"

    assert item["side"] == side
    assert item["date"] == expected["date"]
    assert item["due_date"] == expected["due_date"]
    assert item["ref"] == expected_ref
    assert item["company_id"] == company_id
    assert item["move"]["move_type"] == expected["move_type"]
    assert item["move"]["state"] == "posted"
    assert item["move"]["name"]
    assert item["journal"]["code"]
    assert item["journal"]["name"]
    assert item["partner"] is not None
    assert item["partner"]["reference"] == (
        f"ODACV4-FX1-{code}-{expected['role']}"
    )
    assert item["account"]["account_type"] == (
        "asset_receivable" if side == "receivable" else "liability_payable"
    )
    assert item["account"]["non_trade"] is False
    assert item["currency"]["code"] == _CURRENCY[company_id]
    assert item["company_currency"] == item["currency"]
    assert item["reconciled"] is False
    if side == "receivable":
        assert isinstance(item["matching_number"], str)
        assert item["matching_number"].startswith("P")
    else:
        assert item["matching_number"] is None

    for field in (
        "debit",
        "credit",
        "balance",
        "amount_currency",
        "amount_residual",
        "amount_residual_currency",
    ):
        _assert_money(item[field], expected[field])
    assert Decimal(item["debit"]) - Decimal(item["credit"]) == Decimal(
        item["balance"]
    )
    assert (Decimal(item["amount_residual"]) > 0) is (side == "receivable")


@pytest.mark.integration
@pytest.mark.parametrize("alias", _ALIASES)
@pytest.mark.parametrize("company_id", _COMPANIES)
@pytest.mark.parametrize("capability_id", _CAPABILITIES)
def test_open_items_use_real_company_scoped_terminal_pages_and_filters(
    alias: str, company_id: int, capability_id: str
) -> None:
    if not os.environ.get(_CONFIG_ENV):
        pytest.skip(f"{_CONFIG_ENV} is not configured")

    side = "receivable" if capability_id.startswith("receivable") else "payable"
    expected = _fixture_expectation(company_id, side)
    basic = _invoke(
        alias,
        company_id,
        capability_id,
        {"limit": 1, "cursor": None},
        case="terminal-limit-one",
    )
    items = basic["data"]["items"]
    assert len(items) == 1
    item = items[0]
    _assert_success_metadata(
        basic, alias=alias, company_id=company_id, record_ids=[item["id"]]
    )
    assert basic["data"]["has_more"] is False
    assert basic["data"]["next_cursor"] is None
    _assert_fixture_item(item, company_id=company_id, side=side)

    combined_filters = {
        "limit": 1,
        "cursor": None,
        "date_from": expected["date"],
        "date_to": expected["date"],
        "due_date_from": expected["due_date"],
        "due_date_to": expected["due_date"],
        "partner_id": item["partner"]["id"],
        "account_id": item["account"]["id"],
        "journal_id": item["journal"]["id"],
        "currency_id": item["currency"]["id"],
        "query": item["ref"],
    }
    filtered = _invoke(
        alias,
        company_id,
        capability_id,
        combined_filters,
        case="all-filters",
    )
    _assert_success_metadata(
        filtered, alias=alias, company_id=company_id, record_ids=[item["id"]]
    )
    assert filtered["data"] == basic["data"]

    other_company = 1 if company_id == 2 else 2
    other_ref = (
        f"ODACV4-FX1-{_CODE[other_company]}-{expected['ref_kind']}"
    )
    cross_company_query = _invoke(
        alias,
        company_id,
        capability_id,
        {"limit": 1, "cursor": None, "query": other_ref},
        case="cross-company-query",
    )
    _assert_success_metadata(
        cross_company_query, alias=alias, company_id=company_id, record_ids=[]
    )
    assert cross_company_query["data"] == {
        "items": [],
        "has_more": False,
        "next_cursor": None,
    }
