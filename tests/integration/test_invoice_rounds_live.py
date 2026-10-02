"""One dual-isolated ordinary-user invoice-round smoke; full fresh rollback."""

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

import test_accounting_settlement_batch_live as settlement

maintenance, lifecycle, core = settlement.maintenance, settlement.lifecycle, settlement.core

try:
    import pytest
except ModuleNotFoundError:
    if "--live-worker" not in sys.argv:
        raise
    pytest = None

_ALLOW_ENV = "ODACV4_ALLOW_INVOICE_ROUNDS_SMOKE"
_TARGETS = {"customer_credit_note.create", "vendor_refund.create", "receivable.payment.register", "payable.payment.register",
            "sale.order.invoice.create", "purchase.order.bill.create", "sale.order.down_payment.create",
            "product.accounting_profile.get", "product.accounting_profile.update"}
_WIZARDS = ("account.move.reversal", "account.payment.register", "sale.advance.payment.inv")
_MODELS = tuple(dict.fromkeys((*settlement._MODELS, "res.partner", "product.product", "product.template", "product.category",
                              "sale.order", "sale.order.line", "purchase.order", "purchase.order.line", *_WIZARDS,
                              "product.attribute", "product.attribute.value", "product.template.attribute.line",
                              "product.template.attribute.value", "mail.message", "mail.followers")))


def _root():
    return Path(__file__).resolve().parents[2]


def _summary(alias, database):
    return {"alias": alias, "database": database, "company_id": 1, "user_id": 5, "business_su": False,
            "target_capabilities": sorted(_TARGETS), "execution": "in_process_cli_real_orm",
            "full_batch_refund_sources_replay_and_whole_selection_key_drift_verified": True,
            "native_installment_modes_cutoff_per_term_partial_group_and_refund_directions_verified": True,
            "native_sale_purchase_partial_later_rounds_and_consolidation_verified": True,
            "native_percentage_fixed_downpayment_and_final_deduction_consumer_verified": True,
            "shared_template_policy_variant_reads_native_acl_and_foreign_denial_verified": True,
            "all_fixtures_company_settings_defaults_currency_rates_and_all_user_groups_fresh_rollback_verified": True}


class _Client(core._RuntimeClient):
    def invoke(self, action, payload):
        try:
            with self.env.cr.savepoint():
                page = super().invoke(action, payload)
                for item in (page.get("result") or {}).get("items", []):
                    self.tracked[item["model"]].add(item["id"])
                    self.tracked["account.move.line"].update(item["line_ids"])
                    self.tracked["account.partial.reconcile"].update(item["partial_reconcile_ids"])
                    if item["full_reconcile_id"]:
                        self.tracked["account.full.reconcile"].add(item["full_reconcile_id"])
                core._collect_related(self.env, self.tracked)
                return page
        finally:
            for ids in self.tracked.values():
                ids.discard(None)
            if hasattr(self, "admin"):
                for model, before in self.wizard_before.items():
                    self.tracked[model].update(set(self.admin[model].search([]).ids) - before)


if pytest is not None:
    @pytest.mark.integration
    def test_invoice_rounds_roll_back_per_alias():
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

    from odoo_accounting_cli_v4 import cli
    from odoo_accounting_cli_v4.bridge.product_accounting_profile import (
        OdooProductAccountingProfilePort,
    )
    from odoo_accounting_cli_v4.capabilities.core_writes import (
        _expected_idempotency_key,
        validate_core_write_request,
    )

    env = client.env
    today = fields.Date.context_today(env.user)
    assert env.uid == 5 and not env.su and env.company.id == 1
    client.admin = admin
    client.wizard_before = {model: set(admin[model].search([]).ids) for model in _WIZARDS}

    def track(record):
        client.tracked[record._name].update(record.ids)
        if record._name == "account.journal":
            client.tracked["mail.alias"].update(record.alias_id.ids)
            client.tracked["account.payment.method.line"].update((record.inbound_payment_method_line_ids | record.outbound_payment_method_line_ids).ids)
        if record._name == "account.payment.term":
            client.tracked["account.payment.term.line"].update(record.line_ids.ids)
        if record._name == "product.template":
            client.tracked["product.product"].update(record.product_variant_ids.ids)
            client.tracked["product.template.attribute.line"].update(record.attribute_line_ids.ids)
            client.tracked["product.template.attribute.value"].update(record.attribute_line_ids.product_template_value_ids.ids)
        if record._name in {"sale.order", "purchase.order"}:
            client.tracked[record.order_line._name].update(record.order_line.ids)
        if "message_ids" in record._fields:
            client.tracked["mail.message"].update(record.message_ids.ids)
            client.tracked["mail.followers"].update(record.message_follower_ids.ids)
        return record

    def fixture(model, values, *, company=1):
        return track(admin[model].with_company(admin["res.company"].browse(company)).create(values))

    def account(label, kind, reconcile=False):
        return fixture("account.account", {"name": marker + label, "code": "I" + uuid.uuid5(run_id, label).hex[:9],
                       "account_type": kind, "reconcile": reconcile, "company_ids": [Command.set([1])]})

    def call(capability, parameters, **options):
        if capability != "product.accounting_profile.get":
            return maintenance._call(client, alias, run_id, capability, parameters, **options)
        stdout, stderr = io.StringIO(), io.StringIO()
        code = cli.main(["read", capability, "--request", "-"], stdin=io.StringIO(json.dumps(core._request(alias, run_id, capability, parameters))),
                        stdout=stdout, stderr=stderr, port_factory=lambda *args: OdooProductAccountingProfilePort(client))
        value = json.loads(stdout.getvalue())
        assert code == options.get("exit_code", 0) and not stderr.getvalue(), value
        if code:
            return value
        assert value["success"] and value["odoo"]["user_id"] == 5
        client.capabilities.add(capability)
        return value["data"]

    def key_for(capability, parameters, label):
        normalized = validate_core_write_request(capability, core._request(alias, run_id, capability, parameters))[2]
        return _expected_idempotency_key(capability, normalized, 1) or f"{capability}:{run_id.hex}:{label}"

    def write(capability, parameters, label, replay=True):
        key = key_for(capability, parameters, label)
        first = call(capability, parameters, key=key)
        assert not first["idempotent_replay"], first
        if replay:
            second = call(capability, parameters, key=key)
            assert second["idempotent_replay"] and second["result"] == first["result"], second
        result = first["result"]
        for item in result.get("items", [result]):
            if item["model"] in {"account.move", "account.payment"}:
                track(env[item["model"]].browse(item["id"]))
        return result

    def denied(capability, parameters, label, error, code=5, key=None):
        response = call(capability, parameters, key=key or key_for(capability, parameters, label), exit_code=code)
        assert response["error"]["code"] == error, response

    user = admin["res.users"].browse(5)
    for xmlid in ("sales_team.group_sale_salesman", "purchase.group_purchase_user", "product.group_product_manager"):
        if not user.has_group(xmlid):
            user.write({"group_ids": [Command.link(admin.ref(xmlid).id)]})
    env.invalidate_all()
    income, expense = account("income", "income"), account("expense", "expense")
    receivable, payable = account("receivable", "asset_receivable", True), account("payable", "liability_payable", True)
    liquidity, outstanding, suspense = account("bank", "asset_cash", True), account("outstanding", "asset_current", True), account("suspense", "asset_current", True)
    customer = fixture("res.partner", {"name": marker + "customer", "company_id": 1, "property_account_receivable_id": receivable.id, "property_account_payable_id": payable.id})
    supplier = fixture("res.partner", {"name": marker + "supplier", "company_id": 1, "supplier_rank": 1, "property_account_receivable_id": receivable.id, "property_account_payable_id": payable.id})
    sale = fixture("account.journal", {"name": marker + "sale", "code": "S" + run_id.hex[:4], "type": "sale", "company_id": 1, "default_account_id": income.id})
    purchase = fixture("account.journal", {"name": marker + "purchase", "code": "P" + run_id.hex[:4], "type": "purchase", "company_id": 1, "default_account_id": expense.id})
    bank = fixture("account.journal", {"name": marker + "bank", "code": "B" + run_id.hex[:4], "type": "bank", "company_id": 1,
                   "default_account_id": liquidity.id, "suspense_account_id": suspense.id})
    (bank.inbound_payment_method_line_ids | bank.outbound_payment_method_line_ids).write({"payment_account_id": outstanding.id})
    term = fixture("account.payment.term", {"name": marker + "installments", "company_id": 1, "line_ids": [
        Command.create({"value": "percent", "value_amount": 40, "delay_type": "days_after", "nb_days": 10}),
        Command.create({"value": "percent", "value_amount": 60, "delay_type": "days_after", "nb_days": 30})]})
    env.invalidate_all()

    def document(label, supplier_side=False, amount="100", payment_term=None, date=None):
        day = date or today
        result = write("vendor_bill.create" if supplier_side else "customer_invoice.create", {
            "partner_id": supplier.id if supplier_side else customer.id, "journal_id": purchase.id if supplier_side else sale.id,
            "invoice_date": day.isoformat(), "date": day.isoformat(), "currency_id": env.company.currency_id.id,
            "payment_term_id": payment_term, "reference": marker + label,
            "lines": [{"name": marker + label, "account_id": expense.id if supplier_side else income.id, "quantity": "1", "price_unit": amount, "tax_ids": []}]}, label)
        write("invoice.post", {"move_id": result["id"]}, label + "-post")
        return env["account.move"].browse(result["id"])

    for supplier_side, refund_cap, payment_cap in ((False, "customer_credit_note.create", "receivable.payment.register"),
                                                  (True, "vendor_refund.create", "payable.payment.register")):
        sources = [document(refund_cap + str(i), supplier_side, amount=str(40 + i * 20)) for i in range(4)]
        # Posting a reversal of an unpaid source natively offsets its residual;
        # cash-refund registration therefore needs already-settled sources.
        write(payment_cap, {"move_ids": [move.id for move in sources], "journal_id": bank.id,
                            "payment_date": today.isoformat(), "group_payment": True, "installments_mode": "full"}, refund_cap + "-source-settlement")
        assert all(move.currency_id.is_zero(move.amount_residual) for move in sources)
        original = {move.id: maintenance._graph(move) for move in sources}
        params = {"move_ids": [move.id for move in sources[:2]], "date": today.isoformat(), "reason": marker + "batch-refund"}
        refunds = write(refund_cap, params, refund_cap)["items"]
        assert {row["source_id"] for row in refunds} == set(params["move_ids"])
        assert all(maintenance._graph(move) == original[move.id] for move in sources)
        denied(refund_cap, {**params, "move_ids": [move.id for move in sources[2:]]}, "drift", "idempotency_conflict", key=key_for(refund_cap, params, refund_cap))
        for row in refunds:
            write("invoice.post", {"move_id": row["id"]}, "refund-post")
        paid = write(payment_cap, {"move_ids": [row["id"] for row in refunds], "journal_id": bank.id,
                                  "payment_date": today.isoformat(), "group_payment": True, "installments_mode": "full"}, "refund-payment")
        payment = env["account.payment"].browse(paid["id"])
        assert payment.payment_type == ("inbound" if supplier_side else "outbound") and Decimal(str(payment.amount)) == 100

    for supplier_side, cap in ((False, "receivable.payment.register"), (True, "payable.payment.register")):
        for mode in ("next", "overdue", "before_date", "full"):
            invoice = document(cap + mode, supplier_side, payment_term=term.id, date=today - timedelta(days=20) if mode == "overdue" else today)
            params = {"move_id": invoice.id, "journal_id": bank.id, "payment_date": today.isoformat(), "installments_mode": mode}
            if mode == "before_date":
                params["installment_cutoff_date"] = (today + timedelta(days=15)).isoformat()
            if mode in {"overdue", "full"}:
                params["group_payment"] = False
            result = write(cap, params, cap + mode)
            items = result.get("items", [result])
            assert len(items) == (2 if mode == "full" else 1)
            assert sum(Decimal(str(env["account.payment"].browse(item["id"]).amount)) for item in items) == (100 if mode == "full" else 40)
            assert Decimal(str(invoice.amount_residual)) == (0 if mode == "full" else 60)
            if mode != "full":
                write(cap, {"move_id": invoice.id, "journal_id": bank.id, "payment_date": today.isoformat(), "installments_mode": "full"}, cap + mode + "-finish")
                assert invoice.currency_id.is_zero(invoice.amount_residual)
        sources = [document(cap + "-partial" + str(i), supplier_side, amount=str(80 + i * 40)) for i in range(2)]
        params = {"move_ids": [move.id for move in sources], "journal_id": bank.id, "payment_date": today.isoformat(), "group_payment": True, "amount": "50"}
        result = write(cap, params, cap + "-partial")
        assert Decimal(str(env["account.payment"].browse(result["id"]).amount)) == 50
        assert sum(Decimal(str(move.amount_residual)) for move in sources) == 150

    attribute = fixture("product.attribute", {"name": marker + "variant", "create_variant": "always"})
    values = [fixture("product.attribute.value", {"name": marker + str(i), "attribute_id": attribute.id}) for i in range(2)]
    category = fixture("product.category", {"name": marker + "category"})
    template = fixture("product.template", {"name": marker + "service", "company_id": False, "type": "service", "categ_id": category.id,
                       "invoice_policy": "order", "purchase_method": "purchase", "taxes_id": [Command.clear()], "supplier_taxes_id": [Command.clear()],
                       "property_account_income_id": income.id, "property_account_expense_id": expense.id,
                       "attribute_line_ids": [Command.create({"attribute_id": attribute.id, "value_ids": [Command.set([value.id for value in values])]})]})
    product = template.product_variant_ids[0]
    write("product.accounting_profile.update", {"product_id": product.id, "changes": {"invoice_policy": "delivery", "purchase_method": "receive"}}, "policy")
    for variant in template.product_variant_ids:
        profile = call("product.accounting_profile.get", {"product_id": variant.id})
        assert profile["invoice_policy"] == "delivery" and profile["purchase_method"] == "receive"
        assert profile["product"]["company_id"] is None

    def order(label, purchase_side=False):
        model = "purchase.order" if purchase_side else "sale.order"
        item = fixture(model, {"partner_id": supplier.id if purchase_side else customer.id, "company_id": 1, "user_id": 5,
                       "payment_term_id": False, "order_line": [Command.create({"product_id": product.id, "name": marker + label,
                       "product_qty" if purchase_side else "product_uom_qty": 10, "price_unit": 10,
                       "tax_ids": [Command.clear()]})]})
        item.button_confirm() if purchase_side else item.action_confirm()
        track(item)
        return item

    for purchase_side, cap in ((False, "sale.order.invoice.create"), (True, "purchase.order.bill.create")):
        item = order(cap, purchase_side)
        quantity_field = "qty_received" if purchase_side else "qty_delivered"
        item.order_line.write({quantity_field: 4})
        env.invalidate_all()
        params = {"order_ids": [item.id]}
        first = write(cap, params, cap + "-round1")["items"]
        assert len(first) == 1
        assert Decimal(str(env["account.move"].browse(first[0]["id"]).amount_total)) == 40
        item.order_line.write({quantity_field: 10})
        env.invalidate_all()
        second = write(cap, params, cap + "-round2")["items"]
        assert len(second) == 1 and second[0]["id"] != first[0]["id"]
        assert Decimal(str(env["account.move"].browse(second[0]["id"]).amount_total)) == 60
        denied(cap, params, "empty-round", "state_conflict")
        for source in (item,):
            track(source)

    write("product.accounting_profile.update", {"product_id": product.id, "changes": {"invoice_policy": "order"}}, "policy-order")
    for consolidate in (True, False):
        orders = [order("consolidate" + str(consolidate) + str(i)) for i in range(2)]
        rows = write("sale.order.invoice.create", {"order_ids": [item.id for item in orders], "consolidated_billing": consolidate}, "consolidate" + str(consolidate))["items"]
        assert len(rows) == (1 if consolidate else 2)
        assert sum(Decimal(str(env["account.move"].browse(row["id"]).amount_total)) for row in rows) == 200
        assert (rows[0]["source_id"] is None) is consolidate

    downpayment_order = order("downpayment")
    for method, amount, total in (("percentage", "10", 10), ("fixed", "20", 20)):
        row = write("sale.order.down_payment.create", {"order_id": downpayment_order.id, "method": method, "amount": amount}, "downpayment-" + method)
        assert Decimal(str(env["account.move"].browse(row["id"]).amount_total)) == total
        write("invoice.post", {"move_id": row["id"]}, "downpayment-post-" + method)
        track(downpayment_order)
    row = write("sale.order.invoice.create", {"order_ids": [downpayment_order.id], "deduct_down_payments": True}, "downpayment-final")["items"][0]
    final = env["account.move"].browse(row["id"])
    assert Decimal(str(final.amount_total)) == 70
    assert sum(line.quantity for line in final.invoice_line_ids if line.is_downpayment) == -2
    track(downpayment_order)

    foreign = fixture("product.template", {"name": marker + "foreign", "type": "service", "company_id": 2}, company=2)
    denied("product.accounting_profile.update", {"product_id": foreign.product_variant_id.id, "changes": {"invoice_policy": "order"}}, "foreign-policy", "record_not_found", 4)
    groups = list(user.group_ids.ids)
    user.write({"group_ids": [Command.unlink(admin.ref("product.group_product_manager").id)]})
    env.invalidate_all()
    assert not env.user.has_group("product.group_product_manager")
    before_policy = template.invoice_policy
    denied("product.accounting_profile.update", {"product_id": product.id, "changes": {"invoice_policy": "delivery"}}, "policy-acl", "unauthorized", 3)
    assert template.invoice_policy == before_policy
    user.write({"group_ids": [Command.set(groups)]})
    assert _TARGETS <= client.capabilities


def _live_worker():
    settlement._MODELS, settlement._exercise, settlement._summary = _MODELS, _exercise, _summary
    settlement.maintenance._Client = _Client
    return settlement._live_worker()


if __name__ == "__main__":
    raise SystemExit(_live_worker())
