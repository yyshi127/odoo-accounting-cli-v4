"""Guarded transactional smoke for the twelve reference-object reads.

Each alias runs in one Odoo worker and one database transaction.  The worker
creates the three fixtures missing from the isolated databases as the
administrator, executes the public core capability contract as the configured
business user, and explicitly rolls the whole transaction back.
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
_ALLOW_ENV = "ODACV4_ALLOW_REFERENCE_READ_SMOKE"
_ALIASES = ("v4-dev", "v4-e2e")
_PHYSICAL_DATABASES = {
    "v4-dev": "odoo_cli_v4_dev",
    "v4-e2e": "odoo_cli_v4_e2e",
}
_COMPANY_ID = 1
_USER_LOGIN = "odacv4_g5_accountant"
_CAPABILITY_IDS = (
    "product.search",
    "product.get",
    "analytic.plan.list",
    "analytic.plan.get",
    "analytic.account.search",
    "analytic.account.get",
    "fiscal_position.search",
    "fiscal_position.get",
    "account.tag.list",
    "account.tag.get",
    "tax.group.list",
    "tax.group.get",
)
_PAGE_KEYS = {
    "user_id",
    "company_visible",
    "module_installed",
    "access_allowed",
    "cursor_found",
    "items",
}


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _enabled_runtime(alias: str) -> tuple[Path, dict[str, Any]]:
    assert pytest is not None
    if os.environ.get(_ALLOW_ENV) != "1":
        pytest.skip(f"set {_ALLOW_ENV}=1 to authorize transactional fixture setup")
    raw_path = os.environ.get(_CONFIG_ENV)
    if not raw_path:
        pytest.skip(f"{_CONFIG_ENV} is not configured")
    path = Path(raw_path)
    if not path.is_file():
        pytest.skip(f"{_CONFIG_ENV} does not name an existing file")

    document = json.loads(path.read_text(encoding="utf-8"))
    aliases = document.get("aliases")
    assert isinstance(aliases, dict)
    entry = aliases.get(alias)
    assert isinstance(entry, dict)
    assert entry.get("database") == _PHYSICAL_DATABASES[alias]
    users = entry.get("companies", {}).get(str(_COMPANY_ID))
    assert isinstance(users, list) and _USER_LOGIN in users
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

    executable = Path(argv[0])
    configured_runtime = Path(argv[3])
    odoo_config = Path(argv[5])
    odoo_source = Path(argv[7])
    assert executable.is_absolute() and executable.is_file()
    assert configured_runtime.resolve(strict=True) == config_path.resolve(strict=True)
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
            _PHYSICAL_DATABASES[alias],
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
) -> dict[str, Any]:
    command, timeout = _worker_command(alias, run_id, config_path, runtime)
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = os.pathsep.join(
        part
        for part in (
            str(_project_root() / "src"),
            environment.get("PYTHONPATH"),
        )
        if part
    )
    completed = subprocess.run(
        command,
        cwd=_project_root(),
        env=environment,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert len(completed.stdout.splitlines()) == 1
    result = json.loads(completed.stdout)
    assert result["alias"] == alias
    assert result["database"] == _PHYSICAL_DATABASES[alias]
    assert result["company_id"] == _COMPANY_ID
    assert result["capabilities"] == list(_CAPABILITY_IDS)
    assert result["rollback_verified"] is True
    assert isinstance(result["user_id"], int) and result["user_id"] > 0
    return result


if pytest is not None:

    @pytest.mark.integration
    @pytest.mark.parametrize("alias", _ALIASES)
    def test_reference_object_batch_rolls_back_one_real_chain_per_alias(
        alias: str,
    ) -> None:
        config_path, runtime = _enabled_runtime(alias)
        _run_worker(alias, uuid.uuid4(), config_path, runtime)


def _worker_arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-worker", action="store_true", required=True)
    parser.add_argument("--odoo-config", type=Path, required=True)
    parser.add_argument("--odoo-source", type=Path, required=True)
    parser.add_argument("--alias", choices=_ALIASES, required=True)
    parser.add_argument(
        "--database", choices=tuple(_PHYSICAL_DATABASES.values()), required=True
    )
    parser.add_argument("--run-id", type=uuid.UUID, required=True)
    args = parser.parse_args(argv)
    if args.database != _PHYSICAL_DATABASES[args.alias]:
        parser.error("alias and physical database do not match")
    if not args.odoo_config.is_absolute() or not args.odoo_config.is_file():
        parser.error("odoo-config must be an existing absolute file")
    if not args.odoo_source.is_absolute() or not args.odoo_source.is_dir():
        parser.error("odoo-source must be an existing absolute directory")
    return args


class _RuntimePort:
    def __init__(self, env: Any) -> None:
        self.env = env
        self.pages: list[dict[str, Any]] = []

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
        self.pages.append(page)
        return page


def _request(
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "request_id": str(uuid.uuid5(run_id, f"reference-object-live:{capability_id}")),
        "context": {
            "database": alias,
            "company_id": _COMPANY_ID,
            "user_login": _USER_LOGIN,
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": parameters,
    }


def _read(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    from odoo_accounting_cli_v4.capabilities.core_object_reads import read_core_object

    port = _RuntimePort(env)
    result = read_core_object(
        capability_id,
        port,
        _request(alias, run_id, capability_id, parameters),
    )
    if len(port.pages) != 1:
        raise RuntimeError(f"{capability_id} did not issue exactly one runtime read")
    page = port.pages[0]
    if (
        set(page) != _PAGE_KEYS
        or page["user_id"] != env.uid
        or page["company_visible"] is not True
        or page["module_installed"] is not True
        or page["access_allowed"] is not True
        or page["cursor_found"] is not True
    ):
        raise RuntimeError(f"{capability_id} returned an invalid runtime page")
    return result


def _setup_fixtures(admin_env: Any, marker: str) -> dict[str, int]:
    plan = admin_env["account.analytic.plan"].search([], order="id", limit=1)
    if not plan:
        raise RuntimeError("account.analytic.plan has no live fixture row")

    product = admin_env["product.product"].create(
        {
            "name": marker,
            "default_code": marker,
            "type": "consu",
            "company_id": _COMPANY_ID,
            "active": True,
        }
    )
    analytic = admin_env["account.analytic.account"].create(
        {
            "name": marker,
            "code": marker,
            "active": True,
            "plan_id": plan.id,
            "company_id": _COMPANY_ID,
        }
    )
    fiscal_position = admin_env["account.fiscal.position"].create(
        {
            "name": marker,
            "active": True,
            "auto_apply": False,
            "company_id": _COMPANY_ID,
        }
    )
    admin_env.flush_all()
    return {
        "product": product.id,
        "plan": plan.id,
        "analytic": analytic.id,
        "fiscal_position": fiscal_position.id,
    }


def _select_item(
    data: dict[str, Any], capability_id: str, *, expected_id: int | None = None
) -> dict[str, Any]:
    items = data.get("items")
    if not isinstance(items, list) or not items:
        raise RuntimeError(f"{capability_id} has no live fixture rows")
    if expected_id is None:
        return items[0]
    selected = [item for item in items if item.get("id") == expected_id]
    if len(selected) != 1:
        raise RuntimeError(f"{capability_id} did not return its transaction fixture")
    return selected[0]


def _exercise_batch(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    marker: str,
    fixture_ids: dict[str, int],
) -> None:
    collections = (
        (
            "product.search",
            {"query": marker, "active": True, "limit": 100, "cursor": None},
            "product.get",
            "product_id",
            fixture_ids["product"],
        ),
        (
            "analytic.plan.list",
            {"limit": 1000, "cursor": None},
            "analytic.plan.get",
            "plan_id",
            fixture_ids["plan"],
        ),
        (
            "analytic.account.search",
            {
                "query": marker,
                "active": True,
                "plan_id": fixture_ids["plan"],
                "limit": 100,
                "cursor": None,
            },
            "analytic.account.get",
            "analytic_account_id",
            fixture_ids["analytic"],
        ),
        (
            "fiscal_position.search",
            {
                "query": marker,
                "active": True,
                "auto_apply": False,
                "limit": 100,
                "cursor": None,
            },
            "fiscal_position.get",
            "fiscal_position_id",
            fixture_ids["fiscal_position"],
        ),
        (
            "account.tag.list",
            {"limit": 1000, "cursor": None},
            "account.tag.get",
            "tag_id",
            None,
        ),
        (
            "tax.group.list",
            {"limit": 1000, "cursor": None},
            "tax.group.get",
            "tax_group_id",
            None,
        ),
    )
    selected: list[tuple[str, str, int]] = []
    covered: list[str] = []
    for list_id, parameters, get_id, id_field, expected_id in collections:
        data = _read(env, alias, run_id, list_id, parameters)
        item = _select_item(data, list_id, expected_id=expected_id)
        selected.append((get_id, id_field, item["id"]))
        covered.append(list_id)

    for get_id, id_field, record_id in selected:
        data = _read(env, alias, run_id, get_id, {id_field: record_id})
        if data.get("id") != record_id:
            raise RuntimeError(f"{get_id} returned the wrong record")
        covered.append(get_id)

    if set(covered) != set(_CAPABILITY_IDS) or len(covered) != len(_CAPABILITY_IDS):
        raise RuntimeError(
            "the live worker did not cover the frozen twelve-command batch"
        )


def _verify_rollback(registry: Any, marker: str) -> None:
    from odoo import SUPERUSER_ID, api

    cursor = registry.cursor()
    try:
        env = api.Environment(
            cursor,
            SUPERUSER_ID,
            {"allowed_company_ids": [_COMPANY_ID], "active_test": False},
        )
        remaining = {
            "product": env["product.product"].search_count(
                [("default_code", "=", marker)], limit=1
            ),
            "analytic": env["account.analytic.account"].search_count(
                [("code", "=", marker)], limit=1
            ),
            "fiscal_position": env["account.fiscal.position"].search_count(
                [("name", "=", marker)], limit=1
            ),
        }
        if any(remaining.values()):
            raise RuntimeError(f"transaction fixtures survived rollback: {remaining}")
    finally:
        cursor.rollback()
        cursor.close()


def _live_worker(argv: list[str] | None = None) -> int:
    args = _worker_arguments(argv)
    root = _project_root()
    sys.path.insert(0, str(args.odoo_source.resolve(strict=True)))
    sys.path.insert(0, str((root / "src").resolve(strict=True)))

    from odoo import SUPERUSER_ID, api
    from odoo.orm.registry import Registry
    from odoo.tools import config as odoo_runtime_config

    odoo_runtime_config.parse_config(
        [
            "--config",
            str(args.odoo_config.resolve(strict=True)),
            "--database",
            args.database,
            "--no-http",
        ]
    )
    registry = Registry(args.database)
    cursor = registry.cursor()
    marker = f"ODACV4-REFERENCE-{args.alias}-{args.run_id.hex}"
    user_id: int | None = None
    try:
        context = {
            "allowed_company_ids": [_COMPANY_ID],
            "active_test": True,
            "lang": "en_US",
            "tz": "Asia/Shanghai",
        }
        admin_env = api.Environment(cursor, SUPERUSER_ID, context)
        company = admin_env["res.company"].browse(_COMPANY_ID).exists()
        user = (
            admin_env["res.users"]
            .with_context(active_test=False)
            .search([("login", "=", _USER_LOGIN)], limit=1)
        )
        if (
            not company
            or not user
            or not user.active
            or company not in user.company_ids
        ):
            raise RuntimeError("the configured company or business user is unavailable")

        fixture_ids = _setup_fixtures(admin_env, marker)
        user_id = user.id
        business_env = api.Environment(cursor, user_id, context)
        _exercise_batch(
            business_env,
            args.alias,
            args.run_id,
            marker,
            fixture_ids,
        )
    finally:
        cursor.rollback()
        cursor.close()

    _verify_rollback(registry, marker)
    sys.stdout.write(
        json.dumps(
            {
                "alias": args.alias,
                "capabilities": list(_CAPABILITY_IDS),
                "company_id": _COMPANY_ID,
                "database": args.database,
                "rollback_verified": True,
                "user_id": user_id,
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
