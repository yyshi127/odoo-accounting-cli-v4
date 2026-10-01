"""One rollback-only native tax workflow; no external filing or payment."""

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

_ALLOW_ENV = "ODACV4_ALLOW_TAX_PROCESSING_SMOKE"
_GROUPS = ("account.group_account_manager",)
_WRITES = {"tax.delete", "tax.repartition_line.update", "tax.repartition_pair.create", "tax.repartition_pair.delete",
           "tax.repartition_lines.update", "tax.repartition_lines.resequence"}
_READS = {"tax.processing_settings.get", "tax.usage_lines.list"}
_SETUP = {"tax.create", "tax.archive", "customer_invoice.create", "invoice.post", "customer_credit_note.create"}
_MODELS = ("account.tax", "account.tax.repartition.line", "account.tax.group", "account.account", "account.account.tag",
           "account.move", "account.move.line", "account.partial.reconcile", "account.full.reconcile")


def _root():
    return Path(__file__).resolve().parents[2]


def _summary(alias, database):
    return {"alias": alias, "database": database, "company_id": 1, "user_id": 5, "business_su": False,
            "capabilities": sorted(_WRITES | _READS | _SETUP), "immediate_replays": 8,
            "native_pair_create_delete_and_fresh_identity_verified": True,
            "native_atomic_factors_and_complete_order_verified": True,
            "native_signed_reverse_charge_invoice_and_refund_verified": True,
            "native_failed_mutations_rolled_back": True, "native_computed_closing_flag_verified": True,
            "native_scoped_usage_and_archived_read_verified": True,
            "native_referenced_deletions_denied": True, "posted_entries_unchanged_by_configuration": True,
            "company_parent_and_missing_target_denials_verified": True,
            "rollback_verified": True, "temporary_groups_rolled_back": True, "execution": "in_process_cli_real_orm"}


if pytest is not None:
    @pytest.mark.integration
    def test_tax_processing_rolls_back_per_alias():
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

    from odoo_accounting_cli_v4.bridge import core_writes_runtime as native
    from odoo_accounting_cli_v4.capabilities.core_writes import (
        _expected_idempotency_key,
        validate_core_write_request,
    )

    env = client.env
    ids = lifecycle._fixture_ids(admin, alias)
    replays = 0
    def fixture(model, values):
        record = admin[model].create(values)
        client.tracked[model].add(record.id)
        if model == "account.tax": client.tracked["account.tax.repartition.line"].update(record.repartition_line_ids.ids)
        return record
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
            else:
                value = shared._write(client, alias, run_id, cap, params, replay=replay)
        except AssertionError:
            if client.last_runtime_failure is not None: raise client.last_runtime_failure
            raise
        if cap in _WRITES and replay: replays += 1
        if value["model"] == "account.tax" and value["state"] != "deleted":
            client.tracked["account.tax.repartition.line"].update(env["account.tax"].browse(value["id"]).repartition_line_ids.ids)
        if value["model"] == "account.move":
            rows = env["account.move"].browse(value["id"]).line_ids
            client.tracked["account.move.line"].update(rows.ids)
            client.tracked["account.partial.reconcile"].update((rows.matched_debit_ids | rows.matched_credit_ids).ids)
            client.tracked["account.full.reconcile"].update(rows.full_reconcile_id.ids)
        return value
    def read(cap, params):
        client.last_runtime_failure = None
        try: return shared._read(client, alias, run_id, cap, params)
        except AssertionError:
            if client.last_runtime_failure is not None: raise client.last_runtime_failure
            raise
    def denied(cap, params, code):
        client.last_runtime_failure = None
        try: shared._write(client, alias, run_id, cap, params, replay=False)
        except AssertionError: assert getattr(client.last_runtime_failure, "code", None) == code
        else: raise RuntimeError("A native tax/company denial succeeded")
    def missing_settings(tax_id):
        from odoo_accounting_cli_v4 import cli
        from odoo_accounting_cli_v4.bridge.core_object_reads import (
            OdooCoreObjectReadPort,
        )
        cap = "tax.processing_settings.get"
        stdout, stderr = io.StringIO(), io.StringIO()
        code = cli.main(["read", cap, "--request", "-"], stdin=io.StringIO(json.dumps(core._request(alias, run_id, cap, {"tax_id": tax_id}))),
                        stdout=stdout, stderr=stderr, port_factory=lambda *args: OdooCoreObjectReadPort(client))
        reply = json.loads(stdout.getvalue())
        assert code == 4 and not stderr.getvalue() and reply["error"]["code"] == "record_not_found" and reply["odoo"]["user_id"] == 5
    def snapshot(tax): return [(row.id, row.document_type, native._normalized_tax_repartition_line(row)) for row in tax.repartition_line_ids]
    def settings(): return read("tax.processing_settings.get", {"tax_id": tax.id})
    today = fields.Date.context_today(env.user)
    tax_id = write("tax.create", {"name": marker, "type_tax_use": "sale", "amount_type": "percent", "amount": 10,
                                  "price_include_override": "tax_excluded"}, replay=False)["id"]
    tax = env["account.tax"].browse(tax_id)
    inv_base, inv_tax = tax.invoice_repartition_line_ids.sorted(lambda row: (row.sequence, row.id)).ids
    ref_base, ref_tax = tax.refund_repartition_line_ids.sorted(lambda row: (row.sequence, row.id)).ids
    initial = settings()
    assert initial["is_used"] is False and initial["price_include"] is False and initial["price_include_override"] == "tax_excluded"
    tag = fixture("account.account.tag", {"name": marker, "applicability": "taxes", "country_id": tax.country_id.id})
    wrong_tag = fixture("account.account.tag", {"name": marker+"-WRONG", "applicability": "accounts"})
    closing_account = fixture("account.account", {"name": marker, "code": "V4T"+run_id.hex[:8], "account_type": "liability_current", "company_ids": [(6, 0, [1])]})
    foreign_group = fixture("account.tax.group", {"name": marker+"-FOREIGN", "company_id": 2, "country_id": tax.country_id.id})
    foreign = admin["account.tax"].with_company(2).create({"name": marker+"-FOREIGN", "company_id": 2, "country_id": tax.country_id.id,
        "tax_group_id": foreign_group.id, "type_tax_use": "sale", "amount": 10})
    client.tracked["account.tax"].add(foreign.id)
    client.tracked["account.tax.repartition.line"].update(foreign.repartition_line_ids.ids)
    line = {"sequence": 30, "repartition_type": "tax", "factor_percent": "0", "account_id": ids["income"], "tag_ids": [tag.id], "use_in_tax_closing": False}
    pair = {"tax_id": tax.id, "invoice_line": line, "refund_line": line}
    before = set(tax.repartition_line_ids.ids)
    write("tax.repartition_pair.create", pair)
    first_pair = {row.document_type: row.id for row in tax.repartition_line_ids if row.id not in before}
    write("tax.repartition_pair.delete", {"tax_id": tax.id, "invoice_line_id": first_pair["invoice"], "refund_line_id": first_pair["refund"]}, replay=False)
    assert set(tax.repartition_line_ids.ids) == before
    denied("tax.repartition_pair.delete", {"tax_id": tax.id, "invoice_line_id": first_pair["invoice"], "refund_line_id": first_pair["refund"]}, "record_not_found")
    write("tax.repartition_pair.create", pair)
    extra = {row.document_type: row.id for row in tax.repartition_line_ids if row.id not in before}
    assert not set(extra.values()) & set(first_pair.values())
    write("tax.repartition_line.update", {"tax_id": tax.id, "line_id": inv_tax, "changes": {"use_in_tax_closing": True}})
    updates = [{"line_id": row_id, "changes": {"factor_percent": amount}} for row_id, amount in
               ((inv_tax, "40"), (ref_tax, "40"), (extra["invoice"], "60"), (extra["refund"], "60"))]
    write("tax.repartition_lines.update", {"tax_id": tax.id, "lines": list(reversed(updates))})
    order = {"tax_id": tax.id, "invoice_line_ids": [inv_base, extra["invoice"], inv_tax], "refund_line_ids": [ref_base, extra["refund"], ref_tax]}
    write("tax.repartition_lines.resequence", order)
    assert settings()["invoice_repartition_line_ids"] == order["invoice_line_ids"] and settings()["refund_repartition_line_ids"] == order["refund_line_ids"]
    negative = {**line, "sequence": 40, "factor_percent": "-100"}
    write("tax.repartition_pair.create", {"tax_id": tax.id, "invoice_line": negative, "refund_line": negative})
    assert settings()["has_negative_factor"] is True
    current = snapshot(tax)
    denied("tax.repartition_line.update", {"tax_id": tax.id, "line_id": inv_tax, "changes": {"factor_percent": "20"}}, "business_rule_error")
    assert snapshot(tax) == current
    failed = [{"line_id": row_id, "changes": {"factor_percent": "20" if row_id in {inv_tax, ref_tax} else "70"}} for row_id in (inv_tax, ref_tax, extra["invoice"], extra["refund"])]
    denied("tax.repartition_lines.update", {"tax_id": tax.id, "lines": failed}, "business_rule_error")
    assert snapshot(tax) == current
    denied("tax.repartition_lines.resequence", {**order, "invoice_line_ids": [inv_base, inv_tax]}, "record_not_found")
    denied("tax.repartition_lines.update", {"tax_id": tax.id, "lines": [{"line_id": inv_tax, "changes": {"sequence": 2}},
        {"line_id": foreign.invoice_repartition_line_ids[0].id, "changes": {"sequence": 3}}]}, "record_not_found")
    denied("tax.repartition_line.update", {"tax_id": tax.id, "line_id": inv_tax, "changes": {"tag_ids": [wrong_tag.id]}}, "record_not_found")
    denied("tax.repartition_pair.delete", {"tax_id": tax.id, "invoice_line_id": ref_tax, "refund_line_id": inv_tax}, "record_not_found")
    denied("tax.delete", {"tax_id": foreign.id}, "record_not_found")
    assert snapshot(tax) == current
    billed_id = write("customer_invoice.create", {"partner_id": ids["customer"], "journal_id": ids["sale_journal"], "currency_id": env.company.currency_id.id, "invoice_date": today.isoformat(), "reference": marker,
        "lines": [{"name": marker, "account_id": ids["income"], "quantity": "1", "price_unit": "100", "tax_ids": [tax.id]}]}, replay=False)["id"]
    billed = env["account.move"].browse(billed_id)
    write("invoice.post", {"move_id": billed.id}, replay=False)
    refunded_id = write("customer_credit_note.create", {"move_id": billed.id, "date": today.isoformat(), "reason": marker}, replay=False)["id"]
    refunded = env["account.move"].browse(refunded_id)
    write("invoice.post", {"move_id": refunded.id}, replay=False)
    assert billed.state == refunded.state == "posted" and refunded.move_type == "out_refund"
    assert billed.amount_total == refunded.amount_total == 100
    for invoice, kind in ((billed, "invoice"), (refunded, "refund")):
        tax_lines = invoice.line_ids.filtered(lambda row: row.tax_line_id.id == tax.id)
        assert len(tax_lines) == 3 and sorted(abs(row.balance) for row in tax_lines) == [4, 6, 10]
        assert sum(row.balance for row in tax_lines) == 0
        assert all(row.tax_repartition_line_id.document_type == kind for row in tax_lines)
    assert settings()["is_used"] is True
    def ledger(): return [(row.id, row.account_id.id, row.date_maturity, row.balance, row.amount_currency, row.amount_residual,
                          row.tax_repartition_line_id.id, row.tax_line_id.id, row.tax_ids.ids) for invoice in (billed, refunded) for row in invoice.line_ids]
    posted = ledger()
    write("tax.repartition_line.update", {"tax_id": tax.id, "line_id": inv_tax, "changes": {"use_in_tax_closing": False}})
    write("tax.repartition_line.update", {"tax_id": tax.id, "line_id": inv_tax, "changes": {"account_id": closing_account.id}})
    assert env["account.tax.repartition.line"].browse(inv_tax).use_in_tax_closing is True
    assert ledger() == posted
    expected_usage = {row.id for invoice in (billed, refunded) for row in invoice.line_ids
                      if tax.id in row.tax_ids.ids or row.tax_line_id.id == tax.id or row.group_tax_id.id == tax.id}
    rows, cursor = [], None
    while True:
        page = read("tax.usage_lines.list", {"tax_id": tax.id, "limit": 2, "cursor": cursor})
        rows.extend(page["items"])
        if not page["has_more"]: break
        cursor = page["next_cursor"]
    assert len(rows) == len(expected_usage) == 8 and {row["id"] for row in rows} == expected_usage
    assert all(row["company_id"] == 1 and row["parent_state"] == "posted" for row in rows)
    write("tax.archive", {"tax_id": tax.id}, replay=False)
    assert settings()["active"] is False and {row["id"] for row in read("tax.usage_lines.list", {"tax_id": tax.id})["items"]} == expected_usage
    denied("tax.repartition_pair.delete", {"tax_id": tax.id, "invoice_line_id": inv_tax, "refund_line_id": ref_tax}, "odoo_write_error")
    denied("tax.delete", {"tax_id": tax.id}, "odoo_write_error")
    assert tax.exists() and ledger() == posted
    unused_id = write("tax.create", {"name": marker+"-UNUSED", "type_tax_use": "sale", "amount_type": "percent", "amount": 10}, replay=False)["id"]
    unused = env["account.tax"].browse(unused_id)
    unused_lines = unused.repartition_line_ids.ids
    removed = write("tax.delete", {"tax_id": unused_id}, replay=False)
    assert removed["state"] == "deleted" and not unused.exists() and not env["account.tax.repartition.line"].browse(unused_lines).exists()
    denied("tax.delete", {"tax_id": unused_id}, "record_not_found")
    assert read("tax.usage_lines.list", {"tax_id": unused_id})["items"] == []
    assert read("tax.usage_lines.list", {"tax_id": foreign.id})["items"] == []
    missing_settings(foreign.id)
    missing_settings(1_999_999_999)
    assert replays == 8 and client.capabilities == _WRITES | _READS | _SETUP


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
    marker = f"ODACV4-TAXPROC-{args.alias}-{args.run_id.hex}"
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
            for model in ("account.tax", "account.tax.group", "account.account", "account.account.tag"):
                assert not verify[model].with_context(active_test=False).search_count([("name", "ilike", marker)])
            assert not verify["account.move.line"].search_count([("name", "ilike", marker)])
            for group_id, members in baseline.items(): assert shared._direct_group(verify_cursor, group_id) == members
        finally: verify_cursor.rollback()
    if failure is not None: raise failure
    print(json.dumps(_summary(args.alias, args.database), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_live_worker())
