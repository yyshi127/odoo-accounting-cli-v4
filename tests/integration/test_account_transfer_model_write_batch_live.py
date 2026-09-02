"""Rollback-only dual-database smoke for transfer-model lifecycle writes.

The fixed accountant receives ``account.group_account_manager`` only inside the
outer transaction.  Every public capability still runs as uid 5 with ``su=False``;
the grant and all transfer-model writes are rolled back and checked from a fresh
cursor.
"""

from __future__ import annotations

import argparse
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
_ALLOW_ENV = "ODACV4_ALLOW_TRANSFER_MODEL_WRITE_SMOKE"
_ALIASES = ("v4-dev", "v4-e2e")
_DATABASES = {
    "v4-dev": "odoo_cli_v4_dev",
    "v4-e2e": "odoo_cli_v4_e2e",
}
_COMPANY_ID = 1
_USER_ID = 5
_USER_LOGIN = "odacv4_g5_accountant"
_MANAGER_GROUP = "account.group_account_manager"
_WRITE_CAPABILITIES = (
    "account.transfer_model.create",
    "account.transfer_model.update",
    "account.transfer_model.duplicate",
    "account.transfer_model.enable",
    "account.transfer_model.disable",
    "account.transfer_model.archive",
    "account.transfer_model.restore",
    "account.transfer_model.delete",
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
    assert {alias: aliases[alias].get("database") for alias in _ALIASES} == (
        _DATABASES
    )
    assert all(
        aliases[alias].get("companies", {}).get(str(_COMPANY_ID))
        == [_USER_LOGIN]
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
        "capabilities": list(_WRITE_CAPABILITIES),
        "company_id": _COMPANY_ID,
        "database": _DATABASES[alias],
        "default_manager_authorized": False,
        "immediate_replays": 7,
        "rollback_verified": True,
        "temporary_group_fixture": _MANAGER_GROUP,
        "temporary_group_rolled_back": True,
        "user_id": _USER_ID,
        "verification_read": "account.transfer_model.get",
    }


if pytest is not None:

    @pytest.mark.integration
    def test_transfer_model_write_batch_rolls_back_one_chain_per_alias() -> None:
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

    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        if self.env.uid != _USER_ID or self.env.su:
            raise RuntimeError("a public capability escaped uid 5 with su=False")
        from odoo_accounting_cli_v4.bridge.runtime import _dispatch

        return _dispatch(self.env, action, payload, _COMPANY_ID)


def _write(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    parameters: dict[str, Any],
    *,
    replayable: bool = True,
) -> dict[str, Any]:
    from odoo_accounting_cli_v4.bridge.core_writes import OdooCoreWritePort
    from odoo_accounting_cli_v4.capabilities.core_writes import (
        _expected_idempotency_key,
        execute_core_write,
        validate_core_write_request,
    )

    request = _request(alias, run_id, capability_id, parameters)
    _, context, normalized = validate_core_write_request(capability_id, request)
    key = _expected_idempotency_key(capability_id, normalized, context["company_id"])
    if key is None:
        raise RuntimeError(f"{capability_id} lacks the frozen deterministic key")
    port = OdooCoreWritePort(_DirectClient(env))
    first = execute_core_write(port, capability_id, request, key, capability_id)
    if port.user_id != _USER_ID or first["idempotent_replay"] is not False:
        raise RuntimeError(f"{capability_id} replayed its first execution")
    if replayable:
        replay = execute_core_write(port, capability_id, request, key, capability_id)
        if (
            port.user_id != _USER_ID
            or replay["idempotent_replay"] is not True
            or replay["result"] != first["result"]
        ):
            raise RuntimeError(f"{capability_id} did not replay deterministically")
    return first["result"]


def _get(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    transfer_model_id: int,
) -> dict[str, Any]:
    from odoo_accounting_cli_v4.bridge.core_object_reads import (
        OdooCoreObjectReadPort,
    )
    from odoo_accounting_cli_v4.capabilities.core_object_reads import (
        read_core_object,
    )

    port = OdooCoreObjectReadPort(_DirectClient(env))
    result = read_core_object(
        "account.transfer_model.get",
        port,
        _request(
            alias,
            run_id,
            "account.transfer_model.get",
            {"transfer_model_id": transfer_model_id},
        ),
    )
    if port.user_id != _USER_ID:
        raise RuntimeError("transfer-model verification escaped the fixed accountant")
    return result


def _assert_result(
    result: dict[str, Any],
    *,
    state: str,
    transfer_model_id: int | None = None,
    source_id: int | None = None,
) -> int:
    if (
        result["model"] != "account.transfer.model"
        or not isinstance(result["id"], int)
        or isinstance(result["id"], bool)
        or result["id"] <= 0
        or (transfer_model_id is not None and result["id"] != transfer_model_id)
        or result["state"] != state
        or result["company_id"] != _COMPANY_ID
        or result["move_type"] is not None
        or result["source_id"] != source_id
        or result["partial_reconcile_ids"]
        or result["full_reconcile_id"] is not None
        or result["reconciled"]
    ):
        raise RuntimeError(f"invalid transfer-model write result: {result}")
    return result["id"]


def _assert_read(
    item: dict[str, Any],
    *,
    transfer_model_id: int,
    name: str,
    state: str,
    active: bool,
    journal_id: int,
    origin_account_ids: list[int],
    destination_account_ids: list[int],
    percentages: list[str],
    frequency: str,
) -> None:
    if (
        item["id"] != transfer_model_id
        or item["name"] != name
        or item["state"] != state
        or item["active"] is not active
        or item["company_id"] != _COMPANY_ID
        or item["journal"]["id"] != journal_id
        or item["frequency"] != frequency
        or [entry["id"] for entry in item["origin_accounts"]]
        != origin_account_ids
        or [line["account"]["id"] for line in item["destination_lines"]]
        != destination_account_ids
        or [line["percentage"] for line in item["destination_lines"]]
        != percentages
        or item["move_ids_count"] != 0
    ):
        raise RuntimeError(f"transfer-model readback mismatch: {item}")


def _fixture(admin_env: Any) -> dict[str, Any]:
    journal = admin_env["account.journal"].search(
        [
            ("company_id", "=", _COMPANY_ID),
            ("type", "=", "general"),
            ("active", "=", True),
        ],
        order="id",
        limit=1,
    )
    accounts = admin_env["account.account"].search(
        [
            ("company_ids", "in", [_COMPANY_ID]),
            ("account_type", "!=", "off_balance"),
            ("active", "=", True),
        ],
        order="id",
        limit=4,
    )
    if not journal or len(accounts) < 4:
        raise RuntimeError("general journal or four usable accounts are unavailable")
    return {"journal_id": journal.id, "account_ids": accounts.ids}


def _exercise(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    marker: str,
    fixture: dict[str, Any],
) -> set[int]:
    journal_id = fixture["journal_id"]
    origin_a, destination_a, origin_b, destination_b = fixture["account_ids"]
    original_name = f"{marker} Original"
    updated_name = f"{marker} Updated"
    duplicate_name = f"{marker} Copy"
    created = _write(
        env,
        alias,
        run_id,
        "account.transfer_model.create",
        {
            "name": original_name,
            "journal_id": journal_id,
            "date_start": "2026-01-01",
            "date_stop": None,
            "frequency": "month",
            "origin_account_ids": [origin_a],
            "destination_lines": [
                {"account_id": destination_a, "percentage": "100"}
            ],
        },
    )
    original_id = _assert_result(created, state="disabled")
    if not created["line_ids"]:
        raise RuntimeError("transfer-model create returned no destination line")
    _assert_read(
        _get(env, alias, run_id, original_id),
        transfer_model_id=original_id,
        name=original_name,
        state="disabled",
        active=True,
        journal_id=journal_id,
        origin_account_ids=[origin_a],
        destination_account_ids=[destination_a],
        percentages=["100"],
        frequency="month",
    )

    updated = _write(
        env,
        alias,
        run_id,
        "account.transfer_model.update",
        {
            "transfer_model_id": original_id,
            "changes": {
                "name": updated_name,
                "frequency": "quarter",
                "origin_account_ids": [origin_b],
                "destination_lines": [
                    {"account_id": destination_b, "percentage": "100"}
                ],
            },
        },
    )
    _assert_result(updated, state="disabled", transfer_model_id=original_id)
    _assert_read(
        _get(env, alias, run_id, original_id),
        transfer_model_id=original_id,
        name=updated_name,
        state="disabled",
        active=True,
        journal_id=journal_id,
        origin_account_ids=[origin_b],
        destination_account_ids=[destination_b],
        percentages=["100"],
        frequency="quarter",
    )

    duplicated = _write(
        env,
        alias,
        run_id,
        "account.transfer_model.duplicate",
        {"transfer_model_id": original_id, "name": duplicate_name},
    )
    duplicate_id = _assert_result(
        duplicated, state="disabled", source_id=original_id
    )
    if duplicate_id == original_id or not duplicated["line_ids"]:
        raise RuntimeError("transfer-model duplicate did not create a distinct copy")
    _assert_read(
        _get(env, alias, run_id, duplicate_id),
        transfer_model_id=duplicate_id,
        name=duplicate_name,
        state="disabled",
        active=True,
        journal_id=journal_id,
        origin_account_ids=[origin_b],
        destination_account_ids=[destination_b],
        percentages=["100"],
        frequency="quarter",
    )
    deleted = _write(
        env,
        alias,
        run_id,
        "account.transfer_model.delete",
        {"transfer_model_id": duplicate_id},
        replayable=False,
    )
    _assert_result(deleted, state="deleted", transfer_model_id=duplicate_id)
    if env["account.transfer.model"].with_context(active_test=False).browse(
        duplicate_id
    ).exists():
        raise RuntimeError("transfer-model delete left the duplicate present")

    _assert_result(
        _write(
            env,
            alias,
            run_id,
            "account.transfer_model.enable",
            {"transfer_model_id": original_id},
        ),
        state="in_progress",
        transfer_model_id=original_id,
    )
    _assert_result(
        _write(
            env,
            alias,
            run_id,
            "account.transfer_model.disable",
            {"transfer_model_id": original_id},
        ),
        state="disabled",
        transfer_model_id=original_id,
    )
    _assert_result(
        _write(
            env,
            alias,
            run_id,
            "account.transfer_model.archive",
            {"transfer_model_id": original_id},
        ),
        state="archived",
        transfer_model_id=original_id,
    )
    _assert_read(
        _get(env, alias, run_id, original_id),
        transfer_model_id=original_id,
        name=updated_name,
        state="disabled",
        active=False,
        journal_id=journal_id,
        origin_account_ids=[origin_b],
        destination_account_ids=[destination_b],
        percentages=["100"],
        frequency="quarter",
    )
    _assert_result(
        _write(
            env,
            alias,
            run_id,
            "account.transfer_model.restore",
            {"transfer_model_id": original_id},
        ),
        state="disabled",
        transfer_model_id=original_id,
    )
    _assert_read(
        _get(env, alias, run_id, original_id),
        transfer_model_id=original_id,
        name=updated_name,
        state="disabled",
        active=True,
        journal_id=journal_id,
        origin_account_ids=[origin_b],
        destination_account_ids=[destination_b],
        percentages=["100"],
        frequency="quarter",
    )
    return {original_id, duplicate_id}


def _direct_group_membership(cursor: Any, group_id: int) -> bool:
    cursor.execute(
        "SELECT 1 FROM res_groups_users_rel WHERE uid = %s AND gid = %s",
        [_USER_ID, group_id],
    )
    return cursor.fetchone() is not None


def _verify_rollback(
    registry: Any,
    *,
    transfer_model_ids: set[int],
    manager_group_id: int,
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
            "models_by_id": env["account.transfer.model"].search_count(
                [("id", "in", sorted(transfer_model_ids))]
            ),
            "models_by_marker": env["account.transfer.model"].search_count(
                [("name", "ilike", marker)]
            ),
            "lines": env["account.transfer.model.line"].search_count(
                [("transfer_model_id", "in", sorted(transfer_model_ids))]
            ),
            "moves": env["account.move"].search_count(
                [("transfer_model_id", "in", sorted(transfer_model_ids))]
            ),
        }
        if any(survivors.values()):
            raise RuntimeError(f"transfer-model fixtures survived rollback: {survivors}")
        if _direct_group_membership(cursor, manager_group_id):
            raise RuntimeError("temporary accounting-manager grant survived rollback")
    finally:
        cursor.rollback()
        cursor.close()


def _live_worker(argv: list[str] | None = None) -> int:
    args = _arguments(argv)
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
    marker = f"ODACV4-TRANSFER-{args.alias}-{args.run_id.hex}"
    transfer_model_ids: set[int] = set()
    manager_group_id: int | None = None
    failure: BaseException | None = None
    try:
        context = {
            "allowed_company_ids": [_COMPANY_ID],
            "active_test": False,
            "lang": "en_US",
            "tz": "Asia/Shanghai",
        }
        admin_env = api.Environment(cursor, SUPERUSER_ID, context)
        company = admin_env["res.company"].browse(_COMPANY_ID).exists()
        user = admin_env["res.users"].with_context(active_test=False).browse(_USER_ID)
        manager_group_id = admin_env.ref(_MANAGER_GROUP).id
        if (
            not company
            or not user.exists()
            or user.login != _USER_LOGIN
            or not user.active
            or company not in user.company_ids
        ):
            raise RuntimeError("the configured company or accountant is unavailable")
        if user.has_group(_MANAGER_GROUP) or _direct_group_membership(
            cursor, manager_group_id
        ):
            raise RuntimeError("uid 5 already has the temporary accounting-manager grant")

        fixture = _fixture(admin_env)
        user.write({"group_ids": [Command.link(manager_group_id)]})
        admin_env.flush_all()
        if not _direct_group_membership(cursor, manager_group_id):
            raise RuntimeError("temporary accounting-manager grant was not persisted")

        business_env = api.Environment(
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
            business_env.uid != _USER_ID
            or business_env.su
            or business_env.user.login != _USER_LOGIN
            or not business_env.user.has_group(_MANAGER_GROUP)
        ):
            raise RuntimeError("uid 5 or its temporary manager grant is unavailable")
        transfer_model_ids = _exercise(
            business_env, args.alias, args.run_id, marker, fixture
        )
    except BaseException as exc:  # noqa: BLE001 - rollback precedes re-raising.
        failure = exc
    finally:
        cursor.rollback()
        cursor.close()

    rollback_failure: BaseException | None = None
    if manager_group_id is not None:
        try:
            _verify_rollback(
                registry,
                transfer_model_ids=transfer_model_ids,
                manager_group_id=manager_group_id,
                marker=marker,
            )
        except BaseException as exc:  # noqa: BLE001 - preserve first failure.
            rollback_failure = exc
    if failure is not None:
        if rollback_failure is not None:
            failure.add_note(f"rollback verification also failed: {rollback_failure}")
        raise failure
    if rollback_failure is not None:
        raise rollback_failure
    if manager_group_id is None or len(transfer_model_ids) != 2:
        raise RuntimeError("the transfer-model rollback fixture was not initialized")

    sys.stdout.write(
        json.dumps(
            {
                "alias": args.alias,
                "business_su": False,
                "capabilities": list(_WRITE_CAPABILITIES),
                "company_id": _COMPANY_ID,
                "database": args.database,
                "default_manager_authorized": False,
                "immediate_replays": 7,
                "rollback_verified": True,
                "temporary_group_fixture": _MANAGER_GROUP,
                "temporary_group_rolled_back": True,
                "user_id": _USER_ID,
                "verification_read": "account.transfer_model.get",
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
