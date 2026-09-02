"""Shared rollback smoke for return reads, writes, and journal analysis."""

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
_ALLOW_ENV = "ODACV4_ALLOW_RETURN_JOURNAL_ANALYSIS_SMOKE"
_ALIASES = ("v4-dev", "v4-e2e")
_PHYSICAL_DATABASES = {
    "v4-dev": "odoo_cli_v4_dev",
    "v4-e2e": "odoo_cli_v4_e2e",
}
_COMPANY_ID = 1
_USER_LOGIN = "odacv4_g5_accountant"
_DRAFT_ENTRIES_VIEW_XMLID = "account_reports.view_draft_entries_tree"
_CAPABILITY_IDS = (
    "account.return.search",
    "account.return.get",
    "account.return.summary",
    "account.return.type.list",
    "account.return.check.list",
    "account.return.check.get",
    "journal.accounting_date.resolve",
    "journal_item.analysis.summary",
    "account.return.create",
    "account.return.checks.refresh",
    "account.return.check.result.update",
    "account.return.validate",
    "account.return.mark_submitted",
    "account.return.archive",
    "account.return.restore",
    "account.return.delete",
)
_WRITE_CAPABILITY_IDS = frozenset(_CAPABILITY_IDS[-8:])


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
    assert result["environment_fixtures"] in (
        [],
        [_DRAFT_ENTRIES_VIEW_XMLID],
    )
    assert result == {
        "alias": alias,
        "capabilities": list(_CAPABILITY_IDS),
        "company_id": _COMPANY_ID,
        "database": _PHYSICAL_DATABASES[alias],
        "environment_fixtures": result["environment_fixtures"],
        "positive_results": len(_CAPABILITY_IDS),
        "rollback_verified": True,
        "user_id": result["user_id"],
    }
    assert isinstance(result["user_id"], int) and result["user_id"] > 0
    return result


if pytest is not None:

    @pytest.mark.integration
    @pytest.mark.parametrize("alias", _ALIASES)
    def test_return_journal_analysis_batch_is_live_and_rolls_back(
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
    canonical_parameters = json.dumps(
        parameters,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return {
        "schema_version": "v1",
        "request_id": str(
            uuid.uuid5(run_id, f"{capability_id}:{canonical_parameters}")
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


def _write_key(capability_id: str, parameters: dict[str, Any]) -> str:
    if capability_id == "account.return.create":
        canonical = json.dumps(
            parameters,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()[:32]
        return f"{capability_id}:{_COMPANY_ID}:{digest}"
    if capability_id == "account.return.check.result.update":
        return (
            f"{capability_id}:{parameters['check_id']}:{parameters['result']}"
        )
    return f"{capability_id}:{parameters['return_id']}"


def _invoke_write(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    parameters: dict[str, Any],
    *,
    replay: bool = True,
    expected_first_replay: bool | None = False,
) -> dict[str, Any]:
    from odoo_accounting_cli_v4.bridge.core_writes import OdooCoreWritePort
    from odoo_accounting_cli_v4.capabilities.core_writes import execute_core_write

    if capability_id not in _WRITE_CAPABILITY_IDS:
        raise RuntimeError(f"{capability_id} is not in the return-write smoke")
    key = _write_key(capability_id, parameters)
    request = _request(alias, run_id, capability_id, parameters)
    port = OdooCoreWritePort(_DirectClient(env))
    first = execute_core_write(port, capability_id, request, key, capability_id)
    if (
        expected_first_replay is not None
        and first["idempotent_replay"] is not expected_first_replay
    ):
        raise RuntimeError(
            f"{capability_id} returned an unexpected first replay flag"
        )
    if not replay:
        return first["result"]
    second = execute_core_write(port, capability_id, request, key, capability_id)
    if second["idempotent_replay"] is not True:
        raise RuntimeError(f"{capability_id} did not replay its target state")
    if second["result"] != first["result"]:
        raise RuntimeError(f"{capability_id} changed during immediate replay")
    return first["result"]


def _invoke_capability(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    from odoo_accounting_cli_v4.bridge.account_returns import OdooAccountReturnPort
    from odoo_accounting_cli_v4.bridge.journal_analysis import (
        OdooJournalAnalysisPort,
    )
    from odoo_accounting_cli_v4.capabilities.account_returns import (
        read_account_return,
    )
    from odoo_accounting_cli_v4.capabilities.journal_analysis import (
        read_journal_analysis,
    )

    client = _DirectClient(env)
    request = _request(alias, run_id, capability_id, parameters)
    if capability_id.startswith("account.return."):
        port = OdooAccountReturnPort(client)
        data = read_account_return(port, capability_id, request)
    else:
        port = OdooJournalAnalysisPort(client)
        data = read_journal_analysis(port, capability_id, request)
    if port.user_id != env.uid or not isinstance(data, dict):
        raise RuntimeError(
            f"{capability_id} returned an invalid public capability result"
        )
    return data


def _setup_return_fixture(admin_env: Any, marker: str) -> tuple[int, int, int, str]:
    return_type = admin_env["account.return.type"].search(
        [
            ("category", "=", "account_return"),
            ("report_id", "=", False),
            ("states_workflow", "=", "generic_state_review_submit"),
        ],
        order="id",
        limit=1,
    )
    if not return_type:
        raise RuntimeError("no reportless submit-workflow return type is available")
    account_return = admin_env["account.return"].create(
        {
            "name": marker,
            "date_from": "2096-01-01",
            "date_to": "2096-12-31",
            "type_id": return_type.id,
            "company_id": _COMPANY_ID,
            "manually_created": True,
        }
    )
    return_check = admin_env["account.return.check"].create(
        {
            "return_id": account_return.id,
            "code": marker,
            "name": marker,
        }
    )
    admin_env.flush_all()
    if (
        not account_return.manually_created
        or account_return.company_id.id != _COMPANY_ID
        or account_return.type_id.category == "audit"
        or return_check.return_id != account_return
        or not account_return.date_deadline
    ):
        raise RuntimeError("the manual account-return fixture is invalid")
    return (
        account_return.id,
        return_check.id,
        return_type.id,
        account_return.date_deadline.isoformat(),
    )


def _ensure_draft_entries_view_fixture(
    admin_env: Any, marker: str
) -> tuple[list[int], list[int], list[str]]:
    existing_data = admin_env["ir.model.data"].search(
        [
            ("module", "=", "account_reports"),
            ("name", "=", "view_draft_entries_tree"),
        ],
        limit=2,
    )
    existing_view = admin_env.ref(
        _DRAFT_ENTRIES_VIEW_XMLID, raise_if_not_found=False
    )
    if existing_data or existing_view:
        if (
            len(existing_data) != 1
            or not existing_view
            or existing_data.model != "ir.ui.view"
            or existing_data.res_id != existing_view.id
        ):
            raise RuntimeError("the draft-entries external ID is inconsistent")
        return [], [], []
    view = admin_env["ir.ui.view"].create(
        {
            "name": f"{marker} draft entries list",
            "model": "account.move",
            "inherit_id": admin_env.ref("account.view_invoice_tree").id,
            "mode": "primary",
            "arch": """
                <xpath expr="//field[@name='date']" position="attributes">
                    <attribute name="optional">show</attribute>
                </xpath>
            """,
        }
    )
    external_id = admin_env["ir.model.data"].create(
        {
            "module": "account_reports",
            "name": "view_draft_entries_tree",
            "model": "ir.ui.view",
            "res_id": view.id,
            "noupdate": True,
        }
    )
    admin_env.flush_all()
    if (
        admin_env.ref(_DRAFT_ENTRIES_VIEW_XMLID) != view
        or view.model != "account.move"
        or view.inherit_id != admin_env.ref("account.view_invoice_tree")
        or view.mode != "primary"
        or view.type != "list"
        or external_id.module != "account_reports"
        or external_id.name != "view_draft_entries_tree"
        or external_id.model != "ir.ui.view"
        or external_id.res_id != view.id
        or not external_id.noupdate
    ):
        raise RuntimeError("the rollback-only draft-entries view fixture is unavailable")
    return [view.id], [external_id.id], [_DRAFT_ENTRIES_VIEW_XMLID]


def _posted_journal_and_date(env: Any) -> tuple[int, str]:
    line = env["account.move.line"].search(
        [
            ("company_id", "=", _COMPANY_ID),
            ("parent_state", "=", "posted"),
            ("journal_id", "!=", False),
        ],
        order="id",
        limit=1,
    )
    if not line or not line.journal_id:
        raise RuntimeError("no posted journal item is available")
    return line.journal_id.id, line.date.isoformat()


def _ids(items: list[dict[str, Any]]) -> list[int]:
    return [item["id"] for item in items]


def _exercise_batch(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    return_id: int,
    check_id: int,
    type_id: int,
    deadline: str,
) -> None:
    journal_id, journal_date = _posted_journal_and_date(env)

    search = _invoke_capability(
        env,
        alias,
        run_id,
        "account.return.search",
        {
            "type_id": type_id,
            "deadline_from": deadline,
            "deadline_to": deadline,
            "active": True,
            "limit": 100,
            "cursor": None,
        },
    )
    if return_id not in _ids(search["items"]):
        raise RuntimeError("account.return.search missed the fixture")

    returned = _invoke_capability(
        env,
        alias,
        run_id,
        "account.return.get",
        {"return_id": return_id},
    )
    if returned["id"] != return_id:
        raise RuntimeError("account.return.get missed the fixture")

    summary = _invoke_capability(
        env,
        alias,
        run_id,
        "account.return.summary",
        {"as_of": deadline},
    )
    if summary["counts"]["total"] < 1:
        raise RuntimeError("account.return.summary returned no live rows")

    return_types = _invoke_capability(
        env,
        alias,
        run_id,
        "account.return.type.list",
        {"category": "account_return", "limit": 100, "cursor": None},
    )
    if type_id not in _ids(return_types["items"]):
        raise RuntimeError("account.return.type.list missed the fixture type")

    checks = _invoke_capability(
        env,
        alias,
        run_id,
        "account.return.check.list",
        {
            "return_id": return_id,
            "result": "todo",
            "type": "check",
            "limit": 100,
            "cursor": None,
        },
    )
    if check_id not in _ids(checks["items"]):
        raise RuntimeError("account.return.check.list missed the fixture")

    check = _invoke_capability(
        env,
        alias,
        run_id,
        "account.return.check.get",
        {"check_id": check_id},
    )
    if check["id"] != check_id:
        raise RuntimeError("account.return.check.get missed the fixture")

    resolution = _invoke_capability(
        env,
        alias,
        run_id,
        "journal.accounting_date.resolve",
        {"journal_id": journal_id, "date": journal_date, "has_tax": False},
    )
    if resolution["journal"]["id"] != journal_id:
        raise RuntimeError("journal.accounting_date.resolve missed the live journal")

    journal_summary = _invoke_capability(
        env,
        alias,
        run_id,
        "journal_item.analysis.summary",
        {"date_from": journal_date, "date_to": journal_date, "group_by": "journal"},
    )
    if journal_summary["totals"]["row_count"] < 1 or journal_id not in [
        group["group"]["id"] for group in journal_summary["groups"]
    ]:
        raise RuntimeError("journal_item.analysis.summary missed live posted entries")


def _exercise_write_batch(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    marker: str,
    type_id: int,
) -> tuple[list[int], list[int]]:
    main_parameters = {
        "return_type_id": type_id,
        "date_from": "2095-01-01",
        "date_to": "2095-12-31",
    }
    created = _invoke_write(
        env,
        alias,
        run_id,
        "account.return.create",
        main_parameters,
    )
    main_id = created["id"]
    if created["state"] != "new" or created["source_id"] != type_id:
        raise RuntimeError("account.return.create returned the wrong type or state")

    refreshed = _invoke_write(
        env,
        alias,
        run_id,
        "account.return.checks.refresh",
        {"return_id": main_id},
        expected_first_replay=None,
    )
    if refreshed["id"] != main_id or refreshed["state"] != "new":
        raise RuntimeError("account.return.checks.refresh returned the wrong return")

    checks = env["account.return.check"].search(
        [
            ("return_id", "=", main_id),
            ("state", "=", "new"),
            ("result", "in", ["todo", "anomaly"]),
        ],
        order="id",
    )
    if not checks:
        checks = env["account.return.check"].create(
            {
                "return_id": main_id,
                "code": f"{marker}-WRITE-CHECK",
                "name": f"{marker} write check",
            }
        )
    check_ids = sorted(checks.ids)
    for check_id in check_ids:
        updated = _invoke_write(
            env,
            alias,
            run_id,
            "account.return.check.result.update",
            {"check_id": check_id, "result": "reviewed"},
        )
        if (
            updated["id"] != check_id
            or updated["state"] != "reviewed"
            or updated["source_id"] != main_id
        ):
            raise RuntimeError(
                "account.return.check.result.update returned the wrong check"
            )

    validated = _invoke_write(
        env,
        alias,
        run_id,
        "account.return.validate",
        {"return_id": main_id},
    )
    if validated["state"] != "reviewed":
        raise RuntimeError("account.return.validate did not enter reviewed state")
    submitted = _invoke_write(
        env,
        alias,
        run_id,
        "account.return.mark_submitted",
        {"return_id": main_id},
    )
    main_return = env["account.return"].browse(main_id).exists()
    if (
        submitted["state"] != "submitted"
        or len(main_return) != 1
        or main_return.state != "submitted"
        or not main_return.is_completed
    ):
        raise RuntimeError(
            "account.return.mark_submitted did not complete the internal state"
        )

    disposable_parameters = {
        "return_type_id": type_id,
        "date_from": "2098-01-01",
        "date_to": "2098-12-31",
    }
    disposable = _invoke_write(
        env,
        alias,
        run_id,
        "account.return.create",
        disposable_parameters,
    )
    disposable_id = disposable["id"]
    archived = _invoke_write(
        env,
        alias,
        run_id,
        "account.return.archive",
        {"return_id": disposable_id},
    )
    if archived["state"] != "archived":
        raise RuntimeError("account.return.archive left the return active")
    restored = _invoke_write(
        env,
        alias,
        run_id,
        "account.return.restore",
        {"return_id": disposable_id},
    )
    if restored["state"] != "new":
        raise RuntimeError("account.return.restore changed the business state")
    deleted = _invoke_write(
        env,
        alias,
        run_id,
        "account.return.delete",
        {"return_id": disposable_id},
        replay=False,
    )
    if deleted["id"] != disposable_id or deleted["state"] != "deleted":
        raise RuntimeError("account.return.delete returned the wrong record")
    if env["account.return"].with_context(active_test=False).search_count(
        [("id", "=", disposable_id)], limit=1
    ):
        raise RuntimeError("account.return.delete left the record visible")
    return [main_id, disposable_id], check_ids


def _verify_rollback(
    registry: Any,
    marker: str,
    return_ids: list[int],
    check_ids: list[int],
    fixture_view_ids: list[int],
    fixture_xmlid_ids: list[int],
) -> None:
    from odoo import SUPERUSER_ID, api

    cursor = registry.cursor()
    try:
        env = api.Environment(
            cursor,
            SUPERUSER_ID,
            {"allowed_company_ids": [_COMPANY_ID], "active_test": False},
        )
        remaining_returns = env["account.return"].search_count(
            [("name", "=", marker), ("company_id", "=", _COMPANY_ID)],
            limit=1,
        )
        remaining_checks = env["account.return.check"].search_count(
            [("code", "=", marker)],
            limit=1,
        )
        remaining_ids = env["account.return"].search_count(
            [("id", "in", return_ids)], limit=1
        )
        remaining_check_ids = env["account.return.check"].search_count(
            [("id", "in", check_ids)], limit=1
        )
        remaining_view_ids = env["ir.ui.view"].search_count(
            [("id", "in", fixture_view_ids)], limit=1
        )
        remaining_xmlid_ids = env["ir.model.data"].search_count(
            [("id", "in", fixture_xmlid_ids)], limit=1
        )
        remaining_fixture_xmlid = bool(
            fixture_xmlid_ids
            and env.ref(_DRAFT_ENTRIES_VIEW_XMLID, raise_if_not_found=False)
        )
        remaining_fixture_views = env["ir.ui.view"].search_count(
            [("name", "=", f"{marker} draft entries list")], limit=1
        )
        if (
            remaining_returns
            or remaining_checks
            or remaining_ids
            or remaining_check_ids
            or remaining_view_ids
            or remaining_xmlid_ids
            or remaining_fixture_xmlid
            or remaining_fixture_views
        ):
            raise RuntimeError("an account-return fixture survived rollback")
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
    marker = f"ODACV4-RETURN-JOURNAL-{args.alias}-{args.run_id.hex}"
    user_id: int | None = None
    created_return_ids: list[int] = []
    created_check_ids: list[int] = []
    fixture_view_ids: list[int] = []
    fixture_xmlid_ids: list[int] = []
    environment_fixtures: list[str] = []
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
            or company.parent_id
            or company.child_ids
            or not user
            or not user.active
            or company not in user.company_ids
        ):
            raise RuntimeError(
                "the configured standalone company or user is unavailable"
            )
        (
            fixture_view_ids,
            fixture_xmlid_ids,
            environment_fixtures,
        ) = _ensure_draft_entries_view_fixture(admin_env, marker)
        return_id, check_id, type_id, deadline = _setup_return_fixture(
            admin_env, marker
        )
        created_return_ids.append(return_id)
        created_check_ids.append(check_id)
        user_id = user.id
        business_env = api.Environment(cursor, user_id, context)
        _exercise_batch(
            business_env,
            args.alias,
            args.run_id,
            return_id,
            check_id,
            type_id,
            deadline,
        )
        write_return_ids, write_check_ids = _exercise_write_batch(
            business_env,
            args.alias,
            args.run_id,
            marker,
            type_id,
        )
        created_return_ids.extend(write_return_ids)
        created_check_ids.extend(write_check_ids)
    finally:
        cursor.rollback()
        cursor.close()

    _verify_rollback(
        registry,
        marker,
        created_return_ids,
        created_check_ids,
        fixture_view_ids,
        fixture_xmlid_ids,
    )
    sys.stdout.write(
        json.dumps(
            {
                "alias": args.alias,
                "capabilities": list(_CAPABILITY_IDS),
                "company_id": _COMPANY_ID,
                "database": args.database,
                "environment_fixtures": environment_fixtures,
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
