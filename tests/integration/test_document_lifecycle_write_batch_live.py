"""Transactional dual-database smoke for document lifecycle writes.

The worker uses the ordinary configured accountant and public CLI commands backed
by one real Odoo transaction. It verifies independent invoice/accounting dates,
retains the three document lifecycles and immediate replay, and rolls everything
back. This is in-process CLI/real-ORM coverage, not cross-process transport.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import sysconfig
import uuid
from datetime import timedelta
from pathlib import Path
from typing import Any

import test_payment_bank_capability_batch_live as core

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
_CAPABILITIES = set(_NEW_CAPABILITIES) | {
    "customer_invoice.create",
    "vendor_bill.create",
    "invoice.post",
    "invoice.get",
    "journal_entry.create",
    "journal_entry.post",
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
        part
        for part in (
            str(_root() / "src"),
            sysconfig.get_path("purelib"),
            environment.get("PYTHONPATH"),
        )
        if part
    )
    completed = subprocess.run(
        command,
        cwd=_root(),
        env=environment,
        text=True,
        capture_output=True,
        check=False,
        timeout=max(timeout, 900),
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert completed.stderr == ""
    assert len(completed.stdout.splitlines()) == 1
    assert json.loads(completed.stdout) == {
        "accounting_dates_verified": True,
        "alias": alias,
        "capabilities": sorted(_CAPABILITIES),
        "company_id": _COMPANY_ID,
        "database": _DATABASES[alias],
        "execution": "in_process_cli_real_orm",
        "marker_migration_verified": True,
        "rollback_verified": True,
        "user_id": _USER_ID,
    }
    print(completed.stdout.strip(), flush=True)


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


def _dispatch_twice(
    client: core._RuntimeClient,
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    parameters: dict[str, Any],
    *,
    explicit_key: str | None = None,
) -> dict[str, Any]:
    idempotency_key = _key(capability_id, parameters, explicit_key)
    first = core._cli(
        client, alias, run_id, capability_id, parameters, key=idempotency_key
    )
    second = core._cli(
        client, alias, run_id, capability_id, parameters, key=idempotency_key
    )
    assert first["idempotent_replay"] is False
    assert second["idempotent_replay"] is True
    assert first["result"] == second["result"]
    assert set(first["result"]) == _RESULT_KEYS
    assert first["result"]["company_id"] == _COMPANY_ID
    assert first["result"]["model"] == "account.move"
    return first["result"]


def _replay_existing_create(
    client: core._RuntimeClient,
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    parameters: dict[str, Any],
    key: str,
) -> dict[str, Any]:
    replay = core._cli(client, alias, run_id, capability_id, parameters, key=key)
    assert replay["idempotent_replay"] is True
    assert set(replay["result"]) == _RESULT_KEYS
    assert replay["result"]["company_id"] == _COMPANY_ID
    assert replay["result"]["model"] == "account.move"
    return replay["result"]


def _marker(capability_id: str, company_id: int, key: str, parameters: Any) -> str:
    key_raw = f"{capability_id}\0{company_id}\0{key}".encode()
    key_marker = f"ODACV4K:{hashlib.sha256(key_raw).hexdigest()}"
    return f"{key_marker};ODACV4:{_canonical_digest(parameters)}"


def _assert_invoice_dates(
    client: core._RuntimeClient,
    alias: str,
    run_id: uuid.UUID,
    invoice_id: int,
    accounting_date: str,
    invoice_date: str,
    state: str = "draft",
) -> None:
    data = core._cli(client, alias, run_id, "invoice.get", {"invoice_id": invoice_id})
    assert data["id"] == invoice_id
    assert data["date"] == accounting_date
    assert data["invoice_date"] == invoice_date
    assert data["state"] == state
    assert data["date"] != data["invoice_date"]


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


def _run_chain(client: core._RuntimeClient, alias: str, run_id: uuid.UUID) -> None:
    from odoo import fields

    env = client.env
    ids = _fixture_ids(env, alias)
    run_token = f"{run_id.hex}-{alias}"
    today_date = fields.Date.context_today(env.user)
    today = fields.Date.to_string(today_date)
    yesterday = fields.Date.to_string(today_date - timedelta(days=1))
    original_invoice_date = fields.Date.to_string(today_date - timedelta(days=3))
    updated_invoice_date = fields.Date.to_string(today_date - timedelta(days=2))

    invoice_parameters = {
        "partner_id": ids["customer"],
        "journal_id": ids["sale_journal"],
        "date": today,
        "invoice_date": original_invoice_date,
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
        client,
        alias,
        run_id,
        "customer_invoice.create",
        invoice_parameters,
        explicit_key=invoice_key,
    )
    invoice_id = invoice_result["id"]
    assert isinstance(invoice_id, int)
    invoice = env["account.move"].browse(invoice_id)
    assert not invoice.ref
    assert invoice.invoice_origin == _marker(
        "customer_invoice.create", _COMPANY_ID, invoice_key, invoice_parameters
    )
    _assert_invoice_dates(
        client, alias, run_id, invoice_id, today, original_invoice_date
    )
    _dispatch_twice(
        client,
        alias,
        run_id,
        "invoice.update",
        {"move_id": invoice_id, "changes": {"date": yesterday}},
    )
    _assert_invoice_dates(
        client, alias, run_id, invoice_id, yesterday, original_invoice_date
    )
    _dispatch_twice(
        client,
        alias,
        run_id,
        "invoice.update",
        {
            "move_id": invoice_id,
            "changes": {"date": today, "invoice_date": updated_invoice_date},
        },
    )
    _assert_invoice_dates(
        client, alias, run_id, invoice_id, today, updated_invoice_date
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
    _dispatch_twice(client, alias, run_id, "invoice.lines.replace", replace_invoice)
    _dispatch_twice(client, alias, run_id, "invoice.post", {"move_id": invoice_id})
    _assert_invoice_dates(
        client, alias, run_id, invoice_id, today, updated_invoice_date, "posted"
    )
    canceled_invoice = _dispatch_twice(
        client, alias, run_id, "invoice.cancel", {"move_id": invoice_id}
    )
    assert canceled_invoice["state"] == "cancel"

    bill_parameters = {
        "partner_id": ids["supplier"],
        "journal_id": ids["purchase_journal"],
        "date": today,
        "invoice_date": original_invoice_date,
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
        client,
        alias,
        run_id,
        "vendor_bill.create",
        bill_parameters,
        explicit_key=bill_key,
    )
    bill_id = bill_result["id"]
    assert isinstance(bill_id, int)
    bill = env["account.move"].browse(bill_id)
    assert not bill.ref
    assert bill.invoice_origin == _marker(
        "vendor_bill.create", _COMPANY_ID, bill_key, bill_parameters
    )
    _assert_invoice_dates(client, alias, run_id, bill_id, today, original_invoice_date)
    bill_reference = f"BILL-{run_id.hex[:16]}"
    _dispatch_twice(
        client,
        alias,
        run_id,
        "invoice.update",
        {
            "move_id": bill_id,
            "changes": {"reference": bill_reference, "date": yesterday},
        },
    )
    _assert_invoice_dates(
        client, alias, run_id, bill_id, yesterday, original_invoice_date
    )
    bill.invalidate_recordset(["ref"])
    assert bill.ref == bill_reference
    assert (
        _replay_existing_create(
            client, alias, run_id, "vendor_bill.create", bill_parameters, bill_key
        )["id"]
        == bill_id
    )
    _assert_invoice_dates(
        client, alias, run_id, bill_id, yesterday, original_invoice_date
    )
    _dispatch_twice(
        client,
        alias,
        run_id,
        "invoice.update",
        {
            "move_id": bill_id,
            "changes": {"date": today, "invoice_date": updated_invoice_date},
        },
    )
    _assert_invoice_dates(client, alias, run_id, bill_id, today, updated_invoice_date)
    _dispatch_twice(client, alias, run_id, "invoice.post", {"move_id": bill_id})
    _assert_invoice_dates(
        client, alias, run_id, bill_id, today, updated_invoice_date, "posted"
    )
    reset_bill = _dispatch_twice(
        client, alias, run_id, "invoice.reset_to_draft", {"move_id": bill_id}
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
        client,
        alias,
        run_id,
        "journal_entry.create",
        entry_parameters,
        explicit_key=entry_key,
    )
    entry_id = entry_result["id"]
    assert isinstance(entry_id, int)
    entry = env["account.move"].browse(entry_id)
    assert not entry.ref
    assert entry.invoice_origin == _marker(
        "journal_entry.create", _COMPANY_ID, entry_key, entry_parameters
    )
    entry_reference = f"ENTRY-{run_id.hex[:16]}"
    _dispatch_twice(
        client,
        alias,
        run_id,
        "journal_entry.update",
        {"move_id": entry_id, "changes": {"reference": entry_reference}},
    )
    entry.invalidate_recordset(["ref"])
    assert entry.ref == entry_reference
    assert (
        _replay_existing_create(
            client, alias, run_id, "journal_entry.create", entry_parameters, entry_key
        )["id"]
        == entry_id
    )
    _dispatch_twice(
        client,
        alias,
        run_id,
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
    _dispatch_twice(client, alias, run_id, "journal_entry.post", {"move_id": entry_id})
    reset_entry = _dispatch_twice(
        client, alias, run_id, "journal_entry.reset_to_draft", {"move_id": entry_id}
    )
    assert reset_entry["state"] == "draft"
    canceled_entry = _dispatch_twice(
        client, alias, run_id, "journal_entry.cancel", {"move_id": entry_id}
    )
    assert canceled_entry["state"] == "cancel"
    assert client.tracked["account.move"] == {invoice_id, bill_id, entry_id}


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
            "--logfile=/dev/null",
        ]
    )
    registry = Registry(args.database)
    cursor = registry.cursor()
    tracked: dict[str, set[int]] = {model: set() for model in core._BUSINESS_MODELS}
    env = client = None
    failure: BaseException | None = None
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
        client = core._RuntimeClient(env)
        client.tracked = tracked
        user = env.user
        if (
            env.uid != _USER_ID
            or user.id != _USER_ID
            or not user.active
            or user.login != _USER_LOGIN
            or _COMPANY_ID not in user.company_ids.ids
        ):
            raise RuntimeError("the fixed business user is unavailable")
        _run_chain(client, args.alias, args.run_id)
        assert client.capabilities == _CAPABILITIES
    except BaseException as exc:  # noqa: BLE001 - re-raised after rollback verification
        failure = exc
    finally:
        try:
            if env is not None:
                core._collect_marked(env, tracked, args.run_id.hex)
        except Exception as exc:  # noqa: BLE001 - collection must not prevent rollback
            if failure is None:
                failure = exc
            else:
                failure.add_note(f"rollback ID collection also failed: {exc}")
        finally:
            try:
                cursor.rollback()
            finally:
                cursor.close()

    try:
        core._verify_rollback(registry, tracked=tracked, marker=args.run_id.hex)
    except Exception as exc:
        raise exc from failure
    if failure is not None:
        raise failure
    assert client is not None
    sys.stdout.write(
        json.dumps(
            {
                "accounting_dates_verified": True,
                "alias": args.alias,
                "capabilities": sorted(client.capabilities),
                "company_id": _COMPANY_ID,
                "database": args.database,
                "execution": "in_process_cli_real_orm",
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
