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


def _invoke(alias: str, *, limit: int, cursor: str | None, page: int) -> dict:
    project_root = Path(__file__).resolve().parents[2]
    request = {
        "schema_version": "v1",
        "request_id": str(
            uuid.uuid5(uuid.NAMESPACE_URL, f"odacv4:{alias}:account-list:{page}")
        ),
        "context": {
            "database": alias,
            "company_id": int(os.environ.get("ODACV4_LIVE_COMPANY_ID", "1")),
            "user_login": os.environ.get(
                "ODACV4_LIVE_USER_LOGIN", "odacv4_g5_accountant"
            ),
            "language": os.environ.get("ODACV4_LIVE_LANGUAGE", "en_US"),
            "timezone": os.environ.get(
                "ODACV4_LIVE_TIMEZONE", "Asia/Shanghai"
            ),
        },
        "parameters": {"limit": limit, "cursor": cursor},
    }
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
            "account.account.list",
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
    assert document["success"] is True
    assert document["status"] == "verified"
    assert document["capability"] == "account.account.list"
    assert document["request_id"] == request["request_id"]
    assert document["odoo"]["database"] == request["context"]["database"]
    assert document["odoo"]["company_id"] == request["context"]["company_id"]
    assert isinstance(document["odoo"]["user_id"], int)
    assert document["odoo"]["user_id"] > 0
    items = document["data"]["items"]
    assert items
    assert 1 <= len(items) <= limit
    assert [(item["code"], item["id"]) for item in items] == sorted(
        (item["code"], item["id"]) for item in items
    )
    assert all(request["context"]["company_id"] in item["company_ids"] for item in items)
    load_registry().validate_instance(
        "schemas/v1/account.account.list.response.schema.json", document
    )
    return document


@pytest.mark.integration
@pytest.mark.parametrize("alias", ["v4-dev", "v4-e2e"])
def test_account_account_list_uses_the_real_read_only_bridge(alias: str) -> None:
    if not os.environ.get(_CONFIG_ENV):
        pytest.skip(f"{_CONFIG_ENV} is not configured")

    first = _invoke(alias, limit=2, cursor=None, page=1)
    assert first["data"]["has_more"] is True
    assert isinstance(first["data"]["next_cursor"], str)

    second = _invoke(
        alias,
        limit=2,
        cursor=first["data"]["next_cursor"],
        page=2,
    )
    first_keys = [(item["code"], item["id"]) for item in first["data"]["items"]]
    second_keys = [(item["code"], item["id"]) for item in second["data"]["items"]]
    assert set(first_keys).isdisjoint(second_keys)
    assert first_keys + second_keys == sorted(first_keys + second_keys)
