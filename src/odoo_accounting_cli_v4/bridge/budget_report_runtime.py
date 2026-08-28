"""Odoo-side runtime for the official raw budget execution detail report."""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

ACTION = "accounting.budget_report.read"
_LINE_TYPES = frozenset({"budget", "achieved"})
_SOURCE_MODELS = frozenset({"budget.analytic", "account.analytic.line"})
_ROW_KEY = re.compile(r"^(?:bl|aal)[1-9][0-9]*$")
_POSITION_KEYS = (
    "date",
    "row_key",
    "budget_line_id",
    "line_type",
    "source_model",
    "source_id",
)
_MODELS = (
    "res.company",
    "res.users",
    "budget.report",
    "budget.analytic",
    "budget.line",
    "account.analytic.plan",
    "account.analytic.account",
    "account.analytic.line",
)
_REQUIRED_FIELDS = {
    "budget.report": {
        "date",
        "res_model",
        "res_id",
        "description",
        "company_id",
        "user_id",
        "line_type",
        "budget",
        "achieved",
        "theoretical",
        "budget_analytic_id",
        "budget_line_id",
    },
    "budget.analytic": {"name", "date_from", "date_to", "company_id"},
    "budget.line": {"budget_analytic_id", "company_id"},
    "account.analytic.plan": {"name", "root_id"},
    "account.analytic.account": {
        "name",
        "plan_id",
        "root_plan_id",
        "company_id",
    },
    "res.users": {"name"},
}
_QUERY_FIELDS = (
    "id",
    "date",
    "budget_analytic_id",
    "budget_line_id",
    "res_model",
    "res_id",
    "description",
    "company_id",
    "user_id",
    "line_type",
    "budget",
    "achieved",
    "theoretical",
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


def _record_not_found(failure_type: Any, object_name: str) -> Exception:
    return _failure(
        failure_type,
        "record_not_found",
        f"The requested {object_name} was not found.",
        4,
    )


def _invalid_request(failure_type: Any, message: str) -> Exception:
    return _failure(failure_type, "invalid_request", message, 2)


def _integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _positive_id(value: Any) -> bool:
    return _integer(value) and value > 0


def _date_text(value: Any) -> str:
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str) and date.fromisoformat(value).isoformat() == value:
        return value
    raise ValueError("invalid date")


def _optional_date(value: Any) -> bool:
    if value is None:
        return True
    try:
        return _date_text(value) == value
    except (TypeError, ValueError):
        return False


def _valid_after(value: Any) -> bool:
    return bool(
        isinstance(value, dict)
        and set(value) == set(_POSITION_KEYS)
        and _optional_date(value["date"])
        and value["date"] is not None
        and isinstance(value["row_key"], str)
        and _ROW_KEY.fullmatch(value["row_key"])
        and _positive_id(value["budget_line_id"])
        and isinstance(value["line_type"], str)
        and value["line_type"] in _LINE_TYPES
        and isinstance(value["source_model"], str)
        and value["source_model"] in _SOURCE_MODELS
        and _positive_id(value["source_id"])
    )


def _valid_parameters(parameters: Any) -> bool:
    if not isinstance(parameters, dict) or set(parameters) != {
        "budget_id",
        "budget_line_id",
        "date_from",
        "date_to",
        "plan_id",
        "analytic_account_id",
        "line_type",
        "after",
        "limit",
    }:
        return False
    budget_line_id = parameters["budget_line_id"]
    plan_id = parameters["plan_id"]
    account_id = parameters["analytic_account_id"]
    line_type = parameters["line_type"]
    after = parameters["after"]
    limit = parameters["limit"]
    return bool(
        _positive_id(parameters["budget_id"])
        and (budget_line_id is None or _positive_id(budget_line_id))
        and _optional_date(parameters["date_from"])
        and _optional_date(parameters["date_to"])
        and (
            plan_id is None
            and account_id is None
            or _positive_id(plan_id)
            and _positive_id(account_id)
        )
        and (
            line_type is None or isinstance(line_type, str) and line_type in _LINE_TYPES
        )
        and (after is None or _valid_after(after))
        and _integer(limit)
        and 1 <= limit <= 1001
    )


def _validated_payload(
    payload: Any, company_id: int, failure_type: Any
) -> dict[str, Any]:
    if (
        not isinstance(payload, dict)
        or set(payload) != {"company_id", "parameters"}
        or payload["company_id"] != company_id
        or not _valid_parameters(payload["parameters"])
    ):
        raise _protocol_failure(failure_type)
    return payload["parameters"]


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
        names <= set(getattr(env[model_name], "_fields", {}))
        for model_name, names in _REQUIRED_FIELDS.items()
    )


def _scope_page(env: Any, company_id: int, failure_type: Any) -> dict[str, Any]:
    company_visible = bool(
        env["res.company"].search_count([("id", "=", company_id)], limit=1)
    )
    module_installed = all(env.registry.get(name) is not None for name in _MODELS)
    if company_visible and module_installed and not _field_shape_available(env):
        raise _runtime_failure(failure_type)
    access_allowed = bool(
        company_visible
        and module_installed
        and env.user.has_group("account.group_account_readonly")
        and all(env[name].has_access("read") for name in _MODELS)
    )
    return _empty_page(
        env,
        company_visible=company_visible,
        module_installed=module_installed,
        access_allowed=access_allowed,
    )


def _model(env: Any, name: str, company_id: int) -> Any:
    return env[name].with_context(allowed_company_ids=[company_id], active_test=False)


def _one(model: Any, domain: list[Any]) -> Any | None:
    records = model.search(domain, limit=2)
    if len(records) > 1:
        raise ValueError("ambiguous record")
    return records[0] if records else None


def _record_id(value: Any) -> int:
    result = getattr(value, "id", value)
    if not _positive_id(result):
        raise ValueError("invalid record id")
    return result


def _text(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("invalid text")
    return value


def _optional_text(value: Any) -> str | None:
    return None if value in (None, False, "/") else _text(value)


def _decimal_text(value: Any) -> str:
    if isinstance(value, bool):
        raise TypeError("invalid decimal")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("invalid decimal") from exc
    if not number.is_finite():
        raise ValueError("invalid decimal")
    if number == 0:
        return "0"
    rendered = format(number, "f")
    return rendered.rstrip("0").rstrip(".") if "." in rendered else rendered


def _company_id(value: Any) -> int | None:
    if value in (None, False):
        return None
    return _record_id(value)


def _effective_filters(
    env: Any,
    company_id: int,
    parameters: dict[str, Any],
    failure_type: Any,
) -> tuple[Any, str, str, str | None]:
    budget = _one(
        _model(env, "budget.analytic", company_id),
        [
            ("id", "=", parameters["budget_id"]),
            ("company_id", "in", [False, company_id]),
        ],
    )
    if budget is None:
        raise _record_not_found(failure_type, "budget")

    if parameters["budget_line_id"] is not None:
        budget_line = _one(
            _model(env, "budget.line", company_id),
            [
                ("id", "=", parameters["budget_line_id"]),
                ("budget_analytic_id", "=", budget.id),
                ("company_id", "in", [False, company_id]),
            ],
        )
        if budget_line is None:
            raise _record_not_found(failure_type, "budget line")

    date_from = parameters["date_from"] or _date_text(budget.date_from)
    date_to = parameters["date_to"] or _date_text(budget.date_to)
    if date_from > date_to:
        raise _invalid_request(
            failure_type,
            "The effective report start date cannot be after the end date.",
        )

    plan_column = None
    if parameters["plan_id"] is not None:
        plan = _one(
            _model(env, "account.analytic.plan", company_id),
            [("id", "=", parameters["plan_id"])],
        )
        account = _one(
            _model(env, "account.analytic.account", company_id),
            [
                ("id", "=", parameters["analytic_account_id"]),
                ("plan_id", "child_of", parameters["plan_id"]),
                ("company_id", "in", [False, company_id]),
            ],
        )
        if plan is None or account is None:
            raise _record_not_found(failure_type, "analytic plan/account pair")
        plan_column = account.root_plan_id._column_name()
        if plan_column not in env["budget.report"]._fields:
            raise _runtime_failure(failure_type)
    return budget, date_from, date_to, plan_column


def _plan_columns(env: Any) -> list[tuple[str, int]]:
    project_plan, other_plans = env["account.analytic.plan"]._get_all_plans()
    report_fields = env["budget.report"]._fields
    result: list[tuple[str, int]] = []
    for plan in project_plan | other_plans:
        name = plan._column_name()
        if name in report_fields:
            result.append((name, _record_id(plan)))
    if len({name for name, _ in result}) != len(result):
        raise ValueError("duplicate analytic plan column")
    return sorted(result, key=lambda item: item[1])


def _base_domain(
    company_id: int,
    parameters: dict[str, Any],
    *,
    date_from: str,
    date_to: str,
    plan_column: str | None,
) -> list[Any]:
    domain: list[Any] = [
        ("budget_analytic_id", "=", parameters["budget_id"]),
        ("company_id", "in", [False, company_id]),
        ("date", ">=", date_from),
        ("date", "<=", date_to),
    ]
    if parameters["budget_line_id"] is not None:
        domain.append(("budget_line_id", "=", parameters["budget_line_id"]))
    if parameters["line_type"] is not None:
        domain.append(("line_type", "=", parameters["line_type"]))
    if plan_column is not None:
        domain.append((plan_column, "=", parameters["analytic_account_id"]))
    return domain


def _field_expressions(model: Any, query: Any, names: tuple[str, ...]) -> list[Any]:
    return [model._field_to_sql(model._table, name, query) for name in names]


def _position_expressions(model: Any, query: Any) -> list[Any]:
    return _field_expressions(
        model,
        query,
        ("date", "id", "budget_line_id", "line_type", "res_model", "res_id"),
    )


def _position_values(after: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(after[key] for key in _POSITION_KEYS)


def _position_clause(
    expressions: list[Any], values: tuple[Any, ...], operator: str
) -> Any:
    from odoo.tools import SQL

    if operator not in {"=", ">"}:
        raise ValueError("invalid position operator")
    return SQL(
        f"(%s) {operator} (%s)",
        SQL(", ").join(expressions),
        SQL(", ").join(SQL("%s", value) for value in values),
    )


def _query_rows(
    env: Any,
    company_id: int,
    parameters: dict[str, Any],
    *,
    date_from: str,
    date_to: str,
    plan_column: str | None,
    plan_columns: list[tuple[str, int]],
) -> tuple[bool, list[dict[str, Any]]]:
    from odoo.tools import SQL

    model = _model(env, "budget.report", company_id)
    domain = _base_domain(
        company_id,
        parameters,
        date_from=date_from,
        date_to=date_to,
        plan_column=plan_column,
    )
    after = parameters["after"]
    if after is not None:
        cursor_query = model._search(domain, limit=1)
        cursor_expressions = _position_expressions(model, cursor_query)
        cursor_query.add_where(
            _position_clause(cursor_expressions, _position_values(after), "=")
        )
        if not env.execute_query(cursor_query.select(SQL("1"))):
            return False, []

    query = model._search(domain, limit=parameters["limit"])
    position_expressions = _position_expressions(model, query)
    if after is not None:
        query.add_where(
            _position_clause(position_expressions, _position_values(after), ">")
        )
    query.order = SQL(", ").join(position_expressions)
    field_names = (*_QUERY_FIELDS, *(name for name, _ in plan_columns))
    expressions = _field_expressions(model, query, field_names)
    rows = env.execute_query(query.select(*expressions))
    return True, [dict(zip(field_names, row, strict=True)) for row in rows]


def _related_records(
    env: Any,
    company_id: int,
    rows: list[dict[str, Any]],
    *,
    budget_id: int,
    plan_columns: list[tuple[str, int]],
) -> tuple[dict[int, Any], dict[int, Any], dict[int, Any]]:
    line_ids = {_record_id(row["budget_line_id"]) for row in rows}
    lines = _model(env, "budget.line", company_id).search(
        [
            ("id", "in", sorted(line_ids)),
            ("budget_analytic_id", "=", budget_id),
            ("company_id", "in", [False, company_id]),
        ]
    )
    line_by_id = {line.id: line for line in lines}
    if set(line_by_id) != line_ids:
        raise ValueError("inaccessible budget line")

    user_ids = {
        _record_id(row["user_id"])
        for row in rows
        if row["user_id"] not in (None, False)
    }
    users = _model(env, "res.users", company_id).search(
        [("id", "in", sorted(user_ids))]
    )
    user_by_id = {user.id: user for user in users}
    if set(user_by_id) != user_ids:
        raise ValueError("inaccessible report user")

    account_ids = {
        _record_id(row[column])
        for row in rows
        for column, _root_id in plan_columns
        if row[column] not in (None, False)
    }
    accounts = _model(env, "account.analytic.account", company_id).search(
        [
            ("id", "in", sorted(account_ids)),
            ("company_id", "in", [False, company_id]),
        ]
    )
    account_by_id = {account.id: account for account in accounts}
    if set(account_by_id) != account_ids:
        raise ValueError("inaccessible analytic account")
    return line_by_id, user_by_id, account_by_id


def _items(
    env: Any,
    company_id: int,
    rows: list[dict[str, Any]],
    *,
    budget: Any,
    plan_columns: list[tuple[str, int]],
) -> list[dict[str, Any]]:
    _line_by_id, user_by_id, account_by_id = _related_records(
        env,
        company_id,
        rows,
        budget_id=budget.id,
        plan_columns=plan_columns,
    )
    result = []
    for row in rows:
        row_key = _text(row["id"])
        line_type = _text(row["line_type"])
        source_model = _text(row["res_model"])
        source_id = _record_id(row["res_id"])
        budget_line_id = _record_id(row["budget_line_id"])
        row_company_id = _company_id(row["company_id"])
        if (
            not _ROW_KEY.fullmatch(row_key)
            or line_type not in _LINE_TYPES
            or source_model not in _SOURCE_MODELS
            or _record_id(row["budget_analytic_id"]) != budget.id
            or row_company_id not in {None, company_id}
        ):
            raise ValueError("out-of-scope budget report row")

        plan_accounts = []
        for column, root_plan_id in plan_columns:
            raw_account_id = row[column]
            if raw_account_id in (None, False):
                continue
            account = account_by_id[_record_id(raw_account_id)]
            if _record_id(account.root_plan_id) != root_plan_id:
                raise ValueError("analytic account is in the wrong plan column")
            plan_accounts.append(
                {
                    "plan": {
                        "id": _record_id(account.plan_id),
                        "name": _text(account.plan_id.name),
                    },
                    "account": {
                        "id": account.id,
                        "name": _text(account.name),
                    },
                }
            )
        plan_accounts.sort(
            key=lambda value: (value["plan"]["id"], value["account"]["id"])
        )
        if len({item["plan"]["id"] for item in plan_accounts}) != len(plan_accounts):
            raise ValueError("duplicate analytic plan in report row")

        user_id = _company_id(row["user_id"])
        user = user_by_id.get(user_id) if user_id is not None else None
        result.append(
            {
                "row_key": row_key,
                "line_type": line_type,
                "date": _date_text(row["date"]),
                "budget": {"id": budget.id, "name": _text(budget.name)},
                "budget_line": {"id": budget_line_id},
                "source": {"model": source_model, "id": source_id},
                "description": _optional_text(row["description"]),
                "plan_accounts": plan_accounts,
                "company_id": row_company_id,
                "user": (
                    None if user is None else {"id": user.id, "name": _text(user.name)}
                ),
                "budget_amount": _decimal_text(row["budget"]),
                "achieved_amount": _decimal_text(row["achieved"]),
                "theoretical_amount": _decimal_text(row["theoretical"]),
            }
        )
    return result


def dispatch(
    env: Any,
    payload: dict[str, Any],
    company_id: int,
    *,
    failure_type: Any,
) -> dict[str, Any]:
    """Validate, ACL-gate, and execute the fixed official budget report read."""

    try:
        parameters = _validated_payload(payload, company_id, failure_type)
        page = _scope_page(env, company_id, failure_type)
        if not page["access_allowed"]:
            return page
        budget, date_from, date_to, plan_column = _effective_filters(
            env, company_id, parameters, failure_type
        )
        plan_columns = _plan_columns(env)
        cursor_found, rows = _query_rows(
            env,
            company_id,
            parameters,
            date_from=date_from,
            date_to=date_to,
            plan_column=plan_column,
            plan_columns=plan_columns,
        )
        items = (
            _items(
                env,
                company_id,
                rows,
                budget=budget,
                plan_columns=plan_columns,
            )
            if cursor_found
            else []
        )
        return {**page, "cursor_found": cursor_found, "items": items}
    except failure_type:
        raise
    except Exception as exc:
        raise _runtime_failure(failure_type) from exc
