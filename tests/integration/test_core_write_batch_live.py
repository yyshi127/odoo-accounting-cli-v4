"""Explicit, isolated live smoke for the implemented core accounting writes."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

import pytest

from odoo_accounting_cli_v4.registry import load_registry

_CONFIG_ENV = "ODOO_ACCOUNTING_CLI_V4_CONFIG"
_ALLOW_ENV = "ODACV4_ALLOW_WRITE_SMOKE"
_ALIASES = ("v4-dev", "v4-e2e")
_PHYSICAL_DATABASES = {
    "v4-dev": "odoo_cli_v4_dev",
    "v4-e2e": "odoo_cli_v4_e2e",
}
_CUSTOMER = {"v4-dev": 16, "v4-e2e": 8}
_SUPPLIER = {"v4-dev": 17, "v4-e2e": 9}
_COMPANY_ID = 1
_USER_LOGIN = "odacv4_g5_accountant"
_DATE = "2026-08-24"
_SALE_JOURNAL_ID = 9
_PURCHASE_JOURNAL_ID = 10
_GENERAL_JOURNAL_ID = 11
_BANK_JOURNAL_ID = 14
_CURRENCY_ID = 6
_RECEIVABLE_ACCOUNT_ID = 55
_INCOME_ACCOUNT_ID = 130
_EXPENSE_ACCOUNT_ID = 125
_CURRENT_ASSET_ACCOUNT_ID = 152
_RESULT_KEYS = {
    "model",
    "id",
    "name",
    "state",
    "company_id",
    "move_type",
    "source_id",
    "line_ids",
    "partial_reconcile_ids",
    "full_reconcile_id",
    "reconciled",
}


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _enabled_runtime_config() -> Path:
    if os.environ.get(_ALLOW_ENV) != "1":
        pytest.skip(f"set {_ALLOW_ENV}=1 to authorize isolated write smoke")
    raw_path = os.environ.get(_CONFIG_ENV)
    if not raw_path:
        pytest.skip(f"{_CONFIG_ENV} is not configured")
    path = Path(raw_path)
    if not path.is_file():
        pytest.skip(f"{_CONFIG_ENV} does not name an existing file")
    return path


def _assert_runtime_aliases(config_path: Path) -> dict[str, Any]:
    document = json.loads(config_path.read_text(encoding="utf-8"))
    aliases = document.get("aliases")
    assert isinstance(aliases, dict)
    assert set(aliases) == set(_ALIASES)
    assert {
        alias: value.get("database") for alias, value in aliases.items()
    } == _PHYSICAL_DATABASES
    assert all(
        aliases[alias].get("companies", {}).get(str(_COMPANY_ID)) == [_USER_LOGIN]
        for alias in _ALIASES
    )
    return document


def _create_draft_payment(
    alias: str,
    run_id: str,
    config_path: Path,
    runtime_document: dict[str, Any],
) -> int:
    bridge = runtime_document.get("bridge")
    assert isinstance(bridge, dict) and set(bridge) == {"argv", "timeout_seconds"}
    bridge_argv = bridge["argv"]
    assert isinstance(bridge_argv, list) and len(bridge_argv) == 8
    assert bridge_argv[2::2] == [
        "--runtime-config",
        "--odoo-config",
        "--odoo-source",
    ]

    root = _project_root()
    executable = Path(bridge_argv[0])
    bridge_script = Path(bridge_argv[1])
    configured_runtime = Path(bridge_argv[3])
    odoo_config = Path(bridge_argv[5])
    odoo_source = Path(bridge_argv[7])
    helper = root / "tests" / "integration" / "core_write_draft_payment_fixture.py"
    assert executable.is_absolute() and executable.is_file()
    assert bridge_script.resolve(strict=True) == (
        root / "scripts" / "odoo_bridge.py"
    ).resolve(strict=True)
    assert configured_runtime.resolve(strict=True) == config_path.resolve(strict=True)
    assert odoo_config.is_absolute() and odoo_config.is_file()
    assert odoo_source.is_absolute() and odoo_source.is_dir()
    assert helper.is_file()
    timeout = bridge["timeout_seconds"]
    assert isinstance(timeout, int) and not isinstance(timeout, bool) and timeout > 0

    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [
            str(executable),
            str(helper),
            "--odoo-config",
            str(odoo_config),
            "--odoo-source",
            str(odoo_source),
            "--alias",
            alias,
            "--database",
            _PHYSICAL_DATABASES[alias],
            "--run-id",
            run_id,
        ],
        cwd=root,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert len(completed.stdout.splitlines()) == 1
    result = json.loads(completed.stdout)
    assert result == {
        "database": _PHYSICAL_DATABASES[alias],
        "company_id": _COMPANY_ID,
        "user_id": 5,
        "payment_id": result["payment_id"],
        "state": "draft",
        "marker": f"ODACV4-{run_id}-{alias}-draft-payment",
    }
    assert isinstance(result["payment_id"], int) and result["payment_id"] > 0
    return result["payment_id"]


def _request(alias: str, parameters: dict[str, Any], token: str) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "request_id": str(uuid.uuid5(uuid.NAMESPACE_URL, token)),
        "context": {
            "database": alias,
            "company_id": _COMPANY_ID,
            "user_login": _USER_LOGIN,
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": parameters,
    }


def _invoke(
    capability_id: str,
    request: dict[str, Any],
    command: list[str],
) -> dict[str, Any]:
    root = _project_root()
    registry = load_registry()
    registry.validate_instance(
        f"schemas/v1/{capability_id}.request.schema.json", request
    )
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = os.pathsep.join(
        part for part in (str(root / "src"), environment.get("PYTHONPATH")) if part
    )
    completed = subprocess.run(
        [sys.executable, "-m", "odoo_accounting_cli_v4", *command],
        cwd=root,
        env=environment,
        input=json.dumps(request, sort_keys=True, separators=(",", ":")),
        text=True,
        capture_output=True,
        check=False,
        timeout=300,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert completed.stderr == ""
    assert len(completed.stdout.splitlines()) == 1
    document = json.loads(completed.stdout)
    registry.validate_instance(
        f"schemas/v1/{capability_id}.response.schema.json", document
    )
    assert document["schema_version"] == "v1"
    assert document["request_id"] == request["request_id"]
    assert document["capability"] == capability_id
    assert document["success"] is True
    assert document["status"] == "verified"
    assert document["error"] is None
    assert document["odoo"]["database"] == request["context"]["database"]
    assert document["odoo"]["company_id"] == _COMPANY_ID
    assert document["odoo"]["user_id"] == 5
    return document


def _read(
    alias: str,
    capability_id: str,
    parameters: dict[str, Any],
    *,
    run_id: str,
    case: str,
) -> dict[str, Any]:
    request = _request(
        alias,
        parameters,
        f"odacv4:core-write-smoke:{run_id}:{alias}:read:{capability_id}:{case}",
    )
    return _invoke(
        capability_id,
        request,
        ["read", capability_id, "--request", "-"],
    )


def _write_twice(
    alias: str,
    capability_id: str,
    parameters: dict[str, Any],
    *,
    idempotency_key: str,
    run_id: str,
    expected_model: str | None = None,
    expected_state: str | tuple[str, ...] | None = None,
    expected_move_type: str | None = None,
    expected_source_id: int | None = None,
    expect_positive_source_id: bool = False,
) -> dict[str, Any]:
    request = _request(
        alias,
        parameters,
        f"odacv4:core-write-smoke:{run_id}:{alias}:write:{capability_id}:{idempotency_key}",
    )
    command = [
        "write",
        "run",
        capability_id,
        "--request",
        "-",
        "--idempotency-key",
        idempotency_key,
        "--confirm",
        capability_id,
    ]
    first = _invoke(capability_id, request, command)
    second = _invoke(capability_id, request, command)

    assert first["data"]["idempotent_replay"] is False
    assert second["data"]["idempotent_replay"] is True
    assert first["data"]["result"] == second["data"]["result"]
    assert first["odoo"] == second["odoo"]
    assert first["audit"]["idempotency_key"] == idempotency_key
    assert second["audit"]["idempotency_key"] == idempotency_key
    assert first["audit"]["operation_id"] == second["audit"]["operation_id"]

    result = first["data"]["result"]
    assert set(result) == _RESULT_KEYS
    assert result["company_id"] == _COMPANY_ID
    assert result["line_ids"] == sorted(set(result["line_ids"]))
    assert result["partial_reconcile_ids"] == sorted(
        set(result["partial_reconcile_ids"])
    )
    if expect_positive_source_id:
        assert isinstance(result["source_id"], int) and result["source_id"] > 0
    else:
        assert result["source_id"] == expected_source_id
    if expected_model is not None:
        assert result["model"] == expected_model
    if isinstance(expected_state, str):
        assert result["state"] == expected_state
    elif expected_state is not None:
        assert result["state"] in expected_state
    if expected_move_type is not None:
        assert result["move_type"] == expected_move_type

    expected_record_ids = result["line_ids"] if result["id"] is None else [result["id"]]
    assert first["odoo"]["model"] == result["model"]
    assert first["odoo"]["record_ids"] == expected_record_ids
    return result


def _account_line_id(lines: list[dict[str, Any]], account_id: int) -> int:
    matches = [line["id"] for line in lines if line["account"]["id"] == account_id]
    assert len(matches) == 1
    return matches[0]


def _invoice_parameters(
    partner_id: int,
    journal_id: int,
    account_id: int,
    amount: str,
    marker: str,
) -> dict[str, Any]:
    return {
        "partner_id": partner_id,
        "journal_id": journal_id,
        "invoice_date": _DATE,
        "currency_id": _CURRENCY_ID,
        "lines": [
            {
                "name": marker,
                "account_id": account_id,
                "quantity": "1",
                "price_unit": amount,
                "tax_ids": [],
            }
        ],
    }


def _run_alias_chain(
    alias: str,
    run_id: str,
    config_path: Path,
    runtime_document: dict[str, Any],
) -> None:
    customer_id = _CUSTOMER[alias]
    supplier_id = _SUPPLIER[alias]
    marker = f"ODACV4-{run_id}-{alias}"

    invoices = []
    for number, amount in ((1, "25"), (2, "30")):
        invoices.append(
            _write_twice(
                alias,
                "customer_invoice.create",
                _invoice_parameters(
                    customer_id,
                    _SALE_JOURNAL_ID,
                    _INCOME_ACCOUNT_ID,
                    amount,
                    f"{marker}-invoice-{number}",
                ),
                idempotency_key=f"core-write:{run_id}:{alias}:invoice:{number}",
                run_id=run_id,
                expected_model="account.move",
                expected_state="draft",
                expected_move_type="out_invoice",
            )
        )

    bill = _write_twice(
        alias,
        "vendor_bill.create",
        _invoice_parameters(
            supplier_id,
            _PURCHASE_JOURNAL_ID,
            _EXPENSE_ACCOUNT_ID,
            "20",
            f"{marker}-bill",
        ),
        idempotency_key=f"core-write:{run_id}:{alias}:bill",
        run_id=run_id,
        expected_model="account.move",
        expected_state="draft",
        expected_move_type="in_invoice",
    )
    refund_invoice = _write_twice(
        alias,
        "customer_invoice.create",
        _invoice_parameters(
            customer_id,
            _SALE_JOURNAL_ID,
            _INCOME_ACCOUNT_ID,
            "12",
            f"{marker}-credit-note-source",
        ),
        idempotency_key=f"core-write:{run_id}:{alias}:credit-note-source",
        run_id=run_id,
        expected_model="account.move",
        expected_state="draft",
        expected_move_type="out_invoice",
    )
    refund_bill = _write_twice(
        alias,
        "vendor_bill.create",
        _invoice_parameters(
            supplier_id,
            _PURCHASE_JOURNAL_ID,
            _EXPENSE_ACCOUNT_ID,
            "9",
            f"{marker}-vendor-refund-source",
        ),
        idempotency_key=f"core-write:{run_id}:{alias}:vendor-refund-source",
        run_id=run_id,
        expected_model="account.move",
        expected_state="draft",
        expected_move_type="in_invoice",
    )

    first_entry = _write_twice(
        alias,
        "journal_entry.create",
        {
            "journal_id": _GENERAL_JOURNAL_ID,
            "date": _DATE,
            "lines": [
                {
                    "name": f"{marker}-reconcile-bank",
                    "account_id": _CURRENT_ASSET_ACCOUNT_ID,
                    "partner_id": None,
                    "debit": "30",
                    "credit": "0",
                },
                {
                    "name": f"{marker}-reconcile-receivable",
                    "account_id": _RECEIVABLE_ACCOUNT_ID,
                    "partner_id": customer_id,
                    "debit": "0",
                    "credit": "30",
                },
            ],
        },
        idempotency_key=f"core-write:{run_id}:{alias}:entry:1",
        run_id=run_id,
        expected_model="account.move",
        expected_state="draft",
        expected_move_type="entry",
    )
    second_entry = _write_twice(
        alias,
        "journal_entry.create",
        {
            "journal_id": _GENERAL_JOURNAL_ID,
            "date": _DATE,
            "lines": [
                {
                    "name": f"{marker}-reverse-expense",
                    "account_id": _EXPENSE_ACCOUNT_ID,
                    "partner_id": None,
                    "debit": "7",
                    "credit": "0",
                },
                {
                    "name": f"{marker}-reverse-bank",
                    "account_id": _CURRENT_ASSET_ACCOUNT_ID,
                    "partner_id": None,
                    "debit": "0",
                    "credit": "7",
                },
            ],
        },
        idempotency_key=f"core-write:{run_id}:{alias}:entry:2",
        run_id=run_id,
        expected_model="account.move",
        expected_state="draft",
        expected_move_type="entry",
    )

    for move in (*invoices, bill, refund_invoice, refund_bill):
        _write_twice(
            alias,
            "invoice.post",
            {"move_id": move["id"]},
            idempotency_key=f"invoice.post:{move['id']}",
            run_id=run_id,
            expected_model="account.move",
            expected_state="posted",
            expected_move_type=move["move_type"],
        )

    _write_twice(
        alias,
        "customer_credit_note.create",
        {
            "move_id": refund_invoice["id"],
            "date": _DATE,
            "reason": f"{marker}-credit-note",
        },
        idempotency_key=f"customer_credit_note.create:{refund_invoice['id']}",
        run_id=run_id,
        expected_model="account.move",
        expected_state="draft",
        expected_move_type="out_refund",
        expected_source_id=refund_invoice["id"],
    )
    _write_twice(
        alias,
        "vendor_refund.create",
        {
            "move_id": refund_bill["id"],
            "date": _DATE,
            "reason": f"{marker}-vendor-refund",
        },
        idempotency_key=f"vendor_refund.create:{refund_bill['id']}",
        run_id=run_id,
        expected_model="account.move",
        expected_state="draft",
        expected_move_type="in_refund",
        expected_source_id=refund_bill["id"],
    )
    for entry in (first_entry, second_entry):
        _write_twice(
            alias,
            "journal_entry.post",
            {"move_id": entry["id"]},
            idempotency_key=f"journal_entry.post:{entry['id']}",
            run_id=run_id,
            expected_model="account.move",
            expected_state="posted",
            expected_move_type="entry",
        )

    invoice_status = _read(
        alias,
        "invoice.payment_status.inspect",
        {"invoice_id": invoices[1]["id"]},
        run_id=run_id,
        case="reconcile-invoice",
    )
    invoice_line_id = _account_line_id(
        invoice_status["data"]["receivable_payable_lines"],
        _RECEIVABLE_ACCOUNT_ID,
    )
    entry_document = _read(
        alias,
        "journal_entry.get",
        {"entry_id": first_entry["id"]},
        run_id=run_id,
        case="reconcile-entry",
    )
    entry_line_id = _account_line_id(
        entry_document["data"]["lines"], _RECEIVABLE_ACCOUNT_ID
    )
    reconciliation_line_ids = sorted((invoice_line_id, entry_line_id))
    reconciliation = _write_twice(
        alias,
        "reconciliation.apply",
        {"line_ids": reconciliation_line_ids},
        idempotency_key=(
            f"reconciliation.apply:{reconciliation_line_ids[0]}:"
            f"{reconciliation_line_ids[1]}"
        ),
        run_id=run_id,
        expected_model="account.move.line",
        expected_state="reconciled",
    )
    assert reconciliation["id"] is None
    assert reconciliation["line_ids"] == reconciliation_line_ids
    assert reconciliation["reconciled"] is True
    assert reconciliation["partial_reconcile_ids"]
    assert reconciliation["full_reconcile_id"] is not None

    undo = _write_twice(
        alias,
        "reconciliation.undo",
        {"line_ids": reconciliation["line_ids"]},
        idempotency_key=(
            f"reconciliation.undo:{reconciliation['line_ids'][0]}:"
            f"{reconciliation['line_ids'][1]}"
        ),
        run_id=run_id,
        expected_model="account.move.line",
        expected_state="unreconciled",
    )
    assert undo["id"] is None
    assert undo["name"] is None
    assert undo["line_ids"] == reconciliation_line_ids
    assert undo["partial_reconcile_ids"] == []
    assert undo["full_reconcile_id"] is None
    assert undo["reconciled"] is False

    _write_twice(
        alias,
        "journal_entry.reverse",
        {
            "move_id": second_entry["id"],
            "date": _DATE,
            "reason": f"{marker}-reverse",
        },
        idempotency_key=f"journal_entry.reverse:{second_entry['id']}",
        run_id=run_id,
        expected_model="account.move",
        expected_state="posted",
        expected_move_type="entry",
        expected_source_id=second_entry["id"],
    )

    bank_transaction = _write_twice(
        alias,
        "bank.transaction.record",
        {
            "journal_id": _BANK_JOURNAL_ID,
            "date": _DATE,
            "amount": "6.25",
            "payment_ref": f"{marker}-bank-transaction",
            "partner_id": customer_id,
        },
        idempotency_key=f"core-write:{run_id}:{alias}:bank-transaction",
        run_id=run_id,
        expected_model="account.bank.statement.line",
        expected_state="posted",
        expected_move_type="entry",
        expect_positive_source_id=True,
    )
    assert bank_transaction["line_ids"]

    receipt = _write_twice(
        alias,
        "receivable.payment.register",
        {
            "move_id": invoices[0]["id"],
            "journal_id": _BANK_JOURNAL_ID,
            "payment_date": _DATE,
        },
        idempotency_key=f"receivable.payment.register:{invoices[0]['id']}",
        run_id=run_id,
        expected_model="account.payment",
        expected_state=("in_process", "paid"),
        expected_source_id=invoices[0]["id"],
    )
    _write_twice(
        alias,
        "payable.payment.register",
        {
            "move_id": bill["id"],
            "journal_id": _BANK_JOURNAL_ID,
            "payment_date": _DATE,
        },
        idempotency_key=f"payable.payment.register:{bill['id']}",
        run_id=run_id,
        expected_model="account.payment",
        expected_state=("in_process", "paid"),
        expected_source_id=bill["id"],
    )
    _write_twice(
        alias,
        "payment.cancel",
        {"payment_id": receipt["id"]},
        idempotency_key=f"payment.cancel:{receipt['id']}",
        run_id=run_id,
        expected_model="account.payment",
        expected_state="canceled",
    )

    draft_payment_id = _create_draft_payment(
        alias, run_id, config_path, runtime_document
    )
    _write_twice(
        alias,
        "payment.post",
        {"payment_id": draft_payment_id},
        idempotency_key=f"payment.post:{draft_payment_id}",
        run_id=run_id,
        expected_model="account.payment",
        expected_state=("in_process", "paid"),
    )


@pytest.mark.integration
def test_core_write_batch_runs_one_serial_chain_per_isolated_alias() -> None:
    config_path = _enabled_runtime_config()
    runtime_document = _assert_runtime_aliases(config_path)
    run_id = str(uuid.uuid4())
    for alias in _ALIASES:
        _run_alias_chain(alias, run_id, config_path, runtime_document)
