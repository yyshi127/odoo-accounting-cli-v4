from __future__ import annotations

import hashlib
import json
from types import SimpleNamespace
from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge import core_writes_runtime as runtime

CAPABILITIES = {
    "account.transfer_model.create",
    "account.transfer_model.update",
    "account.transfer_model.duplicate",
    "account.transfer_model.enable",
    "account.transfer_model.disable",
    "account.transfer_model.archive",
    "account.transfer_model.restore",
    "account.transfer_model.delete",
}
CREATE_PARAMETERS = {
    "name": "Monthly expense transfer",
    "journal_id": 11,
    "date_start": "2026-01-01",
    "date_stop": None,
    "frequency": "month",
    "origin_account_ids": [31, 32],
    "destination_lines": [
        {"account_id": 41, "percentage": "60"},
        {"account_id": 42, "percentage": "40"},
    ],
}


class Records(list[Any]):
    @property
    def ids(self) -> list[int]:
        return [record.id for record in self]


class Transfer:
    def __init__(self, *, active: bool = True, state: str = "disabled") -> None:
        self.id = 21
        self.name = "Monthly expense transfer"
        self.active = active
        self.state = state
        self.journal_id = SimpleNamespace(id=11)
        self.date_start = "2026-01-01"
        self.date_stop = False
        self.frequency = "month"
        self.account_ids = Records(
            [SimpleNamespace(id=31), SimpleNamespace(id=32)]
        )
        self.line_ids = Records(
            [
                SimpleNamespace(
                    id=51,
                    sequence=20,
                    account_id=SimpleNamespace(id=42),
                    percent=40.0,
                ),
                SimpleNamespace(
                    id=50,
                    sequence=10,
                    account_id=SimpleNamespace(id=41),
                    percent=60.0,
                ),
            ]
        )
        self.total_percent = 100.0
        self.move_ids = Records()
        self.unlinked = False

    def action_enable(self) -> None:
        self.state = "in_progress"

    def action_disable(self) -> None:
        self.state = "disabled"

    def action_archive(self) -> None:
        self.state = "disabled"
        self.active = False

    def action_unarchive(self) -> None:
        self.active = True

    def invalidate_recordset(self, _fields: list[str]) -> None:
        return None

    def unlink(self) -> None:
        self.unlinked = True


def _digest(value: Any) -> str:
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()[:32]


def test_runtime_registers_exact_transfer_model_surface_and_acl() -> None:
    assert CAPABILITIES <= runtime.CAPABILITIES
    assert all(
        runtime._GROUPS[capability_id] == "account.group_account_manager"
        for capability_id in CAPABILITIES
    )
    assert runtime._ACCESS["account.transfer_model.duplicate"] >= {
        ("account.transfer.model", "create"),
        ("account.transfer.model", "write"),
        ("account.transfer.model.line", "create"),
    }
    assert runtime._ACCESS["account.transfer_model.update"] >= {
        ("account.transfer.model", "write"),
        ("account.transfer.model.line", "create"),
        ("account.transfer.model.line", "write"),
        ("account.transfer.model.line", "unlink"),
    }
    assert ("account.transfer.model.line", "unlink") not in runtime._ACCESS[
        "account.transfer_model.delete"
    ]


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    [
        ("account.transfer_model.create", CREATE_PARAMETERS),
        (
            "account.transfer_model.update",
            {"transfer_model_id": 21, "changes": {"frequency": "quarter"}},
        ),
        (
            "account.transfer_model.duplicate",
            {"transfer_model_id": 21, "name": "Copy"},
        ),
        *[
            (capability_id, {"transfer_model_id": 21})
            for capability_id in CAPABILITIES
            if capability_id
            not in {
                "account.transfer_model.create",
                "account.transfer_model.update",
                "account.transfer_model.duplicate",
            }
        ],
    ],
)
def test_runtime_accepts_the_closed_transfer_model_contract(
    capability_id: str, parameters: dict[str, Any]
) -> None:
    assert runtime._valid_parameters(capability_id, parameters, 7)


@pytest.mark.parametrize(
    "parameters",
    [
        {**CREATE_PARAMETERS, "date_stop": "2025-12-31"},
        {**CREATE_PARAMETERS, "origin_account_ids": [31, 31]},
        {
            **CREATE_PARAMETERS,
            "destination_lines": [{"account_id": 41, "percentage": "0"}],
        },
        {
            **CREATE_PARAMETERS,
            "destination_lines": [{"account_id": 41, "percentage": "1.0"}],
        },
        {
            **CREATE_PARAMETERS,
            "destination_lines": [
                {"account_id": 41, "percentage": "60"},
                {"account_id": 42, "percentage": "41"},
            ],
        },
        {
            **CREATE_PARAMETERS,
            "destination_lines": [
                {"account_id": 41, "percentage": "33.3333333"}
            ],
        },
    ],
)
def test_runtime_rejects_invalid_transfer_model_values(
    parameters: dict[str, Any]
) -> None:
    assert not runtime._valid_parameters(
        "account.transfer_model.create", parameters, 7
    )


def test_runtime_keys_match_the_public_contract() -> None:
    assert runtime._deterministic_key(
        "account.transfer_model.create", CREATE_PARAMETERS, 7
    ) == f"account.transfer_model.create:7:{_digest(CREATE_PARAMETERS)}"
    changes = {"frequency": "quarter"}
    assert runtime._deterministic_key(
        "account.transfer_model.update",
        {"transfer_model_id": 21, "changes": changes},
        7,
    ) == f"account.transfer_model.update:21:{_digest(changes)}"
    assert runtime._deterministic_key(
        "account.transfer_model.enable", {"transfer_model_id": 21}, 7
    ) == "account.transfer_model.enable:21"


def test_runtime_maps_only_the_fixed_odoo_fields() -> None:
    values = runtime._transfer_model_write_values(
        CREATE_PARAMETERS, creating=True
    )

    assert values["account_ids"] == [(6, 0, [31, 32])]
    assert values["conditions"] == "[('account_id', 'in', [31, 32])]"
    assert values["date_stop"] is False
    assert values["line_ids"] == [
        (0, 0, {"account_id": 41, "percent": 60.0, "sequence": 10}),
        (0, 0, {"account_id": 42, "percent": 40.0, "sequence": 20}),
    ]
    assert "company_id" not in values
    assert "state" not in values


@pytest.mark.parametrize(
    ("capability_id", "initial_state", "expected_state"),
    [
        ("account.transfer_model.enable", "disabled", "in_progress"),
        ("account.transfer_model.disable", "in_progress", "disabled"),
        ("account.transfer_model.archive", "in_progress", "archived"),
    ],
)
def test_runtime_calls_native_transfer_model_transitions(
    monkeypatch: pytest.MonkeyPatch,
    capability_id: str,
    initial_state: str,
    expected_state: str,
) -> None:
    transfer = Transfer(state=initial_state)
    monkeypatch.setattr(runtime, "_account_transfer_model", lambda *_args: transfer)
    monkeypatch.setattr(
        runtime, "_validate_transfer_model_references", lambda *_args: None
    )

    result, replay = runtime._transition_transfer_model(
        object(), capability_id, {"transfer_model_id": 21}, 7, RuntimeError
    )

    assert not replay
    assert result["state"] == expected_state
    assert result["line_ids"] == [50, 51]


def test_runtime_restores_as_disabled_and_deletes_without_line_acl(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transfer = Transfer(active=False)
    monkeypatch.setattr(runtime, "_account_transfer_model", lambda *_args: transfer)

    restored, replay = runtime._transition_transfer_model(
        object(),
        "account.transfer_model.restore",
        {"transfer_model_id": 21},
        7,
        RuntimeError,
    )
    assert not replay
    assert restored["state"] == "disabled"

    class EmptyModel:
        def search_count(self, *_args: Any, **_kwargs: Any) -> int:
            return 0

    monkeypatch.setattr(runtime, "_scoped", lambda *_args: EmptyModel())
    deleted, replay = runtime._delete_transfer_model(
        object(), {"transfer_model_id": 21}, 7, RuntimeError
    )
    assert not replay
    assert transfer.unlinked
    assert deleted["state"] == "deleted"
    assert deleted["line_ids"] == [50, 51]


def test_runtime_rejects_deleting_an_archived_transfer_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transfer = Transfer(active=False)
    monkeypatch.setattr(runtime, "_account_transfer_model", lambda *_args: transfer)
    monkeypatch.setattr(
        runtime,
        "_fail",
        lambda *_args, **_kwargs: RuntimeError("state_conflict"),
    )

    with pytest.raises(RuntimeError, match="state_conflict"):
        runtime._delete_transfer_model(
            object(), {"transfer_model_id": 21}, 7, RuntimeError
        )

    assert not transfer.unlinked
