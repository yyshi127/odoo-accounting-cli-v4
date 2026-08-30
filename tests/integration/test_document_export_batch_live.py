"""Rollback-only dual-database smoke for ten fixed document PDF exports."""

from __future__ import annotations

import argparse
import base64
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
_ALLOW_ENV = "ODACV4_ALLOW_DOCUMENT_EXPORT_SMOKE"
_ALIASES = ("v4-dev", "v4-e2e")
_DATABASES = {
    "v4-dev": "odoo_cli_v4_dev",
    "v4-e2e": "odoo_cli_v4_e2e",
}
_COMPANY_ID = 1
_USER_ID = 5
_USER_LOGIN = "odacv4_g5_accountant"
_GROUPS = (
    "account.group_account_user",
    "sales_team.group_sale_salesman",
    "purchase.group_purchase_user",
    "stock.group_stock_user",
)
_CAPABILITIES = (
    "invoice.pdf.export",
    "payment.receipt.pdf.export",
    "bank.statement.pdf.export",
    "sale.order.pdf.export",
    "purchase.order.pdf.export",
    "purchase.rfq.pdf.export",
    "stock.delivery_slip.pdf.export",
    "stock.picking_operations.pdf.export",
    "stock.return_slip.pdf.export",
    "localization.china.voucher.render",
)


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _enabled_runtime(alias: str) -> tuple[Path, dict[str, Any]]:
    assert pytest is not None
    if os.environ.get(_ALLOW_ENV) != "1":
        pytest.skip(f"set {_ALLOW_ENV}=1 to authorize rollback fixture setup")
    raw = os.environ.get(_CONFIG_ENV)
    if not raw:
        pytest.skip(f"{_CONFIG_ENV} is not configured")
    path = Path(raw)
    if not path.is_file():
        pytest.skip(f"{_CONFIG_ENV} does not name an existing file")
    runtime = json.loads(path.read_text(encoding="utf-8"))
    entry = runtime.get("aliases", {}).get(alias)
    assert isinstance(entry, dict) and entry.get("database") == _DATABASES[alias]
    users = entry.get("companies", {}).get(str(_COMPANY_ID))
    assert isinstance(users, list) and _USER_LOGIN in users
    return path, runtime


def _worker_command(
    alias: str, run_id: uuid.UUID, config_path: Path, runtime: dict[str, Any]
) -> tuple[list[str], int]:
    bridge = runtime.get("bridge")
    assert isinstance(bridge, dict) and set(bridge) == {"argv", "timeout_seconds"}
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
        max(timeout, 600),
    )


def _run_worker(
    alias: str, run_id: uuid.UUID, config_path: Path, runtime: dict[str, Any]
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
        "attachments_unchanged": True,
        "capabilities": list(_CAPABILITIES),
        "company_id": _COMPANY_ID,
        "database": _DATABASES[alias],
        "exports": len(_CAPABILITIES),
        "group_membership_rolled_back": True,
        "rollback_verified": True,
        "user_id": _USER_ID,
    }


if pytest is not None:

    @pytest.mark.integration
    @pytest.mark.parametrize("alias", _ALIASES)
    def test_document_export_batch_rolls_back_real_fixtures(alias: str) -> None:
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


def _one(records: Any, label: str) -> Any:
    if len(records) != 1:
        raise RuntimeError(f"expected one {label}, got {len(records)}")
    return records


def _record(artifacts: dict[str, set[int]], model: str, records: Any) -> None:
    artifacts.setdefault(model, set()).update(records.ids)


class _DirectClient:
    def __init__(self, env: Any, company_id: int) -> None:
        self.env = env
        self.company_id = company_id
        self.pages: list[dict[str, Any]] = []

    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        from odoo_accounting_cli_v4.bridge.runtime import _dispatch

        page = _dispatch(self.env, action, payload, self.company_id)
        self.pages.append(page)
        return page


def _request(
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    id_parameter: str,
    target_id: int,
) -> dict[str, Any]:
    parameters: dict[str, Any] = {id_parameter: target_id}
    if capability_id == "invoice.pdf.export":
        parameters["layout"] = "with_payments"
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


def _account(env: Any, account_type: str) -> Any:
    return _one(
        env["account.account"].search(
            [
                ("company_ids", "in", [_COMPANY_ID]),
                ("account_type", "=", account_type),
                ("active", "=", True),
            ],
            order="id",
            limit=1,
        ),
        f"{account_type} account",
    )


def _journal(env: Any, journal_type: str) -> Any:
    return _one(
        env["account.journal"].search(
            [
                ("company_id", "=", _COMPANY_ID),
                ("type", "=", journal_type),
                ("active", "=", True),
            ],
            order="id",
            limit=1,
        ),
        f"{journal_type} journal",
    )


def _setup_fixture(admin_env: Any, marker: str) -> dict[str, Any]:
    from odoo import Command, fields

    company = _one(admin_env["res.company"].browse(_COMPANY_ID).exists(), "company")
    fiscal_country = company.account_fiscal_country_id
    if (
        not fiscal_country
        or fiscal_country.code != "CN"
        or company.chart_template != "cn_oscg"
    ):
        raise RuntimeError(
            "company 1 is not a CN/cn_oscg fixture for the native voucher report"
        )
    pricelist = _one(
        admin_env["product.pricelist"].search(
            [
                ("currency_id", "=", company.currency_id.id),
                ("company_id", "in", [False, _COMPANY_ID]),
                ("active", "=", True),
            ],
            order="id",
            limit=1,
        ),
        "company pricelist",
    )
    incoming = _one(
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
    outgoing = _one(
        admin_env["stock.picking.type"].search(
            [
                ("company_id", "=", _COMPANY_ID),
                ("code", "=", "outgoing"),
                ("active", "=", True),
            ],
            order="id",
            limit=1,
        ),
        "outgoing operation type",
    )
    bank = _journal(admin_env, "bank")
    inbound_method = _one(
        admin_env["account.payment.method.line"].search(
            [
                ("journal_id", "=", bank.id),
                ("payment_type", "=", "inbound"),
                ("payment_method_id.code", "=", "manual"),
            ],
            order="id",
            limit=1,
        ),
        "manual inbound payment method line",
    )
    if not inbound_method.payment_account_id:
        raise RuntimeError("the inbound payment method has no outstanding account")

    orphan_line = _one(
        admin_env["account.bank.statement.line"].search(
            [
                ("company_id", "=", _COMPANY_ID),
                ("statement_id", "=", False),
                ("state", "=", "posted"),
                ("date", "!=", False),
            ],
            order="id",
            limit=1,
        ),
        "orphan posted bank transaction",
    )
    partner = admin_env["res.partner"].create(
        {
            "name": marker,
            "company_id": _COMPANY_ID,
            "customer_rank": 1,
            "supplier_rank": 1,
        }
    )
    product = admin_env["product.product"].create(
        {
            "name": marker,
            "default_code": marker[:64],
            "company_id": _COMPANY_ID,
            "sale_ok": True,
            "purchase_ok": True,
        }
    )
    sale_order = admin_env["sale.order"].create(
        {
            "partner_id": partner.id,
            "company_id": _COMPANY_ID,
            "pricelist_id": pricelist.id,
            "user_id": _USER_ID,
            "client_order_ref": marker,
            "order_line": [
                Command.create(
                    {
                        "product_id": product.id,
                        "name": marker,
                        "product_uom_qty": 1.0,
                        "product_uom_id": product.uom_id.id,
                        "price_unit": 10.0,
                        "tax_ids": [Command.clear()],
                    }
                )
            ],
        }
    )

    def purchase_order(reference: str) -> Any:
        return admin_env["purchase.order"].create(
            {
                "partner_id": partner.id,
                "company_id": _COMPANY_ID,
                "currency_id": company.currency_id.id,
                "user_id": _USER_ID,
                "picking_type_id": incoming.id,
                "partner_ref": reference,
                "order_line": [
                    Command.create(
                        {
                            "product_id": product.id,
                            "name": marker,
                            "product_qty": 1.0,
                            "product_uom_id": product.uom_id.id,
                            "price_unit": 8.0,
                            "date_planned": fields.Datetime.now(),
                            "tax_ids": [Command.clear()],
                        }
                    )
                ],
            }
        )

    purchase = purchase_order(f"PO-{marker}")
    rfq = purchase_order(f"RFQ-{marker}")
    purchase.button_confirm()

    invoice = admin_env["account.move"].create(
        {
            "move_type": "out_invoice",
            "company_id": _COMPANY_ID,
            "journal_id": _journal(admin_env, "sale").id,
            "partner_id": partner.id,
            "invoice_date": fields.Date.context_today(admin_env.user),
            "ref": marker,
            "invoice_line_ids": [
                Command.create(
                    {
                        "name": marker,
                        "account_id": _account(admin_env, "income").id,
                        "quantity": 1.0,
                        "price_unit": 10.0,
                        "tax_ids": [Command.clear()],
                    }
                )
            ],
        }
    )
    voucher = admin_env["account.move"].create(
        {
            "move_type": "entry",
            "company_id": _COMPANY_ID,
            "journal_id": _journal(admin_env, "general").id,
            "date": fields.Date.context_today(admin_env.user),
            "ref": marker,
            "line_ids": [
                Command.create(
                    {
                        "name": marker,
                        "account_id": _account(admin_env, "asset_current").id,
                        "debit": 1.0,
                        "credit": 0.0,
                    }
                ),
                Command.create(
                    {
                        "name": marker,
                        "account_id": _account(admin_env, "expense").id,
                        "debit": 0.0,
                        "credit": 1.0,
                    }
                ),
            ],
        }
    )
    voucher.action_post()
    payment = admin_env["account.payment"].create(
        {
            "company_id": _COMPANY_ID,
            "journal_id": bank.id,
            "payment_method_line_id": inbound_method.id,
            "payment_type": "inbound",
            "partner_type": "customer",
            "partner_id": partner.id,
            "amount": 11.0,
            "currency_id": company.currency_id.id,
            "date": fields.Date.context_today(admin_env.user),
            "memo": marker,
        }
    )
    payment.action_post()

    statement_model = admin_env["account.bank.statement"].with_context(
        active_ids=[orphan_line.id],
        st_line_id=orphan_line.id,
        skip_pdf_attachment_generation=True,
    )
    line_commands = statement_model.default_get(["line_ids"]).get("line_ids")
    if not line_commands:
        raise RuntimeError("the statement context did not select its orphan line")
    statement = statement_model.create({"reference": marker, "line_ids": line_commands})
    picking = admin_env["stock.picking"].create(
        {
            "picking_type_id": outgoing.id,
            "location_id": outgoing.default_location_src_id.id,
            "location_dest_id": outgoing.default_location_dest_id.id,
            "partner_id": partner.id,
            "company_id": _COMPANY_ID,
            "origin": marker,
        }
    )
    admin_env["stock.move"].create(
        {
            "description_picking": marker,
            "product_id": product.id,
            "product_uom_qty": 1.0,
            "product_uom": product.uom_id.id,
            "location_id": outgoing.default_location_src_id.id,
            "location_dest_id": outgoing.default_location_dest_id.id,
            "picking_id": picking.id,
            "company_id": _COMPANY_ID,
        }
    )
    admin_env.flush_all()
    if (
        sale_order.state != "draft"
        or purchase.state != "purchase"
        or rfq.state not in {"draft", "sent"}
        or invoice.state != "draft"
        or voucher.state != "posted"
        or payment.state not in {"in_process", "paid"}
        or statement.line_ids != orphan_line
        or picking.state != "draft"
        or picking.picking_type_code != "outgoing"
    ):
        raise RuntimeError("the fixed-document export fixture is invalid")
    return {
        "partner": partner,
        "product": product,
        "sale_order": sale_order,
        "purchase": purchase,
        "rfq": rfq,
        "invoice": invoice,
        "voucher": voucher,
        "payment": payment,
        "statement": statement,
        "orphan_line": orphan_line,
        "picking": picking,
    }


def _targets(fixture: dict[str, Any]) -> dict[str, tuple[str, int]]:
    return {
        "invoice.pdf.export": ("move_id", fixture["invoice"].id),
        "payment.receipt.pdf.export": ("payment_id", fixture["payment"].id),
        "bank.statement.pdf.export": ("statement_id", fixture["statement"].id),
        "sale.order.pdf.export": ("order_id", fixture["sale_order"].id),
        "purchase.order.pdf.export": ("order_id", fixture["purchase"].id),
        "purchase.rfq.pdf.export": ("order_id", fixture["rfq"].id),
        "stock.delivery_slip.pdf.export": ("transfer_id", fixture["picking"].id),
        "stock.picking_operations.pdf.export": (
            "transfer_id",
            fixture["picking"].id,
        ),
        "stock.return_slip.pdf.export": ("transfer_id", fixture["picking"].id),
        "localization.china.voucher.render": ("move_id", fixture["voucher"].id),
    }


def _attachment_counts(env: Any, targets: dict[str, tuple[str, int]]) -> dict:
    from odoo_accounting_cli_v4.capabilities.document_exports import (
        DOCUMENT_EXPORT_SPECS,
    )

    return {
        capability_id: env["ir.attachment"].search_count(
            [
                ("res_model", "=", DOCUMENT_EXPORT_SPECS[capability_id]["model"]),
                ("res_id", "=", target_id),
            ]
        )
        for capability_id, (_, target_id) in targets.items()
    }


def _exercise(
    env: Any,
    admin_env: Any,
    alias: str,
    run_id: uuid.UUID,
    fixture: dict[str, Any],
) -> None:
    from odoo_accounting_cli_v4.bridge.document_exports import (
        OdooDocumentExportPort,
    )
    from odoo_accounting_cli_v4.capabilities.document_exports import export_document

    targets = _targets(fixture)
    before = _attachment_counts(admin_env, targets)
    client = _DirectClient(env, _COMPANY_ID)
    failures: list[str] = []
    for capability_id in _CAPABILITIES:
        id_parameter, target_id = targets[capability_id]
        port = OdooDocumentExportPort(client)
        try:
            data = export_document(
                capability_id,
                port,
                _request(alias, run_id, capability_id, id_parameter, target_id),
            )
        except Exception as exc:  # noqa: BLE001 - exercise every live report.
            failures.append(f"{capability_id}: {type(exc).__name__}: {exc}")
            continue
        page = client.pages[-1]
        content = base64.b64decode(data["content_base64"], validate=True)
        if (
            set(data)
            != {
                "filename",
                "format",
                "mimetype",
                "byte_count",
                "sha256",
                "content_base64",
            }
            or port.user_id != _USER_ID
            or page["user_id"] != _USER_ID
            or not all(
                page[key]
                for key in (
                    "company_visible",
                    "module_installed",
                    "access_allowed",
                    "record_visible",
                    "applicable",
                )
            )
            or data["format"] != "pdf"
            or data["mimetype"] != "application/pdf"
            or data["byte_count"] != len(content)
            or data["sha256"] != hashlib.sha256(content).hexdigest()
            or not content.startswith(b"%PDF-")
        ):
            raise RuntimeError(f"{capability_id} returned an invalid live PDF")
    admin_env.flush_all()
    if _attachment_counts(admin_env, targets) != before:
        raise RuntimeError("document exports created report attachments")
    if failures:
        raise RuntimeError("document exports failed:\n" + "\n".join(failures))


def _capture_artifacts(
    env: Any, fixture: dict[str, Any], artifacts: dict[str, set[int]]
) -> None:
    _record(artifacts, "res.partner", fixture["partner"])
    _record(artifacts, "product.product", fixture["product"])
    _record(artifacts, "product.template", fixture["product"].product_tmpl_id)
    for key in ("sale_order",):
        _record(artifacts, "sale.order", fixture[key])
        _record(artifacts, "sale.order.line", fixture[key].order_line)
    for key in ("purchase", "rfq"):
        order = fixture[key]
        _record(artifacts, "purchase.order", order)
        _record(artifacts, "purchase.order.line", order.order_line)
        _record(artifacts, "stock.picking", order.picking_ids)
        _record(artifacts, "stock.move", order.picking_ids.move_ids)
    _record(artifacts, "stock.picking", fixture["picking"])
    _record(artifacts, "stock.move", fixture["picking"].move_ids)
    _record(artifacts, "account.bank.statement", fixture["statement"])
    _record(artifacts, "account.payment", fixture["payment"])
    moves = fixture["invoice"] | fixture["voucher"] | fixture["payment"].move_id
    _record(artifacts, "account.move", moves)
    _record(artifacts, "account.move.line", moves.line_ids)
    env.flush_all()


def _verify_rollback(
    registry: Any,
    marker: str,
    artifacts: dict[str, set[int]],
    baseline_groups: dict[str, bool],
    orphan_line_id: int,
) -> None:
    from odoo import SUPERUSER_ID, api

    cursor = registry.cursor()
    try:
        env = api.Environment(
            cursor,
            SUPERUSER_ID,
            {"allowed_company_ids": [_COMPANY_ID], "active_test": False},
        )
        survivors = {
            model: env[model].search_count([("id", "in", sorted(ids))], limit=1)
            for model, ids in artifacts.items()
            if ids and model in env.registry.models
        }
        marker_survivors = {
            "partner": env["res.partner"].search_count(
                [("name", "=", marker)], limit=1
            ),
            "product": env["product.template"].search_count(
                [("name", "=", marker)], limit=1
            ),
            "sale": env["sale.order"].search_count(
                [("client_order_ref", "=", marker)], limit=1
            ),
            "purchase": env["purchase.order"].search_count(
                [("partner_ref", "ilike", marker)], limit=1
            ),
            "moves": env["account.move"].search_count([("ref", "=", marker)], limit=1),
            "payments": env["account.payment"].search_count(
                [("memo", "=", marker)], limit=1
            ),
            "statement": env["account.bank.statement"].search_count(
                [("reference", "=", marker)], limit=1
            ),
            "picking": env["stock.picking"].search_count(
                [("origin", "=", marker)], limit=1
            ),
        }
        orphan_line = env["account.bank.statement.line"].browse(orphan_line_id).exists()
        if (
            any(survivors.values())
            or any(marker_survivors.values())
            or not orphan_line
            or orphan_line.statement_id
        ):
            raise RuntimeError(
                "document-export fixtures survived rollback: "
                f"ids={survivors}, markers={marker_survivors}"
            )
        group_ids = {group: env.ref(group).id for group in _GROUPS}
        cursor.execute(
            "SELECT gid FROM res_groups_users_rel WHERE uid = %s AND gid IN %s",
            [_USER_ID, tuple(group_ids.values())],
        )
        direct_groups = {row[0] for row in cursor.fetchall()}
        rolled_back = {
            group: group_id in direct_groups for group, group_id in group_ids.items()
        }
        if rolled_back != baseline_groups:
            raise RuntimeError("temporary standard groups survived rollback")
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
    marker = f"ODACV4-DOC-EXPORT-{args.alias}-{args.run_id.hex}"
    artifacts: dict[str, set[int]] = {}
    baseline_groups: dict[str, bool] | None = None
    fixture: dict[str, Any] | None = None
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
        company = admin_env["res.company"].browse(_COMPANY_ID).exists()
        user = admin_env["res.users"].browse(_USER_ID).exists()
        if (
            not company
            or not user
            or user.login != _USER_LOGIN
            or not user.active
            or company not in user.company_ids
        ):
            raise RuntimeError("the configured company or mapped user is unavailable")
        group_ids = {group: admin_env.ref(group).id for group in _GROUPS}
        cursor.execute(
            "SELECT gid FROM res_groups_users_rel WHERE uid = %s AND gid IN %s",
            [_USER_ID, tuple(group_ids.values())],
        )
        direct_groups = {row[0] for row in cursor.fetchall()}
        baseline_groups = {
            group: group_id in direct_groups for group, group_id in group_ids.items()
        }
        missing = [
            group_id
            for group, group_id in group_ids.items()
            if not user.has_group(group)
        ]
        if missing:
            user.write({"group_ids": [Command.link(group_id) for group_id in missing]})
            admin_env.flush_all()

        fixture = _setup_fixture(admin_env, marker)
        business_env = api.Environment(
            cursor, _USER_ID, {**context, "active_test": True}
        )
        if (
            business_env.uid != _USER_ID
            or business_env.user.login != _USER_LOGIN
            or not all(business_env.user.has_group(group) for group in _GROUPS)
        ):
            raise RuntimeError("uid 5 or its temporary standard groups are unavailable")
        _exercise(business_env, admin_env, args.alias, args.run_id, fixture)
        _capture_artifacts(admin_env, fixture, artifacts)
    except Exception as exc:  # noqa: BLE001 - rollback must cover every Odoo failure.
        failure = exc
    finally:
        cursor.rollback()
        cursor.close()

    if baseline_groups is not None and fixture is not None:
        _verify_rollback(
            registry,
            marker,
            artifacts,
            baseline_groups,
            fixture["orphan_line"].id,
        )
    if failure is not None:
        raise failure
    if fixture is None or baseline_groups is None:
        raise RuntimeError("the document-export fixture was not fully exercised")
    sys.stdout.write(
        json.dumps(
            {
                "alias": args.alias,
                "attachments_unchanged": True,
                "capabilities": list(_CAPABILITIES),
                "company_id": _COMPANY_ID,
                "database": args.database,
                "exports": len(_CAPABILITIES),
                "group_membership_rolled_back": True,
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
