from __future__ import annotations

import io
import json
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

from odoo_accounting_cli_v4.bridge import bank_reconciliation_runtime as bank_runtime
from odoo_accounting_cli_v4.bridge import runtime


class Failure(RuntimeError):
    def __init__(self, code: str, message: str, *, exit_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


class Records:
    def __init__(self, rows: list[Any] | None = None, **relations: Any) -> None:
        self.rows = list(rows or [])
        self.relations = dict(relations)

    @property
    def ids(self) -> list[int]:
        return [row.id for row in self.rows]

    @property
    def id(self) -> int | bool:
        return self.rows[0].id if len(self.rows) == 1 else False

    def __bool__(self) -> bool:
        return bool(self.rows)

    def __len__(self) -> int:
        return len(self.rows)

    def __iter__(self):
        return iter(self.rows)

    def __getattr__(self, name: str) -> Any:
        if name in self.relations:
            return self.relations[name]
        if len(self.rows) == 1:
            return getattr(self.rows[0], name)
        raise AttributeError(name)

    def __or__(self, other: Records) -> Records:
        rows = {row.id: row for row in [*self.rows, *other.rows]}
        return Records(list(rows.values()))


def _line(line_id: int, balance: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=line_id,
        account_id=SimpleNamespace(id=20),
        partner_id=SimpleNamespace(id=False),
        currency_id=SimpleNamespace(id=1),
        balance=Decimal(balance),
        amount_currency=Decimal(balance),
        amount_residual=Decimal(balance),
        amount_residual_currency=Decimal(balance),
        name="Liquidity" if line_id == 70 else "Suspense",
    )


def _transaction() -> SimpleNamespace:
    empty = Records()
    liquidity = Records([_line(70, "50")])
    suspense = Records([_line(71, "-50")])
    move_lines = Records(
        [*liquidity.rows, *suspense.rows],
        matched_debit_ids=empty,
        matched_credit_ids=empty,
    )
    move = SimpleNamespace(
        id=40,
        state="posted",
        move_type="entry",
        company_id=SimpleNamespace(id=7),
        line_ids=move_lines,
    )
    return SimpleNamespace(
        id=41,
        company_id=SimpleNamespace(id=7),
        move_id=move,
        date="2026-08-26",
        journal_id=SimpleNamespace(id=9),
        partner_id=SimpleNamespace(id=False),
        amount=Decimal(50),
        currency_id=SimpleNamespace(id=1),
        foreign_currency_id=SimpleNamespace(id=False),
        amount_currency=Decimal(50),
        amount_residual=Decimal(-50),
        is_reconciled=False,
        checked=True,
        payment_ids=Records(),
        _seek_for_lines=lambda: (liquidity, suspense, Records()),
    )


def test_two_fixed_read_actions_are_allowlisted_and_read_only() -> None:
    for action, payload in (
        (
            bank_runtime.GET_ACTION,
            {"company_id": 7, "transaction_id": 41},
        ),
        (
            bank_runtime.CANDIDATE_ACTION,
            {"company_id": 7, "transaction_id": 41, "after": None, "limit": 2},
        ),
    ):
        request = {
            "schema_version": "v1",
            "target": {
                "alias": "test",
                "database": "odoo_cli_v4_dev",
                "company_id": 7,
                "user_login": "accountant",
                "language": "en_US",
                "timezone": "UTC",
            },
            "action": action,
            "payload": payload,
        }

        assert runtime._decode_request(io.StringIO(json.dumps(request))) == request
        assert runtime._cursor_factory_for(action, payload) is runtime._read_only_cursor


def test_bank_search_runtime_accepts_only_the_normalized_filter_shape() -> None:
    payload = {
        "company_id": 7,
        "after": ["2026-08-26", 41],
        "limit": 101,
        "filters": {
            "date_from": "2026-08-01",
            "date_to": "2026-08-31",
            "journal_id": 9,
            "partner_id": None,
            "reconciled": False,
            "query": "Deposit",
        },
    }

    assert runtime._bank_transaction_payload_is_valid(payload) is True
    payload["filters"]["unexpected"] = True
    assert runtime._bank_transaction_payload_is_valid(payload) is False


def test_reconciliation_get_normalizes_the_fixed_graph_without_sudo() -> None:
    result = bank_runtime._get_result(_transaction(), 7, Failure)

    assert result == {
        "transaction": {
            "id": 41,
            "company_id": 7,
            "move_id": 40,
            "move_state": "posted",
            "date": "2026-08-26",
            "journal_id": 9,
            "partner_id": None,
            "amount": "50",
            "currency_id": 1,
            "foreign_currency_id": None,
            "amount_currency": "50",
            "amount_residual": "-50",
            "is_reconciled": False,
            "checked": True,
        },
        "liquidity_line": {
            "id": 70,
            "account_id": 20,
            "partner_id": None,
            "currency_id": 1,
            "balance": "50",
            "amount_currency": "50",
            "amount_residual": "50",
            "amount_residual_currency": "50",
        },
        "suspense_line": {
            "id": 71,
            "account_id": 20,
            "partner_id": None,
            "currency_id": 1,
            "balance": "-50",
            "amount_currency": "-50",
            "amount_residual": "-50",
            "amount_residual_currency": "-50",
        },
        "matched_lines": [],
        "writeoff_lines": [],
        "payment_ids": [],
    }


def test_denied_reconciliation_read_returns_only_the_closed_empty_page() -> None:
    env = SimpleNamespace(uid=5)

    page = bank_runtime._empty_page(
        env,
        bank_runtime.GET_ACTION,
        company_visible=True,
        module_installed=True,
        access_allowed=False,
    )

    assert page == {
        "user_id": 5,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": False,
        "result": None,
    }
