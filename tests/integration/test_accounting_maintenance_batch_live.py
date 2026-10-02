"""One rollback-only, ordinary-user CLI workflow for eight maintenance operations."""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import sysconfig
import uuid
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

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

_ALLOW_ENV = "ODACV4_ALLOW_ACCOUNTING_MAINTENANCE_SMOKE"
_TARGETS = {"currency.rate.update", "currency.rate.delete", "bank.statement.update", "bank.transaction.record",
            "bank.transaction.update", "invoice.update", "invoice.payment_method.assign", "invoice.incoterm.update"}
_MODELS = tuple(dict.fromkeys((*core._BUSINESS_MODELS, "account.bank.statement", "account.account", "account.journal",
                             "mail.alias", "account.payment.method.line", "res.currency.rate", "res.partner.bank",
                             "account.incoterms", "ir.attachment", "account.payment.register")))
_FINANCIAL = ["id", "account_id", "partner_id", "balance", "debit", "credit", "currency_id", "amount_currency",
              "amount_residual", "amount_residual_currency", "date_maturity", "tax_ids", "tax_line_id",
              "tax_repartition_line_id", "matched_debit_ids", "matched_credit_ids", "full_reconcile_id"]
_PARTIAL = ["id", "debit_move_id", "credit_move_id", "amount", "debit_amount_currency", "credit_amount_currency",
            "max_date", "exchange_move_id", "full_reconcile_id"]


def _root():
    return Path(__file__).resolve().parents[2]


def _summary(alias, database):
    return {"alias": alias, "database": database, "company_id": 1, "user_id": 5, "business_su": False,
            "target_capabilities": sorted(_TARGETS), "execution": "in_process_cli_real_orm",
            "root_owned_rate_correction_replay_conversion_delete_fallback_and_missing_denial_verified": True,
            "foreign_bank_positive_negative_pair_set_clear_replay_and_native_unmatched_sync_verified": True,
            "statement_reconciled_membership_detach_without_delete_financial_and_graph_preservation_verified": True,
            "posted_unsent_invoice_bank_set_clear_replay_sent_and_pdf_denials_verified": True,
            "posted_preferred_method_native_wizard_default_and_incoterm_set_clear_verified": True,
            "posted_invoice_partial_graph_and_amounts_unchanged_no_external_send_verified": True,
            "full_fixtures_settings_defaults_currency_rates_and_all_user_groups_rollback_verified": True}


class _Client(workflows._Client):
    def invoke(self, action, payload):
        try:
            return super().invoke(action, payload)
        except Exception as exc:
            self.last_runtime_failure = exc
            raise


if pytest is not None:
    @pytest.mark.integration
    def test_accounting_maintenance_rolls_back_per_alias():
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


def _call(client, alias, run_id, capability, parameters, **kwargs):
    if capability not in {"currency.convert", "bank.transaction.reconciliation.get"}:
        try:
            return workflows._call(client, alias, run_id, capability, parameters, **kwargs)
        except AssertionError as exc:
            if client.last_runtime_failure is not None:
                raise exc from client.last_runtime_failure
            raise
    from odoo_accounting_cli_v4 import cli
    from odoo_accounting_cli_v4.bridge.bank_reconciliation import (
        OdooBankReconciliationPort,
    )
    from odoo_accounting_cli_v4.bridge.currency_rates import OdooCurrencyConvertPort

    port = OdooCurrencyConvertPort(client) if capability == "currency.convert" else OdooBankReconciliationPort(client)
    stdout, stderr = io.StringIO(), io.StringIO()
    code = cli.main(["read", capability, "--request", "-"], stdin=io.StringIO(json.dumps(core._request(alias, run_id, capability, parameters))),
                    stdout=stdout, stderr=stderr, port_factory=lambda *args: port)
    response = json.loads(stdout.getvalue())
    assert code == 0 and not stderr.getvalue() and response["success"] and response["status"] == "verified", response
    assert client.env.uid == 5 and not client.env.su and client.env.company.id == 1 and response["odoo"]["user_id"] == 5
    client.capabilities.add(capability)
    return response["data"]


def _graph(move):
    partials = move.line_ids.matched_debit_ids | move.line_ids.matched_credit_ids
    return (move.line_ids.sorted("id").read(_FINANCIAL, load=None), partials.sorted("id").read(_PARTIAL, load=None),
            move.line_ids.full_reconcile_id.ids, (move.amount_untaxed, move.amount_tax, move.amount_total, move.amount_residual, move.date, move.name))


def _groups(env):
    return (env["res.users"].with_context(active_test=False).search([], order="id").read(["id", "group_ids"], load=None),
            env["res.groups"].search([], order="id").read(["id", "implied_ids"], load=None))


def _exercise(admin, client, alias, run_id, marker):
    from odoo import Command, fields

    from odoo_accounting_cli_v4.capabilities.core_writes import (
        _expected_idempotency_key,
        validate_core_write_request,
    )

    env, ids = client.env, lifecycle._fixture_ids(admin, alias)
    today = fields.Date.context_today(env.user).isoformat()

    def track(record):
        client.tracked[record._name].update(record.ids)
        if record._name == "account.move":
            client.tracked["account.move.line"].update(record.line_ids.ids)
        if record._name == "account.bank.statement.line":
            client.tracked["account.move"].update(record.move_id.ids)
            client.tracked["account.move.line"].update(record.move_id.line_ids.ids)
        if record._name == "account.journal":
            client.tracked["mail.alias"].update(record.alias_id.ids)
            client.tracked["account.payment.method.line"].update((record.inbound_payment_method_line_ids | record.outbound_payment_method_line_ids).ids)
        return record

    def fixture(model, values, *, company=1):
        return track(admin[model].with_company(admin["res.company"].browse(company)).create(values))

    def write(capability, params, *, replay=False):
        normalized = validate_core_write_request(capability, core._request(alias, run_id, capability, params))[2]
        key = _expected_idempotency_key(capability, normalized, 1) or f"{capability}:{run_id.hex}:{lifecycle._canonical_digest(normalized)[:32]}"
        first = _call(client, alias, run_id, capability, params, key=key)
        assert not first["idempotent_replay"], first
        if replay:
            second = _call(client, alias, run_id, capability, params, key=key)
            assert second["idempotent_replay"] and second["result"] == first["result"], second
        return first["result"]

    def denied(capability, params, error, code):
        normalized = validate_core_write_request(capability, core._request(alias, run_id, capability, params))[2]
        key = _expected_idempotency_key(capability, normalized, 1) or f"{capability}:{run_id.hex}:denied"
        response = _call(client, alias, run_id, capability, params, key=key, exit_code=code)
        assert response["error"]["code"] == error, response

    def account(label, account_type, *, company=1, reconcile=False):
        return fixture("account.account", {"name": marker + label, "code": label[:2].upper() + uuid.uuid5(run_id, label).hex[:8],
                        "account_type": account_type, "reconcile": reconcile, "company_ids": [Command.set([company])]}, company=company)

    suspense, outstanding, liquidity = account("suspense", "asset_current", reconcile=True), account("outstanding", "asset_current", reconcile=True), account("liquidity", "asset_cash", reconcile=True)
    bank = fixture("account.journal", {"name": marker + "bank", "code": "B" + run_id.hex[:4], "type": "bank", "company_id": 1,
                                      "default_account_id": liquidity.id, "suspense_account_id": suspense.id})
    inbound = bank.inbound_payment_method_line_ids.filtered(lambda line: line.payment_method_id.code == "manual")
    assert len(inbound) == 1
    inbound.write({"payment_account_id": outstanding.id})  # Transaction-only fixture; business calls remain UID 5.
    invoice = env["account.move"].browse(write("customer_invoice.create", {"partner_id": ids["customer"], "journal_id": ids["sale_journal"],
        "date": today, "invoice_date": today, "currency_id": ids["currency"], "lines": [{"name": marker + "invoice", "account_id": ids["income"],
        "quantity": "1", "price_unit": "30", "tax_ids": []}]})["id"])
    write("invoice.post", {"move_id": invoice.id})

    def entry(label, debit_account, credit_account, amount, *, partner=None):
        move = env["account.move"].browse(write("journal_entry.create", {"journal_id": ids["general_journal"], "date": today, "reference": marker + label,
            "lines": [{"name": marker + label + "debit", "account_id": debit_account, "partner_id": partner, "debit": amount, "credit": "0"},
                      {"name": marker + label + "credit", "account_id": credit_account, "partner_id": partner, "debit": "0", "credit": amount, "date_maturity": today}]})["id"])
        write("journal_entry.post", {"move_id": move.id})
        return move

    ar = invoice.line_ids.filtered(lambda line: line.account_id.account_type == "asset_receivable")
    assert len(ar) == 1
    offset = entry("partial", ids["expense"], ar.account_id.id, "1", partner=invoice.partner_id.id)
    write("reconciliation.apply", {"line_ids": sorted([ar.id, offset.line_ids.filtered(lambda line: line.account_id == ar.account_id).id])})
    assert len(ar.matched_debit_ids | ar.matched_credit_ids) == 1 and not ar.full_reconcile_id
    invoice_snapshot, offset_snapshot = _graph(invoice), _graph(offset)

    usd = admin["res.currency"].with_context(active_test=False).search([("name", "=", "USD")], limit=1)
    eur = admin["res.currency"].with_context(active_test=False).search([("name", "=", "EUR")], limit=1)
    assert usd and eur and len({usd.id, eur.id, env.company.currency_id.id}) == 3
    for currency in (usd, eur):
        if not currency.active:
            currency.write({"active": True})  # Native activation and group effects are captured by the outer rollback snapshots.
    env.invalidate_all()
    user = admin["res.users"].browse(5)
    if not user.has_group("account.group_account_manager"):
        user.write({"group_ids": [Command.link(admin.ref("account.group_account_manager").id)]})
    env.invalidate_all()
    assert not env.su and env.company.root_id == env.company
    start = date(2100 + int(run_id.hex[:4], 16) % 300, 2, 10)
    assert not admin["res.currency.rate"].search([("currency_id", "=", usd.id), ("name", ">=", start), ("name", "<=", start + timedelta(days=4))])
    fallback = write("currency.rate.record", {"currency_id": usd.id, "date": start.isoformat(), "company_units_per_foreign_unit": "1.125"})
    rate = write("currency.rate.record", {"currency_id": usd.id, "date": (start + timedelta(days=1)).isoformat(), "company_units_per_foreign_unit": "7.123456"})
    rate_record = env["res.currency.rate"].browse(rate["id"])
    assert rate_record.company_id == env.company and rate_record.currency_id == usd
    new_date = start + timedelta(days=2)
    write("currency.rate.update", {"rate_id": rate["id"], "changes": {"date": new_date.isoformat(), "company_units_per_foreign_unit": "8.123456"}}, replay=True)
    # Exercise an actual quote correction after cache invalidation, not only its create-time protected value.
    env.invalidate_all()
    write("currency.rate.update", {"rate_id": rate["id"], "changes": {"company_units_per_foreign_unit": "7.123456"}}, replay=True)
    env.invalidate_all()
    write("currency.rate.update", {"rate_id": rate["id"], "changes": {"company_units_per_foreign_unit": "8.123456"}}, replay=True)
    assert rate_record.name == new_date and rate_record.currency_id == usd and rate_record.company_id == env.company

    def conversion():
        params = {"amount": "100", "from_currency_id": usd.id, "to_currency_id": env.company.currency_id.id, "date": new_date.isoformat()}
        value = _call(client, alias, run_id, "currency.convert", params)
        native = usd.with_env(env)._convert(100, env.company.currency_id, env.company, new_date)
        assert Decimal(value["converted_amount"]) == Decimal(str(native))
        return value["converted_amount"]

    changed_conversion = conversion()
    denied("currency.rate.update", {"rate_id": rate["id"], "changes": {"date": start.isoformat()}}, "idempotency_conflict", 5)
    foreign_rate = fixture("res.currency.rate", {"currency_id": usd.id, "company_id": 2, "name": new_date, "inverse_company_rate": 2}, company=2)
    global_rate = fixture("res.currency.rate", {"currency_id": usd.id, "company_id": False, "name": new_date, "inverse_company_rate": 3})
    for target in (foreign_rate, global_rate):
        denied("currency.rate.update", {"rate_id": target.id, "changes": {"company_units_per_foreign_unit": "4"}}, "record_not_found", 4)
        denied("currency.rate.delete", {"rate_id": target.id}, "record_not_found", 4)
    write("currency.rate.delete", {"rate_id": rate["id"]})
    assert not rate_record.exists() and env["res.currency.rate"].browse(fallback["id"]).exists()
    assert conversion() != changed_conversion
    denied("currency.rate.delete", {"rate_id": rate["id"]}, "record_not_found", 4)
    assert _graph(invoice) == invoice_snapshot and _graph(offset) == offset_snapshot

    foreign_liquidity = account("foreign-liquidity", "asset_cash", reconcile=True)
    foreign_bank = fixture("account.journal", {"name": marker + "foreign-bank", "code": "F" + run_id.hex[:4], "type": "bank", "company_id": 1,
                                               "currency_id": usd.id, "default_account_id": foreign_liquidity.id, "suspense_account_id": suspense.id})

    def transaction(journal, amount, label, **extra):
        value = write("bank.transaction.record", {"journal_id": journal.id, "date": today, "amount": amount,
                      "payment_ref": marker + label, "partner_id": ids["customer"], **extra}, replay=True)
        return env["account.bank.statement.line"].browse(value["id"])

    for amount, foreign_amount in (("100", "90"), ("-100", "-90")):
        line = transaction(foreign_bank, amount, amount, foreign_currency_id=eur.id, amount_currency=foreign_amount)
        native = _call(client, alias, run_id, "bank.transaction.reconciliation.get", {"transaction_id": line.id})["transaction"]
        assert native["foreign_currency_id"] == eur.id and Decimal(native["amount_currency"]) == Decimal(foreign_amount) and not native["is_reconciled"]
        write("bank.transaction.update", {"transaction_id": line.id, "changes": {"foreign_currency_id": None, "amount_currency": "0"}}, replay=True)
        assert not line.foreign_currency_id and line.amount_currency == 0 and not line.is_reconciled
        write("bank.transaction.update", {"transaction_id": line.id, "changes": {"foreign_currency_id": eur.id, "amount_currency": foreign_amount}}, replay=True)
        assert line.foreign_currency_id == eur and Decimal(str(line.amount_currency)) == Decimal(foreign_amount) and line.move_id.state == "posted" and not line.is_reconciled
    foreign_snapshot = _graph(line.move_id)
    denied("bank.transaction.record", {"journal_id": foreign_bank.id, "date": today, "amount": "100", "payment_ref": marker + "same-currency",
           "partner_id": ids["customer"], "foreign_currency_id": usd.id, "amount_currency": "90"}, "business_rule_error", 6)
    denied("bank.transaction.update", {"transaction_id": line.id, "changes": {"foreign_currency_id": usd.id, "amount_currency": "-90"}}, "business_rule_error", 6)
    assert _graph(line.move_id) == foreign_snapshot

    transactions = [transaction(bank, amount, "membership" + amount) for amount in ("30", "2", "3")]
    # Native matching negates the source residual: incoming liquidity debit needs an outstanding debit source.
    match_source = entry("bank-match", outstanding.id, ids["expense"], "30", partner=ids["customer"])
    candidate = match_source.line_ids.filtered(lambda line: line.account_id == outstanding)
    assert candidate.balance == transactions[0].amount == 30
    matched = write("bank.transaction.match", {"transaction_id": transactions[0].id, "candidate_line_ids": candidate.ids})
    native_match = _call(client, alias, run_id, "bank.transaction.reconciliation.get", {"transaction_id": transactions[0].id})
    assert transactions[0].is_reconciled and matched["reconciled"] and native_match["transaction"]["is_reconciled"], {
        "write_result": matched, "native_readback": native_match, "source_lines": candidate.read(_FINANCIAL, load=None)}
    assert candidate.reconciled and candidate.currency_id.is_zero(candidate.amount_residual_currency)
    matched_snapshot, candidate_snapshot = _graph(transactions[0].move_id), _graph(match_source)
    denied("bank.transaction.update", {"transaction_id": transactions[0].id, "changes": {"foreign_currency_id": eur.id, "amount_currency": "20"}}, "state_conflict", 5)
    statement = write("bank.statement.create", {"transaction_ids": sorted(line.id for line in transactions[:2]), "reference": marker, "balance_end_real": "32"})
    write("bank.statement.update", {"statement_id": statement["id"], "changes": {"transaction_ids": sorted(line.id for line in transactions)}}, replay=True)
    assert _graph(transactions[0].move_id) == matched_snapshot and _graph(match_source) == candidate_snapshot
    write("bank.statement.update", {"statement_id": statement["id"], "changes": {"transaction_ids": sorted(line.id for line in transactions[1:])}}, replay=True)
    assert transactions[0].exists() and transactions[0].move_id.exists() and not transactions[0].statement_id and transactions[0].is_reconciled
    assert _graph(transactions[0].move_id) == matched_snapshot and _graph(match_source) == candidate_snapshot
    fourth = transaction(bank, "4", "other-statement")
    other = write("bank.statement.create", {"transaction_ids": [fourth.id], "reference": marker + "other", "balance_end_real": "4"})
    denied("bank.statement.update", {"statement_id": statement["id"], "changes": {"transaction_ids": sorted([transactions[1].id, transactions[2].id, fourth.id])}}, "state_conflict", 5)
    assert fourth.statement_id.id == other["id"]
    denied("bank.statement.update", {"statement_id": statement["id"], "changes": {"transaction_ids": sorted([transactions[0].id, transactions[2].id])}}, "state_conflict", 5)
    denied("bank.statement.update", {"statement_id": statement["id"], "changes": {"transaction_ids": [line.id]}}, "record_not_found", 4)
    empty = _call(client, alias, run_id, "bank.statement.update", {"statement_id": statement["id"], "changes": {"transaction_ids": []}}, key="empty-membership", exit_code=2)
    assert empty["error"]["code"] == "invalid_request" and empty["data"] is None, empty

    bank_account = fixture("res.partner.bank", {"acc_number": marker + "recipient", "partner_id": env.company.partner_id.id, "company_id": 1})
    write("invoice.update", {"move_id": invoice.id, "changes": {"partner_bank_id": bank_account.id}}, replay=True)
    assert invoice.partner_bank_id.id == bank_account.id
    write("invoice.update", {"move_id": invoice.id, "changes": {"partner_bank_id": None}}, replay=True)
    assert not invoice.partner_bank_id
    write("invoice.payment_method.assign", {"move_id": invoice.id, "payment_method_line_id": inbound.id}, replay=True)
    wizard = track(env["account.payment.register"].with_context(active_model="account.move", active_ids=invoice.ids).create({"journal_id": bank.id}))
    assert wizard.payment_method_line_id.id == inbound.id and invoice.preferred_payment_method_line_id.id == inbound.id
    write("invoice.payment_method.assign", {"move_id": invoice.id, "payment_method_line_id": None}, replay=True)
    incoterm = fixture("account.incoterms", {"name": marker + "incoterm", "code": "M" + run_id.hex[:4]})
    write("invoice.incoterm.update", {"move_id": invoice.id, "changes": {"incoterm_id": incoterm.id, "incoterm_location": "Shanghai"}}, replay=True)
    assert invoice.invoice_incoterm_id == incoterm and invoice.incoterm_location == "Shanghai"
    write("invoice.incoterm.update", {"move_id": invoice.id, "changes": {"incoterm_id": None, "incoterm_location": None}}, replay=True)
    assert not invoice.invoice_incoterm_id and not invoice.incoterm_location
    admin["account.move"].browse(invoice.id).write({"is_move_sent": True})
    env.invalidate_all()
    denied("invoice.update", {"move_id": invoice.id, "changes": {"partner_bank_id": None}}, "state_conflict", 5)
    admin["account.move"].browse(invoice.id).write({"is_move_sent": False})
    # Native linking marks an invoice sent; this fixture neither generates a PDF nor sends anything.
    admin_move = admin["account.move"].browse(invoice.id)
    pdf_bytes = b"%PDF-1.4\nrollback-only database fixture"
    admin["account.move.send"]._link_invoice_documents({admin_move: {"pdf_attachment_values": {
        "name": marker + ".pdf", "res_model": "account.move", "res_id": invoice.id, "res_field": "invoice_pdf_report_file",
        "type": "binary", "db_datas": pdf_bytes, "mimetype": "application/pdf"}}})
    attachment = track(admin_move.invoice_pdf_report_id)
    env.invalidate_all()
    assert not attachment.store_fname and attachment.db_datas == pdf_bytes and attachment.raw == pdf_bytes
    assert invoice.invoice_pdf_report_id.id == attachment.id and invoice.is_move_sent
    denied("invoice.update", {"move_id": invoice.id, "changes": {"partner_bank_id": None}}, "state_conflict", 5)
    assert _graph(invoice) == invoice_snapshot and _graph(offset) == offset_snapshot
    assert not env["account.payment"].search([("reconciled_invoice_ids", "in", invoice.ids)])
    # Keep foreign fixtures last: successful UID5 calls collect only current-company related objects.
    other_liquidity, other_suspense = account("other-liquidity", "asset_cash", company=2, reconcile=True), account("other-suspense", "asset_current", company=2, reconcile=True)
    other_bank = fixture("account.journal", {"name": marker + "company2-bank", "code": "O" + run_id.hex[:4], "type": "bank", "company_id": 2,
                                           "default_account_id": other_liquidity.id, "suspense_account_id": other_suspense.id}, company=2)
    other_line = fixture("account.bank.statement.line", {"journal_id": other_bank.id, "date": today, "amount": 1, "payment_ref": marker + "company2-line"}, company=2)
    denied("bank.statement.update", {"statement_id": statement["id"], "changes": {"transaction_ids": [other_line.id]}}, "record_not_found", 4)
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
    cursor, marker = registry.cursor(), f"ODACV4-MAINTENANCE-{args.alias}-{args.run_id.hex}"
    tracked, groups, company_fields, settings, defaults, currencies, failure = {}, None, [], None, None, None, None
    try:
        context = {"allowed_company_ids": [1], "lang": "en_US", "tz": "Asia/Shanghai", "tracking_disable": True, "mail_create_nosubscribe": True, "mail_notrack": True}
        admin = api.Environment(cursor, SUPERUSER_ID, context)
        user = admin["res.users"].browse(5).exists()
        assert user.active and user.login == lifecycle._USER_LOGIN and user.has_group("account.group_account_user")
        groups = _groups(admin)
        company_fields = sorted(name for name, field in admin["res.company"]._fields.items() if field.store and field.type not in {"binary", "one2many", "many2many"})
        settings, defaults, currencies = company_batch._company_snapshot(admin, company_fields), preparation._defaults(admin), workflows._currency_snapshot(admin)
        client = _Client(api.Environment(cursor, 5, context))
        client.tracked = {model: set() for model in _MODELS}
        tracked = client.tracked
        _exercise(admin, client, args.alias, args.run_id, marker)
        assert company_batch._company_snapshot(admin, company_fields)[1] == settings[1]
        core._collect_related(admin, tracked)
    except BaseException as exc:  # noqa: BLE001 - verify full rollback before propagating any native or assertion failure.
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
            for model in ("account.account", "account.journal", "account.incoterms", "ir.attachment"):
                assert not verify[model].with_context(active_test=False).search_count([("name", "ilike", marker)])
            assert not verify["account.move.line"].search_count([("name", "ilike", marker)])
            if groups is not None:
                assert _groups(verify) == groups
                assert company_batch._company_snapshot(verify, company_fields) == settings and preparation._defaults(verify) == defaults and workflows._currency_snapshot(verify) == currencies
        finally:
            verify_cursor.rollback()
    if failure is not None:
        raise failure
    print(json.dumps(_summary(args.alias, args.database), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_live_worker())
