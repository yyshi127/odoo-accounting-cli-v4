"""Live configured-company discovery against both synthetic V4 databases."""

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
_CAPABILITY = "company.accounting_context.list"
_EXPECTED = [
    {
        "id": 1,
        "name": "ODACV4 G5 China",
        "sequence": 0,
        "active": True,
        "currency": {"id": 6, "code": "CNY", "decimal_places": 2},
        "country": {"id": 48, "code": "CN", "name": "China"},
        "fiscal_country": {"id": 48, "code": "CN", "name": "China"},
        "chart_template": "cn_oscg",
        "tax_calculation_rounding_method": "round_globally",
        "fiscal_year_end": {"month": 12, "day": 31},
    },
    {
        "id": 2,
        "name": "ODACV4 G5 Singapore",
        "sequence": 10,
        "active": True,
        "currency": {"id": 37, "code": "SGD", "decimal_places": 2},
        "country": {"id": 197, "code": "SG", "name": "Singapore"},
        "fiscal_country": {
            "id": 197,
            "code": "SG",
            "name": "Singapore",
        },
        "chart_template": "sg",
        "tax_calculation_rounding_method": "round_globally",
        "fiscal_year_end": {"month": 12, "day": 31},
    },
]


def _invoke(alias: str, company_id: int, cursor: str | None, page: int) -> dict:
    project_root = Path(__file__).resolve().parents[2]
    request = {
        "schema_version": "v1",
        "request_id": str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"odacv4:{alias}:{company_id}:{_CAPABILITY}:{page}",
            )
        ),
        "context": {
            "database": alias,
            "company_id": company_id,
            "user_login": "odacv4_g5_accountant",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": {"limit": 1, "cursor": cursor},
    }
    registry = load_registry()
    registry.validate_instance(
        f"schemas/v1/{_CAPABILITY}.request.schema.json", request
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
            _CAPABILITY,
            "--request",
            "-",
        ],
        cwd=project_root,
        env=environment,
        input=json.dumps(request, sort_keys=True, separators=(",", ":")),
        text=True,
        capture_output=True,
        timeout=240,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stderr == ""
    assert completed.stdout.endswith("\n")
    assert len(completed.stdout.splitlines()) == 1
    document = json.loads(completed.stdout)
    registry.validate_instance(
        f"schemas/v1/{_CAPABILITY}.response.schema.json", document
    )
    assert document["success"] is True
    assert document["status"] == "verified"
    assert document["odoo"]["database"] == alias
    assert document["odoo"]["company_id"] == company_id
    assert document["odoo"]["user_id"] == 5
    assert document["odoo"]["model"] == "res.company"
    assert document["odoo"]["record_ids"] == [document["data"]["items"][0]["id"]]
    return document


@pytest.mark.integration
@pytest.mark.parametrize("alias", ("v4-dev", "v4-e2e"))
@pytest.mark.parametrize("company_id", (1, 2))
def test_configured_company_contexts_are_complete_scoped_and_stably_paginated(
    alias: str, company_id: int
) -> None:
    if not os.environ.get(_CONFIG_ENV):
        pytest.skip(f"{_CONFIG_ENV} is required for the live integration test")

    first = _invoke(alias, company_id, None, 1)
    assert first["data"]["has_more"] is True
    assert isinstance(first["data"]["next_cursor"], str)
    second = _invoke(alias, company_id, first["data"]["next_cursor"], 2)
    assert second["data"]["has_more"] is False
    assert second["data"]["next_cursor"] is None

    items = first["data"]["items"] + second["data"]["items"]
    assert [item["id"] for item in items] == [1, 2]
    assert len({item["id"] for item in items}) == 2
    for item, expected in zip(items, _EXPECTED, strict=True):
        observed = dict(item)
        assert observed.pop("current") is (item["id"] == company_id)
        assert observed == expected
