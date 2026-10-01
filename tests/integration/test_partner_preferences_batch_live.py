"""One guarded rollback-only CLI/ORM workflow for partner accounting preferences."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import sysconfig
import uuid
from decimal import Decimal
from pathlib import Path

import test_document_lifecycle_write_batch_live as lifecycle
import test_payment_configuration_batch_live as payment
import test_report_budget_write_batch_live as shared

try:
    import pytest
except ModuleNotFoundError:
    if "--live-worker" not in sys.argv:
        raise
    pytest = None

_ALLOW_ENV = "ODACV4_ALLOW_PARTNER_PREFERENCES_SMOKE"
_WRITES = {
    "partner.payment_preferences.update", "partner.invoice_delivery_preferences.update",
    "partner.bill_validation_preferences.update", "partner.credit_limit.update",
    "partner.credit_limit.reset",
}
_READS = {
    "partner.payment_preferences.get", "partner.invoice_delivery_preferences.get",
    "partner.bill_validation_preferences.get", "partner.credit_exposure.inspect",
}
_SETUP = {"journal.create"}


def _root():
    return Path(__file__).resolve().parents[2]


if pytest is not None:

    @pytest.mark.integration
    def test_partner_preferences_roll_back_per_alias():
        config_path, runtime = lifecycle._enabled_runtime(_ALLOW_ENV)
        run_id = uuid.uuid4()
        for alias in lifecycle._ALIASES:
            command, timeout = lifecycle._worker_command(alias, run_id, config_path, runtime)
            command[1] = str(Path(__file__).resolve())
            environment = os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            environment["PYTHONPATH"] = os.pathsep.join(filter(None, (
                str(_root() / "src"), sysconfig.get_path("purelib"),
                environment.get("PYTHONPATH"),
            )))
            completed = subprocess.run(command, cwd=_root(), env=environment, text=True,
                                       capture_output=True, check=False, timeout=max(timeout, 900))
            assert completed.returncode == 0, completed.stdout + completed.stderr
            result = json.loads(completed.stdout)
            assert result == _summary(alias, lifecycle._DATABASES[alias])
            print(completed.stdout.strip(), flush=True)


def _summary(alias, database):
    return {
        "alias": alias, "database": database, "company_id": 1, "user_id": 5,
        "business_su": False, "capabilities": sorted(_WRITES | _READS | _SETUP),
        "immediate_replays": 5, "nonzero_company_credit_fallback": 300,
        "company_dependent_preferences_isolated": True,
        "global_shared_preferences_observed": True, "native_edi_clear_verified": True,
        "payment_direction_rejected": True, "cross_company_rejected": True,
        "rollback_verified": True, "temporary_groups_and_default_rolled_back": True,
        "execution": "in_process_cli_real_orm",
    }


def _defaults(cursor):
    cursor.execute("""
        SELECT d.id, d.company_id, d.user_id, d.condition, d.json_value
        FROM ir_default d JOIN ir_model_fields f ON d.field_id=f.id
        WHERE f.model='res.partner' AND f.name='credit_limit' ORDER BY d.id
    """)
    return cursor.fetchall()


def _exercise(client, alias, run_id, marker, partner, foreign):
    read = lambda cap: shared._read(client, alias, run_id, cap, {"partner_id": partner.id})
    write = lambda cap, params: shared._write(client, alias, run_id, cap,
                                             {"partner_id": partner.id, **params})
    journal_id = shared._write(client, alias, run_id, "journal.create",
                              {"name": marker, "code": "R" + run_id.hex[:4], "type": "bank"},
                              replay=False)["id"]
    journal = client.env["account.journal"].browse(journal_id)
    inbound = journal.inbound_payment_method_line_ids[:1]
    outbound = journal.outbound_payment_method_line_ids[:1]
    assert inbound and outbound
    write("partner.payment_preferences.update", {"changes": {
        "property_inbound_payment_method_line_id": inbound.id,
        "property_outbound_payment_method_line_id": outbound.id,
    }})
    stored = read("partner.payment_preferences.get")
    assert stored["shared_partner"] and stored["property_inbound_payment_method_line_id"] == inbound.id
    assert stored["property_outbound_payment_method_line_id"] == outbound.id
    choices = read("partner.invoice_delivery_preferences.get")
    assert "manual" in choices["available_sending_methods"] and choices["available_pdf_report_ids"]
    pdf_id = choices["available_pdf_report_ids"][0]
    write("partner.invoice_delivery_preferences.update", {"changes": {
        "invoice_sending_method": "manual", "invoice_edi_format": None,
        "invoice_template_pdf_report_id": pdf_id,
    }})
    delivery = read("partner.invoice_delivery_preferences.get")
    assert delivery["invoice_edi_format"] is None and delivery["invoice_sending_method"] == "manual"
    assert delivery["invoice_template_pdf_report_id"] == pdf_id
    partner.invalidate_recordset()
    expected_store = "none" if partner._get_suggested_invoice_edi_format() else False
    assert partner.invoice_edi_format_store == expected_store
    write("partner.bill_validation_preferences.update", {"changes": {
        "autopost_bills": "never", "ignore_abnormal_invoice_date": True,
        "ignore_abnormal_invoice_amount": True,
    }})
    bill = read("partner.bill_validation_preferences.get")
    assert bill["autopost_bills"] == "never" and bill["ignore_abnormal_invoice_date"] and bill["ignore_abnormal_invoice_amount"]
    write("partner.credit_limit.update", {"credit_limit": "1000"})
    exposure = read("partner.credit_exposure.inspect")
    assert Decimal(exposure["credit_limit"]) == 1000 and exposure["use_partner_credit_limit"]
    write("partner.credit_limit.reset", {})
    exposure = read("partner.credit_exposure.inspect")
    assert Decimal(exposure["credit_limit"]) == 300 and not exposure["use_partner_credit_limit"]
    # Invalid direction and foreign-company targets must fail without mutating preferences.
    for target, changes, expected in (
        (partner.id, {"property_inbound_payment_method_line_id": outbound.id}, "business_rule_error"),
        (foreign.id, {"property_inbound_payment_method_line_id": inbound.id}, "record_not_found"),
    ):
        try:
            shared._write(client, alias, run_id, "partner.payment_preferences.update",
                          {"partner_id": target, "changes": changes}, replay=False)
        except AssertionError:
            assert getattr(client.last_runtime_failure, "code", None) == expected
        else:
            raise RuntimeError("An invalid partner preference unexpectedly succeeded")
    assert read("partner.payment_preferences.get") == stored
    assert client.capabilities == _WRITES | _READS | _SETUP


def _live_worker():
    args = lifecycle._arguments(None)
    assert not (args.refund_only or args.payment_difference_only or args.analytic_readback_only)
    sys.path.insert(0, str(args.odoo_source.resolve(strict=True)))
    sys.path.insert(0, str(_root() / "src"))
    from odoo import SUPERUSER_ID, Command, api
    from odoo.orm.registry import Registry
    from odoo.tools import config

    config.parse_config(["--config", str(args.odoo_config.resolve(strict=True)),
                         "--database", args.database, "--no-http", "--logfile=/dev/null"])
    registry = Registry(args.database)
    cursor = registry.cursor()
    marker = f"ODACV4-PARTNER-PREF-{args.alias}-{args.run_id.hex}"
    tracked = {model: set() for model in payment._MODELS}
    groups = {}
    failure = None
    try:
        context = {"allowed_company_ids": [1], "lang": "en_US", "tz": "Asia/Shanghai"}
        admin = api.Environment(cursor, SUPERUSER_ID, context)
        user = admin["res.users"].browse(5).exists()
        assert user.active and user.login == lifecycle._USER_LOGIN and 1 in user.company_ids.ids
        defaults = _defaults(cursor)
        for group in payment._GROUPS:
            group_id = admin.ref(group).id
            groups[group_id] = shared._direct_group(cursor, group_id)
            if not user.has_group(group):
                user.write({"group_ids": [Command.link(group_id)]})
        # A nonzero isolated-company fallback distinguishes reset from setting zero.
        admin["ir.default"].set("res.partner", "credit_limit", 300, company_id=1)
        partner = admin["res.partner"].create({"name": marker, "company_id": False, "is_company": True})
        foreign = admin["res.partner"].create({"name": marker + "-FOREIGN", "company_id": 2})
        partner.with_company(2).write({"credit_limit": 100,
                                      "ignore_abnormal_invoice_date": False,
                                      "ignore_abnormal_invoice_amount": False})
        partner.write({"invoice_sending_method": "email", "autopost_bills": "ask"})
        admin.flush_all()
        env = api.Environment(cursor, 5, context)
        assert not env.su and all(env.user.has_group(group) for group in payment._GROUPS)
        client = payment._Client(env)
        tracked = client.tracked
        tracked["res.partner"].update((partner.id, foreign.id))
        _exercise(client, args.alias, args.run_id, marker, env["res.partner"].browse(partner.id), foreign)
        admin.invalidate_all()
        other = partner.with_company(2)
        assert other.credit_limit == 100 and not other.ignore_abnormal_invoice_date and not other.ignore_abnormal_invoice_amount
        assert other.autopost_bills == "never" and other.invoice_template_pdf_report_id
        assert not other.property_inbound_payment_method_line_id and not other.property_outbound_payment_method_line_id
    except BaseException as exc:  # noqa: BLE001 - failed synthetic fixtures also roll back.
        failure = exc
    finally:
        cursor.rollback()
        cursor.close()
    with registry.cursor() as verify_cursor:
        try:
            verify = api.Environment(verify_cursor, SUPERUSER_ID, {"allowed_company_ids": [1, 2]})
            for model, ids in tracked.items():
                assert not verify[model].with_context(active_test=False).search_count([("id", "in", sorted(ids))])
            for model in ("res.partner", "account.journal", "account.account"):
                assert not verify[model].with_context(active_test=False).search_count([("name", "ilike", marker)])
            assert _defaults(verify_cursor) == defaults
            assert all(shared._direct_group(verify_cursor, group_id) == baseline for group_id, baseline in groups.items())
        finally:
            verify_cursor.rollback()
    if failure is not None:
        raise failure
    print(json.dumps(_summary(args.alias, args.database), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_live_worker())
