"""Transactional dual-database smoke for accounting rules and fiscal years."""

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
_ALLOW_ENV = "ODACV4_ALLOW_ACCOUNTING_RULES_FISCAL_YEAR_WRITE_SMOKE"
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
    "fiscal_year.create",
    "fiscal_year.update",
    "analytic.applicability.create",
    "analytic.applicability.update",
    "analytic.distribution_model.create",
    "analytic.distribution_model.update",
    "fiscal_position.account_mapping.list",
    "fiscal_position.tax_mapping.list",
)
_CREATED_MODELS = {
    "fiscal_year": "account.fiscal.year",
    "applicability": "account.analytic.applicability",
    "analytic_account": "account.analytic.account",
    "distribution_model": "account.analytic.distribution.model",
    "tax_group": "account.tax.group",
    "source_tax": "account.tax",
    "destination_tax_1": "account.tax",
    "destination_tax_2": "account.tax",
    "fiscal_position": "account.fiscal.position",
    "empty_fiscal_position": "account.fiscal.position",
    "account_mapping": "account.fiscal.position.account",
}


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
    def test_accounting_rules_and_fiscal_year_roll_back_per_alias() -> None:
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


class _DirectClient:
    def __init__(self, env: Any) -> None:
        self.env = env

    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        from odoo_accounting_cli_v4.bridge.runtime import _dispatch

        return _dispatch(self.env, action, payload, _COMPANY_ID)


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
    replay = execute_core_write(port, capability_id, request, key, capability_id)
    if replay["idempotent_replay"] is not True or replay["result"] != first["result"]:
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


def _read_fiscal_year(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    fiscal_year_id: int,
) -> dict[str, Any]:
    from odoo_accounting_cli_v4.bridge.period_context import OdooPeriodContextPort
    from odoo_accounting_cli_v4.capabilities.period_context import read_period_context

    port = OdooPeriodContextPort(_DirectClient(env))
    data = read_period_context(
        "fiscal_year.get",
        port,
        _request(
            alias,
            run_id,
            "fiscal_year.get",
            {"fiscal_year_id": fiscal_year_id},
        ),
    )
    if port.user_id != env.uid:
        raise RuntimeError("fiscal_year.get ran as the wrong user")
    return data


def _assert_result(
    result: dict[str, Any], model: str, record_id: int, state: str = "active"
) -> None:
    if (
        result["model"] != model
        or result["id"] != record_id
        or result["state"] != state
    ):
        raise RuntimeError(f"unexpected {model} result: {result}")


def _available_fiscal_year(env: Any) -> tuple[str, str]:
    model = env["account.fiscal.year"].with_company(_COMPANY_ID)
    for year in range(2200, 2300):
        date_from = f"{year}-01-01"
        date_to = f"{year}-12-31"
        overlaps = model.search_count(
            [
                ("company_id", "=", _COMPANY_ID),
                ("date_from", "<=", date_to),
                ("date_to", ">=", date_from),
            ],
            limit=1,
        )
        if not overlaps:
            return date_from, date_to
    raise RuntimeError("no unused future fiscal-year range is available")


def _exercise_writes(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    marker: str,
    created: dict[str, int | None],
) -> None:
    date_from, date_to = _available_fiscal_year(env)
    fiscal_result = _write(
        env,
        alias,
        run_id,
        "fiscal_year.create",
        {"name": f"{marker} FY", "date_from": date_from, "date_to": date_to},
    )
    fiscal_year_id = fiscal_result["id"]
    created["fiscal_year"] = fiscal_year_id
    _assert_result(fiscal_result, "account.fiscal.year", fiscal_year_id)
    updated_fiscal_name = f"{marker} FY Updated"
    _assert_result(
        _write(
            env,
            alias,
            run_id,
            "fiscal_year.update",
            {"id": fiscal_year_id, "changes": {"name": updated_fiscal_name}},
        ),
        "account.fiscal.year",
        fiscal_year_id,
    )
    fiscal_year = env["account.fiscal.year"].browse(fiscal_year_id)
    fiscal_year.invalidate_recordset(["name", "date_from", "date_to", "company_id"])
    if (
        fiscal_year.name != updated_fiscal_name
        or str(fiscal_year.date_from) != date_from
        or str(fiscal_year.date_to) != date_to
        or fiscal_year.company_id.id != _COMPANY_ID
    ):
        raise RuntimeError("the fiscal-year write was not readable through Odoo ORM")
    fiscal_year_data = _read_fiscal_year(env, alias, run_id, fiscal_year_id)
    if fiscal_year_data != {
        "id": fiscal_year_id,
        "name": updated_fiscal_name,
        "company_id": _COMPANY_ID,
        "date_from": date_from,
        "date_to": date_to,
    }:
        raise RuntimeError(f"fiscal_year.get mismatched: {fiscal_year_data}")

    plan = env["account.analytic.plan"].search(
        [("parent_id", "=", False)], order="id", limit=1
    )
    if not plan:
        raise RuntimeError("the isolated database has no root analytic plan")
    selector = f"V4{run_id.hex[:20]}"
    applicability_result = _write(
        env,
        alias,
        run_id,
        "analytic.applicability.create",
        {
            "plan_id": plan.id,
            "business_domain": "invoice",
            "applicability": "optional",
            "account_prefix": selector,
            "product_category_id": None,
        },
    )
    applicability_id = applicability_result["id"]
    created["applicability"] = applicability_id
    _assert_result(
        applicability_result, "account.analytic.applicability", applicability_id
    )
    _assert_result(
        _write(
            env,
            alias,
            run_id,
            "analytic.applicability.update",
            {
                "id": applicability_id,
                "changes": {"applicability": "mandatory"},
            },
        ),
        "account.analytic.applicability",
        applicability_id,
    )
    applicability = _read(
        env,
        alias,
        run_id,
        "analytic.applicability.get",
        {"applicability_id": applicability_id},
    )
    if (
        applicability["id"] != applicability_id
        or applicability["plan"] is None
        or applicability["plan"]["id"] != plan.id
        or applicability["business_domain"] != "invoice"
        or applicability["applicability"] != "mandatory"
        or applicability["account_prefix"] != selector
        or applicability["company_id"] != _COMPANY_ID
    ):
        raise RuntimeError(f"analytic.applicability.get mismatched: {applicability}")

    analytic_account = env["account.analytic.account"].create(
        {
            "name": f"{marker} Analytic Account",
            "code": f"V4{run_id.hex[:24]}",
            "active": True,
            "plan_id": plan.id,
            "company_id": _COMPANY_ID,
        }
    )
    created["analytic_account"] = analytic_account.id
    distribution_result = _write(
        env,
        alias,
        run_id,
        "analytic.distribution_model.create",
        {
            "sequence": 91,
            "account_prefix": f"{selector}D",
            "partner_id": None,
            "partner_category_id": None,
            "product_id": None,
            "product_category_id": None,
            "analytic_distribution": {str(analytic_account.id): "100"},
        },
    )
    distribution_model_id = distribution_result["id"]
    created["distribution_model"] = distribution_model_id
    _assert_result(
        distribution_result,
        "account.analytic.distribution.model",
        distribution_model_id,
    )
    _assert_result(
        _write(
            env,
            alias,
            run_id,
            "analytic.distribution_model.update",
            {"id": distribution_model_id, "changes": {"sequence": 92}},
        ),
        "account.analytic.distribution.model",
        distribution_model_id,
    )
    distribution = _read(
        env,
        alias,
        run_id,
        "analytic.distribution_model.get",
        {"distribution_model_id": distribution_model_id},
    )
    if (
        distribution["id"] != distribution_model_id
        or distribution["sequence"] != 92
        or distribution["company_id"] != _COMPANY_ID
        or len(distribution["allocations"]) != 1
        or distribution["allocations"][0]["percentage"] != "100"
        or [
            account["id"]
            for account in distribution["allocations"][0]["analytic_accounts"]
        ]
        != [analytic_account.id]
    ):
        raise RuntimeError(
            f"analytic.distribution_model.get mismatched: {distribution}"
        )


def _exercise_mapping_reads(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    marker: str,
    created: dict[str, int | None],
) -> None:
    from odoo import Command

    company = env["res.company"].browse(_COMPANY_ID)
    country = company.account_fiscal_country_id or company.country_id
    if not country:
        raise RuntimeError("the isolated company lacks a fiscal country")
    accounts = env["account.account"].search(
        [("company_ids", "in", [_COMPANY_ID]), ("active", "=", True)],
        order="id",
        limit=2,
    )
    if len(accounts) != 2:
        raise RuntimeError("the isolated database lacks two company accounts")

    tax_group = env["account.tax.group"].create(
        {
            "name": f"{marker} Tax Group",
            "company_id": _COMPANY_ID,
            "country_id": country.id,
        }
    )
    created["tax_group"] = tax_group.id
    source_tax = env["account.tax"].create(
        {
            "name": f"{marker} Source Tax",
            "amount": 10.0,
            "amount_type": "percent",
            "type_tax_use": "sale",
            "company_id": _COMPANY_ID,
            "tax_group_id": tax_group.id,
        }
    )
    created["source_tax"] = source_tax.id
    destination_taxes = env["account.tax"].create(
        [
            {
                "name": f"{marker} Destination Tax {index}",
                "amount": amount,
                "amount_type": "percent",
                "type_tax_use": "sale",
                "company_id": _COMPANY_ID,
                "tax_group_id": tax_group.id,
                "original_tax_ids": [Command.set([source_tax.id])],
            }
            for index, amount in ((1, 5.0), (2, 15.0))
        ]
    )
    created["destination_tax_1"] = destination_taxes[0].id
    created["destination_tax_2"] = destination_taxes[1].id

    fiscal_position = env["account.fiscal.position"].create(
        {
            "name": f"{marker} Fiscal Position",
            "company_id": _COMPANY_ID,
            "tax_ids": [Command.set(destination_taxes.ids)],
        }
    )
    created["fiscal_position"] = fiscal_position.id
    empty_fiscal_position = env["account.fiscal.position"].create(
        {
            "name": f"{marker} Empty Fiscal Position",
            "company_id": _COMPANY_ID,
            "tax_ids": [Command.clear()],
        }
    )
    created["empty_fiscal_position"] = empty_fiscal_position.id
    account_mapping = env["account.fiscal.position.account"].create(
        {
            "position_id": fiscal_position.id,
            "account_src_id": accounts[0].id,
            "account_dest_id": accounts[1].id,
        }
    )
    created["account_mapping"] = account_mapping.id
    env.flush_all()

    account_page = _read(
        env,
        alias,
        run_id,
        "fiscal_position.account_mapping.list",
        {"fiscal_position_id": fiscal_position.id, "limit": 100, "cursor": None},
    )
    if account_page != {
        "items": [
            {
                "id": account_mapping.id,
                "company_id": _COMPANY_ID,
                "source_account": {
                    "id": accounts[0].id,
                    "code": accounts[0].code,
                    "name": accounts[0].name,
                },
                "destination_account": {
                    "id": accounts[1].id,
                    "code": accounts[1].code,
                    "name": accounts[1].name,
                },
            }
        ],
        "has_more": False,
        "next_cursor": None,
    }:
        raise RuntimeError(f"account mapping list mismatched: {account_page}")

    tax_page = _read(
        env,
        alias,
        run_id,
        "fiscal_position.tax_mapping.list",
        {"fiscal_position_id": fiscal_position.id, "limit": 100, "cursor": None},
    )
    if (
        tax_page["has_more"] is not False
        or tax_page["next_cursor"] is not None
        or tax_page["removes_all_taxes"] is not False
        or len(tax_page["items"]) != 1
        or tax_page["items"][0]["source_tax"]["id"] != source_tax.id
        or [tax["id"] for tax in tax_page["items"][0]["destination_taxes"]]
        != sorted(destination_taxes.ids)
    ):
        raise RuntimeError(f"tax mapping list mismatched: {tax_page}")

    empty_tax_page = _read(
        env,
        alias,
        run_id,
        "fiscal_position.tax_mapping.list",
        {
            "fiscal_position_id": empty_fiscal_position.id,
            "limit": 100,
            "cursor": None,
        },
    )
    if empty_tax_page != {
        "items": [],
        "has_more": False,
        "next_cursor": None,
        "removes_all_taxes": True,
    }:
        raise RuntimeError(f"empty tax mapping semantics mismatched: {empty_tax_page}")


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
        remaining = {
            key: env[model].search_count([("id", "=", record_id)], limit=1)
            for key, model in _CREATED_MODELS.items()
            if (record_id := created[key]) is not None
        }
        remaining["marker"] = sum(
            env[model].search_count([("name", "ilike", marker)], limit=1)
            for model in (
                "account.fiscal.year",
                "account.analytic.account",
                "account.tax.group",
                "account.tax",
                "account.fiscal.position",
            )
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
    marker = f"ODACV4-ACCOUNTING-RULES-{args.alias}-{args.run_id.hex}"
    created: dict[str, int | None] = dict.fromkeys(_CREATED_MODELS)
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
        _exercise_writes(env, args.alias, args.run_id, marker, created)
        _exercise_mapping_reads(env, args.alias, args.run_id, marker, created)
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
