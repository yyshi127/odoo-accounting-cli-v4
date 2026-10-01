"""One guarded rollback-only workflow for payment definitions and journal configuration."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import sysconfig
import uuid
from pathlib import Path

import test_document_lifecycle_write_batch_live as lifecycle
import test_payment_bank_capability_batch_live as core
import test_report_budget_write_batch_live as shared

try:
    import pytest
except ModuleNotFoundError:
    if "--live-worker" not in sys.argv:
        raise
    pytest = None

_ALLOW_ENV = "ODACV4_ALLOW_PAYMENT_CONFIGURATION_SMOKE"
_GROUPS = ("account.group_account_manager", "base.group_partner_manager")
_WRITES = {
    "payment.method_line.create",
    "payment.method_line.update",
    "payment.method_line.duplicate",
    "payment.method_line.remove",
    "journal.liquidity_configuration.update",
    "journal.bank_account.assign",
}
_READS = {"payment.method_definition.list", "payment.method_definition.get"}
_SETUP = {
    "journal.create",
    "partner.bank_account.create",
    "payment.create",
    "payment.post",
}
_MODELS = (
    "account.journal",
    "account.payment.method.line",
    "account.account",
    "res.partner.bank",
    "res.partner",
    "account.payment",
    "account.move",
    "account.move.line",
)


def _root():
    return Path(__file__).resolve().parents[2]


if pytest is not None:

    @pytest.mark.integration
    def test_payment_configuration_rolls_back_per_alias():
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
                "immediate_replays": 5,
                "native_account_reconcile_enabled": True,
                "copy_account_preserved": True,
                "used_line_detached_history_retained": True,
                "unused_line_deleted": True,
                "cross_company_rejected": True,
                "rollback_verified": True,
                "temporary_groups_rolled_back": True,
                "execution": "in_process_cli_real_orm",
            }
            print(completed.stdout.strip(), flush=True)


class _Client(shared._Client):
    def __init__(self, env):
        super().__init__(env)
        self.tracked = {model: set() for model in _MODELS}

    def invoke(self, action, payload):
        page = super().invoke(action, payload)
        result = page.get("result")
        if isinstance(result, dict):
            if result["model"] == "account.journal":
                journal = self.env["account.journal"].browse(result["id"])
                self.tracked["account.account"].update(journal.default_account_id.ids)
                self.tracked["account.payment.method.line"].update(
                    (
                        journal.inbound_payment_method_line_ids
                        | journal.outbound_payment_method_line_ids
                    ).ids
                )
            elif result["model"] == "account.payment":
                payment = self.env["account.payment"].browse(result["id"])
                self.tracked["account.move"].update(payment.move_id.ids)
                self.tracked["account.move.line"].update(payment.move_id.line_ids.ids)
        return page


def _exercise(client, alias, run_id, marker):
    from odoo_accounting_cli_v4.capabilities.core_writes import (
        _expected_idempotency_key,
        validate_core_write_request,
    )

    env = client.env
    definitions = shared._read(
        client, alias, run_id, "payment.method_definition.list", {"limit": 1000}
    )
    method = next(
        row
        for row in definitions["items"]
        if row["code"] == "manual" and row["payment_type"] == "inbound"
    )
    assert (
        shared._read(
            client,
            alias,
            run_id,
            "payment.method_definition.get",
            {"payment_method_id": method["id"]},
        )
        == method
    )
    accounts = {}
    for index, kind in enumerate(("asset_current", "income", "expense")):
        account = env["account.account"].create(
            {
                "name": marker + "-" + kind,
                "code": "P" + run_id.hex[:12] + str(index),
                "account_type": kind,
                "company_ids": [(6, 0, [1])],
                "reconcile": False,
            }
        )
        accounts[kind] = account
        client.tracked["account.account"].add(account.id)
    journal_id = shared._write(
        client,
        alias,
        run_id,
        "journal.create",
        {"name": marker, "code": "P" + run_id.hex[:4], "type": "bank"},
        replay=False,
    )["id"]
    journal = env["account.journal"].browse(journal_id)
    shared._write(
        client,
        alias,
        run_id,
        "journal.liquidity_configuration.update",
        {
            "journal_id": journal_id,
            "changes": {
                "suspense_account_id": accounts["asset_current"].id,
                "profit_account_id": accounts["income"].id,
                "loss_account_id": accounts["expense"].id,
            },
        },
    )
    bank_id = shared._write(
        client,
        alias,
        run_id,
        "partner.bank_account.create",
        {"partner_id": env.company.partner_id.id, "account_number": marker + "-BANK"},
        replay=False,
    )["id"]
    shared._write(
        client,
        alias,
        run_id,
        "journal.bank_account.assign",
        {"journal_id": journal_id, "partner_bank_id": bank_id},
    )
    assert journal.bank_account_id.id == bank_id
    created = shared._write(
        client,
        alias,
        run_id,
        "payment.method_line.create",
        {
            "journal_id": journal_id,
            "payment_method_id": method["id"],
            "name": marker + "-RECEIPT",
            "sequence": 20,
            "payment_account_id": accounts["asset_current"].id,
        },
    )
    line_id = created["id"]
    assert accounts["asset_current"].reconcile
    shared._write(
        client,
        alias,
        run_id,
        "payment.method_line.update",
        {
            "payment_method_line_id": line_id,
            "changes": {"name": marker + "-UPDATED", "sequence": 7},
        },
    )
    copied = shared._write(
        client,
        alias,
        run_id,
        "payment.method_line.duplicate",
        {"payment_method_line_id": line_id, "name": marker + "-COPY"},
    )
    assert (
        env["account.payment.method.line"].browse(copied["id"]).payment_account_id.id
        == accounts["asset_current"].id
    )
    removed = shared._write(
        client,
        alias,
        run_id,
        "payment.method_line.remove",
        {"payment_method_line_id": copied["id"]},
        replay=False,
    )
    assert (
        removed["state"] == "deleted"
        and not env["account.payment.method.line"].browse(copied["id"]).exists()
    )
    partner = env["res.partner"].create({"name": marker + "-CUSTOMER", "company_id": 1})
    client.tracked["res.partner"].add(partner.id)
    params = {
        "payment_type": "inbound",
        "partner_type": "customer",
        "partner_id": partner.id,
        "amount": "10",
        "currency_id": env.company.currency_id.id,
        "journal_id": journal_id,
        "payment_method_line_id": line_id,
        "date": "2026-10-01",
        "payment_reference": marker,
    }
    payment = core._cli(
        client,
        alias,
        run_id,
        "payment.create",
        params,
        key="payment-config:" + run_id.hex,
    )["result"]
    post_params = {"payment_id": payment["id"]}
    normalized = validate_core_write_request(
        "payment.post", core._request(alias, run_id, "payment.post", post_params)
    )[2]
    core._cli(
        client,
        alias,
        run_id,
        "payment.post",
        post_params,
        key=_expected_idempotency_key("payment.post", normalized, 1),
    )
    native_payment = env["account.payment"].browse(payment["id"])
    history = (
        native_payment.payment_method_line_id.id,
        native_payment.journal_id.id,
        native_payment.move_id.id,
    )
    removed = shared._write(
        client,
        alias,
        run_id,
        "payment.method_line.remove",
        {"payment_method_line_id": line_id},
        replay=False,
    )
    assert removed["state"] == "detached"
    assert (
        env["account.payment.method.line"].browse(line_id).exists()
        and not env["account.payment.method.line"].browse(line_id).journal_id
    )
    assert history == (
        native_payment.payment_method_line_id.id,
        native_payment.journal_id.id,
        native_payment.move_id.id,
    )
    assert native_payment.exists() and native_payment.move_id.state == "posted"
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
    marker = f"ODACV4-PAYMENT-CONFIG-{args.alias}-{args.run_id.hex}"
    tracked = {model: set() for model in _MODELS}
    baselines = {}
    failure = None
    try:
        context = {"allowed_company_ids": [1], "lang": "en_US", "tz": "Asia/Shanghai"}
        admin = api.Environment(cursor, SUPERUSER_ID, context)
        user = admin["res.users"].browse(5).exists()
        assert (
            user.active
            and user.login == lifecycle._USER_LOGIN
            and 1 in user.company_ids.ids
        )
        for group in _GROUPS:
            group_id = admin.ref(group).id
            baselines[group_id] = shared._direct_group(cursor, group_id)
            if not user.has_group(group):
                user.write({"group_ids": [Command.link(group_id)]})
        admin.flush_all()
        env = api.Environment(cursor, 5, context)
        assert not env.su and all(env.user.has_group(group) for group in _GROUPS)
        client = _Client(env)
        tracked = client.tracked
        assert admin["res.company"].browse(2).exists()
        foreign = (
            admin["account.journal"]
            .with_company(2)
            .create(
                {
                    "name": marker + "-FOREIGN",
                    "code": "Q" + args.run_id.hex[:4],
                    "type": "bank",
                    "company_id": 2,
                }
            )
        )
        tracked["account.journal"].add(foreign.id)
        tracked["account.account"].update(foreign.default_account_id.ids)
        foreign_lines = (
            foreign.inbound_payment_method_line_ids
            | foreign.outbound_payment_method_line_ids
        )
        tracked["account.payment.method.line"].update(foreign_lines.ids)
        target = foreign_lines[:1]
        assert target
        try:
            shared._write(
                client,
                args.alias,
                args.run_id,
                "payment.method_line.remove",
                {"payment_method_line_id": target.id},
                replay=False,
            )
        except AssertionError:
            assert (
                getattr(client.last_runtime_failure, "code", None) == "record_not_found"
                and target.exists()
            )
        else:
            raise RuntimeError("A company-2 payment method escaped company-1 scope")
        _exercise(client, args.alias, args.run_id, marker)
    except BaseException as exc:  # noqa: BLE001 - failed fixtures must roll back too.
        failure = exc
    finally:
        cursor.rollback()
        cursor.close()
    with registry.cursor() as verify_cursor:
        try:
            verify = api.Environment(
                verify_cursor, SUPERUSER_ID, {"allowed_company_ids": [1, 2]}
            )
            for model, ids in tracked.items():
                assert (
                    not verify[model]
                    .with_context(active_test=False)
                    .search_count([("id", "in", sorted(ids))])
                )
            for model in (
                "account.journal",
                "account.account",
                "res.partner",
                "account.payment.method.line",
            ):
                assert (
                    not verify[model]
                    .with_context(active_test=False)
                    .search_count([("name", "ilike", marker)])
                )
            assert (
                not verify["res.partner.bank"]
                .with_context(active_test=False)
                .search_count([("acc_number", "ilike", marker)])
            )
            for group_id, baseline in baselines.items():
                assert shared._direct_group(verify_cursor, group_id) == baseline
        finally:
            verify_cursor.rollback()
    if failure is not None:
        raise failure
    print(
        json.dumps(
            {
                "alias": args.alias,
                "database": args.database,
                "company_id": 1,
                "user_id": 5,
                "business_su": False,
                "capabilities": sorted(client.capabilities),
                "immediate_replays": 5,
                "native_account_reconcile_enabled": True,
                "copy_account_preserved": True,
                "used_line_detached_history_retained": True,
                "unused_line_deleted": True,
                "cross_company_rejected": True,
                "rollback_verified": True,
                "temporary_groups_rolled_back": True,
                "execution": "in_process_cli_real_orm",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_live_worker())
