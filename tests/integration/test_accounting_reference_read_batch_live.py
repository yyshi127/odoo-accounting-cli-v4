"""Shared read-only live smoke for accounting reference/configuration reads."""

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
_ALIASES = ("v4-dev", "v4-e2e")
_COMPANY_ID = 1

_TARGET_CAPABILITIES = frozenset(
    {
        "account.group.list",
        "journal.configuration.inspect",
        "tax.repartition_line.list",
        "tax.repartition_line.get",
        "reconciliation.model.line.list",
        "reconciliation.model.line.get",
        "bank.list",
        "bank.get",
        "report.catalog.list",
        "report.catalog.get",
    }
)

_MODELS = {
    "account.group.list": "account.group",
    "journal.list": "account.journal",
    "journal.configuration.inspect": "account.journal",
    "tax.repartition_line.list": "account.tax.repartition.line",
    "tax.repartition_line.get": "account.tax.repartition.line",
    "reconciliation.model.line.list": "account.reconcile.model.line",
    "reconciliation.model.line.get": "account.reconcile.model.line",
    "bank.list": "res.bank",
    "bank.get": "res.bank",
    "report.catalog.list": "account.report",
    "report.catalog.get": "account.report",
}

_LIST_GET_CASES = (
    (
        "tax.repartition_line.list",
        {"limit": 100, "cursor": None},
        "tax.repartition_line.get",
        "tax_repartition_line_id",
    ),
    (
        "reconciliation.model.line.list",
        {"limit": 100, "cursor": None},
        "reconciliation.model.line.get",
        "reconciliation_model_line_id",
    ),
    (
        "bank.list",
        {"limit": 100, "cursor": None},
        "bank.get",
        "bank_id",
    ),
    (
        "report.catalog.list",
        {"limit": 100, "cursor": None},
        "report.catalog.get",
        "report_id",
    ),
)


def test_accounting_reference_batch_matrix_is_closed() -> None:
    exercised = {"account.group.list", "journal.configuration.inspect"}
    for list_id, _parameters, get_id, _id_parameter in _LIST_GET_CASES:
        exercised.update({list_id, get_id})

    assert exercised == _TARGET_CAPABILITIES


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


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
                f"odacv4:{alias}:{_COMPANY_ID}:{capability_id}:reference-live:{case}",
            )
        ),
        "context": {
            "database": alias,
            "company_id": _COMPANY_ID,
            "user_login": os.environ.get(
                "ODACV4_LIVE_USER_LOGIN", "odacv4_g5_accountant"
            ),
            "language": os.environ.get("ODACV4_LIVE_LANGUAGE", "en_US"),
            "timezone": os.environ.get("ODACV4_LIVE_TIMEZONE", "Asia/Shanghai"),
        },
        "parameters": parameters,
    }


def _record_ids(capability_id: str, data: dict[str, Any]) -> list[int]:
    if capability_id.endswith(".list"):
        return [item["id"] for item in data["items"]]
    return [data["id"]]


def _invoke(
    alias: str,
    capability_id: str,
    parameters: dict[str, Any],
    *,
    case: str,
) -> dict[str, Any]:
    root = _root()
    request = _request(alias, capability_id, parameters, case=case)
    registry = load_registry()
    descriptor = registry.describe(capability_id)
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

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert completed.stderr == ""
    assert len(completed.stdout.splitlines()) == 1
    document = json.loads(completed.stdout)
    registry.validate_instance(descriptor["schemas"]["response"], document)
    assert document["request_id"] == request["request_id"]
    assert document["success"] is True
    assert document["status"] == "verified"
    assert document["capability"] == capability_id
    assert document["error"] is None
    assert document["odoo"]["database"] == alias
    assert document["odoo"]["company_id"] == _COMPANY_ID
    assert document["odoo"]["model"] == _MODELS[capability_id]
    assert document["odoo"]["record_ids"] == _record_ids(
        capability_id, document["data"]
    )
    return document


@pytest.mark.integration
@pytest.mark.parametrize("alias", _ALIASES)
def test_accounting_reference_batch_uses_existing_read_only_rows(alias: str) -> None:
    if not os.environ.get(_CONFIG_ENV):
        pytest.skip(f"{_CONFIG_ENV} is not configured")

    covered: set[str] = set()
    groups = _invoke(
        alias,
        "account.group.list",
        {"limit": 100, "cursor": None},
        case="company-groups",
    )
    assert groups["data"]["items"] == []
    covered.add("account.group.list")

    journals = _invoke(
        alias,
        "journal.list",
        {"limit": 100, "cursor": None},
        case="select-journal",
    )
    assert journals["data"]["items"]
    journal_id = journals["data"]["items"][0]["id"]
    configuration = _invoke(
        alias,
        "journal.configuration.inspect",
        {"journal_id": journal_id},
        case="journal-configuration",
    )
    assert configuration["data"]["id"] == journal_id
    covered.add("journal.configuration.inspect")

    for list_id, list_parameters, get_id, id_parameter in _LIST_GET_CASES:
        listed = _invoke(
            alias,
            list_id,
            list_parameters,
            case=f"select-{get_id}",
        )
        assert listed["data"]["items"], f"{list_id} has no live fixture rows"
        selected_id = listed["data"]["items"][0]["id"]
        covered.add(list_id)

        detail = _invoke(
            alias,
            get_id,
            {id_parameter: selected_id},
            case="get-selected",
        )
        assert detail["data"]["id"] == selected_id
        covered.add(get_id)

    assert covered == _TARGET_CAPABILITIES
