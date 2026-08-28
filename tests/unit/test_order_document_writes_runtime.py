from __future__ import annotations

import copy
from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge import core_writes_runtime as writes

SALE_CAPABILITIES = (
    "sale.order.create",
    "sale.order.update_draft",
    "sale.order.lines.replace",
    "sale.order.confirm",
    "sale.order.cancel",
    "sale.order.reset_to_draft",
)
PURCHASE_CAPABILITIES = (
    "purchase.order.create",
    "purchase.order.update_draft",
    "purchase.order.lines.replace",
    "purchase.order.confirm",
    "purchase.order.cancel",
    "purchase.order.reset_to_draft",
)
RESULT_KEYS = {
    "model",
    "id",
    "name",
    "state",
    "company_id",
    "move_type",
    "source_id",
    "line_ids",
    "partial_reconcile_ids",
    "full_reconcile_id",
    "reconciled",
}


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


class Record:
    def __init__(self, env: Env, model: str, record_id: int, **values: Any) -> None:
        self.env = env
        self._name = model
        self.id = record_id
        for name, value in values.items():
            setattr(self, name, value)

    def write(self, values: dict[str, Any]) -> bool:
        if self._name not in {"sale.order", "purchase.order"}:
            raise AssertionError(f"unexpected write: {self._name}")
        self.env.calls.append(("write", self._name, self.id, copy.deepcopy(values)))
        self.env.apply_order_values(self, values)
        return True

    def action_confirm(self) -> None:
        self.env.calls.append(("action_confirm", self.id))
        self.state = "sale"

    def action_cancel(self) -> None:
        self.env.calls.append(("action_cancel", self.id))
        self.state = "cancel"

    def action_draft(self) -> None:
        self.env.calls.append(("action_draft", self.id))
        self.state = "draft"

    def button_confirm(self) -> None:
        self.env.calls.append(("button_confirm", self.id))
        self.state = self.env.purchase_confirm_state

    def button_cancel(self) -> None:
        self.env.calls.append(("button_cancel", self.id))
        self.state = "cancel"

    def button_draft(self) -> None:
        self.env.calls.append(("button_draft", self.id))
        self.state = "draft"

    def sudo(self, *_args: Any, **_kwargs: Any) -> None:
        raise AssertionError(f"order writes must never sudo {self._name}")


class Records:
    def __init__(
        self, env: Env, model: str, records: list[Record] | None = None
    ) -> None:
        self.env = env
        self.model = model
        self.records = list(records or [])

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

    def filtered(self, predicate: Any) -> Records:
        return Records(
            self.env,
            self.model,
            [record for record in self.records if predicate(record)],
        )

    def sudo(self, *_args: Any, **_kwargs: Any) -> None:
        raise AssertionError(f"order writes must never sudo {self.model}")


def _relation_value(value: Any) -> Any:
    if isinstance(value, Record):
        return value.id
    if isinstance(value, Records):
        return value.ids
    return value


def _matches(record: Record, domain: list[Any]) -> bool:
    for term in domain:
        if not isinstance(term, tuple):
            continue
        field_name, operator, expected = term
        actual = _relation_value(getattr(record, field_name, False))
        if operator == "=":
            if isinstance(actual, list):
                if expected not in actual:
                    return False
            elif actual != expected:
                return False
        elif operator == "in":
            if isinstance(actual, list):
                if not set(actual).intersection(expected):
                    return False
            elif actual not in expected:
                return False
        elif operator == "ilike":
            if str(expected).casefold() not in str(actual).casefold():
                return False
        else:
            raise AssertionError(f"unsupported fake domain operator: {operator}")
    return True


class Model:
    def __init__(self, env: Env, name: str) -> None:
        self.env = env
        self.name = name

    def has_access(self, operation: str) -> bool:
        self.env.calls.append(("has_access", self.name, operation))
        return self.env.denied_access != (self.name, operation)

    def with_company(self, company_id: int) -> Model:
        self.env.calls.append(("with_company", self.name, company_id))
        return self

    def with_context(self, **context: Any) -> Model:
        self.env.calls.append(("with_context", self.name, copy.deepcopy(context)))
        return self

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
        selected = [
            record for record in self.env.data[self.name] if _matches(record, domain)
        ]
        if limit is not None:
            selected = selected[:limit]
        return Records(self.env, self.name, selected)

    def browse(self, ids: int | list[int]) -> Records:
        requested = [ids] if isinstance(ids, int) else ids
        return Records(
            self.env,
            self.name,
            [record for record in self.env.data[self.name] if record.id in requested],
        )

    def create(self, values: dict[str, Any]) -> Records:
        if self.name not in {"sale.order", "purchase.order"}:
            raise AssertionError(f"unexpected create: {self.name}")
        self.env.calls.append(("create", self.name, copy.deepcopy(values)))
        return Records(self.env, self.name, [self.env.new_order(self.name, values)])

    def sudo(self, *_args: Any, **_kwargs: Any) -> None:
        raise AssertionError(f"order writes must never sudo {self.name}")


class Registry:
    def __init__(self, env: Env) -> None:
        self.env = env

    def get(self, model: str) -> Model | None:
        self.env.calls.append(("registry", model))
        return None if model == self.env.missing_model else self.env.models.get(model)


class User:
    def __init__(self, env: Env) -> None:
        self.env = env

    def has_group(self, group: str) -> bool:
        self.env.calls.append(("has_group", group))
        return group != self.env.denied_group


class Env:
    uid = 5

    def __init__(self) -> None:
        self.calls: list[tuple[Any, ...]] = []
        self.denied_group: str | None = None
        self.denied_access: tuple[str, str] | None = None
        self.missing_model: str | None = None
        self.purchase_confirm_state = "purchase"
        model_names = set().union(
            *(writes._MODELS[capability_id] for capability_id in SALE_CAPABILITIES)
        ) | set().union(
            *(writes._MODELS[capability_id] for capability_id in PURCHASE_CAPABILITIES)
        )
        self.models = {name: Model(self, name) for name in model_names}
        self.data: dict[str, list[Record]] = {name: [] for name in model_names}
        self.registry = Registry(self)
        self.user = User(self)
        self.next_id = 1000
        self.next_line_id = 5000

        self.company = self.add("res.company", 7, name="Fixture Company")
        self.partner = self.add(
            "res.partner", 31, name="Order Partner", company_id=False
        )
        self.pricelist = self.add(
            "product.pricelist", 41, name="USD", company_id=False
        )
        self.payment_term = self.add(
            "account.payment.term", 42, name="Net 30", company_id=False
        )
        self.currency = self.add("res.currency", 6, name="USD", active=True)
        self.picking_type = self.add(
            "stock.picking.type",
            2,
            name="Receipts",
            company_id=self.company,
            code="incoming",
        )
        self.incoterm = self.add("account.incoterms", 3, name="FOB")
        self.product = self.add(
            "product.product",
            51,
            name="Service",
            company_id=False,
            sale_ok=True,
            purchase_ok=True,
        )
        self.uom = self.add("uom.uom", 1, name="Units")
        self.sale_tax = self.add(
            "account.tax",
            8,
            name="Sale Tax",
            company_id=self.company,
            type_tax_use="sale",
        )
        self.purchase_tax = self.add(
            "account.tax",
            9,
            name="Purchase Tax",
            company_id=self.company,
            type_tax_use="purchase",
        )
        self.sale_order = self.add_order("sale.order", 101, "draft", [sale_line()])
        self.purchase_order = self.add_order(
            "purchase.order", 201, "draft", [purchase_line()]
        )

    def __getitem__(self, model: str) -> Model:
        return self.models[model]

    def add(self, model: str, record_id: int, **values: Any) -> Record:
        record = Record(self, model, record_id, **values)
        self.data[model].append(record)
        return record

    def _relation(self, model: str, value: Any) -> Record | bool:
        if value in (None, False):
            return False
        if isinstance(value, Record):
            return value
        selected = self[model].browse(value)
        if not selected:
            raise AssertionError(f"missing fake relation {model}({value})")
        return selected.records[0]

    def _line_records(
        self,
        order_model: str,
        commands: list[tuple[Any, ...]],
        current: Records | None = None,
    ) -> Records:
        line_model = f"{order_model}.line"
        rows = list(current.records if current is not None else [])
        for command, _record_id, values in commands:
            if command == 5:
                rows = []
                continue
            if command != 0:
                raise AssertionError(f"unexpected order line command: {command}")
            self.next_line_id += 1
            sale = order_model == "sale.order"
            quantity_name = "product_uom_qty" if sale else "product_qty"
            tax_ids = values["tax_ids"][0][2]
            row = self.add(
                line_model,
                self.next_line_id,
                sequence=values["sequence"],
                display_type=False,
                product_id=self._relation("product.product", values["product_id"]),
                name=values["name"],
                product_uom_id=self._relation("uom.uom", values["product_uom_id"]),
                price_unit=values["price_unit"],
                discount=values["discount"],
                tax_ids=self["account.tax"].browse(tax_ids),
                **{quantity_name: values[quantity_name]},
                **(
                    {"date_planned": values["date_planned"]}
                    if not sale
                    else {}
                ),
            )
            rows.append(row)
        return Records(self, line_model, rows)

    def add_order(
        self,
        model: str,
        record_id: int,
        state: str,
        lines: list[dict[str, Any]],
    ) -> Record:
        line_commands = [
            (0, 0, writes._order_line_values(f"{model}.create", line, index * 10))
            for index, line in enumerate(lines, start=1)
        ]
        return self.add(
            model,
            record_id,
            name=("S" if model == "sale.order" else "P") + f"{record_id:05d}",
            display_name=f"Order {record_id}",
            company_id=self.company,
            partner_id=self.partner,
            state=state,
            origin="",
            date_order="2026-08-28 01:02:03",
            client_order_ref=False,
            validity_date=False,
            commitment_date=False,
            partner_ref=False,
            payment_term_id=False,
            incoterm_id=False,
            order_line=self._line_records(model, line_commands),
        )

    def new_order(self, model: str, values: dict[str, Any]) -> Record:
        self.next_id += 1
        sale = model == "sale.order"
        record = self.add(
            model,
            self.next_id,
            name=("S" if sale else "P") + f"{self.next_id:05d}",
            display_name=f"Order {self.next_id}",
            company_id=self._relation("res.company", values["company_id"]),
            partner_id=self._relation("res.partner", values["partner_id"]),
            state="draft",
            origin=values["origin"],
            date_order=values["date_order"],
            client_order_ref=False,
            validity_date=False,
            commitment_date=False,
            partner_ref=False,
            payment_term_id=False,
            incoterm_id=False,
            order_line=self._line_records(model, values["order_line"]),
        )
        self.apply_order_values(
            record, {name: value for name, value in values.items() if name != "order_line"}
        )
        return record

    def apply_order_values(self, order: Record, values: dict[str, Any]) -> None:
        relation_models = {
            "company_id": "res.company",
            "partner_id": "res.partner",
            "pricelist_id": "product.pricelist",
            "currency_id": "res.currency",
            "picking_type_id": "stock.picking.type",
            "payment_term_id": "account.payment.term",
            "incoterm_id": "account.incoterms",
        }
        for field_name, value in values.items():
            if field_name == "order_line":
                order.order_line = self._line_records(
                    order._name, value, current=order.order_line
                )
            elif field_name in relation_models:
                setattr(order, field_name, self._relation(relation_models[field_name], value))
            else:
                setattr(order, field_name, value)


def sale_line(*, name: str = "Sale line", quantity: str = "3") -> dict[str, Any]:
    return {
        "product_id": 51,
        "name": name,
        "quantity": quantity,
        "uom_id": 1,
        "price_unit": "10.5",
        "discount": "0",
        "tax_ids": [8],
    }


def purchase_line(
    *, name: str = "Purchase line", quantity: str = "5"
) -> dict[str, Any]:
    return {
        **sale_line(name=name, quantity=quantity),
        "price_unit": "8",
        "tax_ids": [9],
        "date_planned": "2026-08-30 02:03:04",
    }


def sale_create_parameters() -> dict[str, Any]:
    return {
        "partner_id": 31,
        "pricelist_id": 41,
        "date_order": "2026-08-28 01:02:03",
        "client_order_ref": "CLIENT-31",
        "validity_date": "2026-09-30",
        "commitment_date": None,
        "payment_term_id": None,
        "lines": [sale_line()],
    }


def purchase_create_parameters() -> dict[str, Any]:
    return {
        "partner_id": 31,
        "currency_id": 6,
        "picking_type_id": 2,
        "date_order": "2026-08-28 01:02:03",
        "partner_ref": "VENDOR-31",
        "payment_term_id": None,
        "incoterm_id": None,
        "lines": [purchase_line()],
    }


def payload(
    capability_id: str,
    parameters: dict[str, Any],
    *,
    company_id: int = 7,
    create_key: str = "order-create-key-0001",
) -> dict[str, Any]:
    key = writes._deterministic_key(capability_id, parameters, company_id)
    return {
        "capability_id": capability_id,
        "company_id": company_id,
        "idempotency_key": key or create_key,
        "confirmation": capability_id,
        "parameters": copy.deepcopy(parameters),
    }


def dispatch(
    env: Env,
    capability_id: str,
    parameters: dict[str, Any],
    *,
    company_id: int = 7,
    create_key: str = "order-create-key-0001",
) -> dict[str, Any]:
    return writes.dispatch(
        env,
        payload(
            capability_id,
            parameters,
            company_id=company_id,
            create_key=create_key,
        ),
        company_id,
        Failure,
    )


@pytest.mark.parametrize("capability_id", SALE_CAPABILITIES)
def test_sale_order_runtime_uses_native_sales_group(capability_id: str) -> None:
    assert writes._GROUPS[capability_id] == "sales_team.group_sale_salesman"


@pytest.mark.parametrize("capability_id", PURCHASE_CAPABILITIES)
def test_purchase_order_runtime_uses_native_purchase_group(capability_id: str) -> None:
    assert writes._GROUPS[capability_id] == "purchase.group_purchase_user"


def test_dispatch_denies_missing_group_acl_and_company_before_any_order_method() -> None:
    parameters = {"order_id": 101}

    no_group = Env()
    no_group.denied_group = "sales_team.group_sale_salesman"
    page = dispatch(no_group, "sale.order.confirm", parameters)
    assert page["company_visible"] is True
    assert page["module_installed"] is True
    assert page["access_allowed"] is False
    assert ("has_group", "sales_team.group_sale_salesman") in no_group.calls
    assert not any(call[0] == "action_confirm" for call in no_group.calls)

    no_acl = Env()
    no_acl.denied_access = ("sale.order.line", "unlink")
    page = dispatch(
        no_acl,
        "sale.order.lines.replace",
        {"order_id": 101, "lines": [sale_line(name="Replacement")]},
    )
    assert page["access_allowed"] is False
    assert ("has_access", "sale.order.line", "unlink") in no_acl.calls
    assert not any(call[0] == "write" for call in no_acl.calls)

    no_company = Env()
    page = dispatch(
        no_company,
        "sale.order.confirm",
        parameters,
        company_id=8,
    )
    assert page["company_visible"] is False
    assert page["access_allowed"] is False
    assert not any(call[0] == "action_confirm" for call in no_company.calls)


@pytest.mark.parametrize(
    ("capability_id", "parameters", "model"),
    (
        ("sale.order.create", sale_create_parameters(), "sale.order"),
        ("purchase.order.create", purchase_create_parameters(), "purchase.order"),
    ),
)
def test_create_uses_marker_replay_and_rejects_same_key_with_different_parameters(
    capability_id: str, parameters: dict[str, Any], model: str
) -> None:
    env = Env()
    first = dispatch(env, capability_id, parameters)
    assert first["access_allowed"] is True
    assert first["idempotent_replay"] is False
    assert first["result"]["model"] == model
    assert first["result"]["state"] == "draft"
    assert set(first["result"]) == RESULT_KEYS
    assert first["result"]["source_id"] == 31
    assert len(first["result"]["line_ids"]) == 1

    replay = dispatch(env, capability_id, parameters)
    assert replay["idempotent_replay"] is True
    assert replay["result"]["id"] == first["result"]["id"]
    assert len([call for call in env.calls if call[:2] == ("create", model)]) == 1

    conflict_parameters = copy.deepcopy(parameters)
    key_name = "client_order_ref" if model == "sale.order" else "partner_ref"
    conflict_parameters[key_name] = "DIFFERENT"
    with pytest.raises(Failure) as exc_info:
        dispatch(env, capability_id, conflict_parameters)
    assert exc_info.value.code == "idempotency_conflict"


@pytest.mark.parametrize(
    ("capability_id", "order_name", "changes"),
    (
        (
            "sale.order.update_draft",
            "sale_order",
            {"client_order_ref": "UPDATED"},
        ),
        (
            "purchase.order.update_draft",
            "purchase_order",
            {"partner_ref": "VENDOR-UPDATED"},
        ),
    ),
)
def test_header_update_is_draft_only_and_replays_verified_values(
    capability_id: str, order_name: str, changes: dict[str, Any]
) -> None:
    env = Env()
    order = getattr(env, order_name)
    parameters = {"order_id": order.id, "changes": changes}
    first = dispatch(env, capability_id, parameters)
    assert first["idempotent_replay"] is False
    assert first["result"]["state"] == "draft"
    assert dispatch(env, capability_id, parameters)["idempotent_replay"] is True

    blocked = Env()
    blocked_order = getattr(blocked, order_name)
    blocked_order.state = "sale" if order_name == "sale_order" else "purchase"
    with pytest.raises(Failure) as exc_info:
        dispatch(
            blocked,
            capability_id,
            {"order_id": blocked_order.id, "changes": changes},
        )
    assert exc_info.value.code == "state_conflict"


@pytest.mark.parametrize(
    ("capability_id", "order_name", "lines", "blocked_state"),
    (
        (
            "sale.order.lines.replace",
            "sale_order",
            [sale_line(name="New sale line", quantity="7")],
            "sale",
        ),
        (
            "purchase.order.lines.replace",
            "purchase_order",
            [purchase_line(name="New purchase line", quantity="9")],
            "purchase",
        ),
    ),
)
def test_line_replacement_is_draft_only_and_preserves_purchase_planned_date(
    capability_id: str,
    order_name: str,
    lines: list[dict[str, Any]],
    blocked_state: str,
) -> None:
    env = Env()
    order = getattr(env, order_name)
    result = dispatch(env, capability_id, {"order_id": order.id, "lines": lines})
    assert result["idempotent_replay"] is False
    assert len(result["result"]["line_ids"]) == 1
    if order_name == "purchase_order":
        assert order.order_line.date_planned == lines[0]["date_planned"]
    assert dispatch(
        env, capability_id, {"order_id": order.id, "lines": lines}
    )["idempotent_replay"] is True

    blocked = Env()
    blocked_order = getattr(blocked, order_name)
    blocked_order.state = blocked_state
    with pytest.raises(Failure) as exc_info:
        dispatch(
            blocked,
            capability_id,
            {"order_id": blocked_order.id, "lines": lines},
        )
    assert exc_info.value.code == "state_conflict"


@pytest.mark.parametrize(
    (
        "capability_id",
        "order_name",
        "initial_state",
        "method",
        "target_state",
    ),
    (
        ("sale.order.confirm", "sale_order", "draft", "action_confirm", "sale"),
        ("sale.order.cancel", "sale_order", "sale", "action_cancel", "cancel"),
        (
            "sale.order.reset_to_draft",
            "sale_order",
            "cancel",
            "action_draft",
            "draft",
        ),
        (
            "purchase.order.confirm",
            "purchase_order",
            "draft",
            "button_confirm",
            "to approve",
        ),
        (
            "purchase.order.cancel",
            "purchase_order",
            "purchase",
            "button_cancel",
            "cancel",
        ),
        (
            "purchase.order.reset_to_draft",
            "purchase_order",
            "cancel",
            "button_draft",
            "draft",
        ),
    ),
)
def test_transitions_call_odoo_native_methods_and_replay_target_states(
    capability_id: str,
    order_name: str,
    initial_state: str,
    method: str,
    target_state: str,
) -> None:
    env = Env()
    if capability_id == "purchase.order.confirm":
        env.purchase_confirm_state = "to approve"
    order = getattr(env, order_name)
    order.state = initial_state
    parameters = {"order_id": order.id}

    first = dispatch(env, capability_id, parameters)
    assert first["idempotent_replay"] is False
    assert first["result"]["state"] == target_state
    assert set(first["result"]) == RESULT_KEYS
    assert (method, order.id) in env.calls

    replay = dispatch(env, capability_id, parameters)
    assert replay["idempotent_replay"] is True
    assert replay["result"]["state"] == target_state
    assert env.calls.count((method, order.id)) == 1
    assert any(call[:2] == ("with_company", order._name) for call in env.calls)
