"""Shared rollback live proof for native invoice copy and type switching."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import sysconfig
import uuid
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

import test_document_lifecycle_write_batch_live as lifecycle
import test_payment_bank_capability_batch_live as core

_CAPABILITIES = {
    "customer_invoice.create",
    "vendor_bill.create",
    "invoice.post",
    "invoice.duplicate",
    "invoice.type.switch",
    "invoice.get",
    "journal_item.search",
}


def _run_chain(client, alias, run_id):
    from odoo import fields

    env = client.env
    assert env.uid == 5 and not env.su and env.company.id == 1
    assert env.company.account_storno is True
    ids = lifecycle._fixture_ids(env, alias)
    today = fields.Date.to_string(fields.Date.context_today(env.user))
    marker = f"ODACV4-{run_id.hex}-{alias}-copy-type"
    calls, replays = [], 0

    def read(capability, parameters):
        calls.append(capability)
        return core._cli(client, alias, run_id, capability, parameters)

    def twice(capability, parameters, key):
        nonlocal replays
        calls.extend([capability, capability])
        first = core._cli(client, alias, run_id, capability, parameters, key=key)
        tracked = {
            model: set(record_ids) for model, record_ids in client.tracked.items()
        }
        second = core._cli(client, alias, run_id, capability, parameters, key=key)
        assert not first["idempotent_replay"] and second["idempotent_replay"]
        assert first["result"] == second["result"] and client.tracked == tracked
        replays += 1
        return first["result"]

    def invoice(move_id):
        return read("invoice.get", {"invoice_id": move_id})

    def line_signature(data):
        return [
            (
                row["sequence"],
                row["display_type"],
                row["name"],
                row["product"]["id"] if row["product"] else None,
                row["account"]["id"] if row["account"] else None,
                Decimal(row["quantity"]),
                Decimal(row["price_unit"]),
                Decimal(row["discount"]),
                Decimal(row["price_subtotal"]),
                Decimal(row["price_total"]),
                tuple(tax["id"] for tax in row["taxes"]),
                row["analytic_distribution"],
            )
            for row in data["lines"]
        ]

    def business_signature(data):
        return (
            data["company_id"],
            data["journal"]["id"],
            data["currency"]["id"],
            data["partner"]["id"],
            data["fiscal_position_id"],
            *(
                Decimal(data[field])
                for field in ("amount_untaxed", "amount_tax", "amount_total")
            ),
            line_signature(data),
        )

    def journal(move_id, move_type, state):
        page = read("journal_item.search", {"move_id": move_id, "limit": 1000})
        assert not page["has_more"] and page["next_cursor"] is None
        rows = page["items"]
        assert len(rows) >= 2
        assert all(
            row["move"]["id"] == move_id
            and row["move"]["move_type"] == move_type
            and row["move"]["state"] == state
            for row in rows
        )
        assert sum(Decimal(row["balance"]) for row in rows) == 0
        balances = defaultdict(Decimal)
        for row in rows:
            balances[row["account"]["id"]] += Decimal(row["balance"])
        return dict(balances)

    for customer in (True, False):
        side = "customer" if customer else "supplier"
        create = "customer_invoice.create" if customer else "vendor_bill.create"
        source_type = "out_invoice" if customer else "in_invoice"
        refund_type = "out_refund" if customer else "in_refund"
        journal_id = ids["sale_journal" if customer else "purchase_journal"]
        account_id = ids["income" if customer else "expense"]

        def create_document(
            purpose,
            create=create,
            side=side,
            journal_id=journal_id,
            account_id=account_id,
        ):
            return twice(
                create,
                {
                    "partner_id": ids[side],
                    "journal_id": journal_id,
                    "date": today,
                    "invoice_date": today,
                    "currency_id": ids["currency"],
                    "payment_term_id": None,
                    "invoice_date_due": today,
                    "reference": f"{marker}-{side}-{purpose}",
                    "lines": [
                        {
                            "name": f"{marker}-{side}-{purpose}-line",
                            "account_id": account_id,
                            "product_id": None,
                            "quantity": "2",
                            "price_unit": "50",
                            "discount": "10",
                            "tax_ids": [],
                        }
                    ],
                },
                f"{marker}-{side}-{purpose}-create",
            )["id"]

        source_id = create_document("duplicate-source")
        twice(
            "invoice.post",
            {"move_id": source_id},
            f"invoice.post:{source_id}",
        )
        source_before = invoice(source_id)
        assert (
            source_before["state"] == "posted"
            and source_before["move_type"] == source_type
        )
        source_balances = journal(source_id, source_type, "posted")
        tracked_before = set(client.tracked["account.move"])
        copied = twice(
            "invoice.duplicate",
            {"move_id": source_id},
            f"{marker}-{side}-duplicate",
        )
        assert copied["model"] == "account.move" and copied["source_id"] == source_id
        assert copied["id"] != source_id and copied["state"] == "draft"
        assert copied["move_type"] == source_type
        assert client.tracked["account.move"] - tracked_before == {copied["id"]}
        duplicate = invoice(copied["id"])
        assert duplicate["state"] == "draft" and duplicate["move_type"] == source_type
        assert business_signature(duplicate) == business_signature(source_before)
        assert set(copied["line_ids"]).isdisjoint(
            {row["id"] for row in source_before["lines"]}
        )
        assert journal(copied["id"], source_type, "draft") == source_balances
        assert invoice(source_id) == source_before

        switch_id = create_document("switch-source")
        original = invoice(switch_id)
        assert original["state"] == "draft" and original["move_type"] == source_type
        original_balances = journal(switch_id, source_type, "draft")
        switched = twice(
            "invoice.type.switch",
            {"move_id": switch_id, "target_move_type": refund_type},
            f"invoice.type.switch:{switch_id}:{refund_type}",
        )
        assert switched["id"] == switched["source_id"] == switch_id
        assert switched["state"] == "draft" and switched["move_type"] == refund_type
        refund = invoice(switch_id)
        assert refund["state"] == "draft" and refund["move_type"] == refund_type
        assert business_signature(refund) == business_signature(original)
        refund_balances = journal(switch_id, refund_type, "draft")
        assert refund_balances == {
            account_id: -balance for account_id, balance in original_balances.items()
        }
        restored = twice(
            "invoice.type.switch",
            {"move_id": switch_id, "target_move_type": source_type},
            f"invoice.type.switch:{switch_id}:{source_type}",
        )
        assert restored["id"] == restored["source_id"] == switch_id
        assert restored["state"] == "draft" and restored["move_type"] == source_type
        restored_data = invoice(switch_id)
        assert business_signature(restored_data) == business_signature(original)
        assert journal(switch_id, source_type, "draft") == original_balances

    assert set(calls) == client.capabilities == _CAPABILITIES
    assert len(calls) == 46 and replays == 12
    assert len(client.tracked["account.move"]) == 6
    return {
        "cli_calls": len(calls),
        "immediate_replays": replays,
        "duplicated_documents": 2,
        "switched_documents": 2,
        "native_balancing_verified": True,
    }


def test_invoice_duplicate_type_switch_roll_back_per_alias():
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
        assert result["rollback_verified"] and result["native_balancing_verified"]
        assert result["cli_calls"] == 46 and result["immediate_replays"] == 12
        assert result["duplicated_documents"] == result["switched_documents"] == 2
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
