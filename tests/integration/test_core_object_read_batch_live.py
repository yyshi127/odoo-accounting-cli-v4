"""Shared read-only live smoke for the core-object capability batch."""

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
_AS_OF = "2025-01-31"

_MODELS = {
    "account.account.list": "account.account",
    "account.account.get": "account.account",
    "journal.list": "account.journal",
    "journal.get": "account.journal",
    "tax.list": "account.tax",
    "tax.get": "account.tax",
    "payment_term.list": "account.payment.term",
    "payment_term.get": "account.payment.term",
    "currency.list": "res.currency",
    "currency.get": "res.currency",
    "partner.accounting.search": "res.partner",
    "partner.accounting.get": "res.partner",
    "bank.transaction.list": "account.bank.statement.line",
    "bank.transaction.get": "account.bank.statement.line",
    "journal_item.search": "account.move.line",
    "journal_item.get": "account.move.line",
    "payment.method.list": "account.payment.method.line",
    "reconciliation.model.list": "account.reconcile.model",
    "report.bank_reconciliation": "account.report",
}

_TARGET_CAPABILITIES = frozenset(
    {
        "account.account.get",
        "journal.get",
        "tax.get",
        "payment_term.get",
        "currency.get",
        "partner.accounting.get",
        "bank.transaction.get",
        "journal_item.search",
        "journal_item.get",
        "payment.method.list",
        "reconciliation.model.list",
        "report.bank_reconciliation",
    }
)

_SELECTORS = (
    (
        "account.account.list",
        {"limit": 100, "cursor": None},
        "account.account.get",
        "account_id",
    ),
    (
        "journal.list",
        {"limit": 100, "cursor": None},
        "journal.get",
        "journal_id",
    ),
    (
        "tax.list",
        {"limit": 100, "cursor": None},
        "tax.get",
        "tax_id",
    ),
    (
        "payment_term.list",
        {"limit": 100, "cursor": None},
        "payment_term.get",
        "payment_term_id",
    ),
    (
        "currency.list",
        {"limit": 100, "cursor": None},
        "currency.get",
        "currency_id",
    ),
    (
        "partner.accounting.search",
        {
            "role": "both",
            "query": None,
            "limit": 100,
            "cursor": None,
        },
        "partner.accounting.get",
        "partner_id",
    ),
    (
        "bank.transaction.list",
        {"limit": 100, "cursor": None},
        "bank.transaction.get",
        "transaction_id",
    ),
    (
        "journal_item.search",
        {"posted_only": True, "limit": 100, "cursor": None},
        "journal_item.get",
        "line_id",
    ),
)


def _project_root() -> Path:
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
                f"odacv4:{alias}:{_COMPANY_ID}:{capability_id}:core-object-live:{case}",
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
    if capability_id.startswith("report."):
        return []
    if capability_id.endswith(".get"):
        return [data["id"]]
    return [item["id"] for item in data["items"]]


def _invoke(
    alias: str,
    capability_id: str,
    parameters: dict[str, Any],
    *,
    case: str,
) -> dict[str, Any]:
    root = _project_root()
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
    assert document["schema_version"] == "v1"
    assert document["request_id"] == request["request_id"]
    assert document["success"] is True
    assert document["status"] == "verified"
    assert document["capability"] == capability_id
    assert document["error"] is None
    assert document["odoo"]["database"] == alias
    assert document["odoo"]["company_id"] == _COMPANY_ID
    assert isinstance(document["odoo"]["user_id"], int)
    assert document["odoo"]["user_id"] > 0
    assert document["odoo"]["model"] == _MODELS[capability_id]
    assert document["odoo"]["record_ids"] == _record_ids(
        capability_id, document["data"]
    )
    return document


def _selected_item(capability_id: str, document: dict[str, Any]) -> dict[str, Any]:
    items = document["data"]["items"]
    assert items, f"{capability_id} has no live fixture rows"
    if capability_id == "journal.list":
        bank_items = [item for item in items if item["type"] == "bank"]
        assert bank_items, "journal.list has no bank journal fixture"
        return bank_items[0]
    return items[0]


@pytest.mark.integration
@pytest.mark.parametrize("alias", _ALIASES)
def test_core_object_batch_uses_existing_live_read_only_fixtures(alias: str) -> None:
    if not os.environ.get(_CONFIG_ENV):
        pytest.skip(f"{_CONFIG_ENV} is not configured")

    covered: set[str] = set()
    bank_journal_id: int | None = None
    for selector_id, selector_parameters, get_id, id_field in _SELECTORS:
        selector = _invoke(
            alias,
            selector_id,
            selector_parameters,
            case=f"select-{get_id}",
        )
        selected = _selected_item(selector_id, selector)
        if selector_id == "journal.list":
            bank_journal_id = selected["id"]
        if selector_id == "journal_item.search":
            covered.add(selector_id)

        detail = _invoke(
            alias,
            get_id,
            {id_field: selected["id"]},
            case="get-selected",
        )
        assert detail["data"]["id"] == selected["id"]
        covered.add(get_id)

    for capability_id in (
        "payment.method.list",
        "reconciliation.model.list",
    ):
        document = _invoke(
            alias,
            capability_id,
            {"limit": 100, "cursor": None},
            case="positive-list",
        )
        assert document["data"]["items"], f"{capability_id} has no live fixture rows"
        covered.add(capability_id)

    assert bank_journal_id is not None
    report = _invoke(
        alias,
        "report.bank_reconciliation",
        {
            "journal_id": bank_journal_id,
            "as_of": _AS_OF,
            "limit": 100,
            "cursor": None,
        },
        case="bank-journal-report",
    )
    assert report["data"]["report"]["key"] == "bank_reconciliation"
    covered.add("report.bank_reconciliation")

    assert covered == _TARGET_CAPABILITIES
