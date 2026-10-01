"""One rollback-only CLI/real-ORM workflow for financial-report budget writes."""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import sysconfig
import uuid
from pathlib import Path
from typing import Any

import test_document_lifecycle_write_batch_live as lifecycle
import test_payment_bank_capability_batch_live as core

try:
    import pytest
except ModuleNotFoundError:
    if "--live-worker" not in sys.argv:
        raise
    pytest = None

_ALLOW_ENV = "ODACV4_ALLOW_REPORT_BUDGET_WRITE_SMOKE"
_GROUP = "account.group_account_manager"
_WRITES = {
    "report.budget_definition.create",
    "report.budget_definition.update",
    "report.budget_definition.duplicate",
    "report.budget_definition.delete",
    "report.budget_item.create",
    "report.budget_item.update",
    "report.budget_item.delete",
    "report.budget_account_period.set_total",
}
_READS = {"report.budget_definition.get", "report.budget_item.get"}
_MODELS = ("account.report.budget", "account.report.budget.item")


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


if pytest is not None:

    @pytest.mark.integration
    def test_report_budget_batch_rolls_back_per_alias() -> None:
        config_path, runtime = lifecycle._enabled_runtime(_ALLOW_ENV)
        run_id = uuid.uuid4()
        for alias in lifecycle._ALIASES:
            command, timeout = lifecycle._worker_command(
                alias, run_id, config_path, runtime
            )
            command[1] = str(Path(__file__).resolve())
            environment = os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            environment["PYTHONPATH"] = os.pathsep.join(
                filter(
                    None,
                    (
                        str(_root() / "src"),
                        sysconfig.get_path("purelib"),
                        environment.get("PYTHONPATH"),
                    ),
                )
            )
            completed = subprocess.run(
                command,
                cwd=_root(),
                env=environment,
                text=True,
                capture_output=True,
                check=False,
                timeout=max(timeout, 900),
            )
            assert completed.returncode == 0, completed.stdout + completed.stderr
            result = json.loads(completed.stdout)
            assert result == {
                "alias": alias,
                "database": lifecycle._DATABASES[alias],
                "company_id": 1,
                "user_id": 5,
                "business_su": False,
                "capabilities": sorted(_WRITES | _READS),
                "immediate_replays": 6,
                "source_items": 4,
                "period_items": 3,
                "cross_company_rejected": True,
                "rollback_verified": True,
                "temporary_group_rolled_back": True,
                "execution": "in_process_cli_real_orm",
            }
            print(completed.stdout.strip(), flush=True)


class _Client:
    def __init__(self, env: Any) -> None:
        self.env = env
        self.capabilities: set[str] = set()
        self.tracked: dict[str, set[int]] = {model: set() for model in _MODELS}
        self.last_runtime_failure: Exception | None = None

    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        from odoo_accounting_cli_v4.bridge.client import BridgeError
        from odoo_accounting_cli_v4.bridge.runtime import RuntimeFailure, _dispatch

        assert self.env.uid == 5 and not self.env.su and self.env.company.id == 1
        self.env.invalidate_all()
        try:
            page = _dispatch(self.env, action, payload, 1, (1,))
        except RuntimeFailure as exc:
            self.last_runtime_failure = exc
            raise BridgeError(
                exc.code,
                str(exc),
                exit_code=exc.exit_code,
                retryable=exc.retryable,
                details=exc.details,
            ) from exc
        result = page.get("result")
        if isinstance(result, dict) and result["model"] in self.tracked:
            self.tracked[result["model"]].add(result["id"])
            if result["model"] == "account.report.budget":
                self.tracked["account.report.budget.item"].update(result["line_ids"])
        return page


def _write(client, alias, run_id, capability, parameters, *, replay=True):
    from odoo_accounting_cli_v4.capabilities.core_writes import (
        _expected_idempotency_key,
        validate_core_write_request,
    )

    request = core._request(alias, run_id, capability, parameters)
    normalized = validate_core_write_request(capability, request)[2]
    key = _expected_idempotency_key(capability, normalized, 1)
    assert key is not None
    first = core._cli(client, alias, run_id, capability, parameters, key=key)
    assert first["idempotent_replay"] is False
    if replay:
        second = core._cli(client, alias, run_id, capability, parameters, key=key)
        assert (
            second["idempotent_replay"] is True and first["result"] == second["result"]
        )
    return first["result"]


def _read(client, alias, run_id, capability, parameters):
    from odoo_accounting_cli_v4 import cli
    from odoo_accounting_cli_v4.bridge.core_object_reads import OdooCoreObjectReadPort

    request = core._request(alias, run_id, capability, parameters)
    stdout, stderr = io.StringIO(), io.StringIO()
    code = cli.main(
        ["read", capability, "--request", "-"],
        stdin=io.StringIO(json.dumps(request)),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda *args: OdooCoreObjectReadPort(client),
    )
    assert code == 0, stdout.getvalue() + stderr.getvalue()
    response = json.loads(stdout.getvalue())
    assert response["success"] is True and response["status"] == "verified"
    assert response["odoo"]["user_id"] == 5 and response["odoo"]["company_id"] == 1
    client.capabilities.add(capability)
    return response["data"]


def _exercise(client, alias, run_id, marker):
    env = client.env
    account = env["account.account"].search(
        [
            ("company_ids", "in", [1]),
            ("account_type", "in", ["income", "expense"]),
        ],
        limit=1,
        order="id",
    )
    assert account
    created = _write(
        client,
        alias,
        run_id,
        "report.budget_definition.create",
        {
            "name": marker,
            "sequence": 0,
        },
    )
    budget_id = created["id"]
    _write(
        client,
        alias,
        run_id,
        "report.budget_definition.update",
        {
            "budget_definition_id": budget_id,
            "changes": {"name": marker + "-UPDATED", "sequence": 7},
        },
    )
    line = _write(
        client,
        alias,
        run_id,
        "report.budget_item.create",
        {
            "budget_definition_id": budget_id,
            "account_id": account.id,
            "date": "2026-01-01",
            "amount": "100",
        },
    )
    _write(
        client,
        alias,
        run_id,
        "report.budget_item.update",
        {
            "budget_item_id": line["id"],
            "changes": {"amount": "-150"},
        },
    )
    read_line = _read(
        client, alias, run_id, "report.budget_item.get", {"budget_item_id": line["id"]}
    )
    assert (
        read_line["amount"] == "-150"
        and read_line["budget_definition"]["id"] == budget_id
    )
    # An ordinary fixture outside the selected period must survive allocation unchanged.
    outside = env["account.report.budget.item"].create(
        {
            "budget_id": budget_id,
            "account_id": account.id,
            "date": "2025-12-01",
            "amount": 33,
        }
    )
    client.tracked["account.report.budget.item"].add(outside.id)
    period = _write(
        client,
        alias,
        run_id,
        "report.budget_account_period.set_total",
        {
            "budget_definition_id": budget_id,
            "account_id": account.id,
            "date_from": "2026-01-01",
            "date_to": "2026-03-31",
            "total": "500",
            "rounding": 2,
        },
    )
    assert len(period["line_ids"]) == 3 and outside.id not in period["line_ids"]
    budget = env["account.report.budget"].browse(budget_id).exists()
    assert (
        round(
            sum(
                item.amount for item in budget.item_ids if item.id in period["line_ids"]
            ),
            2,
        )
        == 500
    )
    assert outside.amount == 33
    description = _read(
        client,
        alias,
        run_id,
        "report.budget_definition.get",
        {"budget_definition_id": budget_id},
    )
    assert description["item_count"] == 4 and description["sequence"] == 7
    assert description["name"] == marker + "-UPDATED"
    source_ids = set(budget.item_ids.ids)
    source_values = sorted(
        (item.account_id.id, str(item.date), item.amount) for item in budget.item_ids
    )
    duplicated = _write(
        client,
        alias,
        run_id,
        "report.budget_definition.duplicate",
        {
            "budget_definition_id": budget_id,
            "name": marker + "-COPY",
        },
    )
    duplicate = env["account.report.budget"].browse(duplicated["id"]).exists()
    assert duplicate.name == marker + "-COPY" and duplicate.id != budget_id
    assert len(duplicate.item_ids) == 4 and source_ids.isdisjoint(
        duplicate.item_ids.ids
    )
    assert (
        sorted(
            (item.account_id.id, str(item.date), item.amount)
            for item in duplicate.item_ids
        )
        == source_values
    )
    deleted_line_id = min(duplicate.item_ids.ids)
    _write(
        client,
        alias,
        run_id,
        "report.budget_item.delete",
        {"budget_item_id": deleted_line_id},
        replay=False,
    )
    assert not env["account.report.budget.item"].browse(deleted_line_id).exists()
    assert len(duplicate.item_ids) == 3 and set(budget.item_ids.ids) == source_ids
    copied_ids = set(duplicate.item_ids.ids)
    _write(
        client,
        alias,
        run_id,
        "report.budget_definition.delete",
        {
            "budget_definition_id": duplicate.id,
        },
        replay=False,
    )
    assert not duplicate.exists()
    assert not env["account.report.budget.item"].browse(sorted(copied_ids)).exists()
    assert set(budget.item_ids.ids) == source_ids
    assert client.capabilities == _WRITES | _READS


def _direct_group(cursor, group_id):
    cursor.execute(
        "SELECT EXISTS(SELECT 1 FROM res_groups_users_rel WHERE uid=%s AND gid=%s)",
        [5, group_id],
    )
    return cursor.fetchone()[0]


def _live_worker():
    args = lifecycle._arguments(None)
    assert not (
        args.refund_only or args.payment_difference_only or args.analytic_readback_only
    )
    sys.path.insert(0, str(args.odoo_source.resolve(strict=True)))
    sys.path.insert(0, str(_root() / "src"))
    from odoo import SUPERUSER_ID, Command, api
    from odoo.orm.registry import Registry
    from odoo.tools import config

    config.parse_config(
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
    marker = f"ODACV4-REPORT-BUDGET-{args.alias}-{args.run_id.hex}"
    admin_env = client = None
    group_id = baseline_group = None
    failure = None
    tracked = {model: set() for model in _MODELS}
    try:
        context = {"allowed_company_ids": [1], "lang": "en_US", "tz": "Asia/Shanghai"}
        admin_env = api.Environment(cursor, SUPERUSER_ID, context)
        user = admin_env["res.users"].browse(5).exists()
        assert (
            user.active
            and user.login == lifecycle._USER_LOGIN
            and 1 in user.company_ids.ids
        )
        group_id = admin_env.ref(_GROUP).id
        baseline_group = _direct_group(cursor, group_id)
        if not user.has_group(_GROUP):
            user.write({"group_ids": [Command.link(group_id)]})
            admin_env.flush_all()
        env = api.Environment(cursor, 5, context)
        assert not env.su and env.user.has_group(_GROUP)
        client = _Client(env)
        tracked = client.tracked
        # A company-2 target inside this same isolated database must not be visible to company-1 commands.
        assert admin_env["res.company"].browse(2).exists()
        foreign = (
            admin_env["account.report.budget"]
            .with_company(2)
            .create(
                {
                    "name": marker + "-FOREIGN",
                    "company_id": 2,
                }
            )
        )
        tracked["account.report.budget"].add(foreign.id)
        try:
            _write(
                client,
                args.alias,
                args.run_id,
                "report.budget_definition.delete",
                {
                    "budget_definition_id": foreign.id,
                },
                replay=False,
            )
        except AssertionError:
            assert (
                getattr(client.last_runtime_failure, "code", None) == "record_not_found"
            )
            assert foreign.exists()
        else:
            raise RuntimeError("a company-2 budget escaped company-1 scope")
        _exercise(client, args.alias, args.run_id, marker)
    except BaseException as exc:  # noqa: BLE001 - rollback also covers failed fixtures.
        failure = exc
    finally:
        try:
            if admin_env is not None:
                admin_env.invalidate_all()
                marked = admin_env["account.report.budget"].search(
                    [("name", "ilike", marker)]
                )
                tracked["account.report.budget"].update(marked.ids)
                tracked["account.report.budget.item"].update(marked.item_ids.ids)
        except Exception as exc:  # noqa: BLE001 - collection must not prevent rollback.
            if failure is None:
                failure = exc
        finally:
            cursor.rollback()
            cursor.close()
    with registry.cursor() as verify_cursor:
        try:
            verify_env = api.Environment(
                verify_cursor, SUPERUSER_ID, {"allowed_company_ids": [1, 2]}
            )
            assert not verify_env["account.report.budget"].search_count(
                [("name", "ilike", marker)]
            )
            for model, ids in tracked.items():
                assert not verify_env[model].search_count([("id", "in", sorted(ids))])
            if group_id is not None and baseline_group is not None:
                assert _direct_group(verify_cursor, group_id) == baseline_group
        finally:
            verify_cursor.rollback()
    if failure is not None:
        raise failure
    assert client is not None
    print(
        json.dumps(
            {
                "alias": args.alias,
                "database": args.database,
                "company_id": 1,
                "user_id": 5,
                "business_su": False,
                "capabilities": sorted(client.capabilities),
                "immediate_replays": 6,
                "source_items": 4,
                "period_items": 3,
                "cross_company_rejected": True,
                "rollback_verified": True,
                "temporary_group_rolled_back": True,
                "execution": "in_process_cli_real_orm",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_live_worker())
