"""One real CLI/ordinary-user settlement workflow with full transaction rollback."""

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

import test_accounting_maintenance_batch_live as maintenance
import test_accounting_workflows_batch_live as workflows
import test_company_processing_batch_live as company_batch
import test_document_lifecycle_write_batch_live as lifecycle
import test_invoice_preparation_batch_live as preparation
import test_payment_bank_capability_batch_live as core

try:
    import pytest
except ModuleNotFoundError:
    if "--live-worker" not in sys.argv:
        raise
    pytest = None

_ALLOW_ENV = "ODACV4_ALLOW_ACCOUNTING_SETTLEMENT_SMOKE"
_TARGETS = {"tax.compute", "payment_term.compute", "tax.group.create", "tax.group.update", "tax.group.get", "tax.group.list",
            "bank.statement.create", "bank.statement.update"}
_ACCOUNTS = ("tax_payable_account_id", "tax_receivable_account_id", "advance_tax_payment_account_id")
_MODELS = tuple(dict.fromkeys((*core._BUSINESS_MODELS, "account.account", "account.journal", "mail.alias", "account.payment.method.line",
                             "account.bank.statement", "account.tax.group", "account.tax", "account.tax.repartition.line",
                             "account.payment.term", "account.payment.term.line", "account.cash.rounding", "account.move.reversal", "res.currency", "res.currency.rate")))


def _root():
    return Path(__file__).resolve().parents[2]


def _summary(alias, database):
    return {"alias": alias, "database": database, "company_id": 1, "user_id": 5, "business_su": False,
            "target_capabilities": sorted(_TARGETS), "execution": "in_process_cli_real_orm",
            "tax_empty_group_included_signed_refund_previews_and_invoice_consumers_verified": True,
            "term_installments_invoice_consumer_discount_foreign_cash_rounding_and_signed_preview_verified": True,
            "tax_group_settlement_accounts_set_clear_get_list_replay_and_foreign_denial_verified": True,
            "statement_start_native_end_recompute_explicit_override_replay_and_neighbor_validity_verified": True,
            "posted_financial_graph_preserved_and_full_fixtures_settings_defaults_currency_groups_rollback_verified": True}


if pytest is not None:
    @pytest.mark.integration
    def test_accounting_settlement_rolls_back_per_alias():
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
    today = fields.Date.context_today(env.user)

    def track(record):
        client.tracked[record._name].update(record.ids)
        if record._name == "account.journal":
            client.tracked["mail.alias"].update(record.alias_id.ids)
            client.tracked["account.payment.method.line"].update((record.inbound_payment_method_line_ids | record.outbound_payment_method_line_ids).ids)
        if record._name == "account.tax":
            client.tracked["account.tax.repartition.line"].update((record.invoice_repartition_line_ids | record.refund_repartition_line_ids).ids)
        if record._name == "account.payment.term":
            client.tracked["account.payment.term.line"].update(record.line_ids.ids)
        if record._name == "account.bank.statement.line":
            client.tracked["account.move"].update(record.move_id.ids)
            client.tracked["account.move.line"].update(record.move_id.line_ids.ids)
        return record

    def fixture(model, values, *, company=1):
        return track(admin[model].with_company(admin["res.company"].browse(company)).create(values))

    def account(label, account_type, *, company=1, reconcile=False):
        return fixture("account.account", {"name": marker + label, "code": label[:2].upper() + uuid.uuid5(run_id, label).hex[:8],
                       "account_type": account_type, "reconcile": reconcile, "company_ids": [Command.set([company])]}, company=company)

    def read(capability, parameters, **kwargs):
        return maintenance._call(client, alias, run_id, capability, parameters, **kwargs)

    def write(capability, parameters, *, replay=False):
        normalized = validate_core_write_request(capability, core._request(alias, run_id, capability, parameters))[2]
        key = _expected_idempotency_key(capability, normalized, 1) or f"{capability}:{run_id.hex}:{lifecycle._canonical_digest(normalized)[:32]}"
        first = read(capability, parameters, key=key)
        assert not first["idempotent_replay"], first
        if replay:
            second = read(capability, parameters, key=key)
            assert second["idempotent_replay"] and second["result"] == first["result"], second
        result = first["result"]
        if result["model"] in {"account.tax", "account.payment.term"}:
            track(env[result["model"]].browse(result["id"]))
        return result

    def denied(capability, parameters, error="record_not_found", code=4, *, write_call=False):
        options = {"exit_code": code}
        if write_call:
            normalized = validate_core_write_request(capability, core._request(alias, run_id, capability, parameters))[2]
            options["key"] = _expected_idempotency_key(capability, normalized, 1) or f"{capability}:{run_id.hex}:denied"
        response = read(capability, parameters, **options)
        assert response["error"]["code"] == error, response

    user = admin["res.users"].browse(5)
    if not user.has_group("account.group_account_manager"):
        user.write({"group_ids": [Command.link(admin.ref("account.group_account_manager").id)]})
    env.invalidate_all()
    assert env.uid == 5 and not env.su and env.company.id == 1
    income, expense = account("income", "income"), account("expense", "expense")
    payable, receivable, advance = account("tax-payable", "liability_current"), account("tax-receivable", "asset_current"), account("tax-advance", "asset_current")
    settlement = dict(zip(_ACCOUNTS, (payable.id, receivable.id, advance.id)))
    group_id = write("tax.group.create", {"name": marker + "group", "sequence": 10, "preceding_subtotal": None, **settlement}, replay=True)["id"]
    assert all(read("tax.group.get", {"tax_group_id": group_id})[field] == value for field, value in settlement.items())
    page = read("tax.group.list", {})
    cursor = page["next_cursor"]
    rows = page["items"]
    while page["has_more"]:
        page = read("tax.group.list", {"cursor": cursor})
        rows += page["items"]
        cursor = page["next_cursor"]
    listed = next(row for row in rows if row["id"] == group_id)
    assert all(listed[field] == value for field, value in settlement.items())
    write("tax.group.update", {"tax_group_id": group_id, "changes": {field: None for field in _ACCOUNTS}}, replay=True)
    assert all(read("tax.group.get", {"tax_group_id": group_id})[field] is None for field in _ACCOUNTS)
    write("tax.group.update", {"tax_group_id": group_id, "changes": settlement}, replay=True)
    native_group = env["account.tax.group"].browse(group_id)
    assert all(getattr(native_group, field).id == value for field, value in settlement.items())

    def tax(label, amount, use="none", included=False, children=None):
        item = fixture("account.tax", {"name": marker + label, "company_id": 1, "tax_group_id": group_id, "type_tax_use": use,
                        "amount_type": "group" if children else "percent", "amount": amount, "sequence": amount or 1,
                        "price_include_override": "tax_included" if included else "tax_excluded",
                        **({"children_tax_ids": [Command.set(children)]} if children else {})})
        if not children:
            item.invoice_repartition_line_ids.filtered(lambda line: line.repartition_type == "tax").write({"account_id": payable.id})
            item.refund_repartition_line_ids.filtered(lambda line: line.repartition_type == "tax").write({"account_id": receivable.id})
        return item

    leaves = [tax("leaf10", 10), tax("leaf5", 5)]
    grouped, included = tax("grouped", 0, use="sale", children=[leaf.id for leaf in leaves]), tax("included", 10, use="purchase", included=True)
    sale = fixture("account.journal", {"name": marker + "sale", "code": "S" + run_id.hex[:4], "type": "sale", "company_id": 1, "default_account_id": income.id})
    purchase = fixture("account.journal", {"name": marker + "purchase", "code": "P" + run_id.hex[:4], "type": "purchase", "company_id": 1, "default_account_id": expense.id})
    installment = fixture("account.payment.term", {"name": marker + "installment", "company_id": 1, "line_ids": [
        Command.create({"value": "percent", "value_amount": 40, "delay_type": "days_after", "nb_days": 10}),
        Command.create({"value": "percent", "value_amount": 60, "delay_type": "days_after", "nb_days": 30})]})
    discount = fixture("account.payment.term", {"name": marker + "discount", "company_id": 1, "early_discount": True,
                       "discount_percentage": 2, "discount_days": 10, "early_pay_discount_computation": "excluded"})
    foreign = fixture("res.currency", {"name": "V4S", "symbol": "V4S", "active": True, "rounding": 0.01})
    fixture("res.currency.rate", {"currency_id": foreign.id, "company_id": 1, "name": today, "rate": 0.25})
    rounding = fixture("account.cash.rounding", {"name": marker + "rounding", "rounding": 0.05, "rounding_method": "HALF-UP", "strategy": "biggest_tax"})
    env.invalidate_all()

    def document(label, *, supplier=False, currency=None, term=None):
        value = write("vendor_bill.create" if supplier else "customer_invoice.create", {
            "partner_id": ids["supplier" if supplier else "customer"], "journal_id": purchase.id if supplier else sale.id,
            "invoice_date": today.isoformat(), "date": today.isoformat(), "currency_id": currency or env.company.currency_id.id,
            "payment_term_id": term, "reference": marker + label,
            "lines": [{"name": marker + label, "account_id": expense.id if supplier else income.id,
                       "quantity": "1", "price_unit": "110" if supplier else "101.01", "tax_ids": [included.id if supplier else grouped.id]}]})
        return env["account.move"].browse(value["id"])

    invoice, bill = document("sale", currency=foreign.id, term=installment.id), document("purchase")

    def tax_preview(move, *, refund=False):
        line = move.invoice_line_ids.filtered(lambda row: row.display_type == "product")
        assert len(line) == 1
        value = read("tax.compute", {"tax_ids": line.tax_ids.ids, "currency_id": move.currency_id.id,
                     "price_unit": _decimal_string(line.price_unit), "quantity": _decimal_string(line.quantity), "partner_id": move.partner_id.id, "is_refund": refund})
        currency = move.currency_id
        assert currency.is_zero(float(Decimal(value["total_excluded"])) - move.amount_untaxed), value
        assert currency.is_zero(float(Decimal(value["total_included"])) - move.amount_total), value
        native_lines = move.line_ids.filtered(lambda row: row.tax_line_id)
        assert {row["tax_repartition_line_id"] for row in value["taxes"]} == set(native_lines.tax_repartition_line_id.ids), value
        assert {row["account_id"] for row in value["taxes"]} == set(native_lines.account_id.ids), value
        assert currency.is_zero(sum(float(Decimal(row["amount"])) for row in value["taxes"]) - move.amount_tax), value
        return value

    tax_preview(invoice)
    tax_preview(bill)
    write("invoice.post", {"move_id": invoice.id})
    snapshot = maintenance._graph(invoice)
    refund = env["account.move"].browse(write("customer_credit_note.create", {"move_id": invoice.id, "date": today.isoformat(), "reason": marker + "refund"})["id"])
    assert refund.move_type == "out_refund"
    tax_preview(refund, refund=True)
    negative = read("tax.compute", {"tax_ids": [grouped.id], "currency_id": foreign.id, "price_unit": "-101.01", "quantity": "1"})
    assert Decimal(negative["total_included"]) < 0 and all(Decimal(row["amount"]) < 0 for row in negative["taxes"])
    empty = read("tax.compute", {"tax_ids": [], "currency_id": foreign.id, "price_unit": "19.99", "quantity": "-2"})
    assert not empty["taxes"] and Decimal(empty["total_excluded"]) == Decimal("-39.98") == Decimal(empty["total_included"])

    schedule = read("invoice.payment_schedule.inspect", {"invoice_id": invoice.id})
    sign = -1 if sum(Decimal(row["balance"]) for row in schedule["lines"]) < 0 else 1
    term_parameters = {"payment_term_id": installment.id, "date_ref": today.isoformat(), "currency_id": foreign.id, "sign": sign,
                       "tax_amount": _decimal_string(abs(invoice.amount_tax_signed) * sign), "tax_amount_currency": _decimal_string(invoice.amount_tax * sign),
                       "untaxed_amount": _decimal_string(abs(invoice.amount_untaxed_signed) * sign), "untaxed_amount_currency": _decimal_string(invoice.amount_untaxed * sign)}
    computed = read("payment_term.compute", term_parameters)
    assert [(row["date"], Decimal(row["company_amount"]), Decimal(row["foreign_amount"])) for row in computed["line_ids"]] == [
        (row["date_maturity"], Decimal(row["balance"]), Decimal(row["amount_currency"])) for row in schedule["lines"]], {"preview": computed, "schedule": schedule}
    assert len(computed["line_ids"]) == 2 and computed["discount_date"] is None
    for native_sign in (1, -1):
        parameters = {"payment_term_id": discount.id, "date_ref": today.isoformat(), "currency_id": foreign.id, "sign": native_sign,
                      "tax_amount": str(Decimal("56.16") * native_sign), "tax_amount_currency": str(Decimal("14.04") * native_sign),
                      "untaxed_amount": str(Decimal("404.04") * native_sign), "untaxed_amount_currency": str(Decimal("101.01") * native_sign), "cash_rounding_id": rounding.id}
        value = read("payment_term.compute", parameters)
        assert value["discount_date"] == (today + timedelta(days=10)).isoformat() and Decimal(value["discount_percentage"]) == 2
        native_inputs = {"date_ref": today, "currency": foreign.with_env(env), "company": env.company, "sign": native_sign,
                         **{field: float(parameters[field]) for field in ("tax_amount", "tax_amount_currency", "untaxed_amount", "untaxed_amount_currency")}}
        plain = discount.with_env(env)._compute_terms(**native_inputs)
        assert not foreign.is_zero(rounding.compute_difference(foreign, plain["discount_amount_currency"])), {"input": parameters, "plain": plain, "preview": value}
        native = discount.with_env(env)._compute_terms(**native_inputs, cash_rounding=rounding.with_env(env))
        diagnostic = {"input": parameters, "preview": value, "native": native, "without_cash_rounding": plain}
        assert value["total_amount"] == _decimal_string(native["total_amount"]), diagnostic
        assert value["line_ids"] == [{"date": str(row["date"]), "company_amount": _decimal_string(row["company_amount"]),
                                      "foreign_amount": _decimal_string(row["foreign_amount"])} for row in native["line_ids"]], diagnostic
        # Native last-line residuals retain float tails; monetary equality uses native currency precision.
        assert foreign.is_zero(float(sum(Decimal(row["foreign_amount"]) for row in value["line_ids"]) - Decimal("115.05") * native_sign)), diagnostic
        assert value["discount_amount_currency"] == _decimal_string(native["discount_amount_currency"]), diagnostic
        assert value["discount_balance"] == _decimal_string(native["discount_balance"]), diagnostic

    liquidity, suspense = account("liquidity", "asset_cash", reconcile=True), account("suspense", "asset_current", reconcile=True)
    bank = fixture("account.journal", {"name": marker + "bank", "code": "B" + run_id.hex[:4], "type": "bank", "company_id": 1,
                   "default_account_id": liquidity.id, "suspense_account_id": suspense.id, "currency_id": foreign.id})
    transactions = [env["account.bank.statement.line"].browse(write("bank.transaction.record", {"journal_id": bank.id, "date": today.isoformat(),
                    "amount": amount, "payment_ref": marker + amount, "partner_id": ids["customer"]})["id"]) for amount in ("1.25", "-0.5")]
    bank_snapshots = {line.id: maintenance._graph(line.move_id) for line in transactions}
    statement = env["account.bank.statement"].browse(write("bank.statement.create", {"transaction_ids": sorted(line.id for line in transactions),
                    "reference": marker, "balance_start": "100", "balance_end_real": "100.75"}, replay=True)["id"])
    assert statement.currency_id == foreign and statement.balance_start == 100 and statement.balance_end == statement.balance_end_real == 100.75
    write("bank.statement.update", {"statement_id": statement.id, "changes": {"balance_start": "-2.5"}}, replay=True)
    assert statement.balance_start == -2.5 and statement.balance_end == statement.balance_end_real == -1.75 and statement.is_complete
    write("bank.statement.update", {"statement_id": statement.id, "changes": {"balance_start": "-1", "balance_end_real": "9"}}, replay=True)
    assert statement.balance_start == -1 and statement.balance_end == -0.25 and statement.balance_end_real == 9 and not statement.is_complete
    write("bank.statement.update", {"statement_id": statement.id, "changes": {"balance_start": "0"}}, replay=True)
    assert statement.balance_start == 0 and statement.balance_end == statement.balance_end_real == 0.75
    projected = read("bank.statement.get", {"bank_statement_id": statement.id})
    assert Decimal(projected["balance_start"]) == 0 and Decimal(projected["balance_end_real"]) == Decimal("0.75")
    third = env["account.bank.statement.line"].browse(write("bank.transaction.record", {"journal_id": bank.id, "date": today.isoformat(),
                 "amount": "2", "payment_ref": marker + "neighbor", "partner_id": ids["customer"]})["id"])
    neighbor = env["account.bank.statement"].browse(write("bank.statement.create", {"transaction_ids": third.ids, "reference": marker + "neighbor",
                 "balance_start": "0.75", "balance_end_real": "2.75"})["id"])
    assert neighbor.is_valid
    write("bank.statement.update", {"statement_id": neighbor.id, "changes": {"balance_start": "1", "balance_end_real": "3"}}, replay=True)
    assert not neighbor.is_valid
    assert maintenance._graph(invoice) == snapshot
    assert all(maintenance._graph(line.move_id) == bank_snapshots[line.id] for line in transactions)

    # Foreign fixtures are last: UID5 successful-call tracking must not read company2 related records.
    other_account = account("foreign-account", "asset_current", company=2)
    for field in _ACCOUNTS:
        denied("tax.group.update", {"tax_group_id": group_id, "changes": {field: other_account.id}}, write_call=True)
    other_group = fixture("account.tax.group", {"name": marker + "foreign-group", "company_id": 2}, company=2)
    denied("tax.group.update", {"tax_group_id": other_group.id, "changes": settlement}, write_call=True)
    denied("tax.group.get", {"tax_group_id": other_group.id})
    other_tax = fixture("account.tax", {"name": marker + "foreign-tax", "company_id": 2, "tax_group_id": other_group.id, "type_tax_use": "sale", "amount": 10}, company=2)
    denied("tax.compute", {"tax_ids": [other_tax.id], "currency_id": foreign.id, "price_unit": "1", "quantity": "1"})
    other_term = fixture("account.payment.term", {"name": marker + "foreign-term", "company_id": 2}, company=2)
    denied("payment_term.compute", {**term_parameters, "payment_term_id": other_term.id})
    assert _TARGETS <= client.capabilities


def _live_worker():
    args = lifecycle._arguments(None)
    sys.path.insert(0, str(args.odoo_source.resolve(strict=True)))
    sys.path.insert(0, str(_root() / "src"))
    from odoo import SUPERUSER_ID, api
    from odoo.orm.registry import Registry
    from odoo.tools import config

    from odoo_accounting_cli_v4 import cli

    config.parse_config(["--config", str(args.odoo_config.resolve(strict=True)), "--database", args.database, "--no-http", "--logfile=/dev/null"])
    registry, actual = Registry(args.database), cli.load_registry()
    cli.load_registry = lambda: actual
    cursor, marker = registry.cursor(), f"ODACV4-SETTLEMENT-{args.alias}-{args.run_id.hex}"
    tracked, groups, company_fields, settings, defaults, currencies, failure = {}, None, [], None, None, None, None
    try:
        context = {"allowed_company_ids": [1], "lang": "en_US", "tz": "Asia/Shanghai", "tracking_disable": True, "mail_create_nosubscribe": True, "mail_notrack": True}
        admin = api.Environment(cursor, SUPERUSER_ID, context)
        user = admin["res.users"].browse(5).exists()
        assert user.active and user.login == lifecycle._USER_LOGIN and user.has_group("account.group_account_user")
        groups = maintenance._groups(admin)
        company_fields = sorted(name for name, field in admin["res.company"]._fields.items() if field.store and field.type not in {"binary", "one2many", "many2many"})
        settings, defaults, currencies = company_batch._company_snapshot(admin, company_fields), preparation._defaults(admin), workflows._currency_snapshot(admin)
        client = maintenance._Client(api.Environment(cursor, 5, context))
        client.tracked = {model: set() for model in _MODELS}
        tracked = client.tracked
        _exercise(admin, client, args.alias, args.run_id, marker)
        core._collect_related(admin, tracked)
    except BaseException as exc:  # noqa: BLE001 - verify full rollback before propagating native or assertion failure.
        failure = exc
    finally:
        cursor.rollback()
        cursor.close()
    with registry.cursor() as verify_cursor:
        try:
            verify = api.Environment(verify_cursor, SUPERUSER_ID, {"allowed_company_ids": [1, 2], "lang": "en_US"})
            for model, record_ids in tracked.items():
                remaining = verify[model].with_context(active_test=False).search([("id", "in", sorted(record_ids))]).ids
                assert not remaining, (model, remaining)
            for model in ("account.account", "account.journal", "account.tax", "account.tax.group", "account.payment.term", "account.cash.rounding"):
                assert not verify[model].with_context(active_test=False).search_count([("name", "ilike", marker)])
            assert not verify["account.move.line"].search_count([("name", "ilike", marker)])
            if groups is not None:
                assert maintenance._groups(verify) == groups
                assert company_batch._company_snapshot(verify, company_fields) == settings and preparation._defaults(verify) == defaults and workflows._currency_snapshot(verify) == currencies
        finally:
            verify_cursor.rollback()
    if failure is not None:
        raise failure
    print(json.dumps(_summary(args.alias, args.database), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_live_worker())
