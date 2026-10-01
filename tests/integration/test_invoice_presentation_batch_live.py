"""One guarded rollback-only native invoice presentation/fiscal workflow."""

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
import test_move_processing_batch_live as processing
import test_payment_bank_capability_batch_live as core
import test_report_budget_write_batch_live as shared

try:
    import pytest
except ModuleNotFoundError:
    if "--live-worker" not in sys.argv:
        raise
    pytest = None

_ALLOW_ENV = "ODACV4_ALLOW_INVOICE_PRESENTATION_SMOKE"
_GROUP = "account.group_account_manager"
_WRITES = {"invoice.presentation_settings.update", "invoice.layout_line.create",
           "invoice.layout_line.update", "invoice.layout_line.delete",
           "invoice.lines.resequence", "invoice.fiscal_position.refresh"}
_READS = {"invoice.presentation_settings.get", "invoice.layout_line.list"}
_SETUP = {"customer_invoice.create", "invoice.update", "invoice.post"}
_EXTRA_MODELS = ("product.product", "product.template", "res.partner", "account.tax",
                 "account.tax.repartition.line", "account.tax.group", "account.fiscal.position",
                 "account.fiscal.position.account")


def _root():
    return Path(__file__).resolve().parents[2]


def _summary(alias, database):
    return {"alias":alias,"database":database,"company_id":1,"user_id":5,"business_su":False,
            "capabilities":sorted(_WRITES|_READS|_SETUP),"immediate_replays":7,
            "native_html_sanitization_verified":True,"native_layout_zero_accounting_verified":True,
            "native_parent_and_order_verified":True,"scoped_keyset_pagination_verified":True,
            "historical_empty_and_long_layout_labels_verified":True,
            "native_price_tax_account_recomputation_verified":True,
            "layout_keeps_financial_totals":True,"product_line_delete_rejected":True,
            "posted_and_company_boundaries_verified":True,"rollback_verified":True,
            "temporary_group_rolled_back":True,"execution":"in_process_cli_real_orm"}


if pytest is not None:
    @pytest.mark.integration
    def test_invoice_presentation_rolls_back_per_alias():
        config_path,runtime=lifecycle._enabled_runtime(_ALLOW_ENV)
        run_id=uuid.uuid4()
        for alias in lifecycle._ALIASES:
            command,timeout=lifecycle._worker_command(alias,run_id,config_path,runtime)
            command[1]=str(Path(__file__).resolve())
            environment=os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"]="1"
            environment["PYTHONPATH"]=os.pathsep.join(filter(None,(str(_root()/"src"),sysconfig.get_path("purelib"),environment.get("PYTHONPATH"))))
            completed=subprocess.run(command,cwd=_root(),env=environment,text=True,capture_output=True,check=False,timeout=max(timeout,900))
            assert completed.returncode==0,completed.stdout+completed.stderr
            result=json.loads(completed.stdout)
            assert result==_summary(alias,lifecycle._DATABASES[alias])
            print(completed.stdout.strip(),flush=True)


class _Client(processing._Client):
    def __init__(self, env):
        super().__init__(env)
        self.tracked.update({model:set() for model in _EXTRA_MODELS})


def _exercise(client,alias,run_id,marker,fixture):
    from odoo import fields

    env=client.env
    ids=lifecycle._fixture_ids(env,alias)
    today=fields.Date.context_today(env.user).isoformat()
    move_id=core._cli(client,alias,run_id,"customer_invoice.create",{
        "partner_id":ids["customer"],"journal_id":ids["sale_journal"],"date":today,
        "invoice_date":today,"currency_id":ids["currency"],"reference":marker,
        "lines":[{"name":marker,"account_id":ids["income"],"product_id":fixture["product"],
                  "quantity":"1","price_unit":"7","discount":"0","tax_ids":[]}],
    },key=marker+"-invoice")["result"]["id"]
    move=env["account.move"].browse(move_id)
    def read(cap,params=None):
        client.last_runtime_failure=None
        try:
            return shared._read(client,alias,run_id,cap,{"move_id":move_id,**(params or {})})
        except AssertionError:
            if client.last_runtime_failure is not None: raise client.last_runtime_failure
            raise
    def write(cap,params,replay=True):
        client.last_runtime_failure=None
        try:
            return shared._write(client,alias,run_id,cap,{"move_id":move_id,**params},replay=replay)
        except AssertionError:
            if cap=="invoice.fiscal_position.refresh" and client.last_runtime_failure is not None:
                raise client.last_runtime_failure
            raise
    write("invoice.presentation_settings.update",{"changes":{
        "partner_shipping_id":fixture["shipping"],"invoice_user_id":5,
        "narration":"<p>"+marker+" terms</p><script>bad()</script>",
    }})
    presentation=read("invoice.presentation_settings.get")
    assert presentation["partner_shipping_id"]==fixture["shipping"] and presentation["invoice_user_id"]==5
    assert marker+" terms" in presentation["narration"] and "<script" not in presentation["narration"].lower()
    before_total=move.amount_total
    layout=[]
    for kind,name,sequence in (("line_section","Services",10),("line_subsection","Details",20),("line_note","Terms note",200)):
        created=write("invoice.layout_line.create",{"line":{"display_type":kind,"name":marker+"-"+name,
            "sequence":sequence,"collapse_prices":False,"collapse_composition":False}})
        layout.append(created["source_id"])
    section,subsection,note=layout
    write("invoice.layout_line.update",{"line_id":section,"changes":{"name":marker+"-Revised section","collapse_prices":True}})
    product=move.invoice_line_ids.filtered(lambda line:line.display_type=="product")
    assert len(product)==1 and product.parent_id.id==subsection
    for line in move.invoice_line_ids.filtered(lambda line:line.id in layout):
        assert not line.account_id and line.balance==line.amount_currency==line.debit==line.credit==0
    rows=[]
    cursor=None
    while True:
        page=read("invoice.layout_line.list",{"limit":1,"cursor":cursor})
        rows.extend(page["items"])
        if not page["has_more"]: break
        cursor=page["next_cursor"]
    assert {row["id"] for row in rows}==set(layout) and len(rows)==3
    assert next(row for row in rows if row["id"]==subsection)["parent_id"]==section
    write("invoice.lines.resequence",{"line_ids":[section,product.id,subsection,note]})
    assert move.invoice_line_ids.sorted(lambda line:(line.sequence,line.id)).ids==[section,product.id,subsection,note]
    assert product.parent_id.id==section
    for cap,params,code in (
        ("invoice.layout_line.delete",{"line_id":product.id},"record_not_found"),
        ("invoice.lines.resequence",{"line_ids":[section,subsection,note]},"business_rule_error"),
        ("invoice.layout_line.update",{"move_id":fixture["foreign_move"],"line_id":fixture["foreign_line"],"changes":{"name":"Denied"}},"record_not_found"),
    ):
        try: write(cap,params,replay=False)
        except AssertionError: assert getattr(client.last_runtime_failure,"code",None)==code
        else: raise RuntimeError("An invalid invoice target or line selection succeeded")
    assert read("invoice.layout_line.list",{"move_id":fixture["foreign_move"]})["items"]==[]
    write("invoice.layout_line.delete",{"line_id":note},replay=False)
    assert not env["account.move.line"].browse(note).exists()
    assert len(move.invoice_line_ids)==3 and move.amount_total==before_total
    historical=[]
    for name in (False,"Historical native note "*50):
        line=env["account.move.line"].create({"move_id":move_id,"display_type":"line_note","name":name,"sequence":999})
        client.tracked["account.move.line"].add(line.id)
        historical.append(line.id)
    existing={row["id"]:row for row in read("invoice.layout_line.list")["items"]}
    assert existing[historical[0]]["name"] is None and len(existing[historical[1]]["name"])>500
    for line_id in historical: write("invoice.layout_line.delete",{"line_id":line_id},replay=False)
    assert move.amount_total==before_total
    write("invoice.update",{"changes":{"fiscal_position_id":fixture["position"]}},replay=False)
    assert Decimal(str(product.price_unit))==Decimal(7)
    write("invoice.fiscal_position.refresh",{})
    product.invalidate_recordset()
    move.invalidate_recordset()
    assert Decimal(str(product.price_unit))==Decimal(25) and product.account_id.id==fixture["mapped_account"]
    assert product.tax_ids.ids==[fixture["mapped_tax"]]
    assert Decimal(str(move.amount_tax))==Decimal("2.5") and Decimal(str(move.amount_total))==Decimal("27.5")
    assert env.company.currency_id.is_zero(sum(move.line_ids.mapped("balance")))
    assert read("invoice.presentation_settings.get")["fiscal_position_id"]==fixture["position"]
    core._cli(client,alias,run_id,"invoice.post",{"move_id":move_id},key=f"invoice.post:{move_id}")
    try: write("invoice.layout_line.update",{"line_id":section,"changes":{"name":"Denied after posting"}},replay=False)
    except AssertionError: assert getattr(client.last_runtime_failure,"code",None)=="state_conflict"
    else: raise RuntimeError("A posted presentation edit succeeded")
    assert client.capabilities==_WRITES|_READS|_SETUP


def _fixture(admin,client,alias,run_id,marker):
    from odoo import fields

    def create(model,values):
        record=admin[model].create(values)
        client.tracked[model].add(record.id)
        return record
    ids=lifecycle._fixture_ids(admin,alias)
    account=create("account.account",{"name":marker,"code":"L"+run_id.hex[:12],"account_type":"income","company_ids":[(6,0,[1])]})
    group=create("account.tax.group",{"name":marker,"company_id":1})
    tax=create("account.tax",{"name":marker+"-source","company_id":1,"type_tax_use":"sale","amount_type":"percent","amount":5,"tax_group_id":group.id})
    mapped=create("account.tax",{"name":marker+"-mapped","company_id":1,"type_tax_use":"sale","amount_type":"percent","amount":10,"tax_group_id":group.id,"original_tax_ids":[(6,0,[tax.id])]})
    for row in (tax,mapped): client.tracked["account.tax.repartition.line"].update((row.invoice_repartition_line_ids|row.refund_repartition_line_ids).ids)
    position=create("account.fiscal.position",{"name":marker,"company_id":1,"tax_ids":[(6,0,[mapped.id])]})
    create("account.fiscal.position.account",{"position_id":position.id,"account_src_id":ids["income"],"account_dest_id":account.id})
    product=create("product.product",{"name":marker,"type":"service","company_id":1,"list_price":25,"taxes_id":[(6,0,[tax.id])],"supplier_taxes_id":[(5,0,0)],"property_account_income_id":ids["income"]})
    client.tracked["product.template"].update(product.product_tmpl_id.ids)
    shipping=create("res.partner",{"name":marker,"type":"delivery","parent_id":ids["customer"],"company_id":1})
    journal=admin["account.journal"].with_company(2).create({"name":marker+"-FOREIGN","code":"L"+run_id.hex[:4],"type":"sale","company_id":2})
    client.tracked["account.journal"].add(journal.id)
    foreign=admin["account.move"].with_company(2).create({"ref":marker+"-FOREIGN","journal_id":journal.id,"company_id":2,"move_type":"out_invoice","date":fields.Date.context_today(admin.user),"invoice_line_ids":[(0,0,{"display_type":"line_note","name":marker+"-FOREIGN"})]})
    client.tracked["account.move"].add(foreign.id)
    client.tracked["account.move.line"].update(foreign.line_ids.ids)
    return {"product":product.id,"shipping":shipping.id,"position":position.id,"mapped_account":account.id,
            "mapped_tax":mapped.id,"foreign_move":foreign.id,"foreign_line":foreign.invoice_line_ids.id}


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
    marker=f"ODACV4-INVOICE-LAYOUT-{args.alias}-{args.run_id.hex}"
    tracked={}
    group_id=baseline_group=None
    failure=None
    try:
        context={"allowed_company_ids":[1],"lang":"en_US","tz":"Asia/Shanghai","tracking_disable":True,"mail_create_nosubscribe":True,"mail_notrack":True}
        admin=api.Environment(cursor,SUPERUSER_ID,context)
        user=admin["res.users"].browse(5).exists()
        assert user.active and user.login==lifecycle._USER_LOGIN and 1 in user.company_ids.ids
        group_id=admin.ref(_GROUP).id
        baseline_group=shared._direct_group(cursor,group_id)
        if not user.has_group(_GROUP): user.write({"group_ids":[Command.link(group_id)]})
        env=api.Environment(cursor,5,context)
        assert not env.su and env.user.has_group(_GROUP)
        client=_Client(env)
        tracked=client.tracked
        fixture=_fixture(admin,client,args.alias,args.run_id,marker)
        _exercise(client,args.alias,args.run_id,marker,fixture)
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
            for model in ("res.partner","account.tax","account.tax.group","account.fiscal.position","product.product","account.account","account.journal"):
                assert not verify[model].with_context(active_test=False).search_count([("name","ilike",marker)])
            assert not verify["account.move"].search_count([("ref","ilike",marker)])
            if group_id is not None: assert shared._direct_group(verify_cursor,group_id)==baseline_group
        finally: verify_cursor.rollback()
    if failure is not None: raise failure
    print(json.dumps(_summary(args.alias,args.database),sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(_live_worker())
