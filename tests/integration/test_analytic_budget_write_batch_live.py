"""Transactional dual-database smoke for analytic and budget capabilities."""

from __future__ import annotations

import argparse
import hashlib
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
_ALLOW_ENV = "ODACV4_ALLOW_ANALYTIC_BUDGET_WRITE_SMOKE"
_ALIASES = ("v4-dev", "v4-e2e")
_DATABASES = {
    "v4-dev": "odoo_cli_v4_dev",
    "v4-e2e": "odoo_cli_v4_e2e",
}
_COMPANY_ID = 1
_USER_ID = 5
_USER_LOGIN = "odacv4_g5_accountant"
_CAPABILITIES = (
    "analytic.plan.create",
    "analytic.plan.update",
    "analytic.account.create",
    "analytic.account.update",
    "analytic.account.archive",
    "analytic.account.restore",
    "analytic.line.create",
    "analytic.line.update",
    "analytic.line.summary",
    "analytic.line.delete",
    "budget.create",
    "budget.update_draft",
    "budget.lines.replace",
    "budget.confirm",
    "budget.reset_to_draft",
    "budget.cancel",
    "budget.mark_done",
)


class _RollbackDelete(Exception):
    """Force the delete-only savepoint to roll back after verification."""


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
        "user_id": _USER_ID,
    }


if pytest is not None:

    @pytest.mark.integration
    def test_analytic_budget_write_batch_rolls_back_one_chain_per_alias() -> None:
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


def _digest(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:32]


def _key(
    capability_id: str,
    parameters: dict[str, Any],
    explicit: str | None = None,
) -> str:
    if explicit is not None:
        return explicit
    if capability_id == "analytic.account.update":
        return (
            f"{capability_id}:{parameters['analytic_account_id']}:"
            f"{_digest(parameters['changes'])}"
        )
    if capability_id in {"analytic.plan.update", "analytic.line.update"}:
        target_id = parameters.get("plan_id", parameters.get("analytic_line_id"))
        return f"{capability_id}:{target_id}:{_digest(parameters['changes'])}"
    if capability_id in {"analytic.account.archive", "analytic.account.restore"}:
        return f"{capability_id}:{parameters['analytic_account_id']}"
    if capability_id == "analytic.line.delete":
        return f"{capability_id}:{parameters['analytic_line_id']}"
    if capability_id == "budget.update_draft":
        return (
            f"{capability_id}:{parameters['budget_id']}:"
            f"{_digest(parameters['changes'])}"
        )
    if capability_id == "budget.lines.replace":
        return (
            f"{capability_id}:{parameters['budget_id']}:{_digest(parameters['lines'])}"
        )
    return f"{capability_id}:{parameters['budget_id']}"


def _request(
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    parameters: dict[str, Any],
    idempotency_key: str,
) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "request_id": str(
            uuid.uuid5(
                run_id,
                f"analytic-budget-write:{capability_id}:{idempotency_key}",
            )
        ),
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
    *,
    explicit_key: str | None = None,
    replay: bool = True,
) -> dict[str, Any]:
    from odoo_accounting_cli_v4.capabilities.core_writes import execute_core_write

    key = _key(capability_id, parameters, explicit_key)
    request = _request(alias, run_id, capability_id, parameters, key)
    port = _CoreWritePort(env)
    first = execute_core_write(port, capability_id, request, key, capability_id)
    if first["idempotent_replay"] is not False:
        raise RuntimeError(f"{capability_id} replayed its first execution")
    if not replay:
        return first["result"]
    second = execute_core_write(port, capability_id, request, key, capability_id)
    if second["idempotent_replay"] is not True or second["result"] != first["result"]:
        raise RuntimeError(f"{capability_id} did not replay deterministically")
    return first["result"]


class _JournalAnalysisPort:
    def __init__(self, env: Any) -> None:
        self.env = env

    @property
    def user_id(self) -> int:
        return self.env.uid

    def read(self, **payload: Any) -> dict[str, Any]:
        from odoo_accounting_cli_v4.bridge.journal_analysis_runtime import dispatch
        from odoo_accounting_cli_v4.bridge.runtime import RuntimeFailure

        return dispatch(
            self.env,
            payload,
            payload["company_id"],
            failure_type=RuntimeFailure,
        )


def _analytic_summary(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    from odoo_accounting_cli_v4.capabilities.journal_analysis import (
        read_journal_analysis,
    )

    request = _request(
        alias,
        run_id,
        "analytic.line.summary",
        parameters,
        "read",
    )
    return read_journal_analysis(
        _JournalAnalysisPort(env), "analytic.line.summary", request
    )


def _exercise(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    marker: str,
) -> tuple[int, int, int, int, int, list[int]]:
    root_plan, _other_plans = env["account.analytic.plan"]._get_all_plans()
    if len(root_plan) != 1:
        raise RuntimeError("no root analytic plan is available")

    plan = _write(
        env,
        alias,
        run_id,
        "analytic.plan.create",
        {
            "name": f"{marker} Plan",
            "parent_plan_id": root_plan.id,
            "color": 0,
            "default_applicability": "optional",
        },
        explicit_key=f"analytic-plan-create-{run_id.hex}-{alias}",
    )
    plan_id = plan["id"]
    if plan["state"] != "active" or plan["source_id"] != root_plan.id:
        raise RuntimeError("analytic.plan.create returned the wrong parent or state")
    updated_plan = _write(
        env,
        alias,
        run_id,
        "analytic.plan.update",
        {"plan_id": plan_id, "changes": {"color": 1}},
    )
    if updated_plan["id"] != plan_id or updated_plan["state"] != "active":
        raise RuntimeError("analytic.plan.update returned the wrong record")

    analytic = _write(
        env,
        alias,
        run_id,
        "analytic.account.create",
        {
            "name": f"{marker} Analytic",
            "plan_id": plan_id,
            "code": None,
            "partner_id": None,
        },
        explicit_key=f"analytic-create-{run_id.hex}-{alias}",
    )
    analytic_id = analytic["id"]
    if analytic["state"] != "active" or analytic["source_id"] != plan_id:
        raise RuntimeError("analytic.account.create returned the wrong plan or state")
    updated_analytic = _write(
        env,
        alias,
        run_id,
        "analytic.account.update",
        {
            "analytic_account_id": analytic_id,
            "changes": {"code": marker, "partner_id": None},
        },
    )
    if updated_analytic["id"] != analytic_id or updated_analytic["state"] != "active":
        raise RuntimeError("analytic.account.update returned the wrong record")

    archived = _write(
        env,
        alias,
        run_id,
        "analytic.account.archive",
        {"analytic_account_id": analytic_id},
    )
    if archived["state"] != "archived":
        raise RuntimeError("analytic.account.archive left the account active")
    restored = _write(
        env,
        alias,
        run_id,
        "analytic.account.restore",
        {"analytic_account_id": analytic_id},
    )
    if restored["state"] != "active":
        raise RuntimeError("analytic.account.restore left the account archived")

    analytic_line = _write(
        env,
        alias,
        run_id,
        "analytic.line.create",
        {
            "name": f"{marker} Manual",
            "date": "2026-08-15",
            "amount": "-125.5",
            "analytic_account_id": analytic_id,
            "reference": marker,
            "unit_amount": "2",
        },
        explicit_key=f"analytic-line-create-{run_id.hex}-{alias}",
    )
    analytic_line_id = analytic_line["id"]
    updated_line = _write(
        env,
        alias,
        run_id,
        "analytic.line.update",
        {
            "analytic_line_id": analytic_line_id,
            "changes": {"amount": "-150", "unit_amount": "3"},
        },
    )
    if updated_line["id"] != analytic_line_id or updated_line["state"] != "manual":
        raise RuntimeError("analytic.line.update returned the wrong record")
    summary = _analytic_summary(
        env,
        alias,
        run_id,
        {
            "date_from": "2026-08-01",
            "date_to": "2026-08-31",
            "plan_id": plan_id,
            "analytic_account_id": analytic_id,
        },
    )
    if summary["totals"] != {
        "row_count": 1,
        "amount": "-150",
        "unit_amount": "3",
    }:
        raise RuntimeError("analytic.line.summary returned the wrong totals")
    try:
        with env.cr.savepoint():
            deleted = _write(
                env,
                alias,
                run_id,
                "analytic.line.delete",
                {"analytic_line_id": analytic_line_id},
                replay=False,
            )
            if deleted["id"] != analytic_line_id or deleted["state"] != "deleted":
                raise RuntimeError("analytic.line.delete returned the wrong record")
            if env["account.analytic.line"].search_count(
                [("id", "=", analytic_line_id)], limit=1
            ):
                raise RuntimeError("analytic.line.delete left the record visible")
            raise _RollbackDelete
    except _RollbackDelete:
        env.invalidate_all()
    restored_line = env["account.analytic.line"].browse(analytic_line_id).exists()
    if len(restored_line) != 1:
        raise RuntimeError("analytic.line.delete did not roll back at the savepoint")

    main = _write(
        env,
        alias,
        run_id,
        "budget.create",
        {
            "name": f"{marker} Main",
            "date_from": "2026-08-01",
            "date_to": "2026-08-31",
            "budget_type": "expense",
        },
        explicit_key=f"budget-main-create-{run_id.hex}-{alias}",
    )
    main_id = main["id"]
    canceled = _write(
        env,
        alias,
        run_id,
        "budget.create",
        {
            "name": f"{marker} Cancel",
            "date_from": "2026-08-01",
            "date_to": "2026-08-31",
            "budget_type": "revenue",
        },
        explicit_key=f"budget-cancel-create-{run_id.hex}-{alias}",
    )
    canceled_id = canceled["id"]

    updated_budget = _write(
        env,
        alias,
        run_id,
        "budget.update_draft",
        {"budget_id": main_id, "changes": {"budget_type": "both"}},
    )
    if updated_budget["state"] != "draft":
        raise RuntimeError("budget.update_draft changed the lifecycle state")

    replaced = _write(
        env,
        alias,
        run_id,
        "budget.lines.replace",
        {
            "budget_id": main_id,
            "lines": [
                {
                    "budget_amount": "1250.50",
                    "analytic_account_ids": [analytic_id],
                }
            ],
        },
    )
    line_ids = replaced["line_ids"]
    if len(line_ids) != 1:
        raise RuntimeError("budget.lines.replace did not create exactly one line")
    line = env["budget.line"].browse(line_ids[0]).exists()
    column = root_plan._column_name()
    if (
        len(line) != 1
        or str(line.budget_amount) != "1250.5"
        or line[column].id != analytic_id
    ):
        raise RuntimeError("budget.lines.replace did not preserve amount and account")

    confirmed = _write(env, alias, run_id, "budget.confirm", {"budget_id": main_id})
    if confirmed["state"] != "confirmed":
        raise RuntimeError("budget.confirm did not open the budget")
    reset = _write(env, alias, run_id, "budget.reset_to_draft", {"budget_id": main_id})
    if reset["state"] != "draft":
        raise RuntimeError("budget.reset_to_draft did not restore draft")
    _write(env, alias, run_id, "budget.confirm", {"budget_id": main_id})
    done = _write(env, alias, run_id, "budget.mark_done", {"budget_id": main_id})
    if done["state"] != "done":
        raise RuntimeError("budget.mark_done did not finish the budget")
    canceled_result = _write(
        env, alias, run_id, "budget.cancel", {"budget_id": canceled_id}
    )
    if canceled_result["state"] != "canceled":
        raise RuntimeError("budget.cancel did not cancel the draft budget")
    return plan_id, analytic_id, analytic_line_id, main_id, canceled_id, line_ids


def _verify_rollback(
    registry: Any,
    *,
    plan_id: int,
    analytic_id: int,
    analytic_line_id: int,
    budget_ids: tuple[int, int],
    line_ids: list[int],
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
            "plan_id": env["account.analytic.plan"].search_count(
                [("id", "=", plan_id)], limit=1
            ),
            "analytic_id": env["account.analytic.account"].search_count(
                [("id", "=", analytic_id)], limit=1
            ),
            "analytic_line_id": env["account.analytic.line"].search_count(
                [("id", "=", analytic_line_id)], limit=1
            ),
            "budget_ids": env["budget.analytic"].search_count(
                [("id", "in", list(budget_ids))], limit=1
            ),
            "line_ids": env["budget.line"].search_count(
                [("id", "in", line_ids)], limit=1
            ),
            "analytic_marker": env["account.analytic.account"].search_count(
                [("name", "ilike", marker)], limit=1
            ),
            "plan_marker": env["account.analytic.plan"].search_count(
                [("name", "ilike", marker)], limit=1
            ),
            "line_marker": env["account.analytic.line"].search_count(
                [("name", "ilike", marker)], limit=1
            ),
            "budget_marker": env["budget.analytic"].search_count(
                [("name", "ilike", marker)], limit=1
            ),
        }
        if any(remaining.values()):
            raise RuntimeError(f"transaction fixtures survived rollback: {remaining}")
    finally:
        cursor.rollback()
        cursor.close()


def _live_worker(argv: list[str] | None = None) -> int:
    args = _arguments(argv)
    sys.path.insert(0, str(args.odoo_source.resolve(strict=True)))
    sys.path.insert(0, str((_root() / "src").resolve(strict=True)))

    from odoo import api
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
    marker = f"ODACV4-AN-BUD-{args.alias}-{args.run_id.hex}"
    created: tuple[int, int, int, int, int, list[int]] | None = None
    failure: Exception | None = None
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
        user = env.user
        if (
            env.uid != _USER_ID
            or user.login != _USER_LOGIN
            or not user.active
            or _COMPANY_ID not in user.company_ids.ids
            or not user.has_group("account.group_account_user")
        ):
            raise RuntimeError("the fixed ordinary accountant is unavailable")
        created = _exercise(env, args.alias, args.run_id, marker)
    except Exception as exc:  # noqa: BLE001 - rollback must cover every Odoo failure.
        failure = exc
    finally:
        cursor.rollback()
        cursor.close()

    if created is not None:
        plan_id, analytic_id, analytic_line_id, main_id, canceled_id, line_ids = created
        _verify_rollback(
            registry,
            plan_id=plan_id,
            analytic_id=analytic_id,
            analytic_line_id=analytic_line_id,
            budget_ids=(main_id, canceled_id),
            line_ids=line_ids,
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
