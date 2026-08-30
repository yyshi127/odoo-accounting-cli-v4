"""Shared read-only live smoke for accounting supporting-object reads."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

import pytest

from odoo_accounting_cli_v4.registry import load_registry

_CONFIG_ENV = "ODOO_ACCOUNTING_CLI_V4_CONFIG"
_ALLOW_ENV = "ODACV4_ALLOW_ACCOUNTING_SUPPORTING_READ_SMOKE"
_ALIASES = ("v4-dev", "v4-e2e")
_DATABASES = {
    "v4-dev": "odoo_cli_v4_dev",
    "v4-e2e": "odoo_cli_v4_e2e",
}
_COMPANY_ID = 1
_USER_ID = 5
_USER_LOGIN = "odacv4_g5_accountant"
_MISSING_ID = 2_147_483_647

_SEARCH_GET_CASES = (
    ("asset.group.search", "asset.group.get", "asset_group_id"),
    (
        "report.budget_definition.search",
        "report.budget_definition.get",
        "budget_definition_id",
    ),
    (
        "report.budget_item.search",
        "report.budget_item.get",
        "budget_item_id",
    ),
    ("tax.unit.search", "tax.unit.get", "tax_unit_id"),
    (
        "account.return.account_status.search",
        "account.return.account_status.get",
        "account_status_id",
    ),
)
_TARGET_CAPABILITIES = frozenset(
    capability_id
    for search_id, get_id, _id_parameter in _SEARCH_GET_CASES
    for capability_id in (search_id, get_id)
)
_MODELS = {
    "user.accounting_access.inspect": "res.users",
    "asset.group.search": "account.asset.group",
    "asset.group.get": "account.asset.group",
    "report.budget_definition.search": "account.report.budget",
    "report.budget_definition.get": "account.report.budget",
    "report.budget_item.search": "account.report.budget.item",
    "report.budget_item.get": "account.report.budget.item",
    "tax.unit.search": "account.tax.unit",
    "tax.unit.get": "account.tax.unit",
    "account.return.account_status.search": "account.audit.account.status",
    "account.return.account_status.get": "account.audit.account.status",
}


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _enabled_runtime() -> None:
    if os.environ.get(_ALLOW_ENV) != "1":
        pytest.skip(f"set {_ALLOW_ENV}=1 to run the isolated read-only smoke")
    raw = os.environ.get(_CONFIG_ENV)
    if not raw:
        pytest.skip(f"{_CONFIG_ENV} is not configured")
    path = Path(raw)
    if not path.is_file():
        pytest.skip(f"{_CONFIG_ENV} does not name an existing file")
    document = json.loads(path.read_text(encoding="utf-8"))
    aliases = document.get("aliases")
    assert isinstance(aliases, dict) and set(aliases) == set(_ALIASES)
    assert {alias: aliases[alias].get("database") for alias in _ALIASES} == _DATABASES
    assert all(
        aliases[alias].get("companies", {}).get(str(_COMPANY_ID)) == [_USER_LOGIN]
        for alias in _ALIASES
    )


def _request(
    alias: str,
    capability_id: str,
    parameters: dict[str, Any],
    *,
    case: str,
) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "request_id": str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"odacv4:{alias}:{_COMPANY_ID}:{capability_id}:supporting:{case}",
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
    alias: str,
    capability_id: str,
    parameters: dict[str, Any],
    *,
    case: str,
    expected_exit: int = 0,
) -> dict[str, Any]:
    root = _root()
    request = _request(alias, capability_id, parameters, case=case)
    registry = load_registry()
    descriptor = registry.describe(capability_id)
    assert descriptor["access"] == "read"
    registry.validate_instance(descriptor["schemas"]["request"], request)

    environment = os.environ.copy()
    environment[_CONFIG_ENV] = os.environ[_CONFIG_ENV]
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = os.pathsep.join(
        part for part in (str(root / "src"), environment.get("PYTHONPATH")) if part
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
        cwd=root,
        env=environment,
        input=json.dumps(request, sort_keys=True, separators=(",", ":")),
        text=True,
        capture_output=True,
        check=False,
        timeout=240,
    )

    assert completed.returncode == expected_exit, completed.stdout + completed.stderr
    assert completed.stderr == ""
    assert len(completed.stdout.splitlines()) == 1
    document = json.loads(completed.stdout)
    registry.validate_instance(descriptor["schemas"]["response"], document)
    assert document["schema_version"] == "v1"
    assert document["request_id"] == request["request_id"]
    assert document["capability"] == capability_id
    assert document["odoo"]["database"] == alias
    assert document["odoo"]["company_id"] == _COMPANY_ID
    assert document["odoo"]["model"] == _MODELS[capability_id]
    if expected_exit == 0:
        assert document["success"] is True
        assert document["status"] == "verified"
        assert document["data"] is not None
        assert document["error"] is None
        assert document["odoo"]["user_id"] == _USER_ID
    else:
        assert expected_exit == 4
        assert document["success"] is False
        assert document["status"] == "unavailable"
        assert document["data"] is None
        assert document["error"]["code"] == "record_not_found"
        assert document["error"]["retryable"] is False
        assert document["odoo"]["record_ids"] == []
    return document


def _get_selected_or_missing(
    alias: str,
    capability_id: str,
    id_parameter: str,
    items: list[dict[str, Any]],
) -> None:
    if items:
        selected_id = items[0]["id"]
        document = _invoke(
            alias,
            capability_id,
            {id_parameter: selected_id},
            case="get-selected",
        )
        assert document["data"]["id"] == selected_id
        assert document["odoo"]["record_ids"] == [selected_id]
        return
    _invoke(
        alias,
        capability_id,
        {id_parameter: _MISSING_ID},
        case="missing-fixture",
        expected_exit=4,
    )


def _assert_ordinary_accounting_user(alias: str) -> None:
    document = _invoke(
        alias,
        "user.accounting_access.inspect",
        {},
        case="ordinary-user-guard",
    )
    assert document["data"]["user"]["id"] == _USER_ID
    assert document["data"]["user"]["login"] == _USER_LOGIN
    groups = {item["xml_id"]: item["member"] for item in document["data"]["groups"]}
    assert groups["account.group_account_readonly"] is True
    assert groups["account.group_account_user"] is True
    assert groups["account.group_account_manager"] is False


@pytest.mark.integration
def test_accounting_supporting_reads_use_uid5_on_both_isolated_databases() -> None:
    _enabled_runtime()

    for alias in _ALIASES:
        covered: set[str] = set()
        _assert_ordinary_accounting_user(alias)

        for search_id, get_id, id_parameter in _SEARCH_GET_CASES:
            search = _invoke(
                alias,
                search_id,
                {"limit": 100, "cursor": None},
                case="search",
            )
            items = search["data"]["items"]
            assert search["odoo"]["record_ids"] == [item["id"] for item in items]
            covered.add(search_id)

            _get_selected_or_missing(alias, get_id, id_parameter, items)
            covered.add(get_id)

        assert covered == _TARGET_CAPABILITIES
