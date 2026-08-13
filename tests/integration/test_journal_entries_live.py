"""Live journal-entry reads against the deterministic two-company fixture.

The fixture contains one journal entry per company, so these tests verify a
terminal search page (``has_more=false``).  They do not claim live cursor
traversal coverage; cursor traversal is covered by the contract/unit tests.
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
_ENTRY_BY_COMPANY = {1: 1, 2: 2}
_MARKER_BY_COMPANY = {
    1: "ODACV4-G5-POSTED-CN",
    2: "ODACV4-G5-POSTED-SG",
}
_CURRENCY_BY_COMPANY = {1: "CNY", 2: "SGD"}
_MONEY = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")


def _invoke(
    alias: str,
    company_id: int,
    capability_id: str,
    parameters: dict,
    *,
    case: str,
    expected_exit: int = 0,
) -> dict:
    project_root = Path(__file__).resolve().parents[2]
    request_id = str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"odacv4:{alias}:{company_id}:{capability_id}:{case}",
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
        input=json.dumps(request),
        text=True,
        capture_output=True,
        check=False,
        timeout=240,
    )

    assert completed.returncode == expected_exit, completed.stdout
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
    assert document["odoo"]["database"] == alias
    assert document["odoo"]["company_id"] == company_id
    assert isinstance(document["odoo"]["user_id"], int)
    assert document["odoo"]["user_id"] > 0
    assert document["odoo"]["model"] == "account.move"
    assert document["odoo"]["record_ids"] == record_ids


def _assert_money(*values: str) -> None:
    assert all(isinstance(value, str) and _MONEY.fullmatch(value) for value in values)


@pytest.mark.integration
@pytest.mark.parametrize("alias", _ALIASES)
@pytest.mark.parametrize("company_id", _COMPANIES)
def test_journal_entry_search_and_get_use_the_real_read_only_bridge(
    alias: str, company_id: int
) -> None:
    if not os.environ.get(_CONFIG_ENV):
        pytest.skip(f"{_CONFIG_ENV} is not configured")

    entry_id = _ENTRY_BY_COMPANY[company_id]
    marker = _MARKER_BY_COMPANY[company_id]
    basic = _invoke(
        alias,
        company_id,
        "journal_entry.search",
        {"limit": 10, "cursor": None},
        case="basic",
    )
    items = basic["data"]["items"]
    assert len(items) == 1
    item = items[0]
    _assert_success_metadata(
        basic, alias=alias, company_id=company_id, record_ids=[entry_id]
    )
    assert basic["data"]["has_more"] is False
    assert basic["data"]["next_cursor"] is None
    assert [(row["date"], row["id"]) for row in items] == sorted(
        ((row["date"], row["id"]) for row in items), reverse=True
    )
    assert item["id"] == entry_id
    assert item["date"] == "2025-01-15"
    assert item["state"] == "posted"
    assert item["ref"] == marker
    assert item["company_id"] == company_id
    assert item["currency"]["code"] == _CURRENCY_BY_COMPANY[company_id]
    assert item["partner"] is None
    assert item["debit"] == "123.45"
    assert item["credit"] == "123.45"
    assert item["balance"] == "0"
    _assert_money(item["debit"], item["credit"], item["balance"])

    filtered = _invoke(
        alias,
        company_id,
        "journal_entry.search",
        {
            "limit": 10,
            "cursor": None,
            "date_from": "2025-01-15",
            "date_to": "2025-01-15",
            "states": ["posted"],
            "journal_id": item["journal"]["id"],
            "query": marker,
        },
        case="combined-filters",
    )
    _assert_success_metadata(
        filtered, alias=alias, company_id=company_id, record_ids=[entry_id]
    )
    assert filtered["data"] == basic["data"]

    empty = _invoke(
        alias,
        company_id,
        "journal_entry.search",
        {"limit": 10, "cursor": None, "states": ["draft"]},
        case="empty",
    )
    _assert_success_metadata(empty, alias=alias, company_id=company_id, record_ids=[])
    assert empty["data"] == {
        "items": [],
        "has_more": False,
        "next_cursor": None,
    }

    fetched = _invoke(
        alias,
        company_id,
        "journal_entry.get",
        {"entry_id": entry_id},
        case="present",
    )
    _assert_success_metadata(
        fetched, alias=alias, company_id=company_id, record_ids=[entry_id]
    )
    entry = fetched["data"]
    for key in (
        "id",
        "name",
        "date",
        "state",
        "ref",
        "journal",
        "company_id",
        "currency",
        "partner",
    ):
        assert entry[key] == item[key]
    assert len(entry["lines"]) == 2
    assert [(line["sequence"], line["id"]) for line in entry["lines"]] == sorted(
        (line["sequence"], line["id"]) for line in entry["lines"]
    )
    for line in entry["lines"]:
        _assert_money(
            line["debit"],
            line["credit"],
            line["balance"],
            line["amount_currency"],
        )
        assert line["company_currency"] == entry["currency"]
        assert line["account"] is not None
    totals = entry["totals"]
    _assert_money(totals["debit"], totals["credit"], totals["balance"])
    assert totals == {"debit": "123.45", "credit": "123.45", "balance": "0"}
    assert sum(Decimal(line["debit"]) for line in entry["lines"]) == Decimal(
        totals["debit"]
    )
    assert sum(Decimal(line["credit"]) for line in entry["lines"]) == Decimal(
        totals["credit"]
    )
    assert sum(Decimal(line["balance"]) for line in entry["lines"]) == Decimal(
        totals["balance"]
    )

    cross_company_id = _ENTRY_BY_COMPANY[1 if company_id == 2 else 2]
    cross_company = _invoke(
        alias,
        company_id,
        "journal_entry.get",
        {"entry_id": cross_company_id},
        case="cross-company",
        expected_exit=4,
    )
    absent = _invoke(
        alias,
        company_id,
        "journal_entry.get",
        {"entry_id": 2_147_483_647},
        case="absent",
        expected_exit=4,
    )
    for document in (cross_company, absent):
        assert document["success"] is False
        assert document["status"] == "unavailable"
        assert document["data"] is None
        assert document["error"]["code"] == "record_not_found"
        assert document["error"]["retryable"] is False
        assert document["odoo"]["record_ids"] == []
    assert cross_company["error"] == absent["error"]
