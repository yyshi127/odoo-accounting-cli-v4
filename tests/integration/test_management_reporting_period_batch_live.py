"""Shared rollback smoke for eight management-reporting and period reads."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    import pytest
except ModuleNotFoundError:
    if "--live-worker" not in sys.argv:
        raise
    pytest = None

_CONFIG_ENV = "ODOO_ACCOUNTING_CLI_V4_CONFIG"
_ALLOW_ENV = "ODACV4_ALLOW_MANAGEMENT_REPORTING_PERIOD_SMOKE"
_ALIASES = ("v4-dev", "v4-e2e")
_PHYSICAL_DATABASES = {
    "v4-dev": "odoo_cli_v4_dev",
    "v4-e2e": "odoo_cli_v4_e2e",
}
_COMPANY_ID = 1
_USER_LOGIN = "odacv4_g5_accountant"
_CAPABILITY_IDS = (
    "report.customer_statement",
    "report.followup",
    "invoice.analysis.search",
    "invoice.analysis.summary",
    "company.lock_dates.inspect",
    "company.fiscal_year.resolve",
    "fiscal_year.search",
    "fiscal_year.get",
)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _enabled_runtime(alias: str) -> tuple[Path, dict[str, Any]]:
    assert pytest is not None
    if os.environ.get(_ALLOW_ENV) != "1":
        pytest.skip(f"set {_ALLOW_ENV}=1 to authorize rollback fixture setup")
    raw_path = os.environ.get(_CONFIG_ENV)
    if not raw_path:
        pytest.skip(f"{_CONFIG_ENV} is not configured")
    path = Path(raw_path)
    if not path.is_file():
        pytest.skip(f"{_CONFIG_ENV} does not name an existing file")
    document = json.loads(path.read_text(encoding="utf-8"))
    entry = document.get("aliases", {}).get(alias)
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
        max(timeout, 300),
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
    assert result == {
        "alias": alias,
        "capabilities": list(_CAPABILITY_IDS),
        "company_id": _COMPANY_ID,
        "database": _PHYSICAL_DATABASES[alias],
        "positive_results": len(_CAPABILITY_IDS),
        "rollback_verified": True,
        "user_id": result["user_id"],
    }
    assert isinstance(result["user_id"], int) and result["user_id"] > 0
    return result


if pytest is not None:

    @pytest.mark.integration
    @pytest.mark.parametrize("alias", _ALIASES)
    def test_management_reporting_period_batch_is_live_and_rolls_back(
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


class _DirectClient:
    def __init__(self, env: Any) -> None:
        self.env = env

    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        from odoo_accounting_cli_v4.bridge.runtime import _dispatch

        return _dispatch(self.env, action, payload, _COMPANY_ID)


def _request(
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "request_id": str(uuid.uuid5(run_id, capability_id)),
        "context": {
            "database": alias,
            "company_id": _COMPANY_ID,
            "user_login": _USER_LOGIN,
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": parameters,
    }


def _invoke_capability(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    from odoo_accounting_cli_v4.bridge.financial_reports import (
        OdooFinancialReportPort,
    )
    from odoo_accounting_cli_v4.bridge.invoice_analysis import (
        OdooInvoiceAnalysisPort,
    )
    from odoo_accounting_cli_v4.bridge.period_context import OdooPeriodContextPort
    from odoo_accounting_cli_v4.capabilities.financial_reports import (
        read_typed_financial_report,
    )
    from odoo_accounting_cli_v4.capabilities.invoice_analysis import (
        read_invoice_analysis,
    )
    from odoo_accounting_cli_v4.capabilities.period_context import (
        read_period_context,
    )

    client = _DirectClient(env)
    request = _request(alias, run_id, capability_id, parameters)
    if capability_id.startswith("report."):
        port = OdooFinancialReportPort(client, capability_id)
        data = read_typed_financial_report(capability_id, port, request)
    elif capability_id.startswith("invoice.analysis."):
        port = OdooInvoiceAnalysisPort(client)
        data = read_invoice_analysis(port, capability_id, request)
    else:
        port = OdooPeriodContextPort(client)
        data = read_period_context(capability_id, port, request)
    if port.user_id != env.uid or not isinstance(data, dict):
        raise RuntimeError(
            f"{capability_id} returned an invalid public capability result"
        )
    return data


def _setup_fiscal_year(admin_env: Any, marker: str) -> int:
    record = admin_env["account.fiscal.year"].create(
        {
            "name": marker,
            "company_id": _COMPANY_ID,
            "date_from": "2097-01-01",
            "date_to": "2097-12-31",
        }
    )
    admin_env.flush_all()
    return record.id


def _open_receivable_partner_id(env: Any) -> int:
    line = env["account.move.line"].search(
        [
            ("company_id", "=", _COMPANY_ID),
            ("parent_state", "=", "posted"),
            ("account_id.account_type", "=", "asset_receivable"),
            ("partner_id", "!=", False),
            ("reconciled", "=", False),
        ],
        order="id",
        limit=1,
    )
    if not line or not line.partner_id:
        raise RuntimeError("no open receivable partner is available")
    return line.partner_id.id


def _exercise_batch(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    fiscal_year_id: int,
) -> None:
    partner_id = _open_receivable_partner_id(env)
    cases = (
        (
            "report.customer_statement",
            {
                "partner_id": partner_id,
                "date_from": "2000-01-01",
                "date_to": "2099-12-31",
                "limit": 1000,
            },
        ),
        (
            "report.followup",
            {
                "partner_id": partner_id,
                "as_of": datetime.now(UTC).date().isoformat(),
                "limit": 1000,
            },
        ),
        (
            "invoice.analysis.search",
            {
                "date_from": "2000-01-01",
                "date_to": "2099-12-31",
                "limit": 1000,
            },
        ),
        (
            "invoice.analysis.summary",
            {
                "date_from": "2000-01-01",
                "date_to": "2099-12-31",
                "group_by": "move_type",
            },
        ),
        ("company.lock_dates.inspect", {}),
        ("company.fiscal_year.resolve", {"date": "2097-06-30"}),
        (
            "fiscal_year.search",
            {"contains_date": "2097-06-30", "limit": 100},
        ),
        ("fiscal_year.get", {"fiscal_year_id": fiscal_year_id}),
    )
    for capability_id, parameters in cases:
        data = _invoke_capability(env, alias, run_id, capability_id, parameters)
        if (
            capability_id
            in {
                "report.customer_statement",
                "report.followup",
            }
            and not data["lines"]
        ):
            raise RuntimeError(f"{capability_id} returned no live lines")
        if capability_id == "invoice.analysis.search" and not data["items"]:
            raise RuntimeError("invoice.analysis.search returned no live rows")
        if capability_id == "invoice.analysis.summary" and not data["groups"]:
            raise RuntimeError("invoice.analysis.summary returned no live groups")
        if (
            capability_id == "company.fiscal_year.resolve"
            and data["fiscal_year"]["id"] != fiscal_year_id
        ):
            raise RuntimeError("fiscal-year resolution missed the fixture")
        if capability_id == "fiscal_year.search" and [
            item["id"] for item in data["items"]
        ] != [fiscal_year_id]:
            raise RuntimeError("fiscal-year search missed the fixture")
        if capability_id == "fiscal_year.get" and data["id"] != fiscal_year_id:
            raise RuntimeError("fiscal-year get missed the fixture")


def _verify_rollback(registry: Any, marker: str) -> None:
    from odoo import SUPERUSER_ID, api

    cursor = registry.cursor()
    try:
        env = api.Environment(
            cursor,
            SUPERUSER_ID,
            {"allowed_company_ids": [_COMPANY_ID], "active_test": False},
        )
        remaining = env["account.fiscal.year"].search_count(
            [("name", "=", marker), ("company_id", "=", _COMPANY_ID)],
            limit=1,
        )
        if remaining:
            raise RuntimeError("the fiscal-year fixture survived rollback")
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
    marker = f"ODACV4-MRP-{args.alias}-{args.run_id.hex}"
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
            raise RuntimeError("the configured company or user is unavailable")
        fiscal_year_id = _setup_fiscal_year(admin_env, marker)
        user_id = user.id
        business_env = api.Environment(cursor, user_id, context)
        _exercise_batch(
            business_env,
            args.alias,
            args.run_id,
            fiscal_year_id,
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
                "positive_results": len(_CAPABILITY_IDS),
                "rollback_verified": True,
                "user_id": user_id,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_live_worker())
