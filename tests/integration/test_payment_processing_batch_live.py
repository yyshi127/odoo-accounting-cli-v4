"""One rollback-only native payment workflow; no bank or provider submission."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import sysconfig
import uuid
from pathlib import Path

import test_document_lifecycle_write_batch_live as lifecycle
import test_payment_bank_capability_batch_live as core
import test_payment_configuration_batch_live as configuration
import test_report_budget_write_batch_live as shared

try:
    import pytest
except ModuleNotFoundError:
    if "--live-worker" not in sys.argv:
        raise
    pytest = None

_ALLOW_ENV = "ODACV4_ALLOW_PAYMENT_PROCESSING_SMOKE"
_GROUPS = ("account.group_account_manager", "base.group_partner_manager")
_WRITES = {"payment.bank_account.assign", "payment.destination_account.assign",
           "payment.sent_status.set", "payment.validate", "payment.reject"}
_READS = {"payment.processing_settings.get", "payment.bank_account_candidates.list", "payment.duplicate_candidates.list"}
_SETUP = {"payment.create", "payment.post", "payment.reset_to_draft"}


def _root():
    return Path(__file__).resolve().parents[2]


def _summary(alias, database):
    return {"alias":alias, "database":database, "company_id":1, "user_id":5, "business_su":False,
            "capabilities":sorted(_WRITES | _READS | _SETUP), "immediate_replays":11,
            "native_recipient_and_company_bank_choices":True, "bank_trust_unchanged":True,
            "native_shared_bank_scope_verified":True,
            "native_duplicate_warning_and_keyset_verified":True, "native_destination_posted_verified":True,
            "native_sent_unset_and_rejection_verified":True, "rejected_payment_reset_verified":True,
            "native_no_entry_validation_verified":True, "posted_bank_change_preserves_native_entry":True,
            "state_company_and_eligibility_denial_verified":True, "rollback_verified":True,
            "temporary_groups_rolled_back":True, "execution":"in_process_cli_real_orm"}


if pytest is not None:
    @pytest.mark.integration
    def test_payment_processing_rolls_back_per_alias():
        config_path, runtime = lifecycle._enabled_runtime(_ALLOW_ENV)
        run_id = uuid.uuid4()
        for alias in lifecycle._ALIASES:
            command, timeout = lifecycle._worker_command(alias, run_id, config_path, runtime)
            command[1] = str(Path(__file__).resolve())
            environment = os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            environment["PYTHONPATH"] = os.pathsep.join(filter(None, (str(_root()/"src"), sysconfig.get_path("purelib"), environment.get("PYTHONPATH"))))
            completed = subprocess.run(command, cwd=_root(), env=environment, text=True, capture_output=True,
                                       check=False, timeout=max(timeout, 900))
            assert completed.returncode == 0, completed.stdout + completed.stderr
            assert json.loads(completed.stdout) == _summary(alias, lifecycle._DATABASES[alias])
            print(completed.stdout.strip(), flush=True)


def _fixture(admin, client, alias, run_id, marker):
    def create(model, values):
        record = admin[model].create(values)
        client.tracked[model].add(record.id)
        if model == "account.journal":
            client.tracked["account.account"].update(record.default_account_id.ids)
            client.tracked["account.payment.method.line"].update((record.inbound_payment_method_line_ids | record.outbound_payment_method_line_ids).ids)
        return record
    ids = lifecycle._fixture_ids(admin, alias)
    defaults = {kind: admin["account.account"].search([("company_ids","in",[1]), ("account_type","=",kind)], limit=1).id
                for kind in ("asset_receivable", "liability_payable")}
    assert all(defaults.values())
    partner = create("res.partner", {"name":marker, "company_id":1, "property_account_receivable_id":defaults["asset_receivable"], "property_account_payable_id":defaults["liability_payable"]})
    other = create("res.partner", {"name":marker+"-OTHER", "company_id":1})
    banks = [create("res.partner.bank", {"acc_number":marker+"-BANK-"+str(index), "partner_id":partner.id}) for index in range(3)]
    wrong = create("res.partner.bank", {"acc_number":marker+"-WRONG", "partner_id":other.id})
    foreign_partner = create("res.partner", {"name":marker+"-FOREIGN", "company_id":2})
    foreign_bank = create("res.partner.bank", {"acc_number":marker+"-FOREIGN", "partner_id":foreign_partner.id})
    shared_partner = create("res.partner", {"name":marker+"-SHARED", "company_id":False, "property_account_receivable_id":defaults["asset_receivable"], "property_account_payable_id":defaults["liability_payable"]})
    shared_bank = create("res.partner.bank", {"acc_number":marker+"-SHARED", "partner_id":shared_partner.id})
    own_bank = create("res.partner.bank", {"acc_number":marker+"-COMPANY", "partner_id":admin["res.company"].browse(1).partner_id.id})
    outstanding = create("account.account", {"name":marker+"-OUTSTANDING", "code":"P"+run_id.hex[:11], "account_type":"asset_current", "reconcile":True, "company_ids":[(6,0,[1])]})
    payable = create("account.account", {"name":marker+"-PAYABLE", "code":"Q"+run_id.hex[:11], "account_type":"liability_payable", "reconcile":True, "company_ids":[(6,0,[1])]})
    journal = create("account.journal", {"name":marker, "code":"P"+run_id.hex[:4], "type":"bank", "company_id":1, "bank_account_id":own_bank.id})
    method = journal.outbound_payment_method_line_ids.filtered(lambda line:line.code == "manual")
    assert len(method) == 1
    method.write({"payment_account_id":outstanding.id})
    no_entry = create("account.journal", {"name":marker+"-NOENTRY", "code":"Q"+run_id.hex[:4], "type":"bank", "company_id":1})
    no_entry_method = no_entry.outbound_payment_method_line_ids.filtered(lambda line:line.code == "manual")
    assert len(no_entry_method) == 1
    no_entry_method.write({"payment_account_id":False})
    foreign_journal = admin["account.journal"].with_company(2).create({"name":marker+"-FOREIGN", "code":"R"+run_id.hex[:4], "type":"bank", "company_id":2})
    client.tracked["account.journal"].add(foreign_journal.id)
    client.tracked["account.account"].update(foreign_journal.default_account_id.ids)
    client.tracked["account.payment.method.line"].update((foreign_journal.inbound_payment_method_line_ids | foreign_journal.outbound_payment_method_line_ids).ids)
    foreign = admin["account.payment"].with_company(2).create({"journal_id":foreign_journal.id, "company_id":2, "payment_type":"outbound", "partner_type":"supplier", "amount":17.5, "memo":marker+"-FOREIGN"})
    client.tracked["account.payment"].add(foreign.id)
    return {"partner":partner.id, "banks":[bank.id for bank in banks], "wrong":wrong.id, "own_bank":own_bank.id,
            "journal":journal.id, "method":method.id, "inbound_method":journal.inbound_payment_method_line_ids.filtered(lambda line:line.code == "manual").id,
            "no_entry_journal":no_entry.id, "no_entry_method":no_entry_method.id, "payable":payable.id,
            "outstanding":outstanding.id, "foreign_payment":foreign.id, "foreign_bank":foreign_bank.id,
            "shared_partner":shared_partner.id, "shared_bank":shared_bank.id, "currency":ids["currency"]}


def _exercise(client, alias, run_id, marker, fixture):
    from odoo import fields

    env = client.env
    today = fields.Date.context_today(env.user).isoformat()
    replays = 0
    def create(key, **changes):
        params = {"payment_type":"outbound", "partner_type":"supplier", "partner_id":fixture["partner"],
                  "amount":"17.5", "currency_id":fixture["currency"], "journal_id":fixture["journal"],
                  "payment_method_line_id":fixture["method"], "date":today, "payment_reference":None, **changes}
        return core._cli(client, alias, run_id, "payment.create", params, key=marker+"-"+key)["result"]["id"]
    def read(cap, payment_id, **params):
        client.last_runtime_failure = None
        try:
            return shared._read(client, alias, run_id, cap, {"payment_id":payment_id, **params})
        except AssertionError:
            if client.last_runtime_failure is not None: raise client.last_runtime_failure
            raise
    def write(cap, payment_id, **params):
        nonlocal replays
        client.last_runtime_failure = None
        try:
            value = shared._write(client, alias, run_id, cap, {"payment_id":payment_id, **params})
        except AssertionError:
            if client.last_runtime_failure is not None: raise client.last_runtime_failure
            raise
        replays += 1
        return value
    def denied(cap, payment_id, expected, **params):
        client.last_runtime_failure = None
        try: shared._write(client, alias, run_id, cap, {"payment_id":payment_id, **params}, replay=False)
        except AssertionError: assert getattr(client.last_runtime_failure, "code", None) == expected
        else: raise RuntimeError("A payment state, company or eligibility denial succeeded")
    payment_id = create("MAIN")
    second, third = create("DUPLICATE-1"), create("DUPLICATE-2")
    payment = env["account.payment"].browse(payment_id)
    first = read("payment.processing_settings.get", payment_id)
    assert first["state"] == "draft" and first["outstanding_account_id"] == fixture["outstanding"]
    banks, cursor = [], None
    while True:
        page = read("payment.bank_account_candidates.list", payment_id, limit=1, cursor=cursor)
        banks.extend(page["items"])
        if not page["has_more"]: break
        cursor = page["next_cursor"]
    assert {row["id"] for row in banks} == set(fixture["banks"]) and len(banks) == 3, banks
    assert all(row["company_id"] == 1 and not row["allow_out_payment"] for row in banks)
    duplicates, cursor = [], None
    while True:
        page = read("payment.duplicate_candidates.list", payment_id, limit=1, cursor=cursor)
        duplicates.extend(page["items"])
        if not page["has_more"]: break
        cursor = page["next_cursor"]
    assert {row["id"] for row in duplicates} == {second, third} and len(duplicates) == 2
    assert all(row["payment_id"] == payment_id and row["amount"] == "17.5" for row in duplicates)
    write("payment.bank_account.assign", payment_id, partner_bank_id=fixture["banks"][1])
    write("payment.bank_account.assign", payment_id, partner_bank_id=None)
    write("payment.bank_account.assign", payment_id, partner_bank_id=fixture["banks"][1])
    write("payment.destination_account.assign", payment_id, account_id=fixture["payable"])
    denied("payment.bank_account.assign", payment_id, "business_rule_error", partner_bank_id=fixture["wrong"])
    denied("payment.bank_account.assign", payment_id, "record_not_found", partner_bank_id=fixture["foreign_bank"])
    denied("payment.sent_status.set", second, "state_conflict", sent=True)
    denied("payment.validate", second, "state_conflict")
    denied("payment.bank_account.assign", fixture["foreign_payment"], "record_not_found", partner_bank_id=fixture["banks"][1])
    assert read("payment.bank_account_candidates.list", fixture["foreign_payment"])["items"] == []
    assert read("payment.duplicate_candidates.list", fixture["foreign_payment"])["items"] == []
    core._cli(client, alias, run_id, "payment.post", {"payment_id":payment_id}, key=f"payment.post:{payment_id}")
    assert payment.state == "in_process" and payment.move_id.state == "posted"
    move = payment.move_id
    assert fixture["payable"] in move.line_ids.account_id.ids and fixture["outstanding"] in move.line_ids.account_id.ids
    assert env.company.currency_id.is_zero(sum(move.line_ids.mapped("balance")))
    snapshot = [(line.id, line.account_id.id, line.balance, line.amount_currency) for line in move.line_ids]
    old_entry_bank = move.partner_bank_id.id
    denied("payment.destination_account.assign", payment_id, "state_conflict", account_id=fixture["payable"])
    denied("payment.validate", payment_id, "state_conflict")
    denied("payment.reject", payment_id, "state_conflict")
    write("payment.sent_status.set", payment_id, sent=True)
    write("payment.sent_status.set", payment_id, sent=False)
    write("payment.sent_status.set", payment_id, sent=True)
    write("payment.bank_account.assign", payment_id, partner_bank_id=fixture["banks"][2])
    assert payment.partner_bank_id.id == fixture["banks"][2] and move.partner_bank_id.id == old_entry_bank
    assert [(line.id, line.account_id.id, line.balance, line.amount_currency) for line in move.line_ids] == snapshot
    assert all(not env["res.partner.bank"].browse(bank_id).allow_out_payment for bank_id in fixture["banks"])
    write("payment.reject", payment_id)
    assert payment.state == "rejected" and move.state == "posted"
    write("payment.reset_to_draft", payment_id)
    assert payment.state == "draft" and move.state == "draft"
    no_entry = create("NOENTRY", journal_id=fixture["no_entry_journal"], payment_method_line_id=fixture["no_entry_method"], amount="19")
    bare = env["account.payment"].browse(no_entry)
    assert not bare.outstanding_account_id and not bare.move_id
    core._cli(client, alias, run_id, "payment.post", {"payment_id":no_entry}, key=f"payment.post:{no_entry}")
    assert bare.state == "in_process" and not bare.move_id
    write("payment.validate", no_entry)
    assert bare.state == "paid" and not bare.move_id and bare.is_matched
    assert read("payment.processing_settings.get", no_entry)["state"] == "paid"
    inbound = create("INBOUND", payment_type="inbound", partner_type="customer", payment_method_line_id=fixture["inbound_method"], amount="23")
    assert {row["id"] for row in read("payment.bank_account_candidates.list", inbound)["items"]} == {fixture["own_bank"]}
    shared_payment = create("SHARED", partner_id=fixture["shared_partner"], amount="29")
    shared_rows = read("payment.bank_account_candidates.list", shared_payment)["items"]
    assert len(shared_rows) == 1 and shared_rows[0]["id"] == fixture["shared_bank"] and shared_rows[0]["company_id"] is None
    assert replays == 11 and client.capabilities == _WRITES | _READS | _SETUP


def _live_worker():
    args = lifecycle._arguments(None)
    assert not (args.refund_only or args.payment_difference_only or args.analytic_readback_only)
    sys.path.insert(0, str(args.odoo_source.resolve(strict=True)))
    sys.path.insert(0, str(_root()/"src"))
    from odoo import SUPERUSER_ID, Command, api
    from odoo.orm.registry import Registry
    from odoo.tools import config

    config.parse_config(["--config",str(args.odoo_config.resolve(strict=True)),"--database",args.database,"--no-http","--logfile=/dev/null"])
    registry = Registry(args.database)
    cursor = registry.cursor()
    marker = f"ODACV4-PAYMENT-PROCESSING-{args.alias}-{args.run_id.hex}"
    tracked, baseline, failure = {}, {}, None
    try:
        context = {"allowed_company_ids":[1], "lang":"en_US", "tz":"Asia/Shanghai", "tracking_disable":True, "mail_create_nosubscribe":True, "mail_notrack":True}
        admin = api.Environment(cursor, SUPERUSER_ID, context)
        user = admin["res.users"].browse(5).exists()
        assert user.active and user.login == lifecycle._USER_LOGIN and 1 in user.company_ids.ids
        for name in _GROUPS:
            group_id = admin.ref(name).id
            baseline[group_id] = shared._direct_group(cursor, group_id)
            if not user.has_group(name): user.write({"group_ids":[Command.link(group_id)]})
        env = api.Environment(cursor, 5, context)
        assert not env.su and all(env.user.has_group(name) for name in _GROUPS)
        client = configuration._Client(env)
        tracked = client.tracked
        fixture = _fixture(admin, client, args.alias, args.run_id, marker)
        _exercise(client, args.alias, args.run_id, marker, fixture)
    except BaseException as exc:  # noqa: BLE001 - failed synthetic fixtures must roll back too.
        failure = exc
    finally:
        cursor.rollback()
        cursor.close()
    with registry.cursor() as verify_cursor:
        try:
            verify = api.Environment(verify_cursor, SUPERUSER_ID, {"allowed_company_ids":[1,2]})
            for model, ids in tracked.items():
                assert not verify[model].with_context(active_test=False).search_count([("id","in",sorted(ids))])
            for model in ("res.partner", "account.account", "account.journal"):
                assert not verify[model].with_context(active_test=False).search_count([("name","ilike",marker)])
            assert not verify["res.partner.bank"].with_context(active_test=False).search_count([("acc_number","ilike",marker)])
            assert not verify["account.payment"].search_count([("memo","ilike",marker)])
            for group_id, members in baseline.items(): assert shared._direct_group(verify_cursor, group_id) == members
        finally:
            verify_cursor.rollback()
    if failure is not None: raise failure
    print(json.dumps(_summary(args.alias, args.database), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_live_worker())
