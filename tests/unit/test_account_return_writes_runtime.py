from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge import core_writes_runtime as writes


class Failure(RuntimeError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        exit_code: int,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code
        self.retryable = retryable
        self.details = details or {}


def _relation_id(value: Any) -> Any:
    return getattr(value, "id", value)


class Records:
    def __init__(self, model: Model, records: list[Record] | None = None) -> None:
        self.model = model
        self.records = records or []

    def __iter__(self):
        return iter(self.records)

    def __len__(self) -> int:
        return len(self.records)

    def __bool__(self) -> bool:
        return bool(self.records)

    def __getattr__(self, name: str) -> Any:
        if len(self.records) != 1:
            raise AttributeError(name)
        return getattr(self.records[0], name)

    @property
    def id(self) -> int | bool:
        return self.records[0].id if len(self.records) == 1 else False

    @property
    def ids(self) -> list[int]:
        return [record.id for record in self.records]

    def invalidate_recordset(self, fields: list[str]) -> None:
        for record in self.records:
            record.invalidate_recordset(fields)


class Record:
    def __init__(self, model: Model, record_id: int, **values: Any) -> None:
        self._model = model
        self.id = record_id
        for field_name, value in values.items():
            setattr(self, field_name, value)

    @property
    def env(self) -> Env:
        return self._model.env

    def invalidate_recordset(self, fields: list[str]) -> None:
        self.env.calls.append(("invalidate_recordset", self._model.name, self.id, fields))

    def write(self, values: dict[str, Any]) -> None:
        self.env.calls.append(("write", self._model.name, self.id, dict(values)))
        for field_name, value in values.items():
            setattr(self, field_name, value)

    def _get_period_boundaries(
        self, company: Record, period_date: date
    ) -> tuple[date, date]:
        assert self._model.name == "account.return.type"
        self.env.calls.append(
            ("_get_period_boundaries", self.id, company.id, period_date.isoformat())
        )
        return date(period_date.year, 1, 1), date(period_date.year, 12, 31)

    def _all_branches_selected(self) -> bool:
        assert self._model.name == "res.company"
        self.env.calls.append(("_all_branches_selected", self.id))
        return self.all_branches_selected

    def action_create_manual_account_returns(self) -> None:
        assert self._model.name == "account.return.creation.wizard"
        self.env.calls.append(("action_create_manual_account_returns", self.id))
        self.env.add_return(
            name=f"{self.return_type_id.name} {self.date_from[:4]}",
            return_type=self.return_type_id,
            company=self.company_id,
            date_from=self.date_from,
            date_to=self.date_to,
        )

    def refresh_checks(self) -> None:
        assert self._model.name == "account.return"
        self.env.calls.append(("refresh_checks", self.id))
        if not self.check_ids:
            self.env.add_check(self, result="todo")

    def action_validate(self) -> None:
        assert self._model.name == "account.return"
        self.env.calls.append(("action_validate", self.id))
        self.state = "reviewed"
        self.date_lock = "2027-12-31"

    def action_submit(self) -> None:
        assert self._model.name == "account.return"
        self.env.calls.append(("action_submit", self.id))
        self.state = "submitted"
        self.date_submission = "2028-01-02"
        self.is_completed = True

    def action_archive(self) -> None:
        assert self._model.name == "account.return"
        self.env.calls.append(("action_archive", self.id))
        self.active = False

    def action_unarchive(self) -> None:
        assert self._model.name == "account.return"
        self.env.calls.append(("action_unarchive", self.id))
        self.active = True

    def action_delete(self) -> None:
        assert self._model.name == "account.return"
        self.env.calls.append(("action_delete", self.id))
        self._model.remove(self)


class Model:
    def __init__(self, env: Env, name: str) -> None:
        self.env = env
        self.name = name
        self.records: list[Record] = []

    def with_company(self, company_id: int) -> Model:
        assert company_id == self.env.company.id
        self.env.calls.append(("with_company", self.name, company_id))
        return self

    def with_context(self, **context: Any) -> Model:
        assert context == {"active_test": False, "allowed_company_ids": [1]}
        self.env.calls.append(("with_context", self.name, context))
        return self

    def has_access(self, operation: str) -> bool:
        self.env.calls.append(("has_access", self.name, operation))
        return self.env.denied_access != (self.name, operation)

    def browse(self, record_id: int) -> Records:
        return Records(self, [record for record in self.records if record.id == record_id])

    def search_count(self, domain: list[Any], limit: int | None = None) -> int:
        return len(self.search(domain, limit=limit))

    def search(
        self,
        domain: list[Any],
        limit: int | None = None,
        order: str | None = None,
    ) -> Records:
        del order
        selected = [record for record in self.records if _matches(record, domain)]
        if limit is not None:
            selected = selected[:limit]
        return Records(self, selected)

    def create(self, values: dict[str, Any]) -> Records:
        assert self.name == "account.return.creation.wizard"
        self.env.next_id += 1
        wizard = Record(
            self,
            self.env.next_id,
            company_id=self.env.record("res.company", values["company_id"]),
            category=values["category"],
            return_type_id=self.env.record(
                "account.return.type", values["return_type_id"]
            ),
            date_from=values["date_from"],
            date_to=values["date_to"],
        )
        self.records.append(wizard)
        self.env.calls.append(("create", self.name, dict(values)))
        return Records(self, [wizard])

    def remove(self, record: Record) -> None:
        self.records.remove(record)
        if self.name == "account.return":
            checks = self.env.models["account.return.check"]
            checks.records = [
                check for check in checks.records if check.return_id.id != record.id
            ]


def _matches(record: Record, domain: list[Any]) -> bool:
    for field_name, operator, expected in domain:
        assert operator == "="
        actual = _relation_id(getattr(record, field_name, False))
        if actual in (None, False):
            actual = False
        expected_value = _relation_id(expected)
        if expected_value in (None, False):
            expected_value = False
        if actual != expected_value:
            return False
    return True


class Registry:
    def __init__(self, env: Env) -> None:
        self.env = env

    def get(self, name: str) -> Model | None:
        return self.env.models.get(name)


class User:
    def __init__(self, env: Env) -> None:
        self.env = env

    def has_group(self, group: str) -> bool:
        self.env.calls.append(("has_group", group))
        return self.env.group_allowed


class Env:
    uid = 5

    def __init__(self) -> None:
        self.calls: list[tuple[Any, ...]] = []
        self.denied_access: tuple[str, str] | None = None
        self.group_allowed = True
        self.next_id = 900
        self.models = {
            name: Model(self, name)
            for name in (
                "res.company",
                "account.return.type",
                "account.return",
                "account.return.check",
                "account.return.creation.wizard",
            )
        }
        self.registry = Registry(self)
        self.user = User(self)
        country = SimpleNamespace(id=233)
        self.company = self.add(
            "res.company",
            1,
            name="Main Company",
            parent_id=False,
            child_ids=False,
            all_branches_selected=True,
            account_fiscal_country_id=country,
        )
        self.other_company = self.add(
            "res.company",
            2,
            name="Other Company",
            parent_id=False,
            child_ids=False,
            all_branches_selected=True,
            account_fiscal_country_id=country,
        )
        self.return_type = self.add(
            "account.return.type",
            17,
            name="Corporate Tax",
            category="account_return",
            report_id=False,
            states_workflow="generic_state_review_submit",
            country_id=country,
        )

    def __getitem__(self, name: str) -> Model:
        return self.models[name]

    def add(self, model_name: str, record_id: int, **values: Any) -> Record:
        record = Record(self.models[model_name], record_id, **values)
        self.models[model_name].records.append(record)
        return record

    def record(self, model_name: str, record_id: int) -> Record:
        matches = [
            record for record in self.models[model_name].records if record.id == record_id
        ]
        assert len(matches) == 1
        return matches[0]

    def add_return(
        self,
        *,
        record_id: int | None = None,
        name: str = "Corporate Tax 2027",
        return_type: Record | None = None,
        company: Record | None = None,
        date_from: str = "2027-01-01",
        date_to: str = "2027-12-31",
        manually_created: bool = True,
        state: str = "new",
        active: bool = True,
        is_completed: bool = False,
    ) -> Record:
        if record_id is None:
            self.next_id += 1
            record_id = self.next_id
        account_return = self.add(
            "account.return",
            record_id,
            name=name,
            type_id=return_type or self.return_type,
            company_id=company or self.company,
            date_from=date_from,
            date_to=date_to,
            manually_created=manually_created,
            state=state,
            active=active,
            is_completed=is_completed,
            date_lock=False,
            date_submission=False,
            check_ids=Records(self.models["account.return.check"]),
        )
        return account_return

    def add_check(
        self,
        account_return: Record,
        *,
        record_id: int | None = None,
        result: str = "todo",
        state: str = "new",
    ) -> Record:
        if record_id is None:
            self.next_id += 1
            record_id = self.next_id
        check = self.add(
            "account.return.check",
            record_id,
            name="Review the return",
            return_id=account_return,
            code="ODACV4-CHECK",
            state=state,
            result=result,
            refresh_result=False,
            records_count=0,
        )
        account_return.check_ids = Records(
            self.models["account.return.check"],
            [*account_return.check_ids.records, check],
        )
        return check


def _payload(capability_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
    key = writes._deterministic_key(capability_id, parameters, 1)
    return {
        "capability_id": capability_id,
        "company_id": 1,
        "idempotency_key": key or f"{capability_id}:client-request-0001",
        "confirmation": capability_id,
        "parameters": parameters,
    }


def _dispatch(
    env: Env, capability_id: str, parameters: dict[str, Any]
) -> dict[str, Any]:
    return writes.dispatch(env, _payload(capability_id, parameters), 1, Failure)


def test_create_uses_the_native_wizard_and_replays_the_natural_key() -> None:
    env = Env()
    parameters = {
        "return_type_id": 17,
        "date_from": "2027-01-01",
        "date_to": "2027-12-31",
    }

    created = _dispatch(env, "account.return.create", parameters)
    return_id = created["result"]["id"]
    assert created["idempotent_replay"] is False
    assert created["result"]["state"] == "new"
    assert created["result"]["source_id"] == 17
    assert ("_get_period_boundaries", 17, 1, "2027-01-01") in env.calls
    assert ("action_create_manual_account_returns", return_id - 1) in env.calls

    account_return = env.record("account.return", return_id)
    account_return.state = "submitted"
    account_return.is_completed = True
    replay = _dispatch(env, "account.return.create", parameters)
    assert replay["idempotent_replay"] is True
    assert replay["result"]["id"] == return_id
    assert replay["result"]["state"] == "submitted"
    assert len(
        [call for call in env.calls if call[0] == "action_create_manual_account_returns"]
    ) == 1


def test_refresh_and_check_update_map_to_native_methods_and_replay() -> None:
    env = Env()
    account_return = env.add_return(record_id=61)

    refreshed = _dispatch(
        env, "account.return.checks.refresh", {"return_id": account_return.id}
    )
    assert refreshed["result"]["line_ids"] == []
    check_id = env.models["account.return.check"].records[0].id
    assert refreshed["idempotent_replay"] is False
    assert refreshed["result"]["source_id"] == env.return_type.id
    assert ("refresh_checks", account_return.id) in env.calls

    replay = _dispatch(
        env, "account.return.checks.refresh", {"return_id": account_return.id}
    )
    assert replay["idempotent_replay"] is True

    updated = _dispatch(
        env,
        "account.return.check.result.update",
        {"check_id": check_id, "result": "reviewed"},
    )
    assert updated["idempotent_replay"] is False
    assert updated["result"]["state"] == "reviewed"
    assert updated["result"]["source_id"] == account_return.id
    assert ("write", "account.return.check", check_id, {"result": "reviewed"}) in env.calls

    replay = _dispatch(
        env,
        "account.return.check.result.update",
        {"check_id": check_id, "result": "reviewed"},
    )
    assert replay["idempotent_replay"] is True


def test_validate_and_submit_use_native_internal_workflow_actions() -> None:
    env = Env()
    account_return = env.add_return(record_id=61)

    validated = _dispatch(
        env, "account.return.validate", {"return_id": account_return.id}
    )
    assert validated["idempotent_replay"] is False
    assert validated["result"]["state"] == "reviewed"
    assert validated["result"]["source_id"] == env.return_type.id
    assert ("action_validate", account_return.id) in env.calls

    replay = _dispatch(
        env, "account.return.validate", {"return_id": account_return.id}
    )
    assert replay["idempotent_replay"] is True
    assert replay["result"]["state"] == "reviewed"

    submitted = _dispatch(
        env, "account.return.mark_submitted", {"return_id": account_return.id}
    )
    assert submitted["idempotent_replay"] is False
    assert submitted["result"]["state"] == "submitted"
    assert account_return.is_completed is True
    assert ("action_submit", account_return.id) in env.calls

    validate_after_submit = _dispatch(
        env, "account.return.validate", {"return_id": account_return.id}
    )
    assert validate_after_submit["idempotent_replay"] is True
    assert validate_after_submit["result"]["state"] == "submitted"


def test_archive_restore_and_delete_use_native_actions_without_a_tombstone() -> None:
    env = Env()
    account_return = env.add_return(record_id=61)

    archived = _dispatch(
        env, "account.return.archive", {"return_id": account_return.id}
    )
    assert archived["idempotent_replay"] is False
    assert archived["result"]["state"] == "archived"
    assert archived["result"]["source_id"] == env.return_type.id
    assert ("action_archive", account_return.id) in env.calls

    assert _dispatch(
        env, "account.return.archive", {"return_id": account_return.id}
    )["idempotent_replay"] is True

    restored = _dispatch(
        env, "account.return.restore", {"return_id": account_return.id}
    )
    assert restored["idempotent_replay"] is False
    assert restored["result"]["state"] == "new"
    assert ("action_unarchive", account_return.id) in env.calls

    deleted = _dispatch(
        env, "account.return.delete", {"return_id": account_return.id}
    )
    assert deleted["idempotent_replay"] is False
    assert deleted["result"]["state"] == "deleted"
    assert deleted["result"]["source_id"] == env.return_type.id
    assert ("action_delete", account_return.id) in env.calls
    assert not env.models["account.return"].records

    with pytest.raises(Failure) as caught:
        _dispatch(env, "account.return.delete", {"return_id": account_return.id})
    assert caught.value.code == "record_not_found"


@pytest.mark.parametrize(
    ("mutation", "capability_id", "expected_code"),
    [
        ("automatic", "account.return.checks.refresh", "record_not_found"),
        ("audit", "account.return.validate", "record_not_found"),
        ("report_bound", "account.return.validate", "record_not_found"),
        ("wrong_workflow", "account.return.mark_submitted", "record_not_found"),
        ("other_company", "account.return.archive", "record_not_found"),
        ("submitted", "account.return.archive", "state_conflict"),
        ("inactive", "account.return.delete", "state_conflict"),
    ],
)
def test_return_actions_reject_records_outside_the_fixed_manual_workflow(
    mutation: str, capability_id: str, expected_code: str
) -> None:
    env = Env()
    account_return = env.add_return(record_id=61)
    if mutation == "automatic":
        account_return.manually_created = False
    elif mutation == "audit":
        account_return.type_id.category = "audit"
    elif mutation == "report_bound":
        account_return.type_id.report_id = SimpleNamespace(id=99)
    elif mutation == "wrong_workflow":
        account_return.type_id.states_workflow = "generic_state_review"
    elif mutation == "other_company":
        account_return.company_id = env.other_company
    elif mutation == "submitted":
        account_return.state = "submitted"
        account_return.is_completed = True
    else:
        account_return.active = False

    with pytest.raises(Failure) as caught:
        _dispatch(env, capability_id, {"return_id": account_return.id})
    assert caught.value.code == expected_code


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        ("child_company", "configuration_missing"),
        ("company_with_children", "configuration_missing"),
        ("company_with_hidden_child", "configuration_missing"),
        ("audit", "record_not_found"),
        ("report_bound", "record_not_found"),
        ("wrong_workflow", "record_not_found"),
        ("foreign_country", "record_not_found"),
    ],
)
def test_create_rejects_types_outside_the_fixed_company_workflow(
    mutation: str, expected_code: str
) -> None:
    env = Env()
    if mutation == "child_company":
        env.company.parent_id = env.other_company
    elif mutation == "company_with_children":
        env.company.child_ids = [env.other_company]
        env.company.all_branches_selected = False
    elif mutation == "company_with_hidden_child":
        env.company.all_branches_selected = False
    elif mutation == "audit":
        env.return_type.category = "audit"
    elif mutation == "report_bound":
        env.return_type.report_id = SimpleNamespace(id=99)
    elif mutation == "wrong_workflow":
        env.return_type.states_workflow = "generic_state_review"
    else:
        env.return_type.country_id = SimpleNamespace(id=44)

    with pytest.raises(Failure) as caught:
        _dispatch(
            env,
            "account.return.create",
            {
                "return_type_id": env.return_type.id,
                "date_from": "2027-01-01",
                "date_to": "2027-12-31",
            },
        )
    assert caught.value.code == expected_code
    assert not any(
        call[0] == "action_create_manual_account_returns" for call in env.calls
    )


def test_create_rejects_a_range_spanning_multiple_native_periods() -> None:
    env = Env()
    with pytest.raises(Failure) as caught:
        _dispatch(
            env,
            "account.return.create",
            {
                "return_type_id": env.return_type.id,
                "date_from": "2027-01-01",
                "date_to": "2028-12-31",
            },
        )
    assert caught.value.code == "business_rule_error"
    assert ("_get_period_boundaries", 17, 1, "2027-01-01") in env.calls
    assert not any(
        call[0] == "action_create_manual_account_returns" for call in env.calls
    )


def test_check_result_boundary_and_write_access_fail_before_native_actions() -> None:
    env = Env()
    account_return = env.add_return(record_id=61)
    check = env.add_check(account_return, record_id=71)
    invalid = _payload(
        "account.return.check.result.update",
        {"check_id": check.id, "result": "supervised"},
    )
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, invalid, 1, Failure)
    assert caught.value.code == "bridge_protocol_error"
    assert not any(call[0] == "write" for call in env.calls)

    env.denied_access = ("account.return", "unlink")
    denied = _dispatch(env, "account.return.delete", {"return_id": account_return.id})
    assert denied["access_allowed"] is False
    assert denied["result"] is None
    assert not any(call[0] == "action_delete" for call in env.calls)
