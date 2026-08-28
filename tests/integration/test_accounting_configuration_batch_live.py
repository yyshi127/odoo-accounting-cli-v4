"""Rollback-only dual-database smoke for configuration writes and readiness reads."""

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
_ALLOW_ENV = "ODACV4_ALLOW_ACCOUNTING_CONFIGURATION_BATCH_LIVE"
_ALIASES = ("v4-dev", "v4-e2e")
_DATABASES = {"v4-dev": "odoo_cli_v4_dev", "v4-e2e": "odoo_cli_v4_e2e"}
_USER_LOGIN = "odacv4_g5_accountant"
_MANAGER_GROUP = "account.group_account_manager"
_WRITES = (
    "fiscal_position.create",
    "fiscal_position.update",
    "fiscal_position.account_mappings.replace",
    "fiscal_position.archive",
    "fiscal_position.restore",
    "journal.group.create",
    "journal.group.update",
)
_READS = (
    "localization.china.configuration.inspect",
    "localization.singapore.configuration.inspect",
)


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _enabled_runtime() -> tuple[Path, dict[str, Any]]:
    assert pytest is not None
    if os.environ.get(_ALLOW_ENV) != "1":
        pytest.skip(f"set {_ALLOW_ENV}=1 to authorize isolated rollback smoke")
    raw = os.environ.get(_CONFIG_ENV)
    if not raw:
        pytest.skip(f"{_CONFIG_ENV} is not configured")
    path = Path(raw)
    if not path.is_file():
        pytest.skip(f"{_CONFIG_ENV} does not name an existing file")
    runtime = json.loads(path.read_text(encoding="utf-8"))
    aliases = runtime.get("aliases")
    assert isinstance(aliases, dict) and set(aliases) == set(_ALIASES)
    assert {key: aliases[key].get("database") for key in _ALIASES} == _DATABASES
    return path, runtime


def _worker_command(
    alias: str, run_id: uuid.UUID, config: Path, runtime: dict[str, Any]
) -> tuple[list[str], int]:
    bridge = runtime.get("bridge")
    assert isinstance(bridge, dict) and set(bridge) == {"argv", "timeout_seconds"}
    argv = bridge["argv"]
    assert isinstance(argv, list) and len(argv) == 8
    assert argv[2::2] == ["--runtime-config", "--odoo-config", "--odoo-source"]
    assert Path(argv[3]).resolve(strict=True) == config.resolve(strict=True)
    executable, odoo_config, odoo_source = Path(argv[0]), Path(argv[5]), Path(argv[7])
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


if pytest is not None:

    @pytest.mark.integration
    def test_accounting_configuration_batch_rolls_back_each_alias() -> None:
        config, runtime = _enabled_runtime()
        run_id = uuid.uuid4()
        for alias in _ALIASES:
            command, timeout = _worker_command(alias, run_id, config, runtime)
            environment = os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            environment["PYTHONPATH"] = os.pathsep.join(
                value
                for value in (str(_root() / "src"), environment.get("PYTHONPATH"))
                if value
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
            assert json.loads(completed.stdout) == {
                "alias": alias,
                "database": _DATABASES[alias],
                "reads": list(_READS),
                "rollback_verified": True,
                "temporary_group_rolled_back": True,
                "writes": list(_WRITES),
            }


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
        parser.error("alias and database do not match")
    if not args.odoo_config.is_absolute() or not args.odoo_config.is_file():
        parser.error("odoo-config must be an existing absolute file")
    if not args.odoo_source.is_absolute() or not args.odoo_source.is_dir():
        parser.error("odoo-source must be an existing absolute directory")
    return args


def _request(
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    company_id: int,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    identity = json.dumps(
        [capability_id, company_id, parameters], sort_keys=True, separators=(",", ":")
    )
    return {
        "schema_version": "v1",
        "request_id": str(uuid.uuid5(run_id, identity)),
        "context": {
            "database": alias,
            "company_id": company_id,
            "user_login": _USER_LOGIN,
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": parameters,
    }


class _WritePort:
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

    request = _request(alias, run_id, capability_id, 1, parameters)
    _, context, normalized = validate_core_write_request(capability_id, request)
    key = _expected_idempotency_key(capability_id, normalized, context["company_id"])
    if key is None:
        raise RuntimeError(f"{capability_id} lacks its deterministic key")
    port = _WritePort(env)
    first = execute_core_write(port, capability_id, request, key, capability_id)
    replay = execute_core_write(port, capability_id, request, key, capability_id)
    if (
        first["idempotent_replay"]
        or not replay["idempotent_replay"]
        or replay["result"] != first["result"]
    ):
        raise RuntimeError(f"{capability_id} did not replay deterministically")
    return first["result"]


class _ReadPort:
    def __init__(self, env: Any) -> None:
        self.env = env
        self._user_id: int | None = None

    @property
    def user_id(self) -> int:
        if self._user_id is None:
            raise ValueError("no readiness page was read")
        return self._user_id

    def read(
        self, *, capability_id: str, company_id: int, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        from odoo_accounting_cli_v4.bridge.localization_configuration_runtime import (
            dispatch,
        )
        from odoo_accounting_cli_v4.bridge.runtime import RuntimeFailure

        page = dispatch(
            self.env,
            {
                "capability_id": capability_id,
                "company_id": company_id,
                "parameters": parameters,
            },
            company_id,
            failure_type=RuntimeFailure,
        )
        self._user_id = page["user_id"]
        return page


def _readiness(
    env: Any, alias: str, run_id: uuid.UUID, capability_id: str, company_id: int
) -> None:
    from odoo_accounting_cli_v4.capabilities.localization_configuration import (
        read_localization_configuration,
    )

    result = read_localization_configuration(
        capability_id,
        _ReadPort(env),
        _request(alias, run_id, capability_id, company_id, {}),
    )
    if result["company_id"] != company_id or not isinstance(result["configured"], bool):
        raise RuntimeError(f"{capability_id} returned inconsistent readiness")


def _exercise(env: Any, alias: str, run_id: uuid.UUID, marker: str) -> tuple[int, int]:
    accounts = env["account.account"].search(
        [("company_ids", "in", [1])], order="id"
    ).filtered(lambda account: set(account.company_ids.ids) == {1})[:2]
    journals = env["account.journal"].search(
        [("company_id", "=", 1)], order="id", limit=2
    )
    if len(accounts) != 2 or not journals:
        raise RuntimeError("company 1 lacks configuration prerequisites")
    fiscal = _write(env, alias, run_id, "fiscal_position.create", {"name": marker})
    fiscal_id = fiscal["id"]
    _write(
        env,
        alias,
        run_id,
        "fiscal_position.update",
        {"fiscal_position_id": fiscal_id, "changes": {"note": marker, "sequence": 91}},
    )
    mapping = _write(
        env,
        alias,
        run_id,
        "fiscal_position.account_mappings.replace",
        {
            "fiscal_position_id": fiscal_id,
            "mappings": [
                {
                    "source_account_id": accounts[0].id,
                    "destination_account_id": accounts[1].id,
                }
            ],
        },
    )
    if len(mapping["line_ids"]) != 1:
        raise RuntimeError("fiscal-position mapping was not replaced")
    archived = _write(
        env, alias, run_id, "fiscal_position.archive", {"fiscal_position_id": fiscal_id}
    )
    restored = _write(
        env, alias, run_id, "fiscal_position.restore", {"fiscal_position_id": fiscal_id}
    )
    if archived["state"] != "archived" or restored["state"] != "active":
        raise RuntimeError("fiscal-position lifecycle returned wrong states")
    group = _write(
        env,
        alias,
        run_id,
        "journal.group.create",
        {"name": marker, "excluded_journal_ids": journals.ids},
    )
    group_id = group["id"]
    updated = _write(
        env,
        alias,
        run_id,
        "journal.group.update",
        {
            "journal_group_id": group_id,
            "changes": {"name": f"{marker}-UPDATED", "sequence": 92},
        },
    )
    if (
        fiscal["model"] != "account.fiscal.position"
        or updated["model"] != "account.journal.group"
    ):
        raise RuntimeError("configuration writes returned wrong models")
    _readiness(env, alias, run_id, _READS[0], 1)
    _readiness(env, alias, run_id, _READS[1], 2)
    return fiscal_id, group_id


def _verify_rollback(
    registry: Any, user_id: int, marker: str, ids: tuple[int, int]
) -> None:
    from odoo import SUPERUSER_ID, api

    cursor = registry.cursor()
    try:
        env = api.Environment(
            cursor, SUPERUSER_ID, {"allowed_company_ids": [1, 2], "active_test": False}
        )
        remaining = env["account.fiscal.position"].search_count(
            [("id", "=", ids[0])], limit=1
        ) + env["account.journal.group"].search_count([("id", "=", ids[1])], limit=1)
        remaining += env["account.fiscal.position"].search_count(
            [("name", "ilike", marker)], limit=1
        ) + env["account.journal.group"].search_count(
            [("name", "ilike", marker)], limit=1
        )
        if remaining:
            raise RuntimeError("configuration marker data survived rollback")
        group_id = env.ref(_MANAGER_GROUP).id
        cursor.execute(
            "SELECT 1 FROM res_groups_users_rel WHERE uid = %s AND gid = %s",
            [user_id, group_id],
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
    from odoo.tools import config

    config.parse_config(
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
    marker = f"ODACV4-CONFIG-BATCH-{args.alias}-{args.run_id.hex}"
    ids: tuple[int, int] | None = None
    user_id: int | None = None
    failure: Exception | None = None
    try:
        admin = api.Environment(
            cursor, SUPERUSER_ID, {"allowed_company_ids": [1, 2], "active_test": False}
        )
        user = admin["res.users"].search([("login", "=", _USER_LOGIN)], limit=1)
        if (
            not user
            or user.has_group(_MANAGER_GROUP)
            or set(user.company_ids.ids) < {1, 2}
        ):
            raise RuntimeError("fixed business user baseline is unavailable")
        user_id = user.id
        user.write({"group_ids": [Command.link(admin.ref(_MANAGER_GROUP).id)]})
        admin.flush_all()
        env = api.Environment(
            cursor,
            user_id,
            {
                "allowed_company_ids": [1, 2],
                "active_test": True,
                "lang": "en_US",
                "tz": "Asia/Shanghai",
            },
        )
        ids = _exercise(env, args.alias, args.run_id, marker)
    except Exception as exc:  # noqa: BLE001 - rollback must precede reporting.
        failure = exc
    finally:
        cursor.rollback()
        cursor.close()
    if ids is not None and user_id is not None:
        _verify_rollback(registry, user_id, marker, ids)
    if failure is not None:
        raise failure
    if ids is None or user_id is None:
        raise RuntimeError("live fixtures were not initialized")
    sys.stdout.write(
        json.dumps(
            {
                "alias": args.alias,
                "database": args.database,
                "reads": list(_READS),
                "rollback_verified": True,
                "temporary_group_rolled_back": True,
                "writes": list(_WRITES),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_live_worker())
