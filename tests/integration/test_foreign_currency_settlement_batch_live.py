"""Rollback-only USD invoice and bill settlement at two historical rates.

The worker uses twelve existing public CLI capabilities in one outer transaction
per isolated database.  The fixed fixtures provide USD/CNY rates of 1.36 on
2025-01-15 and 1.37 on 2025-02-01; no rate or other master data is changed.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import sysconfig
import uuid
from datetime import date as date_type
from decimal import Decimal
from pathlib import Path

import test_document_lifecycle_write_batch_live as lifecycle
import test_payment_bank_capability_batch_live as core

_ALLOW_ENV = "ODACV4_ALLOW_FOREIGN_CURRENCY_SETTLEMENT_SMOKE"
_USD_ID = 1
_CNY_ID = 6
_BANK_JOURNAL_ID = 14
_INVOICE_DATE = "2025-01-15"
_PAYMENT_DATE = "2025-02-01"
_INVOICE_RATE = Decimal("1.36")
_PAYMENT_RATE = Decimal("1.37")
_FOREIGN_AMOUNT = Decimal(100)
_CAPABILITIES = {
    "currency.convert",
    "currency.rate.list",
    "customer_invoice.create",
    "vendor_bill.create",
    "invoice.post",
    "invoice.get",
    "receivable.payment.register",
    "payable.payment.register",
    "invoice.payment_status.inspect",
    "payment.get",
    "journal_item.search",
    "report.trial_balance",
}


def _run_chain(client, alias, run_id):
    from odoo_accounting_cli_v4.capabilities.core_writes import (
        _expected_idempotency_key,
    )

    env = client.env
    assert env.uid == 5 and env.su is False and env.company.id == 1
    ids = lifecycle._fixture_ids(env, alias)
    assert ids["currency"] == _CNY_ID
    company_currency = env.company.currency_id
    usd = lifecycle._one(
        env["res.currency"].search([("id", "=", _USD_ID), ("active", "=", True)]),
        "active USD fixture",
    )
    assert (company_currency.id, company_currency.name) == (_CNY_ID, "CNY")
    assert usd.name == "USD"

    def converted(date):
        return Decimal(str(usd._convert(1.0, company_currency, env.company, date)))

    assert converted(_INVOICE_DATE) == _INVOICE_RATE
    assert converted(_PAYMENT_DATE) == _PAYMENT_RATE
    assert _INVOICE_RATE != _PAYMENT_RATE
    bank = lifecycle._one(
        env["account.journal"].search(
            [
                ("id", "=", _BANK_JOURNAL_ID),
                ("company_id", "=", 1),
                ("type", "=", "bank"),
            ]
        ),
        "fixed bank journal",
    )
    assert bank.id == _BANK_JOURNAL_ID
    exchange_journal = lifecycle._one(
        env.company.currency_exchange_journal_id,
        "configured exchange gain or loss journal",
    )
    expected_exchange_date = str(
        exchange_journal.with_context(
            move_date=date_type.fromisoformat(_PAYMENT_DATE)
        ).accounting_date
    )
    assert expected_exchange_date >= _PAYMENT_DATE

    marker = f"ODACV4-{run_id.hex}-{alias}-fx-settlement"
    calls = []
    replays = 0
    move_items = {}

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

    rate_page = read(
        "currency.rate.list",
        {
            "date_from": _INVOICE_DATE,
            "date_to": _PAYMENT_DATE,
            "currency_id": _USD_ID,
            "limit": 10,
            "cursor": None,
        },
    )
    assert rate_page["has_more"] is False and rate_page["next_cursor"] is None
    rates = {item["date"]: item for item in rate_page["items"]}
    assert set(rates) == {_INVOICE_DATE, _PAYMENT_DATE}
    for date, expected in (
        (_INVOICE_DATE, _INVOICE_RATE),
        (_PAYMENT_DATE, _PAYMENT_RATE),
    ):
        rate = rates[date]
        assert rate["currency"] == {"id": _USD_ID, "code": "USD"}
        assert rate["company_currency"] == {"id": _CNY_ID, "code": "CNY"}
        assert rate["requested_company_id"] == rate["source_company_id"] == 1
        assert Decimal(rate["company_units_per_foreign_unit"]) == expected
        conversion = read(
            "currency.convert",
            {
                "amount": str(_FOREIGN_AMOUNT),
                "from_currency_id": _USD_ID,
                "to_currency_id": _CNY_ID,
                "date": date,
            },
        )
        assert set(conversion) == {
            "company_id",
            "date",
            "amount",
            "converted_amount",
            "from_currency",
            "to_currency",
        }
        assert conversion["company_id"] == 1 and conversion["date"] == date
        assert Decimal(conversion["amount"]) == _FOREIGN_AMOUNT
        assert Decimal(conversion["converted_amount"]) == _FOREIGN_AMOUNT * expected
        assert conversion["from_currency"] == {"id": _USD_ID, "code": "USD"}
        assert conversion["to_currency"] == {"id": _CNY_ID, "code": "CNY"}

    def trial_balance():
        data = read(
            "report.trial_balance",
            {
                "date_from": _INVOICE_DATE,
                "date_to": expected_exchange_date,
                "limit": 1000,
                "cursor": None,
            },
        )
        assert [column["expression_label"] for column in data["columns"]] == [
            "balance",
            "debit",
            "credit",
            "balance",
        ]
        assert data["has_more"] is False and data["next_cursor"] is None
        totals = [line for line in data["lines"] if line["parent_id"] is None]
        assert len(totals) == 1 and all(
            value is not None for value in totals[0]["values"]
        )
        values = [Decimal(value) for value in totals[0]["values"]]
        assert values[0] == values[3] == 0 and values[1] == values[2]
        return values

    def journal_items(move_id):
        assert move_id not in move_items
        page = read(
            "journal_item.search",
            {"move_id": move_id, "posted_only": True, "limit": 1000},
        )
        assert page["has_more"] is False and page["next_cursor"] is None
        items = page["items"]
        assert items and len({item["id"] for item in items}) == len(items)
        assert all(
            item["company_id"] == 1
            and item["move"]["id"] == move_id
            and item["move"]["state"] == "posted"
            for item in items
        )
        assert sum(Decimal(item["balance"]) for item in items) == 0
        assert sum(Decimal(item["debit"]) for item in items) == sum(
            Decimal(item["credit"]) for item in items
        )
        move_items[move_id] = items
        return items

    before = trial_balance()
    exchange_move_ids = set()
    payment_ids = set()
    source_ids = set()
    for customer in (True, False):
        side = "customer" if customer else "supplier"
        create_capability = (
            "customer_invoice.create" if customer else "vendor_bill.create"
        )
        register_capability = (
            "receivable.payment.register" if customer else "payable.payment.register"
        )
        source = twice(
            create_capability,
            {
                "partner_id": ids[side],
                "journal_id": ids["sale_journal" if customer else "purchase_journal"],
                "date": _INVOICE_DATE,
                "invoice_date": _INVOICE_DATE,
                "invoice_date_due": _INVOICE_DATE,
                "currency_id": _USD_ID,
                "payment_term_id": None,
                "reference": f"{marker}-{side}",
                "lines": [
                    {
                        "name": f"{marker}-{side}-line",
                        "account_id": ids["income" if customer else "expense"],
                        "product_id": None,
                        "quantity": "1",
                        "price_unit": str(_FOREIGN_AMOUNT),
                        "discount": "0",
                        "tax_ids": [],
                    }
                ],
            },
            key=f"{marker}-{side}-create",
        )
        source_id = source["id"]
        source_ids.add(source_id)
        posted = twice("invoice.post", {"move_id": source_id})
        assert posted["id"] == source_id and posted["state"] == "posted"

        invoice = read("invoice.get", {"invoice_id": source_id})
        assert invoice["id"] == source_id and invoice["state"] == "posted"
        assert invoice["currency"] == {"id": _USD_ID, "code": "USD"}
        assert Decimal(invoice["amount_total"]) == _FOREIGN_AMOUNT
        assert Decimal(invoice["amount_residual"]) == _FOREIGN_AMOUNT

        source_lines = journal_items(source_id)
        assert len(source_lines) == 2
        assert {item["currency"]["id"] for item in source_lines} == {_USD_ID}
        assert sum(Decimal(item["debit"]) for item in source_lines) == Decimal(136)
        assert sum(Decimal(item["credit"]) for item in source_lines) == Decimal(136)
        assert {abs(Decimal(item["amount_currency"])) for item in source_lines} == {
            _FOREIGN_AMOUNT
        }

        registered = twice(
            register_capability,
            {
                "move_id": source_id,
                "journal_id": _BANK_JOURNAL_ID,
                "payment_date": _PAYMENT_DATE,
            },
        )
        assert registered["source_id"] == source_id
        assert registered["state"] in {"in_process", "paid"}
        assert registered["reconciled"] is True
        payment_id = registered["id"]
        payment_ids.add(payment_id)

        payment = read("payment.get", {"payment_id": payment_id})
        assert payment["date"] == _PAYMENT_DATE
        assert payment["state"] in {"in_process", "paid"}
        assert payment["payment_type"] == ("inbound" if customer else "outbound")
        assert payment["partner_type"] == side
        assert payment["partner"]["id"] == ids[side]
        assert payment["currency"] == {"id": _USD_ID, "code": "USD"}
        assert payment["company_currency"] == {"id": _CNY_ID, "code": "CNY"}
        assert Decimal(payment["amount"]) == _FOREIGN_AMOUNT
        assert abs(Decimal(payment["amount_signed"])) == _FOREIGN_AMOUNT
        assert abs(Decimal(payment["amount_company_currency_signed"])) == Decimal(137)
        linked = payment["reconciled_invoices" if customer else "reconciled_bills"]
        assert [document["id"] for document in linked] == [source_id]
        payment_move_id = payment["move_id"]
        assert payment_move_id == payment["journal_entry"]["id"]

        payment_lines = journal_items(payment_move_id)
        assert len(payment_lines) == 2
        assert sum(Decimal(item["debit"]) for item in payment_lines) == Decimal(137)
        assert sum(Decimal(item["credit"]) for item in payment_lines) == Decimal(137)

        status = read("invoice.payment_status.inspect", {"invoice_id": source_id})
        assert status["id"] == source_id and status["state"] == "posted"
        assert status["currency"] == {"id": _USD_ID, "code": "USD"}
        assert status["company_currency"] == {"id": _CNY_ID, "code": "CNY"}
        assert Decimal(status["amount_residual"]) == 0
        assert status["payment_state"] in {"in_payment", "paid"}
        assert len(status["receivable_payable_lines"]) == 1
        term_line = status["receivable_payable_lines"][0]
        assert term_line["reconciled"] is True
        assert Decimal(term_line["amount_residual"]) == 0
        assert Decimal(term_line["amount_residual_currency"]) == 0
        assert len(status["reconciliations"]) == 1
        reconciliation = status["reconciliations"][0]
        assert reconciliation["payment_id"] == payment_id
        assert reconciliation["currency"] == {"id": _USD_ID, "code": "USD"}
        assert reconciliation["company_currency"] == {
            "id": _CNY_ID,
            "code": "CNY",
        }
        assert abs(Decimal(reconciliation["amount"])) == _FOREIGN_AMOUNT
        exchange_move_id = reconciliation["exchange_move_id"]
        assert exchange_move_id is not None
        exchange_move_ids.add(exchange_move_id)

        exchange_lines = journal_items(exchange_move_id)
        assert len(exchange_lines) == 2
        assert {item["date"] for item in exchange_lines} == {expected_exchange_date}
        assert {abs(Decimal(item["balance"])) for item in exchange_lines} == {
            Decimal(1)
        }
        assert sum(Decimal(item["debit"]) for item in exchange_lines) == 1
        assert sum(Decimal(item["credit"]) for item in exchange_lines) == 1
        term_account_id = term_line["account"]["id"]
        exchange_term_lines = [
            item for item in exchange_lines if item["account"]["id"] == term_account_id
        ]
        assert len(exchange_term_lines) == 1
        assert exchange_term_lines[0]["reconciled"] is True

    assert len(source_ids) == len(payment_ids) == len(exchange_move_ids) == 2
    created_debit = sum(
        Decimal(item["debit"]) for items in move_items.values() for item in items
    )
    created_credit = sum(
        Decimal(item["credit"]) for items in move_items.values() for item in items
    )
    assert created_debit == created_credit == Decimal(548)
    after = trial_balance()
    trial_balance_delta = [new - old for old, new in zip(before, after, strict=True)]
    assert trial_balance_delta == [
        Decimal(0),
        created_debit,
        created_credit,
        Decimal(0),
    ], trial_balance_delta
    assert set(calls) == client.capabilities == _CAPABILITIES
    assert len(calls) == 29 and replays == 6
    return {
        "cli_calls": len(calls),
        "immediate_replays": replays,
        "source_documents": len(source_ids),
        "payments": len(payment_ids),
        "exchange_moves": len(exchange_move_ids),
        "exchange_move_date": expected_exchange_date,
        "invoice_rate": str(_INVOICE_RATE),
        "payment_rate": str(_PAYMENT_RATE),
        "trial_balance_debit_delta": str(created_debit),
        "trial_balance_credit_delta": str(created_credit),
        "foreign_currency_settlement_verified": True,
    }


def test_foreign_currency_settlement_rolls_back_per_alias():
    config_path, runtime = lifecycle._enabled_runtime(_ALLOW_ENV)
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
        assert result["rollback_verified"] is True
        assert result["foreign_currency_settlement_verified"] is True
        assert result["cli_calls"] == 29 and result["immediate_replays"] == 6
        assert result["source_documents"] == result["payments"] == 2
        assert result["exchange_moves"] == 2
        assert result["exchange_move_date"] >= _PAYMENT_DATE
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
    details = None
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
        assert env.uid == 5 and env.su is False and env.user.active
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
    assert client is not None and details is not None
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
