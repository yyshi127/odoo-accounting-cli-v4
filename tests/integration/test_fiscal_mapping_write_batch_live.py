"""One rollback-only CLI/real-ORM workflow for fiscal-position and tax mapping writes."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import sysconfig
import uuid
from pathlib import Path
from typing import Any

import test_document_lifecycle_write_batch_live as lifecycle
import test_report_budget_write_batch_live as shared

try:
    import pytest
except ModuleNotFoundError:
    if "--live-worker" not in sys.argv:
        raise
    pytest = None

_ALLOW_ENV = "ODACV4_ALLOW_FISCAL_MAPPING_WRITE_SMOKE"
_GROUP = "account.group_account_manager"
_WRITES = {
    "fiscal_position.taxes.replace",
    "tax.original_taxes.replace",
    "fiscal_position.account_mapping.create",
    "fiscal_position.account_mapping.update",
    "fiscal_position.account_mapping.delete",
    "fiscal_position.duplicate",
    "fiscal_position.delete",
    "tax.duplicate",
}
_READS = {"fiscal_position.tax_mapping.list", "fiscal_position.account_mapping.list"}
_SETUP = {"fiscal_position.create", "tax.create"}
_MODELS = (
    "account.fiscal.position",
    "account.fiscal.position.account",
    "account.tax",
    "account.tax.repartition.line",
)


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


if pytest is not None:

    @pytest.mark.integration
    def test_fiscal_mapping_batch_rolls_back_per_alias() -> None:
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
                "capabilities": sorted(_WRITES | _READS | _SETUP),
                "immediate_replays": 6,
                "source_mappings": 2,
                "detached_tax_copies": 2,
                "cross_company_rejected": True,
                "rollback_verified": True,
                "temporary_group_rolled_back": True,
                "execution": "in_process_cli_real_orm",
            }
            print(completed.stdout.strip(), flush=True)


class _Client(shared._Client):
    def __init__(self, env: Any) -> None:
        super().__init__(env)
        self.tracked = {model: set() for model in _MODELS}

    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        page = super().invoke(action, payload)
        result = page.get("result")
        if isinstance(result, dict):
            child = {
                "account.fiscal.position": "account.fiscal.position.account",
                "account.tax": "account.tax.repartition.line",
            }.get(result["model"])
            if child is not None:
                self.tracked[child].update(result["line_ids"])
        return page


_write = shared._write
_read = shared._read
_direct_group = shared._direct_group


def _exercise(client, alias, run_id, marker):
    env = client.env
    accounts = (
        env["account.account"]
        .search([("company_ids", "in", [1])], order="id", limit=30)
        .filtered(lambda account: set(account.company_ids.ids) == {1})[:3]
    )
    assert len(accounts) == 3
    position_id = _write(
        client,
        alias,
        run_id,
        "fiscal_position.create",
        {"name": marker, "note": marker},
        replay=False,
    )["id"]
    source_tax_id = _write(
        client,
        alias,
        run_id,
        "tax.create",
        {
            "name": marker + "-SOURCE",
            "type_tax_use": "sale",
            "amount_type": "percent",
            "amount": 10,
        },
        replay=False,
    )["id"]
    destination_tax_id = _write(
        client,
        alias,
        run_id,
        "tax.create",
        {
            "name": marker + "-DESTINATION",
            "type_tax_use": "sale",
            "amount_type": "percent",
            "amount": 8,
        },
        replay=False,
    )["id"]
    _write(
        client,
        alias,
        run_id,
        "fiscal_position.taxes.replace",
        {"fiscal_position_id": position_id, "tax_ids": [destination_tax_id]},
    )
    _write(
        client,
        alias,
        run_id,
        "tax.original_taxes.replace",
        {"tax_id": destination_tax_id, "original_tax_ids": [source_tax_id]},
    )
    mapped = _write(
        client,
        alias,
        run_id,
        "fiscal_position.account_mapping.create",
        {
            "fiscal_position_id": position_id,
            "source_account_id": accounts[0].id,
            "destination_account_id": accounts[1].id,
        },
    )
    _write(
        client,
        alias,
        run_id,
        "fiscal_position.account_mapping.update",
        {
            "account_mapping_id": mapped["id"],
            "changes": {"destination_account_id": accounts[2].id},
        },
    )
    _write(
        client,
        alias,
        run_id,
        "fiscal_position.account_mapping.create",
        {
            "fiscal_position_id": position_id,
            "source_account_id": accounts[1].id,
            "destination_account_id": accounts[2].id,
        },
        replay=False,
    )
    mappings = _read(
        client,
        alias,
        run_id,
        "fiscal_position.account_mapping.list",
        {"fiscal_position_id": position_id},
    )
    assert len(mappings["items"]) == 2
    tax_map = _read(
        client,
        alias,
        run_id,
        "fiscal_position.tax_mapping.list",
        {"fiscal_position_id": position_id},
    )
    assert tax_map["removes_all_taxes"] is False and len(tax_map["items"]) == 1
    assert tax_map["items"][0]["source_tax"]["id"] == source_tax_id
    assert [tax["id"] for tax in tax_map["items"][0]["destination_taxes"]] == [
        destination_tax_id
    ]
    position = env["account.fiscal.position"].browse(position_id)
    source_mapping_ids = set(position.account_ids.ids)
    copied = _write(
        client,
        alias,
        run_id,
        "fiscal_position.duplicate",
        {"fiscal_position_id": position_id, "name": marker + "-COPY"},
    )
    copy_position = env["account.fiscal.position"].browse(copied["id"])
    assert copy_position.id != position_id and len(copy_position.account_ids) == 2
    assert source_mapping_ids.isdisjoint(copy_position.account_ids.ids)
    assert copy_position.tax_ids.ids == [destination_tax_id]
    source_tax = env["account.tax"].browse(source_tax_id)
    destination_tax = env["account.tax"].browse(destination_tax_id)
    before_positions = set(destination_tax.fiscal_position_ids.ids)
    for tax_id, suffix, replay in [
        (source_tax_id, "-SOURCE-COPY", True),
        (destination_tax_id, "-DESTINATION-COPY", False),
    ]:
        tax_copy = _write(
            client,
            alias,
            run_id,
            "tax.duplicate",
            {"tax_id": tax_id, "name": marker + suffix},
            replay=replay,
        )
        copied_tax = env["account.tax"].browse(tax_copy["id"])
        original = env["account.tax"].browse(tax_id)
        assert not copied_tax.fiscal_position_ids and not copied_tax.replacing_tax_ids
        assert set(copied_tax.repartition_line_ids.ids).isdisjoint(
            original.repartition_line_ids.ids
        )
        assert copied_tax.original_tax_ids.ids == original.original_tax_ids.ids
        assert destination_tax.original_tax_ids.ids == [source_tax_id]
        assert set(destination_tax.fiscal_position_ids.ids) == before_positions
    removed = min(copy_position.account_ids.ids)
    _write(
        client,
        alias,
        run_id,
        "fiscal_position.account_mapping.delete",
        {"account_mapping_id": removed},
        replay=False,
    )
    assert not env["account.fiscal.position.account"].browse(removed).exists()
    remaining = set(copy_position.account_ids.ids)
    assert len(remaining) == 1
    _write(
        client,
        alias,
        run_id,
        "fiscal_position.delete",
        {"fiscal_position_id": copy_position.id},
        replay=False,
    )
    assert not copy_position.exists()
    assert not env["account.fiscal.position.account"].browse(sorted(remaining)).exists()
    assert set(position.account_ids.ids) == source_mapping_ids
    assert (
        position.tax_ids.ids == [destination_tax_id]
        and source_tax.exists()
        and destination_tax.exists()
    )
    assert client.capabilities == _WRITES | _READS | _SETUP


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
    marker = f"ODACV4-FISCAL-MAPPING-{args.alias}-{args.run_id.hex}"
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
            admin_env["account.fiscal.position"]
            .with_company(2)
            .create(
                {
                    "name": marker + "-FOREIGN",
                    "company_id": 2,
                }
            )
        )
        tracked["account.fiscal.position"].add(foreign.id)
        try:
            _write(
                client,
                args.alias,
                args.run_id,
                "fiscal_position.delete",
                {
                    "fiscal_position_id": foreign.id,
                },
                replay=False,
            )
        except AssertionError:
            assert (
                getattr(client.last_runtime_failure, "code", None) == "record_not_found"
            )
            assert foreign.exists()
        else:
            raise RuntimeError("a company-2 fiscal position escaped company-1 scope")
        _exercise(client, args.alias, args.run_id, marker)
    except BaseException as exc:  # noqa: BLE001 - rollback also covers failed fixtures.
        failure = exc
    finally:
        try:
            if admin_env is not None:
                admin_env.invalidate_all()
                marked = admin_env["account.fiscal.position"].search(
                    [("name", "ilike", marker)]
                )
                tracked["account.fiscal.position"].update(marked.ids)
                tracked["account.fiscal.position.account"].update(
                    marked.account_ids.ids
                )
                taxes = (
                    admin_env["account.tax"]
                    .with_context(active_test=False)
                    .search([("name", "ilike", marker)])
                )
                tracked["account.tax"].update(taxes.ids)
                tracked["account.tax.repartition.line"].update(
                    taxes.repartition_line_ids.ids
                )
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
            assert not verify_env["account.fiscal.position"].search_count(
                [("name", "ilike", marker)]
            )
            assert (
                not verify_env["account.tax"]
                .with_context(active_test=False)
                .search_count([("name", "ilike", marker)])
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
                "source_mappings": 2,
                "detached_tax_copies": 2,
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
