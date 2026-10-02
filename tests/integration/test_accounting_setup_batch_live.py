"""One ordinary-user CLI/native workflow; fixtures and configuration are rolled back."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import sysconfig
import uuid
from decimal import Decimal
from pathlib import Path

import test_accounting_workflows_batch_live as workflows
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

_ALLOW_ENV = "ODACV4_ALLOW_ACCOUNTING_SETUP_SMOKE"
_GROUPS = ("base.group_erp_manager", "account.group_account_manager")
_TARGETS = {"company.cash_basis_configuration.update", "company.processing_settings.get", "tax.create", "tax.update",
            "invoice.update", "journal_entry.update", "invoice.presentation_settings.update", "cash_rounding.compute"}
_MODELS = tuple(dict.fromkeys((*core._BUSINESS_MODELS, "account.account", "account.journal", "mail.alias",
                             "account.payment.method.line", "account.tax", "account.tax.repartition.line", "account.tax.group", "account.cash.rounding")))


def _root():
    return Path(__file__).resolve().parents[2]


def _summary(alias, database):
    return {"alias": alias, "database": database, "company_id": 1, "user_id": 5, "business_su": False,
            "target_capabilities": sorted(_TARGETS), "execution": "in_process_cli_real_orm",
            "native_company_cash_basis_set_clear_replay_without_ui_onchange_or_tax_cleanup_verified": True,
            "native_advanced_group_tax_fields_and_invoice_computation_verified": True,
            "posted_invoice_entry_nonfinancial_header_and_presentation_replays_verified": True,
            "posted_financial_line_and_amount_preservation_and_restricted_field_denials_verified": True,
            "native_partial_invoice_header_presentation_and_reconciliation_graph_preservation_verified": True,
            "signed_zero_minor_unit_cash_rounding_native_computation_verified": True,
            "full_fixtures_company_settings_defaults_currency_and_all_user_groups_rollback_verified": True}


if pytest is not None:
    @pytest.mark.integration
    def test_accounting_setup_rolls_back_per_alias():
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

    from odoo_accounting_cli_v4 import company_processing_contracts as company_contract
    from odoo_accounting_cli_v4.capabilities.core_writes import (
        _expected_idempotency_key,
        validate_core_write_request,
    )

    env, ids = client.env, lifecycle._fixture_ids(admin, alias)
    today = fields.Date.context_today(env.user).isoformat()
    financial = ["id", "account_id", "partner_id", "balance", "debit", "credit", "currency_id", "amount_currency", "date_maturity",
                 "tax_ids", "tax_line_id", "tax_repartition_line_id", "matched_debit_ids", "matched_credit_ids", "full_reconcile_id"]

    def track(record):
        client.tracked[record._name].update(record.ids)
        if record._name == "account.move":
            client.tracked["account.move.line"].update(record.line_ids.ids)
        if record._name == "account.tax":
            client.tracked["account.tax.repartition.line"].update(record.repartition_line_ids.ids)
        if record._name == "account.journal":
            client.tracked["mail.alias"].update(record.alias_id.ids)
            client.tracked["account.payment.method.line"].update((record.inbound_payment_method_line_ids | record.outbound_payment_method_line_ids).ids)
        return record

    def fixture(model, values, *, company=1):
        return track(admin[model].with_company(admin["res.company"].browse(company)).create(values))

    def read(capability, params, **kwargs):
        return workflows._call(client, alias, run_id, capability, params, **kwargs)

    def write(capability, params, *, replay=False):
        normalized = validate_core_write_request(capability, core._request(alias, run_id, capability, params))[2]
        key = _expected_idempotency_key(capability, normalized, 1) or f"{capability}:{run_id.hex}:{len(client.tracked['account.move'])}"
        first = workflows._call(client, alias, run_id, capability, params, key=key)
        assert not first["idempotent_replay"], first
        value = first["result"]
        if value.get("model") in client.tracked and value.get("id"):
            track(env[value["model"]].browse(value["id"]))
        if replay:
            second = workflows._call(client, alias, run_id, capability, params, key=key)
            assert second["idempotent_replay"] and second["result"] == value, second
        return value

    def denied(capability, params, error, code):
        normalized = validate_core_write_request(capability, core._request(alias, run_id, capability, params))[2]
        key = _expected_idempotency_key(capability, normalized, 1) or f"{capability}:{run_id.hex}:denied"
        response = workflows._call(client, alias, run_id, capability, params, key=key, exit_code=code)
        assert response["error"]["code"] == error, response

    base = fixture("account.account", {"name": marker + "base", "code": "AB" + run_id.hex[:8], "account_type": "asset_current", "company_ids": [Command.set([1])]})
    transition = fixture("account.account", {"name": marker + "transition", "code": "AT" + run_id.hex[:8], "account_type": "liability_current", "reconcile": True, "company_ids": [Command.set([1])]})
    profit = fixture("account.account", {"name": marker + "profit", "code": "AP" + run_id.hex[:8], "account_type": "income", "company_ids": [Command.set([1])]})
    loss = fixture("account.account", {"name": marker + "loss", "code": "AX" + run_id.hex[:8], "account_type": "expense", "company_ids": [Command.set([1])]})
    journal = fixture("account.journal", {"name": marker + "cash-basis", "code": "C" + run_id.hex[:4], "type": "general", "company_id": 1})
    foreign_account = fixture("account.account", {"name": marker + "foreign", "code": "AF" + run_id.hex[:8], "account_type": "liability_current", "reconcile": True, "company_ids": [Command.set([2])]}, company=2)
    foreign_journal = fixture("account.journal", {"name": marker + "foreign-journal", "code": "F" + run_id.hex[:4], "type": "general", "company_id": 2}, company=2)
    changes = {"tax_exigibility": True, "tax_cash_basis_journal_id": journal.id, "account_cash_basis_base_account_id": base.id}
    if not env.user.has_group("base.group_erp_manager"):
        denied("company.cash_basis_configuration.update", {"changes": changes}, "unauthorized", 3)
    for group in _GROUPS:
        if not admin["res.users"].browse(5).has_group(group):
            admin["res.users"].browse(5).write({"group_ids": [Command.link(admin.ref(group).id)]})
    env.invalidate_all()
    assert not env.su and env["res.company"].has_access("write")
    write("company.cash_basis_configuration.update", {"changes": changes}, replay=True)
    settings = read(company_contract.GET_ID, {})
    assert company_contract.valid_read_item(settings, 1) and all(settings[field] == value for field, value in changes.items())
    for field, value in (("account_cash_basis_base_account_id", foreign_account.id), ("tax_cash_basis_journal_id", foreign_journal.id)):
        denied("company.cash_basis_configuration.update", {"changes": {field: value}}, "record_not_found", 4)
    assert all(read(company_contract.GET_ID, {})[field] == value for field, value in changes.items())

    fiscal_country = env.company.account_fiscal_country_id or env.company.country_id
    group = fixture("account.tax.group", {"name": marker + "tax-group", "company_id": 1, "country_id": fiscal_country.id or False})
    children = []
    for index, amount in enumerate((10, 5)):
        value = write("tax.create", {"name": marker + "child" + str(index), "type_tax_use": "sale", "amount_type": "percent", "amount": amount,
            "tax_group_id": group.id, "tax_scope": None, "analytic": bool(index), "tax_exigibility": "on_invoice", "cash_basis_transition_account_id": None}, replay=True)
        children.append(env["account.tax"].browse(value["id"]))
    grouped = env["account.tax"].browse(write("tax.create", {"name": marker + "grouped", "type_tax_use": "sale", "amount_type": "group", "amount": 0,
        "tax_group_id": group.id, "children_tax_ids": [tax.id for tax in reversed(children)], "tax_scope": None, "analytic": False,
        "tax_exigibility": "on_invoice", "cash_basis_transition_account_id": None}, replay=True)["id"])
    assert sorted(grouped.children_tax_ids.ids) == sorted(tax.id for tax in children) and grouped.amount_type == "group"
    write("tax.update", {"tax_id": grouped.id, "changes": {"children_tax_ids": [], "tax_scope": "service", "analytic": True}}, replay=True)
    assert not grouped.children_tax_ids and grouped.tax_scope == "service" and grouped.analytic
    write("tax.update", {"tax_id": grouped.id, "changes": {"children_tax_ids": sorted(tax.id for tax in children), "tax_scope": None, "analytic": False}}, replay=True)
    cash_tax = env["account.tax"].browse(write("tax.create", {"name": marker + "cash-tax", "type_tax_use": "purchase", "amount_type": "percent", "amount": 7,
        "tax_group_id": group.id, "tax_scope": "consu", "analytic": True, "tax_exigibility": "on_payment", "cash_basis_transition_account_id": transition.id}, replay=True)["id"])
    cash_read = read("tax.processing_settings.get", {"tax_id": cash_tax.id})
    assert cash_read["tax_exigibility"] == "on_payment" and cash_read["cash_basis_transition_account_id"] == transition.id and cash_read["analytic"] and cash_read["tax_scope"] == "consu"
    denied("tax.update", {"tax_id": cash_tax.id, "changes": {"cash_basis_transition_account_id": foreign_account.id}}, "record_not_found", 4)
    denied("tax.update", {"tax_id": grouped.id, "changes": {"children_tax_ids": [cash_tax.id]}}, "record_not_found", 4)
    assert sorted(grouped.children_tax_ids.ids) == sorted(tax.id for tax in children)
    write("company.cash_basis_configuration.update", {"changes": {"tax_exigibility": False}}, replay=True)
    assert not env.company.tax_exigibility and cash_tax.tax_exigibility == "on_payment"  # Native UI toggle is not a tax-deletion constraint.
    write("tax.update", {"tax_id": cash_tax.id, "changes": {"tax_exigibility": "on_invoice", "cash_basis_transition_account_id": None, "tax_scope": None, "analytic": False}}, replay=True)
    assert cash_tax.tax_exigibility == "on_invoice" and not cash_tax.cash_basis_transition_account_id
    write("company.cash_basis_configuration.update", {"changes": {"tax_cash_basis_journal_id": None, "account_cash_basis_base_account_id": None}}, replay=True)
    cleared = read(company_contract.GET_ID, {})
    assert not cleared["tax_exigibility"] and cleared["tax_cash_basis_journal_id"] is None and cleared["account_cash_basis_base_account_id"] is None

    def document(capability, tax_ids):
        supplier = capability == "vendor_bill.create"
        value = write(capability, {"partner_id": ids["supplier" if supplier else "customer"], "journal_id": ids["purchase_journal" if supplier else "sale_journal"],
            "date": today, "invoice_date": today, "currency_id": ids["currency"], "lines": [{"name": marker + capability,
                "account_id": ids["expense" if supplier else "income"], "quantity": "1", "price_unit": "101.01", "tax_ids": tax_ids}]})
        return env["account.move"].browse(value["id"])

    invoice, bill = document("customer_invoice.create", [grouped.id]), document("vendor_bill.create", [])
    computed = grouped.compute_all(101.01, currency=invoice.currency_id, quantity=1, partner=invoice.partner_id)
    assert {line.tax_line_id.id for line in invoice.line_ids if line.tax_line_id} == {tax.id for tax in children}
    assert invoice.currency_id.is_zero(invoice.amount_tax - sum(tax["amount"] for tax in computed["taxes"]))
    assert invoice.currency_id.is_zero(invoice.amount_total - computed["total_included"])
    for move in (invoice, bill):
        write("invoice.post", {"move_id": move.id})
        original = move.line_ids.sorted("id").read(financial)
        totals = (move.amount_untaxed, move.amount_tax, move.amount_total, move.date, move.name, move.journal_id.id)
        write("invoice.update", {"move_id": move.id, "changes": {"reference": marker + "posted", "payment_reference": marker + "payment"}}, replay=True)
        assert move.ref == marker + "posted" and move.payment_reference == marker + "payment"
        write("invoice.presentation_settings.update", {"move_id": move.id, "changes": {"narration": "<p>" + marker + " terms</p>", "invoice_user_id": 5}}, replay=True)
        assert marker in move.narration and move.invoice_user_id.id == 5
        denied("invoice.update", {"move_id": move.id, "changes": {"date": today}}, "state_conflict", 5)
        denied("invoice.line.update", {"move_id": move.id, "line_id": move.invoice_line_ids.filtered(lambda line: line.display_type == "product").id, "changes": {"price_unit": "102.01"}}, "state_conflict", 5)
        denied("invoice.presentation_settings.update", {"move_id": move.id, "changes": {"partner_shipping_id": ids["customer"]}}, "state_conflict", 6)
        write("invoice.update", {"move_id": move.id, "changes": {"reference": None, "payment_reference": None}}, replay=True)
        write("invoice.presentation_settings.update", {"move_id": move.id, "changes": {"narration": None, "invoice_user_id": None}}, replay=True)
        assert not move.ref and not move.payment_reference and not move.narration and not move.invoice_user_id
        assert move.line_ids.sorted("id").read(financial) == original
        assert (move.amount_untaxed, move.amount_tax, move.amount_total, move.date, move.name, move.journal_id.id) == totals

    # A real partial reconciliation proves metadata edits also work on settled graphs.
    receivable = invoice.line_ids.filtered(lambda line: line.account_id.account_type == "asset_receivable")
    assert len(receivable) == 1
    counterpart = env["account.move"].browse(write("journal_entry.create", {"journal_id": ids["general_journal"], "date": today, "reference": marker + "partial-offset",
        "lines": [{"name": marker + "partial-expense", "account_id": ids["expense"], "partner_id": None, "debit": "1", "credit": "0"},
                  {"name": marker + "partial-receivable", "account_id": receivable.account_id.id, "partner_id": invoice.partner_id.id, "debit": "0", "credit": "1", "date_maturity": today}]})["id"])
    write("journal_entry.post", {"move_id": counterpart.id})
    offset = counterpart.line_ids.filtered(lambda line: line.account_id == receivable.account_id)
    write("reconciliation.apply", {"line_ids": sorted([receivable.id, offset.id])})
    partials = receivable.matched_debit_ids | receivable.matched_credit_ids
    assert len(partials) == 1 and not receivable.full_reconcile_id
    assert invoice.currency_id.is_zero(invoice.amount_residual - invoice.amount_total + 1)
    partial_fields = ["id", "debit_move_id", "credit_move_id", "amount", "debit_amount_currency", "credit_amount_currency", "max_date", "exchange_move_id", "full_reconcile_id"]
    # Native reference edits may change AR labels; graph identity is the ID, not its display name.
    graph = partials.read(partial_fields, load=None)
    source_financial = invoice.line_ids.sorted("id").read(financial)
    offset_financial = counterpart.line_ids.sorted("id").read(financial)
    write("invoice.update", {"move_id": invoice.id, "changes": {"reference": marker + "partial-reference", "payment_reference": marker + "partial-payment"}}, replay=True)
    write("invoice.presentation_settings.update", {"move_id": invoice.id, "changes": {"narration": "<p>" + marker + " partial terms</p>", "invoice_user_id": 5}}, replay=True)
    assert invoice.line_ids.sorted("id").read(financial) == source_financial and counterpart.line_ids.sorted("id").read(financial) == offset_financial
    after_graph = partials.exists().read(partial_fields, load=None)
    assert after_graph == graph and not receivable.full_reconcile_id, {"before": graph, "after": after_graph, "full_reconcile_id": receivable.full_reconcile_id.id}

    entry = env["account.move"].browse(write("journal_entry.create", {"journal_id": ids["general_journal"], "date": today, "reference": marker + "entry",
        "lines": [{"name": marker + "debit", "account_id": ids["expense"], "partner_id": None, "debit": "20", "credit": "0"},
                  {"name": marker + "credit", "account_id": ids["income"], "partner_id": None, "debit": "0", "credit": "20"}]})["id"])
    write("journal_entry.post", {"move_id": entry.id})
    original = entry.line_ids.sorted("id").read(financial)
    write("journal_entry.update", {"move_id": entry.id, "changes": {"reference": marker + "corrected"}}, replay=True)
    assert entry.ref == marker + "corrected" and entry.state == "posted"
    denied("journal_entry.update", {"move_id": entry.id, "changes": {"journal_id": journal.id}}, "state_conflict", 5)
    write("journal_entry.update", {"move_id": entry.id, "changes": {"reference": None}}, replay=True)
    assert not entry.ref and entry.line_ids.sorted("id").read(financial) == original

    rounding = env["account.cash.rounding"].browse(write("cash_rounding.create", {"name": marker + "rounding", "rounding": "0.05", "strategy": "add_invoice_line",
        "rounding_method": "HALF-UP", "profit_account_id": profit.id, "loss_account_id": loss.id}, replay=True)["id"])
    rule_snapshot = rounding.read(["name", "rounding", "strategy", "rounding_method", "profit_account_id", "loss_account_id"])
    for amount in ("23.91", "-23.91", "0", "23.925", "-23.925"):
        params = {"cash_rounding_id": rounding.id, "currency_id": ids["currency"], "amount": amount}
        item = read("cash_rounding.compute", params)
        currency = env["res.currency"].browse(ids["currency"])
        base_amount = currency.round(float(Decimal(amount)))
        difference = rounding.compute_difference(currency, float(Decimal(amount)))
        expected = {"amount": Decimal(amount), "base_amount": Decimal(str(base_amount)), "difference": Decimal(str(difference)), "rounded_amount": Decimal(str(currency.round(base_amount + difference)))}
        assert item["id"] == rounding.id and item["company_id"] == 1 and item["currency_id"] == currency.id
        assert all(Decimal(item[field]) == value for field, value in expected.items()), (item, expected)
    missing = read("cash_rounding.compute", {"cash_rounding_id": max(admin["account.cash.rounding"].search([]).ids) + 100000, "currency_id": ids["currency"], "amount": "0"}, exit_code=4)
    assert missing["error"]["code"] == "record_not_found"
    assert rounding.read(["name", "rounding", "strategy", "rounding_method", "profit_account_id", "loss_account_id"]) == rule_snapshot
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
    cursor, marker = registry.cursor(), f"ODACV4-SETUP-{args.alias}-{args.run_id.hex}"
    tracked, groups, direct_groups, company_fields, settings, defaults, currencies, failure = {}, None, {}, [], None, None, None, None
    try:
        context = {"allowed_company_ids": [1], "lang": "en_US", "tz": "Asia/Shanghai", "tracking_disable": True, "mail_create_nosubscribe": True, "mail_notrack": True}
        admin = api.Environment(cursor, SUPERUSER_ID, context)
        user = admin["res.users"].browse(5).exists()
        assert user.active and user.login == lifecycle._USER_LOGIN and user.has_group("account.group_account_user")
        groups = sorted(user.group_ids.ids)
        direct_groups = {admin.ref(name).id: shared._direct_group(cursor, admin.ref(name).id) for name in _GROUPS}
        company_fields = sorted(name for name, field in admin["res.company"]._fields.items() if field.store and field.type not in {"binary", "one2many", "many2many"})
        settings, defaults, currencies = company_batch._company_snapshot(admin, company_fields), preparation._defaults(admin), workflows._currency_snapshot(admin)
        client = workflows._Client(api.Environment(cursor, 5, context))
        client.tracked = {model: set() for model in _MODELS}
        tracked = client.tracked
        _exercise(admin, client, args.alias, args.run_id, marker)
        assert company_batch._company_snapshot(admin, company_fields)[1] == settings[1]
        core._collect_related(admin, tracked)
    except BaseException as exc:  # noqa: BLE001 - audit rollback even after an assertion or native failure.
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
            for model in ("account.account", "account.journal", "account.tax", "account.tax.group", "account.cash.rounding"):
                assert not verify[model].with_context(active_test=False).search_count([("name", "ilike", marker)])
            assert not verify["account.move.line"].search_count([("name", "ilike", marker)])
            if groups is not None:
                assert sorted(verify["res.users"].browse(5).group_ids.ids) == groups
                assert all(shared._direct_group(verify_cursor, group_id) == members for group_id, members in direct_groups.items())
                assert company_batch._company_snapshot(verify, company_fields) == settings and preparation._defaults(verify) == defaults and workflows._currency_snapshot(verify) == currencies
        finally:
            verify_cursor.rollback()
    if failure is not None:
        raise failure
    print(json.dumps(_summary(args.alias, args.database), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_live_worker())
