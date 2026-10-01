"""One rollback-only native installment workflow; no payments or external delivery."""

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

_ALLOW_ENV = "ODACV4_ALLOW_PAYMENT_TERM_PROCESSING_SMOKE"
_GROUPS = ("account.group_account_manager",)
_WRITES = {"payment_term.duplicate", "payment_term.delete", "payment_term.line.create",
           "payment_term.line.update", "payment_term.line.delete", "payment_term.lines.update"}
_READS = {"invoice.payment_schedule.inspect", "payment_term.usage_moves.list"}
_SETUP = {"payment_term.create", "payment_term.update", "payment_term.archive", "customer_invoice.create", "invoice.post"}
_MODELS = ("account.payment.term", "account.payment.term.line", "account.move", "account.move.line",
           "res.currency", "res.currency.rate", "account.tax", "account.tax.repartition.line")


def _root():
    return Path(__file__).resolve().parents[2]


def _summary(alias, database):
    return {"alias":alias,"database":database,"company_id":1,"user_id":5,"business_su":False,
            "capabilities":sorted(_WRITES | _READS | _SETUP),"immediate_replays":6,
            "native_shared_and_owned_copy_verified":True,"native_line_ids_and_parent_constraints_verified":True,
            "native_failed_atomic_updates_rolled_back":True,"native_computed_foreign_currency_schedule_verified":True,
            "native_early_discount_schedule_verified":True,"posted_entry_unchanged_by_configuration":True,
            "native_usage_keyset_and_archived_read_verified":True,"native_referenced_deletion_denied":True,
            "company_parent_and_missing_target_denial_verified":True,"rollback_verified":True,
            "temporary_groups_rolled_back":True,"execution":"in_process_cli_real_orm"}


if pytest is not None:
    @pytest.mark.integration
    def test_payment_term_processing_rolls_back_per_alias():
        config_path,runtime=lifecycle._enabled_runtime(_ALLOW_ENV)
        run_id=uuid.uuid4()
        for alias in lifecycle._ALIASES:
            command,timeout=lifecycle._worker_command(alias,run_id,config_path,runtime)
            command[1]=str(Path(__file__).resolve())
            environment=os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"]="1"
            environment["PYTHONPATH"]=os.pathsep.join(filter(None,(str(_root()/"src"),sysconfig.get_path("purelib"),environment.get("PYTHONPATH"))))
            completed=subprocess.run(command,cwd=_root(),env=environment,text=True,capture_output=True,
                                     check=False,timeout=max(timeout,900))
            assert completed.returncode==0,completed.stdout+completed.stderr
            assert json.loads(completed.stdout)==_summary(alias,lifecycle._DATABASES[alias])
            print(completed.stdout.strip(),flush=True)


def _exercise(admin,client,alias,run_id,marker):
    from odoo import fields

    from odoo_accounting_cli_v4.bridge import core_writes_runtime as native

    env=client.env
    ids=lifecycle._fixture_ids(admin,alias)
    replays=0
    def fixture(model,values):
        record=admin[model].create(values)
        client.tracked[model].add(record.id)
        if model=="account.payment.term": client.tracked["account.payment.term.line"].update(record.line_ids.ids)
        if model=="account.tax": client.tracked["account.tax.repartition.line"].update((record.invoice_repartition_line_ids | record.refund_repartition_line_ids).ids)
        return record
    def write(cap,params,*,replay=True):
        from odoo_accounting_cli_v4.capabilities.core_writes import (
            _expected_idempotency_key,
            validate_core_write_request,
        )

        nonlocal replays
        client.last_runtime_failure=None
        normalized=validate_core_write_request(cap,core._request(alias,run_id,cap,params))[2]
        try:
            if _expected_idempotency_key(cap,normalized,1) is None:
                assert cap in _SETUP and replay is False
                key=f"{cap}:{run_id.hex}:{lifecycle._canonical_digest(normalized)[:32]}"
                reply=core._cli(client,alias,run_id,cap,params,key=key)
                assert reply["idempotent_replay"] is False
                value=reply["result"]
            else:
                value=shared._write(client,alias,run_id,cap,params,replay=replay)
        except AssertionError:
            if client.last_runtime_failure is not None: raise client.last_runtime_failure
            raise
        if cap in _WRITES and replay: replays+=1
        if value["model"]=="account.payment.term" and value["state"]!="deleted":
            client.tracked["account.payment.term.line"].update(env["account.payment.term"].browse(value["id"]).line_ids.ids)
        if value["model"]=="account.move":
            client.tracked["account.move.line"].update(env["account.move"].browse(value["id"]).line_ids.ids)
        return value
    def read(cap,params):
        client.last_runtime_failure=None
        try: return shared._read(client,alias,run_id,cap,params)
        except AssertionError:
            if client.last_runtime_failure is not None: raise client.last_runtime_failure
            raise
    def denied(cap,params,code):
        client.last_runtime_failure=None
        try: shared._write(client,alias,run_id,cap,params,replay=False)
        except AssertionError: assert getattr(client.last_runtime_failure,"code",None)==code
        else: raise RuntimeError("A native payment-term/company denial succeeded")
    def missing_schedule(invoice_id):
        from odoo_accounting_cli_v4 import cli
        from odoo_accounting_cli_v4.bridge.core_object_reads import (
            OdooCoreObjectReadPort,
        )

        cap="invoice.payment_schedule.inspect"
        stdout,stderr=io.StringIO(),io.StringIO()
        code=cli.main(["read",cap,"--request","-"],stdin=io.StringIO(json.dumps(core._request(alias,run_id,cap,{"invoice_id":invoice_id}))),
                      stdout=stdout,stderr=stderr,port_factory=lambda *args:OdooCoreObjectReadPort(client))
        reply=json.loads(stdout.getvalue())
        assert code==4 and not stderr.getvalue() and reply["error"]["code"]=="record_not_found" and reply["odoo"]["user_id"]==5
    def snapshot(term): return [(row.id,native._normalized_payment_term_line(row)) for row in term.line_ids]
    def schedule(invoice_id): return read("invoice.payment_schedule.inspect",{"invoice_id":invoice_id})
    today=fields.Date.context_today(env.user)
    currency=fixture("res.currency",{"name":"V4P","symbol":"V4P","rounding":0.01,"active":True})
    fixture("res.currency.rate",{"currency_id":currency.id,"company_id":1,"name":today,"rate":0.25})
    tax=fixture("account.tax",{"name":marker,"company_id":1,"type_tax_use":"sale","amount_type":"percent","amount":10,"price_include_override":"tax_excluded"})
    base={"value":"percent","value_amount":"100","delay_type":"days_after","nb_days":30,"days_next_month":10}
    shared_term=fixture("account.payment.term",{"name":marker+"-SHARED","company_id":False,"early_pay_discount_computation":"excluded"})
    foreign=admin["account.payment.term"].with_company(2).create({"name":marker+"-FOREIGN","company_id":2})
    client.tracked["account.payment.term"].add(foreign.id)
    client.tracked["account.payment.term.line"].update(foreign.line_ids.ids)
    outside=fixture("account.payment.term",{"name":marker+"-OUTSIDE","company_id":1})
    term_id=write("payment_term.create",{"name":marker,"company_id":1,"sequence":10,"note":"<p>Installments</p>","display_on_invoice":True,
        "early_discount":False,"discount_percentage":"2","discount_days":10,"early_pay_discount_computation":"excluded",
        "lines":[{**base,"value_amount":"40","nb_days":10},{**base,"value_amount":"60","nb_days":30}]},replay=False)["id"]
    term=env["account.payment.term"].browse(term_id)
    first_id,last_id=term.line_ids.ids
    copy_id=write("payment_term.duplicate",{"payment_term_id":term_id,"name":marker+"-COPY"})["id"]
    copied=env["account.payment.term"].browse(copy_id)
    copy_line_ids=copied.line_ids.ids
    assert native._payment_term_copy_values(copied)==native._payment_term_copy_values(term)
    assert not set(copied.line_ids.ids)&set(term.line_ids.ids)
    shared_copy_id=write("payment_term.duplicate",{"payment_term_id":shared_term.id,"name":marker+"-SHARED-COPY"})["id"]
    shared_copy=env["account.payment.term"].browse(shared_copy_id)
    assert shared_copy.company_id.id==1 and not shared_term.company_id
    assert native._payment_term_copy_values(shared_copy)==native._payment_term_copy_values(shared_term)
    def invoice(reference,currency_id):
        invoice_id=write("customer_invoice.create",{"partner_id":ids["customer"],"journal_id":ids["sale_journal"],"invoice_date":today.isoformat(),
            "currency_id":currency_id,"payment_term_id":term_id,"reference":reference,
            "lines":[{"name":marker,"account_id":ids["income"],"quantity":"1","price_unit":"100","tax_ids":[tax.id]}]},replay=False)["id"]
        return env["account.move"].browse(invoice_id)
    billed=invoice(marker+"-POST",currency.id)
    before=schedule(billed.id)
    assert before["currency_id"]==currency.id and before["company_currency_id"]==billed.company_id.currency_id.id
    assert before["currency_id"]!=before["company_currency_id"] and before["payment_term_id"]==term_id and len(before["lines"])==2
    assert sorted(Decimal(row["amount_currency"]) for row in before["lines"])==[Decimal(44),Decimal(66)]
    assert sum(Decimal(row["balance"]) for row in before["lines"])==Decimal(str(billed.amount_total_signed))
    write("invoice.post",{"move_id":billed.id},replay=False)
    posted=[(row.id,row.date_maturity,row.balance,row.amount_currency,row.amount_residual,row.amount_residual_currency) for row in billed.line_ids]
    assert schedule(billed.id)["state"]=="posted"
    temporary_id=write("payment_term.line.create",{"payment_term_id":term_id,"line":{**base,"value":"fixed","value_amount":"-7.5","nb_days":-1}})["source_id"]
    assert term.line_ids.ids==[first_id,last_id,temporary_id]
    write("payment_term.line.update",{"payment_term_id":term_id,"line_id":first_id,"changes":{"delay_type":"days_end_of_month_on_the","nb_days":0,"days_next_month":5}})
    write("payment_term.lines.update",{"payment_term_id":term_id,"lines":[{"line_id":last_id,"changes":{"value_amount":"75"}},
        {"line_id":first_id,"changes":{"value_amount":"25"}}]})
    assert term.line_ids.ids==[first_id,last_id,temporary_id]
    assert [row.value_amount for row in term.line_ids[:2]]==[25,75]
    assert native._payment_term_copy_values(copied)["lines"][0]["value_amount"]=="40"
    current=snapshot(term)
    denied("payment_term.lines.update",{"payment_term_id":term_id,"lines":[{"line_id":first_id,"changes":{"value_amount":"20"}},
        {"line_id":last_id,"changes":{"value_amount":"70"}}]},"business_rule_error")
    assert snapshot(term)==current
    denied("payment_term.line.update",{"payment_term_id":term_id,"line_id":first_id,"changes":{"value_amount":"20"}},"business_rule_error")
    assert snapshot(term)==current
    denied("payment_term.line.delete",{"payment_term_id":term_id,"line_id":first_id},"business_rule_error")
    assert snapshot(term)==current
    denied("payment_term.lines.update",{"payment_term_id":term_id,"lines":[{"line_id":first_id,"changes":{"nb_days":1}},
        {"line_id":outside.line_ids.id,"changes":{"nb_days":2}}]},"record_not_found")
    assert snapshot(term)==current
    denied("payment_term.line.create",{"payment_term_id":foreign.id,"line":base},"record_not_found")
    denied("payment_term.delete",{"payment_term_id":foreign.id},"record_not_found")
    denied("payment_term.line.create",{"payment_term_id":shared_term.id,"line":base},"record_not_found")
    denied("payment_term.duplicate",{"payment_term_id":term_id,"name":marker+"-COPY"},"idempotency_conflict")
    write("payment_term.line.delete",{"payment_term_id":term_id,"line_id":temporary_id},replay=False)
    assert term.line_ids.ids==[first_id,last_id]
    denied("payment_term.line.delete",{"payment_term_id":term_id,"line_id":temporary_id},"record_not_found")
    write("payment_term.lines.update",{"payment_term_id":term_id,"lines":[{"line_id":first_id,"changes":{"value_amount":"0"}},
        {"line_id":last_id,"changes":{"value_amount":"100"}}]})
    write("payment_term.line.delete",{"payment_term_id":term_id,"line_id":first_id},replay=False)
    assert term.line_ids.ids==[last_id] and term.line_ids.value_amount==100
    write("payment_term.update",{"payment_term_id":term_id,"early_discount":True,"discount_percentage":"2","discount_days":10,
          "early_pay_discount_computation":"excluded"},replay=False)
    discounted=invoice(marker+"-DISCOUNT",billed.company_id.currency_id.id)
    discount=schedule(discounted.id)
    assert len(discount["lines"])==1 and discount["lines"][0]["discount_date"] and discount["lines"][0]["discount_amount_currency"]=="108"
    write("invoice.post",{"move_id":discounted.id},replay=False)
    denied("payment_term.line.create",{"payment_term_id":term_id,"line":{**base,"value":"fixed","value_amount":"1"}},"business_rule_error")
    assert term.line_ids.ids==[last_id] and term.early_discount
    assert [(row.id,row.date_maturity,row.balance,row.amount_currency,row.amount_residual,row.amount_residual_currency) for row in billed.line_ids]==posted
    rows,cursor=[],None
    while True:
        page=read("payment_term.usage_moves.list",{"payment_term_id":term_id,"limit":1,"cursor":cursor})
        rows.extend(page["items"])
        if not page["has_more"]: break
        cursor=page["next_cursor"]
    assert {row["id"] for row in rows}=={billed.id,discounted.id} and len(rows)==2
    assert all(row["invoice_payment_term_id"]==term_id and row["company_id"]==1 and row["state"]=="posted" for row in rows)
    write("payment_term.archive",{"payment_term_id":term_id},replay=False)
    assert len(read("payment_term.usage_moves.list",{"payment_term_id":term_id})["items"])==2
    denied("payment_term.delete",{"payment_term_id":term_id},"business_rule_error")
    assert term.exists() and len(term.line_ids)==1 and billed.state==discounted.state=="posted"
    removed=write("payment_term.delete",{"payment_term_id":copy_id},replay=False)
    assert removed["state"]=="deleted" and not copied.exists() and not env["account.payment.term.line"].browse(copy_line_ids).exists()
    denied("payment_term.delete",{"payment_term_id":copy_id},"record_not_found")
    write("payment_term.delete",{"payment_term_id":shared_copy_id},replay=False)
    assert not shared_copy.exists() and shared_term.exists() and foreign.exists() and outside.exists()
    assert read("payment_term.usage_moves.list",{"payment_term_id":copy_id})["items"]==[]
    assert read("payment_term.usage_moves.list",{"payment_term_id":foreign.id})["items"]==[]
    missing_schedule(1_999_999_999)
    assert replays==6 and client.capabilities==_WRITES | _READS | _SETUP


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
    marker=f"ODACV4-PAYTERM-{args.alias}-{args.run_id.hex}"
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
            for model in ("account.payment.term","account.tax"):
                assert not verify[model].with_context(active_test=False).search_count([("name","ilike",marker)])
            assert not verify["account.move.line"].search_count([("name","ilike",marker)])
            for group_id,members in baseline.items(): assert shared._direct_group(verify_cursor,group_id)==members
        finally: verify_cursor.rollback()
    if failure is not None: raise failure
    print(json.dumps(_summary(args.alias,args.database),sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(_live_worker())
