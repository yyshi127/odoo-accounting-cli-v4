"""Rollback-only dual-database smoke for bank/payment maintenance writes.

Every capability runs through the public CLI as the configured accountant with
``su=False``.  The worker creates one small statement/payment chain, exercises
the six maintenance commands, rolls back the outer transaction, and checks the
same physical database again from a fresh cursor.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any

try:
    import pytest
except ModuleNotFoundError:
    if "--live-worker" not in sys.argv:
        raise
    pytest = None


_CONFIG_ENV = "ODOO_ACCOUNTING_CLI_V4_CONFIG"
_ALLOW_ENV = "ODACV4_ALLOW_BANK_PAYMENT_MAINTENANCE_SMOKE"
_ALIASES = ("v4-dev", "v4-e2e")
_DATABASES = {
    "v4-dev": "odoo_cli_v4_dev",
    "v4-e2e": "odoo_cli_v4_e2e",
}
_PARTNERS = {"v4-dev": 16, "v4-e2e": 8}
_COMPANY_ID = 1
_USER_ID = 5
_USER_LOGIN = "odacv4_g5_accountant"
_NEW_CAPABILITIES = (
    "bank.statement.create",
    "bank.statement.update",
    "bank.statement.delete",
    "bank.transaction.delete",
    "payment.duplicate",
    "payment.delete",
)
_ALL_CAPABILITIES = (
    "bank.transaction.record",
    "bank.statement.create",
    "bank.statement.get",
    "bank.statement.update",
    "bank.statement.delete",
    "bank.transaction.delete",
    "payment.create",
    "payment.duplicate",
    "payment.get",
    "payment.delete",
)


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
    assert {alias: aliases[alias].get("database") for alias in _ALIASES} == (_DATABASES)
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
    assert completed.stderr == ""
    assert len(completed.stdout.splitlines()) == 1
    assert json.loads(completed.stdout) == {
        "alias": alias,
        "business_su": False,
        "capabilities": list(_ALL_CAPABILITIES),
        "company_id": _COMPANY_ID,
        "database": _DATABASES[alias],
        "immediate_replays": 3,
        "new_capabilities": list(_NEW_CAPABILITIES),
        "rollback_verified": True,
        "user_id": _USER_ID,
        "verification_reads": ["bank.statement.get", "payment.get"],
    }


if pytest is not None:

    @pytest.mark.integration
    def test_bank_payment_maintenance_rolls_back_one_chain_per_alias() -> None:
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


def _request(
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    identity = json.dumps(
        [capability_id, parameters],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return {
        "schema_version": "v1",
        "request_id": str(uuid.uuid5(run_id, identity)),
        "context": {
            "database": alias,
            "company_id": _COMPANY_ID,
            "user_login": _USER_LOGIN,
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": parameters,
    }


class _DirectClient:
    def __init__(self, env: Any) -> None:
        self.env = env
        self.capabilities: list[str] = []

    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        if self.env.uid != _USER_ID or self.env.su:
            raise RuntimeError("a public capability escaped uid 5 with su=False")
        from odoo_accounting_cli_v4.bridge.runtime import _dispatch

        self.env.invalidate_all()
        return _dispatch(
            self.env,
            action,
            payload,
            _COMPANY_ID,
            (_COMPANY_ID,),
        )


def _invoke(
    client: _DirectClient,
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    parameters: dict[str, Any],
    *,
    key: str | None = None,
) -> dict[str, Any]:
    from odoo_accounting_cli_v4 import cli
    from odoo_accounting_cli_v4.bridge.core_object_reads import OdooCoreObjectReadPort
    from odoo_accounting_cli_v4.bridge.core_writes import OdooCoreWritePort
    from odoo_accounting_cli_v4.bridge.payments import OdooPaymentPort

    request = _request(alias, run_id, capability_id, parameters)
    if key is not None:
        port = OdooCoreWritePort(client)
        argv = [
            "write",
            "run",
            capability_id,
            "--request",
            "-",
            "--idempotency-key",
            key,
            "--confirm",
            capability_id,
        ]
    else:
        port = (
            OdooPaymentPort(client)
            if capability_id == "payment.get"
            else OdooCoreObjectReadPort(client)
        )
        argv = ["read", capability_id, "--request", "-"]
    stdout, stderr = io.StringIO(), io.StringIO()
    exit_code = cli.main(
        argv,
        stdin=io.StringIO(json.dumps(request)),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda _capability, _request: port,
    )
    if exit_code != 0:
        raise AssertionError(f"{capability_id}: {stdout.getvalue()}{stderr.getvalue()}")
    if stderr.getvalue() or len(stdout.getvalue().splitlines()) != 1:
        raise RuntimeError(f"{capability_id} emitted an invalid CLI response")
    response = json.loads(stdout.getvalue())
    if (
        response["request_id"] != request["request_id"]
        or response["capability"] != capability_id
        or response["schema_version"] != "v1"
        or response["success"] is not True
        or response["status"] != "verified"
        or response["error"] is not None
        or response["odoo"]["database"] != alias
        or response["odoo"]["company_id"] != _COMPANY_ID
        or response["odoo"]["user_id"] != _USER_ID
    ):
        raise RuntimeError(f"{capability_id} returned invalid CLI metadata")
    if capability_id not in client.capabilities:
        client.capabilities.append(capability_id)
    return response["data"]


def _write(
    client: _DirectClient,
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    parameters: dict[str, Any],
    *,
    replayable: bool,
) -> dict[str, Any]:
    from odoo_accounting_cli_v4.capabilities.core_writes import (
        _expected_idempotency_key,
        validate_core_write_request,
    )

    request = _request(alias, run_id, capability_id, parameters)
    _, context, normalized = validate_core_write_request(capability_id, request)
    key = _expected_idempotency_key(capability_id, normalized, context["company_id"])
    if key is None:
        raise RuntimeError(f"{capability_id} lacks its deterministic key")
    first = _invoke(
        client,
        alias,
        run_id,
        capability_id,
        parameters,
        key=key,
    )
    if first["idempotent_replay"] is not False:
        raise RuntimeError(f"{capability_id} replayed its first execution")
    if replayable:
        replay = _invoke(
            client,
            alias,
            run_id,
            capability_id,
            parameters,
            key=key,
        )
        if (
            replay["idempotent_replay"] is not True
            or replay["result"] != first["result"]
        ):
            raise RuntimeError(f"{capability_id} did not replay deterministically")
    return first["result"]


def _read(
    client: _DirectClient,
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    return _invoke(client, alias, run_id, capability_id, parameters)


def _fixture(env: Any, alias: str) -> dict[str, int]:
    company = env["res.company"].browse(_COMPANY_ID).exists()
    partner = env["res.partner"].browse(_PARTNERS[alias]).exists()
    methods = env["account.payment.method.line"].search(
        [
            ("journal_id.company_id", "=", _COMPANY_ID),
            ("journal_id.type", "=", "bank"),
            ("journal_id.active", "=", True),
            ("payment_type", "=", "inbound"),
            ("payment_method_id.code", "=", "manual"),
        ],
        order="journal_id,id",
    )
    method = next(
        (
            candidate
            for candidate in methods
            if candidate.journal_id.default_account_id
            and candidate.journal_id.suspense_account_id
        ),
        env["account.payment.method.line"],
    )
    if (
        not company
        or len(partner) != 1
        or (partner.company_id and partner.company_id != company)
        or not method
    ):
        raise RuntimeError(
            "the bank journal, payment method, or partner is unavailable"
        )
    return {
        "bank_journal": method.journal_id.id,
        "currency": company.currency_id.id,
        "partner": partner.id,
        "payment_method": method.id,
    }


def _assert_result(
    result: dict[str, Any],
    *,
    model: str,
    state: str | set[str],
    record_id: int | None = None,
    source_id: int | None = None,
    move_type: str | None = None,
) -> int:
    states = {state} if isinstance(state, str) else state
    result_id = result.get("id")
    if (
        result.get("model") != model
        or not isinstance(result_id, int)
        or isinstance(result_id, bool)
        or result_id <= 0
        or (record_id is not None and result_id != record_id)
        or result.get("state") not in states
        or result.get("company_id") != _COMPANY_ID
        or result.get("move_type") != move_type
        or result.get("source_id") != source_id
        or result.get("partial_reconcile_ids")
        or result.get("full_reconcile_id") is not None
        or result.get("reconciled")
    ):
        raise RuntimeError(f"invalid maintenance result: {result}")
    return result_id


def _record_transaction(
    client: _DirectClient,
    alias: str,
    run_id: uuid.UUID,
    fixture: dict[str, int],
    date: str,
    marker: str,
    amount: str,
) -> tuple[int, int, set[int]]:
    result = _write(
        client,
        alias,
        run_id,
        "bank.transaction.record",
        {
            "journal_id": fixture["bank_journal"],
            "date": date,
            "amount": amount,
            "payment_ref": marker,
            "partner_id": fixture["partner"],
        },
        replayable=False,
    )
    move_id = result.get("source_id")
    if not isinstance(move_id, int) or isinstance(move_id, bool) or move_id <= 0:
        raise RuntimeError("bank transaction result omitted its journal entry")
    transaction_id = _assert_result(
        result,
        model="account.bank.statement.line",
        state="posted",
        source_id=move_id,
        move_type="entry",
    )
    transaction = (
        client.env["account.bank.statement.line"].browse(transaction_id).exists()
    )
    if (
        len(transaction) != 1
        or transaction.statement_id
        or transaction.move_id.id != move_id
    ):
        raise RuntimeError("bank transaction fixture was not created ungrouped")
    return transaction_id, move_id, set(transaction.move_id.line_ids.ids)


def _exercise(
    client: _DirectClient,
    alias: str,
    run_id: uuid.UUID,
    fixture: dict[str, int],
    date: str,
    marker: str,
) -> dict[str, set[int]]:
    tracked = {
        "account.bank.statement": set(),
        "account.bank.statement.line": set(),
        "account.payment": set(),
        "account.move": set(),
        "account.move.line": set(),
    }
    first_id, first_move_id, first_line_ids = _record_transaction(
        client, alias, run_id, fixture, date, f"{marker}-BANK-40", "40"
    )
    second_id, second_move_id, second_line_ids = _record_transaction(
        client, alias, run_id, fixture, date, f"{marker}-BANK-60", "60"
    )
    transaction_ids = sorted([first_id, second_id])
    tracked["account.bank.statement.line"].update(transaction_ids)
    tracked["account.move"].update([first_move_id, second_move_id])
    tracked["account.move.line"].update(first_line_ids | second_line_ids)

    original_reference = f"{marker}-STATEMENT"
    created = _write(
        client,
        alias,
        run_id,
        "bank.statement.create",
        {
            "transaction_ids": list(reversed(transaction_ids)),
            "reference": original_reference,
            "balance_end_real": "100",
        },
        replayable=True,
    )
    statement_id = _assert_result(
        created,
        model="account.bank.statement",
        state={"complete", "incomplete"},
    )
    tracked["account.bank.statement"].add(statement_id)
    if created["line_ids"] != transaction_ids:
        raise RuntimeError("statement create returned the wrong transactions")
    statement = _read(
        client,
        alias,
        run_id,
        "bank.statement.get",
        {"bank_statement_id": statement_id},
    )
    if (
        statement["id"] != statement_id
        or statement["reference"] != original_reference
        or statement["transaction_count"] != 2
    ):
        raise RuntimeError("bank.statement.get did not read back the created statement")

    updated_reference = f"{marker}-UPDATED"
    updated = _write(
        client,
        alias,
        run_id,
        "bank.statement.update",
        {
            "statement_id": statement_id,
            "changes": {
                "reference": updated_reference,
                "balance_end_real": "105",
            },
        },
        replayable=True,
    )
    _assert_result(
        updated,
        model="account.bank.statement",
        state={"complete", "incomplete"},
        record_id=statement_id,
    )
    reread = _read(
        client,
        alias,
        run_id,
        "bank.statement.get",
        {"bank_statement_id": statement_id},
    )
    if (
        reread["reference"] != updated_reference
        or Decimal(reread["balance_end_real"]) != Decimal(105)
        or reread["transaction_count"] != 2
    ):
        raise RuntimeError("bank.statement.update did not persist its two fields")

    deleted_statement = _write(
        client,
        alias,
        run_id,
        "bank.statement.delete",
        {"statement_id": statement_id},
        replayable=False,
    )
    _assert_result(
        deleted_statement,
        model="account.bank.statement",
        state="deleted",
        record_id=statement_id,
    )
    if deleted_statement["line_ids"] != transaction_ids:
        raise RuntimeError("statement delete returned the wrong transactions")
    if client.env["account.bank.statement"].browse(statement_id).exists():
        raise RuntimeError("bank.statement.delete left the statement present")
    remaining_transactions = (
        client.env["account.bank.statement.line"].browse(transaction_ids).exists()
    )
    if set(remaining_transactions.ids) != set(transaction_ids) or any(
        remaining_transactions.mapped("statement_id")
    ):
        raise RuntimeError("statement delete did not preserve ungrouped transactions")

    deleted_transaction = _write(
        client,
        alias,
        run_id,
        "bank.transaction.delete",
        {"transaction_id": first_id},
        replayable=False,
    )
    _assert_result(
        deleted_transaction,
        model="account.bank.statement.line",
        state="deleted",
        record_id=first_id,
        source_id=first_move_id,
        move_type="entry",
    )
    if deleted_transaction["line_ids"] != sorted(first_line_ids):
        raise RuntimeError("bank transaction delete returned the wrong journal items")
    if (
        client.env["account.bank.statement.line"].browse(first_id).exists()
        or client.env["account.move"].browse(first_move_id).exists()
    ):
        raise RuntimeError(
            "bank.transaction.delete left the transaction or move present"
        )

    payment_reference = f"{marker}-PAYMENT"
    payment = _write(
        client,
        alias,
        run_id,
        "payment.create",
        {
            "payment_type": "inbound",
            "partner_type": "customer",
            "partner_id": fixture["partner"],
            "amount": "25",
            "currency_id": fixture["currency"],
            "journal_id": fixture["bank_journal"],
            "payment_method_line_id": fixture["payment_method"],
            "date": date,
            "payment_reference": payment_reference,
        },
        replayable=False,
    )
    payment_id = _assert_result(
        payment,
        model="account.payment",
        state="draft",
    )
    source_payment = client.env["account.payment"].browse(payment_id).exists()
    tracked["account.payment"].add(payment_id)
    if source_payment.move_id:
        tracked["account.move"].add(source_payment.move_id.id)
        tracked["account.move.line"].update(source_payment.move_id.line_ids.ids)

    duplicated = _write(
        client,
        alias,
        run_id,
        "payment.duplicate",
        {"payment_id": payment_id},
        replayable=True,
    )
    duplicate_id = _assert_result(
        duplicated,
        model="account.payment",
        state="draft",
        source_id=payment_id,
    )
    duplicate = client.env["account.payment"].browse(duplicate_id).exists()
    if len(duplicate) != 1 or duplicate_id == payment_id:
        raise RuntimeError("payment.duplicate did not create a distinct draft")
    duplicate_move_id = duplicate.move_id.id or None
    tracked["account.payment"].add(duplicate_id)
    if duplicate.move_id:
        tracked["account.move"].add(duplicate.move_id.id)
        tracked["account.move.line"].update(duplicate.move_id.line_ids.ids)
    payment_read = _read(
        client,
        alias,
        run_id,
        "payment.get",
        {"payment_id": duplicate_id},
    )
    if (
        payment_read["id"] != duplicate_id
        or payment_read["state"] != "draft"
        or Decimal(payment_read["amount"]) != Decimal(25)
        or payment_read["journal"]["id"] != fixture["bank_journal"]
    ):
        raise RuntimeError("payment.get did not read back the duplicate")

    deleted_payment = _write(
        client,
        alias,
        run_id,
        "payment.delete",
        {"payment_id": duplicate_id},
        replayable=False,
    )
    _assert_result(
        deleted_payment,
        model="account.payment",
        state="deleted",
        record_id=duplicate_id,
    )
    if (
        client.env["account.payment"].browse(duplicate_id).exists()
        or (
            duplicate_move_id is not None
            and client.env["account.move"].browse(duplicate_move_id).exists()
        )
        or not client.env["account.payment"].browse(payment_id).exists()
    ):
        raise RuntimeError("payment.delete removed the wrong record or left its move")
    return tracked


def _verify_rollback(
    registry: Any,
    *,
    tracked: dict[str, set[int]],
    marker: str,
) -> None:
    from odoo import SUPERUSER_ID, api

    cursor = registry.cursor()
    try:
        env = api.Environment(
            cursor,
            SUPERUSER_ID,
            {"allowed_company_ids": [_COMPANY_ID], "active_test": False},
        )
        survivors = {
            model: env[model].search_count([("id", "in", sorted(record_ids))])
            for model, record_ids in tracked.items()
        }
        survivors.update(
            {
                "statement_marker": env["account.bank.statement"].search_count(
                    [("reference", "ilike", marker)]
                ),
                "transaction_marker": env["account.bank.statement.line"].search_count(
                    [("payment_ref", "ilike", marker)]
                ),
                "payment_marker": env["account.payment"].search_count(
                    [
                        "|",
                        ("payment_reference", "ilike", marker),
                        ("memo", "ilike", marker),
                    ]
                ),
            }
        )
        if any(survivors.values()):
            raise RuntimeError(f"maintenance fixtures survived rollback: {survivors}")
    finally:
        cursor.rollback()
        cursor.close()


def _live_worker(argv: list[str] | None = None) -> int:
    args = _arguments(argv)
    sys.path.insert(0, str(args.odoo_source.resolve(strict=True)))
    sys.path.insert(0, str((_root() / "src").resolve(strict=True)))

    from odoo import api, fields
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
    marker = f"ODACV4-BANK-PAY-MAINT-{args.alias}-{args.run_id.hex}"
    tracked = {
        "account.bank.statement": set(),
        "account.bank.statement.line": set(),
        "account.payment": set(),
        "account.move": set(),
        "account.move.line": set(),
    }
    client: _DirectClient | None = None
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
        if (
            env.uid != _USER_ID
            or env.su
            or not env.user.active
            or env.user.login != _USER_LOGIN
            or _COMPANY_ID not in env.user.company_ids.ids
            or not env.user.has_group("account.group_account_user")
            or not env.user.has_group("account.group_account_invoice")
        ):
            raise RuntimeError(
                "the configured accountant or required groups are unavailable"
            )
        client = _DirectClient(env)
        fixture = _fixture(env, args.alias)
        today = fields.Date.to_string(fields.Date.context_today(env.user))
        tracked = _exercise(
            client,
            args.alias,
            args.run_id,
            fixture,
            today,
            marker,
        )
        if client.capabilities != list(_ALL_CAPABILITIES):
            raise RuntimeError(f"unexpected capability coverage: {client.capabilities}")
    except BaseException as exc:  # noqa: BLE001 - rollback precedes re-raising.
        failure = exc
    finally:
        cursor.rollback()
        cursor.close()

    rollback_failure: BaseException | None = None
    try:
        _verify_rollback(registry, tracked=tracked, marker=marker)
    except BaseException as exc:  # noqa: BLE001 - preserve the business failure.
        rollback_failure = exc
    if failure is not None:
        if rollback_failure is not None:
            failure.add_note(f"rollback verification also failed: {rollback_failure}")
        raise failure
    if rollback_failure is not None:
        raise rollback_failure
    if client is None:
        raise RuntimeError("the maintenance smoke client was not initialized")

    sys.stdout.write(
        json.dumps(
            {
                "alias": args.alias,
                "business_su": False,
                "capabilities": client.capabilities,
                "company_id": _COMPANY_ID,
                "database": args.database,
                "immediate_replays": 3,
                "new_capabilities": list(_NEW_CAPABILITIES),
                "rollback_verified": True,
                "user_id": _USER_ID,
                "verification_reads": ["bank.statement.get", "payment.get"],
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
