"""Live read-only verification for configured-user accounting access."""

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
_COMPANIES = (1, 2)


def _invoke(alias: str, company_id: int) -> dict:
    project_root = Path(__file__).resolve().parents[2]
    request_id = str(
        uuid.uuid5(
            uuid.NAMESPACE_URL, f"odacv4:{alias}:{company_id}:accounting-access"
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
        "schemas/v1/user.accounting_access.inspect.request.schema.json", request
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
            "user.accounting_access.inspect",
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
        "schemas/v1/user.accounting_access.inspect.response.schema.json", document
    )
    assert document["request_id"] == request_id
    return document


@pytest.mark.integration
@pytest.mark.parametrize("alias", _ALIASES)
@pytest.mark.parametrize("company_id", _COMPANIES)
def test_accounting_access_uses_the_real_odoo_user_and_acl(
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
        "model": "res.users",
        "record_ids": [5],
    }
    data = document["data"]
    assert data["user"] == {
        "id": 5,
        "login": "odacv4_g5_accountant",
        "name": "ODACV4 G5 Accountant",
        "active": True,
        "company_ids": [1, 2],
    }
    assert data["company_id"] == company_id
    assert data["groups"] == [
        {"xml_id": "base.group_user", "member": True},
        {"xml_id": "account.group_account_readonly", "member": True},
        {"xml_id": "account.group_account_invoice", "member": True},
        {"xml_id": "account.group_account_user", "member": True},
        {"xml_id": "account.group_account_manager", "member": False},
    ]
    acl = {item["model"]: item for item in data["model_acl"]}
    assert set(acl) == {
        "account.account",
        "account.journal",
        "account.move",
        "account.move.line",
        "account.report",
        "account.tax",
    }
    assert all(item["read"] is True for item in acl.values())
    for model in ("account.move", "account.move.line"):
        assert all(acl[model][operation] is True for operation in ("create", "write", "unlink"))
    for model in set(acl) - {"account.move", "account.move.line"}:
        assert all(acl[model][operation] is False for operation in ("create", "write", "unlink"))
