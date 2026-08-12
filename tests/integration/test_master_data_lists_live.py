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
_CAPABILITIES = (
    "journal.list",
    "tax.list",
    "payment_term.list",
    "currency.list",
)


def _sort_key(capability_id: str, item: dict) -> tuple:
    if capability_id == "journal.list":
        return item["sequence"], item["type"], item["code"], item["id"]
    if capability_id in {"tax.list", "payment_term.list"}:
        return item["sequence"], item["id"]
    return (0 if item["active"] else 1), item["code"], item["id"]


def _invoke(
    alias: str,
    capability_id: str,
    *,
    limit: int,
    cursor: str | None,
    page: int,
) -> dict:
    project_root = Path(__file__).resolve().parents[2]
    request = {
        "schema_version": "v1",
        "request_id": str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"odacv4:{alias}:{capability_id}:{page}",
            )
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
    assert document["success"] is True
    assert document["status"] == "verified"
    assert document["capability"] == capability_id
    assert document["request_id"] == request["request_id"]
    assert document["odoo"]["database"] == alias
    assert document["odoo"]["company_id"] == request["context"]["company_id"]
    assert document["odoo"]["user_id"] > 0
    items = document["data"]["items"]
    assert 1 <= len(items) <= limit
    assert [_sort_key(capability_id, item) for item in items] == sorted(
        _sort_key(capability_id, item) for item in items
    )
    assert document["odoo"]["record_ids"] == [item["id"] for item in items]
    load_registry().validate_instance(
        f"schemas/v1/{capability_id}.response.schema.json", document
    )
    return document


@pytest.mark.integration
@pytest.mark.parametrize("alias", ["v4-dev", "v4-e2e"])
@pytest.mark.parametrize("capability_id", _CAPABILITIES)
def test_master_data_lists_use_the_real_read_only_bridge(
    alias: str, capability_id: str
) -> None:
    if not os.environ.get(_CONFIG_ENV):
        pytest.skip(f"{_CONFIG_ENV} is not configured")

    first = _invoke(alias, capability_id, limit=2, cursor=None, page=1)
    assert first["data"]["has_more"] is True
    assert isinstance(first["data"]["next_cursor"], str)
    second = _invoke(
        alias,
        capability_id,
        limit=2,
        cursor=first["data"]["next_cursor"],
        page=2,
    )
    first_items = first["data"]["items"]
    second_items = second["data"]["items"]
    assert {item["id"] for item in first_items}.isdisjoint(
        item["id"] for item in second_items
    )
    keys = [_sort_key(capability_id, item) for item in first_items + second_items]
    assert keys == sorted(keys)
