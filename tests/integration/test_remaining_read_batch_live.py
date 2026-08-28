"""One shared live smoke for the remaining-read capability batch."""

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
_RANGE = {
    "date_from": "2025-01-01",
    "date_to": "2025-01-31",
    "limit": 100,
    "cursor": None,
}
_SINGLE = {"as_of": "2025-01-31", "limit": 100, "cursor": None}
_CASES = (
    pytest.param("report.deferred_expense", 1, _RANGE, "account.report", id="deferred-expense"),
    pytest.param("report.deferred_revenue", 1, _RANGE, "account.report", id="deferred-revenue"),
    pytest.param(
        "report.multicurrency_revaluation",
        1,
        _SINGLE,
        "account.report",
        id="multicurrency-revaluation",
    ),
    pytest.param(
        "report.china.balance_sheet",
        1,
        _SINGLE,
        "account.report",
        id="china-balance-sheet",
    ),
    pytest.param(
        "report.china.profit_and_loss",
        1,
        _RANGE,
        "account.report",
        id="china-profit-and-loss",
    ),
    pytest.param(
        "report.china.cash_flow",
        1,
        _RANGE,
        "account.report",
        id="china-cash-flow",
    ),
    pytest.param(
        "report.singapore.gst",
        2,
        _RANGE,
        "account.report",
        id="singapore-gst",
    ),
    pytest.param(
        "fiscal_position.resolve",
        1,
        {"partner_id": 1},
        "account.fiscal.position",
        id="fiscal-position",
    ),
    pytest.param(
        "diagnostic.journal_integrity.inspect",
        1,
        {},
        "res.company",
        id="journal-integrity",
    ),
)


def _invoke(
    alias: str,
    capability_id: str,
    company_id: int,
    parameters: dict,
    model: str,
) -> dict:
    project_root = Path(__file__).resolve().parents[2]
    request_id = str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"odacv4:{alias}:{company_id}:{capability_id}:remaining-read-live",
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
            "timezone": os.environ.get("ODACV4_LIVE_TIMEZONE", "Asia/Shanghai"),
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
    assert document["success"] is True
    assert document["status"] == "verified"
    assert document["capability"] == capability_id
    assert document["request_id"] == request_id
    assert document["odoo"]["database"] == alias
    assert document["odoo"]["company_id"] == company_id
    assert document["odoo"]["model"] == model
    registry.validate_instance(
        f"schemas/v1/{capability_id}.response.schema.json", document
    )
    return document


@pytest.mark.integration
@pytest.mark.parametrize("alias", _ALIASES)
@pytest.mark.parametrize(
    ("capability_id", "company_id", "parameters", "model"), _CASES
)
def test_remaining_read_batch_uses_live_odoo(
    alias: str,
    capability_id: str,
    company_id: int,
    parameters: dict,
    model: str,
) -> None:
    if not os.environ.get(_CONFIG_ENV):
        pytest.skip(f"{_CONFIG_ENV} is not configured")

    document = _invoke(alias, capability_id, company_id, parameters, model)
    if capability_id.startswith("report."):
        assert document["data"]["report"]["key"]
    elif capability_id == "fiscal_position.resolve":
        assert document["data"]["partner_id"] == 1
        assert document["data"]["fiscal_position"] is None
    else:
        assert capability_id == "diagnostic.journal_integrity.inspect"
        assert isinstance(document["data"]["results"], list)
