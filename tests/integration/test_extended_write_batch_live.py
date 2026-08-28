"""Guarded transactional smoke for the nine extended accounting writes.

The pytest process starts one real Odoo worker per isolated alias.  Each worker
creates its prerequisites, dispatches every capability twice, and rolls the whole
transaction back.  No fixture or generated accounting entry is committed.
"""

from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import os
import subprocess
import sys
import uuid
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

try:
    import pytest
except ModuleNotFoundError:
    if "--live-worker" not in sys.argv:
        raise
    pytest = None

_CONFIG_ENV = "ODOO_ACCOUNTING_CLI_V4_CONFIG"
_ALLOW_ENV = "ODACV4_ALLOW_WRITE_SMOKE"
_ALIASES = ("v4-dev", "v4-e2e")
_PHYSICAL_DATABASES = {
    "v4-dev": "odoo_cli_v4_dev",
    "v4-e2e": "odoo_cli_v4_e2e",
}
_COMPANY_ID = 1
_USER_ID = 5
_USER_LOGIN = "odacv4_g5_accountant"
_CAPABILITY_IDS = (
    "asset.cancel",
    "asset.dispose",
    "asset.pause",
    "deferred_expense.generate_entries",
    "deferred_revenue.generate_entries",
    "multicurrency.revaluation.generate_entries",
    "reconciliation.automatic.run",
    "period.transfer.run",
    "localization.china.period_transfer.run",
)
_PAGE_KEYS = {
    "user_id",
    "company_visible",
    "module_installed",
    "access_allowed",
    "idempotent_replay",
    "result",
}
_RESULT_KEYS = {
    "model",
    "id",
    "name",
    "state",
    "company_id",
    "move_type",
    "source_id",
    "line_ids",
    "partial_reconcile_ids",
    "full_reconcile_id",
    "reconciled",
}


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _enabled_runtime() -> tuple[Path, dict[str, Any]]:
    assert pytest is not None
    if os.environ.get(_ALLOW_ENV) != "1":
        pytest.skip(f"set {_ALLOW_ENV}=1 to authorize isolated write smoke")
    raw_path = os.environ.get(_CONFIG_ENV)
    if not raw_path:
        pytest.skip(f"{_CONFIG_ENV} is not configured")
    path = Path(raw_path)
    if not path.is_file():
        pytest.skip(f"{_CONFIG_ENV} does not name an existing file")

    document = json.loads(path.read_text(encoding="utf-8"))
    aliases = document.get("aliases")
    assert isinstance(aliases, dict)
    assert set(aliases) == set(_ALIASES)
    assert {
        alias: aliases[alias].get("database") for alias in _ALIASES
    } == _PHYSICAL_DATABASES
    assert all(
        aliases[alias].get("companies", {}).get(str(_COMPANY_ID))
        == [_USER_LOGIN]
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
    assert result == {
        "alias": alias,
        "capabilities": list(_CAPABILITY_IDS),
        "company_id": _COMPANY_ID,
        "database": _PHYSICAL_DATABASES[alias],
        "rollback_verified": True,
        "user_id": _USER_ID,
    }
    return result


if pytest is not None:

    @pytest.mark.integration
    def test_extended_write_batch_rolls_back_one_real_chain_per_alias() -> None:
        config_path, runtime = _enabled_runtime()
        run_id = uuid.uuid4()
        for alias in _ALIASES:
            _run_worker(alias, run_id, config_path, runtime)


def _worker_arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-worker", action="store_true", required=True)
    parser.add_argument("--odoo-config", type=Path, required=True)
    parser.add_argument("--odoo-source", type=Path, required=True)
    parser.add_argument("--alias", choices=_ALIASES, required=True)
    parser.add_argument("--database", choices=tuple(_PHYSICAL_DATABASES.values()), required=True)
    parser.add_argument("--run-id", type=uuid.UUID, required=True)
    args = parser.parse_args(argv)
    if args.database != _PHYSICAL_DATABASES[args.alias]:
        parser.error("alias and physical database do not match")
    if not args.odoo_config.is_absolute() or not args.odoo_config.is_file():
        parser.error("odoo-config must be an existing absolute file")
    if not args.odoo_source.is_absolute() or not args.odoo_source.is_dir():
        parser.error("odoo-source must be an existing absolute directory")
    return args


def _one(records: Any, label: str) -> Any:
    if len(records) != 1:
        raise RuntimeError(f"expected one {label}, got {len(records)}")
    return records


def _account(
    env: Any,
    company: Any,
    account_type: str,
    *,
    exclude_ids: set[int] | None = None,
) -> Any:
    domain: list[tuple[str, str, Any]] = [
        ("company_ids", "in", company.id),
        ("account_type", "=", account_type),
    ]
    if exclude_ids:
        domain.append(("id", "not in", sorted(exclude_ids)))
    return _one(
        env["account.account"].sudo().search(domain, limit=1, order="id"),
        f"{account_type} account",
    )


def _post_entry(
    env: Any,
    company: Any,
    journal: Any,
    entry_date: date,
    ref: str,
    line_values: list[dict[str, Any]],
) -> Any:
    from odoo import Command

    move = env["account.move"].sudo().with_company(company).create(
        {
            "company_id": company.id,
            "journal_id": journal.id,
            "date": entry_date,
            "move_type": "entry",
            "ref": ref,
            "line_ids": [Command.create(values) for values in line_values],
        }
    )
    move._post()
    if move.state != "posted":
        raise RuntimeError(f"fixture entry {ref} was not posted")
    return move


def _create_open_asset(
    env: Any,
    company: Any,
    journal: Any,
    asset_account: Any,
    depreciation_account: Any,
    expense_account: Any,
    *,
    name: str,
    acquisition_date: date,
    original_value: Decimal,
    method_number: int,
) -> Any:
    asset = env["account.asset"].sudo().with_company(company).create(
        {
            "name": name,
            "company_id": company.id,
            "acquisition_date": acquisition_date,
            "original_value": original_value,
            "salvage_value": Decimal(0),
            "account_asset_id": asset_account.id,
            "account_depreciation_id": depreciation_account.id,
            "account_depreciation_expense_id": expense_account.id,
            "journal_id": journal.id,
            "method": "linear",
            "method_number": method_number,
            "method_period": "12",
            "method_progress_factor": Decimal("0.3"),
            "prorata_computation_type": "none",
            "state": "open",
        }
    )
    if asset.state != "open":
        asset.write({"state": "open"})
    compute_board = getattr(asset, "compute_depreciation_board", None)
    if callable(compute_board):
        compute_board()
    asset.invalidate_recordset(["state", "depreciation_move_ids"])
    if asset.state != "open":
        raise RuntimeError(f"fixture asset {name} is not running")
    return asset


def _key(capability_id: str, parameters: dict[str, Any], company_id: int) -> str:
    if capability_id in {"asset.cancel", "asset.dispose"}:
        return f"{capability_id}:{parameters['asset_id']}"
    if capability_id == "asset.pause":
        return f"asset.pause:{parameters['asset_id']}:{parameters['date']}"
    if capability_id.startswith("deferred_"):
        return f"{capability_id}:{parameters['date_to']}"
    if capability_id == "multicurrency.revaluation.generate_entries":
        return f"{capability_id}:{parameters['date']}"
    if capability_id == "reconciliation.automatic.run":
        serialized = ",".join(str(item) for item in parameters["line_ids"])
        digest = hashlib.sha256(serialized.encode("ascii")).hexdigest()[:32]
        return f"reconciliation.automatic.run:{digest}"
    if capability_id == "period.transfer.run":
        return (
            f"period.transfer.run:{parameters['transfer_model_id']}:"
            f"{parameters['run_date']}"
        )
    return (
        f"localization.china.period_transfer.run:{company_id}:"
        f"{parameters['run_date']}"
    )


def _assert_dispatch_page(page: dict[str, Any], *, replay: bool) -> None:
    assert set(page) == _PAGE_KEYS
    assert page["user_id"] == _USER_ID
    assert page["company_visible"] is True
    assert page["module_installed"] is True
    assert page["access_allowed"] is True
    assert page["idempotent_replay"] is replay
    result = page["result"]
    assert isinstance(result, dict) and set(result) == _RESULT_KEYS
    assert result["company_id"] == _COMPANY_ID
    assert result["line_ids"] == sorted(set(result["line_ids"]))
    assert result["partial_reconcile_ids"] == sorted(
        set(result["partial_reconcile_ids"])
    )


class _RuntimePort:
    def __init__(self, env: Any) -> None:
        self.env = env
        self.pages: list[dict[str, Any]] = []

    @property
    def user_id(self) -> int:
        return self.env.uid

    def execute(self, **payload: Any) -> dict[str, Any]:
        from odoo_accounting_cli_v4.bridge.core_writes_runtime import dispatch
        from odoo_accounting_cli_v4.bridge.runtime import RuntimeFailure

        page = dispatch(self.env, payload, payload["company_id"], RuntimeFailure)
        self.pages.append(page)
        return page


def _dispatch_twice(
    env: Any,
    alias: str,
    capability_id: str,
    parameters: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    from odoo_accounting_cli_v4.capabilities.core_writes import execute_core_write

    request = {
        "schema_version": "v1",
        "request_id": "7bc39413-0d69-4092-9319-795d33f3167c",
        "context": {
            "database": alias,
            "company_id": _COMPANY_ID,
            "user_login": _USER_LOGIN,
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": parameters,
    }
    key = _key(capability_id, parameters, _COMPANY_ID)
    port = _RuntimePort(env)
    first = execute_core_write(port, capability_id, request, key, capability_id)
    second = execute_core_write(port, capability_id, request, key, capability_id)
    assert len(port.pages) == 2
    _assert_dispatch_page(port.pages[0], replay=False)
    _assert_dispatch_page(port.pages[1], replay=True)
    assert first["idempotent_replay"] is False
    assert second["idempotent_replay"] is True
    assert first["result"] == second["result"]
    return first, second


def _fixture_and_parameters(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
) -> tuple[dict[str, dict[str, Any]], dict[str, set[int]], dict[str, int | bool]]:
    from odoo import fields

    company = _one(
        env["res.company"].sudo().search([("id", "=", _COMPANY_ID)], limit=2),
        "company",
    )
    if company.account_fiscal_country_id.code != "CN":
        raise RuntimeError("company 1 is not configured for China accounting")
    journal = env["account.journal"].sudo().search(
        [
            ("company_id", "=", company.id),
            ("type", "=", "general"),
            ("code", "=", "MISC"),
        ],
        limit=1,
    ) or env["account.journal"].sudo().search(
        [("company_id", "=", company.id), ("type", "=", "general")],
        limit=1,
        order="id",
    )
    journal = _one(journal, "general journal")
    partner = _one(
        env["res.partner"].sudo().search(
            [("company_id", "in", [False, company.id]), ("active", "=", True)],
            limit=1,
            order="id",
        ),
        "partner",
    )
    expense = _account(env, company, "expense")
    income = _account(env, company, "income")
    current_asset = _account(env, company, "asset_current")
    current_liability = _account(env, company, "liability_current")
    receivable = _account(env, company, "asset_receivable")
    if not receivable.reconcile:
        raise RuntimeError("the selected receivable account is not reconcilable")
    fixed_accounts = env["account.account"].sudo().search(
        [
            ("company_ids", "in", company.id),
            ("account_type", "=", "asset_fixed"),
        ],
        limit=2,
        order="id",
    )
    if len(fixed_accounts) != 2:
        raise RuntimeError("two fixed-asset accounts are required")

    today = fields.Date.today()
    month_start = today.replace(day=1)
    month_end = today.replace(day=calendar.monthrange(today.year, today.month)[1])
    deferred_end_seed = month_end + timedelta(days=32)
    deferred_end = deferred_end_seed.replace(
        day=calendar.monthrange(deferred_end_seed.year, deferred_end_seed.month)[1]
    )
    previous_year = month_start.replace(year=month_start.year - 1)
    marker = f"ODACV4-{run_id}-{alias}"
    created: dict[str, set[int]] = defaultdict(set)

    assets = {
        "cancel": _create_open_asset(
            env,
            company,
            journal,
            fixed_accounts[0],
            fixed_accounts[1],
            expense,
            name=f"{marker}-cancel",
            acquisition_date=previous_year,
            original_value=Decimal(0),
            method_number=1,
        ),
        "dispose": _create_open_asset(
            env,
            company,
            journal,
            fixed_accounts[0],
            fixed_accounts[1],
            expense,
            name=f"{marker}-dispose",
            acquisition_date=previous_year,
            original_value=Decimal(0),
            method_number=1,
        ),
        "pause": _create_open_asset(
            env,
            company,
            journal,
            fixed_accounts[0],
            fixed_accounts[1],
            expense,
            name=f"{marker}-pause",
            acquisition_date=month_start,
            original_value=Decimal(120),
            method_number=1,
        ),
    }
    created["account.asset"].update(asset.id for asset in assets.values())

    original_configuration = {
        "deferred_expense_journal_id": company.deferred_expense_journal_id.id,
        "deferred_expense_account_id": company.deferred_expense_account_id.id,
        "deferred_revenue_journal_id": company.deferred_revenue_journal_id.id,
        "deferred_revenue_account_id": company.deferred_revenue_account_id.id,
    }
    company.sudo().write(
        {
            "deferred_expense_journal_id": journal.id,
            "deferred_expense_account_id": current_asset.id,
            "deferred_revenue_journal_id": journal.id,
            "deferred_revenue_account_id": current_liability.id,
        }
    )
    deferred_fields = {"deferred_start_date", "deferred_end_date"}
    if not deferred_fields <= set(env["account.move.line"]._fields):
        raise RuntimeError("deferred date fields are unavailable")

    expense_move = _post_entry(
        env,
        company,
        journal,
        month_start,
        f"{marker}-deferred-expense",
        [
            {
                "name": f"{marker}-deferred-expense",
                "account_id": expense.id,
                "debit": Decimal(120),
                "credit": Decimal(0),
            },
            {
                "name": f"{marker}-deferred-expense-counterpart",
                "account_id": current_asset.id,
                "debit": Decimal(0),
                "credit": Decimal(120),
            },
        ],
    )
    revenue_move = _post_entry(
        env,
        company,
        journal,
        month_start,
        f"{marker}-deferred-revenue",
        [
            {
                "name": f"{marker}-deferred-revenue",
                "account_id": income.id,
                "debit": Decimal(0),
                "credit": Decimal(120),
            },
            {
                "name": f"{marker}-deferred-revenue-counterpart",
                "account_id": current_asset.id,
                "debit": Decimal(120),
                "credit": Decimal(0),
            },
        ],
    )
    _one(
        expense_move.line_ids.filtered(
            lambda line: line.name == f"{marker}-deferred-expense"
        ),
        "deferred-expense source line",
    ).write(
        {
            "deferred_start_date": month_start,
            "deferred_end_date": deferred_end,
        }
    )
    _one(
        revenue_move.line_ids.filtered(
            lambda line: line.name == f"{marker}-deferred-revenue"
        ),
        "deferred-revenue source line",
    ).write(
        {
            "deferred_start_date": month_start,
            "deferred_end_date": deferred_end,
        }
    )
    created["account.move"].update((expense_move.id, revenue_move.id))
    created["account.move.line"].update((expense_move | revenue_move).line_ids.ids)

    foreign_currency = _one(
        env["res.currency"].sudo().search(
            [("id", "!=", company.currency_id.id), ("active", "=", True)],
            limit=1,
            order="id",
        ),
        "active foreign currency",
    )
    converted = Decimal(
        str(
            foreign_currency._convert(
                1.0, company.currency_id, company, month_end
            )
        )
    )
    foreign_balance = abs(converted) + Decimal(37)
    revaluation_move = _post_entry(
        env,
        company,
        journal,
        month_start,
        f"{marker}-revaluation",
        [
            {
                "name": f"{marker}-foreign-receivable",
                "account_id": receivable.id,
                "partner_id": partner.id,
                "currency_id": foreign_currency.id,
                "amount_currency": Decimal(1),
                "debit": foreign_balance,
                "credit": Decimal(0),
            },
            {
                "name": f"{marker}-foreign-counterpart",
                "account_id": current_asset.id,
                "debit": Decimal(0),
                "credit": foreign_balance,
            },
        ],
    )
    created["account.move"].add(revaluation_move.id)
    created["account.move.line"].update(revaluation_move.line_ids.ids)

    reconciliation_move = _post_entry(
        env,
        company,
        journal,
        month_start,
        f"{marker}-automatic-reconciliation",
        [
            {
                "name": f"{marker}-automatic-debit",
                "account_id": receivable.id,
                "partner_id": partner.id,
                "debit": Decimal(30),
                "credit": Decimal(0),
            },
            {
                "name": f"{marker}-automatic-credit",
                "account_id": receivable.id,
                "partner_id": partner.id,
                "debit": Decimal(0),
                "credit": Decimal(30),
            },
        ],
    )
    reconciliation_lines = reconciliation_move.line_ids.filtered(
        lambda line: line.account_id == receivable
    )
    if len(reconciliation_lines) != 2:
        raise RuntimeError("automatic-reconciliation fixture did not keep two lines")
    created["account.move"].add(reconciliation_move.id)
    created["account.move.line"].update(reconciliation_move.line_ids.ids)

    transfer_model = env.ref(
        "l10n_cn_reports.account_transfer_model_jz", raise_if_not_found=False
    )
    if (
        not transfer_model
        or transfer_model._name != "account.transfer.model"
        or transfer_model.company_id != company
        or not transfer_model.active
        or not transfer_model.account_ids
        or not transfer_model.line_ids
    ):
        raise RuntimeError("China transfer model is unavailable or incomplete")
    if transfer_model.date_start > today or (
        transfer_model.date_stop and transfer_model.date_stop < today
    ):
        raise RuntimeError("China transfer model does not cover the server date")
    transfer_source = transfer_model.account_ids[0]
    transfer_counterpart = _account(
        env,
        company,
        "asset_current",
        exclude_ids=set(transfer_model.account_ids.ids),
    )
    source_is_credit = transfer_source.account_type in {"income", "income_other"}
    transfer_move = _post_entry(
        env,
        company,
        journal,
        today,
        f"{marker}-period-transfer",
        [
            {
                "name": f"{marker}-transfer-source",
                "account_id": transfer_source.id,
                "debit": Decimal(0) if source_is_credit else Decimal(13),
                "credit": Decimal(13) if source_is_credit else Decimal(0),
            },
            {
                "name": f"{marker}-transfer-counterpart",
                "account_id": transfer_counterpart.id,
                "debit": Decimal(13) if source_is_credit else Decimal(0),
                "credit": Decimal(0) if source_is_credit else Decimal(13),
            },
        ],
    )
    created["account.move"].add(transfer_move.id)
    created["account.move.line"].update(transfer_move.line_ids.ids)

    parameters = {
        "asset.cancel": {"asset_id": assets["cancel"].id},
        "asset.dispose": {
            "asset_id": assets["dispose"].id,
            "date": month_end.isoformat(),
            "note": f"{marker}-dispose",
        },
        "asset.pause": {
            "asset_id": assets["pause"].id,
            "date": month_end.isoformat(),
            "note": f"{marker}-pause",
        },
        "deferred_expense.generate_entries": {"date_to": month_end.isoformat()},
        "deferred_revenue.generate_entries": {"date_to": month_end.isoformat()},
        "multicurrency.revaluation.generate_entries": {
            "date": month_end.isoformat(),
            "reversal_date": (month_end + timedelta(days=1)).isoformat(),
            "journal_id": journal.id,
            "expense_provision_account_id": expense.id,
            "income_provision_account_id": income.id,
        },
        "reconciliation.automatic.run": {
            "line_ids": sorted(reconciliation_lines.ids)
        },
        "period.transfer.run": {
            "transfer_model_id": transfer_model.id,
            "run_date": today.isoformat(),
        },
        "localization.china.period_transfer.run": {
            "run_date": today.isoformat()
        },
    }
    return parameters, created, original_configuration


def _record_results_for_rollback(
    capability_id: str,
    page: dict[str, Any],
    created: dict[str, set[int]],
) -> None:
    result = page["result"]
    if result["model"] == "account.asset" and result["id"]:
        created["account.asset"].add(result["id"])
    if result["model"] == "account.move" and result["id"]:
        created["account.move"].add(result["id"])
        created["account.move.line"].update(result["line_ids"])
        if capability_id in {
            "deferred_expense.generate_entries",
            "deferred_revenue.generate_entries",
            "multicurrency.revaluation.generate_entries",
        }:
            created["account.move"].add(result["source_id"])
    if capability_id == "reconciliation.automatic.run":
        created["account.move.line"].update(result["line_ids"])


def _verify_rollback(
    registry: Any,
    created: dict[str, set[int]],
    original_configuration: dict[str, int | bool],
) -> None:
    from odoo import SUPERUSER_ID, api

    cursor = registry.cursor()
    try:
        cursor.execute("SET TRANSACTION READ ONLY")
        env = api.Environment(cursor, SUPERUSER_ID, {"allowed_company_ids": [_COMPANY_ID]})
        for model_name, ids in created.items():
            if ids and env[model_name].browse(sorted(ids)).exists():
                raise RuntimeError(f"rollback left {model_name} records behind")
        company = env["res.company"].browse(_COMPANY_ID)
        restored = {
            "deferred_expense_journal_id": company.deferred_expense_journal_id.id,
            "deferred_expense_account_id": company.deferred_expense_account_id.id,
            "deferred_revenue_journal_id": company.deferred_revenue_journal_id.id,
            "deferred_revenue_account_id": company.deferred_revenue_account_id.id,
        }
        if restored != original_configuration:
            raise RuntimeError("rollback did not restore deferred-account configuration")
    finally:
        cursor.rollback()
        cursor.close()


def _live_worker(argv: list[str] | None = None) -> int:
    args = _worker_arguments(argv)
    root = _project_root()
    sys.path.insert(0, str(args.odoo_source.resolve(strict=True)))
    sys.path.insert(0, str((root / "src").resolve(strict=True)))

    from odoo import api
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
    created: dict[str, set[int]] = defaultdict(set)
    original_configuration: dict[str, int | bool] = {}
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
            or user.id != _USER_ID
            or not user.active
            or user.login != _USER_LOGIN
            or _COMPANY_ID not in user.company_ids.ids
        ):
            raise RuntimeError("the fixed business user is unavailable")

        parameters, fixture_records, original_configuration = _fixture_and_parameters(
            env, args.alias, args.run_id
        )
        for model_name, ids in fixture_records.items():
            created[model_name].update(ids)
        if tuple(parameters) != _CAPABILITY_IDS:
            raise RuntimeError("the live fixture does not cover the frozen batch")

        for capability_id in _CAPABILITY_IDS:
            first, _ = _dispatch_twice(
                env, args.alias, capability_id, parameters[capability_id]
            )
            _record_results_for_rollback(capability_id, first, created)
    finally:
        cursor.rollback()
        cursor.close()

    _verify_rollback(registry, created, original_configuration)
    sys.stdout.write(
        json.dumps(
            {
                "alias": args.alias,
                "capabilities": list(_CAPABILITY_IDS),
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
