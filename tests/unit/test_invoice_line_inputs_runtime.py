from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from types import SimpleNamespace

import pytest

from odoo_accounting_cli_v4.bridge import core_writes_runtime as runtime


class Failure(Exception):
    def __init__(self, code, message, *, exit_code, retryable, details):
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


class Records(list):
    @property
    def ids(self):
        return [record.id for record in self]

    def __getattr__(self, name):
        assert len(self) == 1
        return getattr(self[0], name)

    def __or__(self, other):
        return Records({record.id: record for record in (*self, *other)}.values())

    def filtered(self, predicate):
        return Records(record for record in self if predicate(record))


def ref(record_id):
    return Records([SimpleNamespace(id=record_id)]) if record_id else Records()


LINE = {"name": "Service", "product_id": 21, "account_id": 31, "quantity": "2", "price_unit": "25", "discount": "0", "tax_ids": []}


class Line:
    def __init__(self, record_id, values):
        self.id = record_id
        self.sequence = 10
        self.display_type = "product"
        self.product_uom_id = ref(11)
        self.deductible_amount = 100
        self.tax_ids = ref(None)
        self.analytic_distribution = False
        self.deferred_start_date = self.deferred_end_date = False
        self.sale_line_ids = self.purchase_line_id = Records()
        self._fields = {"sale_line_ids": object(), "purchase_line_id": object()}
        self.writes = []
        self.write({**LINE, **values})
        self.writes.clear()

    def write(self, values):
        self.writes.append(deepcopy(values))
        for field, value in values.items():
            if field in {"product_id", "account_id", "product_uom_id"}:
                value = ref(value)
            elif field == "tax_ids":
                value = Records(SimpleNamespace(id=record_id) for record_id in (value[0][2] if value and isinstance(value[0], tuple) else value))
            setattr(self, field, value)


class Move:
    def __init__(self, move_type="in_invoice", lines=()):
        self.id = 101
        self.move_type = move_type
        self.state = "draft"
        self.company_id = ref(7)
        self.partner_id = ref(41)
        self.journal_id = ref(51)
        self.invoice_origin = False
        self.invoice_line_ids = Records(lines)
        for line in self.invoice_line_ids:
            line.move_id = ref(self.id)
            line.company_id = self.company_id
        self.writes = []

    def write(self, values):
        self.writes.append(deepcopy(values))
        if "invoice_origin" in values:
            self.invoice_origin = values["invoice_origin"]
        for command, _record_id, line_values in values.get("invoice_line_ids", []):
            if command == 5:
                self.invoice_line_ids.clear()
            else:
                assert command == 0
                self.invoice_line_ids.append(Line(201 + len(self.invoice_line_ids), line_values))


class Model:
    def __init__(self, records=()):
        self.records = Records(records)
        self._fields = {field: object() for field in runtime._INVOICE_LINE_INPUT_FIELDS}
        self.searches = []

    def search(self, domain, **_kwargs):
        self.searches.append(deepcopy(domain))
        requested = next((value for field, operation, value in domain if field == "id" and operation == "in"), self.records.ids)
        return Records(record for record in self.records if record.id in requested)

    def browse(self, ids):
        return Records(record for record in self.records if record.id in ids)


def native_models(monkeypatch):
    product = SimpleNamespace(id=21, uom_id=ref(11), uom_ids=ref(12))
    models = {"account.move.line": Model(), "product.product": Model([product]), "uom.uom": Model([SimpleNamespace(id=value) for value in (11, 12, 13)]),
              "res.partner": Model([SimpleNamespace(id=41)]), "account.account": Model([SimpleNamespace(id=31)])}
    env = SimpleNamespace(uid=5, su=False)

    def scoped(selected, model, company_id):
        assert selected is env and selected.uid == 5 and not selected.su and company_id == 7
        return models.setdefault(model, Model())

    monkeypatch.setattr(runtime, "_scoped", scoped)
    monkeypatch.setattr(runtime, "_validate_line_analytic_references", lambda *_args: None)
    monkeypatch.setattr(runtime, "_move_result", lambda move, company, source_id=None: {"id": move.id, "source_id": source_id})
    return env, models


@pytest.mark.parametrize("capability", ["customer_invoice.create", "vendor_bill.create", "invoice.line.create", "invoice.lines.replace", "customer_credit_note.create", "vendor_refund.create"])
@pytest.mark.parametrize("amount", ["0", "50.0", "50.001", "100"])
def test_optional_full_line_inputs_validate_without_forcing_canonical_or_two_places(capability, amount):
    line = {**LINE, "product_uom_id": 12, "deductible_amount": amount}
    if capability in {"customer_invoice.create", "vendor_bill.create"}:
        parameters = {"partner_id": 41, "journal_id": 51, "invoice_date": "2026-10-02", "currency_id": 61, "lines": [line]}
    elif capability == "invoice.line.create":
        parameters = {"move_id": 101, "line": line}
    else:
        parameters = {"move_id": 101, "lines": [line], **({"date": "2026-10-02", "reason": "Adjustment"} if capability.endswith("note.create") or capability == "vendor_refund.create" else {})}
    assert runtime._valid_parameters(capability, parameters)


@pytest.mark.parametrize("changes", [{"product_uom_id": 12}, {"deductible_amount": "50.001"}, {"product_id": 21, "product_uom_id": 12}])
def test_partial_inputs_validate_with_effective_product_to_be_checked_natively(changes):
    assert runtime._valid_parameters("invoice.line.update", {"move_id": 101, "line_id": 201, "changes": changes})


@pytest.mark.parametrize("values", [{"product_uom_id": None}, {"product_uom_id": True}, {"product_uom_id": 0}, {"product_id": None, "product_uom_id": 11},
                                    {"deductible_amount": None}, {"deductible_amount": False}, {"deductible_amount": 50}, {"deductible_amount": "-1"},
                                    {"deductible_amount": "101"}, {"deductible_amount": "1e1"}, {"deductible_amount": "50\n"},
                                    {"deductible_amount": " 50"}, {"deductible_amount": "+50"}, {"deductible_amount": "-0"}])
def test_invalid_new_line_inputs_are_rejected_by_both_shared_validators(values):
    assert not runtime._valid_document_lines([{**LINE, **values}])
    assert not runtime._valid_invoice_line_values({**LINE, **values}, partial=False)
    assert not runtime._valid_invoice_line_values(values, partial=True)


def test_native_reference_check_uses_product_allowed_units_and_ordinary_visibility(monkeypatch):
    env, models = native_models(monkeypatch)
    runtime._validate_invoice_line_inputs(env, [{**LINE, "product_uom_id": 12}], 7, Failure, "in_invoice")
    assert ("company_id", "in", [False, 7]) in models["product.product"].searches[0]
    assert models["uom.uom"].searches == [[("id", "in", [12])]]
    for values, code in (({"product_uom_id": 13}, "business_rule_error"), ({"product_uom_id": 99}, "record_not_found"),
                         ({"product_id": None, "product_uom_id": 11}, "business_rule_error")):
        with pytest.raises(Failure) as caught:
            runtime._validate_invoice_line_inputs(env, [{**LINE, **values}], 7, Failure, "in_invoice")
        assert caught.value.code == code


@pytest.mark.parametrize("move_type", ["out_invoice", "out_refund", "in_invoice", "in_refund"])
def test_native_deductibility_constraint_is_purchase_only_except_explicit_100(monkeypatch, move_type):
    env, _models = native_models(monkeypatch)
    runtime._validate_invoice_line_inputs(env, [{**LINE, "deductible_amount": "100.0"}], 7, Failure, move_type)
    if move_type.startswith("in_"):
        runtime._validate_invoice_line_inputs(env, [{**LINE, "deductible_amount": "50.001"}], 7, Failure, move_type)
    else:
        with pytest.raises(Failure) as caught:
            runtime._validate_invoice_line_inputs(env, [{**LINE, "deductible_amount": "50"}], 7, Failure, move_type)
        assert caught.value.code == "business_rule_error"


def test_omitted_inputs_never_add_a_global_unit_or_native_field_gate(monkeypatch):
    monkeypatch.setattr(runtime, "_scoped", lambda *_args: pytest.fail("No new lookup for old inputs"))
    runtime._validate_invoice_line_inputs(object(), [LINE], 7, Failure, "out_invoice")
    assert runtime._invoice_line_inputs_match(object(), [LINE])
    assert all("uom.uom" not in runtime._MODELS[capability] for capability in ("customer_invoice.create", "vendor_bill.create", "invoice.line.create", "invoice.line.update", "invoice.lines.replace", "customer_credit_note.create", "vendor_refund.create"))


def test_missing_native_input_field_rejects_only_the_explicit_input(monkeypatch):
    env, models = native_models(monkeypatch)
    models["account.move.line"]._fields.clear()
    runtime._validate_invoice_line_inputs(env, [LINE], 7, Failure, "in_invoice")
    with pytest.raises(Failure) as caught:
        runtime._validate_invoice_line_inputs(env, [{**LINE, "deductible_amount": "100"}], 7, Failure, "in_invoice")
    assert caught.value.code == "business_rule_error"


@pytest.mark.parametrize("field,value", [("product_uom_id", 12), ("deductible_amount", "50")])
def test_partial_update_missing_native_field_is_rejected_before_reading_it(monkeypatch, field, value):
    line = Line(201, LINE)
    delattr(line, field)
    move = Move(lines=[line])
    env, models = prepare_line_route(monkeypatch, move)
    models["account.move.line"]._fields.pop(field)
    with pytest.raises(Failure) as caught:
        runtime._update_invoice_line(env, {"move_id": 101, "line_id": 201, "changes": {field: value}}, 7, Failure)
    assert caught.value.code == "business_rule_error" and not line.writes
    assert not runtime._update_invoice_line(env, {"move_id": 101, "line_id": 201, "changes": {"name": "Legacy write"}}, 7, Failure)[1]


def test_comparisons_only_include_requested_inputs_and_compare_native_numbers():
    line = Line(201, {"deductible_amount": 50, "product_uom_id": 12})
    move = Move(lines=[line])
    assert runtime._current_invoice_line(line) == runtime._normalized_invoice_replacement_lines([LINE])[0]
    assert runtime._invoice_lines_match(runtime._current_invoice_lines(move), [LINE])
    requested = {**LINE, "deductible_amount": "50.0"}
    assert runtime._invoice_lines_match(runtime._current_invoice_lines(move, [requested]), [requested])
    requested["product_uom_id"] = 11
    assert not runtime._invoice_lines_match(runtime._current_invoice_lines(move, [requested]), [requested])
    assert not runtime._invoice_line_inputs_match(move, [requested])


def prepare_line_route(monkeypatch, move):
    env, models = native_models(monkeypatch)
    monkeypatch.setattr(runtime, "_lifecycle_move", lambda *_args: move)
    monkeypatch.setattr(runtime, "_search_one", lambda _env, model, domain, *_args, **_kwargs: next(line for line in move.invoice_line_ids if ("id", "=", line.id) in domain) if model == "account.move.line" else move)
    return env, models


@pytest.mark.parametrize("capability", ["invoice.line.create", "invoice.line.update", "invoice.lines.replace"])
def test_actual_line_routes_write_optional_native_values_and_replay(monkeypatch, capability):
    requested = {**LINE, "product_uom_id": 12, "deductible_amount": "50.001"}
    move = Move(lines=[] if capability == "invoice.line.create" else [Line(201, LINE)])
    env, _models = prepare_line_route(monkeypatch, move)
    parameters = {"move_id": 101, **({"line": requested} if capability == "invoice.line.create" else {"line_id": 201, "changes": {"product_uom_id": 12, "deductible_amount": "50.001"}} if capability == "invoice.line.update" else {"lines": [requested]})}
    result, replay = runtime._dispatch_allowed(env, capability, parameters, 7, "key", "marker", Failure)
    assert result["id"] == 101 and not replay
    line = move.invoice_line_ids[0]
    assert line.product_uom_id.id == 12 and line.deductible_amount == Decimal("50.001")
    assert runtime._dispatch_allowed(env, capability, parameters, 7, "key", "marker", Failure)[1]


def test_source_same_value_inputs_replay_or_preserve_other_existing_writes(monkeypatch):
    line = Line(201, {"deductible_amount": 50})
    line.sale_line_ids = ref(401)
    move = Move(lines=[line])
    env, _models = prepare_line_route(monkeypatch, move)
    parameters = {"move_id": 101, "line_id": 201, "changes": {"product_uom_id": 11, "deductible_amount": "50.0"}}
    assert runtime._update_invoice_line(env, parameters, 7, Failure)[1]
    assert not line.writes
    parameters["changes"]["name"] = "Preserved source"
    assert not runtime._update_invoice_line(env, parameters, 7, Failure)[1]
    assert line.name == "Preserved source"
    for changes in ({"product_uom_id": 12}, {"deductible_amount": "0"}):
        with pytest.raises(Failure) as caught:
            runtime._update_invoice_line(env, {"move_id": 101, "line_id": 201, "changes": changes}, 7, Failure)
        assert caught.value.code == "business_rule_error"


@pytest.mark.parametrize("capability", ["customer_invoice.create", "vendor_bill.create"])
def test_document_create_payload_and_replay_verify_explicit_native_inputs(monkeypatch, capability):
    env, models = native_models(monkeypatch)
    move_type = "out_invoice" if capability == "customer_invoice.create" else "in_invoice"
    created = []

    def create(values):
        move = Move(move_type)
        move.write(values)
        created.append(move)
        return move

    models["account.move"] = SimpleNamespace(create=create)
    monkeypatch.setattr(runtime, "_existing_move_for_key", lambda *_args: created[0] if created else None)
    parameters = {"partner_id": 41, "journal_id": 51, "invoice_date": "2026-10-02", "currency_id": 61,
                  "lines": [{**LINE, "product_uom_id": 12, "deductible_amount": "100.0" if move_type == "out_invoice" else "50.001"}]}
    for model, record_id in (("account.journal", 51), ("res.partner", 41), ("res.currency", 61), ("account.account", 31)):
        models[model] = Model([SimpleNamespace(id=record_id)])
    assert not runtime._dispatch_allowed(env, capability, parameters, 7, "key", "marker", Failure)[1]
    move = created[0]
    values = move.writes[0]["invoice_line_ids"][0][2]
    assert values["product_uom_id"] == 12 and values["deductible_amount"] == Decimal(parameters["lines"][0]["deductible_amount"])
    assert runtime._dispatch_allowed(env, capability, parameters, 7, "key", "marker", Failure)[1]
    move.invoice_line_ids[0].product_uom_id = ref(11)
    with pytest.raises(Failure) as caught:
        runtime._dispatch_allowed(env, capability, parameters, 7, "key", "marker", Failure)
    assert caught.value.code == "idempotency_conflict" and len(created) == 1


def test_document_legacy_replay_does_not_read_or_bind_omitted_native_inputs(monkeypatch):
    move = Move(lines=[Line(201, {"product_uom_id": 12, "deductible_amount": 50})])
    monkeypatch.setattr(runtime, "_existing_move_for_key", lambda *_args: move)
    monkeypatch.setattr(runtime, "_scoped", lambda *_args: pytest.fail("Legacy replay needs no new field or unit lookup"))
    monkeypatch.setattr(runtime, "_move_result", lambda *_args: {"id": 101})
    assert runtime._create_document(object(), "customer_invoice.create", {"lines": [LINE]}, 7, "key", "marker", Failure) == ({"id": 101}, True)


def test_partial_update_does_not_claim_success_when_native_ignores_unit(monkeypatch):
    line = Line(201, LINE)
    move = Move(lines=[line])
    env, _models = prepare_line_route(monkeypatch, move)
    line.write = lambda _values: None
    with pytest.raises(Failure) as caught:
        runtime._update_invoice_line(env, {"move_id": 101, "line_id": 201, "changes": {"product_uom_id": 12}}, 7, Failure)
    assert caught.value.code == "odoo_write_error"


def test_partial_unit_only_update_accepts_native_price_and_tax_recomputation(monkeypatch):
    line = Line(201, LINE)
    move = Move(lines=[line])
    env, _models = prepare_line_route(monkeypatch, move)
    write = line.write

    def native_write(values):
        write(values)
        line.price_unit = 72
        line.tax_ids = ref(91)

    line.write = native_write
    parameters = {"move_id": 101, "line_id": 201, "changes": {"product_uom_id": 12}}
    assert not runtime._update_invoice_line(env, parameters, 7, Failure)[1]
    assert line.price_unit == 72 and line.tax_ids.ids == [91]
    assert runtime._update_invoice_line(env, parameters, 7, Failure)[1]
    assert len(line.writes) == 1


def test_partial_unit_update_still_requires_explicit_price_to_persist(monkeypatch):
    line = Line(201, LINE)
    move = Move(lines=[line])
    env, _models = prepare_line_route(monkeypatch, move)
    write = line.write

    def native_write(values):
        write(values)
        line.price_unit = 72

    line.write = native_write
    with pytest.raises(Failure) as caught:
        runtime._update_invoice_line(env, {"move_id": 101, "line_id": 201, "changes": {"product_uom_id": 12, "price_unit": "11"}}, 7, Failure)
    assert caught.value.code == "odoo_write_error"


def test_partial_quantity_unit_price_and_tax_patch_persists_all_requested_values(monkeypatch):
    line = Line(201, LINE)
    move = Move(lines=[line])
    env, _models = prepare_line_route(monkeypatch, move)
    changes = {"product_uom_id": 12, "quantity": "3", "price_unit": "11", "tax_ids": []}
    parameters = {"move_id": 101, "line_id": 201, "changes": changes}
    assert not runtime._update_invoice_line(env, parameters, 7, Failure)[1]
    assert line.writes == [{**changes, "quantity": Decimal(3), "price_unit": Decimal(11), "tax_ids": [(6, 0, [])]}]
    assert runtime._update_invoice_line(env, parameters, 7, Failure)[1]


@pytest.mark.parametrize("field,value", [("id", 202), ("move_id", ref(102)), ("company_id", ref(8)), ("display_type", "line_section")])
def test_partial_unit_recomputation_cannot_change_native_line_identity(monkeypatch, field, value):
    line = Line(201, LINE)
    move = Move(lines=[line])
    env, _models = prepare_line_route(monkeypatch, move)
    write = line.write

    def native_write(values):
        write(values)
        setattr(line, field, value)

    line.write = native_write
    with pytest.raises(Failure) as caught:
        runtime._update_invoice_line(env, {"move_id": 101, "line_id": 201, "changes": {"product_uom_id": 12}}, 7, Failure)
    assert caught.value.code == "odoo_write_error"


@pytest.mark.parametrize("changes", [{"quantity": "3"}, {"deductible_amount": "50"}])
def test_omitted_unit_update_retains_whole_line_native_verification(monkeypatch, changes):
    line = Line(201, LINE)
    move = Move(lines=[line])
    env, _models = prepare_line_route(monkeypatch, move)
    write = line.write

    def native_write(values):
        write(values)
        line.price_unit = 72

    line.write = native_write
    with pytest.raises(Failure) as caught:
        runtime._update_invoice_line(env, {"move_id": 101, "line_id": 201, "changes": changes}, 7, Failure)
    assert caught.value.code == "odoo_write_error"


def test_explicit_unit_native_read_acl_denial_is_not_a_global_legacy_gate(monkeypatch):
    class AccessError(Exception):
        pass

    move = Move()
    env, models = prepare_line_route(monkeypatch, move)

    def denied(*_args, **_kwargs):
        raise AccessError("Unit read denied")

    models["uom.uom"].search = denied
    parameters = {"move_id": 101, "line": {**LINE, "product_uom_id": 12}}
    monkeypatch.setattr(runtime, "_validated_payload", lambda *_args: ("invoice.line.create", "key", parameters, "marker"))
    monkeypatch.setattr(runtime, "_gate", lambda *_args: (True, True, True))
    with pytest.raises(Failure) as caught:
        runtime.dispatch(env, {}, 7, Failure)
    assert caught.value.code == "unauthorized" and not move.writes
    parameters["line"].pop("product_uom_id")
    assert not runtime._create_invoice_line(env, parameters, 7, Failure)[1]


@pytest.mark.parametrize("capability", ["customer_credit_note.create", "vendor_refund.create"])
def test_custom_refund_native_route_preserves_explicit_inputs_and_replay(monkeypatch, capability):
    env, models = native_models(monkeypatch)
    source = Move("out_invoice" if capability == "customer_credit_note.create" else "in_invoice")
    source.state = "posted"
    refund = Move("out_refund" if capability == "customer_credit_note.create" else "in_refund")
    refund.id = 102
    refund.reversed_entry_id = source
    refunds = Records()
    models["account.move"] = SimpleNamespace(search=lambda *_args, **_kwargs: refunds)
    monkeypatch.setattr(runtime, "_search_one", lambda _env, _model, domain, *_args, **_kwargs: refund if ("id", "=", 102) in domain else source)
    monkeypatch.setattr(runtime, "_validate_invoice_line_references", lambda *_args: None)
    wizard = SimpleNamespace(new_move_ids=Records([refund]))
    wizard.refund_moves = lambda: refunds.append(refund)
    models["account.move.reversal"] = SimpleNamespace(with_context=lambda **_kwargs: SimpleNamespace(create=lambda _values: wizard))
    parameters = {"move_id": 101, "date": "2026-10-02", "reason": "Adjustment", "lines": [
        {**LINE, "product_uom_id": 12, "deductible_amount": "100.0" if capability == "customer_credit_note.create" else "50.001"}]}
    assert not runtime._dispatch_allowed(env, capability, parameters, 7, "key", "marker", Failure)[1]
    assert refund.invoice_line_ids[0].product_uom_id.id == 12
    assert runtime._dispatch_allowed(env, capability, parameters, 7, "key", "marker", Failure)[1]
    refund.invoice_line_ids[0].deductible_amount = 100 if capability == "vendor_refund.create" else 50
    with pytest.raises(Failure) as caught:
        runtime._dispatch_allowed(env, capability, parameters, 7, "key", "marker", Failure)
    assert caught.value.code == "idempotency_conflict"


def test_refund_batch_without_custom_lines_does_not_enter_new_reference_path(monkeypatch):
    monkeypatch.setattr(runtime, "_create_refund_round", lambda *_args: ({"batch": True}, False))
    monkeypatch.setattr(runtime, "_validate_invoice_line_inputs", lambda *_args: pytest.fail("No new inputs in refund rounds"))
    assert runtime._create_refund(object(), "vendor_refund.create", {"move_ids": [101, 102], "date": "2026-10-02", "reason": "Adjustment"}, 7, "key", "marker", Failure) == ({"batch": True}, False)
