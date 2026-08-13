"""Live gate for Odoo's default Journal Items to reconcile candidates.

Fixture v1 intentionally provides exactly three default candidates per
company: bank suspense (``other``), trade payable, and trade receivable.
The two configured databases and both fixture companies are immutable test
targets; this test performs only read actions through the public CLI.
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
_CAPABILITY = "reconciliation.candidates.list"
_ALIASES = ("v4-dev", "v4-e2e")
_COMPANIES = (1, 2)
_CODE = {1: "CN", 2: "SG"}
_CURRENCY = {1: "CNY", 2: "SGD"}
_EXPECTED_IDS = {
    "v4-dev": {1: [37, 36, 33], 2: [45, 44, 41]},
    "v4-e2e": {1: [11, 10, 7], 2: [19, 18, 15]},
}
_EXPECTED_RECEIVABLE = {1: ("113", "63"), 2: ("109", "59")}
_MONEY = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
_ITEM_KEYS = {
    "id",
    "date",
    "invoice_date",
    "date_maturity",
    "state",
    "move",
    "label",
    "account",
    "partner",
    "journal",
    "company_id",
    "company_currency",
    "currency",
    "balance",
    "amount_currency",
    "amount_residual",
    "amount_residual_currency",
    "matching_number",
    "reconciliation_model",
}


def _invoke(
    alias: str,
    company_id: int,
    parameters: dict,
    *,
    case: str,
) -> dict:
    project_root = Path(__file__).resolve().parents[2]
    request_id = str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"odacv4:{alias}:{company_id}:{_CAPABILITY}:live:{case}",
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
        f"schemas/v1/{_CAPABILITY}.request.schema.json", request
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
            _CAPABILITY,
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
    assert document["capability"] == _CAPABILITY
    assert document["request_id"] == request_id
    registry.validate_instance(
        f"schemas/v1/{_CAPABILITY}.response.schema.json", document
    )
    return document


def _assert_metadata(
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
    assert document["odoo"]["user_id"] == 5
    assert document["odoo"]["model"] == "account.move.line"
    assert document["odoo"]["record_ids"] == record_ids


def _money(value: str, expected: str | None = None) -> Decimal:
    assert isinstance(value, str) and _MONEY.fullmatch(value)
    result = Decimal(value)
    assert result.is_finite()
    if expected is not None:
        assert result == Decimal(expected)
    return result


def _kind(item: dict) -> str:
    account_type = item["account"]["account_type"]
    if account_type == "asset_receivable":
        return "receivable"
    if account_type == "liability_payable":
        return "payable"
    return "other"


def _assert_item(
    item: dict,
    *,
    company_id: int,
    expected_id: int,
    expected_kind: str,
) -> None:
    assert set(item) == _ITEM_KEYS
    assert item["id"] == expected_id
    assert item["company_id"] == company_id
    assert item["state"] == "posted"
    assert item["reconciliation_model"] is None
    assert item["company_currency"] == item["currency"]
    assert item["currency"]["code"] == _CURRENCY[company_id]
    assert isinstance(item["date"], str)
    assert set(item["move"]) == {"id", "name", "move_type", "ref"}
    assert isinstance(item["move"]["id"], int) and item["move"]["id"] > 0
    assert item["move"]["name"]
    assert set(item["account"]) == {"id", "code", "name", "account_type"}
    assert item["account"]["code"]
    assert item["account"]["name"]
    assert set(item["journal"]) == {"id", "code", "name", "type"}
    assert item["journal"]["code"]
    assert item["journal"]["name"]
    assert item["partner"] is not None
    assert set(item["partner"]) == {"id", "name"}
    assert item["partner"]["name"]
    assert _kind(item) == expected_kind

    balance = _money(item["balance"])
    amount_currency = _money(item["amount_currency"])
    residual = _money(item["amount_residual"])
    residual_currency = _money(item["amount_residual_currency"])
    assert residual != 0
    assert amount_currency == balance
    assert residual_currency == residual

    code = _CODE[company_id]
    if expected_kind == "other":
        assert item["date"] == "2025-01-25"
        assert item["invoice_date"] is None
        assert item["date_maturity"] == "2025-01-25"
        assert item["move"]["move_type"] == "entry"
        assert item["move"]["ref"] == "INV/2025/00001"
        assert item["label"] == "Manual Payment: INV/2025/00001"
        assert item["account"]["account_type"] == "asset_current"
        assert item["account"]["name"] == "Bank Suspense Account"
        assert item["journal"]["code"] == "BNK1"
        assert item["journal"]["type"] == "bank"
        _money(item["balance"], "50")
        _money(item["amount_residual"], "50")
        assert item["matching_number"] is None
    elif expected_kind == "payable":
        assert item["date"] == item["invoice_date"] == "2025-01-21"
        assert item["date_maturity"] == "2025-02-21"
        assert item["move"]["move_type"] == "in_invoice"
        assert item["move"]["ref"] == f"ODACV4-FX1-{code}-BILL-TAX-INCLUDED"
        assert item["label"] is None
        assert item["journal"]["code"] == "BILL"
        assert item["journal"]["type"] == "purchase"
        _money(item["balance"], "-113")
        _money(item["amount_residual"], "-113")
        assert item["matching_number"] is None
    else:
        expected_balance, expected_residual = _EXPECTED_RECEIVABLE[company_id]
        assert item["date"] == item["invoice_date"] == "2025-01-20"
        assert item["date_maturity"] == "2025-02-20"
        assert item["move"]["move_type"] == "out_invoice"
        assert item["move"]["ref"] == f"ODACV4-FX1-{code}-INVOICE-TAX-EXCLUDED"
        assert item["label"]
        assert item["journal"]["code"] == "INV"
        assert item["journal"]["type"] == "sale"
        _money(item["balance"], expected_balance)
        _money(item["amount_residual"], expected_residual)
        assert isinstance(item["matching_number"], str)
        assert item["matching_number"].startswith("P")


def _assert_page(
    document: dict,
    *,
    alias: str,
    company_id: int,
    record_ids: list[int],
) -> list[dict]:
    _assert_metadata(
        document,
        alias=alias,
        company_id=company_id,
        record_ids=record_ids,
    )
    items = document["data"]["items"]
    assert [item["id"] for item in items] == record_ids
    return items


@pytest.mark.integration
@pytest.mark.parametrize("alias", _ALIASES)
@pytest.mark.parametrize("company_id", _COMPANIES)
def test_reconciliation_candidates_live_fixture_pages_filters_and_isolation(
    alias: str,
    company_id: int,
) -> None:
    if not os.environ.get(_CONFIG_ENV):
        pytest.skip(f"{_CONFIG_ENV} is not configured")

    expected_ids = _EXPECTED_IDS[alias][company_id]
    expected_kinds = ("other", "payable", "receivable")

    cursor = None
    paged_items: list[dict] = []
    for index, expected_id in enumerate(expected_ids):
        page = _invoke(
            alias,
            company_id,
            {"limit": 1, "cursor": cursor},
            case=f"page-{index + 1}",
        )
        items = _assert_page(
            page,
            alias=alias,
            company_id=company_id,
            record_ids=[expected_id],
        )
        assert len(items) == 1
        _assert_item(
            items[0],
            company_id=company_id,
            expected_id=expected_id,
            expected_kind=expected_kinds[index],
        )
        paged_items.extend(items)
        if index < 2:
            assert page["data"]["has_more"] is True
            assert isinstance(page["data"]["next_cursor"], str)
            cursor = page["data"]["next_cursor"]
        else:
            assert page["data"]["has_more"] is False
            assert page["data"]["next_cursor"] is None

    assert [item["id"] for item in paged_items] == expected_ids
    assert [item["date"] for item in paged_items] == sorted(
        [item["date"] for item in paged_items], reverse=True
    )

    all_items = _invoke(
        alias,
        company_id,
        {"limit": 3, "cursor": None},
        case="all-three",
    )
    items = _assert_page(
        all_items,
        alias=alias,
        company_id=company_id,
        record_ids=expected_ids,
    )
    assert all_items["data"]["has_more"] is False
    assert all_items["data"]["next_cursor"] is None
    assert items == paged_items

    query_cases = (
        ("label", "Manual Payment:", expected_ids[0]),
        ("move-name", "PBNK1/2025/00001", expected_ids[0]),
        ("move-ref", "BILL-TAX-INCLUDED", expected_ids[1]),
        ("partner-name", "Vendor", expected_ids[1]),
    )
    for case, query, expected_id in query_cases:
        document = _invoke(
            alias,
            company_id,
            {"limit": 3, "cursor": None, "query": query},
            case=f"query-{case}",
        )
        query_items = _assert_page(
            document,
            alias=alias,
            company_id=company_id,
            record_ids=[expected_id],
        )
        assert len(query_items) == 1
        assert document["data"]["has_more"] is False
        assert document["data"]["next_cursor"] is None

    for kind, expected_id in zip(expected_kinds, expected_ids):
        document = _invoke(
            alias,
            company_id,
            {"limit": 3, "cursor": None, "account_kinds": [kind]},
            case=f"kind-{kind}",
        )
        kind_items = _assert_page(
            document,
            alias=alias,
            company_id=company_id,
            record_ids=[expected_id],
        )
        assert _kind(kind_items[0]) == kind

    payable = items[1]
    combined = _invoke(
        alias,
        company_id,
        {
            "limit": 3,
            "cursor": None,
            "date_from": payable["date"],
            "date_to": payable["date"],
            "states": ["posted"],
            "account_id": payable["account"]["id"],
            "partner_id": payable["partner"]["id"],
            "journal_id": payable["journal"]["id"],
            "account_kinds": ["payable"],
            "query": payable["move"]["ref"],
        },
        case="all-structured-filters",
    )
    assert _assert_page(
        combined,
        alias=alias,
        company_id=company_id,
        record_ids=[expected_ids[1]],
    ) == [payable]

    other_company = 1 if company_id == 2 else 2
    other = _invoke(
        alias,
        other_company,
        {"limit": 3, "cursor": None, "account_kinds": ["other"]},
        case=f"isolation-source-for-{company_id}",
    )
    other_items = _assert_page(
        other,
        alias=alias,
        company_id=other_company,
        record_ids=[_EXPECTED_IDS[alias][other_company][0]],
    )
    foreign = other_items[0]
    isolated = _invoke(
        alias,
        company_id,
        {
            "limit": 3,
            "cursor": None,
            "account_id": foreign["account"]["id"],
            "partner_id": foreign["partner"]["id"],
            "journal_id": foreign["journal"]["id"],
            "account_kinds": ["other"],
        },
        case=f"cross-company-from-{other_company}",
    )
    assert _assert_page(
        isolated,
        alias=alias,
        company_id=company_id,
        record_ids=[],
    ) == []
    assert isolated["data"] == {
        "items": [],
        "has_more": False,
        "next_cursor": None,
    }
