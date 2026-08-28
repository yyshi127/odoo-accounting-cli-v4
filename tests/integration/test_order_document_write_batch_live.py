"""Transactional dual-database smoke for sale and purchase order writes.

An administrator creates only rollback-scoped prerequisites and temporarily grants
the standard sales and purchase user groups.  Every capability itself runs as the
configured business user, without sudo, and the outer transaction never commits.
The worker is hard-bound to the two isolated databases because PostgreSQL-backed
Odoo sequence counters are not transactional and may advance during this smoke.
"""

from __future__ import annotations

import argparse
import hashlib
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
_ALLOW_ENV = "ODACV4_ALLOW_ORDER_DOCUMENT_WRITE_SMOKE"
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
    "purchase.group_purchase_user",
)
_CAPABILITIES = (
    "sale.order.create",
    "sale.order.update_draft",
    "sale.order.lines.replace",
    "sale.order.confirm",
    "sale.order.cancel",
    "sale.order.reset_to_draft",
    "purchase.order.create",
    "purchase.order.update_draft",
    "purchase.order.lines.replace",
    "purchase.order.confirm",
    "purchase.order.cancel",
    "purchase.order.reset_to_draft",
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
_FIXTURE_DATE = "2096-08-28"


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
    def test_order_document_write_batch_rolls_back_real_goods_chains(
        alias: str,
    ) -> None:
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


def _canonical_digest(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _key(
    capability_id: str,
    parameters: dict[str, Any],
    explicit: str | None,
) -> str:
    if explicit is not None:
        return explicit
    order_id = parameters["order_id"]
    target = parameters.get("changes", parameters.get("lines"))
    if target is None:
        return f"{capability_id}:{order_id}"
    return f"{capability_id}:{order_id}:{_canonical_digest(target)[:32]}"


def _assert_page(
    page: dict[str, Any],
    *,
    replay: bool,
    model: str,
    partner_id: int,
    states: set[str],
) -> None:
    assert set(page) == _PAGE_KEYS
    assert page["user_id"] == _USER_ID
    assert page["company_visible"] is True
    assert page["module_installed"] is True
    assert page["access_allowed"] is True
    assert page["idempotent_replay"] is replay
    result = page["result"]
    assert isinstance(result, dict) and set(result) == _RESULT_KEYS
    assert result["model"] == model
    assert isinstance(result["id"], int) and result["id"] > 0
    assert isinstance(result["name"], str) and result["name"]
    assert result["state"] in states
    assert result["company_id"] == _COMPANY_ID
    assert result["move_type"] is None
    assert result["source_id"] == partner_id
    assert isinstance(result["line_ids"], list) and result["line_ids"]
    assert result["partial_reconcile_ids"] == []
    assert result["full_reconcile_id"] is None
    assert result["reconciled"] is False


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
    partner_id: int,
    states: set[str],
    explicit_key: str | None = None,
) -> dict[str, Any]:
    from odoo_accounting_cli_v4.capabilities.core_writes import execute_core_write

    request = _request(alias, run_id, capability_id, parameters)
    idempotency_key = _key(capability_id, parameters, explicit_key)
    port = _RuntimePort(env)
    first = execute_core_write(
        port, capability_id, request, idempotency_key, capability_id
    )
    second = execute_core_write(
        port, capability_id, request, idempotency_key, capability_id
    )
    if len(port.pages) != 2:
        raise RuntimeError(f"{capability_id} did not issue two runtime writes")
    _assert_page(
        port.pages[0],
        replay=False,
        model=model,
        partner_id=partner_id,
        states=states,
    )
    _assert_page(
        port.pages[1],
        replay=True,
        model=model,
        partner_id=partner_id,
        states=states,
    )
    assert first["idempotent_replay"] is False
    assert second["idempotent_replay"] is True
    assert first["result"] == second["result"]
    return first["result"]


def _one(records: Any, label: str) -> Any:
    if len(records) != 1:
        raise RuntimeError(f"expected one {label}, got {len(records)}")
    return records


def _setup_prerequisites(admin_env: Any, marker: str) -> dict[str, int]:
    company = admin_env["res.company"].browse(_COMPANY_ID).exists()
    if not company:
        raise RuntimeError("company 1 is unavailable")
    pricelist = admin_env["product.pricelist"].search(
        [
            ("currency_id", "=", company.currency_id.id),
            ("company_id", "in", [False, _COMPANY_ID]),
            ("active", "=", True),
        ],
        order="id",
        limit=1,
    )
    receipt_type = admin_env["stock.picking.type"].search(
        [
            ("company_id", "=", _COMPANY_ID),
            ("code", "=", "incoming"),
            ("active", "=", True),
            ("warehouse_id", "!=", False),
            ("default_location_src_id", "!=", False),
            ("default_location_dest_id", "!=", False),
        ],
        order="id",
        limit=1,
    )
    payment_term = admin_env["account.payment.term"].search(
        [("company_id", "in", [False, _COMPANY_ID])], order="id", limit=1
    )
    incoterm = admin_env["account.incoterms"].search([], order="id", limit=1)
    if not pricelist or not receipt_type or not payment_term or not incoterm:
        raise RuntimeError("the order-write prerequisites are unavailable")

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
            "is_storable": True,
            "company_id": _COMPANY_ID,
            "sale_ok": True,
            "purchase_ok": True,
        }
    )
    admin_env.flush_all()
    if (
        not product.is_storable
        or not product.sale_ok
        or not product.purchase_ok
        or not product.uom_id
        or product.company_id != company
        or partner.company_id != company
        or receipt_type.code != "incoming"
    ):
        raise RuntimeError("the real-goods order fixture is invalid")
    return {
        "partner": partner.id,
        "product": product.id,
        "product_template": product.product_tmpl_id.id,
        "uom": product.uom_id.id,
        "currency": company.currency_id.id,
        "pricelist": pricelist.id,
        "receipt_type": receipt_type.id,
        "payment_term": payment_term.id,
        "incoterm": incoterm.id,
    }


def _line_parameters(kind: str, marker: str, *, replacement: bool) -> dict[str, Any]:
    sale = kind == "sale"
    line = {
        "product_id": None,
        "name": f"{marker}-{kind}-{'replacement' if replacement else 'initial'}",
        "quantity": "3" if sale else "5",
        "uom_id": None,
        "price_unit": "13.25" if sale else "9.5",
        "discount": "5" if replacement else "0",
        "tax_ids": [],
    }
    if not sale:
        line["date_planned"] = (
            "2096-09-03 04:05:06" if replacement else "2096-09-01 02:03:04"
        )
    return line


def _record_artifacts(
    artifacts: dict[str, set[int]], model: str, records: Any
) -> None:
    artifacts.setdefault(model, set()).update(records.ids)


def _exercise_chain(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    marker: str,
    fixture: dict[str, int],
    kind: str,
    artifacts: dict[str, set[int]],
) -> None:
    sale = kind == "sale"
    model = f"{kind}.order"
    create_id = f"{model}.create"
    initial_line = _line_parameters(kind, marker, replacement=False)
    initial_line["product_id"] = fixture["product"]
    initial_line["uom_id"] = fixture["uom"]
    if sale:
        create_parameters = {
            "partner_id": fixture["partner"],
            "pricelist_id": fixture["pricelist"],
            "date_order": f"{_FIXTURE_DATE} 01:02:03",
            "client_order_ref": f"{marker}-sale-create",
            "validity_date": "2096-09-30",
            "commitment_date": None,
            "payment_term_id": None,
            "lines": [initial_line],
        }
    else:
        create_parameters = {
            "partner_id": fixture["partner"],
            "currency_id": fixture["currency"],
            "picking_type_id": fixture["receipt_type"],
            "date_order": f"{_FIXTURE_DATE} 01:02:03",
            "partner_ref": f"{marker}-purchase-create",
            "payment_term_id": None,
            "incoterm_id": None,
            "lines": [initial_line],
        }
    created = _dispatch_twice(
        env,
        alias,
        run_id,
        create_id,
        create_parameters,
        model=model,
        partner_id=fixture["partner"],
        states={"draft"},
        explicit_key=f"order-write-{kind}-{run_id.hex}",
    )
    order_id = created["id"]
    artifacts.setdefault(model, set()).add(order_id)
    artifacts.setdefault(f"{model}.line", set()).update(created["line_ids"])
    order = _one(env[model].browse(order_id).exists(), model)
    if order.env.uid != _USER_ID or order.state != "draft":
        raise RuntimeError(f"{create_id} did not create a uid-5 draft")

    if sale:
        changes = {
            "client_order_ref": f"{marker}-sale-updated",
            "validity_date": "2096-10-31",
            "commitment_date": "2096-09-02 03:04:05",
            "payment_term_id": fixture["payment_term"],
        }
    else:
        changes = {
            "partner_ref": f"{marker}-purchase-updated",
            "date_order": "2096-08-29 03:04:05",
            "payment_term_id": fixture["payment_term"],
            "incoterm_id": fixture["incoterm"],
        }
    _dispatch_twice(
        env,
        alias,
        run_id,
        f"{model}.update_draft",
        {"order_id": order_id, "changes": changes},
        model=model,
        partner_id=fixture["partner"],
        states={"draft"},
    )
    order.invalidate_recordset(list(changes))
    if sale:
        header_valid = (
            order.client_order_ref == changes["client_order_ref"]
            and str(order.validity_date) == changes["validity_date"]
            and str(order.commitment_date) == changes["commitment_date"]
            and order.payment_term_id.id == fixture["payment_term"]
        )
    else:
        header_valid = (
            order.partner_ref == changes["partner_ref"]
            and str(order.date_order) == changes["date_order"]
            and order.payment_term_id.id == fixture["payment_term"]
            and order.incoterm_id.id == fixture["incoterm"]
        )
    if not header_valid:
        raise RuntimeError(f"{model}.update_draft did not persist all header fields")

    replacement_line = _line_parameters(kind, marker, replacement=True)
    replacement_line["product_id"] = fixture["product"]
    replacement_line["uom_id"] = fixture["uom"]
    replaced = _dispatch_twice(
        env,
        alias,
        run_id,
        f"{model}.lines.replace",
        {"order_id": order_id, "lines": [replacement_line]},
        model=model,
        partner_id=fixture["partner"],
        states={"draft"},
    )
    artifacts.setdefault(f"{model}.line", set()).update(replaced["line_ids"])
    order.invalidate_recordset(["order_line"])
    line = _one(order.order_line, f"{model} replacement line")
    line.invalidate_recordset(
        [
            "product_id",
            "name",
            "product_uom_id",
            "product_uom_qty" if sale else "product_qty",
            "price_unit",
            "discount",
            "tax_ids",
            *(("date_planned",) if not sale else ()),
        ]
    )
    quantity = line.product_uom_qty if sale else line.product_qty
    line_valid = (
        line.product_id.id == fixture["product"]
        and line.name == replacement_line["name"]
        and line.product_uom_id.id == fixture["uom"]
        and Decimal(str(quantity)) == Decimal(replacement_line["quantity"])
        and Decimal(str(line.price_unit)) == Decimal(replacement_line["price_unit"])
        and Decimal(str(line.discount)) == Decimal(replacement_line["discount"])
        and not line.tax_ids
    )
    if not sale:
        line_valid = line_valid and str(line.date_planned) == replacement_line[
            "date_planned"
        ]
    if not line_valid:
        raise RuntimeError(f"{model}.lines.replace did not persist the real-goods line")

    confirmed = _dispatch_twice(
        env,
        alias,
        run_id,
        f"{model}.confirm",
        {"order_id": order_id},
        model=model,
        partner_id=fixture["partner"],
        states={"sale"} if sale else {"purchase", "to approve"},
    )
    order.invalidate_recordset(["state", "picking_ids"])
    if order.state != confirmed["state"]:
        raise RuntimeError(f"{model}.confirm returned a stale state")
    pickings = order.picking_ids
    if sale and not pickings:
        raise RuntimeError("the storable sale did not create an outgoing transfer")
    if not sale and order.state == "purchase" and not pickings:
        raise RuntimeError("the approved storable purchase did not create a receipt")
    if any(
        picking.company_id.id != _COMPANY_ID
        or picking.picking_type_id.code != ("outgoing" if sale else "incoming")
        for picking in pickings
    ):
        raise RuntimeError(f"{model}.confirm created a cross-company transfer")
    _record_artifacts(artifacts, "stock.picking", pickings)
    _record_artifacts(artifacts, "stock.move", pickings.move_ids)

    canceled = _dispatch_twice(
        env,
        alias,
        run_id,
        f"{model}.cancel",
        {"order_id": order_id},
        model=model,
        partner_id=fixture["partner"],
        states={"cancel"},
    )
    order.invalidate_recordset(["state"])
    if canceled["state"] != "cancel" or order.state != "cancel":
        raise RuntimeError(f"{model}.cancel did not persist cancel state")

    reset = _dispatch_twice(
        env,
        alias,
        run_id,
        f"{model}.reset_to_draft",
        {"order_id": order_id},
        model=model,
        partner_id=fixture["partner"],
        states={"draft"},
    )
    order.invalidate_recordset(["state"])
    if reset["state"] != "draft" or order.state != "draft":
        raise RuntimeError(f"{model}.reset_to_draft did not persist draft state")


def _exercise_batch(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    marker: str,
    fixture: dict[str, int],
    artifacts: dict[str, set[int]],
) -> None:
    for kind in ("sale", "purchase"):
        _exercise_chain(env, alias, run_id, marker, fixture, kind, artifacts)


def _verify_rollback(
    registry: Any,
    marker: str,
    artifacts: dict[str, set[int]],
    baseline_groups: dict[str, bool],
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
            model: env[model].search_count(
                [("id", "in", sorted(record_ids))], limit=1
            )
            for model, record_ids in artifacts.items()
            if record_ids
        }
        remaining["partner_marker"] = env["res.partner"].search_count(
            [("name", "ilike", marker)], limit=1
        )
        remaining["product_marker"] = env["product.template"].search_count(
            [("name", "ilike", marker)], limit=1
        )
        remaining["sale_order_marker"] = env["sale.order"].search_count(
            [("client_order_ref", "ilike", marker)], limit=1
        )
        remaining["sale_line_marker"] = env["sale.order.line"].search_count(
            [("name", "ilike", marker)], limit=1
        )
        remaining["purchase_order_marker"] = env["purchase.order"].search_count(
            [("partner_ref", "ilike", marker)], limit=1
        )
        remaining["purchase_line_marker"] = env["purchase.order.line"].search_count(
            [("name", "ilike", marker)], limit=1
        )
        if any(remaining.values()):
            raise RuntimeError(f"order-write fixtures survived rollback: {remaining}")
        group_ids = {group: env.ref(group).id for group in _GROUPS}
        cursor.execute(
            "SELECT gid FROM res_groups_users_rel WHERE uid = %s AND gid IN %s",
            [_USER_ID, tuple(group_ids.values())],
        )
        direct_group_ids = {row[0] for row in cursor.fetchall()}
        rolled_back_groups = {
            group: group_id in direct_group_ids
            for group, group_id in group_ids.items()
        }
        if rolled_back_groups != baseline_groups:
            raise RuntimeError(
                "temporary sales or purchase group membership survived rollback"
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
    marker = f"ODACV4-ORDER-WRITE-{args.alias}-{args.run_id.hex}"
    artifacts: dict[str, set[int]] = {}
    baseline_groups: dict[str, bool] | None = None
    fixture: dict[str, int] | None = None
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
        direct_group_ids = {row[0] for row in cursor.fetchall()}
        baseline_groups = {
            group: group_id in direct_group_ids
            for group, group_id in group_ids.items()
        }
        missing_group_ids = [
            group_id
            for group, group_id in group_ids.items()
            if not user.has_group(group)
        ]
        if missing_group_ids:
            user.write({"group_ids": [Command.link(group) for group in missing_group_ids]})
            admin_env.flush_all()

        fixture = _setup_prerequisites(admin_env, marker)
        artifacts.update(
            {
                "res.partner": {fixture["partner"]},
                "product.product": {fixture["product"]},
                "product.template": {fixture["product_template"]},
            }
        )
        business_context = {**context, "active_test": True}
        business_env = api.Environment(cursor, _USER_ID, business_context)
        if (
            business_env.uid != _USER_ID
            or business_env.user.login != _USER_LOGIN
            or not business_env.user.active
            or _COMPANY_ID not in business_env.user.company_ids.ids
            or not all(business_env.user.has_group(group) for group in _GROUPS)
        ):
            raise RuntimeError("uid 5 or its temporary standard groups are unavailable")
        _exercise_batch(
            business_env,
            args.alias,
            args.run_id,
            marker,
            fixture,
            artifacts,
        )
    except Exception as exc:  # noqa: BLE001 - rollback must cover every Odoo failure.
        failure = exc
    finally:
        cursor.rollback()
        cursor.close()

    if baseline_groups is not None:
        _verify_rollback(registry, marker, artifacts, baseline_groups)
    if failure is not None:
        raise failure
    if fixture is None or baseline_groups is None:
        raise RuntimeError("the live order-write fixtures were not initialized")
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
