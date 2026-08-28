"""Odoo-side runtime for five fixed inventory-accounting reads.

The monolithic bridge dispatcher supplies its ``RuntimeFailure`` class so this
slice can be imported and unit-tested without importing Odoo.
"""

from __future__ import annotations

from datetime import UTC, datetime
from datetime import date as date_type
from decimal import Decimal, InvalidOperation
from typing import Any

ACTION = "accounting.inventory.read"
CAPABILITY_IDS = frozenset(
    {
        "cogs.entries.list",
        "inventory.accounting_entries.list",
        "report.inventory_valuation",
        "purchase_bill.matching.inspect",
        "sale_invoice.stock_link.inspect",
    }
)

# These three maps are also the frozen registry audit contract.  Supporting
# display/reference models are intentionally not advertised as capability
# sources.
_MODELS = {
    "cogs.entries.list": (
        "stock.move",
        "account.move",
        "account.move.line",
        "sale.order.line",
    ),
    "inventory.accounting_entries.list": (
        "stock.move",
        "account.move",
        "account.move.line",
    ),
    "report.inventory_valuation": (
        "stock_account.stock.valuation.report",
        "stock.move",
        "account.move.line",
    ),
    "purchase_bill.matching.inspect": (
        "purchase.bill.line.match",
        "purchase.order.line",
        "account.move",
        "account.move.line",
    ),
    "sale_invoice.stock_link.inspect": (
        "sale.order.line",
        "stock.move",
        "account.move",
        "account.move.line",
    ),
}
_ACCESS = {
    capability_id: tuple(
        (model, "read")
        for model in models
        if model != "stock_account.stock.valuation.report"
    )
    for capability_id, models in _MODELS.items()
}
_GROUPS = {
    capability_id: ("account.group_account_readonly",)
    for capability_id in CAPABILITY_IDS
}

_LIST_CAPABILITIES = frozenset(
    {"cogs.entries.list", "inventory.accounting_entries.list"}
)
_COGS_PARAMETERS = {
    "date_from",
    "date_to",
    "invoice_id",
    "product_id",
    "after",
    "limit",
}
_INVENTORY_PARAMETERS = {
    "date_from",
    "date_to",
    "product_id",
    "after",
    "limit",
}


def requires_rollback_only(payload: Any) -> bool:
    """Return whether this request needs report-compatible rollback isolation."""

    return (
        isinstance(payload, dict)
        and payload.get("capability_id") == "report.inventory_valuation"
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


def _valid_id(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _canonical_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return date_type.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _canonical_datetime(value: Any) -> bool:
    if not isinstance(value, str) or not value.endswith("Z"):
        return False
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return False
    return parsed.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ") == value


def _optional_id(value: Any) -> bool:
    return value is None or _valid_id(value)


def _valid_list_parameters(capability_id: str, parameters: Any) -> bool:
    expected = (
        _COGS_PARAMETERS
        if capability_id == "cogs.entries.list"
        else _INVENTORY_PARAMETERS
    )
    if not isinstance(parameters, dict) or set(parameters) != expected:
        return False
    date_from = parameters["date_from"]
    date_to = parameters["date_to"]
    if (
        date_from is not None
        and not _canonical_date(date_from)
        or date_to is not None
        and not _canonical_date(date_to)
        or date_from is not None
        and date_to is not None
        and date_from > date_to
        or not _optional_id(parameters["product_id"])
    ):
        return False
    if capability_id == "cogs.entries.list" and not _optional_id(
        parameters["invoice_id"]
    ):
        return False
    limit = parameters["limit"]
    if not _valid_id(limit) or limit > 1001:
        return False
    after = parameters["after"]
    if after is None:
        return True
    return (
        isinstance(after, list)
        and len(after) == 2
        and _valid_id(after[1])
        and (
            _canonical_date(after[0])
            if capability_id == "cogs.entries.list"
            else _canonical_datetime(after[0])
        )
    )


def _validated_payload(
    payload: Any, company_id: int, failure_type: Any
) -> tuple[str, dict[str, Any]]:
    if (
        not isinstance(payload, dict)
        or set(payload) != {"capability_id", "company_id", "parameters"}
        or not _valid_id(payload["company_id"])
        or payload["company_id"] != company_id
        or payload["capability_id"] not in CAPABILITY_IDS
    ):
        raise _protocol_failure(failure_type)
    capability_id = payload["capability_id"]
    parameters = payload["parameters"]
    if capability_id in _LIST_CAPABILITIES:
        valid = _valid_list_parameters(capability_id, parameters)
    elif capability_id == "report.inventory_valuation":
        valid = (
            isinstance(parameters, dict)
            and set(parameters) == {"date"}
            and (parameters["date"] is None or _canonical_date(parameters["date"]))
        )
    else:
        key = (
            "bill_id"
            if capability_id == "purchase_bill.matching.inspect"
            else "invoice_id"
        )
        valid = (
            isinstance(parameters, dict)
            and set(parameters) == {key}
            and _valid_id(parameters[key])
        )
    if not valid:
        raise _protocol_failure(failure_type)
    return capability_id, parameters


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


def _scope_page(env: Any, capability_id: str, company_id: int) -> dict[str, Any]:
    company_visible = bool(
        env["res.company"].search_count([("id", "=", company_id)], limit=1)
    )
    module_installed = all(
        env.registry.get(model_name) is not None
        for model_name in _MODELS[capability_id]
    )
    access_allowed = bool(
        company_visible
        and module_installed
        and all(env.user.has_group(group) for group in _GROUPS[capability_id])
        and all(
            env[model_name].has_access(operation)
            for model_name, operation in _ACCESS[capability_id]
        )
    )
    return _empty_page(
        env,
        company_visible=company_visible,
        module_installed=module_installed,
        access_allowed=access_allowed,
    )


def _model(env: Any, name: str, company_id: int) -> Any:
    return env[name].with_context(allowed_company_ids=[company_id])


def _record_id(value: Any) -> int | None:
    if value in (None, False):
        return None
    record_id = value if _valid_id(value) else getattr(value, "id", None)
    if not _valid_id(record_id):
        raise ValueError("invalid related record")
    return record_id


def _optional_text(value: Any) -> str | None:
    if value in (None, False):
        return None
    if not isinstance(value, str) or not value:
        raise ValueError("invalid text")
    return value


def _required_text(value: Any) -> str:
    text = _optional_text(value)
    if text is None:
        raise ValueError("missing text")
    return text


def _date_text(value: Any) -> str:
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, date_type):
        return value.isoformat()
    if _canonical_date(value):
        return value
    raise ValueError("invalid date")


def _datetime_text(value: Any) -> str:
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            value = value.astimezone(UTC).replace(tzinfo=None)
        return value.replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    if isinstance(value, str):
        candidate = value
        if candidate.endswith("Z"):
            candidate = candidate[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(candidate)
        except ValueError as exc:
            raise ValueError("invalid datetime") from exc
        return _datetime_text(parsed)
    raise ValueError("invalid datetime")


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


def _named_ref(record: Any) -> dict[str, Any]:
    record_id = _record_id(record)
    if record_id is None:
        raise ValueError("missing related record")
    return {"id": record_id, "name": _required_text(record.name)}


def _optional_named_ref(record: Any) -> dict[str, Any] | None:
    return None if not record else _named_ref(record)


def _account_ref(record: Any) -> dict[str, Any]:
    result = _named_ref(record)
    return {
        "id": result["id"],
        "code": _required_text(record.code),
        "name": result["name"],
    }


def _currency_ref(record: Any) -> dict[str, Any]:
    result = _named_ref(record)
    code = result["name"]
    if len(code) > 3:
        raise ValueError("invalid currency code")
    return {"id": result["id"], "code": code}


def _company_matches(record: Any, company_id: int) -> bool:
    return _record_id(record.company_id) == company_id


def _accounting_lines(entry: Any, company_id: int) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    balance_total = Decimal(0)
    for line in sorted(entry.line_ids, key=lambda item: item.id):
        if not _company_matches(line, company_id):
            raise ValueError("cross-company accounting line")
        debit = _decimal(line.debit)
        credit = _decimal(line.credit)
        if debit < 0 or credit < 0:
            raise ValueError("invalid debit or credit")
        balance = debit - credit
        balance_total += balance
        lines.append(
            {
                "id": _record_id(line),
                "account": _account_ref(line.account_id),
                "debit": _decimal_text(debit),
                "credit": _decimal_text(credit),
                "balance": _decimal_text(balance),
            }
        )
    if not lines or balance_total != 0:
        raise ValueError("unbalanced accounting entry")
    return lines


def _accounting_entry(entry: Any, company_id: int) -> dict[str, Any]:
    if not _company_matches(entry, company_id) or entry.state != "posted":
        raise ValueError("invalid stock accounting entry")
    return {
        "id": _record_id(entry),
        "name": _optional_text(entry.name),
        "date": _date_text(entry.date),
        "state": "posted",
        "lines": _accounting_lines(entry, company_id),
    }


def _stock_move(move: Any, company_id: int) -> dict[str, Any]:
    if not _company_matches(move, company_id) or move.state != "done":
        raise ValueError("invalid stock move")
    entry = move.account_move_id
    return {
        "id": _record_id(move),
        "date": _datetime_text(move.date),
        "state": "done",
        "reference": _optional_text(move.reference),
        "product": _named_ref(move.product_id),
        "quantity": _decimal_text(move.quantity),
        "uom": _named_ref(move.product_uom),
        "value": _decimal_text(move.value),
        "accounting_entry": (_accounting_entry(entry, company_id) if entry else None),
    }


def _after_domain(field: str, after: list[Any]) -> list[Any]:
    return [
        "|",
        (field, "<", after[0]),
        "&",
        (field, "=", after[0]),
        ("id", "<", after[1]),
    ]


def _sale_stock_move_matches(
    move: Any, move_type: str, *, refund_downpayment: bool = False
) -> bool:
    if move.state != "done":
        return False
    if move_type == "out_invoice" or (move_type == "out_refund" and refund_downpayment):
        return move.location_dest_id.usage == "customer"
    if move_type == "out_refund":
        return move.location_id.usage == "customer"
    raise ValueError("invalid sale document type")


def _refund_uses_delivery_direction(invoice: Any) -> bool:
    return invoice.move_type == "out_refund" and any(
        sale_line.is_downpayment
        for invoice_line in invoice.invoice_line_ids
        for sale_line in invoice_line.sale_line_ids
    )


def _cogs_items(
    env: Any, company_id: int, parameters: dict[str, Any]
) -> tuple[bool, list[dict[str, Any]]]:
    model = _model(env, "account.move.line", company_id)
    domain: list[Any] = [
        ("company_id", "=", company_id),
        ("display_type", "=", "cogs"),
        ("parent_state", "=", "posted"),
        ("move_id.move_type", "in", ("out_invoice", "out_refund")),
    ]
    if parameters["date_from"] is not None:
        domain.append(("date", ">=", parameters["date_from"]))
    if parameters["date_to"] is not None:
        domain.append(("date", "<=", parameters["date_to"]))
    if parameters["invoice_id"] is not None:
        domain.append(("move_id", "=", parameters["invoice_id"]))
    if parameters["product_id"] is not None:
        domain.append(("product_id", "=", parameters["product_id"]))

    after = parameters["after"]
    cursor_found = True
    if after is not None:
        cursor_found = bool(
            model.search_count(
                [*domain, ("date", "=", after[0]), ("id", "=", after[1])],
                limit=1,
            )
        )
        if not cursor_found:
            return False, []
        domain.extend(_after_domain("date", after))

    rows = model.search(
        domain,
        order="date desc,id desc",
        limit=parameters["limit"],
    )
    items: list[dict[str, Any]] = []
    for line in rows:
        invoice = line.move_id
        if (
            not _company_matches(line, company_id)
            or not _company_matches(invoice, company_id)
            or line.display_type != "cogs"
            or invoice.state != "posted"
            or invoice.move_type not in {"out_invoice", "out_refund"}
        ):
            raise ValueError("out-of-scope COGS line")
        origin = line.cogs_origin_id
        if origin and not _company_matches(origin, company_id):
            raise ValueError("cross-company COGS origin")
        sale_lines = origin.sale_line_ids if origin else []
        if any(not _company_matches(sale_line, company_id) for sale_line in sale_lines):
            raise ValueError("cross-company sale line")
        refund_downpayment = _refund_uses_delivery_direction(invoice)
        sale_line_ids = sorted({_record_id(value) for value in sale_lines})
        stock_move_ids = sorted(
            {
                _record_id(move)
                for sale_line in sale_lines
                for move in sale_line.move_ids
                if _company_matches(move, company_id)
                and _sale_stock_move_matches(
                    move,
                    invoice.move_type,
                    refund_downpayment=refund_downpayment,
                )
            }
        )
        debit = _decimal(line.debit)
        credit = _decimal(line.credit)
        if debit < 0 or credit < 0:
            raise ValueError("invalid COGS amount")
        items.append(
            {
                "id": _record_id(line),
                "date": _date_text(line.date),
                "company_id": company_id,
                "invoice": {
                    "id": _record_id(invoice),
                    "name": _optional_text(invoice.name),
                    "move_type": invoice.move_type,
                    "state": "posted",
                },
                "origin_invoice_line_id": _record_id(origin),
                "account": _account_ref(line.account_id),
                "product": _optional_named_ref(line.product_id),
                "label": _optional_text(line.name),
                "quantity": _decimal_text(line.quantity),
                "debit": _decimal_text(debit),
                "credit": _decimal_text(credit),
                "balance": _decimal_text(debit - credit),
                "company_currency": _currency_ref(line.company_currency_id),
                "sale_order_line_ids": sale_line_ids,
                "stock_move_ids": stock_move_ids,
            }
        )
    return cursor_found, items


def _inventory_items(
    env: Any, company_id: int, parameters: dict[str, Any]
) -> tuple[bool, list[dict[str, Any]]]:
    model = _model(env, "stock.move", company_id)
    domain: list[Any] = [
        ("company_id", "=", company_id),
        ("state", "=", "done"),
        ("account_move_id", "!=", False),
        ("account_move_id.state", "=", "posted"),
    ]
    if parameters["date_from"] is not None:
        domain.append(("date", ">=", f"{parameters['date_from']} 00:00:00"))
    if parameters["date_to"] is not None:
        domain.append(("date", "<=", f"{parameters['date_to']} 23:59:59"))
    if parameters["product_id"] is not None:
        domain.append(("product_id", "=", parameters["product_id"]))

    after = parameters["after"]
    cursor_found = True
    if after is not None:
        database_after = after[0].replace("T", " ").removesuffix("Z")
        cursor_found = bool(
            model.search_count(
                [
                    *domain,
                    ("date", "=", database_after),
                    ("id", "=", after[1]),
                ],
                limit=1,
            )
        )
        if not cursor_found:
            return False, []
        domain.extend(_after_domain("date", [database_after, after[1]]))

    rows = model.search(
        domain,
        order="date desc,id desc",
        limit=parameters["limit"],
    )
    items: list[dict[str, Any]] = []
    for move in rows:
        entry = move.account_move_id
        if (
            not _company_matches(move, company_id)
            or move.state != "done"
            or not entry
            or not _company_matches(entry, company_id)
            or entry.state != "posted"
        ):
            raise ValueError("out-of-scope inventory accounting move")
        journal = entry.journal_id
        journal_ref = _account_ref(journal)
        items.append(
            {
                "id": _record_id(move),
                "date": _datetime_text(move.date),
                "company_id": company_id,
                "reference": _optional_text(move.reference),
                "state": "done",
                "product": _named_ref(move.product_id),
                "quantity": _decimal_text(move.quantity),
                "uom": _named_ref(move.product_uom),
                "value": _decimal_text(move.value),
                "is_in": bool(move.is_in),
                "is_out": bool(move.is_out),
                "account_move": {
                    "id": _record_id(entry),
                    "name": _optional_text(entry.name),
                    "date": _date_text(entry.date),
                    "state": "posted",
                    "journal": journal_ref,
                },
                "lines": _accounting_lines(entry, company_id),
                "company_currency": _currency_ref(move.company_currency_id),
            }
        )
    return cursor_found, items


def _report_section(report_data: dict[str, Any], key: str) -> dict[str, Any]:
    section = report_data.get(key)
    if not isinstance(section, dict) or "value" not in section:
        raise ValueError("invalid valuation report section")
    return section


def _account_value_map(section: dict[str, Any]) -> dict[int, Decimal]:
    raw = section.get("lines_by_account_id", {})
    if not isinstance(raw, dict):
        raise TypeError("invalid valuation account lines")
    result: dict[int, Decimal] = {}
    for raw_id, value in raw.items():
        try:
            account_id = int(raw_id)
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid valuation account id") from exc
        if not _valid_id(account_id) or not isinstance(value, dict):
            raise ValueError("invalid valuation account value")
        result[account_id] = _decimal(value.get("value"))
    return result


def _variation_map(section: dict[str, Any]) -> dict[int, tuple[Decimal, Decimal]]:
    raw_lines = section.get("lines", [])
    if not isinstance(raw_lines, list):
        raise TypeError("invalid valuation variation lines")
    result: dict[int, tuple[Decimal, Decimal]] = {}
    for line in raw_lines:
        if not isinstance(line, dict):
            raise TypeError("invalid valuation variation line")
        account_id = line.get("account_id")
        if not _valid_id(account_id):
            raise ValueError("invalid valuation account id")
        debit = _decimal(line.get("debit"))
        credit = _decimal(line.get("credit"))
        if debit < 0 or credit < 0:
            raise ValueError("invalid valuation movement")
        old_debit, old_credit = result.get(account_id, (Decimal(0), Decimal(0)))
        result[account_id] = (old_debit + debit, old_credit + credit)
    return result


def _report_accounts(report_data: dict[str, Any]) -> dict[int, dict[str, Any]]:
    raw = report_data.get("accounts_by_id")
    if not isinstance(raw, dict):
        raise TypeError("invalid valuation account metadata")
    result: dict[int, dict[str, Any]] = {}
    for raw_id, value in raw.items():
        try:
            account_id = int(raw_id)
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid valuation account metadata") from exc
        if (
            not _valid_id(account_id)
            or not isinstance(value, dict)
            or value.get("id") != account_id
        ):
            raise ValueError("invalid valuation account metadata")
        result[account_id] = value
    return result


def _optional_report_total(report_data: dict[str, Any], key: str) -> str | None:
    if key not in report_data:
        return None
    section = _report_section(report_data, key)
    return _decimal_text(section["value"])


def _valuation_item(
    env: Any, company_id: int, parameters: dict[str, Any]
) -> dict[str, Any]:
    company = _model(env, "res.company", company_id).search(
        [("id", "=", company_id)], limit=1
    )
    if len(company) != 1:
        raise ValueError("company disappeared")
    company = company[0]
    report_date = parameters["date"]
    report_model = _model(
        env, "stock_account.stock.valuation.report", company_id
    ).with_company(company)
    report_values = report_model.get_report_values(report_date or False)
    if not isinstance(report_values, dict) or not isinstance(
        report_values.get("data"), dict
    ):
        raise TypeError("invalid inventory valuation report")
    report_data = report_values["data"]
    reported_company_id = report_data.get("company_id")
    reported_currency_id = report_data.get("currency_id")
    if reported_company_id != company_id or reported_currency_id != _record_id(
        company.currency_id
    ):
        raise ValueError("cross-company valuation report")

    initial = _report_section(report_data, "initial_balance")
    ending = _report_section(report_data, "ending_stock")
    variation = _report_section(report_data, "stock_variation")
    initial_by_account = _account_value_map(initial)
    ending_by_account = _account_value_map(ending)
    variation_by_account = _variation_map(variation)
    account_metadata = _report_accounts(report_data)
    account_ids = sorted(
        set(initial_by_account) | set(ending_by_account) | set(variation_by_account)
    )
    if any(account_id not in account_metadata for account_id in account_ids):
        raise ValueError("valuation account metadata is incomplete")

    accounts: list[dict[str, Any]] = []
    for account_id in account_ids:
        metadata = account_metadata[account_id]
        debit, credit = variation_by_account.get(account_id, (Decimal(0), Decimal(0)))
        accounts.append(
            {
                "account": {
                    "id": account_id,
                    "code": _required_text(metadata.get("code")),
                    "name": _required_text(metadata.get("name")),
                },
                "initial_balance": _decimal_text(
                    initial_by_account.get(account_id, Decimal(0))
                ),
                "ending_stock": _decimal_text(
                    ending_by_account.get(account_id, Decimal(0))
                ),
                "variation_debit": _decimal_text(debit),
                "variation_credit": _decimal_text(credit),
            }
        )
    return {
        "as_of_date": report_date,
        "company": {"id": company_id, "name": _required_text(company.name)},
        "currency": _currency_ref(company.currency_id),
        "initial_balance": _decimal_text(initial["value"]),
        "ending_stock": _decimal_text(ending["value"]),
        "stock_variation": _decimal_text(variation["value"]),
        "inventory_loss": _optional_report_total(report_data, "inventory_loss"),
        "not_invoiced_delivered_goods": _optional_report_total(
            report_data, "not_invoiced_delivered_goods"
        ),
        "not_invoiced_received_goods": _optional_report_total(
            report_data, "not_invoiced_received_goods"
        ),
        "cost_of_production": _optional_report_total(report_data, "cost_of_production"),
        "accounts": accounts,
    }


def _purchase_item(
    env: Any, company_id: int, parameters: dict[str, Any]
) -> dict[str, Any] | None:
    bills = _model(env, "account.move", company_id).search(
        [
            ("id", "=", parameters["bill_id"]),
            ("company_id", "=", company_id),
            ("move_type", "in", ("in_invoice", "in_refund")),
        ],
        limit=2,
    )
    if not bills:
        return None
    if len(bills) != 1:
        raise ValueError("ambiguous vendor bill")
    bill = bills[0]
    if not _company_matches(bill, company_id):
        raise ValueError("cross-company vendor bill")

    product_lines = sorted(
        (line for line in bill.invoice_line_ids if line.display_type == "product"),
        key=lambda line: line.id,
    )
    line_ids = [_record_id(line) for line in product_lines]
    unmatched_view_ids: set[int] = set()
    if line_ids:
        # This view has no company record rule and uses negative row ids for AML
        # rows.  Scope it explicitly and expose only its positive aml_id values.
        view_rows = _model(env, "purchase.bill.line.match", company_id).search(
            [
                ("company_id", "=", company_id),
                ("aml_id", "in", line_ids),
            ]
        )
        unmatched_view_ids = {_record_id(row.aml_id) for row in view_rows if row.aml_id}

    lines: list[dict[str, Any]] = []
    order_ids: set[int] = set()
    for line in product_lines:
        if not _company_matches(line, company_id):
            raise ValueError("cross-company vendor bill line")
        purchase_line = line.purchase_line_id
        in_unmatched_queue = _record_id(line) in unmatched_view_ids
        if bill.state in {"draft", "posted"} and (
            in_unmatched_queue != (not bool(purchase_line))
        ):
            raise ValueError("purchase matching view is inconsistent")
        purchase_value = None
        if purchase_line:
            if not _company_matches(purchase_line, company_id):
                raise ValueError("cross-company purchase line")
            order_id = _record_id(purchase_line.order_id)
            if order_id is None:
                raise ValueError("purchase line has no order")
            order_ids.add(order_id)
            purchase_value = {
                "id": _record_id(purchase_line),
                "order_id": order_id,
                "ordered_quantity": _decimal_text(purchase_line.product_qty),
                "received_quantity": _decimal_text(purchase_line.qty_received),
                "invoiced_quantity": _decimal_text(purchase_line.qty_invoiced),
                "to_invoice_quantity": _decimal_text(purchase_line.qty_to_invoice),
            }
        lines.append(
            {
                "id": _record_id(line),
                "product": _optional_named_ref(line.product_id),
                "label": _optional_text(line.name),
                "quantity": _decimal_text(line.quantity),
                "price_subtotal": _decimal_text(line.price_subtotal),
                "purchase_line": purchase_value,
                "unmatched_queue": in_unmatched_queue,
            }
        )
    return {
        "id": _record_id(bill),
        "name": _optional_text(bill.name),
        "move_type": bill.move_type,
        "state": bill.state,
        "company_id": company_id,
        "partner": _optional_named_ref(bill.partner_id),
        "currency": _currency_ref(bill.currency_id),
        "is_purchase_matched": all(line["purchase_line"] is not None for line in lines),
        "purchase_order_ids": sorted(order_ids),
        "lines": lines,
    }


def _line_sale_lines(invoice: Any, line: Any) -> list[Any]:
    by_id = {_record_id(sale_line): sale_line for sale_line in line.sale_line_ids}
    if by_id or invoice.move_type != "out_refund" or not invoice.reversed_entry_id:
        return [by_id[record_id] for record_id in sorted(by_id)]
    candidates = [
        source_line
        for source_line in invoice.reversed_entry_id.invoice_line_ids
        if source_line.display_type == "product"
        and _record_id(source_line.product_id) == _record_id(line.product_id)
    ]
    if len(candidates) == 1:
        by_id = {
            _record_id(sale_line): sale_line
            for sale_line in candidates[0].sale_line_ids
        }
    return [by_id[record_id] for record_id in sorted(by_id)]


def _sale_item(
    env: Any, company_id: int, parameters: dict[str, Any]
) -> dict[str, Any] | None:
    invoices = _model(env, "account.move", company_id).search(
        [
            ("id", "=", parameters["invoice_id"]),
            ("company_id", "=", company_id),
            ("move_type", "in", ("out_invoice", "out_refund")),
        ],
        limit=2,
    )
    if not invoices:
        return None
    if len(invoices) != 1:
        raise ValueError("ambiguous customer invoice")
    invoice = invoices[0]
    if not _company_matches(invoice, company_id):
        raise ValueError("cross-company customer invoice")

    lines: list[dict[str, Any]] = []
    stock_move_ids: set[int] = set()
    account_move_ids: set[int] = set()
    refund_downpayment = _refund_uses_delivery_direction(invoice)
    for line in sorted(
        (item for item in invoice.invoice_line_ids if item.display_type == "product"),
        key=lambda item: item.id,
    ):
        if not _company_matches(line, company_id):
            raise ValueError("cross-company customer invoice line")
        sale_lines = _line_sale_lines(invoice, line)
        for sale_line in sale_lines:
            if not _company_matches(sale_line, company_id):
                raise ValueError("cross-company sale line")
        moves_by_id = {
            _record_id(move): move
            for sale_line in sale_lines
            for move in sale_line.move_ids
            if _sale_stock_move_matches(
                move,
                invoice.move_type,
                refund_downpayment=refund_downpayment,
            )
        }
        stock_moves: list[dict[str, Any]] = []
        for move_id in sorted(moves_by_id):
            move = moves_by_id[move_id]
            value = _stock_move(move, company_id)
            stock_moves.append(value)
            stock_move_ids.add(move_id)
            if value["accounting_entry"] is not None:
                account_move_ids.add(value["accounting_entry"]["id"])
        lines.append(
            {
                "id": _record_id(line),
                "product": _optional_named_ref(line.product_id),
                "quantity": _decimal_text(line.quantity),
                "sale_order_line_ids": sorted(
                    _record_id(sale_line) for sale_line in sale_lines
                ),
                "stock_moves": stock_moves,
            }
        )
    return {
        "id": _record_id(invoice),
        "name": _optional_text(invoice.name),
        "move_type": invoice.move_type,
        "state": invoice.state,
        "company_id": company_id,
        "lines": lines,
        "stock_move_ids": sorted(stock_move_ids),
        "account_move_ids": sorted(account_move_ids),
    }


def dispatch(
    env: Any,
    payload: dict[str, Any],
    company_id: int,
    *,
    failure_type: Any,
) -> dict[str, Any]:
    """Validate, gate and execute one allowlisted inventory-accounting read."""

    try:
        capability_id, parameters = _validated_payload(
            payload, company_id, failure_type
        )
        page = _scope_page(env, capability_id, company_id)
        if not page["access_allowed"]:
            return page
        if capability_id == "cogs.entries.list":
            cursor_found, items = _cogs_items(env, company_id, parameters)
        elif capability_id == "inventory.accounting_entries.list":
            cursor_found, items = _inventory_items(env, company_id, parameters)
        elif capability_id == "report.inventory_valuation":
            cursor_found = True
            items = [_valuation_item(env, company_id, parameters)]
        elif capability_id == "purchase_bill.matching.inspect":
            cursor_found = True
            item = _purchase_item(env, company_id, parameters)
            items = [] if item is None else [item]
        else:
            cursor_found = True
            item = _sale_item(env, company_id, parameters)
            items = [] if item is None else [item]
        return {
            **page,
            "cursor_found": cursor_found,
            "items": items,
        }
    except failure_type:
        raise
    except Exception as exc:
        raise _runtime_failure(failure_type) from exc
