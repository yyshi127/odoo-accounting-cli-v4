"""Shared rollback smoke for eight sales and purchase order reads."""

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
_ALLOW_ENV = "ODACV4_ALLOW_ORDER_DOCUMENTS_SMOKE"
_ALIASES = ("v4-dev", "v4-e2e")
_PHYSICAL_DATABASES = {
    "v4-dev": "odoo_cli_v4_dev",
    "v4-e2e": "odoo_cli_v4_e2e",
}
_COMPANY_ID = 1
_USER_ID = 5
_USER_LOGIN = "odacv4_g5_accountant"
_CAPABILITY_IDS = (
    "sale.order.search",
    "sale.order.get",
    "sale.order.line.search",
    "sale.order.analysis.summary",
    "purchase.order.search",
    "purchase.order.get",
    "purchase.order.line.search",
    "purchase.order.analysis.summary",
)
_FIXTURE_DATE = "2096-08-28"


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
        "user_id": _USER_ID,
    }
    return result


if pytest is not None:

    @pytest.mark.integration
    @pytest.mark.parametrize("alias", _ALIASES)
    def test_order_documents_batch_is_live_and_rolls_back(alias: str) -> None:
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
    from odoo_accounting_cli_v4.bridge.order_documents import (
        OdooOrderDocumentsPort,
    )
    from odoo_accounting_cli_v4.capabilities.order_documents import (
        read_order_document,
    )

    port = OdooOrderDocumentsPort(_DirectClient(env))
    data = read_order_document(
        port,
        capability_id,
        _request(alias, run_id, capability_id, parameters),
    )
    if port.user_id != env.uid or not isinstance(data, dict):
        raise RuntimeError(
            f"{capability_id} returned an invalid public capability result"
        )
    return data


def _setup_fixture(admin_env: Any, marker: str) -> dict[str, int]:
    from odoo.fields import Command

    company = admin_env["res.company"].browse(_COMPANY_ID)
    pricelist = admin_env["product.pricelist"].search(
        [
            ("currency_id", "=", company.currency_id.id),
            "|",
            ("company_id", "=", False),
            ("company_id", "=", _COMPANY_ID),
        ],
        order="id",
        limit=1,
    )
    receipt_type = admin_env["stock.picking.type"].search(
        [
            ("company_id", "=", _COMPANY_ID),
            ("code", "=", "incoming"),
            ("active", "=", True),
        ],
        order="id",
        limit=1,
    )
    if not company or not pricelist or not receipt_type:
        raise RuntimeError("the order fixture prerequisites are unavailable")

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
            "user_id": False,
            "date_order": f"{_FIXTURE_DATE} 01:02:03",
            "client_order_ref": marker,
        }
    )
    sale_line = admin_env["sale.order.line"].create(
        {
            "order_id": sale_order.id,
            "product_id": product.id,
            "name": marker,
            "product_uom_qty": 3.0,
            "product_uom_id": product.uom_id.id,
            "price_unit": 10.0,
            "tax_ids": [Command.clear()],
        }
    )
    purchase_order = admin_env["purchase.order"].create(
        {
            "partner_id": partner.id,
            "company_id": _COMPANY_ID,
            "currency_id": company.currency_id.id,
            "user_id": False,
            "picking_type_id": receipt_type.id,
            "date_order": f"{_FIXTURE_DATE} 01:02:03",
            "partner_ref": marker,
        }
    )
    purchase_line = admin_env["purchase.order.line"].create(
        {
            "order_id": purchase_order.id,
            "product_id": product.id,
            "name": marker,
            "product_qty": 5.0,
            "product_uom_id": product.uom_id.id,
            "price_unit": 8.0,
            "date_planned": f"{_FIXTURE_DATE} 02:03:04",
            "tax_ids": [Command.clear()],
        }
    )
    admin_env.flush_all()
    if (
        sale_order.state != "draft"
        or purchase_order.state != "draft"
        or sale_line.product_uom_id != product.uom_id
        or purchase_line.product_uom_id != product.uom_id
        or sale_line.qty_delivered != 0
        or purchase_line.qty_received != 0
        or sale_order.invoice_ids
        or purchase_order.invoice_ids
        or sale_order.picking_ids
        or purchase_order.picking_ids
    ):
        raise RuntimeError("the unconfirmed order rollback fixture is invalid")
    return {
        "partner": partner.id,
        "product": product.id,
        "sale_order": sale_order.id,
        "sale_line": sale_line.id,
        "purchase_order": purchase_order.id,
        "purchase_line": purchase_line.id,
        "currency": company.currency_id.id,
    }


def _ids(items: list[dict[str, Any]]) -> list[int]:
    return [item["id"] for item in items]


def _exercise_batch(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    fixture: dict[str, int],
) -> None:
    common_search = {
        "date_from": _FIXTURE_DATE,
        "date_to": _FIXTURE_DATE,
        "states": ["draft"],
        "partner_id": fixture["partner"],
        "currency_id": fixture["currency"],
        "limit": 100,
        "cursor": None,
    }
    for prefix, order_key, line_key, pending_flag in (
        ("sale", "sale_order", "sale_line", "to_deliver_only"),
        ("purchase", "purchase_order", "purchase_line", "to_receive_only"),
    ):
        search = _invoke_capability(
            env,
            alias,
            run_id,
            f"{prefix}.order.search",
            common_search,
        )
        if fixture[order_key] not in _ids(search["items"]):
            raise RuntimeError(f"{prefix}.order.search missed the fixture")

        order = _invoke_capability(
            env,
            alias,
            run_id,
            f"{prefix}.order.get",
            {"order_id": fixture[order_key]},
        )
        if (
            order["id"] != fixture[order_key]
            or order["company"]["id"] != _COMPANY_ID
            or fixture[line_key] not in _ids(order["lines"])
            or order["invoices"]
            or order["transfers"]
        ):
            raise RuntimeError(f"{prefix}.order.get returned an invalid graph")

        lines = _invoke_capability(
            env,
            alias,
            run_id,
            f"{prefix}.order.line.search",
            {
                "order_id": fixture[order_key],
                "product_id": fixture["product"],
                "states": ["draft"],
                pending_flag: True,
                "limit": 100,
                "cursor": None,
            },
        )
        matching = [item for item in lines["items"] if item["id"] == fixture[line_key]]
        if len(matching) != 1 or matching[0]["company"]["id"] != _COMPANY_ID:
            raise RuntimeError(f"{prefix}.order.line.search missed the fixture")
        pending_quantity = matching[0][
            "to_deliver_quantity" if prefix == "sale" else "to_receive_quantity"
        ]
        expected_pending = Decimal(3 if prefix == "sale" else 5)
        if Decimal(pending_quantity) != expected_pending:
            raise RuntimeError(f"{prefix} pending quantity was not ordered minus done")

        summary = _invoke_capability(
            env,
            alias,
            run_id,
            f"{prefix}.order.analysis.summary",
            {
                "date_from": _FIXTURE_DATE,
                "date_to": _FIXTURE_DATE,
                "group_by": "partner",
                "states": ["draft"],
                "partner_id": fixture["partner"],
                "currency_id": fixture["currency"],
            },
        )
        if summary["company_id"] != _COMPANY_ID:
            raise RuntimeError(f"{prefix} summary crossed the company boundary")
        if not any(
            group["group"]["id"] == fixture["partner"]
            and group["currency"]["id"] == fixture["currency"]
            for group in summary["groups"]
        ):
            raise RuntimeError(f"{prefix} summary missed its currency group")
        if {total["currency"]["id"] for total in summary["totals_by_currency"]} != {
            fixture["currency"]
        }:
            raise RuntimeError(f"{prefix} summary merged or leaked currencies")


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
            "partner": env["res.partner"].search_count(
                [("id", "=", fixture["partner"])], limit=1
            ),
            "product": env["product.product"].search_count(
                [("id", "=", fixture["product"])], limit=1
            ),
            "sale_order": env["sale.order"].search_count(
                [("id", "=", fixture["sale_order"])], limit=1
            ),
            "sale_line": env["sale.order.line"].search_count(
                [("id", "=", fixture["sale_line"])], limit=1
            ),
            "purchase_order": env["purchase.order"].search_count(
                [("id", "=", fixture["purchase_order"])], limit=1
            ),
            "purchase_line": env["purchase.order.line"].search_count(
                [("id", "=", fixture["purchase_line"])], limit=1
            ),
        }
        if any(survivors.values()):
            raise RuntimeError(
                f"order-document fixtures survived rollback: {survivors}"
            )
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
    marker = f"ODACV4-ORDER-{args.alias}-{args.run_id.hex}"
    fixture: dict[str, int] | None = None
    user_id: int | None = None
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
        raise RuntimeError("the order-document rollback fixture was not created")
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
