"""One shared ordinary-user CLI workflow; full fresh-cursor rollback oracle."""
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

import test_document_search_bulk_lines_live as previous

settlement, core, lifecycle = previous.settlement, previous.core, previous.lifecycle
try:
    import pytest
except ModuleNotFoundError:
    if "--live-worker" not in sys.argv:
        raise
    pytest = None

_ALLOW_ENV = "ODACV4_ALLOW_BUSINESS_LINE_SEARCH_REMOVE_SMOKE"
_TARGETS = {"invoice.search", "journal_entry.search", "journal_item.search",
            "receivable.open_items.list", "payable.open_items.list", "invoice.analysis.search",
            "invoice.analysis.summary", "invoice.lines.remove"}
_MODELS = previous._MODELS


def _root():
    return Path(__file__).resolve().parents[2]


def _summary(alias, database):
    return {"alias": alias, "database": database, "company_id": 1, "user_id": 5, "business_su": False,
            "target_capabilities": sorted(_TARGETS), "execution": "in_process_cli_real_orm",
            "same_line_product_account_applied_tax_and_entry_text_filters_verified": True,
            "owner_term_fiscal_unset_filters_before_pagination_legacy_cursors_verified": True,
            "native_report_owner_fiscal_account_company_currency_totals_verified": True,
            "bulk_delete_survivor_ids_inputs_layout_native_dynamic_sync_and_empty_business_graph_verified": True,
            "posted_wrong_parent_layout_missing_and_retry_denials_verified": True,
            "all_fixtures_settings_defaults_currencies_and_all_user_groups_fresh_rollback_verified": True}


if pytest is not None:
    @pytest.mark.integration
    def test_business_line_search_remove_roll_back_per_alias():
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
    invoice_date = (today - timedelta(days=2)).isoformat()

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

    def fixture(model, values):
        return track(admin[model].with_company(admin["res.company"].browse(1)).create(values))

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
            normalized = validate_core_write_request(capability, core._request(alias, run_id, capability, parameters))[2]
            key = _expected_idempotency_key(capability, normalized, 1)
            assert key
            argv = ["write", "run", capability, "--request", "-", "--confirm", capability, "--idempotency-key", key]
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

    def page(capability, parameters):
        found, cursor = [], None
        while True:
            value = call(capability, {**parameters, "limit": 1, **({"cursor": cursor} if cursor else {})})
            found += [row["id"] for row in value["items"]]
            if not value["has_more"]:
                return found
            cursor = value["next_cursor"]
            assert cursor

    journals = {side: fixture("account.journal", {"name": marker + side, "code": side[0].upper() + run_id.hex[:4],
        "type": side, "company_id": 1, "default_account_id": ids["expense" if side == "purchase" else "income"]})
        for side in ("sale", "purchase", "general")}
    base = admin.ref("uom.product_uom_unit")
    category = fixture("product.category", {"name": marker + "category", "property_account_income_categ_id": ids["income"],
                                            "property_account_expense_categ_id": ids["expense"]})
    products = [fixture("product.product", {"name": marker + label, "type": "service", "company_id": 1,
        "categ_id": category.id, "uom_id": base.id, "taxes_id": [Command.clear()], "supplier_taxes_id": [Command.clear()]})
        for label in ("product-p", "product-q")]
    tax = fixture("account.tax", {"name": marker + "purchase-tax", "company_id": 1, "type_tax_use": "purchase", "amount": 10})
    term = fixture("account.payment.term", {"name": marker + "term", "company_id": 1, "line_ids": [
        Command.create({"value": "percent", "value_amount": 100, "delay_type": "days_after", "nb_days": 30})]})
    fiscal = fixture("account.fiscal.position", {"name": marker + "fiscal", "company_id": 1})

    def line(label, product=0, account=None, taxes=False, **extras):
        return {"name": marker + label, "product_id": products[product].id, "account_id": account or ids["expense"],
                "quantity": 1.0, "price_unit": 12.0, "tax_ids": [Command.set(tax.ids if taxes else [])], **extras}

    def document(label, rows, *, vendor=True, owned=True):
        return fixture("account.move", {"move_type": "in_invoice" if vendor else "out_invoice",
            "partner_id": ids["supplier" if vendor else "customer"], "journal_id": journals["purchase" if vendor else "sale"].id,
            "invoice_date": invoice_date, "date": today.isoformat(), "currency_id": ids["currency"], "ref": marker + label,
            "invoice_user_id": 5 if owned else False, "invoice_payment_term_id": term.id if owned else False,
            "fiscal_position_id": fiscal.id if owned else False, "invoice_line_ids": [Command.create(row) for row in rows]})

    bills = [document(label, [line(label + "wanted", taxes=True), line(label + "other", product=1, account=ids["income"])])
             for label in ("bill-a", "bill-b")]
    trap = document("bill-trap", [line("trap-p"), line("trap-q", product=1, taxes=True)], owned=False)
    sales = [document(label, [line(label, account=ids["income"])], vendor=False, owned=owned)
             for label, owned in (("sale-owned", True), ("sale-unset", False))]
    draft = document("draft-delete", [line("keep", taxes=True), line("delete-one", taxes=True, deductible_amount=50.0),
        line("delete-two", product=1, taxes=True), {"display_type": "line_note", "name": marker + "note", "sequence": 999}])
    env.invalidate_all()
    business = draft.invoice_line_ids.filtered(lambda row: row.display_type == "product").sorted("id")
    note = draft.invoice_line_ids.filtered(lambda row: row.display_type == "line_note")
    selected = business[1:]
    preserved = business[:1] | note
    preserved_fields = ["id", "name", "display_type", "sequence", "product_id", "account_id", "quantity", "price_unit", "tax_ids",
                        "analytic_distribution", "product_uom_id", "deductible_amount"]
    before_survivors = preserved.sorted("id").read(preserved_fields)
    graph = settlement.maintenance._graph(draft)
    for line_ids in ([selected[0].id, bills[0].invoice_line_ids[0].id], [selected[0].id, note.id], [selected[0].id, 2147483647]):
        denied = call("invoice.lines.remove", {"move_id": draft.id, "line_ids": line_ids}, write=True, code=4)
        assert denied["error"]["code"] == "record_not_found"
        assert settlement.maintenance._graph(draft) == graph
    value = call("invoice.lines.remove", {"move_id": draft.id, "line_ids": list(reversed(selected.ids))}, write=True)
    assert not value["idempotent_replay"] and not set(selected.ids) & set(value["result"]["line_ids"])
    track(draft)
    assert set(draft.invoice_line_ids.ids) == set(preserved.ids)
    assert preserved.sorted("id").read(preserved_fields) == before_survivors
    assert env.company.currency_id.is_zero(sum(draft.line_ids.mapped("balance")))
    assert Decimal(str(draft.amount_total)) == Decimal("13.2")
    graph = settlement.maintenance._graph(draft)
    retry = call("invoice.lines.remove", {"move_id": draft.id, "line_ids": selected.ids}, write=True, code=4)
    assert retry["error"]["code"] == "record_not_found" and settlement.maintenance._graph(draft) == graph
    empty = document("empty-delete", [line("only")])
    call("invoice.lines.remove", {"move_id": empty.id, "line_ids": empty.invoice_line_ids.ids}, write=True)
    track(empty)
    assert not empty.invoice_line_ids and env.company.currency_id.is_zero(sum(empty.line_ids.mapped("balance")))

    for move in (*bills, trap, *sales):
        move.with_env(env).action_post()
        track(move)
    posted = settlement.maintenance._graph(bills[0])
    denied = call("invoice.lines.remove", {"move_id": bills[0].id, "line_ids": bills[0].invoice_line_ids[:1].ids}, write=True, code=5)
    assert denied["error"]["code"] == "state_conflict" and settlement.maintenance._graph(bills[0]) == posted

    invoice_filters = {"journal_id": journals["purchase"].id, "query": marker + "bill", "product_id": products[0].id,
                       "account_id": ids["expense"], "tax_id": tax.id}
    assert set(page("invoice.search", invoice_filters)) == {move.id for move in bills}
    assert page("invoice.search", {**invoice_filters, "account_id": ids["income"]}) == []
    assert set(page("invoice.search", {"journal_id": journals["purchase"].id, "query": marker + "bill"})) == {trap.id, *(move.id for move in bills)}
    first = call("invoice.search", {**invoice_filters, "limit": 1})
    assert first["has_more"]
    misuse = call("invoice.search", {**invoice_filters, "product_id": products[1].id, "limit": 1, "cursor": first["next_cursor"]}, code=2)
    assert misuse["error"]["code"] == "invalid_cursor"

    entries = []
    for label, same_line in (("entry-match", True), ("entry-trap", False)):
        entries.append(fixture("account.move", {"move_type": "entry", "journal_id": journals["general"].id, "date": today.isoformat(),
            "ref": marker + label, "line_ids": [
                Command.create({"name": marker + "entry-wanted", "account_id": ids["asset"], "debit": 15.0,
                                "tax_ids": [Command.set(tax.ids if same_line else [])]}),
                Command.create({"name": marker + "entry-other", "account_id": ids["income"], "credit": 15.0,
                                "tax_ids": [Command.set([] if same_line else tax.ids)]})]}))
    assert page("journal_entry.search", {"journal_id": journals["general"].id, "query": marker,
        "account_id": ids["asset"], "tax_id": tax.id, "line_query": "entry-wanted"}) == [entries[0].id]
    assert set(page("journal_entry.search", {"journal_id": journals["general"].id, "account_id": ids["asset"], "line_query": None})) == {move.id for move in entries}
    assert page("journal_entry.search", {"journal_id": journals["general"].id, "query": "entry-wanted"}) == []
    wanted = bills[0].invoice_line_ids.filtered(lambda row: row.product_id == products[0])
    assert page("journal_item.search", {"move_id": bills[0].id, "product_id": products[0].id, "tax_id": tax.id}) == wanted.ids
    assert page("journal_item.search", {"move_id": bills[0].id, "product_id": products[1].id, "tax_id": tax.id}) == []

    for capability, owned, unset in (("receivable.open_items.list", sales[0], sales[1]),
                                     ("payable.open_items.list", bills[0], trap)):
        expected = owned.line_ids.filtered(lambda row: row.display_type == "payment_term")
        filters = {"move_id": owned.id, "invoice_user_id": 5, "payment_term_id": term.id, "fiscal_position_id": fiscal.id}
        assert set(page(capability, filters)) == set(expected.ids)
        assert page(capability, {**filters, "invoice_user_id": None}) == []
        assert page(capability, {**filters, "payment_term_id": None}) == []
        assert page(capability, {**filters, "fiscal_position_id": None}) == []
        nulls = {"move_id": unset.id, "invoice_user_id": None, "payment_term_id": None, "fiscal_position_id": None}
        assert set(page(capability, nulls)) == set(unset.line_ids.filtered(lambda row: row.display_type == "payment_term").ids)

    analysis = {"date_from": invoice_date, "date_to": invoice_date, "journal_id": journals["purchase"].id,
                "invoice_user_id": 5, "fiscal_position_id": fiscal.id, "account_id": ids["expense"], "states": ["posted"]}
    native = env["account.invoice.report"].search([("company_id", "=", 1), ("journal_id", "=", journals["purchase"].id),
        ("invoice_date", "=", invoice_date), ("invoice_user_id", "=", 5), ("fiscal_position_id", "=", fiscal.id),
        ("account_id", "=", ids["expense"]), ("state", "=", "posted")])
    assert set(page("invoice.analysis.search", analysis)) == set(native.ids) and len(native) == 2
    summary = call("invoice.analysis.summary", {**analysis, "group_by": "partner"})
    for output, field in (("untaxed_amount", "price_subtotal"), ("total_amount", "price_total"),
                           ("margin", "price_margin"), ("inventory_value", "inventory_value")):
        assert env.company.currency_id.is_zero(float(Decimal(summary["totals"][output])) - sum(native.mapped(field))), summary
    assert summary["totals"]["row_count"] == len(native) and summary["company_currency"]["id"] == ids["currency"]
    null_analysis = {**analysis, "invoice_user_id": None, "fiscal_position_id": None}
    assert set(page("invoice.analysis.search", null_analysis)) == set(trap.invoice_line_ids.ids)
    null_summary = call("invoice.analysis.summary", {**null_analysis, "group_by": "partner"})
    assert null_summary["totals"]["row_count"] == 2
    assert _TARGETS <= client.capabilities


def _live_worker():
    settlement._MODELS, settlement._exercise, settlement._summary = _MODELS, _exercise, _summary
    return settlement._live_worker()


if __name__ == "__main__":
    raise SystemExit(_live_worker())
