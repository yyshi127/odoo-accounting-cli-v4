"""Read-only live proof for fixed Odoo 19 company currency rates."""

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
_CAPABILITY = "currency.rate.list"
_ALIASES = ("v4-dev", "v4-e2e")
_EXPECTED = {
    1: {
        "ids": [3, 2, 1],
        "company_currency": {"id": 6, "code": "CNY"},
    },
    2: {
        "ids": [6, 5, 4],
        "company_currency": {"id": 37, "code": "SGD"},
    },
}
_DATES = ["2025-02-01", "2025-01-15", "2025-01-01"]
_INVERSE = ["1.37", "1.36", "1.35"]


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
            "timezone": os.environ.get("ODACV4_LIVE_TIMEZONE", "Asia/Shanghai"),
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
    assert document["success"] is True
    assert document["status"] == "verified"
    assert document["capability"] == _CAPABILITY
    assert document["request_id"] == request_id
    assert document["odoo"]["database"] == alias
    assert document["odoo"]["company_id"] == company_id
    assert document["odoo"]["user_id"] == 5
    assert document["odoo"]["model"] == "res.currency.rate"
    registry.validate_instance(
        f"schemas/v1/{_CAPABILITY}.response.schema.json", document
    )
    return document


def _assert_item(item: dict, *, company_id: int, position: int) -> None:
    assert item["id"] == _EXPECTED[company_id]["ids"][position]
    assert item["date"] == _DATES[position]
    assert item["currency"] == {"id": 1, "code": "USD"}
    assert item["company_currency"] == _EXPECTED[company_id]["company_currency"]
    assert item["requested_company_id"] == company_id
    assert item["source_company_id"] == company_id
    technical = Decimal(item["technical_rate"])
    direct = Decimal(item["foreign_units_per_company_unit"])
    inverse = Decimal(item["company_units_per_foreign_unit"])
    assert technical.is_finite() and technical > 0
    assert direct.is_finite() and direct > 0
    assert inverse == Decimal(_INVERSE[position])
    assert abs((direct * inverse) - Decimal(1)) < Decimal("0.000000000000001")


@pytest.mark.integration
@pytest.mark.parametrize("alias", _ALIASES)
@pytest.mark.parametrize("company_id", [1, 2])
def test_currency_rates_use_real_root_scoped_keyset_pages(
    alias: str, company_id: int
) -> None:
    if not os.environ.get(_CONFIG_ENV):
        pytest.skip(f"{_CONFIG_ENV} is not configured")

    first = _invoke(alias, company_id, {"limit": 2}, case="page-1")
    assert first["odoo"]["record_ids"] == _EXPECTED[company_id]["ids"][:2]
    assert first["data"]["has_more"] is True
    assert isinstance(first["data"]["next_cursor"], str)
    for position, item in enumerate(first["data"]["items"]):
        _assert_item(item, company_id=company_id, position=position)

    second = _invoke(
        alias,
        company_id,
        {"limit": 2, "cursor": first["data"]["next_cursor"]},
        case="page-2",
    )
    assert second["odoo"]["record_ids"] == _EXPECTED[company_id]["ids"][2:]
    assert second["data"]["has_more"] is False
    assert second["data"]["next_cursor"] is None
    _assert_item(second["data"]["items"][0], company_id=company_id, position=2)


@pytest.mark.integration
@pytest.mark.parametrize("alias", _ALIASES)
@pytest.mark.parametrize("company_id", [1, 2])
def test_currency_rate_filters_are_applied_by_real_odoo(
    alias: str, company_id: int
) -> None:
    if not os.environ.get(_CONFIG_ENV):
        pytest.skip(f"{_CONFIG_ENV} is not configured")

    exact = _invoke(
        alias,
        company_id,
        {
            "date_from": "2025-01-15",
            "date_to": "2025-01-15",
            "currency_id": 1,
            "limit": 10,
        },
        case="exact-filter",
    )
    assert exact["odoo"]["record_ids"] == [_EXPECTED[company_id]["ids"][1]]
    assert exact["data"]["has_more"] is False
    _assert_item(exact["data"]["items"][0], company_id=company_id, position=1)
