"""Shared rollback proof for the accounting-delivery capability batch.

The two isolated aliases run the same public-CLI chain as the configured
accountant.  Every fixture and delivery side effect remains inside one outer
transaction and is audited from a fresh cursor after rollback.  Delivery
assertions prove native Odoo processing and serial replay only; they do not
inspect or claim mail-queue persistence or external SMTP delivery.

The accountant has read-only partner access and both fixed test customers have
no email address.  The fixture therefore gives that existing customer a temporary
``example.invalid`` email through a test-only sudo recordset in the same outer
transaction.  Every CLI call still runs as the configured uid with ``su=False``,
and a fresh cursor verifies that the fixture email rolled back.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import subprocess
import sys
import sysconfig
import uuid
from datetime import timedelta
from pathlib import Path
from typing import Any

try:
    import pytest
except ModuleNotFoundError:
    if "--live-worker" not in sys.argv:
        raise
    pytest = None

import test_payment_bank_capability_batch_live as core

_ALLOW_ENV = "ODACV4_ALLOW_ACCOUNTING_DELIVERY_SMOKE"
_TARGET_CAPABILITIES = frozenset(
    {
        "invoice.send.inspect",
        "invoice.send",
        "payment.receipt.send.inspect",
        "payment.receipt.send",
        "report.customer_statement.export",
        "report.customer_statement.send",
        "report.followup.export",
        "report.followup.send",
        "invoice.followup.update",
    }
)
_FIXTURE_CAPABILITIES = frozenset(
    {
        "customer_invoice.create",
        "invoice.post",
        "payment.create",
        "payment.post",
    }
)
_SEND_CAPABILITIES = frozenset(
    {
        "invoice.send",
        "payment.receipt.send",
        "report.customer_statement.send",
        "report.followup.send",
    }
)
_ACL_DENIED_CAPABILITIES = frozenset(
    {"report.customer_statement.send", "report.followup.send"}
)
_READ_CAPABILITIES = frozenset(
    {
        "invoice.send.inspect",
        "payment.receipt.send.inspect",
        "report.customer_statement.export",
        "report.followup.export",
    }
)
_ARTIFACT_MODELS = (
    "mail.message",
    "mail.mail",
    "mail.notification",
    "mail.followers",
    "ir.attachment",
    "account.move.send.wizard",
    "mail.compose.message",
    "account.report.send",
)
_AUDIT_MODELS = (*core._BUSINESS_MODELS, "res.partner", *_ARTIFACT_MODELS)


def _enabled_runtime() -> tuple[Path, dict[str, Any]]:
    assert pytest is not None
    if os.environ.get(_ALLOW_ENV) != "1":
        pytest.skip(f"set {_ALLOW_ENV}=1 to authorize isolated write smoke")
    raw = os.environ.get(core._CONFIG_ENV)
    if not raw:
        pytest.skip(f"{core._CONFIG_ENV} is not configured")
    path = Path(raw)
    if not path.is_file():
        pytest.skip(f"{core._CONFIG_ENV} does not name an existing file")
    document = json.loads(path.read_text(encoding="utf-8"))
    aliases = document.get("aliases")
    assert isinstance(aliases, dict) and set(aliases) == set(core._ALIASES)
    assert {
        alias: aliases[alias].get("database") for alias in core._ALIASES
    } == core._DATABASES
    assert all(
        aliases[alias].get("companies", {}).get(str(core._COMPANY_ID))
        == [core._USER_LOGIN]
        for alias in core._ALIASES
    )
    return path, document


def _artifact_baseline(env: Any) -> dict[str, int]:
    baseline: dict[str, int] = {}
    for model_name in _AUDIT_MODELS:
        # Odoo implicitly hides field-backed attachments unless the domain
        # explicitly mentions ``id`` or ``res_field``.  Use an explicit all-ID
        # domain so the baseline and later ``id > baseline`` query see the same
        # attachment population.
        domain = [("id", "!=", False)] if model_name == "ir.attachment" else []
        record = env[model_name].sudo().search(domain, order="id desc", limit=1)
        baseline[model_name] = record.id if record else 0
    return baseline


def _fixture_ids(env: Any, alias: str) -> dict[str, int]:
    company = core._one(env["res.company"].browse(core._COMPANY_ID).exists(), "company")
    customer_id = core._PARTNERS[alias]["customer"]
    customer = core._one(
        env["res.partner"].search(
            [
                ("id", "=", customer_id),
                ("company_id", "in", [False, core._COMPANY_ID]),
            ]
        ),
        "customer",
    )
    bank_journal = core._one(
        env["account.journal"].search(
            [
                ("id", "=", 14),
                ("company_id", "=", core._COMPANY_ID),
                ("type", "=", "bank"),
            ]
        ),
        "bank journal",
    )
    sale_journal = core._one(
        env["account.journal"].search(
            [("company_id", "=", core._COMPANY_ID), ("type", "=", "sale")],
            order="id",
            limit=1,
        ),
        "sale journal",
    )
    income_account = core._one(
        env["account.account"].search(
            [
                ("company_ids", "in", [core._COMPANY_ID]),
                ("account_type", "=", "income"),
            ],
            order="id",
            limit=1,
        ),
        "income account",
    )
    inbound_method = core._one(
        env["account.payment.method.line"].search(
            [
                ("journal_id", "=", bank_journal.id),
                ("payment_type", "=", "inbound"),
                ("payment_method_id.code", "=", "manual"),
            ],
            order="id",
            limit=1,
        ),
        "inbound manual payment method line",
    )
    return {
        "customer": customer.id,
        "currency": company.currency_id.id,
        "bank_journal": bank_journal.id,
        "sale_journal": sale_journal.id,
        "income": income_account.id,
        "inbound_method": inbound_method.id,
    }


def _artifact_delta(env: Any, baseline: dict[str, int]) -> dict[str, set[int]]:
    return {
        model_name: set(
            env[model_name].sudo().search([("id", ">", baseline[model_name])]).ids
        )
        for model_name in _ARTIFACT_MODELS
    }


def _collect_since(
    env: Any,
    tracked: dict[str, set[int]],
    baseline: dict[str, int],
    marker: str,
) -> None:
    for model_name in _AUDIT_MODELS:
        tracked[model_name].update(
            env[model_name].sudo().search([("id", ">", baseline[model_name])]).ids
        )
    tracked["res.partner"].update(
        env["res.partner"]
        .sudo()
        .with_context(active_test=False)
        .search(
            [
                ("id", ">", baseline["res.partner"]),
                "|",
                "|",
                ("name", "ilike", marker),
                ("ref", "ilike", marker),
                ("email", "ilike", marker),
            ]
        )
        .ids
    )
    core._collect_marked(env, tracked, marker)


def _delivery_cli(
    client: core._RuntimeClient,
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    parameters: dict[str, Any],
    *,
    key: str | None = None,
) -> dict[str, Any]:
    from odoo_accounting_cli_v4 import cli
    from odoo_accounting_cli_v4.bridge.accounting_delivery import (
        OdooAccountingDeliveryPort,
    )
    from odoo_accounting_cli_v4.bridge.financial_reports import (
        OdooFinancialReportExportPort,
    )

    request = core._request(alias, run_id, capability_id, parameters)
    if capability_id.endswith(".export"):
        port = OdooFinancialReportExportPort(client)
    else:
        port = OdooAccountingDeliveryPort(client)
    if capability_id in _READ_CAPABILITIES:
        argv = ["read", capability_id, "--request", "-"]
    else:
        assert key is not None
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
        "company_id": core._COMPANY_ID,
        "user_id": core._USER_ID,
    }
    if capability_id in _SEND_CAPABILITIES:
        assert response["warnings"] == [
            {
                "code": "capability_degraded",
                "reason_code": "odoo_queue_delivery_only",
            }
        ]
        assert response["audit"]["verification"] == {
            "processed_count": response["data"]["result"]["processed_count"],
            "idempotent_replay": response["data"]["idempotent_replay"],
        }
    client.capabilities.add(capability_id)
    return response["data"]


def _core_twice(
    client: core._RuntimeClient,
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    from odoo_accounting_cli_v4.capabilities.core_writes import (
        _expected_idempotency_key,
        validate_core_write_request,
    )

    request = core._request(alias, run_id, capability_id, parameters)
    _, context, normalized = validate_core_write_request(capability_id, request)
    key = _expected_idempotency_key(capability_id, normalized, context["company_id"])
    if key is None:
        canonical = json.dumps(
            normalized,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        key = f"fixture:{capability_id}:{hashlib.sha256(canonical).hexdigest()[:32]}"
    first = core._cli(client, alias, run_id, capability_id, parameters, key=key)
    tracked = {
        model_name: set(record_ids) for model_name, record_ids in client.tracked.items()
    }
    second = core._cli(client, alias, run_id, capability_id, parameters, key=key)
    assert first["idempotent_replay"] is False
    assert second["idempotent_replay"] is True
    assert second["result"] == first["result"]
    assert client.tracked == tracked
    return first["result"]


def _delivery_acl_denied(
    client: core._RuntimeClient,
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    parameters: dict[str, Any],
    key: str,
    baseline: dict[str, int],
) -> None:
    from odoo_accounting_cli_v4 import cli
    from odoo_accounting_cli_v4.bridge.accounting_delivery import (
        OdooAccountingDeliveryPort,
    )

    assert capability_id in _ACL_DENIED_CAPABILITIES
    assert client.env["res.partner"].has_access("read")
    assert not client.env["res.partner"].has_access("write")
    request = core._request(alias, run_id, capability_id, parameters)
    artifacts = _artifact_delta(client.env, baseline)
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
        port_factory=lambda _capability, _request: OdooAccountingDeliveryPort(client),
    )
    assert exit_code == 3
    assert stderr.getvalue() == ""
    assert len(stdout.getvalue().splitlines()) == 1
    response = json.loads(stdout.getvalue())
    assert response["success"] is False
    assert response["status"] == "denied"
    assert response["capability"] == capability_id
    assert response["error"]["code"] == "unauthorized"
    assert response["odoo"] == {
        "database": alias,
        "company_id": core._COMPANY_ID,
        "user_id": core._USER_ID,
        "model": "res.partner",
        "record_ids": [],
    }
    assert _artifact_delta(client.env, baseline) == artifacts
    client.capabilities.add(capability_id)


def _delivery_twice(
    client: core._RuntimeClient,
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    parameters: dict[str, Any],
    key: str,
    baseline: dict[str, int],
) -> dict[str, Any]:
    first = _delivery_cli(client, alias, run_id, capability_id, parameters, key=key)
    artifacts = _artifact_delta(client.env, baseline)
    second = _delivery_cli(client, alias, run_id, capability_id, parameters, key=key)
    assert first["idempotent_replay"] is False
    assert second["idempotent_replay"] is True
    assert second["result"] == first["result"]
    if capability_id in _SEND_CAPABILITIES:
        assert _artifact_delta(client.env, baseline) == artifacts
        record_id = next(
            parameters[key]
            for key in ("move_id", "payment_id", "partner_id")
            if key in parameters
        )
        assert first["result"] == {
            "record_ids": [record_id],
            "processed_count": 1,
        }
    return first["result"]


def _assert_export(data: dict[str, Any], export_format: str = "pdf") -> None:
    content = base64.b64decode(data["content_base64"], validate=True)
    assert data["format"] == export_format
    assert data["byte_count"] == len(content) > 0
    assert data["sha256"] == hashlib.sha256(content).hexdigest()
    assert data["filename"].lower().endswith("." + export_format)
    assert data["mimetype"] == "application/pdf"
    assert content.startswith(b"%PDF-")


def _delivery_key_marker(capability_id: str, key: str) -> str:
    raw = f"{capability_id}\0{core._COMPANY_ID}\0{key}".encode()
    return f"ODACV4DELIVERYKEY-{hashlib.sha256(raw).hexdigest()}"


def _assert_marked_message(
    env: Any,
    capability_id: str,
    key: str,
    model_name: str,
    record_id: int,
) -> int:
    marker = _delivery_key_marker(capability_id, key)
    messages = (
        env["mail.message"].sudo().search([("body", "ilike", marker)], order="id")
    )
    messages = messages.filtered(lambda message: marker in (message.body or ""))
    assert len(messages) == 1
    assert messages.model == model_name and messages.res_id == record_id
    return messages.id


def _exercise(
    client: core._RuntimeClient,
    alias: str,
    run_id: uuid.UUID,
    baseline: dict[str, int],
    fixture_state: dict[str, Any],
) -> dict[str, Any]:
    from odoo import fields

    env = client.env
    assert (
        env.uid == core._USER_ID and not env.su and env.company.id == core._COMPANY_ID
    )
    ids = _fixture_ids(env, alias)
    today_date = fields.Date.context_today(env.user)
    today = fields.Date.to_string(today_date)
    yesterday = fields.Date.to_string(today_date - timedelta(days=1))
    marker = f"ODACV4-DELIVERY-{alias}-{run_id.hex}"

    partner_id = ids["customer"]
    partner = env["res.partner"].browse(partner_id)
    original_email = partner.email or None
    fixture_state.update(partner_id=partner_id, original_email=original_email)
    fixture_email = f"delivery-{run_id.hex}@example.invalid"
    partner.sudo().write({"email": fixture_email})
    partner.invalidate_recordset(["email"])
    assert partner.email == fixture_email

    invoice = _core_twice(
        client,
        alias,
        run_id,
        "customer_invoice.create",
        {
            "partner_id": partner_id,
            "journal_id": ids["sale_journal"],
            "date": today,
            "invoice_date": yesterday,
            "invoice_date_due": yesterday,
            "currency_id": ids["currency"],
            "reference": marker,
            "lines": [
                {
                    "name": marker,
                    "account_id": ids["income"],
                    "quantity": "1",
                    "price_unit": "125.00",
                    "tax_ids": [],
                }
            ],
        },
    )
    invoice_id = invoice["id"]
    _core_twice(
        client,
        alias,
        run_id,
        "invoice.post",
        {"move_id": invoice_id},
    )

    payment = _core_twice(
        client,
        alias,
        run_id,
        "payment.create",
        {
            "payment_type": "inbound",
            "partner_type": "customer",
            "partner_id": partner_id,
            "amount": "25.00",
            "currency_id": ids["currency"],
            "journal_id": ids["bank_journal"],
            "payment_method_line_id": ids["inbound_method"],
            "date": today,
            "payment_reference": marker,
        },
    )
    payment_id = payment["id"]
    _core_twice(
        client,
        alias,
        run_id,
        "payment.post",
        {"payment_id": payment_id},
    )
    assert env["account.move"].browse(invoice_id).state == "posted"
    assert env["account.payment"].browse(payment_id).state in {"in_process", "paid"}

    invoice_inspection = _delivery_cli(
        client,
        alias,
        run_id,
        "invoice.send.inspect",
        {"move_id": invoice_id},
    )
    payment_inspection = _delivery_cli(
        client,
        alias,
        run_id,
        "payment.receipt.send.inspect",
        {"payment_id": payment_id},
    )
    for inspection, record_id in (
        (invoice_inspection, invoice_id),
        (payment_inspection, payment_id),
    ):
        assert inspection["idempotent_replay"] is False
        assert len(inspection["result"]["records"]) == 1
        descriptor = inspection["result"]["records"][0]
        assert descriptor["record_id"] == record_id
        assert descriptor["partner_id"] == partner_id
        assert descriptor["recipient_emails"] == [
            f"delivery-{run_id.hex}@example.invalid"
        ]
        assert descriptor["sendable"] is True

    statement_export = _delivery_cli(
        client,
        alias,
        run_id,
        "report.customer_statement.export",
        {
            "partner_id": partner_id,
            "date_from": yesterday,
            "date_to": today,
            "format": "pdf",
        },
    )
    followup_export = _delivery_cli(
        client,
        alias,
        run_id,
        "report.followup.export",
        {"partner_id": partner_id, "as_of": today, "format": "pdf"},
    )
    _assert_export(statement_export)
    _assert_export(followup_export)

    send_cases = (
        ("invoice.send", {"move_id": invoice_id}, "account.move", invoice_id),
        (
            "payment.receipt.send",
            {"payment_id": payment_id},
            "account.payment",
            payment_id,
        ),
    )
    message_ids: set[int] = set()
    for capability_id, parameters, model_name, record_id in send_cases:
        key = f"delivery:{capability_id}:{alias}:{run_id.hex}"
        _delivery_twice(
            client,
            alias,
            run_id,
            capability_id,
            parameters,
            key,
            baseline,
        )
        message_ids.add(
            _assert_marked_message(env, capability_id, key, model_name, record_id)
        )

    _delivery_acl_denied(
        client,
        alias,
        run_id,
        "report.customer_statement.send",
        {
            "partner_id": partner_id,
            "date_from": yesterday,
            "date_to": today,
        },
        f"delivery:report.customer-statement:{alias}:{run_id.hex}",
        baseline,
    )
    _delivery_acl_denied(
        client,
        alias,
        run_id,
        "report.followup.send",
        {"partner_id": partner_id, "as_of": today},
        f"delivery:report.followup:{alias}:{run_id.hex}",
        baseline,
    )

    move = env["account.move"].browse(invoice_id)
    receivable = move.line_ids.filtered(
        lambda line: line.account_id.account_type == "asset_receivable"
    )
    assert len(receivable) == 1 and receivable.no_followup is False
    _delivery_twice(
        client,
        alias,
        run_id,
        "invoice.followup.update",
        {"move_id": invoice_id, "no_followup": True},
        f"delivery:invoice-followup:{alias}:{run_id.hex}",
        baseline,
    )
    move.invalidate_recordset(["no_followup"])
    term_lines = move.line_ids.filtered(
        lambda line: (
            line.account_id.account_type in {"asset_receivable", "liability_payable"}
        )
    )
    term_lines.invalidate_recordset(["no_followup"])
    assert move.no_followup is True
    assert term_lines and all(line.no_followup is True for line in term_lines)

    assert _TARGET_CAPABILITIES <= client.capabilities
    assert client.capabilities == _TARGET_CAPABILITIES | _FIXTURE_CAPABILITIES
    assert len(message_ids) == len(_SEND_CAPABILITIES - _ACL_DENIED_CAPABILITIES)
    return {
        "commands_exercised": len(_TARGET_CAPABILITIES),
        "successful_commands": len(_TARGET_CAPABILITIES - _ACL_DENIED_CAPABILITIES),
        "acl_denied_commands": sorted(_ACL_DENIED_CAPABILITIES),
        "exports_verified": 2,
        "immediate_replays": 3,
        "inspections_verified": 2,
        "marked_messages_verified": len(message_ids),
        "external_delivery_claimed": False,
    }


if pytest is not None:

    @pytest.mark.integration
    def test_accounting_delivery_batch_rolls_back_per_alias() -> None:
        config_path, runtime = _enabled_runtime()
        run_id = uuid.uuid4()
        for alias in core._ALIASES:
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
                timeout=max(timeout, 1200),
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
            assert result["database"] == core._DATABASES[alias]
            assert result["user_id"] == core._USER_ID
            assert result["company_id"] == core._COMPANY_ID
            assert result["commands_exercised"] == 9
            assert result["exports_verified"] == 2
            assert result["inspections_verified"] == 2
            assert result["immediate_replays"] == 3
            assert result["marked_messages_verified"] == 2
            assert result["successful_commands"] == 7
            assert result["acl_denied_commands"] == sorted(_ACL_DENIED_CAPABILITIES)
            assert result["external_delivery_claimed"] is False
            assert result["fixture_email_rollback_verified"] is True
            assert result["rollback_verified"] is True
            assert set(result["capabilities"]) == _TARGET_CAPABILITIES
            print(json.dumps(result, sort_keys=True, separators=(",", ":")), flush=True)


def _verify_fixture_rollback(registry: Any, fixture_state: dict[str, Any]) -> None:
    if not fixture_state:
        return
    from odoo import SUPERUSER_ID, api

    cursor = registry.cursor()
    try:
        env = api.Environment(
            cursor,
            SUPERUSER_ID,
            {"allowed_company_ids": [core._COMPANY_ID], "active_test": False},
        )
        partner = env["res.partner"].browse(fixture_state["partner_id"]).exists()
        if (
            len(partner) != 1
            or (partner.email or None) != fixture_state["original_email"]
        ):
            raise RuntimeError("the temporary fixture email survived rollback")
    finally:
        cursor.rollback()
        cursor.close()


def _live_worker() -> int:
    args = core._arguments(None)
    sys.path.insert(0, str(args.odoo_source.resolve(strict=True)))
    sys.path.insert(0, str((core._root() / "src").resolve(strict=True)))

    from odoo import api
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
    tracked = {model_name: set() for model_name in _AUDIT_MODELS}
    env = client = None
    baseline: dict[str, int] = {}
    details: dict[str, Any] = {}
    fixture_state: dict[str, Any] = {}
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
        user = env.user
        if (
            env.uid != core._USER_ID
            or env.su
            or user.id != core._USER_ID
            or not user.active
            or user.login != core._USER_LOGIN
            or core._COMPANY_ID not in user.company_ids.ids
            or env.company.id != core._COMPANY_ID
        ):
            raise RuntimeError("the fixed business user is unavailable")
        baseline = _artifact_baseline(env)
        client = core._RuntimeClient(env)
        client.tracked = tracked
        details = _exercise(client, args.alias, args.run_id, baseline, fixture_state)
    except BaseException as exc:  # noqa: BLE001 - rollback before reporting failure
        failure = exc
    finally:
        try:
            if env is not None and baseline:
                _collect_since(env, tracked, baseline, args.run_id.hex)
        except Exception as exc:  # noqa: BLE001 - never prevent rollback
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
        core._verify_rollback(
            registry,
            tracked=tracked,
            marker=args.run_id.hex,
        )
        _verify_fixture_rollback(registry, fixture_state)
    except Exception as exc:
        raise exc from failure
    if failure is not None:
        raise failure
    assert client is not None
    print(
        json.dumps(
            {
                "alias": args.alias,
                "capabilities": sorted(_TARGET_CAPABILITIES),
                "company_id": core._COMPANY_ID,
                "database": args.database,
                "execution": "in_process_cli_real_orm",
                "fixture_email_rollback_verified": True,
                "rollback_verified": True,
                "user_id": core._USER_ID,
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
