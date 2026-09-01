"""Cash-refund accounting against settled invoices; never a bank transfer."""

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
    "customer_credit_note.create",
    "vendor_refund.create",
    "invoice.post",
    "receivable.payment.register",
    "payable.payment.register",
    "invoice.get",
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
    assert env.company.account_storno is True
    ids = lifecycle._fixture_ids(env, alias)
    assert ids["currency"] == 6
    # Read existing master records only; do not reuse the bank-matching fixture guard.
    for method_id, direction in ((3, "inbound"), (4, "outbound")):
        method = lifecycle._one(
            env["account.payment.method.line"].search(
                [
                    ("id", "=", method_id),
                    ("journal_id", "=", 14),
                    ("journal_id.company_id", "=", 1),
                    ("journal_id.active", "=", True),
                    ("payment_method_id.payment_type", "=", direction),
                ]
            ),
            "existing manual payment method",
        )
        assert method.payment_method_id.code == "manual"
        assert (
            method.payment_account_id.id == 153 and method.payment_account_id.reconcile
        )
        assert (
            method.payment_account_id.active
            and 1 in method.payment_account_id.company_ids.ids
        )

    today = fields.Date.to_string(fields.Date.context_today(env.user))
    marker = f"ODACV4-{run_id.hex}-{alias}-cash-refund"
    calls, replays = [], 0
    items = set()
    payment_ids = set()

    def read(capability, parameters):
        calls.append(capability)
        return core._cli(client, alias, run_id, capability, parameters)

    def twice(capability, parameters, key=None):
        nonlocal replays
        key = key or _expected_idempotency_key(capability, parameters, 1)
        assert key
        calls.extend([capability, capability])
        first = core._cli(client, alias, run_id, capability, parameters, key=key)
        tracked = {
            model: set(record_ids) for model, record_ids in client.tracked.items()
        }
        second = core._cli(client, alias, run_id, capability, parameters, key=key)
        assert (
            first["idempotent_replay"] is False and second["idempotent_replay"] is True
        )
        assert first["result"] == second["result"] and client.tracked == tracked
        replays += 1
        return first["result"]

    def document(move_id, amount, move_type):
        data = read("invoice.get", {"invoice_id": move_id})
        assert (
            data["id"] == move_id
            and data["move_type"] == move_type
            and data["state"] == "posted"
        )
        assert [
            Decimal(data[field])
            for field in ("amount_untaxed", "amount_tax", "amount_total")
        ] == [amount, 0, amount]

    def status(move_id, residual):
        data = read("invoice.payment_status.inspect", {"invoice_id": move_id})
        assert data["id"] == move_id and data["state"] == "posted"
        assert Decimal(data["amount_residual"]) == residual
        assert len(data["receivable_payable_lines"]) == 1
        line = data["receivable_payable_lines"][0]
        assert abs(Decimal(line["amount_residual"])) == residual
        assert line["reconciled"] is (residual == 0)
        if residual == 0:
            assert data["payment_state"] in {"in_payment", "paid"}
        return data

    def payment(result, move_id, amount, side, direction):
        assert result["source_id"] == move_id
        data = read("payment.get", {"payment_id": result["id"]})
        assert data["state"] in {"in_process", "paid"}
        assert data["partner_type"] == side and data["payment_type"] == direction
        assert data["partner"]["id"] == ids[side] and data["currency"]["id"] == 6
        assert Decimal(data["amount"]) == amount
        assert data["payment_method_line"]["id"] == (3 if direction == "inbound" else 4)
        linked = data[
            "reconciled_invoices" if side == "customer" else "reconciled_bills"
        ]
        assert {row["id"] for row in linked} == {move_id}
        assert data["move_id"] and data["journal_entry"]["id"] == data["move_id"]
        assert result["id"] not in payment_ids
        payment_ids.add(result["id"])
        return data["move_id"]

    def journal(move_id, debit_total, term_id, term_balance):
        page = read("journal_item.search", {"move_id": move_id, "limit": 1000})
        assert not page["has_more"] and page["next_cursor"] is None
        rows = page["items"]
        assert len(rows) == 2
        assert all(
            row["move"]["id"] == move_id and row["move"]["state"] == "posted"
            for row in rows
        )
        assert sum(Decimal(row["balance"]) for row in rows) == 0
        assert sum(Decimal(row["debit"]) for row in rows) == debit_total
        assert sum(Decimal(row["credit"]) for row in rows) == debit_total
        term = [row for row in rows if row["account"]["id"] == term_id]
        assert len(term) == 1 and Decimal(term[0]["balance"]) == term_balance
        assert term[0]["reconciled"] is True
        items.update(row["id"] for row in rows)

    calls.append("report.trial_balance")
    before = core._trial_balance_totals(client, alias, run_id, today)
    for customer, credit_amount in ((True, Decimal(40)), (False, Decimal(60))):
        side = "customer" if customer else "supplier"
        register = (
            "receivable.payment.register" if customer else "payable.payment.register"
        )
        source_type = "out_invoice" if customer else "in_invoice"
        refund_type = "out_refund" if customer else "in_refund"
        sign = 1 if customer else -1
        line = {
            "name": f"{marker}-{side}",
            "account_id": ids["income" if customer else "expense"],
            "product_id": None,
            "quantity": "1",
            "price_unit": "100",
            "discount": "0",
            "tax_ids": [],
        }
        source_id = twice(
            "customer_invoice.create" if customer else "vendor_bill.create",
            {
                "partner_id": ids[side],
                "journal_id": ids["sale_journal" if customer else "purchase_journal"],
                "date": today,
                "invoice_date": today,
                "currency_id": 6,
                "payment_term_id": None,
                "invoice_date_due": today,
                "reference": f"{marker}-{side}-source",
                "lines": [line],
            },
            key=f"{marker}-{side}-source",
        )["id"]
        twice("invoice.post", {"move_id": source_id})
        document(source_id, Decimal(100), source_type)
        source_payment = twice(
            register, {"move_id": source_id, "journal_id": 14, "payment_date": today}
        )
        source_payment_move = payment(
            source_payment,
            source_id,
            Decimal(100),
            side,
            "inbound" if customer else "outbound",
        )
        source_status = status(source_id, Decimal(0))
        source_partials = {row["id"] for row in source_status["reconciliations"]}
        assert len(source_partials) == 1
        term_account = source_status["receivable_payable_lines"][0]["account"]["id"]

        credit_id = twice(
            "customer_credit_note.create" if customer else "vendor_refund.create",
            {
                "move_id": source_id,
                "date": today,
                "reason": f"{marker}-{side}-credit",
                "lines": [{**line, "price_unit": str(credit_amount)}],
            },
            key=f"{marker}-{side}-credit",
        )["id"]
        twice("invoice.post", {"move_id": credit_id})
        document(credit_id, credit_amount, refund_type)
        assert {
            row["id"] for row in status(source_id, Decimal(0))["reconciliations"]
        } == source_partials
        credit_status = status(credit_id, credit_amount)
        assert credit_status["reconciliations"] == []
        refund_moves = []
        half = credit_amount / 2
        for index in (0, 1):
            result = twice(
                register,
                {
                    "move_id": credit_id,
                    "journal_id": 14,
                    "payment_date": today,
                    **({"amount": str(half)} if index == 0 else {}),
                },
                key=f"{marker}-{side}-refund-{index}" if index == 0 else None,
            )
            refund_moves.append(
                payment(
                    result, credit_id, half, side, "outbound" if customer else "inbound"
                )
            )
            credit_status = status(credit_id, half if index == 0 else Decimal(0))
            assert len(credit_status["reconciliations"]) == index + 1
            assert sum(
                Decimal(row["company_amount"])
                for row in credit_status["reconciliations"]
            ) == half * (index + 1)
            if index == 0:
                assert credit_status["payment_state"] == "partial"
        assert {
            row["id"] for row in status(source_id, Decimal(0))["reconciliations"]
        } == source_partials
        journal(source_id, Decimal(100), term_account, sign * Decimal(100))
        journal(credit_id, -credit_amount, term_account, -sign * credit_amount)
        journal(source_payment_move, Decimal(100), term_account, -sign * Decimal(100))
        for move_id in refund_moves:
            journal(move_id, half, term_account, sign * half)

    calls.append("report.trial_balance")
    after = core._trial_balance_totals(client, alias, run_id, today)
    assert [a - b for a, b in zip(after, before, strict=True)] == [0, 400, 400, 0]
    assert set(calls) == client.capabilities == _CAPABILITIES
    assert (
        len(calls) == 62
        and replays == 14
        and len(items) == 20
        and len(payment_ids) == 6
    )
    assert len(client.tracked["account.partial.reconcile"]) == 6
    assert len(client.tracked["account.full.reconcile"]) == 4
    return {
        "cli_calls": len(calls),
        "immediate_replays": replays,
        "posted_journal_items": len(items),
        "payments": len(payment_ids),
        "cash_refund_accounting_verified": True,
        "bank_transfer_verified": False,
        "bank_statement_matching_verified": False,
        "trial_balance_delta": {"debit": "400", "credit": "400"},
    }


def test_cash_refund_accounting_rolls_back_per_alias():
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
        assert result["rollback_verified"] and result["cash_refund_accounting_verified"]
        assert (
            result["bank_transfer_verified"]
            is result["bank_statement_matching_verified"]
            is False
        )
        assert result["cli_calls"] == 62 and result["immediate_replays"] == 14
        assert result["posted_journal_items"] == 20 and result["payments"] == 6
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
