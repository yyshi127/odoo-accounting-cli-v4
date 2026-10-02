"""One current-company CLI/real-ORM workflow, including existing-row rollback."""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import sysconfig
import uuid
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

_ALLOW_ENV = "ODACV4_ALLOW_COMPANY_PROCESSING_SMOKE"
_GROUP = "base.group_erp_manager"
_WRITES = {
    "company.fiscal_year_end.update", "company.tax_policy.update",
    "company.cash_discount_accounts.assign", "company.exchange_configuration.update",
    "company.invoice_display.update", "company.credit_policy.update",
    "company.bill_processing_policy.update",
}
_READS = {"company.processing_settings.get"}
_SETUP = {"journal_entry.create", "journal_entry.post"}
_MODELS = (
    "account.move", "account.move.line", "account.account", "account.tax",
    "account.tax.repartition.line", "account.journal", "mail.alias",
    "account.payment.method.line",
)


def _root():
    return Path(__file__).resolve().parents[2]


def _summary(alias, database):
    return {
        "alias": alias, "database": database, "company_id": 1, "user_id": 5,
        "business_su": False, "capabilities": sorted(_WRITES | _READS | _SETUP),
        "immediate_replays": 15, "company_setting_replays": 14,
        "native_company_acl_denial_before_temporary_erp_group_verified": True,
        "native_fiscal_year_february_29_and_invalid_april_31_verified": True,
        "native_tax_price_method_existing_accounting_guard_verified": True,
        "all_seven_native_company_writes_and_serial_replays_verified": True,
        "typed_current_company_read_null_clearing_and_quick_edit_choices_verified": True,
        "foreign_missing_and_incompatible_journal_references_rejected": True,
        "native_category_default_values_verified": True,
        "other_company_and_non_target_settings_unchanged": True,
        "posted_entry_unchanged_by_configuration": True,
        "existing_company_settings_and_defaults_rollback_verified": True,
        "rollback_verified": True, "temporary_groups_rolled_back": True,
        "execution": "in_process_cli_real_orm",
    }


if pytest is not None:
    @pytest.mark.integration
    def test_company_processing_rolls_back_per_alias():
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
            completed = subprocess.run(
                command, cwd=_root(), env=environment, text=True, capture_output=True,
                check=False, timeout=max(timeout, 900),
            )
            assert completed.returncode == 0, completed.stdout + completed.stderr
            assert json.loads(completed.stdout) == _summary(alias, lifecycle._DATABASES[alias])
            print(completed.stdout.strip(), flush=True)


def _denied(client, alias, run_id, capability, parameters, expected_code, exit_code, *, native_validation=False):
    from odoo_accounting_cli_v4 import cli
    from odoo_accounting_cli_v4.bridge.core_writes import OdooCoreWritePort
    from odoo_accounting_cli_v4.capabilities.core_writes import (
        _expected_idempotency_key,
        validate_core_write_request,
    )

    request = core._request(alias, run_id, capability, parameters)
    normalized = validate_core_write_request(capability, request)[2]
    key = _expected_idempotency_key(capability, normalized, 1)
    assert key is not None
    assert client.env.uid == 5 and not client.env.su and client.env.company.id == 1
    stdout, stderr = io.StringIO(), io.StringIO()
    client.last_runtime_failure = None
    result = cli.main(
        ["write", "run", capability, "--request", "-", "--idempotency-key", key, "--confirm", capability],
        stdin=io.StringIO(json.dumps(request)), stdout=stdout, stderr=stderr,
        port_factory=lambda *args: OdooCoreWritePort(client),
    )
    response = json.loads(stdout.getvalue())
    assert result == exit_code and not stderr.getvalue(), response
    assert response["success"] is False and response["error"]["code"] == expected_code, response
    bindings = {field: response["odoo"][field] for field in ("database", "company_id", "user_id", "model")}
    if client.last_runtime_failure is None:
        # A denied gate returns a validated page, so the port has verified its user.
        assert expected_code == "unauthorized"
        assert bindings == {"database": alias, "company_id": 1, "user_id": 5, "model": "res.company"}
    else:
        # BridgeError arrives before a page; the CLI must not invent verified identity metadata.
        assert client.last_runtime_failure.code == expected_code
        assert bindings == {field: None for field in bindings}
    if native_validation:
        failure = client.last_runtime_failure
        assert failure is not None and failure.code == "business_rule_error"
        assert type(failure.__cause__).__name__ == "ValidationError"


def _company_snapshot(env, fields):
    return env["res.company"].with_context(allowed_company_ids=[1, 2]).browse([1, 2]).read(fields)


def _default_snapshot(env):
    return env["ir.default"].search([], order="id").read(
        ["id", "field_id", "user_id", "company_id", "condition", "json_value"]
    )


def _exercise(admin, client, alias, run_id, marker, fields, baseline_company):
    from odoo import Command

    from odoo_accounting_cli_v4 import company_processing_contracts as contracts
    from odoo_accounting_cli_v4.bridge.core_writes_runtime import (
        _company_processing_values,
    )
    from odoo_accounting_cli_v4.capabilities.core_writes import (
        _expected_idempotency_key,
        validate_core_write_request,
    )

    env = client.env
    ids = lifecycle._fixture_ids(admin, alias)
    company = env["res.company"].browse(1)
    assert not company.parent_id and not admin["res.company"].browse(2).parent_id
    initial = _company_processing_values(company)
    replays = 0
    existing_accounts = set(admin["account.account"].with_context(active_test=False).search([]).ids)

    def track(record):
        client.tracked[record._name].update(record.ids)
        if record._name == "account.move":
            client.tracked["account.move.line"].update(record.line_ids.ids)
        elif record._name == "account.tax":
            client.tracked["account.tax.repartition.line"].update(
                (record.invoice_repartition_line_ids | record.refund_repartition_line_ids).ids
            )
        elif record._name == "account.journal":
            for field in ("alias_id", "default_account_id", "inbound_payment_method_line_ids", "outbound_payment_method_line_ids"):
                child = record[field]
                child_ids = set(child.ids)
                if child._name == "account.account":
                    child_ids -= existing_accounts
                client.tracked[child._name].update(child_ids)
        return record

    def write(capability, parameters, *, replay=True):
        nonlocal replays
        request = core._request(alias, run_id, capability, parameters)
        normalized = validate_core_write_request(capability, request)[2]
        key = _expected_idempotency_key(capability, normalized, 1)
        if key is None:
            assert capability == "journal_entry.create"
            key = f"{capability}:{run_id.hex}:{lifecycle._canonical_digest(normalized)[:32]}"
        first = core._cli(client, alias, run_id, capability, parameters, key=key)
        assert first["idempotent_replay"] is False
        if replay:
            second = core._cli(client, alias, run_id, capability, parameters, key=key)
            assert second["idempotent_replay"] is True and second["result"] == first["result"]
            replays += 1
        value = first["result"]
        if capability in _SETUP:
            track(env[value["model"]].browse(value["id"]))
        else:
            assert value["model"] == "res.company" and value["id"] == value["company_id"] == 1
            actual = _company_processing_values(company)
            assert all(actual[field] == wanted for field, wanted in parameters["changes"].items())
        return value

    def read():
        value = shared._read(client, alias, run_id, contracts.GET_ID, {})
        assert contracts.valid_read_item(value, 1)
        assert {field: value[field] for field in contracts.SETTING_FIELDS} == _company_processing_values(company)
        return value

    assert read() == {"id": 1, "company_id": 1, **initial}
    entry = write("journal_entry.create", {
        "journal_id": ids["general_journal"], "date": "2026-10-02", "reference": marker,
        "lines": [
            {"name": marker + "debit", "account_id": ids["expense"], "debit": "20", "credit": "0", "partner_id": None},
            {"name": marker + "credit", "account_id": ids["income"], "debit": "0", "credit": "20", "partner_id": None},
        ],
    }, replay=False)
    move = env["account.move"].browse(entry["id"])
    write("journal_entry.post", {"move_id": move.id})
    line_fields = ["id", "account_id", "journal_id", "date_maturity", "balance", "amount_currency", "amount_residual", "tax_ids"]

    def posted():
        return (move.id, move.name, move.state, move.journal_id.id, move.line_ids.read(line_fields))

    posted_before = posted()
    assert move.state == "posted" and company._existing_accounting()
    protected = [field for field in fields if field not in contracts.SETTING_FIELDS]
    protected_before = _company_snapshot(admin, protected)
    rounding = "round_per_line" if initial["tax_calculation_rounding_method"] == "round_globally" else "round_globally"

    # Price-inclusion constraint is native, and a failing multi-field write must be atomic.
    price = "tax_included" if initial["account_price_include"] == "tax_excluded" else "tax_excluded"
    _denied(client, alias, run_id, "company.tax_policy.update", {"changes": {
        "account_price_include": price, "tax_calculation_rounding_method": rounding,
    }}, "business_rule_error", 6, native_validation=True)
    assert read() == {"id": 1, "company_id": 1, **initial}
    _denied(client, alias, run_id, "company.fiscal_year_end.update", {"changes": {
        "fiscalyear_last_month": "4", "fiscalyear_last_day": 31,
    }}, "business_rule_error", 6, native_validation=True)
    assert read() == {"id": 1, "company_id": 1, **initial}

    write("company.fiscal_year_end.update", {"changes": {"fiscalyear_last_month": "6", "fiscalyear_last_day": 30}})
    write("company.fiscal_year_end.update", {"changes": {"fiscalyear_last_month": "2", "fiscalyear_last_day": 29}})
    write("company.tax_policy.update", {"changes": {
        "tax_calculation_rounding_method": rounding,
        "account_sale_tax_id": initial["account_sale_tax_id"], "account_purchase_tax_id": initial["account_purchase_tax_id"],
    }})
    assert initial["account_sale_tax_id"] is not None and initial["account_purchase_tax_id"] is not None
    write("company.tax_policy.update", {"changes": {"account_sale_tax_id": None, "account_purchase_tax_id": None}})
    write("company.cash_discount_accounts.assign", {"changes": {
        "account_journal_early_pay_discount_gain_account_id": ids["income"],
        "account_journal_early_pay_discount_loss_account_id": ids["expense"],
    }})
    write("company.cash_discount_accounts.assign", {"changes": {
        "account_journal_early_pay_discount_gain_account_id": None, "account_journal_early_pay_discount_loss_account_id": None,
    }})
    write("company.exchange_configuration.update", {"changes": {
        "currency_exchange_journal_id": ids["general_journal"],
        "income_currency_exchange_account_id": ids["income"], "expense_currency_exchange_account_id": ids["expense"],
    }})
    write("company.exchange_configuration.update", {"changes": {
        "currency_exchange_journal_id": None, "income_currency_exchange_account_id": None, "expense_currency_exchange_account_id": None,
    }})
    write("company.invoice_display.update", {"changes": {
        field: not initial[field] for field in contracts.FIELD_GROUPS["company.invoice_display.update"]
    }})
    write("company.credit_policy.update", {"changes": {"account_use_credit_limit": not initial["account_use_credit_limit"]}})
    assert initial["quick_edit_mode"] is None
    for index, mode in enumerate(("out_invoices", "in_invoices", "out_and_in_invoices", None)):
        changes = {"quick_edit_mode": mode}
        if index == 0:
            changes["autopost_bills"] = not initial["autopost_bills"]
        write("company.bill_processing_policy.update", {"changes": changes})
        assert read()["quick_edit_mode"] == mode
    final = read()
    assert final["fiscalyear_last_month"] == "2" and final["fiscalyear_last_day"] == 29
    assert all(final[field] is None for field in contracts.RELATION_MODELS)
    assert final["account_price_include"] == initial["account_price_include"]
    assert _company_snapshot(admin, protected) == protected_before
    assert _company_snapshot(admin, fields)[1] == baseline_company[1]

    # Foreign fixtures are only transaction-local; companies themselves are existing targets, never "new" IDs.
    foreign_company = admin["res.company"].browse(2)
    foreign_account = track(admin["account.account"].with_company(foreign_company).create({
        "name": marker + "foreign-account", "code": "CP" + run_id.hex[:8],
        "account_type": "expense", "company_ids": [Command.set([2])],
    }))
    foreign_tax = track(admin["account.tax"].with_company(foreign_company).create({
        "name": marker + "foreign-tax", "amount": 15, "amount_type": "percent", "type_tax_use": "sale", "company_id": 2,
    }))
    foreign_journal = track(admin["account.journal"].with_company(foreign_company).create({
        "name": marker + "foreign-journal", "code": "C" + run_id.hex[:4], "type": "general", "company_id": 2,
    }))
    before_denials = _company_snapshot(admin, fields)
    foreign = {"account.account": foreign_account.id, "account.tax": foreign_tax.id, "account.journal": foreign_journal.id}
    for field, model in contracts.RELATION_MODELS.items():
        capability = next(cap for cap, names in contracts.FIELD_GROUPS.items() if field in names)
        for value in (foreign[model], 2147483647):
            _denied(client, alias, run_id, capability, {"changes": {field: value}}, "record_not_found", 4)
    _denied(client, alias, run_id, "company.exchange_configuration.update", {"changes": {
        "currency_exchange_journal_id": ids["sale_journal"],
    }}, "record_not_found", 4)
    assert read() == final and posted() == posted_before
    assert _company_snapshot(admin, fields) == before_denials

    # res.company.write calls the native product-category default setter, not a wrapper substitute.
    for field, account in (
        ("property_account_expense_categ_id", company.expense_account_id),
        ("property_account_income_categ_id", company.income_account_id),
    ):
        rows = admin["ir.default"].search([
            ("field_id.model", "=", "product.category"), ("field_id.name", "=", field),
            ("company_id", "=", 1), ("user_id", "=", False), ("condition", "=", False),
        ])
        assert len(rows) == 1 and json.loads(rows.json_value) == account.id
    assert replays == 15 and client.capabilities == _WRITES | _READS | _SETUP


def _live_worker():
    args = lifecycle._arguments(None)
    assert not (args.refund_only or args.payment_difference_only or args.analytic_readback_only)
    sys.path.insert(0, str(args.odoo_source.resolve(strict=True)))
    sys.path.insert(0, str(_root() / "src"))
    from odoo import SUPERUSER_ID, Command, api
    from odoo.orm.registry import Registry
    from odoo.tools import config

    from odoo_accounting_cli_v4 import cli
    from odoo_accounting_cli_v4 import company_processing_contracts as contracts

    config.parse_config(["--config", str(args.odoo_config.resolve(strict=True)), "--database", args.database, "--no-http", "--logfile=/dev/null"])
    registry = Registry(args.database)
    # Cache the actual immutable registry once; CLI request/response validation and native ACLs remain real.
    actual_registry = cli.load_registry()
    cli.load_registry = lambda: actual_registry
    cursor = registry.cursor()
    marker = f"ODACV4-COMPROC-{args.alias}-{args.run_id.hex}"
    tracked, baseline_groups, baseline_company, baseline_defaults = {}, None, None, None
    group_id, baseline_direct, fields, failure = None, None, [], None
    try:
        context = {"allowed_company_ids": [1], "lang": "en_US", "tz": "Asia/Shanghai", "tracking_disable": True,
                   "mail_create_nosubscribe": True, "mail_notrack": True}
        admin = api.Environment(cursor, SUPERUSER_ID, context)
        user = admin["res.users"].browse(5).exists()
        assert user.active and user.login == lifecycle._USER_LOGIN and 1 in user.company_ids.ids
        assert user.has_group("account.group_account_user") and not user.has_group(_GROUP)
        group_id = admin.ref(_GROUP).id
        baseline_groups = sorted(user.group_ids.ids)
        baseline_direct = shared._direct_group(cursor, group_id)
        explicit = {
            "id", "parent_id", "currency_id", "chart_template", "bank_account_code_prefix", "cash_account_code_prefix",
            "transfer_account_code_prefix", "account_storno", "anglo_saxon_accounting", "tax_exigibility",
            "income_account_id", "expense_account_id", "account_opening_date", "account_opening_move_id",
        }
        fields = sorted(set(contracts.SETTING_FIELDS) | {
            name for name, field in admin["res.company"]._fields.items()
            if name in explicit or (field.store and ("lock" in name or "audit" in name))
        })
        baseline_company = _company_snapshot(admin, fields)
        baseline_defaults = _default_snapshot(admin)
        env = api.Environment(cursor, 5, context)
        assert not env.su and not env["res.company"].has_access("write")
        client = shared._Client(env)
        client.tracked = {model: set() for model in _MODELS}
        tracked = client.tracked
        ordinary_read = shared._read(client, args.alias, args.run_id, contracts.GET_ID, {})
        assert contracts.valid_read_item(ordinary_read, 1)
        _denied(client, args.alias, args.run_id, "company.credit_policy.update", {"changes": {
            "account_use_credit_limit": not env["res.company"].browse(1).account_use_credit_limit,
        }}, "unauthorized", 3)
        assert _company_snapshot(admin, fields) == baseline_company and _default_snapshot(admin) == baseline_defaults
        user.write({"group_ids": [Command.link(group_id)]})
        env = api.Environment(cursor, 5, context)
        assert not env.su and env.user.has_group(_GROUP) and env["res.company"].has_access("write")
        client.env = env
        _exercise(admin, client, args.alias, args.run_id, marker, fields, baseline_company)
    except BaseException as exc:  # noqa: BLE001 - existing and new rows must roll back on failure too.
        failure = exc
    finally:
        cursor.rollback()
        cursor.close()
    with registry.cursor() as verify_cursor:
        try:
            verify = api.Environment(verify_cursor, SUPERUSER_ID, {"allowed_company_ids": [1, 2], "lang": "en_US", "tz": "Asia/Shanghai"})
            for model, record_ids in tracked.items():
                assert not verify[model].with_context(active_test=False).search_count([("id", "in", sorted(record_ids))])
            for model in ("account.account", "account.tax", "account.journal"):
                assert not verify[model].with_context(active_test=False).search_count([("name", "ilike", marker)])
            assert not verify["account.move"].search_count([("ref", "ilike", marker)])
            assert not verify["account.move.line"].search_count([("name", "ilike", marker)])
            if baseline_company is not None:
                assert _company_snapshot(verify, fields) == baseline_company
                assert _default_snapshot(verify) == baseline_defaults
            if baseline_groups is not None:
                assert sorted(verify["res.users"].browse(5).group_ids.ids) == baseline_groups
                assert shared._direct_group(verify_cursor, group_id) == baseline_direct
        finally:
            verify_cursor.rollback()
    if failure is not None:
        raise failure
    print(json.dumps(_summary(args.alias, args.database), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_live_worker())
