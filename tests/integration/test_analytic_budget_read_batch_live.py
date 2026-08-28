"""Guarded transactional smoke for the eleven analytic and budget reads."""

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
_ALLOW_ENV = "ODACV4_ALLOW_ANALYTIC_BUDGET_READ_SMOKE"
_ALIASES = ("v4-dev", "v4-e2e")
_PHYSICAL_DATABASES = {
    "v4-dev": "odoo_cli_v4_dev",
    "v4-e2e": "odoo_cli_v4_e2e",
}
_COMPANY_ID = 1
_USER_ID = 5
_USER_LOGIN = "odacv4_g5_accountant"
_CAPABILITY_IDS = (
    "analytic.line.search",
    "analytic.line.get",
    "analytic.distribution_model.list",
    "analytic.distribution_model.get",
    "analytic.applicability.list",
    "analytic.applicability.get",
    "budget.search",
    "budget.get",
    "budget.line.list",
    "budget.line.get",
    "report.budget",
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
        for part in (str(_project_root() / "src"), environment.get("PYTHONPATH"))
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
    assert result == {
        "alias": alias,
        "capabilities": list(_CAPABILITY_IDS),
        "company_id": _COMPANY_ID,
        "database": _PHYSICAL_DATABASES[alias],
        "overlap_rows": 2,
        "rollback_verified": True,
        "user_id": _USER_ID,
    }
    return result


if pytest is not None:

    @pytest.mark.integration
    @pytest.mark.parametrize("alias", _ALIASES)
    def test_analytic_budget_batch_preserves_overlapping_report_rows_and_rolls_back(
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


class _CoreRuntimePort:
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


class _BudgetReportRuntimePort:
    def __init__(self, env: Any) -> None:
        self.env = env
        self.pages: list[dict[str, Any]] = []

    @property
    def user_id(self) -> int:
        return self.env.uid

    def read(self, *, company_id: int, parameters: dict[str, Any]) -> dict[str, Any]:
        from odoo_accounting_cli_v4.bridge.budget_report_runtime import dispatch
        from odoo_accounting_cli_v4.bridge.runtime import RuntimeFailure

        page = dispatch(
            self.env,
            {"company_id": company_id, "parameters": parameters},
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


def _assert_page(page: dict[str, Any], capability_id: str, user_id: int) -> None:
    if (
        set(page) != _PAGE_KEYS
        or page["user_id"] != user_id
        or page["company_visible"] is not True
        or page["module_installed"] is not True
        or page["access_allowed"] is not True
        or page["cursor_found"] is not True
    ):
        raise RuntimeError(f"{capability_id} returned an invalid runtime page")


def _core_read(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    from odoo_accounting_cli_v4.capabilities.core_object_reads import read_core_object

    port = _CoreRuntimePort(env)
    result = read_core_object(
        capability_id,
        port,
        _request(alias, run_id, capability_id, parameters),
    )
    if len(port.pages) != 1:
        raise RuntimeError(f"{capability_id} did not issue exactly one runtime read")
    _assert_page(port.pages[0], capability_id, env.uid)
    return result


def _report_read(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    from odoo_accounting_cli_v4.capabilities.budget_report import read_budget_report

    port = _BudgetReportRuntimePort(env)
    result = read_budget_report(
        port,
        _request(alias, run_id, "report.budget", parameters),
    )
    if len(port.pages) != 1:
        raise RuntimeError("report.budget did not issue exactly one runtime read")
    _assert_page(port.pages[0], "report.budget", env.uid)
    return result


def _setup_fixtures(admin_env: Any, marker: str) -> dict[str, Any]:
    plan = admin_env["account.analytic.plan"].search(
        [("parent_id", "=", False)], order="id", limit=1
    )
    if not plan:
        raise RuntimeError("no root analytic plan is available")
    plan_column = plan._column_name()
    analytic_account = admin_env["account.analytic.account"].create(
        {
            "name": marker,
            "code": marker,
            "active": True,
            "plan_id": plan.id,
            "company_id": _COMPANY_ID,
        }
    )
    analytic_line = admin_env["account.analytic.line"].create(
        {
            "name": marker,
            "date": "2026-08-24",
            "amount": 125.5,
            "unit_amount": 2,
            "company_id": _COMPANY_ID,
            "user_id": _USER_ID,
            plan_column: analytic_account.id,
        }
    )
    distribution_model = admin_env["account.analytic.distribution.model"].create(
        {
            "sequence": 10,
            "company_id": _COMPANY_ID,
            "analytic_distribution": {str(analytic_account.id): 100},
        }
    )
    applicability = admin_env["account.analytic.applicability"].create(
        {
            "analytic_plan_id": plan.id,
            "business_domain": "general",
            "applicability": "optional",
            "company_id": _COMPANY_ID,
        }
    )
    budget = admin_env["budget.analytic"].create(
        {
            "name": marker,
            "date_from": "2026-08-01",
            "date_to": "2026-08-31",
            "state": "draft",
            "budget_type": "both",
            "company_id": _COMPANY_ID,
            "user_id": _USER_ID,
        }
    )
    budget_lines = admin_env["budget.line"].create(
        [
            {
                "sequence": sequence,
                "budget_analytic_id": budget.id,
                "budget_amount": amount,
                plan_column: analytic_account.id,
            }
            for sequence, amount in ((10, 1000), (20, 2000))
        ]
    )
    admin_env.flush_all()
    if len(budget_lines) != 2 or len(set(budget_lines.ids)) != 2:
        raise RuntimeError("the two overlapping budget lines were not created")
    return {
        "plan": plan.id,
        "analytic_account": analytic_account.id,
        "analytic_line": analytic_line.id,
        "distribution_model": distribution_model.id,
        "applicability": applicability.id,
        "budget": budget.id,
        "budget_lines": sorted(budget_lines.ids),
    }


def _select_item(
    data: dict[str, Any], capability_id: str, expected_id: int
) -> dict[str, Any]:
    selected = [item for item in data.get("items", []) if item.get("id") == expected_id]
    if len(selected) != 1:
        raise RuntimeError(f"{capability_id} did not return its fixture")
    return selected[0]


def _assert_get(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    id_field: str,
    expected_id: int,
) -> None:
    item = _core_read(env, alias, run_id, capability_id, {id_field: expected_id})
    if item.get("id") != expected_id:
        raise RuntimeError(f"{capability_id} returned the wrong fixture")


def _exercise_core_reads(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    marker: str,
    fixture: dict[str, Any],
) -> list[str]:
    covered: list[str] = []
    analytic_line = _select_item(
        _core_read(
            env,
            alias,
            run_id,
            "analytic.line.search",
            {
                "query": marker,
                "date_from": "2026-08-24",
                "date_to": "2026-08-24",
                "analytic_account_id": fixture["analytic_account"],
                "limit": 100,
                "cursor": None,
            },
        ),
        "analytic.line.search",
        fixture["analytic_line"],
    )
    if analytic_line.get("company_id") != _COMPANY_ID:
        raise RuntimeError("analytic.line.search escaped the selected company")
    covered.append("analytic.line.search")
    _assert_get(
        env,
        alias,
        run_id,
        "analytic.line.get",
        "analytic_line_id",
        fixture["analytic_line"],
    )
    covered.append("analytic.line.get")

    for list_id, get_id, id_field, fixture_key in (
        (
            "analytic.distribution_model.list",
            "analytic.distribution_model.get",
            "distribution_model_id",
            "distribution_model",
        ),
        (
            "analytic.applicability.list",
            "analytic.applicability.get",
            "applicability_id",
            "applicability",
        ),
    ):
        _select_item(
            _core_read(env, alias, run_id, list_id, {"limit": 1000, "cursor": None}),
            list_id,
            fixture[fixture_key],
        )
        covered.append(list_id)
        _assert_get(env, alias, run_id, get_id, id_field, fixture[fixture_key])
        covered.append(get_id)

    _select_item(
        _core_read(
            env,
            alias,
            run_id,
            "budget.search",
            {
                "query": marker,
                "state": "draft",
                "budget_type": "both",
                "date_from": "2026-08-01",
                "date_to": "2026-08-31",
                "limit": 100,
                "cursor": None,
            },
        ),
        "budget.search",
        fixture["budget"],
    )
    covered.append("budget.search")
    _assert_get(env, alias, run_id, "budget.get", "budget_id", fixture["budget"])
    covered.append("budget.get")

    budget_lines = _core_read(
        env,
        alias,
        run_id,
        "budget.line.list",
        {
            "budget_id": fixture["budget"],
            "plan_id": fixture["plan"],
            "analytic_account_id": fixture["analytic_account"],
            "limit": 100,
            "cursor": None,
        },
    )
    returned_line_ids = {
        item.get("id")
        for item in budget_lines.get("items", [])
        if item.get("id") in fixture["budget_lines"]
    }
    if returned_line_ids != set(fixture["budget_lines"]):
        raise RuntimeError("budget.line.list lost an overlapping budget line")
    covered.append("budget.line.list")
    _assert_get(
        env,
        alias,
        run_id,
        "budget.line.get",
        "budget_line_id",
        fixture["budget_lines"][0],
    )
    covered.append("budget.line.get")
    return covered


def _exercise_report(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    fixture: dict[str, Any],
) -> int:
    cursor = None
    rows: list[dict[str, Any]] = []
    seen_cursors: set[str] = set()
    for _ in range(4):
        page = _report_read(
            env,
            alias,
            run_id,
            {
                "budget_id": fixture["budget"],
                "plan_id": fixture["plan"],
                "analytic_account_id": fixture["analytic_account"],
                "line_type": "achieved",
                "limit": 1,
                "cursor": cursor,
            },
        )
        rows.extend(page["items"])
        if not page["has_more"]:
            break
        cursor = page["next_cursor"]
        if not isinstance(cursor, str) or cursor in seen_cursors:
            raise RuntimeError("report.budget returned an unstable cursor")
        seen_cursors.add(cursor)
    else:
        raise RuntimeError("report.budget pagination did not terminate")

    if len(rows) != 2:
        raise RuntimeError("report.budget did not preserve both overlapping rows")
    if {row["row_key"] for row in rows} != {f"aal{fixture['analytic_line']}"}:
        raise RuntimeError("report.budget returned the wrong analytic source")
    if {row["budget_line"]["id"] for row in rows} != set(fixture["budget_lines"]):
        raise RuntimeError("report.budget merged the duplicate SQL ids")
    positions = [
        (
            row["date"],
            row["row_key"],
            row["budget_line"]["id"],
            row["line_type"],
            row["source"]["model"],
            row["source"]["id"],
        )
        for row in rows
    ]
    if positions != sorted(set(positions)):
        raise RuntimeError("report.budget pagination duplicated or reordered a row")
    if any(
        row["company_id"] != _COMPANY_ID or row["achieved_amount"] != "125.5"
        for row in rows
    ):
        raise RuntimeError("report.budget returned an invalid company or amount")

    filtered = _report_read(
        env,
        alias,
        run_id,
        {
            "budget_id": fixture["budget"],
            "budget_line_id": fixture["budget_lines"][0],
            "date_from": "2026-08-01",
            "date_to": "2026-08-31",
            "line_type": "budget",
            "limit": 10,
            "cursor": None,
        },
    )
    if (
        len(filtered["items"]) != 1
        or filtered["items"][0]["line_type"] != "budget"
        or filtered["items"][0]["budget_line"]["id"] != fixture["budget_lines"][0]
    ):
        raise RuntimeError("report.budget did not enforce its fixed filters")
    return len(rows)


def _verify_rollback(registry: Any, marker: str, fixture: dict[str, Any]) -> None:
    from odoo import SUPERUSER_ID, api

    cursor = registry.cursor()
    try:
        env = api.Environment(
            cursor,
            SUPERUSER_ID,
            {"allowed_company_ids": [_COMPANY_ID], "active_test": False},
        )
        remaining_markers = {
            "analytic_account": env["account.analytic.account"].search_count(
                [("name", "=", marker)], limit=1
            ),
            "analytic_line": env["account.analytic.line"].search_count(
                [("name", "=", marker)], limit=1
            ),
            "budget": env["budget.analytic"].search_count(
                [("name", "=", marker)], limit=1
            ),
        }
        created = {
            "distribution_model": (
                "account.analytic.distribution.model",
                [fixture["distribution_model"]],
            ),
            "applicability": (
                "account.analytic.applicability",
                [fixture["applicability"]],
            ),
            "budget_lines": ("budget.line", fixture["budget_lines"]),
        }
        surviving_ids = {
            key: env[model].browse(ids).exists().ids
            for key, (model, ids) in created.items()
        }
        if any(remaining_markers.values()) or any(surviving_ids.values()):
            raise RuntimeError(
                "transaction fixtures survived rollback: "
                f"markers={remaining_markers}, ids={surviving_ids}"
            )
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
            "--logfile=/dev/null",
        ]
    )
    registry = Registry(args.database)
    cursor = registry.cursor()
    marker = f"ODACV4-ANALYTIC-BUDGET-{args.alias}-{args.run_id.hex}"
    fixture: dict[str, Any] | None = None
    overlap_rows: int | None = None
    failure: Exception | None = None
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
            or user.id != _USER_ID
            or not user.active
            or company not in user.company_ids
        ):
            raise RuntimeError("the configured company or business user is unavailable")
        fixture = _setup_fixtures(admin_env, marker)
        business_env = api.Environment(cursor, user.id, context)
        covered = _exercise_core_reads(
            business_env, args.alias, args.run_id, marker, fixture
        )
        overlap_rows = _exercise_report(business_env, args.alias, args.run_id, fixture)
        covered.append("report.budget")
        if tuple(covered) != _CAPABILITY_IDS:
            raise RuntimeError("the live worker did not cover all eleven commands")
    except Exception as exc:  # noqa: BLE001 - rollback must preserve any failure
        failure = exc
    finally:
        cursor.rollback()
        cursor.close()
        if fixture is not None:
            _verify_rollback(registry, marker, fixture)

    if failure is not None:
        raise failure
    if fixture is None or overlap_rows != 2:
        raise RuntimeError("the overlapping budget fixture was not verified")
    sys.stdout.write(
        json.dumps(
            {
                "alias": args.alias,
                "capabilities": list(_CAPABILITY_IDS),
                "company_id": _COMPANY_ID,
                "database": args.database,
                "overlap_rows": overlap_rows,
                "rollback_verified": True,
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
