"""Transactional dual-database smoke for document lifecycle writes.

The worker uses the ordinary configured accountant, creates all prerequisites through
the public fixed write path, exercises every new capability twice, and rolls the
whole transaction back.  It never commits fixture or accounting data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

try:
    import pytest
except ModuleNotFoundError:
    if "--live-worker" not in sys.argv:
        raise
    pytest = None


_CONFIG_ENV = "ODOO_ACCOUNTING_CLI_V4_CONFIG"
_ALLOW_ENV = "ODACV4_ALLOW_DOCUMENT_LIFECYCLE_WRITE_SMOKE"
_ALIASES = ("v4-dev", "v4-e2e")
_DATABASES = {
    "v4-dev": "odoo_cli_v4_dev",
    "v4-e2e": "odoo_cli_v4_e2e",
}
_PARTNERS = {
    "v4-dev": {"customer": 16, "supplier": 17},
    "v4-e2e": {"customer": 8, "supplier": 9},
}
_COMPANY_ID = 1
_USER_ID = 5
_USER_LOGIN = "odacv4_g5_accountant"
_NEW_CAPABILITIES = (
    "invoice.update",
    "invoice.lines.replace",
    "invoice.cancel",
    "invoice.reset_to_draft",
    "journal_entry.update",
    "journal_entry.lines.replace",
    "journal_entry.cancel",
    "journal_entry.reset_to_draft",
)
_PAGE_KEYS = {
    "user_id",
    "company_visible",
    "module_installed",
    "access_allowed",
    "idempotent_replay",
    "result",
}
_RESULT_KEYS = {
    "model",
    "id",
    "name",
    "state",
    "company_id",
    "move_type",
    "source_id",
    "line_ids",
    "partial_reconcile_ids",
    "full_reconcile_id",
    "reconciled",
}


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _enabled_runtime() -> tuple[Path, dict[str, Any]]:
    assert pytest is not None
    if os.environ.get(_ALLOW_ENV) != "1":
        pytest.skip(f"set {_ALLOW_ENV}=1 to authorize isolated write smoke")
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
    return path, document


def _worker_command(
    alias: str,
    run_id: uuid.UUID,
    config_path: Path,
    runtime: dict[str, Any],
) -> tuple[list[str], int]:
    bridge = runtime.get("bridge")
    assert isinstance(bridge, dict) and set(bridge) == {
        "argv",
        "timeout_seconds",
    }
    argv = bridge["argv"]
    assert isinstance(argv, list) and len(argv) == 8
    assert argv[2::2] == ["--runtime-config", "--odoo-config", "--odoo-source"]
    assert Path(argv[3]).resolve(strict=True) == config_path.resolve(strict=True)
    executable = Path(argv[0])
    odoo_config = Path(argv[5])
    odoo_source = Path(argv[7])
    assert executable.is_absolute() and executable.is_file()
    assert odoo_config.is_absolute() and odoo_config.is_file()
    assert odoo_source.is_absolute() and odoo_source.is_dir()
    timeout = bridge["timeout_seconds"]
    assert isinstance(timeout, int) and not isinstance(timeout, bool) and timeout > 0
    return (
        [
            str(executable),
            str(Path(__file__).resolve()),
            "--live-worker",
            "--odoo-config",
            str(odoo_config),
            "--odoo-source",
            str(odoo_source),
            "--alias",
            alias,
            "--database",
            _DATABASES[alias],
            "--run-id",
            str(run_id),
        ],
        timeout,
    )


def _run_worker(
    alias: str,
    run_id: uuid.UUID,
    config_path: Path,
    runtime: dict[str, Any],
) -> None:
    command, timeout = _worker_command(alias, run_id, config_path, runtime)
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = os.pathsep.join(
        part for part in (str(_root() / "src"), environment.get("PYTHONPATH")) if part
    )
    completed = subprocess.run(
        command,
        cwd=_root(),
        env=environment,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert len(completed.stdout.splitlines()) == 1
    assert json.loads(completed.stdout) == {
        "alias": alias,
        "capabilities": list(_NEW_CAPABILITIES),
        "company_id": _COMPANY_ID,
        "database": _DATABASES[alias],
        "marker_migration_verified": True,
        "rollback_verified": True,
        "user_id": _USER_ID,
    }


if pytest is not None:

    @pytest.mark.integration
    def test_document_lifecycle_batch_rolls_back_one_real_chain_per_alias() -> None:
        config_path, runtime = _enabled_runtime()
        run_id = uuid.uuid4()
        for alias in _ALIASES:
            _run_worker(alias, run_id, config_path, runtime)


def _arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-worker", action="store_true", required=True)
    parser.add_argument("--odoo-config", type=Path, required=True)
    parser.add_argument("--odoo-source", type=Path, required=True)
    parser.add_argument("--alias", choices=_ALIASES, required=True)
    parser.add_argument("--database", choices=tuple(_DATABASES.values()), required=True)
    parser.add_argument("--run-id", type=uuid.UUID, required=True)
    args = parser.parse_args(argv)
    if args.database != _DATABASES[args.alias]:
        parser.error("alias and physical database do not match")
    if not args.odoo_config.is_absolute() or not args.odoo_config.is_file():
        parser.error("odoo-config must be an existing absolute file")
    if not args.odoo_source.is_absolute() or not args.odoo_source.is_dir():
        parser.error("odoo-source must be an existing absolute directory")
    return args


def _one(records: Any, label: str) -> Any:
    if len(records) != 1:
        raise RuntimeError(f"expected one {label}, got {len(records)}")
    return records


def _canonical_digest(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _key(capability_id: str, parameters: dict[str, Any], explicit: str | None) -> str:
    if explicit is not None:
        return explicit
    move_id = parameters["move_id"]
    target = parameters.get("changes", parameters.get("lines"))
    if target is None:
        return f"{capability_id}:{move_id}"
    return f"{capability_id}:{move_id}:{_canonical_digest(target)[:32]}"


def _assert_page(page: dict[str, Any], *, replay: bool) -> None:
    assert set(page) == _PAGE_KEYS
    assert page["user_id"] == _USER_ID
    assert page["company_visible"] is True
    assert page["module_installed"] is True
    assert page["access_allowed"] is True
    assert page["idempotent_replay"] is replay
    result = page["result"]
    assert isinstance(result, dict) and set(result) == _RESULT_KEYS
    assert result["company_id"] == _COMPANY_ID
    assert result["model"] == "account.move"


class _RuntimePort:
    def __init__(self, env: Any) -> None:
        self.env = env
        self.pages: list[dict[str, Any]] = []

    @property
    def user_id(self) -> int:
        return self.env.uid

    def execute(self, **payload: Any) -> dict[str, Any]:
        from odoo_accounting_cli_v4.bridge.core_writes_runtime import dispatch
        from odoo_accounting_cli_v4.bridge.runtime import RuntimeFailure

        page = dispatch(self.env, payload, payload["company_id"], RuntimeFailure)
        self.pages.append(page)
        return page


def _dispatch_twice(
    env: Any,
    alias: str,
    capability_id: str,
    parameters: dict[str, Any],
    *,
    explicit_key: str | None = None,
) -> dict[str, Any]:
    from odoo_accounting_cli_v4.capabilities.core_writes import execute_core_write

    request = {
        "schema_version": "v1",
        "request_id": "7c5ea1f2-f402-48f6-9622-1f8808ff45eb",
        "context": {
            "database": alias,
            "company_id": _COMPANY_ID,
            "user_login": _USER_LOGIN,
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": parameters,
    }
    idempotency_key = _key(capability_id, parameters, explicit_key)
    port = _RuntimePort(env)
    first = execute_core_write(
        port, capability_id, request, idempotency_key, capability_id
    )
    second = execute_core_write(
        port, capability_id, request, idempotency_key, capability_id
    )
    assert len(port.pages) == 2
    _assert_page(port.pages[0], replay=False)
    _assert_page(port.pages[1], replay=True)
    assert first["idempotent_replay"] is False
    assert second["idempotent_replay"] is True
    assert first["result"] == second["result"]
    return first["result"]


def _replay_existing_create(
    env: Any,
    alias: str,
    capability_id: str,
    parameters: dict[str, Any],
    key: str,
) -> dict[str, Any]:
    from odoo_accounting_cli_v4.capabilities.core_writes import execute_core_write

    request = {
        "schema_version": "v1",
        "request_id": "66a361b7-8cec-45f5-b13e-b5e088f06b09",
        "context": {
            "database": alias,
            "company_id": _COMPANY_ID,
            "user_login": _USER_LOGIN,
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": parameters,
    }
    port = _RuntimePort(env)
    replay = execute_core_write(port, capability_id, request, key, capability_id)
    assert len(port.pages) == 1
    _assert_page(port.pages[0], replay=True)
    assert replay["idempotent_replay"] is True
    return replay["result"]


def _marker(capability_id: str, company_id: int, key: str, parameters: Any) -> str:
    key_raw = f"{capability_id}\0{company_id}\0{key}".encode()
    key_marker = f"ODACV4K:{hashlib.sha256(key_raw).hexdigest()}"
    return f"{key_marker};ODACV4:{_canonical_digest(parameters)}"


def _fixture_ids(env: Any, alias: str) -> dict[str, int]:
    company = _one(env["res.company"].search([("id", "=", _COMPANY_ID)]), "company")
    partner_ids = _PARTNERS[alias]
    partners = env["res.partner"].search(
        [
            ("id", "in", sorted(partner_ids.values())),
            ("company_id", "in", [False, _COMPANY_ID]),
        ]
    )
    if set(partners.ids) != set(partner_ids.values()):
        raise RuntimeError("the fixed customer or supplier is unavailable")

    def journal(journal_type: str) -> Any:
        return _one(
            env["account.journal"].search(
                [
                    ("company_id", "=", _COMPANY_ID),
                    ("type", "=", journal_type),
                ],
                limit=1,
                order="id",
            ),
            f"{journal_type} journal",
        )

    def account(account_type: str) -> Any:
        return _one(
            env["account.account"].search(
                [
                    ("company_ids", "in", [_COMPANY_ID]),
                    ("account_type", "=", account_type),
                ],
                limit=1,
                order="id",
            ),
            f"{account_type} account",
        )

    return {
        "customer": partner_ids["customer"],
        "supplier": partner_ids["supplier"],
        "currency": company.currency_id.id,
        "sale_journal": journal("sale").id,
        "purchase_journal": journal("purchase").id,
        "general_journal": journal("general").id,
        "income": account("income").id,
        "expense": account("expense").id,
        "asset": account("asset_current").id,
    }


def _run_chain(env: Any, alias: str, run_id: uuid.UUID) -> set[int]:
    from odoo import fields

    ids = _fixture_ids(env, alias)
    run_token = f"{run_id.hex}-{alias}"
    today = fields.Date.to_string(fields.Date.context_today(env.user))
    created: set[int] = set()

    invoice_parameters = {
        "partner_id": ids["customer"],
        "journal_id": ids["sale_journal"],
        "invoice_date": today,
        "currency_id": ids["currency"],
        "lines": [
            {
                "name": f"Lifecycle invoice {run_token}",
                "account_id": ids["income"],
                "quantity": "1",
                "price_unit": "25",
                "tax_ids": [],
            }
        ],
    }
    invoice_key = f"document-lifecycle-invoice-{run_id.hex}"
    invoice_result = _dispatch_twice(
        env,
        alias,
        "customer_invoice.create",
        invoice_parameters,
        explicit_key=invoice_key,
    )
    invoice_id = invoice_result["id"]
    assert isinstance(invoice_id, int)
    created.add(invoice_id)
    invoice = env["account.move"].browse(invoice_id)
    assert not invoice.ref
    assert invoice.invoice_origin == _marker(
        "customer_invoice.create", _COMPANY_ID, invoice_key, invoice_parameters
    )

    replace_invoice = {
        "move_id": invoice_id,
        "lines": [
            {
                "name": f"Replaced invoice line {run_token}",
                "product_id": None,
                "account_id": ids["income"],
                "quantity": "2",
                "price_unit": "30.50",
                "discount": "5",
                "tax_ids": [],
            }
        ],
    }
    _dispatch_twice(env, alias, "invoice.lines.replace", replace_invoice)
    _dispatch_twice(env, alias, "invoice.post", {"move_id": invoice_id})
    canceled_invoice = _dispatch_twice(
        env, alias, "invoice.cancel", {"move_id": invoice_id}
    )
    assert canceled_invoice["state"] == "cancel"

    bill_parameters = {
        "partner_id": ids["supplier"],
        "journal_id": ids["purchase_journal"],
        "invoice_date": today,
        "currency_id": ids["currency"],
        "lines": [
            {
                "name": f"Lifecycle bill {run_token}",
                "account_id": ids["expense"],
                "quantity": "1",
                "price_unit": "40",
                "tax_ids": [],
            }
        ],
    }
    bill_key = f"document-lifecycle-bill-{run_id.hex}"
    bill_result = _dispatch_twice(
        env,
        alias,
        "vendor_bill.create",
        bill_parameters,
        explicit_key=bill_key,
    )
    bill_id = bill_result["id"]
    assert isinstance(bill_id, int)
    created.add(bill_id)
    bill = env["account.move"].browse(bill_id)
    assert not bill.ref
    assert bill.invoice_origin == _marker(
        "vendor_bill.create", _COMPANY_ID, bill_key, bill_parameters
    )
    bill_reference = f"BILL-{run_id.hex[:16]}"
    _dispatch_twice(
        env,
        alias,
        "invoice.update",
        {"move_id": bill_id, "changes": {"reference": bill_reference}},
    )
    bill.invalidate_recordset(["ref"])
    assert bill.ref == bill_reference
    assert (
        _replay_existing_create(
            env, alias, "vendor_bill.create", bill_parameters, bill_key
        )["id"]
        == bill_id
    )
    _dispatch_twice(env, alias, "invoice.post", {"move_id": bill_id})
    reset_bill = _dispatch_twice(
        env, alias, "invoice.reset_to_draft", {"move_id": bill_id}
    )
    assert reset_bill["state"] == "draft"

    entry_parameters = {
        "journal_id": ids["general_journal"],
        "date": today,
        "lines": [
            {
                "name": f"Entry debit {run_token}",
                "account_id": ids["asset"],
                "partner_id": None,
                "debit": "50",
                "credit": "0",
            },
            {
                "name": f"Entry credit {run_token}",
                "account_id": ids["income"],
                "partner_id": None,
                "debit": "0",
                "credit": "50",
            },
        ],
    }
    entry_key = f"document-lifecycle-entry-{run_id.hex}"
    entry_result = _dispatch_twice(
        env,
        alias,
        "journal_entry.create",
        entry_parameters,
        explicit_key=entry_key,
    )
    entry_id = entry_result["id"]
    assert isinstance(entry_id, int)
    created.add(entry_id)
    entry = env["account.move"].browse(entry_id)
    assert not entry.ref
    assert entry.invoice_origin == _marker(
        "journal_entry.create", _COMPANY_ID, entry_key, entry_parameters
    )
    entry_reference = f"ENTRY-{run_id.hex[:16]}"
    _dispatch_twice(
        env,
        alias,
        "journal_entry.update",
        {"move_id": entry_id, "changes": {"reference": entry_reference}},
    )
    entry.invalidate_recordset(["ref"])
    assert entry.ref == entry_reference
    assert (
        _replay_existing_create(
            env, alias, "journal_entry.create", entry_parameters, entry_key
        )["id"]
        == entry_id
    )
    _dispatch_twice(
        env,
        alias,
        "journal_entry.lines.replace",
        {
            "move_id": entry_id,
            "lines": [
                {
                    "name": f"Replacement debit {run_token}",
                    "account_id": ids["expense"],
                    "partner_id": ids["supplier"],
                    "debit": "75",
                    "credit": "0",
                },
                {
                    "name": f"Replacement credit {run_token}",
                    "account_id": ids["asset"],
                    "partner_id": ids["supplier"],
                    "debit": "0",
                    "credit": "75",
                },
            ],
        },
    )
    _dispatch_twice(env, alias, "journal_entry.post", {"move_id": entry_id})
    reset_entry = _dispatch_twice(
        env, alias, "journal_entry.reset_to_draft", {"move_id": entry_id}
    )
    assert reset_entry["state"] == "draft"
    canceled_entry = _dispatch_twice(
        env, alias, "journal_entry.cancel", {"move_id": entry_id}
    )
    assert canceled_entry["state"] == "cancel"
    return created


def _verify_rollback(registry: Any, created_ids: set[int]) -> None:
    from odoo import SUPERUSER_ID, api

    cursor = registry.cursor()
    try:
        env = api.Environment(
            cursor, SUPERUSER_ID, {"allowed_company_ids": [_COMPANY_ID]}
        )
        if env["account.move"].search_count([("id", "in", sorted(created_ids))]):
            raise RuntimeError("rollback left lifecycle fixture moves behind")
    finally:
        cursor.rollback()
        cursor.close()


def _live_worker(argv: list[str] | None = None) -> int:
    args = _arguments(argv)
    sys.path.insert(0, str(args.odoo_source.resolve(strict=True)))
    sys.path.insert(0, str((_root() / "src").resolve(strict=True)))

    from odoo import api
    from odoo.orm.registry import Registry
    from odoo.tools import config as odoo_config

    odoo_config.parse_config(
        [
            "--config",
            str(args.odoo_config.resolve(strict=True)),
            "--database",
            args.database,
            "--no-http",
        ]
    )
    registry = Registry(args.database)
    cursor = registry.cursor()
    created_ids: set[int] = set()
    try:
        env = api.Environment(
            cursor,
            _USER_ID,
            {
                "allowed_company_ids": [_COMPANY_ID],
                "active_test": True,
                "lang": "en_US",
                "tz": "Asia/Shanghai",
            },
        )
        user = env.user
        if (
            env.uid != _USER_ID
            or user.id != _USER_ID
            or not user.active
            or user.login != _USER_LOGIN
            or _COMPANY_ID not in user.company_ids.ids
        ):
            raise RuntimeError("the fixed business user is unavailable")
        created_ids = _run_chain(env, args.alias, args.run_id)
    finally:
        cursor.rollback()
        cursor.close()

    _verify_rollback(registry, created_ids)
    sys.stdout.write(
        json.dumps(
            {
                "alias": args.alias,
                "capabilities": list(_NEW_CAPABILITIES),
                "company_id": _COMPANY_ID,
                "database": args.database,
                "marker_migration_verified": True,
                "rollback_verified": True,
                "user_id": _USER_ID,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_live_worker())
