"""One public CLI/native ORM line-processing workflow, fully rolled back per alias."""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import sysconfig
import uuid
from decimal import Decimal
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

_ALLOW_ENV = "ODACV4_ALLOW_JOURNAL_ITEM_PROCESSING_SMOKE"
_GROUPS = ("analytic.group_analytic_accounting",)
_WRITES = {"journal_item.date_maturity.update", "journal_item.analytic_distribution.replace",
           "invoice.line.unit.assign", "invoice.line.deductibility.update", "journal_entry.lines.update"}
_READS = {"journal_item.processing_details.get", "journal_item.reconciliation.inspect", "journal_item.analytic_lines.list"}
_SETUP = {"journal_entry.create", "journal_entry.post", "customer_invoice.create", "vendor_bill.create", "invoice.post", "reconciliation.apply"}
_PROFILE = {"product.accounting_profile.get"}
_MODELS = ("account.move", "account.move.line", "account.journal", "mail.alias", "account.analytic.account", "account.analytic.line", "account.partial.reconcile",
           "account.full.reconcile", "product.product", "product.template", "product.category", "uom.uom")


def _root():
    return Path(__file__).resolve().parents[2]


def _summary(alias, database):
    return {"alias": alias, "database": database, "company_id": 1, "user_id": 5, "business_su": False,
            "capabilities": sorted(_WRITES | _READS | _SETUP | _PROFILE), "immediate_replays": 9,
            "draft_atomic_balanced_update_preserves_existing_line_ids_verified": True,
            "native_unbalanced_write_rolls_back_verified": True,
            "posted_maturity_and_full_analytic_replacement_preserve_financial_values_verified": True,
            "posted_analytic_child_sync_and_replay_no_recreation_verified": True,
            "target_partial_full_reconciliation_and_analytic_pagination_verified": True,
            "native_invoice_unit_price_and_tax_recomputation_verified": True,
            "draft_vendor_deductibility_fifty_zero_hundred_and_native_sync_verified": True,
            "ordinary_accountant_product_accounting_profile_positive_read_verified": True,
            "foreign_missing_parent_line_mismatch_and_posted_invoice_denials_verified": True,
            "analytic_plans_unchanged": True, "rollback_verified": True,
            "all_user_groups_and_temporary_direct_memberships_rolled_back": True,
            "execution": "in_process_cli_real_orm"}


class _Client(shared._Client):
    def invoke(self, action, payload):
        # Production uses one rolled-back write transaction on native failure.
        # This shared outer transaction needs the same atomicity per invocation.
        try:
            with self.env.cr.savepoint():
                return super().invoke(action, payload)
        finally:
            for record_ids in self.tracked.values():
                record_ids.discard(None)


if pytest is not None:
    @pytest.mark.integration
    def test_journal_item_processing_rolls_back_per_alias():
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
            completed = subprocess.run(command, cwd=_root(), env=environment, text=True, capture_output=True,
                                       check=False, timeout=max(timeout, 900))
            assert completed.returncode == 0, completed.stdout + completed.stderr
            assert json.loads(completed.stdout) == _summary(alias, lifecycle._DATABASES[alias])
            print(completed.stdout.strip(), flush=True)


def _read(client, alias, run_id, capability, parameters, *, exit_code=0):
    from odoo_accounting_cli_v4 import cli
    from odoo_accounting_cli_v4.bridge.core_object_reads import OdooCoreObjectReadPort
    from odoo_accounting_cli_v4.bridge.product_accounting_profile import (
        OdooProductAccountingProfilePort,
    )

    port = OdooProductAccountingProfilePort if capability in _PROFILE else OdooCoreObjectReadPort
    stdout, stderr = io.StringIO(), io.StringIO()
    client.last_runtime_failure = None
    code = cli.main(["read", capability, "--request", "-"],
                    stdin=io.StringIO(json.dumps(core._request(alias, run_id, capability, parameters))),
                    stdout=stdout, stderr=stderr, port_factory=lambda *args: port(client))
    response = json.loads(stdout.getvalue())
    assert code == exit_code and not stderr.getvalue(), response
    assert client.env.uid == 5 and not client.env.su and client.env.company.id == 1
    if not exit_code:
        assert response["success"] and response["status"] == "verified"
        assert response["odoo"]["user_id"] == 5 and response["odoo"]["company_id"] == 1
        client.capabilities.add(capability)
        return response["data"]
    assert response["error"]["code"] == "record_not_found", response
    if client.last_runtime_failure is not None:
        assert all(response["odoo"][name] is None for name in ("database", "company_id", "user_id", "model"))


def _denied(client, alias, run_id, capability, parameters, expected_code, exit_code):
    from odoo_accounting_cli_v4 import cli
    from odoo_accounting_cli_v4.bridge.core_writes import OdooCoreWritePort
    from odoo_accounting_cli_v4.capabilities.core_writes import (
        _expected_idempotency_key,
        validate_core_write_request,
    )

    req = core._request(alias, run_id, capability, parameters)
    params = validate_core_write_request(capability, req)[2]
    key = _expected_idempotency_key(capability, params, 1)
    assert key is not None
    stdout, stderr = io.StringIO(), io.StringIO()
    client.last_runtime_failure = None
    code = cli.main(["write", "run", capability, "--request", "-", "--confirm", capability, "--idempotency-key", key],
                    stdin=io.StringIO(json.dumps(req)), stdout=stdout, stderr=stderr, port_factory=lambda *args: OdooCoreWritePort(client))
    response = json.loads(stdout.getvalue())
    assert code == exit_code and not stderr.getvalue() and not response["success"], response
    assert response["error"]["code"] == expected_code, response
    assert client.env.uid == 5 and not client.env.su and client.env.company.id == 1
    if client.last_runtime_failure is not None:
        assert client.last_runtime_failure.code == expected_code
        assert all(response["odoo"][name] is None for name in ("database", "company_id", "user_id", "model"))


def _exercise(admin, client, alias, run_id, marker, product):
    from odoo_accounting_cli_v4 import journal_item_processing_contracts as contracts
    from odoo_accounting_cli_v4.capabilities.core_writes import (
        _expected_idempotency_key,
        validate_core_write_request,
    )

    env = client.env
    ids = lifecycle._fixture_ids(admin, alias)
    # Native non-deductible base synchronization needs a journal expense account.
    # The existing journals stay untouched; this prerequisite is transaction-local.
    purchase_journal = admin["account.journal"].create({"name": marker + "purchase-journal", "code": "L" + run_id.hex[:4],
                                                      "type": "purchase", "company_id": 1, "default_account_id": ids["expense"]})
    client.tracked["account.journal"].add(purchase_journal.id)
    client.tracked["mail.alias"].update(purchase_journal.alias_id.ids)
    ids["purchase_journal"] = purchase_journal.id
    plan, _ = env["account.analytic.plan"]._get_all_plans()
    assert plan and plan._column_name() == "account_id"
    replays = 0

    def track(record):
        client.tracked[record._name].update(record.ids)
        if record._name == "account.move":
            client.tracked["account.move.line"].update(record.line_ids.ids)
            client.tracked["account.analytic.line"].update(record.line_ids.analytic_line_ids.ids)
        return record

    def write(capability, parameters, *, replay=True):
        nonlocal replays
        normalized = validate_core_write_request(capability, core._request(alias, run_id, capability, parameters))[2]
        key = _expected_idempotency_key(capability, normalized, 1) or f"{capability}:{run_id.hex}:{lifecycle._canonical_digest(normalized)[:32]}"
        client.last_runtime_failure = None
        try:
            first = core._cli(client, alias, run_id, capability, parameters, key=key)
            assert first["idempotent_replay"] is False
            value = first["result"]
            if value["model"] == "account.move":
                track(env["account.move"].browse(value["id"]))
            client.tracked["account.partial.reconcile"].update(value["partial_reconcile_ids"])
            if value["full_reconcile_id"]:
                client.tracked["account.full.reconcile"].add(value["full_reconcile_id"])
            analytic_ids = env["account.move.line"].browse(parameters.get("line_id", [])).analytic_line_ids.ids
            if replay:
                second = core._cli(client, alias, run_id, capability, parameters, key=key)
                assert second["idempotent_replay"] is True and second["result"] == value
                assert env["account.move.line"].browse(parameters.get("line_id", [])).analytic_line_ids.ids == analytic_ids
                replays += 1
        except AssertionError:
            if client.last_runtime_failure is not None:
                raise client.last_runtime_failure
            raise
        return value

    def read(capability, parameters):
        return _read(client, alias, run_id, capability, parameters)

    def details(line):
        item = read(contracts.DETAIL_ID, {"journal_item_id": line.id})
        assert contracts.valid_read_item(contracts.DETAIL_ID, item, 1)
        assert item["id"] == line.id and item["move_id"] == line.move_id.id
        assert item["date_maturity"] == (line.date_maturity.isoformat() if line.date_maturity else None)
        assert Decimal(item["deductible_amount"]) == Decimal(str(line.deductible_amount))
        return item

    def document(capability, amount, *, product_id=None, tax_ids=None):
        vendor = capability == "vendor_bill.create"
        params = {"partner_id": ids["supplier" if vendor else "customer"], "journal_id": ids["purchase_journal" if vendor else "sale_journal"],
                  "date": "2026-10-02", "invoice_date": "2026-10-02", "currency_id": ids["currency"],
                  "lines": [{"name": marker + capability, "account_id": ids["expense" if vendor else "income"],
                             "quantity": "1", "price_unit": amount, "tax_ids": tax_ids or []}]}
        if product_id is not None:
            params["lines"][0]["product_id"] = product_id
        return env["account.move"].browse(write(capability, params, replay=False)["id"])

    # Balanced changes are applied to existing rows in one parent write, not clear/recreate.
    entry = env["account.move"].browse(write("journal_entry.create", {"journal_id": ids["general_journal"], "date": "2026-10-02", "reference": marker,
        "lines": [{"name": marker + "debit", "account_id": ids["expense"], "debit": "20", "credit": "0", "partner_id": None},
                  {"name": marker + "credit", "account_id": ids["income"], "debit": "0", "credit": "20", "partner_id": None}]}, replay=False)["id"])
    original_ids = sorted(entry.line_ids.ids)
    debit, credit = entry.line_ids.filtered(lambda line: line.debit), entry.line_ids.filtered(lambda line: line.credit)
    updates = sorted([{"line_id": debit.id, "changes": {"name": marker + "updated", "debit": "40"}},
                      {"line_id": credit.id, "changes": {"credit": "40"}}], key=lambda item: item["line_id"])
    write("journal_entry.lines.update", {"move_id": entry.id, "lines": updates})
    assert sorted(entry.line_ids.ids) == original_ids and debit.debit == credit.credit == 40
    before = entry.line_ids.read(["id", "name", "debit", "credit", "balance", "amount_currency", "account_id"])
    _denied(client, alias, run_id, "journal_entry.lines.update", {"move_id": entry.id, "lines": [{"line_id": debit.id, "changes": {"debit": "41"}}]}, "business_rule_error", 6)
    assert entry.line_ids.read(["id", "name", "debit", "credit", "balance", "amount_currency", "account_id"]) == before

    # Posted metadata writes retain monetary, reconciliation and identity fields.
    invoice = document("customer_invoice.create", "120")
    write("invoice.post", {"move_id": invoice.id}, replay=False)
    term = invoice.line_ids.filtered(lambda line: line.account_id.account_type == "asset_receivable")
    revenue = invoice.invoice_line_ids
    assert len(term) == len(revenue) == 1
    financial_fields = ["id", "account_id", "journal_id", "balance", "amount_currency", "amount_residual", "amount_residual_currency", "tax_ids",
                        "matched_debit_ids", "matched_credit_ids", "full_reconcile_id"]
    financial_before = invoice.line_ids.read(financial_fields)
    posted_before = (invoice.name, invoice.state, invoice.date, invoice.amount_total)
    write("journal_item.date_maturity.update", {"move_id": invoice.id, "line_id": term.id, "date_maturity": "2026-11-15"})
    assert details(term)["date_maturity"] == "2026-11-15"
    accounts = [track(admin["account.analytic.account"].create({"name": marker + suffix, "plan_id": plan.id, "company_id": 1})) for suffix in ("project-a", "project-b")]
    distribution = {str(account.id): "50" for account in accounts}
    write("journal_item.analytic_distribution.replace", {"move_id": invoice.id, "line_id": revenue.id, "analytic_distribution": distribution})
    assert revenue.analytic_distribution == {key: 50.0 for key in distribution}
    assert revenue.balance == -120
    assert len(revenue.analytic_line_ids) == 2 and sum(revenue.analytic_line_ids.mapped("amount")) == -revenue.balance, (
        revenue.balance, revenue.analytic_line_ids.mapped("amount"),
    )
    page = read(contracts.ANALYTIC_LIST_ID, {"journal_item_id": revenue.id, "limit": 1, "cursor": None})
    assert len(page["items"]) == 1 and page["has_more"] and page["next_cursor"]
    second = read(contracts.ANALYTIC_LIST_ID, {"journal_item_id": revenue.id, "limit": 1, "cursor": page["next_cursor"]})
    assert len(second["items"]) == 1 and not second["has_more"] and second["next_cursor"] is None
    assert {item["id"] for item in page["items"] + second["items"]} == set(revenue.analytic_line_ids.ids)
    assert all(item["journal_item_id"] == revenue.id for item in page["items"] + second["items"])
    write("journal_item.analytic_distribution.replace", {"move_id": invoice.id, "line_id": revenue.id, "analytic_distribution": {str(accounts[0].id): "100"}})
    assert revenue.analytic_distribution == {str(accounts[0].id): 100.0} and len(revenue.analytic_line_ids) == 1
    write("journal_item.analytic_distribution.replace", {"move_id": invoice.id, "line_id": revenue.id, "analytic_distribution": None})
    assert not revenue.analytic_distribution and not revenue.analytic_line_ids
    assert invoice.line_ids.read(financial_fields) == financial_before
    assert (invoice.name, invoice.state, invoice.date, invoice.amount_total) == posted_before

    # A target inspection reports only this line's actual partial/full links.
    inspection = read(contracts.RECONCILIATION_ID, {"journal_item_id": term.id})
    assert inspection["partial_reconcile_ids"] == [] and inspection["full_reconcile_id"] is None and inspection["reconciled_journal_item_ids"] == []
    counterparts = []
    for amount in ("40", "80"):
        counterpart = env["account.move"].browse(write("journal_entry.create", {"journal_id": ids["general_journal"], "date": "2026-10-02", "reference": marker + amount,
            "lines": [{"name": marker + "settlement", "account_id": term.account_id.id, "partner_id": ids["customer"], "debit": "0", "credit": amount},
                      {"name": marker + "offset", "account_id": ids["expense"], "partner_id": None, "debit": amount, "credit": "0"}]}, replay=False)["id"])
        write("journal_entry.post", {"move_id": counterpart.id}, replay=False)
        counterpart_line = counterpart.line_ids.filtered(lambda line: line.account_id == term.account_id)
        counterparts.append(counterpart_line.id)
        write("reconciliation.apply", {"invoice_id": invoice.id, "outstanding_line_id": counterpart_line.id}, replay=False)
        inspection = read(contracts.RECONCILIATION_ID, {"journal_item_id": term.id})
        assert contracts.valid_read_item(contracts.RECONCILIATION_ID, inspection, 1)
        assert inspection["partial_reconcile_ids"] == sorted((term.matched_debit_ids | term.matched_credit_ids).ids)
        assert inspection["reconciled_journal_item_ids"] == sorted(counterparts)
        assert inspection["full_reconcile_id"] == (term.full_reconcile_id.id or None)
        assert inspection["reconciled"] is (amount == "80")
    assert len(inspection["partial_reconcile_ids"]) == 2 and inspection["full_reconcile_id"]

    # Odoo19 alternate unit assignment invokes native price/tax recomputation.
    bill = document("vendor_bill.create", "7", product_id=product.id)
    bill_line = bill.invoice_line_ids
    assert len(bill_line) == 1 and bill_line.product_uom_id == product.uom_id
    alternate = product.uom_ids
    assert len(alternate) == 1 and alternate in bill_line.allowed_uom_ids
    write("invoice.line.unit.assign", {"move_id": bill.id, "line_id": bill_line.id, "product_uom_id": alternate.id})
    assert bill_line.product_uom_id == alternate and bill_line.price_unit == 72
    assert bill_line.tax_ids == product.supplier_taxes_id
    assert details(bill_line)["product_uom_id"] == alternate.id
    full_total, full_tax = bill.amount_total, bill.amount_tax
    for amount in ("50", "0", "100"):
        write("invoice.line.deductibility.update", {"move_id": bill.id, "line_id": bill_line.id, "deductible_amount": amount})
        assert details(bill_line)["deductible_amount"] == amount
        assert bill.amount_total == full_total and bill.amount_tax == full_tax
        nondeductible = bill.line_ids.filtered(lambda line: line.display_type == "non_deductible_product")
        assert bool(nondeductible) is (amount != "100")
        track(bill)
    write("invoice.post", {"move_id": bill.id}, replay=False)
    bill_before = bill.line_ids.read(financial_fields + ["deductible_amount", "product_uom_id", "price_unit"])
    _denied(client, alias, run_id, "invoice.line.unit.assign", {"move_id": bill.id, "line_id": bill_line.id, "product_uom_id": product.uom_id.id}, "state_conflict", 5)
    _denied(client, alias, run_id, "invoice.line.deductibility.update", {"move_id": bill.id, "line_id": bill_line.id, "deductible_amount": "50"}, "state_conflict", 5)
    assert bill.line_ids.read(financial_fields + ["deductible_amount", "product_uom_id", "price_unit"]) == bill_before
    _denied(client, alias, run_id, "invoice.line.deductibility.update", {"move_id": invoice.id, "line_id": revenue.id, "deductible_amount": "50"}, "state_conflict", 5)
    draft_sale = document("customer_invoice.create", "19")
    sale_before = draft_sale.line_ids.read(financial_fields + ["deductible_amount"])
    _denied(client, alias, run_id, "invoice.line.deductibility.update", {"move_id": draft_sale.id, "line_id": draft_sale.invoice_line_ids.id, "deductible_amount": "50"}, "business_rule_error", 6)
    assert draft_sale.line_ids.read(financial_fields + ["deductible_amount"]) == sale_before

    foreign = track(admin["account.move"].with_company(admin["res.company"].browse(2)).create({"move_type": "entry", "ref": marker + "foreign", "company_id": 2}))
    for parameters in ({"move_id": 2147483647, "line_id": term.id, "date_maturity": "2026-12-01"},
                       {"move_id": foreign.id, "line_id": term.id, "date_maturity": "2026-12-01"},
                       {"move_id": entry.id, "line_id": term.id, "date_maturity": "2026-12-01"},
                       {"move_id": invoice.id, "line_id": 2147483647, "date_maturity": "2026-12-01"}):
        _denied(client, alias, run_id, "journal_item.date_maturity.update", parameters, "record_not_found", 4)
    for capability in _READS:
        parameters = {"journal_item_id": 2147483647}
        if capability == contracts.ANALYTIC_LIST_ID:
            parameters.update(limit=1, cursor=None)
        _read(client, alias, run_id, capability, parameters, exit_code=4)
    assert replays == 9 and client.capabilities == _WRITES | _READS | _SETUP | _PROFILE


def _live_worker():
    args = lifecycle._arguments(None)
    assert not (args.refund_only or args.payment_difference_only or args.analytic_readback_only)
    sys.path.insert(0, str(args.odoo_source.resolve(strict=True)))
    sys.path.insert(0, str(_root() / "src"))
    from odoo import SUPERUSER_ID, Command, api
    from odoo.orm.registry import Registry
    from odoo.tools import config

    from odoo_accounting_cli_v4 import cli

    config.parse_config(["--config", str(args.odoo_config.resolve(strict=True)), "--database", args.database, "--no-http", "--logfile=/dev/null"])
    registry = Registry(args.database)
    actual_registry = cli.load_registry()
    cli.load_registry = lambda: actual_registry
    cursor = registry.cursor()
    marker = f"ODACV4-JITEM-{args.alias}-{args.run_id.hex}"
    tracked, groups, direct, plans, failure = {}, None, {}, None, None
    try:
        context = {"allowed_company_ids": [1], "lang": "en_US", "tz": "Asia/Shanghai", "tracking_disable": True,
                   "mail_create_nosubscribe": True, "mail_notrack": True}
        admin = api.Environment(cursor, SUPERUSER_ID, context)
        user = admin["res.users"].browse(5).exists()
        assert user.active and user.login == lifecycle._USER_LOGIN and 1 in user.company_ids.ids
        assert user.has_group("account.group_account_user")
        groups = sorted(user.group_ids.ids)
        plans = admin["account.analytic.plan"].search([]).read(["id", "name", "parent_id"])
        env = api.Environment(cursor, 5, context)
        client = _Client(env)
        client.tracked = {model: set() for model in _MODELS}
        tracked = client.tracked
        base = admin.ref("uom.product_uom_unit")
        alternate = admin["uom.uom"].create({"name": marker + "pack-six", "relative_uom_id": base.id, "relative_factor": 6})
        tracked["uom.uom"].add(alternate.id)
        category = admin["product.category"].create({"name": marker + "category", "property_account_income_categ_id": lifecycle._fixture_ids(admin, args.alias)["income"],
                                                    "property_account_expense_categ_id": lifecycle._fixture_ids(admin, args.alias)["expense"]})
        tracked["product.category"].add(category.id)
        tax = admin["account.tax"].search([("company_id", "=", 1), ("type_tax_use", "=", "purchase"), ("amount", ">", 0)], order="id", limit=1)
        assert tax
        product = admin["product.product"].create({"name": marker + "product", "type": "consu", "company_id": 1, "categ_id": category.id,
            "uom_id": base.id, "uom_ids": [Command.set(alternate.ids)], "standard_price": 12, "list_price": 18, "supplier_taxes_id": [Command.set(tax.ids)]})
        tracked["product.product"].add(product.id)
        tracked["product.template"].add(product.product_tmpl_id.id)
        # Positive read is exercised before adding any temporary analytic permissions.
        profile = _read(client, args.alias, args.run_id, "product.accounting_profile.get", {"product_id": product.id})
        assert profile["product"]["id"] == product.id and client.env.uid == 5 and not client.env.su
        for name in _GROUPS:
            group_id = admin.ref(name).id
            direct[group_id] = shared._direct_group(cursor, group_id)
            if not user.has_group(name):
                user.write({"group_ids": [Command.link(group_id)]})
        client.env = api.Environment(cursor, 5, context)
        assert not client.env.su and all(client.env.user.has_group(name) for name in _GROUPS)
        _exercise(admin, client, args.alias, args.run_id, marker, client.env["product.product"].browse(product.id))
        assert admin["account.analytic.plan"].search([]).read(["id", "name", "parent_id"]) == plans
    except BaseException as exc:  # noqa: BLE001 - all native fixture writes roll back on failure too.
        failure = exc
    finally:
        cursor.rollback()
        cursor.close()
    with registry.cursor() as verify_cursor:
        try:
            verify = api.Environment(verify_cursor, SUPERUSER_ID, {"allowed_company_ids": [1, 2], "lang": "en_US"})
            for model, ids in tracked.items():
                assert not verify[model].with_context(active_test=False).search_count([("id", "in", sorted(ids))])
            for model in ("account.analytic.account", "account.analytic.line", "product.template", "product.category", "uom.uom"):
                assert not verify[model].with_context(active_test=False).search_count([("name", "ilike", marker)])
            assert not verify["account.move"].search_count([("ref", "ilike", marker)])
            assert not verify["account.move.line"].search_count([("name", "ilike", marker)])
            if groups is not None:
                assert sorted(verify["res.users"].browse(5).group_ids.ids) == groups
            for group_id, baseline in direct.items():
                assert shared._direct_group(verify_cursor, group_id) == baseline
            if plans is not None:
                assert verify["account.analytic.plan"].search([]).read(["id", "name", "parent_id"]) == plans
        finally:
            verify_cursor.rollback()
    if failure is not None:
        raise failure
    print(json.dumps(_summary(args.alias, args.database), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_live_worker())
