"""Odoo-side runtime slice for ``reconciliation.candidates.list``.

This slice stays separate from the monolithic bridge runtime.  The dispatcher
supplies its ``RuntimeFailure`` type through ``failure_type`` so this file can
be audited and tested without a circular import.
"""

from __future__ import annotations

from datetime import date as date_type
from decimal import Decimal
import re
from typing import Any


ACTION = "account.move.line.reconciliation_candidate.read_page"

_REQUIRED_MODELS = (
    "res.company",
    "account.move.line",
    "account.move",
    "account.account",
    "account.journal",
    "res.partner",
    "res.currency",
    "account.reconcile.model",
)
_ACCOUNTANT_SENTINEL = "account.reconcile.wizard"
_STATES = ("draft", "posted")
_ACCOUNT_KINDS = ("receivable", "payable", "other")
_ACCOUNT_TYPES = {
    "asset_receivable",
    "asset_cash",
    "asset_current",
    "asset_non_current",
    "asset_prepayments",
    "asset_fixed",
    "liability_payable",
    "liability_credit_card",
    "liability_current",
    "liability_non_current",
    "equity",
    "equity_unaffected",
    "income",
    "income_other",
    "expense",
    "expense_other",
    "expense_depreciation",
    "expense_direct_cost",
    "off_balance",
}
_MOVE_TYPES = {
    "entry",
    "out_invoice",
    "out_refund",
    "in_invoice",
    "in_refund",
    "out_receipt",
    "in_receipt",
}
_JOURNAL_TYPES = {"sale", "purchase", "cash", "bank", "credit", "general"}
_EXCLUDED_DISPLAY_TYPES = ("line_section", "line_subsection", "line_note")
_ACCOUNT_CODE_PATTERN = re.compile(r"^[A-Za-z0-9.]+$")

_CANDIDATE_FIELDS = (
    "id",
    "date",
    "invoice_date",
    "date_maturity",
    "parent_state",
    "move_id",
    "move_name",
    "ref",
    "name",
    "account_id",
    "partner_id",
    "journal_id",
    "company_id",
    "company_currency_id",
    "currency_id",
    "balance",
    "amount_currency",
    "amount_residual",
    "amount_residual_currency",
    "reconciled",
    "matching_number",
    "reconcile_model_id",
    "display_type",
    "full_reconcile_id",
)
_COMPANY_FIELDS = ("id", "parent_path", "currency_id")
_ACCOUNT_FIELDS = ("id", "code", "name", "account_type", "reconcile")
_MOVE_FIELDS = (
    "id",
    "name",
    "move_type",
    "ref",
    "state",
    "date",
    "invoice_date",
    "company_id",
    "journal_id",
    "company_currency_id",
)
_JOURNAL_FIELDS = ("id", "code", "name", "type", "company_id")
_PARTNER_FIELDS = ("id", "name")
_CURRENCY_FIELDS = ("id", "name")
_RECONCILE_MODEL_FIELDS = ("id", "name", "company_id")


def _failure(failure_type: Any, code: str, message: str, exit_code: int) -> Exception:
    return failure_type(code, message, exit_code=exit_code)


def _runtime_failure(failure_type: Any) -> Exception:
    return _failure(
        failure_type,
        "odoo_runtime_error",
        "The Odoo runtime request failed.",
        7,
    )


def _protocol_failure(failure_type: Any) -> Exception:
    return _failure(
        failure_type,
        "bridge_protocol_error",
        "The bridge action payload is invalid.",
        7,
    )


def _valid_id(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _is_canonical_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return date_type.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _canonical_selection(value: Any, allowed: tuple[str, ...]) -> bool:
    return (
        isinstance(value, list)
        and value
        and value == [choice for choice in allowed if choice in value]
    )


def _payload_is_valid(payload: Any) -> bool:
    if not isinstance(payload, dict) or set(payload) != {
        "company_id",
        "after",
        "limit",
        "filters",
    }:
        return False
    if not _valid_id(payload["company_id"]):
        return False
    after = payload["after"]
    if after is not None and (
        not isinstance(after, list)
        or len(after) != 2
        or not _is_canonical_date(after[0])
        or not _valid_id(after[1])
    ):
        return False
    limit = payload["limit"]
    if not _valid_id(limit) or limit > 1001:
        return False
    filters = payload["filters"]
    if not isinstance(filters, dict) or set(filters) != {
        "date_from",
        "date_to",
        "states",
        "account_id",
        "partner_id",
        "journal_id",
        "account_kinds",
        "query",
    }:
        return False
    for field in ("date_from", "date_to"):
        if filters[field] is not None and not _is_canonical_date(filters[field]):
            return False
    if (
        filters["date_from"] is not None
        and filters["date_to"] is not None
        and filters["date_from"] > filters["date_to"]
    ):
        return False
    if not _canonical_selection(filters["states"], _STATES):
        return False
    if not _canonical_selection(filters["account_kinds"], _ACCOUNT_KINDS):
        return False
    for field in ("account_id", "partner_id", "journal_id"):
        if filters[field] is not None and not _valid_id(filters[field]):
            return False
    query = filters["query"]
    return query is None or (
        isinstance(query, str)
        and query == query.strip()
        and 1 <= len(query) <= 200
    )


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
        "rows": [],
    }


def _gate(env: Any, company_id: int) -> tuple[bool, bool, bool]:
    installed = {
        model: env.registry.get(model) is not None
        for model in (*_REQUIRED_MODELS, _ACCOUNTANT_SENTINEL)
    }
    module_installed = all(installed.values())
    company_visible = installed["res.company"]
    if not module_installed:
        return company_visible, False, False

    read_allowed = {
        model: bool(env[model].has_access("read")) for model in _REQUIRED_MODELS
    }
    company_visible = read_allowed["res.company"]
    access_allowed = all(read_allowed.values())
    if not access_allowed:
        return company_visible, True, False

    company_visible = bool(
        env["res.company"].search_count([("id", "=", company_id)], limit=1)
    )
    return company_visible, True, company_visible


def _scoped_model(env: Any, model: str, company_id: int) -> Any:
    return env[model].with_context(
        active_test=False,
        allowed_company_ids=[company_id],
    )


def _reference_id(value: Any, failure_type: Any, *, optional: bool = False) -> int | None:
    if value is False or value is None:
        if optional:
            return None
        raise _runtime_failure(failure_type)
    if _valid_id(value):
        return value
    if (
        isinstance(value, (list, tuple))
        and len(value) == 2
        and _valid_id(value[0])
    ):
        return value[0]
    raise _runtime_failure(failure_type)


def _optional_text(value: Any, failure_type: Any) -> str | None:
    if value is False or value is None or value == "":
        return None
    if isinstance(value, str):
        return value
    raise _runtime_failure(failure_type)


def _required_text(value: Any, failure_type: Any) -> str:
    if isinstance(value, str) and value:
        return value
    raise _runtime_failure(failure_type)


def _date(value: Any, failure_type: Any) -> str:
    if isinstance(value, date_type):
        return value.isoformat()
    if _is_canonical_date(value):
        return value
    raise _runtime_failure(failure_type)


def _optional_date(value: Any, failure_type: Any) -> str | None:
    if value is False or value is None or value == "":
        return None
    return _date(value, failure_type)


def _decimal(value: Any, failure_type: Any) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise _runtime_failure(failure_type)
    result = value if isinstance(value, Decimal) else Decimal(str(value))
    if not result.is_finite():
        raise _runtime_failure(failure_type)
    return result


def _decimal_text(value: Decimal) -> str:
    if value == 0:
        return "0"
    text = format(value, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def _company_scope(
    env: Any, company_id: int, failure_type: Any
) -> tuple[list[int], int]:
    rows = _scoped_model(env, "res.company", company_id).search_read(
        [("id", "=", company_id)],
        fields=list(_COMPANY_FIELDS),
        limit=1,
        order="id",
    )
    if (
        not isinstance(rows, list)
        or len(rows) != 1
        or not isinstance(rows[0], dict)
        or set(rows[0]) != set(_COMPANY_FIELDS)
        or rows[0].get("id") != company_id
    ):
        raise _runtime_failure(failure_type)
    parent_path = rows[0]["parent_path"]
    if not isinstance(parent_path, str) or not parent_path.endswith("/"):
        raise _runtime_failure(failure_type)
    parts = parent_path[:-1].split("/")
    if (
        not parts
        or any(not part.isdigit() or part.startswith("0") for part in parts)
    ):
        raise _runtime_failure(failure_type)
    scope = [int(part) for part in parts]
    if (
        any(value <= 0 for value in scope)
        or len(scope) != len(set(scope))
        or scope[-1] != company_id
    ):
        raise _runtime_failure(failure_type)
    currency_id = _reference_id(rows[0]["currency_id"], failure_type)
    assert currency_id is not None
    return scope, currency_id


def _account_kind(account_type: str) -> str:
    if account_type == "asset_receivable":
        return "receivable"
    if account_type == "liability_payable":
        return "payable"
    return "other"


def _account_index(
    env: Any,
    company_id: int,
    scope: list[int],
    failure_type: Any,
) -> dict[int, dict[str, Any]]:
    rows = _scoped_model(env, "account.account", company_id).search_read(
        [("company_ids", "in", scope), ("reconcile", "=", True)],
        fields=list(_ACCOUNT_FIELDS),
        order="id",
    )
    if not isinstance(rows, list):
        raise _runtime_failure(failure_type)
    result: dict[int, dict[str, Any]] = {}
    previous = 0
    for row in rows:
        if not isinstance(row, dict) or set(row) != set(_ACCOUNT_FIELDS):
            raise _runtime_failure(failure_type)
        record_id = row.get("id")
        code = _required_text(row.get("code"), failure_type)
        name = _required_text(row.get("name"), failure_type)
        account_type = row.get("account_type")
        if (
            not _valid_id(record_id)
            or record_id <= previous
            or len(code) > 64
            or _ACCOUNT_CODE_PATTERN.fullmatch(code) is None
            or account_type not in _ACCOUNT_TYPES
            or row.get("reconcile") is not True
        ):
            raise _runtime_failure(failure_type)
        result[record_id] = {
            "id": record_id,
            "code": code,
            "name": name,
            "account_type": account_type,
        }
        previous = record_id
    return result


def _candidate_domain(
    company_id: int,
    account_ids: list[int],
    after: list[Any] | None,
    filters: dict[str, Any],
) -> list[Any]:
    from odoo.fields import Domain

    domains: list[list[Any]] = [
        [
            ("company_id", "=", company_id),
            ("display_type", "not in", _EXCLUDED_DISPLAY_TYPES),
            ("account_id", "in", account_ids),
            ("full_reconcile_id", "=", False),
            ("amount_residual", "!=", 0),
            ("parent_state", "in", filters["states"]),
        ]
    ]
    for filter_name, model_field, operator in (
        ("date_from", "date", ">="),
        ("date_to", "date", "<="),
        ("partner_id", "partner_id", "="),
        ("journal_id", "journal_id", "="),
    ):
        if filters[filter_name] is not None:
            domains.append([(model_field, operator, filters[filter_name])])
    if filters["query"] is not None:
        query = filters["query"]
        domains.append(
            list(
                Domain.OR(
                    [
                        [("name", "ilike", query)],
                        [("move_name", "ilike", query)],
                        [("ref", "ilike", query)],
                        [("partner_id.name", "ilike", query)],
                    ]
                )
            )
        )
    if after is not None:
        domains.append(
            [
                "|",
                ("date", "<", after[0]),
                "&",
                ("date", "=", after[0]),
                ("id", "<", after[1]),
            ]
        )
    return list(Domain.AND(domains))


def _read_index(
    env: Any,
    model: str,
    record_ids: set[int],
    fields: tuple[str, ...],
    company_id: int,
    failure_type: Any,
    *,
    domain_tail: list[Any] | None = None,
) -> dict[int, dict[str, Any]]:
    if not record_ids:
        return {}
    domain: list[Any] = [("id", "in", sorted(record_ids))]
    if domain_tail:
        domain.extend(domain_tail)
    rows = _scoped_model(env, model, company_id).search_read(
        domain,
        fields=list(fields),
        limit=len(record_ids),
        order="id",
    )
    if not isinstance(rows, list):
        raise _runtime_failure(failure_type)
    result: dict[int, dict[str, Any]] = {}
    previous = 0
    for row in rows:
        if not isinstance(row, dict) or set(row) != set(fields):
            raise _runtime_failure(failure_type)
        record_id = row.get("id")
        if (
            not _valid_id(record_id)
            or record_id not in record_ids
            or record_id in result
            or record_id <= previous
        ):
            raise _runtime_failure(failure_type)
        result[record_id] = row
        previous = record_id
    if set(result) != record_ids:
        raise _runtime_failure(failure_type)
    return result


def _row_ids(
    rows: list[dict[str, Any]], field: str, failure_type: Any, *, optional: bool = False
) -> set[int]:
    result: set[int] = set()
    for row in rows:
        record_id = _reference_id(row.get(field), failure_type, optional=optional)
        if record_id is not None:
            result.add(record_id)
    return result


def _validate_candidate_rows(
    rows: Any,
    *,
    company_id: int,
    account_ids: set[int],
    after: list[Any] | None,
    limit: int,
    filters: dict[str, Any],
    failure_type: Any,
) -> list[dict[str, Any]]:
    if not isinstance(rows, list) or len(rows) > limit:
        raise _runtime_failure(failure_type)
    previous = tuple(after) if after is not None else None
    seen: set[int] = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != set(_CANDIDATE_FIELDS):
            raise _runtime_failure(failure_type)
        record_id = row.get("id")
        row_date = _date(row.get("date"), failure_type)
        current = (row_date, record_id)
        account_id = _reference_id(row.get("account_id"), failure_type)
        partner_id = _reference_id(
            row.get("partner_id"), failure_type, optional=True
        )
        journal_id = _reference_id(row.get("journal_id"), failure_type)
        row_company_id = _reference_id(row.get("company_id"), failure_type)
        _reference_id(row.get("move_id"), failure_type)
        _reference_id(row.get("company_currency_id"), failure_type)
        _reference_id(row.get("currency_id"), failure_type)
        _reference_id(row.get("reconcile_model_id"), failure_type, optional=True)
        display_type = row.get("display_type")
        if (
            not _valid_id(record_id)
            or record_id in seen
            or (previous is not None and current >= previous)
            or row_company_id != company_id
            or account_id not in account_ids
            or row.get("parent_state") not in filters["states"]
            or (
                filters["date_from"] is not None
                and row_date < filters["date_from"]
            )
            or (
                filters["date_to"] is not None and row_date > filters["date_to"]
            )
            or (
                filters["partner_id"] is not None
                and partner_id != filters["partner_id"]
            )
            or (
                filters["journal_id"] is not None
                and journal_id != filters["journal_id"]
            )
            or row.get("reconciled") is not False
            or not (
                row.get("full_reconcile_id") is False
                or row.get("full_reconcile_id") is None
            )
            or not (
                display_type is False
                or display_type is None
                or (
                    isinstance(display_type, str)
                    and display_type not in _EXCLUDED_DISPLAY_TYPES
                )
            )
        ):
            raise _runtime_failure(failure_type)
        _optional_date(row.get("invoice_date"), failure_type)
        _optional_date(row.get("date_maturity"), failure_type)
        _optional_text(row.get("move_name"), failure_type)
        _optional_text(row.get("ref"), failure_type)
        _optional_text(row.get("name"), failure_type)
        _optional_text(row.get("matching_number"), failure_type)
        amounts = {
            field: _decimal(row.get(field), failure_type)
            for field in (
                "balance",
                "amount_currency",
                "amount_residual",
                "amount_residual_currency",
            )
        }
        if amounts["amount_residual"] == 0:
            raise _runtime_failure(failure_type)
        seen.add(record_id)
        previous = current
    return rows


def _validate_move(row: dict[str, Any], company_id: int, failure_type: Any) -> None:
    if (
        row.get("move_type") not in _MOVE_TYPES
        or row.get("state") not in _STATES
        or _reference_id(row.get("company_id"), failure_type) != company_id
    ):
        raise _runtime_failure(failure_type)
    _optional_text(row.get("name"), failure_type)
    _optional_text(row.get("ref"), failure_type)
    _date(row.get("date"), failure_type)
    _optional_date(row.get("invoice_date"), failure_type)
    _reference_id(row.get("journal_id"), failure_type)
    _reference_id(row.get("company_currency_id"), failure_type)


def _validate_journal(
    row: dict[str, Any], scope: set[int], failure_type: Any
) -> None:
    code = _required_text(row.get("code"), failure_type)
    _required_text(row.get("name"), failure_type)
    if (
        len(code) > 5
        or row.get("type") not in _JOURNAL_TYPES
        or _reference_id(row.get("company_id"), failure_type) not in scope
    ):
        raise _runtime_failure(failure_type)


def _validate_partner(row: dict[str, Any], failure_type: Any) -> None:
    _optional_text(row.get("name"), failure_type)


def _validate_currency(row: dict[str, Any], failure_type: Any) -> None:
    code = _required_text(row.get("name"), failure_type)
    if len(code) > 3:
        raise _runtime_failure(failure_type)


def _validate_reconcile_model(
    row: dict[str, Any], company_id: int, failure_type: Any
) -> None:
    _required_text(row.get("name"), failure_type)
    if _reference_id(row.get("company_id"), failure_type) != company_id:
        raise _runtime_failure(failure_type)


def _build_candidate(
    row: dict[str, Any],
    *,
    company_id: int,
    company_currency_id: int,
    scope: set[int],
    accounts: dict[int, dict[str, Any]],
    moves: dict[int, dict[str, Any]],
    journals: dict[int, dict[str, Any]],
    partners: dict[int, dict[str, Any]],
    currencies: dict[int, dict[str, Any]],
    reconcile_models: dict[int, dict[str, Any]],
    failure_type: Any,
) -> dict[str, Any]:
    move_id = _reference_id(row["move_id"], failure_type)
    account_id = _reference_id(row["account_id"], failure_type)
    partner_id = _reference_id(row["partner_id"], failure_type, optional=True)
    journal_id = _reference_id(row["journal_id"], failure_type)
    row_company_id = _reference_id(row["company_id"], failure_type)
    row_company_currency_id = _reference_id(
        row["company_currency_id"], failure_type
    )
    currency_id = _reference_id(row["currency_id"], failure_type)
    reconcile_model_id = _reference_id(
        row["reconcile_model_id"], failure_type, optional=True
    )
    assert move_id is not None
    assert account_id is not None
    assert journal_id is not None
    assert row_company_id is not None
    assert row_company_currency_id is not None
    assert currency_id is not None

    move = moves[move_id]
    account = accounts[account_id]
    journal = journals[journal_id]
    partner = partners.get(partner_id) if partner_id is not None else None
    company_currency = currencies[row_company_currency_id]
    currency = currencies[currency_id]
    reconcile_model = (
        reconcile_models[reconcile_model_id]
        if reconcile_model_id is not None
        else None
    )

    _validate_move(move, company_id, failure_type)
    _validate_journal(journal, scope, failure_type)
    if partner is not None:
        _validate_partner(partner, failure_type)
    _validate_currency(company_currency, failure_type)
    _validate_currency(currency, failure_type)
    if reconcile_model is not None:
        _validate_reconcile_model(reconcile_model, company_id, failure_type)

    row_date = _date(row["date"], failure_type)
    row_invoice_date = _optional_date(row["invoice_date"], failure_type)
    row_move_name = _optional_text(row["move_name"], failure_type)
    row_ref = _optional_text(row["ref"], failure_type)
    move_name = _optional_text(move["name"], failure_type)
    move_ref = _optional_text(move["ref"], failure_type)
    move_invoice_date = _optional_date(move["invoice_date"], failure_type)
    move_journal_id = _reference_id(move["journal_id"], failure_type)
    move_company_currency_id = _reference_id(
        move["company_currency_id"], failure_type
    )
    if (
        row_company_id != company_id
        or row_company_currency_id != company_currency_id
        or _reference_id(move["company_id"], failure_type) != company_id
        or move_company_currency_id != company_currency_id
        or row["parent_state"] != move["state"]
        or row_move_name != move_name
        or row_ref != move_ref
        or row_date != _date(move["date"], failure_type)
        or row_invoice_date != move_invoice_date
        or journal_id != move_journal_id
    ):
        raise _runtime_failure(failure_type)

    amounts = {
        field: _decimal(row[field], failure_type)
        for field in (
            "balance",
            "amount_currency",
            "amount_residual",
            "amount_residual_currency",
        )
    }
    if amounts["amount_residual"] == 0:
        raise _runtime_failure(failure_type)
    if currency_id == company_currency_id and (
        amounts["balance"] != amounts["amount_currency"]
        or amounts["amount_residual"] != amounts["amount_residual_currency"]
    ):
        raise _runtime_failure(failure_type)

    return {
        "id": row["id"],
        "date": row_date,
        "invoice_date": row_invoice_date,
        "date_maturity": _optional_date(row["date_maturity"], failure_type),
        "state": row["parent_state"],
        "move": {
            "id": move_id,
            "name": move_name,
            "move_type": move["move_type"],
            "ref": move_ref,
        },
        "label": _optional_text(row["name"], failure_type),
        "account": account,
        "partner": (
            None
            if partner is None
            else {
                "id": partner_id,
                "name": _optional_text(partner["name"], failure_type),
            }
        ),
        "journal": {
            "id": journal_id,
            "code": _required_text(journal["code"], failure_type),
            "name": _required_text(journal["name"], failure_type),
            "type": journal["type"],
        },
        "company_id": company_id,
        "company_currency": {
            "id": company_currency_id,
            "code": _required_text(company_currency["name"], failure_type),
        },
        "currency": {
            "id": currency_id,
            "code": _required_text(currency["name"], failure_type),
        },
        **{field: _decimal_text(value) for field, value in amounts.items()},
        "matching_number": _optional_text(row["matching_number"], failure_type),
        "reconciliation_model": (
            None
            if reconcile_model is None
            else {
                "id": reconcile_model_id,
                "name": _required_text(reconcile_model["name"], failure_type),
            }
        ),
    }


def dispatch(
    env: Any,
    payload: dict[str, Any],
    company_id: int,
    *,
    failure_type: Any,
) -> dict[str, Any]:
    """Execute the fixed reconciliation-candidate read action."""

    if not _payload_is_valid(payload):
        raise _protocol_failure(failure_type)
    if payload["company_id"] != company_id:
        raise _failure(
            failure_type,
            "company_unavailable",
            "The company is unavailable.",
            3,
        )

    company_visible, module_installed, access_allowed = _gate(env, company_id)
    if not access_allowed:
        return _empty_page(
            env,
            company_visible=company_visible,
            module_installed=module_installed,
            access_allowed=False,
        )

    scope, company_currency_id = _company_scope(env, company_id, failure_type)
    accounts = _account_index(env, company_id, scope, failure_type)
    filters = payload["filters"]
    selected_accounts = {
        record_id: row
        for record_id, row in accounts.items()
        if _account_kind(row["account_type"]) in filters["account_kinds"]
        and (
            filters["account_id"] is None
            or record_id == filters["account_id"]
        )
    }
    if not selected_accounts:
        return _empty_page(
            env,
            company_visible=True,
            module_installed=True,
            access_allowed=True,
        )

    raw_rows = _scoped_model(env, "account.move.line", company_id).search_read(
        _candidate_domain(
            company_id,
            sorted(selected_accounts),
            payload["after"],
            filters,
        ),
        fields=list(_CANDIDATE_FIELDS),
        limit=payload["limit"],
        order="date desc,id desc",
    )
    rows = _validate_candidate_rows(
        raw_rows,
        company_id=company_id,
        account_ids=set(selected_accounts),
        after=payload["after"],
        limit=payload["limit"],
        filters=filters,
        failure_type=failure_type,
    )
    if not rows:
        return _empty_page(
            env,
            company_visible=True,
            module_installed=True,
            access_allowed=True,
        )

    move_ids = _row_ids(rows, "move_id", failure_type)
    journal_ids = _row_ids(rows, "journal_id", failure_type)
    partner_ids = _row_ids(rows, "partner_id", failure_type, optional=True)
    currency_ids = _row_ids(rows, "currency_id", failure_type) | _row_ids(
        rows, "company_currency_id", failure_type
    )
    reconcile_model_ids = _row_ids(
        rows, "reconcile_model_id", failure_type, optional=True
    )
    moves = _read_index(
        env,
        "account.move",
        move_ids,
        _MOVE_FIELDS,
        company_id,
        failure_type,
        domain_tail=[("company_id", "=", company_id)],
    )
    journals = _read_index(
        env,
        "account.journal",
        journal_ids,
        _JOURNAL_FIELDS,
        company_id,
        failure_type,
        domain_tail=[("company_id", "in", scope)],
    )
    partners = _read_index(
        env,
        "res.partner",
        partner_ids,
        _PARTNER_FIELDS,
        company_id,
        failure_type,
    )
    currencies = _read_index(
        env,
        "res.currency",
        currency_ids,
        _CURRENCY_FIELDS,
        company_id,
        failure_type,
    )
    reconcile_models = _read_index(
        env,
        "account.reconcile.model",
        reconcile_model_ids,
        _RECONCILE_MODEL_FIELDS,
        company_id,
        failure_type,
        domain_tail=[("company_id", "=", company_id)],
    )
    if company_currency_id not in currencies:
        raise _runtime_failure(failure_type)

    scope_set = set(scope)
    result_rows = [
        _build_candidate(
            row,
            company_id=company_id,
            company_currency_id=company_currency_id,
            scope=scope_set,
            accounts=selected_accounts,
            moves=moves,
            journals=journals,
            partners=partners,
            currencies=currencies,
            reconcile_models=reconcile_models,
            failure_type=failure_type,
        )
        for row in rows
    ]
    return {
        "user_id": env.uid,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "rows": result_rows,
    }
