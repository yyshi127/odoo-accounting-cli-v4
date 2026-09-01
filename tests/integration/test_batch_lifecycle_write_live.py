"""Transactional live proof for batch move and payment lifecycles.

The worker runs the public CLI against the real ORM as the configured accountant
in one outer transaction per isolated database.  It proves sorted batch results,
immediate replay, full-scope preflight and rollback without committing fixtures.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import sysconfig
import uuid
from pathlib import Path
from typing import Any

import test_document_lifecycle_write_batch_live as lifecycle
import test_payment_bank_capability_batch_live as core

_ALLOW_ENV = "ODACV4_ALLOW_BATCH_LIFECYCLE_SMOKE"
_BATCH_CAPABILITIES = {
    "invoice.post",
    "invoice.cancel",
    "invoice.reset_to_draft",
    "journal_entry.post",
    "journal_entry.cancel",
    "journal_entry.reset_to_draft",
    "payment.post",
    "payment.cancel",
    "payment.reset_to_draft",
}
_CAPABILITIES = _BATCH_CAPABILITIES | {
    "customer_invoice.create",
    "journal_entry.create",
    "payment.create",
}
_MODELS = {
    capability_id: (
        "account.payment" if capability_id.startswith("payment.") else "account.move"
    )
    for capability_id in _BATCH_CAPABILITIES
}


def _batch_fields(capability_id: str) -> tuple[str, str]:
    if capability_id.startswith("payment."):
        return "payment_id", "payment_ids"
    return "move_id", "move_ids"


def _batch_request_and_key(
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    supplied_ids: list[int],
) -> tuple[dict[str, Any], dict[str, Any], str]:
    from odoo_accounting_cli_v4.capabilities.core_writes import (
        _expected_idempotency_key,
        validate_core_write_request,
    )

    _, batch_field = _batch_fields(capability_id)
    request = core._request(alias, run_id, capability_id, {batch_field: supplied_ids})
    _, context, normalized = validate_core_write_request(capability_id, request)
    key = _expected_idempotency_key(capability_id, normalized, context["company_id"])
    assert isinstance(key, str)
    return request, normalized, key


def _invoke_batch(
    client: core._RuntimeClient,
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    supplied_ids: list[int],
) -> dict[str, Any]:
    from odoo_accounting_cli_v4 import cli
    from odoo_accounting_cli_v4.bridge.core_writes import OdooCoreWritePort

    request, normalized, key = _batch_request_and_key(
        alias, run_id, capability_id, supplied_ids
    )
    _, batch_field = _batch_fields(capability_id)
    expected_ids = normalized[batch_field]
    stdout, stderr = io.StringIO(), io.StringIO()
    client.last_runtime_failure = None
    exit_code = cli.main(
        [
            "write",
            "run",
            capability_id,
            "--request",
            "-",
            "--idempotency-key",
            key,
            "--confirm",
            capability_id,
        ],
        stdin=io.StringIO(json.dumps(request)),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda _capability, _request: OdooCoreWritePort(client),
    )
    if exit_code != 0:
        raise AssertionError(stdout.getvalue() + stderr.getvalue()) from (
            client.last_runtime_failure
        )
    assert stderr.getvalue() == "" and len(stdout.getvalue().splitlines()) == 1
    response = json.loads(stdout.getvalue())
    assert response["schema_version"] == "v1"
    assert response["request_id"] == request["request_id"]
    assert response["capability"] == capability_id
    assert response["success"] is True and response["status"] == "verified"
    assert response["error"] is None
    assert response["odoo"] == {
        "database": alias,
        "company_id": lifecycle._COMPANY_ID,
        "user_id": lifecycle._USER_ID,
        "model": _MODELS[capability_id],
        "record_ids": expected_ids,
    }
    data = response["data"]
    result = data["result"]
    assert result["processed_count"] == len(expected_ids)
    assert [item["id"] for item in result["items"]] == expected_ids
    assert all(
        item["model"] == _MODELS[capability_id]
        and item["company_id"] == lifecycle._COMPANY_ID
        for item in result["items"]
    )
    assert response["audit"]["verification"] == {
        "processed_count": len(expected_ids),
        "idempotent_replay": data["idempotent_replay"],
    }
    client.capabilities.add(capability_id)
    return data


def _invoke_missing_id_failure(
    client: core._RuntimeClient,
    alias: str,
    run_id: uuid.UUID,
    valid_id: int,
    missing_id: int,
) -> None:
    from odoo_accounting_cli_v4 import cli
    from odoo_accounting_cli_v4.bridge.core_writes import OdooCoreWritePort

    capability_id = "invoice.post"
    request, _, key = _batch_request_and_key(
        alias, run_id, capability_id, [missing_id, valid_id]
    )
    stdout, stderr = io.StringIO(), io.StringIO()
    client.last_runtime_failure = None
    exit_code = cli.main(
        [
            "write",
            "run",
            capability_id,
            "--request",
            "-",
            "--idempotency-key",
            key,
            "--confirm",
            capability_id,
        ],
        stdin=io.StringIO(json.dumps(request)),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda _capability, _request: OdooCoreWritePort(client),
    )
    assert exit_code == 4
    assert stderr.getvalue() == "" and len(stdout.getvalue().splitlines()) == 1
    response = json.loads(stdout.getvalue())
    assert response["success"] is False and response["data"] is None
    assert response["error"]["code"] == "record_not_found"
    assert getattr(client.last_runtime_failure, "code", None) == "record_not_found"


def _batch_twice(
    client: core._RuntimeClient,
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    record_ids: list[int],
) -> list[dict[str, Any]]:
    expected_ids = sorted(record_ids)
    first = _invoke_batch(
        client, alias, run_id, capability_id, list(reversed(expected_ids))
    )
    second = _invoke_batch(client, alias, run_id, capability_id, expected_ids)
    assert first["idempotent_replay"] is False
    assert second["idempotent_replay"] is True
    assert first["result"] == second["result"]
    return first["result"]["items"]


def _fixture_ids(env: Any, alias: str) -> dict[str, int]:
    ids = lifecycle._fixture_ids(env, alias)
    method_lines = env["account.payment.method.line"].search(
        [
            ("journal_id.company_id", "=", lifecycle._COMPANY_ID),
            ("journal_id.type", "=", "bank"),
            ("payment_type", "=", "inbound"),
            ("payment_method_id.code", "=", "manual"),
        ],
        order="id",
    )
    method_line = next(
        (
            line
            for line in method_lines
            if line.payment_account_id
            and line.payment_account_id.reconcile
            and lifecycle._COMPANY_ID in line.payment_account_id.company_ids.ids
        ),
        None,
    )
    if method_line is None:
        raise RuntimeError("no company-scoped inbound manual payment method is usable")
    return {
        **ids,
        "bank_journal": method_line.journal_id.id,
        "inbound_method": method_line.id,
    }


def _create_invoices(
    client: core._RuntimeClient,
    alias: str,
    run_id: uuid.UUID,
    ids: dict[str, int],
    today: str,
) -> list[int]:
    result = []
    for index in (1, 2):
        created = core._write(
            client,
            alias,
            run_id,
            "customer_invoice.create",
            {
                "partner_id": ids["customer"],
                "journal_id": ids["sale_journal"],
                "date": today,
                "invoice_date": today,
                "currency_id": ids["currency"],
                "lines": [
                    {
                        "name": f"Batch lifecycle invoice {run_id.hex} {index}",
                        "account_id": ids["income"],
                        "quantity": "1",
                        "price_unit": str(20 + index),
                        "tax_ids": [],
                    }
                ],
            },
            explicit_key=f"batch-lifecycle-invoice-{alias}-{run_id.hex}-{index}",
        )
        result.append(created["id"])
    return result


def _create_entries(
    client: core._RuntimeClient,
    alias: str,
    run_id: uuid.UUID,
    ids: dict[str, int],
    today: str,
) -> list[int]:
    result = []
    for index in (1, 2):
        amount = str(30 + index)
        created = core._write(
            client,
            alias,
            run_id,
            "journal_entry.create",
            {
                "journal_id": ids["general_journal"],
                "date": today,
                "reference": f"Batch lifecycle entry {run_id.hex} {index}",
                "lines": [
                    {
                        "name": f"Batch lifecycle debit {run_id.hex} {index}",
                        "account_id": ids["asset"],
                        "partner_id": None,
                        "debit": amount,
                        "credit": "0",
                    },
                    {
                        "name": f"Batch lifecycle credit {run_id.hex} {index}",
                        "account_id": ids["income"],
                        "partner_id": None,
                        "debit": "0",
                        "credit": amount,
                    },
                ],
            },
            explicit_key=f"batch-lifecycle-entry-{alias}-{run_id.hex}-{index}",
        )
        result.append(created["id"])
    return result


def _create_payments(
    client: core._RuntimeClient,
    alias: str,
    run_id: uuid.UUID,
    ids: dict[str, int],
    today: str,
) -> list[int]:
    result = []
    for index in (1, 2):
        created = core._write(
            client,
            alias,
            run_id,
            "payment.create",
            {
                "payment_type": "inbound",
                "partner_type": "customer",
                "partner_id": ids["customer"],
                "amount": str(40 + index),
                "currency_id": ids["currency"],
                "journal_id": ids["bank_journal"],
                "payment_method_line_id": ids["inbound_method"],
                "date": today,
                "payment_reference": (f"Batch lifecycle payment {run_id.hex} {index}"),
            },
            explicit_key=f"batch-lifecycle-payment-{alias}-{run_id.hex}-{index}",
        )
        result.append(created["id"])
    return result


def _states(env: Any, model: str, record_ids: list[int]) -> set[str]:
    records = env[model].browse(record_ids).exists()
    assert set(records.ids) == set(record_ids)
    records.invalidate_recordset(["state"])
    return set(records.mapped("state"))


def _run_chain(
    client: core._RuntimeClient, alias: str, run_id: uuid.UUID
) -> dict[str, Any]:
    from odoo import fields

    env = client.env
    assert env.uid == lifecycle._USER_ID and env.su is False
    assert env.company.id == lifecycle._COMPANY_ID
    ids = _fixture_ids(env, alias)
    today = fields.Date.to_string(fields.Date.context_today(env.user))
    invoices = _create_invoices(client, alias, run_id, ids, today)
    entries = _create_entries(client, alias, run_id, ids, today)
    payments = _create_payments(client, alias, run_id, ids, today)

    missing_move_id = (
        env["account.move"].search([], order="id desc", limit=1).id + 10_000_000
    )
    _invoke_missing_id_failure(client, alias, run_id, invoices[0], missing_move_id)
    assert _states(env, "account.move", invoices) == {"draft"}

    for prefix, record_ids in (("invoice", invoices), ("journal_entry", entries)):
        posted = _batch_twice(client, alias, run_id, f"{prefix}.post", record_ids)
        assert {item["state"] for item in posted} == {"posted"}
        assert _states(env, "account.move", record_ids) == {"posted"}
        canceled = _batch_twice(client, alias, run_id, f"{prefix}.cancel", record_ids)
        assert {item["state"] for item in canceled} == {"cancel"}
        assert _states(env, "account.move", record_ids) == {"cancel"}
        drafted = _batch_twice(
            client, alias, run_id, f"{prefix}.reset_to_draft", record_ids
        )
        assert {item["state"] for item in drafted} == {"draft"}
        assert _states(env, "account.move", record_ids) == {"draft"}

    posted_payments = _batch_twice(client, alias, run_id, "payment.post", payments)
    assert {item["state"] for item in posted_payments} <= {"in_process", "paid"}
    assert _states(env, "account.payment", payments) <= {"in_process", "paid"}
    canceled_payments = _batch_twice(client, alias, run_id, "payment.cancel", payments)
    assert {item["state"] for item in canceled_payments} == {"canceled"}
    assert _states(env, "account.payment", payments) == {"canceled"}
    drafted_payments = _batch_twice(
        client, alias, run_id, "payment.reset_to_draft", payments
    )
    assert {item["state"] for item in drafted_payments} == {"draft"}
    assert _states(env, "account.payment", payments) == {"draft"}

    assert client.capabilities == _CAPABILITIES
    return {
        "batch_capabilities": len(_BATCH_CAPABILITIES),
        "batch_records": len(invoices) + len(entries) + len(payments),
        "immediate_replays": len(_BATCH_CAPABILITIES),
        "atomic_missing_id_preflight": True,
    }


def test_batch_lifecycles_roll_back_one_real_chain_per_alias() -> None:
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
            part
            for part in (
                str(lifecycle._root() / "src"),
                sysconfig.get_path("purelib"),
                environment.get("PYTHONPATH"),
            )
            if part
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
        assert completed.stderr == ""
        assert len(completed.stdout.splitlines()) == 1
        result = json.loads(completed.stdout)
        assert result == {
            "alias": alias,
            "atomic_missing_id_preflight": True,
            "batch_capabilities": 9,
            "batch_records": 6,
            "capabilities": sorted(_CAPABILITIES),
            "company_id": lifecycle._COMPANY_ID,
            "database": lifecycle._DATABASES[alias],
            "execution": "in_process_cli_real_orm",
            "immediate_replays": 9,
            "rollback_verified": True,
            "user_id": lifecycle._USER_ID,
        }
        print(completed.stdout.strip(), flush=True)


def _live_worker() -> int:
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
    details: dict[str, Any] = {}
    failure: BaseException | None = None
    try:
        env = api.Environment(
            cursor,
            lifecycle._USER_ID,
            {
                "allowed_company_ids": [lifecycle._COMPANY_ID],
                "active_test": True,
                "lang": "en_US",
                "tz": "Asia/Shanghai",
            },
        )
        assert env.user.login == lifecycle._USER_LOGIN
        client = core._RuntimeClient(env)
        client.tracked = tracked
        details = _run_chain(client, args.alias, args.run_id)
    except BaseException as exc:  # noqa: BLE001 - always roll back live fixtures
        failure = exc
    finally:
        try:
            if env is not None:
                core._collect_marked(env, tracked, args.run_id.hex)
        except Exception as exc:  # noqa: BLE001 - preserve the original failure
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
    assert client is not None
    print(
        json.dumps(
            {
                "alias": args.alias,
                "database": args.database,
                "user_id": lifecycle._USER_ID,
                "company_id": lifecycle._COMPANY_ID,
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
