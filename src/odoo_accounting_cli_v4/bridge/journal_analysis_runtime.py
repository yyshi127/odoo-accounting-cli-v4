"""Odoo-side runtime for fixed journal and analytic analysis reads."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

ACTION = "accounting.journal_analysis.read"
CAPABILITY_IDS = frozenset(
    {
        "analytic.line.summary",
        "journal.accounting_date.resolve",
        "journal_item.analysis.summary",
    }
)
GROUP_BY_FIELDS = {"account": "account_id", "journal": "journal_id"}
_AMOUNT_KEYS = ("debit", "credit", "balance")
_AGGREGATES = ("__count", "debit:sum", "credit:sum", "balance:sum")
_JOURNAL_FIELDS = {"code", "name", "company_id", "accounting_date"}
_MOVE_LINE_FIELDS = {
    "company_id",
    "parent_state",
    "date",
    "account_id",
    "journal_id",
    "debit",
    "credit",
    "balance",
}
_ANALYTIC_PLAN_FIELDS = {"name", "parent_id"}
_ANALYTIC_ACCOUNT_FIELDS = {
    "name",
    "code",
    "plan_id",
    "root_plan_id",
    "company_id",
}
_ANALYTIC_LINE_FIELDS = {
    "company_id",
    "date",
    "amount",
    "unit_amount",
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


def _date_text(value: Any) -> str:
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        return date.fromisoformat(value).isoformat()
    raise ValueError("invalid date")


def _canonical_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return _date_text(value) == value
    except ValueError:
        return False


def _valid_parameters(capability_id: str, parameters: Any) -> bool:
    if not isinstance(parameters, dict):
        return False
    if capability_id == "journal.accounting_date.resolve":
        return bool(
            set(parameters) == {"journal_id", "date", "has_tax"}
            and _positive_id(parameters["journal_id"])
            and _canonical_date(parameters["date"])
            and isinstance(parameters["has_tax"], bool)
        )
    if capability_id == "analytic.line.summary":
        required = {"date_from", "date_to", "plan_id", "analytic_account_id"}
        return bool(
            set(parameters) == required
            and _canonical_date(parameters["date_from"])
            and _canonical_date(parameters["date_to"])
            and parameters["date_from"] <= parameters["date_to"]
            and _positive_id(parameters["plan_id"])
            and (
                parameters["analytic_account_id"] is None
                or _positive_id(parameters["analytic_account_id"])
            )
        )
    return bool(
        set(parameters) == {"date_from", "date_to", "group_by"}
        and _canonical_date(parameters["date_from"])
        and _canonical_date(parameters["date_to"])
        and parameters["date_from"] <= parameters["date_to"]
        and isinstance(parameters["group_by"], str)
        and parameters["group_by"] in GROUP_BY_FIELDS
    )


def _validated_payload(
    payload: Any, company_id: int, failure_type: Any
) -> tuple[str, dict[str, Any]]:
    if (
        not isinstance(payload, dict)
        or set(payload) != {"capability_id", "company_id", "parameters"}
        or not isinstance(payload["capability_id"], str)
        or payload["capability_id"] not in CAPABILITY_IDS
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


def _required_models(capability_id: str, parameters: dict[str, Any]) -> tuple[str, ...]:
    if capability_id == "journal.accounting_date.resolve":
        return ("res.company", "account.journal")
    if capability_id == "analytic.line.summary":
        return (
            "res.company",
            "res.currency",
            "account.analytic.plan",
            "account.analytic.account",
            "account.analytic.line",
        )
    group_model = (
        "account.account" if parameters["group_by"] == "account" else "account.journal"
    )
    return (
        "res.company",
        "res.currency",
        "account.move.line",
        group_model,
    )


def _field_shape_available(
    env: Any, capability_id: str, parameters: dict[str, Any]
) -> bool:
    if capability_id == "journal.accounting_date.resolve":
        return _JOURNAL_FIELDS <= set(getattr(env["account.journal"], "_fields", {}))
    if capability_id == "analytic.line.summary":
        return bool(
            {"currency_id"} <= set(getattr(env["res.company"], "_fields", {}))
            and {"name"} <= set(getattr(env["res.currency"], "_fields", {}))
            and _ANALYTIC_PLAN_FIELDS
            <= set(getattr(env["account.analytic.plan"], "_fields", {}))
            and _ANALYTIC_ACCOUNT_FIELDS
            <= set(getattr(env["account.analytic.account"], "_fields", {}))
            and _ANALYTIC_LINE_FIELDS
            <= set(getattr(env["account.analytic.line"], "_fields", {}))
        )
    common = bool(
        {"currency_id"} <= set(getattr(env["res.company"], "_fields", {}))
        and {"name"} <= set(getattr(env["res.currency"], "_fields", {}))
        and _MOVE_LINE_FIELDS <= set(getattr(env["account.move.line"], "_fields", {}))
    )
    if parameters["group_by"] == "account":
        return common and {"code", "name", "company_ids"} <= set(
            getattr(env["account.account"], "_fields", {})
        )
    return common and {"code", "name", "company_id"} <= set(
        getattr(env["account.journal"], "_fields", {})
    )


def _scope_page(
    env: Any,
    capability_id: str,
    parameters: dict[str, Any],
    company_id: int,
    failure_type: Any,
) -> dict[str, Any]:
    company_visible = bool(
        env["res.company"].search_count([("id", "=", company_id)], limit=1)
    )
    models = _required_models(capability_id, parameters)
    module_installed = all(env.registry.get(name) is not None for name in models)
    if (
        company_visible
        and module_installed
        and not _field_shape_available(env, capability_id, parameters)
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
    return env[name].with_context(allowed_company_ids=[company_id], active_test=False)


def _record_id(value: Any) -> int:
    record_id = getattr(value, "id", value)
    if not _positive_id(record_id):
        raise ValueError("invalid record id")
    return record_id


def _text(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("invalid text")
    return value


def _company_id(record: Any) -> int:
    return _record_id(record.company_id)


def _one_company(env: Any, company_id: int) -> Any:
    companies = _model(env, "res.company", company_id).search(
        [("id", "=", company_id)], limit=2
    )
    if len(companies) != 1:
        raise ValueError("company disappeared")
    return companies[0]


def _coded_ref(record: Any) -> dict[str, Any]:
    return {
        "id": _record_id(record),
        "code": _text(record.code),
        "name": _text(record.name),
    }


def _currency(record: Any) -> dict[str, Any]:
    code = _text(record.name)
    if len(code) > 3:
        raise ValueError("invalid currency code")
    return {"id": _record_id(record), "code": code}


def _named_ref(record: Any) -> dict[str, Any]:
    return {"id": _record_id(record), "name": _text(record.name)}


def _analytic_account_ref(record: Any, company_id: int) -> dict[str, Any]:
    record_company = getattr(record, "company_id", False)
    if record_company and _record_id(record_company) != company_id:
        raise ValueError("cross-company analytic account group")
    code = getattr(record, "code", False)
    if code is not False and code is not None:
        code = _text(code)
    else:
        code = None
    return {"id": _record_id(record), "name": _text(record.name), "code": code}


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


def _accounting_date_item(
    env: Any, company_id: int, parameters: dict[str, Any]
) -> dict[str, Any] | None:
    company = _one_company(env, company_id)
    records = _model(env, "account.journal", company_id).search(
        [
            ("id", "=", parameters["journal_id"]),
            ("company_id", "=", company_id),
        ],
        limit=2,
    )
    if len(records) > 1:
        raise ValueError("ambiguous journal")
    if not records:
        return None
    journal = records[0]
    if _company_id(journal) != company_id:
        raise ValueError("cross-company journal")
    target = parameters["date"]
    computed = (
        journal.with_company(company)
        .with_context(
            move_date=date.fromisoformat(target), has_tax=parameters["has_tax"]
        )
        .accounting_date
    )
    accounting_date = _date_text(computed)
    return {
        "company_id": company_id,
        "journal": _coded_ref(journal),
        "requested_date": target,
        "has_tax": parameters["has_tax"],
        "accounting_date": accounting_date,
        "adjusted": accounting_date != target,
    }


def _group_ref(record: Any, group_by: str, company_id: int) -> dict[str, Any]:
    if group_by == "journal":
        if _company_id(record) != company_id:
            raise ValueError("cross-company journal group")
    else:
        company_ids = {_record_id(company) for company in record.company_ids}
        if company_id not in company_ids:
            raise ValueError("cross-company account group")
    return _coded_ref(record)


def _summary_item(
    env: Any, company_id: int, parameters: dict[str, Any]
) -> dict[str, Any]:
    company = _one_company(env, company_id)
    field = GROUP_BY_FIELDS[parameters["group_by"]]
    domain = [
        ("company_id", "=", company_id),
        ("parent_state", "=", "posted"),
        ("date", ">=", parameters["date_from"]),
        ("date", "<=", parameters["date_to"]),
    ]
    rows = _model(env, "account.move.line", company_id)._read_group(
        domain,
        groupby=[field],
        aggregates=list(_AGGREGATES),
        order=f"{field} asc",
    )
    groups: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, (tuple, list)) or len(row) != 5:
            raise ValueError("invalid journal-item aggregate")
        count = row[1]
        if not _integer(count) or count <= 0:
            raise ValueError("invalid journal-item aggregate count")
        groups.append(
            {
                "group": _group_ref(row[0], parameters["group_by"], company_id),
                "row_count": count,
                "debit": _decimal_text(row[2]),
                "credit": _decimal_text(row[3]),
                "balance": _decimal_text(row[4]),
            }
        )
    groups.sort(key=lambda item: item["group"]["id"])
    ids = [item["group"]["id"] for item in groups]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate journal-item aggregate group")
    totals: dict[str, Any] = {"row_count": sum(item["row_count"] for item in groups)}
    for key in _AMOUNT_KEYS:
        totals[key] = _decimal_text(
            sum((_decimal(item[key]) for item in groups), Decimal(0))
        )
    return {
        "company_id": company_id,
        "date_from": parameters["date_from"],
        "date_to": parameters["date_to"],
        "basis": "posted_entries",
        "group_by": parameters["group_by"],
        "company_currency": _currency(company.currency_id),
        "groups": groups,
        "totals": totals,
    }


def _analytic_summary_item(
    env: Any, company_id: int, parameters: dict[str, Any]
) -> dict[str, Any] | None:
    company = _one_company(env, company_id)
    plan_records = _model(env, "account.analytic.plan", company_id).search(
        [("id", "=", parameters["plan_id"])], limit=2
    )
    if len(plan_records) > 1:
        raise ValueError("ambiguous analytic plan")
    if not plan_records:
        return None
    plan = plan_records[0]
    column_name = plan._column_name()
    line_model = _model(env, "account.analytic.line", company_id)
    field = getattr(line_model, "_fields", {}).get(column_name)
    if (
        not isinstance(column_name, str)
        or field is None
        or getattr(field, "comodel_name", None) != "account.analytic.account"
    ):
        raise ValueError("analytic plan column is unavailable")

    account_id = parameters["analytic_account_id"]
    if account_id is not None:
        accounts = _model(env, "account.analytic.account", company_id).search(
            [
                ("id", "=", account_id),
                ("plan_id", "child_of", parameters["plan_id"]),
                ("company_id", "in", [False, company_id]),
            ],
            limit=2,
        )
        if len(accounts) != 1:
            return None

    domain: list[Any] = [
        ("company_id", "=", company_id),
        ("date", ">=", parameters["date_from"]),
        ("date", "<=", parameters["date_to"]),
        (f"{column_name}.plan_id", "child_of", parameters["plan_id"]),
    ]
    if account_id is not None:
        domain.append((column_name, "=", account_id))
    rows = line_model._read_group(
        domain,
        groupby=[column_name],
        aggregates=["id:count", "amount:sum", "unit_amount:sum"],
        order=f"{column_name} asc",
    )
    groups: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, (tuple, list)) or len(row) != 4:
            raise ValueError("invalid analytic-line aggregate")
        count = row[1]
        if not _integer(count) or count <= 0:
            raise ValueError("invalid analytic-line aggregate count")
        groups.append(
            {
                "analytic_account": _analytic_account_ref(row[0], company_id),
                "row_count": count,
                "amount": _decimal_text(row[2]),
                "unit_amount": _decimal_text(row[3]),
            }
        )
    groups.sort(key=lambda item: item["analytic_account"]["id"])
    ids = [item["analytic_account"]["id"] for item in groups]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate analytic account aggregate group")
    totals = {
        "row_count": sum(item["row_count"] for item in groups),
        "amount": _decimal_text(
            sum((_decimal(item["amount"]) for item in groups), Decimal(0))
        ),
        "unit_amount": _decimal_text(
            sum((_decimal(item["unit_amount"]) for item in groups), Decimal(0))
        ),
    }
    return {
        "company_id": company_id,
        "date_from": parameters["date_from"],
        "date_to": parameters["date_to"],
        "basis": "analytic_lines",
        "group_by": "analytic_account",
        "plan": _named_ref(plan),
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
    """Validate, gate, and execute one allowlisted journal-analysis read."""

    try:
        capability_id, parameters = _validated_payload(
            payload, company_id, failure_type
        )
        page = _scope_page(env, capability_id, parameters, company_id, failure_type)
        if not page["access_allowed"]:
            return page
        if capability_id == "journal.accounting_date.resolve":
            item = _accounting_date_item(env, company_id, parameters)
            items = [] if item is None else [item]
        elif capability_id == "analytic.line.summary":
            item = _analytic_summary_item(env, company_id, parameters)
            items = [] if item is None else [item]
        else:
            items = [_summary_item(env, company_id, parameters)]
        return {**page, "items": items}
    except failure_type:
        raise
    except Exception as exc:
        raise _runtime_failure(failure_type) from exc
