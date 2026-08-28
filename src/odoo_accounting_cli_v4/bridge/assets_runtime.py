"""Odoo-side runtime for the three fixed-asset reads."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

ACTION = "accounting.asset.read"
CAPABILITY_IDS = frozenset(
    {"asset.search", "asset.get", "asset.depreciation_schedule.get"}
)
ASSET_STATES = frozenset({"draft", "open", "paused", "close", "cancelled"})

_MODELS = (
    "account.asset",
    "account.move",
    "account.move.line",
    "account.account",
    "account.journal",
    "res.company",
    "res.currency",
)
_REQUIRED_FIELDS = {
    "account.asset": {
        "name",
        "state",
        "active",
        "company_id",
        "currency_id",
        "acquisition_date",
        "prorata_date",
        "disposal_date",
        "account_asset_id",
        "account_depreciation_id",
        "account_depreciation_expense_id",
        "journal_id",
        "original_value",
        "salvage_value",
        "total_depreciable_value",
        "book_value",
        "value_residual",
        "method",
        "method_number",
        "method_period",
        "method_progress_factor",
        "prorata_computation_type",
        "depreciation_move_ids",
    },
    "account.move": {
        "name",
        "date",
        "state",
        "auto_post",
        "company_id",
        "journal_id",
        "asset_id",
        "depreciation_value",
        "asset_depreciated_value",
        "asset_remaining_value",
        "line_ids",
    },
    "account.account": {"code", "name"},
    "account.journal": {"code", "name", "company_id"},
    "res.currency": {"name"},
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


def _valid_parameters(capability_id: str, parameters: Any) -> bool:
    if not isinstance(parameters, dict):
        return False
    if capability_id != "asset.search":
        return set(parameters) == {"asset_id"} and _positive_id(parameters["asset_id"])
    if set(parameters) != {"query", "states", "after", "limit"}:
        return False
    query = parameters["query"]
    states = parameters["states"]
    after = parameters["after"]
    limit = parameters["limit"]
    return (
        (
            query is None
            or isinstance(query, str)
            and bool(query)
            and query == query.strip()
            and len(query) <= 200
        )
        and isinstance(states, list)
        and bool(states)
        and all(isinstance(state, str) for state in states)
        and states == sorted(set(states))
        and set(states) <= ASSET_STATES
        and (after is None or _positive_id(after))
        and _integer(limit)
        and 1 <= limit <= 1001
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


def _field_shape_available(env: Any) -> bool:
    for model_name, names in _REQUIRED_FIELDS.items():
        fields = getattr(env[model_name], "_fields", {})
        if not names <= set(fields):
            return False
    return True


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
    if value in (False, None, "/"):
        return None
    return _text(value)


def _date_text(value: Any) -> str:
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        return date.fromisoformat(value).isoformat()
    raise ValueError("invalid date")


def _optional_date(value: Any) -> str | None:
    return None if value in (False, None) else _date_text(value)


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


def _company_id(record: Any) -> int | None:
    company = getattr(record, "company_id", None)
    record_id = getattr(company, "id", None)
    return record_id if _positive_id(record_id) else None


def _company_matches(record: Any, company_id: int) -> bool:
    return _company_id(record) == company_id


def _account_company_matches(record: Any, company_id: int) -> bool:
    company_ids = getattr(record, "company_ids", None)
    ids = getattr(company_ids, "ids", None)
    if isinstance(ids, list):
        return company_id in ids
    return _company_matches(record, company_id)


def _currency(record: Any) -> dict[str, Any]:
    code = _text(record.name)
    if len(code) > 3:
        raise ValueError("invalid currency")
    return {"id": _record_id(record), "code": code}


def _account(record: Any, company_id: int) -> dict[str, Any] | None:
    if not record:
        return None
    if not _account_company_matches(record, company_id):
        raise ValueError("cross-company account")
    return {
        "id": _record_id(record),
        "code": _text(record.code),
        "name": _text(record.name),
    }


def _journal(record: Any, company_id: int) -> dict[str, Any] | None:
    if not record:
        return None
    if not _company_matches(record, company_id):
        raise ValueError("cross-company journal")
    return {
        "id": _record_id(record),
        "code": _text(record.code),
        "name": _text(record.name),
    }


def _summary(asset: Any, company_id: int) -> dict[str, Any]:
    if not _company_matches(asset, company_id) or asset.state not in ASSET_STATES:
        raise ValueError("out-of-scope asset")
    return {
        "id": _record_id(asset),
        "name": _text(asset.name),
        "state": asset.state,
        "company_id": company_id,
        "currency": _currency(asset.currency_id),
        "acquisition_date": _date_text(asset.acquisition_date),
        "original_value": _decimal_text(asset.original_value),
        "book_value": _decimal_text(asset.book_value),
    }


def _detail(asset: Any, company_id: int) -> dict[str, Any]:
    summary = _summary(asset, company_id)
    if not _integer(asset.method_number) or asset.method_number < 0:
        raise ValueError("invalid depreciation duration")
    return {
        "id": summary["id"],
        "name": summary["name"],
        "state": summary["state"],
        "active": bool(asset.active),
        "company_id": company_id,
        "currency": summary["currency"],
        "accounts": {
            "asset": _account(asset.account_asset_id, company_id),
            "depreciation": _account(asset.account_depreciation_id, company_id),
            "expense": _account(asset.account_depreciation_expense_id, company_id),
        },
        "journal": _journal(asset.journal_id, company_id),
        "values": {
            "original": _decimal_text(asset.original_value),
            "salvage": _decimal_text(asset.salvage_value),
            "depreciable": _decimal_text(asset.total_depreciable_value),
            "book": _decimal_text(asset.book_value),
            "residual": _decimal_text(asset.value_residual),
        },
        "method": {
            "type": _text(asset.method),
            "number": asset.method_number,
            "period": _text(asset.method_period),
            "progress_factor": _decimal_text(asset.method_progress_factor),
            "prorata_computation_type": _text(asset.prorata_computation_type),
        },
        "dates": {
            "acquisition": _date_text(asset.acquisition_date),
            "prorata": _date_text(asset.prorata_date),
            "disposal": _optional_date(asset.disposal_date),
        },
    }


def _schedule(asset: Any, company_id: int) -> dict[str, Any]:
    moves = []
    for move in sorted(
        asset.depreciation_move_ids, key=lambda value: (value.date, value.id)
    ):
        if (
            not _company_matches(move, company_id)
            or _record_id(move.asset_id) != asset.id
        ):
            raise ValueError("out-of-scope depreciation move")
        journal = _journal(move.journal_id, company_id)
        if journal is None:
            raise ValueError("depreciation move has no journal")
        line_ids = sorted(set(move.line_ids.ids))
        if any(not _positive_id(line_id) for line_id in line_ids):
            raise ValueError("invalid depreciation line")
        moves.append(
            {
                "id": _record_id(move),
                "name": _optional_text(move.name),
                "date": _date_text(move.date),
                "state": _text(move.state),
                "auto_post": _text(move.auto_post),
                "journal": journal,
                "depreciation_value": _decimal_text(move.depreciation_value),
                "cumulative_depreciation": _decimal_text(move.asset_depreciated_value),
                "remaining_value": _decimal_text(move.asset_remaining_value),
                "line_ids": line_ids,
            }
        )
    return {"asset": _summary(asset, company_id), "moves": moves}


def _base_domain(company_id: int, parameters: dict[str, Any]) -> list[Any]:
    domain: list[Any] = [
        ("company_id", "=", company_id),
        ("state", "in", parameters["states"]),
    ]
    if parameters["query"] is not None:
        domain.append(("name", "ilike", parameters["query"]))
    return domain


def _search_items(
    env: Any, company_id: int, parameters: dict[str, Any]
) -> tuple[bool, list[dict[str, Any]]]:
    model = _model(env, "account.asset", company_id)
    domain = _base_domain(company_id, parameters)
    after = parameters["after"]
    cursor_found = True
    if after is not None:
        cursor_found = bool(model.search_count([*domain, ("id", "=", after)], limit=1))
        if not cursor_found:
            return False, []
        domain.append(("id", "<", after))
    records = model.search(domain, order="id desc", limit=parameters["limit"])
    return True, [_summary(asset, company_id) for asset in records]


def _one_asset(env: Any, company_id: int, asset_id: int) -> Any | None:
    records = _model(env, "account.asset", company_id).search(
        [
            ("id", "=", asset_id),
            ("company_id", "=", company_id),
            ("state", "in", sorted(ASSET_STATES)),
        ],
        limit=2,
    )
    if len(records) > 1:
        raise ValueError("ambiguous asset")
    return records[0] if records else None


def dispatch(
    env: Any,
    payload: dict[str, Any],
    company_id: int,
    *,
    failure_type: Any,
) -> dict[str, Any]:
    """Validate, gate, and execute one fixed-asset read."""

    try:
        capability_id, parameters = _validated_payload(
            payload, company_id, failure_type
        )
        page = _scope_page(env, company_id, failure_type)
        if not page["access_allowed"]:
            return page
        if capability_id == "asset.search":
            cursor_found, items = _search_items(env, company_id, parameters)
        else:
            cursor_found = True
            asset = _one_asset(env, company_id, parameters["asset_id"])
            if asset is None:
                items = []
            elif capability_id == "asset.get":
                items = [_detail(asset, company_id)]
            else:
                items = [_schedule(asset, company_id)]
        return {**page, "cursor_found": cursor_found, "items": items}
    except failure_type:
        raise
    except Exception as exc:
        raise _runtime_failure(failure_type) from exc
