"""One rollback-only public CLI workflow for invoice preparation and product lookups."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import sysconfig
import uuid
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import test_document_lifecycle_write_batch_live as lifecycle
import test_journal_item_processing_batch_live as line_batch
import test_payment_bank_capability_batch_live as core

try:
    import pytest
except ModuleNotFoundError:
    if "--live-worker" not in sys.argv:
        raise
    pytest = None

_ALLOW_ENV = "ODACV4_ALLOW_INVOICE_PREPARATION_SMOKE"
_WRITES = {"invoice.service_dates.update", "invoice.tax_totals.adjust"}
_READS = {"invoice.service_dates.get", "invoice.alerts.inspect", "accounting_move.origin_links.inspect",
          "product.category.accounting_profile.get", "product.tax_profile.get", "product.accounts.resolve"}
_SETUP = {"customer_invoice.create", "vendor_bill.create", "invoice.post", "customer_credit_note.create"}
_MODELS = ("account.move", "account.move.line", "account.tax", "account.tax.repartition.line", "account.tax.group",
           "account.account", "account.account.tag", "account.fiscal.position", "account.fiscal.position.account",
           "product.product", "product.template", "product.category")


def _root():
    return Path(__file__).resolve().parents[2]


def _summary(alias, database):
    return {"alias": alias, "database": database, "company_id": 1, "user_id": 5, "business_su": False,
            "capabilities": sorted(_WRITES | _READS | _SETUP), "immediate_replays": 4,
            "native_service_dates_set_clear_and_replay_verified": True,
            "native_zero_purchase_line_warning_sanitization_verified": True,
            "native_reversal_and_direct_fixture_cashbasis_adjusting_relations_verified": True,
            "native_category_product_company_fallback_and_fiscal_mapping_verified": True,
            "product_current_company_taxes_and_product_tags_verified": True,
            "sale_purchase_existing_tax_group_minor_unit_inverse_and_replay_verified": True,
            "balance_payment_term_and_other_tax_line_preservation_verified": True,
            "posted_missing_foreign_and_invalid_tax_target_denials_verified": True,
            "rollback_verified": True, "all_user_groups_unchanged": True,
            "company_settings_and_defaults_rollback_verified": True, "execution": "in_process_cli_real_orm"}


if pytest is not None:
    @pytest.mark.integration
    def test_invoice_preparation_rolls_back_per_alias():
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


def _settings(env):
    from odoo_accounting_cli_v4.company_processing_contracts import SETTING_FIELDS

    return env["res.company"].with_context(allowed_company_ids=[1, 2]).browse([1, 2]).read(list(SETTING_FIELDS))


def _defaults(env):
    return env["ir.default"].search([], order="id").read(["id", "field_id", "user_id", "company_id", "condition", "json_value"])


def _exercise(admin, client, alias, run_id, marker):
    from odoo import Command, fields

    from odoo_accounting_cli_v4 import invoice_preparation_contracts as contracts
    from odoo_accounting_cli_v4.capabilities.core_writes import (
        _expected_idempotency_key,
        validate_core_write_request,
    )

    env, ids, replays = client.env, lifecycle._fixture_ids(admin, alias), 0
    today = fields.Date.context_today(env.user)

    def track(record):
        client.tracked[record._name].update(record.ids)
        children = {"account.move": "line_ids", "account.tax": "repartition_line_ids", "account.fiscal.position": "account_ids", "product.product": "product_tmpl_id"}
        if record._name in children:
            child = record[children[record._name]]
            client.tracked[child._name].update(child.ids)
        return record

    def fixture(model, values, *, company=1):
        return track(admin[model].with_company(admin["res.company"].browse(company)).create(values))

    def read(capability, params):
        item = line_batch._read(client, alias, run_id, capability, params)
        assert contracts.valid_read_item(capability, item, 1), item
        return item

    def write(capability, params, *, replay=False):
        nonlocal replays
        normalized = validate_core_write_request(capability, core._request(alias, run_id, capability, params))[2]
        key = _expected_idempotency_key(capability, normalized, 1) or f"{capability}:{run_id.hex}:{lifecycle._canonical_digest(normalized)[:32]}"
        client.last_runtime_failure = None
        first = core._cli(client, alias, run_id, capability, params, key=key)
        assert first["idempotent_replay"] is False
        value = first["result"]
        track(env[value["model"]].browse(value["id"]))
        if replay:
            second = core._cli(client, alias, run_id, capability, params, key=key)
            assert second["idempotent_replay"] and second["result"] == value
            replays += 1
        return value

    category = fixture("product.category", {"name": marker + "category", "property_account_income_categ_id": ids["income"], "property_account_expense_categ_id": ids["expense"]})
    group = fixture("account.tax.group", {"name": marker + "tax-group", "company_id": 1})
    taxes = {kind: [fixture("account.tax", {"name": marker + kind + str(amount), "company_id": 1, "type_tax_use": kind,
              "amount_type": "percent", "amount": amount, "price_include_override": "tax_excluded", "tax_group_id": group.id}) for amount in (10, 5)] for kind in ("sale", "purchase")}
    foreign_group = fixture("account.tax.group", {"name": marker + "foreign-group", "company_id": 2}, company=2)
    foreign_taxes = {kind: fixture("account.tax", {"name": marker + "foreign-" + kind, "company_id": 2, "type_tax_use": kind,
                    "amount": 17, "tax_group_id": foreign_group.id}, company=2) for kind in ("sale", "purchase")}
    tag = fixture("account.account.tag", {"name": marker + "product-tag", "applicability": "products"})
    product = fixture("product.product", {"name": marker + "product", "type": "consu", "company_id": False, "categ_id": category.id,
        "property_account_income_id": False, "property_account_expense_id": False, "uom_id": admin.ref("uom.product_uom_unit").id,
        "taxes_id": [Command.set([tax.id for tax in taxes["sale"]] + foreign_taxes["sale"].ids)],
        "supplier_taxes_id": [Command.set([tax.id for tax in taxes["purchase"]] + foreign_taxes["purchase"].ids)], "account_tag_ids": [Command.set(tag.ids)]})
    product = env["product.product"].browse(product.id)
    alt_accounts = {kind: fixture("account.account", {"name": marker + kind, "code": "I" + kind[:1] + run_id.hex[:7], "account_type": kind,
                    "company_ids": [Command.set([1])]}) for kind in ("income", "expense")}
    position = fixture("account.fiscal.position", {"name": marker + "position", "company_id": 1, "account_ids": [
        Command.create({"account_src_id": ids[kind], "account_dest_id": alt_accounts[kind].id}) for kind in ("income", "expense")]})
    foreign_position = fixture("account.fiscal.position", {"name": marker + "foreign-position", "company_id": 2}, company=2)
    category_item = read(contracts.CATEGORY_ID, {"category_id": category.id})
    assert (category_item["income_account_id"], category_item["expense_account_id"]) == (ids["income"], ids["expense"])
    assert category_item["company_income_account_id"] == (env.company.income_account_id.id or None)
    assert category_item["company_expense_account_id"] == (env.company.expense_account_id.id or None)
    profile = read(contracts.TAX_PROFILE_ID, {"product_id": product.id})
    assert profile["sale_tax_ids"] == sorted(tax.id for tax in taxes["sale"])
    assert profile["purchase_tax_ids"] == sorted(tax.id for tax in taxes["purchase"]) and profile["account_tag_ids"] == tag.ids

    def accounts(position_id=None):
        item = read(contracts.ACCOUNTS_ID, {"product_id": product.id, "fiscal_position_id": position_id})
        native = product.product_tmpl_id.get_product_accounts(fiscal_pos=env["account.fiscal.position"].browse(position_id or []))
        for key, target in (("income", "income_account_id"), ("expense", "expense_account_id"), ("stock_valuation", "stock_valuation_account_id"), ("stock_variation", "stock_variation_account_id"), ("stock_journal", "stock_journal_id")):
            assert item[target] == (native[key].id if native.get(key) else None)
        return item

    resolved, mapped = accounts(), accounts(position.id)
    assert (resolved["income_account_id"], resolved["expense_account_id"]) == (ids["income"], ids["expense"])
    assert (mapped["income_account_id"], mapped["expense_account_id"]) == (alt_accounts["income"].id, alt_accounts["expense"].id)
    admin["product.product"].browse(product.id).write({"property_account_income_id": alt_accounts["income"].id})
    assert accounts()["income_account_id"] == alt_accounts["income"].id
    admin["product.product"].browse(product.id).write({"property_account_income_id": False})
    # Category getters include ir.default; force this fallback prerequisite only
    # inside the isolated transaction, then verify the entire defaults rollback.
    for field in ("property_account_income_categ_id", "property_account_expense_categ_id"):
        admin["ir.default"].set("product.category", field, False, company_id=1)
    admin["product.category"].browse(category.id).write({"property_account_income_categ_id": False, "property_account_expense_categ_id": False})
    company_fallback = accounts()
    assert (company_fallback["income_account_id"], company_fallback["expense_account_id"]) == (env.company.income_account_id.id or None, env.company.expense_account_id.id or None)

    def document(capability, *, zero=False):
        supplier = capability == "vendor_bill.create"
        rows = [{"name": marker + capability, "account_id": ids["expense" if supplier else "income"], "quantity": "1", "price_unit": "101.01",
                 "tax_ids": [tax.id for tax in taxes["purchase" if supplier else "sale"]]}]
        if zero:
            rows = [{**rows[0], "name": marker + str(index), "quantity": "1", "price_unit": "0"} for index in (1, 2)]
        value = write(capability, {"partner_id": ids["supplier" if supplier else "customer"], "journal_id": ids["purchase_journal" if supplier else "sale_journal"],
            "date": today.isoformat(), "invoice_date": today.isoformat(), "currency_id": ids["currency"], "lines": rows})
        return env["account.move"].browse(value["id"])

    invoice, bill = document("customer_invoice.create"), document("vendor_bill.create")
    changes = {"delivery_date": (today - timedelta(days=1)).isoformat(), "taxable_supply_date": today.isoformat()}
    write("invoice.service_dates.update", {"move_id": invoice.id, "changes": changes}, replay=True)
    dates = read(contracts.DATES_ID, {"move_id": invoice.id})
    assert all(dates[key] == value for key, value in changes.items())
    assert all(dates[key] == (invoice[key].isoformat() if invoice[key] else None) for key in contracts.DATE_FIELDS)
    write("invoice.service_dates.update", {"move_id": invoice.id, "changes": {key: None for key in changes}}, replay=True)
    cleared = read(contracts.DATES_ID, {"move_id": invoice.id})
    assert cleared["delivery_date"] is None and cleared["taxable_supply_date"] is None
    zero_bill = document("vendor_bill.create", zero=True)
    raw_alerts, alert_item = zero_bill._get_alerts(), read(contracts.ALERTS_ID, {"move_id": zero_bill.id})
    assert "account_remove_empty_lines" in raw_alerts and "action_call" in raw_alerts["account_remove_empty_lines"]
    assert alert_item["alerts"] == [{"key": key, "level": raw_alerts[key]["level"], "message": raw_alerts[key]["message"], "action_label": raw_alerts[key].get("action_text") or None} for key in sorted(raw_alerts)]
    assert all(set(value) == {"key", "level", "message", "action_label"} for value in alert_item["alerts"])
    assert len(zero_bill.invoice_line_ids) == 2 and all(line.price_total == 0 for line in zero_bill.invoice_line_ids)

    def tax_groups(move):
        return {value["id"]: value for subtotal in move.tax_totals["subtotals"] for value in subtotal["tax_groups"]}

    monetary_fields = ["id", "account_id", "balance", "amount_currency", "debit", "credit", "date_maturity", "tax_line_id", "tax_repartition_line_id"]
    for move in (invoice, bill):
        old = tax_groups(move)[group.id]
        wanted = Decimal(str(move.currency_id.round(float(Decimal(str(old["tax_amount_currency"])) + Decimal(str(move.currency_id.rounding))))))
        canonical = format(wanted, "f").rstrip("0").rstrip(".") if "." in format(wanted, "f") else format(wanted, "f")
        original_ids, original_lines = set(move.line_ids.ids), move.invoice_line_ids.read(monetary_fields)
        tax_lines = move.line_ids.filtered(lambda line: line.tax_group_id.id == group.id)
        assert len(tax_lines) == 2
        untouched = tax_lines[1:].read(monetary_fields)
        write("invoice.tax_totals.adjust", {"move_id": move.id, "groups": [{"tax_group_id": group.id, "tax_amount": canonical}]}, replay=True)
        assert Decimal(str(move.currency_id.round(tax_groups(move)[group.id]["tax_amount_currency"]))) == wanted
        assert set(move.line_ids.ids) == original_ids and move.invoice_line_ids.read(monetary_fields) == original_lines
        assert tax_lines[1:].read(monetary_fields) == untouched
        assert move.currency_id.is_zero(sum(move.line_ids.mapped("balance")))
        term = move.line_ids.filtered(lambda line: line.display_type == "payment_term")
        others = move.line_ids - term
        assert len(term) == 1 and move.currency_id.is_zero(term.balance + sum(others.mapped("balance")))
        denied_snapshot = move.line_ids.read(monetary_fields)
        line_batch._denied(client, alias, run_id, "invoice.tax_totals.adjust", {"move_id": move.id, "groups": [{"tax_group_id": foreign_group.id, "tax_amount": canonical}]}, "business_rule_error", 6)
        assert move.line_ids.read(monetary_fields) == denied_snapshot

    write("invoice.post", {"move_id": invoice.id})
    refund = env["account.move"].browse(write("customer_credit_note.create", {"move_id": invoice.id, "date": today.isoformat(), "reason": marker})["id"])
    linked = fixture("account.move", {"move_type": "entry", "journal_id": ids["general_journal"], "date": today,
        "ref": marker + "direct-links", "tax_cash_basis_origin_move_id": invoice.id, "adjusting_entry_origin_move_ids": [Command.set(invoice.ids)]})
    origin = read(contracts.ORIGINS_ID, {"move_id": invoice.id})
    linked_origin = read(contracts.ORIGINS_ID, {"move_id": linked.id})
    refund_origin = read(contracts.ORIGINS_ID, {"move_id": refund.id})
    assert refund_origin["reversed_entry"]["id"] == invoice.id and refund.id in {row["id"] for row in origin["reversal_moves"]}
    assert linked.id in {row["id"] for row in origin["tax_cash_basis_created_moves"]}
    assert linked.id in {row["id"] for row in origin["adjusting_entries_moves"]}
    assert linked_origin["tax_cash_basis_origin_move"]["id"] == invoice.id
    assert invoice.id in {row["id"] for row in linked_origin["adjusting_entry_origin_moves"]}
    posted_before = invoice.line_ids.read(monetary_fields)
    for capability, params in (("invoice.service_dates.update", {"move_id": invoice.id, "changes": {"delivery_date": today.isoformat()}}),
                               ("invoice.tax_totals.adjust", {"move_id": invoice.id, "groups": [{"tax_group_id": group.id, "tax_amount": canonical}]})):
        line_batch._denied(client, alias, run_id, capability, params, "state_conflict", 6)
    assert invoice.line_ids.read(monetary_fields) == posted_before
    foreign = fixture("account.move", {"move_type": "out_invoice", "date": today, "ref": marker + "foreign"}, company=2)
    foreign_product = fixture("product.product", {"name": marker + "foreign-product", "company_id": 2, "type": "consu"}, company=2)
    for capability in _READS:
        field = contracts.ID_FIELDS[capability]
        params = {field: 2147483647}
        if capability == contracts.ACCOUNTS_ID:
            params["fiscal_position_id"] = None
        line_batch._read(client, alias, run_id, capability, params, exit_code=4)
        if field != "category_id":
            params[field] = foreign_product.id if field == "product_id" else foreign.id
            line_batch._read(client, alias, run_id, capability, params, exit_code=4)
    line_batch._read(client, alias, run_id, contracts.ACCOUNTS_ID, {"product_id": product.id, "fiscal_position_id": foreign_position.id}, exit_code=4)
    line_batch._denied(client, alias, run_id, "invoice.service_dates.update", {"move_id": foreign.id, "changes": {"delivery_date": None}}, "record_not_found", 4)
    assert replays == 4 and client.capabilities == _WRITES | _READS | _SETUP


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
    cursor, marker = registry.cursor(), f"ODACV4-INVPREP-{args.alias}-{args.run_id.hex}"
    tracked, groups, settings, defaults, failure = {}, None, None, None, None
    try:
        context = {"allowed_company_ids": [1], "lang": "en_US", "tz": "Asia/Shanghai", "tracking_disable": True, "mail_create_nosubscribe": True, "mail_notrack": True}
        admin = api.Environment(cursor, SUPERUSER_ID, context)
        user = admin["res.users"].browse(5).exists()
        assert user.active and user.login == lifecycle._USER_LOGIN and user.has_group("account.group_account_user")
        groups, settings, defaults = sorted(user.group_ids.ids), _settings(admin), _defaults(admin)
        client = line_batch._Client(api.Environment(cursor, 5, context))
        assert not client.env.su and client.env.company.id == 1
        client.tracked = {model: set() for model in _MODELS}
        tracked = client.tracked
        _exercise(admin, client, args.alias, args.run_id, marker)
        assert sorted(user.group_ids.ids) == groups
    except BaseException as exc:  # noqa: BLE001 - synthetic fixtures roll back even on failure.
        failure = exc
    finally:
        cursor.rollback()
        cursor.close()
    with registry.cursor() as verify_cursor:
        try:
            verify = api.Environment(verify_cursor, SUPERUSER_ID, {"allowed_company_ids": [1, 2], "lang": "en_US"})
            for model, ids in tracked.items():
                assert not verify[model].with_context(active_test=False).search_count([("id", "in", sorted(ids))])
            for model in ("account.tax", "account.tax.group", "account.account", "account.account.tag", "account.fiscal.position", "product.template", "product.category"):
                assert not verify[model].with_context(active_test=False).search_count([("name", "ilike", marker)])
            assert not verify["account.move"].search_count([("ref", "ilike", marker)])
            assert not verify["account.move.line"].search_count([("name", "ilike", marker)])
            if groups is not None:
                assert sorted(verify["res.users"].browse(5).group_ids.ids) == groups
                assert _settings(verify) == settings and _defaults(verify) == defaults
        finally:
            verify_cursor.rollback()
    if failure is not None:
        raise failure
    print(json.dumps(_summary(args.alias, args.database), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_live_worker())
