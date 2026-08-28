"""Guarded live smoke for the fixed-asset capability batch."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

import pytest

from odoo_accounting_cli_v4.registry import load_registry

_CONFIG_ENV = "ODOO_ACCOUNTING_CLI_V4_CONFIG"
_ALLOW_ENV = "ODACV4_ALLOW_WRITE_SMOKE"
_ALIASES = ("v4-dev", "v4-e2e")
_PHYSICAL_DATABASES = {
    "v4-dev": "odoo_cli_v4_dev",
    "v4-e2e": "odoo_cli_v4_e2e",
}
_COMPANY_ID = 1
_USER_LOGIN = "odacv4_g5_accountant"
_USER_ID = 5
_CURRENCY_ID = 6
_ASSET_ACCOUNT_ID = 78
_DEPRECIATION_ACCOUNT_ID = 80
_EXPENSE_ACCOUNT_ID = 146
_GENERAL_JOURNAL_ID = 11
_DATE_FROM = "2026-01-01"
_DATE_TO = "2026-12-31"
_ASSET_COLUMNS = [
    "acquisition_date",
    "method",
    "duration_rate",
    "assets_date_from",
    "assets_plus",
    "assets_minus",
    "assets_date_to",
    "depre_date_from",
    "depre_plus",
    "depre_minus",
    "depre_date_to",
    "balance",
]


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _enabled_runtime_config() -> Path:
    if os.environ.get(_ALLOW_ENV) != "1":
        pytest.skip(f"set {_ALLOW_ENV}=1 to authorize isolated write smoke")
    raw_path = os.environ.get(_CONFIG_ENV)
    if not raw_path:
        pytest.skip(f"{_CONFIG_ENV} is not configured")
    path = Path(raw_path)
    if not path.is_file():
        pytest.skip(f"{_CONFIG_ENV} does not name an existing file")

    document = json.loads(path.read_text(encoding="utf-8"))
    aliases = document.get("aliases")
    assert isinstance(aliases, dict)
    assert set(aliases) == set(_ALIASES)
    assert {
        alias: aliases[alias].get("database") for alias in _ALIASES
    } == _PHYSICAL_DATABASES
    assert all(
        aliases[alias].get("companies", {}).get(str(_COMPANY_ID)) == [_USER_LOGIN]
        for alias in _ALIASES
    )
    return path


def _request(
    alias: str,
    capability_id: str,
    parameters: dict[str, Any],
    *,
    run_id: str,
    case: str,
) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "request_id": str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"odacv4:asset-live:{run_id}:{alias}:{capability_id}:{case}",
            )
        ),
        "context": {
            "database": alias,
            "company_id": _COMPANY_ID,
            "user_login": _USER_LOGIN,
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": parameters,
    }


def _invoke(
    capability_id: str,
    request: dict[str, Any],
    command: list[str],
) -> tuple[int, dict[str, Any]]:
    root = _project_root()
    registry = load_registry()
    registry.validate_instance(
        f"schemas/v1/{capability_id}.request.schema.json", request
    )

    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = os.pathsep.join(
        part for part in (str(root / "src"), environment.get("PYTHONPATH")) if part
    )
    completed = subprocess.run(
        [sys.executable, "-m", "odoo_accounting_cli_v4", *command],
        cwd=root,
        env=environment,
        input=json.dumps(request, sort_keys=True, separators=(",", ":")),
        text=True,
        capture_output=True,
        check=False,
        timeout=300,
    )
    assert completed.stderr == ""
    assert len(completed.stdout.splitlines()) == 1
    document = json.loads(completed.stdout)
    registry.validate_instance(
        f"schemas/v1/{capability_id}.response.schema.json", document
    )
    assert document["schema_version"] == "v1"
    assert document["request_id"] == request["request_id"]
    assert document["capability"] == capability_id
    return completed.returncode, document


def _success(
    alias: str,
    capability_id: str,
    parameters: dict[str, Any],
    *,
    run_id: str,
    case: str,
) -> dict[str, Any]:
    request = _request(alias, capability_id, parameters, run_id=run_id, case=case)
    returncode, document = _invoke(
        capability_id,
        request,
        ["read", capability_id, "--request", "-"],
    )
    assert returncode == 0
    assert document["success"] is True
    assert document["status"] == "verified"
    assert document["warnings"] == []
    assert document["error"] is None
    assert document["odoo"]["database"] == alias
    assert document["odoo"]["company_id"] == _COMPANY_ID
    assert document["odoo"]["user_id"] == _USER_ID
    return document


def _write(
    alias: str,
    capability_id: str,
    parameters: dict[str, Any],
    *,
    idempotency_key: str,
    run_id: str,
    case: str,
) -> tuple[int, dict[str, Any]]:
    request = _request(alias, capability_id, parameters, run_id=run_id, case=case)
    return _invoke(
        capability_id,
        request,
        [
            "write",
            "run",
            capability_id,
            "--request",
            "-",
            "--idempotency-key",
            idempotency_key,
            "--confirm",
            capability_id,
        ],
    )


def _assert_created_asset(document: dict[str, Any], alias: str, key: str) -> None:
    assert document["success"] is True
    assert document["status"] == "verified"
    assert document["error"] is None
    assert document["warnings"] == [
        {
            "code": "capability_degraded",
            "reason_code": "odoo_native_asset_idempotency_field_unavailable",
        }
    ]
    assert document["odoo"]["database"] == alias
    assert document["odoo"]["company_id"] == _COMPANY_ID
    assert document["odoo"]["user_id"] == _USER_ID
    assert document["odoo"]["model"] == "account.asset"
    assert document["audit"]["idempotency_key"] == key


def _create_asset(alias: str, run_id: str) -> tuple[int, str]:
    base_name = f"ODACV4 Asset {run_id} {alias}"
    key = f"asset.create:{run_id}:{alias}"
    parameters = {
        "name": base_name,
        "acquisition_date": _DATE_FROM,
        "original_value": "1200",
        "salvage_value": "0",
        "account_asset_id": _ASSET_ACCOUNT_ID,
        "account_depreciation_id": _DEPRECIATION_ACCOUNT_ID,
        "account_depreciation_expense_id": _EXPENSE_ACCOUNT_ID,
        "journal_id": _GENERAL_JOURNAL_ID,
        "method": "linear",
        "method_number": 12,
        "method_period": "1",
        "method_progress_factor": "0.3",
        "prorata_computation_type": "none",
    }
    first_code, first = _write(
        alias,
        "asset.create",
        parameters,
        idempotency_key=key,
        run_id=run_id,
        case="create",
    )
    second_code, second = _write(
        alias,
        "asset.create",
        parameters,
        idempotency_key=key,
        run_id=run_id,
        case="create",
    )
    assert first_code == second_code == 0
    _assert_created_asset(first, alias, key)
    _assert_created_asset(second, alias, key)
    assert first["data"]["idempotent_replay"] is False
    assert second["data"]["idempotent_replay"] is True
    assert first["data"]["result"] == second["data"]["result"]

    result = first["data"]["result"]
    assert result["model"] == "account.asset"
    assert isinstance(result["id"], int) and result["id"] > 0
    assert re.fullmatch(
        re.escape(base_name) + r" \[ODACV4:[0-9a-f]{64}\]", result["name"]
    )
    assert result["state"] == "draft"
    assert result["company_id"] == _COMPANY_ID
    assert result["move_type"] is None
    assert result["source_id"] is None
    assert result["line_ids"] == []
    assert result["partial_reconcile_ids"] == []
    assert result["full_reconcile_id"] is None
    assert result["reconciled"] is False
    assert first["odoo"]["record_ids"] == [result["id"]]
    return result["id"], base_name


def _assert_asset_reads(alias: str, run_id: str, asset_id: int, name: str) -> None:
    search = _success(
        alias,
        "asset.search",
        {"query": name, "states": ["draft"], "limit": 10, "cursor": None},
        run_id=run_id,
        case="search-created",
    )
    assert len(search["data"]["items"]) == 1
    assert search["data"]["items"][0]["id"] == asset_id
    assert search["data"]["items"][0]["state"] == "draft"
    assert search["data"]["has_more"] is False
    assert search["data"]["next_cursor"] is None
    assert search["odoo"]["model"] == "account.asset"
    assert search["odoo"]["record_ids"] == [asset_id]

    detail = _success(
        alias,
        "asset.get",
        {"asset_id": asset_id},
        run_id=run_id,
        case="get-created",
    )
    data = detail["data"]
    assert data["id"] == asset_id
    assert data["state"] == "draft"
    assert data["active"] is True
    assert data["company_id"] == _COMPANY_ID
    assert data["currency"] == {"id": _CURRENCY_ID, "code": "CNY"}
    assert data["accounts"]["asset"]["id"] == _ASSET_ACCOUNT_ID
    assert data["accounts"]["depreciation"]["id"] == _DEPRECIATION_ACCOUNT_ID
    assert data["accounts"]["expense"]["id"] == _EXPENSE_ACCOUNT_ID
    assert data["journal"]["id"] == _GENERAL_JOURNAL_ID
    assert data["journal"]["code"] == "MISC"
    assert data["values"] == {
        "original": "1200",
        "salvage": "0",
        "depreciable": "1200",
        "book": "1200",
        "residual": "1200",
    }
    assert data["method"] == {
        "type": "linear",
        "number": 12,
        "period": "1",
        "progress_factor": "0.3",
        "prorata_computation_type": "none",
    }
    assert data["dates"]["acquisition"] == _DATE_FROM
    assert data["dates"]["disposal"] is None
    assert detail["odoo"]["record_ids"] == [asset_id]

    schedule = _success(
        alias,
        "asset.depreciation_schedule.get",
        {"asset_id": asset_id},
        run_id=run_id,
        case="draft-schedule",
    )
    assert schedule["data"]["asset"]["id"] == asset_id
    assert schedule["data"]["asset"]["state"] == "draft"
    assert schedule["data"]["moves"] == []
    assert schedule["odoo"]["record_ids"] == [asset_id]


def _assert_asset_report(alias: str, run_id: str) -> None:
    document = _success(
        alias,
        "report.asset",
        {
            "date_from": _DATE_FROM,
            "date_to": _DATE_TO,
            "limit": 100,
            "cursor": None,
        },
        run_id=run_id,
        case="asset-report",
    )
    data = document["data"]
    assert data["report"]["key"] == "asset"
    assert data["date"] == {"from": _DATE_FROM, "to": _DATE_TO}
    assert data["currency"]["id"] == _CURRENCY_ID
    assert data["currency"]["code"] == "CNY"
    assert data["basis"] == "posted_entries"
    assert [column["expression_label"] for column in data["columns"]] == (
        _ASSET_COLUMNS
    )
    assert data["columns"][-1]["label"] == "Book Value"
    assert data["columns"][0]["figure_type"] == "string"
    assert isinstance(data["lines"], list)
    assert data["has_more"] is False
    assert data["next_cursor"] is None
    assert document["odoo"]["model"] == "account.report"
    assert document["odoo"]["record_ids"] == []


def _assert_validate_blocker_rolls_back(alias: str, run_id: str, asset_id: int) -> None:
    key = f"asset.validate:{asset_id}"
    returncode, document = _write(
        alias,
        "asset.validate",
        {"asset_id": asset_id},
        idempotency_key=key,
        run_id=run_id,
        case="known-server-blocker",
    )
    assert returncode == 6
    assert document["success"] is False
    assert document["status"] == "failed"
    assert document["data"] is None
    assert document["warnings"] == []
    assert document["error"]["code"] == "odoo_write_error"
    assert document["error"]["message"] == "The Odoo accounting write failed."
    assert document["error"]["details"] == {}
    assert document["error"]["retryable"] is False
    assert document["odoo"] == {
        "database": None,
        "company_id": None,
        "user_id": None,
        "model": None,
        "record_ids": [],
    }
    assert document["audit"]["idempotency_key"] == key

    detail = _success(
        alias,
        "asset.get",
        {"asset_id": asset_id},
        run_id=run_id,
        case="validate-rollback-detail",
    )
    assert detail["data"]["state"] == "draft"
    schedule = _success(
        alias,
        "asset.depreciation_schedule.get",
        {"asset_id": asset_id},
        run_id=run_id,
        case="validate-rollback-schedule",
    )
    assert schedule["data"]["asset"]["state"] == "draft"
    assert schedule["data"]["moves"] == []


@pytest.mark.integration
def test_asset_batch_runs_one_guarded_chain_per_isolated_alias() -> None:
    _enabled_runtime_config()
    run_id = str(uuid.uuid4())
    for alias in _ALIASES:
        asset_id, base_name = _create_asset(alias, run_id)
        _assert_asset_reads(alias, run_id, asset_id, base_name)
        _assert_asset_report(alias, run_id)
        _assert_validate_blocker_rolls_back(alias, run_id, asset_id)
