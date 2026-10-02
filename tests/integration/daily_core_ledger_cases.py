"""Ordinary-user ledger, bank and reconciliation cases for the shared smoke."""

from collections import Counter
from decimal import Decimal
from hashlib import sha256


def _number(value):
    return Decimal(str(value))


def _lines(case, amount, debit_account=None, credit_account=None, suffix="entry"):
    return [
        {"name": case.marker + suffix + " debit", "account_id": debit_account or case.ids["expense"],
         "partner_id": None, "debit": amount, "credit": "0"},
        {"name": case.marker + suffix + " credit", "account_id": credit_account or case.ids["income"],
         "partner_id": None, "debit": "0", "credit": amount},
    ]


def _entry(case, amount, suffix, *, debit_account=None, credit_account=None):
    result = case.write("journal_entry.create", {
        "journal_id": case.ids["general_journal"], "date": case.today.isoformat(),
        "reference": case.marker + suffix,
        "lines": _lines(case, amount, debit_account, credit_account, suffix),
    }, replay=True, label=suffix)
    move = case.env["account.move"].browse(result["id"])
    assert result["state"] == "draft" and move.company_id.id == 1 and move.move_type == "entry"
    _read_entry(case, move, "draft", amount)
    return move


def _read_entry(case, move, state, amount=None):
    data = case.read("journal_entry.get", {"entry_id": move.id})
    assert data["id"] == move.id and data["company_id"] == 1 and data["state"] == state == move.state
    assert data["journal"]["id"] == move.journal_id.id and data["date"] == str(move.date)
    assert data["ref"] == (move.ref or None)
    assert {row["id"] for row in data["lines"]} == set(move.line_ids.ids)
    by_id = {line.id: line for line in move.line_ids}
    for row in data["lines"]:
        native = by_id[row["id"]]
        assert row["account"]["id"] == native.account_id.id
        assert row["name"] == (native.name or None)
        for field in ("debit", "credit", "balance", "amount_currency"):
            assert _number(row[field]) == _number(native[field])
    debit = sum((_number(line.debit) for line in move.line_ids), Decimal(0))
    credit = sum((_number(line.credit) for line in move.line_ids), Decimal(0))
    assert _number(data["totals"]["debit"]) == debit == credit == _number(data["totals"]["credit"])
    assert _number(data["totals"]["balance"]) == 0
    if amount is not None:
        assert debit == _number(amount)
    return data


def _snapshot(move):
    lines = move.line_ids.sorted("id")
    partials = (lines.matched_debit_ids | lines.matched_credit_ids).sorted("id")
    fulls = (lines.full_reconcile_id | partials.full_reconcile_id).sorted("id")
    return (
        move.read(["state", "date", "ref", "journal_id", "company_id", "reversed_entry_id", "reversal_move_ids"]),
        lines.read(["name", "account_id", "partner_id", "debit", "credit", "balance", "currency_id",
                    "amount_currency", "amount_residual", "amount_residual_currency", "reconciled",
                    "matched_debit_ids", "matched_credit_ids", "full_reconcile_id"]),
        partials.read(["amount", "debit_move_id", "credit_move_id", "full_reconcile_id", "exchange_move_id"]),
        fulls.read(["partial_reconcile_ids", "reconciled_line_ids"]),
    )


def _financial(move):
    return move.line_ids.sorted("id").read([
        "name", "account_id", "partner_id", "debit", "credit", "balance", "currency_id", "amount_currency",
    ])


def _s06(case):
    source = _entry(case, "120", "s06-source")
    case.write("journal_entry.update", {"move_id": source.id, "changes": {
        "reference": case.marker + "s06-edited"}}, replay=True)
    existing_ids = set(source.line_ids.ids)
    patches = [{"line_id": line.id, "changes": {
        "debit": "135" if line.balance > 0 else "0",
        "credit": "135" if line.balance < 0 else "0"}} for line in source.line_ids.sorted("id")]
    case.write("journal_entry.lines.update", {"move_id": source.id, "lines": patches}, replay=True)
    assert set(source.line_ids.ids) == existing_ids
    _read_entry(case, source, "draft", "135")
    case.write("journal_entry.post", {"move_id": source.id}, replay=True)
    _read_entry(case, source, "posted", "135")
    before = _financial(source)
    result = case.write("journal_entry.reverse", {"move_id": source.id,
        "date": case.today.isoformat(), "reason": case.marker + "s06-reversal"}, replay=True)
    reversal = case.env["account.move"].browse(result["id"])
    assert result["source_id"] == source.id and reversal.reversed_entry_id == source
    assert reversal.id != source.id and reversal.move_type == "entry" and reversal.company_id.id == 1
    _read_entry(case, reversal, "posted", "-135" if all(reversal.line_ids.mapped("is_storno")) else "135")
    assert Counter((line.account_id.id, _number(line.balance)) for line in reversal.line_ids) == Counter(
        (line.account_id.id, -_number(line.balance)) for line in source.line_ids)
    assert _financial(source) == before and source.state == "posted"
    origins = case.read("accounting_move.origin_links.inspect", {"move_id": source.id})
    reverse_origins = case.read("accounting_move.origin_links.inspect", {"move_id": reversal.id})
    assert [row["id"] for row in origins["reversal_moves"]] == [reversal.id]
    assert reverse_origins["reversed_entry"]["id"] == source.id
    case.verified.add("S06")
    return source, reversal


def _s07(case):
    ids, env = case.ids, case.env
    invoice_result = case.write("customer_invoice.create", {
        "partner_id": ids["customer"], "journal_id": ids["sale_journal"],
        "date": case.today.isoformat(), "invoice_date": case.today.isoformat(),
        "invoice_date_due": case.today.isoformat(), "payment_term_id": None, "currency_id": ids["currency"],
        "lines": [{"name": case.marker + "s07-payment", "account_id": ids["income"],
                   "quantity": "1", "price_unit": "30", "tax_ids": []}],
    }, replay=True, label="s07-payment-source")
    invoice = env["account.move"].browse(invoice_result["id"])
    case.write("invoice.post", {"move_id": invoice.id}, replay=True)
    payment_result = case.write("receivable.payment.register", {"move_id": invoice.id,
        "journal_id": ids["owned_bank_journal"], "payment_date": case.today.isoformat()}, replay=True)
    payment = env["account.payment"].browse(payment_result["id"])
    outstanding = payment.move_id.line_ids.filtered(lambda line: line.account_id == payment.outstanding_account_id)
    assert len(outstanding) == 1 and _number(outstanding.amount_residual) == 30
    assert _number(invoice.amount_residual) == 0 and payment.payment_type == "inbound"
    payment_before = _snapshot(payment.move_id)
    assert case.read("payment.get", {"payment_id": payment.id})["reconciled_bank_transactions"] == []
    transactions = [case.write("bank.transaction.record", {
        "journal_id": ids["owned_bank_journal"], "date": case.today.isoformat(), "amount": amount,
        "payment_ref": case.marker + "s07-bank-" + amount, "partner_id": ids["customer"],
    }, replay=True, label="s07-bank-" + amount) for amount in ("30", "1")]
    transaction_ids = sorted(row["id"] for row in transactions)
    statement = case.write("bank.statement.create", {"transaction_ids": transaction_ids,
        "reference": case.marker + "s07-statement", "balance_start": "0", "balance_end_real": "31"}, replay=True)
    header = case.read("bank.statement.get", {"bank_statement_id": statement["id"]})
    assert header["journal"]["id"] == ids["owned_bank_journal"] and header["transaction_count"] == 2
    assert _number(header["balance_start"]) == 0 and _number(header["balance_end"]) == 31
    assert _number(header["balance_end_real"]) == 31
    parameters = {"statement_id": statement["id"], "limit": 1, "cursor": None}
    first = case.read("bank.transaction.search", parameters)
    assert first["has_more"] and first["next_cursor"] and len(first["items"]) == 1
    second = case.read("bank.transaction.search", {**parameters, "cursor": first["next_cursor"]})
    assert not second["has_more"] and second["next_cursor"] is None and len(second["items"]) == 1
    rows = first["items"] + second["items"]
    assert sorted(row["id"] for row in rows) == transaction_ids
    assert all(row["statement_id"] == statement["id"] for row in rows)
    target = transactions[0]["id"]
    initial = case.read("bank.transaction.reconciliation.get", {"transaction_id": target})
    assert not initial["transaction"]["is_reconciled"] and initial["suspense_line"] is not None
    assert _number(initial["suspense_line"]["amount_residual"]) == -30
    case.write("bank.transaction.match", {"transaction_id": target, "candidate_line_ids": [outstanding.id]}, replay=True)
    matched = case.read("bank.transaction.reconciliation.get", {"transaction_id": target})
    assert matched["transaction"]["is_reconciled"] and matched["suspense_line"] is None
    assert any(row["source_line_id"] == outstanding.id for row in matched["matched_lines"])
    assert _number(outstanding.amount_residual) == 0
    assert case.read("payment.get", {"payment_id": payment.id})["reconciled_bank_transactions"] == [
        {"id": target, "company_id": 1}]
    assert payment.reconciled_statement_line_ids.ids == [target]
    case.write("bank.transaction.unmatch", {"transaction_id": target}, replay=True)
    restored = case.read("bank.transaction.reconciliation.get", {"transaction_id": target})
    assert not restored["transaction"]["is_reconciled"] and not restored["matched_lines"] and not restored["payment_ids"]
    assert _number(restored["suspense_line"]["amount_residual"]) == -30
    assert _number(restored["liquidity_line"]["balance"]) == _number(initial["liquidity_line"]["balance"]) == 30
    assert _number(outstanding.amount_residual) == 30 and _number(invoice.amount_residual) == 0
    assert _snapshot(payment.move_id) == payment_before
    assert not payment.reconciled_statement_line_ids
    assert case.read("payment.get", {"payment_id": payment.id})["reconciled_bank_transactions"] == []
    for row_id in transaction_ids:
        assert case.read("bank.transaction.get", {"transaction_id": row_id})["statement_id"] == statement["id"]
    assert sorted(env["account.bank.statement"].browse(statement["id"]).line_ids.ids) == transaction_ids
    case.verified.add("S07")


def _s08(case):
    account = case.fixture("account.account", {"name": case.marker + "s08 matching", "code": "DG" + sha256(case.marker.encode()).hexdigest()[:8],
        "account_type": "asset_current", "reconcile": True, "company_ids": [(6, 0, [1])]})
    for label, final_amount in (("partial", "20"), ("full", "50")):
        moves = [_entry(case, "120", "s08-" + label + "-source", debit_account=account.id)]
        moves += [_entry(case, amount, "s08-" + label + "-credit-" + amount,
                         credit_account=account.id) for amount in ("70", final_amount)]
        for move in moves:
            case.write("journal_entry.post", {"move_id": move.id}, replay=True)
        targets = [move.line_ids.filtered(lambda line: line.account_id == account) for move in moves]
        assert all(len(line) == 1 for line in targets)
        financial = [_financial(move) for move in moves]
        for other in targets[1:]:
            case.write("reconciliation.apply", {"line_ids": sorted([targets[0].id, other.id])}, replay=True)
        partials = targets[0].matched_debit_ids | targets[0].matched_credit_ids
        assert len(partials) == 2 and bool(targets[0].full_reconcile_id) is (label == "full")
        assert _number(targets[0].amount_residual) == (0 if label == "full" else 30)
        for line in targets:
            graph = case.read("journal_item.reconciliation.inspect", {"journal_item_id": line.id})
            assert graph["partial_reconcile_ids"] == sorted((line.matched_debit_ids | line.matched_credit_ids).ids)
            assert graph["full_reconcile_id"] == (line.full_reconcile_id.id or None)
            assert _number(graph["amount_residual"]) == _number(line.amount_residual)
        before = [_snapshot(move) for move in moves]
        case.denied("reconciliation.undo", {"line_ids": sorted([targets[0].id, targets[1].id])}, "state_conflict", 5)
        assert [_snapshot(move) for move in moves] == before
        # A replay from this leaf naturally shrinks to one row; no identical-result claim.
        undone = case.write("reconciliation.undo", {"mode": "match_group", "line_ids": [targets[1].id]})
        assert undone["line_ids"] == sorted(line.id for line in targets) and not partials.exists()
        assert not undone["partial_reconcile_ids"] and undone["full_reconcile_id"] is None
        for line in targets:
            graph = case.read("journal_item.reconciliation.inspect", {"journal_item_id": line.id})
            assert not graph["partial_reconcile_ids"] and graph["full_reconcile_id"] is None and not graph["reconciled"]
            assert _number(graph["amount_residual"]) == _number(line.balance)
        assert [_financial(move) for move in moves] == financial
    case.verified.add("S08")


def _s12(case, source, reversal):
    adjustment = _entry(case, "45", "s12-period-adjustment")
    original = _financial(adjustment)
    case.write("journal_entry.cancel", {"move_id": adjustment.id}, replay=True)
    _read_entry(case, adjustment, "cancel", "45")
    case.write("journal_entry.reset_to_draft", {"move_id": adjustment.id}, replay=True)
    assert _financial(adjustment) == original
    case.write("journal_entry.lines.replace", {"move_id": adjustment.id,
        "lines": _lines(case, "60", suffix="s12-adjusted")}, replay=True)
    _read_entry(case, adjustment, "draft", "60")
    positive = adjustment.line_ids.filtered(lambda line: line.balance > 0)
    before = _snapshot(adjustment)
    case.denied("journal_entry.lines.update", {"move_id": adjustment.id,
        "lines": [{"line_id": positive.id, "changes": {"debit": "61"}}]}, "business_rule_error", 6)
    assert _snapshot(adjustment) == before
    source_before = _snapshot(source)
    case.denied("journal_entry.lines.update", {"move_id": adjustment.id,
        "lines": [{"line_id": source.line_ids[0].id, "changes": {"name": case.marker + "wrong-parent"}}]}, "record_not_found", 4)
    assert _snapshot(adjustment) == before and _snapshot(source) == source_before
    case.denied("journal_entry.post", {"move_id": adjustment.id}, "confirmation_required", 2, confirmation="invoice.post")
    case.denied("journal_entry.post", {"move_id": adjustment.id}, "invalid_idempotency_key", 2, key="wrong-key-12345")
    assert _snapshot(adjustment) == before
    reversed_before = (_snapshot(source), _snapshot(reversal))
    case.denied("journal_entry.reverse", {"move_id": source.id, "date": case.today.isoformat(),
        "reason": case.marker + "different-reversal-intent"}, "idempotency_conflict", 5)
    assert (_snapshot(source), _snapshot(reversal)) == reversed_before
    case.write("journal_entry.post", {"move_id": adjustment.id}, replay=True)
    _read_entry(case, adjustment, "posted", "60")
    before = _snapshot(adjustment)
    case.denied("journal_entry.lines.update", {"move_id": adjustment.id,
        "lines": [{"line_id": positive.id, "changes": {"debit": "61"}}]}, "state_conflict", 5)
    assert _snapshot(adjustment) == before
    # Foreign fixtures come last; only fixture setup/audit use the supplied admin.
    journal = case.fixture("account.journal", {"name": case.marker + "foreign-general",
        "code": "L" + sha256(case.marker.encode()).hexdigest()[:4], "type": "general", "company_id": 2}, company=2)
    foreign = case.fixture("account.move", {"move_type": "entry", "company_id": 2, "journal_id": journal.id,
        "date": case.today.isoformat(), "ref": case.marker + "foreign-adjustment"}, company=2)
    foreign_before = _snapshot(foreign)
    case.denied("journal_entry.update", {"move_id": foreign.id,
        "changes": {"reference": case.marker + "foreign-change"}}, "record_not_found", 4)
    assert _snapshot(foreign) == foreign_before and _snapshot(adjustment) == before
    case.verified.add("S12")


def exercise(case):
    """Run four fixed cases; the parent owns schemas, tracking and fresh rollback."""
    assert case.env.uid == 5 and not case.env.su and case.env.company.id == 1
    source, reversal = _s06(case)
    _s07(case)
    _s08(case)
    _s12(case, source, reversal)
