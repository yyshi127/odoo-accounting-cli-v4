from __future__ import annotations

import hashlib
import json
import sys
from decimal import ROUND_HALF_UP, Decimal
from types import SimpleNamespace
from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge import core_writes_runtime as writes


class Failure(RuntimeError):
    def __init__(self, code: str, message: str, *, exit_code: int, **_kwargs: Any) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


class Records(list[Any]):
    @property
    def ids(self) -> list[int]:
        return [record.id for record in self]

    @property
    def id(self) -> int | bool:
        return self[0].id if len(self) == 1 else False

    def __getattr__(self, name: str) -> Any:
        if len(self) == 1:
            return getattr(self[0], name)
        if name in {"matched_debit_ids", "matched_credit_ids", "full_reconcile_id"}:
            result = Records()
            for record in self:
                result |= getattr(record, name)
            return result
        raise AttributeError(name)

    def __or__(self, other: Records) -> Records:
        return Records({record.id: record for record in [*self, *other]}.values())

    def filtered(self, predicate) -> Records:
        return Records(record for record in self if predicate(record))

    def sorted(self, key) -> Records:
        return Records(sorted(self, key=key))

    def invalidate_recordset(self, *_args: Any) -> None:
        return None


class Currency:
    id = 1

    def round(self, amount: float) -> float:
        assert isinstance(amount, float)
        return float(Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _line(line_id: int, account_id: int, balance: float, name: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=line_id, account_id=SimpleNamespace(id=account_id), balance=balance,
        amount_currency=balance, currency_id=SimpleNamespace(id=1), name=name,
        matched_debit_ids=Records(), matched_credit_ids=Records(),
        full_reconcile_id=Records(), reconciled_lines_ids=Records(), payment_id=False,
        tax_ids=Records(), tax_repartition_line_id=False, tax_tag_ids=Records(),
        group_tax_id=False, tax_line_id=False, tax_base_amount=0, display_type="product",
    )


def _transaction(amount: float = 100) -> SimpleNamespace:
    currency = Currency()
    company = SimpleNamespace(id=7, currency_id=currency)
    journal = SimpleNamespace(id=9, type="bank", company_id=company, currency_id=False)
    move = SimpleNamespace(
        id=40, name="BNK/40", state="posted", move_type="entry", company_id=company,
        line_ids=Records([_line(401, 101, amount, "Liquidity"), _line(402, 102, -amount, "Suspense")]),
        invalidate_recordset=lambda *_args: None, _is_user_able_to_review=lambda: True,
    )
    transaction = SimpleNamespace(
        id=41, move_id=move, company_id=company, journal_id=journal,
        date="2026-10-02", amount=amount, payment_ref="Bank movement",
        partner_id=Records(), account_number=False, partner_name=False,
        foreign_currency_id=False, currency_id=currency, amount_currency=0,
        is_reconciled=False, checked=False, payment_ids=Records(),
        invalidate_recordset=lambda *_args: None,
    )
    transaction._seek_for_lines = lambda: (
        move.line_ids.filtered(lambda line: line.account_id.id == 101),
        move.line_ids.filtered(lambda line: line.account_id.id == 102),
        move.line_ids.filtered(lambda line: line.account_id.id not in {101, 102}),
    )
    transaction.write_calls = []

    def write(values: dict[str, Any]) -> None:
        transaction.write_calls.append(dict(values))
        for field, value in values.items():
            if field == "partner_id":
                value = Records([SimpleNamespace(id=value)]) if value else Records()
            setattr(transaction, field, value)

    transaction.write = write
    transaction.native_calls = []

    def replace(lines_to_set: Records, values: list[dict[str, Any]]) -> None:
        transaction.native_calls.append((list(lines_to_set.ids), values))
        move.line_ids = Records([*lines_to_set, *[
            _line(500 + index, value["account_id"], value["balance"], value["name"])
            for index, value in enumerate(values)
        ]])
        transaction.is_reconciled = True

    transaction._set_move_line_to_statement_line_move = replace
    transaction.undo_calls = []

    def undo() -> None:
        transaction.undo_calls.append(True)
        move.line_ids = Records([_line(601, 101, amount, "Liquidity"), _line(602, 102, -amount, "Suspense")])
        transaction.is_reconciled = False

    transaction.action_undo_reconciliation = undo
    return transaction


def _scope(monkeypatch, transaction: SimpleNamespace) -> list[tuple[str, set[int], list[Any]]]:
    references = []
    monkeypatch.setattr(writes, "_bank_transaction", lambda *_args: transaction)
    monkeypatch.setattr(writes, "_search_one", lambda *_args, **_kwargs: transaction.company_id)

    def ensure(_env, model, ids, domain, _company, _failure):
        references.append((model, ids, domain))
        if model == "account.journal":
            return Records([transaction.journal_id])
        if model == "account.move.line":
            return transaction.move_id.line_ids
        return Records([SimpleNamespace(id=record_id) for record_id in ids])

    monkeypatch.setattr(writes, "_ensure_ids", ensure)
    return references


def _counterparts() -> dict[str, Any]:
    return {"transaction_id": 41, "lines": [
        {"account_id": 20, "label": "First fee", "balance": "-70"},
        {"account_id": 21, "label": "Second fee", "balance": "-30"},
    ]}


@pytest.mark.parametrize("parameters", [
    {"transaction_id": True, "lines": _counterparts()["lines"]},
    {"transaction_id": 41, "lines": []},
    {"transaction_id": 41, "lines": _counterparts()["lines"][:1]},
    {"transaction_id": 41, "lines": _counterparts()["lines"] * 51},
    *[{"transaction_id": 41, "lines": [
        {**_counterparts()["lines"][0], field: value}, _counterparts()["lines"][1],
    ]} for field, value in [
        ("account_id", True), ("account_id", None), ("label", ""), ("label", " fee"),
        ("balance", 2), ("balance", True), ("balance", None), ("balance", "0"),
        ("balance", "-0"), ("balance", "1.00"), ("balance", "1e2"),
    ]],
    {"transaction_id": 41, "lines": [{**_counterparts()["lines"][0], "tax_ids": []}, _counterparts()["lines"][1]]},
])
def test_counterpart_runtime_rejects_unclosed_or_noncanonical_inputs(parameters) -> None:
    assert not writes._valid_parameters("bank.transaction.counterparts.replace", parameters)


def test_counterpart_fixed_maps_and_key_preserve_row_order() -> None:
    capability = "bank.transaction.counterparts.replace"
    parameters = _counterparts()
    assert capability in writes.CAPABILITIES
    assert writes._valid_parameters(capability, parameters)
    digest = hashlib.sha256(json.dumps(parameters["lines"], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:32]
    assert writes._deterministic_key(capability, parameters, 7) == f"{capability}:41:{digest}"
    assert writes._deterministic_key(capability, {**parameters, "lines": list(reversed(parameters["lines"]))}, 7) != f"{capability}:41:{digest}"
    assert {("res.partner.bank", "read"), ("account.move.line", "unlink")} <= writes._ACCESS[capability]
    assert ("res.partner.bank", "create") not in writes._ACCESS[capability]
    assert "res.partner.bank" in writes._MODELS[capability]


@pytest.mark.parametrize("denied,allowed", [
    (("res.partner.bank", "create"), True),
    (("account.move.line", "unlink"), False),
])
def test_counterpart_gate_leaves_conditional_bank_creation_to_native_acl(denied, allowed) -> None:
    checks = []

    class Model:
        def __init__(self, name):
            self.name = name

        def has_access(self, operation):
            checks.append((self.name, operation))
            return (self.name, operation) != denied

        def search_count(self, *_args, **_kwargs):
            return 1

    class Environment:
        registry = SimpleNamespace(get=lambda _model: object())
        user = SimpleNamespace(has_group=lambda _group: True)

        def __getitem__(self, model):
            return Model(model)

    assert writes._gate(Environment(), "bank.transaction.counterparts.replace", 7) == (True, True, allowed)
    assert ("res.partner.bank", "create") not in checks


@pytest.mark.parametrize("amount,balances", [(100, ["-70", "-30"]), (-20, ["12", "8"])])
def test_counterparts_call_one_native_helper_and_replay_multiset(monkeypatch, amount, balances) -> None:
    transaction = _transaction(amount)
    references = _scope(monkeypatch, transaction)
    parameters = _counterparts()
    for line, balance in zip(parameters["lines"], balances, strict=True):
        line["balance"] = balance
    result, replay = writes._replace_bank_counterparts(object(), parameters, 7, Failure)
    assert not replay and result["reconciled"] and result["state"] == "posted"
    assert len(result["line_ids"]) == 3 and result["partial_reconcile_ids"] == []
    assert len(transaction.native_calls) == 1
    retained, values = transaction.native_calls[0]
    assert retained == [401]
    assert all(set(value) == {"account_id", "name", "balance", "currency_id", "amount_currency", "partner_id"} for value in values)
    assert all(isinstance(value["balance"], float) and value["balance"] == value["amount_currency"] for value in values)
    assert ("account.account", {20, 21}, [
        ("company_ids", "in", [7]), ("active", "=", True),
        ("account_type", "in", ["income", "income_other", "expense", "expense_other", "expense_depreciation", "expense_direct_cost"]),
    ]) in references
    transaction.checked = True
    transaction.move_id._is_user_able_to_review = lambda: False
    replay_result, replay = writes._replace_bank_counterparts(object(), {**parameters, "lines": list(reversed(parameters["lines"]))}, 7, Failure)
    assert replay and replay_result == result and len(transaction.native_calls) == 1


def test_counterparts_round_individual_native_money_values(monkeypatch) -> None:
    transaction = _transaction()
    _scope(monkeypatch, transaction)
    parameters = _counterparts()
    parameters["lines"][0]["balance"] = "-69.999"
    result, replay = writes._replace_bank_counterparts(object(), parameters, 7, Failure)
    assert not replay and result["reconciled"]
    assert transaction.native_calls[0][1][0]["balance"] == -70.0


@pytest.mark.parametrize("change", [
    "foreign_currency", "journal_currency", "partial", "full", "payment", "source", "tax", "repartition", "tags", "tax_base",
])
def test_counterparts_reject_unsupported_existing_graph_without_writes(monkeypatch, change) -> None:
    transaction = _transaction()
    _scope(monkeypatch, transaction)
    line = transaction.move_id.line_ids[1]
    if change == "foreign_currency":
        transaction.foreign_currency_id = SimpleNamespace(id=2)
    elif change == "journal_currency":
        transaction.journal_id.currency_id = SimpleNamespace(id=2)
    elif change == "partial":
        line.matched_debit_ids = Records([SimpleNamespace(id=80)])
    elif change == "full":
        line.full_reconcile_id = Records([SimpleNamespace(id=81)])
    elif change == "payment":
        transaction.payment_ids = Records([SimpleNamespace(id=82)])
    elif change == "source":
        line.reconciled_lines_ids = Records([SimpleNamespace(id=83)])
    elif change == "tax":
        line.tax_ids = Records([SimpleNamespace(id=84)])
    elif change == "repartition":
        line.tax_repartition_line_id = SimpleNamespace(id=85)
    elif change == "tags":
        line.tax_tag_ids = Records([SimpleNamespace(id=86)])
    else:
        line.tax_base_amount = 1
    with pytest.raises(Failure, match="requires|Only isolated") as error:
        writes._replace_bank_counterparts(object(), _counterparts(), 7, Failure)
    assert error.value.code == "state_conflict" and transaction.native_calls == []


@pytest.mark.parametrize("balances", [["-60", "-30"], ["-0.001", "-99.999"]])
def test_counterparts_reject_unbalanced_or_zero_rounded_amounts(monkeypatch, balances) -> None:
    transaction = _transaction()
    _scope(monkeypatch, transaction)
    parameters = _counterparts()
    for line, balance in zip(parameters["lines"], balances, strict=True):
        line["balance"] = balance
    with pytest.raises(Failure) as error:
        writes._replace_bank_counterparts(object(), parameters, 7, Failure)
    assert error.value.code == "business_rule_error" and transaction.native_calls == []


def test_counterparts_keep_native_reviewer_check_only_on_actual_change(monkeypatch) -> None:
    transaction = _transaction()
    _scope(monkeypatch, transaction)
    writes._replace_bank_counterparts(object(), _counterparts(), 7, Failure)
    transaction.checked = True
    transaction.move_id._is_user_able_to_review = lambda: False
    parameters = _counterparts()
    parameters["lines"][0]["balance"], parameters["lines"][1]["balance"] = "-60", "-40"
    with pytest.raises(Failure, match="Validated") as error:
        writes._replace_bank_counterparts(object(), parameters, 7, Failure)
    assert error.value.code == "business_rule_error" and len(transaction.native_calls) == 1


def test_counterparts_allow_replacement_and_duplicate_rows_without_new_store(monkeypatch) -> None:
    transaction = _transaction()
    _scope(monkeypatch, transaction)
    writes._replace_bank_counterparts(object(), _counterparts(), 7, Failure)
    parameters = {"transaction_id": 41, "lines": [
        {"account_id": 20, "label": "Same fee", "balance": "-50"},
        {"account_id": 20, "label": "Same fee", "balance": "-50"},
    ]}
    result, replay = writes._replace_bank_counterparts(object(), parameters, 7, Failure)
    assert not replay and result["reconciled"] and len(transaction.native_calls) == 2
    _result, replay = writes._replace_bank_counterparts(object(), parameters, 7, Failure)
    assert replay and len(transaction.native_calls) == 2


@pytest.mark.parametrize("model", ["account.journal", "account.account", "account.move.line", "res.partner"])
def test_counterparts_require_ordinary_visible_company_references(monkeypatch, model) -> None:
    transaction = _transaction()
    transaction.partner_id = SimpleNamespace(id=8)
    _scope(monkeypatch, transaction)
    original = writes._ensure_ids

    def ensure(env, reference_model, ids, domain, company, failure):
        if reference_model == model:
            raise Failure("record_not_found", "not visible", exit_code=4)
        return original(env, reference_model, ids, domain, company, failure)

    monkeypatch.setattr(writes, "_ensure_ids", ensure)
    with pytest.raises(Failure) as error:
        writes._replace_bank_counterparts(object(), _counterparts(), 7, Failure)
    assert error.value.code == "record_not_found" and transaction.native_calls == []


@pytest.mark.parametrize("taxed", [False, True])
def test_manual_counterparts_can_undo_using_native_action(monkeypatch, taxed) -> None:
    transaction = _transaction()
    _scope(monkeypatch, transaction)
    writes._replace_bank_counterparts(object(), _counterparts(), 7, Failure)
    if taxed:
        transaction.move_id.line_ids[1].tax_ids = Records([SimpleNamespace(id=90)])
    result, replay = writes._unmatch_bank_transaction(object(), {"transaction_id": 41}, 7, Failure)
    assert not replay and not result["reconciled"] and transaction.undo_calls == [True]
    result, replay = writes._unmatch_bank_transaction(object(), {"transaction_id": 41}, 7, Failure)
    assert replay and transaction.undo_calls == [True] and not result["reconciled"]


def test_manual_unmatch_rejects_source_link_without_deletion(monkeypatch) -> None:
    transaction = _transaction()
    _scope(monkeypatch, transaction)
    transaction.move_id.line_ids[1].account_id.id = 20
    transaction.move_id.line_ids[1].reconciled_lines_ids = Records([SimpleNamespace(id=90)])
    with pytest.raises(Failure) as error:
        writes._unmatch_bank_transaction(object(), {"transaction_id": 41}, 7, Failure)
    assert error.value.code == "state_conflict" and transaction.undo_calls == []


def test_manual_unmatch_requires_pnl_company_accounts_and_native_reviewer(monkeypatch) -> None:
    transaction = _transaction()
    references = _scope(monkeypatch, transaction)
    writes._replace_bank_counterparts(object(), _counterparts(), 7, Failure)
    transaction.checked = True
    transaction.move_id._is_user_able_to_review = lambda: False
    with pytest.raises(Failure, match="Validated") as error:
        writes._unmatch_bank_transaction(object(), {"transaction_id": 41}, 7, Failure)
    assert error.value.code == "business_rule_error" and transaction.undo_calls == []
    assert any(model == "account.account" and ids == {20, 21} and ("company_ids", "in", [7]) in domain for model, ids, domain in references)


def test_bank_metadata_update_only_writes_requested_fields_and_clear_false(monkeypatch) -> None:
    transaction = _transaction()
    _scope(monkeypatch, transaction)
    transaction.account_number = "ACC-1"
    result, replay = writes._update_bank_transaction(object(), {"transaction_id": 41, "changes": {"account_number": None, "partner_name": "Supplier"}}, 7, Failure)
    assert not replay and result["id"] == 41
    assert transaction.write_calls == [{"account_number": False, "partner_name": "Supplier"}]
    _result, replay = writes._update_bank_transaction(object(), {"transaction_id": 41, "changes": {"account_number": None, "partner_name": "Supplier"}}, 7, Failure)
    assert replay and len(transaction.write_calls) == 1


def test_bank_metadata_update_cannot_reset_manual_counterparts(monkeypatch) -> None:
    transaction = _transaction()
    _scope(monkeypatch, transaction)
    writes._replace_bank_counterparts(object(), _counterparts(), 7, Failure)
    with pytest.raises(Failure) as error:
        writes._update_bank_transaction(object(), {"transaction_id": 41, "changes": {"partner_name": "Supplier"}}, 7, Failure)
    assert error.value.code == "state_conflict" and transaction.write_calls == []


@pytest.mark.parametrize("field,value", [("account_number", " account"), ("partner_name", ""), ("account_number", True)])
def test_bank_metadata_runtime_rejects_untyped_or_untrimmed_values(field, value) -> None:
    assert not writes._valid_parameters("bank.transaction.update", {"transaction_id": 41, "changes": {field: value}})


@pytest.mark.parametrize("include_metadata", [False, True])
def test_record_metadata_keeps_omission_and_validates_native_partner(monkeypatch, include_metadata) -> None:
    transaction = _transaction()
    references = _scope(monkeypatch, transaction)
    created = []

    class Model:
        def search(self, *_args, **_kwargs):
            return Records()

        def create(self, values):
            created.append(dict(values))
            for field in ("account_number", "partner_name"):
                if field in values:
                    setattr(transaction, field, values[field])
            if include_metadata:
                transaction.partner_id = SimpleNamespace(id=8)
            return transaction

    monkeypatch.setattr(writes, "_scoped", lambda *_args: Model())
    parameters = {"journal_id": 9, "date": "2026-10-02", "amount": "100", "payment_ref": "Bank movement", "partner_id": None}
    if include_metadata:
        parameters.update(account_number="ACC-1", partner_name=None)
    assert writes._valid_parameters("bank.transaction.record", parameters)
    _result, replay = writes._record_bank_transaction(object(), parameters, 7, "bank-key", "marker", Failure)
    assert not replay
    assert ("account_number" in created[0]) == include_metadata
    assert ("partner_name" in created[0]) == include_metadata
    if include_metadata:
        assert created[0]["partner_name"] is False and transaction.partner_id.id == 8
        assert ("res.partner", {8}, [("company_id", "in", [False, 7])]) in references


def test_record_metadata_replay_requires_actual_requested_values(monkeypatch) -> None:
    transaction = _transaction()
    _scope(monkeypatch, transaction)
    transaction.invoice_origin = "marker"
    transaction.account_number = "CHANGED"
    model = SimpleNamespace(search=lambda *_args, **_kwargs: Records([transaction]))
    monkeypatch.setattr(writes, "_scoped", lambda *_args: model)
    with pytest.raises(Failure) as error:
        writes._record_bank_transaction(object(), {"account_number": "ACC-1"}, 7, "bank-key", "marker", Failure)
    assert error.value.code == "idempotency_conflict"


def test_bank_transaction_old_projection_does_not_read_omitted_metadata() -> None:
    transaction = _transaction()
    del transaction.account_number
    del transaction.partner_name
    assert set(writes._bank_transaction_actual_values(transaction)) == {"date", "amount", "payment_ref", "partner_id"}


def test_statement_requested_name_and_date_bind_actual_state_without_omitted_defaults(monkeypatch) -> None:
    statement = SimpleNamespace(id=50, company_id=SimpleNamespace(id=7), reference="REF", name="Old", date="2026-10-01", balance_end_real=100, line_ids=Records(), invalidate_recordset=lambda *_args: None)
    calls = []

    def write(values):
        calls.append(values)
        for field, value in values.items():
            setattr(statement, field, value)

    statement.write = write
    monkeypatch.setattr(writes, "_search_one", lambda *_args: statement)
    monkeypatch.setattr(writes, "_bank_statement_result", lambda *_args: {"id": 50})
    parameters = {"statement_id": 50, "changes": {"name": "October", "date": "2026-10-02"}}
    assert writes._valid_parameters("bank.statement.update", parameters)
    _result, replay = writes._update_bank_statement(object(), parameters, 7, Failure)
    assert not replay and calls == [{"name": "October", "date": "2026-10-02"}]
    _result, replay = writes._update_bank_statement(object(), parameters, 7, Failure)
    assert replay and len(calls) == 1


def test_statement_create_supplies_optional_name_date_to_native_create(monkeypatch) -> None:
    transaction = _transaction()
    transaction.statement_id = False
    transaction.internal_index = "INDEX-1"
    statement = SimpleNamespace(id=50, company_id=transaction.company_id, journal_id=transaction.journal_id, reference="REF", name="October", date="2026-10-02", balance_end_real=100, line_ids=Records([transaction]), invalidate_recordset=lambda *_args: None)
    created = []
    model = SimpleNamespace(
        search=lambda *_args, **_kwargs: Records(), with_context=lambda **_kwargs: model,
        create=lambda values: created.append(dict(values)) or statement,
    )
    monkeypatch.setitem(sys.modules, "odoo", SimpleNamespace(Command=SimpleNamespace(set=lambda ids: (6, 0, ids))))
    monkeypatch.setattr(writes, "_scoped", lambda *_args: model)
    monkeypatch.setattr(writes, "_ensure_ids", lambda *_args: Records([transaction]))
    monkeypatch.setattr(writes, "_bank_statement_transactions_are_contiguous", lambda *_args: True)
    monkeypatch.setattr(writes, "_bank_statement_result", lambda *_args: {"id": 50})
    parameters = {"transaction_ids": [41], "reference": "REF", "balance_end_real": "100", "name": "October", "date": "2026-10-02"}
    assert writes._valid_parameters("bank.statement.create", parameters)
    _result, replay = writes._create_bank_statement(object(), parameters, 7, Failure)
    assert not replay and created[0]["name"] == "October" and created[0]["date"] == "2026-10-02"


@pytest.mark.parametrize("changes", [{"name": None}, {"name": ""}, {"name": " leading"}, {"date": None}, {"date": "2026-2-3"}, {"date": True}])
def test_statement_name_date_runtime_fields_are_nonnullable_and_closed(changes) -> None:
    assert not writes._valid_parameters("bank.statement.update", {"statement_id": 50, "changes": changes})


def test_statement_legacy_match_does_not_read_omitted_name_date() -> None:
    statement = SimpleNamespace(company_id=SimpleNamespace(id=7), line_ids=Records(), reference=False, balance_end_real=0)
    assert writes._statement_matches(statement, [], None, Decimal(0), 7)
