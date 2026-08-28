"""Odoo-side fixed reads for one bank transaction's reconciliation state."""

from __future__ import annotations

from typing import Any

from odoo_accounting_cli_v4.bridge import (
    reconciliation_candidates_runtime as candidates,
)

GET_ACTION = "account.bank.statement.line.reconciliation.get"
CANDIDATE_ACTION = "account.bank.statement.line.match_candidate.read_page"
ACTIONS = frozenset({GET_ACTION, CANDIDATE_ACTION})

_GET_MODELS = (
    "res.company",
    "account.bank.statement.line",
    "account.move",
    "account.move.line",
    "account.partial.reconcile",
    "account.full.reconcile",
    "account.payment",
    "res.currency",
)


def _failure(
    failure_type: type[Exception], code: str, message: str, exit_code: int
) -> Exception:
    return failure_type(code, message, exit_code=exit_code)


def _protocol(failure_type: type[Exception]) -> Exception:
    return _failure(
        failure_type,
        "bridge_protocol_error",
        "The bridge action payload is invalid.",
        7,
    )


def _runtime(failure_type: type[Exception]) -> Exception:
    return _failure(
        failure_type,
        "odoo_runtime_error",
        "The Odoo runtime request failed.",
        7,
    )


def _valid_id(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _valid_date(value: Any) -> bool:
    return candidates._is_canonical_date(value)


def _decimal_text(value: Any, failure_type: type[Exception]) -> str:
    return candidates._decimal_text(candidates._decimal(value, failure_type))


def _scoped(env: Any, model: str, company_id: int) -> Any:
    return env[model].with_context(
        active_test=False,
        allowed_company_ids=[company_id],
    )


def _payload_is_valid(action: str, payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False
    if action == GET_ACTION:
        return set(payload) == {"company_id", "transaction_id"} and all(
            _valid_id(payload[field]) for field in payload
        )
    if set(payload) != {"company_id", "transaction_id", "after", "limit"}:
        return False
    if not all(_valid_id(payload[field]) for field in ("company_id", "transaction_id")):
        return False
    if not _valid_id(payload["limit"]) or payload["limit"] > 1001:
        return False
    after = payload["after"]
    return after is None or (
        isinstance(after, list)
        and len(after) == 2
        and _valid_date(after[0])
        and _valid_id(after[1])
    )


def _empty_page(
    env: Any,
    action: str,
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
        ("result" if action == GET_ACTION else "rows"): (
            None if action == GET_ACTION else []
        ),
    }


def _gate(env: Any, action: str, company_id: int) -> tuple[bool, bool, bool]:
    if action == CANDIDATE_ACTION:
        company_visible, module_installed, access_allowed = candidates._gate(
            env, company_id
        )
        statement_installed = (
            env.registry.get("account.bank.statement.line") is not None
        )
        module_installed = bool(module_installed and statement_installed)
        access_allowed = bool(
            access_allowed
            and module_installed
            and env["account.bank.statement.line"].has_access("read")
            and env.user.has_group("account.group_account_user")
        )
        return company_visible, module_installed, access_allowed

    installed = {model: env.registry.get(model) is not None for model in _GET_MODELS}
    module_installed = all(installed.values())
    company_read = bool(
        installed["res.company"] and env["res.company"].has_access("read")
    )
    company_visible = bool(
        company_read
        and env["res.company"].search_count([("id", "=", company_id)], limit=1)
    )
    access_allowed = bool(
        company_visible
        and module_installed
        and env.user.has_group("account.group_account_user")
        and all(env[model].has_access("read") for model in _GET_MODELS)
    )
    return company_visible, module_installed, access_allowed


def _line(line: Any, failure_type: type[Exception]) -> dict[str, Any]:
    if (
        not _valid_id(line.id)
        or not line.account_id
        or not line.currency_id
        or not _valid_id(line.account_id.id)
        or not _valid_id(line.currency_id.id)
    ):
        raise _runtime(failure_type)
    return {
        "id": line.id,
        "account_id": line.account_id.id,
        "partner_id": line.partner_id.id or None,
        "currency_id": line.currency_id.id,
        "balance": _decimal_text(line.balance, failure_type),
        "amount_currency": _decimal_text(line.amount_currency, failure_type),
        "amount_residual": _decimal_text(line.amount_residual, failure_type),
        "amount_residual_currency": _decimal_text(
            line.amount_residual_currency, failure_type
        ),
    }


def _matched_lines(
    transaction: Any, failure_type: type[Exception]
) -> list[dict[str, Any]]:
    bank_ids = set(transaction.move_id.line_ids.ids)
    partials = (
        transaction.move_id.line_ids.matched_debit_ids
        | transaction.move_id.line_ids.matched_credit_ids
    )
    result: list[dict[str, Any]] = []
    observed: set[tuple[int, int]] = set()
    for partial in partials:
        debit = partial.debit_move_id
        credit = partial.credit_move_id
        debit_is_bank = debit.id in bank_ids
        credit_is_bank = credit.id in bank_ids
        if debit_is_bank == credit_is_bank:
            continue
        bank_line = debit if debit_is_bank else credit
        source = credit if debit_is_bank else debit
        identity = (bank_line.id, source.id)
        if identity in observed or source.company_id.id != transaction.company_id.id:
            raise _runtime(failure_type)
        observed.add(identity)
        sign = 1 if debit_is_bank else -1
        applied_currency = (
            partial.debit_amount_currency
            if debit_is_bank
            else partial.credit_amount_currency
        )
        full = partial.full_reconcile_id or bank_line.full_reconcile_id
        result.append(
            {
                "bank_move_line_id": bank_line.id,
                "source_line_id": source.id,
                "source_move_id": source.move_id.id,
                "account_id": source.account_id.id,
                "partner_id": source.partner_id.id or None,
                "currency_id": source.currency_id.id,
                "applied_balance": _decimal_text(sign * partial.amount, failure_type),
                "applied_amount_currency": _decimal_text(
                    sign * applied_currency, failure_type
                ),
                "source_amount_residual": _decimal_text(
                    source.amount_residual, failure_type
                ),
                "source_amount_residual_currency": _decimal_text(
                    source.amount_residual_currency, failure_type
                ),
                "full_reconcile_id": full.id or None,
            }
        )
    return sorted(
        result,
        key=lambda item: (item["source_line_id"], item["bank_move_line_id"]),
    )


def _get_result(
    transaction: Any, company_id: int, failure_type: type[Exception]
) -> dict[str, Any]:
    move = transaction.move_id
    liquidity, suspense, other = transaction._seek_for_lines()
    if (
        transaction.company_id.id != company_id
        or move.company_id.id != company_id
        or move.move_type != "entry"
        or len(liquidity) != 1
        or len(suspense) > 1
        or not transaction.currency_id
    ):
        raise _runtime(failure_type)
    writeoffs = [
        {
            "id": line.id,
            "name": candidates._required_text(line.name, failure_type),
            "account_id": line.account_id.id,
            "partner_id": line.partner_id.id or None,
            "currency_id": line.currency_id.id,
            "balance": _decimal_text(line.balance, failure_type),
            "amount_currency": _decimal_text(line.amount_currency, failure_type),
        }
        for line in sorted(other, key=lambda item: item.id)
    ]
    return {
        "transaction": {
            "id": transaction.id,
            "company_id": company_id,
            "move_id": move.id,
            "move_state": move.state,
            "date": candidates._date(transaction.date, failure_type),
            "journal_id": transaction.journal_id.id,
            "partner_id": transaction.partner_id.id or None,
            "amount": _decimal_text(transaction.amount, failure_type),
            "currency_id": transaction.currency_id.id,
            "foreign_currency_id": transaction.foreign_currency_id.id or None,
            "amount_currency": _decimal_text(transaction.amount_currency, failure_type),
            "amount_residual": _decimal_text(transaction.amount_residual, failure_type),
            "is_reconciled": bool(transaction.is_reconciled),
            "checked": bool(transaction.checked),
        },
        "liquidity_line": _line(liquidity, failure_type),
        "suspense_line": _line(suspense, failure_type) if suspense else None,
        "matched_lines": _matched_lines(transaction, failure_type),
        "writeoff_lines": writeoffs,
        "payment_ids": sorted(set(transaction.payment_ids.ids)),
    }


def _dispatch_get(
    env: Any,
    payload: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> dict[str, Any]:
    transactions = _scoped(env, "account.bank.statement.line", company_id).search(
        [
            ("id", "=", payload["transaction_id"]),
            ("company_id", "=", company_id),
        ],
        limit=2,
    )
    if not transactions:
        return _empty_page(
            env,
            GET_ACTION,
            company_visible=True,
            module_installed=True,
            access_allowed=True,
        )
    if len(transactions) != 1:
        raise _runtime(failure_type)
    return {
        "user_id": env.uid,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "result": _get_result(transactions, company_id, failure_type),
    }


def _candidate_domain(transaction: Any, after: list[Any] | None) -> list[Any]:
    from odoo.fields import Domain

    domains: list[list[Any]] = [
        list(transaction._get_default_amls_matching_domain(False)),
        [
            ("company_id", "=", transaction.company_id.id),
            ("statement_line_id", "!=", transaction.id),
        ],
    ]
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


def _dispatch_candidates(
    env: Any,
    payload: dict[str, Any],
    company_id: int,
    failure_type: type[Exception],
) -> dict[str, Any]:
    transactions = _scoped(env, "account.bank.statement.line", company_id).search(
        [
            ("id", "=", payload["transaction_id"]),
            ("company_id", "=", company_id),
        ],
        limit=2,
    )
    if not transactions:
        return _empty_page(
            env,
            CANDIDATE_ACTION,
            company_visible=True,
            module_installed=True,
            access_allowed=True,
        )
    if len(transactions) != 1 or transactions.move_id.state != "posted":
        raise _runtime(failure_type)

    scope, company_currency_id = candidates._company_scope(
        env, company_id, failure_type
    )
    accounts = candidates._account_index(env, company_id, scope, failure_type)
    raw_rows = _scoped(env, "account.move.line", company_id).search_read(
        _candidate_domain(transactions, payload["after"]),
        fields=list(candidates._CANDIDATE_FIELDS),
        limit=payload["limit"],
        order="date desc,id desc",
    )
    filters = {
        "date_from": None,
        "date_to": None,
        "states": ["posted"],
        "account_id": None,
        "partner_id": None,
        "journal_id": None,
        "account_kinds": ["receivable", "payable", "other"],
        "query": None,
    }
    rows = candidates._validate_candidate_rows(
        raw_rows,
        company_id=company_id,
        account_ids=set(accounts),
        after=payload["after"],
        limit=payload["limit"],
        filters=filters,
        failure_type=failure_type,
    )
    move_ids = candidates._row_ids(rows, "move_id", failure_type)
    journal_ids = candidates._row_ids(rows, "journal_id", failure_type)
    partner_ids = candidates._row_ids(rows, "partner_id", failure_type, optional=True)
    currency_ids = candidates._row_ids(
        rows, "currency_id", failure_type
    ) | candidates._row_ids(rows, "company_currency_id", failure_type)
    reconcile_model_ids = candidates._row_ids(
        rows, "reconcile_model_id", failure_type, optional=True
    )
    moves = candidates._read_index(
        env,
        "account.move",
        move_ids,
        candidates._MOVE_FIELDS,
        company_id,
        failure_type,
        domain_tail=[("company_id", "=", company_id)],
    )
    journals = candidates._read_index(
        env,
        "account.journal",
        journal_ids,
        candidates._JOURNAL_FIELDS,
        company_id,
        failure_type,
        domain_tail=[("company_id", "in", scope)],
    )
    partners = candidates._read_index(
        env,
        "res.partner",
        partner_ids,
        candidates._PARTNER_FIELDS,
        company_id,
        failure_type,
    )
    currencies = candidates._read_index(
        env,
        "res.currency",
        currency_ids,
        candidates._CURRENCY_FIELDS,
        company_id,
        failure_type,
    )
    reconcile_models = candidates._read_index(
        env,
        "account.reconcile.model",
        reconcile_model_ids,
        candidates._RECONCILE_MODEL_FIELDS,
        company_id,
        failure_type,
        domain_tail=[("company_id", "=", company_id)],
    )
    scope_set = set(scope)
    normalized = [
        candidates._build_candidate(
            row,
            company_id=company_id,
            company_currency_id=company_currency_id,
            scope=scope_set,
            accounts=accounts,
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
        "rows": normalized,
    }


def dispatch(
    env: Any,
    action: str,
    payload: dict[str, Any],
    company_id: int,
    *,
    failure_type: type[Exception],
) -> dict[str, Any]:
    """Execute one of the two fixed bank-reconciliation read actions."""

    if action not in ACTIONS or not _payload_is_valid(action, payload):
        raise _protocol(failure_type)
    if payload["company_id"] != company_id:
        raise _failure(
            failure_type,
            "company_unavailable",
            "The company is unavailable.",
            3,
        )
    company_visible, module_installed, access_allowed = _gate(env, action, company_id)
    if not access_allowed:
        return _empty_page(
            env,
            action,
            company_visible=company_visible,
            module_installed=module_installed,
            access_allowed=False,
        )
    if action == GET_ACTION:
        return _dispatch_get(env, payload, company_id, failure_type)
    return _dispatch_candidates(env, payload, company_id, failure_type)
