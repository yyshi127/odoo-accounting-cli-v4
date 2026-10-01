"""One rollback-only native chart-of-accounts workflow; no external payment."""

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

_ALLOW_ENV = "ODACV4_ALLOW_ACCOUNT_PROCESSING_SMOKE"
_GROUPS = ("account.group_account_manager",)
_WRITES = {"account.account.duplicate", "account.account.delete", "account.account.default_taxes.assign", "account.account.tags.assign",
           "account.account.notes.update", "account.account.non_trade.set", "account.group.delete"}
_READS = {"account.account.processing_settings.get"}
_SETUP = {"account.account.create", "account.account.archive", "account.group.create", "tax.create", "account.tag.create",
          "journal_entry.create", "journal_entry.post"}
_MODELS = ("account.account", "account.group", "account.account.tag", "account.tax", "account.tax.repartition.line",
           "account.tax.group", "account.move", "account.move.line", "account.fiscal.position", "account.fiscal.position.account")


def _root():
    return Path(__file__).resolve().parents[2]


def _summary(alias, database):
    return {"alias": alias, "database": database, "company_id": 1, "user_id": 5, "business_su": False,
            "capabilities": sorted(_WRITES | _READS | _SETUP), "immediate_replays": 10,
            "native_owned_shared_copy_and_fresh_identity_verified": True,
            "native_default_taxes_tags_nullable_notes_and_non_trade_verified": True,
            "native_current_company_posted_balance_and_used_verified": True,
            "native_group_child_reparenting_verified": True,
            "native_failed_mutations_rolled_back": True,
            "native_journal_fiscal_and_tax_deletion_denials_verified": True,
            "posted_entries_unchanged_by_configuration": True,
            "company_shared_reference_and_missing_target_denials_verified": True,
            "rollback_verified": True, "temporary_groups_rolled_back": True, "execution": "in_process_cli_real_orm"}


if pytest is not None:
    @pytest.mark.integration
    def test_account_processing_rolls_back_per_alias():
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
    from odoo import fields

    from odoo_accounting_cli_v4.capabilities.core_writes import (
        _expected_idempotency_key,
        validate_core_write_request,
    )

    env = client.env
    ids = lifecycle._fixture_ids(admin, alias)
    code = "V4A" + run_id.hex[:8]
    replays = 0
    def track(record):
        model = record._name
        client.tracked[model].add(record.id)
        # account.code.mapping is virtual; its codes are stored on these accounts.
        if model == "account.tax": client.tracked["account.tax.repartition.line"].update(record.repartition_line_ids.ids)
        if model == "account.move": client.tracked["account.move.line"].update(record.line_ids.ids)
        return record
    def fixture(model, values): return track(admin[model].create(values))
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
    def read(account_id):
        client.last_runtime_failure = None
        try: return shared._read(client, alias, run_id, "account.account.processing_settings.get", {"account_id": account_id})
        except AssertionError:
            if client.last_runtime_failure is not None: raise client.last_runtime_failure
            raise
    def denied(cap, params, expected):
        client.last_runtime_failure = None
        try: shared._write(client, alias, run_id, cap, params, replay=False)
        except AssertionError: assert getattr(client.last_runtime_failure, "code", None) == expected
        else: raise RuntimeError("A native account/company denial succeeded")
    def missing_settings(account_id):
        from odoo_accounting_cli_v4 import cli
        from odoo_accounting_cli_v4.bridge.core_object_reads import (
            OdooCoreObjectReadPort,
        )
        cap = "account.account.processing_settings.get"
        stdout, stderr = io.StringIO(), io.StringIO()
        result = cli.main(["read", cap, "--request", "-"], stdin=io.StringIO(json.dumps(core._request(alias, run_id, cap, {"account_id": account_id}))),
                          stdout=stdout, stderr=stderr, port_factory=lambda *args: OdooCoreObjectReadPort(client))
        response = json.loads(stdout.getvalue())
        assert result == 4 and not stderr.getvalue() and response["error"]["code"] == "record_not_found" and response["odoo"]["user_id"] == 5
    def account(suffix, kind="income"):
        value = write("account.account.create", {"code": code+suffix, "name": marker+suffix, "account_type": kind,
                      "reconcile": kind == "asset_receivable", "currency_id": None}, replay=False)
        return env["account.account"].browse(value["id"])
    parent = write("account.group.create", {"name": marker+"-PARENT", "code_prefix_start": code, "code_prefix_end": code}, replay=False)["id"]
    child = write("account.group.create", {"name": marker+"-CHILD", "code_prefix_start": code+"1", "code_prefix_end": code+"1"}, replay=False)["id"]
    source, receivable = account("10"), account("20", "asset_receivable")
    assert read(source.id)["group_id"] == child and read(source.id)["current_balance"] == "0" and not read(source.id)["used"]
    tax = env["account.tax"].browse(write("tax.create", {"name": marker, "type_tax_use": "sale", "amount_type": "percent", "amount": 10}, replay=False)["id"])
    tag = env["account.account.tag"].browse(write("account.tag.create", {"name": marker, "applicability": "accounts", "color": 2, "country_id": None}, replay=False)["id"])
    write("account.account.default_taxes.assign", {"account_id": source.id, "tax_ids": [tax.id]})
    write("account.account.tags.assign", {"account_id": source.id, "tag_ids": [tag.id]})
    write("account.account.notes.update", {"account_id": source.id, "changes": {"description": marker+"\nDescription", "note": marker+"\nInternal"}})
    write("account.account.non_trade.set", {"account_id": receivable.id, "non_trade": True})
    settings = read(source.id)
    assert settings["tax_ids"] == [tax.id] and settings["tag_ids"] == [tag.id] and settings["description"] == source.description and settings["note"] == source.note
    assert read(receivable.id)["non_trade"] is True and read(receivable.id)["include_initial_balance"] is True
    copied = write("account.account.duplicate", {"account_id": source.id, "code": code+"11", "name": marker+"-COPY"})
    duplicate = env["account.account"].browse(copied["id"])
    assert copied["source_id"] == source.id and set(admin["account.account"].browse(duplicate.id).company_ids.ids) == {1} and duplicate.id != source.id
    duplicate_settings = read(duplicate.id)
    for field in ("tax_ids", "tag_ids", "description", "note", "non_trade", "active", "currency_id"):
        assert duplicate_settings[field] == settings[field]
    denied("account.account.duplicate", {"account_id": source.id, "code": code+"11", "name": marker+"-CONFLICT"}, "idempotency_conflict")
    shared_account = fixture("account.account", {"name": marker+"-SHARED", "code": code+"30", "account_type": "income", "company_ids": [(6, 0, [1, 2])],
        "code_mapping_ids": [(0, 0, {"company_id": company_id, "code": code+"30"}) for company_id in (1, 2)]})
    shared_snapshot = (shared_account.company_ids.ids, shared_account.with_company(1).code, shared_account.with_company(2).code)
    assert set(shared_account.company_ids.ids) == {1, 2} and env["account.account"].browse(shared_account.id).company_ids.ids == [1]
    isolated = write("account.account.duplicate", {"account_id": shared_account.id, "code": code+"31", "name": marker+"-ISOLATED"})
    assert admin["account.account"].browse(isolated["id"]).company_ids.ids == [1]
    assert (shared_account.company_ids.ids, shared_account.with_company(1).code, shared_account.with_company(2).code) == shared_snapshot
    denied("account.account.notes.update", {"account_id": shared_account.id, "changes": {"note": "Forbidden"}}, "record_not_found")
    denied("account.account.delete", {"account_id": shared_account.id}, "record_not_found")
    denied("account.account.archive", {"account_id": shared_account.id}, "record_not_found")
    denied("account.account.create", {"code": code+"30", "name": shared_account.name, "account_type": "income", "reconcile": shared_account.reconcile, "currency_id": None}, "idempotency_conflict")
    denied("account.account.duplicate", {"account_id": source.id, "code": code+"30", "name": shared_account.name}, "idempotency_conflict")
    foreign = fixture("account.account", {"name": marker+"-FOREIGN", "code": code+"40", "account_type": "income", "company_ids": [(6, 0, [2])]})
    foreign_group = fixture("account.group", {"name": marker+"-FOREIGN", "code_prefix_start": code, "code_prefix_end": code, "company_id": 2})
    foreign_tax_group = fixture("account.tax.group", {"name": marker+"-FOREIGN", "company_id": 2, "country_id": tax.country_id.id})
    foreign_tax = track(admin["account.tax"].with_company(2).create({"name": marker+"-FOREIGN", "company_id": 2,
        "country_id": tax.country_id.id, "tax_group_id": foreign_tax_group.id, "type_tax_use": "sale", "amount": 10}))
    wrong_tag = fixture("account.account.tag", {"name": marker+"-WRONG", "applicability": "products"})
    current = read(source.id)
    denied("account.account.default_taxes.assign", {"account_id": source.id, "tax_ids": [tax.id, foreign_tax.id]}, "record_not_found")
    denied("account.account.tags.assign", {"account_id": source.id, "tag_ids": [wrong_tag.id]}, "record_not_found")
    denied("account.account.delete", {"account_id": foreign.id}, "record_not_found")
    denied("account.account.duplicate", {"account_id": foreign.id, "code": code+"41", "name": marker+"-BAD"}, "record_not_found")
    denied("account.group.delete", {"account_group_id": foreign_group.id}, "record_not_found")
    assert read(source.id) == current
    unaffected = env["account.account"].search([("account_type", "=", "equity_unaffected"), ("company_ids", "in", [1])], limit=1)
    if not unaffected: unaffected = account("50", "equity_unaffected")
    denied("account.account.duplicate", {"account_id": unaffected.id, "code": code+"51", "name": marker+"-NATIVE-FAIL"}, "business_rule_error")
    assert not env["account.account"].search_count([("code", "=", code+"51"), ("company_ids", "in", [1])])
    today = fields.Date.context_today(env.user).isoformat()
    draft = env["account.move"].browse(write("journal_entry.create", {"journal_id": ids["general_journal"], "date": today, "reference": marker,
        "lines": [{"name": marker, "account_id": source.id, "partner_id": None, "debit": "0", "credit": "100"},
                  {"name": marker, "account_id": ids["expense"], "partner_id": None, "debit": "100", "credit": "0"}]}, replay=False)["id"])
    assert read(source.id)["used"] is True and read(source.id)["current_balance"] == "0"
    denied("account.account.delete", {"account_id": source.id}, "business_rule_error")
    write("journal_entry.post", {"move_id": draft.id}, replay=False)
    assert read(source.id)["current_balance"] == "-100" and read(source.id)["company_currency_id"] == env.company.currency_id.id
    def ledger(): return [(row.id, row.account_id.id, row.date_maturity, row.balance, row.amount_currency, row.amount_residual, row.tax_ids.ids) for row in draft.line_ids]
    posted = ledger()
    write("account.account.default_taxes.assign", {"account_id": source.id, "tax_ids": []})
    write("account.account.tags.assign", {"account_id": source.id, "tag_ids": []})
    write("account.account.notes.update", {"account_id": source.id, "changes": {"description": None, "note": ""}})
    assert read(source.id)["description"] is None and read(source.id)["note"] is None and ledger() == posted
    denied("account.account.delete", {"account_id": source.id}, "business_rule_error")
    write("account.account.archive", {"account_id": source.id}, replay=False)
    assert read(source.id)["active"] is False and read(source.id)["used"] and read(source.id)["current_balance"] == "-100" and ledger() == posted
    removed = write("account.account.delete", {"account_id": duplicate.id}, replay=False)
    assert removed["state"] == "deleted" and not duplicate.exists()
    denied("account.account.delete", {"account_id": duplicate.id}, "record_not_found")
    recreated = write("account.account.duplicate", {"account_id": source.id, "code": code+"11", "name": marker+"-COPY"})
    assert recreated["id"] != duplicate.id and read(recreated["id"])["active"] is False
    fiscal_account, tax_account = account("60"), account("70")
    fiscal = fixture("account.fiscal.position", {"name": marker, "company_id": 1})
    fixture("account.fiscal.position.account", {"position_id": fiscal.id, "account_src_id": fiscal_account.id, "account_dest_id": ids["income"]})
    denied("account.account.delete", {"account_id": fiscal_account.id}, "business_rule_error")
    tax.invoice_repartition_line_ids.filtered(lambda row: row.repartition_type == "tax").write({"account_id": tax_account.id})
    denied("account.account.delete", {"account_id": tax_account.id}, "business_rule_error")
    assert fiscal_account.exists() and tax_account.exists() and ledger() == posted
    removed_group = write("account.group.delete", {"account_group_id": parent}, replay=False)
    assert removed_group["state"] == "deleted" and not env["account.group"].browse(parent).exists()
    assert env["account.group"].browse(child).exists() and not env["account.group"].browse(child).parent_id
    write("account.group.delete", {"account_group_id": child}, replay=False)
    env.invalidate_all()
    assert read(source.id)["group_id"] is None and source.exists() and ledger() == posted
    denied("account.group.delete", {"account_group_id": child}, "record_not_found")
    missing_settings(foreign.id)
    missing_settings(1_999_999_999)
    assert replays == 10 and client.capabilities == _WRITES | _READS | _SETUP


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
    marker = f"ODACV4-ACCTPROC-{args.alias}-{args.run_id.hex}"
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
            for model in ("account.account", "account.group", "account.account.tag", "account.tax", "account.tax.group", "account.fiscal.position"):
                assert not verify[model].with_context(active_test=False).search_count([("name", "ilike", marker)])
            assert not verify["account.move.line"].search_count([("name", "ilike", marker)])
            for group_id, members in baseline.items(): assert shared._direct_group(verify_cursor, group_id) == members
        finally: verify_cursor.rollback()
    if failure is not None: raise failure
    print(json.dumps(_summary(args.alias, args.database), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_live_worker())
