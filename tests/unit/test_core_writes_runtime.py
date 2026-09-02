from __future__ import annotations

import copy
import re
from datetime import date
from decimal import Decimal
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


def _value_ids(value: Any) -> set[int]:
    if isinstance(value, Records):
        return set(value.ids)
    if isinstance(value, Record):
        return {value.id}
    if value in (None, False):
        return set()
    if isinstance(value, (list, tuple, set)):
        return {item.id if isinstance(item, Record) else item for item in value}
    return {value}


class Record:
    def __init__(self, model: str, record_id: int, **values: Any) -> None:
        self._model = model
        self.id = record_id
        for key, value in values.items():
            setattr(self, key, value)

    def __repr__(self) -> str:
        return f"{self._model}({self.id})"

    def round(self, amount: float) -> float:
        if self._model != "res.currency":
            raise AssertionError(f"unexpected round: {self._model}")
        rounding = Decimal(str(getattr(self, "rounding", "0.01")))
        return float(Decimal(str(amount)).quantize(rounding))


class Records:
    def __init__(
        self, env: Env, model: str, records: list[Record] | None = None
    ) -> None:
        self.env = env
        self.model = model
        self.records = list(records or [])

    @property
    def ids(self) -> list[int]:
        return [record.id for record in self.records]

    @property
    def id(self) -> int | bool:
        return self.records[0].id if len(self.records) == 1 else False

    def __bool__(self) -> bool:
        return bool(self.records)

    def __len__(self) -> int:
        return len(self.records)

    def __iter__(self):
        return iter(self.records)

    def __or__(self, other: Records) -> Records:
        by_id = {record.id: record for record in [*self.records, *other.records]}
        return Records(self.env, self.model, list(by_id.values()))

    def __and__(self, other: Records) -> Records:
        other_ids = set(other.ids)
        return Records(
            self.env,
            self.model,
            [record for record in self.records if record.id in other_ids],
        )

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Records)
            and self.model == other.model
            and self.ids == other.ids
        )

    def __getattr__(self, name: str) -> Any:
        if not self.records:
            if name.endswith(("_ids", "_id")):
                target = {
                    "line_ids": "account.move.line",
                    "move_id": "account.move",
                    "reversed_entry_id": "account.move",
                    "matched_debit_ids": "account.partial.reconcile",
                    "matched_credit_ids": "account.partial.reconcile",
                    "full_reconcile_id": "account.full.reconcile",
                    "reconciled_line_ids": "account.move.line",
                    "partial_reconcile_ids": "account.partial.reconcile",
                    "reconciled_invoice_ids": "account.move",
                    "reconciled_bill_ids": "account.move",
                    "depreciation_move_ids": "account.move",
                }.get(name, "unknown")
                return Records(self.env, target)
            return False
        values = [getattr(record, name) for record in self.records]
        if all(isinstance(value, Records) for value in values):
            result = Records(self.env, values[0].model)
            for value in values:
                result |= value
            return result
        if all(isinstance(value, Record) for value in values):
            return Records(self.env, values[0]._model, list(dict.fromkeys(values)))
        if len(values) == 1:
            return values[0]
        return values

    def filtered(self, predicate) -> Records:
        return Records(
            self.env, self.model, [row for row in self.records if predicate(row)]
        )

    def write(self, values: dict[str, Any]) -> bool:
        self.env.calls.append(
            ("write", self.model, tuple(self.ids), copy.deepcopy(values))
        )
        for record in self.records:
            for key, value in values.items():
                if self.model == "account.move" and key in {
                    "invoice_line_ids",
                    "line_ids",
                }:
                    lines = self.env.move_lines_from_commands(value)
                    setattr(record, key, lines)
                    if key == "invoice_line_ids":
                        record.line_ids = lines
                elif self.model == "account.tax" and key in {
                    "invoice_repartition_line_ids",
                    "refund_repartition_line_ids",
                    "repartition_line_ids",
                }:
                    document_type = (
                        "invoice"
                        if key.startswith("invoice")
                        else "refund"
                        if key.startswith("refund")
                        else None
                    )
                    lines = self.env.tax_repartition_lines_from_commands(
                        record, value, document_type=document_type
                    )
                    if key == "repartition_line_ids":
                        record.repartition_line_ids = lines
                        record.invoice_repartition_line_ids = lines.filtered(
                            lambda line: line.document_type == "invoice"
                        )
                        record.refund_repartition_line_ids = lines.filtered(
                            lambda line: line.document_type == "refund"
                        )
                    else:
                        setattr(record, key, lines)
                        record.repartition_line_ids = (
                            record.invoice_repartition_line_ids
                            | record.refund_repartition_line_ids
                        )
                elif self.model == "account.reconcile.model" and key in {
                    "match_journal_ids",
                    "match_partner_ids",
                }:
                    relation_model = (
                        "account.journal"
                        if key == "match_journal_ids"
                        else "res.partner"
                    )
                    setattr(record, key, self.env.relation_from_commands(relation_model, value))
                elif self.model == "account.reconcile.model" and key == "line_ids":
                    record.line_ids = self.env.reconciliation_lines_from_commands(
                        record, value
                    )
                elif self.model == "account.account.tag" and key == "country_id":
                    setattr(record, key, self.env.models["res.country"].browse(value if isinstance(value, int) else []))
                elif self.model == "account.cash.rounding" and key in {"profit_account_id", "loss_account_id"}:
                    setattr(record, key, self.env.models["account.account"].browse(value if isinstance(value, int) else []))
                elif self.model == "account.analytic.applicability" and key in {
                    "analytic_plan_id",
                    "product_categ_id",
                }:
                    relation_model = (
                        "account.analytic.plan"
                        if key == "analytic_plan_id"
                        else "product.category"
                    )
                    setattr(
                        record,
                        key,
                        self.env.models[relation_model].browse(
                            value if isinstance(value, int) else []
                        ),
                    )
                elif self.model == "account.analytic.distribution.model" and key in {
                    "partner_id",
                    "partner_category_id",
                    "product_id",
                    "product_categ_id",
                }:
                    relation_model = {
                        "partner_id": "res.partner",
                        "partner_category_id": "res.partner.category",
                        "product_id": "product.product",
                        "product_categ_id": "product.category",
                    }[key]
                    setattr(
                        record,
                        key,
                        self.env.models[relation_model].browse(
                            value if isinstance(value, int) else []
                        ),
                    )
                else:
                    setattr(record, key, value)
        return True

    def action_post(self) -> None:
        self.env.calls.append(("action_post", tuple(self.ids)))
        if self.model == "account.payment":
            for payment in self.records:
                payment.state = "in_process"
            return
        for move in self.records:
            move.state = "posted"
            for line in move.line_ids:
                line.parent_state = "posted"

    def reverse_moves(self) -> dict[str, Any]:
        return self.env.reverse(self, refund=False)

    def refund_moves(self) -> dict[str, Any]:
        return self.env.reverse(self, refund=True)

    def action_create_payments(self) -> dict[str, Any]:
        return self.env.register_payment(self)

    def js_assign_outstanding_line(self, line_id: int) -> None:
        if self.model != "account.move" or len(self) != 1:
            raise AssertionError("unexpected js_assign_outstanding_line target")
        self.env.assign_outstanding(self, line_id)

    def js_remove_outstanding_partial(self, partial_id: int) -> None:
        if self.model != "account.move" or len(self) != 1:
            raise AssertionError("unexpected js_remove_outstanding_partial target")
        self.env.remove_outstanding(self, partial_id)

    def action_cancel(self) -> None:
        self.env.calls.append(("action_cancel", tuple(self.ids)))
        for payment in self.records:
            payment.state = "canceled"
            payment.is_reconciled = False

    def validate(self) -> None:
        if self.model != "account.asset":
            raise AssertionError(f"unexpected validate: {self.model}")
        self.env.calls.append(("validate_asset", tuple(self.ids)))
        for asset in self.records:
            asset.state = "open"
        if self.env.asset_validate_error is not None:
            raise self.env.asset_validate_error
        for asset in self.records:
            move = self.env.new_record(
                "account.move",
                name=f"DEP/{asset.id}",
                state="posted",
                company_id=self.env.company,
                line_ids=Records(self.env, "account.move.line"),
            )
            asset.depreciation_move_ids = Records(self.env, "account.move", [move])

    def reconcile(self) -> None:
        self.env.reconcile(self)

    def unlink(self) -> bool:
        if self.model != "account.partial.reconcile":
            raise AssertionError(f"unexpected unlink: {self.model}")
        return self.env.unlink_partial(self)

    def invalidate_recordset(self, fields: list[str]) -> None:
        self.env.calls.append(("invalidate", tuple(self.ids), tuple(fields)))

    def sudo(self, *args: Any, **kwargs: Any):
        raise AssertionError(f"core writes must never sudo {self.model}")


def _relation_value(value: Any) -> Any:
    if isinstance(value, Record):
        return value.id
    if isinstance(value, Records):
        return value.ids
    return value


def _matches(record: Record, domain: list[Any], env: Env | None = None) -> bool:
    for term in domain:
        if not isinstance(term, tuple):
            continue
        field, operator, expected = term
        actual = _relation_value(getattr(record, field, False))
        if operator == "=":
            if isinstance(actual, list):
                if expected not in actual:
                    return False
            elif actual != expected:
                return False
        elif operator == "in":
            expected_values = set(expected)
            if isinstance(actual, list):
                if not set(actual).intersection(expected_values):
                    return False
            elif actual not in expected_values:
                return False
        elif operator == "parent_of":
            assert field == "company_id" and env is not None
            ancestors = set()
            for company in env.models["res.company"].browse(expected):
                while company:
                    ancestors.add(company.id)
                    company = getattr(company, "parent_id", False)
            actual_ids = set(actual) if isinstance(actual, list) else {actual}
            if not actual_ids.intersection(ancestors):
                return False
        elif operator == "not in":
            expected_values = set(expected)
            if isinstance(actual, list):
                if set(actual).intersection(expected_values):
                    return False
            elif actual in expected_values:
                return False
        elif operator == "!=":
            if isinstance(actual, list):
                if expected in actual:
                    return False
            elif actual == expected:
                return False
        elif operator == "=like":
            pattern = "^" + re.escape(str(expected)).replace(r"%", ".*") + "$"
            if not isinstance(actual, str) or re.fullmatch(pattern, actual) is None:
                return False
        elif operator == "ilike":
            if str(expected).lower() not in str(actual).lower():
                return False
        else:
            raise AssertionError(f"unsupported fake domain operator: {operator}")
    return True


class Model:
    def __init__(
        self, env: Env, name: str, context: dict[str, Any] | None = None
    ) -> None:
        self.env = env
        self.name = name
        self.context = dict(context or {})

    def __bool__(self) -> bool:
        # Odoo model access returns an empty recordset, which is falsey.
        return False

    def has_access(self, operation: str) -> bool:
        self.env.calls.append(("access", self.name, operation))
        return (self.name, operation) != self.env.denied_access

    def with_context(self, **context: Any) -> Model:
        self.env.calls.append(("context", self.name, copy.deepcopy(context)))
        return Model(self.env, self.name, {**self.context, **context})

    def with_company(self, company_id: int) -> Model:
        self.env.calls.append(("company", self.name, company_id))
        return Model(self.env, self.name, self.context)

    def search_count(self, domain: list[Any], *, limit: int) -> int:
        return len(self.search(domain, limit=limit))

    def search(
        self,
        domain: list[Any],
        *,
        limit: int | None = None,
        order: str | None = None,
    ) -> Records:
        self.env.calls.append(
            ("search", self.name, copy.deepcopy(domain), limit, order)
        )
        rows = [
            record
            for record in self.env.data[self.name]
            if _matches(record, domain, self.env)
        ]
        if order == "id":
            rows.sort(key=lambda record: record.id)
        if limit is not None:
            rows = rows[:limit]
        return Records(self.env, self.name, rows)

    def browse(self, ids: int | list[int]) -> Records:
        values = [ids] if isinstance(ids, int) else ids
        return Records(
            self.env,
            self.name,
            [record for record in self.env.data[self.name] if record.id in values],
        )

    def create(self, values: dict[str, Any]) -> Records:
        self.env.calls.append(
            ("create", self.name, copy.deepcopy(values), copy.deepcopy(self.context))
        )
        if self.name == "account.move":
            return self.env.create_move(values)
        if self.name == "account.move.reversal":
            wizard = self.env.new_record(
                self.name,
                **copy.deepcopy(values),
                active_ids=list(self.context.get("active_ids", [])),
                new_move_ids=Records(self.env, "account.move"),
            )
            return Records(self.env, self.name, [wizard])
        if self.name == "account.payment.register":
            wizard = self.env.new_record(
                self.name,
                **copy.deepcopy(values),
                active_ids=list(self.context.get("active_ids", [])),
            )
            return Records(self.env, self.name, [wizard])
        if self.name == "account.bank.statement.line":
            return self.env.create_bank_statement_line(values)
        if self.name == "account.asset":
            return self.env.create_asset(values)
        if self.name in {
            "res.currency.rate",
            "account.group",
            "account.reconcile.model",
            "account.account.tag",
            "account.tax.group",
            "account.cash.rounding",
            "account.fiscal.year",
            "account.analytic.applicability",
            "account.analytic.distribution.model",
        }:
            return self.env.create_reference_record(self.name, values)
        raise AssertionError(f"unexpected create: {self.name}")

    def sudo(self, *args: Any, **kwargs: Any):
        raise AssertionError(f"core writes must never sudo {self.name}")


class Registry:
    def __init__(self, env: Env) -> None:
        self.env = env

    def get(self, model: str):
        self.env.calls.append(("registry", model))
        return None if model == self.env.missing_model else self.env.models.get(model)


class User:
    def __init__(self, env: Env) -> None:
        self.env = env

    def has_group(self, group: str) -> bool:
        self.env.calls.append(("group", group))
        return group != self.env.denied_group


class Env:
    uid = 42

    def __init__(self) -> None:
        self.calls: list[tuple[Any, ...]] = []
        self.missing_model: str | None = None
        self.denied_access: tuple[str, str] | None = None
        self.denied_group: str | None = None
        self.asset_validate_error: Exception | None = None
        model_names = set().union(*writes._MODELS.values())
        self.data: dict[str, list[Record]] = {name: [] for name in model_names}
        self.models = {name: Model(self, name) for name in model_names}
        self.registry = Registry(self)
        self.user = User(self)
        self._next_id = 1000
        self.company = self.add("res.company", 7, name="Fixture Company")
        self.company.root_id = Records(self, "res.company", [self.company])
        self.company.parent_id = Records(self, "res.company")
        self.country = self.add("res.country", 156, name="China")
        self.company.country_id = Records(self, "res.country", [self.country])
        self.company.account_fiscal_country_id = Records(self, "res.country", [self.country])
        self.partner = self.add(
            "res.partner", 20, name="Fixture Partner", company_id=False
        )
        self.partner.commercial_partner_id = Records(
            self, "res.partner", [self.partner]
        )
        self.currency = self.add(
            "res.currency", 1, name="USD", active=True, rounding=Decimal("0.01")
        )
        self.foreign_currency = self.add(
            "res.currency", 2, name="EUR", active=True, rounding=Decimal("0.01")
        )
        self.company.currency_id = Records(self, "res.currency", [self.currency])
        self.sale_journal = self.add(
            "account.journal", 10, name="Sales", company_id=self.company, type="sale"
        )
        self.purchase_journal = self.add(
            "account.journal",
            11,
            name="Purchases",
            company_id=self.company,
            type="purchase",
        )
        self.general_journal = self.add(
            "account.journal",
            12,
            name="Miscellaneous",
            company_id=self.company,
            type="general",
        )
        self.bank_journal = self.add(
            "account.journal",
            14,
            name="Bank",
            company_id=self.company,
            type="bank",
            currency_id=False,
        )
        self.income = self.account(101, reconcile=False, account_type="income")
        self.expense = self.account(102, reconcile=False, account_type="expense")
        self.receivable = self.account(
            301, reconcile=True, account_type="asset_receivable"
        )
        self.tax = self.add(
            "account.tax",
            31,
            name="Tax",
            company_id=self.company,
            active=True,
            invoice_repartition_line_ids=Records(
                self, "account.tax.repartition.line"
            ),
            refund_repartition_line_ids=Records(
                self, "account.tax.repartition.line"
            ),
            repartition_line_ids=Records(self, "account.tax.repartition.line"),
        )
        self.tax_tag = self.add(
            "account.account.tag", 71, name="VAT", applicability="taxes", color=0,
            country_id=Records(self, "res.country", [self.country]), active=True,
        )
        self.product_category = self.add("product.category", 40, name="Services")
        self.product = self.add(
            "product.product",
            41,
            name="Service",
            company_id=False,
            categ_id=Records(self, "product.category", [self.product_category]),
        )
        self.partner_category = self.add(
            "res.partner.category", 21, name="Preferred"
        )
        self.payment_term = self.add(
            "account.payment.term", 51, name="Net 30", company_id=False
        )
        self.analytic_plan = self.add(
            "account.analytic.plan",
            60,
            name="Projects",
            parent_id=False,
        )
        self.analytic_plan.root_id = Records(
            self, "account.analytic.plan", [self.analytic_plan]
        )
        self.analytic = self.add(
            "account.analytic.account",
            61,
            name="Project",
            company_id=self.company,
            plan_id=Records(self, "account.analytic.plan", [self.analytic_plan]),
            root_plan_id=Records(
                self, "account.analytic.plan", [self.analytic_plan]
            ),
        )
        self.analytic_two = self.add(
            "account.analytic.account",
            63,
            name="Department",
            company_id=self.company,
            plan_id=Records(self, "account.analytic.plan", [self.analytic_plan]),
            root_plan_id=Records(
                self, "account.analytic.plan", [self.analytic_plan]
            ),
        )

    def __getitem__(self, model: str) -> Model:
        self.calls.append(("model", model))
        return self.models[model]

    def add(self, model: str, record_id: int, **values: Any) -> Record:
        record = Record(model, record_id, **values)
        self.data[model].append(record)
        return record

    def new_record(self, model: str, **values: Any) -> Record:
        self._next_id += 1
        return self.add(model, self._next_id, **values)

    def account(
        self, record_id: int, *, reconcile: bool, account_type: str = "asset_current"
    ) -> Record:
        return self.add(
            "account.account",
            record_id,
            name=f"Account {record_id}",
            company_ids=Records(self, "res.company", [self.company]),
            reconcile=reconcile,
            account_type=account_type,
            active=True,
        )

    def relation_from_commands(
        self, model: str, commands: list[tuple[Any, ...]]
    ) -> Records:
        assert len(commands) == 1 and commands[0][0] == 6
        return self.models[model].browse(commands[0][2])

    def create_reference_record(
        self, model: str, values: dict[str, Any]
    ) -> Records:
        stored = copy.deepcopy(values)
        company_id = stored.pop("company_id", None)
        if company_id is not None:
            stored["company_id"] = self.models["res.company"].browse(company_id)
        if model == "res.currency.rate":
            stored["currency_id"] = self.models["res.currency"].browse(
                stored["currency_id"]
            )
        elif model == "account.fiscal.year":
            pass
        elif model == "account.group":
            stored["parent_id"] = Records(self, "account.group")
        elif model in {"account.account.tag", "account.tax.group"}:
            country_id = stored.pop("country_id")
            stored["country_id"] = self.models["res.country"].browse(country_id if isinstance(country_id, int) else [])
        elif model == "account.cash.rounding":
            for field in ("profit_account_id", "loss_account_id"):
                record_id = stored[field]
                stored[field] = self.models["account.account"].browse(record_id if isinstance(record_id, int) else [])
        elif model == "account.analytic.applicability":
            for field, relation_model in (
                ("analytic_plan_id", "account.analytic.plan"),
                ("product_categ_id", "product.category"),
            ):
                record_id = stored[field]
                stored[field] = self.models[relation_model].browse(
                    record_id if isinstance(record_id, int) else []
                )
        elif model == "account.analytic.distribution.model":
            for field, relation_model in (
                ("partner_id", "res.partner"),
                ("partner_category_id", "res.partner.category"),
                ("product_id", "product.product"),
                ("product_categ_id", "product.category"),
            ):
                record_id = stored[field]
                stored[field] = self.models[relation_model].browse(
                    record_id if isinstance(record_id, int) else []
                )
        else:
            for field, relation_model in (
                ("match_journal_ids", "account.journal"),
                ("match_partner_ids", "res.partner"),
            ):
                stored[field] = self.relation_from_commands(
                    relation_model, stored[field]
                )
            stored["line_ids"] = Records(self, "account.reconcile.model.line")
        record = self.new_record(model, **stored)
        return Records(self, model, [record])

    def tax_repartition_lines_from_commands(
        self,
        tax: Record,
        commands: list[tuple[Any, ...]],
        *,
        document_type: str | None,
    ) -> Records:
        lines: list[Record] = []
        for command, _unused, values in commands:
            if command == 5:
                lines.clear()
                continue
            assert command == 0
            stored = copy.deepcopy(values)
            line_document_type = stored.pop("document_type", document_type)
            assert line_document_type in {"invoice", "refund"}
            account_id = stored["account_id"]
            stored["account_id"] = self.models["account.account"].browse(
                account_id if isinstance(account_id, int) else []
            )
            stored["tag_ids"] = self.relation_from_commands(
                "account.account.tag", stored["tag_ids"]
            )
            lines.append(
                self.new_record(
                    "account.tax.repartition.line",
                    **stored,
                    tax_id=Records(self, "account.tax", [tax]),
                    company_id=tax.company_id,
                    document_type=line_document_type,
                )
            )
        return Records(self, "account.tax.repartition.line", lines)

    def reconciliation_lines_from_commands(
        self, model: Record, commands: list[tuple[Any, ...]]
    ) -> Records:
        lines: list[Record] = []
        for command, _unused, values in commands:
            if command == 5:
                lines.clear()
                continue
            assert command == 0
            stored = copy.deepcopy(values)
            for field, relation_model in (
                ("account_id", "account.account"),
                ("partner_id", "res.partner"),
            ):
                record_id = stored[field]
                stored[field] = self.models[relation_model].browse(
                    record_id if isinstance(record_id, int) else []
                )
            stored["tax_ids"] = self.relation_from_commands(
                "account.tax", stored["tax_ids"]
            )
            stored.setdefault("analytic_distribution", False)
            lines.append(
                self.new_record(
                    "account.reconcile.model.line",
                    **stored,
                    model_id=Records(self, "account.reconcile.model", [model]),
                    company_id=model.company_id,
                )
            )
        return Records(self, "account.reconcile.model.line", lines)

    def move_lines_from_commands(self, commands: list[tuple[Any, ...]]) -> Records:
        lines: list[Record] = []
        for command, _unused, line_values in commands:
            if command == 5:
                lines.clear()
                continue
            assert command == 0
            stored = copy.deepcopy(line_values)
            stored["account_id"] = self.models["account.account"].browse(
                line_values["account_id"]
            )
            partner_id = line_values.get("partner_id")
            stored["partner_id"] = self.models["res.partner"].browse(
                partner_id if isinstance(partner_id, int) else []
            )
            product_id = line_values.get("product_id")
            stored["product_id"] = self.models["product.product"].browse(
                product_id if isinstance(product_id, int) else []
            )
            tax_commands = line_values.get("tax_ids", [])
            tax_ids = tax_commands[0][2] if tax_commands else []
            stored["tax_ids"] = self.models["account.tax"].browse(tax_ids)
            currency_id = line_values.get("currency_id") or self.currency.id
            stored["currency_id"] = self.models["res.currency"].browse(currency_id)
            stored.setdefault(
                "amount_currency",
                Decimal(str(line_values.get("debit", 0)))
                - Decimal(str(line_values.get("credit", 0))),
            )
            stored.setdefault("analytic_distribution", {})
            stored.setdefault("sequence", (len(lines) + 1) * 10)
            stored.setdefault("display_type", False)
            stored.setdefault("quantity", Decimal(0))
            stored.setdefault("price_unit", Decimal(0))
            stored.setdefault("discount", Decimal(0))
            line = self.new_record(
                "account.move.line",
                **stored,
                company_id=self.company,
                parent_state="draft",
                amount_residual=Decimal(0),
                reconciled=False,
                matched_debit_ids=Records(self, "account.partial.reconcile"),
                matched_credit_ids=Records(self, "account.partial.reconcile"),
                full_reconcile_id=Records(self, "account.full.reconcile"),
            )
            lines.append(line)
        return Records(self, "account.move.line", lines)

    def create_move(self, values: dict[str, Any]) -> Records:
        line_commands = values.get("invoice_line_ids", values.get("line_ids", []))
        lines = self.move_lines_from_commands(line_commands)
        stored_move_values = copy.deepcopy(values)
        stored_move_values.pop("company_id", None)
        stored_move_values.pop("invoice_line_ids", None)
        stored_move_values.pop("line_ids", None)
        for field_name, model_name in (
            ("partner_id", "res.partner"),
            ("journal_id", "account.journal"),
            ("currency_id", "res.currency"),
            ("invoice_payment_term_id", "account.payment.term"),
        ):
            value = stored_move_values.get(field_name)
            if isinstance(value, int):
                stored_move_values[field_name] = self.models[model_name].browse(value)
        is_invoice = values["move_type"] != "entry"
        ref = stored_move_values.pop("ref", False)
        payment_reference = stored_move_values.pop("payment_reference", False)
        invoice_date_due = stored_move_values.pop("invoice_date_due", False)
        payment_term = stored_move_values.pop(
            "invoice_payment_term_id", Records(self, "account.payment.term")
        )
        partner = stored_move_values.pop("partner_id", Records(self, "res.partner"))
        currency = stored_move_values.pop(
            "currency_id", Records(self, "res.currency", [self.currency])
        )
        move = self.new_record(
            "account.move",
            **stored_move_values,
            name="/",
            state="draft",
            company_id=self.company,
            ref=ref,
            payment_reference=payment_reference,
            invoice_date_due=invoice_date_due,
            invoice_payment_term_id=payment_term,
            partner_id=partner,
            currency_id=currency,
            line_ids=lines,
            invoice_line_ids=(
                lines if is_invoice else Records(self, "account.move.line")
            ),
            reversed_entry_id=Records(self, "account.move"),
            amount_residual=Decimal(100),
            invoice_outstanding_credits_debits_widget=False,
        )
        return Records(self, "account.move", [move])

    def existing_move(
        self,
        record_id: int,
        *,
        move_type: str,
        state: str = "posted",
        residual: str = "100",
    ) -> Record:
        journal = {
            "out_invoice": self.sale_journal,
            "out_refund": self.sale_journal,
            "in_invoice": self.purchase_journal,
            "in_refund": self.purchase_journal,
        }.get(move_type, self.general_journal)
        return self.add(
            "account.move",
            record_id,
            name=f"MOVE/{record_id}",
            move_type=move_type,
            state=state,
            company_id=self.company,
            journal_id=Records(self, "account.journal", [journal]),
            partner_id=Records(self, "res.partner", [self.partner]),
            currency_id=Records(self, "res.currency", [self.currency]),
            ref=False,
            payment_reference=False,
            invoice_date_due=False,
            invoice_payment_term_id=Records(self, "account.payment.term"),
            narration=False,
            invoice_origin=False,
            line_ids=Records(self, "account.move.line"),
            invoice_line_ids=Records(self, "account.move.line"),
            reversed_entry_id=Records(self, "account.move"),
            amount_residual=Decimal(residual),
            invoice_outstanding_credits_debits_widget=False,
        )

    def reverse(self, wizard: Records, *, refund: bool) -> dict[str, Any]:
        source_id = wizard.active_ids[0]
        source = self.models["account.move"].browse(source_id)
        reversal_type = {
            "out_invoice": "out_refund",
            "in_invoice": "in_refund",
        }.get(source.move_type, "entry")
        reversal_state = "draft" if refund else "posted"
        reversal = self.add(
            "account.move",
            self._next_id + 1,
            name=f"REV/{source_id}",
            move_type=reversal_type,
            state=reversal_state,
            company_id=self.company,
            journal_id=self.models["account.journal"].browse(wizard.journal_id),
            partner_id=source.partner_id,
            currency_id=source.currency_id,
            ref=False,
            payment_reference=False,
            invoice_date_due=False,
            invoice_payment_term_id=Records(self, "account.payment.term"),
            narration=False,
            invoice_origin=False,
            line_ids=Records(self, "account.move.line"),
            invoice_line_ids=Records(self, "account.move.line"),
            reversed_entry_id=source,
            amount_residual=Decimal(0),
            invoice_outstanding_credits_debits_widget=False,
        )
        self._next_id = reversal.id
        wizard.records[0].new_move_ids = Records(self, "account.move", [reversal])
        if not refund:
            source.records[0].state = "cancel"
        method = "refund_moves" if refund else "reverse_moves"
        self.calls.append((method, source_id, wizard.date, wizard.reason))
        return {"res_id": reversal.id}

    def create_bank_statement_line(self, values: dict[str, Any]) -> Records:
        journal = self.models["account.journal"].browse(values["journal_id"])
        partner = self.models["res.partner"].browse(values["partner_id"])
        lines = [
            self.new_record(
                "account.move.line",
                company_id=self.company,
                parent_state="posted",
                amount_residual=Decimal(0),
                reconciled=False,
                matched_debit_ids=Records(self, "account.partial.reconcile"),
                matched_credit_ids=Records(self, "account.partial.reconcile"),
                full_reconcile_id=Records(self, "account.full.reconcile"),
            )
            for _unused in range(2)
        ]
        move = self.add(
            "account.move",
            self._next_id + 1,
            name=f"BNK/{self._next_id + 1}",
            move_type="entry",
            state="posted",
            company_id=self.company,
            journal_id=journal,
            ref=values["ref"],
            narration=False,
            invoice_origin=values["invoice_origin"],
            line_ids=Records(self, "account.move.line", lines),
            reversed_entry_id=Records(self, "account.move"),
            amount_residual=Decimal(0),
        )
        self._next_id = move.id
        statement_line = self.add(
            "account.bank.statement.line",
            self._next_id + 1,
            move_id=Records(self, "account.move", [move]),
            company_id=self.company,
            journal_id=journal,
            date=values["date"],
            amount=values["amount"],
            payment_ref=values["payment_ref"],
            partner_id=partner,
            ref=values["ref"],
            invoice_origin=values["invoice_origin"],
            state="posted",
            is_reconciled=False,
        )
        self._next_id = statement_line.id
        self.calls.append(("bank_auto_post", statement_line.id))
        return Records(self, "account.bank.statement.line", [statement_line])

    def create_asset(self, values: dict[str, Any]) -> Records:
        stored = copy.deepcopy(values)
        stored["company_id"] = self.models["res.company"].browse(values["company_id"])
        for field_name, model_name in (
            ("account_asset_id", "account.account"),
            ("account_depreciation_id", "account.account"),
            ("account_depreciation_expense_id", "account.account"),
            ("journal_id", "account.journal"),
        ):
            stored[field_name] = self.models[model_name].browse(values[field_name])
        asset = self.new_record(
            "account.asset",
            **stored,
            state="draft",
            depreciation_move_ids=Records(self, "account.move"),
        )
        return Records(self, "account.asset", [asset])

    def existing_asset(self, record_id: int, *, state: str = "draft") -> Record:
        return self.add(
            "account.asset",
            record_id,
            name=f"Fixture asset {record_id}",
            state=state,
            company_id=Records(self, "res.company", [self.company]),
            depreciation_move_ids=Records(self, "account.move"),
        )

    def register_payment(self, wizard: Records) -> dict[str, Any]:
        source = self.models["account.move"].browse(wizard.active_ids[0])
        payment_move = self.existing_move(
            self._next_id + 1, move_type="entry", state="posted", residual="0"
        )
        self._next_id = payment_move.id
        is_invoice = source.move_type in {"out_invoice", "out_refund"}
        amount = Decimal(
            str(getattr(wizard.records[0], "amount", False) or source.amount_residual)
        )
        payment = self.add(
            "account.payment",
            self._next_id + 1,
            name=f"PAY/{source.id}",
            state="in_process",
            company_id=self.company,
            memo=wizard.communication,
            journal_id=self.models["account.journal"].browse(wizard.journal_id),
            date=wizard.payment_date,
            amount=amount,
            payment_type="inbound"
            if source.move_type in {"out_invoice", "in_refund"}
            else "outbound",
            partner_type="customer" if is_invoice else "supplier",
            move_id=Records(self, "account.move", [payment_move]),
            reconciled_invoice_ids=source
            if is_invoice
            else Records(self, "account.move"),
            reconciled_bill_ids=source
            if not is_invoice
            else Records(self, "account.move"),
            is_reconciled=amount == source.amount_residual,
        )
        self._next_id = payment.id
        source.records[0].amount_residual -= amount
        self.calls.append(
            (
                "action_create_payments",
                source.id,
                wizard.journal_id,
                wizard.payment_date,
                wizard.communication,
            )
        )
        return {"res_id": payment.id}

    def reconciliation_line(
        self,
        record_id: int,
        residual: str,
        *,
        account: Record | None = None,
        partner: Record | None = None,
    ) -> Record:
        return self.add(
            "account.move.line",
            record_id,
            company_id=self.company,
            account_id=Records(self, "account.account", [account or self.receivable]),
            partner_id=Records(self, "res.partner", [partner or self.partner]),
            parent_state="posted",
            amount_residual=Decimal(residual),
            reconciled=False,
            matched_debit_ids=Records(self, "account.partial.reconcile"),
            matched_credit_ids=Records(self, "account.partial.reconcile"),
            full_reconcile_id=Records(self, "account.full.reconcile"),
        )

    def reconcile(self, lines: Records) -> None:
        positive, negative = sorted(
            lines.records, key=lambda line: line.amount_residual
        )
        if positive.amount_residual < 0:
            positive, negative = negative, positive
        partial = self.new_record(
            "account.partial.reconcile",
            debit_move_id=positive,
            credit_move_id=negative,
            company_id=self.company,
            full_reconcile_id=Records(self, "account.full.reconcile"),
        )
        partials = Records(self, "account.partial.reconcile", [partial])
        positive.matched_credit_ids |= partials
        negative.matched_debit_ids |= partials
        amount = min(positive.amount_residual, -negative.amount_residual)
        positive.amount_residual -= amount
        negative.amount_residual += amount
        for line in (positive, negative):
            line.reconciled = line.amount_residual == 0
        if positive.reconciled and negative.reconciled:
            graph_partials = (
                positive.matched_debit_ids
                | positive.matched_credit_ids
                | negative.matched_debit_ids
                | negative.matched_credit_ids
            )
            graph_lines = graph_partials.debit_move_id | graph_partials.credit_move_id
            full = self.new_record(
                "account.full.reconcile",
                reconciled_line_ids=graph_lines,
                partial_reconcile_ids=graph_partials,
            )
            full_records = Records(self, "account.full.reconcile", [full])
            for line in graph_lines:
                line.full_reconcile_id = full_records
            for graph_partial in graph_partials:
                graph_partial.full_reconcile_id = full_records
        self.calls.append(("reconcile", tuple(sorted(lines.ids))))

    def assign_outstanding(self, invoice: Records, line_id: int) -> None:
        counterpart = self.models["account.move.line"].browse(line_id)
        invoice_lines = invoice.line_ids.filtered(
            lambda line: (
                line.account_id.id == counterpart.account_id.id
                and line.amount_residual != 0
            )
        )
        assert invoice_lines
        self.calls.append(("js_assign_outstanding_line", invoice.id, line_id))
        for invoice_line in invoice_lines:
            if counterpart.amount_residual == 0:
                break
            self.reconcile(
                Records(self, "account.move.line", [invoice_line]) | counterpart
            )

    def remove_outstanding(self, invoice: Records, partial_id: int) -> None:
        partial = self.models["account.partial.reconcile"].browse(partial_id)
        self.calls.append(("js_remove_outstanding_partial", invoice.id, partial_id))
        self.unlink_partial(partial)

    def unlink_partial(self, partials: Records) -> bool:
        self.calls.append(("unlink_partial", tuple(partials.ids)))
        fulls = partials.full_reconcile_id
        removed = set(partials.ids)
        for line in fulls.reconciled_line_ids:
            line.full_reconcile_id = Records(self, "account.full.reconcile")
            line.reconciled = False
        for graph_partial in fulls.partial_reconcile_ids:
            graph_partial.full_reconcile_id = Records(self, "account.full.reconcile")
        for partial in partials:
            for line in (partial.debit_move_id, partial.credit_move_id):
                line.matched_debit_ids = line.matched_debit_ids.filtered(
                    lambda row: row.id not in removed
                )
                line.matched_credit_ids = line.matched_credit_ids.filtered(
                    lambda row: row.id not in removed
                )
                line.reconciled = False
                if line.full_reconcile_id & fulls:
                    line.full_reconcile_id = Records(self, "account.full.reconcile")
        self.data["account.partial.reconcile"] = [
            row
            for row in self.data["account.partial.reconcile"]
            if row.id not in removed
        ]
        removed_fulls = set(fulls.ids)
        self.data["account.full.reconcile"] = [
            row
            for row in self.data["account.full.reconcile"]
            if row.id not in removed_fulls
        ]
        return True


def _payload(
    capability_id: str,
    parameters: dict[str, Any],
    *,
    key: str = "write-key-1",
) -> dict[str, Any]:
    return {
        "capability_id": capability_id,
        "company_id": 7,
        "idempotency_key": key,
        "confirmation": capability_id,
        "parameters": parameters,
    }


def _document_parameters(env: Env, capability_id: str) -> dict[str, Any]:
    sale = capability_id == "customer_invoice.create"
    return {
        "partner_id": env.partner.id,
        "journal_id": env.sale_journal.id if sale else env.purchase_journal.id,
        "invoice_date": "2025-02-01",
        "currency_id": env.currency.id,
        "lines": [
            {
                "name": "Consulting",
                "account_id": env.income.id if sale else env.expense.id,
                "quantity": "2.00",
                "price_unit": "50.00",
                "tax_ids": [env.tax.id],
            }
        ],
    }


def _entry_parameters(env: Env) -> dict[str, Any]:
    return {
        "journal_id": env.general_journal.id,
        "date": "2025-02-02",
        "lines": [
            {
                "name": "Debit",
                "account_id": env.expense.id,
                "partner_id": None,
                "debit": "25.00",
                "credit": "0",
            },
            {
                "name": "Credit",
                "account_id": env.income.id,
                "partner_id": env.partner.id,
                "debit": "0",
                "credit": "25.00",
            },
        ],
    }


def _replacement_invoice_lines(env: Env) -> list[dict[str, Any]]:
    return [
        {
            "name": "Adjusted service",
            "product_id": env.product.id,
            "account_id": env.income.id,
            "quantity": "1",
            "price_unit": "75",
            "discount": "5",
            "tax_ids": [env.tax.id],
            "analytic_distribution": {str(env.analytic.id): "100"},
        }
    ]


def _invoice_widget_fixture(
    env: Env, *, invoice_id: int = 700, term_residuals: tuple[str, ...] = ("100",)
) -> tuple[Record, list[Record], Record]:
    invoice = env.existing_move(
        invoice_id, move_type="out_invoice", state="posted", residual="100"
    )
    term_lines = [
        env.reconciliation_line(invoice_id + index + 1, residual)
        for index, residual in enumerate(term_residuals)
    ]
    counterpart = env.reconciliation_line(
        invoice_id + len(term_lines) + 1,
        str(-sum(Decimal(value) for value in term_residuals)),
    )
    invoice.line_ids = Records(env, "account.move.line", term_lines)
    invoice.invoice_outstanding_credits_debits_widget = {
        "content": [{"id": counterpart.id}]
    }
    return invoice, term_lines, counterpart


def _asset_parameters(env: Env) -> dict[str, Any]:
    return {
        "name": "Office laptop",
        "acquisition_date": "2025-01-01",
        "original_value": "120.00",
        "salvage_value": "0",
        "account_asset_id": env.income.id,
        "account_depreciation_id": env.receivable.id,
        "account_depreciation_expense_id": env.expense.id,
        "journal_id": env.general_journal.id,
        "method": "linear",
        "method_number": 1,
        "method_period": "12",
        "method_progress_factor": "0.30",
        "prorata_computation_type": "none",
    }


def test_public_action_and_closed_capability_batch_are_exact() -> None:
    assert writes.ACTION == "accounting.core_write.execute"
    assert writes.CAPABILITIES == {
        "customer_invoice.create",
        "vendor_bill.create",
        "invoice.update",
        "invoice.lines.replace",
        "invoice.cancel",
        "invoice.reset_to_draft",
        "invoice.post",
        "invoice.duplicate",
        "invoice.type.switch",
        "journal_entry.create",
        "journal_entry.update",
        "journal_entry.lines.replace",
        "journal_entry.cancel",
        "journal_entry.reset_to_draft",
        "journal_entry.post",
        "journal_entry.reverse",
        "receivable.payment.register",
        "payable.payment.register",
        "reconciliation.apply",
        "payment.cancel",
        "payment.create",
        "payment.update_draft",
        "payment.reset_to_draft",
        "customer_credit_note.create",
        "vendor_refund.create",
        "payment.post",
        "reconciliation.undo",
        "bank.transaction.record",
        "bank.transaction.update",
        "bank.transaction.match",
        "bank.transaction.unmatch",
        "reconciliation.write_off",
        "analytic.plan.create",
        "analytic.plan.update",
        "analytic.account.create",
        "analytic.account.update",
        "analytic.account.archive",
        "analytic.account.restore",
        "analytic.line.create",
        "analytic.line.update",
        "analytic.line.delete",
        "budget.create",
        "budget.update_draft",
        "budget.lines.replace",
        "budget.confirm",
        "budget.reset_to_draft",
        "budget.cancel",
        "budget.mark_done",
        "partner.create",
        "partner.update",
        "partner.archive",
        "partner.restore",
        "partner.accounting.update",
        "partner.bank_account.create",
        "partner.bank_account.update",
        "partner.bank_account.archive",
        "partner.bank_account.restore",
        "account.account.create",
        "account.account.update",
        "account.account.archive",
        "account.account.restore",
        "journal.create",
        "journal.update",
        "journal.archive",
        "journal.restore",
        "tax.create",
        "tax.update",
        "tax.archive",
        "tax.restore",
        "asset.create",
        "asset.validate",
        "asset.cancel",
        "asset.dispose",
        "asset.pause",
        "deferred_expense.generate_entries",
        "deferred_revenue.generate_entries",
        "multicurrency.revaluation.generate_entries",
        "reconciliation.automatic.run",
        "period.transfer.run",
        "localization.china.period_transfer.run",
        "sale.order.create",
        "sale.order.update_draft",
        "sale.order.lines.replace",
        "sale.order.confirm",
        "sale.order.cancel",
        "sale.order.reset_to_draft",
        "purchase.order.create",
        "purchase.order.update_draft",
        "purchase.order.lines.replace",
        "purchase.order.confirm",
        "purchase.order.cancel",
        "purchase.order.reset_to_draft",
        "purchase.order.bill.create",
        "purchase_bill.match",
        "purchase_bill.lines.unmatch",
        "payment_term.create",
        "payment_term.update",
        "payment_term.lines.replace",
        "payment_term.archive",
        "payment_term.restore",
        "period.accrual.generate",
        "fiscal_position.create",
        "fiscal_position.update",
        "fiscal_position.account_mappings.replace",
        "fiscal_position.archive",
        "fiscal_position.restore",
        "journal.group.create",
        "journal.group.update",
        "currency.rate.record",
        "account.group.create",
        "account.group.update",
        "tax.repartition_lines.replace",
        "reconciliation.model.create",
        "reconciliation.model.update",
        "reconciliation.model.lines.replace",
        "reconciliation.model.archive",
        "reconciliation.model.restore",
        "account.tag.create",
        "account.tag.update",
        "account.tag.archive",
        "account.tag.restore",
        "tax.group.create",
        "tax.group.update",
        "cash_rounding.create",
        "cash_rounding.update",
        "fiscal_year.create",
        "fiscal_year.update",
        "analytic.applicability.create",
        "analytic.applicability.update",
        "analytic.distribution_model.create",
        "analytic.distribution_model.update",
        "sale.order.invoice.create",
        "stock.transfer.create",
        "stock.transfer.confirm",
        "stock.transfer.assign",
        "stock.transfer.quantities.set",
        "stock.transfer.validate",
        "stock.transfer.unreserve",
        "stock.transfer.cancel",
        "account.return.create",
        "account.return.checks.refresh",
        "account.return.check.result.update",
        "account.return.validate",
        "account.return.mark_submitted",
        "account.return.archive",
        "account.return.restore",
        "account.return.delete",
    }


def test_optional_references_do_not_expand_static_access_gate() -> None:
    forbidden_by_capability = {
        "customer_invoice.create": {
            ("product.product", "read"),
            ("account.payment.term", "read"),
            ("account.analytic.account", "read"),
        },
        "vendor_bill.create": {
            ("product.product", "read"),
            ("account.payment.term", "read"),
            ("account.analytic.account", "read"),
        },
        "invoice.lines.replace": {("account.analytic.account", "read")},
        "journal_entry.create": {
            ("res.currency", "read"),
            ("account.analytic.account", "read"),
        },
        "journal_entry.lines.replace": {
            ("res.currency", "read"),
            ("account.analytic.account", "read"),
        },
        "customer_credit_note.create": {
            ("product.product", "read"),
            ("account.analytic.account", "read"),
            ("account.analytic.line", "create"),
        },
        "vendor_refund.create": {
            ("product.product", "read"),
            ("account.analytic.account", "read"),
            ("account.analytic.line", "create"),
        },
    }
    analytic_lifecycle_access = {
        ("account.analytic.account", "read"),
        ("account.analytic.line", "read"),
        ("account.analytic.line", "create"),
        ("account.analytic.line", "unlink"),
    }
    for capability_id in (
        "invoice.post",
        "invoice.cancel",
        "invoice.reset_to_draft",
        "journal_entry.post",
        "journal_entry.cancel",
        "journal_entry.reset_to_draft",
        "journal_entry.reverse",
    ):
        forbidden_by_capability[capability_id] = analytic_lifecycle_access
    for capability_id, forbidden in forbidden_by_capability.items():
        assert not forbidden & writes._ACCESS[capability_id]
    assert ("account.move.line", "read") in writes._ACCESS["invoice.post"]
    assert ("account.move.line", "create") in writes._ACCESS["journal_entry.reverse"]


@pytest.mark.parametrize(
    "capability_id",
    [
        "journal_entry.post",
        "journal_entry.cancel",
        "journal_entry.reset_to_draft",
    ],
)
def test_batch_journal_lifecycle_rejects_non_general_journals_before_actions(
    monkeypatch: pytest.MonkeyPatch, capability_id: str
) -> None:
    moves = [
        Record(
            "account.move",
            31,
            journal_id=Record("account.journal", 41, type="general"),
        ),
        Record(
            "account.move",
            32,
            journal_id=Record("account.journal", 42, type="bank"),
        ),
    ]
    monkeypatch.setattr(writes, "_ensure_ids", lambda *_args, **_kwargs: moves)

    with pytest.raises(Failure) as raised:
        writes._batch_lifecycle_moves(object(), capability_id, [31, 32], 7, Failure)

    assert raised.value.code == "record_not_found"


def test_asset_create_uses_a_visible_marker_and_replays_only_full_fingerprint() -> None:
    env = Env()
    parameters = _asset_parameters(env)
    key = "asset-create-key-1"
    payload = _payload("asset.create", parameters, key=key)

    first = writes.dispatch(env, payload, 7, Failure)
    second = writes.dispatch(env, payload, 7, Failure)

    suffix = writes._asset_marker_suffix(7, key)
    assert first["idempotent_replay"] is False
    assert second["idempotent_replay"] is True
    assert first["result"] == second["result"]
    assert first["result"]["model"] == "account.asset"
    assert first["result"]["name"] == f"Office laptop {suffix}"
    assert first["result"]["state"] == "draft"
    assert first["result"]["line_ids"] == []
    creates = [call for call in env.calls if call[:2] == ("create", "account.asset")]
    assert len(creates) == 1
    assert creates[0][2]["name"] == f"Office laptop {suffix}"
    assert creates[0][2]["original_value"] == Decimal("120.00")
    assert creates[0][2]["method_progress_factor"] == Decimal("0.30")

    changed = copy.deepcopy(payload)
    changed["parameters"]["name"] = "Different laptop"
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, changed, 7, Failure)
    assert caught.value.code == "idempotency_conflict"


def test_asset_validate_calls_public_method_and_replays_open_state() -> None:
    env = Env()
    asset = env.existing_asset(601)
    payload = _payload(
        "asset.validate",
        {"asset_id": asset.id},
        key=f"asset.validate:{asset.id}",
    )

    first = writes.dispatch(env, payload, 7, Failure)
    second = writes.dispatch(env, payload, 7, Failure)

    assert first["idempotent_replay"] is False
    assert second["idempotent_replay"] is True
    assert first["result"]["model"] == "account.asset"
    assert first["result"]["id"] == asset.id
    assert first["result"]["state"] == "open"
    assert first["result"]["line_ids"]
    assert [call[0] for call in env.calls].count("validate_asset") == 1

    closed = Env()
    closed_asset = closed.existing_asset(602, state="close")
    with pytest.raises(Failure) as caught:
        writes.dispatch(
            closed,
            _payload(
                "asset.validate",
                {"asset_id": closed_asset.id},
                key=f"asset.validate:{closed_asset.id}",
            ),
            7,
            Failure,
        )
    assert caught.value.code == "state_conflict"


def test_asset_validate_normalizes_third_party_singleton_failure() -> None:
    env = Env()
    asset = env.existing_asset(603)
    env.asset_validate_error = ValueError("Expected singleton: account.move(1, 2)")

    with pytest.raises(Failure) as caught:
        writes.dispatch(
            env,
            _payload(
                "asset.validate",
                {"asset_id": asset.id},
                key=f"asset.validate:{asset.id}",
            ),
            7,
            Failure,
        )

    assert caught.value.code == "odoo_write_error"
    assert caught.value.exit_code == 6
    assert isinstance(caught.value.__cause__, ValueError)
    assert ("validate_asset", (asset.id,)) in env.calls


@pytest.mark.parametrize(
    "capability_id", ["customer_invoice.create", "vendor_bill.create"]
)
@pytest.mark.parametrize("accounting_date", [None, "2025-03-01"])
def test_document_create_uses_business_orm_and_replays_exact_key(
    capability_id: str,
    accounting_date: str | None,
) -> None:
    env = Env()
    parameters = _document_parameters(env, capability_id)
    if accounting_date is not None:
        parameters["date"] = accounting_date
    payload = _payload(capability_id, parameters, key=f"key-{capability_id}")

    first = writes.dispatch(env, payload, 7, Failure)
    second = writes.dispatch(env, payload, 7, Failure)

    assert first["idempotent_replay"] is False
    assert second["idempotent_replay"] is True
    assert first["result"]["move_type"] == (
        "out_invoice" if capability_id == "customer_invoice.create" else "in_invoice"
    )
    creates = [call for call in env.calls if call[:2] == ("create", "account.move")]
    assert len(creates) == 1
    values = creates[0][2]
    assert "ref" not in values
    assert values.get("date") == accounting_date
    assert ("date" in values) == (accounting_date is not None)
    assert values["invoice_date"] == "2025-02-01"
    marker_tokens = values["invoice_origin"].split(";")
    assert marker_tokens[0] == writes._idempotency_key_marker(
        capability_id, 7, f"key-{capability_id}"
    )
    assert re.fullmatch(r"ODACV4:[0-9a-f]{64}", marker_tokens[1])
    assert values["invoice_line_ids"][0][2]["quantity"] == Decimal("2.00")
    assert values["invoice_line_ids"][0][2]["price_unit"] == Decimal("50.00")
    assert all(call[0] != "sudo" for call in env.calls)

    changed = copy.deepcopy(payload)
    changed["parameters"]["lines"][0]["price_unit"] = "51.00"
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, changed, 7, Failure)
    assert caught.value.code == "idempotency_conflict"

    changed_date = copy.deepcopy(payload)
    changed_date["parameters"]["date"] = "2025-03-02"
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, changed_date, 7, Failure)
    assert caught.value.code == "idempotency_conflict"


@pytest.mark.parametrize(
    "capability_id", ["customer_invoice.create", "vendor_bill.create"]
)
@pytest.mark.parametrize("prices", [("100", "-10"), ("-10.00",)])
def test_document_create_preserves_signed_prices_and_replays(
    capability_id: str, prices: tuple[str, ...]
) -> None:
    env = Env()
    parameters = _document_parameters(env, capability_id)
    template = parameters["lines"][0]
    parameters["lines"] = [
        {**template, "name": f"Line {index}", "quantity": "1", "price_unit": price}
        for index, price in enumerate(prices)
    ]
    payload = _payload(capability_id, parameters)

    first = writes.dispatch(env, payload, 7, Failure)
    replay = writes.dispatch(env, payload, 7, Failure)

    assert first["idempotent_replay"] is False
    assert replay["idempotent_replay"] is True
    assert first["result"] == replay["result"]
    creates = [call for call in env.calls if call[:2] == ("create", "account.move")]
    assert len(creates) == 1
    assert [line[2]["price_unit"] for line in creates[0][2]["invoice_line_ids"]] == [
        Decimal(price) for price in prices
    ]
    assert all(call[0] != "sudo" for call in env.calls)

    changed = copy.deepcopy(payload)
    changed["parameters"]["lines"][-1]["price_unit"] = "-11"
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, changed, 7, Failure)
    assert caught.value.code == "idempotency_conflict"
    assert sum(call[:2] == ("create", "account.move") for call in env.calls) == 1


@pytest.mark.parametrize(
    "capability_id", ["customer_invoice.create", "vendor_bill.create"]
)
@pytest.mark.parametrize(
    "invalid_line",
    [
        {"price_unit": "-01"},
        {"price_unit": -10},
        {"price_unit": "NaN"},
        {"quantity": "-1"},
        {"discount": "101"},
    ],
)
def test_document_create_signed_prices_keep_other_input_boundaries(
    capability_id: str, invalid_line: dict[str, Any]
) -> None:
    env = Env()
    parameters = _document_parameters(env, capability_id)
    parameters["lines"][0].update({"price_unit": "-10", **invalid_line})
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, _payload(capability_id, parameters), 7, Failure)
    assert caught.value.code == "bridge_protocol_error"
    assert env.calls == []


@pytest.mark.parametrize(
    "capability_id", ["customer_invoice.create", "vendor_bill.create", "invoice.update"]
)
@pytest.mark.parametrize("invalid_date", [None, False, "2025-02-29", "20250301"])
def test_invoice_accounting_date_is_validated_at_the_runtime_boundary(
    capability_id: str, invalid_date: Any
) -> None:
    parameters = (
        {"move_id": 610, "changes": {"date": invalid_date}}
        if capability_id == "invoice.update"
        else {**_document_parameters(Env(), capability_id), "date": invalid_date}
    )
    assert not writes._valid_parameters(capability_id, parameters)


@pytest.mark.parametrize(
    "move_type", ["out_invoice", "in_invoice", "out_refund", "in_refund"]
)
@pytest.mark.parametrize("change_invoice_date", [False, True])
def test_invoice_update_passes_accounting_dates_to_drafts_and_replays(
    move_type: str, change_invoice_date: bool
) -> None:
    env = Env()
    invoice = env.existing_move(610, move_type=move_type, state="draft")
    invoice.date = date(2025, 2, 1)
    invoice.invoice_date = date(2025, 2, 1)
    changes = {"date": "2025-03-01"}
    if change_invoice_date:
        changes["invoice_date"] = "2025-02-28"
    parameters = {"move_id": invoice.id, "changes": changes}
    key = writes._deterministic_key("invoice.update", parameters, 7)
    payload = _payload("invoice.update", parameters, key=key)

    assert not writes.dispatch(env, payload, 7, Failure)["idempotent_replay"]
    assert str(invoice.date) == changes["date"]
    assert str(invoice.invoice_date) == changes.get("invoice_date", "2025-02-01")
    assert writes.dispatch(env, payload, 7, Failure)["idempotent_replay"]
    assert [call[3] for call in env.calls if call[:2] == ("write", "account.move")] == [
        changes
    ]

    invoice.state = "posted"
    assert writes.dispatch(env, payload, 7, Failure)["idempotent_replay"]
    changed = {"move_id": invoice.id, "changes": {"date": "2025-03-02"}}
    with pytest.raises(Failure) as caught:
        writes.dispatch(
            env,
            _payload(
                "invoice.update",
                changed,
                key=writes._deterministic_key("invoice.update", changed, 7),
            ),
            7,
            Failure,
        )
    assert caught.value.code == "state_conflict"
    assert invoice.date == "2025-03-01"


@pytest.mark.parametrize(
    "move_type", ["out_invoice", "in_invoice", "out_refund", "in_refund"]
)
@pytest.mark.parametrize(
    "fields", [("journal_id",), ("currency_id",), ("journal_id", "currency_id")]
)
def test_invoice_update_writes_header_references_and_replays(
    move_type: str, fields: tuple[str, ...]
) -> None:
    env = Env()
    invoice = env.existing_move(610, move_type=move_type, state="draft")
    invoice.date = date(2025, 2, 1)
    journal_type = "sale" if move_type.startswith("out_") else "purchase"
    journal = env.add(
        "account.journal",
        61,
        name="Alternative journal",
        company_id=env.company,
        type=journal_type,
        currency_id=env.currency,
    )
    references = {"journal_id": journal.id, "currency_id": env.foreign_currency.id}
    changes = {field: references[field] for field in fields}
    changes.update({"date": "2025-03-01", "reference": "Updated header"})
    parameters = {"move_id": invoice.id, "changes": changes}
    payload = _payload(
        "invoice.update",
        parameters,
        key=writes._deterministic_key("invoice.update", parameters, 7),
    )

    assert not writes.dispatch(env, payload, 7, Failure)["idempotent_replay"]
    assert writes._current_invoice_changes(invoice, set(changes)) == changes
    assert writes.dispatch(env, payload, 7, Failure)["idempotent_replay"]
    expected_values = dict(changes)
    expected_values["ref"] = expected_values.pop("reference")
    assert [call[3] for call in env.calls if call[:2] == ("write", "account.move")] == [
        expected_values
    ]
    if "journal_id" in fields:
        assert any(
            call[:2] == ("search", "account.journal")
            and ("company_id", "=", 7) in call[2]
            and ("type", "=", journal_type) in call[2]
            for call in env.calls
        )
    if "currency_id" in fields:
        assert any(
            call[:2] == ("search", "res.currency")
            and ("active", "=", True) in call[2]
            for call in env.calls
        )
    invoice.state = "posted"
    assert writes.dispatch(env, payload, 7, Failure)["idempotent_replay"]
    changed = {"move_id": invoice.id, "changes": {"currency_id": env.currency.id}}
    if "currency_id" not in fields:
        changed["changes"]["currency_id"] = env.foreign_currency.id
    with pytest.raises(Failure) as caught:
        writes.dispatch(
            env,
            _payload(
                "invoice.update",
                changed,
                key=writes._deterministic_key("invoice.update", changed, 7),
            ),
            7,
            Failure,
        )
    assert caught.value.code == "state_conflict"
    assert sum(call[:2] == ("write", "account.move") for call in env.calls) == 1


@pytest.mark.parametrize(
    "changes",
    [
        {"journal_id": 999},
        {"journal_id": 62},
        {"journal_id": 11},
        {"currency_id": 999},
        {"currency_id": 3},
    ],
)
def test_invoice_update_rejects_unavailable_header_references_without_write(
    changes: dict[str, int],
) -> None:
    env = Env()
    invoice = env.existing_move(610, move_type="out_invoice", state="draft")
    other_company = env.add("res.company", 8, name="Other company")
    env.add(
        "account.journal", 62, name="Other journal", company_id=other_company, type="sale"
    )
    env.add("res.currency", 3, name="Inactive currency", active=False)
    parameters = {"move_id": invoice.id, "changes": changes}
    with pytest.raises(Failure) as caught:
        writes.dispatch(
            env,
            _payload(
                "invoice.update",
                parameters,
                key=writes._deterministic_key("invoice.update", parameters, 7),
            ),
            7,
            Failure,
        )
    assert caught.value.code == "record_not_found"
    assert not any(call[0] == "write" for call in env.calls)


@pytest.mark.parametrize("field", ["journal_id", "currency_id"])
@pytest.mark.parametrize("value", [None, True, 0, -1, "1", 1.0])
def test_invoice_update_header_reference_ids_are_validated_at_runtime(
    field: str, value: Any
) -> None:
    assert not writes._valid_parameters(
        "invoice.update", {"move_id": 610, "changes": {field: value}}
    )


@pytest.mark.parametrize("model", ["account.journal", "res.currency"])
def test_invoice_update_respects_header_reference_read_access(model: str) -> None:
    env = Env()
    env.denied_access = (model, "read")
    parameters = {"move_id": 610, "changes": {"journal_id": 10, "currency_id": 2}}
    result = writes.dispatch(
        env,
        _payload(
            "invoice.update",
            parameters,
            key=writes._deterministic_key("invoice.update", parameters, 7),
        ),
        7,
        Failure,
    )
    assert result["access_allowed"] is False and result["result"] is None
    assert not any(call[0] == "write" for call in env.calls)


def test_document_create_writes_optional_headers_lines_and_scopes_references() -> None:
    env = Env()
    parameters = _document_parameters(env, "customer_invoice.create")
    parameters.update(
        {
            "payment_term_id": env.payment_term.id,
            "reference": "PO-42",
            "payment_reference": "RF-42",
        }
    )
    parameters["lines"][0].update(
        {
            "product_id": env.product.id,
            "discount": "12.5",
            "analytic_distribution": {str(env.analytic.id): "100"},
        }
    )

    page = writes.dispatch(
        env,
        _payload("customer_invoice.create", parameters, key="invoice-fields-key"),
        7,
        Failure,
    )

    assert page["result"]["move_type"] == "out_invoice"
    values = next(
        call[2] for call in env.calls if call[:2] == ("create", "account.move")
    )
    assert values["invoice_payment_term_id"] == env.payment_term.id
    assert values["ref"] == "PO-42"
    assert values["payment_reference"] == "RF-42"
    line_values = values["invoice_line_ids"][0][2]
    assert line_values["product_id"] == env.product.id
    assert line_values["discount"] == Decimal("12.5")
    assert line_values["analytic_distribution"] == {str(env.analytic.id): 100.0}
    assert any(
        call[:2] == ("search", "account.payment.term")
        and ("company_id", "in", [False, 7]) in call[2]
        for call in env.calls
    )
    assert any(
        call[:2] == ("search", "account.analytic.account")
        and ("company_id", "in", [False, 7]) in call[2]
        for call in env.calls
    )

    due_env = Env()
    due_parameters = _document_parameters(due_env, "vendor_bill.create")
    due_parameters["invoice_date_due"] = "2025-03-01"
    writes.dispatch(
        due_env,
        _payload("vendor_bill.create", due_parameters, key="bill-due-date-key"),
        7,
        Failure,
    )
    due_values = next(
        call[2] for call in due_env.calls if call[:2] == ("create", "account.move")
    )
    assert due_values["invoice_date_due"] == "2025-03-01"
    assert "invoice_payment_term_id" not in due_values

    other_company = env.add("res.company", 8, name="Other Company")
    foreign_analytic = env.add(
        "account.analytic.account",
        62,
        name="Other project",
        company_id=other_company,
    )
    bad_parameters = copy.deepcopy(parameters)
    bad_parameters["lines"][0]["analytic_distribution"] = {
        str(foreign_analytic.id): "100"
    }
    with pytest.raises(Failure) as caught:
        writes.dispatch(
            env,
            _payload(
                "customer_invoice.create",
                bad_parameters,
                key="invoice-cross-company-key",
            ),
            7,
            Failure,
        )
    assert caught.value.code == "record_not_found"


def test_invoice_line_replace_persists_analytic_distribution_and_replays() -> None:
    env = Env()
    invoice = env.existing_move(610, move_type="out_invoice", state="draft")
    parameters = {"move_id": invoice.id, "lines": _replacement_invoice_lines(env)}
    key = writes._deterministic_key("invoice.lines.replace", parameters, 7)
    assert key is not None

    first = writes.dispatch(
        env,
        _payload("invoice.lines.replace", parameters, key=key),
        7,
        Failure,
    )
    second = writes.dispatch(
        env,
        _payload("invoice.lines.replace", parameters, key=key),
        7,
        Failure,
    )

    assert first["result"]["id"] == invoice.id
    assert second["idempotent_replay"] is True
    assert writes._current_invoice_lines(
        Records(env, "account.move", [invoice])
    ) == writes._normalized_invoice_replacement_lines(parameters["lines"])


@pytest.mark.parametrize(
    "capability_id", ["customer_invoice.create", "vendor_bill.create"]
)
@pytest.mark.parametrize("clear_dates", [False, True])
def test_document_create_persists_deferred_dates_and_keys_include_them(
    capability_id: str,
    clear_dates: bool,
) -> None:
    env = Env()
    parameters = _document_parameters(env, capability_id)
    dates = {
        "deferred_start_date": None if clear_dates else "2025-03-01",
        "deferred_end_date": None if clear_dates else "2025-04-30",
    }
    parameters["lines"][0].update(dates)
    payload = _payload(capability_id, parameters, key="deferred-create")

    first = writes.dispatch(env, payload, 7, Failure)
    replay = writes.dispatch(env, payload, 7, Failure)

    assert first["idempotent_replay"] is False
    assert replay["idempotent_replay"] is True
    creates = [call for call in env.calls if call[:2] == ("create", "account.move")]
    assert len(creates) == 1
    line_values = creates[0][2]["invoice_line_ids"][0][2]
    assert {field: line_values[field] for field in dates} == {
        field: value or False for field, value in dates.items()
    }
    changed = copy.deepcopy(payload)
    changed["parameters"]["lines"][0].update(
        deferred_start_date="2025-03-01", deferred_end_date="2025-05-31"
    )
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, changed, 7, Failure)
    assert caught.value.code == "idempotency_conflict"


@pytest.mark.parametrize(
    "capability_id", ["customer_invoice.create", "invoice.lines.replace"]
)
@pytest.mark.parametrize(
    "dates",
    [
        {"deferred_end_date": "2025-04-30"},
        {"deferred_start_date": None, "deferred_end_date": "2025-04-30"},
        {"deferred_start_date": "2025-05-01", "deferred_end_date": "2025-04-30"},
        {"deferred_start_date": "2025-02-29", "deferred_end_date": "2025-04-30"},
    ],
)
def test_runtime_rejects_invalid_deferred_dates_before_business_writes(
    capability_id: str,
    dates: dict,
) -> None:
    env = Env()
    parameters = (
        _document_parameters(env, capability_id)
        if capability_id == "customer_invoice.create"
        else {"move_id": 610, "lines": _replacement_invoice_lines(env)}
    )
    parameters["lines"][0].update(dates)
    key = writes._deterministic_key(capability_id, parameters, 7) or "invalid-dates"

    with pytest.raises(Failure) as caught:
        writes.dispatch(env, _payload(capability_id, parameters, key=key), 7, Failure)

    assert caught.value.code == "bridge_protocol_error"
    assert not any(call[0] in {"create", "write"} for call in env.calls)


def test_invoice_line_replace_updates_and_clears_deferred_dates_without_false_replay() -> (
    None
):
    env = Env()
    invoice = env.existing_move(610, move_type="out_invoice", state="draft")
    parameters = {"move_id": invoice.id, "lines": _replacement_invoice_lines(env)}
    parameters["lines"][0].update(
        deferred_start_date="2025-03-01", deferred_end_date="2025-04-30"
    )
    key = writes._deterministic_key("invoice.lines.replace", parameters, 7)
    payload = _payload("invoice.lines.replace", parameters, key=key)
    assert writes.dispatch(env, payload, 7, Failure)["idempotent_replay"] is False
    for line in invoice.invoice_line_ids:
        line.deferred_start_date = date(2025, 3, 1)
        line.deferred_end_date = date(2025, 4, 30)
    assert writes.dispatch(env, payload, 7, Failure)["idempotent_replay"] is True

    for dates in (
        {"deferred_start_date": "2025-03-01", "deferred_end_date": "2025-05-31"},
        {"deferred_start_date": None, "deferred_end_date": None},
    ):
        parameters["lines"][0].update(dates)
        next_key = writes._deterministic_key("invoice.lines.replace", parameters, 7)
        assert next_key != key
        next_payload = _payload("invoice.lines.replace", parameters, key=next_key)
        assert (
            writes.dispatch(env, next_payload, 7, Failure)["idempotent_replay"] is False
        )
        assert (
            writes.dispatch(env, next_payload, 7, Failure)["idempotent_replay"] is True
        )
        assert writes._current_invoice_lines(
            Records(env, "account.move", [invoice])
        ) == writes._normalized_invoice_replacement_lines(parameters["lines"])
        key = next_key
    assert all(
        line.deferred_start_date is False and line.deferred_end_date is False
        for line in invoice.invoice_line_ids
    )


@pytest.mark.parametrize("state", ["draft", "posted"])
def test_legacy_invoice_line_replay_preserves_existing_deferred_dates(
    state: str,
) -> None:
    env = Env()
    invoice = env.existing_move(610, move_type="out_invoice", state="draft")
    parameters = {"move_id": invoice.id, "lines": _replacement_invoice_lines(env)}
    key = writes._deterministic_key("invoice.lines.replace", parameters, 7)
    payload = _payload("invoice.lines.replace", parameters, key=key)
    writes.dispatch(env, payload, 7, Failure)
    invoice.state = state
    for line in invoice.invoice_line_ids:
        line.deferred_start_date = date(2025, 3, 1)
        line.deferred_end_date = date(2025, 4, 30)
    before = len([call for call in env.calls if call[0] == "write"])

    assert writes.dispatch(env, payload, 7, Failure)["idempotent_replay"] is True

    assert len([call for call in env.calls if call[0] == "write"]) == before
    assert all(
        line.deferred_start_date == date(2025, 3, 1)
        and line.deferred_end_date == date(2025, 4, 30)
        for line in invoice.invoice_line_ids
    )


@pytest.mark.parametrize("source_field", ["sale_line_ids", "purchase_line_id"])
def test_deferred_date_change_does_not_bypass_external_invoice_source_guard(
    source_field: str,
) -> None:
    env = Env()
    invoice = env.existing_move(610, move_type="out_invoice", state="draft")
    parameters = {"move_id": invoice.id, "lines": _replacement_invoice_lines(env)}
    parameters["lines"][0].update(
        deferred_start_date="2025-03-01", deferred_end_date="2025-04-30"
    )
    key = writes._deterministic_key("invoice.lines.replace", parameters, 7)
    writes.dispatch(
        env, _payload("invoice.lines.replace", parameters, key=key), 7, Failure
    )
    for line in invoice.invoice_line_ids:
        line._fields = {source_field: object()}
        setattr(line, source_field, [999])
    before = len([call for call in env.calls if call[0] == "write"])
    parameters["lines"][0]["deferred_end_date"] = "2025-05-31"
    key = writes._deterministic_key("invoice.lines.replace", parameters, 7)

    with pytest.raises(Failure) as caught:
        writes.dispatch(
            env, _payload("invoice.lines.replace", parameters, key=key), 7, Failure
        )

    assert caught.value.code == "business_rule_error"
    assert len([call for call in env.calls if call[0] == "write"]) == before


@pytest.mark.parametrize(
    "capability_id", ["customer_credit_note.create", "vendor_refund.create"]
)
def test_refund_deferred_dates_are_persisted_and_verified_on_replay(
    capability_id: str,
) -> None:
    env = Env()
    source = env.existing_move(
        405,
        move_type="out_invoice"
        if capability_id.startswith("customer")
        else "in_invoice",
        state="posted",
    )
    parameters = {
        "move_id": source.id,
        "date": "2025-02-05",
        "reason": "Deferred correction",
        "lines": _replacement_invoice_lines(env),
    }
    parameters["lines"][0].update(
        deferred_start_date="2025-03-01", deferred_end_date="2025-04-30"
    )
    payload = _payload(capability_id, parameters, key="deferred-refund")
    first = writes.dispatch(env, payload, 7, Failure)
    assert writes.dispatch(env, payload, 7, Failure)["idempotent_replay"] is True
    refund = env.models["account.move"].browse(first["result"]["id"])
    assert writes._current_invoice_lines(
        refund
    ) == writes._normalized_invoice_replacement_lines(parameters["lines"])
    for line in refund.invoice_line_ids:
        line.deferred_end_date = "2025-05-31"

    with pytest.raises(Failure) as caught:
        writes.dispatch(env, payload, 7, Failure)
    assert caught.value.code == "idempotency_conflict"


@pytest.mark.parametrize(
    "capability_id", ["customer_credit_note.create", "vendor_refund.create"]
)
def test_legacy_refund_replay_preserves_existing_deferred_dates(
    capability_id: str,
) -> None:
    env = Env()
    source = env.existing_move(
        405,
        move_type="out_invoice"
        if capability_id.startswith("customer")
        else "in_invoice",
        state="posted",
    )
    parameters = {
        "move_id": source.id,
        "date": "2025-02-05",
        "reason": "Legacy deferred correction",
        "lines": _replacement_invoice_lines(env),
    }
    payload = _payload(capability_id, parameters, key="legacy-deferred-refund")
    first = writes.dispatch(env, payload, 7, Failure)
    refund = env.models["account.move"].browse(first["result"]["id"])
    for line in refund.invoice_line_ids:
        line.deferred_start_date = date(2025, 3, 1)
        line.deferred_end_date = date(2025, 4, 30)
    before = len([call for call in env.calls if call[0] == "write"])

    assert writes.dispatch(env, payload, 7, Failure)["idempotent_replay"] is True

    assert len([call for call in env.calls if call[0] == "write"]) == before
    assert all(
        line.deferred_start_date == date(2025, 3, 1)
        and line.deferred_end_date == date(2025, 4, 30)
        for line in refund.invoice_line_ids
    )


def test_entry_create_is_balanced_then_post_is_naturally_idempotent() -> None:
    env = Env()
    created = writes.dispatch(
        env,
        _payload("journal_entry.create", _entry_parameters(env), key="entry-key"),
        7,
        Failure,
    )
    assert created["result"]["move_type"] == "entry"
    move_id = created["result"]["id"]
    post = _payload(
        "journal_entry.post",
        {"move_id": move_id},
        key=f"journal_entry.post:{move_id}",
    )

    first = writes.dispatch(env, post, 7, Failure)
    second = writes.dispatch(env, post, 7, Failure)

    assert (first["result"]["state"], first["idempotent_replay"]) == (
        "posted",
        False,
    )
    assert second["idempotent_replay"] is True
    assert [call[0] for call in env.calls].count("action_post") == 1

    invalid = _entry_parameters(env)
    invalid["lines"][1]["credit"] = "24.00"
    with pytest.raises(Failure) as caught:
        writes.dispatch(Env(), _payload("journal_entry.create", invalid), 7, Failure)
    assert caught.value.code == "bridge_protocol_error"


def test_entry_create_and_replace_write_currency_reference_and_analytic_values() -> (
    None
):
    env = Env()
    parameters = _entry_parameters(env)
    parameters["reference"] = "FX-ENTRY"
    parameters["lines"][0].update(
        {
            "currency_id": env.foreign_currency.id,
            "amount_currency": "30",
            "analytic_distribution": {str(env.analytic.id): "100"},
        }
    )
    parameters["lines"][1].update(
        {"currency_id": env.foreign_currency.id, "amount_currency": "-30"}
    )

    created = writes.dispatch(
        env,
        _payload("journal_entry.create", parameters, key="entry-fx-create-key"),
        7,
        Failure,
    )
    assert created["result"]["move_type"] == "entry"
    values = next(
        call[2] for call in env.calls if call[:2] == ("create", "account.move")
    )
    assert values["ref"] == "FX-ENTRY"
    assert values["line_ids"][0][2]["currency_id"] == env.foreign_currency.id
    assert values["line_ids"][0][2]["amount_currency"] == Decimal(30)
    assert values["line_ids"][0][2]["analytic_distribution"] == {
        str(env.analytic.id): 100.0
    }

    entry = env.existing_move(611, move_type="entry", state="draft")
    replacement_parameters = {"move_id": entry.id, "lines": parameters["lines"]}
    replacement_key = writes._deterministic_key(
        "journal_entry.lines.replace", replacement_parameters, 7
    )
    assert replacement_key is not None
    replaced = writes.dispatch(
        env,
        _payload(
            "journal_entry.lines.replace",
            replacement_parameters,
            key=replacement_key,
        ),
        7,
        Failure,
    )
    replay = writes.dispatch(
        env,
        _payload(
            "journal_entry.lines.replace",
            replacement_parameters,
            key=replacement_key,
        ),
        7,
        Failure,
    )
    assert replaced["result"]["id"] == entry.id
    assert replay["idempotent_replay"] is True

    invalid_env = Env()
    invalid = _entry_parameters(invalid_env)
    invalid["lines"][0].update(
        {"currency_id": invalid_env.currency.id, "amount_currency": "30"}
    )
    invalid["lines"][1].update(
        {"currency_id": invalid_env.currency.id, "amount_currency": "-30"}
    )
    with pytest.raises(Failure) as caught:
        writes.dispatch(
            invalid_env,
            _payload("journal_entry.create", invalid, key="entry-currency-mismatch"),
            7,
            Failure,
        )
    assert caught.value.code == "state_conflict"


def test_invoice_post_rejects_entries_and_posts_only_document_moves() -> None:
    env = Env()
    invoice = env.existing_move(80, move_type="out_invoice", state="draft")
    result = writes.dispatch(
        env,
        _payload(
            "invoice.post",
            {"move_id": invoice.id},
            key=f"invoice.post:{invoice.id}",
        ),
        7,
        Failure,
    )
    assert result["result"]["state"] == "posted"

    entry = env.existing_move(81, move_type="entry", state="draft")
    with pytest.raises(Failure) as caught:
        writes.dispatch(
            env,
            _payload(
                "invoice.post",
                {"move_id": entry.id},
                key=f"invoice.post:{entry.id}",
            ),
            7,
            Failure,
        )
    assert caught.value.code == "record_not_found"


def test_reversal_uses_odoo19_wizard_and_marker_for_replay() -> None:
    env = Env()
    source = env.existing_move(90, move_type="entry", state="posted")
    payload = _payload(
        "journal_entry.reverse",
        {"move_id": source.id, "date": "2025-02-03", "reason": "Correction"},
        key=f"journal_entry.reverse:{source.id}",
    )

    first = writes.dispatch(env, payload, 7, Failure)
    second = writes.dispatch(env, payload, 7, Failure)

    assert first["result"]["source_id"] == source.id
    assert first["result"]["state"] == "posted"
    assert second["idempotent_replay"] is True
    assert [call[0] for call in env.calls].count("reverse_moves") == 1
    reversal_create = next(
        call
        for call in env.calls
        if call[0] == "create" and call[1] == "account.move.reversal"
    )
    assert reversal_create[2]["journal_id"] == env.general_journal.id
    reversal = env.models["account.move"].browse(first["result"]["id"])
    assert reversal.reversed_entry_id == Records(env, "account.move", [source])
    assert reversal.invoice_origin.startswith("ODACV4:")


@pytest.mark.parametrize(
    ("capability_id", "move_type"),
    (
        ("receivable.payment.register", "out_invoice"),
        ("payable.payment.register", "in_invoice"),
        ("receivable.payment.register", "out_refund"),
        ("payable.payment.register", "in_refund"),
    ),
)
def test_payment_register_uses_full_residual_wizard_and_replays_by_source(
    capability_id: str, move_type: str
) -> None:
    env = Env()
    source = env.existing_move(100, move_type=move_type, residual="125.50")
    payload = _payload(
        capability_id,
        {
            "move_id": source.id,
            "journal_id": env.bank_journal.id,
            "payment_date": "2025-02-04",
        },
        key=f"{capability_id}:{source.id}",
    )

    first = writes.dispatch(env, payload, 7, Failure)
    second = writes.dispatch(env, payload, 7, Failure)

    assert first["result"]["model"] == "account.payment"
    assert first["result"]["source_id"] == source.id
    assert first["result"]["state"] == "in_process"
    assert second["idempotent_replay"] is True
    calls = [call for call in env.calls if call[0] == "action_create_payments"]
    payment = env.models["account.payment"].browse(first["result"]["id"])
    assert payment.payment_type == (
        "inbound" if move_type in {"out_invoice", "in_refund"} else "outbound"
    )
    assert payment.partner_type == (
        "customer" if move_type in {"out_invoice", "out_refund"} else "supplier"
    )
    assert calls == [
        (
            "action_create_payments",
            source.id,
            env.bank_journal.id,
            "2025-02-04",
            f"{capability_id}:{source.id}",
        )
    ]


def test_payment_register_replay_rejects_changed_payment_parameters() -> None:
    env = Env()
    source = env.existing_move(110, move_type="out_invoice", residual="25")
    capability_id = "receivable.payment.register"
    key = f"{capability_id}:{source.id}"
    first_payload = _payload(
        capability_id,
        {
            "move_id": source.id,
            "journal_id": env.bank_journal.id,
            "payment_date": "2025-02-04",
        },
        key=key,
    )
    changed_payload = copy.deepcopy(first_payload)
    changed_payload["parameters"]["payment_date"] = "2025-02-05"

    writes.dispatch(env, first_payload, 7, Failure)
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, changed_payload, 7, Failure)

    assert caught.value.code == "idempotency_conflict"


@pytest.mark.parametrize(
    "capability_id,move_type",
    [
        ("receivable.payment.register", "out_invoice"),
        ("receivable.payment.register", "out_refund"),
        ("payable.payment.register", "in_invoice"),
        ("payable.payment.register", "in_refund"),
    ],
)
def test_partial_payment_register_rounds_amount_leaves_open_and_replays(
    capability_id, move_type
) -> None:
    env = Env()
    source = env.existing_move(120, move_type=move_type, residual="125.50")
    parameters = {
        "move_id": source.id,
        "journal_id": env.bank_journal.id,
        "payment_date": "2025-02-04",
        "amount": "50",
    }
    payload = _payload(
        capability_id, parameters, key="partial-payment-operation"
    )

    first = writes.dispatch(env, payload, 7, Failure)
    second = writes.dispatch(env, payload, 7, Failure)

    assert first["idempotent_replay"] is False
    assert second["idempotent_replay"] is True
    assert source.amount_residual == Decimal("75.50")
    payment = env.models["account.payment"].browse(first["result"]["id"])
    assert payment.amount == Decimal("50.0")
    wizard_values = next(
        call[2]
        for call in env.calls
        if call[:2] == ("create", "account.payment.register")
    )
    assert wizard_values["amount"] == 50.0
    assert wizard_values["payment_difference_handling"] == "open"
    assert "payment_type" not in wizard_values
    assert "partner_type" not in wizard_values

    too_large = {**parameters, "amount": "80"}
    with pytest.raises(Failure) as caught:
        writes.dispatch(
            env,
            _payload(
                capability_id,
                too_large,
                key="second-partial-payment-operation",
            ),
            7,
            Failure,
        )
    assert caught.value.code == "state_conflict"


@pytest.mark.parametrize(
    "capability_id,move_type",
    [
        ("receivable.payment.register", "in_invoice"),
        ("receivable.payment.register", "in_refund"),
        ("payable.payment.register", "out_invoice"),
        ("payable.payment.register", "out_refund"),
    ],
)
def test_payment_register_rejects_other_document_family(capability_id, move_type):
    env = Env()
    source = env.existing_move(100, move_type=move_type)
    payload = _payload(
        capability_id,
        {
            "move_id": source.id,
            "journal_id": env.bank_journal.id,
            "payment_date": "2025-02-04",
        },
        key=f"{capability_id}:{source.id}",
    )
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, payload, 7, Failure)
    assert caught.value.code == "record_not_found"
    assert not any(call[0] == "create" for call in env.calls)


@pytest.mark.parametrize(
    ("residuals", "expected_state", "expected_reconciled"),
    ((["100", "-60"], "partial", False), (["60", "-60"], "reconciled", True)),
)
def test_reconciliation_calls_public_two_line_api_and_replays(
    residuals: list[str], expected_state: str, expected_reconciled: bool
) -> None:
    env = Env()
    left = env.reconciliation_line(201, residuals[0])
    right = env.reconciliation_line(202, residuals[1])
    payload = _payload(
        "reconciliation.apply",
        {"line_ids": [right.id, left.id]},
        key=f"reconciliation.apply:{left.id}:{right.id}",
    )

    first = writes.dispatch(env, payload, 7, Failure)
    second = writes.dispatch(env, payload, 7, Failure)

    assert first["result"]["id"] is None
    assert first["result"]["state"] == expected_state
    assert first["result"]["reconciled"] is expected_reconciled
    assert first["result"]["partial_reconcile_ids"]
    assert (first["result"]["full_reconcile_id"] is not None) is expected_reconciled
    assert second["idempotent_replay"] is True
    assert [call[0] for call in env.calls].count("reconcile") == 1


def test_invoice_widget_apply_handles_split_terms_then_targeted_undo_replays() -> None:
    env = Env()
    invoice, term_lines, counterpart = _invoice_widget_fixture(
        env, term_residuals=("60", "40")
    )
    apply_parameters = {
        "invoice_id": invoice.id,
        "outstanding_line_id": counterpart.id,
    }
    apply_key = f"reconciliation.apply:{invoice.id}:{counterpart.id}"

    first_apply = writes.dispatch(
        env,
        _payload("reconciliation.apply", apply_parameters, key=apply_key),
        7,
        Failure,
    )
    replay_apply = writes.dispatch(
        env,
        _payload("reconciliation.apply", apply_parameters, key=apply_key),
        7,
        Failure,
    )

    assert first_apply["result"]["source_id"] == invoice.id
    assert first_apply["result"]["line_ids"] == sorted(
        [term_lines[0].id, term_lines[1].id, counterpart.id]
    )
    assert len(first_apply["result"]["partial_reconcile_ids"]) == 2
    assert replay_apply["idempotent_replay"] is True
    assert (
        "js_assign_outstanding_line",
        invoice.id,
        counterpart.id,
    ) in env.calls

    first_partial = next(
        partial
        for partial in env.data["account.partial.reconcile"]
        if term_lines[0].id in {partial.debit_move_id.id, partial.credit_move_id.id}
    )
    remaining_partial = next(
        partial
        for partial in env.data["account.partial.reconcile"]
        if partial.id != first_partial.id
    )
    undo_parameters = {
        "invoice_id": invoice.id,
        "partial_reconcile_id": first_partial.id,
        "invoice_line_id": term_lines[0].id,
        "counterpart_line_id": counterpart.id,
    }
    low, high = sorted((term_lines[0].id, counterpart.id))
    undo_key = f"reconciliation.undo:{invoice.id}:{first_partial.id}:{low}:{high}"
    first_undo = writes.dispatch(
        env,
        _payload("reconciliation.undo", undo_parameters, key=undo_key),
        7,
        Failure,
    )
    replay_undo = writes.dispatch(
        env,
        _payload("reconciliation.undo", undo_parameters, key=undo_key),
        7,
        Failure,
    )

    assert first_undo["result"]["source_id"] == invoice.id
    assert first_undo["result"]["line_ids"] == sorted(
        [term_lines[0].id, term_lines[1].id, counterpart.id]
    )
    assert first_undo["result"]["partial_reconcile_ids"] == [remaining_partial.id]
    assert first_undo["result"]["full_reconcile_id"] is None
    assert replay_undo["idempotent_replay"] is True
    assert replay_undo["result"] == first_undo["result"]
    assert [
        call for call in env.calls if call[0] == "js_remove_outstanding_partial"
    ] == [("js_remove_outstanding_partial", invoice.id, first_partial.id)]

    cross_env = Env()
    cross_invoice, _cross_terms, cross_counterpart = _invoice_widget_fixture(
        cross_env, invoice_id=800
    )
    other_company = cross_env.add("res.company", 8, name="Other Company")
    cross_counterpart.company_id = other_company
    with pytest.raises(Failure) as caught:
        writes.dispatch(
            cross_env,
            _payload(
                "reconciliation.apply",
                {
                    "invoice_id": cross_invoice.id,
                    "outstanding_line_id": cross_counterpart.id,
                },
                key=(f"reconciliation.apply:{cross_invoice.id}:{cross_counterpart.id}"),
            ),
            7,
            Failure,
        )
    assert caught.value.code == "record_not_found"


def test_payment_cancel_calls_public_action_and_replays_canceled_state() -> None:
    env = Env()
    payment_move = env.existing_move(
        300, move_type="entry", state="posted", residual="0"
    )
    payment = env.add(
        "account.payment",
        301,
        name="PAY/301",
        state="in_process",
        company_id=env.company,
        memo="payment",
        move_id=Records(env, "account.move", [payment_move]),
        reconciled_invoice_ids=Records(env, "account.move"),
        reconciled_bill_ids=Records(env, "account.move"),
        is_reconciled=True,
    )
    payload = _payload(
        "payment.cancel",
        {"payment_id": payment.id},
        key=f"payment.cancel:{payment.id}",
    )

    first = writes.dispatch(env, payload, 7, Failure)
    second = writes.dispatch(env, payload, 7, Failure)

    assert first["result"]["state"] == "canceled"
    assert first["result"]["reconciled"] is False
    assert second["idempotent_replay"] is True
    assert [call[0] for call in env.calls].count("action_cancel") == 1


@pytest.mark.parametrize(
    ("capability_id", "source_type", "refund_type"),
    (
        ("customer_credit_note.create", "out_invoice", "out_refund"),
        ("vendor_refund.create", "in_invoice", "in_refund"),
    ),
)
def test_refund_create_uses_refund_wizard_and_exact_marker_replay(
    capability_id: str, source_type: str, refund_type: str
) -> None:
    env = Env()
    source = env.existing_move(401, move_type=source_type, state="posted")
    parameters = {
        "move_id": source.id,
        "date": "2025-02-05",
        "reason": "Commercial correction",
    }
    payload = _payload(capability_id, parameters, key=f"{capability_id}:{source.id}")

    first = writes.dispatch(env, payload, 7, Failure)
    second = writes.dispatch(env, payload, 7, Failure)

    assert first["idempotent_replay"] is False
    assert second["idempotent_replay"] is True
    assert first["result"]["model"] == "account.move"
    assert first["result"]["move_type"] == refund_type
    assert first["result"]["state"] == "draft"
    assert first["result"]["source_id"] == source.id
    assert source.state == "posted"
    assert [call[0] for call in env.calls].count("refund_moves") == 1
    wizard_create = next(
        call
        for call in env.calls
        if call[0] == "create" and call[1] == "account.move.reversal"
    )
    assert wizard_create[2]["journal_id"] == source.journal_id.id
    refund = env.models["account.move"].browse(first["result"]["id"])
    assert refund.invoice_origin.startswith("ODACV4:")

    changed = copy.deepcopy(payload)
    changed["parameters"]["reason"] = "Different correction"
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, changed, 7, Failure)
    assert caught.value.code == "idempotency_conflict"


def test_refund_replays_legacy_marker_only_for_exact_legacy_contract() -> None:
    capability_id = "customer_credit_note.create"
    env = Env()
    source = env.existing_move(402, move_type="out_invoice", state="posted")
    parameters = {
        "move_id": source.id,
        "date": "2025-02-05",
        "reason": "Legacy correction",
    }
    legacy_key = f"{capability_id}:{source.id}"
    legacy_payload = _payload(capability_id, parameters, key=legacy_key)
    legacy_marker = writes._validated_payload(legacy_payload, 7, Failure)[3]
    legacy_refund = env.existing_move(403, move_type="out_refund", state="draft")
    legacy_refund.reversed_entry_id = source
    legacy_refund.invoice_origin = legacy_marker

    replay = writes.dispatch(env, legacy_payload, 7, Failure)

    assert replay["idempotent_replay"] is True
    assert replay["result"]["id"] == legacy_refund.id
    assert not any(call[0] == "refund_moves" for call in env.calls)

    caller_key_payload = _payload(
        capability_id, parameters, key="migrated-refund-operation"
    )
    created = writes.dispatch(env, caller_key_payload, 7, Failure)
    assert created["idempotent_replay"] is False
    assert created["result"]["id"] != legacy_refund.id
    assert [call[0] for call in env.calls].count("refund_moves") == 1

    lines_env = Env()
    lines_source = lines_env.existing_move(404, move_type="out_invoice", state="posted")
    old_parameters = {**parameters, "move_id": lines_source.id}
    old_key = f"{capability_id}:{lines_source.id}"
    old_payload = _payload(capability_id, old_parameters, key=old_key)
    old_marker = writes._validated_payload(old_payload, 7, Failure)[3]
    old_refund = lines_env.existing_move(406, move_type="out_refund", state="draft")
    old_refund.reversed_entry_id = lines_source
    old_refund.invoice_origin = old_marker
    lines_payload = _payload(
        capability_id,
        {**old_parameters, "lines": _replacement_invoice_lines(lines_env)},
        key=old_key,
    )

    lines_created = writes.dispatch(lines_env, lines_payload, 7, Failure)

    assert lines_created["idempotent_replay"] is False
    assert lines_created["result"]["id"] != old_refund.id
    assert [call[0] for call in lines_env.calls].count("refund_moves") == 1


def test_refund_same_source_allows_distinct_operation_markers_and_replacement_lines() -> (
    None
):
    env = Env()
    source = env.existing_move(405, move_type="out_invoice", state="posted")
    parameters = {
        "move_id": source.id,
        "date": "2025-02-05",
        "reason": "Partial commercial correction",
        "lines": _replacement_invoice_lines(env),
    }
    first_payload = _payload(
        "customer_credit_note.create", parameters, key="refund-operation-one"
    )
    second_payload = _payload(
        "customer_credit_note.create", parameters, key="refund-operation-two"
    )

    first = writes.dispatch(env, first_payload, 7, Failure)
    second = writes.dispatch(env, second_payload, 7, Failure)
    first_replay = writes.dispatch(env, first_payload, 7, Failure)
    second_replay = writes.dispatch(env, second_payload, 7, Failure)

    assert first["result"]["id"] != second["result"]["id"]
    assert first_replay["idempotent_replay"] is True
    assert second_replay["idempotent_replay"] is True
    refunds = [
        move
        for move in env.data["account.move"]
        if move.move_type == "out_refund" and move.reversed_entry_id.id == source.id
    ]
    assert len(refunds) == 2
    assert len({refund.invoice_origin for refund in refunds}) == 2
    assert all(
        writes._current_invoice_lines(Records(env, "account.move", [refund]))
        == writes._normalized_invoice_replacement_lines(parameters["lines"])
        for refund in refunds
    )
    assert [call[0] for call in env.calls].count("refund_moves") == 2


def test_payment_post_calls_public_action_and_replays_terminal_state() -> None:
    env = Env()
    payment_move = env.existing_move(
        410, move_type="entry", state="draft", residual="0"
    )
    payment = env.add(
        "account.payment",
        411,
        name="PAY/411",
        state="draft",
        company_id=env.company,
        memo="payment",
        move_id=Records(env, "account.move", [payment_move]),
        reconciled_invoice_ids=Records(env, "account.move"),
        reconciled_bill_ids=Records(env, "account.move"),
        is_reconciled=False,
    )
    payload = _payload(
        "payment.post",
        {"payment_id": payment.id},
        key=f"payment.post:{payment.id}",
    )

    first = writes.dispatch(env, payload, 7, Failure)
    second = writes.dispatch(env, payload, 7, Failure)

    assert first["result"]["state"] == "in_process"
    assert first["result"]["source_id"] is None
    assert first["idempotent_replay"] is False
    assert second["idempotent_replay"] is True
    assert [call[0] for call in env.calls].count("action_post") == 1


def test_reconciliation_undo_unlinks_only_exact_pair_then_weakly_replays() -> None:
    env = Env()
    left = env.reconciliation_line(421, "60")
    right = env.reconciliation_line(422, "-60")
    env.reconcile(Records(env, "account.move.line", [left, right]))
    partial_id = (left.matched_credit_ids | right.matched_debit_ids).id
    payload = _payload(
        "reconciliation.undo",
        {"line_ids": [right.id, left.id]},
        key=f"reconciliation.undo:{left.id}:{right.id}",
    )

    first = writes.dispatch(env, payload, 7, Failure)
    second = writes.dispatch(env, payload, 7, Failure)

    assert first["result"] == {
        "model": "account.move.line",
        "id": None,
        "name": None,
        "state": "unreconciled",
        "company_id": 7,
        "move_type": None,
        "source_id": None,
        "line_ids": [left.id, right.id],
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }
    assert first["idempotent_replay"] is False
    assert second["idempotent_replay"] is True
    assert ("unlink_partial", (partial_id,)) in env.calls
    assert not any(call[0] == "remove_move_reconcile" for call in env.calls)


def test_reconciliation_undo_rejects_a_larger_full_reconcile_graph() -> None:
    env = Env()
    left = env.reconciliation_line(431, "60")
    right = env.reconciliation_line(432, "-60")
    third = env.reconciliation_line(433, "10")
    env.reconcile(Records(env, "account.move.line", [left, right]))
    full = left.full_reconcile_id.records[0]
    full.reconciled_line_ids = Records(env, "account.move.line", [left, right, third])

    with pytest.raises(Failure) as caught:
        writes.dispatch(
            env,
            _payload(
                "reconciliation.undo",
                {"line_ids": [left.id, right.id]},
                key=f"reconciliation.undo:{left.id}:{right.id}",
            ),
            7,
            Failure,
        )

    assert caught.value.code == "state_conflict"
    assert not any(call[0] == "unlink_partial" for call in env.calls)


def test_reconciliation_undo_rejects_an_extra_side_partial() -> None:
    env = Env()
    left = env.reconciliation_line(441, "100")
    right = env.reconciliation_line(442, "-60")
    third = env.reconciliation_line(443, "-10")
    env.reconcile(Records(env, "account.move.line", [left, right]))
    extra = env.new_record(
        "account.partial.reconcile",
        debit_move_id=left,
        credit_move_id=third,
        full_reconcile_id=Records(env, "account.full.reconcile"),
    )
    extra_records = Records(env, "account.partial.reconcile", [extra])
    left.matched_credit_ids |= extra_records
    third.matched_debit_ids = extra_records

    with pytest.raises(Failure) as caught:
        writes.dispatch(
            env,
            _payload(
                "reconciliation.undo",
                {"line_ids": [left.id, right.id]},
                key=f"reconciliation.undo:{left.id}:{right.id}",
            ),
            7,
            Failure,
        )

    assert caught.value.code == "state_conflict"
    assert not any(call[0] == "unlink_partial" for call in env.calls)


def test_bank_transaction_create_is_posted_and_replays_exact_marker() -> None:
    env = Env()
    parameters = {
        "journal_id": env.bank_journal.id,
        "date": "2025-02-06",
        "amount": "-125.50",
        "payment_ref": "Supplier debit",
        "partner_id": env.partner.id,
    }
    payload = _payload(
        "bank.transaction.record", parameters, key="bank-transaction-key-1"
    )

    first = writes.dispatch(env, payload, 7, Failure)
    second = writes.dispatch(env, payload, 7, Failure)

    assert first["result"]["model"] == "account.bank.statement.line"
    assert first["result"]["name"].startswith("BNK/")
    assert first["result"]["state"] == "posted"
    assert first["result"]["move_type"] == "entry"
    assert first["result"]["source_id"] > 0
    assert first["result"]["line_ids"]
    assert first["idempotent_replay"] is False
    assert second["idempotent_replay"] is True
    creates = [
        call
        for call in env.calls
        if call[:2] == ("create", "account.bank.statement.line")
    ]
    assert len(creates) == 1
    values = creates[0][2]
    assert values["amount"] == Decimal("-125.50")
    assert values["ref"] == "bank-transaction-key-1"
    assert values["invoice_origin"].startswith("ODACV4:")
    assert [call[0] for call in env.calls].count("bank_auto_post") == 1

    changed = copy.deepcopy(payload)
    changed["parameters"]["amount"] = "-126.00"
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, changed, 7, Failure)
    assert caught.value.code == "idempotency_conflict"


def test_payload_confirmation_company_and_access_fail_closed() -> None:
    env = Env()
    payload = _payload("journal_entry.create", _entry_parameters(env))
    payload["confirmation"] = "invoice.post"
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, payload, 7, Failure)
    assert caught.value.code == "bridge_protocol_error"
    assert env.calls == []

    env = Env()
    payload = _payload("journal_entry.create", _entry_parameters(env))
    payload["company_id"] = 8
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, payload, 7, Failure)
    assert caught.value.code == "company_unavailable"
    assert env.calls == []

    env = Env()
    env.denied_access = ("account.move", "create")
    closed = writes.dispatch(
        env,
        _payload("journal_entry.create", _entry_parameters(env)),
        7,
        Failure,
    )
    assert closed["access_allowed"] is False
    assert closed["result"] is None
    assert not any(call[0] == "create" for call in env.calls)


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    (
        ("invoice.post", {"move_id": 41}),
        ("journal_entry.post", {"move_id": 42}),
        (
            "journal_entry.reverse",
            {"move_id": 43, "date": "2025-02-03", "reason": "Correction"},
        ),
        (
            "receivable.payment.register",
            {"move_id": 44, "journal_id": 14, "payment_date": "2025-02-04"},
        ),
        (
            "payable.payment.register",
            {"move_id": 45, "journal_id": 14, "payment_date": "2025-02-04"},
        ),
        ("reconciliation.apply", {"line_ids": [202, 201]}),
        ("payment.cancel", {"payment_id": 46}),
        ("payment.post", {"payment_id": 49}),
        ("reconciliation.undo", {"line_ids": [204, 203]}),
        ("asset.validate", {"asset_id": 50}),
        ("asset.cancel", {"asset_id": 51}),
        (
            "asset.dispose",
            {"asset_id": 52, "date": "2025-02-28", "note": "Disposed"},
        ),
        (
            "asset.pause",
            {"asset_id": 53, "date": "2025-02-28", "note": None},
        ),
        ("deferred_expense.generate_entries", {"date_to": "2025-02-28"}),
        ("deferred_revenue.generate_entries", {"date_to": "2025-02-28"}),
        (
            "multicurrency.revaluation.generate_entries",
            {
                "date": "2025-02-28",
                "reversal_date": "2025-03-01",
                "journal_id": 12,
                "expense_provision_account_id": 102,
                "income_provision_account_id": 101,
            },
        ),
        ("reconciliation.automatic.run", {"line_ids": [201, 202, 203]}),
        (
            "period.transfer.run",
            {"transfer_model_id": 54, "run_date": "2025-02-28"},
        ),
        (
            "localization.china.period_transfer.run",
            {"run_date": "2025-02-28"},
        ),
    ),
)
def test_non_create_capabilities_reject_non_deterministic_key_before_model_access(
    capability_id: str, parameters: dict[str, Any]
) -> None:
    env = Env()

    with pytest.raises(Failure) as caught:
        writes.dispatch(
            env,
            _payload(capability_id, parameters, key="wrong-key"),
            7,
            Failure,
        )

    assert caught.value.code == "bridge_protocol_error"
    assert env.calls == []


def test_unknown_parameter_and_non_string_decimal_fail_before_model_access() -> None:
    env = Env()
    parameters = _document_parameters(env, "customer_invoice.create")
    parameters["extra"] = None
    with pytest.raises(Failure) as caught:
        writes.dispatch(
            env,
            _payload("customer_invoice.create", parameters),
            7,
            Failure,
        )
    assert caught.value.code == "bridge_protocol_error"
    assert env.calls == []

    env = Env()
    parameters = _document_parameters(env, "customer_invoice.create")
    parameters["lines"][0]["price_unit"] = 50.0
    with pytest.raises(Failure) as caught:
        writes.dispatch(
            env,
            _payload("customer_invoice.create", parameters),
            7,
            Failure,
        )
    assert caught.value.code == "bridge_protocol_error"
    assert env.calls == []


@pytest.mark.parametrize("amount", ["0", "-0.00", "01.00", "1e2", 10.0])
def test_bank_transaction_rejects_noncanonical_or_zero_amount_before_access(
    amount: Any,
) -> None:
    env = Env()
    parameters = {
        "journal_id": env.bank_journal.id,
        "date": "2025-02-06",
        "amount": amount,
        "payment_ref": "Bank transaction",
        "partner_id": None,
    }

    with pytest.raises(Failure) as caught:
        writes.dispatch(
            env,
            _payload(
                "bank.transaction.record",
                parameters,
                key="bank-transaction-key-2",
            ),
            7,
            Failure,
        )

    assert caught.value.code == "bridge_protocol_error"
    assert env.calls == []


def test_generated_move_pair_rejects_a_cancelled_underlying_move() -> None:
    env = Env()
    moves = Records(
        env,
        "account.move",
        [
            Record(
                "account.move",
                2001,
                company_id=env.company,
                move_type="entry",
                state="posted",
            ),
            Record(
                "account.move",
                2002,
                company_id=env.company,
                move_type="entry",
                state="cancel",
            ),
        ],
    )

    with pytest.raises(Failure) as caught:
        writes._validated_move_pair(moves, 7, Failure)

    assert caught.value.code == "idempotency_conflict"


def _accounting_reference_payload(
    capability_id: str,
    parameters: dict[str, Any],
    *,
    company_id: int = 7,
) -> dict[str, Any]:
    key = writes._deterministic_key(capability_id, parameters, company_id)
    assert key is not None
    payload = _payload(capability_id, parameters, key=key)
    payload["company_id"] = company_id
    return payload


def _tax_repartition_parameters(env: Env) -> dict[str, Any]:
    lines = [
        {
            "sequence": 10,
            "repartition_type": "base",
            "factor_percent": "100",
            "account_id": None,
            "tag_ids": [],
            "use_in_tax_closing": False,
        },
        {
            "sequence": 20,
            "repartition_type": "tax",
            "factor_percent": "100",
            "account_id": env.expense.id,
            "tag_ids": [env.tax_tag.id],
            "use_in_tax_closing": True,
        },
    ]
    return {
        "tax_id": env.tax.id,
        "invoice_lines": copy.deepcopy(lines),
        "refund_lines": copy.deepcopy(lines),
    }


def test_currency_rate_record_uses_root_company_and_replays() -> None:
    env = Env()
    parameters = {
        "currency_id": env.foreign_currency.id,
        "date": "2025-03-01",
        "company_units_per_foreign_unit": "0.125",
    }
    payload = _accounting_reference_payload("currency.rate.record", parameters)

    created = writes.dispatch(env, payload, 7, Failure)
    replay = writes.dispatch(env, payload, 7, Failure)

    assert created["idempotent_replay"] is False
    assert replay["idempotent_replay"] is True
    assert created["result"]["model"] == "res.currency.rate"
    assert created["result"]["source_id"] == env.foreign_currency.id
    rate = env.data["res.currency.rate"][0]
    assert rate.company_id.id == env.company.id
    assert rate.currency_id.id == env.foreign_currency.id
    assert rate.inverse_company_rate == Decimal("0.125")
    assert sum(call[:2] == ("create", "res.currency.rate") for call in env.calls) == 1


def test_account_tag_header_lifecycle_and_replay() -> None:
    env = Env()
    create_parameters = {
        "name": "CLI VAT",
        "applicability": "taxes",
        "color": 3,
        "country_id": env.country.id,
    }
    create_payload = _accounting_reference_payload("account.tag.create", create_parameters)
    created = writes.dispatch(env, create_payload, 7, Failure)
    assert writes.dispatch(env, create_payload, 7, Failure)["idempotent_replay"]
    tag_id = created["result"]["id"]

    update_parameters = {"account_tag_id": tag_id, "changes": {"name": "CLI VAT 2"}}
    update_payload = _accounting_reference_payload("account.tag.update", update_parameters)
    writes.dispatch(env, update_payload, 7, Failure)
    assert writes.dispatch(env, update_payload, 7, Failure)["idempotent_replay"]
    lifecycle = {"account_tag_id": tag_id}
    archived = writes.dispatch(env, _accounting_reference_payload("account.tag.archive", lifecycle), 7, Failure)
    assert archived["result"]["state"] == "archived"
    restored = writes.dispatch(env, _accounting_reference_payload("account.tag.restore", lifecycle), 7, Failure)
    assert restored["result"]["state"] == "active"


def test_tax_group_create_update_and_replay() -> None:
    env = Env()
    create_parameters = {"name": "CLI VAT", "sequence": 10, "preceding_subtotal": None}
    create_payload = _accounting_reference_payload("tax.group.create", create_parameters)
    created = writes.dispatch(env, create_payload, 7, Failure)
    assert writes.dispatch(env, create_payload, 7, Failure)["idempotent_replay"]
    group_id = created["result"]["id"]
    group = env.models["account.tax.group"].browse(group_id)
    assert group.company_id.id == env.company.id
    assert group.country_id.id == env.country.id
    update_parameters = {"tax_group_id": group_id, "changes": {"preceding_subtotal": "Subtotal"}}
    update_payload = _accounting_reference_payload("tax.group.update", update_parameters)
    writes.dispatch(env, update_payload, 7, Failure)
    assert writes.dispatch(env, update_payload, 7, Failure)["idempotent_replay"]


def test_account_tag_lifecycle_rejects_foreign_country() -> None:
    env = Env()
    foreign = env.add("res.country", 392, name="Japan")
    env.tax_tag.country_id = Records(env, "res.country", [foreign])
    payload = _accounting_reference_payload(
        "account.tag.archive", {"account_tag_id": env.tax_tag.id}
    )
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, payload, 7, Failure)
    assert caught.value.code == "record_not_found"
    assert env.tax_tag.active is True


def test_tax_group_update_rejects_foreign_country() -> None:
    env = Env()
    create_parameters = {"name": "CLI VAT", "sequence": 10, "preceding_subtotal": None}
    created = writes.dispatch(
        env,
        _accounting_reference_payload("tax.group.create", create_parameters),
        7,
        Failure,
    )
    group = env.models["account.tax.group"].browse(created["result"]["id"])
    foreign = env.add("res.country", 392, name="Japan")
    group.records[0].country_id = Records(env, "res.country", [foreign])
    payload = _accounting_reference_payload(
        "tax.group.update",
        {"tax_group_id": group.id, "changes": {"sequence": 20}},
    )
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, payload, 7, Failure)
    assert caught.value.code == "record_not_found"
    assert group.sequence == 10


def test_tax_group_create_does_not_replay_foreign_country_natural_key() -> None:
    env = Env()
    foreign = env.add("res.country", 392, name="Japan")
    env.add(
        "account.tax.group",
        701,
        name="CLI VAT",
        sequence=10,
        preceding_subtotal=False,
        company_id=Records(env, "res.company", [env.company]),
        country_id=Records(env, "res.country", [foreign]),
    )
    parameters = {"name": "CLI VAT", "sequence": 10, "preceding_subtotal": None}
    payload = _accounting_reference_payload("tax.group.create", parameters)
    with pytest.raises(Failure) as caught:
        writes.dispatch(env, payload, 7, Failure)
    assert caught.value.code == "state_conflict"
    assert sum(
        call[:2] == ("create", "account.tax.group") for call in env.calls
    ) == 0


def test_cash_rounding_create_update_and_replay() -> None:
    env = Env()
    create_parameters = {
        "name": "CLI rounding",
        "rounding": "0.05",
        "strategy": "add_invoice_line",
        "rounding_method": "HALF-UP",
        "profit_account_id": env.income.id,
        "loss_account_id": env.expense.id,
    }
    create_payload = _accounting_reference_payload("cash_rounding.create", create_parameters)
    created = writes.dispatch(env, create_payload, 7, Failure)
    assert writes.dispatch(env, create_payload, 7, Failure)["idempotent_replay"]
    rounding_id = created["result"]["id"]
    update_parameters = {
        "cash_rounding_id": rounding_id,
        "changes": {"rounding": "0.1", "rounding_method": "UP"},
    }
    update_payload = _accounting_reference_payload("cash_rounding.update", update_parameters)
    writes.dispatch(env, update_payload, 7, Failure)
    assert writes.dispatch(env, update_payload, 7, Failure)["idempotent_replay"]


def test_reference_write_contract_rejects_cross_scope_shapes() -> None:
    assert not writes._valid_parameters("account.tag.create", {"name": "x"}, 7)
    assert not writes._valid_parameters(
        "account.tag.create",
        {"name": "x", "applicability": "accounts", "color": 0, "country_id": 156},
        7,
    )
    assert not writes._valid_parameters(
        "cash_rounding.create",
        {"name": "x", "rounding": "0.05", "strategy": "biggest_tax", "rounding_method": "UP", "profit_account_id": 101, "loss_account_id": None},
        7,
    )


def test_fiscal_year_create_update_and_replay() -> None:
    env = Env()
    create_parameters = {
        "name": "FY 2026",
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
    }
    create_payload = _accounting_reference_payload(
        "fiscal_year.create", create_parameters
    )

    created = writes.dispatch(env, create_payload, 7, Failure)
    replay = writes.dispatch(env, create_payload, 7, Failure)

    assert created["idempotent_replay"] is False
    assert replay["idempotent_replay"] is True
    assert created["result"]["model"] == "account.fiscal.year"
    assert created["result"]["state"] == "active"
    fiscal_year = env.models["account.fiscal.year"].browse(created["result"]["id"])
    assert fiscal_year.company_id.id == 7

    update_parameters = {
        "id": fiscal_year.id,
        "changes": {"name": "Fiscal 2026"},
    }
    update_payload = _accounting_reference_payload(
        "fiscal_year.update", update_parameters
    )
    updated = writes.dispatch(env, update_payload, 7, Failure)
    update_replay = writes.dispatch(env, update_payload, 7, Failure)

    assert updated["result"]["name"] == "Fiscal 2026"
    assert update_replay["idempotent_replay"] is True
    assert sum(
        call[:2] == ("create", "account.fiscal.year") for call in env.calls
    ) == 1
    assert sum(
        call[:2] == ("write", "account.fiscal.year") for call in env.calls
    ) == 1


def test_fiscal_year_rejects_child_company_and_invalid_merged_dates() -> None:
    env = Env()
    parent = env.add("res.company", 8, name="Parent")
    env.company.parent_id = Records(env, "res.company", [parent])
    parameters = {
        "name": "FY 2026",
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
    }

    with pytest.raises(Failure) as caught:
        writes.dispatch(
            env,
            _accounting_reference_payload("fiscal_year.create", parameters),
            7,
            Failure,
        )
    assert caught.value.code == "company_unavailable"
    assert not env.data["account.fiscal.year"]

    env.company.parent_id = Records(env, "res.company")
    created = writes.dispatch(
        env,
        _accounting_reference_payload("fiscal_year.create", parameters),
        7,
        Failure,
    )
    update = {
        "id": created["result"]["id"],
        "changes": {"date_from": "2027-01-01"},
    }
    with pytest.raises(Failure) as caught:
        writes.dispatch(
            env,
            _accounting_reference_payload("fiscal_year.update", update),
            7,
            Failure,
        )
    assert caught.value.code == "state_conflict"


def test_analytic_applicability_create_update_root_plan_and_replay() -> None:
    env = Env()
    create_parameters = {
        "plan_id": env.analytic_plan.id,
        "business_domain": "invoice",
        "applicability": "mandatory",
        "account_prefix": "40",
        "product_category_id": env.product_category.id,
    }
    create_payload = _accounting_reference_payload(
        "analytic.applicability.create", create_parameters
    )

    created = writes.dispatch(env, create_payload, 7, Failure)
    replay = writes.dispatch(env, create_payload, 7, Failure)

    assert replay["idempotent_replay"] is True
    assert created["result"]["model"] == "account.analytic.applicability"
    assert created["result"]["name"] is None
    rule = env.models["account.analytic.applicability"].browse(
        created["result"]["id"]
    )
    assert rule.company_id.id == 7
    assert rule.analytic_plan_id.id == env.analytic_plan.id

    other_root = env.add(
        "account.analytic.plan", 62, name="Departments", parent_id=False
    )
    other_root.root_id = Records(env, "account.analytic.plan", [other_root])
    update_parameters = {
        "id": rule.id,
        "changes": {"plan_id": other_root.id, "applicability": "optional"},
    }
    update_payload = _accounting_reference_payload(
        "analytic.applicability.update", update_parameters
    )
    writes.dispatch(env, update_payload, 7, Failure)
    assert writes.dispatch(env, update_payload, 7, Failure)["idempotent_replay"]
    assert rule.analytic_plan_id.id == other_root.id


def test_analytic_applicability_rejects_child_plan() -> None:
    env = Env()
    child_plan = env.add(
        "account.analytic.plan",
        62,
        name="Child",
        parent_id=Records(env, "account.analytic.plan", [env.analytic_plan]),
        root_id=Records(env, "account.analytic.plan", [env.analytic_plan]),
    )
    parameters = {
        "plan_id": child_plan.id,
        "business_domain": "general",
        "applicability": "optional",
        "account_prefix": None,
        "product_category_id": None,
    }

    with pytest.raises(Failure) as caught:
        writes.dispatch(
            env,
            _accounting_reference_payload(
                "analytic.applicability.create", parameters
            ),
            7,
            Failure,
        )
    assert caught.value.code == "record_not_found"
    assert not env.data["account.analytic.applicability"]


def test_analytic_applicability_update_rejects_another_rule_selector() -> None:
    env = Env()
    first_parameters = {
        "plan_id": env.analytic_plan.id,
        "business_domain": "invoice",
        "applicability": "mandatory",
        "account_prefix": "40",
        "product_category_id": env.product_category.id,
    }
    second_parameters = {
        **first_parameters,
        "business_domain": "bill",
        "account_prefix": "60",
    }
    first = writes.dispatch(
        env,
        _accounting_reference_payload(
            "analytic.applicability.create", first_parameters
        ),
        7,
        Failure,
    )
    writes.dispatch(
        env,
        _accounting_reference_payload(
            "analytic.applicability.create", second_parameters
        ),
        7,
        Failure,
    )
    update_parameters = {
        "id": first["result"]["id"],
        "changes": {"business_domain": "bill", "account_prefix": "60"},
    }

    with pytest.raises(Failure) as caught:
        writes.dispatch(
            env,
            _accounting_reference_payload(
                "analytic.applicability.update", update_parameters
            ),
            7,
            Failure,
        )

    assert caught.value.code == "state_conflict"
    assert sum(
        call[:2] == ("write", "account.analytic.applicability")
        for call in env.calls
    ) == 0


def _distribution_model_parameters(env: Env) -> dict[str, Any]:
    return {
        "sequence": 10,
        "account_prefix": "60",
        "partner_id": env.partner.id,
        "partner_category_id": env.partner_category.id,
        "product_id": env.product.id,
        "product_category_id": env.product_category.id,
        "analytic_distribution": {str(env.analytic.id): "100"},
    }


def test_analytic_distribution_model_create_update_and_replay() -> None:
    env = Env()
    create_parameters = _distribution_model_parameters(env)
    create_payload = _accounting_reference_payload(
        "analytic.distribution_model.create", create_parameters
    )

    created = writes.dispatch(env, create_payload, 7, Failure)
    replay = writes.dispatch(env, create_payload, 7, Failure)

    assert created["idempotent_replay"] is False
    assert replay["idempotent_replay"] is True
    assert created["result"]["model"] == "account.analytic.distribution.model"
    model = env.models["account.analytic.distribution.model"].browse(
        created["result"]["id"]
    )
    assert model.company_id.id == 7
    assert model.product_id.id == env.product.id
    assert model.analytic_distribution == {str(env.analytic.id): 100.0}

    update_parameters = {
        "id": model.id,
        "changes": {"sequence": 20, "analytic_distribution": None},
    }
    update_payload = _accounting_reference_payload(
        "analytic.distribution_model.update", update_parameters
    )
    updated = writes.dispatch(env, update_payload, 7, Failure)
    update_replay = writes.dispatch(env, update_payload, 7, Failure)

    assert updated["idempotent_replay"] is False
    assert update_replay["idempotent_replay"] is True
    assert model.sequence == 20
    assert model.analytic_distribution is False


def test_analytic_distribution_model_rejects_cross_company_references() -> None:
    env = Env()
    foreign_company = env.add("res.company", 8, name="Foreign")
    foreign_product = env.add(
        "product.product", 42, name="Foreign Product", company_id=foreign_company
    )
    parameters = _distribution_model_parameters(env)
    parameters["product_id"] = foreign_product.id

    with pytest.raises(Failure) as caught:
        writes.dispatch(
            env,
            _accounting_reference_payload(
                "analytic.distribution_model.create", parameters
            ),
            7,
            Failure,
        )
    assert caught.value.code == "record_not_found"

    env = Env()
    foreign_company = env.add("res.company", 8, name="Foreign")
    foreign_account = env.add(
        "account.analytic.account",
        64,
        name="Foreign Analytic",
        company_id=foreign_company,
        plan_id=Records(env, "account.analytic.plan", [env.analytic_plan]),
        root_plan_id=Records(env, "account.analytic.plan", [env.analytic_plan]),
    )
    parameters = _distribution_model_parameters(env)
    parameters["analytic_distribution"] = {str(foreign_account.id): "100"}
    with pytest.raises(Failure) as caught:
        writes.dispatch(
            env,
            _accounting_reference_payload(
                "analytic.distribution_model.create", parameters
            ),
            7,
            Failure,
        )
    assert caught.value.code == "record_not_found"


def test_distribution_model_same_selector_allows_distinct_rules_and_replays_exact() -> None:
    env = Env()
    first_parameters = _distribution_model_parameters(env)
    second_parameters = {**first_parameters, "sequence": 20}

    first = writes.dispatch(
        env,
        _accounting_reference_payload(
            "analytic.distribution_model.create", first_parameters
        ),
        7,
        Failure,
    )
    second = writes.dispatch(
        env,
        _accounting_reference_payload(
            "analytic.distribution_model.create", second_parameters
        ),
        7,
        Failure,
    )
    replay = writes.dispatch(
        env,
        _accounting_reference_payload(
            "analytic.distribution_model.create", second_parameters
        ),
        7,
        Failure,
    )

    assert first["result"]["id"] != second["result"]["id"]
    assert replay["result"]["id"] == second["result"]["id"]
    assert replay["idempotent_replay"] is True
    assert len(env.data["account.analytic.distribution.model"]) == 2

    duplicate = env.models["account.analytic.distribution.model"].browse(
        second["result"]["id"]
    )
    env.add(
        "account.analytic.distribution.model",
        2000,
        sequence=duplicate.sequence,
        account_prefix=duplicate.account_prefix,
        partner_id=duplicate.partner_id,
        partner_category_id=duplicate.partner_category_id,
        product_id=duplicate.product_id,
        product_categ_id=duplicate.product_categ_id,
        analytic_distribution=dict(duplicate.analytic_distribution),
        company_id=duplicate.company_id,
    )
    with pytest.raises(Failure) as caught:
        writes.dispatch(
            env,
            _accounting_reference_payload(
                "analytic.distribution_model.create", second_parameters
            ),
            7,
            Failure,
        )
    assert caught.value.code == "state_conflict"


def test_accounting_configuration_writes_require_manager_without_sudo() -> None:
    env = Env()
    env.denied_group = "account.group_account_manager"
    parameters = {
        "name": "FY 2026",
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
    }

    result = writes.dispatch(
        env,
        _accounting_reference_payload("fiscal_year.create", parameters),
        7,
        Failure,
    )

    assert result["access_allowed"] is False
    assert not env.data["account.fiscal.year"]
    assert writes._GROUPS["analytic.applicability.create"] == (
        "account.group_account_manager"
    )
    assert writes._GROUPS["analytic.distribution_model.update"] == (
        "account.group_account_manager"
    )


def test_account_group_create_update_use_root_company_and_replay() -> None:
    env = Env()
    create_parameters = {
        "name": "Current assets",
        "code_prefix_start": "10",
        "code_prefix_end": "19",
    }
    create_payload = _accounting_reference_payload(
        "account.group.create", create_parameters
    )

    created = writes.dispatch(env, create_payload, 7, Failure)
    replay = writes.dispatch(env, create_payload, 7, Failure)

    group_id = created["result"]["id"]
    group = env.models["account.group"].browse(group_id)
    assert replay["idempotent_replay"] is True
    assert group.company_id.id == env.company.id
    assert group.code_prefix_start == "10"
    update_parameters = {
        "account_group_id": group_id,
        "changes": {"name": "Liquid assets"},
    }
    update_payload = _accounting_reference_payload(
        "account.group.update", update_parameters
    )

    updated = writes.dispatch(env, update_payload, 7, Failure)
    update_replay = writes.dispatch(env, update_payload, 7, Failure)

    assert updated["result"]["name"] == "Liquid assets"
    assert update_replay["idempotent_replay"] is True
    group_writes = [call for call in env.calls if call[:2] == ("write", "account.group")]
    assert len(group_writes) == 1


def test_tax_repartition_lines_replace_uses_native_commands_and_replays() -> None:
    env = Env()
    parameters = _tax_repartition_parameters(env)
    payload = _accounting_reference_payload(
        "tax.repartition_lines.replace", parameters
    )

    replaced = writes.dispatch(env, payload, 7, Failure)
    replay = writes.dispatch(env, payload, 7, Failure)

    assert replaced["idempotent_replay"] is False
    assert replay["idempotent_replay"] is True
    assert len(replaced["result"]["line_ids"]) == 4
    assert [line.document_type for line in env.tax.invoice_repartition_line_ids] == [
        "invoice",
        "invoice",
    ]
    assert [line.repartition_type for line in env.tax.invoice_repartition_line_ids] == [
        "base",
        "tax",
    ]
    assert env.tax.invoice_repartition_line_ids.records[1].account_id.id == (
        env.expense.id
    )
    assert env.tax.invoice_repartition_line_ids.records[1].tag_ids.ids == [
        env.tax_tag.id
    ]
    tax_writes = [call for call in env.calls if call[:2] == ("write", "account.tax")]
    assert len(tax_writes) == 1
    commands = tax_writes[0][3]["repartition_line_ids"]
    assert [command[0] for command in commands] == [5, 0, 0, 0, 0]
    assert [command[2].get("document_type") for command in commands[1:]] == [
        "invoice",
        "invoice",
        "refund",
        "refund",
    ]


def test_reconciliation_model_header_lines_lifecycle_and_replay() -> None:
    env = Env()
    create_parameters = {
        "name": "Bank fees",
        "sequence": 10,
        "trigger": "manual",
        "match_journal_ids": [env.bank_journal.id],
        "match_partner_ids": [env.partner.id],
        "match_amount": {
            "operator": "lower",
            "minimum": None,
            "maximum": "500",
        },
        "match_label": {"operator": "contains", "value": "fee"},
    }
    create_payload = _accounting_reference_payload(
        "reconciliation.model.create", create_parameters
    )
    created = writes.dispatch(env, create_payload, 7, Failure)
    assert writes.dispatch(env, create_payload, 7, Failure)["idempotent_replay"]
    model_id = created["result"]["id"]

    update_parameters = {
        "reconciliation_model_id": model_id,
        "changes": {
            "match_amount": {
                "operator": "between",
                "minimum": "10",
                "maximum": "20",
            },
            "match_label": {"operator": "match_regex", "value": "^fee"},
        },
    }
    update_payload = _accounting_reference_payload(
        "reconciliation.model.update", update_parameters
    )
    writes.dispatch(env, update_payload, 7, Failure)
    assert writes.dispatch(env, update_payload, 7, Failure)["idempotent_replay"]

    line_parameters = {
        "reconciliation_model_id": model_id,
        "lines": [
            {
                "sequence": 10,
                "account_id": env.expense.id,
                "partner_id": env.partner.id,
                "label": "Bank fee",
                "amount_type": "fixed",
                "amount_string": "10",
                "tax_ids": [env.tax.id],
                "analytic_distribution": [
                    {
                        "analytic_account_ids": [
                            env.analytic.id,
                            env.analytic_two.id,
                        ],
                        "percentage": "100",
                    }
                ],
            }
        ],
    }
    line_payload = _accounting_reference_payload(
        "reconciliation.model.lines.replace", line_parameters
    )
    lines_result = writes.dispatch(env, line_payload, 7, Failure)
    assert writes.dispatch(env, line_payload, 7, Failure)["idempotent_replay"]
    assert len(lines_result["result"]["line_ids"]) == 1
    model = env.models["account.reconcile.model"].browse(model_id)
    analytic_key = f"{env.analytic.id},{env.analytic_two.id}"
    assert model.line_ids.records[0].analytic_distribution == {analytic_key: 100.0}

    archive_parameters = {"reconciliation_model_id": model_id}
    archive_payload = _accounting_reference_payload(
        "reconciliation.model.archive", archive_parameters
    )
    archived = writes.dispatch(env, archive_payload, 7, Failure)
    assert writes.dispatch(env, archive_payload, 7, Failure)["idempotent_replay"]
    assert archived["result"]["state"] == "archived"
    restore_payload = _accounting_reference_payload(
        "reconciliation.model.restore", archive_parameters
    )
    restored = writes.dispatch(env, restore_payload, 7, Failure)
    assert writes.dispatch(env, restore_payload, 7, Failure)["idempotent_replay"]
    assert restored["result"]["state"] == "active"

    model_writes = [
        call for call in env.calls if call[:2] == ("write", "account.reconcile.model")
    ]
    assert len(model_writes) == 4
