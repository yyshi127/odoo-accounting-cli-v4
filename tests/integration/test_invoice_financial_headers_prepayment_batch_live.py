"""Rollback-only prepayments and nullable financial headers through public CLI."""

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
    "payment.create",
    "payment.post",
    "payment.get",
    "customer_invoice.create",
    "vendor_bill.create",
    "invoice.update",
    "invoice.post",
    "invoice.get",
    "invoice.payment_status.inspect",
    "reconciliation.apply",
    "journal_item.search",
    "report.trial_balance",
}
_HEADERS = {"partner_bank_id": None, "fiscal_position_id": None}


def _run_chain(client, alias, run_id):
    from odoo import fields

    from odoo_accounting_cli_v4.capabilities.core_writes import (
        _expected_idempotency_key,
    )

    env = client.env
    assert env.uid == 5 and not env.su and env.company.id == 1
    ids = lifecycle._fixture_ids(env, alias)
    assert ids["currency"] == 6
    journal = lifecycle._one(
        env["account.journal"].search(
            [("company_id", "=", 1), ("type", "=", "bank")], order="id", limit=1
        ),
        "existing payment journal",
    )
    today = fields.Date.to_string(fields.Date.context_today(env.user))
    marker = f"ODACV4-{run_id.hex}-{alias}-prepayment"
    calls = []
    replays = 0
    posted_items = set()

    def read(capability, parameters):
        calls.append(capability)
        return core._cli(client, alias, run_id, capability, parameters)

    def twice(capability, parameters, key=None):
        nonlocal replays
        key = key or _expected_idempotency_key(capability, parameters, 1)
        assert key is not None
        calls.extend([capability, capability])
        first = core._cli(client, alias, run_id, capability, parameters, key=key)
        second = core._cli(client, alias, run_id, capability, parameters, key=key)
        assert first["idempotent_replay"] is False
        assert second["idempotent_replay"] is True
        assert first["result"] == second["result"]
        replays += 1
        return first["result"]

    def invoice(invoice_id, amount, state):
        result = read("invoice.get", {"invoice_id": invoice_id})
        assert result["id"] == invoice_id and result["state"] == state
        assert {key: result[key] for key in _HEADERS} == _HEADERS
        assert Decimal(result["amount_total"]) == amount
        assert Decimal(result["amount_untaxed"]) == amount
        assert Decimal(result["amount_tax"]) == 0
        return result

    calls.append("report.trial_balance")
    before = core._trial_balance_totals(client, alias, run_id, today)
    for side, direction, amount in (
        ("customer", "inbound", Decimal(120)),
        ("supplier", "outbound", Decimal(90)),
    ):
        method = lifecycle._one(
            env["account.payment.method.line"].search(
                [
                    ("journal_id", "=", journal.id),
                    ("payment_method_id.payment_type", "=", direction),
                ],
                order="id",
                limit=1,
            ),
            "existing payment method",
        )
        assert method.payment_account_id and method.payment_account_id.reconcile
        assert 1 in method.payment_account_id.company_ids.ids
        # No suspense-account comparison: there is no statement matching in this case.
        payment_id = twice(
            "payment.create",
            {
                "payment_type": direction,
                "partner_type": side,
                "partner_id": ids[side],
                "amount": str(amount),
                "currency_id": ids["currency"],
                "journal_id": journal.id,
                "payment_method_line_id": method.id,
                "date": today,
                "payment_reference": f"{marker}-{side}-advance",
            },
            key=f"{marker}-{side}-payment",
        )["id"]
        # Creation replay must happen while the payment is still draft.
        twice("payment.post", {"payment_id": payment_id})
        payment = read("payment.get", {"payment_id": payment_id})
        assert payment["state"] in {"in_process", "paid"}
        assert Decimal(payment["amount"]) == amount
        assert payment["payment_type"] == direction and payment["partner_type"] == side
        assert payment["partner"]["id"] == ids[side]
        assert payment["currency"]["id"] == ids["currency"]
        assert payment["reconciled_invoices"] == payment["reconciled_bills"] == []
        payment_move_id = payment["move_id"]
        assert payment_move_id and payment["journal_entry"]["id"] == payment_move_id

        customer = side == "customer"
        capability = "customer_invoice.create" if customer else "vendor_bill.create"
        invoice_id = twice(
            capability,
            {
                "partner_id": ids[side],
                "journal_id": ids["sale_journal" if customer else "purchase_journal"],
                "currency_id": ids["currency"],
                "invoice_date": today,
                "payment_term_id": None,
                "invoice_date_due": today,
                "reference": f"{marker}-{side}-invoice",
                **_HEADERS,
                "lines": [
                    {
                        "name": f"{marker}-{side}-service",
                        "product_id": None,
                        "account_id": ids["income" if customer else "expense"],
                        "quantity": "1",
                        "price_unit": str(amount),
                        "discount": "0",
                        "tax_ids": [],
                    }
                ],
            },
            key=f"{marker}-{side}-invoice",
        )["id"]
        invoice(invoice_id, amount, "draft")
        # Reference actually changes; null -> null is not claimed as clearing a value.
        for changes in (
            {"reference": f"{marker}-{side}-updated", **_HEADERS},
            {"payment_reference": f"{marker}-{side}-omitted"},
        ):
            twice("invoice.update", {"move_id": invoice_id, "changes": changes})
            document = invoice(invoice_id, amount, "draft")
            for key, value in changes.items():
                assert document["ref" if key == "reference" else key] == value
        twice("invoice.post", {"move_id": invoice_id})
        status = read("invoice.payment_status.inspect", {"invoice_id": invoice_id})
        assert Decimal(status["amount_residual"]) == amount
        candidates = [
            item
            for item in status["outstanding_items"]
            if item["move_id"] == payment_move_id
        ]
        assert len(candidates) == 1 and Decimal(candidates[0]["amount"]) == amount
        applied = twice(
            "reconciliation.apply",
            {
                "invoice_id": invoice_id,
                "outstanding_line_id": candidates[0]["line_id"],
            },
        )
        assert applied["reconciled"] is True
        assert len(applied["partial_reconcile_ids"]) == 1
        assert applied["full_reconcile_id"] is not None
        status = read("invoice.payment_status.inspect", {"invoice_id": invoice_id})
        assert Decimal(status["amount_residual"]) == 0
        assert status["payment_state"] in {"in_payment", "paid"}
        assert status["receivable_payable_lines"]
        assert all(
            line["reconciled"] and Decimal(line["amount_residual"]) == 0
            for line in status["receivable_payable_lines"]
        )
        assert (
            sum(
                Decimal(row["company_amount"])
                for row in status["reconciliations"]
                if row["payment_id"] == payment_id
            )
            == amount
        )
        payment = read("payment.get", {"payment_id": payment_id})
        assert payment["state"] in {"in_process", "paid"}
        assert invoice_id in {
            row["id"]
            for row in payment[
                "reconciled_invoices" if customer else "reconciled_bills"
            ]
        }
        for move_id in (invoice_id, payment_move_id):
            data = read("journal_item.search", {"move_id": move_id, "limit": 1000})
            assert not data["has_more"] and data["next_cursor"] is None
            assert len(data["items"]) == 2
            assert all(row["move"]["state"] == "posted" for row in data["items"])
            assert sum(Decimal(row["balance"]) for row in data["items"]) == 0
            assert sum(Decimal(row["debit"]) for row in data["items"]) == amount
            assert sum(Decimal(row["credit"]) for row in data["items"]) == amount
            posted_items.update(row["id"] for row in data["items"])

    calls.append("report.trial_balance")
    after = core._trial_balance_totals(client, alias, run_id, today)
    assert [a - b for a, b in zip(after, before, strict=True)] == [0, 420, 420, 0]
    assert client.capabilities == set(calls) == _CAPABILITIES
    assert replays == 14 and len(posted_items) == 8
    assert len(client.tracked["account.partial.reconcile"]) == 2
    assert len(client.tracked["account.full.reconcile"]) == 2
    return {
        "cli_calls": len(calls),
        "immediate_replays": replays,
        "posted_journal_items": len(posted_items),
        "prepayment_settlements": 2,
        "nullable_headers_verified": True,
        "positive_selection_verified": False,
        "nonempty_clearing_verified": False,
        "fixture_gap": "No existing eligible partner banks or fiscal positions",
        "trial_balance_delta": {"debit": "420", "credit": "420"},
    }


def test_financial_headers_and_prepayments_roll_back_per_alias():
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
        rows = [
            json.loads(line)
            for line in completed.stdout.splitlines()
            if line.startswith("{")
        ]
        assert len(rows) == 1
        result = rows[0]
        assert (
            result["alias"] == alias
            and result["database"] == lifecycle._DATABASES[alias]
        )
        assert result["user_id"] == 5 and result["company_id"] == 1
        assert result["rollback_verified"] and result["nullable_headers_verified"]
        assert result["positive_selection_verified"] is False
        assert result["nonempty_clearing_verified"] is False
        assert result["prepayment_settlements"] == 2
        assert result["immediate_replays"] == 14 and result["posted_journal_items"] == 8
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
