"""One guarded rollback-only workflow for native invoice/entry processing."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import sysconfig
import uuid
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import test_document_lifecycle_write_batch_live as lifecycle
import test_payment_bank_capability_batch_live as core
import test_payment_configuration_batch_live as payment
import test_report_budget_write_batch_live as shared

try:
    import pytest
except ModuleNotFoundError:
    if "--live-worker" not in sys.argv:
        raise
    pytest = None

_ALLOW_ENV = "ODACV4_ALLOW_MOVE_PROCESSING_SMOKE"
_GROUPS = ("account.group_account_manager", "base.group_multi_currency")
_WRITES = {
    "invoice.currency_rate.update", "invoice.currency_rate.refresh",
    "invoice.cash_rounding.assign", "invoice.incoterm.update",
    "invoice.payment_method.assign", "invoice.payment_block.set",
    "accounting_move.review.set", "accounting_move.autopost.configure",
}
_READ = "accounting_move.processing_settings.get"
_SETUP = {"customer_invoice.create", "journal_entry.create", "journal_entry.lines.replace", "journal.create", "invoice.post"}


def _root():
    return Path(__file__).resolve().parents[2]


def _summary(alias, database):
    return {
        "alias": alias, "database": database, "company_id": 1, "user_id": 5,
        "business_su": False, "capabilities": sorted(_WRITES | {_READ} | _SETUP),
        "immediate_replays": 8, "foreign_currency_balances_recomputed": True,
        "native_cash_rounding_line_verified": True, "native_rate_refresh_verified": True,
        "native_block_and_review_verified": True, "schedule_saved_without_posting": True,
        "draft_and_direction_boundaries_verified": True, "cross_company_rejected": True,
        "rollback_verified": True, "temporary_groups_and_currency_fixture_rolled_back": True,
        "execution": "in_process_cli_real_orm",
    }


if pytest is not None:

    @pytest.mark.integration
    def test_move_processing_rolls_back_per_alias():
        config_path, runtime = lifecycle._enabled_runtime(_ALLOW_ENV)
        run_id = uuid.uuid4()
        for alias in lifecycle._ALIASES:
            command, timeout = lifecycle._worker_command(alias, run_id, config_path, runtime)
            command[1] = str(Path(__file__).resolve())
            environment = os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            environment["PYTHONPATH"] = os.pathsep.join(filter(None, (
                str(_root() / "src"), sysconfig.get_path("purelib"), environment.get("PYTHONPATH"),
            )))
            completed = subprocess.run(command, cwd=_root(), env=environment, text=True,
                                       capture_output=True, check=False, timeout=max(timeout, 900))
            assert completed.returncode == 0, completed.stdout + completed.stderr
            result = json.loads(completed.stdout)
            assert result == _summary(alias, lifecycle._DATABASES[alias])
            print(completed.stdout.strip(), flush=True)


class _Client(payment._Client):
    def invoke(self, action, payload):
        page = super().invoke(action, payload)
        result = page.get("result")
        if isinstance(result, dict) and result["model"] == "account.move":
            self.tracked["account.move.line"].update(result["line_ids"])
        return page


def _currency_state(cursor, currency_id):
    cursor.execute("SELECT active FROM res_currency WHERE id=%s", [currency_id])
    active = cursor.fetchone()[0]
    cursor.execute("SELECT id,name,company_id,rate FROM res_currency_rate WHERE currency_id=%s ORDER BY id", [currency_id])
    return active, cursor.fetchall()


def _exercise(client, alias, run_id, marker, fx_currency_id, rounding_id, foreign_id):
    from odoo import fields

    from odoo_accounting_cli_v4 import move_processing_contracts as contracts

    env = client.env
    ids = lifecycle._fixture_ids(env, alias)
    today = fields.Date.context_today(env.user)
    today_text = today.isoformat()
    invoice = core._cli(client, alias, run_id, "customer_invoice.create", {
        "partner_id": ids["customer"], "journal_id": ids["sale_journal"],
        "date": today_text, "invoice_date": today_text, "currency_id": fx_currency_id,
        "reference": marker, "lines": [{"name": marker, "account_id": ids["income"],
        "product_id": None, "quantity": "1", "price_unit": "21.02", "discount": "0", "tax_ids": []}],
    }, key=marker + "-invoice")["result"]
    move_id = invoice["id"]
    move = env["account.move"].browse(move_id)
    def read(target=move_id):
        client.last_runtime_failure = None
        try:
            return shared._read(client, alias, run_id, _READ, {"move_id": target})
        except AssertionError:
            if client.last_runtime_failure is not None:
                raise client.last_runtime_failure
            raise
    write = lambda cap, params, replay=True: shared._write(client, alias, run_id, cap,
                                       {"move_id": move_id, **params}, replay=replay)
    first = read()
    assert first["currency_id"] != first["company_currency_id"]
    expected = Decimal(first["expected_currency_rate"])
    manual = contracts.native_decimal(float(expected) * 2)
    before_balance = move.invoice_line_ids.balance
    write("invoice.currency_rate.update", {"rate": manual})
    move.invalidate_recordset()
    line = move.invoice_line_ids
    assert line.balance != before_balance and Decimal(read()["invoice_currency_rate"]) == Decimal(manual)
    assert env.company.currency_id.is_zero(line.balance - env.company.currency_id.round(line.amount_currency / float(manual)))
    write("invoice.currency_rate.refresh", {})
    move.invalidate_recordset()
    assert Decimal(read()["invoice_currency_rate"]) == expected
    assert env.company.currency_id.is_zero(move.invoice_line_ids.balance - before_balance)
    write("invoice.cash_rounding.assign", {"cash_rounding_id": rounding_id})
    move.invalidate_recordset()
    assert read()["invoice_cash_rounding_id"] == rounding_id
    assert len(move.line_ids.filtered(lambda row: row.display_type == "rounding")) == 1
    assert Decimal(str(move.amount_total)) == Decimal("21.0")
    incoterm = env["account.incoterms"].search([], order="id", limit=1)
    assert incoterm
    write("invoice.incoterm.update", {"changes": {"incoterm_id": incoterm.id, "incoterm_location": "Synthetic dock"}})
    assert read()["invoice_incoterm_id"] == incoterm.id and read()["incoterm_location"] == "Synthetic dock"
    journal_id = shared._write(client, alias, run_id, "journal.create", {
        "name": marker, "code": "S" + run_id.hex[:4], "type": "bank",
    }, replay=False)["id"]
    journal = env["account.journal"].browse(journal_id)
    inbound, outbound = journal.inbound_payment_method_line_ids[:1], journal.outbound_payment_method_line_ids[:1]
    assert inbound and outbound
    write("invoice.payment_method.assign", {"payment_method_line_id": inbound.id})
    assert read()["preferred_payment_method_line_id"] == inbound.id
    try:
        write("invoice.payment_method.assign", {"payment_method_line_id": outbound.id}, replay=False)
    except AssertionError:
        assert getattr(client.last_runtime_failure, "code", None) == "business_rule_error"
    else:
        raise RuntimeError("A wrong-direction invoice payment method succeeded")
    assert read()["preferred_payment_method_line_id"] == inbound.id
    entry = core._cli(client, alias, run_id, "journal_entry.create", {
        "journal_id": ids["general_journal"], "date": (today + timedelta(days=30)).isoformat(),
        "reference": marker + "-ENTRY",
        "lines": [{"name": marker, "account_id": ids["expense"], "partner_id": None,
                   "debit": "5", "credit": "0", "currency_id": None, "amount_currency": None},
                  {"name": marker, "account_id": ids["asset"], "partner_id": None,
                   "debit": "0", "credit": "5", "currency_id": None, "amount_currency": None}],
    }, key=marker + "-entry")["result"]
    shared._write(client, alias, run_id, "journal_entry.lines.replace", {
        "move_id": entry["id"],
        "lines": [{"name": marker + "-REPLACED", "account_id": ids["expense"], "partner_id": None,
                   "debit": "5", "credit": "0", "currency_id": None, "amount_currency": None},
                  {"name": marker + "-REPLACED", "account_id": ids["asset"], "partner_id": None,
                   "debit": "0", "credit": "5", "currency_id": None, "amount_currency": None}],
    }, replay=False)
    assert all(row.currency_id == env.company.currency_id and row.amount_currency == row.balance
               for row in env["account.move"].browse(entry["id"]).line_ids)
    shared._write(client, alias, run_id, "accounting_move.autopost.configure", {
        "move_id": entry["id"], "auto_post": "monthly", "auto_post_until": (today + timedelta(days=365)).isoformat(),
    })
    scheduled = read(entry["id"])
    assert scheduled["state"] == "draft" and scheduled["auto_post"] == "monthly" and scheduled["auto_post_origin_id"] is None
    try:
        shared._write(client, alias, run_id, "accounting_move.autopost.configure", {
            "move_id": foreign_id, "auto_post": "at_date", "auto_post_until": None,
        }, replay=False)
    except AssertionError:
        assert getattr(client.last_runtime_failure, "code", None) == "record_not_found"
    else:
        raise RuntimeError("A foreign-company move escaped scope")
    core._cli(client, alias, run_id, "invoice.post", {"move_id": move_id}, key=f"invoice.post:{move_id}")
    write("invoice.payment_block.set", {"blocked": True})
    assert read()["payment_state"] == "blocked"
    write("invoice.payment_block.set", {"blocked": False}, replay=False)
    assert read()["payment_state"] != "blocked"
    write("accounting_move.review.set", {"checked": False})
    assert read()["checked"] is False
    for cap, params in (("invoice.currency_rate.refresh", {}), ("accounting_move.review.set", {"checked": True})):
        target = move_id if cap.startswith("invoice.") else entry["id"]
        try:
            shared._write(client, alias, run_id, cap, {"move_id": target, **params}, replay=False)
        except AssertionError:
            assert getattr(client.last_runtime_failure, "code", None) == "state_conflict"
        else:
            raise RuntimeError("An invalid native move state succeeded")
    assert read()["state"] == "posted" and read(entry["id"])["state"] == "draft"
    assert client.capabilities == _WRITES | {_READ} | _SETUP


def _live_worker():
    args = lifecycle._arguments(None)
    assert not (args.refund_only or args.payment_difference_only or args.analytic_readback_only)
    sys.path.insert(0, str(args.odoo_source.resolve(strict=True)))
    sys.path.insert(0, str(_root() / "src"))
    from odoo import SUPERUSER_ID, Command, api, fields
    from odoo.orm.registry import Registry
    from odoo.tools import config

    config.parse_config(["--config", str(args.odoo_config.resolve(strict=True)),
                         "--database", args.database, "--no-http", "--logfile=/dev/null"])
    registry = Registry(args.database)
    cursor = registry.cursor()
    marker = f"ODACV4-MOVE-PROCESS-{args.alias}-{args.run_id.hex}"
    tracked = {model: set() for model in (*payment._MODELS, "account.cash.rounding")}
    groups = {}
    currency_id = baseline_currency = None
    failure = None
    try:
        context = {"allowed_company_ids": [1], "lang": "en_US", "tz": "Asia/Shanghai",
                   "tracking_disable": True, "mail_create_nosubscribe": True, "mail_notrack": True}
        admin = api.Environment(cursor, SUPERUSER_ID, context)
        user = admin["res.users"].browse(5).exists()
        assert user.active and user.login == lifecycle._USER_LOGIN and 1 in user.company_ids.ids
        for group in _GROUPS:
            group_id = admin.ref(group).id
            groups[group_id] = shared._direct_group(cursor, group_id)
            if not user.has_group(group): user.write({"group_ids": [Command.link(group_id)]})
        currency = admin["res.currency"].with_context(active_test=False).search([("id", "!=", admin.company.currency_id.id)], order="id", limit=1)
        assert currency
        currency_id = currency.id
        baseline_currency = _currency_state(cursor, currency_id)
        currency.write({"active": True})
        today = fields.Date.context_today(user)
        rate = admin["res.currency.rate"].search([("currency_id", "=", currency_id), ("company_id", "=", 1), ("name", "=", today)], limit=1)
        if rate: rate.write({"rate": 1.2})
        else: admin["res.currency.rate"].create({"currency_id": currency_id, "company_id": 1, "name": today, "rate": 1.2})
        admin.flush_all()
        env = api.Environment(cursor, 5, context)
        assert not env.su and all(env.user.has_group(group) for group in _GROUPS)
        client = _Client(env)
        client.tracked = tracked
        ids = lifecycle._fixture_ids(env, args.alias)
        rounding = admin["account.cash.rounding"].create({"name": marker, "rounding": .05,
            "strategy": "add_invoice_line", "rounding_method": "HALF-UP",
            "profit_account_id": ids["income"], "loss_account_id": ids["expense"]})
        tracked["account.cash.rounding"].add(rounding.id)
        foreign_journal = admin["account.journal"].with_company(2).create({"name": marker + "-FOREIGN", "code": "T" + args.run_id.hex[:4], "type": "general", "company_id": 2})
        tracked["account.journal"].add(foreign_journal.id)
        foreign = admin["account.move"].with_company(2).create({"journal_id": foreign_journal.id, "company_id": 2, "move_type": "entry", "date": today})
        tracked["account.move"].add(foreign.id)
        _exercise(client, args.alias, args.run_id, marker, currency_id, rounding.id, foreign.id)
    except BaseException as exc:  # noqa: BLE001 - failed synthetic fixtures must roll back too.
        failure = exc
    finally:
        cursor.rollback()
        cursor.close()
    with registry.cursor() as verify_cursor:
        try:
            verify = api.Environment(verify_cursor, SUPERUSER_ID, {"allowed_company_ids": [1, 2]})
            for model, ids in tracked.items():
                assert not verify[model].with_context(active_test=False).search_count([("id", "in", sorted(ids))])
            for model in ("account.move", "account.journal", "account.cash.rounding"):
                assert not verify[model].with_context(active_test=False).search_count([("name" if model != "account.move" else "ref", "ilike", marker)])
            if currency_id is not None: assert _currency_state(verify_cursor, currency_id) == baseline_currency
            assert all(shared._direct_group(verify_cursor, group_id) == baseline for group_id, baseline in groups.items())
        finally:
            verify_cursor.rollback()
    if failure is not None: raise failure
    print(json.dumps(_summary(args.alias, args.database), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_live_worker())
