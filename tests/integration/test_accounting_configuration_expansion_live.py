"""Transactional dual-database smoke for the accounting configuration expansion."""

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
_ALLOW_ENV = "ODACV4_ALLOW_ACCOUNTING_CONFIGURATION_EXPANSION_WRITE_SMOKE"
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
    "currency.rate.record",
    "account.group.get",
    "account.group.create",
    "account.group.update",
    "tax.repartition_lines.replace",
    "reconciliation.model.create",
    "reconciliation.model.update",
    "reconciliation.model.lines.replace",
    "reconciliation.model.archive",
    "reconciliation.model.restore",
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
    def test_accounting_configuration_expansion_rolls_back_per_alias() -> None:
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


def _get_account_group(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    account_group_id: int,
) -> dict[str, Any]:
    from odoo_accounting_cli_v4.capabilities.core_object_reads import read_core_object

    return read_core_object(
        "account.group.get",
        _CoreReadPort(env),
        _request(
            alias,
            run_id,
            "account.group.get",
            {"account_group_id": account_group_id},
        ),
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
) -> tuple[int, int, int, int, tuple[int, ...]]:
    company = env["res.company"].browse(_COMPANY_ID)
    currency = env["res.currency"].search(
        [("active", "=", True), ("id", "!=", company.currency_id.id)], limit=1
    )
    account = env["account.account"].search(
        [
            ("company_ids", "in", [_COMPANY_ID]),
            ("active", "=", True),
            ("account_type", "!=", "off_balance"),
        ],
        limit=1,
    )
    if not currency or not account:
        raise RuntimeError("the isolated database lacks a currency or account fixture")

    year = 2070 + int(run_id.hex[:2], 16) % 25
    month = 1 + int(run_id.hex[2:4], 16) % 12
    day = 1 + int(run_id.hex[4:6], 16) % 28
    rate_date = f"{year:04d}-{month:02d}-{day:02d}"
    rate_result = _write(
        env,
        alias,
        run_id,
        "currency.rate.record",
        {
            "currency_id": currency.id,
            "date": rate_date,
            "company_units_per_foreign_unit": "7.125",
        },
    )
    rate_id = rate_result["id"]
    _assert_result(rate_result, "res.currency.rate", rate_id, "active")

    prefix = f"Z{run_id.hex[:11].upper()}"
    group_result = _write(
        env,
        alias,
        run_id,
        "account.group.create",
        {
            "name": f"{marker} Account Group",
            "code_prefix_start": prefix,
            "code_prefix_end": prefix,
        },
    )
    group_id = group_result["id"]
    _assert_result(group_result, "account.group", group_id, "active")
    updated_group_name = f"{marker} Account Group Updated"
    _assert_result(
        _write(
            env,
            alias,
            run_id,
            "account.group.update",
            {"account_group_id": group_id, "changes": {"name": updated_group_name}},
        ),
        "account.group",
        group_id,
        "active",
    )
    group = _get_account_group(env, alias, run_id, group_id)
    if (
        group["id"] != group_id
        or group["name"] != updated_group_name
        or group["code_prefix_start"] != prefix
        or group["code_prefix_end"] != prefix
    ):
        raise RuntimeError(f"account.group.get returned the wrong group: {group}")

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
    base_line = {
        "sequence": 71,
        "repartition_type": "base",
        "factor_percent": "100",
        "account_id": None,
        "tag_ids": [],
        "use_in_tax_closing": False,
    }
    tax_line = {
        "sequence": 72,
        "repartition_type": "tax",
        "factor_percent": "100",
        "account_id": account.id,
        "tag_ids": [],
        "use_in_tax_closing": False,
    }
    repartition_result = _write(
        env,
        alias,
        run_id,
        "tax.repartition_lines.replace",
        {
            "tax_id": tax_id,
            "invoice_lines": [base_line, tax_line],
            "refund_lines": [base_line, tax_line],
        },
    )
    _assert_result(repartition_result, "account.tax", tax_id, "active")
    if len(repartition_result["line_ids"]) != 4:
        raise RuntimeError("tax repartition replacement did not create four lines")

    model_result = _write(
        env,
        alias,
        run_id,
        "reconciliation.model.create",
        {
            "name": f"{marker} Reconciliation Model",
            "sequence": 97,
            "trigger": "manual",
            "match_journal_ids": [],
            "match_partner_ids": [],
            "match_amount": None,
            "match_label": None,
        },
    )
    model_id = model_result["id"]
    _assert_result(model_result, "account.reconcile.model", model_id, "active")
    model_name = f"{marker} Reconciliation Model Updated"
    _assert_result(
        _write(
            env,
            alias,
            run_id,
            "reconciliation.model.update",
            {
                "reconciliation_model_id": model_id,
                "changes": {"name": model_name, "sequence": 98},
            },
        ),
        "account.reconcile.model",
        model_id,
        "active",
    )
    lines_result = _write(
        env,
        alias,
        run_id,
        "reconciliation.model.lines.replace",
        {
            "reconciliation_model_id": model_id,
            "lines": [
                {
                    "sequence": 1,
                    "account_id": account.id,
                    "partner_id": None,
                    "label": f"{marker} Bank Fee",
                    "amount_type": "fixed",
                    "amount_string": "10",
                    "tax_ids": [],
                }
            ],
        },
    )
    _assert_result(lines_result, "account.reconcile.model", model_id, "active")
    if len(lines_result["line_ids"]) != 1:
        raise RuntimeError("reconciliation model line replacement failed")
    _assert_result(
        _write(
            env,
            alias,
            run_id,
            "reconciliation.model.archive",
            {"reconciliation_model_id": model_id},
        ),
        "account.reconcile.model",
        model_id,
        "archived",
    )
    _assert_result(
        _write(
            env,
            alias,
            run_id,
            "reconciliation.model.restore",
            {"reconciliation_model_id": model_id},
        ),
        "account.reconcile.model",
        model_id,
        "active",
    )

    rate = env["res.currency.rate"].browse(rate_id)
    account_group = env["account.group"].browse(group_id)
    tax = env["account.tax"].browse(tax_id)
    model = env["account.reconcile.model"].browse(model_id)
    if (
        str(rate.name) != rate_date
        or rate.currency_id != currency
        or account_group.name != updated_group_name
        or tax.name != f"{marker} Tax"
        or len(tax.invoice_repartition_line_ids) != 2
        or len(tax.refund_repartition_line_ids) != 2
        or model.name != model_name
        or model.sequence != 98
        or not model.active
        or len(model.line_ids) != 1
        or model.line_ids.account_id != account
    ):
        raise RuntimeError("accounting configuration state was not preserved")
    return rate_id, group_id, tax_id, model_id, tuple(model.line_ids.ids)


def _verify_rollback(
    registry: Any,
    *,
    record_ids: tuple[int, int, int, int, tuple[int, ...]],
    marker: str,
) -> None:
    from odoo import SUPERUSER_ID, api

    rate_id, group_id, tax_id, model_id, line_ids = record_ids
    cursor = registry.cursor()
    try:
        env = api.Environment(
            cursor,
            SUPERUSER_ID,
            {"allowed_company_ids": [_COMPANY_ID], "active_test": False},
        )
        remaining = {
            "rate": env["res.currency.rate"].search_count(
                [("id", "=", rate_id)], limit=1
            ),
            "group": env["account.group"].search_count(
                [("id", "=", group_id)], limit=1
            ),
            "tax": env["account.tax"].search_count([("id", "=", tax_id)], limit=1),
            "model": env["account.reconcile.model"].search_count(
                [("id", "=", model_id)], limit=1
            ),
            "lines": env["account.reconcile.model.line"].search_count(
                [("id", "in", list(line_ids))]
            ),
            "marker": sum(
                env[model].search_count([("name", "ilike", marker)], limit=1)
                for model in ("account.group", "account.tax", "account.reconcile.model")
            ),
        }
        if any(remaining.values()):
            raise RuntimeError(f"transaction fixtures survived rollback: {remaining}")
        group_xml_id = env.ref(_MANAGER_GROUP).id
        cursor.execute(
            "SELECT 1 FROM res_groups_users_rel WHERE uid = %s AND gid = %s",
            [_USER_ID, group_xml_id],
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
    marker = f"ODACV4-ACCOUNTING-CONFIG-{args.alias}-{args.run_id.hex}"
    created: tuple[int, int, int, int, tuple[int, ...]] | None = None
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
        created = _exercise(env, args.alias, args.run_id, marker)
    except Exception as exc:  # noqa: BLE001 - every Odoo failure must roll back.
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
