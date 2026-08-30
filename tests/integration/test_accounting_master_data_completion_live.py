"""Transactional dual-database smoke for accounting master-data completion."""

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
_ALLOW_ENV = "ODACV4_ALLOW_ACCOUNTING_MASTER_DATA_COMPLETION_WRITE_SMOKE"
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
    "account.tag.create",
    "account.tag.update",
    "account.tag.archive",
    "account.tag.restore",
    "tax.group.create",
    "tax.group.update",
    "cash_rounding.create",
    "cash_rounding.update",
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
    def test_accounting_master_data_completion_rolls_back_per_alias() -> None:
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


class _CoreReadPort:
    def __init__(self, env: Any) -> None:
        self.env = env

    @property
    def user_id(self) -> int:
        return self.env.uid

    def read(
        self,
        *,
        capability_id: str,
        company_id: int,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        from odoo_accounting_cli_v4.bridge.core_object_reads_runtime import dispatch
        from odoo_accounting_cli_v4.bridge.runtime import RuntimeFailure

        return dispatch(
            self.env,
            {
                "capability_id": capability_id,
                "company_id": company_id,
                "parameters": parameters,
            },
            company_id,
            failure_type=RuntimeFailure,
        )


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


def _get(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    from odoo_accounting_cli_v4.capabilities.core_object_reads import read_core_object

    return read_core_object(
        capability_id,
        _CoreReadPort(env),
        _request(alias, run_id, capability_id, parameters),
    )


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
    created: dict[str, int | None],
) -> None:
    company = env["res.company"].browse(_COMPANY_ID)
    fiscal_country = company.account_fiscal_country_id or company.country_id
    if not fiscal_country:
        raise RuntimeError("the isolated company lacks a fiscal country")
    accounts = env["account.account"].search(
        [
            ("company_ids", "in", [_COMPANY_ID]),
            ("active", "=", True),
            (
                "account_type",
                "not in",
                ["asset_receivable", "liability_payable", "off_balance"],
            ),
        ],
        order="id",
        limit=2,
    )
    if len(accounts) != 2:
        raise RuntimeError("the isolated database lacks two cash-rounding accounts")

    tag_name = f"{marker} Tag"
    tag_result = _write(
        env,
        alias,
        run_id,
        "account.tag.create",
        {
            "name": tag_name,
            "applicability": "accounts",
            "color": 7,
            "country_id": None,
        },
    )
    tag_id = tag_result["id"]
    created["tag"] = tag_id
    _assert_result(tag_result, "account.account.tag", tag_id, "active")

    updated_tag_name = f"{marker} Tag Updated"
    _assert_result(
        _write(
            env,
            alias,
            run_id,
            "account.tag.update",
            {
                "account_tag_id": tag_id,
                "changes": {"name": updated_tag_name, "color": 9},
            },
        ),
        "account.account.tag",
        tag_id,
        "active",
    )
    _assert_result(
        _write(
            env,
            alias,
            run_id,
            "account.tag.archive",
            {"account_tag_id": tag_id},
        ),
        "account.account.tag",
        tag_id,
        "archived",
    )
    _assert_result(
        _write(
            env,
            alias,
            run_id,
            "account.tag.restore",
            {"account_tag_id": tag_id},
        ),
        "account.account.tag",
        tag_id,
        "active",
    )
    tag = _get(env, alias, run_id, "account.tag.get", {"tag_id": tag_id})
    if (
        tag["id"] != tag_id
        or tag["name"] != updated_tag_name
        or tag["applicability"] != "accounts"
        or tag["color"] != 9
        or tag["country"] is not None
        or tag["active"] is not True
    ):
        raise RuntimeError(f"account.tag.get returned the wrong tag: {tag}")

    tax_group_name = f"{marker} Tax Group"
    tax_group_result = _write(
        env,
        alias,
        run_id,
        "tax.group.create",
        {
            "name": tax_group_name,
            "sequence": 81,
            "preceding_subtotal": None,
        },
    )
    tax_group_id = tax_group_result["id"]
    created["tax_group"] = tax_group_id
    _assert_result(tax_group_result, "account.tax.group", tax_group_id, "active")

    updated_tax_group_name = f"{marker} Tax Group Updated"
    _assert_result(
        _write(
            env,
            alias,
            run_id,
            "tax.group.update",
            {
                "tax_group_id": tax_group_id,
                "changes": {
                    "name": updated_tax_group_name,
                    "sequence": 82,
                    "preceding_subtotal": f"{marker} Subtotal",
                },
            },
        ),
        "account.tax.group",
        tax_group_id,
        "active",
    )
    tax_group = _get(
        env,
        alias,
        run_id,
        "tax.group.get",
        {"tax_group_id": tax_group_id},
    )
    if (
        tax_group["id"] != tax_group_id
        or tax_group["name"] != updated_tax_group_name
        or tax_group["sequence"] != 82
        or tax_group["company_id"] != _COMPANY_ID
        or tax_group["country"] is None
        or tax_group["country"]["id"] != fiscal_country.id
        or tax_group["preceding_subtotal"] != f"{marker} Subtotal"
    ):
        raise RuntimeError(f"tax.group.get returned the wrong group: {tax_group}")

    rounding_name = f"{marker} Cash Rounding"
    rounding_result = _write(
        env,
        alias,
        run_id,
        "cash_rounding.create",
        {
            "name": rounding_name,
            "rounding": "0.05",
            "strategy": "biggest_tax",
            "rounding_method": "HALF-UP",
            "profit_account_id": None,
            "loss_account_id": None,
        },
    )
    rounding_id = rounding_result["id"]
    created["cash_rounding"] = rounding_id
    _assert_result(rounding_result, "account.cash.rounding", rounding_id, "active")

    _assert_result(
        _write(
            env,
            alias,
            run_id,
            "cash_rounding.update",
            {
                "cash_rounding_id": rounding_id,
                "changes": {
                    "strategy": "add_invoice_line",
                    "profit_account_id": accounts[0].id,
                    "loss_account_id": accounts[1].id,
                },
            },
        ),
        "account.cash.rounding",
        rounding_id,
        "active",
    )
    rounding = _get(
        env,
        alias,
        run_id,
        "cash_rounding.get",
        {"cash_rounding_id": rounding_id},
    )
    if (
        rounding["id"] != rounding_id
        or rounding["name"] != rounding_name
        or rounding["rounding"] != "0.05"
        or rounding["strategy"] != "add_invoice_line"
        or rounding["rounding_method"] != "HALF-UP"
        or rounding["profit_account"] is None
        or rounding["profit_account"]["id"] != accounts[0].id
        or rounding["loss_account"] is None
        or rounding["loss_account"]["id"] != accounts[1].id
    ):
        raise RuntimeError(f"cash_rounding.get returned the wrong record: {rounding}")

    orm_tag = env["account.account.tag"].with_context(active_test=False).browse(tag_id)
    orm_tax_group = env["account.tax.group"].browse(tax_group_id)
    orm_rounding = (
        env["account.cash.rounding"]
        .with_company(env["res.company"].browse(_COMPANY_ID))
        .browse(rounding_id)
    )
    if (
        orm_tag.name != updated_tag_name
        or not orm_tag.active
        or orm_tag.country_id
        or orm_tax_group.name != updated_tax_group_name
        or orm_tax_group.company_id.id != _COMPANY_ID
        or orm_tax_group.country_id != fiscal_country
        or orm_tax_group.sequence != 82
        or orm_rounding.strategy != "add_invoice_line"
        or orm_rounding.profit_account_id != accounts[0]
        or orm_rounding.loss_account_id != accounts[1]
    ):
        raise RuntimeError("accounting master-data state was not preserved")


def _verify_rollback(
    registry: Any,
    *,
    created: dict[str, int | None],
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
        model_by_key = {
            "tag": "account.account.tag",
            "tax_group": "account.tax.group",
            "cash_rounding": "account.cash.rounding",
        }
        remaining = {
            key: env[model].search_count([("id", "=", record_id)], limit=1)
            for key, model in model_by_key.items()
            if (record_id := created[key]) is not None
        }
        remaining["marker"] = sum(
            env[model].search_count([("name", "ilike", marker)], limit=1)
            for model in model_by_key.values()
        )
        if any(remaining.values()):
            raise RuntimeError(f"transaction fixtures survived rollback: {remaining}")
        manager_group_id = env.ref(_MANAGER_GROUP).id
        cursor.execute(
            "SELECT 1 FROM res_groups_users_rel WHERE uid = %s AND gid = %s",
            [_USER_ID, manager_group_id],
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
    marker = f"ODACV4-ACCOUNTING-MASTER-{args.alias}-{args.run_id.hex}"
    created: dict[str, int | None] = {
        "tag": None,
        "tax_group": None,
        "cash_rounding": None,
    }
    failure: Exception | None = None
    try:
        admin_env = api.Environment(
            cursor,
            SUPERUSER_ID,
            {"allowed_company_ids": [_COMPANY_ID], "active_test": False},
        )
        user = admin_env["res.users"].browse(_USER_ID)
        if user.has_group(_MANAGER_GROUP):
            raise RuntimeError("fixed accountant unexpectedly has manager access")
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
        _exercise(env, args.alias, args.run_id, marker, created)
    except Exception as exc:  # noqa: BLE001 - every Odoo failure must roll back.
        failure = exc
    finally:
        cursor.rollback()
        cursor.close()

    _verify_rollback(registry, created=created, marker=marker)
    if failure is not None:
        raise failure
    if any(record_id is None for record_id in created.values()):
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
