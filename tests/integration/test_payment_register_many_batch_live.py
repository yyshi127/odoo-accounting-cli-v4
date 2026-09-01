"""Grouped full payment registration against multiple invoices and bills."""

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
import test_payment_bank_capability_batch_live as core

_CAPABILITIES = {
    "customer_invoice.create",
    "vendor_bill.create",
    "invoice.post",
    "receivable.payment.register",
    "payable.payment.register",
    "invoice.payment_status.inspect",
    "payment.get",
    "journal_item.search",
    "report.trial_balance",
}


def _run_chain(client, alias, run_id):
    from odoo import fields

    from odoo_accounting_cli_v4.capabilities.core_writes import (
        _expected_idempotency_key,
    )

    env = client.env
    assert env.uid == 5 and not env.su and env.company.id == 1
    ids = lifecycle._fixture_ids(env, alias)
    today = fields.Date.to_string(fields.Date.context_today(env.user))
    marker = f"ODACV4-{run_id.hex}-{alias}-grouped-payment"
    calls: list[str] = []
    replays = 0

    def read(capability, parameters):
        calls.append(capability)
        return core._cli(client, alias, run_id, capability, parameters)

    def twice(capability, parameters, *, key=None):
        nonlocal replays
        key = key or _expected_idempotency_key(capability, parameters, 1)
        assert key
        calls.extend([capability, capability])
        first = core._cli(client, alias, run_id, capability, parameters, key=key)
        tracked = {
            model: set(record_ids) for model, record_ids in client.tracked.items()
        }
        second = core._cli(client, alias, run_id, capability, parameters, key=key)
        assert first["idempotent_replay"] is False
        assert second["idempotent_replay"] is True
        assert first["result"] == second["result"]
        assert client.tracked == tracked
        replays += 1
        return first["result"]

    def create_document(*, customer, index, amount):
        side = "customer" if customer else "supplier"
        line = {
            "name": f"{marker}-{side}-{index}",
            "account_id": ids["income" if customer else "expense"],
            "product_id": None,
            "quantity": "1",
            "price_unit": str(amount),
            "discount": "0",
            "tax_ids": [],
        }
        result = twice(
            "customer_invoice.create" if customer else "vendor_bill.create",
            {
                "partner_id": ids[side],
                "journal_id": ids["sale_journal" if customer else "purchase_journal"],
                "date": today,
                "invoice_date": today,
                "currency_id": ids["currency"],
                "payment_term_id": None,
                "invoice_date_due": today,
                "reference": f"{marker}-{side}-{index}",
                "lines": [line],
            },
            key=f"{marker}-{side}-{index}",
        )
        twice("invoice.post", {"move_id": result["id"]})
        return result["id"]

    calls.append("report.trial_balance")
    before = core._trial_balance_totals(client, alias, run_id, today)
    customer_ids = [
        create_document(customer=True, index=1, amount=40),
        create_document(customer=True, index=2, amount=60),
    ]
    supplier_ids = [
        create_document(customer=False, index=1, amount=30),
        create_document(customer=False, index=2, amount=70),
    ]

    payment_ids: set[int] = set()
    payment_move_ids: set[int] = set()
    for customer, source_ids in ((True, customer_ids), (False, supplier_ids)):
        side = "customer" if customer else "supplier"
        capability = (
            "receivable.payment.register" if customer else "payable.payment.register"
        )
        parameters = {
            "move_ids": source_ids,
            "journal_id": 14,
            "payment_date": today,
        }
        result = twice(capability, parameters)
        assert result["source_id"] is None
        assert result["state"] in {"in_process", "paid"}
        assert result["reconciled"] is True
        assert result["line_ids"]
        assert result["partial_reconcile_ids"] == []
        assert result["full_reconcile_id"] is None
        assert result["id"] not in payment_ids
        payment_ids.add(result["id"])

        payment = read("payment.get", {"payment_id": result["id"]})
        assert payment["state"] in {"in_process", "paid"}
        assert payment["partner_type"] == side
        assert payment["payment_type"] == ("inbound" if customer else "outbound")
        assert payment["partner"]["id"] == ids[side]
        assert payment["currency"]["id"] == ids["currency"]
        assert Decimal(payment["amount"]) == 100
        assert payment["payment_method_line"]["id"] == (3 if customer else 4)
        linked = payment["reconciled_invoices" if customer else "reconciled_bills"]
        assert {item["id"] for item in linked} == set(source_ids)
        assert payment["move_id"] == payment["journal_entry"]["id"]
        payment_move_ids.add(payment["move_id"])

        reconciliation_ids = set()
        for source_id in source_ids:
            status = read("invoice.payment_status.inspect", {"invoice_id": source_id})
            assert status["id"] == source_id and status["state"] == "posted"
            assert Decimal(status["amount_residual"]) == 0
            assert status["payment_state"] in {"in_payment", "paid"}
            assert len(status["receivable_payable_lines"]) == 1
            assert status["receivable_payable_lines"][0]["reconciled"] is True
            assert len(status["reconciliations"]) == 1
            reconciliation = status["reconciliations"][0]
            assert reconciliation["payment_id"] == result["id"]
            reconciliation_ids.add(reconciliation["id"])
        assert len(reconciliation_ids) == len(source_ids)

        items = read(
            "journal_item.search", {"move_id": payment["move_id"], "limit": 1000}
        )
        assert not items["has_more"] and items["next_cursor"] is None
        assert len(items["items"]) == 2
        assert sum(Decimal(item["balance"]) for item in items["items"]) == 0
        assert sum(Decimal(item["debit"]) for item in items["items"]) == 100
        assert sum(Decimal(item["credit"]) for item in items["items"]) == 100

    calls.append("report.trial_balance")
    after = core._trial_balance_totals(client, alias, run_id, today)
    assert [new - old for old, new in zip(before, after, strict=True)] == [
        Decimal(0),
        Decimal(400),
        Decimal(400),
        Decimal(0),
    ]
    assert set(calls) == client.capabilities == _CAPABILITIES
    assert len(calls) == 30 and replays == 10
    assert len(payment_ids) == len(payment_move_ids) == 2
    assert len(client.tracked["account.partial.reconcile"]) == 4
    assert len(client.tracked["account.full.reconcile"]) == 2
    return {
        "cli_calls": len(calls),
        "immediate_replays": replays,
        "payments": len(payment_ids),
        "source_documents": len(customer_ids) + len(supplier_ids),
        "grouped_customer_receipt_verified": True,
        "grouped_vendor_payment_verified": True,
        "trial_balance_delta": {"debit": "400", "credit": "400"},
    }


def test_grouped_payment_registration_rolls_back_per_alias():
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
        assert result["alias"] == alias
        assert result["database"] == lifecycle._DATABASES[alias]
        assert result["user_id"] == 5 and result["company_id"] == 1
        assert result["rollback_verified"]
        assert result["grouped_customer_receipt_verified"]
        assert result["grouped_vendor_payment_verified"]
        assert result["cli_calls"] == 30 and result["immediate_replays"] == 10
        assert result["payments"] == 2 and result["source_documents"] == 4
        assert set(result["capabilities"]) == _CAPABILITIES
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
