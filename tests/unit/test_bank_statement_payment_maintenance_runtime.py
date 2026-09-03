from __future__ import annotations

import sys
from decimal import ROUND_HALF_UP, Decimal
from types import SimpleNamespace
from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge import core_writes_runtime as writes
from odoo_accounting_cli_v4.registry import load_registry

CAPABILITIES = {
    "bank.statement.create",
    "bank.statement.update",
    "bank.statement.delete",
    "bank.transaction.delete",
    "payment.duplicate",
    "payment.delete",
}


class Failure(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        exit_code: int,
        retryable: bool,
        details: dict[str, Any],
    ) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code
        self.retryable = retryable
        self.details = details


class Records(list[Any]):
    @property
    def ids(self) -> list[int]:
        return [record.id for record in self]

    def sorted(self, key):
        return Records(sorted(self, key=key))

    def __getattr__(self, name: str) -> Any:
        if len(self) != 1:
            raise AttributeError(name)
        return getattr(self[0], name)


class Currency:
    id = 1

    def __bool__(self) -> bool:
        return True

    def round(self, value: float) -> Decimal:
        assert isinstance(value, float)
        return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _result(
    model: str, record_id: int, *, source_id: int | None = None
) -> dict[str, Any]:
    return {
        "model": model,
        "id": record_id,
        "name": None,
        "state": "draft",
        "company_id": 7,
        "move_type": None,
        "source_id": source_id,
        "line_ids": [901],
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }


def test_static_contract_gate_and_deterministic_keys_are_exact() -> None:
    assert CAPABILITIES <= writes.CAPABILITIES
    assert {
        writes._GROUPS[item] for item in CAPABILITIES if not item.startswith("payment.")
    } == {"account.group_account_user"}
    assert {
        writes._GROUPS[item] for item in CAPABILITIES if item.startswith("payment.")
    } == {"account.group_account_invoice"}
    assert writes._PARAMETER_KEYS["bank.statement.create"] == {
        "transaction_ids",
        "reference",
        "balance_end_real",
    }
    assert writes._PARAMETER_KEYS["bank.statement.update"] == {
        "statement_id",
        "changes",
    }
    assert writes._PARAMETER_KEYS["bank.statement.delete"] == {"statement_id"}
    assert writes._PARAMETER_KEYS["bank.transaction.delete"] == {"transaction_id"}
    assert writes._PARAMETER_KEYS["payment.duplicate"] == {"payment_id"}
    assert writes._PARAMETER_KEYS["payment.delete"] == {"payment_id"}
    assert writes._MODELS["bank.statement.create"] == {
        "res.company",
        "res.currency",
        "account.journal",
        "account.bank.statement",
        "account.bank.statement.line",
        "account.move",
    }
    assert writes._ACCESS["bank.statement.create"] == {
        ("res.currency", "read"),
        ("account.journal", "read"),
        ("account.bank.statement", "read"),
        ("account.bank.statement", "create"),
        ("account.bank.statement.line", "read"),
        ("account.bank.statement.line", "write"),
        ("account.move", "read"),
    }
    assert writes._MODELS["payment.delete"] == {
        "res.company",
        "account.payment",
        "account.move",
        "account.move.line",
        "account.partial.reconcile",
        "account.full.reconcile",
    }
    assert writes._ACCESS["payment.delete"] == {
        ("account.payment", "read"),
        ("account.payment", "unlink"),
        ("account.move", "read"),
        ("account.move", "write"),
        ("account.move", "unlink"),
        ("account.move.line", "read"),
        ("account.partial.reconcile", "read"),
        ("account.full.reconcile", "read"),
    }

    create = {
        "transaction_ids": [11, 12],
        "reference": "February",
        "balance_end_real": "12.34",
    }
    update = {"statement_id": 21, "changes": {"reference": None}}
    assert writes._valid_parameters("bank.statement.create", create)
    assert writes._valid_parameters("bank.statement.update", update)
    assert writes._deterministic_key("bank.statement.create", create, 7).startswith(
        "bank.statement.create:7:"
    )
    assert writes._deterministic_key("bank.statement.update", update, 7).startswith(
        "bank.statement.update:21:"
    )
    assert (
        writes._deterministic_key("bank.statement.delete", {"statement_id": 21}, 7)
        == "bank.statement.delete:21"
    )
    assert (
        writes._deterministic_key("bank.transaction.delete", {"transaction_id": 31}, 7)
        == "bank.transaction.delete:31"
    )
    assert (
        writes._deterministic_key("payment.duplicate", {"payment_id": 41}, 7)
        == "payment.duplicate:41"
    )
    assert (
        writes._deterministic_key("payment.delete", {"payment_id": 41}, 7)
        == "payment.delete:41"
    )


def test_direct_dependency_descriptors_are_exact() -> None:
    registry = load_registry()
    statement_create = registry.describe("bank.statement.create")
    assert statement_create["source"]["models"] == [
        "res.company",
        "res.currency",
        "account.journal",
        "account.bank.statement",
        "account.bank.statement.line",
        "account.move",
    ]
    assert statement_create["source"]["locations"] == [
        "_references/base/models/res_company.py",
        "_references/base/models/res_currency.py",
        "account/models/account_journal.py",
        "account/models/account_bank_statement.py",
        "account/models/account_bank_statement_line.py",
        "account/models/account_move.py",
    ]
    assert statement_create["requirements"]["acl"] == [
        "res.currency:read",
        "account.journal:read",
        "account.bank.statement:read",
        "account.bank.statement:create",
        "account.bank.statement.line:read",
        "account.bank.statement.line:write",
        "account.move:read",
    ]

    payment_delete = registry.describe("payment.delete")
    assert payment_delete["requirements"]["acl"] == [
        "account.payment:read",
        "account.payment:unlink",
        "account.move:read",
        "account.move:write",
        "account.move:unlink",
        "account.move.line:read",
        "account.partial.reconcile:read",
        "account.full.reconcile:read",
    ]


@pytest.mark.parametrize(
    "parameters",
    [
        {"transaction_ids": [], "reference": None, "balance_end_real": "0"},
        {"transaction_ids": [2, 1], "reference": None, "balance_end_real": "0"},
        {"transaction_ids": [1, 1], "reference": None, "balance_end_real": "0"},
        {"transaction_ids": [1], "reference": " padded ", "balance_end_real": "0"},
        {"transaction_ids": [1], "reference": None, "balance_end_real": "01.0"},
        {"transaction_ids": [1], "reference": None, "balance_end_real": 1},
    ],
)
def test_statement_create_rejects_noncanonical_parameters(
    parameters: dict[str, Any],
) -> None:
    assert not writes._valid_parameters("bank.statement.create", parameters)


def test_statement_contiguity_rejects_missing_active_lines_and_ignores_canceled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = Records(
        [
            SimpleNamespace(id=11, internal_index="001", state="posted"),
            SimpleNamespace(id=13, internal_index="003", state="posted"),
        ]
    )
    middle = SimpleNamespace(id=12, internal_index="002", state="posted")

    class TransactionModel:
        def search(self, _domain, **_kwargs):
            return Records(
                transaction
                for transaction in [selected[0], middle, selected[1]]
                if transaction.state != "cancel"
            )

    monkeypatch.setattr(
        writes,
        "_scoped",
        lambda _env, _model, _company_id: TransactionModel(),
    )

    assert not writes._bank_statement_transactions_are_contiguous(
        None, selected, 5, 7
    )
    middle.state = "cancel"
    assert writes._bank_statement_transactions_are_contiguous(None, selected, 5, 7)


def test_statement_create_replays_exact_natural_key_then_updates_and_deletes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    company = SimpleNamespace(id=7, currency_id=Currency())
    journal = SimpleNamespace(
        id=5, company_id=company, currency_id=Currency(), type="bank"
    )
    move = SimpleNamespace(company_id=company, move_type="entry", state="posted")
    transactions = Records(
        [
            SimpleNamespace(
                id=11,
                internal_index="2026-02-01-00001",
                state="posted",
                company_id=company,
                journal_id=journal,
                statement_id=False,
                move_id=move,
            ),
            SimpleNamespace(
                id=12,
                internal_index="2026-02-01-00002",
                state="posted",
                company_id=company,
                journal_id=journal,
                statement_id=False,
                move_id=move,
            ),
        ]
    )

    class Statement:
        id = 21
        name = "STMT/21"
        company_id = company
        journal_id = journal
        currency_id = journal.currency_id
        reference = "February"
        balance_end_real = Decimal("12.35")
        is_complete = True
        line_ids = transactions

        def invalidate_recordset(self, _fields):
            return None

        def write(self, values):
            for name, value in values.items():
                setattr(self, name, value)

        def unlink(self):
            statement_model.rows.clear()
            for transaction in transactions:
                transaction.statement_id = False

    statement = Statement()

    class StatementModel:
        def __init__(self):
            self.rows = Records()
            self.created_values = None
            self.context = None

        def with_context(self, **context):
            self.context = context
            return self

        def search(self, _domain, **_kwargs):
            return self.rows

        def create(self, values):
            self.created_values = values
            self.rows = Records([statement])
            for transaction in transactions:
                transaction.statement_id = statement
            return self.rows

        def search_count(self, _domain, **_kwargs):
            return len(self.rows)

    statement_model = StatementModel()

    class TransactionModel:
        def search(self, _domain, **_kwargs):
            return transactions

    monkeypatch.setitem(
        sys.modules,
        "odoo",
        SimpleNamespace(Command=SimpleNamespace(set=lambda ids: ("set", ids))),
    )
    monkeypatch.setattr(writes, "_bank_is_default_unmatched", lambda _record: True)
    monkeypatch.setattr(writes, "_ensure_ids", lambda *_args, **_kwargs: transactions)
    monkeypatch.setattr(
        writes,
        "_scoped",
        lambda _env, model, _company_id: (
            statement_model if model == "account.bank.statement" else TransactionModel()
        ),
    )

    parameters = {
        "transaction_ids": [11, 12],
        "reference": "February",
        "balance_end_real": "12.345",
    }
    first, replay = writes._create_bank_statement(None, parameters, 7, Failure)
    assert not replay
    assert first["state"] == "complete"
    assert first["line_ids"] == [11, 12]
    assert statement_model.created_values == {
        "line_ids": [("set", [11, 12])],
        "reference": "February",
        "balance_end_real": Decimal("12.35"),
    }
    assert statement_model.context == {"skip_pdf_attachment_generation": True}

    second, replay = writes._create_bank_statement(None, parameters, 7, Failure)
    assert replay
    assert second == first

    monkeypatch.setattr(
        writes, "_search_one", lambda *_args, **_kwargs: statement_model.rows
    )
    updated, replay = writes._update_bank_statement(
        None,
        {"statement_id": 21, "changes": {"reference": None, "balance_end_real": "20"}},
        7,
        Failure,
    )
    assert not replay
    assert updated["id"] == 21
    assert statement.reference is False
    assert statement.balance_end_real == Decimal(20)

    deleted, replay = writes._delete_bank_statement(
        None, {"statement_id": 21}, 7, Failure
    )
    assert not replay
    assert deleted["state"] == "deleted"
    assert deleted["line_ids"] == [11, 12]
    assert not statement_model.rows
    assert all(transaction.statement_id is False for transaction in transactions)


def test_payment_native_duplicate_exact_replay_and_verified_delete(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    company = SimpleNamespace(id=7)
    line_ids = Records([SimpleNamespace(id=901)])
    move_model_rows: dict[int, Any] = {}
    payment_model_rows: dict[int, Any] = {}

    class Payment:
        def __init__(self, record_id: int, *, memo: str, state: str = "draft") -> None:
            self.id = record_id
            self.company_id = company
            self.memo = memo
            self.state = state
            self.name = None
            self.is_reconciled = False
            self.payment_reference = "Customer receipt"
            self.move_id = SimpleNamespace(
                id=record_id + 100, company_id=company, line_ids=line_ids
            )

        def copy(self, default):
            assert default == {
                "memo": "source [ODACV4DUP:payment.duplicate:41]",
                "payment_reference": "Customer receipt",
            }
            duplicate = Payment(42, memo=default["memo"])
            payment_model_rows[duplicate.id] = duplicate
            move_model_rows[duplicate.move_id.id] = duplicate.move_id
            return duplicate

        def unlink(self):
            payment_model_rows.pop(self.id, None)
            if self.move_id:
                move_model_rows.pop(self.move_id.id, None)

    source = Payment(41, memo="source", state="canceled")
    payment_model_rows[source.id] = source
    move_model_rows[source.move_id.id] = source.move_id

    class Model:
        def __init__(self, rows: dict[int, Any]) -> None:
            self.rows = rows

        def search(self, domain, **_kwargs):
            memo_filter = next(
                ((op, value) for field, op, value in domain if field == "memo"),
                (None, None),
            )
            excluded = next(
                (value for field, op, value in domain if field == "id" and op == "!="),
                None,
            )
            return Records(
                record
                for record in self.rows.values()
                if (
                    memo_filter[0] is None
                    or (
                        memo_filter[0] == "="
                        and getattr(record, "memo", None) == memo_filter[1]
                    )
                    or (
                        memo_filter[0] == "=like"
                        and getattr(record, "memo", "").endswith(
                            memo_filter[1].removeprefix("%")
                        )
                    )
                )
                and record.id != excluded
            )

        def search_count(self, domain, **_kwargs):
            record_id = next(value for field, _op, value in domain if field == "id")
            return int(record_id in self.rows)

    payment_model = Model(payment_model_rows)
    move_model = Model(move_model_rows)
    monkeypatch.setattr(writes, "_search_one", lambda *_args, **_kwargs: source)
    monkeypatch.setattr(
        writes,
        "_scoped",
        lambda _env, model, _company_id: (
            payment_model if model == "account.payment" else move_model
        ),
    )
    monkeypatch.setattr(
        writes, "_payment_actual_values", lambda _payment: {"amount": "10"}
    )
    monkeypatch.setattr(
        writes,
        "_payment_result",
        lambda payment, _company_id, *, source_id: {
            **_result("account.payment", payment.id, source_id=source_id),
            "line_ids": [901] if payment.move_id else [],
        },
    )
    monkeypatch.setattr(writes, "_external_reconcile_ids", lambda _move: (set(), set()))

    first, replay = writes._duplicate_payment(
        None, {"payment_id": 41}, 7, "payment.duplicate:41", Failure
    )
    assert not replay
    assert first["source_id"] == 41
    assert (
        payment_model_rows[42].memo
        == "source [ODACV4DUP:payment.duplicate:41]"
    )

    second, replay = writes._duplicate_payment(
        None, {"payment_id": 41}, 7, "payment.duplicate:41", Failure
    )
    assert replay
    assert second == first

    source.memo = "changed source memo"
    with pytest.raises(Failure) as caught:
        writes._duplicate_payment(
            None, {"payment_id": 41}, 7, "payment.duplicate:41", Failure
        )
    assert caught.value.code == "idempotency_conflict"
    source.memo = "source"

    duplicate = payment_model_rows[42]
    monkeypatch.setattr(writes, "_search_one", lambda *_args, **_kwargs: duplicate)
    deleted, replay = writes._delete_payment(None, {"payment_id": 42}, 7, Failure)
    assert not replay
    assert deleted["state"] == "deleted"
    assert deleted["line_ids"] == [901]
    assert 42 not in payment_model_rows
    assert 142 not in move_model_rows

    draft_without_move = Payment(43, memo="draft-without-move")
    draft_without_move.move_id = False
    payment_model_rows[43] = draft_without_move
    monkeypatch.setattr(
        writes, "_search_one", lambda *_args, **_kwargs: draft_without_move
    )
    deleted, replay = writes._delete_payment(None, {"payment_id": 43}, 7, Failure)
    assert not replay
    assert deleted["state"] == "deleted"
    assert deleted["line_ids"] == []
    assert 43 not in payment_model_rows


@pytest.mark.parametrize(
    ("state", "is_reconciled", "external_partials", "external_fulls"),
    [
        ("paid", False, set(), set()),
        ("draft", True, set(), set()),
        ("draft", False, {501}, set()),
        ("draft", False, set(), {601}),
    ],
)
def test_payment_delete_rejects_unsafe_states(
    monkeypatch: pytest.MonkeyPatch,
    state: str,
    is_reconciled: bool,
    external_partials: set[int],
    external_fulls: set[int],
) -> None:
    company = SimpleNamespace(id=7)
    payment = SimpleNamespace(
        id=41,
        company_id=company,
        state=state,
        is_reconciled=is_reconciled,
        move_id=SimpleNamespace(id=141, company_id=company),
    )
    monkeypatch.setattr(writes, "_search_one", lambda *_args, **_kwargs: payment)
    monkeypatch.setattr(
        writes,
        "_external_reconcile_ids",
        lambda _move: (external_partials, external_fulls),
    )

    with pytest.raises(Failure) as caught:
        writes._delete_payment(None, {"payment_id": 41}, 7, Failure)
    assert caught.value.code == "state_conflict"


def test_transaction_delete_requires_ungrouped_default_state_and_verifies_absence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transaction = SimpleNamespace(
        id=31,
        statement_id=False,
        move_id=SimpleNamespace(id=131),
    )
    existing = {"account.bank.statement.line": {31}, "account.move": {131}}

    def unlink() -> None:
        existing["account.bank.statement.line"].clear()
        existing["account.move"].clear()

    transaction.unlink = unlink

    class Model:
        def __init__(self, model: str) -> None:
            self.model = model

        def search_count(self, domain, **_kwargs):
            record_id = next(value for field, _op, value in domain if field == "id")
            return int(record_id in existing[self.model])

    monkeypatch.setattr(
        writes, "_bank_transaction", lambda *_args, **_kwargs: transaction
    )
    monkeypatch.setattr(writes, "_bank_is_default_unmatched", lambda _record: True)
    monkeypatch.setattr(
        writes,
        "_bank_transaction_result",
        lambda *_args, **_kwargs: {
            **_result("account.bank.statement.line", 31, source_id=131),
            "move_type": "entry",
        },
    )
    monkeypatch.setattr(
        writes, "_scoped", lambda _env, model, _company_id: Model(model)
    )

    result, replay = writes._delete_bank_transaction(
        None, {"transaction_id": 31}, 7, Failure
    )
    assert not replay
    assert result["state"] == "deleted"
    assert result["move_type"] == "entry"
    assert result["source_id"] == 131
    assert not existing["account.bank.statement.line"]
    assert not existing["account.move"]

    transaction.statement_id = SimpleNamespace(id=9)
    with pytest.raises(Failure) as caught:
        writes._delete_bank_transaction(None, {"transaction_id": 31}, 7, Failure)
    assert caught.value.code == "state_conflict"

    transaction.statement_id = False
    monkeypatch.setattr(writes, "_bank_is_default_unmatched", lambda _record: False)
    with pytest.raises(Failure) as caught:
        writes._delete_bank_transaction(None, {"transaction_id": 31}, 7, Failure)
    assert caught.value.code == "state_conflict"
