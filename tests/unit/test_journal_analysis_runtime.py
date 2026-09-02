from __future__ import annotations

from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge import journal_analysis_runtime as journal


class Failure(RuntimeError):
    def __init__(self, code: str, message: str, *, exit_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


def _record_id(value: Any) -> Any:
    return getattr(value, "id", value)


def _matches(row: Any, domain: list[tuple[str, str, Any]]) -> bool:
    for field, operator, expected in domain:
        actual = _record_id(getattr(row, field))
        if operator == "=" and actual != expected:
            return False
        if operator == "in" and actual not in expected:
            return False
        if operator == "child_of" and actual != expected:
            return False
        if operator not in {"=", "in", "child_of"}:
            raise AssertionError(f"unsupported fake operator: {operator}")
    return True


class Model:
    def __init__(
        self,
        rows: list[Any] | None = None,
        *,
        fields: set[str] | None = None,
        aggregates: list[tuple[Any, ...]] | None = None,
        access: bool = True,
    ) -> None:
        self.rows = rows or []
        self._fields = {name: object() for name in (fields or set())}
        self.aggregates = aggregates or []
        self.access = access
        self.calls: list[tuple[Any, ...]] = []

    def with_context(self, **context: Any) -> Model:
        self.calls.append(("with_context", context))
        return self

    def has_access(self, operation: str) -> bool:
        self.calls.append(("has_access", operation))
        return self.access

    def search_count(self, domain: list[Any], *, limit: int) -> int:
        self.calls.append(("search_count", domain, limit))
        return min(limit, sum(_matches(row, domain) for row in self.rows))

    def search(self, domain: list[Any], *, limit: int) -> list[Any]:
        self.calls.append(("search", domain, limit))
        return [row for row in self.rows if _matches(row, domain)][:limit]

    def _read_group(
        self,
        domain: list[Any],
        *,
        groupby: list[str],
        aggregates: list[str],
        order: str,
    ) -> list[tuple[Any, ...]]:
        self.calls.append(("_read_group", domain, groupby, aggregates, order))
        return self.aggregates


class JournalRecord:
    def __init__(
        self,
        record_id: int,
        company: Any,
        *,
        accounting_date: date,
        code: str = "INV",
        name: str = "Customer Invoices",
    ) -> None:
        self.id = record_id
        self.company_id = company
        self.code = code
        self.name = name
        self.accounting_date = accounting_date
        self.calls: list[tuple[Any, ...]] = []

    def with_company(self, company: Any) -> JournalRecord:
        self.calls.append(("with_company", company))
        return self

    def with_context(self, **context: Any) -> JournalRecord:
        self.calls.append(("with_context", context))
        return self


class User:
    def __init__(self, allowed: bool = True) -> None:
        self.allowed = allowed

    def has_group(self, xml_id: str) -> bool:
        assert xml_id == "account.group_account_readonly"
        return self.allowed


class Registry:
    def __init__(self, models: dict[str, Model]) -> None:
        self.models = models

    def get(self, name: str) -> Model | None:
        return self.models.get(name)


class Env:
    def __init__(self, models: dict[str, Model]) -> None:
        self.uid = 5
        self.user = User()
        self.models = models
        self.registry = Registry(models)

    def __getitem__(self, name: str) -> Model:
        return self.models[name]


def _fixture() -> tuple[Env, dict[str, Any]]:
    currency = SimpleNamespace(id=6, name="CNY")
    company = SimpleNamespace(id=7, currency_id=currency)
    other_company = SimpleNamespace(id=8, currency_id=currency)
    invoice_journal = JournalRecord(9, company, accounting_date=date(2026, 8, 31))
    bank_journal = JournalRecord(
        10,
        company,
        accounting_date=date(2026, 8, 28),
        code="BNK",
        name="Bank",
    )
    cash = SimpleNamespace(id=101, code="1001", name="Cash", company_ids=[company])
    bank = SimpleNamespace(id=102, code="1002", name="Bank", company_ids=[company])
    plan = SimpleNamespace(
        id=11,
        name="Projects",
        parent_id=False,
        _column_name=lambda: "x_plan1_id",
    )
    project_a = SimpleNamespace(
        id=21,
        name="Project A",
        code="A",
        plan_id=plan,
        root_plan_id=plan,
        company_id=company,
    )
    project_b = SimpleNamespace(
        id=22,
        name="Project B",
        code=False,
        plan_id=plan,
        root_plan_id=plan,
        company_id=False,
    )
    analytic_line_model = Model(
        fields=set(journal._ANALYTIC_LINE_FIELDS) | {"x_plan1_id"}
    )
    analytic_line_model._fields["x_plan1_id"] = SimpleNamespace(
        comodel_name="account.analytic.account"
    )
    models = {
        "res.company": Model([company, other_company], fields={"currency_id"}),
        "res.currency": Model([currency], fields={"name"}),
        "account.journal": Model(
            [invoice_journal, bank_journal], fields=set(journal._JOURNAL_FIELDS)
        ),
        "account.account": Model([cash, bank], fields={"code", "name", "company_ids"}),
        "account.move.line": Model(fields=set(journal._MOVE_LINE_FIELDS)),
        "account.analytic.plan": Model(
            [plan], fields=set(journal._ANALYTIC_PLAN_FIELDS)
        ),
        "account.analytic.account": Model(
            [project_a, project_b], fields=set(journal._ANALYTIC_ACCOUNT_FIELDS)
        ),
        "account.analytic.line": analytic_line_model,
    }
    return Env(models), {
        "company": company,
        "invoice_journal": invoice_journal,
        "bank_journal": bank_journal,
        "cash": cash,
        "bank": bank,
        "plan": plan,
        "project_a": project_a,
        "project_b": project_b,
    }


def _dispatch(
    env: Env, capability_id: str, parameters: dict[str, Any]
) -> dict[str, Any]:
    return journal.dispatch(
        env,
        {
            "capability_id": capability_id,
            "company_id": 7,
            "parameters": parameters,
        },
        7,
        failure_type=Failure,
    )


def test_resolve_reads_native_computed_field_with_fixed_context_without_sudo() -> None:
    env, records = _fixture()
    parameters = {"journal_id": 9, "date": "2026-08-28", "has_tax": True}

    page = _dispatch(env, "journal.accounting_date.resolve", parameters)

    assert page["items"] == [
        {
            "company_id": 7,
            "journal": {
                "id": 9,
                "code": "INV",
                "name": "Customer Invoices",
            },
            "requested_date": "2026-08-28",
            "has_tax": True,
            "accounting_date": "2026-08-31",
            "adjusted": True,
        }
    ]
    assert records["invoice_journal"].calls == [
        ("with_company", records["company"]),
        (
            "with_context",
            {"move_date": date(2026, 8, 28), "has_tax": True},
        ),
    ]
    assert env.models["account.journal"].calls[-1] == (
        "search",
        [("id", "=", 9), ("company_id", "=", 7)],
        2,
    )


def test_resolve_returns_empty_page_for_a_company_scoped_missing_journal() -> None:
    env, _ = _fixture()

    page = _dispatch(
        env,
        "journal.accounting_date.resolve",
        {"journal_id": 999, "date": "2026-08-28", "has_tax": False},
    )

    assert page["items"] == []
    assert page["cursor_found"] is True


def test_account_summary_uses_fixed_posted_domain_aggregates_and_order() -> None:
    env, records = _fixture()
    env.models["account.move.line"].aggregates = [
        (records["bank"], 1, Decimal(0), Decimal(3), Decimal(-3)),
        (records["cash"], 2, Decimal("10.500"), Decimal(2), Decimal("8.5")),
    ]
    parameters = {
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
        "group_by": "account",
    }

    page = _dispatch(env, "journal_item.analysis.summary", parameters)

    item = page["items"][0]
    assert [group["group"]["id"] for group in item["groups"]] == [101, 102]
    assert item["groups"][0] == {
        "group": {"id": 101, "code": "1001", "name": "Cash"},
        "row_count": 2,
        "debit": "10.5",
        "credit": "2",
        "balance": "8.5",
    }
    assert item["totals"] == {
        "row_count": 3,
        "debit": "10.5",
        "credit": "5",
        "balance": "5.5",
    }
    assert env.models["account.move.line"].calls[-1] == (
        "_read_group",
        [
            ("company_id", "=", 7),
            ("parent_state", "=", "posted"),
            ("date", ">=", "2026-01-01"),
            ("date", "<=", "2026-12-31"),
        ],
        ["account_id"],
        ["__count", "debit:sum", "credit:sum", "balance:sum"],
        "account_id asc",
    )


def test_journal_summary_and_empty_summary_have_fixed_shapes() -> None:
    env, records = _fixture()
    env.models["account.move.line"].aggregates = [
        (records["bank_journal"], 4, 12, 7, 5)
    ]
    parameters = {
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
        "group_by": "journal",
    }

    item = _dispatch(env, "journal_item.analysis.summary", parameters)["items"][0]

    assert item["basis"] == "posted_entries"
    assert item["group_by"] == "journal"
    assert item["groups"] == [
        {
            "group": {"id": 10, "code": "BNK", "name": "Bank"},
            "row_count": 4,
            "debit": "12",
            "credit": "7",
            "balance": "5",
        }
    ]

    env.models["account.move.line"].aggregates = []
    empty = _dispatch(env, "journal_item.analysis.summary", parameters)["items"][0]
    assert empty["groups"] == []
    assert empty["totals"] == {
        "row_count": 0,
        "debit": "0",
        "credit": "0",
        "balance": "0",
    }


def test_analytic_summary_uses_dynamic_plan_column_and_company_scope() -> None:
    env, records = _fixture()
    env.models["account.analytic.line"].aggregates = [
        (records["project_b"], 1, Decimal(-2), Decimal("0.5")),
        (records["project_a"], 2, Decimal("10.500"), Decimal(3)),
    ]
    parameters = {
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
        "plan_id": 11,
        "analytic_account_id": None,
    }

    item = _dispatch(env, "analytic.line.summary", parameters)["items"][0]

    assert item == {
        "company_id": 7,
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
        "basis": "analytic_lines",
        "group_by": "analytic_account",
        "plan": {"id": 11, "name": "Projects"},
        "company_currency": {"id": 6, "code": "CNY"},
        "groups": [
            {
                "analytic_account": {"id": 21, "name": "Project A", "code": "A"},
                "row_count": 2,
                "amount": "10.5",
                "unit_amount": "3",
            },
            {
                "analytic_account": {
                    "id": 22,
                    "name": "Project B",
                    "code": None,
                },
                "row_count": 1,
                "amount": "-2",
                "unit_amount": "0.5",
            },
        ],
        "totals": {"row_count": 3, "amount": "8.5", "unit_amount": "3.5"},
    }
    assert env.models["account.analytic.line"].calls[-1] == (
        "_read_group",
        [
            ("company_id", "=", 7),
            ("date", ">=", "2026-01-01"),
            ("date", "<=", "2026-12-31"),
            ("x_plan1_id.plan_id", "child_of", 11),
        ],
        ["x_plan1_id"],
        ["id:count", "amount:sum", "unit_amount:sum"],
        "x_plan1_id asc",
    )


def test_analytic_summary_filters_account_and_rejects_cross_company_group() -> None:
    env, records = _fixture()
    parameters = {
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
        "plan_id": 11,
        "analytic_account_id": 21,
    }
    env.models["account.analytic.line"].aggregates = [(records["project_a"], 1, 4, 1)]

    item = _dispatch(env, "analytic.line.summary", parameters)["items"][0]
    assert item["groups"][0]["analytic_account"]["id"] == 21
    assert env.models["account.analytic.line"].calls[-1][1][-1] == (
        "x_plan1_id",
        "=",
        21,
    )

    other_company = env.models["res.company"].rows[1]
    foreign = SimpleNamespace(
        id=99,
        name="Foreign",
        code=None,
        plan_id=records["plan"],
        root_plan_id=records["plan"],
        company_id=other_company,
    )
    env.models["account.analytic.line"].aggregates = [(foreign, 1, 1, 0)]
    with pytest.raises(Failure) as caught:
        _dispatch(env, "analytic.line.summary", parameters)
    assert caught.value.code == "odoo_runtime_error"


@pytest.mark.parametrize(
    "payload",
    [
        {
            "capability_id": "journal_item.analysis.summary",
            "company_id": 7,
            "parameters": {
                "date_from": "2026-01-01",
                "date_to": "2026-12-31",
                "group_by": "partner",
            },
        },
        {
            "capability_id": "journal.accounting_date.resolve",
            "company_id": 8,
            "parameters": {
                "journal_id": 9,
                "date": "2026-08-28",
                "has_tax": False,
            },
        },
    ],
)
def test_runtime_rejects_non_allowlisted_payloads(payload: dict[str, Any]) -> None:
    env, _ = _fixture()
    with pytest.raises(Failure) as caught:
        journal.dispatch(env, payload, 7, failure_type=Failure)
    assert caught.value.code == "bridge_protocol_error"
    assert caught.value.exit_code == 7


def test_runtime_gates_acl_and_required_field_shape() -> None:
    env, _ = _fixture()
    env.models["account.move.line"].access = False
    page = _dispatch(
        env,
        "journal_item.analysis.summary",
        {
            "date_from": "2026-01-01",
            "date_to": "2026-12-31",
            "group_by": "account",
        },
    )
    assert page["access_allowed"] is False
    assert page["items"] == []

    env, _ = _fixture()
    del env.models["account.journal"]._fields["accounting_date"]
    with pytest.raises(Failure) as drift:
        _dispatch(
            env,
            "journal.accounting_date.resolve",
            {"journal_id": 9, "date": "2026-08-28", "has_tax": False},
        )
    assert drift.value.code == "odoo_runtime_error"


def test_runtime_rejects_cross_company_and_nonfinite_aggregate_rows() -> None:
    env, records = _fixture()
    other_company = env.models["res.company"].rows[1]
    cross_company_account = SimpleNamespace(
        id=999, code="9999", name="Other", company_ids=[other_company]
    )
    parameters = {
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
        "group_by": "account",
    }
    env.models["account.move.line"].aggregates = [(cross_company_account, 1, 1, 0, 1)]
    with pytest.raises(Failure) as cross_company:
        _dispatch(env, "journal_item.analysis.summary", parameters)
    assert cross_company.value.code == "odoo_runtime_error"

    env.models["account.move.line"].aggregates = [
        (records["cash"], 1, Decimal("NaN"), 0, 0)
    ]
    with pytest.raises(Failure) as nonfinite:
        _dispatch(env, "journal_item.analysis.summary", parameters)
    assert nonfinite.value.code == "odoo_runtime_error"
