"""One ordinary-user public-CLI workflow, using the established fresh rollback worker."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import sysconfig
import uuid
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

_ALLOW_ENV = "ODACV4_ALLOW_ACCOUNTING_ENTRY_MEMBERSHIP_SMOKE"
_TARGETS = {"journal_entry.lines.add", "journal_entry.lines.remove", "customer_invoice.create", "vendor_bill.create",
            "invoice.line.create", "invoice.line.update", "invoice.lines.replace", "customer_credit_note.create", "vendor_refund.create"}
_MODELS = settlement._MODELS
_ADD, _REMOVE = "journal_entry.lines.add", "journal_entry.lines.remove"


def _root():
    return Path(__file__).resolve().parents[2]


def _summary(alias, database):
    return {"alias": alias, "database": database, "company_id": 1, "user_id": 5, "business_su": False,
            "target_capabilities": sorted(_TARGETS), "execution": "in_process_cli_real_orm",
            "seven_negative_quantity_inputs_native_tax_and_custom_refund_consumers_verified": True,
            "balanced_append_retained_financial_ids_identical_pairs_and_serial_expected_id_replay_verified": True,
            "stale_extra_missing_and_shape_mismatch_append_conflicts_preserve_native_state_verified": True,
            "balanced_subset_remove_all_empty_and_missing_remove_without_tombstone_verified": True,
            "native_unbalanced_posted_generated_and_foreign_denials_preserve_financial_state_verified": True,
            "full_fixtures_settings_defaults_currency_rates_and_all_user_groups_fresh_rollback_verified": True}


if pytest is not None:
    @pytest.mark.integration
    def test_accounting_entry_membership_rolls_back_per_alias():
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

    from odoo_accounting_cli_v4.bridge.core_object_reads_runtime import _decimal_string
    from odoo_accounting_cli_v4.capabilities.core_writes import (
        _expected_idempotency_key,
        validate_core_write_request,
    )

    env, ids = client.env, lifecycle._fixture_ids(admin, alias)
    today = fields.Date.context_today(env.user).isoformat()
    assert env.uid == 5 and not env.su and env.company.id == 1

    def fixture(model, values, *, company=1):
        record = admin[model].with_company(admin["res.company"].browse(company)).create(values)
        client.tracked[model].update(record.ids)
        if model == "account.journal":
            client.tracked["mail.alias"].update(record.alias_id.ids)
            client.tracked["account.payment.method.line"].update((record.inbound_payment_method_line_ids | record.outbound_payment_method_line_ids).ids)
        if model == "account.tax":
            client.tracked["account.tax.repartition.line"].update(record.repartition_line_ids.ids)
        return record

    def account(label, account_type, *, company=1):
        return fixture("account.account", {"name": marker + label, "code": "M" + uuid.uuid5(run_id, label).hex[:9],
                       "account_type": account_type, "company_ids": [Command.set([company])]}, company=company)

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
            tracked = {model: set(values) for model, values in client.tracked.items()}
            second = call(capability, parameters, key=key)
            assert second["idempotent_replay"] and second["result"] == first["result"] and client.tracked == tracked, second
        return first["result"]

    def denied(capability, parameters, error, code, *, move=None):
        before = maintenance._graph(move) if move is not None else None
        response = call(capability, parameters, key=key_for(capability, parameters), exit_code=code)
        assert response["error"]["code"] == error and response["data"] is None, response
        env.invalidate_all()
        if move is not None:
            assert maintenance._graph(move) == before, response

    income, expense, tax_account = account("income", "income"), account("expense", "expense"), account("tax", "liability_current")
    general = fixture("account.journal", {"name": marker + "general", "code": "G" + run_id.hex[:4], "type": "general", "company_id": 1})
    journals = {supplier: fixture("account.journal", {"name": marker + ("purchase" if supplier else "sale"), "code": ("P" if supplier else "S") + run_id.hex[:4],
                 "type": "purchase" if supplier else "sale", "company_id": 1, "default_account_id": expense.id if supplier else income.id}) for supplier in (False, True)}
    group = fixture("account.tax.group", {"name": marker + "group", "company_id": 1})
    taxes = {supplier: fixture("account.tax", {"name": marker + ("purchase-tax" if supplier else "sale-tax"), "company_id": 1,
             "tax_group_id": group.id, "type_tax_use": "purchase" if supplier else "sale", "amount_type": "percent", "amount": 10,
             "price_include_override": "tax_excluded"}) for supplier in (False, True)}
    for tax in taxes.values():
        tax.repartition_line_ids.filtered(lambda line: line.repartition_type == "tax").write({"account_id": tax_account.id})
    env.invalidate_all()

    def line(label, quantity, *, supplier=False, price="10.00"):
        return {"name": marker + label, "product_id": None, "account_id": expense.id if supplier else income.id,
                "quantity": quantity, "price_unit": price, "discount": "0", "tax_ids": [taxes[supplier].id]}

    def consumer(move, *, refund=False):
        env.invalidate_all()
        products = move.invoice_line_ids.filtered(lambda row: row.display_type == "product")
        total_base, total_tax = Decimal(0), Decimal(0)
        repartition_ids = set()
        for row in products:
            preview = call("tax.compute", {"tax_ids": sorted(row.tax_ids.ids), "currency_id": move.currency_id.id,
                           "price_unit": _decimal_string(row.price_unit), "quantity": _decimal_string(row.quantity), "is_refund": refund})
            total_base += Decimal(preview["total_excluded"])
            total_tax += sum((Decimal(tax["amount"]) for tax in preview["taxes"]), Decimal(0))
            repartition_ids.update(tax["tax_repartition_line_id"] for tax in preview["taxes"])
        diagnostic = {"move": move.id, "quantity": products.quantity if len(products) == 1 else [row.quantity for row in products],
                      "base": str(total_base), "tax": str(total_tax), "native": (move.amount_untaxed, move.amount_tax, move.amount_total)}
        assert move.currency_id.is_zero(float(total_base) - move.amount_untaxed), diagnostic
        assert move.currency_id.is_zero(float(total_tax) - move.amount_tax), diagnostic
        assert repartition_ids == set(move.line_ids.filtered(lambda row: row.tax_line_id).tax_repartition_line_id.ids), diagnostic
        assert move.company_currency_id.is_zero(sum(move.line_ids.mapped("balance"))), diagnostic
        assert any(row.quantity < 0 for row in products), diagnostic

    documents = {}
    for supplier in (False, True):
        capability = "vendor_bill.create" if supplier else "customer_invoice.create"
        parameters = {"partner_id": ids["supplier" if supplier else "customer"], "journal_id": journals[supplier].id,
                      "invoice_date": today, "currency_id": env.company.currency_id.id, "reference": marker + capability,
                      "lines": [line("positive", "1.00", supplier=supplier, price="100.00"), line("negative", "-2.00", supplier=supplier)]}
        move = env["account.move"].browse(write(capability, parameters, replay=True)["id"])
        documents[supplier] = move
        consumer(move)

    invoice = documents[False]
    value = write("invoice.line.create", {"move_id": invoice.id, "line": line("added-negative", "-1.50")}, replay=True)
    new_line = env["account.move.line"].browse(value["source_id"])
    assert new_line.quantity == -1.5
    consumer(invoice)
    write("invoice.line.update", {"move_id": invoice.id, "line_id": new_line.id, "changes": {"quantity": "-2.50"}}, replay=True)
    assert new_line.quantity == -2.5
    consumer(invoice)
    write("invoice.lines.replace", {"move_id": invoice.id, "lines": [line("replacement-positive", "1", price="100"), line("replacement-negative", "-3.00")]}, replay=True)
    consumer(invoice)
    for supplier, source in documents.items():
        write("invoice.post", {"move_id": source.id})
        source_snapshot = maintenance._graph(source)
        capability = "vendor_refund.create" if supplier else "customer_credit_note.create"
        refund = env["account.move"].browse(write(capability, {"move_id": source.id, "date": today, "reason": marker + capability,
               "lines": [line("refund-positive", "1", supplier=supplier, price="100"), line("refund-negative", "-4.00", supplier=supplier)]}, replay=True)["id"])
        assert refund.move_type == ("in_refund" if supplier else "out_refund")
        consumer(refund, refund=True)
        assert maintenance._graph(source) == source_snapshot

    def pair(amount="12.50"):
        return [{"name": marker + "identical-pair", "account_id": expense.id, "partner_id": None, "debit": amount, "credit": "0"},
                {"name": marker + "identical-pair", "account_id": income.id, "partner_id": None, "debit": "0", "credit": amount}]

    entry = env["account.move"].browse(write("journal_entry.create", {"journal_id": general.id, "date": today, "reference": marker, "lines": pair("25")})["id"])
    original_ids = sorted(entry.line_ids.ids)
    original_rows = entry.line_ids.sorted("id").read(maintenance._FINANCIAL, load=None)
    initial = {"move_id": entry.id, "expected_line_ids": original_ids, "lines": pair()}
    first = write(_ADD, initial, replay=True)
    first_added = sorted(set(first["line_ids"]) - set(original_ids))
    assert len(first_added) == 2 and entry.line_ids.filtered(lambda row: row.id in original_ids).sorted("id").read(maintenance._FINANCIAL, load=None) == original_rows
    second_expected = sorted(entry.line_ids.ids)
    second = write(_ADD, {**initial, "expected_line_ids": second_expected}, replay=True)
    second_added = sorted(set(second["line_ids"]) - set(second_expected))
    assert len(second_added) == 2 and not set(second_added) & set(first_added)
    denied(_ADD, initial, "idempotency_conflict", 5, move=entry)
    denied(_ADD, {**initial, "expected_line_ids": [original_ids[0]]}, "idempotency_conflict", 5, move=entry)
    denied(_ADD, {**initial, "expected_line_ids": sorted(entry.line_ids.ids + [2147483000])}, "idempotency_conflict", 5, move=entry)
    denied(_ADD, {**initial, "expected_line_ids": second_expected, "lines": pair("13")}, "idempotency_conflict", 5, move=entry)

    kept = entry.line_ids.filtered(lambda row: row.id not in first_added).sorted("id").read(maintenance._FINANCIAL, load=None)
    denied(_REMOVE, {"move_id": entry.id, "line_ids": first_added[:1]}, "business_rule_error", 6, move=entry)
    removed = write(_REMOVE, {"move_id": entry.id, "line_ids": first_added})
    assert set(removed["line_ids"]) == set(second_expected + second_added) - set(first_added)
    assert entry.line_ids.sorted("id").read(maintenance._FINANCIAL, load=None) == kept
    denied(_REMOVE, {"move_id": entry.id, "line_ids": first_added}, "record_not_found", 4, move=entry)
    removed = write(_REMOVE, {"move_id": entry.id, "line_ids": sorted(entry.line_ids.ids)})
    assert removed["line_ids"] == [] and not entry.line_ids and entry.state == "draft" and not removed["reconciled"]
    write(_ADD, {"move_id": entry.id, "expected_line_ids": [], "lines": pair()}, replay=True)
    write("journal_entry.post", {"move_id": entry.id})
    denied(_ADD, {"move_id": entry.id, "expected_line_ids": sorted(entry.line_ids.ids), "lines": pair()}, "state_conflict", 5, move=entry)
    denied(_REMOVE, {"move_id": entry.id, "line_ids": sorted(entry.line_ids.ids)}, "state_conflict", 5, move=entry)

    source_entry = env["account.move"].browse(write("journal_entry.create", {"journal_id": general.id, "date": today, "lines": pair()})["id"])
    write("journal_entry.post", {"move_id": source_entry.id})
    generated = env["account.move"].browse(write("journal_entry.reverse", {"move_id": source_entry.id, "date": today, "reason": marker + "reverse"})["id"])
    if generated.state != "draft":
        generated = fixture("account.move", {"company_id": 1, "journal_id": general.id, "date": today, "move_type": "entry",
                            "reversed_entry_id": source_entry.id, "line_ids": [Command.create({**row, "partner_id": False,
                            "debit": Decimal(row["debit"]), "credit": Decimal(row["credit"])}) for row in pair()]})
        client.tracked["account.move.line"].update(generated.line_ids.ids)
    denied(_ADD, {"move_id": generated.id, "expected_line_ids": sorted(generated.line_ids.ids), "lines": pair()}, "business_rule_error", 6, move=generated)
    denied(_REMOVE, {"move_id": generated.id, "line_ids": sorted(generated.line_ids.ids)}, "business_rule_error", 6, move=generated)

    # Foreign fixtures come last: ordinary successful calls must not traverse co2 tracked objects.
    other_account = account("foreign", "expense", company=2)
    other_general = fixture("account.journal", {"name": marker + "foreign-general", "code": "F" + run_id.hex[:4], "type": "general", "company_id": 2}, company=2)
    foreign = fixture("account.move", {"company_id": 2, "journal_id": other_general.id, "date": today, "move_type": "entry",
                      "line_ids": [Command.create({**row, "account_id": other_account.id, "partner_id": False,
                      "debit": Decimal(row["debit"]), "credit": Decimal(row["credit"])}) for row in pair()]}, company=2)
    client.tracked["account.move.line"].update(foreign.line_ids.ids)
    denied(_ADD, {"move_id": foreign.id, "expected_line_ids": sorted(foreign.line_ids.ids), "lines": pair()}, "record_not_found", 4)
    denied(_REMOVE, {"move_id": foreign.id, "line_ids": sorted(foreign.line_ids.ids)}, "record_not_found", 4)
    assert _TARGETS <= client.capabilities


def _live_worker():
    # The established worker loads actual CLI registry once and verifies every tracked model,
    # all user groups, both company settings, ir.defaults, currencies/rates after fresh rollback.
    settlement._MODELS, settlement._exercise, settlement._summary = _MODELS, _exercise, _summary
    return settlement._live_worker()


if __name__ == "__main__":
    raise SystemExit(_live_worker())
