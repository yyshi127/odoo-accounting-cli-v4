"""One dual-isolated ordinary-user order-accounting read smoke; fresh rollback."""

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

_ALLOW_ENV = "ODACV4_ALLOW_ORDER_ACCOUNTING_READS_SMOKE"
_TARGETS = {f"{kind}.order.{operation}" for kind in ("sale", "purchase")
            for operation in ("search", "get", "line.search", "line.get", "analysis.summary")}
_MODELS = tuple(dict.fromkeys((*settlement._MODELS, "res.partner", "product.category", "product.template", "product.product",
                              "account.fiscal.position", "sale.order", "sale.order.line", "purchase.order", "purchase.order.line",
                              "sale.advance.payment.inv", "stock.picking.type", "ir.sequence", "mail.message", "mail.followers")))


def _root():
    return Path(__file__).resolve().parents[2]


def _summary(alias, database):
    return {"alias": alias, "database": database, "company_id": 1, "user_id": 5, "business_su": False,
            "target_capabilities": sorted(_TARGETS), "execution": "in_process_cli_real_orm",
            "header_accounting_inputs_native_user_term_fiscal_and_summary_status_filters_verified": True,
            "draft_invoiced_quantity_distinct_from_native_posted_quantity_and_amounts_verified": True,
            "native_policy_downpayment_and_negative_quantity_filters_cursor_and_exclusion_verified": True,
            "exact_line_get_visible_accounting_graph_and_foreign_company_denial_verified": True,
            "fixture_financial_graph_preserved_by_reads_and_no_stock_or_external_send_verified": True,
            "all_fixtures_company_settings_defaults_currency_and_all_user_groups_fresh_rollback_verified": True}


class _Client(core._RuntimeClient):
    def invoke(self, action, payload):
        with self.env.cr.savepoint():
            return super().invoke(action, payload)


if pytest is not None:
    @pytest.mark.integration
    def test_order_accounting_reads_roll_back_per_alias():
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
    from odoo_accounting_cli_v4.bridge.order_documents import OdooOrderDocumentsPort

    env = client.env
    today = fields.Date.context_today(env.user)
    assert env.uid == 5 and not env.su and env.company.id == 1
    assert env.user.has_group("account.group_account_readonly")

    def track(record):
        client.tracked[record._name].update(record.ids)
        if record._name == "account.move":
            client.tracked["account.move.line"].update(record.line_ids.ids)
        if record._name == "account.journal":
            client.tracked["mail.alias"].update(record.alias_id.ids)
            client.tracked["account.payment.method.line"].update((record.inbound_payment_method_line_ids | record.outbound_payment_method_line_ids).ids)
        if record._name == "account.payment.term":
            client.tracked["account.payment.term.line"].update(record.line_ids.ids)
        if record._name == "stock.picking.type":
            client.tracked["ir.sequence"].update(record.sequence_id.ids)
        if record._name == "product.template":
            client.tracked["product.product"].update(record.product_variant_ids.ids)
        if record._name in {"sale.order", "purchase.order"}:
            client.tracked[record.order_line._name].update(record.order_line.ids)
        if "message_ids" in record._fields:
            client.tracked["mail.message"].update(record.message_ids.ids)
            client.tracked["mail.followers"].update(record.message_follower_ids.ids)
        return record

    def fixture(model, values, *, company=1):
        return track(admin[model].with_company(admin["res.company"].browse(company)).create(values))

    def account(label, account_type, reconcile=False):
        return fixture("account.account", {"name": marker + label, "code": "R" + uuid.uuid5(run_id, label).hex[:9],
                       "account_type": account_type, "reconcile": reconcile, "company_ids": [Command.set([1])]})

    def read(capability, parameters, *, exit_code=0, error=None):
        stdout, stderr = io.StringIO(), io.StringIO()
        client.last_runtime_failure = None
        code = cli.main(["read", capability, "--request", "-"],
                        stdin=io.StringIO(json.dumps(core._request(alias, run_id, capability, parameters))),
                        stdout=stdout, stderr=stderr, port_factory=lambda *args: OdooOrderDocumentsPort(client))
        response = json.loads(stdout.getvalue())
        if code != exit_code or stderr.getvalue():
            raise AssertionError(response) from client.last_runtime_failure
        assert env.uid == 5 and not env.su and env.company.id == 1
        if code:
            assert not response["success"] and response["error"]["code"] == error, response
            return response
        assert response["success"] and response["status"] == "verified" and response["odoo"]["user_id"] == 5, response
        client.capabilities.add(capability)
        return response["data"]

    def compare_line(kind, line):
        native = env[f"{kind}.order.line"].browse(line.id)
        value = read(f"{kind}.order.line.get", {"line_id": line.id})
        assert value["id"] == line.id and value["is_downpayment"] == native.is_downpayment
        policy = "invoice_policy" if kind == "sale" else "purchase_method"
        native_policy = getattr(native.product_id, policy) if native.product_id else None
        assert value[policy] == (native_policy or None)
        for public, field in (("invoiced_quantity", "qty_invoiced"), ("to_invoice_quantity", "qty_to_invoice")):
            assert Decimal(value[public]) == Decimal(str(getattr(native, field))), value
        if kind == "sale":
            assert value["invoice_status"] == native.invoice_status
            for public, field in (("posted_invoiced_quantity", "qty_invoiced_posted"), ("amount_invoiced", "amount_invoiced"), ("amount_to_invoice", "amount_to_invoice")):
                assert Decimal(value[public]) == Decimal(str(getattr(native, field))), value
        visible = env["account.move.line"].search([("id", "in", native.invoice_lines.ids), ("company_id", "=", 1)])
        moves = env["account.move"].search([("id", "in", visible.move_id.ids), ("company_id", "=", 1)], order="id")
        assert value["invoice_line_ids"] == sorted(visible.ids)
        assert [invoice["id"] for invoice in value["invoices"]] == moves.ids
        return value

    user = admin["res.users"].browse(5)
    for xmlid in ("sales_team.group_sale_salesman", "purchase.group_purchase_user"):
        if not user.has_group(xmlid):
            user.write({"group_ids": [Command.link(admin.ref(xmlid).id)]})
    income, expense = account("income", "income"), account("expense", "expense")
    receivable, payable = account("receivable", "asset_receivable", True), account("payable", "liability_payable", True)
    admin["res.company"].browse(1).write({"downpayment_account_id": income.id})
    journals = {kind: fixture("account.journal", {"name": marker + kind, "code": kind[0].upper() + run_id.hex[:4],
                "type": kind, "company_id": 1, "default_account_id": income.id if kind == "sale" else expense.id}) for kind in ("sale", "purchase")}
    partners = {kind: fixture("res.partner", {"name": marker + kind + "partner", "company_id": 1,
                "property_account_receivable_id": receivable.id, "property_account_payable_id": payable.id}) for kind in ("sale", "purchase")}
    terms = [fixture("account.payment.term", {"name": marker + "term" + str(i), "company_id": 1, "line_ids": [
                Command.create({"value": "percent", "value_amount": 100, "delay_type": "days_after", "nb_days": i})]}) for i in (0, 1)]
    fiscals = [fixture("account.fiscal.position", {"name": marker + "fiscal" + str(i), "company_id": 1}) for i in (0, 1)]
    category = fixture("product.category", {"name": marker + "category"})
    template = fixture("product.template", {"name": marker + "service", "company_id": False, "type": "service", "categ_id": category.id,
                       "invoice_policy": "delivery", "purchase_method": "receive", "taxes_id": [Command.clear()], "supplier_taxes_id": [Command.clear()],
                       "property_account_income_id": income.id, "property_account_expense_id": expense.id})
    product = template.product_variant_id

    def order(kind, label, *, term=0, fiscal=0, owner=5, downpayment_line=False, service=None):
        item = fixture(f"{kind}.order", {"partner_id": partners[kind].id, "company_id": 1, "user_id": owner,
                       "currency_id": env.company.currency_id.id, "payment_term_id": terms[term].id, "fiscal_position_id": fiscals[fiscal].id,
                       **({"journal_id": journals[kind].id, "client_order_ref": marker + label} if kind == "sale" else {"partner_ref": marker + label}),
                       "order_line": [Command.create({"product_id": (service or product).id, "name": marker + label,
                       "product_uom_qty" if kind == "sale" else "product_qty": 10, "price_unit": 10, "tax_ids": [Command.clear()]})]})
        item.action_confirm() if kind == "sale" else item.button_confirm()
        item.order_line.write({"qty_delivered" if kind == "sale" else "qty_received": 4})
        if downpayment_line:
            fixture("purchase.order.line", {"order_id": item.id, "product_id": product.id, "name": marker + label + "-dp-flag",
                    "product_qty": 10, "qty_received": 4, "price_unit": 10, "tax_ids": [Command.clear()], "is_downpayment": True})
        assert not item.picking_ids and not item.order_line.move_ids
        return track(item)

    orders = {}
    common = {"date_from": (today - timedelta(days=1)).isoformat(), "date_to": (today + timedelta(days=1)).isoformat(),
              "user_id": 5, "payment_term_id": terms[0].id, "fiscal_position_id": fiscals[0].id}
    for kind in ("sale", "purchase"):
        main = orders[kind] = order(kind, "main-" + kind, downpayment_line=kind == "purchase")
        if kind == "sale":
            fixture("sale.order.line", {"order_id": main.id, "product_id": product.id, "name": marker + "main-sale-second",
                    "product_uom_qty": 10, "price_unit": 10, "tax_ids": [Command.clear()]}).write({"qty_delivered": 4})
            track(main)
        decoys = [order(kind, kind + "other-term", term=1), order(kind, kind + "other-fiscal", fiscal=1), order(kind, kind + "other-user", owner=1)]
        filters = {**common, "partner_id": partners[kind].id, "states": ["sale" if kind == "sale" else "purchase"]}
        found = read(f"{kind}.order.search", filters)
        assert [row["id"] for row in found["items"]] == [main.id]
        header = read(f"{kind}.order.get", {"order_id": main.id})
        assert header["payment_term_id"] == terms[0].id and header["fiscal_position_id"] == fiscals[0].id
        assert all(not line["is_downpayment"] or kind == "purchase" for line in header["lines"])
        summary = read(f"{kind}.order.analysis.summary", {**filters, "group_by": "invoice_status", "invoice_statuses": [main.invoice_status]})
        assert sum(row["order_count"] for row in summary["totals_by_currency"]) == 1
        assert Decimal(summary["totals_by_currency"][0]["amount_total"]) == Decimal(str(main.amount_total))
        absent = read(f"{kind}.order.analysis.summary", {**filters, "group_by": "invoice_status", "invoice_statuses": ["invoiced"]})
        assert not absent["groups"] and not absent["totals_by_currency"]
        owned_ids = [main.id, *(item.id for item in decoys)]
        without = read(f"{kind}.order.search", {**filters, "user_id": None, "payment_term_id": None, "fiscal_position_id": None})
        visible = env[f"{kind}.order"].search([("id", "in", owned_ids), ("company_id", "=", 1)], order="id")
        assert [row["id"] for row in without["items"]] == visible.ids
        other_user = read(f"{kind}.order.search", {**filters, "user_id": 1})
        visible_other = env[f"{kind}.order"].search([("id", "in", owned_ids), ("company_id", "=", 1), ("user_id", "=", 1),
                                                   ("payment_term_id", "=", terms[0].id), ("fiscal_position_id", "=", fiscals[0].id)], order="id")
        assert [row["id"] for row in other_user["items"]] == visible_other.ids
        for line in main.order_line:
            compare_line(kind, line)
        native_before = set(main.invoice_ids.ids)
        if kind == "sale":
            invoice = main.with_context(default_journal_id=journals[kind].id)._create_invoices(grouped=True)
        else:
            main.with_context(default_journal_id=journals[kind].id).action_create_invoice()
            invoice = main.invoice_ids.filtered(lambda move, before=native_before: move.id not in before)
        assert len(invoice) == 1 and invoice.state == "draft"
        assert invoice.journal_id.id == journals[kind].id
        product_lines = invoice.invoice_line_ids.filtered(lambda line: line.display_type == "product")
        assert product_lines and all(line.account_id.id in {income.id, expense.id} for line in product_lines)
        track(invoice)
        if kind == "sale":
            for line in main.order_line:
                draft = compare_line(kind, line)
                assert Decimal(draft["invoiced_quantity"]) > Decimal(draft["posted_invoiced_quantity"]) == 0
                assert Decimal(draft["amount_invoiced"]) == 0
        invoice.write({"invoice_date": today})
        invoice.action_post()
        track(invoice)
        track(main)
        for line in main.order_line:
            value = compare_line(kind, line)
            assert value["invoices"][0]["state"] == "posted"
        if kind == "sale":
            assert Decimal(value["posted_invoiced_quantity"]) == Decimal(value["invoiced_quantity"]) > 0
            header = read("sale.order.get", {"order_id": main.id})
            assert Decimal(header["amount_invoiced"]) == Decimal(str(main.amount_invoiced)) > 0
            assert Decimal(header["amount_to_invoice"]) == Decimal(str(main.amount_to_invoice))
        main.order_line.write({"qty_delivered" if kind == "sale" else "qty_received": 2})
        env.invalidate_all()
        assert all(line.qty_to_invoice < 0 for line in main.order_line)

    dp_template = fixture("product.template", {"name": marker + "dp-service", "company_id": False, "type": "service", "categ_id": category.id,
                          "invoice_policy": "order", "purchase_method": "purchase", "taxes_id": [Command.clear()], "supplier_taxes_id": [Command.clear()],
                          "property_account_income_id": income.id, "property_account_expense_id": expense.id})
    dp_order = order("sale", "downpayment", service=dp_template.product_variant_id)
    wizard = fixture("sale.advance.payment.inv", {"sale_order_ids": [Command.set(dp_order.ids)], "advance_payment_method": "percentage", "amount": 10})
    wizard._check_amount_is_positive()
    dp_invoice = track(wizard.with_context(default_journal_id=journals["sale"].id)._create_invoices(dp_order))
    assert dp_invoice.journal_id.id == journals["sale"].id
    product_lines = dp_invoice.invoice_line_ids.filtered(lambda line: line.display_type == "product")
    assert product_lines and all(line.account_id.id in {income.id, expense.id} for line in product_lines)
    dp_invoice.write({"invoice_date": today})
    dp_invoice.action_post()
    track(dp_invoice)
    track(dp_order)
    dp_lines = dp_order.order_line.filtered("is_downpayment")
    assert dp_lines and any(line.invoice_lines & dp_invoice.invoice_line_ids for line in dp_lines)
    for line in dp_lines:
        compare_line("sale", line)
    snapshots = {move.id: maintenance._graph(move) for move in admin["account.move"].browse(sorted(client.tracked["account.move"]))}

    for kind in ("sale", "purchase"):
        capability = f"{kind}.order.line.search"
        base = {"partner_id": partners[kind].id, "states": ["sale" if kind == "sale" else "purchase"], "limit": 1}
        for flag in (None, False, True):
            filters = {**base, **({"negative_to_invoice_only": True} if flag is None else {"is_downpayment": flag})}
            domain = [("company_id", "=", 1), ("order_id.partner_id", "=", partners[kind].id), ("order_id.state", "in", base["states"])]
            domain.append(("qty_to_invoice", "<", 0) if flag is None else ("is_downpayment", "=", flag))
            native = env[f"{kind}.order.line"].search(domain, order="id")
            page = read(capability, filters)
            if flag is None:
                assert len(native) >= 2 and page["has_more"]
                negative_cursor = page["next_cursor"]
            rows = list(page["items"])
            while page["has_more"]:
                page = read(capability, {**filters, "cursor": page["next_cursor"]})
                rows.extend(page["items"])
            assert [row["id"] for row in rows] == native.ids
            assert all(Decimal(row["to_invoice_quantity"]) < 0 if flag is None else row["is_downpayment"] is flag for row in rows)
        read(capability, {**base, "negative_to_invoice_only": True, "to_invoice_only": True}, exit_code=2, error="invalid_request")
        read(capability, {**base, "negative_to_invoice_only": False, "cursor": negative_cursor}, exit_code=2, error="invalid_cursor")
    assert all(maintenance._graph(admin["account.move"].browse(move_id)) == graph for move_id, graph in snapshots.items())
    assert not any(item.picking_ids or item.order_line.move_ids for item in (*orders.values(), dp_order))

    # Foreign fixtures last: all successful ordinary-user reads concern company1.
    foreign_partner = fixture("res.partner", {"name": marker + "foreign-partner", "company_id": 2}, company=2)
    foreign_product = fixture("product.template", {"name": marker + "foreign-service", "company_id": 2, "type": "service", "categ_id": category.id,
                              "taxes_id": [Command.clear()], "supplier_taxes_id": [Command.clear()]}, company=2)
    supplier_location = admin.ref("stock.stock_location_suppliers")
    customer_location = admin.ref("stock.stock_location_customers")
    assert not supplier_location.company_id and not customer_location.company_id
    foreign_receipt_type = fixture("stock.picking.type", {"name": marker + "foreign-receipt", "code": "incoming", "sequence_code": marker,
                                  "company_id": 2, "warehouse_id": False, "default_location_src_id": supplier_location.id,
                                  "default_location_dest_id": customer_location.id}, company=2)
    assert foreign_receipt_type.company_id.id == foreign_receipt_type.sequence_id.company_id.id == 2
    for kind in ("sale", "purchase"):
        foreign = fixture(f"{kind}.order", {"partner_id": foreign_partner.id, "company_id": 2, "user_id": False,
                          **({"picking_type_id": foreign_receipt_type.id} if kind == "purchase" else {}),
                          "order_line": [Command.create({"product_id": foreign_product.product_variant_id.id, "name": marker + "foreign-line",
                          "product_uom_qty" if kind == "sale" else "product_qty": 1, "price_unit": 10, "tax_ids": [Command.clear()]})]}, company=2)
        assert foreign.state == "draft" and not foreign.picking_ids and not foreign.order_line.move_ids
        read(f"{kind}.order.line.get", {"line_id": foreign.order_line.id}, exit_code=4, error="record_not_found")
    assert client.capabilities == _TARGETS


def _live_worker():
    settlement._MODELS, settlement._exercise, settlement._summary = _MODELS, _exercise, _summary
    settlement.maintenance._Client = _Client
    return settlement._live_worker()


if __name__ == "__main__":
    raise SystemExit(_live_worker())
