"""Odoo-side runtime for five fixed inventory master-data lists."""

from __future__ import annotations

from typing import Any

ACTION = "accounting.inventory_master.read"
CAPABILITY_IDS = frozenset(
    {
        "product.category.list",
        "warehouse.list",
        "stock.location.list",
        "stock.operation_type.list",
        "stock.route.list",
    }
)
_MODELS = {
    "product.category.list": "product.category",
    "warehouse.list": "stock.warehouse",
    "stock.location.list": "stock.location",
    "stock.operation_type.list": "stock.picking.type",
    "stock.route.list": "stock.route",
}
_OUTPUT_FIELDS = {
    "product.category.list": ["name", "complete_name", "parent_id"],
    "warehouse.list": [
        "name",
        "code",
        "active",
        "company_id",
        "reception_steps",
        "delivery_steps",
    ],
    "stock.location.list": [
        "name",
        "complete_name",
        "active",
        "usage",
        "company_id",
        "location_id",
        "warehouse_id",
    ],
    "stock.operation_type.list": [
        "name",
        "active",
        "code",
        "sequence_code",
        "company_id",
        "warehouse_id",
        "default_location_src_id",
        "default_location_dest_id",
    ],
    "stock.route.list": [
        "name",
        "active",
        "sequence",
        "company_id",
        "product_selectable",
        "product_categ_selectable",
        "warehouse_selectable",
        "warehouse_ids",
    ],
}


def _failure(failure_type: Any, code: str, message: str, exit_code: int) -> Exception:
    return failure_type(code, message, exit_code=exit_code)


def _protocol_failure(failure_type: Any) -> Exception:
    return _failure(
        failure_type,
        "bridge_protocol_error",
        "The inventory-master bridge payload is invalid.",
        7,
    )


def _runtime_failure(failure_type: Any) -> Exception:
    return _failure(
        failure_type,
        "odoo_runtime_error",
        "The inventory-master Odoo runtime request failed.",
        7,
    )


def _integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _positive_id(value: Any) -> bool:
    return _integer(value) and value > 0


def _valid_parameters(capability_id: str, parameters: Any) -> bool:
    if not isinstance(parameters, dict):
        return False
    expected = {"after", "limit"}
    if capability_id == "product.category.list":
        expected.add("parent_id")
    else:
        expected.add("active")
    if capability_id == "stock.location.list":
        expected.update({"warehouse_id", "usage"})
    elif capability_id == "stock.operation_type.list":
        expected.update({"warehouse_id", "code"})
    elif capability_id == "stock.route.list":
        expected.add("warehouse_id")
    if set(parameters) != expected:
        return False
    if not (
        (parameters["after"] is None or _positive_id(parameters["after"]))
        and _integer(parameters["limit"])
        and 1 <= parameters["limit"] <= 1001
    ):
        return False
    if capability_id == "product.category.list":
        return parameters["parent_id"] is None or _positive_id(parameters["parent_id"])
    if parameters["active"] is not None and not isinstance(parameters["active"], bool):
        return False
    if capability_id == "stock.location.list":
        return bool(
            (
                parameters["warehouse_id"] is None
                or _positive_id(parameters["warehouse_id"])
            )
            and parameters["usage"]
            in {
                None,
                "supplier",
                "view",
                "internal",
                "customer",
                "inventory",
                "production",
                "transit",
            }
        )
    if capability_id == "stock.operation_type.list":
        code = parameters["code"]
        return bool(
            (
                parameters["warehouse_id"] is None
                or _positive_id(parameters["warehouse_id"])
            )
            and (
                code is None
                or isinstance(code, str)
                and bool(code.strip())
                and len(code) <= 64
            )
        )
    if capability_id == "stock.route.list":
        return parameters["warehouse_id"] is None or _positive_id(
            parameters["warehouse_id"]
        )
    return True


def _validated_payload(
    payload: Any, company_id: int, failure_type: Any
) -> tuple[str, dict[str, Any]]:
    if (
        not isinstance(payload, dict)
        or set(payload) != {"capability_id", "company_id", "parameters"}
        or payload["company_id"] != company_id
        or payload["capability_id"] not in CAPABILITY_IDS
        or not _valid_parameters(payload["capability_id"], payload["parameters"])
    ):
        raise _protocol_failure(failure_type)
    return payload["capability_id"], payload["parameters"]


def _empty_page(
    env: Any,
    *,
    company_visible: bool,
    module_installed: bool,
    access_allowed: bool,
) -> dict[str, Any]:
    return {
        "user_id": env.uid,
        "company_visible": company_visible,
        "module_installed": module_installed,
        "access_allowed": access_allowed,
        "cursor_found": True,
        "items": [],
    }


def _scope_page(
    env: Any, capability_id: str, company_id: int, failure_type: Any
) -> dict[str, Any]:
    company_visible = bool(
        env["res.company"].search_count([("id", "=", company_id)], limit=1)
    )
    model_name = _MODELS[capability_id]
    module_installed = env.registry.get(model_name) is not None
    if (
        company_visible
        and module_installed
        and not set(_OUTPUT_FIELDS[capability_id])
        <= set(getattr(env[model_name], "_fields", {}))
    ):
        raise _runtime_failure(failure_type)
    access_allowed = bool(
        company_visible
        and module_installed
        and env.user.has_group("account.group_account_readonly")
        and env["res.company"].has_access("read")
        and env[model_name].has_access("read")
    )
    return _empty_page(
        env,
        company_visible=company_visible,
        module_installed=module_installed,
        access_allowed=access_allowed,
    )


def _model(env: Any, name: str, company_id: int) -> Any:
    return (
        env[name]
        .with_company(company_id)
        .with_context(allowed_company_ids=[company_id], active_test=False)
    )


def _domain(
    capability_id: str, company_id: int, parameters: dict[str, Any]
) -> list[Any]:
    if capability_id == "product.category.list":
        domain: list[Any] = []
    elif capability_id in {"warehouse.list", "stock.operation_type.list"}:
        domain = [("company_id", "=", company_id)]
    else:
        domain = [
            "|",
            ("company_id", "=", False),
            ("company_id", "=", company_id),
        ]
    if capability_id != "product.category.list" and parameters["active"] is not None:
        domain.append(("active", "=", parameters["active"]))
    if capability_id == "product.category.list" and parameters["parent_id"] is not None:
        domain.append(("parent_id", "=", parameters["parent_id"]))
    elif capability_id == "stock.location.list":
        if parameters["warehouse_id"] is not None:
            domain.append(("warehouse_id", "=", parameters["warehouse_id"]))
        if parameters["usage"] is not None:
            domain.append(("usage", "=", parameters["usage"]))
    elif capability_id == "stock.operation_type.list":
        if parameters["warehouse_id"] is not None:
            domain.append(("warehouse_id", "=", parameters["warehouse_id"]))
        if parameters["code"] is not None:
            domain.append(("code", "=", parameters["code"]))
    elif capability_id == "stock.route.list" and parameters["warehouse_id"] is not None:
        domain.append(("warehouse_ids", "in", [parameters["warehouse_id"]]))
    return domain


def _text(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("invalid text")
    return value


def _row_id(row: dict[str, Any]) -> int:
    value = row.get("id")
    if not _positive_id(value):
        raise ValueError("invalid row id")
    return value


def _reference_id(value: Any, *, required: bool = False) -> int | None:
    if value in (None, False):
        if required:
            raise ValueError("missing reference")
        return None
    if isinstance(value, (list, tuple)) and len(value) == 2:
        value = value[0]
    elif not _positive_id(value):
        value = getattr(value, "id", None)
    if not _positive_id(value):
        raise ValueError("invalid reference")
    return value


def _boolean(value: Any) -> bool:
    if not isinstance(value, bool):
        raise TypeError("invalid boolean")
    return value


def _sequence(value: Any) -> int:
    if not _integer(value):
        raise ValueError("invalid sequence")
    return value


def _category_item(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": _row_id(row),
        "name": _text(row.get("name")),
        "complete_name": _text(row.get("complete_name")),
        "parent_id": _reference_id(row.get("parent_id")),
    }


def _warehouse_item(row: dict[str, Any], company_id: int) -> dict[str, Any]:
    if _reference_id(row.get("company_id"), required=True) != company_id:
        raise ValueError("cross-company warehouse")
    return {
        "id": _row_id(row),
        "name": _text(row.get("name")),
        "code": _text(row.get("code")),
        "active": _boolean(row.get("active")),
        "company_id": company_id,
        "reception_steps": _text(row.get("reception_steps")),
        "delivery_steps": _text(row.get("delivery_steps")),
    }


def _location_item(row: dict[str, Any], company_id: int) -> dict[str, Any]:
    row_company_id = _reference_id(row.get("company_id"))
    if row_company_id not in {None, company_id}:
        raise ValueError("cross-company location")
    return {
        "id": _row_id(row),
        "name": _text(row.get("name")),
        "complete_name": _text(row.get("complete_name")),
        "active": _boolean(row.get("active")),
        "usage": _text(row.get("usage")),
        "company_id": row_company_id,
        "parent_id": _reference_id(row.get("location_id")),
        "warehouse_id": _reference_id(row.get("warehouse_id")),
    }


def _operation_item(row: dict[str, Any], company_id: int) -> dict[str, Any]:
    if _reference_id(row.get("company_id"), required=True) != company_id:
        raise ValueError("cross-company operation type")
    return {
        "id": _row_id(row),
        "name": _text(row.get("name")),
        "active": _boolean(row.get("active")),
        "code": _text(row.get("code")),
        "sequence_code": _text(row.get("sequence_code")),
        "company_id": company_id,
        "warehouse_id": _reference_id(row.get("warehouse_id")),
        "source_location_id": _reference_id(row.get("default_location_src_id")),
        "destination_location_id": _reference_id(row.get("default_location_dest_id")),
    }


def _route_item(row: dict[str, Any], company_id: int) -> dict[str, Any]:
    row_company_id = _reference_id(row.get("company_id"))
    if row_company_id not in {None, company_id}:
        raise ValueError("cross-company route")
    warehouse_ids = row.get("warehouse_ids")
    if not isinstance(warehouse_ids, list) or any(
        not _positive_id(value) for value in warehouse_ids
    ):
        raise ValueError("invalid route warehouses")
    return {
        "id": _row_id(row),
        "name": _text(row.get("name")),
        "active": _boolean(row.get("active")),
        "sequence": _sequence(row.get("sequence")),
        "company_id": row_company_id,
        "product_selectable": _boolean(row.get("product_selectable")),
        "product_category_selectable": _boolean(row.get("product_categ_selectable")),
        "warehouse_selectable": _boolean(row.get("warehouse_selectable")),
        "warehouse_ids": sorted(set(warehouse_ids)),
    }


def _item(capability_id: str, row: dict[str, Any], company_id: int) -> dict[str, Any]:
    if capability_id == "product.category.list":
        return _category_item(row)
    if capability_id == "warehouse.list":
        return _warehouse_item(row, company_id)
    if capability_id == "stock.location.list":
        return _location_item(row, company_id)
    if capability_id == "stock.operation_type.list":
        return _operation_item(row, company_id)
    return _route_item(row, company_id)


def _read_page(
    env: Any,
    capability_id: str,
    company_id: int,
    parameters: dict[str, Any],
) -> tuple[bool, list[dict[str, Any]]]:
    model = _model(env, _MODELS[capability_id], company_id)
    domain = _domain(capability_id, company_id, parameters)
    after = parameters["after"]
    if after is not None:
        if not model.search_count([*domain, ("id", "=", after)], limit=1):
            return False, []
        domain.append(("id", "<", after))
    rows = model.search_read(
        domain,
        _OUTPUT_FIELDS[capability_id],
        order="id desc",
        limit=parameters["limit"],
    )
    return True, [_item(capability_id, row, company_id) for row in rows]


def dispatch(
    env: Any,
    payload: dict[str, Any],
    company_id: int,
    *,
    failure_type: Any,
) -> dict[str, Any]:
    """Validate, gate, and execute one allowlisted inventory-master list."""

    try:
        capability_id, parameters = _validated_payload(
            payload, company_id, failure_type
        )
        page = _scope_page(env, capability_id, company_id, failure_type)
        if not page["access_allowed"]:
            return page
        cursor_found, items = _read_page(env, capability_id, company_id, parameters)
        return {**page, "cursor_found": cursor_found, "items": items}
    except failure_type:
        raise
    except Exception as exc:
        raise _runtime_failure(failure_type) from exc
