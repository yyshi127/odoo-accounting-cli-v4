"""Shared live smoke coverage for the current read-capability batch.

The synthetic ``v4-dev`` and ``v4-e2e`` fixtures currently contain no
``product.product`` records.  The product-profile case therefore proves only
the explicit ``record_not_found`` path; it does not claim live coverage of a
successful accounting-profile mapping.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

from odoo_accounting_cli_v4.registry import load_registry

_CONFIG_ENV = "ODOO_ACCOUNTING_CLI_V4_CONFIG"
_ALIASES = ("v4-dev", "v4-e2e")
_COMPANY_ID = 1
_MISSING_PRODUCT_ID = 2_147_483_647
_MODELS = {
    "currency.convert": "res.currency",
    "validation.journal_entry.check": "account.move",
    "report.general_ledger": "account.report",
    "report.partner_ledger": "account.report",
    "report.aged_receivable": "account.report",
    "report.aged_payable": "account.report",
    "report.journal": "account.report",
    "report.executive_summary": "account.report",
    "bank.transaction.list": "account.bank.statement.line",
    "product.accounting_profile.get": "product.product",
}
_CASES = (
    pytest.param(
        "currency.convert",
        {
            "amount": "1",
            "from_currency_id": 1,
            "to_currency_id": 6,
            "date": "2025-01-15",
        },
        0,
        id="currency-convert",
    ),
    pytest.param(
        "validation.journal_entry.check",
        {"entry_id": 1},
        0,
        id="journal-entry-check",
    ),
    pytest.param(
        "report.general_ledger",
        {
            "date_from": "2025-01-01",
            "date_to": "2025-01-31",
            "limit": 100,
            "cursor": None,
        },
        0,
        id="general-ledger",
    ),
    pytest.param(
        "report.partner_ledger",
        {
            "date_from": "2025-01-01",
            "date_to": "2025-01-31",
            "limit": 100,
            "cursor": None,
        },
        0,
        id="partner-ledger",
    ),
    pytest.param(
        "report.aged_receivable",
        {"as_of": "2025-01-31", "limit": 100, "cursor": None},
        0,
        id="aged-receivable",
    ),
    pytest.param(
        "report.aged_payable",
        {"as_of": "2025-01-31", "limit": 100, "cursor": None},
        0,
        id="aged-payable",
    ),
    pytest.param(
        "report.journal",
        {
            "date_from": "2025-01-01",
            "date_to": "2025-01-31",
            "limit": 100,
            "cursor": None,
        },
        0,
        id="journal-report",
    ),
    pytest.param(
        "report.executive_summary",
        {
            "date_from": "2025-01-01",
            "date_to": "2025-01-31",
            "limit": 100,
            "cursor": None,
        },
        0,
        id="executive-summary",
    ),
    pytest.param(
        "bank.transaction.list",
        {"limit": 100, "cursor": None},
        0,
        id="bank-transaction-list",
    ),
    pytest.param(
        "product.accounting_profile.get",
        {"product_id": _MISSING_PRODUCT_ID},
        4,
        id="product-profile-missing",
    ),
)


def _invoke(
    alias: str,
    capability_id: str,
    parameters: dict,
    *,
    expected_exit: int,
) -> dict:
    project_root = Path(__file__).resolve().parents[2]
    request_id = str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"odacv4:{alias}:{_COMPANY_ID}:{capability_id}:batch-live-smoke",
        )
    )
    request = {
        "schema_version": "v1",
        "request_id": request_id,
        "context": {
            "database": alias,
            "company_id": _COMPANY_ID,
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

    assert completed.returncode == expected_exit, completed.stdout
    assert completed.stderr == ""
    assert len(completed.stdout.splitlines()) == 1
    document = json.loads(completed.stdout)
    assert document["schema_version"] == "v1"
    assert document["capability"] == capability_id
    assert document["request_id"] == request_id
    assert document["odoo"]["database"] == alias
    assert document["odoo"]["company_id"] == _COMPANY_ID
    assert document["odoo"]["model"] == _MODELS[capability_id]
    registry.validate_instance(
        f"schemas/v1/{capability_id}.response.schema.json", document
    )
    return document


@pytest.mark.integration
@pytest.mark.parametrize("alias", _ALIASES)
@pytest.mark.parametrize(
    ("capability_id", "parameters", "expected_exit"),
    _CASES,
)
def test_read_capability_batch_uses_live_odoo_and_specialized_schemas(
    alias: str,
    capability_id: str,
    parameters: dict,
    expected_exit: int,
) -> None:
    if not os.environ.get(_CONFIG_ENV):
        pytest.skip(f"{_CONFIG_ENV} is not configured")

    document = _invoke(
        alias,
        capability_id,
        parameters,
        expected_exit=expected_exit,
    )
    if expected_exit == 0:
        assert document["success"] is True
        assert document["status"] == "verified"
        assert document["data"] is not None
        assert document["error"] is None
        return

    assert capability_id == "product.accounting_profile.get"
    assert document["success"] is False
    assert document["status"] == "unavailable"
    assert document["data"] is None
    assert document["error"]["code"] == "record_not_found"
    assert document["error"]["retryable"] is False
    assert document["odoo"]["record_ids"] == []
