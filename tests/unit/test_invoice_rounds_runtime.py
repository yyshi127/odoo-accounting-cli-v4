from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest
from test_core_writes_runtime import Env, Failure, Records, _payload

from odoo_accounting_cli_v4.bridge import core_writes_runtime as writes


@pytest.mark.parametrize("capability", ["customer_credit_note.create", "vendor_refund.create"])
def test_refund_array_contract_preserves_single_lines_and_binds_sorted_sources(capability):
    assert writes._valid_parameters(capability, {"move_ids": [1, 2], "date": "2026-10-02", "reason": "Full"}, 7)
    for ids in ([1], [2, 1], [1, 1], [True, 2], list(range(1, 102))):
        assert not writes._valid_parameters(capability, {"move_ids": ids, "date": "2026-10-02", "reason": "Full"}, 7)
    assert not writes._valid_parameters(capability, {"move_ids": [1, 2], "move_id": 1, "date": "2026-10-02", "reason": "Full"}, 7)
    assert not writes._valid_parameters(capability, {"move_ids": [1, 2], "lines": [], "date": "2026-10-02", "reason": "Full"}, 7)


@pytest.mark.parametrize("capability", ["receivable.payment.register", "payable.payment.register"])
def test_installment_contract_uses_caller_keys_only_for_explicit_new_paths(capability):
    legacy = {"move_id": 1, "journal_id": 2, "payment_date": "2026-10-02"}
    assert writes._deterministic_key(capability, legacy, 7) == f"{capability}:1"
    for extension in ({"installments_mode": "next"}, {"group_payment": False}, {"installments_mode": "before_date", "installment_cutoff_date": "2026-10-15"}):
        params = {**legacy, **extension}
        assert writes._valid_parameters(capability, params, 7)
        assert writes._deterministic_key(capability, params, 7) is None
    many = {"move_ids": [1, 2], "journal_id": 2, "payment_date": "2026-10-02"}
    assert writes._deterministic_key(capability, many, 7) is not None
    for extension in ({"amount": "30"}, {"payment_difference_handling": "open"}):
        params = {**many, **extension}
        assert writes._valid_parameters(capability, params, 7)
        assert writes._deterministic_key(capability, params, 7) is None
    for extension in ({"installments_mode": "before_date"}, {"installment_cutoff_date": "2026-10-15"}, {"group_payment": 0}, {"installments_mode": []}, {"group_payment": False, "amount": "20"}):
        assert not writes._valid_parameters(capability, {**legacy, **extension}, 7)


@pytest.mark.parametrize("capability", ["sale.order.invoice.create", "purchase.order.bill.create"])
def test_new_order_arrays_allow_one_selected_order_without_changing_legacy_key(capability):
    assert writes._valid_parameters(capability, {"order_ids": [1]}, 7)
    assert writes._deterministic_key(capability, {"order_ids": [1]}, 7) is None
    assert writes._deterministic_key(capability, {"order_id": 1}, 7) == f"{capability}:1"
    assert not writes._valid_parameters(capability, {"order_id": 1, "order_ids": [1]}, 7)


def test_down_payment_and_policy_contracts_are_closed_and_nonnullable():
    capability = "sale.order.down_payment.create"
    for method, amount in (("fixed", "200"), ("percentage", "100")):
        params = {"order_id": 1, "method": method, "amount": amount}
        assert writes._valid_parameters(capability, params, 7)
        assert writes._deterministic_key(capability, params, 7) is None
    for method, amount in (("percentage", "101"), ("fixed", "0"), ("other", "1"), ("fixed", "1.0")):
        assert not writes._valid_parameters(capability, {"order_id": 1, "method": method, "amount": amount}, 7)
    for field, choices in writes._PRODUCT_POLICY_FIELDS.items():
        for value in choices:
            assert writes._valid_parameters("product.accounting_profile.update", {"product_id": 1, "changes": {field: value}}, 7)
            assert not writes._valid_parameters("product.update", {"product_id": 1, "changes": {field: value}}, 7)
        for value in (None, "unknown", []):
            assert not writes._valid_parameters("product.accounting_profile.update", {"product_id": 1, "changes": {field: value}}, 7)


class NativePaymentWizard:
    def __init__(self, fixture, values, context):
        self.fixture = fixture
        self.context = context
        self.currency_id = Records(fixture.env, "res.currency", [fixture.env.currency])
        self.can_edit_wizard = fixture.editable
        self.group_payment = values["group_payment"]
        self.line_ids = fixture.terms.filtered(lambda line: line.move_id.id in context["active_ids"])
        self.batches = [{"lines": self.line_ids, "payment_values": {"payment_type": fixture.direction}}]
        self.early_payment_discount_mode = False
        self.writeoff_is_exchange_account = False
        self.previews = []
        self.amount = Decimal(40)
        self.installments_mode = fixture.offered_mode

    def _get_total_amounts_to_pay(self, batches):
        selected = self.line_ids.filtered(lambda line: line.id in {110, 112})
        return {"amount_by_default": sum(abs(line.amount_residual_currency) for line in selected),
                "full_amount": sum(abs(line.amount_residual_currency) for line in self.line_ids),
                "installment_mode": self.fixture.offered_mode, "lines": selected,
                "amount_for_difference": 40, "full_amount_for_difference": 200}

    def write(self, values):
        self.fixture.wizard_writes.append(values)
        for field, value in values.items():
            setattr(self, field, value)
        self.payment_difference = 200 - Decimal(str(self.amount))

    def _create_payment_vals_from_wizard(self, batch):
        values = self.fixture.payment_values(self.amount, self.communication)
        if self.fixture.parameters.get("payment_difference_handling") == "reconcile":
            values["write_off_line_vals"] = [{"account_id": self.writeoff_account_id, "name": self.writeoff_label,
                                               "currency_id": self.currency_id.id, "amount_currency": self.payment_difference}]
        self.previews.append((values, set(batch["lines"].move_id.ids)))
        return values

    def _create_payment_vals_from_batch(self, batch):
        line = next(iter(batch["lines"]))
        values = self.fixture.payment_values(abs(line.amount_residual_currency), f"native term {line.id}")
        self.previews.append((values, {line.move_id.id}))
        return values

    def _create_payments(self):
        self.fixture.creation_count += 1
        rows = []
        for values, source_ids in self.previews:
            move = self.fixture.env.existing_move(self.fixture.env._next_id + 1, move_type="entry", residual="0")
            self.fixture.env._next_id = move.id
            move.invoice_origin = self.context["default_invoice_origin"]
            for writeoff in values.get("write_off_line_vals", []):
                if self.fixture.defect != "writeoff":
                    line = self.fixture.env.add("account.move.line", self.fixture.env._next_id + 1,
                                                account_id=self.fixture.env.models["account.account"].browse(writeoff["account_id"]),
                                                name=writeoff["name"], currency_id=self.currency_id, amount_currency=writeoff["amount_currency"])
                    self.fixture.env._next_id = line.id
                    move.line_ids = Records(self.fixture.env, "account.move.line", [line])
            linked = self.fixture.env.models["account.move"].browse(sorted(source_ids))
            if self.fixture.partial_subset:
                linked = linked.filtered(lambda source: source.id == 100)
            if self.fixture.defect == "source":
                linked = Records(self.fixture.env, "account.move")
            counterpart = self.fixture.env.reconciliation_line(
                self.fixture.env._next_id + 1, "0", account=self.fixture.payment_account,
            )
            self.fixture.env._next_id = counterpart.id
            counterpart.move_id = Records(self.fixture.env, "account.move", [move])
            move.line_ids |= Records(self.fixture.env, "account.move.line", [counterpart])
            for source in linked:
                source_line = next(iter(self.fixture.terms.filtered(lambda line, source_id=source.id: line.move_id.id == source_id)))
                partial = self.fixture.env.add(
                    "account.partial.reconcile", self.fixture.env._next_id + 1,
                    debit_move_id=source_line if self.fixture.direction == "inbound" else counterpart,
                    credit_move_id=counterpart if self.fixture.direction == "inbound" else source_line,
                )
                self.fixture.env._next_id = partial.id
                field = "matched_debit_ids" if self.fixture.direction == "inbound" else "matched_credit_ids"
                setattr(counterpart, field, getattr(counterpart, field) | Records(self.fixture.env, "account.partial.reconcile", [partial]))
            row = self.fixture.env.add(
                "account.payment", self.fixture.env._next_id + 1, name="PAY/native", state="in_process",
                company_id=self.fixture.env.company, memo=values["memo"], date="2026-10-02",
                journal_id=self.fixture.env.models["account.journal"].browse(self.fixture.env.bank_journal.id),
                currency_id=self.currency_id, amount=Decimal(str(values["amount"])) + int(self.fixture.defect == "amount"),
                payment_type=self.fixture.direction, move_id=Records(self.fixture.env, "account.move", [move]),
                reconciled_invoice_ids=linked if self.fixture.receivable else Records(self.fixture.env, "account.move"),
                reconciled_bill_ids=Records(self.fixture.env, "account.move") if self.fixture.receivable else linked,
                is_reconciled=False,
            )
            self.fixture.env._next_id = row.id
            rows.append(row)
        return Records(self.fixture.env, "account.payment", rows)


class PaymentFixture:
    def __init__(self, monkeypatch, *, receivable=True, refund=False):
        self.env = Env()
        self.receivable = receivable
        self.payment_account = self.env.receivable if receivable else self.env.account(302, reconcile=True, account_type="liability_payable")
        self.direction = "inbound" if receivable != refund else "outbound"
        move_type = ("out_" if receivable else "in_") + ("refund" if refund else "invoice")
        self.sources = Records(self.env, "account.move", [self.env.existing_move(record_id, move_type=move_type, residual="100") for record_id in (100, 101)])
        terms = []
        for index, source in enumerate(self.sources):
            for offset, amount in enumerate((20, 80)):
                terms.append(self.env.add("account.move.line", 110 + index * 2 + offset,
                                         move_id=Records(self.env, "account.move", [source]), amount_residual_currency=Decimal(amount),
                                         balance=amount if self.direction == "inbound" else -amount))
        self.terms = Records(self.env, "account.move.line", terms)
        self.editable = True
        self.offered_mode = "next"
        self.partial_subset = False
        self.defect = None
        self.creation_count = 0
        self.wizard_writes = []
        self.contexts = []
        self.capability = "receivable.payment.register" if receivable else "payable.payment.register"
        self.parameters = {"move_ids": [100, 101], "journal_id": self.env.bank_journal.id, "payment_date": "2026-10-02", "installments_mode": "next"}
        original_scoped = writes._scoped
        fixture = self

        class WizardModel:
            def with_context(self, **context):
                fixture.contexts.append(context)
                self.context = context
                return self

            def create(self, values):
                fixture.wizard = NativePaymentWizard(fixture, values, self.context)
                return fixture.wizard

        monkeypatch.setattr(writes, "_scoped", lambda env, model, company: WizardModel() if model == "account.payment.register" else original_scoped(env, model, company))

    def payment_values(self, amount, memo):
        return {"amount": amount, "memo": memo, "currency_id": self.env.currency.id,
                "payment_method_line_id": False, "partner_bank_id": False}

    def execute(self, key="round-key-0001"):
        return writes._register_payment_round(self.env, self.capability, self.parameters, 7, key, Failure)


@pytest.mark.parametrize("receivable,refund", [(True, False), (False, False), (True, True), (False, True)])
def test_native_installment_payment_amount_direction_and_key_replay(monkeypatch, receivable, refund):
    fixture = PaymentFixture(monkeypatch, receivable=receivable, refund=refund)
    result, replay = fixture.execute()
    assert not replay and result["source_id"] is None
    assert fixture.wizard.amount == 40
    assert fixture.execute()[1] is True
    assert fixture.creation_count == 1
    assert all(not any(term[0] == "memo" for term in call[2] if isinstance(term, tuple))
               for call in fixture.env.calls if call[:2] == ("search", "account.payment"))
    fixture.parameters["installments_mode"] = "full"
    with pytest.raises(Failure, match="other parameters") as caught:
        fixture.execute()
    assert caught.value.code == "idempotency_conflict"


def test_native_ungrouped_terms_keep_native_communication_and_support_one_item_batches(monkeypatch):
    fixture = PaymentFixture(monkeypatch)
    fixture.parameters["group_payment"] = False
    result, replay = fixture.execute()
    assert not replay and result["processed_count"] == 2
    assert [item["source_id"] for item in result["items"]] == [100, 101]
    assert fixture.wizard_writes == [{"installments_mode": "next"}]
    payments = fixture.env.models["account.payment"].browse([item["id"] for item in result["items"]])
    assert [payment.memo for payment in payments] == ["native term 110", "native term 112"]
    assert fixture.execute()[1] is True

    fixture.parameters["move_ids"] = [100, 101]
    fixture.wizard._get_total_amounts_to_pay = lambda batches: None  # Replay must not consult the wizard.
    assert fixture.execute()[0]["processed_count"] == 2

    fixture = PaymentFixture(monkeypatch)
    fixture.parameters.pop("move_ids")
    fixture.parameters.update(move_id=100, group_payment=False)
    result, replay = fixture.execute()
    assert not replay and result["processed_count"] == 1
    assert result["items"][0]["source_id"] == 100


def test_cutoff_is_native_active_domain_and_mode_mismatch_is_honest(monkeypatch):
    fixture = PaymentFixture(monkeypatch)
    fixture.offered_mode = "before_date"
    fixture.parameters.update(installments_mode="before_date", installment_cutoff_date="2026-10-15")
    fixture.execute()
    assert fixture.contexts[0]["active_domain"] == [("next_payment_date", "<=", "2026-10-15")]
    assert "installment_cutoff_date" not in fixture.wizard_writes[0]

    fixture = PaymentFixture(monkeypatch)
    fixture.parameters["installments_mode"] = "overdue"
    with pytest.raises(Failure) as caught:
        fixture.execute()
    assert caught.value.code == "state_conflict" and fixture.creation_count == 0


def test_grouped_partial_many_does_not_require_all_sources_or_zero_residual(monkeypatch):
    fixture = PaymentFixture(monkeypatch)
    fixture.parameters.update(installments_mode="full", amount="25")
    fixture.partial_subset = True
    result, replay = fixture.execute()
    assert not replay and result["reconciled"] is False
    assert all(source.amount_residual == 100 for source in fixture.sources)
    assert fixture.wizard.amount == 25


@pytest.mark.parametrize("receivable,refund", [(True, False), (False, False), (True, True), (False, True)])
def test_grouped_partial_source_is_stable_when_native_informational_fields_expand(monkeypatch, receivable, refund):
    fixture = PaymentFixture(monkeypatch, receivable=receivable, refund=refund)
    fixture.parameters.update(installments_mode="full", amount="50")
    fixture.partial_subset = True
    first, replay = fixture.execute()
    assert not replay and first["source_id"] == 100
    payment = fixture.env.models["account.payment"].browse(first["id"])
    # Native invoice_ids/stat-button fields can include every wizard source after
    # deferred M2M writes flush, even though the real partial graph links only one.
    field = "reconciled_invoice_ids" if receivable else "reconciled_bill_ids"
    setattr(payment.records[0], field, fixture.sources)
    assert writes._payment_sources(payment) == {100, 101}
    assert writes._round_payment_sources(payment) == {100}
    second, replay = fixture.execute()
    assert replay and second == first


@pytest.mark.parametrize("defect", ["amount", "source"])
def test_created_payments_are_verified_against_native_values_and_source_graph(monkeypatch, defect):
    fixture = PaymentFixture(monkeypatch)
    fixture.defect = defect
    with pytest.raises(Failure) as caught:
        fixture.execute()
    assert caught.value.code == "odoo_write_error"


def test_noneditable_routes_reject_explicit_amount_and_bank_before_creation(monkeypatch):
    fixture = PaymentFixture(monkeypatch)
    fixture.parameters.update(group_payment=False, amount="40")
    with pytest.raises(Failure) as caught:
        fixture.execute()
    assert caught.value.code == "state_conflict" and fixture.creation_count == 0
    wizard = SimpleNamespace(can_edit_wizard=True, group_payment=False, batches=[{"lines": fixture.terms}])
    with pytest.raises(Failure) as caught:
        writes._validate_register_wizard_references(wizard, {"partner_bank_id": 99}, "inbound", Failure)
    assert caught.value.code == "state_conflict"


@pytest.mark.parametrize("capability,source_type,refund_type", [
    ("customer_credit_note.create", "out_invoice", "out_refund"),
    ("vendor_refund.create", "in_invoice", "in_refund"),
])
def test_full_refund_native_batch_helper_and_global_operation_key_replay(monkeypatch, capability, source_type, refund_type):
    env = Env()
    sources = [env.existing_move(record_id, move_type=source_type) for record_id in (100, 101, 102)]
    for source in sources:
        source.amount_total = Decimal(100)
    sources[1].journal_id = Records(env, "account.journal", [env.add(
        "account.journal", 61, name="Second source journal", company_id=env.company,
        active=True, type="sale" if source_type == "out_invoice" else "purchase",
    )])
    calls = []
    original_scoped = writes._scoped

    class Reversal:
        def with_context(self, **context):
            self.context = context
            return self

        def create(self, values):
            assert set(values) == {"move_ids", "journal_id", "date", "reason"}
            assert values["move_ids"] == [(6, 0, self.context["active_ids"])]
            assert len(self.context["active_ids"]) == 1
            source = env.models["account.move"].browse(self.context["active_ids"])
            assert values["journal_id"] == source.journal_id.id
            self.values = values
            return self

        def refund_moves(self):
            calls.append((self.context, self.values))
            rows = []
            for source_id in self.context["active_ids"]:
                refund = env.existing_move(1000 + source_id, move_type=refund_type, state="draft")
                refund.reversed_entry_id = env.models["account.move"].browse(source_id)
                refund.amount_total = Decimal(100)
                refund.date = self.values["date"]
                refund.journal_id = env.models["account.journal"].browse(self.values["journal_id"])
                rows.append(refund)
            self.new_move_ids = Records(env, "account.move", rows)

    monkeypatch.setattr(writes, "_scoped", lambda current, model, company: Reversal() if model == "account.move.reversal" else original_scoped(current, model, company))
    parameters = {"move_ids": [100, 101], "date": "2026-10-02", "reason": "Return all"}
    execute = lambda: writes._create_refund_round(env, capability, parameters, 7, "refund-round-key", "ODACV4:parameters", Failure)
    result, replay = execute()
    assert not replay and result["processed_count"] == 2
    assert {item["source_id"] for item in result["items"]} == {100, 101}
    assert calls == [({"active_model": "account.move", "active_ids": [source.id]}, {
        "move_ids": [(6, 0, [source.id])], "journal_id": source.journal_id.id,
        "date": "2026-10-02", "reason": "Return all",
    }) for source in sources[:2]]
    assert execute()[1] is True
    parameters["move_ids"] = [100, 102]
    with pytest.raises(Failure) as caught:
        execute()
    assert caught.value.code == "idempotency_conflict" and len(calls) == 2


@pytest.mark.parametrize("sale,refund,combo", [(True, False, False), (True, True, False), (False, False, False), (False, True, False), (True, False, True), (True, True, True)])
def test_source_order_round_uses_native_grouping_and_current_quantities_after_history(monkeypatch, sale, refund, combo):
    env = Env()
    model = "sale.order" if sale else "purchase.order"
    line_model = "sale.order.line" if sale else "purchase.order.line"
    calls = []
    source = env.add(model, 100, name="ORDER/100", company_id=env.company, state="sale" if sale else "purchase", invoice_status="to invoice")
    line = env.add(line_model, 110, order_id=Records(env, model, [source]), display_type=False, is_downpayment=False,
                   qty_to_invoice=Decimal(-2 if refund else 2), product_qty=Decimal(10), product_uom_qty=Decimal(10))
    source.order_line = Records(env, line_model, [line])
    if combo:
        line.product_id = Records(env, "product.product", [env.add("product.product", 66, type="combo")])
    source._get_invoiceable_lines = lambda final: source.order_line
    history = env.existing_move(500, move_type="out_invoice" if sale else "in_invoice", state="posted")
    history.invoice_origin = "previous native invoice"
    setattr(history, "invoice_line_ids.purchase_line_id.order_id", [100])

    def create_native(**options):
        calls.append(options)
        move = env.existing_move(600, move_type=("out_" if sale else "in_") + ("refund" if refund else "invoice"), state="draft")
        move.invoice_origin = source.name
        row = env.add("account.move.line", 610, display_type="line_section" if combo else "product", quantity=line.qty_to_invoice if combo else Decimal(2),
                      sale_line_ids=source.order_line if sale else Records(env, "sale.order.line"),
                      purchase_line_id=Records(env, "purchase.order.line") if sale else source.order_line)
        move.invoice_line_ids = Records(env, "account.move.line", [row])
        move.write = lambda values: Records(env, "account.move", [move]).write(values)
        setattr(move, "invoice_line_ids.purchase_line_id.order_id", [100])
        return Records(env, "account.move", [move])

    source._create_invoices = create_native

    class OrderRecords(Records):
        def _create_invoices(self, **options):
            return create_native(**options)

        def action_create_invoice(self):
            create_native(native_purchase=True)

    original_ensure = writes._ensure_ids
    monkeypatch.setattr(writes, "_ensure_ids", lambda current, name, ids, domain, company, failure:
                        OrderRecords(env, model, [source]) if name == model else original_ensure(current, name, ids, domain, company, failure))
    capability = "sale.order.invoice.create" if sale else "purchase.order.bill.create"
    parameters = {"order_ids": [100]}
    if sale:
        parameters.update(consolidated_billing=False, deduct_down_payments=True)
    execute = lambda: writes._order_invoice_round(env, capability, parameters, 7, "order-round-key", Failure)
    result, replay = execute()
    assert not replay and result["processed_count"] == 1 and result["items"][0]["id"] == 600
    assert result["items"][0]["source_id"] == 100
    assert calls == [{"grouped": True, "final": True} if sale else {"native_purchase": True}]
    assert execute()[1] is True and len(calls) == 1
    assert history.invoice_origin == "previous native invoice"
    assert env.models["account.move"].browse(600).invoice_origin.startswith("ORDER/100;")


@pytest.mark.parametrize("consolidated", [False, True, None])
@pytest.mark.parametrize("final", [False, True])
def test_multiple_sales_orders_keep_native_separate_and_consolidated_creation(monkeypatch, consolidated, final):
    env = Env()
    calls = []
    sources = []
    for record_id, quantity in ((100, 2), (101, 3)):
        source = env.add("sale.order", record_id, name=f"ORDER/{record_id}", company_id=env.company,
                         state="sale", invoice_status="to invoice")
        line = env.add("sale.order.line", record_id + 10, order_id=Records(env, "sale.order", [source]),
                       display_type=False, is_downpayment=False, qty_to_invoice=Decimal(quantity))
        source.order_line = Records(env, "sale.order.line", [line])
        source._get_invoiceable_lines = lambda _final, source=source: source.order_line
        sources.append(source)

    def create_native(selected, **options):
        calls.append(([source.id for source in selected], options))
        if options["grouped"] and len(selected) != 1:
            raise ValueError("Expected singleton: account.move(native separate invoices)")
        move = env.existing_move(1000 + selected[0].id, move_type="out_invoice", state="draft")
        move.invoice_origin = ", ".join(source.name for source in selected)
        rows = []
        for source in selected:
            rows.append(env.add("account.move.line", 2000 + source.id, display_type="product",
                                quantity=source.order_line.qty_to_invoice, sale_line_ids=source.order_line))
        move.invoice_line_ids = Records(env, "account.move.line", rows)
        move.write = lambda values: Records(env, "account.move", [move]).write(values)
        return Records(env, "account.move", [move])

    for source in sources:
        source._create_invoices = lambda source=source, **options: create_native([source], **options)

    class OrderRecords(Records):
        def _create_invoices(self, **options):
            return create_native(list(self), **options)

    original_ensure = writes._ensure_ids
    monkeypatch.setattr(writes, "_ensure_ids", lambda current, name, ids, domain, company, failure:
                        OrderRecords(env, name, sources) if name == "sale.order" else original_ensure(current, name, ids, domain, company, failure))
    parameters = {"order_ids": [100, 101], "deduct_down_payments": final}
    if consolidated is not None:
        parameters["consolidated_billing"] = consolidated
    execute = lambda: writes._order_invoice_round(env, "sale.order.invoice.create", parameters, 7, "multiple-order-round", Failure)
    result, replay = execute()
    assert not replay
    if consolidated is False:
        assert calls == [([100], {"grouped": True, "final": final}), ([101], {"grouped": True, "final": final})]
        assert result["processed_count"] == 2
        assert [item["source_id"] for item in result["items"]] == [100, 101]
    else:
        assert calls == [([100, 101], {"grouped": False, "final": final})]
        assert result["processed_count"] == 1 and result["items"][0]["source_id"] is None
    before = list(calls)
    assert execute() == (result, True) and calls == before


@pytest.mark.parametrize("method,requested", [("percentage", "10"), ("fixed", "12.01")])
def test_down_payment_uses_installed_wizard_tax_rounding_delta_and_replays_before_wizard(monkeypatch, method, requested):
    env = Env()
    order = env.add("sale.order", 100, name="SO/100", company_id=env.company, state="sale")
    source_line = env.add("sale.order.line", 110, order_id=Records(env, "sale.order", [order]), display_type=False,
                          _prepare_base_line_for_taxes_computation=lambda: {"native_base": True})
    order.order_line = Records(env, "sale.order.line", [source_line])
    calls = []
    original_scoped = writes._scoped

    class Tax:
        def _add_tax_details_in_base_lines(self, lines, company):
            calls.append("native-tax-details")

        def _round_base_lines_tax_details(self, lines, company):
            calls.append("native-tax-rounding")

        def _prepare_down_payment_lines(self, **values):
            calls.append(("native-downpayment", values))
            return [{"tax_details": {"total_included_currency": 12, "total_excluded_currency": 10,
                                     "delta_total_excluded_currency": 0.01, "taxes_data": [{"tax_amount_currency": 2}]}}]

    class Wizard:
        id = 900

        def with_context(self, **context):
            return self

        def create(self, values):
            calls.append(("wizard-create", values))
            return self

        def _check_amount_is_positive(self):
            calls.append("native-positive-check")

        def _create_invoices(self, selected_order):
            calls.append("native-create-invoices")
            source = env.add("sale.order.line", 120, order_id=Records(env, "sale.order", [order]), is_downpayment=True)
            invoice = env.existing_move(600, move_type="out_invoice", state="draft")
            invoice.invoice_origin = order.name
            invoice.amount_total = Decimal("12.01")
            line = env.add("account.move.line", 610, display_type="product", is_downpayment=True, sale_line_ids=Records(env, "sale.order.line", [source]))
            invoice.invoice_line_ids = Records(env, "account.move.line", [line])
            return Records(env, "account.move", [invoice])

    monkeypatch.setattr(writes, "_scoped", lambda current, model, company: Wizard() if model == "sale.advance.payment.inv" else Tax() if model == "account.tax" else original_scoped(current, model, company))
    params = {"order_id": 100, "method": method, "amount": requested}
    execute = lambda key="downpayment-round": writes._create_sale_down_payment(env, params, 7, key, Failure)
    result, replay = execute()
    assert not replay and result["source_id"] == 100
    creation = next(call[1] for call in calls if isinstance(call, tuple) and call[0] == "wizard-create")
    assert creation == {"sale_order_ids": [(6, 0, [100])], "advance_payment_method": method,
                        "amount" if method == "percentage" else "fixed_amount": float(Decimal(requested))}
    assert calls.index("native-positive-check") < calls.index("native-create-invoices")
    assert execute()[1] is True
    assert calls.count("native-create-invoices") == 1
    params["amount"] = "20"
    with pytest.raises(Failure) as caught:
        execute()
    assert caught.value.code == "idempotency_conflict"


def test_policy_only_update_writes_visible_shared_template_and_checks_missing_field(monkeypatch):
    env = Env()
    template = env.add("product.template", 100, company_id=False, name="Shared template", active=True,
                       invoice_policy="order", purchase_method="receive", _fields={"invoice_policy": object(), "purchase_method": object()})
    product = env.add("product.product", 101, company_id=False, name="Variant", active=True,
                      product_tmpl_id=Records(env, "product.template", [template]))
    monkeypatch.setattr(writes, "_fixed_product", lambda *_args, **_kwargs: pytest.fail("policy-only writes must not assume one company-local variant"))
    params = {"product_id": product.id, "changes": {"invoice_policy": "delivery", "purchase_method": "purchase"}}
    capability = "product.accounting_profile.update"
    payload = _payload(capability, params, key=writes._deterministic_key(capability, params, 7))
    page = writes.dispatch(env, payload, 7, Failure)
    assert not page["idempotent_replay"] and page["result"]["source_id"] == template.id
    assert template.invoice_policy == "delivery" and template.purchase_method == "purchase"
    assert writes.dispatch(env, payload, 7, Failure)["idempotent_replay"] is True
    template._fields.pop("invoice_policy")
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, payload, 7, Failure)
    assert caught.value.code == "state_conflict"
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, _payload("product.update", params, key="policy-wrong-command"), 7, Failure)
    assert caught.value.code == "bridge_protocol_error"


@pytest.mark.parametrize("omit_line", [False, True])
def test_new_grouped_many_writeoff_checks_native_account_label_and_amount(monkeypatch, omit_line):
    fixture = PaymentFixture(monkeypatch)
    fixture.parameters.update(installments_mode="full", amount="25", payment_difference_handling="reconcile",
                              writeoff_account_id=fixture.env.expense.id, writeoff_label="Round difference")
    fixture.defect = "writeoff" if omit_line else None
    if omit_line:
        with pytest.raises(Failure) as caught:
            fixture.execute()
        assert caught.value.code == "odoo_write_error"
    else:
        result, replay = fixture.execute()
        assert not replay and result["id"] is not None
        assert fixture.wizard.payment_difference == 175


def test_new_round_marker_preserves_long_native_origin_and_legacy_sale_acl():
    assert ("account.move", "write") not in writes._ACCESS["sale.order.invoice.create"]
    assert ("account.move", "write") in writes._ACCESS["sale.order.down_payment.create"]
    assert ("res.partner.bank", "create") not in writes._ACCESS["sale.order.down_payment.create"]
    origin = ", ".join(f"SO/{number:04d}" for number in range(100))
    move = SimpleNamespace(invoice_origin=origin)
    move.write = lambda values: setattr(move, "invoice_origin", values["invoice_origin"])
    writes._mark_invoice_round(move, "ODACV4:round", "ODACV4K:key", Failure)
    assert move.invoice_origin == f"{origin};ODACV4:round;ODACV4K:key"

    class AccessError(RuntimeError):
        pass

    def denied_write(values):
        raise AccessError("native move write denied")

    move.write = denied_write
    with pytest.raises(AccessError, match="native move write denied"):
        writes._mark_invoice_round(move, "ODACV4:other-round", "ODACV4K:other-key", Failure)
