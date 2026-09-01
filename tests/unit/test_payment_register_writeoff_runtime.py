from __future__ import annotations

import copy
from decimal import Decimal

import pytest
from test_core_writes_runtime import Env, Failure, Records, _payload

from odoo_accounting_cli_v4.bridge import core_writes_runtime as writes


class PaymentEnv(Env):
    def __init__(self):
        super().__init__()
        self.early_discount = False
        self.exchange_account = False
        self.different_currency = False
        self.wrong_difference = False
        self.ignore_writeoff = False

    def new_record(self, model, **values):
        if model == "account.payment.register":
            source = self.models["account.move"].browse(values["active_ids"][0])
            difference = source.amount_residual - Decimal(
                str(values.get("amount", source.amount_residual))
            )
            context = next(
                call[3]
                for call in reversed(self.calls)
                if call[:2] == ("create", model)
            )
            values.update(
                can_edit_wizard=True,
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
                payment_difference=difference + int(self.wrong_difference),
                payment_origin=context.get("default_invoice_origin", False),
            )
            values.setdefault("writeoff_label", "Write-Off")
        return super().new_record(model, **values)

    def register_payment(self, wizard):
        result = super().register_payment(wizard)
        payment = self.models["account.payment"].browse(result["res_id"])
        payment.move_id.records[0].invoice_origin = wizard.payment_origin
        if (
            getattr(wizard, "payment_difference_handling", None) == "reconcile"
            and not self.ignore_writeoff
        ):
            source = self.models["account.move"].browse(wizard.active_ids[0])
            difference = source.amount_residual
            source.records[0].amount_residual = Decimal(0)
            if difference:
                line = self.new_record(
                    "account.move.line",
                    name=wizard.writeoff_label,
                    account_id=self.models["account.account"].browse(
                        wizard.writeoff_account_id
                    ),
                    currency_id=wizard.currency_id,
                    amount_currency=difference
                    if source.move_type in {"out_invoice", "in_refund"}
                    else -difference,
                )
                payment.move_id.records[0].line_ids = Records(
                    self, "account.move.line", [line]
                )
        return result


def case(capability="receivable.payment.register", *, amount="99", move_type=None):
    env = PaymentEnv()
    source = env.existing_move(
        100,
        move_type=move_type
        or (
            "out_invoice"
            if capability == "receivable.payment.register"
            else "in_invoice"
        ),
    )
    parameters = {
        "move_id": source.id,
        "journal_id": env.bank_journal.id,
        "payment_date": "2025-02-04",
        "amount": amount,
        "payment_difference_handling": "reconcile",
        "writeoff_account_id": env.expense.id,
        "writeoff_label": "Payment difference",
    }
    return env, source, _payload(capability, parameters, key="writeoff-operation")


@pytest.mark.parametrize(
    "capability,move_type,sign",
    [
        ("receivable.payment.register", "out_invoice", 1),
        ("receivable.payment.register", "out_refund", -1),
        ("payable.payment.register", "in_invoice", -1),
        ("payable.payment.register", "in_refund", 1),
    ],
)
def test_explicit_writeoff_settles_the_residual_and_replays(
    capability, move_type, sign
):
    env, source, payload = case(capability, move_type=move_type)
    first = writes.dispatch(env, payload, 7, Failure)
    second = writes.dispatch(env, payload, 7, Failure)
    assert source.amount_residual == 0
    assert first["idempotent_replay"] is False
    assert second["idempotent_replay"] is True
    payment = env.models["account.payment"].browse(first["result"]["id"])
    assert payment.amount == Decimal(99)
    assert payment.move_id.line_ids.records[0].amount_currency == sign
    assert payment.memo == payload["idempotency_key"]
    assert payment.move_id.invoice_origin == writes._operation_marker(
        capability, payload["idempotency_key"], payload["parameters"]
    )
    calls = [call for call in env.calls if call[0] == "action_create_payments"]
    assert len(calls) == 1
    values = next(
        call[2]
        for call in env.calls
        if call[:2] == ("create", "account.payment.register")
    )
    assert values["payment_difference_handling"] == "reconcile"
    assert values["writeoff_account_id"] == env.expense.id
    assert values["writeoff_label"] == "Payment difference"
    assert values["installments_mode"] == "full"


@pytest.mark.parametrize("change", ["open", "omit", "account", "label"])
def test_same_key_cannot_change_or_remove_writeoff_parameters(change):
    env, _source, payload = case()
    writes.dispatch(env, payload, 7, Failure)
    modified = copy.deepcopy(payload)
    parameters = modified["parameters"]
    if change in {"open", "omit"}:
        parameters.pop("writeoff_account_id")
        parameters.pop("writeoff_label")
        if change == "omit":
            parameters.pop("payment_difference_handling")
        else:
            parameters["payment_difference_handling"] = "open"
    elif change == "account":
        parameters["writeoff_account_id"] = env.income.id
    else:
        parameters["writeoff_label"] = "Changed label"
    with pytest.raises(Failure, match="idempotency") as caught:
        writes.dispatch(env, modified, 7, Failure)
    assert caught.value.code == "idempotency_conflict"
    assert len([call for call in env.calls if call[0] == "action_create_payments"]) == 1


@pytest.mark.parametrize(
    "capability,move_type",
    [
        ("receivable.payment.register", "out_refund"),
        ("payable.payment.register", "in_refund"),
    ],
)
def test_refund_writeoff_rejects_reversed_native_sign(
    capability, move_type, monkeypatch
):
    env, _source, payload = case(capability, move_type=move_type)
    original_register = env.register_payment

    def wrong_sign(wizard):
        result = original_register(wizard)
        payment = env.models["account.payment"].browse(result["res_id"])
        line = payment.move_id.line_ids.records[0]
        line.amount_currency = -line.amount_currency
        return result

    monkeypatch.setattr(env, "register_payment", wrong_sign)
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, payload, 7, Failure)
    assert caught.value.code == "odoo_write_error"


@pytest.mark.parametrize("unavailable", ["missing", "foreign", "inactive"])
def test_writeoff_account_must_be_visible_and_active_in_the_company(unavailable):
    env, _source, payload = case()
    if unavailable == "missing":
        payload["parameters"]["writeoff_account_id"] = 999
    elif unavailable == "foreign":
        env.expense.company_ids = Records(env, "res.company")
    else:
        env.expense.active = False
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, payload, 7, Failure)
    assert caught.value.code == "record_not_found"
    assert not any(call[0] == "create" for call in env.calls)


def test_account_read_acl_is_required():
    env, _source, payload = case()
    env.denied_access = ("account.account", "read")
    result = writes.dispatch(env, payload, 7, Failure)
    assert result["access_allowed"] is False
    assert not any(call[0] == "create" for call in env.calls)


@pytest.mark.parametrize(
    "flag",
    ["early_discount", "exchange_account", "different_currency", "wrong_difference"],
)
def test_native_routes_must_not_ignore_explicit_writeoff_semantics(flag):
    env, source, payload = case()
    setattr(env, flag, True)
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, payload, 7, Failure)
    assert caught.value.code == "state_conflict"
    assert source.amount_residual == Decimal(100)
    assert not any(call[0] == "action_create_payments" for call in env.calls)


def test_native_result_must_actually_close_the_source():
    env, _source, payload = case()
    env.ignore_writeoff = True
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, payload, 7, Failure)
    assert caught.value.code == "odoo_write_error"


def test_full_amount_needs_no_nonzero_writeoff_line():
    env, source, payload = case(amount="100")
    assert writes.dispatch(env, payload, 7, Failure)["idempotent_replay"] is False
    assert source.amount_residual == 0
    assert writes.dispatch(env, payload, 7, Failure)["idempotent_replay"] is True


@pytest.mark.parametrize("amount", [None, "99"])
def test_explicit_open_keeps_the_unpaid_balance_and_replays(amount):
    env, source, payload = case()
    payload["parameters"]["payment_difference_handling"] = "open"
    payload["parameters"].pop("writeoff_account_id")
    payload["parameters"].pop("writeoff_label")
    if amount is None:
        payload["parameters"].pop("amount")
        payload["idempotency_key"] = f"receivable.payment.register:{source.id}"
    first = writes.dispatch(env, payload, 7, Failure)
    assert source.amount_residual == (0 if amount is None else 1)
    payment = env.models["account.payment"].browse(first["result"]["id"])
    assert payment.move_id.invoice_origin == writes._operation_marker(
        payload["capability_id"], payload["idempotency_key"], payload["parameters"]
    )
    assert writes.dispatch(env, payload, 7, Failure)["idempotent_replay"] is True
    assert len([call for call in env.calls if call[0] == "action_create_payments"]) == 1


def test_omitted_label_uses_the_native_wizard_label():
    env, _source, payload = case()
    payload["parameters"].pop("writeoff_label")
    result = writes.dispatch(env, payload, 7, Failure)
    payment = env.models["account.payment"].browse(result["result"]["id"])
    assert payment.move_id.line_ids.records[0].name == "Write-Off"


@pytest.mark.parametrize("field", ["account", "label", "amount", "currency", "marker"])
def test_native_payment_must_preserve_the_requested_writeoff(field, monkeypatch):
    env, _source, payload = case()
    original_register = env.register_payment

    def corrupt_result(wizard):
        result = original_register(wizard)
        payment = env.models["account.payment"].browse(result["res_id"])
        line = payment.move_id.line_ids.records[0]
        if field == "account":
            line.account_id = env.models["account.account"].browse(env.income.id)
        elif field == "label":
            line.name = "Wrong label"
        elif field == "amount":
            line.amount_currency = Decimal(2)
        elif field == "currency":
            line.currency_id = Records(env, "res.currency", [env.foreign_currency])
        else:
            payment.move_id.records[0].invoice_origin = False
        return result

    monkeypatch.setattr(env, "register_payment", corrupt_result)
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, payload, 7, Failure)
    assert caught.value.code == "odoo_write_error"


@pytest.mark.parametrize("handling", [None, [], "invalid"])
def test_invalid_explicit_mode_is_rejected_before_native_execution(handling):
    env, _source, payload = case()
    payload["parameters"]["payment_difference_handling"] = handling
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, payload, 7, Failure)
    assert caught.value.code == "bridge_protocol_error"
    assert not any(call[0] == "create" for call in env.calls)


@pytest.mark.parametrize("amount", [None, "99"])
def test_legacy_request_does_not_change_native_defaults_or_add_a_marker(amount):
    env, source, payload = case()
    env.early_discount = True
    for field in (
        "payment_difference_handling",
        "writeoff_account_id",
        "writeoff_label",
    ):
        payload["parameters"].pop(field)
    if amount is None:
        payload["parameters"].pop("amount")
        payload["idempotency_key"] = f"receivable.payment.register:{source.id}"
    first = writes.dispatch(env, payload, 7, Failure)
    values = next(
        call[2]
        for call in env.calls
        if call[:2] == ("create", "account.payment.register")
    )
    assert values.get("payment_difference_handling") == (
        "open" if amount is not None else None
    )
    assert "installments_mode" not in values
    payment = env.models["account.payment"].browse(first["result"]["id"])
    assert payment.move_id.invoice_origin is False
    assert writes.dispatch(env, payload, 7, Failure)["idempotent_replay"] is True
