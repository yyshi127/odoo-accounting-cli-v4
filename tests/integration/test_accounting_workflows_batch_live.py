"""One public CLI/ordinary-user native workflow; every mutation is rolled back."""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import sysconfig
import uuid
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import test_company_processing_batch_live as company_batch
import test_document_lifecycle_write_batch_live as lifecycle
import test_invoice_preparation_batch_live as preparation
import test_payment_bank_capability_batch_live as core
import test_report_budget_write_batch_live as shared

try:
    import pytest
except ModuleNotFoundError:
    if "--live-worker" not in sys.argv:
        raise
    pytest = None

_ALLOW_ENV = "ODACV4_ALLOW_ACCOUNTING_WORKFLOWS_SMOKE"
_GROUPS = ("base.group_erp_manager", "account.group_account_manager")
_TARGETS = {"invoice.reverse_and_reissue", "company.default_accounts.assign", "company.bank_defaults.assign",
            "company.discount_allocation_accounts.assign", "journal_entry.lines.update", "reconciliation.undo",
            "bank.transaction.search", "payment.get", "company.processing_settings.get", "journal.sequence_policy.update"}
_MODELS = tuple(dict.fromkeys((*core._BUSINESS_MODELS, "account.bank.statement", "account.account", "account.journal",
                             "mail.alias", "account.payment.method.line", "account.move.reversal", "account.payment.register", "product.product", "product.template", "product.category")))


def _root():
    return Path(__file__).resolve().parents[2]


def _summary(alias, database):
    return {"alias": alias, "database": database, "company_id": 1, "user_id": 5, "business_su": False,
            "target_capabilities": sorted(_TARGETS), "execution": "in_process_cli_real_orm",
            "sale_purchase_native_reverse_reissue_two_results_and_replay_verified": True,
            "foreign_currency_existing_line_update_precision_atomicity_verified": True,
            "partial_full_match_group_leaf_undo_and_shrinking_replay_verified": True,
            "statement_pagination_scope_and_native_payment_bank_refs_verified": True,
            "company_account_assign_clear_read_replay_and_product_fallback_verified": True,
            "native_purchase_self_billing_sequence_verified": True,
            "full_fixture_settings_defaults_currency_and_all_user_groups_rollback_verified": True}


class _Client(core._RuntimeClient):
    def invoke(self, action, payload):
        try:
            with self.env.cr.savepoint():
                # The legacy parent interprets line_ids as journal items. A bank
                # statement instead returns bank transaction IDs.
                statement_ids = self.tracked.pop("account.bank.statement", None)
                try:
                    page = super().invoke(action, payload)
                finally:
                    if statement_ids is not None:
                        self.tracked["account.bank.statement"] = statement_ids
                value = page.get("result") or {}
                if value.get("model") == "account.bank.statement":
                    self.tracked["account.bank.statement"].add(value["id"])
                    self.tracked["account.bank.statement.line"].update(value["line_ids"])
                for item in value.get("items", []):
                    assert item["model"] == "account.move"
                    self.tracked["account.move"].add(item["id"])
                    self.tracked["account.move.line"].update(item["line_ids"])
                    self.tracked["account.partial.reconcile"].update(item["partial_reconcile_ids"])
                    if item["full_reconcile_id"]:
                        self.tracked["account.full.reconcile"].add(item["full_reconcile_id"])
                core._collect_related(self.env, self.tracked)
                return page
        finally:
            for record_ids in self.tracked.values():
                record_ids.discard(None)


if pytest is not None:
    @pytest.mark.integration
    def test_accounting_workflows_roll_back_per_alias():
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


def _currency_snapshot(env):
    return (env["res.currency"].with_context(active_test=False).search([], order="id").read(["id", "active", "rounding"]),
            env["res.currency.rate"].search([], order="id").read(["id", "currency_id", "company_id", "name", "rate"]))


def _call(client, alias, run_id, capability, parameters, *, exit_code=0, key=None):
    from odoo_accounting_cli_v4 import cli
    from odoo_accounting_cli_v4.bridge.bank_transactions import (
        OdooBankTransactionListPort,
        OdooBankTransactionSearchPort,
    )
    from odoo_accounting_cli_v4.bridge.core_object_reads import OdooCoreObjectReadPort
    from odoo_accounting_cli_v4.bridge.core_writes import OdooCoreWritePort
    from odoo_accounting_cli_v4.bridge.payments import OdooPaymentPort

    port = OdooCoreWritePort(client) if key is not None else OdooBankTransactionSearchPort(client) if capability == "bank.transaction.search" else OdooBankTransactionListPort(client) if capability == "bank.transaction.list" else OdooPaymentPort(client) if capability == "payment.get" else OdooCoreObjectReadPort(client)
    argv = ["write", "run", capability, "--request", "-", "--confirm", capability, "--idempotency-key", key] if key is not None else ["read", capability, "--request", "-"]
    stdout, stderr = io.StringIO(), io.StringIO()
    client.last_runtime_failure = None
    code = cli.main(argv, stdin=io.StringIO(json.dumps(core._request(alias, run_id, capability, parameters))), stdout=stdout, stderr=stderr, port_factory=lambda *args: port)
    response = json.loads(stdout.getvalue())
    assert code == exit_code and not stderr.getvalue(), response
    assert client.env.uid == 5 and not client.env.su and client.env.company.id == 1
    if code:
        assert not response["success"]
        if client.last_runtime_failure is not None:
            assert all(response["odoo"][field] is None for field in ("database", "company_id", "user_id", "model"))
        return response
    assert response["success"] and response["status"] == "verified" and response["odoo"]["user_id"] == 5
    client.capabilities.add(capability)
    return response["data"]


def _exercise(admin, client, alias, run_id, marker):
    from odoo import Command, fields

    from odoo_accounting_cli_v4 import company_processing_contracts as company_contract
    from odoo_accounting_cli_v4.capabilities.core_writes import (
        _expected_idempotency_key,
        validate_core_write_request,
    )

    env, ids = client.env, lifecycle._fixture_ids(admin, alias)
    today = fields.Date.context_today(env.user)
    financial = ["id", "account_id", "balance", "debit", "credit", "currency_id", "amount_currency", "date_maturity"]

    def track(record):
        client.tracked[record._name].update(record.ids)
        if record._name == "account.move":
            client.tracked["account.move.line"].update(record.line_ids.ids)
        if record._name == "product.product":
            client.tracked["product.template"].update(record.product_tmpl_id.ids)
        if record._name == "account.journal":
            client.tracked["mail.alias"].update(record.alias_id.ids)
            client.tracked["account.payment.method.line"].update((record.inbound_payment_method_line_ids | record.outbound_payment_method_line_ids).ids)
        return record

    def fixture(model, values, *, company=1):
        return track(admin[model].with_company(admin["res.company"].browse(company)).create(values))

    def read(capability, params, **kwargs):
        return _call(client, alias, run_id, capability, params, **kwargs)

    def write(capability, params, *, replay=False, shrinking=False):
        normalized = validate_core_write_request(capability, core._request(alias, run_id, capability, params))[2]
        key = _expected_idempotency_key(capability, normalized, 1) or f"{capability}:{run_id.hex}:{lifecycle._canonical_digest(normalized)[:32]}"
        first = _call(client, alias, run_id, capability, params, key=key)
        assert not first["idempotent_replay"], first
        value = first["result"]
        items = value.get("items", [value])
        for item in items:
            if item.get("model") in {"account.move", "account.payment", "account.bank.statement.line", "account.bank.statement"} and item["id"]:
                track(env[item["model"]].browse(item["id"]))
        if replay:
            second = _call(client, alias, run_id, capability, params, key=key)
            assert second["idempotent_replay"] and (shrinking or second["result"] == value), second
            if shrinking:
                assert second["result"]["line_ids"] == params["line_ids"] and not second["result"]["partial_reconcile_ids"]
        return value

    def denied(capability, params, error, code):
        normalized = validate_core_write_request(capability, core._request(alias, run_id, capability, params))[2]
        key = _expected_idempotency_key(capability, normalized, 1) or f"{capability}:{run_id.hex}:denied"
        response = _call(client, alias, run_id, capability, params, key=key, exit_code=code)
        assert response["error"]["code"] == error, response

    def document(capability, suffix, *, journal_id=None, price="20"):
        supplier = capability == "vendor_bill.create"
        value = write(capability, {"partner_id": ids["supplier" if supplier else "customer"], "journal_id": journal_id or ids["purchase_journal" if supplier else "sale_journal"],
            "date": (today - timedelta(days=1)).isoformat(), "invoice_date": (today - timedelta(days=1)).isoformat(), "currency_id": ids["currency"],
            "lines": [{"name": marker + suffix, "account_id": ids["expense" if supplier else "income"], "quantity": "1", "price_unit": price, "tax_ids": []}]})
        return env["account.move"].browse(value["id"])

    # Native modify_moves returns a posted refund and a fresh draft replacement.
    for capability, move_type in (("customer_invoice.create", "out_invoice"), ("vendor_bill.create", "in_invoice")):
        source = document(capability, "reissue" + move_type)
        denied("invoice.reverse_and_reissue", {"move_id": source.id, "date": today.isoformat(), "reason": marker}, "state_conflict", 5)
        write("invoice.post", {"move_id": source.id})
        original = source.line_ids.read(financial)
        denied("invoice.reverse_and_reissue", {"move_id": source.id, "date": (today + timedelta(days=1)).isoformat(), "reason": marker}, "business_rule_error", 6)
        assert source.line_ids.read(financial) == original and not source.reversal_move_ids
        value = write("invoice.reverse_and_reissue", {"move_id": source.id, "date": today.isoformat(), "reason": marker + move_type}, replay=True)
        assert value["processed_count"] == 2 and [item["id"] for item in value["items"]] == sorted(item["id"] for item in value["items"])
        moves = env["account.move"].browse([item["id"] for item in value["items"]])
        refund, replacement = moves.filtered(lambda move: bool(move.reversed_entry_id)), moves.filtered(lambda move: not move.reversed_entry_id)
        assert len(refund) == len(replacement) == 1 and refund.reversed_entry_id == source and refund.state == "posted"
        assert replacement.move_type == move_type and replacement.state == "draft" and not replacement.invoice_date
        assert refund.date == today and source.date == today - timedelta(days=1)
        assert source.line_ids.read(financial) == original and all(item["source_id"] == source.id for item in value["items"])

    def entry(amount, suffix, *, account_id=None, credit=False):
        a, b = ("0", amount) if credit else (amount, "0")
        value = write("journal_entry.create", {"journal_id": ids["general_journal"], "date": today.isoformat(), "reference": marker + suffix,
            "lines": [{"name": marker + "target", "account_id": account_id or ids["expense"], "partner_id": None, "debit": a, "credit": b},
                      {"name": marker + "offset", "account_id": ids["income"], "partner_id": None, "debit": b, "credit": a}]})
        return env["account.move"].browse(value["id"])

    draft = entry("20", "foreign-currency")
    lines = draft.line_ids.sorted("id")
    usd = env["res.currency"].search([("name", "=", "USD"), ("active", "=", True)], limit=1)
    assert usd and usd != env.company.currency_id and usd.decimal_places == 2
    update = {"move_id": draft.id, "lines": [{"line_id": line.id, "changes": {"currency_id": usd.id, "amount_currency": "3" if line.balance > 0 else "-3", "debit": "25" if line.balance > 0 else "0", "credit": "25" if line.balance < 0 else "0"}} for line in lines]}
    write("journal_entry.lines.update", update, replay=True)
    assert set(draft.line_ids.ids) == set(lines.ids) and all(line.currency_id == usd and abs(line.amount_currency) == 3 for line in lines)
    assert draft.company_currency_id.is_zero(sum(lines.mapped("balance")))
    positive = lines.filtered(lambda line: line.balance > 0)
    write("journal_entry.lines.update", {"move_id": draft.id, "lines": [{"line_id": line.id, "changes": {"amount_currency": "3.01" if line.balance > 0 else "-3.01"}} for line in lines]}, replay=True)
    assert all(abs(Decimal(str(line.amount_currency))) == Decimal("3.01") for line in lines)
    assert set(draft.line_ids.ids) == set(lines.ids) and draft.company_currency_id.is_zero(sum(lines.mapped("balance")))
    before = draft.line_ids.read(financial)
    denied("journal_entry.lines.update", {"move_id": draft.id, "lines": [{"line_id": positive.id, "changes": {"amount_currency": "3.001"}}]}, "business_rule_error", 6)
    denied("journal_entry.lines.update", {"move_id": draft.id, "lines": [{"line_id": positive.id, "changes": {"debit": "26"}}]}, "business_rule_error", 6)
    assert draft.line_ids.read(financial) == before
    write("journal_entry.post", {"move_id": draft.id})
    denied("journal_entry.lines.update", update, "state_conflict", 5)
    assert draft.line_ids.read(financial) == before

    reconcilable = fixture("account.account", {"name": marker + "matching", "code": "AW" + run_id.hex[:8], "account_type": "asset_current", "reconcile": True, "company_ids": [Command.set([1])]})
    for last in ("50", "20"):
        moves = [entry(amount, "graph" + last + amount, account_id=reconcilable.id, credit=index > 0) for index, amount in enumerate(("120", "70", last))]
        for move in moves:
            write("journal_entry.post", {"move_id": move.id})
        targets = [move.line_ids.filtered(lambda line: line.account_id.id == reconcilable.id) for move in moves]
        for counterpart in targets[1:]:
            write("reconciliation.apply", {"line_ids": sorted([targets[0].id, counterpart.id])})
        original = [move.line_ids.read(financial) for move in moves]
        partials = targets[0].matched_debit_ids | targets[0].matched_credit_ids
        assert len(partials) == 2 and bool(targets[0].full_reconcile_id) is (last == "50")
        denied("reconciliation.undo", {"line_ids": sorted([targets[0].id, targets[1].id])}, "state_conflict", 5)
        value = write("reconciliation.undo", {"mode": "match_group", "line_ids": [targets[1].id]}, replay=True, shrinking=True)
        assert value["line_ids"] == sorted(line.id for line in targets)
        assert not partials.exists() and not value["partial_reconcile_ids"] and value["full_reconcile_id"] is None
        for line in targets:
            actual = read("journal_item.reconciliation.inspect", {"journal_item_id": line.id})
            assert not actual["partial_reconcile_ids"] and actual["full_reconcile_id"] is None
            assert line.currency_id.is_zero(line.amount_residual - line.balance)
        assert [move.line_ids.read(financial) for move in moves] == original

    # Match a real payment's outstanding line to a bank transaction, then group two transactions.
    liquidity = fixture("account.account", {"name": marker + "liquidity", "code": "AL" + run_id.hex[:8], "account_type": "asset_cash", "reconcile": True, "company_ids": [Command.set([1])]})
    outstanding_account = fixture("account.account", {"name": marker + "outstanding", "code": "AO" + run_id.hex[:8], "account_type": "asset_current", "reconcile": True, "company_ids": [Command.set([1])]})
    bank = fixture("account.journal", {"name": marker + "bank", "code": "B" + run_id.hex[:4], "type": "bank", "company_id": 1, "default_account_id": liquidity.id, "suspense_account_id": reconcilable.id})
    inbound = bank.inbound_payment_method_line_ids.filtered(lambda line: line.payment_method_id.code == "manual")
    assert len(inbound) == 1
    inbound.write({"payment_account_id": outstanding_account.id})
    ids["bank_journal"] = bank.id
    source = document("customer_invoice.create", "matched-payment", price="30")
    write("invoice.post", {"move_id": source.id})
    payment = write("receivable.payment.register", {"move_id": source.id, "journal_id": ids["bank_journal"], "payment_date": today.isoformat()})
    initial_payment = read("payment.get", {"payment_id": payment["id"]})
    assert initial_payment["reconciled_bank_transactions"] == []
    transactions = [write("bank.transaction.record", {"journal_id": ids["bank_journal"], "date": today.isoformat(), "amount": amount, "payment_ref": marker + amount, "partner_id": ids["customer"]}) for amount in ("30", "1")]
    payment_record = env["account.payment"].browse(payment["id"])
    outstanding = payment_record.move_id.line_ids.filtered(lambda line: line.account_id == payment_record.outstanding_account_id)
    assert len(outstanding) == 1
    write("bank.transaction.match", {"transaction_id": transactions[0]["id"], "candidate_line_ids": outstanding.ids})
    matched = read("payment.get", {"payment_id": payment["id"]})
    assert matched["reconciled_bank_transactions"] == [{"id": transactions[0]["id"], "company_id": 1}]
    assert payment_record.reconciled_statement_line_ids.ids == [transactions[0]["id"]]
    statement = write("bank.statement.create", {"transaction_ids": sorted(item["id"] for item in transactions), "reference": marker, "balance_end_real": "31"})
    transaction_get = read("bank.transaction.get", {"transaction_id": transactions[0]["id"]})
    assert transaction_get["statement_id"] == statement["id"]
    all_rows = read("bank.transaction.list", {"limit": 1000, "cursor": None})
    statement_rows = [row for row in all_rows["items"] if row["id"] in {item["id"] for item in transactions}]
    assert len(statement_rows) == 2 and all(row["statement_id"] == statement["id"] for row in statement_rows)
    params = {"statement_id": statement["id"], "limit": 1, "cursor": None}
    page = read("bank.transaction.search", params)
    assert page["has_more"] and page["next_cursor"] and page["items"][0]["statement_id"] == statement["id"]
    second = read("bank.transaction.search", {**params, "cursor": page["next_cursor"]})
    assert not second["has_more"] and {page["items"][0]["id"], second["items"][0]["id"]} == {item["id"] for item in transactions}
    invalid = read("bank.transaction.search", {**params, "statement_id": statement["id"] + 1, "cursor": page["next_cursor"]}, exit_code=2)
    assert invalid["error"]["code"] == "invalid_cursor"

    # Configuration permissions are native, granted only within this transaction.
    config_income = fixture("account.account", {"name": marker + "income", "code": "AI" + run_id.hex[:8], "account_type": "income", "company_ids": [Command.set([1])]})
    config_expense = fixture("account.account", {"name": marker + "expense", "code": "AE" + run_id.hex[:8], "account_type": "expense", "company_ids": [Command.set([1])]})
    if not env.user.has_group("base.group_erp_manager"):
        denied("company.default_accounts.assign", {"changes": {"income_account_id": config_income.id}}, "unauthorized", 3)
    for name in _GROUPS:
        if not admin["res.users"].browse(5).has_group(name):
            admin["res.users"].browse(5).write({"group_ids": [Command.link(admin.ref(name).id)]})
    env.invalidate_all()
    assert not env.su and env["res.company"].has_access("write")
    category = fixture("product.category", {"name": marker + "category"})
    product = fixture("product.product", {"name": marker + "product", "categ_id": category.id, "property_account_income_id": False, "property_account_expense_id": False})
    changes = {"company.default_accounts.assign": {"income_account_id": config_income.id, "expense_account_id": config_expense.id},
               "company.bank_defaults.assign": {"account_journal_suspense_account_id": reconcilable.id, "transfer_account_id": reconcilable.id},
               "company.discount_allocation_accounts.assign": {"account_discount_income_allocation_id": config_income.id, "account_discount_expense_allocation_id": config_expense.id}}
    for capability, values in changes.items():
        write(capability, {"changes": values}, replay=True)
    current = read("company.processing_settings.get", {})
    assert company_contract.valid_read_item(current, 1) and all(current[field] == value for values in changes.values() for field, value in values.items())
    # Category getters include defaults. Clearing only these transaction-local prerequisites
    # makes the native company fallback observable, without touching stock defaults.
    for field in ("property_account_income_categ_id", "property_account_expense_categ_id"):
        admin["ir.default"].set("product.category", field, False, company_id=1)
    admin["product.category"].browse(category.id).write({"property_account_income_categ_id": False, "property_account_expense_categ_id": False})
    resolved = read("product.accounts.resolve", {"product_id": product.id, "fiscal_position_id": None})
    native = env["product.product"].browse(product.id).product_tmpl_id.get_product_accounts()
    assert resolved["income_account_id"] == native["income"].id == config_income.id
    assert resolved["expense_account_id"] == native["expense"].id == config_expense.id
    foreign_account = fixture("account.account", {"name": marker + "foreign", "code": "AF" + run_id.hex[:8], "account_type": "income", "company_ids": [Command.set([2])]}, company=2)
    denied("company.default_accounts.assign", {"changes": {"income_account_id": foreign_account.id}}, "record_not_found", 4)
    for capability, values in changes.items():
        write(capability, {"changes": dict.fromkeys(values)}, replay=True)
    cleared = read("company.processing_settings.get", {})
    assert all(cleared[field] is None for values in changes.values() for field in values)
    purchase = fixture("account.journal", {"name": marker + "self-billing", "code": "S" + run_id.hex[:4], "type": "purchase", "company_id": 1, "default_account_id": ids["expense"]})
    write("journal.sequence_policy.update", {"journal_id": purchase.id, "changes": {"is_self_billing": True}}, replay=True)
    journal_read = read("journal.processing_settings.get", {"journal_id": purchase.id})
    assert journal_read["is_self_billing"] is True
    self_bill = document("vendor_bill.create", "self-bill", journal_id=purchase.id)
    write("invoice.post", {"move_id": self_bill.id})
    sequence = self_bill._get_starting_sequence()
    assert sequence.startswith(purchase.code + str(self_bill.partner_id.commercial_partner_id.id).zfill(5) + "/")
    assert self_bill.name.startswith(sequence.rsplit("/", 1)[0] + "/")
    denied("journal.sequence_policy.update", {"journal_id": ids["sale_journal"], "changes": {"is_self_billing": True}}, "business_rule_error", 6)
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
    cursor, marker = registry.cursor(), f"ODACV4-WORKFLOW-{args.alias}-{args.run_id.hex}"
    tracked, groups, direct_groups, company_fields, settings, defaults, currencies, wizard_ids, failure = {}, None, {}, [], None, None, None, None, None
    try:
        context = {"allowed_company_ids": [1], "lang": "en_US", "tz": "Asia/Shanghai", "tracking_disable": True, "mail_create_nosubscribe": True, "mail_notrack": True}
        admin = api.Environment(cursor, SUPERUSER_ID, context)
        user = admin["res.users"].browse(5).exists()
        assert user.active and user.login == lifecycle._USER_LOGIN and user.has_group("account.group_account_user")
        groups = sorted(user.group_ids.ids)
        direct_groups = {admin.ref(name).id: shared._direct_group(cursor, admin.ref(name).id) for name in _GROUPS}
        company_fields = sorted(name for name, field in admin["res.company"]._fields.items() if field.store and field.type not in {"binary", "one2many", "many2many"})
        settings, defaults, currencies = company_batch._company_snapshot(admin, company_fields), preparation._defaults(admin), _currency_snapshot(admin)
        wizard_ids = set(admin["account.payment.register"].search([]).ids)
        client = _Client(api.Environment(cursor, 5, context))
        client.tracked = {model: set() for model in _MODELS}
        tracked = client.tracked
        _exercise(admin, client, args.alias, args.run_id, marker)
        assert company_batch._company_snapshot(admin, company_fields)[1] == settings[1]
        core._collect_related(admin, tracked)
        tracked["account.move.reversal"].update(admin["account.move.reversal"].search([("reason", "ilike", marker)]).ids)
        tracked["account.payment.register"].update(set(admin["account.payment.register"].search([]).ids) - wizard_ids)
    except BaseException as exc:  # noqa: BLE001 - failures also get full transaction rollback.
        failure = exc
    finally:
        cursor.rollback()
        cursor.close()
    with registry.cursor() as verify_cursor:
        try:
            verify = api.Environment(verify_cursor, SUPERUSER_ID, {"allowed_company_ids": [1, 2], "lang": "en_US"})
            for model, ids in tracked.items():
                remaining = verify[model].with_context(active_test=False).search([("id", "in", sorted(ids))]).ids
                assert not remaining, (model, remaining)
            for model in ("account.account", "account.journal", "product.template", "product.category"):
                assert not verify[model].with_context(active_test=False).search_count([("name", "ilike", marker)])
            assert not verify["account.move"].search_count([("ref", "ilike", marker)]) and not verify["account.move.line"].search_count([("name", "ilike", marker)])
            assert not verify["account.move.reversal"].search_count([("reason", "ilike", marker)])
            if groups is not None:
                assert sorted(verify["res.users"].browse(5).group_ids.ids) == groups
                assert all(shared._direct_group(verify_cursor, group_id) == members for group_id, members in direct_groups.items())
                assert company_batch._company_snapshot(verify, company_fields) == settings and preparation._defaults(verify) == defaults and _currency_snapshot(verify) == currencies
                assert set(verify["account.payment.register"].search([]).ids) == wizard_ids
        finally:
            verify_cursor.rollback()
    if failure is not None:
        raise failure
    print(json.dumps(_summary(args.alias, args.database), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_live_worker())
