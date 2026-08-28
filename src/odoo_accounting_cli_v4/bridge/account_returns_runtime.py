"""Odoo-side runtime for six fixed accounting-return reads."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

ACTION = "accounting.account_return.read"
CAPABILITY_IDS = frozenset(
    {
        "account.return.search",
        "account.return.get",
        "account.return.summary",
        "account.return.type.list",
        "account.return.check.list",
        "account.return.check.get",
    }
)
RETURN_STATES = frozenset({"new", "reviewed", "submitted", "paid"})
RETURN_CATEGORIES = frozenset({"account_return", "audit"})
CHECK_TYPES = frozenset({"check", "file"})
CHECK_RESULTS = frozenset({"todo", "reviewed", "supervised", "anomaly"})
WORKFLOWS = frozenset(
    {
        "generic_state_review",
        "generic_state_review_submit",
        "generic_state_tax_report",
        "generic_state_only_pay",
    }
)
PERIODICITIES = frozenset(
    {"monthly", "2_months", "trimester", "4_months", "semester", "year"}
)
_RETURN_OUTPUT_FIELDS = [
    "name",
    "active",
    "date_from",
    "date_to",
    "date_deadline",
    "date_submission",
    "date_lock",
    "type_id",
    "state",
    "next_state",
    "is_completed",
    "company_id",
    "tax_unit_id",
    "manually_created",
    "check_count",
    "unresolved_check_count",
    "resolved_check_count",
]
_TYPE_OUTPUT_FIELDS = [
    "name",
    "category",
    "report_id",
    "country_id",
    "auto_generate",
    "states_workflow",
    "deadline_periodicity",
    "deadline_start_date",
    "deadline_days_delay",
]
_CHECK_OUTPUT_FIELDS = [
    "return_id",
    "code",
    "type",
    "name",
    "message",
    "state",
    "result",
    "records_count",
]
_RETURN_FIELDS = set(_RETURN_OUTPUT_FIELDS) | {"check_ids"}
_TYPE_FIELDS = set(_TYPE_OUTPUT_FIELDS)
_CHECK_FIELDS = set(_CHECK_OUTPUT_FIELDS)


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


def _valid_limit_after(parameters: dict[str, Any]) -> bool:
    return bool(
        (parameters["after"] is None or _positive_id(parameters["after"]))
        and _integer(parameters["limit"])
        and 1 <= parameters["limit"] <= 1001
    )


def _valid_parameters(capability_id: str, parameters: Any) -> bool:
    if not isinstance(parameters, dict):
        return False
    if capability_id == "account.return.get":
        return set(parameters) == {"return_id"} and _positive_id(
            parameters["return_id"]
        )
    if capability_id == "account.return.summary":
        return set(parameters) == {"as_of"} and _canonical_date(parameters["as_of"])
    if capability_id == "account.return.check.get":
        return set(parameters) == {"check_id"} and _positive_id(parameters["check_id"])
    if capability_id == "account.return.search":
        if set(parameters) != {
            "type_id",
            "state",
            "completed",
            "deadline_from",
            "deadline_to",
            "active",
            "after",
            "limit",
        }:
            return False
        return bool(
            (parameters["type_id"] is None or _positive_id(parameters["type_id"]))
            and (parameters["state"] is None or parameters["state"] in RETURN_STATES)
            and (
                parameters["completed"] is None
                or isinstance(parameters["completed"], bool)
            )
            and (
                parameters["deadline_from"] is None
                or _canonical_date(parameters["deadline_from"])
            )
            and (
                parameters["deadline_to"] is None
                or _canonical_date(parameters["deadline_to"])
            )
            and (
                parameters["deadline_from"] is None
                or parameters["deadline_to"] is None
                or parameters["deadline_from"] <= parameters["deadline_to"]
            )
            and (parameters["active"] is None or isinstance(parameters["active"], bool))
            and _valid_limit_after(parameters)
        )
    if capability_id == "account.return.type.list":
        return bool(
            set(parameters) == {"category", "after", "limit"}
            and (
                parameters["category"] is None
                or parameters["category"] in RETURN_CATEGORIES
            )
            and _valid_limit_after(parameters)
        )
    return bool(
        set(parameters) == {"return_id", "result", "type", "after", "limit"}
        and _positive_id(parameters["return_id"])
        and (parameters["result"] is None or parameters["result"] in CHECK_RESULTS)
        and (parameters["type"] is None or parameters["type"] in CHECK_TYPES)
        and _valid_limit_after(parameters)
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


def _models(capability_id: str) -> tuple[str, ...]:
    if capability_id == "account.return.summary":
        return ("res.company", "account.return")
    if capability_id == "account.return.type.list":
        return (
            "res.company",
            "account.return.type",
            "account.report",
            "res.country",
        )
    if capability_id.startswith("account.return.check"):
        return (
            "res.company",
            "account.return",
            "account.return.check",
        )
    return (
        "res.company",
        "account.return",
        "account.return.type",
        "account.return.check",
        "account.tax.unit",
    )


def _required_fields(capability_id: str) -> dict[str, set[str]]:
    if capability_id == "account.return.summary":
        return {
            "account.return": {"active", "is_completed", "date_deadline", "company_id"}
        }
    if capability_id == "account.return.type.list":
        return {"account.return.type": _TYPE_FIELDS}
    if capability_id.startswith("account.return.check"):
        return {
            "account.return": {"name", "company_id", "check_ids"},
            "account.return.check": _CHECK_FIELDS,
        }
    return {
        "account.return": _RETURN_FIELDS,
        "account.return.type": {"name", "category"},
    }


def _field_shape_available(env: Any, capability_id: str) -> bool:
    return all(
        fields <= set(getattr(env[model], "_fields", {}))
        for model, fields in _required_fields(capability_id).items()
    )


def _scope_page(
    env: Any, capability_id: str, company_id: int, failure_type: Any
) -> dict[str, Any]:
    company_visible = bool(
        env["res.company"].search_count([("id", "=", company_id)], limit=1)
    )
    models = _models(capability_id)
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
    model = env[name]
    if name == "account.return.type":
        model = model.with_company(company_id)
    return model.with_context(allowed_company_ids=[company_id], active_test=False)


def _text(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("invalid text")
    return value


def _reference(value: Any, *, required: bool = True) -> dict[str, Any] | None:
    if value in (None, False):
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


def _nonnegative(value: Any) -> int:
    if not _integer(value) or value < 0:
        raise ValueError("invalid count")
    return value


def _type_map(
    env: Any, company_id: int, rows: list[dict[str, Any]]
) -> dict[int, dict[str, Any]]:
    type_ids = sorted({_reference(row["type_id"])["id"] for row in rows})
    if not type_ids:
        return {}
    type_rows = _model(env, "account.return.type", company_id).search_read(
        [("id", "in", type_ids)],
        ["name", "category"],
        order="id asc",
        limit=len(type_ids) + 1,
    )
    result: dict[int, dict[str, Any]] = {}
    for row in type_rows:
        type_id = row.get("id")
        category = row.get("category")
        if (
            not _positive_id(type_id)
            or type_id not in type_ids
            or type_id in result
            or category not in RETURN_CATEGORIES
        ):
            raise ValueError("invalid return type")
        result[type_id] = {
            "id": type_id,
            "name": _text(row.get("name")),
            "category": category,
        }
    if set(result) != set(type_ids):
        raise ValueError("missing return type")
    return result


def _return_item(
    row: dict[str, Any], company_id: int, types: dict[int, dict[str, Any]]
) -> dict[str, Any]:
    return_id = row.get("id")
    company = _reference(row.get("company_id"))
    return_type = _reference(row.get("type_id"))
    if (
        not _positive_id(return_id)
        or company is None
        or company["id"] != company_id
        or return_type is None
        or return_type["id"] not in types
        or row.get("state") not in RETURN_STATES
        or row.get("next_state") not in {*RETURN_STATES, False, None}
        or not isinstance(row.get("active"), bool)
        or not isinstance(row.get("is_completed"), bool)
        or not isinstance(row.get("manually_created"), bool)
    ):
        raise ValueError("invalid accounting return")
    counts = {
        "total": _nonnegative(row.get("check_count")),
        "unresolved": _nonnegative(row.get("unresolved_check_count")),
        "resolved": _nonnegative(row.get("resolved_check_count")),
    }
    if counts["total"] != counts["unresolved"] + counts["resolved"]:
        raise ValueError("inconsistent check counts")
    tax_unit = _reference(row.get("tax_unit_id"), required=False)
    return {
        "id": return_id,
        "name": _text(row.get("name")),
        "active": row["active"],
        "date_from": _date_text(row.get("date_from")),
        "date_to": _date_text(row.get("date_to")),
        "date_deadline": _date_text(row.get("date_deadline")),
        "date_submission": _optional_date(row.get("date_submission")),
        "date_lock": _optional_date(row.get("date_lock")),
        "type": types[return_type["id"]],
        "state": row["state"],
        "next_state": row["next_state"] or None,
        "is_completed": row["is_completed"],
        "company_id": company_id,
        "tax_unit_id": None if tax_unit is None else tax_unit["id"],
        "manually_created": row["manually_created"],
        "check_counts": counts,
    }


def _return_domain(company_id: int, parameters: dict[str, Any]) -> list[Any]:
    domain: list[Any] = [("company_id", "=", company_id)]
    mapping = (
        ("type_id", "type_id"),
        ("state", "state"),
        ("completed", "is_completed"),
        ("active", "active"),
    )
    for parameter, field in mapping:
        if parameters[parameter] is not None:
            domain.append((field, "=", parameters[parameter]))
    if parameters["deadline_from"] is not None:
        domain.append(("date_deadline", ">=", parameters["deadline_from"]))
    if parameters["deadline_to"] is not None:
        domain.append(("date_deadline", "<=", parameters["deadline_to"]))
    return domain


def _search_returns(
    env: Any, company_id: int, parameters: dict[str, Any]
) -> tuple[bool, list[dict[str, Any]]]:
    model = _model(env, "account.return", company_id)
    domain = _return_domain(company_id, parameters)
    after = parameters["after"]
    if after is not None:
        if not model.search_count([*domain, ("id", "=", after)], limit=1):
            return False, []
        domain.append(("id", "<", after))
    rows = model.search_read(
        domain,
        _RETURN_OUTPUT_FIELDS,
        order="id desc",
        limit=parameters["limit"],
    )
    types = _type_map(env, company_id, rows)
    return True, [_return_item(row, company_id, types) for row in rows]


def _get_return(env: Any, company_id: int, return_id: int) -> list[dict[str, Any]]:
    rows = _model(env, "account.return", company_id).search_read(
        [("company_id", "=", company_id), ("id", "=", return_id)],
        _RETURN_OUTPUT_FIELDS,
        order="id desc",
        limit=2,
    )
    types = _type_map(env, company_id, rows)
    return [_return_item(row, company_id, types) for row in rows]


def _summary(env: Any, company_id: int, parameters: dict[str, Any]) -> dict[str, Any]:
    model = _model(env, "account.return", company_id)
    as_of = parameters["as_of"]
    upper = (date.fromisoformat(as_of) + timedelta(days=30)).isoformat()
    base = [("company_id", "=", company_id), ("active", "=", True)]

    def count(*terms: tuple[str, str, Any]) -> int:
        return _nonnegative(model.search_count([*base, *terms]))

    counts = {
        "total": count(),
        "open": count(("is_completed", "=", False)),
        "completed": count(("is_completed", "=", True)),
        "overdue": count(("is_completed", "=", False), ("date_deadline", "<", as_of)),
        "due_today": count(("is_completed", "=", False), ("date_deadline", "=", as_of)),
        "due_next_30_days": count(
            ("is_completed", "=", False),
            ("date_deadline", ">", as_of),
            ("date_deadline", "<=", upper),
        ),
        "later": count(("is_completed", "=", False), ("date_deadline", ">", upper)),
    }
    if counts["total"] != counts["open"] + counts["completed"] or counts["open"] != sum(
        counts[key] for key in ("overdue", "due_today", "due_next_30_days", "later")
    ):
        raise ValueError("inconsistent return counts")
    return {"company_id": company_id, "as_of": as_of, "counts": counts}


def _type_item(row: dict[str, Any], company_id: int) -> dict[str, Any]:
    type_id = row.get("id")
    category = row.get("category")
    workflow = row.get("states_workflow")
    periodicity = row.get("deadline_periodicity") or None
    if (
        not _positive_id(type_id)
        or category not in RETURN_CATEGORIES
        or workflow not in WORKFLOWS
        or periodicity not in {*PERIODICITIES, None}
        or not isinstance(row.get("auto_generate"), bool)
        or not _integer(row.get("deadline_days_delay"))
    ):
        raise ValueError("invalid return type")
    return {
        "id": type_id,
        "name": _text(row.get("name")),
        "company_id": company_id,
        "category": category,
        "report": _reference(row.get("report_id"), required=False),
        "country": _reference(row.get("country_id"), required=False),
        "auto_generate": row["auto_generate"],
        "states_workflow": workflow,
        "deadline_periodicity": periodicity,
        "deadline_start_date": _optional_date(row.get("deadline_start_date")),
        "deadline_days_delay": row["deadline_days_delay"],
    }


def _list_types(
    env: Any, company_id: int, parameters: dict[str, Any]
) -> tuple[bool, list[dict[str, Any]]]:
    model = _model(env, "account.return.type", company_id)
    domain: list[Any] = []
    if parameters["category"] is not None:
        domain.append(("category", "=", parameters["category"]))
    after = parameters["after"]
    if after is not None:
        if not model.search_count([*domain, ("id", "=", after)], limit=1):
            return False, []
        domain.append(("id", "<", after))
    rows = model.search_read(
        domain,
        _TYPE_OUTPUT_FIELDS,
        order="id desc",
        limit=parameters["limit"],
    )
    return True, [_type_item(row, company_id) for row in rows]


def _visible_return(
    env: Any, company_id: int, domain: list[Any]
) -> dict[str, Any] | None:
    rows = _model(env, "account.return", company_id).search_read(
        [("company_id", "=", company_id), *domain],
        ["name"],
        order="id desc",
        limit=2,
    )
    if len(rows) > 1:
        raise ValueError("ambiguous visible return")
    if not rows:
        return None
    return {"id": rows[0]["id"], "name": _text(rows[0].get("name"))}


def _check_item(row: dict[str, Any], visible_return: dict[str, Any]) -> dict[str, Any]:
    check_id = row.get("id")
    return_ref = _reference(row.get("return_id"))
    check_type = row.get("type")
    state = row.get("state")
    result = row.get("result")
    message = row.get("message")
    if (
        not _positive_id(check_id)
        or return_ref is None
        or return_ref["id"] != visible_return["id"]
        or check_type not in CHECK_TYPES
        or state not in RETURN_STATES
        or result not in CHECK_RESULTS
        or (message not in (None, False) and not isinstance(message, str))
    ):
        raise ValueError("invalid return check")
    return {
        "id": check_id,
        "return": visible_return,
        "code": _text(row.get("code")),
        "type": check_type,
        "name": _text(row.get("name")),
        "message": None if message in (None, False) else message,
        "state": state,
        "result": result,
        "records_count": _nonnegative(row.get("records_count")),
    }


def _list_checks(
    env: Any, company_id: int, parameters: dict[str, Any]
) -> tuple[bool, list[dict[str, Any]]]:
    visible_return = _visible_return(
        env, company_id, [("id", "=", parameters["return_id"])]
    )
    if visible_return is None:
        return parameters["after"] is None, []
    model = _model(env, "account.return.check", company_id)
    domain: list[Any] = [("return_id", "=", visible_return["id"])]
    if parameters["result"] is not None:
        domain.append(("result", "=", parameters["result"]))
    if parameters["type"] is not None:
        domain.append(("type", "=", parameters["type"]))
    after = parameters["after"]
    if after is not None:
        if not model.search_count([*domain, ("id", "=", after)], limit=1):
            return False, []
        domain.append(("id", "<", after))
    rows = model.search_read(
        domain,
        _CHECK_OUTPUT_FIELDS,
        order="id desc",
        limit=parameters["limit"],
    )
    return True, [_check_item(row, visible_return) for row in rows]


def _get_check(env: Any, company_id: int, check_id: int) -> list[dict[str, Any]]:
    visible_return = _visible_return(env, company_id, [("check_ids", "in", [check_id])])
    if visible_return is None:
        return []
    rows = _model(env, "account.return.check", company_id).search_read(
        [("id", "=", check_id), ("return_id", "=", visible_return["id"])],
        _CHECK_OUTPUT_FIELDS,
        order="id desc",
        limit=2,
    )
    return [_check_item(row, visible_return) for row in rows]


def dispatch(
    env: Any,
    payload: dict[str, Any],
    company_id: int,
    *,
    failure_type: Any,
) -> dict[str, Any]:
    """Validate, gate, and execute one allowlisted accounting-return read."""

    try:
        capability_id, parameters = _validated_payload(
            payload, company_id, failure_type
        )
        page = _scope_page(env, capability_id, company_id, failure_type)
        if not page["access_allowed"]:
            return page
        cursor_found = True
        if capability_id == "account.return.search":
            cursor_found, items = _search_returns(env, company_id, parameters)
        elif capability_id == "account.return.get":
            items = _get_return(env, company_id, parameters["return_id"])
        elif capability_id == "account.return.summary":
            items = [_summary(env, company_id, parameters)]
        elif capability_id == "account.return.type.list":
            cursor_found, items = _list_types(env, company_id, parameters)
        elif capability_id == "account.return.check.list":
            cursor_found, items = _list_checks(env, company_id, parameters)
        else:
            items = _get_check(env, company_id, parameters["check_id"])
        return {**page, "cursor_found": cursor_found, "items": items}
    except failure_type:
        raise
    except Exception as exc:
        raise _runtime_failure(failure_type) from exc
