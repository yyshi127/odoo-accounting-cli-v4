"""Rollback-only dual-database smoke for sales invoicing and stock transfers.

The administrator creates prerequisites and grants only the standard sales and
stock groups inside one outer transaction.  All eight capabilities dispatch as
uid 5, replay immediately, and the transaction is rolled back.  Odoo's native
sales-order invoicing method internally creates the invoice with sudo by design.
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
_ALLOW_ENV = "ODACV4_ALLOW_STOCK_TRANSFER_WRITE_SMOKE"
_ALIASES = ("v4-dev", "v4-e2e")
_DATABASES = {
    "v4-dev": "odoo_cli_v4_dev",
    "v4-e2e": "odoo_cli_v4_e2e",
}
_COMPANY_ID = 1
_USER_ID = 5
_USER_LOGIN = "odacv4_g5_accountant"
_GROUPS = (
    "sales_team.group_sale_salesman",
    "stock.group_stock_user",
)
_CAPABILITIES = (
    "sale.order.invoice.create",
    "stock.transfer.create",
    "stock.transfer.confirm",
    "stock.transfer.assign",
    "stock.transfer.quantities.set",
    "stock.transfer.validate",
    "stock.transfer.unreserve",
    "stock.transfer.cancel",
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
        max(timeout, 300),
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
        "backorders_created": 1,
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
    def test_stock_transfer_write_batch_rolls_back_real_chains(alias: str) -> None:
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


def _key(capability_id: str, parameters: dict[str, Any], run_id: uuid.UUID) -> str:
    if capability_id == "stock.transfer.create":
        return f"stock-transfer-create-{run_id.hex}"
    if capability_id == "sale.order.invoice.create":
        return f"{capability_id}:{parameters['order_id']}"
    if capability_id == "stock.transfer.quantities.set":
        return f"{capability_id}:{parameters['transfer_id']}:{_digest(parameters['lines'])}"
    if capability_id == "stock.transfer.validate":
        return (
            f"{capability_id}:{parameters['transfer_id']}:"
            f"{parameters['backorder_policy']}"
        )
    return f"{capability_id}:{parameters['transfer_id']}"


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
    *,
    model: str,
    states: set[str],
    source_id: int,
) -> dict[str, Any]:
    from odoo_accounting_cli_v4.capabilities.core_writes import execute_core_write

    request = _request(alias, run_id, capability_id, parameters)
    port = _RuntimePort(env)
    key = _key(capability_id, parameters, run_id)
    first = execute_core_write(port, capability_id, request, key, capability_id)
    second = execute_core_write(port, capability_id, request, key, capability_id)
    if len(port.pages) != 2:
        raise RuntimeError(f"{capability_id} did not execute twice")
    for index, page in enumerate(port.pages):
        if set(page) != _PAGE_KEYS:
            raise RuntimeError(f"{capability_id} returned an invalid runtime page")
        result = page["result"]
        if (
            page["user_id"] != _USER_ID
            or not page["company_visible"]
            or not page["module_installed"]
            or not page["access_allowed"]
            or page["idempotent_replay"] is not bool(index)
            or not isinstance(result, dict)
            or set(result) != _RESULT_KEYS
            or result["model"] != model
            or not isinstance(result["id"], int)
            or result["id"] <= 0
            or (
                model == "stock.picking"
                and (not isinstance(result["name"], str) or not result["name"])
            )
            or result["state"] not in states
            or result["company_id"] != _COMPANY_ID
            or result["move_type"]
            != ("out_invoice" if model == "account.move" else None)
            or result["source_id"] != source_id
            or not result["line_ids"]
            or result["partial_reconcile_ids"]
            or result["full_reconcile_id"] is not None
            or result["reconciled"]
        ):
            raise RuntimeError(f"{capability_id} returned a mismatched result")
    if first["idempotent_replay"] or not second["idempotent_replay"]:
        raise RuntimeError(f"{capability_id} replay flags are invalid")
    if first["result"] != second["result"]:
        raise RuntimeError(f"{capability_id} replay changed the result")
    return first["result"]


def _record(artifacts: dict[str, set[int]], model: str, records: Any) -> None:
    artifacts.setdefault(model, set()).update(records.ids)


def _one(records: Any, label: str) -> Any:
    if len(records) != 1:
        raise RuntimeError(f"expected one {label}, got {len(records)}")
    return records


def _setup_fixture(admin_env: Any, marker: str) -> dict[str, Any]:
    company = admin_env["res.company"].browse(_COMPANY_ID).exists()
    picking_type = admin_env["stock.picking.type"].search(
        [
            ("company_id", "=", _COMPANY_ID),
            ("code", "=", "outgoing"),
            ("active", "=", True),
            ("default_location_src_id", "!=", False),
            ("default_location_dest_id", "!=", False),
            ("default_location_src_id.usage", "=", "internal"),
        ],
        order="id",
        limit=1,
    )
    pricelist = admin_env["product.pricelist"].search(
        [
            ("currency_id", "=", company.currency_id.id),
            ("company_id", "in", [False, _COMPANY_ID]),
            ("active", "=", True),
        ],
        order="id",
        limit=1,
    )
    income_account = admin_env["account.account"].search(
        [
            ("company_ids", "in", [_COMPANY_ID]),
            ("account_type", "=", "income"),
            ("active", "=", True),
        ],
        order="id",
        limit=1,
    )
    category = admin_env["product.category"].search([], order="id", limit=1)
    if (
        not company
        or not picking_type
        or not pricelist
        or not income_account
        or not category
    ):
        raise RuntimeError("stock-transfer prerequisites are unavailable")
    picking_type_before = {
        "reservation_method": picking_type.reservation_method,
        "create_backorder": picking_type.create_backorder,
    }
    picking_type.write({"reservation_method": "manual", "create_backorder": "ask"})

    partner = admin_env["res.partner"].create(
        {
            "name": marker,
            "company_id": _COMPANY_ID,
            "customer_rank": 1,
        }
    )
    product = admin_env["product.product"].create(
        {
            "name": marker,
            "default_code": marker[:64],
            "is_storable": True,
            "tracking": "none",
            "company_id": _COMPANY_ID,
            "categ_id": category.id,
            "sale_ok": True,
            "invoice_policy": "order",
            "property_account_income_id": income_account.id,
        }
    )
    source = picking_type.default_location_src_id
    destination = picking_type.default_location_dest_id
    admin_env["stock.quant"]._update_available_quantity(product, source, 20.0)

    sale_order = admin_env["sale.order"].create(
        {
            "partner_id": partner.id,
            "company_id": _COMPANY_ID,
            "user_id": _USER_ID,
            "pricelist_id": pricelist.id,
            "client_order_ref": marker,
            "order_line": [
                (
                    0,
                    0,
                    {
                        "product_id": product.id,
                        "name": marker,
                        "product_uom_qty": 2.0,
                        "product_uom_id": product.uom_id.id,
                        "price_unit": 10.0,
                        "tax_ids": [(5, 0, 0)],
                    },
                )
            ],
        }
    )
    sale_order.action_confirm()

    reserved = admin_env["stock.picking"].create(
        {
            "picking_type_id": picking_type.id,
            "location_id": source.id,
            "location_dest_id": destination.id,
            "partner_id": partner.id,
            "company_id": _COMPANY_ID,
            "origin": f"{marker}-reserved",
        }
    )
    admin_env["stock.move"].create(
        {
            "description_picking": f"{marker}-reserved",
            "product_id": product.id,
            "product_uom_qty": 3.0,
            "product_uom": product.uom_id.id,
            "location_id": source.id,
            "location_dest_id": destination.id,
            "picking_id": reserved.id,
            "company_id": _COMPANY_ID,
        }
    )
    reserved.action_confirm()
    reserved.action_assign()
    admin_env.flush_all()
    reserved_move_line_ids = set(reserved.move_line_ids.ids)
    quant = admin_env["stock.quant"].search(
        [
            ("product_id", "=", product.id),
            ("location_id", "=", source.id),
            ("company_id", "=", _COMPANY_ID),
        ],
        order="id",
        limit=1,
    )
    sale_order.invalidate_recordset(["state", "invoice_status", "picking_ids"])
    if (
        product.tracking != "none"
        or not product.is_storable
        or product.property_account_income_id != income_account
        or sale_order.state != "sale"
        or sale_order.user_id.id != _USER_ID
        or sale_order.invoice_status != "to invoice"
        or reserved.state != "assigned"
        or not reserved.move_line_ids
        or not quant
        or quant.quantity < 20.0
        or picking_type.reservation_method != "manual"
        or picking_type.create_backorder != "ask"
    ):
        raise RuntimeError("the stock-transfer rollback fixture is invalid")
    return {
        "partner": partner,
        "product": product,
        "sale_order": sale_order,
        "reserved": reserved,
        "reserved_move_line_ids": reserved_move_line_ids,
        "picking_type": picking_type,
        "picking_type_before": picking_type_before,
        "source": source,
        "destination": destination,
        "quant": quant,
    }


def _exercise(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    marker: str,
    fixture: dict[str, Any],
    artifacts: dict[str, set[int]],
) -> int:
    sale_order = fixture["sale_order"]
    invoice_result = _dispatch_twice(
        env,
        alias,
        run_id,
        "sale.order.invoice.create",
        {"order_id": sale_order.id},
        model="account.move",
        states={"draft"},
        source_id=sale_order.id,
    )
    invoice = _one(
        env["account.move"].browse(invoice_result["id"]).exists(), "customer invoice"
    )
    if (
        invoice.env.uid != _USER_ID
        or invoice.move_type != "out_invoice"
        or invoice.state != "draft"
        or invoice.company_id.id != _COMPANY_ID
        or not invoice.invoice_line_ids
        or marker not in (invoice.ref or "")
    ):
        raise RuntimeError(
            "sale.order.invoice.create did not create the expected invoice"
        )
    _record(artifacts, "account.move", invoice)
    _record(artifacts, "account.move.line", invoice.line_ids)

    create_parameters = {
        "picking_type_id": fixture["picking_type"].id,
        "location_id": fixture["source"].id,
        "location_dest_id": fixture["destination"].id,
        "partner_id": fixture["partner"].id,
        "scheduled_date": None,
        "origin": f"Stock transfer smoke {run_id.hex}",
        "moves": [
            {
                "product_id": fixture["product"].id,
                "name": f"{marker}-main",
                "quantity": "4",
                "uom_id": fixture["product"].uom_id.id,
            }
        ],
    }
    created = _dispatch_twice(
        env,
        alias,
        run_id,
        "stock.transfer.create",
        create_parameters,
        model="stock.picking",
        states={"draft"},
        source_id=fixture["picking_type"].id,
    )
    transfer = _one(
        env["stock.picking"].browse(created["id"]).exists(), "stock transfer"
    )
    if transfer.create_uid.id != _USER_ID or transfer.state != "draft":
        raise RuntimeError("stock.transfer.create did not create a uid-5 draft")
    move = _one(transfer.move_ids, "stock move")
    _record(artifacts, "stock.picking", transfer)
    _record(artifacts, "stock.move", move)

    _dispatch_twice(
        env,
        alias,
        run_id,
        "stock.transfer.confirm",
        {"transfer_id": transfer.id},
        model="stock.picking",
        states={"confirmed", "waiting"},
        source_id=fixture["picking_type"].id,
    )
    transfer.invalidate_recordset(["state"])
    if transfer.state not in {"confirmed", "waiting"}:
        raise RuntimeError("stock.transfer.confirm did not preserve manual reservation")

    _dispatch_twice(
        env,
        alias,
        run_id,
        "stock.transfer.assign",
        {"transfer_id": transfer.id},
        model="stock.picking",
        states={"assigned"},
        source_id=fixture["picking_type"].id,
    )
    transfer.invalidate_recordset(["state", "move_line_ids"])
    if transfer.state != "assigned" or not transfer.move_line_ids:
        raise RuntimeError("stock.transfer.assign did not reserve real stock")

    _dispatch_twice(
        env,
        alias,
        run_id,
        "stock.transfer.quantities.set",
        {"transfer_id": transfer.id, "lines": [{"move_id": move.id, "quantity": "2"}]},
        model="stock.picking",
        states={"assigned"},
        source_id=fixture["picking_type"].id,
    )
    move.invalidate_recordset(["quantity"])
    if move.quantity != 2.0:
        raise RuntimeError("stock.transfer.quantities.set wrote the wrong quantity")

    _dispatch_twice(
        env,
        alias,
        run_id,
        "stock.transfer.validate",
        {"transfer_id": transfer.id, "backorder_policy": "create"},
        model="stock.picking",
        states={"done"},
        source_id=fixture["picking_type"].id,
    )
    transfer.invalidate_recordset(["state", "write_uid"])
    backorders = env["stock.picking"].search([("backorder_id", "=", transfer.id)])
    if transfer.state != "done" or transfer.write_uid.id != _USER_ID or not backorders:
        raise RuntimeError("stock.transfer.validate did not create a real backorder")
    _record(artifacts, "stock.picking", backorders)

    reserved = fixture["reserved"]
    _record(artifacts, "stock.move", reserved.move_ids)
    artifacts.setdefault("stock.move.line", set()).update(
        fixture["reserved_move_line_ids"]
    )
    _dispatch_twice(
        env,
        alias,
        run_id,
        "stock.transfer.unreserve",
        {"transfer_id": reserved.id},
        model="stock.picking",
        states={"confirmed", "waiting"},
        source_id=fixture["picking_type"].id,
    )
    reserved.invalidate_recordset(["state", "move_line_ids"])
    if reserved.state not in {"confirmed", "waiting"} or reserved.move_line_ids:
        raise RuntimeError("stock.transfer.unreserve left reserved operations")
    _dispatch_twice(
        env,
        alias,
        run_id,
        "stock.transfer.cancel",
        {"transfer_id": reserved.id},
        model="stock.picking",
        states={"cancel"},
        source_id=fixture["picking_type"].id,
    )
    reserved.invalidate_recordset(["state", "write_uid"])
    if reserved.state != "cancel" or reserved.write_uid.id != _USER_ID:
        raise RuntimeError("stock.transfer.cancel did not cancel as uid 5")
    return len(backorders)


def _capture_artifacts(
    env: Any,
    marker: str,
    fixture: dict[str, Any],
    artifacts: dict[str, set[int]],
) -> None:
    _record(artifacts, "res.partner", fixture["partner"])
    _record(artifacts, "product.product", fixture["product"])
    _record(artifacts, "product.template", fixture["product"].product_tmpl_id)
    _record(artifacts, "sale.order", fixture["sale_order"])
    _record(artifacts, "sale.order.line", fixture["sale_order"].order_line)
    _record(artifacts, "stock.picking", fixture["reserved"])
    _record(artifacts, "stock.quant", fixture["quant"])
    pickings = fixture["sale_order"].picking_ids | env["stock.picking"].search(
        [
            "|",
            ("origin", "ilike", marker),
            ("id", "in", sorted(artifacts.get("stock.picking", set()))),
        ]
    )
    _record(artifacts, "stock.picking", pickings)
    moves = env["stock.move"].search([("picking_id", "in", pickings.ids)])
    _record(artifacts, "stock.move", moves)
    move_lines = env["stock.move.line"].search([("move_id", "in", moves.ids)])
    _record(artifacts, "stock.move.line", move_lines)
    quants = env["stock.quant"].search([("product_id", "=", fixture["product"].id)])
    _record(artifacts, "stock.quant", quants)

    account_moves = env["account.move"].browse(
        sorted(artifacts.get("account.move", set()))
    )
    if "stock_move_id" in env["account.move"]._fields and moves:
        account_moves |= env["account.move"].search(
            [("stock_move_id", "in", moves.ids)]
        )
    for model in ("stock.valuation.layer", "product.value"):
        if model not in env.registry.models:
            continue
        Model = env[model]
        if "stock_move_id" in Model._fields and moves:
            records = Model.search([("stock_move_id", "in", moves.ids)])
        elif "product_id" in Model._fields:
            records = Model.search([("product_id", "=", fixture["product"].id)])
        else:
            continue
        _record(artifacts, model, records)
        if "account_move_id" in Model._fields:
            account_moves |= records.mapped("account_move_id")
        if "account_move_ids" in Model._fields:
            account_moves |= records.mapped("account_move_ids")
        if "account_move_line_id" in Model._fields:
            account_moves |= records.mapped("account_move_line_id.move_id")
    _record(artifacts, "account.move", account_moves)
    _record(artifacts, "account.move.line", account_moves.line_ids)


def _verify_rollback(
    registry: Any,
    marker: str,
    artifacts: dict[str, set[int]],
    baseline_groups: dict[str, bool],
    picking_type_id: int,
    picking_type_before: dict[str, str],
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
                [("name", "ilike", marker)], limit=1
            ),
            "product": env["product.template"].search_count(
                [("name", "ilike", marker)], limit=1
            ),
            "sale_order": env["sale.order"].search_count(
                [("client_order_ref", "ilike", marker)], limit=1
            ),
            "sale_line": env["sale.order.line"].search_count(
                [("name", "ilike", marker)], limit=1
            ),
            "invoice_or_valuation_move": env["account.move"].search_count(
                [("ref", "ilike", marker)], limit=1
            ),
            "account_move_line": env["account.move.line"].search_count(
                [("name", "ilike", marker)], limit=1
            ),
            "picking": env["stock.picking"].search_count(
                [("origin", "ilike", marker)], limit=1
            ),
        }
        if any(survivors.values()) or any(marker_survivors.values()):
            raise RuntimeError(
                "stock-transfer fixtures survived rollback: "
                f"ids={survivors}, markers={marker_survivors}"
            )
        group_ids = {group: env.ref(group).id for group in _GROUPS}
        cursor.execute(
            "SELECT gid FROM res_groups_users_rel WHERE uid = %s AND gid IN %s",
            [_USER_ID, tuple(group_ids.values())],
        )
        direct_groups = {row[0] for row in cursor.fetchall()}
        rolled_back_groups = {
            group: group_id in direct_groups for group, group_id in group_ids.items()
        }
        picking_type = env["stock.picking.type"].browse(picking_type_id).exists()
        if rolled_back_groups != baseline_groups:
            raise RuntimeError("temporary sales or stock groups survived rollback")
        if not picking_type or any(
            picking_type[field] != value for field, value in picking_type_before.items()
        ):
            raise RuntimeError("temporary operation-type settings survived rollback")
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
    marker = f"ODACV4-STOCK-WRITE-{args.alias}-{args.run_id.hex}"
    artifacts: dict[str, set[int]] = {}
    baseline_groups: dict[str, bool] | None = None
    fixture: dict[str, Any] | None = None
    backorders_created = 0
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
            raise RuntimeError("the configured company or business user is unavailable")
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
        backorders_created = _exercise(
            business_env,
            args.alias,
            args.run_id,
            marker,
            fixture,
            artifacts,
        )
        _capture_artifacts(admin_env, marker, fixture, artifacts)
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
            fixture["picking_type"].id,
            fixture["picking_type_before"],
        )
    if failure is not None:
        raise failure
    if fixture is None or baseline_groups is None or backorders_created != 1:
        raise RuntimeError("the live stock-transfer fixture was not fully exercised")
    sys.stdout.write(
        json.dumps(
            {
                "alias": args.alias,
                "backorders_created": backorders_created,
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
