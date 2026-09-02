"""Rollback-only dual-database smoke for eight product accounting writes.

The fixed accountant is not assumed to have product-manager or stock-manager
access.  An administrator grants ``product.group_product_manager`` and
``stock.group_stock_manager`` inside the outer transaction only; every capability
call still runs as uid 5 with ``su=False``.  Both grants and every business
write are rolled back and audited from a fresh cursor.
"""

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
_ALLOW_ENV = "ODACV4_ALLOW_PRODUCT_ACCOUNTING_WRITE_SMOKE"
_ALIASES = ("v4-dev", "v4-e2e")
_DATABASES = {
    "v4-dev": "odoo_cli_v4_dev",
    "v4-e2e": "odoo_cli_v4_e2e",
}
_COMPANY_ID = 1
_USER_ID = 5
_USER_LOGIN = "odacv4_g5_accountant"
_MANAGER_GROUP = "product.group_product_manager"
_STOCK_MANAGER_GROUP = "stock.group_stock_manager"
_TEMPORARY_GROUPS = (_MANAGER_GROUP, _STOCK_MANAGER_GROUP)
_WRITE_CAPABILITIES = (
    "product.create",
    "product.update",
    "product.cost.update",
    "product.category.accounting_profile.update",
    "product.accounting_profile.update",
    "product.duplicate",
    "product.archive",
    "product.restore",
)
_VERIFICATION_READS = (
    "product.get",
    "product.accounting_profile.get",
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
    assert isinstance(bridge, dict) and set(bridge) == {"argv", "timeout_seconds"}
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
        "business_su": False,
        "capabilities": list(_WRITE_CAPABILITIES),
        "company_id": _COMPANY_ID,
        "database": _DATABASES[alias],
        "default_product_manager_authorized": False,
        "default_stock_manager_authorized": False,
        "immediate_replays": len(_WRITE_CAPABILITIES),
        "orderpoint_active_state_verified": True,
        "rollback_verified": True,
        "temporary_group_fixtures": list(_TEMPORARY_GROUPS),
        "temporary_groups_rolled_back": True,
        "user_id": _USER_ID,
        "verification_reads": list(_VERIFICATION_READS),
    }


if pytest is not None:

    @pytest.mark.integration
    def test_product_accounting_write_batch_rolls_back_one_chain_per_alias() -> None:
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


def _request(
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    identity = json.dumps(
        [capability_id, parameters],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return {
        "schema_version": "v1",
        "request_id": str(uuid.uuid5(run_id, identity)),
        "context": {
            "database": alias,
            "company_id": _COMPANY_ID,
            "user_login": _USER_LOGIN,
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": parameters,
    }


class _DirectClient:
    def __init__(self, env: Any) -> None:
        self.env = env

    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        if self.env.uid != _USER_ID or self.env.su:
            raise RuntimeError("a public capability escaped uid 5 with su=False")
        from odoo_accounting_cli_v4.bridge.runtime import _dispatch

        return _dispatch(self.env, action, payload, _COMPANY_ID)


def _write(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    capability_id: str,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    from odoo_accounting_cli_v4.bridge.core_writes import OdooCoreWritePort
    from odoo_accounting_cli_v4.capabilities.core_writes import (
        _expected_idempotency_key,
        execute_core_write,
        validate_core_write_request,
    )

    request = _request(alias, run_id, capability_id, parameters)
    _, context, normalized = validate_core_write_request(capability_id, request)
    key = _expected_idempotency_key(capability_id, normalized, context["company_id"])
    if key is None:
        raise RuntimeError(f"{capability_id} lacks the frozen deterministic key")
    port = OdooCoreWritePort(_DirectClient(env))
    first = execute_core_write(port, capability_id, request, key, capability_id)
    if port.user_id != _USER_ID or first["idempotent_replay"] is not False:
        raise RuntimeError(f"{capability_id} replayed its first execution")
    replay = execute_core_write(port, capability_id, request, key, capability_id)
    if (
        port.user_id != _USER_ID
        or replay["idempotent_replay"] is not True
        or replay["result"] != first["result"]
    ):
        raise RuntimeError(f"{capability_id} did not replay deterministically")
    return first["result"]


def _product_get(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    product_id: int,
) -> dict[str, Any]:
    from odoo_accounting_cli_v4.bridge.core_object_reads import (
        OdooCoreObjectReadPort,
    )
    from odoo_accounting_cli_v4.capabilities.core_object_reads import read_core_object

    port = OdooCoreObjectReadPort(_DirectClient(env))
    result = read_core_object(
        "product.get",
        port,
        _request(alias, run_id, "product.get", {"product_id": product_id}),
    )
    if port.user_id != _USER_ID:
        raise RuntimeError("product.get did not run as the fixed accountant")
    return result


def _profile_get(
    env: Any,
    alias: str,
    run_id: uuid.UUID,
    product_id: int,
) -> dict[str, Any]:
    from odoo_accounting_cli_v4.bridge.product_accounting_profile import (
        OdooProductAccountingProfilePort,
    )
    from odoo_accounting_cli_v4.capabilities.product_accounting_profile import (
        get_product_accounting_profile,
    )

    port = OdooProductAccountingProfilePort(_DirectClient(env))
    result = get_product_accounting_profile(
        port,
        _request(
            alias,
            run_id,
            "product.accounting_profile.get",
            {"product_id": product_id},
        ),
    )
    if port.user_id != _USER_ID:
        raise RuntimeError(
            "product.accounting_profile.get did not run as the fixed accountant"
        )
    return result


def _assert_product_result(
    result: dict[str, Any],
    *,
    state: str,
    product_id: int | None = None,
    template_id: int | None = None,
) -> tuple[int, int]:
    if (
        result["model"] != "product.product"
        or result["state"] != state
        or result["company_id"] != _COMPANY_ID
        or not isinstance(result["id"], int)
        or isinstance(result["id"], bool)
        or result["id"] <= 0
        or not isinstance(result["source_id"], int)
        or isinstance(result["source_id"], bool)
        or result["source_id"] <= 0
        or (product_id is not None and result["id"] != product_id)
        or (template_id is not None and result["source_id"] != template_id)
    ):
        raise RuntimeError(f"invalid product write result: {result}")
    return result["id"], result["source_id"]


def _assert_category_result(result: dict[str, Any], category_id: int) -> None:
    if (
        result["model"] != "product.category"
        or result["id"] != category_id
        or result["state"] != "active"
        or result["company_id"] != _COMPANY_ID
        or result["source_id"] is not None
    ):
        raise RuntimeError(f"invalid product-category write result: {result}")


def _direct_group_membership(cursor: Any, group_id: int) -> bool:
    cursor.execute(
        "SELECT 1 FROM res_groups_users_rel WHERE uid = %s AND gid = %s",
        [_USER_ID, group_id],
    )
    return cursor.fetchone() is not None


def _value_ids(env: Any) -> set[int] | None:
    if "product.value" not in env.registry.models:
        return None
    return set(env["product.value"].with_context(active_test=False).search([]).ids)


def _category_accounts(category: Any) -> dict[str, int | None]:
    return {
        "income_account_id": category.property_account_income_categ_id.id or None,
        "expense_account_id": category.property_account_expense_categ_id.id or None,
    }


def _fixture(admin_env: Any) -> dict[str, Any]:
    company = admin_env["res.company"].browse(_COMPANY_ID).exists()
    category = (
        admin_env["product.category"]
        .with_company(company)
        .search([], order="id", limit=1)
    )
    uom = admin_env["uom.uom"].search([("active", "=", True)], order="id", limit=1)
    category_accounts = _category_accounts(category)
    income_domain: list[Any] = [
        ("company_ids", "in", [_COMPANY_ID]),
        ("account_type", "in", ["income", "income_other"]),
        ("active", "=", True),
    ]
    if category_accounts["income_account_id"] is not None:
        income_domain.append(("id", "!=", category_accounts["income_account_id"]))
    income = admin_env["account.account"].search(
        income_domain,
        order="id",
        limit=1,
    )
    expense_domain: list[Any] = [
        ("company_ids", "in", [_COMPANY_ID]),
        (
            "account_type",
            "in",
            ["expense", "expense_depreciation", "expense_direct_cost"],
        ),
        ("active", "=", True),
    ]
    if category_accounts["expense_account_id"] is not None:
        expense_domain.append(("id", "!=", category_accounts["expense_account_id"]))
    expense = admin_env["account.account"].search(
        expense_domain,
        order="id",
        limit=1,
    )
    sale_tax = admin_env["account.tax"].search(
        [
            ("company_id", "=", _COMPANY_ID),
            ("type_tax_use", "=", "sale"),
            ("active", "=", True),
        ],
        order="id",
        limit=1,
    )
    purchase_tax = admin_env["account.tax"].search(
        [
            ("company_id", "=", _COMPANY_ID),
            ("type_tax_use", "=", "purchase"),
            ("active", "=", True),
        ],
        order="id",
        limit=1,
    )
    warehouse = admin_env["stock.warehouse"].search(
        [("company_id", "=", _COMPANY_ID)], order="id", limit=1
    )
    location = warehouse.lot_stock_id
    if not all(
        (
            company,
            category,
            uom,
            income,
            expense,
            sale_tax,
            purchase_tax,
            warehouse,
            location,
        )
    ):
        raise RuntimeError(
            "company-1 product/category/uom/account/tax/warehouse prerequisites "
            "are unavailable"
        )
    return {
        "category_id": category.id,
        "category_accounts": category_accounts,
        "uom_id": uom.id,
        "income_account_id": income.id,
        "expense_account_id": expense.id,
        "sale_tax_id": sale_tax.id,
        "purchase_tax_id": purchase_tax.id,
        "warehouse_id": warehouse.id,
        "location_id": location.id,
        "product_value_ids": _value_ids(admin_env),
    }


def _assert_product_read(
    item: dict[str, Any],
    *,
    product_id: int,
    template_id: int,
    category_id: int,
    uom_id: int,
    default_code: str,
    name: str,
    list_price: str,
    standard_price: str | None,
    active: bool = True,
) -> None:
    if (
        item["id"] != product_id
        or item["template"]["id"] != template_id
        or item["category"]["id"] != category_id
        or item["uom"]["id"] != uom_id
        or item["default_code"] != default_code
        or item["name"] != name
        or item["active"] is not active
        or item["product_type"] != "service"
        or item["is_storable"] is not False
        or item["company_id"] != _COMPANY_ID
        or Decimal(item["list_price"]) != Decimal(list_price)
        or (
            standard_price is not None
            and Decimal(item["standard_price"]) != Decimal(standard_price)
        )
    ):
        raise RuntimeError(f"product.get returned the wrong product: {item}")


def _assert_profile_accounts(
    profile: dict[str, Any],
    *,
    product_id: int,
    template_id: int,
    category_id: int,
    income_account_id: int,
    expense_account_id: int,
) -> None:
    income = profile["accounts"]["income"]
    expense = profile["accounts"]["expense"]
    if (
        profile["company_id"] != _COMPANY_ID
        or profile["product"]["id"] != product_id
        or profile["product"]["template_id"] != template_id
        or profile["product"]["company_id"] != _COMPANY_ID
        or profile["template"]["id"] != template_id
        or profile["template"]["category_id"] != category_id
        or profile["category"]["id"] != category_id
        or income["available"] is not True
        or income["account"] is None
        or income["account"]["id"] != income_account_id
        or expense["available"] is not True
        or expense["account"] is None
        or expense["account"]["id"] != expense_account_id
    ):
        raise RuntimeError(
            "product.accounting_profile.get returned the wrong effective accounts"
        )


def _exercise(
    env: Any,
    admin_env: Any,
    alias: str,
    run_id: uuid.UUID,
    marker: str,
    fixture: dict[str, Any],
) -> dict[str, set[int]]:
    name = f"{marker} Service"
    updated_name = f"{marker} Service Updated"
    default_code = f"{marker}-ORIG"
    duplicate_code = f"{marker}-COPY"
    category_id = fixture["category_id"]
    uom_id = fixture["uom_id"]

    created = _write(
        env,
        alias,
        run_id,
        "product.create",
        {
            "name": name,
            "default_code": default_code,
            "product_type": "service",
            "category_id": category_id,
            "uom_id": uom_id,
            "sale_ok": True,
            "purchase_ok": True,
            "list_price": "120",
        },
    )
    product_id, template_id = _assert_product_result(created, state="active")
    product = env["product.product"].browse(product_id).exists()
    template = env["product.template"].browse(template_id).exists()
    if (
        not product
        or not template
        or product.product_tmpl_id != template
        or product.type != "service"
        or product.is_storable
        or len(template.product_variant_ids) != 1
        or template.product_variant_id != product
    ):
        raise RuntimeError(
            "product.create did not create one nonstorable service variant"
        )

    _assert_product_read(
        _product_get(env, alias, run_id, product_id),
        product_id=product_id,
        template_id=template_id,
        category_id=category_id,
        uom_id=uom_id,
        default_code=default_code,
        name=name,
        list_price="120",
        standard_price="0",
    )
    initial_profile = _profile_get(env, alias, run_id, product_id)
    if (
        initial_profile["product"]["id"] != product_id
        or initial_profile["template"]["id"] != template_id
        or initial_profile["category"]["id"] != category_id
    ):
        raise RuntimeError("the initial product accounting profile is inconsistent")

    _assert_product_result(
        _write(
            env,
            alias,
            run_id,
            "product.update",
            {
                "product_id": product_id,
                "changes": {"name": updated_name, "list_price": "125.5"},
            },
        ),
        state="active",
        product_id=product_id,
        template_id=template_id,
    )
    _assert_product_read(
        _product_get(env, alias, run_id, product_id),
        product_id=product_id,
        template_id=template_id,
        category_id=category_id,
        uom_id=uom_id,
        default_code=default_code,
        name=updated_name,
        list_price="125.5",
        standard_price="0",
    )

    _assert_product_result(
        _write(
            env,
            alias,
            run_id,
            "product.cost.update",
            {"product_id": product_id, "standard_price": "37.5"},
        ),
        state="active",
        product_id=product_id,
        template_id=template_id,
    )
    _assert_product_read(
        _product_get(env, alias, run_id, product_id),
        product_id=product_id,
        template_id=template_id,
        category_id=category_id,
        uom_id=uom_id,
        default_code=default_code,
        name=updated_name,
        list_price="125.5",
        standard_price="37.5",
    )

    category_profile = _write(
        env,
        alias,
        run_id,
        "product.category.accounting_profile.update",
        {
            "category_id": category_id,
            "changes": {
                "income_account_id": fixture["income_account_id"],
                "expense_account_id": fixture["expense_account_id"],
            },
        },
    )
    _assert_category_result(category_profile, category_id)
    _assert_profile_accounts(
        _profile_get(env, alias, run_id, product_id),
        product_id=product_id,
        template_id=template_id,
        category_id=category_id,
        income_account_id=fixture["income_account_id"],
        expense_account_id=fixture["expense_account_id"],
    )

    _assert_product_result(
        _write(
            env,
            alias,
            run_id,
            "product.accounting_profile.update",
            {
                "product_id": product_id,
                "changes": {
                    "income_account_id": fixture["income_account_id"],
                    "expense_account_id": fixture["expense_account_id"],
                    "sale_tax_ids": [fixture["sale_tax_id"]],
                    "purchase_tax_ids": [fixture["purchase_tax_id"]],
                },
            },
        ),
        state="active",
        product_id=product_id,
        template_id=template_id,
    )
    _assert_profile_accounts(
        _profile_get(env, alias, run_id, product_id),
        product_id=product_id,
        template_id=template_id,
        category_id=category_id,
        income_account_id=fixture["income_account_id"],
        expense_account_id=fixture["expense_account_id"],
    )
    template = env["product.template"].with_company(env.company).browse(template_id)
    if (
        template.property_account_income_id.id != fixture["income_account_id"]
        or template.property_account_expense_id.id != fixture["expense_account_id"]
        or sorted(template.taxes_id.ids) != [fixture["sale_tax_id"]]
        or sorted(template.supplier_taxes_id.ids) != [fixture["purchase_tax_id"]]
    ):
        raise RuntimeError("product accounting accounts or taxes were not persisted")

    duplicated = _write(
        env,
        alias,
        run_id,
        "product.duplicate",
        {
            "product_id": product_id,
            "name": f"{marker} Service Copy",
            "default_code": duplicate_code,
        },
    )
    duplicate_id, duplicate_template_id = _assert_product_result(
        duplicated, state="active"
    )
    if duplicate_id == product_id or duplicate_template_id == template_id:
        raise RuntimeError("product.duplicate reused the source product or template")
    _assert_product_read(
        _product_get(env, alias, run_id, duplicate_id),
        product_id=duplicate_id,
        template_id=duplicate_template_id,
        category_id=category_id,
        uom_id=uom_id,
        default_code=duplicate_code,
        name=f"{marker} Service Copy",
        list_price="125.5",
        standard_price=None,
    )
    duplicate_template = env["product.template"].browse(duplicate_template_id)
    if len(duplicate_template.product_variant_ids) != 1:
        raise RuntimeError("product.duplicate created more than one variant")

    env.flush_all()
    admin_env.invalidate_all()
    orderpoint = admin_env["stock.warehouse.orderpoint"].create(
        {
            "name": f"{marker} Orderpoint",
            "product_id": product_id,
            "warehouse_id": fixture["warehouse_id"],
            "location_id": fixture["location_id"],
            "company_id": _COMPANY_ID,
            "trigger": "manual",
            "product_min_qty": 0.0,
            "product_max_qty": 0.0,
        }
    )
    admin_env.flush_all()
    if len(orderpoint) != 1 or not orderpoint.active:
        raise RuntimeError("the attached orderpoint fixture was not created")
    orderpoint_id = orderpoint.id

    _assert_product_result(
        _write(
            env,
            alias,
            run_id,
            "product.archive",
            {"product_id": product_id},
        ),
        state="archived",
        product_id=product_id,
        template_id=template_id,
    )
    archived = (
        env["product.product"]
        .with_context(active_test=False)
        .browse(product_id)
        .exists()
    )
    if not archived or archived.active:
        raise RuntimeError("product.archive left the product active")
    archived_orderpoint = (
        env["stock.warehouse.orderpoint"]
        .with_context(active_test=False)
        .browse(orderpoint_id)
        .exists()
    )
    if not archived_orderpoint or archived_orderpoint.active:
        raise RuntimeError("product.archive left the attached orderpoint active")

    _assert_product_result(
        _write(
            env,
            alias,
            run_id,
            "product.restore",
            {"product_id": product_id},
        ),
        state="active",
        product_id=product_id,
        template_id=template_id,
    )
    restored = (
        env["product.product"]
        .with_context(active_test=False)
        .browse(product_id)
        .exists()
    )
    if not restored or not restored.active:
        raise RuntimeError("product.restore left the product archived")
    restored_orderpoint = (
        env["stock.warehouse.orderpoint"]
        .with_context(active_test=False)
        .browse(orderpoint_id)
        .exists()
    )
    if not restored_orderpoint or not restored_orderpoint.active:
        raise RuntimeError("product.restore left the attached orderpoint archived")

    return {
        "product.product": {product_id, duplicate_id},
        "product.template": {template_id, duplicate_template_id},
        "stock.warehouse.orderpoint": {orderpoint_id},
    }


def _verify_rollback(
    registry: Any,
    *,
    artifacts: dict[str, set[int]],
    fixture: dict[str, Any],
    group_ids: dict[str, int],
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
        survivors = {
            model: env[model].search_count([("id", "in", sorted(ids))])
            for model, ids in artifacts.items()
            if ids
        }
        survivors.update(
            {
                "template_marker": env["product.template"].search_count(
                    [("name", "ilike", marker)]
                ),
                "variant_marker": env["product.product"].search_count(
                    [("default_code", "ilike", marker)]
                ),
                "orderpoint_marker": env["stock.warehouse.orderpoint"].search_count(
                    [("name", "ilike", marker)]
                ),
            }
        )
        if any(survivors.values()):
            raise RuntimeError(f"product fixtures survived rollback: {survivors}")

        expected_value_ids = fixture["product_value_ids"]
        if expected_value_ids is not None and _value_ids(env) != expected_value_ids:
            raise RuntimeError("product.value rows changed across outer rollback")

        company = env["res.company"].browse(_COMPANY_ID)
        category = (
            env["product.category"]
            .with_company(company)
            .browse(fixture["category_id"])
            .exists()
        )
        if not category or _category_accounts(category) != fixture["category_accounts"]:
            raise RuntimeError("product category accounting values survived rollback")
        surviving_groups = [
            external_id
            for external_id, group_id in group_ids.items()
            if _direct_group_membership(cursor, group_id)
        ]
        if surviving_groups:
            raise RuntimeError(
                f"temporary group memberships survived rollback: {surviving_groups}"
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
    marker = f"ODACV4-PRODUCT-{args.alias}-{args.run_id.hex}"
    fixture: dict[str, Any] | None = None
    artifacts: dict[str, set[int]] = {
        "product.product": set(),
        "product.template": set(),
        "stock.warehouse.orderpoint": set(),
    }
    group_ids: dict[str, int] | None = None
    failure: BaseException | None = None
    try:
        context = {
            "allowed_company_ids": [_COMPANY_ID],
            "active_test": False,
            "lang": "en_US",
            "tz": "Asia/Shanghai",
        }
        admin_env = api.Environment(cursor, SUPERUSER_ID, context)
        company = admin_env["res.company"].browse(_COMPANY_ID).exists()
        user = admin_env["res.users"].with_context(active_test=False).browse(_USER_ID)
        group_ids = {
            external_id: admin_env.ref(external_id).id
            for external_id in _TEMPORARY_GROUPS
        }
        if (
            not company
            or not user.exists()
            or user.login != _USER_LOGIN
            or not user.active
            or company not in user.company_ids
        ):
            raise RuntimeError(
                "the configured company or fixed accountant is unavailable"
            )
        existing_groups = [
            external_id
            for external_id, group_id in group_ids.items()
            if user.has_group(external_id) or _direct_group_membership(cursor, group_id)
        ]
        if existing_groups:
            raise RuntimeError(
                "uid 5 already has temporary-fixture access; the precondition is "
                f"false for {existing_groups}"
            )

        fixture = _fixture(admin_env)
        user.write(
            {"group_ids": [Command.link(group_id) for group_id in group_ids.values()]}
        )
        admin_env.flush_all()
        missing_grants = [
            external_id
            for external_id, group_id in group_ids.items()
            if not _direct_group_membership(cursor, group_id)
        ]
        if missing_grants:
            raise RuntimeError(
                f"temporary group grants were not persisted: {missing_grants}"
            )

        business_env = api.Environment(
            cursor,
            _USER_ID,
            {
                "allowed_company_ids": [_COMPANY_ID],
                "active_test": True,
                "lang": "en_US",
                "tz": "Asia/Shanghai",
            },
        )
        if (
            business_env.uid != _USER_ID
            or business_env.su
            or business_env.user.login != _USER_LOGIN
            or not business_env.user.has_group("account.group_account_user")
            or not business_env.user.has_group(_MANAGER_GROUP)
            or not business_env.user.has_group(_STOCK_MANAGER_GROUP)
        ):
            raise RuntimeError(
                "uid 5 or its temporary product/stock groups are unavailable"
            )
        artifacts = _exercise(
            business_env,
            admin_env,
            args.alias,
            args.run_id,
            marker,
            fixture,
        )
    except BaseException as exc:  # noqa: BLE001 - rollback precedes re-raising.
        failure = exc
    finally:
        cursor.rollback()
        cursor.close()

    rollback_failure: BaseException | None = None
    if fixture is not None and group_ids is not None:
        try:
            _verify_rollback(
                registry,
                artifacts=artifacts,
                fixture=fixture,
                group_ids=group_ids,
                marker=marker,
            )
        except BaseException as exc:  # noqa: BLE001 - preserve capability failure.
            rollback_failure = exc
    if failure is not None:
        if rollback_failure is not None:
            failure.add_note(f"rollback verification also failed: {rollback_failure}")
        raise failure
    if rollback_failure is not None:
        raise rollback_failure
    if fixture is None or group_ids is None or not all(artifacts.values()):
        raise RuntimeError(
            "the product accounting rollback fixture was not initialized"
        )

    sys.stdout.write(
        json.dumps(
            {
                "alias": args.alias,
                "business_su": False,
                "capabilities": list(_WRITE_CAPABILITIES),
                "company_id": _COMPANY_ID,
                "database": args.database,
                "default_product_manager_authorized": False,
                "default_stock_manager_authorized": False,
                "immediate_replays": len(_WRITE_CAPABILITIES),
                "orderpoint_active_state_verified": True,
                "rollback_verified": True,
                "temporary_group_fixtures": list(_TEMPORARY_GROUPS),
                "temporary_groups_rolled_back": True,
                "user_id": _USER_ID,
                "verification_reads": list(_VERIFICATION_READS),
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
