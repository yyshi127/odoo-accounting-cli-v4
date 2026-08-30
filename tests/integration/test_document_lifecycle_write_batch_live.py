"""Transactional dual-database smoke for document lifecycle writes.

The worker uses the ordinary configured accountant and public CLI commands backed
by one real Odoo transaction. It verifies independent invoice/accounting dates,
retains the three document lifecycles and immediate replay, and rolls everything
back. This is in-process CLI/real-ORM coverage, not cross-process transport.
The separately enabled refund-only case closes customer and supplier financial
credits through native automatic reconciliation, targeted undo and manual
reapplication, without invoking the original lifecycle, bank or deferred workflows.
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
from decimal import Decimal
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
_REFUND_ALLOW_ENV = "ODACV4_ALLOW_FINANCIAL_REFUND_SMOKE"
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
_REFUND_CAPABILITIES = {
    "customer_invoice.create",
    "vendor_bill.create",
    "customer_credit_note.create",
    "vendor_refund.create",
    "invoice.post",
    "invoice.get",
    "invoice.payment_status.inspect",
    "reconciliation.apply",
    "reconciliation.undo",
    "journal_item.search",
    "report.trial_balance",
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


def _enabled_runtime(allow_env: str = _ALLOW_ENV) -> tuple[Path, dict[str, Any]]:
    assert pytest is not None
    if os.environ.get(allow_env) != "1":
        pytest.skip(f"set {allow_env}=1 to authorize isolated write smoke")
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
    *,
    refund_only: bool = False,
) -> None:
    command, timeout = _worker_command(alias, run_id, config_path, runtime)
    if refund_only:
        command.append("--refund-only")
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
    expected = {
        "alias": alias,
        "capabilities": sorted(_REFUND_CAPABILITIES if refund_only else _CAPABILITIES),
        "company_id": _COMPANY_ID,
        "database": _DATABASES[alias],
        "execution": "in_process_cli_real_orm",
        "rollback_verified": True,
        "user_id": _USER_ID,
    }
    if refund_only:
        expected.update(
            {
                "source_documents": 2,
                "credit_notes": 4,
                "posted_journal_items": 12,
                "account_storno": True,
                "source_residuals": {
                    "customer": ["120", "80", "0"],
                    "supplier": ["120", "80", "0"],
                },
                "trial_balance_period_delta": {
                    "opening_balance": "0",
                    "debit": "0",
                    "credit": "0",
                    "closing_balance": "0",
                },
                "source_only_trial_balance_delta": {"debit": "120", "credit": "120"},
                "absolute_journal_item_movement": {"debit": "480", "credit": "480"},
                "final_reconciliations": {"partial": 4, "full": 2},
                "tracked_reconciliations": {"partial": 8, "full": 4},
            }
        )
    else:
        expected.update(
            {"accounting_dates_verified": True, "marker_migration_verified": True}
        )
    assert json.loads(completed.stdout) == expected
    print(completed.stdout.strip(), flush=True)


if pytest is not None:

    @pytest.mark.integration
    def test_document_lifecycle_batch_rolls_back_one_real_chain_per_alias() -> None:
        config_path, runtime = _enabled_runtime()
        run_id = uuid.uuid4()
        for alias in _ALIASES:
            _run_worker(alias, run_id, config_path, runtime)

    @pytest.mark.integration
    def test_financial_refunds_reconcile_and_roll_back_per_alias() -> None:
        config_path, runtime = _enabled_runtime(_REFUND_ALLOW_ENV)
        run_id = uuid.uuid4()
        for alias in _ALIASES:
            _run_worker(alias, run_id, config_path, runtime, refund_only=True)


def _arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-worker", action="store_true", required=True)
    parser.add_argument("--odoo-config", type=Path, required=True)
    parser.add_argument("--odoo-source", type=Path, required=True)
    parser.add_argument("--alias", choices=_ALIASES, required=True)
    parser.add_argument("--database", choices=tuple(_DATABASES.values()), required=True)
    parser.add_argument("--run-id", type=uuid.UUID, required=True)
    parser.add_argument("--refund-only", action="store_true")
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


def _refund_document_balance(
    client: core._RuntimeClient,
    alias: str,
    run_id: uuid.UUID,
    move_id: int,
    move_type: str,
    total: int,
    residual: int,
) -> Decimal:
    data = core._cli(client, alias, run_id, "invoice.get", {"invoice_id": move_id})
    assert (data["id"], data["move_type"], data["state"]) == (
        move_id,
        move_type,
        "posted",
    )
    assert Decimal(data["amount_total"]) == Decimal(data["amount_untaxed"]) == total
    assert Decimal(data["amount_tax"]) == 0
    actual_residual = Decimal(data["amount_residual"])
    assert actual_residual == residual, (
        f"{move_type} {move_id}: expected residual {residual}, "
        f"got {actual_residual}; payment_state={data['payment_state']}"
    )
    return actual_residual


def _exercise_financial_refunds(
    client: core._RuntimeClient,
    alias: str,
    run_id: uuid.UUID,
    ids: dict[str, int],
    today: str,
    trial_balance_baseline: list[Decimal],
    *,
    supplier: bool,
) -> tuple[list[str], dict[int, int], int, list[Decimal] | None, set[int], int]:
    side = "supplier" if supplier else "customer"
    source_type, refund_type = (
        ("in_invoice", "in_refund")
        if supplier
        else (
            "out_invoice",
            "out_refund",
        )
    )
    source_capability = "vendor_bill.create" if supplier else "customer_invoice.create"
    refund_capability = (
        "vendor_refund.create" if supplier else "customer_credit_note.create"
    )
    marker = f"financial-refund:{alias}:{run_id.hex}:{side}"
    line = {
        "name": marker,
        "product_id": None,
        "account_id": ids["expense" if supplier else "income"],
        "quantity": "1",
        "price_unit": "120",
        "discount": "0",
        "tax_ids": [],
    }
    source = core._write(
        client,
        alias,
        run_id,
        source_capability,
        {
            "partner_id": ids[side],
            "journal_id": ids["purchase_journal" if supplier else "sale_journal"],
            "date": today,
            "invoice_date": today,
            "invoice_date_due": today,
            "payment_term_id": None,
            "currency_id": ids["currency"],
            "lines": [line],
        },
        explicit_key=f"{marker}:source",
    )
    source_id = source["id"]
    assert source["move_type"] == source_type and source["state"] == "draft"
    core._write(client, alias, run_id, "invoice.post", {"move_id": source_id})
    source_delta = None
    if not supplier:
        source_totals = core._trial_balance_totals(client, alias, run_id, today)
        source_delta = [
            new - old
            for old, new in zip(trial_balance_baseline, source_totals, strict=True)
        ]
        assert source_delta == [Decimal(0), Decimal(120), Decimal(120), Decimal(0)]
    residuals = [
        format(
            _refund_document_balance(
                client, alias, run_id, source_id, source_type, 120, 120
            ).normalize(),
            "f",
        )
    ]
    documents = {source_id: 120}
    expected_partials: dict[int, int] = {}
    expected_partial_ids: set[int] = set()
    final_full_id = None
    term_account_id = None
    for amount, remaining in ((40, 80), (80, 0)):
        refund = core._write(
            client,
            alias,
            run_id,
            refund_capability,
            {
                "move_id": source_id,
                "date": today,
                "reason": f"{marker}:{amount}",
                "lines": [
                    {**line, "name": f"{marker}:{amount}", "price_unit": str(amount)}
                ],
            },
            explicit_key=f"{marker}:credit:{amount}",
        )
        refund_id = refund["id"]
        assert refund["source_id"] == source_id
        assert refund["move_type"] == refund_type and refund["state"] == "draft"
        core._write(client, alias, run_id, "invoice.post", {"move_id": refund_id})
        # Odoo automatically reconciles a posted credit with its reversed source.
        _refund_document_balance(
            client, alias, run_id, refund_id, refund_type, amount, 0
        )
        _refund_document_balance(
            client, alias, run_id, source_id, source_type, 120, remaining
        )
        automatic = core._cli(
            client,
            alias,
            run_id,
            "invoice.payment_status.inspect",
            {"invoice_id": source_id},
        )
        auto_partial = _one(
            [
                item
                for item in automatic["reconciliations"]
                if item["counterpart_move"]["id"] == refund_id
            ],
            "this credit note's automatic reconciliation",
        )[0]
        assert auto_partial["payment_id"] is None
        assert Decimal(auto_partial["company_amount"]) == amount
        assert len(automatic["reconciliations"]) == len(expected_partial_ids) + 1
        assert {item["id"] for item in automatic["reconciliations"]} == (
            expected_partial_ids | {auto_partial["id"]}
        )
        low, high = sorted(
            (auto_partial["invoice_line_id"], auto_partial["counterpart_line_id"])
        )
        undone = core._write(
            client,
            alias,
            run_id,
            "reconciliation.undo",
            {
                "invoice_id": source_id,
                "partial_reconcile_id": auto_partial["id"],
                "invoice_line_id": auto_partial["invoice_line_id"],
                "counterpart_line_id": auto_partial["counterpart_line_id"],
            },
            explicit_key=(
                f"reconciliation.undo:{source_id}:{auto_partial['id']}:{low}:{high}"
            ),
        )
        assert undone["source_id"] == source_id and undone["id"] is None
        assert undone["partial_reconcile_ids"] == sorted(expected_partial_ids)
        assert undone["full_reconcile_id"] is None and undone["reconciled"] is False
        assert undone["state"] == (
            "partial" if expected_partial_ids else "unreconciled"
        )
        _refund_document_balance(
            client, alias, run_id, source_id, source_type, 120, remaining + amount
        )
        _refund_document_balance(
            client, alias, run_id, refund_id, refund_type, amount, amount
        )
        before = core._cli(
            client,
            alias,
            run_id,
            "invoice.payment_status.inspect",
            {"invoice_id": source_id},
        )
        assert len(before["reconciliations"]) == len(expected_partial_ids)
        assert {
            item["id"] for item in before["reconciliations"]
        } == expected_partial_ids
        assert {
            item["counterpart_move"]["id"]: Decimal(item["company_amount"])
            for item in before["reconciliations"]
        } == expected_partials
        term_line = _one(before["receivable_payable_lines"], "source payment term")[0]
        assert term_line["id"] == auto_partial["invoice_line_id"]
        term_account_id = term_line["account"]["id"]
        candidate = _one(
            [
                item
                for item in before["outstanding_items"]
                if item["move_id"] == refund_id
            ],
            "this credit note's outstanding item",
        )[0]
        assert (
            candidate["payment_id"] is None and Decimal(candidate["amount"]) == amount
        )
        counterpart_id = candidate["line_id"]
        assert counterpart_id == auto_partial["counterpart_line_id"]
        applied = core._write(
            client,
            alias,
            run_id,
            "reconciliation.apply",
            {"invoice_id": source_id, "outstanding_line_id": counterpart_id},
            explicit_key=f"reconciliation.apply:{source_id}:{counterpart_id}",
        )
        assert applied["source_id"] == source_id and applied["id"] is None
        assert applied["line_ids"] == sorted((term_line["id"], counterpart_id))
        assert len(applied["partial_reconcile_ids"]) == 1
        assert applied["partial_reconcile_ids"][0] not in (
            expected_partial_ids | {auto_partial["id"]}
        )
        expected_partial_ids.update(applied["partial_reconcile_ids"])
        assert applied["reconciled"] is (remaining == 0)
        if remaining == 0:
            assert applied["full_reconcile_id"] is not None
            final_full_id = applied["full_reconcile_id"]
        else:
            assert applied["full_reconcile_id"] is None
        residual = _refund_document_balance(
            client, alias, run_id, source_id, source_type, 120, remaining
        )
        residuals.append(format(residual.normalize(), "f"))
        _refund_document_balance(
            client, alias, run_id, refund_id, refund_type, amount, 0
        )
        after = core._cli(
            client,
            alias,
            run_id,
            "invoice.payment_status.inspect",
            {"invoice_id": source_id},
        )
        expected_partials[refund_id] = amount
        assert len(after["reconciliations"]) == len(expected_partials)
        assert {item["id"] for item in after["reconciliations"]} == expected_partial_ids
        assert {
            item["counterpart_move"]["id"]: Decimal(item["company_amount"])
            for item in after["reconciliations"]
        } == expected_partials
        assert all(item["payment_id"] is None for item in after["reconciliations"])
        assert after["payments"] == []
        assert Decimal(after["amount_residual"]) == remaining
        assert after["payment_state"] == ("partial" if remaining else "reversed")
        if remaining == 0:
            assert all(item["reconciled"] for item in after["receivable_payable_lines"])
        documents[refund_id] = -amount
    assert residuals == ["120", "80", "0"] and term_account_id is not None
    assert len(expected_partial_ids) == 2 and final_full_id is not None
    return (
        residuals,
        documents,
        term_account_id,
        source_delta,
        expected_partial_ids,
        final_full_id,
    )


def _run_refund_chain(
    client: core._RuntimeClient, alias: str, run_id: uuid.UUID
) -> dict[str, Any]:
    from odoo import fields

    ids = _fixture_ids(client.env, alias)
    # Existing isolated-fixture setting: inspect it, never alter accounting setup.
    storno = client.env["res.company"].browse(_COMPANY_ID).account_storno
    assert storno is True, "the isolated refund fixture expects red-storno accounting"
    today = fields.Date.to_string(fields.Date.context_today(client.env.user))
    before = core._trial_balance_totals(client, alias, run_id, today)
    traces: dict[str, list[str]] = {}
    source_checkpoint = None
    move_ids: set[int] = set()
    line_ids: set[int] = set()
    final_partial_ids: set[int] = set()
    final_full_ids: set[int] = set()
    signed_totals = [Decimal(0), Decimal(0)]
    absolute_totals = [Decimal(0), Decimal(0)]
    for supplier in (False, True):
        side = "supplier" if supplier else "customer"
        (
            residuals,
            documents,
            term_account,
            checkpoint,
            partial_ids,
            full_id,
        ) = _exercise_financial_refunds(
            client, alias, run_id, ids, today, before, supplier=supplier
        )
        assert final_partial_ids.isdisjoint(partial_ids)
        final_partial_ids.update(partial_ids)
        final_full_ids.add(full_id)
        traces[side] = residuals
        if checkpoint is not None:
            source_checkpoint = checkpoint
        move_ids.update(documents)
        debit_account = ids["expense"] if supplier else term_account
        credit_account = term_account if supplier else ids["income"]
        account_balances: dict[int, Decimal] = {}
        for move_id, signed_amount in documents.items():
            page = core._cli(
                client,
                alias,
                run_id,
                "journal_item.search",
                {
                    "move_id": move_id,
                    "posted_only": True,
                    "limit": 1000,
                    "cursor": None,
                },
            )
            assert page["has_more"] is False and page["next_cursor"] is None
            assert len(page["items"]) == 2
            expected = {
                debit_account: (Decimal(signed_amount), Decimal(0)),
                credit_account: (Decimal(0), Decimal(signed_amount)),
            }
            assert {item["account"]["id"] for item in page["items"]} == set(expected)
            for item in page["items"]:
                assert item["id"] not in line_ids
                line_ids.add(item["id"])
                assert (
                    item["move"]["id"] == move_id and item["move"]["state"] == "posted"
                )
                assert item["company_id"] == _COMPANY_ID and item["date"] == today
                assert item["currency"]["id"] == ids["currency"]
                account_id = item["account"]["id"]
                debit, credit, balance = (
                    Decimal(item[field]) for field in ("debit", "credit", "balance")
                )
                # Red-storno credits are -40/-80 on the original debit/credit side.
                assert (debit, credit) == expected[account_id]
                assert balance == debit - credit
                if account_id == term_account:
                    assert item["reconciled"] is True
                account_balances[account_id] = (
                    account_balances.get(account_id, Decimal(0)) + balance
                )
                signed_totals[0] += debit
                signed_totals[1] += credit
                absolute_totals[0] += abs(debit)
                absolute_totals[1] += abs(credit)
        assert all(value == 0 for value in account_balances.values())
    after = core._trial_balance_totals(client, alias, run_id, today)
    delta = [new - old for old, new in zip(before, after, strict=True)]
    assert signed_totals == [Decimal(0), Decimal(0)]
    assert delta == [Decimal(0), *signed_totals, Decimal(0)]
    assert absolute_totals == [Decimal(480), Decimal(480)]
    assert len(move_ids) == 6 and len(line_ids) == 12
    assert client.tracked["account.move"] == move_ids
    assert len(final_partial_ids) == 4 and len(final_full_ids) == 2
    assert final_partial_ids <= client.tracked["account.partial.reconcile"]
    assert final_full_ids <= client.tracked["account.full.reconcile"]
    # Retain automatic reconciliations deleted by undo for rollback verification.
    assert len(client.tracked["account.partial.reconcile"]) == 8
    assert len(client.tracked["account.full.reconcile"]) == 4
    assert not client.tracked["account.payment"]
    assert not client.tracked["account.bank.statement.line"]
    assert source_checkpoint is not None
    return {
        "source_documents": len(traces),
        "credit_notes": len(move_ids) - len(traces),
        "posted_journal_items": len(line_ids),
        "account_storno": storno,
        "source_residuals": traces,
        "trial_balance_period_delta": {
            field: format(value.normalize(), "f")
            for field, value in zip(
                ("opening_balance", "debit", "credit", "closing_balance"),
                delta,
                strict=True,
            )
        },
        "source_only_trial_balance_delta": {
            "debit": format(source_checkpoint[1].normalize(), "f"),
            "credit": format(source_checkpoint[2].normalize(), "f"),
        },
        "absolute_journal_item_movement": {
            "debit": format(absolute_totals[0].normalize(), "f"),
            "credit": format(absolute_totals[1].normalize(), "f"),
        },
        "final_reconciliations": {
            "partial": len(final_partial_ids),
            "full": len(final_full_ids),
        },
        "tracked_reconciliations": {
            "partial": len(client.tracked["account.partial.reconcile"]),
            "full": len(client.tracked["account.full.reconcile"]),
        },
    }


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
    details: dict[str, Any] = {}
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
        if args.refund_only:
            details = _run_refund_chain(client, args.alias, args.run_id)
            assert client.capabilities == _REFUND_CAPABILITIES
        else:
            _run_chain(client, args.alias, args.run_id)
            assert client.capabilities == _CAPABILITIES
            details = {
                "accounting_dates_verified": True,
                "marker_migration_verified": True,
            }
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
                "alias": args.alias,
                "capabilities": sorted(client.capabilities),
                "company_id": _COMPANY_ID,
                "database": args.database,
                "execution": "in_process_cli_real_orm",
                "rollback_verified": True,
                "user_id": _USER_ID,
                **details,
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
