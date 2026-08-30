"""Rollback-only CLI acceptance for invoice-line deferred dates.

Uses the existing in-process CLI/real-ORM helpers, not cross-process transport.
Business writes use public CLI commands. ORM access only selects existing master
data, inspects automatic deferral links/scheduling, and verifies rollback.
No company settings, bank setup, or permissions are changed; future entries are
never posted early.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import sysconfig
import uuid
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import test_payment_bank_capability_batch_live as core

_ALLOW_ENV = "ODACV4_ALLOW_DEFERRED_INVOICE_LINES_SMOKE"
_CAPABILITIES = {
    "customer_invoice.create",
    "vendor_bill.create",
    "invoice.get",
    "invoice.lines.replace",
    "invoice.post",
    "journal_entry.get",
    "customer_credit_note.create",
    "vendor_refund.create",
}
_SCENARIOS = [
    "customer_dates_replace_clear_restore",
    "customer_automatic_deferrals",
    "customer_credit_note_dates",
    "vendor_automatic_deferrals",
    "vendor_refund_dates",
]


def _enabled_runtime() -> tuple[Path, dict[str, Any]]:
    assert core.pytest is not None
    if os.environ.get(_ALLOW_ENV) != "1":
        core.pytest.skip(f"set {_ALLOW_ENV}=1 to authorize isolated write smoke")
    raw = os.environ.get(core._CONFIG_ENV)
    if not raw or not Path(raw).is_file():
        core.pytest.skip(f"{core._CONFIG_ENV} must name an existing runtime file")
    path = Path(raw)
    runtime = json.loads(path.read_text(encoding="utf-8"))
    aliases = runtime.get("aliases")
    assert isinstance(aliases, dict) and set(aliases) == set(core._ALIASES)
    assert {
        alias: aliases[alias].get("database") for alias in core._ALIASES
    } == core._DATABASES
    assert all(
        aliases[alias].get("companies", {}).get(str(core._COMPANY_ID))
        == [core._USER_LOGIN]
        for alias in core._ALIASES
    )
    return path, runtime


def _run_worker(
    alias: str, run_id: uuid.UUID, config_path: Path, runtime: dict[str, Any]
) -> None:
    command, timeout = core._worker_command(alias, run_id, config_path, runtime)
    command[1] = str(Path(__file__).resolve())
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = os.pathsep.join(
        part
        for part in (
            str(core._root() / "src"),
            sysconfig.get_path("purelib"),
            environment.get("PYTHONPATH"),
        )
        if part
    )
    completed = subprocess.run(
        command,
        cwd=core._root(),
        env=environment,
        text=True,
        capture_output=True,
        check=False,
        timeout=max(timeout, 900),
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert completed.stderr == "" and len(completed.stdout.splitlines()) == 1
    assert json.loads(completed.stdout) == {
        "alias": alias,
        "database": core._DATABASES[alias],
        "company_id": core._COMPANY_ID,
        "user_id": core._USER_ID,
        "execution": "in_process_cli_real_orm",
        "capabilities": sorted(_CAPABILITIES),
        "scenarios": _SCENARIOS,
        "source_invoices": 2,
        "draft_refunds": 2,
        "automatic_deferred_entries": 6,
        "rollback_verified": True,
    }
    print(completed.stdout.strip(), flush=True)


if core.pytest is not None:

    @core.pytest.mark.integration
    def test_deferred_invoice_lines_roll_back_per_alias() -> None:
        config_path, runtime = _enabled_runtime()
        run_id = uuid.uuid4()
        for alias in core._ALIASES:
            _run_worker(alias, run_id, config_path, runtime)


def _fixture_ids(env: Any, alias: str) -> dict[str, int]:
    company = core._one(env["res.company"].browse(core._COMPANY_ID).exists(), "company")
    partners = core._PARTNERS[alias]
    found = env["res.partner"].search(
        [
            ("id", "in", sorted(partners.values())),
            ("company_id", "in", [False, company.id]),
        ]
    )
    assert set(found.ids) == set(partners.values())
    assert {"deferred_start_date", "deferred_end_date"} <= set(
        env["account.move.line"]._fields
    )
    ids = {**partners, "currency": company.currency_id.id}
    for kind, journal_type, account_type, deferred_type in (
        ("revenue", "sale", "income", "liability_current"),
        ("expense", "purchase", "expense", "asset_current"),
    ):
        journal = core._one(
            env["account.journal"].search(
                [("company_id", "=", company.id), ("type", "=", journal_type)],
                order="id",
                limit=1,
            ),
            f"{journal_type} journal",
        )
        account = core._one(
            env["account.account"].search(
                [
                    ("company_ids", "in", [company.id]),
                    ("account_type", "=", account_type),
                ],
                order="id",
                limit=1,
            ),
            f"{account_type} account",
        )
        deferred_journal = getattr(company, f"deferred_{kind}_journal_id")
        deferred_account = getattr(company, f"deferred_{kind}_account_id")
        if (
            getattr(company, f"generate_deferred_{kind}_entries_method")
            != "on_validation"
            or getattr(company, f"deferred_{kind}_amount_computation_method") != "month"
            or not deferred_journal
            or not deferred_journal.active
            or deferred_journal.company_id != company
            or deferred_journal.type != "general"
            or not deferred_account
            or not deferred_account.active
            or company.id not in deferred_account.company_ids.ids
            or deferred_account.account_type != deferred_type
        ):
            raise RuntimeError(f"existing {kind} deferral configuration is unsuitable")
        assert not journal.currency_id or journal.currency_id == company.currency_id
        ids.update(
            {
                f"{kind}_journal": journal.id,
                f"{kind}_account": account.id,
                f"{kind}_deferred_journal": deferred_journal.id,
                f"{kind}_deferred_account": deferred_account.id,
            }
        )
    return ids


def _collect_deferred(env: Any, tracked: dict[str, set[int]]) -> None:
    """Keep automatic children even though invoice.post only returns the source."""
    sources = env["account.move"].browse(sorted(tracked["account.move"])).exists()
    moves = sources | sources.deferred_move_ids
    tracked["account.move"].update(moves.ids)
    tracked["account.move.line"].update(moves.line_ids.ids)


def _read_invoice(
    client: core._RuntimeClient,
    alias: str,
    run_id: uuid.UUID,
    invoice_id: int,
    expected_line: dict[str, Any],
) -> dict[str, Any]:
    data = core._cli(client, alias, run_id, "invoice.get", {"invoice_id": invoice_id})
    assert Decimal(data["amount_total"]) == Decimal(data["amount_untaxed"]) == 120
    assert Decimal(data["amount_tax"]) == 0
    line = core._one(data["lines"], "invoice line")[0]
    assert line["display_type"] == "product"
    assert line["account"]["id"] == expected_line["account_id"]
    assert line["taxes"] == []
    for field in ("name", "deferred_start_date", "deferred_end_date"):
        assert line[field] == expected_line[field]
    return data


def _assert_automatic_entries(
    client: core._RuntimeClient,
    alias: str,
    run_id: uuid.UUID,
    ids: dict[str, int],
    kind: str,
    invoice_id: int,
    dates: tuple[date, date, date],
) -> set[int]:
    _collect_deferred(client.env, client.tracked)
    moves = (
        client.env["account.move"].browse(invoice_id).deferred_move_ids.sorted("date")
    )
    assert len(moves) == 3
    sign = Decimal(1 if kind == "expense" else -1)
    expected = zip(dates, (Decimal(120), Decimal(60), Decimal(60)), strict=True)
    for index, (move, (move_date, amount)) in enumerate(
        zip(moves, expected, strict=True)
    ):
        assert move.deferred_original_move_ids.ids == [invoice_id]
        data = core._cli(
            client, alias, run_id, "journal_entry.get", {"entry_id": move.id}
        )
        assert data["date"] == move_date.isoformat()
        assert data["state"] == ("posted" if index == 0 else "draft")
        assert data["journal"]["id"] == ids[f"{kind}_deferred_journal"]
        if index:
            assert move.date > dates[0] and move.auto_post == "at_date"
        assert (
            Decimal(data["totals"]["debit"])
            == Decimal(data["totals"]["credit"])
            == amount
        )
        assert Decimal(data["totals"]["balance"]) == 0
        assert len(data["lines"]) == 2
        balances = {
            line["account"]["id"]: Decimal(line["balance"]) for line in data["lines"]
        }
        source_balance = (-sign if index == 0 else sign) * amount
        assert balances == {
            ids[f"{kind}_account"]: source_balance,
            ids[f"{kind}_deferred_account"]: -source_balance,
        }
        assert all(
            Decimal(line["debit"]) - Decimal(line["credit"]) == Decimal(line["balance"])
            for line in data["lines"]
        )
    return set(moves.ids)


def _exercise_invoice(
    client: core._RuntimeClient,
    alias: str,
    run_id: uuid.UUID,
    ids: dict[str, int],
    today: date,
    start: date,
    first_end: date,
    end: date,
    scenarios: list[str],
    *,
    supplier: bool,
) -> tuple[int, int, set[int]]:
    kind = "expense" if supplier else "revenue"
    side = "vendor" if supplier else "customer"
    capability = "vendor_bill.create" if supplier else "customer_invoice.create"
    marker = f"ODACV4-DEFERRED-{alias}-{run_id.hex}-{side}"
    line = {
        "name": marker,
        "product_id": None,
        "account_id": ids[f"{kind}_account"],
        "quantity": "1",
        "price_unit": "120",
        "discount": "0",
        "tax_ids": [],
        "deferred_start_date": start.isoformat(),
        "deferred_end_date": end.isoformat(),
    }
    invoice = core._write(
        client,
        alias,
        run_id,
        capability,
        {
            "partner_id": ids["supplier" if supplier else "customer"],
            "journal_id": ids[f"{kind}_journal"],
            "invoice_date": today.isoformat(),
            "currency_id": ids["currency"],
            "lines": [line],
        },
        explicit_key=f"deferred:{capability}:{alias}:{run_id.hex}",
    )
    invoice_id = invoice["id"]
    data = _read_invoice(client, alias, run_id, invoice_id, line)
    assert data["state"] == "draft"
    assert data["move_type"] == ("in_invoice" if supplier else "out_invoice")
    if not supplier:
        for start_value, end_value in (
            (
                (start + timedelta(days=1)).isoformat(),
                (end - timedelta(days=1)).isoformat(),
            ),
            (None, None),
            (start.isoformat(), end.isoformat()),
        ):
            replacement = {
                **line,
                "deferred_start_date": start_value,
                "deferred_end_date": end_value,
            }
            core._write(
                client,
                alias,
                run_id,
                "invoice.lines.replace",
                {"move_id": invoice_id, "lines": [replacement]},
                explicit_key=f"invoice.lines.replace:{invoice_id}:{core._digest([replacement])}",
            )
            data = _read_invoice(client, alias, run_id, invoice_id, replacement)
            assert data["state"] == "draft"
        scenarios.append("customer_dates_replace_clear_restore")

    core._write(client, alias, run_id, "invoice.post", {"move_id": invoice_id})
    data = _read_invoice(client, alias, run_id, invoice_id, line)
    assert data["state"] == "posted" and Decimal(data["amount_residual"]) == 120
    generated_ids = _assert_automatic_entries(
        client, alias, run_id, ids, kind, invoice_id, (today, first_end, end)
    )
    scenarios.append(f"{side}_automatic_deferrals")

    refund_capability = (
        "vendor_refund.create" if supplier else "customer_credit_note.create"
    )
    refund_line = {
        **line,
        "name": marker + "-REFUND",
        "deferred_start_date": (start + timedelta(days=1)).isoformat(),
        "deferred_end_date": (end - timedelta(days=1)).isoformat(),
    }
    refund = core._write(
        client,
        alias,
        run_id,
        refund_capability,
        {
            "move_id": invoice_id,
            "date": today.isoformat(),
            "reason": marker + " refund",
            "lines": [refund_line],
        },
        explicit_key=f"deferred:{refund_capability}:{alias}:{run_id.hex}",
    )
    assert refund["source_id"] == invoice_id
    data = _read_invoice(client, alias, run_id, refund["id"], refund_line)
    assert data["state"] == "draft"
    assert data["move_type"] == ("in_refund" if supplier else "out_refund")
    scenarios.append(
        "vendor_refund_dates" if supplier else "customer_credit_note_dates"
    )
    return invoice_id, refund["id"], generated_ids


def _live_worker(argv: list[str] | None = None) -> int:
    args = core._arguments(argv)
    if os.environ.get(_ALLOW_ENV) != "1":
        raise RuntimeError(f"{_ALLOW_ENV}=1 is required for the live worker")
    sys.path.insert(0, str(args.odoo_source.resolve(strict=True)))
    sys.path.insert(0, str((core._root() / "src").resolve(strict=True)))
    from odoo import api, fields
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
    tracked: dict[str, set[int]] = {model: set() for model in core._BUSINESS_MODELS}
    source_ids: set[int] = set()
    refund_ids: set[int] = set()
    generated_ids: set[int] = set()
    scenarios: list[str] = []
    env = client = None
    failure: BaseException | None = None
    try:
        env = api.Environment(
            cursor,
            core._USER_ID,
            {
                "allowed_company_ids": [core._COMPANY_ID],
                "active_test": True,
                "lang": "en_US",
                "tz": "Asia/Shanghai",
            },
        )
        assert env.uid == env.user.id == core._USER_ID
        assert env.user.active and env.user.login == core._USER_LOGIN
        assert core._COMPANY_ID in env.user.company_ids.ids
        client = core._RuntimeClient(env)
        client.tracked = tracked
        ids = _fixture_ids(env, args.alias)
        today = fields.Date.context_today(env.user)
        start = (today.replace(day=28) + timedelta(days=4)).replace(day=1)
        second_start = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
        first_end = second_start - timedelta(days=1)
        end = (second_start.replace(day=28) + timedelta(days=4)).replace(
            day=1
        ) - timedelta(days=1)
        for supplier in (False, True):
            source_id, refund_id, automatic_ids = _exercise_invoice(
                client,
                args.alias,
                args.run_id,
                ids,
                today,
                start,
                first_end,
                end,
                scenarios,
                supplier=supplier,
            )
            source_ids.add(source_id)
            refund_ids.add(refund_id)
            generated_ids.update(automatic_ids)
        assert client.capabilities == _CAPABILITIES and scenarios == _SCENARIOS
        assert len(source_ids) == len(refund_ids) == 2 and len(generated_ids) == 6
    except BaseException as exc:  # noqa: BLE001 - re-raised after rollback verification
        failure = exc
    finally:
        try:
            if env is not None:
                core._collect_marked(env, tracked, args.run_id.hex)
                _collect_deferred(env, tracked)
        except Exception as exc:  # noqa: BLE001 - collection must never prevent rollback
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
    assert client is not None
    sys.stdout.write(
        json.dumps(
            {
                "alias": args.alias,
                "database": args.database,
                "company_id": core._COMPANY_ID,
                "user_id": core._USER_ID,
                "execution": "in_process_cli_real_orm",
                "capabilities": sorted(client.capabilities),
                "scenarios": scenarios,
                "source_invoices": len(source_ids),
                "draft_refunds": len(refund_ids),
                "automatic_deferred_entries": len(generated_ids),
                "rollback_verified": True,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_live_worker())
