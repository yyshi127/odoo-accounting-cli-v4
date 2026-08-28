"""Odoo-side runtime for five fixed inventory-operation reads."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

ACTION = "accounting.inventory_operations.read"
CAPABILITY_IDS = frozenset(
    {
        "stock.transfer.search",
        "stock.transfer.get",
        "stock.move.search",
        "inventory.on_hand.summary",
        "inventory.availability.inspect",
    }
)
_SEARCH_CAPABILITIES = frozenset({"stock.transfer.search", "stock.move.search"})
_TRANSFER_STATES = frozenset(
    {"draft", "waiting", "confirmed", "assigned", "done", "cancel"}
)
_MOVE_STATES = frozenset(
    {
        "draft",
        "waiting",
        "confirmed",
        "partially_available",
        "assigned",
        "done",
        "cancel",
    }
)
_PICKING_FIELDS = {
    "company_id",
    "name",
    "origin",
    "state",
    "picking_type_id",
    "scheduled_date",
    "date_done",
    "location_id",
    "location_dest_id",
    "partner_id",
}
_MOVE_FIELDS = {
    "company_id",
    "reference",
    "description_picking",
    "state",
    "date",
    "picking_id",
    "product_id",
    "product_uom",
    "product_uom_qty",
    "quantity",
    "location_id",
    "location_dest_id",
}
_QUANT_FIELDS = {
    "company_id",
    "product_id",
    "location_id",
    "quantity",
    "reserved_quantity",
}
_PRODUCT_FIELDS = {
    "company_id",
    "default_code",
    "display_name",
    "uom_id",
    "is_storable",
}
_AVAILABILITY_FIELDS = {
    "qty_available",
    "free_qty",
    "incoming_qty",
    "outgoing_qty",
    "virtual_available",
}


def _failure(failure_type: Any, code: str, message: str, exit_code: int) -> Exception:
    return failure_type(code, message, exit_code=exit_code)


def _protocol_failure(failure_type: Any) -> Exception:
    return _failure(
        failure_type,
        "bridge_protocol_error",
        "The bridge action payload is invalid.",
        7,
    )


def _runtime_failure(failure_type: Any) -> Exception:
    return _failure(
        failure_type,
        "odoo_runtime_error",
        "The Odoo runtime request failed.",
        7,
    )


def _integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _positive_id(value: Any) -> bool:
    return _integer(value) and value > 0


def _optional_id(value: Any) -> bool:
    return value is None or _positive_id(value)


def _optional_state(value: Any, allowed: frozenset[str]) -> bool:
    return value is None or isinstance(value, str) and value in allowed


def _canonical_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _valid_range(parameters: dict[str, Any]) -> bool:
    date_from = parameters["date_from"]
    date_to = parameters["date_to"]
    return bool(
        (date_from is None or _canonical_date(date_from))
        and (date_to is None or _canonical_date(date_to))
        and (date_from is None or date_to is None or date_from <= date_to)
    )


def _valid_parameters(capability_id: str, parameters: Any) -> bool:
    if not isinstance(parameters, dict):
        return False
    if capability_id == "stock.transfer.get":
        return set(parameters) == {"transfer_id"} and _positive_id(
            parameters["transfer_id"]
        )
    if capability_id == "stock.transfer.search":
        return bool(
            set(parameters)
            == {
                "picking_type_id",
                "partner_id",
                "state",
                "date_from",
                "date_to",
                "after",
                "limit",
            }
            and _optional_id(parameters["picking_type_id"])
            and _optional_id(parameters["partner_id"])
            and _optional_state(parameters["state"], _TRANSFER_STATES)
            and _valid_range(parameters)
            and _optional_id(parameters["after"])
            and _integer(parameters["limit"])
            and 1 <= parameters["limit"] <= 1001
        )
    if capability_id == "stock.move.search":
        return bool(
            set(parameters)
            == {
                "transfer_id",
                "product_id",
                "state",
                "date_from",
                "date_to",
                "after",
                "limit",
            }
            and _optional_id(parameters["transfer_id"])
            and _optional_id(parameters["product_id"])
            and _optional_state(parameters["state"], _MOVE_STATES)
            and _valid_range(parameters)
            and _optional_id(parameters["after"])
            and _integer(parameters["limit"])
            and 1 <= parameters["limit"] <= 1001
        )
    if capability_id == "inventory.on_hand.summary":
        return bool(
            set(parameters) == {"warehouse_id", "location_id", "product_id"}
            and all(_optional_id(parameters[key]) for key in parameters)
        )
    return bool(
        set(parameters) == {"product_id", "warehouse_id", "location_id"}
        and _positive_id(parameters["product_id"])
        and _optional_id(parameters["warehouse_id"])
        and _optional_id(parameters["location_id"])
        and not (
            parameters["warehouse_id"] is not None
            and parameters["location_id"] is not None
        )
    )


def _validated_payload(
    payload: Any, company_id: int, failure_type: Any
) -> tuple[str, dict[str, Any]]:
    if (
        not isinstance(payload, dict)
        or set(payload) != {"capability_id", "company_id", "parameters"}
        or not isinstance(payload.get("capability_id"), str)
        or payload["capability_id"] not in CAPABILITY_IDS
        or not _positive_id(payload.get("company_id"))
        or payload.get("company_id") != company_id
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


def _required_models(capability_id: str) -> tuple[str, ...]:
    if capability_id.startswith("stock.transfer"):
        return (
            "res.company",
            "stock.picking",
            "stock.picking.type",
            "stock.location",
            "res.partner",
        )
    if capability_id == "stock.move.search":
        return (
            "res.company",
            "stock.move",
            "stock.picking",
            "product.product",
            "uom.uom",
            "stock.location",
        )
    models = (
        "res.company",
        "stock.quant",
        "stock.move",
        "stock.location",
        "stock.warehouse",
        "product.product",
        "uom.uom",
    )
    if capability_id == "inventory.on_hand.summary":
        return tuple(name for name in models if name != "stock.move")
    return models


def _fields(env: Any, model: str, required: set[str]) -> bool:
    return required <= set(getattr(env[model], "_fields", {}))


def _field_shape_available(env: Any, capability_id: str) -> bool:
    if capability_id.startswith("stock.transfer"):
        return bool(
            _fields(env, "stock.picking", _PICKING_FIELDS)
            and _fields(
                env,
                "stock.picking.type",
                {"company_id", "code", "display_name"},
            )
            and _fields(env, "stock.location", {"company_id", "complete_name"})
            and _fields(env, "res.partner", {"display_name"})
        )
    if capability_id == "stock.move.search":
        return bool(
            _fields(env, "stock.move", _MOVE_FIELDS)
            and _fields(env, "stock.picking", {"company_id", "name"})
            and _fields(env, "product.product", _PRODUCT_FIELDS)
            and _fields(env, "uom.uom", {"display_name"})
            and _fields(env, "stock.location", {"company_id", "complete_name"})
        )
    common = bool(
        _fields(env, "stock.quant", _QUANT_FIELDS)
        and _fields(env, "stock.location", {"company_id", "complete_name", "usage"})
        and _fields(
            env,
            "stock.warehouse",
            {"company_id", "code", "name", "lot_stock_id"},
        )
        and _fields(env, "product.product", _PRODUCT_FIELDS)
        and _fields(env, "uom.uom", {"display_name"})
    )
    return common and (
        capability_id == "inventory.on_hand.summary"
        or _fields(env, "product.product", _AVAILABILITY_FIELDS)
    )


def _scope_page(
    env: Any, capability_id: str, company_id: int, failure_type: Any
) -> dict[str, Any]:
    company_visible = bool(
        env["res.company"].search_count([("id", "=", company_id)], limit=1)
    )
    models = _required_models(capability_id)
    module_installed = all(env.registry.get(name) is not None for name in models)
    if (
        company_visible
        and module_installed
        and not _field_shape_available(env, capability_id)
    ):
        raise _runtime_failure(failure_type)
    access_allowed = bool(
        company_visible
        and module_installed
        and env.user.has_group("account.group_account_readonly")
        and all(env[name].has_access("read") for name in models)
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


def _record_id(value: Any) -> int:
    record_id = getattr(value, "id", value)
    if not _positive_id(record_id):
        raise ValueError("invalid record id")
    return record_id


def _text(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("invalid text")
    return value


def _optional_text(value: Any) -> str | None:
    return None if value in (None, False) else _text(value)


def _company_id(record: Any) -> int | None:
    company = getattr(record, "company_id", None)
    if not company:
        return None
    return _record_id(company)


def _company_matches(record: Any, company_id: int, *, shared: bool = False) -> bool:
    record_company = _company_id(record)
    return record_company == company_id or shared and record_company is None


def _named_ref(record: Any, *, field: str = "display_name") -> dict[str, Any]:
    return {"id": _record_id(record), "name": _text(getattr(record, field))}


def _optional_named_ref(
    record: Any, *, field: str = "display_name"
) -> dict[str, Any] | None:
    return None if not record else _named_ref(record, field=field)


def _coded_ref(record: Any, *, name_field: str = "display_name") -> dict[str, Any]:
    return {
        "id": _record_id(record),
        "code": _text(record.code),
        "name": _text(getattr(record, name_field)),
    }


def _product_ref(record: Any) -> dict[str, Any]:
    return {
        "id": _record_id(record),
        "code": _optional_text(record.default_code),
        "name": _text(record.display_name),
    }


def _decimal(value: Any) -> Decimal:
    if isinstance(value, bool):
        raise TypeError("invalid decimal")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("invalid decimal") from exc
    if not number.is_finite():
        raise ValueError("invalid decimal")
    return number


def _decimal_text(value: Any) -> str:
    number = _decimal(value)
    if number == 0:
        return "0"
    rendered = format(number, "f")
    return rendered.rstrip("0").rstrip(".") if "." in rendered else rendered


def _utc_text(value: Any) -> str | None:
    if value in (None, False):
        return None
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value)
    elif isinstance(value, datetime):
        parsed = value
    else:
        raise TypeError("invalid datetime")
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(UTC).replace(tzinfo=None)
    return parsed.replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def _date_domain(field: str, parameters: dict[str, Any]) -> list[Any]:
    domain: list[Any] = []
    if parameters["date_from"] is not None:
        start = datetime.combine(date.fromisoformat(parameters["date_from"]), time())
        domain.append((field, ">=", start.strftime("%Y-%m-%d %H:%M:%S")))
    if parameters["date_to"] is not None:
        end = datetime.combine(
            date.fromisoformat(parameters["date_to"]) + timedelta(days=1), time()
        )
        domain.append((field, "<", end.strftime("%Y-%m-%d %H:%M:%S")))
    return domain


def _search_records(
    env: Any,
    model_name: str,
    company_id: int,
    base_domain: list[Any],
    parameters: dict[str, Any],
) -> tuple[bool, list[Any]]:
    model = _model(env, model_name, company_id)
    after = parameters["after"]
    if after is not None and not model.search_count(
        [*base_domain, ("id", "=", after)], limit=1
    ):
        return False, []
    domain = [*base_domain]
    if after is not None:
        domain.append(("id", "<", after))
    return True, list(model.search(domain, order="id desc", limit=parameters["limit"]))


def _transfer_domain(company_id: int, parameters: dict[str, Any]) -> list[Any]:
    domain: list[Any] = [
        ("company_id", "=", company_id),
    ]
    for key in ("picking_type_id", "partner_id", "state"):
        if parameters.get(key) is not None:
            domain.append((key, "=", parameters[key]))
    return [*domain, *_date_domain("scheduled_date", parameters)]


def _transfer(record: Any, company_id: int) -> dict[str, Any]:
    if not _company_matches(record, company_id):
        raise ValueError("cross-company transfer")
    picking_type = record.picking_type_id
    source = record.location_id
    destination = record.location_dest_id
    if (
        not _company_matches(picking_type, company_id)
        or not _company_matches(source, company_id, shared=True)
        or not _company_matches(destination, company_id, shared=True)
    ):
        raise ValueError("cross-company transfer reference")
    return {
        "id": _record_id(record),
        "company_id": company_id,
        "name": _text(record.name),
        "origin": _optional_text(record.origin),
        "state": record.state,
        "operation_type": _coded_ref(picking_type),
        "scheduled_date": _utc_text(record.scheduled_date),
        "completed_date": _utc_text(record.date_done),
        "source_location": _named_ref(source, field="complete_name"),
        "destination_location": _named_ref(destination, field="complete_name"),
        "partner": _optional_named_ref(record.partner_id),
    }


def _transfer_items(
    env: Any, company_id: int, parameters: dict[str, Any]
) -> tuple[bool, list[dict[str, Any]]]:
    cursor_found, records = _search_records(
        env,
        "stock.picking",
        company_id,
        _transfer_domain(company_id, parameters),
        parameters,
    )
    return cursor_found, [_transfer(record, company_id) for record in records]


def _transfer_item(
    env: Any, company_id: int, parameters: dict[str, Any]
) -> dict[str, Any] | None:
    records = _model(env, "stock.picking", company_id).search(
        [
            ("id", "=", parameters["transfer_id"]),
            ("company_id", "=", company_id),
        ],
        limit=2,
    )
    if len(records) > 1:
        raise ValueError("ambiguous transfer")
    return None if not records else _transfer(records[0], company_id)


def _move_domain(company_id: int, parameters: dict[str, Any]) -> list[Any]:
    domain: list[Any] = [("company_id", "=", company_id)]
    field_map = {
        "transfer_id": "picking_id",
        "product_id": "product_id",
        "state": "state",
    }
    for key, field in field_map.items():
        if parameters[key] is not None:
            domain.append((field, "=", parameters[key]))
    return [*domain, *_date_domain("date", parameters)]


def _move(record: Any, company_id: int) -> dict[str, Any]:
    if not _company_matches(record, company_id):
        raise ValueError("cross-company stock move")
    transfer = record.picking_id
    product = record.product_id
    source = record.location_id
    destination = record.location_dest_id
    if (
        transfer
        and not _company_matches(transfer, company_id)
        or not _company_matches(product, company_id, shared=True)
        or not _company_matches(source, company_id, shared=True)
        or not _company_matches(destination, company_id, shared=True)
    ):
        raise ValueError("cross-company stock-move reference")
    return {
        "id": _record_id(record),
        "company_id": company_id,
        "reference": _optional_text(record.reference),
        "description_picking": _optional_text(record.description_picking),
        "state": record.state,
        "date": _utc_text(record.date),
        "transfer": _optional_named_ref(transfer, field="name"),
        "product": _product_ref(product),
        "uom": _named_ref(record.product_uom),
        "demand_quantity": _decimal_text(record.product_uom_qty),
        "moved_quantity": _decimal_text(record.quantity),
        "source_location": _named_ref(source, field="complete_name"),
        "destination_location": _named_ref(destination, field="complete_name"),
    }


def _move_items(
    env: Any, company_id: int, parameters: dict[str, Any]
) -> tuple[bool, list[dict[str, Any]]]:
    cursor_found, records = _search_records(
        env,
        "stock.move",
        company_id,
        _move_domain(company_id, parameters),
        parameters,
    )
    return cursor_found, [_move(record, company_id) for record in records]


def _warehouse(env: Any, company_id: int, warehouse_id: int | None) -> Any | None:
    if warehouse_id is None:
        return None
    records = _model(env, "stock.warehouse", company_id).search(
        [("id", "=", warehouse_id), ("company_id", "=", company_id)], limit=2
    )
    if len(records) > 1:
        raise ValueError("ambiguous warehouse")
    return records[0] if records else None


def _location(
    env: Any,
    company_id: int,
    location_id: int | None,
    *,
    warehouse: Any | None = None,
) -> Any | None:
    if location_id is None:
        return None
    domain: list[Any] = [
        ("id", "=", location_id),
        "|",
        ("company_id", "=", False),
        ("company_id", "=", company_id),
    ]
    if warehouse is not None:
        domain.append(("id", "child_of", _record_id(warehouse.lot_stock_id)))
    records = _model(env, "stock.location", company_id).search(domain, limit=2)
    if len(records) > 1:
        raise ValueError("ambiguous location")
    return records[0] if records else None


def _product(env: Any, company_id: int, product_id: int | None) -> Any | None:
    if product_id is None:
        return None
    records = _model(env, "product.product", company_id).search(
        [
            ("id", "=", product_id),
            "|",
            ("company_id", "=", False),
            ("company_id", "=", company_id),
            ("is_storable", "=", True),
        ],
        limit=2,
    )
    if len(records) > 1:
        raise ValueError("ambiguous product")
    return records[0] if records else None


def _scope_records(
    env: Any, company_id: int, parameters: dict[str, Any]
) -> tuple[Any | None, Any | None, Any | None] | None:
    warehouse = _warehouse(env, company_id, parameters["warehouse_id"])
    if parameters["warehouse_id"] is not None and warehouse is None:
        return None
    location = _location(
        env,
        company_id,
        parameters["location_id"],
        warehouse=warehouse,
    )
    if parameters["location_id"] is not None and location is None:
        return None
    product = _product(env, company_id, parameters["product_id"])
    if parameters["product_id"] is not None and product is None:
        return None
    return warehouse, location, product


def _summary_item(
    env: Any, company_id: int, parameters: dict[str, Any]
) -> dict[str, Any] | None:
    scope = _scope_records(env, company_id, parameters)
    if scope is None:
        return None
    warehouse, location, requested_product = scope
    domain: list[Any] = [
        ("company_id", "=", company_id),
        ("location_id.usage", "=", "internal"),
    ]
    if warehouse is not None:
        domain.append(("location_id", "child_of", _record_id(warehouse.lot_stock_id)))
    if location is not None:
        domain.append(("location_id", "child_of", _record_id(location)))
    if requested_product is not None:
        domain.append(("product_id", "=", _record_id(requested_product)))
    rows = _model(env, "stock.quant", company_id)._read_group(
        domain,
        groupby=["product_id"],
        aggregates=["quantity:sum", "reserved_quantity:sum"],
        order="product_id asc",
    )
    groups: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, (tuple, list)) or len(row) != 3:
            raise ValueError("invalid stock-quant aggregate")
        product = row[0]
        if (
            not product
            or not _company_matches(product, company_id, shared=True)
            or not product.is_storable
        ):
            raise ValueError("invalid stock-quant product")
        quantity = _decimal(row[1])
        reserved = _decimal(row[2])
        groups.append(
            {
                "product": _product_ref(product),
                "uom": _named_ref(product.uom_id),
                "quantity": _decimal_text(quantity),
                "reserved_quantity": _decimal_text(reserved),
                "available_quantity": _decimal_text(quantity - reserved),
            }
        )
    if requested_product is not None and not groups:
        groups.append(
            {
                "product": _product_ref(requested_product),
                "uom": _named_ref(requested_product.uom_id),
                "quantity": "0",
                "reserved_quantity": "0",
                "available_quantity": "0",
            }
        )
    groups.sort(key=lambda item: item["product"]["id"])
    ids = [item["product"]["id"] for item in groups]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate stock-quant aggregate")
    return {
        "company_id": company_id,
        "warehouse": (
            None if warehouse is None else _coded_ref(warehouse, name_field="name")
        ),
        "location": (
            None if location is None else _named_ref(location, field="complete_name")
        ),
        "groups": groups,
    }


def _availability_item(
    env: Any, company_id: int, parameters: dict[str, Any]
) -> dict[str, Any] | None:
    scope = _scope_records(env, company_id, parameters)
    if scope is None:
        return None
    warehouse, location, product = scope
    if product is None:
        raise ValueError("availability requires product")
    context: dict[str, Any] = {
        "allowed_company_ids": [company_id],
        "active_test": False,
    }
    if warehouse is not None:
        context["warehouse_id"] = _record_id(warehouse)
    if location is not None:
        context["location"] = _record_id(location)
    product = product.with_company(company_id).with_context(**context)
    return {
        "company_id": company_id,
        "product": _product_ref(product),
        "warehouse": (
            None if warehouse is None else _coded_ref(warehouse, name_field="name")
        ),
        "location": (
            None if location is None else _named_ref(location, field="complete_name")
        ),
        "uom": _named_ref(product.uom_id),
        "on_hand_quantity": _decimal_text(product.qty_available),
        "free_quantity": _decimal_text(product.free_qty),
        "incoming_quantity": _decimal_text(product.incoming_qty),
        "outgoing_quantity": _decimal_text(product.outgoing_qty),
        "forecast_quantity": _decimal_text(product.virtual_available),
    }


def dispatch(
    env: Any,
    payload: dict[str, Any],
    company_id: int,
    *,
    failure_type: Any,
) -> dict[str, Any]:
    """Validate, gate, and execute one allowlisted inventory-operation read."""

    try:
        capability_id, parameters = _validated_payload(
            payload, company_id, failure_type
        )
        page = _scope_page(env, capability_id, company_id, failure_type)
        if not page["access_allowed"]:
            return page
        if capability_id == "stock.transfer.search":
            cursor_found, items = _transfer_items(env, company_id, parameters)
        elif capability_id == "stock.transfer.get":
            cursor_found = True
            item = _transfer_item(env, company_id, parameters)
            items = [] if item is None else [item]
        elif capability_id == "stock.move.search":
            cursor_found, items = _move_items(env, company_id, parameters)
        elif capability_id == "inventory.on_hand.summary":
            cursor_found = True
            item = _summary_item(env, company_id, parameters)
            items = [] if item is None else [item]
        else:
            cursor_found = True
            item = _availability_item(env, company_id, parameters)
            items = [] if item is None else [item]
        return {**page, "cursor_found": cursor_found, "items": items}
    except failure_type:
        raise
    except Exception as exc:
        raise _runtime_failure(failure_type) from exc
