"""One rollback-only public CLI workflow for native analytic processing."""

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

_ALLOW_ENV = "ODACV4_ALLOW_ANALYTIC_PROCESSING_SMOKE"
_GROUPS = ("account.group_account_manager", "analytic.group_analytic_accounting")
_WRITES = {"analytic.account.duplicate", "analytic.account.delete", "analytic.applicability.delete", "analytic.distribution_model.delete"}
_READS = {"analytic.account.balance.inspect", "analytic.account.invoice_usage.inspect", "analytic.applicability.resolve", "analytic.distribution.resolve"}
_SETUP = {"analytic.account.create", "analytic.account.archive", "analytic.account.restore", "analytic.line.create", "analytic.line.delete",
          "analytic.applicability.create", "analytic.distribution_model.create", "customer_invoice.create", "vendor_bill.create", "invoice.post"}
_MODELS = ("account.analytic.account", "account.analytic.line", "account.analytic.applicability", "account.analytic.distribution.model",
           "account.move", "account.move.line", "res.partner", "res.partner.category", "product.product", "product.template", "product.category")


def _root():
    return Path(__file__).resolve().parents[2]


def _summary(alias, database):
    return {"alias": alias, "database": database, "company_id": 1, "user_id": 5, "business_su": False,
            "capabilities": sorted(_WRITES | _READS | _SETUP), "immediate_replays": 16,
            "native_date_balance_and_shared_company_filter_verified": True,
            "native_posted_usage_distinct_move_count_verified": True,
            "native_copy_profile_no_lines_serial_replay_and_fresh_identity_verified": True,
            "native_restricted_analytic_line_delete_and_source_preservation_verified": True,
            "native_applicability_score_and_deletion_verified": True,
            "native_distribution_precedence_tags_product_and_shared_fallback_verified": True,
            "company_and_missing_target_denials_verified": True,
            "posted_moves_unchanged_by_maintenance": True,
            "rollback_verified": True, "temporary_groups_rolled_back": True, "execution": "in_process_cli_real_orm"}


if pytest is not None:
    @pytest.mark.integration
    def test_analytic_processing_rolls_back_per_alias():
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

    from odoo_accounting_cli_v4 import cli
    from odoo_accounting_cli_v4.bridge.core_object_reads import OdooCoreObjectReadPort
    from odoo_accounting_cli_v4.bridge.core_writes_runtime import (
        _analytic_account_values,
    )
    from odoo_accounting_cli_v4.bridge.runtime import RuntimeFailure
    from odoo_accounting_cli_v4.capabilities.core_writes import (
        _expected_idempotency_key,
        validate_core_write_request,
    )

    env = client.env
    ids = lifecycle._fixture_ids(admin, alias)
    plan, _other_plans = env["account.analytic.plan"]._get_all_plans()
    assert plan and plan._column_name() == "account_id"
    plan_snapshot = admin["account.analytic.plan"].search([]).read(["id", "name", "parent_id"])
    replays = 0

    def track(record):
        client.tracked[record._name].update(record.ids)
        if record._name == "account.move":
            client.tracked["account.move.line"].update(record.line_ids.ids)
            client.tracked["account.analytic.line"].update(record.line_ids.analytic_line_ids.ids)
        if record._name == "product.product": client.tracked["product.template"].update(record.product_tmpl_id.ids)
        return record

    def fixture(model, values, *, company_id=1):
        return track(admin[model].with_company(admin["res.company"].browse(company_id)).create(values))

    def write(cap, params, *, replay=True):
        nonlocal replays
        normalized = validate_core_write_request(cap, core._request(alias, run_id, cap, params))[2]
        key = _expected_idempotency_key(cap, normalized, 1) or f"{cap}:{run_id.hex}:{lifecycle._canonical_digest(normalized)[:32]}"
        client.last_runtime_failure = None
        try:
            first = core._cli(client, alias, run_id, cap, params, key=key)
            assert first["idempotent_replay"] is False
            if replay:
                second = core._cli(client, alias, run_id, cap, params, key=key)
                assert second["idempotent_replay"] is True and second["result"] == first["result"]
                replays += 1
        except AssertionError:
            if client.last_runtime_failure is not None: raise client.last_runtime_failure
            raise
        value = first["result"]
        if value["state"] != "deleted": track(env[value["model"]].browse(value["id"]))
        return value

    def read(cap, params):
        client.last_runtime_failure = None
        if cap == "analytic.distribution.resolve":
            stdout, stderr = io.StringIO(), io.StringIO()
            code = cli.main(["read", cap, "--request", "-"], stdin=io.StringIO(json.dumps(core._request(alias, run_id, cap, params))),
                            stdout=stdout, stderr=stderr, port_factory=lambda *args: OdooCoreObjectReadPort(client))
            response = json.loads(stdout.getvalue())
            assert code == 0 and not stderr.getvalue(), response
            assert response["success"] and response["status"] == "verified" and response["odoo"]["user_id"] == 5
            assert response["odoo"]["company_id"] == 1 and response["odoo"]["model"] == "res.company" and response["odoo"]["record_ids"] == [1]
            client.capabilities.add(cap)
            return response["data"]
        try: return shared._read(client, alias, run_id, cap, params)
        except AssertionError:
            if client.last_runtime_failure is not None: raise client.last_runtime_failure
            raise

    def denied(cap, params, expected):
        client.last_runtime_failure = None
        error = {4: "record_not_found", 5: "idempotency_conflict", 6: "odoo_write_error"}[expected]
        try: write(cap, params, replay=False)
        except (AssertionError, RuntimeFailure):
            failure = client.last_runtime_failure
            assert getattr(failure, "code", None) == error
            if expected == 6:
                cause = failure.__cause__
                assert type(cause).__name__ == "ForeignKeyViolation"
                assert cause.diag.table_name == "account_analytic_line"
                assert cause.diag.constraint_name == "account_analytic_line_account_id_fkey"
        else: raise RuntimeError("A native analytic/company denial succeeded")

    def denied_read(cap, params):
        stdout, stderr = io.StringIO(), io.StringIO()
        code = cli.main(["read", cap, "--request", "-"], stdin=io.StringIO(json.dumps(core._request(alias, run_id, cap, params))),
                        stdout=stdout, stderr=stderr, port_factory=lambda *args: OdooCoreObjectReadPort(client))
        response = json.loads(stdout.getvalue())
        assert code == 4 and not stderr.getvalue() and response["error"]["code"] == "record_not_found" and response["odoo"]["user_id"] == 5

    def balance(account_id, start=None, end=None):
        return read("analytic.account.balance.inspect", {"analytic_account_id": account_id, "date_from": start, "date_to": end})

    def metrics(item):
        return tuple(Decimal(item[field]) for field in ("debit", "credit", "balance"))

    # Every reused setup contract is checked before its first native mutation.
    setup_parameters = {
        "analytic.account.create": {"name": marker, "plan_id": plan.id, "code": "AP"+run_id.hex[:8], "partner_id": ids["customer"]},
        "analytic.account.archive": {"analytic_account_id": 1},
        "analytic.account.restore": {"analytic_account_id": 1},
        "analytic.line.create": {"name": marker, "date": "2026-10-02", "amount": "100", "analytic_account_id": 1, "reference": None, "unit_amount": "0"},
        "analytic.line.delete": {"analytic_line_id": 1},
        "analytic.applicability.create": {"plan_id": plan.id, "business_domain": "invoice", "applicability": "mandatory", "account_prefix": "4", "product_category_id": None},
        "analytic.distribution_model.create": {"sequence": 0, "account_prefix": None, "partner_id": None, "partner_category_id": None,
                                               "product_id": None, "product_category_id": None, "analytic_distribution": {"1": "100"}},
        "customer_invoice.create": {"partner_id": ids["customer"], "journal_id": ids["sale_journal"], "date": "2026-10-02", "invoice_date": "2026-10-02",
                                    "currency_id": ids["currency"], "lines": [{"name": marker, "account_id": ids["income"], "quantity": "1", "price_unit": "10", "tax_ids": [], "analytic_distribution": {"1": "100"}}]},
        "vendor_bill.create": {"partner_id": ids["supplier"], "journal_id": ids["purchase_journal"], "date": "2026-10-02", "invoice_date": "2026-10-02",
                               "currency_id": ids["currency"], "lines": [{"name": marker, "account_id": ids["expense"], "quantity": "1", "price_unit": "7", "tax_ids": [], "analytic_distribution": {"1": "100"}}]},
        "invoice.post": {"move_id": 1},
    }
    for cap, params in setup_parameters.items(): validate_core_write_request(cap, core._request(alias, run_id, cap, params))
    source = env["account.analytic.account"].browse(write("analytic.account.create", setup_parameters["analytic.account.create"])["id"])
    other = env["account.analytic.account"].browse(write("analytic.account.create", {**setup_parameters["analytic.account.create"], "name": marker+"other", "code": "AQ"+run_id.hex[:8]})["id"])
    line_ids = []
    for date, amount in (("2026-09-01", "-45"), ("2026-10-02", "100"), ("2026-08-01", "20")):
        value = write("analytic.line.create", {**setup_parameters["analytic.line.create"], "analytic_account_id": source.id, "date": date, "amount": amount, "name": marker+date})
        line_ids.append(value["id"])
    assert metrics(balance(source.id)) == (Decimal(45), Decimal(120), Decimal(75))
    period = balance(source.id, "2026-09-01", "2026-10-02")
    assert metrics(period) == (Decimal(45), Decimal(100), Decimal(55)) and period["currency_id"] == ids["currency"]
    assert tuple(Decimal(str(source[field])) for field in ("debit", "credit", "balance")) == (Decimal(45), Decimal(120), Decimal(75))
    assert metrics(balance(source.id, "2026-10-02", "2026-10-02")) == (Decimal(0), Decimal(100), Decimal(100))
    assert metrics(balance(source.id)) == (Decimal(45), Decimal(120), Decimal(75))

    def profile(record): return (_analytic_account_values(record), record.plan_id.id, record.company_id.id)
    before = profile(source)
    copy_id = write("analytic.account.duplicate", {"analytic_account_id": source.id, "name": marker+"copy"})["id"]
    copy = env["account.analytic.account"].browse(copy_id)
    assert copy_id != source.id and profile(source) == before
    assert {**profile(copy)[0], "name": source.name} == before[0] and profile(copy)[1:] == before[1:]
    assert metrics(balance(copy_id)) == (Decimal(0), Decimal(0), Decimal(0))
    assert not env["account.analytic.line"].search_count([("account_id", "=", copy_id)])
    denied("analytic.account.duplicate", {"analytic_account_id": other.id, "name": marker+"copy"}, 5)
    ambiguous = fixture("account.analytic.account", {"name": marker+"copy", "code": source.code, "plan_id": plan.id, "partner_id": source.partner_id.id, "company_id": 1})
    denied("analytic.account.duplicate", {"analytic_account_id": source.id, "name": marker+"copy"}, 5)
    write("analytic.account.delete", {"analytic_account_id": ambiguous.id}, replay=False)
    denied("analytic.account.delete", {"analytic_account_id": source.id}, 6)
    assert source.exists() and set(env["account.analytic.line"].browse(line_ids).exists().ids) == set(line_ids)
    assert profile(source) == before and metrics(balance(source.id)) == (Decimal(45), Decimal(120), Decimal(75))
    write("analytic.account.delete", {"analytic_account_id": copy_id}, replay=False)
    denied("analytic.account.delete", {"analytic_account_id": copy_id}, 4)
    denied_read("analytic.account.balance.inspect", {"analytic_account_id": copy_id, "date_from": None, "date_to": None})
    write("analytic.account.archive", {"analytic_account_id": source.id})
    replacement = write("analytic.account.duplicate", {"analytic_account_id": source.id, "name": marker+"copy"})
    assert replacement["id"] != copy_id and replacement["state"] == "archived" and source.active is False
    assert metrics(balance(source.id)) == (Decimal(45), Decimal(120), Decimal(75))
    write("analytic.account.restore", {"analytic_account_id": source.id})

    # Separate active account is used by actual posted invoice lines.
    documents = []
    for cap, count in (("customer_invoice.create", 2), ("vendor_bill.create", 1)):
        params = dict(setup_parameters[cap])
        params["lines"] = [{**params["lines"][0], "name": marker+cap+str(index), "analytic_distribution": {str(other.id): "100"}} for index in range(count)]
        documents.append(env["account.move"].browse(write(cap, params)["id"]))
    assert read("analytic.account.invoice_usage.inspect", {"analytic_account_id": other.id})["invoice_count"] == 0
    for move in documents: write("invoice.post", {"move_id": move.id})
    usage = read("analytic.account.invoice_usage.inspect", {"analytic_account_id": other.id})
    assert (usage["invoice_count"], usage["vendor_bill_count"]) == (1, 1) and len(documents) == 2, usage
    assert len(documents[0].invoice_line_ids) == 2
    fields = ["id", "account_id", "journal_id", "date_maturity", "balance", "amount_currency", "amount_residual", "tax_ids", "analytic_distribution"]
    def posted_snapshot(): return [(move.id, move.name, move.state, move.line_ids.read(fields)) for move in documents]
    posted = posted_snapshot()

    shared_account = fixture("account.analytic.account", {"name": marker+"shared", "plan_id": plan.id, "company_id": False})
    foreign_account = fixture("account.analytic.account", {"name": marker+"foreign", "plan_id": plan.id, "company_id": 2}, company_id=2)
    for company_id, amount in ((1, 12), (2, 999)):
        fixture("account.analytic.line", {"name": marker+"shared-line", "account_id": shared_account.id, "company_id": company_id, "amount": amount, "date": "2026-10-02"}, company_id=company_id)
    assert metrics(balance(shared_account.id)) == (Decimal(0), Decimal(12), Decimal(12)) and balance(shared_account.id)["company_id"] is None
    for record in (shared_account, foreign_account):
        denied("analytic.account.delete", {"analytic_account_id": record.id}, 4)
        denied("analytic.account.duplicate", {"analytic_account_id": record.id, "name": marker+"denied"}, 4)
    denied_read("analytic.account.invoice_usage.inspect", {"analytic_account_id": foreign_account.id})
    denied_read("analytic.account.balance.inspect", {"analytic_account_id": foreign_account.id, "date_from": None, "date_to": None})

    tag = fixture("res.partner.category", {"name": marker+"tag"})
    partner = fixture("res.partner", {"name": marker+"partner", "company_id": 1, "category_id": [Command.set(tag.ids)]})
    category = fixture("product.category", {"name": marker+"category"})
    product = fixture("product.product", {"name": marker+"product", "type": "consu", "company_id": False, "categ_id": category.id})
    ledger = env["account.account"].browse(ids["income"])
    applicability_params = {"plan_id": plan.id, "business_domain": "invoice", "account_id": ledger.id, "product_id": product.id}
    default = read("analytic.applicability.resolve", applicability_params)["applicability"]
    prefixes = "NOMATCH; " + ledger.code
    rule = write("analytic.applicability.create", {**setup_parameters["analytic.applicability.create"], "account_prefix": prefixes, "product_category_id": category.id})
    assert read("analytic.applicability.resolve", applicability_params)["applicability"] == "mandatory"
    assert read("analytic.applicability.resolve", {**applicability_params, "product_id": None})["applicability"] == default
    shared_rule = fixture("account.analytic.applicability", {"analytic_plan_id": plan.id, "company_id": False, "business_domain": "bill", "applicability": "mandatory"})
    foreign_rule = fixture("account.analytic.applicability", {"analytic_plan_id": plan.id, "company_id": 2, "business_domain": "invoice", "applicability": "unavailable", "account_prefix": ledger.code, "product_categ_id": category.id}, company_id=2)
    assert read("analytic.applicability.resolve", applicability_params)["applicability"] == "mandatory"
    for record in (shared_rule, foreign_rule): denied("analytic.applicability.delete", {"applicability_id": record.id}, 4)
    write("analytic.applicability.delete", {"applicability_id": rule["id"]}, replay=False)
    assert read("analytic.applicability.resolve", applicability_params)["applicability"] == default
    denied("analytic.applicability.delete", {"applicability_id": rule["id"]}, 4)

    distribution_params = {"account_id": ledger.id, "partner_id": partner.id, "product_id": product.id}
    model_params = {**setup_parameters["analytic.distribution_model.create"], "account_prefix": prefixes, "partner_id": partner.id,
                    "partner_category_id": tag.id, "product_id": product.id, "product_category_id": category.id}
    first_model = write("analytic.distribution_model.create", {**model_params, "analytic_distribution": {str(source.id): "100"}})
    second_model = write("analytic.distribution_model.create", {**model_params, "sequence": 1, "analytic_distribution": {str(other.id): "100"}})
    native_model_values = {"account_prefix": ledger.code, "partner_id": partner.id, "partner_category_id": tag.id, "product_id": product.id, "product_categ_id": category.id}
    global_model = fixture("account.analytic.distribution.model", {**native_model_values, "sequence": 2, "company_id": False, "analytic_distribution": {str(shared_account.id): 100}})
    foreign_model = fixture("account.analytic.distribution.model", {**native_model_values, "sequence": 0, "company_id": 2, "partner_id": False, "product_id": False, "analytic_distribution": {str(foreign_account.id): 100}}, company_id=2)
    def distribution(): return read("analytic.distribution.resolve", distribution_params)["analytic_distribution"]
    assert distribution() == {str(source.id): "100"}
    assert read("analytic.distribution.resolve", {**distribution_params, "product_id": None})["analytic_distribution"] == {}
    for record in (global_model, foreign_model): denied("analytic.distribution_model.delete", {"distribution_model_id": record.id}, 4)
    write("analytic.distribution_model.delete", {"distribution_model_id": first_model["id"]}, replay=False)
    assert distribution() == {str(other.id): "100"}
    write("analytic.distribution_model.delete", {"distribution_model_id": second_model["id"]}, replay=False)
    assert distribution() == {str(shared_account.id): "100"}
    denied("analytic.distribution_model.delete", {"distribution_model_id": second_model["id"]}, 4)
    denied_read("analytic.distribution.resolve", {**distribution_params, "partner_id": 2147483647})
    denied_read("analytic.applicability.resolve", {**applicability_params, "plan_id": 2147483647})
    for line_id in line_ids: write("analytic.line.delete", {"analytic_line_id": line_id}, replay=False)
    assert metrics(balance(source.id)) == (Decimal(0), Decimal(0), Decimal(0))
    write("analytic.account.delete", {"analytic_account_id": source.id}, replay=False)
    assert not source.exists() and shared_account.exists() and foreign_account.exists()
    assert posted_snapshot() == posted
    assert admin["account.analytic.plan"].search([]).read(["id", "name", "parent_id"]) == plan_snapshot
    assert replays == 16 and client.capabilities == _WRITES | _READS | _SETUP


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
    marker = f"ODACV4-ANPROC-{args.alias}-{args.run_id.hex}"
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
            for model in ("account.analytic.account", "account.analytic.line", "res.partner", "res.partner.category", "product.template", "product.category"):
                assert not verify[model].with_context(active_test=False).search_count([("name", "ilike", marker)])
            assert not verify["account.move.line"].search_count([("name", "ilike", marker)])
            for group_id, members in baseline.items(): assert shared._direct_group(verify_cursor, group_id) == members
        finally: verify_cursor.rollback()
    if failure is not None: raise failure
    print(json.dumps(_summary(args.alias, args.database), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_live_worker())
