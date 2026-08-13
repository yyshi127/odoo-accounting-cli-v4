"""Live read-only verification for fixed accounting environment inspections."""

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
_COMPANY_FACTS = {
    1: {
        "name": "ODACV4 G5 China",
        "currency": {"id": 6, "code": "CNY"},
        "country": {"id": 48, "code": "CN", "name": "China"},
        "chart_template": "cn_oscg",
        "prefixes": {"bank": "1002", "cash": "1001", "transfer": "1012"},
        "suspense": {"id": 153, "code": "1004"},
        "pos_receivable": {"id": 58, "code": "1124"},
    },
    2: {
        "name": "ODACV4 G5 Singapore",
        "currency": {"id": 37, "code": "SGD"},
        "country": {"id": 197, "code": "SG", "name": "Singapore"},
        "chart_template": "sg",
        "prefixes": {
            "bank": "10141",
            "cash": "10140",
            "transfer": "101100",
        },
        "suspense": {"id": 295, "code": "101412"},
        "pos_receivable": {"id": 199, "code": "100030"},
    },
}
_MODULES = ["account", "account_reports", "base"]
_MODELS = [
    "account.account",
    "account.journal",
    "account.move",
    "account.move.line",
    "account.report",
    "account.tax",
    "ir.module.module",
    "res.company",
    "res.users",
]


def _invoke(capability_id: str, alias: str, company_id: int) -> dict:
    project_root = Path(__file__).resolve().parents[2]
    request_id = str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"odacv4:{alias}:{company_id}:{capability_id}",
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
        "parameters": {},
    }
    registry = load_registry()
    registry.validate_instance(
        f"schemas/v1/{capability_id}.request.schema.json", request
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
    assert completed.returncode == 0, completed.stdout
    assert completed.stderr == ""
    assert len(completed.stdout.splitlines()) == 1
    document = json.loads(completed.stdout)
    registry.validate_instance(
        f"schemas/v1/{capability_id}.response.schema.json", document
    )
    assert document["request_id"] == request_id
    assert document["success"] is True
    assert document["status"] == "verified"
    assert document["error"] is None
    return document


@pytest.mark.integration
@pytest.mark.parametrize("alias", _ALIASES)
@pytest.mark.parametrize("company_id", sorted(_COMPANY_FACTS))
def test_company_accounting_configuration_matches_the_synthetic_company(
    alias: str, company_id: int
) -> None:
    if not os.environ.get(_CONFIG_ENV):
        pytest.skip(f"{_CONFIG_ENV} is not configured")

    document = _invoke("company.accounting_configuration.inspect", alias, company_id)
    facts = _COMPANY_FACTS[company_id]
    assert document["odoo"] == {
        "database": alias,
        "company_id": company_id,
        "user_id": 5,
        "model": "res.company",
        "record_ids": [company_id],
    }
    data = document["data"]
    assert data["company"] == {"id": company_id, "name": facts["name"]}
    assert data["currency"] == facts["currency"]
    assert data["country"] == facts["country"]
    assert data["fiscal_country"] == facts["country"]
    assert data["chart_template"] == facts["chart_template"]
    assert data["tax_calculation_rounding_method"] == "round_globally"
    assert data["fiscal_year_end"] == {"month": 12, "day": 31}
    assert data["anglo_saxon_accounting"] is False
    assert data["account_code_prefixes"] == facts["prefixes"]
    assert {
        key: data["suspense_account"][key] for key in ("id", "code")
    } == facts["suspense"]
    assert {
        key: data["pos_receivable_account"][key] for key in ("id", "code")
    } == facts["pos_receivable"]
    assert data["opening"] == {"date": None, "move_id": None}


@pytest.mark.integration
@pytest.mark.parametrize("alias", _ALIASES)
@pytest.mark.parametrize("company_id", sorted(_COMPANY_FACTS))
def test_accounting_environment_reports_fixed_modules_models_and_read_only_state(
    alias: str, company_id: int
) -> None:
    if not os.environ.get(_CONFIG_ENV):
        pytest.skip(f"{_CONFIG_ENV} is not configured")

    document = _invoke("diagnostic.accounting_environment.inspect", alias, company_id)
    assert document["odoo"] == {
        "database": alias,
        "company_id": company_id,
        "user_id": 5,
        "model": "ir.module.module",
        "record_ids": [],
    }
    data = document["data"]
    assert data["company"] == {
        "id": company_id,
        "name": _COMPANY_FACTS[company_id]["name"],
    }
    assert data["user"] == {"id": 5, "login": "odacv4_g5_accountant"}
    assert [item["name"] for item in data["modules"]] == _MODULES
    assert all(item["state"] == "installed" for item in data["modules"])
    assert [item["model"] for item in data["models"]] == _MODELS
    assert all(item["available"] is True for item in data["models"])
    assert all(item["read"] is True for item in data["models"])
    assert data["transaction_read_only"] is True
