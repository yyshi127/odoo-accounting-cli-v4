from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge import core_writes_runtime as runtime

CAPABILITIES = {
    "fiscal_position.create",
    "fiscal_position.update",
    "fiscal_position.account_mappings.replace",
    "fiscal_position.archive",
    "fiscal_position.restore",
    "journal.group.create",
    "journal.group.update",
}


class Failure(Exception):
    def __init__(self, code: str, message: str, **_kwargs: Any) -> None:
        super().__init__(message)
        self.code = code


class Records(list[Any]):
    @property
    def ids(self) -> list[int]:
        return [item.id for item in self]

    def __getattr__(self, name: str) -> Any:
        if len(self) != 1:
            raise AttributeError(name)
        return getattr(self[0], name)

    def unlink(self) -> None:
        self.clear()


class Record(SimpleNamespace):
    def write(self, values: dict[str, Any]) -> None:
        for key, value in values.items():
            setattr(self, key, value)

    def invalidate_recordset(self, _fields: list[str]) -> None:
        return None


def _position(*, active: bool = True) -> Record:
    return Record(
        id=21,
        name="Domestic",
        sequence=0,
        auto_apply=False,
        vat_required=False,
        country_id=False,
        country_group_id=False,
        state_ids=Records(),
        zip_from=False,
        zip_to=False,
        note=False,
        active=active,
        company_id=Record(id=7),
        account_ids=Records(),
    )


def test_metadata_is_closed_manager_only_and_company_scoped() -> None:
    assert CAPABILITIES <= runtime.CAPABILITIES
    assert {runtime._GROUPS[item] for item in CAPABILITIES} == {
        "account.group_account_manager"
    }
    assert all("res.company" in runtime._MODELS[item] for item in CAPABILITIES)
    assert (
        "account.fiscal.position.account",
        "unlink",
    ) in runtime._ACCESS["fiscal_position.account_mappings.replace"]


def test_parameter_validation_matches_public_boundaries() -> None:
    assert runtime._valid_parameters(
        "fiscal_position.create", {"name": "Domestic", "sequence": 10}, 7
    )
    assert runtime._valid_parameters(
        "fiscal_position.create",
        {"name": "Domestic", "country_id": 1, "country_group_id": 2},
        7,
    )
    assert runtime._valid_parameters(
        "fiscal_position.account_mappings.replace",
        {"fiscal_position_id": 21, "mappings": []},
        7,
    )
    assert runtime._valid_parameters(
        "fiscal_position.create", {"name": "X" * 256}, 7
    )
    assert not runtime._valid_parameters(
        "journal.group.create", {"name": "X" * 257}, 7
    )
    assert not runtime._valid_parameters(
        "fiscal_position.account_mappings.replace",
        {
            "fiscal_position_id": 21,
            "mappings": [
                {"source_account_id": 31, "destination_account_id": 41},
                {"source_account_id": 31, "destination_account_id": 42},
            ],
        },
        7,
    )


def test_fiscal_position_create_forces_company_and_replays_exact_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    position = _position()
    created: dict[str, Any] = {}
    existing = Records()
    model = SimpleNamespace(
        search=lambda *_args, **_kwargs: existing,
        create=lambda values: (created.update(values), position)[1],
    )
    monkeypatch.setattr(runtime, "_scoped", lambda *_args: model)
    monkeypatch.setattr(
        runtime, "_validate_fiscal_position_references", lambda *_args: None
    )

    result, replay = runtime._create_fiscal_position(
        object(), {"name": "Domestic"}, 7, Failure
    )
    assert not replay
    assert created == {"name": "Domestic", "company_id": 7}
    assert result["id"] == 21

    existing.append(position)
    _, replay = runtime._create_fiscal_position(
        object(), {"name": "Domestic"}, 7, Failure
    )
    assert replay

    position.sequence = 11
    with pytest.raises(Failure) as raised:
        runtime._create_fiscal_position(
            object(), {"name": "Domestic"}, 7, Failure
        )
    assert raised.value.code == "state_conflict"


def test_archive_restore_are_target_state_replay_safe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    position = _position()
    monkeypatch.setattr(runtime, "_fiscal_position", lambda *_args: position)
    parameters = {"fiscal_position_id": 21}

    _, replay = runtime._transition_fiscal_position(
        object(), "fiscal_position.archive", parameters, 7, Failure
    )
    assert not replay and not position.active
    _, replay = runtime._transition_fiscal_position(
        object(), "fiscal_position.archive", parameters, 7, Failure
    )
    assert replay
    _, replay = runtime._transition_fiscal_position(
        object(), "fiscal_position.restore", parameters, 7, Failure
    )
    assert not replay and position.active


def test_fiscal_position_note_compares_odoo_sanitized_html(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    position = _position()
    position.note = "<p>Updated</p>"
    monkeypatch.setattr(runtime, "_sanitize_html", lambda value: f"<p>{value}</p>")

    assert runtime._configuration_matches(position, {"note": "Updated"})


def test_journal_group_create_forces_company_and_native_unique_replay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    group = Record(
        id=51,
        name="Primary",
        sequence=10,
        excluded_journal_ids=Records(),
        company_id=Record(id=7),
    )
    created: dict[str, Any] = {}
    existing = Records()
    model = SimpleNamespace(
        search=lambda *_args, **_kwargs: existing,
        create=lambda values: (created.update(values), group)[1],
    )
    monkeypatch.setattr(runtime, "_scoped", lambda *_args: model)

    result, replay = runtime._write_journal_group(
        object(), "journal.group.create", {"name": "Primary"}, 7, Failure
    )
    assert not replay
    assert created == {"name": "Primary", "company_id": 7}
    assert result["model"] == "account.journal.group"

    existing.append(group)
    _, replay = runtime._write_journal_group(
        object(), "journal.group.create", {"name": "Primary"}, 7, Failure
    )
    assert replay


def test_content_operations_have_deterministic_keys() -> None:
    update = runtime._deterministic_key(
        "fiscal_position.update",
        {"fiscal_position_id": 21, "changes": {"sequence": 20}},
        7,
    )
    replace = runtime._deterministic_key(
        "fiscal_position.account_mappings.replace",
        {
            "fiscal_position_id": 21,
            "mappings": [{"source_account_id": 31, "destination_account_id": 41}],
        },
        7,
    )
    assert update and update.startswith("fiscal_position.update:21:")
    assert replace and replace.startswith(
        "fiscal_position.account_mappings.replace:21:"
    )


def test_mapping_replace_uses_exact_company_accounts_and_native_lines(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    position = _position()
    accounts = Records(
        [
            Record(id=31, company_ids=Records([Record(id=7)])),
            Record(id=41, company_ids=Records([Record(id=7)])),
        ]
    )
    created: list[dict[str, Any]] = []

    class MappingModel:
        def create(self, values: list[dict[str, Any]]) -> None:
            created.extend(values)
            position.account_ids.extend(
                Record(
                    id=50 + index,
                    account_src_id=Record(id=item["account_src_id"]),
                    account_dest_id=Record(id=item["account_dest_id"]),
                )
                for index, item in enumerate(values, 1)
            )

    monkeypatch.setattr(runtime, "_fiscal_position", lambda *_args: position)
    monkeypatch.setattr(runtime, "_ensure_ids", lambda *_args, **_kwargs: accounts)
    monkeypatch.setattr(runtime, "_scoped", lambda *_args: MappingModel())
    parameters = {
        "fiscal_position_id": 21,
        "mappings": [{"source_account_id": 31, "destination_account_id": 41}],
    }

    result, replay = runtime._replace_fiscal_position_mappings(
        object(), parameters, 7, Failure
    )

    assert not replay
    assert created == [{"position_id": 21, "account_src_id": 31, "account_dest_id": 41}]
    assert result["line_ids"] == [51]


def test_mapping_replace_accepts_empty_list_to_clear_all(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    position = _position()
    position.account_ids.append(
        Record(id=51, account_src_id=Record(id=31), account_dest_id=Record(id=41))
    )
    monkeypatch.setattr(runtime, "_fiscal_position", lambda *_args: position)
    monkeypatch.setattr(runtime, "_ensure_ids", lambda *_args, **_kwargs: Records())

    result, replay = runtime._replace_fiscal_position_mappings(
        object(), {"fiscal_position_id": 21, "mappings": []}, 7, Failure
    )

    assert not replay
    assert result["line_ids"] == []
