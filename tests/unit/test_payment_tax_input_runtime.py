from copy import deepcopy
from types import SimpleNamespace

import pytest
from test_core_writes_runtime import Env, Failure, Records, _entry_parameters, _payload

from odoo_accounting_cli_v4.bridge import core_writes_runtime as writes


def tax_line(**changes):
    return {
        "name": "Manual base", "account_id": 11, "partner_id": None,
        "debit": "100.00", "credit": "0", "tax_ids": [31],
        "tax_tag_ids": [41], "tax_repartition_line_id": None,
        "tax_base_amount": "-100.00", **changes,
    }


def test_entry_tax_values_are_native_commands_and_preserve_omission():
    row = tax_line(tax_ids=[], tax_tag_ids=[], tax_repartition_line_id=None, tax_base_amount="-0.00")
    values = writes._replacement_commands("journal_entry.lines.add", [row])[1][2]
    assert values["tax_ids"] == values["tax_tag_ids"] == [(6, 0, [])]
    assert values["tax_repartition_line_id"] is False
    assert values["tax_base_amount"] == 0.0
    old = {field: value for field, value in row.items() if field not in writes._ENTRY_TAX_FIELDS}
    assert not writes._ENTRY_TAX_FIELDS & writes._replacement_commands("journal_entry.lines.add", [old])[1][2].keys()


@pytest.mark.parametrize("changes", [
    {"tax_ids": [True]}, {"tax_ids": [2, 1]}, {"tax_tag_ids": [1, 1]},
    {"tax_tag_ids": list(range(1, 102))}, {"tax_repartition_line_id": False},
    {"tax_base_amount": "NaN"}, {"tax_line_id": 31},
])
def test_complete_tax_input_rejects_invalid_closed_values(changes):
    assert not writes._valid_entry_lines([
        tax_line(**changes), {"name": "Counterpart", "account_id": 12, "partner_id": None, "debit": "0", "credit": "100"},
    ])


def test_tax_projection_compares_explicit_values_but_ignores_omitted_fields():
    rows = [tax_line()]
    current = writes._normalized_entry_replacement_lines(rows, 1)
    before = deepcopy(current)
    assert writes._entry_lines_match(current, rows, 1)
    assert current == before
    drifted = deepcopy(current)
    drifted[0]["tax_tag_ids"] = [42]
    assert not writes._entry_lines_match(drifted, rows, 1)
    old = [{field: value for field, value in rows[0].items() if field not in writes._ENTRY_TAX_FIELDS}]
    assert writes._entry_lines_match(drifted, old, 1)
    cleared = tax_line(tax_ids=[], tax_tag_ids=[], tax_repartition_line_id=None, tax_base_amount="0.00")
    assert writes._entry_lines_match(writes._normalized_entry_replacement_lines([cleared], 1), [cleared], 1)


def test_tax_current_projection_is_typed_and_accepts_old_lightweight_fakes():
    line = SimpleNamespace(tax_ids=SimpleNamespace(ids=[3, 2]), tax_tag_ids=SimpleNamespace(ids=[8]),
                           tax_repartition_line_id=SimpleNamespace(id=9), tax_base_amount=-100.0)
    assert writes._journal_item_current(line, writes._ENTRY_TAX_FIELDS) == {
        "tax_ids": [2, 3], "tax_tag_ids": [8], "tax_repartition_line_id": 9, "tax_base_amount": "-100",
    }
    assert writes._journal_item_current(SimpleNamespace(), writes._ENTRY_TAX_FIELDS) == {
        "tax_ids": [], "tax_tag_ids": [], "tax_repartition_line_id": None, "tax_base_amount": "0",
    }


def test_tax_references_use_ordinary_company_and_tax_tag_domains(monkeypatch):
    calls = []
    monkeypatch.setattr(writes, "_ensure_ids", lambda env, model, ids, domain, co, error: calls.append((model, ids, domain, co)))
    writes._validate_entry_tax_references(None, [tax_line(tax_repartition_line_id=51)], 7, Failure)
    assert calls == [
        ("account.tax", {31}, [("company_id", "=", 7)], 7),
        ("account.account.tag", {41}, [("applicability", "=", "taxes")], 7),
        ("account.tax.repartition.line", {51}, [("company_id", "=", 7)], 7),
    ]


def test_payment_replay_preflight_does_not_recompute_native_availability(monkeypatch):
    journal = SimpleNamespace(id=9)
    calls = []
    monkeypatch.setattr(writes, "_search_one", lambda *args: journal)
    monkeypatch.setattr(writes, "_ensure_ids", lambda env, model, ids, domain, co, error: calls.append((model, domain)))
    params = {"journal_id": 9, "payment_method_line_id": 21, "partner_bank_id": 31}
    assert writes._register_payment_references(None, params, "outbound", 7, Failure) == {
        "payment_method_line_id": 21, "partner_bank_id": 31,
    }
    assert calls == [
        ("account.payment.method.line", [("journal_id", "=", 9), ("payment_type", "=", "outbound")]),
        ("res.partner.bank", [("company_id", "in", [False, 7])]),
    ]
    assert writes._register_payment_references(None, {}, "inbound", 7, Failure) == {}


@pytest.mark.parametrize("can_edit,count,group,accepted", [
    (True, 1, False, True), (True, 2, True, True),
    (True, 2, False, False), (False, 1, True, False),
])
def test_native_bank_editability_matches_actual_payment_action(can_edit, count, group, accepted):
    wizard = SimpleNamespace(
        can_edit_wizard=can_edit, batches=[{"lines": list(range(count))}], group_payment=group,
        payment_type="outbound", partner_bank_id=SimpleNamespace(id=31),
        available_partner_bank_ids=SimpleNamespace(ids=[31]),
    )
    if accepted:
        writes._validate_register_wizard_references(wizard, {"partner_bank_id": 31}, "outbound", Failure)
    else:
        with pytest.raises(Failure) as caught:
            writes._validate_register_wizard_references(wizard, {"partner_bank_id": 31}, "outbound", Failure)
        assert (caught.value.code, caught.value.exit_code) == ("state_conflict", 5)


def test_native_method_selection_is_checked_before_payment_action():
    wizard = SimpleNamespace(payment_type="inbound", payment_method_line_id=SimpleNamespace(id=21),
                             available_payment_method_line_ids=SimpleNamespace(ids=[22]))
    with pytest.raises(Failure) as caught:
        writes._validate_register_wizard_references(wizard, {"payment_method_line_id": 21}, "inbound", Failure)
    assert (caught.value.code, caught.value.exit_code) == ("business_rule_error", 6)
    writes._validate_register_wizard_references(SimpleNamespace(), {}, "inbound", Failure)


@pytest.mark.parametrize("capability_id,move_type,direction", [
    ("receivable.payment.register", "out_invoice", "inbound"),
    ("receivable.payment.register", "out_refund", "outbound"),
    ("payable.payment.register", "in_invoice", "outbound"),
    ("payable.payment.register", "in_refund", "inbound"),
])
def test_explicit_payment_replay_binds_marker_direction_and_actual_reference_ids(monkeypatch, capability_id, move_type, direction):
    env = Env()
    source = env.existing_move(100, move_type=move_type, residual="125.50")
    params = {"move_id": source.id, "journal_id": env.bank_journal.id, "payment_date": "2025-02-04"}
    payload = _payload(capability_id, params, key=f"{capability_id}:{source.id}")
    first = writes.dispatch(env, payload, 7, Failure)
    payment = env.models["account.payment"].browse(first["result"]["id"])
    payment.records[0].payment_method_line_id = SimpleNamespace(id=21)
    params["payment_method_line_id"] = 21
    monkeypatch.setattr(writes, "_register_payment_references", lambda env, values, kind, co, error: {"payment_method_line_id": 21} if "payment_method_line_id" in values else {})
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, payload, 7, Failure)
    assert caught.value.code == "idempotency_conflict"
    payment.move_id.records[0].invoice_origin = writes._operation_marker(capability_id, payload["idempotency_key"], params)
    assert payment.payment_type == direction
    assert writes.dispatch(env, payload, 7, Failure)["idempotent_replay"] is True
    payment.records[0].payment_method_line_id = SimpleNamespace(id=22)
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, payload, 7, Failure)
    assert caught.value.code == "idempotency_conflict"
    assert len([call for call in env.calls if call[0] == "action_create_payments"]) == 1


def test_old_complete_entry_parameters_do_not_gain_new_tax_defaults():
    env = Env()
    params = _entry_parameters(env)
    assert writes._valid_parameters("journal_entry.create", params, 7)
    assert all(not writes._ENTRY_TAX_FIELDS & row.keys() for row in params["lines"])


def test_new_tax_update_replay_rejects_unselected_source_linked_rows(monkeypatch):
    env = Env()
    move = env.existing_move(31, move_type="entry", residual="100")
    move.state = "draft"
    move.journal_id = env.general_journal
    linked = env.add("account.move.line", 41, _fields={"sale_line_ids": object()}, sale_line_ids=[1])
    selected = env.add("account.move.line", 42)
    move.line_ids = Records(env, "account.move.line", [linked, selected])
    monkeypatch.setattr(writes, "_search_one", lambda *args: move)
    monkeypatch.setattr(writes, "_ensure_ids", lambda env, model, ids, *args: move.line_ids.filtered(lambda line: line.id in ids) if model == "account.move.line" else [])
    monkeypatch.setattr(writes, "_validate_line_analytic_references", lambda *args: None)
    with pytest.raises(Failure) as caught:
        writes._write_journal_item_processing(
            env, "journal_entry.lines.update",
            {"move_id": move.id, "lines": [{"line_id": selected.id, "changes": {"tax_ids": []}}]},
            7, Failure,
        )
    assert (caught.value.code, caught.value.exit_code) == ("business_rule_error", 6)
