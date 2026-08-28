from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge import core_writes_runtime as runtime


class Failure(RuntimeError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        exit_code: int,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code
        self.retryable = retryable
        self.details = details or {}


class Records:
    def __init__(self, rows: list[Any] | None = None) -> None:
        self.rows = list(rows or [])

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

    def filtered(self, predicate) -> Records:
        return Records([row for row in self.rows if predicate(row)])


def _payment(**changes: Any) -> SimpleNamespace:
    values = {
        "id": 31,
        "name": False,
        "state": "draft",
        "company_id": SimpleNamespace(id=7),
        "payment_type": "inbound",
        "partner_type": "customer",
        "partner_id": SimpleNamespace(id=8),
        "amount": Decimal("125.50"),
        "currency_id": SimpleNamespace(id=1),
        "journal_id": SimpleNamespace(id=9),
        "payment_method_line_id": SimpleNamespace(id=10),
        "date": "2026-08-26",
        "payment_reference": "INV/42",
        "memo": "payment-create-key",
        "move_id": False,
        "is_reconciled": False,
    }
    values.update(changes)
    payment = SimpleNamespace(**values)

    def write(update: dict[str, Any]) -> bool:
        for field, value in update.items():
            if field == "amount":
                value = Decimal(value)
            if field == "payment_reference" and value is False:
                value = False
            setattr(payment, field, value)
        return True

    def action_draft() -> None:
        payment.state = "draft"
        if payment.move_id:
            payment.move_id.state = "draft"

    payment.write = write
    payment.action_draft = action_draft
    return payment


def _payment_create_parameters() -> dict[str, Any]:
    return {
        "payment_type": "inbound",
        "partner_type": "customer",
        "partner_id": 8,
        "amount": "125.50",
        "currency_id": 1,
        "journal_id": 9,
        "payment_method_line_id": 10,
        "date": "2026-08-26",
        "payment_reference": "INV/42",
    }


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    [
        ("payment.create", _payment_create_parameters()),
        (
            "payment.update_draft",
            {"payment_id": 31, "changes": {"amount": "126"}},
        ),
        ("payment.reset_to_draft", {"payment_id": 31}),
        (
            "bank.transaction.update",
            {"transaction_id": 41, "changes": {"payment_ref": "Updated"}},
        ),
        (
            "bank.transaction.match",
            {"transaction_id": 41, "candidate_line_ids": [51, 52]},
        ),
        ("bank.transaction.unmatch", {"transaction_id": 41}),
        (
            "reconciliation.write_off",
            {
                "transaction_id": 41,
                "write_off_account_id": 61,
                "label": "Bank fee",
                "expected_residual_amount": "-2.5",
            },
        ),
    ],
)
def test_new_write_payloads_use_the_closed_runtime_contract(
    capability_id: str, parameters: dict[str, Any]
) -> None:
    key = runtime._deterministic_key(capability_id, parameters, 7)
    payload = {
        "capability_id": capability_id,
        "company_id": 7,
        "idempotency_key": key or "payment-create-key",
        "confirmation": capability_id,
        "parameters": parameters,
    }

    assert runtime._validated_payload(payload, 7, Failure)[:3] == (
        capability_id,
        payload["idempotency_key"],
        parameters,
    )


def test_payment_create_uses_memo_only_for_the_operation_key(monkeypatch) -> None:
    payment = _payment()
    created: list[dict[str, Any]] = []

    class Model:
        def search(self, *_args, **_kwargs):
            return Records()

        def create(self, values: dict[str, Any]):
            created.append(dict(values))
            return payment

    monkeypatch.setattr(runtime, "_scoped", lambda *_args: Model())
    monkeypatch.setattr(runtime, "_validate_payment_configuration", lambda *_args: None)

    result, replay = runtime._create_payment(
        object(), _payment_create_parameters(), 7, "payment-create-key", Failure
    )

    assert replay is False
    assert result["id"] == 31
    assert created == [
        {
            **_payment_create_parameters(),
            "amount": Decimal("125.50"),
            "company_id": 7,
            "memo": "payment-create-key",
        }
    ]
    assert created[0]["payment_reference"] == "INV/42"


def test_payment_update_replays_target_state_before_enforcing_draft(
    monkeypatch,
) -> None:
    payment = _payment(state="paid")
    monkeypatch.setattr(runtime, "_search_one", lambda *_args, **_kwargs: payment)
    monkeypatch.setattr(runtime, "_validate_payment_configuration", lambda *_args: None)

    result, replay = runtime._update_draft_payment(
        object(), {"payment_id": 31, "changes": {"amount": "125.5"}}, 7, Failure
    )

    assert replay is True
    assert result["state"] == "paid"


def test_payment_reset_calls_the_native_action_and_rejects_rejected(
    monkeypatch,
) -> None:
    move = SimpleNamespace(state="posted", line_ids=Records())
    payment = _payment(state="in_process", move_id=move)
    monkeypatch.setattr(runtime, "_search_one", lambda *_args, **_kwargs: payment)

    result, replay = runtime._reset_payment_to_draft(
        object(), {"payment_id": 31}, 7, Failure
    )

    assert replay is False
    assert result["state"] == "draft"
    payment.state = "rejected"
    with pytest.raises(Failure, match="cannot be reset") as raised:
        runtime._reset_payment_to_draft(object(), {"payment_id": 31}, 7, Failure)
    assert raised.value.code == "state_conflict"


def _transaction(**changes: Any) -> SimpleNamespace:
    values = {
        "id": 41,
        "date": "2026-08-26",
        "amount": Decimal(50),
        "payment_ref": "Deposit",
        "partner_id": SimpleNamespace(id=8),
        "move_id": SimpleNamespace(state="posted"),
        "is_reconciled": False,
    }
    values.update(changes)
    transaction = SimpleNamespace(**values)

    def write(update: dict[str, Any]) -> bool:
        for field, value in update.items():
            setattr(transaction, field, value)
        return True

    transaction.write = write
    return transaction


def test_bank_update_requires_default_unmatched_and_never_writes_business_markers(
    monkeypatch,
) -> None:
    transaction = _transaction()
    monkeypatch.setattr(runtime, "_bank_transaction", lambda *_args: transaction)
    monkeypatch.setattr(runtime, "_bank_is_default_unmatched", lambda *_args: True)
    monkeypatch.setattr(runtime, "_invalidate_bank_transaction", lambda *_args: None)
    monkeypatch.setattr(runtime, "_ensure_ids", lambda *_args: None)
    monkeypatch.setattr(runtime, "_bank_transaction_result", lambda *_args: {"id": 41})

    result, replay = runtime._update_bank_transaction(
        object(),
        {"transaction_id": 41, "changes": {"payment_ref": "Updated"}},
        7,
        Failure,
    )

    assert replay is False
    assert result == {"id": 41}
    assert transaction.payment_ref == "Updated"
    assert not hasattr(transaction, "ref")
    assert not hasattr(transaction, "invoice_origin")


def test_bank_match_uses_only_the_native_fixed_method_and_exact_sources(
    monkeypatch,
) -> None:
    transaction = _transaction(matched_ids=set())
    transaction._get_default_amls_matching_domain = lambda _allow: [("base", "=", True)]
    transaction.set_line_bank_statement_line = lambda ids: (
        transaction.matched_ids.update(ids)
    )
    candidates = SimpleNamespace(ids=[51, 52])
    model = SimpleNamespace(search=lambda *_args, **_kwargs: candidates)
    monkeypatch.setattr(runtime, "_bank_transaction", lambda *_args: transaction)
    monkeypatch.setattr(runtime, "_bank_is_default_unmatched", lambda *_args: True)
    monkeypatch.setattr(runtime, "_invalidate_bank_transaction", lambda *_args: None)
    monkeypatch.setattr(runtime, "_scoped", lambda *_args: model)
    monkeypatch.setattr(
        runtime, "_bank_external_match_ids", lambda row: set(row.matched_ids)
    )
    monkeypatch.setattr(runtime, "_bank_transaction_result", lambda *_args: {"id": 41})

    result, replay = runtime._match_bank_transaction(
        object(),
        {"transaction_id": 41, "candidate_line_ids": [51, 52]},
        7,
        Failure,
    )

    assert replay is False
    assert result == {"id": 41}
    assert transaction.matched_ids == {51, 52}


def test_bank_unmatch_calls_action_undo_reconciliation(monkeypatch) -> None:
    transaction = _transaction(matched=True)

    def undo() -> None:
        transaction.matched = False

    transaction.action_undo_reconciliation = undo
    monkeypatch.setattr(runtime, "_bank_transaction", lambda *_args: transaction)
    monkeypatch.setattr(
        runtime,
        "_bank_external_match_ids",
        lambda row: {51} if row.matched else set(),
    )
    monkeypatch.setattr(
        runtime, "_bank_is_default_unmatched", lambda row: not row.matched
    )
    monkeypatch.setattr(runtime, "_invalidate_bank_transaction", lambda *_args: None)
    monkeypatch.setattr(runtime, "_bank_transaction_result", lambda *_args: {"id": 41})

    _result, replay = runtime._unmatch_bank_transaction(
        object(), {"transaction_id": 41}, 7, Failure
    )

    assert replay is False
    assert transaction.matched is False


def test_write_off_passes_only_account_and_label_to_native_method(monkeypatch) -> None:
    liquidity = Records([SimpleNamespace(id=70)])
    suspense_line = SimpleNamespace(id=71, amount_residual=Decimal("-2.5"))
    suspense = Records([suspense_line])
    other = Records()
    transaction = _transaction(is_reconciled=False)

    def seek():
        return (
            liquidity,
            suspense if not transaction.is_reconciled else Records(),
            other,
        )

    def edit(line_id: int, values: dict[str, Any]) -> None:
        assert line_id == 71
        assert values == {"account_id": 61, "name": "Bank fee"}
        other.rows.append(
            SimpleNamespace(id=72, account_id=SimpleNamespace(id=61), name="Bank fee")
        )
        transaction.is_reconciled = True

    transaction._seek_for_lines = seek
    transaction.edit_reconcile_line = edit
    monkeypatch.setattr(runtime, "_bank_transaction", lambda *_args: transaction)
    monkeypatch.setattr(runtime, "_bank_external_match_ids", lambda *_args: set())
    monkeypatch.setattr(runtime, "_invalidate_bank_transaction", lambda *_args: None)
    monkeypatch.setattr(runtime, "_ensure_ids", lambda *_args: None)
    monkeypatch.setattr(runtime, "_bank_transaction_result", lambda *_args: {"id": 41})

    result, replay = runtime._write_off_bank_transaction(
        object(),
        {
            "transaction_id": 41,
            "write_off_account_id": 61,
            "label": "Bank fee",
            "expected_residual_amount": "-2.5",
        },
        7,
        Failure,
    )

    assert replay is False
    assert result == {"id": 41}
