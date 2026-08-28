from __future__ import annotations

import sys
from datetime import date
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge import budget_report_runtime as runtime


class Failure(RuntimeError):
    def __init__(self, code: str, message: str, *, exit_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


class Records(list):
    @property
    def ids(self) -> list[int]:
        return [record.id for record in self]

    def __or__(self, other: Records) -> Records:
        return Records([*self, *(record for record in other if record not in self)])


def _id(value: Any) -> Any:
    return getattr(value, "id", value)


def _matches(record: Any, domain: list[Any]) -> bool:
    for leaf in domain:
        if not isinstance(leaf, tuple):
            raise TypeError(f"unexpected domain token: {leaf!r}")
        field, operator, expected = leaf
        raw_actual = getattr(record, field)
        actual = _id(raw_actual)
        if actual in (None, False):
            actual = False
        expected = (
            [_id(value) for value in expected]
            if isinstance(expected, list)
            else _id(expected)
        )
        if operator == "=" and actual != expected:
            return False
        if operator == "in" and actual not in expected:
            return False
        if operator == "child_of":
            current = raw_actual
            while current not in (None, False) and _id(current) != expected:
                current = getattr(current, "parent_id", None)
            if current in (None, False):
                return False
    return True


class Model:
    def __init__(self, records: list[Any], *, fields: set[str] | None = None) -> None:
        self.records = Records(records)
        self._fields = {name: object() for name in (fields or set())}
        self.contexts: list[dict] = []
        self.access = True

    def with_context(self, **context: Any) -> Model:
        self.contexts.append(context)
        return self

    def has_access(self, operation: str) -> bool:
        assert operation == "read"
        return self.access

    def search(self, domain: list[Any], limit: int | None = None) -> Records:
        result = Records(record for record in self.records if _matches(record, domain))
        return Records(result[:limit] if limit else result)

    def search_count(self, domain: list[Any], limit: int | None = None) -> int:
        return len(self.search(domain, limit=limit))


class Registry:
    def __init__(self, models: dict[str, Model]) -> None:
        self.models = models

    def get(self, name: str) -> Model | None:
        return self.models.get(name)


class User:
    def __init__(self, allowed: bool = True) -> None:
        self.allowed = allowed

    def has_group(self, name: str) -> bool:
        assert name == "account.group_account_readonly"
        return self.allowed


class Env:
    uid = 5

    def __init__(self, models: dict[str, Model], *, group: bool = True) -> None:
        self.models = models
        self.registry = Registry(models)
        self.user = User(group)

    def __getitem__(self, name: str) -> Model:
        return self.models[name]


def _parameters(**updates: Any) -> dict[str, Any]:
    value = {
        "budget_id": 71,
        "budget_line_id": None,
        "date_from": None,
        "date_to": None,
        "plan_id": None,
        "analytic_account_id": None,
        "line_type": None,
        "after": None,
        "limit": 101,
    }
    value.update(updates)
    return value


def _record(record_id: int, **values: Any) -> Any:
    return SimpleNamespace(id=record_id, **values)


def _fixture_env() -> tuple[Env, dict[str, Any]]:
    company = _record(7, name="Demo")
    root_plan = _record(21, name="Projects", parent_id=None)
    root_plan._column_name = lambda: "account_id"
    plan = _record(22, name="Delivery", parent_id=root_plan)
    sibling_plan = _record(23, name="Sales", parent_id=root_plan)
    account = _record(
        31,
        name="Project Alpha",
        plan_id=plan,
        root_plan_id=root_plan,
        company_id=company,
    )
    budget = _record(
        71,
        name="FY2026",
        date_from=date(2026, 1, 1),
        date_to=date(2026, 12, 31),
        company_id=company,
    )
    line1 = _record(901, budget_analytic_id=budget, company_id=company)
    line2 = _record(902, budget_analytic_id=budget, company_id=company)
    user = _record(5, name="V4 Accountant")
    fields = {name: set(values) for name, values in runtime._REQUIRED_FIELDS.items()}
    models = {
        name: Model([], fields=fields.get(name, set())) for name in runtime._MODELS
    }
    models["res.company"] = Model([company], fields=fields.get("res.company", set()))
    models["res.users"] = Model([user], fields=fields["res.users"])
    models["budget.analytic"] = Model([budget], fields=fields["budget.analytic"])
    models["budget.line"] = Model([line1, line2], fields=fields["budget.line"])
    models["account.analytic.plan"] = Model(
        [root_plan, plan, sibling_plan], fields=fields["account.analytic.plan"]
    )
    models["account.analytic.account"] = Model(
        [account], fields=fields["account.analytic.account"]
    )
    models["budget.report"] = Model([], fields={*fields["budget.report"], "account_id"})
    return Env(models), {
        "company": company,
        "plan": plan,
        "account": account,
        "budget": budget,
    }


def test_runtime_payload_is_exact_and_keeps_the_full_composite_position() -> None:
    after = {
        "date": "2026-08-24",
        "row_key": "aal501",
        "budget_line_id": 901,
        "line_type": "achieved",
        "source_model": "account.analytic.line",
        "source_id": 501,
    }
    parameters = _parameters(after=after)
    assert runtime._valid_parameters(parameters) is True
    assert runtime._position_values(after) == (
        "2026-08-24",
        "aal501",
        901,
        "achieved",
        "account.analytic.line",
        501,
    )

    for invalid in (
        {**parameters, "extra": True},
        {**parameters, "after": {"row_key": "aal501"}},
        {**parameters, "after": {**after, "budget_line_id": True}},
        {**parameters, "limit": 1002},
    ):
        assert runtime._valid_parameters(invalid) is False


def test_effective_filters_enforce_budget_line_company_and_plan_membership() -> None:
    env, records = _fixture_env()
    parameters = _parameters(
        budget_line_id=901,
        plan_id=21,
        analytic_account_id=31,
    )

    budget, date_from, date_to, column = runtime._effective_filters(
        env, 7, parameters, Failure
    )

    assert budget is records["budget"]
    assert (date_from, date_to, column) == (
        "2026-01-01",
        "2026-12-31",
        "account_id",
    )
    assert all(
        model.contexts[-1]
        == {
            "allowed_company_ids": [7],
            "active_test": False,
        }
        for model in (
            env["budget.analytic"],
            env["budget.line"],
            env["account.analytic.plan"],
            env["account.analytic.account"],
        )
    )

    with pytest.raises(Failure) as caught:
        runtime._effective_filters(env, 7, _parameters(budget_line_id=999), Failure)
    assert caught.value.code == "record_not_found"

    with pytest.raises(Failure) as caught:
        runtime._effective_filters(
            env,
            7,
            _parameters(plan_id=23, analytic_account_id=31),
            Failure,
        )
    assert caught.value.code == "record_not_found"


def test_acl_scope_requires_the_public_models_and_accounting_read_access() -> None:
    env, _ = _fixture_env()
    page = runtime._scope_page(env, 7, Failure)
    assert page == {
        "user_id": 5,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "cursor_found": True,
        "items": [],
    }

    env["budget.report"].access = False
    assert runtime._scope_page(env, 7, Failure)["access_allowed"] is False


def test_raw_rows_keep_same_aal_id_for_two_overlapping_budget_lines() -> None:
    env, records = _fixture_env()
    rows = [
        {
            "id": "aal501",
            "date": date(2026, 8, 24),
            "budget_analytic_id": 71,
            "budget_line_id": line_id,
            "res_model": "account.analytic.line",
            "res_id": 501,
            "description": "Project effort",
            "company_id": 7,
            "user_id": 5,
            "line_type": "achieved",
            "budget": 0,
            "achieved": 125.5,
            "theoretical": 0,
            "account_id": 31,
        }
        for line_id in (901, 902)
    ]

    items = runtime._items(
        env,
        7,
        rows,
        budget=records["budget"],
        plan_columns=[("account_id", 21)],
    )

    assert [item["row_key"] for item in items] == ["aal501", "aal501"]
    assert [item["budget_line"]["id"] for item in items] == [901, 902]
    assert [item["source"]["id"] for item in items] == [501, 501]
    assert all(item["achieved_amount"] == "125.5" for item in items)


def test_query_path_selects_raw_rows_without_browsing_text_ids(monkeypatch) -> None:
    class SQL:
        def __init__(self, code: Any = "", *params: Any) -> None:
            self.code = code
            self.params = params

        def join(self, values: Any) -> SQL:
            return SQL("join", *tuple(values))

    odoo = ModuleType("odoo")
    tools = ModuleType("odoo.tools")
    tools.SQL = SQL
    odoo.__path__ = []
    odoo.tools = tools
    monkeypatch.setitem(sys.modules, "odoo", odoo)
    monkeypatch.setitem(sys.modules, "odoo.tools", tools)

    class Query:
        def __init__(self, limit: int) -> None:
            self.limit = limit
            self.where: list[SQL] = []
            self.order: SQL | None = None

        def add_where(self, clause: SQL) -> None:
            self.where.append(clause)

        def select(self, *expressions: SQL) -> tuple[str, Query, tuple[SQL, ...]]:
            return ("select", self, expressions)

    class ReportModel:
        _table = "budget_report"

        def __init__(self) -> None:
            self.queries: list[Query] = []

        def with_context(self, **_context: Any) -> ReportModel:
            return self

        def _search(self, _domain: list[Any], limit: int) -> Query:
            query = Query(limit)
            self.queries.append(query)
            return query

        def _field_to_sql(self, _table: str, name: str, _query: Query) -> SQL:
            return SQL(name)

    report_model = ReportModel()

    class QueryEnv:
        def __getitem__(self, name: str) -> ReportModel:
            assert name == "budget.report"
            return report_model

        def execute_query(self, selected: tuple) -> list[tuple]:
            _kind, _query, expressions = selected
            if len(expressions) == 1 and expressions[0].code == "1":
                return [(1,)]
            row = (
                "aal501",
                date(2026, 8, 24),
                71,
                901,
                "account.analytic.line",
                501,
                "Project effort",
                7,
                5,
                "achieved",
                0,
                125.5,
                0,
                31,
            )
            return [row, (*row[:3], 902, *row[4:])]

    after = {
        "date": "2026-08-23",
        "row_key": "aal500",
        "budget_line_id": 900,
        "line_type": "achieved",
        "source_model": "account.analytic.line",
        "source_id": 500,
    }
    found, rows = runtime._query_rows(
        QueryEnv(),
        7,
        _parameters(after=after),
        date_from="2026-01-01",
        date_to="2026-12-31",
        plan_column=None,
        plan_columns=[("account_id", 21)],
    )

    assert found is True
    assert [row["id"] for row in rows] == ["aal501", "aal501"]
    assert [row["budget_line_id"] for row in rows] == [901, 902]
    assert len(report_model.queries) == 2
    assert len(report_model.queries[0].where) == 1
    assert len(report_model.queries[1].where) == 1
    assert report_model.queries[1].order is not None


def test_dispatch_rejects_expanded_payload_before_odoo_access() -> None:
    with pytest.raises(Failure) as caught:
        runtime.dispatch(
            object(),
            {"company_id": 7, "parameters": _parameters(), "extra": True},
            7,
            failure_type=Failure,
        )
    assert caught.value.code == "bridge_protocol_error"
