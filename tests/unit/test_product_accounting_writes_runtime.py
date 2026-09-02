from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge import core_writes_runtime as writes


class Failure(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        exit_code: int,
        retryable: bool,
        details: dict[str, Any],
    ) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code
        self.retryable = retryable
        self.details = details


def _relation_id(value: Any) -> Any:
    return getattr(value, "id", value)


class Records:
    def __init__(self, model: Model, records: list[Record] | None = None) -> None:
        self.model = model
        self.records = records or []

    @property
    def ids(self) -> list[int]:
        return [record.id for record in self.records]

    @property
    def id(self) -> int | None:
        return self.records[0].id if len(self.records) == 1 else None

    def __bool__(self) -> bool:
        return bool(self.records)

    def __len__(self) -> int:
        return len(self.records)

    def __iter__(self):
        return iter(self.records)

    def __getattr__(self, name: str) -> Any:
        if len(self.records) != 1:
            raise AttributeError(name)
        return getattr(self.records[0], name)

    def with_company(self, company_id: int) -> Records:
        assert company_id == 1
        return self

    def with_context(self, **context: Any) -> Records:
        assert context == {"active_test": False, "allowed_company_ids": [1]}
        return self


class Record:
    def __init__(self, model: Model, record_id: int, **values: Any) -> None:
        self._model = model
        self.id = record_id
        for field_name, value in values.items():
            setattr(self, field_name, value)

    def with_company(self, company_id: int) -> Record:
        assert company_id == 1
        self._model.env.calls.append(("with_company", self._model.name, self.id))
        return self

    def with_context(self, **context: Any) -> Record:
        assert context == {"active_test": False, "allowed_company_ids": [1]}
        return self

    def invalidate_recordset(self, fields: list[str]) -> None:
        self._model.env.calls.append(("invalidate", self._model.name, self.id, fields))

    def write(self, values: dict[str, Any]) -> None:
        self._model.env.calls.append(("write", self._model.name, self.id, values))
        if self._model.name == "product.template":
            variant = self.product_variant_ids.records[0]
            for field_name, value in values.items():
                if field_name == "default_code":
                    variant.default_code = value
                elif field_name == "barcode":
                    variant.barcode = value or False
                elif field_name == "categ_id":
                    self.categ_id = self._model.env.record("product.category", value)
                elif field_name == "uom_id":
                    self.uom_id = self._model.env.record("uom.uom", value)
                elif field_name in {"taxes_id", "supplier_taxes_id"}:
                    tax_ids = value[0][2]
                    setattr(
                        self,
                        field_name,
                        Records(
                            self._model.env.models["account.tax"],
                            [
                                self._model.env.record("account.tax", tax_id)
                                for tax_id in tax_ids
                            ],
                        ),
                    )
                elif field_name in {
                    "property_account_income_id",
                    "property_account_expense_id",
                }:
                    setattr(
                        self,
                        field_name,
                        self._model.env.record("account.account", value)
                        if value
                        else False,
                    )
                else:
                    setattr(self, field_name, value)
        elif self._model.name == "product.category":
            for field_name, value in values.items():
                setattr(
                    self,
                    field_name,
                    self._model.env.record("account.account", value)
                    if value
                    else False,
                )
        else:
            for field_name, value in values.items():
                setattr(self, field_name, value)

    def copy(self, default: dict[str, Any]) -> Records:
        assert self._model.name == "product.template"
        self._model.env.calls.append(("copy", self.id, default))
        source_variant = self.product_variant_ids.records[0]
        return self._model.env.add_product(
            name=default["name"],
            default_code=default["default_code"],
            company=self._model.env.record("res.company", default["company_id"]),
            product_type=self.type,
            category=self.categ_id,
            uom=self.uom_id,
            barcode=False,
            sale_ok=self.sale_ok,
            purchase_ok=self.purchase_ok,
            list_price=self.list_price,
            standard_price=source_variant.standard_price,
        )[0]

    def action_archive(self) -> None:
        assert self._model.name == "product.template"
        self._model.env.calls.append(("action_archive", self.id))
        self.active = False
        self.product_variant_ids.records[0].active = False

    def action_unarchive(self) -> None:
        assert self._model.name in {"product.template", "product.product"}
        self._model.env.calls.append(("action_unarchive", self._model.name, self.id))
        self.active = True
        if self._model.name == "product.product":
            self.product_tmpl_id.active = True


class Model:
    def __init__(self, env: Env, name: str) -> None:
        self.env = env
        self.name = name
        self.records: list[Record] = []

    def with_company(self, company_id: int) -> Model:
        assert company_id == 1
        return self

    def with_context(self, **context: Any) -> Model:
        assert context == {"active_test": False, "allowed_company_ids": [1]}
        return self

    def has_access(self, operation: str) -> bool:
        self.env.calls.append(("has_access", self.name, operation))
        return True

    def browse(self, record_ids: int | list[int]) -> Records:
        ids = [record_ids] if isinstance(record_ids, int) else record_ids
        return Records(self, [record for record in self.records if record.id in ids])

    def search_count(self, domain: list[Any], limit: int | None = None) -> int:
        return len(self.search(domain, limit=limit))

    def search(self, domain: list[Any], limit: int | None = None) -> Records:
        selected = [record for record in self.records if _matches(record, domain)]
        if limit is not None:
            selected = selected[:limit]
        return Records(self, selected)

    def create(self, values: dict[str, Any]) -> Records:
        assert self.name == "product.template"
        self.env.calls.append(("create", self.name, values))
        return self.env.add_product(
            name=values["name"],
            default_code=values["default_code"],
            company=self.env.record("res.company", values["company_id"]),
            product_type=values["type"],
            category=self.env.record("product.category", values["categ_id"]),
            uom=self.env.record("uom.uom", values["uom_id"]),
            barcode=values["barcode"],
            sale_ok=values["sale_ok"],
            purchase_ok=values["purchase_ok"],
            list_price=values["list_price"],
        )[0]


def _matches(record: Record, domain: list[Any]) -> bool:
    for field_name, operator, expected in domain:
        actual = getattr(record, field_name)
        if isinstance(actual, Records):
            actual = actual.ids
        else:
            actual = _relation_id(actual)
        if operator == "=":
            if actual != expected:
                return False
        elif operator == "in":
            if isinstance(actual, list):
                if not set(actual) & set(expected):
                    return False
            elif actual not in expected:
                return False
        else:
            raise AssertionError(operator)
    return True


class Registry:
    def __init__(self, env: Env) -> None:
        self.env = env

    def get(self, name: str) -> Model | None:
        return self.env.models.get(name)


class User:
    def __init__(self) -> None:
        self.groups = {
            "product.group_product_manager",
            "stock.group_stock_manager",
        }

    def has_group(self, group: str) -> bool:
        return group in self.groups


class Env:
    uid = 5

    def __init__(self) -> None:
        self.calls: list[tuple[Any, ...]] = []
        self.next_id = 1000
        self.models = {
            name: Model(self, name)
            for name in (
                "res.company",
                "product.category",
                "uom.uom",
                "product.template",
                "product.product",
                "product.value",
                "stock.warehouse.orderpoint",
                "account.account",
                "account.tax",
            )
        }
        self.registry = Registry(self)
        self.user = User()
        self.company = self.add("res.company", 1, name="Main Company")
        self.other_company = self.add("res.company", 2, name="Other Company")
        self.category = self.add(
            "product.category",
            10,
            name="Services",
            complete_name="Services",
            property_account_income_categ_id=False,
            property_account_expense_categ_id=False,
        )
        self.uom = self.add("uom.uom", 20, name="Units", active=True)
        self.income = self.add_account(30, "income")
        self.expense = self.add_account(31, "expense")
        self.receivable = self.add_account(32, "asset_receivable")
        self.foreign_account = self.add_account(
            33, "income", company=self.other_company
        )
        self.sale_tax = self.add(
            "account.tax",
            40,
            name="Sales Tax",
            company_id=self.company,
            type_tax_use="sale",
            active=True,
        )
        self.purchase_tax = self.add(
            "account.tax",
            41,
            name="Purchase Tax",
            company_id=self.company,
            type_tax_use="purchase",
            active=True,
        )
        self.foreign_tax = self.add(
            "account.tax",
            42,
            name="Foreign Tax",
            company_id=self.other_company,
            type_tax_use="sale",
            active=True,
        )

    def __getitem__(self, name: str) -> Model:
        return self.models[name]

    def add(self, model_name: str, record_id: int, **values: Any) -> Record:
        record = Record(self.models[model_name], record_id, **values)
        self.models[model_name].records.append(record)
        return record

    def record(self, model_name: str, record_id: int) -> Record:
        matches = [
            record
            for record in self.models[model_name].records
            if record.id == record_id
        ]
        assert len(matches) == 1
        return matches[0]

    def add_account(
        self, record_id: int, account_type: str, *, company: Record | None = None
    ) -> Record:
        owner = company or self.company
        return self.add(
            "account.account",
            record_id,
            name=f"Account {record_id}",
            company_ids=Records(self.models["res.company"], [owner]),
            account_type=account_type,
            active=True,
        )

    def add_product(
        self,
        *,
        name: str = "Consulting",
        default_code: str = "CONSULT",
        company: Record | None = None,
        product_type: str = "service",
        category: Record | None = None,
        uom: Record | None = None,
        barcode: str | bool = False,
        sale_ok: bool = True,
        purchase_ok: bool = True,
        list_price: Any = Decimal(0),
        standard_price: Any = Decimal(0),
    ) -> tuple[Records, Record]:
        self.next_id += 1
        template_id = self.next_id
        self.next_id += 1
        product_id = self.next_id
        owner = company or self.company
        template = self.add(
            "product.template",
            template_id,
            name=name,
            type=product_type,
            categ_id=category or self.category,
            uom_id=uom or self.uom,
            company_id=owner,
            active=True,
            is_storable=False,
            attribute_line_ids=Records(self.models["product.template"]),
            sale_ok=sale_ok,
            purchase_ok=purchase_ok,
            list_price=Decimal(str(list_price)),
            property_account_income_id=False,
            property_account_expense_id=False,
            taxes_id=Records(self.models["account.tax"]),
            supplier_taxes_id=Records(self.models["account.tax"]),
        )
        product = self.add(
            "product.product",
            product_id,
            name=name,
            product_tmpl_id=template,
            company_id=owner,
            active=True,
            default_code=default_code,
            barcode=barcode,
            standard_price=Decimal(str(standard_price)),
        )
        template.product_variant_ids = Records(
            self.models["product.product"], [product]
        )
        return Records(self.models["product.template"], [template]), product


def _payload(capability_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
    return {
        "capability_id": capability_id,
        "company_id": 1,
        "idempotency_key": writes._deterministic_key(capability_id, parameters, 1),
        "confirmation": capability_id,
        "parameters": parameters,
    }


def _dispatch(
    env: Env, capability_id: str, parameters: dict[str, Any]
) -> dict[str, Any]:
    return writes.dispatch(env, _payload(capability_id, parameters), 1, Failure)


def _create_parameters(**overrides: Any) -> dict[str, Any]:
    return {
        "name": "Consulting",
        "default_code": "CONSULT",
        "product_type": "service",
        "category_id": 10,
        "uom_id": 20,
        **overrides,
    }


def test_create_and_duplicate_use_serial_company_code_natural_key_rechecks() -> None:
    env = Env()
    created = _dispatch(env, "product.create", _create_parameters())
    assert created["idempotent_replay"] is False
    assert created["result"]["model"] == "product.product"
    assert created["result"]["source_id"] > 0
    assert created["result"]["state"] == "active"
    assert (
        _dispatch(env, "product.create", _create_parameters())["idempotent_replay"]
        is True
    )

    duplicate_parameters = {
        "product_id": created["result"]["id"],
        "name": "Consulting Copy",
        "default_code": "CONSULT-COPY",
    }
    duplicated = _dispatch(env, "product.duplicate", duplicate_parameters)
    assert duplicated["idempotent_replay"] is False
    assert duplicated["result"]["id"] != created["result"]["id"]
    assert (
        _dispatch(env, "product.duplicate", duplicate_parameters)["idempotent_replay"]
        is True
    )


def test_create_and_duplicate_disclose_preexisting_exact_match_attribution_limit() -> (
    None
):
    create_env = Env()
    create_env.add_product()
    created = _dispatch(create_env, "product.create", _create_parameters())
    assert created["idempotent_replay"] is True
    assert not any(
        call[:2] == ("create", "product.template") for call in create_env.calls
    )

    duplicate_env = Env()
    _, source = duplicate_env.add_product(default_code="SOURCE", barcode="SOURCE-EAN")
    duplicate_env.add_product(name="Consulting Copy", default_code="COPY")
    duplicated = _dispatch(
        duplicate_env,
        "product.duplicate",
        {
            "product_id": source.id,
            "name": "Consulting Copy",
            "default_code": "COPY",
        },
    )
    assert duplicated["idempotent_replay"] is True
    assert not any(call[0] == "copy" for call in duplicate_env.calls)


def test_update_archive_restore_and_cost_recheck_current_target_state() -> None:
    env = Env()
    _, product = env.add_product()
    update = {
        "product_id": product.id,
        "changes": {"name": "Advisory", "list_price": "125.5"},
    }
    assert _dispatch(env, "product.update", update)["idempotent_replay"] is False
    assert _dispatch(env, "product.update", update)["idempotent_replay"] is True

    cost = {"product_id": product.id, "standard_price": "42.75"}
    assert _dispatch(env, "product.cost.update", cost)["idempotent_replay"] is False
    assert _dispatch(env, "product.cost.update", cost)["idempotent_replay"] is True

    archived = _dispatch(env, "product.archive", {"product_id": product.id})
    assert archived["result"]["state"] == "archived"
    assert ("action_archive", product.product_tmpl_id.id) in env.calls
    assert (
        _dispatch(env, "product.archive", {"product_id": product.id})[
            "idempotent_replay"
        ]
        is True
    )
    restored = _dispatch(env, "product.restore", {"product_id": product.id})
    assert restored["result"]["state"] == "active"
    assert ("action_unarchive", "product.product", product.id) in env.calls
    assert ("has_access", "stock.warehouse.orderpoint", "read") in env.calls
    assert ("has_access", "stock.warehouse.orderpoint", "write") in env.calls


@pytest.mark.parametrize("capability_id", ["product.archive", "product.restore"])
def test_archive_and_restore_require_stock_manager_access(capability_id: str) -> None:
    env = Env()
    _, product = env.add_product()
    env.user.groups.remove("stock.group_stock_manager")
    env.user.groups.add("stock.group_stock_user")

    page = _dispatch(env, capability_id, {"product_id": product.id})

    assert page["module_installed"] is True
    assert page["access_allowed"] is False
    assert page["result"] is None
    assert not any(call[0] in {"action_archive", "action_unarchive"} for call in env.calls)


def test_product_and_category_profiles_validate_and_write_company_values() -> None:
    env = Env()
    _, product = env.add_product()
    product_parameters = {
        "product_id": product.id,
        "changes": {
            "income_account_id": env.income.id,
            "expense_account_id": env.expense.id,
            "sale_tax_ids": [env.sale_tax.id],
            "purchase_tax_ids": [env.purchase_tax.id],
        },
    }
    updated = _dispatch(env, "product.accounting_profile.update", product_parameters)
    assert updated["idempotent_replay"] is False
    assert (
        _dispatch(env, "product.accounting_profile.update", product_parameters)[
            "idempotent_replay"
        ]
        is True
    )

    category_parameters = {
        "category_id": env.category.id,
        "changes": {
            "income_account_id": env.income.id,
            "expense_account_id": env.expense.id,
        },
    }
    category = _dispatch(
        env,
        "product.category.accounting_profile.update",
        category_parameters,
    )
    assert category["result"]["model"] == "product.category"
    assert category["result"]["source_id"] is None
    assert (
        _dispatch(
            env,
            "product.category.accounting_profile.update",
            category_parameters,
        )["idempotent_replay"]
        is True
    )


@pytest.mark.parametrize(
    "mutation",
    ["foreign_company", "multiple_variants", "inventory", "combo", "attributes"],
)
def test_product_targets_reject_records_outside_the_fixed_scope(
    mutation: str,
) -> None:
    env = Env()
    _, product = env.add_product()
    template = product.product_tmpl_id
    if mutation == "foreign_company":
        product.company_id = env.other_company
        template.company_id = env.other_company
    elif mutation == "multiple_variants":
        _, second = env.add_product(default_code="SECOND")
        second.product_tmpl_id = template
        template.product_variant_ids = Records(
            env.models["product.product"], [product, second]
        )
    elif mutation == "inventory":
        template.is_storable = True
    elif mutation == "combo":
        template.type = "combo"
    else:
        template.attribute_line_ids = Records(
            env.models["product.template"], [template]
        )

    with pytest.raises(Failure) as caught:
        _dispatch(
            env,
            "product.update",
            {"product_id": product.id, "changes": {"name": "Blocked"}},
        )
    assert caught.value.code == "record_not_found"


@pytest.mark.parametrize(
    ("changes", "expected_code"),
    [
        ({"income_account_id": 32}, "record_not_found"),
        ({"income_account_id": 33}, "record_not_found"),
        ({"sale_tax_ids": [41]}, "record_not_found"),
        ({"sale_tax_ids": [42]}, "record_not_found"),
    ],
)
def test_accounting_profile_rejects_excluded_or_cross_company_references(
    changes: dict[str, Any], expected_code: str
) -> None:
    env = Env()
    _, product = env.add_product()
    with pytest.raises(Failure) as caught:
        _dispatch(
            env,
            "product.accounting_profile.update",
            {"product_id": product.id, "changes": changes},
        )
    assert caught.value.code == expected_code


def test_create_rejects_missing_or_inactive_references() -> None:
    env = Env()
    env.uom.active = False
    with pytest.raises(Failure) as caught:
        _dispatch(env, "product.create", _create_parameters())
    assert caught.value.code == "record_not_found"


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    [
        (
            "product.create",
            {**_create_parameters(), "list_price": "-1"},
        ),
        (
            "product.cost.update",
            {"product_id": 1001, "standard_price": "-1"},
        ),
    ],
)
def test_product_money_values_must_be_nonnegative(
    capability_id: str, parameters: dict[str, Any]
) -> None:
    env = Env()
    with pytest.raises(Failure) as caught:
        _dispatch(env, capability_id, parameters)
    assert caught.value.code == "bridge_protocol_error"
