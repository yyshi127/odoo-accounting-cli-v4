"""Live read-only verification for the fixed balance-sheet report."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

from odoo_accounting_cli_v4.registry import load_registry


_CONFIG_ENV = "ODOO_ACCOUNTING_CLI_V4_CONFIG"
_ALIASES = ("v4-dev", "v4-e2e")
_COMPANIES = (1, 2)
_CURRENCY_BY_COMPANY = {1: "CNY", 2: "SGD"}
_MONEY = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")


def _invoke(alias: str, company_id: int) -> dict:
    project_root = Path(__file__).resolve().parents[2]
    request_id = str(
        uuid.uuid5(uuid.NAMESPACE_URL, f"odacv4:{alias}:{company_id}:balance-sheet")
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
            "timezone": os.environ.get("ODACV4_LIVE_TIMEZONE", "Asia/Shanghai"),
        },
        "parameters": {"as_of": "2025-01-31", "limit": 100, "cursor": None},
    }
    registry = load_registry()
    registry.validate_instance(
        "schemas/v1/report.balance_sheet.request.schema.json", request
    )
    environment = os.environ.copy()
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
            "report.balance_sheet",
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
    assert completed.returncode == 0, completed.stdout
    assert completed.stderr == ""
    assert len(completed.stdout.splitlines()) == 1
    document = json.loads(completed.stdout)
    registry.validate_instance(
        "schemas/v1/report.balance_sheet.response.schema.json", document
    )
    assert document["request_id"] == request_id
    return document


@pytest.mark.integration
@pytest.mark.parametrize("alias", _ALIASES)
@pytest.mark.parametrize("company_id", _COMPANIES)
def test_balance_sheet_uses_the_real_odoo_readonly_report_handler(
    alias: str, company_id: int
) -> None:
    if not os.environ.get(_CONFIG_ENV):
        pytest.skip(f"{_CONFIG_ENV} is not configured")

    document = _invoke(alias, company_id)
    assert document["success"] is True
    assert document["status"] == "verified"
    assert document["error"] is None
    assert document["odoo"] == {
        "database": alias,
        "company_id": company_id,
        "user_id": 5,
        "model": "account.report",
        "record_ids": [],
    }
    data = document["data"]
    assert data["report"]["key"] == "balance_sheet"
    assert data["date"] == {"from": "2025-01-01", "to": "2025-01-31"}
    assert data["currency"]["code"] == _CURRENCY_BY_COMPANY[company_id]
    assert data["basis"] == "posted_entries"
    assert data["columns"] == [
        {"index": 0, "label": "Balance", "expression_label": "balance"}
    ]
    assert len(data["lines"]) == 21
    assert len({line["id"] for line in data["lines"]}) == 21
    assert data["has_more"] is False
    assert data["next_cursor"] is None
    assert all(
        value is None or _MONEY.fullmatch(value)
        for line in data["lines"]
        for value in line["values"]
    )
    top = {line["name"]: line["values"] for line in data["lines"] if line["parent_id"] is None}
    assert top == {
        "ASSETS": ["-123.45"],
        "LIABILITIES": ["0"],
        "EQUITY": ["-123.45"],
        "LIABILITIES + EQUITY": ["-123.45"],
    }
