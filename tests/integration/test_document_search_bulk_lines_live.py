"""One shared CLI/ordinary-user workflow with a fresh full rollback oracle."""
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

core, lifecycle = settlement.core, settlement.lifecycle

try:
    import pytest
except ModuleNotFoundError:
    if "--live-worker" not in sys.argv:
        raise
    pytest = None

_ALLOW_ENV = "ODACV4_ALLOW_DOCUMENT_SEARCH_BULK_SMOKE"
_TARGETS = {"invoice.search", "journal_entry.search", "journal_item.search",
            "receivable.open_items.list", "payable.open_items.list", "invoice.analysis.search",
            "invoice.analysis.summary", "invoice.lines.update", "invoice.lines.add"}
_MODELS = tuple(dict.fromkeys((*settlement._MODELS, "product.product", "product.template",
                              "product.category", "uom.uom", "account.fiscal.position",
                              "mail.message", "mail.followers")))


def _root():
    return Path(__file__).resolve().parents[2]


def _summary(alias, database):
    return {"alias": alias, "database": database, "company_id": 1, "user_id": 5,
            "business_su": False, "target_capabilities": sorted(_TARGETS),
            "execution": "in_process_cli_real_orm",
            "optional_native_filters_before_pagination_and_legacy_cursors_verified": True,
            "document_currency_filter_and_company_currency_report_totals_verified": True,
            "bulk_duplicate_append_sparse_update_layout_ids_native_dynamic_sync_replay_verified": True,
            "posted_foreign_membership_unit_denials_and_untouched_rows_verified": True,
            "all_fixtures_settings_defaults_currencies_and_all_user_groups_fresh_rollback_verified": True}


if pytest is not None:
    @pytest.mark.integration
    def test_document_search_bulk_lines_roll_back_per_alias():
        config_path, runtime = lifecycle._enabled_runtime(_ALLOW_ENV)
        run_id = uuid.uuid4()
        for alias in lifecycle._ALIASES:
            command, timeout = lifecycle._worker_command(alias, run_id, config_path, runtime)
            command[1] = str(Path(__file__).resolve())
            environment = os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            environment["PYTHONPATH"] = os.pathsep.join(filter(None, (
                str(_root() / "src"), sysconfig.get_path("purelib"), environment.get("PYTHONPATH"))))
            completed = subprocess.run(command, cwd=_root(), env=environment, text=True,
                                       capture_output=True, check=False, timeout=max(timeout, 900))
            assert completed.returncode == 0, completed.stdout + completed.stderr
            assert json.loads(completed.stdout) == _summary(alias, lifecycle._DATABASES[alias])
            print(completed.stdout.strip(), flush=True)


def _exercise(admin, client, alias, run_id, marker):
    from odoo import Command, fields

    from odoo_accounting_cli_v4 import cli
    from odoo_accounting_cli_v4.bridge.core_object_reads import OdooCoreObjectReadPort
    from odoo_accounting_cli_v4.bridge.core_writes import OdooCoreWritePort
    from odoo_accounting_cli_v4.bridge.invoice_analysis import OdooInvoiceAnalysisPort
    from odoo_accounting_cli_v4.bridge.invoices import OdooInvoicePort
    from odoo_accounting_cli_v4.bridge.journal_entries import OdooJournalEntryPort
    from odoo_accounting_cli_v4.bridge.open_items import OdooOpenItemsPort
    from odoo_accounting_cli_v4.capabilities.core_writes import (
        _expected_idempotency_key,
        validate_core_write_request,
    )

    env, ids = client.env, lifecycle._fixture_ids(admin, alias)
    today = fields.Date.context_today(env.user)
    invoice_date, due = (today - timedelta(days=2)).isoformat(), (today + timedelta(days=28)).isoformat()

    def track(record):
        client.tracked[record._name].update(record.ids)
        if record._name == "account.move":
            client.tracked["account.move.line"].update(record.line_ids.ids)
        if record._name == "product.product":
            client.tracked["product.template"].update(record.product_tmpl_id.ids)
        if record._name == "account.journal":
            client.tracked["mail.alias"].update(record.alias_id.ids)
            client.tracked["account.payment.method.line"].update(
                (record.inbound_payment_method_line_ids | record.outbound_payment_method_line_ids).ids)
        if record._name == "account.tax":
            client.tracked["account.tax.repartition.line"].update(
                (record.invoice_repartition_line_ids | record.refund_repartition_line_ids).ids)
        if record._name == "account.payment.term":
            client.tracked["account.payment.term.line"].update(record.line_ids.ids)
        return record

    def fixture(model, values, *, company=1):
        return track(admin[model].with_company(admin["res.company"].browse(company)).create(values))

    def key_for(capability, parameters):
        normalized = validate_core_write_request(capability, core._request(alias, run_id, capability, parameters))[2]
        return _expected_idempotency_key(capability, normalized, 1) or f"{capability}:{run_id.hex}:{core._digest(normalized)}"

    def call(capability, parameters, *, write=False, code=0):
        if write:
            port = OdooCoreWritePort(client)
        elif capability.startswith("invoice.analysis."):
            port = OdooInvoiceAnalysisPort(client)
        elif capability == "invoice.search":
            port = OdooInvoicePort(client)
        elif capability == "journal_entry.search":
            port = OdooJournalEntryPort(client)
        elif capability in {"receivable.open_items.list", "payable.open_items.list"}:
            port = OdooOpenItemsPort(client, capability)
        else:
            port = OdooCoreObjectReadPort(client)
        argv = ["read", capability, "--request", "-"]
        if write:
            argv = ["write", "run", capability, "--request", "-", "--confirm", capability,
                    "--idempotency-key", key_for(capability, parameters)]
        stdout, stderr = io.StringIO(), io.StringIO()
        client.last_runtime_failure = None
        actual = cli.main(argv, stdin=io.StringIO(json.dumps(core._request(alias, run_id, capability, parameters))),
                          stdout=stdout, stderr=stderr, port_factory=lambda *args: port)
        response = json.loads(stdout.getvalue())
        assert actual == code and not stderr.getvalue(), response
        assert env.uid == 5 and not env.su and env.company.id == 1
        if code:
            assert not response["success"]
            return response
        assert response["success"] and response["status"] == "verified" and response["odoo"]["user_id"] == 5, response
        client.capabilities.add(capability)
        return response["data"]

    def write(capability, parameters, *, replay=True):
        first = call(capability, parameters, write=True)
        assert not first["idempotent_replay"], first
        if replay:
            second = call(capability, parameters, write=True)
            assert second["idempotent_replay"] and second["result"] == first["result"], second
        result = first["result"]
        if result["model"] == "account.move":
            track(env["account.move"].browse(result["id"]))
        return result

    def denied(capability, parameters, error, code):
        response = call(capability, parameters, write=True, code=code)
        assert response["error"]["code"] == error, response

    def page(capability, parameters, *, ids_of=lambda row: row["id"]):
        found, cursor = [], None
        while True:
            value = call(capability, {**parameters, "limit": 1, **({"cursor": cursor} if cursor else {})})
            found += [ids_of(row) for row in value["items"]]
            if not value["has_more"]:
                return found
            cursor = value["next_cursor"]
            assert cursor

    journals = {side: fixture("account.journal", {"name": marker + side, "code": side[0].upper() + run_id.hex[:4],
                "type": side, "company_id": 1, "default_account_id": ids["expense" if side == "purchase" else "income"]})
                for side in ("sale", "purchase", "general")}
    base = admin.ref("uom.product_uom_unit")
    alternate = fixture("uom.uom", {"name": marker + "six", "relative_uom_id": base.id, "relative_factor": 6})
    disallowed = fixture("uom.uom", {"name": marker + "four", "relative_uom_id": base.id, "relative_factor": 4})
    category = fixture("product.category", {"name": marker + "category", "property_account_income_categ_id": ids["income"],
                                            "property_account_expense_categ_id": ids["expense"]})
    product = fixture("product.product", {"name": marker + "service", "type": "service", "company_id": 1,
        "categ_id": category.id, "uom_id": base.id, "uom_ids": [Command.set(alternate.ids)],
        "taxes_id": [Command.clear()], "supplier_taxes_id": [Command.clear()]})
    tax = fixture("account.tax", {"name": marker + "purchase-tax", "company_id": 1, "type_tax_use": "purchase", "amount": 10})
    term = fixture("account.payment.term", {"name": marker + "term", "company_id": 1, "line_ids": [
        Command.create({"value": "percent", "value_amount": 100, "delay_type": "days_after", "nb_days": 30})]})
    fiscal = fixture("account.fiscal.position", {"name": marker + "fiscal", "company_id": 1})
    existing_codes = set(admin["res.currency"].with_context(active_test=False).search([]).mapped("name"))
    currency_code = next(f"Q{index:02X}" for index in range(256) if f"Q{index:02X}" not in existing_codes)
    foreign_currency = fixture("res.currency", {"name": currency_code, "symbol": currency_code, "active": True, "rounding": 0.01})
    fixture("res.currency.rate", {"currency_id": foreign_currency.id, "company_id": 1, "name": today.isoformat(), "rate": 0.25})
    env.invalidate_all()

    def line(label, vendor=False, **extras):
        return {"name": marker + label, "product_id": product.id,
                "account_id": ids["expense" if vendor else "income"], "quantity": "1", "price_unit": "12",
                "discount": "0", "tax_ids": tax.ids if vendor else [], **extras}

    def document(label, *, vendor=False, currency=None, owned=True):
        result = write("vendor_bill.create" if vendor else "customer_invoice.create", {
            "partner_id": ids["supplier" if vendor else "customer"], "journal_id": journals["purchase" if vendor else "sale"].id,
            "invoice_date": invoice_date, "date": today.isoformat(), "currency_id": currency or ids["currency"],
            "payment_term_id": term.id, "reference": marker + label,
            "lines": [line(label + "-one", vendor), line(label + "-two", vendor)]})
        move = env["account.move"].browse(result["id"])
        move.with_env(admin).write({"invoice_user_id": 5 if owned else False, "fiscal_position_id": fiscal.id if owned else False})
        return track(move)

    sale1, sale2 = document("sale-one", currency=foreign_currency.id), document("sale-two", currency=foreign_currency.id)
    decoy, bill = document("decoy", owned=False), document("bill", vendor=True)
    bill.with_env(admin).write({"invoice_line_ids": [Command.create({"display_type": "line_note", "name": marker + "note", "sequence": 999})]})
    track(bill)
    original_ids = sorted(bill.invoice_line_ids.ids)
    originals = bill.invoice_line_ids.sorted("id").read(["id", "name", "display_type", "quantity", "price_unit", "product_uom_id", "deductible_amount"])
    duplicate = line("duplicate", True, product_uom_id=base.id, deductible_amount="50")
    append = {"move_id": bill.id, "expected_line_ids": original_ids, "lines": [duplicate, duplicate]}
    write("invoice.lines.add", append)
    added = bill.invoice_line_ids.filtered(lambda row: row.id not in original_ids)
    assert len(added) == 2 and all(row.display_type == "product" and row.deductible_amount == 50 for row in added)
    assert bill.invoice_line_ids.filtered(lambda row: row.id in original_ids).sorted("id").read(
        ["id", "name", "display_type", "quantity", "price_unit", "product_uom_id", "deductible_amount"]) == originals
    assert bill.line_ids.filtered(lambda row: row.display_type == "non_deductible_product")
    assert env.company.currency_id.is_zero(sum(bill.line_ids.mapped("balance")))
    neighbor = bill.invoice_line_ids.filtered(lambda row: row.id not in added.ids).sorted("id").read(
        ["id", "name", "display_type", "quantity", "price_unit", "product_uom_id", "deductible_amount"])
    write("invoice.lines.update", {"move_id": bill.id, "lines": [
        {"line_id": added[1].id, "changes": {"quantity": "3", "price_unit": "11", "deductible_amount": "25", "product_uom_id": alternate.id}},
        {"line_id": added[0].id, "changes": {"name": marker + "renamed", "deductible_amount": "0"}}]})
    assert added[1].quantity == 3 and added[1].price_unit == 11 and added[1].product_uom_id == alternate and added[1].deductible_amount == 25
    assert added[0].name == marker + "renamed" and added[0].deductible_amount == 0
    assert bill.invoice_line_ids.filtered(lambda row: row.id not in added.ids).sorted("id").read(
        ["id", "name", "display_type", "quantity", "price_unit", "product_uom_id", "deductible_amount"]) == neighbor
    graph = settlement.maintenance._graph(bill)
    denied("invoice.lines.add", {**append, "expected_line_ids": original_ids[:-1]}, "idempotency_conflict", 5)
    denied("invoice.lines.update", {"move_id": bill.id, "lines": [{"line_id": sale1.invoice_line_ids[0].id, "changes": {"quantity": "2"}}]}, "record_not_found", 4)
    denied("invoice.lines.update", {"move_id": bill.id, "lines": [{"line_id": added[0].id, "changes": {"product_uom_id": disallowed.id}}]}, "business_rule_error", 6)
    assert settlement.maintenance._graph(bill) == graph

    for move in (sale1, sale2, decoy, bill):
        write("invoice.post", {"move_id": move.id})
    posted = settlement.maintenance._graph(bill)
    denied("invoice.lines.update", {"move_id": bill.id, "lines": [{"line_id": added[0].id, "changes": {"quantity": "2"}}]}, "state_conflict", 5)
    denied("invoice.lines.add", {"move_id": bill.id, "expected_line_ids": sorted(bill.invoice_line_ids.ids), "lines": [duplicate]}, "state_conflict", 5)
    assert settlement.maintenance._graph(bill) == posted

    invoice_filters = {"journal_id": journals["sale"].id, "query": marker,
        "currency_id": foreign_currency.id, "invoice_date_from": invoice_date, "invoice_date_to": invoice_date,
        "due_date_from": due, "due_date_to": due, "invoice_user_id": 5, "payment_term_id": term.id, "fiscal_position_id": fiscal.id}
    assert set(page("invoice.search", invoice_filters)) == {sale1.id, sale2.id}
    null_filters = {"journal_id": journals["sale"].id, "query": marker, "invoice_user_id": None, "fiscal_position_id": None}
    assert page("invoice.search", null_filters) == [decoy.id]
    assert page("invoice.search", {**invoice_filters, "payment_term_id": None}) == []
    assert set(page("invoice.search", {"journal_id": journals["sale"].id, "query": marker})) == {sale1.id, sale2.id, decoy.id}

    entry = env["account.move"].browse(write("journal_entry.create", {"journal_id": journals["general"].id,
        "date": today.isoformat(), "reference": marker + "entry", "lines": [
            {"name": marker + "debit", "account_id": ids["asset"], "partner_id": None, "debit": "15", "credit": "0"},
            {"name": marker + "credit", "account_id": ids["income"], "partner_id": None, "debit": "0", "credit": "15"}]})["id"])
    foreign_entry = fixture("account.move", {"move_type": "entry", "journal_id": journals["general"].id,
        "currency_id": foreign_currency.id, "date": today.isoformat(), "ref": marker + "foreign-entry",
        "line_ids": [Command.create({"name": marker + "foreign-debit", "account_id": ids["asset"],
            "balance": 15.0, "currency_id": foreign_currency.id, "amount_currency": 3.75}),
            Command.create({"name": marker + "foreign-credit", "account_id": ids["income"],
            "balance": -15.0, "currency_id": foreign_currency.id, "amount_currency": -3.75})]})
    assert page("journal_entry.search", {"query": marker, "currency_id": ids["currency"], "account_id": ids["asset"]}) == [entry.id]
    assert page("journal_entry.search", {"query": marker, "currency_id": foreign_currency.id}) == [foreign_entry.id]
    foreign_header = call("journal_entry.search", {"query": marker, "currency_id": foreign_currency.id})["items"][0]
    assert foreign_header["currency"]["id"] == ids["currency"] != foreign_entry.currency_id.id
    assert Decimal(foreign_header["debit"]) == 15 and Decimal(foreign_header["credit"]) == 15
    term_lines = sale1.line_ids.filtered(lambda row: row.display_type == "payment_term")
    journal_filters = {"move_id": sale1.id, "currency_id": foreign_currency.id,
                       "due_date_from": due, "due_date_to": due, "reconciled": False,
                       "move_types": ["out_invoice"], "query": sale1.name}
    assert set(page("journal_item.search", journal_filters)) == set(term_lines.ids)
    assert page("journal_item.search", {**journal_filters, "reconciled": True}) == []
    assert page("journal_item.search", {**journal_filters, "move_types": ["in_invoice"]}) == []
    assert set(page("journal_item.search", {"move_id": sale1.id})) == set(sale1.line_ids.ids)
    for capability, move, types in (("receivable.open_items.list", sale1, ["out_invoice"]),
                                    ("payable.open_items.list", bill, ["in_invoice"])):
        expected = move.line_ids.filtered(lambda row: row.display_type == "payment_term")
        assert set(page(capability, {"move_id": move.id, "move_types": types})) == set(expected.ids)
        assert page(capability, {"move_id": move.id, "move_types": ["entry"]}) == []

    analysis = {"date_from": invoice_date, "date_to": invoice_date, "journal_id": journals["sale"].id,
                "currency_id": foreign_currency.id, "due_date_from": due, "due_date_to": due}
    rows = page("invoice.analysis.search", analysis)
    native = env["account.invoice.report"].search([("company_id", "=", 1), ("journal_id", "=", journals["sale"].id),
        ("currency_id", "=", foreign_currency.id), ("invoice_date", "=", invoice_date), ("invoice_date_due", "=", due)])
    assert set(rows) == set(native.ids) and len(rows) == 4
    summary = call("invoice.analysis.summary", {**analysis, "group_by": "partner"})
    for output, field in (("untaxed_amount", "price_subtotal"), ("total_amount", "price_total"),
                           ("margin", "price_margin"), ("inventory_value", "inventory_value")):
        assert env.company.currency_id.is_zero(float(Decimal(summary["totals"][output])) - sum(native.mapped(field))), summary
    assert summary["totals"]["row_count"] == len(native) and summary["company_currency"]["id"] == ids["currency"]
    assert page("invoice.analysis.search", {**analysis, "due_date_from": (today + timedelta(days=31)).isoformat(), "due_date_to": None}) == []

    # All ordinary successful calls precede the company2 fixture.
    draft = document("foreign-denial")
    draft_graph = settlement.maintenance._graph(draft)
    foreign_product = fixture("product.product", {"name": marker + "foreign", "type": "service", "company_id": 2,
        "categ_id": category.id, "uom_id": base.id}, company=2)
    denied("invoice.lines.add", {"move_id": draft.id, "expected_line_ids": sorted(draft.invoice_line_ids.ids),
        "lines": [line("foreign-add", product_id=foreign_product.id)]}, "record_not_found", 4)
    assert settlement.maintenance._graph(draft) == draft_graph
    assert _TARGETS <= client.capabilities


def _live_worker():
    settlement._MODELS, settlement._exercise, settlement._summary = _MODELS, _exercise, _summary
    return settlement._live_worker()


if __name__ == "__main__":
    raise SystemExit(_live_worker())
