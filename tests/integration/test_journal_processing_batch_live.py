"""One rollback-only native journal maintenance workflow; no external payment."""

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

_ALLOW_ENV = "ODACV4_ALLOW_JOURNAL_PROCESSING_SMOKE"
_GROUPS = ("account.group_account_manager",)
_WRITES = {"journal.duplicate", "journal.delete", "journal.sequence_policy.update", "journal.invoice_reference.update",
           "journal.non_deductible_account.assign", "journal.invoice_template.assign", "journal.group.delete"}
_READS = {"journal.processing_settings.get"}
_SETUP = {"journal.create", "journal.archive", "journal.bank_account.assign", "journal.group.create", "journal_entry.create", "journal_entry.post"}
_MODELS = ("account.journal", "account.journal.group", "account.account", "account.payment.method.line", "res.partner.bank",
           "mail.alias", "account.move", "account.move.line")


def _root():
    return Path(__file__).resolve().parents[2]


def _summary(alias, database):
    return {"alias":alias, "database":database, "company_id":1, "user_id":5, "business_su":False,
            "capabilities":sorted(_WRITES | _READS | _SETUP), "immediate_replays":12,
            "native_general_sale_bank_copy_and_fresh_identity_verified":True,
            "native_sequence_reference_private_account_and_template_settings_verified":True,
            "native_journal_guard_and_child_unlink_verified":True,
            "native_conditional_bank_unlink_acl_and_child_rollback_verified":True,
            "native_group_delete_preserves_journals_verified":True,
            "company_reference_and_missing_target_denials_verified":True,
            "posted_entries_unchanged_by_configuration":True,
            "rollback_verified":True, "temporary_groups_rolled_back":True, "execution":"in_process_cli_real_orm"}


if pytest is not None:
    @pytest.mark.integration
    def test_journal_processing_rolls_back_per_alias():
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


def _exercise(admin, client, alias, run_id, marker):
    from odoo import Command

    from odoo_accounting_cli_v4.bridge.core_writes_runtime import (
        _journal_processing_values,
    )
    from odoo_accounting_cli_v4.capabilities.core_writes import (
        _expected_idempotency_key,
        validate_core_write_request,
    )

    env = client.env
    ids = lifecycle._fixture_ids(admin, alias)
    existing_account_ids = set(admin["account.account"].with_context(active_test=False).search([]).ids)
    suffix = run_id.hex[:4]
    replays = 0
    def track(record):
        client.tracked[record._name].update(record.ids)
        if record._name == "account.journal":
            for field in ("default_account_id", "inbound_payment_method_line_ids", "outbound_payment_method_line_ids", "alias_id", "bank_account_id"):
                child = record[field]
                if child:
                    child_ids = set(child.ids)
                    if child._name == "account.account": child_ids -= existing_account_ids
                    client.tracked[child._name].update(child_ids)
        if record._name == "account.move": client.tracked["account.move.line"].update(record.line_ids.ids)
        return record
    def fixture(model, values, *, company_id=1): return track(admin[model].with_company(admin["res.company"].browse(company_id)).create(values))
    def write(cap, params, *, replay=True):
        nonlocal replays
        client.last_runtime_failure = None
        normalized = validate_core_write_request(cap, core._request(alias, run_id, cap, params))[2]
        try:
            if _expected_idempotency_key(cap, normalized, 1) is None:
                assert cap in _SETUP and replay is False
                key = f"{cap}:{run_id.hex}:{lifecycle._canonical_digest(normalized)[:32]}"
                reply = core._cli(client, alias, run_id, cap, params, key=key)
                assert reply["idempotent_replay"] is False
                value = reply["result"]
            else: value = shared._write(client, alias, run_id, cap, params, replay=replay)
        except AssertionError:
            if client.last_runtime_failure is not None: raise client.last_runtime_failure
            raise
        if cap in _WRITES and replay: replays += 1
        if value["state"] != "deleted": track(env[value["model"]].browse(value["id"]))
        return value
    def read(journal_id):
        client.last_runtime_failure = None
        try: return shared._read(client, alias, run_id, "journal.processing_settings.get", {"journal_id": journal_id})
        except AssertionError:
            if client.last_runtime_failure is not None: raise client.last_runtime_failure
            raise
    def denied(cap, params, expected):
        client.last_runtime_failure = None
        error = {3: "unauthorized", 4: "record_not_found", 5: "idempotency_conflict", 6: "odoo_write_error"}[expected]
        try: shared._write(client, alias, run_id, cap, params, replay=False)
        except AssertionError:
            failure = client.last_runtime_failure
            assert getattr(failure, "code", None) == error
            if expected == 6:
                cause = failure.__cause__
                assert type(cause).__name__ == "ForeignKeyViolation"
                assert cause.diag.constraint_name == "account_move_journal_id_fkey" and cause.diag.table_name == "account_move"
        else: raise RuntimeError("A native journal/company denial succeeded")
    journals = {}
    for kind, prefix, account_id in (("general", "G", ids["expense"]), ("sale", "S", ids["income"]), ("purchase", "P", ids["expense"]), ("bank", "B", None)):
        value = write("journal.create", {"name":marker+kind, "code":prefix+suffix, "type":kind, "sequence":10, "currency_id":None, "default_account_id":account_id})
        journals[kind] = env["account.journal"].browse(value["id"])
    sale, general, purchase, bank = (journals[kind] for kind in ("sale", "general", "purchase", "bank"))
    initial = read(sale.id)
    assert initial["type"] == "sale" and initial["refund_sequence"] is True and initial["available_invoice_template_pdf_report_ids"]
    report_id = initial["available_invoice_template_pdf_report_ids"][0]
    write("journal.sequence_policy.update", {"journal_id":sale.id, "changes":{"refund_sequence":False}})
    write("journal.sequence_policy.update", {"journal_id":bank.id, "changes":{"payment_sequence":False}})
    write("journal.invoice_reference.update", {"journal_id":sale.id, "changes":{"invoice_reference_type":"partner", "invoice_reference_model":"euro"}})
    write("journal.non_deductible_account.assign", {"journal_id":purchase.id, "account_id":ids["expense"]})
    write("journal.invoice_template.assign", {"journal_id":sale.id, "report_id":report_id})
    assert sale.refund_sequence is False and bank.payment_sequence is False
    assert sale.invoice_reference_type == "partner" and sale.invoice_reference_model == "euro"
    assert read(purchase.id)["non_deductible_account_id"] == ids["expense"]
    assert read(sale.id)["invoice_template_pdf_report_id"] == report_id

    bank_account = fixture("res.partner.bank", {"acc_number":marker+"BANK", "partner_id":admin["res.company"].browse(1).partner_id.id, "company_id":1})
    write("journal.bank_account.assign", {"journal_id":bank.id, "partner_bank_id":bank_account.id})
    copies = {}
    for kind, prefix in (("general","C"),("sale","D"),("bank","E")):
        source = journals[kind]
        snapshot = (_journal_processing_values(source), source.name, source.code, source.default_account_id.id, source.bank_account_id.id,
                    source.inbound_payment_method_line_ids.ids, source.outbound_payment_method_line_ids.ids)
        value = write("journal.duplicate", {"journal_id":source.id, "code":prefix+suffix, "name":marker+kind+"copy"})
        target = env["account.journal"].browse(value["id"])
        copies[kind] = target
        assert target.id != source.id and target.company_id.id == 1 and target.code == prefix+suffix and target.name == marker+kind+"copy"
        assert _journal_processing_values(target) == snapshot[0]
        assert snapshot == (_journal_processing_values(source), source.name, source.code, source.default_account_id.id, source.bank_account_id.id,
                            source.inbound_payment_method_line_ids.ids, source.outbound_payment_method_line_ids.ids)
        if kind == "bank":
            assert target.default_account_id and target.default_account_id != source.default_account_id and not target.bank_account_id
            assert target.inbound_payment_method_line_ids and target.outbound_payment_method_line_ids
            assert not (target.inbound_payment_method_line_ids | target.outbound_payment_method_line_ids) & (source.inbound_payment_method_line_ids | source.outbound_payment_method_line_ids)
        else: assert not target.default_account_id
    denied("journal.duplicate", {"journal_id":general.id, "code":"C"+suffix, "name":marker+"conflict"}, 5)
    foreign = fixture("account.journal", {"name":marker+"foreign", "code":"F"+suffix, "type":"general", "company_id":2}, company_id=2)
    foreign_account = fixture("account.account", {"name":marker+"foreign-account", "code":"JP"+run_id.hex[:8], "account_type":"expense", "company_ids":[Command.set([2])]}, company_id=2)
    foreign_group = fixture("account.journal.group", {"name":marker+"foreign-group", "company_id":2}, company_id=2)
    global_group = fixture("account.journal.group", {"name":marker+"global-group", "company_id":False})
    denied("journal.duplicate", {"journal_id":foreign.id, "code":"H"+suffix, "name":marker+"denied"}, 4)
    denied("journal.delete", {"journal_id":foreign.id}, 4)
    denied("journal.sequence_policy.update", {"journal_id":foreign.id, "changes":{"refund_sequence":True}}, 4)
    denied("journal.non_deductible_account.assign", {"journal_id":purchase.id, "account_id":foreign_account.id}, 4)
    denied("journal.group.delete", {"journal_group_id":foreign_group.id}, 4)
    denied("journal.group.delete", {"journal_group_id":global_group.id}, 4)
    invalid_report = admin["ir.actions.report"].search([("id","not in", initial["available_invoice_template_pdf_report_ids"])], limit=1)
    assert invalid_report
    denied("journal.invoice_template.assign", {"journal_id":sale.id, "report_id":invalid_report.id}, 4)
    denied("journal.invoice_template.assign", {"journal_id":purchase.id, "report_id":report_id}, 4)
    assert sale.invoice_template_pdf_report_id.id == report_id and purchase.non_deductible_account_id.id == ids["expense"]

    entry = write("journal_entry.create", {"journal_id":general.id, "date":"2026-10-01", "reference":marker,
        "lines":[{"name":marker+"debit", "account_id":ids["expense"], "debit":"100", "credit":"0", "partner_id":None},
                 {"name":marker+"credit", "account_id":ids["income"], "debit":"0", "credit":"100", "partner_id":None}]}, replay=False)
    move = env["account.move"].browse(entry["id"])
    denied("journal.delete", {"journal_id":general.id}, 6)
    assert move.exists() and general.exists()
    write("journal_entry.post", {"move_id":move.id})
    fields = ["id","account_id","journal_id","date_maturity","balance","amount_currency","amount_residual","tax_ids"]
    posted = (move.id, move.name, move.state, move.journal_id.id, move.line_ids.read(fields))
    write("journal.invoice_reference.update", {"journal_id":general.id, "changes":{"invoice_reference_model":"number"}})
    write("journal.invoice_template.assign", {"journal_id":sale.id, "report_id":None})
    write("journal.non_deductible_account.assign", {"journal_id":purchase.id, "account_id":None})
    denied("journal.delete", {"journal_id":general.id}, 6)
    assert posted == (move.id, move.name, move.state, move.journal_id.id, move.line_ids.read(fields))
    assert read(sale.id)["invoice_template_pdf_report_id"] is None and read(purchase.id)["non_deductible_account_id"] is None

    group = write("journal.group.create", {"name":marker+"group", "sequence":10, "excluded_journal_ids":[sale.id,general.id]})
    group_id = group["id"]
    before_journals = {record.id for record in journals.values()} | {record.id for record in copies.values()}
    write("journal.group.delete", {"journal_group_id":group_id}, replay=False)
    assert not env["account.journal.group"].browse(group_id).exists()
    assert set(env["account.journal"].browse(sorted(before_journals)).exists().ids) == before_journals
    denied("journal.group.delete", {"journal_group_id":group_id}, 4)
    deleted_id = copies["general"].id
    write("journal.delete", {"journal_id":deleted_id}, replay=False)
    assert not env["account.journal"].browse(deleted_id).exists()
    denied("journal.delete", {"journal_id":deleted_id}, 4)
    write("journal.archive", {"journal_id":general.id})
    assert read(general.id)["active"] is False
    recreated = write("journal.duplicate", {"journal_id":general.id, "code":"C"+suffix, "name":marker+"generalcopy"})
    assert recreated["id"] != deleted_id and recreated["state"] == "archived"
    bank_line_ids = (bank.inbound_payment_method_line_ids | bank.outbound_payment_method_line_ids).ids
    denied("journal.delete", {"journal_id":bank.id}, 3)
    assert bank.exists() and bank.bank_account_id.id == bank_account.id and bank_account.exists()
    assert set(env["account.payment.method.line"].browse(bank_line_ids).exists().ids) == set(bank_line_ids)
    write("journal.bank_account.assign", {"journal_id":bank.id, "partner_bank_id":None})
    write("journal.delete", {"journal_id":bank.id}, replay=False)
    assert not env["account.journal"].browse(bank.id).exists()
    assert not env["account.payment.method.line"].browse(bank_line_ids).exists() and bank_account.exists()
    assert copies["bank"].exists() and copies["bank"].default_account_id.exists()
    assert posted == (move.id, move.name, move.state, move.journal_id.id, move.line_ids.read(fields))
    for journal_id in (deleted_id,foreign.id):
        from odoo_accounting_cli_v4 import cli
        from odoo_accounting_cli_v4.bridge.core_object_reads import (
            OdooCoreObjectReadPort,
        )

        stdout, stderr = io.StringIO(), io.StringIO()
        result = cli.main(["read", "journal.processing_settings.get", "--request", "-"],
                          stdin=io.StringIO(json.dumps(core._request(alias, run_id, "journal.processing_settings.get", {"journal_id":journal_id}))),
                          stdout=stdout, stderr=stderr, port_factory=lambda *args: OdooCoreObjectReadPort(client))
        response = json.loads(stdout.getvalue())
        assert result == 4 and not stderr.getvalue() and response["error"]["code"] == "record_not_found" and response["odoo"]["user_id"] == 5
    assert replays == 12 and client.capabilities == _WRITES | _READS | _SETUP


def _live_worker():
    args = lifecycle._arguments(None)
    assert not (args.refund_only or args.payment_difference_only or args.analytic_readback_only)
    sys.path.insert(0, str(args.odoo_source.resolve(strict=True)))
    sys.path.insert(0, str(_root()/"src"))
    from odoo import SUPERUSER_ID, Command, api
    from odoo.orm.registry import Registry
    from odoo.tools import config
    config.parse_config(["--config", str(args.odoo_config.resolve(strict=True)), "--database", args.database, "--no-http", "--logfile=/dev/null"])
    registry = Registry(args.database)
    cursor = registry.cursor()
    marker = f"ODACV4-JRNPROC-{args.alias}-{args.run_id.hex}"
    tracked, baseline, failure = {}, {}, None
    try:
        context = {"allowed_company_ids": [1], "lang": "en_US", "tz": "Asia/Shanghai", "tracking_disable": True, "mail_create_nosubscribe": True, "mail_notrack": True}
        admin = api.Environment(cursor, SUPERUSER_ID, context)
        user = admin["res.users"].browse(5).exists()
        assert user.active and user.login == lifecycle._USER_LOGIN and 1 in user.company_ids.ids
        for name in _GROUPS:
            group_id = admin.ref(name).id
            baseline[group_id] = shared._direct_group(cursor, group_id)
            if not user.has_group(name): user.write({"group_ids": [Command.link(group_id)]})
        env = api.Environment(cursor, 5, context)
        assert not env.su and all(env.user.has_group(name) for name in _GROUPS)
        client = shared._Client(env)
        client.tracked = {model: set() for model in _MODELS}
        tracked = client.tracked
        _exercise(admin, client, args.alias, args.run_id, marker)
    except BaseException as exc:  # noqa: BLE001 - synthetic fixtures must roll back on failure too.
        failure = exc
    finally:
        cursor.rollback()
        cursor.close()
    with registry.cursor() as verify_cursor:
        try:
            verify = api.Environment(verify_cursor, SUPERUSER_ID, {"allowed_company_ids": [1, 2]})
            for model, ids in tracked.items(): assert not verify[model].with_context(active_test=False).search_count([("id", "in", sorted(ids))])
            for model in ("account.account", "account.journal", "account.journal.group"):
                assert not verify[model].with_context(active_test=False).search_count([("name", "ilike", marker)])
            assert not verify["account.move.line"].search_count([("name", "ilike", marker)])
            assert not verify["account.move"].search_count([("ref", "ilike", marker)])
            assert not verify["res.partner.bank"].search_count([("acc_number", "ilike", marker)])
            assert not verify["mail.alias"].search_count([("alias_name", "ilike", args.run_id.hex)])
            for group_id, members in baseline.items(): assert shared._direct_group(verify_cursor, group_id) == members
        finally: verify_cursor.rollback()
    if failure is not None: raise failure
    print(json.dumps(_summary(args.alias, args.database), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_live_worker())
