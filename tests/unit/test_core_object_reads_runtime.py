from __future__ import annotations

import sys
from datetime import date
from decimal import Decimal
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge import core_object_reads_runtime as core
from odoo_accounting_cli_v4.capabilities.core_object_reads import (
    CoreObjectReadError,
    read_core_object,
)

EXPECTED_CAPABILITY_IDS = frozenset(
    {
        "partner.search",
        "partner.get",
        "account.account.get",
        "bank.transaction.get",
        "currency.get",
        "journal.get",
        "journal_item.get",
        "journal_item.search",
        "partner.accounting.get",
        "payment.method.list",
        "payment_term.get",
        "reconciliation.model.list",
        "tax.get",
        "product.search",
        "product.get",
        "analytic.plan.list",
        "analytic.plan.get",
        "analytic.account.search",
        "analytic.account.get",
        "fiscal_position.search",
        "fiscal_position.get",
        "account.tag.list",
        "account.tag.get",
        "tax.group.list",
        "tax.group.get",
        "payment.method.get",
        "reconciliation.model.get",
        "cash_rounding.list",
        "cash_rounding.get",
        "journal.group.list",
        "journal.group.get",
        "incoterm.list",
        "incoterm.get",
        "partner.bank_account.search",
        "partner.bank_account.get",
        "bank.statement.search",
        "bank.statement.get",
        "reconciliation.partial.list",
        "reconciliation.partial.get",
        "reconciliation.full.list",
        "reconciliation.full.get",
        "analytic.line.search",
        "analytic.line.get",
        "analytic.distribution_model.list",
        "analytic.distribution_model.get",
        "analytic.applicability.list",
        "analytic.applicability.get",
        "budget.search",
        "budget.get",
        "budget.line.list",
        "budget.line.get",
        "account.group.list",
        "account.group.get",
        "journal.configuration.inspect",
        "tax.repartition_line.list",
        "tax.repartition_line.get",
        "reconciliation.model.line.list",
        "reconciliation.model.line.get",
        "bank.list",
        "bank.get",
        "report.catalog.list",
        "report.catalog.get",
    }
)
FISCAL_POSITION_MAPPING_CAPABILITY_IDS = frozenset(
    {
        "fiscal_position.account_mapping.list",
        "fiscal_position.tax_mapping.list",
    }
)
ACCOUNTING_INSIGHT_CAPABILITY_IDS = frozenset(
    {
        "invoice.duplicate_candidates.list",
        "invoice.tax_breakdown.inspect",
        "recurring.journal_entry.search",
        "recurring.journal_entry.get",
        "account.transfer_model.search",
        "account.transfer_model.get",
        "partner.credit_exposure.inspect",
        "journal.sequence_irregularity.list",
        "account.lock_exception.search",
        "account.lock_exception.get",
        "report.external_value.search",
        "report.external_value.get",
    }
)
SUPPORTING_OBJECT_CAPABILITY_IDS = frozenset(
    {
        "asset.group.search",
        "asset.group.get",
        "report.budget_definition.search",
        "report.budget_definition.get",
        "report.budget_item.search",
        "report.budget_item.get",
        "tax.unit.search",
        "tax.unit.get",
        "account.return.account_status.search",
        "account.return.account_status.get",
    }
)

GET_ID_FIELDS = {
    "account.account.get": "account_id",
    "journal.get": "journal_id",
    "tax.get": "tax_id",
    "payment_term.get": "payment_term_id",
    "currency.get": "currency_id",
    "partner.accounting.get": "partner_id",
    "bank.transaction.get": "transaction_id",
    "journal_item.get": "line_id",
    "product.get": "product_id",
    "analytic.plan.get": "plan_id",
    "analytic.account.get": "analytic_account_id",
    "fiscal_position.get": "fiscal_position_id",
    "account.tag.get": "tag_id",
    "tax.group.get": "tax_group_id",
    "payment.method.get": "payment_method_line_id",
    "reconciliation.model.get": "reconciliation_model_id",
    "cash_rounding.get": "cash_rounding_id",
    "journal.group.get": "journal_group_id",
    "incoterm.get": "incoterm_id",
    "partner.bank_account.get": "partner_bank_id",
    "bank.statement.get": "bank_statement_id",
    "reconciliation.partial.get": "partial_reconcile_id",
    "reconciliation.full.get": "full_reconcile_id",
    "analytic.line.get": "analytic_line_id",
    "analytic.distribution_model.get": "distribution_model_id",
    "analytic.applicability.get": "applicability_id",
    "budget.get": "budget_id",
    "budget.line.get": "budget_line_id",
    "account.group.get": "account_group_id",
}

PRIMARY_MODELS = {
    "partner.search": "res.partner",
    "partner.get": "res.partner",
    "account.account.get": "account.account",
    "journal.get": "account.journal",
    "tax.get": "account.tax",
    "payment_term.get": "account.payment.term",
    "currency.get": "res.currency",
    "partner.accounting.get": "res.partner",
    "bank.transaction.get": "account.bank.statement.line",
    "journal_item.get": "account.move.line",
    "journal_item.search": "account.move.line",
    "payment.method.list": "account.payment.method.line",
    "reconciliation.model.list": "account.reconcile.model",
    "product.search": "product.product",
    "product.get": "product.product",
    "analytic.plan.list": "account.analytic.plan",
    "analytic.plan.get": "account.analytic.plan",
    "analytic.account.search": "account.analytic.account",
    "analytic.account.get": "account.analytic.account",
    "fiscal_position.search": "account.fiscal.position",
    "fiscal_position.get": "account.fiscal.position",
    "account.tag.list": "account.account.tag",
    "account.tag.get": "account.account.tag",
    "tax.group.list": "account.tax.group",
    "tax.group.get": "account.tax.group",
    "payment.method.get": "account.payment.method.line",
    "reconciliation.model.get": "account.reconcile.model",
    "cash_rounding.list": "account.cash.rounding",
    "cash_rounding.get": "account.cash.rounding",
    "journal.group.list": "account.journal.group",
    "journal.group.get": "account.journal.group",
    "incoterm.list": "account.incoterms",
    "incoterm.get": "account.incoterms",
    "partner.bank_account.search": "res.partner.bank",
    "partner.bank_account.get": "res.partner.bank",
    "bank.statement.search": "account.bank.statement",
    "bank.statement.get": "account.bank.statement",
    "reconciliation.partial.list": "account.partial.reconcile",
    "reconciliation.partial.get": "account.partial.reconcile",
    "reconciliation.full.list": "account.full.reconcile",
    "reconciliation.full.get": "account.full.reconcile",
    "analytic.line.search": "account.analytic.line",
    "analytic.line.get": "account.analytic.line",
    "analytic.distribution_model.list": "account.analytic.distribution.model",
    "analytic.distribution_model.get": "account.analytic.distribution.model",
    "analytic.applicability.list": "account.analytic.applicability",
    "analytic.applicability.get": "account.analytic.applicability",
    "budget.search": "budget.analytic",
    "budget.get": "budget.analytic",
    "budget.line.list": "budget.line",
    "budget.line.get": "budget.line",
    "account.group.list": "account.group",
    "account.group.get": "account.group",
    "journal.configuration.inspect": "account.journal",
    "tax.repartition_line.list": "account.tax.repartition.line",
    "tax.repartition_line.get": "account.tax.repartition.line",
    "reconciliation.model.line.list": "account.reconcile.model.line",
    "reconciliation.model.line.get": "account.reconcile.model.line",
    "bank.list": "res.bank",
    "bank.get": "res.bank",
    "report.catalog.list": "account.report",
    "report.catalog.get": "account.report",
}

GET_OBJECT_IDS = {
    "account.account.get": 31,
    "journal.get": 9,
    "tax.get": 31,
    "payment_term.get": 31,
    "currency.get": 6,
    "partner.accounting.get": 31,
    "bank.transaction.get": 31,
    "journal_item.get": 31,
    "product.get": 31,
    "analytic.plan.get": 31,
    "analytic.account.get": 31,
    "fiscal_position.get": 31,
    "account.tag.get": 31,
    "tax.group.get": 5,
    "payment.method.get": 31,
    "reconciliation.model.get": 31,
    "cash_rounding.get": 31,
    "journal.group.get": 31,
    "incoterm.get": 31,
    "partner.bank_account.get": 31,
    "bank.statement.get": 31,
    "reconciliation.partial.get": 31,
    "reconciliation.full.get": 31,
    "analytic.line.get": 31,
    "analytic.distribution_model.get": 31,
    "analytic.applicability.get": 31,
    "budget.get": 31,
    "budget.line.get": 31,
    "account.group.get": 41,
}

REFERENCE_PAGE_CAPABILITIES = (
    "product.search",
    "analytic.plan.list",
    "analytic.account.search",
    "fiscal_position.search",
    "account.tag.list",
    "tax.group.list",
    "cash_rounding.list",
    "journal.group.list",
    "incoterm.list",
    "partner.bank_account.search",
    "bank.statement.search",
    "reconciliation.partial.list",
    "reconciliation.full.list",
    "analytic.line.search",
    "analytic.distribution_model.list",
    "analytic.applicability.list",
    "budget.search",
    "budget.line.list",
)
REFERENCE_PAGE_DEFAULTS = {
    "product.search": {"query": None, "active": None},
    "analytic.plan.list": {},
    "analytic.account.search": {"query": None, "active": None, "plan_id": None},
    "fiscal_position.search": {
        "query": None,
        "active": None,
        "auto_apply": None,
    },
    "account.tag.list": {},
    "tax.group.list": {},
    "cash_rounding.list": {},
    "journal.group.list": {},
    "incoterm.list": {},
    "partner.bank_account.search": {"partner_id": None, "active": None},
    "bank.statement.search": {
        "journal_id": None,
        "date_from": None,
        "date_to": None,
    },
    "reconciliation.partial.list": {},
    "reconciliation.full.list": {},
    "analytic.line.search": {
        "query": None,
        "date_from": None,
        "date_to": None,
        "analytic_account_id": None,
    },
    "analytic.distribution_model.list": {},
    "analytic.applicability.list": {},
    "budget.search": {
        "query": None,
        "state": None,
        "budget_type": None,
        "date_from": None,
        "date_to": None,
    },
    "budget.line.list": {
        "budget_id": 31,
        "plan_id": None,
        "analytic_account_id": None,
    },
}


@pytest.fixture(autouse=True)
def _fake_odoo_expression(monkeypatch: pytest.MonkeyPatch) -> None:
    def and_domains(domains: list[list[Any]]) -> list[Any]:
        nonempty = [domain for domain in domains if domain]
        return ["&"] * max(0, len(nonempty) - 1) + [
            item for domain in nonempty for item in domain
        ]

    odoo = ModuleType("odoo")
    odoo.__path__ = []  # type: ignore[attr-defined]
    odoo.fields = SimpleNamespace(  # type: ignore[attr-defined]
        Date=SimpleNamespace(context_today=lambda _model: date(2026, 8, 31))
    )
    osv = ModuleType("odoo.osv")
    osv.expression = SimpleNamespace(AND=and_domains)  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "odoo", odoo)
    monkeypatch.setitem(sys.modules, "odoo.osv", osv)


class Failure(RuntimeError):
    def __init__(self, code: str, message: str, *, exit_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


class Record(SimpleNamespace):
    pass


class Records(list[Record]):
    @property
    def ids(self) -> list[int]:
        return [record.id for record in self]

    def exists(self) -> Records:
        return self

    def mapped(self, field: str) -> list[Any]:
        return [getattr(record, field) for record in self]

    def __getattr__(self, name: str) -> Any:
        if len(self) != 1:
            raise AttributeError(name)
        return getattr(self[0], name)


def _record(record_id: int, **values: Any) -> Record:
    return Record(id=record_id, **values)


def _scalar(value: Any) -> Any:
    if isinstance(value, Record):
        return value.id
    if isinstance(value, (list, Records, tuple)):
        return [_scalar(item) for item in value]
    return value


def _field(record: Record, path: str) -> Any:
    def descend(value: Any, names: list[str]) -> Any:
        if value is None or value is False:
            return False
        if isinstance(value, (list, Records, tuple)):
            return [descend(item, names) for item in value]
        if not names:
            return _scalar(value)
        return descend(getattr(value, names[0]), names[1:])

    return descend(record, path.split("."))


def _equal(actual: Any, expected: Any) -> bool:
    if actual is None:
        actual = False
    if expected is None:
        expected = False
    return actual == expected


def _term_matches(record: Record, term: tuple[Any, Any, Any]) -> bool:
    field, operator, expected = term
    actual = _field(record, field)
    expected = _scalar(expected)
    if operator == "child_of":
        related: Any = record
        if field != "id":
            for name in field.split("."):
                related = getattr(related, name)
        expected_ids = set(expected if isinstance(expected, list) else [expected])
        related_values = related if isinstance(related, (list, Records)) else [related]
        for value in related_values:
            while isinstance(value, Record):
                if value.id in expected_ids:
                    return True
                value = getattr(value, "parent_id", False)
        return False
    if operator == "parent_of":
        related: Any = record
        if field != "id":
            for name in field.split("."):
                related = getattr(related, name)
        expected_ids = set(expected if isinstance(expected, list) else [expected])
        related_values = related if isinstance(related, (list, Records)) else [related]

        def descendant_ids(value: Any, seen: set[int]) -> set[int]:
            if not isinstance(value, Record) or value.id in seen:
                return set()
            seen.add(value.id)
            result = {value.id}
            for child in getattr(value, "child_ids", Records()):
                result.update(descendant_ids(child, seen))
            return result

        return any(
            expected_ids & descendant_ids(value, set()) for value in related_values
        )
    if operator == "=":
        if isinstance(actual, list) and not isinstance(expected, list):
            return any(_equal(item, expected) for item in actual)
        return _equal(actual, expected)
    if operator == "!=":
        if isinstance(actual, list) and not isinstance(expected, list):
            return all(not _equal(item, expected) for item in actual)
        return not _equal(actual, expected)
    if operator == "in":
        expected_values = expected if isinstance(expected, list) else [expected]
        if isinstance(actual, list):
            return bool(set(actual) & set(expected_values))
        return actual in expected_values
    if operator == "ilike":
        return str(expected).casefold() in str(actual or "").casefold()
    if operator == ">":
        return actual not in (None, False) and actual > expected
    if operator == ">=":
        return actual not in (None, False) and actual >= expected
    if operator == "<=":
        return actual not in (None, False) and actual <= expected
    raise AssertionError(f"unsupported fake-domain operator: {operator}")


def _matches(record: Record, domain: list[Any]) -> bool:
    def parse(index: int) -> tuple[bool, int]:
        token = domain[index]
        if token == "|":
            left, index = parse(index + 1)
            right, index = parse(index)
            return left or right, index
        if token == "&":
            left, index = parse(index + 1)
            right, index = parse(index)
            return left and right, index
        if token == "!":
            value, index = parse(index + 1)
            return not value, index
        return _term_matches(record, token), index + 1

    index = 0
    result = True
    while index < len(domain):
        value, index = parse(index)
        result = result and value
    return result


class Model:
    def __init__(
        self,
        name: str,
        rows: list[Record] | None = None,
        *,
        fields: set[str] | None = None,
        access: bool = True,
    ) -> None:
        self.name = name
        self.rows = Records(rows or [])
        inferred = {field for row in self.rows for field in vars(row) if field != "id"}
        self._fields = {field: object() for field in (fields or inferred)}
        self.access = access
        self.calls: list[tuple[Any, ...]] = []

    def with_context(self, **context: Any) -> Model:
        self.calls.append(("with_context", context))
        return self

    def with_company(self, company: Records) -> Model:
        self.calls.append(("with_company", company.id))
        return self

    def has_access(self, operation: str) -> bool:
        self.calls.append(("has_access", operation))
        return self.access

    def search_count(self, domain: list[Any], *, limit: int | None = None) -> int:
        self.calls.append(("search_count", domain, limit))
        count = sum(_matches(row, domain) for row in self.rows)
        return min(count, limit) if limit is not None else count

    def search(
        self,
        domain: list[Any],
        *,
        order: str | None = None,
        limit: int | None = None,
    ) -> Records:
        self.calls.append(("search", domain, order, limit))
        rows = [row for row in self.rows if _matches(row, domain)]
        if order:
            for part in reversed(order.split(",")):
                tokens = part.strip().split()
                field = tokens[0]
                reverse = len(tokens) > 1 and tokens[1].lower() == "desc"
                rows.sort(key=lambda row: _field(row, field), reverse=reverse)
        return Records(rows[:limit] if limit is not None else rows)

    def search_read(
        self,
        domain: list[Any],
        *,
        fields: list[str],
        order: str | None = None,
        limit: int | None = None,
        **read_kwargs: Any,
    ) -> list[dict[str, Any]]:
        self.calls.append(("search_read", domain, order, limit, fields))
        if read_kwargs:
            self.calls.append(("read_options", read_kwargs))
        rows = [row for row in self.rows if _matches(row, domain)]
        if order:
            for part in reversed(order.split(",")):
                tokens = part.strip().split()
                field = tokens[0]
                reverse = len(tokens) > 1 and tokens[1].lower() == "desc"
                rows.sort(key=lambda row: _field(row, field), reverse=reverse)
        if limit is not None:
            rows = rows[:limit]

        def read_value(value: Any) -> Any:
            if isinstance(value, Record):
                if read_kwargs.get("load", "_classic_read") is None:
                    return value.id
                label = getattr(value, "name", getattr(value, "complete_name", ""))
                return [value.id, label]
            if isinstance(value, (list, Records, tuple)):
                return [item.id if isinstance(item, Record) else item for item in value]
            return value

        return [
            {field: read_value(getattr(row, field)) for field in fields} for row in rows
        ]

    def browse(self, record_id: int) -> Records:
        self.calls.append(("browse", record_id))
        return Records([row for row in self.rows if row.id == record_id])

    def sudo(self, *_args: Any, **_kwargs: Any) -> None:
        raise AssertionError(f"core-object runtime must never sudo {self.name}")


class Registry:
    def __init__(self, models: dict[str, Model]) -> None:
        self.models = models

    def get(self, name: str) -> Model | None:
        return self.models.get(name)


class User:
    def __init__(self, groups_allowed: bool = True) -> None:
        self.groups_allowed = groups_allowed
        self.calls: list[str] = []

    def has_group(self, xml_id: str) -> bool:
        self.calls.append(xml_id)
        return self.groups_allowed


class Env:
    uid = 5

    def __init__(self, models: dict[str, Model]) -> None:
        self.models = models
        self.registry = Registry(models)
        self.user = User()

    def __getitem__(self, name: str) -> Model:
        return self.models[name]


def _fixture() -> tuple[Env, dict[str, Any]]:
    cny = _record(
        6,
        name="CNY",
        full_name="Chinese Yuan",
        symbol="¥",
        rounding=Decimal("0.0100"),
        decimal_places=2,
        active=True,
        position="before",
        is_current_company_currency=True,
    )
    china = _record(156, name="China")
    japan = _record(157, name="Japan")
    company = _record(
        7, name="Demo Company", currency_id=cny, account_fiscal_country_id=china
    )
    other_company = _record(
        8, name="Other Company", currency_id=cny, account_fiscal_country_id=japan
    )
    cash = _record(
        31,
        code="1000",
        name="Cash",
        account_type="asset_cash",
        active=True,
        reconcile=False,
        company_ids=Records([company]),
    )
    receivable = _record(
        121,
        code="112200",
        name="Accounts Receivable",
        account_type="asset_receivable",
        active=True,
        reconcile=True,
        company_ids=Records([company]),
    )
    payable = _record(
        221,
        code="220200",
        name="Accounts Payable",
        account_type="liability_payable",
        active=True,
        reconcile=True,
        company_ids=Records([company]),
    )
    bank_account = _record(
        101,
        code="100200",
        name="Bank Account",
        account_type="asset_cash",
        active=True,
        reconcile=True,
        company_ids=Records([company]),
    )
    rounding_profit = _record(
        701,
        code="759000",
        name="Cash Rounding Profit",
        account_type="income_other",
        active=True,
        reconcile=False,
        company_ids=Records([company]),
    )
    rounding_loss = _record(
        702,
        code="659000",
        name="Cash Rounding Loss",
        account_type="expense",
        active=True,
        reconcile=False,
        company_ids=Records([company]),
    )
    bank_journal = _record(
        9,
        sequence=10,
        code="BNK1",
        name="Bank",
        type="bank",
        active=True,
        currency_id=False,
        company_id=company,
    )
    misc_journal = _record(
        4,
        sequence=20,
        code="MISC",
        name="Miscellaneous Operations",
        type="general",
        active=True,
        currency_id=False,
        company_id=company,
    )
    other_journal = _record(
        19,
        sequence=10,
        code="OBNK",
        name="Other Bank",
        type="bank",
        active=True,
        currency_id=False,
        company_id=other_company,
    )
    tax_group = _record(
        5,
        name="VAT",
        sequence=10,
        country_id=china,
        preceding_subtotal=False,
        company_id=company,
    )
    tax = _record(
        31,
        sequence=1,
        name="VAT 13%",
        type_tax_use="sale",
        amount_type="percent",
        amount=Decimal("13.00"),
        price_include=False,
        include_base_amount=False,
        is_base_affected=True,
        active=True,
        tax_group_id=tax_group,
        company_id=company,
    )
    term_line = _record(
        301,
        value="percent",
        value_amount=Decimal("100.00"),
        delay_type="days_after",
        nb_days=30,
        days_next_month="10",
    )
    payment_term = _record(
        31,
        sequence=10,
        name="30 Days",
        active=True,
        company_id=False,
        display_on_invoice=True,
        early_discount=False,
        discount_percentage=Decimal("0.00"),
        discount_days=0,
        early_pay_discount_computation="included",
        line_ids=Records([term_line]),
    )
    term_line.payment_id = payment_term
    partner = _record(
        31,
        complete_name="Fixture Partner",
        ref="PARTNER-31",
        active=True,
        is_company=True,
        company_id=False,
        customer_rank=1,
        supplier_rank=0,
        property_account_receivable_id=receivable,
        property_account_payable_id=payable,
    )
    fixture_bank = _record(18, name="Fixture Bank", bic=False)
    partner_banks = [
        _record(
            31,
            acc_number="CN621234",
            acc_holder_name=False,
            acc_type="bank",
            active=True,
            sequence=10,
            partner_id=partner,
            allow_out_payment=True,
            bank_id=fixture_bank,
            currency_id=cny,
            company_id=company,
            journal_id=Records([bank_journal]),
        ),
        _record(
            32,
            acc_number="SHARED-32",
            acc_holder_name="Fixture Holder",
            acc_type="bank",
            active=False,
            sequence=20,
            partner_id=partner,
            allow_out_payment=False,
            bank_id=False,
            currency_id=False,
            company_id=False,
            journal_id=Records(),
        ),
    ]
    bank_journal.bank_account_id = partner_banks[0]
    move = _record(
        301,
        name="MISC/2026/0031",
        state="posted",
        move_type="entry",
        date="2026-08-24",
        ref=False,
        company_id=company,
        journal_id=misc_journal,
    )
    bank_move = _record(
        302,
        name="BNK1/2026/0031",
        state="posted",
        move_type="entry",
        date="2026-08-24",
        ref="BANK/31",
        company_id=company,
        journal_id=bank_journal,
    )
    transaction = _record(
        31,
        company_id=company,
        date="2026-08-24",
        payment_date=False,
        payment_ref="Customer transfer",
        partner_id=partner,
        journal_id=bank_journal,
        amount=Decimal("125.500"),
        currency_id=cny,
        move_id=bank_move,
        is_reconciled=False,
        payment_ids=Records(),
    )
    bank_statements = [
        _record(
            31,
            name="BNK1/2026/08",
            reference=False,
            date="2026-08-24",
            company_id=company,
            journal_id=bank_journal,
            currency_id=cny,
            balance_start=Decimal("100.00"),
            balance_end=Decimal("225.500"),
            balance_end_real=Decimal("225.500"),
            is_complete=True,
            is_valid=True,
            problem_description=False,
            line_ids=Records([transaction]),
        ),
        _record(
            32,
            name="BNK1/2026/09",
            reference="September opening",
            date=False,
            company_id=company,
            journal_id=bank_journal,
            currency_id=cny,
            balance_start=Decimal("225.500"),
            balance_end=Decimal("225.500"),
            balance_end_real=Decimal("225.500"),
            is_complete=False,
            is_valid=False,
            problem_description="Missing closing balance",
            line_ids=Records(),
        ),
    ]
    transaction.statement_id = bank_statements[0]

    def journal_line(record_id: int) -> Record:
        return _record(
            record_id,
            company_id=company,
            date="2026-08-24",
            date_maturity=False,
            move_id=move,
            account_id=receivable,
            partner_id=partner,
            journal_id=misc_journal,
            name="Fixture journal item",
            ref=False,
            debit=Decimal("125.500"),
            credit=Decimal("0.00"),
            balance=Decimal("125.500"),
            amount_currency=Decimal("125.500"),
            currency_id=cny,
            reconciled=False,
            matching_number=False,
            analytic_distribution=False,
            parent_state="posted",
            tax_line_id=False,
            tax_ids=Records(),
            tax_base_amount=Decimal("0.00"),
        )

    journal_lines = [journal_line(31), journal_line(32)]
    partial_reconciles = [
        _record(
            31,
            company_id=company,
            max_date="2026-08-24",
            amount=Decimal("125.500"),
            company_currency_id=cny,
            debit_amount_currency=Decimal("125.500"),
            debit_currency_id=cny,
            credit_amount_currency=Decimal("-125.500"),
            credit_currency_id=cny,
            debit_move_id=journal_lines[0],
            credit_move_id=journal_lines[1],
            full_reconcile_id=False,
            exchange_move_id=False,
        ),
        _record(
            32,
            company_id=company,
            max_date="2026-08-25",
            amount=Decimal("25.00"),
            company_currency_id=cny,
            debit_amount_currency=Decimal("25.00"),
            debit_currency_id=cny,
            credit_amount_currency=Decimal("-25.00"),
            credit_currency_id=cny,
            debit_move_id=journal_lines[0],
            credit_move_id=journal_lines[1],
            full_reconcile_id=False,
            exchange_move_id=bank_move,
        ),
    ]
    full_reconciles = [
        _record(
            31,
            partial_reconcile_ids=Records(partial_reconciles),
            reconciled_line_ids=Records(journal_lines),
        )
    ]
    for line in journal_lines:
        line.matching_number = "31"
        line.full_reconcile_id = full_reconciles[0]
    for partial in partial_reconciles:
        partial.full_reconcile_id = full_reconciles[0]
    payment_method = _record(2, code="manual", name="Manual")

    def payment_method_line(record_id: int) -> Record:
        return _record(
            record_id,
            name="Manual",
            payment_type="inbound",
            sequence=10,
            company_id=company,
            payment_method_id=payment_method,
            journal_id=bank_journal,
            payment_account_id=bank_account,
        )

    payment_method_lines = [payment_method_line(31), payment_method_line(32)]

    def reconcile_model(record_id: int) -> Record:
        return _record(
            record_id,
            name="Bank fees",
            sequence=10,
            active=True,
            company_id=company,
            match_amount="lower",
            match_amount_min=Decimal("0.00"),
            match_amount_max=Decimal("1000.00"),
            match_label="contains",
            match_label_param="fee",
        )

    reconcile_models = [reconcile_model(31), reconcile_model(32)]
    cash_roundings = [
        _record(
            31,
            name="Cash rounding 0.05",
            rounding=Decimal("0.0500"),
            strategy="add_invoice_line",
            rounding_method="HALF-UP",
            profit_account_id=rounding_profit,
            loss_account_id=rounding_loss,
        ),
        _record(
            32,
            name="Round on largest tax",
            rounding=Decimal("1.00"),
            strategy="biggest_tax",
            rounding_method="UP",
            profit_account_id=False,
            loss_account_id=False,
        ),
    ]
    journal_groups = [
        _record(
            31,
            name="Liquidity Journals",
            sequence=10,
            company_id=False,
            excluded_journal_ids=Records([bank_journal, misc_journal]),
        ),
        _record(
            32,
            name="Company Journals",
            sequence=20,
            company_id=company,
            excluded_journal_ids=Records(),
        ),
        _record(
            33,
            name="Other Company Journals",
            sequence=10,
            company_id=other_company,
            excluded_journal_ids=Records([other_journal]),
        ),
    ]
    incoterms = [
        _record(31, code="FOB", name="Free On Board", active=True),
        _record(32, code="CIF", name="Cost, Insurance and Freight", active=False),
    ]
    category = _record(51, name="Services")
    uom = _record(1, name="Units")
    product_template = _record(401, name="Consulting Template")

    def product(record_id: int, *, record_company: Record | bool = False) -> Record:
        return _record(
            record_id,
            name="Consulting Service",
            default_code=f"CONSULT-{record_id}",
            barcode=f"69000000{record_id}",
            active=True,
            type="service",
            is_storable=False,
            product_tmpl_id=product_template,
            categ_id=False if record_id == 31 else category,
            uom_id=uom,
            company_id=record_company,
            currency_id=cny,
            standard_price=Decimal("100.00"),
            list_price=Decimal("500.00"),
        )

    products = [product(31), product(32), product(33, record_company=other_company)]
    parent_plan = _record(
        32,
        name="Management",
        complete_name="Management",
        parent_id=False,
        color=2,
    )

    def analytic_plan(record_id: int) -> Record:
        return _record(
            record_id,
            name="Projects",
            complete_name="Management / Projects",
            parent_id=parent_plan,
            color=4,
        )

    analytic_plans = [analytic_plan(31), parent_plan]

    def analytic_account(
        record_id: int, *, record_company: Record | bool = False
    ) -> Record:
        return _record(
            record_id,
            name="Project Alpha",
            code=f"ALPHA-{record_id}",
            active=True,
            plan_id=analytic_plans[0],
            partner_id=partner,
            company_id=record_company,
            currency_id=cny if record_company else False,
            balance=Decimal("125.500"),
        )

    analytic_accounts = [
        analytic_account(31),
        analytic_account(32, record_company=company),
        analytic_account(33, record_company=other_company),
    ]
    analytic_lines = [
        _record(
            31,
            date="2026-08-24",
            name="Project effort",
            ref=False,
            amount=Decimal("125.500"),
            unit_amount=Decimal("2.00"),
            company_id=company,
            currency_id=cny,
            partner_id=partner,
            product_id=products[0],
            product_uom_id=uom,
            general_account_id=receivable,
            move_line_id=journal_lines[0],
            account_id=analytic_accounts[0],
            auto_account_id=analytic_accounts[0],
        ),
        _record(
            32,
            date="2026-08-25",
            name="Project materials",
            ref="ANL/32",
            amount=Decimal("75.00"),
            unit_amount=Decimal("1.00"),
            company_id=company,
            currency_id=cny,
            partner_id=False,
            product_id=False,
            product_uom_id=False,
            general_account_id=False,
            move_line_id=False,
            account_id=analytic_accounts[0],
            auto_account_id=analytic_accounts[0],
        ),
    ]
    partner_category = _record(17, name="Preferred")
    distribution_models = [
        _record(
            31,
            sequence=10,
            company_id=company,
            account_prefix="6",
            partner_id=partner,
            partner_category_id=partner_category,
            product_id=products[0],
            product_categ_id=category,
            analytic_distribution={"32,31": Decimal("100.00")},
            distribution_analytic_account_ids=Records(
                [analytic_accounts[1], analytic_accounts[0]]
            ),
        ),
        _record(
            32,
            sequence=20,
            company_id=False,
            account_prefix=False,
            partner_id=False,
            partner_category_id=False,
            product_id=False,
            product_categ_id=False,
            analytic_distribution={"31": Decimal("100.00")},
            distribution_analytic_account_ids=Records([analytic_accounts[0]]),
        ),
    ]
    applicabilities = [
        _record(
            31,
            analytic_plan_id=analytic_plans[0],
            business_domain="invoice",
            applicability="mandatory",
            company_id=company,
            account_prefix="4",
            product_categ_id=category,
        ),
        _record(
            32,
            analytic_plan_id=False,
            business_domain="general",
            applicability="optional",
            company_id=False,
            account_prefix=False,
            product_categ_id=False,
        ),
    ]
    budget_user = _record(5, name="V4 Accountant")
    budgets = [
        _record(
            31,
            name="FY2026 Operating Budget",
            date_from="2026-01-01",
            date_to="2026-12-31",
            state="confirmed",
            budget_type="both",
            company_id=company,
            user_id=budget_user,
            parent_id=False,
        ),
        _record(
            32,
            name="FY2027 Expense Budget",
            date_from="2027-01-01",
            date_to="2027-12-31",
            state="draft",
            budget_type="expense",
            company_id=company,
            user_id=False,
            parent_id=False,
        ),
    ]
    budgets[1].parent_id = budgets[0]
    budget_lines = [
        _record(
            31,
            sequence=10,
            budget_analytic_id=budgets[0],
            date_from="2026-01-01",
            date_to="2026-12-31",
            budget_amount=Decimal("100000.00"),
            achieved_amount=Decimal("25000.00"),
            achieved_percentage=Decimal("25.00"),
            theoritical_amount=Decimal("66666.670"),
            theoritical_percentage=Decimal("66.66667"),
            is_above_budget=False,
            budget_analytic_state="confirmed",
            currency_id=cny,
            company_id=company,
            account_id=analytic_accounts[0],
            auto_account_id=analytic_accounts[0],
        ),
        _record(
            32,
            sequence=20,
            budget_analytic_id=budgets[0],
            date_from="2026-01-01",
            date_to="2026-12-31",
            budget_amount=Decimal("50000.00"),
            achieved_amount=Decimal("10000.00"),
            achieved_percentage=Decimal("20.00"),
            theoritical_amount=Decimal("33333.33"),
            theoritical_percentage=Decimal("66.66666"),
            is_above_budget=False,
            budget_analytic_state="confirmed",
            currency_id=cny,
            company_id=company,
            account_id=analytic_accounts[0],
            auto_account_id=analytic_accounts[0],
        ),
    ]
    asia = _record(77, name="Asia")
    beijing = _record(91, name="Beijing")
    shanghai = _record(92, name="Shanghai")

    def fiscal_position(record_id: int, record_company: Record = company) -> Record:
        return _record(
            record_id,
            name="China Domestic",
            active=True,
            auto_apply=True,
            vat_required=False,
            country_id=china,
            country_group_id=asia,
            state_ids=Records([shanghai, beijing]),
            company_id=record_company,
            foreign_vat=False,
        )

    fiscal_positions = [
        fiscal_position(31),
        fiscal_position(32),
        fiscal_position(33, other_company),
    ]
    tags = [
        _record(
            31,
            name="Operating",
            applicability="accounts",
            active=True,
            color=3,
            country_id=china,
        ),
        _record(
            32,
            name="Shared",
            applicability="accounts",
            active=True,
            color=4,
            country_id=False,
        ),
        _record(
            33,
            name="Japan Tax",
            applicability="taxes",
            active=True,
            color=5,
            country_id=japan,
        ),
    ]
    tax_groups = [
        tax_group,
        _record(
            32,
            name="GST",
            sequence=20,
            country_id=china,
            preceding_subtotal="Untaxed Amount",
            company_id=company,
        ),
        _record(
            33,
            name="Other VAT",
            sequence=10,
            country_id=japan,
            preceding_subtotal=False,
            company_id=other_company,
        ),
    ]
    root_account_group = _record(
        40,
        name="Assets",
        code_prefix_start="1",
        code_prefix_end="1",
        parent_id=False,
        company_id=company,
    )
    account_group = _record(
        41,
        name="Current Assets",
        code_prefix_start="10",
        code_prefix_end="19",
        parent_id=root_account_group,
        company_id=company,
    )
    models = {
        "res.company": Model("res.company", [company, other_company]),
        "res.currency": Model("res.currency", [cny]),
        "account.account": Model(
            "account.account",
            [
                cash,
                receivable,
                payable,
                bank_account,
                rounding_profit,
                rounding_loss,
            ],
        ),
        "account.journal": Model(
            "account.journal", [bank_journal, misc_journal, other_journal]
        ),
        "account.tax": Model("account.tax", [tax]),
        "account.tax.group": Model("account.tax.group", tax_groups),
        "account.payment.term": Model("account.payment.term", [payment_term]),
        "account.payment.term.line": Model("account.payment.term.line", [term_line]),
        "res.partner": Model("res.partner", [partner]),
        "res.users": Model("res.users", [budget_user]),
        "res.partner.category": Model("res.partner.category", [partner_category]),
        "res.bank": Model("res.bank", [fixture_bank]),
        "res.partner.bank": Model("res.partner.bank", partner_banks),
        "account.move": Model("account.move", [move, bank_move]),
        "account.payment": Model("account.payment"),
        "account.bank.statement": Model("account.bank.statement", bank_statements),
        "account.bank.statement.line": Model(
            "account.bank.statement.line", [transaction]
        ),
        "account.move.line": Model("account.move.line", journal_lines),
        "account.partial.reconcile": Model(
            "account.partial.reconcile", partial_reconciles
        ),
        "account.full.reconcile": Model("account.full.reconcile", full_reconciles),
        "account.payment.method": Model("account.payment.method", [payment_method]),
        "account.payment.method.line": Model(
            "account.payment.method.line", payment_method_lines
        ),
        "account.reconcile.model": Model("account.reconcile.model", reconcile_models),
        "account.cash.rounding": Model("account.cash.rounding", cash_roundings),
        "account.journal.group": Model("account.journal.group", journal_groups),
        "account.incoterms": Model("account.incoterms", incoterms),
        "product.product": Model("product.product", products),
        "product.template": Model("product.template", [product_template]),
        "product.category": Model("product.category", [category]),
        "uom.uom": Model("uom.uom", [uom]),
        "account.analytic.plan": Model("account.analytic.plan", analytic_plans),
        "account.analytic.account": Model(
            "account.analytic.account", analytic_accounts
        ),
        "account.analytic.line": Model("account.analytic.line", analytic_lines),
        "account.analytic.distribution.model": Model(
            "account.analytic.distribution.model", distribution_models
        ),
        "account.analytic.applicability": Model(
            "account.analytic.applicability", applicabilities
        ),
        "budget.analytic": Model("budget.analytic", budgets),
        "budget.line": Model("budget.line", budget_lines),
        "account.fiscal.position": Model("account.fiscal.position", fiscal_positions),
        "account.account.tag": Model("account.account.tag", tags),
        "res.country": Model("res.country", [china, japan]),
        "res.country.group": Model("res.country.group", [asia]),
        "res.country.state": Model("res.country.state", [beijing, shanghai]),
        "account.group": Model("account.group", [root_account_group, account_group]),
        "account.tax.repartition.line": Model("account.tax.repartition.line"),
        "account.reconcile.model.line": Model("account.reconcile.model.line"),
        "account.report": Model("account.report"),
        "account.report.column": Model("account.report.column"),
    }
    return Env(models), {
        "company": company,
        "other_company": other_company,
        "journal_lines": journal_lines,
        "payment_method_lines": payment_method_lines,
        "reconcile_models": reconcile_models,
        "cash_roundings": cash_roundings,
        "journal_groups": journal_groups,
        "incoterms": incoterms,
        "products": products,
        "analytic_plans": analytic_plans,
        "analytic_accounts": analytic_accounts,
        "fiscal_positions": fiscal_positions,
        "tags": tags,
        "tax_groups": tax_groups,
        "partner_banks": partner_banks,
        "bank_statements": bank_statements,
        "partial_reconciles": partial_reconciles,
        "full_reconciles": full_reconciles,
        "analytic_lines": analytic_lines,
        "distribution_models": distribution_models,
        "applicabilities": applicabilities,
        "budgets": budgets,
        "budget_lines": budget_lines,
    }


def _dispatch(
    env: Env, capability_id: str, parameters: dict[str, Any]
) -> dict[str, Any]:
    return core.dispatch(
        env,
        {
            "capability_id": capability_id,
            "company_id": 7,
            "parameters": parameters,
        },
        7,
        failure_type=Failure,
    )


def _parameters(capability_id: str) -> dict[str, Any]:
    if capability_id == "partner.get":
        return {"partner_id": 31}
    if capability_id == "partner.search":
        return {
            "query": None,
            "active": None,
            "company_type": None,
            "customer": None,
            "supplier": None,
            "after_id": None,
            "limit": 1,
        }
    if capability_id == "journal.configuration.inspect":
        return {"journal_id": 9}
    if capability_id == "tax.repartition_line.get":
        return {"tax_repartition_line_id": 31}
    if capability_id == "reconciliation.model.line.get":
        return {"reconciliation_model_line_id": 31}
    if capability_id == "bank.get":
        return {"bank_id": 4}
    if capability_id == "report.catalog.get":
        return {"report_id": 31}
    if capability_id == "account.group.list":
        return {"query": None, "parent_id": None, "after_id": None, "limit": 1}
    if capability_id == "tax.repartition_line.list":
        return {
            "tax_id": None,
            "document_types": None,
            "repartition_types": None,
            "account_id": None,
            "use_in_tax_closing": None,
            "after_id": None,
            "limit": 1,
        }
    if capability_id == "reconciliation.model.line.list":
        return {
            "reconciliation_model_id": None,
            "account_id": None,
            "partner_id": None,
            "amount_types": None,
            "after_id": None,
            "limit": 1,
        }
    if capability_id == "bank.list":
        return {
            "query": None,
            "country_id": None,
            "active": None,
            "after_id": None,
            "limit": 1,
        }
    if capability_id == "report.catalog.list":
        return {
            "country_id": None,
            "root_report_id": None,
            "availability_conditions": None,
            "active": None,
            "after_id": None,
            "limit": 1,
        }
    if capability_id in GET_ID_FIELDS:
        return {GET_ID_FIELDS[capability_id]: GET_OBJECT_IDS[capability_id]}
    if capability_id == "journal_item.search":
        return {
            "date_from": None,
            "date_to": None,
            "move_id": None,
            "account_id": None,
            "partner_id": None,
            "journal_id": None,
            "posted_only": False,
            "after_id": None,
            "limit": 1,
        }
    if capability_id in REFERENCE_PAGE_DEFAULTS:
        return {
            **REFERENCE_PAGE_DEFAULTS[capability_id],
            "after_id": None,
            "limit": 1,
        }
    return {"after_id": None, "limit": 1}


def _coded(record_id: int, code: str, name: str) -> dict[str, Any]:
    return {"id": record_id, "code": code, "name": name}


def _expected_item(capability_id: str, record_id: int = 31) -> dict[str, Any]:
    if capability_id == "account.account.get":
        return {
            "id": record_id,
            "code": "1000",
            "name": "Cash",
            "account_type": "asset_cash",
            "active": True,
            "reconcile": False,
            "company_ids": [7],
        }
    if capability_id == "journal.get":
        return {
            "id": record_id,
            "sequence": 10,
            "code": "BNK1",
            "name": "Bank",
            "type": "bank",
            "active": True,
            "currency": None,
            "company_id": 7,
        }
    if capability_id == "tax.get":
        return {
            "id": record_id,
            "sequence": 1,
            "name": "VAT 13%",
            "type_tax_use": "sale",
            "amount_type": "percent",
            "amount": "13",
            "price_include": False,
            "include_base_amount": False,
            "is_base_affected": True,
            "active": True,
            "tax_group": {"id": 5, "name": "VAT"},
            "company_id": 7,
        }
    if capability_id == "payment_term.get":
        return {
            "id": record_id,
            "sequence": 10,
            "name": "30 Days",
            "active": True,
            "company_id": None,
            "display_on_invoice": True,
            "early_discount": False,
            "discount_percentage": "0",
            "discount_days": 0,
            "early_pay_discount_computation": "included",
            "lines": [
                {
                    "id": 301,
                    "value": "percent",
                    "value_amount": "100",
                    "delay_type": "days_after",
                    "nb_days": 30,
                    "days_next_month": "10",
                }
            ],
        }
    if capability_id == "currency.get":
        return {
            "id": 6,
            "code": "CNY",
            "name": "Chinese Yuan",
            "symbol": "¥",
            "rounding": "0.01",
            "decimal_places": 2,
            "active": True,
            "position": "before",
            "is_company_currency": True,
        }
    if capability_id == "partner.accounting.get":
        return {
            "id": record_id,
            "complete_name": "Fixture Partner",
            "ref": "PARTNER-31",
            "active": True,
            "is_company": True,
            "company_id": None,
            "customer_rank": 1,
            "supplier_rank": 0,
            "receivable_account": _coded(121, "112200", "Accounts Receivable"),
            "payable_account": _coded(221, "220200", "Accounts Payable"),
        }
    if capability_id == "bank.transaction.get":
        return {
            "id": record_id,
            "company_id": 7,
            "date": "2026-08-24",
            "payment_date": None,
            "name": "Customer transfer",
            "reference": "BANK/31",
            "partner": {"id": 31, "name": "Fixture Partner"},
            "journal": _coded(9, "BNK1", "Bank"),
            "amount": "125.5",
            "currency": {"id": 6, "code": "CNY"},
            "move": {"id": 302, "name": "BNK1/2026/0031", "state": "posted"},
            "reconciled": False,
        }
    if capability_id in {"journal_item.get", "journal_item.search"}:
        return {
            "id": record_id,
            "company_id": 7,
            "date": "2026-08-24",
            "date_maturity": None,
            "move": {
                "id": 301,
                "name": "MISC/2026/0031",
                "state": "posted",
                "move_type": "entry",
            },
            "account": _coded(121, "112200", "Accounts Receivable"),
            "partner": {"id": 31, "name": "Fixture Partner"},
            "journal": _coded(4, "MISC", "Miscellaneous Operations"),
            "name": "Fixture journal item",
            "reference": None,
            "debit": "125.5",
            "credit": "0",
            "balance": "125.5",
            "amount_currency": "125.5",
            "currency": {"id": 6, "code": "CNY"},
            "reconciled": False,
            "matching_number": "31",
            "analytic_distribution": {},
            "tax_line_id": None,
            "tax_ids": [],
            "tax_base_amount": "0",
        }
    if capability_id in {"product.search", "product.get"}:
        return {
            "id": record_id,
            "name": "Consulting Service",
            "default_code": f"CONSULT-{record_id}",
            "active": True,
            "product_type": "service",
            "is_storable": False,
            "template": {"id": 401, "name": "Consulting Template"},
            "category": None if record_id == 31 else {"id": 51, "name": "Services"},
            "uom": {"id": 1, "name": "Units"},
            "company_id": None,
            "currency": {"id": 6, "code": "CNY"},
            "standard_price": "100",
            "list_price": "500",
        }
    if capability_id in {"analytic.plan.list", "analytic.plan.get"}:
        return {
            "id": record_id,
            "name": "Projects",
            "complete_name": "Management / Projects",
            "parent": {"id": 32, "name": "Management"},
            "color": 4,
        }
    if capability_id in {"analytic.account.search", "analytic.account.get"}:
        return {
            "id": record_id,
            "name": "Project Alpha",
            "code": f"ALPHA-{record_id}",
            "active": True,
            "plan": {"id": 31, "name": "Projects"},
            "partner": {"id": 31, "name": "Fixture Partner"},
            "company_id": None if record_id == 31 else 7,
            "currency": {"id": 6, "code": "CNY"},
            "balance": "125.5",
        }
    if capability_id in {"fiscal_position.search", "fiscal_position.get"}:
        return {
            "id": record_id,
            "name": "China Domestic",
            "active": True,
            "auto_apply": True,
            "vat_required": False,
            "country": {"id": 156, "name": "China"},
            "country_group": {"id": 77, "name": "Asia"},
            "states": [
                {"id": 91, "name": "Beijing"},
                {"id": 92, "name": "Shanghai"},
            ],
            "company_id": 7,
            "foreign_vat": None,
        }
    if capability_id in {"account.tag.list", "account.tag.get"}:
        return {
            "id": record_id,
            "name": "Operating" if record_id == 31 else "Shared",
            "applicability": "accounts",
            "active": True,
            "color": 3 if record_id == 31 else 4,
            "country": {"id": 156, "name": "China"} if record_id == 31 else None,
        }
    if capability_id in {"tax.group.list", "tax.group.get"}:
        return {
            "id": record_id,
            "name": "VAT" if record_id == 5 else "GST",
            "sequence": 10 if record_id == 5 else 20,
            "country": {"id": 156, "name": "China"},
            "preceding_subtotal": None if record_id == 5 else "Untaxed Amount",
            "company_id": 7,
        }
    if capability_id in {"payment.method.list", "payment.method.get"}:
        return {
            "id": record_id,
            "name": "Manual",
            "payment_type": "inbound",
            "sequence": 10,
            "company_id": 7,
            "payment_method": {"id": 2, "code": "manual", "name": "Manual"},
            "journal": _coded(9, "BNK1", "Bank"),
            "payment_account": _coded(101, "100200", "Bank Account"),
        }
    if capability_id in {
        "reconciliation.model.list",
        "reconciliation.model.get",
    }:
        return {
            "id": record_id,
            "name": "Bank fees",
            "sequence": 10,
            "active": True,
            "company_id": 7,
            "match_amount": "lower",
            "match_amount_min": "0",
            "match_amount_max": "1000",
            "match_label": "contains",
            "match_label_param": "fee",
        }
    if capability_id in {"cash_rounding.list", "cash_rounding.get"}:
        if record_id == 32:
            return {
                "id": 32,
                "name": "Round on largest tax",
                "rounding": "1",
                "strategy": "biggest_tax",
                "rounding_method": "UP",
                "profit_account": None,
                "loss_account": None,
            }
        return {
            "id": record_id,
            "name": "Cash rounding 0.05",
            "rounding": "0.05",
            "strategy": "add_invoice_line",
            "rounding_method": "HALF-UP",
            "profit_account": _coded(701, "759000", "Cash Rounding Profit"),
            "loss_account": _coded(702, "659000", "Cash Rounding Loss"),
        }
    if capability_id in {"journal.group.list", "journal.group.get"}:
        if record_id == 32:
            return {
                "id": 32,
                "name": "Company Journals",
                "sequence": 20,
                "company_id": 7,
                "excluded_journals": [],
            }
        return {
            "id": record_id,
            "name": "Liquidity Journals",
            "sequence": 10,
            "company_id": None,
            "excluded_journals": [
                _coded(4, "MISC", "Miscellaneous Operations"),
                _coded(9, "BNK1", "Bank"),
            ],
        }
    if capability_id in {"incoterm.list", "incoterm.get"}:
        return {
            "id": record_id,
            "code": "FOB" if record_id == 31 else "CIF",
            "name": "Free On Board"
            if record_id == 31
            else "Cost, Insurance and Freight",
            "active": record_id == 31,
        }
    if capability_id in {
        "partner.bank_account.search",
        "partner.bank_account.get",
    }:
        if record_id == 32:
            return {
                "id": 32,
                "acc_number": "SHARED-32",
                "account_holder_name": "Fixture Holder",
                "account_type": "bank",
                "active": False,
                "sequence": 20,
                "account_holder": {"id": 31, "name": "Fixture Partner"},
                "allow_out_payment": False,
                "bank": None,
                "currency": None,
                "company_id": None,
                "linked_journal": None,
            }
        return {
            "id": record_id,
            "acc_number": "CN621234",
            "account_holder_name": None,
            "account_type": "bank",
            "active": True,
            "sequence": 10,
            "account_holder": {"id": 31, "name": "Fixture Partner"},
            "allow_out_payment": True,
            "bank": {"id": 18, "name": "Fixture Bank", "bic": None},
            "currency": {"id": 6, "code": "CNY"},
            "company_id": 7,
            "linked_journal": _coded(9, "BNK1", "Bank"),
        }
    if capability_id in {"bank.statement.search", "bank.statement.get"}:
        if record_id == 32:
            return {
                "id": 32,
                "name": "BNK1/2026/09",
                "reference": "September opening",
                "date": None,
                "company_id": 7,
                "journal": _coded(9, "BNK1", "Bank"),
                "currency": {"id": 6, "code": "CNY"},
                "balance_start": "225.5",
                "balance_end": "225.5",
                "balance_end_real": "225.5",
                "is_complete": False,
                "is_valid": False,
                "problem_description": "Missing closing balance",
                "transaction_count": 0,
            }
        return {
            "id": record_id,
            "name": "BNK1/2026/08",
            "reference": None,
            "date": "2026-08-24",
            "company_id": 7,
            "journal": _coded(9, "BNK1", "Bank"),
            "currency": {"id": 6, "code": "CNY"},
            "balance_start": "100",
            "balance_end": "225.5",
            "balance_end_real": "225.5",
            "is_complete": True,
            "is_valid": True,
            "problem_description": None,
            "transaction_count": 1,
        }
    if capability_id in {
        "reconciliation.partial.list",
        "reconciliation.partial.get",
    }:
        return {
            "id": record_id,
            "company_id": 7,
            "max_date": "2026-08-24" if record_id == 31 else "2026-08-25",
            "amount": "125.5" if record_id == 31 else "25",
            "company_currency": {"id": 6, "code": "CNY"},
            "debit_amount_currency": "125.5" if record_id == 31 else "25",
            "debit_currency": {"id": 6, "code": "CNY"},
            "credit_amount_currency": "-125.5" if record_id == 31 else "-25",
            "credit_currency": {"id": 6, "code": "CNY"},
            "debit_journal_item_id": 31,
            "credit_journal_item_id": 32,
            "full_reconcile_id": 31,
            "exchange_move_id": None if record_id == 31 else 302,
            "matching_number": "31",
        }
    if capability_id in {
        "reconciliation.full.list",
        "reconciliation.full.get",
    }:
        return {
            "id": record_id,
            "company_id": 7,
            "matching_number": str(record_id),
            "partial_reconcile_ids": [31, 32],
            "reconciled_journal_item_ids": [31, 32],
        }
    if capability_id in {"analytic.line.search", "analytic.line.get"}:
        if record_id == 32:
            return {
                "id": 32,
                "date": "2026-08-25",
                "name": "Project materials",
                "reference": "ANL/32",
                "amount": "75",
                "unit_amount": "1",
                "company_id": 7,
                "currency": {"id": 6, "code": "CNY"},
                "analytic_accounts": [{"id": 31, "name": "Project Alpha"}],
                "partner": None,
                "product": None,
                "uom": None,
                "general_account": None,
                "journal_item_id": None,
            }
        return {
            "id": record_id,
            "date": "2026-08-24",
            "name": "Project effort",
            "reference": None,
            "amount": "125.5",
            "unit_amount": "2",
            "company_id": 7,
            "currency": {"id": 6, "code": "CNY"},
            "analytic_accounts": [{"id": 31, "name": "Project Alpha"}],
            "partner": {"id": 31, "name": "Fixture Partner"},
            "product": {"id": 31, "name": "Consulting Service"},
            "uom": {"id": 1, "name": "Units"},
            "general_account": _coded(121, "112200", "Accounts Receivable"),
            "journal_item_id": 31,
        }
    if capability_id in {
        "analytic.distribution_model.list",
        "analytic.distribution_model.get",
    }:
        if record_id == 32:
            return {
                "id": 32,
                "sequence": 20,
                "company_id": None,
                "account_prefix": None,
                "partner": None,
                "partner_category": None,
                "product": None,
                "product_category": None,
                "allocations": [
                    {
                        "analytic_accounts": [{"id": 31, "name": "Project Alpha"}],
                        "percentage": "100",
                    }
                ],
            }
        return {
            "id": record_id,
            "sequence": 10,
            "company_id": 7,
            "account_prefix": "6",
            "partner": {"id": 31, "name": "Fixture Partner"},
            "partner_category": {"id": 17, "name": "Preferred"},
            "product": {"id": 31, "name": "Consulting Service"},
            "product_category": {"id": 51, "name": "Services"},
            "allocations": [
                {
                    "analytic_accounts": [
                        {"id": 31, "name": "Project Alpha"},
                        {"id": 32, "name": "Project Alpha"},
                    ],
                    "percentage": "100",
                }
            ],
        }
    if capability_id in {
        "analytic.applicability.list",
        "analytic.applicability.get",
    }:
        if record_id == 32:
            return {
                "id": 32,
                "plan": None,
                "business_domain": "general",
                "applicability": "optional",
                "company_id": None,
                "account_prefix": None,
                "product_category": None,
            }
        return {
            "id": record_id,
            "plan": {"id": 31, "name": "Projects"},
            "business_domain": "invoice",
            "applicability": "mandatory",
            "company_id": 7,
            "account_prefix": "4",
            "product_category": {"id": 51, "name": "Services"},
        }
    if capability_id in {"budget.search", "budget.get"}:
        if record_id == 32:
            return {
                "id": 32,
                "name": "FY2027 Expense Budget",
                "date_from": "2027-01-01",
                "date_to": "2027-12-31",
                "state": "draft",
                "budget_type": "expense",
                "company_id": 7,
                "responsible": None,
                "revision_of": {
                    "id": 31,
                    "name": "FY2026 Operating Budget",
                },
            }
        return {
            "id": record_id,
            "name": "FY2026 Operating Budget",
            "date_from": "2026-01-01",
            "date_to": "2026-12-31",
            "state": "confirmed",
            "budget_type": "both",
            "company_id": 7,
            "responsible": {"id": 5, "name": "V4 Accountant"},
            "revision_of": None,
        }
    if capability_id in {"budget.line.list", "budget.line.get"}:
        return {
            "id": record_id,
            "sequence": 10 if record_id == 31 else 20,
            "budget": {"id": 31, "name": "FY2026 Operating Budget"},
            "date_from": "2026-01-01",
            "date_to": "2026-12-31",
            "budget_amount": "100000" if record_id == 31 else "50000",
            "achieved_amount": "25000" if record_id == 31 else "10000",
            "achieved_percentage": "25" if record_id == 31 else "20",
            "theoretical_amount": "66666.67" if record_id == 31 else "33333.33",
            "theoretical_percentage": "66.66667" if record_id == 31 else "66.66666",
            "above_budget": False,
            "state": "confirmed",
            "currency": {"id": 6, "code": "CNY"},
            "company_id": 7,
            "analytic_accounts": [{"id": 31, "name": "Project Alpha"}],
        }
    if capability_id == "account.group.get":
        return {
            "id": record_id,
            "name": "Current Assets",
            "code_prefix_start": "10",
            "code_prefix_end": "19",
            "parent": {"id": 40, "name": "Assets"},
            "company_id": 7,
        }
    raise AssertionError(capability_id)


def _search_call(model: Model) -> tuple[Any, ...]:
    return next(call for call in reversed(model.calls) if call[0] == "search_read")


def test_runtime_exports_only_the_fixed_core_object_action_and_capabilities() -> None:
    assert core.ACTION == "accounting.core_object.read"
    assert core.CAPABILITY_IDS == (
        EXPECTED_CAPABILITY_IDS
        | FISCAL_POSITION_MAPPING_CAPABILITY_IDS
        | ACCOUNTING_INSIGHT_CAPABILITY_IDS
        | SUPPORTING_OBJECT_CAPABILITY_IDS
    )


@pytest.mark.parametrize(("capability_id", "id_field"), GET_ID_FIELDS.items())
def test_each_get_returns_one_exact_normalized_item(
    capability_id: str, id_field: str
) -> None:
    env, _ = _fixture()
    object_id = GET_OBJECT_IDS[capability_id]

    page = _dispatch(env, capability_id, {id_field: object_id})

    assert page == {
        "user_id": 5,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "cursor_found": True,
        "items": [_expected_item(capability_id, object_id)],
    }


@pytest.mark.parametrize(
    "capability_id", ["payment.method.list", "reconciliation.model.list"]
)
def test_support_lists_are_company_scoped_id_ascending_and_limited(
    capability_id: str,
) -> None:
    env, _ = _fixture()

    page = _dispatch(env, capability_id, {"after_id": None, "limit": 1})

    assert page["items"] == [_expected_item(capability_id)]
    call = _search_call(env.models[PRIMARY_MODELS[capability_id]])
    assert ("company_id", "=", 7) in call[1]
    assert call[2:4] == ("id", 1)


@pytest.mark.parametrize(
    ("get_capability", "list_capability", "id_field"),
    [
        ("payment.method.get", "payment.method.list", "payment_method_line_id"),
        (
            "reconciliation.model.get",
            "reconciliation.model.list",
            "reconciliation_model_id",
        ),
    ],
)
def test_support_gets_reuse_the_existing_list_item_normalizer(
    get_capability: str, list_capability: str, id_field: str
) -> None:
    env, _ = _fixture()

    get_page = _dispatch(env, get_capability, {id_field: 31})
    list_page = _dispatch(env, list_capability, {"after_id": None, "limit": 1})

    assert get_page["items"] == list_page["items"] == [_expected_item(list_capability)]


@pytest.mark.parametrize("capability_id", REFERENCE_PAGE_CAPABILITIES)
def test_reference_pages_are_normalized_id_ascending_and_limited(
    capability_id: str,
) -> None:
    env, _ = _fixture()
    parameters = {
        **REFERENCE_PAGE_DEFAULTS[capability_id],
        "after_id": None,
        "limit": 1,
    }

    page = _dispatch(env, capability_id, parameters)

    first_id = 5 if capability_id == "tax.group.list" else 31
    assert page["items"] == [_expected_item(capability_id, first_id)]
    call = _search_call(env.models[PRIMARY_MODELS[capability_id]])
    assert call[2:4] == ("id", 1)


@pytest.mark.parametrize(
    ("capability_id", "parameters", "domain_terms"),
    [
        (
            "product.search",
            {
                "query": "CONSULT",
                "active": True,
                "after_id": None,
                "limit": 2,
            },
            {
                ("name", "ilike", "CONSULT"),
                ("default_code", "ilike", "CONSULT"),
                ("barcode", "ilike", "CONSULT"),
                ("active", "=", True),
            },
        ),
        (
            "analytic.account.search",
            {
                "query": "ALPHA",
                "active": True,
                "plan_id": 31,
                "after_id": None,
                "limit": 2,
            },
            {
                ("name", "ilike", "ALPHA"),
                ("code", "ilike", "ALPHA"),
                ("active", "=", True),
                ("plan_id", "=", 31),
            },
        ),
        (
            "fiscal_position.search",
            {
                "query": "China",
                "active": True,
                "auto_apply": True,
                "after_id": None,
                "limit": 2,
            },
            {
                ("name", "ilike", "China"),
                ("active", "=", True),
                ("auto_apply", "=", True),
            },
        ),
        (
            "partner.bank_account.search",
            {
                "partner_id": 31,
                "active": True,
                "after_id": None,
                "limit": 2,
            },
            {
                ("partner_id", "=", 31),
                ("active", "=", True),
            },
        ),
        (
            "bank.statement.search",
            {
                "journal_id": 9,
                "date_from": "2026-08-01",
                "date_to": "2026-08-31",
                "after_id": None,
                "limit": 2,
            },
            {
                ("journal_id", "=", 9),
                ("date", ">=", "2026-08-01"),
                ("date", "<=", "2026-08-31"),
            },
        ),
        (
            "analytic.line.search",
            {
                "query": "Project",
                "date_from": "2026-08-01",
                "date_to": "2026-08-31",
                "analytic_account_id": 31,
                "after_id": None,
                "limit": 2,
            },
            {
                ("name", "ilike", "Project"),
                ("ref", "ilike", "Project"),
                ("date", ">=", "2026-08-01"),
                ("date", "<=", "2026-08-31"),
                ("auto_account_id", "=", 31),
            },
        ),
        (
            "budget.search",
            {
                "query": "FY2026",
                "state": "confirmed",
                "budget_type": "both",
                "date_from": "2026-04-01",
                "date_to": "2026-06-30",
                "after_id": None,
                "limit": 2,
            },
            {
                ("name", "ilike", "FY2026"),
                ("state", "=", "confirmed"),
                ("budget_type", "=", "both"),
                ("date_to", ">=", "2026-04-01"),
                ("date_from", "<=", "2026-06-30"),
            },
        ),
        (
            "budget.line.list",
            {
                "budget_id": 31,
                "plan_id": 31,
                "analytic_account_id": 31,
                "after_id": None,
                "limit": 2,
            },
            {
                ("budget_analytic_id", "=", 31),
                ("auto_account_id", "=", 31),
            },
        ),
    ],
)
def test_reference_searches_apply_every_fixed_filter(
    capability_id: str,
    parameters: dict[str, Any],
    domain_terms: set[tuple[Any, Any, Any]],
) -> None:
    env, _ = _fixture()

    page = _dispatch(env, capability_id, parameters)

    assert page["items"]
    call = _search_call(env.models[PRIMARY_MODELS[capability_id]])
    assert domain_terms <= {term for term in call[1] if isinstance(term, tuple)}


def test_budget_line_optional_account_filter_is_semantically_validated() -> None:
    env, _ = _fixture()

    valid = _dispatch(
        env,
        "budget.line.list",
        {
            "budget_id": 31,
            "plan_id": 31,
            "analytic_account_id": 31,
            "after_id": None,
            "limit": 2,
        },
    )
    invalid = _dispatch(
        env,
        "budget.line.list",
        {
            "budget_id": 31,
            "plan_id": 999,
            "analytic_account_id": 31,
            "after_id": None,
            "limit": 2,
        },
    )

    assert [item["id"] for item in valid["items"]] == [31, 32]
    assert invalid["cursor_found"] is True
    assert invalid["items"] == []


def test_company_shared_and_global_get_domains_are_distinct() -> None:
    env, _ = _fixture()

    account = _dispatch(env, "account.account.get", {"account_id": 31})
    account_domain = _search_call(env.models["account.account"])[1]
    partner = _dispatch(env, "partner.accounting.get", {"partner_id": 31})
    partner_domain = _search_call(env.models["res.partner"])[1]
    term = _dispatch(env, "payment_term.get", {"payment_term_id": 31})
    term_domain = _search_call(env.models["account.payment.term"])[1]
    currency = _dispatch(env, "currency.get", {"currency_id": 6})
    currency_domain = _search_call(env.models["res.currency"])[1]

    assert account["items"] and partner["items"] and term["items"] and currency["items"]
    assert any(
        term[0] == "company_ids" for term in account_domain if isinstance(term, tuple)
    )
    assert any(
        term[0] == "company_id" for term in partner_domain if isinstance(term, tuple)
    )
    assert any(
        term[0] == "company_id" for term in term_domain if isinstance(term, tuple)
    )
    assert all(
        term[0] != "company_id" for term in currency_domain if isinstance(term, tuple)
    )


def test_reference_scopes_follow_company_localization_and_global_rules() -> None:
    env, _ = _fixture()

    _dispatch(env, "product.get", {"product_id": 31})
    product_domain = _search_call(env.models["product.product"])[1]
    _dispatch(env, "analytic.account.get", {"analytic_account_id": 31})
    analytic_domain = _search_call(env.models["account.analytic.account"])[1]
    _dispatch(env, "fiscal_position.get", {"fiscal_position_id": 31})
    fiscal_domain = _search_call(env.models["account.fiscal.position"])[1]
    _dispatch(env, "analytic.plan.get", {"plan_id": 31})
    plan_domain = _search_call(env.models["account.analytic.plan"])[1]
    _dispatch(env, "account.tag.get", {"tag_id": 31})
    tag_domain = _search_call(env.models["account.account.tag"])[1]
    _dispatch(env, "tax.group.get", {"tax_group_id": 5})
    tax_group_domain = _search_call(env.models["account.tax.group"])[1]
    _dispatch(env, "journal.group.get", {"journal_group_id": 31})
    journal_group_domain = _search_call(env.models["account.journal.group"])[1]
    _dispatch(env, "cash_rounding.get", {"cash_rounding_id": 31})
    cash_rounding_domain = _search_call(env.models["account.cash.rounding"])[1]
    _dispatch(env, "incoterm.get", {"incoterm_id": 31})
    incoterm_domain = _search_call(env.models["account.incoterms"])[1]

    for domain in (product_domain, analytic_domain):
        assert ("company_id", "=", False) in domain
        assert ("company_id", "=", 7) in domain
    assert ("company_id", "=", 7) in fiscal_domain
    assert all(
        term[0] != "company_id" for term in plan_domain if isinstance(term, tuple)
    )
    assert ("country_id", "=", False) in tag_domain
    assert ("country_id", "=", 156) in tag_domain
    assert ("company_id", "=", 7) in tax_group_domain
    assert ("company_id", "=", False) in journal_group_domain
    assert ("company_id", "=", 7) in journal_group_domain
    for domain in (cash_rounding_domain, incoterm_domain):
        assert all(
            term[0] != "company_id" for term in domain if isinstance(term, tuple)
        )
    assert ("with_company", 7) in env.models["account.cash.rounding"].calls


def test_bank_and_reconciliation_scopes_use_the_frozen_company_domains() -> None:
    env, _ = _fixture()

    _dispatch(env, "partner.bank_account.get", {"partner_bank_id": 31})
    partner_bank_domain = _search_call(env.models["res.partner.bank"])[1]
    _dispatch(env, "bank.statement.get", {"bank_statement_id": 31})
    statement_domain = _search_call(env.models["account.bank.statement"])[1]
    _dispatch(env, "reconciliation.partial.get", {"partial_reconcile_id": 31})
    partial_domain = _search_call(env.models["account.partial.reconcile"])[1]
    _dispatch(env, "reconciliation.full.get", {"full_reconcile_id": 31})
    full_domain = _search_call(env.models["account.full.reconcile"])[1]

    assert ("company_id", "=", False) in partner_bank_domain
    assert ("company_id", "=", 7) in partner_bank_domain
    assert ("company_id", "=", 7) in statement_domain
    assert ("company_id", "=", 7) in partial_domain
    assert ("reconciled_line_ids.company_id", "=", 7) in full_domain


def test_analytic_and_budget_scopes_use_the_frozen_company_domains() -> None:
    env, _ = _fixture()

    _dispatch(env, "analytic.line.get", {"analytic_line_id": 31})
    line_domain = _search_call(env.models["account.analytic.line"])[1]
    _dispatch(
        env,
        "analytic.distribution_model.get",
        {"distribution_model_id": 31},
    )
    distribution_domain = _search_call(
        env.models["account.analytic.distribution.model"]
    )[1]
    _dispatch(env, "budget.get", {"budget_id": 31})
    budget_domain = _search_call(env.models["budget.analytic"])[1]
    _dispatch(env, "budget.line.get", {"budget_line_id": 31})
    budget_line_domain = _search_call(env.models["budget.line"])[1]

    assert ("company_id", "=", 7) in line_domain
    for domain in (distribution_domain, budget_domain):
        assert ("company_id", "=", False) in domain
        assert ("company_id", "=", 7) in domain
    assert ("company_id", "=", False) in budget_line_domain
    assert ("company_id", "=", 7) in budget_line_domain
    assert ("budget_analytic_id.company_id", "=", False) in budget_line_domain
    assert ("budget_analytic_id.company_id", "=", 7) in budget_line_domain


def test_new_reference_normalizers_preserve_null_relations() -> None:
    env, _ = _fixture()

    cash_rounding = _dispatch(env, "cash_rounding.get", {"cash_rounding_id": 32})
    journal_group = _dispatch(env, "journal.group.get", {"journal_group_id": 32})
    partner_bank = _dispatch(env, "partner.bank_account.get", {"partner_bank_id": 32})
    statement = _dispatch(env, "bank.statement.get", {"bank_statement_id": 32})
    partial = _dispatch(env, "reconciliation.partial.get", {"partial_reconcile_id": 31})

    assert cash_rounding["items"] == [_expected_item("cash_rounding.get", 32)]
    assert journal_group["items"] == [_expected_item("journal.group.get", 32)]
    assert partner_bank["items"] == [_expected_item("partner.bank_account.get", 32)]
    assert statement["items"] == [_expected_item("bank.statement.get", 32)]
    assert partial["items"][0]["exchange_move_id"] is None


def test_analytic_and_budget_normalizers_preserve_null_relations() -> None:
    env, _ = _fixture()

    line = _dispatch(env, "analytic.line.get", {"analytic_line_id": 32})
    distribution = _dispatch(
        env,
        "analytic.distribution_model.get",
        {"distribution_model_id": 32},
    )
    applicability = _dispatch(
        env,
        "analytic.applicability.get",
        {"applicability_id": 32},
    )
    budget = _dispatch(env, "budget.get", {"budget_id": 32})

    assert line["items"] == [_expected_item("analytic.line.get", 32)]
    assert distribution["items"] == [
        _expected_item("analytic.distribution_model.get", 32)
    ]
    assert applicability["items"] == [_expected_item("analytic.applicability.get", 32)]
    assert budget["items"] == [_expected_item("budget.get", 32)]


def test_new_company_relations_are_revalidated_after_primary_reads() -> None:
    env, fixture = _fixture()
    profit_account = next(
        row for row in env.models["account.account"].rows if row.id == 701
    )
    profit_account.company_ids = Records([fixture["other_company"]])

    with pytest.raises(Failure) as cash_failure:
        _dispatch(env, "cash_rounding.get", {"cash_rounding_id": 31})

    assert cash_failure.value.code == "odoo_runtime_error"

    env, fixture = _fixture()
    bank_journal = next(
        row for row in env.models["account.journal"].rows if row.id == 9
    )
    bank_journal.company_id = fixture["other_company"]

    with pytest.raises(Failure) as group_failure:
        _dispatch(env, "journal.group.get", {"journal_group_id": 31})

    assert group_failure.value.code == "odoo_runtime_error"


@pytest.mark.parametrize(
    ("capability_id", "parameters", "mutate"),
    [
        (
            "analytic.line.get",
            {"analytic_line_id": 31},
            lambda env, fixture: setattr(
                fixture["analytic_accounts"][0],
                "company_id",
                fixture["other_company"],
            ),
        ),
        (
            "analytic.distribution_model.get",
            {"distribution_model_id": 32},
            lambda env, fixture: setattr(
                fixture["analytic_accounts"][0], "company_id", fixture["company"]
            ),
        ),
        (
            "budget.line.get",
            {"budget_line_id": 31},
            lambda env, fixture: setattr(
                fixture["analytic_accounts"][0],
                "company_id",
                fixture["other_company"],
            ),
        ),
    ],
)
def test_analytic_account_relations_fail_closed_across_companies(
    capability_id: str, parameters: dict[str, Any], mutate
) -> None:
    env, fixture = _fixture()
    mutate(env, fixture)

    with pytest.raises(Failure) as caught:
        _dispatch(env, capability_id, parameters)

    assert caught.value.code == "odoo_runtime_error"


def test_distribution_json_and_computed_relation_must_agree() -> None:
    env, fixture = _fixture()
    fixture["distribution_models"][0].distribution_analytic_account_ids = Records()

    with pytest.raises(Failure) as caught:
        _dispatch(
            env,
            "analytic.distribution_model.get",
            {"distribution_model_id": 31},
        )

    assert caught.value.code == "odoo_runtime_error"


def test_empty_distribution_model_is_supported() -> None:
    env, fixture = _fixture()
    model = fixture["distribution_models"][0]
    model.analytic_distribution = {}
    model.distribution_analytic_account_ids = Records()

    page = _dispatch(
        env,
        "analytic.distribution_model.get",
        {"distribution_model_id": 31},
    )

    assert page["items"][0]["allocations"] == []


@pytest.mark.parametrize(
    ("capability_id", "field"),
    [
        ("analytic.line.get", "amount"),
        ("budget.line.get", "theoritical_amount"),
    ],
)
def test_computed_numbers_must_be_finite(capability_id: str, field: str) -> None:
    env, fixture = _fixture()
    target = (
        fixture["analytic_lines"][0]
        if capability_id == "analytic.line.get"
        else fixture["budget_lines"][0]
    )
    setattr(target, field, Decimal("NaN"))

    with pytest.raises(Failure) as caught:
        _dispatch(env, capability_id, _parameters(capability_id))

    assert caught.value.code == "odoo_runtime_error"


@pytest.mark.parametrize(
    ("capability_id", "mutate"),
    [
        (
            "partner.bank_account.get",
            lambda env, fixture: setattr(
                next(row for row in env.models["account.journal"].rows if row.id == 9),
                "company_id",
                fixture["other_company"],
            ),
        ),
        (
            "bank.statement.get",
            lambda env, fixture: setattr(
                env.models["account.bank.statement.line"].rows[0],
                "company_id",
                fixture["other_company"],
            ),
        ),
        (
            "reconciliation.partial.get",
            lambda env, fixture: setattr(
                fixture["journal_lines"][0],
                "company_id",
                fixture["other_company"],
            ),
        ),
        (
            "reconciliation.full.get",
            lambda env, fixture: setattr(
                fixture["partial_reconciles"][0],
                "company_id",
                fixture["other_company"],
            ),
        ),
    ],
)
def test_bank_and_reconciliation_relations_are_revalidated(
    capability_id: str, mutate
) -> None:
    env, fixture = _fixture()
    mutate(env, fixture)

    with pytest.raises(Failure) as caught:
        _dispatch(env, capability_id, _parameters(capability_id))

    assert caught.value.code == "odoo_runtime_error"


def test_partial_and_full_reconciliation_matching_numbers_are_cross_checked() -> None:
    env, fixture = _fixture()
    fixture["journal_lines"][1].matching_number = "P"

    with pytest.raises(Failure) as partial_failure:
        _dispatch(
            env,
            "reconciliation.partial.get",
            {"partial_reconcile_id": 31},
        )
    assert partial_failure.value.code == "odoo_runtime_error"

    env, fixture = _fixture()
    fixture["journal_lines"][1].matching_number = "P"
    with pytest.raises(Failure) as full_failure:
        _dispatch(env, "reconciliation.full.get", {"full_reconcile_id": 31})
    assert full_failure.value.code == "odoo_runtime_error"


def test_partial_reconcile_preserves_a_null_full_reconcile_relation() -> None:
    env, fixture = _fixture()
    fixture["partial_reconciles"][0].full_reconcile_id = False

    page = _dispatch(
        env,
        "reconciliation.partial.get",
        {"partial_reconcile_id": 31},
    )

    assert page["items"][0]["full_reconcile_id"] is None
    assert page["items"][0]["matching_number"] == "31"


def test_full_reconcile_requires_nonempty_relations_and_sorts_ids() -> None:
    env, fixture = _fixture()
    full = fixture["full_reconciles"][0]
    full.partial_reconcile_ids = Records(list(reversed(full.partial_reconcile_ids)))
    full.reconciled_line_ids = Records(list(reversed(full.reconciled_line_ids)))

    page = _dispatch(env, "reconciliation.full.get", {"full_reconcile_id": 31})

    assert page["items"] == [_expected_item("reconciliation.full.get")]

    env, fixture = _fixture()
    fixture["full_reconciles"][0].partial_reconcile_ids = Records()
    with pytest.raises(Failure) as empty:
        _dispatch(env, "reconciliation.full.get", {"full_reconcile_id": 31})
    assert empty.value.code == "odoo_runtime_error"


def test_get_returns_empty_for_missing_and_cross_company_records() -> None:
    env, _ = _fixture()

    missing = _dispatch(env, "journal.get", {"journal_id": 999})
    cross_company = _dispatch(env, "journal.get", {"journal_id": 19})

    assert missing["items"] == []
    assert cross_company["items"] == []


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    [
        ("product.get", {"product_id": 33}),
        ("analytic.account.get", {"analytic_account_id": 33}),
        ("fiscal_position.get", {"fiscal_position_id": 33}),
        ("account.tag.get", {"tag_id": 33}),
        ("tax.group.get", {"tax_group_id": 33}),
        ("journal.group.get", {"journal_group_id": 33}),
    ],
)
def test_reference_gets_hide_cross_company_or_cross_localization_records(
    capability_id: str, parameters: dict[str, Any]
) -> None:
    env, _ = _fixture()

    page = _dispatch(env, capability_id, parameters)

    assert page["items"] == []


@pytest.mark.parametrize(
    ("capability_id", "fixture_key", "parameters"),
    [
        ("analytic.line.get", "analytic_lines", {"analytic_line_id": 31}),
        (
            "analytic.distribution_model.get",
            "distribution_models",
            {"distribution_model_id": 31},
        ),
        (
            "analytic.applicability.get",
            "applicabilities",
            {"applicability_id": 31},
        ),
        ("budget.get", "budgets", {"budget_id": 31}),
        ("budget.line.get", "budget_lines", {"budget_line_id": 31}),
    ],
)
def test_analytic_and_budget_gets_hide_cross_company_records(
    capability_id: str,
    fixture_key: str,
    parameters: dict[str, Any],
) -> None:
    env, fixture = _fixture()
    fixture[fixture_key][0].company_id = fixture["other_company"]

    page = _dispatch(env, capability_id, parameters)

    assert page["items"] == []


def test_journal_item_search_applies_every_filter_and_normalizes_rows() -> None:
    env, _ = _fixture()
    parameters = {
        "date_from": "2026-08-01",
        "date_to": "2026-08-31",
        "move_id": 301,
        "account_id": 121,
        "partner_id": 31,
        "journal_id": 4,
        "posted_only": True,
        "after_id": None,
        "limit": 1,
    }

    page = _dispatch(env, "journal_item.search", parameters)

    assert page["items"] == [_expected_item("journal_item.search")]
    call = _search_call(env.models["account.move.line"])
    for term in (
        ("company_id", "=", 7),
        ("date", ">=", "2026-08-01"),
        ("date", "<=", "2026-08-31"),
        ("move_id", "=", 301),
        ("account_id", "=", 121),
        ("partner_id", "=", 31),
        ("journal_id", "=", 4),
        ("parent_state", "=", "posted"),
    ):
        assert term in call[1]
    assert call[2:4] == ("id", 1)


@pytest.mark.parametrize("capability_id", ["journal_item.search", "journal_item.get"])
def test_journal_item_reads_normalize_an_unnamed_draft_move(
    capability_id: str,
) -> None:
    env, fixture = _fixture()
    line = fixture["journal_lines"][0]
    line.move_id.name = False
    line.move_id.state = "draft"
    line.move_id.move_type = "out_invoice"
    line.parent_state = "draft"

    page = _dispatch(env, capability_id, _parameters(capability_id))

    expected = _expected_item(capability_id)
    expected["move"].update(name=None, state="draft", move_type="out_invoice")
    assert page["items"] == [expected]


@pytest.mark.parametrize("value", [False, None, {}])
def test_line_analytic_distribution_normalizes_native_empty_values(value: Any) -> None:
    assert core._line_analytic_distribution(value) == {}


def test_line_analytic_distribution_preserves_keys_without_write_limits() -> None:
    value = {
        **{str(index): 1 for index in range(20)},
        "2,1": Decimal("123.4567890"),
        "1,2": -5.25,
        "1,1": -7,
        "opaque key\n": Decimal("2.5E-7"),
        " ": -0.0,
        "decimal-zero": Decimal("-0.000"),
        "wide": Decimal("1E+300"),
    }
    original = value.copy()

    assert core._line_analytic_distribution(value) == {
        **{str(index): "1" for index in range(20)},
        "2,1": "123.456789",
        "1,2": "-5.25",
        "1,1": "-7",
        "opaque key\n": "0.00000025",
        " ": "0",
        "decimal-zero": "0",
        "wide": "1" + "0" * 300,
    }
    assert value == original


@pytest.mark.parametrize(
    "value",
    [
        True,
        0,
        [],
        "",
        {"": 1},
        {1: 1},
        *(
            {"1": percentage}
            for percentage in (
                True,
                False,
                None,
                "1",
                [],
                {},
                float("nan"),
                float("inf"),
                Decimal("NaN"),
                Decimal("-Infinity"),
            )
        ),
    ],
)
def test_line_analytic_distribution_rejects_invalid_native_values(value: Any) -> None:
    with pytest.raises((TypeError, ValueError)):
        core._line_analytic_distribution(value)


@pytest.mark.parametrize("capability_id", ["journal_item.search", "journal_item.get"])
def test_journal_item_reads_select_and_normalize_analytic_distribution(
    capability_id: str,
) -> None:
    env, fixture = _fixture()
    fixture["journal_lines"][0].analytic_distribution = {
        "3,1": Decimal("60.12500"),
        "1,2": -5,
        "opaque": -0.0,
    }
    env.models["account.analytic.account"].access = False

    page = _dispatch(env, capability_id, _parameters(capability_id))

    expected = _expected_item(capability_id)
    expected["analytic_distribution"] = {"3,1": "60.125", "1,2": "-5", "opaque": "0"}
    assert page["items"] == [expected]
    assert "analytic_distribution" in _search_call(env.models["account.move.line"])[4]
    assert env.models["account.analytic.account"].calls == []
    assert env.models["account.analytic.plan"].calls == []


@pytest.mark.parametrize("capability_id", ["journal_item.search", "journal_item.get"])
def test_journal_item_reads_reject_invalid_native_analytic_distribution(
    capability_id: str,
) -> None:
    env, fixture = _fixture()
    fixture["journal_lines"][0].analytic_distribution = {"1": True}

    with pytest.raises(Failure) as caught:
        _dispatch(env, capability_id, _parameters(capability_id))

    assert caught.value.code == "odoo_runtime_error"
    assert caught.value.exit_code == 7


@pytest.mark.parametrize(
    "capability_id",
    [
        "journal_item.search",
        "payment.method.list",
        "reconciliation.model.list",
        "product.search",
        "analytic.plan.list",
        "analytic.account.search",
        "fiscal_position.search",
        "account.tag.list",
        "cash_rounding.list",
        "journal.group.list",
        "incoterm.list",
        "partner.bank_account.search",
        "bank.statement.search",
        "reconciliation.partial.list",
        "analytic.line.search",
        "analytic.distribution_model.list",
        "analytic.applicability.list",
        "budget.search",
        "budget.line.list",
    ],
)
def test_after_id_is_verified_in_scope_then_pages_forward(capability_id: str) -> None:
    env, _ = _fixture()
    parameters: dict[str, Any] = {"after_id": 31, "limit": 2}
    if capability_id == "journal_item.search":
        parameters = {
            "date_from": None,
            "date_to": None,
            "move_id": None,
            "account_id": None,
            "partner_id": None,
            "journal_id": None,
            "posted_only": False,
            **parameters,
        }
    elif capability_id in REFERENCE_PAGE_DEFAULTS:
        parameters = {**REFERENCE_PAGE_DEFAULTS[capability_id], **parameters}

    page = _dispatch(env, capability_id, parameters)

    assert page["cursor_found"] is True
    assert [item["id"] for item in page["items"]] == [32]
    model = env.models[PRIMARY_MODELS[capability_id]]
    boundary = next(call for call in model.calls if call[0] == "search_count")
    assert ("id", "=", 31) in boundary[1]
    search = next(
        call
        for call in model.calls
        if call[0] == "search_read" and ("id", ">", 31) in call[1]
    )
    assert ("id", ">", 31) in search[1]
    assert search[2:4] == ("id", 2)


def test_full_reconcile_cursor_is_verified_in_scope_then_pages_forward() -> None:
    env, _ = _fixture()

    page = _dispatch(
        env,
        "reconciliation.full.list",
        {"after_id": 31, "limit": 2},
    )

    assert page["cursor_found"] is True
    assert page["items"] == []
    model = env.models["account.full.reconcile"]
    boundary = next(call for call in model.calls if call[0] == "search_count")
    assert ("reconciled_line_ids.company_id", "=", 7) in boundary[1]
    assert ("id", "=", 31) in boundary[1]
    search = _search_call(model)
    assert ("id", ">", 31) in search[1]


def test_tax_group_cursor_is_verified_inside_the_current_company() -> None:
    env, _ = _fixture()

    page = _dispatch(env, "tax.group.list", {"after_id": 5, "limit": 2})

    assert page["cursor_found"] is True
    assert page["items"] == [_expected_item("tax.group.list", 32)]
    model = env.models["account.tax.group"]
    boundary = next(call for call in model.calls if call[0] == "search_count")
    assert ("company_id", "=", 7) in boundary[1]
    assert ("id", "=", 5) in boundary[1]


def test_missing_after_id_returns_an_explicit_empty_cursor_page() -> None:
    env, _ = _fixture()

    page = _dispatch(
        env,
        "payment.method.list",
        {"after_id": 999, "limit": 2},
    )

    assert page["cursor_found"] is False
    assert page["items"] == []


@pytest.mark.parametrize(
    ("payload", "company_id"),
    [
        ({}, 7),
        (
            {
                "capability_id": "journal.get",
                "company_id": 7,
                "parameters": {"journal_id": 9},
                "extra": True,
            },
            7,
        ),
        (
            {
                "capability_id": "res.partner.read",
                "company_id": 7,
                "parameters": {},
            },
            7,
        ),
        (
            {
                "capability_id": "journal.get",
                "company_id": 8,
                "parameters": {"journal_id": 9},
            },
            7,
        ),
        (
            {
                "capability_id": "journal.get",
                "company_id": 7,
                "parameters": {"journal_id": True},
            },
            7,
        ),
        (
            {
                "capability_id": "payment.method.list",
                "company_id": 7,
                "parameters": {"after_id": None, "limit": 0},
            },
            7,
        ),
        (
            {
                "capability_id": "incoterm.list",
                "company_id": 7,
                "parameters": {"query": "FOB", "after_id": None, "limit": 1},
            },
            7,
        ),
        (
            {
                "capability_id": "partner.bank_account.search",
                "company_id": 7,
                "parameters": {
                    "partner_id": True,
                    "active": None,
                    "after_id": None,
                    "limit": 1,
                },
            },
            7,
        ),
        (
            {
                "capability_id": "bank.statement.search",
                "company_id": 7,
                "parameters": {
                    "journal_id": None,
                    "date_from": "2026-09-01",
                    "date_to": "2026-08-31",
                    "after_id": None,
                    "limit": 1,
                },
            },
            7,
        ),
        (
            {
                "capability_id": "reconciliation.partial.list",
                "company_id": 7,
                "parameters": {
                    "date_from": None,
                    "after_id": None,
                    "limit": 1,
                },
            },
            7,
        ),
        (
            {
                "capability_id": "analytic.line.search",
                "company_id": 7,
                "parameters": {
                    "query": " spaced ",
                    "date_from": None,
                    "date_to": None,
                    "analytic_account_id": None,
                    "after_id": None,
                    "limit": 1,
                },
            },
            7,
        ),
        (
            {
                "capability_id": "budget.search",
                "company_id": 7,
                "parameters": {
                    "query": None,
                    "state": "approved",
                    "budget_type": None,
                    "date_from": None,
                    "date_to": None,
                    "after_id": None,
                    "limit": 1,
                },
            },
            7,
        ),
        (
            {
                "capability_id": "budget.line.list",
                "company_id": 7,
                "parameters": {
                    "budget_id": 31,
                    "plan_id": 31,
                    "analytic_account_id": None,
                    "after_id": None,
                    "limit": 1,
                },
            },
            7,
        ),
    ],
)
def test_runtime_rejects_expanded_or_invalid_payloads(
    payload: dict[str, Any], company_id: int
) -> None:
    env, _ = _fixture()

    with pytest.raises(Failure) as caught:
        core.dispatch(env, payload, company_id, failure_type=Failure)

    assert caught.value.code == "bridge_protocol_error"


def test_company_and_group_gates_return_closed_empty_pages() -> None:
    env, _ = _fixture()
    env.models["res.company"].rows = Records()
    assert _dispatch(env, "journal.get", {"journal_id": 9}) == {
        "user_id": 5,
        "company_visible": False,
        "module_installed": True,
        "access_allowed": False,
        "cursor_found": True,
        "items": [],
    }

    env, _ = _fixture()
    env.user.groups_allowed = False
    denied_group = _dispatch(env, "journal.get", {"journal_id": 9})
    assert denied_group["access_allowed"] is False
    assert denied_group["items"] == []


def test_applicability_uses_the_account_user_group_gate() -> None:
    env, _ = _fixture()

    _dispatch(
        env,
        "analytic.applicability.list",
        {"after_id": None, "limit": 1},
    )

    assert env.user.calls == ["account.group_account_user"]

    env, _ = _fixture()
    _dispatch(env, "analytic.line.get", {"analytic_line_id": 31})
    assert env.user.calls == ["account.group_account_readonly"]


def test_analytic_and_budget_capabilities_use_only_the_frozen_acl_models() -> None:
    expected = {
        "analytic.line": {
            "res.company",
            "account.analytic.line",
            "account.analytic.account",
            "res.partner",
            "res.currency",
            "product.product",
            "uom.uom",
            "account.account",
            "account.move.line",
        },
        "analytic.distribution_model": {
            "res.company",
            "account.analytic.distribution.model",
            "account.analytic.account",
            "res.partner",
            "res.partner.category",
            "product.product",
            "product.category",
        },
        "analytic.applicability": {
            "res.company",
            "account.analytic.applicability",
            "account.analytic.plan",
            "product.category",
        },
        "budget": {"res.company", "budget.analytic", "res.users"},
        "budget.line": {
            "res.company",
            "budget.analytic",
            "budget.line",
            "res.currency",
            "account.analytic.plan",
            "account.analytic.account",
        },
    }

    for prefix, model_names in expected.items():
        page_id = (
            f"{prefix}.search"
            if prefix in {"analytic.line", "budget"}
            else f"{prefix}.list"
        )
        assert set(core._REQUIRED_MODELS[page_id]) == model_names
        assert set(core._REQUIRED_MODELS[f"{prefix}.get"]) == model_names


@pytest.mark.parametrize(
    "capability_id",
    [
        "partner.bank_account.search",
        "partner.bank_account.get",
        "bank.statement.search",
        "bank.statement.get",
        "reconciliation.partial.list",
        "reconciliation.partial.get",
        "reconciliation.full.list",
        "reconciliation.full.get",
        "analytic.line.search",
        "analytic.line.get",
        "analytic.distribution_model.list",
        "analytic.distribution_model.get",
        "analytic.applicability.list",
        "analytic.applicability.get",
        "budget.search",
        "budget.get",
        "budget.line.list",
        "budget.line.get",
    ],
)
def test_recent_capabilities_gate_every_required_model_read_acl(
    capability_id: str,
) -> None:
    for model_name in core._REQUIRED_MODELS[capability_id]:
        env, _ = _fixture()
        env.models[model_name].access = False

        page = _dispatch(env, capability_id, _parameters(capability_id))

        assert page["module_installed"] is True
        assert page["access_allowed"] is False
        assert page["items"] == []


def test_partial_reconcile_uses_only_the_frozen_five_model_acl_set() -> None:
    expected = {
        "res.company",
        "account.partial.reconcile",
        "account.move.line",
        "account.move",
        "res.currency",
    }

    assert set(core._REQUIRED_MODELS["reconciliation.partial.list"]) == expected
    assert set(core._REQUIRED_MODELS["reconciliation.partial.get"]) == expected


def test_partial_reconcile_does_not_read_the_full_reconcile_model() -> None:
    env, _ = _fixture()
    env.registry.models.pop("account.full.reconcile")

    page = _dispatch(
        env,
        "reconciliation.partial.get",
        {"partial_reconcile_id": 31},
    )

    assert page["items"] == [_expected_item("reconciliation.partial.get")]


def test_accounting_metadata_reads_use_fixed_scopes_and_normalized_shapes() -> None:
    env, _ = _fixture()
    company = env.models["res.company"].rows[0]
    china = env.models["res.country"].rows[0]
    japan = env.models["res.country"].rows[1]
    state = env.models["res.country.state"].rows[0]
    state.country_id = china
    journal = env.models["account.journal"].rows[0]
    account = next(row for row in env.models["account.account"].rows if row.id == 101)
    bank_account = env.models["res.partner.bank"].rows[0]
    methods = env.models["account.payment.method.line"].rows
    journal.default_account_id = account
    journal.suspense_account_id = account
    journal.profit_account_id = False
    journal.loss_account_id = False
    journal.bank_account_id = bank_account
    journal.inbound_payment_method_line_ids = Records([methods[1], methods[0]])
    journal.outbound_payment_method_line_ids = Records()
    journal.invoice_reference_type = "invoice"
    journal.invoice_reference_model = "odoo"
    journal.restrict_mode_hash_table = False

    bank = env.models["res.bank"].rows[0]
    bank.active = True
    bank.street = "1 Finance Road"
    bank.street2 = False
    bank.zip = "100000"
    bank.city = "Beijing"
    bank.state = state
    bank.country = china
    bank.email = "bank@example.test"
    bank.phone = False

    root_group = _record(
        40,
        name="Assets",
        code_prefix_start="1",
        code_prefix_end="1",
        parent_id=False,
        company_id=company,
    )
    child_group = _record(
        41,
        name="Child Assets",
        code_prefix_start="10",
        code_prefix_end="19",
        parent_id=root_group,
        company_id=company,
    )
    env.models["account.group"] = Model("account.group", [root_group, child_group])
    env.registry.models["account.group"] = env.models["account.group"]

    tax = env.models["account.tax"].rows[0]
    tags = env.models["account.account.tag"].rows
    repartition_line = _record(
        42,
        sequence=10,
        company_id=company,
        tax_id=tax,
        document_type="invoice",
        repartition_type="tax",
        factor_percent=Decimal("100.00"),
        factor=Decimal("1.00"),
        account_id=account,
        tag_ids=Records([tags[1], tags[0]]),
        use_in_tax_closing=True,
    )
    env.models["account.tax.repartition.line"] = Model(
        "account.tax.repartition.line", [repartition_line]
    )
    env.registry.models["account.tax.repartition.line"] = env.models[
        "account.tax.repartition.line"
    ]

    reconciliation_line = _record(
        43,
        sequence=20,
        company_id=company,
        model_id=env.models["account.reconcile.model"].rows[0],
        account_id=account,
        partner_id=env.models["res.partner"].rows[0],
        label="Bank fee",
        amount_type="fixed",
        amount=Decimal("15.00"),
        amount_string="15",
        tax_ids=Records([tax]),
        analytic_distribution={"31": 100},
    )
    env.models["account.reconcile.model.line"] = Model(
        "account.reconcile.model.line", [reconciliation_line]
    )
    env.registry.models["account.reconcile.model.line"] = env.models[
        "account.reconcile.model.line"
    ]

    root_report = _record(
        50,
        name="Root Report",
        active=True,
        root_report_id=False,
        country_id=False,
        availability_condition="always",
    )
    variant_report = _record(
        51,
        name="China Variant",
        active=True,
        root_report_id=False,
        country_id=china,
        availability_condition="country",
    )
    foreign_variant = _record(
        54,
        name="Japan Variant",
        active=True,
        root_report_id=False,
        country_id=japan,
        availability_condition="country",
    )
    section_report = _record(
        52,
        name="Assets Section",
        active=True,
        root_report_id=False,
        country_id=False,
        availability_condition="always",
    )
    report = _record(
        53,
        name="Balance Sheet",
        active=True,
        root_report_id=root_report,
        country_id=china,
        availability_condition="country",
        variant_report_ids=Records([variant_report, foreign_variant]),
        section_report_ids=Records([section_report]),
        column_ids=Records(),
        filter_multi_company="selector",
        filter_date_range=True,
        filter_show_draft=False,
        filter_unreconciled=False,
        filter_unfold_all=True,
        filter_journals=True,
        filter_analytic=True,
        filter_partner=False,
    )
    later_column = _record(
        500,
        name="Balance",
        expression_label="balance",
        sequence=20,
        figure_type="monetary",
        sortable=True,
        blank_if_zero=False,
        report_id=report,
    )
    earlier_column = _record(
        501,
        name="Current",
        expression_label="current",
        sequence=10,
        figure_type="monetary",
        sortable=False,
        blank_if_zero=True,
        report_id=report,
    )
    report.column_ids = Records([later_column, earlier_column])
    env.models["account.report"] = Model(
        "account.report",
        [root_report, variant_report, foreign_variant, section_report, report],
    )
    env.registry.models["account.report"] = env.models["account.report"]
    env.models["account.report.column"] = Model(
        "account.report.column", [later_column, earlier_column]
    )
    env.registry.models["account.report.column"] = env.models["account.report.column"]

    group_page = _dispatch(
        env,
        "account.group.list",
        {"query": "Child", "parent_id": 40, "after_id": None, "limit": 10},
    )
    journal_page = _dispatch(
        env, "journal.configuration.inspect", {"journal_id": journal.id}
    )
    tax_parameters = {
        "tax_id": tax.id,
        "document_types": ["invoice"],
        "repartition_types": ["tax"],
        "account_id": account.id,
        "use_in_tax_closing": True,
        "after_id": None,
        "limit": 10,
    }
    tax_list_page = _dispatch(env, "tax.repartition_line.list", tax_parameters)
    tax_get_page = _dispatch(
        env,
        "tax.repartition_line.get",
        {"tax_repartition_line_id": repartition_line.id},
    )
    reconciliation_parameters = {
        "reconciliation_model_id": reconciliation_line.model_id.id,
        "account_id": account.id,
        "partner_id": reconciliation_line.partner_id.id,
        "amount_types": ["fixed"],
        "after_id": None,
        "limit": 10,
    }
    reconciliation_list_page = _dispatch(
        env, "reconciliation.model.line.list", reconciliation_parameters
    )
    reconciliation_get_page = _dispatch(
        env,
        "reconciliation.model.line.get",
        {"reconciliation_model_line_id": reconciliation_line.id},
    )
    bank_list_page = _dispatch(
        env,
        "bank.list",
        {
            "query": "Fixture",
            "country_id": china.id,
            "active": True,
            "after_id": None,
            "limit": 10,
        },
    )
    bank_get_page = _dispatch(env, "bank.get", {"bank_id": bank.id})
    report_list_page = _dispatch(
        env,
        "report.catalog.list",
        {
            "country_id": china.id,
            "root_report_id": root_report.id,
            "availability_conditions": ["country"],
            "active": True,
            "after_id": None,
            "limit": 10,
        },
    )
    report_get_page = _dispatch(env, "report.catalog.get", {"report_id": report.id})

    assert group_page["items"] == [
        {
            "id": 41,
            "name": "Child Assets",
            "code_prefix_start": "10",
            "code_prefix_end": "19",
            "parent": {"id": 40, "name": "Assets"},
            "company_id": 7,
        }
    ]
    assert [item["id"] for item in tax_list_page["items"]] == [42]
    assert tax_get_page["items"] == tax_list_page["items"]
    assert tax_get_page["items"][0]["tags"] == [
        {"id": 31, "name": "Operating"},
        {"id": 32, "name": "Shared"},
    ]
    assert [item["id"] for item in reconciliation_list_page["items"]] == [43]
    assert reconciliation_get_page["items"] == reconciliation_list_page["items"]
    assert reconciliation_get_page["items"][0]["analytic_distribution"] == [
        {
            "analytic_accounts": [{"id": 31, "name": "Project Alpha"}],
            "percentage": "100",
        }
    ]
    assert journal_page["items"][0]["inbound_payment_methods"] == [
        {"id": 31, "name": "Manual"},
        {"id": 32, "name": "Manual"},
    ]
    assert bank_get_page["items"] == bank_list_page["items"]
    assert bank_get_page["items"][0]["country"] == {"id": 156, "name": "China"}
    assert report_get_page["items"] == report_list_page["items"]
    assert report_get_page["items"][0]["variants"] == [
        {"id": 51, "name": "China Variant"}
    ]
    assert [column["id"] for column in report_get_page["items"][0]["columns"]] == [
        501,
        500,
    ]


def test_odoo_false_analytic_distribution_is_normalized_as_empty() -> None:
    assert core._parsed_distribution(False) == []


def test_parent_company_accounting_metadata_is_visible_to_branch_only() -> None:
    env, fixture = _fixture()
    branch = fixture["company"]
    unrelated_company = fixture["other_company"]
    parent = _record(
        70,
        name="Parent Company",
        currency_id=branch.currency_id,
        account_fiscal_country_id=branch.account_fiscal_country_id,
        parent_id=False,
        child_ids=Records([branch]),
    )
    branch.parent_id = parent
    branch.child_ids = Records()
    unrelated_company.parent_id = False
    unrelated_company.child_ids = Records()
    env.models["res.company"].rows.append(parent)

    account = next(row for row in env.models["account.account"].rows if row.id == 101)
    account.company_ids = Records([parent])
    partner = env.models["res.partner"].rows[0]
    partner.company_id = parent
    analytic_account = fixture["analytic_accounts"][1]
    analytic_account.company_id = parent

    journal = next(row for row in env.models["account.journal"].rows if row.id == 9)
    journal.company_id = parent
    journal.default_account_id = account
    journal.suspense_account_id = account
    journal.profit_account_id = False
    journal.loss_account_id = False
    journal.bank_account_id = fixture["partner_banks"][0]
    journal.bank_account_id.company_id = parent
    journal.inbound_payment_method_line_ids = Records(fixture["payment_method_lines"])
    journal.outbound_payment_method_line_ids = Records()
    journal.invoice_reference_type = "invoice"
    journal.invoice_reference_model = "odoo"
    journal.restrict_mode_hash_table = False
    for method in fixture["payment_method_lines"]:
        method.company_id = parent
        method.journal_id = journal

    group = _record(
        60,
        name="Parent Assets",
        code_prefix_start="1",
        code_prefix_end="1",
        parent_id=False,
        company_id=parent,
    )
    unrelated_group = _record(
        61,
        name="Unrelated Assets",
        code_prefix_start="2",
        code_prefix_end="2",
        parent_id=False,
        company_id=unrelated_company,
    )
    env.models["account.group"].rows = Records([group, unrelated_group])

    tax = env.models["account.tax"].rows[0]
    tax.company_id = parent
    unrelated_tax = _record(99, name="Unrelated Tax", company_id=unrelated_company)
    parent_repartition = _record(
        62,
        sequence=10,
        company_id=parent,
        tax_id=tax,
        document_type="invoice",
        repartition_type="tax",
        factor_percent=Decimal(100),
        factor=Decimal(1),
        account_id=account,
        tag_ids=Records(),
        use_in_tax_closing=True,
    )
    unrelated_repartition = _record(
        63,
        sequence=10,
        company_id=unrelated_company,
        tax_id=unrelated_tax,
        document_type="invoice",
        repartition_type="tax",
        factor_percent=Decimal(100),
        factor=Decimal(1),
        account_id=False,
        tag_ids=Records(),
        use_in_tax_closing=False,
    )
    env.models["account.tax.repartition.line"].rows = Records(
        [parent_repartition, unrelated_repartition]
    )

    reconcile_model = fixture["reconcile_models"][0]
    reconcile_model.company_id = parent
    unrelated_model = fixture["reconcile_models"][1]
    unrelated_model.company_id = unrelated_company
    parent_reconciliation_line = _record(
        64,
        sequence=10,
        company_id=parent,
        model_id=reconcile_model,
        account_id=account,
        partner_id=partner,
        label="Parent fee",
        amount_type="fixed",
        amount=Decimal(5),
        amount_string="5",
        tax_ids=Records([tax]),
        analytic_distribution={str(analytic_account.id): 100},
    )
    unrelated_reconciliation_line = _record(
        65,
        sequence=10,
        company_id=unrelated_company,
        model_id=unrelated_model,
        account_id=False,
        partner_id=False,
        label="Unrelated fee",
        amount_type="fixed",
        amount=Decimal(7),
        amount_string="7",
        tax_ids=Records(),
        analytic_distribution={},
    )
    env.models["account.reconcile.model.line"].rows = Records(
        [parent_reconciliation_line, unrelated_reconciliation_line]
    )

    group_page = _dispatch(
        env,
        "account.group.list",
        {"query": None, "parent_id": None, "after_id": None, "limit": 10},
    )
    group_get_page = _dispatch(env, "account.group.get", {"account_group_id": group.id})
    unrelated_group_page = _dispatch(
        env, "account.group.get", {"account_group_id": unrelated_group.id}
    )
    journal_page = _dispatch(
        env, "journal.configuration.inspect", {"journal_id": journal.id}
    )
    unrelated_journal_page = _dispatch(
        env, "journal.configuration.inspect", {"journal_id": 19}
    )
    tax_page = _dispatch(
        env,
        "tax.repartition_line.list",
        {
            "tax_id": None,
            "document_types": None,
            "repartition_types": None,
            "account_id": None,
            "use_in_tax_closing": None,
            "after_id": None,
            "limit": 10,
        },
    )
    tax_get_page = _dispatch(
        env,
        "tax.repartition_line.get",
        {"tax_repartition_line_id": parent_repartition.id},
    )
    unrelated_tax_page = _dispatch(
        env,
        "tax.repartition_line.get",
        {"tax_repartition_line_id": unrelated_repartition.id},
    )
    reconciliation_page = _dispatch(
        env,
        "reconciliation.model.line.list",
        {
            "reconciliation_model_id": None,
            "account_id": None,
            "partner_id": None,
            "amount_types": None,
            "after_id": None,
            "limit": 10,
        },
    )
    reconciliation_get_page = _dispatch(
        env,
        "reconciliation.model.line.get",
        {"reconciliation_model_line_id": parent_reconciliation_line.id},
    )
    unrelated_reconciliation_page = _dispatch(
        env,
        "reconciliation.model.line.get",
        {"reconciliation_model_line_id": unrelated_reconciliation_line.id},
    )

    assert [item["id"] for item in group_page["items"]] == [group.id]
    assert group_get_page["items"] == group_page["items"]
    assert [item["id"] for item in tax_page["items"]] == [parent_repartition.id]
    assert tax_get_page["items"] == tax_page["items"]
    assert [item["id"] for item in reconciliation_page["items"]] == [
        parent_reconciliation_line.id
    ]
    assert reconciliation_get_page["items"] == reconciliation_page["items"]
    for page in (
        group_page,
        journal_page,
        tax_page,
        reconciliation_page,
    ):
        assert page["items"][0]["company_id"] == parent.id
    assert unrelated_journal_page["items"] == []
    assert unrelated_group_page["items"] == []
    assert unrelated_tax_page["items"] == []
    assert unrelated_reconciliation_page["items"] == []
    for model_name in (
        "account.group",
        "account.journal",
        "account.tax.repartition.line",
        "account.reconcile.model.line",
    ):
        assert ("company_id", "parent_of", [branch.id]) in _search_call(
            env.models[model_name]
        )[1]


@pytest.mark.parametrize("capability_id", sorted(EXPECTED_CAPABILITY_IDS))
def test_each_capability_gates_its_primary_model_and_read_acl(
    capability_id: str,
) -> None:
    env, _ = _fixture()
    primary_model = PRIMARY_MODELS[capability_id]
    env.registry.models.pop(primary_model)
    missing = _dispatch(env, capability_id, _parameters(capability_id))
    assert missing["module_installed"] is False
    assert missing["access_allowed"] is False
    assert missing["items"] == []

    env, _ = _fixture()
    env.models[primary_model].access = False
    denied_acl = _dispatch(env, capability_id, _parameters(capability_id))
    assert denied_acl["module_installed"] is True
    assert denied_acl["access_allowed"] is False
    assert denied_acl["items"] == []


class CreditAggregateModel(Model):
    def _read_group(
        self,
        domain: list[Any],
        *,
        groupby: list[str],
        aggregates: list[str],
    ) -> list[tuple[Decimal]]:
        self.calls.append(("_read_group", domain, groupby, aggregates))
        assert ("company_id", "=", 7) in domain
        assert groupby == []
        assert aggregates == ["amount_residual:sum"]
        account_type = next(
            term[2]
            for term in domain
            if isinstance(term, tuple) and term[0] == "account_id.account_type"
        )
        return [
            (
                Decimal("125.50")
                if account_type == "asset_receivable"
                else Decimal("-45.00"),
            )
        ]


class MoveAggregateModel(Model):
    def _read_group(
        self,
        domain: list[Any],
        *,
        groupby: list[str],
        aggregates: list[str],
    ) -> list[tuple[str, Decimal]]:
        self.calls.append(("_read_group", domain, groupby, aggregates))
        assert ("company_id", "=", 7) in domain
        assert ("commercial_partner_id", "=", 31) in domain
        assert ("state", "not in", ["draft", "cancel"]) in domain
        assert (
            "move_type",
            "in",
            ["out_invoice", "out_refund", "out_receipt"],
        ) in domain
        assert groupby == []
        assert aggregates == ["invoice_date:min", "amount_total_signed:sum"]
        return [("2026-08-01", Decimal("250.00"))]


def _accounting_insight_fixture() -> tuple[
    Env, dict[str, dict[str, Any]], dict[str, dict[str, Any]]
]:
    env, values = _fixture()
    company = values["company"]
    cny = env.models["res.currency"].rows[0]
    partner = env.models["res.partner"].rows[0]
    partner.credit_to_invoice = Decimal("20.00")
    partner.credit_limit = Decimal("500.00")
    partner.use_partner_credit_limit = True
    partner.total_invoiced = Decimal("1000.00")
    partner.commercial_partner_id = partner
    journal = next(row for row in env.models["account.journal"].rows if row.id == 4)
    origin_account = next(
        row for row in env.models["account.account"].rows if row.id == 31
    )
    destination_account = next(
        row for row in env.models["account.account"].rows if row.id == 121
    )

    tax_totals = {
        "has_tax_groups": True,
        "subtotals": [
            {
                "name": "Untaxed Amount",
                "base_amount_currency": Decimal("100.00"),
                "tax_amount_currency": Decimal("13.00"),
                "tax_groups": [
                    {
                        "id": 5,
                        "group_name": "VAT",
                        "base_amount_currency": Decimal("100.00"),
                        "tax_amount_currency": Decimal("13.00"),
                    }
                ],
            }
        ],
    }
    invoice = _record(
        401,
        company_id=company,
        name="INV/2026/0401",
        move_type="out_invoice",
        state="posted",
        date="2026-08-01",
        invoice_date="2026-08-01",
        ref="CUSTOMER-REF",
        partner_id=partner,
        currency_id=cny,
        amount_untaxed=Decimal("100.00"),
        amount_tax=Decimal("13.00"),
        amount_total=Decimal("113.00"),
        tax_totals=tax_totals,
        journal_id=journal,
        auto_post="no",
        auto_post_until=False,
        auto_post_origin_id=False,
        made_sequence_gap=False,
        sequence_prefix="INV/2026/",
        sequence_number=401,
    )
    duplicate = _record(
        402,
        company_id=company,
        name="INV/2026/0402",
        move_type="out_invoice",
        state="draft",
        date="2026-08-01",
        invoice_date="2026-08-01",
        ref=False,
        partner_id=partner,
        currency_id=cny,
        amount_untaxed=Decimal("100.00"),
        amount_tax=Decimal("13.00"),
        amount_total=Decimal("113.00"),
        tax_totals=tax_totals,
        journal_id=journal,
        auto_post="no",
        auto_post_until=False,
        auto_post_origin_id=False,
        made_sequence_gap=False,
        sequence_prefix=False,
        sequence_number=0,
        duplicated_ref_ids=Records([invoice]),
    )
    invoice.duplicated_ref_ids = Records([duplicate])
    sequence_marker = _record(
        403,
        company_id=company,
        name="MISC/2026/0403",
        move_type="entry",
        state="posted",
        date="2026-08-02",
        invoice_date=False,
        ref=False,
        partner_id=False,
        currency_id=cny,
        amount_untaxed=Decimal(0),
        amount_tax=Decimal(0),
        amount_total=Decimal(0),
        tax_totals=False,
        journal_id=journal,
        auto_post="no",
        auto_post_until=False,
        auto_post_origin_id=False,
        made_sequence_gap=True,
        sequence_prefix="MISC/2026/",
        sequence_number=403,
        duplicated_ref_ids=Records(),
    )
    recurring = _record(
        404,
        company_id=company,
        name="MISC/2026/0404",
        move_type="entry",
        state="draft",
        date="2026-08-03",
        invoice_date=False,
        ref="MONTHLY ACCRUAL",
        partner_id=False,
        currency_id=cny,
        amount_untaxed=Decimal(0),
        amount_tax=Decimal(0),
        amount_total=Decimal(0),
        tax_totals=False,
        journal_id=journal,
        auto_post="monthly",
        auto_post_until="2026-12-31",
        auto_post_origin_id=False,
        made_sequence_gap=False,
        sequence_prefix=False,
        sequence_number=0,
        duplicated_ref_ids=Records(),
    )
    env.models["account.move"] = MoveAggregateModel(
        "account.move", [invoice, duplicate, sequence_marker, recurring]
    )
    env.registry.models["account.move"] = env.models["account.move"]

    transfer_model = _record(
        501,
        name="Monthly Allocation",
        active=True,
        state="in_progress",
        journal_id=journal,
        company_id=company,
        date_start="2026-01-01",
        date_stop=False,
        frequency="month",
        account_ids=Records([origin_account]),
        line_ids=Records(),
        move_ids_count=2,
        has_draft_moves=True,
        total_percent=Decimal("100.00"),
    )
    transfer_line = _record(
        502,
        transfer_model_id=transfer_model,
        sequence=10,
        account_id=destination_account,
        percent=Decimal("100.00"),
    )
    transfer_model.line_ids = Records([transfer_line])
    env.models["account.transfer.model"] = Model(
        "account.transfer.model", [transfer_model]
    )
    env.models["account.transfer.model.line"] = Model(
        "account.transfer.model.line", [transfer_line]
    )

    lock_exception = _record(
        701,
        active=True,
        state="active",
        company_id=company,
        user_id=env.models["res.users"].rows[0],
        reason="Year-end correction",
        end_datetime="2026-09-01 08:30:00",
        lock_date_field="fiscalyear_lock_date",
        lock_date="2026-07-31",
        company_lock_date="2026-08-31",
    )
    env.models["account.lock_exception"] = Model(
        "account.lock_exception", [lock_exception]
    )

    report = _record(601, name="Balance Sheet")
    report_line = _record(602, name="Retained Earnings", code="RE", report_id=report)
    carryover_line = _record(604, name="Opening Balance", code=False, report_id=report)
    expression = _record(603, label="balance", report_line_id=report_line)
    external_value = _record(
        605,
        name="Manual adjustment",
        value=Decimal("12.500"),
        text_value=False,
        date="2026-08-31",
        target_report_expression_id=expression,
        target_report_line_id=report_line,
        target_report_expression_label="balance",
        company_id=company,
        carryover_origin_expression_label="opening_balance",
        carryover_origin_report_line_id=carryover_line,
    )
    env.models["account.report"] = Model("account.report", [report])
    env.models["account.report.line"] = Model(
        "account.report.line", [report_line, carryover_line]
    )
    env.models["account.report.expression"] = Model(
        "account.report.expression", [expression]
    )
    env.models["account.report.external.value"] = Model(
        "account.report.external.value", [external_value]
    )
    env.models["account.invoice.report"] = Model("account.invoice.report")
    env.models["account.move.line"] = CreditAggregateModel("account.move.line")
    env.registry.models = env.models

    parameters = {
        "invoice.duplicate_candidates.list": {
            "invoice_id": 401,
            "after_id": None,
            "limit": 10,
        },
        "invoice.tax_breakdown.inspect": {"invoice_id": 401},
        "recurring.journal_entry.search": {
            "states": None,
            "auto_post_types": None,
            "date_from": None,
            "date_to": None,
            "after_id": None,
            "limit": 10,
        },
        "recurring.journal_entry.get": {"entry_id": 404},
        "account.transfer_model.search": {
            "query": None,
            "active": None,
            "after_id": None,
            "limit": 10,
        },
        "account.transfer_model.get": {"transfer_model_id": 501},
        "partner.credit_exposure.inspect": {"partner_id": 31},
        "journal.sequence_irregularity.list": {
            "journal_id": None,
            "date_from": None,
            "date_to": None,
            "after_id": None,
            "limit": 10,
        },
        "account.lock_exception.search": {
            "states": None,
            "user_id": None,
            "lock_date_fields": None,
            "after_id": None,
            "limit": 10,
        },
        "account.lock_exception.get": {"lock_exception_id": 701},
        "report.external_value.search": {
            "report_id": None,
            "expression_id": None,
            "date_from": None,
            "date_to": None,
            "after_id": None,
            "limit": 10,
        },
        "report.external_value.get": {"external_value_id": 605},
    }

    recurring_item = {
        "id": 404,
        "company_id": 7,
        "name": "MISC/2026/0404",
        "date": "2026-08-03",
        "state": "draft",
        "journal": {"id": 4, "code": "MISC", "name": "Miscellaneous Operations"},
        "reference": "MONTHLY ACCRUAL",
        "auto_post": "monthly",
        "auto_post_until": "2026-12-31",
        "auto_post_origin": None,
    }
    transfer_item = {
        "id": 501,
        "name": "Monthly Allocation",
        "active": True,
        "state": "in_progress",
        "company_id": 7,
        "journal": {"id": 4, "code": "MISC", "name": "Miscellaneous Operations"},
        "date_start": "2026-01-01",
        "date_stop": None,
        "frequency": "month",
        "origin_accounts": [{"id": 31, "code": "1000", "name": "Cash"}],
        "destination_lines": [
            {
                "id": 502,
                "sequence": 10,
                "account": {
                    "id": 121,
                    "code": "112200",
                    "name": "Accounts Receivable",
                },
                "percentage": "100",
            }
        ],
        "move_ids_count": 2,
        "has_draft_moves": True,
        "total_percent": "100",
    }
    lock_item = {
        "id": 701,
        "company_id": 7,
        "user": {"id": 5, "name": "V4 Accountant"},
        "reason": "Year-end correction",
        "end_datetime": "2026-09-01T08:30:00Z",
        "state": "active",
        "active": True,
        "lock_date_field": "fiscalyear_lock_date",
        "lock_date": "2026-07-31",
        "company_lock_date": "2026-08-31",
    }
    external_item = {
        "id": 605,
        "company_id": 7,
        "name": "Manual adjustment",
        "date": "2026-08-31",
        "value": "12.5",
        "text_value": None,
        "report": {"id": 601, "name": "Balance Sheet"},
        "report_line": {"id": 602, "name": "Retained Earnings", "code": "RE"},
        "expression": {"id": 603, "label": "balance"},
        "carryover_origin_line": {
            "id": 604,
            "name": "Opening Balance",
        },
        "carryover_origin_expression_label": "opening_balance",
    }
    expected = {
        "invoice.duplicate_candidates.list": {
            "id": 402,
            "company_id": 7,
            "name": "INV/2026/0402",
            "move_type": "out_invoice",
            "state": "draft",
            "invoice_date": "2026-08-01",
            "reference": None,
            "partner": {"id": 31, "name": "Fixture Partner"},
            "currency": {"id": 6, "code": "CNY"},
            "amount_total": "113",
        },
        "invoice.tax_breakdown.inspect": {
            "id": 401,
            "invoice": {
                "id": 401,
                "name": "INV/2026/0401",
                "move_type": "out_invoice",
                "state": "posted",
            },
            "company_id": 7,
            "currency": {"id": 6, "code": "CNY"},
            "amount_untaxed": "100",
            "amount_tax": "13",
            "amount_total": "113",
            "has_tax_groups": True,
            "subtotals": [
                {
                    "name": "Untaxed Amount",
                    "base_amount": "100",
                    "tax_amount": "13",
                    "tax_groups": [
                        {
                            "id": 5,
                            "name": "VAT",
                            "base_amount": "100",
                            "tax_amount": "13",
                        }
                    ],
                }
            ],
        },
        "recurring.journal_entry.search": recurring_item,
        "recurring.journal_entry.get": recurring_item,
        "account.transfer_model.search": transfer_item,
        "account.transfer_model.get": transfer_item,
        "partner.credit_exposure.inspect": {
            "id": 31,
            "partner": {"id": 31, "name": "Fixture Partner"},
            "company_id": 7,
            "company_currency": {"id": 6, "code": "CNY"},
            "credit": "125.5",
            "debit": "45",
            "credit_to_invoice": "20",
            "credit_limit": "500",
            "use_partner_credit_limit": True,
            "days_sales_outstanding": "15.06",
            "total_invoiced": "1000",
        },
        "journal.sequence_irregularity.list": {
            "id": 403,
            "company_id": 7,
            "name": "MISC/2026/0403",
            "date": "2026-08-02",
            "state": "posted",
            "move_type": "entry",
            "journal": {
                "id": 4,
                "code": "MISC",
                "name": "Miscellaneous Operations",
            },
            "sequence_prefix": "MISC/2026/",
            "sequence_number": 403,
            "made_sequence_gap": True,
        },
        "account.lock_exception.search": lock_item,
        "account.lock_exception.get": lock_item,
        "report.external_value.search": external_item,
        "report.external_value.get": external_item,
    }
    return env, parameters, expected


@pytest.mark.parametrize("capability_id", sorted(ACCOUNTING_INSIGHT_CAPABILITY_IDS))
def test_accounting_insight_capabilities_return_frozen_normalized_items(
    capability_id: str,
) -> None:
    env, parameters, expected = _accounting_insight_fixture()

    page = _dispatch(env, capability_id, parameters[capability_id])

    assert page == {
        "user_id": 5,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "cursor_found": True,
        "items": [expected[capability_id]],
    }


def test_tax_breakdown_runtime_item_passes_public_read_validator() -> None:
    env, _, expected = _accounting_insight_fixture()

    class RuntimePort:
        user_id = 5

        def read(
            self,
            *,
            capability_id: str,
            company_id: int,
            parameters: dict[str, Any],
        ) -> dict[str, Any]:
            return core.dispatch(
                env,
                {
                    "capability_id": capability_id,
                    "company_id": company_id,
                    "parameters": parameters,
                },
                company_id,
                failure_type=Failure,
            )

    result = read_core_object(
        "invoice.tax_breakdown.inspect",
        RuntimePort(),
        {
            "schema_version": "v1",
            "request_id": "7bc39413-0d69-4092-9319-795d33f3167c",
            "context": {
                "database": "odoo_cli_v4_dev",
                "company_id": 7,
                "user_login": "v4-agent",
                "language": "zh_CN",
                "timezone": "Asia/Shanghai",
            },
            "parameters": {"invoice_id": 401},
        },
    )

    assert result == expected["invoice.tax_breakdown.inspect"]


def test_credit_exposure_uses_exact_company_acl_aggregates() -> None:
    env, parameters, _ = _accounting_insight_fixture()

    _dispatch(
        env,
        "partner.credit_exposure.inspect",
        parameters["partner.credit_exposure.inspect"],
    )

    aggregate_calls = [
        call
        for call in env.models["account.move.line"].calls
        if call[0] == "_read_group"
    ]
    assert len(aggregate_calls) == 2
    assert all(("company_id", "=", 7) in call[1] for call in aggregate_calls)
    assert all(
        not any(term == ("company_id", "child_of", 7) for term in call[1])
        for call in aggregate_calls
    )
    dso_calls = [
        call for call in env.models["account.move"].calls if call[0] == "_read_group"
    ]
    assert len(dso_calls) == 1
    assert ("company_id", "=", 7) in dso_calls[0][1]
    assert ("commercial_partner_id", "=", 31) in dso_calls[0][1]
    assert dso_calls[0][3] == ["invoice_date:min", "amount_total_signed:sum"]
    assert (
        "with_context",
        {"active_test": False, "allowed_company_ids": [7]},
    ) in env.models["account.move"].calls
    partner_fields = next(
        call[4]
        for call in env.models["res.partner"].calls
        if call[0] == "search_read" and "credit_limit" in call[4]
    )
    assert "days_sales_outstanding" not in partner_fields


def test_credit_exposure_preflights_account_move_model_and_read_acl() -> None:
    env, parameters, _ = _accounting_insight_fixture()
    env.registry.models.pop("account.move")

    missing = _dispatch(
        env,
        "partner.credit_exposure.inspect",
        parameters["partner.credit_exposure.inspect"],
    )

    assert missing["module_installed"] is False
    assert missing["access_allowed"] is False
    assert missing["items"] == []

    env, parameters, _ = _accounting_insight_fixture()
    env.models["account.move"].access = False
    denied = _dispatch(
        env,
        "partner.credit_exposure.inspect",
        parameters["partner.credit_exposure.inspect"],
    )
    assert denied["module_installed"] is True
    assert denied["access_allowed"] is False
    assert denied["items"] == []


def test_missing_duplicate_source_invoice_is_runtime_record_not_found() -> None:
    env, parameters, _ = _accounting_insight_fixture()
    parameters["invoice.duplicate_candidates.list"]["invoice_id"] = 999

    with pytest.raises(Failure) as caught:
        _dispatch(
            env,
            "invoice.duplicate_candidates.list",
            parameters["invoice.duplicate_candidates.list"],
        )

    assert caught.value.code == "record_not_found"
    assert caught.value.exit_code == 4


def test_missing_duplicate_source_invoice_reaches_public_record_not_found() -> None:
    env, _, _ = _accounting_insight_fixture()

    class RuntimePort:
        user_id = 5

        def read(
            self,
            *,
            capability_id: str,
            company_id: int,
            parameters: dict[str, Any],
        ) -> dict[str, Any]:
            return core.dispatch(
                env,
                {
                    "capability_id": capability_id,
                    "company_id": company_id,
                    "parameters": parameters,
                },
                company_id,
                failure_type=CoreObjectReadError,
            )

    with pytest.raises(CoreObjectReadError) as caught:
        read_core_object(
            "invoice.duplicate_candidates.list",
            RuntimePort(),
            {
                "schema_version": "v1",
                "request_id": "7bc39413-0d69-4092-9319-795d33f3167c",
                "context": {
                    "database": "odoo_cli_v4_dev",
                    "company_id": 7,
                    "user_login": "v4-agent",
                    "language": "zh_CN",
                    "timezone": "Asia/Shanghai",
                },
                "parameters": {"invoice_id": 999, "limit": 10, "cursor": None},
            },
        )

    assert caught.value.code == "record_not_found"
    assert caught.value.exit_code == 4


def test_sequence_gap_uses_only_stored_marker_and_rejects_unknown_cursor() -> None:
    env, parameters, _ = _accounting_insight_fixture()
    parameters["journal.sequence_irregularity.list"]["after_id"] = 999

    page = _dispatch(
        env,
        "journal.sequence_irregularity.list",
        parameters["journal.sequence_irregularity.list"],
    )

    assert page["cursor_found"] is False
    calls = env.models["account.move"].calls
    boundary = next(call[1] for call in calls if call[0] == "search_count")
    assert ("company_id", "=", 7) in boundary
    assert ("made_sequence_gap", "=", True) in boundary


def test_lock_exception_reads_disable_active_filter_and_transfer_requires_module() -> (
    None
):
    env, parameters, _ = _accounting_insight_fixture()

    _dispatch(
        env,
        "account.lock_exception.search",
        parameters["account.lock_exception.search"],
    )

    contexts = [
        call[1]
        for call in env.models["account.lock_exception"].calls
        if call[0] == "with_context"
    ]
    assert {"active_test": False, "allowed_company_ids": [7]} in contexts

    env, parameters, _ = _accounting_insight_fixture()
    env.registry.models.pop("account.transfer.model")
    page = _dispatch(
        env,
        "account.transfer_model.search",
        parameters["account.transfer_model.search"],
    )
    assert page["module_installed"] is False
    assert page["access_allowed"] is False
    assert page["items"] == []
