from __future__ import annotations

import copy

import pytest
from test_core_writes_runtime import Env, Failure, Records, _payload

from odoo_accounting_cli_v4.bridge import core_writes_runtime as writes


def _prepare_move(env: Env, move_id: int, move_type: str, *, state: str = "draft"):
    move = env.existing_move(move_id, move_type=move_type, state=state)
    move.posted_before = state == "posted"
    move.payment_state = "paid" if state == "posted" else "not_paid"
    move.reconciled_payment_ids = Records(env, "account.payment")
    return move


@pytest.fixture
def native_actions(monkeypatch):
    def copy_move(records, default=None):
        assert len(records) == 1
        env = records.env
        source = next(iter(records))
        duplicate = _prepare_move(
            env, env._next_id + 1, source.move_type, state="draft"
        )
        env._next_id = duplicate.id
        duplicate.invoice_origin = (default or {}).get(
            "invoice_origin", source.invoice_origin
        )
        if getattr(env, "invalid_duplicate", False):
            duplicate.state = "posted"
        env.calls.append(("copy", source.id, duplicate.id, default))
        return Records(env, "account.move", [duplicate])

    def action_switch_move_type(records):
        assert len(records) == 1
        move = next(iter(records))
        move.move_type = {
            "out_invoice": "out_refund",
            "out_refund": "out_invoice",
            "in_invoice": "in_refund",
            "in_refund": "in_invoice",
        }[move.move_type]
        if getattr(records.env, "wrong_switch", False):
            move.move_type = "out_invoice"
        records.env.calls.append(("action_switch_move_type", move.id))

    monkeypatch.setattr(Records, "copy", copy_move, raising=False)
    monkeypatch.setattr(
        Records, "action_switch_move_type", action_switch_move_type, raising=False
    )


@pytest.mark.parametrize(
    "move_type", ["out_invoice", "out_refund", "in_invoice", "in_refund"]
)
def test_duplicate_uses_native_action_preserves_origin_and_replays(
    native_actions, move_type
):
    env = Env()
    source = _prepare_move(env, 100, move_type, state="posted")
    source.invoice_origin = "ERP-ORIGIN"
    source.reconciled_payment_ids = env.models["account.payment"].browse([])
    payload = _payload("invoice.duplicate", {"move_id": source.id}, key="copy-key")

    first = writes.dispatch(env, payload, 7, Failure)
    second = writes.dispatch(env, payload, 7, Failure)

    assert first["result"]["id"] != source.id
    assert first["result"]["source_id"] == source.id
    assert first["result"]["state"] == "draft"
    assert first["result"]["move_type"] == move_type
    assert second["idempotent_replay"] is True
    duplicate = env.models["account.move"].browse(first["result"]["id"])
    assert "ERP-ORIGIN" in duplicate.invoice_origin
    assert duplicate.payment_state == "not_paid"
    assert duplicate.posted_before is False
    assert [call[0] for call in env.calls].count("copy") == 1


def test_duplicate_allows_distinct_caller_keys_for_one_source(native_actions):
    env = Env()
    source = _prepare_move(env, 100, "out_invoice")
    first = writes.dispatch(
        env,
        _payload("invoice.duplicate", {"move_id": source.id}, key="copy-one"),
        7,
        Failure,
    )
    second = writes.dispatch(
        env,
        _payload("invoice.duplicate", {"move_id": source.id}, key="copy-two"),
        7,
        Failure,
    )
    assert first["result"]["id"] != second["result"]["id"]
    assert [call[0] for call in env.calls].count("copy") == 2


def test_duplicate_preserves_long_origin_without_an_artificial_limit(native_actions):
    env = Env()
    source = _prepare_move(env, 100, "out_invoice")
    source.invoice_origin = "ERP-" + ("X" * 400)
    result = writes.dispatch(
        env,
        _payload("invoice.duplicate", {"move_id": source.id}, key="copy-long-origin"),
        7,
        Failure,
    )

    duplicate = env.models["account.move"].browse(result["result"]["id"])
    assert duplicate.invoice_origin.startswith(source.invoice_origin)
    assert duplicate.invoice_origin.count("ODACV4K:") == 1
    assert duplicate.invoice_origin.count("ODACV4:") == 1


def test_duplicate_of_duplicate_does_not_copy_internal_markers(native_actions):
    env = Env()
    source = _prepare_move(env, 100, "out_invoice")
    source.invoice_origin = "ERP-ORIGIN"
    first_payload = _payload(
        "invoice.duplicate", {"move_id": source.id}, key="copy-one"
    )
    first = writes.dispatch(env, first_payload, 7, Failure)
    copied_source = env.models["account.move"].browse(first["result"]["id"])
    second = writes.dispatch(
        env,
        _payload("invoice.duplicate", {"move_id": copied_source.id}, key="copy-two"),
        7,
        Failure,
    )
    nested = env.models["account.move"].browse(second["result"]["id"])
    assert "ERP-ORIGIN" in nested.invoice_origin
    assert "ODACV4K:" in nested.invoice_origin
    assert nested.invoice_origin.count("ODACV4K:") == 1
    assert writes.dispatch(env, first_payload, 7, Failure)["idempotent_replay"] is True


def test_duplicate_same_key_rejects_changed_source(native_actions):
    env = Env()
    first = _prepare_move(env, 100, "out_invoice")
    second = _prepare_move(env, 101, "out_invoice")
    payload = _payload("invoice.duplicate", {"move_id": first.id}, key="copy-key")
    writes.dispatch(env, payload, 7, Failure)
    changed = copy.deepcopy(payload)
    changed["parameters"]["move_id"] = second.id
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, changed, 7, Failure)
    assert caught.value.code == "idempotency_conflict"


def test_duplicate_rejects_invalid_native_result(native_actions):
    env = Env()
    source = _prepare_move(env, 100, "out_invoice")
    env.invalid_duplicate = True
    with pytest.raises(Failure) as caught:
        writes.dispatch(
            env,
            _payload("invoice.duplicate", {"move_id": source.id}, key="copy-key"),
            7,
            Failure,
        )
    assert caught.value.code == "odoo_write_error"


@pytest.mark.parametrize(
    "denied_access", [("account.move", "write"), ("account.move.line", "create")]
)
def test_duplicate_requires_copy_and_marker_acls(native_actions, denied_access):
    env = Env()
    source = _prepare_move(env, 100, "out_invoice")
    env.denied_access = denied_access
    result = writes.dispatch(
        env,
        _payload("invoice.duplicate", {"move_id": source.id}, key="copy-key"),
        7,
        Failure,
    )
    assert result["access_allowed"] is False
    assert not any(call[0] == "copy" for call in env.calls)


@pytest.mark.parametrize(
    ("source_type", "target_type"),
    [
        ("out_invoice", "out_refund"),
        ("out_refund", "out_invoice"),
        ("in_invoice", "in_refund"),
        ("in_refund", "in_invoice"),
    ],
)
def test_type_switch_uses_native_action_and_target_replays(
    native_actions, source_type, target_type
):
    env = Env()
    move = _prepare_move(env, 100, source_type)
    payload = _payload(
        "invoice.type.switch",
        {"move_id": move.id, "target_move_type": target_type},
        key=f"invoice.type.switch:{move.id}:{target_type}",
    )
    first = writes.dispatch(env, payload, 7, Failure)
    second = writes.dispatch(env, payload, 7, Failure)
    assert first["result"]["id"] == move.id
    assert first["result"]["source_id"] == move.id
    assert first["result"]["move_type"] == target_type
    assert second["idempotent_replay"] is True
    assert [call[0] for call in env.calls].count("action_switch_move_type") == 1


@pytest.mark.parametrize("invalid", ["wrong_direction", "posted", "posted_before"])
def test_type_switch_rejects_non_native_or_non_draft_transition(
    native_actions, invalid
):
    env = Env()
    move = _prepare_move(
        env, 100, "out_invoice", state="posted" if invalid == "posted" else "draft"
    )
    if invalid == "posted_before":
        move.posted_before = True
    target = "in_refund" if invalid == "wrong_direction" else "out_refund"
    with pytest.raises(Failure) as caught:
        writes.dispatch(
            env,
            _payload(
                "invoice.type.switch",
                {"move_id": move.id, "target_move_type": target},
                key=f"invoice.type.switch:{move.id}:{target}",
            ),
            7,
            Failure,
        )
    assert caught.value.code == "state_conflict"
    assert not any(call[0] == "action_switch_move_type" for call in env.calls)


def test_type_switch_rejects_wrong_native_result(native_actions):
    env = Env()
    move = _prepare_move(env, 100, "in_invoice")
    env.wrong_switch = True
    with pytest.raises(Failure) as caught:
        writes.dispatch(
            env,
            _payload(
                "invoice.type.switch",
                {"move_id": move.id, "target_move_type": "in_refund"},
                key="invoice.type.switch:100:in_refund",
            ),
            7,
            Failure,
        )
    assert caught.value.code == "odoo_write_error"


def test_type_switch_requires_line_write_acl(native_actions):
    env = Env()
    move = _prepare_move(env, 100, "out_invoice")
    env.denied_access = ("account.move.line", "write")
    result = writes.dispatch(
        env,
        _payload(
            "invoice.type.switch",
            {"move_id": move.id, "target_move_type": "out_refund"},
            key="invoice.type.switch:100:out_refund",
        ),
        7,
        Failure,
    )
    assert result["access_allowed"] is False
    assert not any(call[0] == "action_switch_move_type" for call in env.calls)
