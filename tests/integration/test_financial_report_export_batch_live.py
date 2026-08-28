"""One shared read-only smoke for ten fixed financial-report exports."""

from __future__ import annotations

import argparse
import base64
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
_ALLOW_ENV = "ODACV4_ALLOW_FINANCIAL_REPORT_EXPORT_SMOKE"
_ALIASES = ("v4-dev", "v4-e2e")
_DATABASES = {
    "v4-dev": "odoo_cli_v4_dev",
    "v4-e2e": "odoo_cli_v4_e2e",
}
_COMPANY_ID = 1
_USER_LOGIN = "odacv4_g5_accountant"
_CAPABILITIES = {
    "report.trial_balance.export": "range",
    "report.balance_sheet.export": "single",
    "report.profit_and_loss.export": "range",
    "report.cash_flow.export": "range",
    "report.tax.export": "range",
    "report.general_ledger.export": "range",
    "report.partner_ledger.export": "range",
    "report.aged_receivable.export": "single",
    "report.aged_payable.export": "single",
    "report.executive_summary.export": "range",
}


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _enabled_runtime() -> tuple[Path, dict[str, Any]]:
    assert pytest is not None
    if os.environ.get(_ALLOW_ENV) != "1":
        pytest.skip(f"set {_ALLOW_ENV}=1 to authorize the live read-only smoke")
    raw_path = os.environ.get(_CONFIG_ENV)
    if not raw_path:
        pytest.skip(f"{_CONFIG_ENV} is not configured")
    path = Path(raw_path)
    if not path.is_file():
        pytest.skip(f"{_CONFIG_ENV} does not name an existing file")
    document = json.loads(path.read_text(encoding="utf-8"))
    for alias, database in _DATABASES.items():
        entry = document.get("aliases", {}).get(alias)
        assert isinstance(entry, dict) and entry.get("database") == database
        users = entry.get("companies", {}).get(str(_COMPANY_ID))
        assert isinstance(users, list) and _USER_LOGIN in users
    return path, document


def _worker_command(
    alias: str, config_path: Path, runtime: dict[str, Any]
) -> tuple[list[str], int]:
    bridge = runtime.get("bridge")
    assert isinstance(bridge, dict)
    argv = bridge.get("argv")
    timeout = bridge.get("timeout_seconds")
    assert isinstance(argv, list) and len(argv) == 8
    assert argv[2::2] == ["--runtime-config", "--odoo-config", "--odoo-source"]
    assert isinstance(timeout, int) and not isinstance(timeout, bool) and timeout > 0
    executable = Path(argv[0])
    configured_runtime = Path(argv[3])
    odoo_config = Path(argv[5])
    odoo_source = Path(argv[7])
    assert executable.is_absolute() and executable.is_file()
    assert configured_runtime.resolve(strict=True) == config_path.resolve(strict=True)
    assert odoo_config.is_absolute() and odoo_config.is_file()
    assert odoo_source.is_absolute() and odoo_source.is_dir()
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
        ],
        max(timeout, 600),
    )


def _run_worker(
    alias: str, config_path: Path, runtime: dict[str, Any]
) -> dict[str, Any]:
    command, timeout = _worker_command(alias, config_path, runtime)
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
        "capabilities": list(_CAPABILITIES),
        "company_id": _COMPANY_ID,
        "database": _DATABASES[alias],
        "exports": len(_CAPABILITIES) * 2,
        "formats": ["pdf", "xlsx"],
        "read_only_transaction": True,
        "user_id": result["user_id"],
    }
    assert isinstance(result["user_id"], int) and result["user_id"] > 0
    return result


if pytest is not None:

    @pytest.mark.integration
    def test_financial_report_export_batch_is_live_and_read_only() -> None:
        config_path, runtime = _enabled_runtime()
        results = [_run_worker(alias, config_path, runtime) for alias in _ALIASES]
        assert [item["alias"] for item in results] == list(_ALIASES)


def _worker_arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-worker", action="store_true", required=True)
    parser.add_argument("--odoo-config", type=Path, required=True)
    parser.add_argument("--odoo-source", type=Path, required=True)
    parser.add_argument("--alias", choices=_ALIASES, required=True)
    parser.add_argument("--database", choices=tuple(_DATABASES.values()), required=True)
    args = parser.parse_args(argv)
    if args.database != _DATABASES[args.alias]:
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


def _parameters(mode: str, export_format: str) -> dict[str, str]:
    if mode == "single":
        return {"as_of": "2025-12-31", "format": export_format}
    return {
        "date_from": "2025-01-01",
        "date_to": "2025-12-31",
        "format": export_format,
    }


def _request(
    alias: str, capability_id: str, export_format: str, mode: str
) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "request_id": str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"odacv4:{alias}:{capability_id}:{export_format}",
            )
        ),
        "context": {
            "database": alias,
            "company_id": _COMPANY_ID,
            "user_login": _USER_LOGIN,
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": _parameters(mode, export_format),
    }


def _exercise_batch(env: Any, alias: str) -> None:
    from odoo_accounting_cli_v4.bridge.financial_reports import (
        OdooFinancialReportExportPort,
    )
    from odoo_accounting_cli_v4.capabilities.financial_reports import (
        export_financial_report,
    )

    client = _DirectClient(env)
    for capability_id, mode in _CAPABILITIES.items():
        for export_format in ("pdf", "xlsx"):
            port = OdooFinancialReportExportPort(client)
            data = export_financial_report(
                capability_id,
                port,
                _request(alias, capability_id, export_format, mode),
            )
            content = base64.b64decode(data["content_base64"], validate=True)
            expected_magic = b"%PDF-" if export_format == "pdf" else b"PK\x03\x04"
            if (
                port.user_id != env.uid
                or data["byte_count"] != len(content)
                or data["sha256"] != hashlib.sha256(content).hexdigest()
                or not content.startswith(expected_magic)
            ):
                raise RuntimeError(f"{capability_id} returned an invalid live export")


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
    user_id: int | None = None
    try:
        cursor.execute("SET TRANSACTION READ ONLY")
        context = {
            "allowed_company_ids": [_COMPANY_ID],
            "active_test": True,
            "lang": "en_US",
            "tz": "Asia/Shanghai",
        }
        root_env = api.Environment(cursor, SUPERUSER_ID, context)
        company = root_env["res.company"].browse(_COMPANY_ID).exists()
        user = (
            root_env["res.users"]
            .with_context(active_test=False)
            .search([("login", "=", _USER_LOGIN)], limit=1)
        )
        if not company or not user or not user.active or company not in user.company_ids:
            raise RuntimeError("the configured company or user is unavailable")
        user_id = user.id
        _exercise_batch(api.Environment(cursor, user_id, context), args.alias)
    finally:
        cursor.rollback()
        cursor.close()

    sys.stdout.write(
        json.dumps(
            {
                "alias": args.alias,
                "capabilities": list(_CAPABILITIES),
                "company_id": _COMPANY_ID,
                "database": args.database,
                "exports": len(_CAPABILITIES) * 2,
                "formats": ["pdf", "xlsx"],
                "read_only_transaction": True,
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
