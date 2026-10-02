from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager
from copy import deepcopy

import pytest
import test_invoice_bulk_lines_runtime as bulk

from odoo_accounting_cli_v4.bridge import core_writes_runtime as runtime
from odoo_accounting_cli_v4.capabilities import core_writes as sdk


def fixture(monkeypatch, lines=None):
    env, move = bulk.fixture(monkeypatch, lines)
    model = env.models["account.move.line"]
    model.search_count = lambda domain, **_kwargs: len(model.search(domain))
    previous_savepoint = env.cr.savepoint

    @contextmanager
    def savepoint():
        old_state = move.state, move.company_id, move.move_type
        try:
            with previous_savepoint():
                yield
        except Exception:
            move.state, move.company_id, move.move_type = old_state
            raise

    env.cr.savepoint = savepoint

    def write(values):
        assert env.uid == 5 and not env.su
        env.calls.append(deepcopy(values))
        for command, line_id, value in values["invoice_line_ids"]:
            assert command == 2 and value == 0
            move.invoice_line_ids = bulk.Records(line for line in move.invoice_line_ids if line.id != line_id)
            model.records = bulk.Records(line for line in model.records if line.id != line_id)
        move.line_ids = bulk.Records([*move.invoice_line_ids, bulk.SimpleNamespace(id=900 + len(env.calls), display_type="tax")])
        if move.hook:
            move.hook(move)

    move.write = write
    return env, move


def execute(env, ids):
    return bulk.execute(env, "invoice.lines.remove", {"move_id": 101, "line_ids": ids})


def test_remove_uses_one_parent_delete_command_write_and_preserves_layout_and_native_dynamic_ids(monkeypatch):
    env, move = fixture(monkeypatch)
    layout = runtime._invoice_bulk_line_snapshot(move.invoice_line_ids[2])
    result, replay = execute(env, [201, 202])
    assert result == {"id": 101, "source_id": None} and not replay
    assert env.calls == [{"invoice_line_ids": [(2, 201, 0), (2, 202, 0)]}]
    assert move.invoice_line_ids.ids == [203] and move.line_ids.ids == [203, 901]
    assert runtime._invoice_bulk_line_snapshot(move.invoice_line_ids[0]) == layout
    assert not env.models["account.move.line"].search_count([("id", "in", [201, 202])])


def test_missing_deleted_id_is_not_a_successful_replay(monkeypatch):
    env, _move = fixture(monkeypatch)
    execute(env, [201])
    with pytest.raises(bulk.Failure) as caught:
        execute(env, [201])
    assert caught.value.code == "record_not_found" and len(env.calls) == 1


@pytest.mark.parametrize("line_ids", [[201, 999], [201, 203], [201, 204]])
def test_all_selected_rows_must_be_visible_same_parent_business_lines_before_any_write(monkeypatch, line_ids):
    env, move = fixture(monkeypatch)
    foreign = bulk.Line(204)
    move.bind(foreign)
    foreign.move_id = bulk.ref(102)
    env.models["account.move.line"].records.append(foreign)
    with pytest.raises(bulk.Failure) as caught:
        execute(env, line_ids)
    assert caught.value.code == "record_not_found" and not env.calls
    assert move.invoice_line_ids.ids == [201, 202, 203]


@pytest.mark.parametrize("scope", ["move_company", "line_company", "entry", "posted", "cancel"])
def test_remove_retains_ordinary_company_document_and_draft_scope(monkeypatch, scope):
    env, move = fixture(monkeypatch)
    if scope == "move_company":
        move.company_id = bulk.ref(8)
    elif scope == "line_company":
        move.invoice_line_ids[0].company_id = bulk.ref(8)
    elif scope == "entry":
        move.move_type = "entry"
    else:
        move.state = scope
    with pytest.raises(bulk.Failure) as caught:
        execute(env, [201])
    assert caught.value.code == ("state_conflict" if scope in {"posted", "cancel"} else "record_not_found")
    assert not env.calls


@pytest.mark.parametrize("move_type", ["out_invoice", "out_refund", "in_invoice", "in_refund"])
def test_all_four_document_types_allow_last_business_line_removal_without_invented_minimum(monkeypatch, move_type):
    env, move = fixture(monkeypatch, [bulk.Line(201)])
    move.move_type = move_type
    assert not execute(env, [201])[1]
    assert not move.invoice_line_ids


def test_sourced_rows_use_native_removal_while_survivor_sources_and_inputs_are_preserved(monkeypatch):
    env, move = fixture(monkeypatch)
    move.invoice_line_ids[0].sale_line_ids = bulk.ref(401)
    survivor = move.invoice_line_ids[1]
    survivor.purchase_line_id = bulk.ref(402)
    survivor.write({"product_uom_id": 12, "deductible_amount": 25})
    before = runtime._invoice_bulk_line_snapshot(survivor)
    assert not execute(env, [201])[1]
    assert runtime._invoice_bulk_line_snapshot(survivor) == before


@pytest.mark.parametrize("failure", ["input", "layout", "source", "membership", "retained_target", "state", "company"])
def test_post_write_proof_failure_rolls_back_the_entire_removal(monkeypatch, failure):
    env, move = fixture(monkeypatch)
    selected = move.invoice_line_ids[0]
    before = [runtime._invoice_bulk_line_snapshot(line) for line in move.invoice_line_ids]

    def tamper(record):
        if failure == "input":
            record.invoice_line_ids[0].deductible_amount = 25
        elif failure == "layout":
            record.invoice_line_ids[-1].name = "Changed layout"
        elif failure == "source":
            record.invoice_line_ids[0].purchase_line_id = bulk.ref(402)
        elif failure == "membership":
            record.invoice_line_ids.pop()
        elif failure == "retained_target":
            env.models["account.move.line"].records.append(selected)
        elif failure == "state":
            record.state = "posted"
        else:
            record.company_id = bulk.ref(8)

    move.hook = tamper
    with pytest.raises(bulk.Failure) as caught:
        execute(env, [201])
    assert caught.value.code == "odoo_write_error"
    assert move.invoice_line_ids.ids == [201, 202, 203]
    assert [runtime._invoice_bulk_line_snapshot(line) for line in move.invoice_line_ids] == before
    assert move.state == "draft" and move.company_id.id == 7


def test_native_unlink_acl_error_maps_without_sudo_and_rolls_back(monkeypatch):
    class AccessError(Exception):
        pass

    env, move = fixture(monkeypatch)

    def denied(_record):
        raise AccessError("Native unlink denied")

    move.hook = denied
    parameters = {"move_id": 101, "line_ids": [201, 202]}
    monkeypatch.setattr(runtime, "_validated_payload", lambda *_args: ("invoice.lines.remove", "key", parameters, "marker"))
    monkeypatch.setattr(runtime, "_gate", lambda *_args: (True, True, True))
    with pytest.raises(bulk.Failure) as caught:
        runtime.dispatch(env, {}, 7, bulk.Failure)
    assert caught.value.code == "unauthorized" and caught.value.exit_code == 3
    assert move.invoice_line_ids.ids == [201, 202, 203] and not env.su


def test_remove_closed_maps_and_content_key_match_sdk_without_changing_single_delete():
    capability = "invoice.lines.remove"
    parameters = {"move_id": 101, "line_ids": [201, 202]}
    canonical = json.dumps(parameters, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    expected = f"{capability}:101:{hashlib.sha256(canonical.encode()).hexdigest()[:32]}"
    assert capability in runtime.CAPABILITIES
    assert runtime._MODELS[capability] == runtime._MODELS["invoice.line.delete"]
    assert runtime._ACCESS[capability] == runtime._ACCESS["invoice.line.delete"]
    assert runtime._GROUPS[capability] == runtime._GROUPS["invoice.line.delete"]
    assert runtime._deterministic_key(capability, parameters, 7) == expected
    assert runtime._deterministic_key(capability, parameters, 7) == sdk._expected_idempotency_key(capability, parameters, 7)
    assert sdk._validate_invoice_bulk_line_parameters(capability, {"move_id": 101, "line_ids": [202, 201]}) == parameters
    assert runtime._deterministic_key("invoice.line.delete", {"move_id": 101, "line_id": 201}, 7) == "invoice.line.delete:101:201"


@pytest.mark.parametrize("ids", [[], [201, 201], [202, 201], [0], [True], ["201"], list(range(1, 202)), None])
def test_remove_native_protocol_rejects_invalid_or_noncanonical_ids(ids):
    assert not runtime._valid_parameters("invoice.lines.remove", {"move_id": 101, "line_ids": ids})


def test_remove_native_protocol_accepts_maximum_ids_and_rejects_extra_parameters():
    assert runtime._valid_parameters("invoice.lines.remove", {"move_id": 101, "line_ids": list(range(1, 201))})
    assert not runtime._valid_parameters("invoice.lines.remove", {"move_id": 101, "line_ids": [201], "expected_line_ids": [201]})


def test_maximum_removal_still_uses_one_parent_write_and_allows_empty_business_rows(monkeypatch):
    ids = list(range(201, 401))
    env, move = fixture(monkeypatch, [bulk.Line(line_id) for line_id in ids])
    assert not execute(env, ids)[1]
    assert len(env.calls) == 1 and len(env.calls[0]["invoice_line_ids"]) == 200
    assert not move.invoice_line_ids and not env.models["account.move.line"].records
