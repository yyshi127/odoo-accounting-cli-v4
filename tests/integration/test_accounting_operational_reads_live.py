"""Shared read-only live smoke for operational accounting reads."""

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
_ALLOW_ENV = "ODACV4_ALLOW_ACCOUNTING_OPERATIONAL_READ_SMOKE"
_ALIASES = ("v4-dev", "v4-e2e")
_DATABASES = {
    "v4-dev": "odoo_cli_v4_dev",
    "v4-e2e": "odoo_cli_v4_e2e",
}
_COMPANY_ID = 1
_USER_ID = 5
_USER_LOGIN = "odacv4_g5_accountant"
_MISSING_ID = 2_147_483_647

_TARGET_CAPABILITIES = frozenset(
    {
        "invoice.duplicate_candidates.list",
        "invoice.tax_breakdown.inspect",
        "recurring.journal_entry.search",
        "recurring.journal_entry.get",
        "account.transfer_model.search",
        "account.transfer_model.get",
        "partner.credit_exposure.inspect",
        "journal.sequence_irregularity.list",
        "account.lock_exception.search",
        "account.lock_exception.get",
        "report.external_value.search",
        "report.external_value.get",
    }
)

_MODELS = {
    "user.accounting_access.inspect": "res.users",
    "invoice.search": "account.move",
    "partner.accounting.search": "res.partner",
    "invoice.duplicate_candidates.list": "account.move",
    "invoice.tax_breakdown.inspect": "account.move",
    "recurring.journal_entry.search": "account.move",
    "recurring.journal_entry.get": "account.move",
    "account.transfer_model.search": "account.transfer.model",
    "account.transfer_model.get": "account.transfer.model",
    "partner.credit_exposure.inspect": "res.partner",
    "journal.sequence_irregularity.list": "account.move",
    "account.lock_exception.search": "account.lock_exception",
    "account.lock_exception.get": "account.lock_exception",
    "report.external_value.search": "account.report.external.value",
    "report.external_value.get": "account.report.external.value",
}


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _enabled_runtime() -> dict[str, Any]:
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
    return document


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
                f"odacv4:{alias}:{_COMPANY_ID}:{capability_id}:operational:{case}",
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
) -> dict[str, Any]:
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
        return document
    return _invoke(
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
def test_accounting_operational_reads_use_uid5_on_both_isolated_databases() -> None:
    _enabled_runtime()

    for alias in _ALIASES:
        covered: set[str] = set()
        _assert_ordinary_accounting_user(alias)

        invoices = _invoke(
            alias,
            "invoice.search",
            {"limit": 100, "cursor": None},
            case="select-invoice",
        )["data"]["items"]
        assert invoices, "invoice.search has no live fixture rows"
        invoice_id = invoices[0]["id"]
        duplicates = _invoke(
            alias,
            "invoice.duplicate_candidates.list",
            {"invoice_id": invoice_id, "limit": 100, "cursor": None},
            case="duplicates",
        )
        assert isinstance(duplicates["data"]["items"], list)
        covered.add("invoice.duplicate_candidates.list")
        tax = _invoke(
            alias,
            "invoice.tax_breakdown.inspect",
            {"invoice_id": invoice_id},
            case="tax-breakdown",
        )
        assert tax["data"]["id"] == invoice_id
        covered.add("invoice.tax_breakdown.inspect")

        recurring = _invoke(
            alias,
            "recurring.journal_entry.search",
            {"limit": 100, "cursor": None},
            case="recurring-search",
        )
        covered.add("recurring.journal_entry.search")
        _get_selected_or_missing(
            alias,
            "recurring.journal_entry.get",
            "entry_id",
            recurring["data"]["items"],
        )
        covered.add("recurring.journal_entry.get")

        transfers = _invoke(
            alias,
            "account.transfer_model.search",
            {"limit": 100, "cursor": None},
            case="transfer-model-search",
        )
        covered.add("account.transfer_model.search")
        _get_selected_or_missing(
            alias,
            "account.transfer_model.get",
            "transfer_model_id",
            transfers["data"]["items"],
        )
        covered.add("account.transfer_model.get")

        partners = _invoke(
            alias,
            "partner.accounting.search",
            {"role": "both", "query": None, "limit": 100, "cursor": None},
            case="select-partner",
        )["data"]["items"]
        assert partners, "partner.accounting.search has no live fixture rows"
        exposure = _invoke(
            alias,
            "partner.credit_exposure.inspect",
            {"partner_id": partners[0]["id"]},
            case="credit-exposure",
        )
        assert exposure["data"]["id"] == partners[0]["id"]
        covered.add("partner.credit_exposure.inspect")

        irregularities = _invoke(
            alias,
            "journal.sequence_irregularity.list",
            {"limit": 100, "cursor": None},
            case="sequence-irregularities",
        )
        assert isinstance(irregularities["data"]["items"], list)
        covered.add("journal.sequence_irregularity.list")

        lock_exceptions = _invoke(
            alias,
            "account.lock_exception.search",
            {"limit": 100, "cursor": None},
            case="lock-exception-search",
        )
        covered.add("account.lock_exception.search")
        _get_selected_or_missing(
            alias,
            "account.lock_exception.get",
            "lock_exception_id",
            lock_exceptions["data"]["items"],
        )
        covered.add("account.lock_exception.get")

        external_values = _invoke(
            alias,
            "report.external_value.search",
            {"limit": 100, "cursor": None},
            case="external-value-search",
        )
        assert external_values["odoo"]["record_ids"] == [
            item["id"] for item in external_values["data"]["items"]
        ]
        covered.add("report.external_value.search")
        _get_selected_or_missing(
            alias,
            "report.external_value.get",
            "external_value_id",
            external_values["data"]["items"],
        )
        covered.add("report.external_value.get")

        assert covered == _TARGET_CAPABILITIES
