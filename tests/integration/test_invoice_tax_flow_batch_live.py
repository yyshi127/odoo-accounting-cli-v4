"""Existing 13% taxes: invoice lines, journal items and generic tax report."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import sysconfig
import uuid
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import test_document_lifecycle_write_batch_live as lifecycle
import test_payment_bank_capability_batch_live as core

_CAPABILITIES = {
    "tax.get",
    "customer_invoice.create",
    "vendor_bill.create",
    "invoice.lines.replace",
    "invoice.get",
    "invoice.tax_breakdown.inspect",
    "invoice.post",
    "journal_item.search",
    "journal_item.get",
    "report.tax",
    "report.trial_balance",
}


def test_shared_tax_read_helper_binds_requested_capability(monkeypatch):
    from odoo_accounting_cli_v4 import cli
    from odoo_accounting_cli_v4.bridge.core_object_reads import OdooCoreObjectReadPort
    from odoo_accounting_cli_v4.bridge.financial_reports import OdooFinancialReportPort

    class DispatchChecked(Exception):
        pass

    def check_dispatch(_argv, **kwargs):
        port = kwargs["port_factory"](None, None)
        assert isinstance(port, expected_class)
        if capability == "report.tax":
            assert port._action == "account.report.tax.read_page"
        raise DispatchChecked

    monkeypatch.setattr(cli, "main", check_dispatch)
    for capability, expected_class in (
        ("tax.get", OdooCoreObjectReadPort),
        ("invoice.tax_breakdown.inspect", OdooCoreObjectReadPort),
        ("report.tax", OdooFinancialReportPort),
    ):
        with lifecycle.pytest.raises(DispatchChecked):
            core._cli(SimpleNamespace(), "v4-dev", uuid.uuid4(), capability, {})


def test_tax_flow_setup_needs_no_technical_model_access(monkeypatch):
    class PublicReadStarted(Exception):
        pass

    class Report:
        @property
        def custom_handler_model_id(self):
            raise AssertionError("An accounting user does not need ir.model access.")

        def _get_generic_line_id(self, model, record_id, **kwargs):
            return f"{kwargs.get('parent_line_id', kwargs.get('markup'))}:{model}:{record_id}"

    env = SimpleNamespace(uid=5, su=False, company=SimpleNamespace(id=1), user=object())
    env.ref = lambda xml_id: Report()
    monkeypatch.setattr(lifecycle, "_fixture_ids", lambda *_: {"currency": 6})
    fake_date = SimpleNamespace(
        context_today=lambda _: "2026-08-31", to_string=lambda value: value
    )
    monkeypatch.setitem(
        sys.modules, "odoo", SimpleNamespace(fields=SimpleNamespace(Date=fake_date))
    )

    def first_read(_client, _alias, _run_id, capability, _parameters):
        assert capability == "report.tax"
        raise PublicReadStarted

    monkeypatch.setattr(core, "_cli", first_read)
    with lifecycle.pytest.raises(PublicReadStarted):
        _run_chain(SimpleNamespace(env=env), "v4-dev", uuid.uuid4())


def _run_chain(client, alias, run_id):
    from odoo import fields

    from odoo_accounting_cli_v4.capabilities.core_writes import (
        _expected_idempotency_key,
    )

    env = client.env
    assert env.uid == 5 and not env.su and env.company.id == 1
    ids = lifecycle._fixture_ids(env, alias)
    assert ids["currency"] == 6
    today = fields.Date.to_string(fields.Date.context_today(env.user))
    marker = f"ODACV4-{run_id.hex}-{alias}-tax"
    calls, replays = [], 0
    item_ids = set()
    native_report = env.ref("account.generic_tax_report")
    # Source: account_generic_tax_report.py:584/589 and account_report.py:2301.
    # Use the native identifier formatter, not translated display names or guessed delimiters.
    line_ids = {
        tax_id: native_report._get_generic_line_id(
            "account.tax",
            tax_id,
            parent_line_id=native_report._get_generic_line_id(None, None, markup=side),
        )
        for tax_id, side in ((5, "sale"), (11, "purchase"))
    }

    def read(capability, parameters):
        calls.append(capability)
        return core._cli(client, alias, run_id, capability, parameters)

    def twice(capability, parameters, key=None):
        nonlocal replays
        key = key or _expected_idempotency_key(capability, parameters, 1)
        assert key
        calls.extend([capability, capability])
        first = core._cli(client, alias, run_id, capability, parameters, key=key)
        tracked = {name: set(values) for name, values in client.tracked.items()}
        second = core._cli(client, alias, run_id, capability, parameters, key=key)
        assert (
            first["idempotent_replay"] is False and second["idempotent_replay"] is True
        )
        assert first["result"] == second["result"] and client.tracked == tracked
        replays += 1
        return first["result"]

    def tax_report(require_rows=False):
        data = read("report.tax", {"date_from": today, "date_to": today, "limit": 1000})
        assert not data["has_more"] and data["next_cursor"] is None
        assert [c["expression_label"] for c in data["columns"]] == ["net", "tax"]
        result = {}
        for tax_id, line_id in line_ids.items():
            rows = [row for row in data["lines"] if row["id"] == line_id]
            assert len(rows) <= 1 and (rows or not require_rows)
            result[tax_id] = (
                [Decimal(value) for value in rows[0]["values"]]
                if rows
                else [Decimal(0), Decimal(0)]
            )
        return result

    def check_invoice(move_id, base, tax, state, group_id):
        total = base + tax
        for capability in ("invoice.get", "invoice.tax_breakdown.inspect"):
            data = read(capability, {"invoice_id": move_id})
            assert data["id"] == move_id
            assert [
                Decimal(data[key])
                for key in ("amount_untaxed", "amount_tax", "amount_total")
            ] == [base, tax, total]
            if capability == "invoice.get":
                assert data["state"] == state
            else:
                assert data["invoice"]["state"] == state and data["has_tax_groups"]
                assert len(data["subtotals"]) == 1
                subtotal = data["subtotals"][0]
                assert Decimal(subtotal["base_amount"]) == base
                assert Decimal(subtotal["tax_amount"]) == tax
                assert len(subtotal["tax_groups"]) == 1
                group = subtotal["tax_groups"][0]
                assert group["id"] == group_id
                assert (
                    Decimal(group["base_amount"]) == base
                    and Decimal(group["tax_amount"]) == tax
                )

    baseline = tax_report()
    calls.append("report.trial_balance")
    trial_before = core._trial_balance_totals(client, alias, run_id, today)
    expected = {5: [Decimal(180), Decimal("23.4")], 11: [Decimal(120), Decimal("15.6")]}
    for customer, tax_id, tax_account in ((True, 5, 99), (False, 11, 100)):
        tax = read("tax.get", {"tax_id": tax_id})
        assert tax["active"] and tax["company_id"] == 1
        assert tax["type_tax_use"] == ("sale" if customer else "purchase")
        assert tax["amount_type"] == "percent" and Decimal(tax["amount"]) == 13
        assert tax["price_include"] is False
        native_tax = env["account.tax"].browse(tax_id)
        assert native_tax.tax_exigibility == "on_invoice"
        assert native_tax.country_id == env.company.account_fiscal_country_id
        partitions = native_tax.invoice_repartition_line_ids
        assert len(partitions) == 2 and all(p.factor_percent == 100 for p in partitions)
        tax_partition = partitions.filtered(lambda p: p.repartition_type == "tax")
        assert len(tax_partition) == 1 and tax_partition.account_id.id == tax_account
        side = "customer" if customer else "supplier"
        account_id = ids["income" if customer else "expense"]
        line = {
            "name": f"{marker}-{side}",
            "account_id": account_id,
            "product_id": None,
            "quantity": "1",
            "price_unit": "100",
            "discount": "0",
            "tax_ids": [tax_id],
        }
        move_id = twice(
            "customer_invoice.create" if customer else "vendor_bill.create",
            {
                "partner_id": ids[side],
                "journal_id": ids["sale_journal" if customer else "purchase_journal"],
                "invoice_date": today,
                "currency_id": ids["currency"],
                "payment_term_id": None,
                "invoice_date_due": today,
                "reference": f"{marker}-{side}",
                "lines": [line],
            },
            key=f"{marker}-{side}",
        )["id"]
        check_invoice(
            move_id, Decimal(100), Decimal(13), "draft", tax["tax_group"]["id"]
        )
        replacement = {
            **line,
            "quantity": "2" if customer else "3",
            "price_unit": "100" if customer else "50",
            "discount": "10" if customer else "20",
        }
        twice(
            "invoice.lines.replace",
            {"move_id": move_id, "lines": [deepcopy(replacement)]},
        )
        base, tax_amount = expected[tax_id]
        check_invoice(move_id, base, tax_amount, "draft", tax["tax_group"]["id"])
        twice("invoice.post", {"move_id": move_id})
        check_invoice(move_id, base, tax_amount, "posted", tax["tax_group"]["id"])
        page = read("journal_item.search", {"move_id": move_id, "limit": 1000})
        assert not page["has_more"] and page["next_cursor"] is None
        rows = page["items"]
        assert len(rows) == 3 and all(
            row["move"]["id"] == move_id and row["move"]["state"] == "posted"
            for row in rows
        )
        tax_rows = [row for row in rows if row["tax_line_id"] == tax_id]
        base_rows = [row for row in rows if row["account"]["id"] == account_id]
        assert len(tax_rows) == len(base_rows) == 1
        assert read("journal_item.get", {"line_id": tax_rows[0]["id"]}) == tax_rows[0]
        sign = -1 if customer else 1
        assert tax_rows[0]["account"]["id"] == tax_account
        assert Decimal(tax_rows[0]["tax_base_amount"]) == sign * base
        assert Decimal(tax_rows[0]["balance"]) == sign * tax_amount
        assert (
            base_rows[0]["tax_ids"] == [tax_id] and base_rows[0]["tax_line_id"] is None
        )
        assert Decimal(base_rows[0]["balance"]) == sign * base
        assert sum(Decimal(row["balance"]) for row in rows) == 0
        for key in ("debit", "credit"):
            assert sum(Decimal(row[key]) for row in rows) == base + tax_amount
        item_ids.update(row["id"] for row in rows)

    actual = tax_report(require_rows=True)
    assert {
        tax_id: [a - b for a, b in zip(actual[tax_id], baseline[tax_id], strict=True)]
        for tax_id in expected
    } == expected
    calls.append("report.trial_balance")
    trial_after = core._trial_balance_totals(client, alias, run_id, today)
    assert [a - b for a, b in zip(trial_after, trial_before, strict=True)] == [
        0,
        339,
        339,
        0,
    ]
    assert set(calls) == client.capabilities == _CAPABILITIES
    assert len(calls) == 34 and replays == 6 and len(item_ids) == 6
    return {
        "cli_calls": len(calls),
        "immediate_replays": replays,
        "posted_journal_items": len(item_ids),
        "tax_flow_verified": True,
        "tax_ids": [5, 11],
        "trial_balance_delta": {"debit": "339", "credit": "339"},
        "scope": "price_excluded_on_invoice_generic_tax_report_not_statutory_return",
    }


def test_tax_flow_rolls_back_per_alias():
    config_path, runtime = lifecycle._enabled_runtime()
    run_id = uuid.uuid4()
    for alias in lifecycle._ALIASES:
        command, timeout = lifecycle._worker_command(
            alias, run_id, config_path, runtime
        )
        command[1] = str(Path(__file__).resolve())
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment["PYTHONPATH"] = os.pathsep.join(
            [
                str(lifecycle._root() / "src"),
                sysconfig.get_path("purelib"),
                environment.get("PYTHONPATH", ""),
            ]
        )
        completed = subprocess.run(
            command,
            cwd=lifecycle._root(),
            env=environment,
            text=True,
            capture_output=True,
            check=False,
            timeout=max(timeout, 900),
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        results = [
            json.loads(line)
            for line in completed.stdout.splitlines()
            if line.startswith("{")
        ]
        assert len(results) == 1
        result = results[0]
        assert (
            result["alias"] == alias
            and result["database"] == lifecycle._DATABASES[alias]
        )
        assert result["user_id"] == 5 and result["company_id"] == 1
        assert result["rollback_verified"] and result["tax_flow_verified"]
        assert result["cli_calls"] == 34 and result["immediate_replays"] == 6
        assert (
            result["posted_journal_items"] == 6
            and set(result["capabilities"]) == _CAPABILITIES
        )
        print(json.dumps(result, sort_keys=True, separators=(",", ":")), flush=True)


def _live_worker():
    args = lifecycle._arguments(None)
    assert not (
        args.refund_only or args.payment_difference_only or args.analytic_readback_only
    )
    sys.path.insert(0, str(args.odoo_source.resolve(strict=True)))
    sys.path.insert(0, str((lifecycle._root() / "src").resolve(strict=True)))
    from odoo import api
    from odoo.orm.registry import Registry
    from odoo.tools import config as odoo_config

    odoo_config.parse_config(
        [
            "--config",
            str(args.odoo_config),
            "--database",
            args.database,
            "--no-http",
            "--logfile=/dev/null",
        ]
    )
    registry = Registry(args.database)
    cursor = registry.cursor()
    tracked = {model: set() for model in core._BUSINESS_MODELS}
    env = client = None
    failure = None
    try:
        env = api.Environment(
            cursor,
            5,
            {
                "allowed_company_ids": [1],
                "active_test": True,
                "lang": "en_US",
                "tz": "Asia/Shanghai",
            },
        )
        assert env.uid == 5 and not env.su and env.user.active
        assert env.user.login == lifecycle._USER_LOGIN and 1 in env.user.company_ids.ids
        client = core._RuntimeClient(env)
        client.tracked = tracked
        details = _run_chain(client, args.alias, args.run_id)
    except BaseException as exc:  # noqa: BLE001 - rollback before reporting failure
        failure = exc
    finally:
        try:
            if env is not None:
                core._collect_marked(env, tracked, args.run_id.hex)
        except Exception as exc:  # noqa: BLE001 - do not prevent rollback
            if failure is None:
                failure = exc
            else:
                failure.add_note(f"rollback collection also failed: {exc}")
        finally:
            try:
                cursor.rollback()
            finally:
                cursor.close()
    try:
        core._verify_rollback(registry, tracked=tracked, marker=args.run_id.hex)
    except Exception as exc:
        raise exc from failure
    if failure is not None:
        raise failure
    print(
        json.dumps(
            {
                "alias": args.alias,
                "database": args.database,
                "user_id": 5,
                "company_id": 1,
                "rollback_verified": True,
                "execution": "in_process_cli_real_orm",
                "capabilities": sorted(client.capabilities),
                **details,
            },
            sort_keys=True,
            separators=(",", ":"),
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_live_worker())
