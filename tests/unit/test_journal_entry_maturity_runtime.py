from __future__ import annotations

from copy import deepcopy
from datetime import date

import pytest
from test_core_writes_runtime import Env, Failure, Records, _entry_parameters, _payload

from odoo_accounting_cli_v4.bridge import core_writes_runtime as writes


def _replacement_payload(move_id, lines):
    parameters = {"move_id": move_id, "lines": lines}
    return _payload(
        "journal_entry.lines.replace",
        parameters,
        key=writes._deterministic_key("journal_entry.lines.replace", parameters, 7),
    )


@pytest.mark.parametrize("maturity", [None, "2024-12-31", "2025-04-30"])
def test_entry_creation_persists_explicit_maturity_and_binds_replay(maturity):
    env = Env()
    parameters = _entry_parameters(env)
    parameters["lines"][0]["date_maturity"] = maturity
    original = deepcopy(parameters)
    payload = _payload("journal_entry.create", parameters, key="entry-maturity")

    first = writes.dispatch(env, payload, 7, Failure)
    assert first["idempotent_replay"] is False
    assert writes.dispatch(env, payload, 7, Failure)["idempotent_replay"] is True
    values = next(
        call[2] for call in env.calls if call[:2] == ("create", "account.move")
    )
    assert values["line_ids"][0][2]["date_maturity"] == (maturity or False)
    assert "date_maturity" not in values["line_ids"][1][2]
    assert parameters == original

    changed = deepcopy(parameters)
    changed["lines"][0]["date_maturity"] = "2025-05-31"
    with pytest.raises(Failure) as caught:
        writes.dispatch(
            env,
            _payload("journal_entry.create", changed, key="entry-maturity"),
            7,
            Failure,
        )
    assert caught.value.code == "idempotency_conflict"
    assert sum(call[:2] == ("create", "account.move") for call in env.calls) == 1


def test_legacy_entry_creation_does_not_supply_maturity_defaults():
    env = Env()
    parameters = _entry_parameters(env)
    original = deepcopy(parameters)
    payload = _payload("journal_entry.create", parameters, key="legacy-entry")
    writes.dispatch(env, payload, 7, Failure)
    assert writes.dispatch(env, payload, 7, Failure)["idempotent_replay"] is True
    values = next(
        call[2] for call in env.calls if call[:2] == ("create", "account.move")
    )
    assert all("date_maturity" not in command[2] for command in values["line_ids"])
    assert parameters == original


def test_replacement_changes_clears_and_verifies_native_date_values():
    env = Env()
    entry = env.existing_move(611, move_type="entry", state="draft")
    lines = _entry_parameters(env)["lines"]
    keys = set()
    for maturity in ("2024-12-31", "2025-04-30", None):
        lines[0]["date_maturity"] = maturity
        original = deepcopy(lines)
        payload = _replacement_payload(entry.id, lines)
        keys.add(
            writes._deterministic_key(
                "journal_entry.lines.replace", payload["parameters"], 7
            )
        )
        assert writes.dispatch(env, payload, 7, Failure)["idempotent_replay"] is False
        actual = next(iter(entry.line_ids))
        assert actual.date_maturity == (maturity or False)
        actual.date_maturity = date.fromisoformat(maturity) if maturity else False
        assert writes.dispatch(env, payload, 7, Failure)["idempotent_replay"] is True
        snapshot = writes._current_entry_lines(Records(env, "account.move", [entry]))
        assert snapshot[0]["date_maturity"] == maturity
        assert lines == original
    assert len(keys) == 3
    assert sum(call[0] == "write" for call in env.calls) == 3

    entry.state = "posted"
    assert writes.dispatch(env, payload, 7, Failure)["idempotent_replay"] is True
    lines[0]["date_maturity"] = "2025-06-30"
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, _replacement_payload(entry.id, lines), 7, Failure)
    assert caught.value.code == "state_conflict"
    assert sum(call[0] == "write" for call in env.calls) == 3


@pytest.mark.parametrize("state", ["draft", "posted"])
@pytest.mark.parametrize("explicit_first", [False, True])
def test_omitted_maturity_is_ignored_per_line_on_replay(state, explicit_first):
    env = Env()
    entry = env.existing_move(611, move_type="entry", state="draft")
    lines = _entry_parameters(env)["lines"]
    writes.dispatch(env, _replacement_payload(entry.id, lines), 7, Failure)
    entry.state = state
    for line in entry.line_ids:
        line.date_maturity = date(2025, 3, 31)
    if explicit_first:
        lines[0]["date_maturity"] = "2025-03-31"
    original = deepcopy(lines)

    result = writes.dispatch(env, _replacement_payload(entry.id, lines), 7, Failure)

    assert result["idempotent_replay"] is True
    assert sum(call[0] == "write" for call in env.calls) == 1
    assert all(line.date_maturity == date(2025, 3, 31) for line in entry.line_ids)
    assert lines == original


@pytest.mark.parametrize(
    "capability", ["journal_entry.create", "journal_entry.lines.replace"]
)
@pytest.mark.parametrize(
    "maturity", ["2025-02-30", "2025-2-03", "2025-02-03T00:00:00", "", True, 12, [], {}]
)
def test_invalid_maturity_is_rejected_before_orm(capability, maturity):
    env = Env()
    parameters = _entry_parameters(env)
    parameters["lines"][0]["date_maturity"] = maturity
    if capability == "journal_entry.lines.replace":
        payload = _replacement_payload(611, parameters["lines"])
    else:
        payload = _payload(capability, parameters)
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, payload, 7, Failure)
    assert caught.value.code == "bridge_protocol_error"
    assert not any(call[0] in {"create", "write"} for call in env.calls)


def test_replacement_detects_maturity_not_persisted(monkeypatch):
    env = Env()
    entry = env.existing_move(611, move_type="entry", state="draft")
    lines = _entry_parameters(env)["lines"]
    lines[0]["date_maturity"] = "2025-03-31"
    original = env.move_lines_from_commands

    def lose_maturity(commands):
        records = original(commands)
        for line in records:
            line.date_maturity = False
        return records

    monkeypatch.setattr(env, "move_lines_from_commands", lose_maturity)
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, _replacement_payload(entry.id, lines), 7, Failure)
    assert caught.value.code == "odoo_write_error"
