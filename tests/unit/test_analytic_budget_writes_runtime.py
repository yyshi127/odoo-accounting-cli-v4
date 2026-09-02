from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from types import MappingProxyType, SimpleNamespace
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


def _record_id(value: Any) -> Any:
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
    def ids(self) -> list[int]:
        return [record.id for record in self.records]

    @property
    def id(self) -> int | bool:
        return self.records[0].id if len(self.records) == 1 else False

    def write(self, values: dict[str, Any]) -> None:
        for record in self.records:
            record.write(values)

    def unlink(self) -> None:
        for record in list(self.records):
            record.unlink()

    def invalidate_recordset(self, fields: list[str]) -> None:
        for record in self.records:
            record.invalidate_recordset(fields)


class Record:
    def __init__(self, model: Model, record_id: int, **values: Any) -> None:
        self._model = model
        self.id = record_id
        for name, value in values.items():
            setattr(self, name, value)

    def write(self, values: dict[str, Any]) -> None:
        self._model.env.calls.append(("write", self._model.name, self.id, dict(values)))
        self._model.apply_values(self, values)

    def unlink(self) -> None:
        self._model.env.calls.append(("unlink", self._model.name, self.id))
        self._model.remove(self)

    def invalidate_recordset(self, _fields: list[str]) -> None:
        return None

    def action_budget_confirm(self) -> None:
        terminal = "revised" if getattr(self, "children_ids", False) else "confirmed"
        self._transition("action_budget_confirm", terminal)

    def action_budget_draft(self) -> None:
        self._transition("action_budget_draft", "draft")

    def action_budget_cancel(self) -> None:
        self._transition("action_budget_cancel", "canceled")

    def action_budget_done(self) -> None:
        self._transition("action_budget_done", "done")

    def _transition(self, method: str, state: str) -> None:
        self._model.env.calls.append((method, self.id))
        self.state = state


class Model:
    def __init__(self, env: Env, name: str) -> None:
        self.env = env
        self.name = name
        self.records: list[Record] = []
        self._fields: dict[str, Any] = {}

    def with_context(self, **context: Any) -> Model:
        self.env.contexts.append((self.name, context))
        return self

    def with_company(self, company_id: int) -> Model:
        assert company_id == self.env.company.id
        return self

    def has_access(self, operation: str) -> bool:
        self.env.calls.append(("has_access", self.name, operation))
        return self.env.denied_access != (self.name, operation)

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

    def browse(self, ids: int | list[int]) -> Records:
        requested = [ids] if isinstance(ids, int) else ids
        return Records(self, [record for record in self.records if record.id in requested])

    def create(self, values: dict[str, Any] | list[dict[str, Any]]) -> Records:
        rows = values if isinstance(values, list) else [values]
        created = [self._create_one(row) for row in rows]
        self.env.calls.append(("create", self.name, values))
        return Records(self, created)

    def _create_one(self, values: dict[str, Any]) -> Record:
        self.env.next_id += 1
        resolved = self._resolved(values)
        if self.name == "account.analytic.plan":
            parent = resolved.get("parent_id", False)
            resolved.setdefault("company_id", False)
            resolved.setdefault("color", 0)
            resolved.setdefault("default_applicability", "optional")
            resolved["root_plan_id"] = parent.root_plan_id if parent else False
        elif self.name == "account.analytic.account":
            plan = resolved["plan_id"]
            resolved.setdefault("active", True)
            resolved.setdefault("code", False)
            resolved.setdefault("partner_id", False)
            resolved["root_plan_id"] = plan.root_plan_id
        elif self.name == "account.analytic.line":
            resolved["amount"] = Decimal(str(resolved["amount"]))
            resolved["unit_amount"] = Decimal(str(resolved["unit_amount"]))
            resolved.setdefault("ref", False)
            resolved.setdefault("category", "other")
            resolved.setdefault("move_line_id", False)
        elif self.name == "budget.analytic":
            resolved.setdefault("state", "draft")
            resolved["budget_line_ids"] = Records(self.env.models["budget.line"])
            resolved["children_ids"] = []
        elif self.name == "budget.line":
            resolved["budget_amount"] = Decimal(str(resolved["budget_amount"]))
            for column in ("account_id", "x_plan2_id"):
                resolved.setdefault(column, False)
            resolved["company_id"] = resolved["budget_analytic_id"].company_id
        record = Record(self, self.env.next_id, **resolved)
        self.records.append(record)
        if self.name == "budget.line":
            budget = record.budget_analytic_id
            budget.budget_line_ids = Records(
                self, [*budget.budget_line_ids.records, record]
            )
        return record

    def _resolved(self, values: dict[str, Any]) -> dict[str, Any]:
        resolved = dict(values)
        relations = {
            "company_id": "res.company",
            "partner_id": "res.partner",
            "parent_id": "account.analytic.plan",
            "plan_id": "account.analytic.plan",
            "user_id": "res.users",
            "budget_analytic_id": "budget.analytic",
            "account_id": "account.analytic.account",
            "x_plan2_id": "account.analytic.account",
        }
        for field_name, model_name in relations.items():
            if field_name not in resolved:
                continue
            value = resolved[field_name]
            if value in (None, False):
                resolved[field_name] = False
            elif isinstance(value, int):
                resolved[field_name] = self.env.models[model_name].browse(value).records[0]
        return resolved

    def apply_values(self, record: Record, values: dict[str, Any]) -> None:
        resolved = self._resolved(values)
        for field_name, value in resolved.items():
            setattr(record, field_name, value)

    def remove(self, record: Record) -> None:
        self.records.remove(record)
        if self.name == "budget.line":
            budget = record.budget_analytic_id
            budget.budget_line_ids = Records(
                self, [line for line in budget.budget_line_ids if line.id != record.id]
            )


def _matches(record: Record, domain: list[Any]) -> bool:
    for field_name, operator, expected in domain:
        actual = _record_id(getattr(record, field_name, False))
        if actual in (None, False):
            actual = False
        if operator == "=" and actual != _record_id(expected):
            return False
        if operator == "!=" and actual == _record_id(expected):
            return False
        if operator == "in" and actual not in [_record_id(item) for item in expected]:
            return False
        if operator == "=like":
            suffix = expected.removeprefix("%")
            if not isinstance(actual, str) or not actual.endswith(suffix):
                return False
    return True


class Registry:
    def __init__(self, env: Env) -> None:
        self.env = env

    def get(self, name: str) -> Model | None:
        return self.env.models.get(name)


class AuthUser:
    def __init__(self, env: Env) -> None:
        self.env = env

    def has_group(self, group: str) -> bool:
        self.env.calls.append(("has_group", group))
        return self.env.group_allowed


class Env:
    uid = 5

    def __init__(self) -> None:
        self.calls: list[tuple[Any, ...]] = []
        self.contexts: list[tuple[str, dict[str, Any]]] = []
        self.denied_access: tuple[str, str] | None = None
        self.group_allowed = True
        self.next_id = 1000
        self.models = {
            name: Model(self, name)
            for name in (
                "res.company",
                "res.partner",
                "res.users",
                "account.analytic.plan",
                "account.analytic.account",
                "account.analytic.line",
                "budget.analytic",
                "budget.line",
            )
        }
        self.registry = Registry(self)
        self.user = AuthUser(self)
        self.company = self.add("res.company", 7, name="Demo")
        self.other_company = self.add("res.company", 8, name="Other")
        self.responsible = self.add("res.users", self.uid, name="Accountant")
        self.partner = self.add("res.partner", 41, name="Global", company_id=False)
        self.company_partner = self.add(
            "res.partner", 42, name="Company", company_id=self.company
        )
        self.foreign_partner = self.add(
            "res.partner", 43, name="Foreign", company_id=self.other_company
        )

        self.root_plan = self.add(
            "account.analytic.plan",
            21,
            name="Projects",
            parent_id=False,
            company_id=False,
            color=0,
            default_applicability="optional",
        )
        self.root_plan.root_plan_id = self.root_plan
        self.root_plan._column_name = lambda: "account_id"
        self.child_plan = self.add(
            "account.analytic.plan",
            22,
            name="Delivery",
            parent_id=self.root_plan,
            root_plan_id=self.root_plan,
            company_id=False,
            color=0,
            default_applicability="optional",
        )
        self.second_root = self.add(
            "account.analytic.plan",
            23,
            name="Departments",
            parent_id=False,
            company_id=False,
            color=0,
            default_applicability="optional",
        )
        self.second_root.root_plan_id = self.second_root
        self.second_root._column_name = lambda: "x_plan2_id"
        self.foreign_plan = self.add(
            "account.analytic.plan",
            24,
            name="Foreign",
            parent_id=False,
            company_id=self.other_company,
            color=0,
            default_applicability="optional",
        )
        self.foreign_plan.root_plan_id = self.foreign_plan
        self.foreign_plan._column_name = lambda: "x_foreign_id"

        self.account = self.add_account(31, self.child_plan, self.company)
        self.second_account = self.add_account(32, self.second_root, False)
        self.same_root_account = self.add_account(33, self.child_plan, self.company)
        self.foreign_account = self.add_account(34, self.foreign_plan, self.other_company)

        relation = lambda: SimpleNamespace(comodel_name="account.analytic.account")
        self.models["budget.line"]._fields = {
            "account_id": relation(),
            "x_plan2_id": relation(),
            "budget_analytic_id": SimpleNamespace(comodel_name="budget.analytic"),
        }

    def __getitem__(self, name: str) -> Model:
        return self.models[name]

    def add(self, model_name: str, record_id: int, **values: Any) -> Record:
        model = self.models[model_name]
        record = Record(model, record_id, **values)
        model.records.append(record)
        return record

    def add_account(self, record_id: int, plan: Record, company: Any) -> Record:
        return self.add(
            "account.analytic.account",
            record_id,
            name=f"Account {record_id}",
            code=False,
            active=True,
            plan_id=plan,
            root_plan_id=plan.root_plan_id,
            partner_id=False,
            company_id=company,
        )

    def add_budget(self, record_id: int = 71, *, state: str = "draft") -> Record:
        return self.add(
            "budget.analytic",
            record_id,
            name="FY2026",
            date_from="2026-01-01",
            date_to="2026-12-31",
            state=state,
            budget_type="both",
            company_id=self.company,
            user_id=self.responsible,
            budget_line_ids=Records(self.models["budget.line"]),
            children_ids=[],
        )

    def add_analytic_line(
        self,
        record_id: int,
        *,
        account: Record | None = None,
        company: Any | None = None,
        category: str = "other",
        move_line_id: Any = False,
    ) -> Record:
        return self.add(
            "account.analytic.line",
            record_id,
            name=f"Manual line {record_id}",
            date="2026-09-01",
            amount=Decimal(10),
            unit_amount=Decimal(1),
            ref=False,
            account_id=account or self.account,
            company_id=company or self.company,
            category=category,
            move_line_id=move_line_id,
        )


def _payload(
    capability_id: str,
    parameters: dict[str, Any],
    *,
    key: str | None = None,
    company_id: int = 7,
) -> dict[str, Any]:
    expected = writes._deterministic_key(capability_id, parameters, company_id)
    return {
        "capability_id": capability_id,
        "company_id": company_id,
        "idempotency_key": key or expected or "create-key-0001",
        "confirmation": capability_id,
        "parameters": parameters,
    }


def _dispatch(
    env: Env,
    capability_id: str,
    parameters: dict[str, Any],
    *,
    key: str | None = None,
) -> dict[str, Any]:
    return writes.dispatch(env, _payload(capability_id, parameters, key=key), 7, Failure)


def _analytic_create_parameters(env: Env) -> dict[str, Any]:
    return {
        "name": "Project Alpha",
        "plan_id": env.child_plan.id,
        "code": "ALPHA",
        "partner_id": env.partner.id,
    }


def _budget_create_parameters() -> dict[str, Any]:
    return {
        "name": "FY2027",
        "date_from": "2027-01-01",
        "date_to": "2027-12-31",
        "budget_type": "both",
    }


def test_analytic_account_create_replays_exact_visible_marker() -> None:
    env = Env()
    parameters = _analytic_create_parameters(env)

    first = _dispatch(env, "analytic.account.create", parameters)
    second = _dispatch(env, "analytic.account.create", parameters)

    assert first["result"]["model"] == "account.analytic.account"
    assert first["result"]["source_id"] == env.child_plan.id
    assert first["result"]["state"] == "active"
    assert first["result"]["line_ids"] == []
    assert first["result"]["name"].startswith("Project Alpha [ODACV4:")
    assert second["idempotent_replay"] is True
    creates = [call for call in env.calls if call[:2] == ("create", "account.analytic.account")]
    assert len(creates) == 1
    created = env.models["account.analytic.account"].browse(
        first["result"]["id"]
    ).records[0]
    created.code = "CHANGED"
    with pytest.raises(Failure) as caught:
        _dispatch(env, "analytic.account.create", parameters)
    assert caught.value.code == "idempotency_conflict"


def test_analytic_account_update_preserves_marker_and_replays() -> None:
    env = Env()
    created = _dispatch(env, "analytic.account.create", _analytic_create_parameters(env))
    account = env.models["account.analytic.account"].browse(created["result"]["id"])
    suffix = account.name[account.name.index(" [ODACV4:") :]
    parameters = {
        "analytic_account_id": account.id,
        "changes": {
            "name": "Renamed",
            "code": None,
            "partner_id": env.company_partner.id,
            "active": False,
        },
    }

    first = _dispatch(env, "analytic.account.update", parameters)
    second = _dispatch(env, "analytic.account.update", parameters)

    assert account.name == f"Renamed{suffix}"
    assert account.code is False
    assert account.partner_id.id == env.company_partner.id
    assert first["result"]["state"] == "archived"
    assert first["result"]["source_id"] == env.child_plan.id
    assert second["idempotent_replay"] is True
    write = next(call for call in env.calls if call[:2] == ("write", "account.analytic.account"))
    assert "plan_id" not in write[3]
    assert "company_id" not in write[3]


def test_analytic_references_are_visible_and_company_scoped() -> None:
    env = Env()
    parameters = _analytic_create_parameters(env)
    parameters["plan_id"] = env.foreign_plan.id
    with pytest.raises(Failure) as caught:
        _dispatch(env, "analytic.account.create", parameters)
    assert caught.value.code == "record_not_found"
    assert not any(call[:2] == ("create", "account.analytic.account") for call in env.calls)

    env = Env()
    parameters = _analytic_create_parameters(env)
    parameters["partner_id"] = env.foreign_partner.id
    with pytest.raises(Failure) as caught:
        _dispatch(env, "analytic.account.create", parameters)
    assert caught.value.code == "record_not_found"
    assert not any(call[:2] == ("create", "account.analytic.account") for call in env.calls)


def test_analytic_subplan_create_replays_and_root_update_is_forbidden() -> None:
    env = Env()
    parameters = {
        "name": "Delivery East",
        "parent_plan_id": env.root_plan.id,
        "color": None,
        "default_applicability": None,
    }

    first = _dispatch(env, "analytic.plan.create", parameters)
    replay = _dispatch(env, "analytic.plan.create", parameters)

    assert first["result"]["model"] == "account.analytic.plan"
    assert first["result"]["source_id"] == env.root_plan.id
    assert first["result"]["name"].startswith("Delivery East [ODACV4:")
    assert replay["idempotent_replay"] is True
    creates = [
        call for call in env.calls if call[:2] == ("create", "account.analytic.plan")
    ]
    assert len(creates) == 1

    update = {
        "plan_id": first["result"]["id"],
        "changes": {"name": "Delivery West", "color": 5},
    }
    changed = _dispatch(env, "analytic.plan.update", update)
    unchanged = _dispatch(env, "analytic.plan.update", update)
    assert changed["result"]["name"].startswith("Delivery West [ODACV4:")
    assert unchanged["idempotent_replay"] is True

    with pytest.raises(Failure) as caught:
        _dispatch(
            env,
            "analytic.plan.update",
            {"plan_id": env.root_plan.id, "changes": {"name": "No"}},
        )
    assert caught.value.code == "state_conflict"


def test_analytic_account_archive_restore_replay_and_company_scope() -> None:
    env = Env()
    parameters = {"analytic_account_id": env.account.id}

    archived = _dispatch(env, "analytic.account.archive", parameters)
    archived_replay = _dispatch(env, "analytic.account.archive", parameters)
    restored = _dispatch(env, "analytic.account.restore", parameters)
    restored_replay = _dispatch(env, "analytic.account.restore", parameters)

    assert archived["result"]["state"] == "archived"
    assert archived_replay["idempotent_replay"] is True
    assert restored["result"]["state"] == "active"
    assert restored_replay["idempotent_replay"] is True

    with pytest.raises(Failure) as caught:
        _dispatch(
            env,
            "analytic.account.archive",
            {"analytic_account_id": env.foreign_account.id},
        )
    assert caught.value.code == "record_not_found"


def test_manual_analytic_line_lifecycle_and_generated_line_boundary() -> None:
    env = Env()
    parameters = {
        "name": "Manual adjustment",
        "date": "2026-09-01",
        "amount": "-10.5",
        "analytic_account_id": env.account.id,
        "reference": None,
        "unit_amount": "2.5",
    }

    created = _dispatch(env, "analytic.line.create", parameters)
    replay = _dispatch(env, "analytic.line.create", parameters)
    assert created["result"]["state"] == "manual"
    assert created["result"]["source_id"] == env.account.id
    assert replay["idempotent_replay"] is True

    line_id = created["result"]["id"]
    update = {
        "analytic_line_id": line_id,
        "changes": {
            "amount": "10",
            "analytic_account_id": env.same_root_account.id,
            "reference": "Correction",
        },
    }
    changed = _dispatch(env, "analytic.line.update", update)
    unchanged = _dispatch(env, "analytic.line.update", update)
    assert changed["result"]["source_id"] == env.same_root_account.id
    assert unchanged["idempotent_replay"] is True

    deleted = _dispatch(env, "analytic.line.delete", {"analytic_line_id": line_id})
    assert deleted["result"]["state"] == "deleted"
    assert not env.models["account.analytic.line"].browse(line_id)
    with pytest.raises(Failure) as absent:
        _dispatch(env, "analytic.line.delete", {"analytic_line_id": line_id})
    assert absent.value.code == "record_not_found"

    generated = env.add_analytic_line(81, move_line_id=SimpleNamespace(id=501))
    with pytest.raises(Failure) as protected:
        _dispatch(
            env,
            "analytic.line.update",
            {"analytic_line_id": generated.id, "changes": {"amount": "1"}},
        )
    assert protected.value.code == "record_not_found"
    assert generated.amount == Decimal(10)


def test_manual_analytic_line_is_company_scoped() -> None:
    env = Env()
    foreign = env.add_analytic_line(
        82,
        account=env.foreign_account,
        company=env.other_company,
    )
    with pytest.raises(Failure) as caught:
        _dispatch(
            env,
            "analytic.line.delete",
            {"analytic_line_id": foreign.id},
        )
    assert caught.value.code == "record_not_found"
    assert env.models["account.analytic.line"].browse(foreign.id)


def test_budget_create_and_draft_update_preserve_marker_and_replay() -> None:
    env = Env()
    parameters = _budget_create_parameters()
    first = _dispatch(env, "budget.create", parameters)
    replay = _dispatch(env, "budget.create", parameters)
    budget = env.models["budget.analytic"].browse(first["result"]["id"])
    suffix = budget.name[budget.name.index(" [ODACV4:") :]

    assert first["result"]["state"] == "draft"
    assert first["result"]["line_ids"] == []
    assert budget.company_id.id == 7
    assert budget.user_id.id == env.uid
    assert replay["idempotent_replay"] is True

    update = {
        "budget_id": budget.id,
        "changes": {"name": "Plan 2027", "date_from": "2027-02-01"},
    }
    changed = _dispatch(env, "budget.update_draft", update)
    unchanged = _dispatch(env, "budget.update_draft", update)
    assert budget.name == f"Plan 2027{suffix}"
    assert budget.date_from == "2027-02-01"
    assert changed["idempotent_replay"] is False
    assert unchanged["idempotent_replay"] is True


def test_budget_update_enforces_final_dates_and_draft_state() -> None:
    env = Env()
    budget = env.add_budget()
    invalid = {"budget_id": budget.id, "changes": {"date_from": "2027-01-01"}}
    with pytest.raises(Failure) as caught:
        _dispatch(env, "budget.update_draft", invalid)
    assert caught.value.code == "state_conflict"
    assert not any(call[:2] == ("write", "budget.analytic") for call in env.calls)

    budget.state = "confirmed"
    exact = {"budget_id": budget.id, "changes": {"name": budget.name}}
    with pytest.raises(Failure) as caught:
        _dispatch(env, "budget.update_draft", exact)
    assert caught.value.code == "state_conflict"


def test_budget_lines_replace_uses_dynamic_root_plan_columns_and_replays() -> None:
    env = Env()
    budget = env.add_budget()
    parameters = {
        "budget_id": budget.id,
        "lines": [
            {
                "budget_amount": "1000.00",
                "analytic_account_ids": [env.account.id, env.second_account.id],
            },
            {
                "budget_amount": "-250",
                "analytic_account_ids": [env.same_root_account.id],
            },
        ],
    }

    first = _dispatch(env, "budget.lines.replace", parameters)
    second = _dispatch(env, "budget.lines.replace", parameters)

    assert first["idempotent_replay"] is False
    assert second["idempotent_replay"] is True
    assert first["result"]["line_ids"] == sorted(first["result"]["line_ids"])
    assert len(first["result"]["line_ids"]) == 2
    ordered = sorted(budget.budget_line_ids, key=lambda line: line.sequence)
    assert ordered[0].account_id.id == env.account.id
    assert ordered[0].x_plan2_id.id == env.second_account.id
    assert ordered[0].budget_amount == Decimal("1000.00")
    assert ordered[1].account_id.id == env.same_root_account.id
    creates = [call for call in env.calls if call[:2] == ("create", "budget.line")]
    assert len(creates) == 1


def test_budget_lines_replace_accepts_read_only_odoo_field_mapping() -> None:
    env = Env()
    env.models["budget.line"]._fields = MappingProxyType(
        env.models["budget.line"]._fields
    )
    budget = env.add_budget()

    page = _dispatch(
        env,
        "budget.lines.replace",
        {
            "budget_id": budget.id,
            "lines": [
                {"budget_amount": "10", "analytic_account_ids": [env.account.id]}
            ],
        },
    )

    assert page["result"]["line_ids"]
    assert page["idempotent_replay"] is False


def test_budget_lines_validate_all_plans_before_mutation() -> None:
    env = Env()
    budget = env.add_budget()
    valid = {
        "budget_id": budget.id,
        "lines": [
            {"budget_amount": "10", "analytic_account_ids": [env.account.id]}
        ],
    }
    _dispatch(env, "budget.lines.replace", valid)
    original_ids = budget.budget_line_ids.ids
    env.calls.clear()
    conflicting = {
        "budget_id": budget.id,
        "lines": [
            {
                "budget_amount": "20",
                "analytic_account_ids": [
                    env.account.id,
                    env.same_root_account.id,
                ],
            }
        ],
    }

    with pytest.raises(Failure) as caught:
        _dispatch(env, "budget.lines.replace", conflicting)

    assert caught.value.code == "business_rule_error"
    assert budget.budget_line_ids.ids == original_ids
    assert not any(call[0] in {"unlink", "create"} for call in env.calls)


def test_budget_lines_enforce_account_company_and_draft_state() -> None:
    env = Env()
    budget = env.add_budget()
    foreign = {
        "budget_id": budget.id,
        "lines": [
            {
                "budget_amount": "10",
                "analytic_account_ids": [env.foreign_account.id],
            }
        ],
    }
    with pytest.raises(Failure) as caught:
        _dispatch(env, "budget.lines.replace", foreign)
    assert caught.value.code == "record_not_found"

    budget.state = "confirmed"
    valid = {
        "budget_id": budget.id,
        "lines": [
            {"budget_amount": "10", "analytic_account_ids": [env.account.id]}
        ],
    }
    with pytest.raises(Failure) as caught:
        _dispatch(env, "budget.lines.replace", valid)
    assert caught.value.code == "state_conflict"


@pytest.mark.parametrize(
    ("capability_id", "initial", "terminal", "method"),
    (
        ("budget.confirm", "draft", "confirmed", "action_budget_confirm"),
        ("budget.reset_to_draft", "confirmed", "draft", "action_budget_draft"),
        ("budget.cancel", "draft", "canceled", "action_budget_cancel"),
        ("budget.mark_done", "confirmed", "done", "action_budget_done"),
    ),
)
def test_budget_lifecycle_calls_fixed_native_action_and_replays(
    capability_id: str, initial: str, terminal: str, method: str
) -> None:
    env = Env()
    budget = env.add_budget(state=initial)
    parameters = {"budget_id": budget.id}

    first = _dispatch(env, capability_id, parameters)
    second = _dispatch(env, capability_id, parameters)

    assert first["result"]["state"] == terminal
    assert first["idempotent_replay"] is False
    assert second["idempotent_replay"] is True
    assert [call[0] for call in env.calls].count(method) == 1


def test_budget_confirm_accepts_native_revised_terminal_state() -> None:
    env = Env()
    budget = env.add_budget()
    budget.children_ids = [object()]
    parameters = {"budget_id": budget.id}

    first = _dispatch(env, "budget.confirm", parameters)
    second = _dispatch(env, "budget.confirm", parameters)

    assert first["result"]["state"] == "revised"
    assert first["idempotent_replay"] is False
    assert second["result"]["state"] == "revised"
    assert second["idempotent_replay"] is True
    assert [call[0] for call in env.calls].count("action_budget_confirm") == 1


def test_budget_confirm_treats_existing_revised_state_as_replay() -> None:
    env = Env()
    budget = env.add_budget(state="revised")

    page = _dispatch(env, "budget.confirm", {"budget_id": budget.id})

    assert page["result"]["state"] == "revised"
    assert page["idempotent_replay"] is True
    assert not any(call[0] == "action_budget_confirm" for call in env.calls)


@pytest.mark.parametrize(
    ("capability_id", "state"),
    (
        ("budget.confirm", "done"),
        ("budget.cancel", "confirmed"),
        ("budget.mark_done", "draft"),
    ),
)
def test_budget_lifecycle_rejects_disallowed_source_state(
    capability_id: str, state: str
) -> None:
    env = Env()
    budget = env.add_budget(state=state)
    with pytest.raises(Failure) as caught:
        _dispatch(env, capability_id, {"budget_id": budget.id})
    assert caught.value.code == "state_conflict"
    assert not any(call[0].startswith("action_budget_") for call in env.calls)


def test_gate_is_exact_and_never_elevates_company_context() -> None:
    env = Env()
    env.denied_access = ("account.analytic.account", "create")
    page = _dispatch(env, "analytic.account.create", _analytic_create_parameters(env))
    assert page["access_allowed"] is False
    assert page["result"] is None
    assert not any(call[:2] == ("create", "account.analytic.account") for call in env.calls)

    assert writes._ACCESS["budget.lines.replace"] == {
        ("budget.analytic", "read"),
        ("budget.line", "read"),
        ("budget.line", "create"),
        ("budget.line", "unlink"),
        ("account.analytic.plan", "read"),
        ("account.analytic.account", "read"),
    }
    assert all(
        context == {"active_test": False, "allowed_company_ids": [7]}
        for _model, context in env.contexts
    )


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    (
        (
            "analytic.account.create",
            {"name": " x ", "plan_id": 21, "code": None, "partner_id": None},
        ),
        (
            "analytic.account.update",
            {"analytic_account_id": 31, "changes": {"plan_id": 21}},
        ),
        (
            "budget.create",
            {
                "name": "Budget",
                "date_from": "2027-12-31",
                "date_to": "2027-01-01",
                "budget_type": "both",
            },
        ),
        (
            "budget.lines.replace",
            {
                "budget_id": 71,
                "lines": [
                    {"budget_amount": 10, "analytic_account_ids": [32, 31]}
                ],
            },
        ),
    ),
)
def test_invalid_closed_payload_fails_before_orm_access(
    capability_id: str, parameters: dict[str, Any]
) -> None:
    env = Env()
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, _payload(capability_id, parameters), 7, Failure)
    assert caught.value.code == "bridge_protocol_error"
    assert env.calls == []


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    (
        (
            "analytic.account.create",
            {
                "name": "Injected [ODACV4:attacker]",
                "plan_id": 21,
                "code": None,
                "partner_id": None,
            },
        ),
        (
            "analytic.account.update",
            {
                "analytic_account_id": 31,
                "changes": {"name": "Injected [ODACV4:attacker]"},
            },
        ),
        (
            "budget.create",
            {
                "name": "Injected [ODACV4:attacker]",
                "date_from": "2027-01-01",
                "date_to": "2027-12-31",
                "budget_type": "both",
            },
        ),
        (
            "budget.update_draft",
            {
                "budget_id": 71,
                "changes": {"name": "Injected [ODACV4:attacker]"},
            },
        ),
    ),
)
def test_reserved_marker_in_business_name_fails_before_orm_access(
    capability_id: str, parameters: dict[str, Any]
) -> None:
    env = Env()

    with pytest.raises(Failure) as caught:
        writes.dispatch(env, _payload(capability_id, parameters), 7, Failure)

    assert caught.value.code == "bridge_protocol_error"
    assert env.calls == []


def test_deterministic_keys_bind_changes_lines_and_lifecycle() -> None:
    changes = {"name": "Renamed", "active": False}
    canonical = json.dumps(
        changes,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    expected = f"analytic.account.update:31:{hashlib.sha256(canonical).hexdigest()[:32]}"
    assert (
        writes._deterministic_key(
            "analytic.account.update",
            {"analytic_account_id": 31, "changes": changes},
            7,
        )
        == expected
    )
    assert (
        writes._deterministic_key("budget.confirm", {"budget_id": 71}, 7)
        == "budget.confirm:71"
    )

    env = Env()
    with pytest.raises(Failure) as caught:
        writes.dispatch(
            env,
            _payload(
                "budget.confirm",
                {"budget_id": 71},
                key="wrong-key-0001",
            ),
            7,
            Failure,
        )
    assert caught.value.code == "bridge_protocol_error"
    assert env.calls == []
