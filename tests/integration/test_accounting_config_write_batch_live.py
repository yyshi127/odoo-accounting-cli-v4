"""Transactional dual-database smoke for accounting configuration writes."""

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
_ALLOW_ENV = "ODACV4_ALLOW_ACCOUNTING_CONFIG_WRITE_SMOKE"
_ALIASES = ("v4-dev", "v4-e2e")
_DATABASES = {
    "v4-dev": "odoo_cli_v4_dev",
    "v4-e2e": "odoo_cli_v4_e2e",
}
_COMPANY_ID = 1
_USER_ID = 5
_USER_LOGIN = "odacv4_g5_accountant"
_MANAGER_GROUP = "account.group_account_manager"
_CAPABILITIES = (
    "account.account.create",
    "account.account.update",
    "account.account.archive",
    "account.account.restore",
    "journal.create",
    "journal.update",
    "journal.archive",
    "journal.restore",
    "tax.create",
    "tax.update",
    "tax.archive",
    "tax.restore",
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
    assert isinstance(bridge, dict) and set(bridge) == {"argv", "timeout_seconds"}
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
        "capabilities": list(_CAPABILITIES),
        "company_id": _COMPANY_ID,
        "database": _DATABASES[alias],
        "rollback_verified": True,
        "temporary_group_rolled_back": True,
        "user_id": _USER_ID,
    }


if pytest is not None:

    @pytest.mark.integration
    def test_accounting_config_write_batch_rolls_back_one_chain_per_alias() -> None:
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


class _CoreWritePort:
    def __init__(self, env: Any) -> None:
        self.env = env

    @property
    def user_id(self) -> int:
        return self.env.uid

    def execute(self, **payload: Any) -> dict[str, Any]:
        from odoo_accounting_cli_v4.bridge.core_writes_runtime import dispatch
        from odoo_accounting_cli_v4.bridge.runtime import RuntimeFailure

        return dispatch(self.env, payload, payload["company_id"], RuntimeFailure)


def _write(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    from odoo_accounting_cli_v4.capabilities.core_writes import (
        _expected_idempotency_key,
        execute_core_write,
        validate_core_write_request,
    )

    request = _request(alias, run_id, capability_id, parameters)
    _, context, normalized = validate_core_write_request(capability_id, request)
    key = _expected_idempotency_key(capability_id, normalized, context["company_id"])
    if key is None:
        raise RuntimeError(f"{capability_id} unexpectedly lacks a deterministic key")
    port = _CoreWritePort(env)
    first = execute_core_write(port, capability_id, request, key, capability_id)
    if first["idempotent_replay"] is not False:
        raise RuntimeError(f"{capability_id} replayed its first execution")
    second = execute_core_write(port, capability_id, request, key, capability_id)
    if second["idempotent_replay"] is not True or second["result"] != first["result"]:
        raise RuntimeError(f"{capability_id} did not replay deterministically")
    return first["result"]


def _assert_result(
    result: dict[str, Any], model: str, record_id: int, state: str
) -> None:
    if (
        result["model"] != model
        or result["id"] != record_id
        or result["state"] != state
    ):
        raise RuntimeError(f"unexpected {model} result: {result}")


def _exercise(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    marker: str,
) -> tuple[int, int, int, int]:
    account_code = f"Z{run_id.hex[:12].upper()}"
    account_result = _write(
        env,
        alias,
        run_id,
        "account.account.create",
        {
            "code": account_code,
            "name": f"{marker} Receivable",
            "account_type": "asset_receivable",
            "currency_id": None,
        },
    )
    account_id = account_result["id"]
    _assert_result(account_result, "account.account", account_id, "active")
    _assert_result(
        _write(
            env,
            alias,
            run_id,
            "account.account.update",
            {
                "account_id": account_id,
                "changes": {"name": f"{marker} Receivable Updated"},
            },
        ),
        "account.account",
        account_id,
        "active",
    )
    _assert_result(
        _write(
            env, alias, run_id, "account.account.archive", {"account_id": account_id}
        ),
        "account.account",
        account_id,
        "archived",
    )
    _assert_result(
        _write(
            env, alias, run_id, "account.account.restore", {"account_id": account_id}
        ),
        "account.account",
        account_id,
        "active",
    )

    journal_code = f"V{run_id.hex[:4].upper()}"
    journal_result = _write(
        env,
        alias,
        run_id,
        "journal.create",
        {
            "name": f"{marker} Journal",
            "code": journal_code,
            "type": "bank",
            "sequence": 91,
            "currency_id": None,
        },
    )
    journal_id = journal_result["id"]
    _assert_result(journal_result, "account.journal", journal_id, "active")
    automatic_account_id = (
        env["account.journal"].browse(journal_id).default_account_id.id
    )
    if not automatic_account_id:
        raise RuntimeError("Odoo did not assign the bank journal default account")
    _assert_result(
        _write(
            env,
            alias,
            run_id,
            "journal.update",
            {
                "journal_id": journal_id,
                "changes": {"name": f"{marker} Journal Updated", "sequence": 92},
            },
        ),
        "account.journal",
        journal_id,
        "active",
    )
    _assert_result(
        _write(env, alias, run_id, "journal.archive", {"journal_id": journal_id}),
        "account.journal",
        journal_id,
        "archived",
    )
    _assert_result(
        _write(env, alias, run_id, "journal.restore", {"journal_id": journal_id}),
        "account.journal",
        journal_id,
        "active",
    )

    tax_result = _write(
        env,
        alias,
        run_id,
        "tax.create",
        {
            "name": f"{marker} Tax",
            "type_tax_use": "sale",
            "amount_type": "percent",
            "amount": 6.5,
            "sequence": 97,
            "invoice_label": f"{marker} 6.5%",
            "price_include_override": "tax_excluded",
            "include_base_amount": False,
            "is_base_affected": True,
        },
    )
    tax_id = tax_result["id"]
    _assert_result(tax_result, "account.tax", tax_id, "active")
    _assert_result(
        _write(
            env,
            alias,
            run_id,
            "tax.update",
            {
                "tax_id": tax_id,
                "changes": {"amount": 7.5, "invoice_label": f"{marker} 7.5%"},
            },
        ),
        "account.tax",
        tax_id,
        "active",
    )
    _assert_result(
        _write(env, alias, run_id, "tax.archive", {"tax_id": tax_id}),
        "account.tax",
        tax_id,
        "archived",
    )
    _assert_result(
        _write(env, alias, run_id, "tax.restore", {"tax_id": tax_id}),
        "account.tax",
        tax_id,
        "active",
    )

    account = env["account.account"].with_context(active_test=False).browse(account_id)
    journal = env["account.journal"].with_context(active_test=False).browse(journal_id)
    tax = env["account.tax"].with_context(active_test=False).browse(tax_id)
    if (
        account.code != account_code
        or account.name != f"{marker} Receivable Updated"
        or account.account_type != "asset_receivable"
        or not account.reconcile
        or account.company_ids.ids != [_COMPANY_ID]
        or journal.code != journal_code
        or journal.name != f"{marker} Journal Updated"
        or journal.sequence != 92
        or journal.company_id.id != _COMPANY_ID
        or tax.name != f"{marker} Tax"
        or tax.amount != 7.5
        or tax.invoice_label != f"{marker} 7.5%"
        or tax.company_id.id != _COMPANY_ID
        or not account.active
        or not journal.active
        or not tax.active
    ):
        raise RuntimeError("accounting configuration values were not preserved")
    return account_id, journal_id, tax_id, automatic_account_id


def _verify_rollback(
    registry: Any,
    *,
    record_ids: tuple[int, int, int, int],
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
        models = (
            "account.account",
            "account.journal",
            "account.tax",
            "account.account",
        )
        remaining = {
            f"{model}:{record_id}": env[model].search_count(
                [("id", "=", record_id)], limit=1
            )
            for model, record_id in zip(models, record_ids, strict=True)
        }
        remaining["marker"] = sum(
            env[model].search_count([("name", "ilike", marker)], limit=1)
            for model in models
        )
        if any(remaining.values()):
            raise RuntimeError(f"transaction fixtures survived rollback: {remaining}")
        group_id = env.ref(_MANAGER_GROUP).id
        cursor.execute(
            "SELECT 1 FROM res_groups_users_rel WHERE uid = %s AND gid = %s",
            [_USER_ID, group_id],
        )
        if cursor.fetchone():
            raise RuntimeError("temporary accounting-manager group survived rollback")
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
    marker = f"ODACV4-CONFIG-{args.alias}-{args.run_id.hex}"
    created: tuple[int, int, int, int] | None = None
    failure: Exception | None = None
    try:
        admin_env = api.Environment(
            cursor,
            SUPERUSER_ID,
            {"allowed_company_ids": [_COMPANY_ID], "active_test": False},
        )
        user = admin_env["res.users"].browse(_USER_ID)
        if user.has_group(_MANAGER_GROUP):
            raise RuntimeError(
                "fixed accountant unexpectedly has accounting-manager access"
            )
        for model_name in ("account.account", "account.journal", "account.tax"):
            if admin_env[model_name].with_user(_USER_ID).has_access("create"):
                raise RuntimeError(
                    f"fixed accountant unexpectedly can create {model_name}"
                )
        user.write({"group_ids": [Command.link(admin_env.ref(_MANAGER_GROUP).id)]})
        admin_env.flush_all()

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
            or env.user.login != _USER_LOGIN
            or not env.user.active
            or _COMPANY_ID not in env.user.company_ids.ids
            or not env.user.has_group(_MANAGER_GROUP)
        ):
            raise RuntimeError("the fixed accountant or temporary group is unavailable")
        created = _exercise(env, args.alias, args.run_id, marker)
    except Exception as exc:  # noqa: BLE001 - rollback must cover every Odoo failure.
        failure = exc
    finally:
        cursor.rollback()
        cursor.close()

    if created is not None:
        _verify_rollback(registry, record_ids=created, marker=marker)
    if failure is not None:
        raise failure
    if created is None:
        raise RuntimeError("the live fixtures were not initialized")
    sys.stdout.write(
        json.dumps(
            {
                "alias": args.alias,
                "capabilities": list(_CAPABILITIES),
                "company_id": _COMPANY_ID,
                "database": args.database,
                "rollback_verified": True,
                "temporary_group_rolled_back": True,
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
