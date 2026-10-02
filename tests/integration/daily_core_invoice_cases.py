"""Owned daily invoice/payment scenarios for the shared rollback smoke."""

from decimal import Decimal


def exercise(case):
    assert case.env.uid == 5 and case.env.su is False
    assert case.env.context["allowed_company_ids"] == [1]
    ids, today = case.ids, case.today.isoformat()
    currency = case.env["res.currency"].browse(ids["currency"])
    assert currency == case.env.company.currency_id

    def line(side, amount="100", taxed=False):
        return {
            "name": f"{case.marker}-{side}",
            "product_id": None,
            "account_id": ids["income" if side == "customer" else "expense"],
            "quantity": "1",
            "price_unit": amount,
            "discount": "0",
            "tax_ids": [ids["sale_tax" if side == "customer" else "purchase_tax"]]
            if taxed else [],
        }

    def document(move_id, side, base, tax=0, *, refund=False, state="posted"):
        data = case.read("invoice.get", {"invoice_id": move_id})
        native = case.env["account.move"].browse(move_id)
        move_type = ("out_" if side == "customer" else "in_") + (
            "refund" if refund else "invoice"
        )
        assert data["id"] == native.id and data["state"] == native.state == state
        assert data["move_type"] == native.move_type == move_type
        assert data["company_id"] == native.company_id.id == 1
        assert data["currency"]["id"] == native.currency_id.id == currency.id
        expected = (Decimal(base), Decimal(tax), Decimal(base) + Decimal(tax))
        for field, amount in zip(
            ("amount_untaxed", "amount_tax", "amount_total"), expected, strict=True
        ):
            assert Decimal(data[field]) == amount
            assert currency.is_zero(float(amount - Decimal(str(native[field]))))
        assert currency.is_zero(
            float(Decimal(data["amount_residual"]) - Decimal(str(native.amount_residual)))
        )
        return data

    def status(move_id, residual):
        data = case.read("invoice.payment_status.inspect", {"invoice_id": move_id})
        native = case.env["account.move"].browse(move_id)
        assert data["id"] == move_id and data["state"] == native.state == "posted"
        assert Decimal(data["amount_residual"]) == residual
        assert currency.is_zero(float(Decimal(str(native.amount_residual)) - residual))
        assert len(data["receivable_payable_lines"]) == 1
        term = data["receivable_payable_lines"][0]
        assert abs(Decimal(term["amount_residual"])) == residual
        assert abs(Decimal(term["amount_residual_currency"])) == residual
        assert term["reconciled"] is (residual == 0)
        if residual == 0:
            assert data["payment_state"] in {"in_payment", "paid"}
        return data

    def create(side, suffix, *, taxed=False):
        result = case.write(
            "customer_invoice.create" if side == "customer" else "vendor_bill.create",
            {
                "partner_id": ids[side],
                "journal_id": ids["sale_journal" if side == "customer" else "purchase_journal"],
                "date": today, "invoice_date": today, "invoice_date_due": today,
                "payment_term_id": None, "currency_id": currency.id,
                "reference": f"{case.marker}-{side}-{suffix}",
                "lines": [line(side, taxed=taxed)],
            }, replay=True, label=f"{side}-{suffix}",
        )
        document(result["id"], side, 100, 10 if taxed else 0, state="draft")
        return result["id"]

    def post(move_id):
        case.write("invoice.post", {"move_id": move_id}, replay=True)

    def pay(side, move_id, expected_amount, direction, term_balance, **controls):
        remaining = Decimal(str(case.env["account.move"].browse(move_id).amount_residual))
        before = status(move_id, remaining)
        assert remaining >= abs(term_balance) > 0
        result = case.write(
            "receivable.payment.register" if side == "customer" else "payable.payment.register",
            {
                "move_id": move_id, "journal_id": ids["owned_bank_journal"],
                "payment_date": today, **controls,
            }, replay=True,
        )
        assert result["model"] == "account.payment" and result["source_id"] == move_id
        data = case.read("payment.get", {"payment_id": result["id"]})
        native = case.env["account.payment"].browse(result["id"])
        assert data["id"] == native.id and data["state"] == native.state
        assert data["state"] in {"in_process", "paid"}
        assert data["company_id"] == native.company_id.id == 1
        assert data["date"] == today
        assert data["journal"]["id"] == native.journal_id.id == ids["owned_bank_journal"]
        assert data["partner_type"] == native.partner_type == side
        assert data["payment_type"] == native.payment_type == direction
        assert data["partner"]["id"] == native.partner_id.id == ids[side]
        assert data["currency"]["id"] == data["company_currency"]["id"] == currency.id
        assert Decimal(data["amount"]) == Decimal(str(native.amount)) == expected_amount
        assert data["payment_method_line"]["id"] == native.payment_method_line_id.id == ids[f"owned_bank_{direction}"]
        linked = data["reconciled_invoices" if side == "customer" else "reconciled_bills"]
        assert {row["id"] for row in linked} == {move_id}
        assert data["move_id"] == data["journal_entry"]["id"] == native.move_id.id
        entry = case.read("journal_entry.get", {"entry_id": data["move_id"]})
        assert entry["state"] == "posted" and entry["company_id"] == 1
        rows = entry["lines"]
        assert {row["id"] for row in rows} == set(result["line_ids"]) == set(native.move_id.line_ids.ids)
        assert sum(Decimal(row["balance"]) for row in rows) == 0
        assert sum(Decimal(row["debit"]) for row in rows) == sum(Decimal(row["credit"]) for row in rows)
        term_id = before["receivable_payable_lines"][0]["account"]["id"]
        terms = [row for row in rows if row["account"]["id"] == term_id]
        assert len(terms) == 1 and Decimal(terms[0]["balance"]) == -term_balance
        for row in rows:
            native_line = case.env["account.move.line"].browse(row["id"])
            assert Decimal(row["debit"]) - Decimal(row["credit"]) == Decimal(row["balance"])
            assert Decimal(row["amount_currency"]) == Decimal(row["balance"])
            assert currency.is_zero(float(Decimal(row["balance"]) - Decimal(str(native_line.balance))))
        return data, entry

    for side, scenario in (("customer", "S02"), ("supplier", "S03")):
        sign = Decimal(1 if side == "customer" else -1)
        move_id = create(side, "taxed", taxed=True)
        draft = document(move_id, side, 100, 10, state="draft")
        business = [row for row in draft["lines"] if row["display_type"] == "product"]
        assert len(business) == 1
        case.write("invoice.line.update", {
            "move_id": move_id, "line_id": business[0]["id"], "changes": {"price_unit": "120"},
        }, replay=True)
        edited = document(move_id, side, 120, 12, state="draft")
        assert {row["id"] for row in edited["lines"] if row["display_type"] == "product"} == {business[0]["id"]}
        edited_line = next(row for row in edited["lines"] if row["id"] == business[0]["id"])
        assert Decimal(edited_line["price_unit"]) == 120
        assert Decimal(edited_line["quantity"]) == 1 and Decimal(edited_line["discount"]) == 0
        assert {tax["id"] for tax in edited_line["taxes"]} == set(line(side, taxed=True)["tax_ids"])
        post(move_id)
        document(move_id, side, 120, 12)
        status(move_id, Decimal(132))
        direction = "inbound" if side == "customer" else "outbound"
        # For a partial payment the term counterpart closes only the paid amount.
        partial, _ = pay(side, move_id, Decimal(40), direction, sign * 40, amount="40")
        partial_status = status(move_id, Decimal(92))
        assert partial_status["payment_state"] == "partial"
        assert {row["id"] for row in partial_status["payments"]} == {partial["id"]}
        open_cap = "receivable.open_items.list" if side == "customer" else "payable.open_items.list"
        opened = case.read(open_cap, {"move_id": move_id, "limit": 1})
        assert not opened["has_more"] and len(opened["items"]) == 1
        item = opened["items"][0]
        assert item["move"]["id"] == move_id and not item["reconciled"]
        assert Decimal(item["amount_residual"]) == sign * 92
        assert Decimal(item["amount_residual_currency"]) == sign * 92
        full, _ = pay(side, move_id, Decimal(92), direction, sign * 92)
        settled = status(move_id, Decimal(0))
        assert {row["id"] for row in settled["payments"]} == {partial["id"], full["id"]}
        assert sum(Decimal(row["company_amount"]) for row in settled["reconciliations"]) == 132
        closed = case.read(open_cap, {"move_id": move_id, "limit": 1})
        assert not closed["items"] and not closed["has_more"]
        document(move_id, side, 120, 12)
        case.verified.add(scenario)

    for side, scenario in (("customer", "S04"), ("supplier", "S05")):
        sign = Decimal(1 if side == "customer" else -1)
        refund_cap = "customer_credit_note.create" if side == "customer" else "vendor_refund.create"
        source = create(side, "unpaid-credit")
        post(source)
        status(source, Decimal(100))
        refund = case.write(refund_cap, {
            "move_id": source, "date": today, "reason": f"{case.marker}-{side}-partial-credit",
            "lines": [line(side, "40")],
        }, replay=True, label=f"{side}-partial-credit")["id"]
        assert case.env["account.move"].browse(refund).reversed_entry_id.id == source
        document(refund, side, 40, refund=True, state="draft")
        status(source, Decimal(100))
        post(refund)
        document(refund, side, 40, refund=True)
        status(refund, Decimal(0))
        credited = status(source, Decimal(60))
        matches = [row for row in credited["reconciliations"] if row["counterpart_move"]["id"] == refund]
        assert len(matches) == 1 and matches[0]["payment_id"] is None
        matched = matches[0]
        assert Decimal(matched["company_amount"]) == 40
        case.write("reconciliation.undo", {
            "invoice_id": source, "partial_reconcile_id": matched["id"],
            "invoice_line_id": matched["invoice_line_id"], "counterpart_line_id": matched["counterpart_line_id"],
        }, replay=True)
        undone = status(source, Decimal(100))
        assert undone["reconciliations"] == []
        status(refund, Decimal(40))
        outstanding = [row for row in undone["outstanding_items"] if row["move_id"] == refund]
        assert len(outstanding) == 1 and outstanding[0]["payment_id"] is None
        assert Decimal(outstanding[0]["amount"]) == 40
        case.write("reconciliation.apply", {
            "invoice_id": source, "outstanding_line_id": outstanding[0]["line_id"],
        }, replay=True)
        applied = status(source, Decimal(60))
        assert len(applied["reconciliations"]) == 1 and applied["reconciliations"][0]["id"] != matched["id"]
        assert applied["reconciliations"][0]["counterpart_move"]["id"] == refund
        assert Decimal(applied["reconciliations"][0]["company_amount"]) == 40
        status(refund, Decimal(0))
        document(source, side, 100)
        document(refund, side, 40, refund=True)

        paid_source = create(side, "cash-refund")
        post(paid_source)
        pay(side, paid_source, Decimal(100), "inbound" if side == "customer" else "outbound", sign * 100)
        paid = status(paid_source, Decimal(0))
        original_matches = {row["id"] for row in paid["reconciliations"]}
        cash_refund = case.write(refund_cap, {
            "move_id": paid_source, "date": today, "reason": f"{case.marker}-{side}-cash-refund",
        }, replay=True)["id"]
        assert case.env["account.move"].browse(cash_refund).reversed_entry_id.id == paid_source
        document(cash_refund, side, 100, refund=True, state="draft")
        post(cash_refund)
        document(cash_refund, side, 100, refund=True)
        cash_open = status(cash_refund, Decimal(100))
        assert cash_open["reconciliations"] == []
        cash_payment, _ = pay(side, cash_refund, Decimal(100), "outbound" if side == "customer" else "inbound", -sign * 100)
        cash_paid = status(cash_refund, Decimal(0))
        assert {row["id"] for row in cash_paid["payments"]} == {cash_payment["id"]}
        assert {row["id"] for row in status(paid_source, Decimal(0))["reconciliations"]} == original_matches
        document(paid_source, side, 100)
        document(cash_refund, side, 100, refund=True)
        case.verified.add(scenario)

    for side in ("customer", "supplier"):
        sign = Decimal(1 if side == "customer" else -1)
        source = create(side, "difference")
        post(source)
        account_id = ids["expense" if side == "customer" else "income"]
        label = f"{case.marker}-{side}-difference"
        payment, entry = pay(side, source, Decimal(99), "inbound" if side == "customer" else "outbound", sign * 100,
            amount="99", payment_difference_handling="reconcile",
            writeoff_account_id=account_id, writeoff_label=label)
        rows = entry["lines"]
        assert len(rows) == 3
        writeoffs = [row for row in rows if row["account"]["id"] == account_id and row["name"] == label]
        assert len(writeoffs) == 1 and Decimal(writeoffs[0]["balance"]) == sign
        assert Decimal(writeoffs[0]["amount_currency"]) == sign
        method = case.env["account.payment.method.line"].browse(payment["payment_method_line"]["id"])
        outstanding = [row for row in rows if row["account"]["id"] == method.payment_account_id.id]
        assert len(outstanding) == 1 and Decimal(outstanding[0]["balance"]) == sign * 99
        assert Decimal(entry["totals"]["debit"]) == Decimal(entry["totals"]["credit"]) == 100
        settled = status(source, Decimal(0))
        assert {row["id"] for row in settled["payments"]} == {payment["id"]}
        assert len(settled["reconciliations"]) == 1
        assert Decimal(settled["reconciliations"][0]["company_amount"]) == 100
        document(source, side, 100)
    case.verified.add("S09")
