from __future__ import annotations

from decimal import Decimal

import pytest
from test_core_writes_runtime import Env, Failure, Records, _payload

from odoo_accounting_cli_v4.bridge import core_writes_runtime as writes
from odoo_accounting_cli_v4.capabilities.core_writes import _expected_idempotency_key


class BatchPaymentEnv(Env):
    def __init__(self) -> None:
        super().__init__()
        self.batch_count = 1
        self.can_edit = True
        self.can_group = True
        self.early_discount = False
        self.exchange_account = False
        self.wrong_difference = False
        self.different_currency = False
        self.payment_count = 1
        self.omit_source_id: int | None = None
        self.keep_residual = False

    def new_record(self, model, **values):
        if model == "account.payment.register":
            sources = self.models["account.move"].browse(values["active_ids"])
            context = next(
                call[3]
                for call in reversed(self.calls)
                if call[:2] == ("create", model)
            )
            total = sum(source.amount_residual for source in sources)
            values.update(
                batches=[object() for _unused in range(self.batch_count)],
                can_edit_wizard=self.can_edit,
                can_group_payments=self.can_group,
                early_payment_discount_mode=self.early_discount,
                writeoff_is_exchange_account=self.exchange_account,
                currency_id=Records(
                    self,
                    "res.currency",
                    [
                        self.foreign_currency
                        if self.different_currency
                        else self.currency
                    ],
                ),
                amount=total,
                payment_difference=Decimal(int(self.wrong_difference)),
                payment_origin=context["default_invoice_origin"],
            )
        return super().new_record(model, **values)

    def register_payment(self, wizard):
        sources = self.models["account.move"].browse(wizard.active_ids)
        linked = sources.filtered(lambda move: move.id != self.omit_source_id)
        first = next(iter(sources))
        total = sum(source.amount_residual for source in sources)
        first_payment_id = None
        for index in range(self.payment_count):
            payment_move = self.existing_move(
                self._next_id + 1, move_type="entry", state="posted", residual="0"
            )
            self._next_id = payment_move.id
            payment_move.invoice_origin = wizard.payment_origin
            payment = self.add(
                "account.payment",
                self._next_id + 1,
                name=f"PAY/BATCH/{index}",
                state="in_process",
                company_id=self.company,
                memo=wizard.communication,
                journal_id=self.models["account.journal"].browse(wizard.journal_id),
                date=wizard.payment_date,
                amount=total,
                payment_type=(
                    "inbound" if first.move_type == "out_invoice" else "outbound"
                ),
                partner_type=(
                    "customer" if first.move_type == "out_invoice" else "supplier"
                ),
                move_id=Records(self, "account.move", [payment_move]),
                reconciled_invoice_ids=(
                    linked
                    if first.move_type == "out_invoice"
                    else Records(self, "account.move")
                ),
                reconciled_bill_ids=(
                    linked
                    if first.move_type == "in_invoice"
                    else Records(self, "account.move")
                ),
                is_reconciled=True,
            )
            self._next_id = payment.id
            first_payment_id = first_payment_id or payment.id
        if not self.keep_residual:
            for source in sources:
                source.amount_residual = Decimal(0)
        self.calls.append(("action_create_payments_many", tuple(wizard.active_ids)))
        return {"res_id": first_payment_id}


def case(capability="receivable.payment.register"):
    env = BatchPaymentEnv()
    move_type = (
        "out_invoice" if capability == "receivable.payment.register" else "in_invoice"
    )
    first = env.existing_move(100, move_type=move_type, residual="40")
    second = env.existing_move(101, move_type=move_type, residual="60")
    parameters = {
        "move_ids": [first.id, second.id],
        "journal_id": env.bank_journal.id,
        "payment_date": "2025-02-04",
    }
    key = writes._deterministic_key(capability, parameters, 7)
    assert key == _expected_idempotency_key(capability, parameters, 7)
    return env, (first, second), _payload(capability, parameters, key=key)


@pytest.mark.parametrize(
    "capability",
    ["receivable.payment.register", "payable.payment.register"],
)
def test_many_register_creates_one_full_payment_and_replays(capability):
    env, sources, payload = case(capability)
    first = writes.dispatch(env, payload, 7, Failure)
    second = writes.dispatch(env, payload, 7, Failure)

    assert first["idempotent_replay"] is False
    assert first["result"]["source_id"] is None
    assert second["idempotent_replay"] is True
    payment = env.models["account.payment"].browse(first["result"]["id"])
    assert payment.amount == Decimal(100)
    assert writes._payment_sources(payment) == {100, 101}
    assert all(source.amount_residual == 0 for source in sources)
    assert payment.move_id.invoice_origin == writes._operation_marker(
        capability, payload["idempotency_key"], payload["parameters"]
    )
    assert [call[0] for call in env.calls].count("action_create_payments_many") == 1
    values = next(
        call[2]
        for call in env.calls
        if call[:2] == ("create", "account.payment.register")
    )
    assert values["installments_mode"] == "full"
    assert values["group_payment"] is True


def test_many_register_rejects_unbound_key_before_odoo_access():
    env, _sources, payload = case()
    payload["idempotency_key"] = "batch-key"
    calls_before = list(env.calls)
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, payload, 7, Failure)
    assert caught.value.code == "bridge_protocol_error"
    assert env.calls == calls_before


@pytest.mark.parametrize("mismatch", ["partner", "currency", "type"])
def test_many_register_rejects_incompatible_sources(mismatch):
    env, sources, payload = case()
    if mismatch == "partner":
        other = env.add("res.partner", 21, name="Other", company_id=False)
        sources[1].partner_id = Records(env, "res.partner", [other])
    elif mismatch == "currency":
        sources[1].currency_id = Records(env, "res.currency", [env.foreign_currency])
    else:
        sources[1].move_type = "out_refund"
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, payload, 7, Failure)
    assert caught.value.code in {"record_not_found", "state_conflict"}
    assert not any(call[0] == "action_create_payments_many" for call in env.calls)


@pytest.mark.parametrize(
    "flag",
    [
        "batch_count",
        "can_edit",
        "can_group",
        "early_discount",
        "exchange_account",
        "wrong_difference",
        "different_currency",
    ],
)
def test_many_register_rejects_native_routes_that_cannot_merge_fully(flag):
    env, _sources, payload = case()
    value = 2 if flag == "batch_count" else flag not in {"can_edit", "can_group"}
    setattr(env, flag, value)
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, payload, 7, Failure)
    assert caught.value.code == "state_conflict"
    assert not any(call[0] == "action_create_payments_many" for call in env.calls)


def test_many_register_rejects_missing_or_duplicate_source_ids():
    env, _sources, payload = case()
    payload["parameters"]["move_ids"] = [100, 999]
    payload["idempotency_key"] = writes._deterministic_key(
        payload["capability_id"], payload["parameters"], 7
    )
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, payload, 7, Failure)
    assert caught.value.code == "record_not_found"

    env, _sources, payload = case()
    payload["parameters"]["move_ids"] = [100, 100]
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, payload, 7, Failure)
    assert caught.value.code == "bridge_protocol_error"

    env, _sources, payload = case()
    payload["parameters"]["move_ids"] = [101, 100]
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, payload, 7, Failure)
    assert caught.value.code == "bridge_protocol_error"


def test_many_register_replay_rejects_changed_parameters_or_source_graph():
    env, _sources, payload = case()
    writes.dispatch(env, payload, 7, Failure)
    payment = env.models["account.payment"].search(
        [("memo", "=", payload["idempotency_key"])]
    )
    payment.move_id.records[0].invoice_origin = "ODACV4:wrong"
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, payload, 7, Failure)
    assert caught.value.code == "idempotency_conflict"

    payment.move_id.records[0].invoice_origin = writes._operation_marker(
        payload["capability_id"], payload["idempotency_key"], payload["parameters"]
    )
    payment.records[0].reconciled_invoice_ids = env.models["account.move"].browse(100)
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, payload, 7, Failure)
    assert caught.value.code == "idempotency_conflict"


@pytest.mark.parametrize(
    "defect", ["multiple_payments", "missing_source", "open_residual"]
)
def test_many_register_rejects_invalid_native_results(defect):
    env, _sources, payload = case()
    if defect == "multiple_payments":
        env.payment_count = 2
    elif defect == "missing_source":
        env.omit_source_id = 101
    else:
        env.keep_residual = True
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, payload, 7, Failure)
    assert caught.value.code == "odoo_write_error"
