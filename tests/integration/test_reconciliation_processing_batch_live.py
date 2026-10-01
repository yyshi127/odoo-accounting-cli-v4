"""One rollback-only rule workflow; no reconciliation execution or notification."""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import sysconfig
import uuid
from decimal import Decimal
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

_ALLOW_ENV = "ODACV4_ALLOW_RECONCILIATION_PROCESSING_SMOKE"
_GROUPS = ("account.group_account_manager",)
_WRITES = {"reconciliation.model.duplicate", "reconciliation.model.delete", "reconciliation.model.line.create",
           "reconciliation.model.line.update", "reconciliation.model.line.delete", "reconciliation.model.lines.resequence",
           "reconciliation.model.activity_type.assign"}
_READS = {"reconciliation.model.processing_settings.get", "reconciliation.model.usage_lines.list"}
_SETUP = {"reconciliation.model.create", "reconciliation.model.archive"}
_MODELS = ("account.reconcile.model", "account.reconcile.model.line", "account.move", "account.move.line",
           "res.partner", "mail.activity.type", "account.analytic.account")


def _root():
    return Path(__file__).resolve().parents[2]


def _summary(alias, database):
    return {"alias":alias, "database":database, "company_id":1, "user_id":5, "business_su":False,
            "capabilities":sorted(_WRITES | _READS | _SETUP), "immediate_replays":11,
            "native_computed_partner_mapping_verified":True, "native_child_ids_and_order_preserved":True,
            "native_signed_amounts_and_regex_verified":True, "native_tax_and_analytic_copy_verified":True,
            "native_activity_configuration_only":True, "native_usage_keyset_verified":True,
            "archived_usage_read_verified":True, "native_delete_cascade_and_usage_link_clear_verified":True,
            "posted_amounts_unchanged":True, "company_parent_and_configuration_denial_verified":True,
            "rollback_verified":True, "temporary_groups_rolled_back":True, "execution":"in_process_cli_real_orm"}


if pytest is not None:
    @pytest.mark.integration
    def test_reconciliation_processing_rolls_back_per_alias():
        config_path, runtime = lifecycle._enabled_runtime(_ALLOW_ENV)
        run_id = uuid.uuid4()
        for alias in lifecycle._ALIASES:
            command, timeout = lifecycle._worker_command(alias, run_id, config_path, runtime)
            command[1] = str(Path(__file__).resolve())
            environment = os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            environment["PYTHONPATH"] = os.pathsep.join(filter(None, (str(_root()/"src"),sysconfig.get_path("purelib"),environment.get("PYTHONPATH"))))
            completed = subprocess.run(command,cwd=_root(),env=environment,text=True,capture_output=True,
                                       check=False,timeout=max(timeout,900))
            assert completed.returncode == 0, completed.stdout+completed.stderr
            assert json.loads(completed.stdout) == _summary(alias,lifecycle._DATABASES[alias])
            print(completed.stdout.strip(),flush=True)


def _exercise(admin, client, alias, run_id, marker):
    from odoo import Command, fields

    from odoo_accounting_cli_v4.bridge import core_writes_runtime as native

    env = client.env
    ids = lifecycle._fixture_ids(admin,alias)
    replays = 0
    def fixture(model,values):
        record = admin[model].create(values)
        client.tracked[model].add(record.id)
        return record
    def write(cap,params,*,replay=True):
        nonlocal replays
        client.last_runtime_failure = None
        try:
            value = shared._write(client,alias,run_id,cap,params,replay=replay)
        except AssertionError:
            if client.last_runtime_failure is not None: raise client.last_runtime_failure
            raise
        if cap in _WRITES and replay: replays += 1
        if value["model"] == "account.reconcile.model" and value["state"] != "deleted":
            client.tracked["account.reconcile.model.line"].update(env["account.reconcile.model"].browse(value["id"]).line_ids.ids)
        return value
    def read(cap,model_id,**params):
        client.last_runtime_failure = None
        try:
            return shared._read(client,alias,run_id,cap,{"reconciliation_model_id":model_id,**params})
        except AssertionError:
            if client.last_runtime_failure is not None: raise client.last_runtime_failure
            raise
    def denied(cap,params,code):
        client.last_runtime_failure = None
        try: shared._write(client,alias,run_id,cap,params,replay=False)
        except AssertionError: assert getattr(client.last_runtime_failure,"code",None) == code
        else: raise RuntimeError("A company, parent or native-configuration denial succeeded")
    def missing_read(model_id):
        from odoo_accounting_cli_v4 import cli
        from odoo_accounting_cli_v4.bridge.core_object_reads import (
            OdooCoreObjectReadPort,
        )

        cap = "reconciliation.model.processing_settings.get"
        req = core._request(alias,run_id,cap,{"reconciliation_model_id":model_id})
        stdout,stderr = io.StringIO(),io.StringIO()
        code = cli.main(["read",cap,"--request","-"],stdin=io.StringIO(json.dumps(req)),
                        stdout=stdout,stderr=stderr,port_factory=lambda *args:OdooCoreObjectReadPort(client))
        response = json.loads(stdout.getvalue())
        assert code == 4 and not stderr.getvalue() and response["success"] is False
        assert response["capability"] == cap and response["data"] is None
        assert response["error"]["code"] == "record_not_found" and response["odoo"]["user_id"] == 5
    partner = fixture("res.partner",{"name":marker,"company_id":1})
    activity = fixture("mail.activity.type",{"name":marker,"res_model":"account.bank.statement.line"})
    wrong_activity = fixture("mail.activity.type",{"name":marker+"-WRONG","res_model":"res.partner"})
    plan = admin["account.analytic.plan"].search([("parent_id","=",False)],limit=1)
    assert plan
    analytic = fixture("account.analytic.account",{"name":marker,"company_id":1,"plan_id":plan.id})
    tax = admin["account.tax"].search([("company_id","=",1),("active","=",True)],limit=1)
    assert tax
    outside = fixture("account.reconcile.model",{"name":marker+"-OUTSIDE","company_id":1})
    foreign = admin["account.reconcile.model"].with_company(2).create({"name":marker+"-FOREIGN","company_id":2})
    client.tracked["account.reconcile.model"].add(foreign.id)
    line = {"sequence":-10,"account_id":None,"partner_id":partner.id,"label":"MAP",
            "amount_type":"percentage","amount_string":"100","tax_ids":[]}
    outsider = fixture("account.reconcile.model.line",{"model_id":outside.id,"account_id":ids["expense"],"amount_type":"fixed","amount_string":"1"})
    model_id = write("reconciliation.model.create",{"name":marker,"sequence":10,"trigger":"manual",
                     "match_journal_ids":[],"match_partner_ids":[],"match_amount":None,
                     "match_label":{"operator":"contains","value":marker}},replay=False)["id"]
    model = env["account.reconcile.model"].browse(model_id)
    map_id = write("reconciliation.model.line.create",{"reconciliation_model_id":model_id,"line":line})["source_id"]
    settings = read("reconciliation.model.processing_settings.get",model_id)
    assert settings["mapped_partner_id"] == partner.id and settings["can_be_proposed"] is False
    fee_id = write("reconciliation.model.line.create",{"reconciliation_model_id":model_id,
                   "line":{**line,"sequence":0,"account_id":ids["expense"],"partner_id":None,"label":"FEE","amount_type":"fixed","amount_string":"-7.5"}})["source_id"]
    settings = read("reconciliation.model.processing_settings.get",model_id)
    assert settings["mapped_partner_id"] is None and settings["can_be_proposed"] is True
    temporary_id = write("reconciliation.model.line.create",{"reconciliation_model_id":model_id,
                         "line":{**line,"sequence":50,"account_id":ids["expense"],"partner_id":None,"label":"TEMP","amount_type":"percentage_st_line","amount_string":"-125"}})["source_id"]
    for target in (activity.id,None,activity.id):
        write("reconciliation.model.activity_type.assign",{"reconciliation_model_id":model_id,"activity_type_id":target})
        assert read("reconciliation.model.processing_settings.get",model_id)["next_activity_type_id"] == target
    assert not admin["mail.activity"].search_count([("activity_type_id","=",activity.id)])
    write("reconciliation.model.line.update",{"reconciliation_model_id":model_id,"line_id":fee_id,
          "changes":{"sequence":-11,"label":None,"amount_string":"-8.50","tax_ids":[tax.id],
                     "analytic_distribution":[{"analytic_account_ids":[analytic.id],"percentage":"100"}]}})
    fee = env["account.reconcile.model.line"].browse(fee_id)
    assert fee.amount_string == "-8.50" and not fee.label and fee.tax_ids.ids == [tax.id]
    assert native._normalized_reconciliation_analytic_distribution(fee.analytic_distribution) == [{"analytic_account_ids":[analytic.id],"percentage":"100"}]
    write("reconciliation.model.line.update",{"reconciliation_model_id":model_id,"line_id":fee_id,
          "changes":{"amount_type":"percentage","amount_string":"125"}})
    assert fee.amount == 125 and fee.analytic_distribution and fee.tax_ids
    order = [fee_id,map_id,temporary_id]
    write("reconciliation.model.lines.resequence",{"reconciliation_model_id":model_id,"line_ids":order})
    assert model.line_ids.ids == order and read("reconciliation.model.processing_settings.get",model_id)["line_ids"] == order
    duplicate_id = write("reconciliation.model.duplicate",{"reconciliation_model_id":model_id,"name":marker+"-COPY"})["id"]
    duplicate = env["account.reconcile.model"].browse(duplicate_id)
    assert not set(duplicate.line_ids.ids) & set(order)
    assert native._reconciliation_copy_values(duplicate) == native._reconciliation_copy_values(model)
    assert duplicate.next_activity_type_id.id == activity.id
    snapshot = native._reconciliation_copy_values(duplicate)
    write("reconciliation.model.line.update",{"reconciliation_model_id":model_id,"line_id":fee_id,
          "changes":{"amount_type":"regex","amount_string":r"FEE: ([0-9]+)","tax_ids":[],"analytic_distribution":[]}})
    assert fee.amount_type == "regex" and not fee.tax_ids and not fee.analytic_distribution
    assert native._reconciliation_copy_values(duplicate) == snapshot
    denied("reconciliation.model.duplicate",{"reconciliation_model_id":model_id,"name":marker+"-COPY"},"idempotency_conflict")
    denied("reconciliation.model.line.update",{"reconciliation_model_id":model_id,"line_id":fee_id,"changes":{"amount_string":"["}},"business_rule_error")
    denied("reconciliation.model.line.update",{"reconciliation_model_id":model_id,"line_id":outsider.id,"changes":{"label":"BAD"}},"record_not_found")
    denied("reconciliation.model.lines.resequence",{"reconciliation_model_id":model_id,"line_ids":[map_id]},"business_rule_error")
    denied("reconciliation.model.activity_type.assign",{"reconciliation_model_id":model_id,"activity_type_id":wrong_activity.id},"record_not_found")
    denied("reconciliation.model.line.create",{"reconciliation_model_id":foreign.id,"line":line},"record_not_found")
    denied("reconciliation.model.delete",{"reconciliation_model_id":foreign.id},"record_not_found")
    missing_read(foreign.id)
    assert read("reconciliation.model.usage_lines.list",foreign.id)["items"] == []
    write("reconciliation.model.line.delete",{"reconciliation_model_id":model_id,"line_id":temporary_id},replay=False)
    assert model.line_ids.ids == [fee_id,map_id] and len(duplicate.line_ids) == 3
    denied("reconciliation.model.line.delete",{"reconciliation_model_id":model_id,"line_id":temporary_id},"record_not_found")
    today = fields.Date.context_today(env.user)
    entry = fixture("account.move",{"company_id":1,"journal_id":ids["general_journal"],"move_type":"entry","date":today,
          "line_ids":[Command.create({"name":marker,"account_id":ids["asset"],"debit":17.5,"credit":0,"reconcile_model_id":model_id}),
                      Command.create({"name":marker,"account_id":ids["income"],"debit":0,"credit":17.5,"reconcile_model_id":model_id})]})
    client.tracked["account.move.line"].update(entry.line_ids.ids)
    entry.action_post()
    posted = [(row.id,row.account_id.id,row.balance,row.amount_currency) for row in entry.line_ids]
    rows,cursor=[],None
    while True:
        page=read("reconciliation.model.usage_lines.list",model_id,limit=1,cursor=cursor)
        rows.extend(page["items"])
        if not page["has_more"]: break
        cursor=page["next_cursor"]
    assert len(rows)==2 and {row["id"] for row in rows} == set(entry.line_ids.ids)
    assert all(row["reconcile_model_id"]==model_id and row["move_id"]==entry.id for row in rows)
    assert sum(Decimal(row["balance"]) for row in rows)==0
    write("reconciliation.model.archive",{"reconciliation_model_id":model_id},replay=False)
    assert read("reconciliation.model.processing_settings.get",model_id)["active"] is False
    assert len(read("reconciliation.model.usage_lines.list",model_id)["items"]) == 2
    removed=write("reconciliation.model.delete",{"reconciliation_model_id":model_id},replay=False)
    assert removed["state"]=="deleted" and not model.exists()
    assert not env["account.reconcile.model.line"].browse([fee_id,map_id]).exists()
    entry.line_ids.invalidate_recordset(["reconcile_model_id"])
    assert not entry.line_ids.reconcile_model_id and entry.state=="posted"
    assert [(row.id,row.account_id.id,row.balance,row.amount_currency) for row in entry.line_ids] == posted
    missing_read(model_id)
    assert read("reconciliation.model.usage_lines.list",model_id)["items"] == []
    denied("reconciliation.model.delete",{"reconciliation_model_id":model_id},"record_not_found")
    write("reconciliation.model.delete",{"reconciliation_model_id":duplicate_id},replay=False)
    assert not duplicate.exists() and foreign.exists() and outsider.exists()
    assert replays==11 and client.capabilities == _WRITES | _READS | _SETUP


def _live_worker():
    args=lifecycle._arguments(None)
    assert not (args.refund_only or args.payment_difference_only or args.analytic_readback_only)
    sys.path.insert(0,str(args.odoo_source.resolve(strict=True)))
    sys.path.insert(0,str(_root()/"src"))
    from odoo import SUPERUSER_ID, Command, api
    from odoo.orm.registry import Registry
    from odoo.tools import config

    config.parse_config(["--config",str(args.odoo_config.resolve(strict=True)),"--database",args.database,"--no-http","--logfile=/dev/null"])
    registry=Registry(args.database)
    cursor=registry.cursor()
    marker=f"ODACV4-RECON-PROCESSING-{args.alias}-{args.run_id.hex}"
    tracked,baseline,failure={}, {},None
    try:
        context={"allowed_company_ids":[1],"lang":"en_US","tz":"Asia/Shanghai","tracking_disable":True,"mail_create_nosubscribe":True,"mail_notrack":True}
        admin=api.Environment(cursor,SUPERUSER_ID,context)
        user=admin["res.users"].browse(5).exists()
        assert user.active and user.login==lifecycle._USER_LOGIN and 1 in user.company_ids.ids
        for name in _GROUPS:
            group_id=admin.ref(name).id
            baseline[group_id]=shared._direct_group(cursor,group_id)
            if not user.has_group(name): user.write({"group_ids":[Command.link(group_id)]})
        env=api.Environment(cursor,5,context)
        assert not env.su and all(env.user.has_group(name) for name in _GROUPS)
        client=shared._Client(env)
        client.tracked={model:set() for model in _MODELS}
        tracked=client.tracked
        _exercise(admin,client,args.alias,args.run_id,marker)
    except BaseException as exc:  # noqa: BLE001 - failed synthetic fixtures must roll back too.
        failure=exc
    finally:
        cursor.rollback()
        cursor.close()
    with registry.cursor() as verify_cursor:
        try:
            verify=api.Environment(verify_cursor,SUPERUSER_ID,{"allowed_company_ids":[1,2]})
            for model,ids in tracked.items():
                assert not verify[model].with_context(active_test=False).search_count([("id","in",sorted(ids))])
            for model in ("account.reconcile.model","res.partner","mail.activity.type","account.analytic.account"):
                assert not verify[model].with_context(active_test=False).search_count([("name","ilike",marker)])
            assert not verify["account.move.line"].search_count([("name","ilike",marker)])
            for group_id,members in baseline.items(): assert shared._direct_group(verify_cursor,group_id)==members
        finally:
            verify_cursor.rollback()
    if failure is not None: raise failure
    print(json.dumps(_summary(args.alias,args.database),sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(_live_worker())
