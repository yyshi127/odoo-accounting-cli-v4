"""One ordinary-user bank workflow with full fresh-cursor fixture rollback."""

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

import test_accounting_settlement_batch_live as settlement

maintenance, lifecycle, core = settlement.maintenance, settlement.lifecycle, settlement.core

try:
    import pytest
except ModuleNotFoundError:
    if "--live-worker" not in sys.argv:
        raise
    pytest = None

_ALLOW_ENV = "ODACV4_ALLOW_BANK_SETTLEMENT_INPUTS_SMOKE"
_TARGETS = {"bank.transaction.record", "bank.transaction.update", "bank.transaction.get",
            "bank.transaction.search", "bank.statement.create", "bank.statement.update",
            "bank.statement.search", "bank.transaction.unmatch", "bank.transaction.counterparts.replace"}
_MODELS = tuple(dict.fromkeys((*settlement._MODELS, "res.partner", "res.partner.bank")))


def _root():
    return Path(__file__).resolve().parents[2]


def _summary(alias, database):
    return {"alias": alias, "database": database, "company_id": 1, "user_id": 5, "business_su": False,
            "target_capabilities": sorted(_TARGETS), "execution": "in_process_cli_real_orm",
            "bank_metadata_native_partner_consumers_set_clear_get_and_replays_verified": True,
            "statement_titles_dates_assignment_complete_valid_native_filters_paging_verified": True,
            "signed_split_counterparts_replace_replay_liquidity_and_manual_undo_verified": True,
            "conditional_bank_creation_native_acl_denial_existing_bank_and_temporary_native_role_verified": True,
            "foreign_unbalanced_matched_update_denials_preserve_native_graph_verified": True,
            "full_fixtures_settings_defaults_currency_rates_and_all_user_groups_fresh_rollback_verified": True}


if pytest is not None:
    @pytest.mark.integration
    def test_bank_settlement_inputs_roll_back_per_alias():
        config_path, runtime = lifecycle._enabled_runtime(_ALLOW_ENV)
        run_id = uuid.uuid4()
        for alias in lifecycle._ALIASES:
            command, timeout = lifecycle._worker_command(alias, run_id, config_path, runtime)
            command[1] = str(Path(__file__).resolve())
            environment = os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            environment["PYTHONPATH"] = os.pathsep.join(filter(None, (str(_root() / "src"), sysconfig.get_path("purelib"), environment.get("PYTHONPATH"))))
            completed = subprocess.run(command, cwd=_root(), env=environment, text=True, capture_output=True, check=False, timeout=max(timeout, 900))
            assert completed.returncode == 0, completed.stdout + completed.stderr
            assert json.loads(completed.stdout) == _summary(alias, lifecycle._DATABASES[alias])
            print(completed.stdout.strip(), flush=True)


def _exercise(admin, client, alias, run_id, marker):
    from odoo import Command, fields

    from odoo_accounting_cli_v4.capabilities.core_writes import (
        _expected_idempotency_key,
        validate_core_write_request,
    )

    env = client.env
    today = fields.Date.context_today(env.user)
    assert env.uid == 5 and not env.su and env.company.id == 1

    def track(record):
        client.tracked[record._name].update(record.ids)
        if record._name == "account.journal":
            client.tracked["mail.alias"].update(record.alias_id.ids)
            client.tracked["account.payment.method.line"].update((record.inbound_payment_method_line_ids | record.outbound_payment_method_line_ids).ids)
        if record._name == "account.bank.statement.line":
            client.tracked["account.move"].update(record.move_id.ids)
            client.tracked["account.move.line"].update(record.move_id.line_ids.ids)
            client.tracked["res.partner.bank"].update(record.partner_bank_id.ids)
        return record

    def fixture(model, values, *, company=1):
        return track(admin[model].with_company(admin["res.company"].browse(company)).create(values))

    def account(label, account_type, *, company=1, reconcile=False):
        return fixture("account.account", {"name": marker + label, "code": "B" + uuid.uuid5(run_id, label).hex[:9],
                       "account_type": account_type, "reconcile": reconcile, "company_ids": [Command.set([company])]}, company=company)

    def call(capability, parameters, **kwargs):
        return maintenance._call(client, alias, run_id, capability, parameters, **kwargs)

    def key_for(capability, parameters):
        normalized = validate_core_write_request(capability, core._request(alias, run_id, capability, parameters))[2]
        return _expected_idempotency_key(capability, normalized, 1) or f"{capability}:{run_id.hex}:{lifecycle._canonical_digest(normalized)[:32]}"

    def write(capability, parameters, *, replay=False):
        key = key_for(capability, parameters)
        first = call(capability, parameters, key=key)
        assert not first["idempotent_replay"], first
        if replay:
            second = call(capability, parameters, key=key)
            assert second["idempotent_replay"] and second["result"] == first["result"], second
        if first["result"]["model"] == "account.bank.statement.line":
            track(env["account.bank.statement.line"].browse(first["result"]["id"]))
        return first["result"]

    def denied(capability, parameters, error, code, *, move=None):
        before = maintenance._graph(move) if move is not None else None
        response = call(capability, parameters, key=key_for(capability, parameters), exit_code=code)
        assert response["error"]["code"] in ({error} if isinstance(error, str) else error), response
        env.invalidate_all()
        if move is not None:
            assert maintenance._graph(move) == before, response

    def pages(capability, parameters):
        query, rows = {**parameters, "limit": 1}, []
        while True:
            page = call(capability, query)
            rows.extend(page["items"])
            if not page["has_more"]:
                return rows
            query["cursor"] = page["next_cursor"]

    liquidity = account("liquidity", "asset_cash", reconcile=True)
    suspense = account("suspense", "asset_current", reconcile=True)
    expense, expense_other, income = account("expense", "expense"), account("expense-other", "expense_other"), account("income", "income")
    bank = fixture("account.journal", {"name": marker + "bank", "code": "B" + run_id.hex[:4], "type": "bank", "company_id": 1,
                   "default_account_id": liquidity.id, "suspense_account_id": suspense.id})
    payer = fixture("res.partner", {"name": marker + "payer", "company_id": 1})
    named_payer = fixture("res.partner", {"name": marker + "named-payer", "company_id": 1})
    account_number = "V4" + run_id.hex
    existing_bank = fixture("res.partner.bank", {"partner_id": payer.id, "acc_number": account_number})

    def transaction(label, amount, offset, **extra):
        value = write("bank.transaction.record", {"journal_id": bank.id, "date": (today + timedelta(days=offset)).isoformat(), "amount": amount,
                      "payment_ref": marker + label, "partner_id": None, **extra}, replay=True)
        return env["account.bank.statement.line"].browse(value["id"])

    first = transaction("account-payer", "40", 0, account_number=account_number)
    second = transaction("name-payer", "60", 1, partner_name=named_payer.name)
    assert first.partner_id == payer.with_env(env) and second.partner_id == named_payer.with_env(env)
    orphan = transaction("orphan", "20", 2, partner_id=payer.id, account_number=None, partner_name=None)
    for line in (first, second, orphan):
        data = call("bank.transaction.get", {"transaction_id": line.id})
        assert data["account_number"] == (line.account_number or None) and data["partner_name"] == (line.partner_name or None)
    before = maintenance._graph(orphan.move_id)
    metadata = {"account_number": "V4NEW" + run_id.hex, "partner_name": payer.name}
    write("bank.transaction.update", {"transaction_id": orphan.id, "changes": metadata}, replay=True)
    assert maintenance._graph(orphan.move_id) == before
    assert {key: call("bank.transaction.get", {"transaction_id": orphan.id})[key] for key in metadata} == metadata
    write("bank.transaction.update", {"transaction_id": orphan.id, "changes": {key: None for key in metadata}}, replay=True)
    assert maintenance._graph(orphan.move_id) == before
    write("bank.transaction.update", {"transaction_id": orphan.id, "changes": metadata}, replay=True)
    assert {row["id"] for row in pages("bank.transaction.search", {"journal_id": bank.id, "statement_assignment": "unassigned"})} == {first.id, second.id, orphan.id}
    assert not pages("bank.transaction.search", {"journal_id": bank.id, "statement_assignment": "assigned"})

    statement_params = {"reference": marker + "external", "transaction_ids": [first.id], "balance_start": "0", "balance_end_real": "40",
                        "name": marker + "title", "date": (today - timedelta(days=7)).isoformat()}
    statement_id = write("bank.statement.create", statement_params, replay=True)["id"]
    next_id = write("bank.statement.create", {"reference": None, "transaction_ids": [second.id], "balance_start": "40", "balance_end_real": "100",
                    "name": marker + "next", "date": (today - timedelta(days=6)).isoformat()}, replay=True)["id"]
    snapshots = {line.id: maintenance._graph(line.move_id) for line in (first, second, orphan)}
    statement = env["account.bank.statement"].browse(statement_id)
    assert statement.name == statement_params["name"] and statement.date.isoformat() == statement_params["date"]
    changes = {"name": marker + "corrected-title", "date": (today - timedelta(days=5)).isoformat()}
    write("bank.statement.update", {"statement_id": statement.id, "changes": changes}, replay=True)
    readback = call("bank.statement.get", {"bank_statement_id": statement.id})
    assert readback["name"] == changes["name"] and readback["date"] == changes["date"]
    assert all(maintenance._graph(line.move_id) == snapshots[line.id] for line in (first, second, orphan))
    assert {row["id"] for row in pages("bank.transaction.search", {"journal_id": bank.id, "statement_assignment": "assigned"})} == {first.id, second.id}
    assert {row["id"] for row in pages("bank.transaction.search", {"journal_id": bank.id, "statement_assignment": "unassigned"})} == {orphan.id}
    assert {row["id"] for row in pages("bank.statement.search", {"journal_id": bank.id, "is_complete": True, "is_valid": True})} == {statement.id, next_id}
    # Native start changes recompute end_real; explicitly retain 100 to create a real discrepancy.
    write("bank.statement.update", {"statement_id": next_id, "changes": {"balance_start": "50", "balance_end_real": "100"}}, replay=True)
    abnormal = env["account.bank.statement"].browse(next_id)
    assert not abnormal.is_complete and not abnormal.is_valid
    assert {row["id"] for row in pages("bank.statement.search", {"journal_id": bank.id, "is_complete": False, "is_valid": False})} == {next_id}
    assert {row["id"] for row in pages("bank.statement.search", {"journal_id": bank.id, "is_valid": True})} == {statement.id}
    write("bank.statement.update", {"statement_id": next_id, "changes": {"balance_start": "40"}}, replay=True)

    def counterparts(line, rows):
        original_liquidity = line._seek_for_lines()[0]
        snapshot = original_liquidity.read(["id", "account_id", "balance", "debit", "credit", "currency_id", "amount_currency"], load=None)
        write("bank.transaction.counterparts.replace", {"transaction_id": line.id, "lines": rows}, replay=True)
        native_liquidity, native_suspense, native_other = line._seek_for_lines()
        assert native_liquidity.read(["id", "account_id", "balance", "debit", "credit", "currency_id", "amount_currency"], load=None) == snapshot
        assert not native_suspense and line.is_reconciled and line.move_id.state == "posted"
        assert not (line.move_id.line_ids.matched_debit_ids | line.move_id.line_ids.matched_credit_ids)
        actual = sorted((item.account_id.id, item.name, Decimal(str(item.balance))) for item in native_other)
        expected = sorted((row["account_id"], row["label"], Decimal(row["balance"])) for row in rows)
        assert actual == expected and sum(line.move_id.line_ids.mapped("balance")) == 0

    negative = transaction("fees", "-100", 3)
    rows = [{"account_id": expense.id, "label": marker + "fee-A", "balance": "70"},
            {"account_id": expense_other.id, "label": marker + "fee-B", "balance": "30"}]
    counterparts(negative, rows)
    replacement = [{"account_id": expense.id, "label": marker + "changed-A", "balance": "60"},
                   {"account_id": expense_other.id, "label": marker + "changed-B", "balance": "40"}]
    counterparts(negative, replacement)
    assert not env["res.partner.bank"].has_access("create")
    counterparts(first, [{"account_id": income.id, "label": marker + "existing-bank-A", "balance": "-25"},
                         {"account_id": income.id, "label": marker + "existing-bank-B", "balance": "-15"}])
    assert first.partner_bank_id == existing_bank.with_env(env)
    orphan_rows = [{"account_id": income.id, "label": marker + "income-A", "balance": "-12"},
                   {"account_id": income.id, "label": marker + "income-B", "balance": "-8"}]
    denied("bank.transaction.counterparts.replace", {"transaction_id": orphan.id, "lines": orphan_rows},
           "unauthorized", 3, move=orphan.move_id)
    # Only this rollback fixture receives the installed native contact-creation role.
    user = admin["res.users"].browse(env.uid)
    original_groups = user.group_ids.ids
    user.write({"group_ids": [Command.link(admin.ref("base.group_partner_manager").id)]})
    env.invalidate_all()
    assert env.uid == 5 and not env.su and env["res.partner.bank"].has_access("create")
    counterparts(orphan, orphan_rows)
    assert orphan.partner_bank_id and orphan.partner_bank_id.acc_number == metadata["account_number"]
    user.write({"group_ids": [Command.set(original_groups)]})
    env.invalidate_all()
    assert not env["res.partner.bank"].has_access("create")
    denied("bank.transaction.update", {"transaction_id": negative.id, "changes": {"payment_ref": marker + "unsafe"}}, "state_conflict", 5, move=negative.move_id)
    denied("bank.transaction.counterparts.replace", {"transaction_id": negative.id, "lines": [{**row, "balance": "10"} for row in rows]}, "business_rule_error", 6, move=negative.move_id)
    foreign_expense = account("foreign-expense", "expense", company=2)
    denied("bank.transaction.counterparts.replace", {"transaction_id": negative.id, "lines": [{**rows[0], "account_id": foreign_expense.id}, rows[1]]}, "record_not_found", 4, move=negative.move_id)
    currency = fixture("res.currency", {"name": "V4B", "symbol": "V4B", "active": True, "rounding": 0.01})
    fixture("res.currency.rate", {"currency_id": currency.id, "company_id": 1, "name": today, "rate": 2})
    fx_bank = fixture("account.journal", {"name": marker + "fx-bank", "code": "F" + run_id.hex[:4], "type": "bank", "company_id": 1,
                      "currency_id": currency.id, "default_account_id": liquidity.id, "suspense_account_id": suspense.id})
    fx_id = write("bank.transaction.record", {"journal_id": fx_bank.id, "date": today.isoformat(), "amount": "-100", "payment_ref": marker + "fx",
                  "partner_id": None}, replay=True)["id"]
    fx_transaction = env["account.bank.statement.line"].browse(fx_id)
    denied("bank.transaction.counterparts.replace", {"transaction_id": fx_id, "lines": rows}, "state_conflict", 5, move=fx_transaction.move_id)
    write("bank.transaction.unmatch", {"transaction_id": negative.id}, replay=True)
    assert not negative.is_reconciled and len(negative._seek_for_lines()[1]) == 1 and not negative._seek_for_lines()[2]
    write("reconciliation.write_off", {"transaction_id": negative.id, "write_off_account_id": expense.id,
          "label": marker + "single-fee", "expected_residual_amount": "100"}, replay=True)
    write("bank.transaction.unmatch", {"transaction_id": negative.id}, replay=True)
    counterparts(negative, rows)
    # Keep inaccessible owned transactions after successful calls: the inherited
    # fixture collector reads all tracked transactions as the ordinary user.
    foreign_liquidity = account("foreign-liquidity", "asset_cash", company=2, reconcile=True)
    foreign_suspense = account("foreign-suspense", "asset_current", company=2, reconcile=True)
    foreign_bank = fixture("account.journal", {"name": marker + "foreign-bank", "code": "X" + run_id.hex[:4], "type": "bank", "company_id": 2,
                           "default_account_id": foreign_liquidity.id, "suspense_account_id": foreign_suspense.id}, company=2)
    foreign_transaction = fixture("account.bank.statement.line", {"journal_id": foreign_bank.id, "date": today.isoformat(), "amount": -100,
                                  "payment_ref": marker + "foreign-transaction", "partner_id": False}, company=2)
    denied("bank.transaction.counterparts.replace", {"transaction_id": foreign_transaction.id, "lines": rows}, "record_not_found", 4, move=foreign_transaction.move_id)
    assert _TARGETS <= client.capabilities


def _live_worker():
    settlement._MODELS, settlement._exercise, settlement._summary = _MODELS, _exercise, _summary
    return settlement._live_worker()


if __name__ == "__main__":
    raise SystemExit(_live_worker())
