"""Odoo-side runtime for fixed sales and purchase order reads."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

ACTION = "accounting.order_documents.read"
CAPABILITY_IDS = frozenset(
    {
        "sale.order.search",
        "sale.order.get",
        "sale.order.line.search",
        "sale.order.analysis.summary",
        "purchase.order.search",
        "purchase.order.get",
        "purchase.order.line.search",
        "purchase.order.analysis.summary",
    }
)

_SALE_STATES = frozenset({"draft", "sent", "sale", "cancel"})
_PURCHASE_STATES = frozenset({"draft", "sent", "to approve", "purchase", "cancel"})
_SALE_INVOICE_STATUSES = frozenset({"no", "to invoice", "invoiced", "upselling"})
_PURCHASE_INVOICE_STATUSES = frozenset({"no", "to invoice", "invoiced"})
_GROUP_FIELDS = {
    "sale": {
        "state": "state",
        "invoice_status": "invoice_status",
        "partner": "partner_id",
        "salesperson": "user_id",
        "currency": "currency_id",
    },
    "purchase": {
        "state": "state",
        "invoice_status": "invoice_status",
        "partner": "partner_id",
        "buyer": "user_id",
        "currency": "currency_id",
    },
}

_COMMON_ORDER_FIELDS = {
    "company_id",
    "name",
    "partner_id",
    "state",
    "date_order",
    "currency_id",
    "user_id",
    "invoice_status",
    "amount_untaxed",
    "amount_tax",
    "amount_total",
    "invoice_ids",
    "picking_ids",
    "order_line",
}
_SALE_ORDER_FIELDS = _COMMON_ORDER_FIELDS | {
    "validity_date",
    "client_order_ref",
    "team_id",
    "delivery_status",
}
_PURCHASE_ORDER_FIELDS = _COMMON_ORDER_FIELDS | {
    "date_approve",
    "partner_ref",
    "origin",
    "receipt_status",
}
_COMMON_LINE_FIELDS = {
    "order_id",
    "company_id",
    "state",
    "sequence",
    "display_type",
    "name",
    "product_id",
    "product_uom_id",
    "qty_invoiced",
    "qty_to_invoice",
    "price_unit",
    "discount",
    "price_subtotal",
    "price_tax",
    "price_total",
    "currency_id",
    "tax_ids",
    "invoice_lines",
    "move_ids",
}
_SALE_LINE_FIELDS = _COMMON_LINE_FIELDS | {"product_uom_qty", "qty_delivered"}
_PURCHASE_LINE_FIELDS = _COMMON_LINE_FIELDS | {
    "product_qty",
    "qty_received",
    "date_planned",
}
_INVOICE_FIELDS = {
    "company_id",
    "name",
    "move_type",
    "state",
    "payment_state",
    "amount_total",
    "currency_id",
}
_TRANSFER_FIELDS = {
    "company_id",
    "name",
    "state",
    "location_id",
    "location_dest_id",
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


def _canonical_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _valid_date_range(
    parameters: dict[str, Any], *, dates_required: bool = False
) -> bool:
    date_from = parameters["date_from"]
    date_to = parameters["date_to"]
    return bool(
        (not dates_required or date_from is not None and date_to is not None)
        and (date_from is None or _canonical_date(date_from))
        and (date_to is None or _canonical_date(date_to))
        and (date_from is None or date_to is None or date_from <= date_to)
    )


def _enum_list(value: Any, allowed: frozenset[str]) -> bool:
    return value is None or bool(
        isinstance(value, list)
        and value
        and all(isinstance(item, str) for item in value)
        and value == sorted(set(value))
        and set(value) <= allowed
    )


def _kind(capability_id: str) -> str:
    return "sale" if capability_id.startswith("sale.") else "purchase"


def _valid_parameters(capability_id: str, parameters: Any) -> bool:
    if not isinstance(parameters, dict):
        return False
    kind = _kind(capability_id)
    states = _SALE_STATES if kind == "sale" else _PURCHASE_STATES
    invoice_statuses = (
        _SALE_INVOICE_STATUSES if kind == "sale" else _PURCHASE_INVOICE_STATUSES
    )
    if capability_id.endswith(".get"):
        return set(parameters) == {"order_id"} and _positive_id(parameters["order_id"])
    if capability_id.endswith(".order.search"):
        if set(parameters) != {
            "query",
            "date_from",
            "date_to",
            "states",
            "partner_id",
            "currency_id",
            "invoice_statuses",
            "after",
            "limit",
        }:
            return False
        query = parameters["query"]
        return bool(
            (
                query is None
                or isinstance(query, str)
                and query == query.strip()
                and 1 <= len(query) <= 256
            )
            and _valid_date_range(parameters)
            and _enum_list(parameters["states"], states)
            and _optional_id(parameters["partner_id"])
            and _optional_id(parameters["currency_id"])
            and _enum_list(parameters["invoice_statuses"], invoice_statuses)
            and _optional_id(parameters["after"])
            and _integer(parameters["limit"])
            and 1 <= parameters["limit"] <= 1001
        )
    if capability_id.endswith(".line.search"):
        pending_key = "to_deliver_only" if kind == "sale" else "to_receive_only"
        if set(parameters) != {
            "order_id",
            "date_from",
            "date_to",
            "partner_id",
            "product_id",
            "states",
            pending_key,
            "to_invoice_only",
            "after",
            "limit",
        }:
            return False
        return bool(
            _optional_id(parameters["order_id"])
            and _valid_date_range(parameters)
            and _optional_id(parameters["partner_id"])
            and _optional_id(parameters["product_id"])
            and _enum_list(parameters["states"], states)
            and isinstance(parameters[pending_key], bool)
            and isinstance(parameters["to_invoice_only"], bool)
            and _optional_id(parameters["after"])
            and _integer(parameters["limit"])
            and 1 <= parameters["limit"] <= 1001
        )
    if set(parameters) != {
        "date_from",
        "date_to",
        "group_by",
        "states",
        "partner_id",
        "currency_id",
    }:
        return False
    return bool(
        _valid_date_range(parameters, dates_required=True)
        and isinstance(parameters["group_by"], str)
        and parameters["group_by"] in _GROUP_FIELDS[kind]
        and _enum_list(parameters["states"], states)
        and _optional_id(parameters["partner_id"])
        and _optional_id(parameters["currency_id"])
    )


def _validated_payload(
    payload: Any, company_id: int, failure_type: Any
) -> tuple[str, dict[str, Any]]:
    if (
        not isinstance(payload, dict)
        or set(payload) != {"capability_id", "company_id", "parameters"}
        or not isinstance(payload.get("capability_id"), str)
        or payload.get("capability_id") not in CAPABILITY_IDS
        or not _positive_id(payload.get("company_id"))
        or payload["company_id"] != company_id
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


def _order_model(kind: str) -> str:
    return f"{kind}.order"


def _line_model(kind: str) -> str:
    return f"{kind}.order.line"


def _required_models(capability_id: str) -> tuple[str, ...]:
    kind = _kind(capability_id)
    models = {
        "res.company",
        "res.partner",
        "res.users",
        "res.currency",
        _order_model(kind),
    }
    if capability_id.endswith(".analysis.summary"):
        return tuple(sorted(models))
    models.add(_line_model(kind))
    if capability_id.endswith(".order.search"):
        models.update({"account.move", "stock.picking"})
    elif capability_id.endswith(".line.search"):
        models.update(
            {
                "product.product",
                "uom.uom",
                "account.tax",
                "account.move.line",
                "stock.move",
            }
        )
    else:
        models.update(
            {
                "product.product",
                "uom.uom",
                "account.tax",
                "account.move",
                "account.move.line",
                "stock.picking",
                "stock.move",
                "stock.location",
            }
        )
    if kind == "sale":
        models.add("crm.team")
    return tuple(sorted(models))


def _fields(env: Any, model: str, required: set[str]) -> bool:
    return required <= set(getattr(env[model], "_fields", {}))


def _field_shape_available(env: Any, capability_id: str) -> bool:
    kind = _kind(capability_id)
    order_fields = _SALE_ORDER_FIELDS if kind == "sale" else _PURCHASE_ORDER_FIELDS
    summary_fields = {
        "company_id",
        "state",
        "date_order",
        "partner_id",
        "user_id",
        "currency_id",
        "invoice_status",
        "amount_untaxed",
        "amount_tax",
        "amount_total",
    }
    if not _fields(
        env,
        _order_model(kind),
        summary_fields if capability_id.endswith(".analysis.summary") else order_fields,
    ):
        return False
    if capability_id.endswith(".analysis.summary"):
        return _fields(env, "res.currency", {"name"})
    line_fields = _SALE_LINE_FIELDS if kind == "sale" else _PURCHASE_LINE_FIELDS
    if not _fields(env, _line_model(kind), line_fields):
        return False
    if capability_id.endswith(".order.search"):
        return bool(
            _fields(env, "account.move", {"company_id"})
            and _fields(env, "stock.picking", {"company_id"})
        )
    if capability_id.endswith(".line.search"):
        return bool(
            _fields(env, "account.move.line", {"company_id"})
            and _fields(env, "stock.move", {"company_id"})
        )
    return bool(
        _fields(env, "account.move", _INVOICE_FIELDS)
        and _fields(env, "account.move.line", {"company_id"})
        and _fields(env, "stock.picking", _TRANSFER_FIELDS)
        and _fields(env, "stock.move", {"company_id"})
        and _fields(env, "stock.location", {"company_id", "complete_name"})
    )


def _scope_page(
    env: Any, capability_id: str, company_id: int, failure_type: Any
) -> dict[str, Any]:
    company_visible = bool(
        env["res.company"]
        .with_context(allowed_company_ids=[company_id])
        .search_count([("id", "=", company_id)], limit=1)
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


def _named_ref(record: Any, *, field: str = "display_name") -> dict[str, Any]:
    return {"id": _record_id(record), "name": _text(getattr(record, field))}


def _optional_named_ref(
    record: Any, *, field: str = "display_name"
) -> dict[str, Any] | None:
    return None if not record else _named_ref(record, field=field)


def _currency(record: Any) -> dict[str, Any]:
    code = _text(record.name)
    if len(code) > 3:
        raise ValueError("invalid currency code")
    return {"id": _record_id(record), "code": code}


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


def _date_text(value: Any) -> str | None:
    if value in (None, False):
        return None
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, date):
        return value.isoformat()
    if _canonical_date(value):
        return value
    raise TypeError("invalid date")


def _company_id(record: Any) -> int | None:
    company = getattr(record, "company_id", None)
    return None if not company else _record_id(company)


def _company_matches(record: Any, company_id: int, *, shared: bool = False) -> bool:
    record_company = _company_id(record)
    return record_company == company_id or shared and record_company is None


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


def _linked_records(
    env: Any,
    model_name: str,
    records: Any,
    company_id: int,
    *,
    order: str = "id asc",
) -> list[Any]:
    ids = list(getattr(records, "ids", []))
    if not ids:
        return []
    return list(
        _model(env, model_name, company_id).search(
            [("id", "in", ids), ("company_id", "=", company_id)],
            order=order,
        )
    )


def _order_domain(kind: str, company_id: int, parameters: dict[str, Any]) -> list[Any]:
    domain: list[Any] = [
        ("company_id", "=", company_id),
        *_date_domain("date_order", parameters),
    ]
    if parameters["states"] is not None:
        domain.append(("state", "in", parameters["states"]))
    if parameters["partner_id"] is not None:
        domain.append(("partner_id", "=", parameters["partner_id"]))
    if parameters["currency_id"] is not None:
        domain.append(("currency_id", "=", parameters["currency_id"]))
    if "invoice_statuses" in parameters and parameters["invoice_statuses"] is not None:
        domain.append(("invoice_status", "in", parameters["invoice_statuses"]))
    query = parameters.get("query")
    if query is not None:
        if kind == "sale":
            domain.extend(
                [
                    "|",
                    "|",
                    ("name", "ilike", query),
                    ("client_order_ref", "ilike", query),
                    ("partner_id.name", "ilike", query),
                ]
            )
        else:
            domain.extend(
                [
                    "|",
                    "|",
                    "|",
                    ("name", "ilike", query),
                    ("partner_ref", "ilike", query),
                    ("origin", "ilike", query),
                    ("partner_id.name", "ilike", query),
                ]
            )
    return domain


def _search_records(
    env: Any,
    model_name: str,
    company_id: int,
    domain: list[Any],
    parameters: dict[str, Any],
) -> tuple[bool, list[Any]]:
    model = _model(env, model_name, company_id)
    after = parameters["after"]
    if after is not None and not model.search_count(
        [*domain, ("id", "=", after)], limit=1
    ):
        return False, []
    search_domain = [*domain]
    if after is not None:
        search_domain.append(("id", ">", after))
    return True, list(
        model.search(search_domain, order="id asc", limit=parameters["limit"])
    )


def _order_links(env: Any, order: Any, company_id: int) -> tuple[list[Any], list[Any]]:
    invoices = _linked_records(
        env, "account.move", order.invoice_ids, company_id, order="id asc"
    )
    transfers = _linked_records(
        env, "stock.picking", order.picking_ids, company_id, order="id asc"
    )
    return invoices, transfers


def _line_count(env: Any, kind: str, order_id: int, company_id: int) -> int:
    return _model(env, _line_model(kind), company_id).search_count(
        [("order_id", "=", order_id), ("company_id", "=", company_id)]
    )


def _order_header(env: Any, kind: str, order: Any, company_id: int) -> dict[str, Any]:
    if not _company_matches(order, company_id):
        raise ValueError("cross-company order")
    partner = order.partner_id
    if not _company_matches(partner, company_id, shared=True):
        raise ValueError("cross-company order partner")
    invoices, transfers = _order_links(env, order, company_id)
    item: dict[str, Any] = {
        "id": _record_id(order),
        "name": _text(order.name),
        "company": _named_ref(order.company_id, field="name"),
        "partner": _named_ref(partner),
        "state": _text(order.state),
        "date_order": _utc_text(order.date_order),
        "currency": _currency(order.currency_id),
        "user": _optional_named_ref(order.user_id),
        "invoice_status": _text(order.invoice_status),
        "amount_untaxed": _decimal_text(order.amount_untaxed),
        "amount_tax": _decimal_text(order.amount_tax),
        "amount_total": _decimal_text(order.amount_total),
        "invoice_ids": [_record_id(record) for record in invoices],
        "transfer_ids": [_record_id(record) for record in transfers],
        "line_count": _line_count(env, kind, _record_id(order), company_id),
    }
    if kind == "sale":
        team = order.team_id
        if team and not _company_matches(team, company_id, shared=True):
            raise ValueError("cross-company sales team")
        item.update(
            {
                "validity_date": _date_text(order.validity_date),
                "client_order_ref": _optional_text(order.client_order_ref),
                "team": _optional_named_ref(team),
                "delivery_status": _optional_text(order.delivery_status),
            }
        )
    else:
        item.update(
            {
                "date_approve": _utc_text(order.date_approve),
                "partner_ref": _optional_text(order.partner_ref),
                "origin": _optional_text(order.origin),
                "receipt_status": _optional_text(order.receipt_status),
            }
        )
    return item


def _order_search_items(
    env: Any, capability_id: str, company_id: int, parameters: dict[str, Any]
) -> tuple[bool, list[dict[str, Any]]]:
    kind = _kind(capability_id)
    cursor_found, records = _search_records(
        env,
        _order_model(kind),
        company_id,
        _order_domain(kind, company_id, parameters),
        parameters,
    )
    return cursor_found, [
        _order_header(env, kind, record, company_id) for record in records
    ]


def _line_domain(kind: str, company_id: int, parameters: dict[str, Any]) -> list[Any]:
    domain: list[Any] = [
        ("company_id", "=", company_id),
        *_date_domain("order_id.date_order", parameters),
    ]
    field_map = {
        "order_id": "order_id",
        "partner_id": "order_id.partner_id",
        "product_id": "product_id",
    }
    for key, field in field_map.items():
        if parameters[key] is not None:
            domain.append((field, "=", parameters[key]))
    if parameters["states"] is not None:
        domain.append(("state", "in", parameters["states"]))
    return domain


def _pending_quantity(kind: str, line: Any) -> Decimal:
    ordered = line.product_uom_qty if kind == "sale" else line.product_qty
    completed = line.qty_delivered if kind == "sale" else line.qty_received
    return max(Decimal(0), _decimal(ordered) - _decimal(completed))


def _line_matches(kind: str, line: Any, parameters: dict[str, Any]) -> bool:
    pending_key = "to_deliver_only" if kind == "sale" else "to_receive_only"
    return bool(
        (not parameters[pending_key] or _pending_quantity(kind, line) > 0)
        and (not parameters["to_invoice_only"] or _decimal(line.qty_to_invoice) > 0)
    )


def _line_records(
    env: Any, kind: str, company_id: int, parameters: dict[str, Any]
) -> tuple[bool, list[Any]]:
    model = _model(env, _line_model(kind), company_id)
    domain = _line_domain(kind, company_id, parameters)
    after = parameters["after"]
    if after is not None:
        cursor_records = model.search([*domain, ("id", "=", after)], limit=2)
        if len(cursor_records) != 1 or not _line_matches(
            kind, cursor_records[0], parameters
        ):
            return False, []
    found: list[Any] = []
    last_seen = after or 0
    scan_limit = max(100, min(1001, parameters["limit"] * 2))
    while len(found) < parameters["limit"]:
        batch = list(
            model.search(
                [*domain, ("id", ">", last_seen)],
                order="id asc",
                limit=scan_limit,
            )
        )
        if not batch:
            break
        for record in batch:
            last_seen = _record_id(record)
            if _line_matches(kind, record, parameters):
                found.append(record)
                if len(found) == parameters["limit"]:
                    break
        if len(batch) < scan_limit:
            break
    return True, found


def _taxes(env: Any, line: Any, company_id: int) -> list[dict[str, Any]]:
    records = _linked_records(
        env, "account.tax", line.tax_ids, company_id, order="id asc"
    )
    return [_named_ref(record) for record in records]


def _line_link_ids(env: Any, line: Any, company_id: int) -> tuple[list[int], list[int]]:
    invoice_lines = _linked_records(
        env,
        "account.move.line",
        line.invoice_lines,
        company_id,
        order="id asc",
    )
    stock_moves = _linked_records(
        env, "stock.move", line.move_ids, company_id, order="id asc"
    )
    return (
        [_record_id(record) for record in invoice_lines],
        [_record_id(record) for record in stock_moves],
    )


def _line_item(env: Any, kind: str, line: Any, company_id: int) -> dict[str, Any]:
    if not _company_matches(line, company_id):
        raise ValueError("cross-company order line")
    order = line.order_id
    if not _company_matches(order, company_id):
        raise ValueError("cross-company line order")
    partner = order.partner_id
    product = line.product_id
    if not _company_matches(partner, company_id, shared=True) or (
        product and not _company_matches(product, company_id, shared=True)
    ):
        raise ValueError("cross-company line reference")
    invoice_line_ids, stock_move_ids = _line_link_ids(env, line, company_id)
    item: dict[str, Any] = {
        "id": _record_id(line),
        "order": _named_ref(order, field="name"),
        "company": _named_ref(order.company_id, field="name"),
        "partner": _named_ref(partner),
        "state": _text(line.state),
        "date_order": _utc_text(order.date_order),
        "sequence": line.sequence,
        "display_type": _optional_text(line.display_type),
        "description": _text(line.name),
        "product": _optional_named_ref(product),
        "uom": _optional_named_ref(line.product_uom_id),
        "ordered_quantity": _decimal_text(
            line.product_uom_qty if kind == "sale" else line.product_qty
        ),
        "invoiced_quantity": _decimal_text(line.qty_invoiced),
        "to_invoice_quantity": _decimal_text(line.qty_to_invoice),
        "unit_price": _decimal_text(line.price_unit),
        "discount_percent": _decimal_text(line.discount),
        "amount_untaxed": _decimal_text(line.price_subtotal),
        "amount_tax": _decimal_text(line.price_tax),
        "amount_total": _decimal_text(line.price_total),
        "currency": _currency(line.currency_id),
        "taxes": _taxes(env, line, company_id),
        "invoice_line_ids": invoice_line_ids,
        "stock_move_ids": stock_move_ids,
    }
    if kind == "sale":
        item.update(
            {
                "delivered_quantity": _decimal_text(line.qty_delivered),
                "to_deliver_quantity": _decimal_text(_pending_quantity(kind, line)),
            }
        )
    else:
        item.update(
            {
                "received_quantity": _decimal_text(line.qty_received),
                "to_receive_quantity": _decimal_text(_pending_quantity(kind, line)),
                "date_planned": _utc_text(line.date_planned),
            }
        )
    return item


def _line_search_items(
    env: Any, capability_id: str, company_id: int, parameters: dict[str, Any]
) -> tuple[bool, list[dict[str, Any]]]:
    kind = _kind(capability_id)
    cursor_found, records = _line_records(env, kind, company_id, parameters)
    return cursor_found, [
        _line_item(env, kind, record, company_id) for record in records
    ]


def _invoice_item(invoice: Any, company_id: int) -> dict[str, Any]:
    if not _company_matches(invoice, company_id):
        raise ValueError("cross-company linked invoice")
    return {
        "id": _record_id(invoice),
        "name": _text(getattr(invoice, "display_name", None) or invoice.name),
        "move_type": _text(invoice.move_type),
        "state": _text(invoice.state),
        "payment_state": _optional_text(invoice.payment_state),
        "amount_total": _decimal_text(invoice.amount_total),
        "currency": _currency(invoice.currency_id),
    }


def _transfer_item(transfer: Any, company_id: int) -> dict[str, Any]:
    if not _company_matches(transfer, company_id):
        raise ValueError("cross-company linked transfer")
    source = transfer.location_id
    destination = transfer.location_dest_id
    if not _company_matches(source, company_id, shared=True) or not _company_matches(
        destination, company_id, shared=True
    ):
        raise ValueError("cross-company transfer location")
    return {
        "id": _record_id(transfer),
        "name": _text(transfer.name),
        "state": _text(transfer.state),
        "source_location": _named_ref(source, field="complete_name"),
        "destination_location": _named_ref(destination, field="complete_name"),
    }


def _order_get_item(
    env: Any, capability_id: str, company_id: int, parameters: dict[str, Any]
) -> dict[str, Any] | None:
    kind = _kind(capability_id)
    order_id = parameters["order_id"]
    orders = _model(env, _order_model(kind), company_id).search(
        [("id", "=", order_id), ("company_id", "=", company_id)], limit=2
    )
    if len(orders) > 1:
        raise ValueError("ambiguous order")
    if not orders:
        return None
    order = orders[0]
    lines = list(
        _model(env, _line_model(kind), company_id).search(
            [("order_id", "=", order_id), ("company_id", "=", company_id)],
            order="id asc",
        )
    )
    invoices, transfers = _order_links(env, order, company_id)
    return {
        **_order_header(env, kind, order, company_id),
        "lines": [_line_item(env, kind, line, company_id) for line in lines],
        "invoices": [_invoice_item(invoice, company_id) for invoice in invoices],
        "transfers": [_transfer_item(transfer, company_id) for transfer in transfers],
    }


def _group_descriptor(group_by: str, value: Any) -> dict[str, Any]:
    if group_by in {"partner", "salesperson", "buyer"}:
        reference = _optional_named_ref(value)
        return {
            "id": None if reference is None else reference["id"],
            "value": None if reference is None else reference["name"],
        }
    if group_by == "currency":
        if not value:
            return {"id": None, "value": None}
        currency = _currency(value)
        return {"id": currency["id"], "value": currency["code"]}
    return {
        "id": None,
        "value": None if value in (None, False) else _text(value),
    }


def _summary_item(
    env: Any, capability_id: str, company_id: int, parameters: dict[str, Any]
) -> dict[str, Any]:
    kind = _kind(capability_id)
    group_by = parameters["group_by"]
    group_field = _GROUP_FIELDS[kind][group_by]
    group_fields = [group_field]
    if group_field != "currency_id":
        group_fields.append("currency_id")
    rows = _model(env, _order_model(kind), company_id)._read_group(
        _order_domain(kind, company_id, parameters),
        groupby=group_fields,
        aggregates=[
            "__count",
            "amount_untaxed:sum",
            "amount_tax:sum",
            "amount_total:sum",
        ],
    )
    groups: list[dict[str, Any]] = []
    totals: dict[int, dict[str, Any]] = {}
    expected_length = len(group_fields) + 4
    for row in rows:
        if not isinstance(row, (list, tuple)) or len(row) != expected_length:
            raise ValueError("invalid order aggregate")
        group_value = row[0]
        currency_record = row[0] if group_field == "currency_id" else row[1]
        if not currency_record:
            raise ValueError("order aggregate has no currency")
        if group_by == "partner" and not _company_matches(
            group_value, company_id, shared=True
        ):
            raise ValueError("cross-company aggregate partner")
        currency = _currency(currency_record)
        aggregate_offset = len(group_fields)
        count = row[aggregate_offset]
        if not _integer(count) or count <= 0:
            raise ValueError("invalid order count")
        group = {
            "group": _group_descriptor(group_by, group_value),
            "currency": currency,
            "order_count": count,
            "amount_untaxed": _decimal_text(row[aggregate_offset + 1]),
            "amount_tax": _decimal_text(row[aggregate_offset + 2]),
            "amount_total": _decimal_text(row[aggregate_offset + 3]),
        }
        groups.append(group)
        total = totals.setdefault(
            currency["id"],
            {
                "currency": currency,
                "order_count": 0,
                "amount_untaxed": Decimal(0),
                "amount_tax": Decimal(0),
                "amount_total": Decimal(0),
            },
        )
        total["order_count"] += count
        for key in ("amount_untaxed", "amount_tax", "amount_total"):
            total[key] += _decimal(group[key])
    groups.sort(
        key=lambda item: (
            item["group"]["value"] or "",
            item["group"]["id"] or 0,
            item["currency"]["id"],
        )
    )
    totals_by_currency: list[dict[str, Any]] = []
    for currency_id in sorted(totals):
        total = totals[currency_id]
        totals_by_currency.append(
            {
                "currency": total["currency"],
                "order_count": total["order_count"],
                "amount_untaxed": _decimal_text(total["amount_untaxed"]),
                "amount_tax": _decimal_text(total["amount_tax"]),
                "amount_total": _decimal_text(total["amount_total"]),
            }
        )
    return {
        "company_id": company_id,
        "group_by": group_by,
        "date_from": parameters["date_from"],
        "date_to": parameters["date_to"],
        "groups": groups,
        "totals_by_currency": totals_by_currency,
    }


def dispatch(
    env: Any,
    payload: dict[str, Any],
    company_id: int,
    *,
    failure_type: Any,
) -> dict[str, Any]:
    """Validate, gate, and execute one allowlisted order-document read."""

    try:
        capability_id, parameters = _validated_payload(
            payload, company_id, failure_type
        )
        page = _scope_page(env, capability_id, company_id, failure_type)
        if not page["access_allowed"]:
            return page
        if capability_id.endswith(".order.search"):
            cursor_found, items = _order_search_items(
                env, capability_id, company_id, parameters
            )
        elif capability_id.endswith(".order.get"):
            cursor_found = True
            item = _order_get_item(env, capability_id, company_id, parameters)
            items = [] if item is None else [item]
        elif capability_id.endswith(".line.search"):
            cursor_found, items = _line_search_items(
                env, capability_id, company_id, parameters
            )
        else:
            cursor_found = True
            items = [_summary_item(env, capability_id, company_id, parameters)]
        return {**page, "cursor_found": cursor_found, "items": items}
    except failure_type:
        raise
    except Exception as exc:
        raise _runtime_failure(failure_type) from exc
