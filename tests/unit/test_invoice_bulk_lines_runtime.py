from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager
from copy import deepcopy
from types import SimpleNamespace

import pytest

from odoo_accounting_cli_v4.bridge import core_writes_runtime as runtime
from odoo_accounting_cli_v4.capabilities import core_writes as sdk


class Failure(Exception):
    def __init__(self, code, message, *, exit_code, retryable, details):
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


class Records(list):
    @property
    def ids(self):
        return [record.id for record in self]

    def __getattr__(self, field):
        if field.startswith("__"):
            raise AttributeError(field)
        if field == "id" and not self:
            return False
        assert len(self) == 1
        return getattr(self[0], field)

    def __or__(self, other):
        return Records({record.id: record for record in (*self, *other)}.values())

    def invalidate_recordset(self):
        pass


def ref(record_id):
    return Records([SimpleNamespace(id=record_id)]) if record_id else Records()


LINE = {"name": "Service", "product_id": 21, "account_id": 31, "quantity": "2", "price_unit": "25", "discount": "0", "tax_ids": []}


class Line:
    def __init__(self, record_id, **values):
        self.id = record_id
        self.display_type = "product"
        self.sequence = 10
        self.product_uom_id = ref(11)
        self.deductible_amount = 100
        self.analytic_distribution = False
        self.deferred_start_date = self.deferred_end_date = False
        self.sale_line_ids = self.purchase_line_id = Records()
        self.write({**LINE, **values})
        self._fields = {field: object() for field in self.__dict__}

    def write(self, values):
        for field, value in values.items():
            if field in {"product_id", "account_id", "product_uom_id"}:
                value = ref(value)
            elif field == "tax_ids":
                ids = value[0][2] if value and isinstance(value[0], tuple) else value
                value = Records(SimpleNamespace(id=record_id) for record_id in ids)
            setattr(self, field, value)


class Model:
    def __init__(self, records=()):
        self.records = Records(records)
        self._fields = {field: object() for field in runtime._INVOICE_LINE_INPUT_FIELDS}

    def browse(self, ids):
        return Records(record for record in self.records if record.id in ids)

    def search(self, domain, **kwargs):
        def matches(record):
            for field, operator, expected in domain:
                value = getattr(record, field)
                if isinstance(value, Records):
                    value = value.ids if field == "company_ids" else value.id or False
                if operator == "=" and value != expected:
                    return False
                if operator == "in" and not (set(value) & set(expected) if isinstance(value, list) else value in expected):
                    return False
            return True

        rows = Records(record for record in self.records if matches(record))
        return Records(rows[:kwargs["limit"]]) if "limit" in kwargs else rows


class Move:
    def __init__(self, lines):
        self.id = 101
        self.company_id = ref(7)
        self.partner_id = ref(41)
        self.journal_id = ref(51)
        self.move_type = "in_invoice"
        self.state = "draft"
        self.invoice_line_ids = Records(lines)
        self.line_ids = Records(lines)
        self.hook = None
        for line in lines:
            self.bind(line)

    def bind(self, line):
        line.move_id = ref(self.id)
        line.company_id = self.company_id

    def invalidate_recordset(self):
        pass

    def write(self, values):
        self.env.calls.append(deepcopy(values))
        for command, line_id, data in values["invoice_line_ids"]:
            if command == 1:
                next(line for line in self.invoice_line_ids if line.id == line_id).write(data)
            else:
                assert command == 0
                line = Line(max(self.env.models["account.move.line"].records.ids, default=200) + 1, **data)
                self.bind(line)
                self.invoice_line_ids.append(line)
                self.env.models["account.move.line"].records.append(line)
        self.line_ids = Records([*self.invoice_line_ids, SimpleNamespace(id=900 + len(self.env.calls), display_type="tax")])
        if self.hook:
            self.hook(self)


def fixture(monkeypatch, lines=None):
    move = Move(lines if lines is not None else [Line(201), Line(202, name="Other"), Line(203, name="Layout", display_type="line_section")])
    env = SimpleNamespace(uid=5, su=False, calls=[])
    env.models = {
        "account.move": Model([move]), "account.move.line": Model(move.invoice_line_ids),
        "res.partner": Model([SimpleNamespace(id=41, company_id=Records())]),
        "account.account": Model([SimpleNamespace(id=31, company_ids=ref(7))]),
        "product.product": Model([SimpleNamespace(id=21, company_id=Records(), uom_id=ref(11), uom_ids=ref(12))]),
        "uom.uom": Model([SimpleNamespace(id=11), SimpleNamespace(id=12)]),
        "account.tax": Model([SimpleNamespace(id=91, company_id=ref(7))]),
    }
    move.env = env

    @contextmanager
    def savepoint():
        rows = list(env.models["account.move.line"].records)
        state = [(line, deepcopy(line.__dict__)) for line in rows]
        old_lines, old_dynamic = Records(move.invoice_line_ids), Records(move.line_ids)
        try:
            yield
        except Exception:
            for line, values in state:
                line.__dict__.clear()
                line.__dict__.update(values)
            move.invoice_line_ids, move.line_ids = old_lines, old_dynamic
            env.models["account.move.line"].records = Records(rows)
            raise

    env.cr = SimpleNamespace(savepoint=savepoint)

    def scoped(selected, model, company):
        assert selected is env and env.uid == 5 and not env.su and company == 7
        return env.models[model]

    monkeypatch.setattr(runtime, "_scoped", scoped)
    monkeypatch.setattr(runtime, "_validate_line_analytic_references", lambda *_args: None)
    monkeypatch.setattr(runtime, "_move_result", lambda record, company, source_id=None: {"id": record.id, "source_id": source_id})
    return env, move


def execute(env, capability, parameters):
    return runtime._dispatch_allowed(env, capability, parameters, 7, "key", "marker", Failure)


def test_sparse_updates_use_one_parent_write_keep_ids_layout_and_native_dynamic_lines(monkeypatch):
    env, move = fixture(monkeypatch)
    parameters = {"move_id": 101, "lines": [{"line_id": 201, "changes": {"quantity": "3"}}, {"line_id": 202, "changes": {"price_unit": "11"}}]}
    old_ids = move.invoice_line_ids.ids
    assert not execute(env, "invoice.lines.update", parameters)[1]
    assert move.invoice_line_ids.ids == old_ids and move.invoice_line_ids[2].name == "Layout"
    assert move.line_ids.ids == [201, 202, 203, 901]
    assert env.calls == [{"invoice_line_ids": [(1, 201, {"quantity": 3.0}), (1, 202, {"price_unit": 11.0})]}]
    assert execute(env, "invoice.lines.update", parameters)[1] and len(env.calls) == 1


def test_unit_only_update_accepts_native_unrequested_price_and_tax_recompute(monkeypatch):
    env, move = fixture(monkeypatch)
    move.hook = lambda record: record.invoice_line_ids[0].write({"price_unit": 72, "tax_ids": [(6, 0, [91])]})
    parameters = {"move_id": 101, "lines": [{"line_id": 201, "changes": {"product_uom_id": 12}}]}
    assert not execute(env, "invoice.lines.update", parameters)[1]
    assert move.invoice_line_ids[0].price_unit == 72
    assert execute(env, "invoice.lines.update", parameters)[1]


@pytest.mark.parametrize("failure", ["explicit_price", "untouched", "source", "membership"])
def test_bulk_post_write_failures_roll_back_all_selected_rows(monkeypatch, failure):
    env, move = fixture(monkeypatch)
    changes = {"product_uom_id": 12, "price_unit": "11"}

    def tamper(record):
        if failure == "explicit_price":
            record.invoice_line_ids[0].price_unit = 72
        elif failure == "untouched":
            record.invoice_line_ids[1].name = "Unexpected"
        elif failure == "source":
            record.invoice_line_ids[0].sale_line_ids = ref(401)
        else:
            record.invoice_line_ids.pop()

    move.hook = tamper
    before = [runtime._invoice_bulk_line_snapshot(line) for line in move.invoice_line_ids]
    with pytest.raises(Failure) as caught:
        execute(env, "invoice.lines.update", {"move_id": 101, "lines": [{"line_id": 201, "changes": changes}]})
    assert caught.value.code == "odoo_write_error"
    assert [runtime._invoice_bulk_line_snapshot(line) for line in move.invoice_line_ids] == before
    assert move.invoice_line_ids.ids == [201, 202, 203]


@pytest.mark.parametrize("changes", [{"product_id": None}, {"product_uom_id": 12}, {"deductible_amount": "50"}])
def test_sourced_changed_product_unit_or_deductibility_rejects_before_write(monkeypatch, changes):
    env, move = fixture(monkeypatch)
    move.invoice_line_ids[0].sale_line_ids = ref(401)
    with pytest.raises(Failure) as caught:
        execute(env, "invoice.lines.update", {"move_id": 101, "lines": [{"line_id": 201, "changes": changes}]})
    assert caught.value.code == "business_rule_error" and not env.calls


def test_sourced_same_value_inputs_replay_and_old_quantity_remains_editable(monkeypatch):
    env, move = fixture(monkeypatch)
    move.invoice_line_ids[0].purchase_line_id = ref(401)
    changes = {"product_id": 21, "product_uom_id": 11, "deductible_amount": "100.0"}
    parameters = {"move_id": 101, "lines": [{"line_id": 201, "changes": changes}]}
    assert execute(env, "invoice.lines.update", parameters)[1]
    changes["quantity"] = "3"
    assert not execute(env, "invoice.lines.update", parameters)[1]


@pytest.mark.parametrize("line_id", [203, 999])
def test_bulk_update_requires_visible_same_parent_business_line(monkeypatch, line_id):
    env, _move = fixture(monkeypatch)
    with pytest.raises(Failure) as caught:
        execute(env, "invoice.lines.update", {"move_id": 101, "lines": [{"line_id": line_id, "changes": {"name": "Changed"}}]})
    assert caught.value.code == "record_not_found" and not env.calls


def test_all_refs_are_checked_before_parent_write(monkeypatch):
    env, _move = fixture(monkeypatch)
    with pytest.raises(Failure) as caught:
        execute(env, "invoice.lines.update", {"move_id": 101, "lines": [{"line_id": 201, "changes": {"quantity": "3"}}, {"line_id": 202, "changes": {"account_id": 999}}]})
    assert caught.value.code == "record_not_found" and not env.calls


def test_append_duplicates_once_and_membership_replay_as_native_multiset(monkeypatch):
    env, move = fixture(monkeypatch)
    old = [runtime._invoice_bulk_line_snapshot(line) for line in move.invoice_line_ids]
    parameters = {"move_id": 101, "expected_line_ids": [201, 202, 203], "lines": [LINE, LINE]}
    assert not execute(env, "invoice.lines.add", parameters)[1]
    assert len(env.calls) == 1 and [command[0] for command in env.calls[0]["invoice_line_ids"]] == [0, 0]
    assert move.invoice_line_ids.ids == [201, 202, 203, 204, 205]
    assert old == [runtime._invoice_bulk_line_snapshot(line) for line in move.invoice_line_ids[:3]]
    assert execute(env, "invoice.lines.add", parameters)[1] and len(env.calls) == 1
    move.invoice_line_ids[-1].price_unit = 12
    with pytest.raises(Failure) as caught:
        execute(env, "invoice.lines.add", parameters)
    assert caught.value.code == "idempotency_conflict" and len(env.calls) == 1


def test_append_allows_empty_baseline_and_validates_native_inputs(monkeypatch):
    env, move = fixture(monkeypatch, [])
    parameters = {"move_id": 101, "expected_line_ids": [], "lines": [{**LINE, "product_uom_id": 12, "deductible_amount": "50.001"}]}
    assert not execute(env, "invoice.lines.add", parameters)[1]
    assert move.invoice_line_ids[0].deductible_amount == 50.001
    assert execute(env, "invoice.lines.add", parameters)[1]


@pytest.mark.parametrize("failure", ["old_layout", "missing_added", "bad_added"])
def test_append_native_verification_failure_rolls_back_old_and_new_rows(monkeypatch, failure):
    env, move = fixture(monkeypatch)
    parameters = {"move_id": 101, "expected_line_ids": [201, 202, 203], "lines": [LINE, LINE]}

    def tamper(record):
        if failure == "old_layout":
            record.invoice_line_ids[2].name = "Unexpected"
        elif failure == "missing_added":
            record.invoice_line_ids.pop()
        else:
            record.invoice_line_ids[-1].quantity = 7

    move.hook = tamper
    before = [runtime._invoice_bulk_line_snapshot(line) for line in move.invoice_line_ids]
    with pytest.raises(Failure) as caught:
        execute(env, "invoice.lines.add", parameters)
    assert caught.value.code == "odoo_write_error"
    assert env.models["account.move.line"].records.ids == [201, 202, 203]
    assert [runtime._invoice_bulk_line_snapshot(line) for line in move.invoice_line_ids] == before


def test_append_stale_membership_rejects_before_write(monkeypatch):
    env, _move = fixture(monkeypatch)
    with pytest.raises(Failure) as caught:
        execute(env, "invoice.lines.add", {"move_id": 101, "expected_line_ids": [201, 202], "lines": [LINE]})
    assert caught.value.code == "idempotency_conflict" and not env.calls


def test_append_foreign_product_is_not_visible_and_never_writes(monkeypatch):
    env, _move = fixture(monkeypatch)
    env.models["product.product"].records[0].company_id = ref(8)
    with pytest.raises(Failure) as caught:
        execute(env, "invoice.lines.add", {"move_id": 101, "expected_line_ids": [201, 202, 203], "lines": [LINE]})
    assert caught.value.code == "record_not_found" and not env.calls


def test_bulk_native_acl_denial_is_mapped_and_atomic_without_elevation(monkeypatch):
    class AccessError(Exception):
        pass

    env, move = fixture(monkeypatch)
    parameters = {"move_id": 101, "lines": [{"line_id": 201, "changes": {"quantity": "3"}}]}

    def denied(_record):
        raise AccessError("Native write denied")

    move.hook = denied
    monkeypatch.setattr(runtime, "_validated_payload", lambda *_args: ("invoice.lines.update", "key", parameters, "marker"))
    monkeypatch.setattr(runtime, "_gate", lambda *_args: (True, True, True))
    with pytest.raises(Failure) as caught:
        runtime.dispatch(env, {}, 7, Failure)
    assert caught.value.code == "unauthorized" and caught.value.exit_code == 3
    assert move.invoice_line_ids[0].quantity == "2" and not env.su


def test_maximum_duplicate_append_multiset_and_replay_are_bounded(monkeypatch):
    env, move = fixture(monkeypatch, [])
    parameters = {"move_id": 101, "expected_line_ids": [], "lines": [LINE] * 200}
    assert runtime._valid_parameters("invoice.lines.add", parameters)
    assert not execute(env, "invoice.lines.add", parameters)[1]
    assert len(move.invoice_line_ids) == 200 and len(env.calls) == 1
    assert execute(env, "invoice.lines.add", parameters)[1]


def test_added_multiset_matching_does_not_greedily_consume_explicit_unit_candidate():
    lines = [Line(201, product_uom_id=12), Line(202, product_uom_id=11)]
    assert runtime._invoice_added_lines_match(lines, [LINE, {**LINE, "product_uom_id": 12}])
    assert not runtime._invoice_added_lines_match(lines, [{**LINE, "product_uom_id": 12}] * 2)


@pytest.mark.parametrize("capability", ["invoice.lines.update", "invoice.lines.add"])
def test_new_bulk_maps_key_and_draft_guard_are_closed_and_match_sdk(monkeypatch, capability):
    env, move = fixture(monkeypatch)
    parameters = {"move_id": 101, "lines": [{"line_id": 201, "changes": {"quantity": "3"}}]} if capability.endswith("update") else {"move_id": 101, "expected_line_ids": [201, 202, 203], "lines": [LINE]}
    canonical = json.dumps(parameters, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    expected_key = f"{capability}:101:{hashlib.sha256(canonical.encode()).hexdigest()[:32]}"
    assert runtime._deterministic_key(capability, parameters, 7) == expected_key
    normalized = sdk._validate_invoice_bulk_line_parameters(capability, parameters)
    assert runtime._valid_parameters(capability, normalized)
    assert runtime._deterministic_key(capability, normalized, 7) == sdk._expected_idempotency_key(capability, normalized, 7)
    single = "invoice.line.update" if capability.endswith("update") else "invoice.line.create"
    assert runtime._MODELS[capability] == runtime._MODELS[single]
    assert runtime._ACCESS[capability] == runtime._ACCESS[single]
    assert runtime._valid_parameters(capability, parameters)
    move.state = "posted"
    with pytest.raises(Failure) as caught:
        execute(env, capability, parameters)
    assert caught.value.code == "state_conflict" and not env.calls


@pytest.mark.parametrize("parameters", [
    {"move_id": 101, "lines": []},
    {"move_id": True, "lines": [{"line_id": 201, "changes": {"quantity": "3"}}]},
    {"move_id": 101, "lines": [{"line_id": 201, "changes": {}}]},
    {"move_id": 101, "lines": [{"line_id": 201, "changes": {"quantity": "3"}}] * 2},
    {"move_id": 101, "lines": [{"line_id": 202, "changes": {"quantity": "3"}}, {"line_id": 201, "changes": {"quantity": "3"}}]},
    {"move_id": 101, "lines": [{"line_id": 201, "changes": {"quantity": "3"}}] * 201},
])
def test_invalid_bulk_update_parameters(parameters):
    assert not runtime._valid_parameters("invoice.lines.update", parameters)


@pytest.mark.parametrize("ids,lines", [([201, 201], [LINE]), ([202, 201], [LINE]), ([True], [LINE]), ([], []), ([], [LINE] * 201)])
def test_invalid_append_parameters(ids, lines):
    assert not runtime._valid_parameters("invoice.lines.add", {"move_id": 101, "expected_line_ids": ids, "lines": lines})
