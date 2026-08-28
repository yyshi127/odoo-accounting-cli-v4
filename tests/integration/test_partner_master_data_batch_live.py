"""Transactional dual-database smoke for partner master-data capabilities."""

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
_ALLOW_ENV = "ODACV4_ALLOW_PARTNER_MASTER_DATA_SMOKE"
_ALIASES = ("v4-dev", "v4-e2e")
_DATABASES = {
    "v4-dev": "odoo_cli_v4_dev",
    "v4-e2e": "odoo_cli_v4_e2e",
}
_COMPANY_ID = 1
_USER_ID = 5
_USER_LOGIN = "odacv4_g5_accountant"
_PARTNER_MANAGER_GROUP = "base.group_partner_manager"
_CAPABILITIES = (
    "partner.search",
    "partner.get",
    "partner.create",
    "partner.update",
    "partner.archive",
    "partner.restore",
    "partner.accounting.update",
    "partner.bank_account.create",
    "partner.bank_account.update",
    "partner.bank_account.archive",
    "partner.bank_account.restore",
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
    def test_partner_master_data_batch_rolls_back_one_chain_per_alias() -> None:
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


def _read(
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


def _accounting_change(env: Any, partner: Any) -> dict[str, Any]:
    terms = env["account.payment.term"].search(
        [
            ("active", "=", True),
            "|",
            ("company_id", "=", False),
            ("company_id", "=", _COMPANY_ID),
        ],
        order="id",
    )
    for term in terms:
        if partner.property_payment_term_id != term:
            return {"property_payment_term_id": term.id}
        if partner.property_supplier_payment_term_id != term:
            return {"property_supplier_payment_term_id": term.id}
    raise RuntimeError("no payment term can exercise partner.accounting.update")


def _exercise(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    marker: str,
) -> tuple[int, int]:
    partner_result = _write(
        env,
        alias,
        run_id,
        "partner.create",
        {
            "name": f"{marker} Partner",
            "company_type": "company",
            "reference": f"REF-{run_id.hex}",
            "email": "partner-smoke@example.invalid",
        },
    )
    partner_id = partner_result["id"]
    partner = env["res.partner"].browse(partner_id)
    if partner_result["state"] != "active" or partner.company_id.id != _COMPANY_ID:
        raise RuntimeError("partner.create returned the wrong company or state")

    updated = _write(
        env,
        alias,
        run_id,
        "partner.update",
        {
            "partner_id": partner_id,
            "changes": {
                "email": "partner-updated@example.invalid",
                "phone": "+81 3 1234 5678",
                "city": "Tokyo",
            },
        },
    )
    if updated["id"] != partner_id or updated["state"] != "active":
        raise RuntimeError("partner.update returned the wrong record")

    found = _read(
        env,
        alias,
        run_id,
        "partner.search",
        {"query": marker, "active": True, "company_type": "company"},
    )
    if [item["id"] for item in found["items"]] != [partner_id]:
        raise RuntimeError("partner.search did not return the created partner")
    item = _read(
        env,
        alias,
        run_id,
        "partner.get",
        {"partner_id": partner_id},
    )
    if (
        item["id"] != partner_id
        or item["reference"] != f"REF-{run_id.hex}"
        or "[ODACV4:" in (item["reference"] or "")
    ):
        raise RuntimeError("partner.get leaked or lost the idempotency marker")

    accounting = _write(
        env,
        alias,
        run_id,
        "partner.accounting.update",
        {"partner_id": partner_id, "changes": _accounting_change(env, partner)},
    )
    if accounting["id"] != partner_id:
        raise RuntimeError("partner.accounting.update returned the wrong partner")

    account_number = f"JP-{run_id.hex[:24]}"
    bank_result = _write(
        env,
        alias,
        run_id,
        "partner.bank_account.create",
        {"partner_id": partner_id, "account_number": account_number},
    )
    bank_id = bank_result["id"]
    if bank_result["state"] != "active" or bank_result["source_id"] != partner_id:
        raise RuntimeError("partner.bank_account.create returned the wrong owner")
    bank_update = _write(
        env,
        alias,
        run_id,
        "partner.bank_account.update",
        {
            "partner_bank_id": bank_id,
            "changes": {
                "account_number": f"JP {run_id.hex[:12]} {run_id.hex[12:24]}",
                "account_holder_name": f"{marker} Holder",
            },
        },
    )
    if bank_update["id"] != bank_id or bank_update["source_id"] != partner_id:
        raise RuntimeError("partner.bank_account.update changed the owner")

    archived_bank = _write(
        env,
        alias,
        run_id,
        "partner.bank_account.archive",
        {"partner_bank_id": bank_id},
    )
    if archived_bank["state"] != "archived":
        raise RuntimeError("partner.bank_account.archive did not archive")
    restored_bank = _write(
        env,
        alias,
        run_id,
        "partner.bank_account.restore",
        {"partner_bank_id": bank_id},
    )
    if restored_bank["state"] != "active":
        raise RuntimeError("partner.bank_account.restore did not restore")

    archived_partner = _write(
        env,
        alias,
        run_id,
        "partner.archive",
        {"partner_id": partner_id},
    )
    if archived_partner["state"] != "archived":
        raise RuntimeError("partner.archive did not archive")
    restored_partner = _write(
        env,
        alias,
        run_id,
        "partner.restore",
        {"partner_id": partner_id},
    )
    if restored_partner["state"] != "active":
        raise RuntimeError("partner.restore did not restore")
    return partner_id, bank_id


def _verify_rollback(
    registry: Any,
    *,
    partner_id: int,
    bank_id: int,
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
        remaining = {
            "partner_id": env["res.partner"].search_count(
                [("id", "=", partner_id)], limit=1
            ),
            "bank_id": env["res.partner.bank"].search_count(
                [("id", "=", bank_id)], limit=1
            ),
            "partner_marker": env["res.partner"].search_count(
                [("name", "ilike", marker)], limit=1
            ),
            "bank_marker": env["res.partner.bank"].search_count(
                [("acc_holder_name", "ilike", marker)], limit=1
            ),
        }
        if any(remaining.values()):
            raise RuntimeError(f"transaction fixtures survived rollback: {remaining}")
        group_id = env.ref(_PARTNER_MANAGER_GROUP).id
        cursor.execute(
            "SELECT 1 FROM res_groups_users_rel WHERE uid = %s AND gid = %s",
            [_USER_ID, group_id],
        )
        if cursor.fetchone():
            raise RuntimeError("temporary partner-manager group survived rollback")
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
    marker = f"ODACV4-PARTNER-{args.alias}-{args.run_id.hex}"
    created: tuple[int, int] | None = None
    failure: Exception | None = None
    try:
        admin_env = api.Environment(
            cursor,
            SUPERUSER_ID,
            {"allowed_company_ids": [_COMPANY_ID], "active_test": False},
        )
        user = admin_env["res.users"].browse(_USER_ID)
        if user.has_group(_PARTNER_MANAGER_GROUP):
            raise RuntimeError(
                "fixed accountant unexpectedly has partner-manager access"
            )
        group = admin_env.ref(_PARTNER_MANAGER_GROUP)
        user.write({"group_ids": [Command.link(group.id)]})
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
            or not env.user.has_group("account.group_account_user")
            or not env.user.has_group(_PARTNER_MANAGER_GROUP)
        ):
            raise RuntimeError("the fixed accountant or temporary group is unavailable")
        created = _exercise(env, args.alias, args.run_id, marker)
    except Exception as exc:  # noqa: BLE001 - rollback must cover every Odoo failure.
        failure = exc
    finally:
        cursor.rollback()
        cursor.close()

    if created is not None:
        _verify_rollback(
            registry,
            partner_id=created[0],
            bank_id=created[1],
            marker=marker,
        )
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
