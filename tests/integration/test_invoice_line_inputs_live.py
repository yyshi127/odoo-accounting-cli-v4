"""Shared ordinary-user invoice line inputs workflow; full fresh rollback."""
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

core, lifecycle = settlement.core, settlement.lifecycle

try:
    import pytest
except ModuleNotFoundError:
    if "--live-worker" not in sys.argv:
        raise
    pytest = None

_ALLOW_ENV = "ODACV4_ALLOW_INVOICE_LINE_INPUTS_SMOKE"
_TARGETS = {"customer_invoice.create", "vendor_bill.create", "invoice.line.create",
            "invoice.line.update", "invoice.lines.replace", "customer_credit_note.create",
            "vendor_refund.create", "invoice.get"}
_MODELS = tuple(dict.fromkeys((*settlement._MODELS, "product.product", "product.template",
                              "product.category", "uom.uom", "mail.message", "mail.followers")))


def _root():
    return Path(__file__).resolve().parents[2]


def _summary(alias, database):
    return {"alias": alias, "database": database, "company_id": 1, "user_id": 5,
            "business_su": False, "target_capabilities": sorted(_TARGETS),
            "execution": "in_process_cli_real_orm",
            "explicit_native_unit_quantity_price_and_percentage_persist_replay_verified": True,
            "native_non_deductible_generated_lines_and_purchase_tax_sync_verified": True,
            "custom_customer_credit_and_vendor_refund_lines_verified": True,
            "legacy_omission_preserves_native_defaults_and_replay_verified": True,
            "native_allowed_unit_parent_membership_sales_percentage_posted_foreign_denials_verified": True,
            "all_fixtures_settings_defaults_currencies_and_all_user_groups_fresh_rollback_verified": True}


if pytest is not None:
    @pytest.mark.integration
    def test_invoice_line_inputs_roll_back_per_alias():
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

    from odoo_accounting_cli_v4.capabilities.core_writes import (
        _expected_idempotency_key,
        validate_core_write_request,
    )

    env, ids = client.env, lifecycle._fixture_ids(admin, alias)
    today = fields.Date.context_today(env.user).isoformat()

    def track(record):
        client.tracked[record._name].update(record.ids)
        if record._name == "product.product":
            client.tracked["product.template"].update(record.product_tmpl_id.ids)
        if record._name == "account.journal":
            client.tracked["mail.alias"].update(record.alias_id.ids)
            client.tracked["account.payment.method.line"].update(
                (record.inbound_payment_method_line_ids | record.outbound_payment_method_line_ids).ids)
        if record._name == "account.move":
            client.tracked["account.move.line"].update(record.line_ids.ids)
        if record._name == "account.tax":
            client.tracked["account.tax.repartition.line"].update(
                (record.invoice_repartition_line_ids | record.refund_repartition_line_ids).ids)
        return record

    def fixture(model, values, *, company=1):
        return track(admin[model].with_company(admin["res.company"].browse(company)).create(values))

    def key_for(capability, parameters):
        normalized = validate_core_write_request(capability, core._request(alias, run_id, capability, parameters))[2]
        return _expected_idempotency_key(capability, normalized, 1) or (
            f"{capability}:{run_id.hex}:{lifecycle._canonical_digest(normalized)[:32]}")

    def write(capability, parameters):
        key = key_for(capability, parameters)
        first = core._cli(client, alias, run_id, capability, parameters, key=key)
        second = core._cli(client, alias, run_id, capability, parameters, key=key)
        assert not first["idempotent_replay"] and second["idempotent_replay"]
        assert second["result"] == first["result"]
        result = first["result"]
        for item in result.get("items", [result]):
            if item["model"] == "account.move":
                track(env["account.move"].browse(item["id"]))
        client.tracked["account.move.reversal"].update(
            admin["account.move.reversal"].search([("reason", "ilike", marker)]).ids)
        return result

    def denied(capability, parameters, error, code):
        response = settlement.workflows._call(client, alias, run_id, capability, parameters,
                                             key=key_for(capability, parameters), exit_code=code)
        assert response["error"]["code"] == error, response

    def inspect(move):
        result = core._cli(client, alias, run_id, "invoice.get", {"invoice_id": move.id})
        for key in ("amount_untaxed", "amount_tax", "amount_total"):
            assert Decimal(result[key]) == Decimal(str(move[key]))
        for row in result["lines"]:
            native = move.invoice_line_ids.filtered(lambda line, row_id=row["id"]: line.id == row_id)
            assert len(native) == 1
            assert row["product_uom_id"] == (native.product_uom_id.id or None)
            assert Decimal(row["deductible_amount"]) == Decimal(str(native.deductible_amount))
            for key in ("quantity", "price_unit", "price_subtotal", "price_total"):
                assert Decimal(row[key]) == Decimal(str(native[key]))
        return result

    journals = {}
    for side, label, account in (("sale", "S", ids["income"]), ("purchase", "P", ids["expense"])):
        journals[side] = fixture("account.journal", {"name": marker + side, "code": label + run_id.hex[:4],
                                "type": side, "company_id": 1, "default_account_id": account})
    base = admin.ref("uom.product_uom_unit")
    alternate = fixture("uom.uom", {"name": marker + "pack-six", "relative_uom_id": base.id, "relative_factor": 6})
    disallowed = fixture("uom.uom", {"name": marker + "pack-four", "relative_uom_id": base.id, "relative_factor": 4})
    category = fixture("product.category", {"name": marker + "category", "property_account_income_categ_id": ids["income"],
                                           "property_account_expense_categ_id": ids["expense"]})
    product = fixture("product.product", {"name": marker + "service", "type": "service", "company_id": 1,
        "categ_id": category.id, "uom_id": base.id, "uom_ids": [Command.set(alternate.ids)],
        "taxes_id": [Command.clear()], "supplier_taxes_id": [Command.clear()]})
    tax = fixture("account.tax", {"name": marker + "purchase-tax", "company_id": 1,
                                 "type_tax_use": "purchase", "amount_type": "percent", "amount": 15})

    def line(label, vendor=False, **extras):
        return {"name": marker + label, "product_id": product.id,
                "account_id": ids["expense" if vendor else "income"], "quantity": "2",
                "price_unit": "12", "discount": "0", "tax_ids": [tax.id] if vendor else [], **extras}

    def document(label, vendor=False, *, explicit=True):
        capability = "vendor_bill.create" if vendor else "customer_invoice.create"
        params = {"partner_id": ids["supplier" if vendor else "customer"],
                  "journal_id": journals["purchase" if vendor else "sale"].id,
                  "date": today, "invoice_date": today, "currency_id": ids["currency"],
                  "reference": marker + label,
                  "lines": [line(label, vendor, **({"product_uom_id": alternate.id,
                              "deductible_amount": "50.0" if vendor else "100.00"} if explicit else {}))]}
        move = env["account.move"].browse(write(capability, params)["id"])
        inspect(move)
        business = move.invoice_line_ids.filtered(lambda item: item.display_type == "product")
        assert business.quantity == 2 and business.price_unit == 12
        assert business.product_uom_id.id == (alternate.id if explicit else base.id)
        assert business.deductible_amount == (50 if vendor and explicit else 100)
        return move, params

    sale, _ = document("sale")
    bill, _ = document("bill", True)
    assert bill.line_ids.filtered(lambda item: item.display_type == "non_deductible_product")
    # Native tax sync must stay balanced; no client-side amount/UoM conversion.
    assert env.company.currency_id.is_zero(sum(bill.line_ids.mapped("balance")))
    assert bill.line_ids.filtered(lambda item: item.display_type == "tax")
    legacy, legacy_params = document("legacy", explicit=False)
    legacy_line = legacy.invoice_line_ids
    write("invoice.line.update", {"move_id": legacy.id, "line_id": legacy_line.id,
          "changes": {"product_uom_id": alternate.id}})
    inspect(legacy)
    # Native unit changes can reprice; restore the old explicitly
    # requested price before proving only omitted new fields do not bind replay.
    write("invoice.line.update", {"move_id": legacy.id, "line_id": legacy_line.id, "changes": {"price_unit": "12"}})
    replay = core._cli(client, alias, run_id, "customer_invoice.create", legacy_params,
                       key=key_for("customer_invoice.create", legacy_params))
    assert replay["idempotent_replay"] and legacy_line.product_uom_id.id == alternate.id

    original_bill_line = bill.invoice_line_ids
    added = line("added", True, product_uom_id=base.id, deductible_amount="25", quantity="1", price_unit="9")
    result = write("invoice.line.create", {"move_id": bill.id, "line": added})
    added_line = env["account.move.line"].browse(result["source_id"])
    assert added_line.move_id == bill and added_line.product_uom_id == base and added_line.deductible_amount == 25
    neighbor = original_bill_line.read(["id", "quantity", "price_unit", "product_uom_id", "deductible_amount"])
    write("invoice.line.update", {"move_id": bill.id, "line_id": added_line.id,
          "changes": {"product_uom_id": alternate.id, "quantity": "3", "price_unit": "11", "deductible_amount": "0"}})
    assert added_line.product_uom_id == alternate and added_line.quantity == 3 and added_line.deductible_amount == 0
    assert original_bill_line.read(["id", "quantity", "price_unit", "product_uom_id", "deductible_amount"]) == neighbor
    inspect(bill)
    before = bill.invoice_line_ids.read(["id", "quantity", "product_uom_id", "deductible_amount"])
    denied("invoice.line.update", {"move_id": bill.id, "line_id": added_line.id,
           "changes": {"product_uom_id": disallowed.id}}, "business_rule_error", 6)
    assert bill.invoice_line_ids.read(["id", "quantity", "product_uom_id", "deductible_amount"]) == before
    denied("invoice.line.update", {"move_id": sale.id, "line_id": sale.invoice_line_ids.id,
           "changes": {"deductible_amount": "50"}}, "business_rule_error", 6)
    denied("invoice.line.update", {"move_id": sale.id, "line_id": added_line.id,
           "changes": {"product_uom_id": base.id}}, "record_not_found", 4)
    replacement = line("replacement", True, product_uom_id=alternate.id, deductible_amount="100", quantity="4")
    write("invoice.lines.replace", {"move_id": bill.id, "lines": [replacement]})
    assert len(bill.invoice_line_ids) == 1 and bill.invoice_line_ids.id != added_line.id
    assert bill.invoice_line_ids.product_uom_id == alternate and bill.invoice_line_ids.deductible_amount == 100
    assert not bill.line_ids.filtered(lambda item: item.display_type.startswith("non_deductible"))
    inspect(bill)
    for source, vendor, capability in ((sale, False, "customer_credit_note.create"), (bill, True, "vendor_refund.create")):
        write("invoice.post", {"move_id": source.id})
        denied("invoice.line.update", {"move_id": source.id, "line_id": source.invoice_line_ids.id,
               "changes": {"product_uom_id": base.id}}, "state_conflict", 5)
        source_graph = settlement.maintenance._graph(source)
        custom = line("refund" + capability, vendor, product_uom_id=base.id,
                      deductible_amount="50.001" if vendor else "100", quantity="1", price_unit="10")
        result = write(capability, {"move_id": source.id, "date": today, "reason": marker + capability, "lines": [custom]})
        refund = env["account.move"].browse(result["id"])
        assert refund.move_type == ("in_refund" if vendor else "out_refund") and refund.state == "draft"
        assert refund.invoice_line_ids.product_uom_id == base
        assert Decimal(str(refund.invoice_line_ids.deductible_amount)) == Decimal(custom["deductible_amount"])
        inspect(refund)
        assert settlement.maintenance._graph(source) == source_graph

    # Foreign product input checked after all successful native business calls.
    foreign = fixture("product.product", {"name": marker + "foreign", "type": "service", "company_id": 2,
                      "categ_id": category.id, "uom_id": base.id}, company=2)
    denied("invoice.line.update", {"move_id": legacy.id, "line_id": legacy_line.id,
           "changes": {"product_id": foreign.id, "product_uom_id": base.id}}, "record_not_found", 4)
    assert _TARGETS <= client.capabilities


def _live_worker():
    settlement._MODELS, settlement._exercise, settlement._summary = _MODELS, _exercise, _summary
    return settlement._live_worker()


if __name__ == "__main__":
    raise SystemExit(_live_worker())
