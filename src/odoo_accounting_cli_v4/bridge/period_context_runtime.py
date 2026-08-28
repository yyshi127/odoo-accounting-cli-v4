"""Odoo-side runtime for period-context reads."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

ACTION = "accounting.period_context.read"
CAPABILITY_IDS = frozenset(
    {
        "company.lock_dates.inspect",
        "company.fiscal_year.resolve",
        "fiscal_year.search",
        "fiscal_year.get",
    }
)
_COMPANY_CAPABILITIES = frozenset({"company.lock_dates.inspect"})
_LOCK_FIELDS = {
    "fiscalyear_lock_date": "user_fiscalyear_lock_date",
    "tax_lock_date": "user_tax_lock_date",
    "sale_lock_date": "user_sale_lock_date",
    "purchase_lock_date": "user_purchase_lock_date",
    "hard_lock_date": "user_hard_lock_date",
}
_FISCAL_YEAR_FIELDS = {"name", "company_id", "date_from", "date_to"}


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
    if capability_id == "company.lock_dates.inspect":
        return not parameters
    if capability_id == "company.fiscal_year.resolve":
        return set(parameters) == {"date"} and _canonical_date(parameters["date"])
    if capability_id == "fiscal_year.get":
        return set(parameters) == {"fiscal_year_id"} and _positive_id(
            parameters["fiscal_year_id"]
        )
    if set(parameters) != {
        "contains_date",
        "date_from",
        "date_to",
        "after",
        "limit",
    }:
        return False
    dates = [
        parameters["contains_date"],
        parameters["date_from"],
        parameters["date_to"],
    ]
    after = parameters["after"]
    return (
        all(value is None or _canonical_date(value) for value in dates)
        and (
            parameters["date_from"] is None
            or parameters["date_to"] is None
            or parameters["date_from"] <= parameters["date_to"]
        )
        and (
            after is None
            or isinstance(after, list)
            and len(after) == 2
            and _canonical_date(after[0])
            and _positive_id(after[1])
        )
        and _integer(parameters["limit"])
        and 1 <= parameters["limit"] <= 1001
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


def _required_models(capability_id: str) -> tuple[str, ...]:
    if capability_id in _COMPANY_CAPABILITIES:
        return ("res.company",)
    return ("res.company", "account.fiscal.year")


def _field_shape_available(env: Any, capability_id: str) -> bool:
    if capability_id == "company.lock_dates.inspect":
        fields = set(getattr(env["res.company"], "_fields", {}))
        return set(_LOCK_FIELDS) | set(_LOCK_FIELDS.values()) <= fields
    if capability_id not in _COMPANY_CAPABILITIES:
        fields = set(getattr(env["account.fiscal.year"], "_fields", {}))
        return _FISCAL_YEAR_FIELDS <= fields
    return True


def _scope_page(
    env: Any, capability_id: str, company_id: int, failure_type: Any
) -> dict[str, Any]:
    company_visible = bool(
        env["res.company"].search_count([("id", "=", company_id)], limit=1)
    )
    models = _required_models(capability_id)
    module_installed = all(env.registry.get(name) is not None for name in models)
    if company_visible and module_installed and not _field_shape_available(
        env, capability_id
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


def _company_id(record: Any) -> int:
    return _record_id(record.company_id)


def _text(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("invalid text")
    return value


def _one_company(env: Any, company_id: int) -> Any:
    companies = _model(env, "res.company", company_id).search(
        [("id", "=", company_id)], limit=2
    )
    if len(companies) != 1:
        raise ValueError("company disappeared")
    return companies[0]


def _lock_date(value: Any) -> str | None:
    if value in (False, None):
        return None
    rendered = _date_text(value)
    return None if rendered == date.min.isoformat() else rendered


def _lock_result(company: Any, company_id: int) -> dict[str, Any]:
    if _record_id(company) != company_id:
        raise ValueError("cross-company result")
    return {
        "company_id": company_id,
        "configured": {
            public: _lock_date(getattr(company, public))
            for public in _LOCK_FIELDS
        },
        "effective": {
            public: _lock_date(getattr(company, effective))
            for public, effective in _LOCK_FIELDS.items()
        },
    }


def _fiscal_year(record: Any, company_id: int) -> dict[str, Any]:
    if _company_id(record) != company_id:
        raise ValueError("cross-company fiscal year")
    date_from = _date_text(record.date_from)
    date_to = _date_text(record.date_to)
    if date_from > date_to:
        raise ValueError("invalid fiscal year")
    return {
        "id": _record_id(record),
        "name": _text(record.name),
        "company_id": company_id,
        "date_from": date_from,
        "date_to": date_to,
    }


def _resolve_result(company: Any, company_id: int, target: str) -> dict[str, Any]:
    if _record_id(company) != company_id:
        raise ValueError("cross-company result")
    method = getattr(company, "compute_fiscalyear_dates", None)
    if not callable(method):
        raise TypeError("fiscal-year resolver unavailable")
    resolved = method(date.fromisoformat(target))
    if (
        not isinstance(resolved, dict)
        or not {"date_from", "date_to"} <= set(resolved)
        or not set(resolved) <= {"date_from", "date_to", "record"}
    ):
        raise ValueError("invalid fiscal-year resolution")
    date_from = _date_text(resolved["date_from"])
    date_to = _date_text(resolved["date_to"])
    if not date_from <= target <= date_to:
        raise ValueError("invalid fiscal-year range")
    record = resolved.get("record")
    fiscal_year = None
    if record:
        item = _fiscal_year(record, company_id)
        if item["date_from"] != date_from or item["date_to"] != date_to:
            raise ValueError("fiscal-year record does not match the resolution")
        fiscal_year = {"id": item["id"], "name": item["name"]}
    return {
        "company_id": company_id,
        "date": target,
        "date_from": date_from,
        "date_to": date_to,
        "fiscal_year": fiscal_year,
    }


def _base_domain(company_id: int, parameters: dict[str, Any]) -> list[Any]:
    domain: list[Any] = [("company_id", "=", company_id)]
    if parameters["contains_date"] is not None:
        domain.extend(
            [
                ("date_from", "<=", parameters["contains_date"]),
                ("date_to", ">=", parameters["contains_date"]),
            ]
        )
    if parameters["date_from"] is not None:
        domain.append(("date_to", ">=", parameters["date_from"]))
    if parameters["date_to"] is not None:
        domain.append(("date_from", "<=", parameters["date_to"]))
    return domain


def _search_items(
    env: Any, company_id: int, parameters: dict[str, Any]
) -> tuple[bool, list[dict[str, Any]]]:
    model = _model(env, "account.fiscal.year", company_id)
    domain = _base_domain(company_id, parameters)
    after = parameters["after"]
    if after is not None:
        anchor = [
            *domain,
            ("id", "=", after[1]),
            ("date_from", "=", after[0]),
        ]
        if not model.search_count(anchor, limit=1):
            return False, []
        domain.extend(
            [
                "|",
                ("date_from", "<", after[0]),
                "&",
                ("date_from", "=", after[0]),
                ("id", "<", after[1]),
            ]
        )
    records = model.search(
        domain, order="date_from desc, id desc", limit=parameters["limit"]
    )
    return True, [_fiscal_year(record, company_id) for record in records]


def _one_fiscal_year(env: Any, company_id: int, fiscal_year_id: int) -> Any | None:
    records = _model(env, "account.fiscal.year", company_id).search(
        [("id", "=", fiscal_year_id), ("company_id", "=", company_id)],
        limit=2,
    )
    if len(records) > 1:
        raise ValueError("ambiguous fiscal year")
    return records[0] if records else None


def dispatch(
    env: Any,
    payload: dict[str, Any],
    company_id: int,
    *,
    failure_type: Any,
) -> dict[str, Any]:
    """Validate, gate, and execute one period-context read."""

    try:
        capability_id, parameters = _validated_payload(
            payload, company_id, failure_type
        )
        page = _scope_page(env, capability_id, company_id, failure_type)
        if not page["access_allowed"]:
            return page
        if capability_id == "company.lock_dates.inspect":
            items = [_lock_result(_one_company(env, company_id), company_id)]
            cursor_found = True
        elif capability_id == "company.fiscal_year.resolve":
            items = [
                _resolve_result(
                    _one_company(env, company_id), company_id, parameters["date"]
                )
            ]
            cursor_found = True
        elif capability_id == "fiscal_year.search":
            cursor_found, items = _search_items(env, company_id, parameters)
        else:
            cursor_found = True
            record = _one_fiscal_year(
                env, company_id, parameters["fiscal_year_id"]
            )
            items = [] if record is None else [_fiscal_year(record, company_id)]
        return {**page, "cursor_found": cursor_found, "items": items}
    except failure_type:
        raise
    except Exception as exc:
        raise _runtime_failure(failure_type) from exc
