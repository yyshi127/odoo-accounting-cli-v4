"""Rollback-only dual-database smoke for draft-document maintenance.

The worker creates one invoice and one ordinary journal entry through the public
CLI, exercises the six maintenance commands as uid 5 with ``su=False``, and
rolls the outer transaction back.  A fresh cursor verifies both business data
and any temporary accounting-group membership were restored.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import sysconfig
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any

import test_document_lifecycle_write_batch_live as lifecycle
import test_payment_bank_capability_batch_live as core

try:
    import pytest
except ModuleNotFoundError:
    if "--live-worker" not in sys.argv:
        raise
    pytest = None


_ALLOW_ENV = "ODACV4_ALLOW_DRAFT_DOCUMENT_MAINTENANCE_SMOKE"
_GROUPS = (
    "account.group_account_invoice",
    "account.group_account_user",
)
_NEW_CAPABILITIES = {
    "invoice.line.create",
    "invoice.line.update",
    "invoice.line.delete",
    "invoice.delete",
    "journal_entry.duplicate",
    "journal_entry.delete",
}
_SETUP_CAPABILITIES = {
    "customer_invoice.create",
    "journal_entry.create",
}
_ALL_CAPABILITIES = _NEW_CAPABILITIES | _SETUP_CAPABILITIES


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _run_worker(
    alias: str,
    run_id: uuid.UUID,
    config_path: Path,
    runtime: dict[str, Any],
) -> None:
    command, timeout = lifecycle._worker_command(
        alias, run_id, config_path, runtime
    )
    command[1] = str(Path(__file__).resolve())
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
    results = [
        json.loads(line)
        for line in completed.stdout.splitlines()
        if line.startswith("{")
    ]
    assert len(results) == 1
    result = results[0]
    assert result == {
        "alias": alias,
        "capabilities": sorted(_ALL_CAPABILITIES),
        "company_id": lifecycle._COMPANY_ID,
        "database": lifecycle._DATABASES[alias],
        "deleted_documents": 2,
        "execution": "in_process_cli_real_orm",
        "group_membership_rolled_back": True,
        "immediate_replays": 5,
        "invoice_lines_created": 1,
        "invoice_lines_deleted": 1,
        "invoice_lines_updated": 1,
        "journal_entries_duplicated": 1,
        "new_capabilities": sorted(_NEW_CAPABILITIES),
        "rollback_verified": True,
        "user_id": lifecycle._USER_ID,
    }


if pytest is not None:

    @pytest.mark.integration
    def test_draft_document_maintenance_rolls_back_per_alias() -> None:
        config_path, runtime = lifecycle._enabled_runtime(_ALLOW_ENV)
        run_id = uuid.uuid4()
        for alias in lifecycle._ALIASES:
            _run_worker(alias, run_id, config_path, runtime)


def _write_key(
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    parameters: dict[str, Any],
    explicit: str | None = None,
) -> str:
    from odoo_accounting_cli_v4.capabilities.core_writes import (
        _expected_idempotency_key,
        validate_core_write_request,
    )

    request = core._request(alias, run_id, capability_id, parameters)
    _, context, normalized = validate_core_write_request(capability_id, request)
    expected = _expected_idempotency_key(
        capability_id, normalized, context["company_id"]
    )
    if expected is not None:
        if explicit is not None and explicit != expected:
            raise RuntimeError(f"{capability_id} received a noncanonical key")
        return expected
    if explicit is None:
        raise RuntimeError(f"{capability_id} requires a caller-chosen key")
    return explicit


def _write_once(
    client: core._RuntimeClient,
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    parameters: dict[str, Any],
    *,
    explicit_key: str | None = None,
) -> dict[str, Any]:
    key = _write_key(
        alias, run_id, capability_id, parameters, explicit=explicit_key
    )
    data = core._cli(
        client, alias, run_id, capability_id, parameters, key=key
    )
    assert data["idempotent_replay"] is False
    result = data["result"]
    assert set(result) == lifecycle._RESULT_KEYS
    assert result["company_id"] == lifecycle._COMPANY_ID
    return result


def _write_twice(
    client: core._RuntimeClient,
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    parameters: dict[str, Any],
    *,
    explicit_key: str | None = None,
) -> dict[str, Any]:
    key = _write_key(
        alias, run_id, capability_id, parameters, explicit=explicit_key
    )
    first = core._cli(
        client, alias, run_id, capability_id, parameters, key=key
    )
    tracked = {
        model: set(record_ids) for model, record_ids in client.tracked.items()
    }
    second = core._cli(
        client, alias, run_id, capability_id, parameters, key=key
    )
    assert first["idempotent_replay"] is False
    assert second["idempotent_replay"] is True
    assert first["result"] == second["result"]
    assert client.tracked == tracked
    result = first["result"]
    assert set(result) == lifecycle._RESULT_KEYS
    assert result["company_id"] == lifecycle._COMPANY_ID
    return result


def _entry_signature(move: Any) -> list[tuple[Any, ...]]:
    return sorted(
        (
            line.name,
            line.account_id.id,
            line.partner_id.id or None,
            Decimal(str(line.debit)),
            Decimal(str(line.credit)),
        )
        for line in move.line_ids
    )


def _run_chain(
    client: core._RuntimeClient,
    alias: str,
    run_id: uuid.UUID,
) -> dict[str, int]:
    from odoo import fields

    env = client.env
    assert (
        env.uid == lifecycle._USER_ID
        and not env.su
        and env.company.id == lifecycle._COMPANY_ID
    )
    ids = lifecycle._fixture_ids(env, alias)
    today = fields.Date.to_string(fields.Date.context_today(env.user))
    marker = f"ODACV4-DRAFT-MAINT-{alias}-{run_id.hex}"

    invoice = _write_twice(
        client,
        alias,
        run_id,
        "customer_invoice.create",
        {
            "partner_id": ids["customer"],
            "journal_id": ids["sale_journal"],
            "date": today,
            "invoice_date": today,
            "currency_id": ids["currency"],
            "reference": marker,
            "lines": [
                {
                    "name": f"{marker}-ORIGINAL",
                    "account_id": ids["income"],
                    "product_id": None,
                    "quantity": "1",
                    "price_unit": "20",
                    "discount": "0",
                    "tax_ids": [],
                }
            ],
        },
        explicit_key=f"{marker}-invoice-create",
    )
    invoice_id = invoice["id"]
    assert isinstance(invoice_id, int) and invoice["state"] == "draft"
    move = env["account.move"].browse(invoice_id).exists()
    original_lines = move.invoice_line_ids.filtered(
        lambda line: line.name == f"{marker}-ORIGINAL"
    )
    assert len(original_lines) == 1

    created = _write_twice(
        client,
        alias,
        run_id,
        "invoice.line.create",
        {
            "move_id": invoice_id,
            "line": {
                "name": f"{marker}-CREATED",
                "product_id": None,
                "account_id": ids["income"],
                "quantity": "2",
                "price_unit": "12.50",
                "discount": "0",
                "tax_ids": [],
            },
        },
    )
    line_id = created["source_id"]
    assert (
        isinstance(line_id, int)
        and created["id"] == invoice_id
        and created["state"] == "draft"
        and line_id in created["line_ids"]
    )

    updated_name = f"{marker}-UPDATED"
    updated = _write_twice(
        client,
        alias,
        run_id,
        "invoice.line.update",
        {
            "move_id": invoice_id,
            "line_id": line_id,
            "changes": {
                "name": updated_name,
                "quantity": "3",
                "price_unit": "11.25",
                "discount": "5",
            },
        },
    )
    assert updated["id"] == invoice_id and updated["source_id"] == line_id
    line = env["account.move.line"].browse(line_id).exists()
    line.invalidate_recordset(["name", "quantity", "price_unit", "discount"])
    assert (
        line.name == updated_name
        and Decimal(str(line.quantity)) == Decimal(3)
        and Decimal(str(line.price_unit)) == Decimal("11.25")
        and Decimal(str(line.discount)) == Decimal(5)
    )

    deleted_line = _write_once(
        client,
        alias,
        run_id,
        "invoice.line.delete",
        {"move_id": invoice_id, "line_id": line_id},
    )
    assert (
        deleted_line["id"] == invoice_id
        and deleted_line["state"] == "draft"
        and deleted_line["source_id"] == line_id
        and line_id not in deleted_line["line_ids"]
        and not env["account.move.line"].browse(line_id).exists()
    )

    deleted_invoice = _write_once(
        client,
        alias,
        run_id,
        "invoice.delete",
        {"move_id": invoice_id},
    )
    assert (
        deleted_invoice["id"] == invoice_id
        and deleted_invoice["state"] == "deleted"
        and deleted_invoice["source_id"] is None
        and not env["account.move"].browse(invoice_id).exists()
    )

    source = _write_twice(
        client,
        alias,
        run_id,
        "journal_entry.create",
        {
            "journal_id": ids["general_journal"],
            "date": today,
            "reference": marker,
            "lines": [
                {
                    "name": f"{marker}-DEBIT",
                    "account_id": ids["asset"],
                    "partner_id": None,
                    "debit": "40",
                    "credit": "0",
                },
                {
                    "name": f"{marker}-CREDIT",
                    "account_id": ids["income"],
                    "partner_id": None,
                    "debit": "0",
                    "credit": "40",
                },
            ],
        },
        explicit_key=f"{marker}-entry-create",
    )
    source_id = source["id"]
    assert isinstance(source_id, int) and source["state"] == "draft"
    source_move = env["account.move"].browse(source_id).exists()
    source_signature = _entry_signature(source_move)

    duplicate = _write_twice(
        client,
        alias,
        run_id,
        "journal_entry.duplicate",
        {"move_id": source_id},
        explicit_key=f"{marker}-entry-duplicate",
    )
    duplicate_id = duplicate["id"]
    duplicate_move = env["account.move"].browse(duplicate_id).exists()
    assert (
        isinstance(duplicate_id, int)
        and duplicate_id != source_id
        and duplicate["source_id"] == source_id
        and duplicate["state"] == "draft"
        and duplicate["move_type"] == "entry"
        and set(duplicate["line_ids"]).isdisjoint(source["line_ids"])
        and _entry_signature(duplicate_move) == source_signature
    )

    deleted_entry = _write_once(
        client,
        alias,
        run_id,
        "journal_entry.delete",
        {"move_id": duplicate_id},
    )
    assert (
        deleted_entry["id"] == duplicate_id
        and deleted_entry["state"] == "deleted"
        and deleted_entry["source_id"] is None
        and not env["account.move"].browse(duplicate_id).exists()
        and env["account.move"].browse(source_id).exists()
    )
    assert client.capabilities == _ALL_CAPABILITIES
    return {
        "deleted_documents": 2,
        "immediate_replays": 5,
        "invoice_lines_created": 1,
        "invoice_lines_deleted": 1,
        "invoice_lines_updated": 1,
        "journal_entries_duplicated": 1,
    }


def _direct_groups(cursor: Any, group_ids: dict[str, int]) -> dict[str, bool]:
    cursor.execute(
        "SELECT gid FROM res_groups_users_rel WHERE uid = %s AND gid IN %s",
        [lifecycle._USER_ID, tuple(group_ids.values())],
    )
    direct = {row[0] for row in cursor.fetchall()}
    return {group: group_id in direct for group, group_id in group_ids.items()}


def _verify_rollback(
    registry: Any,
    tracked: dict[str, set[int]],
    marker: str,
    group_ids: dict[str, int],
    baseline_groups: dict[str, bool],
) -> None:
    from odoo import SUPERUSER_ID, api

    cursor = registry.cursor()
    try:
        env = api.Environment(
            cursor,
            SUPERUSER_ID,
            {
                "allowed_company_ids": [lifecycle._COMPANY_ID],
                "active_test": False,
            },
        )
        leaked = {model: set(record_ids) for model, record_ids in tracked.items()}
        core._collect_marked(env, leaked, marker)
        remaining = {
            model: env[model].search_count(
                [("id", "in", sorted(record_ids))], limit=1
            )
            for model, record_ids in leaked.items()
            if record_ids
        }
        if any(remaining.values()):
            raise RuntimeError(
                f"draft-document fixtures survived rollback: {remaining}"
            )
        if _direct_groups(cursor, group_ids) != baseline_groups:
            raise RuntimeError("temporary accounting groups survived rollback")
    finally:
        cursor.rollback()
        cursor.close()


def _live_worker() -> int:
    args = lifecycle._arguments(None)
    assert not (
        args.refund_only
        or args.payment_difference_only
        or args.analytic_readback_only
    )
    sys.path.insert(0, str(args.odoo_source.resolve(strict=True)))
    sys.path.insert(0, str((_root() / "src").resolve(strict=True)))

    from odoo import SUPERUSER_ID, Command, api
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
    marker = f"ODACV4-DRAFT-MAINT-{args.alias}-{args.run_id.hex}"
    tracked = {model: set() for model in core._BUSINESS_MODELS}
    group_ids: dict[str, int] | None = None
    baseline_groups: dict[str, bool] | None = None
    admin_env = client = None
    details: dict[str, int] | None = None
    failure: BaseException | None = None
    try:
        context = {
            "allowed_company_ids": [lifecycle._COMPANY_ID],
            "active_test": False,
            "lang": "en_US",
            "tz": "Asia/Shanghai",
            "mail_create_nosubscribe": True,
            "tracking_disable": True,
            "mail_notrack": True,
        }
        admin_env = api.Environment(cursor, SUPERUSER_ID, context)
        company = admin_env["res.company"].browse(lifecycle._COMPANY_ID).exists()
        user = admin_env["res.users"].browse(lifecycle._USER_ID).exists()
        if (
            not company
            or not user
            or not user.active
            or user.login != lifecycle._USER_LOGIN
            or company not in user.company_ids
        ):
            raise RuntimeError("the configured company or business user is unavailable")
        group_ids = {group: admin_env.ref(group).id for group in _GROUPS}
        baseline_groups = _direct_groups(cursor, group_ids)
        missing = [
            group_id
            for group, group_id in group_ids.items()
            if not user.has_group(group)
        ]
        if missing:
            user.write({"group_ids": [Command.link(group_id) for group_id in missing]})
            admin_env.flush_all()

        business_env = api.Environment(
            cursor, lifecycle._USER_ID, {**context, "active_test": True}
        )
        if (
            business_env.uid != lifecycle._USER_ID
            or business_env.su
            or business_env.company.id != lifecycle._COMPANY_ID
            or business_env.user.login != lifecycle._USER_LOGIN
            or not all(business_env.user.has_group(group) for group in _GROUPS)
        ):
            raise RuntimeError("uid 5 or its accounting groups are unavailable")
        client = core._RuntimeClient(business_env)
        client.tracked = tracked
        details = _run_chain(client, args.alias, args.run_id)
    except BaseException as exc:  # noqa: BLE001 - verify rollback before re-raising
        failure = exc
    finally:
        try:
            if admin_env is not None:
                admin_env.invalidate_all()
                core._collect_marked(admin_env, tracked, marker)
        except Exception as exc:  # noqa: BLE001 - collection must not prevent rollback
            if failure is None:
                failure = exc
            else:
                failure.add_note(f"rollback collection also failed: {exc}")
        finally:
            try:
                cursor.rollback()
            finally:
                cursor.close()

    if group_ids is not None and baseline_groups is not None:
        try:
            _verify_rollback(
                registry, tracked, marker, group_ids, baseline_groups
            )
        except Exception as exc:
            raise exc from failure
    if failure is not None:
        raise failure
    if client is None or details is None:
        raise RuntimeError("the draft-document smoke did not run")
    sys.stdout.write(
        json.dumps(
            {
                "alias": args.alias,
                "capabilities": sorted(client.capabilities),
                "company_id": lifecycle._COMPANY_ID,
                "database": args.database,
                "execution": "in_process_cli_real_orm",
                "group_membership_rolled_back": True,
                "new_capabilities": sorted(_NEW_CAPABILITIES),
                "rollback_verified": True,
                "user_id": lifecycle._USER_ID,
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
