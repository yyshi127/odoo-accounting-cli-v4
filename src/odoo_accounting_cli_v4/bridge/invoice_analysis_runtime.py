"""Odoo-side runtime for the two fixed invoice-analysis reads."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

ACTION = "accounting.invoice_analysis.read"
CAPABILITY_IDS = frozenset({"invoice.analysis.search", "invoice.analysis.summary"})
MOVE_TYPES = frozenset({"out_invoice", "out_refund", "in_invoice", "in_refund"})
STATES = frozenset({"draft", "posted", "cancel"})
PAYMENT_STATES = frozenset(
    {
        "not_paid",
        "in_payment",
        "paid",
        "partial",
        "reversed",
        "blocked",
        "invoicing_legacy",
    }
)
GROUP_BY_FIELDS = {
    "move_type": "move_type",
    "state": "state",
    "payment_state": "payment_state",
    "partner": "partner_id",
    "product": "product_id",
}

_MODELS = (
    "account.invoice.report",
    "res.company",
    "res.currency",
    "res.partner",
    "product.product",
    "account.journal",
    "uom.uom",
)
_REQUIRED_FIELDS = {
    "account.invoice.report": {
        "move_id",
        "journal_id",
        "company_id",
        "company_currency_id",
        "partner_id",
        "move_type",
        "state",
        "payment_state",
        "invoice_date",
        "invoice_date_due",
        "quantity",
        "product_id",
        "product_uom_id",
        "price_subtotal_currency",
        "price_subtotal",
        "price_total",
        "price_total_currency",
        "price_average",
        "price_margin",
        "inventory_value",
        "currency_id",
    },
    "res.company": {"currency_id"},
    "res.currency": {"name"},
}
_SEARCH_FIELDS = [
    "move_id",
    "journal_id",
    "company_id",
    "company_currency_id",
    "partner_id",
    "move_type",
    "state",
    "payment_state",
    "invoice_date",
    "invoice_date_due",
    "quantity",
    "product_id",
    "product_uom_id",
    "price_subtotal_currency",
    "price_subtotal",
    "price_total",
    "price_total_currency",
    "price_average",
    "price_margin",
    "inventory_value",
    "currency_id",
]
_AGGREGATES = (
    "__count",
    "quantity:sum",
    "price_subtotal:sum",
    "price_total:sum",
    "price_margin:sum",
    "inventory_value:sum",
)
_SUMMARY_AMOUNT_KEYS = (
    "quantity",
    "untaxed_amount",
    "total_amount",
    "margin",
    "inventory_value",
)


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


def _canonical_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _enum_list(value: Any, allowed: frozenset[str]) -> bool:
    return value is None or bool(
        isinstance(value, list)
        and value == sorted(set(value))
        and bool(value)
        and set(value) <= allowed
    )


def _common_parameters(parameters: dict[str, Any], *, require_dates: bool) -> bool:
    date_from = parameters["date_from"]
    date_to = parameters["date_to"]
    return bool(
        (date_from is None) == (date_to is None)
        and (not require_dates or date_from is not None)
        and (
            date_from is None
            or _canonical_date(date_from)
            and _canonical_date(date_to)
            and date_from <= date_to
        )
        and _enum_list(parameters["move_types"], MOVE_TYPES)
        and _enum_list(parameters["states"], STATES)
        and _enum_list(parameters["payment_states"], PAYMENT_STATES)
        and (parameters["partner_id"] is None or _positive_id(parameters["partner_id"]))
        and (parameters["product_id"] is None or _positive_id(parameters["product_id"]))
    )


def _valid_parameters(capability_id: str, parameters: Any) -> bool:
    if not isinstance(parameters, dict):
        return False
    common = {
        "date_from",
        "date_to",
        "move_types",
        "states",
        "payment_states",
        "partner_id",
        "product_id",
    }
    if capability_id == "invoice.analysis.search":
        if set(parameters) != common | {"after", "limit"}:
            return False
        return bool(
            _common_parameters(parameters, require_dates=False)
            and (parameters["after"] is None or _positive_id(parameters["after"]))
            and _integer(parameters["limit"])
            and 1 <= parameters["limit"] <= 1001
        )
    if set(parameters) != common | {"group_by"}:
        return False
    return bool(
        _common_parameters(parameters, require_dates=True)
        and isinstance(parameters["group_by"], str)
        and parameters["group_by"] in GROUP_BY_FIELDS
    )


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


def _field_shape_available(env: Any) -> bool:
    return all(
        names <= set(getattr(env[model], "_fields", {}))
        for model, names in _REQUIRED_FIELDS.items()
    )


def _scope_page(env: Any, company_id: int, failure_type: Any) -> dict[str, Any]:
    company_visible = bool(
        env["res.company"].search_count([("id", "=", company_id)], limit=1)
    )
    module_installed = all(env.registry.get(model) is not None for model in _MODELS)
    if company_visible and module_installed and not _field_shape_available(env):
        raise _runtime_failure(failure_type)
    access_allowed = bool(
        company_visible
        and module_installed
        and env.user.has_group("account.group_account_readonly")
        and all(env[model].has_access("read") for model in _MODELS)
    )
    return _empty_page(
        env,
        company_visible=company_visible,
        module_installed=module_installed,
        access_allowed=access_allowed,
    )


def _model(env: Any, name: str, company_id: int) -> Any:
    return env[name].with_context(allowed_company_ids=[company_id])


def _base_domain(company_id: int, parameters: dict[str, Any]) -> list[Any]:
    domain: list[Any] = [
        ("company_id", "=", company_id),
        ("move_type", "in", parameters["move_types"] or sorted(MOVE_TYPES)),
    ]
    if parameters["date_from"] is not None:
        domain.extend(
            [
                ("invoice_date", ">=", parameters["date_from"]),
                ("invoice_date", "<=", parameters["date_to"]),
            ]
        )
    for parameter, field in (
        ("states", "state"),
        ("payment_states", "payment_state"),
    ):
        if parameters[parameter] is not None:
            domain.append((field, "in", parameters[parameter]))
    for parameter, field in (
        ("partner_id", "partner_id"),
        ("product_id", "product_id"),
    ):
        if parameters[parameter] is not None:
            domain.append((field, "=", parameters[parameter]))
    return domain


def _reference(value: Any, *, required: bool = True) -> dict[str, Any] | None:
    is_empty_recordset = (
        not isinstance(value, (list, tuple))
        and hasattr(value, "id")
        and not bool(value)
    )
    if value is None or value is False or is_empty_recordset:
        if required:
            raise ValueError("missing reference")
        return None
    if isinstance(value, (list, tuple)) and len(value) == 2:
        record_id, name = value
    else:
        record_id = getattr(value, "id", None)
        name = getattr(value, "display_name", None)
    if not _positive_id(record_id) or not isinstance(name, str) or not name.strip():
        raise ValueError("invalid reference")
    return {"id": record_id, "name": name}


def _currency(value: Any) -> dict[str, Any]:
    reference = _reference(value)
    if reference is None or len(reference["name"]) > 3:
        raise ValueError("invalid currency")
    return {"id": reference["id"], "code": reference["name"]}


def _date_text(value: Any) -> str:
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, date):
        return value.isoformat()
    if _canonical_date(value):
        return value
    raise ValueError("invalid date")


def _optional_date(value: Any) -> str | None:
    return None if value in (None, False) else _date_text(value)


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


def _search_item(row: dict[str, Any], company_id: int) -> dict[str, Any]:
    company = _reference(row["company_id"])
    if company is None or company["id"] != company_id:
        raise ValueError("cross-company invoice analysis row")
    payment_state = row["payment_state"]
    if payment_state in (None, False):
        payment_state = None
    if payment_state is not None and payment_state not in PAYMENT_STATES:
        raise ValueError("invalid payment state")
    return {
        "id": row["id"],
        "invoice": _reference(row["move_id"]),
        "journal": _reference(row["journal_id"]),
        "company_id": company_id,
        "company_currency": _currency(row["company_currency_id"]),
        "partner": _reference(row["partner_id"], required=False),
        "move_type": row["move_type"],
        "state": row["state"],
        "payment_state": payment_state,
        "invoice_date": _optional_date(row["invoice_date"]),
        "due_date": _optional_date(row["invoice_date_due"]),
        "product": _reference(row["product_id"], required=False),
        "uom": _reference(row["product_uom_id"], required=False),
        "currency": _currency(row["currency_id"]),
        "quantity": _decimal_text(row["quantity"]),
        "untaxed_amount_currency": _decimal_text(row["price_subtotal_currency"]),
        "untaxed_amount": _decimal_text(row["price_subtotal"]),
        "total_amount": _decimal_text(row["price_total"]),
        "total_amount_currency": _decimal_text(row["price_total_currency"]),
        "average_price": _decimal_text(row["price_average"]),
        "margin": _decimal_text(row["price_margin"]),
        "inventory_value": _decimal_text(row["inventory_value"]),
    }


def _search_items(
    env: Any, company_id: int, parameters: dict[str, Any]
) -> tuple[bool, list[dict[str, Any]]]:
    model = _model(env, "account.invoice.report", company_id)
    domain = _base_domain(company_id, parameters)
    after = parameters["after"]
    cursor_found = True
    if after is not None:
        cursor_found = bool(model.search_count([*domain, ("id", "=", after)], limit=1))
        if not cursor_found:
            return False, []
        domain.append(("id", "<", after))
    rows = model.search_read(
        domain,
        _SEARCH_FIELDS,
        order="id desc",
        limit=parameters["limit"],
    )
    return True, [_search_item(row, company_id) for row in rows]


def _group_descriptor(group_by: str, value: Any) -> dict[str, Any]:
    if group_by in {"partner", "product"}:
        reference = _reference(value, required=False)
        return {
            "id": None if reference is None else reference["id"],
            "value": None if reference is None else reference["name"],
        }
    if value in (None, False):
        return {"id": None, "value": None}
    if not isinstance(value, str):
        raise TypeError("invalid selection group")
    return {"id": None, "value": value}


def _summary_item(
    env: Any, company_id: int, parameters: dict[str, Any]
) -> dict[str, Any]:
    company = _model(env, "res.company", company_id).search(
        [("id", "=", company_id)], limit=2
    )
    if len(company) != 1:
        raise ValueError("company disappeared")
    company = company[0]
    group_by = parameters["group_by"]
    field = GROUP_BY_FIELDS[group_by]
    rows = _model(env, "account.invoice.report", company_id)._read_group(
        _base_domain(company_id, parameters),
        groupby=[field],
        aggregates=list(_AGGREGATES),
        order=f"{field} asc",
    )
    groups: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, (list, tuple)) or len(row) != 7:
            raise ValueError("invalid invoice analysis aggregate")
        descriptor = _group_descriptor(group_by, row[0])
        count = row[1]
        if not _integer(count) or count <= 0:
            raise ValueError("invalid invoice analysis group count")
        groups.append(
            {
                "group": descriptor,
                "row_count": count,
                "quantity": _decimal_text(row[2]),
                "untaxed_amount": _decimal_text(row[3]),
                "total_amount": _decimal_text(row[4]),
                "margin": _decimal_text(row[5]),
                "inventory_value": _decimal_text(row[6]),
            }
        )
    groups.sort(
        key=lambda item: (item["group"]["id"] or 0, item["group"]["value"] or "")
    )
    totals: dict[str, Any] = {"row_count": sum(item["row_count"] for item in groups)}
    for key in _SUMMARY_AMOUNT_KEYS:
        totals[key] = _decimal_text(
            sum((_decimal(item[key]) for item in groups), Decimal(0))
        )
    return {
        "group_by": group_by,
        "date_from": parameters["date_from"],
        "date_to": parameters["date_to"],
        "company_id": company_id,
        "company_currency": _currency(company.currency_id),
        "groups": groups,
        "totals": totals,
    }


def dispatch(
    env: Any,
    payload: dict[str, Any],
    company_id: int,
    *,
    failure_type: Any,
) -> dict[str, Any]:
    """Validate, gate and execute one allowlisted invoice-analysis read."""

    try:
        capability_id, parameters = _validated_payload(
            payload, company_id, failure_type
        )
        page = _scope_page(env, company_id, failure_type)
        if not page["access_allowed"]:
            return page
        if capability_id == "invoice.analysis.search":
            cursor_found, items = _search_items(env, company_id, parameters)
        else:
            cursor_found = True
            items = [_summary_item(env, company_id, parameters)]
        return {**page, "cursor_found": cursor_found, "items": items}
    except failure_type:
        raise
    except Exception as exc:
        raise _runtime_failure(failure_type) from exc
