"""One rollback-only manual AR/AP maturity workflow using existing CLI paths."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import sysconfig
import uuid
from copy import deepcopy
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import test_document_lifecycle_write_batch_live as lifecycle
import test_payment_bank_capability_batch_live as core

_CAPABILITIES = {
    "journal_entry.create",
    "journal_entry.lines.replace",
    "journal_entry.post",
    "journal_entry.get",
    "journal_item.search",
    "receivable.open_items.list",
    "payable.open_items.list",
    "report.aged_receivable",
    "report.aged_payable",
    "report.trial_balance",
    "reconciliation.apply",
    "reconciliation.undo",
}
_PERIODS = (*[f"period{i}" for i in range(6)], "total")


def test_shared_read_helper_binds_the_requested_capability(monkeypatch):
    from odoo_accounting_cli_v4 import cli

    class DispatchChecked(Exception):
        pass

    def check_dispatch(_argv, **kwargs):
        port = kwargs["port_factory"](None, None)
        assert port._action == expected_action
        raise DispatchChecked

    monkeypatch.setattr(cli, "main", check_dispatch)
    for capability, expected_action in (
        ("report.aged_receivable", "account.report.aged_receivable.read_page"),
        ("report.aged_payable", "account.report.aged_payable.read_page"),
        ("report.trial_balance", "account.report.trial_balance.read_page"),
        (
            "receivable.open_items.list",
            "account.move.line.receivable.open_items.search_page",
        ),
        ("payable.open_items.list", "account.move.line.payable.open_items.search_page"),
    ):
        with lifecycle.pytest.raises(DispatchChecked):
            core._cli(SimpleNamespace(), "v4-dev", uuid.uuid4(), capability, {})


def _entry_parameters(ids, side, marker, today, maturity, *, counterpart=False):
    customer = side == "receivable"
    amount = "120" if customer else "90"
    debit = customer != counterpart
    return {
        "journal_id": ids["general_journal"],
        "date": today,
        "reference": marker,
        "lines": [
            {
                "name": f"{marker}-due",
                "account_id": ids[side],
                "partner_id": ids["customer" if customer else "supplier"],
                "debit": amount if debit else "0",
                "credit": "0" if debit else amount,
                "date_maturity": maturity,
            },
            {
                "name": f"{marker}-offset",
                "account_id": ids["income" if customer else "expense"],
                "partner_id": None,
                "debit": "0" if debit else amount,
                "credit": amount if debit else "0",
                "date_maturity": None,
            },
        ],
    }


def _aged_totals(data):
    assert data["has_more"] is False and data["next_cursor"] is None
    totals = [line for line in data["lines"] if line["parent_id"] is None]
    assert len(totals) == 1
    columns = [column["expression_label"] for column in data["columns"]]
    assert columns == ["invoice_date", *_PERIODS]
    return {
        name: Decimal(totals[0]["values"][columns.index(name)]) for name in _PERIODS
    }


def _run_chain(client, alias, run_id):
    from odoo import fields

    from odoo_accounting_cli_v4.capabilities.core_writes import (
        _expected_idempotency_key,
    )

    env = client.env
    ids = lifecycle._fixture_ids(env, alias)
    assert env.uid == 5 and env.su is False and env.company.id == 1
    assert ids["currency"] == 6
    for side, account_type in (
        ("receivable", "asset_receivable"),
        ("payable", "liability_payable"),
    ):
        account = lifecycle._one(
            env["account.account"].search(
                [
                    ("company_ids", "in", [1]),
                    ("account_type", "=", account_type),
                    ("reconcile", "=", True),
                ],
                order="id",
                limit=1,
            ),
            side,
        )
        assert not account.currency_id or account.currency_id.id == ids["currency"]
        ids[side] = account.id
    today = fields.Date.to_string(fields.Date.context_today(env.user))
    past = (date.fromisoformat(today) - timedelta(days=45)).isoformat()
    future = (date.fromisoformat(today) + timedelta(days=15)).isoformat()
    tomorrow = (date.fromisoformat(today) + timedelta(days=1)).isoformat()
    marker = f"ODACV4-{run_id.hex}-{alias}-maturity"
    calls = []
    replays = 0

    def read(capability, parameters):
        calls.append(capability)
        return core._cli(client, alias, run_id, capability, parameters)

    def twice(capability, parameters, *, key=None):
        nonlocal replays
        key = key or _expected_idempotency_key(capability, parameters, 1)
        assert key is not None
        calls.extend([capability, capability])
        first = core._cli(client, alias, run_id, capability, parameters, key=key)
        second = core._cli(client, alias, run_id, capability, parameters, key=key)
        assert (
            first["idempotent_replay"] is False and second["idempotent_replay"] is True
        )
        assert first["result"] == second["result"]
        replays += 1
        return first["result"]

    def aged(side):
        return _aged_totals(
            read(f"report.aged_{side}", {"as_of": today, "limit": 1000})
        )

    def assert_aging(side, expected):
        actual = aged(side)
        assert {name: actual[name] - baseline[side][name] for name in _PERIODS} == {
            name: Decimal(expected.get(name, 0)) for name in _PERIODS
        }

    def open_items(side, **bounds):
        data = read(
            f"{side}.open_items.list",
            {
                "partner_id": ids["customer" if side == "receivable" else "supplier"],
                "account_id": ids[side],
                "journal_id": ids["general_journal"],
                "query": marker,
                "limit": 1000,
                **bounds,
            },
        )
        assert data["has_more"] is False and data["next_cursor"] is None
        return {item["id"]: item for item in data["items"]}

    def document(move_id, expected_lines):
        data = read("journal_entry.get", {"entry_id": move_id})
        assert (
            data["id"] == move_id and data["state"] == "draft" and data["date"] == today
        )
        assert {line["name"]: line["date_maturity"] for line in data["lines"]} == {
            line["name"]: line["date_maturity"] for line in expected_lines
        }

    current_items = set()

    def posted_items(move_id, side, expected_maturity, expected_balance):
        data = read("journal_item.search", {"move_id": move_id, "limit": 1000})
        assert data["has_more"] is False and data["next_cursor"] is None
        items = data["items"]
        assert len(items) == 2 and sum(Decimal(item["balance"]) for item in items) == 0
        assert all(
            item["move"]["id"] == move_id and item["move"]["state"] == "posted"
            for item in items
        )
        selected = [item for item in items if item["account"]["id"] == ids[side]]
        assert len(selected) == 1
        principal = selected[0]
        assert principal["date_maturity"] == expected_maturity
        assert Decimal(principal["balance"]) == expected_balance
        assert principal["reconciled"] is False
        current_items.update(item["id"] for item in items)
        return principal["id"]

    baseline = {side: aged(side) for side in ("receivable", "payable")}
    calls.append("report.trial_balance")
    trial_before = core._trial_balance_totals(client, alias, run_id, today)
    originals, counterparts = {}, {}
    documents = []
    for side in ("receivable", "payable"):
        parameters = _entry_parameters(
            ids, side, f"{marker}-{side}-source", today, future
        )
        created = twice(
            "journal_entry.create", parameters, key=f"{marker}-{side}-source"
        )
        move_id = created["id"]
        documents.append(move_id)
        document(move_id, parameters["lines"])
        for maturity in (None, past):
            parameters["lines"][0]["date_maturity"] = maturity
            twice(
                "journal_entry.lines.replace",
                {"move_id": move_id, "lines": deepcopy(parameters["lines"])},
            )
            document(move_id, parameters["lines"])
        twice("journal_entry.post", {"move_id": move_id})
        amount = Decimal(120 if side == "receivable" else -90)
        originals[side] = posted_items(move_id, side, past, amount)
        due = open_items(side, due_date_to=today)
        assert set(due) == {originals[side]}
        assert due[originals[side]]["due_date"] == past
        assert Decimal(due[originals[side]]["amount_residual"]) == amount
        assert open_items(side, due_date_from=tomorrow) == {}
        assert_aging(side, {"period2": abs(amount), "total": abs(amount)})

    for side in ("receivable", "payable"):
        parameters = _entry_parameters(
            ids, side, f"{marker}-{side}-counter", today, future, counterpart=True
        )
        created = twice(
            "journal_entry.create", parameters, key=f"{marker}-{side}-counter"
        )
        move_id = created["id"]
        documents.append(move_id)
        twice("journal_entry.post", {"move_id": move_id})
        amount = Decimal(-120 if side == "receivable" else 90)
        counterparts[side] = posted_items(move_id, side, future, amount)
        future_items = open_items(side, due_date_from=tomorrow)
        assert set(future_items) == {counterparts[side]}
        assert future_items[counterparts[side]]["due_date"] == future
        assert Decimal(future_items[counterparts[side]]["amount_residual"]) == amount

    for side in ("receivable", "payable"):
        pair = sorted([originals[side], counterparts[side]])
        result = twice("reconciliation.apply", {"line_ids": pair})
        assert result["reconciled"] is True and result["line_ids"] == pair
        assert open_items(side) == {}
        assert_aging(side, {})

    for side in ("receivable", "payable"):
        pair = sorted([originals[side], counterparts[side]])
        result = twice("reconciliation.undo", {"line_ids": pair})
        assert result["reconciled"] is False and result["line_ids"] == pair
        items = open_items(side)
        assert set(items) == set(pair)
        amount = Decimal(120 if side == "receivable" else -90)
        assert Decimal(items[originals[side]]["amount_residual"]) == amount
        assert Decimal(items[counterparts[side]]["amount_residual"]) == -amount
        assert items[originals[side]]["due_date"] == past
        assert items[counterparts[side]]["due_date"] == future
        assert_aging(side, {"period0": -abs(amount), "period2": abs(amount)})

    calls.append("report.trial_balance")
    trial_after = core._trial_balance_totals(client, alias, run_id, today)
    assert [
        after - before for before, after in zip(trial_before, trial_after, strict=True)
    ] == [0, 420, 420, 0]
    assert set(calls) == client.capabilities == _CAPABILITIES
    assert len(documents) == 4 and len(current_items) == 8 and replays == 16
    assert len(client.tracked["account.partial.reconcile"]) == 2
    assert len(client.tracked["account.full.reconcile"]) == 2
    return {
        "source_documents": len(documents),
        "posted_journal_items": len(current_items),
        "cli_calls": len(calls),
        "immediate_replays": replays,
        "maturity_updates": 4,
        "cleared_dates": 2,
        "reconciled_pairs": 2,
        "undone_pairs": 2,
        "receivable_amount": "120",
        "payable_amount": "90",
        "trial_balance_delta": {"debit": "420", "credit": "420"},
        "aging_and_open_items_verified": True,
    }


def test_manual_entry_maturity_aging_and_reconciliation_roll_back_per_alias():
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
        data = rows[0]
        assert (
            data["alias"] == alias and data["database"] == lifecycle._DATABASES[alias]
        )
        assert data["user_id"] == 5 and data["company_id"] == 1
        assert (
            data["rollback_verified"] is True
            and data["aging_and_open_items_verified"] is True
        )
        assert set(data["capabilities"]) == _CAPABILITIES
        assert data["source_documents"] == 4 and data["posted_journal_items"] == 8
        assert (
            data["immediate_replays"] == 16
            and data["reconciled_pairs"] == data["undone_pairs"] == 2
        )
        print(json.dumps(data, sort_keys=True, separators=(",", ":")), flush=True)


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
        assert env.uid == 5 and env.su is False and env.user.active
        assert env.user.login == lifecycle._USER_LOGIN and 1 in env.user.company_ids.ids
        client = core._RuntimeClient(env)
        client.tracked = tracked
        details = _run_chain(client, args.alias, args.run_id)
    except BaseException as exc:  # noqa: BLE001 - always rollback before re-raising
        failure = exc
    finally:
        try:
            if env is not None:
                core._collect_marked(env, tracked, args.run_id.hex)
        except Exception as exc:  # noqa: BLE001 - collection must not prevent rollback
            if failure is None:
                failure = exc
            else:
                failure.add_note(f"rollback ID collection also failed: {exc}")
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
    sys.stdout.write(
        json.dumps(
            {
                "alias": args.alias,
                "database": args.database,
                "company_id": 1,
                "user_id": 5,
                "execution": "in_process_cli_real_orm",
                "rollback_verified": True,
                "capabilities": sorted(client.capabilities),
                **details,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_live_worker())
