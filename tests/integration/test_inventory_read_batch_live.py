"""Shared rollback smoke for ten inventory master and operation reads."""

from __future__ import annotations

import argparse
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
_ALLOW_ENV = "ODACV4_ALLOW_INVENTORY_READ_SMOKE"
_ALIASES = ("v4-dev", "v4-e2e")
_PHYSICAL_DATABASES = {
    "v4-dev": "odoo_cli_v4_dev",
    "v4-e2e": "odoo_cli_v4_e2e",
}
_COMPANY_ID = 1
_USER_ID = 5
_USER_LOGIN = "odacv4_g5_accountant"
_MASTER_CAPABILITY_IDS = (
    "product.category.list",
    "warehouse.list",
    "stock.location.list",
    "stock.operation_type.list",
    "stock.route.list",
)
_OPERATION_CAPABILITY_IDS = (
    "stock.transfer.search",
    "stock.transfer.get",
    "stock.move.search",
    "inventory.on_hand.summary",
    "inventory.availability.inspect",
)
_CAPABILITY_IDS = _MASTER_CAPABILITY_IDS + _OPERATION_CAPABILITY_IDS


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _enabled_runtime(alias: str) -> tuple[Path, dict[str, Any]]:
    assert pytest is not None
    if os.environ.get(_ALLOW_ENV) != "1":
        pytest.skip(f"set {_ALLOW_ENV}=1 to authorize rollback fixture setup")
    raw_path = os.environ.get(_CONFIG_ENV)
    if not raw_path:
        pytest.skip(f"{_CONFIG_ENV} is not configured")
    path = Path(raw_path)
    if not path.is_file():
        pytest.skip(f"{_CONFIG_ENV} does not name an existing file")
    document = json.loads(path.read_text(encoding="utf-8"))
    entry = document.get("aliases", {}).get(alias)
    assert isinstance(entry, dict)
    assert entry.get("database") == _PHYSICAL_DATABASES[alias]
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
            _PHYSICAL_DATABASES[alias],
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
) -> dict[str, Any]:
    command, timeout = _worker_command(alias, run_id, config_path, runtime)
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = os.pathsep.join(
        part
        for part in (
            str(_project_root() / "src"),
            environment.get("PYTHONPATH"),
        )
        if part
    )
    completed = subprocess.run(
        command,
        cwd=_project_root(),
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
        "alias": alias,
        "capabilities": list(_CAPABILITY_IDS),
        "company_id": _COMPANY_ID,
        "database": _PHYSICAL_DATABASES[alias],
        "positive_results": len(_CAPABILITY_IDS),
        "rollback_verified": True,
        "user_id": result["user_id"],
    }
    assert result["user_id"] == _USER_ID
    return result


if pytest is not None:

    @pytest.mark.integration
    @pytest.mark.parametrize("alias", _ALIASES)
    def test_inventory_read_batch_is_live_and_rolls_back(alias: str) -> None:
        config_path, runtime = _enabled_runtime(alias)
        _run_worker(alias, uuid.uuid4(), config_path, runtime)


def _worker_arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-worker", action="store_true", required=True)
    parser.add_argument("--odoo-config", type=Path, required=True)
    parser.add_argument("--odoo-source", type=Path, required=True)
    parser.add_argument("--alias", choices=_ALIASES, required=True)
    parser.add_argument(
        "--database", choices=tuple(_PHYSICAL_DATABASES.values()), required=True
    )
    parser.add_argument("--run-id", type=uuid.UUID, required=True)
    args = parser.parse_args(argv)
    if args.database != _PHYSICAL_DATABASES[args.alias]:
        parser.error("alias and physical database do not match")
    if not args.odoo_config.is_absolute() or not args.odoo_config.is_file():
        parser.error("odoo-config must be an existing absolute file")
    if not args.odoo_source.is_absolute() or not args.odoo_source.is_dir():
        parser.error("odoo-source must be an existing absolute directory")
    return args


class _DirectClient:
    def __init__(self, env: Any) -> None:
        self.env = env

    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        from odoo_accounting_cli_v4.bridge.runtime import _dispatch

        return _dispatch(self.env, action, payload, _COMPANY_ID)


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


def _invoke_capability(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    from odoo_accounting_cli_v4.bridge.inventory_master import (
        OdooInventoryMasterPort,
    )
    from odoo_accounting_cli_v4.bridge.inventory_operations import (
        OdooInventoryOperationsPort,
    )
    from odoo_accounting_cli_v4.capabilities.inventory_master import (
        read_inventory_master,
    )
    from odoo_accounting_cli_v4.capabilities.inventory_operations import (
        read_inventory_operations,
    )

    client = _DirectClient(env)
    request = _request(alias, run_id, capability_id, parameters)
    if capability_id in _MASTER_CAPABILITY_IDS:
        port = OdooInventoryMasterPort(client)
        data = read_inventory_master(port, capability_id, request)
    else:
        port = OdooInventoryOperationsPort(client)
        data = read_inventory_operations(port, capability_id, request)
    if port.user_id != env.uid or not isinstance(data, dict):
        raise RuntimeError(
            f"{capability_id} returned an invalid public capability result"
        )
    return data


def _setup_fixture(admin_env: Any, marker: str) -> dict[str, int]:
    operation_type = admin_env["stock.picking.type"].search(
        [
            ("company_id", "=", _COMPANY_ID),
            ("code", "=", "incoming"),
            ("active", "=", True),
            ("default_location_src_id", "!=", False),
            ("default_location_dest_id", "!=", False),
            ("default_location_dest_id.usage", "=", "internal"),
        ],
        order="id",
        limit=1,
    )
    if not operation_type or not operation_type.warehouse_id:
        raise RuntimeError("no usable company-1 receipt operation type is available")
    source = operation_type.default_location_src_id
    destination = operation_type.default_location_dest_id
    route = (
        admin_env["stock.route"]
        .with_context(active_test=False)
        .search(
            [
                "|",
                ("company_id", "=", False),
                ("company_id", "=", _COMPANY_ID),
            ],
            order="id",
            limit=1,
        )
    )
    if not route:
        raise RuntimeError("no company-visible stock route is available")
    category = admin_env["product.category"].search([], order="id", limit=1)
    if not category:
        raise RuntimeError("no product category is available")

    product = admin_env["product.product"].create(
        {
            "name": marker,
            "is_storable": True,
            "company_id": _COMPANY_ID,
            "categ_id": category.id,
        }
    )
    transfer = admin_env["stock.picking"].create(
        {
            "picking_type_id": operation_type.id,
            "location_id": source.id,
            "location_dest_id": destination.id,
            "company_id": _COMPANY_ID,
        }
    )
    move = admin_env["stock.move"].create(
        {
            "product_id": product.id,
            "product_uom_qty": 2.0,
            "product_uom": product.uom_id.id,
            "location_id": source.id,
            "location_dest_id": destination.id,
            "picking_id": transfer.id,
            "company_id": _COMPANY_ID,
        }
    )
    admin_env["stock.quant"]._update_available_quantity(
        product,
        destination,
        5.0,
    )
    admin_env.flush_all()
    quant = admin_env["stock.quant"].search(
        [
            ("product_id", "=", product.id),
            ("location_id", "=", destination.id),
            ("company_id", "=", _COMPANY_ID),
        ],
        order="id",
        limit=1,
    )
    if (
        not product.is_storable
        or product.categ_id != category
        or transfer.state != "draft"
        or move.state != "draft"
        or not quant
        or quant.quantity != 5.0
        or destination.usage != "internal"
    ):
        raise RuntimeError("the inventory rollback fixture is invalid")
    return {
        "category": category.id,
        "warehouse": operation_type.warehouse_id.id,
        "location": destination.id,
        "operation_type": operation_type.id,
        "route": route.id,
        "product": product.id,
        "transfer": transfer.id,
        "move": move.id,
        "quant": quant.id,
    }


def _ids(items: list[dict[str, Any]]) -> list[int]:
    return [item["id"] for item in items]


def _exercise_batch(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    fixture: dict[str, int],
) -> None:
    master_requests = {
        "product.category.list": {"limit": 1000, "cursor": None},
        "warehouse.list": {"active": True, "limit": 1000, "cursor": None},
        "stock.location.list": {
            "active": None,
            "warehouse_id": fixture["warehouse"],
            "usage": "internal",
            "limit": 1000,
            "cursor": None,
        },
        "stock.operation_type.list": {
            "active": True,
            "warehouse_id": fixture["warehouse"],
            "code": "incoming",
            "limit": 1000,
            "cursor": None,
        },
        "stock.route.list": {
            "active": None,
            "limit": 1000,
            "cursor": None,
        },
    }
    expected = {
        "product.category.list": fixture["category"],
        "warehouse.list": fixture["warehouse"],
        "stock.location.list": fixture["location"],
        "stock.operation_type.list": fixture["operation_type"],
        "stock.route.list": fixture["route"],
    }
    for capability_id, parameters in master_requests.items():
        result = _invoke_capability(env, alias, run_id, capability_id, parameters)
        if expected[capability_id] not in _ids(result["items"]):
            raise RuntimeError(
                f"{capability_id} missed expected id {expected[capability_id]}; "
                f"observed ids were {_ids(result['items'])}"
            )

    transfers = _invoke_capability(
        env,
        alias,
        run_id,
        "stock.transfer.search",
        {
            "picking_type_id": fixture["operation_type"],
            "state": "draft",
            "limit": 100,
            "cursor": None,
        },
    )
    if fixture["transfer"] not in _ids(transfers["items"]):
        raise RuntimeError("stock.transfer.search missed the fixture")

    transfer = _invoke_capability(
        env,
        alias,
        run_id,
        "stock.transfer.get",
        {"transfer_id": fixture["transfer"]},
    )
    if transfer["id"] != fixture["transfer"] or transfer["state"] != "draft":
        raise RuntimeError("stock.transfer.get missed the draft fixture")

    moves = _invoke_capability(
        env,
        alias,
        run_id,
        "stock.move.search",
        {
            "transfer_id": fixture["transfer"],
            "product_id": fixture["product"],
            "state": "draft",
            "limit": 100,
            "cursor": None,
        },
    )
    if fixture["move"] not in _ids(moves["items"]):
        raise RuntimeError("stock.move.search missed the fixture")

    summary = _invoke_capability(
        env,
        alias,
        run_id,
        "inventory.on_hand.summary",
        {"location_id": fixture["location"], "product_id": fixture["product"]},
    )
    groups = summary["groups"]
    if len(groups) != 1 or groups[0]["product"]["id"] != fixture["product"]:
        raise RuntimeError("inventory.on_hand.summary missed the fixture product")
    if Decimal(groups[0]["quantity"]) != Decimal(5):
        raise RuntimeError("inventory.on_hand.summary returned the wrong quantity")

    availability = _invoke_capability(
        env,
        alias,
        run_id,
        "inventory.availability.inspect",
        {"product_id": fixture["product"], "location_id": fixture["location"]},
    )
    if (
        availability["product"]["id"] != fixture["product"]
        or Decimal(availability["on_hand_quantity"]) != Decimal(5)
        or Decimal(availability["free_quantity"]) != Decimal(5)
    ):
        raise RuntimeError("inventory.availability.inspect returned wrong quantities")


def _verify_rollback(registry: Any, fixture: dict[str, int]) -> None:
    from odoo import SUPERUSER_ID, api

    cursor = registry.cursor()
    try:
        env = api.Environment(
            cursor,
            SUPERUSER_ID,
            {"allowed_company_ids": [_COMPANY_ID], "active_test": False},
        )
        survivors = {
            "product": env["product.product"].search_count(
                [("id", "=", fixture["product"])], limit=1
            ),
            "transfer": env["stock.picking"].search_count(
                [("id", "=", fixture["transfer"])], limit=1
            ),
            "move": env["stock.move"].search_count(
                [("id", "=", fixture["move"])], limit=1
            ),
            "quant": env["stock.quant"].search_count(
                [("id", "=", fixture["quant"])], limit=1
            ),
        }
        if any(survivors.values()):
            raise RuntimeError(f"inventory fixtures survived rollback: {survivors}")
    finally:
        cursor.rollback()
        cursor.close()


def _live_worker(argv: list[str] | None = None) -> int:
    args = _worker_arguments(argv)
    root = _project_root()
    sys.path.insert(0, str(args.odoo_source.resolve(strict=True)))
    sys.path.insert(0, str((root / "src").resolve(strict=True)))

    from odoo import SUPERUSER_ID, api
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
    registry = Registry(args.database)
    cursor = registry.cursor()
    marker = f"ODACV4-INVENTORY-{args.alias}-{args.run_id.hex}"
    user_id: int | None = None
    fixture: dict[str, int] | None = None
    try:
        context = {
            "allowed_company_ids": [_COMPANY_ID],
            "active_test": True,
            "lang": "en_US",
            "tz": "Asia/Shanghai",
        }
        admin_env = api.Environment(cursor, SUPERUSER_ID, context)
        company = admin_env["res.company"].browse(_COMPANY_ID).exists()
        user = (
            admin_env["res.users"]
            .with_context(active_test=False)
            .search([("login", "=", _USER_LOGIN)], limit=1)
        )
        if (
            not company
            or not user
            or user.id != _USER_ID
            or not user.active
            or company not in user.company_ids
        ):
            raise RuntimeError("the configured company or user is unavailable")
        fixture = _setup_fixture(admin_env, marker)
        user_id = user.id
        business_env = api.Environment(cursor, user_id, context)
        _exercise_batch(business_env, args.alias, args.run_id, fixture)
    finally:
        cursor.rollback()
        cursor.close()

    if fixture is None:
        raise RuntimeError("the inventory rollback fixture was not created")
    _verify_rollback(registry, fixture)
    sys.stdout.write(
        json.dumps(
            {
                "alias": args.alias,
                "capabilities": list(_CAPABILITY_IDS),
                "company_id": _COMPANY_ID,
                "database": args.database,
                "positive_results": len(_CAPABILITY_IDS),
                "rollback_verified": True,
                "user_id": user_id,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_live_worker())
