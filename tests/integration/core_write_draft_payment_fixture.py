#!/usr/bin/env python3
"""Create one isolated draft payment for the guarded core-write live smoke."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

_DATABASES = {
    "v4-dev": ("odoo_cli_v4_dev", 16),
    "v4-e2e": ("odoo_cli_v4_e2e", 8),
}
_COMPANY_ID = 1
_USER_ID = 5
_USER_LOGIN = "odacv4_g5_accountant"
_BANK_JOURNAL_ID = 14
_CURRENCY_ID = 6
_INBOUND_METHOD_LINE_ID = 3
_OUTSTANDING_RECEIPTS_ACCOUNT_ID = 153
_PAYMENT_DATE = "2026-08-24"


def _arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--odoo-config", type=Path, required=True)
    parser.add_argument("--odoo-source", type=Path, required=True)
    parser.add_argument("--alias", choices=tuple(_DATABASES), required=True)
    parser.add_argument(
        "--database",
        choices=tuple(value[0] for value in _DATABASES.values()),
        required=True,
    )
    parser.add_argument("--run-id", type=uuid.UUID, required=True)
    args = parser.parse_args(argv)
    expected_database, _ = _DATABASES[args.alias]
    if args.database != expected_database:
        parser.error("alias and physical database do not match")
    if not args.odoo_config.is_absolute() or not args.odoo_config.is_file():
        parser.error("odoo-config must be an existing absolute file")
    if not args.odoo_source.is_absolute() or not args.odoo_source.is_dir():
        parser.error("odoo-source must be an existing absolute directory")
    return args


def _one(records, label: str):
    if len(records) != 1:
        raise RuntimeError(f"expected one {label}, got {len(records)}")
    return records


def main(argv: list[str] | None = None) -> int:
    args = _arguments(argv)
    sys.path.insert(0, str(args.odoo_source.resolve(strict=True)))

    from odoo import api
    from odoo.orm.registry import Registry
    from odoo.tools import config as odoo_runtime_config

    odoo_runtime_config.parse_config(
        [
            "--config",
            str(args.odoo_config.resolve(strict=True)),
            "--database",
            args.database,
            "--no-http",
        ]
    )
    marker = f"ODACV4-{args.run_id}-{args.alias}-draft-payment"
    _, partner_id = _DATABASES[args.alias]

    registry = Registry(args.database)
    with registry.cursor() as cursor:
        context = {
            "allowed_company_ids": [_COMPANY_ID],
            "active_test": True,
            "lang": "en_US",
            "tz": "Asia/Shanghai",
        }
        env = api.Environment(cursor, _USER_ID, context)
        user = env.user
        if (
            env.uid != _USER_ID
            or user.id != _USER_ID
            or not user.active
            or user.login != _USER_LOGIN
            or _COMPANY_ID not in user.company_ids.ids
        ):
            raise RuntimeError("the fixed business user is unavailable")

        company = _one(
            env["res.company"].search([("id", "=", _COMPANY_ID)], limit=2),
            "company",
        )
        partner = _one(
            env["res.partner"].search(
                [
                    ("id", "=", partner_id),
                    ("company_id", "in", [False, _COMPANY_ID]),
                ],
                limit=2,
            ),
            "customer",
        )
        currency = _one(
            env["res.currency"]
            .with_context(active_test=False)
            .search([("id", "=", _CURRENCY_ID), ("active", "=", True)], limit=2),
            "CNY currency",
        )
        journal = _one(
            env["account.journal"]
            .with_context(active_test=False)
            .search(
                [
                    ("id", "=", _BANK_JOURNAL_ID),
                    ("company_id", "=", _COMPANY_ID),
                    ("type", "=", "bank"),
                    ("active", "=", True),
                ],
                limit=2,
            ),
            "bank journal",
        )
        method_line = _one(
            env["account.payment.method.line"].search(
                [
                    ("id", "=", _INBOUND_METHOD_LINE_ID),
                    ("journal_id", "=", journal.id),
                    ("payment_type", "=", "inbound"),
                    ("payment_method_id.code", "=", "manual"),
                    ("payment_account_id", "=", _OUTSTANDING_RECEIPTS_ACCOUNT_ID),
                ],
                limit=2,
            ),
            "manual inbound payment method",
        )
        if company.currency_id != currency or (
            journal.currency_id and journal.currency_id != currency
        ):
            raise RuntimeError("company 1 or journal 14 is not configured in CNY")

        payment_model = env["account.payment"].with_company(company)
        if not payment_model.has_access("read") or not payment_model.has_access(
            "create"
        ):
            raise RuntimeError(
                "business user cannot create the draft payment prerequisite"
            )
        payments = payment_model.search(
            [
                ("company_id", "=", _COMPANY_ID),
                ("memo", "=", marker),
            ],
            limit=2,
        )
        if payments:
            payment = _one(payments, "draft payment marker")
        else:
            payment = payment_model.create(
                {
                    "company_id": _COMPANY_ID,
                    "journal_id": journal.id,
                    "payment_method_line_id": method_line.id,
                    "payment_type": "inbound",
                    "partner_type": "customer",
                    "partner_id": partner.id,
                    "amount": 11.0,
                    "currency_id": currency.id,
                    "date": _PAYMENT_DATE,
                    "memo": marker,
                }
            )
        if (
            payment.state != "draft"
            or payment.company_id != company
            or payment.journal_id != journal
            or payment.currency_id != currency
            or payment.partner_id != partner
            or payment.payment_method_line_id != method_line
            or payment.payment_type != "inbound"
            or payment.partner_type != "customer"
            or payment.memo != marker
        ):
            raise RuntimeError(
                "draft payment prerequisite drifted from the fixed fixture"
            )
        cursor.commit()

        result = {
            "database": args.database,
            "company_id": company.id,
            "user_id": env.uid,
            "payment_id": payment.id,
            "state": payment.state,
            "marker": marker,
        }
    sys.stdout.write(
        json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
