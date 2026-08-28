"""Transactional dual-database smoke for the accounting follow-up write batch."""

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
_ALLOW_ENV = "ODACV4_ALLOW_ACCOUNTING_FOLLOWUP_WRITE_SMOKE"
_ALIASES = ("v4-dev", "v4-e2e")
_DATABASES = {
    "v4-dev": "odoo_cli_v4_dev",
    "v4-e2e": "odoo_cli_v4_e2e",
}
_COMPANY_ID = 1
_USER_ID = 5
_USER_LOGIN = "odacv4_g5_accountant"
_MANAGER_GROUP = "account.group_account_manager"
_CAPABILITIES = (
    "purchase.order.bill.create",
    "purchase_bill.lines.unmatch",
    "purchase_bill.match",
    "payment_term.create",
    "payment_term.update",
    "payment_term.lines.replace",
    "payment_term.archive",
    "payment_term.restore",
    "period.accrual.generate",
)
_PAGE_KEYS = {
    "user_id",
    "company_visible",
    "module_installed",
    "access_allowed",
    "idempotent_replay",
    "result",
}
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


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _enabled_runtime(alias: str) -> tuple[Path, dict[str, Any]]:
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
    entry = document.get("aliases", {}).get(alias)
    assert isinstance(entry, dict)
    assert entry.get("database") == _DATABASES[alias]
    users = entry.get("companies", {}).get(str(_COMPANY_ID))
    assert isinstance(users, list) and _USER_LOGIN in users
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
    executable = Path(argv[0])
    configured_runtime = Path(argv[3])
    odoo_config = Path(argv[5])
    odoo_source = Path(argv[7])
    assert executable.is_absolute() and executable.is_file()
    assert configured_runtime.resolve(strict=True) == config_path.resolve(strict=True)
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
        max(timeout, 300),
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
    assert len(completed.stdout.splitlines()) == 1
    assert json.loads(completed.stdout) == {
        "alias": alias,
        "capabilities": list(_CAPABILITIES),
        "company_id": _COMPANY_ID,
        "database": _DATABASES[alias],
        "first_results": len(_CAPABILITIES),
        "group_membership_rolled_back": True,
        "replays": len(_CAPABILITIES),
        "rollback_verified": True,
        "user_id": _USER_ID,
    }


if pytest is not None:

    @pytest.mark.integration
    @pytest.mark.parametrize("alias", _ALIASES)
    def test_accounting_followup_write_batch_rolls_back(alias: str) -> None:
        config_path, runtime = _enabled_runtime(alias)
        _run_worker(alias, uuid.uuid4(), config_path, runtime)


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


def _digest(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:32]


def _idempotency_key(
    capability_id: str, parameters: dict[str, Any], run_id: uuid.UUID
) -> str:
    if capability_id == "purchase.order.bill.create":
        return f"{capability_id}:{parameters['order_id']}"
    if capability_id in {"purchase_bill.match", "purchase_bill.lines.unmatch"}:
        target = parameters.get("pairs", parameters.get("bill_line_ids"))
        return f"{capability_id}:{parameters['bill_id']}:{_digest(target)}"
    if capability_id in {"payment_term.update", "payment_term.lines.replace"}:
        target = (
            parameters["lines"]
            if capability_id == "payment_term.lines.replace"
            else {
                key: value
                for key, value in parameters.items()
                if key != "payment_term_id"
            }
        )
        return f"{capability_id}:{parameters['payment_term_id']}:{_digest(target)}"
    if capability_id in {"payment_term.archive", "payment_term.restore"}:
        return f"{capability_id}:{parameters['payment_term_id']}"
    return f"followup-{capability_id.replace('.', '-')}-{run_id.hex}"


class _RuntimePort:
    def __init__(self, env: Any) -> None:
        self.env = env
        self.pages: list[dict[str, Any]] = []

    @property
    def user_id(self) -> int:
        return self.env.uid

    def execute(self, **payload: Any) -> dict[str, Any]:
        from odoo_accounting_cli_v4.bridge.core_writes_runtime import dispatch
        from odoo_accounting_cli_v4.bridge.runtime import RuntimeFailure

        page = dispatch(self.env, payload, payload["company_id"], RuntimeFailure)
        self.pages.append(page)
        return page


def _request(
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "request_id": str(uuid.uuid5(run_id, capability_id)),
        "context": {
            "database": alias,
            "company_id": _COMPANY_ID,
            "user_login": _USER_LOGIN,
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": parameters,
    }


def _dispatch_twice(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    from odoo_accounting_cli_v4.capabilities.core_writes import execute_core_write

    request = _request(alias, run_id, capability_id, parameters)
    key = _idempotency_key(capability_id, parameters, run_id)
    port = _RuntimePort(env)
    first = execute_core_write(port, capability_id, request, key, capability_id)
    second = execute_core_write(port, capability_id, request, key, capability_id)
    if len(port.pages) != 2:
        raise RuntimeError(f"{capability_id} did not issue two runtime writes")
    for page, replay in zip(port.pages, (False, True), strict=True):
        if (
            set(page) != _PAGE_KEYS
            or page["user_id"] != _USER_ID
            or page["company_visible"] is not True
            or page["module_installed"] is not True
            or page["access_allowed"] is not True
            or page["idempotent_replay"] is not replay
        ):
            raise RuntimeError(f"{capability_id} returned an invalid runtime page")
        result = page["result"]
        if (
            not isinstance(result, dict)
            or set(result) != _RESULT_KEYS
            or result["company_id"] != _COMPANY_ID
        ):
            raise RuntimeError(f"{capability_id} returned an invalid result")
    if first["result"] != second["result"]:
        raise RuntimeError(f"{capability_id} replay changed the result")
    return first["result"]


def _one(records: Any, label: str) -> Any:
    if len(records) != 1:
        raise RuntimeError(f"expected one {label}, got {len(records)}")
    return records


def _confirmed_purchase_order(
    admin_env: Any,
    *,
    partner_id: int,
    product_id: int,
    picking_type_id: int,
    marker: str,
    suffix: str,
) -> Any:
    product = admin_env["product.product"].browse(product_id)
    order = admin_env["purchase.order"].create(
        {
            "partner_id": partner_id,
            "company_id": _COMPANY_ID,
            "picking_type_id": picking_type_id,
            "partner_ref": f"{marker}-{suffix}",
            "order_line": [
                (
                    0,
                    0,
                    {
                        "product_id": product.id,
                        "name": f"{marker}-{suffix}-line",
                        "product_qty": 2.0,
                        "product_uom_id": product.uom_id.id,
                        "price_unit": 50.0,
                        "date_planned": "2096-09-01 00:00:00",
                    },
                )
            ],
        }
    )
    order.button_confirm()
    if order.state == "to approve":
        order.button_approve()
    if order.state != "purchase" or len(order.order_line) != 1:
        raise RuntimeError("the confirmed purchase fixture is unavailable")
    return order


def _setup_prerequisites(admin_env: Any, marker: str) -> dict[str, Any]:
    company = _one(admin_env["res.company"].browse(_COMPANY_ID).exists(), "company")
    expense = _one(
        admin_env["account.account"].search(
            [
                ("company_ids", "in", [_COMPANY_ID]),
                ("account_type", "=", "expense"),
                ("active", "=", True),
            ],
            order="id",
            limit=1,
        ),
        "expense account",
    )
    accrual = _one(
        admin_env["account.account"].search(
            [
                ("company_ids", "in", [_COMPANY_ID]),
                ("account_type", "=", "liability_current"),
                ("active", "=", True),
            ],
            order="id",
            limit=1,
        ),
        "current liability account",
    )
    journal = _one(
        admin_env["account.journal"].search(
            [
                ("company_id", "=", _COMPANY_ID),
                ("type", "=", "general"),
                ("active", "=", True),
            ],
            order="id",
            limit=1,
        ),
        "general journal",
    )
    picking_type = _one(
        admin_env["stock.picking.type"].search(
            [
                ("company_id", "=", _COMPANY_ID),
                ("code", "=", "incoming"),
                ("active", "=", True),
            ],
            order="id",
            limit=1,
        ),
        "incoming operation type",
    )
    partner = admin_env["res.partner"].create(
        {
            "name": f"{marker}-vendor",
            "company_id": _COMPANY_ID,
            "supplier_rank": 1,
        }
    )
    product = admin_env["product.product"].create(
        {
            "name": f"{marker}-service",
            "default_code": marker[:64],
            "company_id": _COMPANY_ID,
            "purchase_ok": True,
            "sale_ok": False,
            "is_storable": False,
            "purchase_method": "purchase",
            "property_account_expense_id": expense.id,
        }
    )
    bill_order = _confirmed_purchase_order(
        admin_env,
        partner_id=partner.id,
        product_id=product.id,
        picking_type_id=picking_type.id,
        marker=marker,
        suffix="bill",
    )
    accrual_order = _confirmed_purchase_order(
        admin_env,
        partner_id=partner.id,
        product_id=product.id,
        picking_type_id=picking_type.id,
        marker=marker,
        suffix="accrual",
    )
    admin_env.flush_all()
    if (
        company.id != _COMPANY_ID
        or bill_order.invoice_status != "to invoice"
        or accrual_order.state != "purchase"
    ):
        raise RuntimeError("the accounting follow-up fixture is invalid")
    return {
        "partner": partner,
        "product": product,
        "bill_order": bill_order,
        "accrual_order": accrual_order,
        "journal": journal,
        "accrual_account": accrual,
    }


def _exercise_batch(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    marker: str,
    fixture: dict[str, Any],
    artifacts: dict[str, set[int]],
) -> dict[str, set[int]]:
    artifacts.update(
        {
            "res.partner": {fixture["partner"].id},
            "product.product": {fixture["product"].id},
            "product.template": {fixture["product"].product_tmpl_id.id},
            "purchase.order": {
                fixture["bill_order"].id,
                fixture["accrual_order"].id,
            },
            "purchase.order.line": set(
                (
                    fixture["bill_order"].order_line
                    | fixture["accrual_order"].order_line
                ).ids
            ),
        }
    )

    bill_result = _dispatch_twice(
        env,
        alias,
        run_id,
        "purchase.order.bill.create",
        {"order_id": fixture["bill_order"].id},
    )
    if (
        bill_result["model"] != "account.move"
        or bill_result["state"] != "draft"
        or bill_result["move_type"] != "in_invoice"
        or bill_result["source_id"] != fixture["bill_order"].id
    ):
        raise RuntimeError("purchase.order.bill.create returned the wrong bill")
    bill = _one(env["account.move"].browse(bill_result["id"]).exists(), "vendor bill")
    bill_line = _one(
        bill.invoice_line_ids.filtered(
            lambda line: line.display_type == "product" and line.purchase_line_id
        ),
        "linked vendor-bill line",
    )
    purchase_line_id = bill_line.purchase_line_id.id
    artifacts.setdefault("account.move", set()).add(bill.id)
    artifacts.setdefault("account.move.line", set()).update(bill.line_ids.ids)

    unmatch_result = _dispatch_twice(
        env,
        alias,
        run_id,
        "purchase_bill.lines.unmatch",
        {"bill_id": bill.id, "bill_line_ids": [bill_line.id]},
    )
    bill_line.invalidate_recordset(["purchase_line_id"])
    if bill_line.purchase_line_id or unmatch_result["line_ids"] != [bill_line.id]:
        raise RuntimeError("purchase_bill.lines.unmatch did not clear the link")

    match_result = _dispatch_twice(
        env,
        alias,
        run_id,
        "purchase_bill.match",
        {
            "bill_id": bill.id,
            "pairs": [
                {
                    "bill_line_id": bill_line.id,
                    "purchase_line_id": purchase_line_id,
                }
            ],
        },
    )
    bill_line.invalidate_recordset(["purchase_line_id"])
    if bill_line.purchase_line_id.id != purchase_line_id or match_result[
        "line_ids"
    ] != [bill_line.id]:
        raise RuntimeError("purchase_bill.match did not restore the native link")

    term_result = _dispatch_twice(
        env,
        alias,
        run_id,
        "payment_term.create",
        {
            "name": f"{marker}-term",
            "company_id": _COMPANY_ID,
            "sequence": 10,
            "note": "<p>Created by the isolated CLI smoke</p>",
            "display_on_invoice": True,
            "early_discount": False,
            "lines": [
                {
                    "value": "percent",
                    "value_amount": "100",
                    "delay_type": "days_after",
                    "nb_days": 0,
                }
            ],
        },
    )
    term_id = term_result["id"]
    term = _one(
        env["account.payment.term"]
        .with_context(active_test=False)
        .browse(term_id)
        .exists(),
        "payment term",
    )
    artifacts.setdefault("account.payment.term", set()).add(term.id)
    artifacts.setdefault("account.payment.term.line", set()).update(term.line_ids.ids)

    _dispatch_twice(
        env,
        alias,
        run_id,
        "payment_term.update",
        {"payment_term_id": term.id, "sequence": 17, "display_on_invoice": False},
    )
    term.invalidate_recordset(["sequence", "display_on_invoice", "note"])
    if (
        term.sequence != 17
        or term.display_on_invoice
        or "Created by the isolated CLI smoke" not in (term.note or "")
    ):
        raise RuntimeError("payment_term.update changed the wrong header fields")

    replaced = _dispatch_twice(
        env,
        alias,
        run_id,
        "payment_term.lines.replace",
        {
            "payment_term_id": term.id,
            "lines": [
                {
                    "value": "percent",
                    "value_amount": "40",
                    "delay_type": "days_after",
                    "nb_days": 30,
                },
                {
                    "value": "percent",
                    "value_amount": "60",
                    "delay_type": "days_after_end_of_month",
                    "nb_days": 15,
                },
            ],
        },
    )
    term.invalidate_recordset(["line_ids"])
    if len(term.line_ids) != 2 or replaced["line_ids"] != sorted(term.line_ids.ids):
        raise RuntimeError("payment_term.lines.replace did not persist exact lines")
    artifacts["account.payment.term.line"].update(term.line_ids.ids)

    archived = _dispatch_twice(
        env,
        alias,
        run_id,
        "payment_term.archive",
        {"payment_term_id": term.id},
    )
    restored = _dispatch_twice(
        env,
        alias,
        run_id,
        "payment_term.restore",
        {"payment_term_id": term.id},
    )
    if archived["state"] != "archived" or restored["state"] != "active":
        raise RuntimeError("payment-term archive/restore returned the wrong state")

    from dateutil.relativedelta import relativedelta
    from odoo import fields

    today = fields.Date.today()
    accrual_date = str(today - relativedelta(days=2))
    reversal_date = str(today - relativedelta(days=1))
    accrual_result = _dispatch_twice(
        env,
        alias,
        run_id,
        "period.accrual.generate",
        {
            "source_model": "purchase.order",
            "order_ids": [fixture["accrual_order"].id],
            "date": accrual_date,
            "reversal_date": reversal_date,
            "journal_id": fixture["journal"].id,
            "accrual_account_id": fixture["accrual_account"].id,
            "amount": "125",
        },
    )
    primary = _one(
        env["account.move"].browse(accrual_result["id"]).exists(), "accrual move"
    )
    reversal = _one(
        env["account.move"].browse(accrual_result["source_id"]).exists(),
        "accrual reversal move",
    )
    if (
        primary.state != "posted"
        or reversal.state != "posted"
        or str(primary.date) != accrual_date
        or str(reversal.date) != reversal_date
        or primary.company_id.id != _COMPANY_ID
        or reversal.company_id.id != _COMPANY_ID
    ):
        raise RuntimeError("period.accrual.generate returned an invalid move pair")
    artifacts["account.move"].update((primary | reversal).ids)
    artifacts["account.move.line"].update((primary | reversal).line_ids.ids)
    return artifacts


def _verify_rollback(
    registry: Any,
    marker: str,
    artifacts: dict[str, set[int]],
    baseline_manager: bool,
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
            model: env[model].search_count([("id", "in", sorted(ids))], limit=1)
            for model, ids in artifacts.items()
            if ids
        }
        remaining["partner_marker"] = env["res.partner"].search_count(
            [("name", "ilike", marker)], limit=1
        )
        remaining["product_marker"] = env["product.template"].search_count(
            [("name", "ilike", marker)], limit=1
        )
        remaining["purchase_marker"] = env["purchase.order"].search_count(
            [("partner_ref", "ilike", marker)], limit=1
        )
        remaining["payment_term_marker"] = env["account.payment.term"].search_count(
            [("name", "ilike", marker)], limit=1
        )
        if any(remaining.values()):
            raise RuntimeError(f"rollback residue detected: {remaining}")
        manager_id = env.ref(_MANAGER_GROUP).id
        cursor.execute(
            "SELECT 1 FROM res_groups_users_rel WHERE uid = %s AND gid = %s",
            [_USER_ID, manager_id],
        )
        if (cursor.fetchone() is not None) != baseline_manager:
            raise RuntimeError(
                "temporary accounting-manager membership was not rolled back"
            )
    finally:
        cursor.rollback()
        cursor.close()


def _live_worker(argv: list[str] | None = None) -> int:
    args = _arguments(argv)
    sys.path.insert(0, str(args.odoo_source.resolve(strict=True)))
    sys.path.insert(0, str((_root() / "src").resolve(strict=True)))

    from odoo import SUPERUSER_ID, Command, api
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
    marker = f"ODACV4-ACCOUNTING-FOLLOWUP-{args.alias}-{args.run_id.hex}"
    artifacts: dict[str, set[int]] = {}
    baseline_manager: bool | None = None
    failure: Exception | None = None
    try:
        context = {
            "allowed_company_ids": [_COMPANY_ID],
            "active_test": False,
            "lang": "en_US",
            "tz": "Asia/Shanghai",
            "mail_create_nosubscribe": True,
            "tracking_disable": True,
            "mail_notrack": True,
        }
        admin_env = api.Environment(cursor, SUPERUSER_ID, context)
        user = _one(admin_env["res.users"].browse(_USER_ID).exists(), "business user")
        if (
            user.login != _USER_LOGIN
            or not user.active
            or _COMPANY_ID not in user.company_ids.ids
        ):
            raise RuntimeError("the configured business user is unavailable")
        manager = admin_env.ref(_MANAGER_GROUP)
        cursor.execute(
            "SELECT 1 FROM res_groups_users_rel WHERE uid = %s AND gid = %s",
            [_USER_ID, manager.id],
        )
        baseline_manager = cursor.fetchone() is not None
        if not user.has_group(_MANAGER_GROUP):
            user.write({"group_ids": [Command.link(manager.id)]})
            admin_env.flush_all()

        fixture = _setup_prerequisites(admin_env, marker)
        business_env = api.Environment(
            cursor,
            _USER_ID,
            {**context, "active_test": True},
        )
        if (
            business_env.uid != _USER_ID
            or business_env.user.login != _USER_LOGIN
            or not business_env.user.has_group(_MANAGER_GROUP)
        ):
            raise RuntimeError("uid 5 or its temporary manager group is unavailable")
        _exercise_batch(
            business_env,
            args.alias,
            args.run_id,
            marker,
            fixture,
            artifacts,
        )
    except Exception as exc:  # noqa: BLE001 - rollback must cover all Odoo failures.
        failure = exc
    finally:
        cursor.rollback()
        cursor.close()

    if baseline_manager is not None:
        _verify_rollback(registry, marker, artifacts, baseline_manager)
    if failure is not None:
        raise failure
    if baseline_manager is None:
        raise RuntimeError("the live fixture was not initialized")
    sys.stdout.write(
        json.dumps(
            {
                "alias": args.alias,
                "capabilities": list(_CAPABILITIES),
                "company_id": _COMPANY_ID,
                "database": args.database,
                "first_results": len(_CAPABILITIES),
                "group_membership_rolled_back": True,
                "replays": len(_CAPABILITIES),
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
