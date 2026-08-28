"""Transactional dual-database smoke for the payment/bank capability batch.

The worker runs as the configured accountant, creates its own accounting fixtures,
exercises all ten new capabilities, and rolls the transaction back.  It never
commits fixture or accounting data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import uuid
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
        "capabilities": list(_CAPABILITIES),
        "company_id": _COMPANY_ID,
        "database": _DATABASES[alias],
        "rollback_verified": True,
        "user_id": _USER_ID,
    }


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
        "request_id": str(uuid.uuid5(run_id, f"payment-bank:{capability_id}")),
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

        return dispatch(self.env, payload, payload["company_id"], RuntimeFailure)


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

    request = _request(alias, run_id, capability_id, parameters)
    key = _write_key(capability_id, parameters, explicit_key)
    port = _CoreWritePort(env)
    first = execute_core_write(port, capability_id, request, key, capability_id)
    if first["idempotent_replay"] is not False:
        raise RuntimeError(f"{capability_id} unexpectedly replayed its first write")
    if not twice:
        return first["result"]
    second = execute_core_write(port, capability_id, request, key, capability_id)
    if second["idempotent_replay"] is not True or second["result"] != first["result"]:
        raise RuntimeError(f"{capability_id} did not replay deterministically")
    return first["result"]


class _BankSearchPort:
    def __init__(self, env: Any) -> None:
        self.env = env

    @property
    def user_id(self) -> int:
        return self.env.uid

    def search_page(self, **payload: Any) -> dict[str, Any]:
        from odoo_accounting_cli_v4.bridge.runtime import (
            _dispatch_bank_transaction_search,
        )

        return _dispatch_bank_transaction_search(
            self.env,
            payload,
            payload["company_id"],
        )


class _BankReconciliationPort:
    def __init__(self, env: Any) -> None:
        self.env = env

    @property
    def user_id(self) -> int:
        return self.env.uid

    def get(self, *, company_id: int, transaction_id: int) -> dict[str, Any]:
        from odoo_accounting_cli_v4.bridge.bank_reconciliation_runtime import (
            GET_ACTION,
            dispatch,
        )
        from odoo_accounting_cli_v4.bridge.runtime import RuntimeFailure

        return dispatch(
            self.env,
            GET_ACTION,
            {"company_id": company_id, "transaction_id": transaction_id},
            company_id,
            failure_type=RuntimeFailure,
        )

    def read_candidates_page(
        self,
        *,
        company_id: int,
        transaction_id: int,
        after: list[Any] | None,
        limit: int,
    ) -> dict[str, Any]:
        from odoo_accounting_cli_v4.bridge.bank_reconciliation_runtime import (
            CANDIDATE_ACTION,
            dispatch,
        )
        from odoo_accounting_cli_v4.bridge.runtime import RuntimeFailure

        return dispatch(
            self.env,
            CANDIDATE_ACTION,
            {
                "company_id": company_id,
                "transaction_id": transaction_id,
                "after": after,
                "limit": limit,
            },
            company_id,
            failure_type=RuntimeFailure,
        )


def _read_search(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    from odoo_accounting_cli_v4.capabilities.bank_transactions import (
        search_bank_transactions,
    )

    return search_bank_transactions(
        _BankSearchPort(env),
        _request(alias, run_id, "bank.transaction.search", parameters),
    )


def _read_reconciliation(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    transaction_id: int,
) -> dict[str, Any]:
    from odoo_accounting_cli_v4.capabilities.bank_reconciliation import (
        get_bank_transaction_reconciliation,
    )

    return get_bank_transaction_reconciliation(
        _BankReconciliationPort(env),
        _request(
            alias,
            run_id,
            "bank.transaction.reconciliation.get",
            {"transaction_id": transaction_id},
        ),
    )


def _read_candidates(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    transaction_id: int,
) -> dict[str, Any]:
    from odoo_accounting_cli_v4.capabilities.bank_reconciliation import (
        list_bank_match_candidates,
    )

    return list_bank_match_candidates(
        _BankReconciliationPort(env),
        _request(
            alias,
            run_id,
            "bank.transaction.match_candidates.list",
            {"transaction_id": transaction_id, "limit": 1000, "cursor": None},
        ),
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
    sale_journal = _one(
        env["account.journal"].search(
            [("company_id", "=", _COMPANY_ID), ("type", "=", "sale")],
            order="id",
            limit=1,
        ),
        "sale journal",
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

    return {
        "customer": partner_ids["customer"],
        "supplier": partner_ids["supplier"],
        "currency": company.currency_id.id,
        "bank_journal": bank_journal.id,
        "sale_journal": sale_journal.id,
        "income": account("income").id,
        "expense": account("expense").id,
        "inbound_method": method_line("inbound").id,
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
        twice=False,
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
        twice=False,
    )
    invoice_move = env["account.move"].browse(invoice_id)
    receivable = _one(
        invoice_move.line_ids.filtered(
            lambda line: (
                line.account_id.account_type == "asset_receivable"
                and not line.reconciled
            )
        ),
        "open receivable line",
    )

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
    if receivable.id not in candidate_ids:
        raise RuntimeError("the fixture receivable is absent from match candidates")

    matched = _write(
        env,
        alias,
        run_id,
        "bank.transaction.match",
        {"transaction_id": transaction_id, "candidate_line_ids": [receivable.id]},
    )
    if matched["reconciled"] is not True:
        raise RuntimeError("bank.transaction.match did not reconcile the transaction")
    matched_state = _read_reconciliation(env, alias, run_id, transaction_id)
    if not any(
        line["source_line_id"] == receivable.id
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


def _verify_rollback(
    registry: Any,
    *,
    payment_id: int,
    invoice_id: int,
    transaction_id: int,
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
        remaining = {
            "payment_id": env["account.payment"].search_count(
                [("id", "=", payment_id)], limit=1
            ),
            "invoice_id": env["account.move"].search_count(
                [("id", "=", invoice_id)], limit=1
            ),
            "transaction_id": env["account.bank.statement.line"].search_count(
                [("id", "=", transaction_id)], limit=1
            ),
            "marker_payment": env["account.payment"].search_count(
                [("payment_reference", "ilike", marker)], limit=1
            ),
            "marker_bank": env["account.bank.statement.line"].search_count(
                [("payment_ref", "=", marker)], limit=1
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
    marker = f"ODACV4-PAY-BANK-{args.alias}-{args.run_id.hex}"
    payment_id: int | None = None
    invoice_id: int | None = None
    transaction_id: int | None = None
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
        ids = _fixture_ids(env, args.alias)
        today = fields.Date.to_string(fields.Date.context_today(env.user))
        payment_id = _exercise_payment(env, args.alias, args.run_id, ids, today, marker)
        invoice_id, transaction_id = _exercise_bank(
            env, args.alias, args.run_id, ids, today, marker
        )
    except Exception as exc:
        failure = exc
    finally:
        cursor.rollback()
        cursor.close()

    if payment_id is not None and invoice_id is not None and transaction_id is not None:
        _verify_rollback(
            registry,
            payment_id=payment_id,
            invoice_id=invoice_id,
            transaction_id=transaction_id,
            marker=marker,
        )
    if failure is not None:
        raise failure
    if payment_id is None or invoice_id is None or transaction_id is None:
        raise RuntimeError("the live fixtures were not initialized")
    sys.stdout.write(
        json.dumps(
            {
                "alias": args.alias,
                "capabilities": list(_CAPABILITIES),
                "company_id": _COMPANY_ID,
                "database": args.database,
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
