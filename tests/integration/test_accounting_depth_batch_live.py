"""One rollback-only dual-database smoke for the accounting depth batch."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any

try:
    import pytest
except ModuleNotFoundError:
    if "--live-worker" not in sys.argv:
        raise
    pytest = None


_CONFIG_ENV = "ODOO_ACCOUNTING_CLI_V4_CONFIG"
_ALLOW_ENV = "ODACV4_ALLOW_ACCOUNTING_DEPTH_SMOKE"
_ALIASES = ("v4-dev", "v4-e2e")
_DATABASES = {
    "v4-dev": "odoo_cli_v4_dev",
    "v4-e2e": "odoo_cli_v4_e2e",
}
_PARTNERS = {
    "v4-dev": {"customer": 16, "supplier": 17},
    "v4-e2e": {"customer": 8, "supplier": 9},
}
_COMPANY_ID = 1
_USER_ID = 5
_USER_LOGIN = "odacv4_g5_accountant"
_TARGET_CAPABILITIES = (
    "customer_invoice.create",
    "vendor_bill.create",
    "invoice.lines.replace",
    "customer_credit_note.create",
    "vendor_refund.create",
    "journal_entry.create",
    "journal_entry.lines.replace",
    "receivable.payment.register",
    "payable.payment.register",
    "invoice.payment_status.inspect",
    "reconciliation.apply",
    "reconciliation.undo",
)
_HELPER_CAPABILITIES = (
    "invoice.post",
    "journal_entry.post",
    "payment.create",
    "payment.post",
)


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _enabled_runtime() -> tuple[Path, dict[str, Any]]:
    assert pytest is not None
    if os.environ.get(_ALLOW_ENV) != "1":
        pytest.skip(f"set {_ALLOW_ENV}=1 to authorize isolated write smoke")
    raw = os.environ.get(_CONFIG_ENV)
    if not raw:
        pytest.skip(f"{_CONFIG_ENV} is not configured")
    path = Path(raw)
    if not path.is_file():
        pytest.skip(f"{_CONFIG_ENV} does not name an existing file")
    document = json.loads(path.read_text(encoding="utf-8"))
    aliases = document.get("aliases")
    assert isinstance(aliases, dict) and set(aliases) == set(_ALIASES)
    assert {alias: aliases[alias].get("database") for alias in _ALIASES} == _DATABASES
    assert all(
        aliases[alias].get("companies", {}).get(str(_COMPANY_ID)) == [_USER_LOGIN]
        for alias in _ALIASES
    )
    return path, document


def _worker_command(
    alias: str,
    run_id: uuid.UUID,
    config_path: Path,
    runtime: dict[str, Any],
) -> tuple[list[str], int]:
    bridge = runtime.get("bridge")
    assert isinstance(bridge, dict) and set(bridge) == {"argv", "timeout_seconds"}
    argv = bridge["argv"]
    assert isinstance(argv, list) and len(argv) == 8
    assert argv[2::2] == ["--runtime-config", "--odoo-config", "--odoo-source"]
    assert Path(argv[3]).resolve(strict=True) == config_path.resolve(strict=True)
    executable = Path(argv[0])
    odoo_config = Path(argv[5])
    odoo_source = Path(argv[7])
    assert executable.is_absolute() and executable.is_file()
    assert odoo_config.is_absolute() and odoo_config.is_file()
    assert odoo_source.is_absolute() and odoo_source.is_dir()
    timeout = bridge["timeout_seconds"]
    assert isinstance(timeout, int) and not isinstance(timeout, bool) and timeout > 0
    return (
        [
            str(executable),
            str(Path(__file__).resolve()),
            "--live-worker",
            "--odoo-config",
            str(odoo_config),
            "--odoo-source",
            str(odoo_source),
            "--alias",
            alias,
            "--database",
            _DATABASES[alias],
            "--run-id",
            str(run_id),
        ],
        timeout,
    )


def _run_worker(
    alias: str,
    run_id: uuid.UUID,
    config_path: Path,
    runtime: dict[str, Any],
) -> None:
    command, timeout = _worker_command(alias, run_id, config_path, runtime)
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = os.pathsep.join(
        part for part in (str(_root() / "src"), environment.get("PYTHONPATH")) if part
    )
    completed = subprocess.run(
        command,
        cwd=_root(),
        env=environment,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert completed.stderr == ""
    assert len(completed.stdout.splitlines()) == 1
    assert json.loads(completed.stdout) == {
        "alias": alias,
        "capabilities": list(_TARGET_CAPABILITIES),
        "company_id": _COMPANY_ID,
        "database": _DATABASES[alias],
        "helper_capabilities": list(_HELPER_CAPABILITIES),
        "rollback_verified": True,
        "user_id": _USER_ID,
    }


if pytest is not None:

    @pytest.mark.integration
    def test_accounting_depth_batch_rolls_back_one_real_chain_per_alias() -> None:
        config_path, runtime = _enabled_runtime()
        run_id = uuid.uuid4()
        for alias in _ALIASES:
            _run_worker(alias, run_id, config_path, runtime)


def _arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-worker", action="store_true", required=True)
    parser.add_argument("--odoo-config", type=Path, required=True)
    parser.add_argument("--odoo-source", type=Path, required=True)
    parser.add_argument("--alias", choices=_ALIASES, required=True)
    parser.add_argument("--database", choices=tuple(_DATABASES.values()), required=True)
    parser.add_argument("--run-id", type=uuid.UUID, required=True)
    args = parser.parse_args(argv)
    if args.database != _DATABASES[args.alias]:
        parser.error("alias and physical database do not match")
    if not args.odoo_config.is_absolute() or not args.odoo_config.is_file():
        parser.error("odoo-config must be an existing absolute file")
    if not args.odoo_source.is_absolute() or not args.odoo_source.is_dir():
        parser.error("odoo-source must be an existing absolute directory")
    return args


def _one(records: Any, label: str) -> Any:
    if len(records) != 1:
        raise RuntimeError(f"expected one {label}, got {len(records)}")
    return records


def _digest(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:32]


def _key(
    capability_id: str,
    parameters: dict[str, Any],
    explicit: str | None,
) -> str:
    if explicit is not None:
        return explicit
    if capability_id in {"invoice.lines.replace", "journal_entry.lines.replace"}:
        return f"{capability_id}:{parameters['move_id']}:{_digest(parameters['lines'])}"
    if capability_id == "reconciliation.apply" and "invoice_id" in parameters:
        return (
            f"reconciliation.apply:{parameters['invoice_id']}:"
            f"{parameters['outstanding_line_id']}"
        )
    if capability_id == "reconciliation.undo" and "invoice_id" in parameters:
        first, second = sorted(
            (parameters["invoice_line_id"], parameters["counterpart_line_id"])
        )
        return (
            f"reconciliation.undo:{parameters['invoice_id']}:"
            f"{parameters['partial_reconcile_id']}:"
            f"{first}:{second}"
        )
    record_id = parameters.get("move_id", parameters.get("payment_id"))
    return f"{capability_id}:{record_id}"


def _request(
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    parameters: dict[str, Any],
    operation_key: str,
) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "request_id": str(
            uuid.uuid5(
                run_id,
                f"accounting-depth:{alias}:{capability_id}:{operation_key}",
            )
        ),
        "context": {
            "database": alias,
            "company_id": _COMPANY_ID,
            "user_login": _USER_LOGIN,
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": parameters,
    }


class _CoreWritePort:
    def __init__(self, env: Any) -> None:
        self.env = env

    @property
    def user_id(self) -> int:
        return self.env.uid

    def execute(self, **payload: Any) -> dict[str, Any]:
        from odoo_accounting_cli_v4.bridge.core_writes_runtime import dispatch
        from odoo_accounting_cli_v4.bridge.runtime import RuntimeFailure

        # Real CLI calls get a fresh bridge Environment.  This rollback-only
        # chain reuses one cursor, so clear computed-field caches between calls.
        self.env.invalidate_all()
        return dispatch(self.env, payload, payload["company_id"], RuntimeFailure)


class _InvoiceStatusPort:
    def __init__(self, env: Any) -> None:
        self.env = env

    @property
    def user_id(self) -> int:
        return self.env.uid

    def inspect_payment_status(
        self, *, company_id: int, invoice_id: int
    ) -> dict[str, Any]:
        from odoo_accounting_cli_v4.bridge.runtime import (
            _dispatch_invoice_payment_status,
        )

        self.env.invalidate_all()
        return _dispatch_invoice_payment_status(
            self.env,
            {"company_id": company_id, "move_id": invoice_id},
            company_id,
        )


def _write(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    parameters: dict[str, Any],
    *,
    explicit_key: str | None = None,
    twice: bool = True,
) -> dict[str, Any]:
    from odoo_accounting_cli_v4.capabilities.core_writes import execute_core_write

    operation_key = _key(capability_id, parameters, explicit_key)
    request = _request(alias, run_id, capability_id, parameters, operation_key)
    port = _CoreWritePort(env)
    first = execute_core_write(
        port,
        capability_id,
        request,
        operation_key,
        capability_id,
    )
    if first["idempotent_replay"] is not False:
        raise RuntimeError(f"{capability_id} unexpectedly replayed its first write")
    if not twice:
        return first["result"]
    second = execute_core_write(
        port,
        capability_id,
        request,
        operation_key,
        capability_id,
    )
    if second["idempotent_replay"] is not True or second["result"] != first["result"]:
        raise RuntimeError(f"{capability_id} did not replay deterministically")
    return first["result"]


def _payment_status(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    invoice_id: int,
    case: str,
) -> dict[str, Any]:
    from odoo_accounting_cli_v4.capabilities.invoices import (
        inspect_invoice_payment_status,
    )

    request = _request(
        alias,
        run_id,
        "invoice.payment_status.inspect",
        {"invoice_id": invoice_id},
        case,
    )
    return inspect_invoice_payment_status(_InvoiceStatusPort(env), request)


def _account(env: Any, account_type: str) -> Any:
    return _one(
        env["account.account"].search(
            [
                ("company_ids", "in", [_COMPANY_ID]),
                ("account_type", "=", account_type),
            ],
            order="id",
            limit=1,
        ),
        f"{account_type} account",
    )


def _fixture_ids(
    env: Any,
    alias: str,
    marker: str,
    record_ids: dict[str, list[int]],
) -> dict[str, int]:
    from odoo import SUPERUSER_ID

    company = _one(env["res.company"].browse(_COMPANY_ID).exists(), "company")
    partner_ids = _PARTNERS[alias]
    partners = env["res.partner"].search(
        [
            ("id", "in", sorted(partner_ids.values())),
            ("company_id", "in", [False, _COMPANY_ID]),
        ]
    )
    if set(partners.ids) != set(partner_ids.values()):
        raise RuntimeError("the fixed customer or supplier is unavailable")

    def journal(journal_type: str) -> Any:
        return _one(
            env["account.journal"].search(
                [
                    ("company_id", "=", _COMPANY_ID),
                    ("type", "=", journal_type),
                ],
                order="id",
                limit=1,
            ),
            f"{journal_type} journal",
        )

    bank = journal("bank")
    payment_term = _one(
        env["account.payment.term"].search(
            [("company_id", "in", [False, _COMPANY_ID])],
            order="id",
            limit=1,
        ),
        "payment term",
    )
    if len(payment_term.line_ids) != 1:
        raise RuntimeError("the payment term must contain exactly one installment")
    foreign_currency = _one(
        env["res.currency"].search(
            [("active", "=", True), ("id", "!=", company.currency_id.id)],
            order="id",
            limit=1,
        ),
        "active foreign currency",
    )
    product = (
        env["product.product"]
        .with_user(SUPERUSER_ID)
        .with_context(allowed_company_ids=[_COMPANY_ID])
        .create(
            {
                "name": marker,
                "type": "service",
                "sale_ok": True,
                "purchase_ok": True,
            }
        )
    )
    record_ids["product"].append(product.id)

    def method_line(payment_type: str) -> Any:
        line = _one(
            env["account.payment.method.line"].search(
                [
                    ("journal_id", "=", bank.id),
                    ("payment_type", "=", payment_type),
                    ("payment_method_id.code", "=", "manual"),
                ],
                order="id",
                limit=1,
            ),
            f"{payment_type} manual payment method line",
        )
        payment_account = line.payment_account_id
        if (
            line.company_id.id != _COMPANY_ID
            or not payment_account
            or _COMPANY_ID not in payment_account.company_ids.ids
            or not payment_account.reconcile
        ):
            raise RuntimeError(
                f"{payment_type} payment method line has no valid outstanding account"
            )
        return line

    return {
        "customer": partner_ids["customer"],
        "supplier": partner_ids["supplier"],
        "currency": company.currency_id.id,
        "foreign_currency": foreign_currency.id,
        "sale_journal": journal("sale").id,
        "purchase_journal": journal("purchase").id,
        "general_journal": journal("general").id,
        "bank_journal": bank.id,
        "income": _account(env, "income").id,
        "expense": _account(env, "expense").id,
        "current_asset": _account(env, "asset_current").id,
        "payment_term": payment_term.id,
        "product": product.id,
        "inbound_method": method_line("inbound").id,
    }


def _invoice_line(
    ids: dict[str, int],
    marker: str,
    *,
    account: str,
    amount: str,
) -> dict[str, Any]:
    return {
        "name": marker,
        "product_id": ids["product"],
        "account_id": ids[account],
        "quantity": "1",
        "price_unit": amount,
        "discount": "0",
        "tax_ids": [],
    }


def _create_and_post_documents(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    ids: dict[str, int],
    today: str,
    marker: str,
    record_ids: dict[str, list[int]],
) -> tuple[int, int]:
    invoice = _write(
        env,
        alias,
        run_id,
        "customer_invoice.create",
        {
            "partner_id": ids["customer"],
            "journal_id": ids["sale_journal"],
            "invoice_date": today,
            "currency_id": ids["currency"],
            "invoice_date_due": None,
            "payment_term_id": ids["payment_term"],
            "reference": f"INV-{marker}",
            "payment_reference": f"PAY-{marker}",
            "lines": [
                {
                    "name": marker,
                    "account_id": ids["income"],
                    "quantity": "2",
                    "price_unit": "60",
                    "tax_ids": [],
                    "product_id": ids["product"],
                    "discount": "10",
                }
            ],
        },
        explicit_key=f"invoice-{run_id.hex}-{alias}",
    )
    invoice_id = invoice["id"]
    record_ids["moves"].append(invoice_id)
    draft_invoice = env["account.move"].browse(invoice_id)
    draft_line = _one(draft_invoice.invoice_line_ids, "draft invoice line")
    if (
        draft_invoice.invoice_payment_term_id.id != ids["payment_term"]
        or draft_line.product_id.id != ids["product"]
        or Decimal(str(draft_line.discount)) != Decimal(10)
    ):
        raise RuntimeError("rich invoice-create fields were not persisted")
    _write(
        env,
        alias,
        run_id,
        "invoice.lines.replace",
        {
            "move_id": invoice_id,
            "lines": [_invoice_line(ids, marker, account="income", amount="100")],
        },
    )
    _write(env, alias, run_id, "invoice.post", {"move_id": invoice_id})

    bill = _write(
        env,
        alias,
        run_id,
        "vendor_bill.create",
        {
            "partner_id": ids["supplier"],
            "journal_id": ids["purchase_journal"],
            "invoice_date": today,
            "currency_id": ids["currency"],
            "invoice_date_due": today,
            "payment_term_id": None,
            "reference": f"BILL-{marker}",
            "payment_reference": None,
            "lines": [
                {
                    "name": marker,
                    "account_id": ids["expense"],
                    "quantity": "1",
                    "price_unit": "80",
                    "tax_ids": [],
                    "product_id": ids["product"],
                    "discount": "0",
                }
            ],
        },
        explicit_key=f"bill-{run_id.hex}-{alias}",
    )
    bill_id = bill["id"]
    record_ids["moves"].append(bill_id)
    _write(env, alias, run_id, "invoice.post", {"move_id": bill_id})

    invoice_move = env["account.move"].browse(invoice_id)
    bill_move = env["account.move"].browse(bill_id)
    if (
        invoice_move.ref != f"INV-{marker}"
        or invoice_move.payment_reference != f"PAY-{marker}"
        or bill_move.ref != f"BILL-{marker}"
        or invoice_move.invoice_line_ids.product_id.id != ids["product"]
        or bill_move.invoice_line_ids.product_id.id != ids["product"]
    ):
        raise RuntimeError("rich invoice or bill fields were not persisted and posted")

    refund_ids: list[int] = []
    for index, amount in enumerate(("25", "15"), start=1):
        refund = _write(
            env,
            alias,
            run_id,
            "customer_credit_note.create",
            {
                "move_id": invoice_id,
                "date": today,
                "reason": f"partial-{index}-{marker}",
                "lines": [
                    _invoice_line(
                        ids,
                        f"credit-{index}-{marker}",
                        account="income",
                        amount=amount,
                    )
                ],
            },
            explicit_key=f"credit-{index}-{run_id.hex}-{alias}",
        )
        refund_ids.append(refund["id"])
        record_ids["moves"].append(refund["id"])
    vendor_refund = _write(
        env,
        alias,
        run_id,
        "vendor_refund.create",
        {
            "move_id": bill_id,
            "date": today,
            "reason": f"partial-vendor-{marker}",
            "lines": [
                _invoice_line(
                    ids,
                    f"vendor-refund-{marker}",
                    account="expense",
                    amount="20",
                )
            ],
        },
        explicit_key=f"vendor-refund-{run_id.hex}-{alias}",
    )
    refund_ids.append(vendor_refund["id"])
    record_ids["moves"].append(vendor_refund["id"])
    if (
        len(
            env["account.move"].search(
                [("reversed_entry_id", "=", invoice_id), ("id", "in", refund_ids)]
            )
        )
        != 2
    ):
        raise RuntimeError("one source invoice did not retain two distinct refunds")
    return invoice_id, bill_id


def _exercise_journal_entry(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    ids: dict[str, int],
    today: str,
    marker: str,
    record_ids: dict[str, list[int]],
) -> int:
    entry = _write(
        env,
        alias,
        run_id,
        "journal_entry.create",
        {
            "journal_id": ids["general_journal"],
            "date": today,
            "reference": f"JE-{marker}",
            "lines": [
                {
                    "name": marker,
                    "account_id": ids["expense"],
                    "partner_id": None,
                    "debit": "50",
                    "credit": "0",
                },
                {
                    "name": marker,
                    "account_id": ids["current_asset"],
                    "partner_id": None,
                    "debit": "0",
                    "credit": "50",
                },
            ],
        },
        explicit_key=f"entry-{run_id.hex}-{alias}",
    )
    entry_id = entry["id"]
    record_ids["moves"].append(entry_id)
    lines = [
        {
            "name": marker,
            "account_id": ids["expense"],
            "partner_id": None,
            "debit": "75",
            "credit": "0",
            "currency_id": ids["foreign_currency"],
            "amount_currency": "150",
        },
        {
            "name": marker,
            "account_id": ids["current_asset"],
            "partner_id": None,
            "debit": "0",
            "credit": "75",
        },
    ]
    _write(
        env,
        alias,
        run_id,
        "journal_entry.lines.replace",
        {"move_id": entry_id, "lines": lines},
    )
    _write(env, alias, run_id, "journal_entry.post", {"move_id": entry_id})
    move = env["account.move"].browse(entry_id)
    foreign_line = _one(
        move.line_ids.filtered(
            lambda line: line.currency_id.id == ids["foreign_currency"]
        ),
        "foreign-currency entry line",
    )
    if move.ref != f"JE-{marker}" or Decimal(
        str(foreign_line.amount_currency)
    ) != Decimal(150):
        raise RuntimeError("rich journal-entry fields were not persisted and posted")
    return entry_id


def _exercise_payments_and_outstanding(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    ids: dict[str, int],
    today: str,
    marker: str,
    invoice_id: int,
    bill_id: int,
    record_ids: dict[str, list[int]],
) -> None:
    receivable = _write(
        env,
        alias,
        run_id,
        "receivable.payment.register",
        {
            "move_id": invoice_id,
            "journal_id": ids["bank_journal"],
            "payment_date": today,
            "amount": "40",
        },
        explicit_key=f"partial-receivable-{marker}",
    )
    record_ids["payments"].append(receivable["id"])
    payable = _write(
        env,
        alias,
        run_id,
        "payable.payment.register",
        {
            "move_id": bill_id,
            "journal_id": ids["bank_journal"],
            "payment_date": today,
            "amount": "30",
        },
        explicit_key=f"partial-payable-{marker}",
    )
    record_ids["payments"].append(payable["id"])
    invoice = env["account.move"].browse(invoice_id)
    bill = env["account.move"].browse(bill_id)
    if Decimal(str(invoice.amount_residual)) != Decimal(60) or Decimal(
        str(bill.amount_residual)
    ) != Decimal(50):
        raise RuntimeError("partial payment did not preserve the expected residual")

    standalone = _write(
        env,
        alias,
        run_id,
        "payment.create",
        {
            "payment_type": "inbound",
            "partner_type": "customer",
            "partner_id": ids["customer"],
            "amount": "25",
            "currency_id": ids["currency"],
            "journal_id": ids["bank_journal"],
            "payment_method_line_id": ids["inbound_method"],
            "date": today,
            "payment_reference": marker,
        },
        explicit_key=f"standalone-payment-{marker}",
    )
    standalone_id = standalone["id"]
    record_ids["payments"].append(standalone_id)
    _write(
        env,
        alias,
        run_id,
        "payment.post",
        {"payment_id": standalone_id},
        twice=False,
    )
    before = _payment_status(env, alias, run_id, invoice_id, "before-assign")
    registered_reconciliations = [
        item
        for item in before["reconciliations"]
        if item["payment_id"] == receivable["id"]
    ]
    if len(registered_reconciliations) != 1:
        raise RuntimeError("registered receivable payment has no stable partial")
    registered_partial_id = registered_reconciliations[0]["id"]
    candidate = next(
        (
            item
            for item in before["outstanding_items"]
            if item["payment_id"] == standalone_id
        ),
        None,
    )
    if candidate is None:
        raise RuntimeError("standalone payment was absent from outstanding items")
    applied = _write(
        env,
        alias,
        run_id,
        "reconciliation.apply",
        {"invoice_id": invoice_id, "outstanding_line_id": candidate["line_id"]},
    )
    if len(applied["partial_reconcile_ids"]) != 1:
        raise RuntimeError("outstanding assignment did not create exactly one partial")
    applied_partial_id = applied["partial_reconcile_ids"][0]
    after_apply = _payment_status(env, alias, run_id, invoice_id, "after-assign")
    invoice.invalidate_recordset(["amount_residual"])
    if Decimal(str(invoice.amount_residual)) != Decimal(35):
        raise RuntimeError("outstanding assignment did not reduce the residual to 35")
    if any(
        item["line_id"] == candidate["line_id"]
        for item in after_apply["outstanding_items"]
    ):
        raise RuntimeError("assigned outstanding item remained available")
    reconciliations = [
        item
        for item in after_apply["reconciliations"]
        if item["id"] == applied_partial_id
    ]
    if len(reconciliations) != 1:
        raise RuntimeError("payment status omitted the applied partial reconciliation")
    reconciliation = reconciliations[0]
    undone = _write(
        env,
        alias,
        run_id,
        "reconciliation.undo",
        {
            "invoice_id": invoice_id,
            "partial_reconcile_id": reconciliation["id"],
            "invoice_line_id": reconciliation["invoice_line_id"],
            "counterpart_line_id": reconciliation["counterpart_line_id"],
        },
    )
    if (
        undone["state"] != "partial"
        or undone["partial_reconcile_ids"] != [registered_partial_id]
        or undone["full_reconcile_id"] is not None
        or undone["reconciled"]
    ):
        raise RuntimeError("reconciliation undo returned an incomplete invoice graph")
    after_undo = _payment_status(env, alias, run_id, invoice_id, "after-undo")
    invoice.invalidate_recordset(["amount_residual"])
    if Decimal(str(invoice.amount_residual)) != Decimal(60):
        raise RuntimeError("reconciliation undo did not restore the residual to 60")
    if any(item["id"] == applied_partial_id for item in after_undo["reconciliations"]):
        raise RuntimeError("payment status retained the undone partial reconciliation")
    if not any(
        item["id"] == registered_partial_id for item in after_undo["reconciliations"]
    ):
        raise RuntimeError("undo removed the pre-existing registered-payment partial")
    if not any(
        item["line_id"] == candidate["line_id"]
        for item in after_undo["outstanding_items"]
    ):
        raise RuntimeError("undo did not restore the outstanding item")


def _verify_rollback(
    registry: Any,
    *,
    record_ids: dict[str, list[int]],
    marker: str,
) -> None:
    from odoo import SUPERUSER_ID, api

    cursor = registry.cursor()
    try:
        cursor.execute("SET TRANSACTION READ ONLY")
        env = api.Environment(
            cursor,
            SUPERUSER_ID,
            {"allowed_company_ids": [_COMPANY_ID], "active_test": False},
        )
        remaining = {
            "moves": env["account.move"].search_count(
                [("id", "in", record_ids["moves"])], limit=1
            ),
            "payments": env["account.payment"].search_count(
                [("id", "in", record_ids["payments"])], limit=1
            ),
            "product": env["product.product"].search_count(
                [("id", "in", record_ids["product"])], limit=1
            ),
            "marker_moves": env["account.move"].search_count(
                [
                    "|",
                    "|",
                    "|",
                    ("ref", "ilike", marker),
                    ("payment_reference", "ilike", marker),
                    ("invoice_origin", "ilike", marker),
                    ("line_ids.name", "ilike", marker),
                ],
                limit=1,
            ),
            "marker_payments": env["account.payment"].search_count(
                [
                    "|",
                    ("payment_reference", "ilike", marker),
                    ("memo", "ilike", marker),
                ],
                limit=1,
            ),
            "marker_product": env["product.product"].search_count(
                [("name", "ilike", marker)], limit=1
            ),
        }
        if any(remaining.values()):
            raise RuntimeError(f"transaction fixtures survived rollback: {remaining}")
    finally:
        cursor.rollback()
        cursor.close()


def _live_worker(argv: list[str] | None = None) -> int:
    args = _arguments(argv)
    sys.path.insert(0, str(args.odoo_source.resolve(strict=True)))
    sys.path.insert(0, str((_root() / "src").resolve(strict=True)))

    from odoo import api, fields
    from odoo.orm.registry import Registry
    from odoo.tools import config as odoo_config

    odoo_config.parse_config(
        [
            "--config",
            str(args.odoo_config.resolve(strict=True)),
            "--database",
            args.database,
            "--no-http",
            "--logfile=/dev/null",
        ]
    )
    registry = Registry(args.database)
    cursor = registry.cursor()
    marker = f"ODACV4-DEPTH-{args.alias}-{args.run_id.hex}"
    record_ids = {"moves": [], "payments": [], "product": []}
    failure: Exception | None = None
    try:
        env = api.Environment(
            cursor,
            _USER_ID,
            {
                "allowed_company_ids": [_COMPANY_ID],
                "active_test": True,
                "lang": "en_US",
                "tz": "Asia/Shanghai",
            },
        )
        user = env.user
        if (
            env.uid != _USER_ID
            or user.id != _USER_ID
            or not user.active
            or user.login != _USER_LOGIN
            or _COMPANY_ID not in user.company_ids.ids
        ):
            raise RuntimeError("the fixed business user is unavailable")
        ids = _fixture_ids(env, args.alias, marker, record_ids)
        today = fields.Date.to_string(fields.Date.context_today(env.user))
        invoice_id, bill_id = _create_and_post_documents(
            env, args.alias, args.run_id, ids, today, marker, record_ids
        )
        _exercise_journal_entry(
            env, args.alias, args.run_id, ids, today, marker, record_ids
        )
        _exercise_payments_and_outstanding(
            env,
            args.alias,
            args.run_id,
            ids,
            today,
            marker,
            invoice_id,
            bill_id,
            record_ids,
        )
    except Exception as exc:  # noqa: BLE001 - rollback must precede re-raising
        failure = exc
    finally:
        cursor.rollback()
        cursor.close()

    _verify_rollback(registry, record_ids=record_ids, marker=marker)
    if failure is not None:
        raise failure
    if not all(record_ids.values()):
        raise RuntimeError("the live fixtures were not initialized")
    sys.stdout.write(
        json.dumps(
            {
                "alias": args.alias,
                "capabilities": list(_TARGET_CAPABILITIES),
                "company_id": _COMPANY_ID,
                "database": args.database,
                "helper_capabilities": list(_HELPER_CAPABILITIES),
                "rollback_verified": True,
                "user_id": _USER_ID,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_live_worker())
