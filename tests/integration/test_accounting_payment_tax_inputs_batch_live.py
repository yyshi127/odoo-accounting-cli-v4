"""One ordinary-user CLI payment/tax consumer workflow; all fixtures are rolled back."""

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

_ALLOW_ENV = "ODACV4_ALLOW_ACCOUNTING_PAYMENT_TAX_INPUTS_SMOKE"
_TARGETS = {"receivable.payment.register", "payable.payment.register", "journal_entry.create", "journal_entry.lines.replace",
            "journal_entry.lines.update", "journal_entry.lines.add", "journal_item.get", "journal_item.search", "journal_item.processing_details.get"}
_MODELS = tuple(dict.fromkeys((*settlement._MODELS, "res.partner", "res.partner.bank", "account.payment.register",
                             "account.report.line", "account.report.expression", "account.account.tag", "sale.order", "sale.order.line")))
_TAX_FIELDS = ["tax_ids", "tax_line_id", "tax_base_amount", "tax_tag_ids", "tax_repartition_line_id"]


def _root():
    return Path(__file__).resolve().parents[2]


def _summary(alias, database):
    return {"alias": alias, "database": database, "company_id": 1, "user_id": 5, "business_su": False,
            "target_capabilities": sorted(_TARGETS), "execution": "in_process_cli_real_orm",
            "single_and_grouped_inbound_outbound_explicit_method_bank_native_consumers_and_replays_verified": True,
            "complete_manual_tax_create_replace_update_clear_restore_add_and_three_projections_verified": True,
            "native_tax_report_single_plain_tag_balance_and_sequential_leading_minus_consumer_verified": True,
            "unsupported_auto_sync_posted_generated_and_foreign_denials_preserve_state_verified": True,
            "full_fixtures_settings_defaults_currency_rates_and_all_user_groups_fresh_rollback_verified": True}


if pytest is not None:
    @pytest.mark.integration
    def test_accounting_payment_tax_inputs_roll_back_per_alias():
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

    env = client.env
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
        if model == "account.move":
            client.tracked["account.move.line"].update(record.line_ids.ids)
        return record

    def account(label, account_type, *, company=1, reconcile=False):
        return fixture("account.account", {"name": marker + label, "code": "T" + uuid.uuid5(run_id, label).hex[:9],
                       "account_type": account_type, "reconcile": reconcile, "company_ids": [Command.set([company])]}, company=company)

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

    def denied(capability, parameters, error, code, *, move=None, key=None):
        before = maintenance._graph(move) if move is not None else None
        response = call(capability, parameters, key=key or key_for(capability, parameters), exit_code=code)
        assert response["error"]["code"] in ({error} if isinstance(error, str) else error) and response["data"] is None, response
        env.invalidate_all()
        if move is not None:
            assert maintenance._graph(move) == before, response

    income, expense = account("income", "income"), account("expense", "expense")
    receivable, payable = account("receivable", "asset_receivable", reconcile=True), account("payable", "liability_payable", reconcile=True)
    liquidity, suspense = account("liquidity", "asset_cash", reconcile=True), account("suspense", "asset_current", reconcile=True)
    outstanding = {direction: account(direction, "asset_current", reconcile=True) for direction in ("inbound", "outbound")}
    tax_account = account("tax", "liability_current")
    partners = {supplier: fixture("res.partner", {"name": marker + ("supplier" if supplier else "customer"), "is_company": True,
                "supplier_rank": int(supplier), "customer_rank": int(not supplier), "company_id": False,
                "property_account_receivable_id": receivable.id, "property_account_payable_id": payable.id}) for supplier in (False, True)}
    general = fixture("account.journal", {"name": marker + "general", "code": "G" + run_id.hex[:4], "type": "general", "company_id": 1})
    journals = {supplier: fixture("account.journal", {"name": marker + ("purchase" if supplier else "sale"), "code": ("P" if supplier else "S") + run_id.hex[:4],
                "type": "purchase" if supplier else "sale", "company_id": 1, "default_account_id": expense.id if supplier else income.id}) for supplier in (False, True)}
    company_bank = fixture("res.partner.bank", {"acc_number": marker + "company-bank", "partner_id": env.company.partner_id.id, "company_id": 1, "allow_out_payment": True})
    vendor_banks = [fixture("res.partner.bank", {"acc_number": marker + suffix, "partner_id": partners[True].id,
                    "company_id": 1, "allow_out_payment": True}) for suffix in ("vendor-first", "vendor-selected")]
    bank = fixture("account.journal", {"name": marker + "bank", "code": "B" + run_id.hex[:4], "type": "bank", "company_id": 1,
                   "default_account_id": liquidity.id, "suspense_account_id": suspense.id, "bank_account_id": company_bank.id})
    methods = {}
    for direction in ("inbound", "outbound"):
        primary = getattr(bank, direction + "_payment_method_line_ids").filtered(lambda row: row.code == "manual")[:1]
        assert primary, direction
        primary.write({"payment_account_id": outstanding[direction].id})
        methods[direction] = fixture("account.payment.method.line", {"name": marker + direction, "journal_id": bank.id,
                             "payment_method_id": primary.payment_method_id.id, "payment_account_id": outstanding[direction].id, "sequence": 100})
    env.invalidate_all()

    def invoice(label, *, supplier=False, amount="30"):
        move = env["account.move"].browse(write("vendor_bill.create" if supplier else "customer_invoice.create", {
            "partner_id": partners[supplier].id, "journal_id": journals[supplier].id, "invoice_date": today, "date": today,
            "currency_id": env.company.currency_id.id, "reference": marker + label,
            "lines": [{"name": marker + label, "account_id": expense.id if supplier else income.id,
                       "quantity": "1", "price_unit": amount, "tax_ids": []}]})["id"])
        write("invoice.post", {"move_id": move.id})
        return move

    for supplier in (False, True):
        direction = "outbound" if supplier else "inbound"
        capability = "payable.payment.register" if supplier else "receivable.payment.register"
        references = {"payment_method_line_id": methods[direction].id, "partner_bank_id": vendor_banks[1].id if supplier else company_bank.id}
        for many in (False, True):
            sources = [invoice(f"{direction}-{many}-{number}", supplier=supplier, amount=amount) for number, amount in enumerate(("40", "60") if many else ("30",))]
            source_lines = {move.id: move.line_ids.ids for move in sources}
            fixed_fields = ["id", "account_id", "partner_id", "debit", "credit", "balance", "currency_id", "amount_currency", *_TAX_FIELDS]
            source_financial = {move.id: move.line_ids.sorted("id").read(fixed_fields, load=None) for move in sources}
            params = {"move_ids": sorted(move.id for move in sources)} if many else {"move_id": sources[0].id}
            params.update({"journal_id": bank.id, "payment_date": today, **references})
            value = write(capability, params, replay=True)
            payment = env["account.payment"].browse(value["id"])
            assert payment.payment_type == direction and payment.payment_method_line_id.id == references["payment_method_line_id"] and payment.partner_bank_id.id == references["partner_bank_id"], value
            assert payment.amount == (100 if many else 30) and payment.move_id.state == "posted", value
            assert env.company.currency_id.is_zero(sum(payment.move_id.line_ids.mapped("balance")))
            assert all(move.amount_residual == 0 and move.line_ids.ids == source_lines[move.id] for move in sources), value
            assert all(move.line_ids.sorted("id").read(fixed_fields, load=None) == source_financial[move.id] for move in sources), value
            assert all(move.line_ids.matched_debit_ids or move.line_ids.matched_credit_ids for move in sources)
            # Single requests retain the source key; grouped requests hash the changed selection.
            drift = {**params, "payment_method_line_id": getattr(bank, direction + "_payment_method_line_ids")[:1].id}
            denied(capability, drift, "state_conflict" if many else "idempotency_conflict", 5, move=sources[0])
        unpaid = invoice(direction + "denial", supplier=supplier)
        params = {"move_id": unpaid.id, "journal_id": bank.id, "payment_date": today, **references}
        denied(capability, {**params, "payment_method_line_id": methods["inbound" if supplier else "outbound"].id}, "record_not_found", 4, move=unpaid)
        if not supplier:
            denied(capability, {**params, "partner_bank_id": vendor_banks[1].id}, "business_rule_error", 6, move=unpaid)

    report = admin.ref("account.generic_tax_report")
    expression_label = report.column_ids[:1].expression_label
    assert expression_label
    report_line = fixture("account.report.line", {"name": marker + "report", "report_id": report.id, "sequence": 9999})
    expression = fixture("account.report.expression", {"report_line_id": report_line.id, "label": expression_label,
                         "engine": "tax_tags", "formula": marker})
    tag = admin["account.account.tag"]._get_tax_tags(marker, report.country_id.id)
    assert len(tag) == 1 and tag.name == marker and tag.applicability == "taxes" and tag.country_id == report.country_id
    client.tracked["account.account.tag"].update(tag.ids)
    group = fixture("account.tax.group", {"name": marker + "group", "company_id": 1})
    tax = fixture("account.tax", {"name": marker + "tax", "company_id": 1, "tax_group_id": group.id,
                  "type_tax_use": "none", "amount_type": "percent", "amount": 10, "price_include_override": "tax_excluded"})
    repartition = tax.invoice_repartition_line_ids.filtered(lambda row: row.repartition_type == "tax")
    repartition.write({"account_id": tax_account.id})
    env.invalidate_all()

    def tax_lines(base="100", tax_amount="10"):
        clean = {"tax_ids": [], "tax_tag_ids": [], "tax_repartition_line_id": None, "tax_base_amount": "0"}
        return [{"name": marker + "base", "account_id": expense.id, "partner_id": None, "debit": base, "credit": "0", **clean, "tax_ids": [tax.id]},
                {"name": marker + "tax-line", "account_id": tax_account.id, "partner_id": None, "debit": tax_amount, "credit": "0", **clean,
                 "tax_tag_ids": tag.ids, "tax_repartition_line_id": repartition.id, "tax_base_amount": base},
                {"name": marker + "counter", "account_id": income.id, "partner_id": None, "debit": "0", "credit": str(Decimal(base) + Decimal(tax_amount)), **clean}]

    entry = env["account.move"].browse(write("journal_entry.create", {"journal_id": general.id, "date": today, "reference": marker, "lines": tax_lines()}, replay=True)["id"])

    def projections(move):
        params, rows = {"move_id": move.id, "posted_only": False, "limit": 1}, []
        while True:
            page = call("journal_item.search", params)
            rows.extend(page["items"])
            if not page["has_more"]:
                break
            params = {**params, "cursor": page["next_cursor"]}
        assert [row["id"] for row in rows] == sorted(move.line_ids.ids), rows
        for native, row in zip(move.line_ids.sorted("id"), rows, strict=True):
            expected = {"tax_ids": sorted(native.tax_ids.ids), "tax_line_id": native.tax_line_id.id or None,
                        "tax_base_amount": _decimal_string(native.tax_base_amount), "tax_tag_ids": sorted(native.tax_tag_ids.ids),
                        "tax_repartition_line_id": native.tax_repartition_line_id.id or None}
            assert {field: row[field] for field in _TAX_FIELDS} == expected, (row, expected)
            assert call("journal_item.get", {"line_id": native.id}) == row
            detail = call("journal_item.processing_details.get", {"journal_item_id": native.id})
            assert {field: detail[field] for field in _TAX_FIELDS} == expected and detail["display_type"] == "product", (detail, expected)

    projections(entry)
    write("journal_entry.lines.replace", {"move_id": entry.id, "lines": tax_lines("200", "20")}, replay=True)
    projections(entry)
    original = entry.line_ids.sorted("id")
    balances = original.read(["id", "balance", "debit", "credit", "amount_currency"], load=None)
    tax_values = original.read(["tax_ids", "tax_tag_ids", "tax_repartition_line_id", "tax_base_amount"], load=None)
    clear = {"tax_ids": [], "tax_tag_ids": [], "tax_repartition_line_id": None, "tax_base_amount": "0"}
    write("journal_entry.lines.update", {"move_id": entry.id, "lines": [{"line_id": row.id, "changes": clear} for row in original]}, replay=True)
    assert original.read(["id", "balance", "debit", "credit", "amount_currency"], load=None) == balances
    restored = []
    for row, values in zip(original, tax_values, strict=True):
        changes = {**values, "tax_ids": sorted(values["tax_ids"]), "tax_tag_ids": sorted(values["tax_tag_ids"]),
                   "tax_repartition_line_id": values["tax_repartition_line_id"] or None, "tax_base_amount": _decimal_string(values["tax_base_amount"])}
        changes.pop("id")
        restored.append({"line_id": row.id, "changes": changes})
    write("journal_entry.lines.update", {"move_id": entry.id, "lines": restored}, replay=True)
    explicit_tax_line = original.filtered(lambda row: row.tax_repartition_line_id)
    # Separate metadata edit: native tax synchronisation must first restore its real base.
    write("journal_entry.lines.update", {"move_id": entry.id, "lines": [{"line_id": explicit_tax_line.id, "changes": {"tax_base_amount": "999"}}]}, replay=True)
    assert original.read(["id", "balance", "debit", "credit", "amount_currency"], load=None) == balances
    retained = original.read(maintenance._FINANCIAL + ["tax_tag_ids", "tax_base_amount"], load=None)
    write("journal_entry.lines.add", {"move_id": entry.id, "expected_line_ids": sorted(entry.line_ids.ids), "lines": tax_lines("75", "7.5")}, replay=True)
    assert original.read(maintenance._FINANCIAL + ["tax_tag_ids", "tax_base_amount"], load=None) == retained
    projections(entry)
    write("journal_entry.post", {"move_id": entry.id})
    snapshot = maintenance._graph(entry)

    def report_value():
        page = core._cli(client, alias, run_id, "report.tax", {"date_from": today, "date_to": today, "limit": 1000})
        rows = page["lines"]
        while page["has_more"]:
            page = core._cli(client, alias, run_id, "report.tax", {"date_from": today, "date_to": today, "limit": 1000, "cursor": page["next_cursor"]})
            rows += page["lines"]
        row = next(row for row in rows if row["id"] == report._get_generic_line_id("account.report.line", report_line.id))
        column = next(column["index"] for column in page["columns"] if column["expression_label"] == expression_label)
        return Decimal(row["values"][column])

    positive = report_value()
    expected_balance = sum(entry.line_ids.filtered(lambda row: tag.id in row.tax_tag_ids.ids).mapped("balance"))
    assert env.company.currency_id.is_zero(float(positive) - expected_balance) and positive == Decimal("27.5"), (positive, expected_balance)
    # Native v19 maps one plain tag per expression batch; evaluate +/- sequentially on the owned expression.
    expression.write({"formula": "-" + marker})
    env.invalidate_all()
    assert report_value() == -positive and maintenance._graph(entry) == snapshot
    denied("journal_entry.lines.update", {"move_id": entry.id, "lines": [{"line_id": entry.line_ids[:1].id, "changes": clear}]}, "state_conflict", 5, move=entry)

    simple = [{key: value for key, value in row.items() if key not in clear} for row in tax_lines() if row["name"] != marker + "tax-line"]
    simple[1]["credit"] = "100"
    draft = env["account.move"].browse(write("journal_entry.create", {"journal_id": general.id, "date": today, "lines": simple})["id"])
    denied("journal_entry.lines.update", {"move_id": draft.id, "lines": [{"line_id": draft.line_ids[:1].id, "changes": {"tax_ids": [tax.id]}}]},
           {"business_rule_error", "odoo_write_error"}, 6, move=draft)
    generated = fixture("account.move", {"company_id": 1, "journal_id": general.id, "date": today, "move_type": "entry", "reversed_entry_id": entry.id,
                        "line_ids": [Command.create({**row, "partner_id": False, "debit": Decimal(row["debit"]), "credit": Decimal(row["credit"])}) for row in simple]})
    denied("journal_entry.lines.add", {"move_id": generated.id, "expected_line_ids": sorted(generated.line_ids.ids), "lines": tax_lines()}, "business_rule_error", 6, move=generated)
    # A native source-link fixture tests this guard, not a sale-order invoicing lifecycle.
    order = fixture("sale.order", {"partner_id": partners[False].id, "company_id": 1})
    source_line = fixture("sale.order.line", {"order_id": order.id, "name": marker + "source-link", "display_type": "line_note"})
    draft.with_env(admin).line_ids[:1].write({"sale_line_ids": [Command.link(source_line.id)]})
    denied("journal_entry.lines.update", {"move_id": draft.id, "lines": [{"line_id": draft.line_ids[:1].id, "changes": clear}]}, "business_rule_error", 6, move=draft)
    draft.with_env(admin).line_ids[:1].write({"sale_line_ids": [Command.clear()]})
    client.tracked["account.payment.register"].update(admin["account.payment.register"].search([("communication", "like", "%" + run_id.hex + "%")]).ids)

    # Foreign fixtures last: ordinary successful-call collection must not traverse co2 records.
    other_group = fixture("account.tax.group", {"name": marker + "foreign-group", "company_id": 2}, company=2)
    other_tax = fixture("account.tax", {"name": marker + "foreign-tax", "company_id": 2, "tax_group_id": other_group.id, "type_tax_use": "none", "amount": 10}, company=2)
    denied("journal_entry.lines.update", {"move_id": draft.id, "lines": [{"line_id": draft.line_ids[:1].id, "changes": {"tax_ids": other_tax.ids}}]}, "record_not_found", 4, move=draft)
    denied("journal_entry.lines.update", {"move_id": draft.id, "lines": [{"line_id": draft.line_ids[:1].id, "changes": {"tax_repartition_line_id": other_tax.invoice_repartition_line_ids[:1].id}}]}, "record_not_found", 4, move=draft)
    other_partner = fixture("res.partner", {"name": marker + "foreign-partner", "company_id": 2}, company=2)
    other_bank = fixture("res.partner.bank", {"acc_number": marker + "foreign-bank", "partner_id": other_partner.id}, company=2)
    assert other_bank.company_id.id == 2
    denied("payable.payment.register", {"move_id": unpaid.id, "journal_id": bank.id, "payment_date": today, "partner_bank_id": other_bank.id}, "record_not_found", 4, move=unpaid)
    assert _TARGETS <= client.capabilities


def _live_worker():
    # Reuse exact-user/groups/company/defaults/currency fresh-cursor rollback oracle, not a fake registry.
    settlement._MODELS, settlement._exercise, settlement._summary = _MODELS, _exercise, _summary
    return settlement._live_worker()


if __name__ == "__main__":
    raise SystemExit(_live_worker())
