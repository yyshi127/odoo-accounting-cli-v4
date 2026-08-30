"""Transactional dual-database smoke for the payment/bank capability batch.

The worker uses the public CLI in-process with normal Odoo ports and a shared
real ORM transaction as the configured accountant.  This checks CLI contracts
and accounting effects, not cross-process transport.  Business records are only
created/changed through CLI commands; ORM reads select master data and audit
rollback.  No fixture or accounting data is committed.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import subprocess
import sys
import sysconfig
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
_ALLOW_ENV = "ODACV4_ALLOW_PAYMENT_BANK_CAPABILITY_SMOKE"
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
_CAPABILITIES = (
    "bank.transaction.search",
    "bank.transaction.reconciliation.get",
    "bank.transaction.match_candidates.list",
    "payment.create",
    "payment.update_draft",
    "payment.reset_to_draft",
    "bank.transaction.update",
    "bank.transaction.match",
    "bank.transaction.unmatch",
    "reconciliation.write_off",
    "payment.post",
    "customer_invoice.create",
    "invoice.post",
    "bank.transaction.record",
    "invoice.payment_status.inspect",
    "receivable.payment.register",
    "payment.get",
    "vendor_bill.create",
    "payable.payment.register",
    "journal_entry.create",
    "journal_entry.post",
    "journal_entry.reverse",
    "journal_entry.get",
    "report.trial_balance",
)
_SCENARIOS = (
    "payment_lifecycle",
    "bank_match_unmatch_writeoff",
    "customer_split_payment_bank_match",
    "supplier_bill_payment",
    "adjustment_reversal",
    "trial_balance_movement",
)
_BUSINESS_MODELS = (
    "account.payment",
    "account.move",
    "account.move.line",
    "account.bank.statement.line",
    "account.partial.reconcile",
    "account.full.reconcile",
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
    assert isinstance(bridge, dict) and set(bridge) == {
        "argv",
        "timeout_seconds",
    }
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
        part
        for part in (
            str(_root() / "src"),
            sysconfig.get_path("purelib"),
            environment.get("PYTHONPATH"),
        )
        if part
    )
    completed = subprocess.run(
        command,
        cwd=_root(),
        env=environment,
        text=True,
        capture_output=True,
        check=False,
        timeout=max(timeout, 900),
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert completed.stderr == ""
    assert len(completed.stdout.splitlines()) == 1
    assert json.loads(completed.stdout) == {
        "alias": alias,
        "capabilities": sorted(_CAPABILITIES),
        "company_id": _COMPANY_ID,
        "database": _DATABASES[alias],
        "execution": "in_process_cli_real_orm",
        "rollback_verified": True,
        "scenarios": list(_SCENARIOS),
        "trial_balance_period_delta": {"debit": "510", "credit": "510"},
        "user_id": _USER_ID,
    }
    print(completed.stdout.strip(), flush=True)


if pytest is not None:

    @pytest.mark.integration
    def test_payment_bank_batch_rolls_back_one_real_chain_per_alias() -> None:
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


def _write_key(
    capability_id: str,
    parameters: dict[str, Any],
    explicit: str | None = None,
) -> str:
    if explicit is not None:
        return explicit
    if capability_id == "payment.update_draft":
        return (
            f"payment.update_draft:{parameters['payment_id']}:"
            f"{_digest(parameters['changes'])}"
        )
    if capability_id == "payment.reset_to_draft":
        return f"payment.reset_to_draft:{parameters['payment_id']}"
    if capability_id == "bank.transaction.update":
        target = parameters["changes"]
    elif capability_id == "bank.transaction.match":
        target = parameters["candidate_line_ids"]
    elif capability_id == "reconciliation.write_off":
        target = {
            "write_off_account_id": parameters["write_off_account_id"],
            "expected_residual_amount": parameters["expected_residual_amount"],
            "label": parameters["label"],
        }
    else:
        target = None
    if target is not None:
        return f"{capability_id}:{parameters['transaction_id']}:{_digest(target)}"
    if capability_id == "bank.transaction.unmatch":
        return f"bank.transaction.unmatch:{parameters['transaction_id']}"
    record_id = parameters.get("move_id", parameters.get("payment_id"))
    return f"{capability_id}:{record_id}"


def _request(
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "request_id": str(
            uuid.uuid5(
                run_id, f"payment-bank:{alias}:{capability_id}:{_digest(parameters)}"
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


class _RuntimeClient:
    def __init__(self, env: Any) -> None:
        self.env = env
        self.capabilities: set[str] = set()
        self.tracked: dict[str, set[int]] = {model: set() for model in _BUSINESS_MODELS}
        self.last_runtime_failure: Exception | None = None

    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        from odoo_accounting_cli_v4.bridge.client import BridgeError
        from odoo_accounting_cli_v4.bridge.runtime import RuntimeFailure, _dispatch

        self.env.invalidate_all()
        try:
            page = _dispatch(self.env, action, payload, _COMPANY_ID, (_COMPANY_ID,))
        except RuntimeFailure as exc:
            self.last_runtime_failure = exc
            raise BridgeError(
                exc.code,
                str(exc),
                exit_code=exc.exit_code,
                retryable=exc.retryable,
                details=exc.details,
            ) from exc
        result = page.get("result")
        if isinstance(result, dict) and result.get("model") in self.tracked:
            if result["id"] is not None:
                self.tracked[result["model"]].add(result["id"])
            self.tracked["account.move.line"].update(result.get("line_ids", []))
            self.tracked["account.partial.reconcile"].update(
                result.get("partial_reconcile_ids", [])
            )
            if result.get("full_reconcile_id"):
                self.tracked["account.full.reconcile"].add(result["full_reconcile_id"])
            _collect_related(self.env, self.tracked)
        return page


def _cli(
    client: _RuntimeClient,
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    parameters: dict[str, Any],
    *,
    key: str | None = None,
) -> dict[str, Any]:
    from odoo_accounting_cli_v4 import cli
    from odoo_accounting_cli_v4.bridge.bank_reconciliation import (
        OdooBankReconciliationPort,
    )
    from odoo_accounting_cli_v4.bridge.bank_transactions import (
        OdooBankTransactionSearchPort,
    )
    from odoo_accounting_cli_v4.bridge.core_object_reads import OdooCoreObjectReadPort
    from odoo_accounting_cli_v4.bridge.core_writes import OdooCoreWritePort
    from odoo_accounting_cli_v4.bridge.financial_reports import OdooFinancialReportPort
    from odoo_accounting_cli_v4.bridge.invoices import OdooInvoicePort
    from odoo_accounting_cli_v4.bridge.journal_entries import OdooJournalEntryPort
    from odoo_accounting_cli_v4.bridge.payments import OdooPaymentPort

    request = _request(alias, run_id, capability_id, parameters)
    if key is not None:
        port = OdooCoreWritePort(client)
        argv = [
            "write",
            "run",
            capability_id,
            "--request",
            "-",
            "--idempotency-key",
            key,
            "--confirm",
            capability_id,
        ]
    else:
        ports = {
            "bank.transaction.search": OdooBankTransactionSearchPort,
            "bank.transaction.reconciliation.get": OdooBankReconciliationPort,
            "bank.transaction.match_candidates.list": OdooBankReconciliationPort,
            "invoice.get": OdooInvoicePort,
            "invoice.payment_status.inspect": OdooInvoicePort,
            "payment.get": OdooPaymentPort,
            "journal_entry.get": OdooJournalEntryPort,
            "journal_item.search": OdooCoreObjectReadPort,
            "report.trial_balance": OdooFinancialReportPort,
        }
        port = ports[capability_id](client)
        argv = ["read", capability_id, "--request", "-"]
    stdout, stderr = io.StringIO(), io.StringIO()
    client.last_runtime_failure = None
    exit_code = cli.main(
        argv,
        stdin=io.StringIO(json.dumps(request)),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda _capability, _request: port,
    )
    if exit_code != 0:
        raise AssertionError(
            f"{capability_id}: {stdout.getvalue()}{stderr.getvalue()}"
        ) from client.last_runtime_failure
    assert stderr.getvalue() == ""
    assert len(stdout.getvalue().splitlines()) == 1
    response = json.loads(stdout.getvalue())
    assert response["request_id"] == request["request_id"]
    assert response["capability"] == capability_id
    assert response["schema_version"] == "v1"
    assert response["success"] is True and response["status"] == "verified"
    assert response["error"] is None
    assert {
        field: response["odoo"][field]
        for field in ("database", "company_id", "user_id")
    } == {
        "database": alias,
        "company_id": _COMPANY_ID,
        "user_id": _USER_ID,
    }
    if key is not None:
        result = response["data"]["result"]
        assert response["odoo"]["model"] == result["model"]
        record_ids = [result["id"]] if result["id"] is not None else result["line_ids"]
        assert response["odoo"]["record_ids"] == record_ids
    client.capabilities.add(capability_id)
    return response["data"]


def _write(
    env: _RuntimeClient,
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    parameters: dict[str, Any],
    *,
    explicit_key: str | None = None,
) -> dict[str, Any]:
    key = _write_key(capability_id, parameters, explicit_key)
    first = _cli(env, alias, run_id, capability_id, parameters, key=key)
    if first["idempotent_replay"] is not False:
        raise RuntimeError(f"{capability_id} unexpectedly replayed its first write")
    second = _cli(env, alias, run_id, capability_id, parameters, key=key)
    if second["idempotent_replay"] is not True or second["result"] != first["result"]:
        raise RuntimeError(f"{capability_id} did not replay deterministically")
    return first["result"]


def _read_search(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    return _cli(env, alias, run_id, "bank.transaction.search", parameters)


def _read_reconciliation(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    transaction_id: int,
) -> dict[str, Any]:
    return _cli(
        env,
        alias,
        run_id,
        "bank.transaction.reconciliation.get",
        {"transaction_id": transaction_id},
    )


def _read_candidates(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    transaction_id: int,
    cursor: str | None = None,
) -> dict[str, Any]:
    return _cli(
        env,
        alias,
        run_id,
        "bank.transaction.match_candidates.list",
        {"transaction_id": transaction_id, "limit": 1000, "cursor": cursor},
    )


def _fixture_ids(env: Any, alias: str) -> dict[str, int]:
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
    bank_journal = _one(
        env["account.journal"].search(
            [
                ("id", "=", 14),
                ("company_id", "=", _COMPANY_ID),
                ("type", "=", "bank"),
            ]
        ),
        "bank journal",
    )

    def journal(journal_type: str) -> Any:
        return _one(
            env["account.journal"].search(
                [("company_id", "=", _COMPANY_ID), ("type", "=", journal_type)],
                order="id",
                limit=1,
            ),
            f"{journal_type} journal",
        )

    def account(account_type: str) -> Any:
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

    def method_line(payment_type: str) -> Any:
        return _one(
            env["account.payment.method.line"].search(
                [
                    ("journal_id", "=", bank_journal.id),
                    ("payment_type", "=", payment_type),
                    ("payment_method_id.code", "=", "manual"),
                ],
                order="id",
                limit=1,
            ),
            f"{payment_type} manual payment method line",
        )

    inbound_method = method_line("inbound")
    outstanding = inbound_method.payment_account_id
    if (
        not outstanding
        or not outstanding.reconcile
        or _COMPANY_ID not in outstanding.company_ids.ids
        or outstanding == bank_journal.default_account_id
        or outstanding == bank_journal.suspense_account_id
    ):
        raise RuntimeError(
            "split receipts require a reconcilable outstanding account distinct "
            "from the bank and suspense accounts"
        )
    return {
        "customer": partner_ids["customer"],
        "supplier": partner_ids["supplier"],
        "currency": company.currency_id.id,
        "bank_journal": bank_journal.id,
        "sale_journal": journal("sale").id,
        "purchase_journal": journal("purchase").id,
        "general_journal": journal("general").id,
        "income": account("income").id,
        "expense": account("expense").id,
        "current_asset": account("asset_current").id,
        "inbound_method": inbound_method.id,
        "outstanding": outstanding.id,
        "outbound_method": method_line("outbound").id,
    }


def _exercise_payment(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    ids: dict[str, int],
    today: str,
    marker: str,
) -> int:
    create_parameters = {
        "payment_type": "inbound",
        "partner_type": "customer",
        "partner_id": ids["customer"],
        "amount": "125.00",
        "currency_id": ids["currency"],
        "journal_id": ids["bank_journal"],
        "payment_method_line_id": ids["inbound_method"],
        "date": today,
        "payment_reference": f"PAY-{marker}",
    }
    result = _write(
        env,
        alias,
        run_id,
        "payment.create",
        create_parameters,
        explicit_key=f"payment-smoke-{run_id.hex}-{alias}",
    )
    payment_id = result["id"]
    _write(
        env,
        alias,
        run_id,
        "payment.update_draft",
        {
            "payment_id": payment_id,
            "changes": {
                "amount": "130.00",
                "payment_reference": f"PAY-UPD-{marker}",
            },
        },
    )
    _write(
        env,
        alias,
        run_id,
        "payment.post",
        {"payment_id": payment_id},
    )
    reset = _write(
        env,
        alias,
        run_id,
        "payment.reset_to_draft",
        {"payment_id": payment_id},
    )
    if reset["state"] != "draft":
        raise RuntimeError("payment.reset_to_draft did not return a draft payment")
    return payment_id


def _exercise_bank(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    ids: dict[str, int],
    today: str,
    marker: str,
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
            "lines": [
                {
                    "name": f"Bank match {marker}",
                    "account_id": ids["income"],
                    "quantity": "1",
                    "price_unit": "100.00",
                    "tax_ids": [],
                }
            ],
        },
        explicit_key=f"bank-match-invoice-{run_id.hex}-{alias}",
    )
    invoice_id = invoice["id"]
    _write(
        env,
        alias,
        run_id,
        "invoice.post",
        {"move_id": invoice_id},
    )
    invoice_status = _cli(
        env, alias, run_id, "invoice.payment_status.inspect", {"invoice_id": invoice_id}
    )
    receivable = _one(
        [
            line
            for line in invoice_status["receivable_payable_lines"]
            if line["account"]["account_type"] == "asset_receivable"
            and not line["reconciled"]
        ],
        "open receivable line",
    )[0]

    recorded = _write(
        env,
        alias,
        run_id,
        "bank.transaction.record",
        {
            "journal_id": ids["bank_journal"],
            "date": today,
            "amount": "100.00",
            "payment_ref": f"RAW-{marker}",
            "partner_id": ids["customer"],
        },
        explicit_key=f"bank-transaction-{run_id.hex}-{alias}",
    )
    transaction_id = recorded["id"]
    _write(
        env,
        alias,
        run_id,
        "bank.transaction.update",
        {
            "transaction_id": transaction_id,
            "changes": {"payment_ref": marker},
        },
    )

    search = _read_search(
        env,
        alias,
        run_id,
        {
            "date_from": today,
            "date_to": today,
            "journal_id": ids["bank_journal"],
            "partner_id": ids["customer"],
            "reconciled": False,
            "query": marker,
            "limit": 100,
            "cursor": None,
        },
    )
    if [item["id"] for item in search["items"]] != [transaction_id]:
        raise RuntimeError("bank.transaction.search did not isolate its fixture")

    initial = _read_reconciliation(env, alias, run_id, transaction_id)
    if initial["transaction"]["is_reconciled"] or initial["suspense_line"] is None:
        raise RuntimeError("the new bank transaction is not initially unmatched")
    candidates = _read_candidates(env, alias, run_id, transaction_id)
    candidate_ids = {item["id"] for item in candidates["items"]}
    if receivable["id"] not in candidate_ids:
        raise RuntimeError("the fixture receivable is absent from match candidates")

    matched = _write(
        env,
        alias,
        run_id,
        "bank.transaction.match",
        {"transaction_id": transaction_id, "candidate_line_ids": [receivable["id"]]},
    )
    if matched["reconciled"] is not True:
        raise RuntimeError("bank.transaction.match did not reconcile the transaction")
    matched_state = _read_reconciliation(env, alias, run_id, transaction_id)
    if not any(
        line["source_line_id"] == receivable["id"]
        for line in matched_state["matched_lines"]
    ):
        raise RuntimeError("reconciliation.get did not report the matched receivable")

    unmatched = _write(
        env,
        alias,
        run_id,
        "bank.transaction.unmatch",
        {"transaction_id": transaction_id},
    )
    if unmatched["reconciled"] is not False:
        raise RuntimeError("bank.transaction.unmatch left the transaction reconciled")
    unmatched_state = _read_reconciliation(env, alias, run_id, transaction_id)
    suspense = unmatched_state["suspense_line"]
    if suspense is None or suspense["amount_residual"] == "0":
        raise RuntimeError("unmatch did not restore one non-zero suspense line")

    label = f"Write off {marker}"
    written_off = _write(
        env,
        alias,
        run_id,
        "reconciliation.write_off",
        {
            "transaction_id": transaction_id,
            "write_off_account_id": ids["expense"],
            "label": label,
            "expected_residual_amount": suspense["amount_residual"],
        },
    )
    if written_off["reconciled"] is not True:
        raise RuntimeError("reconciliation.write_off did not close the residual")
    final_state = _read_reconciliation(env, alias, run_id, transaction_id)
    if not any(
        line["account_id"] == ids["expense"] and line["name"] == label
        for line in final_state["writeoff_lines"]
    ):
        raise RuntimeError("reconciliation.get did not report the write-off line")
    return invoice_id, transaction_id


def _create_posted_invoice(
    client: _RuntimeClient,
    alias: str,
    run_id: uuid.UUID,
    ids: dict[str, int],
    today: str,
    marker: str,
    amount: str,
    *,
    supplier: bool = False,
) -> int:
    capability = "vendor_bill.create" if supplier else "customer_invoice.create"
    invoice = _write(
        client,
        alias,
        run_id,
        capability,
        {
            "partner_id": ids["supplier" if supplier else "customer"],
            "journal_id": ids["purchase_journal" if supplier else "sale_journal"],
            "invoice_date": today,
            "currency_id": ids["currency"],
            "lines": [
                {
                    "name": marker,
                    "account_id": ids["expense" if supplier else "income"],
                    "quantity": "1",
                    "price_unit": amount,
                    "tax_ids": [],
                }
            ],
        },
        explicit_key=f"{capability}:{alias}:{run_id.hex}:business-chain",
    )
    _write(client, alias, run_id, "invoice.post", {"move_id": invoice["id"]})
    state = _cli(
        client,
        alias,
        run_id,
        "invoice.payment_status.inspect",
        {"invoice_id": invoice["id"]},
    )
    assert state["state"] == "posted"
    assert state["move_type"] == ("in_invoice" if supplier else "out_invoice")
    assert Decimal(state["amount_total"]) == Decimal(amount)
    assert Decimal(state["amount_residual"]) == Decimal(amount)
    return invoice["id"]


def _exercise_split_receipts(
    client: _RuntimeClient,
    alias: str,
    run_id: uuid.UUID,
    ids: dict[str, int],
    today: str,
    marker: str,
) -> None:
    invoice_id = _create_posted_invoice(
        client, alias, run_id, ids, today, marker, "100"
    )
    payments = []
    for amount, residual in (("40", "60"), ("60", "0")):
        result = _write(
            client,
            alias,
            run_id,
            "receivable.payment.register",
            {
                "move_id": invoice_id,
                "journal_id": ids["bank_journal"],
                "payment_date": today,
                "amount": amount,
            },
            explicit_key=f"split-receipt:{alias}:{run_id.hex}:{amount}",
        )
        assert result["source_id"] == invoice_id
        state = _cli(
            client,
            alias,
            run_id,
            "invoice.payment_status.inspect",
            {"invoice_id": invoice_id},
        )
        assert Decimal(state["amount_residual"]) == Decimal(residual)
        assert sum(
            Decimal(item["company_amount"])
            for item in state["reconciliations"]
            if item["payment_id"] == result["id"]
        ) == Decimal(amount)
        if residual == "60":
            assert state["payment_state"] == "partial"
        else:
            assert state["payment_state"] in {"in_payment", "paid"}
            assert all(line["reconciled"] for line in state["receivable_payable_lines"])
        payment = _cli(
            client, alias, run_id, "payment.get", {"payment_id": result["id"]}
        )
        assert Decimal(payment["amount"]) == Decimal(amount)
        assert (payment["payment_type"], payment["partner_type"]) == (
            "inbound",
            "customer",
        )
        assert payment["payment_method_line"]["id"] == ids["inbound_method"]
        assert payment["move_id"] == payment["journal_entry"]["id"]
        assert invoice_id in {item["id"] for item in payment["reconciled_invoices"]}
        payments.append(payment)
    assert len({payment["id"] for payment in payments}) == 2
    assert {payment["id"] for payment in payments} <= {
        item["id"] for item in state["payments"]
    }
    transaction = _write(
        client,
        alias,
        run_id,
        "bank.transaction.record",
        {
            "journal_id": ids["bank_journal"],
            "date": today,
            "amount": "100",
            "payment_ref": marker,
            "partner_id": ids["customer"],
        },
        explicit_key=f"split-bank:{alias}:{run_id.hex}",
    )
    move_ids = {payment["move_id"] for payment in payments}
    candidates, cursor = [], None
    while True:
        page = _read_candidates(client, alias, run_id, transaction["id"], cursor)
        candidates.extend(
            item
            for item in page["items"]
            if item["move"]["id"] in move_ids
            and item["account"]["id"] == ids["outstanding"]
        )
        if not page["has_more"]:
            break
        assert page["next_cursor"] is not None and page["next_cursor"] != cursor
        cursor = page["next_cursor"]
    assert (
        len(candidates) == 2 and {item["move"]["id"] for item in candidates} == move_ids
    )
    assert sorted(Decimal(item["amount_residual"]) for item in candidates) == [
        Decimal(40),
        Decimal(60),
    ]
    line_ids = sorted(item["id"] for item in candidates)
    _write(
        client,
        alias,
        run_id,
        "bank.transaction.match",
        {"transaction_id": transaction["id"], "candidate_line_ids": line_ids},
    )
    bank = _read_reconciliation(client, alias, run_id, transaction["id"])
    assert bank["transaction"]["is_reconciled"] is True
    assert Decimal(bank["transaction"]["amount_residual"]) == 0
    assert bank["suspense_line"] is None
    assert {line["source_line_id"] for line in bank["matched_lines"]} == set(line_ids)
    assert all(
        Decimal(line["source_amount_residual"]) == 0 for line in bank["matched_lines"]
    )
    assert all(
        Decimal(line["source_amount_residual_currency"]) == 0
        for line in bank["matched_lines"]
    )
    assert (
        Decimal(bank["liquidity_line"]["balance"])
        + sum(Decimal(line["applied_balance"]) for line in bank["matched_lines"])
        == 0
    )
    for payment in payments:
        paid = _cli(client, alias, run_id, "payment.get", {"payment_id": payment["id"]})
        assert paid["is_matched"] is True and paid["state"] == "paid"
    final = _cli(
        client,
        alias,
        run_id,
        "invoice.payment_status.inspect",
        {"invoice_id": invoice_id},
    )
    assert Decimal(final["amount_residual"]) == 0 and final["payment_state"] == "paid"
    entry = _cli(
        client,
        alias,
        run_id,
        "journal_entry.get",
        {"entry_id": bank["transaction"]["move_id"]},
    )
    assert entry["state"] == "posted"
    assert (
        Decimal(entry["totals"]["debit"]) == Decimal(entry["totals"]["credit"]) == 100
    )
    assert Decimal(entry["totals"]["balance"]) == 0


def _exercise_supplier_payment(
    client: _RuntimeClient,
    alias: str,
    run_id: uuid.UUID,
    ids: dict[str, int],
    today: str,
    marker: str,
) -> None:
    bill_id = _create_posted_invoice(
        client, alias, run_id, ids, today, marker, "80", supplier=True
    )
    result = _write(
        client,
        alias,
        run_id,
        "payable.payment.register",
        {
            "move_id": bill_id,
            "journal_id": ids["bank_journal"],
            "payment_date": today,
            "amount": "80",
        },
        explicit_key=f"supplier-payment:{alias}:{run_id.hex}",
    )
    assert result["source_id"] == bill_id
    payment = _cli(client, alias, run_id, "payment.get", {"payment_id": result["id"]})
    assert (payment["payment_type"], payment["partner_type"]) == (
        "outbound",
        "supplier",
    )
    assert Decimal(payment["amount"]) == 80
    assert bill_id in {item["id"] for item in payment["reconciled_bills"]}
    state = _cli(
        client, alias, run_id, "invoice.payment_status.inspect", {"invoice_id": bill_id}
    )
    assert Decimal(state["amount_residual"]) == 0
    assert state["payment_state"] in {"in_payment", "paid"}
    assert all(line["reconciled"] for line in state["receivable_payable_lines"])


def _exercise_adjustment_reversal(
    client: _RuntimeClient,
    alias: str,
    run_id: uuid.UUID,
    ids: dict[str, int],
    today: str,
    marker: str,
) -> None:
    entry = _write(
        client,
        alias,
        run_id,
        "journal_entry.create",
        {
            "journal_id": ids["general_journal"],
            "date": today,
            "reference": marker,
            "lines": [
                {
                    "name": marker + " debit",
                    "account_id": ids["expense"],
                    "partner_id": None,
                    "debit": "25",
                    "credit": "0",
                },
                {
                    "name": marker + " credit",
                    "account_id": ids["current_asset"],
                    "partner_id": None,
                    "debit": "0",
                    "credit": "25",
                },
            ],
        },
        explicit_key=f"adjustment:{alias}:{run_id.hex}",
    )
    _write(client, alias, run_id, "journal_entry.post", {"move_id": entry["id"]})
    reversal = _write(
        client,
        alias,
        run_id,
        "journal_entry.reverse",
        {"move_id": entry["id"], "date": today, "reason": marker},
    )
    assert reversal["source_id"] == entry["id"] and reversal["id"] != entry["id"]
    if reversal["state"] == "draft":
        _write(client, alias, run_id, "journal_entry.post", {"move_id": reversal["id"]})
    balances: dict[int, Decimal] = {}
    for entry_id in (entry["id"], reversal["id"]):
        posted = _cli(
            client, alias, run_id, "journal_entry.get", {"entry_id": entry_id}
        )
        assert posted["state"] == "posted"
        assert (
            Decimal(posted["totals"]["debit"])
            == Decimal(posted["totals"]["credit"])
            == 25
        )
        assert Decimal(posted["totals"]["balance"]) == 0
        for line in posted["lines"]:
            account_id = line["account"]["id"]
            balances[account_id] = balances.get(account_id, Decimal(0)) + Decimal(
                line["balance"]
            )
    assert set(balances) == {ids["expense"], ids["current_asset"]}
    assert all(balance == 0 for balance in balances.values())


def _trial_balance_totals(
    client: _RuntimeClient, alias: str, run_id: uuid.UUID, today: str
) -> list[Decimal]:
    data = _cli(
        client,
        alias,
        run_id,
        "report.trial_balance",
        {"date_from": today, "date_to": today, "limit": 1000, "cursor": None},
    )
    assert [column["expression_label"] for column in data["columns"]] == [
        "balance",
        "debit",
        "credit",
        "balance",
    ]
    assert data["has_more"] is False and data["next_cursor"] is None
    totals = [line for line in data["lines"] if line["parent_id"] is None]
    assert len(totals) == 1 and all(value is not None for value in totals[0]["values"])
    values = [Decimal(value) for value in totals[0]["values"]]
    assert values[0] == values[3] == 0
    assert values[1] == values[2]
    return values


def _collect_related(env: Any, tracked: dict[str, set[int]]) -> None:
    """Read-only rollback audit; never supplies records to a business command."""
    records = {
        model: env[model].browse(sorted(ids)).exists() for model, ids in tracked.items()
    }
    records["account.payment"] |= records["account.bank.statement.line"].payment_ids
    records["account.move"] |= (
        records["account.payment"].move_id
        | records["account.bank.statement.line"].move_id
    )
    lines = records["account.move.line"] | records["account.move"].line_ids
    partials = (
        records["account.partial.reconcile"]
        | lines.matched_debit_ids
        | lines.matched_credit_ids
    )
    fulls = (
        records["account.full.reconcile"]
        | lines.full_reconcile_id
        | partials.full_reconcile_id
    )
    partials |= fulls.partial_reconcile_ids
    lines |= (
        fulls.reconciled_line_ids | partials.debit_move_id | partials.credit_move_id
    )
    records["account.move"] |= lines.move_id | partials.exchange_move_id
    records["account.move.line"] = lines | records["account.move"].line_ids
    records["account.partial.reconcile"] = partials
    records["account.full.reconcile"] = fulls
    for model, found in records.items():
        tracked[model].update(found.ids)


def _collect_marked(env: Any, tracked: dict[str, set[int]], marker: str) -> None:
    """Find this run's roots even if a failed CLI returned no new record ID."""
    domains = {
        "account.payment": [
            "|",
            ("memo", "ilike", marker),
            ("payment_reference", "ilike", marker),
        ],
        "account.bank.statement.line": [("payment_ref", "ilike", marker)],
        "account.move": [
            "|",
            ("ref", "ilike", marker),
            ("line_ids.name", "ilike", marker),
        ],
        "account.move.line": [("name", "ilike", marker)],
    }
    for model, domain in domains.items():
        tracked[model].update(
            env[model].with_context(active_test=False).search(domain).ids
        )
    _collect_related(env, tracked)


def _verify_rollback(
    registry: Any,
    *,
    tracked: dict[str, set[int]],
    marker: str,
) -> None:
    from odoo import SUPERUSER_ID, api

    cursor = registry.cursor()
    try:
        env = api.Environment(
            cursor,
            SUPERUSER_ID,
            {"allowed_company_ids": [_COMPANY_ID], "active_test": False},
        )
        leaked = {model: set(record_ids) for model, record_ids in tracked.items()}
        _collect_marked(env, leaked, marker)
        remaining = {
            model: env[model].search_count([("id", "in", sorted(record_ids))])
            for model, record_ids in leaked.items()
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
    marker = f"ODACV4-PAY-BANK-{args.alias}-{args.run_id.hex}"
    tracked: dict[str, set[int]] = {model: set() for model in _BUSINESS_MODELS}
    scenarios: list[str] = []
    env = client = None
    failure: BaseException | None = None
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
        client = _RuntimeClient(env)
        client.tracked = tracked
        user = env.user
        if (
            env.uid != _USER_ID
            or user.id != _USER_ID
            or not user.active
            or user.login != _USER_LOGIN
            or _COMPANY_ID not in user.company_ids.ids
        ):
            raise RuntimeError("the fixed business user is unavailable")
        ids = _fixture_ids(env, args.alias)
        today = fields.Date.to_string(fields.Date.context_today(env.user))
        _exercise_payment(client, args.alias, args.run_id, ids, today, marker)
        scenarios.append("payment_lifecycle")
        _exercise_bank(client, args.alias, args.run_id, ids, today, marker)
        scenarios.append("bank_match_unmatch_writeoff")
        before = _trial_balance_totals(client, args.alias, args.run_id, today)
        _exercise_split_receipts(
            client, args.alias, args.run_id, ids, today, marker + "-SPLIT"
        )
        scenarios.append("customer_split_payment_bank_match")
        _exercise_supplier_payment(
            client, args.alias, args.run_id, ids, today, marker + "-SUPPLIER"
        )
        scenarios.append("supplier_bill_payment")
        _exercise_adjustment_reversal(
            client, args.alias, args.run_id, ids, today, marker + "-ADJUST"
        )
        scenarios.append("adjustment_reversal")
        after = _trial_balance_totals(client, args.alias, args.run_id, today)
        delta = [new - old for old, new in zip(before, after, strict=True)]
        # Eight posted moves: invoice, two receipts, bank deposit, bill, payment,
        # adjustment and reversal. These are period movements, not net balances.
        expected_movement = Decimal(100 + 40 + 60 + 100 + 80 + 80 + 25 + 25)
        assert delta == [Decimal(0), expected_movement, expected_movement, Decimal(0)]
        scenarios.append("trial_balance_movement")
        assert client.capabilities == set(_CAPABILITIES)
        assert all(tracked.values()), "rollback tracking omitted a business model"
    except BaseException as exc:  # noqa: BLE001 - re-raised after rollback verification
        failure = exc
    finally:
        try:
            if env is not None:
                _collect_marked(env, tracked, args.run_id.hex)
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
        _verify_rollback(
            registry,
            tracked=tracked,
            marker=args.run_id.hex,
        )
    except Exception as exc:
        raise exc from failure
    if failure is not None:
        raise failure
    assert client is not None and scenarios == list(_SCENARIOS)
    sys.stdout.write(
        json.dumps(
            {
                "alias": args.alias,
                "capabilities": sorted(client.capabilities),
                "company_id": _COMPANY_ID,
                "database": args.database,
                "execution": "in_process_cli_real_orm",
                "rollback_verified": True,
                "scenarios": scenarios,
                "trial_balance_period_delta": {
                    "debit": format(delta[1].normalize(), "f"),
                    "credit": format(delta[2].normalize(), "f"),
                },
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
